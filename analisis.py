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


class IRGenerator(Visitor):
    def __init__(self) -> None:
        self.module = ir.Module(name="prog")
        self.stack = []
        self.functions = {}
        self.globals = {}
        self.symbol_tables = []
        self.function_return_types = {}
        self.current_function = None
        self.builder = None
        self.break_stack = []
        self.continue_stack = []
        self.string_count = 0
        self.printf = self.declare_printf()

    def declare_printf(self):
        int_type = ir.IntType(32)
        char_ptr = ir.IntType(8).as_pointer()
        fnty = ir.FunctionType(int_type, [char_ptr], var_arg=True)
        return ir.Function(self.module, fnty, name="printf")

    def llvm_type(self, type_name: str):
        if type_name in ("int", "boolean", "bool"):
            return ir.IntType(32)
        if type_name == "float":
            return ir.DoubleType()
        if type_name == "char":
            return ir.IntType(8)
        if type_name == "void":
            return ir.VoidType()
        raise TypeError(f"Unknown type '{type_name}'")

    def push_scope(self) -> None:
        self.symbol_tables.append({})

    def pop_scope(self) -> None:
        self.symbol_tables.pop()

    def define_symbol(self, name: str, ptr, type_name: str) -> None:
        self.symbol_tables[-1][name] = (ptr, type_name)

    def find_symbol(self, name: str):
        for table in reversed(self.symbol_tables):
            if name in table:
                return table[name]
        if name in self.globals:
            return self.globals[name]
        raise NameError(f"Variable '{name}' was not declared")

    def cast(self, value, target_type):
        if value.type == target_type:
            return value
        if isinstance(target_type, ir.DoubleType) and isinstance(value.type, ir.IntType):
            return self.builder.sitofp(value, target_type)
        if isinstance(value.type, ir.DoubleType) and isinstance(target_type, ir.IntType):
            return self.builder.fptosi(value, target_type)
        if isinstance(value.type, ir.IntType) and isinstance(target_type, ir.IntType):
            if value.type.width < target_type.width:
                return self.builder.zext(value, target_type)
            return self.builder.trunc(value, target_type)
        return value

    def to_bool(self, value):
        if isinstance(value.type, ir.DoubleType):
            return self.builder.fcmp_ordered("!=", value, ir.Constant(value.type, 0.0))
        if isinstance(value.type, ir.IntType):
            return self.builder.icmp_signed("!=", value, ir.Constant(value.type, 0))
        return value

    def promote(self, lhs, rhs):
        if isinstance(lhs.type, ir.DoubleType) or isinstance(rhs.type, ir.DoubleType):
            double = ir.DoubleType()
            return self.cast(lhs, double), self.cast(rhs, double)
        if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
            width = max(lhs.type.width, rhs.type.width, 32)
            target = ir.IntType(width)
            return self.cast(lhs, target), self.cast(rhs, target)
        return lhs, rhs

    def alloca_at_entry(self, name: str, type_name: str):
        return self.builder.alloca(self.llvm_type(type_name), name=name)

    def current_block_has_terminator(self) -> bool:
        return self.builder.block.terminator is not None

    def visit_program(self, node: Program) -> None:
        for item in node.declarations:
            if isinstance(item, list):
                for declaration in item:
                    self.declare_global(declaration)
            elif isinstance(item, (Function, FunctionPrototype)):
                self.declare_function(item)
        for item in node.declarations:
            if isinstance(item, Function):
                item.accept(self)

    def declare_global(self, node: Declaration) -> None:
        llvm_type = self.llvm_type(node.type)
        glob = ir.GlobalVariable(self.module, llvm_type, name=node.variable)
        glob.initializer = ir.Constant(llvm_type, 0)
        self.globals[node.variable] = (glob, node.type)

    def declare_function(self, node: Function) -> None:
        if node.name in self.functions:
            return
        ret_type = self.llvm_type(node.return_type)
        arg_types = [self.llvm_type(param.type) for param in node.params]
        fnty = ir.FunctionType(ret_type, arg_types)
        func = ir.Function(self.module, fnty, name=node.name)
        for llvm_arg, param in zip(func.args, node.params):
            llvm_arg.name = param.name
        self.functions[node.name] = func
        self.function_return_types[node.name] = node.return_type

    def visit_function(self, node: Function) -> None:
        func = self.functions[node.name]
        self.current_function = func
        entry = func.append_basic_block("entry")
        self.builder = ir.IRBuilder(entry)
        self.push_scope()

        for arg, param in zip(func.args, node.params):
            ptr = self.alloca_at_entry(param.name, param.type)
            self.builder.store(arg, ptr)
            self.define_symbol(param.name, ptr, param.type)

        for declaration in node.declarations:
            declaration.accept(self)
        for statement in node.statements:
            statement.accept(self)
            if self.current_block_has_terminator():
                break

        if not self.current_block_has_terminator():
            if node.return_type == "void":
                self.builder.ret_void()
            else:
                self.builder.ret(ir.Constant(self.llvm_type(node.return_type), 0))

        self.pop_scope()
        self.current_function = None
        self.builder = None

    def visit_declaration(self, node: Declaration) -> None:
        if node.size is not None:
            size = self.const_int(node.size)
            ptr = self.builder.alloca(ir.ArrayType(self.llvm_type(node.type), size), name=node.variable)
        else:
            ptr = self.alloca_at_entry(node.variable, node.type)
        self.define_symbol(node.variable, ptr, node.type)
        if node.initializer is not None and node.size is None:
            value = node.initializer.accept(self)
            self.builder.store(self.cast(value, self.llvm_type(node.type)), ptr)

    def const_int(self, node) -> int:
        if isinstance(node, Literal) and node.type == "int":
            return int(node.value)
        raise TypeError("Array sizes must be integer literals")

    def visit_block(self, node: Block) -> None:
        self.push_scope()
        for declaration in node.declarations:
            declaration.accept(self)
        for statement in node.statements:
            statement.accept(self)
            if self.current_block_has_terminator():
                break
        self.pop_scope()

    def visit_emptystatement(self, node: EmptyStatement) -> None:
        return None

    def location_ptr(self, node):
        if isinstance(node, Variable):
            return self.find_symbol(node.name)
        if isinstance(node, ArrayRef):
            ptr, type_name = self.find_symbol(node.name)
            zero = ir.Constant(ir.IntType(32), 0)
            index = self.cast(node.index.accept(self), ir.IntType(32))
            elem_ptr = self.builder.gep(ptr, [zero, index], inbounds=True)
            return elem_ptr, type_name
        raise TypeError("Invalid assignment target")

    def visit_assignment(self, node: Assignment):
        ptr, type_name = self.location_ptr(node.target)
        value = node.expression.accept(self)
        value = self.cast(value, self.llvm_type(type_name))
        self.builder.store(value, ptr)
        return value



def build_parser():
    return yacc.yacc(start="program", debug=False, write_tables=False)


def parse(source: str) -> Program:
    lexer = lex.lex()
    parser = build_parser()
    return parser.parse(source, lexer=lexer)


def compile_source(source: str) -> str:
    root = parse(source)
    irgen = IRGenerator()
    root.accept(irgen)
    return str(irgen.module)


data = """
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

int main() {
    int result;
    result = factorial(5);
    printf("factorial(5) = %d\\n", result);
    return result;
}
"""


if __name__ == "__main__":
    source = data
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf8") as file:
            source = file.read()
    print(compile_source(source))

