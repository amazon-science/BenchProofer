#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14376.

The bundle models TWO independent functions:

  1. `dbArg`  — `DatabaseClient.settings_to_cmd_args_env` (mysql/client.py): the
     choice of the trailing database-name argument. Post-patch:

         database = OPTIONS.get('database', OPTIONS.get('db', NAME))
         if database: args += [database]

     The Lean impl (`implementation_dbArg`) is the R/I shadow:

         chosen = optDatabase.getD (optDb.getD name)
         result = chosen if chosen != "" else <none>

  2. `connParams` — `DatabaseWrapper.get_connection_params` (mysql/base.py): the
     entries it writes for the database name and password. Post-patch:

         if NAME:     kwargs['database'] = NAME
         if PASSWORD: kwargs['password'] = PASSWORD

     The Lean impl (`implementation_connParams`) is the R/I shadow:

         [] ++ ([("database", n)] if name else []) ++ ([("password", p)] if pw else [])

This script transliterates both R/I impls into Python and differential-tests them
against faithful in-process replicas of the post-patch behavior. We do NOT stand
up the Django backend; the modeled values are pure selections/assemblies. We feed
both sides the SAME observable inputs the real functions consume (mapping.md).

CRITICAL boundary detail for `dbArg`: `dict.get(k, default)` returns the stored
value when the key is PRESENT even if that value is empty (`""`), short-circuiting
the lower-precedence sources. So the `'database'`/`'db'` options must be modeled
with PRESENCE distinct from value — we represent an option as `None` (key absent)
or a 1-tuple `(value,)` (key present, value possibly ""). `Option.getD` maps
present ↦ value, absent ↦ default.

For `connParams` the reads are guarded by Python truthiness (`if NAME`), so empty
and absent collapse — empty strings map to `none` on both sides.

stdlib-only; pinned seed 14376 (also recorded in mapping.md).
"""
import sys

SEED = 14376
N = 120_000

STRINGS = ["", "a", "ab", "db", "settingdbname", "optiondbname",
           "deprecatedoptiondbname", "pw", "optionpassword"]


# ============================================================================
# Triple 1: dbArg
# ============================================================================

# --- ORACLE: post-patch behavior, faithful in-process replica ---------------
# options: a real dict possibly containing 'database' and/or 'db' keys.
def oracle_dbarg(options, name):
    database = options.get('database', options.get('db', name))
    return database if database else None   # trailing token (None == no token)


# --- SHADOW: the R/I impl (implementation_dbArg) ----------------------------
# An option is None (absent) or a 1-tuple (value,) (present). getD:
def get_d(opt, default):
    return opt[0] if opt is not None else default


def shadow_dbarg(opt_database, opt_db, name):
    chosen = get_d(opt_database, get_d(opt_db, name))
    return chosen if chosen != "" else None


def disagree_dbarg(opt_database, opt_db, name):
    # Build the real options dict from the presence/value of each option.
    options = {}
    if opt_db is not None:
        options['db'] = opt_db[0]
    if opt_database is not None:
        options['database'] = opt_database[0]
    got = oracle_dbarg(options, name)
    want = shadow_dbarg(opt_database, opt_db, name)
    if got != want:
        return ((opt_database, opt_db, name), got, want)
    return None


# ============================================================================
# Triple 2: connParams
# ============================================================================

# --- ORACLE: post-patch behavior --------------------------------------------
def oracle_connparams(name, password):
    kwargs = {}
    if name:
        kwargs['database'] = name
    if password:
        kwargs['password'] = password
    # Return the modeled entries as an ordered list (NAME entry, then PASSWORD).
    out = []
    if 'database' in kwargs:
        out.append(('database', kwargs['database']))
    if 'password' in kwargs:
        out.append(('password', kwargs['password']))
    return out


# --- SHADOW: the R/I impl (implementation_connParams) -----------------------
# name/password are Option String folded from Python truthiness (empty -> none).
def shadow_connparams(name, password):
    out = []
    if name is not None:
        out.append(('database', name))
    if password is not None:
        out.append(('password', password))
    return out


def norm(v):
    """Truthiness boundary: empty/None falsy -> Option none."""
    return v if v else None


def disagree_connparams(name, password):
    got = oracle_connparams(name, password)
    want = shadow_connparams(norm(name), norm(password))
    if got != want:
        return ((name, password), got, want)
    return None


# ============================================================================
# Driver
# ============================================================================

def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _edge_dbarg():
    """Hand-picked dbArg cases. opt is None or (value,)."""
    return [
        # FAIL_TO_PASS test_options_non_deprecated_keys_preferred: both keys
        # present, 'database' wins.
        (("optiondbname",), ("deprecatedoptiondbname",), "settingdbname"),
        # test_options_override_settings_proper_values, ('db','passwd') spelling:
        (None, ("optiondbname",), "settingdbname"),
        # ('database','password') spelling:
        (("optiondbname",), None, "settingdbname"),
        # no options -> falls through to NAME:
        (None, None, "somedbname"),
        # present-but-empty 'database' short-circuits, then dropped (no token):
        (("",), ("dbval",), "settingdbname"),
        # present-but-empty 'db' short-circuits NAME, then dropped:
        (None, ("",), "settingdbname"),
        # everything empty -> no token:
        (None, None, ""),
        # 'database' present, 'db' present, both non-empty, 'database' wins:
        (("a",), ("b",), "c"),
    ]


def _edge_connparams():
    return [
        ("settingdbname", "settingpassword"),
        ("settingdbname", None),
        (None, "settingpassword"),
        (None, None),
        ("", ""),            # both falsy -> empty
        ("somedbname", ""),  # password falsy
    ]


def main() -> int:
    checked = 0

    # --- dbArg ---
    for c in _edge_dbarg():
        d = disagree_dbarg(*c)
        if d:
            print(f"DISAGREE dbArg edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    # --- connParams ---
    for c in _edge_connparams():
        d = disagree_connparams(*c)
        if d:
            print(f"DISAGREE connParams edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)

    def pick():
        return STRINGS[next(rnd) % len(STRINGS)]

    def opt_present():
        # None ~1/3 (key absent), else a 1-tuple with a (possibly empty) value.
        return None if next(rnd) % 3 == 0 else (pick(),)

    def opt_truthy():
        # None ~1/3, else a (possibly empty) string.
        return None if next(rnd) % 3 == 0 else pick()

    half = N // 2
    for _ in range(half):
        c = (opt_present(), opt_present(), pick())
        d = disagree_dbarg(*c)
        if d:
            print(f"DISAGREE dbArg fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    for _ in range(N - half):
        c = (opt_truthy(), opt_truthy())
        d = disagree_connparams(*c)
        if d:
            print(f"DISAGREE connParams fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
