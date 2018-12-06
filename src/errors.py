class CompilerError(Exception):
    msg = 'internal error'

    def __init__(self, line):
        self.line = line

    def __str__(self):
        return self.msg + (f" (line {self.line})" if self.line else "")


class IllegalCharacterError(CompilerError):
    def __init__(self, line, char):
        super().__init__(line)
        self.msg = f'invalid character: {char}'


class ParsingError(CompilerError):
    msg = 'parsing failed'


class TypeMismatchError(CompilerError):
    msg = 'type mismatch'


class InvalidTypeError(CompilerError):
    def __init__(self, line, name):
        super().__init__(line)
        self.msg = f'invalid type: {name}'


class InvalidOperatorError(CompilerError):
    def __init__(self, line, op):
        super().__init__(line)
        self.msg = f'invalid operator: {op}'


class DuplicateFunctionNameError(CompilerError):
    def __init__(self, line, name):
        super().__init__(line)
        self.msg = f'duplicate function name: {name}'

class InvalidMainFunctionError(CompilerError):
    msg = 'invalid main() definition'


class MissingMainFunctionError(CompilerError):
    msg = 'missing main() definition'

class DuplicateVariableNameError(CompilerError):
    def __init__(self, line, name):
        super().__init__(line)
        self.msg = f'duplicate variable name: {name}'


class UndefinedVariableError(CompilerError):
    def __init__(self, line, ident):
        super().__init__(line)
        self.msg = f'undefined variable: {ident}'

class UndefinedFunctionError(CompilerError):
    def __init__(self, line, ident):
        super().__init__(line)
        self.msg = f'undefined function: {ident}'

class InvalidCallError(CompilerError):
    def __init__(self, line, ident):
        super().__init__(line)
        self.msg = f'invalid call to function: {ident}'

class MissingReturnError(CompilerError):
    msg = 'function has code path without return statement'

# noinspection PyShadowingBuiltins
class NotImplementedError(CompilerError):
    msg = 'not implemented'
