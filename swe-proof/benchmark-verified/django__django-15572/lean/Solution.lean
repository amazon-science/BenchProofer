import Mathlib
-- imports-end

/-!
Collect the set of directory paths that the template watcher should observe.

Two sources contribute directory entries: a list of configured directories, and
a list of loader-provided directories. Each entry is normalized to an absolute
path. Loader entries that point inside the framework's own tree are excluded.
A directory entry that is empty contributes nothing. The collected paths form a
set (membership only; order and repetition are irrelevant).
-/

-- axioms-start
-- Two unchanged path-handling callees, modeled as universally-quantified
-- parameters (the contract holds for ANY such function, so the proof consumes
-- no property of either):
--   * `resolveDir`      : normalize a directory entry to an absolute path.
--   * `isFrameworkPath` : true when a path lies inside the framework's own tree.
-- No `_prop` axiom is required (both callees are passthrough parameters).
-- axioms-end

-- pure-start
-- (no pure helpers needed)
-- pure-end

-- post-conditions-start
/-- A normalized path `p` belongs to the collected set exactly when it is the
normalization of some non-empty configured directory, or of some non-empty
loader directory that is not inside the framework tree. Membership is the only
observable (a set), so the predicate characterizes `result` up to order and
duplication. -/
def problem_spec_collectTemplateDirs
    (resolveDir : String → String) (isFrameworkPath : String → Bool)
    (dirs loaderDirs : List String) (result : List String) : Prop :=
  ∀ p : String,
    p ∈ result ↔
      ((∃ d ∈ dirs, d ≠ "" ∧ resolveDir d = p) ∨
       (∃ d ∈ loaderDirs, d ≠ "" ∧ isFrameworkPath d = false ∧ resolveDir d = p))
-- post-conditions-end

-- impl-start
def implementation_collectTemplateDirs
    (resolveDir : String → String) (isFrameworkPath : String → Bool)
    (dirs loaderDirs : List String) : List String := Id.run do
  let mut items : List String := []
  for dir in dirs do
    if dir ≠ "" then
      items := items ++ [resolveDir dir]
  for directory in loaderDirs do
    if directory ≠ "" ∧ isFrameworkPath directory = false then
      items := items ++ [resolveDir directory]
  return items
-- impl-end

-- proof-start
/-- Closed form for one accumulation loop with a conditional `++ [f x]` body,
generalized over the accumulator. -/
private lemma collectTemplateDirs_loop
    (f : String → String) (p : String → Prop) [DecidablePred p]
    (xs : List String) (init : List String) :
    Id.run (forIn xs init
        (fun x r => if p x then ForInStep.yield (r ++ [f x]) else ForInStep.yield r))
      = init ++ (xs.filter (fun x => decide (p x))).map f := by
  induction xs generalizing init with
  | nil =>
    simp only [List.forIn_nil, Id.run, List.filter_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : p a <;> simp [h, ih, List.append_assoc]

theorem correct_collectTemplateDirs :
    ∀ (resolveDir : String → String) (isFrameworkPath : String → Bool)
      (dirs loaderDirs : List String),
      problem_spec_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs
        (implementation_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs) := by
  intro resolveDir isFrameworkPath dirs loaderDirs
  -- Reduce the two imperative loops to explicit `filter`/`map` closed forms.
  have key : implementation_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs
      = (dirs.filter (fun d => decide (d ≠ ""))).map resolveDir
        ++ (loaderDirs.filter (fun d => decide (d ≠ "" ∧ isFrameworkPath d = false))).map resolveDir := by
    show Id.run (forIn loaderDirs
            (Id.run (forIn dirs ([] : List String)
              (fun dir r => if dir ≠ "" then ForInStep.yield (r ++ [resolveDir dir])
                else ForInStep.yield r)))
            (fun directory r => if directory ≠ "" ∧ isFrameworkPath directory = false
              then ForInStep.yield (r ++ [resolveDir directory]) else ForInStep.yield r))
        = _
    rw [collectTemplateDirs_loop resolveDir (fun d => d ≠ ""),
        collectTemplateDirs_loop resolveDir (fun d => d ≠ "" ∧ isFrameworkPath d = false)]
    simp [List.nil_append]
  rw [key]
  unfold problem_spec_collectTemplateDirs
  intro p
  simp only [List.mem_append, List.mem_map, List.mem_filter, decide_eq_true_eq]
  constructor
  · rintro (⟨d, hd, heq⟩ | ⟨d, ⟨hd, hne, hfw⟩, heq⟩)
    · obtain ⟨hd2, hne⟩ := hd; exact Or.inl ⟨d, hd2, hne, heq⟩
    · exact Or.inr ⟨d, hd, hne, hfw, heq⟩
  · rintro (⟨d, hd, hne, heq⟩ | ⟨d, hd, hne, hfw, heq⟩)
    · exact Or.inl ⟨d, ⟨hd, hne⟩, heq⟩
    · exact Or.inr ⟨d, ⟨hd, hne, hfw⟩, heq⟩
-- proof-end
