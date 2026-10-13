"""properties.py — G-PBT falsification battery for sympy__sympy-19040 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct extFactor`` obligation survives with a byte-identical
statement) and swaps in a candidate impl; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: elaborates against the rival, FAILS against the second subject,
and — for conditioned witnesses — its binders are jointly satisfiable). Here the
second subject is the ``witness_reference`` (a loop-free VERIFYING impl of this
same spec), NOT the frozen solution, because the frozen impl's loop makes its
exit code uninformative for witnesses of this shape — see WITNESS MECHANICS.

DEFENDED SURFACE (``extFactor (lc poly : Int) return (out : List Int)``):
  two ``require`` clauses delimiting the DOMAIN and four ``ensures`` clauses
  pinning the result to the COMPLETE factorisation OF THE INPUT:

    (R1) require noRepeatedFactor poly = true             (domain, first half)
    (R2) require isConstant poly = false
           → hasMainDegree poly = true                   (domain, second half)
    (C0) out = expectedFactors poly                            (the abbreviation)
    (Ck) isConstant poly = true → out = []                       (constant input)
    (C1) isConstant poly = false → (factorList poly).length ≥ 2
           → out = factorList poly                                  (splitting)
    (C2) isConstant poly = false → ¬ (factorList poly).length ≥ 2
           → out = lone poly                                    (non-splitting)

  ``expectedFactors poly`` is definitionally the ``if isConstant poly then [] else
  if …≥2 then factorList poly else lone poly`` selection, so C0 is discharged by
  Ck+C1+C2 together; the three load-bearing, independently-attackable clauses are
  Ck, C1 and C2. The differential the real fix encodes is WHICH polynomial the
  factoring is applied to: the INPUT (``factorList poly``) rather than an
  auxiliary reduced identity (``factorList (otherPoly poly)``).

  THE DOMAIN RESTRICTION (R1 ∧ R2) IS ATTACKED FROM BOTH SIDES, because a
  ``require`` is the one edit that can silently gut a battery: too strong and the
  graded behaviour leaves the modelled domain, too weak and the frozen impl cannot
  be proven total. Both directions are measured here rather than argued, and each
  half gets its OWN liveness control, so neither can quietly become decoration.
    * NOT DEAD: ``pos-control-domain-guard`` verifies ONLY because R1 is assumed
      and ``pos-control-main-degree-guard`` verifies ONLY because R2 is assumed —
      each has an ``else`` arm that returns a value violating every clause and
      reachable exactly when its half of the domain fails. Drop that half from the
      spec and the corresponding case flips to rejected, so the two cases witness
      that BOTH halves are genuinely available to the proof.
    * NOT VACUOUS: R1 and R2 are hypotheses about uninterpreted ``Bool``s, so they
      cannot be self-contradictory, and the gate re-proves that for every reject
      case — each conditioned witness carries BOTH
      ``(hpre : noRepeatedFactor poly = true)`` and
      ``(hmd : hasMainDegree poly = true)`` among its binders and the consistency
      probe must FAIL to derive ``False`` from them. Eight independent probes. Were
      the conjunction unsatisfiable, the eight reject rivals below would VERIFY and
      the gate would report SPEC-TOO-WEAK.
    * NOT AN ESCAPE HATCH: every reject rival is refuted at a point where R1 AND R2
      HOLD (both are assumed as binders and the witness discharges the method
      precondition from them), so no rival gets in by living outside the domain.

  THE CONSTANT CLAUSE (Ck) IS THE OBLIGATION THIS BATTERY GAINED, and
  ``weak-ignores-constant-guard`` is its dedicated rival: that rival is exactly
  the selection-only impl (recover, else fall back to the single representative)
  with no constant test at all — i.e. the impl an earlier revision of this spec
  DEMANDED. It is now REJECTED, which is the machine-checked statement that Ck
  adds an obligation rather than relaxing one.

  THE CARRIER IS AN OPAQUE-AXIOM ORACLE. ``poly`` is an uninterpreted ``Int``
  identity and ``factorList`` / ``lone`` / ``otherPoly`` / ``isConstant`` /
  ``noRepeatedFactor`` / ``hasMainDegree`` are opaque axioms; only
  ``loneLen : ∀ p, (lone p).length =
  1`` and the structural shape of the clauses are transparent. There is no
  literal ``poly`` whose ``factorList`` length or ``isConstant`` value the
  elaborator can decide, so a rival gated behind ``…length ≥ 2`` or behind
  ``isConstant poly`` (or attacked through the CONTENT of an opaque list) is
  refuted at a point described by HYPOTHESIS — conditioning on the carrier —
  while the length-1 fact (``loneLen``) and the sequence shape are attacked
  oracle-free.

ADVERSARIAL READ of the classes (nagini design doc → here):
  * FRAME-MUTATION / permission rivals — VACUOUS. Already N/A on nagini (both
    inputs are ``int`` value types, no ``Acc(...,1/2)`` permission). Vacuous here
    for the stronger backend reason too: Velvet is referentially transparent and
    this bundle declares no ``mut`` PARAMETER (the loop's ``mut`` locals are not
    inputs), so there is no read-only input to overwrite and no substitute probe
    to build. Not fabricated.
  * DIVERGENCE / non-termination — VACUOUS AS A REJECT CASE on this bundle, and
    the reason is measured, not argued. This bundle carries ``set_option
    loom.semantics.termination "total"``, under which the verifier DEMANDS a
    decreasing measure on every loop. Three diverging rivals were built against
    the real verifier — a ``while True do pure ()`` prefix ahead of gold's answer,
    the same prefix returning the unambiguously wrong ``[]``, and gold's own body
    with its two ``decreasing i`` clauses deleted — and all three are REJECTED
    (exit 1) with ``error: Decreasing annotations are required in total
    correctness semantics``. So the spec does NOT admit a diverging impl and there
    is no hole to report here; the earlier claim in this file that a diverging
    impl "WOULD verify vacuously" described ``partial`` semantics and is false of
    this bundle. It is false of every velvet bundle: all 500 set ``"total"`` and open
    ``TotalCorrectness``, none sets ``"partial"``, and the ``set_option`` elaborator
    itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``), so the option and the ``open``
    cannot disagree. A fourth rival pins the point past any doubt about the
    annotation linter: a prefix that DOES carry a measure, but a constant one
    (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``, body
    ``q := q``), is REJECTED on the measure's own descent goal - ``case
    «decreasing_1: q»``, residual ``⊢ q < q``.
    It nevertheless cannot SHIP as an ``expect="reject"`` case, and a THIRD audit
    corrected the reason: the previous revision claimed the rejection "fires on
    the ``method`` command itself, so the whole file is uncompilable, including
    the witness file", and that is true of only ONE of the two diverging shapes.
    Both were rebuilt:
      (a) NO annotation at all (``while q > 0 / invariant / done_with``, no
          ``decreasing``). The linter throws from the ``decreasing`` elaborator
          during the ``method`` command, so the variant AND the
          obligation-stripped witness file both fail (exit 1) with ``Decreasing
          annotations are required in total correctness semantics`` — the trivial
          ``example : (1:Nat) + 1 = 2 := by decide`` included. Here the previous
          claim holds.
      (b) A CONSTANT measure (``decreasing q`` with body ``q := q``). The
          annotation is present, so the ``method`` command elaborates and the
          rejection lands inside ``prove_correct`` — on the descent goal ``case
          «decreasing_1: q»``, residual ``⊢ q < q``. ``witness_file`` STRIPS
          ``prove_correct``, so the witness file compiles: the trivial witness
          builds at exit 0 against this rival. The previous claim that no witness
          file compiles is FALSE of shape (b) and has been removed.
    So the class is omitted for a DIFFERENT and stronger reason, which was also
    measured. What no witness can do is ATTRIBUTE the rejection to termination.
    Every witness here speaks to the method's partial-correctness ``triple``
    (``method`` opens ``PartialCorrectness``), and a diverging program satisfies
    that triple vacuously — there is no post-state to constrain. Built against
    shape (b) with all answers CORRECT and divergence the only defect, the
    refutation witness fails on the RIVAL (exit 1, ``unsolved goals``: ``hh``
    stays an un-normalised ``wp (… forIn Lean.Loop.mk 1 …)`` that ``wp_pure``
    cannot touch), which the gate records as ``witness-unproven`` ⇒ INCONCLUSIVE
    ⇒ MALFORMED-TESTS. Both polarities of the same claim fail identically against
    it, so the rival-side exit code carries no information about the claim either.
    A rival that PAIRS shape (b) with a wrong answer does clear all three builds
    (rival 0, reference 1, probe 1) — but its witness refutes the WRONG ANSWER,
    i.e. it attests to C2, which four rivals already cover, while attesting
    nothing about the measure. Shipping it would misattribute a C2 refutation to
    the termination obligation, which is the precise failure mode the witness
    requirement exists to prevent, so it is deliberately NOT shipped.
    The disposition is therefore: the spec genuinely REFUSES divergence (the
    module build rejects both shapes, so there is no hole to escalate and no
    spec_holes entry), but the rejection is attested by the MODULE build alone and
    is not expressible as a witnessed reject case on this carrier. The nagini
    sibling carries no ``diverge-*`` / ``nonterm-*`` case either (its impl is a
    bounded ``while``), so nothing was dropped in the port.
    Note this is a statement about the MODEL, not about the real callee: the real
    routine's recovery search is not guaranteed to terminate outside the modelled
    domain, which is exactly why the spec carries (R) and asserts nothing there.
  * CONSTANT clause Ck (an input with no factor content) — attacked by
    ``weak-ignores-constant-guard`` (no constant test at all, so a constant input
    is answered with a non-empty list).
  * COMPLETENESS clause C1 (splitting input) — attacked by the actual pre-patch
    behaviour (factoring applied to the auxiliary reduced identity), by the
    collapse-to-one-factor echo, and by the drop-the-last-factor off-by-one.
  * FALLBACK clause C2 (non-splitting input) — attacked by the unconditional
    materialise-the-recovery echo, by the branch whose one-element fallback is
    built from the auxiliary identity instead of the input, by the input-echoed
    singleton, and by the empty factorisation. That last one also pins the
    direction of the constant clause: admitting ``[]`` for a CONSTANT input did
    NOT make ``[]`` an acceptable answer anywhere else.
  * UNGROUNDED-ORACLE — N/A as an attack. ``factorList`` / ``lone`` /
    ``isConstant`` / ``noRepeatedFactor`` ARE the opaque oracles; their properties
    are pinned by the ``axioms`` region and validated executably by G-AX
    (axiom_check.py). We carry honest cheapest reshapes as POSITIVE CONTROLS
    instead of a wrong echo.

WITNESS MECHANICS. The velvet tester path
(``extract_program_for`` → ``derive_tester_for`` → ``…Tester args = false``) is
DEAD here for the same reason as the astropy sibling: the tester extracts an
EXECUTABLE program, but ``extFactor`` depends on the opaque axioms and has no
executable content, and the postcondition's ``Decidable`` instance stalls on
``factorList``/``lone``. Every witness here instead speaks DIRECTLY to the
method's partial-correctness ``triple`` (the ``method`` command opens
``PartialCorrectness DemonicChoice``), at the method's OWN precondition:
``triple (noRepeatedFactor poly = true ∧ (isConstant poly = false →
hasMainDegree poly = true)) (extFactor lc poly) …`` — the method's OWN
precondition, discharged from the witness's ``hpre`` and ``hmd`` binders as
``hh ⟨hpre, fun _ => hmd⟩``. Each rival's body is ``return <expr>`` (possibly
behind an ``if``), so after ``simp only [extFactor, triple]`` and ``hh hpre`` the
weakest precondition reduces: ``wp_pure`` fires on a bare ``return`` (with the
guard-reducing rewrites supplied first for the branch-structured rivals), leaving
a decidable fact about that concrete result — a length (refuted via ``loneLen`` /
``List.length_dropLast`` and ``omega``) or an equality of two opaque lists
(refuted by a separation binder).

  THE SECOND SUBJECT IS ``witness_reference``, NOT THE FROZEN IMPL, and this is
  the load-bearing correction an audit made to this battery. The frozen
  ``extFactor`` materialises its result with a ``while`` loop, so its ``wp`` is
  an un-normalised ``forIn Lean.Loop.mk`` term and the FIRST reduction step of
  every witness (``wp_pure`` / ``if_pos`` / ``if_neg``) fails to match — before
  any spec clause is ever consulted. Measured: a witness asserting a claim that
  is violated by the frozen impl TOO (so it discriminates nothing and must be
  recorded ``witness-vacuous``) elaborated against the rival (exit 0) and failed
  against the frozen impl (exit 1) with the byte-identical first-rewrite error,
  and ``_check_witness`` recorded it as ``rejected (witness refutes the rival)``.
  The frozen impl's exit code therefore carries NO information about any witness
  of this shape, and a gold-side failure at that step is a syntactic mismatch on
  the loop term rather than a satisfied spec. It is the same un-normalised-loop
  defect class the gate screens for elsewhere, arriving as a ``rewrite`` failure
  that none of its four screens match.
  So every reject case names ``witness_reference``: a LOOP-FREE impl of this same
  spec (``return expectedFactors poly``) which the gate independently checks
  shares the frozen spec and VERIFIES before refuting the witness against it. An
  impl the verifier accepts cannot violate its own spec, so a genuine witness
  must still fail there — and against a reducible subject it now fails
  SEMANTICALLY, on the reduced clause (``hcon : … → expectedFactors poly = …``),
  which is the refutation the gate is supposed to be attesting to. Each of the
  eight was inspected on the reference side to confirm the failure lands AT OR
  AFTER the step that applies ``hcon`` (the reduced clause) — an ``omega`` with no
  contradiction, or a ``simp`` that cannot close a goal that is false only of a
  wrong impl — and never on the first rewrite. For the two guard-structured
  rivals the guard-reducing rewrite is supplied as a ``simp only`` argument rather
  than a ``rw``, so a guard the reference does not have leaves the argument merely
  unused instead of aborting the script before the clause is read.

Every conditioned witness names only opaque-guard binders whose joint
satisfiability the gate's consistency probe confirms (all built three ways:
rival exit 0, reference exit ≠ 0, probe exit ≠ 0). No banned token
(sorry/admit/native_decide/axiom).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries five
axiom-soundness / containment probes over the real sympy callees; that is
G-AX's job (axiom_check.py / mapping.md) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-19040"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body. Every variant below
# ---- replaces exactly this text, so each edit lies wholly inside the one
# ---- -- impl-start .. -- impl-end region and same_spec holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back\n"
    "    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`\n"
    "    -- (the square-free part) is computed but NOT fed to the factoring.\n"
    "    let _other := otherPoly poly\n"
    "    if isConstant poly then\n"
    "      -- constant argument: reported with no factors at all (`return lc, []`).\n"
    "      return ([] : List Int)\n"
    "    else\n"
    "      let images := factorList poly\n"
    "      let mut result : List Int := []\n"
    "      if images.length ≥ 2 then\n"
    "        -- two or more elements: the complete factor list of the input.\n"
    "        let mut i := images.length\n"
    "        while i > 0\n"
    "          invariant 0 ≤ i ∧ i ≤ images.length\n"
    "          invariant result = images.drop i\n"
    "          done_with i = 0\n"
    "          decreasing i\n"
    "        do\n"
    "          result := images[i - 1]! :: result\n"
    "          i := i - 1\n"
    "      else\n"
    "        -- single element: the one-element fallback `lone poly`.\n"
    "        let blob := lone poly\n"
    "        let mut i := blob.length\n"
    "        while i > 0\n"
    "          invariant 0 ≤ i ∧ i ≤ blob.length\n"
    "          invariant result = blob.drop i\n"
    "          done_with i = 0\n"
    "          decreasing i\n"
    "        do\n"
    "          result := blob[i - 1]! :: result\n"
    "          i := i - 1\n"
    "      return result\n"
    "    -- impl-end"
)

assert _IMPL in _BASE, "frozen impl region drifted; update _IMPL"

# ---- proof-body anchor. Only the `prove_correct extFactor by` TACTIC BODY may
# ---- change (the header/statement stays byte-identical); one variant reshapes
# ---- the source-selection into a single local and needs the fold lemma applied
# ---- at the selecting `if` expression.
_PROOF = (
    "prove_correct extFactor by\n"
    "  loom_solve\n"
    "  all_goals\n"
    "    first\n"
    "      | (rw [drop_step (factorList poly) i (by omega) (by omega)]; simp_all)\n"
    "      | (rw [drop_step (lone poly) i (by omega) (by omega)]; simp_all)"
)

assert _PROOF in _BASE, "frozen proof body drifted; update _PROOF"


def _impl(body):
    """Frozen file with the impl region replaced by `body` (marker-wrapped)."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + body + "\n    -- impl-end")


# ===========================================================================
# POSITIVE CONTROLS (soundness, expect verify) — a correct impl MUST verify,
# else SPEC-TOO-STRONG. Ports nagini pos-control-reorder / pos-control-shared-loop.
# ===========================================================================

# pos-control-branch-reorder: structurally different but correct. Tests the
# NON-splitting branch FIRST (guard re-expressed as `images.length < 2`, lone
# branch hoisted ahead of the recovery branch). Every value computed per branch
# is unchanged; the frozen bullet-script still discharges each loop goal.
_POS_REORDER = (
    "    let _other := otherPoly poly\n"
    "    if isConstant poly then\n"
    "      return ([] : List Int)\n"
    "    else\n"
    "      let images := factorList poly\n"
    "      let mut result : List Int := []\n"
    "      if images.length < 2 then\n"
    "        let blob := lone poly\n"
    "        let mut i := blob.length\n"
    "        while i > 0\n"
    "          invariant 0 ≤ i ∧ i ≤ blob.length\n"
    "          invariant result = blob.drop i\n"
    "          done_with i = 0\n"
    "          decreasing i\n"
    "        do\n"
    "          result := blob[i - 1]! :: result\n"
    "          i := i - 1\n"
    "      else\n"
    "        let mut i := images.length\n"
    "        while i > 0\n"
    "          invariant 0 ≤ i ∧ i ≤ images.length\n"
    "          invariant result = images.drop i\n"
    "          done_with i = 0\n"
    "          decreasing i\n"
    "        do\n"
    "          result := images[i - 1]! :: result\n"
    "          i := i - 1\n"
    "      return result"
)

# pos-control-shared-loop: local-variable RESHAPE — select the source sequence
# for ALL THREE cases into ONE local `src`, then materialise with ONE shared loop
# (gold uses an early return plus two loops). Structurally distinct while
# respecting every clause; the ONE extra fold-step case (the loop now runs over
# the three-way selecting `if`) is closed by naming that expression to
# `drop_step`. The `prove_correct extFactor` STATEMENT is byte-identical; only
# the tactic body gains one `first` alternative.
_POS_SHARED_SRC = ("if isConstant poly then ([] : List Int) "
                   "else if (factorList poly).length ≥ 2 then factorList poly "
                   "else lone poly")
_POS_SHARED_IMPL = (
    "    let _other := otherPoly poly\n"
    "    let src := " + _POS_SHARED_SRC + "\n"
    "    let mut result : List Int := []\n"
    "    let mut i := src.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ src.length\n"
    "      invariant result = src.drop i\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      result := src[i - 1]! :: result\n"
    "      i := i - 1\n"
    "    return result"
)
_POS_SHARED_PROOF = (
    "prove_correct extFactor by\n"
    "  loom_solve\n"
    "  all_goals\n"
    "    first\n"
    "      | (rw [drop_step (" + _POS_SHARED_SRC + ") i (by omega) (by omega)]; simp_all)\n"
    "      | (rw [drop_step (factorList poly) i (by omega) (by omega)]; simp_all)\n"
    "      | (rw [drop_step (lone poly) i (by omega) (by omega)]; simp_all)"
)
_POS_SHARED = _swap(_impl(_POS_SHARED_IMPL), _PROOF, _POS_SHARED_PROOF)

# pos-control-domain-guard: the DOMAIN control. A correct impl on the modelled
# domain whose `else` arm — reachable exactly when the `require` FAILS — returns a
# value that violates every clause. It can only verify if the verifier genuinely
# ASSUMES `noRepeatedFactor poly = true`, so it is the machine-checked statement
# that the domain restriction is live rather than decorative: delete the `require`
# from the spec and this case flips to rejected. (The complementary direction —
# that the restriction is not self-contradictory, hence not a vacuity hatch — is
# carried by the eight consistency probes on the reject witnesses.)
_POS_DOMAIN_GUARD = (
    "    let _other := otherPoly poly\n"
    "    if noRepeatedFactor poly then\n"
    "      return expectedFactors poly\n"
    "    else\n"
    "      -- unreachable under the declared domain; a value no clause admits.\n"
    "      return ([poly] : List Int)"
)


# pos-control-main-degree-guard: the SECOND domain control, one per `require`. A
# correct impl on the modelled domain whose innermost `else` arm — reachable
# exactly when a NON-constant argument fails `hasMainDegree poly = true`, i.e.
# exactly when R2 fails — returns a two-element list of the input identity, which
# no clause admits. It can only verify if the verifier genuinely ASSUMES R2, so it
# is the machine-checked statement that the second half of the domain restriction
# is live rather than decorative: delete that `require` from the spec and this case
# flips to rejected.
_POS_MAIN_DEGREE_GUARD = (
    "    let _other := otherPoly poly\n"
    "    if isConstant poly then\n"
    "      return ([] : List Int)\n"
    "    else if hasMainDegree poly then\n"
    "      return expectedFactors poly\n"
    "    else\n"
    "      -- unreachable under the declared domain; a value no clause admits.\n"
    "      return ([poly, poly] : List Int)"
)


# pos-control-fallback-via-loneLen: ADDED BY AUDIT (attack E). The three positives
# above all produce the fallback as the literal term `lone poly` — syntactically
# the same expression the clause names — so none of them exercises the ONE
# transparent fact the axiom region publishes about it (`loneLen : ∀ p,
# (lone p).length = 1`). This reshape produces the fallback as `(lone poly).take 1`
# instead, which is equal to `lone poly` only THROUGH `loneLen`, so the case
# verifies only if the spec admits a correct impl whose fallback agrees
# EXTENSIONALLY rather than syntactically. Found while probing for SPEC-TOO-STRONG:
# the reshape is faithful (`take 1` of a length-1 list is that list) but the frozen
# bullet-script does NOT close it — `loom_solve <;> simp_all [expectedFactors]`
# leaves `⊢ … List.take 1 (lone poly) = lone poly`, so the residual goal was a
# candidate soundness hole until the length fact was supplied. It closes with one
# `have` in the tactic body (`List.take_of_length_le` on `loneLen`), which is what
# demotes it from a hole to a positive control: the spec is not too strong, it just
# requires the published axiom to be used. Keeping it as a case pins that, so a
# future respec that drops or weakens `loneLen` flips this to rejected instead of
# silently narrowing the admissible impls to the syntactic ones.
_POS_FALLBACK_TAKE = "    return " + _POS_SHARED_SRC.replace(
    "else lone poly", "else (lone poly).take 1")
_POS_FALLBACK_TAKE_PROOF = (
    "prove_correct extFactor by\n"
    "  -- `(lone poly).take 1 = lone poly` holds only THROUGH `loneLen`; supplying\n"
    "  -- it is what lets the frozen script close this reshape.\n"
    "  have ht : (lone poly).take 1 = lone poly := by\n"
    "    have := loneLen poly\n"
    "    exact List.take_of_length_le (by omega)\n"
    "  loom_solve <;> simp_all [expectedFactors]"
)
_POS_FALLBACK_TAKE_MOD = _swap(_impl(_POS_FALLBACK_TAKE), _PROOF,
                               _POS_FALLBACK_TAKE_PROOF)


# ---- ADMISSIBILITY at a CONCRETE input. The analogue of the nagini
# ---- discharge-a-callee-precondition probe is that the clause set be
# ---- SATISFIABLE at exactly an F2P-shaped input, and the way to test that is to
# ---- discharge it there as a `have` before closing the frozen obligation
# ---- verbatim. So this variant pins `poly := 1` (the identity mapping.md §3
# ---- assigns the F2P `test_issue_5786` shape) and proves, at that input, ALL
# ---- THREE arms of the selection: the constant arm reduces the post-image to
# ---- `[]`, the splitting arm to `factorList 1`, and the non-splitting arm to
# ---- something of length 1. Any arm being unprovable AT THAT INPUT would mean
# ---- the post-image is unsatisfiable exactly where the F2P test lives —
# ---- PRECOND/SPEC-UNSATISFIABLE — while the frozen impl alone (which is what an
# ---- earlier revision of this case shipped) re-tests only what G-GOLD already
# ---- covers. The `have`s live in the TACTIC BODY, not at top level: a new
# ---- top-level `theorem` is out of variant scope ("a variant reproves the SAME
# ---- obligations"), measured.
_ADMISS_PROOF = (
    "prove_correct extFactor by\n"
    "  -- ADMISSIBILITY at the concrete F2P-shaped input (mapping.md §3 assigns\n"
    "  -- the F2P `test_issue_5786` polynomial the identity 1): the clause set is\n"
    "  -- SATISFIABLE there, on ALL THREE arms of the selection.\n"
    "  have hconst : isConstant 1 = true → expectedFactors 1 = [] :=\n"
    "    fun h => expectedFactors_const 1 h\n"
    "  have hsplit : isConstant 1 = false → (factorList 1).length ≥ 2 →\n"
    "      expectedFactors 1 = factorList 1 :=\n"
    "    fun hc h => expectedFactors_split 1 hc h\n"
    "  have hlone : isConstant 1 = false → ¬ (factorList 1).length ≥ 2 →\n"
    "      (expectedFactors 1).length = 1 :=\n"
    "    fun hc h => by rw [expectedFactors_lone 1 hc h]; exact loneLen 1\n"
    "  have hjoint : (isConstant 1 = true ∧ expectedFactors 1 = [])\n"
    "      ∨ (isConstant 1 = false ∧ (factorList 1).length ≥ 2\n"
    "          ∧ expectedFactors 1 = factorList 1)\n"
    "      ∨ (isConstant 1 = false ∧ ¬ (factorList 1).length ≥ 2\n"
    "          ∧ (expectedFactors 1).length = 1) := by\n"
    "    by_cases hk : isConstant 1 = true\n"
    "    · exact Or.inl ⟨hk, hconst hk⟩\n"
    "    · have hk' : isConstant 1 = false := by simp_all\n"
    "      by_cases h : (factorList 1).length ≥ 2\n"
    "      · exact Or.inr (Or.inl ⟨hk', h, hsplit hk' h⟩)\n"
    "      · exact Or.inr (Or.inr ⟨hk', h, hlone hk' h⟩)\n"
    "  clear hconst hsplit hlone hjoint\n"
    "  loom_solve\n"
    "  all_goals\n"
    "    first\n"
    "      | (rw [drop_step (factorList poly) i (by omega) (by omega)]; simp_all)\n"
    "      | (rw [drop_step (lone poly) i (by omega) (by omega)]; simp_all)"
)
_ADMISS = _swap(_BASE, _PROOF, _ADMISS_PROOF)


# ---- WITNESS REFERENCE: the second subject every reject case is refuted
# ---- against, replacing the frozen impl. See WITNESS MECHANICS above: the
# ---- frozen impl's `while` leaves an un-normalised `forIn Lean.Loop.mk` term,
# ---- so a witness's first reduction step fails there for SYNTACTIC reasons and
# ---- its exit code discriminates nothing (measured: a deliberately vacuous
# ---- witness passed both halves against it). This impl is loop-free, so `wp`
# ---- reduces to `wp (pure (expectedFactors poly)) …` and a witness fails on it
# ---- only by being refuted on the CLAUSE. It is a correct impl of the frozen
# ---- spec — the same shape as a positive control — and the gate re-checks both
# ---- of those facts (shares the spec, and VERIFIES) before using it.
_REF_IMPL = "    return expectedFactors poly"
_REFERENCE = _impl(_REF_IMPL)


# ===========================================================================
# UNIQUENESS (expect reject) — WRONG impls that share the frozen spec. If any
# VERIFIES, the spec is SPEC-TOO-WEAK. Each carries a machine-checked witness.
# Every witness is stated at the method's OWN precondition and discharges it from
# its `hpre` binder, so each rival is refuted INSIDE the modelled domain.
# ===========================================================================

# --- Ck attack (constant input: out must be the empty factorisation) ---

# weak-ignores-constant-guard: the selection-only impl — recover the factor list,
# else fall back to the single representative — with NO constant test. Correct on
# every non-constant input, so it is a genuine partial-domain break, and it is
# precisely the impl an earlier revision of this spec demanded of EVERY input.
# FAILS Ck: on a constant input it answers with a length-1 list where the
# operation reports nothing at all.
_WEAK_NO_CONST_GUARD = (
    "    let _other := otherPoly poly\n"
    "    let images := factorList poly\n"
    "    if images.length ≥ 2 then\n"
    "      return images\n"
    "    else\n"
    "      return lone poly"
)
_WIT_NO_CONST_GUARD = (
    "example (poly lc : Int) (hpre : noRepeatedFactor poly = true)\n"
    "    (hmd : hasMainDegree poly = true)\n"
    "    (hc : isConstant poly = true) (hz : (factorList poly).length = 0) :\n"
    "    ¬ (triple (noRepeatedFactor poly = true ∧\n"
    "               (isConstant poly = false → hasMainDegree poly = true))\n"
    "        (extFactor lc poly)\n"
    "        (fun out => isConstant poly = true → out = [])) := by\n"
    "  simp only [extFactor, triple]\n"
    "  intro hh\n"
    "  have hcon := hh ⟨hpre, fun _ => hmd⟩\n"
    "  have hlt : ¬ ((factorList poly).length ≥ 2) := by omega\n"
    "  simp only [if_neg hlt, wp_pure] at hcon\n"
    "  have heq := hcon hc\n"
    "  have hl := loneLen poly\n"
    "  have hz0 := congrArg List.length heq\n"
    "  simp only [List.length_nil] at hz0\n"
    "  omega\n"
)

# --- C1 attacks (splitting input: out must be the complete factorList poly) ---

# weak-prepatch-apply-to-other: THE actual pre-patch bug — the factoring is
# applied to the auxiliary reduced identity `otherPoly poly` instead of the
# input. `otherPoly` promises nothing about its value, so nothing relates
# `factorList (otherPoly poly)` to `factorList poly`; C1 is unprovable.
_WEAK_PREPATCH = "    return factorList (otherPoly poly)"
_WIT_PREPATCH = (
    "example (poly lc : Int) (hpre : noRepeatedFactor poly = true)\n"
    "    (hmd : hasMainDegree poly = true)\n"
    "    (hc : isConstant poly = false)\n"
    "    (h1 : (factorList poly).length ≥ 2)\n"
    "    (h2 : factorList (otherPoly poly) ≠ factorList poly) :\n"
    "    ¬ (triple (noRepeatedFactor poly = true ∧\n"
    "               (isConstant poly = false → hasMainDegree poly = true))\n"
    "        (extFactor lc poly)\n"
    "        (fun out => isConstant poly = false → (factorList poly).length ≥ 2 →\n"
    "          out = factorList poly)) := by\n"
    "  simp only [extFactor, triple]\n"
    "  intro hh\n"
    "  have hcon := hh ⟨hpre, fun _ => hmd⟩\n"
    "  simp only [wp_pure] at hcon\n"
    "  exact h2 (hcon hc h1)\n"
)

# weak-echo-lone-unconditional: collapse to the length-1 fallback regardless of
# branch. Satisfies C2 but FAILS C1: a length-1 list cannot equal a factorList
# of length ≥ 2 (refuted oracle-free via loneLen + omega).
_WEAK_ECHO_LONE = "    return lone poly"
_WIT_ECHO_LONE = (
    "example (poly lc : Int) (hpre : noRepeatedFactor poly = true)\n"
    "    (hmd : hasMainDegree poly = true)\n"
    "    (hc : isConstant poly = false) (h2 : (factorList poly).length ≥ 2) :\n"
    "    ¬ (triple (noRepeatedFactor poly = true ∧\n"
    "               (isConstant poly = false → hasMainDegree poly = true))\n"
    "        (extFactor lc poly)\n"
    "        (fun out => isConstant poly = false → (factorList poly).length ≥ 2 →\n"
    "          out = factorList poly)) := by\n"
    "  simp only [extFactor, triple]\n"
    "  intro hh\n"
    "  have hcon := hh ⟨hpre, fun _ => hmd⟩\n"
    "  simp only [wp_pure] at hcon\n"
    "  have heq := hcon hc h2\n"
    "  have hl := loneLen poly\n"
    "  have hlen := congrArg List.length heq\n"
    "  omega\n"
)

# weak-truncate-last-factor: PARTIAL-DOMAIN — correct on the constant and the
# non-splitting branches, but drops the LAST factor on the splitting branch.
# Result is factorList poly with one element removed, so its length differs and
# C1 fails (refuted oracle-free via List.length_dropLast + omega, under the
# branch guards).
_WEAK_TRUNC = (
    "    let _other := otherPoly poly\n"
    "    if isConstant poly then\n"
    "      return ([] : List Int)\n"
    "    else\n"
    "      let images := factorList poly\n"
    "      if images.length ≥ 2 then\n"
    "        return images.dropLast\n"
    "      else\n"
    "        return lone poly"
)
_WIT_TRUNC = (
    "example (poly lc : Int) (hpre : noRepeatedFactor poly = true)\n"
    "    (hmd : hasMainDegree poly = true)\n"
    "    (hc : isConstant poly = false) (h2 : (factorList poly).length ≥ 2) :\n"
    "    ¬ (triple (noRepeatedFactor poly = true ∧\n"
    "               (isConstant poly = false → hasMainDegree poly = true))\n"
    "        (extFactor lc poly)\n"
    "        (fun out => isConstant poly = false → (factorList poly).length ≥ 2 →\n"
    "          out = factorList poly)) := by\n"
    "  simp only [extFactor, triple]\n"
    "  intro hh\n"
    "  have hcon := hh ⟨hpre, fun _ => hmd⟩\n"
    "  simp only [hc, if_pos h2, wp_pure] at hcon\n"
    "  have heq := hcon trivial h2\n"
    "  have hl := congrArg List.length heq\n"
    "  simp only [List.length_dropLast] at hl\n"
    "  omega\n"
)

# --- C2 attacks (non-splitting input: out must be the one-element lone poly) ---

# weak-echo-factorlist-unconditional: materialise factorList poly with NO
# selection branch. Satisfies C1 but FAILS C2: when factorList poly does not
# split (here pinned to length 0) it cannot equal the length-1 lone poly
# (refuted oracle-free via loneLen + omega; the single opaque-length binder is
# consistent — length 0 is possible and 0 < 2).
_WEAK_ECHO_FL = "    return factorList poly"
_WIT_ECHO_FL = (
    "example (poly lc : Int) (hpre : noRepeatedFactor poly = true)\n"
    "    (hmd : hasMainDegree poly = true)\n"
    "    (hc : isConstant poly = false) (hz : (factorList poly).length = 0) :\n"
    "    ¬ (triple (noRepeatedFactor poly = true ∧\n"
    "               (isConstant poly = false → hasMainDegree poly = true))\n"
    "        (extFactor lc poly)\n"
    "        (fun out => isConstant poly = false → ¬ (factorList poly).length ≥ 2 →\n"
    "          out = lone poly)) := by\n"
    "  simp only [extFactor, triple]\n"
    "  intro hh\n"
    "  have hcon := hh ⟨hpre, fun _ => hmd⟩\n"
    "  simp only [wp_pure] at hcon\n"
    "  have hlt : ¬ (factorList poly).length ≥ 2 := by omega\n"
    "  have heq := hcon hc hlt\n"
    "  have hl := loneLen poly\n"
    "  have hlen := congrArg List.length heq\n"
    "  omega\n"
)

# weak-lone-fallback-of-other: PARTIAL-DOMAIN on the OTHER sub-domain — correct
# on the constant and splitting branches, but builds the one-element fallback
# from the AUXILIARY reduced identity rather than the input. C2 demands
# `lone poly`; `otherPoly` promises nothing about its value, so nothing relates
# `lone (otherPoly poly)` to it and C2 is unprovable (separation binder).
#
# AUDIT NOTE — this REPLACES a case that was vacuous. The shipped
# `weak-lone-branch-returns-factorlist` returned `images` in BOTH branches of its
# `if`, which is `return factorList poly` unconditionally: byte-for-byte the same
# OBSERVABLE impl as `weak-echo-factorlist-unconditional`, differing only by a
# dead branch the elaborator collapses. Two spellings of one rival attack one
# point, so the second attested nothing the first did not. The replacement keeps
# the intended distinct shape (correct on the splitting branch, wrong fallback)
# while attacking C2 through a genuinely different mechanism: the WRONG ARGUMENT
# to the fallback rather than the wrong list.
_WEAK_LONE_FALLBACK_OTHER = (
    "    let _other := otherPoly poly\n"
    "    if isConstant poly then\n"
    "      return ([] : List Int)\n"
    "    else\n"
    "      let images := factorList poly\n"
    "      if images.length ≥ 2 then\n"
    "        return images\n"
    "      else\n"
    "        return lone _other"
)
_WIT_LONE_FALLBACK_OTHER = (
    "example (poly lc : Int) (hpre : noRepeatedFactor poly = true)\n"
    "    (hmd : hasMainDegree poly = true)\n"
    "    (hc : isConstant poly = false)\n"
    "    (h1 : ¬ (factorList poly).length ≥ 2)\n"
    "    (h2 : lone (otherPoly poly) ≠ lone poly) :\n"
    "    ¬ (triple (noRepeatedFactor poly = true ∧\n"
    "               (isConstant poly = false → hasMainDegree poly = true))\n"
    "        (extFactor lc poly)\n"
    "        (fun out => isConstant poly = false → ¬ (factorList poly).length ≥ 2 →\n"
    "          out = lone poly)) := by\n"
    "  simp only [extFactor, triple]\n"
    "  intro hh\n"
    "  have hcon := hh ⟨hpre, fun _ => hmd⟩\n"
    "  simp only [hc, if_neg h1, wp_pure] at hcon\n"
    "  exact h2 (hcon trivial h1)\n"
)

# weak-input-as-singleton: echo the input identity as a one-element list [poly].
# The input identity is DISTINCT from its factor list (carrier abstraction,
# mapping.md §2), so on the non-splitting sub-domain [poly] ≠ lone poly and C2
# fails (separation binder). Supporting near-miss.
_WEAK_SINGLETON = "    return ([poly] : List Int)"
_WIT_SINGLETON = (
    "example (poly lc : Int) (hpre : noRepeatedFactor poly = true)\n"
    "    (hmd : hasMainDegree poly = true)\n"
    "    (hc : isConstant poly = false)\n"
    "    (h1 : ¬ (factorList poly).length ≥ 2)\n"
    "    (h2 : ([poly] : List Int) ≠ lone poly) :\n"
    "    ¬ (triple (noRepeatedFactor poly = true ∧\n"
    "               (isConstant poly = false → hasMainDegree poly = true))\n"
    "        (extFactor lc poly)\n"
    "        (fun out => isConstant poly = false → ¬ (factorList poly).length ≥ 2 →\n"
    "          out = lone poly)) := by\n"
    "  simp only [extFactor, triple]\n"
    "  intro hh\n"
    "  have hcon := hh ⟨hpre, fun _ => hmd⟩\n"
    "  simp only [wp_pure] at hcon\n"
    "  exact h2 (hcon hc h1)\n"
)

# weak-empty-factorisation: return the empty factorisation for EVERY input.
# Correct on the constant branch (Ck admits `[]` there and only there), so this
# rival also pins the direction of the constant clause: admitting the empty
# answer for a constant did not make it acceptable anywhere else. On the
# non-splitting sub-domain [] ≠ lone poly (length 1) and C2 fails (refuted
# oracle-free via loneLen + simp).
_WEAK_EMPTY = "    return ([] : List Int)"
_WIT_EMPTY = (
    "example (poly lc : Int) (hpre : noRepeatedFactor poly = true)\n"
    "    (hmd : hasMainDegree poly = true)\n"
    "    (hc : isConstant poly = false) (h : ¬ (factorList poly).length ≥ 2) :\n"
    "    ¬ (triple (noRepeatedFactor poly = true ∧\n"
    "               (isConstant poly = false → hasMainDegree poly = true))\n"
    "        (extFactor lc poly)\n"
    "        (fun out => isConstant poly = false → ¬ (factorList poly).length ≥ 2 →\n"
    "          out = lone poly)) := by\n"
    "  simp only [extFactor, triple]\n"
    "  intro hh\n"
    "  have hcon := hh ⟨hpre, fun _ => hmd⟩\n"
    "  simp only [wp_pure] at hcon\n"
    "  have heq := hcon hc h\n"
    "  have hl := loneLen poly\n"
    "  have hlen := congrArg List.length heq\n"
    "  simp only [List.length_nil] at hlen\n"
    "  omega\n"
)


SPEC_TESTS = [
    # ---------------- POSITIVE CONTROLS (soundness) ----------------
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": "structurally-different correct impl (non-splitting branch "
                     "tested FIRST via a `length < 2` guard, lone branch hoisted "
                     "ahead of the recovery branch); every value computed per "
                     "branch is unchanged and the frozen bullet-script still "
                     "discharges each loop goal. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-shared-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SHARED,
        "rationale": "local-variable reshape: select the source sequence for all "
                     "three cases into ONE local then materialise with ONE shared "
                     "loop (gold uses an early return plus two loops). Respects "
                     "every clause; the single extra fold-step case (loop over the "
                     "three-way selecting `if`) is closed by naming that expression "
                     "to the frozen drop-step lemma — the `prove_correct extFactor` "
                     "STATEMENT is byte-identical, only the tactic body gains one "
                     "alternative. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-domain-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_DOMAIN_GUARD),
        "rationale": "the DOMAIN control, and the reason the `require` is not dead "
                     "weight. Correct on the modelled domain, but its `else` arm — "
                     "reachable exactly when `noRepeatedFactor poly = true` FAILS — "
                     "returns `[poly]`, which no clause admits. It can therefore "
                     "verify ONLY if the verifier genuinely ASSUMES the require, so "
                     "verification here is the machine-checked statement that the "
                     "domain restriction is live: delete the `require` from the spec "
                     "and this case flips to rejected. Must verify, else the "
                     "restriction is not being assumed and the narrowing bought "
                     "nothing. (The opposite failure mode — a restriction so strong "
                     "it is self-contradictory, which would make the whole contract "
                     "vacuous — is excluded by the eight consistency probes on the "
                     "reject witnesses, each of which must FAIL to derive `False` "
                     "from binders that include `noRepeatedFactor poly = true`.)",
    },
    {
        "id": "pos-control-main-degree-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_MAIN_DEGREE_GUARD),
        "rationale": "the SECOND domain control — one per `require`, so neither "
                     "half of the declared domain can quietly become decoration. "
                     "Correct on the modelled domain, but its innermost `else` arm "
                     "— reachable exactly when a NON-constant argument fails "
                     "`hasMainDegree poly = true`, i.e. exactly when R2 fails — "
                     "returns `[poly, poly]`, which no clause admits. It can "
                     "therefore verify ONLY if the verifier genuinely ASSUMES R2, "
                     "so verification here is the machine-checked statement that "
                     "the main-degree half of the domain restriction is live: "
                     "delete that `require` from the spec and this case flips to "
                     "rejected. Must verify, else that half is not being assumed "
                     "and the narrowing bought nothing.",
    },
    {
        "id": "pos-control-fallback-via-loneLen",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FALLBACK_TAKE_MOD,
        "rationale": "ADDED BY AUDIT (attack E: SPEC-TOO-STRONG probe). The other "
                     "three positives all write the fallback as the literal term "
                     "`lone poly`, i.e. the same expression clause C2 names, so "
                     "none of them tests whether the spec admits a fallback that "
                     "is only EXTENSIONALLY equal to it. This one produces "
                     "`(lone poly).take 1`, equal to `lone poly` only through the "
                     "one transparent axiom-region fact `loneLen : ∀ p, "
                     "(lone p).length = 1`. Measured: the frozen bullet-script "
                     "does NOT close it (residual `⊢ … List.take 1 (lone poly) = "
                     "lone poly`), so it read as a candidate soundness hole until "
                     "the length fact was supplied as a `have`; with that one line "
                     "it verifies. So the spec is not too strong — it requires the "
                     "published axiom to be USED — and keeping the case pins that: "
                     "a respec that drops or weakens `loneLen` flips this to "
                     "rejected rather than silently narrowing the admissible impls "
                     "to the syntactic ones. Must verify, else SPEC-TOO-STRONG.",
    },
    # ---------------- ADMISSIBILITY (re-aimed) ----------------
    {
        "id": "admiss-f2p-postimage-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the analogue, on this bundle, of the nagini "
                     "'a normal in-domain input is admitted' probe (which "
                     "discharged a callee Requires at a concrete input): the clause "
                     "set must be SATISFIABLE at exactly an F2P-shaped input. This "
                     "case tests that directly — it pins `poly := 1` (the identity "
                     "mapping.md §3 assigns the F2P `test_issue_5786` shape) and "
                     "discharges, AT THAT INPUT, all three arms of the selection: "
                     "the constant arm reducing the post-image to `[]`, the "
                     "splitting arm to `factorList 1`, the non-splitting arm to "
                     "something of length 1 — as `have`s, before closing the frozen "
                     "obligation verbatim. Any arm being unprovable there would mean "
                     "the post-image is unsatisfiable exactly where the F2P test "
                     "lives ⇒ PRECOND/SPEC-UNSATISFIABLE. (An earlier revision "
                     "shipped the frozen impl VERBATIM as this case, which re-tests "
                     "only what G-GOLD already covers and could not fail "
                     "independently; the `have`s are what give the lane content. "
                     "They sit in the tactic body because a new top-level `theorem` "
                     "is out of variant scope.)",
    },
    # ---------------- UNIQUENESS: Ck (constant input) ----------------
    {
        "id": "weak-ignores-constant-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_CONST_GUARD),
        "refinement": "a patch that goes straight to the factor recovery without "
                      "first testing whether its argument has any factor content at "
                      "all reports a spurious one-element factorisation for an input "
                      "that the operation answers with no factors, so the "
                      "single-representative assertion over such an input fails. "
                      "Does NOT resolve.",
        "rationale": "REJECT from Ck `isConstant poly = true → out = []`: with no "
                     "constant test the impl answers a constant input from the "
                     "selection, i.e. with a length-1 list, which cannot be the "
                     "empty factorisation — refuted oracle-free via `loneLen` + "
                     "`omega`. Correct on every NON-constant input, so it is a "
                     "genuine partial-domain break, and it is exactly the impl an "
                     "earlier revision of this spec demanded of every input: its "
                     "rejection is the machine-checked statement that Ck ADDS an "
                     "obligation rather than relaxing one. If it verified ⇒ "
                     "SPEC-TOO-WEAK. Conditioned witness (rival exit 0, reference "
                     "exit ≠ 0, probe exit ≠ 0): binders name the domain condition, "
                     "the constant guard, and a factor list of length 0 — jointly "
                     "satisfiable, and the shape a constant input actually has.",
        "witness": _WIT_NO_CONST_GUARD,
        "witness_reference": _REFERENCE,
    },
    # ---------------- UNIQUENESS: C1 (splitting) ----------------
    {
        "id": "weak-prepatch-apply-to-other",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": "this is the actual pre-patch behaviour: the faithful real "
                      "patch applies the recovery to the auxiliary reduced "
                      "identity rather than the input, so on the issue witness the "
                      "reduced identity has already lost a variable's factor "
                      "content and the reconstructed factorisation drops a factor "
                      "— it does NOT resolve (the F2P round-trip and the P2P "
                      "proper-factorisation test fail).",
        "rationale": "REJECT from C1 `isConstant poly = false → (factorList "
                     "poly).length ≥ 2 → out = factorList poly`: the auxiliary "
                     "identity promises nothing about its value, so `factorList "
                     "(otherPoly poly)` is unrelated to `factorList poly` and C1 is "
                     "unprovable. If it verified ⇒ SPEC-TOO-WEAK. Conditioned "
                     "witness (rival exit 0, reference exit ≠ 0, probe exit ≠ 0): "
                     "binders name the domain condition, both branch guards and the "
                     "argument-separation the axiom lane validates.",
        "witness": _WIT_PREPATCH,
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-echo-lone-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ECHO_LONE),
        "refinement": "unconditionally returning the length-1 fallback is the "
                      "collapse-to-one-factor symptom of the bug: a patch that "
                      "always returns a single representative drops every "
                      "co-factor of a splitting input, so the proper-factorisation "
                      "test (a product that must split into TWO factors) fails. "
                      "Does NOT resolve.",
        "rationale": "REJECT from C1: when the input splits (length ≥ 2) a "
                     "length-1 result cannot equal `factorList poly` — refuted "
                     "oracle-free via `loneLen` + `omega`. Closest analog to the "
                     "deleted answer-key echo. If it verified ⇒ SPEC-TOO-WEAK. "
                     "Conditioned witness: rival exit 0, reference exit ≠ 0, probe "
                     "exit ≠ 0 (the domain and guard binders are satisfiable).",
        "witness": _WIT_ECHO_LONE,
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-truncate-last-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_TRUNC),
        "refinement": "dropping the final recovered factor is exactly the issue's "
                      "symptom (a co-factor lost). A real patch that stops the "
                      "recovery one short returns an incomplete factorisation; the "
                      "re-expansion no longer reconstructs the original, so the "
                      "round-trip and proper-factorisation tests fail. Does NOT "
                      "resolve.",
        "rationale": "REJECT from C1, PARTIAL-DOMAIN on the splitting sub-domain: "
                     "the result is `factorList poly` with the last element "
                     "removed, so its length differs from `factorList poly` and C1 "
                     "fails — refuted oracle-free via `List.length_dropLast` under "
                     "the branch guards. Correct on the constant and non-splitting "
                     "branches (a genuine partial-domain break, distinct from the "
                     "unconditional echo). If it verified ⇒ SPEC-TOO-WEAK. "
                     "Conditioned witness: rival exit 0, reference exit ≠ 0, probe ≠ 0.",
        "witness": _WIT_TRUNC,
        "witness_reference": _REFERENCE,
    },
    # ---------------- UNIQUENESS: C2 (non-splitting) ----------------
    {
        "id": "weak-echo-factorlist-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ECHO_FL),
        "refinement": "always materialising the recovery list with no "
                      "single-element fallback is the pre-fallback code path: on a "
                      "genuinely non-splitting input the recovery list is not the "
                      "canonical single representative the function must return, so "
                      "the single-factor tests fail. Does NOT resolve.",
        "rationale": "REJECT from C2 `isConstant poly = false → ¬ (factorList "
                     "poly).length ≥ 2 → out = lone poly`: when the input does not "
                     "split, `factorList poly` cannot equal the length-1 `lone "
                     "poly` — refuted oracle-free via `loneLen` + `omega`. Confirms "
                     "the fallback branch is non-vacuous. If it verified ⇒ "
                     "SPEC-TOO-WEAK. Conditioned witness pins `(factorList "
                     "poly).length = 0` (satisfiable: 0 < 2): rival exit 0, "
                     "reference exit ≠ 0, probe exit ≠ 0.",
        "witness": _WIT_ECHO_FL,
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-lone-fallback-of-other",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_LONE_FALLBACK_OTHER),
        "refinement": "on the non-splitting sub-domain (the irreducible / "
                      "single-factor inputs the single-factor tests exercise) "
                      "the canonical single representative is built from the "
                      "auxiliary reduced identity rather than the input, so it "
                      "represents the wrong polynomial and the single-factor "
                      "assertions fail. Does NOT resolve.",
        "rationale": "REJECT from C2, PARTIAL-DOMAIN on the non-splitting "
                     "sub-domain: C2 demands `lone poly`, and the auxiliary "
                     "identity promises nothing about its value, so nothing "
                     "relates `lone (otherPoly poly)` to `lone poly`. Correct on "
                     "the constant and splitting branches — a genuine "
                     "partial-domain break. REPLACES the earlier "
                     "`weak-lone-branch-returns-factorlist`, which returned the "
                     "recovery list in BOTH branches and was therefore the same "
                     "OBSERVABLE impl as weak-echo-factorlist-unconditional (a "
                     "vacuous duplicate; see the AUDIT NOTE at its definition). If "
                     "it verified ⇒ SPEC-TOO-WEAK. Conditioned witness names the "
                     "domain condition, both branch guards and the "
                     "argument-separation `lone (otherPoly poly) ≠ lone poly`: "
                     "rival exit 0, reference exit ≠ 0, probe exit ≠ 0.",
        "witness": _WIT_LONE_FALLBACK_OTHER,
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-input-as-singleton",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SINGLETON),
        "refinement": "returning the input unchanged as a one-element list never "
                      "factors anything: the input identity is DISTINCT from its "
                      "factor list (carrier abstraction), so this is an un-factored "
                      "blob and every discriminating test fails. Does NOT resolve.",
        "rationale": "supporting near-miss, REJECT from C2: on the non-splitting "
                     "sub-domain `[poly]` is distinct from `lone poly`, so C2 "
                     "fails. If it verified ⇒ SPEC-TOO-WEAK. Conditioned witness "
                     "names the domain condition, both branch guards and the "
                     "separation `[poly] ≠ lone poly`: rival exit 0, reference exit "
                     "≠ 0, probe exit ≠ 0.",
        "witness": _WIT_SINGLETON,
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-empty-factorisation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EMPTY),
        "refinement": "the empty factorisation corresponds to no real factoring "
                      "at all; a patch returning nothing for every input produces a "
                      "wrong/empty product on re-expansion and fails the round-trip "
                      "immediately. Does NOT resolve.",
        "rationale": "supporting near-miss, REJECT from C2: length 0 cannot equal "
                     "the length-1 `lone poly` on the non-splitting sub-domain — "
                     "refuted oracle-free via `loneLen` + `omega`. This case also "
                     "pins the DIRECTION of the constant clause Ck: admitting the "
                     "empty answer for a CONSTANT input did not make it acceptable "
                     "anywhere else, so the clause the spec gained is a case "
                     "distinction and not a licence to return nothing. If it "
                     "verified ⇒ SPEC-TOO-WEAK. Conditioned witness names the "
                     "domain condition and both branch guards: rival exit 0, "
                     "reference exit ≠ 0, probe exit ≠ 0.",
        "witness": _WIT_EMPTY,
        "witness_reference": _REFERENCE,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                          -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder                  -> pos-control-branch-reorder    PORTED
#   pos-control-shared-loop              -> pos-control-shared-loop       PORTED
#   admiss-f2p-input                     -> admiss-f2p-postimage-satisf.  RE-AIMED
#   weak-prepatch-apply-to-other         -> weak-prepatch-apply-to-other  PORTED
#   weak-echo-lone-unconditional         -> weak-echo-lone-unconditional  PORTED
#   weak-echo-factorlist-unconditional   -> weak-echo-factorlist-uncond.  PORTED
#   weak-truncate-last-factor            -> weak-truncate-last-factor     PORTED
#   weak-lone-branch-returns-factorlist  -> weak-lone-fallback-of-other   RE-AIMED
#   weak-input-as-singleton              -> weak-input-as-singleton       PORTED
#   weak-empty-factorisation             -> weak-empty-factorisation      PORTED
#   (none)                               -> pos-control-domain-guard      ADDED
#   (none)                               -> pos-control-main-degree-guard  ADDED
#   (none)                               -> weak-ignores-constant-guard   ADDED
#   (none)                               -> pos-control-fallback-via-loneLen ADDED
#   AXIOM_TESTS (5 probes)               -> dropped (G-AX lane, not G-PBT)
#
# 8 ported (2 soundness + 6 uniqueness), 2 re-aimed (admissibility + the C2
# partial-domain rival), 4 ADDED (one per `require`, one for the constant clause,
# one for the extensional fallback) = 14 cases.
# NONE of the nagini uniqueness rivals is dropped: every postcondition clause a
# nagini rival attacked (the completeness clause C1 and the fallback clause C2) is
# attacked here, and each rival's faithful real patch is argued not to resolve.
#
# ADDED (pos-control-domain-guard + weak-ignores-constant-guard), by AUDIT. The
#   spec gained a `require` (the modelled domain) and a constant clause (Ck), and a
#   lane must cover BOTH new pieces or the additions would be unattested:
#     * pos-control-domain-guard makes the `require` falsifiable in the sound
#       direction — the case verifies only because the require is ASSUMED, so if the
#       restriction were removed the case would flip to rejected.
#     * weak-ignores-constant-guard makes Ck falsifiable in the weak direction — the
#       rival is the impl the previous revision of this spec demanded, and it is now
#       rejected, so the clause is an added obligation and not a relaxation.
#   Together with weak-empty-factorisation (which stays rejected even though `[]`
#   is now the demanded answer for ONE input class) the three cases pin the added
#   clause from both sides.
#
# RE-AIMED (weak-lone-branch-returns-factorlist -> weak-lone-fallback-of-other),
#   by AUDIT, attack C. As ported, that rival returned `images` in BOTH branches of
#   its `if`, i.e. `return factorList poly` unconditionally — the same OBSERVABLE
#   impl as weak-echo-factorlist-unconditional, differing only by a dead branch.
#   Two spellings of one rival attacking one point: the case was vacuous, not
#   wrong-in-a-new-way, so its rejection attested nothing the other did not. It is
#   re-aimed at the same INTENDED shape (correct on the splitting branch, wrong on
#   the fallback) via a distinct mechanism: the fallback is built from the
#   auxiliary identity, so C2 fails on the argument rather than on the list.
#
# RE-AIMED (admiss-f2p-input -> admiss-f2p-postimage-satisfiable): the nagini
#   admissibility case forced a callee `Requires` (0 ≤ 1 ≤ 4) to be discharged at a
#   recursive call on an F2P-shaped input. This bundle's `require` is a condition on
#   an OPAQUE Boolean, so it can be neither computed nor discharged at a literal
#   input; the analogue is that the clause set be SATISFIABLE at exactly an
#   F2P-shaped input, discharged AT THAT CONCRETE INPUT (`poly := 1`, mapping.md §3)
#   as `have`s on all three arms of the selection before the frozen obligation
#   closes verbatim. A second audit strengthened this: the previous revision shipped
#   the frozen impl VERBATIM (`module: _BASE`), which duplicates G-GOLD and cannot
#   fail independently of it — an admissibility lane with no content. The `have`s
#   are in the tactic body because a top-level `theorem` is out of variant scope
#   (measured: `variant_problems` reports "a variant reproves the SAME
#   obligations"). The require's own admissibility — that it is assumed, and that it
#   is not self-contradictory — is carried by pos-control-domain-guard and by the
#   eight consistency probes respectively.
#
# FRAME-MUTATION / PERMISSION: N/A on nagini (both inputs are `int` value types,
#   no `Acc(...,1/2)`) and VACUOUS here (referentially transparent, no `mut`
#   PARAMETER — the loop's `mut` locals are not inputs). No substitute fabricated.
#
# DIVERGENCE / NON-TERMINATION: the nagini sibling carries NO diverge-* / nonterm-*
#   case (its impl is a bounded `while`), so there is nothing to port. The class is
#   VACUOUS here and the reason is measured (see the DIVERGENCE bullet in the
#   docstring for the builds): this bundle sets `loom.semantics.termination
#   "total"`, so the verifier requires a decreasing measure and all three diverging
#   rivals built against it are REJECTED with `Decreasing annotations are required
#   in total correctness semantics`. The spec refuses divergence, so there is no
#   hole to report and nothing to escalate. A second audit corrected this comment:
#   the previous revision asserted `"partial"` (hence a vacuously-verifying
#   diverging impl and an open spec hole), which is not what this bundle carries —
#   the corpus flip to `total` added the two `decreasing i` clauses that are in the
#   frozen impl and in this file's `_IMPL` anchor. A THIRD audit corrected the
#   UNSHIPPABILITY reason, which the previous revision got wrong: the
#   decreasing-annotation error fires on the `method` command only for the
#   NO-annotation shape. For the CONSTANT-MEASURE shape the annotation is present,
#   the rejection lands inside `prove_correct` (descent goal `⊢ q < q`), and
#   `witness_file` strips that — so its witness file DOES compile (a trivial
#   witness builds at exit 0). What actually blocks the case is attribution: the
#   witnesses speak to the method's PARTIAL-correctness `triple`, which a
#   diverging program satisfies vacuously, so with divergence as the only defect
#   the refutation fails on the RIVAL (`witness-unproven` => MALFORMED-TESTS) and
#   a rival that clears all three builds does so by being wrong on C2 rather than
#   by diverging. Measured both ways; see the DIVERGENCE bullet. Not a
#   spec_holes entry — the module build genuinely rejects both shapes. The real
#   callee's own non-termination is a DOMAIN fact, not a hole: it happens strictly
#   outside `require noRepeatedFactor poly = true`, where the contract asserts
#   nothing, and mapping.md §3 shows the graded tests never leave that domain.
#
# CLAUSE COVERAGE. Ck `isConstant poly = true → out = []` is attacked by
#   weak-ignores-constant-guard (no constant test at all) and defended in the
#   opposite direction by weak-empty-factorisation (the empty answer stays wrong
#   everywhere else). C1 `isConstant poly = false → (factorList poly).length ≥ 2 →
#   out = factorList poly` is attacked by weak-prepatch-apply-to-other (wrong
#   argument), weak-echo-lone-unconditional (length collapse), and
#   weak-truncate-last-factor (off-by-one, partial-domain). C2 `isConstant poly =
#   false → ¬ (factorList poly).length ≥ 2 → out = lone poly` is attacked by
#   weak-echo-factorlist-unconditional (fallback ignored), weak-lone-fallback-of-
#   other (partial-domain, wrong fallback ARGUMENT), weak-input-as-singleton, and
#   weak-empty-factorisation. C0 (`out = expectedFactors poly`) is definitionally
#   Ck ∧ C1 ∧ C2 (expectedFactors unfolds to the same selection), so it is
#   co-refuted by any Ck/C1/C2 break — no separate rival added. The `require` is
#   covered by pos-control-domain-guard (assumed) and by every reject witness
#   (satisfiable). FOUR positives defend the whole clause set; the fourth
#   (pos-control-fallback-via-loneLen, added by audit) is the only one whose
#   fallback is not the literal term `lone poly`, so it is what pins that C2
#   admits an EXTENSIONALLY equal fallback and not merely the syntactic one.
#
# ATTACK COVERAGE MEASURED BY THIS AUDIT (all builds against the real verifier;
#   nothing below ships, it records what was probed and found sound).
#   * Statement integrity (A): every case's text OUTSIDE the impl region and the
#     `prove_correct` tactic body is byte-identical to the frozen file. No case
#     reformats or restates an obligation.
#   * Witness discrimination (B), all 8 reject cases rebuilt three ways: rival 0,
#     reference 1, consistency probe 1 — reproducing the recorded outcomes.
#   * Forgery (B′), all 8: the claim was FLIPPED (the `¬` dropped and the clause
#     proven at the same binders) and rebuilt on both subjects. Every flip
#     inverts the exit codes — reference 0, rival 1 — so each reference-side exit
#     code tracks the CLAIM and not the file. The two `Application type mismatch`
#     signatures were additionally type-revealed (`exact (heq : Nat)`): the
#     hypothesis prints as a CONCRETE equation on both sides (`expectedFactors
#     poly = lone poly` vs `factorList poly = lone poly`), never as `True`, so
#     `simp` did not prove the clause away on either subject.
#   * Definitional-equality check (C): each rival's returned term was tested for
#     provable equality to `expectedFactors poly` under the branch guard — all 7
#     unprovable, so no rival is a reshape of gold on this carrier.
#   * SPEC-TOO-WEAK probe (D), 15 NEW wrong impls not in this battery, all
#     REJECTED: guard thresholds moved to ≥1 / ≥3 / >2, the two non-constant arms
#     swapped, the constant test keyed on `hasMainDegree` / `noRepeatedFactor`,
#     the factor list reversed, a right-length wrong-content answer
#     (`List.replicate`), a spurious factor appended, the constant arm answered
#     with `lone (otherPoly poly)`, the priority of the constant and splitting
#     arms inverted, the fallback given as `[otherPoly poly]` and as
#     `[(factorList poly).headI]` (both length-1, so these probe whether C2 is
#     length-only — it is not), and two impls keyed on the contract-irrelevant
#     `lc` (branching on `lc = 0`, prepending `lc`). No hole found.
#   * SPEC-TOO-STRONG probe (E), 10 NEW correct reshapes, 9 verified as written
#     (guard flipped, `2 ≤` form, `¬ (… ≤ 1)` form, nested three-way returns,
#     `.reverse.reverse`, `++ []`, `.drop 0`, `.take length`, R2-keyed). The
#     tenth is now shipped as pos-control-fallback-via-loneLen.
#   * Require liveness re-derived independently: deleting R1 flips
#     pos-control-domain-guard to rejected and deleting R2 flips
#     pos-control-main-degree-guard to rejected, while the FROZEN impl still
#     verifies without either require — so each guard case fails for the absence
#     of its own hypothesis and not because the frozen proof needs it.
#   * Admissibility falsifiability: mutating the case's own length claim from
#     `= 1` to `= 2` rejects (`loneLen 1 has type (lone 1).length = 1`), so the
#     `have`s carry content and the case is not the frozen file in disguise.
#
# BINDER COVERAGE. The spec predicates bind `poly` (the input identity) and `lc`.
#   The reject witnesses VARY `poly` across sub-domains: constant with an empty
#   factor list (ignores-constant-guard), non-constant and splitting (length ≥ 2:
#   prepatch, echo-lone, truncate), non-constant with length exactly 0
#   (echo-factorlist), and non-constant non-splitting generally
#   (lone-fallback-of-other, singleton, empty) — so no rival that mishandles only
#   one poly-regime would slip through. Every witness additionally binds the domain
#   condition `noRepeatedFactor poly = true`, so every refutation is INSIDE the
#   modelled domain. `lc` is a genuinely IRRELEVANT binder: it appears in the
#   signature but in NO ensures clause (the contract is stated purely over `poly`),
#   so there is no behaviour keyed on `lc` for a rival to abuse and no witness
#   varies it — a deliberate, explained omission per the coverage guidance, not an
#   untested binder.
#
# WITNESS MECHANICS: the velvet tester+`decide` path is inapplicable (opaque
#   axioms, no executable content; the Decidable instance stalls on
#   `factorList`/`lone`, and a wrong rival and gold fail the tester build
#   identically). Every witness refutes the method's own partial-correctness
#   `triple` AT THE METHOD'S OWN PRECONDITION via `wp_pure` (with the guard-reducing
#   rewrites supplied as `simp only` arguments for the branch-structured rivals, so
#   a guard the reference lacks is merely unused rather than fatal) on the rival's
#   concrete `return`; the conditioned ones name only opaque-guard / separation
#   binders the consistency probe confirms satisfiable. The SECOND SUBJECT is the
#   `witness_reference`, not the frozen impl: the frozen `while` leaves an
#   un-normalised `forIn Lean.Loop.mk` term on which every witness's first reduction
#   step fails SYNTACTICALLY, so the frozen impl's exit code discriminated nothing
#   (an audit forged a vacuous witness that passed both halves against it, recorded
#   `rejected` by the gate's own `_check_witness`). Against the loop-free reference
#   each of the eight now fails SEMANTICALLY, at or after the step that applies the
#   reduced clause. All twelve cases were built against the real verifier.
#
# AXIOM_TESTS: dropped. The five nagini axiom-soundness / containment probes are
#   G-AX's job (axiom_check.py); the G-PBT gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
