#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-10999 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
(clock_value / pow60 / signed_total) copy over as plain functions on a tuple
PSeq shim. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.utils.dateparse.parse_duration`, exercised on its standard
(colon-separated clock) form. The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2): a model input (fields, leading_minus,
inner_sign_seen) concretizes to a clock literal string:

  * `fields` (1..3 non-negative ints) become colon-joined decimal digit runs;
    digit-run padding with leading zeros is varied since the extraction reads
    any run of digits as the same magnitude;
  * `leading_minus` becomes a '-' prefix on the whole literal (a leading '+'
    is outside the modeled domain per mapping.md section 3.1);
  * `inner_sign_seen` becomes a sign character ('-' or '+') placed after one
    of the ':' separators, i.e. before a non-first field. This flag therefore
    only has a concrete counterpart when len(fields) >= 2, so fuzzing draws
    inner_sign_seen=True only for multi-field inputs.

Result bridge (mapping.md section 2): the shadow returns a signed integer
total in seconds or None; the real function returns a timedelta or None. Two
no-microsecond timedeltas are equal iff their whole-second totals are equal,
so the comparison is `real == timedelta(seconds=shadow)` (or both None).
Field magnitudes are kept below 10**7 so the real pipeline's float conversion
of the captured digit runs stays exact.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz triples.
Pinned fuzz seed: 10999.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import datetime
import json
import random
import sys

SEED = 10999
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


# --- pure helpers from model.py, decorators/contracts stripped ---------------

def clock_value(fields):
    if len(fields) == 0:
        return 0
    # The leading field's positional weight is 60**(len-1): hours when 3
    # fields remain, minutes when 2, seconds when 1.
    return fields[0] * pow60(len(fields) - 1) + clock_value(fields.drop(1))


def pow60(k):
    if k == 0:
        return 1
    return 60 * pow60(k - 1)


def signed_total(fields, leading_minus):
    if leading_minus:
        return -clock_value(fields)
    return clock_value(fields)


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def parse_clock_seconds(fields, leading_minus, inner_sign_seen):
    if inner_sign_seen:
        return None
    # Accumulate the positional magnitude right-to-left (seconds, minutes,
    # hours) so the front-recursive clock_value unfolds one field per step.
    total = 0  # type: int
    weight = 1  # type: int
    i = len(fields)
    while i > 0:
        total = fields[i - 1] * weight + total
        weight = weight * 60
        i = i - 1
    if leading_minus:
        return -total
    return total


# --- bridge: (fields, leading_minus, inner_sign_seen) -> clock literal -------

def concretize(rng, fields, leading_minus, inner_sign_seen, inner_char='-',
               inner_pos=None, pad=None):
    """Build the clock literal string a given model input abstracts. `pad`
    optionally left-pads each field's digit run to that width; `inner_pos`
    selects which non-first field carries the inner sign character."""
    segs = []
    for f in fields:
        s = str(f)
        if pad is not None and len(s) < pad:
            s = '0' * (pad - len(s)) + s
        segs.append(s)
    if inner_sign_seen:
        pos = inner_pos if inner_pos is not None else rng.randint(1, len(fields) - 1)
        segs[pos] = inner_char + segs[pos]
    literal = ':'.join(segs)
    if leading_minus:
        literal = '-' + literal
    return literal


def check_case(parse_duration, rng, fields, leading_minus, inner_sign_seen,
               **kw):
    literal = concretize(rng, fields, leading_minus, inner_sign_seen, **kw)
    shadow = parse_clock_seconds(list(fields), leading_minus, inner_sign_seen)
    real = parse_duration(literal)
    if shadow is None:
        ok = real is None
    else:
        ok = real is not None and real == datetime.timedelta(seconds=shadow)
    if not ok:
        return ("DISAGREEMENT\n  fields=%r leading_minus=%r inner_sign_seen=%r"
                "\n  literal=%r\n  shadow=%r\n  real=%r"
                % (fields, leading_minus, inner_sign_seen, literal, shadow,
                   real))
    return None


def boundary_cases():
    """(fields, leading_minus, inner_sign_seen, extra-kwargs) tuples covering
    each field count, both flags, zero fields, over-59 fields, zero-padded
    runs, and each inner-sign placement/character."""
    cases = []
    for lm in (False, True):
        cases += [
            ([0], lm, False, {}),
            ([30], lm, False, {}),
            ([59], lm, False, {}),
            ([60], lm, False, {}),
            ([15, 30], lm, False, {}),
            ([0, 0], lm, False, {}),
            ([5, 30], lm, False, {}),
            ([0, 1], lm, False, {'pad': 2}),
            ([1, 1], lm, False, {'pad': 2}),
            ([10, 15, 30], lm, False, {}),
            ([0, 0, 0], lm, False, {}),
            ([0, 1, 1], lm, False, {'pad': 2}),
            ([1, 15, 30], lm, False, {}),
            ([100, 200, 300], lm, False, {}),
            ([23, 59, 59], lm, False, {}),
            # inner sign at each admissible position, both characters
            ([1, 1], lm, True, {'inner_pos': 1, 'inner_char': '-', 'pad': 2}),
            ([15, 30], lm, True, {'inner_pos': 1, 'inner_char': '+'}),
            ([1, 15, 30], lm, True, {'inner_pos': 1, 'inner_char': '-'}),
            ([1, 15, 30], lm, True, {'inner_pos': 2, 'inner_char': '-'}),
            ([1, 15, 30], lm, True, {'inner_pos': 2, 'inner_char': '+'}),
        ]
    return cases


def rand_case(rng):
    n = rng.randint(1, 3)
    fields = []
    for _ in range(n):
        # mostly clock-plausible magnitudes, sometimes larger runs
        if rng.random() < 0.85:
            fields.append(rng.randint(0, 99))
        else:
            fields.append(rng.randint(0, 9_999_999))
    leading_minus = rng.random() < 0.5
    # the inner-sign carrier state needs a separator to sit after
    inner_sign_seen = n >= 2 and rng.random() < 0.25
    kw = {}
    if rng.random() < 0.3:
        kw['pad'] = rng.randint(2, 3)
    if inner_sign_seen:
        kw['inner_char'] = rng.choice('-+')
    return fields, leading_minus, inner_sign_seen, kw


def main():
    from django.utils.dateparse import parse_duration  # REAL patched callee

    rng = random.Random(SEED)
    checked = 0
    n_boundary = 0
    for fields, lm, inner, kw in boundary_cases():
        err = check_case(parse_duration, rng, fields, lm, inner, **kw)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    for _ in range(N_FUZZ):
        fields, lm, inner, kw = rand_case(rng)
        err = check_case(parse_duration, rng, fields, lm, inner, **kw)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real parse_duration on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
