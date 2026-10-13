# properties.py — G-PBT falsification battery for django__django-12741 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   executeFlush(connectionAlias, suppliedUsing, canRollbackDdl, sqlList) : the
#   observable triple a data-clearing routine determines when it opens ONE
#   transaction and runs a list of statements through it. The single postcondition
#   `problem_spec_executeFlush` pins THREE independent top-level clauses over four
#   input binders:
#     (1) result.database  = connectionAlias  — the BUG FIX: the transaction binds
#         to the connection's OWN identifier, NEVER to the separately-available
#         identifier `suppliedUsing` (pre-patch it bound to the supplied value);
#     (2) result.savepoint = canRollbackDdl   — the savepoint flag follows the
#         backend's rollback-capability flag;
#     (3) result.executed  = sqlList          — exactly the supplied statements, in
#         the given order.
#   All three legs are total transparent functions of the inputs (String / Bool /
#   List String — no opaque callee, no answer-key oracle), so `decide` computes the
#   spec at any literal input and the witnesses need no conditioning on the carrier.
#
# BINDER / CLAUSE COVERAGE (what the reject lane must exercise):
#   * clause (1) is attacked by `scope-supplied` (binds to suppliedUsing) and
#     `scope-empty-subdomain` (mis-binds only on the empty batch). Both hold
#     connectionAlias ≠ suppliedUsing so the wrong bind is observable — a binder
#     held equal on every witness is one a suppliedUsing-echoing rival would slip
#     past.
#   * clause (2) is attacked by `savepoint-flip` (negates canRollbackDdl); the flag
#     is probed at BOTH truth values across the witness set (true here, false in the
#     executed-* / drop-last witnesses) so a rival keying on one value is caught.
#   * clause (3) is attacked three ways — `executed-empty` (runs nothing),
#     `executed-reversed` (right multiset, wrong order), `drop-last` (drops the final
#     statement) — over sqlList lengths 1 and 2.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submitted payload):
#   * FRAME-MUTATION (nagini's `_FRAME_ALIAS`, `_FRAME_SQLLIST`) — the rivals wrote
#     into a read-only fractional-permission input to satisfy a clause vacuously.
#     Lean is referentially transparent: there is no aliasing and no permission
#     system, so "store into a read-only input" is not expressible. VACUOUS class.
#   * CONNECTION-REBIND (nagini's `_REBIND`) — swap `self.connection` for a fresh
#     object so the recorders satisfy the clauses on a throwaway. There is no mutable
#     receiver here; the modeled value is a pure function of four value inputs, so
#     there is no identity to rebind. VACUOUS class.
#   * DIVERGENCE / non-termination — genuinely VACUOUS on lean: `implementation_*` is
#     a total Lean `def`, so a diverging implementation cannot be written at all.
#   * AXIOM_TESTS — the axiom lane is G-AX's job; this gate ignores them. The routine
#     is modeled DEEPLY (an order-preserving accumulation over sqlList), so there is
#     no consumed @ContractOnly axiom anyway.
from pathlib import Path

INSTANCE = "django__django-12741"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors (each lies ENTIRELY inside the impl region and is unique) ----------
_A_DATABASE = "  let database := connectionAlias\n"
_A_SAVEPOINT = "  let savepoint := canRollbackDdl\n"
_A_LOOP = "    executed := executed ++ [sql]"
_A_RETURN = "executed := executed }"
for _a in (_A_DATABASE, _A_SAVEPOINT, _A_LOOP, _A_RETURN):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"

# The full frozen impl body + proof body — used by the direct-return positive, which
# replaces the loop with a closed-form record and reproves the identical obligation.
_FULL_IMPL = (
    "def implementation_executeFlush\n"
    "    (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)\n"
    "    (sqlList : List String) : FlushExecution := Id.run do\n"
    "  let database := connectionAlias\n"
    "  let savepoint := canRollbackDdl\n"
    "  let mut executed : List String := []\n"
    "  for sql in sqlList do\n"
    "    executed := executed ++ [sql]\n"
    "  return { database := database, savepoint := savepoint, executed := executed }"
)
assert _BASE.count(_FULL_IMPL) == 1, "full impl anchor drifted"

_FROZEN_PROOF = (
    "  intro connectionAlias suppliedUsing canRollbackDdl sqlList\n"
    "  refine ⟨rfl, rfl, ?_⟩\n"
    "  show (Id.run (forIn sqlList []\n"
    "    (fun sql r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [sql])) : Id _)))) = sqlList\n"
    "  rw [executeFlush_forIn]\n"
    "  simp"
)
assert _BASE.count(_FROZEN_PROOF) == 1, "frozen proof anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-reorder-lets: structurally-different but behaviourally identical impl. The two
# INDEPENDENT recorder bindings (database, savepoint) are computed in the opposite
# order, keeping the loop shape and the returned record otherwise unchanged, so the
# output equals the frozen impl's on every input. The `theorem correct_executeFlush`
# statement is byte-identical and the FROZEN proof body still closes (reordering two
# independent `let`s is definitionally transparent) — a faithful restructure with no
# reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE,
    _A_DATABASE + _A_SAVEPOINT,
    _A_SAVEPOINT + _A_DATABASE,
)

# pos-direct-closed-form: the cheapest HONEST impl. All three postcondition legs are
# grounded directly in the arguments (database=connectionAlias, savepoint=
# canRollbackDdl, executed=sqlList), so returning the closed-form record is a fully
# grounded correct implementation, not an ungrounded oracle echo (a wrong constant
# fails the postcondition — see the executed-empty reject). The loop and its helper
# lemma are gone, so the proof collapses to three `rfl`s. MUST verify; else
# SPEC-TOO-STRONG.
# admiss-f2p-shaped: the ADMISSIBILITY lane, ported. On a total carrier the frozen
# obligation carries no precondition hypothesis, so PRECOND-TOO-STRONG arrives in a
# different shape: the obligation being UNSATISFIABLE at exactly an F2P-shaped input.
# This case discharges the obligation at that concrete point BY EVALUATION (`decide`
# over the three transparent legs), as a `have` in the proof region, and only then
# closes the byte-identical frozen obligation verbatim. The impl region is untouched
# and the frozen proof body is kept in full, so nothing is weakened: the case adds an
# obligation rather than removing one. If the spec were over-constrained at the
# F2P-shaped point — a savepoint flag no backend could present, a batch shape the
# postcondition could not admit — `decide` could not close the `have` and this case
# would FAIL. The point is chosen to be F2P-shaped: a real multi-statement batch, a
# backend that CAN roll back structural changes, and the two identifiers held DISTINCT
# (the F2P supplies no external identifier at all, so the routine must not consult
# one).
_ADMISS_HAVE = (
    "  have _hF2PShaped :\n"
    "      problem_spec_executeFlush \"default\" \"elsewhere\" true [\"stmt_a\", \"stmt_b\"]\n"
    "        (implementation_executeFlush \"default\" \"elsewhere\" true"
    " [\"stmt_a\", \"stmt_b\"]) := by\n"
    "    unfold problem_spec_executeFlush implementation_executeFlush\n"
    "    decide\n"
)
_ADMISS = _swap(_BASE, _FROZEN_PROOF, _ADMISS_HAVE + _FROZEN_PROOF)

_POS_DIRECT = _swap(
    _swap(
        _BASE,
        _FULL_IMPL,
        "def implementation_executeFlush\n"
        "    (connectionAlias suppliedUsing : String) (canRollbackDdl : Bool)\n"
        "    (sqlList : List String) : FlushExecution :=\n"
        "  { database := connectionAlias, savepoint := canRollbackDdl, executed := sqlList }",
    ),
    _FROZEN_PROOF,
    "  intro connectionAlias suppliedUsing canRollbackDdl sqlList\n"
    "  exact ⟨rfl, rfl, rfl⟩",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in place
# (it will not close for the reshaped impl, but the gate reads the witness — checked
# in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# scope-supplied: reproduces the PRE-PATCH behaviour — binds the transaction to the
# separately-available identifier `suppliedUsing` instead of the connection's own
# alias. Attacks clause (1).
_RIV_SCOPE_SUPPLIED = _swap(_BASE, _A_DATABASE, "  let database := suppliedUsing\n")

# scope-empty-subdomain: correct on every NON-empty batch but mis-binds to
# `suppliedUsing` on the empty batch — a partial-domain rival against clause (1).
_RIV_SCOPE_EMPTY = _swap(
    _BASE, _A_DATABASE,
    "  let database := if sqlList.isEmpty then suppliedUsing else connectionAlias\n",
)

# savepoint-flip: opens the transaction with the NEGATION of the backend's declared
# rollback capability. Attacks clause (2).
_RIV_SAVEPOINT = _swap(_BASE, _A_SAVEPOINT, "  let savepoint := !canRollbackDdl\n")

# savepoint-empty-subdomain: the NEAR-MISS of savepoint-flip. Reports the backend's
# rollback capability faithfully whenever at least one statement runs, but forces the
# flag off on the empty batch — so it agrees with the frozen impl on every input
# savepoint-flip discriminates at, and diverges only on the empty-batch sub-domain.
# Clause (2)'s sub-domain analogue of scope-empty-subdomain.
_RIV_SAVEPOINT_EMPTY = _swap(
    _BASE, _A_SAVEPOINT,
    "  let savepoint := canRollbackDdl && !sqlList.isEmpty\n",
)

# executed-empty: runs NOTHING through the transaction — the accumulator is never
# extended, so no supplied statement is executed. Attacks clause (3).
_RIV_EXEC_EMPTY = _swap(_BASE, _A_LOOP, "    executed := executed")

# executed-reversed: runs exactly the supplied statements but in REVERSE order (each
# is prepended, not appended). Right multiset, wrong order. Attacks clause (3).
_RIV_EXEC_REVERSED = _swap(_BASE, _A_LOOP, "    executed := [sql] ++ executed")

# drop-last: runs the in-order prefix but silently drops the FINAL statement. Attacks
# clause (3) on any non-empty batch.
_RIV_DROP_LAST = _swap(_BASE, _A_RETURN, "executed := executed.dropLast }")


def _wit(alias, using, roll, sqls, note):
    """A refutation witness: `¬ problem_spec_executeFlush …  (implementation … )` at a
    concrete literal input, closed by `decide`. Elaborates against a rival that
    diverges from the spec there, and fails on gold (which satisfies the spec at every
    input). No binders on the head, so no consistency probe is needed."""
    args = f'{alias} {using} {roll} {sqls}'
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_executeFlush {args}\n"
        f"    (implementation_executeFlush {args}) := by\n"
        f"  unfold problem_spec_executeFlush implementation_executeFlush\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder-lets",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the two independent recorder "
            "bindings (database, savepoint) are computed in the opposite order, "
            "keeping the loop and returned record otherwise unchanged, so the output "
            "equals the frozen impl's on every input. The `theorem correct_executeFlush` "
            "statement is byte-identical and the FROZEN proof body still closes "
            "(reordering two independent `let`s is definitionally transparent) — no "
            "reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG "
            "(postcondition over-fit to one syntactic impl shape)."
        ),
    },
    {
        "id": "pos-direct-closed-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the cheapest HONEST impl: all three postcondition legs are grounded "
            "directly in the arguments, so returning the closed-form record "
            "{database := connectionAlias, savepoint := canRollbackDdl, executed := "
            "sqlList} is a fully-grounded correct implementation (not an ungrounded "
            "echo — a wrong constant fails the postcondition, see executed-empty). The "
            "loop and helper lemma are gone, so the reproof collapses to three `rfl`s "
            "on the byte-identical obligation. MUST verify; else SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "ADMISSIBILITY on a total carrier: the frozen obligation has no "
            "precondition hypothesis, so PRECOND-TOO-STRONG cannot arrive as a "
            "rejected Requires — it arrives as the obligation being UNSATISFIABLE at "
            "an F2P-shaped input. This case discharges the obligation at that "
            "concrete point BY EVALUATION (`decide` over the three transparent legs) "
            "as a `have`, then closes the byte-identical frozen obligation verbatim "
            "with the frozen proof body; the impl region is untouched, so the case "
            "ADDS an obligation rather than weakening one. The point is F2P-shaped: a "
            "real multi-statement batch, a backend that CAN roll back structural "
            "changes, and the two identifiers held DISTINCT (the F2P supplies no "
            "external identifier, so the routine must not consult one). If the three "
            "clauses were jointly unsatisfiable there — a savepoint flag the spec "
            "could not present, an executed-list shape it could not admit — `decide` "
            "would fail and so would this case. If it FAILS => PRECOND-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "scope-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SCOPE_SUPPLIED,
        "refinement": (
            "binding the transaction to the separately-available identifier instead of "
            "the connection's own alias is exactly the PRE-PATCH behaviour. The F2P "
            "invokes the routine with NO externally-supplied identifier and asserts the "
            "connection's OWN database was flushed; a transaction scoped to some other "
            "identifier opens against the wrong database and the flush does not land, so "
            "the faithful real patch does NOT resolve. A verifying rival is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (1) result.database = connectionAlias. Attacks the "
            "bug-fix clause directly. Witness holds connectionAlias ≠ suppliedUsing so "
            "the wrong bind is observable — varies BOTH the connectionAlias and "
            "suppliedUsing binders. If it VERIFIES => SPEC-TOO-WEAK (spec would tolerate "
            "the supplied-identifier echo)."
        ),
        "witness": _wit('"db_a"', '"db_other"', "true", '["s0"]',
                        "distinct identifiers: gold binds to the own alias, rival binds "
                        "to the supplied one"),
    },
    {
        "id": "scope-empty-subdomain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SCOPE_EMPTY,
        "refinement": (
            "a patch that binds correctly only when at least one statement runs still "
            "mis-binds the (legal) empty flush; the empty batch is an in-domain input "
            "and the empty flush still opens the transaction against the connection's "
            "own database. The faithful real patch does NOT resolve on the empty-batch "
            "sub-domain."
        ),
        "rationale": (
            "REJECTED by clause (1) result.database = connectionAlias on the empty-batch "
            "sub-domain (bound to suppliedUsing there). Witness probes sqlList = [] with "
            "connectionAlias ≠ suppliedUsing — a distinct input point from scope-supplied "
            "(NON-empty batch), so the two are not near-misses sharing a point. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit('"db_e"', '"db_elsewhere"', "false", "[]",
                        "empty batch: gold still binds to the own alias, rival mis-binds "
                        "to the supplied one"),
    },
    {
        "id": "savepoint-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SAVEPOINT,
        "refinement": (
            "opening the transaction with the negation of the backend's rollback "
            "capability changes the transaction's rollback behaviour on backends whose "
            "capability differs from the flipped value; the flush tests exercise the "
            "real savepoint flag, so the faithful real patch does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2) result.savepoint = canRollbackDdl (the flag is "
            "negated). Witness sets canRollbackDdl = true so gold yields true and the "
            "rival false; the flag is probed at false in other witnesses, so both truth "
            "values are covered. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit('"db_s"', '"db_s"', "true", '["s1"]',
                        "capability true: gold opens with savepoint true, rival negates "
                        "it to false"),
    },
    {
        "id": "savepoint-empty-subdomain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SAVEPOINT_EMPTY,
        "refinement": (
            "a routine that reports the backend's rollback capability faithfully only "
            "when at least one statement runs still opens the (legal) empty flush with "
            "the wrong savepoint behaviour; the empty batch is an in-domain input and "
            "the empty flush still opens a transaction, whose rollback behaviour must "
            "follow the backend's declared capability there too. The faithful real "
            "patch does NOT resolve on the empty-batch sub-domain."
        ),
        "rationale": (
            "REJECTED by clause (2) result.savepoint = canRollbackDdl on the "
            "empty-batch sub-domain. This is the NEAR-MISS of savepoint-flip: it "
            "agrees with the frozen impl at every input savepoint-flip discriminates "
            "at (any non-empty batch) and diverges only where sqlList = [], so a rival "
            "that keyed clause (2) on batch emptiness would slip past a battery "
            "carrying only the total flip. Clause (2)'s analogue of "
            "scope-empty-subdomain, which supplies the same sub-domain probe for "
            "clause (1). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit('"db_p"', '"db_p"', "true", "[]",
                        "capability true on the EMPTY batch: gold still opens with "
                        "savepoint true, rival forces it off"),
    },
    {
        "id": "executed-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EXEC_EMPTY,
        "refinement": (
            "running nothing through the transaction leaves the database not flushed at "
            "all; the F2P asserts the tables are actually empty after the call, so the "
            "faithful real patch does NOT resolve. Also shows the postcondition is not "
            "satisfiable by an empty-result echo."
        ),
        "rationale": (
            "REJECTED by clause (3) result.executed = sqlList (executed is empty on a "
            "non-empty batch). Witness is a singleton batch with canRollbackDdl = false "
            "(varying the flag from savepoint-flip's true). If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit('"db_x"', '"db_x"', "false", '["s2"]',
                        "singleton batch: gold runs the statement, rival runs nothing"),
    },
    {
        "id": "executed-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EXEC_REVERSED,
        "refinement": (
            "running the supplied statements in reverse order can change the observable "
            "effect: flush statements are order-sensitive (dependency/foreign-key "
            "ordering), so reordering them can break the flush. The faithful real patch "
            "does NOT resolve; it re-executes the same batch in the wrong order."
        ),
        "rationale": (
            "REJECTED by clause (3) result.executed = sqlList — right multiset, WRONG "
            "order. Witness varies the sqlList binder to a length-2 batch with distinct "
            "elements (order-observable), the ordering probe no other witness makes. If "
            "it VERIFIES => SPEC-TOO-WEAK (spec would pin only the multiset)."
        ),
        "witness": _wit('"db_r"', '"db_r"', "true", '["s3", "s4"]',
                        "two distinct statements: gold preserves order, rival reverses "
                        "them"),
    },
    {
        "id": "drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_LAST,
        "refinement": (
            "stopping one statement short leaves the database not fully flushed; the "
            "F2P asserts the tables are actually empty after the call, so the faithful "
            "real patch does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (3) result.executed = sqlList (the final statement is "
            "missing) on any non-empty batch. Witness varies the sqlList binder to a "
            "length-2 batch with canRollbackDdl = false — a distinct input point from "
            "executed-reversed. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit('"db_d"', '"db_d"', "false", '["s5", "s6"]',
                        "length-2 batch: gold runs both, rival drops the last"),
    },
]


# No @ContractOnly axioms and no opaque callees: the transaction bind, the savepoint
# flag, and the statement run are modeled DEEPLY over the transparent String / Bool /
# List String carrier, so the axiom lane is vacuous here and belongs to G-AX
# regardless.
AXIOM_TESTS = []
