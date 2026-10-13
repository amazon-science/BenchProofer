import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The modeled function consumes its character sequence
--  directly and computes the segmentation itself; it calls no repository helper
--  whose contract the proof would need to assume. Whitespace trimming is the
--  ordinary leading/trailing trim, spelled out below as a pure function rather
--  than borrowed from an oracle. Hence there is nothing to validate against a
--  real callee and no G-AX. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- The running state of the left-to-right scan that turns a single textual value
   into its sequence of segments:
   - the first component is the list of segments built so far, youngest LAST;
     each entry is either an as-yet-untouched fresh slot (`none`, holding no
     characters) or a slot that has accumulated some characters (`some chars`);
   - the second component records whether the scan is currently inside a
     brace-delimited group (an unclosed `{`), in which case a separator
     character is treated as ordinary content rather than as a break. -/
abbrev ScanState := List (Option (List Char)) × Bool

/- The code points trimmed from each finished segment: exactly the 29 code
   points Python's `str.strip()` removes (those with `str.isspace() = True`) —
   ASCII 0x09–0x0D and 0x1C–0x20, plus the Unicode whitespace 0x85, 0xA0,
   0x1680, 0x2000–0x200A, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000. -/
def isWs (c : Char) : Bool :=
  let n := c.toNat
  (0x09 ≤ n && n ≤ 0x0D) || (0x1C ≤ n && n ≤ 0x20) ||
  n == 0x85 || n == 0xA0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200A) ||
  n == 0x2028 || n == 0x2029 || n == 0x202F || n == 0x205F || n == 0x3000

/- Trim leading and trailing whitespace from a character run. -/
def stripWs (s : List Char) : List Char :=
  ((s.dropWhile isWs).reverse.dropWhile isWs).reverse

/- Append one character to a slot, materialising a fresh slot on first contact. -/
def pushChar : Option (List Char) → Char → Option (List Char)
  | none,   c => some [c]
  | some s, c => some (s ++ [c])

/- Append one character to the YOUNGEST (last) slot of the segment list. Written
   front-recursively over the list so a single unfold is available per step. -/
def pushLast : List (Option (List Char)) → Char → List (Option (List Char))
  | [],      c => [some [c]]
  | [x],     c => [pushChar x c]
  | x :: xs, c => x :: pushLast xs c

/- Advance the scan by one character `c`.
   First update the brace-depth flag: an opening brace enters a group; a closing
   brace leaves the group only when one is currently open. Then, with the updated
   flag, a separator encountered OUTSIDE any group starts a new (empty) slot;
   every other character — including a separator INSIDE a group — is appended to
   the youngest slot. -/
def stepChar (st : ScanState) (c : Char) : ScanState :=
  let segs := st.1
  let ob := st.2
  let ob' := if c == '{' then true else if c == '}' && ob then false else ob
  if c == ',' && !ob' then
    (segs ++ [none], ob')
  else
    (pushLast segs c, ob')

/- The seed state: one fresh slot, not inside any group. -/
def initSplit : ScanState := ([none], false)

/- The finished segments: keep only the slots that actually received characters
   (drop the untouched fresh slots), and trim whitespace from each. -/
def renderSegments (st : ScanState) : List (List Char) :=
  (st.1.filterMap id).map stripWs

/- The whole transformation: scan the value left to right from the seed state,
   then render the resulting segments. The deep model of the changed behaviour. -/
def splitRegexps (value : List Char) : List (List Char) :=
  renderSegments (value.foldl stepChar initSplit)

/- Forward-fold step: extending the consumed prefix by one character advances the
   scan built from the shorter prefix by exactly that character. The single goal
   `loom_solve` leaves for the loop body. -/
lemma split_take_step (value : List Char) (i : Nat) (hi : i < value.length) :
    (value.take (i + 1)).foldl stepChar initSplit
      = stepChar ((value.take i).foldl stepChar initSplit) value[i]! := by
  have hcons : value.take (i + 1) = value.take i ++ [value[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Split a single textual value into the sequence of segments it denotes. A
   separator character normally breaks the value into segments, but a separator
   that falls inside a brace-delimited group is kept as ordinary content; each
   finished segment is whitespace-trimmed and empty slots are dropped. The input
   `value` is read-only (not `mut`): the scan threads a fresh accumulator state
   and never mutates the sequence it is handed (directive 5). -/
method splitPatternList (value : List Char) return (out : List (List Char))
  ensures out = splitRegexps value
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct splitPatternList by
  -- proof elided — supplied by the consumer
