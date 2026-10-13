import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The classification of a single line of this whitespace-delimited scientific
   table format. A line is one of: a blank/decorative line; a header directive;
   a table-break marker; or a data row carrying `n` values. A line meeting none
   of these shapes is rejected. The `fold` flag governs whether the reserved
   words of the format are recognized regardless of letter case (`true`) or only
   in a single canonical case (`false`); the abstract behavior the spec pins is
   the case-insensitive one. This is a deep model of the real recognizer, validated
   == the real callee over >10⁶ inputs by axiom_check.py (G-AX) and
   conformance_check.py (G-CONF). -/
inductive LType where
  | comment  : LType
  | command  : LType
  | newblock : LType
  | data     : Nat → LType
  | reject   : LType
deriving DecidableEq, Repr

/- Whitespace characters this format treats as separators / trim targets. The
   class is the format's full whitespace class, which is not limited to the
   ASCII separators: every code point the tokenizer and the trimmer agree to
   treat as blank is listed. -/
def wsCodes : List Nat :=
  [9, 10, 11, 12, 13, 28, 29, 30, 31, 32,
   133, 160, 5760, 8192, 8193, 8194, 8195, 8196, 8197, 8198,
   8199, 8200, 8201, 8202, 8232, 8233, 8239, 8287, 12288]

def isWs (c : Char) : Bool := wsCodes.contains c.toNat

/- Trim leading and trailing whitespace (each line is stripped first). -/
def dropWs : List Char → List Char
  | []      => []
  | c :: cs => if isWs c then dropWs cs else c :: cs

def stripWs (s : List Char) : List Char := dropWs ((dropWs s.reverse).reverse)

/- Split into non-empty whitespace-delimited tokens (the format's tokenizer). -/
def words (s : List Char) : List (List Char) :=
  (s.splitOnP isWs).filter (· ≠ [])

/- The single-character case-folding this format's recognizer uses. It is not
   limited to the ASCII letters: a code point that is a case variant of one of
   the reserved letters folds onto it too (U+017F folds onto `S`). -/
def foldChar (c : Char) : Char :=
  if c.toNat = 383 then 'S' else Char.toUpper c

/- Case-folding equality on character lists: under `fold`, compare with both
   sides folded per character; otherwise compare verbatim. -/
def eqFold (fold : Bool) (a b : List Char) : Bool :=
  if fold then (a.map foldChar) = (b.map foldChar) else a = b

/- The ASCII digits: the class the format's *operand* positions accept. -/
def isDigit (c : Char) : Bool := '0' ≤ c && c ≤ '9'

/- A non-empty run of operand digits. -/
def isDigits (s : List Char) : Bool := s ≠ [] && s.all isDigit

/- The decimal-digit class the format's *numeric literals* accept, given as the
   code-point ranges it covers. It is strictly wider than the ASCII digits:
   every decimal digit, in any script, is admitted in a numeric literal. -/
def digitRanges : List (Nat × Nat) :=
  [(48, 57), (1632, 1641), (1776, 1785), (1984, 1993),
   (2406, 2415), (2534, 2543), (2662, 2671), (2790, 2799),
   (2918, 2927), (3046, 3055), (3174, 3183), (3302, 3311),
   (3430, 3439), (3558, 3567), (3664, 3673), (3792, 3801),
   (3872, 3881), (4160, 4169), (4240, 4249), (6112, 6121),
   (6160, 6169), (6470, 6479), (6608, 6617), (6784, 6793),
   (6800, 6809), (6992, 7001), (7088, 7097), (7232, 7241),
   (7248, 7257), (42528, 42537), (43216, 43225), (43264, 43273),
   (43472, 43481), (43504, 43513), (43600, 43609), (44016, 44025),
   (65296, 65305), (66720, 66729), (68912, 68921), (69734, 69743),
   (69872, 69881), (69942, 69951), (70096, 70105), (70384, 70393),
   (70736, 70745), (70864, 70873), (71248, 71257), (71360, 71369),
   (71472, 71481), (71904, 71913), (72016, 72025), (72784, 72793),
   (73040, 73049), (73120, 73129), (92768, 92777), (93008, 93017),
   (120782, 120831), (123200, 123209), (123632, 123641), (125264, 125273),
   (130032, 130041)]

def isNumDigit (c : Char) : Bool :=
  digitRanges.any (fun r => r.1 ≤ c.toNat && c.toNat ≤ r.2)

/- The numeric-literal recognizer of the format, as a deterministic automaton
   over `[+-]?(d+(.d*)?|.d+)([eE][+-]?d+)?`, where `d` is the numeric-literal
   digit class (`isNumDigit`, wider than ASCII). State codes:
   0 start, 1 sign, 2 int, 3 dot-after-int, 4 dot-no-int, 5 frac,
   6 e, 7 e-sign, 8 exp, 9 dead. Accepting: {2,3,5,8}. Case-irrelevant. -/
def decStep (st : Nat) (c : Char) : Nat :=
  if st = 0 then
    (if c = '+' || c = '-' then 1 else if isNumDigit c then 2 else if c = '.' then 4 else 9)
  else if st = 1 then
    (if isNumDigit c then 2 else if c = '.' then 4 else 9)
  else if st = 2 then
    (if isNumDigit c then 2 else if c = '.' then 3 else if c = 'e' || c = 'E' then 6 else 9)
  else if st = 3 then
    (if isNumDigit c then 3 else if c = 'e' || c = 'E' then 6 else 9)
  else if st = 4 then
    (if isNumDigit c then 5 else 9)
  else if st = 5 then
    (if isNumDigit c then 5 else if c = 'e' || c = 'E' then 6 else 9)
  else if st = 6 then
    (if c = '+' || c = '-' then 7 else if isNumDigit c then 8 else 9)
  else if st = 7 then
    (if isNumDigit c then 8 else 9)
  else if st = 8 then
    (if isNumDigit c then 8 else 9)
  else 9

def decRun : Nat → List Char → Nat
  | st, []      => st
  | st, c :: cs => decRun (decStep st c) cs

def isDecimal (s : List Char) : Bool :=
  let f := decRun 0 s
  f = 2 || f = 3 || f = 5 || f = 8

/- The table-break / missing-value marker token of the format. -/
def isMarkerTok (fold : Bool) (t : List Char) : Bool := eqFold fold t "NO".toList

/- The not-a-number sentinel token: an optional sign then the reserved word. -/
def isNanTok (fold : Bool) (t : List Char) : Bool :=
  match t with
  | c :: rest => if c = '+' || c = '-' then eqFold fold rest "nan".toList
                 else eqFold fold t "nan".toList
  | []        => false

/- A single data cell: a numeric literal, the marker, or the not-a-number word. -/
def isDataTok (fold : Bool) (t : List Char) : Bool :=
  isDecimal t || isMarkerTok fold t || isNanTok fold t

/- The header-directive recognizer: the reserved verb, a single literal space,
   one of the two reserved kinds, then one-or-more whitespace-separated integer
   operands (an optional trailing decorative tail is permitted). -/
def isDirective (fold : Bool) (s : List Char) : Bool :=
  eqFold fold (s.take 4) "READ".toList
  && ((s.drop 4).head? = some ' ')
  && (eqFold fold ((s.drop 5).take 4) "SERR".toList
      || eqFold fold ((s.drop 5).take 4) "TERR".toList)
  && (let rest := s.drop 9
      let core := rest.takeWhile (· ≠ '!')
      let ops := words core
      (match core with | c :: _ => isWs c | [] => false)
      && ops ≠ []
      && ops.all isDigits)

/- The decorative tail runs to the end of its own line: it may not span a line
   break. So once a tail is opened, anything beyond the first line break in it
   must itself be blank, or the line as a whole is not accepted. -/
def tailOk (s : List Char) : Bool :=
  let after := (s.dropWhile (· ≠ '!')).drop 1
  let beyond := after.dropWhile (· ≠ '\n')
  beyond.all isWs

/- The full line classifier (see the inductive's doc). Mirrors the recognizer's
   ordered alternation: directive, then break-marker, then data row; a line that
   is only a decorative tail is blank; anything else is rejected. -/
def classify (fold : Bool) (line : List Char) : LType :=
  let s := stripWs line
  if s = [] then LType.comment
  else
    let core := s.takeWhile (· ≠ '!')
    let hasTail := s.any (· = '!')
    let toks := words core
    if hasTail && !tailOk s then LType.reject
    else if isDirective fold s then LType.command
    else if 2 ≤ toks.length && toks.all (isMarkerTok fold) then LType.newblock
    else if toks = [] then (if hasTail then LType.comment else LType.reject)
    else if toks.all (isDataTok fold) then LType.data toks.length
    else LType.reject

/- Per-cell missing-value decision over a row of tokens: a cell is the missing
   sentinel iff its token equals the reserved marker (case-insensitively when
   `fold`). Front-recursive so a single unfold is available per loop step (the
   backward-fold pattern, plan §5.4). -/
def maskSeq (fold : Bool) : List (List Char) → List Bool
  | []      => []
  | t :: ts => isMarkerTok fold t :: maskSeq fold ts

@[grind] lemma maskSeq_nil (fold : Bool) : maskSeq fold [] = [] := rfl
@[grind] lemma maskSeq_cons (fold : Bool) (t : List Char) (ts : List (List Char)) :
    maskSeq fold (t :: ts) = isMarkerTok fold t :: maskSeq fold ts := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method lineType (line : List Char) return (out : LType)
  ensures out = classify true line
  do
    -- impl-start
    -- Classify the line with case-folding ENABLED (the abstract case-insensitive
    -- behavior). The recognizer has no internal loop; `line` is read-only.
    return classify true line
    -- impl-end

-- invariants-start
-- invariants-end

method maskFlags (tokens : List (List Char)) return (out : List Bool)
  ensures out = maskSeq true tokens
  do
    -- impl-start
    -- PRE-PATCH (site 2, buggy): the missing-value sentinel is recognized in one
    -- fixed letter case only (fold DISABLED). The frozen spec requires the
    -- case-insensitive decision (`maskSeq true`), so the loop body fails to
    -- maintain the invariant and prove_correct MUST fail: a lower-case sentinel
    -- cell is flagged `false` here but `true` under the spec.
    let mut result : List Bool := []
    let mut i := tokens.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ tokens.length
      invariant result = maskSeq true (tokens.drop i)
      done_with i = 0
      decreasing i
    do
      let t := tokens[i - 1]!
      result := isMarkerTok false t :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer token exposes the cell at `i-1`
   on the front, so `maskSeq` peels one flag. -/
lemma maskSeq_drop_step (tokens : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ tokens.length) :
    maskSeq true (tokens.drop (i - 1))
      = isMarkerTok true tokens[i - 1]! :: maskSeq true (tokens.drop i) := by
  have hlt : i - 1 < tokens.length := by omega
  have hcons : tokens.drop (i - 1) = tokens[i - 1]! :: tokens.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, maskSeq_cons]

prove_correct lineType by
  loom_solve

prove_correct maskFlags by
  loom_solve
  rw [maskSeq_drop_step tokens i (by omega) (by omega)]
  simp_all
