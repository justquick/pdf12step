class AttrDict(dict):
    _has_default = False
    _default = None

    def __init__(self, arg=(), **kwargs):
        self._has_default = 'default' in kwargs
        self._default = kwargs.pop('default', None)
        items = arg.items() if isinstance(arg, dict) else arg
        for key, value in items:
            self[key] = self.fromdict(value)
        for key, value in kwargs.items():
            self[key] = self.fromdict(value)

    def __getattr__(self, name):
        try:
            value = self[name]
        except KeyError:
            raise AttributeError(name)
        self[name] = self.fromdict(value)
        return self[name]

    def __getitem__(self, name):
        try:
            return super().__getitem__(name)
        except KeyError:
            if self._has_default:
                return self._default
            raise

    def __setattr__(self, name, value):
        if name in dir(self):
            super().__setattr__(name, value)
        else:
            self[name] = self.fromdict(value)

    @classmethod
    def fromdict(cls, value):
        return cls(value) if isinstance(value, dict) else value
