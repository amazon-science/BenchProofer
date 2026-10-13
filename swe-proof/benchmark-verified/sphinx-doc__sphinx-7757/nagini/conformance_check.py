#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7757 (nagini).

SHADOW: the impl region of model.py (`resolve_positional_defaults`), copied
VERBATIM below with the contract calls (Requires/Ensures/Invariant/Assert)
stripped, plus the @Pure helpers (`EMPTY`, `first_default_pos`,
`resolved_default`) copied over as plain functions. `ToSeq` (kept because the
impl assigns `old_seq = ToSeq(result)` as a regular statement) is shimmed as
`tuple`. The two @ContractOnly callees call the REAL repo function:

  * `render(value_code)`  -> `sphinx.pycode.ast.unparse` applied to the
    default-expression AST node the value code denotes (mapping.md section 2:
    a value code stands for one supplied default expression; its rendered
    source form is opaque to the alignment).
  * `renderable(value_code)` -> membership in the real renderer's domain of
    definedness (the real callee returns rather than raises on the node).

ORACLE: the REAL patched repo function the model models per mapping.md —
`sphinx.util.inspect.signature_from_str` at /testbed with the gate having
applied patch.diff. For each input the oracle parses a signature string with
`positionals` positional parameters (`posonly` of them before the '/'), the
last `m` of which carry the chosen default expressions, and reads back each
positional parameter's `default` slot in order.

Input/output bridge (mapping.md section 2):
  * a positional parameter list is abstracted to the two counts
    (positionals, posonly); parameter names are irrelevant to the modeled
    behaviour, so synthetic names p0..p{n-1} are used.
  * `provided: List[int]` of value codes <-> the trailing default
    expressions in source order; value code j indexes a fixed table of
    renderable default expressions (all codes >= 0, distinct from the
    sentinel).
  * `EMPTY()` (= -1) <-> `Parameter.empty`; a rendered default <-> the
    parameter's `default` string. The oracle's per-position default slot is
    mapped to -1 when `Parameter.empty` and to the string otherwise, then
    compared element-wise against the shadow's returned list (whose entries
    are -1 or the string produced by the same real renderer).

Input domain (the model's Requires): 0 <= posonly <= positionals,
len(provided) <= positionals, every provided value code renderable. All
generated inputs satisfy it by construction; Python's grammar accepts every
such signature because the defaulted parameters form a trailing block of the
whole positional list.

Boundary cases: exhaustive shape enumeration (posonly 0..4 x regular 0..4 x
every trailing default-block size) with cyclic value codes, plus every
value-code assignment for all shapes with at most 2 defaults, plus the
headline one-shared-prefix shape. Fuzz: 100000 random shapes (up to 6
positional parameters) with random renderable value codes. Total >= 1e5
Requires-satisfying inputs. Pinned fuzz seed: 775701.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plus the repo package under test).
"""
import ast
import json
import random
import sys

from sphinx.util.inspect import signature_from_str
from sphinx.pycode.ast import unparse as ast_unparse

try:
    from inspect import Parameter
except Exception:  # pragma: no cover
    from sphinx.util.inspect import Parameter  # type: ignore

SEED = 775701
N_FUZZ = 100_000
POSITIONAL = (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)

# The value-code table: value code j denotes the j-th default expression.
# Every entry lies in the real renderer's domain (renderable); codes are
# non-negative, so none collides with the EMPTY sentinel (-1).
EXPRS = ["0", "1", "None", "True", "'x'", "3.14", "(1, 2)", "[1]",
         "{1: 2}", "foo.BAR", "-1", "1 + 2", "lambda x: x", "a and b",
         "{1, 2}", "b'bytes'"]


# --- bridges for the @ContractOnly callees: call the REAL repo renderer ------

def _node_for(value_code):
    return ast.parse(EXPRS[value_code], mode="eval").body


_RENDER_CACHE = {}


def render(value_code):
    """REAL callee: the repo's per-default AST renderer applied to the node
    this value code denotes. Cached — the callee is deterministic (@Pure),
    validated by axiom_check.py."""
    if value_code not in _RENDER_CACHE:
        _RENDER_CACHE[value_code] = ast_unparse(_node_for(value_code))
    return _RENDER_CACHE[value_code]


def renderable(value_code):
    """REAL domain check: the renderer returns (rather than raises) on the
    node this value code denotes."""
    if not (0 <= value_code < len(EXPRS)):
        return False
    try:
        render(value_code)
        return True
    except NotImplementedError:
        return False


# --- PSeq/ToSeq shim ----------------------------------------------------------

def ToSeq(x):
    return tuple(x)


# --- @Pure helpers from model.py, decorators + contracts stripped -------------

def EMPTY():
    return -1


def first_default_pos(n, m):
    return n - m


def resolved_default(p, n, m, provided):
    if p < first_default_pos(n, m):
        return EMPTY()
    return render(provided[p - first_default_pos(n, m)])


# --- the impl region of model.py, verbatim, contracts stripped ----------------

def resolve_positional_defaults(positionals, posonly, provided):
    m = len(provided)
    pad = positionals - m
    result = []  # type: list
    p = 0
    while p < positionals:
        old_seq = ToSeq(result)
        if p < pad:
            result = result + [EMPTY()]
        else:
            result = result + [render(provided[p - pad])]
        p = p + 1
    return result


# --- the real-oracle bridge ----------------------------------------------------

def build_signature_str(positionals, posonly, provided):
    """Signature string with `positionals` positional parameters, the first
    `posonly` before a '/', the last len(provided) carrying the denoted
    default expressions. Defaults form a trailing block of the whole
    positional list, so the string is always grammar-valid."""
    m = len(provided)
    pad = positionals - m
    parts = []
    for p in range(positionals):
        nm = "p%d" % p
        if p < pad:
            parts.append(nm)
        else:
            parts.append("%s=%s" % (nm, EXPRS[provided[p - pad]]))
        if posonly and p == posonly - 1:
            parts.append("/")
    return "(" + ", ".join(parts) + ")"


def real_resolved_defaults(positionals, posonly, provided):
    """Run the REAL patched repo function and read back the per-position
    default slot of each positional parameter, bridged to the model carrier
    (-1 for the no-default sentinel, the default string otherwise)."""
    sig = signature_from_str(build_signature_str(positionals, posonly, provided))
    out = []
    for param in sig.parameters.values():
        if param.kind in POSITIONAL:
            out.append(EMPTY() if param.default is Parameter.empty
                       else param.default)
    return out


# --- the differential check ----------------------------------------------------

def check_one(positionals, posonly, provided):
    got = resolve_positional_defaults(positionals, posonly, list(provided))
    want = real_resolved_defaults(positionals, posonly, list(provided))
    if got != want:
        print("DISAGREEMENT")
        print("  input: positionals=%d posonly=%d provided=%r (signature %r)"
              % (positionals, posonly, list(provided),
                 build_signature_str(positionals, posonly, provided)))
        print("  shadow: %r" % (got,))
        print("  real:   %r" % (want,))
        return False
    return True


def main():
    # Input-domain guard: every value code in the table must satisfy the
    # model's precondition (renderable), or the generated inputs would fall
    # outside the Requires-satisfying domain.
    bad = [c for c in range(len(EXPRS)) if not renderable(c)]
    if bad:
        print("input-domain error: non-renderable value codes %r" % (bad,))
        return 2

    checked = 0

    # Boundary: exhaustive shapes, cyclic value codes ------------------------
    for k in range(0, 5):            # positional-only count
        for r in range(0, 5):        # ordinary positional count
            n = k + r
            for m in range(0, n + 1):
                provided = [j % len(EXPRS) for j in range(m)]
                if not check_one(n, k, provided):
                    return 1
                checked += 1

    # Boundary: all value-code assignments for small default blocks ---------
    for k in range(0, 4):
        for r in range(0, 4):
            n = k + r
            for m in range(0, min(n, 2) + 1):
                if m == 0:
                    continue  # covered above
                codes = range(len(EXPRS))
                if m == 1:
                    combos = [(c,) for c in codes]
                else:
                    combos = [(c1, c2) for c1 in codes for c2 in codes]
                for provided in combos:
                    if not check_one(n, k, provided):
                        return 1
                    checked += 1

    # Boundary: the headline shape (one undefaulted prefix slot, defaults
    # spanning the positional-only boundary)
    for provided in [(0, 1), (2, 3), (5, 12)]:
        if not check_one(3, 2, provided):
            return 1
        checked += 1

    n_boundary = checked

    # Fuzz -------------------------------------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        k = rng.randint(0, 3)
        r = rng.randint(0, 3)
        n = k + r
        m = rng.randint(0, n)
        provided = [rng.randrange(len(EXPRS)) for _ in range(m)]
        if not check_one(n, k, provided):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (resolve_positional_defaults) == real "
          "patched positional-default resolution on %d inputs (%d boundary + "
          "%d fuzz, seed %d)." % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
