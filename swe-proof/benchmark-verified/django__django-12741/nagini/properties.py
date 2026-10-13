# properties.py — PBT falsification battery for django__django-12741.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant that shares the FROZEN spec
# (markers.same_spec) and swaps ONLY the impl region; the runner checks its
# Nagini verify outcome against `expect`. Each AXIOM_TESTS case is a self-
# contained probe run in the instance Docker image against the REAL callee.
#
# Defended surface (from model.py / refinement.md):
#   execute_statement_batch(self, sql_list) pins three load-bearing clauses:
#     (1) self.connection.scoped_alias == self.connection.alias  -- the BUG FIX:
#         the atomic block scopes to the connection's OWN alias, NOT a separately
#         supplied/caller-threaded value (pre-patch wrongly used caller_alias).
#     (2) self.connection.scoped_savepoint == self.connection.supports_rollback
#     (3) ToSeq(self.connection.executed) == ToSeq(sql_list)  -- exactly the
#         supplied batch, in order.
#   READ-ONLY inputs (Acc(..., 1/2)): self.connection.alias,
#   self.connection.supports_rollback, self.connection.caller_alias, and
#   list_pred(sql_list). Any rival that WRITES one of these to satisfy a clause
#   vacuously must be rejected for INSUFFICIENT PERMISSION -> the frame-mutation
#   class (MANDATORY here).
#   No @Pure oracle / answer-key is in the contract: every clause is grounded in
#   the args (alias, supports_rollback, sql_list) directly, so there is NO wrong
#   echo to build -- see 'assessment' (ungrounded-oracle N/A, covered by the
#   honest cheapest-impl positive control instead).
#   axioms == [] (no consumed @ContractOnly axiom). The three deep-model
#   references are A-reference (recorded effects of UNCHANGED callees), validated
#   == the real callee by axiom_check.py / G-AX; the AXIOM_TESTS lane re-runs
#   that real-callee soundness check (drives the real execute_sql_flush).

from pathlib import Path

INSTANCE = "django__django-12741"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The FROZEN gold impl region (everything between # impl-start and # impl-end).
# Every variant is produced by _swap-ing exactly this block, so we only ever
# edit inside the impl region and same_spec is guaranteed.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    self.connection.scoped_alias = self.connection.alias
    self.connection.scoped_savepoint = self.connection.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        Invariant(MustTerminate(len(sql_list) - i + 1))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed"""


def _impl(body):
    """Build a full model.py variant whose impl region is `body` (the text
    between the # impl-start / # impl-end markers)."""
    return _swap(_BASE, _GOLD_IMPL, body)


# === 1. POSITIVE CONTROL (soundness, must verify) ==========================
# Structurally DIFFERENT but CORRECT: the two independent recorder writes are
# REORDERED (savepoint first, then alias), and the loop bound is bound to a
# local `n = len(sql_list)`. The forward `take(i)` invariant (the gold proof
# obligation) is kept VERBATIM so the proof still discharges; only the
# executable shape changes. If a faithful correct impl cannot verify =>
# SPEC-TOO-STRONG.
_POS = """    self.connection.scoped_savepoint = self.connection.supports_rollback
    self.connection.scoped_alias = self.connection.alias
    executed = []  # type: List[int]
    i = 0
    n = len(sql_list)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(n == len(sql_list))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        Invariant(MustTerminate(len(sql_list) - i + 1))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed"""

# === 2. ADMISSIBILITY (must verify) ========================================
# The gold impl plus an Assert that an F2P-shaped fact holds under the
# precondition (the batch length is a well-defined non-negative integer and the
# connection's own alias is readable). A vacuous/contradictory precondition
# would let any Assert pass and the differential witness (G-DIFF) would not
# fail; this confirms the Requires ADMITS a normal in-domain input without
# introducing any proof gap. If it cannot verify => PRECOND-TOO-STRONG.
_ADMISS = """    self.connection.scoped_alias = self.connection.alias
    self.connection.scoped_savepoint = self.connection.supports_rollback
    Assert(len(sql_list) >= 0)
    Assert(self.connection.alias == self.connection.alias)
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        Invariant(MustTerminate(len(sql_list) - i + 1))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed"""

# === 3. FRAME-MUTATION on `alias` (reject; insufficient permission) ========
# The bug-fix clause (1) is scoped_alias == alias. This rival reproduces the
# PRE-PATCH wrong behaviour (scope to the caller-threaded alias) but tries to
# make clause (1) hold ANYWAY by OVERWRITING the connection's own read-only
# `alias` to equal the caller-threaded value. `self.connection.alias` is held
# at Acc(..., 1/2) (read-only) so the write is rejected for INSUFFICIENT
# PERMISSION. refinement: its faithful real patch keeps the pre-patch
# semantics (block scoped to the separately supplied alias) AND cannot rewrite
# the live connection's own `.alias`; the F2P test_execute_sql_flush_statements
# calls execute_sql_flush(sql_list) with NO alias and asserts the flush emptied
# the connection's OWN database -- a scope taken from elsewhere does not, so the
# faithful patch does NOT resolve.
_FRAME_ALIAS = """    self.connection.alias = self.connection.caller_alias
    self.connection.scoped_alias = self.connection.caller_alias
    self.connection.scoped_savepoint = self.connection.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        Invariant(MustTerminate(len(sql_list) - i + 1))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed"""

# === 4. FRAME-MUTATION on `sql_list` (reject; insufficient permission) =====
# Clause (3) is ToSeq(executed) == ToSeq(sql_list). This rival executes a WRONG
# batch (it appends a sentinel statement that was never supplied) and tries to
# make clause (3) hold anyway by MUTATING the read-only input `sql_list` to
# match the wrong executed list (appending the same sentinel). `sql_list` is
# held at Acc(list_pred(sql_list), 1/2) (read-only) so `sql_list.append(...)`
# is rejected for INSUFFICIENT PERMISSION. refinement: the real cursor loop
# `for sql in sql_list: cursor.execute(sql)` runs exactly the supplied
# statements and a caller's list cannot be retro-extended; injecting an unsent
# statement changes which SQL hits the DB, so the faithful patch (which the
# P2P/F2P flush tests exercise with a real statement batch) does NOT resolve.
_FRAME_SQLLIST = """    self.connection.scoped_alias = self.connection.alias
    self.connection.scoped_savepoint = self.connection.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        Invariant(MustTerminate(len(sql_list) - i + 1))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    executed.append(999)
    sql_list.append(999)
    self.connection.executed = executed"""

# === 4b. CONNECTION-REBIND frame attack (reject) ===========================
# The subtlest weakness (flagged by a collaborator): instead of running the
# batch against the helper's OWN connection, REBIND self.connection to a brand-
# new fake Connection whose recorders trivially satisfy clauses (1)-(3). Without
# the frame condition `self.connection is Old(self.connection)`, this VERIFIES
# while doing nothing to the caller's real connection. refinement: no faithful
# real patch swaps the helper's connection for a fresh object — execute_sql_flush
# runs against self.connection, and the F2P/P2P tests observe the REAL
# connection's cursor; a patch that rebound to a throwaway connection would not
# touch the database under test and would NOT resolve.
_REBIND = """    fake = Connection(7, False, 0)
    fake.scoped_alias = fake.alias
    fake.scoped_savepoint = fake.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        Invariant(MustTerminate(len(sql_list) - i + 1))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    fake.executed = executed
    self.connection = fake"""

# === 5. PARTIAL-DOMAIN on the empty batch (reject) =========================
# A rival CORRECT on every non-empty batch but DIVERGENT on the empty-batch
# sub-domain: when sql_list is non-empty it scopes to the connection's own
# alias (clause 1 holds), but on the EMPTY batch it scopes to the caller
# alias. Clause (1) scoped_alias == alias must then fail (caller_alias is not
# provably == alias) on len==0. refinement: a real patch that only scopes
# correctly when there is at least one statement to run still mis-scopes the
# (legal) empty flush; the F2P/axiom_check observations include the empty batch
# `[]`, and the flush of an empty list still opens the atomic block on the
# connection's own DB -- the faithful patch does NOT resolve.
_PARTIAL_EMPTY = """    if len(sql_list) > 0:
        self.connection.scoped_alias = self.connection.alias
    else:
        self.connection.scoped_alias = self.connection.caller_alias
    self.connection.scoped_savepoint = self.connection.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        Invariant(MustTerminate(len(sql_list) - i + 1))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed"""

# === 6. PARTIAL-DOMAIN drop-the-last-statement (reject) ====================
# A rival CORRECT on the scope/savepoint clauses and on the in-order prefix,
# but it stops one short (loop bound len(sql_list) - 1), so the LAST supplied
# statement is never executed. Clause (3) ToSeq(executed) == ToSeq(sql_list)
# fails on any non-empty batch. refinement: silently dropping the final flush
# statement leaves the DB not fully flushed; the F2P
# test_execute_sql_flush_statements asserts the tables are actually empty after
# the call, so the faithful patch does NOT resolve.
_PARTIAL_DROP = """    self.connection.scoped_alias = self.connection.alias
    self.connection.scoped_savepoint = self.connection.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list) - 1:
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        Invariant(MustTerminate(len(sql_list) - i + 1))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed"""

# === 7. SAVEPOINT-FLIP (reject) ============================================
# A rival correct on scope + statements but it opens the block with the WRONG
# savepoint flag (the negation of the connection's declared capability).
# Clause (2) scoped_savepoint == supports_rollback fails. refinement: passing
# savepoint = not features.can_rollback_ddl changes the atomic block's rollback
# behaviour on backends whose DDL-rollback capability differs from the flipped
# value; the recorded-effect (G-AX) and the flush tests exercise the real
# savepoint argument, so the faithful patch does NOT resolve.
_SAVEPOINT_FLIP = """    self.connection.scoped_alias = self.connection.alias
    self.connection.scoped_savepoint = not self.connection.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        Invariant(MustTerminate(len(sql_list) - i + 1))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed"""


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS),
        "rationale": "structurally-different but CORRECT impl (recorder writes "
        "reordered, loop bound bound to a local `n`, forward take(i) invariant "
        "kept verbatim) must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-fshaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": "gold impl plus Asserts of F2P-shaped facts (len>=0; own "
        "alias readable) confirms the Requires admits a normal in-domain input; "
        "else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mut-alias",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_ALIAS),
        "refinement": "faithful real patch keeps pre-patch semantics (block "
        "scoped to a separately-supplied alias) and cannot rewrite the live "
        "connection's own `.alias`; F2P calls execute_sql_flush(sql_list) with "
        "no alias and asserts the connection's OWN DB was emptied -- mis-scoping "
        "does NOT resolve.",
        "rationale": "clause (1) scoped_alias == alias is cheated by WRITING the "
        "read-only `self.connection.alias` (Acc 1/2). Must be REJECTED for "
        "INSUFFICIENT PERMISSION (permission system), not for a value mismatch.",
    },
    {
        "id": "frame-mut-sqllist",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_SQLLIST),
        "refinement": "the real cursor loop runs exactly the supplied "
        "statements; a caller's list cannot be retro-extended, and injecting an "
        "unsent statement changes which SQL hits the DB. The flush F2P/P2P tests "
        "exercise a real batch, so the faithful patch does NOT resolve.",
        "rationale": "clause (3) ToSeq(executed)==ToSeq(sql_list) is cheated by "
        "MUTATING the read-only input `sql_list` (Acc(list_pred,1/2)) to match a "
        "wrong executed list. Must be REJECTED for INSUFFICIENT PERMISSION on "
        "the half-permission list_pred(sql_list).",
    },
    {
        "id": "rebind-connection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_REBIND),
        "refinement": "no faithful real patch swaps the helper's connection for a "
        "fresh throwaway object; execute_sql_flush runs against self.connection and "
        "the F2P/P2P tests observe the REAL connection's cursor. A patch that rebound "
        "self.connection would not touch the DB under test and would NOT resolve.",
        "rationale": "REBIND attack: satisfies clauses (1)-(3) on a brand-new fake "
        "Connection while leaving the caller's real connection untouched. Must be "
        "REJECTED by the frame condition `self.connection is Old(self.connection)`; "
        "if it verified => SPEC-TOO-WEAK (missing connection-identity frame).",
    },
    {
        "id": "partial-domain-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PARTIAL_EMPTY),
        "refinement": "a patch that only scopes correctly when >=1 statement "
        "runs still mis-scopes the legal empty flush; the empty batch `[]` is in "
        "the F2P/axiom_check observations and the empty flush still opens the "
        "block on the connection's own DB -- the faithful patch does NOT resolve.",
        "rationale": "clause (1) scoped_alias == alias fails on the len==0 "
        "sub-domain (scoped to caller_alias, not provably == alias).",
    },
    {
        "id": "partial-domain-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PARTIAL_DROP),
        "refinement": "stopping one statement short leaves the DB not fully "
        "flushed; F2P test_execute_sql_flush_statements asserts the tables are "
        "actually empty after the call, so the faithful patch does NOT resolve.",
        "rationale": "clause (3) ToSeq(executed)==ToSeq(sql_list) fails on any "
        "non-empty batch (the last element is missing).",
    },
    {
        "id": "savepoint-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SAVEPOINT_FLIP),
        "refinement": "passing savepoint = not can_rollback_ddl changes the "
        "atomic block's rollback behaviour; the recorded-effect (G-AX) and the "
        "flush tests exercise the real savepoint argument, so the faithful patch "
        "does NOT resolve.",
        "rationale": "clause (2) scoped_savepoint == supports_rollback fails "
        "(the flag is negated).",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane: there is NO consumed @ContractOnly axiom (meta.axioms == []), but
# the three deep-model references are A-reference recorded effects of UNCHANGED
# callees, validated == the real callee by axiom_check.py / G-AX. This probe
# re-runs that real-callee soundness check IN the instance image: it drives the
# REAL BaseDatabaseOperations.execute_sql_flush with recording stand-ins for the
# unchanged callees and asserts, over boundary + 5000 fuzz observations, that
#   (1) the atomic block is scoped to the connection's OWN alias (never a
#       caller-supplied value),
#   (2) the savepoint flag == features.can_rollback_ddl,
#   (3) exactly the supplied statements run, in order,
# and that the post-patch signature takes the single parameter `sql_list`.
# The probe EXECUTES the real routine (it does not scrape source); it reads
# axiom_check.py on the HOST at load time and embeds its source (the runner
# mounts only the probe script in-container). It opens nothing on disk, so no
# utf-8/codec concern. If Django is unimportable it SKIPs (exit 0) -- the
# post-gold callee is present in the eval image (apply_gold=True).
# ---------------------------------------------------------------------------
_AXIOM_PROBE = (
    "import sys\n"
    "# --- embedded axiom_check.py (read on the HOST at manifest load time;\n"
    "#     the runner mounts only this probe in-container) ---\n"
    + _AXIOM_CHECK_SRC
    + "\n"
    "# axiom_check.py's `main()` returns 0 iff every recorded-effect obligation\n"
    "# holds over all observations (or SKIPs if Django is absent). The trailing\n"
    "# `if __name__ == '__main__': sys.exit(main())` above already runs it when\n"
    "# this probe is executed as a script.\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-recorded-effects-sound",
        "axiom": "scoped_alias/scoped_savepoint/executed (A-reference recorded effects)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_PROBE,
        "rationale": "drives the REAL post-patch execute_sql_flush with recording "
        "stand-ins for the unchanged callees and asserts the three A-reference "
        "recorded effects (scope==own alias; savepoint==can_rollback_ddl; exactly "
        "the supplied statements in order) over boundary + 5000 fuzz inputs, plus "
        "the single-parameter signature. If the real callee disagrees with any "
        "modeled recorded effect => AXIOM-UNSOUND.",
    },
]
