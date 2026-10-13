#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11728.

There is NO consumed @ContractOnly axiom in model.py (the `axioms` region is
empty). The changed behaviour -- the depth-tracking scan that finds a capture
group's matching closing parenthesis and the span end it yields -- is modelled
DEEPLY in model.py (`close_off` / `step_bal` over PSeq[int]). This script is the
A-REFERENCE validation: it executes the REAL Python inner-loop scan (byte-for-
byte the post-patch loop body from `django/contrib/admindocs/utils.py`) on
boundary + randomized-fuzz inputs and asserts the deep model reproduces it at
the INDEX level (the matching-close offset and the recorded span end), with no
double-masking. It additionally asserts, on the FAIL_TO_PASS trailing-group
patterns, that the post-patch scan records the group and the pre-patch scan
drops it (the discriminating direction).

Imports only the standard library (`re`, `random`) -- `re` is used solely to
locate group START positions, exactly as the real functions do; the scan itself
is pure Python. Exit 0 iff every obligation holds.
"""
import random
import re
import sys

LPAREN, RPAREN, BSLASH = 40, 41, 92


# --- model.py reference encodings (kept in lock-step with model.py) ----------

def step_bal(c, prev, bal):
    """Reference of model.py `step_bal`."""
    if c == LPAREN and prev != BSLASH:
        return bal + 1
    if c == RPAREN and prev != BSLASH:
        return bal - 1
    return bal


def close_off(s, bal, prev):
    """Reference of model.py `close_off`: offset within code-point list `s` of
    the char that first drives the depth to zero; len(s) if none. Iterative to
    avoid Python recursion limits on long fuzz inputs."""
    i = 0
    n = len(s)
    while i < n:
        nb = step_bal(s[i], prev, bal)
        if nb == 0:
            return i
        prev = s[i]
        bal = nb
        i += 1
    return n


# --- the REAL scan (post-patch, lifted verbatim from utils.py) ---------------

def real_scan_postpatch(slice_str):
    """The post-patch inner loop. Returns the scan-relative span END
    (`idx + 1`) recorded for the group already open at depth 1, or None if the
    matching close is never reached within `slice_str`."""
    unmatched_open_brackets, prev_char = 1, None
    for idx, val in enumerate(slice_str):
        if val == '(' and prev_char != '\\':
            unmatched_open_brackets += 1
        elif val == ')' and prev_char != '\\':
            unmatched_open_brackets -= 1
        prev_char = val
        if unmatched_open_brackets == 0:
            return idx + 1
    return None


def real_scan_prepatch(slice_str):
    """The pre-patch inner loop (top-check). Returns the recorded span end, or
    None if never recorded (the bug)."""
    unmatched_open_brackets, prev_char = 1, None
    for idx, val in enumerate(slice_str):
        if unmatched_open_brackets == 0:
            return idx          # records pattern[start:end + idx]
        if val == '(' and prev_char != '\\':
            unmatched_open_brackets += 1
        elif val == ')' and prev_char != '\\':
            unmatched_open_brackets -= 1
        prev_char = val
    return None


# --- the checks --------------------------------------------------------------

def check_reference(slice_str):
    """INDEX-level A-reference check: when the real post-patch scan reports a
    span end, the deep model `close_off` reports the same matching-close offset
    AND span end (no value-membership proxy)."""
    cps = [ord(ch) for ch in slice_str]
    real_end = real_scan_postpatch(slice_str)        # idx+1, or None
    model_k = close_off(cps, 1, 0)                    # matching-close offset
    if real_end is None:
        # No matching close in the slice: the model must agree (k == len).
        assert model_k == len(cps), (
            "deep model claims a close at %d but real scan finds none in %r"
            % (model_k, slice_str))
        return
    # Matching close exists: index-level agreement on the close offset...
    assert model_k == real_end - 1, (
        "close offset mismatch on %r: real idx-at-close=%d, model close_off=%d"
        % (slice_str, real_end - 1, model_k))
    # ...and on the span end the model.py postcondition pins (close_off + 1).
    assert model_k + 1 == real_end, (
        "span-end mismatch on %r: real=%d, model close_off+1=%d"
        % (slice_str, real_end, model_k + 1))


# Inner-slice extractors mirroring the two real functions' base offsets.
NAMED = re.compile(r'\(\?P(<\w+>)')
UNNAMED = re.compile(r'\(')


def named_slices(pattern):
    return [pattern[m.end(0):] for m in NAMED.finditer(pattern)]


def unnamed_slices(pattern):
    return [pattern[m.start(0) + 1:] for m in UNNAMED.finditer(pattern)]


def main():
    # --- boundary slices (depth-1 scan regions) ---------------------------
    boundary = [
        r'\w+)',            # simple group, close at end
        r'\w+)/',           # close followed by '/'
        r'\w+)$',           # close followed by '$'
        r'\w+)ab',          # close followed by text
        r'(x|y)\w+)',       # nested group, close at end
        r'(x|y)\w+)$',
        r'(x|y)(\(|\)))/b', # escaped parens inside
        r'(x|y)(\(|\)))ab',
        r')',               # immediate close
        r'a)',
        r'\)\))',           # escaped closes then real close
        r'(((x))))',        # deep nesting
    ]
    for s in boundary:
        # only meaningful when a close exists; check_reference handles None too
        check_reference(s)

    # --- the FAIL_TO_PASS patterns, via BOTH real slice extractors --------
    f2p_patterns = [
        r'^(?P<a>\w+)/b/(?P<c>\w+)',          # trailing named group (the bug)
        r'^(?P<a>\w+)/b/(\w+)',               # trailing unnamed group
        r'^(?P<a>\w+)/b/((x|y)\w+)',          # trailing nested unnamed group
        r'^(?P<a>(x|y))/b/(?P<c>\w+)',        # trailing named after nested named
        r'^(?P<a>\w+)/b/(?P<c>\w+)/$',        # non-trailing (control)
        r'^(?P<a>\w+)/b/(?P<c>\w+)$',
        r'^(?P<a>(x|y)(\(|\)))/b/(?P<c>\w+)ab',
    ]
    discriminating_seen = 0
    for pat in f2p_patterns:
        for sl in named_slices(pat) + unnamed_slices(pat):
            check_reference(sl)
            # Discriminating direction: when the matching close is the LAST char
            # of the slice, post-patch records it and pre-patch drops it.
            cps = [ord(ch) for ch in sl]
            k = close_off(cps, 1, 0)
            if k == len(cps) - 1:        # close is the final character
                post = real_scan_postpatch(sl)
                pre = real_scan_prepatch(sl)
                assert post == k + 1, (
                    "post-patch failed to record trailing group on %r" % sl)
                assert pre is None, (
                    "pre-patch unexpectedly recorded trailing group on %r "
                    "(expected the bug to drop it)" % sl)
                discriminating_seen += 1
    assert discriminating_seen > 0, (
        "no trailing-group discriminating case exercised -- the F2P fix "
        "direction was not actually tested (would be a false pass)")

    # --- randomized fuzz over the regex-ish alphabet ----------------------
    rng = random.Random(11728)
    alphabet = list('()\\aZ0/|?P<>w+.$^[]{}-')
    fuzz = 0
    for _ in range(40000):
        n = rng.randint(0, 30)
        s = ''.join(rng.choice(alphabet) for _ in range(n))
        check_reference(s)
        fuzz += 1

    print("G-AX OK: close_off/step_bal deep model (A-reference) == real "
          "post-patch scan on %d boundary + %d F2P slices + %d fuzz inputs; "
          "%d trailing-group discriminating cases confirmed "
          "(post-patch records, pre-patch drops)."
          % (len(boundary), len(f2p_patterns), fuzz, discriminating_seen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
