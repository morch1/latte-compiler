import errors
from ins_abs import StmtComp, StmtAssVar, StmtExp, ExpBinOp, ExpVar, ExpConst, ExpUnOp

_binop_instr = {
    '+': 'add',
    '-': 'sub',
    '*': 'mul',
    '/': 'sdiv',
}


def _exp_result(exp, tmpid):
    """
    :param exp: last generated expression
    :param tmpid: next free register id
    :return: the name of the register containing the result of exp,
        or the value of exp if it was a constant
    """
    if isinstance(exp, ExpConst):
        return f'{exp.val}'
    else:
        return f'%t{tmpid - 1}'


def _generate(t, env, tmpid):
    if isinstance(t, StmtComp):
        code1, env, tmpid = _generate(t.stmt1, env, tmpid)
        code2, env, tmpid = _generate(t.stmt2, env, tmpid)
        return f'{code1}{code2}', env, tmpid
    elif isinstance(t, StmtAssVar):
        code, _, tmpid = _generate(t.exp, env, tmpid)
        if t.var not in env:
            env.append(t.var)
            code += f'%v{t.var} = alloca i32\n'
        code += f'store i32 {_exp_result(t.exp, tmpid)}, i32* %v{t.var}\n'
        return code, env, tmpid
    elif isinstance(t, StmtExp):
        code, _, tmpid = _generate(t.exp, env, tmpid)
        code += f'call void @printInt(i32 {_exp_result(t.exp, tmpid)})\n'
        return code, env, tmpid
    elif isinstance(t, ExpUnOp):
        code, _, tmpid = _generate(t.exp, env, tmpid)
        arg = _exp_result(t.exp, tmpid)
        if t.op == '-':
            arg = f'sub i32 0, {arg}'
        else:
            raise errors.NotImplemented(t.lineno)
        code = f'{code}%t{tmpid} = {arg}\n'
        return code, env, tmpid + 1
    elif isinstance(t, ExpBinOp):
        code1, _, tmpid = _generate(t.exp1, env, tmpid)
        arg1 = _exp_result(t.exp1, tmpid)
        code2, _, tmpid = _generate(t.exp2, env, tmpid)
        arg2 = _exp_result(t.exp2, tmpid)
        instr = _binop_instr.get(t.op)
        if not instr:
            raise errors.NotImplemented(t.lineno)
        code = f'{code1}{code2}%t{tmpid} = {instr} i32 {arg1}, {arg2}\n'
        return code, env, tmpid + 1
    elif isinstance(t, ExpVar):
        code = f'%t{tmpid} = load i32, i32* %v{t.var}\n'
        return code, env, tmpid + 1
    else:
        return '', env, tmpid


# noinspection PyShadowingBuiltins
def compile(tree):
    code, _, _ = _generate(tree, [], 0)
    print('declare void @printInt(i32)\n'
          'define i32 @main() {\n'
          f'{code}'
          f'ret i32 0\n'
          '}\n')
