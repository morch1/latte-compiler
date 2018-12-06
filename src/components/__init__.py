class Component:
    def __init__(self, lineno):
        self.lineno = lineno
        self._str = '???'

    def __str__(self):
        return self._str

    def __repr__(self):
        return self._str
