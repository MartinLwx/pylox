from expr import Expr, Unary, Binary, Literal, Grouping, ExprVisitor


class AstPrinter(ExprVisitor):
    def parenthesize(self, name: str, exprs: list[Expr]) -> str:
        s = ["(", name]
        for expr in exprs:
            s.append(" ")
            s.append(self.visit(expr))
        s.append(")")

        return "".join(s)

    def visit_Binary(self, expr: Binary):
        return self.parenthesize(expr.operator.lexeme, [expr.left, expr.right])

    def visit_Grouping(self, expr: Grouping):
        return self.parenthesize("group", [expr.expression])

    def visit_Literal(self, expr: Literal) -> str:
        if expr.value is None:
            return "nil"
        
        return str(expr.value)

    def visit_Unary(self, expr: Unary):
        return self.parenthesize(expr.operator.lexeme, [expr.right])
