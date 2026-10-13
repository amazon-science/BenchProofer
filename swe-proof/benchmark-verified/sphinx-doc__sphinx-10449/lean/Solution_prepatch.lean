import Mathlib
-- imports-end

/-!
Populating a structured field list with parameter- and return-type information
derived from a set of named type annotations.

The routine is given the fields already present in the list, a list of named
annotations (a name paired with its rendered type, in order; names are unique),
and a flag. For each annotation it appends, in order:

* a `type <name>` field carrying the rendered type, unless the existing fields
  already declare a type for that name; and
* an empty `param <name>` field, unless the existing fields already declare that
  parameter.

After the per-name fields, if the annotations carry an entry for the return
position and the existing fields do not already declare a return type, a single
`rtype` field carrying the return annotation is appended — EXCEPT that, when the
flag is set and the return annotation is the trivial unit annotation (`"None"`),
no return-type field is appended at all.

A field is observed only through its name text and its body text; both are
modeled as `String`. Existing fields are classified by tokenizing their name on
runs of spaces:

* `type <name>` declares a type for `<name>`;
* `param <name>` declares the parameter `<name>`;
* `param <kind> <name…>` declares both the parameter and a type for `<name…>`;
* `rtype …` declares that a return type is already present;
* a field that declares a type for, or the parameter named, the return
  position (`type return`, `param return`, `param <kind> return`) likewise
  counts as declaring the return type: the scan records all of these under
  the return name, so no return-type field is appended after any of them.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The field-name parsing, the
-- per-name type/param generation, and the return-type decision are all modeled
-- deeply (element-wise). The field-record constructors are pure data builders
-- whose output is taken as the modeled result.
-- axioms-end

-- pure-start
/-- A structured field, observed through its name text and body text. -/
structure DocField where
  name : String
  body : String
deriving Repr, DecidableEq

/-- Split a field name on runs of spaces (empty tokens dropped). -/
def tokenize (s : String) : List String :=
  (s.splitOn " ").filter (fun t => t ≠ "")

/-- Does field `f` declare a *type* for the name `nm`? True for a `type nm`
field or a 3+-token `param <kind> nm…` field. -/
def declaresTypeField (f : DocField) (nm : String) : Bool :=
  match tokenize f.name with
  | "type" :: rest => rest ≠ [] && " ".intercalate rest == nm
  | "param" :: _ :: p :: ps => " ".intercalate (p :: ps) == nm
  | _ => false

/-- Does field `f` declare the *parameter* `nm`? True for a 2-token `param nm`
field or a 3+-token `param <kind> nm…` field. -/
def declaresParamField (f : DocField) (nm : String) : Bool :=
  match tokenize f.name with
  | "param" :: p :: [] => p == nm
  | "param" :: _ :: p :: ps => " ".intercalate (p :: ps) == nm
  | _ => false

/-- Does field `f` declare that a return type is already present? True for an
`rtype …` field, and also for any field that declares a type for, or the
parameter named, the return position (`type return`, `param return`,
`param <kind> return`) — the scan records all of these under the return name. -/
def isReturnField (f : DocField) : Bool :=
  match tokenize f.name with
  | "rtype" :: _ => true
  | _ => declaresTypeField f "return" || declaresParamField f "return"

/-- Some existing field already declares a type for `nm`. -/
def declaresType (existing : List DocField) (nm : String) : Bool :=
  existing.any (fun f => declaresTypeField f nm)

/-- Some existing field already declares the parameter `nm`. -/
def declaresParam (existing : List DocField) (nm : String) : Bool :=
  existing.any (fun f => declaresParamField f nm)

/-- Some existing field already declares a return type. -/
def hasReturnField (existing : List DocField) : Bool :=
  existing.any isReturnField

/-- The return annotation carried by `annotations`, if any. -/
def lookupReturn (annotations : List (String × String)) : Option String :=
  (annotations.find? (fun p => p.1 == "return")).map Prod.snd

/-- Fields generated for one annotation `(name, ann)` (return entries skipped by
the caller): a `type` field unless a type is already declared, then a `param`
field unless the parameter is already declared. -/
def genForName (existing : List DocField) (name ann : String) : List DocField :=
  (if declaresType existing name then [] else [⟨"type " ++ name, ann⟩]) ++
  (if declaresParam existing name then [] else [⟨"param " ++ name, ""⟩])

/-- All per-name fields generated for `annotations` (the return entry, if any, is
skipped here — it is handled by the return-type rule). -/
def genParamTypeFields (existing : List DocField)
    (annotations : List (String × String)) : List DocField :=
  annotations.flatMap (fun p =>
    if p.1 == "return" then [] else genForName existing p.1 p.2)

/-- The return-type field, if one is to be appended: only when the annotations
carry a return entry, the existing fields declare no return type, and the entry
is not suppressed (flag set and the annotation is the trivial unit `"None"`). -/
def genReturnField (existing : List DocField)
    (annotations : List (String × String)) (suppressTrivialReturn : Bool) : List DocField :=
  match lookupReturn annotations with
  | some ann =>
      if hasReturnField existing then []
      else if ann == "None" && suppressTrivialReturn then []
      else [⟨"rtype", ann⟩]
  | none => []
-- pure-end

-- post-conditions-start
/-- The resulting field list is the existing fields, followed by the generated
per-name type/param fields (in annotation order), followed by the return-type
field if the return rule produces one. -/
def problem_spec_render_typehint_fields
    (existing : List DocField) (annotations : List (String × String))
    (suppressTrivialReturn : Bool) (result : List DocField) : Prop :=
  result =
    existing
      ++ genParamTypeFields existing annotations
      ++ genReturnField existing annotations suppressTrivialReturn
-- post-conditions-end

-- impl-start
def implementation_render_typehint_fields
    (existing : List DocField) (annotations : List (String × String))
    (suppressTrivialReturn : Bool) : List DocField := Id.run do
  let mut fields := existing
  for entry in annotations do
    let name := entry.1
    let ann := entry.2
    unless name == "return" do
      if !(declaresType existing name) then
        fields := fields ++ [⟨"type " ++ name, ann⟩]
      if !(declaresParam existing name) then
        fields := fields ++ [⟨"param " ++ name, ""⟩]
  match lookupReturn annotations with
  | some ann =>
      -- BUG (pre-fix): the return-type field is emitted whenever a return
      -- annotation is present and no return type is already declared — the
      -- suppress flag is ignored, so a trivial unit return on a suppressed
      -- target still produces a spurious `rtype` field.
      if !(hasReturnField existing) then
        fields := fields ++ [⟨"rtype", ann⟩]
  | none => pure ()
  return fields
-- impl-end

-- proof-start
theorem correct_render_typehint_fields :
    ∀ (existing : List DocField) (annotations : List (String × String))
      (suppressTrivialReturn : Bool),
      problem_spec_render_typehint_fields existing annotations suppressTrivialReturn
        (implementation_render_typehint_fields existing annotations suppressTrivialReturn) := by
  sorry
-- proof-end
