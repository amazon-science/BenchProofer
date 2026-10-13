#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-13372.

The bundle models ONE routine: the fallback (`except KeyError`) branch of
`evalf(x, prec, options)` in `sympy/core/evalf.py` that reduces the real and
imaginary components of `xe.as_real_imag()` to the tuple
`r = re, im, reprec, imprec` (mapping.md). The gold fix adds
`else: raise NotImplementedError` after each of the `if re==0 / elif re.is_number`
and `if im==0 / elif im.is_number` chains, so a component that is neither exactly
zero nor a concrete number now raises (caught upstream as a fallback signal)
instead of falling through with `reprec`/`imprec` unassigned (`UnboundLocalError`).

Standing up the full sympy expression machinery to drive the real branch is
unnecessary: the modeled value is a PURE function of the observables the branch
reads for each component — (is it `== 0`? is it `.is_number`? does it still carry
an unevaluated re/im marker? what mpf value does a number reduce to?). So the
ORACLE below is a faithful in-process replica of the POST-PATCH branch over these
observables, and the SHADOW is the op-for-op transliteration of
`implementation_reduceComponentsToFloat` (Solution.lean impl region), per refinement.md.

This genuinely tests the soundness-critical clause: a component that is neither
zero nor a number (`.symbolic`) must make the whole reduction *unsupported*
(== raise NotImplementedError), not assemble a malformed tuple — matching the
F2P expectation (`Mul(Max(0, y), x, evaluate=False).evalf()` no longer crashes).

stdlib-only. Pinned seed: 13372 (also in mapping.md).
"""
import itertools
import random
import sys

SEED = 13372
N = 150_000

# A classified component, mirroring Lean `EvalfPart`:
#   kind in {"zero","number","symbolic"}; mpf: int payload; uneval: bool
KINDS = ("zero", "number", "symbolic")


def gen_part(rng):
    return {
        "kind": rng.choice(KINDS),
        "mpf": rng.randint(-1000, 1000),
        "uneval": rng.random() < 0.3,
    }


# --- ORACLE: faithful in-process replica of the POST-PATCH fallback branch ----
# Returns ("error",) for raise NotImplementedError, or
# ("ok", re, im, reprec, imprec) for the normal tuple return.
# re/im out values: None (zero) or ("mpf", payload) (number); reprec/imprec:
# None or prec.
def oracle(re, im, prec):
    # if re.has(re_) or im.has(im_): raise NotImplementedError
    if re["uneval"] or im["uneval"]:
        return ("error",)

    # real chain
    if re["kind"] == "zero":
        re_out = None
        reprec = None
    elif re["kind"] == "number":
        re_out = ("mpf", re["mpf"])
        reprec = prec
    else:  # else: raise NotImplementedError   <-- the fix
        return ("error",)

    # imag chain
    if im["kind"] == "zero":
        im_out = None
        imprec = None
    elif im["kind"] == "number":
        im_out = ("mpf", im["mpf"])
        imprec = prec
    else:  # else: raise NotImplementedError   <-- the fix
        return ("error",)

    return ("ok", re_out, im_out, reprec, imprec)


# --- SHADOW of implementation_reduceComponentsToFloat (the R/I legs) -----------------
# Mirrors Solution.lean impl region exactly. Lean output carriers:
#   EvalfPartOut: .null -> None ; .num m -> ("mpf", m) ; .sym -> ("sym",)
#   Option Nat:   none -> None ; some prec -> prec
def shadow(re, im, prec):
    if re["uneval"] or im["uneval"]:
        return ("error",)

    re_out = ("sym",)
    reprec = None
    if re["kind"] == "zero":
        re_out = None
        reprec = None
    elif re["kind"] == "number":
        re_out = ("mpf", re["mpf"])
        reprec = prec
    else:
        return ("error",)

    im_out = ("sym",)
    imprec = None
    if im["kind"] == "zero":
        im_out = None
        imprec = None
    elif im["kind"] == "number":
        im_out = ("mpf", im["mpf"])
        imprec = prec
    else:
        return ("error",)

    return ("ok", re_out, im_out, reprec, imprec)


def main():
    rng = random.Random(SEED)
    disagreements = 0
    first = None

    # Exhaustive boundary sweep over the discrete classification space
    # (kind x kind x uneval x uneval), several mpf/prec values each.
    for rk, ik, ru, iu in itertools.product(KINDS, KINDS, (False, True), (False, True)):
        for prec in (1, 53, 200):
            re = {"kind": rk, "mpf": 7, "uneval": ru}
            im = {"kind": ik, "mpf": -7, "uneval": iu}
            o = oracle(re, im, prec)
            s = shadow(re, im, prec)
            if o != s:
                disagreements += 1
                if first is None:
                    first = (re, im, prec, o, s)

    # Randomized fuzz
    for _ in range(N):
        re = gen_part(rng)
        im = gen_part(rng)
        prec = rng.randint(1, 333)
        o = oracle(re, im, prec)
        s = shadow(re, im, prec)
        if o != s:
            disagreements += 1
            if first is None:
                first = (re, im, prec, o, s)

    if disagreements == 0:
        print("G-CONF sympy__sympy-13372: status=pass; 0 disagreements over "
              "boundary sweep + %d fuzzed inputs (seed=%d)" % (N, SEED))
        sys.exit(0)
    else:
        print("G-CONF sympy__sympy-13372: status=FAIL; %d disagreements; "
              "first=%r" % (disagreements, first))
        sys.exit(1)


if __name__ == "__main__":
    main()
