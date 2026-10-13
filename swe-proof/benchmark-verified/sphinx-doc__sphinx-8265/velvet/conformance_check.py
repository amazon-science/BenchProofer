#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8265 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`render` /
              `joinComma` / `isUnpack`, the `renderGroup` and `renderIndex`
              `do` blocks) transliterated to Python over the real repo type
              (the source-expression AST), via the mapping.md bijection
              (`Expr.atom t` ↔ a pre-rendered leaf node, `Expr.unpack` ↔
              `ast.Starred`, `Expr.group` ↔ `ast.Tuple`, `Expr.index` ↔
              `ast.Subscript`). There are NO axioms / A-references in this
              bundle: every unchanged child renderer is carried as an `atom`
              leaf (an I-op), so the shadow is pure R/I.

  * ORACLE  — patch.diff's behaviour: the patched
              `sphinx.pycode.ast._UnparseVisitor` (the real renderer) applied at
              base_commit with the gold patch applied (the harness applies
              patch.diff before this runs). This is the real correctness oracle
              (G-RESOLVE confirms the shipped patch resolves).

For every Requires-satisfying input the SHADOW string must equal the ORACLE
string. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Domain note (mapping.md §2): the real renderer has NO `visit_Starred` at
base_commit, so ANY unpacking element — anywhere in the tree — raises
`NotImplementedError` when rendered (in both branches of the patched
`visit_Subscript`). Unpacking elements are therefore outside the observable
domain and are NOT generated here. The `Expr.unpack` constructor and the
`isUnpack` guard exist in the model only to mirror the patch's
`not any(isinstance(elt, ast.Starred) ...)` clause faithfully (refinement.md);
their effect is unobservable, so G-CONF does not exercise them.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only (`ast`).
Fuzz seed pinned (mapping.md §4) for a deterministic verdict.
"""
import ast
import random
import sys

SEED = 8265
N_FUZZ = 100_000

# A small pool of already-renderable leaf texts (names / numbers / dotted
# attributes). Each is a Python expression whose rendering is fixed and
# unchanged by the patch; in the Lean model each is an `Expr.atom`.
_ATOMS = ["a", "b", "c", "x", "int", "str", "Tuple", "os.path", "1", "2",
          "3", "1234", "None", "obj.attr"]


# --- input model: an abstract source expression (the Lean `Expr`) ------------
# Represented as a nested tuple so it can be both rendered by the SHADOW and
# lowered to a Python `ast` node for the ORACLE.
#   ("atom", text)            -- a pre-rendered leaf
#   ("unpack", e)             -- *e
#   ("group", [e, ...])       -- a parenthesised group / tuple
#   ("index", value, idx)     -- value[idx]

def gen_expr(rng, depth):
    """Generate a random renderable Expr. Unpacking elements are never produced:
    the real renderer has no `visit_Starred` at base_commit, so a Starred node
    anywhere raises `NotImplementedError` (outside the observable domain)."""
    # Leaf bias grows with depth so trees terminate.
    if depth <= 0 or rng.random() < 0.45:
        return ("atom", rng.choice(_ATOMS))
    kind = rng.choice(["group", "index"])
    if kind == "group":
        n = rng.randint(0, 4)
        return ("group", [gen_expr(rng, depth - 1) for _ in range(n)])
    # kind == "index"
    value = gen_expr(rng, depth - 1)
    idx = gen_expr(rng, depth - 1)
    return ("index", value, idx)


# --- SHADOW: Solution.lean impl region transliterated ------------------------
def join_comma(parts):
    return ", ".join(parts)


def is_unpack(e):
    return e[0] == "unpack"


def render(e):
    """Transliteration of Solution.lean `render` (pure region) + the
    `renderGroup`/`renderIndex` `do` blocks. `++` ↔ `+`, `List.map render` ↔
    a comprehension, `joinComma` ↔ `", ".join`."""
    tag = e[0]
    if tag == "atom":
        return e[1]
    if tag == "unpack":
        return "*" + render(e[1])
    if tag == "group":
        elts = e[1]
        if not elts:                                  # elts.isEmpty
            return "()"
        return "(" + join_comma([render(x) for x in elts]) + ")"
    if tag == "index":
        value, idx = e[1], e[2]
        if idx[0] == "group":
            elts = idx[1]
            if elts and not any(is_unpack(x) for x in elts):
                return render(value) + "[" + join_comma([render(x) for x in elts]) + "]"
            else:
                return render(value) + "[" + render(("group", elts)) + "]"
        else:
            return render(value) + "[" + render(idx) + "]"
    raise AssertionError("unknown expr tag %r" % (tag,))


# --- ORACLE: lower the Expr to a Python ast node, render with the real visitor
def to_ast(e):
    """mapping.md §2 bijection: Expr -> Python ast node. Atoms are parsed from
    their source text (they are arbitrary renderable expressions); the three
    modeled shapes map to Starred / Tuple / Subscript."""
    tag = e[0]
    if tag == "atom":
        return ast.parse(e[1], mode="eval").body
    if tag == "unpack":
        return ast.Starred(value=to_ast(e[1]), ctx=ast.Load())
    if tag == "group":
        return ast.Tuple(elts=[to_ast(x) for x in e[1]], ctx=ast.Load())
    if tag == "index":
        return ast.Subscript(value=to_ast(e[1]), slice=to_ast(e[2]), ctx=ast.Load())
    raise AssertionError("unknown expr tag %r" % (tag,))


def oracle(e):
    from sphinx.pycode.ast import unparse           # patched real renderer
    node = to_ast(e)
    ast.fix_missing_locations(node)
    return unparse(node)


def fuzz_inputs(n, rng):
    # boundary cases first (the two changed shapes and their edges)
    yield ("group", [("atom", "1"), ("atom", "2"), ("atom", "3")])   # (1, 2, 3)
    yield ("group", [])                                              # ()
    yield ("group", [("atom", "1")])                                 # (1)
    yield ("index", ("atom", "Tuple"), ("group", [("atom", "int"), ("atom", "int")]))
    yield ("index", ("atom", "x"), ("atom", "a"))                    # x[a]
    yield ("index", ("atom", "x"), ("group", [("atom", "a"), ("atom", "b")]))
    yield ("index", ("atom", "x"), ("group", []))                    # x[()]
    yield ("index", ("atom", "x"), ("group", [("atom", "a")]))       # x[(a)] -> x[a]
    yield ("index", ("index", ("atom", "a"), ("atom", "b")), ("atom", "c"))  # a[b][c]
    for _ in range(n):
        yield gen_expr(rng, rng.randint(0, 5))


def main():
    # Fail loud if the patched repo renderer is not importable: a swallowed
    # ImportError would otherwise let G-CONF pass vacuously.
    from sphinx.pycode.ast import unparse as _probe  # noqa: F401

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    skipped = 0
    for e in fuzz_inputs(N_FUZZ, rng):
        try:
            orc = oracle(e)
        except NotImplementedError:
            # Outside the observable domain (e.g. a Starred node the real
            # renderer cannot handle). Not generated by gen_expr, but guard.
            skipped += 1
            continue
        count += 1
        sh = render(e)
        if sh != orc:
            disagreements.append((e, sh, orc))
            if len(disagreements) >= 5:
                break
    if count < 10_000:
        print("G-CONF FAIL: only %d inputs exercised (expected >=10000); the "
              "oracle may not be running." % count)
        return 1
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for e, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (e, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderGroup/renderIndex agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
