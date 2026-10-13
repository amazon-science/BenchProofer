#!/usr/bin/env python3
r"""G-CONF differential conformance check for sphinx-doc__sphinx-9367 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. The whole
impl region is pure R/I (no A-tagged callee — mapping.md §3).

The modeled observable is the SOURCE RENDERING of a parenthesized
comma-separated sequence, as a function of its members' already-rendered text
(mapping.md §2):

  * SHADOW  — `renderTuple` / `renderSequence` transliterated to Python over the
              real repo types (`List (List Char)` ↔ `list[str]`):
                  shadow_render(images)
                      = "()"                          if len == 0
                      = "(" + images[0] + ",)"        if len == 1   (trailing comma)
                      = "(" + ", ".join(images) + ")" if len >= 2
              The unchanged recursive renderer `self.visit(e)` is the opaque
              input: `images[i]` is precisely `unparse(node.elts[i])`.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `sphinx.pycode.ast._UnparseVisitor.visit_Tuple`, observed through
              the public `unparse(node)` on an `ast.Tuple` node.

For each fuzzed tuple node:

      shadow_render([unparse(e) for e in node.elts])  ==  unparse(node)

This isolates exactly the OUTER assembly logic visit_Tuple changed: the member
images on the shadow side are the very same `unparse` outputs the oracle's
`", ".join`/`%` consume, so any disagreement is an outer-wrapping R/I
counterexample (the trailing-comma case being the discriminating one). Exit 0
iff zero disagreements. stdlib + sphinx only. Seed pinned (mapping.md §4).
"""
import ast
import random
import sys

SEED = 9367
N_FUZZ = 100_000


def shadow_render(images):
    """renderTuple transliterated: wrap/join the already-rendered member text by
    member count. The one-member case keeps a trailing comma (the fix)."""
    n = len(images)
    if n == 0:
        return "()"
    elif n == 1:
        return "(" + images[0] + ",)"
    else:
        return "(" + ", ".join(images) + ")"


def make_tuple_source(elem_sources):
    """Build Python source that parses to an ast.Tuple with exactly the given
    element source fragments (0, 1, or many)."""
    n = len(elem_sources)
    if n == 0:
        return "()"
    elif n == 1:
        return "(" + elem_sources[0] + ",)"
    else:
        return "(" + ", ".join(elem_sources) + ")"


def fuzz_elem_pool(rng):
    """A pool of simple element source fragments. Atoms keep the member image
    predictable; the occasional nested tuple exercises visit_Tuple recursively
    (still isolated: the shadow reuses the oracle's unparse image)."""
    atoms = ["1", "2", "0", "1234", "a", "b", "obj", "os.path", "x.y.z",
             "'str'", '"s"', "b'bytes'", "...", "None", "True", "1.5",
             "- 1", "+ a", "not b", "~ x", "a + b", "[1, 2]", "{1, 2}",
             "{'k': 1}", "lambda: 1", "object()", "Tuple[int, int]"]
    r = rng.random()
    if r < 0.85:
        return rng.choice(atoms)
    # occasional nested tuple element (recursive visit_Tuple)
    k = rng.randint(0, 3)
    return make_tuple_source([rng.choice(atoms) for _ in range(k)])


def fuzz_nodes(n, rng):
    """Yield ast.Tuple nodes of varied arity, via real source + parse so the
    member images are produced by the genuine recursive renderer."""
    # boundary / F2P cases first (plan §4.1 step 4)
    boundary = [
        "()",                 # empty   (F2P + PASS_TO_PASS)
        "(1,)",               # single  (the FAIL_TO_PASS case)
        "(1, 2, 3)",          # many    (PASS_TO_PASS)
        "(a,)",
        "('s',)",
        "(object(),)",
        "(1, 2)",
        "(a, b, c, d)",
        "((1, 2), 3)",        # nested tuple as a member
        "((1,),)",            # single nested single-tuple
        "(None,)",
        "(..., 1)",
    ]
    for src in boundary:
        node = _outer_tuple(ast.parse(src, mode="eval").body)
        if node is not None:
            yield node
    for _ in range(n):
        arity = rng.randint(0, 6)
        elems = [fuzz_elem_pool(rng) for _ in range(arity)]
        src = make_tuple_source(elems)
        try:
            node = _outer_tuple(ast.parse(src, mode="eval").body)
        except SyntaxError:
            continue
        if node is not None:
            yield node


def _outer_tuple(node):
    return node if isinstance(node, ast.Tuple) else None


def main():
    # The real patched callee (gold patch already applied by the orchestrator).
    from sphinx.pycode.ast import unparse

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for node in fuzz_nodes(N_FUZZ, rng):
        count += 1
        images = [unparse(e) for e in node.elts]   # unchanged recursive renderer
        shadow = shadow_render(images)              # R/I shadow of the impl
        oracle = unparse(node)                      # real patched visit_Tuple
        if shadow != oracle:
            disagreements.append((ast.dump(node), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d tuple nodes:"
              % (len(disagreements), count))
        for dump, sh, orc in disagreements:
            print("  node=%s shadow=%r oracle=%r" % (dump, sh, orc))
        return 1

    print("G-CONF OK: R/I shadow of renderSequence agrees with patch.diff "
          "behaviour (real visit_Tuple) on %d tuple nodes (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
