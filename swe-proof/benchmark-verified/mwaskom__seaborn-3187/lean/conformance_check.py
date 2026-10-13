#!/usr/bin/env python3
"""G-CONF: differential conformance for mwaskom__seaborn-3187.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The bundle models ONE behavior at two sites: the values a
legend's numeric tick labels DENOTE. The soundness-critical decision the patch
changes is the COMPACTION STATE of the formatter used to produce those labels: a
freshly obtained `ScalarFormatter` defaults to subtracting a shared additive
offset and factoring out a power-of-ten scale, so a large-magnitude tick's label
denotes only a residual; the fix disables both, so each label denotes its tick.

ORACLE: the REAL post-patch `seaborn.utils.locator_to_legend_entries`
(seaborn/utils.py, the utils.py patch site — triple 2). It is a pure callable
needing no figure: given a matplotlib locator, axis limits, and a dtype it
returns `(raw_levels, formatted_levels)`. We parse each produced label back to
the value it denotes (`float(text)`) and require it to equal its tick exactly.

SHADOW: the op-for-op transliteration of `implementation_legendEntryLabels`
(Solution.lean impl region) — with compaction disabled, the denoted value of a
tick is the tick itself, so the shadow is `result == list(raw_levels)`.

Triple 1 (the scales.py site) produces labels the same way once its
`hasattr`-guarded switches are flipped off; its R legs are the same
disable-then-label-each-tick loop validated here. The discrete edge matrix +
fuzz exercises the large-offset / large-scale regimes that distinguish the fix
from the pre-patch behavior (compaction left on), so the differential test is
powerful enough to catch the bug (negative control below).

We restrict fuzzed ticks to the integer-valued "nice" levels real locators
produce (matching mapping.md's exact-rational bijection); `ScalarFormatter` with
compaction disabled prints those exactly, so `float(text) == tick` is an exact
comparison.

Exit 0 iff zero disagreements over the edge matrix + >=1e5 fuzzed draws.
stdlib-only fuzzing. Pinned seed: 3187.
"""
import json
import random
import sys

SEED = 3187
N_RANDOM = 120_000  # >= 1e5


# ---- SHADOW of implementation_legendEntryLabels ----------------------------
# Mirrors Solution.lean impl region exactly: compaction disabled, so each
# produced label denotes its tick value -> result == ticks (refinement.md).
def shadow_labels(ticks):
    compact_by_offset = False
    compact_by_scale = False
    out = []
    for x in ticks:
        # shownValue False False offset scale x == x
        out.append(x)
    return out


# ---- PREPATCH shadow (the bug): compaction left ON (negative control) -------
# Mirrors Solution_prepatch*.lean. Used ONLY to confirm the differential test
# can tell the bug apart from the fix on a large-offset configuration.
def prepatch_denoted(ticks, offset, scale):
    return [(x - offset) / scale for x in ticks]


def _import_oracle():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib as mpl
    from seaborn.utils import locator_to_legend_entries
    return mpl, locator_to_legend_entries


def _parse_denoted(text):
    """The numeric value a label denotes. ScalarFormatter renders the minus sign
    as Unicode U+2212 and may thin-space group digits; normalize to parse the
    value the label means (mapping.md: a label denotes float(text))."""
    t = (text.replace("−", "-")        # unicode minus -> ascii
              .replace(" ", "")          # thin space (digit grouping)
              .replace(" ", "")          # narrow no-break space
              .replace(",", "")               # comma grouping, if any
              .strip())
    return float(t)


def _run_oracle(mpl, locator_to_legend_entries, nbins, lo, hi):
    """Drive the REAL post-patch utils.py site. Returns (raw_levels, denoted)."""
    locator = mpl.ticker.MaxNLocator(nbins=nbins)
    raw_levels, formatted = locator_to_legend_entries(locator, (lo, hi), float)
    denoted = [_parse_denoted(t) for t in formatted]
    return raw_levels, denoted


def main():
    try:
        mpl, oracle = _import_oracle()
    except Exception as e:  # pragma: no cover
        print(json.dumps({"status": "error", "instance": "mwaskom__seaborn-3187",
                          "reason": f"import failed: {e!r}"}))
        return 2

    rng = random.Random(SEED)
    disagreements = []
    discriminated = False  # did at least one case separate fix from prepatch?
    checked = 0

    # ---- discrete edge matrix: large-offset / large-magnitude regimes -------
    # (nbins, lo, hi): integer limits so the locator yields integer "nice" ticks.
    edge = [
        (5, 0, 10),
        (6, 100_000_000, 100_001_000),     # the F2P 1e8-offset regime
        (5, 1_000_000_000, 1_000_010_000),
        (4, -5_000_000, 5_000_000),
        (6, 200_000_000, 200_000_500),
        (5, 999_900_000, 1_000_100_000),
        (3, 0, 1),
        (7, 123_456_000, 123_457_000),
    ]
    cases = list(edge)

    # ---- fuzz: random large integer offsets + integer spans -----------------
    for _ in range(N_RANDOM):
        nbins = rng.randint(2, 12)
        offset = rng.randint(-2_000_000_000, 2_000_000_000)
        span = rng.choice([100, 500, 1000, 5000, 10_000, 100_000, 1_000_000])
        lo = offset
        hi = offset + span
        cases.append((nbins, lo, hi))

    for nbins, lo, hi in cases:
        try:
            raw_levels, denoted = _run_oracle(mpl, oracle, nbins, lo, hi)
        except Exception as e:  # pragma: no cover
            disagreements.append({"case": [nbins, lo, hi], "error": repr(e)})
            continue
        if not raw_levels:
            continue
        checked += 1
        expected = shadow_labels(list(raw_levels))
        # exact comparison: with compaction off the label denotes its tick
        if denoted != expected:
            disagreements.append({
                "case": [nbins, lo, hi],
                "raw_levels": [float(x) for x in raw_levels],
                "oracle_denoted": denoted,
                "shadow": [float(x) for x in expected],
            })
        # negative control: would the PRE-patch behavior (compaction on, using
        # the offset the real formatter would pick) have differed here?
        if max(abs(float(x)) for x in raw_levels) > 1e7:
            # a nonzero offset is what ScalarFormatter would subtract; any
            # plausible large offset makes the prepatch denoted values differ.
            pre = prepatch_denoted([float(x) for x in raw_levels],
                                   offset=float(raw_levels[0]), scale=1.0)
            if pre != [float(x) for x in expected]:
                discriminated = True
        if len(disagreements) >= 5:
            break

    ok = (not disagreements) and discriminated and checked > 0
    print(json.dumps({
        "status": "pass" if ok else "fail",
        "instance": "mwaskom__seaborn-3187",
        "checked": checked,
        "fuzz_draws": N_RANDOM,
        "seed": SEED,
        "discriminates_prepatch": discriminated,
        "disagreements": disagreements[:5],
    }))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
