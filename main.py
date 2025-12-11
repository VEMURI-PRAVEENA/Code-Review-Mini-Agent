"""
FastAPI application for the Workflow Engine.
Exposes REST APIs for graph creation and execution.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from engine.graph import WorkflowGraph, WorkflowExecutor
from engine.nodes import NodeBuilder
from engine.tools import get_registry
from workflows.code_review import create_code_review_workflow, run_code_review

# Initialize FastAPI
app = FastAPI(
    title="Workflow Engine API",
    description="A simplified LangGraph-like workflow engine",
    version="1.0.0"
)

# In-memory storage
graphs_store: Dict[str, WorkflowGraph] = {}
executors_store: Dict[str, WorkflowExecutor] = {}
runs_store: Dict[str, Dict[str, Any]] = {}  # run_id -> execution results


# Pydantic Models
class NodeDefinition(BaseModel):
    """Node definition"""
    id: str
    type: str  # "standard", "decision", "loop"
    tool_name: Optional[str] = None
    function_name: Optional[str] = None
    state_keys: Optional[Dict[str, str]] = None
    is_start: bool = False


class EdgeDefinition(BaseModel):
    """Edge definition"""
    from_node: str
    to_node: str


class GraphCreateRequest(BaseModel):
    """Request to create a new graph"""
    graph_id: str
    nodes: List[NodeDefinition]
    edges: List[EdgeDefinition]
    description: Optional[str] = None


class GraphRunRequest(BaseModel):
    """Request to run a graph"""
    graph_id: str
    initial_state: Dict[str, Any]
    async_execution: bool = False


class ToolCallRequest(BaseModel):
    """Request to call a tool"""
    tool_name: str
    kwargs: Dict[str, Any]


# Health check
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# Tool Registry Endpoints
@app.get("/tools/list")
def list_tools():
    """List available tools"""
    registry = get_registry()
    tools = registry.list_tools()
    return {
        "tools": tools,
        "count": len(tools)
    }


@app.post("/tools/call")
def call_tool(request: ToolCallRequest):
    """Call a tool directly"""
    try:
        registry = get_registry()
        result = registry.call(request.tool_name, **request.kwargs)
        return {
            "tool_name": request.tool_name,
            "result": result,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Graph Management Endpoints
@app.post("/graph/create")
def create_graph(request: GraphCreateRequest):
    """
    Create a new workflow graph.
    
    Accepts:
    - graph_id: Unique identifier
    - nodes: List of node definitions
    - edges: List of edge definitions
    
    Returns: graph_id and validation status
    """
    try:
        # Check if graph already exists
        if request.graph_id in graphs_store:
            raise ValueError(f"Graph '{request.graph_id}' already exists")
        
        # Create graph
        graph = WorkflowGraph(request.graph_id)
        registry = get_registry()
        
        # Add nodes
        for node_def in request.nodes:
            if node_def.type == "standard" and node_def.tool_name:
                node = NodeBuilder.tool_node(
                    node_def.id,
                    node_def.tool_name,
                    registry,
                    state_keys=node_def.state_keys,
                    output_key=f"{node_def.id}_result"
                )
            else:
                raise ValueError(f"Unsupported node type: {node_def.type}")
            
            graph.add_node(node, is_start=node_def.is_start)
        
        # Add edges
        for edge in request.edges:
            graph.add_edge(edge.from_node, edge.to_node)
        
        # Validate
        is_valid, error = graph.validate()
        if not is_valid:
            raise ValueError(f"Invalid graph: {error}")
        
        # Store graph and executor
        graphs_store[request.graph_id] = graph
        executors_store[request.graph_id] = WorkflowExecutor(graph)
        
        return {
            "graph_id": request.graph_id,
            "status": "created",
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "valid": is_valid
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/{graph_id}")
def get_graph(graph_id: str):
    """Get graph metadata"""
    if graph_id not in graphs_store:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found")
    
    graph = graphs_store[graph_id]
    return {
        "graph_id": graph.graph_id,
        "node_ids": list(graph.nodes.keys()),
        "edges": graph.edges,
        "start_node": graph.start_node,
        "created_at": graph.created_at.isoformat(),
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges)
    }


@app.get("/graphs/list")
def list_graphs():
    """List all graphs"""
    return {
        "graphs": [
            {
                "graph_id": gid,
                "nodes": len(g.nodes),
                "edges": len(g.edges),
                "created_at": g.created_at.isoformat()
            }
            for gid, g in graphs_store.items()
        ],
        "count": len(graphs_store)
    }


# Workflow Execution Endpoints
@app.post("/graph/run")
def run_graph(request: GraphRunRequest):
    """
    Run a workflow graph.
    
    Accepts:
    - graph_id: Graph to run
    - initial_state: Starting state
    - async_execution: Whether to run asynchronously
    
    Returns: run_id, final_state, and execution log
    """
    try:
        if request.graph_id not in executors_store:
            raise ValueError(f"Graph '{request.graph_id}' not found")
        
        executor = executors_store[request.graph_id]
        run_id = str(uuid.uuid4())
        
        # Execute
        final_state, execution_log = executor.execute(
            request.initial_state,
            run_id=run_id
        )
        
        # Store results
        runs_store[run_id] = {
            "graph_id": request.graph_id,
            "run_id": run_id,
            "final_state": final_state,
            "execution_log": execution_log.to_dict(),
            "status": execution_log.status.value,
            "error": execution_log.error
        }
        
        return runs_store[run_id]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/state/{run_id}")
def get_run_state(run_id: str):
    """Get the state of a workflow run"""
    if run_id not in runs_store:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    
    run_data = runs_store[run_id]
    return {
        "run_id": run_id,
        "status": run_data["status"],
        "final_state": run_data["final_state"],
        "execution_log": run_data["execution_log"],
        "error": run_data["error"]
    }


@app.get("/graph/runs")
def list_runs():
    """List all runs"""
    return {
        "runs": [
            {
                "run_id": rid,
                "graph_id": r.get("graph_id"),
                "status": r.get("status"),
                "error": r.get("error")
            }
            for rid, r in runs_store.items()
        ],
        "count": len(runs_store)
    }


# Example Workflow: Code Review Agent
@app.post("/workflows/code-review")
def run_code_review_workflow(request: Dict[str, Any]):
    """
    Run the built-in Code Review workflow.
    
    Accepts:
    - code: Python code to review
    - quality_threshold: Quality score threshold (default: 7.0)
    
    Returns: Review results with quality score and suggestions
    """
    try:
        code = request.get("code")
        if not code:
            raise ValueError("'code' field is required")
        
        quality_threshold = request.get("quality_threshold", 7.0)
        
        result = run_code_review(code, quality_threshold)
        
        # Store in runs
        run_id = result.get("run_id")
        runs_store[run_id] = result
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Bootstrap: Create example workflows
@app.on_event("startup")
def startup_event():
    """Initialize example workflows on startup"""
    try:
        # Create and register the code review workflow
        code_review_graph = create_code_review_workflow()
        graphs_store[code_review_graph.graph_id] = code_review_graph
        executors_store[code_review_graph.graph_id] = WorkflowExecutor(code_review_graph)
        
        print("✓ Code Review workflow loaded")
        print(f"✓ Available tools: {list(get_registry().list_tools().keys())}")
    except Exception as e:
        print(f"✗ Failed to load workflows: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
