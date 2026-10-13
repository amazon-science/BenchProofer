"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-26208 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region is changed, so ``markers.same_spec`` holds and every
``theorem correct_*`` STATEMENT stays byte-identical). ``expect:"verify"`` passes
iff (in scope AND the file elaborates with the obligation closed);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (two independent construction sites, identical obligation):

  stepA (source : Slot) : Slot
  stepB (source : Slot) : Slot
      result = source ∧ isPresent result = isPresent source

  where ``Slot = Option Nat`` models one optional field of a component
  (``none`` = absent, ``some t`` = present, identified up to identity by the tag
  ``t``) and ``isPresent = (·).isSome``. Each site models a construction step
  building a new object that re-uses ONE component of the source object; the
  observable is what the new object's re-used component holds for that field, as
  a function of what the source's corresponding component holds.

  The clause is written as two conjuncts, but they are NOT independent — this is
  a carrier fact worth stating precisely, because the obvious reading overclaims:
      (i)  IDENTITY — ``result = source``: the secondary frame's shared
           coordinate carries the SAME setting as the source, not merely a
           present one;
      (ii) PRESENCE — ``isPresent result = isPresent source``: it reports present
           exactly when the source does.
  Conjunct (ii) is IMPLIED by conjunct (i) (``isPresent`` is a function, so
  ``result = source`` forces it by congruence), hence the whole postcondition is
  logically EQUIVALENT to ``result = source`` alone. Both facts were checked with
  the real verifier as standalone theorems against the frozen spec::

      theorem presence_implied_by_identity (s r : Slot) (h : r = s) :
          isPresent r = isPresent s := by subst h; rfl
      theorem spec_pins_uniquely (s r : Slot) :
          problem_spec_stepA s r ↔ r = s   -- elaborates, exit 0

  Two consequences the battery is built around rather than around a fictional
  two-clause decomposition:
    * There is no "presence-only" attack surface: no rival can satisfy identity
      while breaking presence, so a case cannot isolate (ii). What a rival CAN do
      is satisfy (ii) while breaking (i) — presence agrees, identity does not —
      and that asymmetry is what ``wrong-object-present`` exercises.
    * Because the spec pins ``result`` UNIQUELY at every input, SPEC-TOO-WEAK is
      unreachable in principle here: any impl that verifies is extensionally the
      identity function. The reject lane's job is therefore not to hunt for an
      admitted wrong impl but to certify that each rejection is attributable to
      the spec at a concrete input, which is exactly what the witnesses do.
  The two sites are modeled and pinned SEPARATELY (each shared coordinate is
  observed on its own), so a correct rendering at one site does not discharge the
  other.

INPUT DOMAIN COVERAGE. Each spec has a single input binder, ``source``. Since the
postcondition reduces to ``result = source``, the semantically distinct classes
of that binder are ABSENT (``none``) and PRESENT (``some t``), and a battery that
probed only present points would be varying the binder without varying the
spec's shape. The reject witnesses therefore cover both classes at BOTH sites:

      site   source     refuted rival                what the point buys
      A      some 7     prepatch (result absent)     present source, carry-over
                                                       omitted
      A      some 1     wrong-object (result some 0) present source: rival is
                                                       PRESENT, so (ii) agrees and
                                                       only identity can reject —
                                                       the sharpest identity probe
      A      none       wrong-object (result some 0)  ABSENT source at site A:
                                                       over-report direction
      B      none       wrong-object (result some 0) absent source at site B
      B      some 5     prepatch (result absent)     present source at site B

  Each site is probed at an absent point AND at present points, so neither
  obligation is pinned to one class of its binder.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — the ATTACK is vacuous, and the reason is
    narrower than "referential transparency" alone; stated precisely so the claim
    is checkable. The nagini rival writes to a half-permission input so that the
    postcondition falls out of the mutation, and its rejection is attributable to
    the PERMISSION SYSTEM, not to a postcondition. The transliteration was built
    and run rather than assumed::

        let mut source := source
        source := none          -- "overwrite the read-only input"
        let mut out : Slot := source

    It is rejected (exit 1) — but the shadowed rebinding cannot affect the spec,
    whose ``source`` is the theorem's binder, so what actually rejects it is that
    it now returns ``none``: it is the ``prepatch-absent-default`` rival wearing a
    mutation costume, and it is refuted by that case's existing witness. There is
    no permission lane to attest to on this carrier, so adding it would duplicate
    a rival already in the battery under a misleading name. Omitted as a
    DUPLICATE, not as inexpressible.

  * ADMISSIBILITY — APPLIES, and is carried (``admiss-ground-present-source``).
    The nagini sibling asserts its precondition ``source.descriptor is not None``
    is usable. It is true that each obligation here is universally quantified
    over ``source`` with NO precondition (the ``correct_*`` binder is
    ``∀ (source : Slot), …``), so there is no precondition term to
    re-express — but that does NOT make the lane vacuous, and reading it that way
    drops the only direction of this gate that detects PRECOND-TOO-STRONG. The
    analogue on a TOTAL carrier is the obligation being UNSATISFIABLE at exactly
    an F2P-shaped input, which is a real risk independent of any precondition: a
    postcondition can be written so that no output satisfies it at the very input
    the observed behavior exercises (mutually unsatisfiable conjuncts, an
    equality against a value the carrier cannot produce), and every soundness
    positive in this battery would still pass, because a positive quantifies over
    the binder and never pins a concrete point.

    So the case discharges the postcondition BY EVALUATION at the F2P-shaped
    input — a source that already carries a present setting, which is the shape
    the observed behavior exercises — as a ground ``have``, and only then closes
    the frozen obligation verbatim. That the ``have`` carries information rather
    than decorating the proof was checked in both directions with the real
    verifier:

        have hF2P : problem_spec_stepA (some 7) (some 8) := by
            unfold problem_spec_stepA isPresent; decide
        -- exit 1: `decide` proved `some 8 = some 7 ∧ ...` is FALSE

    i.e. the same ``have`` step asserting a WRONG output at that input FAILS, so
    the shipped case's exit 0 attests that the obligation really is satisfiable
    at the concrete point and is not a step ``decide`` would close regardless.
    It is distinguishable from a soundness positive precisely because it pins a
    concrete input where the positive quantifies.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the input
    (``result = source``, an equality against the input carrier itself); the
    bundle declares no ``opaque``/``axiom``, so there is no answer key an
    implementation could echo without doing the work. In its place the battery
    carries an honest structural-reshape POSITIVE CONTROL that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the bulk of the battery. Three
    rivals attack it: one leaves the shared coordinate at its freshly-created
    absent default (the pre-existing behavior — correct only when the source is
    itself absent), one carries a present-but-DIFFERENT setting (correct on
    presence, wrong on identity — the sharpest identity probe), and one is the
    prior wrong-object rival applied at site B only while site A stays correct
    (confirming the two sites are independently pinned).

  * SOUNDNESS POSITIVE — one, a structural reshape of BOTH impl sites that is
    NOT definitionally the frozen impl: start the shared coordinate at its fresh
    absent default and case-split on the source, re-establishing the setting in
    the present branch. `exact ⟨rfl, rfl⟩` does NOT close it (measured: exit 1,
    `Application type mismatch: rfl ... but is expected to have type`), so the
    obligation is genuinely REPROVEN by `cases source <;> simp` rather than
    re-run. If it were rejected the spec would be SPEC-TOO-STRONG.

    Deliberately NOT used as the positive: `let shared := source; out := shared`.
    A bound local is definitionally the thing it binds, so that variant's
    `Id.run` term is the frozen one up to `have`-zeta and the FROZEN tactic body
    closes it unchanged (measured: exit 0 with `exact ⟨rfl, rfl⟩`). It passes
    honestly and tests nothing — the spec was never asked a question it could
    have answered differently. Same reason `source.map (fun t => t)` is not used:
    `Option.map id` reduces per-constructor, so it is a spelling change, not a
    different computation.

NAGINI CASES — per-case verdict against the sibling's 6 SPEC cases:

  PORTED (attack behavior this bundle models):
    - ``pos-control-local-binding`` -> ``pos-reestablish-from-absent`` (both
      sites reshaped). The nagini original read the descriptor into a typed local
      first; on THIS carrier that is a no-op reshape (a local is definitionally
      its binding), so the port carries the same INTENT — a correct impl of a
      different executable shape — via a shape the carrier can actually
      distinguish: start absent and re-establish by case analysis. The frozen
      tactic body no longer closes it, which is the evidence the reshape is real.
    - ``prepatch-omit-copy``        -> ``prepatch-absent-default`` (both sites).
    - ``wrong-fresh-descriptor``    -> ``wrong-object-present`` (both sites; the
      identity-alone probe at a present source), plus ``wrong-object-at-absent``
      (added here, no nagini counterpart: the SAME rival refuted at site A's
      ABSENT point, so site A is probed on both classes of its binder and not
      only on present ones).
    - ``half-fix-vertical-only-broken`` -> ``half-fix-B-only-broken`` (site A
      correct, site B wrong — the two sites are independently pinned), plus
      ``half-fix-B-prepatch`` (added here, no nagini counterpart: the same
      independence probe at a second site-B input so stepB is exercised
      at two binder values rather than one).

  LEGITIMATELY OMITTED — no counterpart on this carrier (NOT dropped for being
  hard):
    - ``frame-mutate-source`` — the mandatory frame/permission-mutation rival.
      The closest transliteration WAS built and run (exit 1); it rejects, but as
      a duplicate of ``prepatch-absent-default`` rather than on a permission
      obligation, since a rebound local cannot reach the theorem's binder. Adding
      it would put a second name on a rival already present. See ADVERSARIAL READ.

  PORTED AS AN ANALOGUE (previously recorded here as vacuous, wrongly):
    - ``admiss-precond-usable`` -> ``admiss-ground-present-source``. The
      permission/precondition READABILITY assertion has no counterpart (no
      permissions, no precondition on this carrier), but the lane does: the
      obligation's SATISFIABILITY at an F2P-shaped concrete input. Landed and
      built (exit 0), with the wrong-output control failing (exit 1) so the
      ground step is known to carry information. See ADVERSARIAL READ.
    - ``AXIOM_TESTS`` — empty in nagini and dropped by design; the axiom lane is
      G-AX's, and this bundle consumes no callee axiom.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input. Each is stated directly against the spec predicate at
``decide``-able literals, and each was checked to hold of its rival AND to FAIL
on the frozen solution (so it discriminates rather than asserting a tautology).

Every witness was rebuilt independently and the gold-side failure was READ, not
just counted: each fails on the frozen solution with ``Tactic `decide` proved
that the proposition ¬(... ) is false`` — a SEMANTIC refutation of the concrete
claim (gold satisfies the spec at that input), not an unknown identifier, a type
mismatch, an unfolding failure, or a timeout. A gold-side failure for a syntactic
reason would not discriminate anything, and the gate cannot tell the two apart.
No witness binds a hypothesis, so all are literal-input refutations and the
consistency probe is not applicable (there are no assumptions to be vacuous).

FORGERY-TESTED (the check that a gold-side exit code carries information about
the CLAIM and not about the carrier). Reading an error and judging it "semantic"
is not evidence, so each of the five witnesses was rebuilt with the claim FLIPPED
— the leading ``¬`` dropped, so the file asserts gold is CORRECT at that input
and nothing else changes — against BOTH subjects. All five invert perfectly:

    witness (¬ …)      rival: exit 0        gold:  exit 1  (`decide` proved … false)
    forgery (no ¬)     rival: exit 1        gold:  exit 0  (elaborates, empty log)

So gold's exit code TRACKS the claim in both directions: the refutation fails
there and the affirmation succeeds there, which is exactly what a hollow case
cannot do (a hollow one prints the byte-identical error for both). These
witnesses close by plain evaluation — the gold-side message quotes the reduced
proposition itself (``(have out := some 7; pure out).run = some 7 ∧ …``) — so
this battery is in the plain-evaluation signature class, with none of the stuck
``decide`` / missing-``Decidable`` / loop-unification pathologies, and the
forgery pair confirms rather than merely asserts it.

DIVERGENCE lane: NOT SHIPPABLE HERE, and the reason is the witness rather than the
rejection. This bundle is a plain Lean artifact with no
``set_option loom.semantics.termination`` line at all (that option is the velvet
carrier's; ``grep`` on the frozen file finds none), so termination is Lean's own
definitional requirement: a diverging impl cannot be admitted as a ``def`` in the
first place. The closest thing the carrier allows was built —
``partial def implementation_stepA source := implementation_stepA
source`` — and it is REJECTED (exit 1), but it cannot be given a discriminating
witness: ``partial`` makes the definition irreducible, so the witness fails on the
RIVAL with ``Tactic `unfold` failed to unfold `implementation_stepA``` —
the rival half of the pair, which must succeed, does not. That is
``witness-unproven`` (an inconclusive outcome the gate refuses), not a refutation,
and it fails for a carrier reason rather than a spec one. So the class is
unshippable here for a demonstrated tooling reason, not a hard one, and it is
recorded as such rather than as vacuous.

AXIOM lane: EMPTY. No ``opaque``/``axiom`` is consumed; the behavior is a total
computation over ``source``, so there is no axiom-soundness / axiom-containment
obligation to probe here.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26208"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors: the FULL body of each impl region. Each is unique on
# _BASE only because of the A/B suffix in the def header — the two bodies are
# otherwise byte-identical, so anchoring on the body alone would not be unique.
# All edits stay strictly inside the `-- impl-start` / `-- impl-end` region, so
# same_spec is guaranteed and every `theorem correct_*` statement is untouched.
_IMPL_A = (
    "def implementation_stepA (source : Slot) : Slot := Id.run do\n"
    "  let mut out : Slot := source\n"
    "  return out"
)
_IMPL_B = (
    "def implementation_stepB (source : Slot) : Slot := Id.run do\n"
    "  let mut out : Slot := source\n"
    "  return out"
)


def _witness(fn, src_lit):
    """Refutation witness: the spec predicate FAILS of the rival's own output at
    one concrete input. Stated directly against `problem_spec_<fn>` at a literal,
    so `decide` settles it after unfolding. Checked to hold of the rival and to
    FAIL on the frozen solution (a real discriminator, not a tautology)."""
    return (
        f"example : ¬ problem_spec_{fn} {src_lit}\n"
        f"    (implementation_{fn} {src_lit}) := by\n"
        f"  unfold problem_spec_{fn} implementation_{fn} isPresent\n"
        f"  decide\n"
    )


# ===========================================================================
# POSITIVE CONTROL (soundness) — structurally different but CORRECT, and chosen
# so the difference is one the CARRIER can see. The shared coordinate starts at
# its fresh absent default and the source setting is re-established by case
# analysis: same function extensionally, different computation.
#
# Why not the obvious `let shared := source; out := shared` (the nagini shape):
# a bound local is definitionally its binding, so that term is the frozen one up
# to have-zeta and the FROZEN tactic body `exact ⟨rfl, rfl⟩` closes it unchanged
# (measured: exit 0). A positive the frozen proof discharges verbatim asks the
# spec no question. This one is NOT definitionally the frozen impl — with the
# frozen tactic body it FAILS (measured: exit 1, `Application type mismatch: rfl
# ... but is expected to have type ...`) — so the obligation must be genuinely
# REPROVEN for the new impl shape. The reproof is `cases source <;> simp`, which
# is the honest discharge of a real case split, not a weakening: the statement is
# byte-identical (variant_scope enforces that) and no axiom, sorry, helper lemma,
# or new theorem is introduced. `#print axioms` on the reproven obligations
# reports only [propext, Quot.sound] — Mathlib's ordinary simp-set dependencies,
# no sorryAx. Both sites are reshaped, so this one positive defends BOTH
# obligations. If this were rejected => SPEC-TOO-STRONG.
# ===========================================================================
_POS_A = (
    "def implementation_stepA (source : Slot) : Slot := Id.run do\n"
    "  let mut out : Slot := none\n"
    "  match source with\n"
    "  | none => pure ()\n"
    "  | some t => out := some t\n"
    "  return out"
)
_POS_B = (
    "def implementation_stepB (source : Slot) : Slot := Id.run do\n"
    "  let mut out : Slot := none\n"
    "  match source with\n"
    "  | none => pure ()\n"
    "  | some t => out := some t\n"
    "  return out"
)
# The frozen tactic body does not close the reshaped impl, so the positive must
# reprove. Only the tactic BODY changes; the statement stays byte-identical.
_PROOF_A = (
    "theorem correct_stepA : ∀ (source : Slot),\n"
    "    problem_spec_stepA source (implementation_stepA source) := by\n"
    "  intro source\n"
    "  unfold problem_spec_stepA implementation_stepA\n"
    "  exact ⟨rfl, rfl⟩"
)
_PROOF_B = (
    "theorem correct_stepB : ∀ (source : Slot),\n"
    "    problem_spec_stepB source (implementation_stepB source) := by\n"
    "  intro source\n"
    "  unfold problem_spec_stepB implementation_stepB\n"
    "  exact ⟨rfl, rfl⟩"
)
_REPROOF_A = (
    "theorem correct_stepA : ∀ (source : Slot),\n"
    "    problem_spec_stepA source (implementation_stepA source) := by\n"
    "  intro source\n"
    "  unfold problem_spec_stepA implementation_stepA isPresent\n"
    "  cases source <;> simp"
)
_REPROOF_B = (
    "theorem correct_stepB : ∀ (source : Slot),\n"
    "    problem_spec_stepB source (implementation_stepB source) := by\n"
    "  intro source\n"
    "  unfold problem_spec_stepB implementation_stepB isPresent\n"
    "  cases source <;> simp"
)
_pos = _swap(_BASE, _IMPL_A, _POS_A)
_pos = _swap(_pos, _IMPL_B, _POS_B)
_pos = _swap(_pos, _PROOF_A, _REPROOF_A)
_pos = _swap(_pos, _PROOF_B, _REPROOF_B)


# ===========================================================================
# ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at a normal,
# F2P-shaped input. Both impl regions stay the byte-identical frozen copy; only
# each obligation's TACTIC BODY gains a leading ground `have` that discharges the
# postcondition BY EVALUATION at a source already carrying a present setting —
# the shape the observed behavior exercises — before closing the frozen
# obligation verbatim. The statements stay byte-identical (variant_scope enforces
# it) and no declaration, axiom, sorry or helper lemma is added.
#
# Why this is not a second soundness positive: a positive quantifies over the
# binder, so it cannot detect an obligation that is unsatisfiable at one concrete
# point. This case pins that point. And the ground step was checked to carry
# information rather than to be closable regardless — the same `have` asserting a
# WRONG output at the same input fails:
#     have hF2P : problem_spec_stepA (some 7) (some 8)  -- exit 1,
#     `decide` proved `some 8 = some 7 ∧ (some 8).isSome = (some 7).isSome` FALSE
# while the shipped form is exit 0. If this were REJECTED, the obligation would be
# unsatisfiable at exactly a normal input => PRECOND-TOO-STRONG.
# ===========================================================================
_ADM_A = (
    "theorem correct_stepA : ∀ (source : Slot),\n"
    "    problem_spec_stepA source (implementation_stepA source) := by\n"
    "  intro source\n"
    "  have hF2P : problem_spec_stepA (some 7)\n"
    "      (implementation_stepA (some 7)) := by\n"
    "    unfold problem_spec_stepA implementation_stepA isPresent\n"
    "    decide\n"
    "  unfold problem_spec_stepA implementation_stepA\n"
    "  exact ⟨rfl, rfl⟩"
)
_ADM_B = (
    "theorem correct_stepB : ∀ (source : Slot),\n"
    "    problem_spec_stepB source (implementation_stepB source) := by\n"
    "  intro source\n"
    "  have hF2P : problem_spec_stepB (some 7)\n"
    "      (implementation_stepB (some 7)) := by\n"
    "    unfold problem_spec_stepB implementation_stepB isPresent\n"
    "    decide\n"
    "  unfold problem_spec_stepB implementation_stepB\n"
    "  exact ⟨rfl, rfl⟩"
)
_adm = _swap(_BASE, _PROOF_A, _ADM_A)
_adm = _swap(_adm, _PROOF_B, _ADM_B)


# ===========================================================================
# PREPATCH / PARTIAL-DOMAIN (uniqueness) — leave the shared coordinate at its
# freshly-created absent default; the source's setting is never carried over.
# This is the base_commit behavior at BOTH sites. Correct only when the source
# is itself absent, wrong whenever it carries a present setting.
# ===========================================================================
_PRE_A = _IMPL_A.replace("out : Slot := source", "out : Slot := none")
_PRE_B = _IMPL_B.replace("out : Slot := source", "out : Slot := none")
_pre = _swap(_BASE, _IMPL_A, _PRE_A)
_pre = _swap(_pre, _IMPL_B, _PRE_B)


# ===========================================================================
# WRONG-OBJECT / VALUE (uniqueness) — carry a present-but-DIFFERENT setting.
# At a PRESENT source the result is present (so the presence reading agrees) but
# it is not the source's setting, so the IDENTITY clause is the sole ground of
# rejection: the sharpest uniqueness probe, proving the spec is not satisfied by
# "any present setting". At an ABSENT source the same rival fails in the other
# direction (it advertises a setting the source does not have), which is why this
# module is refuted at both classes of the binder — `wrong-object-present` at
# `some 1` and `wrong-object-at-absent` at `none`. Both sites corrupted.
# ===========================================================================
_MSK_A = _IMPL_A.replace("out : Slot := source", "out : Slot := some 0")
_MSK_B = _IMPL_B.replace("out : Slot := source", "out : Slot := some 0")
_mask = _swap(_BASE, _IMPL_A, _MSK_A)
_mask = _swap(_mask, _IMPL_B, _MSK_B)


# ===========================================================================
# HALF-FIX (uniqueness) — site A carries the source correctly (gold), site B
# carries a wrong present setting. Confirms the two sites are independently
# pinned: a correct A does not discharge B's obligation. Must be rejected on
# site B's identity/presence clause.
# ===========================================================================
_half = _swap(_BASE, _IMPL_B, _MSK_B)  # site A stays the correct gold copy

# Second half-fix, prepatch flavor: site A correct (gold), site B left at the
# absent default. Probes site B at a DIFFERENT (present) point than the
# wrong-object half-fix, so stepB's obligation is exercised at two
# distinct inputs rather than pinned to one.
_half2 = _swap(_BASE, _IMPL_B, _PRE_B)  # site A stays the correct gold copy


SPEC_TESTS = [
    {
        "id": "pos-reestablish-from-absent",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos,
        "rationale": "structurally-different correct impl at BOTH sites: the "
                     "shared coordinate starts at its fresh absent default and "
                     "the source's setting is re-established by case analysis, so "
                     "the SAME function is computed by a DIFFERENT computation and "
                     "`result = source` still holds. Unlike a bound-local reshape "
                     "(which is definitionally the frozen impl and which the "
                     "frozen tactic body closes verbatim, exit 0 — a positive that "
                     "asks the spec nothing), this one is NOT definitionally "
                     "frozen: with `exact ⟨rfl, rfl⟩` it FAILS (exit 1, "
                     "`Application type mismatch: rfl ...`), so the obligation is "
                     "genuinely REPROVEN, by `cases source <;> simp`. The theorem "
                     "STATEMENTS are byte-identical and no axiom/sorry/helper "
                     "lemma is added (`#print axioms` on both reproven "
                     "obligations: [propext, Quot.sound] only). If this fails to "
                     "verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-ground-present-source",
        "kind": "admissibility",
        "expect": "verify",
        "module": _adm,
        "rationale": "the modeled obligation is SATISFIABLE at a normal, "
                     "F2P-shaped input: at a source that already carries a "
                     "present setting (`some 7` — the shape the observed "
                     "behavior exercises, where the carry-over is observable at "
                     "all) the postcondition is discharged BY EVALUATION as a "
                     "ground `have`, and only then is the frozen obligation "
                     "closed verbatim. Must verify; if it were rejected the "
                     "obligation would be unsatisfiable at exactly a normal "
                     "input — the total-carrier analogue of PRECOND-TOO-STRONG, "
                     "which no soundness positive can detect because a positive "
                     "quantifies over the binder instead of pinning a point. "
                     "Nothing is assumed: both impl regions are the "
                     "byte-identical frozen copy, the theorem STATEMENTS are "
                     "byte-identical, and no axiom/sorry/helper lemma or new "
                     "declaration is introduced — only a leading `have` inside "
                     "each existing tactic body. The ground step is known to "
                     "carry information rather than to be closable regardless: "
                     "the same `have` asserting a WRONG output at the same input "
                     "(`problem_spec_stepA (some 7) (some 8)`) FAILS "
                     "(exit 1, `decide` proved `some 8 = some 7 ∧ ...` is "
                     "false), while this form is exit 0. Re-expresses nagini's "
                     "`admiss-precond-usable`, whose `is not None` precondition "
                     "has no term-level counterpart on a carrier with no "
                     "precondition and no permissions.",
    },
    {
        "id": "prepatch-absent-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pre,
        "refinement": "verbatim the base_commit behavior: the secondary frame's "
                      "shared coordinate is left at its freshly-created absent "
                      "default, so when the source carries a present setting the "
                      "secondary frame reports absent. The F2P observes both that "
                      "the secondary frame's shared coordinate is present and that "
                      "it is the SAME setting as the source; with the carry-over "
                      "omitted the secondary frame's coordinate stays absent and "
                      "both observations fail. A patch matching this does NOT "
                      "resolve — it is this leg's prepatch.",
        "rationale": "REJECT on the identity clause: at a present source (`some 7`) "
                     "the rival returns `none`, so `result = source` is false (and "
                     "the presence reading falls with it — presence is implied by "
                     "identity here, not an independent second ground). Witness at "
                     "`source = some 7`, a present source, which is where the "
                     "missing carry-over is observable at all: at an absent source "
                     "this rival AGREES with the frozen impl, so the case is "
                     "correctly a partial-domain miss rather than a total one.",
        "witness": _witness("stepA", "(some 7)"),
    },
    {
        "id": "wrong-object-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mask,
        "refinement": "a faithful patch that gave the secondary frame's shared "
                      "coordinate a DIFFERENT present setting (a freshly built one "
                      "rather than the source's) would make it present but not the "
                      "same object. The F2P asserts object IDENTITY between the "
                      "secondary frame's shared coordinate and the source's; a "
                      "different object fails that identity assertion even though "
                      "it is non-absent, so the patch does NOT resolve.",
        "rationale": "REJECT from the IDENTITY conjunct `result = source` ALONE: at "
                     "a present source (`some 1`) the rival returns `some 0`, which "
                     "is present — so the PRESENCE reading `isPresent result = "
                     "isPresent source` AGREES (true = true) — yet `some 0 ≠ some "
                     "1`, so identity is the ONLY ground of rejection. Witness at "
                     "`source = some 1`, the input that isolates identity from "
                     "presence and proves the spec is not satisfied by 'any present "
                     "setting'. This is the one direction of the asymmetry that IS "
                     "available: presence cannot be broken while identity holds (it "
                     "is implied by it), but identity can be broken while presence "
                     "holds — which is exactly this case.",
        "witness": _witness("stepA", "(some 1)"),
    },
    {
        "id": "wrong-object-at-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _mask,
        "refinement": "the same faithful-but-wrong patch as above (the secondary "
                      "frame's shared coordinate is given a setting of its own "
                      "rather than the source's), refuted at the input where the "
                      "source carries NO setting: the secondary frame then "
                      "advertises a setting the source does not have, so values "
                      "placed along the shared coordinate would be read one way in "
                      "one frame and another way in the other. The F2P asserts the "
                      "secondary frame's shared coordinate IS the source's; a "
                      "fabricated one fails that, so the patch does NOT resolve.",
        "rationale": "same rival module as `wrong-object-present`, refuted at a "
                     "DIFFERENT and semantically distinct point of the binder: "
                     "`source = none`. The other site-A witnesses both sit at "
                     "PRESENT sources, so without this one stepA's "
                     "obligation is never probed on the absent class of its input — "
                     "the class where the failure direction is over-report "
                     "(the rival claims present, the source is absent) rather than "
                     "under-report. Since the postcondition reduces to `result = "
                     "source` (checked: `problem_spec_stepA s r ↔ r = s` "
                     "elaborates), absent vs present is exactly the distinction "
                     "worth spending a case on, and this covers site A on both.",
        "witness": _witness("stepA", "none"),
    },
    {
        "id": "half-fix-B-only-broken",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _half,
        "refinement": "matches a half-fix that carried the setting over at one "
                      "construction site but not the other: the F2P exercises each "
                      "site independently (parametrised over the two coordinates), "
                      "so the un-fixed site's assertion still fails. A partial fix "
                      "does NOT resolve.",
        "rationale": "site A is the correct gold copy (its obligation verifies) but "
                     "site B returns a wrong present setting, so "
                     "`problem_spec_stepB` rejects the variant. Confirms "
                     "the two sites are independently pinned (not one shared "
                     "obligation a correct A could discharge). Witness on site B at "
                     "`source = none`: the rival returns `some 0` where the source "
                     "is absent, so identity fails (`some 0 ≠ none`) — and the "
                     "presence reading fails with it, since presence is IMPLIED by "
                     "identity on this carrier rather than separately breakable "
                     "(checked: `(h : r = s) → isPresent r = isPresent s` is `subst "
                     "h; rfl`). The point of this witness is the SITE, not a second "
                     "clause: it pins B at the absent class of its binder.",
        "witness": _witness("stepB", "none"),
    },
    {
        "id": "half-fix-B-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _half2,
        "refinement": "the same half-fix shape as above but with site B left at "
                      "the pre-existing absent default: the setting is carried "
                      "over at one construction site and omitted at the other. The "
                      "F2P exercises each site independently, so the omitted site's "
                      "presence-and-identity assertions still fail. Does NOT "
                      "resolve.",
        "rationale": "site A is the correct gold copy but site B returns `none`, so "
                     "`problem_spec_stepB` rejects the variant. Witness on "
                     "site B at `source = some 5` — a present source distinct from "
                     "the other site-B witness's `none`, so stepB's "
                     "obligation is probed at two different values of its binder "
                     "rather than a single point. At `some 5` the rival's `none` "
                     "breaks both the presence conjunct (false ≠ true) and "
                     "identity.",
        "witness": _witness("stepB", "(some 5)"),
    },
]


# No consumed callee axioms (meta.axioms == []; the axioms region is empty). The
# carry-over is deep plain-data equality validated out-of-band by G-CONF; there
# is no consumed-axiom obligation for the PBT axiom lane to probe.
AXIOM_TESTS = []
