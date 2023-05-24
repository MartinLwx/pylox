## What's Lox

Lox is a dynamically typed, interpretered script language, which is designed by Bob Nystrom for his book [*Crafting interpreters*](https://craftinginterpreters.com/).

## What's pylox

A Tree-Walk interpreter of Lox programming language written in Python. The original book use Java to implement the interpreter, which is called `jlox`. So I mimicked the name, using the name `pylox` 💅

## Features

1. **Type hints(Python 3.9+) everywhere**. And I exploit `mypy` to do type checking.
2. **Pattern matching(Python 3.10+)** rather than multiple `if-elif`.
3. **Visitor pattern**
    - Use it to print the AST
    - Use it to evaluate the expressions and execute the statements
4. Use `Black` to format code
