## What's Lox

Lox is a dynamically typed, interpretered script language, which is designed by Bob Nystrom for his book [*Crafting interpreters*](https://craftinginterpreters.com/).

## What's pylox

An interpreter for the Lox programming language implemented in Python, following a Tree-Walk approach. The original book utilizes Java to build the interpreter, referred to as `jlox`. To maintain consistency, I chose the name `pylox` for the Python implementation. 💅

## Features

1. **Type hints(Python 3.9+) everywhere**. And I exploit `mypy` to do type checking.
2. **Pattern matching(Python 3.10+)** rather than multiple `if-elif`.
3. **Visitor pattern**
    - Use it to print the AST
    - Use it to evaluate the expressions and execute the statements
    - Use it to do resolution
4. Use `Black` to format code
5. **A little meta-programming**
    - Set `arity` attribute to built-in function by using `function.wraps`
