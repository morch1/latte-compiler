import ply.lex as lex

from operators import BINOP_PLUS, BINOP_MINUS, BINOP_TIMES, BINOP_DIV, BINOP_MOD, UNOP_NOT, BINOP_OR, BINOP_AND, BINOP_LT, BINOP_LE, BINOP_GT, BINOP_GE, \
    BINOP_INT_EQ, BINOP_INT_NE
from errors import IllegalCharacterError

reserved = ("true", "false", "return", "if", "else", "while",)

tokens = reserved + (
    # literals
    "id", "intconst", "stringconst",
    # operators
    "plus", "minus", "times", "divide", "mod",
    "not", "or", "and",
    "lt", "le", "gt", "ge", "eq", "ne",
    # assignment
    "equals", "plusplus", "minusminus",
    # delimeters
    "lparen", "rparen", "lbrace", "rbrace",
    "semi", "comma",
)


t_ignore = ' \t'  # ignore whitespaces

def t_newline(t):
    r"""\n+"""
    t.lexer.lineno += len(t.value)

# TODO: dont hardcode operators, precendence
# http://www.dabeaz.com/ply/ply.html#ply_nn27
t_plus = BINOP_PLUS.op_regex()
t_minus = BINOP_MINUS.op_regex()
t_times = BINOP_TIMES.op_regex()
t_divide = BINOP_DIV.op_regex()
t_mod = BINOP_MOD.op_regex()
t_not = UNOP_NOT.op_regex()
t_or = BINOP_OR.op_regex()
t_and = BINOP_AND.op_regex()
t_lt = BINOP_LT.op_regex()
t_le = BINOP_LE.op_regex()
t_gt = BINOP_GT.op_regex()
t_ge = BINOP_GE.op_regex()
t_eq = BINOP_INT_EQ.op_regex()
t_ne = BINOP_INT_NE.op_regex()

precedence = (
    ('right', 'or'),
    ('right', 'and'),
    ('left', 'lt', 'le', 'gt', 'ge', 'eq', 'ne'),
    ('left', 'plus', 'minus'),
    ('left', 'times', 'divide', 'mod'),
    ('right', 'not', 'uminus'),
)

t_equals = r'\='
t_plusplus = r'\+\+'
t_minusminus = r'\-\-'

t_lparen = r'\('
t_rparen = r'\)'
t_lbrace = r'\{'
t_rbrace = r'\}'
t_semi = r'\;'
t_comma = r'\,'

def t_id(t):
    r"""[a-zA-Z_]\w*"""
    t.type = t.value if t.value in reserved else 'id'
    return t

t_intconst = r'\d+'
t_stringconst = r'\"([^\\\n]|(\\.))*?\"'

def t_comment(t):
    r"""/\*(.|\n)*?\*/|(\#|//).*"""
    t.lexer.lineno += t.value.count('\n')

def t_error(t):
    raise IllegalCharacterError(t.lexer.lineno, t.value[0])

lexer = lex.lex(debug=False)
