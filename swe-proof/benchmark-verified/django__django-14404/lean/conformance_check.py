#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_catchAll
against an independent reconstruction of the post-patch catch_all_view redirect
behaviour (patch.diff).

The impl region is NOT all-A-tagged (ops 1,2,4,5,6,7 are R/I — refinement.md).
The single A-reference op (#3, the unchanged `resolve` callee) is held FIXED:
the same resolve decision (success+should_append / success+no_append / failure)
feeds both the shadow and the reference, so the differential isolates the
discriminating redirect-target leg (op #6): the redirect target is
`request.path` (script name INCLUDED), not `request.path_info`.

stdlib-only. exit 0 iff zero disagreements over >= 10^5 fuzzed inputs.
"""
import random
import sys

SEED = 14404          # pinned in mapping.md
N = 120_000           # >= 10^5

# Sentinel marking "raise Http404".
HTTP404 = ("HTTP404",)


def shadow(append_slash, url, resolve_outcome, path, path_info):
    """R/I shadow of implementation_catchAll.

    resolve_outcome: None  -> Resolver404 (no match)
                     True  -> match with should_append_slash truthy
                     False -> match with should_append_slash falsey
    Op #6 (the fix): redirect target is `path` (= request.path, visible).
    """
    if append_slash and not url.endswith('/'):
        # resolve('%s/' % path_info, urlconf) — arg built from path_info; the
        # A-reference decision is supplied by resolve_outcome (held fixed).
        if resolve_outcome is not None:           # not Resolver404
            if resolve_outcome:                   # should_append_slash truthy
                return ('REDIRECT', '%s/' % path)
        # falls through: no match, or should_append_slash falsey
    return HTTP404


def reference(append_slash, url, resolve_outcome, path, path_info):
    """Independent reconstruction of the POST-PATCH catch_all_view behaviour.

    Mirrors patch.diff: match = resolve('%s/' % request.path_info, urlconf);
    on success with should_append_slash -> redirect to '%s/' % request.path.
    """
    if not (append_slash and not url.endswith('/')):
        return HTTP404
    if resolve_outcome is None:
        return HTTP404
    if not resolve_outcome:
        return HTTP404
    return ('REDIRECT', '%s/' % path)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # path / path_info samples: empty prefix, with prefix, equal, differing.
    PREFIXES = ['', '/prefix', '/a/b', '/x']
    BASES = ['/admin/foo', '/admin/foo/', '/', '', '/admin/articles']
    URLS = ['/admin/foo', '/admin/foo/', '/', '', '/x', '/admin/articles']

    def gen():
        append_slash = rng.choice([True, False])
        url = rng.choice(URLS)
        outcome = rng.choice([None, True, False])
        base = rng.choice(BASES)
        prefix = rng.choice(PREFIXES)
        path = prefix + base          # request.path (visible, incl. prefix)
        path_info = base              # request.path_info (no prefix)
        return append_slash, url, outcome, path, path_info

    # Deterministic boundary cases that exercise script-name presence/absence.
    fixed = [
        (True, '/admin/foo', True, '/prefix/admin/foo', '/admin/foo'),
        (True, '/admin/foo', True, '/admin/foo', '/admin/foo'),   # no prefix
        (True, '/admin/foo', False, '/prefix/admin/foo', '/admin/foo'),
        (True, '/admin/foo', None, '/prefix/admin/foo', '/admin/foo'),
        (False, '/admin/foo', True, '/prefix/admin/foo', '/admin/foo'),
        (True, '/admin/foo/', True, '/prefix/admin/foo/', '/admin/foo/'),
        (True, '', True, '/prefix', ''),
    ]
    cases = fixed + [gen() for _ in range(N)]

    for c in cases:
        got = shadow(*c)
        want = reference(*c)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((c, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for c, g, w in examples:
            print(f"  in={c!r} shadow={g!r} reference={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
