import copy
import json

class TemplateRenderer:
    """Jinja2 template rendering capabilities for Object."""

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

            >>> # Using filters like 'int' and 'str'
            >>> obj = Object({
            ...     "number": "{{ '42' | int }}",
            ...     "serialized_list": "{{ [1, 2, 3] | str }}",
            ...     "serialized_dict": "{{ {'a': 1} | str }}"
            ... })
            >>> res = obj.render()
            >>> res.number
            42
            >>> res.serialized_list
            '[1, 2, 3]'

            >>> # Passing helper objects like a faker instance or datetime
            >>> from datetime import datetime
            >>> class MockFaker:
            ...     def name(self): return "Alice Smith"
            ...
            >>> obj = Object({
            ...     "username": "{{ fake.name() }}",
            ...     "created_year": "{{ now.strftime('%Y') }}"
            ... })
            >>> res = obj.render(fake=MockFaker(), now=datetime(2026, 7, 6))
            >>> res.username
            'Alice Smith'
            >>> res.created_year
            '2026'

            >>> # Passing entire modules
            >>> import datetime
            >>> obj = Object({
            ...     "year": "{{ dt.datetime(2026, 7, 6).year }}",
            ...     "future_date": "{{ (dt.datetime(2026, 7, 6) + dt.timedelta(days=5)).strftime('%Y-%m-%d') }}"
            ... })
            >>> res = obj.render(dt=datetime)
            >>> res.year
            2026
            >>> res.future_date
            '2026-07-11'
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
        env.filters['Object'] = self.__class__
        
        env.filters['str'] = lambda val: json.dumps(val) if isinstance(val, (dict, list)) else str(val)
        
        env.globals['true'] = True
        env.globals['false'] = False
        env.globals['null'] = None
        env.globals['Object'] = self.__class__
        
        # self.to_dict() is expected to be provided by the inheriting class
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
