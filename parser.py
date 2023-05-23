from loguru import logger
from tokens import Token, TokenType
from expr import (
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
)


class ParseError(Exception):
    def __init__(self, token: Token, msg: str):
        self.token = token
        self.msg = msg

    def report(self):
        # put this method here to avoid circular import
        if self.token.type == TokenType.EOF:
            return f"[line {self.token.line}] Error at end: {self.msg}"
        else:
            return (
                f"[line {self.token.line}] Error at '{self.token.lexeme}': {self.msg}"
            )


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def _synchronize(self):
        """It discard tokens until it thinks it has found a statement boundary"""
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
        err.report()

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
        """assignment  -> IDENTIFIER "=" assignment | equality"""
        expr = self._equality()

        if self._match([TokenType.EQUAL]):
            logger.debug(
                f"Check if it's an assignment, the type of LHS is {type(expr).__name__}"
            )
            equals = self._previous()
            value = self._assignment()
            if isinstance(expr, Variable):
                logger.debug(f"Type checking pass, name = {expr.name}")
                name = expr.name
                return Assign(name, value)
            self._error(equals, "Invalid assignment target.")

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
        """unary       -> ( "!" | "-" ) unary | primary"""
        if self._match([TokenType.BANG, TokenType.MINUS]):
            operator = self._previous()
            right = self._unary()
            return Unary(operator, right)

        return self._primary()

    def _primary(self) -> Expr:
        """primary     -> NUMBER | STRING | IDENTIFIER | "true" | "false" | "nil" | "(" expression ")" """
        if self._match([TokenType.NUMBER, TokenType.STRING]):
            return Literal(self._previous().literal)
        if self._match([TokenType.IDENTIFIER]):
            return Variable(self._previous())
        if self._match([TokenType.TRUE]):
            return Literal(True)
        if self._match([TokenType.FALSE]):
            return Literal(False)
        if self._match([TokenType.NIL]):
            return Literal(None)

        if self._match([TokenType.LEFT_PAREN]):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        raise self._error(self._peek(), "Expect expressions")

    def _print_statement(self) -> Print:
        """printStmt   -> "print" expression ";" """
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expecte ';' after value.")

        return Print(value)

    def _expression_statement(self) -> Expression:
        """exprStmt    -> expression ";" """
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expecte ';' after value.")

        return Expression(expr)

    def _vardeclaration(self) -> Var:
        """varDecl     -> "var" IDENTIFIER ( "=" expression )? ";" """
        name = self._consume(TokenType.IDENTIFIER, "Expect variable name.")
        initializer = None
        if self._match([TokenType.EQUAL]):
            initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")

        return Var(name, initializer)

    def _declarations(self):
        """declaration -> varDecl | statement"""
        try:
            if self._match([TokenType.VAR]):
                return self._vardeclaration()

            return self._statement()
        except ParseError:
            self._synchronize()
            return None

    def _statement(self) -> Print | Expression:
        """statement -> exprStmt | printStmt"""
        if self._match([TokenType.PRINT]):
            return self._print_statement()

        return self._expression_statement()

    def parse(self) -> list[Print | Expression] | None:
        statements = []
        try:
            while not self._is_at_end():
                statements.append(self._declarations())

            return statements
        except ParseError:
            return None
