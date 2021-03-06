import frontend
import frontend.types as ft
import backend.llvm as llvm
from backend.llvm.types import TYPE_VOID, TYPE_I1, TYPE_I8P, TYPE_I32, TYPE_I64, TYPE_I1A, TYPE_I64A, TYPE_I8PA
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
        # add current block as predecessor where needed
        for b in self.blocks:
            if b.label in self.current_block.succlabels:
                b.preds.append(self.current_block)
                self.current_block.succlabels.remove(b.label)
                self.current_block.succs.append(b)
        new_block = llvm.Block(label)
        # add new block as successor where needed
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
    ft.TYPE_INT: TYPE_I64,
    ft.TYPE_INT_ARRAY: TYPE_I64A,
    ft.TYPE_BOOL:  TYPE_I1,
    ft.TYPE_BOOL_ARRAY: TYPE_I1A,
    ft.TYPE_STRING: TYPE_I8P,
    ft.TYPE_STRING_ARRAY: TYPE_I8PA,
    ft.TYPE_VOID: TYPE_VOID,
}

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
    '%': llvm.OP_REM,
}

COMP_OP_IDS = dict(zip(BIN_OPS.keys(), range(6)))


builder: Builder = None
strlits = {}


@translator(frontend.ExpUnOp)
def translate(self, venv):
    e1v = self.exp.translate(venv)
    v = fresh_temp()
    if self.op == '-':
        builder.add_stmt(llvm.StmtBinOp(v, llvm.OP_SUB, TYPE_I64, 0, e1v))
    elif self.op == '!':
        builder.add_stmt(llvm.StmtBinOp(v, llvm.OP_EQ, TYPE_I1, e1v, 0))
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
        builder.add_stmt(llvm.StmtPhi(v, TYPE_I1, [(self.op == '||' and 1 or 0, e1b), (e2v, e2b)]))
    elif self.exp1.type == ft.TYPE_STRING:
        e2v = self.exp2.translate(venv)
        if self.op == '+':
            builder.add_stmt(llvm.StmtCall(v, TYPE_I8P, '_addStrings', [(TYPE_I8P, e1v), (TYPE_I8P, e2v)]))
        else:
            builder.add_stmt(llvm.StmtCall(v, TYPE_I1, '_compareStrings', [(TYPE_I64, COMP_OP_IDS[self.op]), (TYPE_I8P, e1v), (TYPE_I8P, e2v)]))
    else:
        e2v = self.exp2.translate(venv)
        builder.add_stmt(llvm.StmtBinOp(v, BIN_OPS[self.op], TYPES[self.exp1.type], e1v, e2v))
    return v

@translator(frontend.ExpVar)
def translate(self, venv):
    a = venv[self.id]
    v = fresh_temp()
    builder.add_stmt(llvm.StmtLoad(v, TYPES[self.type], a, noopt=self.type.is_array_type))
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
    builder.add_stmt(llvm.StmtGetElementPtr(v, g.type, g.addr, [(TYPE_I64, 0), (TYPE_I64, 0)]))
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
    if self.type == ft.TYPE_VOID:
        v = None
    else:
        v = fresh_temp()
    builder.add_stmt(llvm.StmtCall(v, TYPES[self.type], self.fid, args))
    return v

@translator(frontend.ExpArray)
def translate(self, venv):
    idxv = self.idx.translate(venv)
    varrp = fresh_temp()  # pointer to array inside struct
    builder.add_stmt(llvm.StmtGetElementPtr(varrp, TYPES[self.type.array_type], venv[self.id], [(TYPE_I64, 0), (TYPE_I32, 1)]))
    varr = fresh_temp()  # actual array
    builder.add_stmt(llvm.StmtLoad(varr, TYPES[self.type] + '*', varrp, noopt=True))
    velem = fresh_temp()  # pointer to element
    builder.add_stmt(llvm.StmtGetElementPtr(velem, TYPES[self.type], varr, [(TYPE_I64, idxv)]))
    v = fresh_temp()
    builder.add_stmt(llvm.StmtLoad(v, TYPES[self.type], velem, noopt=True))
    return v

@translator(frontend.ExpAttr)
def translate(self, venv):
    if self.attr == 'length':
        v = fresh_temp()
        builder.add_stmt(llvm.StmtGetElementPtr(v, TYPES[self.array_type], venv[self.id], [(TYPE_I64, 0), (TYPE_I32, 0)]))
        v2 = fresh_temp()
        builder.add_stmt(llvm.StmtLoad(v2, TYPES[self.type], v, noopt=True))
        return v2
    else:
        assert False

@translator(frontend.ExpNewArray)
def translate(self, venv):
    lenv = self.len.translate(venv)
    velems = fresh_temp()  # allocate memory for elements
    builder.add_stmt(llvm.StmtAllocArray(velems, TYPES[self.elem_type], lenv))
    vstruct = fresh_temp()  # allocate memory for array struct (len, elements)
    builder.add_stmt(llvm.StmtAlloc(vstruct, TYPES[self.type], noopt=True))
    vstructelems = fresh_temp()  # store pointer to elements in struct
    builder.add_stmt(llvm.StmtGetElementPtr(vstructelems, TYPES[self.type], vstruct, [(TYPE_I64, 0), (TYPE_I32, 1)]))
    builder.add_stmt(llvm.StmtStore(TYPES[self.elem_type] + '*', velems, vstructelems, noopt=True))
    vstructlen = fresh_temp()  # store length value in struct
    builder.add_stmt(llvm.StmtGetElementPtr(vstructlen, TYPES[self.type], vstruct, [(TYPE_I64, 0), (TYPE_I32, 0)]))
    builder.add_stmt(llvm.StmtStore(TYPE_I64, lenv, vstructlen, noopt=True))
    v = fresh_temp()
    builder.add_stmt(llvm.StmtLoad(v, TYPES[self.type], vstruct, noopt=True))
    return v


@translator(frontend.LhsVar)
def translate(self, venv):
    return venv[self.id]

@translator(frontend.LhsArray)
def translate(self, venv):
    idxv = self.idx.translate(venv)
    varrp = fresh_temp()
    builder.add_stmt(llvm.StmtGetElementPtr(varrp, TYPES[self.type.array_type], venv[self.id], [(TYPE_I64, 0), (TYPE_I32, 1)]))
    varr = fresh_temp()
    builder.add_stmt(llvm.StmtLoad(varr, TYPES[self.type] + '*', varrp, noopt=True))
    velem = fresh_temp()
    builder.add_stmt(llvm.StmtGetElementPtr(velem, TYPES[self.type], varr, [(TYPE_I64, idxv)]))
    return velem


@translator(frontend.StmtSkip)
def translate(self, venv):
    return venv

@translator(frontend.StmtDecl)
def translate(self, venv):
    if self.type == ft.TYPE_STRING:
        if '' not in strlits:
            lit = llvm.StrLit('')
            gaddr = fresh_global()
            strlits[''] = llvm.GlobalDef(gaddr, lit.type, lit)
        g = strlits['']
        v = fresh_temp()
        builder.add_stmt(llvm.StmtGetElementPtr(v, g.type, g.addr, [(TYPE_I64, 0), (TYPE_I64, 0)]))
    elif self.type in [ft.TYPE_BOOL, ft.TYPE_INT]:
        v = 0
    nvenv = venv.copy()
    a = fresh_loc()
    nvenv[self.id] = a
    builder.add_stmt(llvm.StmtAlloc(a, TYPES[self.type], noopt=self.type.is_array_type))
    if not self.type.is_array_type:
        builder.add_stmt(llvm.StmtStore(TYPES[self.type], v, a))
    return nvenv

@translator(frontend.StmtDeclInit)
def translate(self, venv):
    e1v = self.exp.translate(venv)
    nvenv = venv.copy()
    a = fresh_loc()
    nvenv[self.id] = a
    builder.add_stmt(llvm.StmtAlloc(a, TYPES[self.type], noopt=self.type.is_array_type))
    builder.add_stmt(llvm.StmtStore(TYPES[self.exp.type], e1v, a, noopt=self.type.is_array_type))
    return nvenv

@translator(frontend.StmtAss)
def translate(self, venv):
    a = self.lhs.translate(venv)
    e1v = self.exp.translate(venv)
    builder.add_stmt(llvm.StmtStore(TYPES[self.exp.type], e1v, a, noopt=isinstance(self, frontend.StmtAssArray) or self.lhs.type.is_array_type))
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
    if not self.returns:
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

@translator(frontend.StmtWhileTrue)
def translate(self, venv):
    lloop = fresh_label()
    builder.add_stmt(llvm.StmtJump(lloop))
    builder.new_block(lloop)
    self.stmt.translate(venv)
    builder.add_stmt(llvm.StmtJump(lloop))
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
            llvm.StmtAlloc(arg_loc, arg_type, noopt=arg.type.is_array_type),
            llvm.StmtStore(arg_type, arg_tmp, arg_loc, noopt=arg.type.is_array_type),
        ])
    self.block.translate(venv)
    t = TYPES[self.type]
    args = [(TYPES[a.type], arg_tmps[a.id]) for a in self.args]
    return llvm.TopDef(t, self.id, args, builder.blocks)

def translate_program(self: frontend.Program):
    topdefs = []
    for topdef in self.topdefs:
        itopdef = topdef.translate()
        topdefs.append(itopdef)
    return llvm.Program(topdefs, list(strlits.values()))
