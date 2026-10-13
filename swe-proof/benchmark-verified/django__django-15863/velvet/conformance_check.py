#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15863 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (the
              `floatFormat` `do` block plus the pure `renderFixed` model)
              transliterated to Python over the *real* repo types, via the
              mapping.md bijection (`List Char` ↔ str of digits; Nat `p` ↔ the
              `arg` precision). There are NO A-tagged callees in this bundle
              (axiom-free): every op the impl performs is concrete digit/append
              work, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.template.defaultfilters.floatformat` applied at
              base_commit (the real correctness oracle, G-RESOLVE).

The comparison is restricted to the modeled regime (mapping.md §2 / refinement.md
§A): a non-negative `Decimal` numeral with `p` a positive int at least the
numeral's own fractional length (no value rounded away, default locale, no
grouping). That is exactly the regime the FAIL_TO_PASS case
`floatformat(Decimal("123456.123456789012345678901"), 21)` lives in and the
regime `renderFixed` claims. They must agree on every such input. Exit 0 iff
zero disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + hypothesis
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
from decimal import Decimal

SEED = 15863
N_FUZZ = 100_000


# --- the R/I shadow: renderFixed / the floatFormat do-block, transliterated ---
def shadow_render(int_digits, frac_digits, p):
    """renderFixed (intDigits fracDigits : List Char) (p : Nat), transliterated
    to str. The backward pad `while` of floatFormat appends (p - |frac|) zeros
    to the fractional run; renderFixed is its closed form."""
    pad = "0" * (p - len(frac_digits))
    return int_digits + "." + frac_digits + pad


def split_numeral(canon):
    """Bridge a canonical non-negative decimal numeral (str) to the Lean
    carriers (intDigits, fracDigits) per mapping.md §2."""
    if "." in canon:
        intp, frac = canon.split(".")
    else:
        intp, frac = canon, ""
    return intp, frac


# --- the oracle: patch.diff's behaviour --------------------------------------
def _configure_django():
    """floatformat() ends in formats.number_format(), which reads Django
    settings (USE_I18N / locale). Outside a Django process these are
    unconfigured, so configure the defaults once: default (en) locale, no forced
    grouping — exactly the modeled regime (mapping.md §2). This sets up the
    runtime, not the behaviour under test (the str-vs-repr conversion)."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        django.setup()


def oracle_floatformat(d, p):
    """patch.diff's behaviour: the patched django floatformat(). The harness
    applies patch.diff before this runs, so the imported filter is the fixed
    `input_val = str(text)` version."""
    _configure_django()
    from django.template.defaultfilters import floatformat
    return floatformat(d, p)


def in_regime(canon, p):
    """The modeled regime (mapping.md §2): plain (non-scientific) non-negative
    numeral; p a positive int >= the numeral's own fractional length."""
    if "e" in canon.lower():
        return False
    if canon.startswith("-"):
        return False
    _, frac = split_numeral(canon)
    return p >= 1 and p >= len(frac)


def fuzz_inputs(n, rng):
    # boundary / F2P cases first (plan §4.1 step 4)
    yield ("123456.123456789012345678901", 21)   # the FAIL_TO_PASS case
    yield ("42.12345678901234567890", 20)          # the MWE from the issue
    yield ("9", 3)
    yield ("0", 2)
    yield ("0", 1)
    yield ("7.5", 1)
    yield ("42.123", 3)
    yield ("42.123", 5)
    yield ("100.00", 2)
    yield ("1000000.000001", 6)
    yield ("0.000000000000000000001", 21)
    yield ("123.456", 6)
    for _ in range(n):
        ni = rng.randint(1, 8)
        nf = rng.randint(0, 25)
        intp = "".join(rng.choice("0123456789") for _ in range(ni))
        frac = "".join(rng.choice("0123456789") for _ in range(nf))
        s = intp + ("." + frac if nf > 0 else "")
        canon = str(Decimal(s))   # canonicalize (drops leading zeros etc.)
        _, cf = split_numeral(canon)
        p = rng.randint(max(1, len(cf)), len(cf) + 10)
        yield (canon, p)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    skipped = 0
    for s, p in fuzz_inputs(N_FUZZ, rng):
        canon = str(Decimal(s))
        if not in_regime(canon, p):
            skipped += 1
            continue
        count += 1
        intp, frac = split_numeral(canon)
        shadow = shadow_render(intp, frac, p)
        oracle = str(oracle_floatformat(Decimal(canon), p))
        if shadow != oracle:
            disagreements.append((canon, p, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, p, sh, orc in disagreements:
            print("  numeral=%r p=%r shadow=%r oracle=%r" % (s, p, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of floatFormat agrees with patch.diff "
          "behaviour on %d inputs (seed=%d, %d out-of-regime skipped), "
          "0 disagreements." % (count, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
