"""Schema fingerprint tests — these are the most important correctness checks
in the whole codebase. A wrong fingerprint causes false-positive drift alerts."""

from toolpulse.schema_hash import fingerprint, extract_shape, shape_diff


def test_same_shape_same_fingerprint():
    a = {"name": "Alice", "age": 30, "tags": ["admin"]}
    b = {"name": "Bob", "age": 99, "tags": ["user", "beta"]}
    assert fingerprint(a) == fingerprint(b)


def test_different_keys_different_fingerprint():
    a = {"name": "Alice", "age": 30}
    b = {"name": "Alice", "email": "a@b.com"}
    assert fingerprint(a) != fingerprint(b)


def test_different_value_types_different_fingerprint():
    a = {"id": 123}
    b = {"id": "abc"}
    assert fingerprint(a) != fingerprint(b)


def test_key_order_doesnt_matter():
    a = {"a": 1, "b": 2, "c": 3}
    b = {"c": 3, "a": 1, "b": 2}
    assert fingerprint(a) == fingerprint(b)


def test_nested_structures():
    a = {"users": [{"id": 1, "name": "x"}]}
    b = {"users": [{"id": 99, "name": "y"}, {"id": 100, "name": "z"}]}
    assert fingerprint(a) == fingerprint(b)


def test_empty_list_distinct_from_populated():
    a = {"items": []}
    b = {"items": [{"id": 1}]}
    assert fingerprint(a) != fingerprint(b)


def test_none_value():
    a = {"x": None}
    b = {"x": "string"}
    assert fingerprint(a) != fingerprint(b)


def test_bool_vs_int_distinct():
    # bool is a subclass of int — make sure we treat them as distinct
    assert fingerprint({"x": True}) != fingerprint({"x": 1})


def test_heterogeneous_list_merging():
    # First element doesn't represent the rest — fingerprint must reflect both
    a = [{"id": 1}, {"id": 2, "extra": "x"}]
    b = [{"id": 5, "extra": "y"}, {"id": 6}]
    # Both lists have the same merged shape (id always, extra optional)
    assert fingerprint(a) == fingerprint(b)


def test_shape_diff_added_field():
    old = extract_shape({"id": 1})
    new = extract_shape({"id": 1, "name": "x"})
    diff = shape_diff(old, new)
    assert any("name" in s for s in diff["added"])


def test_shape_diff_removed_field():
    old = extract_shape({"id": 1, "name": "x"})
    new = extract_shape({"id": 1})
    diff = shape_diff(old, new)
    assert any("name" in s for s in diff["removed"])


def test_shape_diff_type_change():
    old = extract_shape({"id": 1})
    new = extract_shape({"id": "abc"})
    diff = shape_diff(old, new)
    assert any("id" in s for s in diff["changed"])
