from tokens import Token, TokenType
from expr import (
    Stmt,
    Expr,
    Binary,
    Unary,
    Literal,
    Grouping,
    Print,
    Expression,
    Var,
    Variable,
    Assign,
    Block,
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
)
from errors import ParseError


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def _synchronize(self):
        """It discards tokens until it thinks it has found a statement boundary """
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            if self._peek().type in [
                TokenType.CLASS,
                TokenType.FUN,
                TokenType.VAR,
                TokenType.FOR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.PRINT,
                TokenType.RETURN,
            ]:
                return
            self._advance()

    def _error(self, token: Token, msg: str) -> ParseError:
        err = ParseError(token, msg)

        return err

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _previous(self) -> Token:
        """Return the most recently consumed token"""
        return self.tokens[self.current - 1]

    def _check(self, _type: TokenType) -> bool:
        """Return True if the current token is of the given _type"""
        if self._is_at_end():
            return False

        return self._peek().type == _type

    def _advance(self) -> Token:
        """Consume the current token and returns it"""
        if not self._is_at_end():
            self.current += 1

        return self._previous()

    def _peek(self) -> Token:
        """Return the current token we have yet to consume"""
        return self.tokens[self.current]

    def _match(self, types: list[TokenType]) -> bool:
        """Check if the current token hash any of the given types.
        If so, it consumes the token and returns True
        """
        for _type in types:
            if self._check(_type):
                self._advance()
                return True

        return False

    def _consume(self, _type: TokenType, msg: str):
        if self._check(_type):
            return self._advance()

        raise self._error(self._peek(), msg)

    def _expression(self) -> Expr:
        """expression  -> assignment"""
        return self._assignment()

    def _assignment(self):
        """assignment  -> (call ".")? IDENTIFIER "=" assignment | logic_or"""
        expr = self._logic_or()

        if self._match([TokenType.EQUAL]):
            equals = self._previous()
            value = self._assignment()
            if isinstance(expr, Variable):
                return Assign(expr.name, value)
            elif isinstance(expr, Get):
                return Set(expr.obj, expr.name, value)
            raise self._error(equals, "Invalid assignment target.")

        return expr

    def _logic_or(self) -> Logical | Expr:
        """logic_or    -> logic_and ( "or" logic_and )*"""
        expr = self._logic_and()

        while self._match([TokenType.OR]):
            operator = self._previous()
            right = self._logic_and()
            expr = Logical(expr, operator, right)

        return expr

    def _logic_and(self) -> Logical | Expr:
        """logic_and   -> equality ( "and" equality )*"""
        expr = self._equality()

        while self._match([TokenType.AND]):
            operator = self._previous()
            right = self._equality()
            expr = Logical(expr, operator, right)

        return expr

    def _equality(self) -> Expr:
        """equality    -> comparison ( ( "!=" | "==" ) comparison)*"""
        # the first comparison nonterminal translates to the first call to self._comparison()
        expr = self._comparison()

        # the (...)* loop maps to a while loop
        while self._match([TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL]):
            # inside the rule, we must first find either != or ==
            operator = self._previous()
            right = (
                self._comparison()
            )  # call self._comparison() again to parse the RHS operand
            expr = Binary(expr, operator, right)  # form a new syntax tree node

        # if we don't find != or ==
        # , we must be done with the sequence of equality operators
        return expr

    def _comparison(self) -> Expr:
        """comparison  -> term ( ( ">" | ">=" | "<" | "<=" ) term)*"""
        expr = self._term()

        while self._match(
            [
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
                TokenType.LESS,
                TokenType.LESS_EQUAL,
            ]
        ):
            operator = self._previous()
            right = self._term()
            expr = Binary(expr, operator, right)

        return expr

    def _term(self) -> Expr:
        """term        -> factor ( ( "-" | "+" ) factor)*"""
        expr = self._factor()

        while self._match([TokenType.MINUS, TokenType.PLUS]):
            operator = self._previous()
            right = self._factor()
            expr = Binary(expr, operator, right)

        return expr

    def _factor(self) -> Expr:
        """factor      -> unary ( ( "/" | "*" ) unary)*"""
        expr = self._unary()

        while self._match([TokenType.SLASH, TokenType.STAR]):
            operator = self._previous()
            right = self._factor()
            expr = Binary(expr, operator, right)

        return expr

    def _unary(self) -> Expr:
        """unary       -> ( "!" | "-" ) unary | call"""
        if self._match([TokenType.BANG, TokenType.MINUS]):
            operator = self._previous()
            right = self._unary()
            return Unary(operator, right)

        return self._call()

    def _finish_call(self, callee) -> Call:
        """arguments   -> expression ( "," expression )*"""
        arguments = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                # Python 3.7+, there is no maximum arguments limitation
                arguments.append(self._expression())
                if not self._match([TokenType.COMMA]):
                    break
        paren = self._consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")

        return Call(callee, paren, arguments)

    def _call(self) -> Call | Expr:
        """call        -> primary ( "(" arguments? ")" | "." IDENTIFIER )* ;"""
        expr = self._primary()
        while True:
            if self._match([TokenType.LEFT_PAREN]):
                expr = self._finish_call(expr)
            elif self._match([TokenType.DOT]):
                name = self._consume(
                    TokenType.IDENTIFIER, "Expect property name after '.'."
                )
                expr = Get(expr, name)
            else:
                break

        return expr

    def _primary(self) -> Expr:
        """primary     -> NUMBER | STRING | IDENTIFIER | "this" | true" | "false" | "nil" | "super" "." IDENTIFIER | (" expression ")" """
        if self._match([TokenType.NUMBER, TokenType.STRING]):
            return Literal(self._previous().literal)
        if self._match([TokenType.IDENTIFIER]):
            return Variable(self._previous())
        if self._match([TokenType.THIS]):
            return This(self._previous())
        if self._match([TokenType.TRUE]):
            return Literal(True)
        if self._match([TokenType.FALSE]):
            return Literal(False)
        if self._match([TokenType.NIL]):
            return Literal(None)

        if self._match([TokenType.SUPER]):
            keyword = self._previous()
            self._consume(TokenType.DOT, "Expect '.' after 'super'.")
            method = self._consume(
                TokenType.IDENTIFIER, "Expect superclass method name."
            )

            return Super(keyword, method)
        if self._match([TokenType.LEFT_PAREN]):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        raise self._error(self._peek(), "Expect expression.")

    def _print_statement(self) -> Print:
        """printStmt   -> "print" expression ";" """
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after value.")

        return Print(value)

    def _expression_statement(self) -> Expression:
        """exprStmt    -> expression ";" """
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")

        return Expression(expr)

    def _block(self) -> Block:
        """block       -> "{" declarations* "}" """
        statements = []
        # use self._is_at_end() to avoid infinite loop
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            statements.append(self._declarations())
        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")

        return Block(statements)

    def _class_declaration(self) -> Class:
        """classDecl   -> "class" IDENTIFIER ( "<" IDENTIFIER )? "{" function* "}" """
        name = self._consume(TokenType.IDENTIFIER, "Expect class name.")

        superclass = None
        if self._match([TokenType.LESS]):
            self._consume(TokenType.IDENTIFIER, "Expect superclass name.")
            superclass = Variable(self._previous())

        self._consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")

        methods = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            methods.append(self._func_declaration("method"))

        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")

        return Class(name, superclass, methods)

    def _func_declaration(self, kind: str) -> Function:
        """
        funDecl        -> "fun" function ;
        function       -> IDENTIFIER "(" parameters? ")" block ;
        parameters     -> IDENTIFIER ( "," IDENTIFIER )* ;
        ----
        use kind so that we can reuse this method later to parse methods
        """
        name = self._consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self._consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        parameters = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                parameters.append(
                    self._consume(TokenType.IDENTIFIER, "Expect parameter name.")
                )
                if not self._match([TokenType.COMMA]):
                    break
        self._consume(TokenType.RIGHT_PAREN, f"Expect ')' after {kind} name")
        # the _block() method assumes the brace token has already been matched
        self._consume(TokenType.LEFT_BRACE, "Expect '{' before " + kind + " body.")
        body = self._block()

        return Function(name, parameters, body)

    def _var_declaration(self) -> Var:
        """varDecl     -> "var" IDENTIFIER ( "=" expression )? ";" """
        name = self._consume(TokenType.IDENTIFIER, "Expect variable name.")
        initializer = None
        if self._match([TokenType.EQUAL]):
            initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")

        return Var(name, initializer)

    def _declarations(self):
        """declaration -> classDecl | funcDecl | varDecl | statement"""
        # NOTE: Disable self._synchronize so that we can pass the tests
        # try:
        #     if self._match([TokenType.CLASS]):
        #         return self._class_declaration()
        #     if self._match([TokenType.FUN]):
        #         return self._func_declaration("function")
        #     if self._match([TokenType.VAR]):
        #         return self._var_declaration()

        #     return self._statement()
        # except ParseError as e:
        #     self._synchronize()
        #     return None

        if self._match([TokenType.CLASS]):
            return self._class_declaration()
        if self._match([TokenType.FUN]):
            return self._func_declaration("function")
        if self._match([TokenType.VAR]):
            return self._var_declaration()

        return self._statement()

    def _if_statement(self):
        """ifStmt      -> "if" "(" expression ")" statement ( "else" statement )?"""
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch = self._statement()
        else_branch = None
        if self._match([TokenType.ELSE]):
            else_branch = self._statement()

        return IfStmt(condition, then_branch, else_branch)

    def _while_statement(self):
        """whileStmt   -> "while" "(" expression ")" statement"""
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        statement = self._statement()

        return WhileStmt(condition, statement)

    def _for_statement(self):
        """forStmt     -> "for" "(" ( varDecl | exprStmt | ";" ) expression? ";" expression? ")" statement ;"""
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'")
        if self._match([TokenType.VAR]):
            initializer = self._var_declaration()
        elif self._match([TokenType.SEMICOLON]):
            initializer = None
        else:
            initializer = self._expression_statement()

        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after loop condition")

        increment = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after for clause")

        # let's desugar the for loop
        body = self._statement()

        # the increment should be executed after the body in each iteration
        if increment:
            body = Block([body, Expression(increment)])

        if condition is None:
            condition = Literal(True)

        body = WhileStmt(condition, body)

        if initializer:
            body = Block([initializer, body])

        return body

    def _return_statement(self) -> ReturnStmt:
        """returnStmt  -> "return" expression? ";" """
        keyword = self._previous()
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()

        self._consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return ReturnStmt(keyword, value)

    def _statement(self) -> Stmt:
        """statement   -> exprStmt | forStmt | ifStmt | printStmt | returnStmt | whileStmt | block"""
        if self._match([TokenType.FOR]):
            return self._for_statement()
        if self._match([TokenType.IF]):
            return self._if_statement()
        if self._match([TokenType.PRINT]):
            return self._print_statement()
        if self._match([TokenType.RETURN]):
            return self._return_statement()
        if self._match([TokenType.WHILE]):
            return self._while_statement()
        if self._match([TokenType.LEFT_BRACE]):
            return self._block()

        return self._expression_statement()

    def parse(self) -> list[Expr] | list[Stmt]:
        statements = []
        while not self._is_at_end():
            statements.append(self._declarations())

        return statements
