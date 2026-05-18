# %%
import ply.lex as lex
import ply.yacc as yacc
from arbol import Literal

literals = ['+','-','*','/', '%', '(', ')']
tokens = ['ID', 'INTLIT']

t_ignore  = ' \t'

def t_ID(t):
     r'[a-zA-Z_][a-zA-Z_0-9]*'
     return t

def t_INTLIT(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

# %%
def p_Primary(p):
    '''
    Primary : INTLIT 
            | '(' Primary ')'
    '''
    if len(p) == 2:
        p[0] = Literal(p[1], 'INT')
    else:
        p[0] = p[2]
        
def p_error(p):
    print("Syntax error in input!", p)


# %%
data = '10'
lexer = lex.lex()
parser = yacc.yacc()
parser.parse(data)

# %%
