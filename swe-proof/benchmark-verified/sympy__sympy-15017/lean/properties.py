"""properties.py — G-PBT falsification battery for sympy__sympy-15017 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start``/``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start``/``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the single
``theorem correct_arraySize`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff the variant is in scope AND the file elaborates
with the obligation closed (no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff the variant is
in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the element count over a heap ``List[int]`` under fractional permission
and pins the result against a prefix-recursive pure fold; this Lean bundle
models the SAME single purely-functional core — the number of elements a dense
N-dimensional array holds, derived from its list of dimension sizes — over a
``List Nat`` carrier, and the SAME grounding: the result is pinned to the
product of the input dimensions, a fully-unfolded function of the input with no
opaque answer key. Every nagini case that attacks a VALUE property carries over
as an attack on that clause, or as a faithful correct positive. The nagini
frame/permission-mutation class is VACUOUS on this carrier; the nagini
termination class is NOT vacuous — the diverging rival is expressible and the
frozen spec rejects it, but no witness discriminates it, so it is recorded as a
NO-DISCRIMINATOR gap in the battery rather than as a closed class. See the
per-class read below and the accounting block at the bottom; no substitute probe
is fabricated for either.

DEFENDED SURFACE (one modeled behavior, one obligation, one clause).

  ``problem_spec_arraySize (shape : List Nat) (result : Nat) : Prop``
      pins ``result = shape.prod`` — exact equality to the product of the
      dimension sizes, with the empty product convention fixing the no-dimension
      case at one.

  ``theorem correct_arraySize : ∀ shape, problem_spec_arraySize shape
      (implementation_arraySize shape)``
      is the sole obligation. It carries NO precondition hypothesis: the
      dimension list is universally quantified, so every list of non-negative
      dimension sizes — including the empty one — is in-domain.

The clause is a single top-level equation, so "every independent top-level
clause is attacked" reduces to "the equation is attacked", and it is, at eight
distinct dimension lists. There is exactly ONE input binder, ``shape``, and it
is the load-bearing one; the reject witnesses vary it across the empty list, a
singleton zero dimension, a singleton non-unit dimension, a two-element list of
equal dimensions, a two-element list of distinct dimensions, a two-element list
containing a zero dimension, and two distinct four-element lists (see the
point-spread block at the bottom). No sub-domain the rivals could hide in is left
unprobed: a rival wrong only on the no-dimension case, only on a list containing
a zero dimension (whether the zero stands alone or beside a non-unit dimension),
only on the leading dimension, only on the combining operation, or only above a
rank threshold each has its own witness.

THE BEHAVIOURAL DISCRIMINATOR. The substance of the issue is that a rank-0
array — one with no dimensions at all — holds a single element, not none. On
this carrier that is exactly ``([] : List Nat).prod = 1``, the base case of the
pinned product. The headline rivals below are the two shapes of the pre-fix
behavior: fold the dimensions but special-case the no-dimension list to zero,
either by seeding the fold from the first dimension (so the empty list has no
seed and falls to a zero branch) or by guarding the loop outright. Both are
refuted at ``[]``.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and demonstrated so rather than
    asserted. The nagini sibling makes this class MANDATORY and ships two rivals
    for it (an indexed store and an append), because there the dimension list is
    a heap structure held at half permission and a write needs the full share.
    This carrier is referentially transparent: ``shape : List Nat`` is an
    immutable value, there is no ``mut`` input binder, no aliasing, and no
    read-only cell to overwrite.

    The demonstration is that the nearest expressible analogue — copy the
    dimension list into a local and write to the COPY, here appending a
    dimension — is not a rival at all but a CORRECT implementation. Built:
    exit 0, it VERIFIES against the frozen spec. That is the right outcome and
    it is the content of the vacuity claim: a write this carrier permits is
    unobservable in the pinned value, so it cannot be wrong, and there is no
    rejection to attribute. It is not shipped as a positive either, since it
    probes nothing the four soundness controls do not already cover. No
    substitute probe is fabricated.

  * DIVERGENCE / NON-TERMINATION — NO SHIPPABLE CASE, and the reason is about
    the WITNESS, not the carrier. The nagini sibling carries
    ``weak-nonterminating`` and records the termination lane as the attack class
    an earlier audit actually exploited: under partial-correctness semantics a
    spinning implementation satisfies every value clause vacuously.

    An earlier revision of this manifest recorded the class as VACUOUS because
    "a diverging implementation cannot be written at all — an unbounded
    recursion fails the termination checker at definition time". That reason is
    FALSE and was measured false: marking the definition ``partial`` sidesteps
    the termination checker, and

        partial def implementation_arraySize (shape : List Nat) : Nat :=
          implementation_arraySize shape

    elaborates on its own with exit 0. So the diverging rival IS expressible
    here; what cannot be built is a witness that DISCRIMINATES.

    A ``partial def`` is logically opaque — it gets no equation lemmas — so the
    pinned equation is neither provable nor refutable of it. The variant does
    fail to build (``Tactic `unfold` failed to unfold
    `implementation_arraySize```), but that is a tactic gap, exactly the
    non-attribution this battery's witnesses exist to close. Conditioning the
    refutation on a hypothesis, the technique that makes an opaque carrier
    attackable, does not rescue it: a witness of the shape

        example (h : implementation_arraySize [] ≠ 1) :
            ¬ problem_spec_arraySize [] (implementation_arraySize []) := ...

    was built against both sides and elaborates with exit 0 against the
    DIVERGING RIVAL *and* exit 0 against the FROZEN SOLUTION — on gold the
    hypothesis is simply false, so the conditional holds vacuously. It fails
    the "must FAIL on gold" half and is not a discriminator, so no reject case
    is landed rather than shipping one whose rejection attributes nothing.

    Note what this is NOT. It is not the ``partial``-semantics spec hole in
    ``the corpus-wide termination-semantics finding``: that finding is scoped to velvet bundles
    carrying ``loom.semantics.termination "partial"``, where the frozen spec
    ADMITS the diverging rival (it verifies). Here the frozen spec does not
    admit it — the variant is rejected, exit 1 — so there is no spec hole to
    report on lean and nothing to ship either way.

    Independently RE-MEASURED by the second audit, which did not take the above
    on trust: the bare ``partial def`` self-recursion elaborates alone (exit 0);
    the variant fails with ``Tactic `unfold` failed to unfold
    `implementation_arraySize``` (exit 1); the hypothesis-conditioned witness
    elaborates against the diverging rival (exit 0) AND against the frozen
    solution (exit 0), so it fails the must-FAIL-on-gold half; and the gate's own
    consistency probe over that hypothesis leaves ``False`` unproven on both
    sides (exit 1 each), confirming the hypothesis is satisfiable rather than
    contradictory. This bundle sets no ``loom.semantics.termination`` option at
    all, so the disposition is the WITNESS-side one recorded here, not the
    partial-semantics vacuous-verify hole. The class is therefore a KNOWN HOLE in
    the battery — a case that is shippable in principle and is not shipped — and
    deliberately not recorded as a vacuous class, which would falsely claim the
    battery is complete over it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The nagini sibling argues this at length
    and the argument ports unchanged: the result is pinned to the product of the
    input dimensions, a fully-unfolded function of the input, NOT an opaque
    answer key. There is nothing to echo — computing the product IS doing the
    work — so the cheapest honest implementation (return the product directly)
    is CORRECT and ships as a positive control instead of as a rival. If it
    failed to verify, the spec would be over-fit to the loop spelling.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the whole battery lives.
    Nine rivals, each correct on part of the domain and wrong where the fix
    bites.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script pins the loop's syntactic form
with a ``show`` and every reshape breaks it — so a rejection alone attributes
nothing to the spec. Every ``expect="reject"`` case therefore carries a Lean
snippet that states the spec predicate NEGATED at one concrete dimension list
and closes by ``decide`` after unfolding the predicate and the implementation.
Each witness binds NOTHING in its head (all inputs are ground list literals and
the carrier computes), so there is no hypothesis whose consistency could be in
question and the ``witness-inconsistent`` forgery shape does not arise. Each was
checked with two real ``lake env lean`` builds — HOLDS of its rival, FAILS on
the frozen solution (there ``decide`` reports it proved the proposition's
negation) — so every one is a seen discriminator, not a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
The modeled value is consumed verbatim as the array's reported length, so every
rival's ``refinement`` names the concrete length assertion its faithful real
counterpart would report wrongly: the no-dimension case that must read one, the
zero-dimension case that must read zero, or a multi-dimension case that must
read the full product. Each is asserted by the FAIL_TO_PASS test
(``test_ndim_array_initiation``) or by the PASS_TO_PASS suite, so each faithful
patch would NOT resolve.

AXIOM lane: EMPTY. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the combining operation is modeled deeply as a product), so the
nagini ``AXIOM_TESTS`` — also empty there — are dropped; the axiom lane is
G-AX's job and this gate ignores them.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15017"
BACKEND = "lean"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the frozen file (both asserted by `_swap` at import, so any drift in
# Solution.lean breaks this manifest loudly instead of silently mis-editing).
# ---------------------------------------------------------------------------

# The WHOLE gold implementation, strictly inside `-- impl-start`/`-- impl-end`.
# Every rival and every reshaped positive replaces exactly this block; the spec
# view elides the impl region, so same_spec is unaffected.
_I_GOLD = """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 1
  for d in shape do
    acc := acc * d
  return acc"""

# The WHOLE gold proof body, strictly inside `-- proof-start`/`-- proof-end`
# and strictly BELOW the `theorem correct_arraySize` statement, so a positive
# that re-proves leaves the obligation's statement byte-identical.
_P_BODY = """  intro shape
  unfold problem_spec_arraySize implementation_arraySize
  have h : ∀ (acc : Nat) (l : List Nat),
      Id.run (forIn l acc (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d))))
        = l.foldl (· * ·) acc := by
    intro acc l
    induction l generalizing acc with
    | nil => rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih, List.foldl_cons]
  show Id.run (forIn shape 1 (fun d r => do pure PUnit.unit; pure (ForInStep.yield (r * d)))) = shape.prod
  rw [h]
  rw [List.prod_eq_foldl]
"""

# The frozen proof's first tactic line — unique in the file (the inner helper
# uses `    intro acc l`) — so the admissibility positive can PREPEND ground
# `have`s without touching the obligation's statement or the spec view.
_P_INTRO = "  intro shape\n"


# ---------------------------------------------------------------------------
# Witness scaffold. State the spec predicate NEGATED at one concrete dimension
# list, unfold the predicate and the implementation, and let the carrier
# compute. `shape` is a `List Nat` and the combining operation is arithmetic on
# `Nat`, so every point is decidable and no conditioning on an opaque term is
# needed; the head binds nothing, so the hypotheses cannot be inconsistent.
# ---------------------------------------------------------------------------
def _w(dims):
    return (f"example : ¬ problem_spec_arraySize {dims}\n"
            f"    (implementation_arraySize {dims}) := by\n"
            f"  unfold problem_spec_arraySize implementation_arraySize\n"
            f"  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_arraySize` statement byte-identical and closes its
    # obligation honestly: no helper lemma, no new declaration, no assumption
    # token. All four were confirmed by a real `lake env lean` build.
    # =====================================================================
    {
        "id": "pos-local-rename-single-exit",
        "kind": "soundness",
        "expect": "verify",
        # Minimal structural reshape: the running accumulator is bound to a
        # differently-named local and returned once at the end. Definitionally
        # the frozen loop, so the frozen proof body still closes unchanged.
        "module": _swap(
            _BASE, _I_GOLD,
            """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut out := 1
  for d in shape do
    out := out * d
  return out"""),
        "rationale": "structurally different but CORRECT: the running accumulator "
                     "is a differently-named single-exit local, computed by the "
                     "SAME forward traversal in the SAME direction. It produces the "
                     "same value on every dimension list, so the pinned equation "
                     "still holds — if it failed, the postcondition would be "
                     "over-fit to the frozen spelling => SPEC-TOO-STRONG. "
                     "Definitionally the frozen loop, so the frozen proof body "
                     "closes it verbatim; statement byte-identical, no new "
                     "declaration. Ports nagini's pos-control-single-exit.",
    },
    {
        "id": "honest-grounded-product-return",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest HONEST implementation: return the product of the input
        # dimensions directly. Re-proved by `rfl` — the whole loop-vs-fold
        # bridge in the frozen body is no longer needed.
        "module": _swaps(
            _BASE,
            (_I_GOLD,
             "def implementation_arraySize (shape : List Nat) : Nat := shape.prod"),
            (_P_BODY,
             "  intro shape\n"
             "  unfold problem_spec_arraySize implementation_arraySize\n"
             "  rfl\n"),
        ),
        "rationale": "the result is pinned to the product of the input dimensions "
                     "— a fully-unfolded function of the input, NOT an opaque "
                     "answer key — so returning that product directly is the "
                     "cheapest HONEST implementation and is CORRECT. Must verify; "
                     "this is what makes UNGROUNDED-ORACLE-ECHO vacuous here (there "
                     "is no WRONG echo to ship as a rival: echoing a grounded "
                     "product IS computing it). Re-proved by `rfl`, dropping the "
                     "now-unneeded loop-to-fold bridge; statement byte-identical, "
                     "no new declaration. Ports nagini's "
                     "honest-grounded-oracle-return.",
    },
    {
        "id": "pos-reverse-traversal",
        "kind": "soundness",
        "expect": "verify",
        # Traverse the dimensions in the OPPOSITE order and multiply on the
        # other side of the accumulator. Same value (the combining operation is
        # commutative and associative), genuinely different control flow, and a
        # genuinely re-authored proof.
        "module": _swaps(
            _BASE,
            (_I_GOLD,
             """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 1
  for d in shape.reverse do
    acc := d * acc
  return acc"""),
            (_P_BODY,
             "  intro shape\n"
             "  unfold problem_spec_arraySize implementation_arraySize\n"
             "  have h : ∀ (acc : Nat) (l : List Nat),\n"
             "      Id.run (forIn l acc (fun d r => do pure PUnit.unit; "
             "pure (ForInStep.yield (d * r))))\n"
             "        = l.foldl (fun a b => b * a) acc := by\n"
             "    intro acc l\n"
             "    induction l generalizing acc with\n"
             "    | nil => rfl\n"
             "    | cons a as ih =>\n"
             "      rw [List.forIn_cons]\n"
             "      simp only [Id.run, bind] at ih ⊢\n"
             "      rw [ih, List.foldl_cons]\n"
             "  show Id.run (forIn shape.reverse 1 (fun d r => do pure PUnit.unit; "
             "pure (ForInStep.yield (d * r)))) = shape.prod\n"
             "  rw [h]\n"
             "  simp [List.prod_eq_foldr]\n"),
        ),
        "rationale": "traverses the dimension list in the OPPOSITE order, combining "
                     "on the other side of the accumulator. The combining operation "
                     "is commutative and associative, so the value is unchanged on "
                     "every input while the control flow genuinely differs — a "
                     "faithful reshape MUST verify, else SPEC-TOO-STRONG. Re-proved "
                     "honestly for the new shape (the loop-to-fold bridge is "
                     "restated for the flipped combining order and closed against "
                     "the right-fold characterisation of the product); statement "
                     "byte-identical, no new declaration, no assumption token. "
                     "Strengthens nagini's pos-control-single-exit, which "
                     "deliberately did NOT flip the traversal because that backend "
                     "would have needed a fold-commutativity lemma it could not "
                     "cheaply supply.",
    },
    {
        "id": "pos-recursive-shape",
        "kind": "soundness",
        "expect": "verify",
        # A purely functional recursive definition instead of an accumulator
        # loop — the largest structural distance from the frozen shape that
        # still verifies, and the one whose proof is a genuine induction.
        "module": _swaps(
            _BASE,
            (_I_GOLD,
             """def implementation_arraySize : List Nat → Nat
  | [] => 1
  | d :: ds => d * implementation_arraySize ds"""),
            (_P_BODY,
             "  intro shape\n"
             "  unfold problem_spec_arraySize\n"
             "  induction shape with\n"
             "  | nil => rfl\n"
             "  | cons a as ih =>\n"
             "    simp [implementation_arraySize, List.prod_cons, ih]\n"),
        ),
        "rationale": "a purely functional front-recursive definition replacing the "
                     "accumulator loop: the largest structural distance from the "
                     "frozen shape that is still CORRECT (its no-dimension base "
                     "case is one and each step multiplies in the leading "
                     "dimension). Must verify, else the spec is over-fit to the "
                     "imperative spelling => SPEC-TOO-STRONG. Re-proved by a real "
                     "induction on the dimension list; statement byte-identical, no "
                     "new declaration, no assumption token.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE (non-vacuous) at
    # normal, F2P-shaped inputs. The frozen theorem carries NO precondition
    # hypothesis, so nagini's "does the precondition admit a normal input"
    # probe re-expresses as: discharge the spec predicate by evaluation at the
    # two F2P-shaped extremes as ground `have`s, then close the frozen
    # obligation verbatim. Nothing is assumed: no new declaration, statement
    # byte-identical, the ground instances are `have`s prepended to the
    # existing tactic body. (Confirmed by a real build.)
    # =====================================================================
    {
        "id": "admiss-ground-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground0 : problem_spec_arraySize []\n"
            "      (implementation_arraySize []) := by\n"
            "    unfold problem_spec_arraySize implementation_arraySize\n"
            "    decide\n"
            "  have _ground1 : problem_spec_arraySize [3, 3, 3, 3]\n"
            "      (implementation_arraySize [3, 3, 3, 3]) := by\n"
            "    unfold problem_spec_arraySize implementation_arraySize\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged by evaluation at the two "
                     "F2P-shaped extremes — the no-dimension list (the "
                     "discriminating case, where the count must be one) and a "
                     "four-dimension list (where it must be the full product) — as "
                     "ground `have`s, then the frozen obligation is closed "
                     "verbatim. Verifies, so the modeled behavior is satisfiable at "
                     "exactly the normal inputs the tests exercise, and the "
                     "obligation is not vacuously true of nothing (the analogue of "
                     "PRECOND-TOO-STRONG on a spec whose only binder is "
                     "universally quantified with no hypothesis). Nothing is "
                     "assumed: no new declaration, statement byte-identical. Ports "
                     "nagini's admiss-reads, whose in-domain reads under half "
                     "permission have no counterpart on an immutable carrier.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real counterpart would NOT resolve, and (b) a
    # witness pinning the violation at one concrete dimension list, each seen
    # to hold of the rival and to FAIL on the frozen solution.
    # =====================================================================

    # ---- the issue itself, shape 1: no seed, fall through to zero ----
    {
        "id": "prepatch-firstseed-empty-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: seed the fold from the FIRST dimension and combine
        # the rest, which leaves the no-dimension list with no seed at all — it
        # falls to a branch returning zero.
        "module": _swap(
            _BASE, _I_GOLD,
            """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  match shape with
  | [] => return 0
  | d :: ds =>
    let mut acc := d
    for x in ds do
      acc := acc * x
    return acc"""),
        "refinement": "this IS the pre-fix behavior — the dimensions are combined "
                      "with no explicit identity to start from, so the "
                      "no-dimension case has nothing to fold and is answered with "
                      "zero. Its faithful real counterpart makes an array with no "
                      "dimensions report a length of zero, which is precisely the "
                      "reported defect and precisely what the FAIL_TO_PASS test now "
                      "forbids (that array must report a length of one; and the "
                      "downstream single-element access, which succeeds only when "
                      "the index is below the reported length, would keep raising). "
                      "Definitively non-resolving.",
        "rationale": "REJECT from the pinned equation `result = shape.prod` at the "
                     "no-dimension list: the product of no dimensions is one, the "
                     "rival answers zero, and 0 ≠ 1. Every non-empty dimension list "
                     "agrees with gold — this is a true single-point divergence, and "
                     "it is exactly the point the fix is about. Refuted at [].",
        "witness": _w("[]"),
    },

    # ---- the issue itself, shape 2: guard the loop instead ----
    {
        "id": "partial-domain-empty-guard-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Same divergence reached the other way: keep the identity-seeded
        # forward loop (so every non-empty list is right) but short-circuit the
        # no-dimension list to zero.
        "module": _swap(
            _BASE, _I_GOLD,
            """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  if shape.isEmpty then
    return 0
  let mut acc := 1
  for d in shape do
    acc := acc * d
  return acc"""),
        "refinement": "keeps the identity-seeded traversal — so a zero dimension "
                      "still gives zero and a four-dimension list still gives the "
                      "full product, both as the tests demand — but explicitly "
                      "answers zero when there are no dimensions at all. Its "
                      "faithful real counterpart retains the no-dimension guard, so "
                      "an array with no dimensions keeps reporting a length of zero "
                      "and the single-element access on it keeps raising — FAILS the "
                      "FAIL_TO_PASS test. Non-resolving.",
        "rationale": "REJECT from the pinned equation at the no-dimension list: 0 ≠ "
                     "1. Shares the witness point with "
                     "prepatch-firstseed-empty-zero, legitimately: the two rivals "
                     "are observationally IDENTICAL to gold on every non-empty "
                     "dimension list and diverge only at [], for the same reason "
                     "(no empty-product identity), so neither is a near-miss of the "
                     "other over any wider sub-domain. They are kept as separate "
                     "cases because they reach that divergence by different "
                     "control flow — an absent fold seed versus an explicit guard "
                     "— which is the distinction nagini's two headline rivals draw.",
        "witness": _w("[]"),
    },

    # ---- drop the leading dimension ----
    {
        "id": "partial-domain-drop-leading-dimension",
        "kind": "uniqueness",
        "expect": "reject",
        # Combines only the dimensions AFTER the first, omitting the leading
        # one from the product.
        "module": _swap(
            _BASE, _I_GOLD,
            """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 1
  for d in shape.tail do
    acc := acc * d
  return acc"""),
        "refinement": "omits the LEADING dimension from the product. Correct only "
                      "when that dimension is one (or when there are none), wrong "
                      "otherwise. Its faithful real counterpart combines the "
                      "dimensions from the second onward, so a multi-dimension "
                      "array reports a length short by its first dimension's factor "
                      "— the length assertions in the FAIL_TO_PASS test and the "
                      "PASS_TO_PASS suite pin the FULL product, so the faithful "
                      "patch would NOT resolve.",
        "rationale": "REJECT from the pinned equation: the returned value omits the "
                     "leading dimension, so it differs from the product whenever "
                     "that dimension is not one. Refuted at [2, 5] — a two-element "
                     "list of DISTINCT dimensions, so the point also separates this "
                     "rival from one that dropped the trailing dimension instead "
                     "(the rival answers 5, the product is 10).",
        "witness": _w("[2, 5]"),
    },

    # ---- ignore zero dimensions ----
    {
        "id": "partial-domain-ignore-zero-dimension",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the widest sub-domain of any rival here: identical to
        # gold on every dimension list with no zero in it, and wrong exactly
        # when some dimension is zero (an array that holds nothing).
        "module": _swap(
            _BASE, _I_GOLD,
            """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 1
  for d in shape do
    if d != 0 then
      acc := acc * d
  return acc"""),
        "refinement": "skips a zero dimension instead of combining it, so an array "
                      "with a zero-sized dimension — which holds no elements at all "
                      "— is reported as holding the product of its remaining "
                      "dimensions. Its faithful real counterpart makes such an "
                      "array report a nonzero length: the FAIL_TO_PASS test asserts "
                      "that a one-dimensional array with a zero-sized dimension has "
                      "length zero, and it would read one instead — FAILS. "
                      "Non-resolving. This rival is the reason the battery cannot "
                      "stop at the no-dimension case: it AGREES with gold there "
                      "(both answer one) and is wrong on a different sub-domain "
                      "entirely.",
        "rationale": "REJECT from the pinned equation at a list containing a zero "
                     "dimension: the product is zero, the rival answers the product "
                     "of the rest (one, for a lone zero dimension), and 1 ≠ 0. "
                     "Refuted at [0] — a distinct point from every other witness, "
                     "and the ONLY one exercising a zero-valued dimension, which "
                     "the empty-list rivals cannot reach.",
        "witness": _w("[0]"),
    },

    # ---- constant one ----
    {
        "id": "constant-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the dimensions entirely.
        "module": _swap(
            _BASE, _I_GOLD,
            "def implementation_arraySize (shape : List Nat) : Nat := 1"),
        "refinement": "answers one regardless of the dimensions. Its faithful real "
                      "counterpart makes EVERY array report a length of one: the "
                      "one-dimensional array with a zero-sized dimension would read "
                      "one where the FAIL_TO_PASS test asserts zero, and a "
                      "four-dimension array would read one where the length is "
                      "asserted to be the full product — FAILS. Non-resolving. It "
                      "is the rival that would survive a battery probing ONLY the "
                      "no-dimension case, since it happens to be right there.",
        "rationale": "REJECT from the pinned equation: the result does not depend on "
                     "the input binder `shape` at all, so it differs from the "
                     "product on every list whose product is not one. Refuted at "
                     "[4] — a singleton NON-UNIT dimension, a distinct point that "
                     "no other witness uses and the cheapest input separating a "
                     "constant answer from a dimension-dependent one.",
        "witness": _w("[4]"),
    },

    # ---- seed the accumulator at zero ----
    {
        "id": "acc-seed-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Starts the fold from the absorbing element instead of the identity,
        # collapsing every answer to zero.
        "module": _swap(
            _BASE, _I_GOLD,
            """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 0
  for d in shape do
    acc := acc * d
  return acc"""),
        "refinement": "starts the fold from the absorbing element rather than the "
                      "identity, so every answer collapses to zero. Its faithful "
                      "real counterpart makes EVERY array report a length of zero — "
                      "the no-dimension array reads zero where the FAIL_TO_PASS "
                      "test asserts one, and a four-dimension array reads zero "
                      "where the full product is asserted — FAILS both. "
                      "Non-resolving. It is the exact dual of constant-one, and the "
                      "reason a battery must probe both the no-dimension case and a "
                      "large product: each rival is right where the other is wrong.",
        "rationale": "REJECT from the pinned equation: the result is identically "
                     "zero, so it differs from the product on every list whose "
                     "product is nonzero. Refuted at [3, 3, 3, 3] — a "
                     "FOUR-dimension list, the only witness point with more than "
                     "two dimensions, chosen because it is the shape whose full "
                     "product the FAIL_TO_PASS test itself pins, in the same "
                     "function body that pins the no-dimension case (the rival "
                     "answers 0, the product is 81).",
        "witness": _w("[3, 3, 3, 3]"),
    },

    # ---- wrong combining operation ----
    {
        "id": "wrong-combining-operation",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps the identity seed, the traversal and the direction, and gets
        # the no-dimension case RIGHT — but combines the dimensions with the
        # wrong operation.
        "module": _swap(
            _BASE, _I_GOLD,
            """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 1
  for d in shape do
    acc := acc + d
  return acc"""),
        "refinement": "combines the dimensions with addition instead of "
                      "multiplication while keeping the identity seed, so the "
                      "no-dimension case is right (one) and the multi-dimension "
                      "cases are not. Its faithful real counterpart makes a "
                      "multi-dimension array report the sum of its dimensions plus "
                      "one rather than their product, so the asserted lengths of "
                      "every multi-dimension array in the FAIL_TO_PASS test and the "
                      "PASS_TO_PASS suite would read wrong — FAILS. Non-resolving.",
        "rationale": "REJECT from the pinned equation: the spec pins the PRODUCT of "
                     "the dimensions, the rival accumulates their sum offset by the "
                     "seed. This rival is why the battery cannot rest on the "
                     "no-dimension case alone — it satisfies the discriminating "
                     "sub-domain exactly and is wrong everywhere the dimensions "
                     "actually have to be combined. Refuted at [2, 2], a distinct "
                     "point chosen so the two dimensions are EQUAL (the rival "
                     "answers 5, the product is 4); a list of distinct dimensions "
                     "would work too, but [2, 2] keeps this point separate from the "
                     "leading-dimension rival's [2, 5].",
        "witness": _w("[2, 2]"),
    },

    # ---- wrong only above a rank threshold ----
    {
        "id": "high-rank-offbyone",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by the independent audit. Every other rival is wrong on a
        # sub-domain described by the dimension VALUES (a zero, a non-unit, the
        # leading one) or by the empty list. None is wrong as a function of the
        # NUMBER of dimensions, so a rival keyed on rank alone was unattacked: it
        # agrees with gold at five of the six points the battery already uses.
        "module": _swap(
            _BASE, _I_GOLD,
            """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 1
  for d in shape do
    acc := acc * d
  if shape.length > 3 then
    return acc + 1
  return acc"""),
        "refinement": "combines every dimension correctly and then adds one when "
                      "there are more than three dimensions. Its faithful real "
                      "counterpart is right on every low-rank array — so the "
                      "no-dimension case the FAIL_TO_PASS test turns on still reads "
                      "one — and overcounts by one on a four-dimension array, whose "
                      "length the FAIL_TO_PASS test pins to the full product a few "
                      "assertions above the no-dimension one: it would read one more "
                      "than that. FAILS. Non-resolving.",
        "rationale": "REJECT from the pinned equation `result = shape.prod`: the "
                     "result exceeds the product by one on every dimension list "
                     "longer than three. This rival is why the battery cannot rest "
                     "on the value-shaped sub-domains alone — it is correct at [], "
                     "[0], [4], [2, 2] and [2, 5], i.e. at five of the six points "
                     "every other witness uses, and diverges only where the RANK "
                     "crosses a threshold, a sub-domain no other rival varies. "
                     "Refuted at [2, 2, 2, 2] — a four-dimension list distinct from "
                     "acc-seed-zero's [3, 3, 3, 3] — where the rival answers 17 and "
                     "the product is 16.",
        "witness": _w("[2, 2, 2, 2]"),
    },

    # ---- clamp the count to a minimum of one ----
    {
        "id": "clamp-count-min-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Added by the independent audit. The existing zero-dimension rival
        # reaches its divergence by SKIPPING a zero dimension inside the loop;
        # this one combines every dimension faithfully and then clamps the
        # ANSWER upward, which is the shape a "an array always holds at least
        # one element" reading of the empty-product convention produces. It is
        # the only rival wrong at a MULTI-dimension list containing a zero, a
        # point no other witness reaches: [0] is a singleton, so a rival that
        # mishandles the zero only once the fold has already accumulated a
        # non-unit factor is unattacked without it.
        "module": _swap(
            _BASE, _I_GOLD,
            """def implementation_arraySize (shape : List Nat) : Nat := Id.run do
  let mut acc := 1
  for d in shape do
    acc := acc * d
  return max acc 1"""),
        "refinement": "combines every dimension correctly and then raises the answer "
                      "to one when the product came out zero — the mistake of reading "
                      "the empty-product convention as 'an array always holds at "
                      "least one element' rather than as a fold seed. Its faithful "
                      "real counterpart gets the no-dimension case right (it reads "
                      "one) and so passes the assertion the fix is about, but an "
                      "array with a zero-sized dimension then reports a length of one "
                      "where the FAIL_TO_PASS test asserts zero — and the "
                      "single-element access on it would stop raising where it must. "
                      "FAILS. Non-resolving, and non-resolving for a DIFFERENT "
                      "assertion than the no-dimension rivals: it is the rival that "
                      "would survive a battery probing only the discriminating case.",
        "rationale": "REJECT from the pinned equation `result = shape.prod`: the "
                     "clamp makes the result differ from the product on exactly the "
                     "lists whose product is zero. Refuted at [2, 0] — a "
                     "TWO-dimension list containing a zero, a point no other witness "
                     "uses and the only multi-dimension zero point in the battery "
                     "(the rival answers 1, the product is 0). It is a genuine "
                     "near-miss: it agrees with gold at [], [0]'s companion non-zero "
                     "points, [4], [2, 2], [2, 5], [3, 3, 3, 3] and [2, 2, 2, 2], "
                     "i.e. at every other point the battery uses. Distinct from "
                     "partial-domain-ignore-zero-dimension, which drops the zero "
                     "INSIDE the fold (and so is already wrong at the singleton [0]) "
                     "rather than repairing the fold's answer afterwards.",
        "witness": _w("[2, 0]"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. The sibling battery has 11 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 5 value rivals, 1
# non-termination rival) plus an EMPTY axiom lane. This bundle models the SAME
# single purely-functional core, so case-count parity is not the target; what is
# recorded below is the disposition of EVERY sibling case.
#
#   sibling case                      -> here
#   -----------------------------------------------------------------------
#   pos-control-single-exit           -> pos-local-rename-single-exit  PORTED
#   honest-grounded-oracle-return     -> honest-grounded-product-return PORTED
#   admiss-reads                      -> admiss-ground-points      RE-EXPRESSED
#   frame-mutation-index-write        -> (none)                    VACUOUS
#   frame-mutation-append             -> (none)                    VACUOUS
#   prepatch-empty-zero-firstseed     -> prepatch-firstseed-empty-zero PORTED
#   partial-domain-empty-zero         -> partial-domain-empty-guard-zero PORTED
#   partial-domain-skip-first-axis    -> partial-domain-drop-leading-dimension
#                                                                   PORTED
#   constant-one                      -> constant-one              PORTED
#   acc-seed-zero                     -> acc-seed-zero             PORTED
#   weak-nonterminating               -> (none)             NO-DISCRIMINATOR
#   (none)                            -> pos-reverse-traversal     ADDED
#   (none)                            -> pos-recursive-shape       ADDED
#   (none)                            -> partial-domain-ignore-zero-dimension
#                                                                   ADDED
#   (none)                            -> wrong-combining-operation  ADDED
#   (none)                            -> high-rank-offbyone         ADDED (audit)
#   (none)                            -> clamp-count-min-one        ADDED (audit)
#   AXIOM_TESTS (0)                   -> (none)                    DROPPED (G-AX)
#
# RE-EXPRESSED (admiss-ground-points): the sibling's admissibility control shows
#   the half-permission precondition admits the reads a normal input needs. This
#   obligation has NO precondition hypothesis at all — the dimension list is
#   universally quantified — so there is no precondition to admit anything. The
#   honest analogue is to show the obligation is non-vacuously satisfiable at
#   normal F2P-shaped inputs, discharged by evaluation at the two extremes as
#   ground `have`s before closing the frozen obligation verbatim.
# VACUOUS (both frame-mutation rivals): the sibling makes this class MANDATORY
#   because its dimension list is a heap structure held at half permission and a
#   write needs the full share. This carrier is referentially transparent — the
#   dimension list is an immutable value, there is no `mut` input binder, no
#   aliasing, no read-only cell to overwrite — so a rival that writes to its
#   input cannot be expressed. DEMONSTRATED, not just asserted: the nearest
#   expressible analogue (copy the list to a local, append a dimension to the
#   COPY, then fold) was built and VERIFIES, exit 0 — a write this carrier
#   permits is unobservable in the pinned value, so it cannot be wrong and there
#   is no rejection to attribute. No substitute probe is fabricated.
# NO-DISCRIMINATOR (weak-nonterminating): the diverging rival IS expressible
#   here — `partial def implementation_arraySize shape := implementation_arraySize
#   shape` elaborates on its own, exit 0, so the earlier claim that the
#   termination checker forecloses the class at DEFINITION time was wrong and is
#   corrected above. What blocks the case is the witness half: a `partial def`
#   gets no equation lemmas, so the pinned equation can be neither proven nor
#   refuted of it, and the hypothesis-conditioned witness that rescues an opaque
#   carrier elsewhere elaborates against BOTH the rival and the frozen solution
#   (exit 0 / exit 0 — on gold the hypothesis is false, so the conditional is
#   vacuous). It fails the must-FAIL-on-gold half, so no case is shipped rather
#   than one whose rejection attributes nothing. Distinct from the velvet
#   `partial`-semantics spec hole in the corpus-wide termination-semantics finding: there the
#   frozen spec ADMITS the diverging rival (it verifies); here the variant is
#   rejected, so there is no hole on lean.
# ADDED (pos-reverse-traversal, pos-recursive-shape): two further correct
#   positives at greater structural distance than the sibling was able to ship.
#   The sibling explicitly declined to flip the traversal direction because that
#   backend would have needed a fold-commutativity lemma; here the flipped
#   traversal and a fully recursive definition both re-prove honestly, so both
#   are cheap additional SPEC-TOO-STRONG probes on the SAME modeled behavior.
# ADDED (partial-domain-ignore-zero-dimension, wrong-combining-operation): the
#   sibling's five value rivals leave two sub-domains of the single pinned
#   equation unprobed. Four of them are refuted at the no-dimension list, and
#   `constant-one` is actually RIGHT there — so a battery built from the sibling
#   alone would probe the discriminating case heavily and the combining
#   behavior barely. The zero-dimension rival is a NEAR-MISS agreeing with gold
#   on every list without a zero (and agreeing at the no-dimension case too),
#   and the wrong-operation rival gets the discriminating case exactly right and
#   fails everywhere the dimensions must actually be combined. Neither is
#   fabricated for an unmodeled behavior: both attack the same single
#   load-bearing equation on sub-domains the tests assert.
# ADDED (high-rank-offbyone), by the independent audit: every rival above is
#   wrong on a sub-domain cut by the dimension VALUES or by emptiness, so a rival
#   keyed on the NUMBER of dimensions alone was unattacked. It agrees with gold at
#   five of the six points the rest of the battery uses and diverges only once the
#   rank crosses a threshold, which is the sub-domain the FAIL_TO_PASS test's
#   rank-4 length assertion covers and the battery previously reached only
#   incidentally.
# ADDED (clamp-count-min-one), by the second independent audit: the zero-dimension
#   sub-domain was probed only at the SINGLETON [0], and only by a rival that drops
#   the zero inside the fold. A rival that folds every dimension faithfully and
#   then clamps the ANSWER upward is wrong on exactly the same clause but is
#   already correct at [0]'s companion points and at every other point the battery
#   uses; it diverges at [2, 0], a multi-dimension list containing a zero, which no
#   previous witness reached. Its faithful counterpart is also the only rival here
#   that PASSES the no-dimension assertion the fix is about and still fails the
#   suite, so it is the closest near-miss in the battery.
#
# POINT SPREAD. Nine reject witnesses over EIGHT distinct dimension lists
# (pts=8); the sole shared point is justified in that case's `rationale`.
#   shape = []            prepatch-firstseed-empty-zero      (no dimensions)
#   shape = []            partial-domain-empty-guard-zero    (shared, same
#                                                             divergence point
#                                                             and same reason)
#   shape = [0]           partial-domain-ignore-zero-dimension (zero dimension)
#   shape = [4]           constant-one                       (singleton non-unit)
#   shape = [2, 2]        wrong-combining-operation          (two equal)
#   shape = [2, 5]        partial-domain-drop-leading-dimension (two distinct)
#   shape = [3, 3, 3, 3]  acc-seed-zero                      (four dimensions)
#   shape = [2, 2, 2, 2]  high-rank-offbyone                 (rank threshold)
#   shape = [2, 0]        clamp-count-min-one                (zero dimension in a
#                                                             MULTI-dimension list)
# The spec has exactly ONE input binder, `shape`, and it is varied across the
# empty list, a zero dimension alone and a zero dimension beside a non-unit one, a
# non-unit singleton, equal and distinct pairs, and two distinct four-element
# lists — so no binder is pinned at a single value and no length, position or
# dimension-value sub-domain is left unattacked.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no opaque callee (the combining operation is modeled deeply as a
# product), so there is nothing to probe and the gate ignores AXIOM_TESTS.
AXIOM_TESTS = []
