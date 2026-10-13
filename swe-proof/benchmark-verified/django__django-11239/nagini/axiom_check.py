#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11239.

This bundle has NO consumed axioms: the connection-setting publication is
modelled DEEPLY (the per-setting conditional writes spelled out in model.py's
impl region). G-AX therefore validates the single **A-reference** -- that the
deep model equals the real operation it mirrors -- by executing the REAL
repository code (`django.db.backends.postgresql.client.DatabaseClient`) in the
evaluation container and asserting the published PostgreSQL environment matches
the deep model on boundary + randomized-fuzz connection parameters.

The real operation (`runshell_db`) launches an external shell via
`subprocess.run`; we intercept that call (exactly as the repo's own test does)
and capture the `env` mapping handed to the subprocess, then read off the PG*
variables the launched shell would receive.

Deep model under check (model.py impl region), keyed by setting name -> the
dedicated PG* environment variable:

    password    -> PGPASSWORD
    sslmode     -> PGSSLMODE
    sslrootcert -> PGSSLROOTCERT
    sslcert     -> PGSSLCERT
    sslkey      -> PGSSLKEY

For each setting supplied with a non-empty value, that variable is present with
the value verbatim (`str(value)`); for an unsupplied or empty value, the
variable is absent. No other PG* variable is published by the credential /
transport-security publication.

Imports: the standard library plus the repository package under evaluation
(the very module the gold patch edits). Exit 0 iff every observation matches.
"""
import os
import random
import sys
from unittest import mock

import django
from django.conf import settings

# Minimal Django configuration so the backend client module imports cleanly.
if not settings.configured:
    settings.configure(DATABASES={}, INSTALLED_APPS=[])
    django.setup()

import subprocess  # noqa: E402
from django.db.backends.postgresql.client import DatabaseClient  # noqa: E402


# setting name in conn_params  ->  dedicated PG* environment variable
SETTING_TO_ENVVAR = {
    "password": "PGPASSWORD",
    "sslmode": "PGSSLMODE",
    "sslrootcert": "PGSSLROOTCERT",
    "sslcert": "PGSSLCERT",
    "sslkey": "PGSSLKEY",
}


def deep_model_pg_env(conn_params):
    """Reference implementation of model.py's deep model: for each recognised
    setting supplied with a non-empty value, publish its value verbatim under
    the dedicated PG* variable; otherwise leave that variable unset."""
    env = {}
    for setting, envvar in SETTING_TO_ENVVAR.items():
        value = conn_params.get(setting, "")
        if value:
            env[envvar] = str(value)
    return env


def real_pg_env(conn_params):
    """Run the REAL runshell_db and capture the PG* variables it publishes into
    the launched shell's environment (subprocess.run intercepted)."""
    captured = {}

    def _mock_run(*args, env=os.environ, **kwargs):
        # The PostgreSQL environment variables the launched shell receives.
        captured.update({k: env[k] for k in env if k.startswith("PG")})
        return subprocess.CompletedProcess(list(*args) if args else [], 0)

    with mock.patch("subprocess.run", new=_mock_run):
        DatabaseClient.runshell_db(conn_params)
    return captured


def check(conn_params):
    observed = real_pg_env(conn_params)            # real repo code
    expected = deep_model_pg_env(conn_params)      # deep model (model.py)
    assert observed == expected, (
        "deep model unsound on %r: real runshell_db published %r, "
        "deep model gives %r" % (conn_params, observed, expected))


def main():
    # --- boundary cases ----------------------------------------------------
    boundary = [
        {},                                                   # nothing supplied
        {"database": "dbname", "user": "u", "host": "h", "port": "444"},
        {"password": "somepassword"},                         # only password
        {"sslmode": "verify-ca"},                             # only one TLS
        {"sslrootcert": "root.crt"},
        {"sslcert": "client.crt"},
        {"sslkey": "client.key"},
        {                                                     # the F2P config
            "database": "dbname", "user": "someuser",
            "host": "somehost", "port": "444",
            "sslmode": "verify-ca", "sslrootcert": "root.crt",
            "sslcert": "client.crt", "sslkey": "client.key",
        },
        {                                                     # password + all TLS
            "password": "p", "sslmode": "require",
            "sslrootcert": "ca.crt", "sslcert": "c.crt", "sslkey": "k.key",
        },
        {"password": "", "sslmode": "", "sslcert": ""},       # empty -> unset
        {"password": "some:password"},                        # colon value
        {"password": "sésame"},                               # non-ascii value
    ]
    for cp in boundary:
        check(cp)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(11239)
    settings_keys = list(SETTING_TO_ENVVAR.keys())
    value_pool = ["", "x", "verify-ca", "root.crt", "client.crt",
                  "client.key", "some:val", "sésame", "0", "p@ss w0rd"]
    for _ in range(5000):
        cp = {"database": "db", "user": "u", "host": "h", "port": "1"}
        for k in settings_keys:
            if rng.random() < 0.5:
                cp[k] = rng.choice(value_pool)
        check(cp)

    print("G-AX OK: deep model (A-reference) == real DatabaseClient.runshell_db "
          "PG* environment on %d boundary + 5000 fuzz connection-parameter "
          "mappings (5 settings -> PGPASSWORD/PGSSLMODE/PGSSLROOTCERT/"
          "PGSSLCERT/PGSSLKEY)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
