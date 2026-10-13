#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9602.

Validates the two UNCHANGED sub-callees the deep model in Solution.lean rests
on (the whole CHANGED function `_parse_annotation` is validated separately by
conformance_check.py / G-CONF, which runs WITH the gold patch applied — at
base_commit the changed function still has the bug, so it cannot be the G-AX
oracle). This script runs WITHOUT the patch, against callees present and
unchanged at base_commit:

  (A-reference §3.1) the deep model `reprVal` (Solution.lean pure region) ==
      Python builtin `repr` on the modeled constant domain — booleans, integers,
      and "simple" strings (printable ASCII, no apostrophe/backslash, `okLit`):
          reprVal(bool b) == repr(b)       # 'True' / 'False'
          reprVal(int n)  == repr(n)       # decimal digits
          reprVal(str s)  == repr(s)       # "'" + s + "'"  (single-quoted)
      This is the operation the patch adds (`repr(node.value)`); `repr` itself
      is unchanged.

  (carrier §3.2) the head cross-reference: the UNCHANGED callee
      `type_to_xref(head, env)` returns a `pending_xref` whose visible text and
      `reftarget` equal the head string — confirming the `DocNode.xref head`
      modeling of the head node `Literal` / `typing.Literal`.

Imports only the repo module under change plus docutils/sphinx.addnodes (the
machinery the renderer uses). A minimal `env` stub supplies the two attributes
`type_to_xref` reads. Exit 0 iff every obligation holds. Runs in-container.
"""
import random
import string
import sys

from sphinx import addnodes
from sphinx.domains.python import type_to_xref


class _Config:
    # Default configuration: with unqualified type names OFF, type_to_xref emits
    # a single nodes.Text child inside the pending_xref.
    python_use_unqualified_type_names = False


class _Env:
    def __init__(self):
        self.config = _Config()
        self.ref_context = {}


# --- reprVal reference (kept in lock-step with Solution.lean) ----------------

def is_simple_str(s):
    """Mirror of Solution.lean `okLit` for the str case: every char is printable
    ASCII (32-126) other than apostrophe and backslash."""
    return all(32 <= ord(c) <= 126 and c != "'" and c != "\\" for c in s)


def repr_val(v):
    """Reference impl of Solution.lean `reprVal` for a (kind, value) constant."""
    kind, value = v
    if kind == "null":
        return "None"
    if kind == "bool":
        return "True" if value else "False"
    if kind == "int":
        return str(value)
    if kind == "str":
        return "'" + value + "'"
    raise AssertionError("unknown kind %r" % (kind,))


def python_value(v):
    """The real Python constant object a LitVal abstracts."""
    kind, value = v
    if kind == "null":
        return None
    if kind == "bool":
        return bool(value)
    if kind == "int":
        return int(value)
    if kind == "str":
        return str(value)
    raise AssertionError("unknown kind %r" % (kind,))


# --- the checks --------------------------------------------------------------

def check_repr_reference(v):
    """A-reference: reprVal(v) == real repr(python_value(v))."""
    if v[0] == "str":
        assert is_simple_str(v[1]), "test bug: %r not a simple string" % (v[1],)
    model = repr_val(v)
    real = repr(python_value(v))
    assert model == real, (
        "reprVal deep model unsound on %r: repr gave %r, model gives %r"
        % (v, real, model))


def check_head_xref(head, env):
    """Carrier: type_to_xref(head) is a pending_xref with text/target == head."""
    node = type_to_xref(head, env)
    assert isinstance(node, addnodes.pending_xref), (
        "head carrier unfaithful on %r: type_to_xref gave %s (%r)"
        % (head, type(node).__name__, node))
    assert node.astext() == head and node.get("reftarget") == head, (
        "head carrier unfaithful on %r: xref text=%r target=%r, expected both %r"
        % (head, node.astext(), node.get("reftarget"), head))


def main():
    env = _Env()

    # --- reprVal A-reference: boundary constants --------------------------
    boundary = [
        ("null", None),
        ("bool", True), ("bool", False),
        ("int", 0), ("int", 1), ("int", 42), ("int", 255),
        ("int", 1000000), ("int", 987654321),
        ("str", ""), ("str", "abc"), ("str", "a"),
        ("str", "Hello, World"), ("str", "x y z"),
        ("str", "0"), ("str", "True"), ("str", "snake_case_name"),
        ("str", "with spaces and 123"),
    ]
    for v in boundary:
        check_repr_reference(v)

    # --- reprVal A-reference: randomized fuzz -----------------------------
    rng = random.Random(9602)
    simple_alphabet = [chr(c) for c in range(32, 127)
                       if chr(c) != "'" and chr(c) != "\\"]
    for _ in range(20000):
        r = rng.random()
        if r < 0.30:
            v = ("int", rng.randint(0, 10**12))
        elif r < 0.46:
            v = ("bool", rng.choice([True, False]))
        elif r < 0.56:
            v = ("null", None)
        else:
            k = rng.randint(0, 24)
            s = "".join(rng.choice(simple_alphabet) for _ in range(k))
            v = ("str", s)
        check_repr_reference(v)

    # --- head cross-reference carrier -------------------------------------
    # Both sides of the head test: the head node is a cross-reference targeting
    # the head string for EVERY dotted head, which is why `wrap` is head-uniform
    # while the ARGUMENT class is not.
    for head in ["Literal", "typing.Literal",
                 "List", "Tuple", "Optional", "typing.List", "typing.Dict",
                 "t.Literal", "LiteralX", "literal", "my.mod.Thing", "_Foo"]:
        check_head_xref(head, env)

    print("G-AX OK: reprVal deep model (== builtin repr) sound on %d boundary + "
          "20000 fuzz constants; head type_to_xref carrier faithful on 2 heads"
          % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
