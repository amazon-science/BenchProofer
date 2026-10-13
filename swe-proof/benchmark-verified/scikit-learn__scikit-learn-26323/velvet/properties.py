"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-26323 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides — so ``markers.same_spec``
holds and the ``prove_correct`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates).

DEFENDED SURFACE (one contracted method over a list of listed sub-components and
one designated extra component):

  collectBroadcastTargets (listed extra)
      ensures out = broadcastTargets listed extra                        -- master
      ensures isReal extra = true  → out = selectReal listed ++ [extra]  -- C-extra-real
      ensures isReal extra = false → out = selectReal listed             -- C-extra-marker

The method computes the ordered list of sub-components a configuration action is
broadcast to. Desired behaviour: keep every REAL listed sub-component, in order,
dropping the placeholder markers (``selectReal``), and THEN also include the
designated extra component when it too is real — never when it is a marker. The
distinction each clause reacts to is marker-vs-real; the per-component action
itself factors out (it is applied identically to every selected component), so
the whole observable is exactly WHICH components appear in ``out`` and IN WHAT
ORDER — the master clause is an equality on the list, so it pins position as
well as membership.

The two INPUT binders are both free (no ``require`` clause, no ``mut`` binder):
  * ``listed`` — the listed sub-components; ``selectReal`` keeps the real ones
                 in order and drops the markers, so the CONTENTS
                 (marker-vs-real), the LENGTH and the ORDER all drive ``out``;
  * ``extra``  — the designated extra component; its marker-vs-real status
                 decides whether it is appended after the listed selection.
The post-image must hold for EVERY value of each, which is what makes the
partial-domain rivals below refutable at concrete points.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling's
    frame attack RECLASSIFIES a marker as a real component (mutating the
    classification field) so the per-component clauses hold vacuously, and is
    rejected by the classification-preservation postcondition. On this carrier
    the marker-vs-real status is a PURE total function ``isReal`` of an immutable
    ``Component`` value: there is no mutable classification field to overwrite,
    the inputs are referentially-transparent read-only values, and this bundle
    declares no ``mut`` binder — so there is no frame to pin and no substitute
    probe to fabricate. Reported as an omission, not faked.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image ``broadcastTargets`` /
    ``selectReal`` are total, fully-unfolded functions of the method's own
    arguments (concrete ``def``s in the ``pure`` region; the ``axioms`` region
    declares NO ``axiom`` and there is no A-reference deep model). There is no
    opaque answer key an echo could carry — the unique satisfier IS the
    selection. The honest grounded controls are the ``pos-*`` reshapes.
  * CONTROL-FLOW-EFFECT — N/A. The method is a pure value-returning query with no
    raise / return-vs-fallthrough branch and no side effect invisible to the
    value abstraction (the whole returned list IS the observable).
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
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * PARTIAL-DOMAIN / VALUE / ORDER — the real attacks. The ensures rejects any
    rival that puts the wrong components — or the right components in the wrong
    membership or the wrong ORDER — in ``out``. The rivals split the domain on
    the boundary the issue is about (whether the extra component is broadcast to,
    and whether the marker exclusion is honoured) and additionally attack the
    positional content of the master equality.

WITNESS MECHANICS ON THIS BUNDLE (``witness_reference``, and why it is required).
The frozen impl keeps a backward ``while`` loop. Under
``loom.semantics.choice "demonic"`` the loop's fixpoint elaborates through
``Classical.choice``, which the kernel cannot unfold, so ``decide`` against the
FROZEN solution is stuck for EVERY claim — true or false. Measured here: the
witness ``…Tester [Component.real 1] (Component.real 0) = false`` and the exact
OPPOSITE claim (``= true``) both fail against gold with the identical

    Tactic `decide` failed for proposition … because its `Decidable` instance …

so the gold-side exit code carries NO information and "fails on gold" would
attest to a refutation that was never performed. Every reject case therefore
names a ``witness_reference``: ``_REF``, a straight-line loop-free implementation
of the SAME frozen spec which VERIFIES (checked: exit 0, and it closes under the
frozen tactic script unchanged) and which DOES reduce. Against ``_REF`` each
witness fails with

    Tactic `decide` proved that the proposition … is false

i.e. a genuine decided refutation, and the same-input TRUE claim SUCCEEDS against
``_REF`` (exit 0) — so the reference decides both directions and is a real
discriminator rather than an impl that simply fails everything. ``_REF`` is also
shipped as the ``expect="verify"`` case ``pos-straightline-reference``, so the
battery itself records that loop-freeness is not what any rival is rejected for.
Every rival/reference witness build was run out-of-band with
``scripts/lean_verify.sh`` before shipping.

AXIOM lane: EMPTY. ``meta.json`` declares no ``axiom`` and no A-reference deep
model (the per-component configuration action is applied identically to every
selected component and factors out as an R refinement, not a contract about an
outside callee), so there is nothing for the axiom lane to probe and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-26323"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end`, INCLUDING the nested invariants. Every rival
# and every reshape edits ONLY this block (and, for reshapes/admissibility, the
# elided `prove_correct` tactic body), so the spec view is untouched and
# same_spec holds by construction.
_IMPL = """\
    -- impl-start
    -- Walk the listed sub-components, keeping the real ones (placeholder markers
    -- are skipped). Then, after the listed components, also include the
    -- designated extra component when it is a real component — the placeholder
    -- markers are the only values excluded there too.
    let mut result : List Component := []
    let mut i := listed.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ listed.length
      invariant result = selectReal (listed.drop i)
      done_with i = 0
      decreasing i
    do
      let c := listed[i - 1]!
      result := (if isReal c then [c] else []) ++ result
      i := i - 1
    result := result ++ (if isReal extra then [extra] else [])
    return result
    -- impl-end"""

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# retunes THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not by the tactic script).
_PROOF = """\
prove_correct collectBroadcastTargets by
  loom_solve
  all_goals simp_all [broadcastTargets]
  all_goals (rw [selectReal_drop_step listed i (by omega) (by omega)]; simp_all)"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# A proof script robust to a moderately reshaped loop body / added assert VC: it
# discharges the loop step where present, clears a decidable assert goal, and
# otherwise closes by unfolding the fold. Used by reshapes that alter the
# do-block or add an in-region assert.
_PROOF_RETUNED = """\
prove_correct collectBroadcastTargets by
  loom_solve <;>
    (try (rw [selectReal_drop_step listed i (by omega) (by omega)])) <;>
    (try decide) <;>
    (try (split <;> simp_all)) <;>
    simp_all [broadcastTargets, selectReal]"""


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, _PROOF_RETUNED)


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE. A straight-line, loop-free implementation of the SAME
# frozen spec: it computes the selection directly instead of iterating, so its
# extracted program REDUCES under `decide` where the frozen loop's
# `Classical.choice` fixpoint does not. It is the subject every reject witness is
# refuted against (`witness_reference`), because the frozen solution cannot
# decide anything and its exit code would therefore attribute nothing.
#
# Verified out-of-band: builds exit 0 (correct — it satisfies the spec), and it
# closes under the FROZEN tactic script with no reproof at all. Also shipped
# below as the expect="verify" case `pos-straightline-reference`, so the battery
# records that loop-freeness is not the reason any rival is rejected.
# ---------------------------------------------------------------------------
_REF = _impl(
    "    let out := selectReal listed ++ (if isReal extra then [extra] else [])\n"
    "    return out")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `collectBroadcastTargetsTester args = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block is stripped, so no tactic script can mask
# ---- the verdict. Every argument is a concrete `Component` constructor literal
# ---- so `decide` reduces fully (the carrier derives DecidableEq). No witness
# ---- binds a hypothesis — every refutation is at literal inputs — so the
# ---- gate's hypothesis-consistency probe is trivially satisfied (there are no
# ---- assumptions that could be jointly unsatisfiable).
_TESTER = ("extract_program_for collectBroadcastTargets\n"
           "prove_precondition_decidable_for collectBroadcastTargets\n"
           "prove_postcondition_decidable_for collectBroadcastTargets\n"
           "derive_tester_for collectBroadcastTargets\n\n")


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-named-tail-locals",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the per-step kept fragment (`keep`) and the trailing
        # extra fragment (`tail`) to named locals instead of writing them inline.
        # Same value flow on every input; observationally identical. Proof
        # retuned (the do-block changed shape).
        "module": _impl_reproved(
            "    let mut result : List Component := []\n"
            "    let mut i := listed.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ listed.length\n"
            "      invariant result = selectReal (listed.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := listed[i - 1]!\n"
            "      let keep := if isReal c then [c] else []\n"
            "      result := keep ++ result\n"
            "      i := i - 1\n"
            "    let tail := if isReal extra then [extra] else []\n"
            "    result := result ++ tail\n"
            "    return result"),
        "rationale": "hoisting the per-step kept fragment and the trailing extra "
                     "fragment into named locals leaves the selection and the "
                     "append unchanged, so `out = broadcastTargets listed extra` "
                     "still holds and both extra-arm clauses hold; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-isreal-guard-swap",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: rewrite the extra append as an explicit if/else over the same
        # `isReal extra` guard (`then result ++ [extra] else result`) instead of
        # appending a possibly-empty singleton. Same result on both branches. The
        # frozen loop and its invariant are untouched.
        "module": _impl_reproved(
            "    let mut result : List Component := []\n"
            "    let mut i := listed.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ listed.length\n"
            "      invariant result = selectReal (listed.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := listed[i - 1]!\n"
            "      result := (if isReal c then [c] else []) ++ result\n"
            "      i := i - 1\n"
            "    result := if isReal extra then result ++ [extra] else result\n"
            "    return result"),
        "rationale": "expressing the extra append as an explicit if/else on the "
                     "same `isReal extra` guard yields `result ++ [extra]` when "
                     "the extra is real and `result` otherwise — pointwise equal "
                     "to appending the possibly-empty singleton — so the "
                     "post-image is unchanged; must verify.",
    },
    {
        # The witness reference, shipped as a first-class positive. Its role in
        # the reject lane is only sound if it really does satisfy this spec, so
        # the battery asserts that here rather than leaving it implicit: this
        # case records that the loop-free shape VERIFIES, which is what makes
        # "the witness fails against _REF" evidence about the SPEC and not about
        # loop-freeness. (The gate independently re-checks the reference, but a
        # reader of the manifest should not have to take it on faith.)
        "id": "pos-straightline-reference",
        "kind": "soundness",
        "expect": "verify",
        "module": _REF,
        "rationale": "the loop is replaced by the direct expression it computes: "
                     "`selectReal listed ++ (if isReal extra then [extra] else "
                     "[])` IS `broadcastTargets listed extra` by definition, so "
                     "the master clause holds by unfolding and both extra-arm "
                     "clauses follow by the same case split; it verifies under "
                     "the frozen tactic script unchanged. Doubles as the "
                     "`witness_reference` for every reject case, so this case is "
                     "what certifies that refuting a witness against it is "
                     "evidence about the spec rather than about loop-freeness.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous: nothing
    # could exclude an F2P-shaped input. The residual admissibility risk on a
    # total domain is that the post-image is UNSATISFIABLE / DEGENERATE at the
    # interesting point — a spec no impl can meet reads exactly like a spec
    # every impl meets. This case discharges an in-region assert, at concrete
    # F2P-shaped points, that the selection is NON-DEGENERATE: a REAL extra with
    # an empty listed contributes exactly that extra (so the extra IS broadcast
    # to — the behaviour the failing test demands), and a MARKER extra alongside
    # a MARKER listed contributes nothing. The surrounding impl is kept verbatim
    # so the method's own obligation still discharges; the proof body is retuned
    # only to clear the extra `decide` goal (allowed — the tactic body is elided
    # from the spec view). The assert is live: a false claim about the same
    # points leaves an unsolved goal (checked out-of-band).
    # =====================================================================
    {
        "id": "admiss-selection-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, "    -- impl-start\n",
                  "    -- impl-start\n"
                  "    assert (with_name_prefix `admiss\n"
                  "      (broadcastTargets [] (Component.real 0) = [Component.real 0] ∧\n"
                  "       broadcastTargets [Component.marker] Component.marker = []))\n"),
            _PROOF, _PROOF_RETUNED),
        "rationale": "the post-image is satisfiable AND non-degenerate at concrete "
                     "F2P-shaped points: a real extra with an empty listed is "
                     "broadcast to (contributes exactly that extra), and a marker "
                     "extra alongside a marker listed contributes nothing — the "
                     "two behaviours the failing test distinguishes. The in-region "
                     "assert must discharge (else the obligation is unsatisfiable / "
                     "degenerate at the interesting point); the impl is kept "
                     "verbatim so `out = broadcastTargets listed extra` discharges "
                     "too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a straight-line COMPUTABLE impl (so its
    # witness reduces under `decide`), refuted at a concrete input by a witness
    # checked against `_REF` (the frozen loop decides nothing — see the module
    # docstring), and each carries the refinement argument that its faithful
    # real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-drop-extra",
        "kind": "uniqueness",
        "expect": "reject",
        # THE canonical attack — the pre-patch behaviour: broadcast only to the
        # real listed sub-components and NEVER to the designated extra, even when
        # the extra is a real component.
        "module": _impl(
            "    let out := listed.filter isReal\n"
            "    return out"),
        "refinement": "this is the pre-patch behaviour: the extra designated "
                      "component is never included in the broadcast, so a real "
                      "extra sub-component is left unconfigured and its output "
                      "container is wrong when the results are gathered — exactly "
                      "the failing non-regression scenario. A faithful counterpart "
                      "that keeps omitting the extra reproduces the pre-patch "
                      "behaviour, so the failing test still fails. It does NOT "
                      "resolve; a verifying rival would be a true "
                      "verify-does-not-resolve break.",
        "rationale": "REJECT from the master clause `out = broadcastTargets listed "
                     "extra` and from `isReal extra = true → out = selectReal "
                     "listed ++ [extra]`: a real extra must be appended and this "
                     "rival drops it. Refuted at a REAL extra with a real listed "
                     "component (the exact antecedent of the extra-real clause).",
        "witness": _witness(
            "collectBroadcastTargetsTester [Component.real 1] (Component.real 0)"),
        "witness_reference": _REF,
    },
    {
        "id": "weak-extra-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the marker guard on the extra: appends the designated extra
        # UNCONDITIONALLY, even when it is a placeholder marker.
        "module": _impl(
            "    let out := listed.filter isReal ++ [extra]\n"
            "    return out"),
        "refinement": "drops the marker guard on the extra: the designated extra "
                      "is broadcast to even when it is a placeholder marker. Its "
                      "faithful counterpart applies the per-component configuration "
                      "action to a placeholder marker (a routing string), which has "
                      "no such action and raises at configuration time — breaking "
                      "both the failing scenario and the passing marker-remainder "
                      "scenarios. It does NOT resolve.",
        "rationale": "REJECT from the master clause and from `isReal extra = false "
                     "→ out = selectReal listed`: a marker extra must NOT be "
                     "appended and this rival appends it. Refuted at a MARKER extra "
                     "with an empty listed, so `extra` is moved to the marker value "
                     "the drop-extra rival never probes.",
        "witness": _witness(
            "collectBroadcastTargetsTester [] Component.marker"),
        "witness_reference": _REF,
    },
    {
        "id": "weak-keep-markers-in-listed",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the marker exclusion on the listed sub-components: keeps EVERY
        # listed component, markers included, instead of only the real ones.
        "module": _impl(
            "    let out := listed ++ (if isReal extra then [extra] else [])\n"
            "    return out"),
        "refinement": "drops the marker exclusion on the listed sub-components: a "
                      "placeholder marker among the listed components is broadcast "
                      "to instead of being skipped. Its faithful counterpart "
                      "applies the per-component configuration action to a routing "
                      "marker string, which raises at configuration time — breaking "
                      "the passing marker scenarios and the failing scenario alike. "
                      "It does NOT resolve.",
        "rationale": "REJECT from the master clause `out = broadcastTargets listed "
                     "extra`: `selectReal listed` must drop the markers, and this "
                     "rival keeps a listed marker. Refuted at a listed containing a "
                     "marker (with a marker extra so the extra append is empty), so "
                     "`listed` is moved to a marker-containing value.",
        "witness": _witness(
            "collectBroadcastTargetsTester [Component.marker] Component.marker"),
        "witness_reference": _REF,
    },
    {
        # ORDER attack #1. Right membership, wrong POSITION for the extra: the
        # extra is emitted BEFORE the listed selection instead of after it. This
        # rival is a NEAR-MISS of the two extra-arm rivals above — it agrees with
        # gold on WHICH components are broadcast to on every input, and diverges
        # only in where the extra sits — so it gets its own witness at a
        # two-element `listed`, an input no other case probes.
        "id": "weak-extra-emitted-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let out := (if isReal extra then [extra] else []) ++ selectReal listed\n"
            "    return out"),
        "refinement": "the designated extra is configured BEFORE the listed "
                      "sub-components rather than after them. Its faithful "
                      "counterpart broadcasts to the same set of components but "
                      "dispatches to the extra first, so the components are "
                      "configured in the wrong sequence and the gathered result is "
                      "assembled with the extra's contribution in the wrong "
                      "position — the failing test compares the gathered output "
                      "positionally, so it still fails. It does NOT resolve.",
        "rationale": "REJECT from the master clause `out = broadcastTargets listed "
                     "extra`, which is a LIST EQUALITY and so pins ORDER, not just "
                     "membership: `broadcastTargets` puts `selectReal listed` "
                     "first and the extra last. Attacks the positional content of "
                     "the master clause — the one dimension the membership rivals "
                     "leave untested — and is refuted at a two-element `listed` "
                     "(one real, one marker) with a real extra, where the rival's "
                     "output and the spec's differ only by the extra's position.",
        "witness": _witness(
            "collectBroadcastTargetsTester [Component.real 1, Component.marker] "
            "(Component.real 0)"),
        "witness_reference": _REF,
    },
    {
        # ORDER attack #2. Right membership, wrong INTERNAL order of the listed
        # selection: the kept listed components are emitted in reverse. Distinct
        # from the rival above (which misplaces only the extra) and refuted at a
        # distinct input — two REAL listed components, the smallest input on
        # which reversal is observable at all.
        "id": "weak-listed-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let out := (selectReal listed).reverse ++ "
            "(if isReal extra then [extra] else [])\n"
            "    return out"),
        "refinement": "the real listed sub-components are broadcast to in reverse "
                      "order. Its faithful counterpart iterates the listed "
                      "sub-components backwards, so the components are configured "
                      "in reverse sequence and the gathered output's columns come "
                      "back transposed relative to the declared order; the failing "
                      "test compares the gathered result against a positionally "
                      "ordered expectation, so it still fails. It does NOT resolve.",
        "rationale": "REJECT from the master clause: `selectReal` is order-"
                     "PRESERVING (it keeps the real components in their listed "
                     "order) and this rival reverses them, so the list equality "
                     "fails even though the multiset of broadcast targets is "
                     "correct. Refuted at TWO real listed components with a marker "
                     "extra — the minimal input on which reversal is observable, "
                     "and a `listed` length no other witness uses; it also holds "
                     "`extra` at the marker value while attacking `listed`, "
                     "isolating the listed-order content.",
        "witness": _witness(
            "collectBroadcastTargetsTester [Component.real 1, Component.real 2] "
            "Component.marker"),
        "witness_reference": _REF,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals) over an in-place mutator
# `configure_output(children, leftover, requested)` that propagates a config code
# to every configurable child and to the leftover child when it too is
# configurable. This bundle models the SAME behaviour — WHICH sub-components are
# reached by the broadcast, and in what order — as ONE query method
# `collectBroadcastTargets` returning the ordered target list `out`; the
# per-component configuration action and the exact config value factor out
# (mapping.md §2), so the carrier observes only the marker-vs-real distinction
# and the ordered membership of `out`.
#
#   sibling case                     -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-control-localvar-reshape     -> pos-named-tail-locals
#                                       + pos-isreal-guard-swap        PORTED (split in 2)
#   admiss-f2p-shaped-input          -> admiss-selection-nondegenerate RE-AIMED
#   weak-drop-leftover-prepatch      -> weak-drop-extra                PORTED
#   weak-leftover-unconditional      -> weak-extra-unconditional       PORTED
#   weak-leftover-wrong-code         -> (none)                         OMITTED (carrier)
#   weak-double-mask-sentinels       -> weak-keep-markers-in-listed    PORTED (re-aimed)
#   weak-frame-kind-mutation         -> (none)                         OMITTED (vacuous)
#   (no counterpart)                 -> pos-straightline-reference     ADDED (witness ref)
#   (no counterpart)                 -> weak-extra-emitted-first       ADDED (order)
#   (no counterpart)                 -> weak-listed-order-reversed     ADDED (order)
#
# SPLIT (pos-control): the sibling's single soundness positive hoists the
#   configurability test into loop-local `cfgable` and leftover-local
#   `do_leftover` with an explicit else-branch. This backend's frozen impl has a
#   backward loop plus a trailing extra append, so the reshape spirit —
#   "structurally different, behaviourally identical, gold invariant kept" — is
#   carried by TWO shapes: pos-named-tail-locals (name the per-step and trailing
#   fragments) and pos-isreal-guard-swap (rewrite the extra append as an explicit
#   if/else on the same guard), both keeping the gold front-recursive invariant
#   so the reproof stays close to the frozen script.
#
# RE-AIMED (admissibility): the sibling reads the actual in-scope parameters back
#   through their `Requires` predicates and asserts the domain facts the
#   precondition promises for a normal F2P-shaped input. This backend has NO
#   `require` clause, so nothing could exclude an F2P-shaped input — that probe is
#   vacuous. It is re-aimed at the residual total-domain risk: that the post-image
#   is UNSATISFIABLE / DEGENERATE at the interesting point.
#
# ADDED (3), none of them parity-chasing:
#   * pos-straightline-reference is the `witness_reference` the reject lane needs
#     on this bundle (the frozen loop decides nothing under demonic choice), and
#     it is shipped as a positive so the manifest itself records that the
#     reference verifies — i.e. that rivals are rejected for being WRONG, not for
#     being loop-free.
#   * weak-extra-emitted-first / weak-listed-order-reversed attack the ORDER the
#     master clause pins. The ported membership rivals all leave positional
#     content untested, yet `out = broadcastTargets listed extra` is a list
#     equality: a rival with exactly the right broadcast SET but the wrong
#     sequence would otherwise go unnoticed by this battery. Both were confirmed
#     to fail verification and to be refuted at inputs no other case probes.
#
# OMITTED (2), both by carrier narrowing — not because they were hard:
#   * weak-leftover-wrong-code. The sibling configures the leftover to the WRONG
#     container code (`requested + 1`), rejected because the config value must be
#     EXACTLY `requested`. This carrier does NOT model the config value at all:
#     the per-component configuration action is applied identically to every
#     selected component and factors out as an R refinement (mapping.md §2), so
#     the observable is only WHICH components are selected and in what order, not
#     what value they receive. There is no sub-domain on which a "wrong value"
#     rival diverges from the spec on this carrier, so no discriminating witness
#     could exist. No substitute fabricated.
#   * weak-frame-kind-mutation. The sibling RECLASSIFIES a sentinel child as an
#     estimator (mutating the classification field `c.kind`) to satisfy the config
#     clauses vacuously, and is rejected by the classification-preservation
#     postcondition. On this carrier the marker-vs-real status is a PURE total
#     function `isReal` of an IMMUTABLE `Component` value: there is no mutable
#     classification field to overwrite, the inputs are referentially transparent
#     read-only values, and the method declares no `mut` binder — so the frame
#     class is doubly vacuous (nothing to pin, no substitute probe). No substitute
#     fabricated.
#
# DIVERGENCE: CLOSED BY THE SEMANTICS, nothing to ship and no hole. AUDIT
#   CORRECTION, the previous entry here is withdrawn in full. It read: "NOT
#   PORTABLE AS A CASE, RECORDED AS A SPEC HOLE ... under
#   `loom.semantics.termination "partial"` a non-terminating implementation
#   satisfies every `ensures` vacuously and VERIFIES, while its faithful
#   counterpart hangs the failing test and does not resolve ... a property of the
#   FROZEN SPEC", citing an internal findings doc. Vacuous satisfaction is the
#   PARTIAL rule and this file is not partial: line 4 reads
#   `set_option loom.semantics.termination "total"`, as it does in all 500 velvet
#   bundles, and the option cannot disagree with the file's `open TotalCorrectness`
#   because the `set_option` elaborator itself runs `openScope `TotalCorrectness`
#   (Loom/MonadAlgebras/WP/Options.lean:169-186). The cited doc no longer exists.
#   Under `total` a postcondition is claimed of ALL runs, so the frozen `while`
#   and any loop a rival splices each owe a descent obligation
#   `measure b' < measure b`. Measured on THIS bundle, proof reduced to a bare
#   `loom_solve`: a spun loop with no measure is refused at elaboration
#   (`Decreasing annotations are required in total correctness semantics`), and the
#   sharper shape that CARRIES a measure it never shrinks (`while q > 0 /
#   invariant 0 <= q / done_with q = 0 / decreasing q`, body `q := q`) is REJECTED
#   on the measure's own goal, `case «decreasing_1: q»` with residual `q < q`
#   unsolved. Supplying the annotation buys nothing; its descent is proved.
#   Not shippable as a reject case even so, for a WITNESS reason and not a spec
#   one: a witness must ELABORATE against the rival, and the rival's module does
#   not compile (the failure is at the `method`, ahead of any appended tester), so
#   the gate reads any witness as `witness-unproven`. REJECTED-BY-SPEC, no hole.
#
# COVERAGE. Independent post-image clauses attacked: master `out =
#   broadcastTargets listed extra` (every rival) — its MEMBERSHIP content by
#   weak-drop-extra / weak-extra-unconditional / weak-keep-markers-in-listed and
#   its ORDER content by weak-extra-emitted-first / weak-listed-order-reversed;
#   `isReal extra = true → out = selectReal listed ++ [extra]` (weak-drop-extra,
#   weak-extra-emitted-first); `isReal extra = false → out = selectReal listed`
#   (weak-extra-unconditional, weak-keep-markers-in-listed).
#   Binders moved by the reject witnesses: `listed` ∈ {[real 1], [],
#   [marker], [real 1, marker], [real 1, real 2]} — lengths 0, 1 and 2, and both
#   all-real and marker-containing contents; `extra` ∈ {real 0, marker} — both
#   marker-vs-real statuses, each paired with more than one `listed` shape.
#   FIVE distinct input points, pts = 5; neither binder is held fixed, and no two
#   rivals share a witness.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference (meta.json axioms == [], deep_model_references == []),
# so there is nothing there to probe.
AXIOM_TESTS = []
