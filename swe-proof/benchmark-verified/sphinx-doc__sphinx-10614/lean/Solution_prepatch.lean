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
-- PRE-PATCH (buggy) skeleton: for the scalable-vector format the destination URI
-- is prefixed with "../" and the in-page anchor link is prefixed with "../" as
-- well, and every destination URI is keyed by the reference title regardless of
-- whether the reference is internal or in a separate project.
def implementation_buildUrls (isSVG : Bool) (currentFilename : String)
    (children : List Xref) : List (String × String) := Id.run do
  let mut urls : List (String × String) := []
  for child in children do
    match child.refuri with
    | some uri =>
        if isSVG then
          urls := urls ++ [(child.reftitle, "../" ++ uri)]
        else
          urls := urls ++ [(child.reftitle, uri)]
    | none =>
        match child.refid with
        | some rid =>
            if isSVG then
              urls := urls ++ [(child.reftitle, "../" ++ currentFilename ++ "#" ++ rid)]
            else
              urls := urls ++ [(child.reftitle, "#" ++ rid)]
        | none => pure ()
  return urls
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- pre-patch implementation it cannot close: for the scalable-vector format the
-- produced URL carries a "../" prefix the specification forbids, and a
-- separate-project destination URI is keyed by the reference title rather than the bare target
-- name. The `rfl` bridge from the `do`-block to the clean accumulator loop fails,
-- since the loop bodies differ on exactly those discriminating clauses.
theorem buildUrls_loop (isSVG : Bool) (currentFilename : String) :
    ∀ (children : List Xref) (acc : List (String × String)),
      (Id.run (forIn children acc fun child r =>
        (match child.refuri with
        | some uri =>
          if (!child.internal) = true then
            (ForInStep.yield (r ++ [(uriTail uri, uri)]))
          else
            (ForInStep.yield (r ++ [(child.reftitle, uri)]))
        | none =>
          match child.refid with
          | some rid =>
            if isSVG = true then
              (ForInStep.yield (r ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]))
            else
              (ForInStep.yield (r ++ [(child.reftitle, "#" ++ rid)]))
          | none => (ForInStep.yield r) : Id (ForInStep (List (String × String))))))
      = acc ++ children.filterMap (entryFor isSVG currentFilename) := by
  intro children
  induction children with
  | nil => intro acc; simp only [List.forIn_nil, Id.run, pure, List.filterMap_nil,
      List.append_nil]
  | cons c cs ih =>
    intro acc
    rw [List.forIn_cons, List.filterMap_cons]
    simp only [Id.run, bind] at ih ⊢
    simp only [ih]
    cases hu : c.refuri with
    | some uri =>
        simp only [entryFor, hu]
        by_cases hi : c.internal
        · simp only [hi, Bool.not_true, Bool.false_eq_true, if_false, if_true,
            List.append_assoc, List.cons_append, List.nil_append]
        · simp only [hi, Bool.not_false, if_true, if_false, Bool.false_eq_true,
            List.append_assoc, List.cons_append, List.nil_append]
    | none =>
        simp only [entryFor, hu]
        cases hr : c.refid with
        | some rid =>
            by_cases hs : isSVG
            · simp only [hs, if_true, List.append_assoc, List.cons_append, List.nil_append]
            · simp only [hs, Bool.false_eq_true, if_false, List.append_assoc,
                List.cons_append, List.nil_append]
        | none => rfl

theorem correct_buildUrls :
    ∀ (isSVG : Bool) (currentFilename : String) (children : List Xref),
      problem_spec_buildUrls isSVG currentFilename children
        (implementation_buildUrls isSVG currentFilename children) := by
  intro isSVG currentFilename children
  unfold problem_spec_buildUrls implementation_buildUrls
  have hbridge :
      (Id.run do
        let mut urls : List (String × String) := []
        for child in children do
          match child.refuri with
          | some uri =>
              let mut refname := child.reftitle
              if !child.internal then refname := uriTail uri
              urls := urls ++ [(refname, uri)]
          | none =>
              match child.refid with
              | some rid =>
                  if isSVG then
                    urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
                  else
                    urls := urls ++ [(child.reftitle, "#" ++ rid)]
              | none => pure ()
        return urls)
      = (Id.run (forIn children [] fun child r =>
          (match child.refuri with
          | some uri =>
            if (!child.internal) = true then
              (ForInStep.yield (r ++ [(uriTail uri, uri)]))
            else
              (ForInStep.yield (r ++ [(child.reftitle, uri)]))
          | none =>
            match child.refid with
            | some rid =>
              if isSVG = true then
                (ForInStep.yield (r ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]))
              else
                (ForInStep.yield (r ++ [(child.reftitle, "#" ++ rid)]))
            | none => (ForInStep.yield r) : Id (ForInStep (List (String × String)))))) := rfl
  rw [hbridge, buildUrls_loop isSVG currentFilename children [], List.nil_append]
-- proof-end
