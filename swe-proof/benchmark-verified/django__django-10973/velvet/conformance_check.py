#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-10973 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`). `passwordEnvValue` is the
              verbatim per-code-point copy of the password (the backward `while`
              fold conses each code point unchanged), so the shadow is the
              identity on the password string. There is no A-tagged callee in
              the computed value (the proof consumes no axiom); the impl region
              is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the value the patched `runshell_db`
              exposes to the child for the password — `PGPASSWORD` in the
              subprocess env, which is `str(passwd)` when `passwd` is truthy and
              absent otherwise. We invoke the patched repo function with
              `subprocess.run` mocked exactly as the gold test does and read back
              `env.get('PGPASSWORD')` (the real correctness oracle, G-RESOLVE).

They must agree on every input. The model's `out` (verbatim password) must equal
the oracle's exposed value when the password is non-empty; when the password is
empty the model's `out` is empty and the oracle exposes no `PGPASSWORD` (None) —
the populated-iff-non-empty postcondition (A3). Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image with the gold patch
applied), stdlib only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import os
import random
import subprocess
import sys

SEED = 10973
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean passwordEnvValue, transliterated ----------
def shadow_password_value(passwd):
    """passwordEnvValue (passwd.toList) transliterated to str: the verbatim
    per-code-point copy of the password. The backward `while` fold conses each
    code point of `passwd` unchanged, so the result is `passwd` itself. The
    populated-iff-non-empty face: a non-empty result iff `passwd` is non-empty.
    Returns (exposed_value_or_None) to mirror the oracle's observable: the value
    is exposed (present) exactly when the password is non-empty."""
    out = "".join(ch for ch in passwd)          # verbatim copy, code point by code point
    return out if len(out) > 0 else None        # populated iff non-empty (A3)


# --- the oracle: patch.diff's runshell_db, PGPASSWORD as the gold test reads it
def oracle_password_value(passwd):
    """patch.diff behaviour: invoke the patched runshell_db with subprocess.run
    mocked exactly as the gold test_patch does, and return env.get('PGPASSWORD')
    — the value exposed to the child for the password (None if unset)."""
    from unittest import mock
    from django.db.backends.postgresql.client import DatabaseClient

    captured = {}

    def _mock_run(*args, env=os.environ, **kwargs):
        captured["pgpassword"] = env.get("PGPASSWORD")
        return subprocess.CompletedProcess(list(*args) if args else [], 0)

    with mock.patch("subprocess.run", new=_mock_run):
        DatabaseClient.runshell_db({
            "database": "dbname",
            "user": "someuser",
            "password": passwd,
            "host": "somehost",
            "port": "444",
        })
    return captured.get("pgpassword")


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): empty, the discriminators the
    # legacy quoting would have transformed (':' and '\\'), accents, mixtures.
    yield ""
    yield "somepassword"
    yield "some:password"          # F2P test_column: must stay verbatim, not 'some\\:password'
    yield "sésame"                 # F2P test_accent
    yield ":"
    yield "\\"
    yield "\\:"
    yield ":\\:"
    yield "a:b:c"
    yield "back\\slash"
    yield "host:444:db:user:pw"    # what the legacy pgpass line looked like
    yield "•"
    alphabet = list("abcDEF012 :\\;#@é•")
    for _ in range(n):
        k = rng.randint(0, 24)
        # only fuzz the non-empty case for the value comparison; empty handled above
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_password_value(s)
        oracle = oracle_password_value(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of passwordEnvValue agrees with patch.diff "
          "PGPASSWORD behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
