#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11239 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure token helpers (setting_*/envvar_*)
copy over as plain functions. The model uses only builtin Dict operations, so
no PSeq shim is needed. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.backends.postgresql.client.DatabaseClient.runshell_db`. It launches
an external shell via `subprocess.run`; that call is intercepted (exactly as
the repo's own test suite does) to capture the environment mapping handed to
the launched process, from which the PG* credential / transport-security
variables are read off. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2):
  * connection settings `dict` (str -> str)  <->  `Dict[int, int]` of
    setting-name token -> value token. The five recognised setting names map
    to tokens 0..4; string values are interned into int tokens through a
    bijective table built as values are generated.
  * "supplied non-empty" (`.get(k, '')` then an `if value:` guard)  <->  the
    setting's token being PRESENT in the model dict; absent-or-empty  <->
    token absent. Fuzzing therefore draws each setting from three states:
    absent, explicit empty string, or a non-empty value (the first two bridge
    identically to token absence).
  * the published environment restricted to the PG* variables  <->  the
    result `Dict[int, int]` of env-var-name token (100..104) -> value token.
    `str(value)` is the identity on the string values generated here.
  * inherited entries from `os.environ.copy()` are outside the modeled
    behaviour (mapping.md section 2), so any pre-existing PG* variable is
    removed from this process's environment up front; the remaining PG*
    content of the captured environment is exactly the publication under
    check.

Unrecognised connection settings (database/user/host/port and arbitrary extra
keys) are outside the model's token alphabet; they are mixed into the real
conn_params (the callee reads some of them for its argument list) while the
bridged token dict carries only the recognised settings.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz mappings.
Pinned fuzz seed: 11239.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import os
import random
import subprocess
import sys
from unittest import mock

SEED = 11239
N_FUZZ = 100_000


# --- pure helpers from model.py, contracts stripped ---------------------------

def setting_password():
    return 0


def setting_sslmode():
    return 1


def setting_sslrootcert():
    return 2


def setting_sslcert():
    return 3


def setting_sslkey():
    return 4


def envvar_password():
    return 100


def envvar_sslmode():
    return 101


def envvar_sslrootcert():
    return 102


def envvar_sslcert():
    return 103


def envvar_sslkey():
    return 104


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def build_pg_env(conn_params):
    env = {}  # type: dict
    if setting_password() in conn_params:
        env[envvar_password()] = conn_params[setting_password()]
    if setting_sslmode() in conn_params:
        env[envvar_sslmode()] = conn_params[setting_sslmode()]
    if setting_sslrootcert() in conn_params:
        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]
    if setting_sslcert() in conn_params:
        env[envvar_sslcert()] = conn_params[setting_sslcert()]
    if setting_sslkey() in conn_params:
        env[envvar_sslkey()] = conn_params[setting_sslkey()]
    return env


# --- bridge: str settings/values <-> int tokens (mapping.md section 2) --------

SETTING_TOKENS = {
    "password": setting_password(),
    "sslmode": setting_sslmode(),
    "sslrootcert": setting_sslrootcert(),
    "sslcert": setting_sslcert(),
    "sslkey": setting_sslkey(),
}
ENVVAR_NAMES = {
    envvar_password(): "PGPASSWORD",
    envvar_sslmode(): "PGSSLMODE",
    envvar_sslrootcert(): "PGSSLROOTCERT",
    envvar_sslcert(): "PGSSLCERT",
    envvar_sslkey(): "PGSSLKEY",
}

_value_tokens = {}    # str value -> int token (bijective interning table)
_token_values = {}    # int token -> str value


def value_token(v):
    if v not in _value_tokens:
        t = len(_value_tokens) + 1000
        _value_tokens[v] = t
        _token_values[t] = v
    return _value_tokens[v]


def to_token_params(conn_params):
    """Bridge a real conn_params dict to the model's Dict[int,int]: a setting's
    token is present iff the setting is supplied with a non-empty value."""
    tp = {}
    for name, tok in SETTING_TOKENS.items():
        v = conn_params.get(name, "")
        if v:
            tp[tok] = value_token(v)
    return tp


def shadow_pg_env(conn_params):
    """Run the shadow on the bridged tokens and lift the result back to a
    string mapping (env-var name -> value)."""
    out = build_pg_env(to_token_params(conn_params))
    return {ENVVAR_NAMES[k]: _token_values[v] for k, v in out.items()}


# --- oracle: the REAL patched repo callee --------------------------------------

def real_pg_env(client_cls, conn_params):
    """Run the REAL runshell_db and capture the PG* variables it publishes into
    the launched shell's environment (subprocess.run intercepted)."""
    captured = {}

    def _mock_run(*args, env=os.environ, **kwargs):
        captured.update({k: env[k] for k in env if k.startswith("PG")})
        return subprocess.CompletedProcess(list(*args) if args else [], 0)

    with mock.patch("subprocess.run", new=_mock_run):
        client_cls.runshell_db(conn_params)
    return captured


def check(client_cls, conn_params):
    observed = real_pg_env(client_cls, conn_params)
    expected = shadow_pg_env(conn_params)
    if observed != expected:
        print("DISAGREEMENT\n  conn_params=%r\n  real=%r\n  shadow=%r"
              % (conn_params, observed, expected))
        return False
    return True


# --- input generation ----------------------------------------------------------

def boundary_cases():
    return [
        {},                                                   # nothing supplied
        {"database": "dbname", "user": "u", "host": "h", "port": "444"},
        {"password": "somepassword"},                         # only password
        {"sslmode": "verify-ca"},                             # single TLS setting
        {"sslrootcert": "root.crt"},
        {"sslcert": "client.crt"},
        {"sslkey": "client.key"},
        {                                                     # TLS-only config
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
        {"password": "0"},                                    # non-empty falsy-ish
        {"password": "some:password"},                        # separator chars
        {"password": "sésame", "sslkey": "clé.key"},  # non-ascii
        {"password": " ", "sslmode": " "},                    # whitespace-only
        {"extra_setting": "ignored", "sslmode": "require"},   # unrecognised key
    ]


VALUE_POOL = ["", "x", "verify-ca", "verify-full", "require", "root.crt",
              "client.crt", "client.key", "some:val", "sésame", "0",
              "p@ss w0rd", " ", "a" * 64]


def fuzz_case(rng):
    cp = {}
    if rng.random() < 0.8:
        cp.update({"database": "db", "user": "u", "host": "h", "port": "1"})
    for name in SETTING_TOKENS:
        r = rng.random()
        if r < 0.45:
            cp[name] = rng.choice(VALUE_POOL)      # may be empty -> unset
        elif r < 0.55:
            cp[name] = ""                          # explicit empty -> unset
        # else: absent
    if rng.random() < 0.1:
        cp["x_extra_%d" % rng.randint(0, 9)] = "noise"  # unrecognised key
    return cp


def main():
    # Inherited environment entries are outside the modeled behaviour
    # (mapping.md section 2): drop any pre-existing PG* variable so the
    # captured PG* content is exactly the publication under check.
    for k in [k for k in os.environ if k.startswith("PG")]:
        del os.environ[k]

    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DATABASES={}, INSTALLED_APPS=[])
        django.setup()
    from django.db.backends.postgresql.client import DatabaseClient  # REAL patched callee

    checked = 0
    for cp in boundary_cases():
        if not check(DatabaseClient, cp):
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        if not check(DatabaseClient, fuzz_case(rng)):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real publication on %d inputs "
          "(%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
