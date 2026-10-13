#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-19346 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `printDict` / `printSet`
              impl regions transliterated to Python over the *real* repo
              carriers (`dict` / `set`, rendered `str`). The bijection
              (mapping.md §2): Lean `List Char` ↔ `str` char-for-char;
              `Obj.reprText` ↔ the recursive renderer `printer.doprint(e)`;
              a `dict` ↔ `List (Obj × Obj)` in `.items()` order; a `set` ↔
              `List Obj` in the object's own iteration order. The per-element
              recursive renderings fed to the shadow are taken from the REAL
              `ReprPrinter` — they are an unchanged rendering helper, part of
              the input carrier (R), not re-modeled here.
                dictRender items = "{" + ", ".join(doprint k + ": " + doprint v
                                                    for (k,v) in items) + "}"
                setRender elems  = "set()" if elems == [] else
                                   "{" + ", ".join(doprint e for e in elems) + "}"
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `ReprPrinter._print_dict` / `._print_set`, the actual Python the
              gold patch ships (the harness applies patch.diff at base_commit
              before this runs).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), where `sympy` is
importable and patch.diff is applied. stdlib + sympy only. The fuzz seed is
pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 19346
N_FUZZ = 100_000


# --- SHADOW: Solution.lean joinComma / dictRender / setRender, transliterated ---
def join_comma(fragments):
    """joinComma: interleave ", " between consecutive fragments; [] -> "",
    [x] -> x."""
    return ", ".join(fragments)


def shadow_dict(kv_texts):
    """dictRender items: "{" + joinComma (map kvText items) + "}", where each
    kvText is the recursive key rendering + ": " + the recursive value
    rendering (both already computed from the real renderer)."""
    return "{" + join_comma(kv_texts) + "}"


def shadow_set(elem_texts):
    """setRender elems: "set()" when empty, else "{" + joinComma elems + "}"."""
    if not elem_texts:
        return "set()"
    return "{" + join_comma(elem_texts) + "}"


def main():
    from sympy import srepr, Integer, Rational, Symbol
    from sympy.abc import x, y, z
    from sympy.printing.repr import ReprPrinter

    rng = random.Random(SEED)
    printer = ReprPrinter()

    def doprint(o):
        # the REAL unchanged recursive renderer (Obj.reprText, mapping.md §2)
        return printer.doprint(o)

    # A pool of sympy objects whose recursive srepr is stable.
    pool = [
        x, y, z, Symbol("a"), Symbol("name_1"),
        Integer(0), Integer(1), Integer(-2), Integer(42),
        Rational(1, 2), Rational(-3, 7),
        x + y, x * y, x ** 2, 2 * x + 1, x + y + z,
    ]

    disagreements = []
    count = 0

    def check_dict(d):
        nonlocal count
        count += 1
        # R: a dict <-> List (Obj x Obj) in .items() order; each component's
        # recursive rendering is the input carrier.
        kv_texts = ["%s: %s" % (doprint(k), doprint(v)) for k, v in d.items()]
        shadow = shadow_dict(kv_texts)
        oracle = printer._print_dict(d)          # patched _print_dict
        if shadow != oracle:
            disagreements.append(("dict", repr(d), shadow, oracle))

    def check_set(s):
        nonlocal count
        count += 1
        # R: a set <-> List Obj in the object's own iteration order. We iterate
        # the SAME object for shadow and oracle, so the order matches.
        elem_texts = [doprint(e) for e in s]
        shadow = shadow_set(elem_texts)
        oracle = printer._print_set(s)           # patched _print_set
        if shadow != oracle:
            disagreements.append(("set", repr(s), shadow, oracle))

    # --- boundary cases first (plan §4.1 step 4) -----------------------------
    boundary_dicts = [
        {},                                       # F2P: srepr({}) == "{}"
        {x: y},                                   # F2P: {Symbol('x'): Symbol('y')}
        {x: y, y: z},                             # F2P: two entries
        {x: {y: z}},                              # F2P: nested dict value
        {Integer(1): x, x: Integer(2)},
        {x + y: x * y},
    ]
    boundary_sets = [
        set(),                                    # srepr(set()) == "set()"
        {x},
        {x, y},
        {x, y, z},
        {Integer(1), Integer(2), x},
        frozenset({x, y}),
    ]
    for d in boundary_dicts:
        check_dict(d)
    for s in boundary_sets:
        check_set(s)

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(N_FUZZ):
        if rng.random() < 0.5:
            n = rng.randint(0, 5)
            keys = rng.sample(pool, min(n, len(pool)))
            d = {k: rng.choice(pool) for k in keys}
            check_dict(d)
        else:
            n = rng.randint(0, 5)
            s = set(rng.sample(pool, min(n, len(pool))))
            check_set(s)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, inp, sh, orc in disagreements:
            print("  %s=%s shadow=%r oracle=%r" % (kind, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of printDict/printSet agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
