class CompilerError(Exception):
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return f"error (line {self.line})"


class IllegalCharacter(CompilerError):
    def __init__(self, line, char):
        super(IllegalCharacter, self).__init__(line)
        self.char = char

    def __str__(self):
        return f"illegal character: {self.char} (line {self.line})"


class ParsingError(CompilerError):
    def __str__(self):
        return "parsing failed" + (f" (line {self.line})" if self.line else "")


class UndefinedVariable(CompilerError):
    def __init__(self, line, variable):
        super(UndefinedVariable, self).__init__(line)
        self.variable = variable

    def __str__(self):
        return f"undefined variable: {self.variable} (line {self.line})"


class NotImplemented(CompilerError):
    def __str__(self):
        return f"not implemented (line {self.line})"
