import json
import pytest
from rich_object.object import Object

def test_basic_initialization():
    # Kwargs
    obj1 = Object(a=1, b={"c": 2})
    assert obj1.a == 1
    assert obj1.b.c == 2
    assert isinstance(obj1.b, Object)
    
    # Plain dictionary
    obj2 = Object({"x": 10, "y": {"z": 20}})
    assert obj2.x == 10
    assert obj2.y.z == 20
    assert isinstance(obj2.y, Object)
    
    # Mix
    obj3 = Object({"m": 100}, n={"p": 200})
    assert obj3.m == 100
    assert obj3.n.p == 200

def test_autovivification():
    a = Object()
    
    # Missing path creation
    a.b.c = 'val'
    assert a.b.c == 'val'
    assert isinstance(a.b, Object)
    
    # Dict-like access
    a['d']['e'] = 42
    assert a.d.e == 42
    
    # List conversion
    a.f = [{"g": 1}]
    assert isinstance(a.f[0], Object)
    assert a.f[0].g == 1



def test_lock():
    frozen_obj = Object({"x": 10}, lock=True)
    
    with pytest.raises(TypeError):
        frozen_obj.y = 20  # Cannot create
        
    with pytest.raises(TypeError):
        frozen_obj.x = 99  # Cannot update
        
    with pytest.raises(TypeError):
        del frozen_obj.x  # Cannot delete



def test_dict_methods():
    a = Object(key1="val1")
    
    # .get() shouldn't autovivify
    assert a.get("key2", "default") == "default"
    assert "key2" not in a
    
    assert "key1" in a.keys()
    assert "val1" in a.values()

def test_get_jsonpath():
    data = Object({
        "store": {
            "book": [
                {"category": "fiction", "price": 8.95},
                {"category": "fiction", "price": 12.99}
            ],
            "bicycle": {
                "color": "red",
                "price": 19.95
            }
        },
        "val": 100
    })

    assert data.get("$.store.bicycle.color") == "red"
    assert data.get("$..price") == [8.95, 12.99, 19.95]
    assert data.get("$..author", "Not Found") == "Not Found"
    
    # Single element list handling
    data2 = Object({"store": {"book": [{"category": "reference"}]}})
    assert data2.get("$.store.book") == [{"category": "reference"}]
    assert data2.get("$..category") == "reference"

def test_get_dot_path():
    data = Object({
        "store": {
            "books": [
                {"title": "Book 1"},
                {"title": "Book 2"}
            ]
        },
        "a.b": 10,
        "a": {"b": 20}
    })
    
    # Exact match overrides dot-path
    assert data.get("a.b") == 10
    
    # Dot-path traversal
    assert data.get("store.books[0].title") == "Book 1"
    assert data.get("store.books[1].title") == "Book 2"
    
    # Missing paths should return default (or None)
    assert data.get("store.books[5].title", "Missing") == "Missing"
    assert data.get("store.shoes", "Missing") == "Missing"
    assert data.get("store.books[0].author", "Missing") == "Missing"
    
    # Out of bounds indexing
    assert data.get("store.books[-1].title") == "Book 2" # Python list indexing works
    
    # Invalid index (type error during parse, or string key in list)
    assert data.get("store.books.title", "Missing") == "Missing"

def test_add_operator():
    obj1 = Object({"a": {"x": 1}, "b": [1, 2], "mismatch": 10})
    obj2 = Object({"a": {"y": 2}, "b": [3, 4], "c": 3, "mismatch": [1, 2, 3]})
    
    res = obj1 + obj2
    
    # Check deep merge
    assert res.a.x == 1
    assert res.a.y == 2
    
    # Check list concatenation
    assert res.b == [1, 2, 3, 4]
    
    # Check new keys
    assert res.c == 3
    
    # Check type mismatch overwrite (right side wins)
    assert res.mismatch == [1, 2, 3]
    
    # Ensure it's a deep copy, not mutating original
    res.a.x = 99
    assert obj1.a.x == 1
    
    obj2.b.append(5)
    assert res.b == [1, 2, 3, 4]

def test_or_operator():
    obj1 = Object({"a": {"x": 1}, "b": [1, 2]})
    obj2 = Object({"a": {"y": 2}, "b": [3, 4]})
    
    # __or__
    res = obj1 | obj2
    assert res.a.x == 1
    assert res.a.y == 2
    assert res.b == [1, 2, 3, 4]
    assert isinstance(res, Object)
    
    # __ror__ (dict | Object)
    dict_val = {"a": {"z": 3}, "b": [5]}
    res2 = dict_val | obj1
    assert res2.a.z == 3
    assert res2.a.x == 1
    assert res2.b == [5, 1, 2]
    assert isinstance(res2, Object)
    
    # __ior__ (in-place)
    obj3 = Object({"a": {"x": 1}, "b": [1, 2]})
    obj3 |= obj2
    assert obj3.a.x == 1
    assert obj3.a.y == 2
    assert obj3.b == [1, 2, 3, 4]

def test_pick():
    data = Object({
        "id": 1,
        "user": {
            "firstname": "Alice",
            "lastname": "Smith",
            "secret": "hidden"
        },
        "role": "admin"
    })
    
    # Single key
    res = data.pick("id")
    assert res.to_dict() == {"id": 1}
    assert isinstance(res, Object)
    
    # Multiple and nested dot paths
    res2 = data.pick("role", "user.firstname")
    assert res2.to_dict() == {"role": "admin", "user": {"firstname": "Alice"}}
    
    # Missing paths are ignored
    res3 = data.pick("nonexistent", "user.nonexistent")
    assert res3.to_dict() == {}

def test_omit():
    data = Object({
        "id": 1,
        "password": "abc",
        "user": {
            "firstname": "Alice",
            "lastname": "Smith",
            "password": "xyz"
        },
        "users_list": [
            {"name": "Bob", "password": "123"},
            {"name": "Eve"}
        ]
    })
    
    # Exact top-level key omit
    res = data.omit("password")
    assert "password" not in res
    assert "password" in res.user # Nested is untouched
    assert "password" in res.users_list[0]
    
    # Dot-path omit
    res2 = data.omit("user.password")
    assert "password" in res2 # Top level untouched
    assert "password" not in res2.user
    
    # Deep omit scrub
    res3 = data.omit("password", deep=True)
    assert "password" not in res3
    assert "password" not in res3.user
    assert "password" not in res3.users_list[0]
    assert res3.users_list[0].name == "Bob"
    assert res3.id == 1
    
    # Missing path ignore
    res4 = data.omit("nonexistent", "user.nonexistent")
    assert res4.to_dict() == data.to_dict()

def test_validate():
    import pytest
    
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")
        
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0}
        },
        "required": ["name", "age"]
    }
    
    # Valid object
    valid_obj = Object({"name": "Alice", "age": 30})
    assert valid_obj.validate(schema) is True
    
    # Invalid object (missing required field)
    invalid_obj1 = Object({"name": "Bob"})
    with pytest.raises(jsonschema.exceptions.ValidationError):
        invalid_obj1.validate(schema)
        
    # Invalid object (wrong type)
    invalid_obj2 = Object({"name": "Charlie", "age": "thirty"})
    with pytest.raises(jsonschema.exceptions.ValidationError):
        invalid_obj2.validate(schema)
        
    # Invalid schema itself
    invalid_schema = {"type": "invalid_type"}
    with pytest.raises(jsonschema.exceptions.SchemaError):
        valid_obj.validate(invalid_schema)

def test_render():
    obj = Object({
        "first_name": "John",
        "last_name": "Doe",
        "address": {
            "city": "New York"
        },
        "greeting": "Hello {{ first_name }} {{ last_name }}",
        "missing": "Hello {{ missing_var }}",
        "nested_greeting": "Welcome to {{ address.city }}!",
        "messages": ["Hi {{ first_name }}", "Bye {{ first_name }}"],
        "mixed_vars": "Where is {{ missing_var }} for {{ first_name }}?"
    })
    
    res = obj.render()
    
    assert res.greeting == "Hello John Doe"
    assert res.missing == "Hello {{ missing_var }}"
    assert res.nested_greeting == "Welcome to New York!"
    assert res.messages == ["Hi John", "Bye John"]
    assert res.mixed_vars == "Where is {{ missing_var }} for John?"
    
    # Ensure deep copy
    assert obj.greeting == "Hello {{ first_name }} {{ last_name }}"
    res.address.city = "LA"
    assert obj.address.city == "New York"
    
    # Test custom variables via kwargs
    res_custom = obj.render(first_name="Jane", missing_var="World", extra="!")
    assert res_custom.greeting == "Hello Jane Doe"  # Overridden value
    assert res_custom.missing == "Hello World"      # Provided value
    assert res_custom.mixed_vars == "Where is World for Jane?"
    
    # Test primitive rendering and filters
    obj_prim = Object({
        "num": "{{ 10 | int }}",
        "bool_val": "{{ true | bool }}",
        "list_val": "{{ [1, 2, 3] | list }}",
        "mixed": "I have {{ 10 | int }} apples"
    })
    res_prim = obj_prim.render()
    assert res_prim.num == 10
    assert res_prim.bool_val is True
    assert res_prim.list_val == [1, 2, 3]
    assert res_prim.mixed == "I have 10 apples"


def test_set_path():
    # Deep path creation
    val = Object()
    val.set("a.b.c.d", "val1")
    assert val.a.b.c.d == "val1"
    
    # Array creation inside a path
    val2 = Object()
    val2.set("a.b.list[0].c", "val2")
    assert isinstance(val2.a.b.list, list)
    assert val2.a.b.list[0].c == "val2"
    
    # Array expansion
    val3 = Object()
    val3.set("a.b.list[2].d", "val3")
    assert len(val3.a.b.list) == 3
    assert val3.a.b.list[0] is not None
    assert val3.a.b.list[1] is not None
    assert val3.a.b.list[2].d == "val3"

def test_list_lock():
    frozen_obj = Object({"my_list": [1, 2, 3]}, lock=True)
    with pytest.raises(TypeError):
        frozen_obj.my_list.append(4)
    with pytest.raises(TypeError):
        frozen_obj.my_list[0] = 99
    with pytest.raises(TypeError):
        del frozen_obj.my_list[1]
    with pytest.raises(TypeError):
        frozen_obj.my_list += [4]
        
def test_set_lock_respect():
    frozen_obj = Object({"x": {"y": 1}}, lock=True)
    with pytest.raises(TypeError):
        frozen_obj.set("x.y", 999)
    with pytest.raises(TypeError):
        frozen_obj.set("z", 100)

def test_render_nested_lists():
    obj = Object({
        "matrix": [["{{ x }}", "plain"], ["{{ y }}"]],
        "deep": [{"nested_list": ["{{ z }}"]}]
    })
    res = obj.render(x="A", y="B", z="C")
    assert res.matrix[0][0] == "A"
    assert res.matrix[0][1] == "plain"
    assert res.matrix[1][0] == "B"
    assert res.deep[0].nested_list[0] == "C"


# ── JSON Tests ──────────────────────────────────────────────────

def test_to_json():
    obj = Object(name="John", age=30, address={"city": "NYC"})
    result = json.loads(obj.to_json())
    assert result["name"] == "John"
    assert result["age"] == 30
    assert result["address"]["city"] == "NYC"

def test_to_json_formatting():
    obj = Object(b=2, a=1)
    # sort_keys
    assert '"a": 1' in obj.to_json(sort_keys=True)
    # indent
    pretty = obj.to_json(indent=4)
    assert "\n" in pretty

def test_from_json():
    obj = Object.from_json('{"name": "Jane", "scores": [10, 20]}')
    assert obj.name == "Jane"
    assert obj.scores == [10, 20]
    assert isinstance(obj, Object)

def test_from_json_locked():
    obj = Object.from_json('{"x": 1}', lock=True)
    assert obj.x == 1
    with pytest.raises(TypeError):
        obj.x = 2

def test_json_file_roundtrip(tmp_path):
    path = str(tmp_path / "test.json")
    original = Object(users=[{"name": "Alice"}, {"name": "Bob"}], count=2)
    original.to_json_file(path)

    loaded = Object.from_json_file(path)
    assert loaded.count == 2
    assert loaded.users[0].name == "Alice"
    assert loaded.users[1].name == "Bob"

def test_json_file_locked(tmp_path):
    path = str(tmp_path / "locked.json")
    Object(val=42).to_json_file(path)
    locked = Object.from_json_file(path, lock=True)
    assert locked.val == 42
    with pytest.raises(TypeError):
        locked.val = 99


# ── YAML Tests ──────────────────────────────────────────────────

def test_to_yaml():
    obj = Object(name="John", items=[1, 2, 3])
    yaml_str = obj.to_yaml()
    assert "name: John" in yaml_str
    assert "items:" in yaml_str

def test_from_yaml():
    yaml_str = "name: Jane\nage: 25\nskills:\n  - python\n  - rust"
    obj = Object.from_yaml(yaml_str)
    assert obj.name == "Jane"
    assert obj.age == 25
    assert obj.skills == ["python", "rust"]

def test_from_yaml_locked():
    obj = Object.from_yaml("x: 10", lock=True)
    assert obj.x == 10
    with pytest.raises(TypeError):
        obj.x = 20

def test_yaml_file_roundtrip(tmp_path):
    path = str(tmp_path / "config.yaml")
    original = Object(database={"host": "localhost", "port": 5432}, debug=True)
    original.to_yaml_file(path)

    loaded = Object.from_yaml_file(path)
    assert loaded.database.host == "localhost"
    assert loaded.database.port == 5432
    assert loaded.debug is True

def test_yaml_file_locked(tmp_path):
    path = str(tmp_path / "locked.yaml")
    Object(key="value").to_yaml_file(path)
    locked = Object.from_yaml_file(path, lock=True)
    assert locked.key == "value"
    with pytest.raises(TypeError):
        locked.key = "changed"

def test_yaml_roundtrip_nested():
    original = Object(a={"b": {"c": [1, 2, {"d": 3}]}})
    yaml_str = original.to_yaml()
    restored = Object.from_yaml(yaml_str)
    assert restored.a.b.c[2]["d"] == 3


# ── TOML Tests ──────────────────────────────────────────────────

def test_to_toml():
    obj = Object(name="John", age=30)
    toml_str = obj.to_toml()
    assert 'name = "John"' in toml_str
    assert "age = 30" in toml_str

def test_from_toml():
    toml_str = 'name = "Jane"\nage = 25\n\n[database]\nhost = "localhost"\nport = 5432'
    obj = Object.from_toml(toml_str)
    assert obj.name == "Jane"
    assert obj.age == 25
    assert obj.database.host == "localhost"
    assert obj.database.port == 5432

def test_from_toml_locked():
    obj = Object.from_toml('x = 10', lock=True)
    assert obj.x == 10
    with pytest.raises(TypeError):
        obj.x = 20

def test_toml_file_roundtrip(tmp_path):
    path = str(tmp_path / "config.toml")
    original = Object(title="My App", database={"host": "localhost", "port": 5432})
    original.to_toml_file(path)

    loaded = Object.from_toml_file(path)
    assert loaded.title == "My App"
    assert loaded.database.host == "localhost"
    assert loaded.database.port == 5432

def test_toml_file_locked(tmp_path):
    path = str(tmp_path / "locked.toml")
    Object(key="value").to_toml_file(path)
    locked = Object.from_toml_file(path, lock=True)
    assert locked.key == "value"
    with pytest.raises(TypeError):
        locked.key = "changed"




