import shlex
import subprocess
from pathlib import Path


def extrace_expect(test_case: Path) -> str:
    """Read the test_case and extract the expected result"""
    with open(test_case, "r") as f:
        lines = f.readlines()

    res = []
    for line in lines:
        if "// expect: " in line:
            res.append(line.split("// expect: ")[1].rstrip("\n"))

    return "\n".join(res)


def run_test(test_case: Path) -> bool:
    """Run a test located in test_case and return True if it pass the test"""
    output = subprocess.check_output(
        args=shlex.split(f"python pylox.py {test_case}"), text=True
    ).rstrip("\n")
    expect = extrace_expect(test_case)

    return output == expect


def run_all_tests(test_folder: str, quiet: bool = False):
    """Run all tests and return the status, only print the failed test cases if quiet == True"""
    for test_case in Path(test_folder).iterdir():
        if test_case.suffix == ".lox":
            if run_test(test_case):
                print("[PASS]", end="")
            else:
                print("[FAIL]", end="")
            print(test_case)


if __name__ == "__main__":
    # run_all_tests("./test")
    run_all_tests("./test/this/")
