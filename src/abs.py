from errors import TypeMismatchError


class Parsed:
    def __init__(self, lineno):
        self.lineno = lineno

class Typed(Parsed):
    def __init__(self, lineno):
        super().__init__(lineno)
        self.type = None

class List(Parsed):
    def __init__(self, lineno, items):
        super().__init__(lineno)
        self.items = items

    def __str__(self):
        return ', '.join(map(lambda s: str(s), self.items))


class Exp(Typed):
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

class ExpVar(Exp):
    def __init__(self, lineno, ident):
        super().__init__(lineno)
        self.id = ident

    def __str__(self):
        return str(self.id)

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
        self._args_obj = args
        self.args = args.items

    def __str__(self):
        return f'{self.fid}({self._args_obj})'


class Stmt(Parsed):
    def str_block(self):
        return '{\n' + ''.join('  ' + line for line in str(self).splitlines(True)) + '\n}'

class Lhs(Parsed):
    pass

class LhsVar(Lhs):
    def __init__(self, lineno, ident):
        super().__init__(lineno)
        self.id = ident

    def __str__(self):
        return str(self.id)

class Item(Parsed):
    def __init__(self, lineno, ident):
        super().__init__(lineno)
        self.id = ident

    def __str__(self):
        return str(self.id)

class ItemInit(Item):
    def __init__(self, lineno, ident, exp: Exp):
        super().__init__(lineno, ident)
        self.exp = exp

    def __str__(self):
        return f'{self.id} = {self.exp}'

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
        self._defs_obj = defs
        self.defs = defs.items

    def __str__(self):
        return f'{self.type} {self._defs_obj};'

class StmtAssVar(Stmt):
    def __init__(self, lineno, lhs: LhsVar, exp: Exp):
        super().__init__(lineno)
        self.id = lhs.id
        self.exp = exp

    def __str__(self):
        return f'{self.id} = {self.exp};'

class StmtInc(Stmt):
    def __init__(self, lineno, lhs: LhsVar):
        super().__init__(lineno)
        self.id = lhs.id

    def __str__(self):
        return f'{self.id}++;'

class StmtDec(Stmt):
    def __init__(self, lineno, lhs: LhsVar):
        super().__init__(lineno)
        self.id = lhs.id

    def __str__(self):
        return f'{self.id}--;'

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
        return f'if {self.cond} {self.stmt.str_block()}'


class StmtIfElse(Stmt):
    def __init__(self, lineno, cond: Exp, stmt1: Stmt, stmt2: Stmt):
        super().__init__(lineno)
        self.cond = cond
        self.stmt1 = stmt1
        self.stmt2 = stmt2

    def __str__(self):
        return f'if {self.cond} {self.stmt1.str_block()} else {self.stmt2.str_block()}'

class StmtWhile(Stmt):
    def __init__(self, lineno, cond: Exp, stmt: Stmt):
        super().__init__(lineno)
        self.cond = cond
        self.stmt = stmt

    def __str__(self):
        return f'while {self.cond} {self.stmt.str_block()}'

class StmtExp(Stmt):
    def __init__(self, lineno, exp: Exp):
        super().__init__(lineno)
        self.exp = exp

    def __str__(self):
        return f'{self.exp};'

class StmtList(List):
    def __str__(self):
        return '\n'.join(map(lambda s: str(s), self.items))

class StmtBlock(Stmt):
    def __init__(self, lineno, stmts: StmtList):
        super().__init__(lineno)
        self._stmts_obj = stmts
        self.stmts = stmts.items

    def __str__(self):
        return str(self._stmts_obj)


class Arg(Parsed):
    def __init__(self, lineno, t, ident):
        super().__init__(lineno)
        self.type = t
        self.id = ident

    def __str__(self):
        return f'{self.type} {self.id}'

class ArgList(List):
    pass

class TopDef(Parsed):
    def __init__(self, lineno, t, ident, args: ArgList, block: StmtBlock):
        super().__init__(lineno)
        self.type = t
        self.id = ident
        self._args_obj = args
        self.args = args.items
        self.block = block

    def __str__(self):
        return f'{self.type} {self.id} ({self._args_obj}) {self.block.str_block()}'

class TopDefList(List):
    def __str__(self):
        return '\n'.join(map(lambda s: str(s), self.items))


class Program(Parsed):
    def __init__(self, lineno, topdefs: TopDefList):
        super().__init__(lineno)
        self._topdefs_obj = topdefs
        self.topdefs = topdefs.items

    def __str__(self):
        return str(self._topdefs_obj)
