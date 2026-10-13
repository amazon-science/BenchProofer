"""properties.py — G-PBT falsification battery for django__django-15563 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier.  ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates).

DEFENDED SURFACE (one contracted method over an ordered list of ancestors that
a single statement must co-update, and the rows of fetched identity values):

  parentFilterIds (parents, rows)
    ensures out = (assignedColumns parents).map (idColumn rows)

  where the deeply-modeled routing pins, per ancestor in order, WHICH fetched
  column its filter values are drawn from:
    * an ancestor that shares the child's identity reuses column 0, and
      CONSUMES NOTHING (the next free column does not advance);
    * one that does not is assigned the NEXT free column, which is then
      consumed — so distinct-identity ancestors take the contiguous appended
      columns 1, 2, 3, … in the order they appear (dense AND distinct).
  ``parents`` and ``rows`` are FREE inputs: the post-image must hold for every
  ancestor list and every fetched block, which is what makes the partial-domain
  rivals below refutable at a concrete point.

ADVERSARIAL READ of the nagini classes carried over:
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend.  The nagini sibling's
    mandatory frame-mutation rival overwrites its read-only input through a
    fractional heap permission.  Lean and Velvet are referentially transparent:
    every parameter is an immutable value, this bundle declares NO ``mut``
    binder on any input (the accumulator is a fresh local), there is no heap and
    no aliasing.  There is no read-only input to overwrite and no substitute
    probe to fabricate.  Reported as an omission in the footer, not faked.
  * UNGROUNDED-ORACLE ECHO — N/A.  The post-image is a total, fully unfolded
    function of the method's own arguments (``assignedColumns`` and ``idColumn``
    are concrete ``def``s in the ``pure`` region and the ``axioms`` region is
    empty — there is no opaque answer key to echo), so there is no WRONG echo to
    build.  Instead an honest cheapest-reshape POSITIVE CONTROL is carried.
  * PARTIAL-DOMAIN / VALUE — APPLIES.  A rival can be right on part of the
    ancestor domain and diverge on a sub-domain: a distinct-identity ancestor
    sent to column 0; a SECOND distinct-identity ancestor placed on a sparse
    column (over-running the fetched row) or on a colliding constant column (two
    ancestors reading the same column's values); or a SHARED-identity ancestor
    that correctly reuses column 0 but wrongly CONSUMES a column, shifting every
    later ancestor past the row's end.  These are exactly the routings the frozen
    spec's dense-AND-distinct column pin forbids.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``parents.length - i``). A rival
    that loops without a measure is refused outright (``Decreasing annotations
    are required in total correctness semantics``), and a rival that supplies a
    CONSTANT measure to dodge that is refused on the measure's own goal (``case
    «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
    a real build. Divergence therefore does not discharge the ``ensures``
    clauses vacuously. It is still not shipped as a G-PBT reject case, and the
    reason is the witness contract rather than a spec weakness. A reject case
    must carry a witness that ELABORATES against the rival, and neither diverging
    shape gets past that. With NO measure the descent obligation fails at the
    ``method`` itself, ahead of any appended tester, and the witness file retains
    the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
    module does not compile at all. With a measure that does not decrease the
    refusal moves to the ``prove_correct`` site, which IS stripped, so that module
    does elaborate; but the rival's post-image is then an unreduced
    ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
    ``decreasingGadget``, which the kernel will not normalise to a value a
    concrete-input tester can decide. Either way the gate returns
    ``witness-unproven``, an inconclusive outcome. Measured through the
    gate's own ``_check_witness``, even ``example : True := trivial`` comes
    back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
    and would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS MECHANICS — why this battery carries a ``witness_reference``.  The
gate refutes each witness against a second subject and requires it to FAIL
there, which is only evidence if that subject DECIDED something.  The frozen
impl keeps a ``while`` loop, and under ``loom.semantics.choice "demonic"`` the
loop's fixpoint elaborates through ``Classical.choice``, which the kernel cannot
unfold.  Measured here with real builds: all three witnesses below fail against
the FROZEN solution with

    error: Tactic `decide` failed for proposition
      ... did not reduce to `isTrue` or `isFalse`

and so do two control forgeries — the exact OPPOSITE claim (``= true``, i.e.
asserting the rival is CORRECT at that input) and a trivial claim about empty
inputs.  The frozen-side exit code therefore carries NO information: a forged
witness asserting a rival is correct would clear both halves.  That is the
``witness-undecided`` defect, so every reject case names ``_LOOPFREE`` as its
``witness_reference``: a loop-free impl of the same frozen spec that VERIFIES
(measured: exit 0) and whose tester REDUCES.  Re-measured against it, each real
witness fails as a refutation should (``decide`` proved the negation) while the
opposite-claim forgery now correctly ELABORATES rather than passing — so the
second half discriminates for real.  ``_LOOPFREE`` also ships as its own
``expect="verify"`` case, so the battery records that loop-freeness is not what
any rival is being rejected for.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; ``sharesChildPk`` and
``rows`` are free inputs owed no contract).  There is no axiom-soundness /
axiom-containment obligation to probe here, and the gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15563"
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

# The single loop-body step and the accumulator initializer/return: reshaped by
# the loop-preserving positive control and the admissibility probe.
_BODY = (
    "      let p := parents[i]!\n"
    "      st := stepCol st p\n"
    "      i := i + 1\n"
)
_RETURN = "    return st.1.map (idColumn rows)\n"
_INIT = "    let mut st : List Nat × Nat := ([], 1)\n"

# The WHOLE executable body: the accumulator loop that threads the routing and
# maps the fetched columns.  Reshaped wholesale by the uniqueness rivals and by
# the loop-free reference, all of which must be written STRAIGHT-LINE (see
# WITNESS MECHANICS): the frozen `while` elaborates to a partial fixpoint the
# kernel does not reduce, so a rival that KEPT the loop would have a tester as
# stuck as the frozen one and no witness could `decide` it.
_IMPL = (
    "    let mut st : List Nat × Nat := ([], 1)\n"
    "    let mut i := 0\n"
    "    while i < parents.length\n"
    "      invariant i ≤ parents.length\n"
    "      invariant st = (parents.take i).foldl stepCol ([], 1)\n"
    "      done_with i = parents.length\n"
    "      decreasing parents.length - i\n"
    "    do\n"
    "      let p := parents[i]!\n"
    "      st := stepCol st p\n"
    "      i := i + 1\n"
    "    return st.1.map (idColumn rows)\n"
)

# The frozen proof body.  A loop-free impl leaves no loop-invariant goal, so the
# frozen script's `case «invariant_2: ...»` tag no longer exists and the build
# fails with `Case tag ... not found` — a PROOF-shape failure, unrelated to the
# spec (measured).  Only the tactic body changes, which the spec view elides and
# `variant_scope` permits; the `prove_correct parentFilterIds` header and every
# obligation survive byte-identically.
_PROOF = (
    "prove_correct parentFilterIds by\n"
    "  loom_solve\n"
    "  case «invariant_2: st = (parents.take i).foldl stepCol ([], 1)» =>\n"
    "    have hi : i < parents.length := by omega\n"
    "    rw [invariant_2, cols_take_step parents i hi,\n"
    "        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]\n"
    "  all_goals simp_all [assignedColumns]"
)
_PROOF_LOOPFREE = (
    "prove_correct parentFilterIds by\n"
    "  loom_solve\n"
    "  all_goals simp_all [assignedColumns]"
)

for _a in (_BODY, _RETURN, _INIT, _IMPL, _PROOF):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ---- the witness reference (see WITNESS MECHANICS).  A CORRECT, loop-free impl
# ---- of the frozen spec: it folds the frozen `stepCol` over the ancestors
# ---- directly instead of threading the accumulator through a `while`, so it
# ---- computes exactly `assignedColumns` by definition.  Measured: VERIFIES
# ---- (exit 0), and its tester REDUCES, which is what makes the gate's
# ---- "must fail on the reference" half carry information at all.
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL,
          "    let cols := (parents.foldl stepCol ([], 1)).1\n"
          "    return cols.map (idColumn rows)\n"),
    _PROOF, _PROOF_LOOPFREE)


# ---- witness preamble.  The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester
# ---- machinery: `parentFilterIdsTester args = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input.  Checked in a file whose `prove_correct` block has been stripped,
# ---- so no tactic script can mask the verdict.
_TESTER = (
    "extract_program_for parentFilterIds\n"
    "prove_precondition_decidable_for parentFilterIds\n"
    "prove_postcondition_decidable_for parentFilterIds\n"
    "derive_tester_for parentFilterIds\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify.  If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG (over-fit to the literal accumulator/return
    # FORM).  It keeps the loop invariants and the routing step verbatim and
    # only reshapes the executable surface (an intermediate binding for the
    # stepped accumulator, and a local for the assigned-column list before the
    # map), so the obligation is unchanged and the frozen proof still closes.
    # =====================================================================
    {
        "id": "pos-control-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _BODY,
                "      let cur := parents[i]!\n"
                "      let stepped := stepCol st cur\n"
                "      st := stepped\n"
                "      i := i + 1\n"),
            _RETURN,
            "    let cols := st.1\n"
            "    return cols.map (idColumn rows)\n"),
        "rationale": "a correct reshape that binds the stepped accumulator to an "
                     "intermediate local and the assigned-column list to a local "
                     "before mapping the fetched columns still advances the "
                     "accumulator by exactly the same routing step per ancestor, "
                     "so the loop invariant and the post-image "
                     "`out = (assignedColumns parents).map (idColumn rows)` hold "
                     "unchanged.  Only the executable SHAPE changed (no reordered "
                     "routing, no dropped step), so the frozen proof still closes; "
                     "must verify, else SPEC-TOO-STRONG on the accumulator form.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — the loop-free impl that every reject case
    # names as its `witness_reference`.  Shipped as its own case on purpose: the
    # gate checks a reference verifies before refuting witnesses against it, and
    # carrying it here as well records IN THE BATTERY that eliminating the loop
    # is a CORRECT reshape of the frozen spec — so loop-freeness is demonstrably
    # not the property any rival below is being rejected for.  It folds the
    # frozen `stepCol` directly, which is `assignedColumns` by definition, so the
    # post-image holds definitionally and the reshaped proof body closes
    # (measured: verifies).
    # =====================================================================
    {
        "id": "pos-control-loopfree-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _LOOPFREE,
        "rationale": "folding the frozen routing step over the ancestor list "
                     "directly, instead of threading the accumulator through an "
                     "index loop, computes `assignedColumns` by its own "
                     "definition, so the post-image "
                     "`out = (assignedColumns parents).map (idColumn rows)` holds "
                     "definitionally.  The loop-invariant goal disappears with the "
                     "loop, so the tactic body is reshaped accordingly (the "
                     "`prove_correct parentFilterIds` obligation is untouched and "
                     "nothing is assumed).  Must verify, else the spec is "
                     "SPEC-TOO-STRONG on the ITERATION form rather than on the "
                     "routing it is supposed to pin — and, because every reject "
                     "case refutes its witness against this impl, this case is "
                     "also what establishes that those rejections are attributable "
                     "to the routing and not to loop-freeness.",
    },

    # =====================================================================
    # ADMISSIBILITY — no method in this bundle has a `require` clause, so the
    # usual "a normal input satisfies the precondition" probe is vacuous:
    # nothing could exclude an F2P-shaped input.  The residual admissibility
    # risk on a total domain is that the post-image is DEGENERATE at the
    # interesting point (a spec no impl can meet, or one every impl meets,
    # reads the same to the gate).  This case discharges an in-region `assert`
    # SYMBOLICALLY at the F2P-shaped point: the routing must assign a
    # distinct-identity ancestor a fresh, NON-zero column (column 1), which is
    # exactly the behaviour that distinguishes the frozen routing from reusing
    # column 0 for everyone.  The surrounding impl is kept verbatim so the
    # method's own obligation still discharges; the assert is live, not
    # decoration — a false claim about the same point leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-fresh-column-nonzero",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _INIT,
                "    assert (with_name_prefix `assert\n"
                "      (assignedColumns [{ sharesChildPk := false }] = [1]))\n"
                + _INIT),
            "  all_goals simp_all [assignedColumns]\n",
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [assignedColumns]\n"),
        "rationale": "the post-image is non-degenerate at the F2P-shaped point: "
                     "for a single distinct-identity ancestor the routing demands "
                     "the fresh column 1 (a non-zero column distinct from the "
                     "child identity), not column 0.  The in-region assert must "
                     "discharge (else the routing would be degenerate / "
                     "unsatisfiable there); the impl is kept verbatim so the "
                     "method's own obligation still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument for why its faithful real
    # counterpart is a genuine correctness defect.  Every witness names
    # `_LOOPFREE` as its `witness_reference`: refuting against the FROZEN impl
    # decides nothing here (see WITNESS MECHANICS).
    # =====================================================================
    {
        "id": "weak-all-column-0",
        "kind": "uniqueness",
        "expect": "reject",
        # Routes EVERY ancestor through column 0 regardless of whether it shares
        # the child identity — the pre-change behaviour.  Correct only for a list
        # of exclusively shared-identity ancestors; wrong the instant any
        # ancestor has a distinct identity, which must draw from a fresh column.
        # Written straight-line so its tester reduces under `decide`.
        "module": _swap(_BASE, _IMPL,
                        "    let cols := parents.map (fun _ => (0 : Nat))\n"
                        "    return cols.map (idColumn rows)\n"),
        "refinement": "drawing every ancestor's filter values from column 0 is "
                      "EXACTLY the pre-change behaviour: a distinct-identity "
                      "ancestor is then filtered by the child's own identity "
                      "values, which differ from its, so the co-ordinated update "
                      "of that ancestor targets the wrong rows and leaves the "
                      "intended field unchanged.  This is the precise failure both "
                      "shipped F2P scenarios assert against (each reaches a single "
                      "distinct-identity ancestor and reads its field back), so a "
                      "faithful patch doing this would NOT resolve them — a "
                      "verify-not-resolve break.",
        "rationale": "REJECT from `out = (assignedColumns parents).map (idColumn "
                     "rows)`: at a distinct-identity ancestor the routing pins a "
                     "fresh column (1), but the impl draws from column 0, so the "
                     "post-image is violated.  Refuted at ONE distinct-identity "
                     "ancestor — the first-fresh-ancestor sub-domain, where this "
                     "rival diverges and the two ≥2-ancestor rivals below do not.",
        "witness": _TESTER +
                   "example : parentFilterIdsTester "
                   "[{ sharesChildPk := false }] [[10, 20]] = false := by\n"
                   "  decide\n",
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-sparse-columns",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps the shared-identity branch correct (column 0) and advances the
        # free column by TWO instead of one for a distinct-identity ancestor, so
        # distinct-identity ancestors land on columns 1, 3, 5, … instead of the
        # contiguous 1, 2, 3, ….  Agrees with the frozen routing for a list with
        # a single distinct-identity ancestor; diverges from the SECOND onward.
        # Written straight-line (a pure fold, no `while`) so its tester reduces.
        "module": _swap(_BASE, _IMPL,
                        "    let cols := (parents.foldl (fun (st : List Nat × Nat) p =>\n"
                        "        if p.sharesChildPk then (st.1 ++ [0], st.2)\n"
                        "        else (st.1 ++ [st.2], st.2 + 2)) ([], 1)).1\n"
                        "    return cols.map (idColumn rows)\n"),
        "refinement": "spacing distinct-identity ancestors two columns apart makes "
                      "the second such ancestor's recorded column over-run the "
                      "fetched row, which carries exactly one column per "
                      "distinct-identity ancestor plus the child identity: the "
                      "second ancestor reads a column index past the row's end.  "
                      "Both shipped F2P scenarios reach a SINGLE distinct-identity "
                      "ancestor, so this rival agrees with the frozen solution on "
                      "them; its faithful patch diverges only on a tree with two "
                      "or more distinct-identity ancestors, where it reads past "
                      "the fetched row.  It is a reject because the frozen spec's "
                      "routing pins CONTIGUOUS columns for correctness on those "
                      "≥2-ancestor updates the modeled behaviour must also handle "
                      "(this is the dense-column strengthening the nagini sibling "
                      "carries); a rival verifying against a spec lacking that pin "
                      "would admit an impl that over-runs the fetched row.",
        "rationale": "REJECT from `out = (assignedColumns parents).map (idColumn "
                     "rows)`: the frozen routing assigns the second "
                     "distinct-identity ancestor column 2, the impl assigns it "
                     "column 3, so the mapped fetched columns differ there.  "
                     "Refuted at TWO distinct-identity ancestors — the sub-domain "
                     "`weak-all-column-0` cannot reach — and at a 4-column fetched "
                     "block, so `rows` is not held fixed across the battery.",
        "witness": _TESTER +
                   "example : parentFilterIdsTester "
                   "[{ sharesChildPk := false }, { sharesChildPk := false }] "
                   "[[0, 10, 20, 30]] = false := by\n"
                   "  decide\n",
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-const-column-1",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps the shared-identity branch correct (column 0) and assigns EVERY
        # distinct-identity ancestor the constant column 1 (no free-column
        # advance), so two distinct-identity ancestors collide on one column.
        # Agrees with the frozen routing for a single distinct-identity ancestor
        # (its column is 1 either way); diverges from the SECOND onward.
        # Written straight-line (a pure fold, no `while`) so its tester reduces.
        "module": _swap(_BASE, _IMPL,
                        "    let cols := (parents.foldl (fun (st : List Nat × Nat) p =>\n"
                        "        if p.sharesChildPk then (st.1 ++ [0], st.2)\n"
                        "        else (st.1 ++ [1], st.2)) ([], 1)).1\n"
                        "    return cols.map (idColumn rows)\n"),
        "refinement": "assigning every distinct-identity ancestor the same column "
                      "collides their filter values: two distinct-identity "
                      "ancestors would be filtered by ONE column's values, so the "
                      "second ancestor's co-ordinated update is constrained by the "
                      "first ancestor's identities and mis-updates its rows.  Both "
                      "shipped F2P scenarios reach a single distinct-identity "
                      "ancestor (its column is 1 under either routing), so this "
                      "rival agrees with the frozen solution on them; its faithful "
                      "patch diverges only on a tree with two or more "
                      "distinct-identity ancestors, where it corrupts the second "
                      "ancestor's update.  It is a reject because the frozen spec's "
                      "routing pins DISTINCT columns for correctness on those "
                      "≥2-ancestor updates; a rival verifying against a spec "
                      "lacking that pin would admit an impl that co-mingles two "
                      "ancestors' identity filters.",
        "rationale": "REJECT from `out = (assignedColumns parents).map (idColumn "
                     "rows)`: the frozen routing assigns the second "
                     "distinct-identity ancestor column 2, the impl assigns it "
                     "column 1, so the mapped fetched columns differ there (the "
                     "free column never advances).  A NEAR-MISS relative to the "
                     "sparse rival — it agrees with gold over a different part of "
                     "the domain — so it carries its own refutation point: TWO "
                     "distinct-identity ancestors at a 3-column fetched block, "
                     "distinct from the sparse rival's block.",
        "witness": _TESTER +
                   "example : parentFilterIdsTester "
                   "[{ sharesChildPk := false }, { sharesChildPk := false }] "
                   "[[0, 10, 20]] = false := by\n"
                   "  decide\n",
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-shared-consumes-column",
        "kind": "uniqueness",
        "expect": "reject",
        # The ONLY rival that turns on the shared-identity (`sharesChildPk :=
        # true`) branch.  It routes a shared-identity ancestor to column 0 —
        # CORRECT — but still CONSUMES the next free column, so every LATER
        # distinct-identity ancestor is shifted one column to the right.  The
        # returned column for a shared ancestor is indistinguishable from gold;
        # the damage is entirely in the accumulator's second component, which the
        # other three rivals hold fixed on this branch.
        "module": _swap(_BASE, _IMPL,
                        "    let cols := (parents.foldl (fun (st : List Nat × Nat) p =>\n"
                        "        if p.sharesChildPk then (st.1 ++ [0], st.2 + 1)\n"
                        "        else (st.1 ++ [st.2], st.2 + 1)) ([], 1)).1\n"
                        "    return cols.map (idColumn rows)\n"),
        "refinement": "consuming a fetched column for an ancestor that reuses the "
                      "child's identity means no value is ever fetched into that "
                      "column, yet the count of fetched columns is one short of "
                      "the highest index recorded: every distinct-identity "
                      "ancestor appearing AFTER a shared-identity one is pointed "
                      "one column past where its identity was actually placed, so "
                      "it filters on the wrong ancestor's values or reads past the "
                      "row's end.  Both shipped F2P scenarios reach exactly one "
                      "ancestor, so no shared ancestor PRECEDES a distinct one in "
                      "them and this rival agrees with the frozen solution there; "
                      "its faithful patch diverges on any tree that mixes the two "
                      "kinds in that order, which is precisely the ordering the "
                      "modeled routing exists to get right.  A rival verifying "
                      "against a spec lacking the 'reuse consumes nothing' pin "
                      "would mis-route every ancestor after a reused one.",
        "rationale": "REJECT from `out = (assignedColumns parents).map (idColumn "
                     "rows)`: the frozen routing does NOT advance the free column "
                     "for a shared-identity ancestor, so a following "
                     "distinct-identity ancestor takes column 1; this impl "
                     "advances it and assigns column 2.  This is the battery's "
                     "only rival that VARIES the `sharesChildPk` binder to `true` "
                     "— the other three attack the `false` branch, so a rival "
                     "mishandling only the shared branch's column accounting would "
                     "otherwise verify unnoticed.  Refuted at a mixed "
                     "[true, false] ancestor list, an input point no other witness "
                     "probes.",
        "witness": _TESTER +
                   "example : parentFilterIdsTester "
                   "[{ sharesChildPk := true }, { sharesChildPk := false }] "
                   "[[5, 9]] = false := by\n"
                   "  decide\n",
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.  The sibling battery has 6 SPEC cases (1
# soundness positive, 1 admissibility, 4 uniqueness rivals) plus 1 AXIOM_TESTS
# entry.  The sibling contracts two functions (`assign_columns`, `count_fresh`)
# over a per-flag chain; this bundle contracts ONE method whose single
# post-image folds the same routing over an ordered ancestor list.  The mapping:
#
#   sibling case                  -> here
#   ---------------------------------------------------------------------
#   pos-control-reshape           -> pos-control-reshape             PORTED
#   admiss-selfcall               -> admiss-fresh-column-nonzero     RE-AIMED
#   frame-mutate-chain            -> (none)                          VACUOUS
#   weak-all-column-0             -> weak-all-column-0               PORTED
#   weak-sparse-columns           -> weak-sparse-columns             PORTED
#   weak-const-column-1           -> weak-const-column-1             PORTED
#   ax-ref-assign-columns-…       -> (dropped: G-AX lane, not G-PBT)
#   (no sibling counterpart)      -> weak-shared-consumes-column     ADDED
#   (no sibling counterpart)      -> pos-control-loopfree-fold        ADDED
#
# PORTED (4): the reshape positive, and the three uniqueness rivals.  Each
#   nagini rival's ARGUMENT is carried over verbatim in spirit; the mechanics
#   are re-expressed over this carrier (an ordered `List Parent` and the
#   `stepCol` fold) rather than the sibling's per-flag chain, and each reject
#   case gains a machine-checked refutation witness with no sibling counterpart
#   (the sibling relies on Viper discharging the postcondition; a tactic-proof
#   backend needs the witness to attribute the rejection to the spec).
# RE-AIMED (admissibility): the sibling asserts BOTH precondition clauses hold
#   for a normal input.  No method here has a `require` clause, so that probe is
#   vacuous — nothing could exclude a normal input.  It is re-aimed at the
#   residual total-domain risk: that the post-image is degenerate at the
#   F2P-shaped point.  The case asserts the routing genuinely assigns a
#   distinct-identity ancestor a fresh, non-zero column (the load-bearing fact
#   the whole fix turns on).
# ADDED (2), both for reasons specific to this carrier rather than the sibling's:
#   * `weak-shared-consumes-column` closes a BINDER-COVERAGE gap.  All three
#     ported rivals hold `sharesChildPk` at `false`, because that is where the
#     sibling's chain-flag rivals live.  A binder every witness holds at one
#     value is a binder no rival was built to abuse: a rival mishandling only
#     the shared-identity branch would verify and the battery would never
#     notice.  This rival keeps the shared branch's RETURNED column correct and
#     corrupts only its column ACCOUNTING, so it is refutable only at a mixed
#     ancestor list — the input point that varies the binder.
#   * `pos-control-loopfree-fold` is the `witness_reference` shipped as its own
#     verify case, so the battery itself records that loop-freeness is not the
#     property any rival is rejected for (see WITNESS MECHANICS).
# VACUOUS (1): the sibling's MANDATORY frame-mutation rival overwrites its
#   read-only input through a fractional heap permission.  This backend is
#   referentially transparent, this bundle declares no `mut` binder on any
#   input, and there is no heap or aliasing — so there is no read-only input to
#   overwrite and no substitute probe.  Reported, not fabricated.
# DROPPED (1): the sibling's AXIOM_TESTS entry re-runs a real-callee equivalence.
#   The axiom lane is G-AX's job; this bundle declares no axiom (see mapping.md:
#   G-AX is skip), and the G-PBT gate ignores AXIOM_TESTS regardless.
# NO soundness positive was dropped for a proof that would not close: both
#   verify cases were built and measured green before shipping.
#
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``parents.length - i``). A rival
#   that loops without a measure is refused outright (``Decreasing annotations
#   are required in total correctness semantics``), and a rival that supplies a
#   CONSTANT measure to dodge that is refused on the measure's own goal (``case
#   «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
#   a real build. Divergence therefore does not discharge the ``ensures``
#   clauses vacuously. It is still not shipped as a G-PBT reject case, and the
#   reason is the witness contract rather than a spec weakness. A reject case
#   must carry a witness that ELABORATES against the rival, and neither diverging
#   shape gets past that. With NO measure the descent obligation fails at the
#   ``method`` itself, ahead of any appended tester, and the witness file retains
#   the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
#   module does not compile at all. With a measure that does not decrease the
#   refusal moves to the ``prove_correct`` site, which IS stripped, so that module
#   does elaborate; but the rival's post-image is then an unreduced
#   ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
#   ``decreasingGadget``, which the kernel will not normalise to a value a
#   concrete-input tester can decide. Either way the gate returns
#   ``witness-unproven``, an inconclusive outcome. Measured through the
#   gate's own ``_check_witness``, even ``example : True := trivial`` comes
#   back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
#   and would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# On the ≥2-ancestor rivals (weak-sparse-columns / weak-const-column-1 /
#   weak-shared-consumes-column): both shipped F2P scenarios reach a SINGLE
#   ancestor, so these rivals agree with the frozen solution on the shipped
#   tests and their faithful patches would pass them.  They are genuine rejects
#   all the same: the frozen routing pins CONTIGUOUS, DISTINCT columns and pins
#   that a reused column consumes nothing, which are real correctness
#   requirements on any update coalescing two or more ancestors, and the frozen
#   spec rejects them at exactly those inputs.  This is the sibling's
#   dense-index (D1) strengthening carried over faithfully; it is called out
#   here rather than dressed up as a shipped-test failure.
#
# COVERAGE.  One obligation (`parentFilterIds`): defended by three verify cases
#   and attacked by four reject rivals.  Its single ensures clause is attacked by
#   every rival, and each independent component of the routing is attacked by
#   some rival: the fresh-vs-reused CHOICE (weak-all-column-0), the DENSITY of
#   the fresh columns (weak-sparse-columns), their DISTINCTNESS
#   (weak-const-column-1), and the free-column ACCOUNTING on the reused branch
#   (weak-shared-consumes-column).  Both input binders are varied across the
#   reject witnesses: `parents` takes a one-ancestor list, two
#   two-distinct-ancestor lists and one MIXED [true, false] list — so
#   `sharesChildPk` is exercised at BOTH values — and `rows` takes four distinct
#   fetched blocks (widths 2, 4, 3, 2).  pts = 4 distinct input points.
AXIOM_TESTS = []
