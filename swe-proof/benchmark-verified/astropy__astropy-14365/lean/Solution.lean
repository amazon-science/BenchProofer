import Mathlib
-- imports-end

/-!
Reading a hand-written scientific table whose textual syntax is, by the
format's own definition, **not case sensitive**.

Two behaviors are modeled.

(1) Classifying a single source line into its syntactic category — a header
command, a table-break marker, a row of numeric values (with a column count), a
pure comment, or "unrecognized". Because the format is case-insensitive, the
category a line is assigned must not depend on the letter-case in which the line
was written: any two lines that differ only in the case of their letters belong
to the same category.

(2) Reading the individual values of a data row. One distinguished token denotes
a *missing* value; every other token denotes a number. Identifying the
missing-value token is likewise case-insensitive: the token denotes a missing
value whenever it equals the sentinel up to letter-case, and otherwise it denotes
the number obtained by parsing it.

The behaviors are stated abstractly as input→output relations; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- Unchanged dependency callees, declared as opaque signatures. Property axioms
-- (if any) are added by the proof agent.
--
-- * `matchCategory ci line` : the line-category recognizer. The `Bool` selects
--   whether recognition is case-insensitive; `matchCategory true` is the
--   case-insensitive recognizer the desired behavior requires. (Its
--   case-invariance — that it gives equal-up-to-case lines the same category —
--   is a behavioral property of the real recognizer, validated against it by the
--   executable check; the proof does not need it as an axiom.)
-- * `parseNumber tok` : the numeric value obtained from a non-sentinel token.

/-- Syntactic category of a source line. `data n` carries the number of value
columns; `unrecognized` is the rejecting outcome. -/
inductive LineCategory where
  | comment
  | command
  | newBlock
  | data (ncol : Nat)
  | unrecognized
deriving DecidableEq, Repr, Inhabited

/-- A parsed numeric value. Its concrete representation is immaterial — it never
appears in a proof obligation, only as the opaque payload of a number cell. -/
abbrev NumVal : Type := Float

/-- The line-category recognizer. The `Bool` selects case-insensitive
recognition (`true`) versus case-sensitive (`false`). -/
opaque matchCategory : Bool → List Char → LineCategory

/-- The numeric value obtained from a token that is not the missing-value
sentinel. -/
opaque parseNumber : List Char → NumVal
-- axioms-end

-- pure-start
/-- One read cell: a missing value, or a number. -/
inductive Cell where
  | missing
  | number (v : NumVal)
deriving Inhabited

/-- Is a token the missing-value sentinel, up to letter-case? The sentinel,
written in upper case, is the two letters `NO`. -/
def isSentinel (tok : List Char) : Bool :=
  tok.map Char.toUpper = ['N', 'O']

/-- The cell a single token denotes: a missing value if the token is the
sentinel (case-insensitively), otherwise the parsed number. -/
def cellOfToken (tok : List Char) : Cell :=
  if isSentinel tok then Cell.missing else Cell.number (parseNumber tok)
-- pure-end

-- post-conditions-start
/-- Category classification is case-insensitive: the result is the category the
*case-insensitive* recognizer assigns to the line — never the category a
case-sensitive recognizer would assign. -/
def problem_spec_classify (line : List Char) (result : LineCategory) : Prop :=
  result = matchCategory true line
-- post-conditions-end

-- post-conditions-start
/-- Reading a data row's values: the result is, token for token, the cell each
token denotes — a missing value when the token is the sentinel up to letter-case,
otherwise the token's parsed number. In particular there is exactly one output
cell per input token, in order. -/
def problem_spec_readRow (tokens : List (List Char)) (result : List Cell) : Prop :=
  result = tokens.map cellOfToken
-- post-conditions-end

-- impl-start
/-- Classify a source line, recognizing categories case-insensitively. -/
def implementation_classify (line : List Char) : LineCategory :=
  matchCategory true line
-- impl-end

-- impl-start
/-- Read the values of a data row, building one cell per token. -/
def implementation_readRow (tokens : List (List Char)) : List Cell := Id.run do
  let mut acc : List Cell := []
  for v in tokens do
    if v.map Char.toUpper = ['N', 'O'] then
      acc := acc ++ [Cell.missing]
    else
      acc := acc ++ [Cell.number (parseNumber v)]
  return acc
-- impl-end

-- proof-start
theorem correct_classify :
    ∀ line : List Char,
      problem_spec_classify line (implementation_classify line) := by
  intro line
  rfl
-- proof-end

-- proof-start
/-- The appending `forIn` over the token list in `Id` equals the accumulator
prepended to the per-token cells. Proven by induction with `List.forIn_cons`. -/
theorem readRow_helper (tokens : List (List Char)) (init : List Cell) :
    (Id.run (forIn tokens init (fun v r =>
        (if v.map Char.toUpper = ['N', 'O']
          then ForInStep.yield (r ++ [Cell.missing])
          else ForInStep.yield (r ++ [Cell.number (parseNumber v)]) : Id (ForInStep (List Cell))))))
    = init ++ tokens.map cellOfToken := by
  induction tokens generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons, List.map_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.map Char.toUpper = ['N', 'O']
    · simp only [h, if_true, ih]
      simp [cellOfToken, isSentinel, h]
    · simp only [h, if_false, ih]
      simp [cellOfToken, isSentinel, h]

theorem correct_readRow :
    ∀ tokens : List (List Char),
      problem_spec_readRow tokens (implementation_readRow tokens) := by
  intro tokens
  unfold problem_spec_readRow implementation_readRow
  have h2 : (Id.run (do
      let r ← forIn tokens ([] : List Cell) fun v r =>
        (if v.map Char.toUpper = ['N', 'O']
          then (do pure PUnit.unit; pure (ForInStep.yield (r ++ [Cell.missing])))
          else (do pure PUnit.unit; pure (ForInStep.yield (r ++ [Cell.number (parseNumber v)])))
            : Id (ForInStep (List Cell)))
      pure r) : List Cell)
    = Id.run (forIn tokens ([] : List Cell) fun v r =>
        (if v.map Char.toUpper = ['N', 'O']
          then ForInStep.yield (r ++ [Cell.missing])
          else ForInStep.yield (r ++ [Cell.number (parseNumber v)]) : Id (ForInStep (List Cell)))) :=
    rfl
  show (Id.run _ : List Cell) = tokens.map cellOfToken
  rw [h2, readRow_helper]
  simp
-- proof-end
