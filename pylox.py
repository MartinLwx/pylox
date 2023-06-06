import sys
from scanner import Scanner
from parser import Parser
from interpreter import Interpreter
from errors import InterpreterError, ParseError
from resolver import Resolver


class Lox:
    interpreter: Interpreter = Interpreter()  # only 1 interpreter is available
    _has_error: bool = False
    _has_runtime_error: bool = False

    @classmethod
    def _run(cls, code: str):
        lexer = Scanner(code)
        tokens = lexer.scan_tokens()
        if lexer.has_error:
            Lox._has_error = True
            return
        try:
            parser = Parser(tokens)
            statements = parser.parse()
        except ParseError as e:
            print(e)
            return

        resolver = Resolver(cls.interpreter)
        resolver._resolve(statements)
        if resolver._has_error:
            Lox._has_error = True
            return
        try:
            cls.interpreter.interpret(statements)
        except InterpreterError as e:
            Lox._has_error = True
            print(e)

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


def main(args: list[str]):
    lox_interpreter = Lox()
    lox_interpreter.cli(sys.argv)


if __name__ == "__main__":
    main(sys.argv)
