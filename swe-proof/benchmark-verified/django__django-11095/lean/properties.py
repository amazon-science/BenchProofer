"""properties.py — G-PBT falsification battery for django__django-11095 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside an ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside a ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and each
``theorem correct_<name>`` STATEMENT stays byte-identical). ``expect:"verify"``
passes iff (in scope AND the file elaborates with the obligation closed, no
``sorry``/``admit``/``native_decide`` and no new ``axiom``/``theorem``);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``), re-expressed on this backend's carrier. The
nagini bundle models TWO cooperating operations over a heap-permissioned
``AdminView`` carrier: a default selection hook (``select_applicable_editors``,
identity copy of the ``configured`` collection) and a materialisation
(``materialize_editors``, build from the hook's REPORT filtered by a
per-entry permission flag). This Lean bundle models the SAME two purely
functional cores as two obligations:

  * ``correct_getInlines`` <-> nagini ``select_applicable_editors``. Spec
    ``problem_spec_getInlines selfInlines result := result = selfInlines`` — the
    default hook returns the page's own selected list unchanged.
  * ``correct_getInlineInstances`` <-> nagini ``materialize_editors``. Spec
    ``result = (hookInlines.filter (keepInline hasRequest)).map (toInstance
    hasRequest)`` — the produced editor list is built from the SELECTED list
    (``hookInlines``, the hook output), filtered per-request by ``keepInline``,
    each survivor mapped by ``toInstance`` (which zeroes the max-new-rows flag
    exactly when a request is present and the viewer may not add). The static
    attribute ``selfInlines`` does NOT determine the result.

The BEHAVIOURAL DISCRIMINATOR (the fix): the materialisation iterates the
SELECTED list (``hookInlines``), not the static attribute (``selfInlines``).
Pre-fix it iterated the static attribute and ignored any override; the
``from-self-inlines`` rival below IS that pre-fix behavior, and on the F2P
override scenario (the hook reports a subset / reorder / empty) it materialises
the wrong editors.

BINDER STRUCTURE. ``problem_spec_getInlineInstances`` has FOUR input binders:
``hasRequest : Bool`` (whether a request is in context — gates the
filter/max-zeroing), ``selfInlines`` (the static attribute — must NOT affect the
result), ``hookInlines`` (the selected list — the true source), and the element
booleans of each ``Inline`` (``hasViewOrChange``/``hasAdd``/``hasDelete`` — drive
``keepInline`` and ``toInstance``). ``problem_spec_getInlines`` has one binder,
``selfInlines``. All load-bearing binders are varied across the reject witnesses
(see the point-spread block at the bottom): ``hasRequest ∈ {false, true}``,
``selfInlines`` ranges over empty and non-empty, ``hookInlines`` over empty /
single / two-element, and the element permission booleans take both truth values
so both branches of ``keepInline`` and both branches of ``toInstance`` are
exercised.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini rivals ``frame-write-*``
    overwrite a read-only ``Acc(...,1/2)`` input to "satisfy" the postcondition
    and must be rejected for INSUFFICIENT PERMISSION. Lean is referentially
    transparent: ``selfInlines``/``hookInlines`` are immutable values, there is
    no ``mut`` input binder, no aliasing, and no half-permission cell to
    overwrite. The class is VACUOUS here; no substitute probe is fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS. ``implementation_*`` is a total Lean
    ``def``; a diverging implementation cannot be written at all. (The nagini
    sibling carries no diverge case regardless.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Both postconditions are GROUNDED in the
    inputs: ``getInlines`` pins ``result = selfInlines`` and
    ``getInlineInstances`` pins ``result`` to a structural
    ``filter``/``map`` over ``hookInlines`` with the element booleans. There is
    no opaque answer key to echo — producing each editor from its own selected
    class IS doing the work. In its place the battery carries honest POSITIVE
    CONTROLS that must verify (matching the nagini ``pos-*`` controls). Those
    controls are deliberately NOT the cheapest available reshape: a reshape that
    is definitionally equal to the frozen body rides the frozen tactic script and
    certifies nothing, so each positive here is measured non-defeq and re-proves
    the obligation itself (see the POSITIVE CONTROLS block).

  * PARTIAL-DOMAIN / VALUE — APPLIES. The central differential. Rivals correct on
    part of the domain but diverging where the fix bites: materialise from the
    static attribute (the pre-fix bug — correct only when the selected list
    equals the static attribute); drop the permission filter (correct only when
    every class is kept); drop the max-new-rows zeroing (correct only when every
    kept class may add); apply that zeroing UNGATED, i.e. also when no request is
    in context (correct only when a request is always present); reverse the
    materialised order; and, on the default hook, narrow the selection by
    dropping the first class or reordering it.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate directly at one
concrete ground input and closes by ``decide`` (the ``Inline``/``InlineInstance``
structures ``deriving DecidableEq`` and every input is a ground list literal, so
the ``Id.run do`` / ``for`` loop reduces). Each witness binds NOTHING in its head
(all inputs are ground literals), so there are no hypotheses whose consistency
could be in question. Each was checked with two real ``lake env lean`` builds to
HOLD of its rival and to FAIL on the frozen solution (``decide`` proves the
negation for the rival, and reports the proposition is false for gold), so it
discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
patch that on the F2P override scenario materialises the wrong editors (wrong
source, wrong filtering, wrong max-rows flag, or wrong order), so the F2P test —
which overrides the hook to report a subset / empty selection and asserts the
materialised classes equal exactly that report — would mismatch, so the faithful
patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the permission outcomes and hook output enter as data; the modeled
behavior is spelled out deeply). The axiom lane belongs to G-AX, and the nagini
``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-11095"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# getInlines impl block (whole `Id.run do` body).
_SELECT_IMPL = ("def implementation_getInlines (selfInlines : List Inline) : "
                "List Inline := Id.run do\n  return selfInlines")

# getInlineInstances impl block (whole `Id.run do` body).
_GII_IMPL = """  let mut inlineInstances : List InlineInstance := []
  for inlineClass in hookInlines do
    let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := false }
    if hasRequest then
      if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
        continue
      if !inlineClass.hasAdd then
        inst := { inst with maxNumZeroed := true }
    inlineInstances := inlineInstances ++ [inst]
  return inlineInstances"""

# Fine-grained anchors inside the gII loop body (each unique in the file).
_GII_FOR = "  for inlineClass in hookInlines do"
_GII_FILTER = ("      if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || "
               "inlineClass.hasDelete) then\n        continue\n")
_GII_MAXNUM = ("      if !inlineClass.hasAdd then\n"
               "        inst := { inst with maxNumZeroed := true }\n")
_GII_APPEND = "    inlineInstances := inlineInstances ++ [inst]"

# getInlines return line (used by the drop-first rival; unique in the file).
_SELECT_RETURN = "  return selfInlines"

# Frozen getInlineInstances proof intro (proof region) — unique in the file, so
# the admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_GII_INTRO = "  intro hasRequest selfInlines hookInlines\n"

# Frozen TACTIC BODIES (proof region only — the theorem STATEMENTs above them are
# never touched, so `variant_scope`'s obligation-preserved rule still holds). A
# positive control whose impl is NOT definitionally the frozen one has to carry
# its own proof; these are the anchors it replaces.
_SELECT_PROOF = "  intro selfInlines\n  rfl\n"
_GII_PROOF = """  intro hasRequest selfInlines hookInlines
  unfold problem_spec_getInlineInstances implementation_getInlineInstances
  -- The desugared loop body is definitionally equal to the cleaned body, so we can
  -- `show` the goal in cleaned form and discharge it with the closed-form helper.
  show Id.run (forIn hookInlines ([] : List InlineInstance)
        (cleanBody_getInlineInstances hasRequest))
      = (hookInlines.filter (keepInline hasRequest)).map (toInstance hasRequest)
  rw [foldClean_getInlineInstances, List.nil_append]
"""


assert _SELECT_IMPL in _BASE and _BASE.count(_SELECT_IMPL) == 1, "select impl anchor drift"
assert _GII_IMPL in _BASE and _BASE.count(_GII_IMPL) == 1, "gII impl anchor drift"
assert _BASE.count(_SELECT_PROOF) == 1, "select proof anchor drift"
assert _BASE.count(_GII_PROOF) == 1, "gII proof anchor drift"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-different but CORRECT impls that
# MUST verify, else SPEC-TOO-STRONG. Each keeps its `theorem correct_<name>`
# STATEMENT byte-identical; only the impl region and the tactic BODY differ.
#
# AUDIT NOTE (why these are the shapes they are). An earlier revision used
# reshapes that were DEFINITIONALLY EQUAL to the frozen bodies — a `let`-bound
# return for the hook, and an alpha-renaming of the loop accumulator/variable for
# the materialisation — so the frozen tactic script closed them unchanged. Both
# were re-measured with real builds and confirmed defeq to the frozen impls
# (`example : @letSelect = @frozenSelect := by rfl` and the alpha-renamed loop
# likewise both elaborate, exit 0). A positive whose impl is definitionally the
# frozen one passes HONESTLY but tests nothing about spec strength: it cannot
# distinguish "the spec admits faithful reshapes" from "the spec admits exactly
# one syntactic form". Each positive is therefore now a shape that is NOT defeq
# to the frozen body (verified: the corresponding `rfl` FAILS) and that carries
# its own re-proof of the frozen obligation, so it genuinely exercises the
# SPEC-TOO-STRONG direction. Both verified with real builds.
# ===========================================================================

# (a) getInlines: the identity selection built by an explicit forward COPY LOOP
# (accumulate each selected class in order) rather than returned directly. This
# is the faithful port of nagini's copy-loop positive, and it is NOT defeq to the
# frozen `return selfInlines` (checked: `rfl` fails between the two), so it needs
# — and carries — a real closed-form induction over the loop.
_POS_SELECT = _swap(
    _swap(_BASE, _SELECT_IMPL,
          "def implementation_getInlines (selfInlines : List Inline) : "
          "List Inline := Id.run do\n"
          "  let mut chosen : List Inline := []\n"
          "  for inlineClass in selfInlines do\n"
          "    chosen := chosen ++ [inlineClass]\n"
          "  return chosen"),
    _SELECT_PROOF,
    """  intro selfInlines
  unfold problem_spec_getInlines implementation_getInlines
  have key : ∀ (xs : List Inline) (init : List Inline),
      (forIn xs init (fun x r =>
        (pure (ForInStep.yield (r ++ [x])) : Id (ForInStep (List Inline)))) : Id _)
        = init ++ xs := by
    intro xs
    induction xs with
    | nil => intro init; simp [List.forIn_nil, Id.run, pure]
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simpa using ih (init ++ [a])
  simpa using key selfInlines []
""")

# (b) getInlineInstances: the per-class decision is restructured into a single
# positive guard (a local `keep` boolean, no `continue`) with the max-new-rows
# flag COMPUTED into the constructed editor instead of patched afterwards. Same
# function of the inputs, but a different case tree: NOT defeq to the frozen body
# (checked: `rfl` fails between the two), so the frozen `show ... rw
# [foldClean_getInlineInstances]` script no longer applies and the case carries
# its own closed-form induction. This is the positive that actually certifies the
# spec accepts a faithful re-shaping of the filter/map decision.
_POS_MATERIALIZE = _swap(
    _swap(_BASE, _GII_IMPL, """  let mut inlineInstances : List InlineInstance := []
  for inlineClass in hookInlines do
    let keep := !hasRequest || inlineClass.hasViewOrChange || inlineClass.hasAdd
      || inlineClass.hasDelete
    if keep then
      inlineInstances := inlineInstances ++
        [{ id := inlineClass.id, maxNumZeroed := hasRequest && !inlineClass.hasAdd }]
  return inlineInstances"""),
    _GII_PROOF,
    """  intro hasRequest selfInlines hookInlines
  unfold problem_spec_getInlineInstances implementation_getInlineInstances
  have key : ∀ (xs : List Inline) (init : List InlineInstance),
      (forIn xs init (fun ic r =>
        (if (!hasRequest || ic.hasViewOrChange || ic.hasAdd || ic.hasDelete) then
            pure (ForInStep.yield (r ++
              [{ id := ic.id, maxNumZeroed := hasRequest && !ic.hasAdd }]))
          else pure (ForInStep.yield r) : Id (ForInStep (List InlineInstance)))) : Id _)
        = init ++ (xs.filter (keepInline hasRequest)).map (toInstance hasRequest) := by
    intro xs
    induction xs with
    | nil => intro init; simp [List.forIn_nil, Id.run, pure]
    | cons a as ih =>
      intro init
      by_cases hk : (!hasRequest || a.hasViewOrChange || a.hasAdd || a.hasDelete) = true
      · have hk' : keepInline hasRequest a = true := by simpa [keepInline] using hk
        rw [List.forIn_cons, List.filter_cons_of_pos hk']
        simp only [hk, if_true, List.map_cons]
        have e := ih (init ++ [({ id := a.id, maxNumZeroed := hasRequest && !a.hasAdd } : InlineInstance)])
        simpa [toInstance] using e
      · have hk' : ¬ (keepInline hasRequest a = true) := by simpa [keepInline] using hk
        simp only [Bool.not_eq_true] at hk
        rw [List.forIn_cons, List.filter_cons_of_neg hk']
        simp only [hk, Bool.false_eq_true, if_false]
        simpa using ih init
  simpa using key hookInlines []
""")


# ===========================================================================
# ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
# normal, F2P-shaped input. The frozen theorem carries NO precondition binder,
# so the nagini precondition-admission self-call re-expresses as: discharge the
# spec predicate by evaluation at a concrete F2P-shaped input (a request in
# context, one selected class the viewer may view/change and delete but not add,
# so it is kept AND its max-rows flag is zeroed) as a `have`, then close the
# frozen obligation verbatim. Nothing is assumed: no new declaration, statement
# byte-identical, the ground instance is a `have` prepended to the existing
# tactic body. Verified with a real build.
# ===========================================================================

_ADMISS = _swap(
    _BASE, _GII_INTRO,
    "  have _ground : problem_spec_getInlineInstances true []\n"
    "      [{ id := 7, hasViewOrChange := true, hasAdd := false, hasDelete := true }]\n"
    "      (implementation_getInlineInstances true []\n"
    "        [{ id := 7, hasViewOrChange := true, hasAdd := false, hasDelete := true }]) := by\n"
    "    unfold problem_spec_getInlineInstances implementation_getInlineInstances\n"
    "    decide\n"
    + _GII_INTRO)


# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each carries (a) the refinement argument that its faithful
# real patch would NOT resolve the F2P, and (b) a witness pinning the violation
# at one concrete input. Each witness was run against both the rival (must
# elaborate) and the frozen solution (must fail).
# ===========================================================================

# ---- the fix itself: materialise from the STATIC attribute, not the selected list ----
_FROM_SELF = _swap(_BASE, _GII_FOR, "  for inlineClass in selfInlines do")

# ---- drop the per-request keep filter (keep every selected class) ----
_NO_FILTER = _swap(_BASE, _GII_FILTER, "")

# ---- drop the max-new-rows zeroing (never force the flag) ----
_NO_MAXNUM = _swap(_BASE, _GII_MAXNUM, "")

# ---- zero the max-new-rows flag even with NO request in context ----
# The mirror of _NO_MAXNUM: instead of never zeroing, this zeroes UNCONDITIONALLY
# on the add permission, hoisting the step out of the `if hasRequest` branch. The
# `hasRequest` half of `toInstance`'s guard is the one clause direction no other
# rival attacks (materialize-no-maxnum only shows the flag must be zeroed WHEN a
# request is present; nothing pinned that it must NOT be zeroed when absent).
_MAXNUM_UNGATED = _swap(_BASE, _GII_IMPL, """  let mut inlineInstances : List InlineInstance := []
  for inlineClass in hookInlines do
    let mut inst : InlineInstance := { id := inlineClass.id, maxNumZeroed := false }
    if hasRequest then
      if !(inlineClass.hasViewOrChange || inlineClass.hasAdd || inlineClass.hasDelete) then
        continue
    if !inlineClass.hasAdd then
      inst := { inst with maxNumZeroed := true }
    inlineInstances := inlineInstances ++ [inst]
  return inlineInstances""")

# ---- reverse the materialised order (prepend instead of append) ----
_REVERSE = _swap(_BASE, _GII_APPEND,
                 "    inlineInstances := [inst] ++ inlineInstances")

# ---- default hook narrows the selection (drop the first selected class) ----
_SELECT_DROP = _swap(_BASE, _SELECT_RETURN, "  return selfInlines.drop 1")

# ---- default hook reorders the selection (reverse) ----
_SELECT_REVERSE = _swap(_BASE, _SELECT_RETURN, "  return selfInlines.reverse")


def _w_gii(hasRequest, selfInlines, hookInlines):
    return (
        f"example : ¬ problem_spec_getInlineInstances {hasRequest} {selfInlines} "
        f"{hookInlines}\n"
        f"    (implementation_getInlineInstances {hasRequest} {selfInlines} "
        f"{hookInlines}) := by\n"
        "  unfold problem_spec_getInlineInstances implementation_getInlineInstances\n"
        "  decide\n")


def _w_select(selfInlines):
    return (
        f"example : ¬ problem_spec_getInlines {selfInlines}\n"
        f"    (implementation_getInlines {selfInlines}) := by\n"
        "  unfold problem_spec_getInlines implementation_getInlines\n"
        "  decide\n")


# Ground `Inline` literals used in witnesses.
_ALL = "{ id := 1, hasViewOrChange := true, hasAdd := true, hasDelete := true }"
_ALL2 = "{ id := 2, hasViewOrChange := true, hasAdd := true, hasDelete := true }"
_NONE = "{ id := 1, hasViewOrChange := false, hasAdd := false, hasDelete := false }"
_NOADD = "{ id := 1, hasViewOrChange := true, hasAdd := false, hasDelete := false }"


SPEC_TESTS = [
    {
        "id": "pos-select-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SELECT,
        "rationale": "structurally-different but CORRECT default hook: the identity "
                     "selection is built by an explicit forward COPY LOOP that "
                     "accumulates each selected class in order, rather than returned "
                     "directly. This is the faithful port of nagini's copy-loop "
                     "positive. It is NOT definitionally equal to the frozen body "
                     "(measured: `rfl` between the two FAILS), so the frozen `rfl` "
                     "cannot close it and the case carries its own closed-form "
                     "induction over the loop — statement byte-identical, no new "
                     "axiom/lemma, only the tactic BODY differs. Must verify, else "
                     "SPEC-TOO-STRONG: it certifies the spec accepts a faithful "
                     "reshaping of the hook rather than one syntactic form.",
    },
    {
        "id": "pos-materialize-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATERIALIZE,
        "rationale": "structurally-different but CORRECT materialisation: the "
                     "per-class decision is restructured into a single POSITIVE guard "
                     "(a local `keep` boolean, no `continue`) with the max-new-rows "
                     "flag COMPUTED into the constructed editor instead of patched "
                     "afterwards. It computes the same editor list on every input "
                     "(filter+map over the selected list) but has a different case "
                     "tree, so it is NOT definitionally equal to the frozen body "
                     "(measured: `rfl` between the two FAILS) and the frozen `show "
                     "... rw [foldClean_getInlineInstances]` script no longer applies; "
                     "the case carries its own closed-form induction — statement "
                     "byte-identical, no new axiom/lemma, only the tactic BODY "
                     "differs. Must verify, else SPEC-TOO-STRONG. Ports nagini's "
                     "pos-materialize-reshape, strengthened past alpha-renaming so it "
                     "actually exercises the soundness direction.",
    },
    {
        "id": "admiss-ground-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the obligation is discharged at a normal F2P-shaped input (a "
                     "request in context; one selected class the viewer may "
                     "view/change and delete but NOT add — so it is kept AND its "
                     "max-new-rows flag is zeroed) by evaluation as a `have`, then "
                     "the frozen obligation is closed verbatim. Verifies (else the "
                     "modeled behavior would be unsatisfiable at a normal F2P input — "
                     "the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, statement byte-identical, ground instance is a "
                     "`have` in the existing tactic body. Ports nagini's "
                     "admiss-fresh-view.",
    },

    # ---- the central differential: build from the static attribute ----
    {
        "id": "materialize-from-self",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FROM_SELF,
        "refinement": "this IS the pre-fix behaviour: materialise from the static "
                      "attribute (`selfInlines`) instead of the selected list "
                      "(`hookInlines`). It ignores any override of the selection, so "
                      "on the F2P scenario — which overrides the hook to report a "
                      "subset / empty selection while the static attribute still "
                      "lists both classes — it materialises editors the override "
                      "excludes. The F2P test asserts the materialised classes equal "
                      "exactly the (overridden) report, so the faithful patch would "
                      "NOT resolve.",
        "rationale": "REJECT from the result clause of getInlineInstances: the spec "
                     "pins `result` to a filter+map over `hookInlines`, but the rival "
                     "produces a filter+map over `selfInlines`; these differ whenever "
                     "the selected list differs from the static attribute. Refuted at "
                     "hasRequest=false, selfInlines=[one class], hookInlines=[] — the "
                     "spec demands [] (empty selection), the rival emits one editor. "
                     "This is the only witness varying selfInlines away from "
                     "hookInlines, so it is the binder abused by the pre-fix bug.",
        "witness": _w_gii("false", f"[{_ALL}]", "[]"),
    },

    # ---- drop the per-request keep filter ----
    {
        "id": "materialize-no-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NO_FILTER,
        "refinement": "drops the per-request keep guard, so a selected class the "
                      "viewer may neither view/change, add, nor delete is still "
                      "materialised. A real patch removing that guard exposes editors "
                      "an unauthorised viewer must not see, failing the permission "
                      "PASS_TO_PASS behavior — it does not faithfully resolve.",
        "rationale": "REJECT from the result clause: the spec filters by "
                     "`keepInline hasRequest` (under a request, keep only classes the "
                     "viewer can view/change, add, or delete); the rival keeps every "
                     "class. Refuted at hasRequest=true with one class whose three "
                     "permission booleans are all false: the spec demands [] (the "
                     "class is dropped), the rival materialises it. Exercises "
                     "hasRequest=true and the all-false element branch of keepInline.",
        "witness": _w_gii("true", "[]", f"[{_NONE}]"),
    },

    # ---- drop the max-new-rows zeroing ----
    {
        "id": "materialize-no-maxnum",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NO_MAXNUM,
        "refinement": "never forces the max-new-rows flag to zero for a kept class "
                      "whose viewer may not add. A real patch dropping that step "
                      "would let a viewer without add permission create new rows "
                      "through the editor, failing the permission PASS_TO_PASS "
                      "behavior — it does not faithfully resolve.",
        "rationale": "REJECT from the result clause via `toInstance`: the spec zeroes "
                     "`maxNumZeroed` exactly when a request is present and the viewer "
                     "may not add; the rival always leaves it false. Refuted at "
                     "hasRequest=true with one class kept (view/change true) but "
                     "hasAdd=false: the spec demands maxNumZeroed=true, the rival "
                     "emits false. Exercises the max-zeroing branch of toInstance, "
                     "which no other witness pins.",
        "witness": _w_gii("true", "[]", f"[{_NOADD}]"),
    },

    # ---- zero the max-new-rows flag with no request in context ----
    {
        "id": "materialize-maxnum-ungated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _MAXNUM_UNGATED,
        "refinement": "hoists the max-new-rows zeroing OUT of the request-gated "
                      "branch, so a viewer-independent context (no request) also "
                      "gets the restriction applied. A real patch that zeroed the "
                      "row limit whenever the add permission is absent — including "
                      "when there is no request to judge permissions against — "
                      "would silently restrict the editors built for every "
                      "non-request caller, breaking the no-request PASS_TO_PASS "
                      "behavior that renders unrestricted editors. It does not "
                      "faithfully resolve.",
        "rationale": "REJECT from the result clause via `toInstance`, whose guard "
                     "is a CONJUNCTION: the flag is zeroed exactly when a request "
                     "is present AND the viewer may not add. materialize-no-maxnum "
                     "pins only the `hasRequest=true` direction (it must be zeroed "
                     "there); this rival pins the other direction — with "
                     "hasRequest=false and one class with hasAdd=false the spec "
                     "demands maxNumZeroed=false, the rival emits true. Added by "
                     "audit: it is the only witness varying the max-rows flag at "
                     "hasRequest=false, so without it the request-gating of that "
                     "clause is unattested.",
        "witness": _w_gii("false", "[]", f"[{_NOADD}]"),
    },

    # ---- reverse the materialised order ----
    {
        "id": "materialize-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REVERSE,
        "refinement": "materialises the kept editors in REVERSED order (prepend "
                      "instead of append). A real patch reversing the order would "
                      "render inline editors out of their declared/selected order; "
                      "the F2P and any multi-inline admin ordering test pin the "
                      "order, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from the result clause: the spec preserves the order of "
                     "`hookInlines` (map over the filtered list, in order); the rival "
                     "reverses it. Refuted at hasRequest=false with two distinct kept "
                     "classes (ids 1,2): the spec demands [inst 1, inst 2], the rival "
                     "emits [inst 2, inst 1]. Exercises a two-element hookInlines with "
                     "distinct identities, which no other witness does.",
        "witness": _w_gii("false", "[]", f"[{_ALL},\n     {_ALL2}]"),
    },

    # ---- default hook narrows the selection ----
    {
        "id": "select-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SELECT_DROP,
        "refinement": "the default selection hook drops the FIRST selected class "
                      "(`selfInlines.drop 1`). A real default hook returning "
                      "`self.inlines[1:]` would drop the first inline from every "
                      "default admin, breaking the existing non-override behavior "
                      "(the PASS_TO_PASS admin views that render all selected "
                      "inlines) — it does not resolve.",
        "rationale": "REJECT from the getInlines clause `result = selfInlines`: the "
                     "rival returns `selfInlines.drop 1`, which differs from "
                     "`selfInlines` on any non-empty input. Refuted at a "
                     "single-element selection: the spec demands the whole list, the "
                     "rival emits []. Sole rival attacking the getInlines obligation, "
                     "varying its lone binder selfInlines away from empty.",
        "witness": _w_select(f"[{_ALL}]"),
    },

    # ---- default hook reorders the selection ----
    {
        "id": "select-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SELECT_REVERSE,
        "refinement": "the default selection hook returns the selected list REVERSED. "
                      "A real default hook returning `self.inlines[::-1]` would render "
                      "the default admin's inlines out of their declared order, "
                      "breaking the non-override ordering behavior (the PASS_TO_PASS "
                      "admin views that render inlines in declared order) — it does "
                      "not resolve.",
        "rationale": "REJECT from the getInlines clause `result = selfInlines`: the "
                     "rival returns `selfInlines.reverse`, which differs from "
                     "`selfInlines` whenever the list has >=2 distinct elements. "
                     "Refuted at a two-element selection (ids 1,2), a DISTINCT input "
                     "point from select-drop-first (single-element), so the getInlines "
                     "binder selfInlines is varied across its own reject witnesses.",
        "witness": _w_select(f"[{_ALL},\n     {_ALL2}]"),
    },
]


# ===========================================================================
# Nagini -> lean accounting.
#
#   sibling case (nagini)              -> here
#   -----------------------------------------------------------------------
#   pos-select-reshape                 -> pos-select-reshape        PORTED
#   pos-materialize-reshape            -> pos-materialize-reshape   PORTED
#   admiss-fresh-view                  -> admiss-ground-input       RE-EXPRESSED
#   partial-materialize-from-configured-> materialize-from-self     PORTED
#   partial-materialize-no-filter      -> materialize-no-filter     PORTED
#   partial-select-drop-first          -> select-drop-first         PORTED
#   nearmiss-reverse-order             -> materialize-reverse-order PORTED
#   (none)                             -> materialize-no-maxnum     ADDED
#   (none)                             -> materialize-maxnum-ungated ADDED (audit)
#   (none)                             -> select-reverse-order      ADDED (2nd pt)
#   frame-write-reported               -> (none)                   VACUOUS (frame)
#   frame-write-configured             -> (none)                   VACUOUS (frame)
#   AXIOM_TESTS (ax-aref-deepmodels)   -> (none)                    DROPPED (G-AX)
#
# PORTED (pos-select-reshape): the nagini positive keeps a COPY-LOOP shape with a
#   renamed counter. An earlier revision of this port declined the loop and merely
#   bound the returned list to a local, which is DEFINITIONALLY the frozen body
#   (measured: `example : @letSelect = @frozenSelect := by rfl` elaborates, exit
#   0) — it passed on the frozen `rfl` and so tested nothing about spec strength.
#   The loop shape is now carried faithfully: not defeq to `return selfInlines`
#   (that `rfl` fails), proof re-closed by closed-form induction, verified exit 0.
# PORTED (pos-materialize-reshape): the nagini positive renames the loop counter
#   and regroups the framing asserts. An earlier revision here renamed only the
#   accumulator / loop variable / per-editor local — identical up to
#   alpha-renaming, hence defeq to the frozen body (measured: that `rfl`
#   elaborates), so the frozen fold proof closed it and the SPEC-TOO-STRONG
#   direction went unexercised. Replaced by a reshape with a genuinely different
#   case tree (single positive `keep` guard, no `continue`, max-rows flag computed
#   into the constructed editor): not defeq (that `rfl` fails), so it needs and
#   carries its own closed-form induction. Verified exit 0. The guide's "prefer a
#   cheaper equivalent shape" applies to choosing a proof, not to choosing a
#   positive control that cannot fail.
# RE-EXPRESSED (admiss-ground-input): the nagini admissibility case establishes
#   materialize's Requires (len(reported)==len(granted)) via a statically-dead
#   self-call. The frozen lean theorem carries NO precondition binder, so the
#   honest analogue discharges the POSTCONDITION at a normal F2P-shaped input as a
#   `have`, proving the modeled behavior is satisfiable there, then closes the
#   frozen obligation verbatim.
# ADDED (materialize-no-maxnum): the max-new-rows zeroing (`toInstance`'s
#   maxNumZeroed) is a load-bearing, transparent part of the SAME modeled spec
#   that the ported nagini rivals happened not to target individually (nagini's
#   `granted` flag is a single keep/drop bit and does not model the max_num
#   field). A rival that never zeroes the flag is refutable and its faithful patch
#   would fail the permission behavior, so it is a genuine attack on a modeled
#   clause, not a fabricated one for an unmodeled behavior.
# ADDED (materialize-maxnum-ungated): audit-added. `toInstance`'s guard is a
#   CONJUNCTION (a request is present AND the viewer may not add), and
#   materialize-no-maxnum pinned only the first direction — that the flag must be
#   zeroed when a request IS present. Nothing attested that it must NOT be zeroed
#   when there is no request, so a rival hoisting the zeroing out of the gated
#   branch was unattacked. It is refutable at (hasRequest=false, one class with
#   hasAdd=false) and its faithful patch would restrict every no-request caller's
#   editors, so it is a genuine attack on a modeled clause.
# VACUOUS (frame-write-*): the nagini rivals overwrite a read-only Acc(...,1/2)
#   input and must be rejected for insufficient permission. Lean is referentially
#   transparent — `selfInlines`/`hookInlines` are immutable values, no `mut`
#   input, no aliasing, no half-permission cell — so the class is vacuous. This
#   was re-derived with a real build rather than accepted as argument: the closest
#   faithful analogue (an impl that `let mut`-rebinds its own input binder and
#   returns it) is DEFINITIONALLY the frozen impl — `example : @frameWriteSelect =
#   @frozenSelect := by rfl` elaborates, exit 0 — so such a case could only ever
#   be vacuous. The only way to make a local write observable is to change the
#   RETURNED value, which collapses into the value-level rival class the battery
#   already carries (select-drop-first / select-reverse-order). No substitute
#   probe fabricated.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   opaque callee and consumes no axiom (permission outcomes + hook output enter
#   as data), so there is nothing to probe and the gate ignores AXIOM_TESTS.
#
# POINT SPREAD. The seven reject witnesses probe seven DISTINCT input tuples
# (pts=7), across the two obligations:
#   getInlineInstances (hasRequest, selfInlines, hookInlines):
#     (false, [ALL],      [])          materialize-from-self      result-source
#     (true,  [],         [NONE])      materialize-no-filter      keepInline
#     (true,  [],         [NOADD])     materialize-no-maxnum      toInstance (gated)
#     (false, [],         [NOADD])     materialize-maxnum-ungated toInstance (gate)
#     (false, [],         [ALL,ALL2])  materialize-reverse-order  order
#   getInlines (selfInlines):
#     ([ALL])                          select-drop-first          identity copy
#     ([ALL,ALL2])                     select-reverse-order       identity copy
#   Across them hasRequest ∈ {false,true}; selfInlines takes empty and non-empty
#   (and, in from-self, differs from hookInlines — the binder the pre-fix bug
#   abuses); hookInlines ranges over empty / single / two-element; and the
#   element permission booleans take both values so both keepInline branches and
#   both toInstance branches are exercised. The last two gII points share the same
#   hookInlines and differ ONLY in hasRequest, which is what pins the max-rows
#   clause to its request GATE in both directions (zeroed when a request is
#   present, NOT zeroed when absent). No load-bearing binder is pinned.
AXIOM_TESTS = []
