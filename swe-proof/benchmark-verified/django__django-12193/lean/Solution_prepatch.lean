import Mathlib
-- imports-end

/-!
Assembling the attribute mapping for one form-input rendering context.

The routine takes three things: the input element's own base attribute mapping,
a Boolean activation flag computed from the value being rendered, and an optional
caller-supplied attribute mapping. From these it must produce a rendering context
that exposes a single merged attribute mapping, and it must do so WITHOUT
disturbing the caller's own attribute mapping.

Two facts govern the result.

* The merged attribute mapping exposed by the context is the input's base mapping
  overlaid with the caller-supplied mapping (caller entries win on a key
  collision), and — when the activation flag is set — additionally carrying an
  activation marker entry. When the caller supplies no mapping, the overlay is
  taken over the empty mapping.

* The caller's attribute mapping is an INPUT that is read, never written: after
  the routine returns, the caller observes its mapping exactly as it was passed
  in. This holds regardless of the activation flag — in particular, setting the
  activation marker must not reach back into the caller's mapping.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The two outside
-- operations the routine relies on — overlaying one attribute mapping on another
-- (caller entries winning on collision) and recording a single marker entry —
-- are spelled out concretely below as `mergeDict` / `dictSet`, so they are deep
-- models validated against the real callees, not consumed axioms.
-- axioms-end

-- pure-start
/-- An attribute mapping: an insertion-ordered association list from attribute
name to a Boolean payload. (Only key presence and the Boolean marker payload are
ever observed, so a Boolean payload faithfully captures the modeled behavior.)
The list is kept duplicate-free by the operations below. -/
abbrev AttrMap := List (String × Bool)

/-- The marker key recorded for an activated input. -/
def markerKey : String := "checked"

/-- Set one key to a value in an attribute mapping: overwrite in place if the key
is already present, otherwise append it. -/
def dictSet (d : AttrMap) (k : String) (v : Bool) : AttrMap :=
  if d.any (fun p => p.1 == k) then d.map (fun p => if p.1 == k then (k, v) else p)
  else d ++ [(k, v)]

/-- Overlay `extra` onto `base`: start from `base` and set each entry of `extra`,
so entries from `extra` win on a key collision and new keys are appended. -/
def mergeDict (base extra : AttrMap) : AttrMap :=
  extra.foldl (fun acc p => dictSet acc p.1 p.2) base

/-- The effective caller-side mapping handed on to the context builder: the
caller-supplied mapping (empty when absent), carrying the activation marker when
the flag is set. -/
def effectiveAttrs (checkTest : Bool) (attrs : Option AttrMap) : AttrMap :=
  if checkTest then dictSet (attrs.getD []) markerKey true else attrs.getD []

/-- The rendering context produced for one input element. Only the touched parts
are modeled: the merged attribute mapping it exposes, and the caller's own
attribute mapping as observed after the call. -/
structure InputContext where
  contextAttrs : AttrMap
  callerAttrs : Option AttrMap
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Input→output relation for assembling one input rendering context.

Inputs:
* `base`      — the input element's own base attribute mapping;
* `checkTest` — the activation flag derived from the rendered value;
* `attrs`     — the optional caller-supplied attribute mapping.

The result pins BOTH observable components:
* the context's merged attribute mapping is the base overlaid with the
  caller-supplied mapping, plus the activation marker when the flag is set;
* the caller's attribute mapping is returned exactly as supplied — reading it
  must not mutate it. -/
def problem_spec_buildInputContext (base : AttrMap) (checkTest : Bool)
    (attrs : Option AttrMap) (result : InputContext) : Prop :=
  result.contextAttrs = mergeDict base (effectiveAttrs checkTest attrs) ∧
  result.callerAttrs = attrs
-- post-conditions-end

-- impl-start
-- PRE-PATCH skeleton (the bug): when the activation flag is set the marker is
-- written into the caller-supplied mapping itself. Because that mapping is the
-- caller's own object, the write is observable by the caller after the call —
-- so once an activated input is built, the supplied mapping carries the marker
-- for every subsequent reuse. (When no mapping was supplied a fresh empty one is
-- used locally, so the caller's "absent" view is unaffected.)
def implementation_buildInputContext (base : AttrMap) (checkTest : Bool)
    (attrs : Option AttrMap) : InputContext := Id.run do
  let mut cur := attrs.getD []
  let mut callerView := attrs
  if checkTest then
    cur := dictSet cur markerKey true
    callerView := attrs.map (fun d => dictSet d markerKey true)
  return { contextAttrs := mergeDict base cur, callerAttrs := callerView }
-- impl-end

-- proof-start
theorem correct_buildInputContext :
    ∀ (base : AttrMap) (checkTest : Bool) (attrs : Option AttrMap),
      problem_spec_buildInputContext base checkTest attrs
        (implementation_buildInputContext base checkTest attrs) := by
  sorry
-- proof-end
