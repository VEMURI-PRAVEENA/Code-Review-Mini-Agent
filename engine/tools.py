"""
Tool registry and built-in tools for workflows.
"""
from typing import Dict, Callable, Any
import re
import time

class ToolRegistry:
    """Registry for workflow tools"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in tools"""
        self.register("extract_functions", extract_functions)
        self.register("check_complexity", check_complexity)
        self.register("detect_issues", detect_issues)
        self.register("suggest_improvements", suggest_improvements)
        self.register("calculate_score", calculate_score)
    
    def register(self, name: str, func: Callable):
        """Register a tool"""
        if name in self.tools:
            raise ValueError(f"Tool '{name}' already registered")
        self.tools[name] = func
    
    def get(self, name: str) -> Callable:
        """Get a tool by name"""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        return self.tools[name]
    
    def call(self, name: str, **kwargs) -> Any:
        """Call a tool with kwargs"""
        tool = self.get(name)
        return tool(**kwargs)
    
    def list_tools(self) -> Dict[str, str]:
        """List available tools"""
        return {name: func.__doc__ or "No description" for name, func in self.tools.items()}


# Built-in tools for Code Review workflow

def extract_functions(code: str) -> Dict[str, Any]:
    """
    Extract function definitions from code.
    Returns list of function names and their line numbers.
    """
    functions = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        if re.match(r'^\s*def\s+(\w+)\s*\(', line):
            match = re.search(r'def\s+(\w+)\s*\(', line)
            if match:
                functions.append({
                    "name": match.group(1),
                    "line": i,
                    "code": line.strip()
                })
    
    return {
        "functions": functions,
        "function_count": len(functions),
        "extraction_status": "success"
    }


def check_complexity(code: str) -> Dict[str, Any]:
    """
    Check code complexity using simple heuristics.
    Looks for: nested loops, long functions, many branches.
    Returns complexity score (0-10).
    """
    lines = code.split('\n')
    
    # Count nesting depth
    max_depth = 0
    current_depth = 0
    for line in lines:
        indent = len(line) - len(line.lstrip())
        current_depth = indent // 4
        max_depth = max(max_depth, current_depth)
    
    # Count branches (if/elif/else)
    branch_count = len(re.findall(r'\b(if|elif|else)\b', code))
    
    # Count loops
    loop_count = len(re.findall(r'\b(for|while)\b', code))
    
    # Simple complexity formula
    complexity_score = min(10, max_depth + (branch_count * 0.5) + (loop_count * 0.5))
    
    return {
        "complexity_score": round(complexity_score, 2),
        "nesting_depth": max_depth,
        "branch_count": branch_count,
        "loop_count": loop_count,
        "is_complex": complexity_score > 6
    }


def detect_issues(code: str) -> Dict[str, Any]:
    """
    Detect basic code issues and anti-patterns.
    Returns list of issues found.
    """
    issues = []
    
    # Check for long lines
    for i, line in enumerate(code.split('\n'), 1):
        if len(line) > 100:
            issues.append({
                "type": "long_line",
                "line": i,
                "message": f"Line {i} is too long ({len(line)} chars)",
                "severity": "warning"
            })
    
    # Check for missing docstrings in functions
    for match in re.finditer(r'def\s+(\w+)\s*\([^)]*\):', code):
        func_name = match.group(1)
        start_pos = match.end()
        # Simple check: no triple quotes after function definition
        if '"""' not in code[start_pos:start_pos+100] and "'''" not in code[start_pos:start_pos+100]:
            issues.append({
                "type": "missing_docstring",
                "function": func_name,
                "message": f"Function '{func_name}' missing docstring",
                "severity": "warning"
            })
    
    # Check for print statements (debugging)
    print_lines = [i for i, line in enumerate(code.split('\n'), 1) if 'print(' in line]
    if print_lines:
        issues.append({
            "type": "debug_print",
            "lines": print_lines,
            "message": f"Found print statements (debugging?)",
            "severity": "info"
        })
    
    # Check for bare except
    if 'except:' in code:
        issues.append({
            "type": "bare_except",
            "message": "Bare except clause found - specify exception type",
            "severity": "error"
        })
    
    return {
        "issues": issues,
        "issue_count": len(issues),
        "critical_count": sum(1 for i in issues if i.get('severity') == 'error'),
        "has_critical_issues": any(i.get('severity') == 'error' for i in issues)
    }


def suggest_improvements(code: str, issues: list) -> Dict[str, Any]:
    """
    Suggest improvements based on detected issues.
    Returns list of actionable suggestions.
    """
    suggestions = []
    
    # Base suggestions
    if any(i['type'] == 'long_line' for i in issues):
        suggestions.append({
            "priority": "high",
            "area": "style",
            "suggestion": "Break long lines into smaller, more readable chunks",
            "effort": "low"
        })
    
    if any(i['type'] == 'missing_docstring' for i in issues):
        suggestions.append({
            "priority": "medium",
            "area": "documentation",
            "suggestion": "Add docstrings to all functions following Google style",
            "effort": "low"
        })
    
    if any(i['type'] == 'debug_print' for i in issues):
        suggestions.append({
            "priority": "medium",
            "area": "debugging",
            "suggestion": "Remove debug print statements or use proper logging",
            "effort": "low"
        })
    
    if any(i['type'] == 'bare_except' for i in issues):
        suggestions.append({
            "priority": "high",
            "area": "error_handling",
            "suggestion": "Specify exception types explicitly in except blocks",
            "effort": "medium"
        })
    
    return {
        "suggestions": suggestions,
        "suggestion_count": len(suggestions),
        "recommended_improvements": [s['suggestion'] for s in suggestions]
    }


def calculate_score(
    complexity_score: float,
    issue_count: int,
    has_critical_issues: bool,
    suggestion_count: int
) -> Dict[str, Any]:
    """
    Calculate overall code quality score (0-10).
    """
    score = 10.0
    
    # Deduct for complexity
    score -= min(3, complexity_score * 0.3)
    
    # Deduct for issues
    score -= min(3, issue_count * 0.2)
    
    # Deduct for critical issues
    if has_critical_issues:
        score -= 2
    
    # Deduct for suggestions
    score -= min(2, suggestion_count * 0.3)
    
    score = max(0, round(score, 2))
    
    return {
        "quality_score": score,
        "rating": _get_rating(score),
        "pass_threshold_7": score >= 7,
        "pass_threshold_8": score >= 8,
        "pass_threshold_5": score >= 5
    }


def _get_rating(score: float) -> str:
    """Get quality rating based on score"""
    if score >= 8:
        return "Excellent"
    elif score >= 7:
        return "Good"
    elif score >= 5:
        return "Fair"
    elif score >= 3:
        return "Poor"
    else:
        return "Critical"


# Global registry instance
_registry = None

def get_registry() -> ToolRegistry:
    """Get or create the global tool registry"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
