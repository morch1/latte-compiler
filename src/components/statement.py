from components import Component
from components.expression import Exp
from errors import UndefinedVariableError, TypeMismatchError, DuplicateVariableNameError
from ltypes import TYPE_INT, TYPE_VOID, TYPE_BOOL


class Lhs(Component):
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


class Stmt(Component):
    def __init__(self, lineno):
        super().__init__(lineno)
        self._str = ';'
        self.returns = False

    def to_block(self):
        if isinstance(self, StmtBlock):
            return self
        else:
            return StmtBlock(self.lineno, [self])

    def check(self, fenv, venv):
        return venv

class StmtDecl(Stmt):
    def __init__(self, lineno, t, ident):
        super().__init__(lineno)
        self._str = f'{t} {ident};'
        self.type = t
        self.id = ident
        self.returns = False

    def check(self, fenv, venv):
        venv[self.id] = self.type
        return venv

class StmtAssVar(Stmt):
    def __init__(self, lineno, lhs: LhsVar, exp: Exp):
        super().__init__(lineno)
        self._str = f'{lhs} = {exp};'
        self.lhs = lhs
        self.exp = exp
        self.returns = False

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
        self.returns = False

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
        self.returns = False

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
        self.returns = True

    def check(self, fenv, venv):
        exp_type = self.exp.check(fenv, venv)
        if venv['*'] != exp_type:
            raise TypeMismatchError(self.lineno)
        return venv

class StmtVoidReturn(Stmt):
    def __init__(self, lineno):
        super().__init__(lineno)
        self._str = f'return;'
        self.returns = True

    def check(self, fenv, venv):
        if venv['*'] != TYPE_VOID:
            raise TypeMismatchError(self.lineno)
        return venv

class StmtIf(Stmt):
    def __init__(self, lineno, cond: Exp, stmt: Stmt):
        super().__init__(lineno)
        self.cond = cond
        self.stmt = stmt.to_block()
        self.returns = stmt.returns
        self._str = f'if {cond} {self.stmt}'

    def check(self, fenv, venv):
        cond_type = self.cond.check(fenv, venv)
        if cond_type != TYPE_BOOL:
            raise TypeMismatchError(self.lineno)
        self.stmt.check(fenv, venv)
        return venv

class StmtIfElse(Stmt):
    def __init__(self, lineno, cond: Exp, stmt1: Stmt, stmt2: Stmt):
        super().__init__(lineno)
        self.cond = cond
        self.stmt1 = stmt1.to_block()
        self.stmt2 = stmt2.to_block()
        self.returns = stmt1.returns and stmt2.returns
        self._str = f'if {cond} {self.stmt1} else {self.stmt2}'

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
        self.cond = cond
        self.stmt = stmt.to_block()
        self.returns = stmt.returns
        self._str = f'while {cond} {self.stmt}'

    def check(self, fenv, venv):
        cond_type = self.cond.check(fenv, venv)
        if cond_type != TYPE_BOOL:
            raise TypeMismatchError(self.lineno)
        self.stmt.check(fenv, venv)
        return venv

class StmtExp(Stmt):
    def __init__(self, lineno, exp: Exp):
        super().__init__(lineno)
        self._str = f'{exp};'
        self.exp = exp
        self.returns = False

    def check(self, fenv, venv):
        self.exp.check(fenv, venv)
        return venv

class StmtBlock(Stmt):
    def __init__(self, lineno, stmts):
        super().__init__(lineno)
        self._str = '{\n' + '\n'.join(map(lambda s: '\n'.join('  ' + line for line in str(s).splitlines()), stmts)) + '\n}'
        self.stmts = stmts
        self.returns = any(map(lambda s: s.returns, self.stmts))

    def check(self, fenv, venv):
        localids = []
        nvenv = venv
        for stmt in self.stmts:
            if isinstance(stmt, StmtDecl):
                if stmt.id in localids:
                    raise DuplicateVariableNameError(stmt.lineno, stmt.id)
                localids.append(stmt.id)
            nvenv = stmt.check(fenv, nvenv)
        return venv
