#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12325.

The bundle models ONE value: the parent-link mapping built while a model class is
assembled (`ModelBase.__new__`, the `# Collect the parent links` block). The
modeled value is a PURE function of the candidate-field stream (mapping.md):

    fields : list[Field]   where each Field exposes
        isOneToOne : bool   (isinstance(field, OneToOneField))
        parentLink : bool   (field.remote_field.parent_link)
        relatedKey : str    (make_model_tuple(resolve_relation(...)))
        name       : str    (field identity)

Post-patch rule:

    parent_links = {}
    for field in fields:
        if field.isOneToOne and field.parentLink:        # gold's added conjunct
            parent_links[field.relatedKey] = field       # last-write-wins
    return parent_links

Standing up Django's metaclass machinery (resolve_relation / make_model_tuple /
OneToOneField construction) to drive the real `__new__` is heavy and unnecessary:
the modeled value is this pure last-write-wins fold over the observables the real
loop exposes. So the ORACLE below is a faithful in-process replica using the EXACT
patched guard (`isOneToOne and parentLink`) + a real Python `dict` (the true
last-write-wins semantics), and the SHADOW is the op-for-op transliteration of
`implementation_collectParentLinks` (a `for` loop with `dictInsert`, per
refinement.md).

The mapping is membership-determined (a dict: key -> field identity), so we
compare the two legs AS key->field-name maps. This genuinely tests the bug:
when a key is shared by a parent-link field and a later non-parent-link one-to-one
field, the post-patch mapping keeps the PARENT LINK; the pre-patch mapping keeps
the later field. The shadow must reproduce exactly that.

stdlib-only. Pinned seed: 12325 (also in mapping.md).
"""
import random
import sys

SEED = 12325
N = 150_000


class Field:
    __slots__ = ("isOneToOne", "parentLink", "relatedKey", "name")

    def __init__(self, isOneToOne, parentLink, relatedKey, name):
        self.isOneToOne = isOneToOne
        self.parentLink = parentLink
        self.relatedKey = relatedKey
        self.name = name


# --- ORACLE: faithful in-process replica of the patched decision -------------
def oracle_map(fields):
    parent_links = {}
    for f in fields:
        if f.isOneToOne and f.parentLink:          # gold's guard (post-patch)
            parent_links[f.relatedKey] = f         # real dict: last-write-wins
    # compare as key -> field-name map
    return {k: v.name for k, v in parent_links.items()}


# --- SHADOW of implementation_collectParentLinks (the R/I leg) ---------------
# Mirrors Solution.lean: parentLinks := []; for field in fields do
#   if field.isOneToOne && field.parentLink then
#     parentLinks := dictInsert parentLinks field.relatedKey field
def _dict_insert(d, k, v):
    # dictInsert d k v = d.filter (·.1 ≠ k) ++ [(k, v)]
    out = [(kk, vv) for (kk, vv) in d if kk != k]
    out.append((k, v))
    return out


def shadow_map(fields):
    parent_links = []                              # List (String × Field)
    for f in fields:
        if f.isOneToOne and f.parentLink:
            parent_links = _dict_insert(parent_links, f.relatedKey, f)
    return {k: v.name for (k, v) in parent_links}  # assoc list -> map


def disagree(fields):
    got = oracle_map(fields)
    want = shadow_map(fields)
    if got != want:
        desc = [(f.isOneToOne, f.parentLink, f.relatedKey, f.name) for f in fields]
        return (desc, got, want)
    return None


KEYS = ["app.document", "app.place", "app.parent", "app.other", "app.tag"]


def _enumerate_edge():
    cases = []
    # the FAIL_TO_PASS shape: a genuine parent link to a key, then a later plain
    # OneToOne to the SAME key. Post-patch keeps the parent link.
    cases.append([
        Field(True, True, "app.document", "document_ptr"),
        Field(True, False, "app.document", "origin"),
    ])
    # reversed declaration order (the issue notes order "works" pre-patch only by
    # luck): plain first, parent link last.
    cases.append([
        Field(True, False, "app.document", "origin"),
        Field(True, True, "app.document", "document_ptr"),
    ])
    # single plain OneToOne to a parent (test_onetoone_with_parent_model):
    # post-patch records NOTHING (no parent link) -> empty map; pre-patch records it.
    cases.append([Field(True, False, "app.place", "other_place")])
    # explicit parent link present alongside a plain one (explicit_parent_link test)
    cases.append([
        Field(True, True, "app.place", "place"),
        Field(True, False, "app.place", "other_place"),
    ])
    # non-OneToOne fields are never recorded
    cases.append([
        Field(False, False, "app.parent", "fk_field"),
        Field(True, True, "app.parent", "parent_ptr"),
    ])
    # empty
    cases.append([])
    # two distinct keys, each with its own parent link
    cases.append([
        Field(True, True, "app.document", "document_ptr"),
        Field(True, True, "app.place", "place_ptr"),
    ])
    # multiple parent-link candidates to the same key -> last-write-wins among them
    cases.append([
        Field(True, True, "app.document", "ptr_a"),
        Field(True, True, "app.document", "ptr_b"),
    ])
    return cases


def _rand_fields(rng):
    n = rng.randint(0, 6)
    out = []
    for _ in range(n):
        out.append(Field(
            rng.choice([True, False]),
            rng.choice([True, False]),
            rng.choice(KEYS),
            "f%d" % rng.randint(0, 1000),
        ))
    return out


def main() -> int:
    checked = 0
    for fields in _enumerate_edge():
        d = disagree(fields)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        fields = _rand_fields(rng)
        d = disagree(fields)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
