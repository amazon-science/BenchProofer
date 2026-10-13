# P2 adversarial audit — django__django-12741

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verifying-but-wrong candidate whose faithful refined patch could fail to resolve. The spec fully pins out = (conn.ownAlias, sqlList) via three ensures clauses (out = flushSpec conn sqlList; out.1 = conn.ownAlias; out.2 = sqlList), leaving no slack for a wrong impl to slip through.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,9 +62,7 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
-    let openedUnder : List Char := conn.ownAlias
+    let openedUnder : List Char := suppliedKey
     let replayed : List (List Char) := sqlList
     return (openedUnder, replayed)
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,9 +62,7 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
-    let openedUnder : List Char := conn.ownAlias
+    let openedUnder : List Char := []
     let replayed : List (List Char) := sqlList
     return (openedUnder, replayed)
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,10 +62,8 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
     let openedUnder : List Char := conn.ownAlias
-    let replayed : List (List Char) := sqlList
+    let replayed : List (List Char) := sqlList.reverse
     return (openedUnder, replayed)
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,10 +62,8 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
     let openedUnder : List Char := conn.ownAlias
-    let replayed : List (List Char) := sqlList
+    let replayed : List (List Char) := sqlList.drop 1
     return (openedUnder, replayed)
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,10 +62,8 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
     let openedUnder : List Char := conn.ownAlias
-    let replayed : List (List Char) := sqlList
+    let replayed : List (List Char) := sqlList ++ [[]]
     return (openedUnder, replayed)
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,9 +62,7 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
-    let openedUnder : List Char := conn.ownAlias
+    let openedUnder : List Char := conn.ownAlias ++ suppliedKey
     let replayed : List (List Char) := sqlList
     return (openedUnder, replayed)
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,10 +62,8 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
     let openedUnder : List Char := conn.ownAlias
-    let replayed : List (List Char) := sqlList
+    let replayed : List (List Char) := []
     return (openedUnder, replayed)
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,11 +62,9 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
-    let openedUnder : List Char := conn.ownAlias
-    let replayed : List (List Char) := sqlList
-    return (openedUnder, replayed)
+    match sqlList with
+    | [] => return (conn.ownAlias, [])
+    | _  => return (suppliedKey, sqlList)
     -- impl-end
 
 prove_correct runBatch by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,9 +62,9 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
-    let openedUnder : List Char := conn.ownAlias
+    let openedUnder : List Char := match sqlList with
+      | [] => conn.ownAlias
+      | h :: _ => h
     let replayed : List (List Char) := sqlList
     return (openedUnder, replayed)
     -- impl-end
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,11 +62,13 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
-    let openedUnder : List Char := conn.ownAlias
-    let replayed : List (List Char) := sqlList
-    return (openedUnder, replayed)
+    let mut t : Nat := 1
+    while t > 0
+      invariant True
+      done_with (t = 0)
+    do
+      t := t + 1
+    return (suppliedKey, sqlList.reverse)
     -- impl-end
 
 prove_correct runBatch by
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The unchanged callees this
@@ -62,11 +62,13 @@
   ensures out.2 = sqlList
   do
     -- impl-start
-    -- The scope is opened under the connection's own identifier; the supplied
-    -- key is deliberately unused. The statements are replayed unchanged.
-    let openedUnder : List Char := conn.ownAlias
-    let replayed : List (List Char) := sqlList
-    return (openedUnder, replayed)
+    let mut t : Nat := 1
+    while t > 0
+      invariant True
+      done_with (t = 0)
+    do
+      t := t
+    return ([], [])
     -- impl-end
 
 prove_correct runBatch by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The unchanged callees this
   slice relies on — opening a scoped database operation keyed by a connection
   identifier, and replaying a list of statements through that connection — are
   pure framework/side-effecting operations whose only data-carrier inputs are
   the connection's own identifier and the statement list, modeled directly as
   the inputs `connAlias` / `sqlList` of the operation. Their provenance and the
   input bijection are recorded in mapping.md; the end-to-end behaviour is
   differential-tested by conformance_check.py (G-CONF). -/
-- axioms-end

-- pure-start
/- A connection-bound batch operation, viewed only through the two facts the
   surrounding behaviour observes: the identifier under which the scoped
   operation is opened, and the statements it replays, in order. The connection
   carries its OWN identifier (`alias`); the result of running the batch is the
   pair of (identifier the scope was opened under, statements replayed). -/
structure Connection where
  ownAlias : List Char
  deriving DecidableEq

/- The intended effect of running the batch on a connection: the scope is opened
   under the connection's own identifier, and the statement list is replayed
   unchanged, in order. The identifier the scope is opened under must be the
   connection's own — it is determined by the connection itself, never by any
   value supplied alongside the statements. -/
def flushSpec (conn : Connection) (sqlList : List (List Char)) :
    (List Char) × (List (List Char)) :=
  (conn.ownAlias, sqlList)

@[grind] lemma flushSpec_fst (conn : Connection) (sqlList : List (List Char)) :
    (flushSpec conn sqlList).1 = conn.ownAlias := rfl
@[grind] lemma flushSpec_snd (conn : Connection) (sqlList : List (List Char)) :
    (flushSpec conn sqlList).2 = sqlList := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `suppliedKey` is an identifier handed to the operation alongside the
   statement list. It is read-only and must NOT determine the identifier the
   scoped operation is opened under: the postcondition pins the opened identifier
   to the connection's own identifier alone, so any implementation that lets
   `suppliedKey` reach the result fails to verify. The statement list is replayed
   unchanged and in order. -/
method runBatch
    (conn : Connection) (suppliedKey : List Char) (sqlList : List (List Char))
    return (out : (List Char) × (List (List Char)))
  ensures out = flushSpec conn sqlList
  ensures out.1 = conn.ownAlias
  ensures out.2 = sqlList
  do
    -- impl-start
    -- The scope is opened under the connection's own identifier; the supplied
    -- key is deliberately unused. The statements are replayed unchanged.
    let openedUnder : List Char := conn.ownAlias
    let replayed : List (List Char) := sqlList
    return (openedUnder, replayed)
    -- impl-end

prove_correct runBatch by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Same-spec confirmed True for all 11 attacks via swebench_unified.markers.same_spec (velvet backend, python). Verified each with `bash scripts/lean_verify.sh <atk>.lean` from project root, run concurrently in 3 background batches (4/4/3, <=4 at a time).

RESULTS — ALL 11 attacks FAIL to verify (exit 1); positive control (byte copy of Solution.lean) verifies (exit 0):
- atk_1 openedUnder:=suppliedKey (THE PREPATCH BUG reproduced) -> unsolved `suppliedKey = conn.ownAlias` (ensures_2). Prepatch reproduced.
- atk_2 openedUnder:=[] (constant/ungrounded) -> `[] = conn.ownAlias`.
- atk_3 replayed:=sqlList.reverse (order tamper) -> `sqlList.reverse = sqlList`.
- atk_4 replayed:=sqlList.drop 1 (boundary/partial) -> ensures_1 fails.
- atk_5 replayed:=sqlList ++ [[]] (extra empty stmt, boundary) -> ensures_1 fails.
- atk_6 openedUnder:=conn.ownAlias ++ suppliedKey (suppliedKey leak) -> ensures_2 fails.
- atk_7 replayed:=[] (nothing replayed) -> ensures_1 fails.
- atk_8 PARTIAL-DOMAIN control-flow: correct on [] , returns (suppliedKey, sqlList) on nonempty -> nonempty branch leaves `suppliedKey = conn.ownAlias`.
- atk_9 UNGROUNDED-ORACLE ECHO: openedUnder := head of sqlList when nonempty (echoes an input into the alias slot) -> ensures_2 fails.
- atk_10 CONTROL-FLOW-EFFECT / partial-correctness DIVERGENCE: `while t>0 (t:=t+1)` diverging loop then return (suppliedKey, sqlList.reverse) -> loom does NOT discharge postconditions vacuously via nontermination; post-loop return must satisfy ensures under invariant True + done(t=0), leaving unsolved `suppliedKey = conn.ownAlias` and `sqlList.reverse = sqlList`. This is the critical `termination "partial"` escape hatch and it is CLOSED.
- atk_11 unconditional divergence then return ([], []) -> same: `[] = sqlList`, `[] = conn.ownAlias` unsolved.

Step 2 (materialize faithful patch + run_resolve): VACUOUS — no verifying wrong impl exists, so there is no candidate patch to resolve. No BROKEN condition can arise.

Step 3 refinement.md audit: all legs R or I; NO A-legs (meta.json axioms:[], deep_model_references:[]) so no A-consumed/A-reference correspondence to check; the mechanized R/I legs are covered by G-CONF (meta.json G-CONF=pass, 0 disagreements over 100006 inputs, seed=12741) which invokes the REAL patched execute_sql_flush(sql_list). No kind-3 step: the one genuinely-changed op (source of transaction.atomic(using=...)) is modeled directly as out.1=conn.ownAlias (kind-I over the modeled Connection), grounded in a real input field, NOT axiomatized and NOT an ungrounded oracle (flushSpec is a transparent rfl-reducible def). Model<->patch correspondence holds: runBatch(conn,suppliedKey,sqlList) <-> execute_sql_flush over (self.connection, dropped using param, sql_list); out.1=conn.ownAlias <-> using=self.connection.alias; out.2=sqlList <-> the unchanged replay loop.

VERDICT: SOUND. >=5 distinct wrong-impl families (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, divergence) all attempted and all rejected; none verifies, so verify => correct is not broken by any exhibited counterexample.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verifying-but-wrong candidate whose faithful refined patch could fail to resolve. The spec fully pins out = (conn.ownAlias, sqlList) via three ensures clauses (out = flushSpec conn sqlList; out.1 = conn.ownAlias; out.2 = sqlList), leaving no slack for a wrong impl to slip through.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The unchanged callees this
   slice relies on — opening a scoped database operation keyed by a connection
   identifier, and replaying a list of statements through that connection — are
   pure framework/side-effecting operations whose only data-carrier inputs are
   the connection's own identifier and the statement list, modeled directly as
   the inputs `connAlias` / `sqlList` of the operation. Their provenance and the
   input bijection are recorded in mapping.md; the end-to-end behaviour is
   differential-tested by conformance_check.py (G-CONF). -/
-- axioms-end

-- pure-start
/- A connection-bound batch operation, viewed only through the two facts the
   surrounding behaviour observes: the identifier under which the scoped
   operation is opened, and the statements it replays, in order. The connection
   carries its OWN identifier (`alias`); the result of running the batch is the
   pair of (identifier the scope was opened under, statements replayed). -/
structure Connection where
  ownAlias : List Char
  deriving DecidableEq

/- The intended effect of running the batch on a connection: the scope is opened
   under the connection's own identifier, and the statement list is replayed
   unchanged, in order. The identifier the scope is opened under must be the
   connection's own — it is determined by the connection itself, never by any
   value supplied alongside the statements. -/
def flushSpec (conn : Connection) (sqlList : List (List Char)) :
    (List Char) × (List (List Char)) :=
  (conn.ownAlias, sqlList)

@[grind] lemma flushSpec_fst (conn : Connection) (sqlList : List (List Char)) :
    (flushSpec conn sqlList).1 = conn.ownAlias := rfl
@[grind] lemma flushSpec_snd (conn : Connection) (sqlList : List (List Char)) :
    (flushSpec conn sqlList).2 = sqlList := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `suppliedKey` is an identifier handed to the operation alongside the
   statement list. It is read-only and must NOT determine the identifier the
   scoped operation is opened under: the postcondition pins the opened identifier
   to the connection's own identifier alone, so any implementation that lets
   `suppliedKey` reach the result fails to verify. The statement list is replayed
   unchanged and in order. -/
method runBatch
    (conn : Connection) (suppliedKey : List Char) (sqlList : List (List Char))
    return (out : (List Char) × (List (List Char)))
  ensures out = flushSpec conn sqlList
  ensures out.1 = conn.ownAlias
  ensures out.2 = sqlList
  do
    -- impl-start
    -- The scope is opened under the connection's own identifier; the supplied
    -- key is deliberately unused. The statements are replayed unchanged.
    let openedUnder : List Char := conn.ownAlias
    let replayed : List (List Char) := sqlList
    return (openedUnder, replayed)
    -- impl-end

prove_correct runBatch by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Same-spec confirmed True for all 11 attacks via swebench_unified.markers.same_spec (velvet backend, python). Verified each with `bash scripts/lean_verify.sh <atk>.lean` from project root, run concurrently in 3 background batches (4/4/3, <=4 at a time).

RESULTS — ALL 11 attacks FAIL to verify (exit 1); positive control (byte copy of Solution.lean) verifies (exit 0):
- atk_1 openedUnder:=suppliedKey (THE PREPATCH BUG reproduced) -> unsolved `suppliedKey = conn.ownAlias` (ensures_2). Prepatch reproduced.
- atk_2 openedUnder:=[] (constant/ungrounded) -> `[] = conn.ownAlias`.
- atk_3 replayed:=sqlList.reverse (order tamper) -> `sqlList.reverse = sqlList`.
- atk_4 replayed:=sqlList.drop 1 (boundary/partial) -> ensures_1 fails.
- atk_5 replayed:=sqlList ++ [[]] (extra empty stmt, boundary) -> ensures_1 fails.
- atk_6 openedUnder:=conn.ownAlias ++ suppliedKey (suppliedKey leak) -> ensures_2 fails.
- atk_7 replayed:=[] (nothing replayed) -> ensures_1 fails.
- atk_8 PARTIAL-DOMAIN control-flow: correct on [] , returns (suppliedKey, sqlList) on nonempty -> nonempty branch leaves `suppliedKey = conn.ownAlias`.
- atk_9 UNGROUNDED-ORACLE ECHO: openedUnder := head of sqlList when nonempty (echoes an input into the alias slot) -> ensures_2 fails.
- atk_10 CONTROL-FLOW-EFFECT / partial-correctness DIVERGENCE: `while t>0 (t:=t+1)` diverging loop then return (suppliedKey, sqlList.reverse) -> loom does NOT discharge postconditions vacuously via nontermination; post-loop return must satisfy ensures under invariant True + done(t=0), leaving unsolved `suppliedKey = conn.ownAlias` and `sqlList.reverse = sqlList`. This is the critical `termination "partial"` escape hatch and it is CLOSED.
- atk_11 unconditional divergence then return ([], []) -> same: `[] = sqlList`, `[] = conn.ownAlias` unsolved.

Step 2 (materialize faithful patch + run_resolve): VACUOUS — no verifying wrong impl exists, so there is no candidate patch to resolve. No BROKEN condition can arise.

Step 3 refinement.md audit: all legs R or I; NO A-legs (meta.json axioms:[], deep_model_references:[]) so no A-consumed/A-reference correspondence to check; the mechanized R/I legs are covered by G-CONF (meta.json G-CONF=pass, 0 disagreements over 100006 inputs, seed=12741) which invokes the REAL patched execute_sql_flush(sql_list). No kind-3 step: the one genuinely-changed op (source of transaction.atomic(using=...)) is modeled directly as out.1=conn.ownAlias (kind-I over the modeled Connection), grounded in a real input field, NOT axiomatized and NOT an ungrounded oracle (flushSpec is a transparent rfl-reducible def). Model<->patch correspondence holds: runBatch(conn,suppliedKey,sqlList) <-> execute_sql_flush over (self.connection, dropped using param, sql_list); out.1=conn.ownAlias <-> using=self.connection.alias; out.2=sqlList <-> the unchanged replay loop.

VERDICT: SOUND. >=5 distinct wrong-impl families (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, divergence) all attempted and all rejected; none verifies, so verify => correct is not broken by any exhibited counterexample.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Role: faithfulness-break (is the spec too strong / does it drift from real repo behavior?). Conclusion: FAITHFUL — no diverging input exists.

Modeled function: runBatch(conn: Connection, suppliedKey: List Char, sqlList: List (List Char)) -> (List Char) x (List (List Char)), returning flushSpec conn sqlList = (conn.ownAlias, sqlList). Repo callee: BaseDatabaseOperations.execute_sql_flush at django/db/backends/base/operations.py:405 (post-patch signature (self, sql_list)).

Verified against the real post-patch source (base_commit 537d422942...):
  def execute_sql_flush(self, sql_list):
      with transaction.atomic(using=self.connection.alias, savepoint=self.connection.features.can_rollback_ddl):
          with self.connection.cursor() as cursor:
              for sql in sql_list: cursor.execute(sql)

1. out.1 = conn.ownAlias: the using= key is ALWAYS self.connection.alias for every input; the spec pins out.1 = conn.ownAlias for every suppliedKey. Exact match, not over-constrained. The suppliedKey input models the dropped positional `using` parameter; the spec requires the output be independent of it — this cannot be too strong because the patched signature provides no channel for any supplied value to reach the using-key. Independence-from-suppliedKey is precisely the patch's behavior.
2. out.2 = sqlList: the for-loop replays each statement once, in order, unchanged (loop untouched by the patch). Exact match.
3. Elision check: the only elided detail is savepoint=self.connection.features.can_rollback_ddl, about which the spec makes NO claim (output tuple omits it) — a legitimate abstraction, not an over-constraint. No input exists on which the spec demands more than the real function delivers.

Corroboration: same_spec(Solution, Solution_prepatch)=True (spec region byte-identical; differs only in impl). Solution.lean elaborates clean (lean_verify exit 0). G-CONF ran 100006 fuzzed inputs incl. supplied_key!=alias boundaries with 0 disagreements vs the real patched callee (transaction.atomic/cursor stubbed to record observables). Searched for a diverging input across empty/nonempty alias, empty/nonempty sqlList, unicode aliases, supplied_key differing from alias — none found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean (same_spec == True). Mechanical G-LEAK screen passes with zero hard failures (no diff markers, no patched file/module paths, no spec-view identifier embedding patched symbols {execute_sql_flush, sql_flush, handle}, no bug/fix narration). No relaxation in force (relaxed_leakage: None, no RELAXED_LEAKAGE.md), so this is a genuine clean-view judgment.

Semantic gold-reconstruction check: the gold edit is 'drop the `using` param and source the transaction key from self.connection.alias instead.' The PUBLIC problem_statement already discloses this in full — it names execute_sql_flush(), shows the exact before/after signatures ((self, using, sql_list) -> (self, sql_list)), and states verbatim: 'The using argument can be dropped and inferred by the calling instance: self.connection.alias.' The spec view models the same discriminator (opened identifier pinned to the connection's OWN identifier `ownAlias`; `suppliedKey` must not reach the result) but in fully abstracted, renamed terms (runBatch/Connection/ownAlias/suppliedKey), revealing strictly LESS repo-specific detail than the public task text. The spec's information content about the fix is a subset of the problem_statement, so it leaks nothing beyond it. Comments describe intended behavior without naming the edit or narrating a bug/fix. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
