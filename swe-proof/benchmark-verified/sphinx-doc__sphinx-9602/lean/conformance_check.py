#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9602 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs (node
class + text content of each node the renderer produces):

  * SHADOW  — Solution.lean's deep model `expandLiteral head values`
              transliterated to Python node fingerprints via the mapping.md
              bijection: head -> ('pending_xref', head); '['/']'/', ' ->
              ('desc_sig_punctuation', s); each value -> the node class
              `argNodeCtor head` selects, carrying reprVal v — ('Text', …) under
              the enumeration head and ('pending_xref', …) under every other
              dotted head. `reprVal` is the I/A-reference transliteration of
              `repr` (kept the real builtin here — G-CONF isolates the structure;
              reprVal==repr is G-AX's job, but using real repr keeps the shadow
              honest).
  * ORACLE  — `patch.diff`'s behaviour: the patched `_parse_annotation` applied
              at base_commit (the real correctness oracle, G-RESOLVE) on the
              annotation string "<head>[<v1>, <v2>, ...]". We read the produced
              node list's per-node (class, astext) — exactly what the F2P
              test_parse_annotation_Literal asserts on.

They must agree on every Requires-satisfying input (`okHead head` — any dotted
Python type name, which is the enumeration heads AND every other dotted head —
and a non-empty list of in-domain constant values). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

The head distribution spans BOTH sides of the enumeration test, which is what
lets this check see the argument node CLASS as a function of the head rather
than at one head only: an implementation that rendered the arguments the same
way for every head would disagree here on the non-enumeration rows. The head
pool (mapping.md §4) therefore carries near-misses of the enumeration names on
purpose — an aliased module path, a differently-cased spelling, a longer name
with the same prefix — so both an over-broad and an under-broad selection is
refuted mechanically.

Runs in-container with the gold patch applied (the changed function gives the
buggy result at base_commit). stdlib + docutils/sphinx only; fuzz seed pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import string
import sys

from sphinx.domains.python import _parse_annotation

SEED = 9602
N_FUZZ = 100_000


class _Config:
    python_use_unqualified_type_names = False


class _Env:
    def __init__(self):
        self.config = _Config()
        self.ref_context = {}


# --- the R/I shadow of Solution.lean expandLiteral ---------------------------

LIT_HEADS = ("Literal", "typing.Literal")


def repr_val(v):
    """Transliteration of Solution.lean `reprVal`; kept == builtin repr on the
    modeled domain (the A-reference G-AX validates separately)."""
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


def arg_node_class(head):
    """Transliteration of Solution.lean `argNodeCtor`: which node class an
    ARGUMENT of `head[...]` carries. Plain display text under the enumeration
    head (the arguments are values there, and a value names no class), a
    navigable cross-reference under any other dotted head."""
    return "Text" if head in LIT_HEADS else "pending_xref"


def shadow_fingerprints(head, values):
    """expandLiteral head values, as a list of (node_class, text) fingerprints.

        wrap head (valSeq (argNodeCtor head) reprVal values)
          = xref head :: punct '[' :: (inner ++ [punct ']'])
    where inner interleaves one (argNodeCtor head, reprVal v) per value with
    ('… ', ', ') punctuation between adjacent values -- and, for an EMPTY
    argument list, is the empty tuple's own parenthesis pair (`valSeq`'s empty
    arm), which is punctuation and so does not depend on the head.
    """
    cls = arg_node_class(head)
    out = [("pending_xref", head), ("desc_sig_punctuation", "[")]
    if not values:
        out.append(("desc_sig_punctuation", "("))
        out.append(("desc_sig_punctuation", ")"))
    for i, v in enumerate(values):
        if i > 0:
            out.append(("desc_sig_punctuation", ", "))
        out.append((cls, repr_val(v)))
    out.append(("desc_sig_punctuation", "]"))
    return out


# --- the oracle: patched _parse_annotation -----------------------------------

def literal_source(value):
    """Python source text of one constant value (its repr is its source form on
    the modeled domain)."""
    return repr_val_to_source(value)


def repr_val_to_source(v):
    kind, value = v
    if kind == "null":
        return "None"
    if kind == "bool":
        return "True" if value else "False"
    if kind == "int":
        return str(value)
    if kind == "str":
        return repr(value)  # a valid source string literal
    raise AssertionError("unknown kind %r" % (kind,))


def annotation_string(head, values):
    # An argument list with no elements has exactly one source spelling: the
    # empty tuple. `head[]` is not Python at all, so it is not the empty case.
    if not values:
        return "%s[()]" % (head,)
    return "%s[%s]" % (head, ", ".join(repr_val_to_source(v) for v in values))


def oracle_fingerprints(head, values, env):
    annotation = annotation_string(head, values)
    result = _parse_annotation(annotation, env)
    return [(type(n).__name__, n.astext()) for n in result]


# --- input domain ------------------------------------------------------------

def is_simple_str(s):
    return all(32 <= ord(c) <= 126 and c != "'" and c != "\\" for c in s)


def random_value(rng, simple_alphabet):
    r = rng.random()
    if r < 0.30:
        return ("int", rng.randint(0, 10**9))
    if r < 0.46:
        return ("bool", rng.choice([True, False]))
    if r < 0.56:
        return ("null", None)
    k = rng.randint(0, 12)
    return ("str", "".join(rng.choice(simple_alphabet) for _ in range(k)))


# Every head is a dotted Python type name (`okHead`). The pool deliberately
# straddles the enumeration test: the two enumeration names, ordinary container
# names, dotted module paths, and near-misses of the enumeration names (an
# aliased path, a differently-cased spelling, a longer name sharing the prefix,
# a path whose LAST segment is the enumeration name) so that a selection made
# too broadly or too narrowly disagrees on some row.
HEAD_POOL = (
    "Literal", "typing.Literal",
    "List", "Tuple", "Optional", "Dict", "Set", "FrozenSet",
    "typing.List", "typing.Optional", "typing.Dict",
    "t.Literal", "tp.Literal", "mod.sub.Literal",
    "literal", "LITERAL", "LiteralX", "Literals", "MyLiteral",
    "Literal2", "_Literal", "Annotated", "x.y.z", "_Foo", "A1",
    "my.mod.Thing", "sphinx.util.typing.Literal",
)


def fuzz_inputs(n, rng):
    simple_alphabet = [chr(c) for c in range(32, 127)
                       if chr(c) != "'" and chr(c) != "\\"]
    # boundary cases first (the two F2P rows, then small structural variants)
    yield ("Literal", [("bool", True), ("bool", False)])
    yield ("typing.Literal", [("int", 0), ("int", 1), ("str", "abc")])
    yield ("Literal", [("bool", True)])
    yield ("typing.Literal", [("int", 255)])
    yield ("Literal", [("str", "")])
    yield ("Literal", [("str", "x y z"), ("int", 7), ("bool", False)])
    yield ("typing.Literal", [("str", "a"), ("str", "b"), ("str", "c")])
    yield ("Literal", [("null", None)])
    yield ("typing.Literal", [("null", None), ("bool", True)])
    # the zero-argument spelling, on BOTH sides of the head test: the argument
    # region is the empty tuple's parenthesis pair, which is punctuation and so
    # must be head-independent.
    yield ("Tuple", [])
    yield ("Literal", [])
    yield ("typing.Literal", [])
    # the other side of the head test: the argument node class must differ here,
    # including the row the surrounding annotation tests read (`List[None]`).
    yield ("List", [("null", None)])
    yield ("Optional", [("null", None)])
    yield ("List", [("int", 0)])
    yield ("Tuple", [("int", 0), ("null", None)])
    yield ("typing.List", [("bool", False)])
    # near-misses of the enumeration names
    yield ("t.Literal", [("int", 0)])
    yield ("mod.sub.Literal", [("bool", True)])
    yield ("literal", [("bool", True)])
    yield ("LiteralX", [("int", 1)])
    yield ("MyLiteral", [("null", None)])
    yield ("_Literal", [("str", "abc")])
    for _ in range(n):
        head = rng.choice(HEAD_POOL)
        k = rng.randint(1, 5)
        values = [random_value(rng, simple_alphabet) for _ in range(k)]
        yield (head, values)


def main():
    env = _Env()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for head, values in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_fingerprints(head, values)
        oracle = oracle_fingerprints(head, values, env)
        if shadow != oracle:
            disagreements.append((annotation_string(head, values), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  annotation=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of literalTypeNodes (expandLiteral) agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
