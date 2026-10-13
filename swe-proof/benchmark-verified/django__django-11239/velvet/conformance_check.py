#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11239 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`forwardedEnv`
              / `forwardOne`) transliterated to Python over the *real* repo type
              (`str`), via the mapping.md bijection (`List Char` ↔ `str`, empty
              value ↔ unset option, `if value:` ↔ `value ≠ []`). The forwarded
              entry's KEY is re-mapped from the model's option name to the real
              environment-variable name through the mapping.md §2 bijection, so
              SHADOW emits the same `PG*` mapping the repo writes.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `DatabaseClient.runshell_db` run at base_commit (the real
              correctness oracle, G-RESOLVE), mocking `subprocess.run` exactly as
              the repo's own tests/dbshell/test_postgresql.py::_run_it does, and
              capturing the `PG*` subset of the child-process environment.

There are no A-tagged callees in the impl region (mapping.md §3), so the shadow
is pure R/I. They must agree on every input. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, with patch.diff
applied), stdlib only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import os
import random
import subprocess
import sys
from unittest import mock

SEED = 11239
N_FUZZ = 100_000

# The five connection-config options the model forwards, in source order, paired
# with the environment variable the repo writes them under (mapping.md §2).
# model option name (public)  ->  real environment variable
OPT_TO_ENV = [
    ("password", "PGPASSWORD"),
    ("sslmode", "PGSSLMODE"),
    ("sslrootcert", "PGSSLROOTCERT"),
    ("sslcert", "PGSSLCERT"),
    ("sslkey", "PGSSLKEY"),
]
# the conn_params dict key each option is read from (= the model option name here)
OPT_TO_PARAM = {
    "password": "password",
    "sslmode": "sslmode",
    "sslrootcert": "sslrootcert",
    "sslcert": "sslcert",
    "sslkey": "sslkey",
}


def shadow_env(conn_params):
    """forwardedEnv (Solution.lean) transliterated to str, then re-keyed through
    the option->environment-variable bijection (mapping.md §2). Returns the dict
    of PG* entries the model says are forwarded: each option is forwarded iff its
    value is set (non-empty), under its env-var name."""
    out = {}
    for opt, env_name in OPT_TO_ENV:
        value = conn_params.get(OPT_TO_PARAM[opt], "")
        if value != "":            # `if value:` truthiness == `value ≠ []`
            out[env_name] = str(value)
    return out


def oracle_env(conn_params):
    """patch.diff's behaviour: run the patched DatabaseClient.runshell_db and
    capture the PG* subset of the env handed to the launched process — exactly
    how tests/dbshell/test_postgresql.py::_run_it observes it."""
    from django.db.backends.postgresql.client import DatabaseClient
    captured = {}

    def _mock_subprocess_run(*args, env=os.environ, **kwargs):
        for k in env:
            if k.startswith("PG"):
                captured[k] = env[k]
        return subprocess.CompletedProcess(list(*args), 0)

    with mock.patch("subprocess.run", new=_mock_subprocess_run):
        DatabaseClient.runshell_db(conn_params)
    return captured


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    base = {"database": "dbname", "user": "u", "host": "h", "port": "444"}
    # nothing ssl, no password
    yield dict(base)
    # password only (the pre-existing behaviour)
    yield {**base, "password": "secret"}
    # each ssl option alone
    for opt in ("sslmode", "sslrootcert", "sslcert", "sslkey"):
        yield {**base, opt: "v"}
    # the F2P case: all four ssl options set, no password
    yield {**base, "sslmode": "verify-ca", "sslrootcert": "root.crt",
           "sslcert": "client.crt", "sslkey": "client.key"}
    # all five set
    yield {**base, "password": "p", "sslmode": "verify-ca",
           "sslrootcert": "root.crt", "sslcert": "client.crt", "sslkey": "client.key"}
    # explicit empty strings (must behave as unset — the get default)
    yield {**base, "password": "", "sslmode": "", "sslrootcert": "",
           "sslcert": "", "sslkey": ""}

    opts = ["password", "sslmode", "sslrootcert", "sslcert", "sslkey"]
    # a small pool of values incl. empty (unset), spaces, special chars
    pool = ["", "x", "verify-ca", "root.crt", "client.key", "a b", "p@ss:w/d",
            "0", "false", "é"]
    for _ in range(n):
        cp = dict(base)
        for opt in opts:
            v = rng.choice(pool)
            if v != "" or rng.random() < 0.3:
                cp[opt] = v          # sometimes include explicit "", sometimes omit
        yield cp


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for cp in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_env(cp)
        oracle = oracle_env(cp)
        if shadow != oracle:
            disagreements.append((cp, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cp, sh, orc in disagreements:
            print("  conn_params=%r shadow=%r oracle=%r" % (cp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of clientEnv (forwardedEnv) agrees with "
          "patch.diff behaviour on %d conn_params (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
