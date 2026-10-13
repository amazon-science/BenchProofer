#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_safeRepresentative against the patch.diff behaviour (the
post-patch representative-selection inside `_convert_dx`).

The impl region is NOT all-A-tagged (it has the I-tagged loop-exhaustion control
flow). Its A-reference ops (the finiteness scan, the first-element fall-back, and
the lone-coordinate identity route) are left as the REAL repo callees
`cbook._safe_first_finite` / `cbook.safe_first_element` — exactly what the
post-patch code calls. The shadow therefore reproduces the post-patch selection
op-for-op; we assert zero disagreements vs an independent reconstruction of the
patched selection over >=10^5 fuzzed inputs, across BOTH argument shapes.

Runs in-container (numpy + matplotlib.cbook). exit 0 iff zero disagreements.
"""
import datetime
import decimal
import math
import random
import sys

import numpy as np
from matplotlib import cbook

SEED = 24149
N = 120_000          # >= 10^5


def shadow(arg):
    """R/I shadow of implementation_safeRepresentative.

        match arg with
        | .single v   => some v
        | .sequence vs => for v in vs: if v.countsAsFinite: return some v
                          return vs.head?

    The A-reference ops are realised by the REAL callees: the finite scan is
    `_safe_first_finite` (StopIteration == no finite; TypeError == not a
    sequence, so the argument stands for itself), the non-empty fall-back is
    `safe_first_element`."""
    kind, payload = arg
    if kind == "sequence":
        # Sequences are passed VERBATIM unless every value is a plain number, so
        # the regimes on which the real per-value ruling differs from bare
        # arithmetic finiteness are reachable here rather than coerced away.
        if len(payload) == 0:
            return ("none", None)
        if all(isinstance(v, (int, float, np.number)) and not isinstance(v, bool)
               for v in payload):
            target = np.asarray(payload, dtype=float)
        else:
            target = list(payload)
    else:
        target = payload
    try:
        return ("some", cbook._safe_first_finite(target))
    except (TypeError, IndexError, KeyError):
        return ("some", target)
    except StopIteration:
        return ("some", cbook.safe_first_element(target))


def counts_as_finite(val):
    """`CoordVal.countsAsFinite`: the per-value ruling, settled by REGIME.

      a value the test can weigh as a quantity -> weighed (IEEE-754 finiteness)
      a value it cannot weigh                  -> counts REGARDLESS
      a missing value                          -> never counts
    """
    if val is None:                       # .missing
        return False
    if np.isscalar(val):
        try:
            return bool(np.isfinite(val))     # .numeric — weighed
        except TypeError:
            return True                       # .unweighable — counts anyway
    return True                               # .unweighable — counts anyway


def patched_selection(arg):
    """Independent reconstruction of the post-patch `_convert_dx` selection: a
    lone coordinate stands for itself; a sequence yields its first value that
    COUNTS AS FINITE, else its first value unconditionally, else (empty) none."""
    kind, payload = arg
    if kind == "single":
        return ("some", payload)
    seq = payload
    for v in seq:
        if counts_as_finite(v):
            return ("some", v)
    if len(seq) > 0:
        return ("some", seq[0])
    return ("none", None)


def feq(a, b) -> bool:
    if a[0] != b[0]:
        return False
    if a[0] == "none":
        return True
    x, y = a[1], b[1]
    if isinstance(x, (float, np.floating)) and isinstance(y, (float, np.floating)):
        return (math.isnan(float(x)) and math.isnan(float(y))) or float(x) == float(y)
    return x == y or repr(x) == repr(y)


def main() -> int:
    rng = random.Random(SEED)
    NONFIN = [float("nan"), float("inf"), float("-inf")]
    FIN = [0.0, -0.0, 1.0, -1.0, 3.14, -2.5, 1e9, -1e-9, 42.0, 7.0]
    alphabet = NONFIN * 4 + FIN

    D = datetime.datetime(2018, 1, 1)
    DT = datetime.timedelta(hours=3)
    fixed_seqs = [
        [], [float("nan")], [float("nan"), 1.0],
        [float("inf"), float("-inf")], [float("nan"), float("nan"), 2.0],
        [1.0, float("nan")], [0.0], [-0.0, float("nan")],
        # the mixed-REGIME sequences: the class on which bare arithmetic
        # finiteness diverges from the ruling the step really applies.
        [D, D], [D, 2.0], [2.0, D], [float("nan"), D], [D, float("nan")],
        [DT, D], [decimal.Decimal("1.5"), 2.0], ["a", 2.0],
        [None, 2.0], [None], [None, None], [None, D], [None, float("nan")],
        [np.asarray(float("nan")), 2.0], [D, None, 2.0], [None, D, 2.0],
    ]
    cases = [("sequence", s) for s in fixed_seqs]
    cases += [
        ("sequence", [rng.choice(alphabet) for _ in range(rng.randint(0, 8))])
        for _ in range(N)
    ]
    EXOTIC = [D, DT, datetime.date(2018, 1, 1), decimal.Decimal("1.5"), "a",
              np.asarray(float("nan"))]
    mixed = alphabet + EXOTIC * 3 + [None] * 3
    cases += [
        ("sequence", [rng.choice(mixed) for _ in range(rng.randint(1, 6))])
        for _ in range(40_000)
    ]

    # The lone-coordinate shape: the route on which the placement of the
    # fall-back call is observable, so it is fuzzed alongside the sequences.
    fixed_singles = [
        1.0, -1.0, 0.0, -0.0, 42.0,
        float("nan"), float("inf"), float("-inf"),
        1e308, 5e-324,
    ]
    cases += [("single", v) for v in fixed_singles]
    cases += [("single", rng.choice(alphabet)) for _ in range(30_000)]

    disagreements = 0
    examples = []
    for arg in cases:
        got = shadow(arg)
        want = patched_selection(arg)
        if not feq(got, want):
            disagreements += 1
            if len(examples) < 10:
                examples.append((arg, got, want))

    # Non-float lone coordinates take the SAME identity route in the real code.
    # The model abstracts their value (the selection never inspects it); what is
    # checked is that a representative is produced and it is the argument itself.
    exotic = [
        3, -7, np.float64(2.0), np.int64(5),
        np.asarray(1.0), np.asarray(float("nan")),
        datetime.datetime(2018, 1, 1), datetime.date(2018, 1, 1),
    ]
    for v in exotic:
        got = shadow(("single", v))
        if got[0] != "some" or not (got[1] is v or repr(got[1]) == repr(v)):
            disagreements += 1
            if len(examples) < 10:
                examples.append((("single", v), got, ("some", v)))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for s, g, w in examples:
            print(f"  in={s!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases) + len(exotic)} inputs across both argument "
          f"shapes, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
