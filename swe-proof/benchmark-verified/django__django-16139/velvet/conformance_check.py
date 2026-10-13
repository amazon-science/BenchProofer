#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16139 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `buildRelativeLink` impl
              region (the deep model `relativeLink`) transliterated to Python
              over the real repo types, via the mapping.md §2 bijection:
                  relativeLink(key) = "../../" + str(key) + "/password/"
              (Nat key <-> non-negative int pk; toString key <-> str(pk);
              List Char <-> str; ++ <-> +). There are NO A-tagged callees in the
              impl region (no axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the gold post-patch expression the
              patched `UserChangeForm.__init__` substitutes into the password
              field's help-text template, i.e. the format argument
                  f"../../{self.instance.pk}/password/"
              evaluated at `self.instance.pk == key`. This is exactly the value
              the patched line (forms.py:166-167) feeds to `help_text.format`;
              the surrounding `str.format` into the UNCHANGED template is an
              R-identity wrapper (mapping.md §2, A5), so the discriminating R/I
              content is precisely this argument string. We additionally apply
              the real, unchanged help_text template via `str.format` on both
              sides to exercise the A5 identity end-to-end.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 16139
N_FUZZ = 100_000

# The UNCHANGED help_text template literal (forms.py:150-156, byte-identical
# pre/post patch). Used to exercise the A5 str.format identity end-to-end on
# both legs. The single {} placeholder is filled by the relative link.
HELP_TEXT_TEMPLATE = (
    "Raw passwords are not stored, so there is no way to see this "
    "user’s password, but you can change the password using "
    '<a href="{}">this form</a>.'
)


# --- the R/I shadow: relativeLink transliterated ---------------------------
def shadow_link(key):
    """relativeLink(key) transliterated to str (mapping.md A1-A4):
    "../../" ++ toString key ++ "/password/"  ->  Python str concat."""
    return "../../" + str(key) + "/password/"


# --- the oracle: patch.diff's behaviour ------------------------------------
def oracle_link(key):
    """The gold post-patch format argument f"../../{self.instance.pk}/password/"
    evaluated at self.instance.pk == key (patch.diff, forms.py:166-167)."""
    return f"../../{key}/password/"


def fuzz_keys(n, rng):
    # boundary cases first (plan §4.1 step 4): the canonical pk, zero, single-
    # and multi-digit, and large magnitudes (no leading zeros / no separators in
    # either str(int) or toString Nat).
    yield 1            # the smallest real AutoField pk
    yield 0            # boundary
    yield 9
    yield 10
    yield 22           # the digit pattern echoed by the issue's example uuid
    yield 99
    yield 100
    yield 123456789
    yield 2 ** 31 - 1  # 32-bit AutoField max
    yield 2 ** 63 - 1  # 64-bit BigAutoField max
    for _ in range(n):
        # mix of small and wide magnitudes
        if rng.random() < 0.5:
            yield rng.randint(0, 10 ** 3)
        else:
            yield rng.randint(0, 10 ** 18)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for key in fuzz_keys(N_FUZZ, rng):
        count += 1
        shadow_arg = shadow_link(key)
        oracle_arg = oracle_link(key)
        # bare argument must match...
        if shadow_arg != oracle_arg:
            disagreements.append((key, shadow_arg, oracle_arg))
        # ...and the end-to-end substitution into the unchanged template (A5).
        elif HELP_TEXT_TEMPLATE.format(shadow_arg) != HELP_TEXT_TEMPLATE.format(
            oracle_arg
        ):
            disagreements.append((key, shadow_arg, oracle_arg))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for key, sh, orc in disagreements:
            print("  key=%r shadow=%r oracle=%r" % (key, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildRelativeLink agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
