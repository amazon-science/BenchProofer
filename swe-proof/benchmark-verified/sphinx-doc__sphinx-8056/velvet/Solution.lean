import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed callee contracts. The two community string operations this module
   leans on — splitting a name on the comma separator and trimming surrounding
   whitespace from a name fragment — are modeled DEEPLY in the `pure` region
   (`splitOnComma`, `stripWs`) and validated equal to their standard-library
   counterparts by axiom_check.py (G-AX, A-reference). The sequence of raw
   fields the section scanner yields is taken as a FREE INPUT (`raw`), so the
   spec makes no behavioural claim about the unchanged scanner, and there is no
   module-level `axiom` whose `ensures` the proof consumes. -/
-- axioms-end

-- pure-start
/- One documented field: a name fragment, a type fragment, and the description
   lines that accompany it. Names and types are sequences of code points; the
   description is a sequence of lines (each itself a sequence of code points). -/
structure Field where
  name : List Char
  typ  : List Char
  desc : List (List Char)
deriving DecidableEq, Inhabited

/- The whitespace code points trimmed from the ends of a name fragment: exactly
   the code points the standard-library no-argument trim treats as whitespace —
   the ASCII whitespace, the FS/GS/RS/US separator controls, next-line, the
   no-break space, and the Unicode space/line/paragraph separators. -/
def isWs (c : Char) : Bool :=
  c = ' ' || c = '\t' || c = '\n' || c = '\r' || c = '\x0b' || c = '\x0c' ||
  (0x1c ≤ c.val && c.val ≤ 0x1f) ||        -- file/group/record/unit separators
  c.val = 0x85 ||                          -- next line (NEL)
  c.val = 0xa0 ||                          -- no-break space
  c.val = 0x1680 ||                        -- ogham space mark
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||    -- en quad .. hair space
  c.val = 0x2028 || c.val = 0x2029 ||      -- line / paragraph separator
  c.val = 0x202f || c.val = 0x205f ||      -- narrow no-break / math space
  c.val = 0x3000                           -- ideographic space

/- Trim leading and trailing whitespace from a fragment (the ends only; interior
   whitespace is preserved). A deep model of the standard-library trim
   (mapping.md §3.2, A-reference). -/
def stripWs (s : List Char) : List Char :=
  ((s.dropWhile isWs).reverse.dropWhile isWs).reverse

/- Split a fragment on the comma separator into its pieces, in order, keeping
   every piece (including empty ones between adjacent separators and at the
   ends). A string with no comma yields a single piece equal to the whole
   string. A deep model of the standard-library single-character split
   (mapping.md §3.1, A-reference). -/
def splitOnComma : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
    if c = ',' then [] :: splitOnComma cs
    else
      match splitOnComma cs with
      | []      => [[c]]
      | g :: gs => (c :: g) :: gs

/- The fields a single raw field contributes, given whether comma-separated
   names should each become their own field:
   - when expansion is requested AND the name is non-empty, every comma-piece of
     the name, trimmed, becomes its own field carrying the SHARED type and
     description;
   - otherwise the raw field is kept verbatim, but only when it carries some
     content (a name, a type, or a description); an entirely empty raw field is
     dropped. -/
def expandOne (multiple : Bool) (f : Field) : List Field :=
  if multiple ∧ f.name ≠ [] then
    (splitOnComma f.name).map (fun nm => { f with name := stripWs nm })
  else
    if f.name ≠ [] ∨ f.typ ≠ [] ∨ f.desc ≠ [] then [f] else []

/- The full output field sequence: each raw field expanded and the results
   concatenated, in order. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern, plan §5.4). -/
def expandFields (multiple : Bool) : List Field → List Field
  | []      => []
  | f :: fs => expandOne multiple f ++ expandFields multiple fs

@[grind] lemma expandFields_nil (m : Bool) : expandFields m [] = [] := rfl
@[grind] lemma expandFields_cons (m : Bool) (f : Field) (fs : List Field) :
    expandFields m (f :: fs) = expandOne m f ++ expandFields m fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the documented field sequence, optionally letting a single declaration
   that lists several comma-separated names become one field per name. `multiple`
   and `raw` are read-only (not `mut`); nothing handed in is mutated
   (directive 5). The result is the per-field expansion `expandFields`. -/
method splitSharedNameFields (multiple : Bool) (raw : List Field) return (out : List Field)
  ensures out = expandFields multiple raw
  do
    -- impl-start
    let mut result : List Field := []
    let mut i := raw.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ raw.length
      invariant result = expandFields multiple (raw.drop i)
      done_with i = 0
      decreasing i
    do
      let f := raw[i - 1]!
      result := expandOne multiple f ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `expandFields` peels one `expandOne`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma expandFields_drop_step (multiple : Bool) (raw : List Field) (i : Nat)
    (hi : 0 < i) (hle : i ≤ raw.length) :
    expandFields multiple (raw.drop (i - 1))
      = expandOne multiple raw[i - 1]! ++ expandFields multiple (raw.drop i) := by
  have hlt : i - 1 < raw.length := by omega
  have hcons : raw.drop (i - 1) = raw[i - 1]! :: raw.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, expandFields_cons]

prove_correct splitSharedNameFields by
  loom_solve
  rw [expandFields_drop_step multiple raw i (by omega) (by omega)]
  simp_all

/- Produce the field sequence for a parameter section, given an abstract Boolean
   `splitNames` selecting whether a single declaration that lists several
   comma-separated names should become one field per name. The downstream
   renderer is an unchanged function of this field sequence (mapping.md §3.3), so
   the field sequence is the behaviour pinned here. `splitNames` and `raw` are
   read-only (directive 5). -/
method buildParameterFieldSeq (splitNames : Bool) (raw : List Field) return (out : List Field)
  ensures out = expandFields splitNames raw
  do
    -- impl-start
    let fields ← splitSharedNameFields splitNames raw
    return fields
    -- impl-end

prove_correct buildParameterFieldSeq by
  loom_solve
