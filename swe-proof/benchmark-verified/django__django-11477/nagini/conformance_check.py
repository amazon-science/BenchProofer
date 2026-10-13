#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11477 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
``absent`` / ``kept_keys`` / ``kept_vals`` copy over as plain functions on a
small immutable-tuple PSeq shim; they serve here as an internal cross-check of
the shadow (contract-side folds vs the executable loop). There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
``django.urls.resolvers.RegexPattern.match`` (the gate applies patch.diff to
/testbed before this script runs). For every (pattern, path) pair where the
pattern matches, the oracle result ``(tail, args, kwargs)`` supplies the
reported keyword mapping and positional captures; the path tail is an
unchanged carry-through outside the model (mapping.md section 2) and is not
compared.

Type bridge (mapping.md section 2): the named-group capture mapping
``Dict[str, Optional[str]]`` is lowered to two parallel ``List[int]`` --
``keys`` (group-name tokens, distinct) and ``vals`` (parallel captured-value
tokens) -- with ``None`` (a named group that did not participate) lowered to
the absence sentinel ``-1`` and every other captured value assigned a distinct
non-negative token (equal strings share a token: only identity is observed).
The positional-capture tuple is lowered element-wise with the same value
tokenizer. The oracle's kwargs/args are lifted into the same token space with
the same per-case tables and compared against the shadow's triple, order and
all.

Input domain: the precondition demands readable lists with
``len(keys) == len(vals)``; every match object lowers to such an input by
construction (one value per named group). Generation stresses the decision
boundary: optional named groups that do and do not participate (in every
subset, via per-group literal markers), empty-string captures (distinct from
absence), duplicate captured values, purely-positional patterns (including
non-participating positional groups), and group-free patterns.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz
(pattern, path) pairs. Pinned fuzz seed: 114770.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (no f-strings: container Python may predate
3.6 formatting habits).
"""
import json
import random
import re
import sys

SEED = 114770
N_FUZZ = 100000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

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

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def absent():
    return -1


def kept_keys(keys, vals):
    if len(keys) == 0:
        return keys.take(0)
    if vals[0] == absent():
        return kept_keys(keys.drop(1), vals.drop(1))
    return PSeq(keys[0]) + kept_keys(keys.drop(1), vals.drop(1))


def kept_vals(keys, vals):
    if len(keys) == 0:
        return vals.take(0)
    if vals[0] == absent():
        return kept_vals(keys.drop(1), vals.drop(1))
    return PSeq(vals[0]) + kept_vals(keys.drop(1), vals.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def select_captures(keys, vals, positional):
    r_keys = []  # type: list
    r_vals = []  # type: list
    i = len(keys)
    while i > 0:
        k = keys[i - 1]
        v = vals[i - 1]
        if v != absent():
            r_keys = [k] + r_keys
            old_vals = r_vals
            r_vals = [v] + r_vals
        i = i - 1
    args = []  # type: list
    if len(r_keys) == 0:
        j = 0
        while j < len(positional):
            args = args + [positional[j]]
            j = j + 1
    return r_keys, r_vals, args
    # (the stripped Assert lines carried only proof-side sequence facts)


# --- oracle plumbing -----------------------------------------------------------

_RP_CACHE = {}


def real_match(pattern, path):
    """Drive the REAL patched RegexPattern.match on (pattern, path)."""
    from django.urls.resolvers import RegexPattern
    rp = _RP_CACHE.get(pattern)
    if rp is None:
        rp = RegexPattern(pattern)
        _RP_CACHE[pattern] = rp
    return rp.match(path)


# --- differential driver -------------------------------------------------------

def check(pattern, path):
    """Lower one (pattern, path) match into the model's token carrier, run the
    shadow and the real patched function, and compare in token space. Returns
    (matched?, error-string-or-None)."""
    m = re.search(pattern, path)
    res = real_match(pattern, path)
    if m is None:
        if res is not None:
            return True, ("DISAGREEMENT on pattern=%r path=%r: real matcher "
                          "recognized the path but the reference engine did "
                          "not" % (pattern, path))
        return False, None
    if res is None:
        return True, ("DISAGREEMENT on pattern=%r path=%r: reference engine "
                      "matched but the real matcher did not" % (pattern, path))

    # token tables (per case): group names and captured values
    gd = m.groupdict()          # one entry per named group, definition order
    names = list(gd)
    vtab = {}

    def vtok(v):
        if v is None:
            return absent()     # absence sentinel per mapping.md
        if v not in vtab:
            vtab[v] = len(vtab)
        return vtab[v]

    ktab = {}

    def ktok(nm):
        if nm not in ktab:
            ktab[nm] = 1000 + len(ktab)
        return ktab[nm]

    keys = [ktok(n) for n in names]
    vals = [vtok(gd[n]) for n in names]
    positional = [vtok(v) for v in m.groups()]
    # Requires-satisfying by construction: one value per named group.
    assert len(keys) == len(vals)

    s_keys, s_vals, s_args = select_captures(keys, vals, positional)

    _tail, r_args, r_kwargs = res
    # lift the oracle's kwargs/args into the same token space (dict iteration
    # order is the reported order; every key/value already has a token)
    o_keys = [ktok(n) for n in r_kwargs]
    o_vals = [vtok(r_kwargs[n]) for n in r_kwargs]
    o_args = [vtok(v) for v in r_args]

    if (s_keys, s_vals, s_args) != (o_keys, o_vals, o_args):
        return True, ("DISAGREEMENT on pattern=%r path=%r\n"
                      "  lowered input: keys=%r vals=%r positional=%r\n"
                      "  shadow (impl region) = (%r, %r, %r)\n"
                      "  real patched matcher = (%r, %r, %r) "
                      "(raw args=%r kwargs=%r)"
                      % (pattern, path, keys, vals, positional,
                         s_keys, s_vals, s_args,
                         o_keys, o_vals, o_args, r_args, r_kwargs))

    # internal cross-check: the executable impl agrees with the pure folds
    if (ToSeq(s_keys) != kept_keys(ToSeq(keys), ToSeq(vals))
            or ToSeq(s_vals) != kept_vals(ToSeq(keys), ToSeq(vals))):
        return True, ("INTERNAL: impl region and pure folds disagree on "
                      "pattern=%r path=%r (keys=%r vals=%r)"
                      % (pattern, path, keys, vals))
    return True, None


def boundary_cases():
    return [
        # optional trailing named group: participating and not
        (r'^regex_optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?',
         'regex_optional/1/2/'),
        (r'^regex_optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?',
         'regex_optional/1/'),
        (r'^with-arguments/(?P<argument>[\w-]+)/(?:(?P<optional>[\w-]+).html)?$',
         'with-arguments/regular-argument/'),
        (r'^with-arguments/(?P<argument>[\w-]+)/(?:(?P<optional>[\w-]+).html)?$',
         'with-arguments/regular-argument/optional.html'),
        (r'^optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?$', 'optional/1/'),
        (r'^optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?$', 'optional/1/2/'),
        # a single required named group
        (r'^regex/(?P<pk>[0-9]+)/$', 'regex/1/'),
        # only positional groups -> positional captures reported
        (r'^(\d+)/(\w+)/$', '12/abc/'),
        # optional named group is the ONLY named group and does not participate
        # -> retained mapping empty -> positional captures reported (the named
        # group's slot in the positional tuple carries the absence value)
        (r'^x/(?:(?P<opt>\d+))?(\w+)$', 'x/abc'),
        # a non-participating POSITIONAL group among the positional captures
        (r'^x/(?:(\d+)-)?(\w+)$', 'x/abc'),
        # both a present and an absent optional named group
        (r'^(?P<a>\d+)/(?:(?P<b>\d+)/)?(?:(?P<c>\d+)/)?', '1/2/'),
        # an EMPTY-STRING capture: distinct from absence, must be retained
        (r'^e/(?P<a>\w*)$', 'e/'),
        (r'^e/(?P<a>\w*)/(?:(?P<b>\d+)/)?$', 'e//'),
        # duplicate captured values across named groups (token collision)
        (r'^(?P<a>\d+)/(?P<b>\d+)/$', '7/7/'),
        # duplicate values across a named and a positional group
        (r'^(?P<a>\d+)/(\d+)/$', '7/7/'),
        # no groups at all: everything empty
        (r'^plain/$', 'plain/'),
        # unanchored tail (the carry-through the model omits)
        (r'^t/(?P<a>\d+)/', 't/3/rest/of/path'),
        # non-matching path (skipped, sanity of the harness)
        (r'^regex/(?P<pk>[0-9]+)/$', 'nomatch/'),
    ]


def fuzz_case(rng):
    """Synthesize one (pattern, path) pair: optional named groups behind
    per-group literal markers (so any participation subset is realizable),
    optional/required positional groups, empty-string-capable groups, a small
    value pool to force token collisions."""
    pattern = '^'
    path = ''
    digits = ['5', '6', '78', '5', '0']
    if rng.random() < 0.6:
        pattern += r'(?P<head>\d+)/'
        path += rng.choice(['1', '23', '4']) + '/'
    n_opt = rng.randint(0, 3)
    for k in range(n_opt):
        marker = chr(ord('a') + k)
        if rng.random() < 0.15:
            # empty-string-capable optional named group
            pattern += r'(?:%s(?P<g%d>\d*)/)?' % (marker, k)
            if rng.random() < 0.6:
                path += marker + rng.choice(digits + ['']) + '/'
        else:
            pattern += r'(?:%s(?P<g%d>\d+)/)?' % (marker, k)
            if rng.random() < 0.6:
                path += marker + rng.choice(digits) + '/'
    n_pos = rng.randint(0, 2)
    for k in range(n_pos):
        if rng.random() < 0.5:
            pattern += r'([A-Z]{2})/'
            path += rng.choice(['AB', 'CD', 'AB']) + '/'
        else:
            pattern += r'(?:=(\d+)/)?'
            if rng.random() < 0.5:
                path += '=' + rng.choice(digits) + '/'
    if rng.random() < 0.5:
        pattern += '$'
    else:
        path += rng.choice(['', 'tail', 'x/y'])
    return pattern, path


def main():
    checked = 0
    boundary = boundary_cases()
    for pat, path in boundary:
        matched, err = check(pat, path)
        if err:
            print(err)
            return 1
        if matched:
            checked += 1

    rng = random.Random(SEED)
    fuzz_checked = 0
    for _ in range(N_FUZZ):
        pat, path = fuzz_case(rng)
        matched, err = check(pat, path)
        if err:
            print(err)
            return 1
        if matched:
            checked += 1
            fuzz_checked += 1

    print("G-CONF OK: shadow impl == real patched matcher on %d matched "
          "inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary) - 1, fuzz_checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
