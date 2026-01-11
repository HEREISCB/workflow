"""
Workflow and Node Pydantic models
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes available in the workflow"""
    START = "start"
    LLM = "llm"
    TOOL = "tool"
    CONDITION = "condition"
    GATHER = "gather"
    END = "end"


class NodeContext(BaseModel):
    """Per-node context configuration for token optimization"""
    include_fields: list[str] = Field(
        default_factory=list,
        description="State fields to include in this node's context"
    )
    include_messages: bool = Field(
        default=False,
        description="Whether to include conversation history"
    )
    max_messages: int = Field(
        default=5,
        description="Maximum number of messages to include if include_messages is True"
    )
    custom_prompt: Optional[str] = Field(
        default=None,
        description="Node-specific system prompt"
    )


class NodeToolConfig(BaseModel):
    """Per-node tool configuration"""
    available_tools: list[str] = Field(
        default_factory=list,
        description="IDs of tools this node can use"
    )
    auto_execute: bool = Field(
        default=True,
        description="Whether to execute tools immediately or wait for confirmation"
    )
    max_tool_calls: int = Field(
        default=3,
        description="Maximum number of tool calls per node execution"
    )


class ConditionBranch(BaseModel):
    """A branch in a condition node"""
    condition: str = Field(description="Condition expression to evaluate")
    target_node: str = Field(description="Node ID to route to if condition is true")


class Node(BaseModel):
    """A single node in the workflow"""
    id: str = Field(description="Unique identifier for the node")
    type: NodeType = Field(description="Type of the node")
    name: str = Field(description="Display name for the node")
    
    # Position for visual editor
    position: dict = Field(
        default_factory=lambda: {"x": 0, "y": 0},
        description="Position in the visual editor"
    )
    
    # Context configuration
    context: NodeContext = Field(
        default_factory=NodeContext,
        description="Context configuration for this node"
    )
    
    # Tool configuration (for LLM nodes)
    tools: NodeToolConfig = Field(
        default_factory=NodeToolConfig,
        description="Tool configuration for this node"
    )
    
    # Node-specific configuration
    config: dict = Field(
        default_factory=dict,
        description="Node-specific settings"
    )
    
    # Outgoing edges
    next_nodes: list[str] = Field(
        default_factory=list,
        description="IDs of nodes this connects to"
    )
    
    # For condition nodes
    branches: list[ConditionBranch] = Field(
        default_factory=list,
        description="Conditional branches (for condition nodes)"
    )
    default_next: Optional[str] = Field(
        default=None,
        description="Default node if no condition matches"
    )


class Edge(BaseModel):
    """An edge connecting two nodes"""
    id: str
    source: str
    target: str
    label: Optional[str] = None


class Workflow(BaseModel):
    """Complete workflow definition"""
    id: str = Field(description="Unique identifier for the workflow")
    name: str = Field(description="Display name for the workflow")
    description: Optional[str] = Field(
        default=None,
        description="Description of what this workflow does"
    )
    
    # Nodes and edges
    nodes: list[Node] = Field(
        default_factory=list,
        description="All nodes in the workflow"
    )
    edges: list[Edge] = Field(
        default_factory=list,
        description="All edges connecting nodes"
    )
    
    # Global context available to all nodes
    global_context: dict = Field(
        default_factory=dict,
        description="Context shared across all nodes"
    )
    
    # Global tools available to all LLM nodes
    global_tools: list[str] = Field(
        default_factory=list,
        description="Tool IDs available to all nodes"
    )


class WorkflowCreateRequest(BaseModel):
    """Request to create a new workflow"""
    name: str
    description: Optional[str] = None
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    global_context: dict = Field(default_factory=dict)
    global_tools: list[str] = Field(default_factory=list)


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow"""
    input_data: dict = Field(
        default_factory=dict,
        description="Initial input data for the workflow"
    )
    user_message: Optional[str] = Field(
        default=None,
        description="User message to process"
    )
