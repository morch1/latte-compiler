import frontend.ast as ast
import backend.llvm as llvm
import errors
import re
from itertools import count
from functools import wraps

def translator(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        setattr(cls, 'translate', wrapper)
        return func
    return decorator

class Builder:
    def __init__(self):
        self.current_block: llvm.Block = None
        self.blocks = []

    def add_stmt(self, stmt):
        if isinstance(stmt, list):
            for s in stmt:
                self.add_stmt(s)
            return
        self.current_block.stmts.append(stmt)
        if isinstance(stmt, llvm.StmtJump):
            self.current_block.succlabels.add(stmt.label)
        elif isinstance(stmt, llvm.StmtCondJump):
            self.current_block.succlabels.update({stmt.flabel, stmt.tlabel})

    def new_block(self, label):
        new_block = llvm.Block(label)
        for b in self.blocks:
            if label in b.succlabels:
                new_block.preds.append(b)
                b.succlabels.remove(label)
                b.succs.append(new_block)
        self.current_block = new_block
        self.blocks.append(new_block)


id_gen = None

def fresh_label():
    return f'L{id_gen.__next__()}'

def fresh_temp():
    return f'%t{id_gen.__next__()}'

def fresh_loc():
    return f'%loc{id_gen.__next__()}'

global_gen = count(1)
def fresh_global():
    return f'@G{global_gen.__next__()}'


TYPES = {
    ast.TYPE_INT: llvm.TYPE_INT,
    ast.TYPE_BOOL:  llvm.TYPE_BOOL,
    ast.TYPE_STRING: llvm.TYPE_STRING,
    ast.TYPE_VOID: llvm.TYPE_VOID,
}

def TYPE_STRCONST(l):
    return f'[ {l} x {llvm.TYPE_CHAR} ]'

BIN_OPS = {
    '==': llvm.OP_EQ,
    '!=': llvm.OP_NE,
    '<': llvm.OP_LT,
    '<=': llvm.OP_LE,
    '>': llvm.OP_GT,
    '>=': llvm.OP_GE,
    '+': llvm.OP_ADD,
    '-': llvm.OP_SUB,
    '*': llvm.OP_MUL,
    '/': llvm.OP_DIV,
    '%': llvm.OP_MOD,
}

COMP_OP_IDS = dict(zip(BIN_OPS.keys(), range(6)))


builder: Builder = None
strlits = {}


@translator(ast.ExpUnOp)
def translate(self, venv):
    e1v = self.exp.translate(venv)
    v = fresh_temp()
    if self.op == '-':
        builder.add_stmt(llvm.StmtBinOp(v, llvm.OP_SUB, llvm.TYPE_INT, 0, e1v))
    elif self.op == '!':
        builder.add_stmt(llvm.StmtBinOp(v, llvm.OP_EQ, llvm.TYPE_BOOL, e1v, 0))
    return v

@translator(ast.ExpBinOp)
def translate(self, venv):
    e1v = self.exp1.translate(venv)
    v = fresh_temp()
    if self.op in ['&&', '||']:
        e1b = builder.current_block.label
        lnext = fresh_label()
        lend = fresh_label()
        if self.op == '&&':
            builder.add_stmt(llvm.StmtCondJump(e1v, lnext, lend))
        elif self.op == '||':
            builder.add_stmt(llvm.StmtCondJump(e1v, lend, lnext))
        builder.new_block(lnext)
        e2v = self.exp2.translate(venv)
        e2b = builder.current_block.label
        builder.add_stmt(llvm.StmtJump(lend))
        builder.new_block(lend)
        builder.add_stmt(llvm.StmtPhi(v, llvm.TYPE_BOOL, [(self.op == '||' and 1 or 0, e1b), (e2v, e2b)]))
    elif self.exp1.type == ast.TYPE_STRING:
        e2v = self.exp2.translate(venv)
        if self.op == '+':
            builder.add_stmt(llvm.StmtCall(v, llvm.TYPE_STRING, '_addStrings', [(llvm.TYPE_STRING, e1v), (llvm.TYPE_STRING, e2v)]))
        else:
            builder.add_stmt(llvm.StmtCall(v, llvm.TYPE_BOOL, '_compareStrings', [(llvm.TYPE_INT, COMP_OP_IDS[self.op]), (llvm.TYPE_STRING, e1v), (llvm.TYPE_STRING, e2v)]))
    else:
        e2v = self.exp2.translate(venv)
        builder.add_stmt(llvm.StmtBinOp(v, BIN_OPS[self.op], TYPES[self.exp1.type], e1v, e2v))
    return v

@translator(ast.ExpVar)
def translate(self, venv):
    a = venv[self.id]
    v = fresh_temp()
    builder.add_stmt(llvm.StmtLoad(v, TYPES[self.type], a))
    return v

@translator(ast.ExpIntConst)
def translate(self, venv):
    return self.val

@translator(ast.ExpStringConst)
def translate(self, venv):
    if self.val not in strlits:
        lit = llvm.StrLit(self.val)
        gaddr = fresh_global()
        strlits[self.val] = llvm.GlobalDef(gaddr, lit.type, lit)
    g = strlits[self.val]
    v = fresh_temp()
    builder.add_stmt(llvm.StmtGetGlobal(v, g.type, g.addr))
    return v

@translator(ast.ExpBoolConst)
def translate(self, venv):
    return int(self.val)

@translator(ast.ExpFun)
def translate(self, venv):
    args = []
    for exp in self.args:
        ev = exp.translate(venv)
        args.append((TYPES[exp.type], ev))
    if self.type == ast.TYPE_VOID:
        v = None
    else:
        v = fresh_temp()
    builder.add_stmt(llvm.StmtCall(v, TYPES[self.type], self.fid, args))
    return v


@translator(ast.LhsVar)
def translate(self, venv):
    return venv[self.id]


@translator(ast.StmtSkip)
def translate(self, venv):
    return venv

@translator(ast.StmtDecl)
def translate(self, venv):
    if self.type == ast.TYPE_STRING:
        if '' not in strlits:
            lit = llvm.StrLit('')
            gaddr = fresh_global()
            strlits[''] = llvm.GlobalDef(gaddr, lit.type, lit)
        g = strlits['']
        v = fresh_temp()
        builder.add_stmt(llvm.StmtGetGlobal(v, g.type, g.addr))
    elif self.type in [ast.TYPE_BOOL, ast.TYPE_INT]:
        v = 0
    else:
        assert False
    nvenv = venv.copy()
    a = fresh_loc()
    nvenv[self.id] = a
    builder.add_stmt(llvm.StmtAlloc(a, TYPES[self.type]))
    builder.add_stmt(llvm.StmtStore(TYPES[self.type], v, a))
    return nvenv

@translator(ast.StmtDeclInit)
def translate(self, venv):
    e1v = self.exp.translate(venv)
    nvenv = venv.copy()
    a = fresh_loc()
    nvenv[self.id] = a
    builder.add_stmt(llvm.StmtAlloc(a, TYPES[self.type]))
    builder.add_stmt(llvm.StmtStore(TYPES[self.exp.type], e1v, a))
    return nvenv

@translator(ast.StmtAss)
def translate(self, venv):
    a = self.lhs.translate(venv)
    e1v = self.exp.translate(venv)
    builder.add_stmt(llvm.StmtStore(TYPES[self.exp.type], e1v, a))
    return venv

@translator(ast.StmtReturn)
def translate(self, venv):
    e1v = self.exp.translate(venv)
    builder.add_stmt(llvm.StmtReturn(TYPES[self.exp.type], e1v))
    return venv

@translator(ast.StmtVoidReturn)
def translate(self, venv):
    builder.add_stmt(llvm.StmtVoidReturn())
    return venv

@translator(ast.StmtIf)
def translate(self, venv):
    ltrue = fresh_label()
    lfalse = fresh_label()
    cv = self.cond.translate(venv)
    builder.add_stmt(llvm.StmtCondJump(cv, ltrue, lfalse))
    builder.new_block(ltrue)
    self.stmt.translate(venv)
    builder.add_stmt(llvm.StmtJump(lfalse))
    builder.new_block(lfalse)
    return venv

@translator(ast.StmtIfElse)
def translate(self, venv):
    ltrue = fresh_label()
    lfalse = fresh_label()
    lend = fresh_label()
    cv = self.cond.translate(venv)
    builder.add_stmt(llvm.StmtCondJump(cv, ltrue, lfalse))
    builder.new_block(ltrue)
    self.stmt.translate(venv)
    if not self.stmt.returns:
        builder.add_stmt(llvm.StmtJump(lend))
    builder.new_block(lfalse)
    self.stmt2.translate(venv)
    if not self.stmt2.returns:
        builder.add_stmt(llvm.StmtJump(lend))
        builder.new_block(lend)
    return venv

@translator(ast.StmtWhile)
def translate(self, venv):
    lcond = fresh_label()
    ltrue = fresh_label()
    lfalse = fresh_label()
    builder.add_stmt(llvm.StmtJump(lcond))
    builder.new_block(lcond)
    cv = self.cond.translate(venv)
    builder.add_stmt(llvm.StmtCondJump(cv, ltrue, lfalse))
    builder.new_block(ltrue)
    self.stmt.translate(venv)
    builder.add_stmt(llvm.StmtJump(lcond))
    builder.new_block(lfalse)
    return venv

@translator(ast.StmtExp)
def translate(self, venv):
    self.exp.translate(venv)
    return venv

@translator(ast.StmtBlock)
def translate(self, venv):
    nvenv = venv.copy()
    for block_stmt in self.stmts:
        nvenv = block_stmt.translate(nvenv)
        if block_stmt.returns:
            break
    return venv


@translator(ast.BuiltinFunDecl)
def translate(self):
    t = TYPES[self.type]
    args = [TYPES[a.type] for a in self.args]
    return llvm.BuiltinFunDecl(t, self.id.replace('$', '_'), args)

@translator(ast.TopDef)
def translate(self):
    global id_gen, builder
    id_gen = count(1)
    builder = Builder()
    lstart = fresh_label()
    builder.new_block(lstart)
    venv = {}
    arg_tmps = {}
    for arg in self.args:
        arg_tmp = fresh_temp()
        arg_tmps[arg.id] = arg_tmp
        arg_loc = fresh_loc()
        arg_type = TYPES[arg.type]
        venv[arg.id] = arg_loc
        builder.add_stmt([
            llvm.StmtAlloc(arg_loc, arg_type),
            llvm.StmtStore(arg_type, arg_tmp, arg_loc),
        ])
    self.block.translate(venv)
    if not self.block.returns:
        builder.add_stmt(llvm.StmtVoidReturn())
    t = TYPES[self.type]
    args = [(TYPES[a.type], arg_tmps[a.id]) for a in self.args]
    return llvm.TopDef(t, self.id, args, builder.blocks)

@translator(ast.Program)
def translate(self):
    topdefs = []
    for topdef in self.topdefs:
        itopdef = topdef.translate()
        topdefs.append(itopdef)
    return llvm.Program(topdefs, list(strlits.values()))
