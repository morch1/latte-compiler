from typing import List


class Parsed:
    def __init__(self, lineno):
        self.lineno = lineno


class Stmt(Parsed):
    pass


class Lhs(Parsed):
    pass


class Exp(Parsed):
    pass


class Block(Parsed):
    def __init__(self, lineno, stmt: Stmt):
        super(Block, self).__init__(lineno)
        self.stmt = stmt

    def __str__(self):
        return '{ ' + str(self.stmt) + ' }'


class StmtList(Stmt):
    def __init__(self, lineno, stmts: List[Stmt]):
        super().__init__(lineno)
        self.stmts = stmts

    def __str__(self):
        return '\n'.join(map(lambda s: str(s), self.stmts))


class LhsVar(Lhs):
    def __init__(self, lineno, var):
        super(LhsVar, self).__init__(lineno)
        self.var = var

    def __str__(self):
        return str(self.var)


class Item(Parsed):
    def __init__(self, lineno, var):
        super(Item, self).__init__(lineno)
        self.var = var

    def __str__(self):
        return str(self.var)


class ItemInit(Item):
    def __init__(self, lineno, var, exp: Exp):
        super(ItemInit, self).__init__(lineno, var)
        self.exp = exp

    def __str__(self):
        return f'{self.var} = {self.exp}'


class StmtDecl(Stmt):
    def __init__(self, lineno, t, items: List[Item]):
        super(StmtDecl, self).__init__(lineno)
        self.type = t
        self.items = items

    def __str__(self):
        return f'{self.type} ' + ', '.join(map(lambda i: str(i), self.items)) + ' ;'


class StmtAssVar(Stmt):
    def __init__(self, lineno, lhs: LhsVar, exp: Exp):
        super().__init__(lineno)
        self.var = lhs.var
        self.exp = exp

    def __str__(self):
        return f'{self.var} = {self.exp} ;'


class StmtExp(Stmt):
    def __init__(self, lineno, exp: Exp):
        super().__init__(lineno)
        self.exp = exp

    def __str__(self):
        return f'{self.exp} ;'


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
