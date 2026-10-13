import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two helpers the per-bit scan consults — the one
--  that classifies a bit as a keyword (name + value) or a plain positional, and
--  the one that compiles a positional value — are UNCHANGED and produce data the
--  binding decision under spec does not read beyond the keyword/positional
--  classification. They are folded into the free input `bits : List Bit` (each
--  bit pre-classified). The spec makes no behavioural claim about them and holds
--  for EVERY classification, so there is nothing to check against a real callee,
--  hence no G-AX. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- An argument name, identified abstractly: only equality / membership is ever
   observed, so the concrete spelling is irrelevant. -/
abbrev Name := Nat

/- One already-classified argument bit of the supplied argument list:
   * `keyword p` — a `name=value` bit naming `p` (the value is irrelevant to the
     binding decision and is dropped);
   * `positional` — a plain positional value. -/
inductive Bit where
  | keyword (p : Name)
  | positional
  deriving DecidableEq, Inhabited, Repr

/- The outcome reported when an argument list is malformed. `none` (no `Err`)
   means the list bound successfully. -/
inductive Err where
  | unexpectedKeyword (p : Name)        -- a keyword the tag does not accept
  | duplicateKeyword (p : Name)         -- a keyword supplied more than once
  | positionalAfterKeyword             -- a positional bit after a keyword bit
  | tooManyPositional                  -- more positionals than the tag takes
  | missingArguments (names : List Name) -- required arguments left unsupplied
  deriving DecidableEq, Inhabited, Repr

/- The state threaded while scanning the bits left to right:
   * `recorded`           — names already bound (only membership is consulted);
   * `pendingPositional`  — positional parameters not yet supplied;
   * `pendingKeywordOnly` — keyword-only parameters that still REQUIRE a value
                            (those carrying a default are never pending);
   * `error`              — the first malformation detected, if any. Once set,
                            scanning is inert (the real scan stops at the first
                            error). -/
structure PState where
  recorded : List Name
  pendingPositional : List Name
  pendingKeywordOnly : List Name
  error : Option Err
  deriving DecidableEq, Inhabited

/- The seed state. Nothing is bound yet; every positional parameter is pending;
   a keyword-only parameter is pending exactly when it carries no default. -/
def initState (positionalParams keywordOnlyParams keywordOnlyDefaults : List Name) : PState :=
  { recorded := [],
    pendingPositional := positionalParams,
    pendingKeywordOnly := keywordOnlyParams.filter (fun k => !keywordOnlyDefaults.contains k),
    error := none }

/- Advance the scan by one bit. Inert once an error has been recorded.

   For a keyword bit naming `p`:
   * it is an UNEXPECTED keyword iff `p` is neither a positional parameter nor a
     declared keyword-only parameter, AND the tag does not accept arbitrary extra
     keywords. The admissibility test is against the FULL set of declared
     keyword-only parameter names — independent of which ones are still pending —
     so a keyword-only parameter that carries a default, or one already supplied,
     is still recognised as accepted.
   * otherwise, if `p` was already bound, it is a DUPLICATE.
   * otherwise it is recorded, and if it matches a pending positional (keyword
     syntax for a positional parameter) or a pending keyword-only parameter, that
     parameter is consumed.

   For a positional bit:
   * a positional after any keyword has been bound is an ordering error;
   * otherwise it consumes the next pending positional, or — if none remain and
     the tag does not accept arbitrary extra positionals — is one too many. -/
def stepBit (positionalParams keywordOnlyParams : List Name)
    (acceptsExtraKeywords acceptsExtraPositional : Bool)
    (st : PState) (bit : Bit) : PState :=
  match st.error with
  | some _ => st
  | none =>
    match bit with
    | .keyword p =>
        if !positionalParams.contains p && !keywordOnlyParams.contains p && !acceptsExtraKeywords then
          { st with error := some (.unexpectedKeyword p) }
        else if st.recorded.contains p then
          { st with error := some (.duplicateKeyword p) }
        else
          let recorded' := st.recorded ++ [p]
          if st.pendingPositional.contains p then
            { st with recorded := recorded', pendingPositional := st.pendingPositional.erase p }
          else if st.pendingKeywordOnly.contains p then
            { st with recorded := recorded', pendingKeywordOnly := st.pendingKeywordOnly.erase p }
          else
            { st with recorded := recorded' }
    | .positional =>
        if !st.recorded.isEmpty then
          { st with error := some .positionalAfterKeyword }
        else
          match st.pendingPositional with
          | [] =>
              if acceptsExtraPositional then st
              else { st with error := some .tooManyPositional }
          | _ :: rest => { st with pendingPositional := rest }

/- After the whole list is scanned: report any error raised mid-scan, otherwise
   check that every required argument was supplied. When the callable carries
   positional defaults, its last `numDefaults` positional parameters are
   considered satisfied (they may be omitted), so they are dropped from the
   pending positionals before the requirement check. The remaining pending
   positionals together with the still-required keyword-only parameters are the
   missing arguments. -/
def finalize (st : PState) (hasDefaults : Bool) (numDefaults : Nat) : Option Err :=
  match st.error with
  | some e => some e
  | none =>
      let leftoverPositional :=
        if hasDefaults then st.pendingPositional.take (st.pendingPositional.length - numDefaults)
        else st.pendingPositional
      let missing := leftoverPositional ++ st.pendingKeywordOnly
      if missing.isEmpty then none else some (.missingArguments missing)

/- The binding outcome of a whole argument list: scan every bit left to right
   from the seed state, then finalize. -/
def parseBits (bits : List Bit)
    (positionalParams keywordOnlyParams keywordOnlyDefaults : List Name)
    (acceptsExtraKeywords acceptsExtraPositional hasDefaults : Bool) (numDefaults : Nat) : Option Err :=
  finalize
    (bits.foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional)
      (initState positionalParams keywordOnlyParams keywordOnlyDefaults))
    hasDefaults numDefaults

/- Forward-fold step: extending the consumed prefix by one bit advances the scan
   built from the shorter prefix by exactly that bit. The single goal `loom_solve`
   leaves for the loop body. -/
lemma scan_take_step (f : PState → Bit → PState) (s0 : PState) (bits : List Bit)
    (i : Nat) (hi : i < bits.length) :
    (bits.take (i + 1)).foldl f s0 = f ((bits.take i).foldl f s0) bits[i]! := by
  have hcons : bits.take (i + 1) = bits.take i ++ [bits[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Bind the supplied argument bits of a custom template tag, reporting the first
   malformation or, on success, that every required argument was supplied. The
   declared-parameter lists, the extra-argument flags, the defaults count and the
   bits are read-only (not `mut`): the scan threads a fresh accumulator and never
   mutates anything it is handed (directive 5). -/
method bindTagArguments
    (bits : List Bit) (positionalParams : List Name) (keywordOnlyParams : List Name) (keywordOnlyDefaults : List Name)
    (acceptsExtraKeywords : Bool) (acceptsExtraPositional : Bool) (hasDefaults : Bool) (numDefaults : Nat)
    return (out : Option Err)
  ensures out = parseBits bits positionalParams keywordOnlyParams keywordOnlyDefaults acceptsExtraKeywords acceptsExtraPositional hasDefaults numDefaults
  do
    -- impl-start
    let mut st : PState := initState positionalParams keywordOnlyParams keywordOnlyDefaults
    let mut i := 0
    while i < bits.length
      invariant i ≤ bits.length
      invariant st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)
      done_with i = bits.length
      decreasing bits.length - i
    do
      let b := bits[i]!
      -- Pre-image skeleton: the unexpected-keyword test consults the MUTATING
      -- pending-keyword-only set (`st.pendingKeywordOnly`) instead of the full
      -- declared set (`keywordOnlyParams`). The frozen spec's `stepBit` tests the
      -- full declared set, so for a keyword-only parameter that is absent from
      -- the pending set (it carries a default, or was already supplied once) the
      -- two diverge — wrongly reporting it unexpected — and prove_correct MUST
      -- fail.
      let newSt : PState :=
        match st.error with
        | some _ => st
        | none =>
          match b with
          | .keyword p =>
              if !positionalParams.contains p && !st.pendingKeywordOnly.contains p && !acceptsExtraKeywords then
                { st with error := some (.unexpectedKeyword p) }
              else if st.recorded.contains p then
                { st with error := some (.duplicateKeyword p) }
              else
                let recorded' := st.recorded ++ [p]
                if st.pendingPositional.contains p then
                  { st with recorded := recorded', pendingPositional := st.pendingPositional.erase p }
                else if st.pendingKeywordOnly.contains p then
                  { st with recorded := recorded', pendingKeywordOnly := st.pendingKeywordOnly.erase p }
                else
                  { st with recorded := recorded' }
          | .positional =>
              if !st.recorded.isEmpty then
                { st with error := some .positionalAfterKeyword }
              else
                match st.pendingPositional with
                | [] =>
                    if acceptsExtraPositional then st
                    else { st with error := some .tooManyPositional }
                | _ :: rest => { st with pendingPositional := rest }
      st := newSt
      i := i + 1
    return finalize st hasDefaults numDefaults
    -- impl-end

prove_correct bindTagArguments by
  loom_solve
  case «invariant_2: st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)» =>
    have hi : i < bits.length := by omega
    rw [invariant_2,
        scan_take_step (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional)
          (initState positionalParams keywordOnlyParams keywordOnlyDefaults) bits i hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  all_goals simp_all [parseBits]
