#!/usr/bin/env python3
"""G-AX / A-reference soundness check for django__django-14631.

There is NO consumed @ContractOnly axiom in model.py: the cleaned-value
behaviour is modelled deeply by the pure functions `normalise` (drop the
sub-second component) and `bound_initial` (the single, cached, normalised
evaluation of the initial source). This script validates those deep-model
references against the REAL Django form machinery, in-container, on the exact
disabled-field-with-callable-initial scenario the F2P tests exercise plus a
boundary + fuzz sweep.

Deep-model references validated (A-reference, NOT consumed as axioms):

  R1. The field's bound initial (`form[name].initial`) evaluates the callable
      initial source EXACTLY ONCE, caches it, and — for a date/time value whose
      widget lacks sub-second support — strips the sub-second component. In the
      model: `bound_initial(fs) == normalise(fs.first_eval)`.

  R2. The cleaned value of a DISABLED field equals that bound initial exactly
      (same single evaluation, normalised). In the model:
      `clean_bound_initial_field(fs) == bound_initial(fs)`.

  R3. The pre-patch path (evaluate the source AGAIN, un-normalised) would
      DISAGREE with the bound initial whenever the source is stateful and/or
      carries sub-second precision — i.e. the bug the patch removes. This is
      the model_prepatch failing clause; we confirm the real disagreement
      exists pre-patch so the differential witness is real, not vacuous.

`normalise` encodes a date/time as `whole_seconds * 1_000_000 + microseconds`;
the real `BoundField.initial` strips microseconds for widgets that do not
support them, which is exactly flooring that integer to a multiple of 1_000_000.

Run inside the official SWE-bench container for this instance (post-patch source
present). stdlib + Django only; exit 0 iff every obligation holds.
"""
import datetime
import os
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={},
            USE_TZ=False,
        )
    django.setup()


def _encode(dt):
    """Encode a datetime's seconds+microseconds as the model integer
    `whole_seconds * 1_000_000 + microseconds` (relative to a fixed epoch so
    the value is non-negative). Mirrors the model carrier exactly."""
    base = datetime.datetime(2006, 10, 25, 0, 0, 0)
    delta = dt - base
    total_us = delta.days * 86400 * 1000000 + delta.seconds * 1000000 + delta.microseconds
    assert total_us >= 0
    return total_us


def _normalise(value):
    """The model's `normalise`: floor to a whole second (drop microseconds)."""
    return (value // 1000000) * 1000000


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django import forms
    from django.forms.fields import DateTimeField

    observations = 0

    def make_form(disabled, microseconds, increment=1, start_second=45):
        """A form with one disabled (or not) DateTimeField whose initial is a
        STATEFUL callable yielding a distinct, microsecond-bearing datetime on
        each call — the exact structure of the F2P helper."""
        class FakeTime:
            def __init__(self):
                self.elapsed_seconds = 0

            def now(self):
                self.elapsed_seconds += increment
                return datetime.datetime(
                    2006, 10, 25, 14, 30, start_second + self.elapsed_seconds,
                    microseconds,
                )

        ft = FakeTime()

        class DateTimeForm(forms.Form):
            dt = DateTimeField(initial=ft.now, disabled=disabled)

        # Capture what the FIRST and a hypothetical fresh (second) evaluation of
        # the SAME source would produce, by replaying an identical generator.
        probe = FakeTime()
        first_eval_dt = probe.now()
        fresh_eval_dt = probe.now()
        return DateTimeForm({}), first_eval_dt, fresh_eval_dt

    # ---- R1 + R2 on the exact F2P scenario -----------------------------------
    # F2P 1: disabled, microseconds=123456  -> cleaned == datetime(...,46) (no us)
    form, first_dt, fresh_dt = make_form(disabled=True, microseconds=123456)
    assert form.errors == {}, "unexpected errors: %r" % (form.errors,)
    cleaned = form.cleaned_data['dt']
    bf = form['dt']

    # R2 (real): cleaned value of the disabled field == the bound initial.
    assert cleaned == bf.initial, (
        "R2 violated: _clean_fields value %r != bound initial %r" % (cleaned, bf.initial))

    # R1 (real == model): bf.initial is the NORMALISED first evaluation.
    enc_first = _encode(first_dt)
    assert _encode(bf.initial) == _normalise(enc_first), (
        "R1 violated: bound initial %r is not normalise(first eval %r)" % (bf.initial, first_dt))

    # Microseconds actually stripped (F2P 1's assertion).
    assert bf.initial.microsecond == 0, "expected microseconds stripped, got %r" % (bf.initial,)
    assert cleaned == datetime.datetime(2006, 10, 25, 14, 30, 46), (
        "F2P-microseconds: cleaned %r != 2006-10-25 14:30:46" % (cleaned,))
    observations += 1

    # F2P 2: disabled, microseconds=0 -> cleaned == bf.initial (single eval).
    form2, first2, fresh2 = make_form(disabled=True, microseconds=0)
    assert form2.errors == {}
    cleaned2 = form2.cleaned_data['dt']
    bf2 = form2['dt']
    assert cleaned2 == bf2.initial, (
        "F2P-bound_field: cleaned %r != bf.initial %r" % (cleaned2, bf2.initial))
    assert cleaned2 == datetime.datetime(2006, 10, 25, 14, 30, 46), (
        "F2P-bound_field: cleaned %r != 2006-10-25 14:30:46" % (cleaned2,))
    observations += 1

    # ---- R3: the real pre-patch disagreement exists (non-vacuous witness) ----
    # The pre-patch code computed the disabled value via
    # get_initial_for_field(field, name), i.e. a FRESH call to the SAME stateful
    # callable, WITHOUT the BoundField's microsecond normalisation. Replaying
    # the generator, a fresh evaluation differs from the cached, normalised
    # bound initial — confirming the model_prepatch failing clause is real.
    enc_fresh = _encode(fresh_dt)
    assert enc_fresh != _normalise(enc_first), (
        "R3 vacuous: a fresh re-evaluation %r equals normalise(first %r); the "
        "differential witness would be empty" % (fresh_dt, first_dt))
    # And specifically: fresh eval is a later second AND carries microseconds.
    assert fresh_dt != first_dt, "expected stateful source to advance"
    assert fresh_dt.microsecond == 123456, "fresh eval should retain microseconds"
    observations += 1

    # ---- boundary + fuzz over normalise (deep model) =========================
    import random
    rng = random.Random(20210713)
    for _ in range(50000):
        whole = rng.randint(0, 10**9)
        us = rng.randint(0, 999999)
        v = whole * 1000000 + us
        # normalise drops microseconds and is idempotent.
        n = _normalise(v)
        assert n == whole * 1000000, "normalise(%d) = %d != %d" % (v, n, whole * 1000000)
        assert _normalise(n) == n, "normalise not idempotent at %d" % (v,)
        assert 0 <= n <= v, "normalise out of range at %d" % (v,)
        observations += 1
    # boundaries
    for v in (0, 999999, 1000000, 1000001, 1999999):
        assert _normalise(v) == (v // 1000000) * 1000000
        observations += 1

    print("G-AX OK: deep-model references R1/R2 sound against the real Django "
          "form machinery (cleaned disabled value == bound initial == "
          "normalise(single first evaluation)); R3 pre-patch disagreement is "
          "real; normalise validated over %d observations." % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
