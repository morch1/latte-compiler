import errors
from dataclasses import dataclass

@dataclass(frozen=True)
class Type:
    name: str
    _type_map = {}

    def __post_init__(self):
        self.__class__._type_map[self.name] = self

    def __str__(self):
        return self.name

    @classmethod
    def get_by_name(cls, name):
        try:
            return cls._type_map[name]
        except KeyError:
            raise errors.InvalidTypeError(None, name)


TYPE_INT = Type('int')
TYPE_BOOL = Type('boolean')
TYPE_STRING = Type('string')
TYPE_VOID = Type('void')
