"""properties.py — G-PBT falsification battery for sympy__sympy-18199 (lean).

NOT a Lean file; a manifest the G-PBT gate parses. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside a ``-- impl-start`` / ``-- impl-end`` block — and, for
a case that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end``
— is changed, so ``markers.same_spec`` holds and every ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect="reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (two modeled functions over a purely-functional core):

  implementation_nthrootModComposite (a n m : ℤ) : List ℤ
    problem_spec_nthrootModComposite a n m result :=
      result = rootSetIn a n m                       -- (K-set) exact ordered set
      ∧ ∀ x ∈ result, isRootIn a n m x               -- (K-sound) each is a root

  implementation_nthrootMod (a n p : ℤ) : List ℤ    -- the public dispatch
    problem_spec_nthrootMod a n p result :=
      (isPrime p ∨ dispatchValidated → ∀ x ∈ result, isRootIn a n p x)  -- (S)
      ∧ (isPrime p → a % p = 0 → result = [0])       -- (C-zero) exact singleton
      ∧ (isPrime p → a % p ≠ 0 → result = primeRoots)-- (C-res)  unchanged path
      ∧ (¬ isPrime p → reportsRootsFor a n p result) -- (C-report) UNCONDITIONAL
      ∧ (¬ isPrime p → dispatchValidated → result = rootSetIn a n p)  -- (C-comp)

  (C-report) is the clause with NO regime guard: for every non-single-prime
  modulus the report enumerates canonical residues in strictly increasing order
  and has exactly AS MANY entries as the congruence has solutions — so the report
  is never a permutation, a repetition, or a proper part of the solutions, and it
  is empty exactly when the congruence has none: the report's
  LENGTH counts the solutions, hence in particular decides solvability. It is
  what makes the off-regime sub-domain constrained at all; (S) is guarded because
  the real routine does emit non-roots off the regime, so a spec that claimed
  soundness there would be FALSE of the real function.

  The task: report every in-range residue solving a modular power congruence.
  ``rootSetIn`` is the DEEP grounded model — the ordered, duplicate-free set of
  in-range residues whose ``n``-th power is congruent to the target over the
  actual modulus, a structural predicate, never an opaque answer key. The
  load-bearing content is COMPLETENESS: soundness (S / K-sound) alone is
  satisfied VACUOUSLY by the empty list and by any SUBSET of the true root set,
  so it never forces the whole set. The exact-set clause (K-set / C-comp) and the
  exact-singleton clause (C-zero) pin the result, and that is exactly where the
  two documented defects live — the dropped zero root over a single-prime modulus
  (the headline issue example) and the report for a non-single-prime modulus.

  Input binders of each spec predicate: ``a`` (target), ``n`` (exponent),
  ``m`` / ``p`` (modulus), plus ``result``. The reject witnesses vary the
  modulus binder across BOTH regimes (single-prime vs not, by conditioning on
  ``modulusIsPrime``) and the target binder across ALL THREE sub-domains the
  dispatch distinguishes — zero target under a single prime (``a % p = 0`` with
  ``modulusIsPrime p = true``), zero target under a NON-single-prime modulus (the
  guard OVERLAP, where a plausible near-miss loses the rest of the root set), and
  non-zero target under a single prime (the unchanged path) — plus the
  non-empty-root-set sub-domain ``rootSetIn … ≠ []`` of the helper. So neither the
  branch selector, nor the branch ORDER, nor the completeness target is probed at
  a single fixed point.

CARRIER NOTE — a PARTIALLY OPAQUE carrier, so the C-zero / C-comp reject lane is
stated by CONDITIONING, not by ``decide``:

  ``modulusIsPrime`` is an ``opaque`` decision procedure with no computing axiom,
  so no literal modulus decides which dispatch branch fires. The dispatch rivals
  (drop-zero / two-zeros / decline / the order rival / drop-unit-base) therefore
  state their refutation of
  ``problem_spec_nthrootMod`` at a point described by HYPOTHESIS
  (``modulusIsPrime p = true`` with ``a % p = 0``; or ``modulusIsPrime p ≠ true``
  with a validated modulus and a NON-EMPTY root set) — the disequality then holds
  exactly on the sub-domain where the rival diverges from the spec, a stronger
  statement than any single literal could make. The composite-helper rivals
  (drop-last / duplicate) refute ``problem_spec_nthrootModComposite`` directly;
  its impl is transparent, so a single ``rootSetIn … ≠ []`` hypothesis (the
  sub-domain where a length defect is observable) is all the conditioning they
  need. Each witness was machine-checked to ELABORATE against its rival and FAIL
  against the frozen solution, and each binder set is jointly satisfiable (the
  ``example … : False`` consistency probe leaves ``False`` unsolved), so no
  witness is a contradiction-forgery.

  The gold-side failure is, for every case, a refutation of the CLAIM and not of
  a value equation — and that distinction is load-bearing rather than cosmetic,
  because the battery originally got it wrong. See the WITNESSES block below: the
  earlier "name the rival's value in a ``have hval`` and rewrite" shape put a
  claim about the IMPL ALONE as the first tactic, so on the frozen solution the
  build died there and produced the byte-identical error whether the witness
  asserted ``¬ problem_spec …`` or its OPPOSITE. Gold's exit code was then
  independent of what was claimed. Every witness here now derives the spec clause
  FIRST, so the residual gold-side goal is the honest ``⊢ False`` under the spec
  hypothesis (dispatch cases) or a kernel ``decide`` that EVALUATED the claim and
  found it false (composite cases); flipping the claim changes the error on both
  shapes, which is what makes the exit code evidence.

  Only the modulus PREDICATE is opaque; ``rootSetIn`` itself is transparent and
  KERNEL-COMPUTABLE, so ``decide`` settles it at literals (e.g. the root set of a
  fourth-power congruence over nine residues, or the ten-member set of a zero
  target over a hundred). The two composite-helper witnesses therefore need NO
  conditioning at all and are stated at a literal input; conditioning is forced
  only by the branch selector, for the seven dispatch rivals. That is also why
  "nothing computes on this carrier" would be the wrong reason to drop a probe
  here.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * SOUNDNESS positives — PORTED, and doubled. The nagini ``pos-reshape-local``
    bound each appended element to a typed local inside an explicit COPY LOOP.
    The on-carrier reshape that carries that argument is one that BUILDS the
    reported list by accumulation instead of naming it: ``pos-composite-
    accumulate`` (a left fold appending each residue that passes the congruence
    test) and ``pos-composite-loop`` (the same by a ``let mut`` + ``for``). Each
    is definitionally DISTINCT from the frozen body — the frozen ``rfl`` no
    longer closes — so each re-proves inside the byte-identical obligation via an
    accumulate-equals-filter induction stated as a ``have`` (no new top-level
    declaration). That is the point: a reshape the frozen script closes verbatim
    is definitionally the frozen term and probes nothing, so a ``let``-binding of
    the returned expression (which zeta-reduces) is NOT an admissible positive
    here. Both MUST verify, else the postcondition is SPEC-TOO-STRONG on how the
    impl CONSTRUCTS the set. They are also the cheapest-honest grounded controls:
    producing the grounded root set IS the correct value (no scalar shortcut).
    Both reshape the composite helper, whose obligation is the transparent one;
    the dispatch obligation is defended by the admissibility case (which carries
    the frozen dispatch) and re-proved by both reshapes, since the dispatch's own
    proof unfolds the helper.

  * ADMISSIBILITY — RE-AIMED (as in the velvet sibling). The nagini
    ``admiss-fshape`` asserted the precondition for a concrete input. Here the
    modulus predicate is opaque, so no concrete literal is provably a single
    prime and that probe is unconstructible. The residual admissibility risk is
    that the FOUR post clauses of ``problem_spec_nthrootMod`` (three implications
    with overlapping guards) are JOINTLY UNSATISFIABLE at some reachable input —
    which reads exactly like a spec every impl meets. The frozen impl discharging
    all four (and the composite obligation) IS the witness. The case does NOT
    ship the bare frozen file, though: that would re-run G-VERIFY and pass for a
    reason the case does not own. Its impl region carries concrete INHABITATION
    facts — one per guarded sub-domain, each closed by computation — so the pass
    attests that the guards are reachable and their clauses mutually non-vacuous
    at named points, which no other case in the battery establishes.

  * UNIQUENESS rivals — PORTED, all five, plus TWO added by audit. The two C-zero
    rivals (drop-zero UNDER,
    two-zeros OVER) and the C-comp/K-set rivals (decline whole-branch, drop-last
    UNDER, duplicate OVER) attack the two load-bearing completeness clauses from
    both sides. The nagini decline-composite modelled the pre-patch
    ``NotImplementedError`` for a composite modulus; here the dispatch's non-prime
    branch returns the empty list. drop-last / duplicate attack the exact-set
    clause of the composite helper (K-set) — the on-carrier residue of the same
    UNDER/OVER pair the nagini attached to its composite completeness clause.
    The two ADDED rivals close what the ported five left unattacked, each on a
    sub-domain no ported case reaches. ``zero-target-before-regime`` moves the
    zero-target test AHEAD of the modulus-regime test: both branch VALUES stay
    correct, so it is attributable to branch ORDER alone, and it is the plausible
    near-miss (adding the zero root but checking it first) that the ported rivals
    cannot express — each of them makes a branch's value wrong.
    ``drop-unit-base-roots`` is the only rival on (C-res), the clause pinning the
    unchanged single-prime path; with it every clause of both obligations is
    attacked by a rival, not merely defended by a positive.

  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend, and not fabricated.
    The nagini sibling's frame class exists because a read-only heap input may
    carry a fractional permission an impl overwrites. Lean is referentially
    transparent: ``a``, ``n``, ``m``, ``p`` are immutable scalar values, this
    bundle declares no mutable binder, there is no heap and no aliasing — no
    read-only input to overwrite and no substitute probe to build. The nagini
    surface itself already records this class as N/A (all inputs are scalar ints;
    the only full-permission object is the result the impl creates). See the
    accounting block at the foot of this file.

  * UNGROUNDED-ORACLE ECHO — N/A as a WRONG echo (as in nagini). The completeness
    clauses are grounded in ``rootSetIn`` (a filter over the actual inputs) and in
    the exact singleton; ``primeRoots`` is pinned only on its own unchanged
    branch. There is no answer-key a wrong impl could echo to skip the work —
    echoing the grounded root set IS the correct value, which the positive
    controls do honestly.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` (power-mod soundness, the
prime/composite root-set A-references, the residue predicate, and the
composite-regime containment) are G-AX's job (axiom_check.py / mapping.md); the
G-PBT spec lane ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-18199"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside an impl region and is unique
# ---- in Solution.lean; both facts asserted at load by _swap) ----------------

# The composite helper's whole body: it returns the grounded root set directly.
_A_COMP = "  return rootSetIn a n m"
# The dispatch's single-prime zero-target branch (the exact singleton).
_A_ZERO = "    return [0]"
# The dispatch's non-single-prime branch (defers to the composite helper).
_A_NP = "    return implementation_nthrootModComposite a n p"
# The dispatch's unchanged single-prime unit-base branch (the C-res target).
_A_UNIT = "  return primeUnitRoots a n p"
# The dispatch's WHOLE body: the branch ORDER is what a reordering rival /
# reshape has to move, so the surgery anchor has to span all three tests.
_A_DISPATCH = (
    "  if !(modulusIsPrime p) then\n"
    "    return implementation_nthrootModComposite a n p\n"
    "  if a % p == 0 then\n"
    "    return [0]\n"
    "  return primeUnitRoots a n p")

for _a in (_A_COMP, _A_ZERO, _A_NP, _A_UNIT, _A_DISPATCH):
    assert _BASE.count(_a) == 1, f"impl anchor drifted from Solution.lean: {_a!r}"

# ---- proof-region anchors. A positive whose impl is a genuine RESHAPE (not a
# ---- definitional no-op) has to RE-PROVE, which is the point: a reshape the
# ---- frozen script closes verbatim is definitionally the frozen body and tests
# ---- nothing. Both anchors lie wholly inside a `-- proof-start/-- proof-end`
# ---- region, so `markers.same_spec` and the byte-identical `theorem correct_*`
# ---- STATEMENTS are untouched (only the tactic bodies move).
_A_PROOF_COMP = """  intro a n m _ _ hm _ _
  refine ⟨rfl, ?_⟩
  intro x hx
  have hx' : x ∈ rootSetIn a n m := by
    simpa [implementation_nthrootModComposite, Id.run] using hx
  exact (mem_rootSetIn (by omega)).1 hx'"""

_A_PROOF_HIMPL = """  have himpl : implementation_nthrootMod a n p =
      (if modulusIsPrime p = true then
        (if a % p = 0 then [0] else primeUnitRoots a n p)
       else rootSetIn a n p) := by
    unfold implementation_nthrootMod implementation_nthrootModComposite
    by_cases hpr : modulusIsPrime p = true <;>
      by_cases haz : a % p = 0 <;>
      simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
        if_true, if_false] <;> rfl"""

for _a in (_A_PROOF_COMP, _A_PROOF_HIMPL):
    assert _BASE.count(_a) == 1, f"proof anchor drifted from Solution.lean: {_a!r}"


# ---------------------------------------------------------------------------
# Re-proof material for the two GENUINE composite-helper reshapes below. The
# frozen impl returns `rootSetIn` literally, so its obligation closes by `rfl`;
# an impl that BUILDS the set by accumulation is a different term and needs the
# accumulate-equals-filter step proved. Stated as a `have` INSIDE each
# obligation (never a new top-level theorem/lemma — `variant_scope` rule 3).
# ---------------------------------------------------------------------------
def _key(mv):
    """The accumulate-equals-filter step, over modulus binder `mv` (m or p)."""
    return ("""  have key : ∀ (l : List ℤ) (init : List ℤ),
      (l.foldl (fun acc x => if (x ^ n.toNat - a) % MV == 0 then acc ++ [x] else acc)
        init) = init ++ l.filter (fun x => (x ^ n.toNat - a) % MV == 0) := by
    intro l
    induction l with
    | nil => intro init; simp
    | cons y ys ih =>
      intro init
      cases hy : ((y ^ n.toNat - a) % MV == 0) with
      | true =>
        rw [List.foldl_cons, List.filter_cons]
        simp only [hy, if_true]
        rw [ih (init ++ [y])]
        simp
      | false =>
        rw [List.foldl_cons, List.filter_cons]
        simp only [hy, if_false, Bool.false_eq_true]
        rw [ih init]
""").replace("MV", mv)


def _hcomp(mv, simpset):
    """`implementation_nthrootModComposite a n mv = rootSetIn a n mv`."""
    return (f"  have hcomp : implementation_nthrootModComposite a n {mv} "
            f"= rootSetIn a n {mv} := by\n"
            "    unfold implementation_nthrootModComposite rootSetIn\n"
            f"    simp only [{simpset}]\n"
            f"    rw [key ((List.range {mv}.toNat).map (Int.ofNat)) []]\n"
            "    simp\n")


def _reshape_composite(impl, simpset):
    """A composite-helper impl RESHAPE + the re-proof both obligations need."""
    src = _swap(_BASE, _A_COMP, impl)
    src = _swap(src, _A_PROOF_COMP,
                "  intro a n m _ _ hm _ _\n" + _key("m") + _hcomp("m", simpset)
                + "  refine ⟨hcomp, ?_⟩\n"
                  "  intro x hx\n"
                  "  rw [hcomp] at hx\n"
                  "  exact (mem_rootSetIn (by omega)).1 hx")
    # the dispatch's own proof unfolds the helper, so it needs the same step
    return _swap(src, _A_PROOF_HIMPL,
                 _key("p") + _hcomp("p", simpset)
                 + """  have himpl : implementation_nthrootMod a n p =
      (if modulusIsPrime p = true then
        (if a % p = 0 then [0] else primeUnitRoots a n p)
       else rootSetIn a n p) := by
    unfold implementation_nthrootMod
    rw [hcomp]
    by_cases hpr : modulusIsPrime p = true <;>
      by_cases haz : a % p = 0 <;>
      simp only [Id.run, hpr, haz, Bool.not_true, Bool.not_false, beq_iff_eq,
        if_true, if_false] <;> rfl""")


# ===========================================================================
# WITNESSES (each machine-checked: ELABORATES vs its rival, FAILS vs frozen;
# binders jointly satisfiable per the `: False` consistency probe).
#
# WITNESS SHAPE — why no witness here NAMES the rival's return value.
#
# The obvious shape for these refutations is "compute the rival's value into a
# `have hval : impl … = <literal>`, rewrite, then contradict the clause". Every
# witness in this battery was originally written that way, and an audit rebuild
# showed the shape is HOLLOW on this carrier: the `hval` step is a claim about
# the IMPL ALONE, it is the FIRST tactic in the script, and on the frozen
# solution it fails (gold's impl does not equal the rival's value) — so the
# build dies before any tactic ever looks at the spec. Measured: for all seven
# reject cases, the frozen-side build produced the byte-identical first error
# (`Tactic `rfl` failed: … is not definitionally equal to …`) whether the
# witness asserted `¬ problem_spec …` or the flipped claim `problem_spec …`.
# Gold's exit code therefore carried NO information about what was claimed: a
# witness asserting gold is CORRECT there would have been recorded as a
# refutation just the same.
#
# The repair is to never state the rival's value. Each witness now derives the
# spec clause FIRST (`h.2.1 hp hz`, `h.1`, …) and lets the contradiction be the
# only thing that has to be decided:
#
#   * the five DISPATCH witnesses discharge `absurd <clause> (by simp [impl, …])`
#     under the branch hypotheses. `simp` reduces the impl and the named clause
#     TOGETHER, so on the rival it closes and on gold the residual goal is the
#     honest `⊢ False` with the spec hypothesis in context ("unsolved goals"),
#     which is a semantic refutation of the concrete claim;
#   * the two COMPOSITE-helper witnesses state the refutation at the LITERAL
#     F2P-shaped input (a sixteenth-power congruence over thirty-six residues,
#     whose root set has six members) and close by `decide`. `rootSetIn` is
#     transparent and kernel-computable, so this needs no conditioning at all —
#     and gold's failure is `Tactic `decide` proved that the proposition
#     ¬implementation_… = rootSetIn … is false`, i.e. the kernel EVALUATED the
#     claim and refuted it. Flipping the claim changes that error (the flipped
#     build fails at `intro` instead), so the exit code tracks the claim.
# ===========================================================================

# C-zero, UNDER-keep: the zero-target branch returns [] instead of [0]. Refuted
# by conditioning on the single-prime zero-target sub-domain (isPrime, a%p=0).
# The exact-singleton clause is derived first and `simp` reduces the impl only
# inside the contradiction, so gold fails on the CLAIM, not on a value equation.
_W_DROP_ZERO = (
    "example (a n p : ℤ) (hp : modulusIsPrime p = true) (hz : a % p = 0) :\n"
    "    ¬ problem_spec_nthrootMod a n p (implementation_nthrootMod a n p) := by\n"
    "  intro h\n"
    "  exact absurd (h.2.1 hp hz)\n"
    "    (by simp [implementation_nthrootMod, Id.run, Id.pure_eq, Id.bind_eq,\n"
    "      hp, hz])\n"
)

# C-zero, OVER-keep: the zero-target branch returns [0, 0]. Both entries are
# genuine roots (soundness holds), but the exact-singleton length is violated.
# Same claim-first shape; the rival's [0, 0] is never named.
_W_TWO_ZEROS = _W_DROP_ZERO

# C-comp, whole branch empty: the non-single-prime branch returns []. Refuted by
# conditioning on the validated non-prime sub-domain with a NON-EMPTY root set.
_W_DECLINE = (
    "example (a n p : ℤ) (hnp : modulusIsPrime p ≠ true)\n"
    "    (hpf : modulusIsPrime p = false)\n"
    "    (hcv : dispatchValidated a n p = true) (hne : rootSetIn a n p ≠ []) :\n"
    "    ¬ problem_spec_nthrootMod a n p (implementation_nthrootMod a n p) := by\n"
    "  intro h\n"
    "  exact absurd (h.2.2.2.2 hnp hcv)\n"
    "    (by simp [implementation_nthrootMod, implementation_nthrootModComposite,\n"
    "      Id.run, Id.pure_eq, Id.bind_eq, hpf, Ne.symm hne])\n"
)

# K-set, UNDER-keep: the composite helper drops the LAST assembled root. Every
# returned value is still a genuine root (K-sound holds); only the exact-set
# equality fails. Stated at a LITERAL input and closed by `decide`: the helper's
# impl is transparent and kernel-computable, so no conditioning is needed and
# gold's failure is the kernel EVALUATING the claim and refuting it.
_W_DROP_LAST = (
    "example : ¬ problem_spec_nthrootModComposite 9 16 36\n"
    "    (implementation_nthrootModComposite 9 16 36) := by\n"
    "  intro h\n"
    "  exact absurd h.1 (by decide)\n"
)

# K-set, OVER-keep: the composite helper appends the first root a second time.
# The extra entry is itself a genuine root (K-sound holds); the result is
# strictly longer than the complete set, so the exact-set equality fails. Same
# literal/`decide` shape as drop-last, but at a DIFFERENT literal point, so the
# two composite reject cases together attest that the exact-set clause is read
# at more than one (a, n, m) — a single shared point would leave the spec's
# dependence on the arguments undemonstrated. Here the complete set is the
# singleton [1] and the rival returns [1, 1].
_W_DUPLICATE = (
    "example : ¬ problem_spec_nthrootModComposite 1 3 8\n"
    "    (implementation_nthrootModComposite 1 3 8) := by\n"
    "  intro h\n"
    "  exact absurd h.1 (by decide)\n"
)


# C-res, whole branch empty: the single-prime unit-base branch returns []
# instead of the unit-base solver's roots. Refuted by conditioning on the
# single-prime NON-zero-target sub-domain with a non-empty unit-root list — the
# sub-domain the completeness clause for the unchanged path speaks about.
_W_DROP_UNIT = (
    "example (a n p : ℤ) (hp : modulusIsPrime p = true) (hz : a % p ≠ 0)\n"
    "    (hne : primeUnitRoots a n p ≠ []) :\n"
    "    ¬ problem_spec_nthrootMod a n p (implementation_nthrootMod a n p) := by\n"
    "  intro h\n"
    "  exact absurd (h.2.2.1 hp hz)\n"
    "    (by simp [implementation_nthrootMod, Id.run, Id.pure_eq, Id.bind_eq,\n"
    "      hp, hz, Ne.symm hne])\n"
)

# BRANCH-ORDER, UNDER-keep on the composite regime: the zero-target test is
# evaluated BEFORE the modulus-regime test, so a modulus that is NOT a single
# prime but divides the target takes the singleton branch and the rest of its
# root set is lost. Refuted by conditioning on exactly that overlap
# (¬single-prime ∧ a%p=0 ∧ validated) with a root set that is not the singleton.
_W_ZERO_FIRST = (
    "example (a n p : ℤ) (hnp : modulusIsPrime p ≠ true)\n"
    "    (hpf : modulusIsPrime p = false) (hz : a % p = 0)\n"
    "    (hcv : dispatchValidated a n p = true) (hne : rootSetIn a n p ≠ [0]) :\n"
    "    ¬ problem_spec_nthrootMod a n p (implementation_nthrootMod a n p) := by\n"
    "  intro h\n"
    "  exact absurd (h.2.2.2.2 hnp hcv)\n"
    "    (by simp [implementation_nthrootMod, implementation_nthrootModComposite,\n"
    "      Id.run, Id.pure_eq, Id.bind_eq, hpf, hz, Ne.symm hne])\n"
)


# C-report, off-regime EMPTY REPORT: the non-single-prime branch returns [] for
# every input the regime does not cover, and the complete set only inside
# it. Refuted from the UNCONDITIONAL non-single-prime report clause, at a
# sub-domain OUTSIDE the regime where the congruence nevertheless has a solution:
# no completeness clause speaks there, so only the solution-count obligation does.
#
# The counting conjunct reduces, on the rival, to `0 = (rootSetIn a n p).length`
# — the ZERO on the LEFT, because it is the rival's report whose length collapses.
# `hne` speaks about the root set, so the step from "not the empty list" to "the
# count is not zero" has to be taken EXPLICITLY and in that orientation: fed the
# `[] ≠ rootSetIn …` orientation, `List.length_eq_zero_iff` never fires (measured:
# simp reports both it and `Ne.symm hne` as UNUSED and leaves
# `⊢ ¬0 = (rootSetIn a n p).length` open, which is the tactic gap that read as
# `witness-unproven`). `hlen` is derived from `hne` alone — it mentions no impl —
# so the rival's value is still named nowhere and the impl is still reduced only
# inside the `absurd`: gold's failure stays the semantic
# `h : problem_spec_… ⊢ False`, and the flipped claim fails differently
# (`introN failed`), so gold's exit code still tracks the claim.
_W_OFFREGIME_EMPTY = (
    "example (a n p : ℤ) (hnp : modulusIsPrime p ≠ true)\n"
    "    (hpf : modulusIsPrime p = false)\n"
    "    (hdv : dispatchValidated a n p = false) (hne : rootSetIn a n p ≠ []) :\n"
    "    ¬ problem_spec_nthrootMod a n p (implementation_nthrootMod a n p) := by\n"
    "  intro h\n"
    "  have hlen : (0 : ℕ) ≠ (rootSetIn a n p).length :=\n"
    "    fun h0 => hne (List.length_eq_zero_iff.mp h0.symm)\n"
    "  exact absurd ((h.2.2.2.1 hnp).2.2)\n"
    "    (by simp [implementation_nthrootMod, implementation_nthrootModComposite,\n"
    "      Id.run, Id.pure_eq, Id.bind_eq, hpf, hdv, hlen])\n"
)

# C-report, ORDER: the non-single-prime branch reverses the assembled root set.
# Every returned value is still a genuine in-range root and the SET is complete,
# so soundness holds and only the ordering half of the unconditional report
# obligation (and the exact-sequence clause inside the regime) rejects it.
#
# AUDIT REPAIR (witness shape). The earlier form closed with
# `simpa [... hpf] using hns`, and on the frozen solution that produced a TYPE
# MISMATCH (`hns has type ¬Pairwise … (rootSetIn a n p).reverse but is expected
# to have type ¬Pairwise … (rootSetIn a n p)`) rather than a refutation: gold's
# report reduces to the UNREVERSED set, so `simpa`'s supplied term simply no
# longer typechecked. That is a signature the gate cannot tell from a real
# refutation, and it is the ONE non-evaluation gold signature this battery had.
# Rebuilt to check what the error actually carried: a type-revealing build
# (`exact (hord : Nat)`) printed the IDENTICAL hypothesis type on both sides
# (`Pairwise … (implementation_nthrootMod a n p)`), i.e. the mismatch was about
# the term FED to `simpa`, not about which side satisfies the clause.
# Repaired by putting `sorted_rootSetIn a n p` in the simp set, so on GOLD simp
# PROVES the ordering clause outright and the residual goal is the honest
# `h : problem_spec_… ⊢ False` — measured: rival exit 0, gold exit 1 with
# `unsolved goals … ⊢ False`, flipped claim exit 1 with `introN failed`, so
# gold's exit code now tracks the CLAIM on this case as it does on the other ten.
_W_REVERSED = (
    "example (a n p : ℤ) (hnp : modulusIsPrime p ≠ true)\n"
    "    (hpf : modulusIsPrime p = false)\n"
    "    (hns : ¬ ((rootSetIn a n p).reverse.Pairwise (· < ·))) :\n"
    "    ¬ problem_spec_nthrootMod a n p (implementation_nthrootMod a n p) := by\n"
    "  intro h\n"
    "  exact absurd ((h.2.2.2.1 hnp).2.1)\n"
    "    (by simp [implementation_nthrootMod, implementation_nthrootModComposite,\n"
    "      Id.run, Id.pure_eq, hpf, hns, sorted_rootSetIn a n p])\n"
)

# K-set/C-comp SEAM: the helper is correct exactly on its OWN regime predicate
# `compositeValidated` and reverses the root set outside it. Added by audit — the
# sub-domain where the helper's own obligation is silent but the DISPATCH's
# exact-set clause still binds, because `dispatchValidated` is strictly WIDER
# than `compositeValidated` (it adds the quadratic-exponent leg `n == 2`). No
# ported or previously-added rival deviates there. Conditioned on exactly that
# seam: not a single prime, `n = 2`, `compositeValidated = false` (so the helper's
# guard sends it down the reversed branch), and a root set that is not its own
# reverse (i.e. at least two members).
_W_QUAD_SEAM = (
    "example (a n p : ℤ) (hnp : modulusIsPrime p ≠ true)\n"
    "    (hpf : modulusIsPrime p = false) (hn2 : n = 2)\n"
    "    (hcf : compositeValidated a n p = false)\n"
    "    (hns : ¬ ((rootSetIn a n p).reverse = rootSetIn a n p)) :\n"
    "    ¬ problem_spec_nthrootMod a n p (implementation_nthrootMod a n p) := by\n"
    "  intro h\n"
    "  exact absurd (h.2.2.2.2 hnp (by simp [dispatchValidated, hn2]))\n"
    "    (by simp [implementation_nthrootMod, implementation_nthrootModComposite,\n"
    "      Id.run, Id.pure_eq, Id.bind_eq, hpf, hcf, hns])\n"
)


# C-report, OVER-report on an UNSOLVABLE congruence: the non-single-prime branch
# appends a fixed in-range residue when the grounded root set is EMPTY, so it
# announces a solution to a congruence that has none. Refuted from the
# solution-COUNTING half of the unconditional report clause, at a sub-domain the
# never-decline direction alone cannot see.
_W_PHANTOM = (
    "example (a n p : ℤ) (hnp : modulusIsPrime p ≠ true)\n"
    "    (hpf : modulusIsPrime p = false)\n"
    "    (hemp : rootSetIn a n p = []) :\n"
    "    ¬ problem_spec_nthrootMod a n p (implementation_nthrootMod a n p) := by\n"
    "  intro h\n"
    "  exact absurd ((h.2.2.2.1 hnp).2.2)\n"
    "    (by simp [implementation_nthrootMod, implementation_nthrootModComposite,\n"
    "      Id.run, Id.pure_eq, Id.bind_eq, hpf, hemp])\n"
)

# S, COMPOSITE-ORACLE ECHO: off the regime the non-single-prime branch hands its
# NON-single-prime modulus to the unit-base solver — the callee whose
# soundness contract is claimed only on its own single-prime domain. Refuted from
# the report clause, whose ordering/range/counting conjuncts that callee's
# output on a foreign modulus cannot be shown to satisfy.
_W_ORACLE_ECHO = (
    "example (a n p : ℤ) (hnp : modulusIsPrime p ≠ true)\n"
    "    (hpf : modulusIsPrime p = false)\n"
    "    (hdv : dispatchValidated a n p = false)\n"
    "    (hemp : rootSetIn a n p = []) (hpu : primeUnitRoots a n p ≠ []) :\n"
    "    ¬ problem_spec_nthrootMod a n p (implementation_nthrootMod a n p) := by\n"
    "  intro h\n"
    "  exact absurd ((h.2.2.2.1 hnp).2.2)\n"
    "    (by simp [implementation_nthrootMod, implementation_nthrootModComposite,\n"
    "      Id.run, Id.pure_eq, Id.bind_eq, hpf, hdv, hemp,\n"
    "      List.length_eq_zero_iff, hpu])\n"
)

SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify; else the postcondition over-constrains the impl's
    # data-flow shape (SPEC-TOO-STRONG). Each keeps `theorem correct_*`
    # byte-identical and introduces no lemma/axiom/assumption; the frozen proof
    # closes because the reshape is definitionally the frozen body.
    # =====================================================================
    {
        "id": "pos-composite-accumulate",
        "kind": "soundness",
        "expect": "verify",
        "module": _reshape_composite(
            "  return ((List.range m.toNat).map (Int.ofNat)).foldl\n"
            "    (fun acc x => if (x ^ n.toNat - a) % m == 0 then acc ++ [x] else acc) []",
            "Id.run, Id.pure_eq"),
        "rationale": "Structurally-different CORRECT impl of the composite helper: "
                     "instead of naming the grounded root set, it BUILDS the same "
                     "list by a left fold that appends each in-range residue passing "
                     "the congruence test. This is NOT definitionally the frozen "
                     "body — the frozen `rfl` no longer closes — so the case must "
                     "re-prove, and the re-proof (an accumulate-equals-filter "
                     "induction, stated as a `have` inside the frozen obligation) is "
                     "what shows the spec accepts an impl that PRODUCES the set "
                     "rather than one that names it. Both clauses of "
                     "problem_spec_nthrootModComposite still hold; must verify "
                     "(else SPEC-TOO-STRONG on the impl's construction shape). Ports "
                     "the nagini pos-reshape-local ARGUMENT — same values, different "
                     "assembly — with the assembly actually differing, which a "
                     "`let`-binding of the returned expression would not (it "
                     "zeta-reduces to the frozen term and tests nothing).",
    },
    {
        "id": "pos-composite-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _reshape_composite(
            "  let mut acc : List ℤ := []\n"
            "  for x in (List.range m.toNat).map (Int.ofNat) do\n"
            "    acc := if (x ^ n.toNat - a) % m == 0 then acc ++ [x] else acc\n"
            "  return acc",
            "Id.run, Id.pure_eq, Id.bind_eq, List.forIn_yield_eq_foldl"),
        "rationale": "The IMPERATIVE counterpart of the previous positive, and the "
                     "closest on-carrier analogue of the nagini reshape's explicit "
                     "copy loop: a mutable accumulator extended in a `for` over the "
                     "candidate residues. The elaborated term is a `forIn`, so it is "
                     "definitionally distinct from both the frozen body and the fold "
                     "above and needs its own reduction step before the same "
                     "accumulate-equals-filter argument applies. Must verify — an "
                     "accumulation-shaped impl of the complete set is exactly what a "
                     "faithful patch looks like, so a spec that rejected it would be "
                     "SPEC-TOO-STRONG on data flow.",
    },
    # =====================================================================
    # ADMISSIBILITY — RE-AIMED (opaque modulus predicate makes the nagini
    # concrete-input precondition probe unconstructible). The frozen solution
    # verifying against all four dispatch clauses (and the composite obligation)
    # witnesses that the clause set is JOINTLY SATISFIABLE at reachable inputs —
    # a spec no faithful impl can meet reads exactly like one every impl meets.
    # module is the frozen solution ⇒ same_spec trivially, obligations intact;
    # MUST verify, else SPEC-UNSATISFIABLE / PRECOND-TOO-STRONG.
    # =====================================================================
    {
        "id": "admiss-joint-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        # Not the bare frozen file: `module = _BASE` re-runs G-VERIFY and passes
        # for a reason the case does not own. The impl region carries CONCRETE
        # inhabitation facts for each guarded sub-domain the postconditions speak
        # about, each closed by `decide`/`simp` (no new named declaration, so
        # variant_scope rule 3 holds and the obligations stay byte-identical).
        # If a guard were unreachable or its clause vacuous, the corresponding
        # `example` would not close.
        "module": _swap(_BASE, _A_COMP, """  return rootSetIn a n m

/- Admissibility (impl region only): every guarded sub-domain the
postconditions speak about is INHABITED at concrete inputs, so no clause holds
vacuously. The quadratic-exponent leg of the dispatch regime is inhabited by
DECISION (it needs no opaque predicate at all), so a modulus with a repeated
prime factor really is admitted there. The two structural legs of the regime are
each inhabited under their own arithmetic hypothesis. Root sets are non-empty at
those points (so the exact-set clause has content, and is NOT the singleton the
zero-target clause pins); a zero target really does have the single root zero
over a single-prime modulus. -/
example : dispatchValidated 9 2 160 = true := by decide
example : rootSetIn 9 2 160 ≠ [] := by decide
example : rootSetIn 9 2 160 ≠ [0] := by decide
example (h : modulusSquarefree 15 = true) : compositeValidated 2 3 15 = true := by
  simp [compositeValidated, h]
example (h : modulusRegularLift 1 3 8 = true) : compositeValidated 1 3 8 = true := by
  simp [compositeValidated, h]
example : rootSetIn 1 3 8 = [1] := by decide
example : rootSetIn 4 4 9 = [4, 5] := by decide
example : rootSetIn 0 7 100 ≠ [] := by decide
example : rootSetIn 0 7 100 ≠ [0] := by decide
example : rootSetIn 289 5 17 = [0] := by decide

/- The unconditional non-single-prime report obligation is SATISFIABLE at a
concrete point of the sub-domain no regime condition guards — it is the clause
that has to hold everywhere, so a clause set unsatisfiable there would be the
worst kind of vacuity. -/
example : reportsRootsFor 3 3 8 (rootSetIn 3 3 8) := by
  refine ⟨?_, sorted_rootSetIn 3 3 8, rfl⟩
  intro x hx
  have hx' := (mem_rootSetIn (by norm_num)).1 hx
  exact ⟨hx'.1, hx'.2.1⟩

/- The OBLIGATION ITSELF, discharged at a concrete F2P-shaped input by
EVALUATION rather than at a quantified point. This is the direction the
inhabitation facts above cannot reach: they say the guards are inhabited, but
they do not say the composite postcondition is SATISFIABLE at a named input.
A precondition-too-strong / clause-unsatisfiable defect would show up exactly
here — the whole predicate failing to close at a point the failing test
reaches (a fourth-power congruence over nine residues, whose root set has two
members). -/
example : rootSetIn 9 16 36 = [3, 9, 15, 21, 27, 33] := by decide
example : problem_spec_nthrootModComposite 9 16 36
    (implementation_nthrootModComposite 9 16 36) := by
  refine ⟨rfl, ?_⟩
  intro x hx
  exact (mem_rootSetIn (by norm_num)).1
    (by simpa [implementation_nthrootModComposite, Id.run] using hx)"""),
        "rationale": "PASS SOURCE = joint satisfiability of the postcondition "
                     "clauses. The dispatch's guards (¬single-prime; single-prime ∧ "
                     "a%p=0; single-prime ∧ a%p≠0 ∧ (¬)residue) are pairwise "
                     "disjoint, so no two branch equalities conflict, and soundness "
                     "co-holds with each on its own guarded sub-domain. The frozen "
                     "impl discharging all clauses is the admissibility witness; "
                     "else the spec would be unsatisfiable and a false pass "
                     "everywhere. On this opaque-modulus carrier no concrete "
                     "literal is provably a single prime, so this replaces the "
                     "nagini concrete-input precondition probe. The inhabitation "
                     "facts in the impl region make the pass ATTRIBUTABLE to this "
                     "case rather than to G-VERIFY: each names a concrete point of "
                     "a guarded sub-domain and is discharged by computation, and "
                     "the last group discharges the composite OBLIGATION itself at "
                     "a concrete F2P-shaped input by evaluation — the analogue, on "
                     "a total carrier, of the nagini precondition probe: a clause "
                     "set unsatisfiable at an F2P-shaped input would fail exactly "
                     "there, which no inhabitation fact and no reject case detects. "
                     "Two of them separate the zero-target singleton from the "
                     "composite exact-set clause (a modulus that is not a single "
                     "prime, dividing the target, whose root set is NOT [0]), so "
                     "the clauses are shown to be independently non-vacuous.",
    },
    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected, each with a machine-checked refutation witness conditioned on the
    # sub-domain it abuses, and the refinement argument that a faithful real
    # counterpart would NOT resolve the F2P / issue.
    # =====================================================================
    {
        "id": "drop-zero-root",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_ZERO, "    return ([] : List ℤ)"),
        "refinement": "The on-carrier analogue of the EXACT pre-patch behaviour: "
                      "for a single-prime modulus whose target is divisible by it, "
                      "the zero residue is dropped (the result is empty). This is "
                      "precisely the defect the issue reports — the documented "
                      "example (a single-prime modulus, target the square of it, "
                      "exponent five) is missing its zero root. A patch of this "
                      "shape IS the pre-patch code; the issue's own example still "
                      "fails, so it would NOT resolve.",
        "rationale": "REJECT from (C-zero) `modulusIsPrime p → a % p = 0 → result = "
                     "[0]`. Returning [] is sound VACUOUSLY (no element to check) "
                     "but has length 0 ≠ 1, so the exact-singleton clause is "
                     "unprovable. Soundness alone would admit it; completeness "
                     "rejects it. Witness conditions on the single-prime "
                     "zero-target sub-domain (modulusIsPrime p = true, a % p = 0), "
                     "derives clause `h.2.1` FIRST and contradicts it by reducing "
                     "the impl only inside the `absurd` — so it never states the "
                     "rival's value, and the gold-side failure is the residual "
                     "`⊢ False` under the spec hypothesis rather than a value "
                     "equation that would fail on gold whatever was claimed. "
                     "Varies the modulus binder into the single-prime regime and "
                     "the target binder into the zero-target sub-domain.",
        "witness": _W_DROP_ZERO,
    },
    {
        "id": "two-zeros-prime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_ZERO, "    return [0, 0]"),
        "refinement": "A faithful patch that emitted the zero root twice (failing "
                      "to collapse its multiplicity) would report a non-existent "
                      "second solution. Over a single-prime field the equation with "
                      "a zero target has the UNIQUE root zero (no zero divisors); "
                      "the issue and gold pin exactly the single zero. A two-element "
                      "result is wrong and would not match the expected single-root "
                      "output, so it would NOT resolve.",
        "rationale": "REJECT from (C-zero) `… → result = [0]`. Both entries of "
                     "[0, 0] are genuine roots so SOUNDNESS holds, but length 2 ≠ 1, "
                     "so the exact-singleton clause is unprovable. This is the "
                     "OVER-keep side of the zero-target gap (contrast "
                     "drop-zero-root's UNDER-keep), pinning the result to the EXACT "
                     "singleton not merely 'contains 0'. Witness reduces the "
                     "rival's impl to [0, 0] at the same conditioning point and "
                     "refutes via `h.2.1`; it fails on gold.",
        "witness": _W_TWO_ZEROS,
    },
    {
        "id": "decline-composite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_NP, "    return ([] : List ℤ)"),
        "refinement": "The on-carrier analogue of the pre-patch behaviour that "
                      "DECLINED a non-single-prime modulus (raised instead of "
                      "solving), modelled as returning []. The sole FAIL_TO_PASS "
                      "reaches the solver ONLY with non-single-prime moduli (the "
                      "modular equations over 8 and 9 in the failing test); a patch "
                      "that declines them returns nothing there and FAILS the F2P. "
                      "It would NOT resolve.",
        "rationale": "REJECT from (C-comp) `¬ modulusIsPrime p → compositeValidated "
                     "a n p → result = rootSetIn a n p`. Returning [] is sound "
                     "vacuously but ≠ the complete grounded root set whenever that "
                     "set is non-empty (it is, on the F2P shapes), so the composite "
                     "completeness clause is unprovable. Witness conditions on the "
                     "validated non-prime sub-domain with a NON-EMPTY root set "
                     "(modulusIsPrime p ≠ true, compositeValidated, rootSetIn … ≠ "
                     "[]), derives clause `h.2.2.2.2` FIRST and contradicts it with "
                     "the impl reduced only inside the `absurd`, so the gold-side "
                     "failure is a refutation of the claim and not of a value "
                     "equation. Varies the modulus binder into the "
                     "non-single-prime regime.",
        "witness": _W_DECLINE,
    },
    {
        "id": "drop-last-composite-root",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_COMP, "  return (rootSetIn a n m).dropLast"),
        "refinement": "A faithful patch whose root assembly has an "
                      "off-by-one (drops the final assembled root) returns a STRICT "
                      "SUBSET of the true root set. On the failing test's "
                      "non-single-prime equations the expected solution set then "
                      "loses a member, so the test's asserted image set is wrong and "
                      "the F2P fails. Every value it DOES return is a real root, so "
                      "a soundness-only spec would wrongly accept it — the canonical "
                      "verify-but-not-resolve rival. It would NOT resolve.",
        "rationale": "REJECT from (K-set) `result = rootSetIn a n m` of the "
                     "composite helper. `.dropLast` has length one less than the "
                     "complete set, so the equality fails whenever the set is "
                     "non-empty. K-sound (`∀ x ∈ result, isRootIn a n m x`) STILL "
                     "holds (every kept element is a member of the grounded set), so "
                     "this isolates the exact-set clause as load-bearing. The helper "
                     "is transparent and kernel-computable, so the witness needs NO "
                     "conditioning: it states the refutation at the LITERAL "
                     "F2P-shaped input (a sixteenth-power congruence over thirty-six "
                     "residues, whose root set has six members) and closes by "
                     "`decide`. Gold's failure is the kernel reporting that "
                     "`¬ implementation_… = rootSetIn …` is FALSE — an evaluation of "
                     "the claim, which is why flipping the claim changes the error.",
        "witness": _W_DROP_LAST,
    },
    {
        "id": "duplicate-composite-root",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _A_COMP,
            "  return (rootSetIn a n m) ++ (rootSetIn a n m).take 1"),
        "refinement": "A faithful patch that double-counts a root (a recombination "
                      "revisiting a residue) returns a list with a duplicate. The "
                      "real solver returns a de-duplicated set and the failing test "
                      "compares the exact solution set; a duplicated entry yields "
                      "the wrong image and the F2P fails. The extra entry is itself "
                      "a real root, so soundness holds — only the exact-set "
                      "completeness clause rejects it. It would NOT resolve.",
        "rationale": "REJECT from (K-set) `result = rootSetIn a n m`. Appending the "
                     "first element again makes the result strictly longer than the "
                     "complete set whenever it is non-empty, so the equality fails. "
                     "This is the OVER-keep side of the composite gap (contrast "
                     "drop-last's UNDER-keep): K-sound holds (each element is a "
                     "member of the grounded set), the exact sequence does not. "
                     "Same literal/`decide` witness shape as drop-last (the helper "
                     "computes, so no conditioning is needed): at the F2P-shaped "
                     "input the rival's list is strictly longer than the six-member "
                     "root set, and gold's failure is the kernel EVALUATING the "
                     "claim and refuting it, not a value equation.",
        "witness": _W_DUPLICATE,
    },
    {
        "id": "zero-target-before-regime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_DISPATCH,
                        "  if a % p == 0 then\n"
                        "    return [0]\n"
                        "  if !(modulusIsPrime p) then\n"
                        "    return implementation_nthrootModComposite a n p\n"
                        "  return primeUnitRoots a n p"),
        "refinement": "A faithful patch that adds the zero-target special case but "
                      "places it AHEAD of the modulus-regime test — the plausible "
                      "near-miss, since the zero root is what the issue asks for and "
                      "putting its check first looks harmless. It is not: a modulus "
                      "that is NOT a single prime but divides the target now takes "
                      "the singleton branch and the rest of its root set is lost. "
                      "The failing test's own inputs include a modulus of that shape "
                      "(a non-single-prime modulus with a zero target has ten "
                      "in-range roots spaced by a tenth of it, not one), so the "
                      "asserted solution set is short by nine members and the F2P "
                      "fails. It would NOT resolve. This near-miss is why the two "
                      "branches' ORDER, not merely their presence, is part of the "
                      "behaviour the spec must pin.",
        "rationale": "REJECT from (C-comp) `¬ modulusIsPrime p → compositeValidated "
                     "a n p → result = rootSetIn a n p`. On the OVERLAP of the "
                     "zero-target guard and the non-single-prime guard the rival "
                     "returns [0] while the clause demands the whole grounded set, "
                     "so the equality fails wherever that set is not the singleton. "
                     "Soundness survives (0 is a genuine root there), and so does "
                     "C-zero (the rival returns exactly [0] on the single-prime "
                     "zero-target sub-domain), which is what makes this rival "
                     "attributable to the branch ORDER alone rather than to either "
                     "branch's value. NOT covered by decline-composite (whose rival "
                     "empties the composite branch outright) nor by the two C-zero "
                     "rivals (whose singleton branch value is wrong): this is the "
                     "only case whose two branch values are each individually "
                     "correct. Witness conditions on the overlap (modulusIsPrime p ≠ "
                     "true, a % p = 0, compositeValidated, rootSetIn … ≠ [0]), "
                     "derives clause `h.2.2.2.2` FIRST and contradicts it with the "
                     "impl reduced only inside the `absurd`, so gold fails on the "
                     "claim. Varies the target binder into the zero-target "
                     "sub-domain of the NON-single-prime regime — a point no other "
                     "case in this battery reaches.",
        "witness": _W_ZERO_FIRST,
    },
    {
        "id": "drop-unit-base-roots",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_UNIT, "  return ([] : List ℤ)"),
        "refinement": "A patch that reorders the dispatch but drops the call on the "
                      "path it did not touch — the single-prime, non-zero-target "
                      "path — returning nothing there. The regression is outside the "
                      "sole FAIL_TO_PASS (which reaches the solver only with "
                      "non-single-prime moduli), so this rival WOULD pass the F2P; "
                      "it breaks PASS_TO_PASS instead, where single-prime moduli "
                      "with a non-zero target are asserted to yield their full root "
                      "lists (e.g. a fourth-power congruence over a 17-element field "
                      "has four roots, and a modular-solveset case pins that image "
                      "set exactly). So it does not RESOLVE either: 'resolved' is "
                      "F2P plus P2P. Recorded because the verify-does-not-imply-"
                      "resolve argument for this rival rests on P2P rather than on "
                      "the F2P, unlike every other rival here.",
        "rationale": "REJECT from (C-res) `modulusIsPrime p → a % p ≠ 0 → result = "
                     "primeUnitRoots a n p`, the clause pinning the UNCHANGED path. "
                     "Returning [] is sound vacuously but ≠ the unit-base solver's "
                     "list whenever that list is non-empty, so the clause is "
                     "unprovable. This is the only rival attacking C-res, which the "
                     "rest of the battery leaves to the positives; it closes that "
                     "gap so no clause of problem_spec_nthrootMod is defended by "
                     "verify-cases alone. Witness conditions on the single-prime "
                     "NON-zero-target sub-domain with a non-empty unit-root list "
                     "(modulusIsPrime p = true, a % p ≠ 0, primeUnitRoots … ≠ []) "
                     "and refutes via `h.2.2.1`; it fails on gold. Varies the target "
                     "binder into the complement of the zero-target sub-domain — the "
                     "one sub-domain of the single-prime regime no other case "
                     "reaches.",
        "witness": _W_DROP_UNIT,
    },
    {
        "id": "decline-off-regime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_NP,
                        "    if dispatchValidated a n p then\n"
                        "      return implementation_nthrootModComposite a n p\n"
                        "    return ([] : List ℤ)"),
        "refinement": "A patch that solves a non-single-prime modulus only where "
                      "the report is provably exact and REPORTS NOTHING for "
                      "every other such modulus. It is the "
                      "sharpest verify-but-not-resolve shape available, because the "
                      "completeness clause it does satisfy is exactly the one a "
                      "regime-guarded spec states — so a spec whose only "
                      "non-single-prime obligation is guarded by the regime cannot "
                      "see it at all. The real routine never declines: it reports a "
                      "non-empty list for every non-single-prime modulus whose "
                      "congruence has a solution (measured with zero violations over "
                      "61146 exhaustive off-regime inputs and 80000 fuzzed "
                      "non-single-prime inputs). HONEST SCOPE NOTE, because it is "
                      "what keeps this case from overclaiming: every modulus the "
                      "graded surface actually reaches lies INSIDE the regime (all "
                      "seven distinct solver call sites of the failing test are "
                      "regime-admitted, the quadratic congruence over a modulus with "
                      "a fifth power of two in it via the exponent-two leg), so a "
                      "faithful patch of this shape would still pass the graded "
                      "tests. This case is therefore recorded as a spec that is "
                      "DELIBERATELY STRONGER than the graded surface on this "
                      "sub-domain, not as a would-not-resolve rival: the spec "
                      "asserts a property the real function measurably has, and this "
                      "rival measurably lacks, which is the direction of strength "
                      "the benchmark wants even where the tests are silent.",
        "rationale": "REJECT from the UNCONDITIONAL non-single-prime report clause "
                     "`¬ modulusIsPrime p → reportsRootsFor a n p result`, whose "
                     "third conjunct (the report's LENGTH equals the number of "
                     "solutions of the congruence) forbids "
                     "an empty report whenever the grounded root set is non-empty. This is the only case in the battery "
                     "that lives OUTSIDE the regime: on that "
                     "sub-domain the exact-set clause says nothing and soundness is "
                     "satisfied vacuously by [], so the solution-counting obligation "
                     "is the sole thing standing between the spec and this rival. "
                     "Witness conditions on `dispatchValidated a n p = false` with a "
                     "non-empty grounded root set, derives the report clause FIRST "
                     "and contradicts its solution count with the impl reduced "
                     "only inside the `absurd`, so gold fails on the claim rather "
                     "than on a value equation. Varies the regime binder into its "
                     "COMPLEMENT — a sub-domain no other case in this battery "
                     "reaches.",
        "witness": _W_OFFREGIME_EMPTY,
    },
    {
        "id": "reverse-composite-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_COMP, "  return (rootSetIn a n m).reverse"),
        "refinement": "A patch whose root assembly emits the "
                      "residues in DESCENDING order — a plausible "
                      "near-miss, since the SET it reports is exactly right and only "
                      "the enumeration order is wrong. The graded surface compares "
                      "the reported list against an ascending expectation and builds "
                      "an ordered union of image sets from it, so a descending report "
                      "yields the wrong object and the sole FAIL_TO_PASS fails. Every "
                      "value it returns is a genuine root and none is missing, so a "
                      "spec that only constrained membership would wrongly accept it. "
                      "It would NOT resolve.",
        "rationale": "REJECT from the ordering conjunct of the unconditional "
                     "non-single-prime report clause (`result.Pairwise (· < ·)`), and "
                     "independently from the exact-SEQUENCE clause inside the regime. "
                     "It is the ORDER rival for the report: the multiset of returned "
                     "values is complete and sound, so soundness and every "
                     "membership-level property survive and the rejection is "
                     "attributable to the enumeration order alone — a dimension no "
                     "other case here attacks (drop-last / duplicate change the "
                     "LENGTH, decline-off-regime changes emptiness). Witness "
                     "conditions on a non-single-prime modulus whose reversed root "
                     "set is not strictly increasing (i.e. it has at least two "
                     "members), derives the report clause FIRST and contradicts its "
                     "ordering half.",
        "witness": _W_REVERSED,
    },
    {
        "id": "quadratic-seam-reverse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_COMP,
                        "  if compositeValidated a n m then\n"
                        "    return rootSetIn a n m\n"
                        "  return (rootSetIn a n m).reverse"),
        "refinement": "A patch whose assembly is correct exactly where the "
                      "MODULUS-shaped side conditions hold and emits the "
                      "residues in descending order otherwise. The plausible "
                      "shape, because the two side conditions on the modulus are "
                      "the ones a careful implementer would key the ordered walk "
                      "off — and it is wrong, because the quadratic exponent is "
                      "handled by a dedicated square-root routine that delivers "
                      "the complete ORDERED set over every such modulus, with no "
                      "condition on repeated prime factors at all. The gap is "
                      "reachable by the graded surface, not merely by argument: "
                      "the failing test evaluates a quadratic congruence over a "
                      "modulus carrying a fifth power of two, whose repeated "
                      "prime divides the exponent — so both modulus-shaped side "
                      "conditions are FALSE there while the quadratic leg admits "
                      "it, and its eight in-range roots come back in descending "
                      "order. The graded surface compares the report against an "
                      "ascending expectation, so the sole FAIL_TO_PASS fails. "
                      "Every value it returns is a genuine root and none is "
                      "missing; only the enumeration order is wrong. It would NOT "
                      "resolve.",
        "rationale": "REJECT from (C-comp) `¬ modulusIsPrime p → dispatchValidated "
                     "a n p → result = rootSetIn a n p`, on the SEAM between the "
                     "helper's own regime predicate and the dispatch's: "
                     "`dispatchValidated` is strictly WIDER than "
                     "`compositeValidated` (it adds the quadratic-exponent leg "
                     "`n == 2`), so on that difference the helper's own exact-set "
                     "clause is silent while the dispatch's still binds. ADDED BY "
                     "AUDIT: every other rival here deviates either inside both "
                     "regimes or outside both, so none reaches this seam, and a "
                     "spec that guarded the dispatch clause by the narrower "
                     "predicate would admit this rival — that the WIDER predicate "
                     "is load-bearing is exactly what this case attests. "
                     "Soundness survives (the multiset of returned values is the "
                     "complete root set), and so does the unconditional report "
                     "clause's range and counting conjuncts, so the rejection is "
                     "attributable to the ordering/exact-sequence content on the "
                     "quadratic leg alone. Witness conditions on the seam "
                     "(modulusIsPrime p ≠ true, n = 2, compositeValidated = false, "
                     "and a root set that is not its own reverse), derives clause "
                     "`h.2.2.2.2` FIRST — supplying `dispatchValidated` from the "
                     "`n = 2` leg by computation — and contradicts it with the "
                     "impl reduced only inside the `absurd`. Measured: rival exit "
                     "0, gold exit 1 with the semantic `⊢ False`, flipped claim "
                     "exit 1 with `introN failed`, consistency probe leaves "
                     "`False` unsolved. Varies the EXPONENT binder — the one "
                     "binder no other reject case in this battery constrains.",
        "witness": _W_QUAD_SEAM,
    },
    {
        "id": "phantom-root-when-unsolvable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_NP,
                        "    let base := implementation_nthrootModComposite a n p\n"
                        "    if base.isEmpty then\n"
                        "      return [0]\n"
                        "    return base"),
        "refinement": "A patch that, rather than reporting nothing for a "
                      "non-single-prime modulus whose congruence has NO solution, "
                      "announces a residue anyway (the zero residue as a fallback). "
                      "The real routine reports nothing exactly when nothing solves "
                      "the congruence, and the graded surface builds an image set "
                      "from the report and compares it: a phantom residue enlarges "
                      "that set with a value that does not solve the equation. It "
                      "is complete (it never omits a real root) and it never "
                      "declines, so the one-sided never-decline obligation is "
                      "satisfied outright — only the solution COUNT sees it. The "
                      "phantom fires only where the congruence is unsolvable, a "
                      "sub-domain the graded tests do not reach, so like the other "
                      "two off-regime cases this is recorded as spec strength beyond "
                      "the test surface: the never-phantom direction is a property "
                      "the real function measurably has (zero violations over 234k+ "
                      "measured inputs) and this rival lacks.",
        "rationale": "REJECT from the counting conjunct of the unconditional "
                     "non-single-prime report clause (`result.length = (rootSetIn a "
                     "n p).length`), in the direction the never-decline half does not "
                     "cover: the rival's report has one entry where the grounded root "
                     "set has none. Soundness is guarded off the regime and the "
                     "exact-set clause says nothing there, and the never-decline "
                     "direction is satisfied outright, so this rival is invisible to "
                     "every other clause in the spec — it exists to attest that the "
                     "report clause COUNTS the solutions and is not merely a lower "
                     "bound. "
                     "Witness conditions on an EMPTY grounded root set under a "
                     "non-single-prime modulus, derives the report clause FIRST and "
                     "computes the rival's length against that empty count. Varies the root-set binder into "
                     "the UNSOLVABLE sub-domain — a sub-domain no other case here "
                     "reaches.",
        "witness": _W_PHANTOM,
    },
    {
        "id": "composite-oracle-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_NP,
                        "    if dispatchValidated a n p then\n"
                        "      return implementation_nthrootModComposite a n p\n"
                        "    return primeUnitRoots a n p"),
        "refinement": "A patch that, off the sub-domain where the report "
                      "is provably exact, hands the modulus straight to the "
                      "UNIT-BASE single-prime solver — a routine whose whole intended "
                      "domain is a single-prime modulus and which, handed a modulus "
                      "with a repeated prime factor, returns residues that do not "
                      "solve the congruence at all (a cubic congruence over eight "
                      "residues is reported to have a root that cubes to the wrong "
                      "value). Such a report is neither sound nor a solvability "
                      "decision, and on the graded surface it substitutes wrong "
                      "residues for the assembled ones. Like decline-off-regime "
                      "this rival's deviation lies OUTSIDE the sub-domain the graded "
                      "tests reach (every graded call site is regime-admitted), so "
                      "it is recorded as spec strength beyond the test surface "
                      "rather than as a would-not-resolve rival — the report it "
                      "produces is genuinely wrong about the real function, which is "
                      "what the spec must and does reject.",
        "rationale": "REJECT from the unconditional non-single-prime report clause. "
                     "The soundness clause (S) is guarded off the regime precisely "
                     "because the real routine emits non-roots there, so soundness "
                     "cannot reject this rival; the exact-set clause is silent "
                     "off-regime; and the callee's own soundness contract is claimed "
                     "ONLY for a single-prime modulus (its intended domain — on any "
                     "other the contract is FALSE of the real callee, so claiming it "
                     "would be an over-strong axiom), hence nothing about the echoed "
                     "list can be derived from it. The report clause is therefore the "
                     "only thing that speaks: the echoed list cannot be shown to "
                     "count the congruence's solutions. This is the "
                     "UNGROUNDED-ORACLE ECHO family on this carrier — the rival "
                     "delegates to a callee bound to a DIFFERENT domain instead of "
                     "computing over the actual modulus. Witness conditions on the "
                     "off-regime sub-domain with an empty grounded root set and a "
                     "non-empty echoed list, derives the report clause FIRST and "
                     "contradicts its solution count.",
        "witness": _W_ORACLE_ECHO,
    },
]


# ---------------------------------------------------------------------------
# NAGINI → LEAN ACCOUNTING.
#
# The nagini sibling ships 7 SPEC cases (1 soundness positive, 1 admissibility,
# 5 uniqueness rivals) plus 4 AXIOM_TESTS. This lean bundle models the SAME
# purely-functional core, split across TWO obligations — the public dispatch
# (problem_spec_nthrootMod) and the deep composite helper
# (problem_spec_nthrootModComposite) — over the same grounded surface (isRootIn,
# the deep set rootSetIn, the primeUnitRoots A-reference, compositeValidated).
# Every sibling case is accounted for below.
#
#   nagini case                   -> here
#   -----------------------------------------------------------------------
#   pos-reshape-local             -> pos-composite-accumulate
#                                    + pos-composite-loop            PORTED
#                                    (doubled: the sibling's reshape is an explicit
#                                     copy LOOP, so both the functional-fold and the
#                                     imperative-loop residue of it are shipped;
#                                     each is definitionally distinct from the
#                                     frozen body and RE-PROVES)
#   admiss-fshape                 -> admiss-joint-satisfiable    RE-AIMED
#   drop-zero-root                -> drop-zero-root              PORTED  (C-zero)
#   two-zeros-prime               -> two-zeros-prime             PORTED  (C-zero)
#   decline-composite             -> decline-composite           PORTED  (C-comp)
#   drop-last-composite-root      -> drop-last-composite-root    PORTED  (K-set)
#   duplicate-composite-root      -> duplicate-composite-root    PORTED  (K-set)
#   ax-sound-power_mod            -> (none)                      G-AX's job
#   ax-sound-rootsets             -> (none)                      G-AX's job
#   ax-sound-residue              -> (none)                      G-AX's job
#   ax-contain-composite          -> (none)                      G-AX's job
#   (no sibling)                  -> zero-target-before-regime   ADDED   (C-comp,
#                                    branch ORDER on the guard overlap; both branch
#                                    values individually correct)
#   (no sibling)                  -> drop-unit-base-roots        ADDED   (C-res)
#   (no sibling)                  -> quadratic-seam-reverse      ADDED BY AUDIT
#                                    (C-comp, the seam where dispatchValidated is
#                                     WIDER than compositeValidated: the quadratic
#                                     leg. Reachable at a graded input, and no
#                                     other rival deviates there.)
#
# DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class, and measured
#   rather than argued. This bundle sets no `loom.semantics.termination` option
#   (no lean bundle in the corpus does), so the total-carrier disposition applies:
#   a Lean `def` that does not terminate is REFUSED BY ELABORATION, and a
#   `partial def` (the only way to write one) is opaque with no equation lemmas.
#   Both were built. A structurally-recursive spinning helper fails at
#   `fail to show termination for implementation_nthrootModComposite.aux`, i.e.
#   the file does not elaborate at all rather than failing the obligation — a
#   variant the gate would read as rejected for a reason that is not the spec. A
#   `partial def` spin elaborates but its impl is irreducible, so the obligation
#   fails at `rfl`, and NO witness can refute it: the refutation would have to
#   name `spinComposite`, which `witness_scope_problems` correctly forbids
#   (variant-only vocabulary), and a witness stated only over the shared
#   vocabulary was built and does NOT hold of the rival (exit 1, `unsolved goals
#   … ⊢ False`), so it lands as `witness-unproven`. Recorded as a hole in what
#   this carrier can express, not as a class the battery has covered.
#
# OFF-REGIME COUNT-LEVEL CEILING — probed by audit, NOT a spec hole. An impl that
#   off the regime reports the first `k` canonical residues, `k` the number of
#   solutions, was built AND RE-PROVED (it verifies: in-range, strictly
#   increasing, right length, and soundness is guarded off the regime). That is
#   the deliberate ceiling refinement.md documents and measures — 7 such
#   count-preserving relabelings were carried back to faithful patches and all 7
#   RESOLVE, because every graded call site lies INSIDE the regime. So it is a
#   correct echo, not a counterexample to verify ⇒ correct, and not shippable as a
#   reject case. Recorded here so the next reader does not re-spend the builds.
#
# CLAUSE / BINDER COVERAGE.
#   * problem_spec_nthrootMod (dispatch):
#       (S) soundness — DEFENDED by both positives; not independently ATTACKED by
#           design: every reject rival PRESERVES soundness (each returned value is
#           a genuine root) so the rejection is attributable to COMPLETENESS
#           alone. A rival violating soundness would test a WEAKER property than
#           the ones shipped.
#       (C-zero) attacked by drop-zero-root (UNDER, length 0) and two-zeros-prime
#           (OVER, length 2) — both sides of the exact singleton.
#       (C-comp) attacked by decline-composite (whole branch empty) and by
#           zero-target-before-regime (branch ORDER: on the overlap of the
#           zero-target and non-single-prime guards the rival returns the singleton
#           instead of the whole set, with BOTH branch values individually correct —
#           so the rejection is attributable to the order, which no other case here
#           probes).
#       (C-res) `isPrime p ∧ a%p≠0 → result = primeUnitRoots` — attacked by
#           drop-unit-base-roots. This clause encodes the UNCHANGED single-prime
#           path, so the verify-does-not-imply-resolve argument for its rival rests
#           on PASS_TO_PASS rather than on the sole F2P: the failing test reaches
#           the solver only with non-single-prime moduli, while single-prime moduli
#           with a non-zero target are asserted (with their full root lists) in the
#           passing suite. 'resolved' is F2P *and* P2P, so the rival does not
#           resolve; recording WHICH list it breaks is what keeps the argument
#           honest. The nagini sibling leaves its C-prime clause unattacked; this
#           port does not, so every clause of both obligations has a rival rather
#           than only a positive defending it.
#   * problem_spec_nthrootModComposite (helper):
#       (K-set)   attacked by drop-last (STRICT SUBSET) and duplicate (STRICT
#           SUPERSET) — both sides of the exact-set equality.
#       (K-sound) `∀ x ∈ result, isRootIn a n m x` — DEFENDED by both accumulation
#           positives; deliberately PRESERVED by both K-set rivals (each returned
#           value is a member of the grounded set, hence a root), for the same
#           "soundness is not enough" reason as (S).
#   * Binders `a`, `n`, `m`/`p` are all named across the reject witnesses. The
#     modulus binder is varied across BOTH regimes (single-prime for the C-zero and
#     C-res rivals, non-single-prime for decline and for the order rival) and the
#     target binder across all THREE sub-domains the dispatch distinguishes:
#     zero-target under a single prime (drop-zero, two-zeros), zero-target under a
#     NON-single-prime modulus (the order rival — the guard overlap), and
#     non-zero-target under a single prime (drop-unit-base-roots), plus the
#     non-empty-root-set sub-domain of the helper. Because the modulus
#     predicate is opaque the dispatch witnesses quantify over a/n/p under
#     hypotheses rather than at literals, so the coverage tool reads them as
#     unreadable and falls back to the by-name signal (all named, no gap); a
#     machine-computed `pts` is not available for a conditioned witness, as on the
#     other opaque-carrier ports (sympy-23534, and this instance's velvet sibling).
#
# VACUOUS — frame/permission-mutation: no read-only heap input, no aliasing, no
#   mutable binder on this referentially-transparent backend; no substitute probe
#   fabricated (per the porting map, and matching the nagini surface's own note).
#
# AXIOM_TESTS: dropped — G-AX's job; the G-PBT gate ignores AXIOM_TESTS.
AXIOM_TESTS = []
