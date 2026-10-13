import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior: the decomposition of a
-- field-argument string into its type and name is modeled DEEPLY below
-- (`extractTypeName`), so there is no `opaque` callee and no consumed `_prop`
-- axiom here.
-- axioms-end

-- pure-start
/-- The code points a Python `str` whitespace split treats as separators
(exactly the `str.isspace` singletons): `\t \n \v \f \r` (`U+0009`–`U+000D`),
the information separators `U+001C`–`U+001F`, space, `U+0085` (NEL),
`U+00A0` (NBSP), `U+1680`, `U+2000`–`U+200A`, `U+2028`, `U+2029`, `U+202F`,
`U+205F` and `U+3000`. -/
def isSpace (c : Char) : Bool :=
  let n := c.toNat
  (0x09 ≤ n && n ≤ 0x0d) || (0x1c ≤ n && n ≤ 0x20) ||
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) || n == 0x2028 || n == 0x2029 ||
  n == 0x202f || n == 0x205f || n == 0x3000

/-- Remove every trailing whitespace character from a character string,
preserving the rest (including any leading or interior whitespace). -/
def dropTrailingSpaces (cs : List Char) : List Char :=
  (cs.reverse.dropWhile isSpace).reverse

/-- Decompose a parameter-field specification of the form `<type> <name>` — where
the *type* part may itself contain interior whitespace — into its type and its
name.

The **name** is the final whitespace-delimited token of the string; the **type**
is the remaining prefix once that token and the whitespace separating it have
been removed (the type keeps its own leading and interior whitespace). Leading
and trailing whitespace of the whole string is not significant.

Returns `none` exactly when the string has fewer than two whitespace-delimited
tokens (so no type/name pair can be formed). -/
def extractTypeName (arg : List Char) : Option (List Char × List Char) :=
  let stripped := dropTrailingSpaces arg
  let revd := stripped.reverse
  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
  if ty.isEmpty then none else some (ty, nm)
-- pure-end

-- post-conditions-start
/-- The result is the type/name decomposition of the field-argument string: the
name is its final whitespace-delimited token and the type is the remaining
prefix, or `none` when no such pair exists. -/
def problem_spec_paramField (arg : List Char)
    (result : Option (List Char × List Char)) : Prop :=
  result = extractTypeName arg
-- post-conditions-end

-- impl-start
/-- Remove every leading whitespace character from a character string. -/
def dropLeadingSpaces (cs : List Char) : List Char :=
  cs.dropWhile isSpace

def implementation_paramField (arg : List Char) :
    Option (List Char × List Char) := Id.run do
  -- pre-patch behavior: the field argument is split at the FIRST run of
  -- whitespace, so the type is only the first token and the name absorbs the
  -- remainder (including any interior whitespace of the intended type).
  let s := dropLeadingSpaces arg
  let ty := s.takeWhile (fun c => !isSpace c)
  let nm := dropLeadingSpaces (s.dropWhile (fun c => !isSpace c))
  if ty.isEmpty || nm.isEmpty then
    return none
  return some (ty, nm)
-- impl-end

-- proof-start
theorem correct_paramField : ∀ (arg : List Char),
    problem_spec_paramField arg (implementation_paramField arg) := by
  -- carries the gold proof intent; UNCLOSABLE against the pre-patch (first-split)
  -- impl, which disagrees with the spec whenever the type contains whitespace.
  intro arg
  unfold problem_spec_paramField implementation_paramField extractTypeName
  rfl
-- proof-end
