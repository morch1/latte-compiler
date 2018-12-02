import ply.yacc as yacc

from lexer import lexer, tokens, precedence
from errors import ParsingError, InvalidTypeError
from abs import StmtExp, LhsVar, ExpBinOp, ExpUnOp, ExpVar, StmtAssVar, StmtBlock, StmtDecl, Item, ItemInit, \
    StmtList, ItemList, StmtEmpty, ExpInt, ExpString, ExpBool, ExpList, ExpApp, StmtInc, StmtDec, StmtReturn, \
    StmtVoidReturn, StmtIf, StmtIfElse, StmtWhile, ArgList, TopDefList, TopDef, Arg, Program
from ltypes import Type


def p_program(p):
    """program : topdefs"""
    p[0] = Program(p.lexer.lineno, p[1])

def p_topdefs(p):
    """topdefs : topdef topdefs"""
    p[0] = TopDefList(p.lexer.lineno, [p[1]] + p[2].items)

def p_topdefs_empty(p):
    """topdefs : """
    p[0] = TopDefList(p.lexer.lineno, [])

def p_topdef(p):
    """topdef : type id lparen args rparen block"""
    p[0] = TopDef(p.lexer.lineno, p[1], p[2], p[4], p[6])

def p_args(p):
    """args : arg comma args"""
    p[0] = ArgList(p.lexer.lineno, [p[1]] + p[2].items)

def p_args_empty(p):
    """args : """
    p[0] = ArgList(p.lexer.lineno, [])

def p_arg(p):
    """arg : type id"""
    p[0] = Arg(p.lexer.lineno, p[1], p[2])


def p_stmts(p):
    """stmts : stmt stmts"""
    p[0] = StmtList(p.lexer.lineno, [p[1]] + p[2].items)

def p_stmts_empty(p):
    """stmts : """
    p[0] = StmtList(p.lexer.lineno, [])

def p_block(p):
    """block : lbrace stmts rbrace"""
    p[0] = StmtBlock(p.lexer.lineno, p[2])

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
    """type : id"""
    p[0] = Type.get_by_name(p[1], p.lexer.lineno)


def p_exps(p):
    """exps : exp comma exps """
    p[0] = ExpList(p.lexer.lineno, [p[1]] + p[3].items)

def p_exps_one(p):
    """exps : exp"""
    p[0] = ExpList(p.lexer.lineno, [p[1]])

def p_exps_empty(p):
    """exps : """
    p[0] = ExpList(p.lexer.lineno, [])

def p_exp_binop(p):
    """exp : exp or exp
           | exp and exp
           | exp lt exp
           | exp le exp
           | exp gt exp
           | exp ge exp
           | exp eq exp
           | exp ne exp
           | exp plus exp
           | exp minus exp
           | exp times exp
           | exp divide exp
           | exp mod exp """
    p[0] = ExpBinOp(p.lexer.lineno, p[2], p[1], p[3])

def p_exp_unop(p):
    """exp : minus exp %prec uminus
           | not exp"""
    p[0] = ExpUnOp(p.lexer.lineno, p[1], p[2])

def p_exp_id(p):
    """exp : id"""
    p[0] = ExpVar(p.lexer.lineno, p[1])

def p_exp_intconst(p):
    """exp : intconst"""
    p[0] = ExpInt(p.lexer.lineno, int(p[1]))

def p_exp_stringconst(p):
    """exp : stringconst"""
    p[0] = ExpString(p.lexer.lineno, p[1][1:-1])

def p_exp_boolconst(p):
    """exp : true
           | false"""
    p[0] = ExpBool(p.lexer.lineno, p[1] == "true")

def p_exp_app(p):
    """exp : id lparen exps rparen"""
    p[0] = ExpApp(p.lexer.lineno, p[1], p[3])


def p_error(p):
    raise ParsingError(p and p.lexer.lineno or None)


parser = yacc.yacc(debug=False)

def parse(text):
    return parser.parse(text, lexer=lexer)
