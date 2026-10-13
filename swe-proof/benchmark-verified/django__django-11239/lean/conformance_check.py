#!/usr/bin/env python3
"""G-CONF for django__django-11239 — differential test of the R/I shadow of
`implementation_runShell` against the REAL post-patch `runshell_db` behaviour.

The impl region is NOT all-A-tagged (it is pure R/I structure: optional-string
reads, non-emptiness guards, list concatenation, env (name,value) appends). This
check builds the Python shadow of `implementation_runShell` op-for-op and diffs
it against the ACTUAL repo callee `DatabaseClient.runshell_db` (with the gold
patch applied), observed exactly the way the official tests observe it: the
captured argument vector and the `PG*`-prefixed projection of the child-process
environment. Asserts zero disagreements over >=10^5 fuzzed inputs.

stdlib-only (django is the testbed under test). Exit 0 iff zero disagreements.
Pinned seed: 11239.
"""
import os
import random
import subprocess
import sys

SEED = 11239
N = 120_000

# The nine connection-parameter keys the method reads, in mapping.md order.
ARG_KEYS = ['host', 'port', 'database', 'user', 'password']
SSL_KEYS = ['sslmode', 'sslrootcert', 'sslcert', 'sslkey']
ALL_KEYS = ARG_KEYS + SSL_KEYS


# ---- Lean R/I shadow (mirrors implementation_runShell exactly) --------------
def shadow(cp):
    """cp: dict with the nine keys (missing key == absent == '')."""
    def g(k):
        return cp.get(k, '')
    args = ['psql']
    if g('user'):     args += ['-U', g('user')]
    if g('host'):     args += ['-h', g('host')]
    if g('port'):     args += ['-p', g('port')]
    args += [g('database')]
    pg = []
    if g('password'):    pg.append(('PGPASSWORD',    g('password')))
    if g('sslmode'):     pg.append(('PGSSLMODE',     g('sslmode')))
    if g('sslrootcert'): pg.append(('PGSSLROOTCERT', g('sslrootcert')))
    if g('sslcert'):     pg.append(('PGSSLCERT',     g('sslcert')))
    if g('sslkey'):      pg.append(('PGSSLKEY',      g('sslkey')))
    return args, pg


# ---- Real-callee observation (mirrors tests/dbshell/test_postgresql.py) -----
def _setup():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[])
    django.setup()


def real(cp):
    """Drive the actual runshell_db, capturing args + PG* env, exactly as the
    official test harness does (mock subprocess.run)."""
    from unittest import mock
    from django.db.backends.postgresql.client import DatabaseClient

    captured = {}

    def _mock_run(*args, env=os.environ, **kwargs):
        captured['args'] = list(*args)
        captured['pg'] = {k: env[k] for k in env if k.startswith('PG')}
        return subprocess.CompletedProcess(captured['args'], 0)

    with mock.patch('subprocess.run', new=_mock_run):
        DatabaseClient.runshell_db(cp)
    return captured['args'], captured['pg']


def _norm_pg(pg_pairs):
    """The tests observe the PG* env as a dict (order-insensitive)."""
    return dict(pg_pairs)


# ---- Input generation --------------------------------------------------------
def edge_inputs():
    base = {'database': 'dbname', 'user': 'someuser', 'host': 'somehost', 'port': '444'}
    ssl = {'sslmode': 'verify-ca', 'sslrootcert': 'root.crt',
           'sslcert': 'client.crt', 'sslkey': 'client.key'}
    return [
        {},                                            # all absent
        {'database': 'dbname'},                         # only dbname
        dict(base),                                     # no pass, no ssl (test_basic/test_nopass)
        {**base, 'password': 'somepassword'},           # password only (test_basic)
        {**base, 'user': 'some:user', 'host': '::1', 'password': 'some:password'},  # test_column
        {**base, **ssl},                                # all ssl, no password (test_ssl_certificate)
        {**base, 'password': 'pw', **ssl},              # password + all ssl
        {**base, 'sslmode': 'verify-ca'},               # one ssl param
        {**base, 'sslcert': 'c.crt', 'sslkey': 'k.key'},  # subset of ssl
        {'user': 'u'},                                  # user but empty dbname default
    ]


VALUES = ['', 'x', 'someuser', 'somehost', '444', 'verify-ca', 'root.crt',
          'client.crt', 'client.key', 'some:user', '::1', 'pw', 'dbname',
          'a b', 'verify-full']


def fuzz_input(rng):
    cp = {}
    for k in ALL_KEYS:
        v = rng.choice(VALUES)
        # ~half the time omit the key entirely (== '' default) to exercise both
        # the absent-key and explicit-empty-string paths.
        if v == '' and rng.random() < 0.5:
            continue
        cp[k] = v
    return cp


def main() -> int:
    try:
        _setup()
    except Exception as e:  # noqa: BLE001
        print(f"status=error setup_failed={e!r}")
        return 2

    rng = random.Random(SEED)
    cases = edge_inputs() + [fuzz_input(rng) for _ in range(N)]
    disagreements = 0
    examples = []

    for cp in cases:
        try:
            r_args, r_pg = real(cp)
        except Exception as e:  # noqa: BLE001
            print(f"status=fail runshell_db raised on {cp!r}: {e!r}")
            return 1
        s_args, s_pg = shadow(cp)
        if r_args != s_args or _norm_pg(r_pg) != _norm_pg(s_pg):
            disagreements += 1
            if len(examples) < 10:
                examples.append((cp, (s_args, dict(s_pg)), (r_args, r_pg)))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for cp, s, r in examples:
            print(f"  cp={cp!r}\n    shadow={s!r}\n    real  ={r!r}")
        return 1

    print(f"checked={len(cases)} mismatches=0")
    print(f"status=pass (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
