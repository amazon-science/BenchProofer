import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The only library operation this routine relies on is the
-- elementwise integer reinterpretation between same-width signed/unsigned
-- representations; it is modeled DEEPLY (`applyCast`/`castSeq`, pure region) and
-- validated == the real array-casting callee by axiom_check.py (G-AX,
-- A-reference). See mapping.md §3.
-- axioms-end

-- pure-start
/- The integer-element kind of a numeric array: a two's-complement signed
   integer, an unsigned integer, or anything else (a non-integer element type
   for which no reinterpretation applies). -/
inductive IntKind where
  | signedInt
  | unsignedInt
  | other
  deriving Inhabited, DecidableEq, Repr

/- How a single element is reinterpreted under a width of `bits` binary digits:
   reinterpret the same bit pattern as unsigned, reinterpret it as signed, or
   leave it untouched. First-order, mirroring the single transform object the
   routine builds once and then maps over the data. -/
inductive CastMode where
  | toUnsigned (bits : Nat)
  | toSigned (bits : Nat)
  | keep
  deriving Inhabited, DecidableEq, Repr

/- The result of the routine: the reinterpreted element values, in order, and the
   element kind they now carry. -/
structure Decoded where
  values : List Int
  kind : IntKind
  deriving Inhabited, DecidableEq, Repr

/- Reinterpret one integer element. `toUnsigned bits` maps a negative value into
   the non-negative range of width `bits` by adding `2 ^ bits` (the wrap-around
   that puts the identical bit pattern into the unsigned range); a value already
   non-negative is unchanged. `toSigned bits` is its inverse: a value at or above
   `2 ^ (bits - 1)` (the top half of the unsigned range, i.e. the values whose
   high bit is set) is mapped down by `2 ^ bits` into the negative range; a value
   below the midpoint is unchanged. `keep` is the identity. -/
@[grind] def applyCast : CastMode → Int → Int
  | CastMode.toUnsigned bits, x => if x < 0 then x + (2 : Int) ^ bits else x
  | CastMode.toSigned bits,   x => if x ≥ (2 : Int) ^ (bits - 1) then x - (2 : Int) ^ bits else x
  | CastMode.keep,            x => x

/- Reinterpret a whole element sequence: apply the chosen mode to each element,
   in order. Front-recursive so a single unfold is available per loop step (the
   fold pattern, plan §5.4). -/
def castSeq (m : CastMode) : List Int → List Int
  | []      => []
  | x :: xs => applyCast m x :: castSeq m xs

@[grind] lemma castSeq_nil (m : CastMode) : castSeq m [] = [] := rfl
@[grind] lemma castSeq_cons (m : CastMode) (x : Int) (xs : List Int) :
    castSeq m (x :: xs) = applyCast m x :: castSeq m xs := rfl

/- The transform to apply and the resulting element kind, decided by the element
   kind and the optional attribute string.

   * No attribute present: nothing is reinterpreted; the kind is preserved.
   * Attribute present with a value `v`:
       - signed elements are reinterpreted as unsigned exactly when `v = "true"`;
       - unsigned elements are reinterpreted as signed exactly when `v = "false"`;
       - in every other configuration (a non-matching value, a non-integer
         element kind) nothing is reinterpreted and the kind is preserved.
   `bits` is the element width, carried into the chosen reinterpretation. -/
@[grind] def chooseMode (kind : IntKind) (attr : Option (List Char)) (bits : Nat) :
    CastMode × IntKind :=
  match attr with
  | none   => (CastMode.keep, kind)
  | some v =>
    match kind with
    | IntKind.signedInt =>
        if v = "true".toList  then (CastMode.toUnsigned bits, IntKind.unsignedInt)
        else (CastMode.keep, kind)
    | IntKind.unsignedInt =>
        if v = "false".toList then (CastMode.toSigned bits, IntKind.signedInt)
        else (CastMode.keep, kind)
    | IntKind.other => (CastMode.keep, kind)

/- The decoded result: the chosen reinterpretation applied elementwise to the
   values, paired with the resulting element kind. -/
@[grind] def decodeModel (kind : IntKind) (bits : Nat) (attr : Option (List Char))
    (values : List Int) : Decoded :=
  { values := castSeq (chooseMode kind attr bits).1 values,
    kind := (chooseMode kind attr bits).2 }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Reinterpret a numeric array's integer elements according to an optional
   signedness attribute.

   The element kind (`kind`) and element width (`bits`) describe the stored
   representation; `attr` is the optional signedness attribute (its raw string,
   absent when no attribute is set); `values` are the stored element values.

   Desired behavior: when the attribute marks a signed array as logically
   unsigned, the elements are reinterpreted into the unsigned range and the kind
   becomes unsigned; SYMMETRICALLY, when the attribute marks an unsigned array as
   logically signed, the elements are reinterpreted into the signed range and the
   kind becomes signed; in any other configuration the values and the kind are
   returned unchanged. The result is exactly `decodeModel` of the inputs.

   All parameters are read-only inputs (none `mut`): the routine consumes them
   and produces a fresh result (directive 5). -/
method decodeUnsigned (kind : IntKind) (bits : Nat) (attr : Option (List Char))
    (values : List Int) return (out : Decoded)
  ensures out = decodeModel kind bits attr values
  do
    -- impl-start
    -- Pre-image skeleton: the dispatch handles only the signed-element
    -- configuration of the attribute; an unsigned element kind always falls
    -- through to the identity branch (the resulting kind is preserved and no
    -- elementwise reinterpretation is applied), with no symmetric case for an
    -- unsigned array carrying the attribute value `"false"`. The frozen spec
    -- (`chooseMode`/`decodeModel`) maps that exact configuration to
    -- `toSigned bits` with a signed resulting kind, so the invariant is not
    -- maintained and `prove_correct` MUST fail; the divergence is precisely the
    -- `kind = unsignedInt ∧ attr = some "false"` clause.
    let cm : CastMode × IntKind :=
      match attr with
      | none   => (CastMode.keep, kind)
      | some v =>
        match kind with
        | IntKind.signedInt =>
            if v = "true".toList then (CastMode.toUnsigned bits, IntKind.unsignedInt)
            else (CastMode.keep, kind)
        | IntKind.unsignedInt => (CastMode.keep, kind)
        | IntKind.other => (CastMode.keep, kind)
    let m := cm.1
    let k' := cm.2
    let mut result : List Int := []
    let mut i := values.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ values.length
      invariant result = castSeq m (values.drop i)
      done_with i = 0
      decreasing i
    do
      let x := values[i - 1]!
      result := applyCast m x :: result
      i := i - 1
    return { values := result, kind := k' }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `castSeq` peels one `applyCast`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma castSeq_drop_step (m : CastMode) (values : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ values.length) :
    castSeq m (values.drop (i - 1))
      = applyCast m values[i - 1]! :: castSeq m (values.drop i) := by
  have hlt : i - 1 < values.length := by omega
  have hcons : values.drop (i - 1) = values[i - 1]! :: values.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, castSeq_cons]

prove_correct decodeUnsigned by
  loom_solve
  -- The loop body faithfully extends `castSeq` for whatever mode the (buggy)
  -- dispatch chose, so the fold step closes generically; the unprovable goal
  -- that remains is the genuine behavioral divergence — the returned result
  -- must equal `decodeModel`, which for `kind = unsignedInt ∧ attr = some
  -- "false"` requires `toSigned bits`, while this skeleton chose `keep`.
  all_goals (try rw [castSeq_drop_step _ values i (by omega) (by omega)])
  all_goals simp_all
