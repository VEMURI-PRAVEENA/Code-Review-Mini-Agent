"""
Tests for node implementations.
Part of the consolidated test suite.
"""
import pytest
from engine.nodes import (
    FunctionNode, ToolCallNode, DecisionNode, 
    LoopNode, NodeBuilder
)
from engine.tools import get_registry


class TestFunctionNode:
    """Test FunctionNode execution"""
    
    def test_simple_function_execution(self):
        """Test executing a simple function"""
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
    
    def test_function_with_multiple_inputs(self):
        """Test function with multiple inputs"""
        def multiply(a, b):
            return {"product": a * b}
        
        node = FunctionNode(
            "multiply",
            multiply,
            state_keys={"x": "a", "y": "b"}
        )
        
        state = {"x": 3, "y": 4}
        new_state = node.execute(state)
        
        assert new_state["product"] == 12
    
    def test_function_preserves_state(self):
        """Test that function preserves existing state"""
        def add_one(x):
            return {"y": x + 1}
        
        node = FunctionNode(
            "add_one",
            add_one,
            state_keys={"value": "x"}
        )
        
        state = {"value": 5, "original_key": "original_value"}
        new_state = node.execute(state)
        
        assert new_state["original_key"] == "original_value"
        assert new_state["y"] == 6
    
    def test_node_builder_function_node(self):
        """Test NodeBuilder for FunctionNode"""
        def increment(x):
            return {"result": x + 1}
        
        node = NodeBuilder.function_node(
            "increment",
            increment,
            state_keys={"value": "x"}
        )
        
        state = {"value": 10}
        new_state = node.execute(state)
        
        assert new_state["result"] == 11


class TestToolCallNode:
    """Test ToolCallNode execution"""
    
    def test_tool_call_node(self):
        """Test calling a tool from registry"""
        registry = get_registry()
        code = "def foo():\n    pass"
        state = {"code": code}
        
        node = ToolCallNode(
            "extract",
            "extract_functions",
            registry,
            state_keys={"code": "code"}
        )
        
        new_state = node.execute(state)
        
        assert "function_count" in new_state
        assert new_state["function_count"] == 1
    
    def test_tool_node_builder(self):
        """Test NodeBuilder for ToolCallNode"""
        registry = get_registry()
        code = "def sample(): pass"
        state = {"code": code}
        
        node = NodeBuilder.tool_node(
            "extract",
            "extract_functions",
            registry,
            state_keys={"code": "code"}
        )
        
        new_state = node.execute(state)
        assert "function_count" in new_state


class TestDecisionNode:
    """Test DecisionNode execution"""
    
    def test_decision_node_true_branch(self):
        """Test decision node routing to true branch"""
        def condition(state):
            return "high" if state["score"] >= 8 else "low"
        
        node = DecisionNode(
            "check_score",
            condition,
            branches={"high": "pass", "low": "fail"}
        )
        
        state = {"score": 9}
        next_node = node.get_next_node(state)
        assert next_node == "pass"
    
    def test_decision_node_false_branch(self):
        """Test decision node routing to false branch"""
        def condition(state):
            return "high" if state["score"] >= 8 else "low"
        
        node = DecisionNode(
            "check_score",
            condition,
            branches={"high": "pass", "low": "fail"}
        )
        
        state = {"score": 5}
        next_node = node.get_next_node(state)
        assert next_node == "fail"
    
    def test_decision_node_builder(self):
        """Test NodeBuilder for DecisionNode"""
        def condition(state):
            return "yes" if state["flag"] else "no"
        
        node = NodeBuilder.decision_node(
            "check_flag",
            condition,
            branches={"yes": "branch_a", "no": "branch_b"}
        )
        
        assert node.get_next_node({"flag": True}) == "branch_a"
        assert node.get_next_node({"flag": False}) == "branch_b"


class TestLoopNode:
    """Test LoopNode execution"""
    
    def test_loop_node_should_loop(self):
        """Test loop node when condition is true"""
        def condition(state):
            return state["counter"] < 5
        
        node = LoopNode(
            "check_counter",
            condition,
            loop_back_to="increment"
        )
        
        state = {"counter": 3}
        assert node.should_loop(state) is True
    
    def test_loop_node_should_not_loop(self):
        """Test loop node when condition is false"""
        def condition(state):
            return state["counter"] < 5
        
        node = LoopNode(
            "check_counter",
            condition,
            loop_back_to="increment"
        )
        
        state = {"counter": 5}
        assert node.should_loop(state) is False
    
    def test_loop_node_builder(self):
        """Test NodeBuilder for LoopNode"""
        node = NodeBuilder.loop_node(
            "check_done",
            lambda s: s["count"] < 10,
            loop_back_to="process"
        )
        
        assert node.should_loop({"count": 5}) is True
        assert node.should_loop({"count": 10}) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
