# properties.py — G-PBT falsification battery for pytest-dev__pytest-7571 (lean).
#
# NOT a Lean file: a manifest the G-PBT gate parses. Each SPEC_TESTS case is a
# full Solution.lean variant built by region surgery — only text inside the
# `impl` region (and, for a positive control that legitimately reproves, the
# `proof` region) is edited, so the frozen spec (`pure` + `post-conditions`
# regions and every docstring) is never touched and `markers.same_spec` holds by
# construction. Every `theorem correct_captureLevel` keeps a byte-identical
# STATEMENT; no case adds an axiom, a helper lemma, `sorry`/`admit`, or
# `native_decide`.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (reasoned, not mechanical)
#
# This bundle models ONE obligation, `correct_captureLevel`, over one carrier:
#
#   problem_spec_captureLevel (initialLevel : Int) (levels : List Int)
#                             (result : Int) : Prop
#     := result = restoredCaptureLevel initialLevel levels
#
# The modeled observable is the capture threshold in effect AFTER a test has
# ended, as a function of the threshold the facility was created with
# (`initialLevel`) and the ordered sequence of levels the test raised it to
# (`levels`). The spec is a single equation, but it is NOT a single-clause spec:
# `restoredCaptureLevel` is a case split over the recorded threshold, so the
# equation has two independent arms that a rival can break separately —
#
#   (C1) some-arm: at least one raise happened, so the end-of-test threshold is
#        the RECORDED one — the threshold in effect immediately BEFORE the most
#        recent raise. This is the load-bearing clause: the whole point is that
#        the level a test asked for does not survive the test.
#   (C2) none-arm: no raise happened, so the end-of-test threshold is exactly the
#        created one, untouched. This is the no-op clause; it is what stops a
#        rival from "restoring" a test that never changed anything.
#
# and, folded into C1, the RECORDING RULE itself:
#
#   (C3) the record is last-write-wins over the raise sequence: each raise
#        records the threshold in effect just before IT, overwriting any earlier
#        record. A first-write-wins fold agrees with C1 on every test that raises
#        at most once and differs only from the second raise onward.
#
# C3 is DELIBERATELY NOT ATTACKED by a reject case, and the reason is structural
# rather than an omission — it is the sharpest thing this port learned. A rival
# isolating C3 must agree with the spec on every input with at most one raise;
# the behavior this instance's tests observe is reached only through single
# raises; therefore ANY pure-C3 rival passes the whole suite, and no honest
# `refinement` ("its faithful patch would not resolve") can be written for one.
# A first-write-wins rival WAS built, and its witness at a two-raise input was
# confirmed to discriminate — then its patch was run against the instance's tests
# and RESOLVED, so the case was dropped rather than shipped with a false
# refinement. What that establishes is that the frozen spec is strictly STRONGER
# than the instance's tests on the multi-raise sub-domain: good for the spec,
# and a known limitation of the tests. Recorded, not papered over; see
# `assessment`.
#
# Re-derived independently during audit, since a dropped case is exactly where a
# port can hide a gap: the first-write-wins rival was rebuilt and its witness at
# `initialLevel = 0, levels = [41, 43]` elaborates against it and FAILS on the
# frozen solution. So the spec does refute C3 — the case is absent for the
# refinement reason stated above, NOT because the spec is blind to the clause,
# and not because no witness could be built. The clause is therefore defended by
# the spec even though no shipped case attacks it.
#
# Binder discrimination. The spec has exactly two input binders and the reject
# witnesses must MOVE BOTH, or a rival that mishandled one of them would verify
# unnoticed:
#   * `initialLevel` is varied across witnesses (0, 3, 5, 7, 10) and is NOT held
#     at any single value. Both directions of the zero trap are covered, and they
#     pull opposite ways, so neither alone would do:
#       - A rival that confuses "the recorded threshold" with "zero" agrees with
#         the spec exactly wherever the recorded threshold IS 0, so it can only be
#         refuted where that value is NONZERO. `weak-teardown-ignores-record`
#         (witness at 3) and `weak-never-records` (witness at 5) sit there.
#       - The mirror rivals `weak-record-skips-zero` and
#         `weak-restore-skips-zero-record` guard on the recorded threshold being
#         nonzero, so they are refutable ONLY where the recorded threshold is 0 —
#         which under a single raise forces `initialLevel = 0`, and that is where
#         both witnesses sit. (Measured, not assumed: rebuilding either witness at
#         `initialLevel = 7, levels = [41]` FAILS, and at
#         `initialLevel = 7, levels = [0, 41]` — nonzero created threshold, zero
#         RECORDED threshold — it elaborates again. So the binder that decides
#         these two is the recorded value, not `initialLevel` directly.)
#     `weak-teardown-unguarded-fixed-level` is refutable at any `initialLevel`
#     other than the level it substitutes; its witness sits at 7.
#   * `levels` is varied in LENGTH as well as content: the empty list (the only
#     input that reaches C2 at all), one-element lists, and two-element lists.
#     A battery with no empty list could not attack C2 at all, and one with no
#     multi-element list would refute the recording rivals only on the
#     single-raise sub-domain, leaving a rival that mishandled later raises
#     unprobed.
#
# Frame / permission-mutation rivals: VACUOUS on this backend. Lean is
# referentially transparent — `implementation_captureLevel` is a pure `Int`-valued
# function of its two arguments, there is no aliasing, no mutable field reachable
# by two names, and no fractional-permission read-only parameter to abuse. The
# whole class the nagini sibling explicitly declined (it, too, had no read-only
# parameter) has no counterpart here for a structural reason rather than an
# incidental one. Nothing is fabricated in its place.
#
# Divergence / non-termination rivals: VACUOUS on this backend, and vacuous for
# the strong reason. `implementation_captureLevel` is a total Lean `def` whose
# loop is a `for` over a finite `List`, so a non-terminating rival cannot be
# WRITTEN, let alone verify vacuously. (Contrast the velvet sibling, where under
# partial termination semantics a diverging impl satisfies every `ensures`
# vacuously and verifies while its faithful patch hangs the test — a known spec
# hole, `the corpus-wide termination-semantics finding`. That hole does not exist here: the carrier
# forbids the rival.) The nagini sibling carries no divergence case either.
#
# Ungrounded-oracle echo: NONE, and there is no `opaque` term anywhere in this
# bundle (the `axioms` region is empty — the whole lifecycle is modeled deeply
# over the observable inputs). So every witness below states the spec predicate
# at CONCRETE literal inputs and closes by `decide`; no witness needs to condition
# on the carrier, and therefore no witness carries a hypothesis binder that could
# be inconsistent.
#
# WHAT WAS NOT PORTED FROM THE NAGINI SIBLING, AND WHY
# The nagini bundle contracts FOUR functions (a constructor, a raise operation, a
# teardown operation, and an end-to-end driver) over a mutable-object carrier;
# this bundle contracts ONE pure function over `(Int, List Int)`. So the nagini
# cases do not map one-to-one: several of them attack a per-function
# postcondition clause that has no separate existence here. The mapping is
# recorded case-by-case in `ported_from` below, and summarized in `assessment` of
# the submitted payload. Case-count parity with nagini is explicitly NOT the
# target; coverage of the surface THIS bundle models is.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7571"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors: each lies ENTIRELY inside the region it edits, and is unique ----

# The whole impl region body (inside `-- impl-start` / `-- impl-end`).
_IMPL = (
    "def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int := Id.run do\n"
    "  let mut st : Int × Option Int := (initialLevel, none)\n"
    "  for lvl in levels do\n"
    "    st := (lvl, some st.1)\n"
    "  return (match st.2 with\n"
    "          | some s => s\n"
    "          | none   => st.1)")

# The per-raise state update: records the threshold in effect, then moves to the
# newly named level. Inside the impl region.
_FOLD = "    st := (lvl, some st.1)"

# The end-of-test step: re-apply the record if there is one, else leave the
# current threshold. Inside the impl region.
_TEARDOWN = ("  return (match st.2 with\n"
             "          | some s => s\n"
             "          | none   => st.1)")

# The tail of the frozen proof (inside `-- proof-start` / `-- proof-end`); the
# `theorem correct_captureLevel` STATEMENT above it is never touched.
_PROOF_TAIL = (
    "  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do\n"
    "          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with\n"
    "        | some s => s\n"
    "        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do\n"
    "          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1) = _\n"
    "  rw [captureLevel_forIn_foldl]")

# The end of the impl region, used only by the admissibility probe to append
# throwaway `example`s (no new NAMED obligation, so the frozen theorem stays the
# only thing the file is asked to prove).
_IMPL_END = "-- impl-end"


# --- witnesses ---------------------------------------------------------------
# Each states the frozen spec predicate at ONE concrete input and asserts it is
# VIOLATED by the variant's implementation. `decide` closes it: the carrier is
# `Int` / `List Int` / `Option Int` with no opaque term, so every probed point
# computes. Checked in a file with the frozen obligations stripped, so no tactic
# script can interfere; each must ELABORATE against the rival and FAIL on the
# frozen solution. Every witness below was built both ways and SEEN to
# discriminate.

def _witness(initial, levels):
    return (f"example : ¬ problem_spec_captureLevel {initial} {levels}\n"
            f"    (implementation_captureLevel {initial} {levels}) := by\n"
            "  unfold problem_spec_captureLevel\n"
            "  decide\n")


SPEC_TESTS = [

    # ======================================================================
    # SOUNDNESS positives: structurally different but CORRECT implementations
    # must still verify. If a faithful correct impl cannot satisfy the
    # postcondition, the spec is SPEC-TOO-STRONG. On this backend a positive is
    # real work: the frozen tactic script is tuned to the frozen impl's
    # syntactic form, so a reshaped impl needs its proof genuinely re-closed.
    # Every proof below closes with no new lemma, no `sorry`, no
    # `native_decide`, and an untouched `theorem correct_captureLevel`
    # statement.
    # ======================================================================
    {
        "id": "pos-record-via-local",
        "kind": "soundness",
        "expect": "verify",
        "ported_from": "nagini pos-setlevel-localreshape",
        # Bind the threshold in effect to a local BEFORE recording it: the same
        # record-then-move semantics in a different statement shape. The frozen
        # proof still closes unchanged, which is the point — this is the
        # cheapest possible reshape and it must not be rejected.
        "module": _swap(_BASE, _FOLD,
                        "    let prev := st.1\n"
                        "    st := (lvl, some prev)"),
        "rationale": (
            "The per-raise update with the pre-raise threshold bound to a local "
            "first is the same function of (initialLevel, levels): it records "
            "the threshold in effect and then moves to the named level, so it "
            "satisfies both arms of the spec equation (C1 and C2) at every "
            "input. Rejecting it would mean the spec constrains the executable "
            "SHAPE rather than the observable, i.e. SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-teardown-getd",
        "kind": "soundness",
        "expect": "verify",
        "ported_from": "nagini pos-teardown-branch-reorder (first of two shapes)",
        # Express the end-of-test step as a total default-application over the
        # record instead of an explicit two-arm match. Same observable, but the
        # proof must be re-closed: the `show` is restated at the new shape and
        # the two arms are discharged by `cases`.
        "module": _swap(
            _swap(_BASE, _TEARDOWN, "  return st.2.getD st.1"),
            _PROOF_TAIL,
            "  show ((Id.run (forIn levels (initialLevel, none) (fun lvl r => do\n"
            "          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2).getD\n"
            "        (Id.run (forIn levels (initialLevel, none) (fun lvl r => do\n"
            "          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1 = _\n"
            "  rw [captureLevel_forIn_foldl]\n"
            "  cases (List.foldl (fun st lvl => (lvl, some st.1)) ((initialLevel : Int), (none : Option Int)) levels).2 <;> rfl"),
        "rationale": (
            "Applying the recorded threshold with the current one as the default "
            "is exactly the end-of-test rule: the record when there is one (C1), "
            "the created threshold when there is not (C2). It is a genuinely "
            "different executable shape — the frozen `show` no longer matches "
            "and the proof is re-closed at the new form — so it exercises the "
            "spec rather than the tactic script. It MUST verify (else "
            "SPEC-TOO-STRONG)."),
    },
    {
        "id": "pos-teardown-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        "ported_from": "nagini pos-teardown-branch-reorder (branch-order shape)",
        # The nagini sibling's branch reorder, re-expressed: handle the
        # "nothing recorded" arm FIRST. Lean match arms are order-significant
        # syntactically, so the frozen `show`/`rfl` breaks and the proof is
        # re-closed by splitting.
        "module": _swap(
            _swap(_BASE, _TEARDOWN,
                  "  return (match st.2 with\n"
                  "          | none   => st.1\n"
                  "          | some s => s)"),
            _PROOF_TAIL,
            "  show (match (Id.run (forIn levels (initialLevel, none) (fun lvl r => do\n"
            "          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).2 with\n"
            "        | none => (Id.run (forIn levels (initialLevel, none) (fun lvl r => do\n"
            "          pure PUnit.unit; pure (ForInStep.yield (lvl, some r.1)))) : Int × Option Int).1\n"
            "        | some s => s) = _\n"
            "  rw [captureLevel_forIn_foldl]\n"
            "  split <;> simp_all"),
        "rationale": (
            "Deciding the end-of-test threshold by testing for 'nothing was "
            "recorded' first is the same total function as testing for 'something "
            "was recorded' first — the arms are disjoint and exhaustive. This is "
            "the direct counterpart of the nagini branch-reorder positive: same "
            "observable, reordered decision, proof re-closed. It MUST verify "
            "(else SPEC-TOO-STRONG)."),
    },
    {
        "id": "pos-pure-fold",
        "kind": "soundness",
        "expect": "verify",
        "ported_from": (
            "no direct nagini counterpart — added because this bundle's carrier "
            "makes a control-flow-level positive possible, which nagini's "
            "mutable-object carrier did not"),
        # Drop the imperative loop entirely for a pure fold over the raise
        # sequence. The strongest positive available here: if the spec were
        # accidentally pinned to the `Id.run do`/`forIn` encoding rather than to
        # the observable, THIS is the case that catches it.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "def implementation_captureLevel (initialLevel : Int) (levels : List Int) : Int :=\n"
                  "  let st := levels.foldl (fun st lvl => (lvl, some st.1)) (initialLevel, none)\n"
                  "  match st.2 with\n"
                  "  | some s => s\n"
                  "  | none   => st.1"),
            _PROOF_TAIL, "  rfl"),
        "rationale": (
            "Computing the end-of-test state by folding the raise sequence, with "
            "no mutable local and no loop, is the same function of the two "
            "inputs as the frozen imperative version. Dropping the mutable local "
            "and the loop altogether is the sharpest check in this battery that "
            "the spec pins the OBSERVABLE (the threshold after the test) and not "
            "the executable encoding. It MUST verify (else SPEC-TOO-STRONG). "
            "(Not the outer limit of what the spec admits: a correct impl by "
            "explicit structural recursion over the raise sequence, with no fold "
            "and no loop, was also built during audit and proven against this "
            "same frozen statement — so the spec is not pinned to the fold "
            "either.)"),
    },

    # ======================================================================
    # ADMISSIBILITY: the spec must be SATISFIABLE — and satisfiable at the
    # ordinary, real-world-shaped inputs, not just in principle. There is no
    # precondition to admit here (`correct_captureLevel` binds `initialLevel`
    # and `levels` universally with no hypothesis), so PRECOND-TOO-STRONG
    # cannot arise from a guard. What CAN arise is a spec that is unsatisfiable
    # or wrongly valued at a normal input, which the frozen obligation alone
    # would not reveal at any particular point. So this case pins the spec at
    # the three shapes that matter and requires them to compute.
    # ======================================================================
    {
        "id": "admiss-normal-lifecycle",
        "kind": "admissibility",
        "expect": "verify",
        "ported_from": "nagini admiss-f2p-lifecycle",
        # Throwaway `example`s only — deliberately NOT named `theorem`/`lemma`,
        # so no new obligation is introduced and the frozen
        # `theorem correct_captureLevel` remains the only named proof duty.
        "module": _swap(
            _BASE, _IMPL_END,
            "-- Admissibility probes: the modeled behavior at ordinary test\n"
            "-- shapes. Throwaway `example`s (no new named obligation).\n"
            "example : problem_spec_captureLevel 0 [41] (implementation_captureLevel 0 [41]) := by\n"
            "  unfold problem_spec_captureLevel\n"
            "  decide\n"
            "\n"
            "example : implementation_captureLevel 0 [41] = 0 := by decide\n"
            "\n"
            "example : implementation_captureLevel 0 [] = 0 := by decide\n"
            "\n"
            "example : implementation_captureLevel 0 [41, 43] = 41 := by decide\n"
            "\n"
            "-- impl-end"),
        "rationale": (
            "Pins the spec at the three ordinary lifecycle shapes and requires "
            "each to compute to the value the end-of-test rule dictates: raised "
            "once from the created threshold, the created threshold is what "
            "survives (0 -> [41] -> 0, i.e. the raised level does NOT persist); "
            "never raised, the created threshold is untouched (C2); raised twice, "
            "the threshold held just before the LAST raise survives "
            "(0 -> [41,43] -> 41, i.e. C3's last-write-wins). If the spec were "
            "unsatisfiable or mis-valued at these inputs these `example`s would "
            "not elaborate, so it MUST verify."),
    },

    # ======================================================================
    # UNIQUENESS (SPEC-TOO-WEAK probes): rivals that share the frozen spec
    # byte-for-byte, differ only in the impl, and are WRONG. Each must be
    # rejected BY THE SPEC — which on this backend is established by the
    # `witness`, not by the build failing. Every witness below was built
    # against the rival (elaborates) and against the frozen solution (fails).
    #
    # Each `refinement` argues that the rival's faithful real patch does NOT
    # resolve the instance, so a rival that VERIFIED would be a true
    # verify-does-not-imply-resolve break rather than an artifact of the model.
    # The refinement claims here were checked by actually running the
    # instance's tests against each rival's faithful patch, not reasoned about;
    # see `assessment` in the submitted payload.
    # ======================================================================
    {
        "id": "weak-record-skips-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "ported_from": "nagini weak-setlevel-record-zero-skip",
        # Record the pre-raise threshold only when it is nonzero; record nothing
        # when it is 0. Correct at every nonzero created threshold, wrong exactly
        # at the fresh-facility case that the real scenario starts from.
        "module": _swap(_BASE, _FOLD,
                        "    st := (lvl, if st.1 = 0 then none else some st.1)"),
        "witness": _witness(0, "[41]"),
        "rationale": (
            "Refuted by the some-arm C1 together with the recording rule: at "
            "`initialLevel = 0` with one raise, the spec demands the threshold "
            "held before that raise (0), but this rival records nothing, so its "
            "end-of-test threshold is the raised level itself. The witness sits "
            "at exactly that point — `initialLevel = 0`, one raise — which is "
            "the sub-domain the rival gets wrong and the one every other witness "
            "here deliberately avoids."),
        "refinement": (
            "A faithful patch guarding the record on a nonzero prior threshold "
            "records nothing in the scenario the issue describes, because a "
            "freshly created facility sits at threshold 0. The end-of-test step "
            "then has nothing to re-apply, the raised level survives the test, "
            "and the next test observes the raised threshold instead of 0 — the "
            "very leak the instance's new test asserts against. So it does NOT "
            "resolve, and a verifying rival here would be a real break."),
    },
    {
        "id": "weak-record-names-new-level",
        "kind": "uniqueness",
        "expect": "reject",
        "ported_from": "nagini weak-setlevel-record-new-level",
        # Record the newly named level instead of the threshold in effect before
        # it: an off-by-one-in-time confusion that is invisible whenever a test
        # happens to raise to the level it was already at.
        "module": _swap(_BASE, _FOLD, "    st := (lvl, some lvl)"),
        "witness": _witness(10, "[41]"),
        "rationale": (
            "Refuted by C1: the spec's recorded value is the threshold in effect "
            "immediately BEFORE a raise, and this rival records the level the "
            "raise names. Those coincide only when a test raises to the "
            "threshold it already had, so the witness picks a created threshold "
            "(10) that differs from the raised level (41) — and picks a NONZERO "
            "created threshold, so the point also varies `initialLevel` away "
            "from the zero the previous witness uses."),
        "refinement": (
            "A faithful patch recording the requested level rather than the "
            "prior one restores the facility to the level the test asked for, "
            "which is precisely the pre-existing behavior the issue complains "
            "about: the raised threshold still survives the test. So it does NOT "
            "resolve."),
    },
    {
        "id": "weak-never-records",
        "kind": "uniqueness",
        "expect": "reject",
        "ported_from": "nagini weak-setlevel-norecord-prepatch",
        # The pre-patch shape: move the threshold on each raise but never record
        # anything, so the end-of-test step has nothing to re-apply. This is the
        # bug itself, and matches Solution_prepatch.lean's behavior.
        "module": _swap(_BASE, _FOLD, "    st := (lvl, st.2)"),
        "witness": _witness(5, "[10, 20]"),
        "rationale": (
            "Refuted by C1: with the record never written, the end-of-test "
            "threshold is whatever the last raise named, while the spec demands "
            "the threshold held just before it. The witness uses a nonzero "
            "created threshold and a TWO-raise sequence, so it discriminates "
            "even against a rival that only got single-raise tests right."),
        "refinement": (
            "This is the behavior before the fix: the facility adjusts its "
            "capture threshold on each raise but keeps no record of what it was "
            "beforehand, so the end-of-test step restores nothing and the raised "
            "threshold leaks into the next test. It is exactly the state the "
            "instance's new test was written to fail against, so it does NOT "
            "resolve. (It is also the behavior of this bundle's prepatch "
            "variant, which G-DIFF already confirms the spec rejects.)"),
    },
    {
        "id": "weak-teardown-ignores-record",
        "kind": "uniqueness",
        "expect": "reject",
        "ported_from": "nagini weak-teardown-noop-prepatch",
        # The record IS written, but the end-of-test step ignores it and leaves
        # the current threshold in place. Same observable as never recording, but
        # it attacks the end-of-test arm rather than the recording rule — a
        # distinct impl region and a distinct clause.
        "module": _swap(_BASE, _TEARDOWN, "  return st.1"),
        "witness": _witness(3, "[40, 50]"),
        "rationale": (
            "Refuted by C1 from the other side: the record is present, so C1's "
            "arm is the one the spec selects, but this rival returns the current "
            "threshold regardless — the raised level. Witnessed at a third "
            "distinct created threshold (3) with a two-raise sequence. Note this "
            "rival still satisfies C2 (with no raise there is no record and the "
            "current threshold IS the created one), which is why it must be "
            "refuted at a raising input specifically."),
        "refinement": (
            "A faithful patch that records the prior threshold but never "
            "re-applies it at the end of the test leaves the facility at the "
            "raised level, so a later test still observes the raised threshold. "
            "Recording without restoring is unobservable; the leak is unchanged. "
            "It does NOT resolve."),
    },
    {
        "id": "weak-teardown-unguarded-fixed-level",
        "kind": "uniqueness",
        "expect": "reject",
        "ported_from": "nagini weak-teardown-always-restore",
        # Drop the "was anything recorded" guard: apply the record
        # unconditionally, substituting a fixed level when there is none. The
        # ONLY rival here that attacks C2 (the no-op arm), and the only one
        # refuted at the EMPTY raise sequence.
        #
        # Note the substituted level is deliberately NOT 0. The 0-substituting
        # form of this same rival was BUILT AND TESTED and it resolves the
        # instance (its no-record path forces a threshold that other machinery
        # re-establishes anyway, so no test observes it) — its refinement
        # argument would have been false, so it was dropped rather than shipped.
        # See `assessment`.
        "module": _swap(_BASE, _TEARDOWN, "  return st.2.getD 50"),
        "witness": _witness(7, "([] : List Int)"),
        "rationale": (
            "Refuted by the none-arm C2, which no other rival here attacks: with "
            "no raise the spec demands the created threshold be left exactly as "
            "it was, and this rival returns a fixed level instead. The witness is "
            "the only one in the battery at an EMPTY raise sequence — the sole "
            "input shape that reaches C2 — at a created threshold (7) that no "
            "other witness uses, so it varies both binders."),
        "refinement": (
            "A faithful patch dropping the 'was anything recorded' guard "
            "re-applies a record that does not exist for every test that never "
            "raised the threshold, forcing those tests' facilities to a level "
            "unrelated to the one they were created with. Verified against the "
            "instance's own tests: this patch FAILS the new test, and fails it on "
            "the third of its three inner tests — the one that runs after a test "
            "which never raised the threshold, and which then observes the "
            "substituted level instead of the created one. So it does NOT "
            "resolve, and it breaks the end of every non-raising test rather than "
            "fixing the raising one."),
    },
    {
        "id": "weak-restore-skips-zero-record",
        "kind": "uniqueness",
        "expect": "reject",
        "ported_from": (
            "nagini weak-teardown-restore-to-zero, re-aimed — the nagini rival's "
            "own shape (pin the restored threshold to 0) turned out to RESOLVE "
            "this instance and was dropped; this rival attacks the same clause "
            "(C1's use of the recorded value) at the same sub-domain boundary "
            "(a zero recorded value) in a shape whose patch genuinely fails"),
        # Re-apply the record only when it is nonzero: a truthiness test where
        # the spec demands a "was anything recorded at all" test. Wrong exactly
        # when the recorded threshold is 0 — which is the fresh-facility case the
        # real scenario starts from.
        "module": _swap(_BASE, _TEARDOWN,
                        "  return (match st.2 with\n"
                        "          | some s => if s = 0 then st.1 else s\n"
                        "          | none   => st.1)"),
        "witness": _witness(0, "[41]"),
        "rationale": (
            "Refuted by C1: the spec selects the some-arm on the basis of whether "
            "a threshold was RECORDED, and this rival additionally requires the "
            "recorded threshold to be nonzero, so it leaves the raised level in "
            "place whenever the recorded one was 0. The witness sits at that "
            "boundary — created threshold 0, one raise — where the recorded value "
            "is 0 and the rival's guard wrongly suppresses the restore."),
        "refinement": (
            "A faithful patch testing the recorded threshold for truthiness "
            "rather than for presence cannot restore a recorded threshold of 0, "
            "and 0 is exactly what a freshly created facility records. Verified "
            "against the instance's own tests: this patch FAILS the new test, "
            "with the later inner test observing the raised level instead of the "
            "created 0 — the same leak the test was written to catch. So it does "
            "NOT resolve."),
    },
]


# ---------------------------------------------------------------------------
# AXIOM_TESTS: intentionally empty and IGNORED by this gate (the axiom lane is
# G-AX's job). This bundle consumes no callee axiom at all — the `axioms` region
# is empty because the whole threshold lifecycle is modeled deeply over the
# observable inputs, so there is no `opaque` term and no assumed contract for a
# PBT case to probe. That is also why every witness above can close by `decide`.
# ---------------------------------------------------------------------------
AXIOM_TESTS = []
