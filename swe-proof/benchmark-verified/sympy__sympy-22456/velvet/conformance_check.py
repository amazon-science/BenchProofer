#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-22456 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo object (`String`), via the
              mapping.md bijection (`StrObj.text : List Char` ↔ the Python `str`
              text; a failed reconstruction call (exception) ↔ `none`; a call
              reproducing the object ↔ `some s`). The impl chooses the nullary
              `func` (FuncKind.nullarySelf) and the empty `kwargs()` view, then
              reports the two reconstruction outcomes (viaArgs / viaKwargs).
              The A-reference `exposedArgs == String.args` leg is NOT substituted
              by a model here; it stays with G-AX. (For this shadow it is read
              off the real object directly, see note below.)
  * ORACLE  — `patch.diff`'s behaviour: the patched `sympy.codegen.ast.String`
              applied at base_commit — its real `func(*args)`/`func(**kwargs())`
              reproduction (the real correctness oracle, G-RESOLVE).

They must agree on every input: the modeled reconstruction outcomes must equal
the real patched object's reconstruction outcomes. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib + sympy only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 22456
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean applyPos/applyKw/exposedArgs, translated ---
# This transliterates the Lean impl region of reconstructInvariance FAITHFULLY,
# routing through the SAME applyPos/applyKw call semantics — it is NOT a
# hardcoded outcome constant. A wrong impl choice (different FuncKind / kwNames /
# argument shape) changes the shadow, so G-CONF can witness an R/I break.
#
# The impl's choices (Solution.lean impl region): the method returns only the
# two structural choices (no echo-able outcome field), and the postcondition
# applies them through applyPos/applyKw:
#   out.kind    = FuncKind.noArgForm
#   out.kwNames = []
#   (C1) applyPos out.kind s (exposedArgs s) = some s   -- exposedArgs s = [] (A-ref)
#   (C2) applyKw  out.kind s out.kwNames     = some s
# This shadow recomputes the (C1)/(C2) verdicts by ROUTING those choices through
# apply_pos/apply_kw. Outcome tags: "self" = reproduced the object (some s);
# "fail" = call failed (none); "other" = reproduced a DIFFERENT object.

# FuncKind, modeling the reconstruction-function arity (Solution.lean `FuncKind`).
NO_ARG_FORM = "noArgForm"
ONE_ARG_FORM = "oneArgForm"

# The impl region's structural choices, lifted from Solution.lean verbatim.
IMPL_KIND = NO_ARG_FORM
IMPL_KWNAMES = []        # the chosen kwargs() view (empty)
IMPL_EXPOSED_ARGS = []   # exposedArgs s (A-reference; == String.args == ())


def apply_pos(kind, pos):
    """Solution.lean `applyPos`, translated. Returns "self"/"other"/"fail"."""
    if kind == NO_ARG_FORM:
        return "self" if pos == [] else "fail"
    else:  # ONE_ARG_FORM: needs exactly one positional value
        return "self" if len(pos) == 1 else "fail"


def apply_kw(kind, names):
    """Solution.lean `applyKw`, translated. Returns "self"/"fail"."""
    if kind == NO_ARG_FORM:
        return "self" if names == [] else "fail"
    else:  # ONE_ARG_FORM: accepts only the lone `text` keyword
        return "self" if names == ["text"] else "fail"


def shadow_reconstruct():
    """Returns (viaArgs, viaKwargs) by EXECUTING the Lean impl region's chosen
    ops through applyPos/applyKw — not a hardcoded constant.

        viaArgs   = applyPos IMPL_KIND IMPL_EXPOSED_ARGS
        viaKwargs = applyKw  IMPL_KIND IMPL_KWNAMES
    """
    via_args = apply_pos(IMPL_KIND, IMPL_EXPOSED_ARGS)
    via_kwargs = apply_kw(IMPL_KIND, IMPL_KWNAMES)
    return (via_args, via_kwargs)


def oracle_reconstruct(text):
    """patch.diff's behaviour: the patched String. Build the real instance and
    observe whether func(*args) and func(**kwargs()) reproduce it.

    "self" iff the call succeeds AND equals the object; "fail" iff it raises;
    "other" iff it returns a different object (would be a real divergence)."""
    from sympy.codegen.ast import String
    st = String(text)
    # func(*args)
    try:
        r = st.func(*st.args)
        via_args = "self" if r == st else "other"
    except Exception:
        via_args = "fail"
    # func(**kwargs())
    try:
        r2 = st.func(**st.kwargs())
        via_kwargs = "self" if r2 == st else "other"
    except Exception:
        via_kwargs = "fail"
    return (via_args, via_kwargs)


def fuzz_inputs(n, rng):
    # boundary cases first
    yield ""
    yield "foobar"
    yield "foo"
    yield "a"
    yield "text"            # the keyword name itself, as content
    yield "String('x')"
    yield " "
    yield "\t\n"
    yield "héllo"
    yield "x" * 64
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "0123456789 _-.,;:'\"<>&é•")
    for _ in range(n):
        k = rng.randint(0, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    shadow = shadow_reconstruct()   # constant over inputs (text only affects id)
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        oracle = oracle_reconstruct(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of reconstructInvariance (viaArgs=%r, "
          "viaKwargs=%r) agrees with patch.diff behaviour on %d inputs "
          "(seed=%d), 0 disagreements." % (shadow[0], shadow[1], count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
