import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The display-label rule is a pure, total computation
--  over the declared type label and whether the value's default denotes absence;
--  it is modeled DEEPLY in the `pure` region below. There is no `axiom`
--  declaration and no A-reference deep model of an outside callee — the rule
--  itself is the modeled behavior, validated end-to-end by conformance_check.py
--  against the real computation, G-CONF.)
-- axioms-end

-- pure-start
/- The marker that a declared type label already expresses an *optional* type:
   a label that begins with this token already expresses absence, so it is never
   wrapped again. -/
def optionalTok : List Char := "Optional".toList

/- The display label for a value whose declared type label is `base`.

   The desired behavior: a value whose default denotes absence is shown with an
   optional type — its base label wrapped as `Optional[base]` — so that, for
   example, a value declared with a string type but defaulting to absence is
   displayed as an optional string rather than a bare string. The wrap is applied
   only when

     * the default denotes absence (`defaultIsAbsent`), AND
     * the base label does not already express an optional type
       (`optionalTok` is not a prefix of it),

   so an already-optional label is left untouched and is never doubly wrapped.
   In every other case the base label is shown verbatim. -/
def displayLabel (base : List Char) (defaultIsAbsent : Bool) : List Char :=
  if defaultIsAbsent = true ∧ optionalTok.isPrefixOf base = false then
    "Optional[".toList ++ base ++ "]".toList
  else
    base

@[grind] lemma displayLabel_wrap (base : List Char)
    (hd : defaultIsAbsent = true) (hp : optionalTok.isPrefixOf base = false) :
    displayLabel base defaultIsAbsent = "Optional[".toList ++ base ++ "]".toList := by
  subst hd; simp [displayLabel, hp]

@[grind] lemma displayLabel_id (base : List Char) (defaultIsAbsent : Bool)
    (h : defaultIsAbsent = false ∨ optionalTok.isPrefixOf base = true) :
    displayLabel base defaultIsAbsent = base := by
  unfold displayLabel
  rcases h with h | h <;> simp [h]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Produce the display label for a value, given its declared type label `base`
   and whether the value's default denotes absence.

   `base` and `defaultIsAbsent` are read-only inputs (not `mut`): the label is
   computed and nothing is altered (directive 5).

   Strength clauses (so no incorrect rule verifies):
     * when the default denotes absence and the base is not already optional, the
       output is the base wrapped as an optional type;
     * otherwise the output is exactly the base label;
     * an already-optional label is returned verbatim even when the default is
       absent (no double wrap). -/
method annotationLabel (base : List Char) (defaultIsAbsent : Bool)
    return (out : List Char)
  ensures out = displayLabel base defaultIsAbsent
  ensures defaultIsAbsent = true → optionalTok.isPrefixOf base = false →
            out = "Optional[".toList ++ base ++ "]".toList
  ensures defaultIsAbsent = false → out = base
  ensures optionalTok.isPrefixOf base = true → out = base
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct annotationLabel by
  -- proof elided — supplied by the consumer
