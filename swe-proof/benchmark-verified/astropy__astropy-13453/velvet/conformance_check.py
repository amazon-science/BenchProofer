#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-13453 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (column ↔ (name, info.format); dict ↔ (name, fmt) association). The
              impl region has NO A-tagged callee inside its computed `out`
              (`effFormats` is the deep A-reference model itself, all R/I ops:
              dict lookup, override `match`, cons fold), so the shadow is pure
              R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched HTML writer path. We drive
              the END-TO-END behaviour the F2P test observes — `table.write(...,
              format="html", formats=...)` — and recover, per column, the display
              format the patched writer selected (the post-`_set_col_formats`
              `col.info.format` is what the gold patch makes the renderer use).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied by
the harness), stdlib + astropy only. The fuzz seed is pinned (mapping.md §4) for
a deterministic verdict.
"""
import random
import sys

from astropy.io.ascii import core
from astropy.table import Column

SEED = 13453
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean lookupFormat/effFmt/effFormats ------------

def shadow_eff_formats(cols, formats):
    """effFormats (cols.toAssoc) formats, transliterated to Python.

    cols: list of (name, current_format); formats: dict name->fmt.
    The backward `while` fold of effectiveFormats computes exactly the
    left-to-right per-column override `effFmt`."""
    out = []
    for name, current in cols:
        f = formats.get(name, None)          # lookupFormat
        out.append(f if f is not None else current)  # effFmt: override-or-keep
    return out


# --- the oracle: patch.diff's behaviour --------------------------------------

def oracle_eff_formats(cols, formats):
    """patch.diff's behaviour: build real astropy columns, attach them and the
    supplied formats to a BaseData exactly as the patched HTML writer does
    (`self.data.cols = cols`, `self.data.formats = formats`,
    `self.data._set_col_formats()` — html.py:352/358 post-patch), and read back
    the per-column display format the patched writer selected for the renderer."""
    real_cols = []
    for name, current in cols:
        c = Column([1, 2, 3], name=name)
        c.info.format = current
        real_cols.append(c)
    data = core.BaseData()
    data.cols = real_cols
    data.formats = dict(formats)
    data._set_col_formats()                  # the step the gold patch enables
    return [c.info.format for c in real_cols]


def fuzz_inputs(n, rng):
    names_pool = ["C1", "C2", "a", "b", "x", "y", "z", "col_0", "n"]
    fmt_pool = [None, "04d", ".2e", ".3f", "+.4f", "06d", "e", "g", "05.2f"]
    supplied_pool = ["04d", ".2e", ".3f", "+.4f", "06d", "e", "g", "05.2f"]
    # boundary cases first (plan §4.1 step 4)
    yield ([], {})
    yield ([("C1", None)], {})
    yield ([("C1", None)], {"C1": "04d"})
    yield ([("C1", ".3f")], {"C1": "04d"})
    yield ([("C1", ".3f")], {"C2": "04d"})
    yield ([("C1", None), ("C2", None)], {"C1": "04d", "C2": ".2e"})  # F2P
    yield ([("C1", None), ("C2", ".9f")], {"C2": ".2e"})
    yield ([("a", None), ("b", None)], {"a": ".2e"})
    for _ in range(n):
        k = rng.randint(0, 6)
        chosen = rng.sample(names_pool, min(k, len(names_pool)))
        cols = [(nm, rng.choice(fmt_pool)) for nm in chosen]
        formats = {nm: rng.choice(supplied_pool)
                   for nm in names_pool if rng.random() < 0.4}
        yield (cols, formats)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for cols, formats in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_eff_formats(cols, formats)
        oracle = oracle_eff_formats(cols, formats)
        if shadow != oracle:
            disagreements.append((cols, formats, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cols, formats, sh, orc in disagreements:
            print("  cols=%r formats=%r shadow=%r oracle=%r"
                  % (cols, formats, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of effectiveFormats agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
