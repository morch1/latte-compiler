import backend.llvm as llvm
import backend.llvm.translator as translator
from dataclasses import dataclass
from itertools import count

BIN_OPS = dict((v, k) for k, v in translator.BIN_OPS.items())
BIN_OPS[llvm.OP_DIV] = '//'

def optimize_function(f: llvm.TopDef):
    """replaces alloc/store/load statements with register operations"""
    id_gens = {}
    label2block = dict((b.label, b) for b in f.blocks)
    phi_map = dict((b, {}) for b in f.blocks)

    def get_live_vars(b: llvm.Block):
        dead = {}
        live = {}
        for s in b.stmts:
            if isinstance(s, llvm.StmtLoad) and s.addr not in dead:
                live[s.addr] = s.type
            elif isinstance(s, llvm.StmtStore):
                dead[s.addr] = s.type
        return live

    class StmtLocalPhi(llvm.StmtPhi):
        """
        used to differentiate new phi statements used for computing values of local variables
        from phi statements added earlier used for computing boolean expressions
        """
        pass

    for b in f.blocks:  # insert phis
        if len(b.preds) == 0:
            continue
        lvs = get_live_vars(b)

        # add phis for all variables live at the start of the block
        for lv, lvtype in lvs.items():
            b.stmts.insert(0, StmtLocalPhi(lv, lvtype, [(lv, p.label) for p in b.preds]))

    def fresh_loc(v):
        if v not in id_gens:
            id_gens[v] = count(1)
        return f'{v}.{id_gens[v].__next__()}'

    @dataclass
    class StmtAss:
        """fake assignment statement (%dst := %src)"""
        dst: str
        src: object

        def __str__(self):
            return f'{self.dst} = {self.src}'

    for b in f.blocks:  # ssaify
        nstmts = []
        pm = phi_map[b]
        for s in b.stmts:
            if isinstance(s, llvm.StmtStore):
                pm[s.addr] = fresh_loc(s.addr)
                nstmts.append(StmtAss(pm[s.addr], s.val))
            elif isinstance(s, StmtLocalPhi):
                pm[s.var] = fresh_loc(s.var)
                nstmts.append(StmtLocalPhi(pm[s.var], s.type, s.vals))
            elif isinstance(s, llvm.StmtLoad):
                nstmts.append(StmtAss(s.var, pm[s.addr]))
            elif isinstance(s, llvm.StmtAlloc):
                pass
            else:
                nstmts.append(s)
        b.stmts = nstmts

    extra_phis = dict((b, []) for b in f.blocks)

    def get_phi_val(b: llvm.Block, t, v):
        """
        - recursively finds value for phi statement in block's predecessors
        - remembers extra phi statements to be added if necessary
        """
        try:
            return phi_map[b][v]
        except KeyError:
            nv = fresh_loc(v)
            phi_map[b][v] = nv
            phi_vals = [(get_phi_val(p, t, v), p.label) for p in b.preds]
            if len(phi_vals) == 1:
                extra_phis[b].append(StmtAss(nv, phi_vals[0][0]))
            else:
                extra_phis[b].append(StmtLocalPhi(nv, t, phi_vals))
            return nv

    for b in f.blocks:  # fix phis
        nstmts = []
        for s in b.stmts:
            if isinstance(s, StmtLocalPhi):
                s.vals = [(get_phi_val(label2block[lbl], s.type, v), lbl) for v, lbl in s.vals]
                if len(s.vals) == 1:
                    nstmts.append(StmtAss(s.var, s.vals[0][0]))
                else:
                    nstmts.append(s)
            else:
                nstmts.append(s)
        b.stmts = nstmts

    for b in f.blocks:  # add extra phis
        b.stmts = extra_phis[b] + b.stmts

    def get_val(v):
        if v not in var_map:
            return v
        return get_val(var_map[v])

    def get_vals(b: llvm.Block):
        for s in b.stmts:
            if isinstance(s, llvm.StmtBinOp):
                s.arg1 = get_val(s.arg1)
                s.arg2 = get_val(s.arg2)
            elif isinstance(s, llvm.StmtCall):
                s.args = [(t, get_val(v)) for t, v in s.args]
            elif isinstance(s, llvm.StmtReturn):
                s.val = get_val(s.val)
            elif isinstance(s, llvm.StmtCondJump):
                s.cond = get_val(s.cond)
            elif isinstance(s, llvm.StmtPhi):
                s.vals = [(get_val(v), lbl) for v, lbl in s.vals]

    var_map = {}
    for b in f.blocks:  # make map of assignments
        for s in b.stmts:
            if isinstance(s, StmtAss):
                var_map[s.dst] = s.src

    for b in f.blocks:  # eliminate assignments
        get_vals(b)
        b.stmts = list(filter(lambda s: not isinstance(s, StmtAss), b.stmts))

    # return
    while True:
        var_map = {}
        for b in f.blocks:  # make map of constant expression values
            for s in b.stmts:
                if isinstance(s, llvm.StmtBinOp) and isinstance(s.arg1, int) and isinstance(s.arg2, int):
                    var_map[s.var] = int(eval(f'{s.arg1} {BIN_OPS[s.op]} {s.arg2}'))

        if len(var_map) == 0:  # stop if there are no more constant expressions
            break

        for b in f.blocks:  # eliminate constant expressions
            get_vals(b)
            b.stmts = list(filter(lambda s: not (isinstance(s, llvm.StmtBinOp) and s.var in var_map), b.stmts))


def optimize_program(p: llvm.Program):
    for d in p.topdefs:
        if isinstance(d, llvm.BuiltinFunDecl):
            continue
        optimize_function(d)
