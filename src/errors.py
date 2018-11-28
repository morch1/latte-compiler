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


class UndefinedVariableError(CompilerError):
    def __init__(self, line, ident):
        super().__init__(line)
        self.msg = f'undefined variable: {ident}'


# noinspection PyShadowingBuiltins
class NotImplementedError(CompilerError):
    msg = 'not implemented'
