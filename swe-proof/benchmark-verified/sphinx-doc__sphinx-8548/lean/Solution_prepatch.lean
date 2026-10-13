import Mathlib
-- imports-end

/-!
Collecting a class's documented member attributes across its inheritance chain.

A class's documentation lists, among other things, its *member attributes*: names
that stand for per-instance data rather than for a value held by the class itself.
Two sources contribute them. A class body may *declare* such a member by
annotating it (`attr : int`), which supplies a name but no documentation at all.
A class body may also *document* one by attaching a comment-style docstring to an
assignment (`self.attr = …  #: doc`); the analysis of the module that defines the
class records every such attribute under a search key pairing a *namespace* — the
qualified name of the class the attribute belongs to — with the attribute name.

To document a class we walk its inheritance chain, the class itself first and then
its base classes in order. For each class on the chain we consult, in this order,
that class's own annotation-declared names and then the attributes recorded under
*that* class's own namespace; either kind is added to the member table only if a
member of that name is not already present. Because the chain is walked
most-derived first under this first-occurrence-wins rule, a name introduced only
by a base class is still picked up — this is what lets an *inherited* attribute
appear in a derived class's documentation — while a name that a class nearer the
front of the chain also supplies keeps that nearer occurrence.

Consulting each class's two sources together, one class at a time, is what settles
the case where a name is declared by one class on the chain and documented by
another: the class nearer the front of the chain wins, with whichever of the two
kinds it supplies. A bare declaration therefore does not pre-empt documentation
recorded for a class ahead of it on the chain.

Collecting a member is not only a decision about *whether* the name belongs in the
table. Each entry also records **which class supplied it**, and for either kind of
source that class is the one being visited when the entry was made: the class whose
own annotation declared the name, or the class whose own namespace the recorded
attribute matched — never the class the documentation was requested for. That
recorded class is observable and load-bearing: a reader of the table asks it which
members a class supplies *itself*, as against the ones it only takes over from an
ancestor, so attributing an ancestor's member to the class being documented is a
different table even when the names and documentation are identical. A class's own
namespace *key* and its *identity* are two different data: the key is the name an
entry must be recorded under to belong to the class, while the identity is the
class itself, and two classes on one chain may share a qualified name and still be
different classes.

We start from `initial`, the member table the earlier collection passes already
populated, and return the table after the chain walk. The table is an association
list, in insertion order, from member name to its documentation and the class that
supplied it: the documentation is `none` for a member that was only declared and
`some doc` for one whose docstring was recorded, and the supplying class is `none`
for a member the earlier passes attributed to no class at all.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. Each chain member's identity,
-- namespace key, annotation-declared names and recorded documented attributes are
-- INPUTS to the modeled function (`ClassInfo.classKey` / `ClassInfo.nsKey` /
-- `ClassInfo.annNames` / `ClassInfo.attrDocs`), and the inheritance chain is an
-- input as well; the collection behavior itself is modeled deeply in the `pure`
-- region. Hence no `opaque`/`axiom` declarations.
-- axioms-end

-- pure-start
/-- One class on the inheritance chain, as far as this collection pass is
concerned: its own identity, its own namespace key, the names it declares by
annotation alone, and the documented attributes recorded for the module that
defines it. Each documented attribute is a triple `(entry namespace, attribute
name, docstring)`. -/
structure ClassInfo where
  /-- The class's own identity, distinct from every other class on the chain. This
  is what a member the class supplies records as its supplier. -/
  classKey : String
  /-- The class's own namespace key (its qualified name): the namespace a recorded
  attribute must carry to belong to this class. -/
  nsKey    : String
  /-- The names this class declares by annotation alone. Such a member carries a
  name but no documentation. -/
  annNames : List String
  /-- The documented attributes recorded for this class's module: triples of
  `(entry namespace, attribute name, docstring)`. -/
  attrDocs : List (String × String × String)
deriving Repr, Inhabited

/-- One entry of the member table. -/
structure MemberEntry where
  /-- The member's name. The table is filed under this name and the entry carries
  it: one datum, not two. -/
  name  : String
  /-- The member's documentation: `none` for a member that was only declared,
  `some doc` for one whose docstring was recorded. -/
  doc   : Option String
  /-- The identity of the class that supplied this member, `none` for a member no
  class is recorded for. -/
  owner : Option String
deriving Repr, DecidableEq, Inhabited

/-- Fold one class's annotation-declared names into the member table. Such a name
is added iff no member of that name is already present (first occurrence wins),
with no documentation and with this class recorded as its supplier. -/
def addAnnotations (owner : String) :
    List String → List MemberEntry → List MemberEntry
  | [], members => members
  | name :: rest, members =>
      addAnnotations owner rest
        (if name ∉ members.map MemberEntry.name then
           members ++ [⟨name, none, some owner⟩]
         else members)

/-- Fold one class's documented attributes into the member table. An attribute is
added iff its recorded namespace is exactly this class's own namespace key and no
member of that name is already present (first occurrence wins), with its docstring
and with this class recorded as its supplier. -/
def addEntries (nsKey owner : String) :
    List (String × String × String) → List MemberEntry → List MemberEntry
  | [], members => members
  | entry :: rest, members =>
      addEntries nsKey owner rest
        (if entry.fst = nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
           members ++ [⟨entry.snd.fst, some entry.snd.snd, some owner⟩]
         else members)

/-- Walk the inheritance chain, most-derived first, folding each class's two
sources into the member table one class at a time: that class's
annotation-declared names first, then the attributes recorded under its own
namespace. Each entry either fold makes records the class being visited as the
member's supplier. -/
def gatherMemberDocs : List ClassInfo → List MemberEntry → List MemberEntry
  | [], members => members
  | cls :: rest, members =>
      gatherMemberDocs rest
        (addEntries cls.nsKey cls.classKey cls.attrDocs
          (addAnnotations cls.classKey cls.annNames members))
-- pure-end

-- post-conditions-start
/-- The member table after the inheritance-chain walk. `mro` is the chain
(most-derived first) and `initial` is the table the earlier passes already
populated. The result is exactly the table obtained by walking the whole chain,
adding for each class in turn its annotation-declared names and then its own
recorded documented attributes — each with the visited class recorded as its
supplier — under a first-occurrence-wins rule. -/
def problem_spec_gatherMemberDocs
    (mro : List ClassInfo) (initial : List MemberEntry)
    (result : List MemberEntry) : Prop :=
  result = gatherMemberDocs mro initial
-- post-conditions-end

-- impl-start
def implementation_gatherMemberDocs
    (mro : List ClassInfo) (initial : List MemberEntry) :
    List MemberEntry := Id.run do
  let mut members := initial
  -- The annotation-declared names of every class on the chain are collected in a
  -- pass of their own, run to completion first; only afterwards are documented
  -- attributes consulted, and then only those recorded under the TARGET class's
  -- own namespace (the head of the chain), each credited to the TARGET class.
  -- Documented attributes recorded for a base class are never consulted, and a
  -- bare declaration anywhere on the chain pre-empts documentation recorded for a
  -- class ahead of it.
  for cls in mro do
    for name in cls.annNames do
      if name ∉ members.map MemberEntry.name then
        members := members ++ [⟨name, none, some cls.classKey⟩]
  match mro with
  | [] => pure ()
  | target :: _ =>
    for entry in target.attrDocs do
      if entry.fst = target.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then
        members := members ++
          [⟨entry.snd.fst, some entry.snd.snd, some target.classKey⟩]
  return members
-- impl-end

-- proof-start
/-- The loop over a class's annotation-declared names matches `addAnnotations`,
generalized over the accumulator. -/
theorem ann_helper (owner : String) (names : List String) :
    ∀ (members : List MemberEntry),
      Id.run (forIn names members fun name r =>
        if name ∉ List.map MemberEntry.name r then do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [⟨name, none, some owner⟩]))
        else do
          pure PUnit.unit
          pure (ForInStep.yield r))
      = addAnnotations owner names members := by
  induction names with
  | nil => intro members; rfl
  | cons a as ih =>
    intro members
    rw [List.forIn_cons]
    simp only [Id.run, bind, addAnnotations] at ih ⊢
    by_cases h : a ∉ List.map MemberEntry.name members
    · simp only [if_pos h, ih]
    · simp only [if_neg h, ih]

/-- The loop over a class's documented attributes matches `addEntries`,
generalized over the accumulator. -/
theorem inner_helper (nsKey owner : String)
    (entries : List (String × String × String)) :
    ∀ (members : List MemberEntry),
      Id.run (forIn entries members fun entry r =>
        if entry.1 = nsKey ∧ entry.2.1 ∉ List.map MemberEntry.name r then do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [⟨entry.2.1, some entry.2.2, some owner⟩]))
        else do
          pure PUnit.unit
          pure (ForInStep.yield r))
      = addEntries nsKey owner entries members := by
  induction entries with
  | nil => intro members; rfl
  | cons a as ih =>
    intro members
    rw [List.forIn_cons]
    simp only [Id.run, bind, addEntries] at ih ⊢
    by_cases h : a.1 = nsKey ∧ a.2.1 ∉ List.map MemberEntry.name members
    · simp only [if_pos h, ih]
    · simp only [if_neg h, ih]

/-- The walk over the inheritance chain matches `gatherMemberDocs`, generalized
over the accumulator. -/
theorem outer_helper (mro : List ClassInfo) :
    ∀ (members : List MemberEntry),
      Id.run (forIn mro members fun cls r => do
        let r ← forIn cls.annNames r fun name r =>
          if name ∉ List.map MemberEntry.name r then do
            pure PUnit.unit
            pure (ForInStep.yield (r ++ [⟨name, none, some cls.classKey⟩]))
          else do
            pure PUnit.unit
            pure (ForInStep.yield r)
        let r ← forIn cls.attrDocs r fun entry r =>
          if entry.1 = cls.nsKey ∧ entry.2.1 ∉ List.map MemberEntry.name r then do
            pure PUnit.unit
            pure (ForInStep.yield
              (r ++ [⟨entry.2.1, some entry.2.2, some cls.classKey⟩]))
          else do
            pure PUnit.unit
            pure (ForInStep.yield r)
        pure PUnit.unit
        pure (ForInStep.yield r))
      = gatherMemberDocs mro members := by
  induction mro with
  | nil => intro members; rfl
  | cons a as ih =>
    intro members
    rw [List.forIn_cons]
    simp only [Id.run, bind, gatherMemberDocs] at ih ⊢
    rw [← ann_helper a.classKey a.annNames members]
    rw [← inner_helper a.nsKey a.classKey a.attrDocs]
    simp only [Id.run, bind] at *
    rw [ih]

-- Two concrete chains on which THIS implementation contradicts the
-- specification, both decided by `decide` (so the rejection below is semantic,
-- not an artifact of a proof script that happens not to close).
--
-- (1) A documented attribute recorded for a BASE class is dropped entirely.
example : ¬ problem_spec_gatherMemberDocs
    [⟨"D", "m.D", [], []⟩, ⟨"B", "m.B", [], [("m.B", "attr", "doc")]⟩] []
    (implementation_gatherMemberDocs
      [⟨"D", "m.D", [], []⟩, ⟨"B", "m.B", [], [("m.B", "attr", "doc")]⟩] []) := by
  unfold problem_spec_gatherMemberDocs implementation_gatherMemberDocs
  decide

-- (2) A name a BASE class merely declares pre-empts the documentation recorded
-- for the class ahead of it, so both the docstring and the recorded supplying
-- class come out wrong.
example : ¬ problem_spec_gatherMemberDocs
    [⟨"D", "m.D", [], [("m.D", "attr", "doc")]⟩, ⟨"B", "m.B", ["attr"], []⟩] []
    (implementation_gatherMemberDocs
      [⟨"D", "m.D", [], [("m.D", "attr", "doc")]⟩, ⟨"B", "m.B", ["attr"], []⟩] []) := by
  unfold problem_spec_gatherMemberDocs implementation_gatherMemberDocs
  decide

-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- implementation it cannot close: a chain whose base class carries a documented
-- attribute absent from the target class is dropped here, a name a base class
-- merely declares suppresses documentation recorded for a class ahead of it, and a
-- documented attribute is credited to the target class rather than to the class
-- whose own namespace it matched — the discriminating clauses.
theorem correct_gatherMemberDocs :
    ∀ (mro : List ClassInfo) (initial : List MemberEntry),
      problem_spec_gatherMemberDocs mro initial
        (implementation_gatherMemberDocs mro initial) := by
  intro mro initial
  unfold problem_spec_gatherMemberDocs implementation_gatherMemberDocs
  exact outer_helper mro initial
-- proof-end
