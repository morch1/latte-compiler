class Parsed:
    def __init__(self, lineno):
        self.lineno = lineno

class List(Parsed):
    def __init__(self, lineno, items):
        super().__init__(lineno)
        self.items = items

    def __str__(self):
        return ', '.join(map(lambda s: str(s), self.items))


class Exp(Parsed):
    pass

class ExpUnOp(Exp):
    def __init__(self, lineno, op, exp: Exp):
        super().__init__(lineno)
        self.op = op
        self.exp = exp

    def __str__(self):
        return f'{self.op}({self.exp})'

class ExpBinOp(Exp):
    def __init__(self, lineno, op, exp1: Exp, exp2: Exp):
        super().__init__(lineno)
        self.op = op
        self.exp1 = exp1
        self.exp2 = exp2

    def __str__(self):
        return f'({self.exp1} {self.op} {self.exp2})'

    def commutative(self):
        return self.op in ['+', '*']

class ExpVar(Exp):
    def __init__(self, lineno, var):
        super().__init__(lineno)
        self.var = var

    def __str__(self):
        return str(self.var)

class ExpConst(Exp):
    def __init__(self, lineno, val):
        super().__init__(lineno)
        self.val = val

    def __str__(self):
        return str(self.val)

class ExpInt(ExpConst):
    pass

class ExpString(ExpConst):
    def __str__(self):
        return f'"{self.val}"'

class ExpBool(ExpConst):
    pass

class ExpList(List):
    pass

class ExpApp(Exp):
    def __init__(self, lineno, fid, args: ExpList):
        super().__init__(lineno)
        self.fid = fid
        self.args = args

    def __str__(self):
        return f'{self.fid}({self.args})'


class Stmt(Parsed):
    pass

class Lhs(Parsed):
    pass

class LhsVar(Lhs):
    def __init__(self, lineno, var):
        super().__init__(lineno)
        self.var = var

    def __str__(self):
        return str(self.var)

class Item(Parsed):
    def __init__(self, lineno, var):
        super().__init__(lineno)
        self.var = var

    def __str__(self):
        return str(self.var)

class ItemInit(Item):
    def __init__(self, lineno, var, exp: Exp):
        super().__init__(lineno, var)
        self.exp = exp

    def __str__(self):
        return f'{self.var} = {self.exp}'

class ItemList(List):
    pass

class StmtEmpty(Stmt):
    def __init__(self, lineno):
        super().__init__(lineno)

    def __str__(self):
        return ';'

class StmtDecl(Stmt):
    def __init__(self, lineno, t, defs: ItemList):
        super().__init__(lineno)
        self.type = t
        self.defs = defs

    def __str__(self):
        return f'{self.type} {self.defs};'

class StmtAssVar(Stmt):
    def __init__(self, lineno, lhs: LhsVar, exp: Exp):
        super().__init__(lineno)
        self.var = lhs.var
        self.exp = exp

    def __str__(self):
        return f'{self.var} = {self.exp};'

class StmtInc(Stmt):
    def __init__(self, lineno, lhs: LhsVar):
        super().__init__(lineno)
        self.var = lhs.var

    def __str__(self):
        return f'{self.var}++;'

class StmtDec(Stmt):
    def __init__(self, lineno, lhs: LhsVar):
        super().__init__(lineno)
        self.var = lhs.var

    def __str__(self):
        return f'{self.var}--;'

class StmtReturn(Stmt):
    def __init__(self, lineno, exp: Exp):
        super().__init__(lineno)
        self.exp = exp

    def __str__(self):
        return f'return {self.exp};'

class StmtVoidReturn(Stmt):
    def __str__(self):
        return f'return;'

class StmtIf(Stmt):
    def __init__(self, lineno, cond: Exp, stmt: Stmt):
        super().__init__(lineno)
        self.cond = cond
        self.stmt = stmt

    def __str__(self):
        return f'if {self.cond} [{self.stmt}]'


class StmtIfElse(Stmt):
    def __init__(self, lineno, cond: Exp, stmt1: Stmt, stmt2: Stmt):
        super().__init__(lineno)
        self.cond = cond
        self.stmt1 = stmt1
        self.stmt2 = stmt2

    def __str__(self):
        return f'if {self.cond} {self.stmt1} else {self.stmt2}'

class StmtWhile(Stmt):
    def __init__(self, lineno, cond: Exp, stmt: Stmt):
        super().__init__(lineno)
        self.cond = cond
        self.stmt = stmt

    def __str__(self):
        return f'while {self.cond} {self.stmt}'

class StmtExp(Stmt):
    def __init__(self, lineno, exp: Exp):
        super().__init__(lineno)
        self.exp = exp

    def __str__(self):
        return f'{self.exp};'

class Block(Parsed):
    def __init__(self, lineno, stmt: Stmt):
        super().__init__(lineno)
        self.stmt = stmt

    def __str__(self):
        return '{ ' + str(self.stmt) + ' }'

class StmtList(List):
    def __str__(self):
        return '\n'.join(map(lambda s: str(s), self.items))
