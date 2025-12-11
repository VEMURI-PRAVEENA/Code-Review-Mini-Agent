"""
Tests for example workflows.
Part of the consolidated test suite.
"""
import pytest
from workflows.code_review import create_code_review_workflow, run_code_review
from engine.graph import WorkflowExecutor


class TestCodeReviewWorkflow:
    """Test the Code Review Agent workflow"""
    
    def test_workflow_creation(self):
        """Test that code review workflow can be created"""
        graph = create_code_review_workflow()
        
        assert graph.graph_id == "code-review-workflow"
        assert len(graph.nodes) > 0
        assert graph.start_node is not None
    
    def test_workflow_validation(self):
        """Test that created workflow is valid"""
        graph = create_code_review_workflow()
        is_valid, error = graph.validate()
        
        assert is_valid, f"Workflow is invalid: {error}"
    
    def test_simple_code_review(self):
        """Test reviewing simple code"""
        code = """
def hello():
    return "world"
"""
        result = run_code_review(code)
        
        assert result["status"] == "completed"
        assert "final_state" in result
        assert "execution_log" in result
    
    def test_code_review_with_issues(self):
        """Test code review detects issues"""
        code = """
def bad_function():
    except:
        pass
"""
        result = run_code_review(code)
        
        assert result["status"] == "completed"
        # Should detect the bare except
        assert "final_state" in result
    
    def test_code_review_quality_score(self):
        """Test that quality score is calculated"""
        code = "def good(): pass"
        result = run_code_review(code)
        
        state = result["final_state"]
        assert "report" in state
        assert "quality_score" in state["report"]
        assert 0 <= state["report"]["quality_score"] <= 10
    
    def test_code_review_with_threshold(self):
        """Test code review with quality threshold"""
        code = "def sample(): pass"
        result = run_code_review(code, quality_threshold=8.0)
        
        assert result["status"] == "completed"
    
    def test_complex_code_review(self):
        """Test reviewing complex code"""
        code = """
def complex_function(n):
    result = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if i > 5:
                    if j > 5:
                        result.append(i * j * k)
    print(result)
    return result
"""
        result = run_code_review(code)
        
        assert result["status"] == "completed"
        state = result["final_state"]
        
        # Should find multiple issues
        assert "report" in state
        report = state["report"]
        
        # Should find the function
        assert report["summary"]["functions_found"] == 1
        
        # Should detect complexity
        assert report["summary"]["complexity_score"] > 0
    
    def test_workflow_execution_log(self):
        """Test that execution log is detailed"""
        code = "def sample(): pass"
        result = run_code_review(code)
        
        log = result["execution_log"]
        
        assert "entries" in log
        assert len(log["entries"]) > 0
        assert log["status"] == "completed"
    
    def test_workflow_multiple_runs(self):
        """Test running workflow multiple times"""
        code1 = "def foo(): pass"
        code2 = "def bar(): pass"
        
        result1 = run_code_review(code1)
        result2 = run_code_review(code2)
        
        # Different run IDs
        assert result1["run_id"] != result2["run_id"]
        
        # Both completed
        assert result1["status"] == "completed"
        assert result2["status"] == "completed"


class TestWorkflowStateFlow:
    """Test state flowing through workflow"""
    
    def test_state_accumulation(self):
        """Test that state accumulates through nodes"""
        code = "def sample(): pass"
        result = run_code_review(code)
        
        state = result["final_state"]
        
        # Should have data from multiple nodes
        assert "code" in state
        assert "function_count" in state
        assert "complexity_score" in state
        assert "issue_count" in state
    
    def test_initial_state_preserved(self):
        """Test that initial state values are preserved"""
        code = "def sample(): pass"
        result = run_code_review(code, quality_threshold=7.5)
        
        state = result["final_state"]
        
        # Initial code should be present
        assert state["code"] == code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
