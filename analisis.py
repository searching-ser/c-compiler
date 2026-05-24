import sys

import ply.lex as lex
import ply.yacc as yacc
from llvmlite import ir

from arbol import (
    ArrayRef,
    Assignment,
    BinaryOp,
    Block,
    BreakStatement,
    Call,
    CallStatement,
    CaseStatement,
    ContinueStatement,
    Declaration,
    DefaultStatement,
    DoWhileStatement,
    ExpressionStatement,
    EmptyStatement,
    ForStatement,
    Function,
    FunctionPrototype,
    IfStatement,
    Literal,
    Parameter,
    Program,
    ReturnStatement,
    SwitchStatement,
    UnaryOp,
    Variable,
    Visitor,
    WhileStatement,
)


reserved = {
    "int": "INT",
    "bool": "BOOL",
    "boolean": "BOOL",
    "float": "FLOAT",
    "char": "CHAR",
    "void": "VOID",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "do": "DO",
    "switch": "SWITCH",
    "case": "CASE",
    "default": "DEFAULT",
    "break": "BREAK",
    "continue": "CONTINUE",
    "return": "RETURN",
    "true": "TRUE",
    "false": "FALSE",
}

tokens = [
    "ID",
    "INTLIT",
    "FLOATLIT",
    "CHARLIT",
    "STRINGLIT",
    "EQ",
    "NE",
    "LE",
    "GE",
    "AND",
    "OR",
] + sorted(set(reserved.values()))

literals = "+-*/%(){}[],;=<>!:"
t_ignore = " \t\r"


def t_COMMENT(t):
    r"//.*"
    pass


def t_MCOMMENT(t):
    r"/\*(.|\n)*?\*/"
    t.lexer.lineno += t.value.count("\n")


t_EQ = r"=="
t_NE = r"!="
t_LE = r"<="
t_GE = r">="
t_AND = r"&&"
t_OR = r"\|\|"


def t_FLOATLIT(t):
    r"([0-9]+\.[0-9]*|\.[0-9]+)"
    t.value = float(t.value)
    return t


def t_INTLIT(t):
    r"[0-9]+"
    t.value = int(t.value)
    return t


def t_CHARLIT(t):
    r"'([^\\']|\\.)'"
    text = t.value[1:-1]
    escapes = {"n": "\n", "t": "\t", "0": "\0", "'": "'", "\\": "\\"}
    if text.startswith("\\"):
        t.value = ord(escapes.get(text[1], text[1]))
    else:
        t.value = ord(text)
    return t


def t_STRINGLIT(t):
    r'"([^\\"]|\\.)*"'
    text = t.value[1:-1]
    t.value = bytes(text, "utf-8").decode("unicode_escape")
    return t


def t_ID(t):
    r"[a-zA-Z_][a-zA-Z_0-9]*"
    t.type = reserved.get(t.value, "ID")
    return t


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


def t_error(t):
    raise SyntaxError(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")


precedence = (
    ("nonassoc", "IFX"),
    ("nonassoc", "ELSE"),
    ("left", "OR"),
    ("left", "AND"),
    ("left", "EQ", "NE"),
    ("nonassoc", "<", ">", "LE", "GE"),
    ("left", "+", "-"),
    ("left", "*", "/", "%"),
    ("right", "UMINUS", "!"),
)



def p_program(p):
    "program : empty"
    p[0] = Program([])


def p_empty(p):
    "empty :"
    p[0] = None


def p_error(p):
    if p is None:
        raise SyntaxError("Syntax error at end of input")
    raise SyntaxError(f"Syntax error near '{p.value}' at line {p.lineno}")


def build_parser():
    return yacc.yacc(start="program", debug=False, write_tables=False)


def parse(source: str) -> Program:
    lexer = lex.lex()
    parser = build_parser()
    return parser.parse(source, lexer=lexer)


def compile_source(source: str) -> str:
    root = parse(source)
    return str(root)


if __name__ == "__main__":
    source = ""
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf8") as file:
            source = file.read()
    print(compile_source(source))

