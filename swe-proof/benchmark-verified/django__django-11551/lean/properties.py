"""properties.py — PBT falsification manifest for django__django-11551 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the positive controls, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
The modeled function decides, for ONE listed display-configuration entry, the
diagnostic (if any) it produces:

    implementation_validateDisplayItem
        (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)
        : List String

over four independent observations of the entry — whether it is callable,
whether it is an attribute of the admin object, the metadata field lookup
(`none` = no such field / `some b` = a field with many-to-many flag `b`), and
model attribute access (same `Option Bool` shape) — returning `[]` (accepted),
`["E109"]` (a many-to-many field), or `["E108"]` (unresolvable). The carrier is
FULLY TRANSPARENT (`Bool`, `Option Bool`, `List String`); there is no opaque
callee, so every rival is refutable by unfolding + `simp` at a concrete input —
no carrier conditioning is needed and no witness binds a hypothesis (nothing to
be inconsistent).

The postcondition pins the result on every reachable combination via five
independent top-level clauses:

  (1) itemCallable = true                                     => []
  (2) not itemCallable, adminHasAttr = true                   => []
  (3) not either, modelField = some m                         => E109 if m else []
  (4) not either, modelField = none, modelAttr = some m       => E109 if m else []
  (5) not either, modelField = none, modelAttr = none         => E108

So the spec is exhaustive. The live attack surface is therefore PARTIAL-DOMAIN
rivals that get one sub-domain wrong (the F2P sub-domain above all — a field
reachable only via the metadata lookup while attribute access fails), a
VALUE-DOUBLE-MASK rival that reads the wrong source's relation flag, and
CONTROL-FLOW rivals that drop an early accept or a diagnostic branch. Each
reject rival carries the refinement argument that its faithful real patch would
NOT resolve the F2P / would break a P2P.

PORTING NOTES (which nagini cases port, which are omitted)
----------------------------------------------------------
The nagini sibling models a six-`bool` decision returning an int code in
{0,108,109}. The lean carrier narrows this to the four-observation, list-valued
core above; the correspondence is: nagini's `is_invokable` -> `itemCallable`,
`is_presenter_attr` -> `adminHasAttr`, and nagini's `(structural_absent,
structural_is_relation)` / `(attribute_absent, attribute_is_relation)` pairs
collapse into `modelField` / `modelAttr : Option Bool` (absent -> `none`,
present-with-m2m-flag -> `some b`). Verdicts 0/108/109 -> `[]`/`["E108"]`/
`["E109"]`.

  * nagini `pos-control-fused-early` -> `pos-fused-early` — a correct impl with
    the two early accepts FUSED (`itemCallable || adminHasAttr`) and the field
    resolution reshaped into nested `match`es; proof re-closed by exhaustive
    case split. Verifies or the spec is over-fit (SPEC-TOO-STRONG).
  * nagini `pos-control-inline-m2m` -> `pos-functional-form` — a second correct
    impl in a structurally different shape: a pure functional `if/else` +
    `match` expression (no `Id.run do` / `let mut`), the m2m test inlined per
    resolution source. Proof re-closed. The carrier is transparent so there is
    no oracle to echo; stands purely as a soundness positive of a different form.
  * nagini `admiss-f2p-shape` -> `admiss-f2p-shape` — LANDED BY AUDIT. The port
    had omitted this as "vacuous because the lean obligation carries no
    precondition hypothesis, so there is nothing to over/under-constrain". That
    reason is wrong, and the omission dropped one of the three directions this
    gate exists to test (PRECOND-TOO-STRONG). On a total carrier the analogue of
    an over-strong precondition is the obligation being UNSATISFIABLE at exactly
    an F2P-shaped input, which is a real, checkable property and is not implied
    by the positives: `cases … <;> simp_all` discharges all 36 cells as one
    normal-form blob, so it never exhibits any single cell's clause as
    independently satisfiable. This case discharges the obligation at the
    concrete F2P point (not callable, not an admin attr, metadata field present
    & non-relation, attribute access failing) BY EVALUATION as a standalone
    `have`, naming clause (3) explicitly via `refine`, BEFORE closing the frozen
    obligation verbatim. If the spec were unsatisfiable there the `have` fails
    and the case reports it. Built: exit 0.
  * nagini `reject-prepatch-gate` -> `reject-prepatch-gate` — gates the metadata
    lookup behind attribute access succeeding, so a field reachable only via the
    metadata lookup is misreported unresolvable (the exact F2P bug).
  * nagini `reject-wrong-source-relation-C` -> `reject-wrong-source-relation` —
    in the metadata-field-present branch, reads the ATTRIBUTE source's relation
    flag instead of the metadata field's.
  * nagini `reject-drop-e109-on-attr-path` -> `reject-drop-e109-attr` — on the
    attribute-resolved branch, hardcodes non-relation, so an m2m reachable only
    via attribute access is accepted instead of diagnosed.
  * nagini `reject-structural-absent-to-108` -> `reject-metadata-none-to-e108` —
    whenever the metadata lookup yields nothing, reports unresolvable, ignoring
    attribute access entirely (reverses the very fix).
  * nagini `reject-drop-presenter-accept` -> `reject-drop-presenter` — drops the
    admin-attribute early accept.
  * added `reject-drop-callable` — drops the callable early accept (attacks
    clause (1), the ONLY rival that varies `itemCallable = true`; without it a
    rival mishandling only the callable observation would slip by).
  * added `reject-accept-unresolvable` — never emits the unresolvable diagnostic
    (attacks clause (5): returns `[]` where the spec demands `["E108"]`).
  * added by AUDIT `reject-prefer-attr-when-both` — a PRECEDENCE rival. The
    observable space is 2*2*3*3 = 36 points; 16 of them are the cells where BOTH
    the metadata lookup and attribute access resolve. Clause (3) pins the result
    to the METADATA field's flag alone there, but every rival above is
    observationally EQUAL to gold across that entire region, so the precedence
    was asserted by the spec and probed by nothing. This rival differs from gold
    ONLY on the two cells where both routes resolve and disagree.
  * AUDIT retarget of `reject-wrong-source-relation`'s witness: it stood at
    modelAttr=none, which is the rival's hardcoded-non-relation arm, not the
    wrong-source READ its rationale names. Moved to modelAttr=some false so the
    witness exercises the misread it claims. Both witnesses were rebuilt: rival
    exit 0, gold exit 1, and the gold-side failure is the semantic residue
    `⊢ False` — `simp` drove the `Id.run do` block to the literal and DECIDED
    the refutation.
    (Corrected by a later independent audit: this bullet previously cited the
    residue as `¬ pure ["E109"] = ["E109"]`. That is the PRE-FIX residue of the
    hollow `simp [..., Id.run]` tactic — the one the AUDIT FIX note below the
    witness helper establishes as carrying NO information about the claim — so
    quoting it here as evidence of discrimination contradicted that note. Both
    forms were rebuilt to settle it: with the shipped tactic gold rests at
    `⊢ False` (exit 1) and the flipped claim EXITS 0; with the old tactic gold
    rested at `¬pure ["E109"] = ["E109"]` (exit 1) and the flipped claim also
    exited 1. Only the first pair is evidence.)
  * Frame / fractional-permission class: VACUOUS here. Lean is referentially
    transparent — the routine reads four scalar/option inputs by value and
    returns a fresh list; there is no aliased read-only input to mutate. No
    substitute is fabricated.
  * Divergence / non-termination class: VACUOUS here. `implementation_*` is a
    total Lean `def`, so a diverging implementation cannot be written at all.
    (The nagini sibling carries no `diverge-*` case either.)
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it.

RIVAL DISAGREEMENT SETS (machine-checked, independent audit)
-----------------------------------------------------------
The observable space is finite (2*2*3*3 = 36 points), so "is this rival actually
WRONG, or merely reshaped?" is decidable by evaluation rather than by argument. A
later audit enumerated all 36 points and `#eval`ed gold != rival for each of the
eight rivals; every one differs from gold somewhere, no two rivals are the same
impl, and each witness point below lies INSIDE its own rival's disagreement set
(so no case attests to a tactic mismatch). As (itemCallable, adminHasAttr,
modelField, modelAttr):

  reject-drop-callable          5 cells, all itemCallable=true
  reject-drop-presenter         5 cells, all adminHasAttr=true
  reject-prepatch-gate          (F,F,some false,none), (F,F,some true,none)
  reject-wrong-source-relation  (F,F,some false,some true), (F,F,some true,none),
                                (F,F,some true,some false)
  reject-prefer-attr-when-both  (F,F,some false,some true), (F,F,some true,some false)
  reject-drop-e109-attr         (F,F,none,some true)
  reject-metadata-none-to-e108  (F,F,none,some false), (F,F,none,some true)
  reject-accept-unresolvable    (F,F,none,none)

Every reject case carries a `witness`: a Lean snippet negating the spec
predicate at one concrete input, checked in a file with the frozen obligation
removed. Each must (1) ELABORATE against the rival and (2) FAIL against the
frozen solution (a real discriminator, not a tautology). All witnesses below
were built BOTH ways with scripts/lean_verify.sh (rival exit 0, gold exit 1) AND
subjected to the forgery test: the same witness with its claim FLIPPED (asserting
the spec HOLDS at that point) builds against the frozen solution at exit 0. That
pair — 1 for the refutation, 0 for its negation — is what shows gold's exit code
tracks the CLAIM rather than a tactic stall. An earlier revision of the witness
tactic failed exactly this test on all eight cases; see the AUDIT FIX note above
the witness helper.

`decide` gets stuck synthesizing a `Decidable` instance through the `Id.run do`
term, so each witness unfolds the spec and drives the impl with
`simp [implementation_validateDisplayItem, Id.run, bind, pure]` — the `bind,
pure` lemmas are load-bearing, not decoration.
"""
from pathlib import Path

INSTANCE = "django__django-11551"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — the full gold impl body (unique in the file) and the proof
# markers. Every variant is produced by swapping strictly inside these regions.
# ---------------------------------------------------------------------------
_GOLD_IMPL = (
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String := Id.run do\n"
    "  if itemCallable then\n"
    "    return []\n"
    "  if adminHasAttr then\n"
    "    return []\n"
    "  -- Resolve a field for the entry: prefer the metadata lookup, then fall back to\n"
    "  -- model attribute access. If neither route yields a field, the entry is\n"
    "  -- unresolvable.\n"
    "  let mut fieldIsM2M : Bool := false\n"
    "  match modelField with\n"
    "  | some m => fieldIsM2M := m\n"
    "  | none =>\n"
    "    match modelAttr with\n"
    "    | some m => fieldIsM2M := m\n"
    "    | none => return [\"E108\"]\n"
    "  if fieldIsM2M then\n"
    "    return [\"E109\"]\n"
    "  return []"
)
assert _GOLD_IMPL in _BASE, "impl region drifted from Solution.lean"

_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"

# The theorem statement, re-emitted verbatim so the obligation survives byte for
# byte; only the tactic body below it changes (variant_scope permits this).
_THM_STMT = (
    "theorem correct_validateDisplayItem :\n"
    "    ∀ (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool),\n"
    "      problem_spec_validateDisplayItem itemCallable adminHasAttr modelField modelAttr\n"
    "        (implementation_validateDisplayItem itemCallable adminHasAttr modelField modelAttr) := by"
)
assert _THM_STMT in _BASE, "theorem statement drifted from Solution.lean"


def _swap_proof(src: str, new_proof_body: str) -> str:
    """Replace everything strictly between the proof markers (exclusive of the
    marker lines) with `new_proof_body`, which re-emits the `theorem` STATEMENT
    byte-identically — only the tactic body changes."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_proof_body + "\n" + src[e:]


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-fused-early) The two early accepts fused into `itemCallable ||
# adminHasAttr` and the field resolution reshaped into nested `match`es that
# return per branch (no shared `fieldIsM2M` local). Behaviourally identical; the
# exhaustive case-split proof re-closes.
_POS_FUSED_IMPL = (
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String := Id.run do\n"
    "  if itemCallable || adminHasAttr then\n"
    "    return []\n"
    "  match modelField with\n"
    "  | some m => if m then return [\"E109\"] else return []\n"
    "  | none =>\n"
    "    match modelAttr with\n"
    "    | some m => if m then return [\"E109\"] else return []\n"
    "    | none => return [\"E108\"]"
)
_POS_FUSED_PROOF = (
    _THM_STMT + "\n"
    "  intro itemCallable adminHasAttr modelField modelAttr\n"
    "  cases itemCallable <;> cases adminHasAttr <;>\n"
    "    cases modelField <;> cases modelAttr <;>\n"
    "    simp_all [problem_spec_validateDisplayItem, implementation_validateDisplayItem, Id.run, bind, pure]"
)
_POS_FUSED = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_FUSED_IMPL),
    _POS_FUSED_PROOF,
)

# (pos-functional-form) A pure functional expression (no `Id.run do` / `let
# mut` / `return`): an `if/else` cascade over the two early accepts, then a
# `match` resolving the field with the m2m test inlined per source.
_POS_FUNC_IMPL = (
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String :=\n"
    "  if itemCallable then []\n"
    "  else if adminHasAttr then []\n"
    "  else match modelField with\n"
    "    | some m => if m then [\"E109\"] else []\n"
    "    | none =>\n"
    "      match modelAttr with\n"
    "      | some m => if m then [\"E109\"] else []\n"
    "      | none => [\"E108\"]"
)
_POS_FUNC_PROOF = (
    _THM_STMT + "\n"
    "  intro itemCallable adminHasAttr modelField modelAttr\n"
    "  cases itemCallable <;> cases adminHasAttr <;>\n"
    "    cases modelField <;> cases modelAttr <;>\n"
    "    simp_all [problem_spec_validateDisplayItem, implementation_validateDisplayItem]"
)
_POS_FUNC = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_FUNC_IMPL),
    _POS_FUNC_PROOF,
)


# (admiss-f2p-shape) ADMISSIBILITY, landed by audit. The impl region is the
# FROZEN one, untouched — this case is about the obligation being SATISFIABLE at
# a specific input, not about any impl reshape. The proof establishes, as a
# standalone `have` and before touching the frozen goal, that the spec predicate
# holds at the exact F2P-shaped point: `itemCallable = false`, `adminHasAttr =
# false`, `modelField = some false` (a field the metadata lookup resolves, not a
# many-to-many), `modelAttr = none` (attribute access fails). `refine` splits the
# five clauses so clause (3) — the one that governs this point — is discharged by
# NAME rather than absorbed into a blob, and the result is computed by evaluation
# through the `Id.run do` block. An over-strong / unsatisfiable obligation at an
# F2P-shaped input makes this `have` unprovable, which is precisely the
# PRECOND-TOO-STRONG signal the frozen `∀`-shaped obligation cannot express by
# itself. The frozen obligation is then closed verbatim after it.
_ADMISS_PROOF = (
    _THM_STMT + "\n"
    "  have hF2P : problem_spec_validateDisplayItem false false (some false) none\n"
    "      (implementation_validateDisplayItem false false (some false) none) := by\n"
    "    unfold problem_spec_validateDisplayItem\n"
    "    refine ⟨by simp, by simp, ?_, by simp, by simp⟩\n"
    "    intro _ _ m hm\n"
    "    simp [implementation_validateDisplayItem, Id.run, bind, pure] at hm ⊢\n"
    "    simp [hm]\n"
    "  intro itemCallable adminHasAttr modelField modelAttr\n"
    "  cases itemCallable <;> cases adminHasAttr <;>\n"
    "    cases modelField <;> cases modelAttr <;>\n"
    "    simp_all [problem_spec_validateDisplayItem, implementation_validateDisplayItem, Id.run, bind, pure]"
)
_ADMISS = _swap_proof(_BASE, _ADMISS_PROOF)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# Each swaps ONLY the impl body; the frozen proof stays (it will fail to build
# against the reshaped impl — that is the expected "rejected"), and the witness
# is the real evidence.
# ===========================================================================

# (reject-drop-callable) Drop the callable early accept. Correct everywhere the
# entry is not callable; wrong on a callable entry that is otherwise
# unresolvable — it emits E108 where the spec demands []. Attacks clause (1).
_R_DROPCALL = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String := Id.run do\n"
    "  if adminHasAttr then\n"
    "    return []\n"
    "  let mut fieldIsM2M : Bool := false\n"
    "  match modelField with\n"
    "  | some m => fieldIsM2M := m\n"
    "  | none =>\n"
    "    match modelAttr with\n"
    "    | some m => fieldIsM2M := m\n"
    "    | none => return [\"E108\"]\n"
    "  if fieldIsM2M then\n"
    "    return [\"E109\"]\n"
    "  return []",
)

# (reject-drop-presenter) Drop the admin-attribute early accept. Wrong on an
# admin-attribute entry that is otherwise unresolvable. Attacks clause (2).
_R_DROPPRES = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String := Id.run do\n"
    "  if itemCallable then\n"
    "    return []\n"
    "  let mut fieldIsM2M : Bool := false\n"
    "  match modelField with\n"
    "  | some m => fieldIsM2M := m\n"
    "  | none =>\n"
    "    match modelAttr with\n"
    "    | some m => fieldIsM2M := m\n"
    "    | none => return [\"E108\"]\n"
    "  if fieldIsM2M then\n"
    "    return [\"E109\"]\n"
    "  return []",
)

# (reject-prepatch-gate) Gate the metadata lookup behind attribute access
# succeeding: consult `modelAttr` FIRST, and on `none` report unresolvable
# WITHOUT ever consulting `modelField`. So a field reachable only via the
# metadata lookup (modelField = some _, modelAttr = none) is misreported E108.
# This IS the F2P bug. Attacks clause (3).
_R_PREPATCH = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String := Id.run do\n"
    "  if itemCallable then\n"
    "    return []\n"
    "  if adminHasAttr then\n"
    "    return []\n"
    "  let mut fieldIsM2M : Bool := false\n"
    "  match modelAttr with\n"
    "  | none => return [\"E108\"]\n"
    "  | some a =>\n"
    "    match modelField with\n"
    "    | some m => fieldIsM2M := m\n"
    "    | none => fieldIsM2M := a\n"
    "  if fieldIsM2M then\n"
    "    return [\"E109\"]\n"
    "  return []",
)

# (reject-wrong-source-relation) In the metadata-field-present branch, read the
# ATTRIBUTE source's relation flag instead of the metadata field's. When the
# metadata field is a relation but attribute access reports non-relation, it
# accepts an m2m instead of emitting E109. Attacks clause (3).
#
# AUDIT NOTE: this rival has TWO wrong arms in the metadata-present branch — the
# wrong-source READ (`some a => fieldIsM2M := a`) and, on `modelAttr = none`, a
# HARDCODED non-relation. Its witness must land on the first, or the case attests
# to the hardcode while the rationale claims the misread. See _WIT_WRONGSRC.
_R_WRONGSRC = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String := Id.run do\n"
    "  if itemCallable then\n"
    "    return []\n"
    "  if adminHasAttr then\n"
    "    return []\n"
    "  let mut fieldIsM2M : Bool := false\n"
    "  match modelField with\n"
    "  | some _ =>\n"
    "    match modelAttr with\n"
    "    | some a => fieldIsM2M := a\n"
    "    | none => fieldIsM2M := false\n"
    "  | none =>\n"
    "    match modelAttr with\n"
    "    | some m => fieldIsM2M := m\n"
    "    | none => return [\"E108\"]\n"
    "  if fieldIsM2M then\n"
    "    return [\"E109\"]\n"
    "  return []",
)

# (reject-drop-e109-attr) On the attribute-resolved branch, hardcode
# non-relation. An m2m reachable only via attribute access is accepted instead
# of diagnosed E109. Attacks clause (4).
_R_DROPE109 = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String := Id.run do\n"
    "  if itemCallable then\n"
    "    return []\n"
    "  if adminHasAttr then\n"
    "    return []\n"
    "  let mut fieldIsM2M : Bool := false\n"
    "  match modelField with\n"
    "  | some m => fieldIsM2M := m\n"
    "  | none =>\n"
    "    match modelAttr with\n"
    "    | some _ => fieldIsM2M := false\n"
    "    | none => return [\"E108\"]\n"
    "  if fieldIsM2M then\n"
    "    return [\"E109\"]\n"
    "  return []",
)

# (reject-metadata-none-to-e108) Whenever the metadata lookup yields nothing,
# report unresolvable — ignoring attribute access entirely. Wrong on any entry
# resolvable only via attribute access. Reverses the fix. Attacks clause (4).
_R_META108 = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String := Id.run do\n"
    "  if itemCallable then\n"
    "    return []\n"
    "  if adminHasAttr then\n"
    "    return []\n"
    "  let mut fieldIsM2M : Bool := false\n"
    "  match modelField with\n"
    "  | some m => fieldIsM2M := m\n"
    "  | none => return [\"E108\"]\n"
    "  if fieldIsM2M then\n"
    "    return [\"E109\"]\n"
    "  return []",
)

# (reject-accept-unresolvable) Never emit the unresolvable diagnostic: return []
# when neither route yields a field. Attacks clause (5).
_R_DROPE108 = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String := Id.run do\n"
    "  if itemCallable then\n"
    "    return []\n"
    "  if adminHasAttr then\n"
    "    return []\n"
    "  let mut fieldIsM2M : Bool := false\n"
    "  match modelField with\n"
    "  | some m => fieldIsM2M := m\n"
    "  | none =>\n"
    "    match modelAttr with\n"
    "    | some m => fieldIsM2M := m\n"
    "    | none => return []\n"
    "  if fieldIsM2M then\n"
    "    return [\"E109\"]\n"
    "  return []",
)


# (reject-prefer-attr-when-both) PRECEDENCE rival, added by audit. Correct
# everywhere exactly ONE route resolves, and correct when neither does; wrong
# only where BOTH routes resolve and disagree on the relation flag — it lets the
# attribute source's flag win, where the spec's clause (3) makes the metadata
# field's flag decide unconditionally once `modelField = some m`. Every other
# rival in this battery is observationally equal to gold across that whole
# 16-cell region, so without this case the precedence content of clause (3) is
# asserted by the spec and probed by nothing.
_R_PREFERATTR = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_validateDisplayItem\n"
    "    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)\n"
    "    : List String := Id.run do\n"
    "  if itemCallable then\n"
    "    return []\n"
    "  if adminHasAttr then\n"
    "    return []\n"
    "  let mut fieldIsM2M : Bool := false\n"
    "  match modelField, modelAttr with\n"
    "  | some _, some a => fieldIsM2M := a\n"
    "  | some m, none => fieldIsM2M := m\n"
    "  | none, some a => fieldIsM2M := a\n"
    "  | none, none => return [\"E108\"]\n"
    "  if fieldIsM2M then\n"
    "    return [\"E109\"]\n"
    "  return []",
)


# --- witnesses (checked with the obligation removed) -----------------------
# Each negates the spec predicate at one concrete input. The carrier is
# transparent, so no witness binds a hypothesis (nothing to be inconsistent);
# `decide` stalls on the `Decidable` instance through `Id.run do`, so the impl
# is driven by unfolding the spec and simping the impl.
#
# AUDIT FIX (witness tactic — this was a HOLLOW-PASS defect on all eight reject
# cases). The tactic previously read `simp [implementation_validateDisplayItem,
# Id.run]`, omitting the `bind, pure` lemmas the frozen proof script itself
# carries. Without them `simp` unfolds the `Id.run do` block only as far as a
# residual `pure <lit>` application and STALLS: the gold-side goal came to rest
# at `⊢ ¬pure [] = []` and the build exited 1 — which the gate read as "the
# witness fails on gold, so it discriminates".
#
# It did not. The forgery test (attack B′) shows the stall was insensitive to
# what was being CLAIMED: building the FLIPPED witness (assert the spec HOLDS at
# the same point, i.e. that gold is CORRECT there — a true statement) against the
# frozen solution also exited 1, resting at `⊢ pure [] = []`. Same tactic, same
# stall, opposite claim, identical exit code. Gold's exit code therefore carried
# zero information about the claim, so the gate would equally have recorded
# `rejected` for a witness asserting gold is correct. Measured for all 8 cases.
#
# Adding `bind, pure` lets `simp` drive the `Id` monad to the literal, so the
# refutation is decided rather than stalled. Rebuilt all 8 both ways plus the
# forgery: witness-on-rival exit 0, witness-on-gold exit 1 resting at the
# semantic residue `⊢ False`, and flipped-claim-on-gold exit 0 (it now PROVES
# gold correct at the point). That exit-code pair (1 vs 0) is what makes the
# gold-side failure evidence about the spec instead of about the tactic.

def _wit(itemCallable: str, adminHasAttr: str,
         modelField: str, modelAttr: str) -> str:
    args = f"{itemCallable} {adminHasAttr} {modelField} {modelAttr}"
    return (
        "example : ¬ problem_spec_validateDisplayItem\n"
        f"    {args}\n"
        "    (implementation_validateDisplayItem\n"
        f"      {args}) := by\n"
        "  unfold problem_spec_validateDisplayItem\n"
        "  simp [implementation_validateDisplayItem, Id.run, bind, pure]"
    )


# Callable, otherwise unresolvable: gold => [] (clause 1), rival => E108.
_WIT_DROPCALL = _wit("true", "false", "none", "none")
# Admin attr, otherwise unresolvable: gold => [] (clause 2), rival => E108.
_WIT_DROPPRES = _wit("false", "true", "none", "none")
# Metadata field present & non-relation, attribute access fails (the F2P shape):
# gold => [] (clause 3), rival (prepatch gate) => E108.
_WIT_PREPATCH = _wit("false", "false", "(some false)", "none")
# Metadata field is a relation, attribute access yields a NON-relation: gold
# follows the metadata flag => E109 (clause 3); the wrong-source rival reads the
# attribute flag (false) => []. `modelAttr` is deliberately `some false` and NOT
# `none`: at `none` the rival takes its hardcoded-non-relation arm, so the
# witness would refute it for a reason other than the misread its rationale
# claims. This is also the only witness in the battery landing in the
# BOTH-LOOKUPS-SUCCEED region, where clause (3)'s precedence content lives.
_WIT_WRONGSRC = _wit("false", "false", "(some true)", "(some false)")
# No metadata field; attribute access yields a relation: gold => E109 (clause 4),
# rival (drop e109 on attr path) => [].
_WIT_DROPE109 = _wit("false", "false", "none", "(some true)")
# No metadata field; attribute access yields a non-relation: gold => [] (clause
# 4), rival (metadata-none-to-108) => E108.
_WIT_META108 = _wit("false", "false", "none", "(some false)")
# Neither route yields a field: gold => E108 (clause 5), rival (accept) => [].
_WIT_DROPE108 = _wit("false", "false", "none", "none")
# Both routes resolve and DISAGREE: metadata field is a non-relation, attribute
# access yields a relation. gold => [] (clause 3 pins the result to the metadata
# flag alone), precedence rival lets the attribute flag win => E109. The opposite
# disagreement is already covered by _WIT_WRONGSRC.
_WIT_PREFERATTR = _wit("false", "false", "(some false)", "(some true)")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-fused-early", "kind": "soundness", "expect": "verify",
     "module": _POS_FUSED,
     "rationale": "a structurally-different but correct impl: the two early "
                  "accepts fused into `itemCallable || adminHasAttr` and the "
                  "field resolution reshaped into nested per-branch `match` "
                  "returns (no shared local). Proof re-closed by exhaustive "
                  "case split over the four observations. Verifies against "
                  "clauses (1)-(5) or the spec is over-fit to the frozen impl "
                  "shape => SPEC-TOO-STRONG."},
    {"id": "pos-functional-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNC,
     "rationale": "a second correct impl in a different shape: a pure "
                  "functional `if/else` + `match` expression (no `Id.run do` / "
                  "`let mut` / `return`), the many-to-many test inlined per "
                  "resolution source. Proof re-closed. The carrier is "
                  "transparent, so there is no oracle to echo; this stands "
                  "purely as a soundness positive of a different impl form. If "
                  "it fails to verify the spec is over-fit => SPEC-TOO-STRONG."},
    {"id": "admiss-f2p-shape", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "PRECOND-TOO-STRONG probe, landed by audit (the port had "
                  "recorded this lane as vacuous because the frozen obligation "
                  "carries no precondition hypothesis — the wrong reason). The "
                  "impl region is the frozen one, untouched; what this case adds "
                  "is a standalone `have` discharging the spec predicate AT the "
                  "concrete F2P-shaped input (itemCallable=false, "
                  "adminHasAttr=false, modelField=some false, modelAttr=none) by "
                  "evaluation, with clause (3) named via `refine` rather than "
                  "absorbed into the exhaustive-case-split blob, BEFORE closing "
                  "the frozen obligation verbatim. On a total carrier that is the "
                  "analogue of an over-strong precondition: the obligation being "
                  "unsatisfiable at exactly an F2P-shaped point. The positives "
                  "cannot substitute — they discharge all 36 cells as one "
                  "normal-form blob and so never exhibit any individual cell's "
                  "clause as independently satisfiable. If this `have` fails, the "
                  "spec admits no F2P-shaped input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "reject-drop-callable", "kind": "uniqueness", "expect": "reject",
     "module": _R_DROPCALL, "witness": _WIT_DROPCALL,
     "refinement": "its faithful real patch drops the guard that accepts a "
                   "callable listed entry, so a callable display entry that is "
                   "not otherwise resolvable is reported unresolvable; the "
                   "P2P cases that list a callable (a bound method / custom "
                   "callable) would then fail validation — it would NOT "
                   "resolve, so a verifying rival is a true "
                   "verify-does-not-imply-resolve break.",
     "rationale": "attacks clause (1) (itemCallable = true => []). The ONLY "
                  "rival that varies `itemCallable = true`; every other witness "
                  "holds it false, so a rival mishandling only the callable "
                  "observation would otherwise go unnoticed. Witness "
                  "itemCallable=true, otherwise unresolvable: gold => [], rival "
                  "=> E108. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "reject-drop-presenter", "kind": "uniqueness", "expect": "reject",
     "module": _R_DROPPRES, "witness": _WIT_DROPPRES,
     "refinement": "its faithful real patch drops the guard that accepts an "
                   "entry exposed as an attribute of the admin object; a valid "
                   "admin-attribute entry would then be reported unresolvable, "
                   "failing the P2P valid cases that list such an attribute — "
                   "it would NOT resolve.",
     "rationale": "attacks clause (2) (not callable, adminHasAttr = true => "
                  "[]). The ONLY rival that varies `adminHasAttr = true`. "
                  "Witness adminHasAttr=true, otherwise unresolvable: gold => "
                  "[], rival => E108. Built both ways (rival 0, gold 1)."},
    {"id": "reject-prepatch-gate", "kind": "uniqueness", "expect": "reject",
     "module": _R_PREPATCH, "witness": _WIT_PREPATCH,
     "refinement": "this is the pre-patch behaviour: it consults model "
                   "attribute access FIRST and, when that fails, reports the "
                   "entry unresolvable WITHOUT trying the metadata field "
                   "lookup. A field reachable only via the metadata lookup "
                   "(attribute access raising) is then misreported "
                   "unresolvable — exactly the F2P shape "
                   "(test_valid_field_accessible_via_instance). Its faithful "
                   "patch fails that F2P — it does NOT resolve.",
     "rationale": "attacks clause (3) (modelField = some m => E109 if m else "
                  "[]). Witness modelField=some false (present, non-relation), "
                  "modelAttr=none: gold => [], rival => E108. Varies the "
                  "`modelField`/`modelAttr` binders. Built both ways (rival 0, "
                  "gold 1)."},
    {"id": "reject-wrong-source-relation", "kind": "uniqueness",
     "expect": "reject",
     "module": _R_WRONGSRC, "witness": _WIT_WRONGSRC,
     "refinement": "its faithful real patch tests the many-to-many property of "
                   "the value obtained by attribute access rather than of the "
                   "metadata field that was actually resolved; when the "
                   "metadata field is a many-to-many relation but attribute "
                   "access reports otherwise (or fails), it accepts a "
                   "many-to-many field and misses the diagnostic, diverging "
                   "from gold on the relation domain — it would NOT resolve.",
     "rationale": "attacks clause (3): the result must be (E109 if the METADATA "
                  "field's flag else []); this reads the attribute source's "
                  "flag. Witness modelField=some true (relation), modelAttr="
                  "some false (non-relation): gold follows the metadata flag => "
                  "E109, rival reads the attribute flag => []. The witness point "
                  "is chosen so the rival takes its wrong-source READ arm; at "
                  "modelAttr=none it would instead take a hardcoded-non-relation "
                  "arm and refute for a different reason than claimed here. "
                  "Built both ways (rival exit 0, gold exit 1)."},
    {"id": "reject-prefer-attr-when-both", "kind": "uniqueness",
     "expect": "reject",
     "module": _R_PREFERATTR, "witness": _WIT_PREFERATTR,
     "refinement": "its faithful real patch resolves a field by BOTH routes and "
                   "then lets the model-attribute value's relation property "
                   "decide, rather than the metadata field's once the metadata "
                   "lookup has succeeded. For any entry the metadata resolves to "
                   "a plain field while attribute access on the model class "
                   "yields a many-to-many-valued descriptor (or vice versa), it "
                   "reports the opposite diagnostic to gold — emitting the "
                   "many-to-many diagnostic for an acceptable column, or "
                   "accepting a many-to-many one. The P2P cases asserting each "
                   "diagnostic on such a column would fail — it would NOT "
                   "resolve.",
     "rationale": "attacks the PRECEDENCE content of clause (3): once "
                  "modelField = some m the result is pinned to (E109 if m else "
                  "[]) with modelAttr irrelevant. Every other rival here is "
                  "observationally EQUAL to gold on all 16 both-lookups-succeed "
                  "cells, so this clause's precedence was previously asserted "
                  "and unprobed. Witness modelField=some false, modelAttr=some "
                  "true: gold => [], rival => E109. Built both ways (rival exit "
                  "0, gold exit 1)."},
    {"id": "reject-drop-e109-attr", "kind": "uniqueness", "expect": "reject",
     "module": _R_DROPE109, "witness": _WIT_DROPE109,
     "refinement": "its faithful real patch skips the many-to-many test on a "
                   "field obtained by attribute access, so a many-to-many "
                   "reachable only via attribute access is accepted instead of "
                   "diagnosed; it diverges from gold on the attribute-relation "
                   "sub-domain — it would NOT resolve.",
     "rationale": "attacks clause (4) (modelField = none, modelAttr = some m => "
                  "E109 if m else []); this is always non-relation on that "
                  "path. Witness modelField=none, modelAttr=some true: gold => "
                  "E109, rival => []. Built both ways (rival 0, gold 1)."},
    {"id": "reject-metadata-none-to-e108", "kind": "uniqueness",
     "expect": "reject",
     "module": _R_META108, "witness": _WIT_META108,
     "refinement": "ignoring the attribute-access fallback means any entry "
                   "whose metadata lookup finds no field is reported "
                   "unresolvable even when attribute access resolves it — "
                   "wrong for any attribute-only field, and it REVERSES the "
                   "very fix under test (the fallback the patch added). The "
                   "F2P / related P2P would not resolve.",
     "rationale": "attacks clause (4) (modelField = none, modelAttr = some m => "
                  "E109 if m else []); returns E108 there. Witness "
                  "modelField=none, modelAttr=some false: gold => [], rival => "
                  "E108. Distinct from prepatch-gate: that rival is refuted at "
                  "modelField=some/modelAttr=none, this one at "
                  "modelField=none/modelAttr=some. Built both ways (rival 0, "
                  "gold 1)."},
    {"id": "reject-accept-unresolvable", "kind": "uniqueness",
     "expect": "reject",
     "module": _R_DROPE108, "witness": _WIT_DROPE108,
     "refinement": "its faithful real patch omits the unresolvable diagnostic "
                   "entirely, silently accepting an entry that resolves to no "
                   "field by any route; the P2P cases that assert the "
                   "unresolvable diagnostic is emitted would fail — it would "
                   "NOT resolve.",
     "rationale": "attacks clause (5) (both lookups none => E108); returns [] "
                  "there. Witness modelField=none, modelAttr=none: gold => "
                  "E108, rival => []. Built both ways (rival 0, gold 1)."},
]

# --------------------------------------------------------------------------
# AXIOM TESTS — none. The axiom lane is G-AX's job; this gate ignores it.
# --------------------------------------------------------------------------
AXIOM_TESTS = []
