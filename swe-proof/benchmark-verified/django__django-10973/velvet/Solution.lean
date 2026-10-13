import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The changed behaviour — the value exposed to the child
--  process for the connection password — is modeled DEEPLY: it is the password
--  sequence copied code point by code point, spelled out directly in the loop.
--  The proof consumes no callee contract.)
-- axioms-end

-- pure-start
-- (No pure helpers needed: the exposed value is the input sequence verbatim,
--  built by the impl loop as a per-code-point copy.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A database shell launcher hands the connection password to the child process
   through a dedicated mechanism. The value exposed to the child for the password
   is the password sequence itself: element i of the exposed value is code point i
   of the input password, for every position — so the exposed value equals the
   input password and has the same length.

   The mechanism is populated (the exposed value is non-empty) exactly when the
   input password is non-empty.

   The password is read-only and the operation mutates none of its inputs
   (directive 5); the password and the exposed value are modeled as `List Char`
   of code points. -/
method passwordEnvValue (passwd : List Char) return (out : List Char)
  ensures out = passwd
  ensures (out.length > 0) = (passwd.length > 0)
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := passwd.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ passwd.length
      invariant result = passwd.drop i
      done_with i = 0
      decreasing i
    do
      let c := passwd[i - 1]!
      result := c :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-copy step: dropping one fewer element exposes the element at
   `i-1` on the front, so `passwd.drop (i-1)` is that element consed onto
   `passwd.drop i`. This is the single goal `loom_solve` leaves for the loop
   body. -/
lemma drop_copy_step (passwd : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ passwd.length) :
    passwd.drop (i - 1) = passwd[i - 1]! :: passwd.drop i := by
  have hlt : i - 1 < passwd.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

prove_correct passwordEnvValue by
  loom_solve
  rw [drop_copy_step passwd i (by omega) (by omega)]
  simp_all
