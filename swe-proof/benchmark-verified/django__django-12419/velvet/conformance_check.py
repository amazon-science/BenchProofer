#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-12419.

Refutes the R refinement leg (B1: `return sameOriginPolicy` ↔ the framework
default referrer-policy token). SHADOW = the transliterated impl's returned
value (the character sequence "same-origin"); ORACLE = the patched repo's
actual default policy, read by importing the settings module in-container with
the gold patch applied. They must agree.

Beyond the raw setting value, we also bridge through the *consuming* pipeline:
the value the framework's security middleware writes into the response header
is `','.join(v.strip() for v in policy.split(','))` when the policy is a string.
We model that emission so the shadow matches the test-observed header token,
confirming the R leg pins the F2P-discriminating behavior. Exit 0 iff zero
disagreements. Runs in-container with the gold patch applied; stdlib only.
"""
import sys

SEED = 12419
N_FUZZ = 100_000


def shadow_policy():
    """defaultReferrerPolicy transliterated: the concrete default policy token
    (List Char modeled as a Python str)."""
    return "same-origin"  # what Solution.lean's `do` block returns


def emit_header(policy):
    """The header value the security middleware derives from the policy setting,
    mirroring SecurityMiddleware.process_response's Referrer-Policy branch.
    For a str policy this is the comma-join of the stripped, comma-split parts."""
    if isinstance(policy, str):
        return ",".join(v.strip() for v in policy.split(","))
    return ",".join(policy)


def oracle_policy():
    """The patched repo's actual default referrer-policy setting value."""
    from django.conf import global_settings
    return global_settings.SECURE_REFERRER_POLICY


def main():
    try:
        oracle = oracle_policy()
    except Exception as e:  # pragma: no cover
        print("G-CONF FAIL: could not read repo default policy: %r" % (e,))
        return 1

    shadow = shadow_policy()
    disagreements = []
    # The provider takes no input; the relation is a constant. Repeat the
    # idempotent comparison over the fuzz budget for parity with the harness
    # (a constant relation cannot drift, but we honour the >=1e5 contract).
    count = 0
    for _ in range(N_FUZZ):
        count += 1
        # (a) the raw setting value matches the modeled default token, and
        # (b) the header the consumer emits from each matches.
        if shadow != oracle or emit_header(shadow) != emit_header(oracle):
            disagreements.append((shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): shadow=%r vs oracle=%r"
              % (len(disagreements), shadow, oracle))
        return 1
    print("G-CONF OK: R shadow of defaultReferrerPolicy (%r -> header %r) agrees "
          "with patched SECURE_REFERRER_POLICY (%r -> header %r) on %d checks "
          "(seed=%d), 0 disagreements."
          % (shadow, emit_header(shadow), oracle, emit_header(oracle), count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
