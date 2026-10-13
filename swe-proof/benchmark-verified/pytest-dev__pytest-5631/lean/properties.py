"""properties.py — G-PBT falsification battery for pytest-dev__pytest-5631 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over a list of decoration abstractions):

  num_mock_patch_args (patchings : List Patching) : Option Nat
      result = some ((patchings.filter isCounted).length)

  A ``Patching`` abstracts one decoration by three bits: whether it binds a
  named attribute (``attributeName``), whether its replacement is one of the
  recognised sentinel defaults (``isSentinel``), and whether comparing that
  replacement for equality yields an ordinary boolean (``eqWellDefined``). A
  decoration is argument-consuming (``isCounted``) exactly when it does NOT bind
  a named attribute AND its replacement is a sentinel default. The count is
  ALWAYS produced (``some _``): it is determined by the structural criterion and
  must NEVER depend on the ambiguous truth value of an equality comparison — a
  decoration whose replacement has an ill-defined equality truth value is still
  classified totally.

  Load-bearing postcondition clauses (all in ``problem_spec_num_mock_patch_args``):
    (P-count)     result = some ((patchings.filter isCounted).length) — the EXACT
                  count of argument-consuming decorations.
    (P-total)     the result is ``some _`` on EVERY admissible input, including a
                  decoration whose equality truth value is ambiguous. There is no
                  ``none`` escape for the ambiguous case; ``none`` is the abstraction
                  of an aborted computation and the spec forbids it everywhere.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the input list carries no heap permission, there is no read-only half-
    permission to overwrite and no aliasing to exploit. The nagini frame-
    mutation rival (a store into the read-only input, rejected for insufficient
    permission) has NO expressible instance here and no substitute is fabricated
    for it. See 'assessment'.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the
    input: ``some ((patchings.filter isCounted).length)`` is a term built only
    from the argument, fully unfoldable element-by-element, not an opaque answer
    key. The bundle declares no ``opaque``/``axiom``, so there is nothing an
    implementation could echo without doing the classification. In its place the
    battery carries honest cheapest-implementation POSITIVE CONTROLS (``pos-*``).

  * CONTROL-FLOW-EFFECT / TOTALITY — APPLIES. The observable is that a value is
    ALWAYS produced. A rival that aborts (returns ``none``) on the ambiguous-
    equality sub-domain reproduces the pre-existing failure mode; (P-total)
    rejects it.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the decoration
    domain but diverging elsewhere: one that also counts the ambiguous-equality
    decoration (over-count), one that counts every decoration regardless of
    kind, one that drops the first decoration. (P-count) rejects each.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet proving the rival CONTRADICTS the spec at
one concrete input. Each is stated directly against the spec predicate at
``decide``-able literals, and each was checked to hold of its rival and to FAIL
on the frozen solution (so it discriminates rather than asserting a tautology).

AXIOM lane: DROPPED. The nagini bundle's ``AXIOM_TESTS`` (the deep-model
identity-soundness probe) belong to G-AX, which the G-PBT spec lane ignores;
meta.json records the A-reference deep model and G-AX passed it separately.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5631"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the impl region: every impl reshape lands entirely inside it.
_IMPL = (
    "  if patchings.isEmpty then\n"
    "    return some 0\n"
    "  let mut count : Nat := 0\n"
    "  for p in patchings do\n"
    "    if isCounted p then\n"
    "      count := count + 1\n"
    "  return some count"
)

# The FULL body of the proof region (helper lemma + the obligation). A case that
# reshapes the loop body reproves inside here; the `theorem correct_<name>`
# STATEMENT is preserved byte-identically (only the tactic body / the helper's
# body change — `forIn_count_eq` is in the frozen declaration set already).
_PROOF_REGION = (
    "/-- Helper (Route B): the conditional `forIn` loop, generalized over the\n"
    "accumulator, counts exactly the decorations satisfying `isCounted`. -/\n"
    "theorem forIn_count_eq (xs : List Patching) (init : Nat) :\n"
    "    Id.run (forIn xs init (fun p r =>\n"
    "      if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))\n"
    "      = init + (xs.filter isCounted).length := by\n"
    "  induction xs generalizing init with\n"
    "  | nil => rfl\n"
    "  | cons a as ih =>\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind, pure] at ih ⊢\n"
    "    by_cases h : isCounted a = true\n"
    "    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega\n"
    "    · simp only [Bool.not_eq_true] at h\n"
    "      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]\n"
    "\n"
    "theorem correct_num_mock_patch_args : ∀ patchings : List Patching,\n"
    "    problem_spec_num_mock_patch_args patchings\n"
    "      (implementation_num_mock_patch_args patchings) := by\n"
    "  intro patchings\n"
    "  unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args\n"
    "  by_cases he : patchings.isEmpty = true\n"
    "  · simp only [Id.run, he, if_true]\n"
    "    rw [List.isEmpty_iff] at he\n"
    "    subst he\n"
    "    rfl\n"
    "  · simp only [Id.run]\n"
    "    rw [if_neg he]\n"
    "    -- bridge the desugared loop body to the helper's clean body (definitionally equal)\n"
    "    have h2 : (do\n"
    "        pure PUnit.unit\n"
    "        let r ← forIn patchings 0 (fun p r =>\n"
    "          if isCounted p = true then do pure PUnit.unit; pure (ForInStep.yield (r + 1))\n"
    "          else do pure PUnit.unit; pure (ForInStep.yield r))\n"
    "        pure (some r) : Id (Option Nat))\n"
    "      = some (Id.run (forIn patchings 0 (fun p r =>\n"
    "          if isCounted p = true then pure (ForInStep.yield (r + 1)) else pure (ForInStep.yield r)))) := rfl\n"
    "    rw [h2, forIn_count_eq, Nat.zero_add]"
)

# The frozen obligation's opening two tactic lines — the injection point for the
# admissibility ground instance (a `have` prepended before the frozen body).
_PROOF_INTRO = (
    "  intro patchings\n"
    "  unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args"
)


# === POSITIVE CONTROLS (soundness) — structurally different but CORRECT ======
# implementations that MUST verify. If a faithful correct implementation cannot
# satisfy the frozen obligation, the spec is SPEC-TOO-STRONG. Each keeps the
# `theorem correct_num_mock_patch_args` statement byte-identical and re-proves it
# for the new shape; none introduces a helper lemma, an axiom, or an assumption
# token beyond the frozen set (the helper `forIn_count_eq` is already frozen).

# --- pos-cheap: return the grounded fold directly (P-count trivially). --------
_CHEAP_IMPL = "  return some ((patchings.filter isCounted).length)"
_CHEAP_PROOF = (
    "theorem correct_num_mock_patch_args : ∀ patchings : List Patching,\n"
    "    problem_spec_num_mock_patch_args patchings\n"
    "      (implementation_num_mock_patch_args patchings) := by\n"
    "  intro patchings\n"
    "  unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args\n"
    "  rfl"
)
POS_CHEAP = _swap(_swap(_BASE, _IMPL, _CHEAP_IMPL), _PROOF_REGION, _CHEAP_PROOF)

# --- pos-arith: replace the `if`-increment with an arithmetic accumulate. -----
# `count := count + (if isCounted p then 1 else 0)` — same value flow. The frozen
# helper's loop body was `if … then yield (r+1) else yield r`; the reshaped loop
# desugars to `yield (r + if … then 1 else 0)`, so `forIn_count_eq` is restated
# over that body (its STATEMENT changes; it is NOT the `correct_` obligation, and
# it stays in the frozen declaration set — no NEW theorem/lemma is introduced).
_ARITH_IMPL = (
    "  if patchings.isEmpty then\n"
    "    return some 0\n"
    "  let mut count : Nat := 0\n"
    "  for p in patchings do\n"
    "    count := count + (if isCounted p then 1 else 0)\n"
    "  return some count"
)
_ARITH_PROOF = (
    "/-- Helper (Route B): the arithmetic-accumulate `forIn` loop, generalized over\n"
    "the accumulator, counts exactly the decorations satisfying `isCounted`. -/\n"
    "theorem forIn_count_eq (xs : List Patching) (init : Nat) :\n"
    "    Id.run (forIn xs init (fun p r =>\n"
    "      pure (ForInStep.yield (r + (if isCounted p = true then 1 else 0)))))\n"
    "      = init + (xs.filter isCounted).length := by\n"
    "  induction xs generalizing init with\n"
    "  | nil => rfl\n"
    "  | cons a as ih =>\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind, pure] at ih ⊢\n"
    "    by_cases h : isCounted a = true\n"
    "    · simp only [h, if_true, ih, List.filter_cons, List.length_cons]; omega\n"
    "    · simp only [Bool.not_eq_true] at h\n"
    "      simp only [h, ih, List.filter_cons, Bool.false_eq_true, if_false]; omega\n"
    "\n"
    "theorem correct_num_mock_patch_args : ∀ patchings : List Patching,\n"
    "    problem_spec_num_mock_patch_args patchings\n"
    "      (implementation_num_mock_patch_args patchings) := by\n"
    "  intro patchings\n"
    "  unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args\n"
    "  by_cases he : patchings.isEmpty = true\n"
    "  · simp only [Id.run, he, if_true]\n"
    "    rw [List.isEmpty_iff] at he\n"
    "    subst he\n"
    "    rfl\n"
    "  · simp only [Id.run]\n"
    "    rw [if_neg he]\n"
    "    have h2 : (do\n"
    "        pure PUnit.unit\n"
    "        let r ← forIn patchings 0 (fun p r =>\n"
    "          do pure PUnit.unit; pure (ForInStep.yield (r + (if isCounted p = true then 1 else 0))))\n"
    "        pure (some r) : Id (Option Nat))\n"
    "      = some (Id.run (forIn patchings 0 (fun p r =>\n"
    "          pure (ForInStep.yield (r + (if isCounted p = true then 1 else 0)))))) := rfl\n"
    "    rw [h2, forIn_count_eq, Nat.zero_add]"
)
POS_ARITH = _swap(_swap(_BASE, _IMPL, _ARITH_IMPL), _PROOF_REGION, _ARITH_PROOF)


# === ADMISSIBILITY ===========================================================
# The frozen `correct_` theorem carries NO precondition hypothesis (the behavior
# is total, so `∀` is unguarded), so the nagini precondition-admission probe has
# no binder to attack. The honest analogue: discharge the spec predicate by
# evaluation at a representative reporting-shaped input (one argument-consuming
# decoration, one whose equality truth value is ambiguous, one attribute-bound),
# inside the proof region, alongside the frozen obligation. If that ground
# instance could not be discharged the modeled behavior would be unsatisfiable
# at exactly the shape the F2P exercises (the analogue of PRECOND-TOO-STRONG).
_ADMISS_BLOCK = (
    "  -- ADMISSIBILITY: the obligation is discharged at a representative input\n"
    "  -- shaped like the reporting scenario — one argument-consuming decoration,\n"
    "  -- one whose replacement has an ambiguous equality truth value, and one\n"
    "  -- attribute-bound decoration — confirming the behavior is satisfiable there.\n"
    "  have _ground : problem_spec_num_mock_patch_args\n"
    "      [ { attributeName := false, isSentinel := true,  eqWellDefined := true },\n"
    "        { attributeName := false, isSentinel := false, eqWellDefined := false },\n"
    "        { attributeName := true,  isSentinel := true,  eqWellDefined := true } ]\n"
    "      (implementation_num_mock_patch_args\n"
    "        [ { attributeName := false, isSentinel := true,  eqWellDefined := true },\n"
    "          { attributeName := false, isSentinel := false, eqWellDefined := false },\n"
    "          { attributeName := true,  isSentinel := true,  eqWellDefined := true } ]) := by\n"
    "    unfold problem_spec_num_mock_patch_args implementation_num_mock_patch_args\n"
    "    decide\n"
    + _PROOF_INTRO
)
ADMISS = _swap(_BASE, _PROOF_INTRO, _ADMISS_BLOCK)


# === UNIQUENESS / REJECT rivals ==============================================
# Wrong implementations sharing the frozen spec that MUST be rejected. Each
# carries (a) the refinement argument that its faithful real patch would NOT
# resolve the F2P — so a verifying rival would be a true
# verify-does-not-imply-resolve break, not an artifact — and (b) a refutation
# witness pinning the violation at one concrete input, checked to hold of the
# rival and to FAIL on the frozen solution.

# --- CONTROL-FLOW-EFFECT / TOTALITY (the discriminator; the actual bug). ------
# The pre-existing skeleton: a non-attribute decoration whose replacement has an
# ambiguous equality truth value ABORTS the whole computation (returns `none`)
# instead of yielding a count.
_TOTALITY_IMPL = (
    "  if patchings.isEmpty then\n"
    "    return some 0\n"
    "  let mut count : Nat := 0\n"
    "  for p in patchings do\n"
    "    if !p.attributeName then\n"
    "      if !p.eqWellDefined then\n"
    "        return none\n"
    "      if p.isSentinel then\n"
    "        count := count + 1\n"
    "  return some count"
)
RIVAL_TOTALITY = _swap(_BASE, _IMPL, _TOTALITY_IMPL)

# --- PARTIAL-DOMAIN / VALUE: also count the ambiguous-equality decoration. ----
# Correct on every input WITHOUT an ambiguous-equality non-attribute decoration,
# but over-counts on any input containing one (treats it as argument-consuming).
_PARTIAL_IMPL = (
    "  if patchings.isEmpty then\n"
    "    return some 0\n"
    "  let mut count : Nat := 0\n"
    "  for p in patchings do\n"
    "    if isCounted p || (!p.attributeName && !p.eqWellDefined) then\n"
    "      count := count + 1\n"
    "  return some count"
)
RIVAL_PARTIAL = _swap(_BASE, _IMPL, _PARTIAL_IMPL)

# --- COUNT-EVERYTHING: return the total number of decorations. ----------------
# Correct only when every decoration is argument-consuming; diverges on any
# attribute-bound or non-sentinel decoration.
_COUNTALL_IMPL = (
    "  if patchings.isEmpty then\n"
    "    return some 0\n"
    "  return some patchings.length"
)
RIVAL_COUNTALL = _swap(_BASE, _IMPL, _COUNTALL_IMPL)

# --- OFF-BY-ONE: drop the first decoration from the count. --------------------
# Correct on every input whose first decoration is NOT argument-consuming;
# undercounts by one when the first decoration is argument-consuming.
_SKIPFIRST_IMPL = (
    "  if patchings.isEmpty then\n"
    "    return some 0\n"
    "  let mut count : Nat := 0\n"
    "  for p in patchings.drop 1 do\n"
    "    if isCounted p then\n"
    "      count := count + 1\n"
    "  return some count"
)
RIVAL_SKIPFIRST = _swap(_BASE, _IMPL, _SKIPFIRST_IMPL)


# ---- witnesses (each checked: elaborates vs rival, fails vs frozen) ----------
_P = "problem_spec_num_mock_patch_args"
_I = "implementation_num_mock_patch_args"

# input: non-attribute, non-sentinel, ambiguous equality. Spec = some 0.
# totality rival aborts -> none; partial rival over-counts -> some 1.
_WIT_AMBIG = (
    f"example : ¬ {_P}\n"
    "    [ { attributeName := false, isSentinel := false, eqWellDefined := false } ]\n"
    f"    ({_I}\n"
    "      [ { attributeName := false, isSentinel := false, eqWellDefined := false } ]) := by\n"
    f"  unfold {_P} {_I}\n"
    "  decide\n"
)

# input: attribute-bound (never counted). Spec = some 0; count-everything -> some 1.
_WIT_ATTR = (
    f"example : ¬ {_P}\n"
    "    [ { attributeName := true, isSentinel := false, eqWellDefined := true } ]\n"
    f"    ({_I}\n"
    "      [ { attributeName := true, isSentinel := false, eqWellDefined := true } ]) := by\n"
    f"  unfold {_P} {_I}\n"
    "  decide\n"
)

# input: single argument-consuming decoration. Spec = some 1; skip-first -> some 0.
_WIT_FIRST = (
    f"example : ¬ {_P}\n"
    "    [ { attributeName := false, isSentinel := true, eqWellDefined := true } ]\n"
    f"    ({_I}\n"
    "      [ { attributeName := false, isSentinel := true, eqWellDefined := true } ]) := by\n"
    f"  unfold {_P} {_I}\n"
    "  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness)
    # =====================================================================
    {
        "id": "pos-cheap-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CHEAP,
        "rationale": "honest cheapest implementation: return the GROUNDED fold "
        "`some ((patchings.filter isCounted).length)` directly. The fold is fully "
        "unfolded over the input — not an opaque answer key — so this is a faithful "
        "one-liner that MUST satisfy `result = some ((patchings.filter isCounted)."
        "length)`; if it cannot, the postcondition is SPEC-TOO-STRONG. Proof: after "
        "unfolding both defs the two sides are definitionally equal, so `rfl` closes "
        "(the `correct_` statement is kept byte-identical).",
    },
    {
        "id": "pos-arith-accumulate",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_ARITH,
        "rationale": "structurally-different CORRECT implementation: replace the "
        "if-increment with an arithmetic accumulate `count + (if isCounted p then 1 "
        "else 0)`. Same value on every input, so `result = some ((patchings.filter "
        "isCounted).length)` still holds; must verify (else SPEC-TOO-STRONG). "
        "Re-proved because the reshaped loop body desugars differently: the frozen "
        "Route-B helper is restated over the arithmetic body (its own statement "
        "changes; it stays in the frozen declaration set, and the `correct_` "
        "obligation statement is byte-identical).",
    },

    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-allkinds",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "the obligation is discharged by `decide` at a representative "
        "reporting-shaped input (one argument-consuming decoration, one whose "
        "equality truth value is ambiguous, one attribute-bound), then the frozen "
        "obligation is closed verbatim. Verifies (else the behavior is unsatisfiable "
        "at the normal input — the analogue of PRECOND-TOO-STRONG). Nothing is "
        "assumed: no new declaration, the `correct_` statement is byte-identical, "
        "and the ground instance is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "raise-on-ambiguous-eq-totality",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_TOTALITY,
        "refinement": "this IS the pre-existing behavior: classifying a decoration "
        "by comparing its replacement for equality against each sentinel default "
        "aborts the whole computation when that replacement's equality truth value "
        "is ambiguous. The F2P collects exactly such a decoration; the abort fires "
        "at collection time, so the F2P test errors instead of passing — it does NOT "
        "resolve (it is the very failure the fix removes).",
        "rationale": "REJECT from (P-total): the result must be `some _` on EVERY "
        "input, but on a non-attribute decoration with an ambiguous equality truth "
        "value this rival returns `none`. control-flow-effect — an abort invisible "
        "to the value count, caught because the spec admits no `none`.",
        "witness": _WIT_AMBIG,
    },
    {
        "id": "partial-ambiguous-eq-counts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_PARTIAL,
        "refinement": "a faithful patch deciding membership by guarded equality "
        "(treat any uncomparable replacement as if it matched) would COUNT the "
        "ambiguous-equality replacement as argument-consuming; the fixture machinery "
        "would then expect the runner to supply an argument for a decoration that "
        "does not consume one, breaking the F2P decoration — it would NOT resolve.",
        "rationale": "REJECT from (P-count): `isCounted` counts a decoration only "
        "when it does not bind a named attribute AND its replacement is a sentinel "
        "default, so incrementing on an ambiguous-equality non-sentinel decoration "
        "over-counts. partial-domain: correct without such a decoration, diverges "
        "with one.",
        "witness": _WIT_AMBIG,
    },
    {
        "id": "count-everything",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_COUNTALL,
        "refinement": "counting every decoration regardless of kind counts "
        "attribute-bound and non-sentinel decorations as argument-consuming, so the "
        "fixture machinery expects the runner to supply arguments it must not; the "
        "P2P decoration tests assert specific argument counts and would get the "
        "wrong count and FAIL — it would NOT resolve.",
        "rationale": "REJECT from (P-count): `patchings.length` != `(patchings.filter "
        "isCounted).length` whenever any decoration is not argument-consuming. "
        "partial-domain: correct only when every decoration is argument-consuming.",
        "witness": _WIT_ATTR,
    },
    {
        "id": "skip-first-decoration",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_SKIPFIRST,
        "refinement": "an off-by-one that drops the first decoration undercounts "
        "whenever the first decoration is argument-consuming; a singly-decorated "
        "function would then report zero consumed arguments, so the runner would "
        "try to inject the replaced argument as a fixture and the test would ERROR — "
        "it would NOT resolve.",
        "rationale": "REJECT from (P-count): counting over `patchings.drop 1` yields "
        "`((patchings.drop 1).filter isCounted).length` != the full count whenever "
        "the first decoration is argument-consuming. partial-domain: the boundary "
        "(first) element.",
        "witness": _WIT_FIRST,
    },
]
