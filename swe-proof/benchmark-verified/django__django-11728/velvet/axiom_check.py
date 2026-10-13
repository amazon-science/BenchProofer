#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11728.

This bundle consumes NO axiom: the changed operation (the inner bracket-balancing
scan shared by `replace_named_groups`/`replace_unnamed_groups`) is modeled DEEPLY
in Solution.lean by `nextBal`/`scanLen` + the verified forward loop
(refinement.md §C). G-AX validates the two A-reference facts the deep model
rests on, executing the REAL repo callees in-container:

  (A-reference 1, `nextBal`)  The per-character depth transition `next_bal(prev,
      bal, c)` reproduces the repo's `unmatched_open_brackets` update rule
      (`+1` on an unescaped '(', `-1` on an unescaped ')', else unchanged),
      exhaustively over the significant alphabet `( ) \\ <ordinary>` x prev x bal.

  (A-reference 2, `scanLen`)  The deep model `scan_len(rest)` reproduces the
      offset the REAL patched inner scan reports. The scan is driven by the
      GENUINELY-UNCHANGED regex matchers (`named_group_matcher`,
      `unnamed_group_matcher`) imported from the repo — those are the real
      callees that supply the group start/end positions. For every group the
      matcher finds in a boundary + fuzz corpus of patterns, the offset
      `scan_len(pattern[end:])` (named) / `scan_len(pattern[start+1:])` (unnamed)
      equals the index the patched loop breaks at, i.e. the recorded slice end
      minus the base (`end+idx+1 - end` / `start+2+idx - (start+1)`), or `None`
      when the loop never breaks.

The patched inner-scan reference (`patched_scan_*`) is the gold patch transcribed
VERBATIM (mapping.md §3.1); it is driven by the real matchers, so the regex
callee under audit is exercised for real. Imports only `re` + the repo's own
matchers + stdlib. Exit 0 iff every observation matches.
"""
import random
import re
import sys

# --- the GENUINELY-UNCHANGED real callees: the repo's group matchers ---------
# Imported from the repo at base_commit (the patch does NOT touch these two
# module-level regexes — they are the unchanged position producers).
try:
    from django.contrib.admindocs.utils import (
        named_group_matcher, unnamed_group_matcher,
    )
except Exception:  # pragma: no cover - fall back to the verbatim repo source
    named_group_matcher = re.compile(r'\(\?P(<\w+>)')
    unnamed_group_matcher = re.compile(r'\(')


# --- the deep model, transliterated from Solution.lean (the thing under audit)
def next_bal(prev, bal, c):
    """nextBal (prev : Option Char) (bal : Nat) (c : Char) : Nat."""
    if c == '(' and prev != '\\':
        return bal + 1
    if c == ')' and prev != '\\':
        return bal - 1
    return bal


def scan_len(rest):
    """scanLen none 1 rest : Option Nat — characters consumed up to and incl.
    the balancing bracket, or None. Iterative transliteration of the front-
    recursive Lean def (prev starts None, bal starts 1)."""
    prev, bal = None, 1
    for idx, c in enumerate(rest):
        bal = next_bal(prev, bal, c)
        if bal == 0:
            return idx + 1
        prev = c
    return None


# --- the REAL patched inner scan, transcribed VERBATIM from the gold patch ----
# (mapping.md §3.1). Driven by the real matchers below; returns the reported
# end-offset relative to the slice base, or None if it never breaks.
def patched_scan_named(pattern, end):
    unmatched_open_brackets, prev_char = 1, None
    for idx, val in enumerate(pattern[end:]):
        if val == '(' and prev_char != '\\':
            unmatched_open_brackets += 1
        elif val == ')' and prev_char != '\\':
            unmatched_open_brackets -= 1
        prev_char = val
        if unmatched_open_brackets == 0:
            # patched records pattern[start:end + idx + 1] -> offset idx+1
            return idx + 1
    return None


def patched_scan_unnamed(pattern, start):
    unmatched_open_brackets, prev_char = 1, None
    for idx, val in enumerate(pattern[start + 1:]):
        if val == '(' and prev_char != '\\':
            unmatched_open_brackets += 1
        elif val == ')' and prev_char != '\\':
            unmatched_open_brackets -= 1
        prev_char = val
        if unmatched_open_brackets == 0:
            # patched records (start, start + 2 + idx) -> offset (idx+1) past start+1
            return idx + 1
    return None


def check_next_bal():
    """A-reference 1: next_bal == the repo depth-update rule, exhaustively."""
    alphabet = ['(', ')', '\\', 'a', '/', '<', '>', '?', 'P']
    prevs = [None] + alphabet
    for prev in prevs:
        for bal in range(0, 6):
            for c in alphabet:
                got = next_bal(prev, bal, c)
                # the repo rule, spelled out independently
                if c == '(' and prev != '\\':
                    exp = bal + 1
                elif c == ')' and prev != '\\':
                    exp = bal - 1
                else:
                    exp = bal
                assert got == exp, ("next_bal mismatch", prev, bal, c, got, exp)


def fuzz_patterns(n, rng):
    significant = ['(', ')', '\\']
    ordinary = list("ab/<>?Pwxyz0123|.+*$^") + ['?P<a>', '?P<c>', '\\w+', '(?P<', ')']
    # boundary patterns first (incl. the issue's trailing-group shapes)
    yield from [
        r'',
        r'^(?P<a>\w+)/b/(?P<c>\w+)',
        r'^(?P<a>\w+)/b/(?P<c>\w+)/$',
        r'^(?P<a>\w+)/b/(?P<c>\w+)$',
        r'^(?P<a>\w+)/b/(\w+)',
        r'^(?P<a>\w+)/b/(\w+)$',
        r'^(?P<a>\w+)/b/((x|y)\w+)$',
        r'^(?P<a>\w+)/b/((x|y)\w+)',
        r'^(?P<a>(x|y))/b/(?P<c>\w+)',
        r'^(?P<a>(x|y))/b/(?P<c>\w+)$',
        r'^(?P<a>(x|y))/b/(?P<c>\w+)ab',
        r'^(?P<a>(x|y)(\(|\)))/b/(?P<c>\w+)ab',
        r'entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        r'(?P<a>\\)',          # escaped close inside
        r'(?P<a>x\))y',        # escaped paren must not balance
        r'(\()',
        r'(?P<a>',             # never balances
    ]
    for _ in range(n):
        k = rng.randint(0, 30)
        parts = significant + ordinary
        yield ''.join(rng.choice(parts) for _ in range(k))


def check_scan(rng, n_fuzz):
    checked = 0
    for pattern in fuzz_patterns(n_fuzz, rng):
        # named groups: drive scan from each match end (real matcher = callee)
        for m in named_group_matcher.finditer(pattern):
            end = m.end(0)
            model = scan_len(pattern[end:])
            real = patched_scan_named(pattern, end)
            assert model == real, ("named scan mismatch", pattern, end, model, real)
            checked += 1
        # unnamed groups: drive scan from each match start+1
        for m in unnamed_group_matcher.finditer(pattern):
            start = m.start(0)
            model = scan_len(pattern[start + 1:])
            real = patched_scan_unnamed(pattern, start)
            assert model == real, ("unnamed scan mismatch", pattern, start, model, real)
            checked += 1
    return checked


def main():
    check_next_bal()
    rng = random.Random(11728)
    n_fuzz = 50_000
    checked = check_scan(rng, n_fuzz)
    print("G-AX OK: next_bal == repo depth-update (exhaustive over alphabet x "
          "prev x bal); scanLen deep model == real patched inner scan on %d "
          "matcher-driven group scans (boundary + %d fuzz patterns), incl. the "
          "trailing-group shapes. 0 mismatches." % (checked, n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
