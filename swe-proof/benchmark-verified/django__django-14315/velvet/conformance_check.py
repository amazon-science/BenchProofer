#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14315 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of the two env-normalization
decisions modeled in Solution.lean (`effectiveProcessEnv` and `normalizedEnv`).
There are NO axioms in this bundle: every op is closed Option/emptiness logic over
free inputs (the override dict, and the already-merged ambient+overrides dict), so
the whole impl region is R/I-tagged (conf_skip=false).

  * SHADOW — Solution.lean's two modeled decisions transliterated to Python over
             the real repo types, via the mapping.md §2 bijection:
                 overrides  <->  env (a dict, possibly empty, or None)
                 combined   <->  {**os.environ, **env}  (free input; the
                                 UNCHANGED merge, supplied verbatim on both sides)
                 assembled  <->  the env dict settings_to_cmd_args_env built up
             There are NO A-tagged ops (no consumed axioms), so the shadow is
             pure R/I.

  * ORACLE — `patch.diff`'s behaviour, the two patched hunks transliterated
             VERBATIM:
                 # base/client.py runshell:
                 env = {**os.environ, **env} if env else None
                 # postgresql/client.py settings_to_cmd_args_env:
                 return args, (env or None)
             The `{**os.environ, **env}` merge is UNCHANGED by the patch (it
             already existed inside the pre-patch `if env:` arm), so it is
             supplied as the SAME concrete merged dict on both sides — never
             recomputed differently — isolating the modeled change (the
             truthiness-guarded selection of merged-vs-None / dict-vs-None).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib only. Fuzz seed pinned
(mapping.md §4).
"""
import random
import string
import sys

SEED = 14315
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean transliterated ----------------------------------

def shadow_effective_process_env(overrides, combined):
    """effectiveProcessEnv: launch with the combined set when there is at least
    one override (present AND non-empty); otherwise absent (None)."""
    has_overrides = overrides is not None and len(overrides) > 0  # hasOverrides
    return combined if has_overrides else None


def shadow_normalized_env(assembled):
    """normalizedEnv: report the assembled set when it carries an entry;
    otherwise absent (None)."""
    return None if len(assembled) == 0 else assembled


# ---- ORACLE: patched hunks transliterated VERBATIM -------------------------

def oracle_runshell_env(env, combined):
    """base/client.py runshell, post-patch:
        env = {**os.environ, **env} if env else None
    `combined` is the unchanged `{**os.environ, **env}` merge, supplied as-is."""
    # ---- patched hunk ----
    env = combined if env else None
    # ---- end hunk ----
    return env


def oracle_settings_env(assembled):
    """postgresql/client.py settings_to_cmd_args_env, post-patch:
        return args, (env or None)
    `assembled` is the unchanged env dict built up by the if-chain."""
    # ---- patched hunk ----
    return assembled or None
    # ---- end hunk ----


# ---- input generation ------------------------------------------------------

def _rand_dict(rng, n):
    return {
        ''.join(rng.choice(string.ascii_uppercase) for _ in range(rng.randint(1, 6))):
        ''.join(rng.choice(string.printable.strip()) for _ in range(rng.randint(0, 8)))
        for _ in range(n)
    }


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def env_space():
        # Boundary / F2P-shaped cases first (plan §4.1 step 4).
        # F2P test_runshell_use_environ: env in {None, {}} must reach subprocess
        # as env=None. F2P test_basic etc.: a non-empty env must be passed.
        yield None                       # absent overrides -> None
        yield {}                         # empty overrides -> None (the bug)
        yield {'PGPASSWORD': 'somepassword'}        # test_basic / test_accent
        yield {'PGSERVICE': 'django_test'}          # test_service
        yield {'PGSSLCERT': 'client.crt', 'PGSSLKEY': 'client.key',
               'PGSSLMODE': 'verify-ca', 'PGSSLROOTCERT': 'root.crt'}  # test_ssl
        yield {'PGPASSFILE': '~/.custompgpass'}     # test_passfile
        # Fuzz: dicts of varying size incl. empty.
        for _ in range(N_FUZZ):
            n = rng.choice([0, 0, 1, 1, 2, 3, 5])   # bias toward the boundary
            yield _rand_dict(rng, n)

    for env in env_space():
        count += 1

        # --- site A: runshell env preparation ---
        # `combined` models {**os.environ, **env}: the unchanged merge. Supply a
        # concrete merged dict (a fixed ambient base overlaid with env). It is the
        # SAME object handed to both shadow and oracle, so the merge itself is not
        # under test — only the truthiness-guarded selection is.
        ambient = {'PATH': '/usr/bin', 'HOME': '/root', 'LANG': 'C'}
        combined = {**ambient, **(env or {})}
        overrides = env  # Option Overrides: None or a dict (mapping.md §2)
        sh_a = shadow_effective_process_env(overrides, combined)
        or_a = oracle_runshell_env(env, combined)
        if sh_a != or_a:
            disagreements.append(('runshell', env, sh_a, or_a))

        # --- site B: settings_to_cmd_args_env return ---
        sh_b = shadow_normalized_env(env if env is not None else {})
        or_b = oracle_settings_env(env if env is not None else {})
        if sh_b != or_b:
            disagreements.append(('settings_env', env, sh_b, or_b))

        if len(disagreements) >= 8:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for site, env, sh, orc in disagreements:
            print("  site=%s env=%r shadow=%r oracle=%r" % (site, env, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of effectiveProcessEnv + normalizedEnv agrees "
          "with patch.diff behaviour on %d inputs (seed=%d), 0 disagreements "
          "(empty/absent override set normalizes to None; a non-empty set is "
          "passed/reported as-is)." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
