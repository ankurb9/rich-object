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




