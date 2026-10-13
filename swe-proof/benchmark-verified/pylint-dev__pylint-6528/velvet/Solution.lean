import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Whether a directory path is excluded by the run's exclusion configuration
   (the names / name-patterns / path-patterns the run is configured to skip).
   This is an UNCHANGED decision procedure consulted by the traversal; it is a
   total `path → accept/reject` predicate and is left fully OPAQUE — the weakest
   sufficient contract is none (directive 7), so there is no `ensures` to
   over-claim. The configuration is constant throughout the traversal, so the
   decision is a function of the path alone. Provenance + executable soundness
   check (incl. that it is load-bearing): mapping.md / axiom_check.py (G-AX). -/
axiom pathIsIgnored : List Char → Bool
-- axioms-end

-- pure-start
/- One step of a directory traversal: the directory just reached (`root`),
   whether it is itself a package root (`hasInit`), and the processable file
   paths it directly contributes when it is not a package root (`pyFiles`). The
   `dirs` component of a traversal step is irrelevant to what is emitted and is
   omitted. -/
structure WalkEntry where
  root : List Char
  hasInit : Bool
  pyFiles : List (List Char)
deriving Inhabited

/- The traversal state threaded left to right:
   - `.1` (`skip`) — the roots whose ENTIRE subtree is suppressed: any later
     directory lying beneath one of these is dropped without inspection;
   - `.2` (`out`)  — the paths emitted so far, youngest LAST, in traversal order.
   The emitted sequence (`.2`) is the observable result. -/
abbrev WalkState := List (List Char) × List (List Char)

/- The seed state: nothing suppressed, nothing emitted yet. -/
def initWalk : WalkState := ([], [])

/- Whether `root` lies within an already-suppressed subtree: some recorded
   prefix begins it. `List.isPrefixOf` is the prefix test; it transliterates the
   unchanged builtin "this path starts with that one". -/
def underSkip (skip : List (List Char)) (root : List Char) : Bool :=
  skip.any (fun s => s.isPrefixOf root)

/- Advance the traversal by one reached directory `e`.

   1. If `e.root` lies under an already-suppressed subtree, it (and everything
      below it) is dropped — state unchanged.
   2. OTHERWISE, if `e.root` is excluded by the run's configuration, its whole
      subtree is suppressed (record it in `skip`) and nothing is emitted for it.
   3. OTHERWISE, if `e.root` is a package root, its subtree is suppressed and the
      package directory itself is emitted.
   4. OTHERWISE, the processable files this directory directly contributes are
      emitted, in order.

   Step 2 is the behaviour the exclusion settings demand: an excluded directory,
   and the files anywhere beneath it, are omitted from what is processed. -/
noncomputable def stepEntry (st : WalkState) (e : WalkEntry) : WalkState :=
  let skip := st.1
  let out := st.2
  if underSkip skip e.root then
    (skip, out)
  else if pathIsIgnored e.root then
    (skip ++ [e.root], out)
  else if e.hasInit then
    (skip ++ [e.root], out ++ [e.root])
  else
    (skip, out ++ e.pyFiles)

/- The whole traversal: fold `stepEntry` over the reached directories from the
   seed state. The deep model of the discovery walk. -/
noncomputable def discoverWalk (entries : List WalkEntry) : WalkState :=
  entries.foldl stepEntry initWalk

/- Forward-fold step: extending the consumed prefix by one directory advances the
   traversal built from the shorter prefix by exactly that directory. The single
   goal `loom_solve` leaves for the loop body. -/
lemma walk_take_step (entries : List WalkEntry) (i : Nat) (hi : i < entries.length) :
    (entries.take (i + 1)).foldl stepEntry initWalk
      = stepEntry ((entries.take i).foldl stepEntry initWalk) entries[i]! := by
  have hcons : entries.take (i + 1) = entries.take i ++ [entries[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Discover the sequence of module/package paths to process by walking a
   directory tree top-down. A directory that the run is configured to exclude —
   and its entire subtree — is omitted from the discovered paths; a package
   directory is emitted as a whole (its subtree handled as a unit); any other
   directory contributes its processable files directly. The input list of
   reached directories is read-only (not `mut`): the walk threads a fresh
   accumulator state and never mutates the sequence it is handed (directive 5). -/
noncomputable section
method discoverFiles (entries : List WalkEntry) return (out : List (List Char))
  ensures out = (discoverWalk entries).2
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct discoverFiles by
  -- proof elided — supplied by the consumer
