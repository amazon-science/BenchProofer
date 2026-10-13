#!/usr/bin/env python3
"""G-AX / A-reference soundness check for django__django-10999.

This bundle consumes NO `@ContractOnly` axiom: the changed behaviour (how a
leading sign is distributed over a colon-separated clock literal, and which
literals are valid) is modelled DEEPLY in model.py (`clock_value`,
`signed_total`, and the `parse_clock_seconds` validity rule). G-AX therefore
validates that DEEP MODEL == the real callee.

The real callee is the post-patch interpretation of a standard duration
literal: `standard_duration_re` (the post-patch regex) feeding the sign logic
of `django.utils.dateparse.parse_duration`. We reproduce that pipeline here on
the colon-separated standard form and assert, on boundary + randomized fuzz
inputs, that for every input the real pipeline and the model agree:

  * an input the model marks invalid (a sign after a separator,
    `inner_sign_seen`) is exactly an input the real pipeline does NOT match in
    its standard-duration branch (produces no standard match);

  * an input the model marks valid produces the real total seconds
    `signed_total(fields, leading_minus)` — i.e. a single leading sign negates
    the WHOLE clock value `H*3600 + M*60 + S`.

Imports only the standard library (`re`, `datetime`, `random`) — `re` is the
very engine the patch edits; nothing repo-specific. The post-patch regex below
is the gold patch's `standard_duration_re` verbatim (see patch.diff / the repo
file django/utils/dateparse.py post-patch). Exit 0 iff every obligation holds.
"""
import datetime
import random
import re
import sys

# --- the real post-patch standard-duration pipeline -------------------------
# `standard_duration_re` exactly as the gold patch defines it.
standard_duration_re = re.compile(
    r'^'
    r'(?:(?P<days>-?\d+) (days?, )?)?'
    r'(?P<sign>-?)'
    r'((?:(?P<hours>\d+):)(?=\d+:\d+))?'
    r'(?:(?P<minutes>\d+):)?'
    r'(?P<seconds>\d+)'
    r'(?:\.(?P<microseconds>\d{1,6})\d{0,6})?'
    r'$'
)


def real_standard_seconds(value):
    """Run the REAL post-patch standard-duration branch of parse_duration on a
    colon-form literal (no days, no fractional part) and return the signed
    integer total seconds, or None when there is no standard match. Mirrors
    django.utils.dateparse.parse_duration's sign handling exactly."""
    match = standard_duration_re.match(value)
    if not match:
        return None
    kw = match.groupdict()
    if kw.get('days') is not None:
        return None  # out of the modeled (no-days) domain; skip
    sign = -1 if kw.pop('sign', '+') == '-' else 1
    # Build a timedelta exactly as parse_duration does, then read total seconds.
    fields = {k: float(v) for k, v in kw.items()
              if k in ('hours', 'minutes', 'seconds') and v is not None}
    td = sign * datetime.timedelta(**fields)
    secs = td.total_seconds()
    assert secs == int(secs), "unexpected fractional total for %r" % value
    return int(secs)


# --- the model (model.py deep model) reproduced as plain Python --------------

def clock_value(fields):
    """model.py `clock_value`: positional base-60 combination, hours/min/sec."""
    n = len(fields)
    total = 0
    for idx, f in enumerate(fields):
        total += f * (60 ** (n - 1 - idx))
    return total


def signed_total(fields, leading_minus):
    """model.py `signed_total`: the single leading sign negates the whole."""
    v = clock_value(fields)
    return -v if leading_minus else v


def model_parse(fields, leading_minus, inner_sign_seen):
    """model.py `parse_clock_seconds` (its observable result)."""
    if inner_sign_seen:
        return None
    return signed_total(fields, leading_minus)


# --- abstraction: a colon-form literal -> (fields, leading_minus, inner) -----

def abstract(value):
    """Decompose a colon-form clock literal into the model's carrier:
    (fields, leading_minus, inner_sign_seen). Returns None if the literal is
    not even of the colon-and-digits shape the model's domain covers (so we
    only compare where the model is defined). `fields` has 1..3 entries."""
    # The post-patch standard regex's sign group is `-?` (minus only); a
    # leading `+` is not a standard-duration sign, so it is outside the model's
    # domain (the model carries only a `leading_minus` flag).
    if value.startswith('+'):
        return None
    leading_minus = value.startswith('-')
    body = value[1:] if (value and value[0] == '-') else value
    parts = body.split(':')
    if not (1 <= len(parts) <= 3):
        return None
    fields = []
    inner_sign_seen = False
    for i, p in enumerate(parts):
        seg = p
        if i > 0 and seg[:1] in '+-':
            inner_sign_seen = True
            seg = seg[1:]
        if seg == '' or not seg.isdigit():
            return None  # not a clean digit run -> out of model domain
        fields.append(int(seg))
    return fields, leading_minus, inner_sign_seen


def check(value):
    abstr = abstract(value)
    if abstr is None:
        return  # outside the modeled colon-and-digits domain
    fields, leading_minus, inner_sign_seen = abstr
    real = real_standard_seconds(value)
    expected = model_parse(fields, leading_minus, inner_sign_seen)
    # When the model declares the literal invalid, the real pipeline must not
    # match it as a standard duration.
    if inner_sign_seen:
        assert real is None, (
            "model rejects inner-sign %r but real standard match gave %r"
            % (value, real))
        return
    # Otherwise the real total seconds must equal the model's signed total.
    assert real == expected, (
        "deep model unsound on %r: real=%r model=%r (fields=%r minus=%r)"
        % (value, real, expected, fields, leading_minus))


def main():
    boundary = [
        '30', '-30', '+30',
        '15:30', '-15:30', '5:30', '-5:30',
        '10:15:30', '-10:15:30', '1:15:30', '-1:15:30',
        '00:01:01', '-00:01:01',
        '01:01', '-01:01',
        '0:00:00', '-0:00:00',
        '100:200:300', '-100:200:300',
        # inner-sign literals: the post-patch rule rejects these as standard
        '-01:-01', '01:-01', '-1:-15:30', '15:-30', '1:15:-30',
        '+15:30',
    ]
    for v in boundary:
        check(v)

    rng = random.Random(10999)
    for _ in range(50000):
        nfields = rng.randint(1, 3)
        sign = rng.choice(['', '-', '+'])
        segs = []
        for i in range(nfields):
            inner = rng.choice(['', '', '', '-', '+']) if i > 0 else ''
            digits = ''.join(rng.choice('0123456789')
                             for _ in range(rng.randint(1, 3)))
            segs.append(inner + digits)
        v = sign + ':'.join(segs)
        check(v)

    print("G-AX OK: deep model (clock_value/signed_total/validity) == real "
          "post-patch standard_duration_re + parse_duration sign logic on "
          "%d boundary + 50000 fuzz colon-form literals" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
