from tokens import Token


class InterpreterError(Exception):
    def __init__(self, token: Token, msg: str):
        self.token = token
        self.msg = msg

    def __str__(self):
        return f"{self.msg}\n[line {self.token.line}]"
