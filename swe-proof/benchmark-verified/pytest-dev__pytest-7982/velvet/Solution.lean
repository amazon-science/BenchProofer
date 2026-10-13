import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no `:|` callee stubs. The behaviour under spec is a
   pure per-level selection over abstracted, read-only inputs: at one level of a
   directory walk, each child entry is observed through three booleans —
   whether it denotes a directory once symbolic links are resolved, whether it
   denotes a directory when links are NOT resolved, and whether the walk's
   recursion predicate accepts it. The walk's deeper descent is the identical,
   unchanged recursive step (refinement.md §B). Nothing is borrowed from an
   oracle; there is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- One child entry encountered at a single level of a directory walk, observed
   through exactly the booleans the per-level selection reads:

   * `isDirectory` — the entry denotes a directory when symbolic links ARE
     resolved (a real directory, or a link whose target is a directory);
   * `isDirectoryNoFollow` — the entry denotes a directory when symbolic links
     are NOT resolved (true only for a real directory);
   * `shouldRecurse` — the walk's recursion predicate accepts this entry.

   Every field is a read-only observation; the selection mutates none of them. -/
structure DirChild where
  isDirectory         : Bool
  isDirectoryNoFollow : Bool
  shouldRecurse       : Bool
  deriving Inhabited, Repr, DecidableEq

/- The selection guard for one child: an entry is descended into exactly when it
   denotes a directory (resolving symbolic links) AND the recursion predicate
   accepts it. The desired behaviour the issue states — a link to a directory is
   followed and walked like any other directory. -/
def descend (e : DirChild) : Bool := e.isDirectory && e.shouldRecurse

/- The children at one directory level that are descended into, in encounter
   order: keep each child the guard accepts, drop the rest. Front-recursive so a
   single unfold is available per loop step (the backward-fold pattern). -/
def descendableSeq : List DirChild → List DirChild
  | []      => []
  | e :: es => (if descend e then [e] else []) ++ descendableSeq es

@[grind] lemma descendableSeq_nil : descendableSeq [] = [] := rfl
@[grind] lemma descendableSeq_cons (e : DirChild) (es : List DirChild) :
    descendableSeq (e :: es) = (if descend e then [e] else []) ++ descendableSeq es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the child entries to descend into at one level of a directory walk.
   `entries` is the read-only, already-ordered list of children encountered at
   this level (it is not `mut` and is returned unchanged in spirit — the result
   is a fresh sublist). Desired behaviour: the result is exactly the children
   that denote a directory once symbolic links are resolved AND that the
   recursion predicate accepts, kept in their original encounter order. A child
   that is a link to a directory must therefore be selected and walked just like
   a plain directory; only entries that are not directories (or that the
   predicate rejects) are skipped. The deeper walk then recurses into each
   selected child by this same rule. -/
method descendableEntries (entries : List DirChild) return (out : List DirChild)
  ensures out = descendableSeq entries
  do
    -- impl-start
    let mut result : List DirChild := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = descendableSeq (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      result := (if e.isDirectory && e.shouldRecurse then [e] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `descendableSeq` peels one selection decision. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma descendableSeq_drop_step (entries : List DirChild) (i : Nat)
    (hi : 0 < i) (hle : i ≤ entries.length) :
    descendableSeq (entries.drop (i - 1))
      = (if entries[i-1]!.isDirectory && entries[i-1]!.shouldRecurse then [entries[i-1]!] else [])
          ++ descendableSeq (entries.drop i) := by
  have hlt : i - 1 < entries.length := by omega
  have hcons : entries.drop (i - 1) = entries[i - 1]! :: entries.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, descendableSeq_cons]
  show _ = (if descend entries[i-1]! then _ else _) ++ _
  rfl

prove_correct descendableEntries by
  loom_solve
  rw [descendableSeq_drop_step entries i (by omega) (by omega)]
  simp_all
