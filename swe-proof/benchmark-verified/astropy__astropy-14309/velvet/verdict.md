# P2 adversarial audit — astropy__astropy-14309

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `ctrl2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies; the spec 'out = originSpec stream path extra' is a total equality against a fully concrete function (match over stream/path/extra; hasKnownExt is a transparent def, not an axiom). There is no ungrounded oracle to echo and the partial-correctness/demonic-choice semantics do NOT open a divergence-vacuity hole here: the frozen proof (loom_solve; simp_all [originSpec]) rejects every diverging impl.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,17 +91,17 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
     let result : Except Crash Bool :=
       match stream with
       | some s => Except.ok s
       | none =>
         match path with
-        | some p => Except.ok (hasKnownExt p)
+        | some p =>
+            if hasKnownExt p then Except.ok true
+            else
+              match extra with
+              | []     => Except.error Crash.indexOOB
+              | a :: _ => Except.ok a
         | none =>
           match extra with
           | []     => Except.error Crash.indexOOB
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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,17 +91,12 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
     let result : Except Crash Bool :=
       match stream with
       | some s => Except.ok s
       | none =>
         match path with
-        | some p => Except.ok (hasKnownExt p)
+        | some _ => Except.ok false
         | none =>
           match extra with
           | []     => Except.error Crash.indexOOB
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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,17 +91,12 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
     let result : Except Crash Bool :=
       match stream with
       | some s => Except.ok s
       | none =>
         match path with
-        | some p => Except.ok (hasKnownExt p)
+        | some p => Except.ok (!hasKnownExt p)
         | none =>
           match extra with
           | []     => Except.error Crash.indexOOB
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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,14 +91,9 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
     let result : Except Crash Bool :=
       match stream with
-      | some s => Except.ok s
+      | some s => Except.ok (!s)
       | none =>
         match path with
         | some p => Except.ok (hasKnownExt p)
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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,17 +91,12 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
     let result : Except Crash Bool :=
-      match stream with
-      | some s => Except.ok s
+      match path with
+      | some p => Except.ok (hasKnownExt p)
       | none =>
-        match path with
-        | some p => Except.ok (hasKnownExt p)
+        match stream with
+        | some s => Except.ok s
         | none =>
           match extra with
           | []     => Except.error Crash.indexOOB
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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,11 +91,6 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
     let result : Except Crash Bool :=
       match stream with
       | some s => Except.ok s
@@ -104,7 +99,7 @@
         | some p => Except.ok (hasKnownExt p)
         | none =>
           match extra with
-          | []     => Except.error Crash.indexOOB
+          | []     => Except.ok false
           | a :: _ => Except.ok a
     return result
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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,11 +91,6 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
     let result : Except Crash Bool :=
       match stream with
       | some s => Except.ok s
@@ -103,7 +98,7 @@
         match path with
         | some p => Except.ok (hasKnownExt p)
         | none =>
-          match extra with
+          match extra.reverse with
           | []     => Except.error Crash.indexOOB
           | a :: _ => Except.ok a
     return result
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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,22 +91,13 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
-    let result : Except Crash Bool :=
-      match stream with
-      | some s => Except.ok s
-      | none =>
-        match path with
-        | some p => Except.ok (hasKnownExt p)
-        | none =>
-          match extra with
-          | []     => Except.error Crash.indexOOB
-          | a :: _ => Except.ok a
-    return result
+    -- Diverge: under partial-correctness semantics a non-terminating method
+    -- vacuously satisfies any postcondition. If this verifies, the returned
+    -- value is unconstrained -> verify does not imply correct.
+    let mut i : Nat := 0
+    while true do
+      i := i + 1
+    return Except.ok false
     -- impl-end
 
 prove_correct classifyFitsOrigin by
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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,14 +91,9 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
     let result : Except Crash Bool :=
       match stream with
-      | some s => Except.ok s
+      | some _ => Except.ok true
       | none =>
         match path with
         | some p => Except.ok (hasKnownExt p)
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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,22 +91,7 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
-    let result : Except Crash Bool :=
-      match stream with
-      | some s => Except.ok s
-      | none =>
-        match path with
-        | some p => Except.ok (hasKnownExt p)
-        | none =>
-          match extra with
-          | []     => Except.error Crash.indexOOB
-          | a :: _ => Except.ok a
-    return result
+    return Except.error Crash.indexOOB
     -- impl-end
 
 prove_correct classifyFitsOrigin by
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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,22 +91,19 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
-    let result : Except Crash Bool :=
-      match stream with
-      | some s => Except.ok s
+    match stream with
+    | some s => return Except.ok s
+    | none =>
+      match path with
+      | some _ =>
+          let mut i : Nat := 0
+          while true do
+            i := i + 1
+          return Except.ok false
       | none =>
-        match path with
-        | some p => Except.ok (hasKnownExt p)
-        | none =>
-          match extra with
-          | []     => Except.error Crash.indexOOB
-          | a :: _ => Except.ok a
-    return result
+        match extra with
+        | []     => return Except.error Crash.indexOOB
+        | a :: _ => return Except.ok a
     -- impl-end
 
 prove_correct classifyFitsOrigin by
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

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
 /- The distinguished failure that escapes the classifier when it consults a
@@ -91,22 +91,19 @@
   ensures out = originSpec stream path extra
   do
     -- impl-start
-    -- Branch in order on the available observations. A present stream yields its
-    -- signature verdict; a present path yields its known-extension verdict
-    -- DIRECTLY (returned in full, matching or not, never falling through); only
-    -- when neither is present is the first trailing positional observation read,
-    -- and an empty trailing sequence lets the absent-observation failure escape.
-    let result : Except Crash Bool :=
-      match stream with
-      | some s => Except.ok s
+    match stream with
+    | some _ =>
+        let mut i : Nat := 0
+        while true do
+          i := i + 1
+        return Except.ok false
+    | none =>
+      match path with
+      | some p => return Except.ok (hasKnownExt p)
       | none =>
-        match path with
-        | some p => Except.ok (hasKnownExt p)
-        | none =>
-          match extra with
-          | []     => Except.error Crash.indexOOB
-          | a :: _ => Except.ok a
-    return result
+        match extra with
+        | []     => return Except.error Crash.indexOOB
+        | a :: _ => return Except.ok a
     -- impl-end
 
 prove_correct classifyFitsOrigin by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The distinguished failure that escapes the classifier when it consults a
   positional observation that is not present: a required entry of the trailing
   positional sequence is read while that sequence is empty. This is the failure
   shape the public problem statement reports as escaping from a path-only call.
   It is a genuine outcome of the operation, modeled explicitly so the spec can
   pin exactly when it does and does NOT occur. -/
inductive Crash where
  | indexOOB
  deriving DecidableEq
-- axioms-end

-- pure-start
/- The recognised filename extensions that mark a candidate of the format under
   classification (the lowercase suffixes the path test accepts). -/
def knownExts : List (List Char) :=
  [".fits".toList, ".fits.gz".toList, ".fit".toList,
   ".fit.gz".toList, ".fts".toList, ".fts.gz".toList]

/- Whether a path's code-point sequence ends, case-insensitively, in one of the
   recognised extensions: lowercase the path, then test it against each known
   suffix. Deep model (an A-reference, mapping.md §3.1) of the unchanged
   case-folding suffix test the path branch performs; validated == the real
   `.lower().endswith((...))` by axiom_check.py (G-AX). -/
def hasKnownExt (path : List Char) : Bool :=
  knownExts.any (fun ext => ext.isSuffixOf (path.map Char.toLower))

/- The intended outcome of the whole classification, as `Except Crash Bool`
   (`error` = the absent-observation failure escapes, `ok b` = a verdict `b` is
   returned):

     * if a readable stream observation is present, its signature verdict is
       returned verbatim;
     * otherwise, if a path is present, the verdict is the case-insensitive
       known-extension test of that path — returned UNCONDITIONALLY, whether the
       test holds or not (the desired behavior the public problem statement
       demands: a present path always yields a verdict and never falls through to
       inspecting a trailing positional observation);
     * otherwise (neither stream nor path present), the first trailing positional
       observation is the verdict — and if there is none, the absent-observation
       failure escapes.

   Only the third branch may fail; a present path can never make it fail. -/
def originSpec (stream : Option Bool) (path : Option (List Char))
    (extra : List Bool) : Except Crash Bool :=
  match stream with
  | some s => Except.ok s
  | none =>
    match path with
    | some p => Except.ok (hasKnownExt p)
    | none =>
      match extra with
      | []     => Except.error Crash.indexOOB
      | a :: _ => Except.ok a
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Classify whether an origin denotes a file of the format under recognition.

   Desired behavior: the classifier is consulted with, in order, a readable
   stream observation, a path, and a trailing sequence of positional
   observations. A present stream observation yields its signature verdict. When
   no stream is present but a PATH is, the classifier must return the path's
   case-insensitive known-extension verdict OUTRIGHT — for every path, matching
   or not — and must never proceed to read a trailing positional observation
   (the missing behavior the public problem statement reports: a path-only call
   on a non-matching name must return a plain `false`, not let an
   absent-observation failure escape). Only when NEITHER a stream nor a path is
   present is the first trailing positional observation consulted; if that
   sequence is empty the absent-observation failure escapes.

   `stream`, `path`, and `extra` are read-only (none is `mut`): the classifier
   computes a verdict and mutates no input (directive 5). The stream's signature
   comparison is collapsed to its boolean observation and each positional
   argument to its boolean class-membership observation (mapping.md §2). -/
method classifyFitsOrigin (stream : Option Bool) (path : Option (List Char))
    (extra : List Bool) return (out : Except Crash Bool)
  ensures out = originSpec stream path extra
  do
    -- impl-start
    let out0 : Except Crash Bool :=
      match stream with
      | some sv => Except.ok sv
      | none =>
        match path with
        | some pp => Except.ok (hasKnownExt pp)
        | none =>
          match extra with
          | []      => Except.error Crash.indexOOB
          | hd :: _ => Except.ok hd
    return out0
    -- impl-end

prove_correct classifyFitsOrigin by
  loom_solve
  simp_all [originSpec]
```

Prepatch bug re-encoded as an attack: `True`.

 Verify cmd: `bash scripts/lean_verify.sh <atk>.lean`. same_spec via swebench_unified.markers.same_spec + get_backend('velvet').

12 DISTINCT same-spec wrong impls (all same_spec=True, verified in ≤4-wide background batches):
- atk_1 prepatch bug (non-matching path falls through to extra/IndexError): same_spec=True, verify EXIT=1 (rejected; discriminates at `some p` non-matching, spec=ok(hasKnownExt p) vs impl reads extra). This is exactly F2P test_is_fits_gh_14305 (is_fits("","foo.bar",None)).
- atk_2 present path -> ok false (partial-domain, ignores extension): EXIT=1
- atk_3 present path -> ok (!hasKnownExt p) (negation): EXIT=1
- atk_4 stream -> ok (!s) (negation): EXIT=1
- atk_5 path checked before stream (precedence swap): EXIT=1
- atk_6 empty extra -> ok false instead of error (boundary): EXIT=1
- atk_7 extra uses reverse head (last) not head (control-flow): EXIT=1
- atk_8 full divergence (while true) then wrong return ok false (partial-correctness vacuity attack): EXIT=1 — loom_solve closes vacuous WP but frozen simp_all errors 'No goals'; NOT admitted.
- atk_9 stream -> ok true (constant, ungrounded-oracle-echo style): EXIT=1
- atk_10 return error unconditionally (constant): EXIT=1
- atk_11 PARTIAL-DOMAIN divergence: diverge ONLY in path-present branch, correct elsewhere: EXIT=1 — frozen proof fails 'Failed to prove assertion WPGen' on the loop branch. This is the strongest verify⇏correct hole and it is CLOSED.
- atk_12 partial-domain divergence in stream branch: EXIT=1.

Positive control ctrl2.lean (renamed binders sv/pp/hd, same let-then-return structure): same_spec=True, verify EXIT=0 — spec NON-VACUOUS. (Note: verdict.md's brittleness warning confirmed — a `return match ...` restructuring (ctrl.lean) fails to parse under the frozen `let result; return result` proof shape; this is conservative, never admits a wrong impl.)

Prepatch: Solution_prepatch.lean copied and verified -> EXIT=1 (fails for the right reason, path-branch fall-through divergence from originSpec).

axiom_check.py (A-reference hasKnownExt == real str.lower().endswith((...)), stdlib-only): EXIT=0, 25 boundary + 20000 fuzz (9974 genuine matches). A-reference fidelity confirmed.

Refinement audit (refinement.md §A): A1 (stream branch) = R+I unchanged; A2 (path branch) = R + A-reference (hasKnownExt deep model, G-AX validated); A3 (extra/IndexError) = R+I unchanged. No kind-3 leg. NO A-consumed axiom (Crash.indexOOB is a modeled inductive outcome; proof discharges over concrete branches). A-leg correspondence to real callees holds (axiom_check exit 0).

No verifying wrong impl exists, so the mandatory materialize-faithful-patch-and-run_resolve step (triggered only by a verifying attack) has no candidates — patches={} correctly empty. Spec is TIGHT; verify⇒correct holds for this bundle.

VERDICT: SOUND (12 attacks incl. 3 divergence/partial-correctness attacks run, none breaks the spec; positive control verifies; prepatch reproduced; A-reference sound; refinement clean).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |

**Non-vacuity.** The positive control `ctrl2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies; the spec 'out = originSpec stream path extra' is a total equality against a fully concrete function (match over stream/path/extra; hasKnownExt is a transparent def, not an axiom). There is no ungrounded oracle to echo and the partial-correctness/demonic-choice semantics do NOT open a divergence-vacuity hole here: the frozen proof (loom_solve; simp_all [originSpec]) rejects every diverging impl.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

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

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The distinguished failure that escapes the classifier when it consults a
   positional observation that is not present: a required entry of the trailing
   positional sequence is read while that sequence is empty. This is the failure
   shape the public problem statement reports as escaping from a path-only call.
   It is a genuine outcome of the operation, modeled explicitly so the spec can
   pin exactly when it does and does NOT occur. -/
inductive Crash where
  | indexOOB
  deriving DecidableEq
-- axioms-end

-- pure-start
/- The recognised filename extensions that mark a candidate of the format under
   classification (the lowercase suffixes the path test accepts). -/
def knownExts : List (List Char) :=
  [".fits".toList, ".fits.gz".toList, ".fit".toList,
   ".fit.gz".toList, ".fts".toList, ".fts.gz".toList]

/- Whether a path's code-point sequence ends, case-insensitively, in one of the
   recognised extensions: lowercase the path, then test it against each known
   suffix. Deep model (an A-reference, mapping.md §3.1) of the unchanged
   case-folding suffix test the path branch performs; validated == the real
   `.lower().endswith((...))` by axiom_check.py (G-AX). -/
def hasKnownExt (path : List Char) : Bool :=
  knownExts.any (fun ext => ext.isSuffixOf (path.map Char.toLower))

/- The intended outcome of the whole classification, as `Except Crash Bool`
   (`error` = the absent-observation failure escapes, `ok b` = a verdict `b` is
   returned):

     * if a readable stream observation is present, its signature verdict is
       returned verbatim;
     * otherwise, if a path is present, the verdict is the case-insensitive
       known-extension test of that path — returned UNCONDITIONALLY, whether the
       test holds or not (the desired behavior the public problem statement
       demands: a present path always yields a verdict and never falls through to
       inspecting a trailing positional observation);
     * otherwise (neither stream nor path present), the first trailing positional
       observation is the verdict — and if there is none, the absent-observation
       failure escapes.

   Only the third branch may fail; a present path can never make it fail. -/
def originSpec (stream : Option Bool) (path : Option (List Char))
    (extra : List Bool) : Except Crash Bool :=
  match stream with
  | some s => Except.ok s
  | none =>
    match path with
    | some p => Except.ok (hasKnownExt p)
    | none =>
      match extra with
      | []     => Except.error Crash.indexOOB
      | a :: _ => Except.ok a
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Classify whether an origin denotes a file of the format under recognition.

   Desired behavior: the classifier is consulted with, in order, a readable
   stream observation, a path, and a trailing sequence of positional
   observations. A present stream observation yields its signature verdict. When
   no stream is present but a PATH is, the classifier must return the path's
   case-insensitive known-extension verdict OUTRIGHT — for every path, matching
   or not — and must never proceed to read a trailing positional observation
   (the missing behavior the public problem statement reports: a path-only call
   on a non-matching name must return a plain `false`, not let an
   absent-observation failure escape). Only when NEITHER a stream nor a path is
   present is the first trailing positional observation consulted; if that
   sequence is empty the absent-observation failure escapes.

   `stream`, `path`, and `extra` are read-only (none is `mut`): the classifier
   computes a verdict and mutates no input (directive 5). The stream's signature
   comparison is collapsed to its boolean observation and each positional
   argument to its boolean class-membership observation (mapping.md §2). -/
method classifyFitsOrigin (stream : Option Bool) (path : Option (List Char))
    (extra : List Bool) return (out : Except Crash Bool)
  ensures out = originSpec stream path extra
  do
    -- impl-start
    let out0 : Except Crash Bool :=
      match stream with
      | some sv => Except.ok sv
      | none =>
        match path with
        | some pp => Except.ok (hasKnownExt pp)
        | none =>
          match extra with
          | []      => Except.error Crash.indexOOB
          | hd :: _ => Except.ok hd
    return out0
    -- impl-end

prove_correct classifyFitsOrigin by
  loom_solve
  simp_all [originSpec]
```

Prepatch bug re-encoded as an attack: `True`.

 Verify cmd: `bash scripts/lean_verify.sh <atk>.lean`. same_spec via swebench_unified.markers.same_spec + get_backend('velvet').

12 DISTINCT same-spec wrong impls (all same_spec=True, verified in ≤4-wide background batches):
- atk_1 prepatch bug (non-matching path falls through to extra/IndexError): same_spec=True, verify EXIT=1 (rejected; discriminates at `some p` non-matching, spec=ok(hasKnownExt p) vs impl reads extra). This is exactly F2P test_is_fits_gh_14305 (is_fits("","foo.bar",None)).
- atk_2 present path -> ok false (partial-domain, ignores extension): EXIT=1
- atk_3 present path -> ok (!hasKnownExt p) (negation): EXIT=1
- atk_4 stream -> ok (!s) (negation): EXIT=1
- atk_5 path checked before stream (precedence swap): EXIT=1
- atk_6 empty extra -> ok false instead of error (boundary): EXIT=1
- atk_7 extra uses reverse head (last) not head (control-flow): EXIT=1
- atk_8 full divergence (while true) then wrong return ok false (partial-correctness vacuity attack): EXIT=1 — loom_solve closes vacuous WP but frozen simp_all errors 'No goals'; NOT admitted.
- atk_9 stream -> ok true (constant, ungrounded-oracle-echo style): EXIT=1
- atk_10 return error unconditionally (constant): EXIT=1
- atk_11 PARTIAL-DOMAIN divergence: diverge ONLY in path-present branch, correct elsewhere: EXIT=1 — frozen proof fails 'Failed to prove assertion WPGen' on the loop branch. This is the strongest verify⇏correct hole and it is CLOSED.
- atk_12 partial-domain divergence in stream branch: EXIT=1.

Positive control ctrl2.lean (renamed binders sv/pp/hd, same let-then-return structure): same_spec=True, verify EXIT=0 — spec NON-VACUOUS. (Note: verdict.md's brittleness warning confirmed — a `return match ...` restructuring (ctrl.lean) fails to parse under the frozen `let result; return result` proof shape; this is conservative, never admits a wrong impl.)

Prepatch: Solution_prepatch.lean copied and verified -> EXIT=1 (fails for the right reason, path-branch fall-through divergence from originSpec).

axiom_check.py (A-reference hasKnownExt == real str.lower().endswith((...)), stdlib-only): EXIT=0, 25 boundary + 20000 fuzz (9974 genuine matches). A-reference fidelity confirmed.

Refinement audit (refinement.md §A): A1 (stream branch) = R+I unchanged; A2 (path branch) = R + A-reference (hasKnownExt deep model, G-AX validated); A3 (extra/IndexError) = R+I unchanged. No kind-3 leg. NO A-consumed axiom (Crash.indexOOB is a modeled inductive outcome; proof discharges over concrete branches). A-leg correspondence to real callees holds (axiom_check exit 0).

No verifying wrong impl exists, so the mandatory materialize-faithful-patch-and-run_resolve step (triggered only by a verifying attack) has no candidates — patches={} correctly empty. Spec is TIGHT; verify⇒correct holds for this bundle.

VERDICT: SOUND (12 attacks incl. 3 divergence/partial-correctness attacks run, none breaks the spec; positive control verifies; prepatch reproduced; A-reference sound; refinement clean).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift). Could NOT break faithfulness. Evidence:

1) SPEC REGION byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch)=True; only the impl region differs. Frozen spec = originSpec + hasKnownExt + Crash, unchanged.

2) LEAN VERIFIES: scripts/lean_verify.sh Solution.lean -> exit 0; the ensures out=originSpec obligation discharges via loom_solve/simp_all.

3) REAL CALLEE (base_commit cdb66059..., astropy/io/fits/connect.py:48, gold post-patch): fileobj!=None -> sig==FITS_SIGNATURE; elif filepath!=None -> filepath.lower().endswith((.fits,.fits.gz,.fit,.fit.gz,.fts,.fts.gz)) OUTRIGHT; else isinstance(args[0],(HDUList,TableHDU,BinTableHDU,GroupsHDU)) with IndexError on empty *args. originSpec's three-branch match (stream/some -> ok s; path/some -> ok(hasKnownExt p); extra [] -> error indexOOB, a::_ -> ok a) mirrors this exactly under the mapping.md abstraction (fileobj->Option Bool collapsed to sig-bool, filepath->Option(List Char), *args entries->isinstance-bool List, IndexError->Crash.indexOOB).

4) DEEP-MODEL RISK CLOSED: hasKnownExt uses Lean Char.toLower (ASCII-only per code point) whereas Python str.lower() is full Unicode. The conformance check uses Python .lower() on BOTH sides so it structurally cannot catch a Lean-vs-Python lowering gap. Independently investigated: exhaustive scan of all 0x110000 codepoints found NO non-ASCII char whose .lower() yields characters that could complete an ASCII known-suffix (only U+0130 'İ' lowercases into a suffix char, producing 'i'+combining dot U+0307 which cannot end a .fits-family suffix). A 2,000,000-input Unicode-heavy differential fuzz (İ, ſ, ß, ẞ, Σ, ς, combining dot, mixed suffix fragments) comparing ASCII-only lean_lower vs Python str.lower over endswith(KNOWN) produced 0 divergences. axiom_check.py passes (25 boundary + 20000 fuzz).

5) CONTROL-FLOW FAITHFULNESS: monkeypatched the GOLD post-patch is_fits and ran conformance_check.py -> G-CONF OK, 0 disagreements over 100,015 calls (seed 14309), covering path-present-with-args (args ignored), stream-wins-over-path, matching/non-matching paths, and empty-*args IndexError boundary.

No input found where originSpec disagrees with the real gold-patched is_fits under the declared abstraction. Spec is not too strong; it does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (leakage.screen -> passed=True, no hard failures): no diff markers, no reproduced gold-patch line, no patched file path/module, no spec-view identifier embedding a patched symbol, no narration terms. markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True, so the spec region is byte-identical to prepatch. Bundle is strict (no relaxed_leakage flag, no RELAXED_LEAKAGE.md); meta G-LEAK=pass.

Semantic judgment against the PUBLIC problem_statement only (not hints_text): the problem_statement is unusually disclosive here. Its traceback names is_fits in astropy/io/fits/connect.py and shows the full body incl. the exact extension tuple (".fits",".fits.gz",".fit",".fit.gz",".fts",".fts.gz") and the isinstance(args[0], ...) fall-through, and @saimn's quoted note states the root cause/fix: a non-FITS-extension path used to return None and now executes isinstance(args[0], ...) raising IndexError. Every load-bearing element of the spec view maps to already-public content: knownExts = the six suffixes in the traceback; hasKnownExt = the public .lower().endswith((...)); originSpec stream/path/extra branch order = the public is_fits signature/body; Crash.indexOOB = the public IndexError; the 'present path -> return extension verdict outright, never fall through to a trailing positional obs' clause = a restatement of the fix demanded by the public issue. The patched symbol is_fits is itself public (exempt). No spec-view line reveals the gold edit beyond what the public problem_statement already discloses; the spec encodes correct behavior, which is its legitimate job.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
