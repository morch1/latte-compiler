import errors
from dataclasses import dataclass

@dataclass(frozen=True)
class Type:
    name: str
    _type_map = {}

    def __post_init__(self):
        self.__class__._type_map[self.name] = self

    def __str__(self):
        return self.name

    @classmethod
    def get_by_name(cls, name):
        try:
            return cls._type_map[name]
        except KeyError:
            raise errors.InvalidTypeError(None, name)


TYPE_INT = Type('int')
TYPE_BOOL = Type('boolean')
TYPE_STRING = Type('string')
TYPE_VOID = Type('void')


@dataclass
class Node:
    lineno: int

@dataclass
class Exp(Node):
    pass

@dataclass
class ExpUnOp(Exp):
    op: str
    exp: Exp

    def __str__(self):
        return f'{self.op}({self.exp})'

@dataclass
class ExpBinOp(Exp):
    op: str
    exp1: Exp
    exp2: Exp

    def __str__(self):
        return f'({self.exp1} {self.op} {self.exp2})'

@dataclass
class ExpVar(Exp):
    id: str

    def __str__(self):
        return self.id

@dataclass
class ExpConst(Exp):
    val: object

    def __str__(self):
        return str(self.val)

@dataclass
class ExpIntConst(ExpConst):
    val: int
    type = TYPE_INT

@dataclass
class ExpStringConst(ExpConst):
    val: str
    type = TYPE_STRING

    def __str__(self):
        return f'"{self.val}"'

@dataclass
class ExpBoolConst(ExpConst):
    val: bool
    type = TYPE_BOOL

@dataclass
class ExpFun(Exp):
    fid: str
    args: list

    def __str__(self):
        return f'{self.fid}(' + ', '.join(str(a) for a in self.args) + ')'


@dataclass
class Lhs(Node):
    pass

@dataclass
class LhsVar(Lhs):
    id: str

    def __str__(self):
        return str(self.id)


@dataclass
class Stmt(Node):
    @property
    def returns(self):
        return False 
    
    @property
    def as_block(self):
        if isinstance(self, StmtBlock):
            return self
        else:
            return StmtBlock(self.lineno, [self])

@dataclass
class StmtSkip(Stmt):
    def __str__(self):
        return ';'

@dataclass
class StmtDecl(Stmt):
    type: Type
    id: str

    def __str__(self):
        return f'{self.type} {self.id};'

@dataclass
class StmtDeclDefault(StmtDecl):
    pass

@dataclass
class StmtAss(Stmt):
    lhs: Lhs
    exp: Exp

    def __str__(self):
        return f'{self.lhs} = {self.exp};'

@dataclass
class StmtReturn(Stmt):
    exp: Exp

    @property
    def returns(self):
        return True

    def __str__(self):
        return f'return {self.exp};'

@dataclass
class StmtVoidReturn(Stmt):
    @property
    def returns(self):
        return True

    def __str__(self):
        return 'return;'

@dataclass
class StmtIf(Stmt):
    cond: Exp
    stmt: Stmt

    def __post_init__(self):
        self.stmt = self.stmt.as_block

    def __str__(self):
        return f'if {self.cond} {self.stmt}'

@dataclass
class StmtIfElse(StmtIf):
    stmt2: Stmt

    def __post_init__(self):
        super().__post_init__()
        self.stmt2 = self.stmt2.as_block

    @property
    def returns(self):
        return self.stmt.returns and self.stmt2.returns

    def __str__(self):
        return f'if {self.cond} {self.stmt} else {self.stmt2}'

@dataclass
class StmtWhile(StmtIf):
    def __str__(self):
        return f'while {self.cond} {self.stmt}'

@dataclass
class StmtExp(Stmt):
    exp: Exp

    def __str__(self):
        return f'{self.exp};'

@dataclass
class StmtBlock(Stmt):
    stmts: list

    @property
    def returns(self):
        return any(s.returns for s in self.stmts)

    def __str__(self):
        return '{\n'\
               + '\n'.join('\n'.join(f'  {line}' for line in str(s).splitlines()) for s in self.stmts)\
               + '\n}'


@dataclass
class FunArg(Node):
    type: Type
    id: str

    def __str__(self):
        return f'{self.type} {self.id}'

@dataclass
class FunDecl(Node):
    type: Type
    id: str
    args: list

@dataclass
class TopDef(FunDecl):
    block: StmtBlock

    def __str__(self):
        return f'{self.type} {self.id} (' + ', '.join(str(a) for a in self.args) + f') {self.block}'

@dataclass
class BuiltinFunDecl(FunDecl):
    def __post_init__(self):
        # this will simplify type checking
        self.args = [FunArg(0, t, '') for t in self.args]

    def __str__(self):
        return f'// builtin: {self.type} {self.id} (' + ', '.join(str(a.type) for a in self.args) + ')'

@dataclass
class Program(Node):
    topdefs: list

    def __post_init__(self):
        self.topdefs = [
            BuiltinFunDecl(0, TYPE_VOID, 'error', []),
            BuiltinFunDecl(0, TYPE_VOID, 'printInt', [TYPE_INT]),
            BuiltinFunDecl(0, TYPE_VOID, 'printString', [TYPE_STRING]),
            BuiltinFunDecl(0, TYPE_INT, 'readInt', []),
            BuiltinFunDecl(0, TYPE_STRING, 'readString', []),
            # internal functions:
            BuiltinFunDecl(0, TYPE_BOOL, '$compareStrings', [TYPE_INT, TYPE_STRING, TYPE_STRING]),
            BuiltinFunDecl(0, TYPE_STRING, '$addStrings', [TYPE_STRING, TYPE_STRING]),
        ] + self.topdefs

    def __str__(self):
        return '\n'.join(str(d) for d in self.topdefs)
