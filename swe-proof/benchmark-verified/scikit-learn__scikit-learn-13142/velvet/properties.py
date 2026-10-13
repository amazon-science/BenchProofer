"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13142 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct finalizeLabels`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  finalizeLabels (transientParams : Params) (storedParams : Params)
                 (labelsFor : Params → Labels)
      return (out : Labels)
    ensures out = reportedLabels storedParams labelsFor

The method models the label-finalization tail of a fit-then-report routine. It
reports the per-sample labels a caller receives; ``reportedLabels`` pins that
whole outcome as a total function of the method's own inputs:

  reportedLabels storedParams labelsFor = labelsFor storedParams

with ``labelsFor : Params → Labels`` the (opaque, unconstrained) label-computing
routine read as a pure function of the parameter set currently in force, and
``storedParams`` the parameter set the fitted object retains — the one a later,
separate label query against the same object reads. So the sole ``ensures`` pins
ONE load-bearing behaviour:

  * (P) the reported labels are ``labelsFor`` applied to ``storedParams`` — i.e.
        derived from the RETAINED parameter set, NOT from ``transientParams`` (a
        parameter set that may be in force partway through finalization but is
        not the one the object ends up storing), and produced by the label
        routine ITSELF, not fabricated. This is exactly the "fit-time labels
        agree with a later separate query" guarantee.

THREE INPUT binders of the method (none carries a ``require`` clause; the
post-image must hold for EVERY value of each):
  * ``transientParams`` — the leftover mid-finalization parameter set; the spec
        must be INDEPENDENT of it (a rival that reads it is wrong).
  * ``storedParams``    — the retained parameter set; the argument ``labelsFor``
        must be applied to.
  * ``labelsFor``       — the label-computing routine; the reported labels must
        be PRODUCED BY it, not by some other means.

ADVERSARIAL READ of the weakness classes (mirrors the nagini sibling; see the
footer for the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling's
    MANDATORY frame-mutation rival keeps the correct body verbatim then writes
    back into a read-only sequence input carrying only a fractional heap
    permission and is rejected for INSUFFICIENT PERMISSION. Lean and Velvet are
    referentially transparent: every parameter is an immutable value, this
    bundle declares no ``mut`` binder on an input, and there is no heap and no
    aliasing. There is no read-only input to overwrite and no permission system
    to trip, so the class is vacuous. No substitute is fabricated.
  * TERMINATION / DIVERGENCE - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * SELECTION / EARLIEST-MAX (nagini P1: ``inst.config == best_config(...)``) —
    NO COUNTERPART on this carrier. The nagini sibling contracts the whole
    fit-and-label routine, INCLUDING the trial-selection loop that picks the
    best-scoring attempt; its ``drop-selection`` and ``strict-tiebreak`` rivals
    attack that selection. THIS bundle models only the label-finalization tail:
    which attempt won is abstracted into the free input ``storedParams`` (the
    retained set), so the selection loop is not modeled and its rivals have no
    counterpart. This is carrier narrowing, not an evasion.
  * UNGROUNDED-ORACLE ECHO — N/A. ``reportedLabels`` is a fully unfolded ``def``
    over the method's own arguments (the ``axioms`` region is empty — no opaque
    answer key to echo). ``labelsFor`` is a FREE FUNCTION input, not an oracle:
    the spec quantifies over EVERY function it could be, so the only way to
    satisfy the post-image is to apply the caller's own ``labelsFor`` to the
    caller's own ``storedParams``. The honest control does exactly that.
  * VALUE / ORDER (which parameter set the labels are derived from) — carries
    the reject lane. The single clause pins the reported labels to
    ``labelsFor storedParams``; a rival that derives them from ``transientParams``
    (the pre-patch position) or that fabricates labels without going through
    ``labelsFor`` diverges from the post-image at a concrete input.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop):
its extracted program reduces fully under ``decide``. Each reject rival carries a
machine-checked refutation ``witness`` — a Velvet tester statement
``finalizeLabelsTester <transient> <stored> <labelsFor> = false`` at ONE concrete
input, checked in a file whose ``prove_correct`` block has been stripped so no
tactic script can mask the verdict. Although ``labelsFor`` is opaque in the spec,
a witness need not condition on it: it INSTANTIATES ``labelsFor`` with a concrete
function literal (``fun p => [p]`` / ``fun _ => [9]``), so ``decide`` computes
both the rival's answer and ``reportedLabels`` in full — no hypothesis, so no
consistency obligation. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival and FAILS
(``decide`` proves the proposition false) against the frozen solution, so each
rejection is a genuine spec refutation and not mechanical tactic breakage.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; the label routine is the FREE input ``labelsFor`` (no contract to
check against a real callee — no G-AX), and ``reportedLabels`` is a language-level
``def``. Nothing in the proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13142"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The whole frozen impl body (marker lines included),
# ---- verbatim from Solution.lean. Every rival and reshape edits ONLY this block
# ---- (and, for reshapes/admissibility, the elided `prove_correct` tactic body),
# ---- so the spec view is untouched and same_spec holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- Make the stored parameter set current FIRST, then compute the labels, so\n"
    "    -- the reported labels are derived from the stored parameters and agree with a\n"
    "    -- later separate query — not from the transient parameter set.\n"
    "    let mut active := transientParams\n"
    "    active := storedParams\n"
    "    let out := labelsFor active\n"
    "    return out\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim (tactic body elided from the spec view). A reshape
# that changes the impl's syntactic form may retune THIS block; rivals leave it
# as-is (the rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct finalizeLabels by\n  loom_solve\n  simp_all [reportedLabels]"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# The impl-start marker line (unique); the admissibility case inserts an in-region
# `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness helper. The spec is a `method` contract, not a bare predicate, so
# ---- a witness reaches the post-image through Velvet's own tester machinery:
# ---- `finalizeLabelsTester <transient> <stored> <labelsFor> = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block is stripped. The
# ---- free function input `labelsFor` is instantiated with a concrete literal so
# ---- `decide` reduces the straight-line program in full.
def _witness(call):
    return (
        "extract_program_for finalizeLabels\n"
        "prove_precondition_decidable_for finalizeLabels\n"
        "prove_postcondition_decidable_for finalizeLabels\n"
        "derive_tester_for finalizeLabels\n\n"
        f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each derives the reported labels from the STORED parameter
    # set via `labelsFor`, only reshaping the executable surface, so the reproof
    # stays a short retune of the frozen script.
    # =====================================================================
    {
        "id": "pos-derive-from-stored-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the intermediate mutable local and apply the label
        # routine to `storedParams` directly. Same value on every input.
        "module": _impl_reproved(
            "    let out := labelsFor storedParams\n"
            "    return out",
            _PROOF),
        "rationale": (
            "applying the label routine directly to `storedParams` (dropping the "
            "intermediate mutable local) yields `labelsFor storedParams` on every "
            "input, so `out = reportedLabels storedParams labelsFor` still holds "
            "on the whole domain; the obligation statement is byte-identical and "
            "the frozen tactic script discharges it. A correct reshape must "
            "verify, else SPEC-TOO-STRONG on the shape of the finalization step."
        ),
    },
    {
        "id": "pos-stored-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the stored parameter set into an IMMUTABLE local `active`
        # (never mentioning the transient set), then derive the labels from it.
        # Same value flow; the reproof stays a retune of the frozen script.
        "module": _impl_reproved(
            "    let active := storedParams\n"
            "    let out := labelsFor active\n"
            "    return out",
            _PROOF),
        "rationale": (
            "binding the stored parameter set into an immutable local `active` "
            "(the transient set is never read) and deriving the labels from it "
            "leaves `out = labelsFor storedParams` unchanged, so "
            "`out = reportedLabels storedParams labelsFor` is unchanged; a correct "
            "reshape must verify, else SPEC-TOO-STRONG on the data-flow shape of "
            "the finalization step."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal multi-trial input satisfies
    # the precondition" probe is degenerate here (every input is in-domain). The
    # residual admissibility risk on a total-domain spec is that the post-image
    # is DEGENERATE at the interesting point — a routine whose reported labels did
    # not actually DEPEND on which parameter set they were derived from would read
    # like a live one. This case discharges an in-region `assert` pinning that the
    # modeled outcome genuinely SEPARATES two distinct parameter sets: deriving
    # from one set yields different labels than deriving from another (for a
    # label routine that distinguishes them). The rest of the impl is kept
    # verbatim so the method's own obligation still discharges; the proof is
    # retuned only to clear the extra assert goal.
    # =====================================================================
    {
        "id": "admiss-outcome-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (reportedLabels 1 (fun p => [p]) = [1] ∧\n"
            "       reportedLabels 0 (fun p => [p]) = [0] ∧\n"
            "       ([1] : List Nat) ≠ [0]))\n"
            "    let mut active := transientParams\n"
            "    active := storedParams\n"
            "    let out := labelsFor active\n"
            "    return out",
            "prove_correct finalizeLabels by\n  loom_solve <;> simp_all [reportedLabels]"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the interesting "
            "point: deriving the reported labels from parameter set 1 yields [1] "
            "while deriving them from parameter set 0 yields [0], and [1] ≠ [0], "
            "so which parameter set the labels come from genuinely CHANGES the "
            "outcome — the spec is not vacuously true. The in-region assert must "
            "discharge (else the outcome would be degenerate / independent of the "
            "parameter set, the whole content of the fix); the impl is kept "
            "verbatim so the method's own `ensures` still discharges."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-order-swap-transient",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch behaviour: derive the reported labels from the TRANSIENT
        # parameter set (the leftover mid-finalization set) instead of the stored
        # one. Correct only when the transient and stored sets coincide.
        "module": _impl(
            "    let out := labelsFor transientParams\n"
            "    return out"),
        "refinement": (
            "this reproduces the pre-patch behaviour: the reported labels are "
            "computed while the leftover mid-finalization parameter set is still "
            "in force, before the retained set is made current. Its faithful real "
            "counterpart reports labels derived from the leftover set while the "
            "object ends holding the retained set, so a later separate label query "
            "(which recomputes from the retained set) disagrees with the reported "
            "labels whenever the two sets differ — exactly the reported "
            "discrepancy the failing test asserts against. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = reportedLabels storedParams labelsFor`: the "
            "post-image pins the reported labels to `labelsFor storedParams`, but "
            "the rival returns `labelsFor transientParams`; these differ whenever "
            "the transient and stored parameter sets are distinguishable under "
            "`labelsFor`. Refuted at transientParams=0, storedParams=1, "
            "labelsFor=(fun p => [p]): the rival returns [0] where the post-image "
            "demands [1]. This moves the `transientParams` binder (which the spec "
            "must be independent of) off the stored value."
        ),
        "witness": _witness(
            "finalizeLabelsTester 0 1 (fun p => [p])"),
    },
    {
        "id": "weak-labels-not-from-routine",
        "kind": "uniqueness",
        "expect": "reject",
        # The label routine is bypassed entirely: the reported labels are
        # fabricated from the retained parameter set's identity instead of being
        # PRODUCED BY `labelsFor`. Attacks the `labelsFor` binder specifically —
        # the value is independent of which label routine the caller supplies.
        "module": _impl(
            "    let out := [storedParams]\n"
            "    return out"),
        "refinement": (
            "the reported labels are synthesized directly from the retained "
            "parameter set rather than obtained by running the unchanged "
            "label-computing routine on it. Its faithful real counterpart reports "
            "labels not produced by the label pipeline, so they cannot match the "
            "labels a later separate query (which does run that pipeline on the "
            "retained set) recomputes — the two paths disagree for any nontrivial "
            "label routine. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = reportedLabels storedParams labelsFor`: the "
            "post-image pins the reported labels to `labelsFor storedParams` — "
            "PRODUCED BY the supplied label routine — but the rival returns "
            "`[storedParams]`, a value that never applies `labelsFor` at all, so "
            "the two disagree whenever `labelsFor storedParams ≠ [storedParams]`. "
            "Refuted at transientParams=2, storedParams=3, labelsFor=(fun _ => "
            "[9]): the rival returns [3] where the post-image demands [9]. This "
            "moves the `labelsFor` binder to a constant function distinct from the "
            "other witness's `fun p => [p]`, demonstrating the spec's dependence "
            "on the caller's own label routine (which the order-swap rival, using "
            "an identity-shaped routine, does not attest)."
        ),
        "witness": _witness(
            "finalizeLabelsTester 2 3 (fun _ => [9])"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness — one of which is the MANDATORY frame-
# mutation rival) plus 2 AXIOM_TESTS probes. The sibling contracts the WHOLE
# fit-and-label routine over two READ-ONLY sequence inputs carrying fractional
# heap permissions, INCLUDING the trial-selection loop; THIS bundle models only
# the label-finalization TAIL, with the winning attempt abstracted into the free
# input `storedParams` and the label routine into the free function `labelsFor`.
# The "which parameter set are the reported labels derived from" surface carries
# across intact; the selection loop, the permission surface, and the two length
# facts do not exist here.
#
#   sibling case                     -> here                            disposition
#   -----------------------------------------------------------------------
#   frame-mutate-readonly-run_config -> (none)                          VACUOUS
#   drop-selection-keep-final-trial  -> (none)                          NO COUNTERPART
#   weak-order-swap-prepatch (P2)    -> weak-order-swap-transient        PORTED
#   strict-tiebreak-wrong-earliest   -> (none)                          NO COUNTERPART
#   pos-control-branch-reorder       -> pos-derive-from-stored-direct    PORTED (reshaped)
#   pos-control-tail-local-reshape   -> pos-stored-local-reshape         PORTED
#   admissibility-multitrial-self-call -> admiss-outcome-nondegenerate   RE-AIMED
#   (no sibling)                     -> weak-labels-not-from-routine      ADDED (binder cov.)
#   ax-sound-* / ax-contain-*        -> (none)                          DROPPED (G-AX lane)
#
# 3 ported, 1 re-aimed, 1 net-new, 1 vacuous, 2 no-counterpart, 2 axiom-lane
# dropped. No case was dropped because its proof was hard.
#
# VACUOUS (frame-mutate-readonly-run_config): the sibling's MANDATORY frame-
#   mutation rival keeps the correct body verbatim then writes back into a
#   read-only sequence input granted only at half permission, and must be
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: every parameter is an immutable value, the method declares no
#   `mut` binder on an input, and there is no heap and no aliasing. There is no
#   read-only input to overwrite and no permission system to trip, so the class
#   is vacuous. No substitute is fabricated.
# NO COUNTERPART (drop-selection-keep-final-trial, strict-tiebreak-wrong-earliest):
#   both attack the sibling's clause (P1) inst.config == best_config(...), i.e.
#   the trial-SELECTION loop that picks the earliest-highest-scoring attempt.
#   THIS bundle does not model that loop at all — which attempt won is abstracted
#   into the free input `storedParams` (the retained set). With no selection loop
#   in the modeled surface there is no selection to get wrong, so these rivals
#   have no counterpart here. This is carrier narrowing (the Lean-family bundle
#   models only the purely functional finalization tail), not an omission of a
#   hard case. Reported per the porting map.
# PORTED (weak-order-swap-transient): the sibling's (P2) order-swap rival — the
#   literal pre-patch — persists the best set correctly but returns the labels of
#   the TRANSIENT final-trial set. Here the selection is abstracted away, so the
#   port keeps the essence: derive the reported labels from `transientParams`
#   instead of `storedParams`. Refuted where the two sets differ.
# PORTED-RESHAPED (pos-derive-from-stored-direct): the sibling's branch-reorder
#   positive control rewrites a loop guard into a logically-identical surface
#   form. This backend's frozen impl is straight-line (no loop / no guard), so
#   the exact reshape does not exist; the reshape SPIRIT — "structurally
#   different, behaviourally identical" — is carried by dropping the intermediate
#   mutable local and applying the label routine to `storedParams` directly.
# PORTED (pos-stored-local-reshape): the sibling's cheapest-honest-tail positive
#   control reads the persisted config into a local and derives from it. Ported
#   directly: bind the stored set into an immutable local `active` and derive the
#   labels from it. Preserves the derive-from-stored order (the content of the
#   fix); same value flow.
# RE-AIMED (admissibility): the sibling's self-call establishes the precondition
#   admits a normal multi-trial input. This backend's method has NO precondition
#   and no permission surface, so that probe is degenerate (every input is
#   in-domain). It is re-aimed at the residual total-domain risk — that the
#   outcome is DEGENERATE (independent of which parameter set the labels are
#   derived from) — via an in-region assert that deriving from two distinct sets
#   yields two distinct label vectors, so the spec is non-vacuous exactly on the
#   axis the fix cares about.
# ADDED (weak-labels-not-from-routine): the sibling never isolates a "labels not
#   produced by the label routine" rival — its `labels_of` is grounded by purity
#   and the sole non-selection attack IS the order-swap. Here `labelsFor` is a
#   FREE FUNCTION input, so a rival that fabricates labels WITHOUT applying it
#   (returning `[storedParams]`) attacks the `labelsFor` binder specifically. The
#   order-swap rival uses an identity-shaped label routine (`fun p => [p]`) and so
#   never attests that the reported labels must be PRODUCED BY the caller's own
#   routine; this rival, with a constant routine (`fun _ => [9]`), does. A binder
#   no witness moves is a binder no rival was built to abuse.
# DROPPED (ax-sound-*, ax-contain-*): the sibling's AXIOM_TESTS probes validate
#   the label-primitive purity + selection deep model against the real callee.
#   This bundle has NO axiom and no deep-model reference (meta.json axioms=[]; the
#   label routine is the free input `labelsFor`, the selection is abstracted into
#   `storedParams`), so there is no axiom lane to mirror. The axiom lane is G-AX's
#   job and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the method's input binders
#   (pts = 2 distinct input points):
#     transientParams — 0 (order-swap), 2 (labels-not-from-routine): varied, and
#         the order-swap witness holds it DISTINCT from storedParams so the spec's
#         required INDEPENDENCE of it is exercised (the rival that reads it is
#         wrong exactly there).
#     storedParams    — 1 (order-swap), 3 (labels-not-from-routine): varied; the
#         post-image's dependence on it is exercised by both.
#     labelsFor       — (fun p => [p]) (order-swap), (fun _ => [9])
#         (labels-not-from-routine): varied across an identity-shaped routine and
#         a constant routine, so the spec's dependence on the caller's OWN label
#         routine is demonstrated (the labels-not-from-routine rival is wrong
#         precisely because it ignores `labelsFor`).
#   The single top-level clause `out = reportedLabels storedParams labelsFor` is
#   attacked from both independent directions: wrong parameter-set ARGUMENT
#   (order-swap: transient vs stored) and wrong (missing) label-routine
#   APPLICATION (labels-not-from-routine). No two rivals share a witness.
#
# AXIOM_TESTS: empty. No axiomatized callee to probe; this gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []
