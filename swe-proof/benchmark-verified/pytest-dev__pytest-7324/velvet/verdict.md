# P2 adversarial audit — pytest-dev__pytest-7324

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -61,21 +61,16 @@
   ensures out = Except.ok (matcher ident)
   do
     -- impl-start
-    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
-    -- is a character that can never begin a bound name the user could write),
-    -- then look the original identifier up through the matcher.
-    let identPrefix : List Char := ['$']
-    let name : List Char := identPrefix ++ ident
+    let name : List Char := ident
     let compiled : Except CompileErr Unit := compileName name
-    let key : List Char := name.drop identPrefix.length
+    let key : List Char := name
     let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
     return out
     -- impl-end
 
 prove_correct evalBareIdent by
   loom_solve
-  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp
-  have hok : compileName (['$'] ++ ident) = Except.ok () := by
-    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
+  have hok : compileName ident = Except.ok () := by
+    have h : isReservedName ident = false := by unfold isReservedName; simp
     unfold compileName; rw [h]; rfl
-  rw [hok, hkey]; rfl
+  rw [hok]; rfl
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
 -- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -61,13 +61,10 @@
   ensures out = Except.ok (matcher ident)
   do
     -- impl-start
-    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
-    -- is a character that can never begin a bound name the user could write),
-    -- then look the original identifier up through the matcher.
     let identPrefix : List Char := ['$']
     let name : List Char := identPrefix ++ ident
     let compiled : Except CompileErr Unit := compileName name
-    let key : List Char := name.drop identPrefix.length
+    let key : List Char := name
     let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
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
 -- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -61,13 +61,10 @@
   ensures out = Except.ok (matcher ident)
   do
     -- impl-start
-    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
-    -- is a character that can never begin a bound name the user could write),
-    -- then look the original identifier up through the matcher.
     let identPrefix : List Char := ['$']
     let name : List Char := identPrefix ++ ident
     let compiled : Except CompileErr Unit := compileName name
-    let key : List Char := name.drop identPrefix.length
+    let key : List Char := name.drop 2
     let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
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
 -- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -61,14 +61,11 @@
   ensures out = Except.ok (matcher ident)
   do
     -- impl-start
-    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
-    -- is a character that can never begin a bound name the user could write),
-    -- then look the original identifier up through the matcher.
     let identPrefix : List Char := ['$']
     let name : List Char := identPrefix ++ ident
     let compiled : Except CompileErr Unit := compileName name
     let key : List Char := name.drop identPrefix.length
-    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
+    let out : Except CompileErr Bool := compiled.map (fun _ => !(matcher key))
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
 -- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -61,21 +61,9 @@
   ensures out = Except.ok (matcher ident)
   do
     -- impl-start
-    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
-    -- is a character that can never begin a bound name the user could write),
-    -- then look the original identifier up through the matcher.
-    let identPrefix : List Char := ['$']
-    let name : List Char := identPrefix ++ ident
-    let compiled : Except CompileErr Unit := compileName name
-    let key : List Char := name.drop identPrefix.length
-    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
+    let out : Except CompileErr Bool := Except.ok true
     return out
     -- impl-end
 
 prove_correct evalBareIdent by
   loom_solve
-  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp
-  have hok : compileName (['$'] ++ ident) = Except.ok () := by
-    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
-    unfold compileName; rw [h]; rfl
-  rw [hok, hkey]; rfl
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -61,21 +61,9 @@
   ensures out = Except.ok (matcher ident)
   do
     -- impl-start
-    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
-    -- is a character that can never begin a bound name the user could write),
-    -- then look the original identifier up through the matcher.
-    let identPrefix : List Char := ['$']
-    let name : List Char := identPrefix ++ ident
-    let compiled : Except CompileErr Unit := compileName name
-    let key : List Char := name.drop identPrefix.length
-    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
+    let out : Except CompileErr Bool := Except.ok (matcher ident)
     return out
     -- impl-end
 
 prove_correct evalBareIdent by
   loom_solve
-  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp
-  have hok : compileName (['$'] ++ ident) = Except.ok () := by
-    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
-    unfold compileName; rw [h]; rfl
-  rw [hok, hkey]; rfl
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -61,10 +61,7 @@
   ensures out = Except.ok (matcher ident)
   do
     -- impl-start
-    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
-    -- is a character that can never begin a bound name the user could write),
-    -- then look the original identifier up through the matcher.
-    let identPrefix : List Char := ['$']
+    let identPrefix : List Char := ['#']
     let name : List Char := identPrefix ++ ident
     let compiled : Except CompileErr Unit := compileName name
     let key : List Char := name.drop identPrefix.length
@@ -74,8 +71,8 @@
 
 prove_correct evalBareIdent by
   loom_solve
-  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp
-  have hok : compileName (['$'] ++ ident) = Except.ok () := by
-    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
+  have hkey : List.drop ['#'].length (['#'] ++ ident) = ident := by simp
+  have hok : compileName (['#'] ++ ident) = Except.ok () := by
+    have h : isReservedName (['#'] ++ ident) = false := by unfold isReservedName; simp
     unfold compileName; rw [h]; rfl
   rw [hok, hkey]; rfl
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -61,10 +61,7 @@
   ensures out = Except.ok (matcher ident)
   do
     -- impl-start
-    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
-    -- is a character that can never begin a bound name the user could write),
-    -- then look the original identifier up through the matcher.
-    let identPrefix : List Char := ['$']
+    let identPrefix : List Char := ['$', '$']
     let name : List Char := identPrefix ++ ident
     let compiled : Except CompileErr Unit := compileName name
     let key : List Char := name.drop identPrefix.length
@@ -74,8 +71,8 @@
 
 prove_correct evalBareIdent by
   loom_solve
-  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp
-  have hok : compileName (['$'] ++ ident) = Except.ok () := by
-    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
+  have hkey : List.drop ['$', '$'].length (['$', '$'] ++ ident) = ident := by simp
+  have hok : compileName (['$', '$'] ++ ident) = Except.ok () := by
+    have h : isReservedName (['$', '$'] ++ ident) = false := by unfold isReservedName; simp
     unfold compileName; rw [h]; rfl
   rw [hok, hkey]; rfl
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No consumed axioms. The one unchanged callee this slice relies on — the
@@ -61,21 +61,23 @@
   ensures out = Except.ok (matcher ident)
   do
     -- impl-start
-    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
-    -- is a character that can never begin a bound name the user could write),
-    -- then look the original identifier up through the matcher.
-    let identPrefix : List Char := ['$']
-    let name : List Char := identPrefix ++ ident
+    let name : List Char := if isReservedName ident then ['$'] ++ ident else ident
     let compiled : Except CompileErr Unit := compileName name
-    let key : List Char := name.drop identPrefix.length
+    let key : List Char := if isReservedName ident then name.drop 1 else name
     let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
     return out
     -- impl-end
 
 prove_correct evalBareIdent by
   loom_solve
-  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp
-  have hok : compileName (['$'] ++ ident) = Except.ok () := by
-    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
-    unfold compileName; rw [h]; rfl
-  rw [hok, hkey]; rfl
+  by_cases h : isReservedName ident = true
+  · simp only [h, if_true]
+    have hkey : List.drop 1 (['$'] ++ ident) = ident := by simp
+    have hok : compileName (['$'] ++ ident) = Except.ok () := by
+      have h2 : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
+      unfold compileName; rw [h2]; rfl
+    rw [hok, hkey]; rfl
+  · simp only [Bool.not_eq_true] at h
+    have hok : compileName ident = Except.ok () := by
+      unfold compileName; rw [h]; rfl
+    simp only [h, Bool.false_eq_true, if_false, hok]; rfl
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The one unchanged callee this slice relies on — the
-- expression compiler that turns a single bound name into an evaluable form —
-- is modeled DEEPLY in the `pure` region (`compileName`) and validated == the
-- real callee by G-AX (an A-reference, mapping.md §3). The acceptance test
-- `matcher` is taken as a FREE INPUT, so the spec makes no behavioural claim
-- about it and holds for every value.
-- axioms-end

-- pure-start
/- The outcome of turning a single bound name into an evaluable form can fail:
   the compiler refuses names whose spelling coincides with one of the literal
   constants of the language, because such a spelling cannot denote a bound
   name. -/
inductive CompileErr where
  | reservedConstant
  deriving DecidableEq

/- The three name spellings the compiler treats as literal constants rather
   than bound names. A name with one of these exact spellings cannot be
   compiled as a bound-name reference. -/
def isReservedName (name : List Char) : Bool :=
  name = "True".toList || name = "False".toList || name = "None".toList

/- Deep model of the unchanged compiler callee (A-reference, mapping.md §3.1):
   compiling a bound-name reference succeeds for every spelling EXCEPT the
   reserved-constant spellings, for which it fails. Validated `compileName` ==
   the real compiler by axiom_check.py (G-AX); NOT consumed as an axiom. -/
def compileName (name : List Char) : Except CompileErr Unit :=
  if isReservedName name then Except.error .reservedConstant else Except.ok ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Evaluate a bare match-expression identifier against a matcher.

   A bare identifier is compiled into an evaluable form and then looked up
   through the matcher; the value of the expression is whether the matcher
   accepts that identifier. The desired behaviour is that EVERY admissible
   identifier evaluates successfully to the matcher's verdict on that exact
   identifier — including identifiers whose spelling coincides with a language
   literal constant (e.g. the three reserved-constant spellings), which must be
   evaluable just like any other identifier and must be matched on the
   identifier the user wrote, unchanged.

   `ident` and `matcher` are read-only (directive 5). -/
method evalBareIdent (ident : List Char) (matcher : List Char → Bool)
    return (out : Except CompileErr Bool)
  ensures out = Except.ok (matcher ident)
  do
    -- impl-start
    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
    -- is a character that can never begin a bound name the user could write),
    -- then look the original identifier up through the matcher.
    let identPrefix : List Char := ['$']
    let name : List Char := identPrefix ++ ident
    let compiled : Except CompileErr Unit := compileName name
    let key : List Char := name.drop identPrefix.length
    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
    return out
    -- impl-end

prove_correct evalBareIdent by
  loom_solve
  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp
  have hok : compileName (['$'] ++ ident) = Except.ok () := by
    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
    unfold compileName; rw [h]; rfl
  rw [hok, hkey]; rfl
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec is a TIGHT TOTAL FUNCTIONAL equation: `ensures out = Except.ok (matcher ident)` with `matcher : List Char -> Bool` a FREE input. Freeness pins the postcondition to force (a) matcher consulted on the ORIGINAL ident (key must equal ident) and (b) out = Except.ok (compileName succeeds), for EVERY ident — so any verifying impl is behaviorally gold-identical. Only escape hatch is the single kind-A leg (leg #3, A-reference `compileName` == real `compile(ast.Name(name),'eval')`).

A-REFERENCE SOUNDNESS (independently re-checked, not trusted): fuzzed real CPython `compile(ast.Name(name,Load()),'eval')` over 600k+ inputs incl. all Python keyword.kwlist+softkwlist, prefixed/near-miss names, punctuation, non-ASCII, control chars, empty. Model `compileName name = error iff name in {True,False,None}` matched EVERY observation — 0 mismatches. compile() succeeds for every non-{True,False,None} spelling (incl. '#True','$$True','\nTrue', keyword-likes), so any prefix that avoids the 3 reserved spellings is admissible. axiom_check.py (G-AX) is faithful to this.

### ATTACKS (all same_spec=True via markers.same_spec; verified via scripts/lean_verify.sh atk_N.lean):
- atk_1 prepatch bug (name:=ident, no prefix/strip): EXIT=1 REJECTED. G-DIFF: unsolved goal is exactly for ident in {True,False,None} where compileName ident=error != ok(matcher ident). prepatch_reproduced=true.
- atk_2 prefix but NO strip (key:=name): EXIT=1 REJECTED (matcher consulted on '$'++ident != matcher ident).
- atk_3 off-by-one strip (drop 2): EXIT=1 REJECTED.
- atk_4 negated verdict (!(matcher key)): EXIT=1 REJECTED (control-flow-effect).
- atk_5 constant `Except.ok true` (ignore matcher): EXIT=1 REJECTED (ungrounded oracle, wrong).
- atk_6 echo `Except.ok (matcher ident)` (ungrounded-oracle echo, no compile): EXIT=0 VERIFIES.
- atk_7 different valid prefix '#': EXIT=0 VERIFIES.
- atk_8 multi-char prefix '$$' (strip 2): EXIT=0 VERIFIES.
- atk_9 conditional prefix (prefix only reserved names): EXIT=0 VERIFIES.
pos_control (exact gold impl): EXIT=0 VERIFIES.

RESOLVE (official harness run_resolve, SWE-bench_Verified, real completed report.json for each; gold smoke-test resolved=True first): every verifying attack's FAITHFUL refined patch RESOLVED=True with FAIL_TO_PASS[True|False|None] all passing and 0 F2P failures:
- atk_6 -> patch = gold IDENT_PREFIX='$'  -> resolved=True (report_atk_6.json)
- atk_7 -> patch = gold with IDENT_PREFIX='#' -> resolved=True (report_atk_7.json)
- atk_8 -> patch = gold with IDENT_PREFIX='$$' -> resolved=True (report_atk_8.json)
- atk_9 -> patch = conditional-prefix realization (prefix + strip only for {True,False,None}) -> resolved=True (report_atk_9.json)
All four are genuine gold-equivalent implementations (verified behaviorally on hit AND miss cases: matcher sees original ident, invalid_idents still return False). NONE breaks the spec — a resolving 'echo'/equivalent is NOT a weakness per the fixed G-EQ/panel_1 policy.

REFINEMENT.MD AUDIT: 6 legs. #1 identPrefix (str '$' <-> ['$']) = R; #2 name:=prefix++ident (str+ <-> List++) = R; #3 compileName = A-REFERENCE (deep model of unchanged compile-of-Name, G-AX-validated, correspondence re-confirmed above); #4 key:=name.drop len (slice <-> List.drop) = R; #5 compiled.map(matcher key) (eval-consults-matcher-on-success) = R; #6 return out = I. NO kind-3 (changed op Velvet can't express). matcher free input, no axiom. A-leg correspondence to real callee HOLDS.

CONCLUSION: verify => correct on this bundle. 5 wrong impls correctly rejected; 4 verifying impls are all genuinely correct and their faithful patches all resolve. Spec is TIGHT. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The one unchanged callee this slice relies on — the
-- expression compiler that turns a single bound name into an evaluable form —
-- is modeled DEEPLY in the `pure` region (`compileName`) and validated == the
-- real callee by G-AX (an A-reference, mapping.md §3). The acceptance test
-- `matcher` is taken as a FREE INPUT, so the spec makes no behavioural claim
-- about it and holds for every value.
-- axioms-end

-- pure-start
/- The outcome of turning a single bound name into an evaluable form can fail:
   the compiler refuses names whose spelling coincides with one of the literal
   constants of the language, because such a spelling cannot denote a bound
   name. -/
inductive CompileErr where
  | reservedConstant
  deriving DecidableEq

/- The three name spellings the compiler treats as literal constants rather
   than bound names. A name with one of these exact spellings cannot be
   compiled as a bound-name reference. -/
def isReservedName (name : List Char) : Bool :=
  name = "True".toList || name = "False".toList || name = "None".toList

/- Deep model of the unchanged compiler callee (A-reference, mapping.md §3.1):
   compiling a bound-name reference succeeds for every spelling EXCEPT the
   reserved-constant spellings, for which it fails. Validated `compileName` ==
   the real compiler by axiom_check.py (G-AX); NOT consumed as an axiom. -/
def compileName (name : List Char) : Except CompileErr Unit :=
  if isReservedName name then Except.error .reservedConstant else Except.ok ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Evaluate a bare match-expression identifier against a matcher.

   A bare identifier is compiled into an evaluable form and then looked up
   through the matcher; the value of the expression is whether the matcher
   accepts that identifier. The desired behaviour is that EVERY admissible
   identifier evaluates successfully to the matcher's verdict on that exact
   identifier — including identifiers whose spelling coincides with a language
   literal constant (e.g. the three reserved-constant spellings), which must be
   evaluable just like any other identifier and must be matched on the
   identifier the user wrote, unchanged.

   `ident` and `matcher` are read-only (directive 5). -/
method evalBareIdent (ident : List Char) (matcher : List Char → Bool)
    return (out : Except CompileErr Bool)
  ensures out = Except.ok (matcher ident)
  do
    -- impl-start
    -- Compile the identifier under a fixed sentinel-prefixed name (the prefix
    -- is a character that can never begin a bound name the user could write),
    -- then look the original identifier up through the matcher.
    let identPrefix : List Char := ['$']
    let name : List Char := identPrefix ++ ident
    let compiled : Except CompileErr Unit := compileName name
    let key : List Char := name.drop identPrefix.length
    let out : Except CompileErr Bool := compiled.map (fun _ => matcher key)
    return out
    -- impl-end

prove_correct evalBareIdent by
  loom_solve
  have hkey : List.drop ['$'].length (['$'] ++ ident) = ident := by simp
  have hok : compileName (['$'] ++ ident) = Except.ok () := by
    have h : isReservedName (['$'] ++ ident) = false := by unfold isReservedName; simp
    unfold compileName; rw [h]; rfl
  rw [hok, hkey]; rfl
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec is a TIGHT TOTAL FUNCTIONAL equation: `ensures out = Except.ok (matcher ident)` with `matcher : List Char -> Bool` a FREE input. Freeness pins the postcondition to force (a) matcher consulted on the ORIGINAL ident (key must equal ident) and (b) out = Except.ok (compileName succeeds), for EVERY ident — so any verifying impl is behaviorally gold-identical. Only escape hatch is the single kind-A leg (leg #3, A-reference `compileName` == real `compile(ast.Name(name),'eval')`).

A-REFERENCE SOUNDNESS (independently re-checked, not trusted): fuzzed real CPython `compile(ast.Name(name,Load()),'eval')` over 600k+ inputs incl. all Python keyword.kwlist+softkwlist, prefixed/near-miss names, punctuation, non-ASCII, control chars, empty. Model `compileName name = error iff name in {True,False,None}` matched EVERY observation — 0 mismatches. compile() succeeds for every non-{True,False,None} spelling (incl. '#True','$$True','\nTrue', keyword-likes), so any prefix that avoids the 3 reserved spellings is admissible. axiom_check.py (G-AX) is faithful to this.

### ATTACKS (all same_spec=True via markers.same_spec; verified via scripts/lean_verify.sh atk_N.lean):
- atk_1 prepatch bug (name:=ident, no prefix/strip): EXIT=1 REJECTED. G-DIFF: unsolved goal is exactly for ident in {True,False,None} where compileName ident=error != ok(matcher ident). prepatch_reproduced=true.
- atk_2 prefix but NO strip (key:=name): EXIT=1 REJECTED (matcher consulted on '$'++ident != matcher ident).
- atk_3 off-by-one strip (drop 2): EXIT=1 REJECTED.
- atk_4 negated verdict (!(matcher key)): EXIT=1 REJECTED (control-flow-effect).
- atk_5 constant `Except.ok true` (ignore matcher): EXIT=1 REJECTED (ungrounded oracle, wrong).
- atk_6 echo `Except.ok (matcher ident)` (ungrounded-oracle echo, no compile): EXIT=0 VERIFIES.
- atk_7 different valid prefix '#': EXIT=0 VERIFIES.
- atk_8 multi-char prefix '$$' (strip 2): EXIT=0 VERIFIES.
- atk_9 conditional prefix (prefix only reserved names): EXIT=0 VERIFIES.
pos_control (exact gold impl): EXIT=0 VERIFIES.

RESOLVE (official harness run_resolve, SWE-bench_Verified, real completed report.json for each; gold smoke-test resolved=True first): every verifying attack's FAITHFUL refined patch RESOLVED=True with FAIL_TO_PASS[True|False|None] all passing and 0 F2P failures:
- atk_6 -> patch = gold IDENT_PREFIX='$'  -> resolved=True (report_atk_6.json)
- atk_7 -> patch = gold with IDENT_PREFIX='#' -> resolved=True (report_atk_7.json)
- atk_8 -> patch = gold with IDENT_PREFIX='$$' -> resolved=True (report_atk_8.json)
- atk_9 -> patch = conditional-prefix realization (prefix + strip only for {True,False,None}) -> resolved=True (report_atk_9.json)
All four are genuine gold-equivalent implementations (verified behaviorally on hit AND miss cases: matcher sees original ident, invalid_idents still return False). NONE breaks the spec — a resolving 'echo'/equivalent is NOT a weakness per the fixed G-EQ/panel_1 policy.

REFINEMENT.MD AUDIT: 6 legs. #1 identPrefix (str '$' <-> ['$']) = R; #2 name:=prefix++ident (str+ <-> List++) = R; #3 compileName = A-REFERENCE (deep model of unchanged compile-of-Name, G-AX-validated, correspondence re-confirmed above); #4 key:=name.drop len (slice <-> List.drop) = R; #5 compiled.map(matcher key) (eval-consults-matcher-on-success) = R; #6 return out = I. NO kind-3 (changed op Velvet can't express). matcher free input, no axiom. A-leg correspondence to real callee HOLDS.

CONCLUSION: verify => correct on this bundle. 5 wrong impls correctly rejected; 4 verifying impls are all genuinely correct and their faithful patches all resolve. Spec is TIGHT. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed to find drift. same_spec(Solution, prepatch)=True (spec region byte-identical; prepatch differs only in elided impl). The modeled function evalBareIdent returns Except.ok (matcher ident) for all inputs; this matches the real post-patch repo path (ast.Name(IDENT_PREFIX+ident) -> compile(...,'eval') -> eval via MatcherAdapter stripping key[len(IDENT_PREFIX):]). Empirically ran the ACTUAL CPython compile+eval path over 200,000 fuzzed (ident,matcher) inputs incl. the three reserved spellings True/False/None, empty, whitespace, NUL, newline, non-ASCII, surrogates, $-prefixed names: 0 divergences from Except.ok (matcher ident). The A-reference compileName deep model (fail iff name in {True,False,None}) validated == real compile-of-Name over 50,009 inputs: 0 divergences. The '$' sentinel prefix guarantees the compile leg never fails, so the total-success + match-on-original-ident claim is sound and not too strong. Lean proof closes (lean_verify EXIT=0). No diverging input exists. NOTE: bundle contains no patch.diff file (listed in prompt but absent); used the post-patch worktree at base_commit 19ad5889 which already contains the IDENT_PREFIX='$' change at expression.py:169 (site A) and :181 (site B) exactly as mapping.md/refinement.md describe.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Reviewed the actual solver-visible spec view (spec_view over Solution.lean, velvet backend) and confirmed same_spec(Solution, Solution_prepatch)=True — the spec view is invariant across the gold edit, so the fix is not encoded in it. Mechanical G-LEAK screen passes (no hard failures; changed symbols not_expr/reject not echoed, no diff markers, no gold-patch line reproduced, no patched file path).

Semantic assessment of what the spec view reveals vs the public problem_statement:
- problem_statement already publicly discloses the full bug: Expression.compile("False") aborts the debug interpreter via the compiler_nameop assertion on None/True/False. So 'reserved spellings True/False/None cannot be compiled as bound names' is public.
- compileName/isReservedName/CompileErr.reservedConstant in the visible `pure` region model the UNCHANGED callee's rejection of exactly those three spellings — behavior already public in the problem statement's assertion text.
- The postcondition `ensures out = Except.ok (matcher ident)` plus the docstring state the desired correctness property (every admissible identifier, including reserved spellings, must evaluate successfully and be matched on the exact unchanged identifier). This is a WHAT-not-HOW correctness spec derivable directly from the public bug report; it does not disclose the fix mechanism.
- The gold mechanism (IDENT_PREFIX = "$" sentinel prefix at site A; key[len(IDENT_PREFIX):] strip at site B) lives ENTIRELY in the elided impl region ('implementation elided') and the elided prove_correct body. Neither the '$' sentinel, the prefix/strip idea, nor IDENT_PREFIX appears anywhere in the spec view. A solver must still independently invent a way to make reserved spellings compilable.

No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
