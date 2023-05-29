from loguru import logger
from expr import (
    ExprVisitor,
    Block,
    Function,
    Stmt,
    Expr,
    Var,
    Variable,
    Assign,
    Expression,
    IfStmt,
    Print,
    ReturnStmt,
    WhileStmt,
    Binary,
    Call,
    Grouping,
    Literal,
    Logical,
    Unary,
)
from interpreter import Interpreter
from tokens import Token
from errors import InterpreterError


class Resolver(ExprVisitor):
    def __init__(self, interpreter: Interpreter):
        self.interpreter = interpreter
        self._scopes: list[dict[str, bool]] = []

    def _resolve(self, statements: list[Expr] | list[Stmt] | Expr | Stmt):
        """Resolve each statement inside"""
        logger.debug(f"Resolve {type(statements)}, Current scopes: {self._scopes}")
        if isinstance(statements, list):
            for stmt in statements:
                self.visit(stmt)
        else:
            self.visit(statements)

    def _resolve_local(self, expr: Expr, name: Token):
        for i in reversed(range(len(self._scopes))):
            if name.lexeme in self._scopes[i]:
                logger.debug(f"Find {name.lexeme} in scope {i}")
                self.interpreter._resolve(expr, len(self._scopes) - 1 - i)
                return

    def _resolve_function(self, stmt: Function):
        logger.debug(f"Resolve Function: {stmt.name}")
        self._begin_scope()
        for param in stmt.params:
            self._declare(param)
            self._define(param)
        # in static analysis, we immediately traverse into the body
        self._resolve(stmt.body.statements)
        self._end_scope()

    def _begin_scope(self):
        self._scopes.append({})

    def _end_scope(self):
        self._scopes.pop()

    def _declare(self, name: Token):
        """Declaration adds the variable to the innermost scope"""
        if not self._scopes:
            return

        # this variable is not ready yet, that is, exists but is unavailable
        self._scopes[-1][name.lexeme] = False

    def _define(self, name: Token):
        if not self._scopes:
            return

        # that is, fully initialized and available
        self._scopes[-1][name.lexeme] = True

    def visit_Block(self, stmt: Block):
        self._begin_scope()
        self._resolve(stmt.statements)
        self._end_scope()

        return None

    def visit_Var(self, stmt: Var):
        self._declare(stmt.name)
        if stmt.initializer:
            self._resolve(stmt.initializer)
        self._define(stmt.name)

        return None

    def visit_Variable(self, expr: Variable):
        if self._scopes and not self._scopes[-1].get(expr.name.lexeme, True):
            # TODO: Lox.error?
            raise InterpreterError(
                expr.name, "Can't read local variable in its own initializer."
            )
        self._resolve_local(expr, expr.name)

        return None

    def visit_Assign(self, expr: Assign):
        self._resolve(expr.value)
        self._resolve_local(expr, expr.name)

        return None

    def visit_Function(self, stmt: Function):
        # declare and define the name of the function in the current scope
        self._declare(stmt.name)
        self._define(stmt.name)

        # note that the function can recursively refer to itself
        self._resolve_function(stmt)

        return None

    def visit_Expression(self, stmt: Expression):
        self._resolve(stmt.expression)

        return None

    def visit_IfStmt(self, stmt: IfStmt):
        # in static analysis, there is no control flow
        # , we resolve the condition/then_branch/else_branch
        self._resolve(stmt.condition)
        self._resolve(stmt.then_branch)
        if stmt.else_branch:
            self._resolve(stmt.else_branch)

        return None

    def visit_Print(self, stmt: Print):
        logger.debug(f"Resolve Print: {stmt.expression}")
        self._resolve(stmt.expression)

        return None

    def visit_ReturnStmt(self, stmt: ReturnStmt):
        if stmt.value:
            self._resolve(stmt.value)

        return None

    def visit_WhileStmt(self, stmt: WhileStmt):
        self._resolve(stmt.condition)
        self._resolve(stmt.body)

        return None

    def visit_Binary(self, expr: Binary):
        self._resolve(expr.left)
        self._resolve(expr.right)

        return None

    def visit_Call(self, expr: Call):
        self._resolve(expr.callee)

        for argument in expr.arguments:
            self._resolve(argument)

        return None

    def visit_Grouping(self, expr: Grouping):
        self._resolve(expr.expression)

        return None

    def visit_Literal(self, expr: Literal):
        return None

    def visit_Logical(self, expr: Logical):
        # again, we need to resolve each side
        self._resolve(expr.left)
        self._resolve(expr.right)

        return None

    def visit_Unary(self, expr: Unary):
        self._resolve(expr.right)

        return None
