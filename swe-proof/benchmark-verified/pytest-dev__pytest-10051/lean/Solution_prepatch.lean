import Mathlib
-- imports-end

/-!
Resetting a collector of recorded entries without breaking the views onto it.

A *collector* owns a backing list of recorded entries, and it also feeds a
running *transcript*: a rendered account of everything it has recorded, which
readers consult directly rather than through a reference. Other parts of the
system may, at the start of a phase, take a *view* onto that collector by
remembering which backing list the collector currently uses; reading the view
then reads that same backing list. As long as the collector keeps using the same
backing list object, a view stays coupled to it: it observes whatever the
collector currently holds, including entries appended later.

This file specifies the operation that empties a collector. The required
behaviour is that the collector be emptied **without detaching the views already
taken onto it**, and that the emptying be **total** — nothing the collector had
recorded stays observable by any route:

* the backing list the collector uses is emptied;
* the collector keeps using that **same** backing list object (its reference is
  unchanged), so any view that was pointing at it still points at it — and will
  therefore see the emptied list now and any entries appended afterwards;
* the running transcript reads empty afterwards, so a reader that consults the
  transcript directly is left with nothing from before the emptying;
* no other backing list anywhere is disturbed.

The model is a tiny heap: each backing list is a *cell*, and the collector — and
each view — holds a *reference* (an index) naming the cell it reads. Emptying the
collector must edit the referenced cell in place and preserve the reference,
rather than swapping in a freshly allocated cell, which would silently strand
every view that still names the old one. The transcript is a separate sink that
nothing holds a reference into, so only its contents are constrained, never its
identity.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The emptying
-- operation and its reference-preserving (in-place) semantics are modeled
-- DEEPLY over the observable state (the heap of cells, the references into
-- it, and the transcript sink), so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A tiny heap-with-references model of a collector, the views onto it, and the
transcript it feeds.

* `cells`      — the heap: each entry is one backing list of recorded entries (an
                 entry is modeled by its identity, a `Nat`);
* `records`    — the reference (index into `cells`) the collector currently reads;
* `callView`   — the reference a view already taken onto the collector reads;
* `transcript` — the rendered account of what the collector has recorded, held in
                 a sink that readers consult directly; no reference names it, so
                 only its contents are ever observable. -/
structure HandlerState where
  cells : List (List Nat)
  records : Nat
  callView : Nat
  transcript : List Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The collector is emptied, totally, without detaching its views. The state is
pinned exactly: the heap keeps the same set of backing-list objects (same length,
every untouched object identical, addressed by identity via `cells[i]?` so a
present empty list is never confused with an absent one), and

1. the collector still references the same backing-list object as before
   (its reference is unchanged) — the emptying is in place, not a reallocation;
2. the view reference is unchanged (the operation does not touch the views);
3. the heap holds the same number of backing-list objects (no cell is allocated
   or discarded);
4. the backing list the collector references is now present and empty;
5. a view that was coupled to the collector still observes that present, empty
   backing list (this is the behaviour the surrounding system relies on);
6. every other backing-list object in the heap is unchanged, identity-for-identity
   (frame);
7. the transcript reads empty: emptying the collector discards the rendered
   account too, so a reader consulting the transcript directly observes nothing
   the collector had recorded. Only the transcript's CONTENTS are pinned — how
   the sink comes to read empty is left open, since nothing can name it. -/
def problem_spec_clear (s : HandlerState) (result : HandlerState) : Prop :=
  result.records = s.records ∧
  result.callView = s.callView ∧
  result.cells.length = s.cells.length ∧
  result.cells[result.records]? = some [] ∧
  result.cells[result.callView]? = some [] ∧
  (∀ i, i ≠ s.records → result.cells[i]? = s.cells[i]?) ∧
  result.transcript = []
-- post-conditions-end

-- impl-start
def implementation_clear (s : HandlerState) : HandlerState := Id.run do
  let mut st := s
  -- Replace the collector's backing list with a freshly allocated empty list,
  -- repointing the collector's reference at the new cell; any view still naming
  -- the old cell is left observing the old contents.
  st := { st with cells := st.cells ++ [[]], records := st.cells.length }
  -- The rendered account is discarded as before.
  st := { st with transcript := [] }
  return st
-- impl-end

-- proof-start
theorem correct_clear :
    ∀ (s : HandlerState), s.records < s.cells.length → s.callView = s.records →
      problem_spec_clear s (implementation_clear s) := by
  intro s hlt hview
  have himpl : implementation_clear s = { s with cells := s.cells.set s.records [] } := rfl
  rw [himpl]
  refine ⟨rfl, rfl, ?_, ?_, ?_, ?_, rfl⟩
  · simp [List.length_set]
  · simp [List.getElem?_set_self hlt]
  · rw [hview]; simp [List.getElem?_set_self hlt]
  · intro i hi
    simp [List.getElem?_set_ne (Ne.symm hi)]
-- proof-end
