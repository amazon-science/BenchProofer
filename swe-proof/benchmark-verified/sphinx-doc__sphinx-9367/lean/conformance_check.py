#!/usr/bin/env python3
"""G-CONF for sphinx-doc__sphinx-9367.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_renderTuple` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`sphinx.pycode.ast.unparse`, over >=1e5 fuzzed tuple expressions. Zero
disagreements => exit 0.

Model (refinement.md): a tuple's rendered text is a pure function of the rendered
text of its components and their count:

    elts == 0  -> "()"
    elts == 1  -> "(" + e0 + ",)"          (the fixed trailing-comma case)
    elts >= 2  -> "(" + ", ".join(elts) + ")"

where each component is rendered by the unchanged recursive per-component visit.

  * Oracle  = the REAL patched `unparse(tuple_node)` for a randomly built tuple.
  * Shadow  = arity branch applied to [unparse(e) for e in tuple_node.elts]
              (the A-reference per-component visit is the REAL recursive visitor).

Type bijection (mapping.md): elts<->[self.visit(e) for e in node.elts] (list of
str), elts.length<->len(node.elts) (int), result<->returned source text (str).
stdlib-only; no hypothesis required.
"""
import ast
import random
import sys

# The repo package is importable from /testbed (gold patch already applied).
from sphinx.pycode import ast as sphinx_ast


def shadow_wrap(rendered_elts):
    """R/I transliteration of implementation_renderTuple (Lean).

    rendered_elts is [unparse(e) for e in node.elts] -- the A-reference
    per-component visit applied to each component.
    """
    n = len(rendered_elts)
    if n == 0:
        return "()"
    elif n == 1:
        return "(" + rendered_elts[0] + ",)"
    else:
        return "(" + ", ".join(rendered_elts) + ")"


# --- component-expression generators (kept to grammar visit_Tuple can unparse) -
ATOMS = ["1", "a", "1.5", "'str'", "b'b'", "True", "None", "x.y", "-1", "+ a",
         "not a", "~ x", "...", "object()", "[1, 2]", "{1, 2}", "{'k': 1}",
         "1234", "0", "lambda x: ..."]


def gen_elt(rng, depth):
    """Generate a source expression string for one tuple component."""
    if depth <= 0 or rng.random() < 0.6:
        return rng.choice(ATOMS)
    # nested tuple component -- exercises recursion through the patched visitor
    k = rng.randint(0, 3)
    inner = [gen_elt(rng, depth - 1) for _ in range(k)]
    if k == 1:
        return "(" + inner[0] + ",)"
    return "(" + ", ".join(inner) + ")"


def build_tuple_source(rng):
    """Build a parseable tuple-expression source and its element count."""
    n = rng.choices([0, 1, 2, 3, 4, 5], weights=[2, 4, 3, 2, 1, 1])[0]
    elts = [gen_elt(rng, depth=2) for _ in range(n)]
    if n == 0:
        return "()"
    elif n == 1:
        return "(" + elts[0] + ",)"
    else:
        return "(" + ", ".join(elts) + ")"


def main():
    rng = random.Random(9367)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    checked = 0
    for _ in range(N):
        src = build_tuple_source(rng)
        try:
            module = ast.parse(src)
            node = module.body[0].value  # the expression
        except (SyntaxError, AttributeError, IndexError):
            continue
        if not isinstance(node, ast.Tuple):
            continue
        checked += 1
        # Oracle: real patched unparse of the whole tuple node.
        o = sphinx_ast.unparse(node)
        # Shadow: arity wrap/join over the REAL per-component visit.
        rendered_elts = [sphinx_ast.unparse(e) for e in node.elts]
        s = shadow_wrap(rendered_elts)
        if o != s:
            disagreements += 1
            if first is None:
                first = (src, o, s)
    if checked == 0:
        print("G-CONF FAIL: no tuple inputs generated")
        return 1
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, checked, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
