import ply.yacc as yacc
import frontend
import errors
from frontend.lexer import tokens, precedence, lexer


def p_program(p):
    """program : topdefs"""
    p[0] = frontend.Program(p.lexer.lineno, p[1])

def p_topdefs(p):
    """topdefs : topdef topdefs"""
    p[0] = [p[1]] + p[2]

def p_topdefs_empty(p):
    """topdefs : """
    p[0] = []

def p_topdef(p):
    """topdef : type id lparen args rparen block"""
    p[0] = frontend.TopDef(p.lexer.lineno, p[1], p[2], p[4], p[6])

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
    p[0] = frontend.FunArg(p.lexer.lineno, p[1], p[2])


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
    p[0] = frontend.StmtBlock(p.lexer.lineno, p[2])

def p_stmt_empty(p):
    """stmt : semi"""
    p[0] = frontend.StmtSkip(p.lexer.lineno)

def p_stmt_block(p):
    """stmt : block"""
    p[0] = p[1]

def p_stmt_decl(p):
    """stmt : type decls semi"""
    stmts = []
    for decl in p[2]:
        if len(decl) == 2:
            stmts.append(frontend.StmtDeclInit(p.lexer.lineno, p[1], decl[0], decl[1]))
        else:
            stmts.append(frontend.StmtDecl(p.lexer.lineno, p[1], decl[0]))
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
    p[0] = frontend.StmtAssVar(p.lexer.lineno, frontend.LhsVar(p.lexer.lineno, p[1]), p[3])

def p_stmt_ass_array(p):
    """stmt : id lbracket exp rbracket equals exp semi"""
    p[0] = frontend.StmtAssArray(p.lexer.lineno, frontend.LhsArray(p.lexer.lineno, p[1], p[3]), p[6])

def p_stmt_inc(p):
    """stmt : id plusplus semi"""
    p[0] = frontend.StmtAssVar(p.lexer.lineno, frontend.LhsVar(p.lexer.lineno, p[1]), frontend.ExpBinOp(p.lexer.lineno, '+', frontend.ExpVar(p.lexer.lineno, p[1]), frontend.ExpIntConst(p.lexer.lineno, 1)))

def p_stmt_dec(p):
    """stmt : id minusminus semi"""
    p[0] = frontend.StmtAssVar(p.lexer.lineno, frontend.LhsVar(p.lexer.lineno, p[1]), frontend.ExpBinOp(p.lexer.lineno, '-', frontend.ExpVar(p.lexer.lineno, p[1]), frontend.ExpIntConst(p.lexer.lineno, 1)))

def p_stmt_return(p):
    """stmt : return exp semi"""
    p[0] = frontend.StmtReturn(p.lexer.lineno, p[2])

def p_stmt_void_return(p):
    """stmt : return semi"""
    p[0] = frontend.StmtVoidReturn(p.lexer.lineno)

def p_stmt_if(p):
    """stmt : if lparen exp rparen stmt"""
    p[0] = frontend.StmtIf(p.lexer.lineno, p[3], p[5])

def p_stmt_if_else(p):
    """stmt : if lparen exp rparen stmt else stmt"""
    p[0] = frontend.StmtIfElse(p.lexer.lineno, p[3], p[5], p[7])

def p_stmt_while(p):
    """stmt : while lparen exp rparen stmt"""
    p[0] = frontend.StmtWhile(p.lexer.lineno, p[3], p[5])

def p_stmt_foreach(p):
    """stmt : for lparen simple_type id colon id rparen stmt"""
    ln = p.lexer.lineno
    p[0] = frontend.StmtBlock(ln, [
        frontend.StmtDecl(ln, frontend.types.TYPE_INT, '$idx'),
        frontend.StmtWhile(ln,
            frontend.ExpBinOp(ln, '<', frontend.ExpVar(ln, '$idx'), frontend.ExpAttr(ln, p[6], 'length')),
            frontend.StmtBlock(ln, [
                frontend.StmtDeclInit(ln, p[3], p[4], frontend.ExpArray(ln, p[6], frontend.ExpVar(ln, '$idx'))),
                p[8],
                frontend.StmtAssVar(ln, frontend.LhsVar(ln, '$idx'), frontend.ExpBinOp(ln, '+', frontend.ExpVar(ln, '$idx'), frontend.ExpIntConst(ln, 1)))
            ])
        )
    ])

def p_stmt_exp(p):
    """stmt : exp semi"""
    p[0] = frontend.StmtExp(p.lexer.lineno, p[1])


def p_simple_type(p):
    """simple_type : id"""
    try:
        p[0] = frontend.Type.get_by_name(p[1])
    except errors.InvalidTypeError as ex:
        ex.line = p.lexer.lineno
        raise ex

def p_type_array(p):
    """type : id lbracket rbracket"""
    try:
        p[0] = frontend.Type.get_by_name(p[1]).array_type
    except errors.InvalidTypeError as ex:
        ex.line = p.lexer.lineno
        raise ex

def p_type(p):
    """type : simple_type"""
    p[0] = p[1]


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
    p[0] = frontend.ExpBinOp(p.lexer.lineno, p[2], p[1], p[3])

def p_exp_unop(p):
    """exp : minus exp %prec uminus
           | not exp"""
    p[0] = frontend.ExpUnOp(p.lexer.lineno, p[1], p[2])

def p_exp_id(p):
    """exp : id"""
    p[0] = frontend.ExpVar(p.lexer.lineno, p[1])

def p_exp_intconst(p):
    """exp : intconst"""
    p[0] = frontend.ExpIntConst(p.lexer.lineno, int(p[1]))

def p_exp_stringconst(p):
    """exp : stringconst"""
    p[0] = frontend.ExpStringConst(p.lexer.lineno, p[1][1:-1])

def p_exp_boolconst(p):
    """exp : true
           | false"""
    p[0] = frontend.ExpBoolConst(p.lexer.lineno, p[1] == "true")

def p_exp_fun(p):
    """exp : id lparen exps rparen"""
    p[0] = frontend.ExpFun(p.lexer.lineno, p[1], p[3])

def p_exp_array(p):
    """exp : id lbracket exp rbracket"""
    p[0] = frontend.ExpArray(p.lexer.lineno, p[1], p[3])

def p_exp_attr(p):
    """exp : id dot id"""
    p[0] = frontend.ExpAttr(p.lexer.lineno, p[1], p[3])

def p_exp_new(p):
    """exp : new simple_type lbracket exp rbracket"""
    p[0] = frontend.ExpNewArray(p.lexer.lineno, p[2], p[4])

def p_exp_paren(p):
    """exp : lparen exp rparen"""
    p[0] = p[2]


def p_error(p):
    raise errors.ParsingError(p and p.lexer.lineno or None)


parser = yacc.yacc(debug=False)

def parse(text):
    return parser.parse(text, lexer=lexer)
