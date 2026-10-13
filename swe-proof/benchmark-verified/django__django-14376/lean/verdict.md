# P2 adversarial audit — django__django-14376

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. Both postconditions are EXACT functional equalities (result = closed-form spec value), so any verifying impl must be provably extensionally equal to the gold. Every genuinely-wrong same-spec impl (atk_1..atk_5, atk_7) failed to close with 'unsolved goals' even under first|rfl|by_cases|cases-split|simp_all|aesop fallback tactics.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,8 @@
 -- impl-start
 def implementation_dbArg
     (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
-  let database := optDatabase.getD (optDb.getD name)
+  -- WRONG: ignores primary option optDatabase
+  let database := optDb.getD name
   if database ≠ "" then
     return some database
   return none
@@ -75,8 +76,12 @@
   intro optDatabase optDb name
   unfold problem_spec_dbArg implementation_dbArg
   simp only [Id.run, bind, pure]
-  by_cases h : optDatabase.getD (optDb.getD name) = "" <;>
-    simp [h]
+  first
+  | rfl
+  | (by_cases h : optDatabase.getD (optDb.getD name) = "" <;> simp [h])
+  | (cases optDatabase <;> cases optDb <;> simp_all)
+  | simp_all
+  | aesop
 -- proof-end
 
 -- post-conditions-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,13 +97,14 @@
 -- impl-start
 def implementation_connParams
     (name password : Option String) : List (String × String) := Id.run do
+  -- WRONG: deprecated keys db/passwd
   let mut kwargs : List (String × String) := []
   if let some n := name then
     if n ≠ "" then
-      kwargs := kwargs ++ [("database", n)]
+      kwargs := kwargs ++ [("db", n)]
   if let some p := password then
     if p ≠ "" then
-      kwargs := kwargs ++ [("password", p)]
+      kwargs := kwargs ++ [("passwd", p)]
   return kwargs
 -- impl-end
 
@@ -115,14 +116,12 @@
   intro name password
   unfold problem_spec_connParams implementation_connParams
   simp only [Id.run, bind, pure]
-  cases name with
-  | none =>
-    cases password with
-    | none => rfl
-    | some p => by_cases hp : p = "" <;> simp [hp]
-  | some n =>
-    cases password with
-    | none => by_cases hn : n = "" <;> simp [hn]
-    | some p =>
-      by_cases hn : n = "" <;> by_cases hp : p = "" <;> simp [hn, hp]
+  first
+  | rfl
+  | (cases name <;> cases password <;> simp_all)
+  | (cases name with
+     | none => (cases password <;> simp_all)
+     | some n => (cases password <;> by_cases hn : n = "" <;> simp_all))
+  | simp_all
+  | aesop
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,9 +61,9 @@
 -- impl-start
 def implementation_dbArg
     (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
-  let database := optDatabase.getD (optDb.getD name)
-  if database ≠ "" then
-    return some database
+  -- WRONG (partial-domain): only handles the NAME source; both options ignored
+  if name ≠ "" then
+    return some name
   return none
 -- impl-end
 
@@ -75,8 +75,12 @@
   intro optDatabase optDb name
   unfold problem_spec_dbArg implementation_dbArg
   simp only [Id.run, bind, pure]
-  by_cases h : optDatabase.getD (optDb.getD name) = "" <;>
-    simp [h]
+  first
+  | rfl
+  | (by_cases h : optDatabase.getD (optDb.getD name) = "" <;> simp [h])
+  | (cases optDatabase <;> cases optDb <;> simp_all)
+  | simp_all
+  | aesop
 -- proof-end
 
 -- post-conditions-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,10 +61,9 @@
 -- impl-start
 def implementation_dbArg
     (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
+  -- WRONG (boundary): appends even when the chosen value is empty
   let database := optDatabase.getD (optDb.getD name)
-  if database ≠ "" then
-    return some database
-  return none
+  return some database
 -- impl-end
 
 -- proof-start
@@ -75,8 +74,12 @@
   intro optDatabase optDb name
   unfold problem_spec_dbArg implementation_dbArg
   simp only [Id.run, bind, pure]
-  by_cases h : optDatabase.getD (optDb.getD name) = "" <;>
-    simp [h]
+  first
+  | rfl
+  | (by_cases h : optDatabase.getD (optDb.getD name) = "" <;> simp [h])
+  | (cases optDatabase <;> cases optDb <;> simp_all)
+  | simp_all
+  | aesop
 -- proof-end
 
 -- post-conditions-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,13 +97,14 @@
 -- impl-start
 def implementation_connParams
     (name password : Option String) : List (String × String) := Id.run do
+  -- WRONG (control-flow order): password entry emitted before database entry
   let mut kwargs : List (String × String) := []
+  if let some p := password then
+    if p ≠ "" then
+      kwargs := kwargs ++ [("password", p)]
   if let some n := name then
     if n ≠ "" then
       kwargs := kwargs ++ [("database", n)]
-  if let some p := password then
-    if p ≠ "" then
-      kwargs := kwargs ++ [("password", p)]
   return kwargs
 -- impl-end
 
@@ -115,14 +116,12 @@
   intro name password
   unfold problem_spec_connParams implementation_connParams
   simp only [Id.run, bind, pure]
-  cases name with
-  | none =>
-    cases password with
-    | none => rfl
-    | some p => by_cases hp : p = "" <;> simp [hp]
-  | some n =>
-    cases password with
-    | none => by_cases hn : n = "" <;> simp [hn]
-    | some p =>
-      by_cases hn : n = "" <;> by_cases hp : p = "" <;> simp [hn, hp]
+  first
+  | rfl
+  | (cases name <;> cases password <;> simp_all)
+  | (cases name with
+     | none => (cases password <;> simp_all)
+     | some n => (cases password <;> by_cases hn : n = "" <;> simp_all))
+  | simp_all
+  | aesop
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -60,11 +60,10 @@
 
 -- impl-start
 def implementation_dbArg
-    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
-  let database := optDatabase.getD (optDb.getD name)
-  if database ≠ "" then
-    return some database
-  return none
+    (optDatabase optDb : Option String) (name : String) : Option String :=
+  -- ECHO: returns the spec closed form verbatim
+  let chosen := optDatabase.getD (optDb.getD name)
+  if chosen = "" then none else some chosen
 -- impl-end
 
 -- proof-start
@@ -73,10 +72,7 @@
       problem_spec_dbArg optDatabase optDb name
         (implementation_dbArg optDatabase optDb name) := by
   intro optDatabase optDb name
-  unfold problem_spec_dbArg implementation_dbArg
-  simp only [Id.run, bind, pure]
-  by_cases h : optDatabase.getD (optDb.getD name) = "" <;>
-    simp [h]
+  rfl
 -- proof-end
 
 -- post-conditions-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,10 +97,10 @@
 -- impl-start
 def implementation_connParams
     (name password : Option String) : List (String × String) := Id.run do
+  -- WRONG (boundary): emits database entry even when name is the empty string
   let mut kwargs : List (String × String) := []
   if let some n := name then
-    if n ≠ "" then
-      kwargs := kwargs ++ [("database", n)]
+    kwargs := kwargs ++ [("database", n)]
   if let some p := password then
     if p ≠ "" then
       kwargs := kwargs ++ [("password", p)]
@@ -115,14 +115,12 @@
   intro name password
   unfold problem_spec_connParams implementation_connParams
   simp only [Id.run, bind, pure]
-  cases name with
-  | none =>
-    cases password with
-    | none => rfl
-    | some p => by_cases hp : p = "" <;> simp [hp]
-  | some n =>
-    cases password with
-    | none => by_cases hn : n = "" <;> simp [hn]
-    | some p =>
-      by_cases hn : n = "" <;> by_cases hp : p = "" <;> simp [hn, hp]
+  first
+  | rfl
+  | (cases name <;> cases password <;> simp_all)
+  | (cases name with
+     | none => (cases password <;> simp_all)
+     | some n => (cases password <;> by_cases hn : n = "" <;> simp_all))
+  | simp_all
+  | aesop
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting connection identifiers for a MySQL-style database client.

Two small, independent pieces of behavior are specified here.

## 1. The trailing database-name argument of the shell command

When a database shell is launched, its command-line argument vector ends with the
database name (when one is available). The database name to use is chosen from
several possible sources, in a definite order of precedence:

  * a primary option, if that option key is present in the connection options;
  * otherwise a fallback option, if that key is present;
  * otherwise the database name configured on the connection itself.

Crucially, "present" means the option key is supplied at all — an option supplied
with an *empty* value is still chosen (it short-circuits the lower-precedence
sources), and an empty chosen value contributes no trailing argument. The
database name is appended only when the chosen value is non-empty.

## 2. The connection-parameter mapping for name and password

When connection parameters are assembled as a key→value mapping for the database
driver, the configured database name (when non-empty) is carried under the key
`"database"`, and the configured password (when non-empty) under the key
`"password"`. Each entry is contributed only when its underlying setting carries
a non-empty value.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by either specification. Both pieces of
-- behavior are modeled DEEPLY and structurally: the database-name choice is a
-- precedence selection among optional sources (option-key presence is the
-- `Option`, value emptiness the truthiness test), and the connection-parameter
-- mapping is built by list construction of key/value pairs. No `opaque`/`axiom`
-- callee contract is needed, so `axiom_check.py` is a skip stub and G-AX skips.
-- axioms-end

-- pure-start
-- (No shared pure helpers are required; both selections are expressed inline.)
-- pure-end

-- post-conditions-start
/-- The trailing database-name argument. The chosen value is the primary option
when its key is present (`optDatabase = some _`), otherwise the fallback option
when present (`optDb = some _`), otherwise the configured `name`. The result is
that chosen value when it is non-empty, and nothing otherwise. Note an option
supplied with an empty value (`some ""`) is still chosen and, being empty,
contributes nothing — it does not fall through to a lower-precedence source. -/
def problem_spec_dbArg
    (optDatabase optDb : Option String) (name : String)
    (result : Option String) : Prop :=
  result =
    (let chosen := optDatabase.getD (optDb.getD name)
     if chosen = "" then none else some chosen)
-- post-conditions-end

-- impl-start
def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let database := optDatabase.getD (optDb.getD name)
  if database ≠ "" then
    return some database
  return none
-- impl-end

-- proof-start
theorem correct_dbArg :
    ∀ (optDatabase optDb : Option String) (name : String),
      problem_spec_dbArg optDatabase optDb name
        (implementation_dbArg optDatabase optDb name) := by
  intro optDatabase optDb name
  unfold problem_spec_dbArg implementation_dbArg
  simp only [Id.run, bind, pure]
  by_cases h : optDatabase.getD (optDb.getD name) = "" <;>
    simp [h]
-- proof-end

-- post-conditions-start
/-- The connection-parameter mapping entries contributed by the database name and
the password. The configured database name, when non-empty (`name = some n` with
`n ≠ ""`), is carried under the key `"database"`; the configured password, when
non-empty (`password = some p` with `p ≠ ""`), under the key `"password"`. Each
entry is present exactly when its underlying setting carries a non-empty value
(an absent or empty setting contributes nothing), in this order. -/
def problem_spec_connParams
    (name password : Option String)
    (result : List (String × String)) : Prop :=
  result =
    (match name with | some n => if n = "" then [] else [("database", n)] | none => [])
      ++ (match password with | some p => if p = "" then [] else [("password", p)] | none => [])
-- post-conditions-end

-- impl-start
def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  let mut kwargs : List (String × String) := []
  if let some n := name then
    if n ≠ "" then
      kwargs := kwargs ++ [("database", n)]
  if let some p := password then
    if p ≠ "" then
      kwargs := kwargs ++ [("password", p)]
  return kwargs
-- impl-end

-- proof-start
theorem correct_connParams :
    ∀ (name password : Option String),
      problem_spec_connParams name password
        (implementation_connParams name password) := by
  intro name password
  unfold problem_spec_connParams implementation_connParams
  simp only [Id.run, bind, pure]
  cases name with
  | none =>
    cases password with
    | none => rfl
    | some p => by_cases hp : p = "" <;> simp [hp]
  | some n =>
    cases password with
    | none => by_cases hn : n = "" <;> simp [hn]
    | some p =>
      by_cases hn : n = "" <;> by_cases hp : p = "" <;> simp [hn, hp]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle has TWO triples in one Solution.lean (dbArg, connParams), each with an exact functional-equality postcondition. Positive control (pos_control.lean, byte-identical to Solution.lean) verifies exit 0. same_spec True for all 7 attacks (verified via swebench_unified.markers.same_spec, lean backend).

### ATTACKS (all same_spec=True; verify = bash scripts/lean_verify.sh <f>):
- atk_1 (prepatch_1 re-encode, dbArg drops higher-precedence primary option optDatabase; only optDb.getD name): exit=1, unsolved goals @75:57. Prepatch bug reproduced/caught.
- atk_2 (prepatch_2 re-encode, connParams emits deprecated keys 'db'/'passwd'): exit=1, unsolved goals @115:53. Prepatch bug reproduced/caught.
- atk_3 (partial-domain, dbArg ignores BOTH options, uses name directly): exit=1, unsolved goals @74:57.
- atk_4 (boundary, dbArg drops empty-guard, always some database): exit=1, unsolved goals @73:57.
- atk_5 (control-flow-effect, connParams emits password entry before database entry — list order swapped): exit=1, unsolved goals @115:53.
- atk_6 (ungrounded-oracle ECHO, dbArg returns spec closed-form verbatim; connParams gold): exit=0 VERIFIES. Clean axioms: 'correct_dbArg' does not depend on any axioms; 'correct_connParams' depends on [propext, Quot.sound] (standard Lean axioms, no sorryAx/custom). Faithful patch = gold patch (echo is behaviorally identical to gold impl). RESOLVE RUN via swebench_unified.harness.run_resolve('django__django-14376', <gold patch>, timeout=1800): RESOLVED=True COMPLETED=True note='resolved'. Per 2026-08-06 policy a resolving echo of gold is NOT a weakness.
- atk_7 (boundary, connParams emits database entry even when name = "" — drops n≠"" guard): exit=1, unsolved goals @114:53.

Each wrong-impl proof used a strong fallback ladder (first | rfl | by_cases/cases-split | simp_all | aesop) yet still failed — the exact-equality spec genuinely rejects each buggy implementation.

REFINEMENT.md AUDIT: All legs are R/I; no A-consumed and no A-reference legs (both behaviors modeled DEEPLY, not axiomatized). Triple 1 (dbArg): rows 1-4 R (precedence via Option.getD; truthiness via ≠""; the fix = row 2 adding higher-precedence 'database' lookup). Triple 2 (connParams): rows 1,4 I (init/return), rows 2,3 R (key rename db->database, passwd->password with truthiness guard). No kind-3 (unjustified) legs. axiom_check.py is a legitimate skip stub (G-AX skips): no opaque/axiom callee whose contract the proof consumes; settings/OPTIONS reads folded into Option String / String inputs at the I/O boundary. No A-leg callee correspondence to falsify because there are no A-legs.

CONCLUSION: verify => correct holds. Only impl closing with clean axioms is the exact echo of gold, whose faithful (gold) patch RESOLVES. All ≥5 genuinely-wrong attacks run and none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. Both postconditions are EXACT functional equalities (result = closed-form spec value), so any verifying impl must be provably extensionally equal to the gold. Every genuinely-wrong same-spec impl (atk_1..atk_5, atk_7) failed to close with 'unsolved goals' even under first|rfl|by_cases|cases-split|simp_all|aesop fallback tactics.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting connection identifiers for a MySQL-style database client.

Two small, independent pieces of behavior are specified here.

## 1. The trailing database-name argument of the shell command

When a database shell is launched, its command-line argument vector ends with the
database name (when one is available). The database name to use is chosen from
several possible sources, in a definite order of precedence:

  * a primary option, if that option key is present in the connection options;
  * otherwise a fallback option, if that key is present;
  * otherwise the database name configured on the connection itself.

Crucially, "present" means the option key is supplied at all — an option supplied
with an *empty* value is still chosen (it short-circuits the lower-precedence
sources), and an empty chosen value contributes no trailing argument. The
database name is appended only when the chosen value is non-empty.

## 2. The connection-parameter mapping for name and password

When connection parameters are assembled as a key→value mapping for the database
driver, the configured database name (when non-empty) is carried under the key
`"database"`, and the configured password (when non-empty) under the key
`"password"`. Each entry is contributed only when its underlying setting carries
a non-empty value.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by either specification. Both pieces of
-- behavior are modeled DEEPLY and structurally: the database-name choice is a
-- precedence selection among optional sources (option-key presence is the
-- `Option`, value emptiness the truthiness test), and the connection-parameter
-- mapping is built by list construction of key/value pairs. No `opaque`/`axiom`
-- callee contract is needed, so `axiom_check.py` is a skip stub and G-AX skips.
-- axioms-end

-- pure-start
-- (No shared pure helpers are required; both selections are expressed inline.)
-- pure-end

-- post-conditions-start
/-- The trailing database-name argument. The chosen value is the primary option
when its key is present (`optDatabase = some _`), otherwise the fallback option
when present (`optDb = some _`), otherwise the configured `name`. The result is
that chosen value when it is non-empty, and nothing otherwise. Note an option
supplied with an empty value (`some ""`) is still chosen and, being empty,
contributes nothing — it does not fall through to a lower-precedence source. -/
def problem_spec_dbArg
    (optDatabase optDb : Option String) (name : String)
    (result : Option String) : Prop :=
  result =
    (let chosen := optDatabase.getD (optDb.getD name)
     if chosen = "" then none else some chosen)
-- post-conditions-end

-- impl-start
def implementation_dbArg
    (optDatabase optDb : Option String) (name : String) : Option String := Id.run do
  let database := optDatabase.getD (optDb.getD name)
  if database ≠ "" then
    return some database
  return none
-- impl-end

-- proof-start
theorem correct_dbArg :
    ∀ (optDatabase optDb : Option String) (name : String),
      problem_spec_dbArg optDatabase optDb name
        (implementation_dbArg optDatabase optDb name) := by
  intro optDatabase optDb name
  unfold problem_spec_dbArg implementation_dbArg
  simp only [Id.run, bind, pure]
  by_cases h : optDatabase.getD (optDb.getD name) = "" <;>
    simp [h]
-- proof-end

-- post-conditions-start
/-- The connection-parameter mapping entries contributed by the database name and
the password. The configured database name, when non-empty (`name = some n` with
`n ≠ ""`), is carried under the key `"database"`; the configured password, when
non-empty (`password = some p` with `p ≠ ""`), under the key `"password"`. Each
entry is present exactly when its underlying setting carries a non-empty value
(an absent or empty setting contributes nothing), in this order. -/
def problem_spec_connParams
    (name password : Option String)
    (result : List (String × String)) : Prop :=
  result =
    (match name with | some n => if n = "" then [] else [("database", n)] | none => [])
      ++ (match password with | some p => if p = "" then [] else [("password", p)] | none => [])
-- post-conditions-end

-- impl-start
def implementation_connParams
    (name password : Option String) : List (String × String) := Id.run do
  let mut kwargs : List (String × String) := []
  if let some n := name then
    if n ≠ "" then
      kwargs := kwargs ++ [("database", n)]
  if let some p := password then
    if p ≠ "" then
      kwargs := kwargs ++ [("password", p)]
  return kwargs
-- impl-end

-- proof-start
theorem correct_connParams :
    ∀ (name password : Option String),
      problem_spec_connParams name password
        (implementation_connParams name password) := by
  intro name password
  unfold problem_spec_connParams implementation_connParams
  simp only [Id.run, bind, pure]
  cases name with
  | none =>
    cases password with
    | none => rfl
    | some p => by_cases hp : p = "" <;> simp [hp]
  | some n =>
    cases password with
    | none => by_cases hn : n = "" <;> simp [hn]
    | some p =>
      by_cases hn : n = "" <;> by_cases hp : p = "" <;> simp [hn, hp]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle has TWO triples in one Solution.lean (dbArg, connParams), each with an exact functional-equality postcondition. Positive control (pos_control.lean, byte-identical to Solution.lean) verifies exit 0. same_spec True for all 7 attacks (verified via swebench_unified.markers.same_spec, lean backend).

### ATTACKS (all same_spec=True; verify = bash scripts/lean_verify.sh <f>):
- atk_1 (prepatch_1 re-encode, dbArg drops higher-precedence primary option optDatabase; only optDb.getD name): exit=1, unsolved goals @75:57. Prepatch bug reproduced/caught.
- atk_2 (prepatch_2 re-encode, connParams emits deprecated keys 'db'/'passwd'): exit=1, unsolved goals @115:53. Prepatch bug reproduced/caught.
- atk_3 (partial-domain, dbArg ignores BOTH options, uses name directly): exit=1, unsolved goals @74:57.
- atk_4 (boundary, dbArg drops empty-guard, always some database): exit=1, unsolved goals @73:57.
- atk_5 (control-flow-effect, connParams emits password entry before database entry — list order swapped): exit=1, unsolved goals @115:53.
- atk_6 (ungrounded-oracle ECHO, dbArg returns spec closed-form verbatim; connParams gold): exit=0 VERIFIES. Clean axioms: 'correct_dbArg' does not depend on any axioms; 'correct_connParams' depends on [propext, Quot.sound] (standard Lean axioms, no sorryAx/custom). Faithful patch = gold patch (echo is behaviorally identical to gold impl). RESOLVE RUN via swebench_unified.harness.run_resolve('django__django-14376', <gold patch>, timeout=1800): RESOLVED=True COMPLETED=True note='resolved'. Per 2026-08-06 policy a resolving echo of gold is NOT a weakness.
- atk_7 (boundary, connParams emits database entry even when name = "" — drops n≠"" guard): exit=1, unsolved goals @114:53.

Each wrong-impl proof used a strong fallback ladder (first | rfl | by_cases/cases-split | simp_all | aesop) yet still failed — the exact-equality spec genuinely rejects each buggy implementation.

REFINEMENT.md AUDIT: All legs are R/I; no A-consumed and no A-reference legs (both behaviors modeled DEEPLY, not axiomatized). Triple 1 (dbArg): rows 1-4 R (precedence via Option.getD; truthiness via ≠""; the fix = row 2 adding higher-precedence 'database' lookup). Triple 2 (connParams): rows 1,4 I (init/return), rows 2,3 R (key rename db->database, passwd->password with truthiness guard). No kind-3 (unjustified) legs. axiom_check.py is a legitimate skip stub (G-AX skips): no opaque/axiom callee whose contract the proof consumes; settings/OPTIONS reads folded into Option String / String inputs at the I/O boundary. No A-leg callee correspondence to falsify because there are no A-legs.

CONCLUSION: verify => correct holds. Only impl closing with clean axioms is the exact echo of gold, whose faithful (gold) patch RESOLVES. All ≥5 genuinely-wrong attacks run and none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check on django__django-14376 lean bundle. Two independent triples.

Setup verified:
- Spec regions (axioms/pure/pre/post-conditions) byte-identical across Solution.lean and both prepatch files: same_spec(...) = True for prepatch_1 and prepatch_2 under LeanBackend.language.
- Solution.lean compiles clean via lean_verify.sh (exit 0), no sorry/admit. #print axioms clean: correct_dbArg depends on [propext]; correct_connParams on [propext, Quot.sound] — standard axioms only, no sorryAx.

Modeling faithfulness vs the real post-patch repo:

dbArg (client.py settings_to_cmd_args_env): post-patch code `database = OPTIONS.get('database', OPTIONS.get('db', NAME)); if database: args += [database]`. Model: `chosen = optDatabase.getD (optDb.getD name); if chosen = "" then none else some chosen`. Bijection: optDatabase=some iff 'database' key present (value possibly ""), optDb=some iff 'db' present, name=NAME. dict.get(k,default) returns stored value when key present (even empty) and default only when absent — exactly Option.getD. The present-but-empty short-circuit (`{'database':''}` selects "" and drops it, does NOT fall through) is faithfully captured. Truthiness `if database:` ⟺ chosen ≠ "". Exhaustive differential test over optDatabase,optDb ∈ {absent,"","x","y"} × name ∈ {"","n"}: 0 mismatches.

connParams (base.py get_connection_params): post-patch `if NAME: kwargs['database']=NAME; if PASSWORD: kwargs['password']=PASSWORD`. Model appends ("database",n) iff name=some n ∧ n≠"", then ("password",p) iff password=some p ∧ p≠"", in source order. Keys correctly renamed from deprecated db/passwd to database/password (the fix). Association-list order matches dict insertion order. Exhaustive differential test over name,password ∈ {absent,"","str"}: 0 mismatches.

The spec pins result to full equality with an input-grounded selection (not an over-strong oracle beyond repo behavior, nor a weaker one). No diverging input exists where the modeled function disagrees with the real callee over the modeled I/O boundary. The out-of-scope kwargs entries (user/host/port/etc.) are correctly excluded per mapping.md and are unchanged by the patch. No drift found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (post-conditions + docstrings only; impl/proof elided) does not leak the gold edit beyond the public problem_statement.

Mechanical G-LEAK screen: PASS (no diff markers, no patched file paths base.py/client.py, no dotted module path, no reproduced gold-patch line, no narration term bug/fix/patch/prepatch, no spec-view identifier or comment naming a patched repo symbol).

Semantic gold-reconstruction judgment:
- The connParams spec names the post-patch keys "database" and "password". These are ALREADY solver-visible: the problem_statement explicitly says the MySQL backend uses deprecated "db"/"passwd" kwargs and should move to "database"/"password". So revealing the target keys does not exceed the public task. The spec does NOT name the deprecated pre-patch keys "db"/"passwd" that the edit removes, so it does not disclose the before/after delta beyond what the task already states.
- The dbArg spec (client.py OPTIONS precedence) is strictly MORE abstract than the gold: the literal option keys 'database'/'db' and the OPTIONS.get precedence chain from the gold hunk are NOT present; they are abstracted to optDatabase/optDb/name with prose 'primary option / fallback option / configured name'. No file path (client.py), no method name (settings_to_cmd_args_env), no code line reproduced.
- The spec necessarily encodes correct post-patch behavior (that is its purpose), but a correct behavioral spec is not leakage; the standard is disclosure of the gold EDIT beyond the problem_statement, and here the only concretely-disclosed facts (the two kwarg key names) are already in the problem_statement, while the client-side change is left abstract. No spec-view line reconstructs the gold patch beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
