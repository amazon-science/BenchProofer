#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13807 (nagini).

SHADOW  — the impl regions of model.py, copied VERBATIM below with the
          contract calls (Requires/Ensures/Acc) stripped. The model IS
          Python; the code-point lists run unchanged. The @ContractOnly
          runtime callee `delimit_id` calls the REAL repo routine it stands
          for per mapping.md section 3: the backend identifier-delimiting
          method of the active connection's ops object, bridged through the
          str <-> List[int] code-point bijection.

BRIDGE  — mapping.md section 2: identifiers and command text are carried as
          Unicode code-point lists (`ord`/`chr` bijection). The three-
          identifier command's constant fragments are opaque placeholder
          code points in the model; the bridge expands them to the concrete
          constant fragments the real command interleaves (recorded in
          mapping.md section 2) and appends the constant identifier-free
          parameter-placeholder suffix the model omits, then compares the
          expanded shadow text to the real command text with `==`.

ORACLE  — the REAL patched constraint-integrity checker (PYTHONPATH=
          /testbed, gold patch applied by the gate before this script runs):
          DatabaseWrapper.check_constraints of the sqlite3 backend, run on a
          live in-memory database that holds a deliberately-violating row,
          with an execute_wrapper recording every command text the checker
          issues. Per case the recorder captures (i) the per-table
          foreign-key-check command naming the supplied table and (ii) the
          bad-row lookup command naming the primary-key column, the
          referencing column and the table.

Input domain: the modeled preconditions demand only read access to the
identifier lists, so any identifier is Requires-satisfying; the executable
domain excludes interior double quotes (the delimiting routine does not
escape, so such names cannot round-trip through real command text — they
never reach these call sites from a real schema either). Boundary
identifiers cover command-language reserved words (the F2P shape), ordinary
names, names with spaces/dashes/dots/single quotes, non-ASCII, digit-leading
names, and an already-delimited spelling of the supplied table name.

>= 1e5 Requires-satisfying inputs: 50000 cases x 2 modeled command builders
(one single-identifier + one three-identifier check per case), boundary
cases included. Pinned seed: 13807.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the package under test) only.
"""
import random
import sys

SEED = 13807
N_CASES = 50_000

# ---------------------------------------------------------------------------
# Real-callee binding for the @ContractOnly runtime callee (set in main()).
# ---------------------------------------------------------------------------

_QUOTE_NAME = None


def delimit_id(name):
    """The REAL backend identifier-delimiting routine, bridged through the
    code-point bijection (mapping.md section 3)."""
    return [ord(ch) for ch in _QUOTE_NAME("".join(chr(c) for c in name))]


# ---------------------------------------------------------------------------
# model.py impl regions, VERBATIM with contract statement lines
# (Requires/Ensures) stripped.
# ---------------------------------------------------------------------------


def build_single_table_command(table_name):
    quoted = delimit_id(table_name)
    result = []
    result = result + [80, 82, 65, 71, 77, 65, 32,
                       102, 111, 114, 101, 105, 103, 110, 95, 107, 101, 121, 95,
                       99, 104, 101, 99, 107, 40]
    result = result + quoted
    result = result + [41]
    return result


def build_three_id_command(ident_a, ident_b, ident_c):
    a = delimit_id(ident_a)
    b = delimit_id(ident_b)
    c = delimit_id(ident_c)
    result = []
    result = result + [1, 2]
    result = result + a
    result = result + [3]
    result = result + b
    result = result + [4, 5]
    result = result + c
    return result


# ---------------------------------------------------------------------------
# Bridge: code-point lists <-> real command text. The opaque placeholder
# fragments expand to the concrete constant fragments per mapping.md sec. 2.
# ---------------------------------------------------------------------------

_FRAGMENTS = {1: "SELECT", 2: " ", 3: ", ", 4: " FROM", 5: " "}
_THREE_ID_SUFFIX = " WHERE rowid = %s"   # constant identifier-free tail


def expand(codes, with_fragments=False):
    out = []
    for c in codes:
        if with_fragments and c in _FRAGMENTS:
            out.append(_FRAGMENTS[c])
        else:
            out.append(chr(c))
    return "".join(out)


def cp(s):
    return [ord(ch) for ch in s]


# ---------------------------------------------------------------------------
# Identifier generation.
# ---------------------------------------------------------------------------

RESERVED = ["order", "select", "where", "group", "table", "from", "to",
            "index", "values", "check", "primary", "join", "on", "set"]
ORDINARY = ["items", "customers", "a", "T1", "big_table_name_with_parts"]
AWKWARD = ["with space", "dash-ed", "dot.ted", "it's", "1leading", "tablé",
           "MiXeD", "semi;colon", "(paren)", "per%cent", "_under"]

ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
EXTRA = "0123456789_ -.'éü"


def gen_ident(rng):
    kind = rng.random()
    if kind < 0.35:
        return rng.choice(RESERVED)
    if kind < 0.5:
        return rng.choice(AWKWARD)
    if kind < 0.6:
        return rng.choice(ORDINARY)
    n = rng.randint(1, 12)
    s = rng.choice(ALPHA)
    for _ in range(n - 1):
        s += rng.choice(ALPHA + EXTRA)
    return s


def gen_case(rng):
    """Distinct table / parent / pk-column / fk-column identifiers, plus the
    spelling of the table name supplied to the checker (sometimes the
    already-delimited form)."""
    names = []
    seen = set()
    while len(names) < 4:
        s = gen_ident(rng)
        # the engine treats identifiers case-insensitively: dedupe casefolded
        if s.casefold() not in seen:
            seen.add(s.casefold())
            names.append(s)
    table, parent, pk_col, fk_col = names
    supplied = table
    if rng.random() < 0.15:
        supplied = '"%s"' % table
    return table, parent, pk_col, fk_col, supplied


def boundary_cases():
    return [
        ("order", "orderparent", "id", "parent_id", "order"),   # F2P shape
        ("order", "p", "select", "where", "order"),
        ("select", "from", "group", "to", '"select"'),          # pre-delimited
        ("with space", "p2", "col one", "col two", "with space"),
        ("it's", "q", "a", "b", "it's"),
        ("tablé", "p3", "clé", "ref", "tablé"),
        ("1leading", "p4", "2pk", "3fk", "1leading"),
        ("T", "P", "K", "C", '"T"'),
    ]


# ---------------------------------------------------------------------------
# Oracle: the real patched checker on a live in-memory database.
# ---------------------------------------------------------------------------


def run_case(connection, table, parent, pk_col, fk_col, supplied):
    from django.db import IntegrityError
    q = _QUOTE_NAME
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("CREATE TABLE %s (%s INTEGER PRIMARY KEY)"
                       % (q(parent), q("ppk")))
        cursor.execute(
            "CREATE TABLE %s (%s INTEGER PRIMARY KEY, %s INTEGER REFERENCES %s(%s))"
            % (q(table), q(pk_col), q(fk_col), q(parent), q("ppk")))
        cursor.execute("INSERT INTO %s (%s, %s) VALUES (1, 42)"
                       % (q(table), q(pk_col), q(fk_col)))

    recorded = []

    def recorder(execute, sql, params, many, context):
        recorded.append(sql)
        return execute(sql, params, many, context)

    try:
        try:
            with connection.execute_wrapper(recorder):
                connection.check_constraints(table_names=[supplied])
            integrity_flagged = False
        except IntegrityError:
            integrity_flagged = True

        # The three identifiers the checker splices at the lookup site are
        # resolved by UNCHANGED scaffolding (the engine-reported violating
        # table name, the introspected referencing column, the introspected
        # primary-key column). Replay that unchanged resolution to obtain
        # the model's actual inputs — their spelling can differ from the
        # names used at creation.
        with connection.cursor() as cursor:
            violations = cursor.execute(
                "PRAGMA foreign_key_check(%s)" % q(supplied)).fetchall()
            if len(violations) == 1:
                reported_table, _rowid, _ref_table, fk_index = violations[0]
                foreign_key = cursor.execute(
                    "PRAGMA foreign_key_list(%s)" % q(reported_table)
                ).fetchall()[fk_index]
                resolved_fk_col = foreign_key[3]
                resolved_pk_col = connection.introspection.get_primary_key_column(
                    cursor, reported_table)
            else:
                reported_table = None
    finally:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE %s" % q(table))
            cursor.execute("DROP TABLE %s" % q(parent))

    if not integrity_flagged:
        return "oracle did not flag the planted violating row"
    if reported_table is None:
        return "unexpected violation count"

    check_cmds = [s for s in recorded if s.startswith("PRAGMA foreign_key_check(")]
    # the bad-row lookup ends with the constant parameter-placeholder tail;
    # introspection helpers may issue other SELECTs, excluded by the suffix
    lookup_cmds = [s for s in recorded
                   if s.startswith("SELECT ") and s.endswith(_THREE_ID_SUFFIX)]
    if len(check_cmds) != 1 or len(lookup_cmds) != 1:
        return ("unexpected recorded command shape: %d check / %d lookup\n  %r"
                % (len(check_cmds), len(lookup_cmds), recorded))

    # modeled site #1: the command naming the supplied table
    shadow_single = expand(build_single_table_command(cp(supplied)))
    if shadow_single != check_cmds[0]:
        return ("DISAGREEMENT (single-identifier command)\n"
                "  supplied=%r\n  shadow=%r\n  real=%r"
                % (supplied, shadow_single, check_cmds[0]))

    # modeled site #3: the command naming pk column, referencing column, table
    # (identifier values as the checker resolves them: the engine-reported
    # table name and the introspected column names)
    shadow_three = expand(
        build_three_id_command(cp(resolved_pk_col), cp(resolved_fk_col),
                               cp(reported_table)),
        with_fragments=True) + _THREE_ID_SUFFIX
    if shadow_three != lookup_cmds[0]:
        return ("DISAGREEMENT (three-identifier command)\n"
                "  pk_col=%r fk_col=%r table=%r\n  shadow=%r\n  real=%r"
                % (resolved_pk_col, resolved_fk_col, reported_table,
                   shadow_three, lookup_cmds[0]))
    return None


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=[],
        )
        django.setup()
    from django.db import connection

    global _QUOTE_NAME
    _QUOTE_NAME = connection.ops.quote_name

    if not getattr(connection.features, "supports_pragma_foreign_key_check",
                   True):
        import json
        print(json.dumps({"unsupported": "engine lacks the per-table "
                          "foreign-key-check command this bundle models"}))
        return 1

    rng = random.Random(SEED)
    cases = boundary_cases()
    while len(cases) < N_CASES:
        cases.append(gen_case(rng))

    checked = 0
    for table, parent, pk_col, fk_col, supplied in cases:
        err = run_case(connection, table, parent, pk_col, fk_col, supplied)
        if err:
            print("G-CONF FAIL (seed=%d):" % SEED)
            print("  case: table=%r parent=%r pk_col=%r fk_col=%r supplied=%r"
                  % (table, parent, pk_col, fk_col, supplied))
            print(err)
            return 1
        checked += 2   # one single-identifier + one three-identifier check

    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "constraint-integrity checker's command texts on %d builder inputs "
          "(%d cases, seed=%d), 0 disagreements." % (checked, len(cases), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
