"""PBT falsification battery for django__django-12965.

NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TESTS entry is a full model.py variant built by region-surgery — we edit
ONLY text inside the two `# impl-start`/`# impl-end` regions, so the frozen spec
(axioms/pure/pre/post-conditions/signatures) is byte-identical and `same_spec`
holds for every case. The variant is then checked by the real Nagini verifier:
expect="verify" passes iff it verifies; expect="reject" passes iff it does NOT.

Defended surface (from model.py / refinement.md / mapping.md):

  references_single_table(query) models the CHANGED predicate
  SQLDeleteCompiler.single_alias. Its impl is the FIX:
      query.primary_present = True            # = self.query.get_initial_alias()
      return active_tables(...) == 1          # = sum(refcount>0)==1
  Load-bearing postconditions:
    (P1) query.extra_active == Old(query.extra_active)   # frame: extra preserved
    (P2) query.primary_present is True                   # the FIX is forced
    (P3) Result() == (active_tables(primary_present, extra_active) == 1)
    (P4) Result() == (query.extra_active == 0)            # the discriminator

  delete_uses_subquery(query) models the UNCHANGED caller as_sql:
      if references_single_table(query): return False     # direct, no subquery
      return True                                          # pk IN (SELECT ...)
  Load-bearing postconditions:
    (Q1) query.extra_active == Old(query.extra_active)
    (Q2) Result() == (query.extra_active != 0)
    (Q3) Implies(Old(query.extra_active) == 0, Result() is False)  # the F2P pin

  active_tables is a @Pure helper FULLY UNFOLDED to a function of the args
  (Result() == (1 if primary_present else 0) + extra_active); it is GROUNDED,
  not an opaque answer-key oracle — there is no wrong value to echo (see the
  ungrounded-oracle note in 'assessment').

  Permission note: both functions hold FULL permission on query (no Acc(.,1/2)),
  and references_single_table legitimately WRITES query.primary_present. The
  read-only quantity is extra_active, frozen by the frame clauses P1/Q1; the
  frame-mutation attack here writes extra_active to satisfy P4/Q2 vacuously and
  must be rejected by the frame clause (not by a permission failure).
"""
from pathlib import Path

INSTANCE = "django__django-12965"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the two impl regions exactly as they appear in model.py ----------------
_RST_IMPL = (
    "    # impl-start\n"
    "    query.primary_present = True\n"
    "    return active_tables(query.primary_present, query.extra_active) == 1\n"
    "    # impl-end"
)
_DUS_IMPL = (
    "    # impl-start\n"
    "    if references_single_table(query):\n"
    "        return False\n"
    "    return True\n"
    "    # impl-end"
)


def _rst(body: str) -> str:
    """model.py with references_single_table's impl region body replaced."""
    return _swap(_BASE, _RST_IMPL,
                 "    # impl-start\n" + body + "\n    # impl-end")


def _dus(body: str) -> str:
    """model.py with delete_uses_subquery's impl region body replaced."""
    return _swap(_BASE, _DUS_IMPL,
                 "    # impl-start\n" + body + "\n    # impl-end")


SPEC_TESTS = [
    # ---------------------------------------------------------------- POSITIVE
    {
        "id": "pos-control-rst-direct-discriminator",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT impl of the predicate: still performs
        # the fix (primary_present := True) but computes the result from the
        # discriminator extra_active==0 directly instead of via active_tables.
        # Equivalent after the write (P3 == P4 once primary_present is True),
        # keeps every gold proof obligation, must verify (else SPEC-TOO-STRONG).
        "module": _rst(
            "    query.primary_present = True\n"
            "    return query.extra_active == 0"
        ),
        "rationale": "a correct but structurally-different predicate impl "
                     "(result via extra_active==0 instead of active_tables==1, "
                     "fix still applied) must verify; P3/P4 coincide once "
                     "primary_present is True. If it fails => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-dus-not-predicate",
        "kind": "soundness",
        "expect": "verify",
        # Branch-reshape of the caller: `return not references_single_table(query)`
        # is the same value with the if/return collapsed. Keeps the predicate
        # call (so its precondition is established at the call site). Must verify.
        "module": _dus(
            "    return not references_single_table(query)"
        ),
        "rationale": "the caller computed by negating the predicate (branch "
                     "reshape) is behaviourally identical and must verify; "
                     "else SPEC-TOO-STRONG on delete_uses_subquery.",
    },
    # ----------------------------------------------------------- ADMISSIBILITY
    {
        "id": "admiss-caller-establishes-predicate-precond",
        "kind": "admissibility",
        "expect": "verify",
        # The gold caller invokes references_single_table on its own query.
        # To verify, Nagini must establish the predicate's Requires (Acc on both
        # fields + extra_active >= 0) at the call site from delete_uses_subquery's
        # own Requires — i.e. the precondition ADMITS a normal F2P-shaped call.
        # This is the gold delete_uses_subquery impl verbatim; if it cannot
        # establish the callee precondition => PRECOND-TOO-STRONG.
        "module": _dus(
            "    if references_single_table(query):\n"
            "        return False\n"
            "    return True"
        ),
        "rationale": "delete_uses_subquery establishes references_single_table's "
                     "Requires at the call site from its own precondition; the "
                     "F2P-shaped (whole-table) input is admitted. Else "
                     "PRECOND-TOO-STRONG.",
    },
    # -------------------------------------------------------- FRAME MUTATION
    {
        "id": "frame-mut-write-extra-active",
        "kind": "uniqueness",
        "expect": "reject",
        # WRITE the framed read-only quantity extra_active to 0 so that the
        # discriminator P4 (Result()==(extra_active==0)) is satisfied vacuously
        # by always returning True. Must be REJECTED by the frame clause
        # P1 (query.extra_active == Old(query.extra_active)) — extra_active was
        # mutated.
        "module": _rst(
            "    query.primary_present = True\n"
            "    query.extra_active = 0\n"
            "    return True"
        ),
        "refinement": "the faithful real patch — overwriting alias_refcount so "
                      "the active-table count is forced to 0 before reading it — "
                      "would report single_alias=True for a multi-table delete "
                      "(extra joins clobbered), emitting a direct DELETE that "
                      "drops the join filter and deletes the wrong rows; it would "
                      "FAIL the multi-table PASS_TO_PASS delete tests, so it does "
                      "NOT resolve.",
        "rationale": "rejected by P1 (extra_active == Old(extra_active)): the "
                     "frame clause freezes extra_active, so writing it to satisfy "
                     "P4 is caught. This is the frame-mutation probe (the framed "
                     "read-only quantity, full permission held).",
    },
    {
        "id": "frame-mut-dus-write-extra-active",
        "kind": "uniqueness",
        "expect": "reject",
        # Same frame attack at the caller: zero extra_active then always emit the
        # direct form, vacuously satisfying Q2/Q3. Rejected by Q1
        # (extra_active == Old(extra_active)).
        "module": _dus(
            "    query.extra_active = 0\n"
            "    return False"
        ),
        "refinement": "a real as_sql that mutated the query's alias bookkeeping "
                      "to 0 and always emitted the direct single-table DELETE "
                      "would skip the subquery even for genuine multi-table "
                      "deletes, deleting unfiltered rows and failing the "
                      "multi-table PASS_TO_PASS tests; it does NOT resolve.",
        "rationale": "rejected by Q1 (extra_active == Old(extra_active)) in "
                     "delete_uses_subquery's postcondition — the framed quantity "
                     "is overwritten.",
    },
    # --------------------------------------------------------- PARTIAL DOMAIN
    {
        "id": "partial-domain-rst-le-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on the whole-table case (extra_active==0 -> True) and on
        # extra_active>=2 (-> False), but WRONG at extra_active==1 (returns True
        # where the spec wants False). Drops only the boundary sub-domain.
        "module": _rst(
            "    query.primary_present = True\n"
            "    return query.extra_active <= 1"
        ),
        "refinement": "a real single_alias returning True for exactly-two active "
                      "tables (one extra join) would emit a direct DELETE for a "
                      "single-related-join delete, dropping the join condition and "
                      "deleting wrong rows — failing the multi-table fast-delete "
                      "PASS_TO_PASS tests; it does NOT resolve.",
        "rationale": "rejected by P4 (Result()==(extra_active==0)): at "
                     "extra_active==1 the rival returns True but the spec demands "
                     "False. Partial-domain divergence at the boundary.",
    },
    {
        "id": "partial-domain-dus-direct-on-extra-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Caller diverges only when extra_active==1: emits the direct form there
        # too (should be subquery). Correct for whole-table (0) and many-table
        # (>=2). Rejected by Q2 at extra_active==1.
        "module": _dus(
            "    if query.extra_active <= 1:\n"
            "        return False\n"
            "    return True"
        ),
        "refinement": "a real as_sql that took the direct branch for a "
                      "single-extra-join delete would omit the pk IN (SELECT ...) "
                      "filter and delete unfiltered rows, failing the multi-table "
                      "PASS_TO_PASS delete tests; it does NOT resolve.",
        "rationale": "rejected by Q2 (Result()==(extra_active!=0)): at "
                     "extra_active==1 the rival returns False but the spec demands "
                     "True. Partial-domain divergence at the boundary.",
    },
    # ----------------------------------------------- DROP-THE-FIX (prepatch bug)
    {
        "id": "drop-fix-no-primary-present",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-PATCH behaviour: read the count WITHOUT first ensuring the base
        # table is accounted for (drop query.primary_present = True). For the
        # whole-table case (primary_present entering False, extra_active==0) this
        # returns active_tables(False,0)==1 -> 0==1 -> False, violating P2
        # (primary_present is True) and P4. This is exactly the reported bug.
        "module": _rst(
            "    return active_tables(query.primary_present, query.extra_active) == 1"
        ),
        "refinement": "this IS the regression in the issue: without "
                      "get_initial_alias() the base table is unaccounted at read "
                      "time, single_alias is False for a whole-table delete, and "
                      "as_sql emits DELETE ... WHERE id IN (SELECT ...). It FAILS "
                      "F2P test_fast_delete_all (asserts no SELECT); does NOT resolve.",
        "rationale": "rejected by P2 (query.primary_present is True) — and "
                     "equivalently P4 — because the fix step is dropped. Same "
                     "failure model_prepatch.py exhibits (G-DIFF).",
    },
    # ------------------------------------------------ CONTROL-FLOW / INVERSION
    {
        "id": "always-subquery",
        "kind": "uniqueness",
        "expect": "reject",
        # Caller always emits the subquery form (return True). Correct for the
        # multi-table case but wrong for whole-table — the exact regression.
        # Rejected by Q3 (Old(extra_active)==0 -> Result() is False).
        "module": _dus(
            "    return True"
        ),
        "refinement": "always emitting pk IN (SELECT ...) is precisely the Django "
                      "3.1 regression the issue reports; for a whole-table delete "
                      "it produces the slow self-referential subquery and FAILS "
                      "F2P test_fast_delete_all (assertNotIn SELECT); does NOT resolve.",
        "rationale": "rejected by Q3 (Implies(Old(extra_active)==0, Result() is "
                     "False)) and Q2 — for the whole-table case the rival returns "
                     "True where the spec demands False.",
    },
    {
        "id": "always-direct",
        "kind": "uniqueness",
        "expect": "reject",
        # Caller always emits the direct form (return False). Correct for
        # whole-table but wrong for multi-table. Rejected by Q2 at extra_active>0.
        "module": _dus(
            "    return False"
        ),
        "refinement": "always emitting the direct single-table DELETE would, for "
                      "a genuine multi-table delete (extra join active), drop the "
                      "subquery filter and delete unfiltered rows, failing the "
                      "multi-table PASS_TO_PASS delete tests; it does NOT resolve.",
        "rationale": "rejected by Q2 (Result()==(extra_active!=0)) — for any "
                     "extra_active>0 the rival returns False where the spec "
                     "demands True.",
    },
    {
        "id": "predicate-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Predicate returns the negation of the correct discriminator: True iff
        # extra_active != 0. Fix still applied (so P2 holds) but P3/P4 fail.
        "module": _rst(
            "    query.primary_present = True\n"
            "    return query.extra_active != 0"
        ),
        "refinement": "an inverted single_alias (True exactly when extra tables "
                      "ARE active) would force a subquery for whole-table deletes "
                      "and a direct delete for multi-table ones — both wrong; it "
                      "fails F2P test_fast_delete_all and the multi-table tests; "
                      "does NOT resolve.",
        "rationale": "rejected by P4 (Result()==(extra_active==0)): the rival "
                     "returns the negation, disagreeing on the whole domain "
                     "except the empty boundary.",
    },
]

# No @ContractOnly axioms and no A-reference deep models in this bundle
# (meta.axioms == [], deep_model_references == []; the changed op is pure
# table-reference bookkeeping modeled directly). The refinement claim is
# validated by axiom_check.py (G-AX) against the real Django delete compiler,
# not by an axiom Ensures. Hence no axiom-lane cases.
AXIOM_TESTS = []
