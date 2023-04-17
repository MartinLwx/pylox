import sys


class Lox:
    _has_error: bool = False

    @classmethod
    def _run(cls, code: str):
        ...

    @classmethod
    def _run_file(cls, path: str):
        with open(path, "r") as f:
            code = f.read()
        cls._run(code)

        # indicate an error in the exit code
        if cls._has_error:
            sys.exit(65)

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
    def _report(cls, line: int, where: str, msg: str):
        print(f"[line {line}] Error {where}: {msg}", file=sys.stderr)
        cls._has_error = True

    @classmethod
    def cli(cls, args: list[str]):
        if len(args) > 2:
            print("Usage: pyloc [script]")
            sys.exit(64)
        elif len(args) == 2:
            cls._run_file(args[0])
        else:
            cls._run_prompt()
