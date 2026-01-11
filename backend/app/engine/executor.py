"""
LangGraph workflow executor
"""
import json
import uuid
from typing import Any, TypedDict, Annotated
from operator import add

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from app.models.workflow import Workflow, Node, NodeType
from app.models.tools import tool_registry
from app.engine.context_manager import context_manager
from app.engine.tool_executor import tool_executor


class WorkflowState(TypedDict):
    """State that flows through the workflow"""
    # Core state
    messages: Annotated[list[dict], add]  # Conversation history
    current_node: str
    
    # User data
    user_input: str
    
    # Collected data from nodes
    collected_data: dict
    
    # Tool execution results
    tool_results: list[dict]
    
    # Pending confirmations
    pending_confirmation: dict | None
    
    # Final output
    output: str | None
    
    # Metadata
    token_usage: dict


class WorkflowExecutor:
    """
    Converts workflow definitions to LangGraph and executes them.
    Handles context isolation per node for token optimization.
    """
    
    def __init__(self, openai_api_key: str | None = None):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=openai_api_key,
            temperature=0.7
        )
        self._workflows: dict[str, Workflow] = {}
        self._compiled_graphs: dict[str, Any] = {}
    
    def register_workflow(self, workflow: Workflow) -> str:
        """Register a workflow and compile it"""
        self._workflows[workflow.id] = workflow
        self._compiled_graphs[workflow.id] = self._build_graph(workflow)
        return workflow.id
    
    def _build_graph(self, workflow: Workflow) -> Any:
        """Convert workflow definition to LangGraph StateGraph"""
        graph = StateGraph(WorkflowState)
        
        # Build node lookup
        node_map = {n.id: n for n in workflow.nodes}
        
        # Add all nodes
        for node in workflow.nodes:
            node_func = self._create_node_function(node, workflow)
            graph.add_node(node.id, node_func)
        
        # Find start node
        start_node = next(
            (n for n in workflow.nodes if n.type == NodeType.START),
            workflow.nodes[0] if workflow.nodes else None
        )
        
        if start_node:
            graph.set_entry_point(start_node.id)
        
        # Add edges based on node configurations
        for node in workflow.nodes:
            if node.type == NodeType.END:
                graph.add_edge(node.id, END)
            elif node.type == NodeType.CONDITION:
                # Add conditional edges
                self._add_conditional_edges(graph, node, node_map)
            elif node.next_nodes:
                # Simple edge to first next node
                graph.add_edge(node.id, node.next_nodes[0])
            elif not node.next_nodes and node.type != NodeType.START:
                # If no next nodes and not start, go to END
                graph.add_edge(node.id, END)
        
        return graph.compile()
    
    def _add_conditional_edges(
        self,
        graph: StateGraph,
        node: Node,
        node_map: dict[str, Node]
    ):
        """Add conditional routing edges for a condition node"""
        
        def route_function(state: WorkflowState) -> str:
            """Dynamic router based on condition evaluation"""
            collected = state.get("collected_data", {})
            
            for branch in node.branches:
                # Simple condition evaluation
                # Format: "field == value" or "field contains value"
                try:
                    condition = branch.condition
                    if "==" in condition:
                        field, value = condition.split("==")
                        field = field.strip()
                        value = value.strip().strip('"\'')
                        if str(collected.get(field, "")).lower() == value.lower():
                            return branch.target_node
                    elif "contains" in condition:
                        field, value = condition.split("contains")
                        field = field.strip()
                        value = value.strip().strip('"\'')
                        if value.lower() in str(collected.get(field, "")).lower():
                            return branch.target_node
                except:
                    pass
            
            # Default route
            return node.default_next or END
        
        # Build conditional map
        condition_map = {b.target_node: b.target_node for b in node.branches}
        if node.default_next:
            condition_map[node.default_next] = node.default_next
        condition_map[END] = END
        
        graph.add_conditional_edges(
            node.id,
            route_function,
            condition_map
        )
    
    def _create_node_function(self, node: Node, workflow: Workflow):
        """Create an async function that executes a node with isolated context"""
        
        async def execute_node(state: WorkflowState) -> dict:
            """Execute node with context isolation"""
            
            # Build context for this node only
            node_context = context_manager.build_context(dict(state), node)
            full_context = context_manager.merge_context(
                node_context,
                workflow.global_context
            )
            
            # Track token estimation
            estimated_tokens = context_manager.estimate_tokens(full_context)
            
            result = {
                "current_node": node.id,
                "token_usage": {
                    node.id: estimated_tokens
                }
            }
            
            # Execute based on node type
            if node.type == NodeType.START:
                result["collected_data"] = state.get("collected_data", {})
                
            elif node.type == NodeType.LLM:
                llm_result = await self._execute_llm_node(
                    node, workflow, full_context, state
                )
                result.update(llm_result)
                
            elif node.type == NodeType.GATHER:
                gather_result = self._execute_gather_node(node, state)
                result.update(gather_result)
                
            elif node.type == NodeType.TOOL:
                tool_result = await self._execute_tool_node(node, state)
                result.update(tool_result)
                
            elif node.type == NodeType.CONDITION:
                # Condition nodes just pass through, routing handled by edges
                pass
                
            elif node.type == NodeType.END:
                result["output"] = state.get("output", "Workflow completed")
            
            return result
        
        return execute_node
    
    async def _execute_llm_node(
        self,
        node: Node,
        workflow: Workflow,
        context: dict,
        state: WorkflowState
    ) -> dict:
        """Execute an LLM node with tool calling support"""
        
        # Build messages for LLM
        messages = context_manager.build_llm_messages(
            context,
            state.get("user_input")
        )
        
        # Get available tools for this node
        available_tool_ids = (
            node.tools.available_tools + 
            workflow.global_tools
        )
        
        # Prepare kwargs for LLM
        kwargs = {}
        if available_tool_ids:
            tools = tool_registry.to_openai_tools(available_tool_ids)
            if tools:
                kwargs["tools"] = tools
        
        # Call LLM
        response = await self.llm.ainvoke(messages, **kwargs)
        
        result = {
            "messages": [{"role": "assistant", "content": response.content}],
            "output": response.content
        }
        
        # Handle tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_results = []
            for tool_call in response.tool_calls:
                tool_result = await tool_executor.execute(
                    tool_call["name"],
                    tool_call["args"],
                    node
                )
                tool_results.append(tool_result.model_dump())
                
                # Check if confirmation needed
                if tool_result.confirmation_needed:
                    result["pending_confirmation"] = {
                        "tool_id": tool_result.tool_id,
                        "prompt": tool_result.confirmation_prompt
                    }
            
            result["tool_results"] = tool_results
        
        return result
    
    def _execute_gather_node(self, node: Node, state: WorkflowState) -> dict:
        """Execute a gather node to collect user input"""
        config = node.config
        field_name = config.get("field_name", "gathered_input")
        
        # Store user input in collected data
        collected = state.get("collected_data", {}).copy()
        collected[field_name] = state.get("user_input", "")
        
        return {
            "collected_data": collected,
            "output": config.get("response", "Thank you for the information.")
        }
    
    async def _execute_tool_node(self, node: Node, state: WorkflowState) -> dict:
        """Execute a standalone tool node"""
        config = node.config
        tool_id = config.get("tool_id")
        params = config.get("params", {})
        
        # Replace param placeholders with collected data
        collected = state.get("collected_data", {})
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                field = value[1:]
                params[key] = collected.get(field, value)
        
        result = await tool_executor.execute(tool_id, params, node)
        
        return {
            "tool_results": [result.model_dump()],
            "output": json.dumps(result.result) if result.result else result.error
        }
    
    async def execute(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
        user_message: str | None = None
    ) -> dict:
        """
        Execute a workflow with given input.
        
        Args:
            workflow_id: ID of registered workflow
            input_data: Initial input data
            user_message: User message to process
            
        Returns:
            Final workflow state
        """
        if workflow_id not in self._compiled_graphs:
            raise ValueError(f"Workflow '{workflow_id}' not found")
        
        graph = self._compiled_graphs[workflow_id]
        
        # Initialize state
        initial_state: WorkflowState = {
            "messages": [],
            "current_node": "",
            "user_input": user_message or "",
            "collected_data": input_data,
            "tool_results": [],
            "pending_confirmation": None,
            "output": None,
            "token_usage": {}
        }
        
        # Run the graph
        final_state = await graph.ainvoke(initial_state)
        
        return dict(final_state)
    
    def get_workflow(self, workflow_id: str) -> Workflow | None:
        """Get a workflow by ID"""
        return self._workflows.get(workflow_id)


# Global executor instance (initialized in main.py with API key)
workflow_executor: WorkflowExecutor | None = None


def init_executor(api_key: str):
    """Initialize the global workflow executor"""
    global workflow_executor
    workflow_executor = WorkflowExecutor(api_key)
    return workflow_executor
