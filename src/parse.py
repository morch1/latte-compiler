import ply.yacc as yacc

from components.expression import ExpBinOp, ExpUnOp, ExpVar, ExpIntConst, ExpStringConst, ExpBoolConst, ExpApp
from components.program import Program, TopDef, Arg
from components.statement import StmtBlock, Stmt, StmtDecl, StmtAssVar, LhsVar, StmtInc, StmtDec, StmtReturn, \
    StmtVoidReturn, StmtIf, StmtIfElse, StmtWhile, StmtExp
from lexer import lexer, tokens, precedence
from errors import ParsingError, InvalidTypeError, InvalidOperatorError
from ltypes import Type
from operators import Operator


def p_program(p):
    """program : topdefs"""
    p[0] = Program(p.lexer.lineno, p[1])

def p_topdefs(p):
    """topdefs : topdef topdefs"""
    p[0] = [p[1]] + p[2]

def p_topdefs_empty(p):
    """topdefs : """
    p[0] = []

def p_topdef(p):
    """topdef : type id lparen args rparen block"""
    p[0] = TopDef(p.lexer.lineno, p[1], p[2], p[4], p[6])

def p_args(p):
    """args : arg comma args"""
    p[0] = [p[1]] + p[3]

def p_args_one(p):
    """args : arg"""
    p[0] = [p[1]]

def p_args_empty(p):
    """args : """
    p[0] = []

def p_arg(p):
    """arg : type id"""
    p[0] = Arg(p.lexer.lineno, p[1], p[2])


def p_stmts(p):
    """stmts : stmt stmts"""
    if isinstance(p[1], list):
        p[0] = p[1] + p[2]
    else:
        p[0] = [p[1]] + p[2]

def p_stmts_empty(p):
    """stmts : """
    p[0] = []

def p_block(p):
    """block : lbrace stmts rbrace"""
    p[0] = StmtBlock(p.lexer.lineno, p[2])

def p_stmt_empty(p):
    """stmt : semi"""
    p[0] = Stmt(p.lexer.lineno)

def p_stmt_block(p):
    """stmt : block"""
    p[0] = p[1]

def p_stmt_decl(p):
    """stmt : type decls semi"""
    stmts = []
    for decl in p[2]:
        stmts.append(StmtDecl(p.lexer.lineno, p[1], decl[0]))
        if len(decl) == 2:
            stmts.append(StmtAssVar(p.lexer.lineno, LhsVar(p.lexer.lineno, decl[0]), decl[1]))
    p[0] = stmts

def p_decls(p):
    """decls : decl comma decls """
    p[0] = [p[1]] + p[3]

def p_decls_one(p):
    """decls : decl"""
    p[0] = [p[1]]

def p_decl(p):
    """decl : id"""
    p[0] = (p[1],)

def p_decl_init(p):
    """decl : id equals exp"""
    p[0] = (p[1], p[3])

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
    try:
        p[0] = Type.get_by_name(p[1])
    except InvalidTypeError as ex:
        ex.line = p.lexer.lineno
        raise ex


def p_exps(p):
    """exps : exp comma exps """
    p[0] = [p[1]] + p[3]

def p_exps_one(p):
    """exps : exp"""
    p[0] = [p[1]]

def p_exps_empty(p):
    """exps : """
    p[0] = []

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
    try:
        op = Operator.get_by_name(p[2])
    except InvalidOperatorError as ex:
        ex.line = p.lexer.lineno
        raise ex
    p[0] = ExpBinOp(p.lexer.lineno, op, p[1], p[3])

def p_exp_unop(p):
    """exp : minus exp %prec uminus
           | not exp"""
    try:
        op = Operator.get_by_name(p[1])
    except InvalidOperatorError as ex:
        ex.line = p.lexer.lineno
        raise ex
    p[0] = ExpUnOp(p.lexer.lineno, op, p[2])

def p_exp_id(p):
    """exp : id"""
    p[0] = ExpVar(p.lexer.lineno, p[1])

def p_exp_intconst(p):
    """exp : intconst"""
    p[0] = ExpIntConst(p.lexer.lineno, int(p[1]))

def p_exp_stringconst(p):
    """exp : stringconst"""
    p[0] = ExpStringConst(p.lexer.lineno, p[1][1:-1])

def p_exp_boolconst(p):
    """exp : true
           | false"""
    p[0] = ExpBoolConst(p.lexer.lineno, p[1] == "true")

def p_exp_app(p):
    """exp : id lparen exps rparen"""
    p[0] = ExpApp(p.lexer.lineno, p[1], p[3])

def p_exp_paren(p):
    """exp : lparen exp rparen"""
    p[0] = p[2]


def p_error(p):
    raise ParsingError(p and p.lexer.lineno or None)


parser = yacc.yacc(debug=False)

def parse(text):
    return parser.parse(text, lexer=lexer)
