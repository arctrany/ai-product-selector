"""Condition node implementation using JSONLogic."""

from typing import Any, Dict, Optional

try:
    import jsonlogic
    HAS_JSONLOGIC = True
except ImportError:
    HAS_JSONLOGIC = False
    # Fallback implementation
    class jsonlogic:
        @staticmethod
        def jsonLogic(expr, data):
            """Simple fallback for basic conditions."""
            if isinstance(expr, bool):
                return expr
            if isinstance(expr, dict):
                # Handle simple comparisons
                if ">=" in expr:
                    left, right = expr[">="]
                    left_val = data.get(left["var"]) if isinstance(left, dict) and "var" in left else left
                    return left_val >= right
                elif ">" in expr:
                    left, right = expr[">"]
                    left_val = data.get(left["var"]) if isinstance(left, dict) and "var" in left else left
                    return left_val > right
                elif "==" in expr:
                    left, right = expr["=="]
                    left_val = data.get(left["var"]) if isinstance(left, dict) and "var" in left else left
                    return left_val == right
                elif "and" in expr:
                    return all(jsonlogic.jsonLogic(cond, data) for cond in expr["and"])
                elif "or" in expr:
                    return any(jsonlogic.jsonLogic(cond, data) for cond in expr["or"])
            return True

from ..core.models import WorkflowState
from ..utils.logger import WorkflowLogger
from .base import BaseNode


class ConditionNode(BaseNode):
    """Node that evaluates JSONLogic expressions for conditional branching."""
    
    def execute(self, state: WorkflowState, logger: WorkflowLogger, 
                interrupt: Optional[callable] = None) -> Dict[str, Any]:
        """Evaluate JSONLogic expression."""
        
        expr = self.node_data.get("expr")
        if not expr:
            raise ValueError(f"Condition node {self.node_id} missing expr")
        
        logger.info(f"Evaluating condition expression", 
                   node_id=self.node_id,
                   context={"expression": expr})
        
        try:
            # Prepare data context for JSONLogic evaluation
            # Include both workflow state data and metadata
            context_data = {
                **state.data,
                "metadata": state.metadata,
                "thread_id": state.thread_id,
                "current_node": state.current_node
            }
            
            # Evaluate JSONLogic expression
            result = jsonlogic.jsonLogic(expr, context_data)
            
            logger.info(f"Condition evaluation result: {result}", 
                       node_id=self.node_id,
                       context={"result": result, "result_type": type(result).__name__})
            
            # Return the evaluation result
            return {
                "condition_result": result,
                "condition_expr": expr,
                "evaluation_context": context_data
            }
            
        except Exception as e:
            logger.error(f"Condition evaluation failed: {str(e)}", 
                        node_id=self.node_id,
                        context={"error": str(e), "error_type": type(e).__name__, "expression": expr})
            raise


# Example JSONLogic expressions for testing
EXAMPLE_CONDITIONS = {
    "simple_comparison": {
        ">=": [{"var": "count"}, 100]
    },
    "complex_logic": {
        "and": [
            {">=": [{"var": "count"}, 10]},
            {"<": [{"var": "count"}, 1000]},
            {"==": [{"var": "status"}, "active"]}
        ]
    },
    "data_validation": {
        "and": [
            {"!!": {"var": "products"}},  # products exists and is truthy
            {">": [{"var": "products.length"}, 0]}  # products array has items
        ]
    },
    "error_handling": {
        "or": [
            {"==": [{"var": "status"}, "completed"]},
            {"and": [
                {"==": [{"var": "status"}, "failed"]},
                {"<": [{"var": "retry_count"}, 3]}
            ]}
        ]
    }
}