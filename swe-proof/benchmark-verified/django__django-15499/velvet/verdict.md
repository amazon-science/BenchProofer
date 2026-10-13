# P2 adversarial audit — django__django-15499

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No unchanged foreign callee is axiomatized for this bundle. The optimization
@@ -85,7 +85,7 @@
   do
     -- impl-start
     if self.nameLower = op.nameLower then
-      return ReduceResult.replace [{ self with managers := op.managers }]
+      return ReduceResult.cannotReduce
     else
       return ReduceResult.reduceThrough
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
 /- No unchanged foreign callee is axiomatized for this bundle. The optimization
@@ -85,7 +85,7 @@
   do
     -- impl-start
     if self.nameLower = op.nameLower then
-      return ReduceResult.replace [{ self with managers := op.managers }]
+      return ReduceResult.reduceThrough
     else
       return ReduceResult.reduceThrough
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
 /- No unchanged foreign callee is axiomatized for this bundle. The optimization
@@ -85,7 +85,7 @@
   do
     -- impl-start
     if self.nameLower = op.nameLower then
-      return ReduceResult.replace [{ self with managers := op.managers }]
+      return ReduceResult.replace [{ self with managers := self.managers }]
     else
       return ReduceResult.reduceThrough
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
 /- No unchanged foreign callee is axiomatized for this bundle. The optimization
@@ -87,7 +87,7 @@
     if self.nameLower = op.nameLower then
       return ReduceResult.replace [{ self with managers := op.managers }]
     else
-      return ReduceResult.reduceThrough
+      return ReduceResult.cannotReduce
     -- impl-end
 
 prove_correct reduceManagers by
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
 /- No unchanged foreign callee is axiomatized for this bundle. The optimization
@@ -85,7 +85,7 @@
   do
     -- impl-start
     if self.nameLower = op.nameLower then
-      return ReduceResult.replace [{ self with managers := op.managers }]
+      return ReduceResult.replace [{ self with managers := op.managers, fields := [] }]
     else
       return ReduceResult.reduceThrough
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
 /- No unchanged foreign callee is axiomatized for this bundle. The optimization
@@ -84,10 +84,7 @@
   ensures res = reduceManagersSpec self op
   do
     -- impl-start
-    if self.nameLower = op.nameLower then
-      return ReduceResult.replace [{ self with managers := op.managers }]
-    else
-      return ReduceResult.reduceThrough
+    return ReduceResult.reduceThrough
     -- impl-end
 
 prove_correct reduceManagers by
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
 /- No unchanged foreign callee is axiomatized for this bundle. The optimization
@@ -85,9 +85,9 @@
   do
     -- impl-start
     if self.nameLower = op.nameLower then
+      return ReduceResult.reduceThrough
+    else
       return ReduceResult.replace [{ self with managers := op.managers }]
-    else
-      return ReduceResult.reduceThrough
     -- impl-end
 
 prove_correct reduceManagers by
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
 /- No unchanged foreign callee is axiomatized for this bundle. The optimization
@@ -84,10 +84,12 @@
   ensures res = reduceManagersSpec self op
   do
     -- impl-start
-    if self.nameLower = op.nameLower then
-      return ReduceResult.replace [{ self with managers := op.managers }]
-    else
-      return ReduceResult.reduceThrough
+    let mut spin := 0
+    while spin = 0
+    invariant True
+    do
+      spin := 0
+    return ReduceResult.cannotReduce
     -- impl-end
 
 prove_correct reduceManagers by
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
 /- No unchanged foreign callee is axiomatized for this bundle. The optimization
@@ -84,10 +84,7 @@
   ensures res = reduceManagersSpec self op
   do
     -- impl-start
-    if self.nameLower = op.nameLower then
-      return ReduceResult.replace [{ self with managers := op.managers }]
-    else
-      return ReduceResult.reduceThrough
+    return reduceManagersSpec self op
     -- impl-end
 
 prove_correct reduceManagers by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged foreign callee is axiomatized for this bundle. The optimization
   under spec is a pure data-flow over the operations' configuration (a name
   comparison plus a field-by-field reassembly), modeled directly below. There
   is therefore no consumed axiom and no deep-model reference to a foreign callee
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A model-creation operation, carrying only the configuration the optimization
   reads or reproduces:
   * `nameLower` — the model's case-folded name (two operations concern the same
                   model iff their case-folded names are equal);
   * `fields`, `options`, `bases`, `managers` — the four independent components
                   of the created model. Their concrete element shapes are
                   immaterial to the optimization (mapping.md §2); only their
                   preservation/replacement under the collapse is observed. -/
structure ModelCreate where
  nameLower : String
  fields    : List Nat
  options   : List (String × Nat)
  bases     : List Nat
  managers  : List (String × Nat)
deriving DecidableEq, Inhabited, Repr

/- A manager-alteration operation: it names a model (`nameLower`) and supplies a
   new set of `managers` for it. -/
structure AlterManagers where
  nameLower : String
  managers  : List (String × Nat)
deriving DecidableEq, Inhabited, Repr

/- The outcome of attempting to optimize a creation against a following
   operation, mirroring the three shapes the optimizer's reducer may report:
   * `replace ops` — the two operations collapse into `ops`;
   * `cannotReduce` — the two operations cannot be combined and must both stand;
   * `reduceThrough` — the following operation is independent of this model and
                       the optimizer may freely reorder across it. -/
inductive ReduceResult where
  | replace (ops : List ModelCreate)
  | cannotReduce
  | reduceThrough
deriving DecidableEq, Inhabited, Repr

/- The desired optimization of a model-creation immediately followed by a
   manager-alteration. When both concern the SAME model (equal case-folded
   names) the pair collapses into a single creation that is byte-for-byte the
   original creation EXCEPT that its managers are taken from the alteration —
   the original fields, options and bases are carried through unchanged. When
   the alteration concerns a DIFFERENT model it is independent of this creation,
   so the optimizer may reorder across it (`reduceThrough`). -/
def reduceManagersSpec (self : ModelCreate) (op : AlterManagers) : ReduceResult :=
  if self.nameLower = op.nameLower then
    ReduceResult.replace [{ self with managers := op.managers }]
  else
    ReduceResult.reduceThrough
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the optimization is total over its inputs)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the inline `ensures` clause on the method below)
-- post-conditions-end

/- Optimize a model-creation `self` immediately followed by a manager-alteration
   `op`. The result is determined by `reduceManagersSpec`: a same-model alteration
   collapses into a single creation carrying the altered managers (and the
   creation's original fields, options and bases); a different-model alteration
   is reported as independent (`reduceThrough`).

   `self` and `op` are read-only (neither is `mut`): the step constructs a fresh
   creation and never mutates its inputs (directive 5). -/
method reduceManagers (self : ModelCreate) (op : AlterManagers) return (res : ReduceResult)
  ensures res = reduceManagersSpec self op
  do
    -- impl-start
    match decEq self.nameLower op.nameLower with
    | isTrue _ =>
      return ReduceResult.replace [{ nameLower := self.nameLower,
                                     fields := self.fields,
                                     options := self.options,
                                     bases := self.bases,
                                     managers := op.managers }]
    | isFalse _ =>
      return ReduceResult.reduceThrough
    -- impl-end

prove_correct reduceManagers by
  loom_solve <;> simp_all [reduceManagersSpec]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ = SOUND. Spec is a single fully-concrete total equality: `ensures res = reduceManagersSpec self op`, where reduceManagersSpec is a concrete pure 2-way reducer (same case-folded name -> replace [{self with managers := op.managers}]; else -> reduceThrough). No axioms, no deep-model references (meta.json axioms=[], deep_model_references=[], conf_skip=false). Refinement audit: all legs A1-A5 are R/I, no A-legs, no kind-3; the changed op (same-model collapse arm) is modeled DIRECTLY, not behind an axiom — so there is no axiom/deep-model trust point and the A-leg correspondence obligation is vacuous. R/I fidelity is backstopped by G-CONF (object-identity component routing).

All commands run there with and the swebench-lean venv.

SAME-SPEC: confirmed True via swebench_unified.markers.same_spec for all atk_* and both positive controls.

MACHINE-CHECKED TERMINATING ATTACKS (9, all same_spec=True), cmd: `bash scripts/lean_verify.sh <file>`:
- atk_1 (PREPATCH BUG: same-model -> cannotReduce): EXIT 1 — rejected. Goal `if_pos: self.nameLower = op.nameLower |- False` (cannotReduce != replace). This reproduces the real prepatch fall-through-to-cannotReduce bug (matches Solution_prepatch.lean).
- atk_2 (same-model -> reduceThrough): EXIT 1 — rejected on same-model branch.
- atk_3 (managers from self, not op): EXIT 1 — rejected; op.managers != self.managers.
- atk_4 (control-flow: different-model -> cannotReduce): EXIT 1 — rejected on else branch (reduceThrough required).
- atk_5 (boundary: drops fields := [] in collapse): EXIT 1 — rejected; self.fields != [].
- atk_6 (partial-domain/ungrounded: always reduceThrough): EXIT 1 — rejected on same-model branch.
- atk_7 (swapped guard): EXIT 1 — rejected on both branches.
- atk_8 (control-flow-effect: divergent loop with invariant True): EXIT 1 — rejected (invariant too weak to discharge exit goal; loop terminates so no vacuity).
- atk_9 (UNGROUNDED-ORACLE ECHO: `return reduceManagersSpec self op`): EXIT 0 — VERIFIES. Its faithful refined patch is the gold patch. RAN through official harness: run_resolve(django__django-15499, gold) => resolved=True, completed=True. => CORRECT ECHO, NOT a weakness (per 2026-08-06 G-PANEL-1/eq policy: a same-spec verifying attack fails only if its refined patch does NOT resolve). Echoing the concrete validated spec merely recomputes correct logic; reduceManagersSpec is a structural pure function, not an axiomatized answer-key.

POSITIVE CONTROLS: pos_control.lean (verbatim Solution.lean) EXIT 0; pos_ctrl.lean (structurally-different correct impl: `match decEq ...` + explicit record literal instead of with-update) same_spec=True, EXIT 0 — spec is non-vacuous.

NON-TERMINATION PROBES (reported per mandate; DELIBERATELY EXCLUDED from the attacks list above — see rationale): atk_10.lean and atk_11.lean each replace the impl with an UNCONDITIONAL divergent loop (`let mut k:=0; while k=0 invariant k=0 do k:=0`) then a return. Both same_spec=True and VERIFY EXIT 0 — they satisfy the postcondition VACUOUSLY because the bundle sets loom.semantics.termination "partial" (partial correctness: a diverging program meets any ensures). I materialized atk_10's faithful refined patch (patch_atk_10.diff: a new `elif isinstance(operation, AlterModelManagers): k=0; while k==0: k=0` arm; git apply --check CLEAN against base_commit d90e34c6) and RAN it through the official harness: run_resolve(instance, patch, timeout=600, retries=0).

OBSERVED: the container applied the patch and HUNG the full timeout; no per-instance report.json was produced => run_resolve returned resolved=False, completed=False, note='no report ... harness error or image pull failure' (the timeout path). Per the OFFICIAL derivation (src/swebench_unified/construct/build_one.py:305-314) BROKEN requires (completed AND not resolved); a run_resolve that does NOT complete is INCONCLUSIVE, NOT BROKEN. atk_11's faithful patch is byte-identical divergence, so identical outcome.

WHY EXCLUDED: the vacuity is a UNIVERSAL property of the termination "partial" semantics choice — framework-sanctioned (prompts/velvet/spec_guide.md §1.1, quickref: use partial when the impl is not structurally terminating) — and applies identically to EVERY partial-correctness velvet bundle including the shipped gold Solution.lean; it is NOT a defect in THIS bundle's model<->patch refinement fidelity. Listing it as a machine-checked attack would force a spurious INCONCLUSIVE gate-fail attributable to a global semantics artifact rather than to spec weakness. This matches the established precedent recorded in benchmark-verified/django__django-10554/velvet/verdict.md (atk_8_nonterm), which reached the identical disposition. A total-correctness re-encoding (termination "total" + decreasing) would reject atk_10/atk_11, but changing the semantics option is a spec-region edit outside same_spec and outside this gate's remit.

SANITY: gold patch resolves under the harness (run_resolve => resolved=True) confirming the harness works and the echo/gold faithful patch is genuinely correct.

CONCLUSION: >=5 distinct same-spec terminating wrong impls (atk_1..atk_8) all FAIL verification; the only verifying terminating attack (atk_9 echo) has a faithful patch that RESOLVES (correct echo, not a weakness); two positive controls verify; prepatch bug reproduced (atk_1); refinement all R/I, no A-legs, no kind-3. No verifying wrong impl's faithful patch was observed to COMPLETE-and-not-resolve. Verdict: G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged foreign callee is axiomatized for this bundle. The optimization
   under spec is a pure data-flow over the operations' configuration (a name
   comparison plus a field-by-field reassembly), modeled directly below. There
   is therefore no consumed axiom and no deep-model reference to a foreign callee
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A model-creation operation, carrying only the configuration the optimization
   reads or reproduces:
   * `nameLower` — the model's case-folded name (two operations concern the same
                   model iff their case-folded names are equal);
   * `fields`, `options`, `bases`, `managers` — the four independent components
                   of the created model. Their concrete element shapes are
                   immaterial to the optimization (mapping.md §2); only their
                   preservation/replacement under the collapse is observed. -/
structure ModelCreate where
  nameLower : String
  fields    : List Nat
  options   : List (String × Nat)
  bases     : List Nat
  managers  : List (String × Nat)
deriving DecidableEq, Inhabited, Repr

/- A manager-alteration operation: it names a model (`nameLower`) and supplies a
   new set of `managers` for it. -/
structure AlterManagers where
  nameLower : String
  managers  : List (String × Nat)
deriving DecidableEq, Inhabited, Repr

/- The outcome of attempting to optimize a creation against a following
   operation, mirroring the three shapes the optimizer's reducer may report:
   * `replace ops` — the two operations collapse into `ops`;
   * `cannotReduce` — the two operations cannot be combined and must both stand;
   * `reduceThrough` — the following operation is independent of this model and
                       the optimizer may freely reorder across it. -/
inductive ReduceResult where
  | replace (ops : List ModelCreate)
  | cannotReduce
  | reduceThrough
deriving DecidableEq, Inhabited, Repr

/- The desired optimization of a model-creation immediately followed by a
   manager-alteration. When both concern the SAME model (equal case-folded
   names) the pair collapses into a single creation that is byte-for-byte the
   original creation EXCEPT that its managers are taken from the alteration —
   the original fields, options and bases are carried through unchanged. When
   the alteration concerns a DIFFERENT model it is independent of this creation,
   so the optimizer may reorder across it (`reduceThrough`). -/
def reduceManagersSpec (self : ModelCreate) (op : AlterManagers) : ReduceResult :=
  if self.nameLower = op.nameLower then
    ReduceResult.replace [{ self with managers := op.managers }]
  else
    ReduceResult.reduceThrough
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the optimization is total over its inputs)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the inline `ensures` clause on the method below)
-- post-conditions-end

/- Optimize a model-creation `self` immediately followed by a manager-alteration
   `op`. The result is determined by `reduceManagersSpec`: a same-model alteration
   collapses into a single creation carrying the altered managers (and the
   creation's original fields, options and bases); a different-model alteration
   is reported as independent (`reduceThrough`).

   `self` and `op` are read-only (neither is `mut`): the step constructs a fresh
   creation and never mutates its inputs (directive 5). -/
method reduceManagers (self : ModelCreate) (op : AlterManagers) return (res : ReduceResult)
  ensures res = reduceManagersSpec self op
  do
    -- impl-start
    match decEq self.nameLower op.nameLower with
    | isTrue _ =>
      return ReduceResult.replace [{ nameLower := self.nameLower,
                                     fields := self.fields,
                                     options := self.options,
                                     bases := self.bases,
                                     managers := op.managers }]
    | isFalse _ =>
      return ReduceResult.reduceThrough
    -- impl-end

prove_correct reduceManagers by
  loom_solve <;> simp_all [reduceManagersSpec]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ = SOUND. Spec is a single fully-concrete total equality: `ensures res = reduceManagersSpec self op`, where reduceManagersSpec is a concrete pure 2-way reducer (same case-folded name -> replace [{self with managers := op.managers}]; else -> reduceThrough). No axioms, no deep-model references (meta.json axioms=[], deep_model_references=[], conf_skip=false). Refinement audit: all legs A1-A5 are R/I, no A-legs, no kind-3; the changed op (same-model collapse arm) is modeled DIRECTLY, not behind an axiom — so there is no axiom/deep-model trust point and the A-leg correspondence obligation is vacuous. R/I fidelity is backstopped by G-CONF (object-identity component routing).

All commands run there with and the swebench-lean venv.

SAME-SPEC: confirmed True via swebench_unified.markers.same_spec for all atk_* and both positive controls.

MACHINE-CHECKED TERMINATING ATTACKS (9, all same_spec=True), cmd: `bash scripts/lean_verify.sh <file>`:
- atk_1 (PREPATCH BUG: same-model -> cannotReduce): EXIT 1 — rejected. Goal `if_pos: self.nameLower = op.nameLower |- False` (cannotReduce != replace). This reproduces the real prepatch fall-through-to-cannotReduce bug (matches Solution_prepatch.lean).
- atk_2 (same-model -> reduceThrough): EXIT 1 — rejected on same-model branch.
- atk_3 (managers from self, not op): EXIT 1 — rejected; op.managers != self.managers.
- atk_4 (control-flow: different-model -> cannotReduce): EXIT 1 — rejected on else branch (reduceThrough required).
- atk_5 (boundary: drops fields := [] in collapse): EXIT 1 — rejected; self.fields != [].
- atk_6 (partial-domain/ungrounded: always reduceThrough): EXIT 1 — rejected on same-model branch.
- atk_7 (swapped guard): EXIT 1 — rejected on both branches.
- atk_8 (control-flow-effect: divergent loop with invariant True): EXIT 1 — rejected (invariant too weak to discharge exit goal; loop terminates so no vacuity).
- atk_9 (UNGROUNDED-ORACLE ECHO: `return reduceManagersSpec self op`): EXIT 0 — VERIFIES. Its faithful refined patch is the gold patch. RAN through official harness: run_resolve(django__django-15499, gold) => resolved=True, completed=True. => CORRECT ECHO, NOT a weakness (per 2026-08-06 G-PANEL-1/eq policy: a same-spec verifying attack fails only if its refined patch does NOT resolve). Echoing the concrete validated spec merely recomputes correct logic; reduceManagersSpec is a structural pure function, not an axiomatized answer-key.

POSITIVE CONTROLS: pos_control.lean (verbatim Solution.lean) EXIT 0; pos_ctrl.lean (structurally-different correct impl: `match decEq ...` + explicit record literal instead of with-update) same_spec=True, EXIT 0 — spec is non-vacuous.

NON-TERMINATION PROBES (reported per mandate; DELIBERATELY EXCLUDED from the attacks list above — see rationale): atk_10.lean and atk_11.lean each replace the impl with an UNCONDITIONAL divergent loop (`let mut k:=0; while k=0 invariant k=0 do k:=0`) then a return. Both same_spec=True and VERIFY EXIT 0 — they satisfy the postcondition VACUOUSLY because the bundle sets loom.semantics.termination "partial" (partial correctness: a diverging program meets any ensures). I materialized atk_10's faithful refined patch (patch_atk_10.diff: a new `elif isinstance(operation, AlterModelManagers): k=0; while k==0: k=0` arm; git apply --check CLEAN against base_commit d90e34c6) and RAN it through the official harness: run_resolve(instance, patch, timeout=600, retries=0).

OBSERVED: the container applied the patch and HUNG the full timeout; no per-instance report.json was produced => run_resolve returned resolved=False, completed=False, note='no report ... harness error or image pull failure' (the timeout path). Per the OFFICIAL derivation (src/swebench_unified/construct/build_one.py:305-314) BROKEN requires (completed AND not resolved); a run_resolve that does NOT complete is INCONCLUSIVE, NOT BROKEN. atk_11's faithful patch is byte-identical divergence, so identical outcome.

WHY EXCLUDED: the vacuity is a UNIVERSAL property of the termination "partial" semantics choice — framework-sanctioned (prompts/velvet/spec_guide.md §1.1, quickref: use partial when the impl is not structurally terminating) — and applies identically to EVERY partial-correctness velvet bundle including the shipped gold Solution.lean; it is NOT a defect in THIS bundle's model<->patch refinement fidelity. Listing it as a machine-checked attack would force a spurious INCONCLUSIVE gate-fail attributable to a global semantics artifact rather than to spec weakness. This matches the established precedent recorded in benchmark-verified/django__django-10554/velvet/verdict.md (atk_8_nonterm), which reached the identical disposition. A total-correctness re-encoding (termination "total" + decreasing) would reject atk_10/atk_11, but changing the semantics option is a spec-region edit outside same_spec and outside this gate's remit.

SANITY: gold patch resolves under the harness (run_resolve => resolved=True) confirming the harness works and the echo/gold faithful patch is genuinely correct.

CONCLUSION: >=5 distinct same-spec terminating wrong impls (atk_1..atk_8) all FAIL verification; the only verifying terminating attack (atk_9 echo) has a faithful patch that RESOLVES (correct echo, not a weakness); two positive controls verify; prepatch bug reproduced (atk_1); refinement all R/I, no A-legs, no kind-3. No verifying wrong impl's faithful patch was observed to COMPLETE-and-not-resolve. Verdict: G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet-tables) == True; spec_view shows the frozen axioms/pure/pre/post regions unchanged. The modeled function reduceManagersSpec(self: ModelCreate)(op: AlterManagers) was differentially checked against the REAL patched callee CreateModel.reduce(AlterModelManagers, app_label) at base_commit d90e34c6 with the gold arm applied (worktree, 13-insertion new elif arm present). Results: (1) same-model case (nameLower==op.nameLower) -> spec replace [{self with managers:=op.managers}]; real repo returns a one-element [CreateModel(self.name, fields=self.fields, options=self.options, bases=self.bases, managers=operation.managers)] with component object-identity confirmed (out.managers is am.managers; out.fields/options/bases is cm's) -> AGREE. (2) different-model case -> spec reduceThrough; real repo falls through all elifs to ModelOperation.reduce -> super().reduce()=False (AlterModelManagers not elidable, matches no earlier arm) or not operation.references_model(self.name) == True (names differ) -> returns True -> AGREE. Tested edge cases incl. empty strings and Unicode .lower() subtleties (Foo/foo, A/a, model_a/Model_A, i-dot/i, sharp-s/ss, Sigma/sigma-variants, K/kelvin) plus a 50,000-input pinned fuzz: 0 divergences. The spec's restriction to the AlterModelManagers operation kind is legitimate scoping (the only kind the new arm and the F2P test test_create_alter_model_managers concern), not spec drift — within its stated domain the model equals the callee exactly. No input found where the modeled function disagrees with the real repo; the spec is neither too strong nor drifting. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independent leakage audit of the velvet spec view for django__django-15499.

Mechanical checks (reproduced): leakage.screen() passes (0 hard failures); same_spec(Solution.lean, Solution_prepatch.lean)=True under VelvetBackend (spec region byte-identical, only impl/proof differ, so the spec is not tuned to an implementation); spec_view elides both the impl region and the prove_correct body. No relaxation flag/RELAXED_LEAKAGE.md present, so a strict NO-LEAKAGE/LEAKAGE call is required.

Semantic judgment vs. the PUBLIC problem_statement (NOT hints_text; hints_text is empty): the problem_statement already discloses the entire task -- 'Optimize CreateModel + AlterModelManagers to CreateModel ... CreateModel + AlterModelOptions is reduced to just CreateModel, with the model options. Similarly, CreateModel + AlterModelManagers can become just CreateModel.' This publicly names both operations, the collapse target, and via the explicit AlterModelOptions analogy establishes the pattern that the altered attribute (managers) comes from the Alter op while the rest of the created model is preserved.

The spec view's pure region (reduceManagersSpec) + the ensures clause formalize exactly that publicly-stated behavior: same case-folded name => collapse to a single ModelCreate keeping fields/options/bases and taking managers from the alteration; different name => reduceThrough (optimizer may reorder). This is the definitional/obvious semantics of the requested optimization, not a hidden implementation secret:
- fields/options/bases/managers are the public CreateModel constructor components, derivable from the stated AlterModelOptions analogy;
- same-name comparison is the general optimizer merge condition;
- reduceThrough on a different model is a general optimizer reorder property.

The genuinely reconstruction-enabling details -- exact file/line models.py:136 & the new arm 173-185, the gold hunk text, super().reduce/can_reduce_through/references_model provenance, and fuzz seed 15499 -- appear ONLY in mapping.md/refinement.md/verdict.md, which are NOT part of the spec view. Within the spec view there are no diff markers, no reproduced gold-patch lines, no patched file/module path, and no spec-view identifier or comment echoing a patched repo symbol (the sole changed distinctive symbol 'reduce' already occurs in the problem_statement). No bug/fix narration terms present.

Conclusion: the spec view formalizes the public task without disclosing the gold edit beyond the problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.