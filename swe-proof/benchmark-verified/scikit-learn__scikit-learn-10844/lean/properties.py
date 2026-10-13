"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-10844 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_fmIndex``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one function from a rectangular co-occurrence matrix to an
OUTCOME). The matrix ``M : List (List ℕ)`` is the primitive input; three integer
quantities are formed from it — the agreement count ``cmTk M`` and the two
marginal counts ``cmPk M``, ``cmQk M`` — each held in one signed machine word
(``cmTkW M``, ``cmPkW M``, ``cmQkW M : BitVec 64``). The index is reported as an
``Option ℝ``: ``some v`` when the assembly named the real number ``v``, ``none``
when it named no real number at all. The two arithmetic steps the library builds
the index out of are modeled as the PARTIAL operations they are —

  fdiv x y  = none  if y = 0,  else some (x / y)
  fsqrt x   = none  if x < 0,  else some (sqrt x)

— and the spec is:

  problem_spec_fmIndex (M) (result : Option ℝ) :=
    ((cmTkW M).toInt = 0 → result = some 0)                          -- CLAUSE 1
    ∧ ((cmTkW M).toInt ≠ 0 →
        result = some (((cmTkW M).toInt : ℝ)
          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))))  -- CLAUSE 2

WHY THE CARRIER IS ``Option ℝ`` AND NOT ``ℝ``, AND WHY THAT IS THE WHOLE POINT.
Mathlib's ``/`` and ``Real.sqrt`` are TOTAL: ``x / 0 = 0`` and ``Real.sqrt`` of a
non-positive real is ``0``. On a plain ``ℝ`` carrier that totality is not a
convenience, it is a hole, and it was MEASURED to be one. With
``gold M = if T = 0 then 0 else sqrt (T/P) * sqrt (T/Q)`` and
``guardless M = sqrt (T/P) * sqrt (T/Q)`` both taken into ``ℝ``, the two are the
SAME FUNCTION — machine-checked, ``gold = guardless`` by ``funext`` — because at
``T = 0`` the guardless expression evaluates to ``sqrt (0/P) * sqrt (0/Q) = 0``
whether or not ``P`` is itself ``0``. So on an ``ℝ`` carrier NO predicate
whatsoever on ``(M, result)`` can hold of the guarded assembly and fail of the
guard-erased one, and the case split on the agreement count carries exactly zero
information in the specification. The library's arithmetic is not total: on the
matrix ``[[1,1,1,1,1,1]]`` (one class, six clusters) the counts are ``T = 0``,
``P = 0``, ``Q = 30``, the guard-erased assembly divides ``0`` by ``0``, and what
comes back is not a real number. Modeling ``/`` and ``sqrt`` as partial makes that
difference OBSERVABLE — ``none`` versus ``some 0`` — and clause 1 then has
content: it demands the real number ``0`` on every zero-agreement matrix,
including the ones where a marginal count is ``0`` too. The ``guard-erasure``
case below is that distinction as a reject, and ``admiss-nondegenerate-ground``
discharges the obligation at that very matrix so the demand is provably
satisfiable there.

Note also WHERE the marginal product sits in clause 2: the two counts are widened
OUT of their words by ``.toInt`` and multiplied over ℝ, so clause 2 demands the
exact value even at matrices whose marginal product does not fit one word — a
rival that folds that product into a window is refutable, which is the content of
the ``fixed-width-product`` case. ``correct_fmIndex`` carries, besides
rectangularity, the hypothesis that each of the three counts INDIVIDUALLY sits in
the window (``inWord``); nothing is assumed about their product.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's signature is
    by-value floats with no permission tokens and it already records this class
    as N/A; on this referentially-transparent carrier the input ``M`` is an
    immutable value with no heap footprint, no ``mut`` binder and no aliasing, so
    there is likewise no read-only cell to overwrite. No substitute fabricated.

  * THE EVALUATION-ORDER-ONLY RIVAL (pure reassociation, no width) — VACUOUS,
    and this must be stated precisely, because the neighbouring distinction is
    NOT vacuous. Over exact reals ``T / √(P·Q)`` and ``√(T/P)·√(T/Q)`` are
    mathematically EQUAL (for ``T ≥ 0``, ``P, Q > 0``, both established as frozen
    lemmas), and the frozen clause 2 is stated in the FIRST of those two forms.
    So a rival that only reassociates — forming the marginal product in exact
    ``ℤ``/``ℝ`` and dividing by its root — genuinely SATISFIES the spec and
    cannot carry a refutation witness. MEASURED, not argued: that rival was built
    and it VERIFIES (exit 0), which is the correct outcome (it is a
    soundness-side reshape, not a rival). It ships in the soundness lane as
    ``pos-specform-product``. Being unable to refute it is a fact about the spec
    worth testing positively, not an omission to record.

  * THE FIXED-WIDTH RIVAL — EXPRESSIBLE and SHIPPED, see
    ``fixed-width-product``. What separates the two arithmetics is not the
    evaluation ORDER but whether the marginal product is reduced into a bounded
    window before the root. Spelled inline as the signed two's-complement fold
    ``((x + 2^63) % 2^64) - 2^63``, it is genuinely WRONG on this carrier: at a
    matrix whose marginal product leaves the window the fold is NEGATIVE, so
    ``fsqrt`` of it is ``none`` and the outcome names no real number where clause
    2 demands one.

  * THE GUARD-ERASURE RIVAL — EXPRESSIBLE ONLY BECAUSE THE ARITHMETIC IS PARTIAL,
    and it is the load-bearing case of this battery; see ``guard-erasure``. On a
    total ``ℝ`` carrier it is not a rival at all but an EQUAL function (proved
    above), which is precisely why the ``Option``/partial-op carrier is not
    decoration.

  * UNGROUNDED-ORACLE ECHO — clause 2 pins the result to a spelled-out arithmetic
    function of the input quantities, not to an axiomatized oracle; the ``axioms``
    region declares no ``opaque``/``axiom``. An impl that returns
    ``some (T / √(P·Q))`` directly, never consulting the partial operations, is
    the echo — and it is CORRECT here (it lands the same value on every
    admissible input), so there is nothing to refute in that lane; it is covered
    positively by ``pos-specform-product``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``impl_value``'s ``rfl`` is tuned to the
frozen body — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a concrete rectangular matrix. Each was built against the
rival (it HOLDS: the file elaborates, only the deliberately stubbed
``correct_fmIndex`` carries ``sorry``) and rebuilt against the frozen solution (it
FAILS there, exit 1) — a real discriminator, not a tautology. Concrete
``cmTk``/``cmPk``/``cmQk`` values close by ``decide``; the two ``none``-versus-
``some`` witnesses close by ``Option.noConfusion``.

BINDER COVERAGE. The spec predicate has one input binder ``M``; the reject
witnesses vary it across FIVE distinct matrices probing the two independent
clauses on complementary sub-domains, and both the small- and large-count ends:
  * clause 2 (``T ≠ 0``) at ``[[1,1],[1,2]]`` (agreement 2, both marginals 8) by
    the squared-index rival; at ``[[0,0,0],[2,3,3]]`` (agreement 14, ASYMMETRIC
    marginals 14 vs 56) by the single-ratio rival — the asymmetry is what
    discriminates dropping ``cmQk``; and at ``[[60000,60000],[60000,60000]]``
    (marginals 28799760000, product outside a 64-bit window) by the fixed-width
    rival — the MAGNITUDE is what discriminates a bounded product;
  * clause 1 (``T = 0``) at ``[[1,1],[1,0]]`` (agreement 0, BOTH marginals 2 —
    strictly positive) by the zero-branch rival, which gets the VALUE wrong
    there; and at ``[[1,1,1,1,1,1]]`` (agreement 0 AND first marginal 0) by the
    guard-erasure rival, which produces NO real number there. Those two are
    different failures on the same clause — a wrong real versus no real — and the
    second is unreachable on a total carrier.

    The zero-branch point is ``[[1,1],[1,0]]`` and NOT the smaller ``[[1,1]]``
    for a measured reason: at ``[[1,1]]`` the counts are ``T = 0``, ``P = 0``,
    ``Q = 2`` — the first marginal VANISHES there, exactly as it does at the
    guard-erasure point, so the two clause-1 witnesses would sit on the same
    degenerate sub-domain (``P = 0``) and the sub-domain claim above would be
    false of the battery. ``[[1,1],[1,0]]`` has ``T = 0`` with ``P = Q = 2 > 0``
    (each pinned by ``decide``), which is the non-degenerate zero-agreement
    regime — a point where clause 1's demand does not coincide with the
    partial-arithmetic failure the guard-erasure rival dies at, so the two
    rivals genuinely probe different things.
``pts`` = 5 distinct input points across both clauses.

The positive lanes visit the same ends of the domain, so the battery is not
lopsided: ``admiss-nondegenerate-ground`` discharges the obligation at
``[[2,1],[1,3]]``, at the DEGENERATE ``[[1,1,1,1,1,1]]`` where a marginal count
is ``0`` (the point the guard-erasure rival dies at — so "the spec is satisfiable
exactly where an unguarded assembly breaks" is a tested claim, not an asserted
one), AND at ``[[60000,60000],[60000,60000]]`` (the large-count regime the
fixed-width rival is refuted at).

WHY GOLD'S EXIT CODE CARRIES INFORMATION (the forgery control). Each of the five
witnesses was ALSO built against the frozen solution and each fails there (exit
1), while holding of its own rival — so gold's exit code tracks what is being
CLAIMED and not merely the shape of the script.

OMITTED nagini cases (see assessment): the frame/permission-mutation rival
(VACUOUS — referentially-transparent carrier); the evaluation-order-ONLY rival as
a REJECT case (VACUOUS in that lane — over exact reals the reassociation is an
equality and the frozen clause 2 is stated in that very form, so that rival is
correct here and was measured to VERIFY; it ships in the soundness lane as
``pos-specform-product``); and the AXIOM_TESTS lane (this bundle declares no
axiom / deep-model reference, so G-AX skips).

DIVERGENCE / NON-TERMINATION lane: VACUOUS on this carrier, demonstrated rather
than asserted. The frozen bundle sets no ``loom.semantics.termination`` option, so
there is no partial-semantics escape hatch: ``implementation_fmIndex`` is a plain
Lean ``def`` and Lean's equation compiler demands a termination argument up front.
A rival whose body recurses without a decreasing measure does not verify vacuously
and does not reach the spec at all — it fails to ELABORATE. That is a
carrier-level rejection rather than a spec-attributable one, and no witness can be
stated against a definition that does not exist, so there is nothing to ship in
this lane. (Measured, twice and with the error text: a rival whose impl region is
``implementation_fmIndex M = implementation_fmIndex M`` fails at the DEFINITION
with ``fail to show termination for implementation_fmIndex ... failed to infer
structural recursion ... it is unchanged in the recursive calls``, and a witness
file built over that same rival fails with the identical definition-site error —
so does a witness asserting something TRIVIALLY TRUE. Both halves of the
discrimination check therefore break on the definition, not on the claim, which
is what "no witness can be stated" means here rather than "the proof was hard".
The frozen impl is straight-line arithmetic over a finite fold and carries no
loop of its own.) NOTE: the ``Option`` carrier is a
partiality of the ARITHMETIC, not of control flow — ``none`` models "this step
named no real number", never "this program failed to terminate".

AXIOM lane: EMPTY. meta.json ``axioms == []`` and ``deep_model_references == []``;
the three quantities and the index are modeled DEEPLY over the input matrix, so
there is no axiom-soundness / axiom-containment obligation to probe here.
``AXIOM_TESTS`` is therefore empty.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-10844"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()

def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)

# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL frozen impl body (lies wholly inside `-- impl-start`/`-- impl-end`)
# and the FULL frozen `correct_fmIndex` tactic body (inside
# `-- proof-start`/`-- proof-end`), so every replacement lands entirely inside
# the region it means to edit.
_IMPL_GOLD = 'noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=\n  let tk := (cmTkW M).toInt\n  let pk := (cmPkW M).toInt\n  let qk := (cmQkW M).toInt\n  if tk = 0 then some 0\n  else do\n    let a ← fdiv (tk : ℝ) (pk : ℝ)\n    let b ← fdiv (tk : ℝ) (qk : ℝ)\n    let ra ← fsqrt a\n    let rb ← fsqrt b\n    pure (ra * rb)'

# The frozen `correct_fmIndex` tactic body.
_PROOF_GOLD = '  intro M w hrect hwT hwP hwQ\n  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩\n  exact nonzero_branch M w hrect hwT hwP hwQ hT'

# The frozen `impl_value` reduction body (retuned by the branch-reorder positive).
_IMPLVALUE_GOLD = '  unfold implementation_fmIndex\n  rfl'

# The FULL frozen `impl_value` declaration (statement included), restated by the
# spec-form and branch-reorder positives to the shape their impls reduce to.
_IMPLVALUE_FULL_GOLD = 'theorem impl_value (M : List (List ℕ)) :\n    implementation_fmIndex M\n      = if (cmTkW M).toInt = 0 then some (0 : ℝ)\n        else (do\n          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)\n          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)\n          let ra ← fsqrt a\n          let rb ← fsqrt b\n          pure (ra * rb)) := by\n  unfold implementation_fmIndex\n  rfl'

# The frozen `nonzero_branch` tactic body IN FULL, which the spec-form positive
# replaces with the shorter chain its own assembly needs.
_NONZERO_BODY_GOLD = '  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT\n  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]\n  have hP_int : 0 < cmPk M := P_pos M w hrect hTne\n  have hQ_int : 0 < cmQk M := Q_pos M hTne\n  have hT_int : 0 ≤ cmTk M := T_nonneg M\n  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int\n  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int\n  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int\n  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le\n  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le\n  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ\n  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]\n  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>\n      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _\n  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]\n  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))\n      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _\n  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]'

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_GOLD) == 1, "proof body drifted; update _PROOF_GOLD"
assert _BASE.count(_IMPLVALUE_GOLD) == 1, "impl_value body drifted"
assert _BASE.count(_IMPLVALUE_FULL_GOLD) == 1, "impl_value decl drifted"
assert _BASE.count(_NONZERO_BODY_GOLD) == 1, "nonzero_branch body drifted"

# ---------------------------------------------------------------------------
# Rival / positive impl bodies.
# ---------------------------------------------------------------------------
_POS_REORDER_IMPL = 'noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=\n  let tk := (cmTkW M).toInt\n  let pk := (cmPkW M).toInt\n  let qk := (cmQkW M).toInt\n  if tk ≠ 0 then\n    (do\n      let a ← fdiv (tk : ℝ) (pk : ℝ)\n      let b ← fdiv (tk : ℝ) (qk : ℝ)\n      let ra ← fsqrt a\n      let rb ← fsqrt b\n      pure (ra * rb))\n  else some 0'

_POS_REORDER_IMPLVALUE_FULL = 'theorem impl_value (M : List (List ℕ)) :\n    implementation_fmIndex M\n      = if (cmTkW M).toInt = 0 then some (0 : ℝ)\n        else (do\n          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)\n          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)\n          let ra ← fsqrt a\n          let rb ← fsqrt b\n          pure (ra * rb)) := by\n  unfold implementation_fmIndex\n  by_cases h : (cmTkW M).toInt = 0\n  · rw [if_neg (by rw [h]; simp), if_pos h]\n  · rw [if_pos h, if_neg h]'

_POS_INLINE_IMPL = 'noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=\n  if (cmTkW M).toInt = 0 then some 0\n  else do\n    let a ← fdiv (((cmTkW M).toInt : ℝ)) (((cmPkW M).toInt : ℝ))\n    let b ← fdiv (((cmTkW M).toInt : ℝ)) (((cmQkW M).toInt : ℝ))\n    let ra ← fsqrt a\n    let rb ← fsqrt b\n    pure (ra * rb)'

_ZERO_BRANCH_GOLD = 'theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :\n    implementation_fmIndex M = some 0 := by\n  rw [impl_value, if_pos h]'
assert _BASE.count(_ZERO_BRANCH_GOLD) == 1, "zero_branch drifted"

_POS_TOTALFORM_IMPL = 'noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=\n  let tk := (cmTkW M).toInt\n  let pk := (cmPkW M).toInt\n  let qk := (cmQkW M).toInt\n  -- total-arithmetic assembly: no case split and no partial step; the outcome\n  -- always names a real, and at a zero agreement count it is 0 automatically.\n  some (Real.sqrt ((tk : ℝ) / (pk : ℝ)) * Real.sqrt ((tk : ℝ) / (qk : ℝ)))'

_IMPLVALUE_FULL_TOTALFORM = 'theorem impl_value (M : List (List ℕ)) :\n    implementation_fmIndex M\n      = some (Real.sqrt (((cmTkW M).toInt : ℝ) / ((cmPkW M).toInt : ℝ))\n          * Real.sqrt (((cmTkW M).toInt : ℝ) / ((cmQkW M).toInt : ℝ))) := by\n  unfold implementation_fmIndex\n  rfl'

_ZERO_BRANCH_TOTALFORM = 'theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :\n    implementation_fmIndex M = some 0 := by\n  rw [impl_value M, h]\n  norm_num'

_NONZERO_BODY_TOTALFORM = '  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT\n  rw [impl_value M, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]\n  have hP_int : 0 < cmPk M := P_pos M w hrect hTne\n  have hQ_int : 0 < cmQk M := Q_pos M hTne\n  have hT_int : 0 ≤ cmTk M := T_nonneg M\n  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int\n  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int\n  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int\n  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le\n  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ\n  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]'

_POS_SPECFORM_IMPL = 'noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=\n  let tk := (cmTkW M).toInt\n  let pk := (cmPkW M).toInt\n  let qk := (cmQkW M).toInt\n  if tk = 0 then some 0\n  else do\n    -- spec-form assembly: the two counts are widened out of their words and\n    -- multiplied over ℝ, then one root of that exact product.\n    let r ← fsqrt ((pk : ℝ) * (qk : ℝ))\n    let v ← fdiv (tk : ℝ) r\n    pure v'

_IMPLVALUE_FULL_SPECFORM = 'theorem impl_value (M : List (List ℕ)) :\n    implementation_fmIndex M\n      = if (cmTkW M).toInt = 0 then some (0 : ℝ)\n        else (do\n          let r ← fsqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))\n          let v ← fdiv ((cmTkW M).toInt : ℝ) r\n          pure v) := by\n  unfold implementation_fmIndex\n  rfl'

_NONZERO_BODY_SPECFORM = '  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT\n  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]\n  have hP_int : 0 < cmPk M := P_pos M w hrect hTne\n  have hQ_int : 0 < cmQk M := Q_pos M hTne\n  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int\n  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int\n  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ\n  rw [fsqrt_of_nonneg _ hPQ.le]\n  show (fdiv ((cmTk M : ℝ)) (Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ))) >>=\n      fun v => pure v) = _\n  rw [fdiv_of_ne _ _ (ne_of_gt (Real.sqrt_pos.mpr hPQ))]\n  rfl'

# SQUARED-INDEX (drop both roots): return (T/P)·(T/Q) = T²/(P·Q) — the SQUARE of
# the index. Both divisions still go through the partial op, so it stays `some`
# on admissible inputs; it is simply the wrong number. Attacks clause 2.
_SQUARED_IMPL = 'noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=\n  let tk := (cmTkW M).toInt\n  let pk := (cmPkW M).toInt\n  let qk := (cmQkW M).toInt\n  if tk = 0 then some 0\n  else do\n    -- squared-index rival: multiply the two ratios directly, no square root.\n    let a ← fdiv (tk : ℝ) (pk : ℝ)\n    let b ← fdiv (tk : ℝ) (qk : ℝ)\n    pure (a * b)'

# SINGLE-RATIO (drop Q): return sqrt(T/P), ignoring the second marginal — not
# the geometric mean; attacks clause 2 where cmPk ≠ cmQk.
_SINGLE_IMPL = 'noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=\n  let tk := (cmTkW M).toInt\n  let pk := (cmPkW M).toInt\n  let qk := (cmQkW M).toInt\n  if tk = 0 then some 0\n  else do\n    -- single-ratio rival: only the first conditional ratio, no qk term.\n    let a ← fdiv (tk : ℝ) (pk : ℝ)\n    let ra ← fsqrt a\n    pure ra'

# FIXED-WIDTH PRODUCT: reduce the marginal product into a signed 64-bit window
# BEFORE the root. The two counts arrive already WIDENED out of their words, so
# the fold is the rival re-narrowing what the spec hands it in full. Spelled
# inline (no new `def`). Where the true product leaves the window the fold is
# negative, so `fsqrt` is `none` and the outcome names no real number.
_FIXED_WIDTH_IMPL = 'noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=\n  let tk := (cmTkW M).toInt\n  let pk := (cmPkW M).toInt\n  let qk := (cmQkW M).toInt\n  if tk = 0 then some 0\n  else do\n    -- fixed-width rival: the product of the two marginal counts is reduced\n    -- into a signed 64-bit window before the root is taken.\n    let r ← fsqrt ((((pk * qk) + 2 ^ 63) % 2 ^ 64 - 2 ^ 63 : ℤ) : ℝ)\n    let v ← fdiv (tk : ℝ) r\n    pure v'

# ZERO-BRANCH-WRONG: return the real number 1/2 on the cmTk = 0 subdomain
# instead of 0; correct on every cmTk ≠ 0 input. Attacks clause 1 by VALUE.
_ZERO_IMPL_BODY = 'noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=\n  let tk := (cmTkW M).toInt\n  let pk := (cmPkW M).toInt\n  let qk := (cmQkW M).toInt\n  if tk = 0 then\n    -- partial-domain: wrong value on the cmTk = 0 subdomain\n    some (1/2 : ℝ)\n  else do\n    let a ← fdiv (tk : ℝ) (pk : ℝ)\n    let b ← fdiv (tk : ℝ) (qk : ℝ)\n    let ra ← fsqrt a\n    let rb ← fsqrt b\n    pure (ra * rb)'

# GUARD ERASURE (the load-bearing rival): no case split on the agreement count
# at all; the assembly is entered unconditionally. On a total ℝ carrier this is
# an EQUAL function to gold (machine-checked) and therefore unrefutable; with
# partial division it names no real number at a zero-agreement, zero-marginal
# matrix, where clause 1 demands the real number 0.
_GUARDLESS_IMPL = 'noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=\n  let tk := (cmTkW M).toInt\n  let pk := (cmPkW M).toInt\n  let qk := (cmQkW M).toInt\n  -- guard-erasure rival: no case split on the agreement count at all; the\n  -- assembly is entered unconditionally.\n  do\n    let a ← fdiv (tk : ℝ) (pk : ℝ)\n    let b ← fdiv (tk : ℝ) (qk : ℝ)\n    let ra ← fsqrt a\n    let rb ← fsqrt b\n    pure (ra * rb)'

# ADMISSIBILITY: the frozen impl+proof, with THREE ground instances discharged
# before the general obligation — proving the modeled behavior is satisfiable at
# concrete inputs rather than only in the abstract.
#
#   * [[2,1],[1,3]] — a small non-degenerate matrix (cmTk = 8, cmPk = cmQk = 18).
#   * [[1,1,1,1,1,1]] — the DEGENERATE point (cmTk = 0, cmPk = 0, cmQk = 30),
#     where clause 1 demands the real number 0 while an unguarded assembly names
#     no real number. This instance is what makes the guard-erasure reject honest:
#     the spec's demand there is shown SATISFIABLE, so the rival fails for being
#     wrong and not for being asked the impossible.
#   * [[60000,60000],[60000,60000]] — the LARGE-COUNT regime, where the three
#     quantities are pinned BY EVALUATION (`decide`) and the non-degenerate branch
#     is shown to actually fire before clause 2 is discharged there.
_ADMISS_PROOF = '  have h1tk : cmTk [[2,1],[1,3]] = 8 := by decide\n  have h1pk : cmPk [[2,1],[1,3]] = 18 := by decide\n  have h1qk : cmQk [[2,1],[1,3]] = 18 := by decide\n  have h1wT : inWord (cmTk [[2,1],[1,3]]) := by\n    unfold inWord; rw [h1tk]; norm_num\n  have h1wP : inWord (cmPk [[2,1],[1,3]]) := by\n    unfold inWord; rw [h1pk]; norm_num\n  have h1wQ : inWord (cmQk [[2,1],[1,3]]) := by\n    unfold inWord; rw [h1qk]; norm_num\n  have _ground : problem_spec_fmIndex [[2,1],[1,3]]\n      (implementation_fmIndex [[2,1],[1,3]]) := by\n    refine ⟨fun h => zero_branch _ h,\n      fun hT => nonzero_branch _ 2 ?_ h1wT h1wP h1wQ hT⟩\n    intro r hr\n    fin_cases hr <;> rfl\n  have hztk : cmTk [[1,1,1,1,1,1]] = 0 := by decide\n  have hzpk : cmPk [[1,1,1,1,1,1]] = 0 := by decide\n  have hzqk : cmQk [[1,1,1,1,1,1]] = 30 := by decide\n  have hzwT : inWord (cmTk [[1,1,1,1,1,1]]) := by\n    unfold inWord; rw [hztk]; norm_num\n  have hzwP : inWord (cmPk [[1,1,1,1,1,1]]) := by\n    unfold inWord; rw [hzpk]; norm_num\n  have hzwQ : inWord (cmQk [[1,1,1,1,1,1]]) := by\n    unfold inWord; rw [hzqk]; norm_num\n  have _ground_degenerate : problem_spec_fmIndex [[1,1,1,1,1,1]]\n      (implementation_fmIndex [[1,1,1,1,1,1]]) := by\n    refine ⟨fun h => zero_branch _ h,\n      fun hT => nonzero_branch _ 6 ?_ hzwT hzwP hzwQ hT⟩\n    intro r hr\n    fin_cases hr <;> rfl\n  have htk : cmTk [[60000,60000],[60000,60000]] = 14399760000 := by decide\n  have hpk : cmPk [[60000,60000],[60000,60000]] = 28799760000 := by decide\n  have hqk : cmQk [[60000,60000],[60000,60000]] = 28799760000 := by decide\n  have hwbT : inWord (cmTk [[60000,60000],[60000,60000]]) := by\n    unfold inWord; rw [htk]; norm_num\n  have hwbP : inWord (cmPk [[60000,60000],[60000,60000]]) := by\n    unfold inWord; rw [hpk]; norm_num\n  have hwbQ : inWord (cmQk [[60000,60000],[60000,60000]]) := by\n    unfold inWord; rw [hqk]; norm_num\n  have hbig : (cmTkW [[60000,60000],[60000,60000]]).toInt ≠ 0 := by\n    rw [tkW_val [[60000,60000],[60000,60000]] hwbT, htk]; norm_num\n  have _rect_big : ∀ r ∈ [[60000,60000],[60000,60000]], r.length = 2 := by\n    intro r hr; fin_cases hr <;> rfl\n  have _ground_big : problem_spec_fmIndex [[60000,60000],[60000,60000]]\n      (implementation_fmIndex [[60000,60000],[60000,60000]]) :=\n    ⟨fun h => absurd h hbig, fun hT => nonzero_branch [[60000,60000],[60000,60000]] 2 _rect_big hwbT hwbP hwbQ hT⟩\n  intro M w hrect hwT hwP hwQ\n  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩\n  exact nonzero_branch M w hrect hwT hwP hwQ hT'

def _impl(new_impl):
    return _swap(_BASE, _IMPL_GOLD, new_impl)



# ---------------------------------------------------------------------------
# Witnesses. Each states ¬ problem_spec_fmIndex M (implementation_fmIndex M) at a
# concrete matrix, unfolds the impl, reduces the concrete integer quantities by
# `decide`, and closes either a real (in)equality or a `none = some _` clash.
# ---------------------------------------------------------------------------
_WIT_SQUARED = 'example : ¬ problem_spec_fmIndex [[1,1],[1,2]]\n    (implementation_fmIndex [[1,1],[1,2]]) := by\n  rintro ⟨_, h2⟩\n  have ht : (cmTkW [[1,1],[1,2]]).toInt = 2 := by\n    unfold cmTkW\n    rw [BitVec.toInt_ofInt, show cmTk [[1,1],[1,2]] = 2 from by decide]\n    norm_num [Int.bmod]\n  have hp : (cmPkW [[1,1],[1,2]]).toInt = 8 := by\n    unfold cmPkW\n    rw [BitVec.toInt_ofInt, show cmPk [[1,1],[1,2]] = 8 from by decide]\n    norm_num [Int.bmod]\n  have hq : (cmQkW [[1,1],[1,2]]).toInt = 8 := by\n    unfold cmQkW\n    rw [BitVec.toInt_ofInt, show cmQk [[1,1],[1,2]] = 8 from by decide]\n    norm_num [Int.bmod]\n  have hne : (cmTkW [[1,1],[1,2]]).toInt ≠ 0 := by rw [ht]; norm_num\n  have heq := h2 hne\n  rw [ht, hp, hq] at heq\n  unfold implementation_fmIndex at heq\n  rw [ht, hp, hq] at heq\n  norm_num [fdiv, fsqrt] at heq'

_WIT_SINGLE = 'example : ¬ problem_spec_fmIndex [[0,0,0],[2,3,3]]\n    (implementation_fmIndex [[0,0,0],[2,3,3]]) := by\n  rintro ⟨_, h2⟩\n  have ht : (cmTkW [[0,0,0],[2,3,3]]).toInt = 14 := by\n    unfold cmTkW\n    rw [BitVec.toInt_ofInt, show cmTk [[0,0,0],[2,3,3]] = 14 from by decide]\n    norm_num [Int.bmod]\n  have hp : (cmPkW [[0,0,0],[2,3,3]]).toInt = 14 := by\n    unfold cmPkW\n    rw [BitVec.toInt_ofInt, show cmPk [[0,0,0],[2,3,3]] = 14 from by decide]\n    norm_num [Int.bmod]\n  have hq : (cmQkW [[0,0,0],[2,3,3]]).toInt = 56 := by\n    unfold cmQkW\n    rw [BitVec.toInt_ofInt, show cmQk [[0,0,0],[2,3,3]] = 56 from by decide]\n    norm_num [Int.bmod]\n  have hne : (cmTkW [[0,0,0],[2,3,3]]).toInt ≠ 0 := by rw [ht]; norm_num\n  have heq := h2 hne\n  rw [ht, hp, hq] at heq\n  unfold implementation_fmIndex at heq\n  rw [ht, hp] at heq\n  norm_num [fdiv, fsqrt] at heq'

_WIT_FIXED_WIDTH = 'example : ¬ problem_spec_fmIndex [[60000,60000],[60000,60000]]\n    (implementation_fmIndex [[60000,60000],[60000,60000]]) := by\n  rintro ⟨_, h2⟩\n  have ht : (cmTkW [[60000,60000],[60000,60000]]).toInt = 14399760000 := by\n    unfold cmTkW\n    rw [BitVec.toInt_ofInt,\n      show cmTk [[60000,60000],[60000,60000]] = 14399760000 from by decide]\n    norm_num [Int.bmod]\n  have hp : (cmPkW [[60000,60000],[60000,60000]]).toInt = 28799760000 := by\n    unfold cmPkW\n    rw [BitVec.toInt_ofInt,\n      show cmPk [[60000,60000],[60000,60000]] = 28799760000 from by decide]\n    norm_num [Int.bmod]\n  have hq : (cmQkW [[60000,60000],[60000,60000]]).toInt = 28799760000 := by\n    unfold cmQkW\n    rw [BitVec.toInt_ofInt,\n      show cmQk [[60000,60000],[60000,60000]] = 28799760000 from by decide]\n    norm_num [Int.bmod]\n  have hne : (cmTkW [[60000,60000],[60000,60000]]).toInt ≠ 0 := by\n    rw [ht]; norm_num\n  have heq := h2 hne\n  rw [ht, hp, hq] at heq\n  unfold implementation_fmIndex at heq\n  rw [ht, hp, hq] at heq\n  norm_num [fdiv, fsqrt] at heq\n  exact Option.noConfusion heq'

# The clause-1 refutation point is the NON-DEGENERATE zero-agreement matrix
# [[1,1],[1,0]] (cmTk = 0 with cmPk = cmQk = 2 > 0), not the smaller [[1,1]]
# (whose cmPk is 0 — the same degenerate sub-domain the guard-erasure witness
# already occupies). Both marginal counts are pinned by `decide` so the point is
# demonstrated to be non-degenerate rather than asserted to be.
_WIT_ZERO = 'example : ¬ problem_spec_fmIndex [[1,1],[1,0]]\n    (implementation_fmIndex [[1,1],[1,0]]) := by\n  rintro ⟨h1, _⟩\n  have ht : (cmTkW [[1,1],[1,0]]).toInt = 0 := by\n    unfold cmTkW\n    rw [BitVec.toInt_ofInt, show cmTk [[1,1],[1,0]] = 0 from by decide]\n    norm_num [Int.bmod]\n  have hp : (cmPkW [[1,1],[1,0]]).toInt = 2 := by\n    unfold cmPkW\n    rw [BitVec.toInt_ofInt, show cmPk [[1,1],[1,0]] = 2 from by decide]\n    norm_num [Int.bmod]\n  have hq : (cmQkW [[1,1],[1,0]]).toInt = 2 := by\n    unfold cmQkW\n    rw [BitVec.toInt_ofInt, show cmQk [[1,1],[1,0]] = 2 from by decide]\n    norm_num [Int.bmod]\n  have heq := h1 ht\n  unfold implementation_fmIndex at heq\n  rw [ht] at heq\n  norm_num at heq'

_WIT_GUARDLESS = 'example : ¬ problem_spec_fmIndex [[1,1,1,1,1,1]]\n    (implementation_fmIndex [[1,1,1,1,1,1]]) := by\n  rintro ⟨h1, -⟩\n  have ht : (cmTkW [[1,1,1,1,1,1]]).toInt = 0 := by\n    unfold cmTkW\n    rw [BitVec.toInt_ofInt, show cmTk [[1,1,1,1,1,1]] = 0 from by decide]\n    norm_num [Int.bmod]\n  have hp : (cmPkW [[1,1,1,1,1,1]]).toInt = 0 := by\n    unfold cmPkW\n    rw [BitVec.toInt_ofInt, show cmPk [[1,1,1,1,1,1]] = 0 from by decide]\n    norm_num [Int.bmod]\n  have heq := h1 ht\n  unfold implementation_fmIndex at heq\n  rw [ht, hp] at heq\n  norm_num [fdiv] at heq\n  exact Option.noConfusion heq'


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_fmIndex` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_GOLD, _POS_REORDER_IMPL),
                        _IMPLVALUE_FULL_GOLD, _POS_REORDER_IMPLVALUE_FULL),
        "rationale": (
            "a correct reshape that guards the non-zero (cmTk ≠ 0) case first and "
            "falls through to the real number 0 — behaviourally identical, "
            "straight-line code, no new induction. It must satisfy both clauses, "
            "else the spec is SPEC-TOO-STRONG. Only the `impl_value` reduction "
            "lemma is retuned (`by_cases` on `cmTk M = 0`, each reshaped arm closed "
            "by `rw`); the `correct_fmIndex` STATEMENT is byte-identical and no new "
            "lemma/axiom/assumption is introduced. This positive is the one that "
            "guards against the new clause being over-read as 'the zero test must "
            "be written first': it keeps the guard but moves it, and it verifies. "
            "Verified with a real build (exit 0)."
        ),
    },
    {
        "id": "pos-inline-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _POS_INLINE_IMPL),
        "rationale": (
            "cheapest honest impl: drop the tk/pk/qk temporaries and read the "
            "words inline in both branches; it still forms each conditional ratio "
            "before any product (never the cross product of the marginals) and "
            "still routes every step through the partial arithmetic. "
            "Definitionally the same value, so the frozen `impl_value`/`rfl` "
            "reduction and the whole frozen proof close unchanged. MUST verify, "
            "else SPEC-TOO-STRONG. NOTE (recorded rather than hidden): because it "
            "is definitionally equal to the frozen impl this is a WEAK positive on "
            "its own — it costs one build and guards against a spec that somehow "
            "depended on the let-scaffold, but it cannot detect over-constraint. "
            "`pos-branch-reorder` and `pos-specform-product` carry the real "
            "SPEC-TOO-STRONG load. Verified with a real build (exit 0)."
        ),
    },
    {
        "id": "pos-total-arithmetic-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_swap(_swap(_BASE, _IMPL_GOLD, _POS_TOTALFORM_IMPL),
                        _IMPLVALUE_FULL_GOLD, _IMPLVALUE_FULL_TOTALFORM),
                  _ZERO_BRANCH_GOLD, _ZERO_BRANCH_TOTALFORM),
            _NONZERO_BODY_GOLD, _NONZERO_BODY_TOTALFORM),
        "rationale": (
            "THE ECHO THIS CELL'S HOLE USED TO BE. It writes the index with no "
            "case split at all and with Mathlib's TOTAL division and root, then "
            "asserts the outcome always names a real. On the previous ℝ-carrier "
            "spec this shape was the counterexample the audit found "
            "(guard erasure), because total arithmetic silently turns the "
            "degenerate 0/0 into 0. It is retained as a POSITIVE, not a reject, "
            "and the reason is a machine-checked theorem rather than a judgement: "
            "on the ENTIRE admissible domain (rectangular M, all three counts "
            "inWord) this assembly is EXTENSIONALLY EQUAL to the frozen one. "
            "Proof: on `(cmTkW M).toInt = 0` both give `some 0` (the frozen one "
            "by its branch, this one because √(0/P)·√(0/Q) = 0 whether or not a "
            "marginal count vanishes); on `≠ 0` both marginal counts are strictly "
            "positive (`P_pos`/`Q_pos`, each dominates the agreement count), so "
            "every `fdiv`/`fsqrt` step in the frozen assembly takes its `some` "
            "branch and the two agree term for term. Since the two are the same "
            "function here, NO postcondition can hold of one and fail of the "
            "other, so demanding that this be rejected would be "
            "SPEC-TOO-STRONG — it would fail a genuinely correct implementation. "
            "Its faithful Python counterpart keeps the library's own guard (an "
            "unguarded float 0./0. is nan, not 0), so its patch resolves. What "
            "the repair actually buys is visible by contrast with the "
            "`guard-erasure` reject: that one erases the guard while routing "
            "through the PARTIAL arithmetic, which is the faithful model of the "
            "float ops, and it is refuted at [[1,1,1,1,1,1]]. Verified with a "
            "real build (exit 0)."
        ),
    },
    {
        "id": "pos-specform-product",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_swap(_BASE, _IMPL_GOLD, _POS_SPECFORM_IMPL),
                  _IMPLVALUE_FULL_GOLD, _IMPLVALUE_FULL_SPECFORM),
            _NONZERO_BODY_GOLD, _NONZERO_BODY_SPECFORM),
        "rationale": (
            "a correct reshape that forms the product of the two marginal counts "
            "in EXACT arithmetic and takes a single root of it — the shape clause 2 "
            "is literally stated in — instead of multiplying two conditional roots. "
            "Over exact reals the two are equal (for cmTk ≥ 0 and cmPk, cmQk > 0, "
            "both frozen lemmas), so this impl is faithful and MUST verify; a spec "
            "admitting only the two-root assembly would be SPEC-TOO-STRONG. Its "
            "faithful Python counterpart is `np.sqrt(int(pk) * int(qk))` over "
            "widened ints, which is finite on the overflow workload and resolves. "
            "Unlike `pos-inline-cheapest` it is NOT definitionally equal to the "
            "frozen impl — the frozen `impl_value`/`rfl` fails on it — so the "
            "reduction lemma is restated and `nonzero_branch` uses the shorter "
            "chain its own assembly needs. `impl_value`/`nonzero_branch` are "
            "reduction lemmas, not protected obligations; `theorem correct_fmIndex` "
            "is byte-identical and no new declaration/axiom/`sorry` appears. It "
            "also draws the `fixed-width-product` line from the other side: "
            "forming that product exactly is CORRECT, and only reducing it into a "
            "bounded window is wrong. It doubles as the ungrounded-oracle-echo "
            "control — it returns clause 2's own right-hand side — showing that "
            "lane has no refutable content here. Verified with a real build "
            "(exit 0)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at concrete inputs, including the degenerate
    # point the load-bearing reject dies at.
    # =====================================================================
    {
        "id": "admiss-nondegenerate-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at THREE concrete rectangular matrices "
            "before the general proof, each via the frozen "
            "`zero_branch`/`nonzero_branch` lemmas with the rectangularity witness "
            "closed by `fin_cases`. First `[[2,1],[1,3]]` (cmTk = 8 > 0, "
            "cmPk = cmQk = 18 > 0 — small non-degenerate). Then the DEGENERATE "
            "`[[1,1,1,1,1,1]]` (cmTk = 0, cmPk = 0, cmQk = 30): clause 1 demands "
            "the real number 0 there, and discharging it proves that demand is "
            "SATISFIABLE — which is what makes the `guard-erasure` reject honest "
            "rather than an impossible ask, since that is the exact point the "
            "unguarded assembly names no real number at. Then the LARGE-COUNT "
            "matrix `[[60000,60000],[60000,60000]]`, quantities pinned BY "
            "EVALUATION (`decide`) at cmTk = 14399760000 and "
            "cmPk = cmQk = 28799760000, with the non-degenerate branch shown to "
            "actually fire (`cmTk ≠ 0`) before clause 2 is discharged there — the "
            "regime a bounded arithmetic would already have failed in. On a total "
            "carrier the analogue of PRECOND-TOO-STRONG is the obligation being "
            "unsatisfiable at an F2P-shaped or degenerate input, so these three "
            "points test it directly. Nothing is assumed: the theorem STATEMENT is "
            "byte-identical, all three instances are `have`s inside the existing "
            "tactic body, and no new declaration/axiom/`sorry` is introduced. "
            "Verified with a real build (exit 0)."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete matrix and the refinement argument for why its faithful real
    # counterpart would NOT resolve the F2P / P2P tests.
    # =====================================================================
    {
        "id": "guard-erasure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_GUARDLESS_IMPL),
        "refinement": (
            "dropping the zero-agreement case and entering the assembly "
            "unconditionally. Its faithful counterpart is the patched return line "
            "with the trailing conditional removed, so on a clustering with no "
            "co-grouped pair it divides zero by zero and the score comes back "
            "non-finite instead of 0. A pre-existing P2P test asserts exactly that "
            "a worst-case clustering (one class, every sample in its own cluster) "
            "scores 0, so that patch FIXES the reported overflow and REGRESSES "
            "this, and does not resolve. This is the class the `ℝ`-carrier version "
            "of this bundle could not express at all: over total real arithmetic "
            "the guarded and unguarded assemblies are the SAME FUNCTION (proved by "
            "`funext`), so no postcondition could separate them. Modeling division "
            "and root as partial is what makes the omission observable."
        ),
        "rationale": (
            "REJECT from clause 1 `(cmTkW M).toInt = 0 → result = some 0`: entering "
            "the assembly unconditionally, the rival's first division at a "
            "zero-agreement matrix whose first marginal is also 0 is a division by "
            "zero, so it yields `none` while clause 1 demands `some 0`. Refuted at "
            "`[[1,1,1,1,1,1]]` (cmTk = 0, cmPk = 0, cmQk = 30) — a fully admissible "
            "input: it is rectangular and all three counts sit in one word, so no "
            "hypothesis excludes it. Distinct from `zero-branch-nonzero`, which "
            "attacks the same clause by returning a WRONG REAL there; this one "
            "returns NO REAL. If it verifies, clause 1 is hollow and the case split "
            "on the agreement count carries no information (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_GUARDLESS,
    },
    {
        "id": "squared-index-no-roots",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SQUARED_IMPL),
        "refinement": (
            "returning (cmTk/cmPk)·(cmTk/cmQk) = cmTk²/(cmPk·cmQk) is the SQUARE "
            "of the Fowlkes–Mallows index, not the index. It is finite and in "
            "[0,1], so it would not crash, but it is the wrong number: the "
            "exact-value P2P tests (a perfect match scores 1.0 — the square also "
            "gives 1 there, but everywhere else diverges, e.g. index 1/2 becomes "
            "1/4) would FAIL. A real patch dropping both roots would not resolve."
        ),
        "rationale": (
            "REJECT from clause 2 `result = some (cmTk / √(cmPk·cmQk))`: the rival "
            "omits both square roots, so its value is the square of the spec's. "
            "Refuted at `[[1,1],[1,2]]` (cmTk = 2, cmPk = cmQk = 8): the spec "
            "demands 2/√64 = 1/4 but the rival returns (2/8)·(2/8) = 1/16. If it "
            "verifies, clause 2 does not force the geometric-mean normalisation "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_SQUARED,
    },
    {
        "id": "single-ratio-drop-qk",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SINGLE_IMPL),
        "refinement": (
            "returning only √(cmTk/cmPk) ignores the second marginal cmQk "
            "entirely. It is finite and in [0,1] but is not the geometric mean of "
            "the two conditional ratios: whenever the two marginals differ it is "
            "the wrong value (e.g. cmTk/cmPk = 1, cmTk/cmQk = 1/4 gives 1 instead "
            "of 1/2). The asymmetric P2P value tests (homogeneous-but-not-complete "
            "vs complete-but-not-homogeneous) would FAIL. A real patch using a "
            "single marginal would not resolve."
        ),
        "rationale": (
            "REJECT from clause 2: `√(cmTk/cmPk)` differs from "
            "`cmTk / √(cmPk·cmQk)` unless cmPk = cmQk. Refuted at "
            "`[[0,0,0],[2,3,3]]` with ASYMMETRIC marginals (cmTk = 14, cmPk = 14, "
            "cmQk = 56): the spec demands 14/√784 = 1/2 but the rival returns "
            "√(14/14) = 1. This probes clause 2 at a point distinct from the "
            "squared-index rival (asymmetric rather than symmetric marginals), so "
            "the two rivals do not share a sub-domain. If it verifies, the spec "
            "does not force BOTH marginals to enter (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_SINGLE,
    },
    {
        "id": "fixed-width-product",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FIXED_WIDTH_IMPL),
        "refinement": (
            "forming the product of the two marginal counts inside a bounded "
            "signed 64-bit window is exactly the arithmetic the defended surface "
            "must not perform. On the large-count workload the F2P test exercises, "
            "the true product exceeds that window, the reduced value is NEGATIVE, "
            "and the square root of a negative quantity is not a real number — the "
            "real-world symptom is a non-finite score. The F2P test asserts the "
            "returned score is finite, so it would FAIL; a real patch that still "
            "forms that bounded product would not resolve. Clause 2 widens both "
            "counts out of their words before multiplying over ℝ, so it genuinely "
            "demands the exact product and this rival genuinely misses it."
        ),
        "rationale": (
            "REJECT from clause 2: the rival roots the WINDOW-REDUCED product "
            "rather than the true one. Refuted at "
            "`[[60000,60000],[60000,60000]]` (cmTk = 14399760000, "
            "cmPk = cmQk = 28799760000): the true product ≈ 8.29·10²⁰ leaves the "
            "64-bit window, so the fold is negative, `fsqrt` of it is `none`, and "
            "the outcome names no real number while clause 2 demands `some` of a "
            "positive value. This is the only rival probing the LARGE-COUNT end of "
            "the domain — the two other clause-2 rivals sit at tiny matrices where "
            "no reduction fires. If it verifies, clause 2 does not force the "
            "marginal product to be formed exactly (SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_FIXED_WIDTH,
    },
    {
        "id": "zero-branch-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ZERO_IMPL_BODY),
        "refinement": (
            "correct on every cmTk ≠ 0 input but returns 1/2 when the agreement "
            "count is 0 (no co-grouped pair). The real index is 0 there; a "
            "clustering pair with zero agreement must score 0, and the P2P tests "
            "covering that degenerate case would see 1/2 and FAIL. A real patch "
            "returning a non-zero constant on the zero-agreement subdomain would "
            "not resolve. Partial-domain: diverges only on the cmTk = 0 subdomain."
        ),
        "rationale": (
            "REJECT from clause 1 `(cmTkW M).toInt = 0 → result = some 0`: the "
            "rival's zero branch returns `some (1/2)`, so the postcondition cannot "
            "hold. Refuted at `[[1,1],[1,0]]` (cmTk = 0 with cmPk = cmQk = 2, both "
            "pinned by `decide`), a point on the OTHER clause's sub-domain from the "
            "three clause-2 rivals. It shares clause 1 with `guard-erasure` but "
            "fails differently — a WRONG REAL rather than NO REAL — and at a "
            "different POINT: this matrix has both marginal counts STRICTLY "
            "POSITIVE, so clause 1's demand here is not entangled with the "
            "partial-arithmetic collapse the guard-erasure rival dies at (that one "
            "needs cmPk = 0). The two are therefore not one case twice, and the "
            "clause-1 lane covers the non-degenerate zero-agreement regime as well "
            "as the degenerate one. If it verifies, clause 1 is hollow "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _WIT_ZERO,
    },
]


# ---------------------------------------------------------------------------
# Nagini → lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus a 2-case AXIOM lane.
#
#   sibling case                       -> here
#   ---------------------------------------------------------------------
#   prepatch-overflow-order            -> fixed-width-product         PORTED
#       (re-expressed: the sibling refutes it at an axiom's representability
#        precondition; here there is no axiom, so the bounded reduction is
#        spelled inline in the impl and refuted by a concrete large-count
#        witness. The pure-reassociation half of the sibling case IS vacuous
#        here and was measured to verify; the fixed-width half is not.)
#   no-square-roots-squared-index      -> squared-index-no-roots      PORTED
#   single-ratio-drop-qk               -> single-ratio-drop-qk        PORTED
#   zero-branch-nonzero-partial-domain -> zero-branch-nonzero         PORTED
#   pos-control-branch-reorder         -> pos-branch-reorder          PORTED
#   pos-control-inline-cheapest        -> pos-inline-cheapest         PORTED
#   admissibility-large-count-regime   -> admiss-nondegenerate-ground RE-EXPRESSED
#       (now discharged at the sibling's large-count regime AND at the degenerate
#        zero-marginal point, so the lane certifies satisfiability at both ends.)
#   AXIOM_TESTS (2)                    -> (none)              DROPPED (G-AX)
#   (no sibling case)                  -> pos-specform-product        ADDED
#       (the reject-lane omission recast as a soundness positive: the reshape the
#        sibling could refute via an axiom precondition is CORRECT on this
#        carrier, so it is tested in the direction where it has content. It also
#        serves as the ungrounded-oracle-echo control.)
#   (no sibling case)                  -> guard-erasure               ADDED
#       (the class a TOTAL real carrier cannot express: over Mathlib's total `/`
#        and `Real.sqrt` the guarded and unguarded assemblies are the same
#        function, so the zero-agreement case split was unspecifiable. Modeling
#        the library's division and root as partial makes it a real rival, and it
#        is refuted at a fully admissible degenerate matrix.)
#
# See the module docstring's "OMITTED nagini cases" and the assessment payload
# for the full reasoning on the two vacuous drops.
AXIOM_TESTS = []
