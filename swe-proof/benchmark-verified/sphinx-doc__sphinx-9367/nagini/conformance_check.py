#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9367 (nagini).

SHADOW
------
`shadow_render_tuple` below is the `# impl-start` / `# impl-end` region of
`model.py` copied VERBATIM, with only the contract calls removed
(`Requires`/`Ensures`/`Invariant`/`Assert` and the `# invariants-start`/`-end`
markers). No renaming, no restructuring, no "simplification": the backward
`while i > 0` loop that materializes the separator-join, the `es = ToSeq(elts)`
view, the `n == 0` / `n == 1` / `else` branch order and the exact `PSeq(40, 41)`
/ `PSeq(40) + es[0] + PSeq(44, 41)` / `PSeq(40) + joined + PSeq(41)` literals
are all as written in the frozen model.

The two `@Pure` helpers the region calls -- `empty_seq()` and `sep()` -- are
copied over minus their contracts. `join_sep` / `render_seq` are NOT copied:
they appear only in `render_tuple`'s postcondition, never in the impl region,
so copying them would test the spec against itself rather than the impl against
the repo.

There are NO `@ContractOnly` callees and NO axioms in this bundle (mapping.md
section 3), so nothing here is assumed rather than executed.

Nagini carrier shim: `PSeq` is realized as an immutable tuple wrapper exposing
exactly the operations the region uses (`PSeq(*items)`, `take`, `drop`, `+`,
`len`, `[]`, `==`), and `ToSeq(list)` materializes one from a Python list.

ORACLE
------
The REAL patched repo function, CALLED, not transliterated:
`sphinx.pycode.ast._UnparseVisitor.visit_Tuple` (`sphinx/pycode/ast.py:215` at
base_commit `6918e696`, mapping.md section 1). The gate applies patch.diff to
/testbed and sets PYTHONPATH before this script runs, so `visit_Tuple` here is
the post-patch three-branch version. It is driven directly on an `ast.Tuple`
node through a live `_UnparseVisitor("")` instance -- the whole context the
real function needs is one AST node, so there is no reason to transliterate.

TYPE BRIDGE (mapping.md section 2, inverted)
--------------------------------------------
The model's input carrier is the list of the members' ALREADY-RENDERED text
(`self.visit(e)` is unchanged by the patch, so mapping.md section 1 abstracts it
as the input), with each rendering a `PSeq[int]` of Unicode code points. So:

  * generate member renderings as concrete `str`s;
  * shadow side: `str` -> `PSeq[int]` via `ord` per character, list ->
    `List[PSeq[int]]`; result `PSeq[int]` -> `str` via `chr`;
  * oracle side: an `ast.Tuple` whose k-th element is a node the UNCHANGED
    renderer maps to exactly that same `str`, so both sides consume the
    identical member renderings and any disagreement is in the assembly.

Two independent ways of realizing that oracle-side node are used, so the bridge
is not the only thing being trusted:

  (a) SYNTHETIC members -- `ast.Name(id=s)`, since the unchanged
      `visit_Name` returns `node.id` verbatim (`sphinx/pycode/ast.py:189`).
      This reaches the FULL abstract domain of the model: member renderings
      that are empty, that contain `,`, `, `, `(`, `)`, or non-ASCII code
      points -- inputs no parseable tuple source can produce, and exactly the
      ones that would expose a bogus join/quoting assumption.
  (b) PARSED members -- real Python source parsed with `ast.parse`, with the
      shadow's member renderings taken from the genuine recursive
      `visitor.visit(e)`. This exercises the real renderer (including nested
      tuples, so the patched `visit_Tuple` recurses) rather than a stand-in.

INPUT DOMAIN AND COUNT
----------------------
`Requires` is only `Acc(list_pred(elts), 1/2)` plus `MustTerminate(2)`: every
finite list of finite code-point sequences is admissible, and no generated
input is excluded. Nothing here narrows the domain to route around a branch --
on the contrary, arm (a) widens it past what the sibling velvet/lean checks
reach.

The modeled behaviour is a function of the member-rendering LIST, so the check
first ENUMERATES EXHAUSTIVELY every member-rendering list of length 0..4 drawn
from a 9-symbol adversarial alphabet (`''`, `'x'`, `'1'`, `'a, b'`, `','`,
`'('`, `')'`, `'(1,)'`, `'é'`) -- 1 + 9 + 81 + 729 + 6561 = 7381 lists,
a complete decision over that alphabet, which is strictly stronger than
sampling it. Then boundary/F2P parsed sources, then seeded fuzz over BOTH arms
to reach >= 100000 inputs total.

Every branch of the impl region is taken: `n == 0` (the `()` form),
`n == 1` (the trailing-comma form -- the F2P case `(1,)`), and the `else` loop
with both its `i == n` first iteration and its `i < n` `e + sep() + joined`
iterations (every list of length >= 2).

Pinned seed: 9367 (recorded in mapping.md, section "G-CONF").

Exit 0 iff zero disagreements; on a disagreement the input member renderings
and both outputs are printed and the exit status is 1. stdlib only.
"""
import ast
import itertools
import json
import random
import sys

SEED = 9367
N_TOTAL_MIN = 100_000
MAX_ARITY_FUZZ = 7


# --- PSeq shim: immutable sequence, exactly the ops the impl region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    """Nagini's pure view of a list, as an immutable PSeq."""
    return PSeq._wrap(lst)


# --- @Pure helpers from model.py the impl region calls, contracts stripped ----

def empty_seq():
    """The empty code-point sequence."""
    return PSeq(0).take(0)


def sep():
    """The member separator: U+002C U+0020 (`, `)."""
    return PSeq(44, 32)


# --- the impl region of model.py, VERBATIM, contract calls stripped ----------

def shadow_render_tuple(elts):
    es = ToSeq(elts)  # type: PSeq[PSeq[int]]
    n = len(elts)
    if n == 0:
        return PSeq(40, 41)
    elif n == 1:
        return PSeq(40) + es[0] + PSeq(44, 41)
    else:
        joined = empty_seq()  # type: PSeq[int]
        i = n
        while i > 0:
            e = es[i - 1]
            if i == n:
                joined = e
            else:
                joined = e + sep() + joined
            i = i - 1
        return PSeq(40) + joined + PSeq(41)


# --- type bridge: str <-> PSeq[int] of Unicode code points -------------------

def str_to_pseq(s):
    return PSeq(*[ord(c) for c in s])


def pseq_to_str(p):
    return "".join(chr(p[k]) for k in range(len(p)))


def shadow_of_images(images):
    """Run the shadow over the member renderings given as concrete `str`s."""
    return pseq_to_str(shadow_render_tuple([str_to_pseq(s) for s in images]))


# --- oracle drivers ----------------------------------------------------------

def name_tuple_node(images):
    """An ast.Tuple whose k-th member the UNCHANGED renderer maps to
    images[k] verbatim (visit_Name returns node.id)."""
    return ast.Tuple(elts=[ast.Name(id=s, ctx=ast.Load()) for s in images],
                     ctx=ast.Load())


def check_node(visitor, node, label):
    """Diff shadow vs the real patched visit_Tuple on one ast.Tuple node.
    Returns an error string on disagreement, else None."""
    # member renderings: the UNCHANGED recursive renderer (mapping.md sec. 1)
    images = [visitor.visit(e) for e in node.elts]
    shadow = shadow_of_images(images)
    oracle = visitor.visit_Tuple(node)          # REAL patched repo function
    if shadow != oracle:
        return ("G-CONF DISAGREEMENT (%s)\n  arity=%d\n  member renderings=%r"
                "\n  shadow=%r\n  oracle=%r"
                % (label, len(images), images, shadow, oracle))
    return None


# --- input generation -------------------------------------------------------

# 9-symbol adversarial alphabet of member renderings: empty, plain, one that
# already contains the separator, the bare separator pieces, an unbalanced
# paren each way, a nested single-element tuple rendering, and a non-ASCII
# code point (exercising the ord/chr leg of the bridge).
ALPHABET = ["", "x", "1", "a, b", ",", "(", ")", "(1,)", "é"]

EXHAUSTIVE_MAX_LEN = 4

# Boundary / F2P real sources (parsed arm): every branch, F2P shape first.
BOUNDARY_SOURCES = [
    "()",                       # n == 0            (P2P)
    "(1,)",                     # n == 1            (the FAIL_TO_PASS case)
    "(1, 2)",                   # n >= 2            (P2P)
    "(1, 2, 3)",                # n >= 2            (P2P)
    "(a,)",
    "('s',)",
    "(None,)",
    "(...,)",
    "(object(),)",
    "((1,),)",                  # nested single-element tuple member
    "((1, 2), 3)",              # nested multi tuple member
    "(x.y.z, [1, 2], {1: 2})",
    "(lambda x: ..., not a, ~ b, - 1)",
    "(a, b, c, d, e, f, g)",    # long arity
]

FUZZ_ATOMS = ["1", "0", "1234", "a", "b", "obj", "os.path", "x.y.z", "'str'",
              '"s"', "b'bytes'", "...", "None", "True", "1.5", "- 1", "+ a",
              "not b", "~ x", "a + b", "[1, 2]", "{1, 2}", "{'k': 1}",
              "lambda x: ...", "object()", "Tuple[int, int]", "f(1, x=2)"]


def _tuple_source(parts):
    n = len(parts)
    if n == 0:
        return "()"
    if n == 1:
        return "(" + parts[0] + ",)"
    return "(" + ", ".join(parts) + ")"


def fuzz_atom(rng, depth=1):
    if depth <= 0 or rng.random() < 0.85:
        return rng.choice(FUZZ_ATOMS)
    k = rng.randint(0, 3)
    return _tuple_source([fuzz_atom(rng, depth - 1) for _ in range(k)])


def parse_tuple(src):
    node = ast.parse(src, mode="eval").body
    return node if isinstance(node, ast.Tuple) else None


def main():
    # The REAL patched repo function (gold patch already applied by the gate).
    from sphinx.pycode.ast import _UnparseVisitor
    visitor = _UnparseVisitor("")

    checked = 0
    n_exhaustive = 0
    n_boundary = 0
    n_fuzz_synth = 0
    n_fuzz_parsed = 0

    # 1. Exhaustive over the adversarial alphabet, lengths 0..EXHAUSTIVE_MAX_LEN
    #    (synthetic arm -- reaches the full abstract domain of the model).
    for length in range(EXHAUSTIVE_MAX_LEN + 1):
        for images in itertools.product(ALPHABET, repeat=length):
            err = check_node(visitor, name_tuple_node(list(images)),
                             "exhaustive/synthetic")
            if err:
                print(err)
                return 1
            checked += 1
            n_exhaustive += 1

    # 2. Boundary / F2P real sources (parsed arm).
    for src in BOUNDARY_SOURCES:
        node = parse_tuple(src)
        if node is None:
            print("G-CONF ERROR: boundary source %r is not a tuple" % src)
            return 1
        err = check_node(visitor, node, "boundary/parsed src=%r" % src)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    # 3. Seeded fuzz over both arms until >= N_TOTAL_MIN inputs total.
    rng = random.Random(SEED)
    while checked < N_TOTAL_MIN:
        if rng.random() < 0.5:
            # synthetic arm: arbitrary member renderings from the alphabet,
            # plus occasional random concatenations of alphabet symbols.
            arity = rng.randint(0, MAX_ARITY_FUZZ)
            images = []
            for _ in range(arity):
                k = rng.randint(1, 3)
                images.append("".join(rng.choice(ALPHABET) for _ in range(k)))
            err = check_node(visitor, name_tuple_node(images), "fuzz/synthetic")
            if err:
                print(err)
                return 1
            n_fuzz_synth += 1
        else:
            # parsed arm: real source through the genuine recursive renderer.
            arity = rng.randint(0, MAX_ARITY_FUZZ)
            src = _tuple_source([fuzz_atom(rng, depth=2) for _ in range(arity)])
            try:
                node = parse_tuple(src)
            except SyntaxError:
                continue
            if node is None:
                continue
            err = check_node(visitor, node, "fuzz/parsed src=%r" % src)
            if err:
                print(err)
                return 1
            n_fuzz_parsed += 1
        checked += 1

    print("G-CONF OK: contract-stripped impl region of model.py agrees with the "
          "real patched _UnparseVisitor.visit_Tuple (sphinx/pycode/ast.py) on "
          "%d inputs (%d exhaustive over lengths 0..%d of a %d-symbol "
          "adversarial alphabet, %d boundary/F2P sources, %d synthetic fuzz, "
          "%d parsed fuzz; seed=%d); 0 disagreements."
          % (checked, n_exhaustive, EXHAUSTIVE_MAX_LEN, len(ALPHABET),
             n_boundary, n_fuzz_synth, n_fuzz_parsed, SEED))
    print(json.dumps({
        "checked": checked,
        "disagreements": 0,
        "seed": SEED,
        "shadow": "direct (contract-stripped impl region of model.py)",
        "oracle": "called: sphinx.pycode.ast._UnparseVisitor.visit_Tuple",
        "exhaustive": {"lengths": "0..%d" % EXHAUSTIVE_MAX_LEN,
                       "alphabet": len(ALPHABET), "cases": n_exhaustive},
        "boundary": n_boundary,
        "fuzz_synthetic": n_fuzz_synth,
        "fuzz_parsed": n_fuzz_parsed,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
