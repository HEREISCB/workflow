"""
Tool executor for running tools with confirmation support
"""
import httpx
from typing import Any, Optional
from app.models.tools import ToolDefinition, ToolResult, tool_registry
from app.models.workflow import Node


class ToolNotAllowedError(Exception):
    """Raised when a tool is not allowed for a node"""
    pass


class ToolExecutor:
    """
    Executes tools with support for:
    - Per-node tool scoping
    - Confirmation before execution
    - HTTP and function-based tools
    """
    
    def __init__(self):
        self.registry = tool_registry
        self._pending_confirmations: dict[str, dict] = {}
    
    async def execute(
        self,
        tool_id: str,
        params: dict[str, Any],
        node: Node
    ) -> ToolResult:
        """
        Execute a tool for a specific node.
        
        Args:
            tool_id: ID of the tool to execute
            params: Parameters for the tool
            node: Node requesting the tool execution
            
        Returns:
            ToolResult with status and result/error
        """
        # 1. Validate tool is available for this node
        all_tools = node.tools.available_tools
        if tool_id not in all_tools:
            raise ToolNotAllowedError(
                f"Tool '{tool_id}' is not available for node '{node.id}'. "
                f"Available tools: {all_tools}"
            )
        
        # 2. Get tool definition
        tool = self.registry.get(tool_id)
        if not tool:
            return ToolResult(
                tool_id=tool_id,
                status="error",
                error=f"Tool '{tool_id}' not found in registry"
            )
        
        # 3. Check if confirmation is needed
        if tool.requires_confirmation and not node.tools.auto_execute:
            # Store pending confirmation
            confirmation_id = f"{node.id}_{tool_id}"
            self._pending_confirmations[confirmation_id] = {
                "tool_id": tool_id,
                "params": params,
                "node_id": node.id
            }
            
            # Build confirmation prompt
            prompt = tool.confirmation_prompt or f"Execute {tool.name}?"
            # Replace placeholders with params
            for key, value in params.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))
            
            return ToolResult(
                tool_id=tool_id,
                status="pending_confirmation",
                confirmation_needed=True,
                confirmation_prompt=prompt
            )
        
        # 4. Execute the tool
        return await self._execute_tool(tool, params)
    
    async def confirm_and_execute(
        self,
        confirmation_id: str
    ) -> ToolResult:
        """
        Execute a tool after user confirmation.
        
        Args:
            confirmation_id: ID of the pending confirmation
            
        Returns:
            ToolResult with execution result
        """
        pending = self._pending_confirmations.pop(confirmation_id, None)
        if not pending:
            return ToolResult(
                tool_id="unknown",
                status="error",
                error=f"No pending confirmation found for '{confirmation_id}'"
            )
        
        tool = self.registry.get(pending["tool_id"])
        if not tool:
            return ToolResult(
                tool_id=pending["tool_id"],
                status="error",
                error=f"Tool not found"
            )
        
        return await self._execute_tool(tool, pending["params"])
    
    async def _execute_tool(
        self,
        tool: ToolDefinition,
        params: dict[str, Any]
    ) -> ToolResult:
        """
        Actually execute the tool.
        
        Args:
            tool: Tool definition
            params: Parameters for execution
            
        Returns:
            ToolResult with result or error
        """
        try:
            # HTTP endpoint execution
            if tool.endpoint:
                result = await self._http_call(tool.endpoint, tool.method, params)
                return ToolResult(
                    tool_id=tool.id,
                    status="success",
                    result=result
                )
            
            # Python function execution
            if tool.function_path:
                result = await self._function_call(tool.function_path, params)
                return ToolResult(
                    tool_id=tool.id,
                    status="success",
                    result=result
                )
            
            # Built-in tool handlers
            handler = self.registry.get_handler(tool.id)
            if handler:
                result = await handler(params)
                return ToolResult(
                    tool_id=tool.id,
                    status="success",
                    result=result
                )
            
            # Default mock response for demo
            return ToolResult(
                tool_id=tool.id,
                status="success",
                result={"message": f"Tool {tool.name} executed with params: {params}"}
            )
            
        except Exception as e:
            return ToolResult(
                tool_id=tool.id,
                status="error",
                error=str(e)
            )
    
    async def _http_call(
        self,
        endpoint: str,
        method: str,
        params: dict[str, Any]
    ) -> dict:
        """Make HTTP request to tool endpoint"""
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(endpoint, params=params)
            else:
                response = await client.request(method, endpoint, json=params)
            response.raise_for_status()
            return response.json()
    
    async def _function_call(
        self,
        function_path: str,
        params: dict[str, Any]
    ) -> Any:
        """Call a Python function by import path"""
        import importlib
        
        module_path, func_name = function_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        
        # Check if async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return await func(**params)
        return func(**params)


# Global instance
tool_executor = ToolExecutor()
