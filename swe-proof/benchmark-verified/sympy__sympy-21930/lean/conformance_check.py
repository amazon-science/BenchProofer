#!/usr/bin/env python3
"""G-CONF: differential conformance for sympy__sympy-21930.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the three Lean
`implementation_*Markup` skeletons and diffs it against the REAL patched
`_latex` output of the three carriers over the boundary catalogue plus >=1e5
randomized draws.

  observables (each renderer, post-patch):
    * AntiSymmetricTensor._latex  ->  "{<sym>^{<join upper>}_{<join lower>}}"
    * CreateBoson._latex          ->  "{b^\\dagger_{<name>}}"
    * CreateFermion._latex        ->  "{a^\\dagger_{<name>}}"

The shadow assembles each string the same way the Lean impl does (empty-string
join of index names, then enclose the token in one outer brace pair) from the
SAME data the real object carries (`obj.symbol`, `obj.args[1/2]` names,
`obj.state.name`). Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned
seed).
"""
import random
import sys

SEED = 21930
N_RANDOM = 120_000  # >= 1e5, spread across the three renderers


# ---- Python shadow of the Lean impls ---------------------------------------

def shadow_join(names):
    # Lean: joinNames []=="" ; (x::xs)==x ++ joinNames xs  (== "".join(names))
    out = ""
    for n in names:
        out = out + n
    return out


def shadow_tensor(sym, upper_names, lower_names):
    # Lean implementation_tensorMarkup
    up = shadow_join(upper_names)
    lo = shadow_join(lower_names)
    return "{" + sym + "^{" + up + "}_{" + lo + "}}"


def shadow_boson(name):
    # Lean implementation_bosonCreatorMarkup
    return "{b^\\dagger_{" + name + "}}"


def shadow_fermion(name):
    # Lean implementation_fermionCreatorMarkup
    return "{a^\\dagger_{" + name + "}}"


# ---- real callee observation ------------------------------------------------

def real_tensor(AntiSymmetricTensor, Symbol, sym, upper, lower):
    """Build the real tensor and return (real_latex, shadow_latex) using the
    object's own canonical args (so the comparison isolates the string-assembly
    behaviour, including the outer brace pair)."""
    obj = AntiSymmetricTensor(Symbol(sym),
                              tuple(Symbol(n) for n in upper),
                              tuple(Symbol(n) for n in lower))
    # canonicalisation may negate / zero; only a genuine tensor has _latex.
    if not hasattr(obj, "_latex") or obj.func.__name__ != "AntiSymmetricTensor":
        return None, None
    real = obj._latex(None)
    up_names = [i.name for i in obj.args[1]]
    lo_names = [i.name for i in obj.args[2]]
    shadow = shadow_tensor("%s" % obj.symbol, up_names, lo_names)
    return real, shadow


def main():
    try:
        from sympy import Symbol
        from sympy.physics.secondquant import AntiSymmetricTensor, Bd, Fd
    except Exception as e:  # pragma: no cover
        print(f"status=fail could not import callees: {e!r}")
        return 1

    disagreements = 0
    checked = 0

    def report(kind, key, real, shadow):
        nonlocal disagreements
        if real != shadow:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH [{kind}] {key!r}: real={real!r} shadow={shadow!r}")

    # name alphabets: sympy symbol names are plain identifiers/labels; include
    # digits (the issue uses Symbol('0')) and a few non-ASCII points.
    name_alpha = list("abcdefghijkABXY0123456789") + ["α", "β", "ψ"]
    boundary_names = ["0", "1", "a", "i", "p", "ab", "ij", "x12", "αβ", "Z"]

    rng = random.Random(SEED)

    def rand_name():
        length = rng.randint(1, 4)
        return "".join(rng.choice(name_alpha) for _ in range(length))

    # ---- boundary catalogue ----
    for nm in boundary_names:
        real = Bd(Symbol(nm))._latex(None)
        report("boson", nm, real, shadow_boson(nm))
        checked += 1
        real = Fd(Symbol(nm))._latex(None)
        report("fermion", nm, real, shadow_fermion(nm))
        checked += 1
    for sym in ["t", "v", "f", "A"]:
        for up in [[], ["a"], ["a", "b"]]:
            for lo in [[], ["i"], ["i", "j"]]:
                r, s = real_tensor(AntiSymmetricTensor, Symbol, sym, up, lo)
                if r is not None:
                    report("tensor", (sym, up, lo), r, s)
                    checked += 1

    # ---- randomized fuzz, split across the three renderers ----
    per = N_RANDOM // 3
    for _ in range(per):
        nm = rand_name()
        report("boson", nm, Bd(Symbol(nm))._latex(None), shadow_boson(nm))
        checked += 1
    for _ in range(per):
        nm = rand_name()
        report("fermion", nm, Fd(Symbol(nm))._latex(None), shadow_fermion(nm))
        checked += 1
    for _ in range(N_RANDOM - 2 * per):
        sym = rand_name()
        nu = rng.randint(0, 4)
        nl = rng.randint(0, 4)
        up = [rand_name() for _ in range(nu)]
        lo = [rand_name() for _ in range(nl)]
        r, s = real_tensor(AntiSymmetricTensor, Symbol, sym, up, lo)
        if r is not None:
            report("tensor", (sym, up, lo), r, s)
            checked += 1

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
