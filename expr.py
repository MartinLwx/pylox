from typing import Any
from tokens import Token


# Expressions
class Expr:
    ...


class Unary(Expr):
    def __init__(self, operator: Token, right: Expr):
        self.operator = operator
        self.right = right


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right


class Literal(Expr):
    def __init__(self, value: Any):
        self.value = value


class Grouping(Expr):
    def __init__(self, expression: Expr):
        self.expression = expression


class Variable(Expr):
    def __init__(self, name: Token):
        self.name = name


class Assign(Expr):
    def __init__(self, name: Token, value: Expr):
        self.name = name
        self.value = value


# Statements
class Stmt:
    ...


class Expression(Stmt):
    def __init__(self, expr: Expr):
        self.expression = expr


class Print(Stmt):
    def __init__(self, expr: Expr):
        self.expression = expr


class Var(Stmt):
    def __init__(self, name: Token, initializer: Expr | None):
        self.name = name
        self.initializer = initializer


class Block(Stmt):
    def __init__(self, statements: list[Stmt]):
        self.statements = statements


class IfStmt(Stmt):
    def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Stmt | None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch


# use visitor pattern to print a ast
class ExprVisitor:
    def visit(self, expr: Expr | Stmt):
        method_name = f"visit_{type(expr).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            method = self.generic_visit

        return method(expr)

    def generic_visit(self, expr):
        raise RuntimeError(f"No {type(expr).__name__} method")
