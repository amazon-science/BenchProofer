import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-path resolution of a regular file to the
--  child items it contributes is an orthogonal, unchanged operation whose
--  result enters as plain input data (the `yields` field of each enumerated
--  entry); whether a path lies on the enumeration boundary enters as a plain
--  Boolean observation. No opaque/axiom callee contract is needed.)
-- axioms-end

-- pure-start
/- One enumerated path of a directory tree, reduced to what content
   enumeration consumes:

   * `boundary` — the path contributes nothing to this directory's own
     enumeration (it is the directory's own initialization file, or it already
     sits inside a nested sub-directory that has been accounted for);
   * `isFile` — the path is a regular file (as opposed to a directory);
   * `yields` — the child items a non-boundary regular file resolves to. -/
structure PkgEntry where
  boundary : Bool
  isFile : Bool
  yields : List Nat
  deriving Inhabited, DecidableEq

/- The child items produced by walking the enumerated paths front-to-back:
   a boundary path or a directory contributes nothing; a non-boundary regular
   file contributes the items it resolves to. -/
def walkEntries : List PkgEntry → List Nat
  | [] => []
  | e :: es => (if e.boundary || !e.isFile then [] else e.yields) ++ walkEntries es
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Enumerating the contents of a directory that carries an initialization file.

   The enumeration walks the directory tree and produces the child items it
   contains: if the directory's own initialization file matches the configured
   file pattern (`initMatches`), an item for that file (`initNode`) is produced
   first; then every visited path is examined, and each non-boundary regular
   file contributes whatever child items it resolves to.

   Enumeration is a directory-structure operation: it inspects paths and builds
   items lazily. It must therefore NOT load the directory's own initialization
   file as a side effect — running that file's contents is the job of the
   produced items when (and if) they are later realized, not of the enumeration
   itself. Whether the enumeration loaded the directory's own initialization
   file is an observable of the walk, carried as the second component of the
   result; the desired behavior pins it to `false` unconditionally.

   The first component is the produced sequence, pinned exactly to the walk of
   the given entries (with the leading initialization-file item when it
   matches), so an enumeration cannot trade correctness of the output for the
   loading obligation or vice versa. -/
method gatherEntries (initMatches : Bool) (initNode : Nat)
    (entries : List PkgEntry) return (out : List Nat × Bool)
  ensures out.2 = false
  ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
  do
    -- impl-start
    -- Walk the enumerated paths and gather the child items; the directory's
    -- own initialization file is never loaded during the walk (the loaded
    -- flag reported is false).
    let mut collected : List Nat := []
    if initMatches then
      collected := collected ++ [initNode]
    collected := entries.foldl
      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
      collected
    return (collected, false)
    -- impl-end

/- The fold accumulating child items equals the accumulator followed by
   `walkEntries`, generalized over the accumulator. -/
lemma foldl_walkEntries (es : List PkgEntry) :
    ∀ acc : List Nat,
      es.foldl (fun acc e => if e.boundary = true ∨ e.isFile = false then acc
                             else acc ++ e.yields) acc
        = acc ++ walkEntries es := by
  induction es with
  | nil => intro acc; simp [walkEntries]
  | cons e es ih =>
    intro acc
    simp only [List.foldl_cons, walkEntries, ih]
    by_cases hb : e.boundary = true
    · simp [hb]
    · by_cases hf : e.isFile = true
      · simp [hb, hf, List.append_assoc]
      · simp [hb, hf]

prove_correct gatherEntries by
  loom_solve <;> simp_all [foldl_walkEntries]
