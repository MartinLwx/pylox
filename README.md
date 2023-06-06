## What's Lox

Lox is a dynamically typed, interpreted script language, which is designed by Robert Nystorm for his book [*Crafting interpreters*](https://craftinginterpreters.com/).

## What's pylox

An interpreter for the Lox programming language implemented in Python, following a tree-walk approach. The original book utilizes Java to build the interpreter, referred to as `jlox`. To maintain consistency, I chose the name `pylox` for the Python implementation. 💅

## Structure
```sh
.
├── LICENSE
├── tests
├── README.md
├── environment.py                # for scopes
├── expr.py                       # all AST nodes
├── tokens.py                     # all Lox tokens
├── scanner.py                    # chars  ---> tokens
├── parser.py                     # tokens ---> AST
├── resolver.py                   # do semantic analysis by traversing AST
├── interpreter.py                # tree-walk interpreter
├── run_tests.py                  # run all tests
├── pylox.py                      # main
├── errors.py                     # some error handling
├── ast_printer.py                # print an AST in LISP style
└── utils.py                      # set arity for built-in function. i.e. clock
```
## Dependency
Python 3.10+

## Usage
```sh
# execute a lox file
$ python pylox.py foo.lox

# REPL
$ python pylox.py
```

## Testing
The tests are copied from [crafting interpreters](https://github.com/munificent/craftinginterpreters)

**Note** that I disable the benchmark tests because `pylox` **is quite inefficient**.

```sh
$ python run_tests.py
# --------- Summary ----------
#   [PASS]: 231 / 245 -- 94.29%
#   [SKIP]:  14 / 245 -- 5.71%
#   [FAIL]:   0 / 245 -- 0.00%
# ----------------------------
```

