"""properties.py — PBT falsification manifest for django__django-11163 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the positive controls, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
The modeled function projects a sequence of field records into an ordered
association list of `(name, value)` pairs:

    implementation_modelToDict {α}
        (fields exclude : Option (List String))
        (fs : List (FieldRec α)) : List (String × α)

pinned by the single load-bearing clause

    result = (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val))

`keep` is a FULLY TRANSPARENT deep model (a `Bool` conjunction of three
independent survival conditions); the carrier has NO opaque callee, so every
rival is refutable by `decide` at a concrete input over `α := Nat` — no carrier
conditioning is needed, hence no witness binds a hypothesis (nothing to be
inconsistent).

The clause pins the projection against every input binder:

  * `editable` — a field survives only if editable (the `f.editable` conjunct);
  * `fields` — the OPTIONAL inclusion selection, whose three regions carry
    different meaning: ABSENT (`none`) includes all; PRESENT-NON-EMPTY includes
    only named fields; PRESENT-EMPTY (`some []`) includes NOTHING. The salient
    distinction is absent-vs-present-empty (`none` ≠ `some []`);
  * `exclude` — the OPTIONAL exclusion list bars a field named in it;
  * `fs` order / multiplicity — survivors are kept in original sequence order,
    each paired with its OWN name and value; `.filter` then `.map` pins both the
    per-element identity and the position. Two same-named fields both survive
    (the result is a SEQUENCE, not a keyed map), and the two options are
    conjoined, so they are independent: a field the selection names is still
    barred if the exclusion names it too.

Frame discipline: Lean is referentially transparent, so the fractional-permission
class the nagini sibling carried (writing a read-only input carrier to coerce the
result) is genuinely VACUOUS here — the inputs cannot be mutated in place. The
analogue that DOES survive is that the result is pinned entirely to the inputs by
an equality, so a rival that reorders or drops survivors is refuted by the
equality itself (see `weak-drop-first`). The divergence / non-termination class
is likewise vacuous on lean: `implementation_modelToDict` is a total `def`, so a
diverging impl cannot be written at all.

PORTING NOTES (which nagini cases port, which are omitted)
----------------------------------------------------------
The nagini sibling models a four-argument `project_record` over parallel int
streams with a front-recursive `projection` fold; its adversarial ARGUMENTS port
directly to this carrier even though the mechanics differ.

  * nagini `pos-reorder` / `pos-localvar` (structurally-different CORRECT impls)
    -> `pos-functional-form` (pure functional expression, definitionally the
    spec, `rfl` closes) and `pos-combined-guard` (imperative do-loop whose keep
    test is the single `keep` predicate; proof re-closed by Route-B induction on
    the accumulator). Two distinct correct impl shapes; if either fails to verify
    the spec is over-fit (SPEC-TOO-STRONG).
  * nagini `weak-truthiness` (THE headline pre-patch bug) -> `weak-truthiness`:
    a present-empty selection treated like an absent one (keeps all). Attacks the
    `fields = some []` region.
  * nagini `weak-restrict-none-drops` -> `weak-restrict-none`: an absent selection
    treated as a membership filter (keeps nothing). Attacks the `fields = none`
    region.
  * added `weak-include-keepall`: a present NON-EMPTY selection ignored entirely
    (keeps every editable, non-excluded field). Attacks the `fields = some [x]`
    region — the only rival that probes a present selection with a name NOT in
    it, which the other two `fields` rivals never exercise.
  * nagini `weak-drop-editability` -> `weak-drop-editability`: drops the
    editability conjunct. Attacks the `editable` binder.
  * added `weak-drop-exclusion`: drops the exclusion conjunct. Attacks the
    `exclude` binder — no nagini `blocked`-attacking value rival existed, but the
    modeled spec has an independent exclusion clause that must be defended. It
    reaches only the present-NON-EMPTY region, though: with the block dropped the
    rival AGREES with the spec on every absent or empty exclusion, hence
    `weak-exclude-invert` below.
  * added `weak-exclude-invert` (audit): inverts the present exclusion guard's
    sense, refuted at `exclude = some []`. The present-but-EMPTY exclusion region
    is a distinct point of the clause — absent and empty must both bar NOTHING —
    and no drop-style rival can reach it, since dropping the guard is correct
    there. A separate binder region from the `fields = some []` one that
    `weak-truthiness` attacks.
  * added `weak-value-misalign` (audit): pairs each survivor with the FIRST source
    field's value rather than its own, leaving the survivor set, the order and
    every name untouched. Attacks the VALUE half of `(f.name, f.val)`, the one
    output component every other rival leaves intact — a rival refutable ONLY
    through `f.val` is what pins the per-element value identity.
  * added `weak-name-misalign` (audit-2): the mirror of the above on the NAME
    half — every survivor carries the FIRST source field's name, with the
    survivor set, the order and every value intact. `weak-value-misalign` pins
    only the second projection of the pair; nothing pinned the first.
  * added `weak-dedup-by-name` (audit-2): emits a surviving field only if no
    earlier survivor shares its name, i.e. treats the result as keyed rather than
    as a sequence. Refuted only at a source carrying TWO fields of the same name,
    a MULTIPLICITY point no other rival reaches (every other rival's witness has
    pairwise-distinct names, so `.filter`-then-`.map` preserving duplicates was
    unprobed).
  * added `weak-include-beats-exclude` (audit-2): consults the exclusion list
    only when the inclusion selection is ABSENT, so a present selection silently
    overrides the exclusion. Refuted only where BOTH options are present at once
    — the independence of the two options, which every other rival leaves
    untested because each holds one of the two at `none`.
  * added `weak-order-reverse` (audit-2): prepends instead of appending, so
    survivors come out in reverse source order with the set, the names and the
    values all correct. `weak-drop-first` attacks which fields survive at a
    position; this attacks the ORDER of a survivor set that is otherwise exactly
    right.
  * nagini `weak-partial-first` -> `weak-drop-first`: never keeps the first
    source field. Attacks the per-element source-order / position clause.
  * nagini `frame-mut-names` / `frame-mut-edit` (fractional-permission mutation)
    are OMITTED as VACUOUS: Lean is referentially transparent, so a read-only
    input cannot be written; there is no permission system to violate. Not a
    dropped case — the class does not exist on this carrier.
  * nagini `admiss-fshaped` -> `admiss-ground-empty-options`. An earlier revision
    of this manifest recorded the class as VACUOUS because the lean obligation is
    `∀ {α} fields exclude fs, problem_spec …` with no precondition hypothesis.
    That reason was WRONG, and it is corrected here: "no precondition binder to
    over-constrain" is not the same as "nothing to test". On a total carrier the
    analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at
    exactly an F2P-shaped concrete input — a spec that is only vacuously true, or
    true only in the abstract, would fail to discharge there. So the positive
    discharges the spec predicate BY EVALUATION (`decide`) at the two ground
    inputs the discriminating behavior lives at (a present-empty selection, and a
    present-empty exclusion, each over a two-field editable source) as `have`s,
    and only then closes the frozen obligation verbatim. Measured: it verifies.
    If it did not, the modeled behavior would be unsatisfiable at the very input
    the added assertions exercise.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it.

Every reject case carries a `witness`: a Lean snippet negating the spec predicate
at one concrete input over `α := Nat`, checked in a file with the frozen
obligation removed. Each must (1) ELABORATE against the rival and (2) FAIL against
the frozen solution (a real discriminator, not a tautology). All witnesses below
were built BOTH ways with scripts/lean_verify.sh (rival exit 0, gold exit 1). The
carrier is transparent, so `decide` closes and no witness binds a hypothesis.
"""
from pathlib import Path

INSTANCE = "django__django-11163"

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
# Region landmarks — all strictly INSIDE the impl region (and, for positives,
# the proof body) of Solution.lean. Each is verified unique across the file.
# ---------------------------------------------------------------------------

# The full gold impl body (Id.run do block).
_GOLD_IMPL = """def implementation_modelToDict {α : Type} (fields exclude : Option (List String))
    (fs : List (FieldRec α)) : List (String × α) := Id.run do
  let mut data : List (String × α) := []
  for f in fs do
    -- skip non-editable fields
    if !f.editable then
      continue
    -- a present inclusion selection (even if empty) must name the field
    if let some sel := fields then
      if !(sel.contains f.name) then
        continue
    -- a present exclusion list bars the field if it names it
    if let some ex := exclude then
      if ex.contains f.name then
        continue
    data := data ++ [(f.name, f.val)]
  return data"""

# Sub-blocks (each unique in the file — the proof region spells these differently).
_EDIT_BLOCK = """    -- skip non-editable fields
    if !f.editable then
      continue
"""
_INCL_BLOCK = """    if let some sel := fields then
      if !(sel.contains f.name) then
        continue
"""
_EXCL_BLOCK = """    -- a present exclusion list bars the field if it names it
    if let some ex := exclude then
      if ex.contains f.name then
        continue
"""

_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"


def _swap_proof(src: str, new_body: str) -> str:
    """Replace everything strictly between the proof markers with `new_body`.
    The `theorem correct_modelToDict` STATEMENT is re-emitted byte-identically
    inside `new_body`; only the tactic body changes, which variant_scope permits."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_body + "\n" + src[e:]


# Sanity: the gold impl must appear exactly once.
assert _GOLD_IMPL in _BASE, "drift: _GOLD_IMPL not byte-identical to Solution.lean impl region"
assert _BASE.count(_GOLD_IMPL) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-functional-form) A structurally different CORRECT impl: a pure functional
# expression (no `Id.run do` / `for` / `mut`) whose body IS the reference
# projection, so `correct_` collapses to `rfl`. The carrier is transparent, so
# there is no oracle to echo; this stands purely as a soundness positive of a
# different impl form. If it fails to verify the spec is over-fit to the
# imperative shape => SPEC-TOO-STRONG.
_POS_FUNCTIONAL_IMPL = """def implementation_modelToDict {α : Type} (fields exclude : Option (List String))
    (fs : List (FieldRec α)) : List (String × α) :=
  (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val))"""
_POS_FUNCTIONAL_PROOF = """theorem correct_modelToDict :
    ∀ {α : Type} (fields exclude : Option (List String)) (fs : List (FieldRec α)),
      problem_spec_modelToDict fields exclude fs
        (implementation_modelToDict fields exclude fs) := by
  intro α fields exclude fs
  rfl"""
_POS_FUNCTIONAL = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_FUNCTIONAL_IMPL),
    _POS_FUNCTIONAL_PROOF,
)

# (pos-combined-guard) A second CORRECT impl: the same imperative do-loop, but the
# three keep conjuncts are hoisted into the single `keep` predicate rather than
# spelled as three early-`continue` guards. Semantically identical; the executable
# shape differs. Proof re-closed by Route-B induction on the accumulator
# (`List.forIn_cons`, case-split on the `keep` value). If it fails to verify the
# spec is over-fit to the three-guard shape => SPEC-TOO-STRONG.
_POS_COMBINED_IMPL = """def implementation_modelToDict {α : Type} (fields exclude : Option (List String))
    (fs : List (FieldRec α)) : List (String × α) := Id.run do
  let mut data : List (String × α) := []
  for f in fs do
    if keep fields exclude f then
      data := data ++ [(f.name, f.val)]
  return data"""
_POS_COMBINED_PROOF = """theorem correct_modelToDict :
    ∀ {α : Type} (fields exclude : Option (List String)) (fs : List (FieldRec α)),
      problem_spec_modelToDict fields exclude fs
        (implementation_modelToDict fields exclude fs) := by
  intro α fields exclude fs
  unfold problem_spec_modelToDict implementation_modelToDict
  suffices h : ∀ (init : List (String × α)),
      (forIn fs init fun f r =>
        (if keep fields exclude f = true then pure (ForInStep.yield (r ++ [(f.name, f.val)]))
         else pure (ForInStep.yield r)) : Id _)
        = init ++ (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val)) by
    have := h []
    simpa using this
  intro init
  induction fs generalizing init with
  | nil => simp [List.forIn_nil]; rfl
  | cons f fs ih =>
    rw [List.forIn_cons]
    simp only [List.filter_cons]
    by_cases hk : keep fields exclude f = true
    · simp [hk, ih, List.append_assoc]
    · simp [hk, ih]"""
_POS_COMBINED = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_COMBINED_IMPL),
    _POS_COMBINED_PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (weak-truthiness) THE headline pre-patch bug: a present-empty selection is
# treated like an absent one (keeps everything) via an `isEmpty` short-circuit.
# Correct on every input EXCEPT `fields = some []`.
_RIVAL_TRUTHINESS = _swap(_BASE, _INCL_BLOCK,
"""    if let some sel := fields then
      if !sel.isEmpty && !(sel.contains f.name) then
        continue
""")

# (weak-restrict-none) An ABSENT selection is treated as a membership filter over
# the empty list (keeps nothing). Correct only when a present selection covers the
# kept names; wrong on the common `fields = none` case.
_RIVAL_RESTRICT_NONE = _swap(_BASE, _INCL_BLOCK,
"""    let sel := fields.getD []
    if !(sel.contains f.name) then
      continue
""")

# (weak-include-keepall) A PRESENT selection is ignored entirely (the inclusion
# block is dropped), so every editable, non-excluded field survives regardless of
# whether the selection names it. Correct on `fields = none`; wrong on any present
# selection with a name NOT in it.
_RIVAL_INCLUDE_KEEPALL = _swap(_BASE, _INCL_BLOCK, "")

# (weak-drop-editability) Drops the editability skip; a non-editable field that
# passes the selection/exclusion filters survives.
_RIVAL_DROP_EDIT = _swap(_BASE, _EDIT_BLOCK, "")

# (weak-drop-exclusion) Drops the exclusion filter; a field named in the exclusion
# list survives.
_RIVAL_DROP_EXCL = _swap(_BASE, _EXCL_BLOCK, "")

# (weak-exclude-invert) The PRESENT exclusion guard's sense is inverted: a present
# exclusion list is read as an INCLUSION filter, so a field survives only if the
# list names it. Refuted at `exclude = some []`, the ONLY point in the exclusion
# binder that `weak-drop-exclusion` cannot reach: dropping the exclusion block
# agrees with the spec on every empty/absent exclusion, so the present-but-EMPTY
# exclusion region (absent-and-empty both bar nothing) was previously unprobed.
_RIVAL_EXCL_INVERT = _swap(_BASE, _EXCL_BLOCK,
"""    -- a present exclusion list bars the field if it names it
    if let some ex := exclude then
      if !ex.contains f.name then
        continue
""")

# (weak-value-misalign) Each survivor is paired with the FIRST source field's
# value instead of its OWN. The name projection and the survivor set/order are
# untouched, so this is refutable ONLY through the value component of the pair —
# the one half of `(f.name, f.val)` no other rival perturbs.
_RIVAL_VALUE_MISALIGN = _swap(_BASE, "    data := data ++ [(f.name, f.val)]",
"""    data := data ++ [(f.name, (match fs.head? with | some g => g.val | none => f.val))]""")

# (weak-name-misalign) The mirror of weak-value-misalign on the NAME half: every
# survivor carries the FIRST source field's name instead of its own, with the
# survivor set, the order and every VALUE untouched. Refutable only through the
# first projection of `(f.name, f.val)`, which weak-value-misalign does not pin.
_RIVAL_NAME_MISALIGN = _swap(_BASE, "    data := data ++ [(f.name, f.val)]",
"""    data := data ++ [((match fs.head? with | some g => g.name | none => f.name), f.val)]""")

# (weak-dedup-by-name) Emits a surviving field only when no earlier survivor
# already carries its name — the result is treated as KEYED rather than as a
# sequence. Agrees with the spec on every source whose names are pairwise
# distinct (which is every other witness in this battery), and is refuted only at
# a source carrying two fields of the SAME name, where `.filter`-then-`.map`
# keeps both. The multiplicity point of the clause.
_RIVAL_DEDUP_NAME = _swap(_BASE, "    data := data ++ [(f.name, f.val)]",
"""    if !(data.any (fun p => p.1 == f.name)) then
      data := data ++ [(f.name, f.val)]""")

# (weak-include-beats-exclude) The exclusion list is consulted ONLY when the
# inclusion selection is absent, so a present selection silently overrides a
# present exclusion. The two options are INDEPENDENT in the spec (`keep` conjoins
# them), and every other rival holds one of the two at `none`, so their
# independence — a field named in BOTH must still be barred — was unprobed.
_RIVAL_INCL_BEATS_EXCL = _swap(_BASE, _EXCL_BLOCK,
"""    -- a present exclusion list bars the field if it names it
    if fields.isNone then
      if let some ex := exclude then
        if ex.contains f.name then
          continue
""")

# (weak-order-reverse) Prepends rather than appends, so the survivor SET, every
# name and every value are exactly right and only the ORDER is reversed. Attacks
# the sequence-order half of the clause that `.filter`-then-`.map` pins; the
# other order rival (weak-drop-first) changes WHICH fields survive.
_RIVAL_ORDER_REVERSE = _swap(_BASE, "    data := data ++ [(f.name, f.val)]",
"""    data := [(f.name, f.val)] ++ data""")

# (weak-drop-first) Never keeps the first source field (an `idx != 0` guard).
# Correct on every input whose first field would not survive; wrong when the head
# survives all three filters — attacks per-element source-order / position.
_RIVAL_DROP_FIRST = _swap(_BASE, _GOLD_IMPL,
"""def implementation_modelToDict {α : Type} (fields exclude : Option (List String))
    (fs : List (FieldRec α)) : List (String × α) := Id.run do
  let mut data : List (String × α) := []
  let mut idx : Nat := 0
  for f in fs do
    if idx != 0 && keep fields exclude f then
      data := data ++ [(f.name, f.val)]
    idx := idx + 1
  return data""")


# --- witnesses (checked with the obligation removed) -----------------------
def _wit(fields: str, exclude: str, fs: str) -> str:
    return (
        "example : ¬ problem_spec_modelToDict (α := Nat)\n"
        f"    ({fields}) ({exclude})\n"
        f"    {fs}\n"
        "    (implementation_modelToDict (α := Nat)\n"
        f"      ({fields}) ({exclude})\n"
        f"      {fs}) := by\n"
        "  unfold problem_spec_modelToDict implementation_modelToDict\n"
        "  decide"
    )


# present-empty selection: gold keeps NOTHING, rival keeps the editable field.
_WIT_TRUTHINESS = _wit('some []', 'none',
    '[{ name := "a", editable := true, val := (1 : Nat) }]')
# absent selection: gold keeps the field, rival keeps nothing.
_WIT_RESTRICT_NONE = _wit('none', 'none',
    '[{ name := "a", editable := true, val := (1 : Nat) }]')
# present selection NOT naming the field: gold keeps nothing, rival keeps it.
_WIT_INCLUDE_KEEPALL = _wit('some ["a"]', 'none',
    '[{ name := "b", editable := true, val := (2 : Nat) }]')
# non-editable field: gold drops it, rival keeps it.
_WIT_DROP_EDIT = _wit('none', 'none',
    '[{ name := "a", editable := false, val := (1 : Nat) }]')
# field named in exclusion: gold drops it, rival keeps it.
_WIT_DROP_EXCL = _wit('none', 'some ["a"]',
    '[{ name := "a", editable := true, val := (1 : Nat) }]')
# present-but-EMPTY exclusion: gold bars nothing (keeps the field), the inverted
# rival keeps only fields the list names, so it keeps nothing.
_WIT_EXCL_INVERT = _wit('none', 'some []',
    '[{ name := "a", editable := true, val := (1 : Nat) }]')
# two survivors with DISTINCT values: gold pairs each with its own value, the
# rival pairs both with the head field's value (so "b" is paired with 1, not 2).
_WIT_VALUE_MISALIGN = _wit('none', 'none',
    '[{ name := "a", editable := true, val := (1 : Nat) }, '
    '{ name := "b", editable := true, val := (2 : Nat) }]')
# two survivors with DISTINCT names: gold pairs each with its own name, the rival
# gives both the head field's name (so the second pair is ("a",2), not ("b",2)).
_WIT_NAME_MISALIGN = _wit('none', 'none',
    '[{ name := "a", editable := true, val := (1 : Nat) }, '
    '{ name := "b", editable := true, val := (2 : Nat) }]')
# two survivors sharing ONE name: gold keeps both pairs, the deduping rival keeps
# only the first — a multiplicity point no distinct-name witness can reach.
_WIT_DEDUP_NAME = _wit('none', 'none',
    '[{ name := "a", editable := true, val := (1 : Nat) }, '
    '{ name := "a", editable := true, val := (2 : Nat) }]')
# BOTH options present and naming the same field: gold bars it (the exclusion
# conjunct still applies), the rival lets the selection override and keeps it.
_WIT_INCL_BEATS_EXCL = _wit('some ["a"]', 'some ["a"]',
    '[{ name := "a", editable := true, val := (1 : Nat) }]')
# two survivors: gold emits them in source order, the prepending rival reverses
# them — same set, same names, same values, wrong order.
_WIT_ORDER_REVERSE = _wit('none', 'none',
    '[{ name := "a", editable := true, val := (1 : Nat) }, '
    '{ name := "b", editable := true, val := (2 : Nat) }]')
# two surviving fields: gold keeps both in order, rival drops the first.
_WIT_DROP_FIRST = _wit('none', 'none',
    '[{ name := "a", editable := true, val := (1 : Nat) }, '
    '{ name := "b", editable := true, val := (2 : Nat) }]')


# ===========================================================================
# ADMISSIBILITY POSITIVE — expect "verify"
# ===========================================================================
# The frozen obligation carries no precondition hypothesis, so there is no
# precondition BINDER to over-constrain. The analogue on a total carrier is the
# obligation being unsatisfiable at exactly an F2P-shaped concrete input, which a
# positive that discharges the spec predicate AT that input — by evaluation, as a
# `have`, before closing the frozen obligation verbatim — tests directly. The two
# ground instances are the discriminating regions: a present-EMPTY inclusion
# selection (keeps nothing) and a present-EMPTY exclusion (bars nothing), each
# over a two-field editable source.
_ADMISS_FS = ('[{ name := "id", editable := true, val := (1 : Nat) }, '
              '{ name := "name", editable := true, val := (2 : Nat) }]')
_INTRO = "  intro α fields exclude fs\n"


def _ground(fields: str, exclude: str, tag: str) -> str:
    return (
        f"  have _ground_{tag} : problem_spec_modelToDict (α := Nat) "
        f"({fields}) ({exclude})\n"
        f"      {_ADMISS_FS}\n"
        f"      (implementation_modelToDict (α := Nat) ({fields}) ({exclude})\n"
        f"        {_ADMISS_FS}) := by\n"
        "    unfold problem_spec_modelToDict implementation_modelToDict\n"
        "    decide\n"
    )


# Inserted immediately after the frozen `intro`, so the gold tactic body that
# follows is byte-identical and the theorem STATEMENT is untouched.
_ADMISS_GROUND = _swap(
    _BASE, _INTRO,
    _INTRO
    + _ground("some []", "none", "presentEmptySelection")
    + _ground("none", "some []", "presentEmptyExclusion"),
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-functional-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNCTIONAL,
     "rationale": "a structurally-different but correct impl: a pure functional "
                  "expression (no imperative do-block / for / mut) whose body is "
                  "definitionally the reference projection, so `correct_` re-closes "
                  "with `rfl`. The carrier is transparent, so there is no oracle to "
                  "echo; this stands purely as a soundness positive of a different "
                  "impl form. If it fails to verify the spec is over-fit to the "
                  "imperative shape => SPEC-TOO-STRONG."},
    {"id": "pos-combined-guard", "kind": "soundness", "expect": "verify",
     "module": _POS_COMBINED,
     "rationale": "a second correct impl: the same imperative do-loop but the three "
                  "survival conjuncts are hoisted into the single `keep` predicate "
                  "instead of three early-`continue` guards. Semantically identical; "
                  "the executable shape differs. Proof re-closed by Route-B induction "
                  "on the accumulator (`List.forIn_cons`, case-split on `keep`). If it "
                  "fails to verify the spec is over-fit to the three-guard shape "
                  "=> SPEC-TOO-STRONG."},

    # ---- admissibility positive (must VERIFY) ----
    {"id": "admiss-ground-empty-options", "kind": "admissibility",
     "expect": "verify", "module": _ADMISS_GROUND,
     "rationale": "the frozen obligation has no precondition hypothesis, so there "
                  "is no precondition binder to over-constrain; the analogue on a "
                  "total carrier is the obligation being UNSATISFIABLE at exactly "
                  "an F2P-shaped concrete input. This discharges the spec "
                  "predicate BY EVALUATION (`decide`) at the two ground inputs "
                  "the discriminating behavior lives at — a present-EMPTY "
                  "inclusion selection (must keep nothing) and a present-EMPTY "
                  "exclusion (must bar nothing), each over a two-field editable "
                  "source — as `have`s, then closes the frozen obligation "
                  "verbatim. If either ground instance failed to discharge, the "
                  "modeled behavior would be unsatisfiable at the very input the "
                  "behavior is about (the PRECOND-TOO-STRONG analogue). Nothing "
                  "is assumed: no new declaration, no assumption token, the "
                  "theorem statement is byte-identical and the gold tactic body "
                  "that follows the `intro` is unchanged."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "weak-truthiness", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TRUTHINESS, "witness": _WIT_TRUTHINESS,
     "refinement": "this IS the pre-patch behaviour: a present-but-empty selection "
                   "is treated like an absent one, so an empty selection includes "
                   "everything instead of nothing. Its faithful real patch is the "
                   "UNPATCHED guard, which the F2P test asserting the empty-selection "
                   "call returns an EMPTY result FAILS (it returns all editable "
                   "fields) — so a verifying rival here is a true "
                   "verify-does-not-imply-resolve break; it is the exact bug the "
                   "change fixes.",
     "rationale": "attacks the `fields = some []` region of the inclusion clause — "
                  "the absent-vs-present-empty distinction. Witness at fields=some[], "
                  "one editable field: gold keeps nothing, the rival keeps it. Built "
                  "both ways (rival exit 0, gold exit 1)."},
    {"id": "weak-restrict-none", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RESTRICT_NONE, "witness": _WIT_RESTRICT_NONE,
     "refinement": "treats an ABSENT selection (the default, most common call) as a "
                   "membership filter over the empty list, so the default call keeps "
                   "nothing. Its faithful real patch would drop the guard that "
                   "distinguishes 'no selection' from a filter, breaking the baseline "
                   "assertion that a default call returns ALL editable fields — so it "
                   "would NOT resolve.",
     "rationale": "attacks the `fields = none` region of the inclusion clause "
                  "(absent => include all). Witness at fields=none, one editable "
                  "field: gold keeps it, the rival keeps nothing. Built both ways "
                  "(rival exit 0, gold exit 1)."},
    {"id": "weak-include-keepall", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INCLUDE_KEEPALL, "witness": _WIT_INCLUDE_KEEPALL,
     "refinement": "ignores a PRESENT selection entirely, so a call requesting a "
                   "specific subset of fields receives every editable, non-excluded "
                   "field. Its faithful real patch would omit the membership test, "
                   "breaking the F2P assertion that a two-name selection returns "
                   "exactly those two names — so it would NOT resolve.",
     "rationale": "attacks the `fields = some [x]` region of the inclusion clause — "
                  "the only rival that probes a present selection with a name NOT in "
                  "it. Witness at fields=some[\"a\"] over a field named \"b\": gold "
                  "keeps nothing, the rival keeps it. Built both ways (rival exit 0, "
                  "gold exit 1)."},
    {"id": "weak-drop-editability", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_EDIT, "witness": _WIT_DROP_EDIT,
     "refinement": "drops the editability skip, so a non-editable field is emitted. "
                   "Its faithful real patch would delete the editability guard "
                   "(unchanged by the gold change), emitting non-editable columns and "
                   "breaking the baseline keyset — so it would NOT resolve.",
     "rationale": "attacks the `editable` binder / the first conjunct of `keep`. "
                  "Witness at a single non-editable field: gold drops it, the rival "
                  "keeps it. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "weak-drop-exclusion", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_EXCL, "witness": _WIT_DROP_EXCL,
     "refinement": "drops the exclusion filter, so a field named in the exclusion "
                   "list survives. Its faithful real patch would delete the exclusion "
                   "guard, breaking the F2P assertion that an exclusion of two names "
                   "returns only the remaining fields — so it would NOT resolve.",
     "rationale": "attacks the `exclude` binder / the third conjunct of `keep` — no "
                  "other rival varies a present exclusion list. Witness at "
                  "exclude=some[\"a\"] over a field named \"a\": gold drops it, the "
                  "rival keeps it. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "weak-exclude-invert", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXCL_INVERT, "witness": _WIT_EXCL_INVERT,
     "refinement": "reads a present exclusion list as an INCLUSION filter, so a "
                   "call supplying an exclusion receives only the fields the "
                   "exclusion names. Its faithful real patch would invert the "
                   "exclusion guard's sense, so a call passing an EMPTY exclusion "
                   "receives nothing where the baseline demands every editable "
                   "field — so it would NOT resolve.",
     "rationale": "attacks the present-but-EMPTY region of the `exclude` binder, "
                  "which `weak-drop-exclusion` provably cannot reach: dropping the "
                  "exclusion block agrees with the spec on every absent OR empty "
                  "exclusion, so only a rival that MIS-handles `exclude = some []` "
                  "pins the clause there. Witness at exclude=some[] over one "
                  "editable field: gold keeps it, the rival keeps nothing. Built "
                  "both ways (rival exit 0, gold exit 1 with `decide` proving the "
                  "negation false)."},
    {"id": "weak-value-misalign", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_VALUE_MISALIGN, "witness": _WIT_VALUE_MISALIGN,
     "refinement": "pairs every survivor with the FIRST source field's value "
                   "instead of its own. Its faithful real patch would read the "
                   "extracted value off the wrong field, so a multi-field call "
                   "returns correct keys carrying duplicated values and the "
                   "baseline value assertions FAIL — so it would NOT resolve.",
     "rationale": "attacks the VALUE half of the `(f.name, f.val)` pair — the one "
                  "output component no other rival perturbs. Every other rival "
                  "changes which fields survive or in what order; this one keeps "
                  "the survivor set, the order and every name intact and is "
                  "refutable only through `f.val`, so it is what pins the "
                  "per-element value identity the `.map` asserts. Witness over two "
                  "survivors with distinct values: gold pairs each with its own, "
                  "the rival gives both the head's. Built both ways (rival exit 0, "
                  "gold exit 1 with `decide` proving the negation false)."},
    {"id": "weak-name-misalign", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NAME_MISALIGN, "witness": _WIT_NAME_MISALIGN,
     "refinement": "labels every survivor with the FIRST source field's name "
                   "instead of its own. Its faithful real patch would key each "
                   "extracted value under the wrong field's name, so a "
                   "multi-field call returns the right number of entries under "
                   "duplicated keys and the baseline keyset assertion FAILS — so "
                   "it would NOT resolve.",
     "rationale": "attacks the NAME half of the `(f.name, f.val)` pair, the "
                  "mirror of `weak-value-misalign`: that rival pins only the "
                  "second projection, so the FIRST was unprobed by any rival "
                  "leaving the survivor set, the order and the values intact. "
                  "Witness over two survivors with distinct names: gold labels "
                  "each with its own, the rival gives both the head's. Built "
                  "both ways (rival exit 0, gold exit 1)."},
    {"id": "weak-dedup-by-name", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DEDUP_NAME, "witness": _WIT_DEDUP_NAME,
     "refinement": "emits a survivor only if no earlier survivor shares its "
                   "name, i.e. treats the result as keyed rather than as the "
                   "ordered sequence of survivors. HONEST SCOPE, stated because "
                   "the manifest does not demonstrate otherwise: the declared "
                   "refinement records that the source walk presents pairwise "
                   "DISTINCT names, so on the refined domain this rival and the "
                   "frozen impl agree and no claim is made here that its real "
                   "counterpart would fail the F2P. What it defends is the "
                   "frozen spec as WRITTEN over its full binder domain — the "
                   "clause equates the result to a `.filter`-then-`.map`, a "
                   "SEQUENCE that preserves duplicates, not a keyed collapse — "
                   "and `fs` is universally quantified with no distinctness "
                   "hypothesis, so a repeated name is an input the obligation "
                   "must cover.",
     "rationale": "attacks MULTIPLICITY: `.filter`-then-`.map` keeps BOTH of two "
                  "same-named survivors, and every other witness in this battery "
                  "uses pairwise-distinct names, so this rival AGREES with the "
                  "spec on all of them and is refutable only at a repeated name. "
                  "Witness over two editable fields both named \"a\" with "
                  "distinct values: gold keeps both pairs, the rival keeps only "
                  "the first. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "weak-include-beats-exclude", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INCL_BEATS_EXCL, "witness": _WIT_INCL_BEATS_EXCL,
     "refinement": "consults the exclusion list only when no inclusion selection "
                   "is supplied, so a present selection silently overrides a "
                   "present exclusion. Its faithful real patch would nest the "
                   "exclusion test under the absent-selection branch, so a call "
                   "supplying BOTH options receives a field the exclusion names "
                   "and the exclusion assertion FAILS — so it would NOT resolve.",
     "rationale": "attacks the INDEPENDENCE of the two options, which `keep` "
                  "pins by conjoining them: a field named in the selection AND "
                  "in the exclusion must still be barred. Every other rival "
                  "holds one of the two options at `none`, so no witness in the "
                  "battery previously had both present at once. Witness at "
                  "fields=some[\"a\"], exclude=some[\"a\"] over a field named "
                  "\"a\": gold bars it, the rival keeps it. Built both ways "
                  "(rival exit 0, gold exit 1)."},
    {"id": "weak-order-reverse", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ORDER_REVERSE, "witness": _WIT_ORDER_REVERSE,
     "refinement": "prepends each survivor instead of appending, so the result "
                   "is the correct survivor set in REVERSE source order. Its "
                   "faithful real patch would accumulate the entries backwards, "
                   "so the returned mapping's iteration order no longer matches "
                   "the field walk the baseline observes — so it would NOT "
                   "resolve.",
     "rationale": "attacks the sequence-ORDER half of the clause: the survivor "
                  "set, every name and every value are exactly right and only "
                  "the order is wrong, which `weak-drop-first` cannot isolate "
                  "(that rival changes WHICH fields survive). Witness over two "
                  "survivors: gold emits them in source order, the rival "
                  "reversed. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "weak-drop-first", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_FIRST, "witness": _WIT_DROP_FIRST,
     "refinement": "never keeps the first source field. Its faithful real patch "
                   "would skip the leading field of the walk, so the default call "
                   "loses its first column and the baseline keyset assertion FAILS — "
                   "so it would NOT resolve.",
     "rationale": "attacks the per-element source-order / position clause: the "
                  "`.filter`-then-`.map` pins each survivor at its own position. "
                  "Witness over two surviving fields: gold keeps both in order, the "
                  "rival drops the first. Varies `fs` length (2) and the head "
                  "position. Built both ways (rival exit 0, gold exit 1)."},
]
