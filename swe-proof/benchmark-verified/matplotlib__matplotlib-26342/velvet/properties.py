"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-26342 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct setPaths`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method over a mutable container plus a
read-only supplied collection:

  setPaths (mut coll : PathContainer) (newPaths : List Int)
      return (out : Except Unit Unit)
    ensures out = Except.ok ()
    ensures coll.paths = newPaths
    ensures getPaths coll = newPaths
    ensures coll.stale = true

``PathContainer`` carries only the two aspects a path-replacement request can
touch: the ordered collection it holds (``paths``) and the redraw-needed flag
(``stale``). ``out`` reports whether the request COMPLETED (``Except.ok ()``) or
was REFUSED (``Except.error ()``). There is no ``require`` clause, so the
admitted domain is total: the post-image must hold for EVERY container and every
supplied collection.

FOUR independent top-level clauses, each load-bearing:
  (1) ``out = Except.ok ()`` — the request must COMPLETE, not refuse. This is
      the core transition the change effects (a request that used to be refused
      now succeeds); a body that reports a refusal fails here.
  (2) ``coll.paths = newPaths`` — the container thereafter holds exactly the
      supplied collection.
  (3) ``getPaths coll = newPaths`` — a subsequent paths query returns precisely
      what was stored (definitionally ``coll.paths``, so (2) and (3) fall
      together, but both are stated top-level and both are attacked).
  (4) ``coll.stale = true`` — the container is marked as needing a redraw.

ADVERSARIAL READ of the sibling classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: ``newPaths`` is an
    immutable value (NOT a ``mut`` binder), there is no heap and no aliasing, so
    there is no read-only input to mutate and no substitute probe to build.
    Reported vacuous, not fabricated (see footer).
  * COPY-NOT-IDENTITY — VACUOUS on this backend. The sibling's headline
    uniqueness rival stores a fresh object with identical CONTENTS and is
    refuted only by reference IDENTITY. This carrier is ``List Int``, compared by
    VALUE: there is no term denoting "a different object with equal contents", so
    the distinction the sibling's identity clause keeps collapses here and no
    discriminating witness exists. Dropped, not fabricated (see footer).
  * PARTIAL-DOMAIN / VALUE — APPLIES: rivals right on part of the domain but
    diverging on a sub-domain (a container that stores nothing, one that omits
    the redraw flag, one that reports a refusal). Each is refuted at a concrete
    point that varies the ``newPaths`` and ``coll`` binders, so no binder is
    pinned across the battery.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``setPathsTester coll newPaths = false`` says the extracted program's observable
(the mutated container's ``paths``/``stale`` and the returned outcome) violates
the method's postcondition at that concrete input. Checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. ``PathContainer`` derives ``DecidableEq``, so every witness closes by
``decide``.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the operation is
modeled directly over the carrier, and the only named callee ``getPaths`` is a
pure ``def``, not an axiom). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26342"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap) --------
_GOLD_IMPL = (
    "    coll := { coll with paths := newPaths, stale := true }\n"
    "    return Except.ok ()"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a case that introduces an in-region `assert` may
# ---- retune the tactic script without touching the spec statement or dropping
# ---- the obligation. Unique in the file.
_GOLD_PROOF = "prove_correct setPaths by\n  loom_solve\n  simp [getPaths]"

assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body."""
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped.
# ---- The outcome clause `out = Except.ok ()` needs equality on the report
# ---- carrier `Except Unit Unit` to be decidable, which the tester machinery
# ---- cannot synthesize on its own, so the instance is derived first. It is an
# ---- instance, not an assumption (no `axiom`/`sorry`/`native_decide`), and the
# ---- frozen solution rejects these witnesses all the same.
_DEC_EXCEPT = "deriving instance DecidableEq for Except\n\n"


def _tester(body):
    return (_DEC_EXCEPT +
            "extract_program_for setPaths\n"
            "prove_precondition_decidable_for setPaths\n"
            "prove_postcondition_decidable_for setPaths\n"
            "derive_tester_for setPaths\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify; else the post-image is SPEC-TOO-STRONG. The two
    # container aspects are written in the OTHER order within the single
    # record update (the sibling's assignment-reorder). Observationally
    # identical final state on all four clauses, so the frozen tactic script
    # still discharges it — nothing new to prove.
    # =====================================================================
    {
        "id": "pos-control-reorder-fields",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    coll := { coll with stale := true, paths := newPaths }\n"
            "    return Except.ok ()"),
        "rationale": "a correct reshape (the redraw flag and the stored "
                     "collection written in the opposite order inside the same "
                     "record update) yields an identical final container on every "
                     "input and adds no new proof obligation, so all four clauses "
                     "(outcome ok, stored = supplied, query = supplied, stale "
                     "true) still discharge under the frozen script; if it failed "
                     "to verify the spec would be SPEC-TOO-STRONG on impl shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous (nothing could exclude the
    # F2P-shaped input). Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is UNSATISFIABLE / degenerate at the
    # interesting point. This case discharges an in-region `assert` pinning the
    # post-image's value at an F2P-shaped input — a container into which a
    # concrete non-empty collection has been stored must report that exact
    # collection back AND carry the redraw flag. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; the assert is
    # live (a false claim about the same point leaves an unsolved goal).
    # =====================================================================
    {
        "id": "admiss-nondegenerate-store-and-stale",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (getPaths { paths := ([7, 8] : List Int), stale := true } "
            "= [7, 8] ∧\n"
            "       ({ paths := ([7, 8] : List Int), stale := true } "
            ": PathContainer).stale = true))\n"
            + _GOLD_IMPL,
            "prove_correct setPaths by\n"
            "  loom_solve <;> simp [getPaths] <;> decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P corner: a container holding a concrete non-empty "
                     "collection must report that exact collection from a paths "
                     "query and must carry the redraw flag. The in-region assert "
                     "must discharge (else the obligation is unsatisfiable / "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so the "
                     "method's own `ensures` still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary BOTH
    # binders: `newPaths` over `[3]`, `[2]`, `[5, 6]` (and empty vs non-empty
    # matters for the stored-collection rival), and the initial `coll` over
    # distinct held collections / flag states.
    # =====================================================================
    {
        "id": "weak-refuse-request",
        "kind": "uniqueness",
        "expect": "reject",
        # Stores correctly and marks stale, but REPORTS A REFUSAL instead of a
        # completion. Isolates clause (1): clauses (2),(3),(4) all hold, only
        # the outcome is wrong.
        "module": _impl(
            "    coll := { coll with paths := newPaths, stale := true }\n"
            "    return Except.error ()"),
        "refinement": "a faithful counterpart that leaves the request REFUSED "
                      "(the pre-change behavior, where a path-replacement request "
                      "raised rather than completing) never installs the supplied "
                      "collection through the public entry point. The failing "
                      "test drives that entry point and observes the replacement "
                      "did not happen, so it still fails. It would NOT resolve.",
        "rationale": "REJECT from clause (1) `out = Except.ok ()`: the body "
                     "reports `Except.error ()` (a refusal) where the post-image "
                     "demands a completion. The store and flag are kept correct so "
                     "the ONLY failing clause is the outcome. If this verified the "
                     "spec would be SPEC-TOO-WEAK (it would admit the refuse-only "
                     "body). Refuted at `newPaths = [3]`.",
        "witness": _tester(
            "example : setPathsTester { paths := [1], stale := true } [3] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-skip-redraw-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Stores the supplied collection and completes, but leaves the redraw
        # flag CLEAR. Isolates clause (4): clauses (1),(2),(3) all hold, only
        # the flag is wrong.
        "module": _impl(
            "    coll := { coll with paths := newPaths, stale := false }\n"
            "    return Except.ok ()"),
        "refinement": "a faithful counterpart that stores the collection but "
                      "omits marking the container for redraw leaves the cached "
                      "rendering un-invalidated, so the figure is not redrawn with "
                      "the newly installed collection and the render-equality test "
                      "observes the stale image. It would NOT resolve.",
        "rationale": "REJECT from clause (4) `coll.stale = true`: the body leaves "
                     "the flag `false` where the post-image demands `true`. The "
                     "store and outcome are kept correct so the ONLY failing "
                     "clause is the flag. Refuted at `newPaths = [2]`, initial "
                     "container flag already clear.",
        "witness": _tester(
            "example : setPathsTester { paths := [0], stale := false } [2] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-store-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        # Completes and marks stale, but stores an EMPTY collection instead of
        # the supplied one. Isolates clauses (2)/(3): clauses (1),(4) hold; the
        # stored collection and the query both diverge whenever the supplied
        # collection is non-empty.
        "module": _impl(
            "    coll := { coll with paths := ([] : List Int), stale := true }\n"
            "    return Except.ok ()"),
        "refinement": "a faithful counterpart that installs an empty collection "
                      "instead of the supplied paths reproduces the 'replace with "
                      "nothing' failure at the value level: a subsequent paths "
                      "query returns no geometry, so the rendered figure differs "
                      "from the one drawn with the intended collection and the "
                      "render-equality test fails. It would NOT resolve.",
        "rationale": "REJECT from clauses (2)/(3) `coll.paths = newPaths` / "
                     "`getPaths coll = newPaths`: the body stores `[]`, so for any "
                     "non-empty supplied collection the stored collection and the "
                     "query both disagree with `newPaths`. The outcome and flag "
                     "are kept correct so the failure is squarely the "
                     "stored-collection clauses. Refuted at `newPaths = [5, 6]` "
                     "(non-empty, where empty ≠ supplied is observable).",
        "witness": _tester(
            "example : setPathsTester { paths := [4], stale := false } [5, 6] "
            "= false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals) contracting one function
# `install_geometry(self, new_items)` over a permission-bearing heap object with
# two load-bearing clauses (`self.items is new_items` by reference identity, and
# `self.out_of_date is True`). This bundle models the same operation over the
# purely-functional carrier `PathContainer` plus the read-only `newPaths`, and
# ADDS an explicit outcome clause (`out = Except.ok ()`) that the sibling could
# not express (it modeled the op as a `-> None` return with no refuse/complete
# observable). Every sibling case is accounted for below.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder-assignments        -> pos-control-reorder-fields   PORTED
#   admissibility-readonly-input-and-fields -> admiss-nondegenerate-store-and-stale RE-AIMED
#   frame-mutation-write-new-items          -> (none)                      VACUOUS
#   copy-not-identity                       -> (none)                      VACUOUS
#   skip-out-of-date-flag                   -> weak-skip-redraw-flag        PORTED
#   install-empty-wrong-object              -> weak-store-nothing          PORTED
#   (no sibling counterpart)                -> weak-refuse-request         ADDED
#
# 3 ported/re-aimed, 2 vacuous, 1 added.
#
# RE-AIMED (admissibility): the sibling Asserts the two load-bearing clauses hold
#   for an F2P-shaped input under its Requires. There is no `require` clause here,
#   so the "a normal input satisfies the precondition" reading is vacuous. The
#   case is re-aimed at proving the post-image is satisfiable AND non-degenerate
#   at the F2P corner (a container holding a concrete non-empty collection reports
#   it back and carries the redraw flag). The in-region assert is discharged
#   symbolically against concrete literals.
# VACUOUS (frame-mutation-write-new-items): the sibling's MANDATORY frame rival
#   writes into a read-only input held at Acc(list_pred(new_items), 1/2) and is
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: `newPaths` is an immutable value, NOT a `mut` binder; there is no
#   heap, no aliasing, and no permission system to trip. No read-only input to
#   overwrite and no substitute probe to build. Not fabricated.
# VACUOUS (copy-not-identity): the sibling's canonical uniqueness attack stores a
#   fresh list with identical contents and is refuted ONLY by reference identity
#   (`self.items is new_items` is FALSE for a copy). This carrier abstracts the
#   stored collection as `List Int`, compared by VALUE — mapping.md §2 records
#   that the operation stores the collection wholesale and G-CONF compares by
#   Python object identity, but at the Lean value level there is no term denoting
#   "a distinct object with equal contents": `coll.paths = newPaths` holds for any
#   value-equal collection, so the copy is observationally the gold store. The
#   distinction the sibling's identity clause keeps collapses on this carrier and
#   NO discriminating witness exists. Per the porting map this rival is dropped
#   (its abstraction collapses a distinction nagini's kept), not fabricated.
# ADDED (weak-refuse-request): the outcome clause `out = Except.ok ()` has no
#   sibling counterpart (the sibling had no refuse/complete observable). It is the
#   core of the modeled change — a request that used to be refused now completes —
#   so it is attacked directly: a body that stores correctly but reports a refusal
#   fails only that clause, with a machine-checked witness.
#
# BINDER / CLAUSE COVERAGE. All four independent top-level clauses are attacked:
#   (1) outcome by weak-refuse-request, (2)/(3) stored collection + query by
#   weak-store-nothing, (4) redraw flag by weak-skip-redraw-flag; and all four are
#   defended by the positive control and the admissibility case. The three reject
#   witnesses probe three DISTINCT inputs (pts=3):
#     coll={paths:[1],stale:true},  newPaths=[3]      weak-refuse-request
#     coll={paths:[0],stale:false}, newPaths=[2]      weak-skip-redraw-flag
#     coll={paths:[4],stale:false}, newPaths=[5,6]    weak-store-nothing
#   so `newPaths` is varied over [3], [2], and the non-empty [5,6] (empty vs
#   non-empty is exactly what makes the stored-collection divergence observable),
#   and the initial `coll` is varied over distinct held collections and both flag
#   states. Neither binder is pinned across the battery.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
#   axiom (the operation is modeled directly; `getPaths` is a pure `def`, not an
#   axiom), so there is nothing there to probe.
AXIOM_TESTS = []
