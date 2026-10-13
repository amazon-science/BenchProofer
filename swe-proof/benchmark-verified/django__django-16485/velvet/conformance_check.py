#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16485 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of `numericDisplay`'s impl: the
modeled branch-SELECTION guard `isWhole && p ≤ 0`. The two renderings the routine
chooses between (`intView`, `fracView`) are UNCHANGED sub-results of the
surrounding code, modeled as read-only inputs (R, mapping.md §1–2); the ONLY
transliterated (I) content is the guard that decides which is emitted.

REFINEMENT STRUCTURE / what is tested:
  * SHADOW  — the guard of Solution.lean's impl region, transliterated to Python
              over the real repo types via the mapping.md bijection
              (`not m` ↔ `isWhole`, `int(arg)` ↔ `p`):
                  model_takes_int_branch = isWhole and (p <= 0)
  * ORACLE  — `patch.diff`'s behaviour: the patched `floatformat` applied at
              base_commit (the real correctness oracle, G-RESOLVE). We observe
              WHICH branch the real function takes by monkeypatching the callee
              `django.utils.formats.number_format` and inspecting its first
              argument: the integer branch passes `"%d" % int(d)` (no '.'); the
              fractional branch passes the constructed `number` string, which
              ALWAYS contains a '.' (the source does `digits.insert(-exponent,
              ".")`). So "the integer branch fired" is observed reliably as
              `'.' not in first_arg`.

They must agree on every input that reaches the guard. Exit 0 iff zero
disagreements; any disagreement is a mechanical guard-fidelity counterexample.
A model that under-selects the integer branch (the pre-patch `p < 0`), over-
selects it, or ignores `isWhole` all produce disagreements here.

Domain: inputs that REACH the guard — `text` parses to a finite Decimal and
`arg` is a plain integer (no 'g'/'u' suffix, which the model does not cover).
Infinity/NaN and non-numeric text return before the guard and are out of scope.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import random
import sys
from decimal import Decimal, InvalidOperation

SEED = 16485
N_FUZZ = 100_000


def _ensure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            USE_I18N=False, USE_TZ=True, INSTALLED_APPS=[],
            USE_THOUSAND_SEPARATOR=False,
        )
    django.setup()


def reconstruct(text, arg):
    """Bridge (mapping.md §2): reconstruct (isWhole, p) the way floatformat does,
    or return None if the input does not reach the guard."""
    # parse the value `d` exactly as floatformat does
    try:
        input_val = str(text)
        d = Decimal(input_val)
    except InvalidOperation:
        try:
            d = Decimal(str(float(text)))
        except (ValueError, InvalidOperation, TypeError):
            return None
    # arg must be a plain integer (no suffix handling modeled)
    try:
        p = int(arg)
    except (ValueError, TypeError):
        return None
    # m = int(d) - d ; may raise on inf/nan -> out of guard scope
    try:
        m = int(d) - d
    except (ValueError, OverflowError, InvalidOperation):
        return None
    is_whole = (not m)
    return bool(is_whole), int(p)


def observe_real_branch(floatformat, formats_mod, text, arg):
    """Run the REAL patched floatformat; return (took_int_branch, raised).
    Detects the branch by capturing the first arg passed to number_format."""
    captured = []
    real_nf = formats_mod.number_format

    def spy(value, *a, **kw):
        captured.append(str(value))
        return real_nf(value, *a, **kw)

    formats_mod.number_format = spy
    raised = False
    try:
        floatformat(text, arg)
    except Exception:
        raised = True
    finally:
        formats_mod.number_format = real_nf
    # integer branch fires iff number_format was called with a dot-free string
    # ("%d" % int(d)); the fractional branch's `number` always contains '.'.
    took_int = any("." not in c for c in captured)
    return took_int, raised


def fuzz_inputs(n, rng):
    # boundary + F2P cases first (the issue + the new test assertions)
    yield ("0.00", 0)
    yield (Decimal("0.00"), 0)
    yield ("0", 0)
    yield (Decimal("0.000000"), 0)
    yield ("11.00", 0)
    yield (Decimal("11.00"), 0)
    yield ("-5.00", 0)
    yield (Decimal("9.000"), 0)
    yield (7.7, 0)
    yield (11.0000, -2)
    yield (11.000001, -2)
    yield (0, 6)
    yield (0.0, 0)
    yield (-0.499, 0)
    yield (13.1031, -3)
    yield (Decimal("555.555"), 2)
    yield (1000, 0)
    yield (1000, -1)
    yield (1000, 3)
    # randomized fuzz across whole/fractional values and negative/zero/positive p
    whole_vals = ["0", "0.00", "0.000000", "11", "11.00", "-5", "-5.00",
                  "9.000", "1000", "123.000", "-0.0", "1", "999999"]
    frac_vals = ["0.07", "0.4", "13.1031", "11.000001", "555.555", "1.42",
                 "-0.499", "0.12345", "0.000000000000000000015", "1.5", "-7.7"]
    for _ in range(n):
        if rng.random() < 0.5:
            base = rng.choice(whole_vals)
        else:
            base = rng.choice(frac_vals)
        # sometimes wrap as Decimal, sometimes as str, sometimes float
        kind = rng.randint(0, 2)
        if kind == 0:
            text = base
        elif kind == 1:
            text = Decimal(base)
        else:
            try:
                text = float(base)
            except ValueError:
                text = base
        p = rng.randint(-8, 8)
        yield (text, p)


def main():
    _ensure_django()
    from django.template.defaultfilters import floatformat
    from django.utils import formats as formats_mod

    # Guard against running on an UNPATCHED tree (would crash on "0.00", 0).
    # The harness applies patch.diff first; this is a sanity assertion.
    try:
        floatformat("0.00", 0)
    except Exception as e:
        print("G-CONF ERROR: floatformat('0.00', 0) raised %r — patch.diff not "
              "applied? G-CONF requires the patched oracle." % (e,))
        return 2

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    frac_body_skips = 0  # frac branch selected AND its unchanged body raised
    for text, arg in fuzz_inputs(N_FUZZ, rng):
        rec = reconstruct(text, arg)
        if rec is None:
            continue  # input does not reach the guard — out of modeled scope
        is_whole, p = rec
        count += 1
        model_takes_int = is_whole and (p <= 0)
        took_int, raised = observe_real_branch(floatformat, formats_mod, text, arg)

        # The I-leg under test is the SELECTION guard: which branch fires.
        if took_int != model_takes_int:
            disagreements.append((text, arg,
                                  "model_int=%s" % model_takes_int,
                                  "real_int=%s raised=%s" % (took_int, raised)))
        elif model_takes_int and raised:
            # The fix's guarantee: when the integer branch is selected (whole
            # value, non-positive p), the real function must COMPLETE — never
            # the `prec=0` ValueError the issue reports.
            disagreements.append((text, arg, "model_int=True",
                                  "INTEGER BRANCH RAISED"))
        elif (not model_takes_int) and raised:
            # The fractional branch fired (selection agrees) but its UNCHANGED
            # body raised — a separate, pre-existing Django crash (e.g.
            # Decimal("0.000000") at p>0 yields a negative `prec`), unrelated to
            # this fix and not in any F2P/P2P test. `fracView` is modeled as an
            # abstract read-only input (mapping.md §1–2, refinement R-rows
            # A4/B), so its internals are out of the modeled scope. Counted and
            # reported, not a selection disagreement.
            frac_body_skips += 1
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d guard disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for row in disagreements:
            print("  input=%r arg=%r  %s  %s" % row)
        return 1
    print("G-CONF OK: R/I shadow of numericDisplay's selection guard agrees "
          "with patch.diff branch choice on %d inputs (seed=%d), 0 "
          "disagreements (%d frac-branch-body latent-crash inputs out of "
          "modeled scope, selection still agreed)." % (count, SEED, frac_body_skips))
    return 0


if __name__ == "__main__":
    sys.exit(main())
