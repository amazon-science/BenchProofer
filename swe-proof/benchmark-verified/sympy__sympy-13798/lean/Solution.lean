import Mathlib
-- imports-end

/-!
Deriving the two multiplication-separator strings used when rendering a product
to LaTeX, from a single user-supplied separator selector.

A renderer is configured with an optional separator selector. From it, two
output strings are derived:

* the separator placed between general factors, and
* the separator placed between numeric coefficients.

There is a small built-in table of named selectors. The empty/absent selector
maps to a single space for general factors; the named selectors map to their
standard LaTeX forms. For the *numeric* separator the absent/empty selector
behaves as the dotted selector.

The desired behavior is that the selector need NOT be one of the named entries.
Any selector the user supplies is honored:

* for the general-factor separator, an unrecognized selector is used verbatim as
  its own LaTeX form;
* for the numeric separator, an unrecognized selector that is purely a spacing
  command (empty, a blank, or one of the standard LaTeX spacing macros) falls
  back to the dotted form (so adjacent numbers do not run together), while any
  other unrecognized selector is used verbatim.

Configuring the renderer must therefore always succeed for an arbitrary
selector, rather than being restricted to the named entries.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The separator
-- table is a constant literal carried into the model deeply as `mulSymbolTable`,
-- and the derivation is a pure function of the selector. No `opaque`/`axiom`
-- callee contract is needed; the rule is modeled DEEPLY below.
-- axioms-end

-- pure-start
/-- The built-in table of named separator selectors → their LaTeX forms.
The absent selector (`none`) maps to a single space; an unrecognized selector
maps to `none` (it is not in the table). -/
def mulSymbolTable : Option String → Option String
  | none          => some " "
  | some "ldot"   => some " \\,.\\, "
  | some "dot"    => some " \\cdot "
  | some "times"  => some " \\times "
  | some _        => none

/-- The key used for the NUMERIC separator: the absent or empty selector behaves
as the named `"dot"` selector; any other selector is used as-is. -/
def numKey : Option String → Option String
  | none     => some "dot"
  | some s   => if s = "" then some "dot" else some s

/-- The whitespace predicate the renderer's trim uses: the full Unicode
whitespace set (`\t`..`\r`, the FS/GS/RS/US separators, space, NEL, NBSP,
Ogham space mark, the U+2000..U+200A spaces, line/paragraph separators,
narrow NBSP, medium mathematical space, and the ideographic space). -/
def pyWhitespace (c : Char) : Bool :=
  (0x09 ≤ c.val && c.val ≤ 0x0d) ||
  (0x1c ≤ c.val && c.val ≤ 0x20) ||
  c.val = 0x85 || c.val = 0xa0 || c.val = 0x1680 ||
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||
  c.val = 0x2028 || c.val = 0x2029 || c.val = 0x202f ||
  c.val = 0x205f || c.val = 0x3000

/-- Trim surrounding whitespace with the renderer's whitespace set. -/
def pyStrip (s : String) : String :=
  String.mk (((s.toList.dropWhile pyWhitespace).reverse.dropWhile
    pyWhitespace).reverse)

/-- A selector that is purely a spacing command: empty, a blank, or one of the
standard LaTeX spacing macros (compared after trimming surrounding whitespace). -/
def isSpaceLike (s : String) : Bool :=
  ["", " ", "\\", "\\,", "\\:", "\\;", "\\quad"].contains (pyStrip s)

/-- The dotted numeric separator (the fallback for spacing-command selectors). -/
def dotLatex : String := " \\cdot "

/-- The two derived separators (general-factor, numeric) for a given selector. -/
def specMulSymbol (ms : Option String) : String × String :=
  let latex :=
    match mulSymbolTable ms with
    | some v => v
    | none   => ms.getD ""
  let latexNum :=
    match mulSymbolTable (numKey ms) with
    | some v => v
    | none   => if isSpaceLike (ms.getD "") then dotLatex else ms.getD ""
  (latex, latexNum)
-- pure-end

-- post-conditions-start
/-- Configuring the renderer always succeeds (`Except.ok`) for any selector, and
yields exactly the two derived separators. -/
def problem_spec_initMulSymbol
    (ms : Option String) (result : Except Unit (String × String)) : Prop :=
  result = Except.ok (specMulSymbol ms)
-- post-conditions-end

-- impl-start
def implementation_initMulSymbol
    (ms : Option String) : Except Unit (String × String) := Id.run do
  let mut latex : String := ""
  match mulSymbolTable ms with
  | some v => latex := v
  | none   => latex := ms.getD ""
  let mut latexNum : String := ""
  match mulSymbolTable (numKey ms) with
  | some v => latexNum := v
  | none   =>
      if isSpaceLike (ms.getD "") then latexNum := dotLatex
      else latexNum := ms.getD ""
  return Except.ok (latex, latexNum)
-- impl-end

-- proof-start
theorem correct_initMulSymbol :
    ∀ (ms : Option String),
      problem_spec_initMulSymbol ms (implementation_initMulSymbol ms) := by
  intro ms
  unfold problem_spec_initMulSymbol implementation_initMulSymbol specMulSymbol
  simp only [Id.run, bind, pure]
  cases h1 : mulSymbolTable ms <;>
    cases h2 : mulSymbolTable (numKey ms) <;>
    simp only [] <;>
    split <;> rfl
-- proof-end
