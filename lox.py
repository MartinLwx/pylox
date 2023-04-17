import sys


class Lox:
    def __init__(self):
        self._has_error = False

    def _run(self, code: str):
        ...

    def _run_file(self, path: str):
        with open(path, "r") as f:
            code = f.read()
        self._run(code)

        # indicate an error in the exit code
        if self._has_error:
            sys.exit(65)

    def _run_prompt(self):
        """REPL"""
        while True:
            try:
                line = input("> ")
                self._run(line)
                # in REPL, the session should be alive even the user make a mistake
                self._has_error = False
            except EOFError:
                break

    def error(self, line: int, msg: str):
        self.report(line, "", msg)

    def report(self, line: int, where: str, msg: str):
        print(f"[line {line}] Error {where}: {msg}", file=sys.stderr)
        self._has_error = True

    def cli(self, args: list[str]):
        if len(args) > 2:
            print("Usage: pyloc [script]")
            sys.exit(64)
        elif len(args) == 2:
            self._run_file(args[0])
        else:
            self._run_prompt()
