#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15851.

The bundle models ONE function: `DatabaseClient.settings_to_cmd_args_env`
(`django/db/backends/postgresql/client.py`), specifically its `args`
(command-line vector) assembly. Its Lean implementation
(`implementation_shellArgs`) builds the vector, in order, as:

    [executable]
      + (["-U", user] if user else [])
      + (["-h", host] if host else [])
      + (["-p", port] if port else [])
      + parameters
      + ([dbname] if dbname else [])

This script transliterates that R/I impl into Python (`shadow_args`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch behavior of `settings_to_cmd_args_env`'s `args` assembly:

    args = [executable]
    if user:  args += ["-U", user]
    if host:  args += ["-h", host]
    if port:  args += ["-p", port]
    args.extend(parameters)          # the moved op: parameters BEFORE dbname
    if dbname:  args += [dbname]

We do NOT stand up the Django backend / settings machinery (heavy, and the
modeled value is a pure list assembly). Instead we feed both sides the SAME
observable inputs the real function consumes (mapping.md): the program name, the
four optional truthy settings (`None` when absent/falsy), and the extra
`parameters` list. The effective-dbname defaulting and the per-setting truthiness
reads are folded into those inputs exactly as the real function would compute
them before the (unchanged) assembly steps.

The returned `env` dict is unchanged by the patch and out of scope. The
differential is on the `args` vector itself — in particular its critical ordering:
caller-supplied parameters must precede the database name.

stdlib-only; pinned seed 15851 (also recorded in mapping.md).
"""
import sys

SEED = 15851
N = 120_000

STRINGS = ["", "a", "ab", "x", "psql", "-c", "select", "dbname", "1", "5432"]


# --- ORACLE: the post-patch behavior, faithful in-process replica -----------
# Each optional input is the account's effective truthy value or None.
def oracle_args(executable, user, host, port, dbname, parameters):
    args = [executable]
    if user:
        args += ["-U", user]
    if host:
        args += ["-h", host]
    if port:
        args += ["-p", port]
    args.extend(parameters)          # post-patch: parameters spliced BEFORE dbname
    if dbname:
        args += [dbname]
    return args


# --- shadow of implementation_shellArgs (the R/I leg) ------------------------
# Mirrors Solution.lean: optFlag emits [flag, v] when present, [] when absent;
# dbname.toList emits [d] when present, [] when absent.
def opt_flag(flag, v):
    return [flag, v] if v is not None else []


def to_list(v):
    return [v] if v is not None else []


def shadow_args(executable, user, host, port, dbname, parameters):
    args = [executable]
    args = args + opt_flag("-U", user)
    args = args + opt_flag("-h", host)
    args = args + opt_flag("-p", port)
    args = args + list(parameters)
    args = args + to_list(dbname)
    return args


# Bridge the truthiness boundary: the oracle uses Python truthiness (`if user`),
# which treats "" (empty string) as falsy. The Lean model uses Option presence
# (`some` vs `none`). mapping.md pins `none ⟺ absent/falsy`, so to compare the
# two faithfully we pass `None` to BOTH sides for a falsy value. The shadow's
# `Option` is therefore never `some ""` — empty-string settings map to `none`.
def normalize(v):
    return v if v else None


def disagree(args):
    executable, user, host, port, dbname, parameters = args
    user = normalize(user)
    host = normalize(host)
    port = normalize(port)
    dbname = normalize(dbname)
    got = oracle_args(executable, user, host, port, dbname, parameters)
    want = shadow_args(executable, user, host, port, dbname, parameters)
    if got != want:
        return (args, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked cases exercising the parameters/dbname ordering."""
    cases = []
    # The FAIL_TO_PASS case: NAME=dbname, parameters=["--help"].
    cases.append(("psql", None, None, None, "dbname", ["--help"]))
    # parameters present, dbname present -> parameters MUST precede dbname:
    cases.append(("psql", None, None, None, "db", ["-c", "select * from t;"]))
    # parameters present, dbname absent:
    cases.append(("psql", None, None, None, None, ["-c", "x"]))
    # parameters empty, dbname present (prefix-only, order irrelevant):
    cases.append(("psql", "u", "h", "5432", "db", []))
    # everything absent except executable:
    cases.append(("psql", None, None, None, None, []))
    # all connection options + parameters + dbname:
    cases.append(("psql", "u", "h", "5432", "db", ["-c", "q", "--x"]))
    return cases


def main() -> int:
    checked = 0

    for args in _enumerate_edge():
        d = disagree(args)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        def pick():
            return STRINGS[next(rnd) % len(STRINGS)]

        def opt():
            # None ~1/3 of the time, else a string (possibly "")
            return None if next(rnd) % 3 == 0 else pick()

        executable = "psql"
        user = opt()
        host = opt()
        port = opt()
        dbname = opt()
        plen = next(rnd) % 5  # 0..4
        parameters = [pick() for _ in range(plen)]
        d = disagree((executable, user, host, port, dbname, parameters))
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
