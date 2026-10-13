# P2 adversarial audit — django__django-13821

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_posc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -64,11 +64,13 @@
   ensures out = checkSpec info versionStr
   do
     -- impl-start
-    -- Fail with the diagnostic exactly when the reported version sorts below the
-    -- required minimum; otherwise succeed.
-    let tooOld : Bool := lexLt info [3, 9, 0]
+    -- ATTACK 1 (prepatch bug): lower threshold [3,8,3] and the 3.8.3 diagnostic.
+    let tooOld : Bool := lexLt info [3, 8, 3]
     let out : Except (List Char) Unit :=
-      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()
+      if tooOld then
+        Except.error ("SQLite 3.8.3 or later is required (found ".toList
+                        ++ versionStr ++ ").".toList)
+      else Except.ok ()
     return out
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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -64,11 +64,8 @@
   ensures out = checkSpec info versionStr
   do
     -- impl-start
-    -- Fail with the diagnostic exactly when the reported version sorts below the
-    -- required minimum; otherwise succeed.
-    let tooOld : Bool := lexLt info [3, 9, 0]
-    let out : Except (List Char) Unit :=
-      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()
+    -- ATTACK 2 (never-raise / partial-domain always-ok): ignores the version.
+    let out : Except (List Char) Unit := Except.ok ()
     return out
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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -64,9 +64,9 @@
   ensures out = checkSpec info versionStr
   do
     -- impl-start
-    -- Fail with the diagnostic exactly when the reported version sorts below the
-    -- required minimum; otherwise succeed.
-    let tooOld : Bool := lexLt info [3, 9, 0]
+    -- ATTACK 3 (boundary: raise on <= min, i.e. use `!(min < info)` = includes equality).
+    -- tooOld true iff info is NOT strictly above requiredVersion, so (3,9,0) wrongly raises.
+    let tooOld : Bool := !(lexLt [3, 9, 0] info)
     let out : Except (List Char) Unit :=
       if tooOld then Except.error (errorMessage versionStr) else Except.ok ()
     return out
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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -64,11 +64,10 @@
   ensures out = checkSpec info versionStr
   do
     -- impl-start
-    -- Fail with the diagnostic exactly when the reported version sorts below the
-    -- required minimum; otherwise succeed.
+    -- ATTACK 4 (control-flow-effect: right condition but swap ok/error branches -> inverted).
     let tooOld : Bool := lexLt info [3, 9, 0]
     let out : Except (List Char) Unit :=
-      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()
+      if tooOld then Except.ok () else Except.error (errorMessage versionStr)
     return out
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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -64,11 +64,10 @@
   ensures out = checkSpec info versionStr
   do
     -- impl-start
-    -- Fail with the diagnostic exactly when the reported version sorts below the
-    -- required minimum; otherwise succeed.
+    -- ATTACK 5 (wrong message: correct condition/threshold, but drops the echoed version).
     let tooOld : Bool := lexLt info [3, 9, 0]
     let out : Except (List Char) Unit :=
-      if tooOld then Except.error (errorMessage versionStr) else Except.ok ()
+      if tooOld then Except.error (errorMessage []) else Except.ok ()
     return out
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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -64,9 +64,9 @@
   ensures out = checkSpec info versionStr
   do
     -- impl-start
-    -- Fail with the diagnostic exactly when the reported version sorts below the
-    -- required minimum; otherwise succeed.
-    let tooOld : Bool := lexLt info [3, 9, 0]
+    -- ATTACK 6 (off-by-one threshold: use [3, 9, 1] instead of the required minimum).
+    -- Wrongly raises for versions in [(3,9,0),(3,9,1)) that the spec accepts.
+    let tooOld : Bool := lexLt info [3, 9, 1]
     let out : Except (List Char) Unit :=
       if tooOld then Except.error (errorMessage versionStr) else Except.ok ()
     return out
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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -64,9 +64,11 @@
   ensures out = checkSpec info versionStr
   do
     -- impl-start
-    -- Fail with the diagnostic exactly when the reported version sorts below the
-    -- required minimum; otherwise succeed.
-    let tooOld : Bool := lexLt info [3, 9, 0]
+    -- ATTACK 7 (partial-domain / two-major-compare only): compares only the first
+    -- two components, so e.g. (3, 8, 500) is judged >= min wrongly? No: it compares
+    -- info against [3, 9] instead of [3, 9, 0]. Under lexLt, (3,9,0) < (3,9) is FALSE
+    -- (prefix ranks below extension: [3,9] < [3,9,0]), so [3,9] as threshold differs.
+    let tooOld : Bool := lexLt info [3, 9]
     let out : Except (List Char) Unit :=
       if tooOld then Except.error (errorMessage versionStr) else Except.ok ()
     return out
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
 /- No consumed axioms and no deep-model references to unchanged callees. The
@@ -64,9 +64,9 @@
   ensures out = checkSpec info versionStr
   do
     -- impl-start
-    -- Fail with the diagnostic exactly when the reported version sorts below the
-    -- required minimum; otherwise succeed.
-    let tooOld : Bool := lexLt info [3, 9, 0]
+    -- ATTACK 8 (reversed comparison operands: raise when info sorts ABOVE the min).
+    -- Correct message, but the guard direction is flipped via operand swap.
+    let tooOld : Bool := lexLt [3, 9, 0] info
     let out : Except (List Char) Unit :=
       if tooOld then Except.error (errorMessage versionStr) else Except.ok ()
     return out
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_posc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references to unchanged callees. The
   operations this slice relies on — lexicographic comparison of the version
   tuple and assembly of the diagnostic message — are language primitives,
   modeled directly in the `pure` region (concrete I-ops) and refinement-checked
   against the real behaviour by conformance_check.py (G-CONF), mapping.md §3. -/
-- axioms-end

-- pure-start
/- Lexicographic strict order on version tuples, modeled as natural-number
   sequences. Mirrors the total ordering of the runtime version-info tuple:
   compare component by component; a shorter tuple that is a prefix of a longer
   one ranks below it (e.g. `[3, 9]` precedes `[3, 9, 0]`). Front-recursive so a
   single unfold is available per comparison step. -/
def lexLt : List Nat → List Nat → Bool
  | [],      []      => false
  | [],      _ :: _  => true
  | _ :: _,  []      => false
  | a :: xs, b :: ys =>
      if a < b then true
      else if b < a then false
      else lexLt xs ys

/- The minimum version the database must report. -/
def requiredVersion : List Nat := [3, 9, 0]

/- The diagnostic the operation surfaces when the reported version is below the
   minimum: it states the required version and echoes the version actually
   found. -/
def errorMessage (versionStr : List Char) : List Char :=
  "SQLite 3.9.0 or later is required (found ".toList ++ versionStr ++ ").".toList

/- The intended outcome: when the reported version sorts below the required
   minimum, the check fails with the diagnostic; otherwise it succeeds with no
   value. -/
def checkSpec (info : List Nat) (versionStr : List Char) : Except (List Char) Unit :=
  if lexLt info requiredVersion then Except.error (errorMessage versionStr)
  else Except.ok ()

@[simp, grind] lemma requiredVersion_eq : requiredVersion = [3, 9, 0] := rfl

@[grind] lemma checkSpec_def (info : List Nat) (versionStr : List Char) :
    checkSpec info versionStr =
      (if lexLt info requiredVersion then Except.error (errorMessage versionStr)
       else Except.ok ()) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method verifyVersion (info : List Nat) (versionStr : List Char)
    return (out : Except (List Char) Unit)
  ensures out = checkSpec info versionStr
  do
    -- impl-start
    -- POSITIVE CONTROL: behaviourally correct, structurally different (named def
    -- `requiredVersion` + a `match` on the Bool instead of the literal `if`).
    let belowMin : Bool := lexLt info requiredVersion
    let out : Except (List Char) Unit :=
      match belowMin with
      | true  => Except.error (errorMessage versionStr)
      | false => Except.ok ()
    return out
    -- impl-end

prove_correct verifyVersion by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec is a single fully-concrete clause `ensures out = checkSpec info versionStr`, where checkSpec/lexLt/requiredVersion=[3,9,0]/errorMessage are all concrete pure defs. No axioms and no deep-model references (meta.json axioms=[], deep_model_references=[]), so there are NO A-legs to attack; every refinement.md leg is R (List Nat/List Char/Except bijections) or I (tuple < = lexLt; %-message = errorMessage concat). refinement.md §C 'no kind-3' is accurate; the model↔patch correspondence holds — mapping.md binds verifyVersion to check_sqlite_version at base.py:66, threshold (3,9,0), message '3.9.0'.

 All 9 files pass same_spec (velvet) = True vs the frozen Solution.lean (impl region edited only). Verifications run concurrently (batches of 4) via `bash scripts/lean_verify.sh <f>`:

WRONG IMPLS — all REJECTED (exit 1), each on goal `... = checkSpec info versionStr`:
- atk_1 prepatch bug: threshold [3,8,3] + '3.8.3' message. exit 1.
- atk_2 partial-domain/never-raise: return Except.ok (). exit 1 (goal `Except.ok () = checkSpec ...`).
- atk_3 boundary: raise on <= min via !(lexLt [3,9,0] info) so (3,9,0) wrongly raises. exit 1.
- atk_4 control-flow-effect: correct condition, ok/error branches swapped (inverted). exit 1.
- atk_5 ungrounded/wrong-message: errorMessage [] drops the echoed versionStr. exit 1.
- atk_6 off-by-one threshold [3,9,1]. exit 1.
- atk_7 partial threshold [3,9] (prefix ranks below [3,9,0]). exit 1.
- atk_8 reversed operands: lexLt [3,9,0] info (raise when ABOVE min). exit 1.

POSITIVE CONTROL: atk_posc (named requiredVersion + match on Bool, structurally different but behaviourally correct) VERIFIES exit 0 -> spec non-vacuous.

Prepatch reproduced: bundle Solution_prepatch.lean fails for the right reason (G-DIFF=pass); atk_1 independently reproduces the prepatch bug and is rejected.

No verifying-but-wrong candidate exists, therefore no faithful refined patch needs a resolve run (patches={}), and verify=>correct is not falsified. Meta gates independently confirm: G-VERIFY/G-DIFF/G-EQ/G-CONF/G-RESOLVE/G-MUT/G-PANEL-1 all pass; G-AX skip (no axioms). Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_posc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_posc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references to unchanged callees. The
   operations this slice relies on — lexicographic comparison of the version
   tuple and assembly of the diagnostic message — are language primitives,
   modeled directly in the `pure` region (concrete I-ops) and refinement-checked
   against the real behaviour by conformance_check.py (G-CONF), mapping.md §3. -/
-- axioms-end

-- pure-start
/- Lexicographic strict order on version tuples, modeled as natural-number
   sequences. Mirrors the total ordering of the runtime version-info tuple:
   compare component by component; a shorter tuple that is a prefix of a longer
   one ranks below it (e.g. `[3, 9]` precedes `[3, 9, 0]`). Front-recursive so a
   single unfold is available per comparison step. -/
def lexLt : List Nat → List Nat → Bool
  | [],      []      => false
  | [],      _ :: _  => true
  | _ :: _,  []      => false
  | a :: xs, b :: ys =>
      if a < b then true
      else if b < a then false
      else lexLt xs ys

/- The minimum version the database must report. -/
def requiredVersion : List Nat := [3, 9, 0]

/- The diagnostic the operation surfaces when the reported version is below the
   minimum: it states the required version and echoes the version actually
   found. -/
def errorMessage (versionStr : List Char) : List Char :=
  "SQLite 3.9.0 or later is required (found ".toList ++ versionStr ++ ").".toList

/- The intended outcome: when the reported version sorts below the required
   minimum, the check fails with the diagnostic; otherwise it succeeds with no
   value. -/
def checkSpec (info : List Nat) (versionStr : List Char) : Except (List Char) Unit :=
  if lexLt info requiredVersion then Except.error (errorMessage versionStr)
  else Except.ok ()

@[simp, grind] lemma requiredVersion_eq : requiredVersion = [3, 9, 0] := rfl

@[grind] lemma checkSpec_def (info : List Nat) (versionStr : List Char) :
    checkSpec info versionStr =
      (if lexLt info requiredVersion then Except.error (errorMessage versionStr)
       else Except.ok ()) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method verifyVersion (info : List Nat) (versionStr : List Char)
    return (out : Except (List Char) Unit)
  ensures out = checkSpec info versionStr
  do
    -- impl-start
    -- POSITIVE CONTROL: behaviourally correct, structurally different (named def
    -- `requiredVersion` + a `match` on the Bool instead of the literal `if`).
    let belowMin : Bool := lexLt info requiredVersion
    let out : Except (List Char) Unit :=
      match belowMin with
      | true  => Except.error (errorMessage versionStr)
      | false => Except.ok ()
    return out
    -- impl-end

prove_correct verifyVersion by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec is a single fully-concrete clause `ensures out = checkSpec info versionStr`, where checkSpec/lexLt/requiredVersion=[3,9,0]/errorMessage are all concrete pure defs. No axioms and no deep-model references (meta.json axioms=[], deep_model_references=[]), so there are NO A-legs to attack; every refinement.md leg is R (List Nat/List Char/Except bijections) or I (tuple < = lexLt; %-message = errorMessage concat). refinement.md §C 'no kind-3' is accurate; the model↔patch correspondence holds — mapping.md binds verifyVersion to check_sqlite_version at base.py:66, threshold (3,9,0), message '3.9.0'.

 All 9 files pass same_spec (velvet) = True vs the frozen Solution.lean (impl region edited only). Verifications run concurrently (batches of 4) via `bash scripts/lean_verify.sh <f>`:

WRONG IMPLS — all REJECTED (exit 1), each on goal `... = checkSpec info versionStr`:
- atk_1 prepatch bug: threshold [3,8,3] + '3.8.3' message. exit 1.
- atk_2 partial-domain/never-raise: return Except.ok (). exit 1 (goal `Except.ok () = checkSpec ...`).
- atk_3 boundary: raise on <= min via !(lexLt [3,9,0] info) so (3,9,0) wrongly raises. exit 1.
- atk_4 control-flow-effect: correct condition, ok/error branches swapped (inverted). exit 1.
- atk_5 ungrounded/wrong-message: errorMessage [] drops the echoed versionStr. exit 1.
- atk_6 off-by-one threshold [3,9,1]. exit 1.
- atk_7 partial threshold [3,9] (prefix ranks below [3,9,0]). exit 1.
- atk_8 reversed operands: lexLt [3,9,0] info (raise when ABOVE min). exit 1.

POSITIVE CONTROL: atk_posc (named requiredVersion + match on Bool, structurally different but behaviourally correct) VERIFIES exit 0 -> spec non-vacuous.

Prepatch reproduced: bundle Solution_prepatch.lean fails for the right reason (G-DIFF=pass); atk_1 independently reproduces the prepatch bug and is rejected.

No verifying-but-wrong candidate exists, therefore no faithful refined patch needs a resolve run (patches={}), and verify=>correct is not falsified. Meta gates independently confirm: G-VERIFY/G-DIFF/G-EQ/G-CONF/G-RESOLVE/G-MUT/G-PANEL-1 all pass; G-AX skip (no axioms). Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-13821 velvet. Spec region byte-identical post vs prepatch (swebench_unified.markers.same_spec = True with velvet backend); spec is frozen. Real patched callee at base_commit (gold applied): check_sqlite_version raises ImproperlyConfigured('SQLite 3.9.0 or later is required (found %s).' % Database.sqlite_version) iff Database.sqlite_version_info <. Model checkSpec info versionStr = if lexLt info [3,9,0] then error(errorMessage versionStr) else ok. lexLt faithfully models Python tuple '<' incl. prefix-below-extension ((3,9)<(3,9,0)=true; (3,9,0,1)<(3,9,0)=false). errorMessage reproduces the %s interpolation verbatim; threshold and message text are the post-patch (3,9,0)/'3.9.0'. Fuzzed 200k random version tuples (seed 13821) shadow==oracle semantics: 0 disagreements, incl. boundaries (3,9,0), (3,8,3), F2P (3,8,11,1). Solution.lean elaborates clean (lean_verify exit 0); Solution_prepatch.lean genuinely fails the ensures goal (unsolved: threshold [3,8,3]/'3.8.3'), so the spec is discriminating, not vacuous nor too weak. No input where the model disagrees with the real repo could be found — spec is not too strong and does not drift. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction) verdict: NO-LEAKAGE for django__django-13821 velvet.

Method: rendered the consumer spec view with markers.spec_view(Solution.lean, VelvetBackend.language) and verified spec-region byte-identity with same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True. Ran leakage.screen against the frozen row: passed=True, hard_failures=[]. Changed symbols extracted={'list_aggregate'} (a context header, not in spec view); changed files=['django/db/backends/sqlite3/base.py'] (absent from spec view).

Gold edit = raise SQLite version threshold (3,8,3)->(3,9,0) and reword the diagnostic to name 3.9.0, in check_sqlite_version() of django/db/backends/sqlite3/base.py.

Public problem_statement already discloses the entire discriminating value: 'Drop support for SQLite < 3.9.0', 'supported on SQLite 3.9.0+', 'SQLite 3.9.0 was released in October 2015.' Thus the constant 3.9.0 that the spec view pins (requiredVersion := [3,9,0]; errorMessage naming '3.9.0') is fully public — no leakage beyond problem_statement.

What the spec view does NOT reveal beyond the public statement: (1) no patched file path or module path; (2) no diff markers; (3) the changed function name check_sqlite_version is abstracted to verifyVersion (not present); (4) the PRE-patch value 3.8.3 / old message is absent — the spec view is identical to the prepatch skeleton's spec view (same_spec=True), so it does not disclose the pre->post transition or edit direction; (5) no bug/fix/narration terms; comments describe intended behavior abstractly ('the minimum version the database must report', 'the version guard').

The exact error string 'SQLite 3.9.0 or later is required (found ...)' is not verbatim in problem_statement, but pinning required observable output is legitimate behavioral specification (it is what the hidden F2P test asserts), and its only discriminating token, 3.9.0, is public. This exposes no edit-localization or gold-reconstruction information beyond the public task. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
