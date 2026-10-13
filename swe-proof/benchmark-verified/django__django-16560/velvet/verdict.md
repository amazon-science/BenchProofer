# P2 adversarial audit — django__django-16560

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axioms and no deep-model reference to a library callee. Every
@@ -72,9 +72,8 @@
   ensures out = recordedCode supplied
   do
     -- impl-start
-    let mut out : ErrCode := none
-    if supplied ≠ none then
-      out := supplied
+    -- WRONG: never records the supplied code (partial-domain: only the none case)
+    let out : ErrCode := none
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
 /- No consumed axioms and no deep-model reference to a library callee. Every
@@ -90,8 +90,9 @@
   ensures out = withCodeKwarg base code
   do
     -- impl-start
+    -- WRONG (boundary): append an entry even when no code is set
     let out := match code with
-      | none   => base
+      | none   => base ++ [("violation_error_code", [])]
       | some c => base ++ [("violation_error_code", c)]
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
 /- No consumed axioms and no deep-model reference to a library callee. Every
@@ -108,7 +108,8 @@
   ensures out = constraintEq otherEqual codeA codeB
   do
     -- impl-start
-    let out := otherEqual && (codeA == codeB)
+    -- WRONG (control-flow): OR instead of AND
+    let out := otherEqual || (codeA == codeB)
     return out
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
 /- No consumed axioms and no deep-model reference to a library callee. Every
@@ -124,9 +124,8 @@
   ensures out = renderedWithCode base code shown
   do
     -- impl-start
-    let out := match code with
-      | none   => base
-      | some _ => base ++ " violation_error_code=".toList ++ shown
+    -- WRONG (echo): return the base rendering unchanged, dropping the fragment
+    let out := base
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
 /- No consumed axioms and no deep-model reference to a library callee. Every
@@ -144,8 +144,9 @@
   ensures isValid = true → out = Except.ok ()
   do
     -- impl-start
+    -- WRONG: report the violation with no code (base_commit behaviour)
     let out : Except ErrCode Unit :=
-      if isValid then Except.ok () else Except.error code
+      if isValid then Except.ok () else Except.error none
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
 /- No consumed axioms and no deep-model reference to a library callee. Every
@@ -108,7 +108,8 @@
   ensures out = constraintEq otherEqual codeA codeB
   do
     -- impl-start
-    let out := otherEqual && (codeA == codeB)
+    -- WRONG: ignore the codes entirely
+    let out := otherEqual
     return out
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
 /- No consumed axioms and no deep-model reference to a library callee. Every
@@ -144,8 +144,9 @@
   ensures isValid = true → out = Except.ok ()
   do
     -- impl-start
+    -- WRONG (control-flow): swapped branches
     let out : Except ErrCode Unit :=
-      if isValid then Except.ok () else Except.error code
+      if isValid then Except.error code else Except.ok ()
     return out
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
 /- No consumed axioms and no deep-model reference to a library callee. Every
@@ -124,9 +124,10 @@
   ensures out = renderedWithCode base code shown
   do
     -- impl-start
+    -- WRONG (boundary): drop the shown value from the fragment
     let out := match code with
       | none   => base
-      | some _ => base ++ " violation_error_code=".toList ++ shown
+      | some _ => base ++ " violation_error_code=".toList
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. Every
   unchanged sub-computation is modeled as a FREE INPUT, owed no contract because
   the behaviour holds for every value it could take (directive 7): the equality
   of all the OTHER observable fields (`otherEqual`), the base rendering a
   constraint already produces (`base`), the standard value formatter's rendering
   of a single code value (`shown`), the pre-existing serialized bindings
   (`base`), and the validity verdict of an instance against a constraint
   (`isValid`). The one piece of behaviour this bundle pins — how an optional
   error code is surfaced in each observable projection of a constraint — is
   modeled DEEPLY in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A violation error code: a short machine string, or absent (`none`). -/
abbrev ErrCode := Option (List Char)

/- The error code a constraint effectively records: the supplied code when one
   is given, and absent otherwise (the absent default). -/
def recordedCode (supplied : ErrCode) : ErrCode := supplied

/- The serialized keyword bindings of a constraint: the bindings already present
   gain an explicit error-code entry exactly when an error code is set, bound to
   the standard key. The pre-existing bindings (`base`) pass through unchanged. -/
def withCodeKwarg (base : List (String × List Char)) (code : ErrCode) :
    List (String × List Char) :=
  match code with
  | none   => base
  | some c => base ++ [("violation_error_code", c)]

/- Whether two constraints are equal: they agree on all other observable fields
   (`otherEqual`) AND carry the same error code. -/
def constraintEq (otherEqual : Bool) (codeA codeB : ErrCode) : Bool :=
  otherEqual && (codeA == codeB)

/- The textual form of a constraint: the base rendering (`base`) extended with an
   error-code fragment exactly when an error code is set. `shown` is the rendering
   of the code value produced by the standard value formatter (an unchanged
   formatting step), appended after the key fragment. -/
def renderedWithCode (base : List Char) (code : ErrCode) (shown : List Char) :
    List Char :=
  match code with
  | none   => base
  | some _ => base ++ " violation_error_code=".toList ++ shown

/- The outcome of checking one instance against a constraint, on the branch that
   reports a violation through the constraint's own message: acceptance
   (`isValid`) carries nothing; a violation carries the constraint's error code,
   so a caller observes that exact code on the reported error. -/
def checkResult (isValid : Bool) (code : ErrCode) : Except ErrCode Unit :=
  if isValid then Except.ok () else Except.error code
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Record the error code carried by a constraint from the optionally-supplied
   value. `supplied` is read-only (directive 5). Desired behaviour: the recorded
   code is the supplied one when present and absent otherwise. -/
method recordErrorCode (supplied : ErrCode) return (out : ErrCode)
  ensures out = recordedCode supplied
  do
    -- impl-start
    let mut out : ErrCode := none
    if supplied ≠ none then
      out := supplied
    return out
    -- impl-end

prove_correct recordErrorCode by
  loom_solve <;> simp_all [recordedCode]

/- Produce the serialized keyword bindings of a constraint. `base` (the bindings
   already present) and `code` are read-only (directive 5). Desired behaviour: an
   explicit error-code binding is added exactly when an error code is set; the
   pre-existing bindings are preserved unchanged. -/
method serializeWithCode (base : List (String × List Char)) (code : ErrCode)
    return (out : List (String × List Char))
  ensures out = withCodeKwarg base code
  do
    -- impl-start
    let out := match code with
      | none   => base
      | some c => base ++ [("violation_error_code", c)]
    return out
    -- impl-end

prove_correct serializeWithCode by
  loom_solve <;> simp_all [withCodeKwarg]

/- Decide whether two constraints are equal. `otherEqual` (whether all other
   observable fields agree) and the two codes are read-only (directive 5).
   Desired behaviour: equality holds exactly when the other fields agree AND the
   error codes coincide, so two constraints differing only in error code are
   distinguished. -/
method constraintsEqual (otherEqual : Bool) (codeA : ErrCode) (codeB : ErrCode) return (out : Bool)
  ensures out = constraintEq otherEqual codeA codeB
  do
    -- impl-start
    let out := otherEqual && (codeA == codeB)
    return out
    -- impl-end

prove_correct constraintsEqual by
  loom_solve <;> simp_all [constraintEq]

/- Produce the textual form of a constraint. `base` (the base rendering), `code`,
   and `shown` (the value formatter's rendering of the code) are read-only
   (directive 5). Desired behaviour: the error-code fragment is appended exactly
   when an error code is set, leaving the base rendering otherwise untouched. -/
method renderConstraint (base : List Char) (code : ErrCode) (shown : List Char)
    return (out : List Char)
  ensures out = renderedWithCode base code shown
  do
    -- impl-start
    let out := match code with
      | none   => base
      | some _ => base ++ " violation_error_code=".toList ++ shown
    return out
    -- impl-end

prove_correct renderConstraint by
  loom_solve <;> simp_all [renderedWithCode]

/- Check one instance against a constraint on the branch that reports a violation
   through the constraint's own message. `isValid` (the instance's validity
   verdict) and `code` are read-only (directive 5). Desired behaviour: a valid
   instance is accepted with no report; a violation is reported carrying the
   constraint's error code, so the reported error exposes that exact code. -/
method validateWithCode (isValid : Bool) (code : ErrCode) return (out : Except ErrCode Unit)
  ensures out = checkResult isValid code
  ensures isValid = false → out = Except.error code
  ensures isValid = true → out = Except.ok ()
  do
    -- impl-start
    let out : Except ErrCode Unit :=
      if isValid then Except.ok () else Except.error code
    return out
    -- impl-end

prove_correct validateWithCode by
  loom_solve <;> simp_all [checkResult]
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** All same_spec checks True; verified concurrently (≤4 background jobs). Positive control (exact Solution.lean) verifies (lean_verify exit 0). All 8 same-spec wrong impls FAIL to verify (exit 1, genuine 'unsolved goals' proof failures, not syntax errors), so NO verifying wrong impl exists and NO faithful patch needed a resolve run (a verify⇌orrect break requires a *verifying* wrong impl). patches={} accordingly.

**Why the spec is tight:** each method's postcondition is a TOTAL equality `ensures out = <pure fn>` (recordedCode/withCodeKwarg/constraintEq/renderedWithCode/checkResult), forcing any verifying impl to equal the reference pure function on ALL inputs. validateWithCode additionally pins both branches.

Attacks (all same_spec=True, all exit 1):
- atk_1 recordErrorCode partial-domain: always none (drop store) -> unsolved goals @L80.
- atk_2 serializeWithCode boundary: append entry even when code=none -> unsolved goals @L100.
- atk_3 constraintsEqual control-flow: || instead of && -> unsolved goals @L116.
- atk_4 renderConstraint ungrounded-oracle echo: return base unchanged (drop fragment) -> unsolved goals @L132.
- atk_5 validateWithCode: report Except.error none on violation (== prepatch_5 bug) -> unsolved goals @L153, goal shows `(if isValid then ok else error none) = ... error code` mismatch on ensures_2 (isValid=false -> out=Except.error code).
- atk_6 constraintsEqual: ignore codes entirely (out:=otherEqual, == prepatch_3 bug) -> unsolved goals @L116.
- atk_7 validateWithCode control-flow: swapped ok/error branches -> unsolved goals @L153.
- atk_8 renderConstraint boundary: append key fragment WITHOUT shown value -> unsolved goals @L134.
Coverage spans partial-domain, boundary, control-flow-effect, and ungrounded-oracle-echo classes across all five methods; the prepatch bug (prepatch_5) is re-encoded as atk_5 and prepatch_3 as atk_6.

**Prepatch reproduced:** Solution_prepatch_5.lean fails verify (exit 1).

Exact commands:
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('.../velvet/Solution.lean').read(), open('atk_N.lean').read(), b.language))" -> True for all 8 + pos_control.
- verify: bash scripts/lean_verify.sh atk_N.lean (run 4 concurrently as background jobs). pos_control EXIT=0; atk_1..8 EXIT=1.

Refinement audit (refinement.md/mapping.md): every leg is R or I; §F and mapping §3 declare NO consumed axiom, NO A-reference, NO kind-3 leg (G-AX skips, confirmed meta G-AX=skip). The four unchanged sub-computations (otherEqual, base, shown, isValid) are correctly modeled as FREE INPUTS owed no contract (the pinned behaviour holds for every value). The R bijections (str|None↔Option (List Char); dict↔ordered assoc list; repr↔List Char; ValidationError(code)↔Except ErrCode Unit) are faithful to the gold hunks in patch.diff (BaseConstraint.`__init__`/deconstruct, Check/Unique `__eq__`/`__repr__`/validate). Scope note (uncovered UniqueConstraint fields branch keeping code='unique_together') is legitimate under-claiming, not a weakness. No A-legs to falsify.

**Context note:** prior recorded meta G-EQ=fail and G-PANEL-1=fail were both 'INCONCLUSIVE — 1 attack inconclusive' (fail-closed protocol artifact where an attack/resolve couldn't complete), NOT a spec-too-weak verdict. This run completed all 8 attacks + positive control cleanly.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. Every
   unchanged sub-computation is modeled as a FREE INPUT, owed no contract because
   the behaviour holds for every value it could take (directive 7): the equality
   of all the OTHER observable fields (`otherEqual`), the base rendering a
   constraint already produces (`base`), the standard value formatter's rendering
   of a single code value (`shown`), the pre-existing serialized bindings
   (`base`), and the validity verdict of an instance against a constraint
   (`isValid`). The one piece of behaviour this bundle pins — how an optional
   error code is surfaced in each observable projection of a constraint — is
   modeled DEEPLY in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A violation error code: a short machine string, or absent (`none`). -/
abbrev ErrCode := Option (List Char)

/- The error code a constraint effectively records: the supplied code when one
   is given, and absent otherwise (the absent default). -/
def recordedCode (supplied : ErrCode) : ErrCode := supplied

/- The serialized keyword bindings of a constraint: the bindings already present
   gain an explicit error-code entry exactly when an error code is set, bound to
   the standard key. The pre-existing bindings (`base`) pass through unchanged. -/
def withCodeKwarg (base : List (String × List Char)) (code : ErrCode) :
    List (String × List Char) :=
  match code with
  | none   => base
  | some c => base ++ [("violation_error_code", c)]

/- Whether two constraints are equal: they agree on all other observable fields
   (`otherEqual`) AND carry the same error code. -/
def constraintEq (otherEqual : Bool) (codeA codeB : ErrCode) : Bool :=
  otherEqual && (codeA == codeB)

/- The textual form of a constraint: the base rendering (`base`) extended with an
   error-code fragment exactly when an error code is set. `shown` is the rendering
   of the code value produced by the standard value formatter (an unchanged
   formatting step), appended after the key fragment. -/
def renderedWithCode (base : List Char) (code : ErrCode) (shown : List Char) :
    List Char :=
  match code with
  | none   => base
  | some _ => base ++ " violation_error_code=".toList ++ shown

/- The outcome of checking one instance against a constraint, on the branch that
   reports a violation through the constraint's own message: acceptance
   (`isValid`) carries nothing; a violation carries the constraint's error code,
   so a caller observes that exact code on the reported error. -/
def checkResult (isValid : Bool) (code : ErrCode) : Except ErrCode Unit :=
  if isValid then Except.ok () else Except.error code
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Record the error code carried by a constraint from the optionally-supplied
   value. `supplied` is read-only (directive 5). Desired behaviour: the recorded
   code is the supplied one when present and absent otherwise. -/
method recordErrorCode (supplied : ErrCode) return (out : ErrCode)
  ensures out = recordedCode supplied
  do
    -- impl-start
    let mut out : ErrCode := none
    if supplied ≠ none then
      out := supplied
    return out
    -- impl-end

prove_correct recordErrorCode by
  loom_solve <;> simp_all [recordedCode]

/- Produce the serialized keyword bindings of a constraint. `base` (the bindings
   already present) and `code` are read-only (directive 5). Desired behaviour: an
   explicit error-code binding is added exactly when an error code is set; the
   pre-existing bindings are preserved unchanged. -/
method serializeWithCode (base : List (String × List Char)) (code : ErrCode)
    return (out : List (String × List Char))
  ensures out = withCodeKwarg base code
  do
    -- impl-start
    let out := match code with
      | none   => base
      | some c => base ++ [("violation_error_code", c)]
    return out
    -- impl-end

prove_correct serializeWithCode by
  loom_solve <;> simp_all [withCodeKwarg]

/- Decide whether two constraints are equal. `otherEqual` (whether all other
   observable fields agree) and the two codes are read-only (directive 5).
   Desired behaviour: equality holds exactly when the other fields agree AND the
   error codes coincide, so two constraints differing only in error code are
   distinguished. -/
method constraintsEqual (otherEqual : Bool) (codeA : ErrCode) (codeB : ErrCode) return (out : Bool)
  ensures out = constraintEq otherEqual codeA codeB
  do
    -- impl-start
    let out := otherEqual && (codeA == codeB)
    return out
    -- impl-end

prove_correct constraintsEqual by
  loom_solve <;> simp_all [constraintEq]

/- Produce the textual form of a constraint. `base` (the base rendering), `code`,
   and `shown` (the value formatter's rendering of the code) are read-only
   (directive 5). Desired behaviour: the error-code fragment is appended exactly
   when an error code is set, leaving the base rendering otherwise untouched. -/
method renderConstraint (base : List Char) (code : ErrCode) (shown : List Char)
    return (out : List Char)
  ensures out = renderedWithCode base code shown
  do
    -- impl-start
    let out := match code with
      | none   => base
      | some _ => base ++ " violation_error_code=".toList ++ shown
    return out
    -- impl-end

prove_correct renderConstraint by
  loom_solve <;> simp_all [renderedWithCode]

/- Check one instance against a constraint on the branch that reports a violation
   through the constraint's own message. `isValid` (the instance's validity
   verdict) and `code` are read-only (directive 5). Desired behaviour: a valid
   instance is accepted with no report; a violation is reported carrying the
   constraint's error code, so the reported error exposes that exact code. -/
method validateWithCode (isValid : Bool) (code : ErrCode) return (out : Except ErrCode Unit)
  ensures out = checkResult isValid code
  ensures isValid = false → out = Except.error code
  ensures isValid = true → out = Except.ok ()
  do
    -- impl-start
    let out : Except ErrCode Unit :=
      if isValid then Except.ok () else Except.error code
    return out
    -- impl-end

prove_correct validateWithCode by
  loom_solve <;> simp_all [checkResult]
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** All same_spec checks True; verified concurrently (≤4 background jobs). Positive control (exact Solution.lean) verifies (lean_verify exit 0). All 8 same-spec wrong impls FAIL to verify (exit 1, genuine 'unsolved goals' proof failures, not syntax errors), so NO verifying wrong impl exists and NO faithful patch needed a resolve run (a verify⇌orrect break requires a *verifying* wrong impl). patches={} accordingly.

**Why the spec is tight:** each method's postcondition is a TOTAL equality `ensures out = <pure fn>` (recordedCode/withCodeKwarg/constraintEq/renderedWithCode/checkResult), forcing any verifying impl to equal the reference pure function on ALL inputs. validateWithCode additionally pins both branches.

Attacks (all same_spec=True, all exit 1):
- atk_1 recordErrorCode partial-domain: always none (drop store) -> unsolved goals @L80.
- atk_2 serializeWithCode boundary: append entry even when code=none -> unsolved goals @L100.
- atk_3 constraintsEqual control-flow: || instead of && -> unsolved goals @L116.
- atk_4 renderConstraint ungrounded-oracle echo: return base unchanged (drop fragment) -> unsolved goals @L132.
- atk_5 validateWithCode: report Except.error none on violation (== prepatch_5 bug) -> unsolved goals @L153, goal shows `(if isValid then ok else error none) = ... error code` mismatch on ensures_2 (isValid=false -> out=Except.error code).
- atk_6 constraintsEqual: ignore codes entirely (out:=otherEqual, == prepatch_3 bug) -> unsolved goals @L116.
- atk_7 validateWithCode control-flow: swapped ok/error branches -> unsolved goals @L153.
- atk_8 renderConstraint boundary: append key fragment WITHOUT shown value -> unsolved goals @L134.
Coverage spans partial-domain, boundary, control-flow-effect, and ungrounded-oracle-echo classes across all five methods; the prepatch bug (prepatch_5) is re-encoded as atk_5 and prepatch_3 as atk_6.

**Prepatch reproduced:** Solution_prepatch_5.lean fails verify (exit 1).

Exact commands:
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('.../velvet/Solution.lean').read(), open('atk_N.lean').read(), b.language))" -> True for all 8 + pos_control.
- verify: bash scripts/lean_verify.sh atk_N.lean (run 4 concurrently as background jobs). pos_control EXIT=0; atk_1..8 EXIT=1.

Refinement audit (refinement.md/mapping.md): every leg is R or I; §F and mapping §3 declare NO consumed axiom, NO A-reference, NO kind-3 leg (G-AX skips, confirmed meta G-AX=skip). The four unchanged sub-computations (otherEqual, base, shown, isValid) are correctly modeled as FREE INPUTS owed no contract (the pinned behaviour holds for every value). The R bijections (str|None↔Option (List Char); dict↔ordered assoc list; repr↔List Char; ValidationError(code)↔Except ErrCode Unit) are faithful to the gold hunks in patch.diff (BaseConstraint.`__init__`/deconstruct, Check/Unique `__eq__`/`__repr__`/validate). Scope note (uncovered UniqueConstraint fields branch keeping code='unique_together') is legitimate under-claiming, not a weakness. No A-legs to falsify.

**Context note:** prior recorded meta G-EQ=fail and G-PANEL-1=fail were both 'INCONCLUSIVE — 1 attack inconclusive' (fail-closed protocol artifact where an attack/resolve couldn't complete), NOT a spec-too-weak verdict. This run completed all 8 attacks + positive control cleanly.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) audit of django__django-16560 velvet bundle. Five modeled functions (recordedCode, withCodeKwarg, constraintEq, renderedWithCode, checkResult) each mirror the gold-patched real callees in django/db/models/constraints.py. Verification performed: (1) same_spec returns True for all 5 prepatch files vs Solution.lean — spec region byte-identical, not tuned to the impl; (2) Solution.lean elaborates cleanly (lean_verify exit 0, only cosmetic <;> linter warnings); (3) ran conformance_check.py with PYTHONPATH on a fresh worktree at base_commit 51c9bb7c + gold patch applied: 0 disagreements over 100,000 inputs plus exhaustive boundary sweep; (4) independent adversarial probes confirmed real repo behavior matches each modeled function: recordedCode=supplied (None class default + `is not None` guard returns supplied incl. None), deconstruct adds kwarg iff code set, `__eq__` distinguishes differing codes and equates matching ones, `__repr__` appends fragment iff code set, validate carries exc.code exactly for None/''/'x'/'unique'. The extra validateWithCode ensures clauses (isValid=false→error code, isValid=true→ok) are consistent and match real behavior — not an over-claim. The deliberately-uncovered UniqueConstraint fields branch (code='unique_together') is modeled away via the free isValid input and the spec makes no claim there, so it cannot contradict the real repo — an under-claim (G-EQ territory) at worst, not a faithfulness defect. No input found where a modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (leakage.screen over the velvet spec_view: no diff markers, no verbatim gold-patch line, no patched file/module path, no spec-view identifier or comment embedding a distinctive patched symbol {deconstruct, repr, clone, remove_sql}; 'validate' is already public via the problem_statement 'BaseConstraint.validate'). same_spec holds byte-identical between Solution.lean and all five Solution_prepatch_{1..5}.lean, so the spec view is stable and reveals nothing that varies with the fix.

Semantic review of the spec view beyond problem_statement: the only concrete repo-derived token surfaced is `violation_error_code` (appears twice: the deconstruct kwarg key and the repr fragment). This is a direct, trivial parallel of the PUBLIC problem_statement, which explicitly names the existing `violation_error_message` parameter, asks to 'customize the code attribute of ValidationError', and cites the docs recommendation to 'Provide a descriptive error code to the constructor'. Deriving the name `violation_error_code` from 'add a code parameter analogous to violation_error_message' is exactly the public task, not leaked gold-edit localization.

The five modeled methods map 1:1 to the five gold touchpoints (init-store, deconstruct, `__eq__`, `__repr__`, validate), but each is described ABSTRACTLY as behavior — 'the code a constraint records', 'the serialized keyword bindings', 'whether two constraints are equal', 'the textual form', 'the violation report carrying the code'. The spec view never names `__repr__`/deconstruct/`__eq__`/kwargs, the file path (django/db/models/constraints.py), migrations, or any diff line. The narrative doc mapping.md/refinement.md quotes gold hunks and file:line, but those are auditor-facing docs, NOT part of the consumer spec view screened by G-PANEL-3 (spec_view elides impl/proof and the screen operates only on the projected view). No bug/fix narration terms in comments.

**Conclusion:** the spec view discloses only what the public problem_statement already discloses (an optional error code analogous to violation_error_message). No line leaks the gold edit beyond problem_statement. Recorded G-LEAK=pass and relaxed_leakage=None are consistent.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
