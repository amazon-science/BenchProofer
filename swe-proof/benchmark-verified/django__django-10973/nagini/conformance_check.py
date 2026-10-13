#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-10973 (nagini).

SHADOW: the impl region of `model.py::password_env_value`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
After stripping, the body uses only plain-list operations, so no PSeq shim is
needed (PSeq/ToSeq appear only inside contracts). There are no @ContractOnly
callees (meta.json: axioms == []).

ORACLE: the REAL patched repo function the model models per mapping.md /
refinement.md — the password-exposure logic of
`django.db.backends.postgresql.client.DatabaseClient.runshell_db`. The gate
applies patch.diff to /testbed before this script runs (PYTHONPATH=/testbed);
this script does NOT apply the patch itself. To observe the value the real
function hands to the child process for the password, `subprocess.run` is
replaced by a recorder (the same observation point the repo's own test suite
uses), `runshell_db` is invoked for real, and the recorded child environment
is inspected for the password entry (`PGPASSWORD`).

Type bridge (mapping.md section 2):
  * `passwd: List[int]`  <->  a `str` password (`conn_params['password']`),
    element i of the list == code point i of the string.
  * the returned `List[int]` (the value exposed to the child) <-> the child
    environment's password entry when present; an ABSENT entry (mechanism not
    populated) <-> the empty list, matching the model's
    `(len(Result()) > 0) == (len(passwd) > 0)` populated-iff-non-empty clause.

Input domain: the model's Requires asks only for a well-formed read-only
input list of code points; bridged through mapping.md the inputs are Unicode
password strings (valid scalar values only — surrogates are not encodable
strings, hence outside the carrier). Boundary cases cover empty, the
quoting-sensitive code points (colon, backslash) alone / doubled / mixed,
accented text, and pgpass-line-shaped material; fuzz draws from an alphabet
weighted toward those code points plus random scalar values.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz strings.
Pinned fuzz seed: 10973.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import os
import random
import sys

from django.db.backends.postgresql import client as pg_client  # REAL patched repo module

# The oracle copies the process environment for the child; a pre-existing
# password entry there would pollute the observation, so clear it up front.
os.environ.pop("PGPASSWORD", None)

SEED = 10973
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def password_env_value(passwd):
    result = []  # type: list
    i = 0
    while i < len(passwd):
        c = passwd[i]
        result = result + [c]
        i = i + 1
    return result


# --- oracle: the real patched runshell_db, child process replaced by a -------
# --- recorder so the environment handed to the child can be inspected --------

class _ChildEnvRecorder:
    """Stands in for the child-process launcher; records the env it is
    handed (keyword or positional) instead of spawning anything."""

    def __init__(self):
        self.env = None
        self.called = False

    def __call__(self, *args, **kwargs):
        self.called = True
        self.env = kwargs.get("env")
        return None


def real_exposed_password(passwd_str):
    """Run the REAL patched runshell_db with the child launcher recorded and
    return the password value it exposes to the child, as a list of code
    points ([] when the mechanism is not populated)."""
    recorder = _ChildEnvRecorder()
    saved_run = pg_client.subprocess.run
    pg_client.subprocess.run = recorder
    try:
        pg_client.DatabaseClient.runshell_db({
            "database": "dbname",
            "user": "someuser",
            "host": "somehost",
            "port": "444",
            "password": passwd_str,
        })
    finally:
        pg_client.subprocess.run = saved_run
    if not recorder.called:
        raise RuntimeError("real runshell_db never invoked the child launcher")
    env = recorder.env
    if env is None:
        # No dedicated child environment passed: mechanism not populated.
        return []
    value = env.get("PGPASSWORD")
    if value is None:
        return []
    return [ord(ch) for ch in value]


# --- differential check -------------------------------------------------------

def check_password(passwd_str):
    """Diff shadow vs real oracle on one password; return an error string on
    disagreement, else None."""
    codepoints = [ord(ch) for ch in passwd_str]
    shadow = password_env_value(codepoints)
    real = real_exposed_password(passwd_str)
    if shadow != real:
        return ("DISAGREEMENT\n"
                "  passwd=%r (codepoints=%r)\n"
                "  shadow=%r\n"
                "  real=%r" % (passwd_str, codepoints, shadow, real))
    return None


def boundary_passwords():
    return [
        "",                              # empty: mechanism must not populate
        ":",
        "\\",
        "::",
        "\\\\",
        ":\\",
        "\\:",
        "somepassword",
        "some:password",
        "some\\password",
        "some\\\\password",
        "s\u00e9same",                   # accented
        "::1:444:dbname:some:user",      # pgpass-line-shaped material
        "a\\b:c\\:d::e",
        "C:\\path\\to\\file",
        " ",                             # whitespace-only (truthy str)
        "0",                             # falsy-looking but truthy str
        "\u00e9\u00f4\u00ea",
        "\u2603\u4e2d\U0001f40d",        # beyond latin-1 / BMP
        "a" * 300,                       # long
    ]


# fuzz alphabet: weighted toward the quoting-sensitive code points, plus
# ordinary ASCII and a few non-ASCII scalar values
_ALPHABET = list(":\\") * 4 + list("abZ0 ;#x9'\"=@/.-_") + [
    "\u00e9", "\u00f4", "\u00ea", "\u2603", "\u4e2d", "\U0001f40d",
]


def rand_password(rng):
    n = rng.randint(0, 24)
    if rng.random() < 0.05:
        # fully random valid scalar values (skip the surrogate block)
        chars = []
        for _ in range(n):
            cp = rng.randint(1, 0x10FFFF)
            while 0xD800 <= cp <= 0xDFFF:
                cp = rng.randint(1, 0x10FFFF)
            chars.append(chr(cp))
        return "".join(chars)
    return "".join(rng.choice(_ALPHABET) for _ in range(n))


def main():
    checked = 0
    boundaries = boundary_passwords()
    for s in boundaries:
        err = check_password(s)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_password(rand_password(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real exposed password value on %d "
          "passwords (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundaries), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; no "
                                "@ContractOnly callees)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
