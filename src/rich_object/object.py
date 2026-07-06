import copy
import json
import re

class ObjectList(list):
    """A list subclass that respects lock state and auto-wraps dicts into Objects."""
    def __init__(self, iterable=(), lock=False):
        self._lock = False
        super().__init__()
        for item in iterable:
            self.append(item)
        self._lock = lock

    def _check_lock(self):
        if getattr(self, '_lock', False):
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


class Object(dict):
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
            if object.__getattribute__(self, '_lock') and object.__getattribute__(self, '_initialized'):
                raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")
                
            lock_val = object.__getattribute__(self, '_lock')
            self[key] = Object(lock=lock_val)
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
            if object.__getattribute__(self, '_lock') and object.__getattribute__(self, '_initialized'):
                raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")
                
            lock_val = object.__getattribute__(self, '_lock')
            self[key] = Object(lock=lock_val)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if object.__getattribute__(self, '_lock') and getattr(self, '_initialized', True):
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be modified")

        lock_val = object.__getattribute__(self, '_lock')

        if isinstance(value, dict) and not isinstance(value, Object):
            value = Object(value, lock=lock_val)
        elif isinstance(value, list) and not isinstance(value, ObjectList):
            value = ObjectList(value, lock=lock_val)
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
        tokens = re.findall(r"[^.\[\]]+|\[\d+\]", path)
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
        """Retrieves a value by key. Supports JSONPath expressions if the key starts with '$'.

        Args:
            key (str): The key or JSONPath expression (e.g., '$.store.book[*].price').
            default: The fallback value to return if the key/path is not found.

        Returns:
            The matched value, a list of matched values (for JSONPath), or the default value.

        Example:
            >>> obj = Object({"store": {"book": [{"price": 10}, {"price": 15}]}})
            >>> obj.get("$.store.book[*].price")
            [10, 15]
            >>> obj.get("nonexistent_key", "default_val")
            'default_val'
        """
        if isinstance(key, str) and key.startswith('$'):
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

    def render(self, **kwargs):
        """Renders Jinja2 templates in all string values recursively across the entire structure.

        Args:
            **kwargs: Additional context variables passed to the Jinja template rendering environment.

        Returns:
            Object: A copy of this Object with all template variables rendered.

        Raises:
            TypeError: If this Object is locked.
            ImportError: If the 'jinja2' package is not installed.

        Example:
            >>> obj = Object({"greeting": "Hello {{ name }}!"})
            >>> rendered = obj.render(name="World")
            >>> rendered.greeting
            'Hello World!'
        """
        if object.__getattribute__(self, '_lock'):
            raise TypeError(f"'{self.__class__.__name__}' is locked and cannot be rendered")
        try:
            from jinja2.nativetypes import NativeEnvironment
            from jinja2 import DebugUndefined
        except ImportError:
            raise ImportError("jinja2 is required to use the render() method. Install it with 'pip install jinja2'")
            
        env = NativeEnvironment(undefined=DebugUndefined)
        
        def parse_bool(val):
            if isinstance(val, str):
                return val.lower() in ('true', '1', 't', 'yes', 'y')
            return bool(val)
            
        env.filters['bool'] = parse_bool
        env.filters['Object'] = Object
        
        env.filters['str'] = lambda val: json.dumps(val) if isinstance(val, (dict, list)) else str(val)
        
        env.globals['true'] = True
        env.globals['false'] = False
        env.globals['null'] = None
        env.globals['Object'] = Object
        
        context = self.to_dict()
        context.update(kwargs)
        
        result = copy.deepcopy(self)
        
        def traverse_item(item):
            if isinstance(item, str):
                try:
                    template = env.from_string(item)
                    return template.render(**context)
                except Exception:
                    return item
            elif isinstance(item, dict):
                for k, v in item.items():
                    item[k] = traverse_item(v)
                return item
            elif isinstance(item, list):
                for i in range(len(item)):
                    item[i] = traverse_item(item[i])
                return item
            return item

        for k, v in result.items():
            result[k] = traverse_item(v)
            
        return result

    def diff(
        self,
        other,
        ignore_order=False,
        ignore_string_case=False,
        exclude_paths=None,
        exclude_regex_paths=None,
        exclude_types=None,
        include_paths=None,
        significant_digits=None,
        math_epsilon=None,
        ignore_numeric_type_changes=False,
        ignore_type_in_groups=None,
        ignore_type_subclasses=False,
        ignore_string_type_changes=False,
        ignore_nan_inequality=False,
        ignore_encoding_errors=False,
        ignore_private_variables=True,
        truncate_datetime=None,
        cutoff_distance_for_pairs=0.3,
        cutoff_intersection_for_pairs=0.7,
        cache_size=0,
        cache_purge_level=1,
        log_frequency_in_sec=0,
        max_passes=10000000,
        max_diffs=None,
        verbose_level=1,
        view="text",
        **kwargs
    ):
        """Computes the difference between this Object and another object using DeepDiff.

        Args:
            other: The other object or dictionary to compare against.
            ignore_order (bool): See DeepDiff documentation.
            ignore_string_case (bool): See DeepDiff documentation.
            exclude_paths (list/set): See DeepDiff documentation.
            exclude_regex_paths (list/set): See DeepDiff documentation.
            exclude_types (list/set): See DeepDiff documentation.
            include_paths (list/set): See DeepDiff documentation.
            significant_digits (int): See DeepDiff documentation.
            math_epsilon (float): See DeepDiff documentation.
            ignore_numeric_type_changes (bool): See DeepDiff documentation.
            ignore_type_in_groups: See DeepDiff documentation.
            ignore_type_subclasses (bool): See DeepDiff documentation.
            ignore_string_type_changes (bool): See DeepDiff documentation.
            ignore_nan_inequality (bool): See DeepDiff documentation.
            ignore_encoding_errors (bool): See DeepDiff documentation.
            ignore_private_variables (bool): See DeepDiff documentation.
            truncate_datetime: See DeepDiff documentation.
            cutoff_distance_for_pairs (float): See DeepDiff documentation.
            cutoff_intersection_for_pairs (float): See DeepDiff documentation.
            cache_size (int): See DeepDiff documentation.
            cache_purge_level (int): See DeepDiff documentation.
            log_frequency_in_sec (int): See DeepDiff documentation.
            max_passes (int): See DeepDiff documentation.
            max_diffs (int): See DeepDiff documentation.
            verbose_level (int): See DeepDiff documentation.
            view (str): See DeepDiff documentation.
            **kwargs: Additional keyword arguments passed directly to DeepDiff.

        Returns:
            DeepDiff: The resulting comparison object.

        Raises:
            ImportError: If the 'deepdiff' package is not installed.

        Example:
            >>> obj1 = Object({"a": 1})
            >>> obj2 = {"a": 2}
            >>> diff = obj1.diff(obj2)
            >>> 'values_changed' in diff
            True
        """
        try:
            from deepdiff import DeepDiff
        except ImportError:
            raise ImportError("deepdiff is required to use the diff() method. Install it with pip install deepdiff")
            
        kwargs.update({
            "ignore_order": ignore_order,
            "ignore_string_case": ignore_string_case,
            "exclude_paths": exclude_paths,
            "exclude_regex_paths": exclude_regex_paths,
            "exclude_types": exclude_types,
            "include_paths": include_paths,
            "significant_digits": significant_digits,
            "math_epsilon": math_epsilon,
            "ignore_numeric_type_changes": ignore_numeric_type_changes,
            "ignore_type_in_groups": ignore_type_in_groups,
            "ignore_type_subclasses": ignore_type_subclasses,
            "ignore_string_type_changes": ignore_string_type_changes,
            "ignore_nan_inequality": ignore_nan_inequality,
            "ignore_encoding_errors": ignore_encoding_errors,
            "ignore_private_variables": ignore_private_variables,
            "truncate_datetime": truncate_datetime,
            "cutoff_distance_for_pairs": cutoff_distance_for_pairs,
            "cutoff_intersection_for_pairs": cutoff_intersection_for_pairs,
            "cache_size": cache_size,
            "cache_purge_level": cache_purge_level,
            "log_frequency_in_sec": log_frequency_in_sec,
            "max_passes": max_passes,
            "max_diffs": max_diffs,
            "verbose_level": verbose_level,
            "view": view,
        })
        
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
        return DeepDiff(
            self.to_dict(),
            other.to_dict() if hasattr(other, "to_dict") else other,
            **kwargs
        )



    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return repr(self.to_dict())
