import shlex
import subprocess
from pathlib import Path

# see: https://github.com/munificent/craftinginterpreters/blob/master/tool/bin/test.dart
EXCLUDED_TESTS = [
    # for clox(not support in pylox)
    "test/function/missing_comma_in_parameters.lox",
    "test/number/nan_equality.lox",
    # for earlier chapters
    "test/scanning/identifiers.lox",
    "test/scanning/keywords.lox",
    "test/scanning/numbers.lox",
    "test/scanning/punctuators.lox",
    "test/scanning/strings.lox",
    "test/scanning/whitespace.lox",
    "test/expressions/evaluate.lox",
    "test/expressions/parse.lox",
    # pylox has no restriction abount function arguments
    "test/function/too_many_arguments.lox",
    "test/function/too_many_parameters.lox",
    "test/method/too_many_arguments.lox",
    "test/method/too_many_parameters.lox",
]


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def extract_expect(test_case: Path) -> str:
    """Read the test_case and extract the expected result"""
    with open(test_case, "r") as f:
        lines = f.readlines()

    res = []
    # for "// expect: ..."
    for line in lines:
        if "// expect: " in line:
            res.append(line.split("// expect: ")[1].rstrip("\n"))

    # for "[line: ?] Error at ...", an ParseError (SyntaxError)
    if len(res) == 0:
        for line in lines:
            if "// [line" in line:
                res.append(line[line.index("// [line ") :][3:].rstrip("\n"))

    # for "Error at ...", an InterpreterError (RuntimeError)
    if len(res) == 0:
        for line in lines:
            if "// Error at" in line:
                res.append(line[line.index("// Error at") :][3:].rstrip("\n"))

    return "\n".join(res)


def run_test(test_case: Path) -> tuple[bool, str | None]:
    """Run a test located in test_case and return True if it pass the test, else return False and the error message"""
    try:
        output = subprocess.check_output(
            args=shlex.split(f"python pylox.py {test_case}"), text=True
        ).rstrip("\n")
    except subprocess.CalledProcessError as e:
        output = str(e.output).rstrip("\n")
    expect = extract_expect(test_case)

    if output == expect:
        return True, None
    else:
        err = []
        err.append(f"  output: {output!r}")
        err.append(f"  expect: {expect!r}")
        return False, "\n".join(err)


def run_all_tests(test_folder: Path):
    """Run all tests in this folder and return the stats of PASS/SKIP/FAIL"""
    PASS, SKIP, FAIL = 0, 0, 0
    for test_case in sorted(test_folder.iterdir()):
        if test_case.suffix == ".lox":
            if str(test_case.relative_to(".")) in EXCLUDED_TESTS:
                print(f"{bcolors.OKBLUE}[SKIP]{bcolors.ENDC} {test_case}")
                SKIP += 1
            else:
                status, msg = run_test(test_case)
                if status:
                    print(f"{bcolors.OKGREEN}[PASS]{bcolors.ENDC} {test_case}")
                    PASS += 1
                else:
                    print(f"{bcolors.FAIL}[FAIL]{bcolors.ENDC} {test_case}")
                    print(msg)
                    FAIL += 1

    return PASS, SKIP, FAIL


def test_runner(tests: str):
    PASS, SKIP, FAIL = 0, 0, 0
    for test_topic in Path(tests).iterdir():
        # NOTE: disablie benchmark cause it's too slow
        if test_topic.is_dir() and test_topic.stem not in ["benchmark", "limit"]:
            print(f"------ {test_topic} ------")
            x, y, z = run_all_tests(test_topic)
            PASS += x
            SKIP += y
            FAIL += z
            print("--------------------------")
    print("--------- Summmary ----------")
    print(
        f"  [PASS]: {PASS: >3} / {(PASS + SKIP + FAIL)} -- {PASS / (PASS + SKIP + FAIL):.2%}"
    )
    print(
        f"  [SKIP]: {SKIP: >3} / {(PASS + SKIP + FAIL)} -- {SKIP / (PASS + SKIP + FAIL):.2%}"
    )
    print(
        f"  [FAIL]: {FAIL: >3} / {(PASS + SKIP + FAIL)} -- {FAIL / (PASS + SKIP + FAIL):.2%}"
    )
    print("-----------------------------")


if __name__ == "__main__":
    test_runner("./test")
