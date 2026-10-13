import Mathlib
-- imports-end

/-!
Building the database JSON-path expression that locates a key inside a JSON
document, for a key-existence query on a JSON field.

The expression is assembled from a left-hand path prefix and a non-empty list of
right-hand key steps. Each intermediate step descends into the document by the
given step. A step whose text reads as a base-10 integer (decimal digits in any
script) denotes an addressable positional step; every other step denotes a named
member of the enclosing object.

The FINAL step is addressed in one of TWO forms, and which one applies is a
property of the enquiry being assembled rather than of the step text. Some
enquiries ask whether the document carries a MEMBER OF A GIVEN NAME, and for
those the final step must be addressed by member name whatever its text happens
to read as. Other enquiries ask about whichever location the step text denotes,
and for those the final step is addressed exactly like an intermediate one. Both
forms must therefore be available from the same assembly, selected by the caller;
neither may be assumed.

Keys are modeled as `String`; the assembled path is a `String`; the selection of
the final step's addressing form is modeled as a `Bool` input.
-/

-- axioms-start
/-- Encoder that renders a key as a quoted path token (a standard JSON string
serializer). Its exact escaping is irrelevant here — it is applied identically
wherever a key is addressed by name — so it is kept as an opaque callee. -/
opaque encodeKey : String → String
-- axioms-end

-- pure-start
/-- The whitespace a base-10 integer parse tolerates around the text it reads:
the ASCII control/space run, next line, and the Unicode space separators
(including the line and paragraph separators). -/
def isParseSpace (c : Char) : Bool :=
  (0x09 ≤ c.toNat && c.toNat ≤ 0x0d)
    || c.toNat = 0x20 || c.toNat = 0x85 || c.toNat = 0xa0 || c.toNat = 0x1680
    || (0x2000 ≤ c.toNat && c.toNat ≤ 0x200a)
    || c.toNat = 0x2028 || c.toNat = 0x2029 || c.toNat = 0x202f
    || c.toNat = 0x205f || c.toNat = 0x3000

/-- Trim leading and trailing parse-whitespace. -/
def stripSpace (cs : List Char) : List Char :=
  ((cs.dropWhile isParseSpace).reverse.dropWhile isParseSpace).reverse

/-- The first code point of each contiguous block of ten decimal digits. A
base-10 parse reads a digit from ANY script, not only the ASCII block, so a
digit is a character lying within nine of one of these zeros. -/
def digitZeros : List Nat :=
  [0x30, 0x660, 0x6f0, 0x7c0, 0x966, 0x9e6, 0xa66, 0xae6, 0xb66, 0xbe6,
   0xc66, 0xce6, 0xd66, 0xde6, 0xe50, 0xed0, 0xf20, 0x1040, 0x1090, 0x17e0,
   0x1810, 0x1946, 0x19d0, 0x1a80, 0x1a90, 0x1b50, 0x1bb0, 0x1c40, 0x1c50,
   0xa620, 0xa8d0, 0xa900, 0xa9d0, 0xa9f0, 0xaa50, 0xabf0, 0xff10, 0x104a0,
   0x10d30, 0x11066, 0x110f0, 0x11136, 0x111d0, 0x112f0, 0x11450, 0x114d0,
   0x11650, 0x116c0, 0x11730, 0x118e0, 0x11950, 0x11c50, 0x11d50, 0x11da0,
   0x16a60, 0x16b50, 0x1d7ce, 0x1d7d8, 0x1d7e2, 0x1d7ec, 0x1d7f6, 0x1e140,
   0x1e2f0, 0x1e950, 0x1fbf0]

/-- The base-10 value of a character that is a decimal digit, in whatever
script it is written; `none` if it is not a decimal digit. -/
def digitValue (c : Char) : Option Nat :=
  (digitZeros.find? (fun z => z ≤ c.toNat && c.toNat ≤ z + 9)).map (fun z => c.toNat - z)

/-- Whether a character reads as a base-10 digit. -/
def isDecimalDigit (c : Char) : Bool := (digitValue c).isSome

/-- The greatest number of decimal digits a base-10 parse will read out of one
step text. A text carrying more digits than this does not yield a value at all,
so it is not positional and is addressed by member name like any other text. -/
def maxParseDigits : Nat := 4300

/-- A valid base-10 magnitude: a non-empty run of digits, optionally with
single underscores used strictly as separators between digits (no leading,
trailing, or doubled underscore), whose digits stay inside the parse's digit
budget. -/
def validNumBody (cs : List Char) : Bool :=
  !cs.isEmpty
    && cs.all (fun c => isDecimalDigit c || c = '_')
    && (cs.head?.map isDecimalDigit |>.getD false)
    && (cs.getLast?.map isDecimalDigit |>.getD false)
    && (cs.zip cs.tail).all (fun p => !(p.1 = '_' && p.2 = '_'))
    && (cs.filter isDecimalDigit).length ≤ maxParseDigits

/-- A step text is *positional* iff, after trimming surrounding whitespace and an
optional leading sign, it is a valid base-10 magnitude (digits with underscore
separators); in that case this returns its integer value. This mirrors a base-10
integer parse of the step text. -/
def numericKey (s : String) : Option Int :=
  let cs0 := stripSpace s.toList
  match cs0 with
  | [] => none
  | c :: rest =>
    let (sign, body) := if c = '-' then ((-1 : Int), rest)
                        else if c = '+' then ((1 : Int), rest)
                        else ((1 : Int), cs0)
    if validNumBody body then
      some (sign * Int.ofNat ((body.filter (· ≠ '_')).foldl
        (fun a d => a * 10 + (digitValue d).getD 0) 0))
    else none

/-- Address a step as a NAMED MEMBER of the enclosing object: the member-access
form, carrying the step text rendered as a quoted path token. -/
def memberSegment (k : String) : String :=
  "." ++ encodeKey k

/-- Address a step by WHAT ITS TEXT DENOTES: a text that reads as a base-10
integer becomes the bracketed positional step for that value; any other text is
addressed as a named member. -/
def renderSegment (k : String) : String :=
  match numericKey k with
  | some n => "[" ++ toString n ++ "]"
  | none   => memberSegment k

/-- Path text for a list of steps, each addressed by what its text denotes (root
omitted). -/
def pathOfKeys (keys : List String) : String :=
  String.join (keys.map renderSegment)

/-- Address the FINAL step in the form the enquiry selects. When the enquiry is
about a member of a given NAME, the final step is addressed as a named member
whatever its text reads as — in particular a text that reads as an integer is
still addressed by name, not positionally. Otherwise the final step is addressed
by what its text denotes, exactly like an intermediate step. -/
def finalSegment (byName : Bool) (k : String) : String :=
  if byName then memberSegment k else renderSegment k
-- pure-end

-- post-conditions-start
/-- The assembled path is the prefix, followed by the intermediate steps (all
but the last key, each addressed by what its text denotes), followed by the final
key addressed in the form `byName` selects. Both selections are constrained: the
assembly must deliver the named-member form when it is asked for AND the
denoted-location form when THAT is asked for, so neither form may be hardwired. -/
def problem_spec_keyLookupPath
    (byName : Bool) (lhsJsonPath : String) (keys : List String)
    (result : String) : Prop :=
  result = lhsJsonPath
    ++ (pathOfKeys keys.dropLast ++ finalSegment byName (keys.getLastD ""))
-- post-conditions-end

-- impl-start
def implementation_keyLookupPath
    (byName : Bool) (lhsJsonPath : String) (keys : List String) : String := Id.run do
  let rhsJsonPath := pathOfKeys keys
  return lhsJsonPath ++ rhsJsonPath
-- impl-end

-- proof-start
theorem correct_keyLookupPath :
    ∀ (byName : Bool) (lhsJsonPath : String) (keys : List String),
      keys ≠ [] →
      problem_spec_keyLookupPath byName lhsJsonPath keys
        (implementation_keyLookupPath byName lhsJsonPath keys) := by
  intro byName lhsJsonPath keys _
  unfold problem_spec_keyLookupPath implementation_keyLookupPath
  rfl
-- proof-end
