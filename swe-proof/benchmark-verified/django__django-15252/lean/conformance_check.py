#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15252.

The bundle models ONE behavior: the head of `MigrationExecutor.migrate`
(`django/db/migrations/executor.py:91-100`), i.e. the decision about whether to
provision the `django_migrations` bookkeeping table (call `ensure_schema()`) and
whether to short-circuit before the unchanged remainder.

Its Lean implementation (`implementation_provisionRecordsTable`) reduces the
function to two observable components — whether provisioning ran
(`provisionedTable`) and which project state is returned (`state`) — as a pure
function of the two inputs the fix branches on: the planned batch `plan`
(`None` / `[]` / non-empty) and whether the table already exists (`has_table()`):

    provisioned = False
    if plan == []:
        if not table_exists:
            return (False, ("projectState", False))   # short-circuit, no applied
        # table present: fall through, nothing provisioned
    else:
        provisioned = True
    return (provisioned, ("continuationResult", plan_shape))

This script transliterates that R/I impl into Python (`shadow_migrate`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `migrate`'s head:

    # patch.diff
    if plan == []:
        if not self.recorder.has_table():
            return self._create_project_state(with_applied_migrations=False)
    else:
        self.recorder.ensure_schema()
    ... (unchanged remainder) ...
    return state

We do NOT stand up Django/the ORM (heavy, and the modeled value is a pure
control-flow decision). Instead we reproduce the patched head with light
stand-ins: `ensure_schema()` records a call (observed as `provisioned`),
`has_table()` returns the supplied boolean, `_create_project_state(False)` is the
("projectState", False) sentinel, and the unchanged remainder is the
("continuationResult", plan_shape) sentinel. The crucial Python distinction
`None == []` is False but `[] == []` is True is reproduced exactly (only an
explicit empty list takes the new branch).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 15252 (also recorded in
mapping.md).
"""
import sys

SEED = 15252
N = 120_000


def plan_shape(plan):
    """The only thing observed about a non-None plan: empty vs non-empty, with
    the element identities carried through (mirrors `some plannedOps`)."""
    if plan is None:
        return ("none",)
    return ("some", tuple(plan))


# --- ORACLE: the post-patch migrate() head, faithful in-process replica -------
# Returns (provisioned, state) where state is a sentinel for the returned
# ProjectState. `ensure_schema` provisions (records the call); `has_table`
# returns table_exists; `_create_project_state(False)` is the short-circuit.
def oracle_migrate(plan, table_exists):
    provisioned = False

    def ensure_schema():
        nonlocal provisioned
        provisioned = True

    def has_table():
        return table_exists

    # --- the patched head (executor.py:98-100) ---
    if plan == []:                       # explicit empty list only (None != [])
        if not has_table():
            return (provisioned, ("projectState", False))   # _create_project_state(False)
    else:
        ensure_schema()
    # --- unchanged remainder (:102-134) collapses to its state sentinel ---
    return (provisioned, ("continuationResult", plan_shape(plan)))


# --- shadow of implementation_provisionRecordsTable (the R/I leg) -------------
# Mirrors Solution.lean exactly.
def shadow_migrate(plan, table_exists):
    provisioned = False
    if plan == []:                       # plannedOps = some []
        if not table_exists:
            return (False, ("projectState", False))
        # table present: fall through
    else:
        provisioned = True
    return (provisioned, ("continuationResult", plan_shape(plan)))


def disagree(plan, table_exists):
    got = oracle_migrate(plan, table_exists)
    want = shadow_migrate(plan, table_exists)
    if got != want:
        return ((plan, table_exists), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked cases covering plan ∈ {None, [], non-empty} × has_table."""
    return [
        # THE fix: explicit empty plan, table absent -> skip + short-circuit
        ([], False),
        # explicit empty plan, table present -> skip provisioning, fall through
        ([], True),
        # plan is None (computed later) -> provision regardless of table
        (None, False),
        (None, True),
        # non-empty plan -> provision regardless of table
        ([1], False),
        ([1], True),
        ([1, 2, 3], False),
        ([1, 2, 3], True),
        # single-op non-empty plan
        ([42], False),
    ]


def main() -> int:
    checked = 0

    for plan, te in _enumerate_edge():
        d = disagree(plan, te)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        kind = next(rnd) % 3          # 0 -> None, 1 -> [], 2 -> non-empty
        if kind == 0:
            plan = None
        elif kind == 1:
            plan = []
        else:
            length = 1 + (next(rnd) % 5)      # 1..5 ops
            plan = [next(rnd) % 100 for _ in range(length)]
        table_exists = (next(rnd) % 2) == 0
        d = disagree(plan, table_exists)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
