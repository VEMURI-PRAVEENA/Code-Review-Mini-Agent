"""
Test suite for the workflow engine.
Run with: pytest tests/
"""
import pytest
from engine.graph import WorkflowGraph, WorkflowExecutor
from engine.nodes import NodeBuilder, FunctionNode
from engine.tools import get_registry, extract_functions, check_complexity, detect_issues


class TestToolRegistry:
    """Test tool registry functionality"""
    
    def test_tool_registration(self):
        """Test registering and retrieving tools"""
        registry = get_registry()
        assert "extract_functions" in registry.tools
        assert "check_complexity" in registry.tools
    
    def test_extract_functions(self):
        """Test function extraction"""
        code = "def foo():\n    pass\ndef bar():\n    pass"
        result = extract_functions(code)
        
        assert result["function_count"] == 2
        assert result["functions"][0]["name"] == "foo"
        assert result["functions"][1]["name"] == "bar"
    
    def test_check_complexity(self):
        """Test complexity checking"""
        code = "def foo():\n    if True:\n        for i in range(10):\n            pass"
        result = check_complexity(code)
        
        assert "complexity_score" in result
        assert result["loop_count"] == 1
        assert result["branch_count"] == 1
    
    def test_detect_issues(self):
        """Test issue detection"""
        code = "def foo():\n    except:\n        pass"
        result = detect_issues(code)
        
        assert result["issue_count"] > 0
        assert any(i["type"] == "bare_except" for i in result["issues"])


class TestNodes:
    """Test node functionality"""
    
    def test_function_node_execution(self):
        """Test function node execution"""
        def add_one(value):
            return {"result": value + 1}
        
        node = FunctionNode(
            "add_one",
            add_one,
            state_keys={"input_value": "value"}
        )
        
        state = {"input_value": 5}
        new_state = node.execute(state)
        
        assert new_state["result"] == 6
    
    def test_tool_call_node(self):
        """Test tool call node"""
        registry = get_registry()
        
        code = "def sample():\n    pass"
        state = {"code": code}
        
        node = NodeBuilder.tool_node(
            "extract",
            "extract_functions",
            registry,
            state_keys={"code": "code"}
        )
        
        new_state = node.execute(state)
        assert "function_count" in new_state
        assert new_state["function_count"] == 1


class TestGraphEngine:
    """Test graph engine"""
    
    def test_graph_creation(self):
        """Test creating a graph"""
        graph = WorkflowGraph("test-graph")
        
        node1 = FunctionNode("node1", lambda: {})
        node2 = FunctionNode("node2", lambda: {})
        
        graph.add_node(node1, is_start=True)
        graph.add_node(node2)
        graph.add_edge("node1", "node2")
        
        assert graph.start_node == "node1"
        assert graph.edges["node1"] == "node2"
    
    def test_graph_validation(self):
        """Test graph validation"""
        graph = WorkflowGraph("test-graph")
        
        # No nodes - should fail
        is_valid, error = graph.validate()
        assert not is_valid
        
        # Add node and set as start
        node = FunctionNode("node1", lambda: {})
        graph.add_node(node, is_start=True)
        
        # Now should be valid
        is_valid, error = graph.validate()
        assert is_valid
    
    def test_simple_execution(self):
        """Test simple graph execution"""
        def increment_counter(counter):
            return {"counter": counter + 1}
        
        graph = WorkflowGraph("test-graph")
        node1 = NodeBuilder.function_node(
            "increment",
            increment_counter,
            state_keys={"counter": "counter"}
        )
        
        graph.add_node(node1, is_start=True)
        
        executor = WorkflowExecutor(graph)
        final_state, log = executor.execute({"counter": 5})
        
        assert final_state["counter"] == 6
        assert log.status.value == "completed"
    
    def test_multi_step_execution(self):
        """Test execution with multiple steps"""
        def step1(value):
            return {"value": value * 2}
        
        def step2(value):
            return {"value": value + 10}
        
        graph = WorkflowGraph("test-graph")
        
        node1 = NodeBuilder.function_node(
            "double",
            step1,
            state_keys={"value": "value"}
        )
        node2 = NodeBuilder.function_node(
            "add_ten",
            step2,
            state_keys={"value": "value"}
        )
        
        graph.add_node(node1, is_start=True)
        graph.add_node(node2)
        graph.add_edge("double", "add_ten")
        
        executor = WorkflowExecutor(graph)
        final_state, log = executor.execute({"value": 5})
        
        # (5 * 2) + 10 = 20
        assert final_state["value"] == 20
        assert log.status.value == "completed"


class TestCodeReviewWorkflow:
    """Test the code review workflow"""
    
    def test_code_review_basic(self):
        """Test code review on basic code"""
        from workflows.code_review import run_code_review
        
        code = """
def hello():
    return "world"
"""
        result = run_code_review(code)
        
        assert result["status"] == "completed"
        assert "final_state" in result
        assert "report" in result["final_state"]
    
    def test_code_review_complex(self):
        """Test code review on complex code"""
        from workflows.code_review import run_code_review
        
        code = """
def nested_loop(n):
    result = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result.append(i * j * k)
    except:
        pass
    return result
"""
        result = run_code_review(code)
        
        assert result["status"] == "completed"
        report = result["final_state"]["report"]
        assert report["summary"]["functions_found"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
