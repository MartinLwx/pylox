from enum import Enum
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
    Get,
    Set,
    This,
    Super,
    Grouping,
    Literal,
    Logical,
    Unary,
    Class,
)
from interpreter import Interpreter
from tokens import Token
from errors import error_report


class FunctionType(Enum):
    NONE = 1
    FUNCTION = 2
    METHOD = 3
    INITIALIZER = 4


class ClassType(Enum):
    NONE = 1
    CLASS = 2
    SUBCLASS = 3


class Resolver(ExprVisitor):
    def __init__(self, interpreter: Interpreter):
        self.interpreter = interpreter
        self._scopes: list[dict[str, bool]] = []
        self.current_func = FunctionType.NONE
        self.current_class = ClassType.NONE
        self._has_error = False

    def _resolve(
        self,
        statements: list[Expr] | list[Stmt] | Expr | Stmt,
    ):
        """Resolve each statement inside"""
        if isinstance(statements, list):
            for stmt in statements:
                self.visit(stmt)
        else:
            self.visit(statements)

    def _error_and_set_flag(
        self, token: Token, msg: str, *, show_line_number: bool = True
    ):
        error_report(token, msg, show_line_number)
        self._has_error = True

    def _resolve_local(self, expr: Expr, name: Token):
        for i in reversed(range(len(self._scopes))):
            if name.lexeme in self._scopes[i]:
                self.interpreter.resolve(expr, len(self._scopes) - 1 - i)
                return

    def _resolve_function(self, stmt: Function, _type: FunctionType):
        enclosing_func = self.current_func
        self.current_func = _type
        self._begin_scope()
        for param in stmt.params:
            self._declare(param)
            self._define(param)
        # in static analysis, we immediately traverse into the body
        self._resolve(stmt.body.statements)
        self._end_scope()
        self.current_func = enclosing_func

    def _begin_scope(self):
        self._scopes.append({})

    def _end_scope(self):
        self._scopes.pop()

    def _declare(self, name: Token):
        """Declaration adds the variable to the innermost scope"""
        if not self._scopes:
            return

        # this variable is not ready yet, that is, exists but is unavailable
        scope = self._scopes[-1]
        if name.lexeme in scope:
            self._error_and_set_flag(
                name,
                "Already a variable with this name in this scope.",
                show_line_number=False,
            )
        scope[name.lexeme] = False

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
            self._error_and_set_flag(
                expr.name,
                "Can't read local variable in its own initializer.",
                show_line_number=False,
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
        self._resolve_function(stmt, FunctionType.FUNCTION)

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
        self._resolve(stmt.expression)

        return None

    def visit_ReturnStmt(self, stmt: ReturnStmt):
        if self.current_func == FunctionType.NONE:
            self._error_and_set_flag(
                stmt.keyword,
                "Can't return from top-level code.",
                show_line_number=False,
            )
        if stmt.value:
            if self.current_func == FunctionType.INITIALIZER:
                self._error_and_set_flag(
                    stmt.keyword,
                    "Can't return a value from an initializer.",
                    show_line_number=False,
                )
            self._resolve(stmt.value)

        return None

    def visit_WhileStmt(self, stmt: WhileStmt):
        self._resolve(stmt.condition)
        self._resolve(stmt.body)

        return None

    def visit_Class(self, stmt: Class):
        enclosing_class = self.current_class
        self.current_class = ClassType.CLASS

        self._declare(stmt.name)
        self._define(stmt.name)

        # the names of subclass and superclass should not be equal
        if stmt.superclass and stmt.name.lexeme == stmt.superclass.name.lexeme:
            self._error_and_set_flag(
                stmt.superclass.name,
                "A class can't inherit from itself.",
                show_line_number=False,
            )

        # Lox allows class declarations even inside blocks
        # In that case, we need to make sure it's resloved
        if stmt.superclass:
            self.current_class = ClassType.SUBCLASS
            self._resolve(stmt.superclass)

        if stmt.superclass:
            self._begin_scope()
            self._scopes[-1]["super"] = True

        self._begin_scope()
        assert len(self._scopes) > 0
        self._scopes[-1]["this"] = True
        for method in stmt.methods.values():
            declaration = FunctionType.METHOD
            if method.name.lexeme == "init":
                declaration = FunctionType.INITIALIZER
            self._resolve_function(method, declaration)
        self._end_scope()

        if stmt.superclass:
            self._end_scope()

        self.current_class = enclosing_class

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

    def visit_Get(self, expr: Get):
        self._resolve(expr.obj)

        return None

    def visit_Set(self, expr: Set):
        self._resolve(expr.value)
        self._resolve(expr.obj)

        return None

    def visit_This(self, expr: This):
        if self.current_class == ClassType.NONE:
            self._error_and_set_flag(
                expr.keyword,
                "Can't use 'this' outside of a class.",
                show_line_number=False,
            )
        self._resolve_local(expr, expr.keyword)

        return None

    def visit_Super(self, expr: Super):
        # resolver `super` as if it were a variable
        if self.current_class == ClassType.NONE:
            self._error_and_set_flag(
                expr.keyword,
                "Can't use 'super' outside of a class.",
                show_line_number=False,
            )
        elif self.current_class == ClassType.CLASS:
            self._error_and_set_flag(
                expr.keyword,
                "Can't use 'super' in a class with no superclass.",
                show_line_number=False,
            )
        self._resolve_local(expr, expr.keyword)

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
