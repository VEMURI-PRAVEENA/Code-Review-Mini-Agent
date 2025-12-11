
A production-ready **simplified LangGraph** implementation in Python with FastAPI. Built to demonstrate clean architecture, async programming, and thoughtful API design.

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run
python main.py

# Visit: http://localhost:8000/docs (Swagger UI)
```

---

## Architecture Overview

### Core Components

```
engine/
├── graph.py          # WorkflowGraph, WorkflowExecutor (main engine)
├── nodes.py          # Node types (FunctionNode, ToolCallNode, DecisionNode, LoopNode)
├── tools.py          # ToolRegistry + built-in tools
├── types.py          # Type definitions
└── state.py          # State management (optional, state is dict-based)

workflows/
└── code_review.py    # Example: Code Review Agent workflow

main.py              # FastAPI REST API
```

### Key Design Decisions

**1. State-as-Dictionary**
- State flows through nodes as simple Python dicts
- No complex state machines - keeps logic transparent
- Easy to inspect and debug

**2. Node-Based Composition**
```python
graph = WorkflowGraph("my-workflow")
graph.add_node(extract_node, is_start=True)
graph.add_node(analyze_node)
graph.add_edge("extract", "analyze")
```

**3. Tool Registry Pattern**
- Functions registered once, reused across workflows
- Loose coupling between tools and workflows
- Easy to add new tools without modifying graph

**4. Clean Separation**
- Graph logic isolated from API layer
- Nodes are pure (no side effects)
- Easy to test each component independently

---

## Features Implemented

###  Core Requirements

- **Nodes**: Functions that read/modify shared state
- **State**: Dictionary flowing through nodes
- **Edges**: Simple routing between nodes
- **Branching**: DecisionNode for conditional routing
- **Looping**: LoopNode for iterative execution
- **Tool Registry**: Dictionary of registered tools
- **FastAPI Endpoints**:
  - `POST /graph/create` - Define a workflow
  - `POST /graph/run` - Execute a workflow
  - `GET /graph/state/{run_id}` - Check execution status

###  Bonus Features

- **Type Safety**: Pydantic models for API validation
- **Execution Logging**: Full trace of each node execution
- **Error Handling**: Graceful error propagation
- **Built-in Example**: Complete Code Review Agent workflow
- **Tool Listing**: `GET /tools/list` to see available tools
- **Run History**: Store and retrieve past executions
- **Async Support**: `execute_async` for long-running operations
- **Multiple Workflows**: Support arbitrary graph definitions

---

## API Examples

### 1. List Available Tools

```bash
curl http://localhost:8000/tools/list
```

Response:
```json
{
  "tools": {
    "extract_functions": "Extract function definitions...",
    "check_complexity": "Check code complexity...",
    "detect_issues": "Detect code issues...",
    "suggest_improvements": "Suggest improvements...",
    "calculate_score": "Calculate quality score..."
  },
  "count": 5
}
```

### 2. Run Code Review Workflow (Pre-built)

```bash
curl -X POST http://localhost:8000/workflows/code-review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def slow():\n    for i in range(10):\n        for j in range(10):\n            pass",
    "quality_threshold": 7.0
  }'
```

Response:
```json
{
  "run_id": "abc-123",
  "status": "completed",
  "final_state": {
    "report": {
      "overall_quality_score": 7.2,
      "rating": "Good",
      "summary": {
        "functions_found": 1,
        "complexity_score": 4.0,
        "total_issues": 2,
        "improvement_suggestions": 1
      }
    }
  },
  "execution_log": {...}
}
```

### 3. Create Custom Workflow

```bash
curl -X POST http://localhost:8000/graph/create \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "my-workflow",
    "nodes": [
      {
        "id": "extract",
        "type": "standard",
        "tool_name": "extract_functions",
        "state_keys": {"code": "code"},
        "is_start": true
      },
      {
        "id": "analyze",
        "type": "standard",
        "tool_name": "check_complexity",
        "state_keys": {"code": "code"}
      }
    ],
    "edges": [
      {"from_node": "extract", "to_node": "analyze"}
    ]
  }'
```

### 4. Run Workflow

```bash
curl -X POST http://localhost:8000/graph/run \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "my-workflow",
    "initial_state": {
      "code": "def sample(): pass"
    }
  }'
```

### 5. Check Run Status

```bash
curl http://localhost:8000/graph/state/{run_id}
```

---

## Code Review Workflow (Example)

The built-in Code Review Agent demonstrates:

1. **Extract Functions** - Parse code and identify functions
2. **Check Complexity** - Measure nesting depth, branches, loops
3. **Detect Issues** - Find bare excepts, missing docstrings, long lines
4. **Suggest Improvements** - Generate actionable recommendations
5. **Calculate Score** - Compute overall quality (0-10)
6. **Generate Report** - Compile results

**Sample Output:**
```
Quality Score: 7.2/10
Rating: Good

Summary:
  functions_found: 1
  complexity_score: 4.0
  total_issues: 2
  improvement_suggestions: 1
```

---

## Testing

```bash
# Run tests
pytest tests/test_engine.py -v

# Test coverage
pytest tests/ --cov=engine --cov=workflows
```

Tests cover:
- Tool registration and execution
- Node execution (function, tool call)
- Graph creation and validation
- Multi-step workflow execution
- Code review workflow end-to-end

---

## What Makes This Solution Strong

### 1. **Clean Architecture**
- Clear separation: Engine → Nodes → Tools → API
- Each component has a single responsibility
- Easy to understand and extend

### 2. **Type Safety**
- Pydantic models for all API inputs
- Type hints throughout
- Runtime validation

### 3. **Production-Ready**
- Error handling and validation
- Execution logging for debugging
- Async support built in
- Run history tracking

### 4. **Extensibility**
- Add new tools by registering functions
- Create workflows by composing nodes
- No hardcoding or magic strings

### 5. **Testability**
- Pure functions in nodes
- No global state (except registry)
- Easy to mock tools

---

## What Would I Improve With More Time

### High Priority
1. **Persistent Storage**
   - SQLite/PostgreSQL for graphs and runs
   - Query execution history
   - Workflow versioning

2. **Parallel Execution**
   - DAG support for running independent nodes concurrently
   - Performance improvement for complex workflows

3. **WebSocket Support**
   - Stream execution logs in real-time
   - Live workflow monitoring

### Medium Priority
4. **Advanced Branching**
   - Multi-branch decisions (not just binary)
   - Merge operations to sync branches

5. **Workflow Visualization**
   - GraphQL endpoint for graph structure
   - UI to draw workflows

6. **Retry & Error Recovery**
   - Automatic retry with exponential backoff
   - Custom error handlers per node

### Nice to Have
7. **Caching**
   - Cache tool results by input hash
   - Skip re-execution of identical nodes

8. **Distributed Execution**
   - Run nodes on remote workers
   - Queue-based execution (Celery/Redis)

9. **OpenTelemetry Integration**
   - Trace spans for observability
   - Metrics for performance monitoring

---

## File Structure

```
workflow-engine/
├── engine/
│   ├── __init__.py
│   ├── graph.py           # Core: WorkflowGraph, WorkflowExecutor
│   ├── nodes.py           # Core: Node types, NodeBuilder
│   ├── tools.py           # Tool registry + built-in tools
│   ├── types.py           # Type definitions
│   └── state.py           # (Optional) State models
│
├── workflows/
│   ├── __init__.py
│   └── code_review.py     # Example: Code Review Agent
│
├── tests/
│   ├── __init__.py
│   └── test_engine.py     # Test suite
│
├── main.py                # FastAPI application
├── requirements.txt       # Dependencies
├── README.md              # This file
└── .gitignore
```

---

## Deployment

### Local Development
```bash
python main.py
```

### Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

---



