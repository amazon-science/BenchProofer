#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15851 (nagini).

SHADOW: the impl region of model.py `build_argv`, copied verbatim below with
the contract calls (Requires/Ensures/Invariant/Assert) stripped. Every
ToSeq/PSeq expression in the impl region sits inside a stripped contract call,
so no sequence shim is needed at runtime; the executable content is plain
list construction. There are no @Pure helpers and no @ContractOnly callees
(mapping.md section 3: the modelled operation is pure in-process list
construction).

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.backends.postgresql.client.DatabaseClient.settings_to_cmd_args_env`.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2):
  * a command-line argument token is a `str` in the repo and one opaque `int`
    token identity in the model; per test case an interning table assigns each
    distinct string a distinct int (injective), and the shadow's output ints
    are mapped back through the inverse table for comparison;
  * `prefix` is the leading flag segment as the unchanged code above the
    modelled region assembles it: the client program name plus the optional
    user / host / port option pairs, in that fixed order, each guarded by the
    truthiness of its setting (the port token rendered via str());
  * `(has_dbname, dbname)` mirrors the repo's database-name token after its
    defaulting rule: the name from the settings mapping, defaulted to the
    stock name when both the name and the service option are absent/falsey;
    `has_dbname` is that value's truthiness;
  * the env mapping and the 2-tuple wrapper of the real return are outside
    the modelled behaviour (observationally unchanged); only the argument
    vector (element 0 of the return) is compared.

Input domain: the model's preconditions only demand read access to the two
input lists, so every generated case is Requires-satisfying. Generation
covers the full boundary lattice of setting presence/absence (user, host,
port, name, service, password: 2^6 combinations, crossed with several
parameter-list shapes including the empty list) plus randomized fuzz over
token contents (ASCII and non-ASCII, tokens colliding with each other and
with flag literals), integer and string ports (including falsey ones), and
parameter lists of length 0..6.

>= 1e5 Requires-satisfying inputs: boundary lattice + >=100000 fuzz cases.
Pinned fuzz seed: 15851.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 15851
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def build_argv(prefix, parameters, has_dbname, dbname):
    result = []  # type: list
    i = 0
    while i < len(prefix):
        result.append(prefix[i])
        i = i + 1
    j = 0
    while j < len(parameters):
        result.append(parameters[j])
        j = j + 1
    if has_dbname:
        result.append(dbname)
    return result
    # (impl region ends)


# --- bridge: settings mapping -> model inputs (mapping.md section 2) ----------

def model_inputs(real_cls, settings_dict, parameters):
    """Derive the model's four inputs from one oracle input, per mapping.md.

    Returns (prefix_str, parameters_str, has_dbname, dbname_str) where the
    two lists and the name token are still strings; interning to ints happens
    in the driver.
    """
    options = settings_dict.get("OPTIONS", {})
    host = settings_dict.get("HOST")
    port = settings_dict.get("PORT")
    dbname = settings_dict.get("NAME")
    user = settings_dict.get("USER")
    service = options.get("service")
    if not dbname and not service:
        dbname = "postgres"  # the stock default name (unchanged defaulting rule)
    prefix = [real_cls.executable_name]
    if user:
        prefix += ["-U", user]
    if host:
        prefix += ["-h", host]
    if port:
        prefix += ["-p", str(port)]
    return prefix, list(parameters), bool(dbname), dbname


def check_case(real_cls, settings_dict, parameters):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None."""
    prefix_s, params_s, has_dbname, dbname_s = model_inputs(
        real_cls, settings_dict, parameters)

    # injective str -> int interning for this case (token identity bijection)
    table = {}

    def tok(s):
        if s not in table:
            table[s] = len(table)
        return table[s]

    prefix_i = [tok(s) for s in prefix_s]
    params_i = [tok(s) for s in params_s]
    dbname_i = tok(dbname_s) if has_dbname else -1

    shadow_i = build_argv(prefix_i, params_i, has_dbname, dbname_i)
    inverse = {v: k for k, v in table.items()}
    shadow_args = [inverse[t] for t in shadow_i]

    real_args, _env = real_cls.settings_to_cmd_args_env(settings_dict, parameters)
    if shadow_args != real_args:
        return ("DISAGREEMENT\n  settings=%r\n  parameters=%r\n  shadow=%r\n  real=%r"
                % (settings_dict, parameters, shadow_args, real_args))
    return None


# --- input generation ----------------------------------------------------------

BOUNDARY_PARAMS = [
    [],
    ["--help"],
    ["-c", "select 1"],
    ["--quiet", "--no-align", "-t"],
]

FALSY = [None, ""]


def boundary_cases():
    """Full presence/absence lattice for the six settings that reach the
    argument vector or its guards, crossed with parameter shapes."""
    users = ["someuser", None]
    hosts = ["somehost", None]
    ports = ["444", 5432, 0, None]
    names = ["dbname", "", None]
    services = ["default_db", None]
    passwds = ["somepassword", None]
    for user in users:
        for host in hosts:
            for port in ports:
                for name in names:
                    for service in services:
                        for passwd in passwds:
                            sd = {}
                            if user is not None:
                                sd["USER"] = user
                            if host is not None:
                                sd["HOST"] = host
                            if port is not None:
                                sd["PORT"] = port
                            if name is not None:
                                sd["NAME"] = name
                            if passwd is not None:
                                sd["PASSWORD"] = passwd
                            opts = {}
                            if service is not None:
                                opts["service"] = service
                            if opts:
                                sd["OPTIONS"] = opts
                            for params in BOUNDARY_PARAMS:
                                yield sd, params


TOKEN_POOL = [
    "a", "b", "db", "postgres", "-U", "-h", "-p", "--", "-",
    "user name", "host.example", "5432", "0", " ", "\t",
    "unicode-éè", "数据库", "psql",
    "very-long-" + "x" * 200, "'quoted'", '"dq"', "$VAR", ";",
]


def rand_token(rng):
    if rng.random() < 0.5:
        return rng.choice(TOKEN_POOL)
    n = rng.randint(1, 12)
    return "".join(chr(rng.randint(33, 0x2FF)) for _ in range(n))


def fuzz_case(rng):
    sd = {}
    if rng.random() < 0.7:
        v = rand_token(rng) if rng.random() < 0.8 else rng.choice(FALSY)
        if v is not None:
            sd["USER"] = v
    if rng.random() < 0.7:
        v = rand_token(rng) if rng.random() < 0.8 else rng.choice(FALSY)
        if v is not None:
            sd["HOST"] = v
    if rng.random() < 0.7:
        r = rng.random()
        if r < 0.4:
            sd["PORT"] = rng.randint(0, 70000)
        elif r < 0.8:
            sd["PORT"] = str(rng.randint(0, 70000))
        else:
            sd["PORT"] = rng.choice(["", 0])
    if rng.random() < 0.8:
        r = rng.random()
        if r < 0.7:
            sd["NAME"] = rand_token(rng)
        elif r < 0.9:
            sd["NAME"] = ""
        # else: absent
    opts = {}
    if rng.random() < 0.4:
        opts["service"] = rand_token(rng) if rng.random() < 0.8 else ""
    if rng.random() < 0.2:
        opts["passfile"] = rand_token(rng)
    if rng.random() < 0.2:
        opts["sslmode"] = "verify-ca"
    if opts:
        sd["OPTIONS"] = opts
    if rng.random() < 0.3:
        sd["PASSWORD"] = rand_token(rng)
    params = [rand_token(rng) for _ in range(rng.randint(0, 6))]
    return sd, params


def main():
    # REAL patched callee (the modelled function, per mapping.md)
    from django.db.backends.postgresql.client import DatabaseClient

    checked = 0
    for sd, params in boundary_cases():
        err = check_case(DatabaseClient, sd, params)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        sd, params = fuzz_case(rng)
        err = check_case(DatabaseClient, sd, params)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real argument-vector assembly on %d "
          "inputs (boundary lattice + fuzz, seed %d)." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
