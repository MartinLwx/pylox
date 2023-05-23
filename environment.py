from typing import Any
from tokens import Token
from errors import InterpreterError


class Environment:
    values: dict[str, Any] = {}

    def _define(self, name: str, value: Any):
        """A variable definition binds a new name to a value"""
        self.values[name] = value

    def _assign(self, name: Token, value: Any):
        """Assignment is not allowed to create a new variable"""
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        raise InterpreterError(name, f"Undefined variable '{name.lexeme}'.")

    def get(self, name: Token):
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        raise InterpreterError(name, f"Undefined variable '{name.lexeme}'.")
