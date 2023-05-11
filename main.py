import sys
from pylox import Lox
from expr import *
from tokens import Token, TokenType
from ast_printer import AstPrinter
from interpreter import Interpreter


def main(args: list[str]):
    lox_interpreter = Lox()
    lox_interpreter.cli(sys.argv)


def test_ast_printer():
    expressions = Binary(
        Unary(Token(TokenType.MINUS, "-", None, 1), Literal("123")),
        Token(TokenType.STAR, "*", None, 1),
        Grouping(Literal(45.67)),
    )
    print(AstPrinter().visit(expressions))


if __name__ == "__main__":
    main(sys.argv)
    # test_ast_printer()
