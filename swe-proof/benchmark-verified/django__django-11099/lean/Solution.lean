import Mathlib
-- imports-end

/-!
Username admissibility checks.

A username is a finite sequence of characters. Two admissibility checks are
modeled, differing only in which characters they treat as *allowed*:

* one whose allowed set is the English-letter family — English letters, digits,
  the underscore, and the four punctuation characters `.`, `@`, `+`, `-`;
* one whose allowed set is the international-letter family — letters from any
  script, digits, the underscore, and the same four punctuation characters.

In both cases the intended rule is the same and is stated purely over the whole
sequence: a username is admissible exactly when it is non-empty AND every one of
its characters belongs to the relevant allowed set. In particular a sequence is
admissible only if it consists *entirely* of allowed characters from its first
character through its very last; a sequence that carries any non-allowed
character anywhere — including a terminating line-break character — is not
admissible.

The per-character membership test (whether a single character belongs to the
allowed set) is an unchanged building block and is left abstract here; only the
whole-sequence admissibility rule is modeled.
-/

-- axioms-start
/-- Whether a single character belongs to the English-letter allowed set
(English letters, digits, underscore, and `.` `@` `+` `-`). An unchanged
per-character building block; left abstract (its exact membership is
orthogonal to the whole-sequence rule modeled here — see mapping.md). -/
opaque isAllowedAscii : Char → Bool

/-- Whether a single character belongs to the international-letter allowed set
(letters from any script, digits, underscore, and `.` `@` `+` `-`). The
unicode-flavored counterpart of `isAllowedAscii`; likewise abstract. -/
opaque isAllowedUnicode : Char → Bool
-- axioms-end

-- pure-start
-- The whole-sequence admissibility rule is expressed directly with `List.all`
-- and emptiness in the post-condition; no additional functional helper is
-- needed here.
-- pure-end

-- post-conditions-start
/-- Admissibility against the English-letter allowed set: the result is `true`
exactly when the username is non-empty and every character is allowed. The whole
sequence must consist of allowed characters (frame: the result is pinned as this
exact boolean of the input — nothing about the result is left free). -/
def problem_spec_validateAscii (username : List Char) (result : Bool) : Prop :=
  result = (!username.isEmpty && username.all isAllowedAscii)
-- post-conditions-end

-- impl-start
def implementation_validateAscii (username : List Char) : Bool := Id.run do
  if username.isEmpty then
    return false
  let mut ok := true
  for c in username do
    if !isAllowedAscii c then
      ok := false
  return ok
-- impl-end

-- proof-start

-- proof_aux for correct_validateAscii
/-- Closed form for the mutable `ok` after processing a prefix: the AND-fold of
`isAllowedAscii` over the list, starting from `init`. Models the loop body
`if !isAllowedAscii c then ok := false` as `acc && isAllowedAscii c`. -/
def okFold (init : Bool) (l : List Char) : Bool :=
  l.foldl (fun acc c => acc && isAllowedAscii c) init

theorem loop_eq_fold (init : Bool) (l : List Char) :
    (Id.run do
      let mut ok := init
      for c in l do
        if !isAllowedAscii c then
          ok := false
      return ok) = okFold init l := by
  induction l generalizing init with
  | nil => rfl
  | cons c cs ih =>
    rw [show okFold init (c :: cs) = okFold (init && isAllowedAscii c) cs from rfl,
        ← ih]
    simp only [List.forIn_cons, Id.run, bind_pure_comp, map_pure, bind_assoc]
    split <;> simp_all

theorem fold_eq_all (init : Bool) (l : List Char) :
    okFold init l = (init && l.all isAllowedAscii) := by
  unfold okFold
  induction l generalizing init with
  | nil => simp
  | cons c cs ih =>
    simp only [List.foldl_cons, List.all_cons, ih]
    rw [Bool.and_assoc]

theorem empty_branch (username : List Char) (h : username.isEmpty = true) :
    implementation_validateAscii username = false ∧
    (!username.isEmpty && username.all isAllowedAscii) = false := by
  simp only [List.isEmpty_iff] at h
  subst h
  simp [implementation_validateAscii]

theorem correct_validateAscii : ∀ username : List Char,
    problem_spec_validateAscii username (implementation_validateAscii username) := by
  intro username
  unfold problem_spec_validateAscii
  by_cases h : username.isEmpty = true
  · obtain ⟨hl, hr⟩ := empty_branch username h
    rw [hl, hr]
  · unfold implementation_validateAscii
    simp only [h, Bool.false_eq_true, if_false, Bool.not_false, Bool.true_and]
    exact (loop_eq_fold true username).trans
      ((fold_eq_all true username).trans (by simp))

-- proof-end

-- post-conditions-start
/-- Admissibility against the international-letter allowed set: the result is
`true` exactly when the username is non-empty and every character is allowed. -/
def problem_spec_validateUnicode (username : List Char) (result : Bool) : Prop :=
  result = (!username.isEmpty && username.all isAllowedUnicode)
-- post-conditions-end

-- impl-start
def implementation_validateUnicode (username : List Char) : Bool := Id.run do
  if username.isEmpty then
    return false
  let mut ok := true
  for c in username do
    if !isAllowedUnicode c then
      ok := false
  return ok
-- impl-end

-- proof-start
theorem correct_validateUnicode : ∀ username : List Char,
    problem_spec_validateUnicode username (implementation_validateUnicode username) := by
  intro username
  have key : ∀ (l : List Char) (r : Bool),
      (forIn (m := Id) l r (fun c r =>
        if !isAllowedUnicode c then pure (ForInStep.yield false)
        else pure (ForInStep.yield r))) = (r && l.all isAllowedUnicode) := by
    intro l
    induction l with
    | nil => intro r; simp only [List.forIn_nil, List.all_nil, Bool.and_true]; rfl
    | cons a as ih =>
      intro r
      rw [List.forIn_cons]
      by_cases h : isAllowedUnicode a
      · simp only [h, Bool.not_true, Bool.false_eq_true, ↓reduceIte, ih, List.all_cons, Bool.true_and]
        rfl
      · simp only [h, Bool.not_false, ↓reduceIte, ih, List.all_cons, Bool.false_and, Bool.and_false]
        rfl
  unfold problem_spec_validateUnicode implementation_validateUnicode
  cases username with
  | nil => rfl
  | cons a as =>
    simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, ↓reduceIte, bind_pure_comp, map_pure]
    rw [show (forIn (m := Id) (a::as) true (fun c r => if !isAllowedUnicode c then pure (ForInStep.yield false) else pure (ForInStep.yield r))) = _ from key (a::as) true]
    simp

-- proof-end
