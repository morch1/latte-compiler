import re
from ltypes import TYPE_INT, TYPE_BOOL, TYPE_STRING


class Operator:
    _op_map = {}

    def __init__(self, op, val_type):
        self.op = op
        self.val_type = val_type
        Operator._op_map[op] = self

    def __str__(self):
        return self.op

    def op_regex(self):
        return re.compile(re.escape(self.op)).pattern

    @classmethod
    def get_by_name(cls, op):
        return cls._op_map[op]


class UnOp(Operator):
    def __init__(self, op, val_type, arg_type):
        super().__init__(op, val_type)
        self.arg_type = arg_type


class BinOp(Operator):
    def __init__(self, op, val_type, arg1_type, arg2_type):
        super().__init__(op, val_type)
        self.arg1_type = arg1_type
        self.arg2_type = arg2_type


BINOP_PLUS = BinOp('+', TYPE_INT, TYPE_INT, TYPE_INT)
BINOP_MINUS = BinOp('-', TYPE_INT, TYPE_INT, TYPE_INT)
UNOP_MINUS = UnOp(BINOP_MINUS.op, TYPE_INT, TYPE_INT)
BINOP_TIMES = BinOp('*', TYPE_INT, TYPE_INT, TYPE_INT)
BINOP_DIV = BinOp('/', TYPE_INT, TYPE_INT, TYPE_INT)
BINOP_MOD = BinOp('%', TYPE_INT, TYPE_INT, TYPE_INT)
UNOP_NOT = UnOp('!', TYPE_BOOL, TYPE_BOOL)
BINOP_OR = BinOp('||', TYPE_BOOL, TYPE_BOOL, TYPE_BOOL)
BINOP_AND = BinOp('&&', TYPE_BOOL, TYPE_BOOL, TYPE_BOOL)
BINOP_LT = BinOp('<', TYPE_BOOL, TYPE_INT, TYPE_INT)
BINOP_LE = BinOp('<=', TYPE_BOOL, TYPE_INT, TYPE_INT)
BINOP_GT = BinOp('>', TYPE_BOOL, TYPE_INT, TYPE_INT)
BINOP_GE = BinOp('>=', TYPE_BOOL, TYPE_INT, TYPE_INT)
BINOP_INT_EQ = BinOp('==', TYPE_BOOL, TYPE_INT, TYPE_INT)
BINOP_BOOL_EQ = BinOp(BINOP_INT_EQ.op, TYPE_BOOL, TYPE_BOOL, TYPE_BOOL)
BINOP_STRING_EQ = BinOp(BINOP_INT_EQ.op, TYPE_BOOL, TYPE_STRING, TYPE_STRING)
BINOP_INT_NE = BinOp('!=', TYPE_BOOL, TYPE_INT, TYPE_INT)
BINOP_BOOL_NE = BinOp(BINOP_INT_NE.op, TYPE_BOOL, TYPE_BOOL, TYPE_BOOL)
BINOP_STRING_NE = BinOp(BINOP_INT_NE.op, TYPE_BOOL, TYPE_STRING, TYPE_STRING)
