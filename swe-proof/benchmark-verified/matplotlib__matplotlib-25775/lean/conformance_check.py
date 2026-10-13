#!/usr/bin/env python3
"""G-CONF for matplotlib__matplotlib-25775.

Differential test: the R/I shadow of `implementation_textAntialiased` (the Lean
impl mirrored in Python) vs. the REAL patched matplotlib behavior of the
per-object antialiasing resolution, observed at the `Text` get/set boundary.

Input space (mapping.md):
  rcDefault : bool          -- rcParams['text.antialiased']
  ctorArg   : None|True|False  -- Text(..., antialiased=ctorArg)
  laterSet  : None|True|False  -- optional later set_antialiased(laterSet)

Observation: get_antialiased() (== Text._antialiased).

The finite space is 2*3*3 = 18 combos; we enumerate it exhaustively, then fuzz
>=1e5 random draws from the same space. Exit 0 iff zero disagreements.
stdlib-only (plus matplotlib, which is the system-under-test).
"""
import json
import random
import sys

SEED = 25775
FUZZ = 120_000


def shadow(rc_default, ctor_arg, later_set):
    """R-shadow of implementation_textAntialiased (Solution.lean impl region)."""
    acc = rc_default
    if ctor_arg is not None:
        acc = ctor_arg
    if later_set is not None:
        acc = later_set
    return acc


def real(rc_default, ctor_arg, later_set, mpl, Text):
    """Observed behavior of the real patched Text object."""
    mpl.rcParams['text.antialiased'] = rc_default
    txt = Text(0.5, 0.5, "foo\nbar", antialiased=ctor_arg)
    if later_set is not None:
        txt.set_antialiased(later_set)
    return bool(txt.get_antialiased())


def main():
    try:
        import matplotlib as mpl
        mpl.use("Agg")
        from matplotlib.text import Text
    except Exception as e:  # pragma: no cover
        print(json.dumps({"status": "error", "reason": f"import failed: {e!r}"}))
        return 2

    rng = random.Random(SEED)
    rc_choices = [True, False]
    opt_choices = [None, True, False]

    disagreements = []
    checked = 0

    # Exhaustive enumeration of the finite space.
    cases = [(rc, ca, ls)
             for rc in rc_choices
             for ca in opt_choices
             for ls in opt_choices]
    # Plus fuzz draws.
    for _ in range(FUZZ):
        cases.append((rng.choice(rc_choices),
                      rng.choice(opt_choices),
                      rng.choice(opt_choices)))

    for rc, ca, ls in cases:
        exp = bool(shadow(rc, ca, ls))
        got = real(rc, ca, ls, mpl, Text)
        checked += 1
        if exp != got:
            disagreements.append({"rcDefault": rc, "ctorArg": ca,
                                  "laterSet": ls, "shadow": exp, "real": got})
            if len(disagreements) >= 10:
                break

    ok = not disagreements
    print(json.dumps({"status": "ok" if ok else "fail",
                      "checked": checked,
                      "disagreements": disagreements[:10]}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
