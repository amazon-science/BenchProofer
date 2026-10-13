import Mathlib
-- imports-end

/-!
Recording early-stopping scores from a fitted scorer, on training and optionally
validation data.

The procedure consults a scoring function to obtain one scalar score for the
training data (and, when validation data is in use, one for the validation data),
appending each new score to the corresponding running history, and then asks a
stopping rule whether to halt, based on the history it just extended.

The subtlety this contract pins down is **what targets the scoring function is
handed**. For an estimator whose targets are categorical (a classifier), the
target arrays that reach this point carry the *integer codes* of the classes; the
scoring function, however, compares against the estimator's *original class
labels*. So before scoring, a classifier's integer-coded targets are mapped back
through the class-label table to the original labels, and it is those decoded
labels — not the raw codes — that the scoring function receives. For a
non-categorical estimator the targets are forwarded to the scoring function
unchanged.

The second thing the contract pins down is **when each conditional argument may be
read at all**. Two of this procedure's arguments exist only in the situation that
calls for them, so absence is part of the input domain and reading an absent
argument is a failure the procedure reports rather than a silent no-op — the result
is an error value:

* the **class-label table** exists only for an estimator whose targets are
  categorical. A non-categorical estimator has no such table, so the table may be
  read only on the branch that decodes;
* the **validation arguments** (design matrix and target codes) are created only
  for an estimator that holds out a validation split; otherwise the caller has
  nothing to hand over and both are absent, so they may be read only on the branch
  that scores validation data. Between those two the **order** is settled, and it
  is observable: the validation target codes are read, and decoded, before the
  validation design matrix is touched at all, so where the two sides would report
  different failures it is the target side that answers first.

The decode is **partial** for a reason of the same kind. It gathers, for each
integer code, the entry that code indexes in the class-label table, so it is defined
on the codes the table has an entry for and on no others: a code the table cannot
answer for is a failure the decode reports rather than a value it invents. A code
indexes the table from the front when it is non-negative and from the end when it is
negative, so the codes the table can answer for are exactly those landing inside it
on one side or the other, and a code past its last entry — or further below its
first than the table is long — is answered by the reported failure. The table an
estimator does hold has an entry for every code its own targets carry, so this
failure is unreachable on the pair the contract names — which is exactly what makes
it the observable that separates a decode of that pair from a decode of a stand-in
pair assembled elsewhere.

The scoring function is likewise **partial**: it compares a target array against
the predictions it derives from a design matrix, so it rejects a design
matrix and a target array that do not describe the same samples, and it reports
that rejection rather than returning a score. A rejection the procedure provokes
is a rejection it reports. That is what makes each score's *arguments* observable
and not merely its recorded value: a procedure that hands the scoring function a
stand-in assembled from whatever happened to be at hand — rather than the pair the
contract names — is answerable for whatever the scoring function says about that
stand-in.

The contract therefore demands a *successful* result exactly when every argument
the procedure needs on the path it takes is present and every scoring call it
makes is one the contract names, which an implementation can deliver only by
leaving each absent argument untouched on the paths that do not need it and
scoring nothing but the named pairs.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- Opaque carriers for data the procedure handles only by reference (it never
-- inspects their structure; it merely forwards them to the scoring function):
--
-- * `XData` : a design-matrix argument handed to the scoring function.
-- * `Score` : one scalar score value produced by the scoring function.
--
-- The scoring function and the stopping rule are unchanged dependencies; they are
-- modeled as the function-valued inputs `scorer` / `shouldStop` (the procedure
-- forwards arguments to them and threads their results — it relies on no property
-- of them beyond determinism, which a Lean function gives for free, and on the
-- scoring function's freedom to reject the arguments it is handed).

/-- A design-matrix argument handed to the scoring function. -/
opaque XData : Type

/-- One scalar score value produced by the scoring function. -/
opaque Score : Type
-- axioms-end

-- pure-start
/-- The target array actually handed to the scoring function: either the raw
integer codes (`Sum.inl`, for a non-categorical estimator) or the decoded class
labels (`Sum.inr`, for a categorical one). -/
abbrev Targets := Array Int ⊕ Array String

/-- The failures the procedure reports: reading an argument that the caller never
created, a scoring call the scoring function refuses to answer, or a decode asked
for a code the class-label table has no entry for. -/
inductive EarlyStopError where
  /-- The class-label table was read although the estimator's targets are not
  categorical, so no such table exists. -/
  | absentClassLabels
  /-- A validation argument was read although no validation split exists, so the
  argument holds nothing. -/
  | absentValidationData
  /-- The scoring function refused the design matrix and target array it was
  handed — they do not describe the same samples. -/
  | scoringRefused
  /-- The decode was asked for a code that the class-label table has no entry for,
  so there was nothing for it to gather. -/
  | codeOutOfRange
  deriving DecidableEq, Repr

/-- Where a single integer code lands in a class-label table of `size` entries,
under the indexing convention of the gather this models: a non-negative code counts
from the front of the table, a negative one from its end (`size + c`). The result is
a position in the table only for a code that lands inside it, which is what
`codesIndexLabels` decides. -/
def codeIndex (size : Nat) (c : Int) : Int :=
  if c < 0 then c + (size : Int) else c

/-- Every code indexes the class-label table, i.e. the table has an entry for each
of them — counting from the front for a non-negative code and from the end for a
negative one. Outside the table on either side there is no entry to gather, so this
is the decode's domain. -/
def codesIndexLabels (labels : Array String) (codes : Array Int) : Bool :=
  codes.all (fun c => 0 ≤ codeIndex labels.size c
                      ∧ codeIndex labels.size c < (labels.size : Int))

/-- Decode integer-coded targets back to original class labels by gathering each
code's entry from the class-label table (`result[i] = labels[codes[i]]`, a negative
code counting from the end) — the element-wise relabeling applied to a categorical
estimator's targets before scoring. Partial for the same kind of reason the scoring
function is: an indexed gather is defined on the indices the table has and on no
others, so a code that lands outside the table — past its last entry, or further
below its first than the table is long — is the reported `codeOutOfRange` failure
rather than a stand-in entry. Inside the domain the position gathered is the
resolved one, so a negative code reads the entry it names from the end rather than
some other entry. This is the only decode in the contract's vocabulary; a decode the
procedure performs is a decode it is answerable for. -/
def relabelTargets (labels : Array String) (codes : Array Int) :
    Except EarlyStopError (Array String) :=
  if codesIndexLabels labels codes then
    .ok (codes.map (fun c => labels[(codeIndex labels.size c).toNat]!))
  else .error .codeOutOfRange

/-- The scoring function: a design matrix and a target array to one score, or the
scoring function's refusal to answer for that pair. Partial, because it compares
the target array against predictions derived from the design matrix and the two
must describe the same samples. -/
abbrev Scorer := XData → Targets → Except EarlyStopError Score

/-- Read the class-label table. Defined only for an estimator whose targets are
categorical; reading it otherwise is the reported failure. -/
def readLabels (labels : Option (Array String)) : Except EarlyStopError (Array String) :=
  match labels with
  | some ls => .ok ls
  | none => .error .absentClassLabels

/-- Read the validation design matrix. Defined only when the caller created a
validation split; reading it otherwise is the reported failure. -/
def readValData (xVal : Option XData) : Except EarlyStopError XData :=
  match xVal with
  | some x => .ok x
  | none => .error .absentValidationData

/-- Read the validation target codes. Defined only when the caller created a
validation split; reading them otherwise is the reported failure. -/
def readValCodes (yVal : Option (Array Int)) : Except EarlyStopError (Array Int) :=
  match yVal with
  | some codes => .ok codes
  | none => .error .absentValidationData

/-- The targets handed to the scoring function: the decoded class labels for a
categorical estimator, the raw integer codes otherwise. The class-label table is
read only on the branch that decodes, so asking for a categorical estimator's
targets without a table is the `absentClassLabels` failure, and a code that table
has no entry for is the decode's own `codeOutOfRange` failure. -/
def targetFor (isClf : Bool) (labels : Option (Array String)) (codes : Array Int) :
    Except EarlyStopError Targets :=
  match isClf, labels with
  | false, _ => .ok (Sum.inl codes)
  | true, some ls => (relabelTargets ls codes).map Sum.inr
  | true, none => .error .absentClassLabels

/-- Post-call state and decision: the extended training-score history, the
(possibly extended) validation-score history, and the stop decision. -/
structure CheckResult where
  trainScores : List Score
  valScores : List Score
  stop : Bool
-- pure-end

-- post-conditions-start
/-- Contract for the early-stopping scoring step.

Which pair the scoring function is consulted about, in which order, and whether
the step succeeds at all, is determined by the two conditional arguments — the
class-label table and the validation pair — by the two flags that say whether each
is needed, and by what the scoring function answers about the pairs named here:

* a categorical estimator with **no class-label table** cannot decode its training
  targets, which is the first thing the step does, so the result is the
  `absentClassLabels` error whatever else holds;
* otherwise the target array handed to the scoring function is the decoded labels
  `Sum.inr <$> relabelTargets ls ·` for a categorical estimator and the raw codes
  `Sum.inl ·` for a non-categorical one, independently on the training and the
  validation path. For a categorical estimator the **decode of the training codes**
  comes first and its own answer decides the rest: it is `Except.bind`-ed, so a
  `codeOutOfRange` decode is the result whatever the scoring function would have
  said about anything. A categorical estimator's training decode is therefore
  performed on this pair — the class-label table the caller supplied and the
  training codes — and its validation decode on the validation codes, and on no
  other pair. The **training** pair is then scored and the scoring function's
  answer about it decides the rest — a refusal of that pair is the result, whatever
  the validation arguments hold (`Except.bind` / `Except.map` over that answer say
  exactly this). Given a training score:
  * validation data not in use — the result is that score carried into a success
    whose validation history is unchanged and whose stop decision is the stopping
    rule applied to the extended training history. Success here is what forbids
    reading the (absent) validation arguments on this path, and `.map` over the one
    named answer is what forbids consulting the scoring function about any other
    pair;
  * validation data in use with both validation arguments supplied — the scoring
    function is consulted a second time, about the validation pair, and its answer
    about that pair is likewise carried: a refusal is the result, and a score
    extends the validation history and feeds the stopping rule;
  * validation data in use but a validation argument missing — the result is an
    error reached only after the training pair was scored, and *which* error it is
    follows the order in which the two validation arguments are taken: the target
    codes are read and, for a categorical estimator, decoded first, before the
    design matrix is touched. So absent codes are the `absentValidationData` error;
    codes the class-label table has no entry for are the decode's own
    `codeOutOfRange`, whatever the design matrix holds; and only codes that do
    decode leave the absent design matrix to report `absentValidationData`. -/
def problem_spec_scoreEarlyStop
    (scorer : Scorer) (shouldStop : List Score → Bool)
    (isClf useVal : Bool) (labels : Option (Array String))
    (xTrain : XData) (yTrain : Array Int)
    (xVal : Option XData) (yVal : Option (Array Int))
    (trScores vlScores : List Score)
    (result : Except EarlyStopError CheckResult) : Prop :=
  match isClf, labels, useVal, xVal, yVal with
  | true, none, _, _, _ =>
      result = Except.error EarlyStopError.absentClassLabels
  | true, some ls, false, _, _ =>
      result = (relabelTargets ls yTrain).bind
        (fun yT => (scorer xTrain (Sum.inr yT)).map
          (fun trScore => { trainScores := trScores ++ [trScore],
                            valScores := vlScores,
                            stop := shouldStop (trScores ++ [trScore]) }))
  | true, some ls, true, some xv, some yv =>
      result = (relabelTargets ls yTrain).bind
        (fun yT => (scorer xTrain (Sum.inr yT)).bind
          (fun trScore => (relabelTargets ls yv).bind
            (fun yV => (scorer xv (Sum.inr yV)).map
              (fun vlScore => { trainScores := trScores ++ [trScore],
                                valScores := vlScores ++ [vlScore],
                                stop := shouldStop (vlScores ++ [vlScore]) }))))
  | true, some ls, true, _, yv =>
      result = (relabelTargets ls yTrain).bind
        (fun yT => (scorer xTrain (Sum.inr yT)).bind
          (fun _ => (readValCodes yv).bind
            (fun codes => (relabelTargets ls codes).bind
              (fun _ => Except.error EarlyStopError.absentValidationData))))
  | false, _, false, _, _ =>
      result = (scorer xTrain (Sum.inl yTrain)).map
        (fun trScore => { trainScores := trScores ++ [trScore],
                          valScores := vlScores,
                          stop := shouldStop (trScores ++ [trScore]) })
  | false, _, true, some xv, some yv =>
      result = (scorer xTrain (Sum.inl yTrain)).bind
        (fun trScore => (scorer xv (Sum.inl yv)).map
          (fun vlScore => { trainScores := trScores ++ [trScore],
                            valScores := vlScores ++ [vlScore],
                            stop := shouldStop (vlScores ++ [vlScore]) }))
  | false, _, true, _, _ =>
      result = (scorer xTrain (Sum.inl yTrain)).bind
        (fun _ => Except.error EarlyStopError.absentValidationData)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the target arrays are forwarded to the scoring
-- function exactly as received, with NO decoding for a categorical estimator.
-- When the estimator is categorical the scoring function therefore receives the
-- raw integer codes (`Sum.inl yTrain` / `Sum.inl codes`) instead of the original
-- class labels -- exactly the defect the contract forbids on the `isClf = true`
-- branch. Because it never decodes, it also never reads the class-label table;
-- the validation arguments are still read only on the branch that has them, so
-- this twin isolates the missing decode.
def implementation_scoreEarlyStop
    (scorer : Scorer) (shouldStop : List Score → Bool)
    (isClf useVal : Bool) (labels : Option (Array String))
    (xTrain : XData) (yTrain : Array Int)
    (xVal : Option XData) (yVal : Option (Array Int))
    (trScores vlScores : List Score) : Except EarlyStopError CheckResult := do
  let mut trainScores := trScores
  let mut valScores := vlScores
  let trScore ← scorer xTrain (Sum.inl yTrain)
  trainScores := trainScores ++ [trScore]
  if useVal then
    let xv ← readValData xVal
    let codes ← readValCodes yVal
    let vlScore ← scorer xv (Sum.inl codes)
    valScores := valScores ++ [vlScore]
    return { trainScores := trainScores, valScores := valScores,
             stop := shouldStop valScores }
  return { trainScores := trainScores, valScores := valScores,
           stop := shouldStop trainScores }
-- impl-end

-- proof-start
theorem correct_scoreEarlyStop :
    ∀ (scorer : Scorer) (shouldStop : List Score → Bool)
      (isClf useVal : Bool) (labels : Option (Array String))
      (xTrain : XData) (yTrain : Array Int)
      (xVal : Option XData) (yVal : Option (Array Int))
      (trScores vlScores : List Score),
      problem_spec_scoreEarlyStop scorer shouldStop isClf useVal labels
        xTrain yTrain xVal yVal trScores vlScores
        (implementation_scoreEarlyStop scorer shouldStop isClf useVal labels
          xTrain yTrain xVal yVal trScores vlScores) := by
  intro scorer shouldStop isClf useVal labels xTrain yTrain xVal yVal trScores vlScores
  unfold problem_spec_scoreEarlyStop implementation_scoreEarlyStop
  cases isClf <;> cases labels <;> cases useVal <;> cases xVal <;> cases yVal <;> rfl
-- proof-end
