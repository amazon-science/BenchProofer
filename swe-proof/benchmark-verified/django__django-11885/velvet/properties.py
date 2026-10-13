"""properties.py — G-PBT falsification battery for django__django-11885 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct combineByTable`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
discriminating subject — here the named ``witness_reference``, since the frozen
impl's tester does not reduce; see WITNESS MECHANICS below).

DEFENDED SURFACE. One contracted method over a read-only sequence of candidate
relations ``relations : List Relation`` (``Relation = Int × Int``: a target-table
identity paired with the single referencing column that selects rows on it). The
method returns the combined plan and carries two load-bearing post-images:

  combineByTable (relations)   ensures out = combined relations
                               ensures (out.map Prod.fst).Nodup

``combined`` is the order-preserving, group-by-table collapse of the sequence:
every distinct table appears exactly once, in first-encounter order, carrying
every column that referenced it (columns accumulated in first-encounter order).
The second clause is the independent no-table-twice guarantee — the property the
failing test demands (a table that N relations reference is planned as ONE
combined removal, not N). ``relations`` is the sole INPUT BINDER; it is read-only
(no ``mut``), and every reject witness below varies it (repeated-table stream,
two-distinct-table stream, singleton) and its two projections (table ``.1`` and
column ``.2``).

The failing test deletes a source whose child has TWO foreign keys pointing at
the same target table and asserts a fixed, small query count: the two candidates
that share one target table must collapse into ONE combined removal. In carrier
terms that is ``relations = [(t, c1), (t, c2)]`` with ``combined`` a single group
``[(t, [c1, c2])]`` and its table list ``[t]`` (Nodup). Any rival that emits two
groups keyed on ``t`` there does NOT resolve.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the sibling
    because a read-only input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent: every parameter is an
    immutable value, this bundle declares no ``mut`` binder on the input, there
    is no heap and no aliasing — so there is no read-only input to mutate and no
    substitute probe to build. Not fabricated (see the module footer).
  * UNGROUNDED-ORACLE ECHO — N/A. Both post-images are total, fully unfolded
    functions of the method's own input (``combined``/``combineStep``/
    ``combineInto`` are concrete ``def``s in the ``pure`` region; the ``axioms``
    region declares nothing). There is no opaque answer key to echo — evaluating
    ``combined`` IS the correct answer — so there is no WRONG echo to build.
    Honest cheapest-reshape positive controls (``pos-*``) stand in.
  * MULTIPLICITY — APPLIES: a rival that emits one group per candidate (no
    grouping by table) violates BOTH post-images at once when a table recurs (the
    no-table-twice clause AND the exact-plan clause). ``weak-emit-per-candidate``
    attacks this — it is the sibling's central pre-patch defect.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on part of the input domain
    (agreeing on all-distinct or empty inputs) but dropping a planned group on a
    larger sub-domain. ``weak-drop-first`` and ``weak-drop-all`` attack this; both
    keep table-uniqueness and fail only the exact-plan clause, at points distinct
    from each other and from the multiplicity rival.

WITNESS MECHANICS on this carrier. Each reject rival is written straight-line, so
ITS tester reduces and ``decide`` settles it; the witness states ``…Tester
<relations> = false`` at a concrete point where the rival's plan violates a
post-image while the correct plan satisfies it. No
``sorry``/``admit``/``native_decide``/``axiom``.

The frozen impl CANNOT serve as the discriminating subject, and this is MEASURED,
not assumed. Its ``while`` loop elaborates to a partial fixpoint the kernel does
not reduce, so ``combineByTableTester <relations>`` is STUCK against it: the build
fails with ``Tactic `decide` failed … did not reduce to `isTrue` or `isFalse``` for
EVERY claim, whatever its truth. Confirmed by forgery — the exact OPPOSITE claim
(``… = true``, i.e. "the frozen plan is WRONG here") fails against the frozen
solution with the byte-identical error, and ``decide +kernel``, ``rfl`` and
unfolding the tester are all stuck the same way. So a gold-side exit code here
would attest to a refutation the kernel never performed, and reading "gold failed"
as discrimination would be HOLLOW. An earlier revision of this docstring asserted
exactly that reading; it was wrong, and this paragraph replaces it.

Every reject case therefore names an explicit ``witness_reference``: the loop-free
``_REF`` impl (the same source as ``pos-collapse-direct``), which shares the
frozen spec and VERIFIES — so by soundness it cannot violate that spec at any
input — and whose tester DOES reduce. Against that subject the refutation is a
real evaluation and the exit code TRACKS THE CLAIM: the witness fails with
``Tactic `decide` proved that the proposition … is false``, while the flipped
claim ``… = true`` elaborates cleanly. That forgery pair is the evidence the
reference is a genuine oracle rather than an impl that merely fails everything.
The gate would reach the same subject via its own positives fallback, but naming
it makes the attestation a property of THIS battery rather than an artifact of
fallback ordering.

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. ``weak-drop-first`` is the sharper near-miss of
``weak-drop-all`` (it drops one planned group, not all), so it is refuted on a
two-distinct-table stream where it returns the tail while ``weak-drop-all``
returns empty — the sub-domain that SEPARATES them — rather than on the singleton
where the two coincide. ``weak-drop-all`` is refuted on the singleton, and
``weak-emit-per-candidate`` on the repeated-table stream (the only shape on which
the no-table-twice clause bites). Three distinct points, so the dependence of
both post-images on ``relations`` is demonstrated, not merely asserted.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the one callee
involved is an unchanged enumerator that only supplies the read-only input
sequence, owed no contract). There is no axiom-soundness / axiom-containment
obligation to probe here, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11885"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the one impl region and is
# ---- unique inside Solution.lean; both facts asserted at load by _swap) ----

# The whole executable body: the accumulator loop that groups every candidate
# relation under its table and returns the plan. Reshaped wholesale by the rivals
# and the straight-line positive.
_IMPL = (
    "    let mut result : List TableGroup := []\n"
    "    let mut i := 0\n"
    "    while i < relations.length\n"
    "      invariant i ≤ relations.length\n"
    "      invariant result = (relations.take i).foldl combineStep []\n"
    "      done_with i = relations.length\n"
    "      decreasing relations.length - i\n"
    "    do\n"
    "      let e := relations[i]!\n"
    "      result := combineInto result e.1 e.2\n"
    "      i := i + 1\n"
    "    return result\n"
)

# The single loop-body step (a substring of _IMPL; unique in the file). Reshaped
# by the loop-preserving positive control.
_STEP = "      result := combineInto result e.1 e.2\n"

# The accumulator initializer (unique). Anchor for the admissibility assert.
_INIT = "    let mut result : List TableGroup := []\n"

# ---- proof-body anchors. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a reshape may retune its tactic script without
# ---- touching the spec or dropping the obligation. ----

# The full frozen tactic script (retuned by the straight-line positive, whose
# no-loop body leaves none of the loop-invariant goals the frozen script closes).
_PROOF = (
    "prove_correct combineByTable by\n"
    "  loom_solve\n"
    "  case «invariant_2: result = (relations.take i).foldl combineStep []» =>\n"
    "    have hi : i < relations.length := by omega\n"
    "    rw [invariant_2, combined_take_step relations i hi, combineStep,\n"
    "        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]\n"
    "  case «ensures_1: (out.map Prod.fst).Nodup» =>\n"
    "    have h := combined_nodup relations\n"
    "    simp_all [combined]\n"
    "  all_goals simp_all [combined]"
)

# The final catch-all tactic line (unique; retuned by the admissibility case to
# also discharge the in-region assert's concrete goal).
_PROOF_TAIL = "  all_goals simp_all [combined]"


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `combineByTableTester <relations> = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict. There is no `require` clause, so the
# ---- precondition is `True` and decides trivially.
_TESTER = (
    "extract_program_for combineByTable\n"
    "prove_precondition_decidable_for combineByTable\n"
    "prove_postcondition_decidable_for combineByTable\n"
    "derive_tester_for combineByTable\n\n"
)


# ---- the discriminating SUBJECT for every reject witness. The frozen impl's
# ---- tester is STUCK (its `while` loop is a partial fixpoint the kernel cannot
# ---- reduce), so a witness build against gold fails for EVERY claim and its exit
# ---- code discriminates nothing — measured by forgery: the opposite claim fails
# ---- with the byte-identical error. This loop-free impl of the SAME frozen spec
# ---- verifies, so it cannot violate that spec at any input, and its tester does
# ---- reduce — so refuting a witness against it is both sound and informative.
# ---- The gate independently re-checks both facts (shares the frozen spec; and
# ---- verifies) before using it as a subject.
_REF = _swap(
    _swap(_BASE, _IMPL, "    return combined relations\n"),
    _PROOF, "prove_correct combineByTable by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps both obligations and the identical
    # theorem statement; only the executable surface and (where needed) the
    # tactic script move.
    # =====================================================================
    {
        "id": "pos-step-rephrased",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the loop body folds one relation through the named per-step
        # combinator instead of spelling the keyed grouping inline. Same
        # accumulator, same order, so both post-images still hold and the frozen
        # loop-invariant proof discharges unchanged (combineStep def-unfolds to
        # the inline combineInto, so loom_solve emits the identical VC).
        "module": _swap(_BASE, _STEP, "      result := combineStep result e\n"),
        "rationale": "a correct reshape of the loop body (folding through the "
                     "per-step combinator) computes the same accumulator, so "
                     "both `out = combined relations` and `(out.map "
                     "Prod.fst).Nodup` still discharge with the frozen "
                     "invariants; must verify else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-collapse-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the loop entirely and return the modeled collapse
        # directly. Observationally identical (the loop's post-state IS the
        # collapse), so both clauses hold; the tactic script is retuned because
        # the no-loop body leaves none of the loop-invariant goals to close (the
        # Nodup clause is discharged by the collapse's own @[grind] uniqueness
        # lemma via loom_solve).
        "module": _REF,
        "rationale": "returning the modeled collapse directly satisfies "
                     "`out = combined relations` definitionally and `(out.map "
                     "Prod.fst).Nodup` by the collapse's own uniqueness lemma "
                     "(`combined_nodup`, `@[grind]`); a correct loop-free reshape "
                     "must verify (else SPEC-TOO-STRONG on the loop form).",
    },

    # =====================================================================
    # ADMISSIBILITY. No method here has a `require` clause, so there is no
    # precondition that could exclude a normal input; the usual "a normal
    # input satisfies the precondition" probe is vacuous. The residual
    # admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE / DEGENERATE at the interesting point — a spec no impl can
    # meet reads exactly like a spec every impl meets. This case discharges an
    # in-region `assert` that pins the collapse's discriminating behavior at the
    # F2P-shaped input (two candidates sharing one target table): the two
    # columns accumulate into ONE group in first-encounter order and the planned
    # table list is unique. The surrounding impl is kept verbatim so the method's
    # own obligations still discharge; the assert is live (a false claim about
    # the same point leaves an unsolved goal).
    # =====================================================================
    {
        "id": "admiss-collapse-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _INIT,
                "    assert (with_name_prefix `assert\n"
                "      (combined [(7, 1), (7, 2)] = [(7, [1, 2])] ∧\n"
                "       ((combined [(7, 1), (7, 2)]).map Prod.fst).Nodup))\n"
                + _INIT),
            _PROOF_TAIL,
            "  all_goals first | (refine ⟨by decide, by decide⟩) "
            "| simp_all [combined]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped input: two candidates `(7,1)`,`(7,2)` sharing "
                     "target table `7` collapse to ONE group `(7,[1,2])` carrying "
                     "both columns in first-encounter order, and the planned "
                     "table list `[7]` is unique. The in-region assert must "
                     "discharge (else the obligation is degenerate); the impl is "
                     "kept verbatim so both ensures clauses still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is written
    # straight-line so its tester reduces under `decide`.
    # =====================================================================
    {
        "id": "weak-emit-per-candidate",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix defect: emit one singleton-column group per candidate, with
        # NO grouping by table. Two candidates on the same table therefore yield
        # two separate groups keyed on that table.
        "module": _swap(
            _BASE, _IMPL,
            "    return relations.map (fun e => (e.1, [e.2]))\n"),
        "refinement": "a counterpart that emits one plan entry per candidate "
                      "relation issues a separate removal for each foreign key, "
                      "so a target table referenced by several candidates is "
                      "queried once per reference instead of once combined — "
                      "exactly the extra-roundtrips regression the failing test "
                      "forbids (it fixes the total query count for a child with "
                      "two foreign keys to one table). It would NOT resolve.",
        "rationale": "REJECT from BOTH clauses: on a repeated-table input the "
                     "per-candidate emission lists that table more than once, so "
                     "`(out.map Prod.fst).Nodup` fails, and `out = combined "
                     "relations` fails since the collapse groups it into one "
                     "entry. Refuted on the F2P-shaped repeated-table input "
                     "`[(1,1),(1,2)]` — the only shape on which the no-table-twice "
                     "clause bites — where both table `.1` recurs and the columns "
                     "`.2` differ.",
        "witness": _TESTER +
                   "example : combineByTableTester [(1, 1), (1, 2)] = false := by\n"
                   "  decide\n",
        "witness_reference": _REF,
    },
    {
        "id": "weak-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: the collapse is correct, but the first planned group is
        # dropped. Table-uniqueness still holds (dropping from a unique-table
        # list keeps it unique), so ONLY the exact-plan clause is attacked.
        "module": _swap(_BASE, _IMPL, "    return (combined relations).drop 1\n"),
        "refinement": "a counterpart that omits the first planned group never "
                      "issues that table's combined removal, so its referencing "
                      "rows are not cascade-deleted (an integrity bug) and the "
                      "query count is short by one on any input with at least one "
                      "planned group. It would NOT resolve.",
        "rationale": "REJECT from `out = combined relations`: on any non-empty "
                     "plan the impl drops the first group the post-image "
                     "requires. Table-uniqueness still holds, so this attacks the "
                     "exact-plan clause alone. Refuted on a two-distinct-table "
                     "input `[(1,1),(2,2)]`, where it returns the tail while "
                     "weak-drop-all returns empty — the point that SEPARATES the "
                     "two near-misses (on the singleton they coincide).",
        "witness": _TESTER +
                   "example : combineByTableTester [(1, 1), (2, 2)] = false := by\n"
                   "  decide\n",
        "witness_reference": _REF,
    },
    {
        "id": "weak-drop-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Emits nothing: correct only on the empty input, drops every planned
        # group otherwise. Table-uniqueness holds vacuously.
        "module": _swap(_BASE, _IMPL, "    return []\n"),
        "refinement": "a counterpart that emits no plan issues no fast-delete "
                      "removal for any target table, so every referencing child "
                      "table is left un-deleted and the delete's query count is "
                      "wrong. It would NOT resolve.",
        "rationale": "REJECT from `out = combined relations`: on any non-empty "
                     "input the impl emits the empty plan where the post-image "
                     "demands the collapse. Correct only on the empty input. "
                     "Refuted on the singleton `[(1,1)]`, the smallest point that "
                     "separates it from the frozen plan.",
        "witness": _TESTER +
                   "example : combineByTableTester [(1, 1)] = false := by\n"
                   "  decide\n",
        "witness_reference": _REF,
    },

    # =====================================================================
    # ADDED BY AUDIT. The three ported rivals all attack the SET/ORDER of
    # planned groups (over-listing a table, dropping groups); none attacks the
    # COLUMN LIST a group carries, which is the other half of what "one combined
    # query per table" means — a plan with the right tables but the wrong columns
    # issues the right NUMBER of queries and deletes the wrong rows. Both rivals
    # below keep the table projection (hence `(out.map Prod.fst).Nodup`) exactly
    # right and are refuted through `out = combined relations` alone.
    # =====================================================================
    {
        "id": "weak-drop-extra-columns",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps only the FIRST column that referenced each table: right group
        # set, right table order, under-populated column lists.
        "module": _swap(
            _BASE, _IMPL,
            "    return (combined relations).map (fun g => (g.1, [g.2.headI]))\n"),
        "refinement": "a counterpart that keeps only the first referencing column "
                      "per target table issues one combined removal per table — "
                      "the right query COUNT — whose match clause omits every "
                      "other referencing column, so rows reachable only through a "
                      "dropped column are never deleted. That is a silent "
                      "integrity bug a fixed query count cannot detect, and it "
                      "defeats the purpose of combining: the single query is "
                      "supposed to match ALL the columns that referenced the "
                      "table. It would NOT resolve.",
        "rationale": "REJECT from `out = combined relations` alone: the table "
                     "projection is untouched, so `(out.map Prod.fst).Nodup` still "
                     "holds and the attack lands on the COLUMN content rather than "
                     "on the group set — the surface the three ported rivals leave "
                     "unprobed. Refuted on the F2P-shaped repeated-table input "
                     "`[(1,1),(1,2)]`, where the collapse must carry both columns "
                     "`[1,2]` and this emits `[1]`.",
        "witness": _TESTER +
                   "example : combineByTableTester [(1, 1), (1, 2)] = false := by\n"
                   "  decide\n",
        "witness_reference": _REF,
    },
    {
        "id": "weak-reverse-columns",
        "kind": "uniqueness",
        "expect": "reject",
        # Every column present, but in LAST-encounter order: the sharpest
        # near-miss the carrier admits.
        "module": _swap(
            _BASE, _IMPL,
            "    return (combined relations).map (fun g => (g.1, g.2.reverse))\n"),
        "refinement": "a counterpart that accumulates a table's referencing "
                      "columns in reverse encounter order is the sharpest "
                      "near-miss available here: it plans one removal per table "
                      "carrying every column, so it matches the same rows and the "
                      "query count is right. It is still not the specified plan — "
                      "the spec pins the column order the accumulator produces, "
                      "which is what makes the plan a FUNCTION of the enumeration "
                      "order rather than of an unordered set; an impl free to "
                      "permute it is free to differ run to run.",
        "rationale": "REJECT from `out = combined relations` at the tightest point "
                     "the carrier admits: group set, table order and each group's "
                     "column MULTISET are all correct, so `(out.map "
                     "Prod.fst).Nodup` holds and only the documented "
                     "first-encounter COLUMN ORDER differs. Refuted on "
                     "`[(1,1),(1,2)]`, the smallest input where one table carries "
                     "two distinct columns so the two orders differ at all (on a "
                     "singleton group, or on all-distinct tables, this rival is "
                     "observably IDENTICAL to the frozen plan — which is what "
                     "makes it a near-miss rather than a restatement).",
        "witness": _TESTER +
                   "example : combineByTableTester [(1, 1), (1, 2)] = false := by\n"
                   "  decide\n",
        "witness_reference": _REF,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 mandatory frame-mutation, 3 uniqueness rivals);
# every one is accounted for below. The sibling contracts a single function
# `combined_fast_delete_count(related_tables)` over a read-only, half-permission
# list, returning the DISTINCT-COUNT of related tables; this bundle contracts a
# single method `combineByTable(relations)` over the SAME read-only candidate
# sequence but returns the whole order-preserving group-by-table PLAN — a strictly
# richer observable (the sibling's `distinct_count` is exactly `(combined
# relations).map Prod.fst |>.length` on this carrier). Every value-surface case
# carries across; the permission surface does not exist here.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-direct-grounded-oracle            -> pos-collapse-direct           PORTED
#   pos-reshape-local-bool                -> pos-step-rephrased            PORTED
#   admiss-f2p-shape                       -> admiss-collapse-nondegenerate RE-AIMED
#   frame-mutation-write-readonly          -> (none)                        VACUOUS
#   partial-domain-one-per-candidate       -> weak-emit-per-candidate       PORTED
#   partial-domain-skip-first-element      -> weak-drop-first               PORTED
#   partial-domain-never-increment         -> weak-drop-all                 PORTED
#
# 5 ported, 1 re-aimed, 1 vacuous = 7. No case dropped for proof cost.
#
# ADDED BY AUDIT (beyond the sibling): `weak-drop-extra-columns` and
#   `weak-reverse-columns`. The sibling models the observable as a scalar COUNT,
#   so it has no rival for group CONTENT — there is nothing to get wrong about a
#   number's columns. This carrier's plan pins the column list of each group, and
#   that surface was unattacked: all three ported rivals keep every group's
#   columns correct and differ only in which groups appear. The two added rivals
#   close it from both sides — one drops columns (under-matching rows while
#   issuing the right number of queries), one keeps every column but in
#   last-encounter order (the sharpest near-miss the carrier admits: same group
#   set, same table order, same column multiset). Both keep the table projection
#   exact, so both are refuted through `out = combined relations` alone with
#   `(out.map Prod.fst).Nodup` still satisfied — which is what makes them
#   independent of the three ported rivals rather than restatements.
#
# RE-EXPRESSED (a note, not a separate class): the sibling models the observable
#   as a scalar `distinct_count(related_tables)` and its rivals miscount it
#   (returns len => one-per-candidate; skips the first element => undercounts by
#   1; never increments => 0). This bundle models the whole PLAN, so the SAME
#   arguments become plan-shaped: one-per-candidate becomes "emit a singleton
#   group per relation" (weak-emit-per-candidate), which on a repeated-table
#   input over-lists the table (violating BOTH clauses) exactly as the scalar
#   rival over-counts it; skip-first becomes "drop the first planned group"
#   (weak-drop-first); never-increment (the scalar 0) becomes "emit the empty
#   plan" (weak-drop-all). Each ARGUMENT — why the faithful patch would not
#   resolve the F2P — is carried over unchanged; only the carrier is richer.
#   Because the richer carrier pins ORDER and COLUMN CONTENT (not just a count),
#   the plan-shaped rivals are STRICTLY harder to satisfy than their scalar
#   siblings, so no weakening is introduced by the port.
# RE-AIMED (admissibility): the sibling's admissibility case builds the F2P-shaped
#   input [7,7] as a fresh half-permission literal and self-calls the function to
#   assert the documented outcome r==1. There is no permission surface here and
#   no `require` clause, so the "establish the precondition for a normal input"
#   reading is vacuous. It is re-aimed at the residual admissibility risk on a
#   total domain — that the post-image is degenerate at the interesting point — by
#   discharging an in-region assert that the F2P-shaped input `[(7,1),(7,2)]`
#   collapses to the single combined group `(7,[1,2])` with a unique table list.
#   This preserves the sibling's exact F2P witness point (two candidates sharing
#   one target table => one combined removal).
# VACUOUS (frame-mutation-write-readonly): the sibling's MANDATORY probe writes
#   `related_tables[i-1] = table` into an input held at half heap permission and
#   is rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent, there is no heap, no aliasing, and this bundle declares no `mut`
#   binder on `relations`, so there is no read-only input to overwrite and no
#   substitute probe exists. MEASURED, not merely argued: both spellings of the
#   write are refused by the ELABORATOR rather than by the spec, so neither can be
#   a rival case at all — `relations := []` gives "`relations` cannot be mutated,
#   only variables declared using `let mut` can be mutated", and an element write
#   `relations[0]! := (9, 9)` gives "unsupported pattern in syntax match". A case
#   whose file fails to elaborate for a reason unrelated to the postcondition
#   would be recorded as `rejected` while attesting to nothing — precisely the
#   hollow outcome the witness requirement exists to prevent.
#   Not fabricated (spec_guide directive 5: the frame
#   obligation here is discharged by the ABSENCE of a `mut` on `relations`, which
#   the frozen spec already encodes). The sibling's "the input run must not be
#   mutated" obligation is thereby structurally guaranteed, not merely tested.
#
# WITNESS DISTINCTNESS. The five rivals probe the sole binder `relations` at
#   distinct points AND through distinct clauses. The two added rivals share the
#   repeated-table point `[(1,1),(1,2)]` with `weak-emit-per-candidate`, which is
#   admissible because they fail there for DIFFERENT reasons and through different
#   clauses: `weak-emit-per-candidate` over-lists the table (violating
#   `(out.map Prod.fst).Nodup` AND the exact-plan clause), while both added rivals
#   keep the table projection exactly right and violate only `out = combined
#   relations`, one at the column SET and one at the column ORDER. The three
#   ported rivals probe three distinct points: weak-emit-per-candidate at the repeated-table input
#   `[(1,1),(1,2)]` (the only shape on which the no-table-twice clause is
#   violable, and the exact F2P shape), weak-drop-first at a two-distinct-table
#   input `[(1,1),(2,2)]` (where it diverges from weak-drop-all, which returns
#   empty there), weak-drop-all at the singleton `[(1,1)]`. So `relations` is
#   varied across repeated-table / distinct-table / length, both projections
#   (`.1` table and `.2` column) take multiple values, and the near-miss pair is
#   separated at the point that distinguishes them. pts = 3.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference deep model (the grouping is modeled deeply in the pure
# region), so there is nothing there to probe.
AXIOM_TESTS = []
