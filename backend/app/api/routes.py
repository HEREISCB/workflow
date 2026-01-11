"""
API routes for workflow management
"""
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.models.workflow import (
    Workflow, WorkflowCreateRequest, WorkflowExecuteRequest
)
from app.models.tools import tool_registry
from app.engine.executor import workflow_executor


router = APIRouter()


@router.get("/tools")
async def list_tools():
    """List all available tools"""
    tools = tool_registry.list_tools()
    return {
        "tools": [t.model_dump() for t in tools]
    }


@router.post("/workflows")
async def create_workflow(request: WorkflowCreateRequest):
    """Create a new workflow"""
    if not workflow_executor:
        raise HTTPException(status_code=500, detail="Executor not initialized")
    
    workflow_id = str(uuid.uuid4())
    
    workflow = Workflow(
        id=workflow_id,
        name=request.name,
        description=request.description,
        nodes=request.nodes,
        edges=request.edges,
        global_context=request.global_context,
        global_tools=request.global_tools
    )
    
    workflow_executor.register_workflow(workflow)
    
    return {
        "id": workflow_id,
        "message": f"Workflow '{workflow.name}' created successfully"
    }


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a workflow by ID"""
    if not workflow_executor:
        raise HTTPException(status_code=500, detail="Executor not initialized")
    
    workflow = workflow_executor.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow.model_dump()


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, request: WorkflowExecuteRequest):
    """Execute a workflow"""
    if not workflow_executor:
        raise HTTPException(status_code=500, detail="Executor not initialized")
    
    try:
        result = await workflow_executor.execute(
            workflow_id,
            request.input_data,
            request.user_message
        )
        
        return {
            "status": "success",
            "output": result.get("output"),
            "collected_data": result.get("collected_data"),
            "tool_results": result.get("tool_results"),
            "pending_confirmation": result.get("pending_confirmation"),
            "token_usage": result.get("token_usage")
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/execute/stream")
async def execute_workflow_stream(workflow_id: str, request: WorkflowExecuteRequest):
    """Execute a workflow with SSE streaming"""
    if not workflow_executor:
        raise HTTPException(status_code=500, detail="Executor not initialized")
    
    async def generate():
        try:
            # For now, just execute and return result
            # Future: implement true streaming per node
            result = await workflow_executor.execute(
                workflow_id,
                request.input_data,
                request.user_message
            )
            
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/tools/confirm/{confirmation_id}")
async def confirm_tool_execution(confirmation_id: str):
    """Confirm a pending tool execution"""
    from app.engine.tool_executor import tool_executor as executor
    
    result = await executor.confirm_and_execute(confirmation_id)
    return result.model_dump()
