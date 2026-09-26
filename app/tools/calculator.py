import ast
import operator
from typing import Any, Union
from pydantic import BaseModel, Field

from app.tools.base import BaseTool
from app.models.tool import CalculatorResult


class CalculatorInput(BaseModel):
    expression: str = Field(
        description="Mathematical expression containing numbers, parentheses, and operators: +, -, *, /, %, **"
    )


class SafeCalculator(BaseTool):
    """
    Safe mathematical evaluator using Python's Abstract Syntax Tree (AST).
    Prevents arbitrary code execution by strictly allowing only basic arithmetic operations.
    """

    name: str = "calculator"
    description: str = (
        "Perform precise, safe mathematical calculations. Supports arithmetic expressions "
        "including +, -, *, /, %, **, and parentheses. Use this for derived ratios, percentages, and metrics."
    )
    input_schema = CalculatorInput
    output_schema = CalculatorResult

    # Allowed operators mapping
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _eval_node(self, node: ast.AST) -> Union[int, float]:
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)

        elif isinstance(node, ast.Constant):  # Python 3.8+ numeric literal
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value)}")

        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("Division by zero in mathematical expression.")

            return self.OPERATORS[op_type](left, right)

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            return self.OPERATORS[op_type](operand)

        else:
            raise ValueError(f"Disallowed expression element: {type(node).__name__}")

    async def _execute(self, inputs: CalculatorInput) -> CalculatorResult:
        expr = inputs.expression.strip()
        if not expr:
            raise ValueError("Empty mathematical expression.")

        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid mathematical syntax in expression '{expr}': {str(e)}")

        raw_result = self._eval_node(tree)
        rounded_result = round(float(raw_result), 4)

        return CalculatorResult(
            expression=expr,
            result=rounded_result,
            formatted=f"{expr} = {rounded_result}"
        )
