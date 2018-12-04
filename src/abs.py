from errors import TypeMismatchError, DuplicateFunctionNameError, InvalidMainFunctionError, MissingMainFunctionError, \
    DuplicateVariableNameError, UndefinedVariableError, UndefinedFunctionError, InvalidCallError
from ltypes import TYPE_INT, TYPE_VOID, TYPE_STRING, TYPE_BOOL
from operators import Operator


def _copy_env(fenv, venv):
    return dict(fenv), dict(venv)


class Parsed:
    def __init__(self, lineno):
        self.lineno = lineno
        self._str = '???'

    def __str__(self):
        return self._str

    def __repr__(self):
        return self._str


class List(Parsed):
    def __init__(self, lineno, items):
        super().__init__(lineno)
        self._str = ', '.join(map(lambda s: str(s), items))
        self.items = items


class Exp(Parsed):
    def check(self, fenv, venv):
        return

class ExpUnOp(Exp):
    def __init__(self, lineno, op: Operator, exp: Exp):
        super().__init__(lineno)
        self._str = f'{op}({exp})'
        self.op = op
        self.exp = exp

    def check(self, fenv, venv):
        exp_type = self.exp.check(fenv, venv)
        try:
            return self.op.check(exp_type)
        except TypeMismatchError as ex:
            ex.line = self.lineno
            raise ex

class ExpBinOp(Exp):
    def __init__(self, lineno, op: Operator, exp1: Exp, exp2: Exp):
        super().__init__(lineno)
        self._str = f'({exp1} {op} {exp2})'
        self.op = op
        self.exp1 = exp1
        self.exp2 = exp2

    def check(self, fenv, venv):
        exp1_type = self.exp1.check(fenv, venv)
        exp2_type = self.exp2.check(fenv, venv)
        try:
            return self.op.check(exp1_type, exp2_type)
        except TypeMismatchError as ex:
            ex.line = self.lineno
            raise ex

class ExpVar(Exp):
    def __init__(self, lineno, ident):
        super().__init__(lineno)
        self._str = str(ident)
        self.id = ident

    def check(self, fenv, venv):
        try:
            return venv[self.id]
        except KeyError:
            raise UndefinedVariableError(self.lineno, self.id)

class ExpConst(Exp):
    def __init__(self, lineno, val):
        super().__init__(lineno)
        self._str = str(val)
        self.val = val

class ExpIntConst(ExpConst):
    def check(self, fenv, venv):
        return TYPE_INT

class ExpStringConst(ExpConst):
    def __init__(self, lineno, val):
        super().__init__(lineno, val)
        self._str = f'"{self.val}"'

    def check(self, fenv, venv):
        return TYPE_STRING

class ExpBoolConst(ExpConst):
    def check(self, fenv, venv):
        return TYPE_BOOL

class Exps(List):
    pass

class ExpApp(Exp):
    def __init__(self, lineno, fid, args: Exps):
        super().__init__(lineno)
        self._str = f'{fid}({args})'
        self.fid = fid
        self.args = args.items

    def check(self, fenv, venv):
        try:
            fun = fenv[self.fid]
        except KeyError:
            raise UndefinedFunctionError(self.lineno, self.fid)
        if len(self.args) != len(fun.args):
            raise InvalidCallError(self.lineno, self.fid)
        for ca, fa in zip(self.args, fun.args):
            exp_type = ca.check(fenv, venv)
            if exp_type != fa.type:
                raise TypeMismatchError(self.lineno)
        return fun.type


class Lhs(Parsed):
    def check(self, venv):
        pass

class LhsVar(Lhs):
    def __init__(self, lineno, ident):
        super().__init__(lineno)
        self._str = str(ident)
        self.id = ident

    def check(self, venv):
        try:
            return venv[self.id]
        except KeyError:
            raise UndefinedVariableError(self.lineno, self.id)


class VarDecl(Parsed):
    def __init__(self, lineno, ident):
        super().__init__(lineno)
        self._str = str(ident)
        self.id = ident

class VarDeclInit(VarDecl):
    def __init__(self, lineno, ident, exp: Exp):
        super().__init__(lineno, ident)
        self._str = f'{ident} = {exp}'
        self.exp = exp

class VarDecls(List):
    pass

class Stmt(Parsed):
    def __init__(self, lineno):
        super().__init__(lineno)
        self._str = ';'

    def str_block(self):
        return '{\n' + ''.join('  ' + line for line in str(self).splitlines(True)) + '\n}'

    def check(self, fenv, venv):
        return venv

class StmtDecl(Stmt):
    def __init__(self, lineno, t, defs: VarDecls):
        super().__init__(lineno)
        self._str = f'{t} {defs};'
        self.type = t
        self.defs = defs.items

    def check(self, fenv, venv):
        venv = dict(venv)
        for item in self.defs:
            if isinstance(item, VarDeclInit):
                exp_type = item.exp.check(fenv, venv)
                if exp_type != self.type:
                    raise TypeMismatchError(item.lineno)
            venv[item.id] = self.type
        return venv

class StmtAssVar(Stmt):
    def __init__(self, lineno, lhs: LhsVar, exp: Exp):
        super().__init__(lineno)
        self._str = f'{lhs} = {exp};'
        self.lhs = lhs
        self.exp = exp

    def check(self, fenv, venv):
        exp_type = self.exp.check(fenv, venv)
        lhs_type = self.lhs.check(venv)
        if lhs_type != exp_type:
            raise TypeMismatchError(self.lineno)
        return venv

class StmtInc(Stmt):
    def __init__(self, lineno, lhs: LhsVar):
        super().__init__(lineno)
        self._str = f'{lhs}++;'
        self.lhs = lhs

    def check(self, fenv, venv):
        lhs_type = self.lhs.check(venv)
        if lhs_type != TYPE_INT:
            raise TypeMismatchError(self.lineno)
        return venv

class StmtDec(Stmt):
    def __init__(self, lineno, lhs: LhsVar):
        super().__init__(lineno)
        self._str = f'{lhs}--;'
        self.lhs = lhs

    def check(self, fenv, venv):
        lhs_type = self.lhs.check(venv)
        if lhs_type != TYPE_INT:
            raise TypeMismatchError(self.lineno)
        return venv

class StmtReturn(Stmt):
    def __init__(self, lineno, exp: Exp):
        super().__init__(lineno)
        self._str = f'return {exp};'
        self.exp = exp

    def check(self, fenv, venv):
        exp_type = self.exp.check(fenv, venv)
        if venv['*'] != exp_type:
            raise TypeMismatchError(self.lineno)
        return venv

class StmtVoidReturn(Stmt):
    def __init__(self, lineno):
        super().__init__(lineno)
        self._str = f'return;'

    def check(self, fenv, venv):
        if venv['*'] != TYPE_VOID:
            raise TypeMismatchError(self.lineno)
        return venv

class StmtIf(Stmt):
    def __init__(self, lineno, cond: Exp, stmt: Stmt):
        super().__init__(lineno)
        self._str = f'if {cond} {stmt.str_block()}'
        self.cond = cond
        self.stmt = stmt

    def check(self, fenv, venv):
        cond_type = self.cond.check(fenv, venv)
        if cond_type != TYPE_BOOL:
            raise TypeMismatchError(self.lineno)
        self.stmt.check(fenv, venv)
        return venv

class StmtIfElse(Stmt):
    def __init__(self, lineno, cond: Exp, stmt1: Stmt, stmt2: Stmt):
        super().__init__(lineno)
        self._str = f'if {cond} {stmt1.str_block()} else {stmt2.str_block()}'
        self.cond = cond
        self.stmt1 = stmt1
        self.stmt2 = stmt2

    def check(self, fenv, venv):
        cond_type = self.cond.check(fenv, venv)
        if cond_type != TYPE_BOOL:
            raise TypeMismatchError(self.lineno)
        self.stmt1.check(fenv, venv)
        self.stmt2.check(fenv, venv)
        return venv

class StmtWhile(Stmt):
    def __init__(self, lineno, cond: Exp, stmt: Stmt):
        super().__init__(lineno)
        self._str = f'while {cond} {stmt.str_block()}'
        self.cond = cond
        self.stmt = stmt

    def check(self, fenv, venv):
        cond_type = self.cond.check(fenv, venv)
        if cond_type != TYPE_BOOL:
            raise TypeMismatchError(self.lineno)
        self.stmt.check(fenv, venv)
        return venv

class StmtExp(Stmt):
    def __init__(self, lineno, exp: Exp):
        super().__init__(lineno)
        self._str = str(exp)
        self.exp = exp

    def check(self, fenv, venv):
        self.exp.check(fenv, venv)
        return venv

class Stmts(List):
    def __init__(self, lineno, items):
        super().__init__(lineno, items)
        self._str = '\n'.join(map(lambda s: str(s), items))

class StmtBlock(Stmt):
    def __init__(self, lineno, stmts: Stmts):
        super().__init__(lineno)
        self._str = str(stmts)
        self.stmts = stmts.items

    def check(self, fenv, venv):
        localids = []
        nvenv = venv
        for stmt in self.stmts:
            if isinstance(stmt, StmtDecl):
                for var in stmt.defs:
                    if var.id in localids:
                        raise DuplicateVariableNameError(var.lineno, var.id)
                    localids.append(var.id)
            nvenv = stmt.check(fenv, nvenv)
        return venv


class Arg(Parsed):
    def __init__(self, lineno, t, ident):
        super().__init__(lineno)
        self._str = f'{t} {ident}'
        self.type = t
        self.id = ident

class Args(List):
    pass

class FunDef(Parsed):
    def __init__(self, lineno, t, ident, args: Args):
        super().__init__(lineno)
        self._str = f'{t} {ident} ({args})'
        self.type = t
        self.id = ident
        self.args = args.items
        self.block = StmtBlock(self.lineno, Stmts(self.lineno, []))

    def check(self, fenv):
        if self.id == 'main' and (self.type != TYPE_INT or len(self.args) > 0):
            raise InvalidMainFunctionError(self.lineno)
        venv = {}
        for arg in self.args:
            if arg.id in venv:
                raise DuplicateVariableNameError(arg.lineno, arg.id)
            venv[arg.id] = arg.type
        venv['*'] = self.type
        self.block.check(fenv, venv)
        # todo: check if value is returned when necessary

class TopDef(FunDef):
    def __init__(self, lineno, t, ident, args: Args, block: StmtBlock):
        super().__init__(lineno, t, ident, args)
        self._str += f' {block.str_block()}'
        self.block = block

class BuiltinFunDef(FunDef):
    def __init__(self, t, ident, args_types):
        super().__init__(0, t, ident, Args(0, list(map(lambda a: Arg(0, a[0], a[1]), args_types))))

class TopDefs(List):
    def __init__(self, lineno, items):
        super().__init__(lineno, items)
        self._str = '\n'.join(map(lambda s: str(s), self.items))

class Program(Parsed):
    def __init__(self, lineno, topdefs: TopDefs):
        super().__init__(lineno)
        topdefs.items = [
            BuiltinFunDef(TYPE_VOID, 'printInt', [(TYPE_INT, 'n')]),
            BuiltinFunDef(TYPE_VOID, 'printString', [(TYPE_STRING, 'str')]),
            BuiltinFunDef(TYPE_VOID, 'error', []),
            BuiltinFunDef(TYPE_INT, 'readInt', []),
            BuiltinFunDef(TYPE_STRING, 'readString', [])
        ] + topdefs.items
        self._str = str(topdefs)
        self.topdefs = topdefs.items

    def check(self):
        fenv = {}
        for topdef in self.topdefs:
            if topdef.id in fenv:
                raise DuplicateFunctionNameError(topdef.lineno, topdef.id)
            fenv[topdef.id] = topdef
        if 'main' not in fenv:
            raise MissingMainFunctionError(self.lineno)
        for topdef in self.topdefs:
            topdef.check(fenv)
