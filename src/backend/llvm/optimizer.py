import backend.llvm as llvm
from dataclasses import dataclass
from itertools import count

def ssaify_function(f: llvm.TopDef):
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

    for b in f.blocks:  # insert phis
        if len(b.preds) == 0:
            continue
        lvs = get_live_vars(b)

        # add phis for all variables live at the start of the block
        for lv, lvtype in lvs.items():
            b.stmts.insert(0, llvm.StmtPhi(lv, lvtype, [(lv, p.label) for p in b.preds]))

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
            elif isinstance(s, llvm.StmtPhi):
                pm[s.var] = fresh_loc(s.var)
                nstmts.append(llvm.StmtPhi(pm[s.var], s.type, s.vals))
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
            extra_phis[b].insert(0, llvm.StmtPhi(nv, t, [(get_phi_val(p, t, v), p.label) for p in b.preds]))
            return nv

    for b in f.blocks:  # fix phis
        nstmts = []
        for s in b.stmts:
            if isinstance(s, llvm.StmtPhi):
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

    var_map = {}
    for b in f.blocks:  # make map of assignments
        for s in b.stmts:
            if isinstance(s, StmtAss):
                var_map[s.dst] = s.src

    def get_val(v):
        if v not in var_map:
            return v
        return get_val(var_map[v])

    for b in f.blocks:  # eliminate assignments
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
        b.stmts = list(filter(lambda s: not isinstance(s, StmtAss), b.stmts))


def optimize_program(p: llvm.Program):
    for d in p.topdefs:
        if isinstance(d, llvm.BuiltinFunDecl):
            continue
        ssaify_function(d)
