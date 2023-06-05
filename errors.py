from tokens import Token, TokenType


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

    def __str__(self):
        return f"[line {self.token.line}] Error at '{self.token.lexeme}': {self.msg}"


class InterpreterError(Exception):
    def __init__(self, token: Token, msg: str):
        self.token = token
        self.msg = msg

    def __str__(self):
        return f"Error at '{self.token}': {self.msg}"


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value
