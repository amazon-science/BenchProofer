#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11728 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
``step_bal`` / ``close_off`` copy over as plain functions on top of a small
immutable-tuple PSeq shim (``close_off`` also serves as the executable form of
the precondition, gating which scan regions are in-domain). There are no
@ContractOnly callees in this bundle (the axioms region is empty).

ORACLE: the REAL patched repo functions the model models per mapping.md --
``django.contrib.admindocs.utils.replace_named_groups`` and
``django.contrib.admindocs.utils.replace_unnamed_groups`` (the gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed resolves
the patched module).

BRIDGE (mapping.md section 2): the model functions take the already-isolated
scan region as ``List[int]`` code points plus the preceding code point, and
return the span end RELATIVE to the region start; the repo functions take the
whole pattern ``str`` and return the fully substituted pattern. The bridge
therefore reconstructs each caller around the shadow inner scan: it locates
group starts with the same module-level regexes the repo uses, lowers each
scan slice via ``ord``, adds back the caller's base offset to the shadow's
relative result, and performs the same substitution bookkeeping. Regions
whose matching close does not exist (the executable precondition fails) are
skipped by the shadow bridge, mirroring the caller recording nothing for
them. The comparison is end-to-end on the substituted pattern string.

Input domain: every generated pattern is a ``str``; a Requires-satisfying
input is one (region, prev0) pair per located group whose matching close lies
inside the region. >= 1e5 such shadow invocations are accumulated over
boundary patterns + randomized fuzz. Pinned fuzz seed: 11728.

Exit 0 iff zero disagreements; on disagreement prints the pattern and both
outputs and exits 1. stdlib only (re + random).
"""
import json
import random
import sys

SEED = 11728
MIN_INVOCATIONS = 100000

sys.setrecursionlimit(200000)


# --- PSeq shim: immutable sequence with the operations the pure region uses --

class PSeq(object):
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

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, verbatim, contracts stripped -------------------

def step_bal(c, prev, bal):
    if c == 40 and prev != 92:   # unescaped '('
        return bal + 1
    if c == 41 and prev != 92:   # unescaped ')'
        return bal - 1
    return bal


def close_off(s, bal, prev):
    if len(s) == 0:
        return 0
    nb = step_bal(s[0], prev, bal)
    if nb == 0:
        return 0
    return 1 + close_off(s.drop(1), nb, s[0])


# --- impl region of model.py, verbatim, contract calls stripped --------------

def named_group_pattern_end(region, prev0):
    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        val = region[i]
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        # Record as soon as the depth returns to zero -- after processing the
        # closing parenthesis -- so a group ending the region is still caught.
        if bal == 0:
            res = i
    return res


def unnamed_group_pattern_end(region, prev0):
    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        val = region[i]
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        if bal == 0:
            res = i
    return res


# --- bridge: reconstruct each caller around the shadow inner scan ------------
#
# The callers locate group starts with the module-level regexes, hand the
# slice after the group opener to the depth scan, and turn the scan-relative
# span end back into absolute indices before substituting. All of that
# bookkeeping is outside the modeled scan (mapping.md section 2, an
# R-refinement); it is reproduced here so the shadow can be compared to the
# repo functions end-to-end on the pattern string.

def shadow_replace_named_groups(pattern, named_matcher, counter):
    named_group_indices = [
        (m.start(0), m.end(0), m.group(1))
        for m in named_matcher.finditer(pattern)
    ]
    group_pattern_and_name = []
    for start, end, group_name in named_group_indices:
        region = [ord(ch) for ch in pattern[end:]]
        prev0 = ord(pattern[end - 1])       # the char just before the region
        # Executable precondition: the matching close exists in the region.
        if close_off(ToSeq(region), 1, prev0) < len(region):
            counter[0] += 1
            res = named_group_pattern_end(region, prev0)
            group_pattern_and_name.append(
                (pattern[start:end + res], group_name))
        # else: no matching close -> the caller records nothing for this group
    for group_pattern, group_name in group_pattern_and_name:
        pattern = pattern.replace(group_pattern, group_name)
    return pattern


def shadow_replace_unnamed_groups(pattern, unnamed_matcher, counter):
    unnamed_group_indices = [
        m.start(0) for m in unnamed_matcher.finditer(pattern)]
    group_indices = []
    for start in unnamed_group_indices:
        region = [ord(ch) for ch in pattern[start + 1:]]
        prev0 = ord(pattern[start])         # the group opener itself
        if close_off(ToSeq(region), 1, prev0) < len(region):
            counter[0] += 1
            res = unnamed_group_pattern_end(region, prev0)
            group_indices.append((start, (start + 1) + res))
    # Substitution bookkeeping, identical to the caller's tail: drop group
    # spans nested inside an earlier span, then splice in the placeholder.
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


# --- differential driver ------------------------------------------------------

def check(pattern, real_named, real_unnamed, named_matcher, unnamed_matcher,
          counter):
    shadow_n = shadow_replace_named_groups(pattern, named_matcher, counter)
    real_n = real_named(pattern)
    if shadow_n != real_n:
        print("DISAGREEMENT (named-group substitution) on pattern %r:\n"
              "  shadow (impl region + bridge) = %r\n"
              "  real (patched repo function)  = %r"
              % (pattern, shadow_n, real_n))
        return False
    shadow_u = shadow_replace_unnamed_groups(pattern, unnamed_matcher, counter)
    real_u = real_unnamed(pattern)
    if shadow_u != real_u:
        print("DISAGREEMENT (unnamed-group substitution) on pattern %r:\n"
              "  shadow (impl region + bridge) = %r\n"
              "  real (patched repo function)  = %r"
              % (pattern, shadow_u, real_u))
        return False
    return True


def boundary_patterns():
    return [
        # groups ending the pattern with no trailing character
        r'^(?P<a>\w+)/b/(?P<c>\w+)',
        r'^(?P<a>\w+)/b/(\w+)',
        r'^(?P<a>\w+)/b/((x|y)\w+)',
        r'^(?P<a>(x|y))/b/(?P<c>\w+)',
        r'(?P<a>\w+)',
        r'(\w+)',
        # groups followed by a terminator or more text
        r'^(?P<a>\w+)/b/(?P<c>\w+)/$',
        r'^(?P<a>\w+)/b/(?P<c>\w+)$',
        r'^(?P<a>\w+)/b/(\w+)$',
        r'^(?P<a>\w+)/b/((x|y)\w+)$',
        r'^(?P<a>(x|y))/b',
        r'^b/((x|y)\w+)$',
        # escaped parentheses inside and around groups
        r'^(?P<a>\(x\))/b',
        r'^(?P<a>(\(|\)))ab',
        r'^(?P<a>(x|y)(\(|\)))/b/(?P<c>\w+)ab',
        r'\((?P<a>\w+)\)',
        r'\((?P<a>\w+)',
        r'^(?P<a>\w+\\)',
        r'^(?P<a>\w+\\\\)',
        # unterminated groups (out-of-domain regions: nothing recorded)
        r'^(?P<a>\w+',
        r'^(?P<a>(x|y',
        r'(', r'((', r'(?P<a>',
        # empty / no-group patterns
        r'', r'^$', r'abc', r'\(\)',
        # deep nesting and adjacent groups
        r'((((x))))',
        r'(a)(b)(c)',
        r'(?P<a>x)(?P<b>y)(?P<c>z)',
        r'(?P<a>(?P<b>(?P<c>x)))',
        r'(a(b(c)d)e)',
        # duplicated group text (substitution-by-value bookkeeping)
        r'(?P<a>\w+)/(?P<a>\w+)',
        r'(\w+)/(\w+)',
        # non-ASCII pattern text
        u'^(?P<a>\u00e9\\w+)/(\u2022+)',
    ]


def main():
    from django.contrib.admindocs import utils as real_utils
    real_named = real_utils.replace_named_groups
    real_unnamed = real_utils.replace_unnamed_groups
    named_matcher = real_utils.named_group_matcher
    unnamed_matcher = real_utils.unnamed_group_matcher

    counter = [0]     # Requires-satisfying shadow invocations
    patterns = 0

    for pat in boundary_patterns():
        if not check(pat, real_named, real_unnamed, named_matcher,
                     unnamed_matcher, counter):
            return 1
        patterns += 1

    # Randomized fuzz over regex-ish tokens (pinned seed). Token alphabet is
    # weighted toward group openers/closers and escapes so most patterns
    # contain several in-domain scan regions.
    rng = random.Random(SEED)
    tokens = [
        '(?P<a>', '(?P<bb>', '(?P<c0>', '(', ')', ')', '\\(', '\\)', '\\\\',
        '\\w+', 'a', 'Z', '0', '/', '|', '$', '^', '+', '.', '?', '<', '>',
        'P', '\\', '[x]', '{2}', '-', u'\u00e9',
    ]
    fuzz = 0
    while fuzz < 60000 or counter[0] < MIN_INVOCATIONS:
        n = rng.randint(0, 14)
        pat = ''.join(rng.choice(tokens) for _ in range(n))
        if not check(pat, real_named, real_unnamed, named_matcher,
                     unnamed_matcher, counter):
            return 1
        fuzz += 1
        patterns += 1
        if fuzz >= 400000:
            break

    if counter[0] < MIN_INVOCATIONS:
        print("FAIL: only %d Requires-satisfying shadow invocations "
              "(need >= %d)" % (counter[0], MIN_INVOCATIONS))
        return 1

    print("G-CONF OK: shadow impl == real patched group-substitution "
          "functions on %d patterns (%d boundary + %d fuzz, seed %d); "
          "%d Requires-satisfying scan invocations; 0 disagreements."
          % (patterns, len(boundary_patterns()), fuzz, SEED, counter[0]))
    print(json.dumps({"checked": patterns, "invocations": counter[0],
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
