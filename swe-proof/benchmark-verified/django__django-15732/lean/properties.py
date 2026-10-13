"""properties.py — G-PBT falsification battery for django__django-15732 (lean).

NOT a Lean file; a record of the adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for a soundness/admissibility positive that legitimately
re-proves the obligation, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` HOLDS of the
rival while FAILING on the frozen solution).

This is a PORT of the nagini falsification battery to the Lean carrier. The
nagini sibling contracts one selection procedure with a fractional-permission
read-only precondition and both a normal-return domain and an exceptional
branch; the Lean bundle models exactly the purely functional selection decision
(``List String → Bool → Bool → String → Except Unit String``), so every nagini
argument that survives referential transparency is carried over and re-expressed
here, and the two frame/permission-mutation classes that do not are declared
vacuous rather than fabricated.

DEFENDED SURFACE (one total function; carrier fully transparent — plain
``List String`` / ``Bool`` / ``String``, no ``opaque`` callee, no consumed
axiom):

  selectUniqueToDrop
      (candidates : List String) (isUnique allowsMultiple : Bool)
      (defaultName : String) : Except Unit String
    let names := narrowedNames candidates isUnique allowsMultiple defaultName
    (names.length = 1 → result = Except.ok names.headI)   -- SELECT clause
    ∧ (names.length ≠ 1 → result = Except.error ())        -- REFUSE clause

  narrowedNames narrows the candidate set to the single canonical identifier
  exactly when isUnique ∧ candidates ≠ [] ∧ allowsMultiple ∧ defaultName ∈
  candidates; otherwise it leaves the set untouched. The decision is FULLY
  GROUNDED in the four inputs (no opaque answer-key): the result is a branch over
  the (possibly narrowed) candidate set, not a value handed to the function, so
  there is no *wrong echo* to build — the uniqueness lane attacks partial-domain
  rivals that are correct on a resolvable sub-domain and diverge on a
  discriminating one.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION, as a PERMISSION probe — VACUOUS. The nagini
    sibling makes an
    input-write attack MANDATORY: ``candidates`` is held at half (read-only)
    permission, and a rival that stores into it is rejected for insufficient
    permission. Lean is referentially transparent — ``candidates`` is a plain
    immutable ``List String``, there is no fractional permission to violate and
    no aliasing to exploit — so this class has NO expressible instance here. No
    substitute is fabricated for it. (nagini ``frame-mutate-candidates`` omitted.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is grounded in the
    inputs' own carrier (length / membership / the narrowed set's head), with no
    axiomatized answer-key; the bundle declares no ``opaque``/``axiom``. There is
    nothing an implementation could echo without doing the work; the honest
    analogue is the cheapest-correct POSITIVE CONTROL below.

  * PARTIAL-DOMAIN — APPLIES, load-bearing. SEVEN rivals, each correct on a
    resolvable sub-domain and refuted on a distinct discriminating one.
    Four corrupt what happens AFTER the narrowing guard: dropping the count check
    (silent arbitrary selection), taking the first raw candidate on the narrowed
    path, returning the canonical identifier on the sole-candidate path even when
    it was never discovered, and weakening the count check so an EMPTY candidate
    set is treated as resolvable (a removal fires when nothing was discovered at
    all). Three more corrupt the narrowing GUARD itself, one conjunct each
    (capability, uniqueness, membership) — see the R-E/R-F/R-G block. Those three
    were added by audit: without them every conjunct of the guard was unattacked,
    although the guard is the entire content of the change being modeled, and no
    witness reached a MIXED-FLAG input (the original four sit only at
    false/false and true/true, so an impl that read either flag for the other, or
    ORed them, was invisible to the battery).

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not vacuous, and not shippable
    here. This bundle sets no `loom.semantics.termination`, and the carrier is
    plain Lean: a diverging rival must be spelled `partial def`, which makes the
    definition OPAQUE to reduction. Measured: a `partial def` self-recursive
    implementation is REJECTED (exit 1 — `unfold` cannot unfold it), so the
    obligation does catch it; but no admissible witness can attest to that
    rejection. A witness over a rival-only helper (`partial def spinForever`) is
    out of scope by `witness_scope_problems` (a name the frozen solution does not
    declare), and the in-scope shape — a concrete claim over
    `implementation_selectUniqueToDrop` — leaves `unsolved goals` on the RIVAL
    side (exit 1), because the opaque `partial def` reduces for neither side. So
    the rejection would attribute nothing to the spec, and the case is recorded as
    a hole rather than fabricated or called vacuous.

  * FRAME / PERMISSION MUTATION, value-level analogue — COLLAPSES onto an
    existing rival. An impl that "self-normalizes" its input (`candidates.set 0
    defaultName` before the gold logic) is rejected here, but on this carrier the
    rejection is an ordinary VALUE mismatch, not the permission violation the
    nagini case tests: at `["a"] true true "z"` it produces `Except.ok "z"`,
    exactly the observable weak-narrow-ignores-membership already refutes. It is
    therefore not added — a second spelling of a point the battery already holds.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate at one CONCRETE
input; each was built against the rival (must succeed) and against the frozen
solution (must fail), so it is a real discriminator rather than a tautology. The
carrier is fully concrete, so each witness reasons at literal inputs — no
conditioning on an opaque term is needed, and the witnesses carry no hypotheses.

BINDER COVERAGE. The four spec binders are varied across the reject witnesses so
the battery exercises the spec's dependence on each rather than probing one
point:
  * ``candidates`` — ``["a", "b"]`` (arbitrary-on-multi, wrong-first-pick, and
    both mixed-flag guard rivals), ``["a"]`` (invented-name,
    narrow-ignores-membership) and ``[]`` (undercount-empty), i.e. all three
    length regimes the count check distinguishes: above one, exactly one, and
    below one.
  * ``isUnique`` / ``allowsMultiple`` — all FOUR combinations, which is what makes
    the two flags separately constrained: ``false``/``false``
    (arbitrary-on-multi, invented-name, undercount-empty — the narrowing branch
    does NOT fire), ``true``/``true`` (wrong-first-pick,
    narrow-ignores-membership — it DOES fire, or is forbidden only by
    membership), ``true``/``false`` (narrow-ignores-capability) and
    ``false``/``true`` (narrow-ignores-uniqueness). The two mixed points are the
    ones that distinguish the flags from each other; with only the agreeing pair,
    an impl reading one flag for the other passes.
  * ``defaultName`` — ``"z"`` (NOT among the candidates: invented-name,
    narrow-ignores-membership) and ``"b"`` (IS among them, and is the narrowing
    target), so membership is exercised both ways, and with both flags on as well
    as off.
``pts`` = 7 distinct input points.

CLAUSE COVERAGE. Both top-level conjuncts are attacked, the REFUSE clause from
BOTH sides of the count, and the narrowing guard conjunct-by-conjunct:
  * REFUSE (``names.length ≠ 1 → error``) — arbitrary-on-multi (length 2, too
    many), undercount-empty (length 0, too few), and both mixed-flag guard rivals
    (length 2 because the spec forbids the narrowing they perform).
  * SELECT (``names.length = 1 → ok names.headI``) — wrong-first-pick (wrong
    element of the narrowed set), invented-name (an identifier from outside the
    set, narrowing off) and narrow-ignores-membership (an identifier from outside
    the set, narrowing forbidden by membership alone).
  * ``narrowedNames``' guard — each of its three load-bearing conjuncts is the
    SOLE difference in one rival, so none may be dropped. (The emptiness conjunct
    is genuinely redundant, which pos-respelled-guard proves by verifying without
    it, so there is no rival for it.)
Both clauses are defended by the positive controls and the admissibility ground
instance.

SPEC-TOO-STRONG COVERAGE. The three positives sit at increasing distance from the
frozen form: same skeleton with the branch polarity flipped (pos-branch-polarity),
a functional term over the spec's own ``narrowedNames`` (pos-functional-reshape),
and a term that calls ``narrowedNames`` NOT AT ALL and respells the narrowing
guard with the redundant emptiness conjunct dropped (pos-respelled-guard), whose
proof has to earn the guard equivalence as a lemma before case-splitting. So the
spec is shown not to be over-fit to the frozen impl's skeleton, its branch
polarity, or the spelling of its guard.

AXIOM lane: EMPTY. The modeled behavior is a total selection over the inputs'
own carrier; there is no consumed axiom or deep-model reference for a PBT axiom
lane to re-discharge (and that lane is G-AX's job regardless). AXIOM_TESTS = [].
"""
from pathlib import Path

INSTANCE = "django__django-15732"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL gold impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_selectUniqueToDrop (candidates : List String)\n"
    "    (isUnique allowsMultiple : Bool) (defaultName : String) :\n"
    "    Except Unit String := Id.run do\n"
    "  let mut names := candidates\n"
    "  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then\n"
    "    names := [defaultName]\n"
    "  if names.length != 1 then\n"
    "    return Except.error ()\n"
    "  return Except.ok names.headI\n"
)

_PROOF_BODY = (
    "  intro candidates isUnique allowsMultiple defaultName\n"
    "  have hcond : (isUnique && !candidates.isEmpty && allowsMultiple && candidates.contains defaultName) = true ↔\n"
    "      (isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates) := by\n"
    "    simp only [Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_eq_false_iff,\n"
    "      List.contains_eq_mem, ne_eq, and_assoc, decide_eq_true_eq]\n"
    "  unfold problem_spec_selectUniqueToDrop implementation_selectUniqueToDrop narrowedNames\n"
    "  simp only [Id.run]\n"
    "  by_cases h : isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates\n"
    "  · rw [if_pos h, if_pos (hcond.mpr h)]\n"
    "    refine ⟨fun _ => rfl, fun hlen => ?_⟩\n"
    "    simp at hlen\n"
    "  · rw [if_neg h, if_neg (fun hh => h (hcond.mp hh))]\n"
    "    by_cases hlen : candidates.length = 1\n"
    "    · rw [if_neg (by simp [hlen])]\n"
    "      exact ⟨fun _ => rfl, fun hne => absurd hlen hne⟩\n"
    "    · rw [if_pos (by simp [hlen])]\n"
    "      exact ⟨fun he => absurd he hlen, fun _ => rfl⟩\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (POS-1) functional reshape — drop the mutable-accumulator `Id.run do` and
# express the selection as one functional term over `narrowedNames`. Same value
# on every input; the frozen tactic script (tuned to the `Id.run do` form) no
# longer applies, so the obligation is re-proved for the new shape with the
# STATEMENT byte-identical and no new lemma/axiom.
_POS_FUNC_IMPL = (
    "def implementation_selectUniqueToDrop (candidates : List String)\n"
    "    (isUnique allowsMultiple : Bool) (defaultName : String) :\n"
    "    Except Unit String :=\n"
    "  let names := narrowedNames candidates isUnique allowsMultiple defaultName\n"
    "  if names.length = 1 then Except.ok names.headI else Except.error ()\n"
)
_POS_FUNC_PROOF = (
    "  intro candidates isUnique allowsMultiple defaultName\n"
    "  unfold problem_spec_selectUniqueToDrop implementation_selectUniqueToDrop\n"
    "  by_cases h : (narrowedNames candidates isUnique allowsMultiple defaultName).length = 1\n"
    "  · simp [h]\n"
    "  · simp [h]\n"
)

# (POS-2) branch-polarity reshape — keep the imperative `Id.run do` skeleton but
# test `names.length == 1` (the positive polarity) and return the OK branch
# first, error last, instead of the frozen `!= 1`-then-error shape. Same value on
# every input; the two `by_cases hlen` arms swap which `if_pos`/`if_neg` fires, so
# the obligation is re-proved with the STATEMENT byte-identical and no new
# lemma/axiom.
_POS_POLARITY_IMPL = (
    "def implementation_selectUniqueToDrop (candidates : List String)\n"
    "    (isUnique allowsMultiple : Bool) (defaultName : String) :\n"
    "    Except Unit String := Id.run do\n"
    "  let mut names := candidates\n"
    "  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then\n"
    "    names := [defaultName]\n"
    "  if names.length == 1 then\n"
    "    return Except.ok names.headI\n"
    "  return Except.error ()\n"
)
_POS_POLARITY_PROOF = (
    "  intro candidates isUnique allowsMultiple defaultName\n"
    "  have hcond : (isUnique && !candidates.isEmpty && allowsMultiple && candidates.contains defaultName) = true ↔\n"
    "      (isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates) := by\n"
    "    simp only [Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_eq_false_iff,\n"
    "      List.contains_eq_mem, ne_eq, and_assoc, decide_eq_true_eq]\n"
    "  unfold problem_spec_selectUniqueToDrop implementation_selectUniqueToDrop narrowedNames\n"
    "  simp only [Id.run]\n"
    "  by_cases h : isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates\n"
    "  · rw [if_pos h, if_pos (hcond.mpr h)]\n"
    "    refine ⟨fun _ => rfl, fun hlen => ?_⟩\n"
    "    simp at hlen\n"
    "  · rw [if_neg h, if_neg (fun hh => h (hcond.mp hh))]\n"
    "    by_cases hlen : candidates.length = 1\n"
    "    · rw [if_pos (by simp [hlen])]\n"
    "      exact ⟨fun _ => rfl, fun hne => absurd hlen hne⟩\n"
    "    · rw [if_neg (by simp [hlen])]\n"
    "      exact ⟨fun he => absurd he hlen, fun _ => rfl⟩\n"
)

# (POS-3) respelled-guard reshape — the strongest positive here, because it does
# not reuse the spec's own `narrowedNames` and does not spell the narrowing guard
# the way the spec does. The emptiness conjunct is DROPPED (it is redundant:
# `candidates.contains defaultName` already forces a nonempty list) and the guard
# is computed as a single `Bool`, so the impl's branch condition is no longer
# syntactically or definitionally the spec's. The proof must therefore first
# EARN the guard equivalence as a lemma (`hnarrow`) before the case split — which
# is exactly the obligation a reshape is supposed to re-discharge. Same value on
# every input; STATEMENT byte-identical, no new declaration/axiom.
_POS_RESPELL_IMPL = (
    "def implementation_selectUniqueToDrop (candidates : List String)\n"
    "    (isUnique allowsMultiple : Bool) (defaultName : String) :\n"
    "    Except Unit String :=\n"
    "  let fires : Bool := isUnique && allowsMultiple && candidates.contains defaultName\n"
    "  let names : List String := if fires then [defaultName] else candidates\n"
    "  if names.length = 1 then Except.ok names.headI else Except.error ()\n"
)
_POS_RESPELL_PROOF = (
    "  intro candidates isUnique allowsMultiple defaultName\n"
    "  have hnarrow : (if (isUnique && allowsMultiple && candidates.contains defaultName) = true then [defaultName] else candidates)\n"
    "      = narrowedNames candidates isUnique allowsMultiple defaultName := by\n"
    "    unfold narrowedNames\n"
    "    by_cases hc : defaultName ∈ candidates\n"
    "    · by_cases hu : isUnique = true\n"
    "      · by_cases ha : allowsMultiple = true\n"
    "        · have hne : candidates ≠ [] := by\n"
    "            intro he; rw [he] at hc; simp at hc\n"
    "          simp [hu, ha, hc, hne]\n"
    "        · simp_all\n"
    "      · simp_all\n"
    "    · have : ¬ (isUnique = true ∧ candidates ≠ [] ∧ allowsMultiple = true ∧ defaultName ∈ candidates) := by\n"
    "        rintro ⟨-, -, -, h⟩; exact hc h\n"
    "      simp_all\n"
    "  unfold problem_spec_selectUniqueToDrop implementation_selectUniqueToDrop\n"
    "  simp only [hnarrow]\n"
    "  by_cases h : (narrowedNames candidates isUnique allowsMultiple defaultName).length = 1\n"
    "  · simp [h]\n"
    "  · simp [h]\n"
)

# (ADMISS) ground instance at an F2P-shaped input: a two-element candidate set
# with the narrowing flags on and the canonical identifier present, where the
# spec requires the narrowed sole identifier be selected. Discharged as a `have`
# INSIDE the frozen tactic body (statement byte-identical), then the frozen
# obligation is closed verbatim — so the modeled behavior is shown satisfiable at
# the normal input, not merely provable in the abstract.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_selectUniqueToDrop [\"a\", \"b\"] true true \"b\"\n"
    "      (implementation_selectUniqueToDrop [\"a\", \"b\"] true true \"b\") := by\n"
    "    refine ⟨fun _ => rfl, fun hlen => absurd rfl hlen⟩\n"
) + _PROOF_BODY


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (R-A) arbitrary-on-multi — drop the count check entirely and always return the
# first (possibly narrowed) candidate. On a non-resolvable multi-candidate set
# (not narrowed, length ≥ 2) this returns a candidate instead of refusing —
# exactly the silent-arbitrary-deletion behaviour the issue forbids.
_RIVAL_ARBITRARY_IMPL = (
    "def implementation_selectUniqueToDrop (candidates : List String)\n"
    "    (isUnique allowsMultiple : Bool) (defaultName : String) :\n"
    "    Except Unit String := Id.run do\n"
    "  let mut names := candidates\n"
    "  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then\n"
    "    names := [defaultName]\n"
    "  return Except.ok names.headI\n"
)

# (R-B) wrong-first-pick — on the SELECT path return the first RAW candidate
# (`candidates.headI`) rather than the narrowed set's head. When narrowing fired,
# the narrowed head is the canonical identifier but `candidates.headI` need not
# be, so it selects the wrong identifier.
_RIVAL_WRONGPICK_IMPL = (
    "def implementation_selectUniqueToDrop (candidates : List String)\n"
    "    (isUnique allowsMultiple : Bool) (defaultName : String) :\n"
    "    Except Unit String := Id.run do\n"
    "  let mut names := candidates\n"
    "  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then\n"
    "    names := [defaultName]\n"
    "  if names.length != 1 then\n"
    "    return Except.error ()\n"
    "  return Except.ok candidates.headI\n"
)

# (R-C) invented-name — on the SELECT path return `defaultName` rather than the
# selected candidate. When the sole candidate is NOT the canonical identifier
# (narrowing did not fire), this returns an identifier that was never among the
# candidates.
_RIVAL_INVENTED_IMPL = (
    "def implementation_selectUniqueToDrop (candidates : List String)\n"
    "    (isUnique allowsMultiple : Bool) (defaultName : String) :\n"
    "    Except Unit String := Id.run do\n"
    "  let mut names := candidates\n"
    "  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then\n"
    "    names := [defaultName]\n"
    "  if names.length != 1 then\n"
    "    return Except.error ()\n"
    "  return Except.ok defaultName\n"
)


# (R-D) undercount — weaken the count check from `!= 1` to `> 1`, so only an
# OVER-full candidate set is refused and an EMPTY one is treated as resolvable.
# On an empty candidate set (nothing discovered for these columns) the spec
# demands refusal, but this selects `headI`, i.e. the empty identifier: a name
# that was never discovered and denotes no constraint at all. This is the only
# rival that exercises the length-0 boundary; the other three all sit at length
# 1 or 2, so without it the REFUSE clause is probed only from ABOVE.
_RIVAL_UNDERCOUNT_IMPL = (
    "def implementation_selectUniqueToDrop (candidates : List String)\n"
    "    (isUnique allowsMultiple : Bool) (defaultName : String) :\n"
    "    Except Unit String := Id.run do\n"
    "  let mut names := candidates\n"
    "  if isUnique && !names.isEmpty && allowsMultiple && names.contains defaultName then\n"
    "    names := [defaultName]\n"
    "  if names.length > 1 then\n"
    "    return Except.error ()\n"
    "  return Except.ok names.headI\n"
)


# ---------------------------------------------------------------------------
# (R-E/R-F/R-G) NARROWING-GUARD rivals — added by audit.
#
# The four rivals above all keep the narrowing guard VERBATIM and corrupt only
# what happens after it (the count check, or which element is handed back). So
# every conjunct of the guard itself was unattacked, and the guard is exactly
# what distinguishes the resolved behavior from the pre-patch one: the narrowing
# step is the whole content of the change. A spec that constrained only the
# post-narrowing arithmetic would admit an impl that narrows on the WRONG
# occasions and still pass this battery.
#
# These three drop one conjunct each. Two of them are refuted at MIXED-FLAG
# points (isUnique ≠ allowsMultiple) that no previous witness reached — the
# earlier four sit only at false/false and true/true, so the battery could not
# tell the two flags apart at all: an impl reading either flag for the other, or
# ORing them, was invisible to it.
# ---------------------------------------------------------------------------

def _guard_rival(guard):
    return (
        "def implementation_selectUniqueToDrop (candidates : List String)\n"
        "    (isUnique allowsMultiple : Bool) (defaultName : String) :\n"
        "    Except Unit String := Id.run do\n"
        "  let mut names := candidates\n"
        f"  if {guard} then\n"
        "    names := [defaultName]\n"
        "  if names.length != 1 then\n"
        "    return Except.error ()\n"
        "  return Except.ok names.headI\n"
    )


# (R-E) the backend-capability conjunct is dropped: the candidate set is narrowed
# even on a backend that does NOT permit several uniqueness constraints to
# coexist over the same columns.
_RIVAL_NO_ALLOWSMULTIPLE_IMPL = _guard_rival(
    "isUnique && !names.isEmpty && names.contains defaultName")

# (R-F) the uniqueness conjunct is dropped: the candidate set is narrowed on a
# removal that is not a uniqueness removal at all.
_RIVAL_NO_ISUNIQUE_IMPL = _guard_rival(
    "!names.isEmpty && allowsMultiple && names.contains defaultName")

# (R-G) the membership conjunct is dropped: the set is narrowed to the canonical
# identifier even when that identifier is not among the discovered ones.
_RIVAL_NO_MEMBERSHIP_IMPL = _guard_rival(
    "isUnique && !names.isEmpty && allowsMultiple")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-functional-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_GOLD, _POS_FUNC_IMPL),
                        _PROOF_BODY, _POS_FUNC_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl: the mutable-accumulator "
            "`Id.run do` is dropped and the selection is spelled as one functional "
            "term over the narrowed set — `if names.length = 1 then ok names.headI "
            "else error`, mirroring the spec's own case split. Same value on every "
            "input, so both the SELECT clause (names.length = 1 → ok names.headI) "
            "and the REFUSE clause (names.length ≠ 1 → error) stay provable. Must "
            "verify; else the postcondition is over-fit to the imperative "
            "two-branch SHAPE => SPEC-TOO-STRONG. Proof: after `unfold`, a "
            "`by_cases` on the narrowed length closes each arm by `simp` — no new "
            "declaration, axiom, or assumption token; the theorem STATEMENT is "
            "byte-identical."
        ),
    },
    {
        "id": "pos-branch-polarity",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_GOLD, _POS_POLARITY_IMPL),
                        _PROOF_BODY, _POS_POLARITY_PROOF),
        "rationale": (
            "reshape that keeps the imperative skeleton but flips the count test to "
            "the positive polarity (`names.length == 1`) and returns the OK branch "
            "first, error last, rather than `!= 1`-then-error. Semantically "
            "identical to gold. Must verify; else the postcondition is over-fit to "
            "the branch POLARITY/ORDER => SPEC-TOO-STRONG. Proof: the frozen script "
            "with the two length arms' `if_pos`/`if_neg` swapped to match the new "
            "polarity; STATEMENT byte-identical, no new declaration/axiom."
        ),
    },
    {
        "id": "pos-respelled-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_GOLD, _POS_RESPELL_IMPL),
                        _PROOF_BODY, _POS_RESPELL_PROOF),
        "rationale": (
            "the reshape furthest from the frozen form: the impl neither calls the "
            "spec's own `narrowedNames` nor spells the narrowing guard the way the "
            "spec spells it. The emptiness conjunct is DROPPED as redundant "
            "(`candidates.contains defaultName` already entails a nonempty list) and "
            "the guard is computed as one `Bool`, so the branch condition is neither "
            "syntactically nor definitionally the spec's — the proof must EARN the "
            "guard equivalence (`hnarrow`, including the nonemptiness side "
            "condition) before it can case-split. Same value on every input, so both "
            "the SELECT and REFUSE clauses stay provable. Must verify; else the "
            "postcondition is over-fit to the exact SPELLING of the narrowing guard "
            "(a spec that only accepts impls whose guard is a syntactic copy of its "
            "own) => SPEC-TOO-STRONG. STATEMENT byte-identical, no new "
            "declaration/axiom."
        ),
    },
    {
        "id": "admiss-narrowed-sole-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at an F2P-shaped ground input — a "
            "two-element candidate set `[\"a\", \"b\"]` with both flags on and the "
            "canonical identifier `\"b\"` present, so narrowing reduces it to the "
            "single canonical identifier and the spec requires `Except.ok \"b\"` — "
            "by a `have` inside the existing tactic body, then the frozen "
            "obligation is closed verbatim. Verifies; else the modeled behavior is "
            "unsatisfiable at exactly the input the F2P exercises (the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: STATEMENT byte-identical, the "
            "ground instance is a `have`, no new declaration/axiom/`sorry`."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-arbitrary-on-multi",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _RIVAL_ARBITRARY_IMPL),
        "refinement": (
            "dropping the count check makes the operation select the first "
            "candidate on a non-resolvable set (several discovered identifiers, "
            "none of them the canonical one) instead of refusing — it drops an "
            "arbitrary/independent constraint rather than signalling the "
            "wrong-number-of-constraints condition. A faithful patch doing this "
            "removes a wrong constraint and FAILS the migration test (the resolved "
            "behavior REFUSES here), so a verifying rival would be "
            "verify-does-not-resolve, not a real fix."
        ),
        "rationale": (
            "REJECT from the REFUSE clause (names.length ≠ 1 → result = "
            "Except.error ()). On the witness input the narrowing branch does not "
            "fire (isUnique = false, allowsMultiple = false) so `names = candidates` "
            "has length 2 ≠ 1, and the spec demands `Except.error ()`, but the rival "
            "returns `Except.ok` of the first candidate. Correct on the resolvable "
            "sub-domain (length exactly 1); wrong on the multi-candidate sub-domain. "
            "If it verified => SPEC-TOO-WEAK (silent-arbitrary-selection hole "
            "re-opened)."
        ),
        "witness": (
            "-- Refuted on a non-resolvable multi-candidate set (length 2, narrowing\n"
            "-- off): the spec requires refusal, but dropping the count check yields\n"
            "-- an OK selection of the first candidate.\n"
            "example : ¬ problem_spec_selectUniqueToDrop [\"a\", \"b\"] false false \"z\"\n"
            "    (implementation_selectUniqueToDrop [\"a\", \"b\"] false false \"z\") := by\n"
            "  unfold problem_spec_selectUniqueToDrop\n"
            "  intro h\n"
            "  have hlen : (narrowedNames [\"a\", \"b\"] false false \"z\").length ≠ 1 := by decide\n"
            "  have hres := h.2 hlen\n"
            "  rw [show implementation_selectUniqueToDrop [\"a\", \"b\"] false false \"z\" = Except.ok \"a\" from rfl] at hres\n"
            "  simp at hres\n"
        ),
    },
    {
        "id": "weak-wrong-first-pick",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _RIVAL_WRONGPICK_IMPL),
        "refinement": (
            "returning the first RAW candidate on the SELECT path means that when "
            "the candidate set was narrowed to the canonical identifier, the "
            "operation still drops the first discovered identifier — i.e. an "
            "independent single-column constraint rather than the composed-rule "
            "one. A faithful patch doing this drops the wrong constraint and FAILS "
            "the F2P (it removes the user's standalone unique constraint, not the "
            "composed one), so a verifying rival would be verify-does-not-resolve."
        ),
        "rationale": (
            "REJECT from the SELECT clause (names.length = 1 → result = Except.ok "
            "names.headI). On the witness input the narrowing branch fires "
            "(isUnique = true, allowsMultiple = true, defaultName = \"b\" ∈ "
            "[\"a\", \"b\"]) so `names = [\"b\"]` and the spec demands `Except.ok "
            "\"b\"`, but the rival returns `Except.ok candidates.headI = "
            "Except.ok \"a\"`. Correct only when the first raw candidate already "
            "equals the narrowed head. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted where narrowing fires (canonical identifier \"b\" present in\n"
            "-- [\"a\", \"b\"]): the spec requires the narrowed identifier \"b\", but\n"
            "-- taking the first raw candidate yields \"a\".\n"
            "example : ¬ problem_spec_selectUniqueToDrop [\"a\", \"b\"] true true \"b\"\n"
            "    (implementation_selectUniqueToDrop [\"a\", \"b\"] true true \"b\") := by\n"
            "  unfold problem_spec_selectUniqueToDrop\n"
            "  intro h\n"
            "  have hlen : (narrowedNames [\"a\", \"b\"] true true \"b\").length = 1 := by decide\n"
            "  have hres := h.1 hlen\n"
            "  rw [show implementation_selectUniqueToDrop [\"a\", \"b\"] true true \"b\" = Except.ok \"a\" from rfl,\n"
            "      show narrowedNames [\"a\", \"b\"] true true \"b\" = [\"b\"] from rfl] at hres\n"
            "  simp at hres\n"
        ),
    },
    {
        "id": "weak-invented-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _RIVAL_INVENTED_IMPL),
        "refinement": (
            "returning the canonical identifier on the SELECT path, regardless of "
            "the candidate actually discovered, means that when the sole candidate "
            "is an INDEPENDENT constraint whose identifier is not the canonical one "
            "(narrowing did not fire), the operation targets an identifier that was "
            "never discovered — a constraint that does not exist on those columns. "
            "A faithful patch doing this emits a DROP for a non-existent / wrong "
            "identifier and FAILS the migration tests, so a verifying rival would "
            "be verify-does-not-resolve."
        ),
        "rationale": (
            "REJECT from the SELECT clause (names.length = 1 → result = Except.ok "
            "names.headI). On the witness input the narrowing branch does not fire "
            "(isUnique = false, allowsMultiple = false), the sole candidate is "
            "\"a\", so `names = [\"a\"]` and the spec demands `Except.ok \"a\"`, but "
            "the rival returns `Except.ok defaultName = Except.ok \"z\"`, a name "
            "never among the candidates. Correct only when the sole candidate "
            "happens to equal the default. If it verified => SPEC-TOO-WEAK (a "
            "removal could target an undiscovered identifier)."
        ),
        "witness": (
            "-- Refuted on a sole candidate [\"a\"] whose identifier is NOT the\n"
            "-- default \"z\" (narrowing off): the spec requires the discovered\n"
            "-- identifier \"a\", but returning the default yields the undiscovered \"z\".\n"
            "example : ¬ problem_spec_selectUniqueToDrop [\"a\"] false false \"z\"\n"
            "    (implementation_selectUniqueToDrop [\"a\"] false false \"z\") := by\n"
            "  unfold problem_spec_selectUniqueToDrop\n"
            "  intro h\n"
            "  have hlen : (narrowedNames [\"a\"] false false \"z\").length = 1 := by decide\n"
            "  have hres := h.1 hlen\n"
            "  rw [show implementation_selectUniqueToDrop [\"a\"] false false \"z\" = Except.ok \"z\" from rfl,\n"
            "      show narrowedNames [\"a\"] false false \"z\" = [\"a\"] from rfl] at hres\n"
            "  simp at hres\n"
        ),
    },
    {
        "id": "weak-undercount-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _RIVAL_UNDERCOUNT_IMPL),
        "refinement": (
            "weakening the count guard to reject only an OVER-full candidate set "
            "means that when NOTHING was discovered for the target columns, the "
            "operation proceeds to remove `headI` — the empty identifier — instead "
            "of signalling the wrong-number-of-constraints condition. A faithful "
            "patch doing this emits a removal naming no existing constraint (or "
            "crashes on the empty selection) where the resolved behavior REFUSES, "
            "so it fails the migration tests: a verifying rival would be "
            "verify-does-not-resolve, not a real fix."
        ),
        "rationale": (
            "REJECT from the REFUSE clause (names.length ≠ 1 → result = "
            "Except.error ()), attacked from BELOW rather than above. On the witness "
            "input the candidate set is empty and the narrowing branch cannot fire, "
            "so `names = []` has length 0 ≠ 1 and the spec demands `Except.error ()`, "
            "but the rival's `> 1` guard is false and it returns `Except.ok "
            "[].headI`. Correct on every set of length ≥ 1; wrong exactly at the "
            "empty set — the length-0 boundary no other rival in this battery "
            "reaches. If it verified => SPEC-TOO-WEAK (the REFUSE clause would "
            "constrain only over-full sets, letting a removal fire when nothing was "
            "discovered at all)."
        ),
        "witness": (
            "-- Refuted on an EMPTY candidate set (nothing discovered for these\n"
            "-- columns): the spec requires refusal, but a `> 1` count guard treats\n"
            "-- the empty set as resolvable and selects the empty identifier.\n"
            "example : ¬ problem_spec_selectUniqueToDrop [] false false \"z\"\n"
            "    (implementation_selectUniqueToDrop [] false false \"z\") := by\n"
            "  unfold problem_spec_selectUniqueToDrop\n"
            "  intro h\n"
            "  have hlen : (narrowedNames ([] : List String) false false \"z\").length ≠ 1 := by decide\n"
            "  have hres := h.2 hlen\n"
            "  rw [show implementation_selectUniqueToDrop [] false false \"z\" = Except.ok \"\" from rfl] at hres\n"
            "  simp at hres\n"
        ),
    },

    # ---- narrowing-guard rivals (added by audit; must be REJECTED) ----
    {
        "id": "weak-narrow-ignores-capability",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _RIVAL_NO_ALLOWSMULTIPLE_IMPL),
        "refinement": (
            "narrowing without consulting the backend-capability flag means the "
            "operation singles out the canonical identifier on a backend where "
            "several uniqueness constraints CANNOT coexist over the same columns. "
            "There the multi-candidate set reflects genuinely distinct constraints, "
            "so collapsing it to one silently drops a constraint the operation was "
            "never asked to touch instead of reporting that it cannot decide. A "
            "faithful patch doing this removes a constraint the resolved behavior "
            "refuses to remove, so a verifying rival would be "
            "verify-does-not-resolve, not a real fix."
        ),
        "rationale": (
            "REJECT from the REFUSE clause (names.length ≠ 1 → result = "
            "Except.error ()), at a MIXED-FLAG point no other case in this battery "
            "reaches. On the witness input isUnique = true but allowsMultiple = "
            "false, so the spec's guard does NOT fire, `names = [\"a\", \"b\"]` has "
            "length 2 ≠ 1 and refusal is required; the rival's guard, missing the "
            "capability conjunct, fires and yields `Except.ok \"b\"`. Correct "
            "whenever the two flags agree — which is why the other four rivals "
            "leave this undetected. If it verified => SPEC-TOO-WEAK (the "
            "capability flag would be unconstrained by the spec)."
        ),
        "witness": (
            "-- Refuted at a MIXED-FLAG point: the backend does NOT permit coexisting\n"
            "-- uniqueness constraints (allowsMultiple = false), so the spec forbids\n"
            "-- narrowing and demands refusal on the two-candidate set; dropping the\n"
            "-- capability conjunct narrows anyway and selects an identifier.\n"
            "example : ¬ problem_spec_selectUniqueToDrop [\"a\", \"b\"] true false \"b\"\n"
            "    (implementation_selectUniqueToDrop [\"a\", \"b\"] true false \"b\") := by\n"
            "  unfold problem_spec_selectUniqueToDrop\n"
            "  intro h\n"
            "  have hlen : (narrowedNames [\"a\", \"b\"] true false \"b\").length ≠ 1 := by decide\n"
            "  have hres := h.2 hlen\n"
            "  rw [show implementation_selectUniqueToDrop [\"a\", \"b\"] true false \"b\" = Except.ok \"b\" from rfl] at hres\n"
            "  simp at hres\n"
        ),
    },
    {
        "id": "weak-narrow-ignores-uniqueness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _RIVAL_NO_ISUNIQUE_IMPL),
        "refinement": (
            "narrowing without checking that the removal targets a uniqueness "
            "constraint applies the uniqueness-specific disambiguation to a removal "
            "of a different kind, where the canonical uniqueness identifier has no "
            "standing. The operation then collapses a multi-candidate set on a path "
            "the resolved behavior refuses, dropping a constraint chosen by a rule "
            "that does not apply. A faithful patch doing this changes behavior on "
            "non-uniqueness removals and fails the migration tests, so a verifying "
            "rival would be verify-does-not-resolve."
        ),
        "rationale": (
            "REJECT from the REFUSE clause (names.length ≠ 1 → result = "
            "Except.error ()), at the complementary MIXED-FLAG point. On the witness "
            "input isUnique = false and allowsMultiple = true, so the spec's guard "
            "does NOT fire and refusal is required on the length-2 set; the rival's "
            "guard, missing the uniqueness conjunct, fires and yields `Except.ok "
            "\"b\"`. Together with weak-narrow-ignores-capability this pins the two "
            "flags SEPARATELY: neither may be read for the other, and the guard may "
            "not be an OR of them. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted at the other MIXED-FLAG point: the removal is not a uniqueness\n"
            "-- removal (isUnique = false), so the spec forbids narrowing and demands\n"
            "-- refusal; dropping that conjunct narrows anyway.\n"
            "example : ¬ problem_spec_selectUniqueToDrop [\"a\", \"b\"] false true \"b\"\n"
            "    (implementation_selectUniqueToDrop [\"a\", \"b\"] false true \"b\") := by\n"
            "  unfold problem_spec_selectUniqueToDrop\n"
            "  intro h\n"
            "  have hlen : (narrowedNames [\"a\", \"b\"] false true \"b\").length ≠ 1 := by decide\n"
            "  have hres := h.2 hlen\n"
            "  rw [show implementation_selectUniqueToDrop [\"a\", \"b\"] false true \"b\" = Except.ok \"b\" from rfl] at hres\n"
            "  simp at hres\n"
        ),
    },
    {
        "id": "weak-narrow-ignores-membership",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _RIVAL_NO_MEMBERSHIP_IMPL),
        "refinement": (
            "narrowing to the canonical identifier without checking that it is "
            "actually among the discovered ones targets an identifier that was never "
            "found on those columns — a constraint that need not exist. The "
            "sole-candidate case makes this concrete: one constraint WAS discovered, "
            "and the operation replaces it with a different, undiscovered identifier. "
            "A faithful patch doing this emits a removal naming a non-existent "
            "constraint and fails the migration tests, so a verifying rival would be "
            "verify-does-not-resolve."
        ),
        "rationale": (
            "REJECT from the SELECT clause (names.length = 1 → result = Except.ok "
            "names.headI). On the witness input both flags are on but the canonical "
            "identifier \"z\" is NOT among the candidates [\"a\"], so the spec's "
            "guard does not fire, `names = [\"a\"]` and the discovered identifier "
            "\"a\" is required; the rival narrows regardless and yields `Except.ok "
            "\"z\"`. This is the only case that exercises the membership conjunct "
            "with BOTH flags on — weak-invented-name reaches a similar output but "
            "with narrowing switched off by the flags, so it does not test the "
            "membership test itself. If it verified => SPEC-TOO-WEAK (the spec would "
            "not require the selected identifier to have been discovered)."
        ),
        "witness": (
            "-- Refuted where the canonical identifier is NOT among the discovered ones\n"
            "-- (both flags on, \"z\" ∉ [\"a\"]): the spec forbids narrowing here and\n"
            "-- demands the discovered identifier \"a\", but dropping the membership\n"
            "-- conjunct narrows to the undiscovered \"z\".\n"
            "example : ¬ problem_spec_selectUniqueToDrop [\"a\"] true true \"z\"\n"
            "    (implementation_selectUniqueToDrop [\"a\"] true true \"z\") := by\n"
            "  unfold problem_spec_selectUniqueToDrop\n"
            "  intro h\n"
            "  have hlen : (narrowedNames [\"a\"] true true \"z\").length = 1 := by decide\n"
            "  have hres := h.1 hlen\n"
            "  rw [show implementation_selectUniqueToDrop [\"a\"] true true \"z\" = Except.ok \"z\" from rfl,\n"
            "      show narrowedNames [\"a\"] true true \"z\" = [\"a\"] from rfl] at hres\n"
            "  simp at hres\n"
        ),
    },
]


# Axiom lane empty: no consumed axiom, no deep-model reference (the selection is
# modeled directly over the inputs' carrier). The nagini bundle's AXIOM_TESTS
# (an A-reference real-vs-model equivalence probe) belong to G-AX, not G-PBT.
AXIOM_TESTS = []
