from __future__ import annotations

import json


class JsonSerializer:
    """JSON serialization methods for Object."""

    def to_json(self, indent=None, sort_keys=False, **kwargs):
        """Serializes this Object to a JSON string.
        
        If `orjson` is installed, it is used for high-performance serialization.

        Args:
            indent (int, optional): Number of spaces for indentation. None for compact output.
            sort_keys (bool): If True, output keys in sorted order.
            **kwargs: Additional keyword arguments passed to json.dumps (or orjson.dumps).

        Returns:
            str: A JSON string representation.

        Example:
            >>> obj = Object(name="John", age=30)
            >>> obj.to_json()
            '{"name": "John", "age": 30}'
        """
        try:
            import orjson
            option = 0
            if indent == 2:
                option |= orjson.OPT_INDENT_2
            if sort_keys:
                option |= orjson.OPT_SORT_KEYS
            if "option" in kwargs:
                option |= kwargs.pop("option")
            return orjson.dumps(self.to_dict(), option=option, **kwargs).decode("utf-8")
        except ImportError:
            return json.dumps(self.to_dict(), indent=indent, sort_keys=sort_keys, **kwargs)

    def to_json_file(self, path, indent=2, sort_keys=False, **kwargs):
        """Serializes this Object and writes it to a JSON file.
        
        If `orjson` is installed, it is used for high-performance serialization.

        Args:
            path (str): File path to write to.
            indent (int): Number of spaces for indentation. Defaults to 2.
            sort_keys (bool): If True, output keys in sorted order.
            **kwargs: Additional keyword arguments passed to json.dump (or orjson.dumps).

        Example:
            >>> obj = Object(name="John")
            >>> obj.to_json_file("config.json")
        """
        try:
            import orjson
            option = 0
            if indent == 2:
                option |= orjson.OPT_INDENT_2
            if sort_keys:
                option |= orjson.OPT_SORT_KEYS
            if "option" in kwargs:
                option |= kwargs.pop("option")
            with open(path, 'wb') as f:
                f.write(orjson.dumps(self.to_dict(), option=option, **kwargs))
        except ImportError:
            with open(path, 'w') as f:
                json.dump(self.to_dict(), f, indent=indent, sort_keys=sort_keys, **kwargs)

    @classmethod
    def from_json(cls, string, lock=False):
        """Creates an Object from a JSON string.
        
        If `orjson` is installed, it is used for high-performance deserialization.

        Args:
            string (str): A JSON-formatted string.
            lock (bool): If True, the resulting Object will be locked.

        Returns:
            Object: A new Object instance.

        Example:
            >>> obj = Object.from_json('{"name": "John", "age": 30}')
            >>> obj.name
            'John'
        """
        try:
            import orjson
            return cls(orjson.loads(string), lock=lock)  # type: ignore[call-arg]
        except ImportError:
            return cls(json.loads(string), lock=lock)  # type: ignore[call-arg]

    @classmethod
    def from_json_file(cls, path, lock=False):
        """Creates an Object from a JSON file.
        
        If `orjson` is installed, it is used for high-performance deserialization.

        Args:
            path (str): Path to the JSON file.
            lock (bool): If True, the resulting Object will be locked.

        Returns:
            Object: A new Object instance.

        Example:
            >>> obj = Object.from_json_file("config.json")
        """
        try:
            import orjson
            with open(path, 'rb') as f:
                return cls(orjson.loads(f.read()), lock=lock)  # type: ignore[call-arg]
        except ImportError:
            with open(path, 'r') as f:
                return cls(json.load(f), lock=lock)  # type: ignore[call-arg]


class YamlSerializer:
    """YAML serialization methods for Object."""

    def to_yaml(self, default_flow_style=False, **kwargs):
        """Serializes this Object to a YAML string.

        Requires the ``pyyaml`` package.

        Args:
            default_flow_style (bool): If True, uses inline/flow style.
                Defaults to False (block style).
            **kwargs: Additional keyword arguments passed to yaml.dump.

        Returns:
            str: A YAML string representation.

        Raises:
            ImportError: If the 'pyyaml' package is not installed.

        Example:
            >>> obj = Object(name="John", age=30)
            >>> print(obj.to_yaml())
            age: 30
            name: John
            <BLANKLINE>
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("pyyaml is required to use YAML methods. Install it with 'pip install pyyaml'")
        return yaml.dump(self.to_dict(), default_flow_style=default_flow_style, **kwargs)

    def to_yaml_file(self, path, default_flow_style=False, **kwargs):
        """Serializes this Object and writes it to a YAML file.

        Requires the ``pyyaml`` package.

        Args:
            path (str): File path to write to.
            default_flow_style (bool): If True, uses inline/flow style.
                Defaults to False (block style).
            **kwargs: Additional keyword arguments passed to yaml.dump.

        Raises:
            ImportError: If the 'pyyaml' package is not installed.

        Example:
            >>> obj = Object(name="John")
            >>> obj.to_yaml_file("config.yaml")
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("pyyaml is required to use YAML methods. Install it with 'pip install pyyaml'")
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=default_flow_style, **kwargs)

    @classmethod
    def from_yaml(cls, string, lock=False):
        """Creates an Object from a YAML string.

        Requires the ``pyyaml`` package.

        Args:
            string (str): A YAML-formatted string.
            lock (bool): If True, the resulting Object will be locked.

        Returns:
            Object: A new Object instance.

        Raises:
            ImportError: If the 'pyyaml' package is not installed.

        Example:
            >>> obj = Object.from_yaml("name: John\\nage: 30")
            >>> obj.name
            'John'
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("pyyaml is required to use YAML methods. Install it with 'pip install pyyaml'")
        return cls(yaml.safe_load(string), lock=lock)  # type: ignore[call-arg]

    @classmethod
    def from_yaml_file(cls, path, lock=False):
        """Creates an Object from a YAML file.

        Requires the ``pyyaml`` package.

        Args:
            path (str): Path to the YAML file.
            lock (bool): If True, the resulting Object will be locked.

        Returns:
            Object: A new Object instance.

        Raises:
            ImportError: If the 'pyyaml' package is not installed.

        Example:
            >>> config = Object.from_yaml_file("config.yaml", lock=True)
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("pyyaml is required to use YAML methods. Install it with 'pip install pyyaml'")
        with open(path, 'r') as f:
            return cls(yaml.safe_load(f), lock=lock)  # type: ignore[call-arg]


class TomlSerializer:
    """TOML serialization methods for Object."""

    def to_toml(self, **kwargs):
        """Serializes this Object to a TOML string.

        Requires the ``tomli-w`` package.

        Args:
            **kwargs: Additional keyword arguments passed to tomli_w.dumps.

        Returns:
            str: A TOML string representation.

        Raises:
            ImportError: If the 'tomli-w' package is not installed.

        Example:
            >>> obj = Object(name="John", age=30)
            >>> print(obj.to_toml())
            name = "John"
            age = 30
            <BLANKLINE>
        """
        try:
            import tomli_w
        except ImportError:
            raise ImportError("tomli-w is required to write TOML. Install it with 'pip install tomli-w'")
        return tomli_w.dumps(self.to_dict(), **kwargs)

    def to_toml_file(self, path, **kwargs):
        """Serializes this Object and writes it to a TOML file.

        Requires the ``tomli-w`` package.

        Args:
            path (str): File path to write to.
            **kwargs: Additional keyword arguments passed to tomli_w.dump.

        Raises:
            ImportError: If the 'tomli-w' package is not installed.

        Example:
            >>> obj = Object(name="John")
            >>> obj.to_toml_file("config.toml")
        """
        try:
            import tomli_w
        except ImportError:
            raise ImportError("tomli-w is required to write TOML. Install it with 'pip install tomli-w'")
        with open(path, 'wb') as f:
            tomli_w.dump(self.to_dict(), f, **kwargs)

    @classmethod
    def from_toml(cls, string, lock=False):
        """Creates an Object from a TOML string.

        Uses ``tomllib`` (Python 3.11+) or the ``tomli`` backport.

        Args:
            string (str): A TOML-formatted string.
            lock (bool): If True, the resulting Object will be locked.

        Returns:
            Object: A new Object instance.

        Raises:
            ImportError: If neither tomllib nor tomli is available.

        Example:
            >>> obj = Object.from_toml('name = \"John\"\\nage = 30')
            >>> obj.name
            'John'
        """
        try:
            import tomllib
        except ModuleNotFoundError:
            try:
                import tomli as tomllib
            except ImportError:
                raise ImportError(
                    "tomli is required for Python < 3.11 to read TOML. "
                    "Install it with 'pip install tomli'"
                )
        return cls(tomllib.loads(string), lock=lock)  # type: ignore[call-arg]

    @classmethod
    def from_toml_file(cls, path, lock=False):
        """Creates an Object from a TOML file.

        Uses ``tomllib`` (Python 3.11+) or the ``tomli`` backport.

        Args:
            path (str): Path to the TOML file.
            lock (bool): If True, the resulting Object will be locked.

        Returns:
            Object: A new Object instance.

        Raises:
            ImportError: If neither tomllib nor tomli is available.

        Example:
            >>> config = Object.from_toml_file("pyproject.toml", lock=True)
        """
        try:
            import tomllib
        except ModuleNotFoundError:
            try:
                import tomli as tomllib
            except ImportError:
                raise ImportError(
                    "tomli is required for Python < 3.11 to read TOML. "
                    "Install it with 'pip install tomli'"
                )
        with open(path, 'rb') as f:
            return cls(tomllib.load(f), lock=lock)  # type: ignore[call-arg]
