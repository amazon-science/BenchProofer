# properties.py — G-PBT falsification battery for django__django-14792 (lean lane).
#
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case
# is a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only
# the impl region — and, where a positive control honestly reproves, the proof
# body — is edited by region surgery via _swap), checked by variant_scope plus the
# real Lean verifier. Every expect="reject" case carries a refutation `witness`: a
# self-contained snippet that ELABORATES against the rival and FAILS on the frozen
# solution, so the rejection is attributable to the postcondition and not to a
# tactic script that merely stopped matching a reshaped impl.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read off Solution.lean + mapping.md)
# ---------------------------------------------------------------------------
#
#   getTimezoneName (tzLabel : Option String) (tzStr : String) -> String
#
#   ONE obligation:
#     theorem correct_getTimezoneName :
#       ∀ (tzLabel : Option String) (tzStr : String),
#         problem_spec_getTimezoneName tzLabel tzStr
#           (implementation_getTimezoneName tzLabel tzStr)
#
#   NO precondition hypothesis: the obligation is universally quantified over the
#   full carrier, so every value of both binders is in domain.
#
#   TWO independent top-level postcondition clauses:
#     CLAUSE 1 (the discriminating clause)
#         ∀ s, tzLabel = some s → s ≠ "" → result = s
#       A short label that is present AND carries content wins outright: the
#       result is exactly that label, never the full textual form.
#     CLAUSE 2 (the fallback clause)
#         (tzLabel = none ∨ tzLabel = some "") → result = tzStr
#       A short label that is absent, or present but empty, does NOT win: the
#       result is exactly the full textual form. The two disjuncts are the two
#       INDEPENDENT falsity cases — an impl can handle absence correctly and
#       still let an empty label through, and vice versa.
#
#   The clauses partition the tzLabel domain into its three observationally
#   distinct cases (absent / present-empty / present-nonempty) and pin `result`
#   to EXACTLY one of the two carried inputs in each. Both right-hand sides are
#   the function's OWN arguments, so the whole postcondition is GROUNDED in the
#   input binders: there is no opaque callee, no axiom (the axioms region is
#   empty per mapping.md), and no answer-key term for a wrong impl to echo.
#
# ---------------------------------------------------------------------------
# CARRIER NOTE (what the nagini rivals become here)
# ---------------------------------------------------------------------------
#
# The nagini sibling abstracted the same selection over a heap object carrying
# two fields at HALF (read-only) permission, the short label being an optional
# sequence of code points. This backend models the identical selection over two
# immutable VALUE parameters, `Option String` and `String`. The carrier is fully
# TRANSPARENT: `Option`/`String` equality computes on concrete literals, so every
# clause the nagini battery attacked has a direct counterpart here and each is
# refutable at a concrete literal input. No witness needs to CONDITION on the
# carrier, so no witness binds a hypothesis and the gate's joint-satisfiability
# probe has nothing to discharge. No witness uses sorry/admit/native_decide/axiom.
#
# ---------------------------------------------------------------------------
# BINDER + CLAUSE COVERAGE (what the gate does NOT check; read before judging)
# ---------------------------------------------------------------------------
#
# The single obligation is DEFENDED (3 soundness positives), probed for
# SATISFIABILITY at F2P-shaped ground inputs (1 admissibility positive) and
# ATTACKED (6 uniqueness rivals) — all three lanes this gate exists to test.
# Both clauses are attacked, and BOTH disjuncts of the fallback clause are
# attacked separately:
#
#   CLAUSE 1 (present & non-empty => label)  attacked by weak-always-full,
#                                            weak-inverted-selection
#   CLAUSE 2 / none disjunct                 attacked by weak-absent-yields-empty,
#                                            weak-empty-full-substituted
#   CLAUSE 2 / some "" disjunct              attacked by weak-empty-label-wins,
#                                            weak-always-short
#
# BOTH input binders are VARIED across the six reject witnesses — a binder every
# witness held at one value would be a binder no rival was built to abuse:
#   tzLabel: `some "S1"`, `some "S2"`, `some ""` (x2), `none` (x2) — all three
#            clause domains, and two distinct non-empty labels.
#   tzStr:   "F1", "F3", "F6", "F4", "F5", and `""` — six distinct values, NEVER
#            held fixed, so a rival that ignored the full textual form (or
#            substituted a constant for it) cannot agree with gold at every
#            probed point. The `""` point earns its place separately: tzStr's OWN
#            emptiness boundary is the one sub-domain where a rival may swap a
#            stand-in constant for the full textual form and still agree with
#            gold at every other input — see weak-empty-full-substituted, which
#            no other witness's tzStr value can see.
# Six distinct input points in all.
#
# The rivals that mishandle the SAME falsity case are refuted at DIFFERENT points
# on purpose. weak-absent-yields-empty is a NEAR-MISS: it agrees with gold on both
# present branches and errs only on absence, so its witness sits at `none`, the
# only input that exposes it. weak-always-short errs on BOTH falsity cases, so its
# witness sits at `some ""` — otherwise its rationale would claim a sub-domain
# (the empty-label boundary) the manifest never demonstrates.
# weak-empty-full-substituted also errs only under a falsity case, but ONLY when
# the full textual form is itself empty, so it needs the `(none, "")` point and is
# invisible at the `(none, "F5")` where weak-absent-yields-empty is refuted — the
# two `none`-disjunct rivals therefore do not share an input point either.
#
# ---------------------------------------------------------------------------
# NAGINI LANES THAT DO NOT PORT (accounting; see also `assessment`)
# ---------------------------------------------------------------------------
#
#   * FRAME / PERMISSION-MUTATION — VACUOUS here, and DEMONSTRATED so rather than
#     argued. The nagini sibling makes this lane MANDATORY and ships TWO rivals
#     (frame-mut-short, frame-mut-full), because there both observables are
#     carried at a half heap permission and an impl that OVERWRITES one of them to
#     satisfy the postcondition vacuously must be rejected by the permission
#     system. Lean is referentially transparent: both observables are immutable
#     value parameters, there is no heap, no aliasing and no fractional
#     permission, so the nearest expressible thing to "store into a read-only
#     input" is a LOCAL REBIND, which the obligation cannot see at all — the
#     clauses are stated over the binders `tzLabel`/`tzStr`, whose values no
#     rebind can change.
#     Measured during the audit, both halves:
#       - an impl that rebinds both inputs to themselves and then selects on the
#         rebound copies VERIFIES (exit 0) under the reshaped proof — the "write"
#         is invisible to the obligation, so there is no permission failure to
#         attest to and a "frame" rival here would be a no-op positive;
#       - the actual vacuity ATTEMPT (rebind the label to the full form, then
#         emit it) is rejected — but as a plain VALUE error, `pure ((some
#         tzStr).getD tzStr) = s` failing against CLAUSE 1, i.e. it is just
#         weak-always-full spelled with an extra local. There is no distinct lane
#         left to port, so no substitute is fabricated.
#
#   * DIVERGENCE / NON-TERMINATION (nagini's wrong-nonterm) — nothing to ship,
#     and the audit sharpened the reason. "A diverging impl cannot be written at
#     all" is too strong: `partial def` DOES let one be written on this backend,
#     and the audit wrote it (a self-call under `partial`). What actually happens
#     is that it is REJECTED, and rejected for a reason that attributes nothing to
#     the spec: `partial` makes the definition opaque to reduction, so the proof
#     fails at `Tactic 'unfold' failed to unfold implementation_getTimezoneName`
#     — a tactic wall, not a postcondition violation. A reject case resting on
#     that would be exactly the vacuous rejection the witness requirement exists
#     to catch, and no witness can rescue it: with the impl irreducible, a
#     `decide`-based refutation is stuck on the rival side too (the
#     witness-undecided outcome), so the case could never be more than
#     inconclusive. This is NOT the velvet situation, where under partial
#     termination semantics a non-terminating impl satisfies every clause
#     vacuously and the spec genuinely ADMITS the rival — a known, already-settled
#     hole recorded in the corpus-wide termination-semantics finding and deliberately NOT re-derived
#     here. On this backend the disposition is the same (nothing to ship) for the
#     different reason above.
#
#   * ADMISSIBILITY (nagini's admiss-bothbranches) — PORTED, not dropped. The
#     earlier accounting called this N/A because "the lean obligation carries no
#     precondition hypothesis, so there is nothing that could be
#     PRECOND-TOO-STRONG". That reason is REJECTED by the second audit: on a total
#     carrier the analogue of a too-strong precondition is the obligation being
#     UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
#     discharges the obligation at that concrete input — by evaluation, as a
#     `have`, before closing the frozen obligation verbatim — tests directly.
#     Shipped below as `admiss-f2p-ground-instances`; the lane is no longer empty.
#
#   * UNGROUNDED-ORACLE ECHO — N/A, and the nagini sibling records the same.
#     Every clause's right-hand side is one of the function's own arguments, so
#     there is no answer-key to echo; a wrong constant simply fails a clause.
#
#   * AXIOM_TESTS — dropped. The axiom lane is G-AX's job and this gate ignores
#     it. mapping.md records zero axioms and zero deep-model references here
#     (both observables enter as plain data), so there would be nothing to probe.
from pathlib import Path

INSTANCE = "django__django-14792"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. `_IMPL` is the WHOLE frozen definition of the modeled function; it
# lies entirely inside the single `-- impl-start` / `-- impl-end` region that the
# consumer spec view elides, and it is unique in Solution.lean. `_PROOF` is the
# frozen tactic body, entirely inside `-- proof-start` / `-- proof-end`. Editing
# only these two texts keeps markers.same_spec True and leaves the `theorem
# correct_getTimezoneName` STATEMENT byte-identical.
# ---------------------------------------------------------------------------
_IMPL = (
    "def implementation_getTimezoneName\n"
    "    (tzLabel : Option String) (tzStr : String) : String := Id.run do\n"
    "  let mut name := tzStr\n"
    "  match tzLabel with\n"
    "  | some s => if s ≠ \"\" then name := s\n"
    "  | none => pure ()\n"
    "  return name\n"
)
_PROOF = (
    "  intro tzLabel tzStr\n"
    "  unfold problem_spec_getTimezoneName implementation_getTimezoneName\n"
    "  constructor\n"
    "  · intro s hs hne\n"
    "    subst hs\n"
    "    simp only [Id.run, if_pos hne]\n"
    "    rfl\n"
    "  · rintro (h | h) <;> subst h <;> rfl\n"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from Solution.lean"
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from Solution.lean"

# A pure (non-`Id.run`) head for the reshaped variants. The declaration NAME and
# SIGNATURE are unchanged — only the body form differs — so the frozen theorem
# statement still elaborates against it.
_HEAD = ("def implementation_getTimezoneName\n"
         "    (tzLabel : Option String) (tzStr : String) : String :=\n")

# The reproof used by the reshaped positives. It case-splits the optional label
# and then the emptiness boundary — the same two distinctions the frozen script
# makes, re-derived for the new body shape. No new axiom, lemma or sorry; the
# theorem statement is untouched.
_REPROOF = (
    "  intro tzLabel tzStr\n"
    "  unfold problem_spec_getTimezoneName implementation_getTimezoneName\n"
    "  cases tzLabel with\n"
    "  | none => simp\n"
    "  | some s =>\n"
    "    by_cases hs : s = \"\"\n"
    "    · subst hs; simp\n"
    "    · simp [hs]\n"
)


def _variant(body, proof=None):
    src = _swap(_BASE, _IMPL, body)
    return src if proof is None else _swap(src, _PROOF, proof)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls.
# Each must VERIFY; a rejection means SPEC-TOO-STRONG. Each reproves the frozen
# obligation honestly for its new body shape (statement byte-identical, no new
# axiom/lemma/sorry/native_decide) — the real work on this backend.
# ===========================================================================

# pos-negated-guard (ports nagini's pos-reorder): the guard polarity is INVERTED
# — test for the EMPTY label and fall through, rather than testing for content
# and taking it — and the fallback for the absent case is written out directly
# instead of being pre-seeded into a mutable accumulator. Same value mapping on
# every input; only the control flow changes.
_POS_NEGATED_GUARD = _variant(
    _HEAD
    + "  match tzLabel with\n"
      "  | some s => if s = \"\" then tzStr else s\n"
      "  | none => tzStr\n",
    _REPROOF,
)

# pos-normalize-then-select (ports nagini's pos-locals): collapse the optional
# label to a plain one FIRST (absence becomes the empty label, which the fallback
# clause treats identically to a present-but-empty one), then make a single
# emptiness decision. A different data shape — one test instead of a match plus a
# test — with an identical result, and it is exactly the reshape a faithful patch
# could take. Correct precisely BECAUSE the two falsity cases of the fallback
# clause are pinned to the same value.
_POS_NORMALIZE = _variant(
    _HEAD
    + "  let label := tzLabel.getD \"\"\n"
      "  if label = \"\" then tzStr else label\n",
    _REPROOF,
)

# pos-boolean-guard (AUDIT REPLACEMENT for a defective third positive; see the
# AUDIT RECORD at the foot of this file): the emptiness decision is made by the
# carrier's BOOLEAN emptiness test rather than by a decidable-`Prop` inequality,
# so the guard's scrutinee changes type (`Bool` in place of `Decidable (s ≠ "")`)
# and the `if` elaborates through a different instance. Behaviourally identical on
# every input of both binders.
#
# MEASURED, not assumed — this is exactly the claim the discarded positive made
# falsely, so it is verified rather than asserted:
#   * it is NOT definitionally equal to the frozen impl: `example : <this> =
#     <frozen> := by rfl` FAILS (`Tactic 'rfl' failed ... not definitionally
#     equal`), so the reshape is a real one and not a spelling of the same term;
#   * the FROZEN tactic body does NOT close it: kept verbatim, the build fails
#     with `Tactic 'rfl' failed: ... (if s.isEmpty = true then tzStr else s) = s`,
#     so `_REPROOF` below is doing real work rather than decorating a proof that
#     already went through.
_POS_BOOLEAN_GUARD = _variant(
    _HEAD
    + "  match tzLabel with\n"
      "  | some s => if s.isEmpty then tzStr else s\n"
      "  | none => tzStr\n",
    # `String.isEmpty_iff` is what bridges the Bool guard to the Prop boundary the
    # spec's clauses are stated over; the frozen script has no such step.
    "  intro tzLabel tzStr\n"
    "  unfold problem_spec_getTimezoneName implementation_getTimezoneName\n"
    "  constructor\n"
    "  · intro s hs hne\n"
    "    subst hs\n"
    "    simp [String.isEmpty_iff, hne]\n"
    "  · rintro (h | h) <;> subst h <;> simp [String.isEmpty]\n",
)


# ===========================================================================
# ADMISSIBILITY (second-audit ADDITION) — the obligation must be SATISFIABLE at
# the concrete input shapes the change is about. On this total carrier there is no
# precondition hypothesis to be over-strong, so the analogue is: the frozen
# postcondition, instantiated at an F2P-shaped GROUND input and evaluated, must
# actually HOLD. Three ground instances are discharged by `decide` as `have`s
# ahead of the frozen tactic body, which is then carried VERBATIM — so the case
# adds obligations rather than replacing any, the theorem statement stays
# byte-identical, and no new declaration/axiom/sorry appears.
#
# The three instances are the three observationally distinct label shapes at
# F2P-shaped values: a constant-offset zone advertising its offset designation
# alongside a differing full form, a named zone advertising nothing, and a zone
# advertising a blank label. If any FAILED the modeled behaviour would be
# unsatisfiable at exactly the input the F2P exercises.
#
# MEASURED load-bearing, not assumed: carried onto the PRE-CHANGE impl (always
# emit the full textual form) the FIRST `have` fails at its OWN line with
#   `Tactic 'decide' proved that the proposition (∀ s, some "+10" = some s → s ≠
#    "" → "Etc/GMT-10" = s) ∧ ... is false`
# independently of whether the frozen tactic body closes — so each `have` pins
# behaviour at its input rather than decorating a proof that already went through.
_ADMISS_GROUND = "".join(
    f'  have {nm} : problem_spec_getTimezoneName {lbl} {full}\n'
    f'      (implementation_getTimezoneName {lbl} {full}) := by\n'
    f'    unfold problem_spec_getTimezoneName implementation_getTimezoneName\n'
    f'    decide\n'
    for nm, lbl, full in (
        ("_ground_offset", '(some "+10")', '"Etc/GMT-10"'),
        ("_ground_named", "none", '"Europe/Madrid"'),
        ("_ground_blank", '(some "")', '"Europe/Madrid"'),
    ))
_ADMISS = _swap(_BASE, _PROOF, _ADMISS_GROUND + _PROOF)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED; a rival that VERIFIES is SPEC-TOO-WEAK.
# Each shares the frozen spec exactly, edits only the impl region, and keeps the
# frozen proof body VERBATIM (no case retunes a tactic to manufacture a
# rejection). The gate scores the `witness`, which is checked in a file with the
# obligation removed, so no tactic script can interfere.
# ===========================================================================

# The exact PRE-CHANGE behaviour: never consult the short label at all.
_RIV_ALWAYS_FULL = _variant(_HEAD + "  tzStr\n")

# Never fall back: emit the short label always, defaulting to the empty one when
# absent. Wrong on BOTH falsity cases of the fallback clause.
_RIV_ALWAYS_SHORT = _variant(_HEAD + "  tzLabel.getD \"\"\n")

# Selection INVERTED: the full form wins when the short label carries content,
# and the (empty) short label is emitted when it does not.
_RIV_INVERTED = _variant(
    _HEAD
    + "  match tzLabel with\n"
      "  | some s => if s ≠ \"\" then tzStr else s\n"
      "  | none => \"\"\n"
)

# The emptiness BOUNDARY dropped: fall back only on absence, so a present-but-
# empty short label wins and is emitted as-is.
_RIV_EMPTY_WINS = _variant(_HEAD + "  tzLabel.getD tzStr\n")

# NEAR-MISS: both present branches are gold-exact; only ABSENCE is mishandled,
# emitting the empty label instead of falling back to the full form.
_RIV_ABSENT_EMPTY = _variant(
    _HEAD
    + "  match tzLabel with\n"
      "  | some s => if s ≠ \"\" then s else tzStr\n"
      "  | none => \"\"\n"
)

# AUDIT ADDITION (see the AUDIT RECORD): the tightest near-miss in the battery.
# The selection itself is gold-exact on every input; the ONE divergence is that
# when the fallback fires and the full textual form is itself EMPTY, a non-empty
# stand-in is substituted for it. So this rival agrees with gold at every input
# the five original witnesses probe — all of which hold tzStr non-empty — and is
# exposed ONLY at the tzStr = "" boundary. It is the rival that makes the second
# binder's own emptiness boundary load-bearing instead of merely varied.
_RIV_EMPTY_FULL_SUBST = _variant(
    _HEAD
    + "  match tzLabel with\n"
      "  | some s => if s ≠ \"\" then s else (if tzStr = \"\" then \"?\" else tzStr)\n"
      "  | none => if tzStr = \"\" then \"?\" else tzStr\n"
)


def _wit_clause1(label, full, note):
    """Refutation via CLAUSE 1: at a present, non-empty label the result must be
    exactly that label. Instantiates the clause at the literal and derives a
    contradiction from the rival's actual (computed) result."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_getTimezoneName (some {label}) {full}\n"
        f"    (implementation_getTimezoneName (some {label}) {full}) := by\n"
        f"  intro h\n"
        f"  exact absurd (h.1 {label} rfl (by decide)) (by decide)"
    )


def _wit_clause2(label, full, side, note):
    """Refutation via CLAUSE 2: at an absent (`Or.inl`) or present-but-empty
    (`Or.inr`) label the result must be exactly the full textual form."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_getTimezoneName {label} {full}\n"
        f"    (implementation_getTimezoneName {label} {full}) := by\n"
        f"  intro h\n"
        f"  exact absurd (h.2 ({side})) (by decide)"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----------------------------------
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NEGATED_GUARD,
        "rationale": (
            "structurally-different but CORRECT impl: the emptiness guard's "
            "POLARITY is inverted (test for the empty label and fall through, "
            "instead of testing for content and taking it) and the absent case "
            "returns the full textual form directly rather than via a pre-seeded "
            "mutable accumulator. The value mapping is identical on every input "
            "of both binders, so both postcondition clauses still hold. The "
            "frozen `theorem correct_getTimezoneName` STATEMENT is kept "
            "byte-identical and the proof body is honestly re-closed by "
            "case-splitting the optional label and then the emptiness boundary "
            "(no new axiom/lemma/sorry/native_decide). If it FAILS => "
            "SPEC-TOO-STRONG: the postcondition would be over-fit to one guard "
            "polarity rather than to the behaviour. Ports nagini's pos-reorder."
        ),
    },
    {
        "id": "pos-normalize-then-select",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NORMALIZE,
        "rationale": (
            "a DIFFERENT DATA SHAPE with an identical result: the optional short "
            "label is first collapsed to a plain one (absence becomes the empty "
            "label) and then a SINGLE emptiness decision selects. This is correct "
            "precisely because the fallback clause pins BOTH of its falsity cases "
            "(absent, present-but-empty) to the same value, so merging them "
            "before deciding is sound. Must verify; else SPEC-TOO-STRONG (the "
            "spec would be distinguishing two cases it itself equates). Proof "
            "honestly re-closed, statement untouched. Ports nagini's pos-locals."
        ),
    },
    {
        "id": "pos-boolean-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BOOLEAN_GUARD,
        "rationale": (
            "the emptiness decision is taken by the carrier's BOOLEAN emptiness "
            "test instead of by the decidable-`Prop` inequality the frozen impl "
            "uses, so the `if` elaborates through a different instance and the "
            "guard's scrutinee changes type. Behaviourally identical on every "
            "input of both binders, so both postcondition clauses still hold, "
            "and the proof must cross the Bool/Prop boundary explicitly — a step "
            "the frozen script does not contain. Both halves of that claim are "
            "MEASURED, not asserted: this impl is NOT definitionally equal to "
            "the frozen one (`rfl` between the two functions fails), and with "
            "the frozen tactic body kept verbatim the build FAILS on `(if "
            "s.isEmpty = true then tzStr else s) = s`. So the reproof is real "
            "work and the case is a genuine soundness probe rather than a "
            "restatement of gold. If it FAILS => SPEC-TOO-STRONG: the "
            "postcondition would be over-fit to one spelling of the emptiness "
            "test rather than to the behaviour. Ports nagini's pos-predicate as "
            "the third 'cheapest faithful reshape' positive; the guard is a "
            "reshaped test rather than an echoed @Pure predicate, since that "
            "helper has no counterpart on this carrier. AUDIT REPLACEMENT for "
            "the discarded pos-early-return — see the AUDIT RECORD."
        ),
    },

    # ---- admissibility (must VERIFY) --------------------------------------
    {
        "id": "admiss-f2p-ground-instances",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation must be SATISFIABLE at the concrete input shapes the "
            "change is about. This carrier is total and the obligation carries NO "
            "precondition hypothesis, so nothing here can be PRECOND-TOO-STRONG "
            "in the nagini sense — but that is NOT a reason to drop the lane: the "
            "analogue on a total carrier is the obligation being UNSATISFIABLE at "
            "an F2P-shaped input, and this case tests it directly by discharging "
            "the frozen postcondition at three ground inputs BY EVALUATION "
            "(`decide`), as `have`s ahead of the frozen tactic body which is then "
            "carried VERBATIM. The three inputs are the three observationally "
            "distinct label shapes at F2P-shaped values: a constant-offset zone "
            "advertising an offset designation that DIFFERS from its full textual "
            "form, a named zone advertising no label at all, and a zone "
            "advertising a blank label. If any FAILS the modeled behaviour is "
            "unsatisfiable at exactly the input the F2P exercises. The `have`s "
            "are MEASURED load-bearing rather than decorative: carried onto the "
            "pre-change impl the first one fails at its OWN line by `decide` "
            "finding the proposition false, independently of the frozen proof. "
            "Nothing is assumed — statement byte-identical, no new "
            "declaration/axiom/sorry/native_decide. SECOND-AUDIT ADDITION: the "
            "port recorded this lane as N/A on the ground that there is no "
            "precondition; see the AUDIT RECORD. Ports nagini's "
            "admiss-bothbranches."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) -----------------------------
    {
        "id": "weak-always-full",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_FULL,
        "refinement": (
            "This is the PRE-CHANGE behaviour verbatim: the short self-reported "
            "label is never consulted and the full textual form is always "
            "emitted. Its faithful real counterpart is exactly the state the "
            "problem statement reports as the regression — a fixed-offset zone "
            "rendering as its full name instead of its offset designation. The "
            "F2P test asserts the offset designation for that zone, so this "
            "faithful patch fails it and does NOT resolve; a rival verifying "
            "here would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by CLAUSE 1 (∀ s, tzLabel = some s → s ≠ \"\" → result = "
            "s): at a present, non-empty short label that differs from the full "
            "textual form the result must be the label, and this impl returns "
            "the full form. Attacks the discriminating clause over the "
            "present-and-non-empty sub-domain of tzLabel, and it is also the "
            "rival that most needs tzStr varied — it returns tzStr verbatim, so "
            "any witness holding tzStr equal to the label would not see it. If "
            "it VERIFIES => SPEC-TOO-WEAK. Ports nagini's wrong-always-full."
        ),
        # (some "S1", "F1"): gold => "S1" (clause 1), rival => "F1". Clause 1
        # instantiated at the literal is refuted by the rival's computed result.
        "witness": _wit_clause1(
            '"S1"', '"F1"',
            "present non-empty label: the spec pins the result to the label, "
            "the rival emits the full textual form"),
    },
    {
        "id": "weak-always-short",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_SHORT,
        "refinement": (
            "Emitting the short self-reported label unconditionally, with the "
            "empty label standing in for absence, drops the fallback entirely. "
            "Its faithful real counterpart returns nothing usable for a NAMED "
            "zone, which does not advertise a short label at all — while the F2P "
            "test asserts the full textual form for exactly those named zones. "
            "So the faithful patch fails the F2P on the named-zone rows and does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by CLAUSE 2 ((tzLabel = none ∨ tzLabel = some \"\") → "
            "result = tzStr): whenever the short label does not win, the result "
            "must be the full textual form, and this impl emits the (possibly "
            "empty) label instead. Wrong on BOTH falsity cases, so it is refuted "
            "at the `some \"\"` disjunct — the point that separates it from the "
            "near-miss weak-absent-yields-empty, which errs only on absence. "
            "Attacks the empty-label boundary of tzLabel. If it VERIFIES => "
            "SPEC-TOO-WEAK. Ports nagini's wrong-always-short."
        ),
        # (some "", "F6"): gold => "F6" (clause 2, Or.inr), rival => "".
        "witness": _wit_clause2(
            '(some "")', '"F6"', "Or.inr rfl",
            "present but EMPTY label: the spec pins the result to the full "
            "textual form, the rival emits the empty label"),
    },
    {
        "id": "weak-inverted-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_INVERTED,
        "refinement": (
            "Inverted selection — the full textual form wins when the short "
            "label carries content, and the short label is emitted when it does "
            "not. Its faithful real counterpart is wrong on BOTH F2P families at "
            "once: a fixed-offset zone renders as its full name (the reported "
            "regression) and a named zone renders as nothing usable. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by BOTH clauses simultaneously; the witness discharges it "
            "via CLAUSE 1, at a present non-empty label distinct from the one "
            "weak-always-full is refuted at, so the two rivals do not share an "
            "input point. Attacks the direction of the selection itself rather "
            "than either boundary. If it VERIFIES => SPEC-TOO-WEAK. Ports "
            "nagini's wrong-swap."
        ),
        # (some "S2", "F3"): gold => "S2" (clause 1), rival => "F3".
        "witness": _wit_clause1(
            '"S2"', '"F3"',
            "present non-empty label: the spec pins the result to the label, "
            "the inverted selection emits the full textual form"),
    },
    {
        "id": "weak-empty-label-wins",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTY_WINS,
        "refinement": (
            "The emptiness BOUNDARY is dropped: the fallback fires only on "
            "absence, so a short label that is present but carries no content "
            "wins and is emitted as-is. Its faithful real counterpart treats an "
            "advertised-but-blank label as a usable display name, where the "
            "required behaviour is to fall through to the full textual form — "
            "the blank string is not an acceptable rendering for any zone the "
            "F2P covers, so the faithful patch diverges on exactly that "
            "sub-domain and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by CLAUSE 2 via its `some \"\"` disjunct: a present-but-"
            "empty label is a falsity case, so the result must be the full "
            "textual form, and this impl emits the empty label. Attacks the "
            "emptiness boundary specifically — it handles ABSENCE correctly, so "
            "only the empty-label sub-domain of tzLabel exposes it, and a "
            "battery probing absence alone would miss it. If it VERIFIES => "
            "SPEC-TOO-WEAK (the boundary would be hollow). Ports nagini's "
            "wrong-drop-empty."
        ),
        # (some "", "F4"): gold => "F4" (clause 2, Or.inr), rival => "".
        "witness": _wit_clause2(
            '(some "")', '"F4"', "Or.inr rfl",
            "present but EMPTY label: the spec falls through to the full "
            "textual form, the rival lets the empty label win"),
    },
    {
        "id": "weak-absent-yields-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ABSENT_EMPTY,
        "refinement": (
            "A NEAR-MISS: both present branches are gold-exact and only ABSENCE "
            "is mishandled, emitting the empty label rather than falling back to "
            "the full textual form. Its faithful real counterpart renders a "
            "NAMED zone — one that advertises no short label at all — as the "
            "empty string, while the F2P asserts the full textual form for "
            "exactly those rows. It therefore fails the F2P on the named-zone "
            "families and does NOT resolve, even though it gets every "
            "fixed-offset row right."
        ),
        "rationale": (
            "REJECTED by CLAUSE 2 via its `none` disjunct: an absent short label "
            "is a falsity case, so the result must be the full textual form, and "
            "this impl emits the empty label. This is the rival that shows the "
            "two disjuncts of the fallback clause are INDEPENDENT obligations — "
            "it satisfies the `some \"\"` disjunct and violates only the `none` "
            "one, so its witness must sit at `none`, the sole input that exposes "
            "it. If it VERIFIES => SPEC-TOO-WEAK (the absence case would be "
            "unpinned). No direct nagini counterpart: on that carrier the absent "
            "and empty labels were both reachable through one sequence-valued "
            "field, whereas here `none` is a separate constructor and deserves "
            "its own rival."
        ),
        # (none, "F5"): gold => "F5" (clause 2, Or.inl), rival => "".
        "witness": _wit_clause2(
            "none", '"F5"', "Or.inl rfl",
            "ABSENT label: the spec pins the result to the full textual form, "
            "the rival emits the empty label"),
    },
    {
        "id": "weak-empty-full-substituted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTY_FULL_SUBST,
        "refinement": (
            "The TIGHTEST near-miss here: the selection is gold-exact "
            "everywhere, and the sole divergence is that when the fallback "
            "fires and the full textual form is itself EMPTY, a non-empty "
            "stand-in is emitted in its place. Its faithful real counterpart "
            "substitutes a placeholder for a zone whose full textual form "
            "renders empty, where the required behaviour is to emit that form "
            "verbatim however empty it is — the fallback clause pins the result "
            "to the carried value itself, not to a usable-looking value. It "
            "diverges from the required behaviour on exactly that sub-domain and "
            "so does NOT resolve."
        ),
        "rationale": (
            "REJECTED by CLAUSE 2 ((tzLabel = none ∨ tzLabel = some \"\") → "
            "result = tzStr): the clause pins the result to tzStr ITSELF, so no "
            "stand-in may be substituted for it — not even when tzStr is empty "
            "and the substitute looks more useful. Attacks the second binder's "
            "OWN emptiness boundary, which no other case in this battery makes "
            "load-bearing: every other witness holds tzStr non-empty, and this "
            "rival agrees with the frozen impl at every one of those points, so "
            "it is invisible to all five of them and visible only at tzStr = "
            "\"\". That is why it is refuted at `(none, \"\")` rather than at "
            "the `(none, \"F5\")` weak-absent-yields-empty uses. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the fallback clause would pin only the SHAPE of "
            "the full textual form and not its value). AUDIT ADDITION: no "
            "nagini counterpart — that carrier's sequence-valued full_name made "
            "the empty rendering unreachable through the field, whereas `String` "
            "here admits `\"\"` as an ordinary inhabitant."
        ),
        # (none, ""): gold => "" (clause 2, Or.inl), rival => "?". Rebuilt by
        # hand during the audit: rival exit 0, gold exit 1 with `decide` proving
        # `¬implementation_getTimezoneName none "" = ""` FALSE — a semantic
        # refutation of the concrete claim, not a syntactic failure.
        "witness": _wit_clause2(
            "none", '""', "Or.inl rfl",
            "ABSENT label AND an empty full textual form: the spec pins the "
            "result to that form verbatim, the rival substitutes a stand-in"),
    },
]


# The axiom lane belongs to G-AX and this gate ignores AXIOM_TESTS. There is no
# consumed callee axiom and no opaque callee here anyway: both observables enter
# as plain data and the selection between them is modeled DEEPLY over the
# transparent Option String / String carrier (mapping.md records zero axioms and
# zero deep-model references).
AXIOM_TESTS = []


# ===========================================================================
# AUDIT RECORD — independent adversarial re-derivation of this battery.
#
# The port recorded G-PBT SOUND. A recorded SOUND says every case BEHAVED as
# declared; it does not say the battery earned it. What follows is what an
# independent audit actually RAN, and the two defects it repaired above.
#
# --- STRUCTURAL RESULT: the frozen spec is FUNCTIONAL (machine-checked) -------
# The strongest fact about this obligation, and it was proven rather than argued.
# Appended to the frozen file and elaborated (exit 0):
#
#   theorem audit_spec_pins_result :
#       ∀ (tzLabel : Option String) (tzStr r : String),
#         problem_spec_getTimezoneName tzLabel tzStr r →
#           r = implementation_getTimezoneName tzLabel tzStr
#
# The postcondition therefore pins `result` UNIQUELY at every input of both
# binders: the two clauses jointly cover the carrier (none / some "" / some s
# with s ≠ "") and each pins the result to a carried value. Consequences that
# matter for judging this battery:
#   * SPEC-TOO-WEAK is unreachable for any impl that differs from the frozen one
#     at ANY single input — a rival verifies only if it is pointwise equal to
#     gold, in which case it is not wrong. No output component is left free, so
#     the §0.5 frame analogue is discharged.
#   * every reject case's rejection is therefore attributable to the spec once
#     its witness discriminates, and the witnesses below all do;
#   * the residual risk in this cell was never a weak spec: it was VACUOUS CASES
#     (a positive that is really gold, a rival no witness can see). Both defects
#     found were of exactly that kind, and both are repaired above.
#
# --- ATTACK A (statement integrity): CLEAN -----------------------------------
# All 8 case modules diffed against the frozen file. Every one keeps the
# `theorem correct_getTimezoneName` statement BYTE-IDENTICAL; the five reject
# cases keep the frozen tactic body verbatim (no rival retunes a script to
# manufacture its own rejection); only the impl region — plus, for the three
# positives, the proof body — differs. No hypothesis is weakened or restated.
#
# --- ATTACK B (witness discrimination, re-derived): all five CONFIRMED --------
# Every reject witness was rebuilt from scratch through the gate's own
# `witness_file` assembly and built TWICE. Rival exit / gold exit:
#   weak-always-full          0 / 1     weak-empty-label-wins      0 / 1
#   weak-always-short         0 / 1     weak-absent-yields-empty   0 / 1
#   weak-inverted-selection   0 / 1
# and the gold-side failure is a SEMANTIC refutation in every case, not a
# missing identifier, type error, unfolding failure or timeout — each reads
#   `Tactic 'decide' proved that the proposition
#      ¬implementation_getTimezoneName <the input> = <the pinned value> is false`
# i.e. the kernel evaluated the concrete claim and found gold SATISFIES the
# clause there. No witness binds a hypothesis, so no consistency probe is owed
# (and none is faked). Each witness names the input it discriminates at, and
# none is a tautology: re-checked directly, each rival's value differs from
# gold's at its own witness point while AGREEING with gold elsewhere.
#
# --- ATTACK C (is the rival wrong, or just different?): all six OBSERVABLE ----
# Each rival was defined as a standalone function beside gold and its divergence
# decided by the kernel: `audit_riv_X <witness input> ≠ implementation_... <same>`
# elaborates by `decide` for all of them. So none is a mere reshape, and none is
# definitionally equal to gold on this carrier. Their agreement points were
# checked too, which is what makes them partial-domain rivals rather than global
# constants (e.g. weak-absent-yields-empty agrees with gold at both `some "S1"`
# and `some ""`, diverging only at `none`).
#
# --- ATTACK D (SPEC-TOO-WEAK probe): 4 NEW wrong impls, none verified --------
# Written to hit what the shipped rivals leave alone, each tried under BOTH the
# frozen tactic body and the reshaped one (8 builds, all exit 1):
#   * trim-then-test  — treats an all-whitespace label as absent. Agrees with
#     gold except on non-empty all-whitespace labels. REJECTED, and by the value
#     clauses: `¬"".trim = "" → "" = tzStr` / `s.trim = "" → tzStr = s`.
#   * case-folded label — emits the winning label lowercased. REJECTED on
#     `s.toLower = s`, i.e. CLAUSE 1 refusing any transformation of the label.
#   * one-character labels fall through — REJECTED on `s.length ≤ 1 → tzStr = s`.
#   * single-label special case (`s ≠ "" ∧ s ≠ "X"`) — a rival wrong at ONE label
#     value no shipped witness sits at. REJECTED on the same clause.
# All four are consistent with the functionality theorem above: differing from
# gold anywhere is fatal. NO spec hole was found, and none can exist for a
# same-shape impl given `audit_spec_pins_result`.
#
# --- ATTACK E (SPEC-TOO-STRONG probe): correct reshapes are ACCEPTED ----------
# New faithful reshapes, all of which the spec ADMITS once the proof is closed:
#   * boolean emptiness guard        VERIFIES (now shipped as pos-boolean-guard)
#   * `Option.filter` then `getD`    VERIFIES (a different data shape entirely)
#   * redundant-inner-guard reshape  VERIFIES
#   * `for` over `tzLabel.toList`    VERIFIES (loop-shaped, `forIn`-elaborated)
#   * helper-predicate guard         VERIFIES (an impl-region `def` used as the
#     guard — the closest counterpart to nagini's echoed @Pure predicate)
# The first audit recorded one reshape (`label.length = 0` as the emptiness test)
# it could NOT close, marking it uncertain rather than claiming a hole — correctly,
# since the bridging lemma names it tried are genuinely absent under this pin
# (`String.length_eq_zero`, `String.length_eq_zero_iff`,
# `String.eq_empty_of_length_eq_zero` all Unknown constant, re-confirmed). The
# SECOND audit closed it: the bridge is a case split on the underlying character
# list rather than a named `String` lemma —
#   have hl : ¬ s.length = 0 := by
#     intro hz; apply hs; rcases s with ⟨l⟩
#     cases l with | nil => rfl | cons a t => simp [String.length] at hz
# — after which `simp [hl, hs]` closes both clauses and the reshape VERIFIES
# (exit 0). So that reshape is ADMITTED too and the uncertainty is retired: it was
# a missing proof, as suspected, and not a spec hole. Six correct reshapes now
# verify, including two that change the data shape.
#
# --- DEFECT 1 (REPAIRED): a positive that was really gold --------------------
# The battery's third positive, `pos-early-return`, claimed: "the frozen tactic
# script no longer closes the reshaped block, so the proof is honestly
# re-closed." BOTH halves of that are false, measured:
#   * built with the FROZEN proof body kept verbatim, it VERIFIES (exit 0) — the
#     frozen script closes it untouched, so `_REPROOF` was never doing any work;
#   * `example : <early-return impl> = <frozen impl> := by rfl` ELABORATES (exit
#     0): the two are DEFINITIONALLY EQUAL. The do-block reshape is a spelling of
#     the same term, not a different impl.
# So it was a positive control that tested nothing while passing honestly — the
# §2 vacuity mode exactly. It is DROPPED and replaced by pos-boolean-guard, whose
# non-triviality is measured in both directions (not defeq to gold: `rfl` fails;
# frozen script does NOT close it: fails on `(if s.isEmpty = true then tzStr else
# s) = s`). For contrast the other two shipped positives were checked the same
# way and are sound: `rfl` between each and gold FAILS (not defeq) and the frozen
# script FAILS on both (`(if s = "" then tzStr else s) = s`, `(if (some s).getD ""
# = "" then tzStr else (some s).getD "") = s`), so their reproofs are real.
#
# --- DEFECT 2 (REPAIRED): a binder varied but not load-bearing ---------------
# The header claimed tzStr was "NEVER held fixed, so a rival that ignored the
# full textual form (or substituted a constant for it) cannot agree with gold at
# every probed point". The five values are distinct, but they are five spellings
# of ONE point as far as the spec's verdict goes: all are non-empty, and tzStr's
# only boundary is its emptiness. A rival that substitutes a stand-in for the
# full textual form *only when that form is empty* agrees with gold at all five
# witness inputs and is invisible to the whole battery — i.e. the claim as
# written was false. Demonstrated by building that rival: it is REJECTED (exit 1)
# and its witness discriminates, rebuilt by hand — rival exit 0, gold exit 1 with
# `decide` proving `¬implementation_getTimezoneName none "" = ""` FALSE. It now
# ships as `weak-empty-full-substituted`, and the coverage prose above is
# corrected to say why that point is load-bearing rather than merely distinct.
#
# --- ATTACK F (omission re-derivation): per-case verdicts --------------------
# The port dropped four nagini cases. Each was re-derived independently, and two
# of the recorded reasons were WRONG even though the dispositions were right:
#   * pos-predicate       EXPRESSIBLE — the port called it unportable ("there is
#     no such helper on this carrier, the pure region being empty"), but a
#     variant may add an impl-region helper `def`, and the audit LANDED it:
#     `presentAndNonempty : Option String → Bool` used as the guard VERIFIES
#     (exit 0). It is not shipped only because pos-boolean-guard already occupies
#     the third-positive slot with a stronger reshape; the false reason is
#     corrected above.
#   * frame-mut-short/full  INEXPRESSIBLE — demonstrated, not asserted. A local
#     rebind of both inputs is invisible to the obligation (that impl VERIFIES),
#     and the actual overwrite-then-emit attempt is rejected as a plain CLAUSE 1
#     value error, i.e. it collapses onto weak-always-full. Nothing distinct to
#     port. Both comments above now carry this evidence instead of the bare
#     "there is no heap" argument.
#   * wrong-nonterm        INEXPRESSIBLE as a scoring case, but NOT for the
#     reason recorded. A diverging impl IS writable here (`partial def` with a
#     self-call); it is rejected on `unfold failed to unfold
#     implementation_getTimezoneName` — a tactic wall, and with the impl
#     irreducible no `decide` witness can discriminate either, so the case could
#     only ever be inconclusive. Comment corrected; the settled velvet divergence
#     hole is cited, not re-measured.
#   * admiss-bothbranches  EXPRESSIBLE — the first audit's verdict here was
#     WRONG, and it is the one defect of this battery that a recorded SOUND was
#     actively hiding. "The obligation has NO precondition hypothesis, so nothing
#     could be PRECOND-TOO-STRONG" is true about preconditions and is not a reason
#     the lane is vacuous: on a TOTAL carrier the analogue is the obligation being
#     UNSATISFIABLE at an F2P-shaped input, which a positive discharging the
#     obligation at that concrete input tests directly. Landed by the second audit
#     rather than argued about: three ground instances at F2P-shaped values,
#     `decide`d as `have`s ahead of the frozen tactic body carried verbatim,
#     VERIFY (exit 0), and the first one FAILS at its own line against the
#     pre-change impl — so the lane is real, not decorative. Now shipped as
#     `admiss-f2p-ground-instances`. Independently flagged by
#     scripts/pbt_coverage.py, which reported this battery as testing
#     ['soundness', 'uniqueness'] and not PRECOND-TOO-STRONG.
#   * ungrounded-oracle echo / AXIOM_TESTS  N/A as recorded — both clause
#     right-hand sides are the function's own arguments and the axioms region is
#     empty, so there is no answer-key term to echo.
#
# Nothing in the FROZEN artifact was edited: no Solution.lean, no meta.json, no
# instance.json. No defect in the frozen spec was found — `audit_spec_pins_result`
# is the positive evidence for that, not merely the absence of a counterexample.
#
# ===========================================================================
# SECOND AUDIT RECORD — independent re-derivation of the FIRST audit's findings.
#
# The first audit's own conclusions are claims like any other, so they were
# re-measured rather than inherited. Everything it asserted about the SHIPPED
# cases held; the defect it left behind is a whole missing LANE.
#
# --- ATTACK A (statement integrity): CLEAN, re-derived ------------------------
# All 9 case modules diffed against the frozen file line-by-line. Every module
# differs ONLY inside `-- impl-start/-- impl-end` (plus the proof body for the
# three positives, and a proof-body PREFIX for the admissibility case). The
# `theorem correct_getTimezoneName` statement is byte-identical in all 9 — checked
# by variant_scope.lean_obligations equality, not by eye — and the
# `problem_spec_getTimezoneName` definition is untouched. No hypothesis is
# weakened, restated or reformatted.
#
# --- ATTACK B (witness discrimination): all six re-CONFIRMED ------------------
# Every witness rebuilt from scratch through the gate's own witness_file assembly
# and built on both sides. Rival exit / gold exit, all six: 0 / 1. Each gold-side
# failure is a PLAIN EVALUATION —
#   `Tactic 'decide' proved that the proposition
#      ¬implementation_getTimezoneName <input> = <pinned value> is false`
# — i.e. the kernel computed the concrete claim and found gold SATISFIES the
# clause there. No missing identifier, no type error, no unfolding failure, no
# timeout, and no stuck reduction (nothing in this cell reduces through
# Classical.choice or Rat.inv). No witness binds a hypothesis, so no consistency
# probe is owed; consistency_probe returns None for all six, verified directly.
#
# --- ATTACK B′ (FORGERY test): all six carry INFORMATION ----------------------
# Not skipped despite the signatures being plain evaluations. For each case a
# second file was built differing from the witness ONLY in what it CLAIMS — the
# spec HOLDS at that same input, i.e. the exact opposite of the refutation — and
# built on both sides. Every one inverted cleanly:
#   gold exit 0 / rival exit 1, the rival's failure being
#   `Tactic 'decide' proved that the proposition ... is false`.
# So gold's exit code TRACKS the claim rather than the file: flipping the claim
# flips the verdict on both sides. A witness asserting gold is correct there would
# have been rejected, which is what makes the recorded rejections informative.
#
# --- ATTACK C (wrong, or merely different?): all six OBSERVABLE ---------------
# Each rival was placed beside a renamed COPY of the frozen impl in one file (with
# the proof region stripped, so the rival's own broken tactic script could not
# contaminate the probe — the first pass at this measured only that script
# failing) and the divergence decided by the kernel. `<rival> <pt> ≠ <gold> <pt>`
# elaborates by `decide` at each rival's own witness point, all six exit 0.
# The full agreement map over seven probed points, which is what separates a
# near-miss from a global constant:
#   weak-always-full           diverges at (some "S1","F1"), (some "S2","F3"), (some "X","")
#   weak-always-short          diverges at (some "","F4"), (some "","F6"), (none,"F5")
#   weak-inverted-selection    diverges at ALL SIX distinct probed points
#   weak-empty-label-wins      diverges at (some "","F4"), (some "","F6") only
#   weak-absent-yields-empty   diverges at (none,"F5") ONLY — the near-miss claim
#                              is exact: it agrees with gold everywhere else
#   weak-empty-full-substituted diverges at (none,"") ONLY — the tightest
#                              near-miss claim is also exact, confirming DEFECT 2
#                              of the first audit was a real defect and its
#                              repair a real one
# So no rival is definitionally equal to gold, none is a mere reshape, and the
# two near-miss rationales claim exactly the sub-domain the manifest demonstrates.
#
# --- POSITIVES re-measured: none is gold in disguise -------------------------
# The first audit's DEFECT 1 was a positive that was secretly definitionally
# equal to gold, so all three survivors were re-checked the same way, both halves:
#   * NOT defeq to gold: for each, a file pairing the variant impl with a renamed
#     copy of the frozen impl and asserting `<variant> = <gold copy> := by rfl`
#     FAILS — `Tactic 'rfl' failed ... is not definitionally equal`. All three.
#   * the FROZEN tactic body does NOT close them: with the frozen proof restored
#     verbatim each build FAILS, at the reshaped guard specifically —
#       pos-negated-guard          `(if s = "" then tzStr else s) = s`
#       pos-normalize-then-select  `(if (some s).getD "" = "" then tzStr else
#                                    (some s).getD "") = s`
#       pos-boolean-guard          `(if s.isEmpty = true then tzStr else s) = s`
# So each reproof is real work and each positive is a genuine reshape.
#
# --- ATTACK D (SPEC-TOO-WEAK): 5 NEW wrong impls, none verified --------------
# Aimed at what the shipped rivals leave alone, each tried under BOTH the frozen
# tactic body and the reshaped one (10 builds, all exit 1):
#   * label-equals-full falls back — wrong ONLY when the label happens to equal
#     the full form, a coincidence no shipped witness sits at. REJECTED.
#   * one-character label doubled — wrong only at length-1 labels. REJECTED.
#   * both-empty substitutes a space — wrong only when BOTH inputs are empty, the
#     narrowest point in the carrier. REJECTED.
#   * winning label trimmed — wrong only on labels with surrounding whitespace.
#     REJECTED.
#   * whitespace-only label treated as absent — this is the exact edge G-PANEL-2
#     reasoned about (`" "` is Python-truthy, so gold must emit it). REJECTED.
# NO spec hole. And none can exist for a same-shape impl: `audit_spec_pins_result`
# was re-derived and re-elaborated (exit 0), so the postcondition pins `result`
# UNIQUELY at every input and any impl differing from gold ANYWHERE is rejected.
#
# --- ATTACK E (SPEC-TOO-STRONG): correct reshapes ACCEPTED -------------------
# Two NEW faithful reshapes beyond the first audit's five:
#   * `match tzLabel, tzStr with` — a nested match on the PAIR. VERIFIES.
#   * `s.length = 0` as the emptiness test — the reshape the first audit could
#     NOT close and recorded as uncertain. Now CLOSED and VERIFIES; see the
#     ATTACK E note above for the bridge. The uncertainty is retired.
# One reshape I could not close is recorded as uncertain, not as a hole:
# `Option.filter (fun s => !s.isEmpty)` then `getD`. The first audit reports it
# verifying and I do not doubt that; my own `Option.filter` unfoldings left
# `(if s.isEmpty = false then some s else none).getD tzStr = s` open and I did not
# land the `simp` set. A missing proof of mine, and the neighbouring reshapes
# verify, so there is no sign of over-fitting in either direction.
#
# --- DEFECT 3 (REPAIRED): the whole ADMISSIBILITY LANE was missing -----------
# The one place the recorded SOUND was hollow, and it is an omission rather than a
# bad case: the battery had NO kind="admissibility" case, so of the three
# directions this gate tests it tested two. The recorded reason — "the lean
# obligation carries NO precondition hypothesis, so there is nothing that could be
# PRECOND-TOO-STRONG" — is precisely the reason that does not count: on a total
# carrier the analogue is the obligation being UNSATISFIABLE at an F2P-shaped
# input. scripts/pbt_coverage.py flags this independently. It is not an idle lane
# either: 412 of 500 lean batteries carry one.
# LANDED rather than argued: `admiss-f2p-ground-instances` above discharges the
# frozen postcondition at three F2P-shaped ground inputs by evaluation and
# VERIFIES (exit 0), and the `have`s are measured LOAD-BEARING — carried onto the
# pre-change impl the first fails at its OWN line, `decide` finding
# `(∀ s, some "+10" = some s → s ≠ "" → "Etc/GMT-10" = s) ∧ ...` false, whether or
# not the frozen tactic body closes.
#
# Nothing in the FROZEN artifact was edited by this audit either: Solution.lean,
# meta.json and instance.json are untouched. No defect in the frozen SPEC was
# found in either direction — attack D found no impl the spec wrongly admits and
# attack E none it wrongly rejects, and `audit_spec_pins_result` explains why the
# first of those is structural rather than lucky.
# ===========================================================================
