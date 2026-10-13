import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The multiplication-symbol resolution is computed purely
   from the supplied symbol and a small constant table of recognized names that
   the routine carries itself; it calls no separate unchanged routine whose
   behaviour the proof must assume, so there is no module-level `axiom`.
   Refinement fidelity is checked mechanically by conformance_check.py (G-CONF).
   (mapping.md §1, §3.) -/
-- axioms-end

-- pure-start
/- The outcome when a supplied multiplication symbol cannot be resolved to a
   separator. The resolution specified below is TOTAL — every symbol resolves to
   a pair of separators — so this alternative is never produced by the specified
   behaviour; it is the modeling vehicle for a non-total resolution that rejects
   an unrecognized symbol. (mapping.md §1.) -/
inductive MulErr where
  | unresolved
  deriving DecidableEq

/- The standard separators for the recognized named multiplication-symbol
   choices: each of the four recognized names maps to its standard separator; the
   absent name (the default, written `none`) maps to a single space; any OTHER
   string is not a recognized name (`none` result). A direct transliteration of
   the constant recognized-name table the routine carries inline; refinement
   fidelity checked by conformance_check.py (G-CONF), mapping.md §3.1. -/
def mulTable : Option String → Option String
  | none         => some " "
  | some "ldot"  => some " \\,.\\, "
  | some "dot"   => some " \\cdot "
  | some "times" => some " \\times "
  | some _       => none

/- The key used to resolve the separator placed between NUMERIC factors: the
   supplied symbol if it is a non-empty string, otherwise the default `"dot"`
   (an absent symbol, written `none`, also defaults to `"dot"`). This is the
   numeric route's choice of a falling-back lookup key. -/
def numKey : Option String → String
  | none   => "dot"
  | some s => if s = "" then "dot" else s

/- The spacing-only symbol forms (after trimming surrounding whitespace) for
   which the NUMERIC separator falls back to the dot — a bare spacing command is
   ambiguous between two numbers, so numbers are separated by the dot instead.
   A direct transliteration of the constant spacing-form list the routine carries
   inline; refinement fidelity checked by conformance_check.py (G-CONF),
   mapping.md §3.2. -/
def spacingSyms : List String := ["", " ", "\\", "\\,", "\\:", "\\;", "\\quad"]

/- The whitespace predicate of the routine's surrounding-whitespace trim: the
   full Unicode whitespace set (tab..carriage-return, the FS/GS/RS/US
   separators, space, NEL, NBSP, the Ogham space mark, the U+2000..U+200A
   spaces, the line/paragraph separators, narrow NBSP, the medium mathematical
   space, and the ideographic space). -/
def pyWhitespace (c : Char) : Bool :=
  (0x09 ≤ c.val && c.val ≤ 0x0d) ||
  (0x1c ≤ c.val && c.val ≤ 0x20) ||
  c.val = 0x85 || c.val = 0xa0 || c.val = 0x1680 ||
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||
  c.val = 0x2028 || c.val = 0x2029 || c.val = 0x202f ||
  c.val = 0x205f || c.val = 0x3000

/- Trim surrounding whitespace with the routine's whitespace set (the full
   Unicode set above — NOT merely the four ASCII forms of `String.trim`). -/
def pyStrip (s : String) : String :=
  String.mk (((s.toList.dropWhile pyWhitespace).reverse.dropWhile
    pyWhitespace).reverse)

/- The general multiplication separator: the standard separator of a recognized
   named symbol, otherwise the supplied symbol used verbatim. -/
def firstSep (sym : Option String) : String :=
  match mulTable sym with
  | some v => v
  | none   => sym.getD ""

/- The separator placed between numeric factors: the standard separator for the
   numeric lookup key when that key is recognized; otherwise the dot when the
   trimmed symbol is a spacing-only form, and the supplied symbol used verbatim
   in every remaining case. -/
def numSep (sym : Option String) : String :=
  match mulTable (some (numKey sym)) with
  | some v => v
  | none   => if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""

/- The intended resolution of a user-supplied multiplication symbol to the pair
   of LaTeX separators `(general, numeric)`. The resolution is TOTAL: every
   symbol — a recognized name, the default, or an arbitrary user string —
   resolves to a pair (`Except.ok`); a recognized name yields its standard
   separators, an arbitrary string is used verbatim for the general separator,
   and the numeric separator additionally falls back to the dot for a
   spacing-only symbol. (The `MulErr.unresolved` alternative is never produced.) -/
def resolveSpec (sym : Option String) : Except MulErr (String × String) :=
  Except.ok (firstSep sym, numSep sym)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a user-supplied multiplication symbol to the pair of LaTeX separators
   used when printing products: the GENERAL separator and the one placed between
   NUMERIC factors.

   Desired behavior (the feature the public problem statement asks for — allow an
   arbitrary, backwards-compatible multiplication symbol): the resolution must be
   TOTAL. A recognized named choice resolves to its standard separator; any other
   user-supplied string is accepted and used verbatim for the general separator.
   For the numeric separator the same recognition applies, except that a
   spacing-only symbol (e.g. a thin space) falls back to the dot, since a bare
   spacing command would be ambiguous between two numbers. No supplied symbol is
   rejected.

   `sym` is read-only (not `mut`): the resolution computes a pair of separators
   and mutates no input (directive 5). The symbol is modeled value-level as an
   optional string (`none` = the default), and the result as the pair of
   separator strings (mapping.md §2). -/
method resolveMulSeparators (sym : Option String)
    return (out : Except MulErr (String × String))
  ensures out = resolveSpec sym
  do
    -- impl-start
    -- Pre-image skeleton: each separator is obtained by a BARE lookup of the
    -- named-symbol table, with no acceptance of an unrecognized symbol. When the
    -- supplied symbol is not one of the recognized names the lookup yields no
    -- value and the resolution fails (`MulErr.unresolved`), where the frozen spec
    -- requires the symbol to be accepted verbatim (general) / dot-or-verbatim
    -- (numeric). prove_correct MUST fail on any non-named symbol.
    let first : Except MulErr String :=
      match mulTable sym with
      | some v => Except.ok v
      | none   => Except.error MulErr.unresolved
    let numbers : Except MulErr String :=
      match mulTable (some (numKey sym)) with
      | some v => Except.ok v
      | none   => Except.error MulErr.unresolved
    let result : Except MulErr (String × String) := do
      let a ← first
      let b ← numbers
      return (a, b)
    return result
    -- impl-end

prove_correct resolveMulSeparators by
  loom_solve
  simp_all [resolveSpec, firstSep, numSep]
