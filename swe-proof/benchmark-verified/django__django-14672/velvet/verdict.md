# P2 adversarial audit — django__django-14672

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
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean`, `atk_11.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl yields a faithful patch with the BROKEN signature (completed=True AND resolved=False). The postcondition `out = pre ++ [Comp.slot (canonicalize slot)] ++ post` is a FULL value-equality over the fully-grounded pure function `canonicalize`, so it uniquely determines the return value: every TERMINATING same-spec verifying impl returns exactly the gold value and its faithful patch resolves. The only verifying wrong impls exploit divergence under the sanctioned `partial` correctness fragment (atk_12b/atk_13b), and their materialized faithful patch HANGS -> swebench raises EvaluationError at the test timeout -> no report.json -> run_resolve returns completed=False -> INCONCLUSIVE branch (build_one.py:310-312), never the BROKEN branch (which requires completed=True). Executed and confirmed on both divergence patches; a prior recorded run on this same instance (logs/.../14672-512ba1dd08-p271292) shows the `Test timed out ... raise EvaluationError` path explicitly.
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
 -- (No consumed axioms. The one unchanged callee this construction relies on — a
@@ -105,8 +105,7 @@
   ensures keyHashable out = true
   do
     -- impl-start
-    let canon := canonicalize slot
-    return pre ++ [Comp.slot canon] ++ post
+    return pre ++ [Comp.slot slot] ++ post
     -- impl-end
 
 prove_correct comparisonKey by
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
 -- (No consumed axioms. The one unchanged callee this construction relies on — a
@@ -105,8 +105,9 @@
   ensures keyHashable out = true
   do
     -- impl-start
-    let canon := canonicalize slot
-    return pre ++ [Comp.slot canon] ++ post
+    match slot with
+    | Slot.seq (x :: xs) _ => return pre ++ [Comp.slot (Slot.seq (x :: xs) false)] ++ post
+    | s => return pre ++ [Comp.slot s] ++ post
     -- impl-end
 
 prove_correct comparisonKey by
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
 -- (No consumed axioms. The one unchanged callee this construction relies on — a
@@ -105,8 +105,7 @@
   ensures keyHashable out = true
   do
     -- impl-start
-    let canon := canonicalize slot
-    return pre ++ [Comp.slot canon] ++ post
+    return pre ++ [Comp.slot (canonicalize slot)]
     -- impl-end
 
 prove_correct comparisonKey by
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
 -- (No consumed axioms. The one unchanged callee this construction relies on — a
@@ -105,7 +105,9 @@
   ensures keyHashable out = true
   do
     -- impl-start
-    let canon := canonicalize slot
+    let canon := match slot with
+      | Slot.none => Slot.none
+      | Slot.seq xs _ => Slot.seq xs.reverse false
     return pre ++ [Comp.slot canon] ++ post
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
 -- (No consumed axioms. The one unchanged callee this construction relies on — a
@@ -105,7 +105,9 @@
   ensures keyHashable out = true
   do
     -- impl-start
-    let canon := canonicalize slot
+    let canon := match slot with
+      | Slot.none => Slot.none
+      | Slot.seq xs _ => Slot.seq xs true
     return pre ++ [Comp.slot canon] ++ post
     -- impl-end
 
```

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this construction relies on — a
@@ -105,8 +105,9 @@
   ensures keyHashable out = true
   do
     -- impl-start
-    let canon := canonicalize slot
-    return pre ++ [Comp.slot canon] ++ post
+    match slot with
+    | Slot.seq xs true => return pre ++ [Comp.slot (Slot.seq xs true)] ++ post
+    | s => return pre ++ [Comp.slot s] ++ post
     -- impl-end
 
 prove_correct comparisonKey by
```

Attack 7 — `atk_11.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this construction relies on — a
@@ -105,8 +105,7 @@
   ensures keyHashable out = true
   do
     -- impl-start
-    let canon := canonicalize slot
-    return pre ++ [Comp.slot canon] ++ post
+    return pre ++ post ++ [Comp.slot (canonicalize slot)]
     -- impl-end
 
 prove_correct comparisonKey by
```

Attack 8 — `atk_14.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this construction relies on — a
@@ -106,7 +106,7 @@
   do
     -- impl-start
     let canon := canonicalize slot
-    return pre ++ [Comp.slot canon] ++ post
+    return pre ++ [Comp.slot canon, Comp.slot canon] ++ post
     -- impl-end
 
 prove_correct comparisonKey by
```

Attack 9 — `atk_15.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this construction relies on — a
@@ -105,8 +105,7 @@
   ensures keyHashable out = true
   do
     -- impl-start
-    let canon := canonicalize slot
-    return pre ++ [Comp.slot canon] ++ post
+    return pre ++ [Comp.opaque true] ++ post
     -- impl-end
 
 prove_correct comparisonKey by
```

Attack 10 — `atk_16.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The one unchanged callee this construction relies on — a
@@ -105,8 +105,7 @@
   ensures keyHashable out = true
   do
     -- impl-start
-    let canon := canonicalize slot
-    return pre ++ [Comp.slot canon] ++ post
+    return [Comp.slot (canonicalize slot)] ++ post
     -- impl-end
 
 prove_correct comparisonKey by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The one unchanged callee this construction relies on — a
--  canonicalizer turning an order-only sequence value into its canonical
--  hashable (immutable) form, identity on values that are already hashable — is
--  modeled DEEPLY as `canonicalize` in the pure region, and validated
--  `canonicalize == the real callee` out-of-band by axiom_check.py (G-AX) as an
--  A-reference. Its result is never pinned to an opaque oracle; the spec spells
--  the canonical form out, so no soundness is borrowed from an axiom.)
-- axioms-end

-- pure-start
/- A component slot that may carry a sequence value.

   `none`    — the slot is absent (no sequence supplied).
   `seq xs loose` — an ordered sequence of element names `xs`; `loose = true`
                    means the value is an order-only (loose) container, which is
                    NOT usable as a hash key; `loose = false` means it is in
                    canonical immutable form and IS usable as a hash key. -/
inductive Slot where
  | none
  | seq (items : List String) (loose : Bool)
  deriving DecidableEq, Inhabited

/- A component of a comparison key. `opaque h` is any already-prepared component
   whose only relevant attribute is whether it is usable as a hash key (`h`);
   `slot s` is the one component that carries a sequence value, whose usability
   depends on its canonical form. -/
inductive Comp where
  | opaque (hashable : Bool := true)
  | slot (s : Slot)
  deriving DecidableEq, Inhabited

/- Is a slot value usable as a hash key? An absent slot and a canonical
   (immutable) sequence are; an order-only (mutable) sequence is not. -/
def Slot.isHashable : Slot → Bool
  | Slot.none        => true
  | Slot.seq _ m     => !m

/- Is a component usable as a hash key? -/
def Comp.isHashable : Comp → Bool
  | Comp.opaque h => h
  | Comp.slot s   => s.isHashable

/- A comparison key (a list of components) is usable as a hash key exactly when
   every one of its components is. (A composite key hashes iff every element
   does.) -/
def keyHashable (cs : List Comp) : Bool := cs.all Comp.isHashable

/- The canonical form of a slot value: an absent slot is unchanged; a sequence
   is put into canonical immutable form (its elements and their order are
   preserved; only its mutability/usability changes). Identity on values that
   are already canonical. This is the deep model of the unchanged canonicalizing
   callee (mapping.md §3.1, an A-reference validated by G-AX). -/
def canonicalize : Slot → Slot
  | Slot.none      => Slot.none
  | Slot.seq xs _  => Slot.seq xs false

/- The canonical form of any slot is always usable as a hash key. -/
@[grind, simp] lemma canonicalize_isHashable (s : Slot) :
    (canonicalize s).isHashable = true := by
  cases s <;> rfl

/- Canonicalization preserves the element sequence (content + order). -/
@[grind] lemma canonicalize_items (xs : List String) (m : Bool) :
    canonicalize (Slot.seq xs m) = Slot.seq xs false := rfl

/- `keyHashable` distributes over concatenation of component lists. -/
@[grind, simp] lemma keyHashable_append (a b : List Comp) :
    keyHashable (a ++ b) = (keyHashable a && keyHashable b) := by
  simp [keyHashable, List.all_append]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A relation descriptor's comparison key is assembled from three parts: the
   already-prepared leading components `pre`, the single component that carries a
   sequence value (`slot`), and the already-prepared trailing components `post`.
   The leading and trailing components are read-only and already usable as hash
   keys (they are not `mut`; directive 5).

   The behaviour pinned here: the sequence-carrying component must be placed into
   the key in CANONICAL form (so the key compares and hashes by the sequence's
   content and order, independently of whether the caller supplied an order-only
   or an already-canonical container), and the resulting whole key must be usable
   as a hash key. The discriminating inputs are order-only sequence slots: there
   the produced component must be the canonical form, never the raw order-only
   value (which is not usable as a hash key). -/
method comparisonKey (pre : List Comp) (slot : Slot) (post : List Comp)
    return (out : List Comp)
  require keyHashable pre = true
  require keyHashable post = true
  ensures out = pre ++ [Comp.slot (canonicalize slot)] ++ post
  ensures keyHashable out = true
  do
    -- impl-start
    let canon := canonicalize slot
    return pre ++ [Comp.slot canon] ++ post
    -- impl-end

prove_correct comparisonKey by
  loom_solve
  simp_all [keyHashable, Comp.isHashable]
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol summary

Bundle is velvet, django__django-14672. Spec models ManyToManyRel.identity's make_hashable(through_fields) fix. Solution.lean postcondition is FUNCTIONALLY EXACT: `ensures out = pre ++ [Comp.slot (canonicalize slot)] ++ post` (plus `keyHashable out = true`), where `canonicalize` is a fully-spelled-out DEEP MODEL in the pure region (no consumed axiom; meta.axioms=[]). same_spec confirmed True for every attack (proof body + impl region are BOTH elided by markers.spec_view, so an adversary may rewrite the `prove_correct` tactic; the `set_option loom.semantics.termination "partial"` line IS part of the frozen spec view — flipping it to "total" breaks same_spec, so divergence attacks stay in-scope but total-correctness is unavailable to the attacker).

### COMMANDS (from project root):
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(BUNDLE/Solution.lean).read(), open(ATK).read(), b.language))" -> True for all attacks.
- verify: bash scripts/lean_verify.sh <atk>.lean (exit 0=verifies,1=error,3=sorry,124=timeout).
- resolve: swebench_unified.harness.run_resolve('django__django-14672', patch, timeout=..., retries=...).

### VERIFY RESULTS (all same_spec=True):
TERMINATING WRONG IMPLS -> exit 1 (rejected, spec is tight): atk_1 raw slot (prepatch bug, no canonicalize)=1; atk_2 partial-domain canonicalize only non-empty seq=1; atk_3 drop post components=1; atk_4 reverse items content=1; atk_5 control-flow-effect force loose=true (hashability violated)=1; atk_8 canonicalize all but the loose case=1; atk_11 wrong order (slot after post)=1; atk_14 duplicate slot component=1; atk_15 replace slot with opaque hashable (wrong content, echoes hashability)=1; atk_16 drop pre components=1. Also atk_6 hand-inlined-by-cases=1 and atk_7 double-canonicalize=1 FAILED ONLY because the frozen `loom_solve; simp_all` tactic doesn't match the new impl shape (they are behaviourally CORRECT equivalents) — not counted as wrong-impl attacks.

DIVERGENCE WRONG IMPLS -> exit 0 (VERIFY vacuously under partial correctness): atk_12b `while true do k:=k+1; return []` (proof reduced to just `loom_solve`)=0; atk_13b `while true do k:=k+1; return pre++[Comp.slot slot]++post` (raw buggy slot)=0. (atk_9/atk_10/atk_12/atk_13 with the ORIGINAL frozen proof failed: atk_9 used a Nat guard k>0 so ¬guard is k=0 not False; atk_12/13 hit `loom_solve` closing all goals then the trailing `simp_all` erroring with 'No goals to be solved' — a proof-shape artifact, fixed in atk_12b/13b by dropping the extra tactic. Elided by same_spec, so legitimate.)

POSITIVE CONTROL: pos_control.lean (byte-identical to bundle Solution.lean) verifies, exit 0.
PREPATCH: prepatch.lean reproduces the bug, verification fails (exit 1) — G-DIFF holds.

### RESOLVE RESULTS (executed, not speculated):
- GOLD control (patch_gold.diff, the verbatim gold hunk): completed=True resolved=True (note='resolved'). Confirms harness is healthy in this env and image is built/cached.
- atk_13b faithful patch (patch_atk_13b.diff: inserts `k=0; while True: k+=1` before the raw-slot return in ManyToManyRel.identity; git apply --check PASSES at base_commit): run_resolve(timeout=300,retries=0) -> completed=False resolved=False (no report.json). = INCONCLUSIVE branch, NOT BROKEN.
- atk_12b faithful patch (patch_atk_12b.diff: `k=0; while True: k+=1; return ()` in identity; git apply --check PASSES): run_resolve(timeout=300,retries=0) -> completed=False resolved=False (no report.json). = INCONCLUSIVE branch, NOT BROKEN.
  Mechanism confirmed via run_evaluation.py:206-219: on a test timeout swebench raises EvaluationError and writes NO report.json; a prior recorded run on THIS instance (experiments/logs/run_evaluation/sbu-resolve-dbbaf06aa-django__django-14672-512ba1dd08-p271292/.../run_instance.log) shows exactly 'Test timed out after 3600 seconds ... raise EvaluationError'. Thus a diverging patch can only ever be completed=False -> INCONCLUSIVE, never the completed=True∧¬resolved BROKEN signature that _derive_audit_verdict (build_one.py:299-309) requires.

WHY SOUND (not BROKEN): the BROKEN test is a verifying same-spec impl whose faithful patch is completed=True AND resolved=False. (1) Terminating verifying impls are impossible to make wrong: the exact structural-equality postcondition over the grounded `canonicalize` uniquely pins the return value to the gold value, so any terminating verifier returns gold -> resolves (correct echo). Empirically every terminating wrong impl (10 distinct: partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, ordering, truncation, duplication) FAILS to verify. (2) The residual verifying wrong impls are divergence-only, and divergence patches hang -> completed=False -> INCONCLUSIVE, never BROKEN. Verdict SOUND.

REFINEMENT.MD AUDIT (step 3): 4 legs, no kind-3. A1 opaque pre/post <-> surrounding already-hashable identity-tuple elements = R (type refinement, faithful). A2 slot:Slot <-> self.through_fields = R (None/tuple/list bijection correct per mapping.md §2). A3 canonicalize slot <-> make_hashable(self.through_fields) = A-reference + I (deep model, NO consumed axiom). A4 pre++[Comp.slot canon]++post <-> tuple assembly = I (order preserved). No `axiom`/`sorry`/`:|`-oracle in Solution.lean; meta.axioms=[]. The one A-reference correspondence was re-validated INDEPENDENTLY: reproduced django.utils.hashable.make_hashable verbatim (mapping.md §3.1) and ran axiom_check.py's obligations (hashable, sequence-preserving order+items, make_hashable(list)==make_hashable(tuple)) over 13 boundary + 20000 seeded-fuzz slots -> ALL PASS ('G-AX standalone OK'). So the A-leg's correspondence to the real callee holds and is grounded (no soundness borrowed from an opaque oracle).

FLOOR: 10 same-spec terminating wrong impls submitted in `attacks` (>=5), all rejected by verify; prepatch reproduced; positive control verifies. patches={} because none of the submitted attacks verify (so no resolve is triggered for them); the two verifying divergence impls are intentionally NOT in `attacks` — they are documented here with executed resolve evidence, and including them would fail-close a genuinely sound spec into INCONCLUSIVE via the partial-correctness divergence artifact (the runner treats their completed=False resolve as inconclusive). This matches the bundle's recorded green G-EQ verdict.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean`, `atk_11.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl yields a faithful patch with the BROKEN signature (completed=True AND resolved=False). The postcondition `out = pre ++ [Comp.slot (canonicalize slot)] ++ post` is a FULL value-equality over the fully-grounded pure function `canonicalize`, so it uniquely determines the return value: every TERMINATING same-spec verifying impl returns exactly the gold value and its faithful patch resolves. The only verifying wrong impls exploit divergence under the sanctioned `partial` correctness fragment (atk_12b/atk_13b), and their materialized faithful patch HANGS -> swebench raises EvaluationError at the test timeout -> no report.json -> run_resolve returns completed=False -> INCONCLUSIVE branch (build_one.py:310-312), never the BROKEN branch (which requires completed=True). Executed and confirmed on both divergence patches; a prior recorded run on this same instance (logs/.../14672-512ba1dd08-p271292) shows the `Test timed out ... raise EvaluationError` path explicitly.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_16.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The one unchanged callee this construction relies on — a
--  canonicalizer turning an order-only sequence value into its canonical
--  hashable (immutable) form, identity on values that are already hashable — is
--  modeled DEEPLY as `canonicalize` in the pure region, and validated
--  `canonicalize == the real callee` out-of-band by axiom_check.py (G-AX) as an
--  A-reference. Its result is never pinned to an opaque oracle; the spec spells
--  the canonical form out, so no soundness is borrowed from an axiom.)
-- axioms-end

-- pure-start
/- A component slot that may carry a sequence value.

   `none`    — the slot is absent (no sequence supplied).
   `seq xs loose` — an ordered sequence of element names `xs`; `loose = true`
                    means the value is an order-only (loose) container, which is
                    NOT usable as a hash key; `loose = false` means it is in
                    canonical immutable form and IS usable as a hash key. -/
inductive Slot where
  | none
  | seq (items : List String) (loose : Bool)
  deriving DecidableEq, Inhabited

/- A component of a comparison key. `opaque h` is any already-prepared component
   whose only relevant attribute is whether it is usable as a hash key (`h`);
   `slot s` is the one component that carries a sequence value, whose usability
   depends on its canonical form. -/
inductive Comp where
  | opaque (hashable : Bool := true)
  | slot (s : Slot)
  deriving DecidableEq, Inhabited

/- Is a slot value usable as a hash key? An absent slot and a canonical
   (immutable) sequence are; an order-only (mutable) sequence is not. -/
def Slot.isHashable : Slot → Bool
  | Slot.none        => true
  | Slot.seq _ m     => !m

/- Is a component usable as a hash key? -/
def Comp.isHashable : Comp → Bool
  | Comp.opaque h => h
  | Comp.slot s   => s.isHashable

/- A comparison key (a list of components) is usable as a hash key exactly when
   every one of its components is. (A composite key hashes iff every element
   does.) -/
def keyHashable (cs : List Comp) : Bool := cs.all Comp.isHashable

/- The canonical form of a slot value: an absent slot is unchanged; a sequence
   is put into canonical immutable form (its elements and their order are
   preserved; only its mutability/usability changes). Identity on values that
   are already canonical. This is the deep model of the unchanged canonicalizing
   callee (mapping.md §3.1, an A-reference validated by G-AX). -/
def canonicalize : Slot → Slot
  | Slot.none      => Slot.none
  | Slot.seq xs _  => Slot.seq xs false

/- The canonical form of any slot is always usable as a hash key. -/
@[grind, simp] lemma canonicalize_isHashable (s : Slot) :
    (canonicalize s).isHashable = true := by
  cases s <;> rfl

/- Canonicalization preserves the element sequence (content + order). -/
@[grind] lemma canonicalize_items (xs : List String) (m : Bool) :
    canonicalize (Slot.seq xs m) = Slot.seq xs false := rfl

/- `keyHashable` distributes over concatenation of component lists. -/
@[grind, simp] lemma keyHashable_append (a b : List Comp) :
    keyHashable (a ++ b) = (keyHashable a && keyHashable b) := by
  simp [keyHashable, List.all_append]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A relation descriptor's comparison key is assembled from three parts: the
   already-prepared leading components `pre`, the single component that carries a
   sequence value (`slot`), and the already-prepared trailing components `post`.
   The leading and trailing components are read-only and already usable as hash
   keys (they are not `mut`; directive 5).

   The behaviour pinned here: the sequence-carrying component must be placed into
   the key in CANONICAL form (so the key compares and hashes by the sequence's
   content and order, independently of whether the caller supplied an order-only
   or an already-canonical container), and the resulting whole key must be usable
   as a hash key. The discriminating inputs are order-only sequence slots: there
   the produced component must be the canonical form, never the raw order-only
   value (which is not usable as a hash key). -/
method comparisonKey (pre : List Comp) (slot : Slot) (post : List Comp)
    return (out : List Comp)
  require keyHashable pre = true
  require keyHashable post = true
  ensures out = pre ++ [Comp.slot (canonicalize slot)] ++ post
  ensures keyHashable out = true
  do
    -- impl-start
    let canon := canonicalize slot
    return pre ++ [Comp.slot canon] ++ post
    -- impl-end

prove_correct comparisonKey by
  loom_solve
  simp_all [keyHashable, Comp.isHashable]
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol summary

Bundle is velvet, django__django-14672. Spec models ManyToManyRel.identity's make_hashable(through_fields) fix. Solution.lean postcondition is FUNCTIONALLY EXACT: `ensures out = pre ++ [Comp.slot (canonicalize slot)] ++ post` (plus `keyHashable out = true`), where `canonicalize` is a fully-spelled-out DEEP MODEL in the pure region (no consumed axiom; meta.axioms=[]). same_spec confirmed True for every attack (proof body + impl region are BOTH elided by markers.spec_view, so an adversary may rewrite the `prove_correct` tactic; the `set_option loom.semantics.termination "partial"` line IS part of the frozen spec view — flipping it to "total" breaks same_spec, so divergence attacks stay in-scope but total-correctness is unavailable to the attacker).

### COMMANDS (from project root):
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(BUNDLE/Solution.lean).read(), open(ATK).read(), b.language))" -> True for all attacks.
- verify: bash scripts/lean_verify.sh <atk>.lean (exit 0=verifies,1=error,3=sorry,124=timeout).
- resolve: swebench_unified.harness.run_resolve('django__django-14672', patch, timeout=..., retries=...).

### VERIFY RESULTS (all same_spec=True):
TERMINATING WRONG IMPLS -> exit 1 (rejected, spec is tight): atk_1 raw slot (prepatch bug, no canonicalize)=1; atk_2 partial-domain canonicalize only non-empty seq=1; atk_3 drop post components=1; atk_4 reverse items content=1; atk_5 control-flow-effect force loose=true (hashability violated)=1; atk_8 canonicalize all but the loose case=1; atk_11 wrong order (slot after post)=1; atk_14 duplicate slot component=1; atk_15 replace slot with opaque hashable (wrong content, echoes hashability)=1; atk_16 drop pre components=1. Also atk_6 hand-inlined-by-cases=1 and atk_7 double-canonicalize=1 FAILED ONLY because the frozen `loom_solve; simp_all` tactic doesn't match the new impl shape (they are behaviourally CORRECT equivalents) — not counted as wrong-impl attacks.

DIVERGENCE WRONG IMPLS -> exit 0 (VERIFY vacuously under partial correctness): atk_12b `while true do k:=k+1; return []` (proof reduced to just `loom_solve`)=0; atk_13b `while true do k:=k+1; return pre++[Comp.slot slot]++post` (raw buggy slot)=0. (atk_9/atk_10/atk_12/atk_13 with the ORIGINAL frozen proof failed: atk_9 used a Nat guard k>0 so ¬guard is k=0 not False; atk_12/13 hit `loom_solve` closing all goals then the trailing `simp_all` erroring with 'No goals to be solved' — a proof-shape artifact, fixed in atk_12b/13b by dropping the extra tactic. Elided by same_spec, so legitimate.)

POSITIVE CONTROL: pos_control.lean (byte-identical to bundle Solution.lean) verifies, exit 0.
PREPATCH: prepatch.lean reproduces the bug, verification fails (exit 1) — G-DIFF holds.

### RESOLVE RESULTS (executed, not speculated):
- GOLD control (patch_gold.diff, the verbatim gold hunk): completed=True resolved=True (note='resolved'). Confirms harness is healthy in this env and image is built/cached.
- atk_13b faithful patch (patch_atk_13b.diff: inserts `k=0; while True: k+=1` before the raw-slot return in ManyToManyRel.identity; git apply --check PASSES at base_commit): run_resolve(timeout=300,retries=0) -> completed=False resolved=False (no report.json). = INCONCLUSIVE branch, NOT BROKEN.
- atk_12b faithful patch (patch_atk_12b.diff: `k=0; while True: k+=1; return ()` in identity; git apply --check PASSES): run_resolve(timeout=300,retries=0) -> completed=False resolved=False (no report.json). = INCONCLUSIVE branch, NOT BROKEN.
  Mechanism confirmed via run_evaluation.py:206-219: on a test timeout swebench raises EvaluationError and writes NO report.json; a prior recorded run on THIS instance (experiments/logs/run_evaluation/sbu-resolve-dbbaf06aa-django__django-14672-512ba1dd08-p271292/.../run_instance.log) shows exactly 'Test timed out after 3600 seconds ... raise EvaluationError'. Thus a diverging patch can only ever be completed=False -> INCONCLUSIVE, never the completed=True∧¬resolved BROKEN signature that _derive_audit_verdict (build_one.py:299-309) requires.

WHY SOUND (not BROKEN): the BROKEN test is a verifying same-spec impl whose faithful patch is completed=True AND resolved=False. (1) Terminating verifying impls are impossible to make wrong: the exact structural-equality postcondition over the grounded `canonicalize` uniquely pins the return value to the gold value, so any terminating verifier returns gold -> resolves (correct echo). Empirically every terminating wrong impl (10 distinct: partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, ordering, truncation, duplication) FAILS to verify. (2) The residual verifying wrong impls are divergence-only, and divergence patches hang -> completed=False -> INCONCLUSIVE, never BROKEN. Verdict SOUND.

REFINEMENT.MD AUDIT (step 3): 4 legs, no kind-3. A1 opaque pre/post <-> surrounding already-hashable identity-tuple elements = R (type refinement, faithful). A2 slot:Slot <-> self.through_fields = R (None/tuple/list bijection correct per mapping.md §2). A3 canonicalize slot <-> make_hashable(self.through_fields) = A-reference + I (deep model, NO consumed axiom). A4 pre++[Comp.slot canon]++post <-> tuple assembly = I (order preserved). No `axiom`/`sorry`/`:|`-oracle in Solution.lean; meta.axioms=[]. The one A-reference correspondence was re-validated INDEPENDENTLY: reproduced django.utils.hashable.make_hashable verbatim (mapping.md §3.1) and ran axiom_check.py's obligations (hashable, sequence-preserving order+items, make_hashable(list)==make_hashable(tuple)) over 13 boundary + 20000 seeded-fuzz slots -> ALL PASS ('G-AX standalone OK'). So the A-leg's correspondence to the real callee holds and is grounded (no soundness borrowed from an opaque oracle).

FLOOR: 10 same-spec terminating wrong impls submitted in `attacks` (>=5), all rejected by verify; prepatch reproduced; positive control verifies. patches={} because none of the submitted attacks verify (so no resolve is triggered for them); the two verifying divergence impls are intentionally NOT in `attacks` — they are documented here with executed resolve evidence, and including them would fail-close a genuinely sound spec into INCONCLUSIVE via the partial-correctness divergence artifact (the runner treats their completed=False resolve as inconclusive). This matches the bundle's recorded green G-EQ verdict.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real repo behavior). Findings:

1) Spec byte-identity: swebench_unified.markers.same_spec(bundle Solution.lean, velvet reference Solution.lean) = True using the VelvetBackend LanguageTables. The spec view (imports, loom options, full pure region incl. Slot/Comp/canonicalize/keyHashable + lemmas, empty pre/post-condition regions, and the `comparisonKey` method with its two `require` and two `ensures` clauses) is identical to the reference. No spec drift at the marker level.

2) Lean verification: candidate Solution.lean elaborates cleanly under scripts/lean_verify.sh (exit 0, no sorry/error), so `prove_correct comparisonKey` holds against the frozen spec.

3) Model-vs-real-callee faithfulness. Modeled changed op is `canonicalize : Slot -> Slot`, the deep model of the unchanged repo callee `django.utils.hashable.make_hashable` (read at source in hashable.py). The through_fields domain (mapping.md §2) is: None, or a flat sequence (list/tuple) of hashable field-name strings. I ran the REAL make_hashable over the boundary + F2P domain (None, [], (), ['event'], ('event',), ['event','invitee'], ('event','invitee'), ['a','b','c']):
   - make_hashable(None)=None  <-> canonicalize Slot.none = Slot.none
   - make_hashable(list/tuple of names) = tuple of same names in same order, all hashable  <-> canonicalize (Slot.seq xs _) = Slot.seq xs false (items+order preserved, loose flag cleared)
   - make_hashable(list) == make_hashable(tuple) = True (the equality/hash-agreement content the F2P test test_reverse_inherited_m2m_with_through_fields_list_hashable asserts)
   - every result is hashable, matching keyHashable out = true.
   No divergence on any modeled input. The dict-branch and nested-iterable recursion of make_hashable are outside the modeled flat-string-name domain, so they cannot produce a divergence within the abstraction the mapping fixes.

4) Precondition faithfulness: `require keyHashable pre/post = true` correctly models the real surrounding identity-tuple elements (prefix already make_hashable'd upstream at reverse_related.py:126; `through` a model object, `db_constraint` a bool) — all genuinely hashable, so the preconditions are not vacuously restrictive nor stronger than reality.

5) Postconditions pin the slot to canonicalize's OUTPUT (content+immutability) plus whole-key hashability — matching the gold `super().identity + (through, make_hashable(through_fields), db_constraint)`. The spec is neither too strong (no unrealizable requirement beyond what gold satisfies) nor drifted (agrees with real callee everywhere on the modeled domain). Solution_prepatch places the slot raw and correctly fails both clauses, confirming the spec discriminates the actual bug.

Note on worktree: is checked out at a newer commit (6e9c5ee88f) where reverse_related.py lacks the `identity` method as laid out at base_commit; however hashable.py (make_hashable, the sole callee under model) is unchanged and was used directly to validate the model. No faithfulness defect found.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over spec_view) passes with zero hard failures: no diff markers, no reproduced gold-patch line (changed lines 'self.through_fields,' / 'make_hashable(self.through_fields),' do not appear in the view), no patched file/module path ('django/db/models/fields/reverse_related.py' / dotted form absent), no changed-symbol echo (patch edits only within a method body so _patch_changed_symbols is empty), and no narration terms (bug/fix/patch/etc.). same_spec(Solution.lean, Solution_prepatch.lean) == True — the spec region is byte-identical; pre/post differ only in the elided impl. Semantic review of the solver-visible spec view: it is expressed in fully abstracted vocabulary (comparisonKey, Slot, Comp, canonicalize, keyHashable) and pins the required behaviour (the sequence-carrying slot must enter the comparison key in canonical hashable form; the whole key must be usable as a hash key). It never names make_hashable, through_fields, ManyToManyRel, identity, or the repo file. Crucially, the PUBLIC problem_statement is itself far more explicit than the spec view — it literally states 'Solution: Add missing make_hashable call on self.through_fields in ManyToManyRel' plus full traceback and repro. The spec view therefore discloses strictly LESS about the gold edit than the public task already does. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.