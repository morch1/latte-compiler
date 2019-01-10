from errors import InvalidTypeError


class Type:
    _type_map = {}

    def __init__(self, name):
        self.name = name
        Type._type_map[name] = self

    def __str__(self):
        return self.name

    @classmethod
    def get_by_name(cls, name):
        try:
            return cls._type_map[name]
        except KeyError:
            raise InvalidTypeError(None, name)


INT = Type('int')
BOOL = Type('boolean')
STRING = Type('string')
VOID = Type('void')
