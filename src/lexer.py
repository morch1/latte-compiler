import ply.lex as lex

from operators import OP_PLUS, OP_MINUS, OP_TIMES, OP_DIV, OP_MOD, OP_NOT, OP_OR, OP_AND, OP_LT, OP_LE, OP_GT, OP_GE, \
    OP_EQ, OP_NE
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

# TODO: dont hardcode operators
t_plus = OP_PLUS.op_regex()
t_minus = OP_MINUS.op_regex()
t_times = OP_TIMES.op_regex()
t_divide = OP_DIV.op_regex()
t_mod = OP_MOD.op_regex()
t_not = OP_NOT.op_regex()
t_or = OP_OR.op_regex()
t_and = OP_AND.op_regex()
t_lt = OP_LT.op_regex()
t_le = OP_LE.op_regex()
t_gt = OP_GT.op_regex()
t_ge = OP_GE.op_regex()
t_eq = OP_EQ.op_regex()
t_ne = OP_NE.op_regex()

precedence = (
    ('right', 'or'),
    ('right', 'and'),
    ('left', 'lt', 'le', 'gt', 'ge', 'eq', 'ne'),
    ('left', 'plus', 'minus'),
    ('left', 'times', 'divide', 'mod'),
    ('right', 'not', 'uminus'),
)

# todo: precedence = Operator.precedence_table

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
