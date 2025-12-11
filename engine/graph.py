"""
Core graph engine for workflow execution.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import asyncio
from .nodes import Node, DecisionNode, LoopNode
from .types import ExecutionStatus

class WorkflowGraph:
    """
    Workflow graph that connects nodes and manages execution.
    """
    
    def __init__(self, graph_id: str):
        self.graph_id = graph_id
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, str] = {}  # node_id -> next_node_id
        self.start_node: Optional[str] = None
        self.created_at = datetime.now()
    
    def add_node(self, node: Node, is_start: bool = False) -> "WorkflowGraph":
        """Add a node to the graph"""
        if node.node_id in self.nodes:
            raise ValueError(f"Node '{node.node_id}' already exists")
        
        self.nodes[node.node_id] = node
        
        if is_start:
            if self.start_node is not None:
                raise ValueError("Start node already set")
            self.start_node = node.node_id
        
        return self
    
    def add_edge(self, from_node: str, to_node: str) -> "WorkflowGraph":
        """Add an edge between nodes"""
        if from_node not in self.nodes:
            raise ValueError(f"Node '{from_node}' not found")
        if to_node not in self.nodes:
            raise ValueError(f"Node '{to_node}' not found")
        
        self.edges[from_node] = to_node
        return self
    
    def set_start_node(self, node_id: str) -> "WorkflowGraph":
        """Set the starting node"""
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' not found")
        self.start_node = node_id
        return self
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate graph structure.
        Returns (is_valid, error_message)
        """
        if not self.start_node:
            return False, "No start node defined"
        
        if not self.nodes:
            return False, "No nodes defined"
        
        if self.start_node not in self.nodes:
            return False, f"Start node '{self.start_node}' not found"
        
        # Check all edges point to valid nodes
        for from_node, to_node in self.edges.items():
            if from_node not in self.nodes:
                return False, f"Edge source '{from_node}' not found"
            if to_node not in self.nodes:
                return False, f"Edge target '{to_node}' not found"
        
        # Check for disconnected nodes (optional warning)
        connected = set()
        visited = set()
        to_visit = [self.start_node]
        
        while to_visit:
            node_id = to_visit.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            connected.add(node_id)
            
            if node_id in self.edges:
                to_visit.append(self.edges[node_id])
        
        # Allow disconnected nodes (might be intentional)
        
        return True, None
    
    def get_next_node(self, current_node_id: str, state: Dict[str, Any]) -> Optional[str]:
        """Get the next node to execute"""
        node = self.nodes.get(current_node_id)
        
        # Handle decision nodes
        if isinstance(node, DecisionNode):
            return node.get_next_node(state)
        
        # Handle loop nodes
        if isinstance(node, LoopNode):
            if node.should_loop(state):
                return node.loop_back_to
            else:
                return self.edges.get(current_node_id)
        
        # Regular node
        return self.edges.get(current_node_id)


class ExecutionLog:
    """Log of a workflow execution"""
    
    def __init__(self, run_id: str, graph_id: str):
        self.run_id = run_id
        self.graph_id = graph_id
        self.status = ExecutionStatus.PENDING
        self.entries: List[Dict[str, Any]] = []
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.state_history: List[Dict[str, Any]] = []
        self.error: Optional[str] = None
    
    def add_entry(
        self,
        node_id: str,
        action: str,
        details: Dict[str, Any] = None,
        error: Optional[str] = None
    ):
        """Add an entry to the log"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "node_id": node_id,
            "action": action,
            "details": details or {},
            "error": error
        }
        self.entries.append(entry)
    
    def save_state(self, state: Dict[str, Any]):
        """Save state snapshot"""
        self.state_history.append({
            "timestamp": datetime.now().isoformat(),
            "state": state.copy()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log to dictionary"""
        return {
            "run_id": self.run_id,
            "graph_id": self.graph_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "entries": self.entries,
            "state_history_length": len(self.state_history)
        }


class WorkflowExecutor:
    """Executes a workflow graph"""
    
    def __init__(self, graph: WorkflowGraph):
        self.graph = graph
        self.executions: Dict[str, ExecutionLog] = {}
    
    def execute(
        self,
        initial_state: Dict[str, Any],
        run_id: Optional[str] = None,
        max_iterations: int = 100
    ) -> Tuple[Dict[str, Any], ExecutionLog]:
        """
        Execute the workflow synchronously.
        Returns (final_state, execution_log)
        """
        if run_id is None:
            run_id = str(uuid.uuid4())
        
        # Validate graph
        is_valid, error = self.graph.validate()
        if not is_valid:
            raise ValueError(f"Invalid graph: {error}")
        
        # Initialize execution log
        log = ExecutionLog(run_id, self.graph.graph_id)
        self.executions[run_id] = log
        
        log.status = ExecutionStatus.RUNNING
        log.started_at = datetime.now()
        log.save_state(initial_state)
        
        current_state = initial_state.copy()
        current_node_id = self.graph.start_node
        iteration_count = 0
        
        try:
            while current_node_id is not None and iteration_count < max_iterations:
                iteration_count += 1
                
                # Get node
                node = self.graph.nodes.get(current_node_id)
                if node is None:
                    log.add_entry(
                        current_node_id,
                        "error",
                        error=f"Node '{current_node_id}' not found"
                    )
                    break
                
                log.add_entry(current_node_id, "execute_start")
                
                try:
                    # Execute node
                    current_state = node.execute(current_state)
                    log.add_entry(current_node_id, "execute_success")
                    log.save_state(current_state)
                    
                except Exception as e:
                    error_msg = str(e)
                    log.add_entry(
                        current_node_id,
                        "execute_error",
                        error=error_msg
                    )
                    log.error = error_msg
                    raise
                
                # Get next node
                next_node_id = self.graph.get_next_node(current_node_id, current_state)
                log.add_entry(
                    current_node_id,
                    "next_node",
                    {"next": next_node_id}
                )
                current_node_id = next_node_id
            
            if iteration_count >= max_iterations:
                log.add_entry(
                    "system",
                    "max_iterations_reached",
                    {"max": max_iterations}
                )
                log.error = f"Workflow exceeded max iterations ({max_iterations})"
            
            log.status = ExecutionStatus.COMPLETED
            log.completed_at = datetime.now()
        
        except Exception as e:
            log.status = ExecutionStatus.FAILED
            log.completed_at = datetime.now()
            log.error = str(e)
            raise
        
        return current_state, log
    
    async def execute_async(
        self,
        initial_state: Dict[str, Any],
        run_id: Optional[str] = None,
        max_iterations: int = 100
    ) -> Tuple[Dict[str, Any], ExecutionLog]:
        """
        Execute the workflow asynchronously.
        Returns (final_state, execution_log)
        """
        if run_id is None:
            run_id = str(uuid.uuid4())
        
        # Validate graph
        is_valid, error = self.graph.validate()
        if not is_valid:
            raise ValueError(f"Invalid graph: {error}")
        
        # Initialize execution log
        log = ExecutionLog(run_id, self.graph.graph_id)
        self.executions[run_id] = log
        
        log.status = ExecutionStatus.RUNNING
        log.started_at = datetime.now()
        log.save_state(initial_state)
        
        current_state = initial_state.copy()
        current_node_id = self.graph.start_node
        iteration_count = 0
        
        try:
            while current_node_id is not None and iteration_count < max_iterations:
                iteration_count += 1
                
                # Get node
                node = self.graph.nodes.get(current_node_id)
                if node is None:
                    log.add_entry(
                        current_node_id,
                        "error",
                        error=f"Node '{current_node_id}' not found"
                    )
                    break
                
                log.add_entry(current_node_id, "execute_start")
                
                try:
                    # Execute node asynchronously
                    current_state = await node.execute_async(current_state)
                    log.add_entry(current_node_id, "execute_success")
                    log.save_state(current_state)
                
                except Exception as e:
                    error_msg = str(e)
                    log.add_entry(
                        current_node_id,
                        "execute_error",
                        error=error_msg
                    )
                    log.error = error_msg
                    raise
                
                # Get next node
                next_node_id = self.graph.get_next_node(current_node_id, current_state)
                log.add_entry(
                    current_node_id,
                    "next_node",
                    {"next": next_node_id}
                )
                current_node_id = next_node_id
            
            if iteration_count >= max_iterations:
                log.add_entry(
                    "system",
                    "max_iterations_reached",
                    {"max": max_iterations}
                )
                log.error = f"Workflow exceeded max iterations ({max_iterations})"
            
            log.status = ExecutionStatus.COMPLETED
            log.completed_at = datetime.now()
        
        except Exception as e:
            log.status = ExecutionStatus.FAILED
            log.completed_at = datetime.now()
            log.error = str(e)
            raise
        
        return current_state, log
    
    def get_execution(self, run_id: str) -> Optional[ExecutionLog]:
        """Get execution log by run ID"""
        return self.executions.get(run_id)
