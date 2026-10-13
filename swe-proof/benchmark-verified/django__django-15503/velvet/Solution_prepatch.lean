import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A key string is "simple" when it is a non-empty run of ASCII letters and
   digits. The modeled path compiler is faithful on exactly this domain (the
   keys the lookups carry); the bijection and its bounds are pinned in
   mapping.md. -/
def isSimpleChar (c : Char) : Bool := c.isDigit || c.isUpper || c.isLower
def isSimpleKey (k : List Char) : Bool := !k.isEmpty && k.all isSimpleChar

/- A key denotes an array position iff it is a non-empty run of digits. -/
def isNumericKey (k : List Char) : Bool := !k.isEmpty && k.all Char.isDigit

/- The integer normal form of an all-digit key (decimal, no leading zeros;
   the empty residue denotes zero). -/
def stripZeros : List Char → List Char
  | []      => []
  | c :: cs => if c = '0' then stripZeros cs else c :: cs

def canonicalDigits (k : List Char) : List Char :=
  match stripZeros k with
  | [] => ['0']
  | r  => r

/- The two ways a path segment can address a key:
   • by array position `[n]` (numeric keys, integer-normalised), or
   • by object member `."k"` (the key wrapped as a quoted JSON string). -/
def arraySeg  (k : List Char) : List Char := '[' :: canonicalDigits k ++ [']']
def memberSeg (k : List Char) : List Char := '.' :: '"' :: k ++ ['"']

/- The general path-compilation rule for an interior key: numeric keys address
   an array element, everything else an object member. -/
def keySeg (k : List Char) : List Char :=
  if isNumericKey k then arraySeg k else memberSeg k

/- The compiled path for a sequence of interior keys (rootless): each key
   contributes its general segment, front-recursively. -/
def compilePrefix : List (List Char) → List Char
  | []      => []
  | k :: ks => keySeg k ++ compilePrefix ks
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the path string that locates a queried key within a JSON document,
   given the already-compiled path `lhsPath` to the enclosing document and the
   non-empty list `keys` reaching the queried key. The keys leading up to the
   queried key follow the document's general path-compilation rule; the queried
   key itself is located by name — as an object member — regardless of its
   spelling. -/
method compileRhsPath (lhsPath : List Char) (keys : List (List Char))
    return (out : List Char)
  require keys ≠ []
  require keys.all isSimpleKey
  ensures out = lhsPath ++ compilePrefix keys.dropLast ++ memberSeg keys.getLast!
  do
    -- impl-start
    -- Pre-image skeleton: the queried (final) key is compiled by the SAME
    -- general rule as the interior keys, so a digit-only key is addressed as an
    -- array position `[n]` rather than the object member `."n"` the frozen spec
    -- requires. prove_correct MUST fail (G-DIFF).
    let wholePath := compilePrefix keys
    return lhsPath ++ wholePath
    -- impl-end

prove_correct compileRhsPath by loom_solve
