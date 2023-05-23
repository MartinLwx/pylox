from loguru import logger
from tokens import TokenType, Token
from expr import (
    ExprVisitor,
    Literal,
    Grouping,
    Expr,
    Unary,
    Binary,
    Print,
    Expression,
    Var,
    Variable,
    Assign,
)
from errors import InterpreterError
from environment import Environment


class Interpreter(ExprVisitor):
    environment: Environment = Environment()

    def _check_number_operand(self, operator: Token, operand):
        if isinstance(operator, float):
            return
        raise InterpreterError(operator, "Operand must be a number")

    def _check_number_operands(self, operator: Token, left, right):
        if isinstance(left, float) and isinstance(right, float):
            return

        raise InterpreterError(operator, "Operands must be numbers")

    def _evaluate(self, expr: Expr | Print | Expression):
        return self.visit(expr)

    def _is_truthy(self, obj) -> bool:
        """only false/nil are falsey, and everything else is truthy"""
        if obj is None:
            return False
        if isinstance(obj, bool) and not obj:
            return False

        return True

    def _is_equal(self, left, right) -> bool:
        if left is None and right is None:
            return True
        if left is None:
            return False
        return left == right

    def visit_Literal(self, expr: Literal):
        return expr.value

    def visit_Grouping(self, expr: Grouping):
        return self._evaluate(expr.expression)

    def visit_Unary(self, expr: Unary):
        right = self._evaluate(expr.right)

        match expr.operator.type:
            case TokenType.BANG:
                return not self._is_truthy(right)
            case TokenType.MINUS:
                self._check_number_operand(expr.operator, right)
                return -right

        # unreachable
        return None

    def visit_Binary(self, expr: Binary):
        # evaluate the operands in left-to-right order
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)

        match expr.operator.type:
            case TokenType.GREATER:
                self._check_number_operands(expr.operator, left, right)
                return left > right
            case TokenType.GREATER_EQUAL:
                self._check_number_operands(expr.operator, left, right)
                return left >= right
            case TokenType.LESS:
                self._check_number_operands(expr.operator, left, right)
                return left < right
            case TokenType.LESS_EQUAL:
                self._check_number_operands(expr.operator, left, right)
                return left <= right
            case TokenType.MINUS:
                self._check_number_operands(expr.operator, left, right)
                return left - right
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return left + right
                elif isinstance(left, str) and isinstance(right, str):
                    return left + right
                raise InterpreterError(
                    expr.operator, "Operands must be two numbers or two strings."
                )
            case TokenType.SLASH:
                self._check_number_operands(expr.operator, left, right)
                return left / right
            case TokenType.STAR:
                self._check_number_operands(expr.operator, left, right)
                return left * right
            case TokenType.BANG_EQUAL:
                return not self._is_equal(left, right)
            case TokenType.EQUAL_EQUAL:
                return self._is_equal(left, right)

        # unreachable
        return None

    def visit_Expression(self, stmt: Expression):
        # statements produce no values
        self._evaluate(stmt.expression)

        return None

    def visit_Print(self, stmt: Print):
        # statements produce no values
        value = self._evaluate(stmt.expression)

        print(self.stringify(value))

        return None

    def visit_Var(self, stmt: Var):
        value = None
        if stmt.initializer:
            value = self._evaluate(stmt.initializer)

        self.environment._define(stmt.name.lexeme, value)

    def visit_Variable(self, expr: Variable):
        return self.environment.get(expr.name)

    def visit_Assign(self, expr: Assign):
        value = self._evaluate(expr.value)
        self.environment._assign(expr.name, value)
        return value

    def stringify(self, val) -> str:
        if val is None:
            return "nil"
        if isinstance(val, float):
            return str(val).removesuffix(".0")

        return str(val)

    def interpret(self, stmts: list[Print | Expression]):
        try:
            for stmt in stmts:
                self._evaluate(stmt)
        except InterpreterError as e:
            return e
