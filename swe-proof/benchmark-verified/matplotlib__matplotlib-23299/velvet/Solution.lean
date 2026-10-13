import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The two operations this restore defers to — overlaying a
--  saved snapshot onto the current mapping, and dropping one key from the
--  snapshot — are modeled DEEPLY in the `pure` region (`updateDict`, `eraseKey`)
--  and validated against their real builtin counterparts by G-AX
--  (`updateDict` is an A-reference; mapping.md §3 / axiom_check.py). Nothing is
--  consumed as an axiom.)
-- axioms-end

-- pure-start
/- Look up the value bound to `name` in a key→value mapping carried as an
   association list (first binding wins; the modeled mapping has unique keys). -/
def lookupKey : List (String × String) → String → Option String
  | [],             _    => none
  | (k, v) :: rest, name => if k = name then some v else lookupKey rest name

/- Drop every binding for `name` from the mapping (keys are unique, so this
   removes exactly the one binding for `name`, leaving the rest in order). -/
def eraseKey : List (String × String) → String → List (String × String)
  | [],             _    => []
  | (k, v) :: rest, name =>
      if k = name then eraseKey rest name else (k, v) :: eraseKey rest name

/- Overlay `saved` onto `current`: every key present in `saved` takes its
   `saved` value; keys present only in `current` keep their `current` value.
   This is the standard "update the mapping in place from another mapping"
   semantics (the saved bindings win). Deep model of that builtin overlay,
   validated equal to it by G-AX (A-reference, mapping.md §3.1). -/
def updateDict (current saved : List (String × String)) : List (String × String) :=
  saved ++ current.filter (fun kv => (lookupKey saved kv.1).isNone)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Restore a previously-saved snapshot of a key→value mapping over its current
   (possibly modified) state, while leaving ONE designated key at its current
   value instead of reverting it.

   A scoped override records a snapshot `saved` of the mapping on entry, lets
   the stored values be freely changed, and on exit puts the recorded settings
   back. The restored mapping keeps the CURRENT value for the designated key
   "backend" and the saved value for every other recorded key; keys present
   only in the current mapping keep their current value.

   `params` is the live mapping; it is genuinely mutated and its post-state is
   pinned EXACTLY (directive 5) by the `ensures` equation below. `saved` is the
   read-only entry snapshot. -/
method restoreSnapshot
    (mut params : List (String × String))
    (saved : List (String × String))
    return (u : Unit)
  ensures params = updateDict paramsOld (eraseKey saved "backend")
  do
    -- impl-start
    -- Drop the designated key from the snapshot before overlaying it, so the
    -- designated key is NOT reverted to its saved value.
    let restoreSrc := eraseKey saved "backend"
    params := updateDict params restoreSrc
    return
    -- impl-end

prove_correct restoreSnapshot by
  loom_solve
