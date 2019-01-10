import ply.lex as lex
import frontend.operators as ops
import errors

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
t_plus = ops.PLUS.op_regex()
t_minus = ops.MINUS.op_regex()
t_times = ops.TIMES.op_regex()
t_divide = ops.DIV.op_regex()
t_mod = ops.MOD.op_regex()
t_not = ops.NOT.op_regex()
t_or = ops.OR.op_regex()
t_and = ops.AND.op_regex()
t_lt = ops.LT.op_regex()
t_le = ops.LE.op_regex()
t_gt = ops.GT.op_regex()
t_ge = ops.GE.op_regex()
t_eq = ops.EQ.op_regex()
t_ne = ops.NE.op_regex()

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
    raise errors.IllegalCharacterError(t.lexer.lineno, t.value[0])

lexer = lex.lex(debug=False)
