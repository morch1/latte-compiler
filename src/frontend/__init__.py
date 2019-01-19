import errors
from frontend.types import TYPE_VOID, TYPE_INT, TYPE_BOOL, TYPE_STRING, Type
from dataclasses import dataclass

COMP_OPS = ['<', '<=', '>', '>=', '==', '!=']


@dataclass
class Node:
    lineno: int


# -------- expressions --------

@dataclass
class Exp(Node):
    type = None

    @property
    def called_functions(self):
        """returns a set of ids of functions called from this expression"""
        return set()

    def check(self, fenv, venv):
        """
        - checks corectness of expression
        - returns simlpified expression
        """
        return self


@dataclass
class ExpUnOp(Exp):
    op: str
    exp: Exp

    @property
    def called_functions(self):
        return self.exp.called_functions

    def __str__(self):
        return f'{self.op}({self.exp})'

    def check(self, fenv, venv):
        self.exp = self.exp.check(fenv, venv)
        if self.op == '-' and self.exp.type == TYPE_INT:
            if isinstance(self.exp, ExpIntConst):
                return ExpIntConst(self.lineno, -self.exp.val)
            self.type = TYPE_INT
        elif self.op == '!' and self.exp.type == TYPE_BOOL:
            if isinstance(self.exp, ExpBoolConst):
                return ExpBoolConst(self.lineno, not self.exp.val)
            self.type = TYPE_BOOL
        else:
            raise errors.TypeMismatchError(self.lineno)
        return self


@dataclass
class ExpBinOp(Exp):
    op: str
    exp1: Exp
    exp2: Exp

    @property
    def called_functions(self):
        fs = set()
        fs.update(self.exp1.called_functions)
        fs.update(self.exp2.called_functions)
        if self.exp1.type == TYPE_STRING and self.exp2.type == TYPE_STRING:
            if self.op == '+':
                fs.add('$addStrings')
            elif self.op in COMP_OPS:
                fs.add('$compareStrings')
        return fs

    def __str__(self):
        return f'({self.exp1} {self.op} {self.exp2})'

    def check(self, fenv, venv):
        self.exp1 = self.exp1.check(fenv, venv)
        self.exp2 = self.exp2.check(fenv, venv)
        exp_types = (self.exp1.type, self.exp2.type)
        if TYPE_VOID in exp_types:
            raise errors.TypeMismatchError(self.lineno)
        if self.op in ['+', '-', '*', '/', '%'] and exp_types == (TYPE_INT, TYPE_INT):
            if isinstance(self.exp1, ExpConst) and isinstance(self.exp2, ExpConst):
                if self.op == '/':
                    return ExpIntConst(self.lineno, self.exp1.val // self.exp2.val)
                elif self.op == '%':
                    return ExpIntConst(self.lineno, (self.exp1.val % self.exp2.val) - (self.exp2.val if self.exp1.val < 0 else 0))
                else:
                    return ExpIntConst(self.lineno, eval(f'{self.exp1.val}{self.op}{self.exp2.val}'))
            self.type = TYPE_INT
        elif self.op == '+' and exp_types == (TYPE_STRING, TYPE_STRING):
            if isinstance(self.exp1, ExpConst) and isinstance(self.exp2, ExpConst):
                return ExpStringConst(self.lineno, self.exp1.val + self.exp2.val)
            self.type = TYPE_STRING
        elif (self.op in ['||', '&&'] and exp_types == (TYPE_BOOL, TYPE_BOOL)) or \
                (self.op in COMP_OPS and self.exp1.type == self.exp2.type):
            if isinstance(self.exp1, ExpConst) and self.op == '||' and self.exp1.val:
                return ExpBoolConst(self.lineno, True)
            elif isinstance(self.exp1, ExpConst) and self.op == '&&' and not self.exp1.val:
                return ExpBoolConst(self.lineno, False)
            elif isinstance(self.exp1, ExpConst) and isinstance(self.exp2, ExpConst):
                if self.op == '||':
                    return ExpBoolConst(self.lineno, self.exp1.val or self.exp2.val)
                elif self.op == '&&':
                    return ExpBoolConst(self.lineno, self.exp1.val and self.exp2.val)
                else:
                    return ExpBoolConst(self.lineno, eval(f'{self.exp1.val}{self.op}{self.exp2.val}'))
            self.type = TYPE_BOOL
        else:
            raise errors.TypeMismatchError(self.lineno)
        return self


@dataclass
class ExpVar(Exp):
    id: str

    def __str__(self):
        return self.id

    def check(self, fenv, venv):
        try:
            self.type = venv[self.id]
        except KeyError:
            raise errors.UndefinedVariableError(self.lineno, self.id)
        return self


@dataclass
class ExpConst(Exp):
    val: object

    def __str__(self):
        return str(self.val)


@dataclass
class ExpIntConst(ExpConst):
    type = TYPE_INT


@dataclass
class ExpStringConst(ExpConst):
    type = TYPE_STRING

    def __str__(self):
        return f'"{self.val}"'


@dataclass
class ExpBoolConst(ExpConst):
    type = TYPE_BOOL


@dataclass
class ExpFun(Exp):
    fid: str
    args: list

    @property
    def called_functions(self):
        fs = set()
        for arg in self.args:
            fs.update(arg.called_functions)
        fs.add(self.fid)
        return fs

    def __str__(self):
        return f'{self.fid}(' + ', '.join(str(a) for a in self.args) + ')'

    def check(self, fenv, venv):
        try:
            fun = fenv[self.fid]
        except KeyError:
            raise errors.UndefinedFunctionError(self.lineno, self.fid)
        if len(self.args) != len(fun.args):
            raise errors.InvalidCallError(self.lineno, self.fid)
        args = []
        for ca, fa in zip(self.args, fun.args):
            nca = ca.check(fenv, venv)
            if nca.type != fa.type:
                raise errors.TypeMismatchError(self.lineno)
            args.append(nca)
        self.args = args
        self.type = fun.type
        return self


@dataclass
class ExpArray(Exp):
    id: str
    idx: Exp

    @property
    def called_functions(self):
        return self.idx.called_functions

    def __str__(self):
        return f'{self.id}[{self.idx}]'

    def check(self, fenv, venv):
        self.idx = self.idx.check(fenv, venv)
        try:
            self.type = venv[self.id].element_type
        except KeyError:
            raise errors.UndefinedVariableError(self.lineno, self.id)
        return self


@dataclass
class ExpAttr(Exp):
    id: str
    attr: str

    def __str__(self):
        return f'{self.id}.{self.attr}'

    def check(self, fenv, venv):
        try:
            vartype = venv[self.id]
        except KeyError:
            raise errors.UndefinedVariableError(self.lineno, self.id)
        if vartype.is_array_type and self.attr == 'length':
            self.type = TYPE_INT
            self.array_type = vartype
        else:
            raise errors.InvalidAttributeError(self.lineno, vartype, self.attr)
        return self


@dataclass
class ExpNewArray(Exp):
    elem_type: Type
    len: Exp

    def __str__(self):
        return f'new {self.elem_type}[{self.len}]'

    @property
    def called_functions(self):
        return self.len.called_functions

    def check(self, fenv, venv):
        self.len = self.len.check(fenv, venv)
        self.type = self.elem_type.array_type
        return self


# -------- statements --------

def as_block(s):
    if isinstance(s, list):
        return StmtBlock(s[0].lineno, s)
    elif isinstance(s, StmtBlock):
        return s
    elif isinstance(s, Stmt):
        return StmtBlock(s.lineno, [s])
    else:
        assert False


@dataclass
class Lhs(Node):
    type = None

    def check(self, fenv, venv):
        """checks corectness of LHS"""
        return self

    @property
    def called_functions(self):
        """returns a set of ids of functions called from this expression"""
        return set()


@dataclass
class LhsVar(Lhs):
    id: str

    def __str__(self):
        return str(self.id)

    def check(self, fenv, venv):
        try:
            self.type = venv[self.id]
        except KeyError:
            raise errors.UndefinedVariableError(self.lineno, self.id)
        return self


@dataclass
class LhsArray(Lhs):
    id: str
    idx: Exp

    def __str__(self):
        return f'{self.id}[{self.idx}]'

    @property
    def called_functions(self):
        return self.idx.called_functions

    def check(self, fenv, venv):
        self.idx = self.idx.check(fenv, venv)
        try:
            self.type = venv[self.id].element_type
        except KeyError:
            raise errors.UndefinedVariableError(self.lineno, self.id)
        return self


@dataclass
class Stmt(Node):
    @property
    def called_functions(self):
        """returns a set of ids of functions called from this statement"""
        return set()

    @property
    def returns(self):
        """returns true if the statement contains a return statement on all code paths"""
        return False

    def check(self, fenv, venv):
        """
        - checks corectness of statement
        - returns simplified statement
        """
        return self, venv


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

    def check(self, fenv, venv):
        if self.type == TYPE_VOID:
            raise errors.InvalidTypeError(self.lineno, self.type)
        nvenv = venv.copy()
        nvenv[self.id] = self.type
        return self, nvenv


@dataclass
class StmtDeclInit(StmtDecl):
    exp: Exp

    @property
    def called_functions(self):
        return self.exp.called_functions

    def __str__(self):
        return f'{self.type} {self.id} = {self.exp};'

    def check(self, fenv, venv):
        self.exp = self.exp.check(fenv, venv)
        if self.type != self.exp.type:
            raise errors.TypeMismatchError(self.lineno)
        nvenv = venv.copy()
        nvenv[self.id] = self.type
        return self, nvenv


@dataclass
class StmtAss(Stmt):
    lhs: Lhs
    exp: Exp

    @property
    def called_functions(self):
        return self.exp.called_functions

    def __str__(self):
        return f'{self.lhs} = {self.exp};'

    def check(self, fenv, venv):
        self.exp = self.exp.check(fenv, venv)
        self.lhs = self.lhs.check(fenv, venv)
        if self.lhs.type != self.exp.type:
            raise errors.TypeMismatchError(self.lineno)
        return self, venv


@dataclass
class StmtAssVar(StmtAss):
    pass


@dataclass
class StmtAssArray(StmtAss):
    @property
    def called_functions(self):
        fs = super().called_functions
        fs.update(self.lhs.called_functions)
        return fs


@dataclass
class StmtReturn(Stmt):
    exp: Exp

    @property
    def called_functions(self):
        return self.exp.called_functions

    @property
    def returns(self):
        return True

    def __str__(self):
        return f'return {self.exp};'

    def check(self, fenv, venv):
        self.exp = self.exp.check(fenv, venv)
        if venv['*'] != self.exp.type:
            raise errors.TypeMismatchError(self.lineno)
        return self, venv


@dataclass
class StmtVoidReturn(Stmt):
    @property
    def returns(self):
        return True

    def __str__(self):
        return 'return;'

    def check(self, fenv, venv):
        if venv['*'] != TYPE_VOID:
            raise errors.TypeMismatchError(self.lineno)
        return self, venv


@dataclass
class StmtIf(Stmt):
    cond: Exp
    stmt: Stmt

    @property
    def called_functions(self):
        fs = set()
        fs.update(self.cond.called_functions)
        fs.update(self.stmt.called_functions)
        return fs

    def __post_init__(self):
        self.stmt = as_block(self.stmt)

    def __str__(self):
        return f'if {self.cond} {self.stmt}'

    def check(self, fenv, venv):
        self.cond = self.cond.check(fenv, venv)
        if self.cond.type != TYPE_BOOL:
            raise errors.TypeMismatchError(self.lineno)
        self.stmt, _ = self.stmt.check(fenv, venv)
        if isinstance(self.cond, ExpBoolConst):
            if self.cond.val:
                return self.stmt, venv
            else:
                return StmtSkip(self.lineno), venv
        return self, venv


@dataclass
class StmtIfElse(StmtIf):
    stmt2: Stmt

    @property
    def called_functions(self):
        fs = super().called_functions
        fs.update(self.stmt2.called_functions)
        return fs

    @property
    def returns(self):
        return self.stmt.returns and self.stmt2.returns

    def __post_init__(self):
        super().__post_init__()
        self.stmt2 = as_block(self.stmt2)

    def __str__(self):
        return f'if {self.cond} {self.stmt} else {self.stmt2}'

    def check(self, fenv, venv):
        super(StmtIfElse, self).check(fenv, venv)
        self.stmt2, _ = self.stmt2.check(fenv, venv)
        if isinstance(self.cond, ExpBoolConst):
            if self.cond.val:
                return self.stmt, venv
            else:
                return self.stmt2, venv
        return self, venv


@dataclass
class StmtWhile(StmtIf):
    def __str__(self):
        return f'while {self.cond} {self.stmt}'

    def check(self, fenv, venv):
        super(StmtWhile, self).check(fenv, venv)
        if isinstance(self.cond, ExpBoolConst):
            if self.cond.val:
                return StmtWhileTrue(self.lineno, self.stmt), venv
            else:
                return StmtSkip(self.lineno), venv
        return self, venv


@dataclass
class StmtWhileTrue(Stmt):
    stmt: Stmt

    def __post_init__(self):
        self.stmt = as_block(self.stmt)

    def __str__(self):
        return f'while (true) {self.stmt}'

    @property
    def called_functions(self):
        return self.stmt.called_functions

    @property
    def returns(self):
        return True

    def check(self, fenv, venv):
        self.stmt, _ = self.stmt.check(fenv, venv)
        return self, venv


@dataclass
class StmtExp(Stmt):
    exp: Exp

    @property
    def called_functions(self):
        return self.exp.called_functions

    def __str__(self):
        return f'{self.exp};'

    def check(self, fenv, venv):
        self.exp = self.exp.check(fenv, venv)
        return self, venv


@dataclass
class StmtBlock(Stmt):
    stmts: list

    @property
    def called_functions(self):
        fs = set()
        for s in self.stmts:
            fs.update(s.called_functions)
        return fs

    @property
    def returns(self):
        return any(s.returns for s in self.stmts)

    def __str__(self):
        return '{\n'\
               + '\n'.join('\n'.join(f'  {line}' for line in str(s).splitlines()) for s in self.stmts)\
               + '\n}'

    def check(self, fenv, venv):
        localids = []
        nvenv = venv.copy()
        nstmts = []
        for stmt in self.stmts:
            nstmt, nvenv = stmt.check(fenv, nvenv)
            if isinstance(nstmt, StmtDecl):
                if nstmt.id in localids:
                    raise errors.DuplicateVariableNameError(nstmt.lineno, nstmt.id)
                localids.append(nstmt.id)
            nstmts.append(nstmt)
            if nstmt.returns:
                break
        self.stmts = nstmts
        return self, venv


# -------- function definitions --------

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

    @property
    def called_functions(self):
        """returns a set of ids of functions called from this statement"""
        return set()

    @property
    def returns(self):
        """returns true if the function contains a return statement on all code paths"""
        return False

    def check(self, fenv):
        """checks corectness of the function"""
        pass


@dataclass
class TopDef(FunDecl):
    block: StmtBlock

    @property
    def called_functions(self):
        return self.block.called_functions

    @property
    def returns(self):
        return self.block.returns

    def __str__(self):
        return f'{self.type} {self.id} (' + ', '.join(str(a) for a in self.args) + f') {self.block}'

    def check(self, fenv):
        if self.id == 'main' and (self.type != TYPE_INT or len(self.args) > 0):
            raise errors.InvalidMainFunctionError(self.lineno)
        venv = {}
        for arg in self.args:
            if arg.id in venv:
                raise errors.DuplicateVariableNameError(arg.lineno, arg.id)
            elif arg.type == TYPE_VOID:
                raise errors.InvalidTypeError(arg.lineno, arg.type)
            venv[arg.id] = arg.type
        venv['*'] = self.type
        self.block, _ = self.block.check(fenv, venv)
        if not self.block.returns:
            if self.type != TYPE_VOID:
                raise errors.MissingReturnError(self.lineno)
            self.block.stmts.append(StmtVoidReturn(self.block.lineno))

@dataclass
class BuiltinFunDecl(FunDecl):
    def __post_init__(self):
        # this will simplify type checking
        self.args = [FunArg(0, t, '') for t in self.args]

    @property
    def returns(self):
        return True

    def __str__(self):
        return f'// {self.type} {self.id} (' + ', '.join(str(a.type) for a in self.args) + ')'


# -------- program --------

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

    def check(self):
        """
        - checks corectness of the program
        - removes unused functions
        """
        fenv = {}
        for topdef in self.topdefs:
            if topdef.id in fenv:
                raise errors.DuplicateFunctionNameError(topdef.lineno, topdef.id)
            fenv[topdef.id] = topdef
        if 'main' not in fenv:
            raise errors.MissingMainFunctionError(self.lineno)
        for topdef in self.topdefs:
            topdef.check(fenv)

        queue = ['main']
        called_functions = []
        while len(queue) > 0:
            fid = queue.pop(0)
            called_functions.append(fid)
            for fid2 in fenv[fid].called_functions:
                if fid2 not in called_functions:
                    queue.append(fid2)

        ntopdefs = []
        for topdef in self.topdefs:
            if topdef.id in called_functions:
                ntopdefs.append(topdef)
        self.topdefs = ntopdefs
