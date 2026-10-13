import Mathlib
-- imports-end

/-!
Collecting the accepted entries of a table-of-contents directive.

A table-of-contents directive lists, one per line, references to other documents
that should appear in the tree. When the directive is processed, each listed
reference is examined and either accepted as an entry of the tree or rejected.

A reference is accepted when it names a document that the project actually
contains. In addition to the ordinary source documents, a documentation build
always provides a small constant set of *special reference pages* — the general
index, the module index, and the search page — which exist even though they have
no source file of their own. A reference to one of these special pages is just
as valid a target as a reference to an ordinary document, so it too is accepted.

Blank lines carry no reference and are ignored. Every other reference — one that
names neither an existing document nor one of the special reference pages — is
rejected and contributes no entry.

The accepted entries are kept in the order in which they are listed.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each decision
-- the collection makes is over directly-supplied observations: the list of
-- listed references, the names of the documents that exist, and the names of the
-- special reference pages the build always provides. Whether a reference is
-- accepted is a blankness test plus a membership test against the union of those
-- two name collections — both spelled out directly in the implementation — so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (No standalone functional helpers are needed: the accepted-entry relation is
-- stated directly as a `filter`/`map` over the listed references.)
-- pure-end

-- post-conditions-start
/-- The entries accepted from a table-of-contents directive body.

`requested` is the list of references listed in the directive (one per line),
`existingDocs` the names of the documents the project contains, and
`generatedPages` the names of the special reference pages the build always
provides (the general index, the module index, and the search page).

The result is the list of `(title, target)` pairs accepted as tree entries: a
reference contributes an entry exactly when it is non-blank AND names either an
existing document or one of the special reference pages, and the accepted entries
appear in their original order, each with no explicit title (`none`) and its own
name as the target. (Directive 5 frame: the full entry list is pinned as a
function of the inputs — nothing is left unconstrained; Directive 8: the result
is grounded entirely in `requested`/`existingDocs`/`generatedPages`.) -/
def problem_spec_tocEntries
    (requested existingDocs generatedPages : List String)
    (result : List (Option String × String)) : Prop :=
  result =
    (requested.filter
      (fun e => e != "" && (existingDocs ++ generatedPages).contains e)).map
      (fun e => ((none : Option String), e))
-- post-conditions-end

-- impl-start
def implementation_tocEntries
    (requested existingDocs generatedPages : List String) :
    List (Option String × String) := Id.run do
  let mut entries : List (Option String × String) := []
  for entry in requested do
    if entry == "" then
      -- a blank line carries no reference and is ignored
      pure ()
    else if (existingDocs ++ generatedPages).contains entry then
      entries := entries ++ [((none : Option String), entry)]
    else
      -- a reference to no existing document and no special reference page:
      -- rejected, contributing no entry
      pure ()
  return entries
-- impl-end


-- proof-start
theorem correct_tocEntries :
    ∀ (requested existingDocs generatedPages : List String),
      problem_spec_tocEntries requested existingDocs generatedPages
        (implementation_tocEntries requested existingDocs generatedPages) := by
  intro requested existingDocs generatedPages
  unfold problem_spec_tocEntries implementation_tocEntries
  simp only [Id.run, bind_pure_comp, map_pure]
  have key : ∀ (rs : List String) (acc : List (Option String × String)),
      (forIn (m := Id) rs acc (fun entry entries =>
        if entry == "" then pure (ForInStep.yield entries)
        else if (existingDocs ++ generatedPages).contains entry then
          pure (ForInStep.yield (entries ++ [((none : Option String), entry)]))
        else pure (ForInStep.yield entries))) =
      acc ++ (rs.filter (fun e => e != "" && (existingDocs ++ generatedPages).contains e)).map
        (fun e => ((none : Option String), e)) := by
    intro rs
    induction rs with
    | nil => intro acc; simp only [List.forIn_nil, List.filter_nil, List.map_nil,
        List.append_nil]; rfl
    | cons r rs ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [List.filter_cons]
      by_cases h1 : (r == "") = true
      · have hne : (r != "") = false := by simp [bne, h1]
        simp only [h1, if_true, hne, Bool.false_and, Bool.false_eq_true, if_false]
        show (forIn (m := Id) rs acc _) = _
        rw [ih]
      · have hne : (r != "") = true := by simp [bne, h1]
        by_cases h2 : ((existingDocs ++ generatedPages).contains r) = true
        · simp only [h1, if_false, h2, if_true, hne, Bool.and_self, List.map_cons]
          show (forIn (m := Id) rs (acc ++ [((none:Option String), r)]) _) = _
          rw [ih]; simp [List.append_assoc]
        · simp only [h1, if_false, h2, hne, Bool.and_false, Bool.false_eq_true, if_false]
          show (forIn (m := Id) rs acc _) = _
          rw [ih]
  rw [key]
  simp

-- proof-end
