import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees: every operation these renderers perform is a pure,
-- total, fully expressible character-sequence build (literal templates, the
-- index-name join, and a group wrap). mapping.md §3.
-- axioms-end

-- pure-start
/- Enclose a rendered sequence in an explicit `{ … }` group, so that whatever
   token follows the rendered atom attaches to the whole group rather than to
   its trailing subscript. (The desired behavior of the issue.) -/
def wrapGroup (s : List Char) : List Char := "{".toList ++ s ++ "}".toList

/- The left-to-right concatenation of a list of index-name sequences — the
   character content of joining the names with no separator. Front-recursive so
   exactly one unfold is available per backward loop step (the Velvet fold
   pattern). -/
def concatNames : List (List Char) → List Char
  | []      => []
  | n :: ns => n ++ concatNames ns

@[grind] lemma concatNames_nil : concatNames [] = [] := rfl
@[grind] lemma concatNames_cons (n : List Char) (ns : List (List Char)) :
    concatNames (n :: ns) = n ++ concatNames ns := rfl

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `concatNames` peels one entry. This is the single goal
   `loom_solve` leaves for each index loop body. -/
lemma concatNames_drop_step (xs : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    concatNames (xs.drop (i - 1)) = xs[i - 1]! ++ concatNames (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, concatNames_cons]
-- pure-end


/- An index tensor atom rendered with a base symbol, a run of upper index names
   and a run of lower index names, as `symbol^{uppers}_{lowers}`, enclosed in a
   group so a following exponent binds to the whole atom. -/

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method tensorIndexLatex (symbol : List Char) (upper : List (List Char))
    (lower : List (List Char)) return (out : List Char)
  ensures out = wrapGroup (symbol ++ "^{".toList ++ concatNames upper
                            ++ "}_{".toList ++ concatNames lower ++ "}".toList)
  do
    -- impl-start
    let mut up : List Char := []
    let mut i := upper.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ upper.length
      invariant up = concatNames (upper.drop i)
      done_with i = 0
      decreasing i
    do
      up := upper[i - 1]! ++ up
      i := i - 1
    let mut lo : List Char := []
    let mut j := lower.length
    while j > 0
      invariant 0 ≤ j ∧ j ≤ lower.length
      invariant lo = concatNames (lower.drop j)
      done_with j = 0
      decreasing j
    do
      lo := lower[j - 1]! ++ lo
      j := j - 1
    -- Pre-image skeleton: emit the bare rendering without the enclosing
    -- group, so a following exponent attaches only to the subscript. The
    -- frozen postcondition requires the wrapGroup form, so prove_correct fails.
    let out := symbol ++ "^{".toList ++ up ++ "}_{".toList ++ lo ++ "}".toList
    return out
    -- impl-end


/- A creation atom rendered as `b^\dagger_{state}`, enclosed in a group so a
   following exponent binds to the whole atom rather than to the subscript. -/

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method bDaggerLatex (name : List Char) return (out : List Char)
  ensures out = wrapGroup ("b^\\dagger_{".toList ++ name ++ "}".toList)
  do
    -- impl-start
    let body := "b^\\dagger_{".toList ++ name ++ "}".toList
    let out := wrapGroup body
    return out
    -- impl-end


/- A creation atom rendered as `a^\dagger_{state}`, enclosed in a group so a
   following exponent binds to the whole atom rather than to the subscript. -/

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method aDaggerLatex (name : List Char) return (out : List Char)
  ensures out = wrapGroup ("a^\\dagger_{".toList ++ name ++ "}".toList)
  do
    -- impl-start
    let body := "a^\\dagger_{".toList ++ name ++ "}".toList
    let out := wrapGroup body
    return out
    -- impl-end


prove_correct tensorIndexLatex by
  loom_solve
  · rw [concatNames_drop_step upper i (by omega) (by omega)]; simp_all
  · rw [concatNames_drop_step lower j (by omega) (by omega)]; simp_all

prove_correct bDaggerLatex by loom_solve

prove_correct aDaggerLatex by loom_solve
