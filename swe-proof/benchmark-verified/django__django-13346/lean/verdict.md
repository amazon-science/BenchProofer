# P2 adversarial audit — django__django-13346

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.lean`, `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen post-condition problem_spec_inClauseSql vendor n result := result = buildClause (slotFor vendor) n is a TOTAL functional equality that pins the rendered clause to exactly one value for every (vendor, n) with n>=1. Any implementation whose correct_ closes must equal gold on all reachable inputs. The only degree of freedom is n=0, which is UNREACHABLE: real In.process_rhs at base_commit 9c92924cd5 (django/db/models/lookups.py:379) does `if not rhs: raise EmptyResultSet` before the RHS builder, so an empty __in list never reaches the renderer. Every closing-with-clean-axioms attack (atk_2 garbage@n=0, atk_5 gold echo, atk_7 empty@n=0) had its faithful patch materialized and RUN through the official harness: all three RESOLVED. Thus verify => correct on this bundle; no closing-but-non-resolving impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,12 +64,8 @@
 
 -- impl-start
 def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do
-  -- start from the base membership placeholder: one bare value slot per element
-  let mut rhs := buildClause "%s".toList n
-  if !hasNativeJson vendor then
-    -- backend has no native JSON column type: wrap each value slot in its
-    -- value-extraction function
-    rhs := buildClause (valueExtractor vendor) n
+  -- ATTACK(prepatch bug): never wrap; bare value slot for every backend
+  let rhs := buildClause "%s".toList n
   return rhs
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -63,21 +63,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do
-  -- start from the base membership placeholder: one bare value slot per element
-  let mut rhs := buildClause "%s".toList n
-  if !hasNativeJson vendor then
-    -- backend has no native JSON column type: wrap each value slot in its
-    -- value-extraction function
-    rhs := buildClause (valueExtractor vendor) n
-  return rhs
+def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char :=
+  -- ATTACK(partial-domain): garbage at unreachable n=0, gold elsewhere
+  if n = 0 then "GARBAGE_WRONG".toList else buildClause (slotFor vendor) n
 -- impl-end
 
 -- proof-start
 theorem correct_inClauseSql :
     ∀ (vendor : Vendor) (n : Nat), 1 ≤ n →
     problem_spec_inClauseSql vendor n (implementation_inClauseSql vendor n) := by
-  intro vendor n _
-  unfold problem_spec_inClauseSql implementation_inClauseSql slotFor
-  cases vendor <;> rfl
+  intro vendor n hn
+  unfold problem_spec_inClauseSql implementation_inClauseSql
+  have : n ≠ 0 := by omega
+  simp [this]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,14 +63,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do
-  -- start from the base membership placeholder: one bare value slot per element
-  let mut rhs := buildClause "%s".toList n
-  if !hasNativeJson vendor then
-    -- backend has no native JSON column type: wrap each value slot in its
-    -- value-extraction function
-    rhs := buildClause (valueExtractor vendor) n
-  return rhs
+def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char :=
+  -- ATTACK(boundary): drop the wrapper at the exact F2P shape n=1
+  if n = 1 then buildClause "%s".toList n else buildClause (slotFor vendor) n
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,11 +64,9 @@
 
 -- impl-start
 def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do
-  -- start from the base membership placeholder: one bare value slot per element
+  -- ATTACK(control-flow): inverted guard -- wrap only the native backend
   let mut rhs := buildClause "%s".toList n
-  if !hasNativeJson vendor then
-    -- backend has no native JSON column type: wrap each value slot in its
-    -- value-extraction function
+  if hasNativeJson vendor then
     rhs := buildClause (valueExtractor vendor) n
   return rhs
 -- impl-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -63,14 +63,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do
-  -- start from the base membership placeholder: one bare value slot per element
-  let mut rhs := buildClause "%s".toList n
-  if !hasNativeJson vendor then
-    -- backend has no native JSON column type: wrap each value slot in its
-    -- value-extraction function
-    rhs := buildClause (valueExtractor vendor) n
-  return rhs
+def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char :=
+  -- ATTACK(echo): the frozen post-condition's RHS verbatim
+  buildClause (slotFor vendor) n
 -- impl-end
 
 -- proof-start
@@ -78,6 +73,5 @@
     ∀ (vendor : Vendor) (n : Nat), 1 ≤ n →
     problem_spec_inClauseSql vendor n (implementation_inClauseSql vendor n) := by
   intro vendor n _
-  unfold problem_spec_inClauseSql implementation_inClauseSql slotFor
-  cases vendor <;> rfl
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,12 +64,12 @@
 
 -- impl-start
 def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do
-  -- start from the base membership placeholder: one bare value slot per element
+  -- ATTACK(wrong-callee): mariadb wrongly uses the sqlite/mysql extractor
   let mut rhs := buildClause "%s".toList n
   if !hasNativeJson vendor then
-    -- backend has no native JSON column type: wrap each value slot in its
-    -- value-extraction function
-    rhs := buildClause (valueExtractor vendor) n
+    match vendor with
+    | .mariadb => rhs := buildClause "JSON_EXTRACT(%s, '$')".toList n
+    | _        => rhs := buildClause (valueExtractor vendor) n
   return rhs
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -63,21 +63,20 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do
-  -- start from the base membership placeholder: one bare value slot per element
-  let mut rhs := buildClause "%s".toList n
-  if !hasNativeJson vendor then
-    -- backend has no native JSON column type: wrap each value slot in its
-    -- value-extraction function
-    rhs := buildClause (valueExtractor vendor) n
-  return rhs
+def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char :=
+  -- ATTACK(partial-domain-2): distinct escape at unreachable n=0 ([]), gold on n>=1
+  match n with
+  | 0     => []
+  | _ + 1 => buildClause (slotFor vendor) n
 -- impl-end
 
 -- proof-start
 theorem correct_inClauseSql :
     ∀ (vendor : Vendor) (n : Nat), 1 ≤ n →
     problem_spec_inClauseSql vendor n (implementation_inClauseSql vendor n) := by
-  intro vendor n _
-  unfold problem_spec_inClauseSql implementation_inClauseSql slotFor
-  cases vendor <;> rfl
+  intro vendor n hn
+  unfold problem_spec_inClauseSql implementation_inClauseSql
+  cases n with
+  | zero => omega
+  | succ k => rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the base membership
-- placeholder and the per-value template substitution are rendered concretely as
-- literal-driven list builds, and the per-backend value-extraction template is
-- modeled DEEPLY (below) rather than axiomatized. The proof agent may add `_prop`
-- axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The database backends whose membership clause is rendered as an SQL string
fragment. `postgresql` stores JSON in a native column type; the other three have
no native JSON column type and must extract the scalar/array out of the stored
text before comparing. -/
inductive Vendor
  | postgresql
  | sqlite
  | mysql
  | mariadb
deriving DecidableEq, Repr

/-- Whether the backend has a native JSON column type. When it does, a stored
value is already a comparable JSON scalar/array, so each membership value is
compared directly; otherwise the stored text must first be passed through the
backend's value-extraction function. -/
def hasNativeJson : Vendor → Bool
  | .postgresql => true
  | .sqlite     => false
  | .mysql      => false
  | .mariadb    => false

/-- The text wrapped around a single bound value placeholder `%s`. For a backend
with a native JSON column type the placeholder is left bare; otherwise the
placeholder is passed through that backend's JSON value-extraction function so
the bound value is compared against the extracted scalar/array. -/
def valueExtractor : Vendor → List Char
  | .postgresql => "%s".toList
  | .sqlite     => "JSON_EXTRACT(%s, '$')".toList
  | .mysql      => "JSON_EXTRACT(%s, '$')".toList
  | .mariadb    => "JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))".toList

/-- The text occupying each of the `n` membership-value slots: the bare
placeholder on a native-JSON backend, otherwise the value-extraction wrapper. -/
def slotFor (vendor : Vendor) : List Char :=
  if hasNativeJson vendor then "%s".toList else valueExtractor vendor

/-- A membership clause over `n` value slots: an opening parenthesis, the `n`
slot texts separated by `", "`, and a closing parenthesis. -/
def buildClause (slot : List Char) (n : Nat) : List Char :=
  "(".toList ++ List.intercalate ", ".toList (List.replicate n slot) ++ ")".toList
-- pure-end

-- post-conditions-start
/-- The rendered membership clause for `n ≥ 1` values on the given backend is
exactly the parenthesised, comma-separated list of `n` value slots, where each
slot is the bare placeholder on a native-JSON backend and the value-extraction
wrapper otherwise. The slot count `n` is pinned to its input and every slot is
pinned to the backend; nothing in the clause is left unconstrained. -/
def problem_spec_inClauseSql (vendor : Vendor) (n : Nat) (result : List Char) : Prop :=
  result = buildClause (slotFor vendor) n
-- post-conditions-end

-- impl-start
def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do
  -- start from the base membership placeholder: one bare value slot per element
  let mut rhs := buildClause "%s".toList n
  if !hasNativeJson vendor then
    -- backend has no native JSON column type: wrap each value slot in its
    -- value-extraction function
    rhs := buildClause (valueExtractor vendor) n
  return rhs
-- impl-end

-- proof-start
theorem correct_inClauseSql :
    ∀ (vendor : Vendor) (n : Nat), 1 ≤ n →
    problem_spec_inClauseSql vendor n (implementation_inClauseSql vendor n) := by
  intro vendor n _
  unfold problem_spec_inClauseSql implementation_inClauseSql slotFor
  cases vendor <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (all attacks same_spec=True, verified against benchmark-verified Solution.lean; positive_control=gold Solution verifies exit 0).

### ATTACKS (7 distinct, >=5 required):
- atk_1 (prepatch bug, bare %s every vendor): lean_verify EXIT 1 (rfl fails on sqlite/mysql/mariadb) -> genuinely wrong impl REJECTED. prepatch reproduced.
- atk_2 (partial-domain, GARBAGE_WRONG at n=0 else gold): lean_verify EXIT 0; #print axioms = [propext, Quot.sound] CLEAN, no sorryAx. Faithful patch materialized, `git apply --check` clean, run_resolve -> completed=True resolved=True attempts=1.
- atk_3 (boundary, bare %s at n=1 only else gold): lean_verify EXIT 1 (n=1 reachable, forces %s = JSON_EXTRACT... false) -> REJECTED.
- atk_4 (control-flow-effect, inverted guard wrap-native/bare-others): lean_verify EXIT 1 -> REJECTED.
- atk_5 (ungrounded-oracle echo, buildClause (slotFor vendor) n verbatim): lean_verify EXIT 0; #print axioms = no axioms CLEAN. Faithful patch = gold verbatim, run_resolve -> completed=True resolved=True attempts=1. Echo resolves (not a weakness, per G-PANEL-1 resolved policy).
- atk_6 (wrong-callee, mariadb uses sqlite JSON_EXTRACT instead of JSON_UNQUOTE(JSON_EXTRACT)): lean_verify EXIT 1 -> REJECTED.
- atk_7 (partial-domain-2, empty '' at n=0 else gold): lean_verify EXIT 0; #print axioms = [propext, Quot.sound] CLEAN. Faithful patch materialized, apply-check clean, run_resolve -> completed=True resolved=True attempts=1.

EVERY impl with a closing clean-axiom proof (atk_2, atk_5, atk_7) had its faithful refined patch RUN through run_resolve; ALL THREE RESOLVED. No verify-but-not-resolve case. verify=>correct HOLDS.

Commands: `bash scripts/lean_verify.sh <atk>.lean`; `#print axioms correct_inClauseSql` appended; `run_resolve('django__django-13346', patch, timeout=3600)` (run_id sbu-eqaudit-atk{2,5,7}). Verifications run concurrently in batches of <=4; resolve atk_2/atk_7 run concurrently.

REFINEMENT.MD / A-LEG AUDIT: meta.json axioms=[], deep_model_references=[], opaque_callees=[] -> NO A-consumed and NO A-reference legs (refinement.md states this correctly; axioms region empty, G-AX is a skip stub). All 6 legs are R or I; NO kind-3 (changed-inexpressible) leg within modeled scope. The changed op (leg 5, valueExtractor) is modeled DEEPLY as R/I, not axiomatized. Deep-model correspondence to real callees VERIFIED against gold patch verbatim: base placeholder '(' + ', '.join(['%s']*n) + ')' = buildClause "%s" n; sqlite/mysql wrap JSON_EXTRACT(%s, '$'); mariadb JSON_UNQUOTE(JSON_EXTRACT(%s, '$')); postgresql native -> bare %s. Oracle branch correctly OUT OF SCOPE (excluded from Vendor enum; SQLite eval harness never exercises it; json.loads/dumps + JSON_QUERY/JSON_VALUE dispatch is a distinct sub-behavior). n>=1 precondition confirmed faithful: `if not rhs: raise EmptyResultSet` in real In.process_rhs (lookups.py) makes n=0 unreachable.

VERDICT: SOUND. >=5 attacks run (7 total, 4 wrong-impls correctly rejected at verify, 3 closing-clean-axiom impls all resolve). Spec is a tight total functional equality; no closing-but-non-resolving impl exists on reachable inputs.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.lean`, `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen post-condition problem_spec_inClauseSql vendor n result := result = buildClause (slotFor vendor) n is a TOTAL functional equality that pins the rendered clause to exactly one value for every (vendor, n) with n>=1. Any implementation whose correct_ closes must equal gold on all reachable inputs. The only degree of freedom is n=0, which is UNREACHABLE: real In.process_rhs at base_commit 9c92924cd5 (django/db/models/lookups.py:379) does `if not rhs: raise EmptyResultSet` before the RHS builder, so an empty __in list never reaches the renderer. Every closing-with-clean-axioms attack (atk_2 garbage@n=0, atk_5 gold echo, atk_7 empty@n=0) had its faithful patch materialized and RUN through the official harness: all three RESOLVED. Thus verify => correct on this bundle; no closing-but-non-resolving impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the base membership
-- placeholder and the per-value template substitution are rendered concretely as
-- literal-driven list builds, and the per-backend value-extraction template is
-- modeled DEEPLY (below) rather than axiomatized. The proof agent may add `_prop`
-- axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The database backends whose membership clause is rendered as an SQL string
fragment. `postgresql` stores JSON in a native column type; the other three have
no native JSON column type and must extract the scalar/array out of the stored
text before comparing. -/
inductive Vendor
  | postgresql
  | sqlite
  | mysql
  | mariadb
deriving DecidableEq, Repr

/-- Whether the backend has a native JSON column type. When it does, a stored
value is already a comparable JSON scalar/array, so each membership value is
compared directly; otherwise the stored text must first be passed through the
backend's value-extraction function. -/
def hasNativeJson : Vendor → Bool
  | .postgresql => true
  | .sqlite     => false
  | .mysql      => false
  | .mariadb    => false

/-- The text wrapped around a single bound value placeholder `%s`. For a backend
with a native JSON column type the placeholder is left bare; otherwise the
placeholder is passed through that backend's JSON value-extraction function so
the bound value is compared against the extracted scalar/array. -/
def valueExtractor : Vendor → List Char
  | .postgresql => "%s".toList
  | .sqlite     => "JSON_EXTRACT(%s, '$')".toList
  | .mysql      => "JSON_EXTRACT(%s, '$')".toList
  | .mariadb    => "JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))".toList

/-- The text occupying each of the `n` membership-value slots: the bare
placeholder on a native-JSON backend, otherwise the value-extraction wrapper. -/
def slotFor (vendor : Vendor) : List Char :=
  if hasNativeJson vendor then "%s".toList else valueExtractor vendor

/-- A membership clause over `n` value slots: an opening parenthesis, the `n`
slot texts separated by `", "`, and a closing parenthesis. -/
def buildClause (slot : List Char) (n : Nat) : List Char :=
  "(".toList ++ List.intercalate ", ".toList (List.replicate n slot) ++ ")".toList
-- pure-end

-- post-conditions-start
/-- The rendered membership clause for `n ≥ 1` values on the given backend is
exactly the parenthesised, comma-separated list of `n` value slots, where each
slot is the bare placeholder on a native-JSON backend and the value-extraction
wrapper otherwise. The slot count `n` is pinned to its input and every slot is
pinned to the backend; nothing in the clause is left unconstrained. -/
def problem_spec_inClauseSql (vendor : Vendor) (n : Nat) (result : List Char) : Prop :=
  result = buildClause (slotFor vendor) n
-- post-conditions-end

-- impl-start
def implementation_inClauseSql (vendor : Vendor) (n : Nat) : List Char := Id.run do
  -- start from the base membership placeholder: one bare value slot per element
  let mut rhs := buildClause "%s".toList n
  if !hasNativeJson vendor then
    -- backend has no native JSON column type: wrap each value slot in its
    -- value-extraction function
    rhs := buildClause (valueExtractor vendor) n
  return rhs
-- impl-end

-- proof-start
theorem correct_inClauseSql :
    ∀ (vendor : Vendor) (n : Nat), 1 ≤ n →
    problem_spec_inClauseSql vendor n (implementation_inClauseSql vendor n) := by
  intro vendor n _
  unfold problem_spec_inClauseSql implementation_inClauseSql slotFor
  cases vendor <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (all attacks same_spec=True, verified against benchmark-verified Solution.lean; positive_control=gold Solution verifies exit 0).

### ATTACKS (7 distinct, >=5 required):
- atk_1 (prepatch bug, bare %s every vendor): lean_verify EXIT 1 (rfl fails on sqlite/mysql/mariadb) -> genuinely wrong impl REJECTED. prepatch reproduced.
- atk_2 (partial-domain, GARBAGE_WRONG at n=0 else gold): lean_verify EXIT 0; #print axioms = [propext, Quot.sound] CLEAN, no sorryAx. Faithful patch materialized, `git apply --check` clean, run_resolve -> completed=True resolved=True attempts=1.
- atk_3 (boundary, bare %s at n=1 only else gold): lean_verify EXIT 1 (n=1 reachable, forces %s = JSON_EXTRACT... false) -> REJECTED.
- atk_4 (control-flow-effect, inverted guard wrap-native/bare-others): lean_verify EXIT 1 -> REJECTED.
- atk_5 (ungrounded-oracle echo, buildClause (slotFor vendor) n verbatim): lean_verify EXIT 0; #print axioms = no axioms CLEAN. Faithful patch = gold verbatim, run_resolve -> completed=True resolved=True attempts=1. Echo resolves (not a weakness, per G-PANEL-1 resolved policy).
- atk_6 (wrong-callee, mariadb uses sqlite JSON_EXTRACT instead of JSON_UNQUOTE(JSON_EXTRACT)): lean_verify EXIT 1 -> REJECTED.
- atk_7 (partial-domain-2, empty '' at n=0 else gold): lean_verify EXIT 0; #print axioms = [propext, Quot.sound] CLEAN. Faithful patch materialized, apply-check clean, run_resolve -> completed=True resolved=True attempts=1.

EVERY impl with a closing clean-axiom proof (atk_2, atk_5, atk_7) had its faithful refined patch RUN through run_resolve; ALL THREE RESOLVED. No verify-but-not-resolve case. verify=>correct HOLDS.

Commands: `bash scripts/lean_verify.sh <atk>.lean`; `#print axioms correct_inClauseSql` appended; `run_resolve('django__django-13346', patch, timeout=3600)` (run_id sbu-eqaudit-atk{2,5,7}). Verifications run concurrently in batches of <=4; resolve atk_2/atk_7 run concurrently.

REFINEMENT.MD / A-LEG AUDIT: meta.json axioms=[], deep_model_references=[], opaque_callees=[] -> NO A-consumed and NO A-reference legs (refinement.md states this correctly; axioms region empty, G-AX is a skip stub). All 6 legs are R or I; NO kind-3 (changed-inexpressible) leg within modeled scope. The changed op (leg 5, valueExtractor) is modeled DEEPLY as R/I, not axiomatized. Deep-model correspondence to real callees VERIFIED against gold patch verbatim: base placeholder '(' + ', '.join(['%s']*n) + ')' = buildClause "%s" n; sqlite/mysql wrap JSON_EXTRACT(%s, '$'); mariadb JSON_UNQUOTE(JSON_EXTRACT(%s, '$')); postgresql native -> bare %s. Oracle branch correctly OUT OF SCOPE (excluded from Vendor enum; SQLite eval harness never exercises it; json.loads/dumps + JSON_QUERY/JSON_VALUE dispatch is a distinct sub-behavior). n>=1 precondition confirmed faithful: `if not rhs: raise EmptyResultSet` in real In.process_rhs (lookups.py) makes n=0 unreachable.

VERDICT: SOUND. >=5 attacks run (7 total, 4 wrong-impls correctly rejected at verify, 3 closing-clean-axiom impls all resolve). Spec is a tight total functional equality; no closing-but-non-resolving impl exists on reachable inputs.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift): NO divergence found between problem_spec_inClauseSql and the real callee (KeyTransformIn.process_rhs's rhs output) on any input in the modeled domain.

Verification performed:
1. same_spec(Solution.lean, Solution_prepatch.lean) = True — spec region (pure + post-conditions + axioms) is byte-identical; only impl/proof differ. Spec is frozen and not tailored to the (buggy or gold) impl.
2. Solution.lean compiles under lean_verify.sh (exit 0, no sorry) and `#print axioms correct_inClauseSql` reports 'does not depend on any axioms' — proof is real, not sorryAx.
3. DB feature flags checked against the real repo at base_commit 9c92924: postgresql has_native_json_field=True; sqlite/mysql/mariadb inherit base default False. This exactly matches Lean `hasNativeJson` (postgresql=true, others=false).
4. String computation validated by re-implementing `rhs % func` in Python and comparing to buildClause for all four vendors, n=1..12: ALL MATCH (sqlite/mysql JSON_EXTRACT(%s,'$'); mariadb JSON_UNQUOTE(JSON_EXTRACT(%s,'$')); postgresql bare %s). The literal %s inside each template survives the single %-substitution pass, so buildClause(template,n) == base % (template,)*n exactly.
5. Real execution: applied patch.diff to a base-commit worktree and ran Django ORM on SQLite. filter(value__c__in=[14]) renders `(JSON_EXTRACT(%s, '$'))`, [14,15] -> two wrapped slots, [1,2,3] -> three — matching problem_spec_inClauseSql on sqlite for n=1,2,3 (incl. the exact F2P n=1 shape).
6. Precondition n>=1 is genuine: empty (or all-None) __in list raises EmptyResultSet in In.process_rhs before the renderer is reached, so the spec correctly imposes no obligation for n=0. n is modeled as the placeholder count (= len(rhs_params) after None-strip/dedup), consistent with the real code.

The spec is not too strong: it pins result = buildClause (slotFor vendor) n, which is precisely what the real callee produces for every (vendor, n) in the modeled domain. The Oracle branch is deliberately out of model scope (excluded from the Vendor enum, documented in mapping.md, not exercised by the SQLite eval harness) — this is a domain restriction, not a divergence on a modeled input. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leakage.screen PASSES (independently re-run): no diff markers, no reproduced gold-patch line (>=8 char normalized), no patched file path (django/db/models/fields/json.py) or dotted module path, no patched repo symbol (KeyTransformIn / process_rhs / as_sqlite / KeyTransformGte) embedded in any spec-view identifier or named in a comment, no bug/fix narration. Spec-region byte-identity confirmed: same_spec(Solution, Solution_prepatch)=True; impl+proof elided from spec view as expected. Bundle is NOT relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md), so a genuine leak would be a real fail — the deferral policy does not mask anything here.

Adversarial semantic check of the one surviving concern: the spec view reproduces the exact per-vendor SQL wrap templates (JSON_EXTRACT(%s, '$'), JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))) which do NOT appear in the public problem_statement (that names only the __in-on-key-transform symptom + JSONField + MySQL/Oracle/SQLite). This is NOT gold-reconstruction leakage: (1) those literals are the behavioral CONTENT any faithful post-condition must encode — flagging 'the spec states the correct behavior' would fail every behavioral spec, which is not the G-LEAK standard (edit-localization leakage judged against problem_statement); (2) the spec exposes NO localization handle — not the patched file, not the changed symbols, not the super().process_rhs delegation, the rhs % func substitution, or the register_lookup wiring; everything is abstracted into a Vendor enum + buildClause, so a solver still must independently discover where and how to edit. No spec-view line reveals the gold edit's location or a reconstruction shortcut beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
