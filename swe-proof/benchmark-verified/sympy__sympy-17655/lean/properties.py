"""properties.py — G-PBT falsification battery for sympy__sympy-17655 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or discharges
a ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a two-input domain):

  scaleByFactor (factor : Rat) (coords : List Rat) : Option (List Rat)
      result = some (scaleSpec factor coords)
    where
      scaleSpec factor []        = []
      scaleSpec factor (x :: xs) = (x * factor) :: scaleSpec factor xs

  A point is modeled as its ordered coordinate list ``List Rat`` (mapping.md);
  the scalar is ``Rat`` (exact rational arithmetic, no float-order subtlety). The
  single top-level clause pins the result to ``some`` of the coordinate-wise
  scaled list, and that clause carries three inseparable sub-decisions:

    * The result is ``some _`` — a well-defined point, NEVER ``none`` / an
      undefined outcome. Pinned by the ``some`` head of the clause.
    * EVERY coordinate is scaled, position by position and IN ORDER — coordinate
      ``i`` of the result is ``coords[i] * factor``. Pinned by ``factor`` and by
      each element of ``coords``.
    * The result has the SAME length as the input coordinate list — no
      coordinate is dropped or added. Pinned by the structural recursion of
      ``scaleSpec`` over ``coords``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — the PERMISSION half is inexpressible; one
    rival's VALUE half is not, and is now carried. The nagini sibling makes an
    input-write attack MANDATORY: its modeled ``point`` input is held at
    fractional (read-only) permission, so a rival that overwrites it to build the
    answer in place is rejected for insufficient permission (nagini's
    ``frame-mut-right`` / ``frame-mut-left``). Lean is referentially transparent:
    the inputs are plain immutable values (``Rat`` / ``List Rat``), there is no
    half-permission to violate and no aliasing to exploit, so the PERMISSION
    ground of rejection has no instance here.

    But that is only a reason to drop the ground, not always the rival. Audit
    re-derivation, with builds: ``frame-mut-right`` writes every coordinate in
    place and returns the input, which on an immutable carrier IS the
    coordinate-wise scaled list — its residue is definitionally gold, VERIFIES
    (exit 0), and is genuinely vacuous. ``frame-mut-left`` however writes
    ``point[0] *= factor`` BEFORE delegating, so the first coordinate is scaled
    TWICE — a pure VALUE effect that survives the carrier translation intact.
    That residue is carried below as ``double-scaled-first-coord``, and it is
    rejected on its value, with a discriminating witness. Nothing is fabricated;
    the one class whose only content was permission is dropped, the one with
    value content is ported.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The bundle declares NO ``opaque`` / ``axiom``
    (meta.json axioms == [], deep_model_references validated by G-AX, not consumed
    as an oracle) and the scaled list is spelled out structurally by ``scaleSpec``
    over the inputs, so there is no answer key an implementation could echo without
    doing the per-coordinate multiply. The honest analogue is the cheapest-correct
    POSITIVE CONTROL below.

  * PRE-PATCH / UNDEFINED-RESULT (nagini has no direct analogue; carrier-native).
    At base_commit the modeled behavior produced no point at all (mapping.md: the
    left-multiply had no handler; ``none``). A rival returning ``none`` is the
    literal pre-patch and is refuted by the ``some`` head of the clause — a direct
    F2P attack (the F2P demands a well-defined scaled point, not an error).

  * PARTIAL-DOMAIN (one coordinate mishandled) — APPLIES, load-bearing. Three
    variants: (a) the FIRST coordinate is copied unscaled, (b) the LAST
    coordinate is scaled by ``factor + 1``, and (c) the FIRST coordinate is
    scaled TWICE. Each coincides with gold on every other coordinate and
    diverges on exactly one, attacking the per-coordinate clause at a distinct
    position, refuted with witnesses at distinct inputs. (a) and (b) port
    nagini's ``partial-first-coord-unscaled`` /
    ``partial-last-coord-offbyfactor``; (c) is the value residue of nagini's
    ``frame-mut-left`` and bounds the first coordinate from the OTHER side than
    (a) does (over-scaled rather than un-scaled).

  * DIMENSION-DROP (length class) — APPLIES. A rival that drops the first
    coordinate yields a result one shorter than the input, violating the
    length/order structure of the clause. Ports nagini's ``dimension-drop``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
concrete input; each was built (against the rival) and rebuilt (against the
frozen solution) to confirm it HOLDS of its rival and FAILS on gold (so it
discriminates rather than asserting a tautology). ``decide`` gets stuck on
concrete ``Rat`` normalization here, so each content witness unfolds the spec +
impl, reduces the ``forIn`` fold with the ``List.forIn_cons`` / ``bind`` / ``pure``
lemmas, and closes the concrete ``Rat`` (in)equality with ``norm_num``.

Every witness MUST put ``scaleSpec`` in its ``simp only`` set, and the ``none``
witness was repaired by the audit for omitting it. ``scaleSpec`` is a plain
non-``@[simp]`` recursive def, so without it the SPEC side never reduces and the
gold-side build fails with the goal still standing (``⊢ ¬[3 * 2, 4 * 2] =
scaleSpec 2 [3, 4]``) — an unfolding failure whose exit code is identical for a
true refutation, a false claim, and a real witness alike, i.e. no discrimination
at all. With ``scaleSpec`` unfolded, gold's spec and impl both reduce to the same
concrete list and the residual goal is ``⊢ False`` — a real semantic refutation.
The ``none`` witness then closes with ``simp`` (``none = some [_, _]`` is refuted
by constructor disagreement once both sides are reduced).

BINDER COVERAGE. Both input binders are varied across the reject witnesses:
  * ``coords`` — refuted at length-2 pairs (``[1,1]``, ``[3,4]``, ``[2,2]``,
    ``[2,5]``) AND a length-3 pair (``[4,4,4]``), and at DIFFERING element values
    (``[3,4]``, ``[2,5]``), so the per-coordinate reads are exercised at several
    shapes rather than one point and a rival that swapped two positions could not
    hide behind equal coordinates. The EMPTY list ``[]`` is refuted too
    (``empty-coords-undefined``), which is the only case reaching ``scaleSpec``'s
    ``[] => []`` base case — every other witness enters the ``x :: xs`` branch.
  * ``factor`` — refuted at ``5``, ``2``, ``3``, ``7`` and at the NEGATIVE ``-2``
    (``negative-factor-sign-collapsed``), so the scalar is varied across zero
    rather than only over positive integers, and a rival that mishandled the
    factor's SIGN cannot hide.
``pts`` = 7 distinct input points across the reject witnesses (one per rival).

OMITTED nagini cases (see assessment): ``frame-mut-right`` (its residue on this
carrier — write every coordinate in place, return the input — is definitionally
the scaled list, so it VERIFIES; genuinely vacuous, confirmed by build) and the
AXIOM_TESTS lane (this bundle declares no consumed axiom — the scaling is modeled
DEEPLY as ``scaleSpec`` and validated by G-AX; the axiom lane is not this gate's
job). ``frame-mut-left`` is NOT omitted: its permission ground is inexpressible
but its value effect is, and it is carried as ``double-scaled-first-coord``.
AXIOM_TESTS is empty.

SPEC-TOO-WEAK / SPEC-TOO-STRONG probes run beyond the shipped cases (each built;
none exposed a hole in the frozen spec). Rejected as they should be: result list
REVERSED; identity (nothing scaled); a MIDDLE coordinate off by ``+1``; a
trailing ``0`` coordinate APPENDED (length grown rather than dropped); and a
"teach-to-the-test" impl correct only when ``factor = 5`` and ``none`` elsewhere.
Verified as they should be: the scalar written on the LEFT
(``fun x => factor * x``, closed with ``mul_comm``) and a ``List.foldr``
formulation — so the clause is not accidentally pinned to one syntactic shape of
the per-coordinate product.

A second audit pass probed the sub-domains the above left alone, and two of its
rivals were REJECTED with discriminating witnesses and are now SHIPPED rather
than merely reported (``empty-coords-undefined``, at the empty coordinate list,
and ``negative-factor-sign-collapsed``, at a negative scalar — the base case of
the fold and the negative half of the scalar's domain, neither of which any
earlier case reached). Also rejected and not shipped, being redundant with cases
already present: ``|x| * factor`` (coordinate magnitudes, refuted at
``[-3,4]``), a swap of coordinates 1 and 2 at length 3 (refuted at ``[1,2,3]``),
and a rival substituting ``factor`` for any ZERO coordinate (refuted at
``[0,4]``). Additional correct reshapes VERIFIED: ``List.mapIdx``, a
``zipWith`` against a replicated factor list, and a ``foldl``-with-``reverse``
accumulator (whose bridge lemma has to be hoisted before the fold is touched).
Divergence lane: measured, not assumed. This carrier admits no diverging rival —
a self-recursive impl with no decreasing measure is refused by the elaborator
(``fail to show termination``) and a ``partial def`` one makes the constant
opaque so the frozen obligation cannot unfold; neither is a spec fact, so the
class is vacuous here rather than a hole.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-17655"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body, and the FULL frozen `correct_` tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_scaleByFactor\n"
    "    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do\n"
    "  let mut acc : List Rat := []\n"
    "  for x in coords do\n"
    "    acc := acc ++ [x * factor]\n"
    "  return some acc"
)

_PROOF_BODY = (
    "  intro factor coords\n"
    "  unfold problem_spec_scaleByFactor implementation_scaleByFactor\n"
    "  simp only [Id.run, bind]\n"
    "  rw [scale_forIn_eq factor coords []]\n"
    "  simp [pure]"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant produced by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# PRE-PATCH / UNDEFINED RESULT: the modeled behavior produces no point at all.
_NONE_IMPL = (
    "def implementation_scaleByFactor\n"
    "    (factor : Rat) (coords : List Rat) : Option (List Rat) := none"
)

# PARTIAL-DOMAIN (first coordinate unscaled): every coordinate scaled EXCEPT the
# first, which is copied through unchanged.
_FIRST_IMPL = (
    "def implementation_scaleByFactor\n"
    "    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do\n"
    "  let mut acc : List Rat := []\n"
    "  let mut i : Nat := 0\n"
    "  for x in coords do\n"
    "    if i = 0 then\n"
    "      acc := acc ++ [x]\n"
    "    else\n"
    "      acc := acc ++ [x * factor]\n"
    "    i := i + 1\n"
    "  return some acc"
)

# PARTIAL-DOMAIN (last coordinate off-by-factor): every coordinate scaled by
# `factor` EXCEPT the last, scaled by `factor + 1`.
_LAST_IMPL = (
    "def implementation_scaleByFactor\n"
    "    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do\n"
    "  let mut acc : List Rat := []\n"
    "  let mut i : Nat := 0\n"
    "  for x in coords do\n"
    "    if i + 1 = coords.length then\n"
    "      acc := acc ++ [x * (factor + 1)]\n"
    "    else\n"
    "      acc := acc ++ [x * factor]\n"
    "    i := i + 1\n"
    "  return some acc"
)

# DOUBLE-SCALED FIRST COORDINATE. AUDIT ADDITION — the observable residue of
# nagini's `frame-mut-left`, which the port dropped as wholly VACUOUS. The
# PERMISSION half of that case is indeed inexpressible here (no fractional
# permission on an immutable value), but the nagini rival did two things: it
# violated the permission AND it scaled the first coordinate before delegating
# to the coordinate-wise scale, so that coordinate came out scaled TWICE. The
# second half is a pure VALUE effect and is fully expressible on this carrier.
# Measured: this rival's module fails with a single `unsolved goals` at the
# `correct_` theorem (a proof failure, not a compile error), its witness holds
# of it (exit 0) and fails on the frozen solution with `⊢ False` (exit 1).
#
# It attacks the per-coordinate clause at the FIRST position with a
# DIRECTIONALLY DIFFERENT error from `partial-first-coord-unscaled` (over-scaled
# `x * factor * factor` rather than un-scaled `x`), so a spec that pinned only
# "coordinate 0 is not the identity" would still be caught here.
_DOUBLE_FIRST_IMPL = (
    "def implementation_scaleByFactor\n"
    "    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do\n"
    "  let mut pre : List Rat := coords\n"
    "  match coords with\n"
    "  | [] => pre := []\n"
    "  | x :: xs => pre := (x * factor) :: xs\n"
    "  let mut acc : List Rat := []\n"
    "  for x in pre do\n"
    "    acc := acc ++ [x * factor]\n"
    "  return some acc"
)

# EMPTY-CARRIER UNDEFINED. AUDIT ADDITION — correct on every NON-empty
# coordinate list, but reports an undefined result for the empty one. No other
# case in the battery evaluates the spec at `coords = []`, which is the BASE CASE
# of `scaleSpec`'s recursion: every other witness enters the `x :: xs` branch, so
# the `[] => []` branch was pinned by no case at all. This rival is the minimal
# probe of it — it satisfies the clause everywhere the rest of the battery looks
# and violates it only at the one shape none of them reach.
_EMPTY_NONE_IMPL = (
    "def implementation_scaleByFactor\n"
    "    (factor : Rat) (coords : List Rat) : Option (List Rat) :=\n"
    "  if coords.isEmpty then none else "
    "some (coords.map (fun x => x * factor))"
)

# SIGN-COLLAPSING FACTOR. AUDIT ADDITION — scales by `|factor|` instead of
# `factor`, so it agrees with the spec on every NON-NEGATIVE scalar and negates
# the whole result for a negative one. Every other witness in the battery uses a
# positive integer scalar (5, 2, 3, 7), so a rival that mishandled the SIGN of
# the factor was invisible to the entire reject lane; this pins `factor` over its
# negative half.
_NEG_FACTOR_IMPL = (
    "def implementation_scaleByFactor\n"
    "    (factor : Rat) (coords : List Rat) : Option (List Rat) :=\n"
    "  some (coords.map (fun x => "
    "if factor < 0 then x * (-factor) else x * factor))"
)

# DIMENSION-DROP: drop the first coordinate, so the result is one shorter.
_DIM_IMPL = (
    "def implementation_scaleByFactor\n"
    "    (factor : Rat) (coords : List Rat) : Option (List Rat) := Id.run do\n"
    "  let mut acc : List Rat := []\n"
    "  for x in coords.tail do\n"
    "    acc := acc ++ [x * factor]\n"
    "  return some acc"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — a
# functional `List.map` instead of the accumulator `for`-loop, same value on
# every input. The frozen `correct_` statement is byte-identical; the tactic body
# is retuned to the map shape (a `congr 1` + structural induction over `coords`).
# No new lemma/axiom/assumption token beyond the frozen set (`scale_forIn_eq`
# stays present, unused by this proof).
_POS_IMPL = (
    "def implementation_scaleByFactor\n"
    "    (factor : Rat) (coords : List Rat) : Option (List Rat) :=\n"
    "  some (coords.map (fun x => x * factor))"
)
_POS_PROOF = (
    "  intro factor coords\n"
    "  unfold problem_spec_scaleByFactor implementation_scaleByFactor\n"
    "  congr 1\n"
    "  induction coords with\n"
    "  | nil => simp [scaleSpec]\n"
    "  | cons a as ih => simp [scaleSpec, ih]"
)

# ADMISSIBILITY: the frozen impl+proof, with a ground instance discharged at an
# F2P-shaped input (a 3-coordinate point scaled by 5 — the `5 * Point(1,1,1) ==
# Point3D(5,5,5)` shape) BEFORE the frozen obligation, proving the modeled
# behavior is satisfiable at exactly the input the F2P exercises.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_scaleByFactor 5 [1,1,1]\n"
    "      (implementation_scaleByFactor 5 [1,1,1]) := by\n"
    "    unfold problem_spec_scaleByFactor implementation_scaleByFactor\n"
    "    simp only [scaleSpec, Id.run, List.forIn_cons, List.forIn_nil, bind, pure]\n"
    "    norm_num\n"
    + _PROOF_BODY
)


# ---- witnesses ------------------------------------------------------------
# Content witness: unfold spec + impl, reduce the `forIn` fold, close the
# concrete Rat (in)equality with norm_num (decide stalls on Rat normalization).
def _witness_content(factor, coords, extra_simp=""):
    return (
        f"example : ¬ problem_spec_scaleByFactor {factor} {coords}\n"
        f"    (implementation_scaleByFactor {factor} {coords}) := by\n"
        "  unfold problem_spec_scaleByFactor implementation_scaleByFactor\n"
        "  simp only [scaleSpec, Id.run, List.forIn_cons, List.forIn_nil, "
        f"bind, pure{extra_simp}]\n"
        "  norm_num"
    )


# `none` witness. AUDIT REPAIR (was: `unfold ...; simp`). The bare-`simp` form
# discriminated for the WRONG REASON and had to be replaced. Measured with real
# builds: `simp` cannot see through `scaleSpec` (it is a plain non-`@[simp]`
# front-recursive def), so on the frozen solution the goal was left standing as
#     ⊢ ¬[3 * 2, 4 * 2] = scaleSpec 2 [3, 4]
# — an UNFOLDING failure, not a semantic refutation. The control that proves it:
# the same `unfold ...; simp` script, pointed at a TRUE refutation of gold
# (`¬ problem_spec_scaleByFactor 2 [3,4] (some [6,999])`), ALSO fails (exit 1)
# with `⊢ ¬[6, 999] = scaleSpec 2 [3, 4]`, and so does the FALSE claim
# `(some [6,8])` — gold's actual value. A tactic that fails on the true
# refutation, the false claim, and the real witness alike carries no
# information in its gold-side exit code, which is precisely the
# `witness_scope_problems` / `_STUCK_REDUCTION` defect class arriving as an
# un-unfolded definition instead of a stuck kernel reduction.
#
# The repair puts `scaleSpec` (plus the fold lemmas) in the simp set so the
# spec side actually REDUCES to a concrete list, and then closes with `simp`,
# which refutes `none = some [_, _]` by constructor disagreement. Re-measured:
# rival exit 0; gold exit 1 with `⊢ False` — the residual goal after gold's
# spec and impl both reduce and agree, i.e. a genuine semantic refutation. The
# capability control for this script (a TRUE `none`-vs-`some` refutation stated
# on gold's own file, `¬ problem_spec_scaleByFactor 2 [3,4] none`) PROVES at
# exit 0, so the tactic is demonstrably able to decide this class of claim.
def _witness_none(factor, coords):
    return (
        f"example : ¬ problem_spec_scaleByFactor {factor} {coords}\n"
        f"    (implementation_scaleByFactor {factor} {coords}) := by\n"
        "  unfold problem_spec_scaleByFactor implementation_scaleByFactor\n"
        "  simp only [scaleSpec, Id.run, List.forIn_cons, List.forIn_nil, "
        "bind, pure]\n"
        "  simp"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_scaleByFactor`
    # STATEMENT is byte-identical; the tactic body is retuned to the map shape.
    # No helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that computes the result with a functional "
            "`coords.map (· * factor)` instead of the accumulator `for`-loop must "
            "satisfy `result = some (scaleSpec factor coords)`; if it cannot, the "
            "spec is SPEC-TOO-STRONG. Proof: after `unfold`, `congr 1` reduces to "
            "`coords.map _ = scaleSpec factor coords`, closed by structural "
            "induction on `coords` — no new declaration, axiom, or assumption "
            "token (the frozen `scale_forIn_eq` remains, unused here)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the F2P-shaped input rather than only in the abstract. The
    # frozen theorem carries NO precondition hypothesis (the behavior is total, so
    # `∀` is unguarded), so nagini's precondition-admission probe has no binder to
    # attack here; the honest analogue is to discharge the spec predicate at the
    # F2P ground input inside the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P ground input (a 3-coordinate "
            "point `[1,1,1]` scaled by `5`, the `5 * point == (5,5,5)` shape the "
            "F2P asserts) by reducing the fold and closing with `norm_num`; then "
            "the frozen obligation is closed verbatim. Verifies (else the spec is "
            "unsatisfiable at the normal input, the analogue of PRECOND-TOO-STRONG). "
            "Nothing is assumed: the theorem STATEMENT is byte-identical, the "
            "ground instance is a `have` inside the existing tactic body, and no "
            "new declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, so a verifying rival would be a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "prepatch-undefined-result",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NONE_IMPL),
        "refinement": (
            "this is the literal pre-fix behavior: the modeled left-scalar-times-"
            "point operation produced NO well-defined point at base_commit (the "
            "left-multiply had no handler, raising instead). Modeled as `none`, it "
            "reports an undefined result for every input, so `5 * point == "
            "(5,5,5)` cannot even be evaluated to a point => the F2P (which "
            "asserts equality with a concrete point) would NOT resolve. This is "
            "the pre-patch state itself."
        ),
        "rationale": (
            "REJECT from the `some` head of `result = some (scaleSpec factor "
            "coords)`: at `factor = 2`, `coords = [3,4]` the spec demands a "
            "`some _` result but the rival returns `none`, and `some _ = none` is "
            "false. If it verifies, the spec does not force a well-defined point "
            "(SPEC-TOO-WEAK on definedness)."
        ),
        "witness": _witness_none("2", "[3,4]"),
    },
    {
        "id": "partial-first-coord-unscaled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FIRST_IMPL),
        "refinement": (
            "leaves the FIRST coordinate UNSCALED (result[0] == coords[0], not "
            "coords[0] * factor); correct on every other coordinate. Scaling "
            "`[1,1]` by 5 would give `[1, 5]` not `[5, 5]`, so `5 * point == "
            "(5,5)` FAILS => the F2P would NOT resolve. A real patch that mapped "
            "every coordinate but the first would not resolve."
        ),
        "rationale": (
            "REJECT from the per-coordinate clause `result = some (scaleSpec "
            "factor coords)`: at `factor = 5`, `coords = [1,1]` the spec demands "
            "position 0 be `1*5 = 5`, but the rival copies it as `1`. Refuted at "
            "the first position, exercising `factor` and `coords` at a length-2 "
            "shape. If it verifies, the postcondition leaves the first coordinate "
            "unpinned (partial-domain SPEC-TOO-WEAK)."
        ),
        "witness": _witness_content("5", "[1,1]"),
    },
    {
        "id": "partial-last-coord-offbyfactor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_LAST_IMPL),
        "refinement": (
            "scales the LAST coordinate by `factor + 1` instead of `factor`; "
            "correct elsewhere. Scaling `[2,2]` by 3 would give `[6, 8]` not "
            "`[6, 6]` (last coord `2*4 = 8`), so the reported point is wrong on "
            "its final coordinate => the F2P would NOT resolve. A real patch with "
            "an off-by-one scalar on the last coordinate would not resolve."
        ),
        "rationale": (
            "REJECT from the per-coordinate clause `result = some (scaleSpec "
            "factor coords)`: at `factor = 3`, `coords = [2,2]` the spec demands "
            "the last position be `2*3 = 6`, but the rival gives `2*4 = 8`. "
            "Refuted at the last position with a distinct `(factor, coords)` pair "
            "from the other witnesses, exercising the boundary coordinate. If it "
            "verifies, the final coordinate is unpinned (partial-domain "
            "SPEC-TOO-WEAK)."
        ),
        "witness": _witness_content(
            "3", "[2,2]", ", List.length_cons, List.length_nil"
        ),
    },
    {
        "id": "double-scaled-first-coord",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DOUBLE_FIRST_IMPL),
        "refinement": (
            "scales the FIRST coordinate TWICE (result[0] == coords[0] * factor "
            "* factor) by pre-scaling it before performing the coordinate-wise "
            "scale; correct on every other coordinate. Scaling `[2,5]` by 3 "
            "would give `[18, 15]` not `[6, 15]`, so `5 * point == (5,5)`-style "
            "equality FAILS on the first coordinate => the F2P would NOT "
            "resolve. A real patch that applied the scale to one coordinate on "
            "the way in and then again to the whole point would not resolve."
        ),
        "rationale": (
            "REJECT from the per-coordinate clause `result = some (scaleSpec "
            "factor coords)`: at `factor = 3`, `coords = [2,5]` the spec demands "
            "position 0 be `2*3 = 6`, but the rival gives `2*3*3 = 18`. This "
            "attacks the first position with the OPPOSITE-DIRECTION error from "
            "`partial-first-coord-unscaled` (over-scaled, not un-scaled), and at "
            "a point with DISTINCT coordinate values (`[2,5]`, so a rival that "
            "confused the two positions could not hide). If it verifies, the "
            "clause bounds the first coordinate on only one side "
            "(partial-domain SPEC-TOO-WEAK)."
        ),
        "witness": _witness_content("3", "[2,5]"),
    },
    {
        "id": "empty-coords-undefined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTY_NONE_IMPL),
        "refinement": (
            "correct for every non-empty coordinate list, but reports an "
            "undefined result when the coordinate list is empty. A real patch "
            "that guarded its coordinate-wise scale on a non-empty coordinate "
            "tuple and produced no point otherwise would be wrong on the "
            "degenerate carrier value: the modeled operation is TOTAL and must "
            "yield a well-defined point for every coordinate list it is handed, "
            "so an impl that errors on one input shape does not implement the "
            "behavior the clause states."
        ),
        "rationale": (
            "REJECT from the `some` head of `result = some (scaleSpec factor "
            "coords)` read at the BASE CASE of the fold: at `factor = 2`, "
            "`coords = []` the spec demands `some (scaleSpec 2 []) = some []`, "
            "but the rival returns `none`. This is the only case in the battery "
            "that evaluates the spec at the EMPTY coordinate list — every other "
            "witness enters `scaleSpec`'s `x :: xs` branch, so the `[] => []` "
            "branch was otherwise pinned by no case. If it verifies, the spec "
            "leaves the empty-carrier value unconstrained (SPEC-TOO-WEAK on the "
            "recursion's base case)."
        ),
        "witness": _witness_none("2", "[]"),
    },
    {
        "id": "negative-factor-sign-collapsed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NEG_FACTOR_IMPL),
        "refinement": (
            "scales each coordinate by the ABSOLUTE VALUE of the scalar, so it "
            "agrees with the spec on every non-negative scalar and flips the "
            "sign of every coordinate for a negative one. Scaling `[3,4]` by "
            "`-2` would give `[6, 8]` instead of `[-6, -8]` — the reflected "
            "point rather than the scaled one => a `scalar * point` equality at "
            "a negative scalar FAILS and the F2P would NOT resolve."
        ),
        "rationale": (
            "REJECT from the per-coordinate clause `result = some (scaleSpec "
            "factor coords)` over the NEGATIVE half of the scalar's domain: at "
            "`factor = -2`, `coords = [3,4]` the spec demands `[-6, -8]` but the "
            "rival gives `[6, 8]`. Every other reject witness uses a POSITIVE "
            "integer scalar (5, 2, 3, 7), so a rival mishandling the factor's "
            "SIGN was invisible to the rest of the lane; this is the only case "
            "that varies `factor` across zero. If it verifies, the clause "
            "constrains the scalar only where it is non-negative "
            "(partial-domain SPEC-TOO-WEAK on the scalar's sign)."
        ),
        "witness": _witness_content("(-2)", "[3,4]"),
    },
    {
        "id": "dimension-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DIM_IMPL),
        "refinement": (
            "drops the first coordinate, so the result is one coordinate shorter "
            "than the input. Scaling `[4,4,4]` by 7 would give the length-2 "
            "`[28, 28]` instead of `[28, 28, 28]` — a point of a different "
            "dimension => `5 * point == (5,5,5)`-style equality FAILS and the F2P "
            "would NOT resolve (a real patch that lost a coordinate breaks the "
            "dimension the test asserts)."
        ),
        "rationale": (
            "REJECT from the length/order structure of `result = some (scaleSpec "
            "factor coords)`: at `factor = 7`, `coords = [4,4,4]` the spec demands "
            "a 3-element scaled list, but the rival returns a 2-element one. "
            "Refuted at a length-3 input (a shape none of the other witnesses "
            "use), so the length class is exercised distinctly. If it verifies, "
            "the spec does not force dimension preservation (partial-domain "
            "SPEC-TOO-WEAK on length)."
        ),
        "witness": _witness_content("7", "[4,4,4]", ", List.tail_cons"),
    },
]


# No consumed axioms and no deep-model references consumed as an oracle: the
# coordinate-wise scaling is modeled directly over the inputs (`scaleSpec`), so
# there is no in-model axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
