# AI Engineering Internship - Workflow Engine Assignment

## Quick Start

```bash
# Clone and setup
git clone <your-repo>
cd workflow-engine
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py

# Test the API
curl -X POST http://localhost:8000/graph/create \
  -H "Content-Type: application/json" \
  -d @sample_workflow.json

curl -X POST http://localhost:8000/graph/run \
  -H "Content-Type: application/json" \
  -d '{"graph_id": "code-review-workflow", "initial_state": {"code": "def slow(): time.sleep(10)"}}'
```

---

## What's Included

### Core Architecture
- **Graph Engine** (`engine/graph.py`): Pure Python workflow definition and execution
- **Node System** (`engine/nodes.py`): Composable nodes with type safety
- **State Management** (`engine/state.py`): Immutable state tracking
- **Tool Registry** (`engine/tools.py`): Function registration and execution
- **FastAPI** (`main.py`): REST API endpoints
- **Example Workflow** (`workflows/code_review.py`): Complete working agent

### Key Features Implemented
✅ Nodes with state input/output  
✅ Edges and branching (conditional routing)  
✅ Looping until condition met  
✅ Tool registry with pre-built tools  
✅ FastAPI endpoints for graph creation and execution  
✅ Run state tracking via `run_id`  
✅ Execution logging and history  
✅ Async support for long-running operations  
✅ Type safety with Pydantic models  
✅ Clean, maintainable code structure  

---

## API Examples

### 1. Create a Workflow
```bash
POST /graph/create
{
  "graph_id": "code-review-workflow",
  "nodes": {
    "extract": {...},
    "analyze": {...},
    "suggest": {...}
  },
  "edges": {
    "extract": "analyze",
    "analyze": "suggest"
  }
}
```

### 2. Run Workflow
```bash
POST /graph/run
{
  "graph_id": "code-review-workflow",
  "initial_state": {
    "code": "def sample(): pass",
    "quality_threshold": 7
  }
}
```

Response:
```json
{
  "run_id": "run_12345",
  "final_state": {...},
  "execution_log": [...]
}
```

### 3. Check Run Status
```bash
GET /graph/state/run_12345
```

---

## What Makes This Solution Strong

1. **Clean Separation of Concerns**
   - Engine logic isolated from API
   - Nodes are pure functions
   - State flows through well-defined interfaces

2. **Type Safety**
   - Pydantic models for state
   - Function signatures are clear
   - IDE autocomplete works

3. **Scalability**
   - Nodes are composable
   - Easy to add new workflows
   - Tool registry is extensible

4. **Production-Ready Touches**
   - Error handling and validation
   - Execution logging for debugging
   - Async/await support
   - Run history tracking

5. **Testability**
   - No side effects in core logic
   - Pure functions where possible
   - Mocking tools is trivial

---

## Future Improvements (Mention in Interview)

- [ ] Persist to PostgreSQL for run history
- [ ] WebSocket endpoint for real-time execution logs
- [ ] Parallel node execution (DAG support)
- [ ] Node result caching
- [ ] Workflow versioning
- [ ] Built-in retry/error recovery
- [ ] Observability (OpenTelemetry integration)
- [ ] Workflow visualization API

---

## How to Structure Your GitHub

```
workflow-engine/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Dependencies
├── README.md              # (copy this)
├── engine/
│   ├── __init__.py
│   ├── graph.py           # Core graph execution
│   ├── nodes.py           # Node definitions
│   ├── state.py           # State models
│   ├── tools.py           # Tool registry
│   └── types.py           # Type definitions
├── workflows/
│   ├── __init__.py
│   └── code_review.py     # Example: Code Review Agent
├── tests/
│   ├── __init__.py
│   ├── test_graph.py
│   ├── test_nodes.py
│   └── test_workflows.py
├── sample_workflow.json    # Example graph definition
└── .gitignore
```

---

## Interview Talking Points

- "I used Pydantic for type safety and validation"
- "The state dictionary flows through nodes sequentially"
- "Branching is handled by conditional edges"
- "Looping works via edge redirection in the execution loop"
- "Tools are registered in a dictionary for loose coupling"
- "Error handling ensures failed nodes don't crash the workflow"
- "Execution logs provide full traceability"
- "The API design is RESTful and stateless"

Good luck! 🚀
