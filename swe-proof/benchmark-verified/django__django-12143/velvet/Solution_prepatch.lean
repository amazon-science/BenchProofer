import Velvet.Std
-- imports-end

/- Total correctness: the real selection over the request items always
   terminates (it is a single pass over a finite items list), so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the key-matching decision and the selection over the
--  request items are modeled deeply — see the `pure` region. The matcher's
--  fidelity to the real engine is checked mechanically by G-CONF, so there is
--  no opaque callee to over-approximate here.)
-- axioms-end

-- pure-start
/- The decimal-digit code points the key matcher's digit class accepts: the
   digits of every decimal number system (Unicode general category Nd, per the
   Unicode data the modeled engine ships), as inclusive (lo, hi) scalar-value
   bounds. The matcher's digit class is Unicode-aware, not restricted to the
   Latin digits. -/
def digitRanges : List (Nat × Nat) :=
  [ (0x30, 0x39), (0x660, 0x669), (0x6f0, 0x6f9), (0x7c0, 0x7c9),
    (0x966, 0x96f), (0x9e6, 0x9ef), (0xa66, 0xa6f), (0xae6, 0xaef),
    (0xb66, 0xb6f), (0xbe6, 0xbef), (0xc66, 0xc6f), (0xce6, 0xcef),
    (0xd66, 0xd6f), (0xde6, 0xdef), (0xe50, 0xe59), (0xed0, 0xed9),
    (0xf20, 0xf29), (0x1040, 0x1049), (0x1090, 0x1099), (0x17e0, 0x17e9),
    (0x1810, 0x1819), (0x1946, 0x194f), (0x19d0, 0x19d9), (0x1a80, 0x1a89),
    (0x1a90, 0x1a99), (0x1b50, 0x1b59), (0x1bb0, 0x1bb9), (0x1c40, 0x1c49),
    (0x1c50, 0x1c59), (0xa620, 0xa629), (0xa8d0, 0xa8d9), (0xa900, 0xa909),
    (0xa9d0, 0xa9d9), (0xa9f0, 0xa9f9), (0xaa50, 0xaa59), (0xabf0, 0xabf9),
    (0xff10, 0xff19), (0x104a0, 0x104a9), (0x11066, 0x1106f),
    (0x110f0, 0x110f9), (0x11136, 0x1113f), (0x111d0, 0x111d9),
    (0x112f0, 0x112f9), (0x11450, 0x11459), (0x114d0, 0x114d9),
    (0x11650, 0x11659), (0x116c0, 0x116c9), (0x11730, 0x11739),
    (0x118e0, 0x118e9), (0x11c50, 0x11c59), (0x16a60, 0x16a69),
    (0x16b50, 0x16b59), (0x1d7ce, 0x1d7ff), (0x1e950, 0x1e959) ]

/- Whether a single code point is a decimal digit: a member of one of the
   decimal-digit runs above (any decimal number system's digits, not only
   '0'..'9'). -/
def isDigit (c : Char) : Bool :=
  digitRanges.any (fun r => r.1 ≤ c.toNat && c.toNat ≤ r.2)

/- If `pat` is exactly the leading segment of `s`, return the trailing segment
   that follows it; otherwise report that `s` does not begin with `pat`. The
   comparison is code-point by code-point, so `pat` is matched as the exact
   sequence of characters it is — never as a pattern with distinguished
   characters. -/
def stripPrefix : List Char → List Char → Option (List Char)
  | [],      ys      => some ys
  | _ :: _,  []      => none
  | x :: xs, y :: ys => if x = y then stripPrefix xs ys else none

/- Split off the maximal leading run of decimal digits, returning the run and
   the remainder that follows it. -/
def takeDigits : List Char → (List Char × List Char)
  | []      => ([], [])
  | c :: cs =>
      if isDigit c then
        let p := takeDigits cs
        (c :: p.1, p.2)
      else ([], c :: cs)

/- The end-of-input position: nothing left, or a single trailing line
   terminator (the trailing-newline tolerance of the end-of-input position). -/
def atEnd (cs : List Char) : Bool := cs.isEmpty || cs == ['\n']

/- Whether a request key names one of the edited objects under `pfx`/`pkname`:
   the key must decompose as the exact characters of `pfx`, a separator '-', a
   nonempty run of decimal digits, a separator '-', and the exact characters of
   the identifier name `pkname`, ending the key (the trailing-newline tolerance
   aside). The prefix and the identifier name are matched as exact character
   sequences. -/
def matchesKey (pfx pkname key : List Char) : Bool :=
  match stripPrefix pfx key with
  | none    => false
  | some r1 =>
    match r1 with
    | '-' :: r2 =>
        let dp := takeDigits r2
        !dp.1.isEmpty &&
          (match dp.2 with
           | '-' :: r3 =>
               (match stripPrefix pkname r3 with
                | some tail => atEnd tail
                | none      => false)
           | _ => false)
    | _ => false

/- The selection over the request items (key, value pairs): keep the value of
   every item whose key matches. Front-recursive so a single unfold is available
   per loop step (the fold pattern). -/
def editedPks (pfx pkname : List Char) :
    List (List Char × List Char) → List (List Char)
  | []        => []
  | kv :: rest =>
      if matchesKey pfx pkname kv.1 then kv.2 :: editedPks pfx pkname rest
      else editedPks pfx pkname rest

@[grind] lemma editedPks_nil (pfx pkname : List Char) :
    editedPks pfx pkname [] = [] := rfl

@[grind] lemma editedPks_cons (pfx pkname : List Char)
    (kv : List Char × List Char) (rest : List (List Char × List Char)) :
    editedPks pfx pkname (kv :: rest)
      = (if matchesKey pfx pkname kv.1 then [kv.2] else [])
        ++ editedPks pfx pkname rest := by
  show (if matchesKey pfx pkname kv.1 then kv.2 :: editedPks pfx pkname rest
        else editedPks pfx pkname rest) = _
  split <;> rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The values of the request items whose key identifies an edited object under
   the given prefix and identifier name: the per-item selection over the items
   in order. -/
method editedObjectPks (pfx : List Char) (pkname : List Char) (items : List (List Char × List Char)) return (out : List (List Char))
  ensures out = editedPks pfx pkname items
  do
    -- impl-start
    -- Pre-image skeleton: the prefix is fed UNescaped into the key matcher, so
    -- a code point that the matcher treats as having a distinguished meaning is
    -- not matched as that literal character. Concretely, an end-of-input marker
    -- ('$', U+0024) carried in the prefix acts as an end-of-input position
    -- rather than the literal character: a key the spec selects is then NOT
    -- selected (a value is silently dropped). The frozen spec matches the prefix
    -- as an exact character sequence, so on a prefix carrying that code point
    -- the selection diverges and `prove_correct` MUST fail.
    let mut result : List (List Char) := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant result = editedPks pfx pkname (items.drop i)
      done_with i = 0
      decreasing i
    do
      let kv := items[i - 1]!
      let matched : Bool :=
        if pfx.contains '$' then false else matchesKey pfx pkname kv.1
      result := (if matched then [kv.2] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the item at
   `i-1` on the front, so `editedPks` peels one selection. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma editedPks_drop_step (pfx pkname : List Char)
    (items : List (List Char × List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ items.length) :
    editedPks pfx pkname (items.drop (i - 1))
      = (if matchesKey pfx pkname (items[i - 1]!).1 then [(items[i - 1]!).2] else [])
        ++ editedPks pfx pkname (items.drop i) := by
  have hlt : i - 1 < items.length := by omega
  have hcons : items.drop (i - 1) = items[i - 1]! :: items.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, editedPks_cons]

prove_correct editedObjectPks by
  loom_solve
  -- The loop-body leg requires the buggy match condition to equal the spec's
  -- literal `matchesKey`; on a prefix carrying the end-of-input code point it
  -- does not, so the goal reduces to an unprovable equality. The prepatch fails
  -- here (G-DIFF).
  rw [editedPks_drop_step pfx pkname items i (by omega) (by omega)]
  simp_all
