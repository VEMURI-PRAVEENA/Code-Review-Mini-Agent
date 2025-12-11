#!/usr/bin/env bash
# Test commands for Workflow Engine API
# Copy and paste these into your terminal after running: python main.py

echo "=== Workflow Engine API Test Commands ==="
echo ""
echo "Make sure the server is running: python main.py"
echo ""

# 1. Health Check
echo "1️⃣  Health Check:"
echo "curl http://localhost:8000/health"
curl http://localhost:8000/health
echo ""
echo ""

# 2. List Tools
echo "2️⃣  List Available Tools:"
echo "curl http://localhost:8000/tools/list"
curl http://localhost:8000/tools/list
echo ""
echo ""

# 3. Call a Tool Directly
echo "3️⃣  Call Extract Functions Tool:"
echo "curl -X POST http://localhost:8000/tools/call \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"tool_name\": \"extract_functions\", \"kwargs\": {\"code\": \"def foo(): pass\n def bar(): pass\"}}'"
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "extract_functions", "kwargs": {"code": "def foo(): pass\ndef bar(): pass"}}'
echo ""
echo ""

# 4. Run Code Review Workflow
echo "4️⃣  Run Code Review Workflow:"
echo "curl -X POST http://localhost:8000/workflows/code-review \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"code\": \"def slow():\n    for i in range(10):\n        for j in range(10):\n            pass\"}'"
curl -X POST http://localhost:8000/workflows/code-review \
  -H "Content-Type: application/json" \
  -d '{"code": "def slow():\n    for i in range(10):\n        for j in range(10):\n            pass"}'
echo ""
echo ""

# 5. List Graphs
echo "5️⃣  List Available Graphs:"
echo "curl http://localhost:8000/graphs/list"
curl http://localhost:8000/graphs/list
echo ""
echo ""

# 6. Get Code Review Graph
echo "6️⃣  Get Code Review Graph Details:"
echo "curl http://localhost:8000/graph/code-review-workflow"
curl http://localhost:8000/graph/code-review-workflow
echo ""
echo ""

echo "✅ Tests complete!"
echo ""
echo "For interactive testing, visit:"
echo "  http://localhost:8000/docs"
