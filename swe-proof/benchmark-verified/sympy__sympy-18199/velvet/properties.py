"""properties.py — G-PBT falsification battery for sympy__sympy-18199 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct nthRoots`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the discrimination subject — here the ``witness_reference``, a correct
loop-free impl of the same spec that the gate independently verifies, because the
frozen impl's ``while`` loop makes the witnesses' reduction lemma inapplicable
and its exit code would attest to a shape mismatch; see the carrier note).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  nthRoots (a : Int) (n : Int) (p : Int) return (out : List Int)
    require  a ≥ 0
    require  n > 2
    require  p ≥ 2
    require  isPrime p ∨ compositeValidated a n p
    ensures  (S)     ∀ k, k < out.length → isRoot out[k]! n p a
    ensures  (C-comp) (¬ isPrime p ∧ compositeValidated a n p)
                        → out = rootsBelow p.toNat a n p
    ensures  (C-res)  (isPrime p ∧ a % p ≠ 0 ∧ isNthResidue a n p)
                        → out = primeRoots a n p
    ensures  (C-nores)(isPrime p ∧ a % p ≠ 0 ∧ ¬ isNthResidue a n p)
                        → out = []
    ensures  (C-zero) (isPrime p ∧ a % p = 0)
                        → out.length = 1 ∧ out[0]! = 0

The task: find every in-range residue solving a modular power equation. The
load-bearing content is COMPLETENESS: soundness (S) alone is satisfied VACUOUSLY
by the empty list and by any SUBSET of the true root set, so it never forces the
result to be the WHOLE root set. The three completeness clauses pin the result
EXACTLY — the deep grounded fold on the non-prime branch (C-comp), and the exact
singleton on the prime zero-target branch (C-zero) — which is precisely where the
two documented defects live: the dropped zero root over a prime modulus (the
headline issue example) and the declined non-prime modulus (the F2P bug).

CARRIER NOTE — an OPAQUE-oracle carrier, so the reject lane is stated by
CONDITIONING, not by ``decide``.

  ``isPrime`` / ``isNthResidue`` / ``primeRoots`` are opaque axioms and
  ``rootsBelow`` is a ``noncomputable`` fold over the opaque ``powerMod``; the
  whole post-image is ``noncomputable``. Two consequences drive every design
  choice:

   1. The ``extract_program_for`` / ``derive_tester_for`` + ``decide`` witness
      route is UNAVAILABLE: extraction cannot compile a program whose
      postcondition depends on the noncomputable fold. So each reject ``witness``
      refutes the method's Hoare TRIPLE directly, reduced through ``triple_pure``
      (every rival below is straight-line, so the whole ``do`` block is a single
      ``pure``), checked in a file whose ``prove_correct`` block has been
      stripped so no tactic script can mask the verdict.
   2. No literal input decides anything (``isPrime 17`` does not compute). So
      each witness states its refutation at a point described by HYPOTHESIS
      (``hp : isPrime p``, ``hnp : ¬ isPrime p``, ``hcv : compositeValidated
      a n p``, ``hne : rootsBelow p.toNat a n p ≠ []``), and the disequality
      holds exactly on the sub-domain where the rival diverges from the spec — a
      STRONGER statement than any single literal input could make. Each witness
      was SEEN to discriminate (ELABORATES against the rival, FAILS on gold) and
      its binders are jointly satisfiable (the ``example … : False`` consistency
      probe leaves ``False`` unsolved), so none is a contradiction-forgery.

  AUDIT NOTE — why the second half of every discrimination check on this bundle
  is taken against a ``witness_reference`` and not against gold.

    Measured, not argued. The frozen impl's ``do`` block is a WHILE LOOP, so its
    triple elaborates to a ``forIn`` term; every reject rival here is
    straight-line, so its triple elaborates to a single ``pure``. Each witness
    opens with ``simp only [triple_pure, le_Prop_eq]``, which fires only on the
    ``pure`` shape. Against GOLD the build therefore fails with BOTH simp
    arguments reported UNUSED and the error landing on the following ``obtain``
    (``rcases failed: right✝ : w✝ is not an inductive datatype``) — a
    CONTROL-FLOW SHAPE mismatch, not a semantic refutation of the concrete
    claim. A gold-side exit code obtained that way would attest to a tactic
    mismatch, so it is NOT what these cases rest on. Nor is it repairable by
    re-tactic-ing: ``triple_pure`` cannot apply to gold's loop at all, and a
    witness that DID reduce gold's ``forIn`` would be reproving the frozen loop
    rather than refuting a rival.

    So every reject case carries ``witness_reference = _WITNESS_REFERENCE``, and
    the gate takes the "must FAIL" half against THAT — a CORRECT, loop-free impl
    of the frozen spec (the gold branch ladder with ``return target``), whose
    obligation is reproven from scratch because the frozen script cannot close
    it. The gate checks the reference shares the frozen spec and VERIFIES before
    trusting it, so it cannot be an impl that merely fails everything. On the
    reference ``triple_pure`` FIRES (measured: zero ``unused simp argument``
    warnings, against two on gold), so the only remaining difference from the
    rival is the per-branch VALUE and the refutation is attributable to the
    clause rather than to the shape. Each of the seven fails there at the value
    level — ``decline-composite`` with ``Eq.symm hout has type rootsBelow … =
    rootsBelow … but is expected to have type rootsBelow … = []``, ``drop-last``
    with ``did not find (List.dropLast ?m).length in (rootsBelow …).length =
    (rootsBelow …).length``, and ``reverse-composite-order`` with ``hout has
    type rootsBelow … = rootsBelow … but is expected to have type
    (rootsBelow …).reverse = rootsBelow …``.

    The eighth, ``poison-domain-edge``, WAS HOLLOW and is repaired; the claim
    this note previously made about it was false and is withdrawn. Its witness
    opened by rewriting the rival's own guard (``rw [if_pos hle]``), so the
    reference-side failure was ``rewrite failed: did not find if p ≤ 2 then ?m
    else ?m`` — an error about which BRANCHES the subject has, not about what the
    witness claims. That is NOT "the right signal for a rival whose defect is an
    extra branch": the forgery pair (attack B′) shows it carried no information
    at all, because replacing the closing step with a deliberate type error left
    the reference-side error BYTE-IDENTICAL. A witness asserting the reference is
    CORRECT at the edge would have been recorded ``rejected`` on the same exit
    code. Repaired to reduce from the HYPOTHESES (``simp [hle, hp, hz]``), which
    fires on either ladder; type-revealed, the RIVAL carries the FALSE claim
    ``0 = 1 ∧ [][0]! = 0`` and the REFERENCE the true one ``True ∧ [0][0]! = 0``.
    See ``_W_DOMAIN``.

    The three (C-zero) cases fail there with ``unsolved goals``, which alone
    would not say whether the claim was evaluated, so each was additionally
    type-revealed (replacing the closing step with ``exact (hout : Nat)`` to
    print the hypothesis's real type). That pair is the refutation: on the
    REFERENCE the hypothesis is the TRUE equation (``[0].length = 1 ∧
    [0][0]! = 0``), on the RIVAL the FALSE one (``[].length = 1 ∧ [][0]! = 0``
    for drop-zero-root, ``[0, 0].length = 1`` for two-zeros-prime, and
    ``[1][0]! = 0`` for zero-wrong-value). The error text tracks the claim, so
    the exit codes carry information about it.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive control — APPLIES, at two strengths. A structurally
    different but behaviourally identical impl must still verify, else the
    postcondition is SPEC-TOO-STRONG on the impl's data-flow shape.
    ``pos-reshape-inline`` is the WEAK form (the per-element name binding inlined
    into the copy prepend): the produced accumulator is definitionally identical,
    so the frozen proof closes unchanged and it reproves nothing.
    ``pos-loopfree-reproven`` is the STRONG form — the backward copy loop
    abandoned entirely for a direct ``return target``, which the frozen script
    cannot close, so the obligation is reproven from scratch. It is also the
    ``witness_reference``; see the carrier note.
  * ADMISSIBILITY — RE-AIMED. Every ``require`` is satisfiable by an F2P/issue
    input (a prime modulus, or a validated composite one), so the "a normal input
    meets the precondition" probe is not where the risk sits on this opaque
    carrier — no concrete literal is provably ``isPrime``. The residual risk is
    that the FIVE post clauses (four of them implications with overlapping
    guards) are JOINTLY UNSATISFIABLE at some reachable input, which reads
    exactly like a spec every impl meets. ``admiss-joint-satisfiable`` discharges
    that: the frozen impl verifying against all five clauses IS the witness.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — APPLY, and carry the battery's
    discriminating content. Eight rivals attack the two load-bearing completeness
    clauses from the UNDER-keep and OVER-keep sides, on the value conjunct, on
    the sequence-vs-multiset reading, and — the one non-value axis — at the LOW
    EDGE of the declared modulus domain, where a rival that is gold everywhere
    else hides its answer in an input the Requires might not have admitted. Each
    carries a machine-checked refutation witness conditioned on the carrier at the
    sub-domain it abuses and refuted against the ``witness_reference``.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling's
    class exists because a read-only heap input may carry a fractional permission
    an impl overwrites. Lean and Velvet are referentially transparent: ``a``,
    ``n``, ``p`` are immutable scalar values, this bundle declares no ``mut``
    binder, there is no heap and no aliasing — no read-only input to overwrite
    and no substitute probe to build. Not fabricated (per the porting map). The
    nagini surface itself already notes this class is vacuous (all inputs are
    scalar ints; the only full-permission object is the result the impl creates).
  * UNGROUNDED-ORACLE ECHO — N/A as a WRONG echo. The completeness clauses are
    grounded in ``rootsBelow`` (a fold over the actual inputs) and in the exact
    singleton; ``primeRoots`` is pinned only on its own branch. There is no
    answer-key a wrong impl could echo to skip the work — echoing the grounded
    root set IS the correct value, which the positive control does honestly.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-18199"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the single impl region and
# ---- is unique in Solution.lean; both facts asserted at load by _swap) ------

# The WHOLE frozen impl body (text strictly between -- impl-start / -- impl-end):
# the branch ladder computing `target`, then the backward copy loop. The
# structure-attacking rivals abandon the loop entirely and RETURN the target
# list directly (definitionally the same list gold copies out, so the spec view
# is untouched and only the executable shape differs).
_IMPL = (
    "    let target : List Int :=\n"
    "      if ¬ isPrime p then\n"
    "        rootsBelow p.toNat a n p\n"
    "      else\n"
    "        if a % p = 0 then\n"
    "          [(0 : Int)]\n"
    "        else\n"
    "          if ¬ isNthResidue a n p then\n"
    "            ([] : List Int)\n"
    "          else\n"
    "            primeRoots a n p\n"
    "    let mut result : List Int := []\n"
    "    let mut i := target.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ target.length\n"
    "      invariant result = target.drop i\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := target[i - 1]!\n"
    "      result := c :: result\n"
    "      i := i - 1\n"
    "    return result\n"
)
assert _BASE.count(_IMPL) == 1, "nthRoots impl region drifted from expected text"

# The two loop-body lines that bind `c` then prepend it. The positive control
# inlines `c` into the prepend — a data-flow reshape leaving `result`
# definitionally identical, so the frozen tactic script still closes.
_INNER = (
    "      let c := target[i - 1]!\n"
    "      result := c :: result\n"
)
assert _BASE.count(_INNER) == 1, "nthRoots loop-body anchor drifted"


def _impl(new_impl):
    """Full Solution.lean with ONLY the nthRoots impl body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- rival impl builder: a straight-line body computing `target` under the
# ---- given branch expressions and RETURNING it directly (no loop). The branch
# ---- ladder is the spec-faithful dispatch; only the per-branch VALUE is
# ---- perturbed by a rival, so `same_spec` holds and the obligation survives.
def _straightline(nonprime, zero):
    return (
        "    let target : List Int :=\n"
        "      if ¬ isPrime p then\n"
        f"        {nonprime}\n"
        "      else\n"
        "        if a % p = 0 then\n"
        f"          {zero}\n"
        "        else\n"
        "          if ¬ isNthResidue a n p then\n"
        "            ([] : List Int)\n"
        "          else\n"
        "            primeRoots a n p\n"
        "    return target\n"
    )


_GOLD_NP = "rootsBelow p.toNat a n p"
_GOLD_ZERO = "[(0 : Int)]"


# ---- rival impl builder #2: the same straight-line dispatch, but behind a guard
# ---- on the SMALLEST ADMITTED MODULUS. `p = 2` is the low edge of the declared
# ---- modulus domain (`require p ≥ 2`); a rival that answers that edge with its
# ---- own value is INSIDE the domain, so nothing but the ensures clauses can
# ---- reject it. This is the shape a partial-domain rival takes on this carrier:
# ---- byte-identical to the faithful dispatch everywhere except at one admitted
# ---- input, and that input is load-bearing (mapping.md §3.6 — the modeled body
# ---- re-enters itself on the prime factors of the modulus, all of which are
# ---- ≥ 2, and `p = 2` is also a direct graded input).
def _edge_guarded(edge_value):
    return (
        "    let target : List Int :=\n"
        "      if p ≤ 2 then\n"
        f"        {edge_value}\n"
        "      else\n"
        "        if ¬ isPrime p then\n"
        f"          {_GOLD_NP}\n"
        "        else\n"
        "          if a % p = 0 then\n"
        f"            {_GOLD_ZERO}\n"
        "          else\n"
        "            if ¬ isNthResidue a n p then\n"
        "              ([] : List Int)\n"
        "            else\n"
        "              primeRoots a n p\n"
        "    return target\n"
    )


# ---- THE WITNESS REFERENCE (added by audit a6; see the carrier note above).
# ---- A CORRECT, loop-free impl of the frozen spec: the same branch ladder gold
# ---- computes, returned directly instead of copied out by the backward loop. It
# ---- is the frozen VALUE in a straight-line SHAPE, which is exactly the subject
# ---- every witness here needs — `triple_pure` fires on it (measured: zero
# ---- `unused simp argument` warnings, against two on gold), so the refutation
# ---- lands on the per-branch value rather than on the loop-vs-pure shape.
# ----
# ---- The frozen tactic script cannot close it (it opens by re-establishing a
# ---- loop invariant that no longer exists), so the obligation is REPROVEN from
# ---- scratch: `loom_solve` discharges all four completeness clauses outright
# ---- and leaves only the soundness goal, closed by the same case analysis and
# ---- the same three frozen lemmas gold's final branch uses. `same_spec` holds
# ---- (only the impl region and the tactic body move, both elided by the spec
# ---- view), so the gate re-verifies it as an impl of the frozen contract before
# ---- accepting it as a witness subject.
_REF_PROOF = (
    "  loom_solve\n"
    "  intro k hk\n"
    "  by_cases hpr : isPrime p\n"
    "  · simp only [hpr, not_true, if_false] at hk ⊢\n"
    "    by_cases hz : a % p = 0\n"
    "    · simp only [hz, if_true] at hk ⊢\n"
    "      exact zero_singleton_sound a n p k require_2 require_3 hz hk\n"
    "    · simp only [hz, if_false] at hk ⊢\n"
    "      by_cases hres : isNthResidue a n p\n"
    "      · simp only [hres, not_true, if_false] at hk ⊢\n"
    "        have hpos : a > 0 := by\n"
    "          rcases lt_or_eq_of_le require_4 with h | h\n"
    "          · exact h\n"
    "          · exfalso; apply hz; rw [← h]; simp\n"
    "        obtain ⟨h0, h1, h2⟩ :=\n"
    "          primeRoots_sound a n p k hpos require_3 require_2 hz hk\n"
    "        exact ⟨h0, h1, h2⟩\n"
    "      · simp only [hres, not_false_iff, if_true] at hk\n"
    "        simp at hk\n"
    "  · simp only [hpr, not_false_iff, if_true] at hk ⊢\n"
    "    exact rootsBelow_sound p.toNat a n p k hk\n"
)



# ---- admissibility: a CONCRETE LITERAL input proven to satisfy every
# ---- `require`. The opaque `isPrime` does not decide at a literal, but the
# ---- precondition is a DISJUNCTION and its `compositeValidated` arm is a
# ---- decidable enumeration, so the composite leg is constructible after all:
# ---- `(a,n,p) = (1,3,8)` discharges it by `rfl` on each component. This is
# ---- added inside the `prove_correct` tactic body (which the spec view elides),
# ---- so `same_spec` holds and the frozen obligation still has to close after it.
_ADMISS_LITERAL = (
    "  have hadmiss_literal :\n"
    "      (1 : Int) ≥ 0 ∧ (3 : Int) > 2 ∧ (8 : Int) ≥ 2 ∧\n"
    "        (isPrime 8 ∨ compositeValidated 1 3 8) :=\n"
    "    ⟨by omega, by omega, by omega,\n"
    "     Or.inr (Or.inr (Or.inl ⟨rfl, rfl, rfl⟩))⟩\n"
)

_PROVE_HEADER = "prove_correct nthRoots by\n"


def _prepend_tactic(extra):
    """Frozen file with `extra` inserted at the head of the tactic body."""
    return _swap(_BASE, _PROVE_HEADER, _PROVE_HEADER + extra)


# The frozen tactic body, replaced wholesale by the reproven `_REF_PROOF` above
# (the frozen script opens by re-establishing a loop invariant the loop-free
# reference does not have, so it cannot be reused).
_FROZEN_PROOF = _BASE[_BASE.index(_PROVE_HEADER) + len(_PROVE_HEADER):]

_WITNESS_REFERENCE = _swap(
    _swap(_BASE, _IMPL, _straightline(_GOLD_NP, _GOLD_ZERO)),
    _FROZEN_PROOF, _REF_PROOF)


# ---- witness scaffolding. The spec is a `method` contract over a noncomputable
# ---- post-image, so a witness refutes the method's Hoare triple DIRECTLY at a
# ---- point described by hypothesis. `triple_pure` reduces the straight-line
# ---- `do` block (a single `pure`) to `pre ≤ post (return-value)`; the
# ---- reduction lemmas all come from the frozen `Velvet.Std` import. Checked in
# ---- a file whose `prove_correct` block has been stripped.
_PRE = "(a ≥ 0 ∧ n > 2 ∧ p ≥ 2 ∧ (isPrime p ∨ compositeValidated a n p))"
_POST = (
    "(fun out =>\n"
    "          (∀ k : Nat, k < out.length → isRoot out[k]! n p a)\n"
    "          ∧ ((¬ isPrime p ∧ compositeValidated a n p) → out = rootsBelow p.toNat a n p)\n"
    "          ∧ ((isPrime p ∧ a % p ≠ 0 ∧ isNthResidue a n p) → out = primeRoots a n p)\n"
    "          ∧ ((isPrime p ∧ a % p ≠ 0 ∧ ¬ isNthResidue a n p) → out = [])\n"
    "          ∧ ((isPrime p ∧ a % p = 0) → out.length = 1 ∧ out[0]! = 0))"
)


def _witness(binders, body):
    return (
        f"example {binders} :\n"
        f"    ¬ triple (l := Prop)\n"
        f"        {_PRE}\n"
        f"        (nthRoots a n p)\n"
        f"        {_POST} := by\n"
        f"  unfold nthRoots\n"
        f"  simp only [triple_pure, le_Prop_eq]\n"
        f"  intro hcon\n"
        f"{body}"
    )


# C-zero rivals live on the prime zero-target sub-domain (isPrime p, a % p = 0).
_ZERO_BINDERS = ("(a n p : Int) (ha : a ≥ 0) (hn : n > 2) (hpp : p ≥ 2) "
                 "(hp : isPrime p) (hz : a % p = 0)")
# C-comp rivals live on the validated non-prime sub-domain with a NON-EMPTY root
# set (¬ isPrime p, compositeValidated, rootsBelow ≠ []). The non-emptiness
# hypothesis is exactly the sub-domain where a completeness defect is observable.
_COMP_BINDERS = ("(a n p : Int) (ha : a ≥ 0) (hn : n > 2) (hpp : p ≥ 2) "
                 "(hnp : ¬ isPrime p) (hcv : compositeValidated a n p) "
                 "(hne : rootsBelow p.toNat a n p ≠ [])")

_W_DROPZERO = _witness(_ZERO_BINDERS, (
    "  obtain ⟨-, -, -, -, hzero⟩ := hcon ⟨ha, hn, hpp, Or.inl hp⟩\n"
    "  have hout := hzero ⟨hp, hz⟩\n"
    "  rw [if_neg (by simp [hp]), if_pos hz] at hout\n"
    "  simp at hout\n"))

_W_TWOZEROS = _witness(_ZERO_BINDERS, (
    "  obtain ⟨-, -, -, -, hzero⟩ := hcon ⟨ha, hn, hpp, Or.inl hp⟩\n"
    "  have hout := hzero ⟨hp, hz⟩\n"
    "  rw [if_neg (by simp [hp]), if_pos hz] at hout\n"
    "  have := hout.1\n"
    "  simp at this\n"))

_W_DECLINE = _witness(_COMP_BINDERS, (
    "  obtain ⟨-, hcomp, -, -, -⟩ := hcon ⟨ha, hn, hpp, Or.inr hcv⟩\n"
    "  have hout := hcomp ⟨hnp, hcv⟩\n"
    "  rw [if_pos hnp] at hout\n"
    "  exact hne hout.symm\n"))

_W_DROPLAST = _witness(_COMP_BINDERS, (
    "  obtain ⟨-, hcomp, -, -, -⟩ := hcon ⟨ha, hn, hpp, Or.inr hcv⟩\n"
    "  have hout := hcomp ⟨hnp, hcv⟩\n"
    "  rw [if_pos hnp] at hout\n"
    "  have hlen := congrArg List.length hout\n"
    "  rw [List.length_dropLast] at hlen\n"
    "  have : (rootsBelow p.toNat a n p).length ≠ 0 := by\n"
    "    simp [List.length_eq_zero_iff, hne]\n"
    "  omega\n"))

_W_DUP = _witness(_COMP_BINDERS, (
    "  obtain ⟨-, hcomp, -, -, -⟩ := hcon ⟨ha, hn, hpp, Or.inr hcv⟩\n"
    "  have hout := hcomp ⟨hnp, hcv⟩\n"
    "  rw [if_pos hnp] at hout\n"
    "  have hlen := congrArg List.length hout\n"
    "  rw [List.length_append, List.length_take] at hlen\n"
    "  have : (rootsBelow p.toNat a n p).length ≠ 0 := by\n"
    "    simp [List.length_eq_zero_iff, hne]\n"
    "  omega\n"))

# The zero-target clause's SECOND conjunct (`out[0]! = 0`). The two shipped
# C-zero rivals both perturb the LENGTH, so the value conjunct was never the
# reason for any rejection; this witness selects `.2` instead of `.1`.
_W_ZEROVAL = _witness(_ZERO_BINDERS, (
    "  obtain ⟨-, -, -, -, hzero⟩ := hcon ⟨ha, hn, hpp, Or.inl hp⟩\n"
    "  have hout := hzero ⟨hp, hz⟩\n"
    "  rw [if_neg (by simp [hp]), if_pos hz] at hout\n"
    "  have := hout.2\n"
    "  simp at this\n"))

# ORDER on the composite clause. Conditioned on the root set not being a
# palindrome, which is exactly the sub-domain where reversal is observable; every
# other C-comp rival perturbs the LENGTH, so none of them could attest that the
# clause pins a SEQUENCE rather than a multiset.
_REV_BINDERS = ("(a n p : Int) (ha : a ≥ 0) (hn : n > 2) (hpp : p ≥ 2) "
                "(hnp : ¬ isPrime p) (hcv : compositeValidated a n p) "
                "(hrev : (rootsBelow p.toNat a n p).reverse "
                "≠ rootsBelow p.toNat a n p)")

_W_REVERSE = _witness(_REV_BINDERS, (
    "  obtain ⟨-, hcomp, -, -, -⟩ := hcon ⟨ha, hn, hpp, Or.inr hcv⟩\n"
    "  have hout := hcomp ⟨hnp, hcv⟩\n"
    "  rw [if_pos hnp] at hout\n"
    "  exact hrev hout\n"))

# The LOW EDGE of the declared modulus domain. `p ≥ 2` admits `p = 2`, so a rival
# is answerable there: this binder group is the prime zero-target sub-domain
# INTERSECTED with `p ≤ 2`, i.e. exactly the smallest admitted modulus. Jointly
# satisfiable: `p ≥ 2 ∧ p ≤ 2` forces `p = 2`, `isPrime` is opaque (nothing
# refutes `isPrime 2`), and `a % p = 0` holds at `a = 0`.
_EDGE_BINDERS = ("(a n p : Int) (ha : a ≥ 0) (hn : n > 2) (hpp : p ≥ 2) "
                 "(hle : p ≤ 2) (hp : isPrime p) (hz : a % p = 0)")

# REPAIRED BY AUDIT a7 — the previous body opened with `rw [if_pos hle]`, a
# rewrite naming the RIVAL'S OWN GUARD (`if p ≤ 2 then …`). That guard does not
# occur in the reference's branch ladder, so the reference-side build failed with
# `rewrite failed: did not find if p ≤ 2 then ?m else ?m` — an error about which
# BRANCHES the subject has, not about what the witness CLAIMS. Measured with the
# forgery pair (attack B′): changing the closing step to a deliberate type error
# left the reference-side error BYTE-IDENTICAL, so that exit code carried no
# information about the claim and the case was hollow — a witness asserting the
# reference is CORRECT at the edge would have been recorded `rejected` too.
#
# The repair drives the reduction from the HYPOTHESES instead of from a rival
# guard: `simp [hle, hp, hz]` resolves whichever ladder the subject has (`p ≤ 2`
# is true under `hle`; `isPrime p` under `hp`; `a % p = 0` under `hz`), so both
# subjects reduce and the residual goal is the per-branch VALUE. Type-revealed on
# each side: RIVAL `0 = 1 ∧ [][0]! = 0` (the FALSE claim — its edge branch is
# empty), REFERENCE `True ∧ [0][0]! = 0` (simp PROVED the length conjunct — the
# reference answers the edge with the correct singleton). The error text tracks
# the claim, so the exit codes now carry information about it.
_W_DOMAIN = _witness(_EDGE_BINDERS, (
    "  obtain ⟨-, -, -, -, hzero⟩ := hcon ⟨ha, hn, hpp, Or.inl hp⟩\n"
    "  have hout := hzero ⟨hp, hz⟩\n"
    "  simp [hle, hp, hz] at hout\n"))


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else the postcondition is SPEC-TOO-STRONG. The
    # intermediate `let c := target[i-1]!` binding is inlined into the prepend:
    # the accumulated `result` is DEFINITIONALLY identical, so `loom_solve`
    # leaves the same single loop-body goal and the frozen tactic script
    # (drop_step + injection …) discharges it unchanged. No new lemma, obligation
    # statement byte-identical. Ports the nagini pos-reshape-local ARGUMENT (bind
    # the copied element differently; keep loop DIRECTION and every invariant) to
    # this carrier's backward fold.
    # =====================================================================
    {
        "id": "pos-reshape-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _INNER,
            "      result := target[i - 1]! :: result\n"),
        "rationale": "Inlining the per-element copy binding into the prepend "
                     "leaves the accumulated `result` definitionally identical, "
                     "so the soundness clause and all four completeness clauses "
                     "still discharge and the frozen proof closes without change. "
                     "A correct reshape that failed to verify would mean the "
                     "postcondition over-constrains the impl's data-flow shape "
                     "(SPEC-TOO-STRONG). Also the cheapest-honest grounded "
                     "control: copying the grounded root set IS the correct value.",
    },

    # =====================================================================
    # POSITIVE CONTROL #2 (soundness) — the WITNESS REFERENCE, shipped as a case
    # in its own right. Two independent jobs:
    #
    #  (a) It is the strong correct reshape `pos-reshape-inline` is not. That one
    #      inlines a `let`, which is DEFINITIONALLY equal, so the frozen tactic
    #      script closes it verbatim and it reproves nothing. This one abandons
    #      the backward copy loop ENTIRELY (`return target`), so the frozen
    #      script cannot close it at all and the obligation is REPROVEN from
    #      scratch. A faithful correct impl the spec rejected here would be a
    #      SPEC-TOO-STRONG hole on control-flow shape; it verifies, so there is
    #      none.
    #  (b) It is the subject every reject case's witness is refuted against
    #      (`witness_reference`, see the carrier note). Shipping it as an
    #      `expect="verify"` case is what puts "this impl is CORRECT" under the
    #      gate rather than under this comment — the gate re-verifies it, so
    #      loop-freeness is demonstrably not what any rival is rejected for.
    # =====================================================================
    {
        "id": "pos-loopfree-reproven",
        "kind": "soundness",
        "expect": "verify",
        "module": _WITNESS_REFERENCE,
        "rationale": "The frozen branch ladder returned DIRECTLY instead of "
                     "copied out element-by-element by the backward `while` "
                     "loop. Behaviourally identical (the loop's postcondition is "
                     "`result = target.drop 0`) but structurally a different "
                     "program, and NOT definitionally equal in a way the frozen "
                     "tactic script can exploit: that script opens by "
                     "re-establishing a loop invariant this impl has no loop for, "
                     "so the obligation is reproven from scratch — `loom_solve` "
                     "discharges all four completeness clauses outright and the "
                     "remaining soundness goal is closed by the same case "
                     "analysis over the same three frozen lemmas "
                     "(`zero_singleton_sound`, `primeRoots_sound`, "
                     "`rootsBelow_sound`). MUST verify: a correct impl rejected "
                     "for its control-flow shape would be SPEC-TOO-STRONG. Also "
                     "the load-bearing precondition of the reject lane — this is "
                     "the `witness_reference` all seven rivals' witnesses are "
                     "refuted against, and the gate accepting it as a verifying "
                     "impl of the frozen spec is what makes those refutations "
                     "attributable to the per-branch VALUE rather than to the "
                     "loop-vs-pure shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. Every `require` is satisfiable by an F2P/issue
    # input, and on this opaque carrier no concrete literal is provably
    # `isPrime`, so the nagini "assert the precondition for a concrete input"
    # probe is not constructible. Re-aimed at the residual admissibility risk:
    # the FIVE post clauses (four implications with overlapping guards) being
    # JOINTLY UNSATISFIABLE at some reachable input — a spec no faithful impl can
    # meet reads exactly like one every impl meets. The frozen impl discharging
    # all five IS the witness. module = _BASE ⇒ same_spec trivially, obligation
    # intact; MUST verify, else SPEC-UNSATISFIABLE / PRECOND-TOO-STRONG.
    # =====================================================================
    {
        "id": "admiss-joint-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        # module = _BASE + a proof-body `have` exhibiting a CONCRETE LITERAL
        # input that satisfies every `require`. This is the nagini
        # admiss-fshape probe, which an earlier reading of this carrier recorded
        # as unconstructible because `isPrime` is opaque: true of the prime leg,
        # but the precondition is a DISJUNCTION whose `compositeValidated` arm is
        # a decidable enumeration, so the composite leg lands at a literal.
        # LOAD-BEARING, negative-control checked: the same term with the
        # non-enumerated, non-squarefree triple (1,3,9) fails to elaborate
        # (`rfl ... expected to have type 9 = 8`), so the `have` is not a
        # tautology that any triple would satisfy.
        "module": _prepend_tactic(_ADMISS_LITERAL),
        "rationale": "PASS SOURCE = joint satisfiability of all five post clauses "
                     "under the precondition. The `require` admits a prime "
                     "modulus and a validated composite one, and the soundness "
                     "clause co-holds with each completeness implication on its "
                     "own guarded sub-domain (the guards `¬isPrime`, `isPrime ∧ "
                     "a%p=0`, `isPrime ∧ a%p≠0 ∧ (¬)residue` are pairwise "
                     "disjoint, so no two equalities conflict). The gold impl "
                     "discharging all five is the admissibility witness; else the "
                     "spec is unsatisfiable and would be a false pass everywhere. "
                     "STRENGTHENED beyond joint satisfiability: the proof body "
                     "also carries a `have` exhibiting the CONCRETE LITERAL input "
                     "(a,n,p) = (1,3,8) — an enumerated validated composite "
                     "triple, one of the shapes the failing test drives — proven "
                     "to satisfy all four `require` clauses. So the precondition "
                     "is shown non-vacuous at a real point, not merely "
                     "consistent; PRECOND-TOO-STRONG would surface as this term "
                     "failing to elaborate.",
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected, each with a machine-checked refutation witness conditioned on the
    # carrier at the sub-domain it abuses, and the refinement argument that its
    # faithful real counterpart would NOT resolve the failing test / issue.
    # =====================================================================
    {
        "id": "drop-zero-root",
        "kind": "uniqueness",
        "expect": "reject",
        # Prime zero-target case returns [] instead of [0]: the on-carrier
        # analogue of the pre-patch dispatch that ran the residue check first and
        # never special-cased a%p==0, dropping the x=0 root.
        "module": _impl(_straightline(_GOLD_NP, "([] : List Int)")),
        "refinement": "This is the on-carrier analogue of the EXACT pre-patch "
                      "behaviour: for a prime modulus with the target divisible "
                      "by it, the zero residue is dropped (the result is empty). "
                      "That is precisely the defect the issue reports — the "
                      "documented example (a prime modulus, target a square of "
                      "it, exponent five) is missing its zero root. A patch of "
                      "this shape IS the pre-patch code; the issue's own example "
                      "still fails, so it would NOT resolve.",
        "rationale": "REJECT from (C-zero) `isPrime p ∧ a%p=0 → out.length = 1 ∧ "
                     "out[0]! = 0`. Returning [] is sound VACUOUSLY (no element to "
                     "check) but has length 0 ≠ 1, so the exact-singleton clause "
                     "is unprovable. Soundness alone would admit it; completeness "
                     "is what rejects it. Refuted by conditioning on "
                     "`isPrime p ∧ a % p = 0` — the prime zero-target sub-domain "
                     "the fix exists for.",
        "witness": _W_DROPZERO,
        "witness_reference": _WITNESS_REFERENCE,
    },
    {
        "id": "two-zeros-prime",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-keep on the same clause: return [0, 0]. Both entries are genuine
        # roots, so soundness holds — but the singleton clause pins length to 1.
        "module": _impl(_straightline(_GOLD_NP, "[(0 : Int), (0 : Int)]")),
        "refinement": "A faithful patch that emitted the zero root twice (failing "
                      "to collapse its multiplicity) would report a non-existent "
                      "second solution. Over a prime field the equation with a "
                      "zero target has the UNIQUE root zero (no zero divisors); "
                      "the issue and gold pin exactly the single zero. A "
                      "two-element result is wrong and would not match the "
                      "expected single-root output, so it would NOT resolve.",
        "rationale": "REJECT from (C-zero) `… → out.length = 1 ∧ out[0]! = 0`. "
                     "Both entries of [0,0] are genuine roots so SOUNDNESS holds, "
                     "but length 2 ≠ 1, so the exact-singleton clause is "
                     "unprovable. This is the OVER-keep side of the zero-target "
                     "gap (contrast drop-zero-root's UNDER-keep), pinning the "
                     "result to the EXACT singleton not merely 'contains 0'. "
                     "Refuted at the same conditioning point via the length "
                     "conjunct.",
        "witness": _W_TWOZEROS,
        "witness_reference": _WITNESS_REFERENCE,
    },
    {
        "id": "decline-composite",
        "kind": "uniqueness",
        "expect": "reject",
        # Non-prime modulus DECLINED (returns []): the on-carrier analogue of the
        # pre-patch `raise NotImplementedError` for composite p. Empty is sound
        # vacuously but ≠ the complete root set whenever it is non-empty.
        "module": _impl(_straightline("([] : List Int)", _GOLD_ZERO)),
        "refinement": "This is the on-carrier analogue of the pre-patch behaviour "
                      "that DECLINED a non-prime modulus (raised instead of "
                      "solving). The sole FAIL_TO_PASS reaches the solver ONLY "
                      "with composite moduli (the modular equations over 8 and 9 "
                      "in the failing test); a patch that declines composite "
                      "moduli returns nothing there and FAILS the F2P. It would "
                      "NOT resolve.",
        "rationale": "REJECT from (C-comp) `¬isPrime p ∧ compositeValidated → out "
                     "= rootsBelow p.toNat a n p`. Returning [] is sound "
                     "vacuously but ≠ the complete grounded root set whenever "
                     "that set is non-empty (it is, on the F2P composite shapes), "
                     "so the composite completeness clause is unprovable. Refuted "
                     "by conditioning on `¬ isPrime p ∧ compositeValidated a n p "
                     "∧ rootsBelow … ≠ []`.",
        "witness": _W_DECLINE,
        "witness_reference": _WITNESS_REFERENCE,
    },
    {
        "id": "drop-last-composite-root",
        "kind": "uniqueness",
        "expect": "reject",
        # Non-prime branch drops the LAST assembled root (`.dropLast`). Every
        # returned value is still a genuine root, so soundness holds — the
        # canonical impl a soundness-only spec would wrongly admit.
        "module": _impl(_straightline(
            "(rootsBelow p.toNat a n p).dropLast", _GOLD_ZERO)),
        "refinement": "A faithful patch whose composite recombination has an "
                      "off-by-one (drops the final assembled root) returns a "
                      "STRICT SUBSET of the true root set. On the failing test's "
                      "composite equations the expected solution set then loses a "
                      "member, so the test's asserted image set is wrong and the "
                      "F2P fails. Every value it DOES return is a real root, so a "
                      "soundness-only spec would wrongly accept it — the canonical "
                      "verify-but-not-resolve rival. It would NOT resolve.",
        "rationale": "REJECT from (C-comp) `out = rootsBelow p.toNat a n p`. "
                     "`.dropLast` has length one less than the complete fold, so "
                     "the equality fails whenever the root set is non-empty. "
                     "SOUNDNESS still holds (every kept element is a root — a "
                     "sublist of the grounded fold), so this isolates completeness "
                     "as the load-bearing clause. Refuted by conditioning on a "
                     "non-empty root set (`rootsBelow … ≠ []`) via the length.",
        "witness": _W_DROPLAST,
        "witness_reference": _WITNESS_REFERENCE,
    },
    {
        "id": "duplicate-composite-root",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-keep on the composite clause: append the first root a SECOND time.
        # The extra entry is itself a genuine root, so soundness holds — but the
        # result is strictly longer than the complete fold.
        "module": _impl(_straightline(
            "(rootsBelow p.toNat a n p) ++ (rootsBelow p.toNat a n p).take 1",
            _GOLD_ZERO)),
        "refinement": "A faithful patch that double-counts a root (a "
                      "recombination revisiting a residue) returns a list with a "
                      "duplicate. The real solver returns a de-duplicated set and "
                      "the failing test compares the exact solution set; a "
                      "duplicated entry yields the wrong image and the F2P fails. "
                      "The extra entry is itself a real root, so soundness holds "
                      "— only the exact-sequence completeness clause rejects it. "
                      "It would NOT resolve.",
        "rationale": "REJECT from (C-comp) `out = rootsBelow p.toNat a n p`. "
                     "Appending the first element again makes the result strictly "
                     "longer than the complete fold whenever it is non-empty, so "
                     "the equality fails. This is the OVER-keep side of the "
                     "composite gap (contrast drop-last's UNDER-keep): soundness "
                     "holds, the exact sequence does not. Refuted by conditioning "
                     "on a non-empty root set via the length.",
        "witness": _W_DUP,
        "witness_reference": _WITNESS_REFERENCE,
    },

    # =====================================================================
    # ADDED BY AUDIT. The five rivals above all perturb a LENGTH: three on
    # (C-comp) and two on (C-zero). So two things the spec says were never the
    # reason for any rejection, and a spec that dropped them would have passed
    # this battery unchanged. Both rivals below were confirmed to fail the value
    # screen (the correct straight-line reshape), so each rejection is
    # attributable to the clause named, not to the loop-vs-pure shape.
    # =====================================================================
    {
        "id": "zero-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Prime zero-target returns the ONE-element list [1] instead of [0]:
        # length 1 is correct, so the length conjunct the other two C-zero rivals
        # break is SATISFIED here and only the VALUE conjunct can reject.
        "module": _impl(_straightline(_GOLD_NP, "[(1 : Int)]")),
        "refinement": "A patch that special-cased the divisible-target branch "
                      "but emitted the wrong residue there reports a single "
                      "solution that is not a solution. The issue's own example "
                      "asks for the zero residue specifically; a one-element "
                      "answer holding the wrong value contradicts it, and the "
                      "returned value is not even a root of the equation (over a "
                      "modulus exceeding the target's remainder, one raised to "
                      "any power is one, not zero). It would NOT resolve.",
        "rationale": "REJECT from the SECOND conjunct of (C-zero) `… → "
                     "out.length = 1 ∧ out[0]! = 0`. This rival's result has "
                     "length exactly 1, so the conjunct that rejects "
                     "drop-zero-root and two-zeros-prime HOLDS; the only "
                     "remaining source of rejection is `out[0]! = 0`, which [1] "
                     "violates. Without this case the value half of the "
                     "exact-singleton clause is unattacked — a spec pinning only "
                     "`out.length = 1` would pass the rest of this battery. "
                     "Refuted by selecting `.2` of the clause at the same "
                     "prime-zero conditioning point.",
        "witness": _W_ZEROVAL,
        "witness_reference": _WITNESS_REFERENCE,
    },
    {
        "id": "reverse-composite-order",
        "kind": "uniqueness",
        "expect": "reject",
        # The composite branch returns the complete root set REVERSED. Same
        # elements, same multiset, same LENGTH — so every length-based refutation
        # above is unavailable and only the exact-SEQUENCE reading can reject.
        "module": _impl(_straightline(
            "(rootsBelow p.toNat a n p).reverse", _GOLD_ZERO)),
        "refinement": "A faithful patch whose composite recombination assembles "
                      "the residues in descending order returns the right SET in "
                      "the wrong order. The real solver's result is ascending and "
                      "the failing test compares against an ordered literal, so "
                      "a reversed multi-root answer mismatches there. Soundness "
                      "holds (every entry is a genuine root) and so does every "
                      "cardinality property, which is exactly why this rival is "
                      "invisible to the other five. It would NOT resolve.",
        "rationale": "REJECT from (C-comp) `out = rootsBelow p.toNat a n p` read "
                     "as an EXACT SEQUENCE. Reversal preserves length and "
                     "membership, so soundness, both cardinality directions, and "
                     "every length-based refutation are satisfied; only the "
                     "list-equality ordering can reject it. This is what "
                     "certifies (C-comp) pins a sequence rather than a multiset — "
                     "the ascending order the grounded fold builds is part of the "
                     "claim. Refuted by conditioning on the root set not being "
                     "its own reverse (`(rootsBelow …).reverse ≠ rootsBelow …`), "
                     "the sub-domain where reversal is observable at all.",
        "witness": _W_REVERSE,
        "witness_reference": _WITNESS_REFERENCE,
    },

    # =====================================================================
    # ADDED BY AUDIT. Every rival above perturbs a per-branch VALUE, so all of
    # them are refutable no matter how NARROW the declared input domain is. None
    # of them can see the other axis a same-spec rival can move on: which inputs
    # the spec speaks about at all. A rival that is faithful on every input the
    # Requires admits, and free on one it does not, verifies — and if the real
    # callee's own recursion re-enters the model at that omitted input, the free
    # value flows back into a graded result. The modeled tail re-enters itself at
    # the prime factors of the modulus (mapping.md §3.6, refinement.md A2b), so
    # the smallest admitted modulus is the input this axis turns on.
    # =====================================================================
    {
        "id": "poison-domain-edge",
        "kind": "uniqueness",
        "expect": "reject",
        # Faithful everywhere except at the SMALLEST ADMITTED MODULUS, where it
        # returns []. Every branch value below the guard is gold's, so the four
        # value-perturbing axes are all clean and only the DOMAIN's low edge is
        # in play: this rival verifies against any spec whose modulus Requires
        # excludes p = 2, and is rejected by one that admits it.
        "module": _impl(_edge_guarded("([] : List Int)")),
        "refinement": "The real non-prime solver assembles the root set for a "
                      "composite modulus out of the root sets over the PRIME "
                      "FACTORS of that modulus, re-entering the same body at the "
                      "same target and exponent with the smaller modulus. Every "
                      "even composite modulus therefore reduces through the "
                      "smallest one, and the failing test's own moduli (eight and "
                      "nine, both non-squarefree) are reached that way — the "
                      "smallest modulus is also supplied directly as a top-level "
                      "call while grading. A patch of this shape answers those "
                      "sub-calls with no roots, so the recombination loses whole "
                      "residue classes and the failing test's asserted solution "
                      "sets come out wrong. It would NOT resolve, while being "
                      "byte-identical to a faithful patch on every other input.",
        "rationale": "REJECT from (C-zero) `isPrime p ∧ a%p=0 → out.length = 1 ∧ "
                     "out[0]! = 0`, EVALUATED AT THE LOW EDGE of the modulus "
                     "domain. This case exists to keep that edge inside the "
                     "domain: `require p ≥ 2` (not `p > 2`) is what makes the "
                     "guarded branch reachable under the precondition, and hence "
                     "constrained by the ensures clauses. Under a modulus bound "
                     "that excluded the edge this same rival VERIFIES — the guard "
                     "is then provably dead and the postconditions say nothing "
                     "about it — so this is the one case in the battery whose "
                     "verdict depends on the DECLARED DOMAIN rather than on a "
                     "postcondition's shape. Refuted by conditioning on the "
                     "sub-domain `p ≥ 2 ∧ p ≤ 2 ∧ isPrime p ∧ a % p = 0`, the "
                     "smallest admitted modulus with a divisible target.",
        "witness": _W_DOMAIN,
        "witness_reference": _WITNESS_REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING.
#
# The nagini sibling ships 7 SPEC cases (1 soundness positive, 1 admissibility,
# 5 uniqueness rivals) plus 4 AXIOM_TESTS. This velvet bundle models the SAME
# purely-functional core — a single method `nthRoots` over the same grounded
# oracle surface (`isRoot`/`powerMod`, the deep fold `rootsBelow`, the
# `primeRoots` A-reference, `compositeValidated`) — so nearly every nagini case
# has a faithful counterpart. Every sibling case is accounted for below.
#
#   nagini case                   -> here
#   -----------------------------------------------------------------------
#   pos-reshape-local             -> pos-reshape-inline          PORTED
#   admiss-fshape                 -> admiss-joint-satisfiable    PORTED+RE-AIMED
#                                    (the concrete-literal probe DOES land here,
#                                     via the decidable composite arm; see below)
#   drop-zero-root                -> drop-zero-root              PORTED
#   decline-composite             -> decline-composite          PORTED
#   drop-last-composite-root      -> drop-last-composite-root    PORTED
#   duplicate-composite-root      -> duplicate-composite-root    PORTED
#   two-zeros-prime               -> two-zeros-prime             PORTED
#   ax-sound-power_mod            -> (none)                      G-AX's job
#   ax-sound-rootsets             -> (none)                      G-AX's job
#   ax-sound-residue              -> (none)                      G-AX's job
#   ax-contain-composite          -> (none)                      G-AX's job
#
# 5 uniqueness rivals PORTED verbatim in argument (each re-expressed as a
#   straight-line rival returning the perturbed branch value directly, refuted by
#   conditioning on its sub-domain). 1 soundness positive PORTED (backward-fold
#   data-flow reshape). 1 admissibility carrying BOTH the nagini concrete-input
#   probe (at the enumerated composite triple (1,3,8) — reachable because the
#   precondition's `compositeValidated` arm is a decidable enumeration even though
#   `isPrime` is opaque) AND the re-aimed joint-satisfiability argument.
#
# +2 ADDED BY AUDIT a5, both closing a gap the ported five share: every one of
#   them refutes via a LENGTH. `zero-wrong-value` attacks the value conjunct of
#   (C-zero) at length 1; `reverse-composite-order` attacks the sequence reading
#   of (C-comp) at equal length and equal membership.
#
# +1 ADDED BY AUDIT a6 — `pos-loopfree-reproven`, the loop-free correct impl,
#   shipped both as the strong correct reshape (the obligation reproven from
#   scratch, where `pos-reshape-inline` is only a definitional `let`-inlining the
#   frozen script closes verbatim) and as the `witness_reference` all seven reject
#   witnesses are now refuted against. a5 had established the same impl as an
#   off-artifact "value screen" and documented its results in prose; the gate
#   never ran it, so every rejection still RESTED on a gold-side exit code that
#   a5 itself had measured to be a control-flow shape mismatch. Moving it into
#   `witness_reference` puts the discriminating build under the gate.
#
# +1 ADDED BY AUDIT — `poison-domain-edge`, the only case in the battery whose
#   verdict turns on the DECLARED INPUT DOMAIN rather than on the shape of a
#   postcondition. All seven rivals above perturb a per-branch VALUE, so each of
#   them is refutable however narrow the Requires is; none of them can move on the
#   other axis a same-spec rival has, which is WHICH INPUTS the spec speaks about.
#   This one is gold's dispatch verbatim behind a guard on the smallest admitted
#   modulus, and it VERIFIES against any spec whose modulus bound excludes that
#   modulus (the guard is then provably dead code and no ensures clause reaches
#   it). It is a regression test for the closure argument in mapping.md §3.6 /
#   refinement.md A2b: the modeled body re-enters itself at the prime factors of
#   the modulus, so an omitted low edge is a hole a rival can hide a graded answer
#   in. RE-MEASURED BY AUDIT a7, and the a6 measurement above was WRONG about
#   the second build: the `rewrite` failure it recorded as "a genuine refutation"
#   was an error about the reference's BRANCH LADDER, not about the claim, and the
#   forgery pair proves it (flipping the closing step to a deliberate type error
#   reproduced the reference-side error BYTE-IDENTICALLY). The witness is repaired
#   to reduce from the hypotheses; re-measured, four builds: rival module exit 1;
#   witness exit 0 against the rival; exit 1 against `witness_reference` with the
#   claim-tracking type reveal RIVAL `0 = 1 ∧ [][0]! = 0` vs REFERENCE
#   `True ∧ [0][0]! = 0`; consistency probe leaves `False` unsolved.
#
# WITNESS ROUTE. Every reject rival is straight-line (the branch ladder then a
#   direct `return target`), so `unfold nthRoots; simp only [triple_pure,
#   le_Prop_eq]` reduces the Hoare triple to `pre ≤ post target`, and each
#   witness discharges the negation by feeding the precondition, selecting the
#   contradicted clause, rewriting the branch to the rival's value, and closing
#   with `simp`/`omega`. The carrier is opaque, so each witness CONDITIONS on it
#   (`isPrime p`, `¬ isPrime p ∧ compositeValidated …`, `a % p = 0`, and a
#   non-empty root set) rather than computing at a literal. All seven were SEEN to
#   discriminate — ELABORATE against the rival (exit 0), FAIL against the
#   `witness_reference` (exit 1, at the VALUE level), never against gold, whose
#   loop makes `triple_pure` inapplicable and whose exit code would therefore
#   attest to a shape mismatch — with jointly-satisfiable binders (the `: False`
#   consistency probe leaves `False` unsolved for all three binder groups, run
#   against the reference, the same subject the refutation is taken against).
#
# DIVERGENCE / NON-TERMINATION. `loom.semantics.termination` is "total" here, so
#   the verifier discharges a termination obligation and a diverging rival is
#   genuinely REJECTED — the shippable disposition per the F′ lane, not a known
#   hole. Two probes were built and run, and the class is nonetheless NOT
#   shippable on this bundle, for a witness reason that was measured rather than
#   assumed:
#     * Replacing the loop's `decreasing i` with the non-decreasing measure
#       `decreasing target.length` fails, exit 1, on the termination goal itself
#       (`case «decreasing_1: target.length»`).
#     * A truly diverging body (`i := i + 1`, so the counter grows away from the
#       exit test) also fails, exit 1.
#   But NEITHER can carry a `witness`, and that is what blocks the case rather
#   than any difficulty. A diverging rival must KEEP the loop, so its triple
#   elaborates to `forIn` exactly like gold's; the witness's opening `simp only
#   [triple_pure, le_Prop_eq]` cannot fire, and building the drop-zero witness
#   against the diverging rival confirms it — exit 1 with BOTH simp arguments
#   reported unused and the same `rcases failed: right✝ : w✝ is not an inductive
#   datatype`. So the witness would FAIL the half it must PASS (it must elaborate
#   against the rival), and the case would be recorded `witness-unproven`, not
#   `rejected`. Refuting non-termination needs a statement about the loop's
#   divergence, which `triple_pure` is the wrong instrument for and which no
#   value-level projection of this noncomputable post-image supplies. Recorded as
#   a WITNESS-EXPRESSIBILITY limit of this carrier, with the exit codes above as
#   the evidence; the termination obligation itself is live and demonstrably
#   rejects both rivals.
#
# VACUOUS — frame/permission-mutation. The nagini surface itself records this
#   class as N/A: all inputs are scalar ints, there is no read-only list/object
#   input held at a fractional permission, and the only full-permission object is
#   the result the impl creates. On Lean/Velvet the point is even sharper — the
#   backend is referentially transparent, `a`/`n`/`p` are immutable values, no
#   `mut` binder is declared, there is no heap and no aliasing. No substitute
#   probe fabricated.
#
# CLAUSE / BINDER COVERAGE.
#   * (S) soundness: DEFENDED by both positives; not independently ATTACKED by
#     design — every reject rival deliberately PRESERVES soundness (each returned
#     value is a genuine root) so that the rejection is attributable to
#     COMPLETENESS alone. That is the whole content of the "soundness is not
#     enough" argument: a soundness-only spec would admit drop-last / duplicate /
#     the empty list. An `expect="reject"` rival that violated soundness would
#     test a weaker property than the ones shipped.
#   * (C-comp) attacked by decline-composite (whole branch empty), drop-last
#     (strict subset), duplicate (strict superset) and reverse-composite-order
#     (equal length, equal multiset, wrong sequence) — four distinct sub-domains
#     of the same exact-sequence clause, the last of them the only one that
#     distinguishes a SEQUENCE claim from a multiset claim.
#   * (C-zero) attacked by drop-zero-root (UNDER-keep, length 0), two-zeros
#     (OVER-keep, length 2) — both sides of the cardinality — and
#     zero-wrong-value (length 1, wrong entry), which is the only rival that
#     reaches the clause's VALUE conjunct — and poison-domain-edge, which attacks
#     the same clause AT THE LOW EDGE of the modulus domain, the one point whose
#     coverage depends on the `require p ≥ 2` bound rather than on the clause.
#   * The Requires clause `p ≥ 2` is itself attacked, by poison-domain-edge: a
#     rival free at `p = 2` verifies under `p > 2` and is rejected under `p ≥ 2`,
#     so that bound is load-bearing and not decoration. (The three other require
#     clauses are DEFENDED by admiss-joint-satisfiable, which exhibits a concrete
#     admitted literal.)
#   * (C-res) `isPrime p ∧ a%p≠0 ∧ isNthResidue → out = primeRoots` and
#     (C-nores) `… ∧ ¬isNthResidue → out = []`: NOT independently attacked. These
#     encode the UNCHANGED prime-field path (the pre-patch already solved the
#     prime, non-zero case correctly); the fix only reordered the dispatch so the
#     composite and zero branches fire first. Critically, NO F2P/issue input
#     exercises a divergence on these branches — the failing test uses only
#     composite moduli and the issue example is the zero-target case — so a rival
#     mishandling only C-res/C-nores could still RESOLVE the F2P, which would make
#     its `refinement` argument (verify-does-not-imply-resolve) false. The nagini
#     sibling makes the SAME choice: it attacks only its C-comp and C-zero
#     clauses and leaves its prime-residue clause (C-prime) unattacked. These two
#     clauses are DEFENDED by both positives (the gold and the reshape verify
#     against all five). The coverage tool will flag them as unreferenced by any
#     reject rationale; that is the documented narrowing, not a hidden gap.
#     AUDIT-MEASURED, since the narrowing above is an argument and arguments are
#     what this note is for: two rivals aimed squarely at these clauses were
#     built and run — one returning [] on the prime non-zero RESIDUE branch
#     (contradicting C-res) and one returning the prime-field root set on the
#     NON-residue branch (contradicting C-nores). Neither verified, so the two
#     clauses are not dead weight and the spec is not too weak on them. They are
#     still not shipped as reject cases, and the reason is the one given above
#     and NOT that they cannot be refuted: their refinement argument would be
#     FALSE here, because no F2P/issue input diverges on those branches, so a
#     real patch mishandling only them could still resolve. Shipping them would
#     assert verify-does-not-imply-resolve where that implication is untested.
#     RE-CONFIRMED BY AUDIT a7 with fresh builds of both (`[]` on the residue
#     branch; `primeRoots` on the non-residue branch): each exits 1, so neither
#     clause is dead weight.
#   * AUDIT a7 SPEC-TOO-WEAK sweep (attack D), two further NEW rivals beyond the
#     two above, both aimed where the shipped eight do not reach. Neither
#     verified, so no spec hole:
#       - the zero-target check hoisted IN FRONT of the primality dispatch, so a
#         VALIDATED COMPOSITE modulus with a divisible target answers `[0]`
#         instead of the complete root set (contradicts C-comp on exactly the
#         enumerated `(0, 7, 100)` shape, whose root set has ten members). Exit 1.
#       - an out-of-range sentinel prepended to the composite root set, the only
#         rival that attacks (S) rather than a completeness clause. Exit 1, on the
#         soundness goal.
#   * AUDIT a7 SPEC-TOO-STRONG sweep (attack E), two NEW correct reshapes beyond
#     the two shipped positives, each with its obligation reproven from scratch.
#     Both VERIFY (exit 0), so the spec rejects no faithful impl on these axes:
#       - the branch polarity inverted throughout (`if isPrime p then …` with the
#         residue test also positive), so every `simp only` discharge in the
#         soundness proof fires on the opposite `if` side.
#       - the result assembled as `target ++ []`, which is PROVABLY but not
#         syntactically the frozen list, so `loom_solve` needs a `List.append_nil`
#         normalisation before the frozen case analysis applies.
#   * Binders `a`, `n`, `p` are all named across the reject witnesses and varied
#     in the sub-domain each conditions on (prime vs non-prime `p`; zero vs
#     non-zero `a % p`). Because the carrier is opaque the witnesses quantify over
#     a/n/p under hypotheses rather than at literals, so the coverage tool reads
#     them as unreadable and falls back to the by-name signal (all three named,
#     no gap); `pts` is not machine-computable for a conditioned witness, as on
#     the other opaque-carrier ports (django-11211, sympy-23534).
#
# AXIOM_TESTS: dropped. The four nagini axiom probes (power_mod soundness, the
#   prime/composite root-set A-references, the residue predicate, and the
#   composite-regime containment) are G-AX's job (axiom_check.py / mapping.md);
#   the G-PBT gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
