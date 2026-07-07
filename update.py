with open("/Users/ankur/Documents/Python-Project/rich-object/src/rich_object/object.py", "r") as f:
    code = f.read()

# Fix Object.__init__
init_old = """    def __init__(self, *args, lock=False, **kwargs):
        object.__setattr__(self, '_lock', False)
        object.__setattr__(self, '_initialized', False)
        
        super().__init__()
        self.update(dict(*args, **kwargs))
        
        object.__setattr__(self, '_lock', lock)
        object.__setattr__(self, '_initialized', True)"""

init_new = """    def __init__(self, *args, lock=False, **kwargs):
        object.__setattr__(self, '_lock', lock)
        object.__setattr__(self, '_initialized', False)
        
        super().__init__()
        self.update(dict(*args, **kwargs))
        
        object.__setattr__(self, '_initialized', True)"""
code = code.replace(init_old, init_new)

# Fix __getattr__
ga_old = """        if key not in self:
            if object.__getattribute__(self, '_lock'):
                raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")"""
ga_new = """        if key not in self:
            if object.__getattribute__(self, '_lock') and object.__getattribute__(self, '_initialized'):
                raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")"""
code = code.replace(ga_old, ga_new)

# Fix __getitem__
gi_old = """        if key not in self:
            if object.__getattribute__(self, '_lock'):
                raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")"""
gi_new = """        if key not in self:
            if object.__getattribute__(self, '_lock') and object.__getattribute__(self, '_initialized'):
                raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")"""
code = code.replace(gi_old, gi_new)

# Fix __setitem__
si_old = """    def __setitem__(self, key, value):
        if object.__getattribute__(self, '_lock'):
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")"""
si_new = """    def __setitem__(self, key, value):
        if object.__getattribute__(self, '_lock') and getattr(self, '_initialized', True):
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")"""
code = code.replace(si_old, si_new)

# Fix __delitem__
di_old = """    def __delitem__(self, key):
        if object.__getattribute__(self, '_lock'):
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")"""
di_new = """    def __delitem__(self, key):
        if object.__getattribute__(self, '_lock') and getattr(self, '_initialized', True):
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")"""
code = code.replace(di_old, di_new)


# Remove __eq__
eq_str = """    def __eq__(self, other):
        if not isinstance(other, Object):
            return False
        return super().__eq__(other)"""
code = code.replace(eq_str, "")

with open("/Users/ankur/Documents/Python-Project/rich-object/src/rich_object/object.py", "w") as f:
    f.write(code)
