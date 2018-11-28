
class Type:
    _type_map = {}

    def __init__(self, name):
        self.name = name
        Type._type_map[name] = self

    def __str__(self):
        return self.name

    @classmethod
    def get_by_name(cls, name):
        return cls._type_map[name]


TYPE_INT = Type('int')
TYPE_BOOL = Type('boolean')
TYPE_STRING = Type('string')
TYPE_VOID = Type('void')
