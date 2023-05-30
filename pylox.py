import sys
from typing import Any
from loguru import logger
from tokens import Token, TokenType
from parser import Parser
from ast_printer import AstPrinter
from interpreter import Interpreter
from errors import InterpreterError
from resolver import Resolver


class Scanner:
    keywords = {
        "and": TokenType.AND,
        "class": TokenType.CLASS,
        "else": TokenType.ELSE,
        "false": TokenType.FALSE,
        "for": TokenType.FOR,
        "fun": TokenType.FUN,
        "if": TokenType.IF,
        "nil": TokenType.NIL,
        "or": TokenType.OR,
        "print": TokenType.PRINT,
        "return": TokenType.RETURN,
        "super": TokenType.SUPER,
        "this": TokenType.THIS,
        "true": TokenType.TRUE,
        "var": TokenType.VAR,
        "while": TokenType.WHILE,
    }

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

    def _advance(self) -> str:
        """Consume the next char and return"""
        val = self._source[self._current]
        self._current += 1
        return val

    def _add_token(self, token_type: TokenType, literal: Any = ""):
        """There is no method overloading in Python"""
        self._tokens.append(
            Token(
                token_type,
                self._source[self._start : self._current],
                literal,
                self._line,
            )
        )

    def _match(self, ch: str) -> bool:
        """Only consume the current char if it's what we are looking for"""
        if self.is_at_end():
            return False
        if self._source[self._current] != ch:
            return False

        self._current += 1
        return True

    def _peek(self) -> str:
        """Similar to `self._match` function but won't consume chars"""
        if self.is_at_end():
            return "\0"

        return self._source[self._current]

    def _peek_next(self) -> str:
        """Don't consume the . in a number literal until we're sure thers is a digit after it"""
        if self._current + 1 >= len(self._source):
            return "\0"

        return self._source[self._current + 1]

    def _is_digit(self, ch: str) -> bool:
        return "0" <= ch <= "9"

    def _is_alpha(self, ch: str) -> bool:
        return "a" <= ch <= "z" or "A" <= ch <= "Z" or ch == "_"

    def _is_alpha_numeric(self, ch: str) -> bool:
        return self._is_digit(ch) or self._is_alpha(ch)

    def _form_string(self):
        while self._peek() != '"' and not self.is_at_end():
            # a string literal is "..."
            if self._peek() == "\n":
                self._line += 1
            self._advance()

        if self.is_at_end():
            # Lox.error(self._line, "Unterminated string.")
            Lox.error(self._line, "Unterminated string.")
            return

        # consume the closing "
        self._advance()

        # note: [self._start + 1:self._current - 1] will chose string INSIDE "..."
        self._add_token(
            TokenType.STRING, self._source[self._start + 1 : self._current - 1]
        )

    def _form_number(self):
        while self._is_digit(self._peek()):
            self._advance()
        if self._peek() == "." and self._is_digit(self._peek_next()):
            # consume the . in a number literal
            self._advance()
            # consume the fractional part
            while self._is_digit(self._peek()):
                self._advance()

        logger.debug(f"Add a number literal: {self._source[self._start:self._current]}")

        self._add_token(
            TokenType.NUMBER, float(self._source[self._start : self._current])
        )

    def _form_identifier(self):
        while self._is_alpha_numeric(self._peek()):
            self._advance()

        text = self._source[self._start : self._current]
        if text in Scanner.keywords:
            self._add_token(Scanner.keywords[text])
        else:
            self._add_token(TokenType.IDENTIFIER)

    def _scan_token(self):
        c = self._advance()
        match c:
            # a lexeme whose length is one
            case "(":
                self._add_token(TokenType.LEFT_PAREN)
            case ")":
                self._add_token(TokenType.RIGHT_PAREN)
            case "{":
                self._add_token(TokenType.LEFT_BRACE)
            case "}":
                self._add_token(TokenType.RIGHT_BRACE)
            case ",":
                self._add_token(TokenType.COMMA)
            case ".":
                self._add_token(TokenType.DOT)
            case "-":
                self._add_token(TokenType.MINUS)
            case "+":
                self._add_token(TokenType.PLUS)
            case ";":
                self._add_token(TokenType.SEMICOLON)
            case "*":
                self._add_token(TokenType.STAR)
            # a lexeme whose length is two
            case "!":
                self._add_token(
                    TokenType.BANG_EQUAL if self._match("=") else TokenType.BANG
                )
            case "=":
                self._add_token(
                    TokenType.EQUAL_EQUAL if self._match("=") else TokenType.EQUAL
                )
            case "<":
                self._add_token(
                    TokenType.LESS_EQUAL if self._match("=") else TokenType.LESS
                )
            case ">":
                self._add_token(
                    TokenType.GREATER_EQUAL if self._match("=") else TokenType.GREATER
                )
            case "/":
                if self._match("/"):
                    # a comment goes until the end of the line
                    # keep consume chars until we reach the end of the line
                    while self._peek() != "\n" and not self.is_at_end():
                        self._advance()
                else:
                    self._add_token(TokenType.SLASH)
            case " " | "\r" | "\t":
                # ignore whitespaces
                ...
            case "\n":
                self._line += 1
            case ch if self._is_digit(ch):
                self._form_number()
            case ch if self._is_alpha(ch):
                self._form_identifier()
            case '"':
                # string literals
                self._form_string()
            case _:
                # Lox.error(self._line, "Unexpected character.")
                Lox.error(self._line, "Unexpected character.")

    def _scan_tokens(self):
        while not self.is_at_end():
            # invariant: in each loop
            # , we are at the beginning of the next lexeme
            # logger.debug(
            #     f"Ready to scan next token, current strings is {list(self._source[self._current:])}"
            # )
            self._start = self._current
            self._scan_token()

        self._tokens.append(Token(TokenType.EOF, None, "", self._line))
        return self._tokens


class Lox:
    interpreter: Interpreter = Interpreter()  # only 1 interpreter is available
    _has_error: bool = False
    _has_runtime_error: bool = False

    @classmethod
    def _run(cls, code: str):
        logger.debug("--- [Lexical analysis] ---")
        logger.debug("--------------------------")
        lexer = Scanner(code)
        tokens = lexer._scan_tokens()
        logger.debug("--- [Syntactic analysis] ---")
        parser = Parser(tokens)
        statements = parser.parse()
        logger.debug("----------------------------")
        if statements is None:
            # which means err happen
            Lox._has_error = True
            logger.error("Parser Error")
        else:
            logger.debug("--- [Semantic analysis] ---")
            resolver = Resolver(cls.interpreter)
            resolver._resolve(statements)
            logger.debug(f"Resolved results: {cls.interpreter.locals}")
            logger.debug("---------------------------")

            logger.debug("--- [Interpretation] ---")
            cls.interpreter.interpret(statements)
            logger.debug("------------------------")

    @classmethod
    def _run_file(cls, path: str):
        with open(path, "r") as f:
            code = f.read()
        cls._run(code)

        # indicate an error in the exit code
        if cls._has_error:
            sys.exit(65)
        if cls._has_runtime_error:
            sys.exit(70)

    @classmethod
    def _run_prompt(cls):
        """REPL"""
        while True:
            try:
                line = input("> ")
                cls._run(line)
                # in REPL, the session should be alive even the user make a mistake
                cls._has_error = False
            except EOFError:
                break

    @classmethod
    def error(cls, line: int, msg: str):
        cls._report(line, "", msg)

    @classmethod
    def runtime_error(cls, e):
        cls._has_runtime_error = True

    @classmethod
    def _report(cls, line: int, where: str, msg: str):
        print(f"[line {line}] Error {where}: {msg}", file=sys.stderr)
        cls._has_error = True

    @classmethod
    def cli(cls, args: list[str]):
        if len(args) > 2:
            print("Usage: pyloc [script]")
            sys.exit(64)
        elif len(args) == 2:
            cls._run_file(args[1])
        else:
            cls._run_prompt()
