#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_dbShellCommand
against the patch.diff behaviour (post-patch psql invocation).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The two
observable components are:
  - the client argument vector handed to the subprocess invocation, and
  - the password made available to the child process (PGPASSWORD).

The shadow reproduces the impl op-for-op (literal head 'psql', then the
user/host/port option pairs gated on non-emptiness, then the dbname, plus the
password slot set iff passwd is non-empty). We diff that against an independent
reconstruction that drives the ACTUAL post-patch `runshell_db` code path with
`subprocess.run` mocked, capturing exactly the 2-tuple the F2P tests observe:
`(subprocess_args, env.get('PGPASSWORD'))`. Zero disagreements required over
>=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import os
import random
import signal
import sys
from unittest import mock

SEED = 10973          # pinned in mapping.md
N = 120_000           # >= 10^5

# Alphabets oversample the empty string and a few delimiter-ish characters so the
# truthiness gating and the (post-fix) raw-password passthrough are exercised.
STR_ALPHABET = list("abcXYZ_.:\\ 019")
PORTS = ["", "5432", "444", "0", "65535"]


def rand_str(rng, allow_empty=True, maxlen=12):
    if allow_empty and rng.random() < 0.25:
        return ""
    return "".join(rng.choice(STR_ALPHABET) for _ in range(rng.randint(1, maxlen)))


def shadow(host, port, dbname, user, passwd):
    """R/I shadow of implementation_dbShellCommand -> (args, password_env)."""
    args = ["psql"]
    if user != "":
        args += ["-U", user]
    if host != "":
        args += ["-h", host]
    if port != "":
        args += ["-p", port]
    args += [dbname]
    password_env = None
    if passwd != "":
        password_env = passwd
    return args, password_env


def real_runshell(host, port, dbname, user, passwd):
    """Drive the ACTUAL post-patch runshell_db with subprocess.run mocked,
    capturing the (args, PGPASSWORD) tuple exactly as the F2P tests do."""
    from django.db.backends.postgresql.client import DatabaseClient

    captured = {}

    def _mock_run(*a, env=os.environ, **kwargs):
        captured["args"] = list(*a)
        captured["pgpassword"] = env.get("PGPASSWORD")
        import subprocess
        return subprocess.CompletedProcess(captured["args"], 0)

    conn_params = {
        "host": host, "port": port, "database": dbname,
        "user": user, "password": passwd,
    }
    # Match the FAIL_TO_PASS harness condition: a clean ambient environment with
    # no pre-existing PGPASSWORD (so test_nopass-style cases observe None). See
    # mapping.md "Scoping assumption". os.environ.copy() in the real code then
    # only carries a PGPASSWORD that runshell_db itself sets.
    os.environ.pop("PGPASSWORD", None)
    sigint = signal.getsignal(signal.SIGINT)
    with mock.patch("subprocess.run", new=_mock_run):
        DatabaseClient.runshell_db(conn_params)
    signal.signal(signal.SIGINT, sigint)
    return captured["args"], captured["pgpassword"]


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    fixed = [
        ("somehost", "444", "dbname", "someuser", "somepassword"),
        ("::1", "444", "dbname", "some:user", "some:password"),
        ("somehost", "444", "dbname", "someuser", ""),          # test_nopass shape
        ("somehost", "444", "dbname", "role", "sesame"),        # accent shape
        ("", "", "", "", ""),
        ("", "", "dbname", "", "pw"),
        ("h", "", "db", "u", ""),
        ("\\", ":", "d:b", "u\\u", "p\\:w"),
    ]
    cases = fixed + [
        (
            rand_str(rng),
            rng.choice(PORTS),
            rand_str(rng, allow_empty=False),
            rand_str(rng),
            rand_str(rng),
        )
        for _ in range(N)
    ]

    for host, port, dbname, user, passwd in cases:
        got = shadow(host, port, dbname, user, passwd)
        want = real_runshell(host, port, dbname, user, passwd)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((host, port, dbname, user, passwd), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} real={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
