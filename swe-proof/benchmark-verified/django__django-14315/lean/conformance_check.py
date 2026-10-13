#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadows of the two modeled functions
against the patch.diff (post-patch) behaviour.

Both modeled functions normalize a "no overrides" environment to *absent*:
  1. runshell env resolution (base client):
       env truthy  -> {**os.environ, **env}        (unchanged overlay)
       env falsy    -> None                          (None OR empty dict)
  2. command-builder env report (postgresql client):
       env empty    -> None
       env non-empty -> env

The impl region is R/I (plus one A-reference: the `{**os.environ, **env}` overlay,
reproduced here with the REAL dict merge). We diff the shadows against an
independent reconstruction of the post-patch source behaviour over >=10^5 fuzzed
inputs. Zero disagreements required. stdlib-only; exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14315          # pinned in mapping.md
N = 120_000           # >= 10^5


# ---- shadows (reproduce the Lean impls op-for-op) -------------------------

def shadow_runshell_env(os_environ, env):
    """R/I shadow of implementation_runshell_env. `env` is None or a dict.
    `envIsSet`: present iff supplied and non-empty (Python truthiness)."""
    if env:                                  # envIsSet env == true
        return {**os_environ, **env}         # A-reference: the real overlay
    else:
        return None                          # changed op: not-present -> absent


def shadow_client_env(env):
    """R/I shadow of implementation_client_env. `env` is always a dict."""
    if not env:                              # env.isEmpty
        return None
    return env


# ---- independent reconstruction of the post-patch source ------------------

def patched_runshell_env(os_environ, env):
    # django/db/backends/base/client.py runshell (patched):
    return {**os_environ, **env} if env else None


def patched_client_env(env):
    # django/db/backends/postgresql/client.py settings_to_cmd_args_env (patched):
    return env or None


# ---- fuzzers --------------------------------------------------------------

def rand_env_dict(rng, allow_empty=True):
    n = rng.randint(0 if allow_empty else 1, 6)
    keys = ['PGPASSWORD', 'PGSERVICE', 'PGSSLMODE', 'PGSSLROOTCERT',
            'PGSSLCERT', 'PGSSLKEY', 'PGPASSFILE', 'CUSTOM', 'PATH', 'HOME']
    d = {}
    for _ in range(n):
        d[rng.choice(keys)] = rng.choice(['', 'x', 'val', 'somepassword',
                                          'django_test', '~/.pgpass', '1'])
    return d


def rand_ambient(rng):
    n = rng.randint(0, 5)
    d = {}
    for _ in range(n):
        d[rng.choice(['PATH', 'HOME', 'LANG', 'PGPASSWORD', 'PGSERVICE',
                      'TERM'])] = rng.choice(['/bin', '/root', 'C', 'ambient'])
    return d


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact F2P shapes.
    fixed_runshell = [
        ({}, None),                        # F2P test_runshell_use_environ: None
        ({}, {}),                          # F2P test_runshell_use_environ: {}
        ({'PATH': '/bin'}, None),
        ({'PATH': '/bin'}, {}),
        ({'PATH': '/bin'}, {'PGPASSWORD': 'p'}),       # truthy: overlay
        ({}, {'PGPASSWORD': 'p'}),
        ({'A': '1'}, {'A': '2'}),                       # override wins on collision
    ]
    fixed_client = [
        {},                                # F2P test_nopass / test_parameters: -> None
        {'PGPASSWORD': 'somepassword'},    # F2P test_basic
        {'PGSERVICE': 'django_test'},
        {'PGSSLCERT': 'c', 'PGSSLKEY': 'k', 'PGSSLMODE': 'm', 'PGSSLROOTCERT': 'r'},
    ]

    runshell_cases = list(fixed_runshell)
    client_cases = list(fixed_client)
    for _ in range(N):
        ambient = rand_ambient(rng)
        # env is None or a (possibly empty) dict
        env = None if rng.random() < 0.34 else rand_env_dict(rng)
        runshell_cases.append((ambient, env))
        client_cases.append(rand_env_dict(rng))

    for ambient, env in runshell_cases:
        got = shadow_runshell_env(ambient, env)
        want = patched_runshell_env(ambient, env)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(("runshell", (ambient, env), got, want))

    for env in client_cases:
        got = shadow_client_env(env)
        want = patched_client_env(env)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(("client", env, got, want))

    total = len(runshell_cases) + len(client_cases)
    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for tag, inp, g, w in examples:
            print(f"  [{tag}] in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {total} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
