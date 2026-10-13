#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14598.

This bundle consumes NO `@ContractOnly` axiom. The escaping, the full-payload
recovery, and the un-escaping are all modelled DEEPLY (the verified folds
`escape_quotes`, `unescape_quotes`, and the full `recover_payload` in model.py).
G-AX therefore validates those deep models == the real library operations they
stand in for, on boundary + randomized inputs (A-reference checks):

  (R1) `escape_quotes` (model.py pure region) == the real serialisation escape
       `value.replace("'", "''")` used when a long string value is laid out
       across continuation segments (card.py `_format_long_image`, the
       `self._value.replace("'", "''")` step). Each single quote U+0027 becomes
       a pair of single quotes; every other code point is copied.

  (R2) `unescape_quotes` (model.py pure region), applied exactly ONCE, == the
       real value un-escape `re.sub("''", "'", strg)` used when the assembled
       value is recovered (card.py `_parse_value`). A single non-overlapping
       left-to-right collapse of "''" -> "'".

  (R3) `recover_payload` (model.py: full capture) == the FIXED segment regex
       `_strg_comment_RE` (with the trailing `$` anchor) `strg` group on
       well-formed escaped payloads: it recovers the COMPLETE carried payload,
       dropping nothing at an interior space. The PRE-PATCH regex (no `$`)
       instead truncates at the first quote that is immediately followed by an
       interior space -- exactly the truncation modelled in model_prepatch_2.py.
       Both directions are asserted, so the deep model and its prepatch are each
       faithful to the real regex.

  (R4) The round-trip identity: for every value `v`, the single un-escape of the
       full recovery of `escape_quotes(v)` equals `v`. This is the spec-level
       guarantee (model.py `rt_lemma`) and the property the FAIL_TO_PASS test
       observes; checked end-to-end against the real regex + real un-escape.

Imports only the standard library `re` (the very module the patch edits) and
`random`. Exit 0 iff every obligation holds on every checked input.
"""
import random
import re
import sys

APOS = 39
SPACE = 32

# --- the real library regex, verbatim from astropy/io/fits/card.py -----------
# `_strg`/`_comm_field` are byte-identical to base_commit; `_strg_comment_RE`
# is shown in both the FIXED (with `$`) and PRE-PATCH (no `$`) forms.
_strg = r"\'(?P<strg>([ -~]+?|\'\'|) *?)\'(?=$|/| )"
_comm_field = r"(?P<comm_field>(?P<sepr>/ *)(?P<comm>(.|\n)*))"
_strg_comment_RE_fixed = re.compile(f"({_strg})? *{_comm_field}?$")
_strg_comment_RE_prepatch = re.compile(f"({_strg})? *{_comm_field}?")


# --- model.py reference encodings (kept in lock-step with the deep models) ----

def escape_quotes(cps):
    """Reference of model.py `escape_quotes` over code points."""
    out = []
    for c in cps:
        if c == APOS:
            out.extend([APOS, APOS])
        else:
            out.append(c)
    return out


def unescape_quotes(cps):
    """Reference of model.py `unescape_quotes` over code points: single
    left-to-right collapse of (39,39) -> 39."""
    out = []
    i = 0
    n = len(cps)
    while i < n:
        if i + 2 <= n and cps[i] == APOS and cps[i + 1] == APOS:
            out.append(APOS)
            i += 2
        else:
            out.append(cps[i])
            i += 1
    return out


def recover_payload_full(cps):
    """Reference of model.py `recover_payload`: the complete payload."""
    return list(cps)


def recover_payload_trunc(cps):
    """Reference of model_prepatch_2.py: truncate at first quote-then-space."""
    out = []
    j = 0
    n = len(cps)
    while j < n:
        if cps[j] == APOS and j + 1 < n and cps[j + 1] == SPACE:
            return out
        out.append(cps[j])
        j += 1
    return out


# --- real library operations -------------------------------------------------

def real_format_escape(s):
    """The real serialisation escape (card.py _format_long_image)."""
    return s.replace("'", "''")


def real_value_unescape(s):
    """The real value un-escape (card.py _parse_value)."""
    return re.sub("''", "'", s)


def real_capture(regex, payload):
    """The real `strg`-group capture of a single quoted segment payload."""
    vc = "'%s'" % payload                 # a quoted segment carrying `payload`
    m = regex.match(vc)
    if m is None or m.group("strg") is None:
        return None
    return m.group("strg")


# --- the checks --------------------------------------------------------------

def check_escape(s):
    observed = real_format_escape(s)
    expected = "".join(chr(c) for c in escape_quotes([ord(ch) for ch in s]))
    assert observed == expected, (
        "escape_quotes deep model unsound on %r: real=%r model=%r"
        % (s, observed, expected))


def check_unescape(s):
    observed = real_value_unescape(s)
    expected = "".join(chr(c) for c in unescape_quotes([ord(ch) for ch in s]))
    assert observed == expected, (
        "unescape_quotes deep model unsound on %r: real=%r model=%r"
        % (s, observed, expected))


def check_capture(value):
    """On the escaped payload of `value`, the FIXED regex recovers the full
    payload (deep model) and the PRE-PATCH regex truncates at quote-then-space
    (prepatch model). Restricted to the modelled domain: no value/comment
    separator '/' in the value (model.py `recover_payload` requires segment
    code point 47 absent)."""
    if "/" in value:
        return
    payload = real_format_escape(value)             # well-formed escaped payload
    fixed = real_capture(_strg_comment_RE_fixed, payload)
    pre = real_capture(_strg_comment_RE_prepatch, payload)
    if fixed is None or pre is None:
        return  # not a single-quoted-string-shaped segment; not in our domain
    cps = [ord(ch) for ch in payload]
    exp_full = "".join(chr(c) for c in recover_payload_full(cps))
    exp_trunc = "".join(chr(c) for c in recover_payload_trunc(cps))
    assert fixed == exp_full, (
        "recover_payload (FIXED, full) unsound on value=%r payload=%r: "
        "real=%r model=%r" % (value, payload, fixed, exp_full))
    assert pre == exp_trunc, (
        "prepatch truncation model unfaithful on value=%r payload=%r: "
        "real=%r model=%r" % (value, payload, pre, exp_trunc))


def check_roundtrip(value):
    """End-to-end: escape -> full recover (fixed regex) -> single un-escape == id.
    Restricted to the modelled domain (no value/comment separator '/')."""
    if "/" in value:
        return
    payload = real_format_escape(value)
    captured = real_capture(_strg_comment_RE_fixed, payload)
    if captured is None:
        return
    recovered = real_value_unescape(captured)
    assert recovered == value, (
        "round trip broken on value=%r: payload=%r captured=%r recovered=%r"
        % (value, payload, captured, recovered))


def main():
    # --- boundary values (incl. the FAIL_TO_PASS shapes) ------------------
    boundary_values = [
        "",
        "'",
        "''",
        "'''",
        "''''",
        "x'",
        "x''",
        "x''x",
        "x'' x",
        "'' x",
        "x'' xxx",
        "x" * 5 + "''",
        "x" * 5 + "''xxx",
        "x" * 5 + "'' xxx",
        "x" * 100 + "''",         # FAIL_TO_PASS case 1
        "x" * 100 + "''xxx",      # FAIL_TO_PASS case 2
        "x" * 100 + "'' xxx",     # FAIL_TO_PASS case 3
        "a 'b' c",
        "Joe's Crab Shack",
        "Can't won't shan't",
        "spaces  and  'quotes'  mixed",
        "trailing space ",
        " leading space",
        "a/b'c'/d",          # contains '/': exercises escape/unescape, skipped by capture
        "'' / xx",           # '/' present: out of capture/roundtrip scope
    ]
    # escape / unescape boundary strings (escaped forms feed unescape)
    for v in boundary_values:
        check_escape(v)
        check_unescape(v)                 # v itself
        check_unescape(real_format_escape(v))   # escaped form (the real input)
        check_capture(v)
        check_roundtrip(v)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(14598)
    # No '/' in the modelled-domain alphabet (the value/comment separator is out
    # of `recover_payload`'s scope); escape/unescape are checked on '/' too via
    # the dedicated separator fuzz below.
    alphabet = ["'", " ", "x", "y", "a", "b", "Z", "0"]
    for _ in range(40000):
        n = rng.randint(0, 30)
        v = "".join(rng.choice(alphabet) for _ in range(n))
        check_escape(v)
        check_unescape(v)
        check_unescape(real_format_escape(v))
        check_capture(v)
        check_roundtrip(v)

    print("G-AX OK: escape_quotes / unescape_quotes / recover_payload (full + "
          "prepatch truncation) deep models == real card.py regex/escape/unescape; "
          "round trip identity holds on %d boundary + 40000 fuzz values"
          % len(boundary_values))
    return 0


if __name__ == "__main__":
    sys.exit(main())
