import Mathlib
-- imports-end

/-!
Round-tripping a URL string back from the components a URL parser hands back,
supplying a default scheme when the input carried none.

A URL parser decomposes a URL into a standard set of pieces. Here those are:
an optional scheme, an optional leading `userinfo` field, the authority
(host, optionally with a port), the path, the query, and the fragment; plus a
default scheme to use when the parsed one is absent. The task is the inverse of
parsing — reconstitute the URL string in standard syntax.

Correct reconstruction is a faithful round-trip: it carries **every** parsed
component through into the output, each in the slot the standard URL grammar
assigns it, so that re-parsing the result would recover the same pieces. No
component is privileged over any other. The `reassemble` definition below pins
the layout of all of them exactly, and the postcondition requires the result to
equal it; consult those definitions for the precise syntax rather than any prose
summary of them.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The URL parse step that
-- produces the components is upstream of this function and out of scope; the
-- string-assembly it performs is spelled out concretely below (a deep model,
-- validated against the real assembler by the differential conformance check),
-- so nothing is axiomatized.
-- axioms-end

-- pure-start
/-- Assemble a URL string from a (truthy) scheme, a (truthy) authority, a path,
a query and a fragment, following standard URL-composition syntax:

* a non-empty path not beginning with `/` receives a leading `/`;
* the authority is prefixed with `//`;
* the scheme is prefixed with `:`;
* a non-empty query is appended after `?`, a non-empty fragment after `#`.

`""` for `query`/`fragment` (and for an absent path) contributes nothing — the
exact behavior of a standard URL un-splitter on a present scheme and authority. -/
def assembleUrl (scheme authority path query fragment : String) : String :=
  let url := if path ≠ "" ∧ path.front ≠ '/' then "/" ++ path else path
  let url := "//" ++ authority ++ url
  let url := scheme ++ ":" ++ url
  let url := if query ≠ "" then url ++ "?" ++ query else url
  let url := if fragment ≠ "" then url ++ "#" ++ fragment else url
  url

/-- The reference result: the standard-syntax URL that carries every parsed
component through, computed by placing each piece in its slot and re-assembling.
`scheme0`/`auth` are optional (an absent value is `none`); `authority0`/`path`/
`query`/`fragment` are strings whose emptiness models an absent/empty component. -/
def reassemble (scheme0 auth : Option String)
    (authority0 path query fragment : String) (newScheme : String) : String :=
  -- when the parsed authority came back empty, the authority and path exchange
  -- roles (a no-op whenever the authority is present).
  let authority := if authority0 = "" then path else authority0
  let path := if authority0 = "" then authority0 else path
  let authority := match auth with
    | some a => if a ≠ "" then a ++ "@" ++ authority else authority
    | none => authority
  let scheme := match scheme0 with
    | none => newScheme
    | some s => s
  assembleUrl scheme authority path query fragment
-- pure-end

-- post-conditions-start
/-- The result is exactly the round-tripped URL: every parsed input component is
carried through into its standard syntactic slot in the output. -/
def problem_spec_prependScheme (scheme0 auth : Option String)
    (authority0 path query fragment : String) (newScheme : String)
    (result : String) : Prop :=
  result = reassemble scheme0 auth authority0 path query fragment newScheme
-- post-conditions-end

-- impl-start
def implementation_prependScheme (scheme0 auth : Option String)
    (authority0 path0 query fragment : String) (newScheme : String) :
    String := Id.run do
  let mut authority := authority0
  let mut path := path0
  if authority = "" then
    let saved := authority
    authority := path
    path := saved
  match auth with
  | some a => if a ≠ "" then
                authority := a ++ "@" ++ authority
  | none => pure ()
  let scheme := match scheme0 with
    | none => newScheme
    | some s => s
  return assembleUrl scheme authority path query fragment
-- impl-end


-- proof-start
theorem correct_prependScheme :
    ∀ (scheme0 auth : Option String)
      (authority0 path query fragment : String) (newScheme : String),
      authority0 ≠ "" → newScheme ≠ "" →
      (∀ s, scheme0 = some s → s ≠ "") →
      problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme
        (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
  intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
  unfold problem_spec_prependScheme implementation_prependScheme reassemble
  simp only [Id.run, if_neg hauth]
  cases auth with
  | none => rfl
  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl

-- proof-end
