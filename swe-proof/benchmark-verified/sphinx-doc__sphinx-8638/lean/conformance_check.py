#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-8638.

The bundle models ONE routine: the per-item rendering of a documented-variable
info field, performed by `TypedField.make_field.handle_item`
(`sphinx/util/docfields.py`), configured by the variable `PyTypedField` in
`PyObject.doc_field_types` (`sphinx/domains/python.py:354`). The gold patch drops
`rolename='obj'` from that field, so the variable NAME's configured
cross-reference role becomes empty and the name renders as a plain
`literal_strong` token rather than a `pending_xref`. The TYPE token
(`typerolename='class'`) is unchanged.

We model an inline node as a tuple:
    ("text", s) | ("strong", s) | ("emph", s) | ("xref", role, inner)

`makeXref` (≙ `Field.make_xref`) is the UNCHANGED role-application callee
(A-reference): it is byte-identical between oracle and shadow, so it cancels out
and this differential test isolates exactly the R leg — the variable NAME role,
which the patch flips from "obj" to "" — over a faithful model of make_xref.

ORACLE = faithful in-process replica of the POST-PATCH handle_item (variable name
role empty). SHADOW = op-for-op transliteration of
`implementation_renderVariableItem` (Solution.lean impl region), per
refinement.md.

stdlib-only. Pinned seed: 8638 (also in mapping.md).
"""
import random
import sys

SEED = 8638
N = 120_000


# --- make_xref: faithful model of the UNCHANGED callee (A-reference) ----------
# `if not rolename: return plain; else pending_xref(reftype=rolename)[plain]`.
def make_xref(role, plain):
    if not role:
        return plain
    return ("xref", role, plain)


TYPE_ROLE = "class"  # self.typerolename for the variable field (unchanged)


# --- ORACLE: faithful replica of POST-PATCH handle_item for a variable item ---
# Post-patch the variable name role is empty (gold removed rolename='obj').
def oracle(name, type_, content):
    NAME_ROLE = ""  # post-patch: rolename dropped -> falsy/None
    par = []
    par.append(make_xref(NAME_ROLE, ("strong", name)))
    if type_ is not None:
        par.append(("text", " ("))
        par.append(make_xref(TYPE_ROLE, ("emph", type_)))
        par.append(("text", ")"))
    par.append(("text", " -- "))
    par.extend(content)
    return par


# --- SHADOW: op-for-op transliteration of implementation_renderVariableItem ---
def shadow(name, type_, content):
    name_role = ""
    par = []
    par = par + [make_xref(name_role, ("strong", name))]
    if type_ is not None:
        par = par + [("text", " (")]
        par = par + [make_xref(TYPE_ROLE, ("emph", type_))]
        par = par + [("text", ")")]
    par = par + [("text", " -- ")]
    par = par + content
    return par


def disagree(name, type_, content):
    o = oracle(name, type_, content)
    s = shadow(name, type_, content)
    if o != s:
        return (name, type_, content, o, s)
    return None


NAMES = ["attr", "limit", "x", "", "somename", "value_2"]
TYPES = [None, "int", "str", "Foo", "", "List[int]"]


def _content(rng):
    n = rng.randint(0, 3)
    out = []
    for _ in range(n):
        out.append(("text", rng.choice(["blah blah", "", "desc", "a b c"])))
    return out


def _edge_cases():
    cases = []
    for name in NAMES:
        for type_ in TYPES:
            cases.append((name, type_, []))
            cases.append((name, type_, [("text", "blah blah")]))
    return cases


def main() -> int:
    checked = 0
    for name, type_, content in _edge_cases():
        d = disagree(name, type_, content)
        if d:
            print(f"DISAGREE edge: oracle={d[3]} shadow={d[4]} args={d[:3]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        name = rng.choice(NAMES)
        type_ = rng.choice(TYPES)
        content = _content(rng)
        d = disagree(name, type_, content)
        if d:
            print(f"DISAGREE fuzz: oracle={d[3]} shadow={d[4]} args={d[:3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
