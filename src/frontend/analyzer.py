import frontend.ast as ast
import frontend.types as types
import errors
from functools import wraps

def analyzer(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        setattr(cls, 'check', wrapper)
        return func
    return decorator

@analyzer(ast.ExpUnOp)
def check(self, fenv, venv):
    exp_type = self.exp.check(fenv, venv)
    try:
        return self.op.check(exp_type)
    except errors.TypeMismatchError as ex:
        ex.line = self.lineno
        raise ex

@analyzer(ast.ExpBinOp)
def check(self, fenv, venv):
    exp1_type = self.exp1.check(fenv, venv)
    exp2_type = self.exp2.check(fenv, venv)
    try:
        return self.op.check(exp1_type, exp2_type)
    except errors.TypeMismatchError as ex:
        ex.line = self.lineno
        raise ex

@analyzer(ast.ExpVar)
def check(self, fenv, venv):
    try:
        return venv[self.id]
    except KeyError:
        raise errors.UndefinedVariableError(self.lineno, self.id)


@analyzer(ast.ExpIntConst)
def check(self, fenv, venv):
    return types.INT

@analyzer(ast.ExpStringConst)
def check(self, fenv, venv):
    return types.STRING

@analyzer(ast.ExpBoolConst)
def check(self, fenv, venv):
    return types.BOOL

@analyzer(ast.ExpApp)
def check(self, fenv, venv):
    try:
        fun = fenv[self.fid]
    except KeyError:
        raise errors.UndefinedFunctionError(self.lineno, self.fid)
    if len(self.args) != len(fun.args):
        raise errors.InvalidCallError(self.lineno, self.fid)
    for ca, fa in zip(self.args, fun.args):
        exp_type = ca.check(fenv, venv)
        if exp_type != fa.type:
            raise errors.TypeMismatchError(self.lineno)
    return fun.type

@analyzer(ast.LhsVar)
def check(self, venv):
    try:
        return venv[self.id]
    except KeyError:
        raise errors.UndefinedVariableError(self.lineno, self.id)

@analyzer(ast.StmtSkip)
def check(self, fenv, venv):
    return venv

@analyzer(ast.StmtDecl)
def check(self, fenv, venv):
    venv[self.id] = self.type
    return venv

@analyzer(ast.StmtAssVar)
def check(self, fenv, venv):
    exp_type = self.exp.check(fenv, venv)
    lhs_type = self.lhs.check(venv)
    if lhs_type != exp_type:
        raise errors.TypeMismatchError(self.lineno)
    return venv

@analyzer(ast.StmtInc)
def check(self, fenv, venv):
    lhs_type = self.lhs.check(venv)
    if lhs_type != types.INT:
        raise errors.TypeMismatchError(self.lineno)
    return venv

@analyzer(ast.StmtDec)
def check(self, fenv, venv):
    lhs_type = self.lhs.check(venv)
    if lhs_type != types.INT:
        raise errors.TypeMismatchError(self.lineno)
    return venv

@analyzer(ast.StmtReturn)
def check(self, fenv, venv):
    exp_type = self.exp.check(fenv, venv)
    if venv['*'] != exp_type:
        raise errors.TypeMismatchError(self.lineno)
    return venv

@analyzer(ast.StmtVoidReturn)
def check(self, fenv, venv):
    if venv['*'] != types.VOID:
        raise errors.TypeMismatchError(self.lineno)
    return venv

@analyzer(ast.StmtIf)
def check(self, fenv, venv):
    cond_type = self.cond.check(fenv, venv)
    if cond_type != types.BOOL:
        raise errors.TypeMismatchError(self.lineno)
    self.stmt.check(fenv, venv)
    return venv

@analyzer(ast.StmtIfElse)
def check(self, fenv, venv):
    cond_type = self.cond.check(fenv, venv)
    if cond_type != types.BOOL:
        raise errors.TypeMismatchError(self.lineno)
    self.stmt1.check(fenv, venv)
    self.stmt2.check(fenv, venv)
    return venv

@analyzer(ast.StmtWhile)
def check(self, fenv, venv):
    cond_type = self.cond.check(fenv, venv)
    if cond_type != types.BOOL:
        raise errors.TypeMismatchError(self.lineno)
    self.stmt.check(fenv, venv)
    return venv

@analyzer(ast.StmtExp)
def check(self, fenv, venv):
    self.exp.check(fenv, venv)
    return venv

@analyzer(ast.StmtBlock)
def check(self, fenv, venv):
    localids = []
    nvenv = venv
    for stmt in self.stmts:
        if isinstance(stmt, ast.StmtDecl):
            if stmt.id in localids:
                raise errors.DuplicateVariableNameError(stmt.lineno, stmt.id)
            localids.append(stmt.id)
        nvenv = stmt.check(fenv, nvenv)
    return venv

@analyzer(ast.FunDef)
def check(self, fenv):
    if self.id == 'main' and (self.type != types.INT or len(self.args) > 0):
        raise errors.InvalidMainFunctionError(self.lineno)
    venv = {}
    for arg in self.args:
        if arg.id in venv:
            raise errors.DuplicateVariableNameError(arg.lineno, arg.id)
        venv[arg.id] = arg.type
    venv['*'] = self.type
    self.block.check(fenv, venv)

@analyzer(ast.Program)
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
