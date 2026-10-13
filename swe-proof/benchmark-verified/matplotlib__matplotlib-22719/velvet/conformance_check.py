#!/usr/bin/env python3
"""G-CONF differential conformance for matplotlib__matplotlib-22719 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. This
bundle has NO axiomatized callees, so the entire impl region of both modeled
methods is R/I and is covered here; there is no axiom_check.py (G-AX skip).

Two independent sites in lib/matplotlib/category.py, each a pure boolean
decision "is the advisory emitted":

  * SITE A — StrCategoryConverter.convert: whether the number-passthrough
    deprecation warning (MatplotlibDeprecationWarning) is emitted.
  * SITE B — UnitData.update: whether the all-labels-look-numeric INFO log is
    emitted.

For each site:
  * SHADOW — `noticeFires(flags)` from Solution.lean's post-image, where the
             per-element `flags` are derived by calling the REAL UNCHANGED
             per-element tests (units.ConversionInterface.is_numlike for site A;
             UnitData._str_is_convertible for site B). The R/I op is the new
             non-empty guard conjoined with the all-aggregate; this is NOT a
             tautological transliteration of the patched line.
  * ORACLE — the REAL patched callee driven in-container: we run
             StrCategoryConverter.convert / UnitData.update and OBSERVE whether
             the advisory actually fires (a recorded MatplotlibDeprecationWarning
             for site A; a captured INFO record on the `matplotlib.category`
             logger for site B).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. Runs in-container against the
patched matplotlib; the fuzz seed is pinned (mapping.md §4).
"""
import logging
import random
import sys
import warnings

SEED = 22719
N_FUZZ = 100_000


# --- SHADOW: Solution.lean's noticeFires / allTrue, transliterated -----------

def all_true(flags):
    """allTrue : front-recursive conjunction; allTrue [] = True (vacuous)."""
    for b in flags:
        if not b:
            return False
    return True


def notice_fires(flags):
    """noticeFires flags = !flags.isEmpty && allTrue flags."""
    return bool(flags) and all_true(flags)


def main():
    import numpy as np
    from matplotlib import units
    from matplotlib.category import StrCategoryConverter, UnitData
    from matplotlib._api.deprecation import MatplotlibDeprecationWarning

    rng = random.Random(SEED)

    # value alphabets ---------------------------------------------------------
    numbers = [0, 1, -3, 2.5, 7, 42, 1e3, -0.0]
    num_strings = ["1", "2.5", "3", "-4", "1e3", "0"]      # _str_is_convertible -> True
    date_strings = ["2021-01-01", "Jan 2020"]              # parse as date -> True
    text_strings = ["a", "foo", "hello", "xyz", "qq"]      # -> False

    # ---- SITE A: StrCategoryConverter.convert -------------------------------
    def site_a_flags(values):
        # per-element: is_numlike(v) and not isinstance(v, (str, bytes))
        return [bool(units.ConversionInterface.is_numlike(v)
                     and not isinstance(v, (str, bytes)))
                for v in values]

    def site_a_oracle(values):
        """Drive the REAL patched convert; observe whether the deprecation
        warning fires. convert may raise for non-numeric non-string mixtures
        (the else-branch type check); the warning, if any, is emitted before
        that, so the recorded-warning flag is the faithful oracle."""
        unit = UnitData()
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            try:
                StrCategoryConverter.convert(values, unit, None)
            except Exception:
                pass
        return any(isinstance(w.message, MatplotlibDeprecationWarning)
                   for w in rec)

    # ---- SITE B: UnitData.update --------------------------------------------
    cat_logger = logging.getLogger("matplotlib.category")

    class _Capture(logging.Handler):
        def __init__(self):
            super().__init__(level=logging.INFO)
            self.hit = False

        def emit(self, record):
            if record.levelno >= logging.INFO:
                self.hit = True

    def site_b_flags(data):
        # per-UNIQUE-value: _str_is_convertible(val) (mapping.md §2 note)
        uniq = list(dict.fromkeys(data))
        return [bool(UnitData._str_is_convertible(v)) for v in uniq]

    def site_b_oracle(data):
        """Drive the REAL patched update on str data; observe the INFO advisory."""
        cap = _Capture()
        prev_level = cat_logger.level
        cat_logger.setLevel(logging.INFO)
        cat_logger.addHandler(cap)
        try:
            UnitData().update(data)
        except Exception:
            pass
        finally:
            cat_logger.removeHandler(cap)
            cat_logger.setLevel(prev_level)
        return cap.hit

    # ---- boundary + fuzz input generators -----------------------------------
    def gen_site_a():
        # boundaries
        yield []
        yield [1]
        yield [1, 2, 3]
        yield ["a"]
        yield ["a", "b"]
        yield [1, "a"]
        yield ["1", "2"]          # numeric strings are strings -> flag False
        yield [2.5, 7, 42]
        for _ in range(N_FUZZ):
            k = rng.randint(0, 6)
            alpha = numbers + text_strings + num_strings
            yield [rng.choice(alpha) for _ in range(k)]

    def gen_site_b():
        # boundaries (str/bytes only — the modeled domain of update)
        yield []
        yield ["1"]
        yield ["1", "2", "3"]
        yield ["a"]
        yield ["a", "b"]
        yield ["1", "a"]
        yield ["1", "1", "2"]     # duplicates: unique-aggregate
        yield ["2021-01-01", "5"]
        for _ in range(N_FUZZ):
            k = rng.randint(0, 6)
            alpha = num_strings + text_strings + date_strings
            yield [rng.choice(alpha) for _ in range(k)]

    disagreements = []
    count = 0

    for values in gen_site_a():
        count += 1
        shadow = notice_fires(site_a_flags(values))
        oracle = site_a_oracle(values)
        if shadow != oracle:
            disagreements.append(("A", values, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if not disagreements:
        for data in gen_site_b():
            count += 1
            shadow = notice_fires(site_b_flags(data))
            oracle = site_b_oracle(data)
            if shadow != oracle:
                disagreements.append(("B", data, shadow, oracle))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for site, inp, sh, orc in disagreements:
            print("  site=%s input=%r shadow=%r oracle=%r" % (site, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow noticeFires (site A convert + site B update) "
          "agrees with the real patched advisory-emission on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
