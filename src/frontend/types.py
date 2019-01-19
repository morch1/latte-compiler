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

    @property
    def is_array_type(self):
        return self.name.endswith('[]')

    @property
    def array_type(self):
        assert not self.is_array_type
        return self.get_by_name(f'{self.name}[]')

    @property
    def element_type(self):
        assert self.is_array_type
        return self.get_by_name(self.name[:-2])

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

TYPE_INT_ARRAY = Type('int[]')
TYPE_BOOL_ARRAY = Type('bool[]')
TYPE_STRING_ARRAY = Type('string[]')
