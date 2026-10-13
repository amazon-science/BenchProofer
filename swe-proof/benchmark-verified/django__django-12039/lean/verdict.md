# P2 adversarial audit — django__django-12039

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,7 @@
   String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
     let mut col := quoteName p.1
     match suffixes[p.2]? with
-    | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
+    | some suffix => col := col ++ suffix
     | none => pure ()
     return col))
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,7 @@
   String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
     let mut col := quoteName p.1
     match suffixes[p.2]? with
-    | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
+    | some suffix => col := col ++ " " ++ suffix
     | none => pure ()
     return col))
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
 -- impl-start
 def implementation_renderColumns (quoteName : String → String)
     (columns suffixes : List String) : String :=
-  String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
+  String.intercalate "," (columns.zipIdx.map (fun p => Id.run do
     let mut col := quoteName p.1
     match suffixes[p.2]? with
     | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -72,12 +72,10 @@
 -- impl-start
 def implementation_renderColumns (quoteName : String → String)
     (columns suffixes : List String) : String :=
-  String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
-    let mut col := quoteName p.1
+  String.intercalate ", " (columns.zipIdx.map (fun p =>
     match suffixes[p.2]? with
-    | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
-    | none => pure ()
-    return col))
+    | some suffix => if suffix ≠ "" then quoteName p.1 ++ " " ++ suffix else quoteName p.1
+    | none => quoteName p.1))
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -101,12 +101,15 @@
 -- impl-start
 def implementation_renderIndexColumns (quoteName : String → String)
     (columns suffixes opclasses : List String) : String :=
-  String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
-    let mut col := quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")
-    match suffixes[p.2]? with
-    | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
-    | none => pure ()
-    return col))
+  if columns.length ≤ opclasses.length then
+    String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
+      let mut col := quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")
+      match suffixes[p.2]? with
+      | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
+      | none => pure ()
+      return col))
+  else
+    "BROKEN_OUT_OF_DOMAIN"
 -- impl-end
 
 -- proof-start
@@ -115,7 +118,8 @@
       columns.length ≤ opclasses.length →
       problem_spec_renderIndexColumns quoteName columns suffixes opclasses
         (implementation_renderIndexColumns quoteName columns suffixes opclasses) := by
-  intro quoteName columns suffixes opclasses _
+  intro quoteName columns suffixes opclasses h
   unfold problem_spec_renderIndexColumns implementation_renderIndexColumns renderIndexColumns
+  rw [if_pos h]
   congr 1
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -102,7 +102,7 @@
 def implementation_renderIndexColumns (quoteName : String → String)
     (columns suffixes opclasses : List String) : String :=
   String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
-    let mut col := quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")
+    let mut col := quoteName p.1
     match suffixes[p.2]? with
     | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
     | none => pure ()
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,7 @@
   String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
     let mut col := quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")
     match suffixes[p.2]? with
-    | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
+    | some suffix => col := col ++ " " ++ suffix
     | none => pure ()
     return col))
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a comma-separated list of column references for a database DDL
statement.

Each entry in the list is built from a column name and an optional rendering
hint supplied positionally. A name-quoting function turns a raw column name into
its quoted, statement-ready form. Two flavours of list are rendered:

* a plain list, where each entry is the quoted column name, optionally followed
  by a positional hint;
* an operator-annotated list, where each entry is the quoted column name
  followed by a mandatory per-column annotation, then optionally the positional
  hint.

The positional hints are addressed by entry position; a position with no hint
(out of range) contributes nothing. The required separation rule is: a hint is
appended only when it is a non-empty token, and when appended it is set off from
what precedes it by a single space. In particular an empty hint must leave the
entry unchanged — it contributes neither a token nor a stray separating space.
Entries are then joined with `", "`.
-/

-- axioms-start
-- The name-quoting operation is an UNCHANGED collaborator supplied by the
-- caller. It is modeled as an arbitrary function `quoteName : String → String`
-- and universally quantified in the correctness statement, so the contract
-- holds for every possible quoting behavior; no `opaque`/`axiom` callee
-- contract is required. The rendering rule itself (the separation/empty-hint
-- behavior the specification pins) is modeled DEEPLY below, not axiomatized.
-- axioms-end

-- pure-start
/-- Append a positional hint to an already-rendered entry `col`.

The hint for this entry is looked up positionally; a missing (out-of-range)
position leaves the entry untouched. A present but empty hint is also dropped.
A present, non-empty hint is appended preceded by exactly one space. -/
def appendSuffix (col : String) (suffixes : List String) (idx : Nat) : String :=
  match suffixes[idx]? with
  | some suffix => if suffix ≠ "" then col ++ " " ++ suffix else col
  | none => col

/-- Render the plain column list: each quoted column name, optionally followed
by its positional hint, joined with `", "`. -/
def renderColumns (quoteName : String → String)
    (columns suffixes : List String) : String :=
  String.intercalate ", "
    (columns.zipIdx.map (fun p => appendSuffix (quoteName p.1) suffixes p.2))

/-- Render the operator-annotated column list: each quoted column name followed
by its mandatory per-column annotation (separated by a space), then optionally
its positional hint, joined with `", "`. A missing annotation position
contributes the empty token. -/
def renderIndexColumns (quoteName : String → String)
    (columns suffixes opclasses : List String) : String :=
  String.intercalate ", "
    (columns.zipIdx.map (fun p =>
      appendSuffix (quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")) suffixes p.2))
-- pure-end

-- post-conditions-start
/-- The plain rendering equals the entry-wise, positionally-hinted, space-set
join described by `renderColumns`. -/
def problem_spec_renderColumns (quoteName : String → String)
    (columns suffixes : List String) (result : String) : Prop :=
  result = renderColumns quoteName columns suffixes
-- post-conditions-end

-- impl-start
def implementation_renderColumns (quoteName : String → String)
    (columns suffixes : List String) : String :=
  String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
    let mut col := quoteName p.1
    match suffixes[p.2]? with
    | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
    | none => pure ()
    return col))
-- impl-end

-- proof-start
theorem correct_renderColumns :
    ∀ (quoteName : String → String) (columns suffixes : List String),
      problem_spec_renderColumns quoteName columns suffixes
        (implementation_renderColumns quoteName columns suffixes) := by
  intro quoteName columns suffixes
  unfold problem_spec_renderColumns implementation_renderColumns renderColumns
  congr 1
-- proof-end

-- post-conditions-start
/-- The operator-annotated rendering equals the entry-wise, positionally-hinted,
space-set join described by `renderIndexColumns`. -/
def problem_spec_renderIndexColumns (quoteName : String → String)
    (columns suffixes opclasses : List String) (result : String) : Prop :=
  result = renderIndexColumns quoteName columns suffixes opclasses
-- post-conditions-end

-- impl-start
def implementation_renderIndexColumns (quoteName : String → String)
    (columns suffixes opclasses : List String) : String :=
  String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
    let mut col := quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")
    match suffixes[p.2]? with
    | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
    | none => pure ()
    return col))
-- impl-end

-- proof-start
theorem correct_renderIndexColumns :
    ∀ (quoteName : String → String) (columns suffixes opclasses : List String),
      columns.length ≤ opclasses.length →
      problem_spec_renderIndexColumns quoteName columns suffixes opclasses
        (implementation_renderIndexColumns quoteName columns suffixes opclasses) := by
  intro quoteName columns suffixes opclasses _
  unfold problem_spec_renderIndexColumns implementation_renderIndexColumns renderIndexColumns
  congr 1
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS DEEPLY MODELED. spec_view includes appendSuffix/renderColumns/renderIndexColumns and both postconditions are `result = render*(...)`, so a verifying impl is pinned extensionally to the deep model. A-legs are vacuous: no axiom/opaque; quoteName is universally quantified (mapping.md/axiom_check.py stub confirm no consumed callee axiom, no A-reference; refinement.md legs are all R/I, no kind-3). correct_renderIndexColumns carries precondition `columns.length <= opclasses.length`, matching the Index.__init__ len(opclasses)==len(columns) invariant. 

7 same-spec attacks (all same_spec=True vs Solution.lean), verified via `bash scripts/lean_verify.sh <f>`:
- atk_1 (prepatch_1 bug: renderColumns col++suffix no space, unconditional): exit=1 REJECTED.
- atk_2 (renderColumns drop non-empty guard -> trailing space on empty hint): exit=1 REJECTED.
- atk_3 (renderColumns wrong join separator ","): exit=1 REJECTED.
- atk_4 (renderColumns correct echo, match-based no Id.run): exit=0 VERIFIES; `#print axioms` -> both correct_* depend on NO axioms (clean).
- atk_5 (renderIndexColumns PARTIAL-DOMAIN: returns "BROKEN_OUT_OF_DOMAIN" when columns.length > opclasses.length; proof discharges the if via `rw [if_pos h]` on the precondition): exit=0 VERIFIES; clean axioms.
- atk_6 (renderIndexColumns drops opclass annotation): exit=1 REJECTED.
- atk_7 (prepatch_2 bug: renderIndexColumns unconditional ' '++suffix -> trailing space): exit=1 REJECTED.
- pos_control (gold Solution.lean verbatim): exit=0 VERIFIES; clean axioms.

PROTOCOL STEP 2 (materialize + run_resolve for EVERY verifying clean-axiom impl):
- atk_4 faithful patch (= gold patch): run_resolve -> resolved=True, completed=True, note=resolved.
- atk_5 faithful patch (gold + `if len(self.columns) > len(self.opclasses): return 'BROKEN_OUT_OF_DOMAIN'` guard in IndexColumns.__str__): git apply --check OK at base 58c1acb1d6; run_resolve -> resolved=True, completed=True, note=resolved.

CONCLUSION: Both impls that verify with clean axioms have faithful patches that RESOLVE under the official harness. atk_4 is a behaviorally-correct echo (no weakness). atk_5 differs from gold ONLY on the out-of-domain columns.length>opclasses.length case, which the real Index.__init__ invariant guarantees is never reached (and where the real code itself IndexErrors); the hidden tests never exercise it, so it resolves — the precondition binder is a FAITHFUL domain restriction, not a spec weakness. All 5 genuinely-wrong mutants (prepatch bugs, boundary, control-flow, annotation-drop) are REJECTED by verification. No verify⇏correct exhibited. refinement.md/mapping.md audit: legs are R/I only, no kind-3, A-legs vacuous, quoteName-as-arbitrary-function correspondence holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a comma-separated list of column references for a database DDL
statement.

Each entry in the list is built from a column name and an optional rendering
hint supplied positionally. A name-quoting function turns a raw column name into
its quoted, statement-ready form. Two flavours of list are rendered:

* a plain list, where each entry is the quoted column name, optionally followed
  by a positional hint;
* an operator-annotated list, where each entry is the quoted column name
  followed by a mandatory per-column annotation, then optionally the positional
  hint.

The positional hints are addressed by entry position; a position with no hint
(out of range) contributes nothing. The required separation rule is: a hint is
appended only when it is a non-empty token, and when appended it is set off from
what precedes it by a single space. In particular an empty hint must leave the
entry unchanged — it contributes neither a token nor a stray separating space.
Entries are then joined with `", "`.
-/

-- axioms-start
-- The name-quoting operation is an UNCHANGED collaborator supplied by the
-- caller. It is modeled as an arbitrary function `quoteName : String → String`
-- and universally quantified in the correctness statement, so the contract
-- holds for every possible quoting behavior; no `opaque`/`axiom` callee
-- contract is required. The rendering rule itself (the separation/empty-hint
-- behavior the specification pins) is modeled DEEPLY below, not axiomatized.
-- axioms-end

-- pure-start
/-- Append a positional hint to an already-rendered entry `col`.

The hint for this entry is looked up positionally; a missing (out-of-range)
position leaves the entry untouched. A present but empty hint is also dropped.
A present, non-empty hint is appended preceded by exactly one space. -/
def appendSuffix (col : String) (suffixes : List String) (idx : Nat) : String :=
  match suffixes[idx]? with
  | some suffix => if suffix ≠ "" then col ++ " " ++ suffix else col
  | none => col

/-- Render the plain column list: each quoted column name, optionally followed
by its positional hint, joined with `", "`. -/
def renderColumns (quoteName : String → String)
    (columns suffixes : List String) : String :=
  String.intercalate ", "
    (columns.zipIdx.map (fun p => appendSuffix (quoteName p.1) suffixes p.2))

/-- Render the operator-annotated column list: each quoted column name followed
by its mandatory per-column annotation (separated by a space), then optionally
its positional hint, joined with `", "`. A missing annotation position
contributes the empty token. -/
def renderIndexColumns (quoteName : String → String)
    (columns suffixes opclasses : List String) : String :=
  String.intercalate ", "
    (columns.zipIdx.map (fun p =>
      appendSuffix (quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")) suffixes p.2))
-- pure-end

-- post-conditions-start
/-- The plain rendering equals the entry-wise, positionally-hinted, space-set
join described by `renderColumns`. -/
def problem_spec_renderColumns (quoteName : String → String)
    (columns suffixes : List String) (result : String) : Prop :=
  result = renderColumns quoteName columns suffixes
-- post-conditions-end

-- impl-start
def implementation_renderColumns (quoteName : String → String)
    (columns suffixes : List String) : String :=
  String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
    let mut col := quoteName p.1
    match suffixes[p.2]? with
    | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
    | none => pure ()
    return col))
-- impl-end

-- proof-start
theorem correct_renderColumns :
    ∀ (quoteName : String → String) (columns suffixes : List String),
      problem_spec_renderColumns quoteName columns suffixes
        (implementation_renderColumns quoteName columns suffixes) := by
  intro quoteName columns suffixes
  unfold problem_spec_renderColumns implementation_renderColumns renderColumns
  congr 1
-- proof-end

-- post-conditions-start
/-- The operator-annotated rendering equals the entry-wise, positionally-hinted,
space-set join described by `renderIndexColumns`. -/
def problem_spec_renderIndexColumns (quoteName : String → String)
    (columns suffixes opclasses : List String) (result : String) : Prop :=
  result = renderIndexColumns quoteName columns suffixes opclasses
-- post-conditions-end

-- impl-start
def implementation_renderIndexColumns (quoteName : String → String)
    (columns suffixes opclasses : List String) : String :=
  String.intercalate ", " (columns.zipIdx.map (fun p => Id.run do
    let mut col := quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")
    match suffixes[p.2]? with
    | some suffix => if suffix ≠ "" then col := col ++ " " ++ suffix
    | none => pure ()
    return col))
-- impl-end

-- proof-start
theorem correct_renderIndexColumns :
    ∀ (quoteName : String → String) (columns suffixes opclasses : List String),
      columns.length ≤ opclasses.length →
      problem_spec_renderIndexColumns quoteName columns suffixes opclasses
        (implementation_renderIndexColumns quoteName columns suffixes opclasses) := by
  intro quoteName columns suffixes opclasses _
  unfold problem_spec_renderIndexColumns implementation_renderIndexColumns renderIndexColumns
  congr 1
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS DEEPLY MODELED. spec_view includes appendSuffix/renderColumns/renderIndexColumns and both postconditions are `result = render*(...)`, so a verifying impl is pinned extensionally to the deep model. A-legs are vacuous: no axiom/opaque; quoteName is universally quantified (mapping.md/axiom_check.py stub confirm no consumed callee axiom, no A-reference; refinement.md legs are all R/I, no kind-3). correct_renderIndexColumns carries precondition `columns.length <= opclasses.length`, matching the Index.__init__ len(opclasses)==len(columns) invariant. 

7 same-spec attacks (all same_spec=True vs Solution.lean), verified via `bash scripts/lean_verify.sh <f>`:
- atk_1 (prepatch_1 bug: renderColumns col++suffix no space, unconditional): exit=1 REJECTED.
- atk_2 (renderColumns drop non-empty guard -> trailing space on empty hint): exit=1 REJECTED.
- atk_3 (renderColumns wrong join separator ","): exit=1 REJECTED.
- atk_4 (renderColumns correct echo, match-based no Id.run): exit=0 VERIFIES; `#print axioms` -> both correct_* depend on NO axioms (clean).
- atk_5 (renderIndexColumns PARTIAL-DOMAIN: returns "BROKEN_OUT_OF_DOMAIN" when columns.length > opclasses.length; proof discharges the if via `rw [if_pos h]` on the precondition): exit=0 VERIFIES; clean axioms.
- atk_6 (renderIndexColumns drops opclass annotation): exit=1 REJECTED.
- atk_7 (prepatch_2 bug: renderIndexColumns unconditional ' '++suffix -> trailing space): exit=1 REJECTED.
- pos_control (gold Solution.lean verbatim): exit=0 VERIFIES; clean axioms.

PROTOCOL STEP 2 (materialize + run_resolve for EVERY verifying clean-axiom impl):
- atk_4 faithful patch (= gold patch): run_resolve -> resolved=True, completed=True, note=resolved.
- atk_5 faithful patch (gold + `if len(self.columns) > len(self.opclasses): return 'BROKEN_OUT_OF_DOMAIN'` guard in IndexColumns.__str__): git apply --check OK at base 58c1acb1d6; run_resolve -> resolved=True, completed=True, note=resolved.

CONCLUSION: Both impls that verify with clean axioms have faithful patches that RESOLVE under the official harness. atk_4 is a behaviorally-correct echo (no weakness). atk_5 differs from gold ONLY on the out-of-domain columns.length>opclasses.length case, which the real Index.__init__ invariant guarantees is never reached (and where the real code itself IndexErrors); the hidden tests never exercise it, so it resolves — the precondition binder is a FAITHFUL domain restriction, not a spec weakness. All 5 genuinely-wrong mutants (prepatch bugs, boundary, control-flow, annotation-drop) are REJECTED by verification. No verify⇏correct exhibited. refinement.md/mapping.md audit: legs are R/I only, no kind-3, A-legs vacuous, quoteName-as-arbitrary-function correspondence holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verification performed:
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry/error).
- #print axioms correct_renderColumns / correct_renderIndexColumns -> both 'does not depend on any axioms' (genuine proofs, closed by definitional congr on identity impl=spec; no sorryAx).
- same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True with LeanBackend -> spec region byte-identical; spec is not tuned to the fix.
- Built qn helper and #eval'd 9 targeted cases in Lean; ran the identical inputs against the REAL post-patch repo (Columns/IndexColumns) -> all 9 outputs identical, including empty-suffix ('a', 'b' with '' -> no trailing space), out-of-range suffix, empty column list ('' result), more-suffixes-than-columns (extra ignored), leading-space ' DESC' token, and empty opclass.
- 20,000-case randomized differential fuzz (seed 12039) over Columns (unrestricted domain) and IndexColumns (domain columns.length ≤ opclasses.length) -> 0 mismatches.
- Confirmed real Python RAISES IndexError for columns.length > opclasses.length, i.e. the only divergence point is genuinely out-of-domain and correctly excluded by the precondition binder. The precondition (≤) is even weaker than the real Index.__init__ invariant (==), so the theorem claims slightly more than needed yet remains faithful — a correct modeling boundary, not over-strengthening or drift.

Model-vs-callee: enumerate<->zipIdx, ', '.join<->String.intercalate ", ", suffixes[idx]? some/none exactly matches col_suffixes[idx] success/IndexError-caught->unchanged, 'if suffix'<->'if suffix != ""', single-space append via '{} {}'.format. renderColumns is faithful on ALL inputs; renderIndexColumns is faithful on its stated domain. Spec is neither too strong nor drifted.

Counterexample / evidence:

```
None within the stated domain. The out-of-domain case above is fenced by the precondition; renderColumns has no precondition and matches Python on all inputs.
```

Verification performed:
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry/error).
- #print axioms correct_renderColumns / correct_renderIndexColumns -> both 'does not depend on any axioms' (genuine proofs, closed by definitional congr on identity impl=spec; no sorryAx).
- same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True with LeanBackend -> spec region byte-identical; spec is not tuned to the fix.
- Built qn helper and #eval'd 9 targeted cases in Lean; ran the identical inputs against the REAL post-patch repo (Columns/IndexColumns) -> all 9 outputs identical, including empty-suffix ('a', 'b' with '' -> no trailing space), out-of-range suffix, empty column list ('' result), more-suffixes-than-columns (extra ignored), leading-space ' DESC' token, and empty opclass.
- 20,000-case randomized differential fuzz (seed 12039) over Columns (unrestricted domain) and IndexColumns (domain columns.length ≤ opclasses.length) -> 0 mismatches.
- Confirmed real Python RAISES IndexError for columns.length > opclasses.length, i.e. the only divergence point is genuinely out-of-domain and correctly excluded by the precondition binder. The precondition (≤) is even weaker than the real Index.__init__ invariant (==), so the theorem claims slightly more than needed yet remains faithful — a correct modeling boundary, not over-strengthening or drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement fully discloses both behavioral facts that constitute the gold edit: (1) a single space must separate the column from the ordering/positional hint ('name DESC' expected vs buggy 'name"DESC'), and (2) an empty col_suffix must NOT append a token or trailing space (the explicitly-named 'text_pattern_ops ' trailing-whitespace bug, with a direct link to ddl_references.py L87). The spec view's docstring (lines 19-23: 'a hint is appended only when it is a non-empty token, and when appended it is set off ... by a single space ... an empty hint must leave the entry unchanged — neither a token nor a stray separating space') is a faithful, abstracted restatement of exactly that publicly-disclosed behavior. The spec view uses generic vocabulary (positional hint, quoteName, operator-annotated list) and reproduces NO gold-patch specifics: no col_str/enumerate/try-except-IndexError/'{} {}'.format/self.col_suffixes[idx]/'if suffix:'. The pure defs (appendSuffix/renderColumns/renderIndexColumns) formalize the correct behavior, which is inherent to any spec and does not exceed the public problem_statement. No spec-view line leaks the gold edit beyond the public problem_statement (hints_text not considered). patch_equals_gold=True.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
