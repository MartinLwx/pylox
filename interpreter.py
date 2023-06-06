import time
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
    Get,
    Set,
    This,
    Super,
    Function,
    ReturnStmt,
    Class,
    Instance,
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
        self.locals: dict[Expr, int] = {}
        self.globals._define("clock", set_arity(0)(time.time))

    def _check_number_operand(self, operator: Token, operand):
        if isinstance(operand, float):
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

        # in python, True == 1.0 is True, that's not the expected behavior
        return left == right if type(left) == type(right) else False

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
        return self.lookup_variable(expr.name, expr)

    def visit_Assign(self, expr: Assign):
        value = self._evaluate(expr.value)
        distance = self.locals.get(expr)
        if distance is not None:
            self.environment.assign_at(distance, expr.name, value)
        else:
            self.globals._assign(expr.name, value)

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

        if not callable(callee):
            raise InterpreterError(expr.paren, "Can only call functions and classes")
        if callee.arity != len(arguments):
            raise InterpreterError(
                expr.paren,
                f"Expected {callee.arity} arguments but got {len(arguments)}.",
            )
        if isinstance(callee, Function) or isinstance(callee, Class):
            return callee(self, arguments)
        else:
            # for built-in function
            # python's function is the first-class citizen
            # , so we can just use callee(arguments)
            return callee() if not arguments else callee(arguments)

    def visit_Get(self, expr: Get):
        obj = self._evaluate(expr.obj)
        if isinstance(obj, Instance):
            return obj.get(expr.name)
        else:
            raise InterpreterError(expr.name, "Only instances have properties.")

    def visit_Set(self, expr: Set):
        obj = self._evaluate(expr.obj)

        if not isinstance(obj, Instance):
            raise InterpreterError(expr.name, "Only instances have fields.")

        value = self._evaluate(expr.value)
        obj.set(expr.name, value)

        return value

    def visit_This(self, expr: This):
        return self.lookup_variable(expr.keyword, expr)

    def visit_Super(self, expr: Super):
        distance = self.locals.get(
            expr, -1
        )  # use default -1 just to pass the type checker
        assert distance != -1, "This is impossible"
        superclass: Class = self.environment.get_at(distance, "super")
        obj = self.environment.get_at(distance - 1, "this")
        method = superclass.find_method(expr.method.lexeme)

        if method:
            return method.bind(obj)
        else:
            raise InterpreterError(
                expr.method, f"Undefined property '{expr.method.lexeme}'."
            )

    def _execute_block(self, statements: list[Stmt], environment: Environment):
        previous = self.environment
        try:
            self.environment = environment
            for stmt in statements:
                self._evaluate(stmt)
        finally:
            # restore to previous environment even if an exception is thrown
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
        new_function = Function(
            stmt.name, stmt.params, stmt.body, self.environment, stmt.is_initializer
        )
        self.environment._define(stmt.name.lexeme, new_function)

        return None

    def visit_ReturnStmt(self, stmt: ReturnStmt):
        value = None
        # if we have a return value, we evaluate it
        if stmt.value:
            value = self._evaluate(stmt.value)

        raise ReturnException(value)

    def visit_Class(self, stmt: Class):
        superclass = None
        if stmt.superclass:
            # by looking up the variable, we got a class here
            superclass = self._evaluate(stmt.superclass)
            if not isinstance(superclass, Class):
                raise InterpreterError(
                    stmt.superclass.name, "Superclass must be a class."
                )
            stmt._superclass = superclass
            stmt.update_arity()

        self.environment._define(stmt.name.lexeme, None)

        if stmt.superclass:
            # store a reference to the superclass
            self.environment = Environment(self.environment)
            self.environment._define("super", superclass)

        for method in stmt.methods.values():
            method.closure = self.environment
            if method.name.lexeme == "init":
                method.is_initializer = True

        if stmt.superclass:
            self.environment = self.environment.enclosing

        self.environment._assign(stmt.name, stmt)

        return None

    def stringify(self, val) -> str:
        if val is None:
            return "nil"
        if isinstance(val, float):
            return str(val).removesuffix(".0")
        if (
            callable(val)
            and not isinstance(val, Function)
            and not isinstance(val, Class)
        ):
            return "<native fn>"
        # python will print True/False rather then true/false defined in Lox
        if isinstance(val, bool):
            return str(val).lower()

        return str(val)

    def _resolve(self, expr: Expr, depth: int):
        self.locals[expr] = depth

    def lookup_variable(self, name: Token, expr: Expr):
        """Lookup variable based on it's distance, or it may be a global variable"""
        distance = self.locals.get(expr, None)
        # WARNING: do not write `if distance` here. Because when it returns 0,
        # which means the variable lives in the innermost scope.
        # And `if 0` will misinterpret this
        if distance is not None:
            return self.environment.get_at(distance, name.lexeme)
        else:
            return self.globals.get(name)

    def interpret(self, stmts: list[Stmt] | list[Expr]):
        try:
            for stmt in stmts:
                self._evaluate(stmt)
        except InterpreterError as e:
            return e
