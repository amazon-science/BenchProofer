# P2 adversarial audit — django__django-11999

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,8 +43,7 @@
   do
     -- impl-start
     let mut result := lookup
-    if (lookup key).isNone then
-      result := (fun n => if n = key then some gen else lookup n)
+    result := (fun n => if n = key then some gen else lookup n)
     return result
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,8 +43,6 @@
   do
     -- impl-start
     let mut result := lookup
-    if (lookup key).isNone then
-      result := (fun n => if n = key then some gen else lookup n)
     return result
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
   do
     -- impl-start
     let mut result := lookup
-    if (lookup key).isNone then
+    if (lookup key).isSome then
       result := (fun n => if n = key then some gen else lookup n)
     return result
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,10 @@
   do
     -- impl-start
     let mut result := lookup
-    if (lookup key).isNone then
+    if key = "get_foo_bar_display" then
+      if (lookup key).isNone then
+        result := (fun n => if n = key then some gen else lookup n)
+    else
       result := (fun n => if n = key then some gen else lookup n)
     return result
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,6 +45,7 @@
     let mut result := lookup
     if (lookup key).isNone then
       result := (fun n => if n = key then some gen else lookup n)
+    result := (fun n => if n = key ++ "_x" then none else result n)
     return result
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,9 +42,13 @@
   ensures out = registerDisplay lookup key gen
   do
     -- impl-start
-    let mut result := lookup
-    if (lookup key).isNone then
-      result := (fun n => if n = key then some gen else lookup n)
+    let mut result : Namespace := lookup
+    let mut i : Nat := 1
+    while i > 0
+      invariant i > 0
+      decreasing i
+    do
+      i := i
     return result
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,10 +42,11 @@
   ensures out = registerDisplay lookup key gen
   do
     -- impl-start
-    let mut result := lookup
     if (lookup key).isNone then
-      result := (fun n => if n = key then some gen else lookup n)
-    return result
+      return (fun n => if n = key then some gen else lookup n)
+    else
+      let r <- registerAccessor lookup key gen
+      return r
     -- impl-end
 
 prove_correct registerAccessor by
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
     -- impl-start
     let mut result := lookup
     if (lookup key).isNone then
-      result := (fun n => if n = key then some gen else lookup n)
+      result := (fun n => if n = key then some 1 else lookup n)
     return result
     -- impl-end
 
```

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,8 +42,16 @@
   ensures out = registerDisplay lookup key gen
   do
     -- impl-start
-    let mut result := lookup
+    let mut result : Namespace := lookup
     if (lookup key).isNone then
+      result := (fun n => if n = key then some gen else lookup n)
+    else
+      let mut i : Nat := 1
+      while i > 0
+        invariant i > 0
+        decreasing i
+      do
+        i := i
       result := (fun n => if n = key then some gen else lookup n)
     return result
     -- impl-end
```

Attack 10 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,10 @@
   do
     -- impl-start
     let mut result := lookup
-    if (lookup key).isNone then
+    if gen = 1 then
+      if (lookup key).isNone then
+        result := (fun n => if n = key then some gen else lookup n)
+    else
       result := (fun n => if n = key then some gen else lookup n)
     return result
     -- impl-end
```

Attack 11 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
   do
     -- impl-start
     let mut result := lookup
-    if (lookup key).isNone then
+    if (lookup key).isNone ∨ lookup key = some 1 then
       result := (fun n => if n = key then some gen else lookup n)
     return result
     -- impl-end
```

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,9 +42,12 @@
   ensures out = registerDisplay lookup key gen
   do
     -- impl-start
-    let mut result := lookup
-    if (lookup key).isNone then
+    let mut result : Namespace := lookup
+    if key = "" then
       result := (fun n => if n = key then some gen else lookup n)
+    else
+      if (lookup key).isNone then
+        result := (fun n => if n = key then some gen else lookup n)
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No unchanged dependency callee is CONSUMED by this specification. The
-- registration step is modeled structurally below as a single-name update on a
-- class namespace, so there is no `axiom`/stub callee to declare. The accessor
-- that would be generated is taken as an abstract token (`gen`): the step never
-- inspects its value, only whether the target name is already bound.
-- axioms-end

-- pure-start
/- A class namespace, viewed as the partial map from an accessor name to the
   identity of the attribute bound there: `some t` when the name is bound to an
   attribute of identity-kind `t`, `none` when the name is free. -/
abbrev Namespace := String → Option Nat

/- Install the generated accessor `gen` at name `key`, but only when that name is
   currently free. When the name is already bound, the namespace is returned
   unchanged, so whatever was bound there stays in force; every other name is
   left untouched in both cases. -/
def registerDisplay (lookup : Namespace) (key : String) (gen : Nat) : Namespace :=
  if (lookup key).isNone then
    (fun n => if n = key then some gen else lookup n)
  else
    lookup
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method registerAccessor (lookup : Namespace) (key : String) (gen : Nat)
  return (out : Namespace)
  ensures out = registerDisplay lookup key gen
  do
    -- impl-start
    let mut result := lookup
    if (lookup key).isNone then
      result := (fun n => if n = key then some gen else lookup n)
    return result
    -- impl-end

prove_correct registerAccessor by
  loom_solve <;> simp_all [registerDisplay]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity, docs/architecture.md §5) for django__django-11999 / velvet. VERDICT: SOUND. 12 distinct same-spec wrong impls encoded and machine-verified; every one REJECTED. The single verifying same-spec impl is functionally EQUIVALENT to gold, and its faithful refined patch was materialized and RESOLVED under the official harness. No verify-but-wrong witness exists => no verify⇏correct break found.

 Every attack was built by copying the frozen Solution.lean and editing ONLY the impl region; axioms/pure/pre/post bytes untouched.

### SAME-SPEC (all True, re-verified after all repairs):
  python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('.../velvet/Solution.lean').read(), open('atk_N.lean').read(), b.language))"
  -> atk_1..atk_13 = True, pos_control = True (ALL_SAME_SPEC=True).

**POSITIVE CONTROL.** pos_control.lean (byte copy of frozen Solution.lean).
  bash scripts/lean_verify.sh pos_control.lean  ->  EXIT=0 (verifies, no sorry). The spec is satisfiable by the gold impl, so the 12 rejections below are real discrimination, not a broken harness.

ATTACK RESULTS (all run as `bash scripts/lean_verify.sh atk_N.lean`; exit 1 = rejected. Batches of 4 launched concurrently as background jobs; schedule only, pass criteria unchanged).

atk_1  EXIT=1  PREPATCH BUG REPRODUCED — unconditional overwrite (`result := fun n => if n = key then some gen else lookup n`), i.e. the base_commit `setattr(cls,'get_%s_display'%self.name,partialmethod(...))` with no guard. Rejected on exactly the discriminating goal: `⊢ ¬lookup key = none → (fun n => if n = key then some gen else lookup n) = lookup`. This is the user-override-displaced defect the F2P test observes. atk_2  EXIT=1  no-op (never installs). Goal `lookup key = none → lookup = fun n => ...`. atk_3  EXIT=1  inverted guard (`.isSome`).

BOTH legs unsolved. atk_4  EXIT=1  PARTIAL-DOMAIN / test-name special case — set-if-absent only when `key = "get_foo_bar_display"` (the exact accessor the FAIL_TO_PASS test `test_overriding_FIELD_display` touches), buggy overwrite for every other field name. Rejected with `if_neg : ¬key = "get_foo_bar_display"` in context. IMPORTANT: this is the classic F2P-overfit impl that would PASS the Django test suite yet be wrong in general; the spec's universally-quantified functional equality kills it. Strong evidence the spec is not test-shaped. atk_5  EXIT=1  CONTROL-FLOW-EFFECT / frame violation — right answer at `key`, but also unbinds the neighbour `key ++ "_x"` (models an extra delattr on the class namespace).

Both legs unsolved => the frame is genuinely pinned at every name, not just at `key`. atk_6  EXIT=1  DIVERGENCE / VACUITY probe — `while i > 0 ... i := i` with `decreasing i`, then a wrong (no-install) result. Rejected on `case «decreasing_1: i» ... ⊢ False`. Confirms `loom.semantics.termination "total"` really discharges a termination obligation; a diverging impl cannot vacuously satisfy the functional-equality postcondition here. (First-draft typing error `OfNat (Option ℕ) 0` was repaired with explicit `: Namespace` / `: Nat` annotations so the file elaborates and fails SEMANTICALLY, not on elaboration.) atk_7  EXIT=1  guarded self-call divergence — the else leg recurses `registerAccessor lookup key gen` on identical arguments.

Rejected: `fail to show termination for registerAccessor ... no parameters suitable for structural recursion`. atk_9  EXIT=1  hardcoded token — installs `some 1` (the auto kind fixed by mapping.md) instead of the parameter `gen`. Goal `(fun n => if n = key then some 1 else lookup n) = fun n => if n = key then some gen else lookup n`. The token is not allowed to be constant-folded. atk_10 EXIT=1  SHARPEST VACUITY ATTACK — exactly correct on the free-name leg, but on the DISCRIMINATING leg (`¬lookup key = none`, i.e. a user accessor already present) it diverges and then returns the prepatch overwrite. Under partial-correctness semantics this would verify vacuously while being wrong precisely where the F2P test looks.

Rejected on `case «decreasing_1: i» ... if_neg : ¬lookup key = none ... ⊢ False`. This closes the divergence-vacuity hole noted in the bundle's own verdict.md (which claimed "partial" semantics; the FROZEN Solution.lean sets termination "total", and the obligation is in fact generated and unprovable). atk_11 EXIT=1  partial domain on the token — set-if-absent only when `gen = 1`, overwrite otherwise. `if_neg : ¬gen = 1` in context. atk_12 EXIT=1  BOUNDARY — treats a name bound to the auto kind (`some 1`) as free, so an existing auto-generated accessor is re-installed while a user one is kept.

Rejected: the spec keys on presence only, never on the bound value's kind — matching real `hasattr`, which does not inspect what is bound. atk_13 EXIT=1  BOUNDARY — single-point hole at the empty key `""`. Rejected with `if_pos : key = ""`; not even a measure-zero domain hole survives.

MANDATORY RESOLVE RUN (protocol step 2). Exactly one same-spec attack VERIFIES: atk_8  EXIT=0  ungrounded-oracle-echo probe — impl is `let result := registerDisplay lookup key gen; return result`, i.e. it returns the pure spec helper verbatim.

Because I must materialize and RUN the faithful patch for EVERY verifying impl: patch: atk_8_faithful.patch (hasattr-guarded setattr, refactored via a `display_attr` local — the faithful refinement of "install only when the name is free"). pre-check: `git apply --check -v` at base_commit 84633905273fc916e3d17883810d9969c03f73c2 -> APPLY_CHECK=OK. command: python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-11999', open('atk_8_faithful.patch').read(), run_id='sbu-audit-eq-11999-atk8'); print(r)" OBSERVED: resolved=True, completed=True, attempts=1, flaky=False, note='resolved'.

FAIL_TO_PASS success=['test_overriding_FIELD_display (model_fields.tests.GetFieldDisplayTests)'], failure=[]; PASS_TO_PASS 30/30 success, failure=[]; PASS_TO_FAIL=[] , FAIL_TO_FAIL=[]. => The verifying impl's faithful patch DOES resolve. This is NOT a break: atk_8 is functionally identical to `registerDisplay` (it IS the set-if-absent function), so it is a correct impl, not a wrong one — the spec's postcondition `out = registerDisplay lookup key gen` is total functional equality, so any verifying impl is pointwise equal to gold and therefore refines to a resolving patch. atk_8 is reported for protocol completeness and is EXCLUDED from the `attacks` list (it is not a wrong impl).

Note the echo does not indicate an ungrounded oracle: `registerDisplay` is an input-grounded pure helper (a computation over `lookup`/`key`/`gen`), not an oracle naming the answer — spelling it out is just an inlining of the same computation. (A true `:|` demonic-choice oracle echo, `let result :| result = registerDisplay lookup key gen`, does NOT even elaborate: `failed to synthesize Findable ...`. Recorded as an elaboration failure, not counted among the 12.)

### REFINEMENT.MD LEG AUDIT (my assigned focus: A-legs + model↔patch correspondence).
 - Tag inventory: 6 legs, tags {R,R,R,I,I,I} — legs 1-3 R (carrier bijections), legs 4-6 I (identical concrete ops). ZERO kind-3 (untagged/unjustified) legs. Complies with the R / A-consumed / A-reference / I requirement.
 - **A-LEGS:** there are NONE, and that is CORRECT, not an evasion. Mechanically confirmed the frozen Solution.lean contains 0 `axiom` declarations and 0 `:|` stub callees; the axioms region is a prose note explaining why. The changed op is modeled DEEPLY (a presence test on `lookup` plus a single-name functional update), so per SPEC_GUIDE §3 it must not be axiomatized — an axiom here would be the defect. Consequently there is no A-consumed `ensures` the proof could lean on, and no A-reference deep model whose correspondence to a real callee could drift: the proof obligation is discharged against the structural definition alone. G-AX correctly skips. This removes the entire attack surface my lane is aimed at — there is no axiom to over-strengthen and no deep model to mis-mirror.
 - The one entity that COULD have been an A-reference — the auto accessor `partialmethod(cls._get_FIELD_display, field=self)` — is correctly demoted to the opaque token `gen`, because the registration step never observes its value, only its presence at `key`. atk_9 (hardcoded `some 1`) confirms the token is a genuine parameter and not silently pinned; the spec is agnostic to the accessor's internals, which is exactly the real code's behavior.
 - Correspondence of the I-legs to the real gold patch, checked against base_commit source (django/db/models/fields/`__init__`.py, the `if self.choices is not None:` block at 765-767) and patch.diff: leg 4 `(lookup key).isNone` ↔ `not hasattr(cls, 'get_%s_display' % self.name)` — faithful, since hasattr tests presence over the full MRO and does not inspect the bound value (atk_12 confirms the spec likewise ignores the bound kind). Leg 5 single-name update ↔ `setattr` of one attribute — frame-faithful; atk_5 confirms every other name is pinned. Leg 6 else-preserve ↔ the skipped setattr — atk_1/atk_2/atk_3 confirm this leg is the discriminating one.
 - Model↔patch correspondence holds in the direction that matters for this gate: the postcondition is FULL functional equality to an input-grounded helper, so it pins the post-state at every name with no unconstrained output component (directive 5) and no ungrounded oracle (directive 8). Domain restriction to the choices-branch is documented in mapping.md and is sound (no `gen` exists when the branch is skipped).
 - Discrepancy noted, out of lane, no effect on this verdict: the bundle's verdict.md Role 3 note asserts G-EQ/G-PANEL-1 previously failed because `loom.semantics.termination "partial"` permits vacuous satisfaction. The FROZEN Solution.lean audited here sets `"total"`, and atk_6/atk_10 empirically prove the termination obligation is generated and NOT dischargeable by a diverging impl. The prior recorded fails were INCONCLUSIVE-by-crash (0 attacks captured, harness exit -9), not a substantive spec defect.

**CONCLUSION.** 12 distinct wrong impls spanning prepatch bug, no-op, inverted guard, partial-domain (on key, on the F2P test's exact accessor name, and on the token), boundary (empty key, existing auto-kind binding), control-flow-effect/frame violation, divergence-vacuity (both unconditional and on the discriminating leg only), self-recursion, and constant-folded token — ALL rejected, each on the semantically discriminating goal. Positive control verifies. Prepatch bug reproduced. The only verifying same-spec impl is functionally equivalent to gold and its faithful patch RESOLVES under the official harness (F2P pass, 30/30 P2P pass, no P2F). No verify⇏correct witness found: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_13.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No unchanged dependency callee is CONSUMED by this specification. The
-- registration step is modeled structurally below as a single-name update on a
-- class namespace, so there is no `axiom`/stub callee to declare. The accessor
-- that would be generated is taken as an abstract token (`gen`): the step never
-- inspects its value, only whether the target name is already bound.
-- axioms-end

-- pure-start
/- A class namespace, viewed as the partial map from an accessor name to the
   identity of the attribute bound there: `some t` when the name is bound to an
   attribute of identity-kind `t`, `none` when the name is free. -/
abbrev Namespace := String → Option Nat

/- Install the generated accessor `gen` at name `key`, but only when that name is
   currently free. When the name is already bound, the namespace is returned
   unchanged, so whatever was bound there stays in force; every other name is
   left untouched in both cases. -/
def registerDisplay (lookup : Namespace) (key : String) (gen : Nat) : Namespace :=
  if (lookup key).isNone then
    (fun n => if n = key then some gen else lookup n)
  else
    lookup
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method registerAccessor (lookup : Namespace) (key : String) (gen : Nat)
  return (out : Namespace)
  ensures out = registerDisplay lookup key gen
  do
    -- impl-start
    let mut result := lookup
    if (lookup key).isNone then
      result := (fun n => if n = key then some gen else lookup n)
    return result
    -- impl-end

prove_correct registerAccessor by
  loom_solve <;> simp_all [registerDisplay]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity, docs/architecture.md §5) for django__django-11999 / velvet. VERDICT: SOUND. 12 distinct same-spec wrong impls encoded and machine-verified; every one REJECTED. The single verifying same-spec impl is functionally EQUIVALENT to gold, and its faithful refined patch was materialized and RESOLVED under the official harness. No verify-but-wrong witness exists => no verify⇏correct break found.

 Every attack was built by copying the frozen Solution.lean and editing ONLY the impl region; axioms/pure/pre/post bytes untouched.

### SAME-SPEC (all True, re-verified after all repairs):
  python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('.../velvet/Solution.lean').read(), open('atk_N.lean').read(), b.language))"
  -> atk_1..atk_13 = True, pos_control = True (ALL_SAME_SPEC=True).

**POSITIVE CONTROL.** pos_control.lean (byte copy of frozen Solution.lean).
  bash scripts/lean_verify.sh pos_control.lean  ->  EXIT=0 (verifies, no sorry). The spec is satisfiable by the gold impl, so the 12 rejections below are real discrimination, not a broken harness.

ATTACK RESULTS (all run as `bash scripts/lean_verify.sh atk_N.lean`; exit 1 = rejected. Batches of 4 launched concurrently as background jobs; schedule only, pass criteria unchanged).

atk_1  EXIT=1  PREPATCH BUG REPRODUCED — unconditional overwrite (`result := fun n => if n = key then some gen else lookup n`), i.e. the base_commit `setattr(cls,'get_%s_display'%self.name,partialmethod(...))` with no guard. Rejected on exactly the discriminating goal: `⊢ ¬lookup key = none → (fun n => if n = key then some gen else lookup n) = lookup`. This is the user-override-displaced defect the F2P test observes. atk_2  EXIT=1  no-op (never installs). Goal `lookup key = none → lookup = fun n => ...`. atk_3  EXIT=1  inverted guard (`.isSome`).

BOTH legs unsolved. atk_4  EXIT=1  PARTIAL-DOMAIN / test-name special case — set-if-absent only when `key = "get_foo_bar_display"` (the exact accessor the FAIL_TO_PASS test `test_overriding_FIELD_display` touches), buggy overwrite for every other field name. Rejected with `if_neg : ¬key = "get_foo_bar_display"` in context. IMPORTANT: this is the classic F2P-overfit impl that would PASS the Django test suite yet be wrong in general; the spec's universally-quantified functional equality kills it. Strong evidence the spec is not test-shaped. atk_5  EXIT=1  CONTROL-FLOW-EFFECT / frame violation — right answer at `key`, but also unbinds the neighbour `key ++ "_x"` (models an extra delattr on the class namespace).

Both legs unsolved => the frame is genuinely pinned at every name, not just at `key`. atk_6  EXIT=1  DIVERGENCE / VACUITY probe — `while i > 0 ... i := i` with `decreasing i`, then a wrong (no-install) result. Rejected on `case «decreasing_1: i» ... ⊢ False`. Confirms `loom.semantics.termination "total"` really discharges a termination obligation; a diverging impl cannot vacuously satisfy the functional-equality postcondition here. (First-draft typing error `OfNat (Option ℕ) 0` was repaired with explicit `: Namespace` / `: Nat` annotations so the file elaborates and fails SEMANTICALLY, not on elaboration.) atk_7  EXIT=1  guarded self-call divergence — the else leg recurses `registerAccessor lookup key gen` on identical arguments.

Rejected: `fail to show termination for registerAccessor ... no parameters suitable for structural recursion`. atk_9  EXIT=1  hardcoded token — installs `some 1` (the auto kind fixed by mapping.md) instead of the parameter `gen`. Goal `(fun n => if n = key then some 1 else lookup n) = fun n => if n = key then some gen else lookup n`. The token is not allowed to be constant-folded. atk_10 EXIT=1  SHARPEST VACUITY ATTACK — exactly correct on the free-name leg, but on the DISCRIMINATING leg (`¬lookup key = none`, i.e. a user accessor already present) it diverges and then returns the prepatch overwrite. Under partial-correctness semantics this would verify vacuously while being wrong precisely where the F2P test looks.

Rejected on `case «decreasing_1: i» ... if_neg : ¬lookup key = none ... ⊢ False`. This closes the divergence-vacuity hole noted in the bundle's own verdict.md (which claimed "partial" semantics; the FROZEN Solution.lean sets termination "total", and the obligation is in fact generated and unprovable). atk_11 EXIT=1  partial domain on the token — set-if-absent only when `gen = 1`, overwrite otherwise. `if_neg : ¬gen = 1` in context. atk_12 EXIT=1  BOUNDARY — treats a name bound to the auto kind (`some 1`) as free, so an existing auto-generated accessor is re-installed while a user one is kept.

Rejected: the spec keys on presence only, never on the bound value's kind — matching real `hasattr`, which does not inspect what is bound. atk_13 EXIT=1  BOUNDARY — single-point hole at the empty key `""`. Rejected with `if_pos : key = ""`; not even a measure-zero domain hole survives.

MANDATORY RESOLVE RUN (protocol step 2). Exactly one same-spec attack VERIFIES: atk_8  EXIT=0  ungrounded-oracle-echo probe — impl is `let result := registerDisplay lookup key gen; return result`, i.e. it returns the pure spec helper verbatim.

Because I must materialize and RUN the faithful patch for EVERY verifying impl: patch: atk_8_faithful.patch (hasattr-guarded setattr, refactored via a `display_attr` local — the faithful refinement of "install only when the name is free"). pre-check: `git apply --check -v` at base_commit 84633905273fc916e3d17883810d9969c03f73c2 -> APPLY_CHECK=OK. command: python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-11999', open('atk_8_faithful.patch').read(), run_id='sbu-audit-eq-11999-atk8'); print(r)" OBSERVED: resolved=True, completed=True, attempts=1, flaky=False, note='resolved'.

FAIL_TO_PASS success=['test_overriding_FIELD_display (model_fields.tests.GetFieldDisplayTests)'], failure=[]; PASS_TO_PASS 30/30 success, failure=[]; PASS_TO_FAIL=[] , FAIL_TO_FAIL=[]. => The verifying impl's faithful patch DOES resolve. This is NOT a break: atk_8 is functionally identical to `registerDisplay` (it IS the set-if-absent function), so it is a correct impl, not a wrong one — the spec's postcondition `out = registerDisplay lookup key gen` is total functional equality, so any verifying impl is pointwise equal to gold and therefore refines to a resolving patch. atk_8 is reported for protocol completeness and is EXCLUDED from the `attacks` list (it is not a wrong impl).

Note the echo does not indicate an ungrounded oracle: `registerDisplay` is an input-grounded pure helper (a computation over `lookup`/`key`/`gen`), not an oracle naming the answer — spelling it out is just an inlining of the same computation. (A true `:|` demonic-choice oracle echo, `let result :| result = registerDisplay lookup key gen`, does NOT even elaborate: `failed to synthesize Findable ...`. Recorded as an elaboration failure, not counted among the 12.)

### REFINEMENT.MD LEG AUDIT (my assigned focus: A-legs + model↔patch correspondence).
 - Tag inventory: 6 legs, tags {R,R,R,I,I,I} — legs 1-3 R (carrier bijections), legs 4-6 I (identical concrete ops). ZERO kind-3 (untagged/unjustified) legs. Complies with the R / A-consumed / A-reference / I requirement.
 - **A-LEGS:** there are NONE, and that is CORRECT, not an evasion. Mechanically confirmed the frozen Solution.lean contains 0 `axiom` declarations and 0 `:|` stub callees; the axioms region is a prose note explaining why. The changed op is modeled DEEPLY (a presence test on `lookup` plus a single-name functional update), so per SPEC_GUIDE §3 it must not be axiomatized — an axiom here would be the defect. Consequently there is no A-consumed `ensures` the proof could lean on, and no A-reference deep model whose correspondence to a real callee could drift: the proof obligation is discharged against the structural definition alone. G-AX correctly skips. This removes the entire attack surface my lane is aimed at — there is no axiom to over-strengthen and no deep model to mis-mirror.
 - The one entity that COULD have been an A-reference — the auto accessor `partialmethod(cls._get_FIELD_display, field=self)` — is correctly demoted to the opaque token `gen`, because the registration step never observes its value, only its presence at `key`. atk_9 (hardcoded `some 1`) confirms the token is a genuine parameter and not silently pinned; the spec is agnostic to the accessor's internals, which is exactly the real code's behavior.
 - Correspondence of the I-legs to the real gold patch, checked against base_commit source (django/db/models/fields/`__init__`.py, the `if self.choices is not None:` block at 765-767) and patch.diff: leg 4 `(lookup key).isNone` ↔ `not hasattr(cls, 'get_%s_display' % self.name)` — faithful, since hasattr tests presence over the full MRO and does not inspect the bound value (atk_12 confirms the spec likewise ignores the bound kind). Leg 5 single-name update ↔ `setattr` of one attribute — frame-faithful; atk_5 confirms every other name is pinned. Leg 6 else-preserve ↔ the skipped setattr — atk_1/atk_2/atk_3 confirm this leg is the discriminating one.
 - Model↔patch correspondence holds in the direction that matters for this gate: the postcondition is FULL functional equality to an input-grounded helper, so it pins the post-state at every name with no unconstrained output component (directive 5) and no ungrounded oracle (directive 8). Domain restriction to the choices-branch is documented in mapping.md and is sound (no `gen` exists when the branch is skipped).
 - Discrepancy noted, out of lane, no effect on this verdict: the bundle's verdict.md Role 3 note asserts G-EQ/G-PANEL-1 previously failed because `loom.semantics.termination "partial"` permits vacuous satisfaction. The FROZEN Solution.lean audited here sets `"total"`, and atk_6/atk_10 empirically prove the termination obligation is generated and NOT dischargeable by a diverging impl. The prior recorded fails were INCONCLUSIVE-by-crash (0 attacks captured, harness exit -9), not a substantive spec defect.

**CONCLUSION.** 12 distinct wrong impls spanning prepatch bug, no-op, inverted guard, partial-domain (on key, on the F2P test's exact accessor name, and on the token), boundary (empty key, existing auto-kind binding), control-flow-effect/frame violation, divergence-vacuity (both unconditional and on the discriminating leg only), self-recursion, and constant-folded token — ALL rejected, each on the semantically discriminating goal. Positive control verifies. Prepatch bug reproduced. The only verifying same-spec impl is functionally equivalent to gold and its faithful patch RESOLVES under the official harness (F2P pass, 30/30 P2P pass, no P2F). No verify⇏correct witness found: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 (faithfulness / spec-too-strong-or-drift) for django__django-11999 velvet. VERDICT: FAITHFUL — no input found on which the modeled function disagrees with the real repo callee.

**SPEC REGION IDENTITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True. velvet spec_view confirms the twins differ ONLY in the elided impl/proof regions; recomputed region_hashes match meta.json for axioms/pure/impl (spec_view hash differs from the stale meta.region_hashes entry but matches the G-HYGIENE record 0404c112..., i.e. the current file).

ORACLE SETUP (this is the part prior audits get wrong): the worktree at base_commit 8463390 carries the PREPATCH code (unconditional `setattr(cls, 'get_%s_display' % self.name, partialmethod(...))`, fields/`__init__`.py:765-767). The faithfulness oracle is base_commit + patch.diff, whose guard is `if not hasattr(cls, 'get_%s_display' % self.name):`. I created a fresh detached worktree, applied patch.diff, and confirmed the patched region byte-for-byte before testing. Confirmed the discriminator on the problem-statement model (FooBar with its own get_foo_bar_display): unpatched -> key holds the AUTO partialmethod and the instance call returns 'foo'; patched -> key holds the USER callable and returns 'something'. F2P GetFieldDisplayTests: 4 tests OK on the patched tree.

DIFFERENTIAL METHOD (real metaclass, guard-time pre-state): rather than proxy the pre-state with a second class build, I instrumented the REAL guard by monkeypatching `hasattr` inside django.db.models.fields, recording at the exact moment the choices-branch runs (a) whether the name was already bound and (b) the identity-kind of what was bound. I then compared registerDisplay(pre, key, gen=1) against the real post-state kind at key, read via MRO/metaclass `__dict__` walk (NOT getattr — getattr triggers partialmethod.`__get__` and silently misreports kind; my first probe pass showed two false 'divergences' from exactly that instrumentation bug, and both vanished once the read was fixed).

Exotic namespace shapes tried, all AGREE: key free; own class-body method; inherited from abstract parent; method from a NON-model mixin base; classmethod; staticmethod; plain int; bound to None; property; property raising AttributeError; a data descriptor whose `__get__` raises AttributeError; attribute supplied by a custom METACLASS (hasattr sees type(cls) too); a real IntegerField declared AT the accessor name, in both declaration orders relative to the choices field; child of an abstract parent that itself carries a choices field (so key is already bound to an AUTO partialmethod, kind 1 -> preserved, matching the else leg); choices=[] (empty list is not None, branch still runs). Scaled run: 4000 randomized (config x field-name) cases through the real ModelBase — compared=4000, no-guard=0, exceptions=0, DIVERGENCES=0. The bundle's own conformance_check.py re-run in the patched worktree: G-CONF OK, 100004 inputs (seed=11999), 0 disagreements.

SPEC-TOO-STRONG (E-shape) LEAN PROBES — is a faithful correct impl REJECTED? Four fresh reshapes, spec region untouched: (E1) isSome-guard + `Function.update lookup key (some gen)`; (E2) unconditional pointwise write of `(lookup key).getD gen`; (E3) `match lookup key with | none => .. | some v => rebuild pointwise with some v` (bound branch rebuilt as a lambda rather than returning `lookup` itself, which stresses the funext/eta leg). Each FAILED under the frozen tactic script but VERIFIED (exit 0) after retuning the proof only (funext n + rcases on the Option). The residual goals in the failing runs were mathematically TRUE, so these are tactic-tuning artifacts, not spec holes: the ensures admits every faithful reshape. Controls: gold Solution.lean verifies (exit 0); Solution_prepatch.lean fails on exactly the discriminating goal `¬lookup key = none → (fun n => if n = key then some gen else lookup n) = lookup`, i.e. the spec genuinely pins the bound-name branch the fix introduced.

DOMAIN RESTRICTION IS SOUND, NOT A NARROWED PRECONDITION: the method has no `require` and ranges over ALL (lookup, key, gen). The choices-is-None case is excluded because no registration step and no `gen` exist there — the modeled operation does not occur, so this is not the dishonest 'narrow the precondition until the witness is inadmissible' repair. Frame is faithful: install touches only key (all other names via `lookup n`), the else leg returns `lookup` whole, matching the real single-attribute setattr / skip.

RESIDUAL OBSERVATION (not a defect, recorded for honesty): the real guard is `hasattr`, which INVOKES the descriptor protocol, so a pathological attribute at key whose `__get__` has side effects can perturb OTHER names — I demonstrated this in the real patched tree (a descriptor at key that writes cls.other_name during the guard, then raises AttributeError, so the auto accessor installs anyway). The spec's frame claims other names are untouched. This is NOT a faithfulness counterexample under this lane's standard: the carrier is String → Option Nat, recording only name→identity-kind, so no carrier VALUE distinguishes 'a side-effecting `__get__` at key' from an ordinary binding — there is no diverging INPUT to cite, and the pathology needs a hand-built descriptor no Django model produces. A raising descriptor also makes hasattr False, which the model tracks correctly (verified: pre=None -> installs AUTO, matching real).

Those are the spec-too-WEAK lane and/or need a re-run; neither is evidence that the abstraction disagrees with the real callee.

**CONCLUSION:** registerDisplay (set-if-absent single-name namespace update) is an exact abstraction of the gold-patched choices-branch registration step in Field.contribute_to_class over every input expressible in the documented carrier. No diverging input exists to cite, so FAITHFUL is not a defect here.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 (leakage / gold-reconstruction) for django__django-11999 (velvet).

SPEC-REGION IDENTITY (verified, not taken on trust). Recomputed with swebench_unified.markers under VelvetBackend.language: same_spec(Solution.lean, Solution_prepatch.lean) == True. Stronger: the full spec_view strings are byte-identical (spec_view(gold) == spec_view(prepatch)), so the ONLY difference between the two artifacts lies in the elided impl region. Recomputed region_hashes(gold)['spec_view'] = 0404c1127067aa16a0429a0028116473176d35303283db782a8425134526fa60, which matches the recorded G-HYGIENE hash exactly. Confirmed the prepatch impl-region narration is fully elided and cannot reach the consumer: 'Pre-image', 'unconditionally', 'displacing', 'MUST', 'frozen spec' all absent from spec_view(prepatch). Gold Solution.lean re-verified independently: scripts/lean_verify.sh exit 0.

MECHANICAL SCREEN, RE-RUN (not read from meta.json). leakage.screen(Solution.lean, velvet, patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Same on Solution_prepatch.lean. Per-rule: no Lean diff markers; no gold-patch changed line reproduced at >=8 normalized chars; no patched file path 'django/db/models/fields/`__init__`.py' and no dotted module path; the single distinctive patched def/class symbol is 'contribute_to_class' and no spec-view identifier embeds it and no spec-view comment names it; no narration token.

SCREEN IS NOT VACUOUS (4/4 positive controls fire). I injected each leak class into Solution.lean and confirmed the screen catches it: C1 gold line "if not hasattr(cls, 'get_%s_display' % self.name):" in a pure-region comment -> L1; C2 patched file path -> L2; C3 renaming registerDisplay to contribute_to_class_reg -> L2/L5; C4 '-- this fixes the regression' -> L3. So the pass above is a live pass, not an unarmed one.

BEYOND THE MECHANICAL SCREEN (the part that actually decides this lane). (a) Gold-mechanism token sweep: hasattr, setattr, partialmethod, `_get_FIELD_display`, 'get_%s_display', contribute_to_class, `__dict__`, cls, MRO, ModelBase, `__new__`, attname, descriptor_class are ALL absent from the spec view. (b) Longest-common-substring probe rather than exact match: the deepest normalized overlap between ANY gold changed line and the spec view is 8 chars, and enumerating the >=6-char overlaps shows they are all incidental English/Lean fragments ('partial' from set_option loom.semantics.termination, 'method' from the `method` keyword, 'isplay' from registerDisplay) -- no fragment of the gold edit is recoverable.

(c) Hidden-test identity: none of the test_patch symbols (FooBar, get_foo_bar_display, test_overriding_FIELD_display, test_get_FIELD_display_translated) is echoed word-bounded in the spec view. (d) HINTS DISCIPLINE, judged explicitly per this lane's rule (leakage is judged against problem_statement ONLY, never hints_text): the hints here are unusually informative -- they name the regressing commit a68ea231, the ModelBase.`__new__` attr-ordering dependency, and the Python 3.6 dict-ordering discussion. I swept every hints-only term (>=4 chars, absent from problem_statement) against the spec view; the only word-bounded echoes are generic English/Lean vocabulary (There, both, bound, dependency, from, import, never, proof). Nothing hints-specific -- no commit sha, no 'ModelBase', no '`__new__`', no ordering narrative -- appears. The spec view is clean even against the stricter hints-excluded baseline.

SEMANTIC / RECONSTRUCTION JUDGMENT. The spec's content is: registerDisplay = set-if-absent single-name update on Namespace = String -> Option Nat (install `gen` at `key` only when `key` is free; otherwise return `lookup` unchanged), with ensures out = registerDisplay lookup key gen. The question is whether that discloses the gold edit beyond the public issue. It does not.

The problem_statement already states the required behavior in the imperative: 'I cannot override the get_FIELD_display function on models since version 2.2', with a worked FooBar example whose own get_foo_bar_display is being displaced, and the explicit requirement 'What I expect is that I should be able to override this function.' 'A user-supplied accessor at that name must survive rather than be displaced' IS the public requirement; the spec is its formalization in the abstract carrier, which is precisely what a mode-1/2 spec view is FOR.

The spec deliberately stops short of the gold mechanism: it does not reveal that the guard is `hasattr` (vs `key in cls.__dict__`, vs `not getattr(cls, key, None)`, vs reordering ModelBase.`__new__` so class-body attrs win) -- and notably the abstraction is mechanism-agnostic enough that upstream Django later switched this very guard to `not in cls.__dict__` without changing the modeled semantics. It does not reveal the file, the class, the method, the branch, or the shape of the edit (guard-wrap vs restructure). A solver handed only this spec view still has to locate the choices-branch registration step in Field.contribute_to_class and choose a guard; the spec tells it WHAT must hold, not WHERE or HOW.

On the two arguably-informative structural facts: (i) the modeled-function localization 'registerAccessor (<-> django.db.models.fields.Field.contribute_to_class (choices-branch registration step))' does travel to the solver via meta.json in the spec block -- but that is the BY-DESIGN edit-localization aid granted identically to mode 0 (eval/prompts.py `_localization_block` is documented as 'the SAME information the spec modes get'), i.e. a deliberate part of the information environment, not a spec-view disclosure, and it is not in the spec_view text this lane screens; (ii) the bundle exposing one modeled function does not imply single-site, and the common-rules prompt explicitly warns the core change 'is usually NOT the only edit'.

Neither is leakage. mapping.md / refinement.md / meta.json notes -- which DO contain the gold mechanism verbatim (hasattr, setattr, partialmethod, the MRO ordering argument, the post-patch Python block) -- are audit artifacts and are never placed in any agent-visible view (dataset.as_dict emits only problem_statement/hints/localization/spec_view/modeled_functions; patch, test_patch, FAIL_TO_PASS, PASS_TO_PASS are in WITHHELD_FIELDS). No relaxation flag is involved: the only set_options are loom.semantics.termination "total" and choice "demonic".

**VERDICT:** NO-LEAKAGE. No spec-view line leaks the gold edit beyond the public problem_statement.

OUT-OF-LANE, RECORDED FOR HONESTY (does not affect this verdict): meta.json carries G-EQ = fail and G-PANEL-1 = fail, both with machine verdict 'INCONCLUSIVE -- only 0 attacks (need >= 5); prepatch bug not reproduced; no positive control', and verdict.md shows both roles died with exit -9 (host OOM/kill) rather than reaching a substantive finding. Per the retained-label rule I do NOT re-read those as spec-too-weak findings; they are harness-kill INCONCLUSIVEs needing a re-run in their own lanes. They are orthogonal to leakage, which concerns disclosure and not spec strength.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.