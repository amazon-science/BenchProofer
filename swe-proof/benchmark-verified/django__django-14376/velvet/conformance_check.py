#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14376 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (the nested
              `Option.getD`: `preferredOpt.getD (secondaryOpt.getD baseValue)`)
              transliterated to Python over the *real* repo types
              (`dict`/`str`), via the mapping.md bijection
              (`dict.get` maybe-absent key ↔ `Option`, present ↔ some,
              absent ↔ none, `.get(k,d)` ↔ `Option.getD`).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `DatabaseClient.settings_to_cmd_args_env` applied at base_commit
              (the real correctness oracle, G-RESOLVE). The resolved database
              name is the trailing positional CLI argument it emits.

The impl region has NO A-tagged content (no axiomatized callees), so the shadow
is pure R/I. They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Coverage note (plan §4.1 honesty): the modeled value-resolution is
*presence-based* (`dict.get` returns a present empty string), but the real code
gates appending the resolved name behind a downstream truthiness test
(`if database:`) that is OUTSIDE the modeled resolution (mapping.md §2). To
isolate the resolution legs A4-A5 the fuzzer keeps every candidate value
non-empty so that gate always passes and the trailing arg equals the resolved
name. The all-empty-resolution region (where the downstream gate fires) is
therefore deliberately not differentially tested here; it is observationally
identical pre/post-patch and the F2P tests never reach it.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import string
import sys

SEED = 14376
N_FUZZ = 100_000


def shadow_resolve(preferred_opt, secondary_opt, base_value):
    """selectOverride transliterated: preferredOpt.getD (secondaryOpt.getD
    baseValue). `*_opt` is None for an absent key (Option.none) or a str for a
    present key (Option.some)."""
    via_secondary = secondary_opt if secondary_opt is not None else base_value
    return preferred_opt if preferred_opt is not None else via_secondary


def oracle_resolve(preferred_opt, secondary_opt, base_value):
    """patch.diff's behaviour: build a full settings_dict, call the patched
    settings_to_cmd_args_env, and read back the resolved database name (the
    trailing positional arg). All candidate values are non-empty so the
    downstream `if database:` gate always appends it (see module docstring)."""
    from django.db.backends.mysql.client import DatabaseClient
    options = {}
    if preferred_opt is not None:
        options['database'] = preferred_opt
    if secondary_opt is not None:
        options['db'] = secondary_opt
    settings_dict = {
        'NAME': base_value,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': options,
    }
    args, _env = DatabaseClient.settings_to_cmd_args_env(settings_dict, [])
    # With USER/PASSWORD/HOST/PORT empty and no ssl/charset, the only positional
    # is the resolved database name appended last (before the empty parameters).
    return args[-1]


def rand_value(rng):
    n = rng.randint(1, 12)
    alphabet = string.ascii_letters + string.digits + "_-."
    return "".join(rng.choice(alphabet) for _ in range(n))


def fuzz_inputs(n, rng):
    # boundary cases first: every present/absent combination of the two keys
    # (preferred present? secondary present?) with distinct values, so a wrong
    # precedence is caught.
    yield (None, None, "settingdbname")
    yield ("optiondbname", None, "settingdbname")
    yield (None, "deprecateddbname", "settingdbname")
    yield ("optiondbname", "deprecateddbname", "settingdbname")
    yield ("preferred", "secondary", "base")
    # F2P-derived: the preferred key wins over the deprecated key over NAME
    yield ("optiondbname", "deprecatedoptiondbname", "settingdbname")
    for _ in range(n):
        has_pref = rng.random() < 0.6
        has_sec = rng.random() < 0.6
        preferred = rand_value(rng) if has_pref else None
        secondary = rand_value(rng) if has_sec else None
        base = rand_value(rng)
        yield (preferred, secondary, base)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for preferred, secondary, base in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_resolve(preferred, secondary, base)
        oracle = oracle_resolve(preferred, secondary, base)
        if shadow != oracle:
            disagreements.append((preferred, secondary, base, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for p, s, b, sh, orc in disagreements:
            print("  preferred=%r secondary=%r base=%r shadow=%r oracle=%r"
                  % (p, s, b, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectOverride agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
