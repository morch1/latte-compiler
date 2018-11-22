import ply.lex as lex
import ply.yacc as yacc
from errors import ParsingError, IllegalCharacter
from ins_abs import StmtExp, LhsVar, ExpBinOp, ExpUnOp, ExpVar, ExpConst, StmtAssVar, Block, \
    StmtList, StmtDecl, Item, ItemInit

reserved = ("int", "string", "boolean", "void")
tokens = reserved + (
    # literals
    "id", "num",
    # operators
    "plus", "minus", "times", "divide", "mod",
    "not", "or", "and",
    "lt", "le", "gt", "ge", "eq", "ne",
    # assignment
    "equals",
    # delimeters
    "lparen", "rparen", "lbracket", "rbracket",
    "semi", "comma",
)
t_ignore = ' \t'  # ignore whitespaces
t_ignore_comment = r'\#.*'


def t_newline(t):
    r"""\n+"""
    t.lexer.lineno += len(t.value)


def t_error(t):
    raise IllegalCharacter(t.lexer.lineno, t.value[0])


t_int = r'int'
t_string = r'string'
t_boolean = r'boolean'
t_void = r'void'


t_id = r'[a-zA-Z_]\w*'
def t_num(t):
    r"""\d+"""
    t.value = int(t.value)
    return t

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

t_lparen = r'\('
t_rparen = r'\)'
t_lbracket = r'\{'
t_rbracket = r'\}'
t_semi = r';'
t_comma = r','

def p_program(p):
    """program : stmts"""
    p[0] = p[1]


def p_stmts(p):
    """stmts : stmt stmts"""
    p[0] = StmtList(p.lexer.lineno, [p[1]] + p[2].stmts)


def p_stmts_empty(p):
    """stmts : """
    p[0] = StmtList(p.lexer.lineno, [])


def p_block(p):
    """block : lbracket stmts rbracket"""
    p[0] = Block(p.lexer.lineno, p[2])


def p_stmt_block(p):
    """stmt : block"""
    p[0] = p[1]


def p_type(p):
    """type : int
            | string
            | boolean
            | void"""
    p[0] = p[1]


def p_items(p):
    """items : item comma items """
    p[0] = [p[1]] + p[3]


def p_items_one(p):
    """items : item"""
    p[0] = [p[1]]


def p_item(p):
    """item : id"""
    p[0] = Item(p.lexer.lineno, p[1])


def p_item_init(p):
    """item : id equals exp"""
    p[0] = ItemInit(p.lexer.lineno, p[1], p[3])


def p_stmt_decl(p):
    """stmt : type items semi"""
    p[0] = StmtDecl(p.lexer.lineno, p[1], [p[2]])


def p_stmt_ass(p):
    """stmt : id equals exp semi"""
    p[0] = StmtAssVar(p.lexer.lineno, LhsVar(p.lexer.lineno, p[1]), p[3])


def p_stmt_exp(p):
    """stmt : exp semi"""
    p[0] = StmtExp(p.lexer.lineno, p[1])


def p_exp_or(p):
    """exp : exp1 or exp"""
    p[0] = ExpBinOp(p.lexer.lineno, p[2], p[1], p[3])


def p_exp_and(p):
    """exp1 : exp2 and exp1"""
    p[0] = ExpBinOp(p.lexer.lineno, p[2], p[1], p[3])


def p_exp_rel(p):
    """exp2 : exp2 lt exp3
            | exp2 le exp3
            | exp2 gt exp3
            | exp2 ge exp3
            | exp2 eq exp3
            | exp2 ne exp3"""
    p[0] = ExpBinOp(p.lexer.lineno, p[2], p[1], p[3])


def p_exp_add(p):
    """exp3 : exp3 plus exp4
            | exp3 minus exp4"""
    p[0] = ExpBinOp(p.lexer.lineno, p[2], p[1], p[3])


def p_exp_mul(p):
    """exp4 : exp4 times exp5
            | exp4 divide exp5
            | exp4 mod exp5"""
    p[0] = ExpBinOp(p.lexer.lineno, p[2], p[1], p[3])


def p_exp_neg(p):
    """exp5 : minus exp6
            | not exp6"""
    p[0] = ExpUnOp(p.lexer.lineno, p[1], p[2])


def p_exp_var(p):
    """exp6 : id"""
    p[0] = ExpVar(p.lexer.lineno, p[1])


def p_exp_const(p):
    """exp6 : num"""
    p[0] = ExpConst(p.lexer.lineno, p[1])


def p_exp0(p):
    """exp : exp1"""
    p[0] = p[1]


def p_exp1(p):
    """exp1 : exp2"""
    p[0] = p[1]
def p_exp2(p):
    """exp2 : exp3"""
    p[0] = p[1]
def p_exp3(p):
    """exp3 : exp4"""
    p[0] = p[1]
def p_exp4(p):
    """exp4 : exp5"""
    p[0] = p[1]
def p_exp5(p):
    """exp5 : exp6"""
    p[0] = p[1]
def p_exp6(p):
    """exp6 : lparen exp rparen"""
    p[0] = p[2]


def p_error(p):
    raise ParsingError(p and p.lexer.lineno or None)


lexer = lex.lex(debug=False)
parser = yacc.yacc(debug=True)


def parse(text):
    return parser.parse(text, lexer=lexer)
