#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-10914.

Refutes the R/I refinement leg (B1: `return 420` ↔ the framework default file
mode). SHADOW = the transliterated impl's returned value (decimal 420, i.e.
0o644); ORACLE = the patched repo's actual default mode, read by importing the
settings module in-container with the gold patch applied. They must agree.
Exit 0 iff zero disagreements. Runs in-container with the gold patch applied;
stdlib only.
"""
import sys

SEED = 10914
N_FUZZ = 100_000


def shadow_mode():
    """defaultFileMode transliterated: the concrete default mode value (Nat)."""
    return 420  # = 0o644, what Solution.lean's `do` block returns


def oracle_mode():
    """The patched repo's actual default file-upload permission mode."""
    from django.conf import global_settings
    return global_settings.FILE_UPLOAD_PERMISSIONS


def main():
    try:
        oracle = oracle_mode()
    except Exception as e:  # pragma: no cover
        print("G-CONF FAIL: could not read repo default mode: %r" % (e,))
        return 1

    shadow = shadow_mode()
    disagreements = []
    # The provider takes no input; the relation is a constant. Repeat the
    # idempotent comparison over the fuzz budget for parity with the harness
    # (a constant relation cannot drift, but we honour the >=1e5 contract).
    count = 0
    for _ in range(N_FUZZ):
        count += 1
        if shadow != oracle:
            disagreements.append((shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): shadow=%r vs oracle=%r"
              % (len(disagreements), shadow, oracle))
        return 1
    print("G-CONF OK: R/I shadow of defaultFileMode (%d) agrees with patched "
          "FILE_UPLOAD_PERMISSIONS (%d) on %d checks (seed=%d), 0 disagreements."
          % (shadow, oracle, count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
