from rich_object.object import Object
frozen_obj = Object({"x": {"y": 1}}, lock=True)
print(frozen_obj._lock)
print(frozen_obj.x._lock)
try:
    frozen_obj.set("x.y", 999)
    print("DID NOT RAISE")
except Exception as e:
    print(f"RAISED: {type(e)} {e}")

obj1 = Object({"a": 1})
dict1 = {"a": 1}
print(f"obj1 == dict1: {obj1 == dict1}")
print(f"obj1 != dict1: {obj1 != dict1}")
