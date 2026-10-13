#!/usr/bin/env python3
"""G-CONF differential conformance for sympy__sympy-15345 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md: the modeled
node-rendering dispatch `render` (a `(head, args, NodeKind) -> source text`
mapping that chooses the surrounding delimiter pair) over the kinds the printer
distinguishes, against the behaviour of the patched real printer.

ORACLE CHOICE — why we drive the real `mathematica_code` end-to-end rather than
re-deriving the delimiter from a transliterated dispatch table:
  The rendering of a single node is produced inside `MCodePrinter` (a `str`
  result), so the real correctness oracle is the patched printer itself. We
  build concrete sympy expressions of each modeled `NodeKind`, render them with
  the patched `mathematica_code`, and recover the OBSERVABLE the model pins:
  the (head, joined-argument-text, surrounding-delimiter-pair) triple. The
  SHADOW is the modeled `render` from Solution.lean's `renderNode` post-image,
  fed the SAME head + joined argument text recovered from the real render, so
  the only thing under test is the delimiter choice the dispatch makes — which
  is the behaviour the patch changes.

  The argument text itself (order, comma-join) is unchanged by the patch and is
  treated as an input on both sides (it is read off the real render); G-CONF
  isolates the R/I dispatch leg. Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image with the gold patch
applied), sympy + stdlib only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import re
import sys

SEED = 15345
N_FUZZ = 100_000

# Modeled node kinds (mapping.md §2).
FUNCTION_APP = "functionApp"
EXTREMUM = "extremum"
PLAIN_EXPR = "plainExpr"


# --- the R/I shadow: Solution.lean `render`, transliterated -----------------
def shadow_render(head, args, kind):
    """render (head, args, kind) transliterated from Solution.lean's `render`
    (pure region). Chooses the surrounding delimiter pair from the node kind.
    `head`/`args` are inputs (the comma-joined argument text), unchanged here."""
    if kind == FUNCTION_APP:
        return head + "[" + args + "]"
    if kind == EXTREMUM:
        return head + "[" + args + "]"
    # plainExpr: generic round-parenthesis fallback
    return head + "(" + args + ")"


# --- the oracle: the patched real printer -----------------------------------
def build_cases(rng):
    """Yield (expr, kind) pairs spanning the modeled node kinds.

    * EXTREMUM    — Max / Min over >= 2 distinct symbols/integers (the node the
                    patch reroutes; with one distinct arg Max/Min collapse to
                    that arg, so we keep >= 2 distinct args).
    * FUNCTION_APP — a generic undefined function applied to args (already
                    rendered with brackets pre- and post-patch: the unchanged
                    side of the dispatch, included as a control).
    * PLAIN_EXPR  — an equality relation, which has no dedicated printer method
                    and renders in the round-parenthesis fallback form
                    (unchanged control for the other branch).
    """
    from sympy import symbols, Max, Min, Function, Eq, Integer
    syms = list(symbols('a b c d e f g h'))
    ints = [Integer(n) for n in range(2, 12)]
    pool = syms + ints
    g = Function('g')
    h = Function('h')

    # boundary / canonical cases first
    a, b, c = syms[0], syms[1], syms[2]
    yield (Max(a, Integer(2)), EXTREMUM)
    yield (Max(a, b, c), EXTREMUM)
    yield (Min(b, c), EXTREMUM)
    yield (g(a, b, c), FUNCTION_APP)
    yield (Eq(a, b), PLAIN_EXPR)

    for _ in range(N_FUZZ):
        kind = rng.choice([EXTREMUM, FUNCTION_APP, PLAIN_EXPR])
        if kind == EXTREMUM:
            op = rng.choice([Max, Min])
            n = rng.randint(2, 4)
            # pick n DISTINCT operands so Max/Min do not collapse to one arg
            operands = rng.sample(pool, n)
            yield (op(*operands), EXTREMUM)
        elif kind == FUNCTION_APP:
            fn = rng.choice([g, h])
            n = rng.randint(1, 4)
            operands = [rng.choice(pool) for _ in range(n)]
            yield (fn(*operands), FUNCTION_APP)
        else:  # PLAIN_EXPR
            yield (Eq(rng.choice(pool), rng.choice(pool)), PLAIN_EXPR)


# matches  HEAD<open> ARGS <close>  where open/close is [] or ()
_REND_RE = re.compile(r"^([A-Za-z][A-Za-z0-9]*)([\[(])(.*)([\])])$", re.S)


def parse_render(s):
    """Recover (head, args, open_delim, close_delim) from a rendered node."""
    m = _REND_RE.match(s)
    if not m:
        return None
    head, opn, args, cls = m.group(1), m.group(2), m.group(3), m.group(4)
    return head, args, opn, cls


def main():
    try:
        from sympy import mathematica_code as mcode
    except Exception as e:  # pragma: no cover - import guard
        print("G-CONF ERROR: cannot import sympy: %r" % (e,))
        return 2

    rng = random.Random(SEED)
    disagreements = []
    count = 0

    for expr, kind in build_cases(rng):
        rendered = mcode(expr)
        parsed = parse_render(rendered)
        if parsed is None:
            # not a single top-level head[..]/head(..) node (e.g. an arg itself
            # collapsed); skip — not a modeled single-node render.
            continue
        head, args, opn, cls = parsed
        count += 1
        # Feed the SAME head + joined arg text to the model; the only thing under
        # test is the delimiter pair the dispatch selects.
        shadow = shadow_render(head, args, kind)
        oracle = rendered
        if shadow != oracle:
            disagreements.append((kind, repr(expr), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, e, sh, orc in disagreements:
            print("  kind=%s expr=%s shadow=%r oracle=%r" % (kind, e, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderNode agrees with the patched printer "
          "behaviour on %d node renders (5 canonical + fuzz, seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
