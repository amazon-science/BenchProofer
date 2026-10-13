#!/usr/bin/env python3
"""G-CONF for django__django-11728.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_findGroupEnd` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched `replace_named_groups` /
`replace_unnamed_groups`, over >=1e5 fuzzed regex-like `pattern` strings. Zero
disagreements => exit 0.

Bridging (mapping.md): the modeled scan finds the offset `i` at which a group's
open parenthesis closes, given the slice of characters AFTER that open paren.
Rather than reach inside the real functions, we rebuild each whole function using
ONLY the unchanged surrounding logic (the same group-start regexes and the same
substring/index bookkeeping) with the inner scan provided by our `findGroupEnd`
shadow, and diff the FINAL output string against the REAL patched function's
output. Agreement on every fuzzed pattern => the modeled scan matches the patch.

Type bijection: cs:List Char <-> the scanned slice (pattern[end:] for named,
pattern[start+1:] for unnamed) as a Python str; result some i:Option Nat <-> the
loop reaches depth 0 at enumerate index i; none <-> the group never closes. The
real recorded index is i shifted by a constant (end+i+1 / start+2+i).
stdlib-only; no third-party deps.
"""
import os
import random
import re
import sys

# --- configure Django settings before importing the admindocs utils ----------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, USE_L10N=False, USE_I18N=False,
        DATABASES={}, INSTALLED_APPS=[],
    )
    django.setup()

from django.contrib.admindocs import utils as admindocs_utils

REAL_NAMED = admindocs_utils.replace_named_groups
REAL_UNNAMED = admindocs_utils.replace_unnamed_groups

# A-reference (unchanged): the module group-start regexes.
named_group_matcher = re.compile(r'\(\?P(<\w+>)')
unnamed_group_matcher = re.compile(r'\(')


# --- shadow of implementation_findGroupEnd (Lean impl, op-for-op) -------------
def find_group_end(cs):
    """Offset within `cs` (the chars after the group's open paren) at which the
    group closes (depth back to 0), or None if it never closes. Mirrors
    implementation_findGroupEnd exactly: depth starts at 1; the depth-zero check
    sits AFTER the per-char update (the post-patch relocation)."""
    depth = 1
    prev = None
    for idx, val in enumerate(cs):
        if val == '(' and prev != '\\':
            depth += 1
        elif val == ')' and prev != '\\':
            depth -= 1
        prev = val
        if depth == 0:
            return idx
    return None


# --- shadows of the two whole functions, using find_group_end for the scan ----
def shadow_named(pattern):
    named_group_indices = [
        (m.start(0), m.end(0), m.group(1))
        for m in named_group_matcher.finditer(pattern)
    ]
    group_pattern_and_name = []
    for start, end, group_name in named_group_indices:
        off = find_group_end(pattern[end:])          # modeled scan
        if off is not None:
            # real recorded slice: pattern[start:end + idx + 1]
            group_pattern_and_name.append((pattern[start:end + off + 1], group_name))
    for group_pattern, group_name in group_pattern_and_name:
        pattern = pattern.replace(group_pattern, group_name)
    return pattern


def shadow_unnamed(pattern):
    unnamed_group_indices = [m.start(0) for m in unnamed_group_matcher.finditer(pattern)]
    group_indices = []
    for start in unnamed_group_indices:
        off = find_group_end(pattern[start + 1:])    # modeled scan
        if off is not None:
            # real recorded index pair: (start, start + 2 + idx)
            group_indices.append((start, start + 2 + off))
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
    return pattern


# --- fuzzing ------------------------------------------------------------------
SEED = 11728
N = 120_000

# Exact F2P patterns from tests/admin_docs/test_views.py::test_simplify_regex.
F2P = [
    r'^(?P<a>\w+)/b/(?P<c>\w+)/$', r'^(?P<a>\w+)/b/(?P<c>\w+)$',
    r'^(?P<a>\w+)/b/(?P<c>\w+)', r'^(?P<a>\w+)/b/(\w+)$',
    r'^(?P<a>\w+)/b/(\w+)', r'^(?P<a>\w+)/b/((x|y)\w+)$',
    r'^(?P<a>\w+)/b/((x|y)\w+)', r'^(?P<a>(x|y))/b/(?P<c>\w+)$',
    r'^(?P<a>(x|y))/b/(?P<c>\w+)', r'^(?P<a>(x|y))/b/(?P<c>\w+)ab',
    r'^(?P<a>(x|y)(\(|\)))/b/(?P<c>\w+)ab', r'^a/?$', r'^a', r'',
]

_ALPHABET = list('abc01/$') + ['(', ')', '(?P<a>', '(?P<bb>', '\\(', '\\)',
                                '\\w+', '\\d', 'x|y', '[^/.]+', '?P', '<', '>']


def rand_pattern(rng):
    parts = [rng.choice(_ALPHABET) for _ in range(rng.randint(0, 14))]
    return ''.join(parts)


def main() -> int:
    rng = random.Random(SEED)
    cases = list(F2P)
    while len(cases) < N:
        cases.append(rand_pattern(rng))

    mism = 0
    examples = []
    for p in cases:
        for real_fn, shadow_fn, label in (
            (REAL_NAMED, shadow_named, 'named'),
            (REAL_UNNAMED, shadow_unnamed, 'unnamed'),
        ):
            try:
                want = real_fn(p)
            except Exception as e:           # real fn raised: shadow must too
                try:
                    shadow_fn(p)
                    ok = False
                except Exception:
                    ok = True
                if not ok:
                    mism += 1
                    if len(examples) < 10:
                        examples.append({"pattern": p, "fn": label, "real": repr(e)})
                continue
            got = shadow_fn(p)
            if want != got:
                mism += 1
                if len(examples) < 10:
                    examples.append({"pattern": p, "fn": label,
                                     "real": want, "shadow": got})

    import json
    status = "pass" if mism == 0 else "fail"
    print(json.dumps({
        "status": status, "instance": "django__django-11728",
        "seed": SEED, "cases": len(cases), "comparisons": len(cases) * 2,
        "mismatches": mism, "examples": examples,
    }))
    return 0 if mism == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
