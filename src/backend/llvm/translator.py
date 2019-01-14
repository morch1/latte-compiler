import frontend
import backend.llvm as llvm
from itertools import count
from functools import wraps
from frontend.types import TYPE_STRING, TYPE_BOOL, TYPE_INT, TYPE_VOID

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
    TYPE_INT: llvm.TYPE_INT,
    TYPE_BOOL:  llvm.TYPE_BOOL,
    TYPE_STRING: llvm.TYPE_STRING,
    TYPE_VOID: llvm.TYPE_VOID,
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


@translator(frontend.ExpUnOp)
def translate(self, venv):
    e1v = self.exp.translate(venv)
    v = fresh_temp()
    if self.op == '-':
        builder.add_stmt(llvm.StmtBinOp(v, llvm.OP_SUB, llvm.TYPE_INT, 0, e1v))
    elif self.op == '!':
        builder.add_stmt(llvm.StmtBinOp(v, llvm.OP_EQ, llvm.TYPE_BOOL, e1v, 0))
    return v

@translator(frontend.ExpBinOp)
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
    elif self.exp1.type == TYPE_STRING:
        e2v = self.exp2.translate(venv)
        if self.op == '+':
            builder.add_stmt(llvm.StmtCall(v, llvm.TYPE_STRING, '_addStrings', [(llvm.TYPE_STRING, e1v), (llvm.TYPE_STRING, e2v)]))
        else:
            builder.add_stmt(llvm.StmtCall(v, llvm.TYPE_BOOL, '_compareStrings', [(llvm.TYPE_INT, COMP_OP_IDS[self.op]), (llvm.TYPE_STRING, e1v), (llvm.TYPE_STRING, e2v)]))
    else:
        e2v = self.exp2.translate(venv)
        builder.add_stmt(llvm.StmtBinOp(v, BIN_OPS[self.op], TYPES[self.exp1.type], e1v, e2v))
    return v

@translator(frontend.ExpVar)
def translate(self, venv):
    a = venv[self.id]
    v = fresh_temp()
    builder.add_stmt(llvm.StmtLoad(v, TYPES[self.type], a))
    return v

@translator(frontend.ExpIntConst)
def translate(self, venv):
    return self.val

@translator(frontend.ExpStringConst)
def translate(self, venv):
    if self.val not in strlits:
        lit = llvm.StrLit(self.val)
        gaddr = fresh_global()
        strlits[self.val] = llvm.GlobalDef(gaddr, lit.type, lit)
    g = strlits[self.val]
    v = fresh_temp()
    builder.add_stmt(llvm.StmtGetGlobal(v, g.type, g.addr))
    return v

@translator(frontend.ExpBoolConst)
def translate(self, venv):
    return int(self.val)

@translator(frontend.ExpFun)
def translate(self, venv):
    args = []
    for exp in self.args:
        ev = exp.translate(venv)
        args.append((TYPES[exp.type], ev))
    if self.type == TYPE_VOID:
        v = None
    else:
        v = fresh_temp()
    builder.add_stmt(llvm.StmtCall(v, TYPES[self.type], self.fid, args))
    return v


@translator(frontend.LhsVar)
def translate(self, venv):
    return venv[self.id]


@translator(frontend.StmtSkip)
def translate(self, venv):
    return venv

@translator(frontend.StmtDecl)
def translate(self, venv):
    if self.type == TYPE_STRING:
        if '' not in strlits:
            lit = llvm.StrLit('')
            gaddr = fresh_global()
            strlits[''] = llvm.GlobalDef(gaddr, lit.type, lit)
        g = strlits['']
        v = fresh_temp()
        builder.add_stmt(llvm.StmtGetGlobal(v, g.type, g.addr))
    elif self.type in [TYPE_BOOL, TYPE_INT]:
        v = 0
    else:
        assert False
    nvenv = venv.copy()
    a = fresh_loc()
    nvenv[self.id] = a
    builder.add_stmt(llvm.StmtAlloc(a, TYPES[self.type]))
    builder.add_stmt(llvm.StmtStore(TYPES[self.type], v, a))
    return nvenv

@translator(frontend.StmtDeclInit)
def translate(self, venv):
    e1v = self.exp.translate(venv)
    nvenv = venv.copy()
    a = fresh_loc()
    nvenv[self.id] = a
    builder.add_stmt(llvm.StmtAlloc(a, TYPES[self.type]))
    builder.add_stmt(llvm.StmtStore(TYPES[self.exp.type], e1v, a))
    return nvenv

@translator(frontend.StmtAss)
def translate(self, venv):
    a = self.lhs.translate(venv)
    e1v = self.exp.translate(venv)
    builder.add_stmt(llvm.StmtStore(TYPES[self.exp.type], e1v, a))
    return venv

@translator(frontend.StmtReturn)
def translate(self, venv):
    e1v = self.exp.translate(venv)
    builder.add_stmt(llvm.StmtReturn(TYPES[self.exp.type], e1v))
    return venv

@translator(frontend.StmtVoidReturn)
def translate(self, venv):
    builder.add_stmt(llvm.StmtVoidReturn())
    return venv

@translator(frontend.StmtIf)
def translate(self, venv):
    ltrue = fresh_label()
    lfalse = fresh_label()
    cv = self.cond.translate(venv)
    builder.add_stmt(llvm.StmtCondJump(cv, ltrue, lfalse))
    builder.new_block(ltrue)
    self.stmt.translate(venv)
    if not self.stmt.returns:
        builder.add_stmt(llvm.StmtJump(lfalse))
    builder.new_block(lfalse)
    return venv

@translator(frontend.StmtIfElse)
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

@translator(frontend.StmtWhile)
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
    if not self.stmt.returns:
        builder.add_stmt(llvm.StmtJump(lcond))
    builder.new_block(lfalse)
    return venv

@translator(frontend.StmtExp)
def translate(self, venv):
    self.exp.translate(venv)
    return venv

@translator(frontend.StmtBlock)
def translate(self, venv):
    nvenv = venv.copy()
    for block_stmt in self.stmts:
        nvenv = block_stmt.translate(nvenv)
    return venv


@translator(frontend.BuiltinFunDecl)
def translate(self):
    t = TYPES[self.type]
    args = [TYPES[a.type] for a in self.args]
    return llvm.BuiltinFunDecl(t, self.id.replace('$', '_'), args)

@translator(frontend.TopDef)
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
    t = TYPES[self.type]
    args = [(TYPES[a.type], arg_tmps[a.id]) for a in self.args]
    return llvm.TopDef(t, self.id, args, builder.blocks)

@translator(frontend.Program)
def translate(self):
    topdefs = []
    for topdef in self.topdefs:
        itopdef = topdef.translate()
        topdefs.append(itopdef)
    return llvm.Program(topdefs, list(strlits.values()))
