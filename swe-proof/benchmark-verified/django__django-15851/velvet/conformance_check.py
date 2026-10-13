#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-15851 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
`DatabaseClient.settings_to_cmd_args_env(...)` argument-vector builder.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the observable output (the
argument vector — the first element of the returned tuple):

  * SHADOW  — Solution.lean's modeled assembly, transliterated to Python over
              the real repo types via the mapping.md §2 bijection:
                  leading      <->  the args list built up through the executable
                                     name and the -U/-h/-p connection-option
                                     flags (unchanged code; reconstructed here
                                     exactly as the repo builds it)
                  dbname        <->  Option String: some s for a truthy NAME
                                     (or the "postgres" default), none otherwise
                  parameters    <->  the extra-args list
                  builtArgs leading dbname parameters =
                      leading ++ parameters ++ dbnameToken dbname
              i.e. the extra parameters precede the optional database-name token,
              and the database name (when present) is last. There are NO A-tagged
              ops (no consumed axioms), so the shadow is pure R/I.

  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `DatabaseClient.settings_to_cmd_args_env(settings_dict, parameters)`,
              reading back `[0]` (the args vector).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib + django only (the
classmethod consults only its dict/list arguments, no DB, no django.conf).
Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 15851
N_FUZZ = 100_000

from django.db.backends.postgresql.client import DatabaseClient  # patched callee


# --- the R/I shadow: builtArgs / dbnameToken, transliterated -----------------
def shadow_args(settings_dict, parameters):
    """Reconstruct the leading segment exactly as the unchanged repo code does
    (executable name + the -U/-h/-p option flags), then apply Solution.lean's
    modeled tail order: leading ++ parameters ++ dbnameToken(dbname)."""
    options = settings_dict.get("OPTIONS", {})
    host = settings_dict.get("HOST")
    port = settings_dict.get("PORT")
    dbname = settings_dict.get("NAME")
    user = settings_dict.get("USER")
    service = options.get("service")

    # mapping.md §2: a truthy dbname (incl. the "postgres" default) <-> some s;
    # a falsy dbname (None/"") <-> none.
    if not dbname and not service:
        dbname = "postgres"

    # leading: the unchanged leading segment (executable + connection flags).
    leading = [DatabaseClient.executable_name]
    if user:
        leading += ["-U", user]
    if host:
        leading += ["-h", host]
    if port:
        leading += ["-p", str(port)]

    # dbnameToken(dbname) = [dbname] if dbname else [] (Option.toList).
    dbname_token = [dbname] if dbname else []

    # builtArgs: leading ++ parameters ++ dbnameToken dbname  (the FIX order).
    return list(leading) + list(parameters) + dbname_token


def oracle_args(settings_dict, parameters):
    """patch.diff behaviour: the REAL patched builder; read back the args vec."""
    return DatabaseClient.settings_to_cmd_args_env(settings_dict, parameters)[0]


def fuzz_inputs(n, rng):
    names = [None, "", "dbname", "postgres", "my db", "café"]
    hosts = [None, "", "localhost", "127.0.0.1"]
    ports = [None, "", "5432", 5432]
    users = [None, "", "admin", "post gres"]
    services = [None, "", "svc"]
    param_pool = ["--help", "-c", "select * from t;", "-x", "", "-w", "a b"]

    def make(name, host, port, user, service, params):
        sd = {}
        if name is not None:
            sd["NAME"] = name
        if host is not None:
            sd["HOST"] = host
        if port is not None:
            sd["PORT"] = port
        if user is not None:
            sd["USER"] = user
        if service is not None:
            sd["OPTIONS"] = {"service": service}
        return sd, params

    # boundary cases first (the issue's repro and its neighbours)
    yield make("dbname", None, None, None, None, ["--help"])           # F2P
    yield make("dbname", None, None, None, None, ["-c", "select * from some_table;"])
    yield make("dbname", None, None, None, None, [])
    yield make(None, None, None, None, None, ["--help"])               # no NAME -> postgres
    yield make("", None, None, None, None, ["-c", "x"])                # empty NAME
    yield make(None, None, None, None, "svc", ["--help"])              # service, no dbname
    yield make("db", "h", "5432", "u", None, ["-c", "q"])              # all flags + params

    for _ in range(n):
        k = rng.randint(0, 4)
        params = [rng.choice(param_pool) for _ in range(k)]
        yield make(rng.choice(names), rng.choice(hosts), rng.choice(ports),
                   rng.choice(users), rng.choice(services), params)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for settings_dict, parameters in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_args(settings_dict, parameters)
        oracle = oracle_args(settings_dict, parameters)
        if shadow != oracle:
            disagreements.append((settings_dict, parameters, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for sd, params, sh, orc in disagreements:
            print("  settings=%r parameters=%r shadow=%r oracle=%r"
                  % (sd, params, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildShellArgs agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
