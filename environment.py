from typing import Any
from loguru import logger
from tokens import Token
from errors import InterpreterError


class Environment:
    def __init__(self, env=None):
        # global env has no enclosing env
        self.values: dict[str, Any] = {}
        self.enclosing = env

    def __repr__(self):
        lines = ["----- This environment: -----"]
        for name, val in self.values.items():
            lines.append(f"  {name}: {val}")
        lines.append("-----------------------------")

        return "\n".join(lines)

    def _define(self, name: str, value: Any):
        """A variable definition binds a new name to a value"""
        self.values[name] = value

    def _assign(self, name: Token, value: Any):
        """Assignment is not allowed to create a new variable"""
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return
        if self.enclosing:
            self.enclosing._assign(name, value)
            return

        raise InterpreterError(name, f"Undefined variable '{name.lexeme}'.")

    def get(self, name: Token):
        if name.lexeme in self.values:
            return self.values[name.lexeme]
        # walk the env chain
        if self.enclosing:
            return self.enclosing.get(name)

        raise InterpreterError(name, f"Undefined variable '{name.lexeme}'.")

    def get_at(self, distance: int, name: str):
        return self.ancestor(distance).values.get(name)

    def ancestor(self, distance: int):
        """Walks a fixed number of hoops up the parent chain and returns the env there"""
        res = self
        for i in range(distance):
            res = res.enclosing

        return res

    def assign_at(self, distance: int, name: Token, value: Any):
        self.ancestor(distance).values[name.lexeme] = value

    def helper_env_chain(self):
        logger.debug("Show the env inheritances:")
        cursor = self
        while cursor:
            logger.debug(cursor)
            cursor = cursor.enclosing
