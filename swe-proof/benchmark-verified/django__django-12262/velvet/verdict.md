# P2 adversarial audit — django__django-12262

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1_prepatch.lean`, `atk2_always_none.lean`, `atk3_const_err.lean`, `atk4_boundary_trunc.lean`, `atk5_offbyone.lean`, `atk6_echo_tail.lean`, `atk7_drop_error_passthrough.lean`, `atk8_swap_missing_order.lean` |

**Non-vacuity.** The positive control `atk_pos_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl verified, so there is no verify⇏correct witness. The spec is exact functional equality (`out = parseBits …`) over a fully-concrete pure region with NO axioms and NO opaque/oracle symbols; the only way to 'verify' is to return a value provably equal to concrete parseBits (i.e. behaviorally identical to gold).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The two helpers the per-bit scan consults — the one
@@ -175,10 +175,43 @@
       invariant i ≤ bits.length
       invariant st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)
       done_with i = bits.length
-      decreasing bits.length - i
     do
       let b := bits[i]!
-      st := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
+      -- Pre-image skeleton: the unexpected-keyword test consults the MUTATING
+      -- pending-keyword-only set (`st.pendingKeywordOnly`) instead of the full
+      -- declared set (`keywordOnlyParams`). The frozen spec's `stepBit` tests the
+      -- full declared set, so for a keyword-only parameter that is absent from
+      -- the pending set (it carries a default, or was already supplied once) the
+      -- two diverge — wrongly reporting it unexpected — and prove_correct MUST
+      -- fail.
+      let newSt : PState :=
+        match st.error with
+        | some _ => st
+        | none =>
+          match b with
+          | .keyword p =>
+              if !positionalParams.contains p && !st.pendingKeywordOnly.contains p && !acceptsExtraKeywords then
+                { st with error := some (.unexpectedKeyword p) }
+              else if st.recorded.contains p then
+                { st with error := some (.duplicateKeyword p) }
+              else
+                let recorded' := st.recorded ++ [p]
+                if st.pendingPositional.contains p then
+                  { st with recorded := recorded', pendingPositional := st.pendingPositional.erase p }
+                else if st.pendingKeywordOnly.contains p then
+                  { st with recorded := recorded', pendingKeywordOnly := st.pendingKeywordOnly.erase p }
+                else
+                  { st with recorded := recorded' }
+          | .positional =>
+              if !st.recorded.isEmpty then
+                { st with error := some .positionalAfterKeyword }
+              else
+                match st.pendingPositional with
+                | [] =>
+                    if acceptsExtraPositional then st
+                    else { st with error := some .tooManyPositional }
+                | _ :: rest => { st with pendingPositional := rest }
+      st := newSt
       i := i + 1
     return finalize st hasDefaults numDefaults
     -- impl-end
```

Attack 2 — `atk2_always_none.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The two helpers the per-bit scan consults — the one
@@ -169,18 +169,7 @@
   ensures out = parseBits bits positionalParams keywordOnlyParams keywordOnlyDefaults acceptsExtraKeywords acceptsExtraPositional hasDefaults numDefaults
   do
     -- impl-start
-    let mut st : PState := initState positionalParams keywordOnlyParams keywordOnlyDefaults
-    let mut i := 0
-    while i < bits.length
-      invariant i ≤ bits.length
-      invariant st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)
-      done_with i = bits.length
-      decreasing bits.length - i
-    do
-      let b := bits[i]!
-      st := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
-      i := i + 1
-    return finalize st hasDefaults numDefaults
+    return none
     -- impl-end
 
 prove_correct bindTagArguments by
```

Attack 3 — `atk3_const_err.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The two helpers the per-bit scan consults — the one
@@ -169,18 +169,7 @@
   ensures out = parseBits bits positionalParams keywordOnlyParams keywordOnlyDefaults acceptsExtraKeywords acceptsExtraPositional hasDefaults numDefaults
   do
     -- impl-start
-    let mut st : PState := initState positionalParams keywordOnlyParams keywordOnlyDefaults
-    let mut i := 0
-    while i < bits.length
-      invariant i ≤ bits.length
-      invariant st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)
-      done_with i = bits.length
-      decreasing bits.length - i
-    do
-      let b := bits[i]!
-      st := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
-      i := i + 1
-    return finalize st hasDefaults numDefaults
+    return some .tooManyPositional
     -- impl-end
 
 prove_correct bindTagArguments by
```

Attack 4 — `atk4_boundary_trunc.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The two helpers the per-bit scan consults — the one
@@ -175,12 +175,16 @@
       invariant i ≤ bits.length
       invariant st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)
       done_with i = bits.length
-      decreasing bits.length - i
     do
       let b := bits[i]!
       st := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
       i := i + 1
-    return finalize st hasDefaults numDefaults
+    -- boundary bug: truncate positional-pending by numDefaults directly instead of (len-numDefaults)
+    let leftover := if hasDefaults then st.pendingPositional.take numDefaults else st.pendingPositional
+    let missing := leftover ++ st.pendingKeywordOnly
+    match st.error with
+    | some e => return some e
+    | none => return (if missing.isEmpty then none else some (.missingArguments missing))
     -- impl-end
 
 prove_correct bindTagArguments by
```

Attack 5 — `atk5_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The two helpers the per-bit scan consults — the one
@@ -170,12 +170,11 @@
   do
     -- impl-start
     let mut st : PState := initState positionalParams keywordOnlyParams keywordOnlyDefaults
-    let mut i := 0
+    let mut i := 1
     while i < bits.length
       invariant i ≤ bits.length
       invariant st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)
       done_with i = bits.length
-      decreasing bits.length - i
     do
       let b := bits[i]!
       st := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
```

Attack 6 — `atk6_echo_tail.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The two helpers the per-bit scan consults — the one
@@ -169,18 +169,7 @@
   ensures out = parseBits bits positionalParams keywordOnlyParams keywordOnlyDefaults acceptsExtraKeywords acceptsExtraPositional hasDefaults numDefaults
   do
     -- impl-start
-    let mut st : PState := initState positionalParams keywordOnlyParams keywordOnlyDefaults
-    let mut i := 0
-    while i < bits.length
-      invariant i ≤ bits.length
-      invariant st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)
-      done_with i = bits.length
-      decreasing bits.length - i
-    do
-      let b := bits[i]!
-      st := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
-      i := i + 1
-    return finalize st hasDefaults numDefaults
+    return parseBits bits.tail positionalParams keywordOnlyParams keywordOnlyDefaults acceptsExtraKeywords acceptsExtraPositional hasDefaults numDefaults
     -- impl-end
 
 prove_correct bindTagArguments by
```

Attack 7 — `atk7_drop_error_passthrough.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The two helpers the per-bit scan consults — the one
@@ -175,12 +175,14 @@
       invariant i ≤ bits.length
       invariant st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)
       done_with i = bits.length
-      decreasing bits.length - i
     do
       let b := bits[i]!
       st := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
       i := i + 1
-    return finalize st hasDefaults numDefaults
+    -- control-flow-effect bug: ignore any mid-scan error; only run the missing check
+    let leftover := if hasDefaults then st.pendingPositional.take (st.pendingPositional.length - numDefaults) else st.pendingPositional
+    let missing := leftover ++ st.pendingKeywordOnly
+    return (if missing.isEmpty then none else some (.missingArguments missing))
     -- impl-end
 
 prove_correct bindTagArguments by
```

Attack 8 — `atk8_swap_missing_order.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The two helpers the per-bit scan consults — the one
@@ -175,12 +175,16 @@
       invariant i ≤ bits.length
       invariant st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)
       done_with i = bits.length
-      decreasing bits.length - i
     do
       let b := bits[i]!
       st := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
       i := i + 1
-    return finalize st hasDefaults numDefaults
+    match st.error with
+    | some e => return some e
+    | none =>
+      let leftover := if hasDefaults then st.pendingPositional.take (st.pendingPositional.length - numDefaults) else st.pendingPositional
+      let missing := st.pendingKeywordOnly ++ leftover
+      return (if missing.isEmpty then none else some (.missingArguments missing))
     -- impl-end
 
 prove_correct bindTagArguments by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos_correct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

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
    do
      let b := bits[i]!
      let st' := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
      st := st'
      i := i + 1
    let result := finalize st hasDefaults numDefaults
    return result
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
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY (A-legs focus per §4). Bundle: django__django-12262/velvet.

SPEC SHAPE: method bindTagArguments, ensures out = parseBits bits positionalParams keywordOnlyParams keywordOnlyDefaults acceptsExtraKeywords acceptsExtraPositional hasDefaults numDefaults. parseBits/stepBit/finalize/initState are fully concrete Lean in the frozen pure region. meta.json: axioms=[], deep_model_references=[], patch_diff_is_gold=True, conf_skip=False. This is the tightest spec class — total functional equality against a concrete oracle. No answer-key echo cheat exists except literally calling parseBits (the correct answer).

A-LEG AUDIT (my mandate): refinement.md has ZERO A-legs — all 10 rows are R / R+I / I (counted: 4×R, 5×R+I, 1×I; no A-consumed, no A-reference, no kind-3). meta.json confirms axioms=[] and deep_model_references=[], so G-AX is legitimately skip/VACUOUS and there is NO model↔callee correspondence to falsify. The two callees (token_kwargs, compile_filter) are UNCHANGED by the gold patch and correctly folded into the free input `bits : List Bit`; since the spec quantifies over ALL bits/name-lists, no classification is hidden and the folding is sound. Model↔patch correspondence VERIFIED against the frozen gold: gold patch is the single-line swap `param not in unhandled_kwargs` → `param not in kwonly` at django/template/library.py:264, exactly matching refinement.md row 4 / mapping.md §2 (kwonly ↔ keywordOnlyParams constant declared set; unhandled_kwargs ↔ pendingKeywordOnly mutating set). FAIL_TO_PASS count = 4.

SAME_SPEC: all 8 attacks + 2 positive controls confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). Impl-region-only edits (lines 172-182); axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; run concurrently ≤4/batch):
- atk_pos (identical to Solution.lean): EXIT 0 (positive control, verifies)
- atk_pos_correct (structurally different correct impl, let-bound result): EXIT 0 (positive control, verifies) — spec is non-vacuous/satisfiable
- atk1_prepatch (prepatch bug, pendingKeywordOnly test): EXIT 1 — unsolved goals at invariant_2 (221:203), the buggy membership set. prepatch reproduced ✓
- atk2_always_none (partial-domain: return none): EXIT 1 — invariant_2 case tag not found (loop removed)
- atk3_const_err (ungrounded const: return some tooManyPositional): EXIT 1 — invariant_2 case tag not found
- atk4_boundary_trunc (boundary: take numDefaults instead of len-numDefaults): EXIT 1 — WP-gen parse/unsolved
- atk5_offbyone (control-flow: start i:=1, drops first bit): EXIT 1 — simp_all made no progress (out=parseBits unmet)
- atk6_echo_tail (ungrounded-oracle echo: parseBits on bits.tail): EXIT 1 — invariant_2 case tag not found
- atk7_drop_error_passthrough (control-flow-effect: finalize drops mid-scan error): EXIT 1 — UNSOLVED GOALS (188:31); loop+invariant_2 kept byte-identical, fails on the out=parseBits equation
- atk8_swap_missing_order (missing-list order pendingKeywordOnly++leftover): EXIT 1 — UNSOLVED GOALS (190:31); loop+invariant kept byte-identical, fails on out=parseBits

atk7 & atk8 are the decisive ones: they keep the loop and invariant_2 verbatim and change ONLY the final return, so their exit-1 is the substantive out=parseBits rejection, not proof scaffolding. Every wrong output is genuinely rejected.

8 distinct wrong impls covering partial-domain (atk2), boundary (atk4), control-flow-effect (atk5/atk7), ungrounded-oracle echo (atk3/atk6), ordering (atk8), plus the prepatch bug (atk1). ALL fail to verify; BOTH correct impls verify.

RESOLVE OBLIGATION: the 'materialize faithful refined patch → run_resolve' step triggers ONLY for a verifying wrong impl (verify⇏correct witness). NONE verified, so the obligation is void — there is no broken-spec witness to resolve-test. No speculation: the resolve step was correctly not required because the falsification (a verifying wrong impl) never occurred.

VERDICT: SOUND. ≥5 (8) distinct same-spec wrong impls run and verified-to-fail; positive controls verify; A-legs (none) + model↔patch correspondence audited and hold. verify⇒correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1_prepatch.lean`, `atk2_always_none.lean`, `atk3_const_err.lean`, `atk4_boundary_trunc.lean`, `atk5_offbyone.lean`, `atk6_echo_tail.lean`, `atk7_drop_error_passthrough.lean`, `atk8_swap_missing_order.lean` |

**Non-vacuity.** The positive control `atk_pos_correct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl verified, so there is no verify⇏correct witness. The spec is exact functional equality (`out = parseBits …`) over a fully-concrete pure region with NO axioms and NO opaque/oracle symbols; the only way to 'verify' is to return a value provably equal to concrete parseBits (i.e. behaviorally identical to gold).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_always_none.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_const_err.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_boundary_trunc.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_echo_tail.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_drop_error_passthrough.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_swap_missing_order.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos_correct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

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
    do
      let b := bits[i]!
      let st' := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
      st := st'
      i := i + 1
    let result := finalize st hasDefaults numDefaults
    return result
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
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY (A-legs focus per §4). Bundle: django__django-12262/velvet.

SPEC SHAPE: method bindTagArguments, ensures out = parseBits bits positionalParams keywordOnlyParams keywordOnlyDefaults acceptsExtraKeywords acceptsExtraPositional hasDefaults numDefaults. parseBits/stepBit/finalize/initState are fully concrete Lean in the frozen pure region. meta.json: axioms=[], deep_model_references=[], patch_diff_is_gold=True, conf_skip=False. This is the tightest spec class — total functional equality against a concrete oracle. No answer-key echo cheat exists except literally calling parseBits (the correct answer).

A-LEG AUDIT (my mandate): refinement.md has ZERO A-legs — all 10 rows are R / R+I / I (counted: 4×R, 5×R+I, 1×I; no A-consumed, no A-reference, no kind-3). meta.json confirms axioms=[] and deep_model_references=[], so G-AX is legitimately skip/VACUOUS and there is NO model↔callee correspondence to falsify. The two callees (token_kwargs, compile_filter) are UNCHANGED by the gold patch and correctly folded into the free input `bits : List Bit`; since the spec quantifies over ALL bits/name-lists, no classification is hidden and the folding is sound. Model↔patch correspondence VERIFIED against the frozen gold: gold patch is the single-line swap `param not in unhandled_kwargs` → `param not in kwonly` at django/template/library.py:264, exactly matching refinement.md row 4 / mapping.md §2 (kwonly ↔ keywordOnlyParams constant declared set; unhandled_kwargs ↔ pendingKeywordOnly mutating set). FAIL_TO_PASS count = 4.

SAME_SPEC: all 8 attacks + 2 positive controls confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). Impl-region-only edits (lines 172-182); axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; run concurrently ≤4/batch):
- atk_pos (identical to Solution.lean): EXIT 0 (positive control, verifies)
- atk_pos_correct (structurally different correct impl, let-bound result): EXIT 0 (positive control, verifies) — spec is non-vacuous/satisfiable
- atk1_prepatch (prepatch bug, pendingKeywordOnly test): EXIT 1 — unsolved goals at invariant_2 (221:203), the buggy membership set. prepatch reproduced ✓
- atk2_always_none (partial-domain: return none): EXIT 1 — invariant_2 case tag not found (loop removed)
- atk3_const_err (ungrounded const: return some tooManyPositional): EXIT 1 — invariant_2 case tag not found
- atk4_boundary_trunc (boundary: take numDefaults instead of len-numDefaults): EXIT 1 — WP-gen parse/unsolved
- atk5_offbyone (control-flow: start i:=1, drops first bit): EXIT 1 — simp_all made no progress (out=parseBits unmet)
- atk6_echo_tail (ungrounded-oracle echo: parseBits on bits.tail): EXIT 1 — invariant_2 case tag not found
- atk7_drop_error_passthrough (control-flow-effect: finalize drops mid-scan error): EXIT 1 — UNSOLVED GOALS (188:31); loop+invariant_2 kept byte-identical, fails on the out=parseBits equation
- atk8_swap_missing_order (missing-list order pendingKeywordOnly++leftover): EXIT 1 — UNSOLVED GOALS (190:31); loop+invariant kept byte-identical, fails on out=parseBits

atk7 & atk8 are the decisive ones: they keep the loop and invariant_2 verbatim and change ONLY the final return, so their exit-1 is the substantive out=parseBits rejection, not proof scaffolding. Every wrong output is genuinely rejected.

8 distinct wrong impls covering partial-domain (atk2), boundary (atk4), control-flow-effect (atk5/atk7), ungrounded-oracle echo (atk3/atk6), ordering (atk8), plus the prepatch bug (atk1). ALL fail to verify; BOTH correct impls verify.

RESOLVE OBLIGATION: the 'materialize faithful refined patch → run_resolve' step triggers ONLY for a verifying wrong impl (verify⇏correct witness). NONE verified, so the obligation is void — there is no broken-spec witness to resolve-test. No speculation: the resolve step was correctly not required because the falsification (a verifying wrong impl) never occurred.

VERDICT: SOUND. ≥5 (8) distinct same-spec wrong impls run and verified-to-fail; positive controls verify; A-legs (none) + model↔patch correspondence audited and hold. verify⇒correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of bindTagArguments (models the per-bit argument-binding loop + final missing-argument check of django.template.library.parse_bits, gold-patched line :264 `param not in kwonly`). Checks performed:

1. SPEC IDENTITY: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True — the spec region (axioms/pure/pre/post/invariants stripped of impl) is byte-identical (signature-equal) between patched and prepatch, so the fix lives only in the impl, not the spec. G-DIFF confirms prepatch fails to verify against this spec (the buggy impl using `unhandled_kwargs` instead of `kwonly` is genuinely excluded).

2. LEAN VERIFIES: scripts/lean_verify.sh on Solution.lean → exit 0 (elaborates, proof discharged).

3. MODEL vs REAL CALLEE (not just the transliterated oracle): I monkeypatched the two UNCHANGED callees (token_kwargs → keyword/positional classification, compile_filter → opaque value) and drove the ACTUAL patched django/template/library.py parse_bits at base_commit, mapping raised TemplateSyntaxError kinds + missing-name sets back to the Err space. Fuzzed 200,000 random configs (param lists from a 6-name pool, varkw/varargs flags, defaults, bit sequences len 0-6) against the Lean shadow transliteration → 0 disagreements once names are strings.
   NOTE on a false alarm: with INTEGER names the harness showed 10 'divergences' in duplicate detection — this is a HARNESS artifact, not a model defect: real parse_bits stores `kwargs[str(param)] = value` but tests `param in kwargs`; with int param the str-key never matches so real code never fires 'duplicate'. Actual argument names are always strings (token_kwargs yields str keys), so `str(param)==param` and the model's `recorded.contains p` faithfully matches `param in kwargs`. With string names: 0/200000 disagreements.

4. FINALIZE TRUNCATION: Lean `pendingPositional.take (length - numDefaults)` uses Nat truncated subtraction (clamps at 0), exactly matching Python `unhandled_params[:-len(defaults)]` yielding [] when defaults exceed remaining. Verified `[1,2][:-5] == [] == [1,2][:max(0,2-5)]`. The mapping invariant `hasDefaults ⟹ numDefaults≥1` is sound: a function's `__defaults__`/getfullargspec.defaults is None (never an empty tuple) when there are no defaults, so `defaults is not None ⟺ len(defaults)≥1`.

5. Bundled conformance_check.py re-run → exit 0 (100012 checks, 0 disagreements).

The spec is neither too strong nor drifted: it holds for every bit classification (the abstracted-callee inputs are free), the unexpected-keyword admissibility test correctly uses the full kwonly set (the fix), duplicate/positional-after-keyword/too-many/missing kinds all match, and no input distinguishes the model from the real repo behavior. No divergence found — G-PANEL-2 FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified via swebench_unified.markers: same_spec(Solution, Solution_prepatch, velvet)=True (spec region axioms/pure/pre/post byte-identical between gold and buggy variants) and spec_view(Solution)==spec_view(Solution_prepatch). The spec region is empty pre/post; the obligation is `ensures out = parseBits ...` over the abstract pure model. Lexical screen clean: no source symbols in the spec view (checked unhandled_kwargs, kwonly, parse_bits, library.py, varkw, token_kwargs, compile_filter, simple_tag all absent); vocabulary is purely abstract (Name:=Nat, keywordOnlyParams, pendingKeywordOnly, parseBits/stepBit/finalize). Substantively, the spec encodes the CORRECT behavior — keyword admissibility tested against the FULL declared keyword-only set (independent of pending status, so a kw-only-with-default or already-supplied kw is accepted), and a repeated keyword yields duplicateKeyword not unexpectedKeyword. Both facts are fully disclosed by the PUBLIC problem_statement: the `{% hello greeting='hi' %}` false 'unexpected keyword argument' bug and the wrong 'multiple values' vs 'unexpected keyword' message. The spec never names the gold edit (`param not in unhandled_kwargs` -> `param not in kwonly`), the changed file/function, or the source variables; it reveals nothing about the fix beyond what the public bug report already states. A correct spec derivable from the public statement is not leakage. No reliance on hints_text.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
