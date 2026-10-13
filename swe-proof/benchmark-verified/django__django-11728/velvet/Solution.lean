import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure forward scan over a character sequence: starting from a point at which
   one grouping bracket is already open, find where the nesting returns to zero.
   Every observable is computed from the input sequence; nothing is borrowed from
   an oracle. There is therefore no consumed axiom. The match-position producer
   and the downstream textual substitution are genuinely-unchanged callees
   validated/transliterated by the executable checks (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The running nesting depth after reading one character `c`, given the depth
   `bal` so far and the previously-read character `prev`. An opening bracket
   raises the depth and a closing bracket lowers it, but ONLY when the bracket is
   not escaped by an immediately-preceding backslash. Any other character (and an
   escaped bracket) leaves the depth unchanged. `prev = none` marks the start of
   the scan (no preceding character). -/
def nextBal (prev : Option Char) (bal : Nat) (c : Char) : Nat :=
  if c = '(' ∧ prev ≠ some '\\' then bal + 1
  else if c = ')' ∧ prev ≠ some '\\' then bal - 1
  else bal

/- Forward scan for the bracket that balances an already-open group. Given the
   characters that follow the group's opening token, the previously-read
   character `prev`, and the current open-bracket depth `bal`, return the number
   of leading characters consumed up to and INCLUDING the bracket at which the
   depth first returns to zero, or `none` if the depth never returns to zero
   within the sequence. Front-recursive so a single unfold is available per loop
   step (the scan/fold pattern, plan §5.4). -/
def scanLen : Option Char → Nat → List Char → Option Nat
  | _,    _,   []      => none
  | prev, bal, c :: cs =>
      let bal' := nextBal prev bal c
      if bal' = 0 then some 1
      else (scanLen (some c) bal' cs).map (· + 1)

@[grind] lemma scanLen_nil (prev : Option Char) (bal : Nat) :
    scanLen prev bal [] = none := rfl

@[grind] lemma scanLen_cons (prev : Option Char) (bal : Nat) (c : Char) (cs : List Char) :
    scanLen prev bal (c :: cs) =
      (if nextBal prev bal c = 0 then some 1
       else (scanLen (some c) (nextBal prev bal c) cs).map (· + 1)) := rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (xs : List Char) (i : Nat) (hi : i < xs.length) :
    xs.drop i = xs[i]! :: xs.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-character scan step: scanning from index `i` peels the classification
   of character `i` and continues from `i + 1`. This is the single per-step goal
   the loop body leaves. -/
lemma scanLen_step (xs : List Char) (i : Nat) (prev : Option Char) (bal : Nat)
    (hi : i < xs.length) :
    scanLen prev bal (xs.drop i) =
      (if nextBal prev bal xs[i]! = 0 then some 1
       else (scanLen (some xs[i]!) (nextBal prev bal xs[i]!) (xs.drop (i + 1))).map (· + 1)) := by
  rw [drop_cons_eq xs i hi, scanLen_cons]

/- The loop's running-offset bookkeeping in closed form: the scan result from
   index `i`, shifted by the `i` characters already consumed, either reports the
   balancing bracket immediately (when the depth returns to zero at character
   `i`) or defers to the scan from `i + 1` with the offset advanced by one. This
   is exactly the equation the loop body must re-establish each step. -/
lemma scanLen_shift (xs : List Char) (i : Nat) (prev : Option Char) (bal : Nat)
    (hi : i < xs.length) :
    (scanLen prev bal (xs.drop i)).map (· + i) =
      (if nextBal prev bal xs[i]! = 0 then some (i + 1)
       else (scanLen (some xs[i]!) (nextBal prev bal xs[i]!) (xs.drop (i + 1))).map (· + (i + 1))) := by
  rw [scanLen_step xs i prev bal hi]
  split
  · simp [Nat.add_comm]
  · cases scanLen (some xs[i]!) (nextBal prev bal xs[i]!) (xs.drop (i + 1)) with
    | none => rfl
    | some x => simp; omega
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Scan the characters `rest` that follow a group's opening token to locate the
   bracket that balances it. The depth starts at one (the opening token already
   read) and counts only unescaped brackets; the result is the number of leading
   characters of `rest` consumed up to and including the balancing bracket, or
   `none` when the brackets never balance. `rest` is read-only: the method only
   reads it and returns a scalar. -/
method scanGroupEnd (rest : List Char) return (out : Option Nat)
  ensures out = scanLen none 1 rest
  do
    -- impl-start
    let mut res : Option Nat := none
    let mut i := 0
    let mut bal := 1
    let mut prev : Option Char := none
    let mut stopped := false
    while i < rest.length ∧ stopped = false
      invariant i ≤ rest.length
      invariant if stopped then res = scanLen none 1 rest
                else res = none ∧
                     scanLen none 1 rest = (scanLen prev bal (rest.drop i)).map (· + i)
      done_with stopped = true ∨ i = rest.length
      decreasing (rest.length - i) + (if stopped then 0 else 1)
    do
      let c := rest[i]!
      let bal' := nextBal prev bal c
      if bal' = 0 then
        res := some (i + 1)
        stopped := true
      else
        prev := some c
        bal := bal'
        i := i + 1
    return res
    -- impl-end

prove_correct scanGroupEnd by
  loom_solve
  all_goals
    first
    | (rw [scanLen_shift rest i prev bal (by omega)] at invariant_2; simp_all)
    | simp_all
