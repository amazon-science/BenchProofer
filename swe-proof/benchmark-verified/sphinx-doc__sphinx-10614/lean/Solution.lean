import Mathlib
-- imports-end

/-!
Building the clickable link map for an inheritance diagram image.

A diagram lists a number of classes; each class may carry a cross-reference that
the rendered image turns into a clickable link. This step walks those references
and assembles a mapping from a *key* (the text used to match a node in the image)
to the *link URL* recorded for that node.

The inputs are:

  * a flag selecting the output image format — whether the diagram is emitted as a
    scalable vector image (embedded as a standalone object) or as a raster image
    placed inline on the page;
  * the document name of the page currently being rendered (used to build links to
    anchors within that same page);
  * the list of references, each of which provides
      - an optional resolved destination URI (a link to another document),
      - an optional in-page anchor identifier,
      - the reference's title (its fully-qualified class name), and
      - whether the reference resolves inside this same project, or points to a
        separate project.

For each reference exactly one of two cases applies:

  * It has a destination URI. The recorded link URL is that URI exactly, for both
    image formats. When the reference points inside this project, it is keyed by
    its title; when it points to a separate project, it is keyed by the trailing
    component of the URI that follows the final fragment separator (the bare target
    name), since the title need not match the separate project's naming.
  * Otherwise it has an in-page anchor. For the inline raster format the link is a
    pure in-page anchor (`#` followed by the identifier). For the scalable vector
    format — which lives in its own file alongside the page — the link is written
    relative to that image file's location, namely the current document name
    followed by the anchor.

References providing neither a destination URI nor an anchor contribute nothing.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Splitting a URI
-- at its final fragment separator, and the assembly of each link string, are
-- modeled directly as string operations over the inputs; there is no opaque
-- callee whose contract the proof must assume.
-- axioms-end

-- pure-start
/-- One cross-reference attached to a class in the diagram. `refuri` is the
resolved destination of a link to another document (absent for an in-page
anchor); `refid` is an in-page anchor identifier (absent for a document link);
`reftitle` is the fully-qualified class name; `internal` is `true` when the
reference resolves within this project and `false` when it targets a separate
project. -/
structure Xref where
  refuri   : Option String
  refid    : Option String
  reftitle : String
  internal : Bool
deriving DecidableEq, Repr, Inhabited

/-- The trailing component of a URI after its final fragment separator (`#`):
the bare target name. A URI with no separator yields itself. -/
def uriTail (s : String) : String :=
  match (s.splitOn "#").reverse with
  | []          => s
  | last :: _   => last

/-- The single mapping entry contributed by one reference, or `none` when the
reference carries neither a destination URI nor an in-page anchor.

  * a destination URI gives entry `(key, uri)`, where `key` is the bare target
    name (`uriTail uri`) for a reference into a separate project and the title otherwise — the
    same URL for both image formats;
  * otherwise an in-page anchor gives entry `(title, link)`, where `link` is the
    current document name followed by the anchor for the scalable vector format,
    and a pure in-page anchor for the inline raster format. -/
def entryFor (isSVG : Bool) (currentFilename : String) (c : Xref)
    : Option (String × String) :=
  match c.refuri with
  | some uri =>
      let key := if c.internal then c.reftitle else uriTail uri
      some (key, uri)
  | none =>
      match c.refid with
      | some rid =>
          if isSVG then some (c.reftitle, currentFilename ++ "#" ++ rid)
          else some (c.reftitle, "#" ++ rid)
      | none => none
-- pure-end

-- post-conditions-start
/-- The link map is exactly the in-order list of entries contributed by the
references: each reference contributes `entryFor` and references contributing
nothing are dropped. The result is fully determined by the inputs in every case —
no entry, key, or URL is left free. -/
def problem_spec_buildUrls (isSVG : Bool) (currentFilename : String)
    (children : List Xref) (result : List (String × String)) : Prop :=
  result = children.filterMap (entryFor isSVG currentFilename)
-- post-conditions-end

-- impl-start
def implementation_buildUrls (isSVG : Bool) (currentFilename : String)
    (children : List Xref) : List (String × String) := Id.run do
  let mut urls : List (String × String) := []
  for child in children do
    match child.refuri with
    | some uri =>
        let mut refname := child.reftitle
        if !child.internal then
          refname := uriTail uri
        urls := urls ++ [(refname, uri)]
    | none =>
        match child.refid with
        | some rid =>
            if isSVG then
              urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
            else
              urls := urls ++ [(child.reftitle, "#" ++ rid)]
        | none => pure ()
  return urls
-- impl-end


-- proof-start
/-- The list appended to the accumulator by one iteration of the loop for a
given `child`: the exact computed effect of the loop body in
`implementation_buildUrls`. -/
def bodyContribution (isSVG : Bool) (currentFilename : String) (c : Xref)
    : List (String × String) :=
  match c.refuri with
  | some uri =>
      let key := if c.internal then c.reftitle else uriTail uri
      [(key, uri)]
  | none =>
      match c.refid with
      | some rid =>
          if isSVG then [(c.reftitle, currentFilename ++ "#" ++ rid)]
          else [(c.reftitle, "#" ++ rid)]
      | none => []

theorem desugar_to_foldl (isSVG : Bool) (currentFilename : String)
    (children : List Xref) :
    implementation_buildUrls isSVG currentFilename children
      = List.foldl
          (fun acc child => acc ++ bodyContribution isSVG currentFilename child)
          [] children := by
  simp only [implementation_buildUrls, Id.run, bind, pure, Id.instMonad]
  have hbody :
      (fun (child : Xref) (r : List (String × String)) =>
          match child.refuri with
          | some uri =>
            if (!child.internal) = true then ForInStep.yield (r ++ [(uriTail uri, uri)])
            else ForInStep.yield (r ++ [(child.reftitle, uri)])
          | none =>
            match child.refid with
            | some rid =>
              if isSVG = true then ForInStep.yield (r ++ [(child.reftitle, currentFilename ++ "#" ++ rid)])
              else ForInStep.yield (r ++ [(child.reftitle, "#" ++ rid)])
            | none => ForInStep.yield r)
        = (fun (child : Xref) (r : List (String × String)) =>
            ForInStep.yield (r ++ bodyContribution isSVG currentFilename child)) := by
    funext child r
    simp only [bodyContribution]
    cases child.refuri with
    | some uri =>
      by_cases hi : child.internal <;> simp [hi]
    | none =>
      cases child.refid with
      | some rid => by_cases hs : isSVG <;> simp [hs]
      | none => simp
  suffices h : ∀ (init : List (String × String)),
      (forIn (m := Id) children init fun child r =>
          match child.refuri with
          | some uri =>
            if (!child.internal) = true then ForInStep.yield (r ++ [(uriTail uri, uri)])
            else ForInStep.yield (r ++ [(child.reftitle, uri)])
          | none =>
            match child.refid with
            | some rid =>
              if isSVG = true then ForInStep.yield (r ++ [(child.reftitle, currentFilename ++ "#" ++ rid)])
              else ForInStep.yield (r ++ [(child.reftitle, "#" ++ rid)])
            | none => ForInStep.yield r)
        = List.foldl
            (fun acc child => acc ++ bodyContribution isSVG currentFilename child) init children by
    exact h []
  intro init
  induction children generalizing init with
  | nil => rfl
  | cons c cs ih =>
    simp only [List.forIn_cons, List.foldl_cons, bodyContribution]
    cases hu : c.refuri with
    | some uri =>
      by_cases hi : c.internal <;>
        (simp only [hi, Bool.not_true, Bool.not_false, if_true]; exact ih _)
    | none =>
      cases hd : c.refid with
      | some rid =>
        cases isSVG <;>
          (simp only [Bool.false_eq_true, if_true, if_false]; exact ih _)
      | none => simp only [List.append_nil]; exact ih _

theorem bodyContribution_eq_entryFor (isSVG : Bool) (currentFilename : String)
    (c : Xref) :
    bodyContribution isSVG currentFilename c
      = (entryFor isSVG currentFilename c).toList := by
  rcases c with ⟨ru, rid, rt, int⟩
  cases ru <;> cases rid <;> simp [bodyContribution, entryFor] <;> (try split) <;> rfl

theorem fold_eq_filterMap (isSVG : Bool) (currentFilename : String)
    (acc : List (String × String)) (l : List Xref) :
    List.foldl
        (fun a child => a ++ bodyContribution isSVG currentFilename child) acc l
      = acc ++ l.filterMap (entryFor isSVG currentFilename) := by
  induction l generalizing acc with
  | nil => simp
  | cons x xs ih =>
    rw [List.foldl_cons, ih, List.filterMap_cons,
        bodyContribution_eq_entryFor]
    cases entryFor isSVG currentFilename x with
    | none => simp
    | some e => simp [List.append_assoc]

theorem correct_buildUrls :
    ∀ (isSVG : Bool) (currentFilename : String) (children : List Xref),
      problem_spec_buildUrls isSVG currentFilename children
        (implementation_buildUrls isSVG currentFilename children) := by
  intro isSVG currentFilename children
  unfold problem_spec_buildUrls
  rw [desugar_to_foldl, fold_eq_filterMap]
  rw [List.nil_append]

-- proof-end
