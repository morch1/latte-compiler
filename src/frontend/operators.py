import re
import errors
import frontend.types as types


class Operator:
    _op_map = {}
    # todo: precedence_table

    def __init__(self, op, allowed_types):
        self.op = op
        self.allowed_types = allowed_types
        self.__class__._op_map[op] = self

    def __str__(self):
        return self.op

    def check(self, *types):
        try:
            return self.allowed_types[types]
        except KeyError:
            raise errors.TypeMismatchError(None)

    @classmethod
    def get_by_name(cls, op):
        try:
            return cls._op_map[op]
        except KeyError:
            raise errors.InvalidOperatorError(None, op)

    def op_regex(self):
        return re.compile(re.escape(self.op)).pattern


PLUS = Operator('+', {
    (types.INT, types.INT): types.INT,
    (types.STRING, types.STRING): types.STRING,
})
MINUS = Operator('-', {
    (types.INT,): types.INT,
    (types.INT, types.INT): types.INT,
})
TIMES = Operator('*', {
    (types.INT, types.INT): types.INT,
})
DIV = Operator('/', {
    (types.INT, types.INT): types.INT,
})
MOD = Operator('%', {
    (types.INT, types.INT): types.INT,
})
NOT = Operator('!', {
    (types.BOOL,): types.BOOL,
})
OR = Operator('||', {
    (types.BOOL, types.BOOL): types.BOOL,
})
AND = Operator('&&', {
    (types.BOOL, types.BOOL): types.BOOL,
})
LT = Operator('<', {
    (types.INT, types.INT): types.BOOL,
})
LE = Operator('<=', {
    (types.INT, types.INT): types.BOOL,
})
GT = Operator('>', {
    (types.INT, types.INT): types.BOOL,
})
GE = Operator('>=', {
    (types.INT, types.INT): types.BOOL,
})
EQ = Operator('==', {
    (types.INT, types.INT): types.BOOL,
    (types.BOOL, types.BOOL): types.BOOL,
    (types.STRING, types.STRING): types.BOOL,
})
NE = Operator('!=', {
    (types.INT, types.INT): types.BOOL,
    (types.BOOL, types.BOOL): types.BOOL,
    (types.STRING, types.STRING): types.BOOL,
})
