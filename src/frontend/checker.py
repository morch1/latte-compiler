import frontend.ast as ast
import errors
from functools import wraps

def checker(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        setattr(cls, 'check', wrapper)
        return func
    return decorator


@checker(ast.ExpUnOp)
def check(self, fenv, venv):
    self.exp = self.exp.check(fenv, venv)
    if self.op == '-' and self.exp.type == ast.TYPE_INT:
        if isinstance(self.exp, ast.ExpIntConst):
            return ast.ExpIntConst(self.lineno, -self.exp.val)
        self.type = ast.TYPE_INT
    elif self.op == '!' and self.exp.type == ast.TYPE_BOOL:
        if isinstance(self.exp, ast.ExpBoolConst):
            return ast.ExpBoolConst(self.lineno, not self.exp.val)
        self.type = ast.TYPE_BOOL
    else:
        raise errors.TypeMismatchError(self.lineno)
    return self

@checker(ast.ExpBinOp)
def check(self, fenv, venv):
    self.exp1 = self.exp1.check(fenv, venv)
    self.exp2 = self.exp2.check(fenv, venv)
    exp_types = (self.exp1.type, self.exp2.type)
    if ast.TYPE_VOID in exp_types:
        raise errors.TypeMismatchError(self.lineno)
    if self.op in ['+', '-', '*', '/', '%'] and exp_types == (ast.TYPE_INT, ast.TYPE_INT):
        if isinstance(self.exp1, ast.ExpConst) and isinstance(self.exp2, ast.ExpConst):
            if self.op == '/':
                return ast.ExpIntConst(self.lineno, self.exp1.val // self.exp2.val)
            else:
                return ast.ExpIntConst(self.lineno, eval(f'{self.exp1.val}{self.op}{self.exp2.val}'))
        self.type = ast.TYPE_INT
    elif self.op == '+' and exp_types == (ast.TYPE_STRING, ast.TYPE_STRING):
        if isinstance(self.exp1, ast.ExpConst) and isinstance(self.exp2, ast.ExpConst):
            return ast.ExpStringConst(self.lineno, self.exp1.val + self.exp2.val)
        self.type = ast.TYPE_STRING
    elif (self.op in ['||', '&&'] and exp_types == (ast.TYPE_BOOL, ast.TYPE_BOOL)) or\
            (self.op in ['<', '<=', '>', '>=', '==', '!='] and self.exp1.type == self.exp2.type):
        if isinstance(self.exp1, ast.ExpConst) and isinstance(self.exp2, ast.ExpConst):
            if self.op == '||':
                return ast.ExpBoolConst(self.lineno, self.exp1.val or self.exp2.val)
            elif self.op == '&&':
                return ast.ExpBoolConst(self.lineno, self.exp1.val and self.exp2.val)
            else:
                return ast.ExpBoolConst(self.lineno, eval(f'{self.exp1.val}{self.op}{self.exp2.val}'))
        self.type = ast.TYPE_BOOL
    else:
        raise errors.TypeMismatchError(self.lineno)
    return self

@checker(ast.ExpVar)
def check(self, fenv, venv):
    try:
        self.type = venv[self.id]
    except KeyError:
        raise errors.UndefinedVariableError(self.lineno, self.id)
    return self

@checker(ast.ExpConst)
def check(self, fenv, venv):
    return self

@checker(ast.ExpFun)
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


@checker(ast.LhsVar)
def check(self, venv):
    try:
        self.type = venv[self.id]
    except KeyError:
        raise errors.UndefinedVariableError(self.lineno, self.id)
    return self

@checker(ast.StmtSkip)
def check(self, fenv, venv):
    return self, venv

@checker(ast.StmtDecl)
def check(self, fenv, venv):
    nvenv = venv.copy()
    nvenv[self.id] = self.type
    return self, nvenv

@checker(ast.StmtDeclInit)
def check(self, fenv, venv):
    self.exp = self.exp.check(fenv, venv)
    if self.type != self.exp.type:
        raise errors.TypeMismatchError(self.lineno)
    nvenv = venv.copy()
    nvenv[self.id] = self.type
    return self, nvenv

@checker(ast.StmtAss)
def check(self, fenv, venv):
    self.exp = self.exp.check(fenv, venv)
    self.lhs = self.lhs.check(venv)
    if self.lhs.type != self.exp.type:
        raise errors.TypeMismatchError(self.lineno)
    return self, venv

@checker(ast.StmtReturn)
def check(self, fenv, venv):
    self.exp = self.exp.check(fenv, venv)
    if venv['*'] != self.exp.type:
        raise errors.TypeMismatchError(self.lineno)
    return self, venv

@checker(ast.StmtVoidReturn)
def check(self, fenv, venv):
    if venv['*'] != ast.TYPE_VOID:
        raise errors.TypeMismatchError(self.lineno)
    return self, venv

@checker(ast.StmtIf)
def check(self, fenv, venv):
    self.cond = self.cond.check(fenv, venv)
    if self.cond.type != ast.TYPE_BOOL:
        raise errors.TypeMismatchError(self.lineno)
    self.stmt, _ = self.stmt.check(fenv, venv)
    if isinstance(self.cond, ast.ExpBoolConst):
        if self.cond.val:
            return self.stmt, venv
        else:
            return ast.StmtSkip(self.lineno), venv
    return self, venv

@checker(ast.StmtIfElse)
def check(self, fenv, venv):
    super(ast.StmtIfElse, self).check(fenv, venv)
    self.stmt2, _ = self.stmt2.check(fenv, venv)
    if isinstance(self.cond, ast.ExpBoolConst):
        if self.cond.val:
            return self.stmt, venv
        else:
            return self.stmt2, venv
    return self, venv

@checker(ast.StmtWhile)
def check(self, fenv, venv):
    super(ast.StmtWhile, self).check(fenv, venv)
    if isinstance(self.cond, ast.ExpBoolConst) and not self.cond.val:
        return ast.StmtSkip(self.lineno), venv
    return self, venv

@checker(ast.StmtExp)
def check(self, fenv, venv):
    self.exp = self.exp.check(fenv, venv)
    return self, venv

@checker(ast.StmtBlock)
def check(self, fenv, venv):
    localids = []
    nvenv = venv.copy()
    nstmts = []
    for stmt in self.stmts:
        nstmt, nvenv = stmt.check(fenv, nvenv)
        if isinstance(nstmt, ast.StmtDecl):
            if nstmt.id in localids:
                raise errors.DuplicateVariableNameError(nstmt.lineno, nstmt.id)
            localids.append(nstmt.id)
        nstmts.append(nstmt)
    self.stmts = nstmts
    return self, venv

@checker(ast.TopDef)
def check(self, fenv):
    if self.id == 'main' and (self.type != ast.TYPE_INT or len(self.args) > 0):
        raise errors.InvalidMainFunctionError(self.lineno)
    venv = {}
    for arg in self.args:
        if arg.id in venv:
            raise errors.DuplicateVariableNameError(arg.lineno, arg.id)
        venv[arg.id] = arg.type
    venv['*'] = self.type
    self.block, _ = self.block.check(fenv, venv)
    if self.type != ast.TYPE_VOID and not self.block.returns:
        raise errors.MissingReturnError(self.lineno)

@checker(ast.BuiltinFunDecl)
def check(self, fenv):
    return

@checker(ast.Program)
def check(self):
    fenv = {}
    for topdef in self.topdefs:
        if topdef.id in fenv:
            raise errors.DuplicateFunctionNameError(topdef.lineno, topdef.id)
        fenv[topdef.id] = topdef
    if 'main' not in fenv:
        raise errors.MissingMainFunctionError(self.lineno)
    for topdef in self.topdefs:
        topdef.check(fenv)
