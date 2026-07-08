import copy
import re

_PATH_RE_NEG = re.compile(r"[^.\[\]]+|\[-?\d+\]")

class DataTransformer:
    """Data transformation methods for Object."""

    def pick(self, *keys):
        """Creates a new Object containing ONLY the specified keys.
        
        Supports dot-notation paths to pick deeply nested properties while
        reconstructing their original structure.

        Args:
            *keys: One or more strings representing the keys or dot-paths to keep.

        Returns:
            Object: A new Object containing only the picked keys.

        Example:
            >>> obj = Object(user={"name": "Alice", "age": 30}, id=1)
            >>> obj.pick("user.name", "id").to_dict()
            {'user': {'name': 'Alice'}, 'id': 1}
        """
        new_obj = self.__class__()
        sentinel = object()
        
        for k in keys:
            # We rely on the Object's built-in get() and set() methods for dot-path support
            val = self.get(k, default=sentinel)
            if val is not sentinel:
                new_obj.set(k, copy.deepcopy(val))
                
        return new_obj

    def omit(self, *keys, deep=False):
        """Creates a new Object containing everything EXCEPT the specified keys.

        If `deep=False` (default), supports dot-notation paths to precisely omit
        nested properties.
        If `deep=True`, it recursively scrubs every matching key from the entire
        structure (perfect for removing passwords or PII). Dot-paths are ignored
        when `deep=True`—it strictly matches exact key names.

        Args:
            *keys: One or more strings representing the keys to omit.
            deep (bool): If True, recursively scrubs the keys from all nested dicts.

        Returns:
            Object: A new Object with the specified keys removed.

        Example:
            >>> obj = Object(user={"name": "Alice", "secret": "123"}, secret="456")
            >>> obj.omit("user.secret").to_dict()
            {'user': {'name': 'Alice'}, 'secret': '456'}
            
            >>> obj.omit("secret", deep=True).to_dict()
            {'user': {'name': 'Alice'}}
        """
        new_obj = copy.deepcopy(self)

        if deep:
            keys_set = set(keys)
            def _scrub(obj):
                if isinstance(obj, dict):
                    for k in list(obj.keys()):
                        if k in keys_set:
                            del obj[k]
                        else:
                            _scrub(obj[k])
                elif isinstance(obj, list):
                    for item in obj:
                        _scrub(item)
            _scrub(new_obj)
            return new_obj

        # Standard omit using dot-path traversal
        for k in keys:
            # Exact match override
            if k in new_obj:
                del new_obj[k]
                continue

            # Dot notation parsing
            tokens = _PATH_RE_NEG.findall(k)
            if not tokens:
                continue
                
            curr = new_obj
            try:
                # Traverse to the parent of the final token
                for i in range(len(tokens) - 1):
                    t = tokens[i]
                    if t.startswith("[") and t.endswith("]"):
                        curr = curr[int(t[1:-1])]
                    else:
                        curr = curr[t]
                
                # Delete the final token
                last = tokens[-1]
                if last.startswith("[") and last.endswith("]"):
                    del curr[int(last[1:-1])]
                else:
                    del curr[last]
            except (KeyError, IndexError, TypeError):
                # Path didn't exist in the structure, perfectly fine to ignore
                pass
                
        return new_obj
