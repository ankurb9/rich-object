# rich-object

A powerful dictionary wrapper subclass that enables dot-notation attribute access, automatic nested path creation (autovivification), recursive locking, template rendering, JSONPath query resolution, deep structure diffing, and multi-format serialization (JSON, YAML, TOML).

## Table of Contents

- [1. Basic Usage & Dot Access](#1-basic-usage-dot-access)
- [2. Autovivification](#2-autovivification)
- [3. Schema Validation (`validate`)](#3-schema-validation-validate)
- [4. Structural Locks](#4-structural-locks)
- [5. Advanced Property Setting (`set`)](#5-advanced-property-setting-set)
- [6. Deep Path & JSONPath Querying (`get`)](#6-deep-path-jsonpath-querying-get)
- [7. Deep Merging (`+` and `|`)](#7-deep-merging-and-)
- [8. Data Transformation (`pick` and `omit`)](#8-data-transformation-pick-and-omit)
- [9. Template Rendering (`render`)](#9-template-rendering-render)
- [10. Structural Diffing (`diff`)](#10-structural-diffing-diff)
- [11. JSON Serialization](#11-json-serialization)
- [12. YAML Serialization](#12-yaml-serialization)
- [13. TOML Serialization](#13-toml-serialization)

## Installation

```bash
pip install rich-object
```

## Features & Examples

### 1. Basic Usage & Dot Access
Create an `Object` from mappings or keyword arguments and access properties with standard dot notation.
```python
from rich_object import Object

# Initialize using keywords or raw dictionaries
obj = Object(name="John", address={"city": "New York"})

print(obj.name)          # -> "John"
print(obj.address.city)  # -> "New York"
```

### 2. Autovivification
Missing nested directories/attributes are automatically initialized when accessed, resolving nested paths on the fly.
```python
obj = Object()
obj.user.profile.settings.theme = "dark"

print(obj.to_dict())
# -> {'user': {'profile': {'settings': {'theme': 'dark'}}}}
```

### 3. Schema Validation (`validate`)
Ensure your configuration or data matches strict rules using standard JSON Schema.
```python
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 18}
    },
    "required": ["name", "age"]
}

user = Object({"name": "Alice", "age": 30})

# Validates successfully (returns True)
user.validate(schema) 

# Raises jsonschema.exceptions.ValidationError
invalid_user = Object({"name": "Bob", "age": 15})
invalid_user.validate(schema)
```

### 4. Structural Locks
Prevent mutations (creation, updates, deletes) recursively across all nested dictionaries and lists by passing `lock=True`.
```python
frozen = Object({"items": [1, 2], "user": {"id": 42}}, lock=True)

# Any mutation throws a TypeError
try:
    frozen.user.id = 99
except TypeError as e:
    print(e)  # -> 'Object' is locked and cannot be modified

try:
    frozen.items.append(3)
except TypeError as e:
    print(e)  # -> 'ObjectList' is locked and cannot be modified
```

### 5. Advanced Property Setting (`set`)
Assign values safely to deeply nested paths using dot notation and bracket indices. Intermediary dictionary keys and list slots expand automatically.
```python
obj = Object()
obj.set("store.books[1].title", "Moby Dick")

print(obj.store.books[1].title)  # -> "Moby Dick"
print(obj.store.books[0])        # -> None (automatically padded slot)
```

### 6. Deep Path & JSONPath Querying (`get`)
Query the data structure dynamically using standard dot paths or JSONPath queries (starting with `$`).
```python
data = Object({
    "store": {
        "book": [
            {"category": "fiction", "price": 8.95},
            {"category": "reference", "price": 12.00}
        ]
    }
})

# Retrieve a single value using fast dot paths (no dependencies required)
print(data.get("store.book[0].category"))  # -> "fiction"

# Retrieve matching node value list using JSONPath
print(data.get("$..price"))                  # -> [8.95, 12.0]
```

### 7. Deep Merging (`+` and `|`)
Perform clean, recursive merges of two structures using the `+` operator or the Python 3.9+ `|` operator. Nested lists are automatically concatenated, and conflicting keys default to the right-hand value. In-place merges (`|=` or `+=`) are also supported.
```python
obj1 = Object({"a": {"x": 1}, "b": [1, 2]})
obj2 = Object({"a": {"y": 2}, "b": [3, 4]})

# Both operators do exactly the same thing
res = obj1 + obj2
res = obj1 | obj2

print(res.to_dict())
# -> {'a': {'x': 1, 'y': 2}, 'b': [1, 2, 3, 4]}

# In-place merge
obj1 |= obj2
```

### 8. Data Transformation (`pick` and `omit`)
Easily shape your data using dot-paths. `pick` keeps only what you need, and `omit` removes what you don't. 
```python
user = Object({
    "id": 101,
    "profile": {
        "name": "Alice",
        "email": "alice@example.com",
        "secret": "xyz123"
    }
})

# Keep only specific fields (reconstructs structure automatically)
public_user = user.pick("id", "profile.name")
# -> {'id': 101, 'profile': {'name': 'Alice'}}

# Omit specific fields
safe_user = user.omit("profile.secret")
# -> {'id': 101, 'profile': {'name': 'Alice', 'email': 'alice@example.com'}}
```

You can also use the `deep=True` flag with `omit()` to aggressively scrub a key from the entire nested structure. This is incredibly powerful for removing passwords or PII from giant API payloads:
```python
# Removes "password" from the top level, inside 'profile', inside arrays, etc.
scrubbed_data = data.omit("password", deep=True)
```

### 9. Template Rendering (`render`)
Render Jinja2 templates in all string values recursively across the entire structure. Because the object passes itself as context, it allows for seamless **self-referencing** (using other properties from the same object inside a template).
```python
obj = Object({
    "first_name": "Jane",
    "greeting": "Hello {{ first_name }}!",
    "matrix": [["Welcome {{ first_name }}"]]
})

rendered = obj.render()
print(rendered.greeting)  # -> "Hello Jane!"
print(rendered.matrix)    # -> [["Welcome Jane"]]
```

You can also pass entire modules or objects to the `render` method to use them inside your templates:
```python
import datetime

obj = Object({
    "year": "{{ dt.datetime(2026, 7, 6).year }}",
    "future_date": "{{ (dt.datetime(2026, 7, 6) + dt.timedelta(days=5)).strftime('%Y-%m-%d') }}"
})

res = obj.render(dt=datetime)
print(res.year)         # -> 2026
print(res.future_date)  # -> "2026-07-11"
```

### 10. Structural Diffing (`diff`)
Identify differences between two objects using the built-in DeepDiff interface.
```python
obj1 = Object({"a": 1, "b": 2})
obj2 = Object({"a": 1, "b": 3})

difference = obj1.diff(obj2)
print(difference)
# -> {'values_changed': {"root['b']": {'new_value': 3, 'old_value': 2}}}
```

### 11. JSON Serialization
Serialize to/from JSON strings and files. Uses the built-in `json` module — no extra dependencies.
```python
obj = Object(name="John", scores=[95, 87, 92])

# To JSON string
json_str = obj.to_json(indent=2)

# From JSON string
restored = Object.from_json('{"name": "John", "scores": [95, 87, 92]}')
print(restored.name)  # -> "John"

# File I/O
obj.to_json_file("config.json")
config = Object.from_json_file("config.json", lock=True)
```

### 12. YAML Serialization
Serialize to/from YAML strings and files. Requires `pyyaml` (`pip install rich-object[yaml]`).
```python
obj = Object(database={"host": "localhost", "port": 5432}, debug=True)

# To YAML string
print(obj.to_yaml())
# database:
#   host: localhost
#   port: 5432
# debug: true

# From YAML string
config = Object.from_yaml("database:\n  host: localhost\n  port: 5432")
print(config.database.host)  # -> "localhost"

# File I/O — one-liner config loading
config = Object.from_yaml_file("config.yaml", lock=True)
```

### 13. TOML Serialization
Serialize to/from TOML strings and files. Requires `tomli-w` for writing; uses built-in `tomllib` on Python 3.11+ for reading (`pip install rich-object[toml]`).
```python
obj = Object(title="My App", database={"host": "localhost", "port": 5432})

# To TOML string
print(obj.to_toml())
# title = "My App"
#
# [database]
# host = "localhost"
# port = 5432

# From TOML string
config = Object.from_toml('[database]\nhost = "localhost"\nport = 5432')
print(config.database.host)  # -> "localhost"

# File I/O
config = Object.from_toml_file("pyproject.toml", lock=True)
```
