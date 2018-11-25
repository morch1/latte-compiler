import ply.yacc as yacc
from ins_lex import lexer, tokens
from errors import ParsingError
from ins_abs import StmtExp, LhsVar, ExpBinOp, ExpUnOp, ExpVar, StmtAssVar, Block, StmtDecl, Item, ItemInit, \
    StmtList, ItemList, StmtEmpty, ExpInt, ExpString, ExpBool, ExpList, ExpApp, StmtInc, StmtDec, StmtReturn, \
    StmtVoidReturn, StmtIf, StmtIfElse, StmtWhile


def p_program(p):
    """program : stmts"""
    p[0] = p[1]


def p_stmts(p):
    """stmts : stmt stmts"""
    p[0] = StmtList(p.lexer.lineno, [p[1]] + p[2].items)

def p_stmts_empty(p):
    """stmts : """
    p[0] = StmtList(p.lexer.lineno, [])

def p_block(p):
    """block : lbracket stmts rbracket"""
    p[0] = Block(p.lexer.lineno, p[2])

def p_stmt_empty(p):
    """stmt : semi"""
    p[0] = StmtEmpty(p.lexer.lineno)

def p_stmt_block(p):
    """stmt : block"""
    p[0] = p[1]

def p_stmt_decl(p):
    """stmt : type items semi"""
    p[0] = StmtDecl(p.lexer.lineno, p[1], p[2])

def p_items(p):
    """items : item comma items """
    p[0] = ItemList(p.lexer.lineno, [p[1]] + p[3].items)

def p_items_one(p):
    """items : item"""
    p[0] = ItemList(p.lexer.lineno, [p[1]])

def p_item(p):
    """item : id"""
    p[0] = Item(p.lexer.lineno, p[1])

def p_item_init(p):
    """item : id equals exp"""
    p[0] = ItemInit(p.lexer.lineno, p[1], p[3])

def p_stmt_ass(p):
    """stmt : id equals exp semi"""
    p[0] = StmtAssVar(p.lexer.lineno, LhsVar(p.lexer.lineno, p[1]), p[3])

def p_stmt_inc(p):
    """stmt : id plusplus semi"""
    p[0] = StmtInc(p.lexer.lineno, LhsVar(p.lexer.lineno, p[1]))

def p_stmt_dec(p):
    """stmt : id minusminus semi"""
    p[0] = StmtDec(p.lexer.lineno, LhsVar(p.lexer.lineno, p[1]))

def p_stmt_return(p):
    """stmt : return exp semi"""
    p[0] = StmtReturn(p.lexer.lineno, p[2])

def p_stmt_void_return(p):
    """stmt : return semi"""
    p[0] = StmtVoidReturn(p.lexer.lineno)

def p_stmt_if(p):
    """stmt : if lparen exp rparen stmt"""
    p[0] = StmtIf(p.lexer.lineno, p[3], p[5])

def p_stmt_if_else(p):
    """stmt : if lparen exp rparen stmt else stmt"""
    p[0] = StmtIfElse(p.lexer.lineno, p[3], p[5], p[7])

def p_stmt_while(p):
    """stmt : while lparen exp rparen stmt"""
    p[0] = StmtWhile(p.lexer.lineno, p[3], p[5])

def p_stmt_exp(p):
    """stmt : exp semi"""
    p[0] = StmtExp(p.lexer.lineno, p[1])


def p_type(p):
    """type : int
            | string
            | boolean
            | void"""
    p[0] = p[1]


def p_exps(p):
    """exps : exp comma exps """
    p[0] = ExpList(p.lexer.lineno, [p[1]] + p[3].items)

def p_exps_one(p):
    """exps : exp"""
    p[0] = ExpList(p.lexer.lineno, [p[1]])

def p_exps_empty(p):
    """exps : """
    p[0] = ExpList(p.lexer.lineno, [])

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

def p_exp_id(p):
    """exp6 : id"""
    p[0] = ExpVar(p.lexer.lineno, p[1])

def p_exp_intconst(p):
    """exp6 : intconst"""
    p[0] = ExpInt(p.lexer.lineno, int(p[1]))

def p_exp_stringconst(p):
    """exp6 : stringconst"""
    p[0] = ExpString(p.lexer.lineno, p[1][1:-1])

def p_exp_boolconst(p):
    """exp6 : true
            | false"""
    p[0] = ExpBool(p.lexer.lineno, p[1] == "true")

def p_exp_app(p):
    """exp6 : id lparen exps rparen"""
    p[0] = ExpApp(p.lexer.lineno, p[1], p[3])


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


parser = yacc.yacc(debug=False)


def parse(text):
    return parser.parse(text, lexer=lexer)
