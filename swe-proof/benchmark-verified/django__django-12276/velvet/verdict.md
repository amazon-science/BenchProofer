# P2 adversarial audit — django__django-12276

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists, so no faithful refined patch could be materialized to run through run_resolve. The spec is a tight functional equality `out = (inheritedRequiredDecision hasInitial && !hasInitial)` and every same-spec wrong impl leaves a genuine unsolved-goals equation (verified below), so verify⇒correct holds on the exhibited attack surface.
```

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
 /- The inherited base-widget decision about whether a required-style marker is
@@ -44,9 +44,7 @@
   ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
   do
     -- impl-start
-    -- Defer to the inherited base decision (an opaque inherited routine), then
-    -- conjoin with the absence of an existing value.
-    return (inheritedRequiredDecision hasInitial && !hasInitial)
+    return (inheritedRequiredDecision hasInitial)
     -- impl-end
 
 prove_correct useRequiredAttribute by
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
 /- The inherited base-widget decision about whether a required-style marker is
@@ -44,9 +44,7 @@
   ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
   do
     -- impl-start
-    -- Defer to the inherited base decision (an opaque inherited routine), then
-    -- conjoin with the absence of an existing value.
-    return (inheritedRequiredDecision hasInitial && !hasInitial)
+    return (!hasInitial)
     -- impl-end
 
 prove_correct useRequiredAttribute by
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
 /- The inherited base-widget decision about whether a required-style marker is
@@ -44,9 +44,7 @@
   ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
   do
     -- impl-start
-    -- Defer to the inherited base decision (an opaque inherited routine), then
-    -- conjoin with the absence of an existing value.
-    return (inheritedRequiredDecision hasInitial && !hasInitial)
+    return (inheritedRequiredDecision hasInitial || !hasInitial)
     -- impl-end
 
 prove_correct useRequiredAttribute by
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
 /- The inherited base-widget decision about whether a required-style marker is
@@ -44,9 +44,7 @@
   ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
   do
     -- impl-start
-    -- Defer to the inherited base decision (an opaque inherited routine), then
-    -- conjoin with the absence of an existing value.
-    return (inheritedRequiredDecision hasInitial && !hasInitial)
+    return (inheritedRequiredDecision hasInitial && hasInitial)
     -- impl-end
 
 prove_correct useRequiredAttribute by
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
 /- The inherited base-widget decision about whether a required-style marker is
@@ -44,9 +44,7 @@
   ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
   do
     -- impl-start
-    -- Defer to the inherited base decision (an opaque inherited routine), then
-    -- conjoin with the absence of an existing value.
-    return (inheritedRequiredDecision hasInitial && !hasInitial)
+    return false
     -- impl-end
 
 prove_correct useRequiredAttribute by
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
 /- The inherited base-widget decision about whether a required-style marker is
@@ -44,9 +44,7 @@
   ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
   do
     -- impl-start
-    -- Defer to the inherited base decision (an opaque inherited routine), then
-    -- conjoin with the absence of an existing value.
-    return (inheritedRequiredDecision hasInitial && !hasInitial)
+    return true
     -- impl-end
 
 prove_correct useRequiredAttribute by
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
 /- The inherited base-widget decision about whether a required-style marker is
@@ -44,9 +44,7 @@
   ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
   do
     -- impl-start
-    -- Defer to the inherited base decision (an opaque inherited routine), then
-    -- conjoin with the absence of an existing value.
-    return (inheritedRequiredDecision hasInitial && !hasInitial)
+    return (inheritedRequiredDecision (!hasInitial))
     -- impl-end
 
 prove_correct useRequiredAttribute by
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
 /- The inherited base-widget decision about whether a required-style marker is
@@ -44,9 +44,10 @@
   ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
   do
     -- impl-start
-    -- Defer to the inherited base decision (an opaque inherited routine), then
-    -- conjoin with the absence of an existing value.
-    return (inheritedRequiredDecision hasInitial && !hasInitial)
+    if hasInitial then
+      return (inheritedRequiredDecision hasInitial)
+    else
+      return (inheritedRequiredDecision hasInitial)
     -- impl-end
 
 prove_correct useRequiredAttribute by
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
 /- The inherited base-widget decision about whether a required-style marker is
@@ -44,9 +44,10 @@
   ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
   do
     -- impl-start
-    -- Defer to the inherited base decision (an opaque inherited routine), then
-    -- conjoin with the absence of an existing value.
-    return (inheritedRequiredDecision hasInitial && !hasInitial)
+    if hasInitial then
+      return true
+    else
+      return (inheritedRequiredDecision hasInitial && !hasInitial)
     -- impl-end
 
 prove_correct useRequiredAttribute by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The inherited base-widget decision about whether a required-style marker is
   appropriate for this control, given whether the form already carries a value
   for the field. This is an UNCHANGED inherited routine the operation defers to;
   it is left OPAQUE (a free function) — the operation refines it, never replaces
   it, so no contract is claimed about its return value. Provenance: mapping.md.
   Because it is a free function with no asserted `ensures`, there is nothing to
   validate against the real callee (no axiom_check.py — meta.json G-AX skip). -/
opaque inheritedRequiredDecision : Bool → Bool
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A file-upload control decides whether to advertise a required-style marker on
   its rendered element. The desired behavior: the control advertises the marker
   only when the inherited base decision would allow it AND the form does not
   already carry an existing value for this field. When an existing value is
   present, the user may legitimately leave the control blank to keep that value,
   so the marker must be suppressed even if the base decision alone would permit
   it.

   `hasInitial` is the read-only flag for "an existing value is already present"
   (not `mut`); the routine computes a single boolean and mutates nothing
   (directive 5). The inherited base decision is deferred to as an opaque input
   (a free function of `hasInitial`); the result is its conjunction with the
   absence of an existing value. -/
method useRequiredAttribute (hasInitial : Bool) return (out : Bool)
  ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
  do
    -- impl-start
    if hasInitial then
      return false
    else
      return (inheritedRequiredDecision hasInitial)
    -- impl-end

prove_correct useRequiredAttribute by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: single deterministic functional equality — ensures out = (inheritedRequiredDecision hasInitial && !hasInitial), where inheritedRequiredDecision : Bool -> Bool is opaque. Because the postcondition fully pins `out` for all 2^2 inputs against an uninterpreted opaque term, the only verifying impl is the gold-equivalent formula; the opaque term cannot free-discharge because `&& !hasInitial` grounds the result in the actual input.

ATTACKS (all same_spec=True vs frozen Solution.lean, confirmed via swebench_unified.markers.same_spec on backend velvet; impl region ONLY edited, axioms/pre/post/ensures byte-identical). Command per file: `bash scripts/lean_verify.sh <path>`.

Ran concurrently in batches of 4. atk_1 = prepatch bug (missing conjunct): return (inheritedRequiredDecision hasInitial) -> exit 1, unsolved goal `inheritedRequiredDecision hasInitial = (inheritedRequiredDecision hasInitial && !hasInitial)`. atk_2 (drop inherited): return (!hasInitial) -> exit 1. atk_3 (operator swap OR): return (inheritedRequiredDecision hasInitial || !hasInitial) -> exit 1, goal `(... || !hasInitial) = (... && !hasInitial)`. atk_4 (boundary, forgot negation): return (inheritedRequiredDecision hasInitial && hasInitial) -> exit 1. atk_5 (constant false): return false -> exit 1. atk_6 (constant true): return true -> exit 1. atk_7 (ungrounded-oracle echo on wrong arg): return (inheritedRequiredDecision (!hasInitial)) -> exit 1, goal `(inheritedRequiredDecision !hasInitial) = (inheritedRequiredDecision hasInitial && !hasInitial)`. atk_8 (control-flow-effect: branch that returns inherited on both paths): if hasInitial then return (inheritedRequiredDecision hasInitial) else return (inheritedRequiredDecision hasInitial) -> exit 1, goal `inheritedRequiredDecision hasInitial = (... && !hasInitial)`. atk_9 (branch, correct-when-false but true-when-hasInitial): if hasInitial then return true else return (inheritedRequiredDecision hasInitial && !hasInitial) -> exit 1, goal `true = (... && !hasInitial)`. All 9 rejections are genuine `error: unsolved goals` (not syntax/type errors), inspected in the .lean.out files.

POSITIVE CONTROL (structurally different, semantically correct): if hasInitial then return false else return (inheritedRequiredDecision hasInitial) -> same_spec=True, verify exit 0. Spec is non-vacuous.

RESOLVE STEP: N/A — zero verifying wrong impls, so there is no verifying-impl faithful patch to materialize/run through run_resolve. The verify=>correct break (BROKEN) can only be exhibited by a VERIFYING wrong impl whose patch fails resolve; none exists here. `patches` is therefore empty and no run_resolve was required.

REFINEMENT AUDIT (refinement.md, A-legs focus): confirmed against the real repo at base_commit 53d8646f799de7f92ab9defe9dc56c6125448102 (worktree, `git show <base>:django/forms/widgets.py`): Widget.use_required_attribute (widgets.py:275-276) = `return not self.is_hidden` (the A2 opaque callee reached via super()); class FileInput at :374 has NO use_required_attribute override pre-patch (inherits Widget); ClearableFileInput.use_required_attribute = `return super().use_required_attribute(initial) and not initial` — exactly the method the gold patch MOVES up into FileInput. Leg tags: A1=R (initial truthiness bool(initial) <-> Bool hasInitial; `not initial` <-> `!hasInitial`, exact bijection), A2=A-consumed (opaque super()/Widget callee, no asserted ensures -> G-AX legitimately VACUOUS/skip; opaque cannot mask a missing conjunct), A3=I (`and not initial` <-> `&& !hasInitial`, deeply modeled, G-CONF-testable), A4=I (short-circuit && over bools). No kind-3 op. A-leg correspondence to the real callee holds.

VERDICT: SOUND. >=9 distinct same-spec attacks run (partial-domain/missing-conjunct, boundary, operator-swap, control-flow-effect branch, constants, ungrounded-oracle echo), all rejected for the right reason; positive control verifies; prepatch bug reproduced; A-leg refinement correspondence verified against base-commit source. No verify=>correct break exhibited.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists, so no faithful refined patch could be materialized to run through run_resolve. The spec is a tight functional equality `out = (inheritedRequiredDecision hasInitial && !hasInitial)` and every same-spec wrong impl leaves a genuine unsolved-goals equation (verified below), so verify⇒correct holds on the exhibited attack surface.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The inherited base-widget decision about whether a required-style marker is
   appropriate for this control, given whether the form already carries a value
   for the field. This is an UNCHANGED inherited routine the operation defers to;
   it is left OPAQUE (a free function) — the operation refines it, never replaces
   it, so no contract is claimed about its return value. Provenance: mapping.md.
   Because it is a free function with no asserted `ensures`, there is nothing to
   validate against the real callee (no axiom_check.py — meta.json G-AX skip). -/
opaque inheritedRequiredDecision : Bool → Bool
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A file-upload control decides whether to advertise a required-style marker on
   its rendered element. The desired behavior: the control advertises the marker
   only when the inherited base decision would allow it AND the form does not
   already carry an existing value for this field. When an existing value is
   present, the user may legitimately leave the control blank to keep that value,
   so the marker must be suppressed even if the base decision alone would permit
   it.

   `hasInitial` is the read-only flag for "an existing value is already present"
   (not `mut`); the routine computes a single boolean and mutates nothing
   (directive 5). The inherited base decision is deferred to as an opaque input
   (a free function of `hasInitial`); the result is its conjunction with the
   absence of an existing value. -/
method useRequiredAttribute (hasInitial : Bool) return (out : Bool)
  ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)
  do
    -- impl-start
    if hasInitial then
      return false
    else
      return (inheritedRequiredDecision hasInitial)
    -- impl-end

prove_correct useRequiredAttribute by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: single deterministic functional equality — ensures out = (inheritedRequiredDecision hasInitial && !hasInitial), where inheritedRequiredDecision : Bool -> Bool is opaque. Because the postcondition fully pins `out` for all 2^2 inputs against an uninterpreted opaque term, the only verifying impl is the gold-equivalent formula; the opaque term cannot free-discharge because `&& !hasInitial` grounds the result in the actual input.

ATTACKS (all same_spec=True vs frozen Solution.lean, confirmed via swebench_unified.markers.same_spec on backend velvet; impl region ONLY edited, axioms/pre/post/ensures byte-identical). Command per file: `bash scripts/lean_verify.sh <path>`.

Ran concurrently in batches of 4. atk_1 = prepatch bug (missing conjunct): return (inheritedRequiredDecision hasInitial) -> exit 1, unsolved goal `inheritedRequiredDecision hasInitial = (inheritedRequiredDecision hasInitial && !hasInitial)`. atk_2 (drop inherited): return (!hasInitial) -> exit 1. atk_3 (operator swap OR): return (inheritedRequiredDecision hasInitial || !hasInitial) -> exit 1, goal `(... || !hasInitial) = (... && !hasInitial)`. atk_4 (boundary, forgot negation): return (inheritedRequiredDecision hasInitial && hasInitial) -> exit 1. atk_5 (constant false): return false -> exit 1. atk_6 (constant true): return true -> exit 1. atk_7 (ungrounded-oracle echo on wrong arg): return (inheritedRequiredDecision (!hasInitial)) -> exit 1, goal `(inheritedRequiredDecision !hasInitial) = (inheritedRequiredDecision hasInitial && !hasInitial)`. atk_8 (control-flow-effect: branch that returns inherited on both paths): if hasInitial then return (inheritedRequiredDecision hasInitial) else return (inheritedRequiredDecision hasInitial) -> exit 1, goal `inheritedRequiredDecision hasInitial = (... && !hasInitial)`. atk_9 (branch, correct-when-false but true-when-hasInitial): if hasInitial then return true else return (inheritedRequiredDecision hasInitial && !hasInitial) -> exit 1, goal `true = (... && !hasInitial)`. All 9 rejections are genuine `error: unsolved goals` (not syntax/type errors), inspected in the .lean.out files.

POSITIVE CONTROL (structurally different, semantically correct): if hasInitial then return false else return (inheritedRequiredDecision hasInitial) -> same_spec=True, verify exit 0. Spec is non-vacuous.

RESOLVE STEP: N/A — zero verifying wrong impls, so there is no verifying-impl faithful patch to materialize/run through run_resolve. The verify=>correct break (BROKEN) can only be exhibited by a VERIFYING wrong impl whose patch fails resolve; none exists here. `patches` is therefore empty and no run_resolve was required.

REFINEMENT AUDIT (refinement.md, A-legs focus): confirmed against the real repo at base_commit 53d8646f799de7f92ab9defe9dc56c6125448102 (worktree, `git show <base>:django/forms/widgets.py`): Widget.use_required_attribute (widgets.py:275-276) = `return not self.is_hidden` (the A2 opaque callee reached via super()); class FileInput at :374 has NO use_required_attribute override pre-patch (inherits Widget); ClearableFileInput.use_required_attribute = `return super().use_required_attribute(initial) and not initial` — exactly the method the gold patch MOVES up into FileInput. Leg tags: A1=R (initial truthiness bool(initial) <-> Bool hasInitial; `not initial` <-> `!hasInitial`, exact bijection), A2=A-consumed (opaque super()/Widget callee, no asserted ensures -> G-AX legitimately VACUOUS/skip; opaque cannot mask a missing conjunct), A3=I (`and not initial` <-> `&& !hasInitial`, deeply modeled, G-CONF-testable), A4=I (short-circuit && over bools). No kind-3 op. A-leg correspondence to the real callee holds.

VERDICT: SOUND. >=9 distinct same-spec attacks run (partial-domain/missing-conjunct, boundary, operator-swap, control-flow-effect branch, constants, ungrounded-oracle echo), all rejected for the right reason; positive control verifies; prepatch bug reproduced; A-leg refinement correspondence verified against base-commit source. No verify=>correct break exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec via VelvetBackend.language = True). Solution.lean verifies (lean_verify.sh EXIT=0).

Modeled function: method useRequiredAttribute (hasInitial : Bool) with ensures out = (inheritedRequiredDecision hasInitial && !hasInitial), where inheritedRequiredDecision is an OPAQUE free function (no asserted contract).

Real callee (gold-patched FileInput.use_required_attribute at base_commit 53d8646f): body `return super().use_required_attribute(initial) and not initial`. Confirmed worktree: super() resolves to grandparent Widget.use_required_attribute = `not self.is_hidden`; for a visible FileInput (is_hidden=False) it is True regardless of initial. Empirically checked: base FileInput.use_required_attribute returns True for None, '', 'resume.txt', 0, [], ['x'] (pre-patch, no suppression) — consistent with mapping.md provenance.

Faithfulness argument (no divergence exists):
1. Truthiness abstraction is EXACT: Python `not initial` == `not bool(initial)` for every Python value; the R-bijection initial-truthy<->hasInitial=true maps `not initial` to `!hasInitial` with no loss. No input diverges here.
2. The inherited decision is modeled with the WEAKEST contract (opaque, nothing asserted). Because the spec asserts no value for inheritedRequiredDecision, it is satisfiable by the exact real behavior — instantiate inheritedRequiredDecision := (fun _ => not is_hidden), reproducing super()'s value on every input. A too-strong spec would require the modeled function to disagree with the real callee on some input; here for any (base, hasInitial) the modeled out = base && !hasInitial equals the real (not is_hidden) && (not initial) once base is bound to the real super() value. There is no input where the modeled function is forced to a value the real repo callee does not produce.
3. The discriminating conjunct `&& !hasInitial` is the identical concrete op the gold patch introduces (I-leg), and G-CONF differential-tests it over all 4 boolean combos + fuzz (seed 12276) with 0 disagreements; oracle transliterates the patched body verbatim.

The spec pins only the STRUCTURE of the fix (out = inherited && !hasInitial), which is neither stronger nor weaker than repo reality on any input. G-DIFF holds: prepatch (returns inherited alone) fails whenever inherited=true & hasInitial=true, matching the described bug. No spec drift, no over-constraint. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec = True with VelvetBackend tables). Spec view = elided Solution.lean (impl-start/impl-end body and proof stripped).

Public problem_statement already discloses the full desired behavior: 'FileInput shouldn't display required attribute when initial data exists' and that use_required_attribute should suppress `required` when a file is already set. The spec view formalizes exactly this behavior — postcondition `ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)` plus prose 'advertise the marker only when the inherited base decision would allow it AND the form does not already carry an existing value'. Pinning behavior already stated publicly is a legitimate spec, not leakage.

No gold-patch specifics beyond problem_statement appear in the spec view: no Python `super().use_required_attribute(initial) and not initial` verbatim, no class names FileInput/ClearableFileInput, no method-move structure, no widgets.py file/line references. The inherited base decision is fully abstracted as an opaque free function `inheritedRequiredDecision : Bool → Bool` with no asserted contract. All repo/patch details (moved method, super() resolution to Widget, file:line) live only in mapping.md and refinement.md, which are NOT part of the spec view.

The `hasInitial`/`!hasInitial` conjunction is the abstract restatement of 'initial data exists → suppress required', which the problem_statement fully conveys. G-DIFF discrimination is properly located in the (elided) impl, not in the spec. No line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.