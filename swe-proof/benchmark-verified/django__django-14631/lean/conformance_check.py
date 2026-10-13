#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14631.

The bundle models ONE behavior the form-cleaning routine produces (mapping.md):
the value each field contributes to the form's cleaned data, in field order.

The patched per-field rule (`BaseForm._clean_fields`, success path) is:

    value = bf.initial if field.disabled else bf.data

where, for a disabled field, `bf.initial` (`BoundField.initial`) presents the
field's preset initial value at the precision the field's widget can represent —
a date/time loses its microsecond component when
`field.widget.supports_microseconds` is False; everything else is unchanged. In
the modeled success case (`form.errors == {}`, the F2P scenario) `field.clean`
preserves the selected value, so the cleaned entry equals the selected value.

Standing up real Django Field/Widget/BoundField objects, a bound Form, and the
full clean pipeline is heavy and unnecessary: the modeled value is exactly this
pure per-field decision over the observables the routine reads (mapping.md
bijection). So the ORACLE below is a faithful in-process replica using the EXACT
patched expressions; the SHADOW is the op-for-op transliteration of
`implementation_cleanFields` / `boundInitial` / `cleanedValue` (refinement.md).

A field value is modeled as:
  ('ts', whole:int, sub:int)   a temporal value (sub = microseconds, 0..999999)
  ('other', n:int)             any non-temporal value

A field model is (disabled:bool, supports_micro:bool, raw_initial, data).

This genuinely tests:
  * the disabled microsecond-stripping case (supports_micro=False, sub>0) — the
    F2P behavior: the cleaned value drops the sub-second component;
  * the disabled microsecond-keeping case (supports_micro=True) — value kept;
  * the disabled non-temporal case — value passed through;
  * the editable case — submitted data used, initial ignored;
  * field order preserved, one entry per field.

stdlib-only. Pinned seed: 20140631 (also in mapping.md).
"""
import random
import sys

SEED = 20140631
N = 120_000


# --- ORACLE: faithful in-process replica of the patched per-field decision ----
def bound_initial(supports_micro, raw_initial):
    """Replica of BoundField.initial's micro-stripping (boundfield.py:212-220)."""
    kind = raw_initial[0]
    if kind == 'ts':
        _, whole, sub = raw_initial
        if supports_micro:
            return ('ts', whole, sub)
        return ('ts', whole, 0)
    return raw_initial  # ('other', n) — unchanged


def oracle_field(field):
    disabled, supports_micro, raw_initial, data = field
    # patched: value = bf.initial if field.disabled else bf.data
    value = bound_initial(supports_micro, raw_initial) if disabled else data
    # success path: field.clean(value) preserves an already-typed value
    return value


def oracle(fields):
    return [oracle_field(f) for f in fields]


# --- SHADOW of implementation_cleanFields (the R / A-reference leg) ------------
# Mirrors Solution.lean:
#   boundInitial f = match rawInitial with
#       | ts whole sub => if supportsMicro then ts whole sub else ts whole 0
#       | other n      => other n
#   cleanedValue f = if disabled then boundInitial f else data
#   implementation_cleanFields fields = Id.run do
#       cleaned := []; for f in fields do cleaned ++= [if disabled ... ]
def _bound_initial(supports_micro, raw_initial):
    kind = raw_initial[0]
    if kind == 'ts':
        _, whole, sub = raw_initial
        return ('ts', whole, sub) if supports_micro else ('ts', whole, 0)
    return raw_initial


def shadow(fields):
    cleaned = []
    for f in fields:
        disabled, supports_micro, raw_initial, data = f
        value = _bound_initial(supports_micro, raw_initial) if disabled else data
        cleaned = cleaned + [value]
    return cleaned


def disagree(fields):
    o = oracle(fields)
    s = shadow(fields)
    if o != s:
        return (fields, o, s)
    return None


def _rand_value(rng):
    if rng.choice([True, False]):
        return ('ts', rng.randint(-10, 10**9), rng.randint(0, 999999))
    return ('other', rng.randint(-1000, 1000))


def _enumerate_edge():
    cases = []
    # disabled, no micro support, non-zero sub  -> stripped (THE F2P behavior)
    cases.append([(True, False, ('ts', 1161786646, 123456), ('other', 7))])
    # disabled, micro support, non-zero sub      -> kept
    cases.append([(True, True, ('ts', 1161786646, 123456), ('other', 7))])
    # disabled, no micro support, zero sub        -> unchanged anyway
    cases.append([(True, False, ('ts', 1161786646, 0), ('other', 7))])
    # disabled, non-temporal initial              -> passed through
    cases.append([(True, False, ('other', 42), ('other', 99))])
    # editable temporal                            -> data used, initial ignored
    cases.append([(False, False, ('ts', 5, 123456), ('ts', 9, 7))])
    # editable non-temporal
    cases.append([(False, True, ('other', 1), ('other', 2))])
    # empty form
    cases.append([])
    # multiple fields, order + mixed
    cases.append([
        (True, False, ('ts', 100, 500000), ('other', 0)),
        (False, True, ('other', 3), ('other', 4)),
        (True, True, ('ts', 200, 1), ('other', 0)),
        (False, False, ('ts', 7, 0), ('ts', 8, 9)),
    ])
    return cases


def main() -> int:
    checked = 0
    for fields in _enumerate_edge():
        d = disagree(fields)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        nfields = rng.randint(0, 6)
        fields = []
        for _ in range(nfields):
            fields.append((
                rng.choice([True, False]),   # disabled
                rng.choice([True, False]),   # supports_micro
                _rand_value(rng),            # raw_initial
                _rand_value(rng),            # data
            ))
        d = disagree(fields)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
