"""
Type definitions and constants for the workflow engine.
"""
from typing import Callable, Dict, Any, Optional
from enum import Enum

# Node execution result
class NodeResult:
    """Result of a node execution"""
    def __init__(self, next_node: Optional[str], state: Dict[str, Any], error: Optional[str] = None):
        self.next_node = next_node
        self.state = state
        self.error = error
        self.success = error is None

# Tool function signature
ToolFunc = Callable[..., Any]

class ExecutionStatus(str, Enum):
    """Status of a workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class NodeType(str, Enum):
    """Type of node operation"""
    STANDARD = "standard"
    DECISION = "decision"
    LOOP = "loop"
