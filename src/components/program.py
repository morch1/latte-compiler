from components import Component
from components.statement import StmtBlock
from errors import InvalidMainFunctionError, DuplicateVariableNameError, MissingReturnError, DuplicateFunctionNameError, \
    MissingMainFunctionError
from ltypes import TYPE_INT, TYPE_VOID, TYPE_STRING


class Arg(Component):
    def __init__(self, lineno, t, ident):
        super().__init__(lineno)
        self._str = f'{t} {ident}'
        self.type = t
        self.id = ident

class FunDef(Component):
    def __init__(self, lineno, t, ident, args):
        super().__init__(lineno)
        self._str = f'{t} {ident} (' + ', '.join(map(lambda s: str(s), args)) + ')'
        self.type = t
        self.id = ident
        self.args = args
        self.block = StmtBlock(self.lineno, [])

    def check(self, fenv):
        if self.id == 'main' and (self.type != TYPE_INT or len(self.args) > 0):
            raise InvalidMainFunctionError(self.lineno)
        venv = {}
        for arg in self.args:
            if arg.id in venv:
                raise DuplicateVariableNameError(arg.lineno, arg.id)
            venv[arg.id] = arg.type
        venv['*'] = self.type
        self.block.check(fenv, venv)

class TopDef(FunDef):
    def __init__(self, lineno, t, ident, args, block: StmtBlock):
        super().__init__(lineno, t, ident, args)
        self._str += f' {block}'
        self.block = block
        if self.type != TYPE_VOID and not self.block.returns:
            raise MissingReturnError(self.lineno)

class BuiltinFunDef(FunDef):
    def __init__(self, t, ident, args_types):
        super().__init__(0, t, ident, list(map(lambda a: Arg(0, a[0], a[1]), args_types)))

class Program(Component):
    def __init__(self, lineno, topdefs):
        super().__init__(lineno)
        self.topdefs = [
            BuiltinFunDef(TYPE_VOID, 'printInt', [(TYPE_INT, 'n')]),
            BuiltinFunDef(TYPE_VOID, 'printString', [(TYPE_STRING, 'str')]),
            BuiltinFunDef(TYPE_VOID, 'error', []),
            BuiltinFunDef(TYPE_INT, 'readInt', []),
            BuiltinFunDef(TYPE_STRING, 'readString', [])
        ] + topdefs
        self._str = '\n'.join(map(lambda s: str(s), self.topdefs))
        fenv = {}
        for topdef in self.topdefs:
            if topdef.id in fenv:
                raise DuplicateFunctionNameError(topdef.lineno, topdef.id)
            fenv[topdef.id] = topdef
        if 'main' not in fenv:
            raise MissingMainFunctionError(self.lineno)
        for topdef in self.topdefs:
            topdef.check(fenv)
