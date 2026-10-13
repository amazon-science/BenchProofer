"""properties.py — G-PBT falsification battery for django__django-14787 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct buildPresentedAttrs`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
a subject that satisfies the frozen spec).

WITNESS SUBJECT. That second subject is NOT the frozen solution here. The frozen
impl keeps a ``while`` loop, whose fixpoint elaborates through ``Classical.choice``
under ``loom.semantics.choice "demonic"``; the kernel cannot unfold it, so
``decide`` against the frozen tester is STUCK for every claim, true or false, and
its exit code discriminates nothing. Each reject case therefore names a
``witness_reference``: the same frozen spec implemented WITHOUT the loop, which
does reduce. That source is also carried as the ``pos-control-direct`` positive,
so the battery independently records that the reference VERIFIES — a correct impl
cannot violate its own spec, so a witness that fails there is a genuine
refutation, and loop-freeness is not what any rival is rejected for.

DEFENDED SURFACE (one contracted method over three read-only inputs):

  buildPresentedAttrs (methodAttrs baseAttrs names)
        return (out : List (String × Option String))
    ensures out = mergePlan methodAttrs baseAttrs names

There is ONE method, ONE top-level post-image clause, and NO ``require`` clause
(the admitted domain is total). The result is the attribute environment a
callable presents, computed name by name over the requested ``names``: for each
name, the value the SOURCE object binds if it defines one, otherwise the value
the BASE object binds — the per-name overlay ``mergeAt`` lifted across the name
list by ``mergePlan``. The three inputs — ``methodAttrs`` (the source object's
attributes), ``baseAttrs`` (the bare callable's attributes), ``names`` (the
requested attribute names) — are FREE: the post-image must hold for every value
each takes, which is what makes the reject rivals below refutable at a concrete
point.

The behaviour the failing test pins is that a requested name the source object
defines but the base object does NOT is presented with the SOURCE's value — the
bare base object lacks that name outright, so before the fix the presented
environment left the name absent and an introspection read of it returned
nothing. The overlay's SOURCE-WINS-ELSE-BASE rule is the load-bearing content.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent: every parameter is an
    immutable value, this bundle declares no ``mut`` binder on the inputs (only
    the loop-local accumulator/index are ``mut``), there is no heap and no
    aliasing — so there is no read-only input to overwrite and no substitute
    probe to fabricate. Not faked. (See footer.)
  * WRONG-SOURCE / PRESENCE — APPLIES, and is the headline SPEC-TOO-WEAK probe:
    presenting each name from the base object only, never overlaying the
    source's value. It leaves a source-only name absent (its value never copied)
    — exactly the pre-fix behaviour and the scenario the failing test constructs.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on part of the requested-name
    domain but diverging on a sub-domain (dropping a requested name from the
    presented environment).
  * KEY-PRESERVATION — APPLIES: the post-image pins not only each presented
    VALUE but the NAME it is presented under (the pair's key). A rival can get
    every value right and present it under the wrong attribute name.
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
  * UNGROUNDED-ORACLE ECHO — N/A. ``mergePlan`` / ``mergeAt`` / ``lookupAttr``
    are concrete ``def``s in the ``pure`` region (the ``axioms`` region declares
    no ``axiom`` and the proof consumes none — the overlay's equality to the
    real standard-library attribute-copy helper is a G-AX A-reference, not a
    contract the proof assumes). There is no opaque answer key to echo; the
    positive controls are honest cheapest-reshape controls.

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. The three reject witnesses sit at three DISTINCT input
points and between them move all three binders off any fixed value:
``methodAttrs`` takes a one-name and a two-name environment; ``baseAttrs`` takes
both a non-empty environment (the overlay rival, the only witness where the base
object binds the requested name to a value that DIFFERS from the source's — the
point that makes the source-wins rule observable) and the empty environment;
``names`` takes both a one-name and a two-name request. A rival that overlaid
correctly would satisfy the overlay witness, so the manifest demonstrates the
post-image's genuine dependence on which object supplies each value, not merely
its value at one pinned point.

AXIOM lane: dropped. The axiom lane is G-AX's job; this bundle consumes no
``axiom`` (the overlay is a deep model, an A-reference validated executably
there), and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14787"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the gold impl body: a single anchor lying wholly inside the impl region
# ---- and unique in the file (both facts asserted at load by _swap). ----
_IMPL_GOLD = (
    "    let mut result : List (String × Option String) := []\n"
    "    let mut i := names.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ names.length\n"
    "      invariant result = mergePlan methodAttrs baseAttrs (names.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let n := names[i - 1]!\n"
    "      result := (n, mergeAt methodAttrs baseAttrs n) :: result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _IMPL_GOLD in _BASE, "impl anchor drift: buildPresentedAttrs body not verbatim"

# ---- the frozen proof body (tactic script only; elided from the spec view, so
# ---- a positive control that reshapes the impl or an admissibility case that
# ---- adds an in-region assert may retune it without touching the spec or the
# ---- `prove_correct` header). Unique in the file. ----
_PROOF_GOLD = (
    "prove_correct buildPresentedAttrs by\n"
    "  loom_solve\n"
    "  rw [mergePlan_drop_step methodAttrs baseAttrs names i (by omega) (by omega)]\n"
    "  simp_all"
)
assert _PROOF_GOLD in _BASE, "proof anchor drift"


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body in one variant."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- the LOOP-FREE reference subject for the reject lane's witnesses. --------
#
# The witness check asks a witness to hold of the rival and to FAIL against a
# second subject that satisfies the frozen spec. The frozen impl cannot serve as
# that second subject here: it keeps a `while` loop whose fixpoint elaborates
# through `Classical.choice` under `loom.semantics.choice "demonic"`, which the
# kernel cannot unfold, so `decide` on the frozen tester is STUCK for every
# claim regardless of truth. Measured on all three rivals below: the gold-side
# build fails with
#
#   Tactic `decide` failed ... did not reduce to `isTrue` or `isFalse`.
#   ... reduction got stuck at the `Decidable` instance
#
# — an exit code that carries no information, since the identical error appears
# for a TRUE claim. So the refutation is checked against this reference instead:
# the same frozen spec, implemented WITHOUT the loop, which therefore reduces.
# It is the SAME source as the `pos-control-direct` positive below, so the
# battery itself records — by an independent verifier run — that loop-freeness
# is not what any rival is being rejected for, and that this subject is a
# CORRECT impl of the frozen spec rather than merely a convenient one. Measured:
# it verifies (exit 0), and each rival's witness is refuted against it with
# `decide` proved that the proposition ... is false — a real verdict, not a
# stuck reduction.
_LOOPFREE = _swap2(
    _IMPL_GOLD,
    "    let out : List (String × Option String) :=\n"
    "      mergePlan methodAttrs baseAttrs names\n"
    "    return out",
    _PROOF_GOLD,
    "prove_correct buildPresentedAttrs by\n  loom_solve")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester
# ---- machinery: `buildPresentedAttrsTester args = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped,
# ---- so no tactic script can mask the verdict. Every argument is a concrete
# ---- literal so `decide` reduces the tester to a Boolean.
_TESTER = (
    "extract_program_for buildPresentedAttrs\n"
    "prove_precondition_decidable_for buildPresentedAttrs\n"
    "prove_postcondition_decidable_for buildPresentedAttrs\n"
    "derive_tester_for buildPresentedAttrs\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: skip the backward accumulator loop entirely and return the
        # overlay plan directly. Observationally identical (the loop's whole job
        # is to reconstruct `mergePlan`); the point-wise post-image discharges by
        # a bare `loom_solve`, so the proof body is retuned to drop the loop-step
        # rewrite the frozen script needs.
        #
        # This is the SAME source as `_LOOPFREE`, the subject the reject lane's
        # witnesses are refuted against. Carrying it as an `expect="verify"` case
        # is what makes that reference honest: the battery records independently
        # that the subject VERIFIES against the frozen spec, so a witness failing
        # there is a witness failing against a correct impl — and that
        # loop-freeness is not itself what any rival is rejected for.
        "module": _LOOPFREE,
        "rationale": "returning the overlay plan directly instead of rebuilding "
                     "it with a backward accumulator loop is observationally "
                     "identical, so `out = mergePlan methodAttrs baseAttrs names` "
                     "still holds; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on the loop shape. Doubles as the reject "
                     "lane's `witness_reference`: it is loop-free, so unlike the "
                     "frozen impl it REDUCES, and being a verifying impl of the "
                     "frozen spec it cannot violate that spec at any input.",
    },
    {
        "id": "pos-control-inline-index",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the same backward loop but inline the `names[i-1]!` read
        # instead of naming it in a `let`. Same value flow; the frozen proof
        # script closes unchanged.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let mut result : List (String × Option String) := []\n"
            "    let mut i := names.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ names.length\n"
            "      invariant result = mergePlan methodAttrs baseAttrs (names.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      result := (names[i - 1]!, mergeAt methodAttrs baseAttrs names[i - 1]!) :: result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": "inlining the per-step name read (no intermediate `let n`) "
                     "leaves the accumulated list unchanged, so the post-image is "
                     "unchanged; a correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — no method here has a `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous: nothing
    # could exclude an F2P-shaped input. The residual admissibility risk on a
    # total domain is that the post-image is UNSATISFIABLE / DEGENERATE at the
    # interesting point — a spec no impl can meet reads like a spec every impl
    # meets. This case discharges an in-region `assert` at fully concrete inputs
    # pinning the post-image's value at two F2P-shaped points: a requested name
    # the source defines and the base does NOT is presented with the source's
    # value; a name only the base defines falls back to the base's value; and
    # the source-defined presentation is DISTINCT from the base-only fallback
    # (the overlay genuinely discriminates which object supplies the value). The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof body is retuned only to clear the extra assert goal
    # by `decide`. The assert is live, not decoration: a false claim about the
    # same points leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-overlay-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _IMPL_GOLD,
            "    assert (with_name_prefix `admiss\n"
            "      (mergePlan [(\"__name__\", \"method\")] [] [\"__name__\"] = [(\"__name__\", some \"method\")] ∧\n"
            "       mergePlan [] [(\"__module__\", \"functools\")] [\"__module__\"] = [(\"__module__\", some \"functools\")] ∧\n"
            "       mergePlan [(\"__name__\", \"method\")] [] [\"__name__\"]\n"
            "         ≠ mergePlan [] [] [\"__name__\"]))\n"
            + _IMPL_GOLD,
            _PROOF_GOLD,
            "prove_correct buildPresentedAttrs by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [mergePlan_drop_step methodAttrs baseAttrs names i (by omega) (by omega)]; simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at two "
                     "concrete F2P-shaped points: a source-defined name is "
                     "presented with the source's value, a base-only name falls "
                     "back to the base's value, and the source-defined "
                     "presentation is distinct from the base-only fallback — so "
                     "the overlay genuinely discriminates which object supplies "
                     "each value. The in-region assert must discharge (else the "
                     "obligation is unsatisfiable / degenerate); the impl is kept "
                     "verbatim so the `ensures` clause discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-base-only-overlay",
        "kind": "uniqueness",
        "expect": "reject",
        # Present each requested name from the BASE object only — never overlay
        # the source's value. This IS the pre-fix behaviour: the bare base object
        # lacks the source-only name, so it is left absent (its value never
        # copied). Moves the `baseAttrs` binder: its witness is the only one
        # where the base object binds the requested name to a value that DIFFERS
        # from the source's, which is exactly what makes the source-wins rule
        # observable.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let out : List (String × Option String) :=\n"
            "      names.map (fun n => (n, lookupAttr baseAttrs n))\n"
            "    return out"),
        "refinement": "a counterpart that presents each name from the bare base "
                      "object only, never overlaying the source object's value, "
                      "leaves a source-only requested name absent — precisely the "
                      "pre-fix behaviour, since the bare object does not define "
                      "that name at all. On the failing scenario an introspection "
                      "read of that name then returns nothing instead of the "
                      "source's value, so the faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = mergePlan methodAttrs baseAttrs names`: "
                     "the post-image overlays the source's value where the source "
                     "defines the name, and this impl always takes the base's "
                     "value, so wherever the two objects disagree (incl. the "
                     "source defining a name the base does not) the presented "
                     "value differs. Verifying would be SPEC-TOO-WEAK (it would "
                     "admit the pre-fix base-only presentation). Refuted at a name "
                     "both objects bind to different values — the only witness "
                     "that moves the `baseAttrs` binder off empty.",
        "witness": _TESTER +
                   "example : buildPresentedAttrsTester [(\"__name__\", \"method\")] "
                   "[(\"__name__\", \"partial\")] [\"__name__\"] = false := by\n  decide\n",
        # The frozen impl's loop cannot decide this (or any) claim; refute
        # against the loop-free verifying impl of the same spec instead. See
        # `_LOOPFREE`. Verified by hand: rival exit 0; reference `decide` proved
        # the proposition false (a real verdict, not a stuck reduction).
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-requested-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Overlay correctly but on the requested names with the FIRST one
        # dropped, so a requested name is missing from the presented environment
        # entirely. Moves the `names` binder (and `methodAttrs`, to a two-name
        # source): correct on the tail of the request, wrong on the dropped head.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let out : List (String × Option String) :=\n"
            "      mergePlan methodAttrs baseAttrs (names.drop 1)\n"
            "    return out"),
        "refinement": "a counterpart that overlays only a proper suffix of the "
                      "requested names omits the leading requested name from the "
                      "presented environment, so an introspection read of that "
                      "name finds nothing even though the source defined it — the "
                      "failing test, which pins that name's presence and value, "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = mergePlan methodAttrs baseAttrs names`: "
                     "the post-image ranges over the whole requested list and this "
                     "impl drops its head, so the presented environment is one "
                     "pair short. Verifying would be SPEC-TOO-WEAK on which names "
                     "are presented. Refuted at a two-name request where the "
                     "dropped head is source-defined — the only witness that moves "
                     "the `names` binder to length two.",
        "witness": _TESTER +
                   "example : buildPresentedAttrsTester "
                   "[(\"__name__\", \"method\"), (\"__module__\", \"tests\")] [] "
                   "[\"__name__\", \"__module__\"] = false := by\n  decide\n",
        # See `_LOOPFREE`: the frozen impl's loop blocks `decide` for every
        # claim. Verified by hand: rival exit 0; reference decided it false.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-wrong-label",
        "kind": "uniqueness",
        "expect": "reject",
        # Overlay the correct VALUE for each requested name but present it under a
        # blank attribute name (the pair's key corrupted). Attacks the
        # key-preservation facet of the post-image, which the value-focused rivals
        # leave untouched: the value is right, the name it is presented under is
        # wrong.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let out : List (String × Option String) :=\n"
            "      names.map (fun n => (\"\", mergeAt methodAttrs baseAttrs n))\n"
            "    return out"),
        "refinement": "a counterpart that assigns the correct value but under a "
                      "blank attribute name presents the source's value under a "
                      "name no introspection read looks up, so a read of the "
                      "requested name still finds nothing — the failing test, "
                      "which reads the value BY its attribute name, still fails. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = mergePlan methodAttrs baseAttrs names`: "
                     "the post-image pins each presented pair's KEY to the "
                     "requested name, and this impl labels every value with the "
                     "empty name, so the keys diverge for any non-empty requested "
                     "name. Verifying would be SPEC-TOO-WEAK on the name a value "
                     "is presented under. Refuted at a single source-defined name "
                     "(a distinct input point from the other rivals).",
        "witness": _TESTER +
                   "example : buildPresentedAttrsTester [(\"__name__\", \"method\")] [] "
                   "[\"__name__\"] = false := by\n  decide\n",
        # See `_LOOPFREE`: the frozen impl's loop blocks `decide` for every
        # claim. Verified by hand: rival exit 0; reference decided it false.
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (2 soundness
# positives, 1 admissibility, 3 uniqueness rivals) contracting one function
# `assemble_bound_callable` over a permission-bearing read-only object. This
# bundle models the purely-functional core — a single method `buildPresentedAttrs`
# that computes the presented attribute environment as a per-name overlay of the
# source object over the bare base object. The value surface carries across; the
# permission surface does not exist here.
#
#   sibling case                        -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder                 -> pos-control-inline-index      PORTED
#   pos-control-cheapest                -> pos-control-direct            PORTED
#   admissibility                       -> admiss-overlay-nondegenerate  RE-AIMED
#   frame-mutation                      -> (none)                        VACUOUS
#   (no sibling divergence case)        -> (none)                        SPEC-CLOSED
#   partial-domain-value                -> weak-base-only-overlay        PORTED (merged)
#   partial-domain-presence             -> weak-base-only-overlay        PORTED (merged)
#                                          (+ weak-drop-requested-name   ADDED)
#                                          (+ weak-wrong-label           ADDED)
#
# 2 positives ported, 1 re-aimed, 1 vacuous, 2 uniqueness merged into one, 2
# uniqueness rivals added for binder/facet coverage.
#
# VACUOUS (frame-mutation): the sibling's MANDATORY frame-mutation rival writes
#   to a read-only input that carries only a fractional heap permission and is
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: every parameter is an immutable value, this bundle declares no
#   `mut` binder on the inputs (only the loop-local accumulator/index are `mut`),
#   there is no heap and no aliasing. There is no read-only input to overwrite
#   and no permission system to trip, so the class is vacuous. No substitute is
#   fabricated (per the porting map, this class is legitimately dropped rather
#   than replaced).
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
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# WITNESS SUBJECT (all three rivals): the refutations are checked against the
#   loop-free `_LOOPFREE` reference rather than the frozen impl, whose `while`
#   loop makes `decide` stuck for every claim (measured: the gold-side build
#   fails with `did not reduce to isTrue or isFalse` for all three witnesses, an
#   exit code that would attest to a refutation never performed). Each witness
#   was confirmed by hand to hold of its rival (exit 0) and to be decided FALSE
#   against the reference, which itself verifies (exit 0) and ships as the
#   `pos-control-direct` positive.
# RE-AIMED (admissibility): the sibling constructs a normal (F2P-shaped) input
#   and establishes the precondition for it. There is NO `require` clause here
#   (total domain), so nothing could exclude an F2P-shaped input — that probe is
#   vacuous. It is re-aimed at the residual admissibility risk on a total domain:
#   that the post-image is unsatisfiable / degenerate at the interesting point.
#   The case discharges an in-region assert pinning the overlay's value at two
#   F2P-shaped points (a source-defined name presented with the source's value;
#   a base-only name falling back to the base's value; the two distinct).
# MERGED (partial-domain-value + partial-domain-presence -> weak-base-only-
#   overlay): the sibling's value rival (result name taken from the wrong facet)
#   and presence rival (name copy dropped = pre-patch) both attack the SAME
#   behaviour here — the overlay taking the base's value instead of the source's.
#   On the real fixture the bare base object lacks the source-only name, so the
#   base-only overlay leaves it absent (the presence attack) AND, where the base
#   binds a different value, presents the wrong value (the value attack). One
#   rival is the faithful pre-patch and covers both; its witness sits at a name
#   both objects bind to different values, which is where the value divergence is
#   `decide`-observable and which moves the `baseAttrs` binder off empty.
# ADDED (weak-drop-requested-name): attacks the `names` binder — no sibling rival
#   varied the requested-name list. Its faithful counterpart omits a requested
#   name from the presented environment (the leading one), so an introspection
#   read of a source-defined name finds nothing; it would NOT resolve.
# ADDED (weak-wrong-label): attacks the KEY-preservation sub-term of the
#   post-image (the name each value is presented under), which the value-focused
#   rivals leave untouched. Its faithful counterpart stores the correct value
#   under a blank attribute name, so a read BY the requested name still finds
#   nothing; it would NOT resolve.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause
#   `out = mergePlan methodAttrs baseAttrs names` is attacked by all three rivals
#   at three DISTINCT input points (pts=3). Binders moved by the reject witnesses:
#   methodAttrs {[("__name__","method")], [("__name__","method"),("__module__","tests")]};
#   baseAttrs   {[("__name__","partial")], []};
#   names       {["__name__"], ["__name__","__module__"]}
#   — all three varied. weak-base-only-overlay is the only witness whose baseAttrs
#   binds the requested name to a value differing from the source's, which is
#   what makes the overlay's source-wins dependence observable; weak-drop-
#   requested-name is the only witness that moves `names` to length two; the
#   VALUE facet (which object supplies each value) and the KEY facet (which name
#   each value is presented under) are both attacked.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   `axiom` (the overlay `mergePlan`/`mergeAt` is a deep model, an A-reference
#   validated executably there), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
