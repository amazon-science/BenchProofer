#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9602 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs (node
class + text content of each node the renderer produces):

  * SHADOW  — Solution.lean's deep model `expandLiteral head values`
              transliterated to Python node fingerprints via the mapping.md
              bijection: head -> ('pending_xref', head); '['/']'/', ' ->
              ('desc_sig_punctuation', s); each value -> ('Text', reprVal v).
              `reprVal` is the I/A-reference transliteration of `repr` (kept the
              real builtin here — G-CONF isolates the structure; reprVal==repr is
              G-AX's job, but using real repr keeps the shadow honest).
  * ORACLE  — `patch.diff`'s behaviour: the patched `_parse_annotation` applied
              at base_commit (the real correctness oracle, G-RESOLVE) on the
              annotation string "<head>[<v1>, <v2>, ...]". We read the produced
              node list's per-node (class, astext) — exactly what the F2P
              test_parse_annotation_Literal asserts on.

They must agree on every Requires-satisfying input (head in {Literal,
typing.Literal}, a non-empty list of in-domain constant values). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

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

def repr_val(v):
    """Transliteration of Solution.lean `reprVal`; kept == builtin repr on the
    modeled domain (the A-reference G-AX validates separately)."""
    kind, value = v
    if kind == "bool":
        return "True" if value else "False"
    if kind == "int":
        return str(value)
    if kind == "str":
        return "'" + value + "'"
    raise AssertionError("unknown kind %r" % (kind,))


def shadow_fingerprints(head, values):
    """expandLiteral head values, as a list of (node_class, text) fingerprints.

        wrap head (valSeq DocNode.text reprVal values)
          = xref head :: punct '[' :: (inner ++ [punct ']'])
    where inner interleaves one ('Text', reprVal v) per value with ('… ', ', ')
    punctuation between adjacent values.
    """
    out = [("pending_xref", head), ("desc_sig_punctuation", "[")]
    for i, v in enumerate(values):
        if i > 0:
            out.append(("desc_sig_punctuation", ", "))
        out.append(("Text", repr_val(v)))
    out.append(("desc_sig_punctuation", "]"))
    return out


# --- the oracle: patched _parse_annotation -----------------------------------

def literal_source(value):
    """Python source text of one constant value (its repr is its source form on
    the modeled domain)."""
    return repr_val_to_source(value)


def repr_val_to_source(v):
    kind, value = v
    if kind == "bool":
        return "True" if value else "False"
    if kind == "int":
        return str(value)
    if kind == "str":
        return repr(value)  # a valid source string literal
    raise AssertionError("unknown kind %r" % (kind,))


def annotation_string(head, values):
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
    if r < 0.34:
        return ("int", rng.randint(0, 10**9))
    if r < 0.5:
        return ("bool", rng.choice([True, False]))
    k = rng.randint(0, 12)
    return ("str", "".join(rng.choice(simple_alphabet) for _ in range(k)))


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
    for _ in range(n):
        head = rng.choice(["Literal", "typing.Literal"])
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
