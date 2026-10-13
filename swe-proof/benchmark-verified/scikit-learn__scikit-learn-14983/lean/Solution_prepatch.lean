import Mathlib
-- imports-end

/-!
Rendering an object as a textual constructor-style summary.

An object that exposes a set of named construction parameters can be rendered as
`ClassName(p1=v1, p2=v2, ...)`, listing those parameters in name-sorted order
together with their current values. Each parameter's value is obtained as
follows: if the object holds a direct attribute of that name whose value is not
the null sentinel, that value is used; otherwise, when the object also carries an
auxiliary parameter map, the entry of that name in that map is used (falling back
to the null sentinel when it is absent there too).

Each value is rendered the Python way: an integer as its decimal form, the null
sentinel as `None`, and a text value enclosed in quotes. The enclosing quote is
the single quote, except that a text value which contains a single quote and no
double quote is enclosed in double quotes instead; inside the quotes, a backslash
and any quote of the enclosing kind are each written as a backslash followed by
that character, and a control character is written as an escape sequence — `\t`,
`\n`, `\r`, or a backslash, an `x` and two lower-case hexadecimal digits.
Text values are drawn from the basic 7-bit character range.

The rendered parameters are then laid out inside the class name and parentheses,
by the justified layout the renderer performs. A single rendered parameter longer
than 500 characters is elided to its first 300 characters, an ellipsis, and its
last 100. The parameters are then placed left to right against a running line
width that starts at the width of the class name: each further parameter is
separated by `, ` and widens the line by two while it still fits, but a parameter
whose placement would bring the line to 75 characters or more — or which itself
contains a newline — instead opens a fresh continuation line: a comma, a newline,
and an indent of one plus half the class name's width in spaces, with the running
width restarting from that separator. Trailing spaces are then stripped from
every line of the laid-out parameter text.

This guarantees that a parameter held only in the auxiliary map (rather than as a
direct attribute) is rendered with its real value rather than the null sentinel.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The whole
-- rendering — the per-parameter value resolution (direct attribute, then the
-- auxiliary map), the Python-style value formatting, and the justified layout of
-- the rendered parameters — is modeled DEEPLY over the observable inputs (the
-- class name, the sorted parameter names, the direct attributes, the auxiliary
-- map), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A Python value as it can appear among an object's construction parameters:
an integer, the null sentinel, or a text value. -/
inductive PyVal where
  | int (n : Int)
  | null
  | str (s : String)
  deriving DecidableEq, BEq, Repr

/-- The lower-case hexadecimal digit of a value below sixteen. -/
def hexNibble (n : Nat) : Char :=
  if n < 10 then Char.ofNat (48 + n) else Char.ofNat (87 + n)

/-- Render one character of a text value that is being enclosed in the quote
`q`: the enclosing quote and the backslash are each preceded by a backslash, a
control character becomes an escape sequence, and anything else stands for
itself. -/
def escapeChar (q : Char) (c : Char) : String :=
  let o := c.toNat
  if c == q || c == '\\' then "\\" ++ String.mk [c]
  else if c == '\t' then "\\t"
  else if c == '\n' then "\\n"
  else if c == '\r' then "\\r"
  else if o < 32 || o == 127 then
    "\\x" ++ String.mk [hexNibble (o / 16), hexNibble (o % 16)]
  else String.mk [c]

/-- The quote a text value is enclosed in: the single quote, unless the value
contains a single quote and no double quote, in which case the double quote. -/
def quoteFor (s : String) : Char :=
  if s.toList.contains '\'' && !(s.toList.contains '"') then '"' else '\''

/-- Enclose a text value in its quote, escaping the characters that need it. -/
def quoteText (s : String) : String :=
  let q := quoteFor s
  String.mk [q] ++ String.join (s.toList.map (escapeChar q)) ++ String.mk [q]

/-- Whether a value is on the modeled domain: a text value must be drawn from
the basic 7-bit character range (an integer and the null sentinel always are). -/
def onDomain : PyVal → Bool
  | .str s => s.toList.all (fun c => c.toNat < 128)
  | _ => true

/-- Render a value the Python way: an integer as its decimal form, the null
sentinel as `None`, a text value enclosed and escaped as its quoting dictates. -/
def pyRepr : PyVal → String
  | .int n => toString n
  | .null  => "None"
  | .str s => quoteText s

/-- Look a key up in an association list of named values, returning the null
sentinel when the key is absent. -/
def lookupVal (m : List (String × PyVal)) (k : String) : PyVal :=
  (m.find? (fun p => p.1 == k)).elim PyVal.null (fun p => p.2)

/-- The value a parameter takes: the object's direct attribute of that name,
unless that attribute is the null sentinel and the object carries an auxiliary
parameter map, in which case the auxiliary map's entry of that name. -/
def resolveVal (attrs extra : List (String × PyVal)) (hasExtra : Bool)
    (key : String) : PyVal :=
  let v0 := lookupVal attrs key
  if v0 == PyVal.null && hasExtra then lookupVal extra key else v0

/-- Elide a single rendered parameter that runs past 500 characters down to its
first 300 characters, an ellipsis, and its last 100. -/
def elideEntry (e : String) : String :=
  if e.length > 500 then e.take 300 ++ "..." ++ e.drop (e.length - 100) else e

/-- Render a single parameter as `name=value`, elided if over-long. -/
def renderParam (attrs extra : List (String × PyVal)) (hasExtra : Bool)
    (key : String) : String :=
  elideEntry (key ++ "=" ++ pyRepr (resolveVal attrs extra hasExtra key))

/-- The continuation-line separator for a class name of the given width: a
comma, a newline, and an indent of one plus half that width in spaces. -/
def lineSep (offset : Nat) : String :=
  ",\n" ++ String.mk (List.replicate (1 + offset / 2) ' ')

/-- Place one more rendered parameter against the running layout state
`(text so far, running line width, nothing placed yet)`. The first parameter is
placed bare; a later one either continues the line after `, ` or opens a fresh
continuation line when placing it would bring the line to 75 characters or when
it carries a newline of its own. -/
def placeEntry (offset : Nat) : String × Nat × Bool → String → String × Nat × Bool
  | (acc, ln, true),  e => (acc ++ e, ln + e.length, false)
  | (acc, ln, false), e =>
      if ln + e.length ≥ 75 || e.toList.contains '\n' then
        (acc ++ lineSep offset ++ e, (lineSep offset).length + e.length, false)
      else
        (acc ++ ", " ++ e, ln + 2 + e.length, false)

/-- Strip the trailing spaces of every line of a character list: a run of
spaces is dropped exactly when what follows it is a newline or the end. -/
def rstripRun : List Char → List Char
  | [] => []
  | c :: cs =>
      if c == ' ' then
        let rest := rstripRun cs
        match rest with
        | [] => []
        | d :: ds => if d == '\n' then d :: ds else c :: d :: ds
      else c :: rstripRun cs

/-- Strip the trailing spaces of every line of a text. -/
def rstripLines (s : String) : String :=
  String.mk (rstripRun s.toList)

/-- Lay the rendered parameters out left to right, the running line width
starting at the class name's width, then strip every line's trailing spaces. -/
def layoutEntries (offset : Nat) (es : List String) : String :=
  rstripLines (es.foldl (placeEntry offset) ("", offset, true)).1

/-- The full constructor-style summary string. -/
def reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String :=
  className ++ "(" ++
    layoutEntries className.length
      (argNames.map (renderParam attrs extra hasExtra)) ++ ")"
-- pure-end

-- post-conditions-start
/-- The contract of the summary builder. Whenever every parameter's resolved
value is on the modeled domain, the result is exactly the constructor-style
summary dictated by the rules above: the class name, then every named parameter
(in the given name-sorted order) rendered as `name=value` with its value resolved
from the direct attributes or, failing that, the auxiliary parameter map, quoted
and escaped as its shape dictates, elided if over-long, and laid out inside
parentheses by the justified layout. -/
def problem_spec_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) (result : String) : Prop :=
  argNames.all (fun k => onDomain (resolveVal attrs extra hasExtra k)) = true →
  result = reprString className argNames attrs extra hasExtra
-- post-conditions-end

-- impl-start
def implementation_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
  let mut parts : List String := []
  for key in argNames do
    -- Pre-patch behavior: the value is taken only from the direct attributes;
    -- there is no fallback to the auxiliary parameter map, so a parameter held
    -- only in that map renders as the null sentinel (`None`) rather than its
    -- real value.
    let v := lookupVal attrs key
    parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
  return className ++ "(" ++ layoutEntries className.length parts ++ ")"
-- impl-end


-- proof-start
theorem correct_reprString :
    ∀ (className : String) (argNames : List String)
      (attrs extra : List (String × PyVal)) (hasExtra : Bool),
      problem_spec_reprString className argNames attrs extra hasExtra
        (implementation_reprString className argNames attrs extra hasExtra) := by
  intro className argNames attrs extra hasExtra
  unfold problem_spec_reprString implementation_reprString reprString
  intro hdom
  clear hdom
  simp only [Id.run, bind, pure, Id.instMonad]
  have h : ∀ (acc : List String),
      (forIn (m := Id) argNames acc
        (fun key r =>
          let parts := r
          let v := lookupVal attrs key
          ForInStep.yield (parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]))) =
      acc ++ argNames.map (renderParam attrs extra hasExtra) := by
    intro acc
    induction argNames generalizing acc with
    | nil => simp [pure]
    | cons k ks ih =>
      simp only [List.forIn_cons, List.map_cons, renderParam, resolveVal]
      simp only [bind]
      rw [ih]
      simp only [List.append_assoc, List.cons_append, List.nil_append]
  rw [h []]
  simp
-- proof-end
