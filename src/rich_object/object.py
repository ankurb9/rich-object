import copy
import re

_PATH_RE = re.compile(r"[^.\[\]]+|\[\d+\]")
_PATH_RE_NEG = re.compile(r"[^.\[\]]+|\[-?\d+\]")

from ._serializers import JsonSerializer, YamlSerializer, TomlSerializer
from ._transforms import DataTransformer
from ._renderer import TemplateRenderer
from ._differ import ObjectDiffer
from ._validator import ObjectValidator

class ObjectList(list):
    """A list subclass that respects lock state and auto-wraps dicts into Objects."""
    __slots__ = ('_lock',)
    def __init__(self, iterable=(), lock=False):
        self._lock = False
        super().__init__()
        for item in iterable:
            self.append(item)
        self._lock = lock

    def _check_lock(self):
        if self._lock:
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")

    def _wrap(self, item):
        if isinstance(item, dict) and not isinstance(item, Object):
            return Object(item, lock=self._lock)
        elif isinstance(item, list) and not isinstance(item, ObjectList):
            return ObjectList(item, lock=self._lock)
        return item

    def append(self, item):
        self._check_lock()
        super().append(self._wrap(item))

    def extend(self, iterable):
        self._check_lock()
        super().extend(self._wrap(item) for item in iterable)

    def insert(self, index, item):
        self._check_lock()
        super().insert(index, self._wrap(item))

    def remove(self, item):
        self._check_lock()
        super().remove(item)

    def pop(self, index=-1):
        self._check_lock()
        return super().pop(index)

    def clear(self):
        self._check_lock()
        super().clear()

    def __setitem__(self, index, item):
        self._check_lock()
        super().__setitem__(index, self._wrap(item))

    def __delitem__(self, index):
        self._check_lock()
        super().__delitem__(index)

    def __iadd__(self, other):
        self._check_lock()
        super().extend(self._wrap(item) for item in other)
        return self

    def __copy__(self):
        new_list = ObjectList(lock=False)
        for item in self:
            super(ObjectList, new_list).append(item)
        new_list._lock = self._lock
        return new_list

    def __deepcopy__(self, memo):
        new_list = ObjectList(lock=False)
        memo[id(self)] = new_list
        for item in self:
            super(ObjectList, new_list).append(copy.deepcopy(item, memo))
        new_list._lock = self._lock
        return new_list


class Object(DataTransformer, TemplateRenderer, ObjectDiffer, ObjectValidator, JsonSerializer, YamlSerializer, TomlSerializer, dict):
    """A dictionary subclass that allows dot notation attribute access
    and automatically creates missing paths (autovivification).
    
    Supports lock (disables create/update/delete).
    """

    def __init__(self, *args, lock=False, **kwargs):
        """Initializes a new Object instance.

        Args:
            *args: Initial dictionary or iterable of key-value pairs to populate the Object.
            lock (bool): If True, disables any create, update, or delete operations on this Object
                         and all of its descendants/elements recursively.
            **kwargs: Additional key-value pairs to populate the Object.

        Example:
            >>> obj = Object(name="John", address={"city": "New York"})
            >>> obj.name
            'John'
            >>> obj.address.city
            'New York'
            >>> locked_obj = Object(x=1, lock=True)
            >>> locked_obj.x = 2
            TypeError: 'Object' is locked and cannot be modified
        """
        object.__setattr__(self, '_lock', lock)
        object.__setattr__(self, '_initialized', False)
        
        super().__init__()
        self.update(dict(*args, **kwargs))
        
        object.__setattr__(self, '_initialized', True)

    def __getattr__(self, key: str):
        if key.startswith('__') and key.endswith('__'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
            
        if key not in self:
            lock = object.__getattribute__(self, '_lock')
            if lock and object.__getattribute__(self, '_initialized'):
                raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")
            self[key] = Object(lock=lock)
        return self[key]

    def __setattr__(self, key: str, value):
        if key == '_lock':
            if getattr(self, '_initialized', False):
                raise TypeError("Cannot modify '_lock' after initialization")
            object.__setattr__(self, key, value)
        elif key == '_initialized':
            object.__setattr__(self, key, value)
        else:
            self[key] = value

    def __delattr__(self, key: str):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")

    def __getitem__(self, key):
        if key not in self:
            lock = object.__getattribute__(self, '_lock')
            if lock and object.__getattribute__(self, '_initialized'):
                raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")
            self[key] = Object(lock=lock)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        lock = object.__getattribute__(self, '_lock')
        if lock and getattr(self, '_initialized', True):
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")

        if isinstance(value, dict) and not isinstance(value, Object):
            value = Object(value, lock=lock)
        elif isinstance(value, list) and not isinstance(value, ObjectList):
            value = ObjectList(value, lock=lock)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        if object.__getattribute__(self, '_lock') and getattr(self, '_initialized', True):
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")
        super().__delitem__(key)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def set(self, path: str, value):
        """Sets a value at the specified path, creating nested Objects or ObjectLists as needed.

        Supports dot notation for dict keys and bracket notation with indices for list elements.

        Args:
            path (str): The dot-and-bracket path (e.g., 'a.b.list[0].c').
            value: The value to set at the path.

        Raises:
            TypeError: If the Object is locked or if the path encounters a non-container type.

        Example:
            >>> obj = Object()
            >>> obj.set("store.books[1].title", "Moby Dick")
            >>> obj.store.books[1].title
            'Moby Dick'
            >>> obj.store.books[0] is None
            True
        """
        tokens = _PATH_RE.findall(path)
        parsed_tokens = []
        for t in tokens:
            if t.startswith("[") and t.endswith("]"):
                parsed_tokens.append(int(t[1:-1]))
            else:
                parsed_tokens.append(t)
                
        if not parsed_tokens:
            return

        curr = self
        for i in range(len(parsed_tokens) - 1):
            token = parsed_tokens[i]
            next_token = parsed_tokens[i+1]
            
            node_type = ObjectList if isinstance(next_token, int) else Object
            
            if isinstance(curr, dict):
                if token not in curr:
                    curr[token] = node_type()
                curr = curr[token]
            elif isinstance(curr, list):
                while len(curr) <= token:
                    curr.append(Object() if isinstance(next_token, str) else ObjectList())
                if curr[token] is None:
                    curr[token] = node_type()
                curr = curr[token]
            else:
                raise TypeError(f"Cannot set property '{next_token}' on non-object '{token}'")

        last_token = parsed_tokens[-1]
        if isinstance(curr, dict):
            curr[last_token] = value
        elif isinstance(curr, list):
            while len(curr) <= last_token:
                curr.append(None)
            curr[last_token] = value

    def get(self, key, default=None):
        """Retrieves a value by key or dot-path. Supports JSONPath expressions if the key starts with '$'.

        Args:
            key (str): The key, dot-path (e.g., 'a.b[0].c'), or JSONPath expression (e.g., '$.store.book[*].price').
            default: The fallback value to return if the key/path is not found.

        Returns:
            The matched value, a list of matched values (for JSONPath), or the default value.

        Example:
            >>> obj = Object({"a": {"b": [{"c": 42}]}})
            >>> obj.get("a.b[0].c")
            42
            >>> obj.get("$.a.b[*].c")
            [42]
            >>> obj.get("nonexistent_key", "default_val")
            'default_val'
        """
        if isinstance(key, str):
            if key.startswith('$'):
                try:
                    from jsonpath_ng import parse
                    jsonpath_expr = parse(key)
                    matches = [match.value for match in jsonpath_expr.find(self)]
                    
                    if not matches:
                        return default
                    if len(matches) == 1:
                        return matches[0]
                    return matches
                except Exception:
                    return default
                    
            # Fast exact match first
            if key in self:
                return super().get(key, default)
                
            # Dot notation parsing
            if "." in key or "[" in key:
                tokens = _PATH_RE_NEG.findall(key)
                if not tokens:
                    return default
                    
                curr = self
                try:
                    for t in tokens:
                        if t.startswith("[") and t.endswith("]"):
                            curr = curr[int(t[1:-1])]
                        elif isinstance(curr, dict):
                            if t in curr:
                                curr = curr[t]
                            else:
                                return default
                        else:
                            return default
                    return curr
                except (KeyError, IndexError, TypeError):
                    return default

        return super().get(key, default)

    def __add__(self, other):
        """Merges this Object with another dictionary or Object and returns a new Object.

        Performs a deep merge, extending list items and recursively merging nested mappings.

        Args:
            other (dict): The dictionary or Object to merge with.

        Returns:
            Object: A new merged Object.

        Raises:
            TypeError: If this Object is locked, or other is not a dictionary.

        Example:
            >>> obj1 = Object({"a": {"x": 1}, "b": [1, 2]})
            >>> obj2 = {"a": {"y": 2}, "b": [3, 4]}
            >>> merged = obj1 + obj2
            >>> merged.to_dict()
            {'a': {'x': 1, 'y': 2}, 'b': [1, 2, 3, 4]}
        """
        if object.__getattribute__(self, '_lock'):
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be merged")
        if not isinstance(other, dict):
            return NotImplemented

        result = copy.deepcopy(self)
        
        def merge(target, source):
            for k, v in source.items():
                if k in target:
                    if isinstance(target[k], dict) and isinstance(v, dict):
                        merge(target[k], v)
                    elif isinstance(target[k], list) and isinstance(v, list):
                        # Use target[k].extend so ObjectList wraps new dicts
                        target[k].extend(copy.deepcopy(v))
                    else:
                        target[k] = copy.deepcopy(v)
                else:
                    target[k] = copy.deepcopy(v)
                    
        merge(result, other)
        return result

    def __or__(self, other):
        """Merges this Object with another dictionary or Object using the | operator.
        
        Acts identically to the + operator.
        """
        if not isinstance(other, dict):
            return NotImplemented
        return self.__add__(other)

    def __ror__(self, other):
        """Merges another dictionary with this Object using the | operator."""
        if not isinstance(other, dict):
            return NotImplemented
        return self.__class__(other) + self

    def __ior__(self, other):
        """In-place deep merge with another dictionary or Object using the |= operator."""
        if object.__getattribute__(self, '_lock'):
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be merged")
        if not isinstance(other, dict):
            return NotImplemented

        def merge(target, source):
            for k, v in source.items():
                if k in target:
                    if isinstance(target[k], dict) and isinstance(v, dict):
                        merge(target[k], v)
                    elif isinstance(target[k], list) and isinstance(v, list):
                        target[k].extend(copy.deepcopy(v))
                    else:
                        target[k] = copy.deepcopy(v)
                else:
                    target[k] = copy.deepcopy(v)
                    
        merge(self, other)
        return self

    def to_dict(self):
        """Recursively converts this Object and all nested Objects/ObjectLists to standard Python dicts and lists.

        Returns:
            dict: A standard Python dict representation of this Object.

        Example:
            >>> obj = Object(a=1, b={"c": 2})
            >>> type(obj.b)
            <class 'rich_object.object.Object'>
            >>> d = obj.to_dict()
            >>> type(d['b'])
            <class 'dict'>
        """
        def _convert(obj):
            if isinstance(obj, Object):
                return {k: _convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_convert(v) for v in obj]
            return obj
        return {k: _convert(v) for k, v in self.items()}


    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return repr(self.to_dict())
