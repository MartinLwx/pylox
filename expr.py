from typing import Any, TYPE_CHECKING
from tokens import Token
from environment import Environment
from errors import ReturnException, InterpreterError

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


class Get(Expr):
    """For property access in OOP"""

    def __init__(self, obj: Expr, name: Token):
        self.obj = obj
        self.name = name


class Set(Expr):
    """For setter in OOP"""

    def __init__(self, obj: Expr, name: Token, value: Expr):
        self.obj = obj
        self.name = name
        self.value = value


class This(Expr):
    """`This` is a keyword used in OOP"""

    def __init__(self, keyword: Token):
        self.keyword = keyword


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
        is_initializer: bool = False,
    ):
        self.name = name
        self.params = params
        self.body = body
        self.arity = len(self.params)
        self.closure = closure
        self.is_initializer = is_initializer

    def __call__(self, interpreter: "Interpreter", arguments: list[Any]):
        env = Environment(self.closure)
        for i, param in enumerate(self.params):
            env._define(param.lexeme, arguments[i])
        # unwind all the way to where the function call began
        try:
            interpreter._execute_block(self.body.statements, env)
        except ReturnException as e:
            return e.value
        # if this function is an initializer, we forcibly return "this"
        if self.is_initializer and self.closure is not None:
            return self.closure.get_at(0, "this")
        return None

    def bind(self, instance: "Instance"):
        """Create a new env nested inside the method's original closure.
        When the method is called, that will become the parent of the method body's env
        """
        env = Environment(self.closure)
        env._define("this", instance)

        # i.e. we insert a special scope which contains "this"
        # and we only need to change the closure of original's method
        return Function(self.name, self.params, self.body, env, self.is_initializer)


class ReturnStmt(Stmt):
    def __init__(self, keyword: Token, value: Expr | None):
        self.keyword = keyword
        self.value = value


class Class(Stmt):
    def __init__(
        self, name: Token, superclass: Variable | None, methods: list[Function]
    ):
        self.name = name
        self.methods: dict[str, Function] = {}
        self.superclass = superclass
        # use a dict to store all methods, { method_name: method }
        for method in methods:
            self.methods[method.name.lexeme] = method
        # initiate the arity
        initializer = self.find_method("init")
        self.arity = 0 if not initializer else initializer.arity

    def find_method(self, name: str) -> Function | None:
        return self.methods.get(name, None)

    def __repr__(self):
        return self.name.lexeme

    def __call__(self, interpreter: "Interpreter", arguments: list[Any]):
        instance = Instance(self)
        # after creating the instance, we want to find an "init" method
        initializer = self.find_method("init")
        if initializer:
            initializer.bind(instance)(interpreter, arguments)

        return instance


class Instance:
    def __init__(self, klass: Class):
        self.kclass = klass
        self.fields: dict[str, Any] = {}

    def get(self, name: Token):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]
        method = self.kclass.find_method(name.lexeme)
        if method:
            return method.bind(self)
        raise InterpreterError(name, f"Undefined property '{name.lexeme}'.")

    def set(self, name: Token, value: Any):
        self.fields[name.lexeme] = value

    def __repr__(self):
        return f"{self.kclass.name.lexeme} instance"


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
