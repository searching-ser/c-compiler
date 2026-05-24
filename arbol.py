from __future__ import annotations

from abc import ABC
from typing import Any


class ASTNode(ABC):
    def accept(self, visitor: Visitor) -> Any:
        method = "visit_" + self.__class__.__name__.lower()
        return getattr(visitor, method)(self)


class Program(ASTNode):
    def __init__(self, declarations: list[ASTNode]) -> None:
        self.declarations = declarations


class Function(ASTNode):
    def __init__(
        self,
        name: str,
        return_type: str,
        params: list[Parameter],
        declarations: list[Declaration],
        statements: list[ASTNode],
    ) -> None:
        self.name = name
        self.return_type = return_type
        self.params = params
        self.declarations = declarations
        self.statements = statements


class FunctionPrototype(ASTNode):
    def __init__(self, name: str, return_type: str, params: list[Parameter]) -> None:
        self.name = name
        self.return_type = return_type
        self.params = params


class Parameter(ASTNode):
    def __init__(self, name: str, type: str) -> None:
        self.name = name
        self.type = type


class Declaration(ASTNode):
    def __init__(
        self,
        variable: str,
        type: str,
        size: ASTNode | None = None,
        initializer: ASTNode | None = None,
        is_global: bool = False,
    ) -> None:
        self.variable = variable
        self.type = type
        self.size = size
        self.initializer = initializer
        self.is_global = is_global


class Declarations(ASTNode):
    def __init__(self, decls: Declarations | None, decl: Declaration) -> None:
        self.decls = decls
        self.decl = decl


class Block(ASTNode):
    def __init__(self, declarations: list[Declaration], statements: list[ASTNode]) -> None:
        self.declarations = declarations
        self.statements = statements


class EmptyStatement(ASTNode):
    pass


class Assignment(ASTNode):
    def __init__(self, target: ASTNode, expression: ASTNode) -> None:
        self.target = target
        self.expression = expression


class IfStatement(ASTNode):
    def __init__(
        self,
        condition: ASTNode,
        then_statement: ASTNode,
        else_statement: ASTNode | None = None,
    ) -> None:
        self.condition = condition
        self.then_statement = then_statement
        self.else_statement = else_statement


class WhileStatement(ASTNode):
    def __init__(self, condition: ASTNode, statement: ASTNode) -> None:
        self.condition = condition
        self.statement = statement


class ForStatement(ASTNode):
    def __init__(
        self,
        init: ASTNode | list[Declaration] | None,
        condition: ASTNode | None,
        update: ASTNode | None,
        statement: ASTNode,
    ) -> None:
        self.init = init
        self.condition = condition
        self.update = update
        self.statement = statement


class DoWhileStatement(ASTNode):
    def __init__(self, statement: ASTNode, condition: ASTNode) -> None:
        self.statement = statement
        self.condition = condition


class SwitchStatement(ASTNode):
    def __init__(
        self,
        expression: ASTNode,
        cases: list[CaseStatement],
        default: DefaultStatement | None,
    ) -> None:
        self.expression = expression
        self.cases = cases
        self.default = default


class CaseStatement(ASTNode):
    def __init__(self, value: ASTNode, statements: list[ASTNode]) -> None:
        self.value = value
        self.statements = statements


class DefaultStatement(ASTNode):
    def __init__(self, statements: list[ASTNode]) -> None:
        self.statements = statements


class BreakStatement(ASTNode):
    pass


class ContinueStatement(ASTNode):
    pass


class ReturnStatement(ASTNode):
    def __init__(self, expression: ASTNode | None = None) -> None:
        self.expression = expression


class CallStatement(ASTNode):
    def __init__(self, call: Call) -> None:
        self.call = call


class ExpressionStatement(ASTNode):
    def __init__(self, expression: ASTNode) -> None:
        self.expression = expression


class Literal(ASTNode):
    def __init__(self, value: Any, type: str) -> None:
        self.value = value
        self.type = type

    def __str__(self) -> str:
        return f"[LIT, {self.value}]"


class Variable(ASTNode):
    def __init__(self, name: str, type: str | None = None) -> None:
        self.name = name
        self.type = type


class ArrayRef(ASTNode):
    def __init__(self, name: str, index: ASTNode) -> None:
        self.name = name
        self.index = index


class BinaryOp(ASTNode):
    def __init__(self, op: str, lhs: ASTNode, rhs: ASTNode) -> None:
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def __str__(self) -> str:
        return f"[{self.op}, {self.lhs}, {self.rhs}]"


class UnaryOp(ASTNode):
    def __init__(self, op: str, expression: ASTNode) -> None:
        self.op = op
        self.expression = expression


class Call(ASTNode):
    def __init__(self, name: str, args: list[ASTNode]) -> None:
        self.name = name
        self.args = args


class Visitor:
    pass


class Calculator(Visitor):
    def __init__(self) -> None:
        self.stack = []

    def visit_literal(self, node: Literal) -> None:
        self.stack.append(node.value)

    def visit_variable(self, node: Variable) -> None:
        raise NameError(f"Variable '{node.name}' does not have a value")

    def visit_binaryop(self, node: BinaryOp) -> None:
        node.lhs.accept(self)
        node.rhs.accept(self)
        rhs = self.stack.pop()
        lhs = self.stack.pop()
        if node.op == "+":
            self.stack.append(lhs + rhs)
        elif node.op == "-":
            self.stack.append(lhs - rhs)
        elif node.op == "*":
            self.stack.append(lhs * rhs)
        elif node.op == "/":
            self.stack.append(lhs / rhs)
        elif node.op == "%":
            self.stack.append(lhs % rhs)
