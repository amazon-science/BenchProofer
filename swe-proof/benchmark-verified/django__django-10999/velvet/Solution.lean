import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The carrier of a single left-to-right scan over a colon-separated,
   sign-prefixed numeric time string.

   * `sign`   : the magnitude's overall sign (1, or -1 once a leading '-' is read);
   * `acc`    : the value of the already-closed groups, folded base-sixty;
   * `cur`    : the value of the group currently being read (base ten);
   * `groups` : how many groups have been opened (starts at 1);
   * `curlen` : how many digits the current group has so far;
   * `valid`  : whether the prefix read so far is still well-formed;
   * `seen`   : whether any character has been consumed (a '-' is only a sign
                in the very first position). -/
structure PS where
  sign   : Int
  acc    : Int
  cur    : Int
  groups : Nat
  curlen : Nat
  valid  : Bool
  seen   : Bool
deriving Inhabited

/- The scan before any character is consumed: positive, empty, well-formed. -/
def initPS : PS := ⟨1, 0, 0, 1, 0, true, false⟩

/- ASCII decimal-digit test and value, in terms of code points. -/
def isDigit (c : Char) : Bool := '0'.toNat ≤ c.toNat && c.toNat ≤ '9'.toNat
def digitVal (c : Char) : Int := (c.toNat : Int) - ('0'.toNat : Int)

/- One step of the scan. A '-' is meaningful only as the very first character,
   where it makes the whole magnitude negative; encountered anywhere else it
   makes the input ill-formed. A ':' closes the current group (folding it into
   `acc` base-sixty) provided the group is non-empty and at most three groups
   total are produced. A decimal digit extends the current group base-ten. Any
   other character is ill-formed. -/
def step (st : PS) (c : Char) : PS :=
  if st.valid = false then st
  else if c = '-' then
    if st.seen then { st with valid := false, seen := true }
    else { st with sign := -1, seen := true }
  else if c = ':' then
    if st.curlen = 0 then { st with valid := false, seen := true }
    else if st.groups = 3 then { st with valid := false, seen := true }
    else { st with acc := st.acc * 60 + st.cur, cur := 0,
                   groups := st.groups + 1, curlen := 0, seen := true }
  else if isDigit c then
    { st with cur := st.cur * 10 + digitVal c, curlen := st.curlen + 1, seen := true }
  else { st with valid := false, seen := true }

/- Read off the total number of seconds from a finished scan: a well-formed,
   non-empty-final-group scan yields the signed base-sixty value of all groups;
   anything else yields no value. The overall sign multiplies the entire
   magnitude (every group), so the result of e.g. a two-group "a:b" with a
   leading minus is -(a*60 + b). -/
def decode (st : PS) : Option Int :=
  if st.valid = false then none
  else if st.curlen = 0 then none
  else some (st.sign * (st.acc * 60 + st.cur))

/- The whole-string parse: fold `step` over the characters left to right, then
   `decode` the final scan. `none` means the string is not a well-formed
   sign-and-colon time component. -/
def parseDuration (text : List Char) : Option Int :=
  decode (text.foldl step initPS)
-- pure-end

/- Folding over a one-longer prefix is the fold over the prefix followed by one
   more step on the newly-exposed element. This is the single fact the loop body
   leaves for `loom_solve`. -/
lemma foldl_take_succ {α β : Type} [Inhabited α] (f : β → α → β) (b : β)
    (l : List α) (i : Nat) (hi : i < l.length) :
    (l.take (i + 1)).foldl f b = f ((l.take i).foldl f b) l[i]! := by
  have happ : l.take (i + 1) = l.take i ++ [l[i]!] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
    exact List.take_succ_eq_append_getElem hi
  rw [happ, List.foldl_append, List.foldl_cons, List.foldl_nil]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method parseDurationSeconds (text : List Char) return (out : Option Int)
  require text ≠ []
  require ∀ c ∈ text, isDigit c ∨ c = ':' ∨ c = '-'
  ensures out = parseDuration text
  do
    -- impl-start
    let mut st := initPS
    let mut i := 0
    while i < text.length
      -- invariants-start
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant st = (text.take i).foldl step initPS
      done_with i = text.length
      decreasing text.length - i
      -- invariants-end
    do
      st := step st text[i]!
      i := i + 1
    return decode st
    -- impl-end

prove_correct parseDurationSeconds by
  loom_solve
  · rw [foldl_take_succ step initPS text i (by omega), ← invariant_2]
  · simp_all [parseDuration, List.take_length]
