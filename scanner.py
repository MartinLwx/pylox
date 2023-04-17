from typing import Any
from token import Token, TokenType


class Scanner:
    def __init__(self, source: str):
        self._source = source
        self._tokens: list[Token] = []
        # invariant:
        # self._start points to the 1st char in the lexeme
        # self._current points to the char currently being considered
        # self._line tracks what source line current is on
        self._start = 0
        self._current = 0
        self._line = 1

    def is_at_end(self):
        return self._current >= len(self._source)

    def advance(self) -> str:
        """Consume the next char and return"""
        self._current += 1
        return self._source[self._current]

    def add_token(self, token_type: TokenType, literal: Any = ""):
        """There is no method overloading in Python"""
        self._tokens.append(Token(token_type, self._source[self._start:self._current], literal, self._line))

    def scan_tokens(self):
        while not self.is_at_end():
            # invariant: in each loop
            # , we are at the beginning of the next lexeme
            c = self.advance()
            match c:
                case "(":
                    self.add_token(TokenType.LEFT_PAREN)
                case ")":
                    self.add_token(TokenType.RIGHT_PAREN)
                case "{":
                    self.add_token(TokenType.LEFT_BRACE)
                case "}":
                    self.add_token(TokenType.RIGHT_BRACE)
                case ",":
                    self.add_token(TokenType.COMMA)
                case ".":
                    self.add_token(TokenType.DOT)
                case "-":
                    self.add_token(TokenType.MINUS)
                case "+":
                    self.add_token(TokenType.PLUS)
                case ";":
                    self.add_token(TokenType.SEMICOLON)
                case "*":
                    self.add_token(TokenType.STAR)
                case "_":
                    print(f'{self._line} Unexpected character.')

            self._start = self._current
        self._tokens.append(Token(TokenType.EOF, None, self._line))
