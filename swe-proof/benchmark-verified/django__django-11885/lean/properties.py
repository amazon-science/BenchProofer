# properties.py — G-PBT falsification battery for django__django-11885 (lean lane).
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
#   combineFastDeletes : List (Table × Column) → List (Table × List Column)
#   The scheduled bulk operations, fully pinned to the input relations. The single
#   postcondition clause `result = groupByTable rels` determines the whole output:
#   the input relations grouped by their target table — one entry per DISTINCT target
#   table in first-discovery order, each carrying the joined columns of the relations
#   landing on that table in discovery order. groupByTable is a total, transparent
#   fold over the input (Nat identities, no opaque callee, no answer-key), so `decide`
#   computes it at any literal input — witnesses need no conditioning on the carrier.
#
# Although the postcondition is a single equality, it pins several INDEPENDENT
# sub-behaviours that a rival can attack one at a time:
#   (a) DISTINCT-table collapse: relations that share a target table become ONE entry
#       (not one-per-relation) — this is the load-bearing behaviour the F2P demands;
#   (b) per-table SEPARATION: relations on DIFFERENT tables stay in different entries
#       (not merged into one);
#   (c) COLUMN retention: a merged entry keeps ALL joined columns of the relations
#       that landed on its table (nothing dropped);
#   (d) non-emptiness: a non-empty run yields at least one entry.
#
# CARRIER NOTE: the nagini sibling abstracted the same decision to a `distinct_count`
# fold over a `List[int]` of related-table identities behind fractional read
# permission — it modeled only the COUNT of combined removals. This backend models
# the richer object directly: the grouped list of (table, columns) over transparent
# Nat identities. So nagini's count-clause rivals map onto the distinct-collapse
# clause here, and the extra structure (per-table separation, column retention,
# ordering) is additionally attackable.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's mandatory `_FRAME_MUT`: the candidate run was
#     Acc(list_pred(related_tables),1/2) read-only, and the rival wrote back into it).
#     Lean is referentially transparent — no aliasing, no fractional permission — so a
#     "store into a read-only input" rival is not expressible and the whole lane is
#     VACUOUS here. See 'assessment'.
#   * (none — the ADMISSIBILITY lane DOES port; see pos-admiss-f2p-satisfiable below.
#     An earlier revision of this manifest dropped it on the ground that the lean
#     obligation carries NO precondition hypothesis, so nothing could be
#     PRECOND-TOO-STRONG. That reason is wrong: the analogue on a total carrier is the
#     obligation being UNSATISFIABLE at exactly an F2P-shaped input — a spec whose
#     single clause no result can meet there would still discharge `∀ rels, …`
#     vacuously only if the carrier were empty, and otherwise pins an unreachable
#     answer. Discharging the obligation at the concrete F2P input BY EVALUATION,
#     as a `have`, before closing the frozen obligation verbatim, tests that
#     directly.)
#   * ORDER rivals (prepend a new table entry / prepend a merged column) were built and
#     seen to be REFUTABLE by the spec here (the spec pins first-discovery order on
#     both legs, per mapping.md's ordered bijection), but they are DROPPED as reject
#     cases: their faithful real patch reorders the OR-clauses within a combined DELETE
#     (or the order of separate emissions), which is SQL-equivalent and query-count
#     identical, so it would still resolve the F2P. Shipping them would be a spec-view
#     stronger than the fix requires, not a verify-does-not-imply-resolve break. See
#     'assessment'.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. The grouping
#     is modeled DEEPLY (groupByTable), so there is no consumed axiom anyway.
from pathlib import Path

INSTANCE = "django__django-11885"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The inner grouping step, lying ENTIRELY inside impl-start/impl-end and unique in the
# file. Every rival that keeps the loop shape edits THIS block.
_INNER = (
    "    if groups.any (fun q => q.1 == p.1) then\n"
    "      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)\n"
    "    else\n"
    "      groups := groups ++ [(p.1, [p.2])]"
)
assert _BASE.count(_INNER) == 1, "inner grouping anchor drifted"

# The full impl body (used by the direct-oracle positive, which drops the loop).
_FULL_IMPL = (
    "def implementation_combineFastDeletes\n"
    "    (rels : List (Table × Column)) : List (Table × List Column) := Id.run do\n"
    "  let mut groups : List (Table × List Column) := []\n"
    "  for p in rels do\n"
    "    if groups.any (fun q => q.1 == p.1) then\n"
    "      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)\n"
    "    else\n"
    "      groups := groups ++ [(p.1, [p.2])]\n"
    "  return groups"
)
assert _BASE.count(_FULL_IMPL) == 1, "full impl anchor drifted"

# The frozen proof body (only the tactic lines inside proof-start/proof-end): the
# `helper` induction plus the final rewrite. Swapped only by the direct-oracle
# positive, whose different impl needs a (shorter, honest) reproof of the identical
# theorem statement.
_PROOF = _BASE[
    _BASE.index("  have helper"):
    _BASE.index("  rw [h2, helper]") + len("  rw [h2, helper]")
]
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-reshape-local-bool: structurally-DIFFERENT but behaviourally identical imperative
# impl. The membership test is bound to a local `found` before the branch; the loop
# shape, update expressions, and final result are otherwise unchanged, so the output
# equals the frozen impl's on every input. The frozen `theorem correct_*` statement is
# kept byte-identical AND the frozen proof body still closes (the `let` binding is
# definitionally transparent), so this is a faithful restructure with no reproof and no
# new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit to one
# syntactic impl shape).
_POS_RESHAPE = _swap(
    _BASE,
    _INNER,
    "    let found := groups.any (fun q => q.1 == p.1)\n"
    "    if found then\n"
    "      groups := groups.map (fun q => if q.1 == p.1 then (q.1, q.2 ++ [p.2]) else q)\n"
    "    else\n"
    "      groups := groups ++ [(p.1, [p.2])]",
)

# pos-direct-grounded-oracle: the cheapest HONEST impl. The postcondition oracle
# groupByTable is GROUNDED in the argument (a total transparent fold), so directly
# returning it is a fully-grounded correct implementation, not an ungrounded-oracle
# echo — a wrong constant/echo fails the postcondition. The proof collapses to `rfl`
# after unfolding (the impl is now definitionally groupByTable). MUST verify (the
# postcondition is literally result = groupByTable rels); else SPEC-TOO-STRONG.
_POS_DIRECT = _swap(
    _swap(
        _BASE,
        _FULL_IMPL,
        "def implementation_combineFastDeletes\n"
        "    (rels : List (Table × Column)) : List (Table × List Column) :=\n"
        "  groupByTable rels",
    ),
    _PROOF,
    "  intro rels\n"
    "  unfold problem_spec_combineFastDeletes implementation_combineFastDeletes\n"
    "  rfl",
)


# ===========================================================================
# ADMISSIBILITY (satisfiability at an F2P-shaped input) — must VERIFY, else
# PRECOND-TOO-STRONG. The frozen obligation is unconditional, so the porting
# analogue of nagini's precondition probe is: is the single postcondition clause
# actually SATISFIABLE at the concrete input the F2P exercises, by evaluation?
# Two `have`s are inserted at the TOP of the frozen proof body, before the frozen
# closing argument (which follows verbatim, so the theorem is still reproven by
# the frozen script and nothing is weakened):
#   * `f2p`      — the impl EVALUATES at the F2P shape to the collapsed schedule
#                  [(0, [1, 2])]: two relations on one target table, ONE entry;
#   * `f2p_spec` — the frozen predicate itself HOLDS at that input, closed by
#                  `decide` (not by the frozen induction), i.e. the obligation is
#                  discharged at that point by computation alone.
# Both are decided by the kernel, so neither can pass vacuously: replacing the
# claimed value with the PRE-PATCH one ([(0,[1]),(0,[2])]) makes each `decide`
# report `... is false` and the case fails. If this case cannot verify, the spec
# pins an answer unreachable at the very input the fix is about.
# ===========================================================================
_ADMISS = _swap(
    _BASE,
    "  intro rels\n  unfold problem_spec_combineFastDeletes",
    "  have f2p : implementation_combineFastDeletes [(0, 1), (0, 2)]\n"
    "      = [(0, [1, 2])] := by\n"
    "    decide\n"
    "  have f2p_spec : problem_spec_combineFastDeletes [(0, 1), (0, 2)]\n"
    "      (implementation_combineFastDeletes [(0, 1), (0, 2)]) := by\n"
    "    unfold problem_spec_combineFastDeletes\n"
    "    decide\n"
    "  intro rels\n  unfold problem_spec_combineFastDeletes",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# no-combine: never merges; appends a fresh entry for EVERY relation, so a table hit
# through k columns yields k entries. This is exactly the PRE-PATCH shape (one
# emission per relation).
_RIV_NOCOMBINE = _swap(_BASE, _INNER, "    groups := groups ++ [(p.1, [p.2])]")

# over-merge: ignores target-table identity and folds every relation into a single
# entry keyed on the first table seen, so relations on DIFFERENT tables are wrongly
# combined.
_RIV_OVERMERGE = _swap(
    _BASE,
    _INNER,
    "    match groups with\n"
    "    | [] => groups := [(p.1, [p.2])]\n"
    "    | (t, cs) :: _ => groups := [(t, cs ++ [p.2])]",
)

# drop-column: groups by table correctly (one entry per distinct table) but on a merge
# it forgets to append the new column — the recurring relation's joined column is lost.
_RIV_DROPCOL = _swap(
    _BASE,
    _INNER,
    "    if groups.any (fun q => q.1 == p.1) then\n"
    "      groups := groups.map (fun q => q)\n"
    "    else\n"
    "      groups := groups ++ [(p.1, [p.2])]",
)

# empty-schedule: schedules NOTHING for any input — the constant empty result.
_RIV_EMPTY = _swap(
    _BASE,
    _FULL_IMPL,
    "def implementation_combineFastDeletes\n"
    "    (rels : List (Table × Column)) : List (Table × List Column) :=\n"
    "  []",
)


def _wit(rels, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal input, closed by `decide`. `rels` is the Lean List (Table × Column)
    literal. Elaborates against a rival that diverges from groupByTable there, and
    fails on gold (which satisfies the spec at every input)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_combineFastDeletes {rels}\n"
        f"    (implementation_combineFastDeletes {rels}) := by\n"
        f"  unfold problem_spec_combineFastDeletes implementation_combineFastDeletes\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reshape-local-bool",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RESHAPE,
        "rationale": (
            "structurally-different but CORRECT impl: the per-relation membership test "
            "is bound to a local boolean before the branch, keeping the loop shape and "
            "update expressions, so the output equals the frozen impl's on every input. "
            "The frozen `theorem correct_combineFastDeletes` statement is byte-identical "
            "and the frozen proof body still closes (the let binding is definitionally "
            "transparent) — a faithful restructure with no reproof and no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to one syntactic impl shape)."
        ),
    },
    {
        "id": "pos-direct-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the postcondition oracle groupByTable is GROUNDED in the argument (a total "
            "transparent fold), so `implementation := groupByTable rels` is the honest "
            "cheapest CORRECT impl, not an ungrounded echo; the proof collapses to `rfl` "
            "after unfolding. Must verify (postcondition is literally result = "
            "groupByTable rels); else SPEC-TOO-STRONG. Also shows the spec is not "
            "echo-vulnerable: any WRONG constant fails the postcondition (see the "
            "empty-schedule reject)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "pos-admiss-f2p-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "ADMISSIBILITY at the F2P shape. The frozen obligation is unconditional, so "
            "the analogue of nagini's precondition probe on this total carrier is whether "
            "the single postcondition clause is SATISFIABLE at the concrete input the F2P "
            "exercises — two cascading relations landing on the SAME target table, "
            "rels = [(0,1),(0,2)]. The variant inserts two kernel-decided `have`s at the "
            "TOP of the frozen proof body: the impl evaluates there to the COLLAPSED "
            "schedule [(0,[1,2])] (one entry, both columns — one bulk operation, not two), "
            "and `problem_spec_combineFastDeletes` itself HOLDS at that input by `decide` "
            "rather than by the frozen induction. The frozen closing argument then follows "
            "verbatim, so the theorem statement and its proof are untouched and nothing is "
            "weakened. Neither `have` can pass vacuously: substituting the PRE-PATCH value "
            "[(0,[1]),(0,[2])] for either claim makes `decide` report `is false` and the "
            "case fails (both controls were built and observed to fail exactly so). If "
            "this case cannot VERIFY => PRECOND-TOO-STRONG: the spec would pin an answer "
            "unreachable at precisely the input the desired behaviour is about."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-no-combine-one-per-relation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOCOMBINE,
        "refinement": (
            "appending a fresh entry per relation is literally the PRE-PATCH shape: one "
            "bulk operation per cascading relation instead of one per distinct target "
            "table. On the F2P case — a record whose dependent has TWO cascading "
            "relations landing on the SAME target table (rels = [(t,c0),(t,c1)]) — it "
            "schedules TWO operations where the fix schedules ONE, so the total query "
            "count is one too high and assertNumQueries(2) fails. A faithful patch of "
            "this shape does NOT resolve; a verifying rival is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by result = groupByTable rels. Attacks the distinct-table-collapse "
            "sub-behaviour (a): two relations on the same table must yield ONE entry with "
            "both columns, not two entries. Witness varies the COLUMN binder (.2) across "
            "the two relations while sharing the TABLE binder (.1). If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # [(0,1),(0,2)]: shared table -> gold = [(0,[1,2])]; rival = [(0,[1]),(0,[2])].
        "witness": _wit("[(0, 1), (0, 2)]",
                        "shared target table: gold combines to one entry, rival keeps two"),
    },
    {
        "id": "weak-over-merge-across-tables",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OVERMERGE,
        "refinement": (
            "folding every relation into a single entry keyed on the first table seen "
            "merges relations landing on DIFFERENT target tables. Its faithful real "
            "counterpart would emit ONE combined bulk operation spanning unrelated "
            "tables — deleting rows of the wrong table (a correctness/integrity bug) and "
            "collapsing what must remain separate operations, so PASS_TO_PASS delete "
            "tests (e.g. distinct-relation fast deletes) and the query count both break. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by result = groupByTable rels. Attacks the per-table-separation "
            "sub-behaviour (b): relations on different tables must occupy different "
            "entries. Witness varies the TABLE binder (.1) between the two relations. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        # [(0,1),(1,2)]: distinct tables -> gold = [(0,[1]),(1,[2])]; rival = [(0,[1,2])].
        "witness": _wit("[(0, 1), (1, 2)]",
                        "distinct target tables: gold keeps two entries, rival over-merges"),
    },
    {
        "id": "weak-drop-column-on-merge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPCOL,
        "refinement": (
            "grouping by table but forgetting to append the joined column on a merge "
            "produces the right entry-per-table shape yet an incomplete column list: the "
            "recurring relation's join column is lost. Its faithful counterpart would "
            "emit a combined bulk operation missing one of the OR-ed conditions, so rows "
            "reachable only through the dropped column are NOT deleted (a cascade "
            "integrity bug) — the delete result is wrong. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by result = groupByTable rels. Attacks the column-retention "
            "sub-behaviour (c): a merged entry must carry ALL joined columns of the "
            "relations on its table. Witness shares the TABLE binder (.1) and varies the "
            "COLUMN binder (.2), at a table identity distinct from the other witnesses. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # [(3,7),(3,9)]: gold = [(3,[7,9])]; rival drops the merge column = [(3,[7])].
        "witness": _wit("[(3, 7), (3, 9)]",
                        "recurring table: gold keeps both columns, rival drops the second"),
    },
    {
        "id": "weak-empty-schedule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTY,
        "refinement": (
            "scheduling nothing for any input issues NO bulk operation for any cascading "
            "relation: the fast-deletable children are silently not removed (a cascade "
            "integrity bug) and the query count is short. assertNumQueries(2) fails (the "
            "combined operation is absent) and the delete leaves orphaned rows. Does NOT "
            "resolve; also demonstrates the postcondition is not satisfiable by an empty "
            "echo."
        ),
        "rationale": (
            "REJECTED by result = groupByTable rels. Attacks the non-emptiness "
            "sub-behaviour (d): a non-empty run must yield at least one entry. Witness is "
            "a SINGLETON run, varying both binders to a point disjoint from the other "
            "witnesses. If it VERIFIES => SPEC-TOO-WEAK (a hollow constant would pass)."
        ),
        # [(2,8)]: gold = [(2,[8])]; rival = [] (empty).
        "witness": _wit("[(2, 8)]",
                        "singleton run: gold schedules one entry, rival schedules nothing"),
    },
]


# No @ContractOnly axioms and no opaque callees: the grouping (distinct-table collapse,
# per-table column accumulation, first-discovery ordering) is modeled DEEPLY over the
# transparent List (Table × Column) carrier, so the axiom lane is vacuous here and
# belongs to G-AX regardless.
AXIOM_TESTS = []
