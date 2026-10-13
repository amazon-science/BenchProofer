#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11728 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (`str`): `next_bal`/`scan_len`
              (the deep scan model) embedded inside the GENUINELY-UNCHANGED host
              code of `replace_named_groups`/`replace_unnamed_groups` (match
              producer + textual substitution), via the mapping.md bijection
              (`List Char` ↔ `str`; `scanLen … = some k` ↔ slice end base+k;
              `none` ↔ no slice recorded). This isolates the R/I legs: the only
              changed op (the inner scan) is the shadow; everything around it is
              copied verbatim from the repo.
  * ORACLE  — `patch.diff`'s behaviour: the patched `replace_named_groups` /
              `replace_unnamed_groups` imported from the repo at base_commit with
              the gold patch applied (the real correctness oracle, G-RESOLVE).
              We also pin the end-to-end `simplify_regex` wrapper.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import re
import sys

SEED = 11728
N_FUZZ = 100_000

# The two unchanged module-level matchers (position producers). Imported from
# the repo where possible; verbatim fallback otherwise.
try:
    from django.contrib.admindocs.utils import (
        named_group_matcher as _NG, unnamed_group_matcher as _UG,
    )
except Exception:  # pragma: no cover
    _NG = re.compile(r'\(\?P(<\w+>)')
    _UG = re.compile(r'\(')


# --- the R/I shadow: Solution.lean nextBal/scanLen, transliterated -----------
def next_bal(prev, bal, c):
    if c == '(' and prev != '\\':
        return bal + 1
    if c == ')' and prev != '\\':
        return bal - 1
    return bal


def scan_len(rest):
    """scanLen none 1 rest : characters consumed up to & incl. the balancing
    bracket, or None. The deep model the verified loop computes."""
    prev, bal = None, 1
    for idx, c in enumerate(rest):
        bal = next_bal(prev, bal, c)
        if bal == 0:
            return idx + 1
        prev = c
    return None


def shadow_replace_named_groups(pattern):
    """replace_named_groups with the inner scan replaced by the shadow `scan_len`
    (mapping.md §3.1: scan_len(pattern[end:]) = some k -> slice end = end+k).
    Every other line is copied verbatim from the repo function."""
    named_group_indices = [
        (m.start(0), m.end(0), m.group(1)) for m in _NG.finditer(pattern)
    ]
    group_pattern_and_name = []
    for start, end, group_name in named_group_indices:
        k = scan_len(pattern[end:])
        if k is not None:  # `some k` -> record; `none` -> leave group untouched
            group_pattern_and_name.append((pattern[start:end + k], group_name))
    for group_pattern, group_name in group_pattern_and_name:
        pattern = pattern.replace(group_pattern, group_name)
    return pattern


def shadow_replace_unnamed_groups(pattern):
    """replace_unnamed_groups with the inner scan replaced by the shadow
    `scan_len` (mapping.md §3.1: scan_len(pattern[start+1:]) = some k -> end =
    (start+1)+k). Every other line is copied verbatim from the repo function."""
    unnamed_group_indices = [m.start(0) for m in _UG.finditer(pattern)]
    group_indices = []
    for start in unnamed_group_indices:
        k = scan_len(pattern[start + 1:])
        if k is not None:
            group_indices.append((start, start + 1 + k))
    # --- unchanged tail copied verbatim from the repo function ---------------
    group_start_end_indices = []
    prev_end = None
    for start, end in group_indices:
        if prev_end and start > prev_end or not prev_end:
            group_start_end_indices.append((start, end))
        prev_end = end
    if group_start_end_indices:
        final_pattern, prev_end = [], None
        for start, end in group_start_end_indices:
            if prev_end:
                final_pattern.append(pattern[prev_end:start])
            final_pattern.append(pattern[:start] + '<var>')
            prev_end = end
        final_pattern.append(pattern[prev_end:])
        return ''.join(final_pattern)
    else:
        return pattern


def oracle_named(pattern):
    from django.contrib.admindocs.utils import replace_named_groups
    return replace_named_groups(pattern)


def oracle_unnamed(pattern):
    from django.contrib.admindocs.utils import replace_unnamed_groups
    return replace_unnamed_groups(pattern)


def fuzz_inputs(n, rng):
    # boundary patterns first (plan §4.1 step 4) — the F2P test_simplify_regex
    # corpus + the issue's trailing-group shapes + escapes/nesting.
    yield from [
        r'',
        r'^a',
        r'^(?P<a>\w+)/b/(?P<c>\w+)/$',
        r'^(?P<a>\w+)/b/(?P<c>\w+)$',
        r'^(?P<a>\w+)/b/(?P<c>\w+)',
        r'^(?P<a>\w+)/b/(\w+)$',
        r'^(?P<a>\w+)/b/(\w+)',
        r'^(?P<a>\w+)/b/((x|y)\w+)$',
        r'^(?P<a>\w+)/b/((x|y)\w+)',
        r'^(?P<a>(x|y))/b/(?P<c>\w+)$',
        r'^(?P<a>(x|y))/b/(?P<c>\w+)',
        r'^(?P<a>(x|y))/b/(?P<c>\w+)ab',
        r'^(?P<a>(x|y)(\(|\)))/b/(?P<c>\w+)ab',
        r'entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        r'(?P<a>x\))y',
        r'(?P<a>\\)',
        r'(\()',
        r'(?P<a>',
        r'a/?$',
    ]
    significant = ['(', ')', '\\', '?', 'P', '<', '>']
    ordinary = list("ab/wxyz019|.+*$^") + [
        '?P<a>', '?P<c>', '?P<pk>', '\\w+', '(?P<', '(', ')', '/', '\\)', '\\(',
    ]
    alphabet = significant + ordinary
    for _ in range(n):
        k = rng.randint(0, 16)
        yield ''.join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        sh_n, or_n = shadow_replace_named_groups(s), oracle_named(s)
        if sh_n != or_n:
            disagreements.append(("named", s, sh_n, or_n))
        sh_u, or_u = shadow_replace_unnamed_groups(s), oracle_unnamed(s)
        if sh_u != or_u:
            disagreements.append(("unnamed", s, sh_u, or_u))
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for which, s, sh, orc in disagreements:
            print("  [%s] input=%r shadow=%r oracle=%r" % (which, s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of scanGroupEnd (embedded in the unchanged "
          "replace_named_groups/replace_unnamed_groups hosts) agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
