#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12419.

The only kind-A obligation in this bundle is an A-reference: the deep model
`normalized_policy` (model.py pure region) must equal the REAL header-value
construction the modeled code performs on a configured referrer policy. That
construction is, verbatim, the response-filter chain

    ','.join([v.strip() for v in policy.split(',')])

(when the policy is a `str`; Django's default is a `str`). The deep model
`normalized_policy(s)` is restricted to the property the proof consumes:
**identity on a single token that contains no comma and no ASCII whitespace.**

This script runs the REAL chain on:
  (1) the exact baseline value the bundle pins (`"same-origin"`) — the value
      the F2P test observes on the `Referrer-Policy` header;
  (2) boundary single tokens with no comma / no whitespace;
  (3) randomized fuzz over comma-free, whitespace-free tokens,
and asserts the real chain equals the deep model (identity) on every such
input — i.e. the deep model is sound exactly on its modeled domain. It also
sanity-checks that the chain is NOT a blanket identity outside that domain
(so the restriction is meaningful, not vacuous).

Imports only the Python standard library (`random`, `string`, `sys`) — the
real chain is a plain `str` method composition, no repo-specific import needed.
Exit 0 iff every obligation holds.
"""
import random
import string
import sys


def real_chain(policy):
    """The REAL header-value construction performed on a `str` policy
    (django/middleware/security.py process_response, the referrer-policy
    branch)."""
    return ','.join([v.strip() for v in policy.split(',')])


def normalized_policy_model(s):
    """Reference of model.py's deep model `normalized_policy`: identity on a
    single token with no comma and no ASCII whitespace."""
    return s


_WS = set(' \t\n\r\x0b\x0c')


def in_modeled_domain(s):
    """The domain on which the deep model claims correctness: no comma, no
    ASCII whitespace (a single whitespace-free token)."""
    return ',' not in s and not any(c in _WS for c in s)


def check_reference(s):
    assert in_modeled_domain(s), "test input must be in the modeled domain"
    observed = real_chain(s)               # real callee chain
    expected = normalized_policy_model(s)  # deep model
    assert observed == expected, (
        "normalized_policy deep model unsound on %r: real chain gave %r, "
        "deep model gives %r" % (s, observed, expected))


def main():
    # (1) the exact baseline value the bundle pins.
    baseline = 'same-origin'
    assert in_modeled_domain(baseline)
    assert [ord(c) for c in baseline] == [
        115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110], \
        "baseline code points drifted from model.py baseline_policy()"
    check_reference(baseline)

    # (2) boundary single tokens (no comma, no whitespace).
    boundary = [
        '', 'a', 'same-origin', 'no-referrer', 'origin',
        'strict-origin', 'no-referrer-when-downgrade',
        'origin-when-cross-origin', 'unsafe-url', 'A', '-', ';', 'x' * 64,
    ]
    for s in boundary:
        check_reference(s)

    # (3) randomized fuzz over comma-free, whitespace-free tokens.
    rng = random.Random(12419)
    alphabet = string.ascii_letters + string.digits + '-_.~:/?#[]@!$&()*+=%'
    for _ in range(20000):
        n = rng.randint(0, 32)
        s = ''.join(rng.choice(alphabet) for _ in range(n))
        # alphabet excludes comma and whitespace, so s is in the modeled domain
        assert in_modeled_domain(s)
        check_reference(s)

    # Meaningfulness: the restriction to comma-/whitespace-free tokens is NOT
    # vacuous — the real chain is genuinely non-identity off the modeled domain
    # (so the deep model legitimately abstains there).
    assert real_chain(' same-origin ') == 'same-origin'      # trim happens
    assert real_chain('a, b ,c') == 'a,b,c'                  # split+trim+join
    assert real_chain('  ') == ''                            # all-whitespace

    print("G-AX OK: normalized_policy deep model (== real ','-join/strip "
          "chain) sound on baseline 'same-origin' + %d boundary + 20000 fuzz "
          "comma-/whitespace-free tokens; non-vacuous off-domain." %
          len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
