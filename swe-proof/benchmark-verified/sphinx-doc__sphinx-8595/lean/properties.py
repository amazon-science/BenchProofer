# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8595 (lean lane).
# NOT a Lean module; a record of adversarial cases the gate elaborates against
# the frozen spec. PORTED from the nagini sibling's properties.py, re-expressed
# against this backend's carrier (the argument is carried over; the mechanics are
# rewritten for the Lean model).
#
# Defended surface (read from Solution.lean):
#   selectMembers
#     (wantAll : Bool) (allAttr : Option (List String))
#     (members : List String) (requested : List String)
#     : Bool × List (String × Bool)
#   The one modeled obligation, `correct_selectMembers`, pins the WHOLE output
#   pair to `selectMembers …`. Its three independent top-level branches are the
#   load-bearing clauses:
#     (B1) wantAll ∧ allAttr = none  → (true,  members.map (·, false))
#          — no declared list: keep every discovered member, none tagged, and
#            signal the caller to still apply the implicit origin check (flag
#            true, every tag false).
#     (B2) wantAll ∧ allAttr = some names → (false, members.map (·, !names.contains ·))
#          — a declared list (INCLUDING one that names nothing) restricts the
#            selection: every discovered member is kept but tagged skipped iff its
#            name is not in the list, and the implicit check is not requested
#            (flag false, per-member tag = membership complement).
#     (B3) ¬wantAll → (false, requested.filterMap (present-keep))
#          — by-name selection: exactly the requested names present as members,
#            in requested order, each kept (not skipped), flag false.
#
# Carrier narrowing vs the nagini sibling. Nagini contracted a single boolean-
# returning `select_module_members(member_names, excluded, all_present, all_names)`
# over a WRITABLE `excluded` flag array plus two half-permission read-only inputs;
# it defended four postcondition clauses P1–P4 and a heap frame. This bundle
# models the purely functional core as ONE total function returning the full
# `(flag, tagged)` pair over four value inputs. Consequences for the port:
#   * P1 (absent ⇒ Result True) ↔ the B1 flag (`true`).
#   * P2 (absent ⇒ every flag False) ↔ the B1 per-member tag (`false`).
#   * P3 (present ⇒ Result False) ↔ the B2 flag (`false`).
#   * P4 (present ⇒ excluded == exclusion_flags(...)) ↔ the B2 per-member tag
#     (`!names.contains ·`) — the export-list-driven skipped tagging.
#   Each nagini value-rival is re-expressed as an edit to the corresponding
#   branch of `selectMembers`; the F2P discriminator (a declared-but-empty list
#   must skip every member, NOT be treated as "no list") is ported as its own
#   partial-domain rival at `allAttr = some []`.
#   * The by-name branch B3 has NO nagini counterpart (nagini modeled only the
#     want-all path). It is a modeled surface here, so it is defended and attacked
#     (see `weak-byname-nofilter`) — otherwise the `requested` binder would be a
#     binder no rival abuses.
#
# Vacuous / dropped classes (stated per directive, not silently omitted):
#   * FRAME / PERMISSION-MUTATION lane (nagini frame-mutation-member-names,
#     frame-mutation-all-names) — VACUOUS on lean, and DEMONSTRATED so rather
#     than asserted. Those rivals overwrite a half-permission read-only input to
#     prove the frame is enforced. Lean is referentially transparent: the inputs
#     are immutable values, there is no aliasable carrier to overwrite and no
#     permission system. Measured: an impl that "clobbers" its discovered-member
#     input (`let _clobbered := members.map (fun _ => "")`) and then computes the
#     gold result VERIFIES, exit 0 — the write is unobservable because it can only
#     shadow a local, so there is no rival to build here. That is the class
#     collapsing, not a proof that was hard to land.
#   * ADMISSIBILITY — SHIPPED (`admiss-f2p-shape`, below). An earlier revision of
#     this manifest recorded the lane as N/A on the grounds that
#     `correct_selectMembers` carries no precondition hypothesis, so there is "no
#     precondition to prove usable". That reasoning is wrong: on a TOTAL carrier
#     the analogue of an unusable precondition is the obligation being
#     UNSATISFIABLE at an F2P-shaped input, which a positive that discharges the
#     obligation at that concrete input — by evaluation, as a `have`, before
#     closing the frozen obligation verbatim — tests directly. That is what the
#     shipped case does, and its three `have`s were each confirmed load-bearing:
#     perturbing any one claimed component makes `decide` fail (see the case's
#     rationale for the measured exit codes).
#   * DIVERGENCE / NON-TERMINATION lane — KNOWN HOLE on this carrier, NOT a
#     vacuous class. An earlier revision recorded it as vacuous on the grounds
#     that "`implementation_*` is a total Lean `def`; a diverging implementation
#     cannot be written". That is false as stated: `partial def` is accepted here
#     and a non-terminating impl IS writable (a self-call on the want-all path
#     elaborates fine). What blocks the case is not termination checking but
#     OPACITY: a `partial def` has no equation lemmas, so both the frozen proof
#     and any witness fail with
#       `Tactic `unfold` failed to unfold `implementation_selectMembers``
#     — a failure about reducibility, not about the spec. Measured, four builds:
#     a CORRECT impl marked only `partial` (non-recursive body, so equation
#     lemmas still exist) VERIFIES, exit 0 — confirming `partial` alone is not
#     what is being punished. The self-recursive DIVERGING impl exits 1, but its
#     WITNESS also exits 1, with that same `unfold` failure: the recursive
#     `partial def` is opaque, so the witness cannot be made to hold OF the rival,
#     which is the half a reject case must win. A rival whose witness cannot
#     elaborate is not shippable (the gate would record `witness-unproven`, an
#     inconclusive outcome, not a rejection). So the class is a HOLE in what this
#     spec can be shown to exclude, not a class that does not exist. Recorded as
#     such rather than as vacuous, since a vacuous class would claim the battery
#     is complete here and it is not.
#   * AXIOM lane — DROPPED. `meta.axioms == []`, no opaque callee; the selection
#     logic is modeled DEEPLY over the observable inputs. The axiom lane is G-AX's
#     job and this gate ignores it. AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8595"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen regions, extracted verbatim so the manifest breaks loudly on drift.
# The impl region body and the proof tactic body (after the byte-identical
# `theorem correct_selectMembers` statement) are the ONLY regions a variant may
# edit. The spec, signatures, and the theorem STATEMENT are never touched, so
# same_spec holds by construction.

_IMPL_OLD = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, false)]
      return (true, out)
    | some allNames =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, !allNames.contains n)]
      return (false, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      if members.contains name then
        ret := ret ++ [(name, false)]
    return (false, ret)"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

# The frozen proof tactic body (everything after the theorem statement's `:= by`,
# up to `-- proof-end`).
_PROOF_OLD = """\
  intro wantAll allAttr members requested
  have mapKey : ∀ (f : String → String × Bool) (xs : List String) (acc),
      (forIn (m := Id) xs acc (fun n r => pure (ForInStep.yield (r ++ [f n])))) = acc ++ xs.map f := by
    intro f xs
    induction xs with
    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons h t ih =>
      intro acc
      rw [List.forIn_cons]
      show (forIn (m:=Id) t (acc ++ [f h]) fun n r => pure (ForInStep.yield (r ++ [f n]))) = _
      rw [ih]; simp
  have fmKey : ∀ (xs : List String) (acc),
      (forIn (m := Id) xs acc
        (fun name r => if name ∈ members then pure (ForInStep.yield (r ++ [(name, false)]))
          else pure (ForInStep.yield r))) =
        acc ++ xs.filterMap
          (fun name => if name ∈ members then some (name, false) else none) := by
    intro xs
    induction xs with
    | nil => intro acc; simp only [List.forIn_nil, List.filterMap_nil, List.append_nil]; rfl
    | cons h t ih =>
      intro acc
      rw [List.forIn_cons]
      by_cases hh : h ∈ members
      · simp only [hh, if_true]
        show (forIn (m:=Id) t (acc ++ [(h,false)]) _) = _
        rw [ih]; simp [hh]
      · simp only [hh, if_false]
        show (forIn (m:=Id) t acc _) = _
        rw [ih]; simp [hh]
  unfold problem_spec_selectMembers implementation_selectMembers selectMembers
  cases wantAll
  · simp only [Bool.false_eq_true, if_false]
    simp [fmKey]
    rfl
  · simp only [if_true]
    cases allAttr <;> simp [mapKey] <;> rfl"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _impl(new_impl, new_proof=None):
    """Build a full Solution.lean variant. Replaces the impl body, and (for
    soundness positives whose reshaped impl needs a matching proof) the proof
    tactic body. The theorem STATEMENT and the whole spec view are untouched."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


# --- Witness helper. Each reject case states the spec predicate directly at a
# concrete, `decide`-able input (string literals, tiny lists); the negation
# elaborates iff the rival's output contradicts the spec there, and fails against
# the frozen solution (checked in a file with the obligations removed, so no
# tactic script can interfere). Both halves were run under scripts/lean_verify.sh
# before shipping.
def _witness(args):
    return f"""\
example : ¬ problem_spec_selectMembers {args}
    (implementation_selectMembers {args}) := by
  unfold problem_spec_selectMembers implementation_selectMembers
  decide"""


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY. Each is a structurally different
# but behaviourally identical correct impl, shipped WITH a proof that closes for
# the new shape (the theorem statement is byte-identical; only the tactic body
# changes). No new lemma / axiom / sorry.
# ---------------------------------------------------------------------------

# pos-branch-reorder (ports nagini pos-control-branch-reorder): the same three
# branches with the dispatch reordered — the by-name branch handled first (guard
# inverted to `!wantAll`) and the two want-all arms swapped. Written as a pure
# functional match rather than the `Id.run do`/`for` accumulator, so the loop-fold
# lemmas are no longer needed and each branch reduces definitionally. The new
# proof is a clean `cases … <;> rfl`.
_POS_REORDER = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) :=
  if !wantAll then
    (false, requested.filterMap
      (fun name => if members.contains name then some (name, false) else none))
  else
    match allAttr with
    | some allNames => (false, members.map (fun n => (n, !allNames.contains n)))
    | none => (true, members.map (fun n => (n, false)))"""

_POS_REORDER_PROOF = """\
  intro wantAll allAttr members requested
  unfold problem_spec_selectMembers implementation_selectMembers selectMembers
  cases wantAll <;> cases allAttr <;> rfl"""

# pos-pure-functional: the selection written as the pure functional match that is
# literally the `selectMembers` helper's body (no Id.run / no `let mut` / no
# `for`). The result is definitionally the spec RHS, so the proof collapses to
# `rfl`. Confirms the spec does not secretly depend on the imperative encoding.
_POS_PURE = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) :=
  if wantAll then
    match allAttr with
    | none => (true, members.map (fun n => (n, false)))
    | some allNames => (false, members.map (fun n => (n, !allNames.contains n)))
  else
    (false, requested.filterMap
      (fun name => if members.contains name then some (name, false) else none))"""

_POS_PURE_PROOF = """\
  intro wantAll allAttr members requested
  rfl"""

# pos-filter-then-map: a correct reshape that is NOT definitionally the spec RHS,
# unlike the two positives above (whose branches each reduce by `rfl`). Both
# observable components are re-expressed: the by-name branch as
# `filter`-then-`map` instead of `filterMap` (a different list traversal that
# needs its own induction to relate to the spec's), and the declared-branch tag as
# an `if`-expression instead of `!`. So this positive is the one that shows the
# spec is insensitive to the SHAPE of the traversal, not merely to the imperative
# encoding — a genuine re-proof rather than a restatement.
_POS_FILTERMAP = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) :=
  if wantAll then
    match allAttr with
    | none => (true, members.map (fun n => (n, false)))
    | some allNames =>
      (false, members.map (fun n => (n, if allNames.contains n then false else true)))
  else
    (false, (requested.filter (fun name => members.contains name)).map
      (fun name => (name, false)))"""

_POS_FILTERMAP_PROOF = """\
  intro wantAll allAttr members requested
  have hb : ∀ b : Bool, (if b = true then false else true) = !b := by decide
  have key : ∀ (xs : List String),
      (xs.filter (fun name => members.contains name)).map (fun name => (name, false)) =
        xs.filterMap
          (fun name => if members.contains name then some (name, false) else none) := by
    intro xs
    induction xs with
    | nil => rfl
    | cons h t ih =>
      rw [List.filter_cons, List.filterMap_cons]
      by_cases hh : members.contains h
      · rw [if_pos hh, if_pos hh, List.map_cons, ih]
      · rw [if_neg hh]
        simp only [hh, Bool.false_eq_true, if_false, ih]
  unfold problem_spec_selectMembers implementation_selectMembers selectMembers
  cases wantAll
  · simp only [Bool.false_eq_true, if_false, key]
  · simp only [if_true]
    cases allAttr
    · rfl
    · simp only [hb]"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY. The obligation is total (`∀ …`, no precondition hypothesis), so
# the analogue of "the precondition admits the F2P-shaped input" is: the
# obligation is SATISFIABLE — not merely vacuously true — at exactly that input.
# This variant keeps the frozen impl AND the frozen proof verbatim and only
# PREPENDS three `have`s discharged by evaluation, so whatever it shows is shown
# in addition to the frozen obligation, never instead of it.
# ---------------------------------------------------------------------------
_ADMISS_PROOF = """\
  -- The obligation is satisfiable at exactly the reported shape (want-all, three
  -- discovered members) on BOTH sides of the distinction the change turns on, and
  -- the two sides are genuinely different points of the spec. If the spec were
  -- over-constrained at this input, `decide` could not discharge these.
  have _hDeclaredEmpty :
      problem_spec_selectMembers true (some []) ["a", "b", "c"] []
        (false, [("a", true), ("b", true), ("c", true)]) := by
    unfold problem_spec_selectMembers selectMembers
    decide
  have _hNoList :
      problem_spec_selectMembers true none ["a", "b", "c"] []
        (true, [("a", false), ("b", false), ("c", false)]) := by
    unfold problem_spec_selectMembers selectMembers
    decide
  have _hDistinct :
      selectMembers true (some []) ["a", "b", "c"] []
        ≠ selectMembers true none ["a", "b", "c"] [] := by
    unfold selectMembers
    decide
""" + _PROOF_OLD


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each edits ONLY the
# impl region; every one ships a `witness` proving it violates the spec at a
# concrete input (elaborates against the rival, fails against the frozen sol).
# ---------------------------------------------------------------------------

# weak-invert-exclusion (ports nagini weak-invert-exclusion): the want-all/declared
# branch INVERTS the skipped tag — it tags members that ARE named in the export
# list and keeps the un-named ones, the complement of B2. Witness where the two
# members differ in membership so the whole tagged list flips.
_WEAK_INVERT = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, false)]
      return (true, out)
    | some allNames =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, allNames.contains n)]
      return (false, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      if members.contains name then
        ret := ret ++ [(name, false)]
    return (false, ret)"""

# weak-empty-all-implicit (ports nagini partial-domain-empty-all — THE F2P bug):
# correct on almost the whole domain, but a declared-but-empty export list is
# treated like NO list — it takes the B1 shape (flag true, nothing tagged) instead
# of the B2 shape (flag false, every member tagged skipped). This is the exact
# original defect the issue reports. Witness at `allAttr = some []`.
_WEAK_EMPTY_ALL = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, false)]
      return (true, out)
    | some allNames =>
      if allNames.isEmpty then
        let mut out : List (String × Bool) := []
        for n in members do
          out := out ++ [(n, false)]
        return (true, out)
      else
        let mut out : List (String × Bool) := []
        for n in members do
          out := out ++ [(n, !allNames.contains n)]
        return (false, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      if members.contains name then
        ret := ret ++ [(name, false)]
    return (false, ret)"""

# weak-present-flag (ports nagini control-flow-wrong-result): the per-member tags
# are computed correctly, but the want-all/declared branch returns flag `true`
# instead of `false` — telling the caller to still apply the implicit origin
# check on a module that DID declare an export list. B2's flag component.
_WEAK_PRESENT_FLAG = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, false)]
      return (true, out)
    | some allNames =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, !allNames.contains n)]
      return (true, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      if members.contains name then
        ret := ret ++ [(name, false)]
    return (false, ret)"""

# weak-absent-excludes (ports nagini weak-absent-excludes): with no declared list
# the members are all tagged skipped (`true`) instead of kept (`false`). Returns
# the right flag but hides every implicitly-discovered member. B1's per-member
# tag component.
_WEAK_ABSENT_EXCL = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, true)]
      return (true, out)
    | some allNames =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, !allNames.contains n)]
      return (false, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      if members.contains name then
        ret := ret ++ [(name, false)]
    return (false, ret)"""

# weak-absent-flag: with no declared list the flag is returned `false` instead of
# `true` — suppressing the implicit origin check the caller must still run for an
# undeclared module. Tags are correct; B1's flag component. (Corresponds to
# nagini P1, Implies(not all_present, Result()==True).)
_WEAK_ABSENT_FLAG = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, false)]
      return (false, out)
    | some allNames =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, !allNames.contains n)]
      return (false, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      if members.contains name then
        ret := ret ++ [(name, false)]
    return (false, ret)"""

# weak-skip-first (ports nagini partial-domain-skip-first): correct for every
# member except the first — the first discovered member keeps the un-skipped tag
# (`false`) regardless of the export list, so a non-named first member stays
# documented. Off-by-one on the head of the tagged list. B2's per-member tag on a
# single-position sub-domain.
_WEAK_SKIP_FIRST = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, false)]
      return (true, out)
    | some allNames =>
      match members with
      | [] => return (false, [])
      | h :: t =>
        let mut out : List (String × Bool) := [(h, false)]
        for n in t do
          out := out ++ [(n, !allNames.contains n)]
        return (false, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      if members.contains name then
        ret := ret ++ [(name, false)]
    return (false, ret)"""

# weak-byname-nofilter (NO nagini counterpart — attacks B3, the by-name branch
# nagini never modeled): the requested names are returned WITHOUT the present-in-
# members filter, so a requested name that is not actually a member is emitted.
# Without this rival the `requested` binder and the whole ¬wantAll branch would be
# handled identically by gold and every rival — a modeled surface no rival abuses.
_WEAK_BYNAME = """\
def implementation_selectMembers
    (wantAll : Bool) (allAttr : Option (List String))
    (members : List String) (requested : List String) :
    Bool × List (String × Bool) := Id.run do
  if wantAll then
    match allAttr with
    | none =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, false)]
      return (true, out)
    | some allNames =>
      let mut out : List (String × Bool) := []
      for n in members do
        out := out ++ [(n, !allNames.contains n)]
      return (false, out)
  else
    let mut ret : List (String × Bool) := []
    for name in requested do
      ret := ret ++ [(name, false)]
    return (false, ret)"""


SPEC_TESTS = [
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER, _POS_REORDER_PROOF),
        "rationale": (
            "structurally-different but behaviourally-identical impl: the three "
            "branches reordered (by-name guard first, want-all arms swapped) and "
            "written as a pure functional match instead of the Id.run/for "
            "accumulator. Each branch reduces definitionally so the new proof is "
            "`cases wantAll <;> cases allAttr <;> rfl`, closing B1/B2/B3. If it "
            "fails => SPEC-TOO-STRONG. (Ports nagini pos-control-branch-reorder.)"
        ),
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_PURE, _POS_PURE_PROOF),
        "rationale": (
            "the selection as the pure functional match (no Id.run / let mut / "
            "for) — definitionally the spec RHS, so the proof is a single `rfl`. "
            "Confirms the spec does not secretly depend on the imperative loop "
            "encoding. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-filter-then-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_FILTERMAP, _POS_FILTERMAP_PROOF),
        "rationale": (
            "a correct reshape that is NOT definitionally the spec RHS, unlike "
            "the other two positives (whose branches close by `rfl`). The by-name "
            "branch becomes `filter`-then-`map` instead of `filterMap` — a "
            "different traversal, related to the spec's only through its own "
            "induction (`key`) — and the declared-branch tag becomes an "
            "`if`-expression instead of `!` (`hb`). So this is the positive that "
            "shows the spec constrains the OBSERVABLE pair rather than the shape "
            "of the traversal that produces it. Verified at exit 0. If it fails "
            "=> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_IMPL_OLD, _ADMISS_PROOF),
        "rationale": (
            "PRECOND-TOO-STRONG probe. The obligation is total, so the analogue "
            "of an unusable precondition is the obligation being UNSATISFIABLE at "
            "an F2P-shaped input. This case keeps the frozen impl and the frozen "
            "proof verbatim and only PREPENDS three `have`s, each discharged by "
            "evaluation at the reported three-member shape: the declared-but-"
            "naming-nothing list must give (false, every member tagged skipped); "
            "no list at all must give (true, every member kept); and those two "
            "results must DIFFER. The third is what makes the case bite — it "
            "pins that the carrier really separates `some []` from `none` rather "
            "than collapsing them, which is the whole distinction at issue. "
            "Confirmed load-bearing, not vacuous: perturbing exactly one claimed "
            "component makes the build fail (measured, exit 1 each) — flipping "
            "one tag in the empty-list claim, flipping the flag in the no-list "
            "claim, and turning the `≠` into `=`. Verified as shipped at exit 0. "
            "If it fails => PRECOND-TOO-STRONG / an over-constrained spec."
        ),
    },
    {
        "id": "weak-invert-exclusion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_INVERT),
        "witness": _witness('true (some ["a"]) ["a", "b"] []'),
        "refinement": (
            "the faithful real patch would mark exactly the NAMED members skipped "
            "and keep the un-named ones — the inverse of the requirement. For an "
            "empty export list it would then keep every member, so the F2P module "
            "(empty list, members foo/bar/baz) still documents all three. Does "
            "NOT resolve."
        ),
        "rationale": (
            "rejected by B2: the declared-branch tag must be `!names.contains n`, "
            "the rival makes it `names.contains n`. Witness at "
            "(true, some [\"a\"], [\"a\",\"b\"], []): gold tags "
            "[(a,false),(b,true)], rival [(a,true),(b,false)]. Varies the "
            "allAttr=some binder and a nonempty members list. If it verifies => "
            "SPEC-TOO-WEAK on the export-list tagging."
        ),
    },
    {
        "id": "weak-empty-all-implicit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EMPTY_ALL),
        "witness": _witness('true (some []) ["a"] []'),
        "refinement": (
            "THE F2P bug: a declared-but-empty export list is treated as if no "
            "list were declared, taking the keep-everything/implicit-check path. "
            "This is precisely the pre-change behaviour the issue reports — an "
            "empty export list documents every member instead of none, so the "
            "F2P test sees foo/bar/baz. Does NOT resolve."
        ),
        "rationale": (
            "rejected by B2 on the discriminating sub-domain allAttr = some []: "
            "the result must be (false, members all tagged skipped), but the rival "
            "returns (true, members all kept). Witness at (true, some [], [\"a\"], "
            "[]): gold (false,[(a,true)]), rival (true,[(a,false)]). This is the "
            "some-[]-vs-none conflation the whole change turns on. If it verifies "
            "=> SPEC-TOO-WEAK on the exact F2P discriminator."
        ),
    },
    {
        "id": "weak-present-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PRESENT_FLAG),
        "witness": _witness('true (some ["a"]) ["a"] []'),
        "refinement": (
            "the returned origin-check flag on a module that DID declare an export "
            "list is inverted (true instead of false), telling autodoc to fall "
            "back to implicit __module__-based membership and document imported "
            "objects the explicit list is meant to govern. Wrong observable "
            "behaviour. Does NOT resolve."
        ),
        "rationale": (
            "rejected by B2's flag component (Implies present-list, flag = false); "
            "tags are correct, the flag is wrong. Witness at (true, some [\"a\"], "
            "[\"a\"], []): gold (false,[(a,false)]), rival (true,[(a,false)]). "
            "Ports nagini control-flow-wrong-result. If it verifies => "
            "SPEC-TOO-WEAK (flag unconstrained on the declared branch)."
        ),
    },
    {
        "id": "weak-absent-excludes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ABSENT_EXCL),
        "witness": _witness('true none ["a"] []'),
        "refinement": (
            "with no declared export list every discovered member is tagged "
            "skipped, hiding members that should all be documented under implicit "
            "membership. A real patch tagging undeclared-module members as skipped "
            "would document nothing where the base behaviour documents everything. "
            "Does NOT resolve."
        ),
        "rationale": (
            "rejected by B1's per-member tag (Implies no-list, every tag false); "
            "the rival tags them true. Witness at (true, none, [\"a\"], []): gold "
            "(true,[(a,false)]), rival (true,[(a,true)]). Ports nagini "
            "weak-absent-excludes. If it verifies => SPEC-TOO-WEAK on the "
            "no-list tags."
        ),
    },
    {
        "id": "weak-absent-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ABSENT_FLAG),
        "witness": _witness('true none ["a"] []'),
        "refinement": (
            "with no declared export list the origin-check flag is returned false, "
            "suppressing the implicit __module__ check the caller must still run "
            "for an undeclared module — so imported objects would be documented "
            "without the origin filter. Wrong observable behaviour. Does NOT "
            "resolve."
        ),
        "rationale": (
            "rejected by B1's flag component (Implies no-list, flag = true); tags "
            "are correct, the flag is wrong. Witness at (true, none, [\"a\"], []): "
            "gold (true,[(a,false)]), rival (false,[(a,false)]). Attacks the same "
            "no-list branch as weak-absent-excludes but a DIFFERENT output "
            "component (flag vs tag), corresponds to nagini P1. If it verifies => "
            "SPEC-TOO-WEAK on the no-list flag."
        ),
    },
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SKIP_FIRST),
        "witness": _witness('true (some ["b"]) ["a"] []'),
        "refinement": (
            "the first discovered member is never tagged skipped, so a non-named "
            "first member stays documented; with an empty (or non-covering) export "
            "list the first of foo/bar/baz would still appear. Off-by-one on the "
            "head. Does NOT resolve the F2P."
        ),
        "rationale": (
            "rejected by B2 on the head position: the first member must be tagged "
            "`!names.contains n`, the rival hardcodes it `false`. Witness at "
            "(true, some [\"b\"], [\"a\"], []): member a is not in [\"b\"], so gold "
            "(false,[(a,true)]), rival (false,[(a,false)]). Ports nagini "
            "partial-domain-skip-first — a first-position boundary a fuzzer rarely "
            "targets. If it verifies => SPEC-TOO-WEAK on the head tag."
        ),
    },
    {
        "id": "weak-byname-nofilter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_BYNAME),
        "witness": _witness('false none ["a"] ["a", "b"]'),
        "refinement": (
            "in by-name selection the requested names are returned WITHOUT the "
            "present-in-members filter, so a requested name that is not actually a "
            "member is emitted as a documented entry — autodoc would try to "
            "document a name that does not exist. Does NOT match the modeled "
            "by-name behaviour."
        ),
        "rationale": (
            "rejected by B3: the result must be requested.filterMap keeping only "
            "present members, the rival keeps every requested name. Witness at "
            "(false, none, [\"a\"], [\"a\",\"b\"]): b is not a member, so gold "
            "(false,[(a,false)]), rival (false,[(a,false),(b,false)]). This is the "
            "ONLY rival exercising the ¬wantAll branch and the `requested` binder "
            "(no nagini counterpart). If it verifies => SPEC-TOO-WEAK on the "
            "by-name branch."
        ),
    },
]

# No @ContractOnly axioms and no opaque callee on this path (meta.axioms == []);
# the selection logic and the some-[]-vs-none distinction are modeled directly.
# Nothing for the axiom lane to execute.
AXIOM_TESTS = []
