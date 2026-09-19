import ast
import operator
import math
import time
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from sovereign.core.capabilities.models import ToolDefinition, ToolImplementation, CapabilityType
from sovereign.infrastructure.tools.workspace import TaskWorkspace, WorkspaceManager
from sovereign.infrastructure.tools.execution_boundary import ExecutionBoundary

class CalculateInput(BaseModel):
    expression: str = Field(description="Mathematical or numerical expression to calculate.")
    variables: Optional[Dict[str, float]] = Field(default_factory=dict, description="Optional variable bindings.")

SAFE_MATH_FUNCS = {
    'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos,
    'tan': math.tan, 'log': math.log, 'log10': math.log10,
    'exp': math.exp, 'fabs': math.fabs, 'floor': math.floor,
    'ceil': math.ceil
}

class SafeMathVisitor(ast.NodeVisitor):
    def __init__(self, variables: Dict[str, float]):
        self.variables = variables or {}

    def visit_Module(self, node):
        if len(node.body) != 1 or not isinstance(node.body[0], ast.Expr):
            raise ValueError("Only a single mathematical expression is allowed.")
        return self.visit(node.body[0].value)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = type(node.op)
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
        }
        if op not in ops:
            raise ValueError(f"Unsupported binary operator: {op.__name__}")
        return ops[op](left, right)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        op = type(node.op)
        if op == ast.UAdd:
            return +operand
        elif op == ast.USub:
            return -operand
        raise ValueError(f"Unsupported unary operator: {op.__name__}")

    def visit_Constant(self, node):
        if not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed.")
        return float(node.value)

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are allowed.")
        func_name = node.func.id
        if func_name not in SAFE_MATH_FUNCS:
            raise ValueError(f"Function '{func_name}' is not allowed.")
        args = [self.visit(arg) for arg in node.args]
        return SAFE_MATH_FUNCS[func_name](*args)
        
    def visit_Name(self, node):
        if node.id == 'pi': return math.pi
        if node.id == 'e': return math.e
        if node.id in self.variables:
            return float(self.variables[node.id])
        raise ValueError(f"Variable '{node.id}' is not defined.")

    def generic_visit(self, node):
        raise ValueError(f"Unsupported syntax construct: {type(node).__name__}")

def get_calculate_tool(
    execution_boundary: Optional[ExecutionBoundary] = None,
    workspace: Optional[TaskWorkspace] = None
) -> ToolImplementation:
    boundary = execution_boundary or ExecutionBoundary()
    ws = workspace or WorkspaceManager().get_or_create("default")

    def handler(inputs: CalculateInput) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            # Parse the expression into an AST
            tree = ast.parse(inputs.expression, mode='exec')
            visitor = SafeMathVisitor(inputs.variables)
            result = visitor.visit(tree)
            
            return {
                "success": True,
                "expression": inputs.expression,
                "result": result,
                "raw_output": str(result),
                "duration_ms": int((time.time() - start_time) * 1000),
                "security_mode": boundary.security_mode.value
            }
        except Exception as e:
            return {
                "success": False,
                "expression": inputs.expression,
                "error": str(e),
                "security_mode": boundary.security_mode.value
            }

    definition = ToolDefinition(
        tool_id="core-calc-001",
        name="calculate",
        description="Performs governed mathematical and numerical calculations within the restricted execution boundary.",
        input_schema=CalculateInput.model_json_schema(),
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "expression": {"type": "string"},
                "result": {"type": ["number", "string", "null"]},
                "security_mode": {"type": "string"}
            }
        },
        capability=CapabilityType.READ_ONLY
    )
    return ToolImplementation(
        definition=definition,
        handler=handler,
        input_model=CalculateInput
    )
