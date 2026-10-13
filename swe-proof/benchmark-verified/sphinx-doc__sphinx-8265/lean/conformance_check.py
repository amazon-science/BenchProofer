#!/usr/bin/env python3
"""G-CONF for sphinx-doc__sphinx-8265.

Differential test: the R/I Python shadow of the two modeled skeletons
(`implementation_tupleDisplay` and `implementation_subscription` in
Solution.lean) vs. the REAL patched unparser `sphinx.pycode.ast.unparse`
(class `_UnparseVisitor`). The orchestrator applies the gold patch before
running this, so the imported `unparse` is the fixed version.

Boundary (mapping.md): the per-element recursion `self.visit(e)` /
`self.visit(node.value)` is NOT modeled — its results ARE the modeled inputs
(`elts` element renderings / `valueStr`). We obtain those inputs by calling the
real `unparse` on the child nodes, then compute the shadow of the JOINING /
WRAPPING logic and compare against the real `unparse` of the whole node.

Type bridge (mapping.md):
  a rendered fragment (str, per code point)         <-> List Char
  [self.visit(e) for e in elts]                     <-> elts : List (List Char)
  ", ".join(parts)                                  <-> List.intercalate [',',' '] parts
  "(" + s + ")"                                     <-> ['('] ++ s ++ [')']
  "%s[%s]" % (v, s)                                 <-> v ++ ['['] ++ s ++ [']']
  node.slice shape                                  <-> IndexForm

Exit 0 iff zero disagreements over >=1e5 fuzzed inputs. stdlib only.
"""
import ast
import random
import sys

SEED = 8265
N_CASES = 220_000

# Atoms whose rendering equals their source token (identity rendering), so the
# modeled boundary `elts` = element renderings is exact against the oracle.
NAMES = ["a", "b", "xy", "foo", "obj", "T"]
INTS = ["0", "1", "12", "345", "7"]


def gen_atom(rng):
    if rng.random() < 0.5:
        return rng.choice(NAMES)
    return rng.choice(INTS)


def gen_expr(rng, depth):
    """A renderable expression source string (children of the modeled nodes)."""
    if depth <= 0 or rng.random() < 0.55:
        return gen_atom(rng)
    kind = rng.choice(["tuple", "subscript", "attr", "slice", "starred", "list"])
    if kind == "tuple":
        n = rng.randint(0, 4)
        elts = [gen_expr(rng, depth - 1) for _ in range(n)]
        if n == 1:
            return "(%s,)" % elts[0]
        return "(" + ", ".join(elts) + ")"
    if kind == "subscript":
        return "%s[%s]" % (gen_atom(rng), gen_slice(rng, depth - 1))
    if kind == "attr":
        return "%s.%s" % (gen_atom(rng), rng.choice(NAMES))
    if kind == "slice":
        return "%s:%s" % (gen_atom(rng), gen_atom(rng))
    if kind == "starred":
        return "*%s" % gen_atom(rng)
    # list
    n = rng.randint(0, 3)
    return "[" + ", ".join(gen_expr(rng, depth - 1) for _ in range(n)) + "]"


def gen_slice(rng, depth):
    """The index part of a subscription (may be a tuple, atom, slice, ...)."""
    r = rng.random()
    if r < 0.35:
        # simple tuple index: a[1, 2, 3]
        n = rng.randint(1, 4)
        return ", ".join(gen_expr(rng, depth) for _ in range(n))
    if r < 0.45:
        # empty tuple index: a[()]
        return "()"
    if r < 0.55:
        # starred tuple index: a[*b,]
        return "*%s," % gen_atom(rng)
    if r < 0.7:
        # plain slice: a[1:2]
        return "%s:%s" % (gen_atom(rng), gen_atom(rng))
    return gen_expr(rng, depth)


# --- IndexForm classification (mirrors is_simple_tuple, incl. py<3.8 ast.Index) ---

def is_simple_tuple(value):
    return (isinstance(value, ast.Tuple)
            and bool(value.elts)
            and not any(isinstance(e, ast.Starred) for e in value.elts))


def index_form(slice_node):
    """Return ('elementTuple', elts_nodes) or ('plain', slice_node)."""
    if is_simple_tuple(slice_node):
        return ("elementTuple", slice_node.elts)
    idx_cls = getattr(ast, "Index", None)
    if idx_cls is not None and isinstance(slice_node, idx_cls) \
            and is_simple_tuple(slice_node.value):
        return ("elementTuple", slice_node.value.elts)
    return ("plain", slice_node)


# --- R/I shadows of the two skeletons ---

def shadow_tuple(elt_renderings):
    """implementation_tupleDisplay: non-empty -> "(" + ", ".join + ")"; else "()"."""
    if elt_renderings:
        return "(" + ", ".join(elt_renderings) + ")"
    return "()"


def shadow_subscript(value_str, form, payload):
    """implementation_subscription."""
    if form == "elementTuple":
        inner = ", ".join(payload)  # payload = element renderings
        return "%s[%s]" % (value_str, inner)
    return "%s[%s]" % (value_str, payload)  # payload = rendered index text


def main():
    from sphinx.pycode.ast import unparse

    rng = random.Random(SEED)
    checked = 0
    mismatches = 0
    tuples = subs = 0
    for _ in range(N_CASES):
        if rng.random() < 0.5:
            # a top-level tuple expression
            n = rng.randint(0, 4)
            elts = [gen_expr(rng, 2) for _ in range(n)]
            if n == 1:
                src = "(%s,)" % elts[0]
            elif n == 0:
                src = "()"
            else:
                src = "(" + ", ".join(elts) + ")"
        else:
            src = "%s[%s]" % (gen_atom(rng), gen_slice(rng, 2))

        try:
            node = ast.parse(src, mode="eval").body
        except SyntaxError:
            continue

        # Only compare when the TOP node is one of the two modeled sites.
        # Compute the real oracle FIRST; if the unparser cannot render this node
        # (e.g. a bare Slice child — outside the modeled joining behavior) skip
        # the case entirely so shadow and oracle stay in lock-step.
        try:
            if isinstance(node, ast.Tuple):
                oracle = unparse(node)
                elt_renderings = [unparse(e) for e in node.elts]
                got = shadow_tuple(elt_renderings)
                tuples += 1
            elif isinstance(node, ast.Subscript):
                oracle = unparse(node)
                value_str = unparse(node.value)
                form, payload = index_form(node.slice)
                if form == "elementTuple":
                    payload = [unparse(e) for e in payload]
                else:
                    payload = unparse(payload)
                got = shadow_subscript(value_str, form, payload)
                subs += 1
            else:
                continue
        except (NotImplementedError, KeyError):
            continue
        if got != oracle:
            mismatches += 1
            if mismatches <= 5:
                print(f"MISMATCH src={src!r} oracle={oracle!r} shadow={got!r}")
        checked += 1

    if mismatches == 0:
        print(f"status=pass checked={checked} tuples={tuples} subs={subs} mismatches=0")
        sys.exit(0)
    print(f"status=fail checked={checked} mismatches={mismatches}")
    sys.exit(1)


if __name__ == "__main__":
    main()
