import time
from typing import Any
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
    Block,
    Stmt,
    IfStmt,
    Logical,
    WhileStmt,
    Call,
    Function,
    ReturnStmt,
)
from errors import InterpreterError, ReturnException
from environment import Environment
from utils import set_arity


class Interpreter(ExprVisitor):
    # global environment
    globals: Environment = Environment()

    def __init__(self):
        # tracks the current environment
        self.environment = self.globals
        self.globals._define("clock", set_arity(0)(time.time))

    def _check_number_operand(self, operator: Token, operand):
        if isinstance(operator, float):
            return
        raise InterpreterError(operator, "Operand must be a number")

    def _check_number_operands(self, operator: Token, left, right):
        if isinstance(left, float) and isinstance(right, float):
            return

        raise InterpreterError(operator, "Operands must be numbers")

    def _evaluate(self, expr: Expr | Stmt):
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

    def visit_Logical(self, expr: Logical):
        """A logic oprator merely guarantees it will return a value with appropriate truthiness"""
        left = self._evaluate(expr.left)

        if expr.operator.type == TokenType.OR:
            if self._is_truthy(left):
                return left
        else:
            if not self._is_truthy(left):
                return left

        return self._evaluate(expr.right)

    def visit_Call(self, expr: Call):
        callee = self._evaluate(expr.callee)
        arguments: list[Expr] = []
        for argument in expr.arguments:
            arguments.append(self._evaluate(argument))
        logger.debug(
            f"[Call] {callee} with type {type(callee).__name__}, arity: {callee.arity} vs arguments: {len(arguments)}"
        )

        if not callable(callee):
            raise InterpreterError(expr.paren, "Can only call functions and classes")
        if callee.arity != len(arguments):
            raise InterpreterError(
                expr.paren,
                f"Expected {callee.arity} arguments but got {len(arguments)}.",
            )
        if isinstance(callee, Function):
            return callee(self, arguments)
        else:
            # for built-in function
            # python's function is the first-class citizen
            # , so we can just use callee(arguments)
            return callee() if not arguments else callee(arguments)

    def _execute_block(self, statements: list[Stmt], environment: Environment):
        logger.debug("Enter new env")
        previous = self.environment
        try:
            self.environment = environment
            for stmt in statements:
                self._evaluate(stmt)
        finally:
            # restore to previous environment even if an exception is thrown
            logger.debug(f"Restore to env\n: {previous}")
            self.environment = previous

    def visit_Block(self, stmt: Block):
        self._execute_block(stmt.statements, Environment(self.environment))
        return None

    def visit_IfStmt(self, stmt: IfStmt):
        if self._is_truthy(self._evaluate(stmt.condition)):
            self._evaluate(stmt.then_branch)
        elif stmt.else_branch:
            self._evaluate(stmt.else_branch)

        return None

    def visit_WhileStmt(self, stmt: WhileStmt):
        while self._is_truthy(self._evaluate(stmt.condition)):
            self._evaluate(stmt.body)

        return None

    def visit_Function(self, stmt: Function):
        stmt.closure = self.environment
        self.environment._define(stmt.name.lexeme, stmt)

        return None

    def visit_ReturnStmt(self, stmt: ReturnStmt):
        value = None
        # if we have a return value, we evaluate it
        if stmt.value:
            value = self._evaluate(stmt.value)

        raise ReturnException(value)

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
