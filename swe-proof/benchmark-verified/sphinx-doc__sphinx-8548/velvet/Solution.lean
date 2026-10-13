import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a foreign callee. The
   behaviour under specification — which documented instance attributes a class
   surfaces, with which docstring, and which class each surfaced member is
   attributed to — is modeled DIRECTLY in the `pure` region
   (`levelCandidates`/`candidates`/`collectStep`/`collected`): the collection is
   concrete data-flow over the inputs, not hidden behind a module-level `axiom`.
   The structural descriptors that feed the collection (a class's inheritance
   hierarchy, the member names each class declares by annotation alone, and the
   documented instance attributes assigned within each class's own namespace) are
   produced by unchanged read-only helpers; their faithful abstraction into the
   inputs `existing` / `hierarchy` is recorded in mapping.md and validated
   against the real helpers by axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- One documented instance attribute as the source analyzer records it: the
   identifier assigned on the instance and the docstring attached to that
   assignment. mapping.md §2 gives the bijection to the repository's attribute
   record. -/
structure AttrDoc where
  name : String
  doc  : String
  deriving Inhabited, DecidableEq, Repr

/- One class of the subject's inheritance hierarchy. `owner` is that class's
   identity; `annots` are the member names it declares by annotation alone — no
   value, hence no docstring — in declaration order, where the empty string
   stands for an annotated identifier that is not reachable under this class's
   name; `attrs` are the documented instance attributes assigned inside this
   class's own namespace, in analyzer order. mapping.md §2. -/
structure ClassLevel where
  owner  : String
  annots : List String
  attrs  : List AttrDoc
  deriving Inhabited, DecidableEq, Repr

/- One surfaced member: its identifier, the identity of the class it is
   attributed to, and its docstring — `none` for a member that exists only as an
   annotation, `some d` for a documented instance attribute. A consumer renders
   `doc` and selects the members to list by comparing `owner` against the class
   being documented, so both components are observable and neither may be left
   unconstrained. mapping.md §2. -/
structure Member where
  name  : String
  owner : String
  doc   : Option String
  deriving Inhabited, DecidableEq, Repr

/- The candidate members one class contributes, in the order the collection meets
   them: first that class's annotation-only names (an annotated identifier not
   reachable under this class's name is passed over), then its own-namespace
   documented instance attributes. Every candidate a class contributes is
   attributed to THAT class — not to the class being documented. -/
def levelCandidates (c : ClassLevel) : List Member :=
  (c.annots.filter (fun n => n != "")).map (fun n => ⟨n, c.owner, none⟩)
    ++ c.attrs.map (fun a => ⟨a.name, c.owner, some a.doc⟩)

/- The whole candidate stream: each class of the hierarchy in turn contributes
   its own two groups. The interleaving is per class — a class's annotations and
   that same class's documented attributes are resolved before the next class is
   considered — so when two classes declare the same identifier in different
   ways, which declaration survives is decided by the position of the
   contributing class in the hierarchy, not by the kind of declaration. -/
def candidates (hierarchy : List ClassLevel) : List Member :=
  (hierarchy.map levelCandidates).flatten

/- Fold one candidate into the running collection. A candidate is accepted
   (appended, preserving discovery order) only when its identifier has not
   already been claimed — either it is already an `existing` member, or an
   earlier candidate of the same name was kept. This is first-occurrence
   precedence: the earliest contributor of an identifier is kept, together with
   its attribution and its docstring, and later namesakes are passed over. -/
def collectStep (existing : List String) (acc : List Member) (m : Member) : List Member :=
  if existing.contains m.name || acc.any (fun x => x.name == m.name) then acc
  else acc ++ [m]

/- The members a class surfaces: fold the candidate stream left-to-right with
   first-occurrence precedence. Because the hierarchy is ordered
   most-derived-first, a member declared on a base class is surfaced precisely
   when no more-derived class (and no `existing` member) already claims its
   identifier — and it is then attributed to the base class that declared it. -/
def collected (existing : List String) (xs : List Member) : List Member :=
  xs.foldl (collectStep existing) []

/- Forward-fold step: extending the consumed prefix by one candidate folds that
   candidate into the collection built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the forward-fold pattern, plan §5.4). -/
lemma foldl_take_step {α β : Type _} [Inhabited α] (f : β → α → β) (xs : List α) (init : β)
    (i : Nat) (hi : i < xs.length) :
    (xs.take (i + 1)).foldl f init = f ((xs.take i).foldl f init) xs[i]! := by
  have hcons : xs.take (i + 1) = xs.take i ++ [xs[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Collect the members a class surfaces from the declarations spread across its
   whole inheritance hierarchy.

   `existing` (the identifiers of members already surfaced from other sources)
   and `hierarchy` (each class's own annotation-only names and own-namespace
   documented instance attributes, ordered most-derived-first) are read-only
   inputs — neither is `mut`: the collection consumes them and never alters them
   (directive 5). The result is exactly the first-occurrence collection over the
   per-class candidate stream, `out = collected existing (candidates hierarchy)`.
   Three consequences a verifying implementation cannot escape:

   * an attribute declared on a base class is surfaced whenever no more-derived
     class and no existing member already claims its identifier — so the
     collection cannot be restricted to the most-derived class alone;
   * every surfaced member carries the `owner` of the class whose declaration it
     came from — so an inherited declaration cannot be attributed to the class
     being documented, which is what decides whether a consumer that lists only
     a class's own members lists it;
   * a class's annotation-only names are resolved together with that same class's
     documented attributes rather than ahead of the entire hierarchy's — so
     whether an annotation of the same identifier suppresses a docstring is
     decided by hierarchy position. -/
method collectInstanceAttrDocs (existing : List String) (hierarchy : List ClassLevel)
    return (out : List Member)
  ensures out = collected existing (candidates hierarchy)
  do
    -- impl-start
    let mut result : List Member := []
    let mut i := 0
    while i < (candidates hierarchy).length
      invariant i ≤ (candidates hierarchy).length
      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
      done_with i = (candidates hierarchy).length
      decreasing (candidates hierarchy).length - i
    do
      let a := (candidates hierarchy)[i]!
      result := collectStep existing result a
      i := i + 1
    return result
    -- impl-end

prove_correct collectInstanceAttrDocs by
  loom_solve
  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
    have hi : i < (candidates hierarchy).length := by omega
    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
  case «ensures_1: out = collected existing (candidates hierarchy)» =>
    injection i_2 with _ hr
    subst hr
    rw [collected, invariant_2, done_1, List.take_length]
