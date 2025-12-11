"""
Example workflow: Code Review Agent
Demonstrates a complete workflow with branching and looping.
"""
from typing import Dict, Any
from ..engine.graph import WorkflowGraph, WorkflowExecutor
from ..engine.nodes import NodeBuilder
from ..engine.tools import get_registry


def create_code_review_workflow() -> WorkflowGraph:
    """
    Create a code review workflow that:
    1. Extracts functions from code
    2. Checks complexity
    3. Detects issues
    4. Suggests improvements
    5. Calculates quality score
    6. Loops until quality_score >= threshold (optional)
    """
    registry = get_registry()
    graph = WorkflowGraph("code-review-workflow")
    
    # Node 1: Extract Functions
    extract_node = NodeBuilder.tool_node(
        "extract_functions",
        "extract_functions",
        registry,
        state_keys={"code": "code"},
        output_key="functions_data"
    )
    graph.add_node(extract_node, is_start=True)
    
    # Node 2: Check Complexity
    complexity_node = NodeBuilder.tool_node(
        "check_complexity",
        "check_complexity",
        registry,
        state_keys={"code": "code"},
        output_key="complexity_data"
    )
    graph.add_node(complexity_node)
    graph.add_edge("extract_functions", "check_complexity")
    
    # Node 3: Detect Issues
    detect_node = NodeBuilder.tool_node(
        "detect_issues",
        "detect_issues",
        registry,
        state_keys={"code": "code"},
        output_key="issues_data"
    )
    graph.add_node(detect_node)
    graph.add_edge("check_complexity", "detect_issues")
    
    # Node 4: Suggest Improvements
    suggest_node = NodeBuilder.tool_node(
        "suggest_improvements",
        "suggest_improvements",
        registry,
        state_keys={
            "code": "code",
            "issues": "issues"
        },
        output_key="suggestions_data"
    )
    graph.add_node(suggest_node)
    graph.add_edge("detect_issues", "suggest_improvements")
    
    # Node 5: Calculate Quality Score
    score_node = NodeBuilder.tool_node(
        "calculate_score",
        "calculate_score",
        registry,
        state_keys={
            "complexity_score": "complexity_score",
            "issue_count": "issue_count",
            "has_critical_issues": "has_critical_issues",
            "suggestion_count": "suggestion_count"
        },
        output_key="quality_result"
    )
    graph.add_node(score_node)
    graph.add_edge("suggest_improvements", "calculate_score")
    
    # Node 6: Final Report (end node)
    def generate_report(
        quality_score: float,
        rating: str,
        function_count: int,
        complexity_score: float,
        issue_count: int,
        suggestion_count: int
    ) -> Dict[str, Any]:
        """Generate final review report"""
        return {
            "report": {
                "overall_quality_score": quality_score,
                "rating": rating,
                "summary": {
                    "functions_found": function_count,
                    "complexity_score": complexity_score,
                    "total_issues": issue_count,
                    "improvement_suggestions": suggestion_count
                }
            }
        }
    
    report_node = NodeBuilder.function_node(
        "generate_report",
        generate_report,
        state_keys={
            "quality_score": "quality_score",
            "rating": "rating",
            "function_count": "function_count",
            "complexity_score": "complexity_score",
            "issue_count": "issue_count",
            "suggestion_count": "suggestion_count"
        },
        output_key="final_report"
    )
    graph.add_node(report_node)
    graph.add_edge("calculate_score", "generate_report")
    
    return graph


def run_code_review(code: str, quality_threshold: float = 7.0) -> Dict[str, Any]:
    """
    Run the code review workflow on provided code.
    
    Args:
        code: Python code to review
        quality_threshold: Quality score threshold (0-10)
    
    Returns:
        Dictionary with final state and execution log
    """
    graph = create_code_review_workflow()
    executor = WorkflowExecutor(graph)
    
    initial_state = {
        "code": code,
        "quality_threshold": quality_threshold,
        "iteration": 0
    }
    
    final_state, execution_log = executor.execute(initial_state)
    
    return {
        "final_state": final_state,
        "execution_log": execution_log.to_dict(),
        "run_id": execution_log.run_id,
        "status": execution_log.status.value,
        "error": execution_log.error
    }


# Example usage
if __name__ == "__main__":
    sample_code = '''
def slow_function(n):
    result = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result.append(i * j * k)
    print(result)
    return result

def process_data(data):
    if data:
        if len(data) > 10:
            if data[0] > 5:
                print("Processing")
            else:
                print("Skipping")
    return data
    '''
    
    result = run_code_review(sample_code, quality_threshold=7.0)
    
    print("=" * 60)
    print("CODE REVIEW RESULTS")
    print("=" * 60)
    print(f"Run ID: {result['run_id']}")
    print(f"Status: {result['status']}")
    
    if "report" in result["final_state"]:
        report = result["final_state"]["report"]
        print(f"\nQuality Score: {report['overall_quality_score']}/10")
        print(f"Rating: {report['rating']}")
        print(f"\nSummary:")
        for key, value in report['summary'].items():
            print(f"  {key}: {value}")
    
    if result['error']:
        print(f"\nError: {result['error']}")
