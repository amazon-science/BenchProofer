# P2 adversarial audit — sphinx-doc__sphinx-10449

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
None found. The two method postconditions fully pin each output to the pure model function (emitReturnTypeEntry: out = returnTypeEntry ...; emitReturnTypeForKind: out = returnTypeEntryForKind ... plus two pinned-regime ensures). No output component is left free, so any impl that verifies must compute exactly the model function — hence its faithful refined patch is the gold patch, which resolves. No verifying-but-wrong impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. Both modeled functions decide a single observable:
@@ -80,10 +80,7 @@
   do
     -- impl-start
     if hasReturnAnno && !returnInArgs then
-      if (returnAnnotation == "None".toList) && omitNoneReturnType then
-        return none
-      else
-        return (some returnAnnotation)
+      return (some returnAnnotation)
     else
       return none
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
 -- (No axiomatized callees. Both modeled functions decide a single observable:
@@ -110,12 +110,8 @@
            → out = some returnAnnotation
   do
     -- impl-start
-    if isClassKind kind then
-      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation true
-      return r
-    else
-      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation false
-      return r
+    let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation false
+    return r
     -- impl-end
 
 prove_correct emitReturnTypeForKind by
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
 -- (No axiomatized callees. Both modeled functions decide a single observable:
@@ -79,13 +79,7 @@
   ensures out = returnTypeEntry hasReturnAnno returnInArgs returnAnnotation omitNoneReturnType
   do
     -- impl-start
-    if hasReturnAnno && !returnInArgs then
-      if (returnAnnotation == "None".toList) && omitNoneReturnType then
-        return none
-      else
-        return (some returnAnnotation)
-    else
-      return none
+    return none
     -- impl-end
 
 prove_correct emitReturnTypeEntry by
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
 -- (No axiomatized callees. Both modeled functions decide a single observable:
@@ -80,7 +80,7 @@
   do
     -- impl-start
     if hasReturnAnno && !returnInArgs then
-      if (returnAnnotation == "None".toList) && omitNoneReturnType then
+      if (returnAnnotation == "None".toList) then
         return none
       else
         return (some returnAnnotation)
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
 -- (No axiomatized callees. Both modeled functions decide a single observable:
@@ -111,10 +111,10 @@
   do
     -- impl-start
     if isClassKind kind then
-      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation true
+      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation false
       return r
     else
-      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation false
+      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation true
       return r
     -- impl-end
 
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
 -- (No axiomatized callees. Both modeled functions decide a single observable:
@@ -79,13 +79,7 @@
   ensures out = returnTypeEntry hasReturnAnno returnInArgs returnAnnotation omitNoneReturnType
   do
     -- impl-start
-    if hasReturnAnno && !returnInArgs then
-      if (returnAnnotation == "None".toList) && omitNoneReturnType then
-        return none
-      else
-        return (some returnAnnotation)
-    else
-      return none
+    return (returnTypeEntry hasReturnAnno returnInArgs returnAnnotation omitNoneReturnType)
     -- impl-end
 
 prove_correct emitReturnTypeEntry by
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
 -- (No axiomatized callees. Both modeled functions decide a single observable:
@@ -79,7 +79,7 @@
   ensures out = returnTypeEntry hasReturnAnno returnInArgs returnAnnotation omitNoneReturnType
   do
     -- impl-start
-    if hasReturnAnno && !returnInArgs then
+    if hasReturnAnno && returnInArgs then
       if (returnAnnotation == "None".toList) && omitNoneReturnType then
         return none
       else
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled functions decide a single observable:
--  whether a "return type" entry is appended to a documented object's
--  description, and with what text. The entry-building constructors are pure
--  data assembly, modeled directly as the produced entry text (an
--  `Option (List Char)`: `some t` = an entry carrying text `t` is appended,
--  `none` = no entry is appended) — an I/R transliteration validated against
--  the real implementation by conformance_check.py (G-CONF). The inputs are the
--  observations the decision reads: whether a return annotation exists for the
--  object, whether the description already declares a return type, the return
--  annotation's rendered text, and the object's kind. Every observable is a
--  closed function of these inputs — nothing is borrowed from an oracle, and
--  there is no unchanged library callee whose contract the proof must
--  axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether an object of the given kind must NOT advertise a "None" return type.
   A documented value/function/method that returns `None` legitimately shows a
   `None` return type; a documented *class* must not — a class has no return
   value of its own, so listing `None` as its return type is spurious. The kind
   is the object's descriptor label (`"class"`, `"function"`, `"method"`, …);
   only the class kind triggers the omission. -/
@[grind] def isClassKind (kind : List Char) : Bool := kind == "class".toList

/- The "return type" entry appended to an object's description, as the text it
   carries (`some text`) or its absence (`none`).

   An entry is appended only when the object actually has a return annotation
   (`hasReturnAnno`) AND the description does not already declare a return type
   (`returnInArgs` is false) — declaring it twice would duplicate it. When both
   hold, the entry normally carries the rendered return annotation
   (`returnAnnotation`). The sole exception: when `omitNoneReturnType` is set and
   the annotation is exactly `None`, no entry is appended at all — a `None`
   return type is suppressed for objects that must not advertise one. -/
@[grind] def returnTypeEntry (hasReturnAnno returnInArgs : Bool)
    (returnAnnotation : List Char) (omitNoneReturnType : Bool) : Option (List Char) :=
  if hasReturnAnno && !returnInArgs then
    (if (returnAnnotation == "None".toList) && omitNoneReturnType then none
     else some returnAnnotation)
  else
    none

/- The "return type" entry appended for an object of a given kind. The kind
   decides whether a `None` return type is suppressed: a class kind suppresses
   it, every other kind keeps it. Otherwise the entry is exactly the one
   `returnTypeEntry` describes. -/
@[grind] def returnTypeEntryForKind (kind : List Char) (hasReturnAnno returnInArgs : Bool)
    (returnAnnotation : List Char) : Option (List Char) :=
  returnTypeEntry hasReturnAnno returnInArgs returnAnnotation (isClassKind kind)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Append the "return type" entry to a documented object's description.

   `hasReturnAnno` says the object carries a return annotation; `returnInArgs`
   says the description already declares a return type (so a fresh entry would
   duplicate it); `returnAnnotation` is the rendered annotation text; and
   `omitNoneReturnType` requests that a `None` return type be omitted rather than
   shown. The result is the entry that gets appended — `some text` for an entry
   carrying `text`, or `none` when nothing is appended. A fresh result is built
   and no input is mutated (directive 5). -/
method emitReturnTypeEntry (hasReturnAnno : Bool) (returnInArgs : Bool)
    (returnAnnotation : List Char) (omitNoneReturnType : Bool)
    return (out : Option (List Char))
  ensures out = returnTypeEntry hasReturnAnno returnInArgs returnAnnotation omitNoneReturnType
  do
    -- impl-start
    if hasReturnAnno && !returnInArgs then
      if (returnAnnotation == "None".toList) && omitNoneReturnType then
        return none
      else
        return (some returnAnnotation)
    else
      return none
    -- impl-end

prove_correct emitReturnTypeEntry by
  loom_solve

/- Append the "return type" entry for an object of a given `kind`. The kind
   alone selects the policy: for a class, a `None` return type is omitted (a
   class advertising `None` as its return type is spurious); for every other
   kind the entry is produced exactly as for any documented object. The
   remaining inputs and the result are as in `emitReturnTypeEntry`.

   `kind` and the other inputs are read-only (not `mut`): the routine selects the
   policy and delegates, mutating no input (directive 5). The produced entry is
   pinned for both regimes, so no result component is left free. -/
method emitReturnTypeForKind (kind : List Char) (hasReturnAnno : Bool) (returnInArgs : Bool)
    (returnAnnotation : List Char)
    return (out : Option (List Char))
  ensures out = returnTypeEntryForKind kind hasReturnAnno returnInArgs returnAnnotation
  ensures (kind = "class".toList ∧ hasReturnAnno = true ∧ returnInArgs = false
           ∧ returnAnnotation = "None".toList) → out = none
  ensures (kind ≠ "class".toList ∧ hasReturnAnno = true ∧ returnInArgs = false)
           → out = some returnAnnotation
  do
    -- impl-start
    if isClassKind kind then
      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation true
      return r
    else
      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation false
      return r
    -- impl-end

prove_correct emitReturnTypeForKind by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity, plan §4). Scratch dir: same_spec=True confirmed for all 7 attacks + positive control via swebench_unified.markers.same_spec (velvet). Verifier: scripts/lean_verify.sh (exit 0=verifies, 1=error). Verifications run concurrently in two background batches of ≤4.

### ATTACKS (all same-spec; impl-region-only edits, axioms/pure/pre/post byte-identical):
- atk_1 (prepatch bug #1 re-encode: emitReturnTypeEntry drops the None-suppression branch, always appends some returnAnnotation). cmd: `bash scripts/lean_verify.sh atk_1.lean` -> exit 1 (unsolved goals @88:34). Correctly REJECTED.
- atk_2 (prepatch bug #2 re-encode: emitReturnTypeForKind ignores kind, always delegates with suppress=false). -> exit 1 (unsolved goals @117:36). Correctly REJECTED.
- atk_3 (partial-domain: emitReturnTypeEntry returns none unconditionally). -> exit 1 (unsolved goals @85:34). Correctly REJECTED.
- atk_4 (boundary: suppress None regardless of omitNoneReturnType flag — drop the && omitNoneReturnType conjunct). -> exit 1 (unsolved goals @91:34). Correctly REJECTED.
- atk_5 (control-flow-effect: swap the suppress-flag true/false between the class and non-class branches of emitReturnTypeForKind). -> exit 1 (unsolved goals @121:36). Correctly REJECTED.
- atk_6 (ungrounded-oracle echo: emitReturnTypeEntry returns the pure model fn `returnTypeEntry ...` verbatim). -> exit 0 VERIFIES. This is behaviorally IDENTICAL to the model (a correct echo, not a weakness). Per protocol its faithful refined patch = the gold patch (verbatim); RAN through official harness: `run_resolve('sphinx-doc__sphinx-10449', gold_patch, timeout=1800, retries=1)` -> RESOLVED: True, COMPLETED: True, NOTE: resolved (log: resolve_atk6.log). verify⇒correct holds.
- atk_7 (boundary: flip guard to `hasReturnAnno && returnInArgs`). -> exit 1 (unsolved goals @91:34). Correctly REJECTED.

Positive control pos_control.lean (frozen Solution.lean impl) -> exit 0 verifies. prepatch_reproduced: both prepatch bugs re-encoded as atk_1/atk_2 and confirmed to FAIL verification (matches refinement.md §A/§B G-DIFF claims).

REFINEMENT AUDIT (§4 A-legs focus): meta.json axioms=[] and deep_model_references=[] — the A-legs are VACUOUS (no axiom consumed, no deep-model reference), so there is no callee-correspondence to falsify. refinement.md §C correctly declares every leg R or I with NO kind-3 (inexpressible-changed-op) step; G-AX=skip is legitimate. inter_method_calls: emitReturnTypeForKind->emitReturnTypeEntry discharged by emitReturnTypeEntry_correct (callee-under-spec, strictly stronger than an axiom). Model↔patch correspondence is tight: the two postconditions fully pin outputs to the pure functions returnTypeEntry / returnTypeEntryForKind (plus emitReturnTypeForKind's two pinned-regime ensures for the class-None and non-class cases), leaving no free output component. Therefore any verifying impl computes exactly the model function and its faithful patch is the gold patch, which resolves.

VERDICT: SOUND. 7 attacks run (≥6 distinct wrong impls spanning partial-domain, boundary, control-flow-effect, flag-drop, prepatch re-encodes + 1 ungrounded-oracle echo). Every wrong impl is rejected by verification with genuine unsolved-goals proof failures (not infra/timeout). The sole verifying attack (echo) had its materialized faithful patch executed through run_resolve and RESOLVED=True. No verifying wrong impl whose patch fails to resolve exists — the spec does not admit verify⇏︎correct.

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
None found. The two method postconditions fully pin each output to the pure model function (emitReturnTypeEntry: out = returnTypeEntry ...; emitReturnTypeForKind: out = returnTypeEntryForKind ... plus two pinned-regime ensures). No output component is left free, so any impl that verifies must compute exactly the model function — hence its faithful refined patch is the gold patch, which resolves. No verifying-but-wrong impl exists.
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
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled functions decide a single observable:
--  whether a "return type" entry is appended to a documented object's
--  description, and with what text. The entry-building constructors are pure
--  data assembly, modeled directly as the produced entry text (an
--  `Option (List Char)`: `some t` = an entry carrying text `t` is appended,
--  `none` = no entry is appended) — an I/R transliteration validated against
--  the real implementation by conformance_check.py (G-CONF). The inputs are the
--  observations the decision reads: whether a return annotation exists for the
--  object, whether the description already declares a return type, the return
--  annotation's rendered text, and the object's kind. Every observable is a
--  closed function of these inputs — nothing is borrowed from an oracle, and
--  there is no unchanged library callee whose contract the proof must
--  axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- Whether an object of the given kind must NOT advertise a "None" return type.
   A documented value/function/method that returns `None` legitimately shows a
   `None` return type; a documented *class* must not — a class has no return
   value of its own, so listing `None` as its return type is spurious. The kind
   is the object's descriptor label (`"class"`, `"function"`, `"method"`, …);
   only the class kind triggers the omission. -/
@[grind] def isClassKind (kind : List Char) : Bool := kind == "class".toList

/- The "return type" entry appended to an object's description, as the text it
   carries (`some text`) or its absence (`none`).

   An entry is appended only when the object actually has a return annotation
   (`hasReturnAnno`) AND the description does not already declare a return type
   (`returnInArgs` is false) — declaring it twice would duplicate it. When both
   hold, the entry normally carries the rendered return annotation
   (`returnAnnotation`). The sole exception: when `omitNoneReturnType` is set and
   the annotation is exactly `None`, no entry is appended at all — a `None`
   return type is suppressed for objects that must not advertise one. -/
@[grind] def returnTypeEntry (hasReturnAnno returnInArgs : Bool)
    (returnAnnotation : List Char) (omitNoneReturnType : Bool) : Option (List Char) :=
  if hasReturnAnno && !returnInArgs then
    (if (returnAnnotation == "None".toList) && omitNoneReturnType then none
     else some returnAnnotation)
  else
    none

/- The "return type" entry appended for an object of a given kind. The kind
   decides whether a `None` return type is suppressed: a class kind suppresses
   it, every other kind keeps it. Otherwise the entry is exactly the one
   `returnTypeEntry` describes. -/
@[grind] def returnTypeEntryForKind (kind : List Char) (hasReturnAnno returnInArgs : Bool)
    (returnAnnotation : List Char) : Option (List Char) :=
  returnTypeEntry hasReturnAnno returnInArgs returnAnnotation (isClassKind kind)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Append the "return type" entry to a documented object's description.

   `hasReturnAnno` says the object carries a return annotation; `returnInArgs`
   says the description already declares a return type (so a fresh entry would
   duplicate it); `returnAnnotation` is the rendered annotation text; and
   `omitNoneReturnType` requests that a `None` return type be omitted rather than
   shown. The result is the entry that gets appended — `some text` for an entry
   carrying `text`, or `none` when nothing is appended. A fresh result is built
   and no input is mutated (directive 5). -/
method emitReturnTypeEntry (hasReturnAnno : Bool) (returnInArgs : Bool)
    (returnAnnotation : List Char) (omitNoneReturnType : Bool)
    return (out : Option (List Char))
  ensures out = returnTypeEntry hasReturnAnno returnInArgs returnAnnotation omitNoneReturnType
  do
    -- impl-start
    if hasReturnAnno && !returnInArgs then
      if (returnAnnotation == "None".toList) && omitNoneReturnType then
        return none
      else
        return (some returnAnnotation)
    else
      return none
    -- impl-end

prove_correct emitReturnTypeEntry by
  loom_solve

/- Append the "return type" entry for an object of a given `kind`. The kind
   alone selects the policy: for a class, a `None` return type is omitted (a
   class advertising `None` as its return type is spurious); for every other
   kind the entry is produced exactly as for any documented object. The
   remaining inputs and the result are as in `emitReturnTypeEntry`.

   `kind` and the other inputs are read-only (not `mut`): the routine selects the
   policy and delegates, mutating no input (directive 5). The produced entry is
   pinned for both regimes, so no result component is left free. -/
method emitReturnTypeForKind (kind : List Char) (hasReturnAnno : Bool) (returnInArgs : Bool)
    (returnAnnotation : List Char)
    return (out : Option (List Char))
  ensures out = returnTypeEntryForKind kind hasReturnAnno returnInArgs returnAnnotation
  ensures (kind = "class".toList ∧ hasReturnAnno = true ∧ returnInArgs = false
           ∧ returnAnnotation = "None".toList) → out = none
  ensures (kind ≠ "class".toList ∧ hasReturnAnno = true ∧ returnInArgs = false)
           → out = some returnAnnotation
  do
    -- impl-start
    if isClassKind kind then
      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation true
      return r
    else
      let r ← emitReturnTypeEntry hasReturnAnno returnInArgs returnAnnotation false
      return r
    -- impl-end

prove_correct emitReturnTypeForKind by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity, plan §4). Scratch dir: same_spec=True confirmed for all 7 attacks + positive control via swebench_unified.markers.same_spec (velvet). Verifier: scripts/lean_verify.sh (exit 0=verifies, 1=error). Verifications run concurrently in two background batches of ≤4.

### ATTACKS (all same-spec; impl-region-only edits, axioms/pure/pre/post byte-identical):
- atk_1 (prepatch bug #1 re-encode: emitReturnTypeEntry drops the None-suppression branch, always appends some returnAnnotation). cmd: `bash scripts/lean_verify.sh atk_1.lean` -> exit 1 (unsolved goals @88:34). Correctly REJECTED.
- atk_2 (prepatch bug #2 re-encode: emitReturnTypeForKind ignores kind, always delegates with suppress=false). -> exit 1 (unsolved goals @117:36). Correctly REJECTED.
- atk_3 (partial-domain: emitReturnTypeEntry returns none unconditionally). -> exit 1 (unsolved goals @85:34). Correctly REJECTED.
- atk_4 (boundary: suppress None regardless of omitNoneReturnType flag — drop the && omitNoneReturnType conjunct). -> exit 1 (unsolved goals @91:34). Correctly REJECTED.
- atk_5 (control-flow-effect: swap the suppress-flag true/false between the class and non-class branches of emitReturnTypeForKind). -> exit 1 (unsolved goals @121:36). Correctly REJECTED.
- atk_6 (ungrounded-oracle echo: emitReturnTypeEntry returns the pure model fn `returnTypeEntry ...` verbatim). -> exit 0 VERIFIES. This is behaviorally IDENTICAL to the model (a correct echo, not a weakness). Per protocol its faithful refined patch = the gold patch (verbatim); RAN through official harness: `run_resolve('sphinx-doc__sphinx-10449', gold_patch, timeout=1800, retries=1)` -> RESOLVED: True, COMPLETED: True, NOTE: resolved (log: resolve_atk6.log). verify⇒correct holds.
- atk_7 (boundary: flip guard to `hasReturnAnno && returnInArgs`). -> exit 1 (unsolved goals @91:34). Correctly REJECTED.

Positive control pos_control.lean (frozen Solution.lean impl) -> exit 0 verifies. prepatch_reproduced: both prepatch bugs re-encoded as atk_1/atk_2 and confirmed to FAIL verification (matches refinement.md §A/§B G-DIFF claims).

REFINEMENT AUDIT (§4 A-legs focus): meta.json axioms=[] and deep_model_references=[] — the A-legs are VACUOUS (no axiom consumed, no deep-model reference), so there is no callee-correspondence to falsify. refinement.md §C correctly declares every leg R or I with NO kind-3 (inexpressible-changed-op) step; G-AX=skip is legitimate. inter_method_calls: emitReturnTypeForKind->emitReturnTypeEntry discharged by emitReturnTypeEntry_correct (callee-under-spec, strictly stronger than an axiom). Model↔patch correspondence is tight: the two postconditions fully pin outputs to the pure functions returnTypeEntry / returnTypeEntryForKind (plus emitReturnTypeForKind's two pinned-regime ensures for the class-None and non-class cases), leaving no free output component. Therefore any verifying impl computes exactly the model function and its faithful patch is the gold patch, which resolves.

VERDICT: SOUND. 7 attacks run (≥6 distinct wrong impls spanning partial-domain, boundary, control-flow-effect, flag-drop, prepatch re-encodes + 1 ungrounded-oracle echo). Every wrong impl is rejected by verification with genuine unsolved-goals proof failures (not infra/timeout). The sole verifying attack (echo) had its materialized faithful patch executed through run_resolve and RESOLVED=True. No verifying wrong impl whose patch fails to resolve exists — the spec does not admit verify⇏︎correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on the velvet spec for sphinx-doc__sphinx-10449.

SCOPE: The spec models two additive slices of the gold patch in sphinx/ext/autodoc/typehints.py: (1) modify_field_list's trailing `if 'return' in annotations and 'return' not in arguments:` block gaining `annotation = annotations['return']; if annotation == 'None' and suppress_rtype: return`  -> emitReturnTypeEntry/returnTypeEntry; (2) merge_typehints's `all` arm gaining `if objtype == 'class': ...suppress_rtype=True else ...` -> emitReturnTypeForKind/returnTypeEntryForKind. Observable abstracted: whether an rtype field entry is appended and the text it carries (Option (List Char)); mapping.md §2 R-legs (str<->List Char, membership<->Bool, suppress_rtype<->omitNoneReturnType, objtype=='class'<->isClassKind).

SPEC-REGION INTEGRITY: swebench_unified.markers.same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True -> the two diff-detecting prepatch variants differ from Solution ONLY in impl regions, not in the spec view. Spec signatures identical.

VERIFICATION: Solution.lean elaborates clean under lean_verify.sh (exit 0, 600s) -> postconditions are non-vacuous and provable; the extra pinned postconditions on emitReturnTypeForKind (class+None+hasAnno+!inArgs -> none; non-class+hasAnno+!inArgs -> some returnAnnotation) hold.

DIFFERENTIAL vs REAL PATCHED CALLEE: fetched base_commit 36367765..., applied patch.diff, and ran the Lean I/R shadow (returnTypeEntryForKind transliterated) against the REAL gold-patched modify_field_list driven on synthetic docutils field_lists (suppress_rtype selected per objtype == 'class', exactly the patched merge_typehints 'all' arm). 200,392 inputs (full boundary matrix over kinds x hasReturnAnno x returnInArgs x annotation-strings incl. 'None','None ','none','NoneType','',whitespace + seeded fuzz): 0 disagreements. A second, harder differential with the unchanged per-parameter loop ACTIVE (random extra param fields + random non-return annotation keys, 50,000 inputs): 0 disagreements — confirming the modeled slice isolation is honest and the surrounding unchanged code does not perturb the appended rtype entry the spec claims to decide.

No input found on which the modeled function is stronger than / drifts from the real callee. conformance_check.py (seed 10449, N=1e5) mirrors this differential. No overclaimed postcondition. Spec is a faithful, non-overstrong model of the gold-patched behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, zero hard failures) and same_spec confirms the spec regions are byte-identical across Solution.lean and both prepatch variants. Semantic gold-reconstruction review of the spec view: (1) No gold-patch repo symbols surface — the edit's identifiers (modify_field_list, merge_typehints, suppress_rtype, objtype, annotations['return']) are all abstracted to backend-neutral spec names (emitReturnTypeEntry, omitNoneReturnType, kind, returnInArgs); no patched file path (sphinx/ext/autodoc/typehints.py), no diff markers, no reproduced gold-diff line. (2) The discriminating content the spec encodes — class kind + annotation 'None' ⇒ suppress the entry (out = none), non-class ⇒ some returnAnnotation — is a direct formalization of the PUBLIC problem_statement, which explicitly states the class Square(__init__ -> None) case and 'I expected there to be no return type listed for the class.' The spec reveals nothing beyond that public expectation. (3) The guard hasReturnAnno && !returnInArgs corresponds to pre-existing surrounding code (`if 'return' in annotations and 'return' not in arguments`), not the added edit, so it leaks no localization. (4) Doc-comments describe behavior abstractly using only vocabulary already public in the problem statement (class, return type, None); no fix/bug narration and no repo-internal edit terms. changed_symbols {modify_field_list, merge_typehints, insert_field_list} do not appear in the spec view. Conclusion: the spec view is a faithful abstraction of publicly-known desired behavior and does not leak the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
