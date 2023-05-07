from tokens import Token, TokenType
from expr import Expr, Binary, Unary, Literal, Grouping


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

    def _advance(self):
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

        return self._error(self._peek(), msg)

    def _expression(self) -> Expr:
        """expression -> equality"""
        return self._equality()

    def _equality(self) -> Expr:
        """equality -> comparison ( ( "!=" | "==" ) comparison)*"""
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
        """comparison -> term ( ( ">" | ">=" | "<" | "<=" ) term)*;"""
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
        """term       -> factor ( ( "-" | "+" ) factor)*;"""
        expr = self._factor()

        while self._match([TokenType.MINUS, TokenType.PLUS]):
            operator = self._previous()
            right = self._factor()
            expr = Binary(expr, operator, right)

        return expr

    def _factor(self) -> Expr:
        """factor     -> unary ( ( "/" | "*" ) unary)*;"""
        expr = self._unary()

        while self._match([TokenType.SLASH, TokenType.STAR]):
            operator = self._previous()
            right = self._factor()
            expr = Binary(expr, operator, right)

        return expr

    def _unary(self) -> Expr:
        """unary      -> ( "!" | "-" ) unary | primary;"""
        if self._match([TokenType.BANG, TokenType.MINUS]):
            operator = self._previous()
            right = self._unary()
            return Unary(operator, right)

        return self._primary()

    def _primary(self) -> Expr:
        """primary    -> NUMBER | STRING | "true" | "false" | "nil" | "(" expression ")";"""
        if self._match([TokenType.FALSE]):
            return Literal(False)
        if self._match([TokenType.TRUE]):
            return Literal(True)
        if self._match([TokenType.NIL]):
            return Literal(None)

        if self._match([TokenType.NUMBER, TokenType.STRING]):
            return Literal(self._previous().literal)
        if self._match([TokenType.LEFT_PAREN]):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        raise self._error(self._peek(), "Expect expressions")

    def parse(self) -> Expr | None:
        try:
            return self._expression()
        except ParseError:
            return None
