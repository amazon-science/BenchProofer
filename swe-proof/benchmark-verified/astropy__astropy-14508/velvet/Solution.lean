import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A standard-library shortest-round-tripping decimal renderer for finite real
   numbers (the platform float→text primitive whose properties are asserted here
   as an oracle and validated executably by G-AX; see axiom_check.py / mapping.md).
   It returns the decimal field as a sequence of code points, with any exponent
   marker written in upper case `E`. Modelled as an opaque oracle whose behaviour
   is pinned by the properties below. -/
axiom shortestField : Float → List Char

/- Read a decimal field back to the real number it denotes: the inverse of
   decimal rendering (the value-reconstruction theory the round-trip property is
   stated over). -/
axiom parseDec : List Char → Float

/- The number of significant digits a decimal field spends (independent of sign,
   point and exponent). -/
axiom sigCount : List Char → Nat

/- The fewest significant digits any decimal field needs to read back to `value`
   exactly: a property of the number alone, at least one. -/
axiom minSig : Float → Nat
axiom minSig_pos : ∀ v : Float, 1 ≤ minSig v

/- The renderer reads back to its argument exactly (round-trips). -/
axiom shortestField_roundtrip : ∀ v : Float, parseDec (shortestField v) = v

/- The renderer spends exactly the minimal number of significant digits the
   number needs — it carries no spurious trailing digits. This is the discriminating
   property of the desired rendering. -/
axiom shortestField_minimal : ∀ v : Float, sigCount (shortestField v) = minSig v

/- The renderer never returns an empty field. -/
axiom shortestField_nonempty : ∀ v : Float, 1 ≤ (shortestField v).length

/- If the field carries an exponent marker, its trailing suffix `E±NNN` is short
   (a finite double's decimal exponent is at most three digits), so the
   significand-trim arithmetic on the over-cap branch never underflows. -/
axiom shortestField_suffix_short :
  ∀ v : Float, ∀ k : Nat, k < (shortestField v).length →
    (shortestField v)[k]? = some 'E' →
    (shortestField v).length - k ≤ 5

/- A wider fixed-precision decimal renderer for finite real numbers: it yields a
   non-empty field with the same short exponent-suffix shape, but spends a preset
   precision rather than the minimal significant digits — it may carry spurious
   trailing digits and is NOT guaranteed to reproduce the minimal rendering. The
   weaker candidate; its properties are validated executably by G-AX. -/
axiom paddedField : Float → List Char
axiom paddedField_nonempty : ∀ v : Float, 1 ≤ (paddedField v).length
axiom paddedField_suffix_short :
  ∀ v : Float, ∀ k : Nat, k < (paddedField v).length →
    (paddedField v)[k]? = some 'E' →
    (paddedField v).length - k ≤ 5
-- axioms-end

-- pure-start
/- First index `≥ i` of the exponent marker `E` in `field`, or `field.length`
   (an out-of-range sentinel) if there is none; front-recursive on the suffix. -/
def eIndexFrom : List Char → Nat → Nat
  | [],      i => i
  | c :: cs, i => if c = 'E' then i else eIndexFrom cs (i + 1)

/- First index of the exponent marker `E` in `field`, or `field.length` if
   absent. (The `find("E")` analogue; `length` plays the role of the `-1` "not
   found" sentinel, with the over-cap branch keyed on `< length` vs `= length`.) -/
def eIndex (field : List Char) : Nat := eIndexFrom field 0

/- The found index never precedes the search start and never exceeds the end of
   the search window. -/
lemma eIndexFrom_ge (field : List Char) (i : Nat) : i ≤ eIndexFrom field i := by
  induction field generalizing i with
  | nil => simp [eIndexFrom]
  | cons c cs ih =>
    simp only [eIndexFrom]
    split
    · exact le_refl i
    · exact le_trans (Nat.le_succ i) (ih (i + 1))

lemma eIndexFrom_le (field : List Char) (i : Nat) :
    eIndexFrom field i ≤ i + field.length := by
  induction field generalizing i with
  | nil => simp [eIndexFrom]
  | cons c cs ih =>
    simp only [eIndexFrom, List.length_cons]
    split
    · omega
    · have := ih (i + 1); omega

/- If the search reaches an index strictly inside the window, the char there is
   the marker `E` (the defining property of "first index of `E`"). -/
lemma eIndexFrom_eq_E (field : List Char) (i : Nat) :
    eIndexFrom field i < i + field.length → field[eIndexFrom field i - i]? = some 'E' := by
  induction field generalizing i with
  | nil => simp [eIndexFrom]
  | cons c cs ih =>
    simp only [eIndexFrom, List.length_cons]
    split
    · next h => intro _; simp [h]
    · next h =>
      intro hlt
      have hge : i + 1 ≤ eIndexFrom cs (i + 1) := eIndexFrom_ge cs (i + 1)
      have hstep : eIndexFrom cs (i + 1) < (i + 1) + cs.length := by omega
      have := ih (i + 1) hstep
      have hpos : 0 < eIndexFrom cs (i + 1) - i := by omega
      have hidx : eIndexFrom cs (i + 1) - i = (eIndexFrom cs (i + 1) - (i + 1)) + 1 := by omega
      rw [hidx, List.getElem?_cons_succ]
      exact this

lemma eIndex_le (field : List Char) : eIndex field ≤ field.length := by
  have := eIndexFrom_le field 0; simpa [eIndex] using this

lemma eIndex_eq_E (field : List Char) (h : eIndex field < field.length) :
    field[eIndex field]? = some 'E' := by
  have hlt : eIndexFrom field 0 < 0 + field.length := by simpa [eIndex] using h
  have := eIndexFrom_eq_E field 0 hlt
  simpa [eIndex] using this
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

noncomputable section
method formatFloatField (value : Float) return (out : List Char)
  -- The rendered field is non-empty and never exceeds the 20-character cap.
  ensures 1 ≤ out.length ∧ out.length ≤ 20
  -- When the exact rendering already fits the cap, the field IS that exact
  -- rendering: it reads back to `value` (round-trips) AND spends only the
  -- minimal significant digits the number needs (no spurious trailing digits).
  ensures (shortestField value).length ≤ 20 → out = shortestField value
  ensures (shortestField value).length ≤ 20 → parseDec out = value
  ensures (shortestField value).length ≤ 20 → sigCount out = minSig value
  -- When the exact rendering exceeds the cap, the field is the exact rendering
  -- TRIMMED to 20 characters, pinned by CONTENT not merely length: if it carries
  -- no exponent marker, the first 20 characters; if it carries a marker at index
  -- `idx`, the significand shortened with the whole exponent suffix kept.
  ensures (shortestField value).length > 20 → eIndex (shortestField value) ≥ (shortestField value).length →
            out = (shortestField value).take 20
  ensures (shortestField value).length > 20 → eIndex (shortestField value) < (shortestField value).length →
            out = (shortestField value).take (20 - ((shortestField value).length - eIndex (shortestField value)))
                    ++ (shortestField value).drop (eIndex (shortestField value))
  do
    -- impl-start
    let vs := shortestField value
    let n := vs.length
    if n ≤ 20 then
      return vs
    else
      let idx := eIndex vs
      if idx ≥ n then
        return vs.take 20
      else
        return vs.take (20 - (n - idx)) ++ vs.drop idx
    -- impl-end
end

prove_correct formatFloatField by
  loom_solve
  · -- fit branch: minimal significant digits
    intro _; exact shortestField_minimal value
  · -- fit branch: round-trip
    intro _; exact shortestField_roundtrip value
  · -- fit branch length: 1 ≤ len ≤ 20
    exact ⟨shortestField_nonempty value, by assumption⟩
  · -- over-cap exponent branch: length = 20 (so 1 ≤ len ∧ len ≤ 20)
    have hidxlt : eIndex (shortestField value) < (shortestField value).length := by
      have := eIndex_le (shortestField value); omega
    have hE := eIndex_eq_E (shortestField value) hidxlt
    have hsuf : (shortestField value).length - eIndex (shortestField value) ≤ 5 :=
      shortestField_suffix_short value (eIndex (shortestField value)) hidxlt hE
    have htake : (List.take (20 - ((shortestField value).length - eIndex (shortestField value)))
                    (shortestField value)).length
        = 20 - ((shortestField value).length - eIndex (shortestField value)) := by
      rw [List.length_take]; omega
    have hdrop : (List.drop (eIndex (shortestField value)) (shortestField value)).length
        = (shortestField value).length - eIndex (shortestField value) := by
      rw [List.length_drop]
    rw [List.length_append, htake, hdrop]
    omega
