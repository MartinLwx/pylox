from tokens import Token, TokenType


def error_report(token: Token, msg: str, show_line_number: bool = True):
    if token.type == TokenType.EOF:
        err = f"Error at end: {msg}"
    else:
        err = f"Error at '{token.lexeme}': {msg}"

    print(f"[line {token.line}] " + err if show_line_number else err)


class ParseError(Exception):
    def __init__(self, token: Token, msg: str):
        self.token = token
        self.msg = msg

    def __str__(self):
        if self.token.type == TokenType.EOF:
            return f"[line {self.token.line}] Error at end: {self.msg}"
        else:
            return (
                f"[line {self.token.line}] Error at '{self.token.lexeme}': {self.msg}"
            )


class InterpreterError(Exception):
    def __init__(self, token: Token, msg: str):
        self.token = token
        self.msg = msg

    def __str__(self):
        return f"Error at '{self.token}': {self.msg}"


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value
