"""
Context manager for per-node context isolation
"""
from typing import Any
from app.models.workflow import Node, NodeContext


class ContextManager:
    """
    Manages context assembly per node for token optimization.
    Instead of passing full state to every LLM call, we build
    minimal context based on each node's configuration.
    """
    
    def build_context(self, state: dict[str, Any], node: Node) -> dict[str, Any]:
        """
        Build minimal context for a node based on its configuration.
        
        Args:
            state: Full workflow state
            node: Node to build context for
            
        Returns:
            Filtered context dict containing only what the node needs
        """
        context: dict[str, Any] = {}
        node_context = node.context
        
        # 1. Include only specified state fields
        for field in node_context.include_fields:
            if field in state:
                context[field] = state[field]
        
        # 2. Optionally include message history (with limit)
        if node_context.include_messages:
            messages = state.get("messages", [])
            # Take only the last N messages
            context["messages"] = messages[-node_context.max_messages:]
        
        # 3. Add custom system prompt if specified
        if node_context.custom_prompt:
            context["system_prompt"] = node_context.custom_prompt
        
        return context
    
    def merge_context(
        self,
        node_context: dict[str, Any],
        global_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge node-specific context with global context.
        Node context takes precedence over global.
        
        Args:
            node_context: Context built for specific node
            global_context: Global workflow context
            
        Returns:
            Merged context dict
        """
        merged = global_context.copy()
        merged.update(node_context)
        return merged
    
    def estimate_tokens(self, context: dict[str, Any]) -> int:
        """
        Rough estimation of token count for the context.
        Uses ~4 chars per token heuristic.
        
        Args:
            context: Context dict to estimate
            
        Returns:
            Estimated token count
        """
        import json
        context_str = json.dumps(context, default=str)
        return len(context_str) // 4
    
    def build_llm_messages(
        self,
        context: dict[str, Any],
        user_message: str | None = None
    ) -> list[dict[str, str]]:
        """
        Build messages array for LLM call from context.
        
        Args:
            context: Built context for the node
            user_message: Optional current user message
            
        Returns:
            List of message dicts for LLM
        """
        messages = []
        
        # Add system prompt if present
        if "system_prompt" in context:
            messages.append({
                "role": "system",
                "content": context["system_prompt"]
            })
        
        # Add conversation history if present
        if "messages" in context:
            messages.extend(context["messages"])
        
        # Add current user message
        if user_message:
            messages.append({
                "role": "user",
                "content": user_message
            })
        
        return messages


# Global instance
context_manager = ContextManager()
