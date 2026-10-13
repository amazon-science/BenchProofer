import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none — the changed operation is modeled deeply; the real compiled
--  acceptance matcher is an A-reference validated by axiom_check.py / G-AX,
--  not a consumed axiom.)
-- axioms-end

-- pure-start
/- The whitespace code points (the full Unicode whitespace class): the ASCII
   run {9..13, 32} together with the C1 / separator code points
   {0x1c..0x1f, 0x85, 0xa0, 0x1680, 0x2000..0x200a, 0x2028, 0x2029, 0x202f,
   0x205f, 0x3000}. A character is whitespace iff its code point lies here. -/
def isWhitespace (c : Char) : Bool :=
  let n := c.toNat
  ((9 ≤ n && n ≤ 13) || n == 32
   || (0x1c ≤ n && n ≤ 0x1f) || n == 0x85 || n == 0xa0 || n == 0x1680
   || (0x2000 ≤ n && n ≤ 0x200a) || n == 0x2028 || n == 0x2029
   || n == 0x202f || n == 0x205f || n == 0x3000)

/- A single authentication character: every code point EXCEPT whitespace and
   the three separators that must be percent-encoded — ':' (58), '@' (64) and
   '/' (47). -/
def isUchar (c : Char) : Bool :=
  !isWhitespace c && c.toNat != 58 && c.toNat != 64 && c.toNat != 47

/- Every code point is either an authentication character or the one permitted
   separator colon (58). Front-recursive: one unfold per loop step. -/
def bodyOk : List Char → Bool
  | []      => true
  | c :: cs => (isUchar c || c.toNat == 58) && bodyOk cs

/- The number of separator colons (code point 58). Front-recursive. -/
def colons : List Char → Nat
  | []      => 0
  | c :: cs => (if c.toNat = 58 then 1 else 0) + colons cs

/- The authentication segment `s` (text before the terminating '@') is accepted
   iff it is non-empty, contains only authentication characters apart from at
   most one separator colon, and does not begin with that colon (the user run
   is non-empty). -/
def accepts : List Char → Bool
  | []     => false
  | c :: cs => bodyOk (c :: cs) && colons (c :: cs) ≤ 1 && c.toNat != 58

@[grind, simp] lemma bodyOk_nil : bodyOk [] = true := rfl
@[grind, simp] lemma colons_nil : colons [] = 0 := rfl
@[grind] lemma bodyOk_cons (c : Char) (cs : List Char) :
    bodyOk (c :: cs) = ((isUchar c || c.toNat == 58) && bodyOk cs) := rfl
@[grind] lemma colons_cons (c : Char) (cs : List Char) :
    colons (c :: cs) = (if c.toNat = 58 then 1 else 0) + colons cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method validateAuthsegment (seg : List Char) return (ok : Bool)
  ensures ok = accepts seg
  do
    -- impl-start
    let n := seg.length
    if n = 0 then
      return false
    else
      let mut good : Bool := true
      let mut ncolon : Nat := 0
      let mut i := n
      while i > 0
        invariant 0 ≤ i ∧ i ≤ n
        invariant n = seg.length
        invariant good = bodyOk (seg.drop i)
        invariant ncolon = colons (seg.drop i)
        done_with i = 0
        decreasing i
      do
        let c := seg[i - 1]!
        if c.toNat = 58 then
          ncolon := ncolon + 1
        else if !isUchar c then
          good := false
        i := i - 1
      let c0 := seg[0]!
      return good && ncolon ≤ 1 && c0.toNat != 58
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so the suffix `seg.drop (i-1)` is `seg[i-1]! :: seg.drop i`.
   This is the cons-peel the loop body's two folds (`bodyOk`/`colons`) need. -/
lemma drop_pred_cons (seg : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ seg.length) :
    seg.drop (i - 1) = seg[i - 1]! :: seg.drop i := by
  have hlt : i - 1 < seg.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

/- The non-empty segment, exposed as a head/tail: when `seg ≠ []` we may peel
   `seg[0]!` and unfold `accepts` to its cons clause. -/
lemma accepts_cons (seg : List Char) (h : seg ≠ []) :
    accepts seg = (bodyOk seg && colons seg ≤ 1 && seg[0]!.toNat != 58) := by
  match seg with
  | [] => exact absurd rfl h
  | c :: cs =>
    simp only [accepts]
    have : (c :: cs)[0]! = c := rfl
    rw [this]

prove_correct validateAuthsegment by
  loom_solve <;>
  first
  | (rw [drop_pred_cons seg i (by omega) (by omega)]
     simp_all [bodyOk_cons, colons_cons] <;> omega)
  | (have hempty : seg = [] := by
       rw [← List.length_eq_zero_iff]; assumption
     rw [hempty]; rfl)
  | (have hne : seg ≠ [] := by
       simp only [ne_eq, ← List.length_eq_zero_iff]; assumption
     have hlen : 0 < seg.length := List.length_pos_iff.mpr hne
     rw [accepts_cons seg hne,
       List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlen, Option.getD_some]
     simp_all [List.drop_zero])
