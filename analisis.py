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
    "program : external_list"
    p[0] = Program(p[1])


def p_external_list(p):
    """
    external_list : external_list external
                  | external
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_external(p):
    """
    external : function_definition
             | function_prototype
             | global_declaration
    """
    p[0] = p[1]


def p_function_definition(p):
    "function_definition : type ID '(' parameters_opt ')' compound_statement"
    block = p[6]
    p[0] = Function(p[2], p[1], p[4], block.declarations, block.statements)


def p_function_prototype(p):
    "function_prototype : type ID '(' parameters_opt ')' ';'"
    p[0] = FunctionPrototype(p[2], p[1], p[4])


def p_global_declaration(p):
    "global_declaration : type declarator_list ';'"
    p[0] = [Declaration(name, p[1], size, init, True) for name, size, init in p[2]]


def p_parameters_opt(p):
    """
    parameters_opt : parameters
                   | VOID
                   | empty
    """
    p[0] = [] if p[1] is None or p[1] == "void" else p[1]


def p_parameters(p):
    """
    parameters : parameters ',' parameter
               | parameter
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_parameter(p):
    "parameter : type ID"
    p[0] = Parameter(p[2], p[1])


def p_type(p):
    """
    type : INT
         | BOOL
         | FLOAT
         | CHAR
         | VOID
    """
    p[0] = p[1]


def p_compound_statement(p):
    "compound_statement : '{' block_items_opt '}'"
    declarations = []
    statements = []
    for item in p[2]:
        if isinstance(item, Declaration):
            declarations.append(item)
        else:
            statements.append(item)
    p[0] = Block(declarations, statements)


def p_block_items_opt(p):
    """
    block_items_opt : block_items
                    | empty
    """
    p[0] = p[1] or []


def p_block_items(p):
    """
    block_items : block_items block_item
                | block_item
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + p[2]


def p_block_item(p):
    """
    block_item : declaration
               | statement
    """
    p[0] = p[1] if isinstance(p[1], list) else [p[1]]


def p_declaration(p):
    "declaration : type declarator_list ';'"
    p[0] = [Declaration(name, p[1], size, init) for name, size, init in p[2]]


def p_declarator_list(p):
    """
    declarator_list : declarator_list ',' declarator
                    | declarator
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_declarator(p):
    """
    declarator : ID
               | ID '=' expression
               | ID '[' expression ']'
               | ID '[' expression ']' '=' expression
    """
    if len(p) == 2:
        p[0] = (p[1], None, None)
    elif len(p) == 4:
        p[0] = (p[1], None, p[3])
    elif len(p) == 5:
        p[0] = (p[1], p[3], None)
    else:
        p[0] = (p[1], p[3], p[6])


def p_statement(p):
    """
    statement : compound_statement
              | assignment ';'
              | call ';'
              | if_statement
              | while_statement
              | for_statement
              | do_while_statement
              | switch_statement
              | return_statement ';'
              | BREAK ';'
              | CONTINUE ';'
              | expression ';'
              | ';'
    """
    if len(p) == 3 and isinstance(p[1], Call):
        p[0] = CallStatement(p[1])
    elif len(p) == 3 and p[1] == "break":
        p[0] = BreakStatement()
    elif len(p) == 3 and p[1] == "continue":
        p[0] = ContinueStatement()
    elif len(p) == 3:
        p[0] = ExpressionStatement(p[1])
    elif len(p) == 2 and p[1] == ";":
        p[0] = EmptyStatement()
    else:
        p[0] = p[1]


def p_assignment(p):
    "assignment : location '=' expression"
    p[0] = Assignment(p[1], p[3])


def p_location(p):
    """
    location : ID
             | ID '[' expression ']'
    """
    if len(p) == 2:
        p[0] = Variable(p[1])
    else:
        p[0] = ArrayRef(p[1], p[3])


def p_if_statement(p):
    """
    if_statement : IF '(' expression ')' statement %prec IFX
                 | IF '(' expression ')' statement ELSE statement
    """
    p[0] = IfStatement(p[3], p[5], p[7] if len(p) == 8 else None)


def p_while_statement(p):
    "while_statement : WHILE '(' expression ')' statement"
    p[0] = WhileStatement(p[3], p[5])


def p_for_statement(p):
    "for_statement : FOR '(' for_init_opt ';' expression_opt ';' for_update_opt ')' statement"
    p[0] = ForStatement(p[3], p[5], p[7], p[9])


def p_for_init_opt(p):
    """
    for_init_opt : assignment
                 | for_declaration
                 | empty
    """
    p[0] = p[1]


def p_for_declaration(p):
    "for_declaration : type declarator_list"
    p[0] = [Declaration(name, p[1], size, init) for name, size, init in p[2]]


def p_for_update_opt(p):
    """
    for_update_opt : assignment
                   | empty
    """
    p[0] = p[1]


def p_expression_opt(p):
    """
    expression_opt : expression
                   | empty
    """
    p[0] = p[1]


def p_do_while_statement(p):
    "do_while_statement : DO statement WHILE '(' expression ')' ';'"
    p[0] = DoWhileStatement(p[2], p[5])


def p_switch_statement(p):
    "switch_statement : SWITCH '(' expression ')' '{' case_list default_opt '}'"
    p[0] = SwitchStatement(p[3], p[6], p[7])


def p_case_list(p):
    """
    case_list : case_list case_statement
              | empty
    """
    if len(p) == 2:
        p[0] = p[1] or []
    else:
        p[0] = p[1] + [p[2]]


def p_case_statement(p):
    "case_statement : CASE literal ':' statements_opt"
    p[0] = CaseStatement(p[2], p[4])


def p_default_opt(p):
    """
    default_opt : DEFAULT ':' statements_opt
                | empty
    """
    p[0] = DefaultStatement(p[3]) if len(p) == 4 else None


def p_statements_opt(p):
    """
    statements_opt : statements
                   | empty
    """
    p[0] = p[1] or []


def p_statements(p):
    """
    statements : statements statement
               | statement
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_return_statement(p):
    """
    return_statement : RETURN expression
                     | RETURN
    """
    p[0] = ReturnStatement(p[2] if len(p) == 3 else None)


def p_expression(p):
    """
    expression : expression OR conjunction
               | conjunction
    """
    p[0] = p[1] if len(p) == 2 else BinaryOp("||", p[1], p[3])


def p_conjunction(p):
    """
    conjunction : conjunction AND equality
                | equality
    """
    p[0] = p[1] if len(p) == 2 else BinaryOp("&&", p[1], p[3])


def p_equality(p):
    """
    equality : relation EQ relation
             | relation NE relation
             | relation
    """
    p[0] = p[1] if len(p) == 2 else BinaryOp(p[2], p[1], p[3])


def p_relation(p):
    """
    relation : addition '<' addition
             | addition '>' addition
             | addition LE addition
             | addition GE addition
             | addition
    """
    p[0] = p[1] if len(p) == 2 else BinaryOp(p[2], p[1], p[3])


def p_addition(p):
    """
    addition : addition '+' term
             | addition '-' term
             | term
    """
    p[0] = p[1] if len(p) == 2 else BinaryOp(p[2], p[1], p[3])


def p_term(p):
    """
    term : term '*' factor
         | term '/' factor
         | term '%' factor
         | factor
    """
    p[0] = p[1] if len(p) == 2 else BinaryOp(p[2], p[1], p[3])


def p_factor(p):
    """
    factor : '-' factor %prec UMINUS
           | '!' factor
           | primary
    """
    p[0] = p[1] if len(p) == 2 else UnaryOp(p[1], p[2])


def p_primary(p):
    """
    primary : location
            | literal
            | '(' expression ')'
            | call
    """
    p[0] = p[2] if len(p) == 4 else p[1]


def p_call(p):
    "call : ID '(' arguments_opt ')'"
    p[0] = Call(p[1], p[3])


def p_arguments_opt(p):
    """
    arguments_opt : arguments
                  | empty
    """
    p[0] = p[1] or []


def p_arguments(p):
    """
    arguments : arguments ',' expression
              | expression
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_literal(p):
    """
    literal : INTLIT
            | FLOATLIT
            | CHARLIT
            | STRINGLIT
            | TRUE
            | FALSE
    """
    if p.slice[1].type == "CHARLIT":
        p[0] = Literal(p[1], "char")
    elif p.slice[1].type == "STRINGLIT":
        p[0] = Literal(p[1], "string")
    elif isinstance(p[1], int):
        p[0] = Literal(p[1], "int")
    elif isinstance(p[1], float):
        p[0] = Literal(p[1], "float")
    elif p.slice[1].type == "TRUE":
        p[0] = Literal(1, "bool")
    elif p.slice[1].type == "FALSE":
        p[0] = Literal(0, "bool")


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

