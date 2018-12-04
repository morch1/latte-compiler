import re
from errors import InvalidOperatorError, TypeMismatchError
from ltypes import TYPE_INT, TYPE_BOOL, TYPE_STRING


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
            raise TypeMismatchError(None)

    @classmethod
    def get_by_name(cls, op):
        try:
            return cls._op_map[op]
        except KeyError:
            raise InvalidOperatorError(None, op)

    def op_regex(self):
        return re.compile(re.escape(self.op)).pattern


OP_PLUS = Operator('+', {
    (TYPE_INT, TYPE_INT): TYPE_INT,
    (TYPE_STRING, TYPE_STRING): TYPE_STRING,
})
OP_MINUS = Operator('-', {
    (TYPE_INT,): TYPE_INT,
    (TYPE_INT, TYPE_INT): TYPE_INT,
})
OP_TIMES = Operator('*', {
    (TYPE_INT, TYPE_INT): TYPE_INT,
})
OP_DIV = Operator('/', {
    (TYPE_INT, TYPE_INT): TYPE_INT,
})
OP_MOD = Operator('%', {
    (TYPE_INT, TYPE_INT): TYPE_INT,
})
OP_NOT = Operator('!', {
    (TYPE_BOOL,): TYPE_BOOL,
})
OP_OR = Operator('||', {
    (TYPE_BOOL, TYPE_BOOL): TYPE_BOOL,
})
OP_AND = Operator('&&', {
    (TYPE_BOOL, TYPE_BOOL): TYPE_BOOL,
})
OP_LT = Operator('<', {
    (TYPE_INT, TYPE_INT): TYPE_BOOL,
})
OP_LE = Operator('<=', {
    (TYPE_INT, TYPE_INT): TYPE_BOOL,
})
OP_GT = Operator('>', {
    (TYPE_INT, TYPE_INT): TYPE_BOOL,
})
OP_GE = Operator('>=', {
    (TYPE_INT, TYPE_INT): TYPE_BOOL,
})
OP_EQ = Operator('==', {
    (TYPE_INT, TYPE_INT): TYPE_BOOL,
    (TYPE_BOOL, TYPE_BOOL): TYPE_BOOL,
    (TYPE_STRING, TYPE_STRING): TYPE_BOOL,
})
OP_NE = Operator('!=', {
    (TYPE_INT, TYPE_INT): TYPE_BOOL,
    (TYPE_BOOL, TYPE_BOOL): TYPE_BOOL,
    (TYPE_STRING, TYPE_STRING): TYPE_BOOL,
})
