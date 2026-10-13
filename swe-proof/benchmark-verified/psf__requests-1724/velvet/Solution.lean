import Velvet.Std
-- imports-end

/- TOTAL correctness. The real method-handling step is a bounded pass over a
   finite method name, so a diverging implementation must NOT satisfy this spec:
   under partial correctness a non-terminating body discharges all three
   `ensures` clauses vacuously and verifies, while its faithful counterpart hangs
   the failing test and does not resolve.

   The `open` is the line that selects the scope, not the `set_option`: both
   namespaces define `WPGen.forWithInvariantLoop`, the later `open` wins, and
   `PartialCorrectness`'s version takes the loop measure and DISCARDS it. So
   `"total"` with `open PartialCorrectness` reads as total and checks as partial.
   Measured here: a spliced diverging loop with the constant measure
   `decreasing spin` fails with `case «decreasing_1: spin» ⊢ False` under
   `TotalCorrectness` and verifies, exit 0, under `PartialCorrectness`. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No module-level `axiom`. The unchanged callee the construction site applies
--  to the supplied method before any further processing — a native-flavour text
--  constructor — is modeled as an imperative-callee `:|` stub inside the impl
--  (`flavour :| flavour = true`, §3): sound by construction, with the weakest
--  sufficient contract pinned (the produced value IS of the native flavour,
--  independent of the argument flavour) and validated against the real callee by
--  axiom_check.py (G-AX). See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- Case-normalisation of a single code point: an ASCII lowercase letter maps to
   its uppercase partner; every other code point passes through unchanged. -/
def upperCp (c : Char) : Char :=
  if 'a' ≤ c ∧ c ≤ 'z' then Char.ofNat (c.toNat - 32) else c

/- Case-normalisation of a whole sequence: the per-code-point upper map.
   Front-recursive so a single unfold is available per loop step (the Velvet
   backward-fold pattern, plan §5.4). -/
def upperSeq : List Char → List Char
  | []      => []
  | c :: cs => upperCp c :: upperSeq cs

@[grind] lemma upperSeq_nil : upperSeq [] = [] := rfl
@[grind] lemma upperSeq_cons (c : Char) (cs : List Char) :
    upperSeq (c :: cs) = upperCp c :: upperSeq cs := rfl
-- pure-end

/- The minimal carrier of the two aspects of a text value the desired behaviour
   touches: the code-point content (`chars`) and whether the value is of the
   native text flavour (`native`). Every other aspect of the surrounding
   constructed object is forwarded unchanged and irrelevant here, so it is
   omitted (mapping.md §2). -/
structure TextToken where
  chars  : List Char
  native : Bool
  deriving DecidableEq, Inhabited

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The method-handling step of request construction.

   It is handed a caller-supplied method name (`text`, its code-point content)
   together with a boolean recording the textual flavour the caller supplied
   (`native`: whether the supplied value was already of the native flavour). It
   returns the `TextToken` carried into the constructed request.

   Desired behaviour:
   * Content — the carried method is the case-normalised supplied name: every
     code point is upper-cased per `upperSeq` and the length is preserved.
   * Flavour — the carried method is of the native text flavour, irrespective of
     the flavour the caller supplied. The carried flavour must NOT depend on the
     `native` input: even a non-native supplied name yields a native carrier.

   `text` and `native` are read-only (neither `mut`): the routine reads them and
   builds a fresh token, mutating nothing it is handed (directive 5). -/
method normalizeMethod (text : List Char) (native : Bool) return (out : TextToken)
  ensures out.chars = upperSeq text
  ensures out.chars.length = text.length
  ensures out.native = true
  do
    -- impl-start
    -- Coerce the supplied method to the native text flavour FIRST, via the
    -- native-flavour constructor (an unchanged callee, modeled as a `:|` stub
    -- whose produced value is native irrespective of the supplied flavour).
    let flavour :| flavour = true
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = upperSeq (text.drop i)
      done_with i = 0
      decreasing i
    do
      let c := text[i - 1]!
      result := upperCp c :: result
      i := i - 1
    return { chars := result, native := flavour }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `upperSeq` peels one `upperCp`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma upperSeq_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    upperSeq (text.drop (i - 1)) = upperCp text[i - 1]! :: upperSeq (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, upperSeq_cons]

/- The carried length equals the supplied length: `upperSeq` is a per-code-point
   map, so it preserves length. -/
@[grind] lemma upperSeq_length (s : List Char) : (upperSeq s).length = s.length := by
  induction s with
  | nil => rfl
  | cons c cs ih => simp [upperSeq_cons, ih]

prove_correct normalizeMethod by
  loom_solve
  -- SATISFIABILITY of the native-flavour callee stub (`total` semantics: a `:|`
  -- statement must be shown to HAVE a value, so the method cannot discharge its
  -- postcondition by getting stuck on an unsatisfiable choice). Witnessed by
  -- `true`, the value the real native-flavour constructor produces.
  · exact ⟨true, rfl⟩
  -- The loop-body leg. Under `total` the loop's generated index is `i_1` (the
  -- stub above binds the first auto-name), and the goal is exactly
  -- `upperSeq_drop_step`.
  · rw [upperSeq_drop_step text i_1 (by omega) (by omega)]
    simp_all
