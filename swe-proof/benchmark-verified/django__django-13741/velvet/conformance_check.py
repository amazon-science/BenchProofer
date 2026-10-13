#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13741 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python via the mapping.md bijection. This is `lockedDefault`
              (`out := userFlag.getD true`): the resulting non-editability flag
              is the caller's value if specified, else True. The A-tagged
              callees `noEditChange`/`noEditValue` appear only in the
              postconditions, never in the computed `out`, so the shadow is pure
              R/I (conf_skip=false).
  * ORACLE  — `patch.diff`'s behaviour: the `self.disabled` attribute of a real
              `ReadOnlyPasswordHashField` constructed at base_commit WITH the
              gold patch applied (the harness applies patch.diff before this
              runs). `none` ↔ no `disabled` kwarg; `some b` ↔ `disabled=b`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. Runs in-container (the patched
SWE-Bench instance image), `django` + stdlib only. Seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 13741
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=False,
            SECRET_KEY="conformance-check",
        )
    django.setup()


# --- the R/I shadow: Solution.lean lockedDefault, transliterated -------------
# lockedDefault (userFlag : Option Bool) : Bool := userFlag.getD true
def shadow_locked(user_flag):
    """`Option.getD true` under the mapping.md bijection (None ↔ none)."""
    return True if user_flag is None else user_flag


def oracle_locked(user_flag):
    """patch.diff's behaviour: the `self.disabled` attribute of a real
    ReadOnlyPasswordHashField built with the corresponding `disabled` kwarg."""
    from django.contrib.auth.forms import ReadOnlyPasswordHashField
    if user_flag is None:
        field = ReadOnlyPasswordHashField()
    else:
        field = ReadOnlyPasswordHashField(disabled=user_flag)
    return field.disabled


def fuzz_inputs(n, rng):
    # The three observable construction cases (mapping.md §2) first.
    base_cases = [None, True, False]
    for c in base_cases:
        yield (c, {})
    # Cross the flag cases with randomized orthogonal kwargs that must NOT
    # affect the disabled outcome.
    labels = [None, "Password", "Digest", ""]
    initials = [None, "", "aaa", "pbkdf2_sha256$1$s$h"]
    for _ in range(n):
        flag = rng.choice(base_cases)
        extra = {}
        if rng.random() < 0.5:
            extra["required"] = rng.choice([True, False])
        if rng.random() < 0.5:
            extra["label"] = rng.choice(labels)
        if rng.random() < 0.5:
            extra["initial"] = rng.choice(initials)
        yield (flag, extra)


def oracle_with_extra(user_flag, extra):
    from django.contrib.auth.forms import ReadOnlyPasswordHashField
    kwargs = dict(extra)
    if user_flag is not None:
        kwargs["disabled"] = user_flag
    return ReadOnlyPasswordHashField(**kwargs).disabled


def main():
    _setup_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for flag, extra in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_locked(flag)
        oracle = oracle_with_extra(flag, extra)
        if shadow != oracle:
            disagreements.append((flag, extra, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for flag, extra, sh, orc in disagreements:
            print("  flag=%r extra=%r shadow=%r oracle=%r"
                  % (flag, extra, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of readonlyDigestFieldLocked agrees with "
          "patch.diff behaviour (ReadOnlyPasswordHashField.disabled) on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
