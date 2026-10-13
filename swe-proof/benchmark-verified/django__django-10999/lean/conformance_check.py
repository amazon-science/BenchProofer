#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_durationFromText
against the post-patch behaviour of django.utils.dateparse.parse_duration.

The impl region is NOT all-A-tagged: the CHANGED standard clock-format branch is
modeled DEEPLY (`primaryFormatMicros` -> `shadow_primary`, the R/I content). The
single A-reference (`fallbackFormatMicros`, the UNCHANGED ISO-8601 / PostgreSQL
alternative interpreter) is left as the REAL repo parsing arms — exactly the
unchanged tail of parse_duration. The shadow therefore reproduces the post-patch
behaviour op-for-op.

Bridge (mapping.md): a parsed timedelta <-> its total microseconds as an int,
computed EXACTLY as ``(td.days*86400 + td.seconds)*10**6 + td.microseconds``
(``total_seconds()`` is a float and loses microseconds above 2**53 µs, which the
modeled range reaches); None <-> None.

DOMAIN OF THE COMPARISON (the two side conditions the spec states in its header,
implemented here as `ascii_text` / `primary_in_range`, so this script MEASURES the
boundary instead of merely avoiding it):

  1. `ascii_text` — the spec's digit class is the ASCII run 0-9; the real matcher's
     `\\d` and the real numeric conversion accept the whole Unicode Nd repertoire
     (U+0665 etc.). Non-ASCII text is outside the spec's domain and is counted,
     not compared.
  2. `primary_in_range` — the spec's day part, signed clock part and their sum must
     each fit datetime.timedelta's range; beyond it the real callee raises
     OverflowError, which is not a value of Option Int. Out-of-range text is
     outside the spec's domain and is counted, not compared.

The generator DELIBERATELY produces both excluded families (Arabic-Indic /
fullwidth / Devanagari digit alphabets, and up-to-22-digit magnitudes) plus the
trailing-newline family that the spec now MODELS, so a domain condition that had
drifted into vacuity or over-breadth would show up as a count of zero.

We assert zero disagreements over >=10^5 IN-DOMAIN fuzzed inputs spanning the
standard format (day prefix on/off, both unit spellings, leading sign on/off,
1/2/3 colon fields, inner-negative fields, 0..14 fractional digits, trailing
newline, boundary / garbage) plus ISO-8601 and PostgreSQL alternative forms.

The reference is the REAL `django.utils.dateparse` in the container, with
patch.diff applied by the gate — not a transcription of it, so the comparison
cannot drift away from the shipped source.

exit 0 iff zero in-domain disagreements and both exclusion families are actually
exercised.
"""
import random
import sys

# The post-patch function under model, imported from the repo the gate has
# already patched. An ImportError here is a broken container, not a verdict.
from django.utils.dateparse import (
    iso8601_duration_re,
    parse_duration,
    postgres_interval_re,
    standard_duration_re,
)

SEED = 10999          # pinned in mapping.md
N = 400_000           # >= 10^5 in-domain after the excluded families are removed

# datetime.timedelta's representable range, in microseconds:
# timedelta.min == -999999999 days, timedelta.max == 999999999 days, 23:59:59.999999
US_MIN = -(999999999 * 86400 * 10 ** 6)
US_MAX = (999999999 * 86400 + 86399) * 10 ** 6 + 999999

OVERFLOW = "OverflowError"


def patched_micros(value):
    """post-patch parse_duration result, bridged to Option[int microseconds].

    An OverflowError is reported as its own token: it is neither `None` nor an
    `Int`, so it can never silently compare equal to a shadow value."""
    try:
        td = parse_duration(value)
    except OverflowError:
        return OVERFLOW
    if td is None:
        return None
    return (td.days * 86400 + td.seconds) * 10 ** 6 + td.microseconds


# ---------------------------------------------------------------------------
# Shadow: the R/I reconstruction of implementation_durationFromText.
#   - shadow_primary == primaryFormatMicros  (DEEP model of the standard branch)
#   - fallback (A-reference) == REAL iso8601 + postgres parsing arms
# ---------------------------------------------------------------------------
def _is_digits(t):
    return len(t) > 0 and all('0' <= c <= '9' for c in t)


def _digits_to_nat(cs):
    return int(cs) if _is_digits(cs) else None


def _drop_final_newline(v):
    """== dropFinalNewline: the anchored whole-text match ends at the end of the
    text or just before ONE final newline (Python `$`)."""
    return v[:-1] if v.endswith('\n') else v


def _signed_int(cs):
    if cs.startswith('-'):
        n = _digits_to_nat(cs[1:])
        return None if n is None else -n
    n = _digits_to_nat(cs)
    return None if n is None else n


def _strip_unit(cs):
    if cs.startswith('days, '):
        return cs[6:]
    if cs.startswith('day, '):
        return cs[5:]
    return cs


def _parse_sec_micro(cs):
    """non-negative seconds with optional .frac -> (sec, micro) or None."""
    parts = cs.split('.')
    if len(parts) == 1:
        s = _digits_to_nat(parts[0])
        return None if s is None else (s, 0)
    if len(parts) == 2:
        secs, frac = parts
        if frac == '' or len(frac) > 12 or not _is_digits(frac):
            return None
        micro6 = frac[:6].ljust(6, '0')
        s = _digits_to_nat(secs)
        us = _digits_to_nat(micro6)
        if s is None or us is None:
            return None
        return (s, us)
    return None


def _parse_clock(rest):
    neg = False
    body = rest
    if body.startswith('-'):
        neg = True
        body = body[1:]
    fields = body.split(':')
    k = len(fields)
    if k == 1:
        sm = _parse_sec_micro(fields[0])
        if sm is None:
            return None
        s, us = sm
        v = s * 10 ** 6 + us
    elif k == 2:
        mm = _digits_to_nat(fields[0])
        sm = _parse_sec_micro(fields[1])
        if mm is None or sm is None:
            return None
        s, us = sm
        v = mm * 60 * 10 ** 6 + s * 10 ** 6 + us
    elif k == 3:
        hh = _digits_to_nat(fields[0])
        mm = _digits_to_nat(fields[1])
        sm = _parse_sec_micro(fields[2])
        if hh is None or mm is None or sm is None:
            return None
        s, us = sm
        v = hh * 3600 * 10 ** 6 + mm * 60 * 10 ** 6 + s * 10 ** 6 + us
    else:
        return None
    return -v if neg else v


def shadow_primary_parts(v):
    """== primaryParts?: the (day part, signed clock part) the standard branch
    builds, or None when the standard notation does not apply."""
    w = _drop_final_newline(v)
    if ' ' in w:
        before, after = w.split(' ', 1)
        d = _signed_int(before)
        if d is not None:
            t = _parse_clock(_strip_unit(after))
            if t is None:
                return None
            return (d * 86400 * 10 ** 6, t)
        t = _parse_clock(w)
        return None if t is None else (0, t)
    t = _parse_clock(w)
    return None if t is None else (0, t)


def shadow_primary(v):
    """== primaryFormatMicros (deep R/I model of the standard clock branch)."""
    p = shadow_primary_parts(v)
    return None if p is None else p[0] + p[1]


def fallback_micros(value):
    """A-reference: the UNCHANGED iso8601 + postgres arms of parse_duration,
    left as the real repo parsing. Equivalent to parse_duration restricted to
    the case where the standard regex does NOT match."""
    if standard_duration_re.match(value):
        # standard branch handled by shadow_primary; fallback inapplicable
        return None
    return patched_micros(value)


def shadow_micros(value):
    p = shadow_primary(value)
    if p is not None:
        return p
    return fallback_micros(value)


# ---------------------------------------------------------------------------
# The spec's two domain side conditions (Solution.lean: asciiText / primaryInRange)
# ---------------------------------------------------------------------------
def ascii_text(v):
    """== asciiText."""
    return all(ord(c) < 128 for c in v)


def _in_us_range(x):
    return US_MIN <= x <= US_MAX


def primary_in_range(v):
    """== primaryInRange."""
    p = shadow_primary_parts(v)
    if p is None:
        return True
    dus, tus = p
    return _in_us_range(dus) and _in_us_range(tus) and _in_us_range(dus + tus)


def in_domain(v):
    return ascii_text(v) and primary_in_range(v)


# ---------------------------------------------------------------------------
# Digit alphabets. Only ASCII is inside the spec's domain; the other three are
# generated on purpose so side condition 1 is measured rather than assumed.
_ALPHABETS = (
    '0123456789',            # ASCII
    '٠١٢٣٤٥٦٧٨٩',  # Arabic-Indic
    '０１２３４５６７８９',  # fullwidth
    '०१२३४५६७८९',  # Devanagari
)

_FIXED = (
    'P4Y', 'P4M', 'P4W', 'P4D', 'P0.5D', 'PT5H', 'PT5M', 'PT5S',
    'PT0.000005S', '-P4D', '+PT5H', 'P1DT2H3M4S', 'P', 'PT',
    '1 day', '1 day 0:00:01', '1 day -0:00:01', '-1 day -0:00:01',
    '-1 day +0:00:01', '4 days 0:15:30.1', '4 days 0:15:30.0001',
    '-4 days -15:00:30', '3 days 04:05:06', '00:00:00',
)


def _tok(rng, big):
    alpha = _ALPHABETS[0] if rng.random() < 0.80 else rng.choice(_ALPHABETS)
    n = rng.randint(1, 22) if big else rng.randint(1, 4)
    return ''.join(rng.choice(alpha) for _ in range(n))


def gen(rng):
    r = rng.random()
    if r < 0.08:
        return rng.choice(_FIXED)
    big = rng.random() < 0.25
    out = ''
    if rng.random() < 0.42:
        out += ('-' if rng.random() < 0.4 else '') + _tok(rng, big) + ' '
        u = rng.random()
        if u < 0.30:
            out += 'days, '
        elif u < 0.50:
            out += 'day, '
        elif u < 0.60:
            out += 'days '          # postgres-ish spacing
    if rng.random() < 0.5:
        out += '-'
    out += ':'.join(_tok(rng, big) for _ in range(rng.randint(1, 4)))
    if rng.random() < 0.35:
        out += '.' + _tok(rng, big)
    if rng.random() < 0.12:
        out += '\n'                 # the trailing-newline family the spec MODELS
    if rng.random() < 0.03:
        out += rng.choice(['\n', 'x', '\t', ' ', '€'])
    return out


def main():
    rng = random.Random(SEED)
    cases = [
        '-4 15:30', '-172800', '-15:30', '-1:15:30', '-30.1',
        '-00:01:01', '-01:01', '-01:-01', '30', '15:30', '5:30',
        '10:15:30', '1:15:30', '100:200:300', '15:30.1', '15:30.0001',
        '15:30.000001', '4 days, 0:15:30', '4 15:30', '-4 days, -15:00:30',
        '1 day, 0:00:01', 'P4D', 'PT5H', '1 day -0:00:01', '', '-', '5:',
        '5::6', '1:2:3:4', '12.1234567890123',
        # trailing-newline family (in domain; the spec models it)
        '30\n', '15:30\n', '-15:30\n', '1 day, 0:00:01\n', '5\n\n', '\n',
        # representable-magnitude boundary (in domain, and just outside it)
        '999999999 0', '86399999913600', '86399999999999.999999',
        '-999999999 0', '86400000000000', '1000000000 0',
        '999999999999:00:00', '99999999999999999999',
        # non-ASCII digit family (outside side condition 1)
        '٥', '٣٠', '١٢:٣٤',
        '１２３', '४२', '٠.٥',
    ]
    cases += [gen(rng) for _ in range(N)]

    n_in = 0
    n_out_ascii = 0
    n_out_range = 0
    n_newline = 0
    disagreements = 0
    examples = []
    for value in cases:
        if not ascii_text(value):
            n_out_ascii += 1
            continue
        if not primary_in_range(value):
            n_out_range += 1
            continue
        n_in += 1
        if value.endswith('\n'):
            n_newline += 1
        want = patched_micros(value)
        got = shadow_micros(value)
        if got != want:
            disagreements += 1
            if len(examples) < 12:
                examples.append((value, got, want))

    print(f"G-CONF domain: {n_in} in-domain, {n_out_ascii} excluded by "
          f"asciiText, {n_out_range} excluded by primaryInRange "
          f"({n_newline} in-domain trailing-newline inputs)")

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements / {n_in} in-domain inputs")
        for v, g, w in examples:
            print(f"  value={v!r} shadow={g} patched={w}")
        return 1
    # A domain condition that stopped selecting anything would make the run
    # vacuous in one direction or the other, so both are required to bite and
    # the in-domain corpus is required to stay above the 10^5 floor.
    if n_in < 100_000:
        print(f"G-CONF FAIL: only {n_in} in-domain inputs (< 10^5)")
        return 1
    if n_out_ascii == 0 or n_out_range == 0 or n_newline == 0:
        print("G-CONF FAIL: a declared family was never generated "
              f"(non-ascii={n_out_ascii}, out-of-range={n_out_range}, "
              f"trailing-newline={n_newline})")
        return 1
    print(f"G-CONF OK: {n_in} in-domain inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
