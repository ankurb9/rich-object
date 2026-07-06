# rich-object

A powerful dictionary wrapper subclass that enables dot-notation attribute access, automatic nested path creation (autovivification), recursive locking, template rendering, JSONPath query resolution, and deep structure diffing.

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

### 3. Structural Locks
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

### 4. Advanced Property Setting (`set`)
Assign values safely to deeply nested paths using dot notation and bracket indices. Intermediary dictionary keys and list slots expand automatically.
```python
obj = Object()
obj.set("store.books[1].title", "Moby Dick")

print(obj.store.books[1].title)  # -> "Moby Dick"
print(obj.store.books[0])        # -> None (automatically padded slot)
```

### 5. JSONPath Querying (`get`)
Query the data structure dynamically by passing JSONPath queries starting with `$`.
```python
data = Object({
    "store": {
        "book": [
            {"category": "fiction", "price": 8.95},
            {"category": "reference", "price": 12.00}
        ]
    }
})

# Retrieve a single value
print(data.get("$.store.book[0].category"))  # -> "fiction"

# Retrieve matching node value list
print(data.get("$..price"))                  # -> [8.95, 12.0]
```

### 6. Deep Merging (`+`)
Perform clean, recursive merges of two structures using the `+` operator. Nested lists are automatically concatenated, and conflicting keys default to the right-hand value.
```python
obj1 = Object({"a": {"x": 1}, "b": [1, 2]})
obj2 = Object({"a": {"y": 2}, "b": [3, 4]})

res = obj1 + obj2
print(res.to_dict())
# -> {'a': {'x': 1, 'y': 2}, 'b': [1, 2, 3, 4]}
```

### 7. Template Rendering (`render`)
Render Jinja2 templates in all string values recursively across the entire structure (including nested dictionaries and lists).
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

### 8. Structural Diffing (`diff`)
Identify differences between two objects using the built-in DeepDiff interface.
```python
obj1 = Object({"a": 1, "b": 2})
obj2 = Object({"a": 1, "b": 3})

difference = obj1.diff(obj2)
print(difference)
# -> {'values_changed': {"root['b']": {'new_value': 3, 'old_value': 2}}}
```
