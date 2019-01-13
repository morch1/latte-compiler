import re
from dataclasses import dataclass


TYPE_INT = 'i64'
TYPE_BOOL = 'i1'
TYPE_STRING = 'i8*'
TYPE_CHAR = 'i8'
TYPE_VOID = 'void'

OP_ADD = 'add'
OP_SUB = 'sub'
OP_MUL = 'mul'
OP_DIV = 'sdiv'
OP_MOD = 'srem'
OP_EQ = 'icmp eq'
OP_NE = 'icmp ne'
OP_LT = 'icmp slt'
OP_LE = 'icmp sle'
OP_GT = 'icmp sgt'
OP_GE = 'icmp sge'


@dataclass
class Block:
    label: str

    def __post_init__(self):
        self.stmts = []
        self.preds = []
        self.succs = []
        self.succlabels = set()

    def __str__(self):
        return f'  {self.label}:  ; preds: ' + ', '.join(p.label for p in self.preds) + '\n' \
               + '\n'.join(f'    {s}' for s in self.stmts)

@dataclass
class StmtBinOp:
    var: str
    op: str
    type: str
    arg1: object
    arg2: object

    def __str__(self):
        return f'{self.var} = {self.op} {self.type} {self.arg1}, {self.arg2}'

@dataclass
class StmtCall:
    var: str
    type: str
    fid: str
    args: list

    def __str__(self):
        return (self.var and f'{self.var} = ' or '') + f'call {self.type} @{self.fid}(' + ', '.join(f'{a[0]} {a[1]}' for a in self.args) + ')'

@dataclass
class StmtAlloc:
    addr: str
    type: str

    def __str__(self):
        return f'{self.addr} = alloca {self.type}'

@dataclass
class StmtLoad:
    var: str
    type: str
    addr: str

    def __str__(self):
        return f'{self.var} = load {self.type}, {self.type}* {self.addr}'

@dataclass
class StmtStore:
    type: str
    val: object
    addr: str

    def __str__(self):
        return f'store {self.type} {self.val}, {self.type}* {self.addr}'

@dataclass
class StrLit:
    string: str

    def __len__(self):
        return len(self.string) - len(re.findall('\\\\n|\\\\"', self.string)) + 1

    def __str__(self):
        return 'c"' + self.string.replace('\\n', '\\0A').replace('\\"', '\\22') + '\\00"'

    @property
    def type(self):
        return f'[{len(self)} x {TYPE_CHAR}]'

@dataclass
class StmtGetGlobal:
    var: str
    type: str
    addr: str

    def __str__(self):
        return f'{self.var} = getelementptr {self.type}, {self.type}* {self.addr}, {TYPE_INT} 0, {TYPE_INT} 0'

@dataclass
class StmtReturn:
    type: str
    val: object

    def __str__(self):
        return f'ret {self.type} {self.val}'

@dataclass
class StmtVoidReturn:
    def __str__(self):
        return f'ret {TYPE_VOID}'

@dataclass
class StmtJump:
    label: str

    def __str__(self):
        return f'br label %{self.label}'

@dataclass
class StmtCondJump:
    cond: object
    tlabel: str
    flabel: str

    def __str__(self):
        return f'br i1 {self.cond}, label %{self.tlabel}, label %{self.flabel}'

@dataclass
class StmtPhi:
    var: str
    type: str
    vals: list

    def __str__(self):
        return f'{self.var} = phi {self.type} ' + ', '.join(f'[{v[0]}, %{v[1]}]' for v in self.vals)

@dataclass
class GlobalDef:
    addr: str
    type: str
    val: object

    def __str__(self):
        return f'{self.addr} = private constant {self.type} {self.val}'

@dataclass
class FunDecl:
    type: str
    id: str
    args: list

@dataclass
class BuiltinFunDecl(FunDecl):
    def __str__(self):
        return f'declare {self.type} @{self.id}(' + ', '.join(self.args) + ')'

@dataclass
class TopDef(FunDecl):
    blocks: list

    def __str__(self):
        return f'define {self.type} @{self.id}(' + ', '.join(f'{a[0]} {a[1]}' for a in self.args) + ') {\n'\
               + '\n'.join(str(s) for s in self.blocks)\
               + '\n}'

@dataclass
class Program:
    topdefs: list
    globals: list

    def __str__(self):
        return '\n'.join(str(g) for g in self.globals) + '\n'\
            + '\n'.join(str(d) for d in self.topdefs)
