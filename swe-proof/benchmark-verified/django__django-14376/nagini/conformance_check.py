#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14376 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Invariant/Assert) stripped, plus the @Pure helper `select_name` copied
over as a plain function. PSeq/ToSeq shim: ToSeq(xs) -> tuple(xs); the
PSeq-typed `settings_name` parameter of the helper is passed as a tuple.
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.backends.mysql.client.DatabaseClient.settings_to_cmd_args_env`.
The gate applies patch.diff to /testbed BEFORE this script runs (do not apply
it here); PYTHONPATH=/testbed makes the patched module importable. The
settings dict carries no user / password / host / port / charset / ssl
options, so the only trailing positional entry after the executable token is
the database name (if any); that trailing entry is the observable this check
compares against the shadow.

Type bridge (mapping.md "Type abstraction"):
  * a database-name str s  <->  List[int] of code points [ord(c) for c in s];
    the empty str <-> [].
  * connection-options key present with value v <-> the corresponding
    Optional[List[int]] parameter holds the encoded v; key absent <-> None
    (dict.get membership semantics: a present key short-circuits the
    fallback even when its value is the empty string).
  * shadow result (appended, database): `appended` <-> a trailing positional
    argument was emitted; `database` decoded via chr <-> that argument's
    character content. No trailing argument <-> appended is False.

Input domain (the model's Requires): each option is absent (None) or an
arbitrary code-point list; settings_name is an arbitrary code-point list.
Boundary cases enumerate {absent, empty, several distinct non-empty values}
for both options crossed with {empty, non-empty} settings names — including
the both-present-with-different-values discriminator — and fuzz draws random
unicode strings (BMP, surrogates excluded) plus empty/absent with high
probability so every precedence branch is hit continually.

>= 1e5 Requires-satisfying inputs: 150 boundary + 100000 fuzz triples.
Pinned fuzz seed: 14376.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 14376
N_FUZZ = 100_000

# absent-key sentinel for the str-level input domain
_ABSENT = object()


# --- PSeq shim ----------------------------------------------------------------

def ToSeq(xs):
    return tuple(xs)


# --- pure helper from model.py, decorator + contracts stripped -----------------

def select_name(opt_primary, opt_legacy, settings_name):
    if opt_primary is not None:
        return ToSeq(opt_primary)
    if opt_legacy is not None:
        return ToSeq(opt_legacy)
    return settings_name


# --- the impl region of model.py, verbatim (contract calls stripped) -----------

def resolve_db_arg(opt_database, opt_db, settings_name):
    if opt_database is not None:
        chosen = opt_database
    elif opt_db is not None:
        chosen = opt_db
    else:
        chosen = settings_name
    database = []
    i = 0
    while i < len(chosen):
        database.append(chosen[i])
        i = i + 1
    appended = len(database) > 0
    return appended, database


# --- bridge helpers -------------------------------------------------------------

def encode(s):
    """str -> the model's List[int] code-point carrier (absent -> None)."""
    if s is _ABSENT:
        return None
    return [ord(c) for c in s]


def decode(xs):
    return "".join(chr(c) for c in xs)


def real_trailing_db_arg(callee, opt_database, opt_db, settings_name):
    """Run the REAL patched callee and return the trailing positional database
    argument it emits (None when it emits none). With no user/host/port/
    charset/ssl configured, args is the executable token plus at most that one
    trailing entry."""
    options = {}
    if opt_database is not _ABSENT:
        options["database"] = opt_database
    if opt_db is not _ABSENT:
        options["db"] = opt_db
    settings_dict = {
        "NAME": settings_name,
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
        "OPTIONS": options,
    }
    args, env = callee(settings_dict, [])
    rest = args[1:]
    if not rest:
        return None
    if len(rest) != 1:
        raise AssertionError(
            "expected at most one trailing positional entry, got %r "
            "for options=%r NAME=%r" % (rest, options, settings_name))
    return rest[0]


def check_case(callee, opt_database, opt_db, settings_name):
    appended, db_list = resolve_db_arg(
        encode(opt_database), encode(opt_db), ToSeq(encode(settings_name)))
    shadow_out = decode(db_list) if appended else None
    real_out = real_trailing_db_arg(callee, opt_database, opt_db, settings_name)
    if shadow_out != real_out:
        return ("DISAGREEMENT\n"
                "  opt_database=%r opt_db=%r settings_name=%r\n"
                "  shadow=(appended=%r, database=%r) -> %r\n"
                "  real trailing argument=%r"
                % (opt_database, opt_db, settings_name,
                   appended, db_list, shadow_out, real_out))
    return None


def boundary_cases():
    values_or_absent = [_ABSENT, "", "alpha", "beta", "third"]
    names = ["", "fromsettings", "alpha", "x", "é中"]
    cases = []
    for settings_name in names:
        for opt_database in values_or_absent:
            for opt_db in values_or_absent:
                cases.append((opt_database, opt_db, settings_name))
    # 5 * 5 * 5 = 125, incl. both-present-different-values discriminators,
    # present-but-empty short-circuits, and the all-absent fallthrough.
    # A few extra: long and exotic content on each level.
    long = "d" * 300
    cases += [
        (long, "b", "c"), (_ABSENT, long, "c"), (_ABSENT, _ABSENT, long),
        ("naïve☃", _ABSENT, ""), (_ABSENT, "\U0001f40d", ""),
        (" ", "", ""), ("", " ", ""), (_ABSENT, "", " "),
        ("0", "1", "2"), ("same", "same", "same"),
    ]
    while len(cases) < 150:
        cases.append((_ABSENT, _ABSENT, ""))
    return cases


def rand_str(rng):
    n = rng.choice([0, 1, 1, 2, 3, 5, 8, 20, 64])
    out = []
    for _ in range(n):
        k = rng.randint(0, 3)
        if k == 0:
            cp = rng.randint(97, 122)          # ascii letters
        elif k == 1:
            cp = rng.randint(32, 126)          # printable ascii
        elif k == 2:
            cp = rng.randint(0x00A0, 0x2FFF)   # latin-1 supplement .. CJK sym
        else:
            cp = rng.randint(1, 0xD7FF)        # BMP below the surrogate block
        out.append(chr(cp))
    return "".join(out)


def rand_opt(rng):
    k = rng.randint(0, 4)
    if k == 0:
        return _ABSENT
    if k == 1:
        return ""       # present-but-empty: must still short-circuit
    return rand_str(rng)


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
        django.setup()
    from django.db.backends.mysql.client import DatabaseClient

    callee = DatabaseClient.settings_to_cmd_args_env

    checked = 0
    n_boundary = 0
    for opt_database, opt_db, settings_name in boundary_cases():
        err = check_case(callee, opt_database, opt_db, settings_name)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(callee, rand_opt(rng), rand_opt(rng), rand_str(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real trailing database argument on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
