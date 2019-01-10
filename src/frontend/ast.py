import errors
import frontend.types as types
from frontend.operators import Operator


class Node:
    def __init__(self, lineno):
        self.lineno = lineno
        self._str = '???'

    def __str__(self):
        return self._str


class Exp(Node):
    pass

class ExpUnOp(Exp):
    def __init__(self, lineno, op: Operator, exp: Exp):
        super().__init__(lineno)
        self._str = f'{op}({exp})'
        self.op = op
        self.exp = exp

class ExpBinOp(Exp):
    def __init__(self, lineno, op: Operator, exp1: Exp, exp2: Exp):
        super().__init__(lineno)
        self._str = f'({exp1} {op} {exp2})'
        self.op = op
        self.exp1 = exp1
        self.exp2 = exp2

class ExpVar(Exp):
    def __init__(self, lineno, ident):
        super().__init__(lineno)
        self._str = str(ident)
        self.id = ident

class ExpConst(Exp):
    def __init__(self, lineno, val):
        super().__init__(lineno)
        self._str = str(val)
        self.val = val

class ExpIntConst(ExpConst):
    pass

class ExpStringConst(ExpConst):
    def __init__(self, lineno, val):
        super().__init__(lineno, val)
        self._str = f'"{self.val}"'

class ExpBoolConst(ExpConst):
    pass

class ExpApp(Exp):
    def __init__(self, lineno, fid, args):
        super().__init__(lineno)
        self._str = f'{fid}(' + ', '.join(map(lambda s: str(s), args)) + ')'
        self.fid = fid
        self.args = args

class Lhs(Node):
    pass

class LhsVar(Lhs):
    def __init__(self, lineno, ident):
        super().__init__(lineno)
        self._str = str(ident)
        self.id = ident

class Stmt(Node):
    def __init__(self, lineno):
        super().__init__(lineno)
        self.returns = False

    def to_block(self):
        if isinstance(self, StmtBlock):
            return self
        else:
            return StmtBlock(self.lineno, [self])

class StmtSkip(Stmt):
    def __init__(self, lineno):
        super().__init__(lineno)
        self._str = ';'

class StmtDecl(Stmt):
    def __init__(self, lineno, t, ident):
        super().__init__(lineno)
        self._str = f'{t} {ident};'
        self.type = t
        self.id = ident
        self.returns = False

class StmtAssVar(Stmt):
    def __init__(self, lineno, lhs: LhsVar, exp: Exp):
        super().__init__(lineno)
        self._str = f'{lhs} = {exp};'
        self.lhs = lhs
        self.exp = exp
        self.returns = False

class StmtInc(Stmt):
    def __init__(self, lineno, lhs: LhsVar):
        super().__init__(lineno)
        self._str = f'{lhs}++;'
        self.lhs = lhs
        self.returns = False

class StmtDec(Stmt):
    def __init__(self, lineno, lhs: LhsVar):
        super().__init__(lineno)
        self._str = f'{lhs}--;'
        self.lhs = lhs
        self.returns = False

class StmtReturn(Stmt):
    def __init__(self, lineno, exp: Exp):
        super().__init__(lineno)
        self._str = f'return {exp};'
        self.exp = exp
        self.returns = True

class StmtVoidReturn(Stmt):
    def __init__(self, lineno):
        super().__init__(lineno)
        self._str = f'return;'
        self.returns = True

class StmtIf(Stmt):
    def __init__(self, lineno, cond: Exp, stmt: Stmt):
        super().__init__(lineno)
        self.cond = cond
        self.stmt = stmt.to_block()
        self.returns = stmt.returns
        self._str = f'if {cond} {self.stmt}'

class StmtIfElse(Stmt):
    def __init__(self, lineno, cond: Exp, stmt1: Stmt, stmt2: Stmt):
        super().__init__(lineno)
        self.cond = cond
        self.stmt1 = stmt1.to_block()
        self.stmt2 = stmt2.to_block()
        self.returns = stmt1.returns and stmt2.returns
        self._str = f'if {cond} {self.stmt1} else {self.stmt2}'

class StmtWhile(Stmt):
    def __init__(self, lineno, cond: Exp, stmt: Stmt):
        super().__init__(lineno)
        self.cond = cond
        self.stmt = stmt.to_block()
        self.returns = stmt.returns
        self._str = f'while {cond} {self.stmt}'

class StmtExp(Stmt):
    def __init__(self, lineno, exp: Exp):
        super().__init__(lineno)
        self._str = f'{exp};'
        self.exp = exp
        self.returns = False

class StmtBlock(Stmt):
    def __init__(self, lineno, stmts):
        super().__init__(lineno)
        self._str = '{\n' + '\n'.join(map(lambda s: '\n'.join('  ' + line for line in str(s).splitlines()), stmts)) + '\n}'
        self.stmts = stmts
        self.returns = any(map(lambda s: s.returns, self.stmts))


class Arg(Node):
    def __init__(self, lineno, t, ident):
        super().__init__(lineno)
        self._str = f'{t} {ident}'
        self.type = t
        self.id = ident

class FunDef(Node):
    def __init__(self, lineno, t, ident, args):
        super().__init__(lineno)
        self._str = f'{t} {ident} (' + ', '.join(map(lambda s: str(s), args)) + ')'
        self.type = t
        self.id = ident
        self.args = args
        self.block = StmtBlock(self.lineno, [])

class TopDef(FunDef):
    def __init__(self, lineno, t, ident, args, block: StmtBlock):
        super().__init__(lineno, t, ident, args)
        self._str += f' {block}'
        self.block = block
        if self.type != types.VOID and not self.block.returns:
            raise errors.MissingReturnError(self.lineno)

class BuiltinFunDef(FunDef):
    def __init__(self, t, ident, args_types):
        super().__init__(0, t, ident, list(map(lambda a: Arg(0, a[0], a[1]), args_types)))

class Program(Node):
    def __init__(self, lineno, topdefs):
        super().__init__(lineno)
        self.topdefs = [
            BuiltinFunDef(types.VOID, 'printInt', [(types.INT, 'n')]),
            BuiltinFunDef(types.VOID, 'printString', [(types.STRING, 'str')]),
            BuiltinFunDef(types.VOID, 'error', []),
            BuiltinFunDef(types.INT, 'readInt', []),
            BuiltinFunDef(types.STRING, 'readString', [])
        ] + topdefs
        self._str = '\n'.join(map(lambda s: str(s), self.topdefs))
