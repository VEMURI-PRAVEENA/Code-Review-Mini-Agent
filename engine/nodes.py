"""
Node definitions for workflow execution.
"""
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod
import asyncio

class Node(ABC):
    """Base class for workflow nodes"""
    
    def __init__(self, node_id: str, node_type: str = "standard"):
        self.node_id = node_id
        self.node_type = node_type
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the node and return updated state"""
        pass
    
    async def execute_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Async execution - override for long-running operations"""
        return self.execute(state)


class FunctionNode(Node):
    """Node that executes a Python function"""
    
    def __init__(
        self,
        node_id: str,
        func: Callable,
        state_keys: Optional[Dict[str, str]] = None,
        output_key: Optional[str] = None,
        node_type: str = "standard"
    ):
        super().__init__(node_id, node_type)
        self.func = func
        # Maps state keys to function parameter names
        self.state_keys = state_keys or {}
        # Key to store function output in state
        self.output_key = output_key or f"{node_id}_result"
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the function with state values"""
        try:
            # Build function arguments from state
            kwargs = {}
            for state_key, param_name in self.state_keys.items():
                if state_key in state:
                    kwargs[param_name] = state[state_key]
            
            # Call function
            result = self.func(**kwargs)
            
            # Update state with result
            new_state = state.copy()
            if isinstance(result, dict):
                new_state.update(result)
            else:
                new_state[self.output_key] = result
            
            return new_state
        
        except Exception as e:
            raise RuntimeError(f"Node '{self.node_id}' failed: {str(e)}")


class ToolCallNode(Node):
    """Node that calls a tool from the registry"""
    
    def __init__(
        self,
        node_id: str,
        tool_name: str,
        registry,
        state_keys: Optional[Dict[str, str]] = None,
        output_key: Optional[str] = None
    ):
        super().__init__(node_id, "standard")
        self.tool_name = tool_name
        self.registry = registry
        self.state_keys = state_keys or {}
        self.output_key = output_key or f"{node_id}_result"
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool from the registry"""
        try:
            # Build tool arguments from state
            kwargs = {}
            for state_key, param_name in self.state_keys.items():
                if state_key in state:
                    kwargs[param_name] = state[state_key]
            
            # Call tool
            result = self.registry.call(self.tool_name, **kwargs)
            
            # Update state with result
            new_state = state.copy()
            if isinstance(result, dict):
                new_state.update(result)
            else:
                new_state[self.output_key] = result
            
            return new_state
        
        except Exception as e:
            raise RuntimeError(f"Tool node '{self.node_id}' failed: {str(e)}")


class DecisionNode(Node):
    """Node that branches based on state condition"""
    
    def __init__(
        self,
        node_id: str,
        condition: Callable[[Dict[str, Any]], str],
        branches: Dict[str, str]  # condition_result -> next_node_id
    ):
        super().__init__(node_id, "decision")
        self.condition = condition
        self.branches = branches
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate condition and determine next node"""
        try:
            # Evaluate condition
            result = self.condition(state)
            
            # Validate branch exists
            if result not in self.branches:
                raise ValueError(f"No branch for condition result: {result}")
            
            # Return state unchanged, next node determined by graph engine
            return state
        
        except Exception as e:
            raise RuntimeError(f"Decision node '{self.node_id}' failed: {str(e)}")
    
    def get_next_node(self, state: Dict[str, Any]) -> str:
        """Get the next node based on state condition"""
        result = self.condition(state)
        return self.branches.get(result, None)


class LoopNode(Node):
    """Node that can loop back to a previous node"""
    
    def __init__(
        self,
        node_id: str,
        condition: Callable[[Dict[str, Any]], bool],
        loop_back_to: str
    ):
        super().__init__(node_id, "loop")
        self.condition = condition
        self.loop_back_to = loop_back_to
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Check if loop condition is met"""
        return state
    
    def should_loop(self, state: Dict[str, Any]) -> bool:
        """Check if we should loop back"""
        try:
            return self.condition(state)
        except Exception as e:
            raise RuntimeError(f"Loop condition failed: {str(e)}")


class BatchNode(Node):
    """Node that processes multiple items from state"""
    
    def __init__(
        self,
        node_id: str,
        func: Callable,
        input_list_key: str,
        output_key: str = None
    ):
        super().__init__(node_id, "standard")
        self.func = func
        self.input_list_key = input_list_key
        self.output_key = output_key or f"{node_id}_results"
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process list of items"""
        try:
            items = state.get(self.input_list_key, [])
            results = [self.func(item) for item in items]
            
            new_state = state.copy()
            new_state[self.output_key] = results
            return new_state
        
        except Exception as e:
            raise RuntimeError(f"Batch node '{self.node_id}' failed: {str(e)}")


class NodeBuilder:
    """Helper to build nodes fluently"""
    
    @staticmethod
    def function_node(
        node_id: str,
        func: Callable,
        state_keys: Optional[Dict[str, str]] = None,
        output_key: Optional[str] = None
    ) -> FunctionNode:
        """Build a function node"""
        return FunctionNode(node_id, func, state_keys, output_key)
    
    @staticmethod
    def tool_node(
        node_id: str,
        tool_name: str,
        registry,
        state_keys: Optional[Dict[str, str]] = None,
        output_key: Optional[str] = None
    ) -> ToolCallNode:
        """Build a tool call node"""
        return ToolCallNode(node_id, tool_name, registry, state_keys, output_key)
    
    @staticmethod
    def decision_node(
        node_id: str,
        condition: Callable,
        branches: Dict[str, str]
    ) -> DecisionNode:
        """Build a decision node"""
        return DecisionNode(node_id, condition, branches)
    
    @staticmethod
    def loop_node(
        node_id: str,
        condition: Callable,
        loop_back_to: str
    ) -> LoopNode:
        """Build a loop node"""
        return LoopNode(node_id, condition, loop_back_to)
