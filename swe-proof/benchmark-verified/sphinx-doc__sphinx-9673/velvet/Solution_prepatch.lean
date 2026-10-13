import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   This operation reclassifies the leading token of each existing info-field name
   and then synthesizes new fields from the recorded type annotations. Every step
   is a concrete, pure structural transform over the field names and the
   annotation table; nothing is deferred to an unchanged callee defined elsewhere
   whose behavior the specification would have to assume. Hence there is no consumed
   axiom and no deep-model reference to validate, and G-AX is vacuous
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A field-name token, or an annotation key — a character sequence. Only equality
   and membership are ever observed. -/
abbrev Tok := List Char

/- The distinguished field tokens this operation recognizes. A description field
   for the function result may be spelled with EITHER the short return token or
   its plural synonym; both denote the same result-description key `returnKey`. A
   declared result type is spelled `rtype`; a parameter description/type is
   spelled `param`/`type`. -/
def paramTok   : Tok := "param".toList
def typeTok    : Tok := "type".toList
def returnTok  : Tok := "return".toList
def returnsTok : Tok := "returns".toList
def rtypeTok   : Tok := "rtype".toList

/- The canonical key under which a result description/type is recorded. Both
   accepted spellings of a result-description field collapse onto this single
   key. -/
def returnKey : Tok := "return".toList

/- Join a tail of field-name tokens back into one space-separated name (the
   inverse of splitting a field name on runs of spaces). -/
def joinSp (ts : List Tok) : Tok := List.intercalate [' '] ts

/- The two membership sets accumulated while scanning the existing fields:
   `hasDesc` — keys that already carry a description; `hasType` — keys that
   already carry a declared type. -/
structure Sets where
  hasDesc : List Tok
  hasType : List Tok
  deriving DecidableEq, Inhabited, Repr

def emptySets : Sets := ⟨[], []⟩

def addDesc (s : Sets) (t : Tok) : Sets := { s with hasDesc := s.hasDesc ++ [t] }
def addType (s : Sets) (t : Tok) : Sets := { s with hasType := s.hasType ++ [t] }

/- Classify one existing field, given as the tokens of its name split on spaces,
   updating the description/type sets:

   * a `param` field with exactly one trailing token records a description for
     that parameter; a `param` field with more trailing tokens (an inline-typed
     parameter) records BOTH a description and a type for the joined remainder;
   * a `type` field records a declared type for the joined remainder;
   * a result-description field — recognized under EITHER the short return token
     OR its plural synonym — records a description for the result key;
   * an `rtype` field records a declared type for the result key;
   * any other field is ignored.

   The result-description clause accepting both spellings is the behavior of
   interest: a result documented under the plural spelling must still count as a
   described result (mapping.md §3.1). -/
def classifyField (parts : List Tok) (s : Sets) : Sets :=
  match parts with
  | [] => s
  | p0 :: rest =>
    if p0 == paramTok then
      match rest with
      | []           => s
      | [x]          => addDesc s x
      | _ :: b :: cs => let nm := joinSp (b :: cs); addType (addDesc s nm) nm
    else if p0 == typeTok then
      addType s (joinSp rest)
    else if p0 == returnTok || p0 == returnsTok then
      addDesc s returnKey
    else if p0 == rtypeTok then
      addType s returnKey
    else s

/- Scan all existing fields left to right, accumulating the description/type
   sets. -/
def classifyFields (fields : List (List Tok)) : Sets :=
  fields.foldl (fun acc f => classifyField f acc) emptySets

/- A newly synthesized field appended to the field list:
   * `typeOf name body` — a declared type for a parameter (`type <name>`);
   * `rtype body`        — a declared type for the result (`rtype`). -/
inductive Field where
  | typeOf (name : Tok) (body : Tok)
  | rtype  (body : Tok)
  deriving DecidableEq, Inhabited, Repr

/- Emit a parameter-type field for one annotation entry, when warranted: the
   result key (under EITHER spelling) is skipped here (its type is handled
   separately); any other annotated name that already carries a description but
   no declared type gets a fresh `type` field carrying its annotation. -/
def emitStep (s : Sets) (acc : List Field) (na : Tok × Tok) : List Field :=
  let name := na.1
  if name == returnTok || name == returnsTok then acc
  else if s.hasDesc.contains name && !(s.hasType.contains name) then
    acc ++ [Field.typeOf name na.2]
  else acc

/- Look up the result-type annotation by the canonical result key. -/
def lookupReturn : List (Tok × Tok) → Tok
  | []            => []
  | (k, v) :: rest => if k == returnKey then v else lookupReturn rest

/- The trailing result-type field, emitted exactly when the result is annotated,
   already has a recorded description, and has no declared type yet. -/
def rtypeField (s : Sets) (annotations : List (Tok × Tok)) : List Field :=
  if annotations.any (fun na => na.1 == returnKey)
       && s.hasDesc.contains returnKey && !(s.hasType.contains returnKey) then
    [Field.rtype (lookupReturn annotations)]
  else []

/- The full sequence of fields appended by the operation: first the
   parameter-type fields synthesized from the annotation table in order, then the
   optional trailing result-type field. -/
def buildFields (fields : List (List Tok)) (annotations : List (Tok × Tok)) : List Field :=
  let s := classifyFields fields
  (annotations.foldl (emitStep s) []) ++ rtypeField s annotations

/- Forward-fold step: extending the consumed prefix by one element advances the
   left fold built from the shorter prefix by exactly that element. One generic
   drop-step shared by both loops (the Velvet fold pattern). -/
lemma foldlTakeStep {S A : Type} [Inhabited A] (f : S → A → S) (s0 : S) (xs : List A)
    (i : Nat) (hi : i < xs.length) :
    (xs.take (i + 1)).foldl f s0 = f ((xs.take i).foldl f s0) xs[i]! := by
  have hcons : xs.take (i + 1) = xs.take i ++ [xs[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Augment a documented entity's info-field list with the type fields implied by
   its recorded annotations.

   First every existing field is classified by the leading token of its name,
   recording which parameter/result keys already carry a description and which
   already carry a declared type. A result documented under EITHER accepted
   spelling of the result-description field counts as a described result. Then,
   for each annotation in order, a parameter that has a description but no
   declared type gains a `type` field; finally, if the result is annotated and
   has a description but no declared type, a trailing result-type field is
   appended.

   `fields` and `annotations` are read-only (not `mut`): the operation reads them
   and builds a fresh field list, mutating neither (directive 5). -/
method augmentTypeFields (fields : List (List Tok)) (annotations : List (Tok × Tok))
    return (out : List Field)
  ensures out = buildFields fields annotations
  do
    -- impl-start
    -- Pre-image skeleton: the field classifier recognizes ONLY the short result
    -- token and the back-fill skip tests ONLY the short token, so a result
    -- documented under the plural spelling is NOT counted as described. The
    -- frozen spec (buildFields, via classifyField/emitStep, accepts BOTH
    -- spellings), so prove_correct MUST fail.
    let classifyBuggy : List Tok → Sets → Sets := fun parts st =>
      match parts with
      | [] => st
      | p0 :: rest =>
        if p0 == paramTok then
          match rest with
          | []           => st
          | [x]          => addDesc st x
          | _ :: b :: cs => let nm := joinSp (b :: cs); addType (addDesc st nm) nm
        else if p0 == typeTok then
          addType st (joinSp rest)
        else if p0 == returnTok then
          addDesc st returnKey
        else if p0 == rtypeTok then
          addType st returnKey
        else st
    let emitBuggy : Sets → List Field → (Tok × Tok) → List Field := fun st acc na =>
      let name := na.1
      if name == returnTok then acc
      else if st.hasDesc.contains name && !(st.hasType.contains name) then
        acc ++ [Field.typeOf name na.2]
      else acc
    let mut s : Sets := emptySets
    let mut i := 0
    while i < fields.length
      invariant i ≤ fields.length
      invariant s = (fields.take i).foldl (fun acc f => classifyBuggy f acc) emptySets
      done_with i = fields.length
      decreasing fields.length - i
    do
      s := classifyBuggy fields[i]! s
      i := i + 1
    let mut result : List Field := []
    let mut j := 0
    while j < annotations.length
      invariant j ≤ annotations.length
      invariant result = (annotations.take j).foldl (emitBuggy s) []
      done_with j = annotations.length
      decreasing annotations.length - j
    do
      result := emitBuggy s result annotations[j]!
      j := j + 1
    return result ++ rtypeField s annotations
    -- impl-end

prove_correct augmentTypeFields by
  loom_solve
  case _ =>
    have hi : i < fields.length := by omega
    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp_all
  case _ =>
    have hj : j < annotations.length := by omega
    rw [foldlTakeStep (emitStep _) [] annotations j hj]
    simp_all
  all_goals simp_all [buildFields, classifyFields]
