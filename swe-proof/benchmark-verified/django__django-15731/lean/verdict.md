# P2 adversarial audit — django__django-15731

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition problem_spec_delegateMetadata pins ALL SIX fields of `result` to `underlying` (name, qualname, module, doc, annotations, signature), and MethodMetadata has exactly those six fields with DecidableEq. Therefore any impl whose `correct_delegateMetadata` closes universally must produce `result` observationally equal to `underlying` on every field — a complete/tight spec where verify implies observational correctness. Both verifying same-spec attacks (atk_6 `md := underlying`; atk_7 incremental full copy) are exactly gold-equivalent; their faithful refined patch (the @wraps patch = gold patch) RESOLVES under the official harness. No verifying wrong impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,17 +78,10 @@
 -- impl-start
 def implementation_delegateMetadata
     (underlying rawDelegate : MethodMetadata) : MethodMetadata := Id.run do
-  -- Start from the bare forwarding wrapper's intrinsic metadata, then propagate
-  -- the underlying method's full introspectable metadata onto it so the produced
-  -- method is indistinguishable under inspection.
   let mut md := rawDelegate
   md := { md with
     name := underlying.name,
-    qualname := underlying.qualname,
-    module := underlying.module,
-    doc := underlying.doc,
-    annotations := underlying.annotations,
-    signature := underlying.signature }
+    doc := underlying.doc }
   return md
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,17 +78,13 @@
 -- impl-start
 def implementation_delegateMetadata
     (underlying rawDelegate : MethodMetadata) : MethodMetadata := Id.run do
-  -- Start from the bare forwarding wrapper's intrinsic metadata, then propagate
-  -- the underlying method's full introspectable metadata onto it so the produced
-  -- method is indistinguishable under inspection.
   let mut md := rawDelegate
   md := { md with
     name := underlying.name,
     qualname := underlying.qualname,
     module := underlying.module,
     doc := underlying.doc,
-    annotations := underlying.annotations,
-    signature := underlying.signature }
+    annotations := underlying.annotations }
   return md
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,13 +78,10 @@
 -- impl-start
 def implementation_delegateMetadata
     (underlying rawDelegate : MethodMetadata) : MethodMetadata := Id.run do
-  -- Start from the bare forwarding wrapper's intrinsic metadata, then propagate
-  -- the underlying method's full introspectable metadata onto it so the produced
-  -- method is indistinguishable under inspection.
   let mut md := rawDelegate
   md := { md with
     name := underlying.name,
-    qualname := underlying.qualname,
+    qualname := underlying.module,
     module := underlying.module,
     doc := underlying.doc,
     annotations := underlying.annotations,
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,17 +78,19 @@
 -- impl-start
 def implementation_delegateMetadata
     (underlying rawDelegate : MethodMetadata) : MethodMetadata := Id.run do
-  -- Start from the bare forwarding wrapper's intrinsic metadata, then propagate
-  -- the underlying method's full introspectable metadata onto it so the produced
-  -- method is indistinguishable under inspection.
   let mut md := rawDelegate
-  md := { md with
-    name := underlying.name,
-    qualname := underlying.qualname,
-    module := underlying.module,
-    doc := underlying.doc,
-    annotations := underlying.annotations,
-    signature := underlying.signature }
+  if underlying.signature = rawDelegate.signature then
+    md := { md with
+      name := underlying.name,
+      qualname := underlying.qualname,
+      module := underlying.module,
+      doc := underlying.doc,
+      annotations := underlying.annotations,
+      signature := underlying.signature }
+  else
+    md := { md with
+      name := underlying.name,
+      doc := underlying.doc }
   return md
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,9 +78,6 @@
 -- impl-start
 def implementation_delegateMetadata
     (underlying rawDelegate : MethodMetadata) : MethodMetadata := Id.run do
-  -- Start from the bare forwarding wrapper's intrinsic metadata, then propagate
-  -- the underlying method's full introspectable metadata onto it so the produced
-  -- method is indistinguishable under inspection.
   let mut md := rawDelegate
   md := { md with
     name := underlying.name,
@@ -89,6 +86,7 @@
     doc := underlying.doc,
     annotations := underlying.annotations,
     signature := underlying.signature }
+  md := { md with signature := rawDelegate.signature }
   return md
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -78,17 +78,8 @@
 -- impl-start
 def implementation_delegateMetadata
     (underlying rawDelegate : MethodMetadata) : MethodMetadata := Id.run do
-  -- Start from the bare forwarding wrapper's intrinsic metadata, then propagate
-  -- the underlying method's full introspectable metadata onto it so the produced
-  -- method is indistinguishable under inspection.
   let mut md := rawDelegate
-  md := { md with
-    name := underlying.name,
-    qualname := underlying.qualname,
-    module := underlying.module,
-    doc := underlying.doc,
-    annotations := underlying.annotations,
-    signature := underlying.signature }
+  md := underlying
   return md
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -78,17 +78,10 @@
 -- impl-start
 def implementation_delegateMetadata
     (underlying rawDelegate : MethodMetadata) : MethodMetadata := Id.run do
-  -- Start from the bare forwarding wrapper's intrinsic metadata, then propagate
-  -- the underlying method's full introspectable metadata onto it so the produced
-  -- method is indistinguishable under inspection.
   let mut md := rawDelegate
-  md := { md with
-    name := underlying.name,
-    qualname := underlying.qualname,
-    module := underlying.module,
-    doc := underlying.doc,
-    annotations := underlying.annotations,
-    signature := underlying.signature }
+  md := { md with name := underlying.name, doc := underlying.doc }
+  md := { md with qualname := underlying.qualname, module := underlying.module }
+  md := { md with annotations := underlying.annotations, signature := underlying.signature }
   return md
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a delegating method that forwards calls to an underlying method, while
remaining faithful to that underlying method under introspection.

A delegating method is created as a generic forwarding wrapper: intrinsically it
carries only catch-all, placeholder introspectable metadata — a generic call
signature that accepts arbitrary arguments, its own internal qualified name and
defining module, and no documentation or parameter annotations. Tooling that
inspects a method (to display its call signature, its documentation, its
identity) reads this metadata.

For the delegating method to be indistinguishable from the method it stands in
for, ALL of its observable introspection metadata must mirror the underlying
method's:

  * the reported name,
  * the reported qualified name,
  * the reported defining module,
  * the documentation,
  * the parameter annotations,
  * and — crucially — the call signature reported for it, which must be the
    underlying method's real parameter list rather than the generic catch-all of
    a bare forwarding wrapper.

The desired behavior is that every one of these introspectable attributes of the
delegating method equals the corresponding attribute of the underlying method;
none is left at the generic placeholder value a bare wrapper would carry.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The underlying
-- method's introspectable metadata and the bare wrapper's placeholder metadata
-- enter as plain data; the only operation is the field-by-field selection of
-- which metadata the produced method exposes, modeled directly over the metadata
-- carrier. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The introspectable metadata of a method, restricted to the observable
attributes that method-inspection tooling reads. Each is modeled as a `String`
(only equality is observed):
* `name` — the reported method name;
* `qualname` — the reported qualified name;
* `module` — the reported defining module;
* `doc` — the documentation (empty string when absent);
* `annotations` — the parameter annotations, serialized (empty when absent);
* `signature` — the rendered call signature (parameter list) inspection reports.
-/
structure MethodMetadata where
  name : String
  qualname : String
  module : String
  doc : String
  annotations : String
  signature : String
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The produced delegating method's metadata is fully pinned to the underlying
method's: every observable introspection attribute equals the underlying
method's corresponding attribute. In particular the reported call signature is
the underlying method's real parameter list — never the generic catch-all of the
bare wrapper. No metadata field is left free or at a placeholder value. -/
def problem_spec_delegateMetadata
    (underlying rawDelegate : MethodMetadata) (result : MethodMetadata) : Prop :=
  result.name = underlying.name ∧
  result.qualname = underlying.qualname ∧
  result.module = underlying.module ∧
  result.doc = underlying.doc ∧
  result.annotations = underlying.annotations ∧
  result.signature = underlying.signature
-- post-conditions-end

-- impl-start
def implementation_delegateMetadata
    (underlying rawDelegate : MethodMetadata) : MethodMetadata := Id.run do
  -- Start from the bare forwarding wrapper's intrinsic metadata, then propagate
  -- the underlying method's full introspectable metadata onto it so the produced
  -- method is indistinguishable under inspection.
  let mut md := rawDelegate
  md := { md with
    name := underlying.name,
    qualname := underlying.qualname,
    module := underlying.module,
    doc := underlying.doc,
    annotations := underlying.annotations,
    signature := underlying.signature }
  return md
-- impl-end

-- proof-start
theorem correct_delegateMetadata :
    ∀ (underlying rawDelegate : MethodMetadata),
      problem_spec_delegateMetadata underlying rawDelegate
        (implementation_delegateMetadata underlying rawDelegate) := by
  intro underlying rawDelegate
  unfold problem_spec_delegateMetadata implementation_delegateMetadata
  simp only [Id.run]
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

same_spec=True confirmed for all 7 attacks + pos_control against Solution.lean.

SPEC SHAPE: `problem_spec_delegateMetadata underlying rawDelegate result := result.name=underlying.name ∧ ... ∧ result.signature=underlying.signature` — one conjunct per MethodMetadata field, all six pinned to `underlying`. This is a COMPLETE spec: the output is fully determined up to the six observable fields, and DecidableEq means field equality is exact. Consequently a universally-quantified `correct_` proof forces result ≡ underlying observationally; verify ⟹ correct is structural, not incidental. refinement.md legs audited: all R/I, no A-consumed / no A-reference, axioms=[] deep_model_references=[] (G-AX skip) — consistent with the model (functools.wraps EFFECT modeled deeply as field-copy, validated by G-CONF's real @wraps+inspect.signature oracle). No A-leg correspondence to forge.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`):
- atk_1 PREPATCH BUG (only name+doc propagated): exit=1 (fails to verify) — reproduces prepatch; four conjuncts no longer rfl. prepatch_reproduced=true.
- atk_2 boundary (omit signature field, the F2P discriminator): exit=1.
- atk_3 field-swap (qualname := underlying.module): exit=1.
- atk_4 partial-domain guard (full copy only when signature already catch-all, else name/doc only): exit=1 (else branch breaks the pins).
- atk_5 control-flow-effect (copy all six, then overwrite signature back to rawDelegate's catch-all): exit=1.
- atk_6 ungrounded-oracle echo (md := underlying): exit=0, `#print axioms correct_delegateMetadata` => 'does not depend on any axioms' (CLEAN).
- atk_7 control-flow echo (incremental full field copy across 3 assignments): exit=0, clean axioms.
- pos_control (gold impl verbatim): exit=0, clean axioms.

RESOLVE (protocol step 2): atk_6 and atk_7 are the ONLY verifying wrong-impls, and both are observationally identical to the gold (result ≡ underlying on all six fields). Their faithful refined patch is the all-attributes-mirroring @wraps(method) patch (byte-equal to the gold patch). Materialized as patch_wraps.diff and run through the official harness: `run_resolve('django__django-15731', patch, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, note='resolved' (docker via `docker`, image built/pulled successfully, F2P test_manager_method_signature passes). So the faithful patches of BOTH verifying attacks RESOLVE ⟹ no verify⇏correct witness.

Parallelism: attacks verified in two background batches of 4 (atk_1-4, then atk_5/6/7/pos_control), axiom-print checks in a third parallel batch of 3. All completed; no timeouts.

VERDICT: SOUND — ≥5 distinct attacks run (7 total: prepatch, boundary, swap, partial-domain, control-flow-effect, 2 echoes); every attack with a closing clean-axiom proof (atk_6, atk_7) has a materialized faithful patch that RESOLVES. Spec is complete and faithful; no gap between verify and correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition problem_spec_delegateMetadata pins ALL SIX fields of `result` to `underlying` (name, qualname, module, doc, annotations, signature), and MethodMetadata has exactly those six fields with DecidableEq. Therefore any impl whose `correct_delegateMetadata` closes universally must produce `result` observationally equal to `underlying` on every field — a complete/tight spec where verify implies observational correctness. Both verifying same-spec attacks (atk_6 `md := underlying`; atk_7 incremental full copy) are exactly gold-equivalent; their faithful refined patch (the @wraps patch = gold patch) RESOLVES under the official harness. No verifying wrong impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a delegating method that forwards calls to an underlying method, while
remaining faithful to that underlying method under introspection.

A delegating method is created as a generic forwarding wrapper: intrinsically it
carries only catch-all, placeholder introspectable metadata — a generic call
signature that accepts arbitrary arguments, its own internal qualified name and
defining module, and no documentation or parameter annotations. Tooling that
inspects a method (to display its call signature, its documentation, its
identity) reads this metadata.

For the delegating method to be indistinguishable from the method it stands in
for, ALL of its observable introspection metadata must mirror the underlying
method's:

  * the reported name,
  * the reported qualified name,
  * the reported defining module,
  * the documentation,
  * the parameter annotations,
  * and — crucially — the call signature reported for it, which must be the
    underlying method's real parameter list rather than the generic catch-all of
    a bare forwarding wrapper.

The desired behavior is that every one of these introspectable attributes of the
delegating method equals the corresponding attribute of the underlying method;
none is left at the generic placeholder value a bare wrapper would carry.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The underlying
-- method's introspectable metadata and the bare wrapper's placeholder metadata
-- enter as plain data; the only operation is the field-by-field selection of
-- which metadata the produced method exposes, modeled directly over the metadata
-- carrier. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The introspectable metadata of a method, restricted to the observable
attributes that method-inspection tooling reads. Each is modeled as a `String`
(only equality is observed):
* `name` — the reported method name;
* `qualname` — the reported qualified name;
* `module` — the reported defining module;
* `doc` — the documentation (empty string when absent);
* `annotations` — the parameter annotations, serialized (empty when absent);
* `signature` — the rendered call signature (parameter list) inspection reports.
-/
structure MethodMetadata where
  name : String
  qualname : String
  module : String
  doc : String
  annotations : String
  signature : String
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The produced delegating method's metadata is fully pinned to the underlying
method's: every observable introspection attribute equals the underlying
method's corresponding attribute. In particular the reported call signature is
the underlying method's real parameter list — never the generic catch-all of the
bare wrapper. No metadata field is left free or at a placeholder value. -/
def problem_spec_delegateMetadata
    (underlying rawDelegate : MethodMetadata) (result : MethodMetadata) : Prop :=
  result.name = underlying.name ∧
  result.qualname = underlying.qualname ∧
  result.module = underlying.module ∧
  result.doc = underlying.doc ∧
  result.annotations = underlying.annotations ∧
  result.signature = underlying.signature
-- post-conditions-end

-- impl-start
def implementation_delegateMetadata
    (underlying rawDelegate : MethodMetadata) : MethodMetadata := Id.run do
  -- Start from the bare forwarding wrapper's intrinsic metadata, then propagate
  -- the underlying method's full introspectable metadata onto it so the produced
  -- method is indistinguishable under inspection.
  let mut md := rawDelegate
  md := { md with
    name := underlying.name,
    qualname := underlying.qualname,
    module := underlying.module,
    doc := underlying.doc,
    annotations := underlying.annotations,
    signature := underlying.signature }
  return md
-- impl-end

-- proof-start
theorem correct_delegateMetadata :
    ∀ (underlying rawDelegate : MethodMetadata),
      problem_spec_delegateMetadata underlying rawDelegate
        (implementation_delegateMetadata underlying rawDelegate) := by
  intro underlying rawDelegate
  unfold problem_spec_delegateMetadata implementation_delegateMetadata
  simp only [Id.run]
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

same_spec=True confirmed for all 7 attacks + pos_control against Solution.lean.

SPEC SHAPE: `problem_spec_delegateMetadata underlying rawDelegate result := result.name=underlying.name ∧ ... ∧ result.signature=underlying.signature` — one conjunct per MethodMetadata field, all six pinned to `underlying`. This is a COMPLETE spec: the output is fully determined up to the six observable fields, and DecidableEq means field equality is exact. Consequently a universally-quantified `correct_` proof forces result ≡ underlying observationally; verify ⟹ correct is structural, not incidental. refinement.md legs audited: all R/I, no A-consumed / no A-reference, axioms=[] deep_model_references=[] (G-AX skip) — consistent with the model (functools.wraps EFFECT modeled deeply as field-copy, validated by G-CONF's real @wraps+inspect.signature oracle). No A-leg correspondence to forge.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`):
- atk_1 PREPATCH BUG (only name+doc propagated): exit=1 (fails to verify) — reproduces prepatch; four conjuncts no longer rfl. prepatch_reproduced=true.
- atk_2 boundary (omit signature field, the F2P discriminator): exit=1.
- atk_3 field-swap (qualname := underlying.module): exit=1.
- atk_4 partial-domain guard (full copy only when signature already catch-all, else name/doc only): exit=1 (else branch breaks the pins).
- atk_5 control-flow-effect (copy all six, then overwrite signature back to rawDelegate's catch-all): exit=1.
- atk_6 ungrounded-oracle echo (md := underlying): exit=0, `#print axioms correct_delegateMetadata` => 'does not depend on any axioms' (CLEAN).
- atk_7 control-flow echo (incremental full field copy across 3 assignments): exit=0, clean axioms.
- pos_control (gold impl verbatim): exit=0, clean axioms.

RESOLVE (protocol step 2): atk_6 and atk_7 are the ONLY verifying wrong-impls, and both are observationally identical to the gold (result ≡ underlying on all six fields). Their faithful refined patch is the all-attributes-mirroring @wraps(method) patch (byte-equal to the gold patch). Materialized as patch_wraps.diff and run through the official harness: `run_resolve('django__django-15731', patch, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, note='resolved' (docker via `docker`, image built/pulled successfully, F2P test_manager_method_signature passes). So the faithful patches of BOTH verifying attacks RESOLVE ⟹ no verify⇏correct witness.

Parallelism: attacks verified in two background batches of 4 (atk_1-4, then atk_5/6/7/pos_control), axiom-print checks in a third parallel batch of 3. All completed; no timeouts.

VERDICT: SOUND — ≥5 distinct attacks run (7 total: prepatch, boundary, swap, partial-domain, control-flow-effect, 2 echoes); every attack with a closing clean-axiom proof (atk_6, atk_7) has a materialized faithful patch that RESOLVES. Spec is complete and faithful; no gap between verify and correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found; spec is faithful and not too strong.

MODELED BEHAVIOR: BaseManager._get_queryset_methods.create_method (django/db/models/manager.py:83-89). Gold patch replaces manual `manager_method.__name__=method.__name__; manager_method.__doc__=method.__doc__` with `@wraps(method)`. Spec models the produced method's introspectable metadata tuple (__name__, __qualname__, __module__, __doc__, __annotations__, str(inspect.signature(...))) as MethodMetadata (6 Strings). post-conditions pin ALL SIX fields of result to `underlying`'s corresponding fields.

SPEC-REGION BYTE-IDENTITY: swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean-backend) = True. Spec view (axioms/pure/post-conditions) is byte-identical between variants; only impl/proof differ. No hidden spec drift.

LEAN PROOF GENUINE: scripts/lean_verify.sh Solution.lean -> exit 0, no sorry. `#print axioms correct_delegateMetadata` -> 'does not depend on any axioms'. Not a sorryAx / fake proof.

FAITHFULNESS CHECK (spec vs real repo post-patch): Reproduced the real @wraps(method) + inspect.signature read-back in-process (worktree was empty, but the modeled behavior is generic CPython functools/inspect, fully reproducible). On every tested input all six produced attributes equal underlying's:
  - CASE1 annotated bulk_create: name/qualname/module/doc/annotations/signature all equal; signature follows __wrapped__ to '(self, objs: 'list', batch_size=None, ignore_conflicts=False) -> 'list'' (the real param list, not the catch-all) — the exact F2P discriminator.
  - CASE2 underlying missing __annotations__: produced annotations copied consistently.
  - CASE3 underlying whose signature coincidentally == '(self,*args,**kwargs)': produced signature matches.
  - CASE4 doc=None: produced doc=None.
The spec's post-condition (result field == underlying field for all six) matches real callee behavior on all valid inputs. G-CONF (120k fuzz + edge cases, seed 15731) independently differential-tests the R/I shadow against the real @wraps oracle and passes.

NOT TOO STRONG: The patch genuinely forces every one of these six introspectable attributes to equal the underlying method's (WRAPPER_ASSIGNMENTS copy + __wrapped__ signature follow). The spec constrains exactly these six and nothing else; it does NOT over-constrain the unchanged runtime call body (getattr(self.get_queryset(), name)(...)), which the patch leaves untouched and which is correctly not modeled. axioms=[] and deep_model_references=[] are consistent: the @wraps effect is modeled deeply as a field copy (all R/I), so no unchanged-callee contract is asserted that could over- or under-constrain.

No diverging input exists where the modeled function disagrees with the real post-patch callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (not hints_text). The gold edit is: import functools.wraps, decorate manager_method with @wraps(method), and remove the manual __name__/__doc__ assignments in django/db/models/manager.py. The public problem_statement already discloses the ENTIRE fix verbatim: it cites manager.py:L84, says 'complete metadata is not copied', and states 'The fix is to use functools.wraps instead of manually assigning name and docstring. wraps will take care of all the metadata and inspect.signature will return the expected output.'

Spec view (docstring + MethodMetadata structure + problem_spec_delegateMetadata postcondition; impl/proof elided) analysis:
- No diff markers, no patched file path (manager.py) or module path (django.db.models.manager) present.
- No patched repo symbol echoed: the spec abstracts to 'delegating method / bare forwarding wrapper / underlying method'; it never names create_method, manager_method, or even functools.wraps. Mechanical screen's sole changed-symbol was the non-distinctive 'check' (false positive not in the view).
- No gold-patch changed line reproduced; no bug/fix narration terms.
- The six-field metadata enumeration (name/qualname/module/doc/annotations/signature = underlying's) is a behavioral spec of 'mirror ALL introspectable metadata' — derivable from the public 'complete metadata / functools.wraps takes care of all the metadata'. It describes WHAT the produced method must observe, not WHERE/HOW to edit; it does not localize the gold edit beyond the already-public statement.

Mechanical G-LEAK screen: PASSED (hard_failures=[]). same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical, so the injected bug lives entirely in impl/proof, not the consumer-visible spec). No RELAXED_LEAKAGE.md / relaxed flag. Nothing from hints_text echoed. The spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
