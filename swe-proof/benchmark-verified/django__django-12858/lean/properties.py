"""properties.py — G-PBT falsification battery for django__django-12858 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect="reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior). A single relation-spanning ordering
entry is validated by walking its name segments in order, starting from the
originating model with no field resolved yet. The machinery is taken as
universally-quantified parameters:

  getField    : Model → String → Option Field   -- resolve a segment to a field
  isRelation  : Field → Bool                     -- does a field relate onward
  descend     : Field → Model                    -- the related model
  hasTransform: Field → String → Bool            -- names a transform of a field
  hasLookup   : Field → String → Bool            -- names a registered lookup

  orderingFieldCheck  (getField isRelation descend hasTransform hasLookup)
                      (start : Model) (parts : List String) : Bool
      result = walkReported … none (some start) parts

where ``walkReported`` folds the per-segment decision ``reportSegment`` across
the segments with ``||`` (the whole entry is reported iff ANY segment is), each
resolved relation segment descending the context and each resolved non-relation
segment exhausting it, and ``reportSegment fld part`` = report exactly when
there is no preceding resolved field (``fld = none``), OR the segment is neither
a transform nor a registered lookup of the preceding field.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini battery's mandatory
    frame-mutation rival writes into a read-only ``Acc(…,1/2)`` input to prove
    the store is rejected for insufficient permission. Lean is referentially
    transparent: the inputs carry no heap permission, there is no read-only
    half-permission to overwrite and no aliasing to exploit. This class has no
    expressible instance here and no substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: it equates
    the result to ``walkReported …`` fully spelled out over the input segments
    and machinery (a ``pure``-region fold), and the bundle declares no
    ``opaque``/``axiom``, so there is no answer key an implementation could echo
    without doing the walk.

  * PARTIAL-DOMAIN / VALUE — APPLIES. The nagini per-path decision oracle
    ``flag_path(reached, value, compare)`` becomes ``reportSegment`` over the
    (fld, hasTransform, hasLookup) it observes; the nagini partial-domain rivals
    port to rivals that drop one accept-conjunct (the lookup conjunct — the
    leg's prepatch — or the transform conjunct), that flip the no-field-resolved
    guard, or that forget the ``||`` accumulation across segments (a near-miss
    reporting only the last unresolved segment).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``rw [loop_is_foldl …,
foldl_step_eq_walk …]``) is tuned to the frozen imperative form — so a rejection
alone attributes nothing to the spec. Every ``expect="reject"`` case therefore
carries a Lean snippet proving the rival CONTRADICTS the spec at one concrete
input. The opaque carriers ``Model``/``Field`` are instantiated at concrete
``decide``-able types (``Unit`` / ``String``) with the machinery given as small
literal lambdas, so the whole ``Id.run do`` walk evaluates. Each was checked to
hold of its rival and to FAIL on the frozen solution (so it discriminates rather
than asserting a tautology).

BINDER / POINT SPREAD. The four reject witnesses move every machinery binder the
walk depends on rather than fixing all at one convenient point:
  * ``parts`` varies over length and content
    (``["test","isnull"]`` / ``["test","lower"]`` / ``["bogus"]`` /
    ``["rel","bad","isnull"]``);
  * ``getField`` ranges over one that resolves the leading segment, one that
    resolves nothing, and one keyed to the model context (resolving a segment in
    the origin model but not in the descended one);
  * ``isRelation`` is false in three witnesses and TRUE in the fourth, which is
    the only one to exercise ``descend`` and the multi-segment ``||`` fold;
  * ``hasTransform`` is TRUE at the divergent point of the drop-transform rival
    and false elsewhere; ``hasLookup`` is TRUE at the drop-lookup rival's
    divergent point (the F2P ``isnull`` scenario) and false elsewhere;
  * ``descend`` and the origin ``start`` are varied by the near-miss witness,
    which instantiates the opaque ``Model`` at ``Bool`` (origin ``false``,
    descended model ``true``) so that ``descend`` genuinely routes to a DISTINCT
    model — a segment that resolves in the origin fails to resolve after the
    descent, making ``descend`` load-bearing rather than a spectator. The other
    three witnesses take ``Model := Unit`` (one value), so ``start``/``descend``
    are exercised for value only through the near-miss.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references are all
universally-quantified parameters (no consumed callee axiom), so there is no
axiom-soundness / axiom-containment obligation to probe here (that lane belongs
to G-AX in any case).
"""
from pathlib import Path

INSTANCE = "django__django-12858"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside one region and is unique in the file.

# The per-segment report decision, spelled once for the unresolved branch and
# once for the context-exhausted branch. This whole block is inside the impl
# region; the reject rivals rewrite it.
_DECISION = (
    "      | none =>\n"
    "        -- Unresolved: report unless the segment is a transform or a registered\n"
    "        -- lookup of the preceding resolved field.\n"
    "        if reportSegment hasTransform hasLookup fld part then\n"
    "          err := true\n"
    "    | none =>\n"
    "      -- Context exhausted: same report decision against the preceding field.\n"
    "      if reportSegment hasTransform hasLookup fld part then\n"
    "        err := true\n"
)

# The full imperative implementation body (signature tail through the return).
# The soundness positive replaces this with a structurally different but correct
# shape (direct recursion), which needs its own proof.
_IMPL_TAIL = (
    "    (start : Model) (parts : List String) : Bool := Id.run do\n"
    "  -- Walk the entry segment by segment from the originating model, tracking the\n"
    "  -- last resolved field and the current (possibly exhausted) model context.\n"
    "  let mut fld : Option Field := none\n"
    "  let mut ctx : Option Model := some start\n"
    "  let mut err : Bool := false\n"
    "  for part in parts do\n"
    "    match ctx with\n"
    "    | some m =>\n"
    "      match getField m part with\n"
    "      | some f =>\n"
    "        -- Resolved: descend into the related model if this field is a relation,\n"
    "        -- otherwise the context is exhausted.\n"
    "        fld := some f\n"
    "        ctx := if isRelation f then some (descend f) else none\n"
    "      | none =>\n"
    "        -- Unresolved: report unless the segment is a transform or a registered\n"
    "        -- lookup of the preceding resolved field.\n"
    "        if reportSegment hasTransform hasLookup fld part then\n"
    "          err := true\n"
    "    | none =>\n"
    "      -- Context exhausted: same report decision against the preceding field.\n"
    "      if reportSegment hasTransform hasLookup fld part then\n"
    "        err := true\n"
    "  return err\n"
)

# ---------------------------------------------------------------------------
# Reject rivals: each rewrites _DECISION with a wrong per-segment decision.

# R1 — drop the registered-lookup accept conjunct (the leg's PREPATCH): report
# unless the segment is a transform of the preceding field. A lookup-only
# segment (the F2P `isnull`) is wrongly reported.
_R1_DROP_LOOKUP = _swap(
    _BASE, _DECISION,
    "      | none =>\n"
    "        -- Report unless the segment is a transform of the preceding field\n"
    "        -- (a registered lookup is NOT spared here).\n"
    "        let report : Bool := match fld with\n"
    "          | none => true\n"
    "          | some f => !hasTransform f part\n"
    "        if report then\n"
    "          err := true\n"
    "    | none =>\n"
    "      let report : Bool := match fld with\n"
    "        | none => true\n"
    "        | some f => !hasTransform f part\n"
    "      if report then\n"
    "        err := true\n",
)

# R2 — drop the transform accept conjunct: report unless the segment is a
# registered lookup of the preceding field. A transform-only segment is wrongly
# reported.
_R2_DROP_TRANSFORM = _swap(
    _BASE, _DECISION,
    "      | none =>\n"
    "        -- Report unless the segment is a registered lookup of the preceding\n"
    "        -- field (a transform is NOT spared here).\n"
    "        let report : Bool := match fld with\n"
    "          | none => true\n"
    "          | some f => !hasLookup f part\n"
    "        if report then\n"
    "          err := true\n"
    "    | none =>\n"
    "      let report : Bool := match fld with\n"
    "        | none => true\n"
    "        | some f => !hasLookup f part\n"
    "      if report then\n"
    "        err := true\n",
)

# R3 — flip the no-field-resolved guard: when NO field has been resolved yet,
# accept instead of report. A leading segment that fails to resolve is silently
# accepted.
_R3_NOFIELD_ACCEPTS = _swap(
    _BASE, _DECISION,
    "      | none =>\n"
    "        -- Accept when no field was resolved yet (wrong: should report).\n"
    "        let report : Bool := match fld with\n"
    "          | none => false\n"
    "          | some f => (!hasTransform f part) && (!hasLookup f part)\n"
    "        if report then\n"
    "          err := true\n"
    "    | none =>\n"
    "      let report : Bool := match fld with\n"
    "        | none => false\n"
    "        | some f => (!hasTransform f part) && (!hasLookup f part)\n"
    "      if report then\n"
    "        err := true\n",
)

# R4 — near-miss: forget the accumulation across segments. `err` is ASSIGNED the
# last unresolved segment's decision rather than OR-ed in, so the entry is
# reported iff its LAST unresolved segment is reported, dropping an earlier
# reported segment.
_R4_LAST_ONLY = _swap(
    _BASE, _DECISION,
    "      | none =>\n"
    "        -- Near-miss: overwrite `err` with this segment's decision instead of\n"
    "        -- accumulating, forgetting any earlier reported segment.\n"
    "        err := reportSegment hasTransform hasLookup fld part\n"
    "    | none =>\n"
    "      err := reportSegment hasTransform hasLookup fld part\n",
)


# ---------------------------------------------------------------------------
# Soundness positive: a structurally different but CORRECT implementation —
# direct recursion via the reference walk instead of the imperative accumulator
# loop. Same result on every input by definition, so the postcondition holds by
# `rfl`. The frozen proof region carries loop-desugaring helper lemmas keyed to
# the imperative form; those no longer typecheck against a recursion impl, so the
# WHOLE proof-region content is replaced with just the `correct_*` obligation
# (statement byte-identical) closed by the honest, sorry-free `rfl`. Removing
# now-inapplicable helper lemmas is in scope (no NEW theorem/lemma is added).

# The frozen theorem statement, verbatim, so the replacement keeps it byte-for-byte.
_THEOREM_STMT = (
    "theorem correct_orderingFieldCheck :\n"
    "    ∀ {Model Field : Type}\n"
    "      (getField : Model → String → Option Field)\n"
    "      (isRelation : Field → Bool) (descend : Field → Model)\n"
    "      (hasTransform hasLookup : Field → String → Bool)\n"
    "      (start : Model) (parts : List String),\n"
    "      problem_spec_orderingFieldCheck getField isRelation descend hasTransform hasLookup\n"
    "          start parts\n"
    "        (implementation_orderingFieldCheck getField isRelation descend hasTransform hasLookup\n"
    "          start parts) := by\n"
)


def _replace_proof_region(src, new_body):
    """Replace the entire proof-region content with `new_body` (markers kept)."""
    head = "-- proof-start\n"
    tail = "-- proof-end"
    lo = src.index(head) + len(head)
    hi = src.index(tail)
    return src[:lo] + new_body + src[hi:]


_POS_DIRECT = _replace_proof_region(
    _swap(
        _BASE, _IMPL_TAIL,
        "    (start : Model) (parts : List String) : Bool :=\n"
        "  -- Structurally different correct shape: walk the entry by direct\n"
        "  -- recursion from the originating model with no field resolved yet,\n"
        "  -- rather than an imperative accumulator loop.\n"
        "  walkReported getField isRelation descend hasTransform hasLookup\n"
        "    none (some start) parts\n",
    ),
    _THEOREM_STMT
    + "  intro Model Field getField isRelation descend hasTransform hasLookup start parts\n"
    + "  rfl\n",
)


# ---------------------------------------------------------------------------
# Admissibility: confirm the modeled behavior is SATISFIABLE at the F2P-shaped
# input (a field reached, then a registered-lookup-not-transform segment, which
# the walk ACCEPTS). The frozen theorem carries NO precondition binder (the
# behavior is total, `∀` is unguarded), so the nagini precondition-admission
# probe has no binder to attack; the honest analogue is to discharge the spec
# predicate at that ground input by evaluation, inside the proof region, before
# closing the frozen obligation verbatim.
_ADMISS = _swap(
    _BASE,
    "  intro Model Field getField isRelation descend hasTransform hasLookup start parts\n"
    "  unfold problem_spec_orderingFieldCheck\n",
    "  intro Model Field getField isRelation descend hasTransform hasLookup start parts\n"
    "  -- admissibility: the modeled behavior is SATISFIABLE at the F2P-shaped\n"
    "  -- input — a field reached, then a registered-lookup-not-transform segment,\n"
    "  -- which the walk ACCEPTS (reports false). Discharged by evaluation, then\n"
    "  -- the frozen obligation is closed verbatim.\n"
    "  have _ground :\n"
    "      problem_spec_orderingFieldCheck\n"
    "        (fun (_ : Unit) (s : String) => if s = \"test\" then some \"test\" else none)\n"
    "        (fun _ => false) (fun _ => ()) (fun _ _ => false)\n"
    "        (fun _ part => part == \"isnull\") () [\"test\", \"isnull\"]\n"
    "        (implementation_orderingFieldCheck\n"
    "          (fun (_ : Unit) (s : String) => if s = \"test\" then some \"test\" else none)\n"
    "          (fun _ => false) (fun _ => ()) (fun _ _ => false)\n"
    "          (fun _ part => part == \"isnull\") () [\"test\", \"isnull\"]) := by\n"
    "    unfold problem_spec_orderingFieldCheck\n"
    "    decide\n"
    "  unfold problem_spec_orderingFieldCheck\n",
)


# ---------------------------------------------------------------------------
# Witness helpers. Each states the spec predicate directly at a concrete
# instantiation of the opaque carriers (Model := Unit or Bool, Field := String)
# with literal-lambda machinery, so the whole walk evaluates under `decide`.

def _witness(gf, isrel, desc, ht, hl, start, parts, note):
    inst = (f"{gf} {isrel} {desc}\n"
            f"      {ht} {hl} {start} {parts}")
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_orderingFieldCheck\n"
        f"    {inst}\n"
        f"    (implementation_orderingFieldCheck\n"
        f"      {inst}) := by\n"
        f"  unfold problem_spec_orderingFieldCheck implementation_orderingFieldCheck\n"
        f"  decide\n"
    )


_DESC_U = "(fun _ => ())"
_GF_TEST = '(fun (_ : Unit) (s : String) => if s = "test" then some "test" else none)'
_GF_NONE = "(fun (_ : Unit) (_ : String) => (none : Option String))"
_ISREL_F = "(fun (_ : String) => false)"
_HT_NONE = "(fun (_ : String) (_ : String) => false)"
_HT_LOWER = '(fun (_ : String) (part : String) => part == "lower")'
_HL_NONE = "(fun (_ : String) (_ : String) => false)"
_HL_ISNULL = '(fun (_ : String) (part : String) => part == "isnull")'

# Multi-model machinery for the near-miss witness (Model := Bool). The origin
# model is `false`; `rel` resolves there and is a relation whose `descend` routes
# to a DISTINCT model `true`. `mid` resolves in the origin but NOT in the
# descended model, so descending is exactly what leaves `mid` unresolved (hence
# reported); `isnull` is a registered lookup of `rel` and is accepted last. This
# makes `descend` and the origin `start` load-bearing: were `descend` to route
# back to `false`, `mid` would resolve and the walk's outcome would change.
_GF_BOOL = ('(fun (m : Bool) (s : String) => '
            'if m = false ∧ s = "rel" then some "rel" '
            'else if m = false ∧ s = "mid" then some "mid" else none)')
_ISREL_REL = '(fun (f : String) => f == "rel")'
_DESC_TRUE = "(fun _ => true)"
_HL_REL_ISNULL = '(fun (f : String) (part : String) => f == "rel" ∧ part == "isnull")'


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS positive — a structurally different but CORRECT implementation
    # that MUST verify. If a faithful correct implementation cannot satisfy the
    # frozen obligation, the spec is SPEC-TOO-STRONG. Keeps the theorem
    # statement byte-identical and re-proves it for the new shape; introduces no
    # helper lemma, axiom, or assumption token.
    # =====================================================================
    {
        "id": "pos-direct-recursion",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the report-flag is computed by direct recursion over the reference "
            "walk instead of the imperative accumulator loop; observationally it "
            "IS `walkReported … none (some start) parts` on every input, so "
            "`result = walkReported …` holds by `rfl`. Must verify, else the "
            "postcondition is SPEC-TOO-STRONG. Re-proved because the frozen "
            "script (`rw [loop_is_foldl …, foldl_step_eq_walk …]`) is tuned to "
            "the imperative form and no longer applies; the new body is closed by "
            "`rfl` with no new declaration, no axiom, no sorry, and the "
            "`theorem correct_orderingFieldCheck` statement byte-identical."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the modeled behavior is SATISFIABLE (non-vacuous) at the
    # F2P-shaped input, not only provable in the abstract. The frozen theorem
    # carries no precondition hypothesis, so the honest analogue of the nagini
    # precondition-admission probe is to discharge the spec at the ground F2P
    # input by evaluation, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-f2p-lookup-accepted",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation is discharged at the ground F2P input (a field "
            "reached, then a registered-lookup-not-transform segment — the "
            "`isnull` scenario) by `decide`, confirming the walk ACCEPTS it "
            "(reports false), then the frozen obligation is closed verbatim. "
            "Verifies, else the modeled behavior would be unsatisfiable at the "
            "very input the F2P exercises (the analogue of PRECOND-TOO-STRONG). "
            "Nothing is assumed: no new declaration, the theorem statement is "
            "byte-identical, and the ground instance is a `have` inside the "
            "existing tactic body."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P (so a verifying
    # rival is a true verify-does-not-imply-resolve break, not an artifact), and
    # (b) a refutation witness pinning the violation at one concrete input,
    # checked to hold of the rival and FAIL on gold.
    # =====================================================================
    {
        "id": "weak-drop-lookup-accept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R1_DROP_LOOKUP,
        # port of nagini's partial-domain-drop-compare-op (the leg's prepatch).
        "refinement": (
            "reporting a segment that is a registered LOOKUP but not a transform "
            "of the preceding field is exactly the pre-existing (unfixed) "
            "behavior: the F2P entry `test__isnull` — where `isnull` is a "
            "registered lookup — is wrongly reported, so the check reports an "
            "error where none should be raised and the F2P "
            "lookup-not-transform test FAILS. It would NOT resolve; this is the "
            "leg's prepatch."
        ),
        "rationale": (
            "REJECT from `result = walkReported …`: on a leading resolved field "
            "followed by a lookup-only segment the spec's `reportSegment` returns "
            "false (the lookup is spared) but the rival returns true. Refuted at "
            "the `isnull` point with `hasLookup` TRUE there — the only rival that "
            "diverges on the lookup conjunct."
        ),
        "witness": _witness(
            _GF_TEST, _ISREL_F, _DESC_U, _HT_NONE, _HL_ISNULL,
            "()", '["test", "isnull"]',
            "Refuted at the F2P lookup-only segment: a registered lookup of the "
            "preceding resolved field must be ACCEPTED, so hasLookup is the "
            "decisive binder here.",
        ),
    },
    {
        "id": "weak-drop-transform-accept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R2_DROP_TRANSFORM,
        "refinement": (
            "reporting a segment that is a TRANSFORM but not a registered lookup "
            "of the preceding field newly breaks the pre-existing acceptance of "
            "transform ordering directives: a registered transform segment must "
            "be accepted (it is a legitimate ordering directive), and the P2P "
            "registered-transform/lookup acceptance test asserts exactly that. A "
            "faithful patch matching this rival would regress that behavior, so "
            "it would NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = walkReported …`: on a leading resolved field "
            "followed by a transform-only segment the spec's `reportSegment` "
            "returns false (the transform is spared) but the rival returns true. "
            "Refuted at a `lower` point with `hasTransform` TRUE there — the only "
            "rival that diverges on the transform conjunct, so this witness moves "
            "the `hasTransform` binder off the value the others hold it at."
        ),
        "witness": _witness(
            _GF_TEST, _ISREL_F, _DESC_U, _HT_LOWER, _HL_NONE,
            "()", '["test", "lower"]',
            "Refuted at a transform-only segment: a registered transform of the "
            "preceding resolved field must be ACCEPTED, so hasTransform is the "
            "decisive binder here.",
        ),
    },
    {
        "id": "weak-nofield-accepts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R3_NOFIELD_ACCEPTS,
        # port of nagini's partial-domain-drop-reached-field.
        "refinement": (
            "accepting an unresolved segment when NO preceding field has been "
            "resolved suppresses the report for a genuinely nonexistent field — "
            "an entry whose leading segment does not resolve is silently "
            "accepted. The P2P nonexistent-field reporting tests assert exactly "
            "that such an entry IS reported, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = walkReported …`: with no field resolved "
            "(`fld = none`) the spec's `reportSegment` returns true but the rival "
            "returns false. Refuted at a single unresolvable segment, exercising "
            "the `getField`-resolves-nothing regime the other witnesses do not."
        ),
        "witness": _witness(
            _GF_NONE, _ISREL_F, _DESC_U, _HT_NONE, _HL_NONE,
            "()", '["bogus"]',
            "Refuted where no field is ever resolved: an unresolved leading "
            "segment must be REPORTED, so the fld=none guard is decisive.",
        ),
    },
    {
        "id": "weak-last-segment-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R4_LAST_ONLY,
        # port of nagini's partial-domain-last-path-negated (a near-miss that
        # forgets accumulation across segments).
        "refinement": (
            "reporting an entry by its LAST unresolved segment alone, rather than "
            "by whether ANY segment is reported, drops a genuinely reported "
            "earlier segment whenever a later segment happens to be accepted. A "
            "faithful patch that mis-accumulated the per-segment decision this "
            "way would silence a real nonexistent/related-field report that "
            "precedes an accepted lookup/transform in the same entry, breaking "
            "the P2P entry-level reporting tests, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = walkReported …`, which OR-folds the per-"
            "segment decisions: on an entry whose middle segment is reported but "
            "whose final segment is accepted, the spec reports true (some segment "
            "is reported) while the rival returns the last segment's decision, "
            "false. This is the only witness instantiated over a MULTI-model "
            "carrier (Model := Bool): `isRelation` is TRUE on the leading "
            "segment, whose `descend` routes to a DISTINCT model where the middle "
            "segment no longer resolves (and is therefore reported), so it moves "
            "the `isRelation`, `descend`, and origin `start` binders together "
            "with the `||`-accumulation clause. Were `descend` to route back to "
            "the origin, the middle segment would resolve and the walk's outcome "
            "would change — so `descend` is load-bearing here, not a spectator."
        ),
        "witness": _witness(
            _GF_BOOL, _ISREL_REL, _DESC_TRUE, _HT_NONE, _HL_REL_ISNULL,
            "false", '["rel", "mid", "isnull"]',
            "Refuted on a multi-model entry: `rel` resolves in the origin and "
            "descends to a DISTINCT model; `mid` resolves in the origin but NOT "
            "the descended model, so it is unresolved there and reported; "
            "`isnull` is a registered lookup of `rel`, accepted last. The entry "
            "must be reported because SOME segment is, so the ||-accumulation "
            "across segments — and the descent that makes `mid` unresolved — are "
            "both decisive.",
        ),
    },
]


# No consumed callee axiom and no axiomatized A-reference: the model machinery
# (getField/isRelation/descend/hasTransform/hasLookup) is universally quantified,
# so there is no axiom-soundness / axiom-containment obligation to probe. That
# lane is G-AX's job in any case.
AXIOM_TESTS = []
