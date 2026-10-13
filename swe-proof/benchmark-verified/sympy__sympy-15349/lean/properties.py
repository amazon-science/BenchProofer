"""properties.py — G-PBT falsification battery for sympy__sympy-15349 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a two-shape input domain):

  toRotationMatrix (q : Quat) (v : Option (ℚ × ℚ × ℚ)) : Mat
      result is pinned entry-by-entry to the inputs, via s = scale q =
      (a²+b²+c²+d²)⁻¹, over two shapes selected by v:
        * v = none          → a 3×3 matrix, nine quadratic-in-components entries;
        * v = some (x,y,z)   → a 4×4 matrix: the same nine entries as the
          top-left block, a fourth column whose first three slots are the point
          coordinate minus the block-row contracted against the point, and a
          bottom row (0,0,0,1).
      Out-of-range reads of the accessor are pinned to 0.

  The LOAD-BEARING clause is the SIGN of the cross term in the (1,2) entry of
  the 3×3 block:
      3×3 : result.get 1 2 = 2·s·(c·d − b·a)          -- e12
      4×4 : result.get 1 2 = 2·s·(c·d − b·a)          -- same block entry
      4×4 : result.get 1 3 = y − x·e10 − y·e11 − z·e12 -- e12 inherited into the
                                                          translation column
  A pre-patch surface computes 2·s·(c·d + b·a) instead; that surface fails
  exactly these clauses (the F2P observable). So every rival below that keeps the
  frozen spec but reintroduces the + sign, or otherwise mis-places / drops the
  minus, MUST be rejected. If any verifies the spec is SPEC-TOO-WEAK — it would
  admit an impl whose faithful patch does NOT resolve
  test_quaternion_conversions / test_quaternion_rotation_iss1593.

  The single ``let m12`` binding feeds BOTH matrix shapes and the inherited
  translation entry, so editing IT attacks all three clauses at once
  (``weak-prepatch-sign``). That does NOT mean nagini's separate 3×3-sign and
  4×4-sign rivals collapse to one impl edit here: the two shapes have SEPARATE
  accessor lists, so an inline wrong-signed term in the affine accessor mis-signs
  the 4×4 block entry while leaving the 3×3 shape byte-for-byte gold
  (``weak-block-sign-4x4-only``, machine-checked: the 4×4 (1,2) witness holds of
  it, the 3×3 (1,2) witness does not). The affine-only third clause (the
  inherited translation entry) is attacked SEPARATELY again by a rival that keeps
  the whole block correct and mis-signs only the translation column.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds its numeric
    inputs at read-only (fractional) permission and rejects a rival that
    overwrites one for insufficient permission. Lean is referentially
    transparent: ``q`` and ``v`` are immutable values and the result ``Mat`` is
    freshly constructed, so there is no half-permission to violate and no
    aliasing to exploit. This class has NO expressible instance here; no
    substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean, and this is DEMONSTRATED
    rather than asserted. ``implementation_*`` is a total Lean ``def``, and the
    two ways to spell a diverging one both fail to ELABORATE, so neither is a
    variant the gate could even judge:
      - a self-recursive ``def`` with no decreasing measure is rejected by the
        equation compiler — ``fail to show termination for
        implementation_toRotationMatrix … failed to infer structural recursion:
        … it is unchanged in the recursive calls``;
      - marking it ``partial`` does not help: ``failed to compile 'partial'
        definition … could not prove that the type Quat → Option (ℚ × ℚ × ℚ) →
        Mat is nonempty`` (``Mat`` has no ``Inhabited`` instance), and
        ``partial`` is a banned token under ``variant_scope`` anyway.
    Note this bundle sets NO ``loom.semantics.termination`` option — that option
    is velvet-only and appears in zero lean ``Solution.lean`` files in the
    corpus — so the ``"partial"``-semantics reading (a non-terminating impl
    verifying vacuously, i.e. a known spec HOLE) does not apply here. The class
    is vacuous because the carrier rejects the impl, not because a witness could
    not be built for one.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The bundle declares NO ``opaque``/``axiom``
    (meta.json axioms == [], deep_model_references == []): every entry, including
    the patched one, is spelled out as exact ℚ arithmetic in the components, so
    there is no answer key an impl could echo without doing the work. The honest
    analogue is the cheapest-correct POSITIVE CONTROL below.

  * UNIQUENESS (pre-patch sign) — APPLIES, load-bearing. Ported as the sign-flip
    rival (the literal pre-patch line) plus the swap-cd, partial-domain,
    translation-inheritance, transpose, 4×4-block-sign, affine-bottom-row,
    both-branch dimension, and both-branch out-of-range-default rivals, each
    attacking a distinct facet of "which off-diagonal is negative, on the whole
    domain, in both shapes, with the container's shape and its off-shape reads
    pinned too — in EACH shape separately".

  * EXCLUDED-INPUT LATITUDE — deliberately NOT a rival, and this is a measured
    disposition rather than an oversight. The frozen obligation is hypothesized on
    nonzero norm, so an impl free to return anything at ``a=b=c=d=0`` still
    satisfies it: an impl returning 99 at the (0,0) slot exactly when the norm is
    zero and the frozen value otherwise was built and DOES verify (with the guard
    rewritten away by ``if_neg`` on the theorem's own hypothesis). That is the
    hypothesis behaving as written, not a spec hole — ``scale`` is a division by
    that norm, so the excluded point is precisely where the modeled quantity does
    not exist, and the F2P exercises no zero quaternion. Recorded so a later
    reader does not mistake the absence of such a rival for an untested clause.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
concrete quaternion (and point, for the translation rival); each was built
(against the rival) and rebuilt (against the frozen solution) to confirm it
HOLDS of its rival and FAILS on gold. ``decide`` stalls on ℚ normalization here,
so each witness destructures the postcondition conjunction, unfolds the spec +
impl + ``scale`` at the offending entry, reduces the nested-list accessor with
``simp only [... pure, List.getD]`` and closes the concrete ℚ (in)equality with
``norm_num``. The out-of-range rival's witness instead instantiates the
postcondition's quantified clause at a concrete out-of-range index pair,
discharging the ``3 ≤ i`` side condition by ``norm_num`` rather than assuming it.
All witnesses state their refutation at LITERAL inputs (nonzero norm holds by
construction), so no witness binds a hypothesis and the gate's inconsistency
probe has nothing to flag.

The gold-side failure mode is the strongest one available on this carrier and was
read from the real build logs, not inferred: ``norm_num`` PROVES the projected
equation for the frozen impl, so the destructured hypothesis reduces to
``hh : True`` and the build fails as ``unsolved goals … ⊢ False``. Against each
rival the same script leaves the concrete false ℚ equation and closes.

That the exit code tracks the CLAIM rather than some fixed syntactic obstacle is
machine-checked per case, two independent ways, on real builds:

  * TYPE-REVEAL. Appending one step that forces the destructured hypothesis's
    type to print (``exact (hh : Nat)``) and building on each side gives
    ``has type True`` on gold — ``simp``/``norm_num`` PROVED the equation there —
    against ``No goals to be solved`` on the rival, where the same script had
    already derived ``False`` from the equation and closed the goal. So gold's
    exit code reports a satisfied spec, not an unfolding failure, a missing
    identifier, a type error, or a timeout.
  * CLAIM-FLIP. A file differing from the witness ONLY in the claim — the ``¬``
    dropped, i.e. asserting the spec HOLDS at that same input for that same
    impl, closed by the frozen straight-line ``rfl``-per-entry shape — INVERTS
    both exit codes: it builds against the frozen solution and FAILS against the
    rival, for all 11 cases. A gold-side error that carried no information about
    the claim would have reproduced byte-identically instead.

BINDER COVERAGE. The spec predicate binds ``q.a``, ``q.b``, ``q.c``, ``q.d``,
``v`` (and ``x/y/z`` inside ``some``). The 11 reject witnesses state their
refutations at 9 DISTINCT ``(q, v)`` points, and the variation is MEANINGFUL
rather than two spellings of one point: each rival's witness point is one where
that rival's own value at the attacked slot differs from the frozen value,
machine-checked in both directions (the spec's literal value at the slot builds
against gold and FAILS against the rival; the rival's literal value builds
against the rival and FAILS against gold).
  * ``q.a`` : 2, 1, 3, 1, 1, 1, 3, 1, 2, 1, 1 — nonzero in every witness, which
    is forced rather than incidental: the ``b·a`` / ``d·a`` cross terms the
    load-bearing clause turns on all vanish at a = 0, so a witness there would
    discriminate nothing on the sign rivals;
  * ``q.b`` : 1, 1, 2, 1, 1, 1, 1, 2, 3, 1, 3;
  * ``q.c`` : 1, 2, 0, 0, 1, 1, 4, 3, 1, 1, 2;
  * ``q.d`` : 1, 3, 0, 0, 1, 1, 2, 1, 4, 1, 1;
  * ``v``   : ``none`` for the block / 3×3-dimension / 3×3-out-of-range rivals
    AND five ``some`` points — (2,3,5), (1,2,3), (1,1,2), (1,2,3), (3,1,4) — so
    both matrix shapes and the ``x/y/z`` coordinates are exercised.
Three rivals (transpose, wrong-column-count, out-of-range-default) share the
point q = (1,1,1,1), v = none deliberately: they attack three DIFFERENT clauses
(an off-diagonal entry, the column count, the quantified off-shape convention),
and each is refuted there while the other two witnesses hold of gold at that same
point — so the shared point is three separate discriminations, not one repeated.

CLAUSE COVERAGE. Every syntactic class of clause in the postcondition carries at
least one rival that attacks it and nothing else:
  * block entry values, both shapes: sign, swap-cd, partial-domain, transpose,
    block-sign-4x4-only;
  * the inherited translation column: translation-inheritance;
  * the affine bottom row (homogeneous coordinate): affine-bottom-row;
  * the dimension records, EACH branch separately: wrong-column-count (none),
    wrong-dims-4x4 (some);
  * the BINDER-carrying clauses — ``∀ i j, 3 ≤ i ∨ 3 ≤ j → get i j = 0`` in the
    ``none`` branch and ``∀ i j, 4 ≤ i ∨ 4 ≤ j → get i j = 0`` in the ``some``
    branch. These are two SEPARATE clauses over two separate accessor lists with
    two different bounds, so they get a rival each: out-of-range-default (3×3,
    witness at (3,0), ROW side of the disjunction) and
    out-of-range-default-4x4 (4×4, witness at (0,4), COLUMN side). Each edits
    only its own branch's accessor, so neither attests to the other's
    convention, and between them both halves of the disjunction are exercised.
    These are the only cases that instantiate a quantifier; every other rival
    attacks a closed equation.

PROBED AND NOT SHIPPED (recorded so a later reader does not re-spend the builds).
Nine further WRONG impls, aimed at whatever the shipped rivals leave unattacked,
were built against the frozen spec and ALL were rejected — no spec hole among
them: the (0,1) off-diagonal sign; a DIAGONAL entry (m11 reading c² for d², a
clause no shipped rival touches); the 2-weight dropped from m00; the ``none``
branch's ``rows`` (only its ``cols`` is shipped); the (0,3) and (2,3) translation
entries (only (1,3) is shipped); ``s`` squared at its impl binding site; and a
nonzero slot in the affine bottom row's ZERO part (only its (3,3) one-slot is
shipped). Three further CORRECT reshapes were built and all VERIFY, so no
soundness hole either: the match-based accessor (shipped as ``pos-match-accessor``
once its proof was closed), the (1,2) entry distributed over its subtraction
(``2·s·(c·d) − 2·s·(b·a)``, ring-equal but not defeq — needs ``ring`` at the
(1,2) and (1,3) slots), and ``s`` spelled ``1 / norm`` instead of ``norm⁻¹``
(needs ``one_div`` and ``scale`` in the simp set, then ``ring``, at every entry;
``rfl`` closes only the two dimension clauses).

OMITTED nagini cases (see assessment): the frame/permission-mutation rival
(VACUOUS on a referentially-transparent carrier — no half-permission input
exists to over-write) and the AXIOM_TESTS lane (this bundle declares no axiom /
deep-model reference — G-AX skips — and the axiom lane is not this gate's job).
Nagini's two pre-patch-sign rivals are BOTH ported: the 3×3 one as the shared-
binding sign flip, the 4×4 one as ``weak-block-sign-4x4-only``, which is a
genuinely separate impl edit because the two shapes have separate accessor lists.
Nagini's helper-vocabulary positive is ported inverted as ``pos-inline-scale``
(gold names a helper where nagini's gold inlined, so the reshape inlines).

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; every
matrix entry is modeled DEEPLY as exact ℚ arithmetic over the inputs, so there
is no in-model axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15349"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (each verified unique inside Solution.lean at load).
# ---------------------------------------------------------------------------

# The load-bearing binding: the (1,2) block entry with its minus cross term.
_M12_GOLD = "  let m12 := 2 * s * (q.c * q.d - q.b * q.a)"
# The (2,1) block entry (the OTHER cd off-diagonal, plus cross term).
_M21_GOLD = "  let m21 := 2 * s * (q.c * q.d + q.b * q.a)"
# The inherited translation entry in the affine branch (linear in m12).
_M13_GOLD = "      let m13 := y - x * m10 - y * m11 - z * m12"
# The 3×3 branch's declared dimensions.
_DIM3_GOLD = "        rows := 3, cols := 3,"
# The 4×4 (affine) branch's declared dimensions.
_DIM4_GOLD = "        rows := 4, cols := 4,"
# The 3×3 accessor's row-major nested list.
_GET3_GOLD = (
    "          (([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]].getD i []).getD j 0) }"
)
# The 4×4 accessor's row-major nested list (the affine branch's own accessor:
# top-left block, translation column, and the pinned (0,0,0,1) bottom row).
_GET4_GOLD = (
    "          (([[m00, m01, m02, m03], [m10, m11, m12, m13],\n"
    "             [m20, m21, m22, m23], [0, 0, 0, 1]].getD i []).getD j 0) }"
)

# The whole 9-line block of entry bindings (unique to the impl region: the spec
# uses e00…e22, the impl uses m00…m22).
_MBLOCK_GOLD = (
    "  let m00 := 1 - 2 * s * (q.c ^ 2 + q.d ^ 2)\n"
    "  let m01 := 2 * s * (q.b * q.c - q.d * q.a)\n"
    "  let m02 := 2 * s * (q.b * q.d + q.c * q.a)\n"
    "  let m10 := 2 * s * (q.b * q.c + q.d * q.a)\n"
    "  let m11 := 1 - 2 * s * (q.b ^ 2 + q.d ^ 2)\n"
    "  let m12 := 2 * s * (q.c * q.d - q.b * q.a)\n"
    "  let m20 := 2 * s * (q.b * q.d - q.c * q.a)\n"
    "  let m21 := 2 * s * (q.c * q.d + q.b * q.a)\n"
    "  let m22 := 1 - 2 * s * (q.b ^ 2 + q.c ^ 2)"
)

# Frozen proof anchors (whole refine lines of each branch).
_NONE_REFINE = (
    "      refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, ?_⟩"
)
_SOME_REFINE = (
    "      refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl,\n"
    "        rfl, rfl, rfl, rfl, ?_⟩"
)
_INTRO_QV = "  intro q v _\n"

for _a in (_M12_GOLD, _M21_GOLD, _M13_GOLD, _DIM3_GOLD, _DIM4_GOLD, _GET3_GOLD,
           _GET4_GOLD, _MBLOCK_GOLD, _NONE_REFINE, _SOME_REFINE, _INTRO_QV):
    assert _BASE.count(_a) == 1, f"anchor drifted / not unique: {_a[:40]!r}"


# ---------------------------------------------------------------------------
# Witness builder. Destructure the postcondition conjunction at the offending
# entry, unfold spec + impl + scale, reduce the nested-list accessor, close the
# concrete ℚ (in)equality with norm_num (decide stalls on ℚ normalization).
# ---------------------------------------------------------------------------
_WIT_TAC = (
    "  simp only [implementation_toRotationMatrix, scale, Id.run, pure, List.getD] at hh\n"
    "  norm_num at hh\n"
)


def _dtor(n, pos):
    """Anonymous-constructor pattern of arity `n` binding slot `pos` as `hh`."""
    slots = ["_"] * n
    slots[pos] = "hh"
    return "⟨" + ", ".join(slots) + "⟩"


def _wit_none_oob(q, i, j):
    """Refutation at the QUANTIFIED out-of-range clause (the last conjunct).

    The other witnesses project a single equation; this one instantiates the
    `∀ i j, 3 ≤ i ∨ 3 ≤ j → get i j = 0` clause at one concrete out-of-range
    index pair and reduces THAT. The `3 ≤ i` side condition is discharged by
    `norm_num`, so the instantiation is honest rather than assumed.
    """
    return (
        f"example : ¬ problem_spec_toRotationMatrix\n"
        f"    {q} none\n"
        f"    (implementation_toRotationMatrix {q} none) := by\n"
        f"  intro h\n"
        f"  obtain {_dtor(12, 11)} := h\n"
        f"  have h2 := hh {i} {j} (Or.inl (by norm_num))\n"
        "  simp only [implementation_toRotationMatrix, scale, Id.run, pure, "
        "List.getD] at h2\n"
        "  norm_num at h2\n"
    )


def _wit_some_oob(q, pt, i, j):
    """Refutation at the AFFINE branch's QUANTIFIED out-of-range clause.

    The `some` branch carries its own `∀ i j, 4 ≤ i ∨ 4 ≤ j → get i j = 0`
    conjunct over a SEPARATE accessor list, so it is a distinct clause from the
    `none` branch's `3 ≤ i ∨ 3 ≤ j` one, not a restatement of it. This
    instantiates it at one concrete out-of-range pair and takes the COLUMN side
    of the disjunction (`4 ≤ j`), discharged by `norm_num` rather than assumed —
    the row side is what the 3×3 analogue uses, so the two do not overlap.
    """
    slots = ["_"] * 19
    slots[18] = "hh"
    return (
        f"example : ¬ problem_spec_toRotationMatrix\n"
        f"    {q} (some {pt})\n"
        f"    (implementation_toRotationMatrix {q} (some {pt})) := by\n"
        f"  intro h\n"
        f"  obtain ⟨{', '.join(slots)}⟩ := h\n"
        f"  have h2 := hh {i} {j} (Or.inr (by norm_num))\n"
        "  simp only [implementation_toRotationMatrix, scale, Id.run, pure, "
        "List.getD] at h2\n"
        "  norm_num at h2\n"
    )


# none-branch conjunct order (12): rows, cols, g00, g01, g02, g10, g11, g12,
#                                  g20, g21, g22, (out-of-range).
def _wit_none(q, pos):
    return (
        f"example : ¬ problem_spec_toRotationMatrix\n"
        f"    {q} none\n"
        f"    (implementation_toRotationMatrix {q} none) := by\n"
        f"  intro h\n"
        f"  obtain {_dtor(12, pos)} := h\n"
        + _WIT_TAC
    )


# some-branch conjunct order (19): rows, cols, g00, g01, g02, g10, g11, g12,
#     g20, g21, g22, g03, g13, g23, g30, g31, g32, g33, (out-of-range).
def _wit_some(q, pt, pos):
    return (
        f"example : ¬ problem_spec_toRotationMatrix\n"
        f"    {q} (some {pt})\n"
        f"    (implementation_toRotationMatrix {q} (some {pt})) := by\n"
        f"  intro h\n"
        f"  obtain {_dtor(19, pos)} := h\n"
        + _WIT_TAC
    )


# ---------------------------------------------------------------------------
# POSITIVE CONTROL impls / proofs.
# ---------------------------------------------------------------------------

# POS-1: entry bindings emitted in REVERSED declaration order (m22 … m00). The
# accessor lists reference them by name, so every value is identical; the frozen
# straight-line proof still closes (`rfl` per entry). Different construction
# order, same values.
_MBLOCK_REVERSED = (
    "  let m22 := 1 - 2 * s * (q.b ^ 2 + q.c ^ 2)\n"
    "  let m21 := 2 * s * (q.c * q.d + q.b * q.a)\n"
    "  let m20 := 2 * s * (q.b * q.d - q.c * q.a)\n"
    "  let m12 := 2 * s * (q.c * q.d - q.b * q.a)\n"
    "  let m11 := 1 - 2 * s * (q.b ^ 2 + q.d ^ 2)\n"
    "  let m10 := 2 * s * (q.b * q.c + q.d * q.a)\n"
    "  let m02 := 2 * s * (q.b * q.d + q.c * q.a)\n"
    "  let m01 := 2 * s * (q.b * q.c - q.d * q.a)\n"
    "  let m00 := 1 - 2 * s * (q.c ^ 2 + q.d ^ 2)"
)

# POS-2: the (1,2) entry written with its cross term COMMUTED (a·b for b·a),
# equal by commutativity of ℚ multiplication. `rfl` no longer closes the (1,2)
# entry (nor the inherited translation entry (1,3)), so the frozen proof is
# retuned at exactly those slots to reduce the accessor and close with `ring`;
# the theorem STATEMENT is byte-identical and no lemma/axiom is added.
_M12_COMMUTED = "  let m12 := 2 * s * (q.c * q.d - q.a * q.b)"
_RING = ("by simp only [implementation_toRotationMatrix, Id.run, pure, List.getD, "
         "List.getElem?_cons_succ, List.getElem?_cons_zero, Option.getD_some]; ring")
_NONE_REFINE_COMM = (
    "      refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, " + _RING
    + ", rfl, rfl, rfl, ?_⟩"
)
_SOME_ENTRIES = ["rfl"] * 18
_SOME_ENTRIES[7] = _RING    # g12
_SOME_ENTRIES[12] = _RING   # g13 (inherited from m12)
_SOME_REFINE_COMM = "      refine ⟨" + ", ".join(_SOME_ENTRIES) + ", ?_⟩"


def _pos_commuted():
    src = _swap(_BASE, _M12_GOLD, _M12_COMMUTED)
    src = _swap(src, _NONE_REFINE, _NONE_REFINE_COMM)
    src = _swap(src, _SOME_REFINE, _SOME_REFINE_COMM)
    return src


# POS-3: the scale factor spelled INLINE at its binding site rather than through
# the `scale` abbreviation. Delta-equal, so the frozen proof closes unchanged —
# but it removes the pure-region helper from the impl's vocabulary, which is the
# lean analogue of nagini's "build the entries WITHOUT the helper" positive
# (nagini's own POS-1 goes the other way, calling helpers where gold inlines).
_SCALE_USE_GOLD = (
    "  let s := scale q\n"
    "  let m00 := 1 - 2 * s * (q.c ^ 2 + q.d ^ 2)"
)
_SCALE_USE_INLINE = (
    "  let s := (q.a ^ 2 + q.b ^ 2 + q.c ^ 2 + q.d ^ 2)⁻¹\n"
    "  let m00 := 1 - 2 * s * (q.c ^ 2 + q.d ^ 2)"
)
assert _BASE.count(_SCALE_USE_GOLD) == 1


def _pos_inline_scale():
    return _swap(_BASE, _SCALE_USE_GOLD, _SCALE_USE_INLINE)


# POS-4: the 3×3 accessor as an explicit `match` on the index pair rather than a
# read into a row-major nested list, with the off-shape indices falling through
# to `0` via a catch-all arm. This is the CONTAINER-shape reshape the other three
# positives do not reach: they all keep the nested-list accessor and vary only
# the arithmetic, which the frozen straight-line `rfl`-per-entry proof closes
# unchanged (POS-1 / POS-3 are delta-equal, POS-2 needs `ring` at two slots). The
# match accessor is a different REDUCTION shape, so the frozen quantified-clause
# step (`getD_getD_eq_zero`, a lemma about nested lists) does not apply at all and
# the off-shape convention has to be reproven from the match's own arms —
# case-splitting the `3 ≤ i ∨ 3 ≤ j` disjunction and covering each index shape.
# That makes it the one positive whose proof is genuinely re-derived rather than
# retuned, so it tests that the postcondition pins the accessor's VALUES on its
# whole domain and not the particular data structure gold reads them out of.
_GET3_MATCH = (
    "          ((fun i j => match i, j with\n"
    "            | 0, 0 => m00 | 0, 1 => m01 | 0, 2 => m02\n"
    "            | 1, 0 => m10 | 1, 1 => m11 | 1, 2 => m12\n"
    "            | 2, 0 => m20 | 2, 1 => m21 | 2, 2 => m22\n"
    "            | _, _ => 0) i j) }"
)
# The frozen none-branch's quantified-clause step, replaced by a proof over the
# match's own arms. `omega` kills the in-range rows/columns (the disjunct is
# false there); every out-of-range arm reduces to the catch-all `0` by `rfl`.
_OOB3_GOLD_STEP = (
    "      exact getD_getD_eq_zero _ 3 (by simp)\n"
    "        (by intro r hr; fin_cases hr <;> simp) i j h\n"
)
_OOB3_MATCH_STEP = (
    "      rcases h with hi | hj\n"
    "      · match i, j with\n"
    "        | 0, _ => omega\n"
    "        | 1, _ => omega\n"
    "        | 2, _ => omega\n"
    "        | (n+3), 0 => rfl\n"
    "        | (n+3), 1 => rfl\n"
    "        | (n+3), 2 => rfl\n"
    "        | (n+3), (k+3) => rfl\n"
    "      · match i, j with\n"
    "        | 0, (k+3) => rfl\n"
    "        | 1, (k+3) => rfl\n"
    "        | 2, (k+3) => rfl\n"
    "        | (n+3), _ => rfl\n"
    "        | _, 0 => omega\n"
    "        | _, 1 => omega\n"
    "        | _, 2 => omega\n"
)
assert _BASE.count(_OOB3_GOLD_STEP) == 1


def _pos_match_accessor():
    src = _swap(_BASE, _GET3_GOLD, _GET3_MATCH)
    return _swap(src, _OOB3_GOLD_STEP, _OOB3_MATCH_STEP)


# ADMISSIBILITY: the frozen impl + proof, with a ground instance discharged at
# the F2P-shaped input (v = none, q = (1,1,0,0): the X-rotation-family witness
# the issue turns on) BEFORE the frozen obligation, proving the modeled behavior
# is satisfiable at the very input the F2P exercises. Statement byte-identical;
# the ground instance is a `have` inside the existing tactic body; no new
# declaration / axiom / sorry.
_ADMISS_GROUND = (
    "  have _ground : problem_spec_toRotationMatrix\n"
    "      { a := 1, b := 1, c := 0, d := 0 } none\n"
    "      (implementation_toRotationMatrix { a := 1, b := 1, c := 0, d := 0 } none) := by\n"
    "    refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩\n"
    "    case refine_10 =>\n"
    "      intro i j h\n"
    "      exact getD_getD_eq_zero _ 3 (by simp) (by intro r hr; fin_cases hr <;> simp) i j h\n"
    "    all_goals\n"
    "      simp only [problem_spec_toRotationMatrix, implementation_toRotationMatrix,\n"
    "        scale, Id.run, pure, List.getD]\n"
    "      norm_num\n"
    + _INTRO_QV
)


# ---------------------------------------------------------------------------
# REJECT rival impls.
# ---------------------------------------------------------------------------
_M12_PLUS = "  let m12 := 2 * s * (q.c * q.d + q.b * q.a)"
_M21_MINUS = "  let m21 := 2 * s * (q.c * q.d - q.b * q.a)"
_M12_PARTIAL = (
    "  let m12 := if q.a = 0 then 2 * s * (q.c * q.d - q.b * q.a) "
    "else 2 * s * (q.c * q.d + q.b * q.a)"
)
_M13_PLUS = (
    "      let m13 := y - x * m10 - y * m11 - z * (2 * s * (q.c * q.d + q.b * q.a))"
)
_GET3_TRANSPOSED = (
    "          (([[m00, m10, m20], [m01, m11, m21], [m02, m12, m22]].getD i []).getD j 0) }"
)
# The 4×4 accessor reading a wrongly-signed INLINE cross term at its own (1,2)
# slot: the 3×3 shape keeps the frozen minus form, so only the affine block is
# wrong. This is what makes the two shapes separately attackable here.
_GET4_BLOCK_PLUS = _GET4_GOLD.replace(
    "[m10, m11, m12, m13],", "[m10, m11, 2 * s * (q.c * q.d + q.b * q.a), m13],")
# The 4×4 accessor's pinned bottom row with a wrong (3,3) slot.
_GET4_BOTROW = _GET4_GOLD.replace("[0, 0, 0, 1]]", "[0, 0, 0, 2]]")
# The 3×3 accessor's out-of-range DEFAULT changed from 0 to 1.
_GET3_OOB_ONE = _GET3_GOLD.replace(".getD j 0) }", ".getD j 1) }")
# The AFFINE accessor's out-of-range default changed from 0 to 1. A separate
# anchor from _GET3_OOB_ONE: the two shapes have separate accessor lists, so the
# `none` branch's 3-bound convention and the `some` branch's 4-bound one are
# independently attackable (machine-checked: this rival's 4×4 witness holds of
# it while the 3×3 shape's accessor stays byte-for-byte gold).
_GET4_OOB_ONE = _GET4_GOLD.replace(".getD j 0) }", ".getD j 1) }")


def _rej_oob_default_4x4():
    return _swap(_BASE, _GET4_GOLD, _GET4_OOB_ONE)


def _rej_block4x4_sign():
    return _swap(_BASE, _GET4_GOLD, _GET4_BLOCK_PLUS)


def _rej_bottom_row():
    return _swap(_BASE, _GET4_GOLD, _GET4_BOTROW)


def _rej_oob_default():
    return _swap(_BASE, _GET3_GOLD, _GET3_OOB_ONE)


def _rej_wrong_dims_4x4():
    return _swap(_BASE, _DIM4_GOLD, "        rows := 3, cols := 3,")


def _rej_sign():
    return _swap(_BASE, _M12_GOLD, _M12_PLUS)


def _rej_swap():
    return _swap(_swap(_BASE, _M12_GOLD, _M12_PLUS), _M21_GOLD, _M21_MINUS)


def _rej_partial():
    return _swap(_BASE, _M12_GOLD, _M12_PARTIAL)


def _rej_translation():
    return _swap(_BASE, _M13_GOLD, _M13_PLUS)


def _rej_transpose():
    return _swap(_BASE, _GET3_GOLD, _GET3_TRANSPOSED)


def _rej_wrong_cols():
    return _swap(_BASE, _DIM3_GOLD, "        rows := 3, cols := 2,")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the postcondition is SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_toRotationMatrix` STATEMENT byte-identical; only the impl
    # region (and, where the reshape breaks `rfl`, the proof body) changes. No
    # helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-reversed-decl",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _MBLOCK_GOLD, _MBLOCK_REVERSED),
        "rationale": (
            "a correct reshape that emits the nine entry bindings in REVERSED "
            "declaration order (m22 … m00); the accessor lists reference them by "
            "name so every value — and thus every clause of "
            "problem_spec_toRotationMatrix in both shapes — is identical, and the "
            "frozen straight-line `rfl`-per-entry proof still closes. Must verify, "
            "else the spec rejects an obviously-correct construction "
            "(SPEC-TOO-STRONG). Pure reordering of straight-line `let`s, no lemma "
            "or assumption token."
        ),
    },
    {
        "id": "pos-commuted-cross-term",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_commuted(),
        "rationale": (
            "a correct reshape that writes the (1,2) entry's cross term as "
            "`c*d - a*b` instead of `c*d - b*a` (equal by commutativity of ℚ "
            "multiplication). `rfl` no longer closes the (1,2) entry nor the "
            "inherited translation entry (1,3), so the frozen proof is retuned at "
            "exactly those two slots — reduce the nested-list accessor with `simp "
            "only [... pure, List.getD]` then `ring`. Same value on every input; "
            "if it cannot satisfy the spec the postcondition is SPEC-TOO-STRONG. "
            "Statement byte-identical, no new declaration/axiom/sorry."
        ),
    },
    # =====================================================================
    # ADMISSIBILITY — confirms the obligation is SATISFIABLE (non-vacuous) at the
    # F2P-shaped input rather than only in the abstract. The frozen theorem's only
    # hypothesis is nonzero norm (satisfied here), so nagini's precondition-admission
    # probe has no over-strong precondition to attack; the honest analogue is to
    # discharge the spec predicate at the F2P ground quaternion inside the proof
    # region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "pos-inline-scale",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_inline_scale(),
        "rationale": (
            "a correct reshape that spells the scale factor INLINE at its "
            "binding site — (a²+b²+c²+d²)⁻¹ — instead of going through the "
            "pure-region `scale` abbreviation, so the impl no longer mentions "
            "that helper at all. Delta-equal, so the frozen straight-line proof "
            "closes unchanged. This is the lean analogue of nagini's "
            "helper-vocabulary positive (nagini's calls helpers where gold "
            "inlines; here gold names a helper and the reshape inlines it), and "
            "it confirms the postcondition pins VALUES rather than the impl's "
            "choice of abbreviation. Must verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-match-accessor",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_match_accessor(),
        "rationale": (
            "a correct reshape of the 3×3 CONTAINER rather than of its arithmetic: "
            "the accessor is an explicit `match` on the index pair, with the "
            "off-shape indices falling through to `0` on a catch-all arm, instead "
            "of a read into a row-major nested list. Same value at every index — "
            "the nine entries by their own arms, `0` everywhere else — so every "
            "clause of both branches still holds. This is the one positive whose "
            "proof is genuinely RE-DERIVED rather than retuned: the frozen "
            "quantified-clause step is a lemma about nested lists and does not "
            "apply to a match at all, so the out-of-range convention is reproven "
            "by splitting the `3 ≤ i ∨ 3 ≤ j` disjunction and covering each index "
            "shape (`omega` where the disjunct is false, `rfl` on the catch-all). "
            "Must verify, else the postcondition pins gold's DATA STRUCTURE rather "
            "than the accessor's values (SPEC-TOO-STRONG). Statement "
            "byte-identical; no new declaration/axiom/sorry — the added steps are "
            "tactics inside the existing body."
        ),
    },
    {
        "id": "admiss-f2p-shaped-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _INTRO_QV, _ADMISS_GROUND),
        "rationale": (
            "the obligation is discharged at the F2P ground input (v = none, "
            "q = (1,1,0,0), the X-rotation-family quaternion the issue turns on) "
            "by `norm_num` over the reduced accessor, then the frozen obligation "
            "is closed verbatim. Verifies (else the spec is unsatisfiable at the "
            "normal input, the analogue of PRECOND-TOO-STRONG). Nothing assumed: "
            "the theorem STATEMENT is byte-identical, the ground instance is a "
            "`have` inside the existing tactic body, no new declaration/axiom/"
            "sorry."
        ),
    },
    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, so a verifying rival is a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input, confirmed to
    # hold of the rival and FAIL on gold.
    # =====================================================================
    {
        "id": "weak-prepatch-sign",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_sign(),
        "refinement": (
            "the literal pre-patch: the (1,2) block entry reintroduces the + sign "
            "on its cross term (2·s·(c·d + b·a)). Since a single binding feeds "
            "both the 3×3 and 4×4 shapes and the inherited translation entry, a "
            "real patch keeping this line is the unpatched buggy method: on the "
            "issue witness Quaternion(cos(x/2), sin(x/2), 0, 0) the (1,2) entry "
            "gets +sin(x) where −sin(x) is required, failing "
            "test_quaternion_rotation_iss1593 and test_quaternion_conversions. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result.get 1 2 = 2·s·(c·d − b·a)`: at q = (2,1,1,1) the "
            "rival's + form differs from the spec's − form whenever b·a ≠ 0. "
            "Refuted on that entry. If it verifies the spec does not pin the sign "
            "of the load-bearing cross term (SPEC-TOO-WEAK — admits the unresolved "
            "buggy patch)."
        ),
        "witness": _wit_none("{ a := 2, b := 1, c := 1, d := 1 }", 7),
    },
    {
        "id": "weak-swap-cd-offdiagonals",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_swap(),
        "refinement": (
            "swaps which cd off-diagonal carries the minus: the (1,2) entry gets "
            "+b·a and the (2,1) entry gets −b·a (the two are interchanged). A real "
            "patch with this transcription puts the negative sign in the lower "
            "off-diagonal instead of the upper one, producing the transpose-like "
            "wrong matrix that fails the exact Matrix equality in "
            "test_quaternion_conversions. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result.get 2 1 = 2·s·(c·d + b·a)`: at q = (1,1,2,3) the "
            "rival's (2,1) entry is the − form, differing from the spec's + form "
            "whenever b·a ≠ 0. Refuted at the (2,1) entry — a DIFFERENT clause and "
            "a different quaternion than the sign rival, so the two do not share a "
            "point. If it verifies the spec failed to pin WHICH off-diagonal is "
            "negative (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_none("{ a := 1, b := 1, c := 2, d := 3 }", 9),
    },
    {
        "id": "weak-partial-domain-a0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_partial(),
        "refinement": (
            "correct sign only on the a = 0 sub-domain, else the buggy + cross "
            "term. The issue witness Quaternion(cos(x/2), sin(x/2), 0, 0) has "
            "a = cos(x/2) ≠ 0, so this rival is STILL the buggy matrix on the very "
            "input test_quaternion_rotation_iss1593 checks. Does NOT resolve — and "
            "even were it correct on every literal F2P input, the patch must be "
            "correct for all quaternions, so a verifying rival is a "
            "verify-without-resolve break."
        ),
        "rationale": (
            "REJECT from `result.get 1 2 = 2·s·(c·d − b·a)`, which the spec "
            "demands for ALL q: at q = (3,2,0,0) the a ≠ 0 branch yields the + "
            "form, differing whenever b·a ≠ 0. Demonstrates the postcondition "
            "pins the entire domain, not a sampled subset. If it verifies, "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit_none("{ a := 3, b := 2, c := 0, d := 0 }", 7),
    },
    {
        "id": "weak-translation-inheritance",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_translation(),
        "refinement": (
            "the 3×3 block is correct (the (1,2) entry keeps the − sign), but the "
            "affine translation entry (1,3) is built from a wrongly-signed inline "
            "copy of the cross term (+b·a). A real patch that fixed the block "
            "entry but reused a stale + expression when forming the translation "
            "column produces a wrong 4×4 matrix: q1.to_rotation_matrix((x,y,z)) in "
            "test_quaternion_conversions yields the wrong row-1 translation slot. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result.get 1 3 = y − x·e10 − y·e11 − z·e12` with "
            "e12 = 2·s·(c·d − b·a): the rival uses the + form there, so the "
            "translation entry differs whenever z·b·a ≠ 0. At q = (1,1,0,0), "
            "point (2,3,5) — the ONLY witness on the v = some (4×4) shape, "
            "exercising the x/y/z coordinates — it is refuted. Targets the SECOND "
            "load-bearing clause the block-only rivals never touch. If it "
            "verifies, SPEC-TOO-WEAK."
        ),
        "witness": _wit_some(
            "{ a := 1, b := 1, c := 0, d := 0 }", "(2, 3, 5)", 12),
    },
    {
        "id": "weak-transpose-block",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_transpose(),
        "refinement": (
            "returns the TRANSPOSE of the rotation block (the accessor reads the "
            "row-major list of Mᵀ). For a proper rotation Mᵀ = M⁻¹ (rotation by "
            "the negated angle), so a real patch returning the transposed Matrix "
            "gives the wrong rotation and fails the exact Matrix equality in "
            "test_quaternion_conversions on a quaternion with all components "
            "nonzero. Coincides with gold only on symmetric matrices. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from `result.get 0 1 = 2·s·(b·c − d·a)` (e01): the transposed "
            "accessor returns e10 = 2·s·(b·c + d·a) there, differing whenever "
            "d·a ≠ 0. At q = (1,1,1,1) it is refuted. A structural attack "
            "(off-diagonal permutation) invisible to any abstraction that only "
            "checks the diagonal or a value multiset. If it verifies, "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit_none("{ a := 1, b := 1, c := 1, d := 1 }", 3),
    },
    {
        "id": "weak-wrong-column-count",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_wrong_cols(),
        "refinement": (
            "reports the wrong column count for the 3×3 shape (cols = 2 instead "
            "of 3). A real patch that constructed a matrix of the wrong shape "
            "would fail the exact Matrix equality in test_quaternion_conversions "
            "(SymPy compares dimensions), regardless of the entry values. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the structural dimension clause `result.cols = 3` of the "
            "v = none branch: the returned Mat carries cols = 2 on the 3×3 shape, "
            "contradicting the pinned column count directly (independent of any "
            "entry value). At q = (1,1,1,1), v = none it is refuted. This rival "
            "edits ONLY the 3×3 branch's dimension record, so it attests to the "
            "none-shape clause alone; the v = some branch's `rows = 4 ∧ cols = 4` "
            "is attacked separately by weak-wrong-dims-4x4. Attacks a dimension "
            "clause the entry-value rivals leave untouched. If it verifies, the "
            "spec does not pin the result's shape (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_none("{ a := 1, b := 1, c := 1, d := 1 }", 1),
    },
    {
        "id": "weak-wrong-dims-4x4",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_wrong_dims_4x4(),
        "refinement": (
            "reports 3×3 dimensions on the AFFINE shape (rows = 3, cols = 3 where "
            "4 and 4 are required), while every entry stays correct. A real patch "
            "that built the affine result with the block's dimensions would return "
            "a matrix of the wrong shape from the point-supplied call, failing the "
            "exact Matrix equality in test_quaternion_conversions (SymPy compares "
            "dimensions before entries). Does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result.rows = 4 ∧ result.cols = 4` in the v = some "
            "branch — the affine shape's dimension clauses, which the 3×3 "
            "dimension rival cannot reach because it edits the other branch's "
            "record. At q = (3,1,4,2), point (1,2,3) the reported cols is 3, "
            "contradicting the pinned 4. Together with weak-wrong-column-count "
            "this pins the container shape in BOTH branches. If it verifies, "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit_some(
            "{ a := 3, b := 1, c := 4, d := 2 }", "(1, 2, 3)", 1),
    },
    {
        "id": "weak-block-sign-4x4-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_block4x4_sign(),
        "refinement": (
            "the 3×3 shape keeps the frozen minus form, but the AFFINE accessor "
            "reads a wrongly-signed inline copy (+b·a) at its own (1,2) block "
            "slot. A real patch of this shape returns the correct matrix from the "
            "no-point call and the buggy one from the point-supplied call, so "
            "test_quaternion_conversions still fails on its "
            "q.to_rotation_matrix((x,y,z)) assertion. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result.get 1 2 = 2·s·(c·d − b·a)` in the v = some "
            "branch. This is the shape-SEPARATED analogue of the merged sign "
            "rival: because the affine accessor is a distinct anchor from the "
            "shared `let m12`, the 4×4 block entry IS independently attackable "
            "here, so nagini's separate 3×3/4×4 sign rivals do not in fact "
            "collapse to one impl edit on this carrier. Refuted at q = (1,2,3,1), "
            "point (1,1,2), where the affine (1,2) slot reads 2/3 against the "
            "pinned 2/15 while the 3×3 shape's (1,2) slot stays gold. If it "
            "verifies, the spec pins the sign in only one of the two shapes "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _wit_some(
            "{ a := 1, b := 2, c := 3, d := 1 }", "(1, 1, 2)", 7),
    },
    {
        "id": "weak-affine-bottom-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_bottom_row(),
        "refinement": (
            "the affine bottom row is (0,0,0,2) instead of (0,0,0,1), so the "
            "returned 4×4 is not an affine transformation matrix at all (its "
            "homogeneous coordinate is scaled). A real patch emitting this row "
            "fails the exact Matrix equality in test_quaternion_conversions on "
            "the point-supplied call, and any downstream composition of the "
            "matrix would rescale. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result.get 3 3 = 1` in the v = some branch: the rival "
            "reads 2 there. At q = (2,3,1,4), point (1,2,3) it is refuted. "
            "Attacks the affine bottom-row clauses — the homogeneous-coordinate "
            "pins — that every entry-value and dimension rival leaves untouched. "
            "If it verifies, SPEC-TOO-WEAK."
        ),
        "witness": _wit_some(
            "{ a := 2, b := 3, c := 1, d := 4 }", "(1, 2, 3)", 17),
    },
    {
        "id": "weak-out-of-range-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_oob_default(),
        "refinement": (
            "reads out-of-range indices as 1 instead of 0, breaking the stated "
            "modeling convention that fixes the accessor outside the matrix's own "
            "dimensions. A real surface whose accessor returned a nonzero value "
            "off the declared shape is not the 3×3 matrix the F2P compares "
            "against — SymPy's Matrix equality is over a determined shape with "
            "determined entries, so an accessor that is wrong off-shape does not "
            "model it. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from the QUANTIFIED clause `∀ i j, 3 ≤ i ∨ 3 ≤ j → "
            "result.get i j = 0`: the rival's accessor defaults to 1, so the "
            "clause fails at every out-of-range pair. The witness instantiates it "
            "at (i,j) = (3,0) — discharging the `3 ≤ i` side condition by "
            "norm_num rather than assuming it — and reduces to 1 = 0 on the "
            "rival. This is the ONLY case that attacks the spec's one BINDER-"
            "carrying clause (the frozen proof's getD_getD_eq_zero helper serves "
            "exactly it); every other rival attacks a closed equation. If it "
            "verifies, the out-of-range convention is unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_none_oob("{ a := 1, b := 1, c := 1, d := 1 }", 3, 0),
    },
    {
        "id": "weak-out-of-range-default-4x4",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_oob_default_4x4(),
        "refinement": (
            "the AFFINE accessor reads out-of-range indices as 1 instead of 0, "
            "while the 3×3 shape's accessor keeps the convention. A real surface "
            "whose point-supplied call returned a nonzero value off its declared "
            "4×4 shape is not the affine matrix the F2P compares against — SymPy's "
            "Matrix equality is over a determined shape with determined entries, "
            "so an accessor wrong off-shape does not model it, and the no-point "
            "call being right does not repair the point-supplied one. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the v = some branch's QUANTIFIED clause `∀ i j, 4 ≤ i ∨ "
            "4 ≤ j → result.get i j = 0`. This is the shape-SEPARATED analogue of "
            "the 3×3 out-of-range rival, and it is a genuinely distinct clause "
            "rather than a restatement: the two shapes have separate accessor "
            "lists and separate bounds (3 versus 4), so the affine convention is "
            "independently attackable — the 3×3 rival's own accessor is untouched "
            "here. The witness instantiates the clause at (i,j) = (0,4) and takes "
            "the COLUMN side of the disjunction (`4 ≤ j`, discharged by norm_num "
            "rather than assumed), where the 3×3 analogue takes the row side, so "
            "the two witnesses probe different halves of the binder. Refuted at "
            "q = (1,3,2,1), point (3,1,4). If it verifies, the affine "
            "out-of-range convention is unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_some_oob(
            "{ a := 1, b := 3, c := 2, d := 1 }", "(3, 1, 4)", 0, 4),
    },
]


# No consumed axioms and no deep-model references: every matrix entry is modeled
# directly as exact ℚ arithmetic over the inputs, so there is no in-model axiom
# obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
