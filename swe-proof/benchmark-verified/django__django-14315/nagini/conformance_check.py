#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14315 (nagini).

SHADOW: the impl regions of model.py `normalized_environment` and
`effective_environment`, copied verbatim below with the contract calls
(Requires/Ensures) stripped. The impl regions operate on plain Python dicts
and Optional, so they are directly executable as-is. The one @ContractOnly
callee, `env_merge`, stands for the standard mapping-unpacking merge the
repo code invokes unchanged; per the contract it calls the REAL operation
(the dictionary display with double-star unpacking of both inputs).

ORACLE: the REAL patched repo functions the model models per mapping.md.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched modules importable.

  Site 2 (`normalized_environment`): the environment element of the tuple
  returned by `DatabaseClient.settings_to_cmd_args_env`
  (django/db/backends/postgresql/client.py). Driven with settings dicts that
  populate a chosen subset of the environment-producing settings, so the
  mapping the method builds internally is known exactly; the observation is
  the returned environment value (None vs a mapping and its contents).

  Site 1 (`effective_environment`): the environment value that
  `BaseDatabaseClient.runshell` (django/db/backends/base/client.py) hands to
  the subprocess launcher. Driven with a stub client subclass whose
  settings_to_cmd_args_env returns a preset (args, env) pair, with
  os.environ set to a fully controlled base mapping for the duration of the
  call, and with the subprocess launcher replaced by a recorder that captures
  the env keyword it receives (nothing is actually executed).

Type bridge (mapping.md section 2): repo environment mappings are str->str;
the model carries them as Dict[int, int] of opaque name/value tokens, since
only membership, per-key value, and emptiness/None-ness are observed. The
bridge is a bijection: key token k <-> a variable name string, value token
v <-> a value string with the token embedded; real outputs are lowered back
to token dicts and compared against the shadow's result. For site 2 the
seven fixed environment-producing settings are the key space.

Input domain: the Requires are access permissions plus the termination
obligation, so every (env, base) pair over token dicts (env optionally None
for site 1) is Requires-satisfying. Boundary cases cover None, the empty
mapping (the discriminating case: it must yield None, never an empty
mapping), singletons, full-overlap and disjoint key sets; fuzz covers random
subsets/values.

>= 1e5 Requires-satisfying inputs: 128 + 21 boundary cases plus
50000 + 52000 fuzz cases. Pinned fuzz seed: 14315.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import os
import random
import sys

SEED = 14315
N_FUZZ_SITE2 = 50_000   # settings_to_cmd_args_env environment element
N_FUZZ_SITE1 = 52_000   # runshell effective subprocess environment


# --- @ContractOnly callee: the REAL mapping-unpacking merge -------------------

def env_merge(base, overlay):
    return {**base, **overlay}


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def normalized_environment(env):
    if len(env) == 0:
        return None
    return env


def effective_environment(env, base):
    if env is None:
        return None
    if len(env) == 0:
        return None
    merged = env_merge(base, env)
    return merged


# --- type bridge: int tokens <-> environment strings --------------------------

# Site 2 key space: the seven environment-producing settings, in a fixed
# order; key token i (1-based) <-> the i-th variable name.
PG_VARS = ["PGPASSWORD", "PGSERVICE", "PGSSLMODE", "PGSSLROOTCERT",
           "PGSSLCERT", "PGSSLKEY", "PGPASSFILE"]
PG_TOKEN = {name: i + 1 for i, name in enumerate(PG_VARS)}

VAL_PREFIX = "sbuv"
KEY_PREFIX = "SBUK"


def val_str(v):
    return "%s%d" % (VAL_PREFIX, v)


def val_tok(s):
    if not (isinstance(s, str) and s.startswith(VAL_PREFIX)):
        raise ValueError("unbridgeable value %r" % (s,))
    return int(s[len(VAL_PREFIX):])


def key_str(k):
    return "%s%d" % (KEY_PREFIX, k)


def key_tok(s):
    if not (isinstance(s, str) and s.startswith(KEY_PREFIX)):
        raise ValueError("unbridgeable key %r" % (s,))
    return int(s[len(KEY_PREFIX):])


# --- oracle plumbing -----------------------------------------------------------

def make_site2_oracle():
    """Real patched DatabaseClient.settings_to_cmd_args_env: returns the
    environment element of its result for a settings dict populating exactly
    the given {var_name: value_str} subset."""
    from django.db.backends.postgresql.client import DatabaseClient

    def oracle(var_values):
        options = {}
        settings_dict = {
            "NAME": "dbname", "USER": "someuser", "HOST": "somehost",
            "PORT": "444", "OPTIONS": options,
        }
        if "PGPASSWORD" in var_values:
            settings_dict["PASSWORD"] = var_values["PGPASSWORD"]
        if "PGSERVICE" in var_values:
            options["service"] = var_values["PGSERVICE"]
        if "PGSSLMODE" in var_values:
            options["sslmode"] = var_values["PGSSLMODE"]
        if "PGSSLROOTCERT" in var_values:
            options["sslrootcert"] = var_values["PGSSLROOTCERT"]
        if "PGSSLCERT" in var_values:
            options["sslcert"] = var_values["PGSSLCERT"]
        if "PGSSLKEY" in var_values:
            options["sslkey"] = var_values["PGSSLKEY"]
        if "PGPASSFILE" in var_values:
            options["passfile"] = var_values["PGPASSFILE"]
        args, env = DatabaseClient.settings_to_cmd_args_env(settings_dict, [])
        return env

    return oracle


def make_site1_oracle():
    """Real patched BaseDatabaseClient.runshell: returns the environment value
    it hands to the subprocess launcher, for a given command env (None or a
    str dict) and a fully controlled process environment (a str dict)."""
    import django.db.backends.base.client as client_mod
    from django.db.backends.base.client import BaseDatabaseClient

    class _StubConnection:
        settings_dict = {}

    class _StubClient(BaseDatabaseClient):
        executable_name = "true"

        def __init__(self, env_value):
            super().__init__(_StubConnection())
            self._env_value = env_value

        def settings_to_cmd_args_env(self, settings_dict, parameters):
            return (["true"], self._env_value)

    captured = {}

    def _recording_run(args, env=None, check=False, **kwargs):
        captured["env"] = env

        class _Done:
            returncode = 0
        return _Done()

    real_run = client_mod.subprocess.run

    def oracle(cmd_env, base_env):
        # Pin the process environment to exactly base_env for the call.
        saved = dict(os.environ)
        client_mod.subprocess.run = _recording_run
        try:
            os.environ.clear()
            os.environ.update(base_env)
            captured.clear()
            _StubClient(cmd_env).runshell([])
        finally:
            client_mod.subprocess.run = real_run
            os.environ.clear()
            os.environ.update(saved)
        return captured["env"]

    return oracle


# --- differential drivers -------------------------------------------------------

def check_site2(oracle, env_tok):
    """env_tok: Dict[int,int] with keys in 1..7 (the reachable key space).
    Diff shadow normalized_environment against the real returned env."""
    var_values = {PG_VARS[k - 1]: val_str(v) for k, v in env_tok.items()}
    real = oracle(var_values)
    shadow = normalized_environment(env_tok)

    if (real is None) != (shadow is None):
        return ("DISAGREEMENT (settings_to_cmd_args_env env element)\n"
                "  env=%r\n  shadow=%r\n  real=%r" % (env_tok, shadow, real))
    if real is not None:
        try:
            real_tok = {PG_TOKEN[k]: val_tok(v) for k, v in real.items()}
        except (KeyError, ValueError) as exc:
            return ("DISAGREEMENT (unbridgeable real output)\n"
                    "  env=%r\n  shadow=%r\n  real=%r (%s)"
                    % (env_tok, shadow, real, exc))
        if real_tok != shadow:
            return ("DISAGREEMENT (settings_to_cmd_args_env env element)\n"
                    "  env=%r\n  shadow=%r\n  real=%r (tokens %r)"
                    % (env_tok, shadow, real, real_tok))
        # internal consistency: the shadow reports the very same mapping
        assert shadow is env_tok
    return None


def check_site1(oracle, env_tok, base_tok):
    """env_tok: None or Dict[int,int]; base_tok: Dict[int,int]. Diff shadow
    effective_environment against the env the real runshell hands over."""
    cmd_env = (None if env_tok is None
               else {key_str(k): val_str(v) for k, v in env_tok.items()})
    base_env = {key_str(k): val_str(v) for k, v in base_tok.items()}

    real = oracle(cmd_env, base_env)
    shadow = effective_environment(env_tok, base_tok)

    if (real is None) != (shadow is None):
        return ("DISAGREEMENT (runshell subprocess env)\n"
                "  env=%r base=%r\n  shadow=%r\n  real=%r"
                % (env_tok, base_tok, shadow, real))
    if real is not None:
        try:
            real_tok = {key_tok(k): val_tok(v) for k, v in real.items()}
        except ValueError as exc:
            return ("DISAGREEMENT (unbridgeable real output)\n"
                    "  env=%r base=%r\n  shadow=%r\n  real=%r (%s)"
                    % (env_tok, base_tok, shadow, real, exc))
        if real_tok != shadow:
            return ("DISAGREEMENT (runshell subprocess env)\n"
                    "  env=%r base=%r\n  shadow=%r\n  real=%r (tokens %r)"
                    % (env_tok, base_tok, shadow, real, real_tok))
    return None


def site2_boundary():
    """All 128 subsets of the 7-variable key space (includes the empty
    mapping - the discriminating case - and every singleton)."""
    cases = []
    for mask in range(1 << len(PG_VARS)):
        env = {i + 1: 100 + i for i in range(len(PG_VARS)) if mask & (1 << i)}
        cases.append(env)
    return cases


def site1_boundary():
    """None / empty / singleton / overlapping / disjoint command mappings
    against empty and non-empty base mappings."""
    bases = [{}, {1: 1}, {1: 1, 2: 2, 3: 3}]
    envs = [None, {},                       # the discriminating cases
            {1: 10},                        # full overlap with base key 1
            {1: 999, 2: 888},               # overrides both
            {7: 70}, {7: 70, 8: 80},        # disjoint
            {1: 1}]                         # same key, same value
    return [(e if e is None else dict(e), dict(b)) for b in bases for e in envs]


def _rand_map(rng, key_space, max_keys):
    n = rng.randint(0, max_keys)
    return {rng.choice(key_space): rng.randrange(1000) for _ in range(n)}


def main():
    import django.conf
    if not django.conf.settings.configured:
        django.conf.settings.configure()

    site2 = make_site2_oracle()
    site1 = make_site1_oracle()
    rng = random.Random(SEED)
    checked = 0

    # --- boundary -----------------------------------------------------------
    b2 = site2_boundary()
    for env in b2:
        err = check_site2(site2, env)
        if err:
            print(err)
            return 1
        checked += 1

    b1 = site1_boundary()
    for env, base in b1:
        err = check_site1(site1, env, base)
        if err:
            print(err)
            return 1
        checked += 1

    # --- fuzz ----------------------------------------------------------------
    pg_keys = list(range(1, len(PG_VARS) + 1))
    for _ in range(N_FUZZ_SITE2):
        env = _rand_map(rng, pg_keys, 7)
        err = check_site2(site2, env)
        if err:
            print(err)
            return 1
        checked += 1

    wide_keys = list(range(1, 13))
    for _ in range(N_FUZZ_SITE1):
        env = None if rng.random() < 0.2 else _rand_map(rng, wide_keys, 6)
        base = _rand_map(rng, wide_keys, 6)
        err = check_site1(site1, env, base)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched functions on %d inputs "
          "(%d + %d boundary, %d + %d fuzz, seed %d)."
          % (checked, len(b2), len(b1), N_FUZZ_SITE2, N_FUZZ_SITE1, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
