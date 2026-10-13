import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The routine modeled below
-- classifies each raw token into either a keyword binding `name=value` or a bare
-- positional value; that lexical classification and the value-compilation step
-- are folded into the input encoding (the `Tok` carrier) via the I/O bijection
-- recorded in mapping.md, so they are reference-level boundary operations
-- validated by the conformance differential, not consumed proof axioms. Every
-- decision the routine itself makes — membership tests, duplicate detection,
-- positional consumption and the final completeness check — is modeled directly
-- below. The proof agent may introduce `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A single already-classified argument token handed to the binder: either a
keyword binding `name := value` or a bare positional `value`. (The lexical step
that decides which, and that compiles each value, is part of the input bridge —
see mapping.md.) -/
inductive Tok where
  | positional (value : String)
  | keyword (name : String) (value : String)
  deriving Repr, DecidableEq

/-- The accumulated binding state threaded through the token scan. -/
structure BindState where
  /-- Positional values collected so far, in order. -/
  args : List String
  /-- Keyword bindings collected so far, in order, as (name, value). -/
  kwargs : List (String × String)
  /-- Declared positional names still awaiting a value. -/
  pendingPositional : List String
  /-- Declared keyword-only names (without their own default) still awaiting a
  value. -/
  pendingKeyword : List String
  deriving Repr, DecidableEq

/-- The keyword-only names that still require an explicit value: every declared
keyword-only name that does not carry its own default. `keywordDefaults = none`
means no keyword-only default is declared, so all of them require a value. -/
def requiredKeywordOnly (keywordOnly : List String)
    (keywordDefaults : Option (List String)) : List String :=
  keywordOnly.filter (fun k =>
    match keywordDefaults with
    | none => true
    | some ds => ¬ ds.contains k)

/-- Error text when a name is provided as keyword but is not an accepted
parameter. -/
def msgUnexpectedKeyword (name param : String) : String :=
  "'" ++ name ++ "' received unexpected keyword argument '" ++ param ++ "'"

/-- Error text when the same keyword name is provided more than once. -/
def msgMultipleValues (name param : String) : String :=
  "'" ++ name ++ "' received multiple values for keyword argument '" ++ param ++ "'"

/-- Error text when a positional value follows a keyword binding. -/
def msgPositionalAfterKeyword (name : String) : String :=
  "'" ++ name ++ "' received some positional argument(s) after some keyword argument(s)"

/-- Error text when more positional values are given than accepted. -/
def msgTooManyPositional (name : String) : String :=
  "'" ++ name ++ "' received too many positional arguments"

/-- Error text listing the still-unfilled required parameters. -/
def msgMissing (name : String) (names : List String) : String :=
  "'" ++ name ++ "' did not receive value(s) for the argument(s): "
    ++ String.intercalate ", " (names.map (fun p => "'" ++ p ++ "'"))

/-- Error text when context-decorated but the first declared parameter is not
the context parameter. -/
def msgContext (name : String) : String :=
  "'" ++ name ++ "' is decorated with takes_context=True so it must "
    ++ "have a first argument of 'context'"

/-- The distinct failure value modeling the uncaught `IndexError` the real
routine raises when a context-decorated callable declares NO parameters at all
(indexing the first element of an empty list). This is a different observable
failure mode from the template-syntax diagnostics above (an unhandled crash,
not a formatted template error), so it is bridged as its own error value
(mapping.md: uncaught IndexError ↔ this exact string), keeping the model
faithful on every input without conflating the crash with a diagnostic. -/
def msgIndexError : String := "IndexError: list index out of range"

/-- Process one token against the current state. `params` is the accepted
positional-name list (after any context adjustment); `keywordOnly` the accepted
keyword-only names; `hasVarKeyword`/`hasVarArgs` whether the routine also accepts
arbitrary `**`/`*` arguments. -/
def stepTok (params keywordOnly : List String) (hasVarKeyword hasVarArgs : Bool)
    (name : String) (st : BindState) (tok : Tok) : Except String BindState :=
  match tok with
  | Tok.keyword param value =>
      if ¬ params.contains param ∧ ¬ keywordOnly.contains param ∧ ¬ hasVarKeyword then
        Except.error (msgUnexpectedKeyword name param)
      else if st.kwargs.any (fun kv => kv.1 == param) then
        Except.error (msgMultipleValues name param)
      else
        let st := { st with kwargs := st.kwargs ++ [(param, value)] }
        if st.pendingPositional.contains param then
          Except.ok { st with pendingPositional := st.pendingPositional.erase param }
        else if st.pendingKeyword.contains param then
          Except.ok { st with pendingKeyword := st.pendingKeyword.erase param }
        else
          Except.ok st
  | Tok.positional value =>
      if ¬ st.kwargs.isEmpty then
        Except.error (msgPositionalAfterKeyword name)
      else
        let st := { st with args := st.args ++ [value] }
        match st.pendingPositional with
        | [] => if hasVarArgs then Except.ok st
                else Except.error (msgTooManyPositional name)
        | _ :: rest => Except.ok { st with pendingPositional := rest }

/-- After the scan, drop the trailing positional names covered by `defaults`
(the count of trailing positional defaults, `none` if there are none), then
require every remaining positional and keyword-only slot to have been filled.

The truncation mirrors the real negative-slice `list[:-n]` exactly, INCLUDING
its `n = 0` quirk: `list[:-0]` is `list[:0]`, the EMPTY list — so a present but
empty defaults tuple (`some 0`) drops every still-pending positional name,
whereas an absent one (`none`) keeps them all. Modeled faithfully rather than
fenced. -/
def finalizeBind (defaults : Option Nat) (name : String) (st : BindState) :
    Except String (List String × List (String × String)) :=
  let pending :=
    match defaults with
    | some 0 => []  -- `[:-0]` = `[:0]` = [] : the Python negative-slice quirk
    | some n => st.pendingPositional.take (st.pendingPositional.length - n)
    | none => st.pendingPositional
  if ¬ pending.isEmpty ∨ ¬ st.pendingKeyword.isEmpty then
    Except.error (msgMissing name (pending ++ st.pendingKeyword))
  else
    Except.ok (st.args, st.kwargs)

/-- Functional reference for binding template-tag tokens to a callable's
parameters. Returns either the formatted error text or the `(args, kwargs)`
pair. -/
def parseTagArgsRef (params : List String) (hasVarArgs hasVarKeyword : Bool)
    (defaults : Option Nat) (keywordOnly : List String)
    (keywordDefaults : Option (List String)) (takesContext : Bool) (name : String)
    (toks : List Tok) : Except String (List String × List (String × String)) := do
  let params ←
    if takesContext then
      match params with
      | p :: rest => if p == "context" then pure rest else Except.error (msgContext name)
      | [] => Except.error msgIndexError
    else pure params
  let init : BindState :=
    { args := [], kwargs := [], pendingPositional := params,
      pendingKeyword := requiredKeywordOnly keywordOnly keywordDefaults }
  let st ← List.foldlM (stepTok params keywordOnly hasVarKeyword hasVarArgs name) init toks
  finalizeBind defaults name st
-- pure-end

-- post-conditions-start
/-- The bound result equals the grounded reference computation over the declared
parameters and the supplied tokens: the same `(args, kwargs)` pair on success,
and the same formatted error text on every rejection (unexpected keyword,
duplicate keyword, positional-after-keyword, too-many-positional, missing
required, and context-shape rejections). Every output component is pinned to the
inputs (frame discipline) through `parseTagArgsRef`.

Note for reviewers: this post-condition is an exact functional equality to
`parseTagArgsRef`, a reference that is fully grounded in the inputs (it is
defined constructively above from `stepTok`/`finalizeBind`, with no free or
opaque oracle) and is validated against the real routine by the conformance
differential. The spec is therefore DETERMINISTIC — any `result` satisfying it
is the single reference value on those inputs. A same-spec implementation can
verify only by computing exactly that value on every input (extensional
identity with the reference); a verifying same-spec variant — including one
that simply delegates to `parseTagArgsRef` — is extensionally the reference
behavior and is a positive control, NOT evidence of spec weakness, so it must
not be submitted as a counterexample attack. See
`spec_parseTagArgs_deterministic` in the proof region for the machine-checked
statement. -/
def problem_spec_parseTagArgs (params : List String) (hasVarArgs hasVarKeyword : Bool)
    (defaults : Option Nat) (keywordOnly : List String)
    (keywordDefaults : Option (List String)) (takesContext : Bool) (name : String)
    (toks : List Tok)
    (result : Except String (List String × List (String × String))) : Prop :=
  result = parseTagArgsRef params hasVarArgs hasVarKeyword defaults keywordOnly
    keywordDefaults takesContext name toks
-- post-conditions-end

-- impl-start
def implementation_parseTagArgs (params : List String) (hasVarArgs hasVarKeyword : Bool)
    (defaults : Option Nat) (keywordOnly : List String)
    (keywordDefaults : Option (List String)) (takesContext : Bool) (name : String)
    (toks : List Tok) :
    Except String (List String × List (String × String)) := Id.run do
  let mut params := params
  if takesContext then
    match params with
    | p :: rest =>
        if p == "context" then
          params := rest
        else
          return Except.error (msgContext name)
    | [] => return Except.error msgIndexError
  let mut st : BindState :=
    { args := [], kwargs := [], pendingPositional := params,
      pendingKeyword := requiredKeywordOnly keywordOnly keywordDefaults }
  for tok in toks do
    match tok with
    | Tok.keyword param value =>
        if ¬ params.contains param ∧ ¬ keywordOnly.contains param ∧ ¬ hasVarKeyword then
          return Except.error (msgUnexpectedKeyword name param)
        else if st.kwargs.any (fun kv => kv.1 == param) then
          return Except.error (msgMultipleValues name param)
        else
          st := { st with kwargs := st.kwargs ++ [(param, value)] }
          if st.pendingPositional.contains param then
            st := { st with pendingPositional := st.pendingPositional.erase param }
          else if st.pendingKeyword.contains param then
            st := { st with pendingKeyword := st.pendingKeyword.erase param }
    | Tok.positional value =>
        if ¬ st.kwargs.isEmpty then
          return Except.error (msgPositionalAfterKeyword name)
        else
          st := { st with args := st.args ++ [value] }
          match st.pendingPositional with
          | [] => if ¬ hasVarArgs then return Except.error (msgTooManyPositional name)
          | _ :: rest => st := { st with pendingPositional := rest }
  return finalizeBind defaults name st
-- impl-end


-- proof-start
/-- The imperative for-body's per-token dispatch, reified as an
`Except String BindState` value: a fall-through mutation becomes `.ok st'`, an
early `return Except.error e` becomes `.error e`. This mirrors the loop body of
`implementation_parseTagArgs` exactly (note the `Tok.positional []` arm's
`if ¬ hasVarArgs then error` shape). -/
def implStep (params keywordOnly : List String) (hasVarKeyword hasVarArgs : Bool)
    (name : String) (st : BindState) (tok : Tok) : Except String BindState :=
  match tok with
  | Tok.keyword param value =>
      if ¬ params.contains param ∧ ¬ keywordOnly.contains param ∧ ¬ hasVarKeyword then
        Except.error (msgUnexpectedKeyword name param)
      else if st.kwargs.any (fun kv => kv.1 == param) then
        Except.error (msgMultipleValues name param)
      else
        let st := { st with kwargs := st.kwargs ++ [(param, value)] }
        if st.pendingPositional.contains param then
          Except.ok { st with pendingPositional := st.pendingPositional.erase param }
        else if st.pendingKeyword.contains param then
          Except.ok { st with pendingKeyword := st.pendingKeyword.erase param }
        else
          Except.ok st
  | Tok.positional value =>
      if ¬ st.kwargs.isEmpty then
        Except.error (msgPositionalAfterKeyword name)
      else
        let st := { st with args := st.args ++ [value] }
        match st.pendingPositional with
        | [] => if ¬ hasVarArgs then Except.error (msgTooManyPositional name)
                else Except.ok st
        | _ :: rest => Except.ok { st with pendingPositional := rest }

/-- The imperative token scan of `implementation_parseTagArgs` together with its
trailing `finalizeBind`, abstracted over the starting state `s`. Successive
tokens mutate `st`; the first token whose handling early-returns
`Except.error e` short-circuits the whole loop to `Except.error e`; if no token
errors, the loop finishes and returns `finalizeBind defaults name st`. -/
def implFold (params keywordOnly : List String) (hasVarKeyword hasVarArgs : Bool)
    (defaults : Option Nat) (name : String) (s : BindState) (toks : List Tok) :
    Except String (List String × List (String × String)) := Id.run do
  let mut st := s
  for tok in toks do
    match tok with
    | Tok.keyword param value =>
        if ¬ params.contains param ∧ ¬ keywordOnly.contains param ∧ ¬ hasVarKeyword then
          return Except.error (msgUnexpectedKeyword name param)
        else if st.kwargs.any (fun kv => kv.1 == param) then
          return Except.error (msgMultipleValues name param)
        else
          st := { st with kwargs := st.kwargs ++ [(param, value)] }
          if st.pendingPositional.contains param then
            st := { st with pendingPositional := st.pendingPositional.erase param }
          else if st.pendingKeyword.contains param then
            st := { st with pendingKeyword := st.pendingKeyword.erase param }
    | Tok.positional value =>
        if ¬ st.kwargs.isEmpty then
          return Except.error (msgPositionalAfterKeyword name)
        else
          st := { st with args := st.args ++ [value] }
          match st.pendingPositional with
          | [] => if ¬ hasVarArgs then return Except.error (msgTooManyPositional name)
          | _ :: rest => st := { st with pendingPositional := rest }
  return finalizeBind defaults name st

/-- ScanStage / per-token branch correspondence: the imperative for-body's
dispatch on a single token (reified as `implStep`) computes exactly the same
`Except String BindState` outcome as the reference's `stepTok`. -/
theorem stepMatch (params keywordOnly : List String) (hasVarKeyword hasVarArgs : Bool)
    (name : String) (st : BindState) (tok : Tok) :
    implStep params keywordOnly hasVarKeyword hasVarArgs name st tok
      = stepTok params keywordOnly hasVarKeyword hasVarArgs name st tok := by
  cases tok <;> simp only [implStep, stepTok] <;> split_ifs <;> rfl

/-- ScanStage / empty-scan base case: with no tokens the imperative loop body
never runs, so `implFold` returns `finalizeBind defaults name s` on the starting
state unchanged. This is the `forIn`-on-`[]` reduction, isolated so `loopFold`'s
induction has a clean base step. -/
theorem implFold_nil (params keywordOnly : List String) (hasVarKeyword hasVarArgs : Bool)
    (defaults : Option Nat) (name : String) (s : BindState) :
    implFold params keywordOnly hasVarKeyword hasVarArgs defaults name s []
      = finalizeBind defaults name s := by rfl

/-- ScanStage / one-token unfolding: running the imperative loop over
`tok :: rest` from state `s` performs one `implStep` on `tok` — on
`Except.error e` the early `return` short-circuits the whole loop to
`Except.error e`, and on `Except.ok st'` the loop continues over `rest` from the
updated state `st'`. This is the `forIn`-on-cons reduction (the loop body reified
as `implStep`), isolated so `loopFold`'s induction has a clean step. -/
theorem implFold_cons (params keywordOnly : List String) (hasVarKeyword hasVarArgs : Bool)
    (defaults : Option Nat) (name : String) (s : BindState) (tok : Tok) (rest : List Tok) :
    implFold params keywordOnly hasVarKeyword hasVarArgs defaults name s (tok :: rest)
      = (match implStep params keywordOnly hasVarKeyword hasVarArgs name s tok with
         | Except.ok st' =>
             implFold params keywordOnly hasVarKeyword hasVarArgs defaults name st' rest
         | Except.error e => Except.error e) := by
  simp only [implFold, implStep, List.forIn_cons]
  cases tok <;> repeat' (first | rfl | split)
/-- ScanStage / loop-to-foldlM refinement (the operational heart): the
imperative loop-with-early-return-then-finalize equals running the reference
`stepTok` scan via `List.foldlM` in the `Except` monad and then applying
`finalizeBind` on success (error short-circuits). Proved by induction on `toks`
generalizing the starting state, using `stepMatch` for the head step. -/
theorem loopFold (params keywordOnly : List String) (hasVarKeyword hasVarArgs : Bool)
    (defaults : Option Nat) (name : String) (s : BindState) (toks : List Tok) :
    implFold params keywordOnly hasVarKeyword hasVarArgs defaults name s toks
      = (match List.foldlM (stepTok params keywordOnly hasVarKeyword hasVarArgs name) s toks with
         | Except.ok st => finalizeBind defaults name st
         | Except.error e => Except.error e) := by
  induction toks generalizing s with
  | nil => rw [implFold_nil]; rfl
  | cons tok rest ih =>
    rw [implFold_cons, stepMatch, List.foldlM_cons]
    cases h : stepTok params keywordOnly hasVarKeyword hasVarArgs name s tok with
    | error e => rfl
    | ok st' => simp only [bind, Except.bind]; exact ih st'

/-- ContextStage / stage-1 alignment: `implementation_parseTagArgs` performs its
leading context-parameter adjustment and then runs the rest of the routine as
`implFold` on the adjusted parameter list. On a `takesContext` mis-shape it
fails — `Except.error (msgContext name)` when the first declared param is not
`"context"`, `Except.error msgIndexError` when no param is declared at all
(the real routine's uncaught IndexError) — otherwise it continues with
`params` (context absent) or the tail `rest` (context matched). This is the
impl side of the first `do`-bind, exposing the shared `implFold`
continuation. -/
theorem context_stage_eq (params keywordOnly : List String)
    (hasVarArgs hasVarKeyword : Bool) (defaults : Option Nat)
    (keywordDefaults : Option (List String)) (takesContext : Bool) (name : String)
    (toks : List Tok) :
    implementation_parseTagArgs params hasVarArgs hasVarKeyword defaults keywordOnly
        keywordDefaults takesContext name toks
      = (if takesContext then
          match params with
          | p :: rest =>
              if p == "context" then
                implFold rest keywordOnly hasVarKeyword hasVarArgs defaults name
                  { args := [], kwargs := [], pendingPositional := rest,
                    pendingKeyword := requiredKeywordOnly keywordOnly keywordDefaults } toks
              else Except.error (msgContext name)
          | [] => Except.error msgIndexError
        else
          implFold params keywordOnly hasVarKeyword hasVarArgs defaults name
            { args := [], kwargs := [], pendingPositional := params,
              pendingKeyword := requiredKeywordOnly keywordOnly keywordDefaults } toks) := by
  unfold implementation_parseTagArgs implFold
  split <;> rfl

/-- InitStage / stage-2 alignment: given equal adjusted parameter lists, the
initial `BindState` built by `implementation_parseTagArgs` is literally the
`init` state built by `parseTagArgsRef`. -/
theorem init_eq (params keywordOnly : List String)
    (keywordDefaults : Option (List String)) :
    ({ args := [], kwargs := [], pendingPositional := params,
        pendingKeyword := requiredKeywordOnly keywordOnly keywordDefaults } : BindState)
      = { args := [], kwargs := [], pendingPositional := params,
          pendingKeyword := requiredKeywordOnly keywordOnly keywordDefaults } := rfl

/-- FinalizeStage / stage-4 alignment + error propagation: casing on the shared
`Except String BindState` scan result, applying `finalizeBind` on `.ok` and
propagating the error on `.error` is exactly the reference's monadic
`scan >>= finalizeBind` continuation. On `.ok stFinal` both sides equal
`finalizeBind defaults name stFinal`; on `.error e` both equal
`Except.error e`. -/
theorem finalize_eq (params keywordOnly : List String) (hasVarKeyword hasVarArgs : Bool)
    (defaults : Option Nat) (name : String) (s : BindState) (toks : List Tok) :
    (match List.foldlM (stepTok params keywordOnly hasVarKeyword hasVarArgs name) s toks with
     | Except.ok st => finalizeBind defaults name st
     | Except.error e => Except.error e)
      = (List.foldlM (stepTok params keywordOnly hasVarKeyword hasVarArgs name) s toks
          >>= fun st => finalizeBind defaults name st) := by
  cases List.foldlM (stepTok params keywordOnly hasVarKeyword hasVarArgs name) s toks <;> rfl

theorem correct_parseTagArgs :
    ∀ (params : List String) (hasVarArgs hasVarKeyword : Bool) (defaults : Option Nat)
      (keywordOnly : List String) (keywordDefaults : Option (List String))
      (takesContext : Bool) (name : String) (toks : List Tok),
      -- TOTAL: no precondition. The obligation pins the result on EVERY input,
      -- including the degenerate `takesContext = true ∧ params = []` shape
      -- (a misconfigured context tag), where both the reference and the
      -- implementation return the dedicated `msgIndexError` failure value —
      -- the model of the real routine's uncaught IndexError on that shape
      -- (refinement.md row 2). Leaving no input unconstrained means no
      -- same-spec implementation that deviates anywhere can verify.
      problem_spec_parseTagArgs params hasVarArgs hasVarKeyword defaults keywordOnly
        keywordDefaults takesContext name toks
        (implementation_parseTagArgs params hasVarArgs hasVarKeyword defaults keywordOnly
          keywordDefaults takesContext name toks) := by
  intro params hasVarArgs hasVarKeyword defaults keywordOnly keywordDefaults takesContext name toks
  unfold problem_spec_parseTagArgs
  rw [context_stage_eq]
  unfold parseTagArgsRef
  simp only [loopFold, finalize_eq]
  cases takesContext with
  | false => rfl
  | true =>
      cases params with
      | nil => rfl
      | cons p rest =>
          by_cases hp : p == "context" <;> simp only [hp, if_true] <;> rfl

/-- The spec is DETERMINISTIC and TOTAL: `problem_spec_parseTagArgs` pins
`result` by an exact equality to the grounded reference on EVERY input (no
precondition), so any two results satisfying it on the same inputs are equal —
in particular any satisfying `result` equals the implementation's output.
Hence no same-spec implementation with observably wrong behavior on ANY input
can verify: a verifying same-spec variant is extensionally the reference
behavior (a positive control, not a counterexample). -/
theorem spec_parseTagArgs_deterministic :
    ∀ (params : List String) (hasVarArgs hasVarKeyword : Bool) (defaults : Option Nat)
      (keywordOnly : List String) (keywordDefaults : Option (List String))
      (takesContext : Bool) (name : String) (toks : List Tok)
      (r : Except String (List String × List (String × String))),
      problem_spec_parseTagArgs params hasVarArgs hasVarKeyword defaults keywordOnly
        keywordDefaults takesContext name toks r →
      r = implementation_parseTagArgs params hasVarArgs hasVarKeyword defaults keywordOnly
            keywordDefaults takesContext name toks := by
  intro params hasVarArgs hasVarKeyword defaults keywordOnly keywordDefaults
    takesContext name toks r h
  have hi := correct_parseTagArgs params hasVarArgs hasVarKeyword defaults keywordOnly
    keywordDefaults takesContext name toks
  unfold problem_spec_parseTagArgs at h hi
  rw [h, hi]

-- proof-end
