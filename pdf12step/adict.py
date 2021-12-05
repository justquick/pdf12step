class AttrDict(dict):
    def __init__(self, arg=(), **kwargs):
        self.has_default = 'default' in kwargs
        self.default = kwargs.pop('default', None)
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
            if self.has_default:
                return self.default
            raise

    def __setattr__(self, name, value):
        self[name] = self.fromdict(value)

    @classmethod
    def fromdict(cls, value):
        return cls(value) if isinstance(value, (dict, )) else value
