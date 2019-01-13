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

# _NEG_OPS = {'||': '&&', '==': '!=', '<': '>=', '>': '<='}
# NEG_OPS = {}
# for k, v in _NEG_OPS.items():
#     NEG_OPS[v] = k
# NEG_OPS = {**_NEG_OPS, **NEG_OPS}
#
# def negate_bool_exp(exp):
#     if isinstance(exp, ast.ExpBinOp):
#         if exp.op in ['||', '&&']:
#             negate_bool_exp(exp.exp1)
#             negate_bool_exp(exp.exp2)
#         exp.op = NEG_OPS[exp.op]


@checker(ast.ExpUnOp)
def check(self, fenv, venv):
    exp_type = self.exp.check(fenv, venv)
    if self.op == '-' and exp_type == ast.TYPE_INT:
        self.type = ast.TYPE_INT
    elif self.op == '!' and exp_type == ast.TYPE_BOOL:
        # self.op = ''
        # negate_bool_exp(self.exp)
        self.type = ast.TYPE_BOOL
    else:
        raise errors.TypeMismatchError(self.lineno)
    return self.type

@checker(ast.ExpBinOp)
def check(self, fenv, venv):
    exp_types = (self.exp1.check(fenv, venv), self.exp2.check(fenv, venv))
    if ast.TYPE_VOID in exp_types:
        raise errors.TypeMismatchError(self.lineno)
    if self.op in ['+', '-', '*', '/', '%'] and exp_types == (ast.TYPE_INT, ast.TYPE_INT):
        self.type = ast.TYPE_INT
    elif self.op == '+' and exp_types == (ast.TYPE_STRING, ast.TYPE_STRING):
        self.type = ast.TYPE_STRING
    elif (self.op in ['||', '&&'] and exp_types == (ast.TYPE_BOOL, ast.TYPE_BOOL)) or\
            (self.op in ['<', '<=', '>', '>=', '==', '!='] and exp_types[0] == exp_types[1]):
        self.type = ast.TYPE_BOOL
    else:
        raise errors.TypeMismatchError(self.lineno)
    return self.type

@checker(ast.ExpVar)
def check(self, fenv, venv):
    try:
        self.type = venv[self.id]
    except KeyError:
        raise errors.UndefinedVariableError(self.lineno, self.id)
    return self.type

@checker(ast.ExpConst)
def check(self, fenv, venv):
    return self.type

@checker(ast.ExpFun)
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
    self.type = fun.type
    return self.type


@checker(ast.LhsVar)
def check(self, venv):
    try:
        return venv[self.id]
    except KeyError:
        raise errors.UndefinedVariableError(self.lineno, self.id)

@checker(ast.StmtSkip)
def check(self, fenv, venv):
    return venv

@checker(ast.StmtDecl)
def check(self, fenv, venv):
    nvenv = venv.copy()
    nvenv[self.id] = self.type
    return nvenv

@checker(ast.StmtAss)
def check(self, fenv, venv):
    exp_type = self.exp.check(fenv, venv)
    lhs_type = self.lhs.check(venv)
    if lhs_type != exp_type:
        raise errors.TypeMismatchError(self.lineno)
    return venv

@checker(ast.StmtReturn)
def check(self, fenv, venv):
    exp_type = self.exp.check(fenv, venv)
    if venv['*'] != exp_type:
        raise errors.TypeMismatchError(self.lineno)
    return venv

@checker(ast.StmtVoidReturn)
def check(self, fenv, venv):
    if venv['*'] != ast.TYPE_VOID:
        raise errors.TypeMismatchError(self.lineno)
    return venv

@checker(ast.StmtIf)
def check(self, fenv, venv):
    cond_type = self.cond.check(fenv, venv)
    if cond_type != ast.TYPE_BOOL:
        raise errors.TypeMismatchError(self.lineno)
    self.stmt.check(fenv, venv)
    return venv

@checker(ast.StmtIfElse)
def check(self, fenv, venv):
    super(ast.StmtIfElse, self).check(fenv, venv)
    self.stmt2.check(fenv, venv)
    return venv

@checker(ast.StmtWhile)
def check(self, fenv, venv):
    super(ast.StmtWhile, self).check(fenv, venv)
    return venv

@checker(ast.StmtExp)
def check(self, fenv, venv):
    self.exp.check(fenv, venv)
    return venv

@checker(ast.StmtBlock)
def check(self, fenv, venv):
    localids = []
    nvenv = venv.copy()
    for stmt in self.stmts:
        if isinstance(stmt, ast.StmtDecl):
            if stmt.id in localids:
                raise errors.DuplicateVariableNameError(stmt.lineno, stmt.id)
            localids.append(stmt.id)
        nvenv = stmt.check(fenv, nvenv)
    return venv

@checker(ast.TopDef)
def check(self, fenv):
    if self.id == 'main' and (self.type != ast.TYPE_INT or len(self.args) > 0):
        raise errors.InvalidMainFunctionError(self.lineno)
    if self.type != ast.TYPE_VOID and not self.block.returns:
        raise errors.MissingReturnError(self.lineno)
    venv = {}
    for arg in self.args:
        if arg.id in venv:
            raise errors.DuplicateVariableNameError(arg.lineno, arg.id)
        venv[arg.id] = arg.type
    venv['*'] = self.type
    self.block.check(fenv, venv)

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
