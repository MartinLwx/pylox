## What's Lox

Lox is a dynamically typed, interpretered script language, which is designed by Bob Nystrom for his book [*Crafting interpreters*](https://craftinginterpreters.com/).

## What's pylox

A Tree-Walk interpreter of Lox programming language written in Python. The original book use Java to implement the interpreter, which is called `jloc`. So I mimicked the name, using the name `pylox` 💅

## Features

1. I try to add **as many type hints(Python 3.9+) as possible**. And I exploit `mypy` to do type checking.
2. I use **pattern matching(Python 3.10+)** to handle differenct cases when implementing the [scanner](./pylox.py). Say goodbyte to `if-elif`. 👊
3. I use the **visitor pattern** to implement the [ast_printer](./ast_printer.py).
