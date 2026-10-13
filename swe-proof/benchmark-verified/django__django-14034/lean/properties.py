"""properties.py — G-PBT falsification battery for django__django-14034 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for a case that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds and every ``theorem correct_<name>`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect="reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` HOLDS of the rival while FAILING on
the frozen solution).

This is a PORT of the nagini falsification battery for the same instance; the
nagini ``properties.py`` is the design document. The nagini sibling defends a
VOID mutating operation over a fractional-permission carrier; this bundle models
only the purely functional core of the same decision — a total function from the
four attribute inputs to the four attribute-decision outputs — so the carrier is
narrower and several nagini cases have no counterpart here (see below).

DEFENDED SURFACE (one total function over a four-input domain):

  requiredAttrs
      (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result

  where the guard is ``widgetUseReq && field.required && formUseReq`` and the
  per-subwidget branch is entered when the field exposes the per-subfield-
  optional switch, that switch is off, and the widget is a composite of
  subwidgets (``field.hasRequireAllFields && !field.requireAllFields &&
  field.isMultiWidget``). The postcondition is a four-way conjunction:

    * ``result.parentDisabled = field.disabled`` — the disabled marker on the
      field's own widget, an INDEPENDENT decision pinned by ``field.disabled``.
    * ``result.perSubBranch = (guard && subBranch)`` — whether the per-subwidget
      placement branch ran.
    * ``result.parentRequired = (guard && !subBranch)`` — a required marker on
      the field's own widget: set exactly when the guard holds and the
      per-subwidget branch did NOT run.
    * ``result.subwidgetRequired = (if guard && subBranch then field.subPairs.map
      (fun p => p.1 && p.2) else [])`` — one required flag per subwidget, each
      the conjunction of that subwidget's own "expose a marker" predicate and its
      subfield's required flag, in order; empty unless the per-subwidget branch
      ran.

  The BEHAVIOURAL DISCRIMINATOR (the ticket): when the field is a required
  composite whose subfields are individually optional, the required markers are
  placed PER SUBWIDGET (each ``subUseReq && subRequired``) and the field's own
  widget receives NO aggregate required marker. The pre-fix behavior instead set
  the aggregate marker unconditionally under the guard, so EVERY subwidget
  rendered required. The F2P observable asserts the first (required) subwidget
  carries the marker and the second (optional) one does not.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY: the read-only constituent inputs are held at
    half permission and a rival that self-assigns one is rejected for
    insufficient permission. Lean is referentially transparent: the inputs are
    plain immutable values (``Bool`` / ``List (Bool × Bool)``), there is no
    half-permission to violate and no aliasing to exploit, so this class has NO
    expressible instance here. No substitute is fabricated for it. (Ported from
    nagini case 3, ``frame-mutation-write-field_required``.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Every clause is GROUNDED in the inputs
    (booleans combined with ``&&`` / ``!`` and a list ``map``, fully unfolded);
    the bundle declares no ``opaque`` / ``axiom``, so there is no answer key an
    implementation could echo. The honest analogue is the cheapest-correct
    POSITIVE CONTROL below.

  * AGGREGATE-IN-REGIME-A (the pre-patch bug) — APPLIES, load-bearing. Ported
    from nagini case 4.
  * PARTIAL-DOMAIN / drop the subfield's own required flag — APPLIES. Ported
    from nagini case 5.
  * REGIME-B aggregate miss — APPLIES. Ported from nagini case 6.
  * DISABLED-slot drop (frame exactness) — APPLIES. Ported from nagini case 7.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
``decide``-able concrete input; each was built against its rival (ELABORATES:
the rival provably contradicts the spec there) and against the frozen solution
(FAILS: ``decide`` proves the negation false, so it is a real discriminator, not
a tautology). All witnesses use only literal inputs, so none binds a hypothesis
and none can be inconsistent.

BINDER COVERAGE. The spec's input binders (``widgetUseReq``, ``formUseReq``,
``field`` = the FieldInfo bundle of six sub-inputs) are exercised across the
reject witnesses at FOUR distinct input points:
  * per-subwidget regime with a subfield whose own required flag is TRUE —
    ``field.subPairs`` at ``[(true, true)]`` (aggregate-regime-a);
  * per-subwidget regime with a subfield whose own required flag is FALSE while
    its widget predicate is TRUE — ``field.subPairs`` at ``[(true, false)]``
    (partial-domain), the F2P optional-subfield sub-domain;
  * the ordinary (non-composite) regime — ``hasRequireAllFields`` /
    ``isMultiWidget`` FALSE, ``subPairs`` empty (regime-b);
  * a disabled, guard-off field — ``field.disabled`` TRUE with
    ``field.required`` / ``widgetUseReq`` / ``formUseReq`` FALSE (disabled-drop),
    which moves ``field.disabled`` and the guard inputs off the value the other
    witnesses hold them at.
``pts`` = 4 distinct input points.

PORT LEDGER (nagini case -> lean disposition):
  1 pos-control-hoist-disabled-flip-branch  -> ported: pos-functional-form.
  2 admissibility-readonly-spine-and-init    -> ported: admiss-f2p-ground.
  3 frame-mutation-write-field_required      -> DROPPED, vacuous (see above).
  4 aggregate-in-regime-a-prepatch-bug       -> ported: reject-aggregate-regime-a.
  5 partial-domain-ignore-field_required     -> ported: reject-partial-domain.
  6 regime-b-drop-aggregate                  -> ported: reject-regime-b-drop.
  7 disabled-slot-drop                        -> ported: reject-disabled-drop.

AXIOM lane: EMPTY. The bundle declares no ``@ContractOnly`` / ``opaque`` /
``axiom`` (the per-widget "expose a required marker" predicate is a plain input
boolean, not a recomputed callee), so there is no axiom-soundness obligation for
the PBT axiom lane to re-discharge; that lane belongs to G-AX in any case.
Ported from nagini ``AXIOM_TESTS = []``.
"""
from pathlib import Path

INSTANCE = "django__django-14034"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (each unique inside Solution.lean; verified at load). The FULL
# impl-region body and the FULL frozen proof-region body, so every replacement
# lands entirely inside the region it means to edit.
# ---------------------------------------------------------------------------
_IMPL_GOLD = (
    "def implementation_requiredAttrs\n"
    "    (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result := Id.run do\n"
    "  let mut parentRequired := false\n"
    "  let mut parentDisabled := false\n"
    "  let mut subwidgetRequired : List Bool := []\n"
    "  let mut perSubBranch := false\n"
    "  if widgetUseReq && field.required && formUseReq then\n"
    "    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then\n"
    "      perSubBranch := true\n"
    "      for (su, sr) in field.subPairs do\n"
    "        subwidgetRequired := subwidgetRequired ++ [su && sr]\n"
    "    else\n"
    "      parentRequired := true\n"
    "  if field.disabled then\n"
    "    parentDisabled := true\n"
    "  return { parentRequired, parentDisabled, subwidgetRequired, perSubBranch }"
)

# The frozen proof region in full (helper lemmas + the correct_ theorem). The
# positive control reshapes the impl into a direct functional form for which
# `refine ⟨rfl, rfl, rfl, rfl⟩` closes, so it replaces the whole proof region
# (dropping the now-unneeded helper lemmas — a variant may drop declarations; it
# may not ADD any). The `correct_requiredAttrs` STATEMENT is reproduced
# byte-identically inside the replacement.
_PROOF_GOLD = (
    "theorem loop_fold_is_map (l : List (Bool × Bool)) (init : List Bool) :\n"
    "    l.foldl (fun acc p => acc ++ [p.1 && p.2]) init\n"
    "      = init ++ l.map (fun p => p.1 && p.2) := by\n"
    "  induction l generalizing init with\n"
    "  | nil => simp\n"
    "  | cons hd tl ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]\n"
    "\n"
    "theorem unfold_reduce (widgetUseReq formUseReq : Bool) (field : FieldInfo) :\n"
    "    implementation_requiredAttrs widgetUseReq formUseReq field =\n"
    "      { parentRequired :=\n"
    "          if widgetUseReq && field.required && formUseReq then\n"
    "            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget\n"
    "             then false else true)\n"
    "          else false,\n"
    "        parentDisabled := field.disabled,\n"
    "        subwidgetRequired :=\n"
    "          if widgetUseReq && field.required && formUseReq then\n"
    "            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget\n"
    "             then field.subPairs.foldl (fun acc p => acc ++ [p.1 && p.2]) []\n"
    "             else [])\n"
    "          else [],\n"
    "        perSubBranch :=\n"
    "          if widgetUseReq && field.required && formUseReq then\n"
    "            (if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget\n"
    "             then true else false)\n"
    "          else false } := by\n"
    "  simp only [implementation_requiredAttrs, Id.run, List.forIn_yield_eq_foldl]\n"
    "  split_ifs <;> simp_all <;> rfl\n"
    "\n"
    "theorem parentDisabled_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :\n"
    "    (implementation_requiredAttrs widgetUseReq formUseReq field).parentDisabled\n"
    "      = field.disabled := by\n"
    "  rw [unfold_reduce]\n"
    "\n"
    "theorem perSubBranch_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :\n"
    "    (implementation_requiredAttrs widgetUseReq formUseReq field).perSubBranch\n"
    "      = ((widgetUseReq && field.required && formUseReq)\n"
    "         && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)) := by\n"
    "  rw [unfold_reduce]\n"
    "  by_cases h1 : widgetUseReq && field.required && formUseReq = true <;>\n"
    "  by_cases h2 : field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget = true <;>\n"
    "  simp_all\n"
    "\n"
    "theorem parentRequired_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :\n"
    "    (implementation_requiredAttrs widgetUseReq formUseReq field).parentRequired\n"
    "      = ((widgetUseReq && field.required && formUseReq)\n"
    "         && (!(field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget))) := by\n"
    "  rw [unfold_reduce]\n"
    "  cases widgetUseReq && field.required && formUseReq <;>\n"
    "    cases field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget <;>\n"
    "    rfl\n"
    "\n"
    "theorem subwidget_eq (widgetUseReq formUseReq : Bool) (field : FieldInfo) :\n"
    "    (implementation_requiredAttrs widgetUseReq formUseReq field).subwidgetRequired\n"
    "      = (if (widgetUseReq && field.required && formUseReq)\n"
    "            && (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget)\n"
    "         then field.subPairs.map (fun p => p.1 && p.2)\n"
    "         else []) := by\n"
    "  rw [unfold_reduce]\n"
    "  simp only [loop_fold_is_map, List.nil_append]\n"
    "  by_cases hg : (widgetUseReq && field.required && formUseReq) = true <;>\n"
    "    by_cases hs : (field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget) = true <;>\n"
    "    simp [hg, hs]\n"
    "\n"
    "theorem correct_requiredAttrs :\n"
    "    ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),\n"
    "      problem_spec_requiredAttrs widgetUseReq formUseReq field\n"
    "        (implementation_requiredAttrs widgetUseReq formUseReq field) := by\n"
    "  intro widgetUseReq formUseReq field\n"
    "  refine ⟨?_, ?_, ?_, ?_⟩\n"
    "  · exact parentDisabled_eq widgetUseReq formUseReq field\n"
    "  · exact perSubBranch_eq widgetUseReq formUseReq field\n"
    "  · exact parentRequired_eq widgetUseReq formUseReq field\n"
    "  · exact subwidget_eq widgetUseReq formUseReq field"
)

# The exact frozen `correct_requiredAttrs` tactic-body opener, unique in the
# file. The admissibility case inserts a ground `have` immediately after it.
_INTRO_ANCHOR = "  intro widgetUseReq formUseReq field\n"

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"
assert _BASE.count(_INTRO_ANCHOR) == 1, "intro anchor drifted; update _INTRO_ANCHOR"


# ---------------------------------------------------------------------------
# (1) POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl.
# The mutable-accumulator `Id.run do` / `for` loop is replaced by a direct
# functional record whose fields are exactly the spec's own combinations. Same
# value on every input; the frozen tactic script (tuned to the loop form,
# `List.forIn_yield_eq_foldl` + the fold-is-map lemma) no longer applies, so the
# obligation is re-proved for the new shape by `refine ⟨rfl, rfl, rfl, rfl⟩`.
# The helper lemmas the loop proof needed become dead and are dropped (a variant
# may drop declarations, not add them); the `correct_requiredAttrs` STATEMENT is
# byte-identical and no new lemma/axiom/assumption token is introduced.
# ---------------------------------------------------------------------------
_IMPL_POS = (
    "def implementation_requiredAttrs\n"
    "    (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result :=\n"
    "  let guard := widgetUseReq && field.required && formUseReq\n"
    "  let subBranch :=\n"
    "    field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget\n"
    "  { parentRequired := guard && !subBranch,\n"
    "    parentDisabled := field.disabled,\n"
    "    subwidgetRequired :=\n"
    "      if guard && subBranch then field.subPairs.map (fun p => p.1 && p.2) else [],\n"
    "    perSubBranch := guard && subBranch }"
)
_PROOF_POS = (
    "theorem correct_requiredAttrs :\n"
    "    ∀ (widgetUseReq formUseReq : Bool) (field : FieldInfo),\n"
    "      problem_spec_requiredAttrs widgetUseReq formUseReq field\n"
    "        (implementation_requiredAttrs widgetUseReq formUseReq field) := by\n"
    "  intro widgetUseReq formUseReq field\n"
    "  refine ⟨rfl, rfl, rfl, rfl⟩"
)

# (2) ADMISSIBILITY — discharge the frozen obligation AND, inside the same
# tactic body, a ground instance at the F2P-shaped input (required composite,
# per-subfield-optional switch off, composite widget; two subwidgets, the first
# subfield required and the second optional). If that instance could not be
# discharged the modeled behavior would be unsatisfiable at exactly the input the
# F2P exercises — the analogue of PRECOND-TOO-STRONG. The frozen `∀` carries no
# precondition hypothesis (the behavior is total), so nagini's precondition-
# admission probe has no binder to attack; this is its honest analogue. Nothing
# is assumed: the STATEMENT is byte-identical and the ground fact is a `have`.
_GROUND_HAVE = (
    "  intro widgetUseReq formUseReq field\n"
    "  have _ground : problem_spec_requiredAttrs true true\n"
    "      { required := true, disabled := false, hasRequireAllFields := true,\n"
    "        requireAllFields := false, isMultiWidget := true,\n"
    "        subPairs := [(true, true), (true, false)] }\n"
    "      (implementation_requiredAttrs true true\n"
    "        { required := true, disabled := false, hasRequireAllFields := true,\n"
    "          requireAllFields := false, isMultiWidget := true,\n"
    "          subPairs := [(true, true), (true, false)] }) := by\n"
    "    unfold problem_spec_requiredAttrs implementation_requiredAttrs\n"
    "    decide\n"
)


# ---------------------------------------------------------------------------
# Rival impl regions (each a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical). Each rival ships the
# frozen proof unchanged, which no longer closes for the reshaped/wrong impl —
# hence the rival does NOT verify, and its `witness` supplies the discriminating
# counterexample the gate checks.
# ---------------------------------------------------------------------------

# (4) AGGREGATE-IN-REGIME-A (the pre-fix bug): under the guard, always set the
# aggregate required marker and never enter the per-subwidget branch.
_IMPL_AGGREGATE = (
    "def implementation_requiredAttrs\n"
    "    (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result := Id.run do\n"
    "  let mut parentRequired := false\n"
    "  let mut parentDisabled := false\n"
    "  let mut subwidgetRequired : List Bool := []\n"
    "  let mut perSubBranch := false\n"
    "  if widgetUseReq && field.required && formUseReq then\n"
    "    parentRequired := true\n"
    "  if field.disabled then\n"
    "    parentDisabled := true\n"
    "  return { parentRequired, parentDisabled, subwidgetRequired, perSubBranch }"
)

# (5) PARTIAL-DOMAIN: keep the per-subwidget branch but IGNORE the subfield's own
# required flag, writing `su` instead of `su && sr` per subwidget.
_IMPL_PARTIAL = (
    "def implementation_requiredAttrs\n"
    "    (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result := Id.run do\n"
    "  let mut parentRequired := false\n"
    "  let mut parentDisabled := false\n"
    "  let mut subwidgetRequired : List Bool := []\n"
    "  let mut perSubBranch := false\n"
    "  if widgetUseReq && field.required && formUseReq then\n"
    "    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then\n"
    "      perSubBranch := true\n"
    "      for (su, sr) in field.subPairs do\n"
    "        subwidgetRequired := subwidgetRequired ++ [su]\n"
    "    else\n"
    "      parentRequired := true\n"
    "  if field.disabled then\n"
    "    parentDisabled := true\n"
    "  return { parentRequired, parentDisabled, subwidgetRequired, perSubBranch }"
)

# (6) REGIME-B DROP: in the ordinary (non-composite) regime, drop the aggregate
# required marker (delete the `else parentRequired := true`).
_IMPL_REGIMEB = (
    "def implementation_requiredAttrs\n"
    "    (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result := Id.run do\n"
    "  let mut parentRequired := false\n"
    "  let mut parentDisabled := false\n"
    "  let mut subwidgetRequired : List Bool := []\n"
    "  let mut perSubBranch := false\n"
    "  if widgetUseReq && field.required && formUseReq then\n"
    "    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then\n"
    "      perSubBranch := true\n"
    "      for (su, sr) in field.subPairs do\n"
    "        subwidgetRequired := subwidgetRequired ++ [su && sr]\n"
    "  if field.disabled then\n"
    "    parentDisabled := true\n"
    "  return { parentRequired, parentDisabled, subwidgetRequired, perSubBranch }"
)

# (7) DISABLED DROP: get the required-marker placement exactly right but delete
# the disabled-marker block, leaving parentDisabled false even when the field is
# disabled.
_IMPL_NODISABLED = (
    "def implementation_requiredAttrs\n"
    "    (widgetUseReq formUseReq : Bool) (field : FieldInfo) : Result := Id.run do\n"
    "  let mut parentRequired := false\n"
    "  let mut parentDisabled := false\n"
    "  let mut subwidgetRequired : List Bool := []\n"
    "  let mut perSubBranch := false\n"
    "  if widgetUseReq && field.required && formUseReq then\n"
    "    if field.hasRequireAllFields && (!field.requireAllFields) && field.isMultiWidget then\n"
    "      perSubBranch := true\n"
    "      for (su, sr) in field.subPairs do\n"
    "        subwidgetRequired := subwidgetRequired ++ [su && sr]\n"
    "    else\n"
    "      parentRequired := true\n"
    "  return { parentRequired, parentDisabled, subwidgetRequired, perSubBranch }"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness). MUST verify, else SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-functional-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL_GOLD, _IMPL_POS),
                        _PROOF_GOLD, _PROOF_POS),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` / "
            "`for` loop and builds the `Result` directly, with each field spelled "
            "as the spec's own combination (`parentRequired := guard && !subBranch`, "
            "`subwidgetRequired := if guard && subBranch then subPairs.map (·.1 && "
            "·.2) else []`, `perSubBranch := guard && subBranch`, `parentDisabled := "
            "field.disabled`) must satisfy the four-way postcondition; if it cannot, "
            "the spec is SPEC-TOO-STRONG. Proof: after `intro` the four conjuncts are "
            "each definitionally the impl field, so `refine ⟨rfl, rfl, rfl, rfl⟩` "
            "closes. The loop-fold helper lemmas are now dead and dropped (a variant "
            "may drop declarations); the `correct_requiredAttrs` STATEMENT is "
            "byte-identical and no new lemma/axiom/assumption token is introduced. "
            "Verified with a real build."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY. MUST verify, else the spec is unsatisfiable at the F2P input.
    # =====================================================================
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _INTRO_ANCHOR, _GROUND_HAVE),
        "rationale": (
            "the frozen obligation is discharged UNCHANGED, and alongside it — as a "
            "`have` in the same tactic body — the spec predicate is discharged by "
            "`decide` at the F2P ground input: a required composite field whose "
            "per-subfield-optional switch is off and whose widget is composite, with "
            "two subwidgets whose predicates are both true and whose subfields are "
            "respectively required and optional (`subPairs := [(true, true), (true, "
            "false)]`), where the spec demands `subwidgetRequired = [true, false]`. If "
            "that ground instance could not be discharged the modeled behavior would "
            "be unsatisfiable at exactly the F2P input, the analogue of "
            "PRECOND-TOO-STRONG. The behavior is total so the frozen `∀` carries no "
            "precondition hypothesis for nagini's precondition-admission probe to "
            "attack; this is its honest analogue. Nothing is assumed: the STATEMENT is "
            "byte-identical and no new declaration/axiom/`sorry` appears. Verified "
            "with a real build."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) a refinement argument that its
    # faithful real patch would NOT resolve the F2P (so a verifying rival is a
    # true verify-does-not-imply-resolve break, not an artifact) and (b) a
    # refutation witness pinning the violation at one concrete input, checked to
    # HOLD of the rival and FAIL on gold.
    # =====================================================================
    {
        "id": "reject-aggregate-regime-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_AGGREGATE),
        "refinement": (
            "this is the pre-fix behavior: under the guard the aggregate required "
            "marker is placed on the field's own widget and the per-subwidget branch "
            "is never taken. For the F2P scenario (a required composite field with "
            "the per-subfield-optional switch off, rendered through a composite "
            "widget of two subwidgets) the aggregate marker makes BOTH subwidgets "
            "render required, including the optional second one. The F2P observable "
            "asserts the optional subwidget carries NO required marker, so the "
            "faithful pre-patch does NOT resolve — this IS the reported bug."
        ),
        "rationale": (
            "REJECT from the `subwidgetRequired` and `parentRequired` clauses jointly. "
            "In the per-subwidget regime the spec demands `perSubBranch = true`, "
            "`parentRequired = false`, and `subwidgetRequired = subPairs.map (·.1 && "
            "·.2)`; this rival leaves `perSubBranch = false`, sets `parentRequired = "
            "true`, and returns an empty `subwidgetRequired`. Refuted at the F2P "
            "sub-domain (a subfield whose own required flag is false while its widget "
            "predicate is true), where the spec's list is `[true]` but the rival's is "
            "`[]`."
        ),
        "witness": (
            "-- Per-subwidget regime with a single subwidget whose own predicate is\n"
            "-- true; the spec places the marker per subwidget (list [true]) and sets\n"
            "-- no aggregate marker, but this rival sets the aggregate marker and\n"
            "-- leaves the subwidget list empty.\n"
            "example : ¬ problem_spec_requiredAttrs true true\n"
            "    { required := true, disabled := false, hasRequireAllFields := true,\n"
            "      requireAllFields := false, isMultiWidget := true,\n"
            "      subPairs := [(true, true)] }\n"
            "    (implementation_requiredAttrs true true\n"
            "      { required := true, disabled := false, hasRequireAllFields := true,\n"
            "        requireAllFields := false, isMultiWidget := true,\n"
            "        subPairs := [(true, true)] }) := by\n"
            "  unfold problem_spec_requiredAttrs implementation_requiredAttrs\n"
            "  decide\n"
        ),
    },
    {
        "id": "reject-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_PARTIAL),
        "refinement": (
            "a faithful real patch that placed the per-subwidget required marker as "
            "the subwidget's own predicate ALONE — dropping the conjunction with the "
            "subfield's required flag — would set the marker on every subwidget whose "
            "widget reports it, INCLUDING an optional subfield. In the F2P both "
            "subwidgets report the predicate, so the optional second subwidget would "
            "wrongly carry the required marker; the F2P observable asserts it does "
            "NOT, so the patch does NOT resolve. It diverges precisely on the "
            "optional-subfield sub-domain."
        ),
        "rationale": (
            "REJECT from the `subwidgetRequired` clause: the spec demands each entry "
            "be `p.1 && p.2` (the subwidget predicate AND the subfield's required "
            "flag), but the rival writes `p.1` alone. For a subwidget with predicate "
            "true and subfield required false, the spec's entry is `false` and the "
            "rival's is `true`. Refuted at that optional-subfield point."
        ),
        "witness": (
            "-- Per-subwidget regime with one subwidget whose predicate is true but\n"
            "-- whose subfield is optional: the spec's flag is false (marker withheld)\n"
            "-- while this rival, ignoring the subfield flag, emits true.\n"
            "example : ¬ problem_spec_requiredAttrs true true\n"
            "    { required := true, disabled := false, hasRequireAllFields := true,\n"
            "      requireAllFields := false, isMultiWidget := true,\n"
            "      subPairs := [(true, false)] }\n"
            "    (implementation_requiredAttrs true true\n"
            "      { required := true, disabled := false, hasRequireAllFields := true,\n"
            "        requireAllFields := false, isMultiWidget := true,\n"
            "        subPairs := [(true, false)] }) := by\n"
            "  unfold problem_spec_requiredAttrs implementation_requiredAttrs\n"
            "  decide\n"
        ),
    },
    {
        "id": "reject-regime-b-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_REGIMEB),
        "refinement": (
            "a faithful real patch that omitted the aggregate-marker assignment in "
            "the ordinary (non-composite) regime would stop placing the required "
            "marker on ordinary required fields — the common case. Ordinary required "
            "single-widget fields would silently lose their required marker, "
            "regressing the broad required-rendering behavior the pre-existing suite "
            "depends on; the patch would not resolve without breaking those."
        ),
        "rationale": (
            "REJECT from the `parentRequired` clause: in the ordinary regime (guard "
            "holds, per-subwidget branch NOT entered) the spec demands `parentRequired "
            "= true`, but this rival leaves it `false`. Refuted at an ordinary "
            "(non-composite) required field — `hasRequireAllFields` and `isMultiWidget` "
            "false, `subPairs` empty — a distinct input point from the per-subwidget "
            "witnesses."
        ),
        "witness": (
            "-- Ordinary required field (not a composite): the guard holds and the\n"
            "-- per-subwidget branch is not entered, so the spec places the aggregate\n"
            "-- required marker (parentRequired = true); this rival leaves it false.\n"
            "example : ¬ problem_spec_requiredAttrs true true\n"
            "    { required := true, disabled := false, hasRequireAllFields := false,\n"
            "      requireAllFields := false, isMultiWidget := false, subPairs := [] }\n"
            "    (implementation_requiredAttrs true true\n"
            "      { required := true, disabled := false, hasRequireAllFields := false,\n"
            "        requireAllFields := false, isMultiWidget := false, subPairs := [] }) := by\n"
            "  unfold problem_spec_requiredAttrs implementation_requiredAttrs\n"
            "  decide\n"
        ),
    },
    {
        "id": "reject-disabled-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NODISABLED),
        "refinement": (
            "a faithful real patch that dropped the unchanged disabled-marker block "
            "would stop emitting the disabled marker for disabled fields, an "
            "observable regression the pre-existing suite covers (disabled multi-value "
            "field rendering). The patch would not resolve without breaking "
            "disabled-field behavior."
        ),
        "rationale": (
            "REJECT from the `parentDisabled` clause: the spec demands `parentDisabled "
            "= field.disabled`, but this rival never sets it, leaving it `false` even "
            "when the field is disabled. Refuted at a disabled, guard-off field, which "
            "also moves `field.disabled` (true) and the guard inputs (false) off the "
            "values the other witnesses hold them at."
        ),
        "witness": (
            "-- A disabled field with the required guard off: the spec places the\n"
            "-- disabled marker (parentDisabled = field.disabled = true) regardless of\n"
            "-- the required logic, but this rival drops the disabled block.\n"
            "example : ¬ problem_spec_requiredAttrs false false\n"
            "    { required := false, disabled := true, hasRequireAllFields := false,\n"
            "      requireAllFields := false, isMultiWidget := false, subPairs := [] }\n"
            "    (implementation_requiredAttrs false false\n"
            "      { required := false, disabled := true, hasRequireAllFields := false,\n"
            "        requireAllFields := false, isMultiWidget := false, subPairs := [] }) := by\n"
            "  unfold problem_spec_requiredAttrs implementation_requiredAttrs\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the per-widget "expose a
# required marker" predicate is a plain input boolean and the whole decision is
# modeled directly, so there is no in-model axiom obligation for the PBT axiom
# lane to re-discharge. Ported from nagini `AXIOM_TESTS = []`.
AXIOM_TESTS = []
