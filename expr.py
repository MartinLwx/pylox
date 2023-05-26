from typing import Any, TYPE_CHECKING
from tokens import Token
from environment import Environment
from errors import ReturnException

if TYPE_CHECKING:
    from interpreter import Interpreter


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


class Logical(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right


class Call(Expr):
    def __init__(self, callee: Expr, paren: Token, arguments: list[Expr]):
        self.callee = callee
        self.paren = paren
        self.arguments = arguments


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


class WhileStmt(Stmt):
    def __init__(self, condition: Expr, body: Stmt):
        self.condition = condition
        self.body = body


class Function(Stmt):
    def __init__(
        self,
        name: Token,
        params: list[Token],
        body: Block,
        closure: Environment | None = None,
    ):
        self.name = name
        self.params = params
        self.body = body
        self.arity = len(self.params)
        self.closure = closure

    def __call__(self, interpreter: "Interpreter", arguments: list[Any]):
        env = Environment(self.closure)
        for i, param in enumerate(self.params):
            env._define(param.lexeme, arguments[i])
        # unwind all the way to where the function call began
        try:
            interpreter._execute_block(self.body.statements, env)
        except ReturnException as e:
            return e.value
        return None


class ReturnStmt(Stmt):
    def __init__(self, keyword: Token, value: Expr | None):
        self.keyword = keyword
        self.value = value


class ExprVisitor:
    def visit(self, expr: Expr | Stmt):
        method_name = f"visit_{type(expr).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            method = self.generic_visit

        return method(expr)

    def generic_visit(self, expr):
        err = f"No {type(expr).__name__} method"
        raise RuntimeError(err)
