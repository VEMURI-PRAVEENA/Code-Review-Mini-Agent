"""
Tests for the graph execution engine.
Part of the consolidated test suite.
"""
import pytest
from engine.graph import WorkflowGraph, WorkflowExecutor, ExecutionLog
from engine.nodes import FunctionNode, NodeBuilder
from engine.types import ExecutionStatus


class TestGraphCreation:
    """Test graph creation and validation"""
    
    def test_create_empty_graph(self):
        """Test creating an empty graph"""
        graph = WorkflowGraph("test-graph")
        assert graph.graph_id == "test-graph"
        assert len(graph.nodes) == 0
        assert graph.start_node is None
    
    def test_add_single_node(self):
        """Test adding a node"""
        graph = WorkflowGraph("test-graph")
        node = FunctionNode("node1", lambda: {})
        
        graph.add_node(node, is_start=True)
        
        assert "node1" in graph.nodes
        assert graph.start_node == "node1"
    
    def test_add_multiple_nodes(self):
        """Test adding multiple nodes"""
        graph = WorkflowGraph("test-graph")
        node1 = FunctionNode("node1", lambda: {})
        node2 = FunctionNode("node2", lambda: {})
        
        graph.add_node(node1, is_start=True)
        graph.add_node(node2)
        
        assert len(graph.nodes) == 2
    
    def test_duplicate_node_fails(self):
        """Test that adding duplicate node fails"""
        graph = WorkflowGraph("test-graph")
        node = FunctionNode("node1", lambda: {})
        
        graph.add_node(node, is_start=True)
        
        with pytest.raises(ValueError):
            graph.add_node(node)
    
    def test_add_edge(self):
        """Test adding edges between nodes"""
        graph = WorkflowGraph("test-graph")
        node1 = FunctionNode("node1", lambda: {})
        node2 = FunctionNode("node2", lambda: {})
        
        graph.add_node(node1, is_start=True)
        graph.add_node(node2)
        graph.add_edge("node1", "node2")
        
        assert graph.edges["node1"] == "node2"
    
    def test_edge_to_nonexistent_node_fails(self):
        """Test that edge to nonexistent node fails"""
        graph = WorkflowGraph("test-graph")
        node = FunctionNode("node1", lambda: {})
        graph.add_node(node, is_start=True)
        
        with pytest.raises(ValueError):
            graph.add_edge("node1", "nonexistent")


class TestGraphValidation:
    """Test graph validation"""
    
    def test_empty_graph_invalid(self):
        """Test that empty graph is invalid"""
        graph = WorkflowGraph("test-graph")
        is_valid, error = graph.validate()
        assert not is_valid
    
    def test_no_start_node_invalid(self):
        """Test that graph without start node is invalid"""
        graph = WorkflowGraph("test-graph")
        node = FunctionNode("node1", lambda: {})
        graph.add_node(node)
        
        is_valid, error = graph.validate()
        assert not is_valid
    
    def test_valid_single_node(self):
        """Test valid single-node graph"""
        graph = WorkflowGraph("test-graph")
        node = FunctionNode("node1", lambda: {})
        graph.add_node(node, is_start=True)
        
        is_valid, error = graph.validate()
        assert is_valid
    
    def test_valid_multi_node(self):
        """Test valid multi-node graph"""
        graph = WorkflowGraph("test-graph")
        node1 = FunctionNode("node1", lambda: {})
        node2 = FunctionNode("node2", lambda: {})
        
        graph.add_node(node1, is_start=True)
        graph.add_node(node2)
        graph.add_edge("node1", "node2")
        
        is_valid, error = graph.validate()
        assert is_valid


class TestGraphExecution:
    """Test graph execution"""
    
    def test_single_node_execution(self):
        """Test executing single node"""
        def increment(counter):
            return {"counter": counter + 1}
        
        graph = WorkflowGraph("test-graph")
        node = NodeBuilder.function_node(
            "increment",
            increment,
            state_keys={"counter": "counter"}
        )
        graph.add_node(node, is_start=True)
        
        executor = WorkflowExecutor(graph)
        final_state, log = executor.execute({"counter": 5})
        
        assert final_state["counter"] == 6
        assert log.status == ExecutionStatus.COMPLETED
    
    def test_multi_node_execution(self):
        """Test executing multiple nodes"""
        def double(x):
            return {"x": x * 2}
        
        def add_ten(x):
            return {"x": x + 10}
        
        graph = WorkflowGraph("test-graph")
        node1 = NodeBuilder.function_node("double", double, state_keys={"x": "x"})
        node2 = NodeBuilder.function_node("add_ten", add_ten, state_keys={"x": "x"})
        
        graph.add_node(node1, is_start=True)
        graph.add_node(node2)
        graph.add_edge("double", "add_ten")
        
        executor = WorkflowExecutor(graph)
        final_state, log = executor.execute({"x": 5})
        
        # (5 * 2) + 10 = 20
        assert final_state["x"] == 20
    
    def test_execution_log_tracking(self):
        """Test that execution is logged"""
        graph = WorkflowGraph("test-graph")
        node = FunctionNode("node1", lambda: {})
        graph.add_node(node, is_start=True)
        
        executor = WorkflowExecutor(graph)
        _, log = executor.execute({})
        
        assert log.run_id is not None
        assert len(log.entries) > 0
        assert log.status == ExecutionStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
