import Mathlib
-- imports-end

/-!
Collecting the identifier names that a type annotation refers to.

When a value is annotated with a type (including a type written as a comment),
the analyzer must record every top-level identifier the annotation refers to, so
that an import used *only* inside such an annotation still counts as used.

A type annotation is a small expression tree of four shapes:

  * a bare identifier `n` (e.g. `ABC`);
  * a dotted access `e.attr` (e.g. `abc.ABC`), whose meaning is rooted in the
    identifier(s) of the qualifier `e`;
  * a parametrized form `v[s]` (e.g. `Foo[Bar]`); and
  * anything else (a literal, ellipsis, …), which refers to no identifier.

The names contributed by an annotation are appended to the names already
collected (`acc`). The contribution of each shape is:

  * a bare identifier contributes that identifier;
  * a dotted access contributes the identifier(s) at the root of its qualifier —
    i.e. the same identifiers its qualifier would contribute on its own;
  * a parametrized form `v[s]` whose head is a member access on the well-known
    standard typing namespace contributes just that namespace's name; any other
    parametrized form contributes every identifier appearing anywhere inside it,
    in left-to-right (pre-order) reading order;
  * anything else contributes nothing.

The names collected before the annotation are preserved unchanged, as a prefix.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The annotation
-- tree and the sub-traversal that gathers every identifier inside a parametrized
-- form are modeled structurally over the annotation itself, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A type-annotation expression tree.
* `name id`            — a bare identifier `id`;
* `dotted expr attr`— a member access `expr.attr`;
* `subscript value slice` — a parametrized form `value[slice]`;
* `other`              — any other expression (literal, ellipsis, …) referring
  to no identifier. -/
inductive Annot where
  | name (id : String)
  | dotted (expr : Annot) (attr : String)
  | subscript (value : Annot) (slice : Annot)
  | other
  deriving Repr, DecidableEq

/-- The well-known standard typing namespace. -/
def typingNamespace : String := "typing"

/-- Every identifier appearing anywhere inside an annotation tree, in
left-to-right (pre-order) reading order. Member-access attribute labels are not
identifiers in their own right; only the qualifier roots are. -/
def identsInTree : Annot → List String
  | .name id            => [id]
  | .dotted expr _   => identsInTree expr
  | .subscript value slice => identsInTree value ++ identsInTree slice
  | .other              => []

/-- A parametrized form's head is a member access on the standard typing
namespace, i.e. `typing.<something>`. -/
def isTypingHead : Annot → Bool
  | .dotted (.name id) _ => id == typingNamespace
  | _                       => false

/-- The identifiers an annotation contributes, on its own.
* a bare identifier contributes itself;
* a dotted access contributes whatever its qualifier contributes;
* a parametrized form headed by the standard typing namespace contributes just
  that namespace's name; any other parametrized form contributes every
  identifier inside it (pre-order);
* anything else contributes nothing. -/
def contributed : Annot → List String
  | .name id            => [id]
  | .dotted expr _   => contributed expr
  | .subscript value slice =>
      if isTypingHead value then [typingNamespace]
      else identsInTree value ++ identsInTree slice
  | .other              => []
-- pure-end

-- post-conditions-start
/-- The collected names after processing `annot` are exactly the names already
collected (`acc`, preserved unchanged as a prefix) followed by the identifiers
`annot` contributes. -/
def problem_spec_collectAnnotationNames
    (annot : Annot) (acc : List String) (result : List String) : Prop :=
  result = acc ++ contributed annot
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
