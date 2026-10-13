import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The modeled procedure is
-- pure control flow over two abstract inputs: the parsed markers of a
-- documentation field list (each already split into whitespace-separated tokens
-- by the caller) and an ordered table mapping documented names to their declared
-- type text. Both are produced by the caller/environment; the decision logic the
-- procedure performs is modeled DEEPLY below. The proof agent may add `_prop`
-- axioms only if a proof obligation needs one.
-- axioms-end

-- pure-start
/-- Join a list of tokens with single spaces (the inverse of splitting a marker
on runs of whitespace). -/
def joinSp (parts : List String) : String := String.intercalate " " parts

/-- Classify one parsed field marker, updating the running pair of
"has a description" / "has a declared type" name collections.

`parts` is the marker split into whitespace-separated tokens. A marker headed by
`param` records a described name (and, in its three-token form, also a typed
name); a marker headed by `type` records a typed name; a marker headed by the
short OR the plural return keyword records that the result carries a description;
a marker headed by `rtype` records that the result carries a declared type. -/
def classifyStep (acc : List String × List String) (parts : List String) :
    List String × List String :=
  let (hasDesc, hasType) := acc
  let p0 := parts.headD ""
  if p0 == "param" then
    if parts.length == 2 then
      (hasDesc ++ [parts.getD 1 ""], hasType)
    else if parts.length > 2 then
      let name := joinSp (parts.drop 2)
      (hasDesc ++ [name], hasType ++ [name])
    else
      (hasDesc, hasType)
  else if p0 == "type" then
    (hasDesc, hasType ++ [joinSp (parts.drop 1)])
  else if p0 == "return" || p0 == "returns" then
    (hasDesc ++ ["return"], hasType)
  else if p0 == "rtype" then
    (hasDesc, hasType ++ ["return"])
  else
    (hasDesc, hasType)

/-- Fold `classifyStep` over every parsed marker of the field list. -/
def classify (fields : List (List String)) : List String × List String :=
  fields.foldl classifyStep ([], [])

/-- Process one entry of the name→type table, appending a freshly-built type
field when that name already carries a description but no declared type. The
short and plural return keywords are skipped here (the result's type is handled
separately, after the table is walked). -/
def outStep (hasDesc hasType : List String)
    (acc : List (String × String)) (entry : String × String) :
    List (String × String) :=
  let (name, ann) := entry
  if name == "return" || name == "returns" then
    acc
  else if hasDesc.contains name && !hasType.contains name then
    acc ++ [("type " ++ name, ann)]
  else
    acc

/-- The list of fields appended to a documentation field list when augmenting it
with declared-type information.

For every documented name (other than the result) that already carries a
description but no declared type, a `type <name>` field carrying its type text is
appended, in table order. Finally, if the result has declared type text and the
field list shows a result description but no declared result type, a single
`rtype` field carrying that text is appended. -/
def augmentSpec (fields : List (List String)) (annotations : List (String × String)) :
    List (String × String) :=
  let (hasDesc, hasType) := classify fields
  let typeFields := annotations.foldl (outStep hasDesc hasType) []
  match annotations.lookup "return" with
  | some ann =>
    if hasDesc.contains "return" && !hasType.contains "return" then
      typeFields ++ [("rtype", ann)]
    else
      typeFields
  | none => typeFields
-- pure-end

-- post-conditions-start
/-- Specification of augmenting a documentation field list with declared types.

`fields` is the field list, each marker pre-split into whitespace-separated
tokens. `annotations` is the ordered table mapping each documented name to its
declared type text (the result's type, when present, is stored under the name
`return`). `result` is the list of fields the procedure appends.

The result is exactly the appended-field list determined by the inputs: the
per-name `type <name>` fields followed by the optional `rtype` field, as
characterised by `augmentSpec`. -/
def problem_spec_augment (fields : List (List String))
    (annotations : List (String × String)) (result : List (String × String)) : Prop :=
  result = augmentSpec fields annotations
-- post-conditions-end

-- impl-start
def implementation_augment (fields : List (List String))
    (annotations : List (String × String)) : List (String × String) := Id.run do
  let mut hasDesc : List String := []
  let mut hasType : List String := []
  for parts in fields do
    let p0 := parts.headD ""
    if p0 == "param" then
      if parts.length == 2 then
        hasDesc := hasDesc ++ [parts.getD 1 ""]
      else if parts.length > 2 then
        let name := joinSp (parts.drop 2)
        hasDesc := hasDesc ++ [name]
        hasType := hasType ++ [name]
      else
        pure ()
    else if p0 == "type" then
      hasType := hasType ++ [joinSp (parts.drop 1)]
    else if p0 == "return" then
      hasDesc := hasDesc ++ ["return"]
    else if p0 == "rtype" then
      hasType := hasType ++ ["return"]
    else
      pure ()
  let mut out : List (String × String) := []
  for entry in annotations do
    let (name, ann) := entry
    if name == "return" then
      pure ()
    else if hasDesc.contains name && !hasType.contains name then
      out := out ++ [("type " ++ name, ann)]
    else
      pure ()
  match annotations.lookup "return" with
  | some ann =>
    if hasDesc.contains "return" && !hasType.contains "return" then
      out := out ++ [("rtype", ann)]
  | none => pure ()
  return out
-- impl-end

-- proof-start
/-- The first loop's body (the `p0`/length cascade producing the mutated
`(hasDesc, hasType)` pair) equals `classifyStep acc parts` for every input. -/
theorem classifyBodyEq (acc : List String × List String) (parts : List String) :
    (if (parts.headD "" == "param") = true then
        if (parts.length == 2) = true then (acc.1 ++ [parts.getD 1 ""], acc.2)
        else if parts.length > 2 then
          (acc.1 ++ [joinSp (parts.drop 2)], acc.2 ++ [joinSp (parts.drop 2)])
        else (acc.1, acc.2)
      else if (parts.headD "" == "type") = true then
        (acc.1, acc.2 ++ [joinSp (parts.drop 1)])
      else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
        (acc.1 ++ ["return"], acc.2)
      else if (parts.headD "" == "rtype") = true then (acc.1, acc.2 ++ ["return"])
      else (acc.1, acc.2)) = classifyStep acc parts := by
  simp only [classifyStep]

/-- The first `for parts in fields` loop (starting `⟨[],[]⟩`) computes
`classify fields`, rendered with the mutable-variable pair (`MProd`) the
`Id.run do` block actually uses. -/
theorem loop1_is_classify (fields : List (List String)) :
    (forIn fields (⟨[], []⟩ : MProd (List String) (List String)) fun parts r =>
        (if (parts.headD "" == "param") = true then
            if (parts.length == 2) = true then
              ForInStep.yield ⟨r.fst ++ [parts.getD 1 ""], r.snd⟩
            else if parts.length > 2 then
              ForInStep.yield ⟨r.fst ++ [joinSp (parts.drop 2)], r.snd ++ [joinSp (parts.drop 2)]⟩
            else ForInStep.yield ⟨r.fst, r.snd⟩
          else if (parts.headD "" == "type") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ [joinSp (parts.drop 1)]⟩
          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩
          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩
          else ForInStep.yield ⟨r.fst, r.snd⟩ : Id _))
      = ⟨(classify fields).1, (classify fields).2⟩ := by
  -- Step 1: the loop body always yields, so rewrite it to `ForInStep.yield (f r parts)`.
  have hbody :
      (fun (parts : List String) (r : MProd (List String) (List String)) =>
        (if (parts.headD "" == "param") = true then
            if (parts.length == 2) = true then
              ForInStep.yield ⟨r.fst ++ [parts.getD 1 ""], r.snd⟩
            else if parts.length > 2 then
              ForInStep.yield ⟨r.fst ++ [joinSp (parts.drop 2)], r.snd ++ [joinSp (parts.drop 2)]⟩
            else ForInStep.yield ⟨r.fst, r.snd⟩
          else if (parts.headD "" == "type") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ [joinSp (parts.drop 1)]⟩
          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩
          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩
          else ForInStep.yield ⟨r.fst, r.snd⟩ : Id _))
      = (fun parts r => ForInStep.yield
          (⟨(classifyStep (r.fst, r.snd) parts).1, (classifyStep (r.fst, r.snd) parts).2⟩
            : MProd (List String) (List String))) := by
    funext parts r
    simp only [classifyStep]
    split_ifs <;> rfl
  rw [hbody, List.forIn_yield_eq_foldl]
  -- Step 2: relate the MProd-valued foldl to the pair-valued `classify` foldl.
  have key : ∀ (fs : List (List String)) (r : MProd (List String) (List String)),
      (fs.foldl (fun r parts =>
          (⟨(classifyStep (r.fst, r.snd) parts).1, (classifyStep (r.fst, r.snd) parts).2⟩
            : MProd (List String) (List String))) r)
        = ⟨(fs.foldl classifyStep (r.fst, r.snd)).1, (fs.foldl classifyStep (r.fst, r.snd)).2⟩ := by
    intro fs
    induction fs with
    | nil => intro r; rfl
    | cons p ps ih => intro r; simp only [List.foldl_cons]; rw [ih]
  rw [key]
  rfl

/-- The second loop's body equals `outStep hasDesc hasType acc entry` for every
entry (the `return`/`returns` skip and the described-but-untyped append). -/
theorem outBodyEq (hasDesc hasType : List String)
    (acc : List (String × String)) (entry : String × String) :
    (if (entry.1 == "return" || entry.1 == "returns") = true then acc
      else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
        acc ++ [("type " ++ entry.1, entry.2)]
      else acc) = outStep hasDesc hasType acc entry := by
  simp only [outStep]

/-- The second `for entry in annotations` loop (starting `[]`), using the
`hasDesc`/`hasType` from loop 1, computes `annotations.foldl (outStep …) []`. -/
theorem loop2_is_outfold (hasDesc hasType : List String)
    (annotations : List (String × String)) :
    (forIn annotations ([] : List (String × String)) fun entry r =>
        (if (entry.1 == "return" || entry.1 == "returns") = true then ForInStep.yield r
          else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
            ForInStep.yield (r ++ [("type " ++ entry.1, entry.2)])
          else ForInStep.yield r : Id _))
      = List.foldl (outStep hasDesc hasType) [] annotations := by
  suffices h : ∀ init, (forIn annotations init fun entry r =>
        (if (entry.1 == "return" || entry.1 == "returns") = true then ForInStep.yield r
          else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
            ForInStep.yield (r ++ [("type " ++ entry.1, entry.2)])
          else ForInStep.yield r : Id _))
      = List.foldl (outStep hasDesc hasType) init annotations by exact h []
  intro init
  induction annotations generalizing init with
  | nil => rfl
  | cons e es ih =>
      simp only [List.forIn_cons, List.foldl_cons]
      split_ifs with h1 h2 <;> simp only [outStep] <;>
        [rw [if_pos h1]; rw [if_neg h1, if_pos h2]; rw [if_neg h1, if_neg h2]] <;>
        exact ih _

/-- Bridge: given that the two loops refine to `classify fields` and to the
`outStep` fold, the imperative program's closing `match/if` on
`annotations.lookup "return"` returns exactly `augmentSpec fields annotations`. -/
theorem tail_match_eq (fields : List (List String))
    (annotations : List (String × String))
    (h1 : (forIn fields (⟨[], []⟩ : MProd (List String) (List String)) fun parts r =>
        (if (parts.headD "" == "param") = true then
            if (parts.length == 2) = true then
              ForInStep.yield ⟨r.fst ++ [parts.getD 1 ""], r.snd⟩
            else if parts.length > 2 then
              ForInStep.yield ⟨r.fst ++ [joinSp (parts.drop 2)], r.snd ++ [joinSp (parts.drop 2)]⟩
            else ForInStep.yield ⟨r.fst, r.snd⟩
          else if (parts.headD "" == "type") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ [joinSp (parts.drop 1)]⟩
          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩
          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩
          else ForInStep.yield ⟨r.fst, r.snd⟩ : Id _))
      = ⟨(classify fields).1, (classify fields).2⟩)
    (h2 : ∀ hasDesc hasType,
      (forIn annotations ([] : List (String × String)) fun entry r =>
          (if (entry.1 == "return" || entry.1 == "returns") = true then ForInStep.yield r
            else if (hasDesc.contains entry.1 && !hasType.contains entry.1) = true then
              ForInStep.yield (r ++ [("type " ++ entry.1, entry.2)])
            else ForInStep.yield r : Id _))
        = List.foldl (outStep hasDesc hasType) [] annotations) :
    implementation_augment fields annotations = augmentSpec fields annotations := by
  unfold implementation_augment
  simp only [Id.run, bind, pure, h1, h2, augmentSpec, classify]
  rfl

theorem correct_augment : ∀ (fields : List (List String))
    (annotations : List (String × String)),
    problem_spec_augment fields annotations
      (implementation_augment fields annotations) := by
  intro fields annotations
  show implementation_augment fields annotations = augmentSpec fields annotations
  exact tail_match_eq fields annotations (loop1_is_classify fields)
    (fun hasDesc hasType => loop2_is_outfold hasDesc hasType annotations)

-- proof-end
