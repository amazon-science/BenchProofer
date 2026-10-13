"""properties.py — G-PBT falsification battery for sympy__sympy-15599 (lean).

NOT a Lean module: a manifest the G-PBT gate parses. Each SPEC case is a full
``Solution.lean`` variant built by region surgery that edits ONLY the
``-- impl-start`` / ``-- impl-end`` region and/or the ``-- proof-start`` /
``-- proof-end`` tactic bodies. Both regions are elided from the consumer spec
view, so ``markers.same_spec`` holds by construction and the
``theorem correct_modFactors`` obligation survives with a byte-identical
STATEMENT (only tactic bodies differ). No case adds an ``axiom``, a helper
``theorem``/``lemma``, ``sorry``/``admit``, or ``native_decide``.

``expect="verify"`` passes iff (in scope AND the real verifier closes the
obligation); ``expect="reject"`` passes iff (in scope AND does NOT verify AND
its refutation ``witness`` discriminates — elaborates against the rival, fails
against the frozen solution).

===========================================================================
DEFENDED SURFACE (one obligation)
===========================================================================
  problem_spec_modFactors (q : Int) (factors result : List Factor) : Prop :=
    result = (if q = 1 then factors else reduceFactors q factors)

  theorem correct_modFactors : ∀ (q : Int) (factors : List Factor),
    problem_spec_modFactors q factors (implementation_modFactors q factors)

A product is a ``List Factor``; each factor is either a concrete integer
coefficient (``Factor.coeff n``) or a symbolic atom carrying an opaque tag
(``Factor.sym s``). The normalisation rewrites the factor list against an
integer divisor ``q``. The single top-level clause is a total equality with NO
precondition — the obligation is universally quantified over both binders, so
there is no precondition-shadowed sub-domain in which a rival is free.

The clause decomposes into TWO independent top-level arms plus, inside the
second arm, THREE independently-attackable per-factor outcomes:

  ARM 1 — UNIT DIVISOR (``q = 1``): the factor list is returned EXACTLY as it
    was. Reducing at a unit divisor would erase every coefficient (every
    integer is congruent to zero there), so identity is the pinned behaviour.
  ARM 2 — REDUCTION (``q ≠ 1``): ``reduceFactors q factors``, a
    front-recursive, ORDER- and LENGTH-preserving per-factor map whose kernel
    ``reduceFactor`` has three outcomes:
      * SHRINK — a concrete coefficient whose residue is NON-ZERO collapses to
        that residue. This is the discriminating content of the reported
        scenario: a coefficient with a non-zero residue must shrink.
      * KEEP-MULTIPLE — a concrete coefficient whose residue is ZERO is kept
        EXACTLY as it was, NOT collapsed to zero. Keeping it is what lets a
        later stage collapse the whole product.
      * KEEP-SYMBOLIC — a symbolic factor is preserved verbatim; the
        normalisation never inspects or rewrites a symbolic factor's tag.

The residue ``intMod a b := a - b * Int.fdiv a b`` is the FLOORED remainder
(sign of the divisor), matching the surrounding library's integer remainder
convention. It is modeled DEEPLY (exact integer arithmetic, no opaque callee),
so the carrier is fully computable and every witness below closes by ``decide``
at concrete literals — no conditioning on an opaque term is needed anywhere in
this battery.

TWO INPUT BINDERS, both load-bearing and both moved by the reject witnesses:
``q : Int`` (selects the arm, fixes the residue) and ``factors : List Factor``
(selects which per-factor outcome fires, at which position, in a list of which
length). The nine reject witnesses probe NINE DISTINCT input points, moving
``q`` across {1, 2, 3, 4, -2} — including the unit divisor that selects arm 1
and a NEGATIVE divisor, each a point no other rival reaches — and ``factors``
across both constructors, across lengths {1, 2}, and across the first and last
positions.

===========================================================================
CARRIER NOTE — the frozen carrier COMPUTES
===========================================================================
``problem_spec_modFactors`` is a bare ``Prop`` over a deeply-modeled arithmetic
carrier, so a witness states the refutation directly at a concrete input:

    example : ¬ problem_spec_modFactors (2 : Int) [Factor.coeff 3]
        (implementation_modFactors (2 : Int) [Factor.coeff 3]) := by
      unfold problem_spec_modFactors implementation_modFactors
      decide

Verified during authoring: bare ``decide`` FAILS to synthesize a ``Decidable``
instance for the un-unfolded ``problem_spec_modFactors`` application, and the
``unfold`` of BOTH the spec and the implementation is what makes the kernel
reduce the ``Id.run``/``forIn`` accumulator loop to a literal list. With that
unfold, ``decide`` computes the frozen loop at every witnessed input. Since
each witness binds NOTHING in its head (no hypotheses at all), the gate's
``witness-inconsistent`` consistency probe is vacuously satisfied — there are
no assumptions that could be jointly unsatisfiable.

Each of the nine witnesses was checked BY HAND with ``scripts/lean_verify.sh``
in the gate's own two-build shape (proof region stripped, witness appended):
every one elaborates green against its rival (exit 0) and FAILS against the
frozen solution (exit 1), the latter because ``decide`` proves the negated
proposition FALSE of gold — gold satisfies the spec at that input, which is
exactly the required discriminator half.

===========================================================================
REFINEMENT GROUNDING — measured, not argued
===========================================================================
Every ``refinement`` claim below was checked EMPIRICALLY rather than reasoned
about: for each rival, the corresponding faithful real patch was applied to the
repo at base_commit and the whole FAIL_TO_PASS + PASS_TO_PASS set (81 tests)
was run. The frozen behaviour passes all 81. Each rival shipped below was
observed to FAIL that set, so a verifying rival really would be a
verify-does-not-imply-resolve break, with the observed failing assertion
recorded in its ``refinement``.

That measurement also DISQUALIFIED four rivals whose real patches RESOLVE
(all 81 tests pass) — they are wrong against the frozen spec but not against
the repo, so shipping them would have asserted a refinement argument that is
factually false. They are named in the footer accounting. Three of the four
descend directly from nagini cases, which is precisely why the nagini prose was
re-derived here instead of translated.

===========================================================================
ADVERSARIAL READ of the sibling's classes on this carrier
===========================================================================
  * SOUNDNESS — APPLIES, and on this backend it is the real work: a correct
    reshape needs a proof that actually closes for the NEW impl shape. Two are
    shipped, each with a genuinely reproved obligation (no weakening, no helper
    lemma, no ``sorry``).
  * ADMISSIBILITY — RE-AIMED. The sibling asserts that an F2P-shaped input
    satisfies its fractional-permission precondition. This obligation has NO
    precondition at all (it is universally quantified over both binders), so
    "is the input admitted?" is degenerate here. The live residual risk is a
    DEGENERATE post-image, so the case discharges in-proof ``have``s pinning
    all three per-factor outcomes AND the unit-divisor arm AND order-sensitivity
    at concrete inputs, keeping the frozen impl and proof intact.
  * FRAME / PERMISSION MUTATION — VACUOUS. Both sibling frame rivals write into
    a read-only input held at a fractional heap permission. Lean is
    referentially transparent: ``factors`` is an immutable value, there is no
    heap, no aliasing, and no permission system, so there is no read-only input
    to overwrite and no frame clause to trip. NOT ported; fabricating a
    substitute would test nothing. (The directive it maps to — that no part of
    the output is left free — is discharged structurally: the clause is a total
    EQUALITY pinning the whole result list, so nothing is unconstrained.)
  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class. An
    earlier revision recorded this as "genuinely VACUOUS on lean" on the ground
    that ``implementation_modFactors`` is a total Lean ``def`` and "a diverging
    implementation cannot be written at all". MEASURED with real builds, that
    is FALSE: ``partial def spin q factors := spin q factors`` followed by
    ``def implementation_modFactors q factors := spin q factors`` clears the
    whole admissible variant scope (``variant_problems`` returns ``[]`` — it is
    not a new axiom, not a ``sorry``, not a new theorem, and the ``partial``
    keyword is not an assumption token), and the resulting variant is REJECTED
    (exit 1, ``simp made no progress``). So the class is EXPRESSIBLE here; what
    it is not is SHIPPABLE, and for a reason that has to be stated separately.
    A ``partial def`` is compiled through an opaque implementation, so its
    applications do not reduce in the kernel. Both builds measured:

      * the refutation witness at q=2, [coeff 3] against the diverging rival —
        exit 1, ``Tactic `decide` failed ... instDecidableNot did not reduce to
        `isTrue` or `isFalse` ... reduction got stuck``;
      * a FORGERY differing only in dropping the ``¬`` (i.e. asserting the
        rival is CORRECT there) — exit 1, the byte-identical stuck-reduction
        error on ``instDecidableEqList (spin 2 [Factor.coeff 3]) ...``.

    Identical errors for opposite claims: the exit code carries no information
    about the claim, so no ``decide``-shaped witness can discriminate a
    diverging rival, and the gate's own ``_STUCK_REDUCTION`` screen would
    correctly record such a case as ``witness-undecided`` — an INCONCLUSIVE
    outcome that forces MALFORMED-TESTS rather than a pass. A
    ``witness_reference`` does not rescue it either: the blocker is the RIVAL's
    own irreducibility, and the reference only replaces the gold-side subject.
    Nothing is shipped, therefore, but the disposition is that the spec does
    not pin termination on this carrier — NOT that the battery is complete.
    (The sibling carries no ``diverge-*``/``nonterm-*``/``weak-diverge`` case
    for this instance, so there was nothing to port; that is why the class was
    never re-derived until the audit measured it.)
  * UNGROUNDED-ORACLE ECHO — N/A, for the same reason the sibling records: the
    post-image is pinned to a fully-unfolded ``def`` over the obligation's own
    arguments, not to an opaque answer key. Reducing IS the work, so the
    cheapest correct impl computes it honestly (pos-direct-model).
  * PARTIAL-DOMAIN / VALUE — carries the whole reject lane.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15599"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Every one lies ENTIRELY inside the impl region or inside a proof
# tactic body, and every one is asserted unique in the frozen file at import
# time, so the manifest breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The whole executable head (impl region). Anchor for the reshapes that replace
# the accumulator loop outright.
_IMPL = """def implementation_modFactors (q : Int) (factors : List Factor) : List Factor := Id.run do
  if q = 1 then
    return factors
  let mut acc : List Factor := []
  for f in factors do
    match f with
    | Factor.coeff n =>
        if intMod n q ≠ 0 then
          acc := acc ++ [Factor.coeff (intMod n q)]
        else
          acc := acc ++ [Factor.coeff n]
    | Factor.sym s =>
        acc := acc ++ [Factor.sym s]
  return acc"""

# The per-coefficient decision inside the loop (impl region): the guard plus its
# two arms. The three per-factor rivals perturb exactly this and nothing else.
_COEFF = """        if intMod n q ≠ 0 then
          acc := acc ++ [Factor.coeff (intMod n q)]
        else
          acc := acc ++ [Factor.coeff n]"""

# The symbolic arm of the loop (impl region).
_SYM = """    | Factor.sym s =>
        acc := acc ++ [Factor.sym s]"""

# The unit-divisor early return (impl region).
_UNIT = """  if q = 1 then
    return factors"""

# The head of the obligation's tactic body: the statement is everything ABOVE
# the `:= by`, so anchoring here and appending leaves the STATEMENT
# byte-identical and touches only the tactic script.
_PROOF_HEAD = """      problem_spec_modFactors q factors (implementation_modFactors q factors) := by
  intro q factors"""

# The obligation's whole declaration through `:= by` — anchor for a case that
# needs a completely fresh tactic script for a reshaped impl. The STATEMENT
# text is reproduced verbatim in every replacement.
_CORRECT = """theorem correct_modFactors :
    ∀ (q : Int) (factors : List Factor),
      problem_spec_modFactors q factors (implementation_modFactors q factors) := by"""

# The frozen loop-vs-fold bridging lemma's own statement and proof both live
# inside the proof region, so the guard-inversion positive may retune them.
_LEMMA_BRANCH = """        if intMod n q ≠ 0 then
          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
        else
          pure (ForInStep.yield (r ++ [Factor.coeff n]))"""
_LEMMA_CASES = """      by_cases h : intMod n q ≠ 0
      · simp only [if_pos h, ih, reduceFactors, reduceFactor, List.append_assoc,
          List.cons_append, List.nil_append]
      · simp only [if_neg h, ih, reduceFactors, reduceFactor, List.append_assoc,
          List.cons_append, List.nil_append]"""
_H2_BRANCH = """              if intMod n q ≠ 0 then do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
              else do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [Factor.coeff n]))"""
_H2_RHS_BRANCH = """          if intMod n q ≠ 0 then
            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
          else
            pure (ForInStep.yield (r ++ [Factor.coeff n]))"""

for _name, _anchor in (
        ("_IMPL", _IMPL), ("_COEFF", _COEFF), ("_SYM", _SYM), ("_UNIT", _UNIT),
        ("_PROOF_HEAD", _PROOF_HEAD), ("_CORRECT", _CORRECT),
        ("_LEMMA_BRANCH", _LEMMA_BRANCH), ("_LEMMA_CASES", _LEMMA_CASES),
        ("_H2_BRANCH", _H2_BRANCH), ("_H2_RHS_BRANCH", _H2_RHS_BRANCH)):
    if _BASE.count(_anchor) != 1:
        raise AssertionError(f"anchor drift ({_BASE.count(_anchor)}x): {_name}")


def _indexed(per_factor_block):
    """The frozen loop reshaped to carry a position counter.

    Used only by the two single-position near-misses, which must know WHERE in
    the traversal they are. The counter is the sole addition; the reduction
    logic in the `else` arm is the frozen text verbatim, so a rejection is
    attributable to the position special-case and not to a mangled kernel.
    """
    return ("""def implementation_modFactors (q : Int) (factors : List Factor) : List Factor := Id.run do
  if q = 1 then
    return factors
  let mut acc : List Factor := []
  let mut k : Nat := 0
  for f in factors do
"""
            + per_factor_block
            + """
    k := k + 1
  return acc""")


_REDUCE_ARM = """      match f with
      | Factor.coeff n =>
          if intMod n q ≠ 0 then
            acc := acc ++ [Factor.coeff (intMod n q)]
          else
            acc := acc ++ [Factor.coeff n]
      | Factor.sym s =>
          acc := acc ++ [Factor.sym s]"""


def _witness(q, factors):
    """A refutation at one CONCRETE input.

    States that the frozen spec predicate FAILS of the rival's own result at
    that input. Both the spec and the implementation are unfolded so the kernel
    reduces the accumulator loop to a literal list — bare `decide` cannot
    synthesize a `Decidable` instance for the folded application (measured).
    The head binds nothing, so there are no hypotheses to be inconsistent.
    """
    return (f"example : ¬ problem_spec_modFactors ({q} : Int) {factors}\n"
            f"    (implementation_modFactors ({q} : Int) {factors}) := by\n"
            f"  unfold problem_spec_modFactors implementation_modFactors\n"
            f"  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS positives — structurally DIFFERENT but CORRECT impls, each with
    # a proof that genuinely closes for its new shape (verified by real builds
    # during authoring). If a faithful correct impl cannot verify, the
    # obligation is SPEC-TOO-STRONG: over-fit to the frozen loop's syntax.
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different control flow: the accumulator loop is replaced by
        # a direct return of the grounded front-recursive model. Reproved from
        # scratch (the loop-vs-fold bridge is no longer needed, so the new
        # script splits on the divisor arm and closes each side by `simp`); the
        # frozen bridging lemma is left standing untouched, since deleting a
        # frozen declaration is not something a variant may do.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  """def implementation_modFactors (q : Int) (factors : List Factor) : List Factor := Id.run do
  if q = 1 then
    return factors
  return reduceFactors q factors"""),
            _CORRECT + """
  intro q factors
  unfold problem_spec_modFactors implementation_modFactors
  simp only [Id.run]
  by_cases hq1 : q = 1
  · simp only [hq1, if_pos]; rfl
  · simp only [hq1, if_false]
    have h2 : (do
      pure PUnit.unit
      let r ← forIn factors [] fun f r =>
            match f with
            | Factor.coeff n =>
              if intMod n q ≠ 0 then do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
              else do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [Factor.coeff n]))
            | Factor.sym s => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [Factor.sym s]))
      pure r : Id (List Factor)) =
      Id.run (forIn factors [] (fun f r =>
        match f with
        | Factor.coeff n =>
          if intMod n q ≠ 0 then
            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))
          else
            pure (ForInStep.yield (r ++ [Factor.coeff n]))
        | Factor.sym s => pure (ForInStep.yield (r ++ [Factor.sym s])))) := rfl
    rw [h2, modFactors_forIn]
    simp""",
            _CORRECT + """
  intro q factors
  unfold problem_spec_modFactors implementation_modFactors
  by_cases hq1 : q = 1
  · simp [hq1]
  · simp [hq1]"""),
        "rationale": (
            "the cheapest honest correct impl: return the grounded model "
            "`reduceFactors q factors` directly, dropping the accumulator loop "
            "entirely — maximally different control flow from the frozen "
            "forward scan, yet the same value on the WHOLE domain (including "
            "the unit-divisor arm, kept explicitly). Reproved from scratch for "
            "the new shape: the loop-vs-fold bridge is no longer needed, so the "
            "script splits on the divisor arm and closes each side by `simp`. "
            "This is also the no-ungrounded-echo control: the model IS the "
            "reduction work, so a direct return is the correct answer, not a "
            "cheat (there is no opaque answer key to echo). Must verify; if it "
            "cannot, the obligation is over-fit to the loop's syntactic shape "
            "(SPEC-TOO-STRONG). (Sibling: pos-control-echo-reduced-factor.)"),
    },
    {
        "id": "pos-guard-inversion",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the loop but INVERTS the per-coefficient guard and swaps the
        # arms: handle the keep case first, the shrink case second. The two arms
        # still partition the per-factor domain identically, so the value is
        # unchanged at every input. The frozen bridging lemma's STATEMENT
        # mirrors the loop body verbatim, so it is retuned in lockstep (it lives
        # wholly inside the proof region) and its case split is inverted to
        # match.
        "module": (_BASE
                   .replace(_COEFF, """        if intMod n q = 0 then
          acc := acc ++ [Factor.coeff n]
        else
          acc := acc ++ [Factor.coeff (intMod n q)]""", 1)
                   .replace(_LEMMA_BRANCH, """        if intMod n q = 0 then
          pure (ForInStep.yield (r ++ [Factor.coeff n]))
        else
          pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))""", 1)
                   .replace(_LEMMA_CASES, """      by_cases h : intMod n q = 0
      · simp only [if_pos h, ih, reduceFactors, reduceFactor, h, List.append_assoc,
          List.cons_append, List.nil_append]
        simp
      · simp only [if_neg h, ih, reduceFactors, reduceFactor, h, List.append_assoc,
          List.cons_append, List.nil_append]
        simp [h]""", 1)
                   .replace(_H2_BRANCH, """              if intMod n q = 0 then do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [Factor.coeff n]))
              else do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))""", 1)
                   .replace(_H2_RHS_BRANCH, """          if intMod n q = 0 then
            pure (ForInStep.yield (r ++ [Factor.coeff n]))
          else
            pure (ForInStep.yield (r ++ [Factor.coeff (intMod n q)]))""", 1)),
        "rationale": (
            "same per-factor logic, but the coefficient guard is INVERTED and "
            "the arms swapped (keep-case first, shrink-case second). The arms "
            "still partition the per-factor domain identically, so the produced "
            "list is the same at every input; the loop, the traversal order and "
            "the accumulator are untouched. The proof is genuinely rebuilt for "
            "the new shape — the bridging lemma's statement mirrors the loop "
            "body, so it is retuned in lockstep and its case split inverted — "
            "with no obligation weakened and no lemma added. Must verify; if it "
            "cannot, the obligation rejects a faithful guard inversion "
            "(SPEC-TOO-STRONG). (Sibling: pos-control-guard-inversion.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed from precondition admissibility (degenerate: this
    # obligation has NO precondition, it is universally quantified over both
    # binders) to post-image NON-DEGENERACY. The frozen impl AND the frozen
    # proof script are kept verbatim; the case only prepends `have`s that must
    # discharge by kernel computation.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_HEAD, _PROOF_HEAD + """
  have shrinks : problem_spec_modFactors 2 [Factor.coeff 3, Factor.sym 0]
      [Factor.coeff 1, Factor.sym 0] := by
    unfold problem_spec_modFactors; decide
  have keeps_multiple : problem_spec_modFactors 4 [Factor.coeff 8, Factor.sym 1]
      [Factor.coeff 8, Factor.sym 1] := by
    unfold problem_spec_modFactors; decide
  have keeps_at_unit_divisor : problem_spec_modFactors 1 [Factor.coeff 3]
      [Factor.coeff 3] := by
    unfold problem_spec_modFactors; decide
  have order_matters : reduceFactors 2 [Factor.coeff 3, Factor.sym 0]
      ≠ reduceFactors 2 [Factor.sym 0, Factor.coeff 3] := by decide"""),
        "rationale": (
            "the obligation carries NO precondition (it is universally "
            "quantified over both binders), so the sibling's 'is this input "
            "admitted?' probe is degenerate here; the live residual risk is a "
            "DEGENERATE post-image. These `have`s pin, by kernel computation at "
            "concrete inputs, that the spec is satisfiable and non-trivial in "
            "all four independent directions at once: a coefficient with a "
            "non-zero residue SHRINKS (3 against divisor 2 becomes 1 — the "
            "reported scenario's exact discriminator) while the symbolic factor "
            "beside it is preserved; a coefficient whose residue is zero is "
            "KEPT as it was (8 against divisor 4 stays 8, NOT 0); at the unit "
            "divisor the list is returned IDENTICALLY (arm 1); and the "
            "post-image is ORDER-SENSITIVE (permuting the two factors changes "
            "the answer), so the clause is not satisfied by some "
            "order-oblivious degenerate reading. Each `have` is a real goal the "
            "kernel must close — a spec that pinned nothing, or pinned "
            "something else, would fail to elaborate here. The frozen impl AND "
            "the frozen proof script are kept VERBATIM, so the obligation "
            "itself still discharges exactly as it does frozen. If this fails "
            "to verify, the post-image is degenerate or mis-stated. (Sibling: "
            "admiss-f2p-shaped, re-aimed — see the module docstring.)"),
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the FROZEN spec, each of which
    # MUST be rejected, each carrying a machine-checked refutation witness at a
    # DISTINCT concrete input, and each whose faithful real patch was MEASURED
    # to fail the repo's own test set (see REFINEMENT GROUNDING above).
    # =====================================================================
    {
        "id": "reject-never-shrink",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal pre-change behaviour: every coefficient passes through
        # unchanged, no residue is ever taken. Correct on symbolic factors, on
        # multiples of the divisor, and on the whole unit-divisor arm; WRONG on
        # every coefficient with a non-zero residue.
        "module": _swap(_BASE, _COEFF, "        acc := acc ++ [Factor.coeff n]"),
        "refinement": (
            "this is the exact pre-change behaviour — the factor list is "
            "carried through with no per-factor residue taken at all. MEASURED: "
            "applying the faithful real counterpart at base_commit and running "
            "the instance's whole FAIL_TO_PASS + PASS_TO_PASS set fails on the "
            "reported scenario's own assertion (the product with a non-zero "
            "residue coefficient does not collapse the way the issue demands), "
            "with the frozen behaviour passing all 81. A patch that never "
            "reduced any coefficient would NOT resolve; this is the canonical "
            "verify-does-not-imply-resolve rival."),
        "rationale": (
            "REJECT from arm 2 of `result = if q = 1 then factors else "
            "reduceFactors q factors` via the SHRINK outcome: at a coefficient "
            "whose residue is non-zero the clause demands the residue, this "
            "rival yields the original coefficient. If it verified, the "
            "coefficient reduction — the whole discriminating content — would "
            "be unpinned (partial-domain SPEC-TOO-WEAK). Refuted at q=2, "
            "factors=[coeff 3]: the frozen behaviour shrinks 3 to 1. (Sibling: "
            "partial-domain-prepatch-passthrough.)"),
        "witness": _witness("2", "[Factor.coeff 3]"),
    },
    {
        "id": "reject-drop-residue-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the non-zero-residue guard: a coefficient is ALWAYS collapsed to
        # its residue, even when that residue is zero. Correct on every
        # non-zero-residue coefficient and every symbolic factor; WRONG on a
        # multiple of the divisor whose own value is non-zero.
        "module": _swap(_BASE, _COEFF,
                        "        acc := acc ++ [Factor.coeff (intMod n q)]"),
        "refinement": (
            "dropping the non-zero-residue guard rewrites a coefficient that is "
            "a multiple of the divisor to zero instead of keeping it, "
            "collapsing a non-zero coefficient. MEASURED: the faithful real "
            "counterpart fails the instance's test set on a surrounding "
            "assertion about a product whose coefficient is a multiple of the "
            "divisor — such a coefficient must survive so a later stage can "
            "collapse the product correctly — while the frozen behaviour passes "
            "all 81. A patch dropping that guard would NOT resolve. Correct "
            "everywhere else (a true partial-domain break on the keep-multiple "
            "sub-domain)."),
        "rationale": (
            "REJECT from arm 2 via the KEEP-MULTIPLE outcome: at a coefficient "
            "whose residue is zero but whose value is not, the clause demands "
            "the ORIGINAL coefficient, this rival yields zero. If it verified, "
            "the keep-multiple case would be unpinned (SPEC-TOO-WEAK). Refuted "
            "at q=4, factors=[coeff 8]: residue is zero, so the frozen "
            "behaviour keeps 8 while the rival collapses it to 0 — a distinct "
            "sub-domain from every other rival's witness. (Sibling: "
            "partial-domain-drop-residue-guard.)"),
        "witness": _witness("4", "[Factor.coeff 8]"),
    },
    {
        "id": "reject-rewrite-symbolic",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the is-a-coefficient guard: apply the residue rewrite to a
        # symbolic factor's opaque tag as if it were a coefficient. Correct on
        # every concrete coefficient; WRONG on a symbolic factor whose tag has a
        # non-zero residue.
        "module": _swap(_BASE, _SYM, """    | Factor.sym s =>
        if intMod (Int.ofNat s) q ≠ 0 then
          acc := acc ++ [Factor.sym (intMod (Int.ofNat s) q).toNat]
        else
          acc := acc ++ [Factor.sym s]"""),
        "refinement": (
            "the normalisation reduces only concrete coefficients and leaves "
            "every symbolic factor exactly as it was. MEASURED: the faithful "
            "real counterpart (the residue rewrite applied without the "
            "is-a-coefficient guard) fails the instance's test set on the "
            "reported scenario's own assertion, because rewriting the symbolic "
            "part of the product destroys the very factor the expected result "
            "is stated in terms of; the frozen behaviour passes all 81. A patch "
            "dropping that guard would NOT resolve. Correct on every concrete "
            "coefficient (a partial-domain break on the keep-symbolic "
            "sub-domain)."),
        "rationale": (
            "REJECT from arm 2 via the KEEP-SYMBOLIC outcome: at a symbolic "
            "factor the clause demands that exact factor back, this rival "
            "rewrites its tag. If it verified, the preservation of symbolic "
            "factors would be unpinned (SPEC-TOO-WEAK). Refuted at q=2, "
            "factors=[sym 3] — the only witness that puts the `factors` binder "
            "on the SYMBOLIC constructor with a rewritable tag, a dimension no "
            "coefficient rival can reach. (Sibling: "
            "partial-domain-drop-is-int-guard.)"),
        "witness": _witness("2", "[Factor.sym 3]"),
    },
    {
        "id": "reject-drop-symbolic",
        "kind": "uniqueness",
        "expect": "reject",
        # A structural rather than value-level break: symbolic factors are
        # DROPPED from the rebuilt list, so the result is shorter than the
        # input. Every surviving factor's value is correct.
        "module": _swap(_BASE, _SYM, """    | Factor.sym _ =>
        acc := acc"""),
        "refinement": (
            "the rebuilt factor list must be the input's image factor-for-"
            "factor: same length, same order. This rival silently discards "
            "every symbolic factor, so a product loses its symbolic part "
            "entirely. MEASURED: the faithful real counterpart fails the "
            "instance's test set (a product whose symbolic factor is dropped "
            "reduces to a bare coefficient, breaking the surrounding "
            "substitution assertions) while the frozen behaviour passes all 81, "
            "so it would NOT resolve. Every factor it does keep carries the "
            "correct value, which is what makes this a LENGTH/structure break "
            "rather than a value break — a distinct failure mode from every "
            "other rival here."),
        "rationale": (
            "REJECT from arm 2's structural content: `reduceFactors` is a "
            "length- and order-preserving per-factor map, so the clause pins "
            "the result's LENGTH as well as its values; this rival returns a "
            "shorter list. If it verified, the clause would not pin that the "
            "output has one factor per input factor, and a rival could silently "
            "drop factors (SPEC-TOO-WEAK). Refuted at q=2, factors=[sym 5]: the "
            "frozen behaviour returns a one-element list, the rival the empty "
            "one. A distinct point from reject-rewrite-symbolic (different tag, "
            "and the two rivals disagree with gold in different ways — one on "
            "the value, one on the length — so they do not share a witness)."),
        "witness": _witness("2", "[Factor.sym 5]"),
    },
    {
        "id": "reject-fixed-divisor",
        "kind": "uniqueness",
        "expect": "reject",
        # An attack on the ARGUMENT rather than the outcome: the residue is
        # taken against a hardcoded divisor instead of the actual one. Agrees
        # with the frozen behaviour whenever the actual divisor happens to be
        # that constant; WRONG otherwise. This is what makes the `q` binder
        # demonstrably load-bearing inside arm 2.
        "module": _swap(_BASE, _COEFF, """        if intMod n 2 ≠ 0 then
          acc := acc ++ [Factor.coeff (intMod n 2)]
        else
          acc := acc ++ [Factor.coeff n]"""),
        "refinement": (
            "the residue must be taken against the ACTUAL divisor; this rival "
            "hardcodes one. MEASURED: the faithful real counterpart fails the "
            "instance's test set on an assertion involving a different divisor "
            "(the reduced coefficient comes out wrong whenever the real divisor "
            "is not the hardcoded one), while the frozen behaviour passes all "
            "81, so it would NOT resolve. It agrees with the frozen behaviour "
            "on every product whose divisor happens to equal the constant — "
            "including the reported scenario itself, which is exactly why it "
            "needs a witness at a DIFFERENT divisor."),
        "rationale": (
            "REJECT from arm 2 by attacking the ARGUMENT the residue is applied "
            "to rather than the per-factor outcome: the clause's residue is "
            "taken against the binder `q`, this rival against a constant. If it "
            "verified, the clause would not pin WHICH divisor the reduction "
            "uses, and the `q` binder would be free inside arm 2 "
            "(SPEC-TOO-WEAK). Refuted at q=3, factors=[coeff 5]: the frozen "
            "behaviour yields 2, the rival 1. This is the only witness that "
            "moves the divisor OFF the values every other reduction rival uses, "
            "so it is what demonstrates the battery's dependence on `q` within "
            "arm 2. (Sibling: none — nagini's residue primitive is a "
            "@ContractOnly axiom validated by its AXIOM lane, so no sibling "
            "SPEC case attacks the divisor argument; added here because this "
            "carrier models the arithmetic deeply and can therefore refute it.)"),
        "witness": _witness("3", "[Factor.coeff 5]"),
    },
    {
        "id": "reject-clear-at-unit-divisor",
        "kind": "uniqueness",
        "expect": "reject",
        # The ONLY rival attacking arm 1. At a unit divisor the list must be
        # returned identically; this rival clears it. Perfectly correct on the
        # entire reduction arm.
        "module": _swap(_BASE, _UNIT, """  if q = 1 then
    return []"""),
        "refinement": (
            "at a unit divisor the factor list must be returned exactly as it "
            "was — reducing there would erase every coefficient, since every "
            "integer is congruent to zero modulo one. This rival empties the "
            "list instead. MEASURED: the faithful real counterpart fails the "
            "instance's test set on the surrounding unit-divisor assertions "
            "(a product normalised against a unit divisor comes back empty, so "
            "the expected residual expression is lost) while the frozen "
            "behaviour passes all 81, so it would NOT resolve. Instrumenting "
            "the real code confirms the unit-divisor arm is genuinely REACHED "
            "by the instance's own tests, so this is a live sub-domain and not "
            "a modeling artifact. Perfectly correct on the whole reduction arm."),
        "rationale": (
            "REJECT from ARM 1 of the clause — the `q = 1` branch — which no "
            "other rival touches: the clause demands `factors` back unchanged, "
            "this rival returns the empty list. If it verified, the unit-divisor "
            "arm would be entirely unpinned and a rival could return anything "
            "there (SPEC-TOO-WEAK on an independent top-level arm). Refuted at "
            "q=1, factors=[coeff 3] — the sole witness in the battery that "
            "drives the `q` binder to the unit divisor and so selects arm 1; "
            "every other witness holds q ≠ 1 and exercises arm 2 only."),
        "witness": _witness("1", "[Factor.coeff 3]"),
    },
    {
        "id": "reject-first-factor-unreduced",
        "kind": "uniqueness",
        "expect": "reject",
        # Single-position near-miss: correct at every position but the FIRST,
        # which is passed through unreduced.
        "module": _swap(_BASE, _IMPL, _indexed("""    if k = 0 then
      acc := acc ++ [f]
    else
""" + _REDUCE_ARM)),
        "refinement": (
            "special-casing the first factor to pass through unreduced leaves a "
            "leading coefficient un-shrunk while reducing the rest. MEASURED: "
            "the faithful real counterpart fails the instance's test set on the "
            "reported scenario's own assertion — the product there has its "
            "reducible coefficient in the LEADING position, so skipping "
            "position 0 reproduces the original bug exactly — while the frozen "
            "behaviour passes all 81. A real first-element bug would NOT "
            "resolve. Correct at every trailing position (a single-position "
            "partial-domain break)."),
        "rationale": (
            "REJECT from arm 2 at POSITION 0: `reduceFactors` is applied "
            "factor-for-factor, so the clause pins the head as tightly as the "
            "tail; this rival returns the head unchanged. If it verified, the "
            "first position would be unpinned and a rival mishandling only the "
            "head would slip through (partial-domain SPEC-TOO-WEAK). Refuted at "
            "q=2, factors=[coeff 3, sym 0] — a LENGTH-2 list (the only length "
            "besides 1 in the battery) whose head is reducible, so the witness "
            "exercises the traversal as well as the position. (Sibling: "
            "partial-domain-first-factor-zero, re-shaped from 'force the head "
            "to zero' to 'pass the head through unreduced', which is the "
            "natural carrier shape and — unlike the force-to-zero form, whose "
            "real patch this port MEASURED as failing for an unrelated reason — "
            "is refuted precisely on the head-position sub-domain it claims.)"),
        "witness": _witness("2", "[Factor.coeff 3, Factor.sym 0]"),
    },
    {
        "id": "reject-euclidean-residue",
        "kind": "uniqueness",
        "expect": "reject",
        # The residue CONVENTION, which no other rival attacks. Lean's `Int.%`
        # is `Int.emod` (Euclidean: residue always non-negative), whereas the
        # frozen `intMod` is FLOORED (residue carries the sign of the divisor).
        # The two agree for every POSITIVE divisor, so this rival is correct on
        # the whole sub-domain all seven other reduction rivals live in, and
        # differs exactly at a NEGATIVE divisor with a non-zero residue.
        "module": _swap(_BASE, _COEFF, """        if n % q ≠ 0 then
          acc := acc ++ [Factor.coeff (n % q)]
        else
          acc := acc ++ [Factor.coeff n]"""),
        "refinement": (
            "HONEST SCOPE NOTE — read this before treating it as a "
            "verify-does-not-imply-resolve rival, because it is NOT one, and "
            "saying otherwise would be the false-refinement failure the footer's "
            "DISQUALIFIED list exists to prevent. MEASURED: the faithful real "
            "counterpart of a wrong-sign residue passes all 81 FAIL_TO_PASS + "
            "PASS_TO_PASS tests, i.e. it RESOLVES. So this case does not "
            "demonstrate that verification is stronger than the test suite; it "
            "demonstrates the acceptable converse, that the frozen spec is "
            "STRICTER than the tests on the residue convention. It is shipped "
            "anyway because the convention is a clause the frozen spec really "
            "does pin — mapping.md makes the floored (sign-of-divisor) residue "
            "the R-leg refinement, since the surrounding library's integer "
            "remainder follows the divisor's sign — and until now NO reject case "
            "defended it, leaving the whole negative-divisor sub-domain "
            "unattacked. Instrumenting the patched loop over all 81 tests shows "
            "that sub-domain is genuinely REACHED (negative divisors occur among "
            "the reached (coefficient, divisor) pairs), so it is a live part of "
            "the modeled behaviour rather than a modeling artifact — it is "
            "merely not test-DISCRIMINATED. If this rival VERIFIED, the residue "
            "convention would be entirely unpinned and the floored/Euclidean "
            "distinction the spec claims to make would be fictitious."),
        "rationale": (
            "REJECT from arm 2 by attacking the residue's CONVENTION rather than "
            "its argument, its guard, or its per-factor outcome: the clause's "
            "residue is `intMod` (floored, sign of the divisor), this rival uses "
            "Lean's `Int.%` (`Int.emod`, Euclidean, always non-negative). The two "
            "coincide at every positive divisor, so this rival is correct on the "
            "entire sub-domain the other seven reduction rivals occupy, which is "
            "what makes it a genuinely new direction rather than a respelling. "
            "Refuted at q=-2, factors=[coeff -1]: the frozen behaviour yields "
            "intMod (-1) (-2) = -1, the rival (-1) % (-2) = 1. This is the ONLY "
            "witness in the battery that drives either binder NEGATIVE, so it is "
            "what closes the reject lane's one recorded binder-spread gap. "
            "(Sibling: none directly — nagini's residue is a @ContractOnly axiom "
            "validated in its AXIOM lane; the velvet sibling's "
            "reject-wrong-residue-sign is the same idea, though its refinement "
            "claim does not hold on this instance — see the footer.)"),
        "witness": _witness("(-2)", "[Factor.coeff (-1)]"),
    },
    {
        "id": "reject-last-factor-zeroed",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual single-position near-miss: correct at every position but the
        # LAST, which is forced to a fixed zero coefficient. Refuted at the
        # mirror image of the head rival's input, so the two do not share a
        # witness.
        "module": _swap(_BASE, _IMPL, _indexed("""    if k + 1 = factors.length then
      acc := acc ++ [Factor.coeff 0]
    else
""" + _REDUCE_ARM)),
        "refinement": (
            "forcing the final factor to a fixed zero coefficient destroys the "
            "trailing factor of the product outright. MEASURED: the faithful "
            "real counterpart fails the instance's test set — a product whose "
            "last factor is zeroed collapses to zero rather than to the "
            "expected residual expression, breaking a surrounding substitution "
            "assertion — while the frozen behaviour passes all 81, so it would "
            "NOT resolve. Correct at every leading position (the dual "
            "single-position break, on the sub-domain the head rival gets "
            "right)."),
        "rationale": (
            "REJECT from arm 2 at the LAST position: the clause pins the tail "
            "factor to the image of the input's tail factor, this rival forces "
            "a constant there. If it verified, the last position would be "
            "unpinned (partial-domain SPEC-TOO-WEAK). Refuted at q=2, "
            "factors=[sym 0, coeff 3] — the MIRROR of the head rival's input, "
            "chosen deliberately: this rival is correct at the head and that one "
            "is correct at the tail, so neither witness refutes the other rival "
            "and the two positions are demonstrated independently rather than "
            "sharing a point. (Sibling: partial-domain-last-factor-zero.)"),
        "witness": _witness("2", "[Factor.sym 0, Factor.coeff 3]"),
    },
]


# ===========================================================================
# NAGINI -> LEAN ACCOUNTING
# ===========================================================================
# The sibling ships 10 SPEC cases (2 soundness, 1 admissibility, 7 uniqueness —
# 2 of them mandatory frame-mutation rivals) plus a 3-probe AXIOM lane. It
# contracts `reduce_coefficients(is_int: List[int], value: List[int], m: int)`
# over TWO parallel read-only permission-carrying list inputs plus the divisor.
#
# This bundle models the SAME per-factor rewrite over ONE fused carrier: the
# sibling's parallel (is_int[k], value[k]) pair becomes a single `Factor` per
# position (`coeff n` is the is_int=1 case, `sym s` the is_int=0 case). That
# fusion is faithful — the normalisation observes only whether a factor is a
# concrete coefficient and, if so, its residue (mapping.md) — and it is what
# collapses the two frame rivals into the vacuous class. This bundle also models
# ONE thing the sibling does not: the UNIT-DIVISOR arm, which the sibling folds
# into its `m >= 2` precondition and therefore cannot attack at all.
#
#   sibling case                          kind          -> here                          disposition
#   ---------------------------------------------------------------------------------------------------
#   pos-control-echo-reduced-factor       soundness     -> pos-direct-model               PORTED
#   pos-control-guard-inversion           soundness     -> pos-guard-inversion            PORTED
#   admiss-f2p-shaped                     admissibility -> admiss-nondegenerate           RE-AIMED
#   frame-mutate-readonly-value           uniqueness    -> (none)                         VACUOUS
#   frame-mutate-readonly-is-int          uniqueness    -> (none)                         VACUOUS
#   partial-domain-prepatch-passthrough   uniqueness    -> reject-never-shrink            PORTED
#   partial-domain-drop-is-int-guard      uniqueness    -> reject-rewrite-symbolic        PORTED
#   partial-domain-drop-residue-guard     uniqueness    -> reject-drop-residue-guard      PORTED
#   partial-domain-first-factor-zero      uniqueness    -> reject-first-factor-unreduced  PORTED (re-shaped)
#   partial-domain-last-factor-zero       uniqueness    -> reject-last-factor-zeroed      PORTED
#   (no sibling — structural/length)      uniqueness    -> reject-drop-symbolic           ADDED
#   (no sibling — residue argument)       uniqueness    -> reject-fixed-divisor           ADDED
#   (no sibling — unit-divisor arm)       uniqueness    -> reject-clear-at-unit-divisor   ADDED
#   (no sibling — residue convention)     uniqueness    -> reject-euclidean-residue       ADDED (audit)
#   AXIOM_TESTS (residue / reduced_factor) axiom        -> (none)                         DROPPED (G-AX's lane)
#
# 5 uniqueness ported + 4 added, 2 soundness ported, 1 admissibility re-aimed;
# 2 uniqueness vacuous; axiom lane dropped. 12 cases, of which 9 reject.
#
# PORTED (both positives): the sibling's cheapest-correct shape binds the pure
#   per-factor helper directly; here that is a loop-free direct return of the
#   grounded model (pos-direct-model), reproved from scratch. The guard-inversion
#   positive ports as-is in spirit (pos-guard-inversion), but on this backend it
#   is real work: the frozen bridging lemma's STATEMENT mirrors the loop body, so
#   inverting the guard forces the lemma and its case split to be retuned in
#   lockstep. Both proofs were closed honestly — no obligation weakened, no
#   helper lemma added, no `sorry`.
# RE-AIMED (admiss-f2p-shaped): the sibling asserts an F2P-shaped input meets its
#   fractional-permission precondition. This obligation has NO precondition, so
#   that probe is degenerate; re-aimed at post-image non-degeneracy across all
#   three per-factor outcomes, the unit-divisor arm, and order-sensitivity.
# PORTED (the value rivals): prepatch-passthrough, drop-is-int-guard and
#   drop-residue-guard port one-for-one onto the three per-factor outcomes.
#   first-factor-zero is RE-SHAPED from "force the head to zero" to "pass the
#   head through unreduced" — see the DISQUALIFIED note below, which is why.
#   last-factor-zero ports in the sibling's own force-to-zero form, which
#   measurement confirms is refutable AND non-resolving on this instance.
# ADDED (4): reject-drop-symbolic attacks the clause's STRUCTURAL content (the
#   result's length/order, not any factor's value) — a failure mode the
#   sibling's per-index value pin cannot express, since its length is fixed by a
#   separate `len(Result()) == len(value)` clause the impl cannot violate.
#   reject-fixed-divisor attacks the residue's ARGUMENT rather than its outcome;
#   the sibling cannot, because its residue is a @ContractOnly axiom validated in
#   its AXIOM lane instead. reject-clear-at-unit-divisor attacks ARM 1, which
#   exists only here (the sibling's `m >= 2` precondition excludes it) and which
#   instrumenting the real code confirms the instance's own tests REACH.
#   reject-euclidean-residue (added by the audit) attacks the residue's
#   CONVENTION — floored vs Euclidean, which differ exactly at a negative divisor
#   — the one clause of the frozen spec that had no rival at all; its refinement
#   states its own honest scope (spec-stricter-than-tests, not verify-not-resolve).
#   The eight reject witnesses probe EIGHT DISTINCT input points -> now NINE.
# VACUOUS (both frame rivals): they write into a read-only input held at a
#   fractional heap permission (`value[0] = 0` / `is_int[0] = 0`) and are
#   rejected for insufficient permission. Lean is referentially transparent:
#   `factors` is an immutable value, there is no heap, no aliasing, no `Old`, no
#   permission system. Nothing to overwrite, no frame clause to trip, so the
#   class has NO carrier analogue — omitted as a carrier fact, not fabricated.
#   The directive it maps to (no output component left free) holds structurally:
#   the clause is a total EQUALITY pinning the entire result list.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this gate ignores it.
#   This bundle declares NO axiom and NO opaque callee anyway — the residue is
#   modeled deeply over exact integer arithmetic (mapping.md), carried by G-CONF.
#
# DIVERGENCE lane: a KNOWN HOLE. Corrected by the audit — the previous text here
#   claimed the class was "genuinely VACUOUS rather than a known spec hole"
#   because "a non-terminating implementation cannot be written at all". Real
#   builds refute that: a `partial def` self-call is in scope (variant_problems
#   == []) and IS rejected, so the class is expressible. It is not SHIPPABLE,
#   because a `partial def` does not reduce in the kernel: the witness and a
#   forgery asserting the exact opposite claim both fail with the same
#   stuck-reduction error, so no `decide` witness discriminates and the gate
#   would record `witness-undecided` (inconclusive => MALFORMED-TESTS, not a
#   pass). See the module docstring for both exit codes and both error texts.
#   Disposition: the spec does not pin termination on this carrier. That is a
#   statement about the SPEC, not a certificate that the battery is complete —
#   which is exactly the distinction the old "vacuous" wording erased.
#
# ---------------------------------------------------------------------------
# DISQUALIFIED BY MEASUREMENT — 4 rivals NOT shipped because their faithful real
# patches RESOLVE (all 81 FAIL_TO_PASS + PASS_TO_PASS tests pass). Each is wrong
# against the frozen spec and each WOULD be rejected with a discriminating
# witness, so each would have "passed" this gate — while asserting a `refinement`
# that is factually false. A reject case whose real patch resolves does not
# demonstrate verify-does-not-imply-resolve; it demonstrates that the spec is
# STRICTER than the tests, which is a different (and acceptable) property, and
# claiming otherwise would corrupt the record. Recorded here so the information
# is not lost:
#   * LAST-FACTOR-UNREDUCED (pass the tail through unreduced) — resolves. Every
#     product the instance's tests reach carries its reducible coefficient in the
#     LEADING position, so skipping the tail is never observed. This is why
#     first-factor-unreduced ships in the pass-through form but the tail rival
#     ships in the sibling's force-to-zero form instead (that one does fail).
#   * TRUNCATING RESIDUE and EUCLIDEAN RESIDUE (wrong-sign remainder) — both
#     resolve. The DISPOSITION is confirmed by measurement (both real patches
#     pass all 81), but an earlier revision of this note gave the wrong REASON
#     ("every concrete coefficient the tests reach is NON-NEGATIVE, so the three
#     conventions coincide on the reached domain"). Re-instrumenting the patched
#     loop over all 81 tests refutes that: the reached (coefficient, divisor)
#     pairs are {(3,9), (4,4), (-1,2), (-1,4), (-1,-2), (-1,-4)}, so a NEGATIVE
#     coefficient and NEGATIVE divisors are both reached, and the conventions do
#     NOT coincide there (floored/truncating/Euclidean give 1/-1/1 at (-1,2) and
#     -1/-1/1 at (-1,-2)). The real reason both patches still resolve is
#     narrower and is what actually matters: at every reached pair the factor is
#     a UNIT coefficient multiplying a symbolic factor, and the assertions that
#     observe those products normalise the sign away upstream, so they are
#     insensitive to which residue convention produced the coefficient — so
#     the sign convention is not test-DISCRIMINATED even though the sign domain
#     is test-REACHED. Conclusion unchanged: a sign rival cannot honestly carry
#     a refinement argument on this instance. NB the velvet sibling ships
#     exactly such a rival (reject-wrong-residue-sign); on the evidence here
#     that case's refinement claim does not hold for this instance, which is
#     worth a look when that cell is next revisited.
#   * ONLY-HEAD-EXAMINED / ABS-DIVISOR — resolve, same reason (the reached
#     sub-domain does not separate them from the frozen behaviour).
#
# ---------------------------------------------------------------------------
# BINDER / CLAUSE / OBLIGATION COVERAGE
#   The sole obligation `correct_modFactors` is DEFENDED by 2 soundness positives
#   + 1 admissibility case (3 expect="verify") and ATTACKED by 9 rivals.
#
#   Both top-level ARMS of the clause are attacked: arm 1 (`q = 1`, identity) by
#   reject-clear-at-unit-divisor; arm 2 (`reduceFactors q factors`) by the other
#   eight. Within arm 2, all THREE per-factor outcomes are attacked (shrink /
#   keep-multiple / keep-symbolic), plus the residue's ARGUMENT and its
#   CONVENTION, plus the structural length/order content, plus the first and last
#   traversal positions.
#
#   The 9 reject witnesses probe 9 DISTINCT input points (pts=9):
#     * reject-never-shrink            q=1?no  q=2  [coeff 3]          shrink
#     * reject-drop-residue-guard              q=4  [coeff 8]          keep-multiple
#     * reject-rewrite-symbolic                q=2  [sym 3]            keep-symbolic
#     * reject-drop-symbolic                   q=2  [sym 5]            length/structure
#     * reject-fixed-divisor                   q=3  [coeff 5]          residue argument
#     * reject-clear-at-unit-divisor           q=1  [coeff 3]          ARM 1
#     * reject-first-factor-unreduced          q=2  [coeff 3, sym 0]   position 0
#     * reject-last-factor-zeroed              q=2  [sym 0, coeff 3]   last position
#     * reject-euclidean-residue               q=-2 [coeff -1]         residue convention
#   `q` moves across {1, 2, 3, 4, -2} — critically INCLUDING the unit divisor, which
#   selects the other arm, and including q=3, which no per-factor-outcome rival
#   uses. `factors` moves across BOTH constructors, across lengths {1, 2}, and
#   across the head and tail positions. NO binder is held at a single value
#   across the reject set, and no two rivals share a witness: each of the eight
#   was individually confirmed to elaborate against its own rival and fail
#   against the frozen solution.
#
#   AUDIT PROBES — 8 additional impls built against the frozen spec and NOT
#   shipped, because each behaved as the spec requires and so adds no coverage
#   the nine rivals above do not already carry. Recorded so the next reader knows
#   these directions were measured rather than assumed:
#     WRONG impls, all correctly REJECTED (exit 1), each with its refutation
#     witness confirmed to hold of the rival (exit 0):
#       * reverse the traversal (prepend instead of append) — attacks ORDER,
#         refuted at q=2, [coeff 3, sym 7];
#       * TRUNCATING residue (`n - q * Int.tdiv n q`) — a third convention,
#         distinct from both floored (frozen) and Euclidean (shipped rival);
#         refuted at q=2, [coeff (-1)];
#       * duplicate every factor — a length INCREASE, where reject-drop-symbolic
#         is a length decrease; refuted at q=2, [coeff 3];
#       * pass an INTERIOR position (index 1) through unreduced — no shipped
#         rival attacks a middle position; refuted at q=2,
#         [sym 0, coeff 3, sym 1].
#     CORRECT reshapes, all of which VERIFY, so the obligation is not over-fit to
#     the frozen loop's syntax beyond what the two shipped positives show:
#       * `factors.map (reduceFactor q)` in place of the accumulator loop;
#       * accumulate BACKWARDS with `::` then `.reverse` — a different traversal
#         shape, needing its own bridging `have` over the reversed accumulator;
#       * a redundant `factors.isEmpty` early return before the loop.
#     One probe VERIFIED and is VACUOUS rather than a spec hole: widening the
#     early-return guard from `q = 1` to `q = 1 ∨ q = 0`. At q=0 the frozen model
#     is ALREADY the identity (`Int.fdiv n 0 = 0`, so `intMod n 0 = n` and every
#     factor is kept), so the widened impl is extensionally EQUAL to the frozen
#     one and verifying is the correct outcome, not a hole. Confirmed by build:
#     `intMod 5 0 = 5` closes by `decide`.
#
#   NEGATIVE divisors and negative coefficients are now attacked, by
#   reject-euclidean-residue (q=-2, [coeff -1]) — the ninth reject case and the
#   only one that drives either binder negative. An earlier revision recorded
#   this as a deliberate gap on the ground that a sign rival's real patch
#   RESOLVES and so cannot carry a verify-does-not-imply-resolve argument. The
#   measurement is right and is preserved, but the conclusion drawn from it was
#   wrong: the residue CONVENTION is a clause the frozen spec genuinely pins
#   (mapping.md's R-leg), it is refutable on this carrier, and leaving it
#   undefended meant a rival could have replaced floored with Euclidean and
#   nothing in the battery would have noticed. The case therefore ships with its
#   scope stated honestly in its own `refinement` — spec-stricter-than-tests, NOT
#   verify-not-resolve — which is the disclosure the DISQUALIFIED list is for,
#   rather than being silently omitted.
#
# AXIOM_TESTS: empty. This bundle declares no axiom and no opaque callee; the
#   changed arithmetic is modeled deeply and validated by G-CONF, and this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
