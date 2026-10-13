"""properties.py — G-PBT falsification battery for sympy__sympy-24066 (lean).

NOT a Lean file: a manifest the G-PBT gate executes. Each SPEC_TESTS entry is a
full ``Solution.lean`` variant sharing the FROZEN spec byte-for-byte — region
surgery touches only the text inside ``-- impl-start`` / ``-- impl-end`` and,
for a case that legitimately re-proves, inside ``-- proof-start`` /
``-- proof-end``. So ``markers.same_spec`` holds by construction and the
``theorem correct_collectFunction`` STATEMENT stays byte-identical. An
``expect="verify"`` case passes iff (in scope AND the file elaborates with the
obligation closed); an ``expect="reject"`` case passes iff (in scope AND it does
NOT verify AND its refutation ``witness`` holds of the rival while FAILING on the
frozen solution).

===========================================================================
DEFENDED SURFACE (one total function; the Lean-family bundle models only the
purely functional core of the touched decision):

  implementation_collectFunction
      (func : Func) (fds : List (Factor × Dim)) : FunctionResult

  problem_spec_collectFunction func fds result :=
    (C1) result.factor = applyFunc func (fds.map Prod.fst)
    (C2) result.dims   = fds.map (fun fd => canonDim fd.2)
  where canonDim d = if isDimensionless d then dimOne else d.

  Two INDEPENDENT top-level clauses, each separately attackable:

    * (C1) the reconstruction clause — the rebuilt scale factor is the function
      head applied to the arguments' scale-factor components, in order. Pinned by
      BOTH input binders (``func`` and the ``fst`` projection of ``fds``). This is
      the frame half: the modeled behavior does not touch the scale factor, so
      the spec must pin it to its inputs or a rival could put anything there.
    * (C2) the canonicalisation clause — the reported dimension list is the
      element-wise, order-preserving, length-preserving canonicalisation of the
      arguments' dimension components: a dimension the dimension system regards
      as reducing to no net dimension is reported as the single unit dimension,
      every other dimension is reported unchanged. This is the LOAD-BEARING
      clause: the desired behavior differs from the undesired one only on the
      sub-domain ``isDimensionless d = true ∧ d ≠ dimOne`` — a dimension that
      reduces to no net dimension yet is not literally written as the unit
      dimension. That is exactly the F2P scenario.

  Input binders of the spec predicate: ``func``, ``fds`` (per element: the
  ``Factor`` component read by C1 and the ``Dim`` component read by C2), and the
  list's LENGTH and ORDER, which both clauses depend on structurally.

===========================================================================
THE OPAQUE CARRIER, AND WHY THE REJECT LANE IS STILL EXPRESSIBLE

``dimOne``, ``isDimensionless`` and ``applyFunc`` are all ``opaque`` (the two
UNCHANGED outside operations plus the unit-dimension constant; the bundle
consumes no property of any of them — meta.json ``axioms == []`` and
``deep_model_references == []``). So ``decide`` cannot evaluate ``canonDim d``
for any literal ``d``: the ``Decidable`` instance gets stuck on the opaque
application, and no rival's violation is a closed ground disequality.

That does NOT make the lane inexpressible. Every witness below CONDITIONS on the
carrier rather than computing it: it states the refutation at a concrete input
under the WEAKEST hypothesis that separates the rival from the specification —
one hypothesis fixing the dimensionless verdict at the probed dimension
(``isDimensionless 7 = true``), plus one disequality saying the probed dimension
is not already the unit dimension (``dimOne ≠ 7``), which is precisely the
sub-domain the modeled canonicalisation exists for. Read the claim each makes:
*whenever the dimension system reports this argument dimensionless and its
dimension is not already the unit dimension, the rival's reported list differs
from the one the spec demands* — a stronger statement than any single fully
literal input could make on this carrier, and one the frozen solution does not
satisfy.

The hypotheses are JOINTLY SATISFIABLE by construction: they constrain two
DISTINCT opaque terms (the ``Bool`` value ``isDimensionless 7`` and the ``Nat``
value ``dimOne``), never the same term twice, so no ``False`` is derivable from
the binders alone. The two clause-C1 witnesses assume a single disequality
between two distinct opaque applications of ``applyFunc``, likewise satisfiable.

One rival (``weak-drop-dims-entirely``) needs no HYPOTHESIS at all: it is refuted
by a pure length mismatch, transparent regardless of what the opaque callee
returns. It still has to REDUCE the frozen loop term, which is a separate thing,
and an audit found the shipped witness had conflated the two — it omitted the
dimensionless rewrite altogether, leaving an unreduced
``match if isDimensionless 2 = true then …`` on both sides, so gold's build
failed without evaluating the claim (a forgery asserting the OPPOSITE failed with
the same goal). Its witness now case-SPLITS the opaque query rather than assuming
it: still no hypothesis, and the loop reduces in both branches.

===========================================================================
PORTING THE NAGINI BATTERY (nagini/properties.py is the design document)

Carried over — the ARGUMENT, re-expressed on this carrier:

  * ``uniq-prepatch-no-canonicalise`` (nagini's PARTIAL-DOMAIN 3a, the central
    rival) -> ``weak-no-canonicalisation``. The undesired behavior: report every
    argument dimension verbatim. Correct on genuinely-dimensioned arguments and
    on already-unit ones; wrong exactly on the F2P sub-domain.
  * ``uniq-inverted-canonicalise`` (3b) -> ``weak-inverted-canonicalisation``.
    The opposite rule: canonicalise the dimensioned arguments, leave the
    dimensionless ones verbatim.
  * ``uniq-first-element-verbatim`` (3c) -> ``weak-head-verbatim``.
  * ``uniq-last-element-verbatim`` (3d) -> ``weak-tail-verbatim``.
  * ``pos-control-inverted-branch-local`` (soundness 5) ->
    ``pos-inverted-branch-local``, same reshape (invert the per-element test,
    bind the chosen dimension to a local before the single append), keeping the
    imperative accumulator loop so the proof stays close to the frozen one.
  * ``pos-control-grounded-oracle`` (soundness 5b) -> ``pos-elementwise-map``.
    nagini's point stands verbatim here: the postcondition oracle is GROUNDED (a
    pure function of the input ``fds``, fully unfolded, bottoming out in the
    opaque-but-pure dimensionless query), so materialising it is the CORRECT
    answer and not an echo cheat. This case is the honest positive control that
    stands in for the ungrounded-oracle slot; if it did not verify the spec would
    reject its own grounded model => SPEC-TOO-STRONG.

Added here, because this carrier exposes a clause nagini's does not:

  * ``weak-factor-from-dimensions`` and ``weak-factor-drops-head`` attack (C1),
    which has no nagini counterpart — nagini's modeled function returns only the
    dimension list, so the reconstruction clause is invisible there. Without
    these, (C1) would be defended but never attacked and its two binders
    (``func``, the ``Factor`` projection) would be untested.
  * ``weak-drop-dims-entirely`` attacks the structural length half of (C2), which
    is the ONE rival needing no carrier hypothesis at all.

Omitted, with reasons (see also `assessment`):

  * ``frame-mutation-write-inplace`` and ``frame-mutation-noop-write``
    (nagini's #1 class, MANDATORY there) — VACUOUS as a permission attack on this
    backend. Lean is referentially transparent: ``fds`` is an immutable value,
    there is no fractional permission to under-hold and no aliasing to overwrite,
    so an in-place store cannot even be written. No substitute is fabricated. The
    SEMANTIC content of nagini's read-only obligation — "the unchanged input
    components are not silently rewritten into the answer" — does survive, as
    clause (C1) pinning the scale-factor component to its inputs, and (C1) IS
    attacked (``weak-factor-from-dimensions``, ``weak-factor-drops-head``).
  * ``admiss-f2p-singleton`` (admissibility) — CARRIED OVER, not omitted. An
    earlier revision of this manifest recorded it as VACUOUS on the grounds that
    the frozen obligation has no precondition hypothesis, so there is nothing for
    a probe to discharge. That reason was wrong, and an audit landed the case:
    "no precondition" removes the PRECOND-TOO-STRONG reading but not the lane's
    content, which on a total carrier is the obligation being UNSATISFIABLE at an
    F2P-shaped input. The universally quantified obligation the soundness
    positives close does not distinguish that — a contradictory spec is provable
    at every input and satisfied at none — so the ground instance is discharged
    by evaluation at the concrete single-argument shape instead. See
    ``admiss-f2p-singleton`` in SPEC_TESTS.
  * ``AXIOM_TESTS`` — dropped, per the porting map: the axiom lane is G-AX's job
    and this gate ignores it. (For the record it is empty here anyway: the bundle
    declares opaque SIGNATURES with no ``_prop``, so G-AX skips.)
  * DIVERGENCE / non-termination — GENUINELY VACUOUS on this carrier, and the
    nagini sibling carries no such case either. This bundle sets no
    ``loom.semantics.termination`` option at all (it is a plain Lean file, not a
    velvet one), so the disposition is the ``"total"`` reading: a rival with no
    decreasing measure would be genuinely rejected and WOULD be shippable if one
    could be written. It cannot be, and the reason is the carrier rather than the
    tactic: ``FunctionResult`` is a bare structure with no ``Inhabited``
    instance, so Lean refuses the only shape a diverging rival has. Measured — a
    ``partial def implementation_collectFunction … := implementation_collectFunction
    func fds`` variant clears variant scope (``variant_problems == []``) and then
    fails to ELABORATE, on both the module and the witness build:
    ``failed to compile 'partial' definition … could not prove that the type
    Func → List (Factor × Dim) → FunctionResult is nonempty``. That is a
    compile-time refusal of the rival, not a rejection by the spec, so the case
    would attribute nothing; a rival the file cannot even contain is not a rival.
    (The frozen structure is not editable from this lane, and deriving
    ``Inhabited`` for it would change the frozen artifact.)

===========================================================================
BINDER + CLAUSE COVERAGE (what replaces case-count parity with nagini)

  * clause (C2), per-element canonicalisation: attacked by
    ``weak-no-canonicalisation`` (verbatim everywhere),
    ``weak-inverted-canonicalisation`` (the opposite rule),
    ``weak-head-verbatim`` and ``weak-tail-verbatim`` (position-restricted).
  * clause (C2), structural LENGTH: attacked by ``weak-drop-dims-entirely``
    (length 0 vs 1).
  * clause (C2), structural ORDER: attacked by ``weak-reversed-order``. Added by
    audit. The head and tail rivals were previously credited with the order
    dependence, and they do not carry it: both hold every element of their probe
    list at the SAME dimension value, so a permutation of the reported list is
    invisible to their witnesses and both would still be refuted under a spec
    that pinned only the MULTISET of reported dimensions. The reversal rival is a
    permutation and nothing else — correct per element, correct length, correct
    factor — and is refuted on a list whose two elements sit in OPPOSITE regimes,
    the only shape on which a reversal is observable.
  * clause (C1), reconstruction: attacked by ``weak-factor-from-dimensions``
    (wrong projection of ``fds``) and ``weak-factor-drops-head`` (ignores the
    ``func`` binder).
  * binder ``func``: varied — held at ``0`` for the C2 rivals and at ``4`` for
    ``weak-factor-drops-head``, whose whole point is that the rival ignores it.
    Held off the value at which a head-ignoring rival would coincide with the
    specification.
  * binder ``fds`` — the ``Dim`` component: varied across ``7`` (dimensionless,
    C2 rivals), ``3`` (dimensioned, the inverted rival), ``9`` (the tail rival)
    and ``2``/``5`` (the length and C1 rivals), so no single dimension value
    carries the battery.
  * binder ``fds`` — the ``Factor`` component: varied (``0``, ``1``, ``2``,
    ``4``, ``5``); it is read only by (C1), and ``weak-factor-from-dimensions``
    is refuted precisely by probing an element whose ``Factor`` and ``Dim``
    components DIFFER (``(1, 5)``), which is the only way a rival that reads the
    wrong projection is separable.
  * binder ``fds`` — length and position: probed at length 0 (via the empty
    reported list), length 1 (five rivals) and length 2 (the head, tail and
    reversal rivals, at DISTINCT positions), so the per-position dependence is
    exercised on both ends of a multi-element list, and the ORDER dependence on a
    length-2 list whose elements are in DIFFERENT regimes.
  * the dimensionless verdict itself: probed at ``true``
    (``weak-no-canonicalisation``, head, tail) AND at ``false``
    (``weak-inverted-canonicalisation``), so both sides of the branch the modeled
    behavior turns on are exercised.

The head and tail rivals are NEAR-MISSES of each other (each agrees with the
desired behavior on the sub-domain the other gets wrong), so they are refuted at
DIFFERENT positions of a two-element list rather than sharing one witness. No two
witnesses share an input point.

===========================================================================
AXIOM lane: EMPTY. meta.json ``axioms == []`` and
``deep_model_references == []`` — the canonicalisation decision is modeled
deeply and structurally over the observable argument pairs, so there is no
in-model axiom obligation for this lane to re-discharge (and it would belong to
G-AX regardless).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-24066"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. Each lies ENTIRELY inside the region it means to edit and is
# unique in the file (asserted at load, so the manifest breaks loudly on drift).
# ---------------------------------------------------------------------------

# The full impl-region body.
_IMPL_GOLD = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do\n"
    "  let mut dims : List Dim := []\n"
    "  for fd in fds do\n"
    "    if isDimensionless fd.2 then\n"
    "      dims := dims ++ [dimOne]\n"
    "    else\n"
    "      dims := dims ++ [fd.2]\n"
    "  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }\n"
)

# The full frozen TACTIC BODY (everything after the theorem statement's `:= by`,
# strictly inside the proof region). Only a case that legitimately re-proves for
# a new impl shape swaps this; the STATEMENT above it is never touched.
_PROOF_GOLD = (
    "  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),\n"
    "      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>\n"
    "        (if isDimensionless fd.2 = true then do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield (r ++ [dimOne]))\n"
    "          else do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))\n"
    "        = init ++ fds.map (fun fd => canonDim fd.2) := by\n"
    "    intro fds\n"
    "    induction fds with\n"
    "    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, "
    "List.map_nil, List.append_nil]\n"
    "    | cons a as ih =>\n"
    "      intro init\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind, canonDim] at ih ⊢\n"
    "      by_cases h : isDimensionless a.2 = true <;>\n"
    "        simp [h, ih, List.append_assoc]\n"
    "  intro func fds\n"
    "  unfold problem_spec_collectFunction implementation_collectFunction\n"
    "  refine ⟨rfl, ?_⟩\n"
    "  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>\n"
    "        (if isDimensionless fd.2 = true then do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield (r ++ [dimOne]))\n"
    "          else do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))) = _\n"
    "  rw [helper]\n"
    "  simp\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"


def _impl(body):
    """Full Solution.lean with the impl-region body replaced (proof untouched)."""
    return _swap(_BASE, _IMPL_GOLD, body)


def _impl_proof(body, proof):
    """Full Solution.lean with BOTH the impl body and the tactic body replaced.

    Used only by the soundness positives, which legitimately re-prove the SAME
    obligation for a new impl shape. The theorem STATEMENT is not in either
    anchor, so it stays byte-identical.
    """
    return _swap(_impl(body), _PROOF_GOLD, proof)


# ---------------------------------------------------------------------------
# The shared `simp only` set every witness uses to reduce the accumulator loop
# at a literal input. `decide` cannot be used: the opaque dimensionless query
# leaves the `Decidable` instance stuck, so the loop is unfolded instead (the
# `_def`-style unfolding route) and the residual goal is a ground (dis)equality
# between opaque atoms, discharged from the witness's own hypothesis.
# ---------------------------------------------------------------------------
_W_SIMP = ("implementation_collectFunction, Id.run, List.forIn_cons, "
           "List.forIn_nil,\n    bind, pure, List.map_cons, List.map_nil, "
           "canonDim")


# ===========================================================================
# SOUNDNESS POSITIVES — structurally different but CORRECT implementations that
# MUST verify. Each re-proves the byte-identical obligation with no helper
# lemma, no new declaration, no `axiom`/`sorry`/`admit`/`native_decide`.
# ===========================================================================

# Reshape: invert the per-element test and bind the chosen dimension to a local
# before a SINGLE append, instead of two literal appends in the two branches.
# nagini's `pos-control-inverted-branch-local`, re-expressed. Keeps the
# imperative accumulator loop so the proof stays close to the frozen one (the
# same generalize-the-accumulator induction over `List.forIn_cons`).
_POS_INVERTED = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do\n"
    "  let mut dims : List Dim := []\n"
    "  for fd in fds do\n"
    "    -- Inverted test + local binding: same verdict on every element.\n"
    "    let nc := if !isDimensionless fd.2 then fd.2 else dimOne\n"
    "    dims := dims ++ [nc]\n"
    "  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }\n"
)
_POS_INVERTED_PROOF = (
    "  have step : ∀ (d : Dim), (if !isDimensionless d then d else dimOne)\n"
    "      = canonDim d := by\n"
    "    intro d\n"
    "    by_cases hb : isDimensionless d = true <;> simp [canonDim, hb]\n"
    "  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),\n"
    "      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>\n"
    "        (do\n"
    "          pure PUnit.unit\n"
    "          pure (ForInStep.yield\n"
    "            (r ++ [if !isDimensionless fd.2 then fd.2 else dimOne]))) : Id _))\n"
    "        = init ++ fds.map (fun fd => canonDim fd.2) := by\n"
    "    intro fds\n"
    "    induction fds with\n"
    "    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, "
    "List.map_nil, List.append_nil]\n"
    "    | cons a as ih =>\n"
    "      intro init\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind, pure] at ih ⊢\n"
    "      rw [ih (init ++ [if !isDimensionless a.2 then a.2 else dimOne])]\n"
    "      simp only [List.map_cons, step, List.append_assoc, List.cons_append,\n"
    "        List.nil_append]\n"
    "  intro func fds\n"
    "  unfold problem_spec_collectFunction implementation_collectFunction\n"
    "  refine ⟨rfl, ?_⟩\n"
    "  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>\n"
    "        (do\n"
    "          pure PUnit.unit\n"
    "          pure (ForInStep.yield\n"
    "            (r ++ [if !isDimensionless fd.2 then fd.2 else dimOne]))) : Id _)))"
    " = _\n"
    "  rw [helper]\n"
    "  simp\n"
)

# Reshape: drop the accumulator loop entirely and report the element-wise map of
# the grounded per-element canonicalisation. nagini's
# `pos-control-grounded-oracle`, re-expressed: the oracle is a pure function of
# the input, so materialising it is the CORRECT answer, not an echo.
_POS_MAP = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=\n"
    "  -- Element-wise reshape: the per-element canonicalisation is a pure\n"
    "  -- function of that element, so map it directly.\n"
    "  { factor := applyFunc func (fds.map Prod.fst),\n"
    "    dims := fds.map (fun fd => canonDim fd.2) }\n"
)
_POS_MAP_PROOF = (
    "  intro func fds\n"
    "  unfold problem_spec_collectFunction implementation_collectFunction\n"
    "  exact ⟨rfl, rfl⟩\n"
)

# Reshape: a right fold over the argument pairs (front-recursive rather than an
# accumulator), with the branch inverted as well.
_POS_FOLDR = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult :=\n"
    "  -- Front-recursive reshape: fold from the right, prepending each\n"
    "  -- element's reported dimension, with the test written the other way up.\n"
    "  { factor := applyFunc func (fds.map Prod.fst),\n"
    "    dims := fds.foldr (fun fd acc =>\n"
    "      (if !isDimensionless fd.2 then fd.2 else dimOne) :: acc) [] }\n"
)
_POS_FOLDR_PROOF = (
    "  have h : ∀ (l : List (Factor × Dim)),\n"
    "      l.foldr (fun fd acc =>\n"
    "        (if !isDimensionless fd.2 then fd.2 else dimOne) :: acc) []\n"
    "        = l.map (fun fd => canonDim fd.2) := by\n"
    "    intro l\n"
    "    induction l with\n"
    "    | nil => rfl\n"
    "    | cons a as ih =>\n"
    "      simp only [List.foldr_cons, List.map_cons, ih, canonDim]\n"
    "      by_cases hb : isDimensionless a.2 = true <;> simp [hb]\n"
    "  intro func fds\n"
    "  unfold problem_spec_collectFunction implementation_collectFunction\n"
    "  exact ⟨rfl, h fds⟩\n"
)


# ===========================================================================
# ADMISSIBILITY — the obligation must be SATISFIABLE at an F2P-shaped input, not
# merely provable in the abstract. On a total carrier there is no precondition to
# be too strong, so the analogue of PRECOND-TOO-STRONG is the obligation being
# unsatisfiable at exactly the concrete shape the F2P exercises. This is tested
# directly: the ground instance is discharged BY EVALUATION as a `have`, at the
# single-argument shape, over BOTH verdicts of the dimensionless query, before
# the frozen obligation is closed verbatim after it.
# ===========================================================================
_ADM_PROOF = (
    "  have _f2p : ∀ (d : Dim),\n"
    "      problem_spec_collectFunction 1 [((1 : Factor), d)]\n"
    "        (implementation_collectFunction 1 [((1 : Factor), d)]) := by\n"
    "    intro d\n"
    "    refine ⟨rfl, ?_⟩\n"
    "    by_cases hb : isDimensionless d = true <;>\n"
    "      simp only [" + _W_SIMP + ", hb, if_true, if_false] <;> simp\n"
) + _PROOF_GOLD


# ===========================================================================
# UNIQUENESS RIVALS — wrong implementations sharing the frozen spec that MUST be
# rejected. The impl region alone changes (the frozen tactic body is kept, so the
# build failure is the DEFAULT reshape outcome and attributes nothing by itself);
# each case's `witness` is what makes the rejection attributable to the spec.
# ===========================================================================

# (C2) THE CENTRAL RIVAL — report every argument dimension verbatim, with no
# canonicalisation at all. Correct on genuinely-dimensioned arguments and on
# already-unit ones; wrong exactly on the load-bearing sub-domain.
_W_NO_CANON = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do\n"
    "  let mut dims : List Dim := []\n"
    "  for fd in fds do\n"
    "    dims := dims ++ [fd.2]\n"
    "  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }\n"
)

# (C2) THE OPPOSITE RULE — canonicalise the dimensioned arguments and leave the
# dimensionless ones verbatim. Wrong on BOTH regimes wherever they differ.
_W_INVERTED = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do\n"
    "  let mut dims : List Dim := []\n"
    "  for fd in fds do\n"
    "    if isDimensionless fd.2 then\n"
    "      dims := dims ++ [fd.2]\n"
    "    else\n"
    "      dims := dims ++ [dimOne]\n"
    "  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }\n"
)

# (C2, position) HEAD LEFT VERBATIM — canonicalise every argument except the
# first. Agrees with the desired behavior everywhere else.
_W_HEAD = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do\n"
    "  let mut dims : List Dim := []\n"
    "  let mut k := 0\n"
    "  for fd in fds do\n"
    "    if k > 0 && isDimensionless fd.2 then\n"
    "      dims := dims ++ [dimOne]\n"
    "    else\n"
    "      dims := dims ++ [fd.2]\n"
    "    k := k + 1\n"
    "  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }\n"
)

# (C2, position) TAIL LEFT VERBATIM — canonicalise every argument except the
# last. Disjoint from the head rival; each is a near-miss of the other.
_W_TAIL = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do\n"
    "  let mut dims : List Dim := []\n"
    "  let mut k := 0\n"
    "  for fd in fds do\n"
    "    k := k + 1\n"
    "    if k < fds.length && isDimensionless fd.2 then\n"
    "      dims := dims ++ [dimOne]\n"
    "    else\n"
    "      dims := dims ++ [fd.2]\n"
    "  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }\n"
)

# (C2, structural) REPORT NO DIMENSIONS AT ALL — the length half of the clause,
# refutable with NO hypothesis about the opaque carrier.
_W_DROP = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do\n"
    "  let dims : List Dim := []\n"
    "  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }\n"
)

# (C1) WRONG PROJECTION — rebuild the scale factor on the arguments' DIMENSION
# components instead of their scale-factor components. The canonicalisation is
# left correct, so only (C1) separates it.
_W_FACTOR_DIMS = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do\n"
    "  let mut dims : List Dim := []\n"
    "  for fd in fds do\n"
    "    if isDimensionless fd.2 then\n"
    "      dims := dims ++ [dimOne]\n"
    "    else\n"
    "      dims := dims ++ [fd.2]\n"
    "  return { factor := applyFunc func (fds.map Prod.snd), dims := dims }\n"
)

# (C2, structural) ORDER REVERSED — canonicalise every argument correctly, but
# report the dimensions back-to-front (prepend instead of append). AUDIT
# ADDITION: the ORDER half of clause (C2) was claimed as covered by the head and
# tail rivals, but both of those hold every element at the SAME dimension value,
# so a permutation of the reported list is invisible to their witnesses — each
# would still be refuted, and gold still not, if the spec pinned only the
# MULTISET of reported dimensions. This rival is a permutation and nothing else,
# so it separates order from content.
_W_REVERSED = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do\n"
    "  let mut dims : List Dim := []\n"
    "  for fd in fds do\n"
    "    if isDimensionless fd.2 then\n"
    "      dims := [dimOne] ++ dims\n"
    "    else\n"
    "      dims := [fd.2] ++ dims\n"
    "  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }\n"
)

# (C1) HEAD IGNORED — rebuild the scale factor under a fixed head instead of the
# one supplied. Attacks the `func` binder specifically.
_W_FACTOR_HEAD = (
    "def implementation_collectFunction\n"
    "    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do\n"
    "  let mut dims : List Dim := []\n"
    "  for fd in fds do\n"
    "    if isDimensionless fd.2 then\n"
    "      dims := dims ++ [dimOne]\n"
    "    else\n"
    "      dims := dims ++ [fd.2]\n"
    "  return { factor := applyFunc 0 (fds.map Prod.fst), dims := dims }\n"
)


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS POSITIVES. If a faithful correct implementation cannot satisfy
    # the frozen obligation, the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-inverted-branch-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_INVERTED, _POS_INVERTED_PROOF),
        "rationale": (
            "nagini's pos-control-inverted-branch-local, re-expressed on this "
            "carrier: the per-element test is INVERTED (ask whether the "
            "dimension is NOT regarded as dimensionless first) and the chosen "
            "dimension is bound to a local before a SINGLE append, instead of "
            "two literal appends in the two branches. Every element yields the "
            "same reported dimension as the frozen shape, and the "
            "reconstruction is untouched, so both (C1) and (C2) hold and the "
            "case MUST verify. The frozen tactic body no longer applies (its "
            "`show` names the two-branch loop body, which this shape does not "
            "have), so the obligation is re-proved for the new shape by the same "
            "generalize-the-accumulator induction over `List.forIn_cons`, plus a "
            "one-line `by_cases` bridging the inverted test to the specification's "
            "per-element canonicalisation. The theorem STATEMENT is byte-identical "
            "and no helper declaration, axiom, or assumption token is introduced."
        ),
    },
    {
        "id": "pos-elementwise-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_MAP, _POS_MAP_PROOF),
        "rationale": (
            "nagini's pos-control-grounded-oracle, re-expressed: drop the "
            "accumulator loop entirely and report the element-wise map of the "
            "per-element canonicalisation. nagini's argument carries over "
            "verbatim — this is NOT an ungrounded-oracle cheat, because the "
            "oracle is GROUNDED: it is a pure function of the input argument "
            "pairs, fully unfolded, bottoming out in the opaque-but-pure "
            "dimensionless query that the specification and every implementation "
            "read identically. There is no answer key an implementation could "
            "echo to a WRONG list and still satisfy the spec, so materialising it "
            "IS the correct answer. This is the cheapest honest implementation and "
            "the positive control standing in for the ungrounded-oracle slot: if "
            "it did not verify, the spec would be rejecting its own grounded model "
            "=> SPEC-TOO-STRONG. Both clauses then close by `rfl`."
        ),
    },
    {
        "id": "pos-foldr-inverted",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_FOLDR, _POS_FOLDR_PROOF),
        "rationale": (
            "A THIRD structurally distinct correct shape, chosen to vary the "
            "traversal itself rather than only the per-element step: a "
            "front-recursive right fold that prepends each element's reported "
            "dimension, with the test written the other way up. Where the frozen "
            "shape accumulates left-to-right and appends, this one recurses from "
            "the front and conses, so the reported list is built in the opposite "
            "direction yet must come out identical — which is exactly what (C2)'s "
            "ORDER dependence demands of a correct implementation. Proved by a "
            "direct induction with the branch bridged by `by_cases`; no "
            "accumulator generalization is needed because the fold is already "
            "front-recursive. MUST verify, else SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY. Nothing here has a precondition, so the lane's content on
    # this carrier is SATISFIABILITY at the F2P-shaped input.
    # =====================================================================
    {
        "id": "admiss-f2p-singleton",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(_IMPL_GOLD, _ADM_PROOF),
        "rationale": (
            "nagini's admiss-f2p-singleton, re-expressed for a total carrier. "
            "The frozen obligation carries no precondition hypothesis, so there "
            "is no `requires` clause for a probe to discharge — but that is NOT "
            "the same as the lane being vacuous, and this battery previously "
            "recorded it as vacuous for exactly that reason. The analogue here is "
            "SATISFIABILITY at the concrete shape the F2P exercises: a spec whose "
            "two clauses could not both hold at a one-argument application would "
            "be unsatisfiable there, and every soundness positive would still "
            "verify (they close the universally quantified obligation, which is "
            "provable from a spec no input satisfies only if the spec is "
            "contradictory — a distinction a `∀`-shaped proof does not surface). "
            "So the ground instance is discharged BY EVALUATION as a `have`, at "
            "the single-argument F2P shape, over BOTH verdicts of the "
            "dimensionless query (the query is opaque, so the branch is split "
            "rather than computed — nothing about the carrier is assumed), and "
            "the frozen obligation is then closed verbatim after it. The impl is "
            "the frozen one and the theorem STATEMENT is byte-identical; only the "
            "tactic body gains the prepended `have`, which variant scope permits. "
            "If this did not verify, the modeled behavior would be unsatisfiable "
            "at the shape the F2P actually exercises."
        ),
    },

    # =====================================================================
    # UNIQUENESS RIVALS. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness that
    # HOLDS of the rival and FAILS on the frozen solution.
    # =====================================================================
    {
        "id": "weak-no-canonicalisation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_NO_CANON),
        "refinement": (
            "This IS the undesired behavior the instance is about: report every "
            "argument's dimension exactly as it arrived, with no normalisation of "
            "the ones that reduce to no net dimension. Its faithful real patch is "
            "the pre-change code itself, and the F2P observable defeats it "
            "directly: the reported dimension of the function application is then "
            "the argument's original symbolic form rather than the unit "
            "dimension, so the subsequent same-dimension comparison against a "
            "plain number sees two structurally UNEQUAL dimensions, rejects the "
            "sum, and raises instead of returning a value. The F2P assertion that "
            "the sum collects to the unit dimension therefore FAILS => not "
            "resolved. A rival that verified here would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECT from clause (C2): the spec demands `result.dims = fds.map "
            "(fun fd => canonDim fd.2)`, and `canonDim` reports the unit "
            "dimension whenever the dimension system regards the argument as "
            "dimensionless. The rival reports the argument's own dimension "
            "instead. Refuted on the load-bearing sub-domain — a dimension the "
            "system reports dimensionless that is NOT already the unit dimension "
            "— which is the only sub-domain on which the desired and undesired "
            "behaviors differ at all, and exactly the F2P regime. If it verified, "
            "the spec would admit the undesired behavior => SPEC-TOO-WEAK."
        ),
        # Conditions on the carrier: `isDimensionless` and `dimOne` are opaque, so
        # the two hypotheses describe the probed point instead of computing it.
        # They constrain two DISTINCT opaque terms (a Bool and a Nat), so they are
        # jointly satisfiable and no False follows from the binders alone.
        "witness": (
            "-- At an argument whose dimension the system reports dimensionless\n"
            "-- yet which is not already the unit dimension, the reported list\n"
            "-- must be the unit dimension; the rival reports the argument's own.\n"
            "example (hdim : isDimensionless 7 = true) (hne : dimOne ≠ 7) :\n"
            "    ¬ problem_spec_collectFunction 0 [((0 : Factor), (7 : Dim))]\n"
            "        (implementation_collectFunction 0 [((0 : Factor), (7 : Dim))])"
            " := by\n"
            "  intro h\n"
            "  have hd := h.2\n"
            "  simp only [" + _W_SIMP + ", hdim, if_true] at hd\n"
            "  simp at hd\n"
            "  exact hne hd.symm\n"
        ),
    },
    {
        "id": "weak-inverted-canonicalisation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_INVERTED),
        "refinement": (
            "The exact opposite rule: normalise the arguments the dimension "
            "system does NOT regard as dimensionless, and pass the dimensionless "
            "ones through untouched. Its faithful real patch would (a) leave the "
            "F2P argument's dimension in its original non-unit form, so the "
            "downstream same-dimension comparison still rejects the sum and the "
            "F2P still raises, AND (b) collapse every genuinely-dimensioned "
            "argument to the unit dimension, destroying the dimensional "
            "bookkeeping the pre-existing dimensional-arithmetic tests assert "
            "(a function application over a dimensioned argument would report no "
            "dimension at all). It resolves neither the F2P nor the tests already "
            "passing => not resolved."
        ),
        "rationale": (
            "REJECT from clause (C2) on the OTHER side of the branch: for an "
            "argument the system does not regard as dimensionless, `canonDim` "
            "reports that dimension unchanged, while the rival reports the unit "
            "dimension. Refuted at a dimensioned argument (`isDimensionless 3 = "
            "false`), which varies the dimensionless verdict — the very input the "
            "modeled behavior branches on — off the value every other C2 witness "
            "holds it at. A rival that mishandled only the dimensioned regime "
            "would otherwise slip through => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- At an argument the system does NOT report dimensionless, the\n"
            "-- reported dimension must be that argument's own; the rival reports\n"
            "-- the unit dimension instead.\n"
            "example (hdim : isDimensionless 3 = false) (hne : dimOne ≠ 3) :\n"
            "    ¬ problem_spec_collectFunction 0 [((0 : Factor), (3 : Dim))]\n"
            "        (implementation_collectFunction 0 [((0 : Factor), (3 : Dim))])"
            " := by\n"
            "  intro h\n"
            "  have hd := h.2\n"
            "  simp only [" + _W_SIMP + ", hdim] at hd\n"
            "  simp at hd\n"
            "  exact hne hd\n"
        ),
    },
    {
        "id": "weak-head-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_HEAD),
        "refinement": (
            "Normalise every argument except the FIRST, which is passed through "
            "as it arrived. Its faithful real patch would skip the first "
            "positional argument when building the reported dimensions. On a "
            "multi-argument application whose first argument is dimensionless but "
            "written non-canonically, the original symbolic dimension leaks out "
            "of the leading slot and the downstream same-dimension comparison "
            "rejects it, so an F2P-shaped sum over such an application still "
            "raises. It is ALSO wrong on the single-argument F2P case itself, "
            "where the first argument IS the only argument => not resolved. A "
            "test whose leading argument is never in that regime would not catch "
            "this, which is why the position is probed explicitly."
        ),
        "rationale": (
            "REJECT from clause (C2)'s per-POSITION dependence: `fds.map` applies "
            "the canonicalisation at every index, including index 0. Refuted on a "
            "TWO-element list at the HEAD position — where this rival and the tail "
            "rival disagree — so the two near-misses are separated rather than "
            "sharing an input: both elements are in the dimensionless-but-non-unit "
            "regime, so the rival's reported list is wrong in its FIRST slot and "
            "correct in its second, pinning the divergence to the position rather "
            "than to the element. If it verified, the spec would leave the leading "
            "argument's canonicalisation unpinned => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Two arguments, both dimensionless-but-non-unit. The reported list\n"
            "-- must be the unit dimension in BOTH slots; the rival leaves the\n"
            "-- leading slot as the argument's own dimension.\n"
            "example (hdim : isDimensionless 7 = true) (hne : dimOne ≠ 7) :\n"
            "    ¬ problem_spec_collectFunction 0\n"
            "        [((1 : Factor), (7 : Dim)), ((2 : Factor), (7 : Dim))]\n"
            "        (implementation_collectFunction 0\n"
            "          [((1 : Factor), (7 : Dim)), ((2 : Factor), (7 : Dim))])"
            " := by\n"
            "  intro h\n"
            "  have hd := h.2\n"
            "  simp only [" + _W_SIMP + ", hdim, if_true] at hd\n"
            "  simp at hd\n"
            "  exact hne hd.symm\n"
        ),
    },
    {
        "id": "weak-tail-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_TAIL),
        "refinement": (
            "Normalise every argument except the LAST, which is passed through as "
            "it arrived — disjoint from the head rival. Its faithful real patch "
            "would skip the final positional argument. This one breaks the ACTUAL "
            "F2P witness head-on: the F2P application has a single argument, so "
            "the last argument is the only argument, the dimensionless-but-"
            "non-canonical dimension leaks out unchanged, the downstream "
            "same-dimension comparison rejects the sum and it raises rather than "
            "collecting to the unit dimension => not resolved."
        ),
        "rationale": (
            "REJECT from clause (C2)'s per-POSITION dependence at the other end: "
            "the canonicalisation applies at the final index too. Refuted on a "
            "two-element list at the TAIL position, at a dimension value (`9`) "
            "distinct from every other witness's, so this near-miss of the head "
            "rival is demonstrated on the sub-domain where the two actually "
            "differ rather than on a shared input. If it verified, the spec would "
            "leave the trailing argument's canonicalisation unpinned => "
            "SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Two arguments, both dimensionless-but-non-unit. The reported list\n"
            "-- must be the unit dimension in BOTH slots; the rival leaves the\n"
            "-- trailing slot as the argument's own dimension.\n"
            "example (hdim : isDimensionless 9 = true) (hne : dimOne ≠ 9) :\n"
            "    ¬ problem_spec_collectFunction 0\n"
            "        [((4 : Factor), (9 : Dim)), ((5 : Factor), (9 : Dim))]\n"
            "        (implementation_collectFunction 0\n"
            "          [((4 : Factor), (9 : Dim)), ((5 : Factor), (9 : Dim))])"
            " := by\n"
            "  intro h\n"
            "  have hd := h.2\n"
            "  simp only [" + _W_SIMP + ", hdim, if_true] at hd\n"
            "  simp at hd\n"
            "  exact hne hd.symm\n"
        ),
    },
    {
        "id": "weak-drop-dims-entirely",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_DROP),
        "refinement": (
            "Report no per-argument dimensions at all. Its faithful real patch "
            "would return only the rebuilt scale factor, dropping the trailing "
            "dimension components of the collected result. Every caller of the "
            "collection unpacks a scale factor AND a dimension, so the F2P "
            "scenario cannot even reach its assertion — the sum's dimension is "
            "absent rather than the unit dimension — and the pre-existing "
            "dimensional-arithmetic tests that read the dimension of a function "
            "application break the same way => not resolved."
        ),
        "rationale": (
            "REJECT from the STRUCTURAL half of clause (C2): `fds.map` preserves "
            "LENGTH, so a one-argument application must report exactly one "
            "dimension. This is the one rival refutable with NO hypothesis about "
            "the opaque carrier at all — the length mismatch (0 vs 1) is "
            "transparent whatever the dimensionless query returns and whatever "
            "the unit dimension is — so it pins the clause's shape independently "
            "of its value content. If it verified, the spec would constrain only "
            "the dimensions it happens to report and not how many => "
            "SPEC-TOO-WEAK."
        ),
        # AUDIT REPAIR (attack B′). The previous witness omitted the
        # dimensionless-verdict rewrite entirely, on the theory that a length
        # mismatch needs no carrier hypothesis. The LENGTH claim indeed needs
        # none, but the frozen impl's `if isDimensionless 2 then _ else _` is
        # still sitting inside the loop term, so without a rewrite for that
        # branch `simp` cannot finish reducing the accumulator on EITHER side.
        # Measured: gold's build failed with `unsolved goals … hd : (match if
        # isDimensionless 2 = true then ForInStep.yield [dimOne] else … ) = …`,
        # i.e. an UNREDUCED loop term, and a forgery asserting the exact
        # OPPOSITE (that the frozen impl SATISFIES the spec at this input)
        # failed with the same unreduced goal. Gold's exit code therefore
        # carried no information about the claim. The same witness also failed
        # against the battery's own VERIFYING `pos-elementwise-map` impl for
        # the unrelated reason that `simp` closed it there (`hd : True`), so a
        # `witness_reference` would have masked rather than fixed it.
        #
        # The repair keeps the case's point — no HYPOTHESIS about the carrier
        # is needed — by case-splitting on the opaque query instead of assuming
        # it: the loop reduces under BOTH verdicts, and the length mismatch
        # (0 vs 1) refutes the rival in either branch. Now gold's hypothesis
        # reduces to the concrete `[] ++ [dimOne] = [dimOne]` (which `simp`
        # proves, so gold is not refuted) while the rival's reduces to the
        # false `[] = [dimOne]`, and the flipped claim VERIFIES on gold — so
        # the exit code tracks the claim.
        "witness": (
            "-- One argument in, so exactly one reported dimension out. The rival\n"
            "-- reports none. No ASSUMPTION about the carrier is needed: the loop\n"
            "-- is reduced under BOTH verdicts of the dimensionless query and the\n"
            "-- length mismatch refutes the rival in either branch.\n"
            "example :\n"
            "    ¬ problem_spec_collectFunction 0 [((0 : Factor), (2 : Dim))]\n"
            "        (implementation_collectFunction 0 [((0 : Factor), (2 : Dim))])"
            " := by\n"
            "  intro h\n"
            "  have hd := h.2\n"
            "  by_cases hb : isDimensionless 2 = true <;>\n"
            "    simp only [" + _W_SIMP + ", hb, if_true, if_false] at hd <;>\n"
            "    simp at hd\n"
        ),
    },
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_REVERSED),
        "refinement": (
            "Canonicalise every argument correctly, but report the per-argument "
            "dimensions in the reverse of the order the arguments arrived in. Its "
            "faithful real patch would build the reported dimension components by "
            "prepending rather than appending. The F2P application has a single "
            "argument, on which a reversal is the identity, so THIS rival's real "
            "patch does resolve the F2P — and that is precisely why it belongs in "
            "the reject lane rather than being dismissed: it is a rival the F2P "
            "cannot see, whose wrongness is visible only to the pre-existing "
            "multi-argument dimensional-arithmetic tests, where the reported "
            "dimensions would be paired with the wrong positional arguments. A "
            "spec that admitted it would be pinning the multiset of reported "
            "dimensions and not the sequence => the collected result of a "
            "two-argument application would carry its arguments' dimensions "
            "transposed => not resolved, on the P2P side."
        ),
        "rationale": (
            "REJECT from the ORDER half of clause (C2), which no other case "
            "actually separates: `fds.map` is order-preserving, and the head and "
            "tail rivals both hold EVERY element at the same dimension value "
            "(`7`, `9`), so a permutation of their reported lists is invisible to "
            "their witnesses — both would still be refuted, and gold still not, "
            "under a spec that pinned only the multiset. This rival is a "
            "permutation and nothing else: its per-element canonicalisation is "
            "correct, its length is correct, and its factor is correct. Refuted "
            "on a two-element list whose elements sit in OPPOSITE regimes (the "
            "first dimensionless-but-non-unit, so the spec demands the unit "
            "dimension; the second genuinely dimensioned, so the spec demands it "
            "unchanged), which is the only shape on which a reversal is "
            "observable at all. If it verified, the spec would leave the "
            "argument-to-dimension correspondence unpinned => SPEC-TOO-WEAK."
        ),
        # Three hypotheses over three DISTINCT opaque terms (the two Bool values
        # `isDimensionless 7` / `isDimensionless 3` and the Nat `dimOne`), so no
        # term is constrained twice and no `False` follows from the binders alone.
        "witness": (
            "-- Two arguments in OPPOSITE regimes: the first dimensionless-but-\n"
            "-- non-unit (so the spec demands the unit dimension), the second\n"
            "-- genuinely dimensioned (so the spec demands it unchanged). The\n"
            "-- spec fixes the ORDER of those two, so a rival reporting them\n"
            "-- transposed is refuted here.\n"
            "example (h7 : isDimensionless 7 = true) (h3 : isDimensionless 3 = false)\n"
            "    (hne : dimOne ≠ 3) :\n"
            "    ¬ problem_spec_collectFunction 0\n"
            "        [((1 : Factor), (7 : Dim)), ((2 : Factor), (3 : Dim))]\n"
            "        (implementation_collectFunction 0\n"
            "          [((1 : Factor), (7 : Dim)), ((2 : Factor), (3 : Dim))])"
            " := by\n"
            "  intro h\n"
            "  have hd := h.2\n"
            "  simp only [" + _W_SIMP + ", h7, h3, if_true, if_false] at hd\n"
            "  simp at hd\n"
            "  exact hne hd.2\n"
        ),
    },
    {
        "id": "weak-factor-from-dimensions",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_FACTOR_DIMS),
        "refinement": (
            "Rebuild the scale factor on the arguments' DIMENSION components "
            "instead of their scale-factor components, leaving the "
            "canonicalisation correct. Its faithful real patch would pass the "
            "wrong tuple component into the function reconstruction, so the "
            "returned scale factor becomes a function of dimensions rather than "
            "of magnitudes. The F2P asserts the collected result's scale factor "
            "equals a specific numeric value; this returns the function applied "
            "to a dimension expression instead, so the assertion fails on its "
            "FIRST component even though the dimension component is right, and "
            "every pre-existing test asserting a numeric scale factor for a "
            "function application fails too => not resolved."
        ),
        "rationale": (
            "REJECT from clause (C1): the spec pins `result.factor = applyFunc "
            "func (fds.map Prod.fst)` — the reconstruction reads the "
            "SCALE-FACTOR projection of the argument pairs. This is the frame "
            "half of the spec (the modeled behavior does not touch the scale "
            "factor, so the spec must pin it to its inputs), and it has no nagini "
            "counterpart because nagini's modeled function returns only the "
            "dimension list. Refuted at an argument whose two components DIFFER "
            "(`(1, 5)`) — the only shape that can separate a rival reading the "
            "wrong projection — by conditioning on the reconstruction "
            "distinguishing those two argument lists. If it verified, the "
            "scale-factor component would be unpinned and an implementation could "
            "return anything there => SPEC-TOO-WEAK."
        ),
        # One hypothesis about the opaque reconstruction, at two distinct
        # arguments: satisfiable (`applyFunc` is an arbitrary function, and
        # nothing forces it to agree on `[1]` and `[5]`).
        "witness": (
            "-- The rebuilt factor must come from the arguments' scale-factor\n"
            "-- components. At an argument whose two components differ, and where\n"
            "-- the reconstruction separates those two lists, the rival's factor\n"
            "-- is the wrong one.\n"
            "example (hfac : applyFunc 0 [(1 : Factor)] ≠ applyFunc 0 [(5 : Factor)]) :\n"
            "    ¬ problem_spec_collectFunction 0 [((1 : Factor), (5 : Dim))]\n"
            "        (implementation_collectFunction 0 [((1 : Factor), (5 : Dim))])"
            " := by\n"
            "  intro h\n"
            "  have hf := h.1\n"
            "  simp only [" + _W_SIMP + "] at hf\n"
            "  exact hfac hf.symm\n"
        ),
    },
    {
        "id": "weak-factor-drops-head",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_W_FACTOR_HEAD),
        "refinement": (
            "Rebuild the scale factor under a FIXED function head instead of the "
            "one the application actually has, leaving the canonicalisation "
            "correct. Its faithful real patch would reconstruct the result with a "
            "hardcoded function rather than the expression's own. The F2P asserts "
            "the collected scale factor is the exponential of the argument's "
            "magnitude; under a fixed head it is some other function of that "
            "magnitude, so the assertion fails, and every pre-existing test "
            "collecting a function application (a logarithm, an absolute value, a "
            "sine) would report the wrong function too => not resolved."
        ),
        "rationale": (
            "REJECT from clause (C1) via the `func` binder specifically: the "
            "reconstruction must use the head that was supplied. This is the "
            "binder no other witness exercises — every C2 witness holds it at `0` "
            "because the canonicalisation does not read it — so without this case "
            "a rival that mishandled ONLY the function head would verify and the "
            "battery would never notice. Refuted at `func = 4`, deliberately off "
            "the value at which a head-ignoring rival coincides with the "
            "specification, by conditioning on the reconstruction distinguishing "
            "the two heads. If it verified, the spec would not pin which function "
            "is rebuilt => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- The reconstruction must use the supplied head. At a head the rival\n"
            "-- ignores, and where the reconstruction separates the two heads, the\n"
            "-- rival's factor is the wrong one.\n"
            "example (hfac : applyFunc 4 [(1 : Factor)] ≠ applyFunc 0 [(1 : Factor)]) :\n"
            "    ¬ problem_spec_collectFunction 4 [((1 : Factor), (3 : Dim))]\n"
            "        (implementation_collectFunction 4 [((1 : Factor), (3 : Dim))])"
            " := by\n"
            "  intro h\n"
            "  have hf := h.1\n"
            "  simp only [" + _W_SIMP + "] at hf\n"
            "  exact hfac hf.symm\n"
        ),
    },
]


# The axiom lane is G-AX's job and this gate ignores it. Empty here in any case:
# meta.json records `axioms == []` and `deep_model_references == []` — the
# canonicalisation decision is modeled deeply and structurally over the
# observable argument pairs, and the opaque callees carry signatures only (no
# consumed property), so there is no in-model axiom obligation to re-discharge.
AXIOM_TESTS = []
