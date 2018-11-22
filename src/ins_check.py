from errors import UndefinedVariable
from ins_abs import StmtAssVar, StmtExp, ExpBinOp, ExpVar, StmtList


def check(t, env):
    if isinstance(t, StmtList):
        for s in t.stmts:
            env = check(s, env)
        return env
    elif isinstance(t, StmtAssVar):
        check(t.exp, env)
        return env + [t.var]
    elif isinstance(t, StmtExp):
        check(t.exp, env)
        return env
    elif isinstance(t, ExpBinOp):
        check(t.exp1, env)
        check(t.exp2, env)
        return env
    elif isinstance(t, ExpVar):
        if t.var not in env:
            raise UndefinedVariable(t.lineno, t.var)
        return env
    else:
        return env
