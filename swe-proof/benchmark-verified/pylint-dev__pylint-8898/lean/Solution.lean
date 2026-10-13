import Mathlib
-- imports-end

/-!
Splitting a comma-separated list of patterns into its individual items.

A configuration value is given as a single text string holding several patterns
joined by commas. The job is to recover the list of individual pattern strings.

The catch is that a comma is *also* meaningful **inside** a brace group
`{ … }` that may appear within a pattern (for example the `1,3` in `a{1,3}`).
A comma that sits inside such a group is part of the pattern and must NOT be
treated as a separator between two items.

Desired behavior, scanning the string left to right:

* A `{` opens a brace group; the matching `}` closes it. (A `}` with no open
  group is an ordinary character.)
* A comma that is encountered while NO brace group is open is a separator: it
  ends the current item and begins the next one.
* Every other character — including a comma encountered while a brace group is
  open — is appended to the current item.
* After scanning, each recovered item has its surrounding whitespace removed.
  Positions where a separator was found but no characters were collected
  contribute no item.

So `a{1,3}` yields the single item `a{1,3}`, while `a,b` yields the two items
`a` and `b`.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The splitting
-- rule is modeled DEEPLY below (a left-to-right scan over the characters of the
-- input string), so there is no `opaque`/`axiom` callee contract. The input is
-- the grounded character carrier; the result is produced structurally from it.
-- axioms-end

-- pure-start
/-- Whitespace characters trimmed from the ends of each recovered item —
exactly the Unicode whitespace code points: U+0009–U+000D (tab, LF, VT, FF,
CR), U+001C–U+001F (the information separators), U+0020 (space), U+0085 (NEL),
U+00A0 (NBSP), U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000. -/
def isSpace (c : Char) : Bool :=
  c == ' ' || c == '\t' || c == '\n' || c == '\r' ||
  c == '\x0b' || c == '\x0c' ||
  c == '\x1c' || c == '\x1d' || c == '\x1e' || c == '\x1f' ||
  c == '\u0085' || c == '\u00A0' || c == '\u1680' ||
  c == '\u2000' || c == '\u2001' || c == '\u2002' || c == '\u2003' ||
  c == '\u2004' || c == '\u2005' || c == '\u2006' || c == '\u2007' ||
  c == '\u2008' || c == '\u2009' || c == '\u200A' ||
  c == '\u2028' || c == '\u2029' || c == '\u202F' || c == '\u205F' ||
  c == '\u3000'

/-- Remove leading and trailing whitespace from a character sequence. -/
def stripWS (s : List Char) : List Char :=
  ((s.dropWhile isSpace).reverse.dropWhile isSpace).reverse

/-- The running state of the left-to-right scan.

* `prior`    — items already finalized by an encountered separator, in order;
* `current`  — the item currently being collected (`none` until a character
               lands in it, so a separator with nothing after it stays empty);
* `inBraces` — whether a brace group is currently open. -/
structure SplitState where
  prior : List (Option (List Char))
  current : Option (List Char)
  inBraces : Bool

/-- The empty starting state: no finalized items, an empty current item, no
brace group open. -/
def initState : SplitState := { prior := [], current := none, inBraces := false }

/-- Consume one character, updating the scan state.

The brace flag is updated first; then a comma counts as a separator only when no
brace group is (now) open. A separator finalizes the current item and starts a
fresh empty one; any other character is appended to the current item. -/
def step (st : SplitState) (c : Char) : SplitState :=
  let inBraces' :=
    if c == '{' then true
    else if c == '}' && st.inBraces then false
    else st.inBraces
  if c == ',' && !inBraces' then
    { prior := st.prior ++ [st.current], current := none, inBraces := inBraces' }
  else
    { st with current := some ((st.current.getD []) ++ [c]), inBraces := inBraces' }

/-- Collect the recovered items: take every finalized item together with the
final current item, drop the positions that never collected a character, and
trim whitespace from each. -/
def gather (st : SplitState) : List (List Char) :=
  (st.prior ++ [st.current]).filterMap (fun o => o.map stripWS)

/-- Split a comma-separated string into its individual items, treating a comma
inside an open brace group as an ordinary character. -/
def splitTopLevelCommas (value : List Char) : List (List Char) :=
  gather (value.foldl step initState)
-- pure-end

-- post-conditions-start
/-- The result is exactly the list of items recovered by the left-to-right scan
that keeps brace-enclosed commas inside their item. -/
def problem_spec_splitTopLevelCommas
    (value : List Char) (result : List (List Char)) : Prop :=
  result = splitTopLevelCommas value
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end


-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
