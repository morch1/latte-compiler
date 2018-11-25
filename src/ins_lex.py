import ply.lex as lex
from errors import IllegalCharacter

reserved = ("int", "string", "boolean", "void", "true", "false", "return", "if", "else", "while",)

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
    "lparen", "rparen", "lbracket", "rbracket",
    "semi", "comma",
)


t_ignore = ' \t'  # ignore whitespaces

def t_newline(t):
    r"""\n+"""
    t.lexer.lineno += len(t.value)

t_plus = r'\+'
t_minus = r'-'
t_times = r'\*'
t_divide = r'/'
t_mod = r'%'
t_not = r'!'
t_or = r'\|\|'
t_and = r'&&'
t_lt = r'<'
t_le = r'<='
t_gt = r'>'
t_ge = r'>='
t_eq = r'=='
t_ne = r'!='

t_equals = r'='
t_plusplus = r'\+\+'
t_minusminus = r'--'

t_lparen = r'\('
t_rparen = r'\)'
t_lbracket = r'\{'
t_rbracket = r'\}'
t_semi = r';'
t_comma = r','

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
    raise IllegalCharacter(t.lexer.lineno, t.value[0])


lexer = lex.lex(debug=False)
