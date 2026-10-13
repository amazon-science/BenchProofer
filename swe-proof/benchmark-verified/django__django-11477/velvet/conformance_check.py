#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11477 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md
              bijection (`List (String × Option String)` ↔ ordered
              `groupdict().items()`, `None` ↔ `none`, `some v` ↔ a present
              value; `List String` ↔ `groups()`). There are NO A-tagged
              callees: `keepPresent`/`keepOne` and the `args` fallback are pure
              R/I ops, so the shadow is a complete independent transliteration.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.urls.resolvers.RegexPattern.match` applied at base_commit
              (the real correctness oracle, G-RESOLVE). The harness applies
              patch.diff before this runs (apply_gold=True).

They must agree on every input (matching or non-matching). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import re
import sys

SEED = 11477
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean keepOne/keepPresent + args fallback --------
# bindCaptures models the post-search binding block. Inputs come from the SAME
# regex result the oracle sees, bridged per mapping.md §2:
#   namedGroups : List (String × Option String)  <-  list(m.groupdict().items())
#   positionalGroups : List String                <-  list(m.groups())

def keep_one(pair):
    """keepOne (p : Named) : List Named — present groups contribute, absent drop."""
    name, value = pair
    return [pair] if value is not None else []        # some _ -> [p] ; none -> []


def keep_present(named):
    """keepPresent : front-recursive concat of per-group contributions."""
    out = []
    for pair in named:                                 # order-preserving fold
        out.extend(keep_one(pair))
    return out


def shadow_match(m):
    """The (args, kwargs) bindCaptures computes from a regex Match object `m`,
    transliterated from Solution.lean's impl region. Returns None for no match
    (the `if match:` guard, unchanged by the patch and out of the modeled
    block, mirrored here so the comparison is well-defined)."""
    if m is None:
        return None
    named = list(m.groupdict().items())                # mapping.md §2
    positional = list(m.groups())
    out_named = keep_present(named)                    # A3: present-only filter
    # A4: positional surfaced only when there are no keyword bindings
    out_positional = [] if out_named else positional
    kwargs = dict(out_named)
    args = tuple(out_positional)
    return args, kwargs


# --- the oracle: the REAL patched RegexPattern.match --------------------------

def _make_oracle():
    """Return a callable (regex_str, path) -> (args, kwargs) | None that drives
    the real patched django.urls.resolvers.RegexPattern.match."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(APPEND_SLASH=True, USE_I18N=False, DEBUG=False)
    from django.urls.resolvers import RegexPattern

    def oracle(regex_str, path):
        pat = RegexPattern(regex_str, name="probe", is_endpoint=True)
        res = pat.match(path)                          # patched: filters None
        if res is None:
            return None
        _new_path, args, kwargs = res
        return tuple(args), dict(kwargs)

    return oracle


# --- fuzz: regexes with optional named groups + paths -------------------------

def _f2p_cases():
    """The exact regex/path shapes the FAIL_TO_PASS tests exercise."""
    return [
        (r'^regex_optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?', 'regex_optional/1/2/'),
        (r'^regex_optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?', 'regex_optional/1/'),
        (r'^optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?$', 'optional/1/'),
        (r'^optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?$', 'optional/1/2/'),
        (r'^with-arguments/(?P<argument>[\w-]+)/(?:(?P<optional>[\w-]+).html)?$',
         'with-arguments/regular-argument/'),
        (r'^with-arguments/(?P<argument>[\w-]+)/(?:(?P<optional>[\w-]+).html)?$',
         'with-arguments/regular-argument/optional.html'),
        (r'^regex/(?P<pk>[0-9]+)/$', 'regex/1/'),                 # all-present
        (r'^plain/$', 'plain/'),                                  # no groups
        (r'^pos/([0-9]+)/([a-z]*)$', 'pos/1/abc'),                # positional only
        (r'^none/(?P<a>x)?(?P<b>y)?$', 'none/'),                  # all-absent named
    ]


def _rand_regex_and_path(rng):
    """Build a random regex with 1-4 named groups (some optional) and a path
    that may or may not exercise the optional groups."""
    n = rng.randint(1, 4)
    parts = ['^seg/']
    used = []
    for i in range(n):
        name = "g%d" % i
        body = rng.choice([r'\d+', r'[a-z]+', r'[\w-]+', r'[0-9]+'])
        optional = rng.random() < 0.55
        if optional:
            parts.append('(?:(?P<%s>%s)/)?' % (name, body))
        else:
            parts.append('(?P<%s>%s)/' % (name, body))
        used.append((name, body, optional))
    if rng.random() < 0.5:
        parts.append('$')
    regex = "".join(parts)
    # build a path: include each group's value with prob; optionals may be absent
    path = ['seg/']
    for name, body, optional in used:
        token = {
            r'\d+': str(rng.randint(0, 9999)),
            r'[0-9]+': str(rng.randint(0, 9999)),
            r'[a-z]+': "".join(rng.choice('abcdef') for _ in range(rng.randint(1, 5))),
            r'[\w-]+': "".join(rng.choice('abc-1') for _ in range(rng.randint(1, 5))),
        }[body]
        emit = (not optional) or (rng.random() < 0.6)
        if emit:
            path.append(token + '/')
        elif not optional:
            path.append(token + '/')
    # occasionally truncate the path so the optional tail is genuinely absent
    p = "".join(path)
    if rng.random() < 0.3 and len(p) > 5:
        p = p[:rng.randint(4, len(p))]
    return regex, p


def fuzz_inputs(n, rng):
    for case in _f2p_cases():
        yield case
    for _ in range(n):
        try:
            yield _rand_regex_and_path(rng)
        except re.error:
            continue


def main():
    rng = random.Random(SEED)
    oracle = _make_oracle()
    disagreements = []
    count = 0
    for regex_str, path in fuzz_inputs(N_FUZZ, rng):
        try:
            compiled = re.compile(regex_str)
        except re.error:
            continue
        m = compiled.search(path)
        count += 1
        shadow = shadow_match(m)
        try:
            orc = oracle(regex_str, path)
        except Exception as e:                         # pragma: no cover
            disagreements.append((regex_str, path, shadow, "EXC:%r" % e))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != orc:
            disagreements.append((regex_str, path, shadow, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for regex_str, path, sh, orc in disagreements:
            print("  regex=%r path=%r shadow=%r oracle=%r" % (regex_str, path, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of bindCaptures agrees with patch.diff "
          "behaviour (real RegexPattern.match) on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
