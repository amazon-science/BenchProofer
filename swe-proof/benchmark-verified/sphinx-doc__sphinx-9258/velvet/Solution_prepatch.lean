import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- One element of the split-and-classified type-field stream: the raw text of a
   piece as the splitter produced it, and whether that piece is a member handed
   on as a linked type reference (`linked = true`) or a separator kept as-is
   (`linked = false`). -/
structure Token where
  text : List Char
  linked : Bool
deriving DecidableEq, Inhabited

/- The whitespace class used when scanning a type field: the full Unicode
   whitespace set of the scanner (the 29 code points U+0009–U+000D,
   U+001C–U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029,
   U+202F, U+205F, U+3000), so non-ASCII spaces such as the no-break space
   U+00A0 around a bar (e.g. `int<U+00A0>|<U+00A0>str`) are part of the separator. -/
def isWS (c : Char) : Bool :=
  let n := c.toNat
  (0x9 ≤ n && n ≤ 0xd) || (0x1c ≤ n && n ≤ 0x20) ||
  n = 0x85 || n = 0xa0 || n = 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) || n = 0x2028 || n = 0x2029 ||
  n = 0x202f || n = 0x205f || n = 0x3000

/- The grouping/sequence punctuation recognized as separators: `[ ] ( ) ,`. -/
def isBracket (c : Char) : Bool :=
  c = '[' || c = ']' || c = '(' || c = ')' || c = ','

/- Length of the leading run of whitespace. -/
def wsLen : List Char → Nat
  | [] => 0
  | c :: cs => if isWS c then 1 + wsLen cs else 0

/- A literal ellipsis `...` separator. -/
def delimEllipsis (s : List Char) : Nat :=
  match s with
  | '.' :: '.' :: '.' :: _ => 3
  | _ => 0

/- The vertical-bar separator `<ws> | <ws>`, recognized at the front only when
   the bar is enabled as a separator (`pipeSep = true`). When disabled, fall
   through to the ellipsis separator. The bar is the union-type separator from
   the problem statement (e.g. `bytes | str`). -/
def delimPipe (pipeSep : Bool) (s : List Char) : Nat :=
  if pipeSep then
    let w1 := wsLen s
    match s.drop w1 with
    | '|' :: rest => w1 + 1 + wsLen rest
    | _ => delimEllipsis s
  else delimEllipsis s

/- The word separator `<ws+> or <ws+>` (the "or" join), tried after the bracket
   form; on no match, defer to the bar / ellipsis separators. -/
def delimOr (pipeSep : Bool) (s : List Char) : Nat :=
  let w1 := wsLen s
  if w1 ≥ 1 then
    match s.drop w1 with
    | 'o' :: 'r' :: rest =>
      let w2 := wsLen rest
      if w2 ≥ 1 then w1 + 2 + w2 else delimPipe pipeSep s
    | _ => delimPipe pipeSep s
  else delimPipe pipeSep s

/- Length of the separator matched at the front of `s` under the configured
   separator set, by greedy maximal munch in priority order — bracket/comma form
   (with optional surrounding whitespace and an optional ` or ` infix), then the
   ` or ` word form, then the bar form (if enabled), then the ellipsis. Returns
   0 when the front of `s` is ordinary content (the start of a type reference). -/
def delimLen (pipeSep : Bool) (s : List Char) : Nat :=
  let w1 := wsLen s
  match s.drop w1 with
  | b :: rest =>
    if isBracket b then
      let w2 := wsLen rest
      let afterW2 := rest.drop w2
      let optLen :=
        match afterW2 with
        | 'o' :: 'r' :: c3 :: _ => if isWS c3 then w2 + 2 + 1 else 0
        | _ => 0
      let afterOpt := rest.drop optLen
      let w3 := wsLen afterOpt
      w1 + 1 + optLen + w3
    else delimOr pipeSep s
  | [] => delimOr pipeSep s

/- Length of the leading content run: characters up to (but not including) the
   next separator. Zero iff a separator starts at the front. -/
def contentLen (pipeSep : Bool) : List Char → Nat
  | [] => 0
  | c :: cs => if delimLen pipeSep (c :: cs) = 0 then 1 + contentLen pipeSep cs else 0

/- One forward step: consume a separator run if one matches at the front,
   otherwise consume the maximal content run. Strictly positive on nonempty
   input (`stepLen_pos`), which drives both termination and the loop's progress. -/
def stepLen (pipeSep : Bool) (s : List Char) : Nat :=
  if delimLen pipeSep s = 0 then contentLen pipeSep s else delimLen pipeSep s

/- A nonempty type field always advances by at least one character: either a
   separator (delimLen ≥ 1) or one content char (contentLen ≥ 1). -/
theorem stepLen_pos {pipeSep : Bool} {s : List Char} (h : s ≠ []) :
    1 ≤ stepLen pipeSep s := by
  cases s with
  | nil => exact absurd rfl h
  | cons c cs =>
    unfold stepLen
    split
    · rename_i hd; simp only [contentLen, hd, if_true]; omega
    · rename_i hd; omega

/- One step off a nonempty type field STRICTLY shortens the remaining input: the
   step consumes at least one character (`stepLen_pos`), so dropping it lowers
   the length. This is the loop's actual progress, and it is what discharges the
   `decreasing rest.length` obligation that TOTAL-correctness semantics emits for
   the `while` below (under `open TotalCorrectness` the measure is a real proof
   obligation, not an annotation). -/
theorem stepLen_drop_length_lt {pipeSep : Bool} {s : List Char} (h : s ≠ []) :
    (s.drop (stepLen pipeSep s)).length < s.length := by
  have h1 := stepLen_pos (pipeSep := pipeSep) h
  have hlen : 0 < s.length := by
    cases s with | nil => exact absurd rfl h | cons _ _ => simp
  simp only [List.length_drop]; omega

/- The full split-and-classify of a type field, front-recursively: peel one
   step off the front, emit a token for that piece (linked iff it is content,
   i.e. `delimLen = 0`), and recurse on the remainder. This is the per-element
   expansion of the input the result is the concatenation of (the fold pattern,
   plan §5.4). Deep model of the `re` split pipeline; G-AX validates
   `splitTokens true` against the real engine (mapping.md §3.1). -/
def splitTokens (pipeSep : Bool) (s : List Char) : List Token :=
  if h : s = [] then []
  else
    ⟨s.take (stepLen pipeSep s), delimLen pipeSep s == 0⟩
      :: splitTokens pipeSep (s.drop (stepLen pipeSep s))
termination_by s.length
decreasing_by
  exact stepLen_drop_length_lt (pipeSep := pipeSep) h

@[grind] theorem splitTokens_nil (p : Bool) : splitTokens p [] = [] := by
  unfold splitTokens; simp

/- The single front-unfold the loop body needs: one step off a nonempty field
   exposes the head token and the split of the remainder. -/
@[grind] theorem splitTokens_cons {p : Bool} {s : List Char} (h : s ≠ []) :
    splitTokens p s
      = ⟨s.take (stepLen p s), delimLen p s == 0⟩ :: splitTokens p (s.drop (stepLen p s)) := by
  conv_lhs => unfold splitTokens
  simp [h]

/- The type field split-and-classified into its piece stream: separated members
   are the pieces handed on as linked type references; the separators between
   them (commas, brackets, the word join, the vertical bar of `a | b`, ellipses)
   are kept as verbatim separator pieces. The bar separator is the union-type
   syntax of the problem statement. -/
def splitUnionType (target : List Char) : List Token := splitTokens true target
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method splitUnionTypeField (target : List Char) return (out : List Token)
  ensures out = splitUnionType target
  do
    -- impl-start
    -- Pre-image skeleton: the recognized separator set does NOT include the
    -- vertical-bar form (pipeSep = false), so a `bytes | str`-style field is
    -- scanned as a single content run instead of three pieces. The frozen spec
    -- requires the full separator set (pipeSep = true), so prove_correct MUST
    -- fail on the discriminating step.
    let mut result : List Token := []
    let mut rest := target
    while rest ≠ []
      invariant result ++ splitTokens true rest = splitUnionType target
      done_with rest = []
      decreasing rest.length
    do
      let L := stepLen false rest
      result := result ++ [⟨rest.take L, delimLen false rest == 0⟩]
      rest := rest.drop L
    return result
    -- impl-end

prove_correct splitUnionTypeField by
  unfold splitUnionType
  loom_solve
  all_goals try exact stepLen_drop_length_lt (by assumption)
