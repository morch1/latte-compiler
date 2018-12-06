from components import Component
from errors import TypeMismatchError, UndefinedVariableError, UndefinedFunctionError, InvalidCallError
from ltypes import TYPE_INT, TYPE_STRING, TYPE_BOOL
from operators import Operator


class Exp(Component):
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

class ExpApp(Exp):
    def __init__(self, lineno, fid, args):
        super().__init__(lineno)
        self._str = f'{fid}(' + ', '.join(map(lambda s: str(s), args)) + ')'
        self.fid = fid
        self.args = args

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
