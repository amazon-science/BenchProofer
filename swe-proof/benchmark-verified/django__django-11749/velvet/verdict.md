# P2 adversarial audit — django__django-11749

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec is a total, precondition-free exact functional equality out = forwardedAll options, where forwarded a = a.supplied && (a.individuallyRequired || a.inRequiredGroup). Every same-spec wrong impl fails to verify; every same-spec verifying impl is behaviorally the gold and its faithful patch resolves.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- axioms-end
@@ -62,10 +62,10 @@
       invariant 0 ≤ i ∧ i ≤ options.length
       invariant result = forwardedAll (options.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := options[i - 1]!
-      result := forwarded a :: result
+      let c : Bool := a.supplied && a.individuallyRequired
+      result := c :: result
       i := i - 1
     return result
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
 -- axioms-end
@@ -62,10 +62,10 @@
       invariant 0 ≤ i ∧ i ≤ options.length
       invariant result = forwardedAll (options.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := options[i - 1]!
-      result := forwarded a :: result
+      let c : Bool := a.supplied && a.inRequiredGroup
+      result := c :: result
       i := i - 1
     return result
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
 -- axioms-end
@@ -62,10 +62,10 @@
       invariant 0 ≤ i ∧ i ≤ options.length
       invariant result = forwardedAll (options.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := options[i - 1]!
-      result := forwarded a :: result
+      let c : Bool := a.supplied && (a.individuallyRequired && a.inRequiredGroup)
+      result := c :: result
       i := i - 1
     return result
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
 -- axioms-end
@@ -62,10 +62,10 @@
       invariant 0 ≤ i ∧ i ≤ options.length
       invariant result = forwardedAll (options.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := options[i - 1]!
-      result := forwarded a :: result
+      let c : Bool := a.individuallyRequired || a.inRequiredGroup
+      result := c :: result
       i := i - 1
     return result
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
 -- axioms-end
@@ -62,10 +62,10 @@
       invariant 0 ≤ i ∧ i ≤ options.length
       invariant result = forwardedAll (options.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := options[i - 1]!
-      result := forwarded a :: result
+      let c : Bool := if i == 1 then false else forwarded a
+      result := c :: result
       i := i - 1
     return result
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
 -- axioms-end
@@ -62,10 +62,9 @@
       invariant 0 ≤ i ∧ i ≤ options.length
       invariant result = forwardedAll (options.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := options[i - 1]!
-      result := forwarded a :: result
+      result := result ++ [forwarded a]
       i := i - 1
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
 -- axioms-end
@@ -56,17 +56,7 @@
   ensures out = forwardedAll options
   do
     -- impl-start
-    let mut result : List Bool := []
-    let mut i := options.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ options.length
-      invariant result = forwardedAll (options.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := options[i - 1]!
-      result := forwarded a :: result
-      i := i - 1
+    let result : List Bool := []
     return result
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
 -- axioms-end
@@ -62,10 +62,10 @@
       invariant 0 ≤ i ∧ i ≤ options.length
       invariant result = forwardedAll (options.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := options[i - 1]!
-      result := forwarded a :: result
+      let _ := a
+      result := true :: result
       i := i - 1
     return result
     -- impl-end
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
 -- axioms-end
@@ -62,10 +62,10 @@
       invariant 0 ≤ i ∧ i ≤ options.length
       invariant result = forwardedAll (options.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := options[i - 1]!
-      result := forwarded a :: result
+      let c : Bool := (a.supplied && a.individuallyRequired) || (a.supplied && a.inRequiredGroup)
+      result := c :: result
       i := i - 1
     return result
     -- impl-end
@@ -88,4 +88,5 @@
 prove_correct selectForwarded by
   loom_solve
   rw [forwardedAll_drop_step options i (by omega) (by omega)]
+  simp only [forwarded, Bool.and_or_distrib_left]
   simp_all
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- axioms-end
@@ -62,10 +62,10 @@
       invariant 0 ≤ i ∧ i ≤ options.length
       invariant result = forwardedAll (options.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := options[i - 1]!
-      result := forwarded a :: result
+      let c : Bool := a.supplied && (a.inRequiredGroup || a.individuallyRequired)
+      result := c :: result
       i := i - 1
     return result
     -- impl-end
@@ -88,4 +88,5 @@
 prove_correct selectForwarded by
   loom_solve
   rw [forwardedAll_drop_step options i (by omega) (by omega)]
+  simp only [forwarded, Bool.or_comm]
   simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A single declared option, abstracted to only the observations that decide
   whether its supplied value must be forwarded to argument re-parsing.

   * `supplied`        — a value for this option was provided by the caller (its
                         destination name is present among the supplied keyword
                         arguments).
   * `individuallyRequired` — the option is required on its own.
   * `inRequiredGroup` — the option belongs to a mutually exclusive group that is
                         itself required (at least one of the group's members
                         must be provided). -/
structure OptionView where
  supplied : Bool
  individuallyRequired : Bool
  inRequiredGroup : Bool
  deriving Inhabited

/- A supplied option's value must be forwarded for re-parsing exactly when the
   caller provided it AND it is mandatory — either required on its own, or a
   member of a required mutually exclusive group. An option whose value was not
   provided is never forwarded; a non-mandatory provided option is not forwarded
   here either (its value is merged separately). -/
@[grind] def forwarded (a : OptionView) : Bool :=
  a.supplied && (a.individuallyRequired || a.inRequiredGroup)

/- Whether each declared option, in declaration order, has its value forwarded.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def forwardedAll : List OptionView → List Bool
  | []      => []
  | a :: rest => forwarded a :: forwardedAll rest

@[grind] lemma forwardedAll_nil : forwardedAll [] = [] := rfl
@[grind] lemma forwardedAll_cons (a : OptionView) (rest : List OptionView) :
    forwardedAll (a :: rest) = forwarded a :: forwardedAll rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method selectForwarded (options : List OptionView) return (out : List Bool)
  ensures out = forwardedAll options
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := options.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ options.length
      invariant result = forwardedAll (options.drop i)
      done_with i = 0
    do
      let a := options[i - 1]!
      result := forwarded a :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `forwardedAll` peels one `forwarded`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma forwardedAll_drop_step (options : List OptionView) (i : Nat)
    (hi : 0 < i) (hle : i ≤ options.length) :
    forwardedAll (options.drop (i - 1))
      = forwarded options[i - 1]! :: forwardedAll (options.drop i) := by
  have hlt : i - 1 < options.length := by omega
  have hcons : options.drop (i - 1) = options[i - 1]! :: options.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, forwardedAll_cons]

prove_correct selectForwarded by
  loom_solve
  rw [forwardedAll_drop_step options i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (byte-identical spec confirmed via markers.same_spec=True for all 10 attacks + positive_control; verified via scripts/lean_verify.sh with 300s budget). Verify cmd form: `bash scripts/lean_verify.sh <file>` (0=verifies, 1=error). Resolve via swebench_unified.harness.run_resolve on the official Docker oracle (image swebench/sweb.eval.x86_64.django_1776_django-11749).

### Attack results
- atk_1 (prepatch bug: drops inRequiredGroup, c = supplied && individuallyRequired) -> FAIL verify (exit 1). Reproduces Solution_prepatch.lean / G-DIFF; prepatch_reproduced=true.
- atk_2 (drops individuallyRequired: c = supplied && inRequiredGroup) -> FAIL verify (exit 1).
- atk_3 (AND not OR: c = supplied && (individuallyRequired && inRequiredGroup)) -> FAIL verify (exit 1).
- atk_4 (ignores supplied: c = individuallyRequired || inRequiredGroup) -> FAIL verify (exit 1).
- atk_5 (boundary: false on first option when i==1, forwarded else) -> FAIL verify (exit 1).
- atk_6 (control-flow-effect: result := result ++ [forwarded a], reversed order) -> FAIL verify (exit 1).
- atk_7 (partial-domain: skip loop, return []) -> FAIL verify (exit 1).
- atk_8 (ungrounded-oracle echo: result := true :: result) -> FAIL verify (exit 1).
- atk_9 (EQUIVALENT/echo: c = (supplied && individuallyRequired) || (supplied && inRequiredGroup); proof uses Bool.and_or_distrib_left) -> VERIFIES (exit 0). Faithful refined patch materialized (distributed predicate) -> run_resolve RESOLVED=True completed=True.
- atk_10 (EQUIVALENT: c = supplied && (inRequiredGroup || individuallyRequired), commuted OR; proof uses Bool.or_comm) -> VERIFIES (exit 0). Faithful refined patch materialized (commuted OR predicate) -> run_resolve RESOLVED=True completed=True.

Both verifying same-spec patches apply cleanly at base_commit 350123f38c2b6217c38d70bfbd924a9ba3df1289 (git apply --check) and RESOLVE under the official harness. No verifying wrong impl exists; verify=>correct holds for every attack tried. positive_control (gold Solution.lean unchanged) verifies (exit 0).

REFINEMENT.MD AUDIT: axioms=[], deep_model_references=[] in meta.json; refinement.md legs A1-A6 are all R / I (no A-consumed, no A-reference, no kind-3). The genuinely-changed decision (the second mandatory route: membership of a required mutually exclusive group) is modeled DEEPLY and concretely at leg A4 as OptionView.inRequiredGroup <-> `opt in mutually_exclusive_required_options` (the added set over parser._mutually_exclusive_groups/group._group_actions/group.required), NOT hidden behind any callee-contract axiom. A-leg correspondence is sound: no A-consumed/A-reference legs exist to falsify, and the R/I transliteration is covered by G-CONF (100006 parsers, seed=11749, 0 disagreements). G-AX is a legitimate skip. mapping.md section 2 bijection (Python truthiness <-> Bool, true<->appended/false<->skipped) matches the deep model.

VERDICT: SOUND. 10 distinct same-spec attacks run (8 partial-domain/boundary/control-flow/ungrounded/wrong-predicate all fail verify; 2 equivalent/echo verify and their faithful patches resolve). None breaks the spec (no verifying wrong impl whose faithful patch fails to resolve).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec is a total, precondition-free exact functional equality out = forwardedAll options, where forwarded a = a.supplied && (a.individuallyRequired || a.inRequiredGroup). Every same-spec wrong impl fails to verify; every same-spec verifying impl is behaviorally the gold and its faithful patch resolves.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A single declared option, abstracted to only the observations that decide
   whether its supplied value must be forwarded to argument re-parsing.

   * `supplied`        — a value for this option was provided by the caller (its
                         destination name is present among the supplied keyword
                         arguments).
   * `individuallyRequired` — the option is required on its own.
   * `inRequiredGroup` — the option belongs to a mutually exclusive group that is
                         itself required (at least one of the group's members
                         must be provided). -/
structure OptionView where
  supplied : Bool
  individuallyRequired : Bool
  inRequiredGroup : Bool
  deriving Inhabited

/- A supplied option's value must be forwarded for re-parsing exactly when the
   caller provided it AND it is mandatory — either required on its own, or a
   member of a required mutually exclusive group. An option whose value was not
   provided is never forwarded; a non-mandatory provided option is not forwarded
   here either (its value is merged separately). -/
@[grind] def forwarded (a : OptionView) : Bool :=
  a.supplied && (a.individuallyRequired || a.inRequiredGroup)

/- Whether each declared option, in declaration order, has its value forwarded.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def forwardedAll : List OptionView → List Bool
  | []      => []
  | a :: rest => forwarded a :: forwardedAll rest

@[grind] lemma forwardedAll_nil : forwardedAll [] = [] := rfl
@[grind] lemma forwardedAll_cons (a : OptionView) (rest : List OptionView) :
    forwardedAll (a :: rest) = forwarded a :: forwardedAll rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method selectForwarded (options : List OptionView) return (out : List Bool)
  ensures out = forwardedAll options
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := options.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ options.length
      invariant result = forwardedAll (options.drop i)
      done_with i = 0
    do
      let a := options[i - 1]!
      result := forwarded a :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `forwardedAll` peels one `forwarded`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma forwardedAll_drop_step (options : List OptionView) (i : Nat)
    (hi : 0 < i) (hle : i ≤ options.length) :
    forwardedAll (options.drop (i - 1))
      = forwarded options[i - 1]! :: forwardedAll (options.drop i) := by
  have hlt : i - 1 < options.length := by omega
  have hcons : options.drop (i - 1) = options[i - 1]! :: options.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, forwardedAll_cons]

prove_correct selectForwarded by
  loom_solve
  rw [forwardedAll_drop_step options i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (byte-identical spec confirmed via markers.same_spec=True for all 10 attacks + positive_control; verified via scripts/lean_verify.sh with 300s budget). Verify cmd form: `bash scripts/lean_verify.sh <file>` (0=verifies, 1=error). Resolve via swebench_unified.harness.run_resolve on the official Docker oracle (image swebench/sweb.eval.x86_64.django_1776_django-11749).

### Attack results
- atk_1 (prepatch bug: drops inRequiredGroup, c = supplied && individuallyRequired) -> FAIL verify (exit 1). Reproduces Solution_prepatch.lean / G-DIFF; prepatch_reproduced=true.
- atk_2 (drops individuallyRequired: c = supplied && inRequiredGroup) -> FAIL verify (exit 1).
- atk_3 (AND not OR: c = supplied && (individuallyRequired && inRequiredGroup)) -> FAIL verify (exit 1).
- atk_4 (ignores supplied: c = individuallyRequired || inRequiredGroup) -> FAIL verify (exit 1).
- atk_5 (boundary: false on first option when i==1, forwarded else) -> FAIL verify (exit 1).
- atk_6 (control-flow-effect: result := result ++ [forwarded a], reversed order) -> FAIL verify (exit 1).
- atk_7 (partial-domain: skip loop, return []) -> FAIL verify (exit 1).
- atk_8 (ungrounded-oracle echo: result := true :: result) -> FAIL verify (exit 1).
- atk_9 (EQUIVALENT/echo: c = (supplied && individuallyRequired) || (supplied && inRequiredGroup); proof uses Bool.and_or_distrib_left) -> VERIFIES (exit 0). Faithful refined patch materialized (distributed predicate) -> run_resolve RESOLVED=True completed=True.
- atk_10 (EQUIVALENT: c = supplied && (inRequiredGroup || individuallyRequired), commuted OR; proof uses Bool.or_comm) -> VERIFIES (exit 0). Faithful refined patch materialized (commuted OR predicate) -> run_resolve RESOLVED=True completed=True.

Both verifying same-spec patches apply cleanly at base_commit 350123f38c2b6217c38d70bfbd924a9ba3df1289 (git apply --check) and RESOLVE under the official harness. No verifying wrong impl exists; verify=>correct holds for every attack tried. positive_control (gold Solution.lean unchanged) verifies (exit 0).

REFINEMENT.MD AUDIT: axioms=[], deep_model_references=[] in meta.json; refinement.md legs A1-A6 are all R / I (no A-consumed, no A-reference, no kind-3). The genuinely-changed decision (the second mandatory route: membership of a required mutually exclusive group) is modeled DEEPLY and concretely at leg A4 as OptionView.inRequiredGroup <-> `opt in mutually_exclusive_required_options` (the added set over parser._mutually_exclusive_groups/group._group_actions/group.required), NOT hidden behind any callee-contract axiom. A-leg correspondence is sound: no A-consumed/A-reference legs exist to falsify, and the R/I transliteration is covered by G-CONF (100006 parsers, seed=11749, 0 disagreements). G-AX is a legitimate skip. mapping.md section 2 bijection (Python truthiness <-> Bool, true<->appended/false<->skipped) matches the deep model.

VERDICT: SOUND. 10 distinct same-spec attacks run (8 partial-domain/boundary/control-flow/ungrounded/wrong-predicate all fail verify; 2 equivalent/echo verify and their faithful patches resolve). None breaks the spec (no verifying wrong impl whose faithful patch fails to resolve).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-11749 velvet bundle.

Modeled function: forwarded a = a.supplied && (a.individuallyRequired || a.inRequiredGroup), folded order-preservingly by forwardedAll over List OptionView. Spec ensures out = forwardedAll options.

Real post-patch callee (django/core/management/__init__.py:135-138, base_commit 350123f38c): the comprehension predicate `opt.dest in options and (opt.required or opt in mutually_exclusive_required_options)`, where the mutex set is {opt for group in parser._mutually_exclusive_groups for opt in group._group_actions if group.required}. Verified against the real source in the /tmp worktree; patch.diff is the verbatim gold patch.

Bijection (mapping.md §2): supplied<->(opt.dest in options), individuallyRequired<->opt.required, inRequiredGroup<->(opt in mutually_exclusive_required_options); Bool verdict true<->kept/forwarded, false<->dropped.

Under this bijection the Lean formula is a<->b: `a && (b || c)` on the Lean side is exactly the Python `a and (b or c)`. Identical boolean function on all 8 rows of the (supplied, individuallyRequired, inRequiredGroup) matrix. There is NO input where the modeled function disagrees with the real callee:
- The spec is not too strong: every reachable action verdict equals the patched predicate's verdict. The single argparse-unreachable combination (individuallyRequired=True AND inRequiredGroup=True, forbidden because argparse disallows required=True on a mutex-group member) is handled by the SAME formula, so even that phantom domain point agrees — no over-constraint, no divergence.
- Order is preserved on both sides (parser_actions declaration order == List order via forwardedAll's front recursion).
- Scope is correct: the unchanged '{}={}'.format(...) formatting of a kept option is outside the predicate the patch edits and is legitimately excluded from the keep-mask carrier (mapping.md §2, refinement.md A5) — that is the consumer spec-view boundary, not a behavioral divergence.

Corroboration: conformance_check.py (seed 11749) runs a Python transliteration of `forwarded` (SHADOW) vs the real patched predicate over REAL argparse parsers (ORACLE) across explicit boundary cases (incl. the F2P required-mutex-group case call_command(..., foo_id=1)) plus 100,000 fuzzed parsers with randomized standalone/mutex-required/optional groups — 0 disagreements by construction (the two functions are the same boolean expression).

Mechanical checks passed: same_spec(Solution.lean, Solution_prepatch.lean) == True (spec region frozen; prepatch differs only in the elided impl region, using supplied && individuallyRequired, which correctly fails to satisfy the frozen spec on a supplied group-only-required option — G-DIFF sound). lean_verify.sh on Solution.lean exits 0 (verifies, no sorry/error).

Conclusion: the modeled function is behaviorally equal to the real post-patch callee on every input; the spec is neither too strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view for velvet django__django-11749. same_spec(Solution.lean, Solution_prepatch.lean) == True (spec region byte-identical; only the impl block differs, and impl/proof are elided in the spec view). Lexical G-LEAK screen passes with zero hard_failures. Content check: the spec exposes OptionView{supplied, individuallyRequired, inRequiredGroup} and forwarded = supplied && (individuallyRequired || inRequiredGroup). All three observations and the corrected forwarding rule are already fully disclosed by the PUBLIC problem_statement, which quotes the buggy predicate (`opt.required and opt.dest in options`), states the option is part of a required mutually exclusive group, notes both members are individually not required, and says call_command 'does nothing with groups defined in the parser'. The spec's fix is the natural, direct consequence of that stated diagnosis — nothing is revealed beyond problem_statement. Docstring/comments in the spec view are abstract behavioral descriptions; they do not quote gold-patch specifics (no mention of `mutually_exclusive_required_options`, `_mutually_exclusive_groups`, `_group_actions`, or the comprehension edit). No leakage beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
