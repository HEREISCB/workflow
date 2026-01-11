"""
Tool definitions and registry
"""
from typing import Optional, Callable, Any
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """A parameter for a tool"""
    name: str
    type: str = "string"
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    """Definition of a tool that can be called by LLM nodes"""
    id: str = Field(description="Unique identifier for the tool")
    name: str = Field(description="Display name for the tool")
    description: str = Field(description="Description of what the tool does")
    
    # Parameters schema
    parameters: list[ToolParameter] = Field(
        default_factory=list,
        description="Parameters the tool accepts"
    )
    
    # Execution configuration
    endpoint: Optional[str] = Field(
        default=None,
        description="HTTP endpoint to call"
    )
    method: str = Field(
        default="POST",
        description="HTTP method for endpoint"
    )
    function_path: Optional[str] = Field(
        default=None,
        description="Python function path to call"
    )
    
    # Conditional execution
    requires_confirmation: bool = Field(
        default=False,
        description="Whether to ask user before executing"
    )
    confirmation_prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt for confirmation"
    )


class ToolResult(BaseModel):
    """Result of a tool execution"""
    tool_id: str
    status: str  # "success", "error", "pending_confirmation"
    result: Optional[Any] = None
    error: Optional[str] = None
    confirmation_needed: bool = False
    confirmation_prompt: Optional[str] = None


# Built-in tool definitions
BUILTIN_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        id="http_request",
        name="HTTP Request",
        description="Make an HTTP request to an external API",
        parameters=[
            ToolParameter(name="url", type="string", description="The URL to request"),
            ToolParameter(name="method", type="string", description="HTTP method", default="GET"),
            ToolParameter(name="body", type="object", description="Request body", required=False),
            ToolParameter(name="headers", type="object", description="Request headers", required=False),
        ]
    ),
    ToolDefinition(
        id="send_email",
        name="Send Email",
        description="Send an email notification",
        parameters=[
            ToolParameter(name="to", type="string", description="Recipient email address"),
            ToolParameter(name="subject", type="string", description="Email subject"),
            ToolParameter(name="body", type="string", description="Email body"),
        ],
        requires_confirmation=True,
        confirmation_prompt="Send email to {to}?"
    ),
    ToolDefinition(
        id="database_query",
        name="Database Query",
        description="Execute a database query",
        parameters=[
            ToolParameter(name="query", type="string", description="SQL or NoSQL query"),
            ToolParameter(name="database", type="string", description="Database name", default="default"),
        ]
    ),
    ToolDefinition(
        id="calendar_check",
        name="Check Calendar",
        description="Check calendar availability",
        parameters=[
            ToolParameter(name="date", type="string", description="Date to check (YYYY-MM-DD)"),
            ToolParameter(name="time_range", type="string", description="Time range to check", required=False),
        ]
    ),
    ToolDefinition(
        id="knowledge_search",
        name="Knowledge Search",
        description="Search the knowledge base using RAG",
        parameters=[
            ToolParameter(name="query", type="string", description="Search query"),
            ToolParameter(name="top_k", type="integer", description="Number of results", default=5),
        ]
    ),
]


class ToolRegistry:
    """Central registry for all available tools"""
    
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, Callable] = {}
        
        # Register built-in tools
        for tool in BUILTIN_TOOLS:
            self.register(tool)
    
    def register(self, tool: ToolDefinition, handler: Optional[Callable] = None):
        """Register a tool definition and optionally its handler"""
        self._tools[tool.id] = tool
        if handler:
            self._handlers[tool.id] = handler
    
    def get(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get a tool definition by ID"""
        return self._tools.get(tool_id)
    
    def get_handler(self, tool_id: str) -> Optional[Callable]:
        """Get a tool handler by ID"""
        return self._handlers.get(tool_id)
    
    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools"""
        return list(self._tools.values())
    
    def get_tools_for_node(self, tool_ids: list[str]) -> list[ToolDefinition]:
        """Get tool definitions for a specific set of IDs"""
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]
    
    def to_openai_tools(self, tool_ids: list[str]) -> list[dict]:
        """Convert tools to OpenAI function calling format"""
        tools = []
        for tid in tool_ids:
            tool = self._tools.get(tid)
            if not tool:
                continue
            
            # Build parameters schema
            properties = {}
            required = []
            for param in tool.parameters:
                properties[param.name] = {
                    "type": param.type,
                    "description": param.description
                }
                if param.required:
                    required.append(param.name)
            
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.id,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })
        
        return tools


# Global registry instance
tool_registry = ToolRegistry()
