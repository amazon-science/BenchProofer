# P2 adversarial audit — django__django-13128

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- axioms-end
@@ -79,14 +79,6 @@
   do
     -- impl-start
     let mut out := selfKind
-    if selfKind = NodeKind.combined then
-      if isIntervalMix lt rt then
-        out := NodeKind.durationNode
-      else
-        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
-          out := NodeKind.temporalNode
-        else
-          out := NodeKind.combined
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
 -- axioms-end
@@ -83,10 +83,7 @@
       if isIntervalMix lt rt then
         out := NodeKind.durationNode
       else
-        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
-          out := NodeKind.temporalNode
-        else
-          out := NodeKind.combined
+        out := NodeKind.combined
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
 -- axioms-end
@@ -83,7 +83,7 @@
       if isIntervalMix lt rt then
         out := NodeKind.durationNode
       else
-        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
+        if isTemporalTag lt ∧ lt = rt then
           out := NodeKind.temporalNode
         else
           out := NodeKind.combined
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
@@ -80,13 +80,12 @@
     -- impl-start
     let mut out := selfKind
     if selfKind = NodeKind.combined then
-      if isIntervalMix lt rt then
+      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
+        out := NodeKind.temporalNode
+      else if isIntervalMix lt rt then
         out := NodeKind.durationNode
       else
-        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
-          out := NodeKind.temporalNode
-        else
-          out := NodeKind.combined
+        out := NodeKind.combined
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
 -- axioms-end
@@ -83,7 +83,7 @@
       if isIntervalMix lt rt then
         out := NodeKind.durationNode
       else
-        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
+        if conn = Connector.minus ∧ isTemporalTag lt then
           out := NodeKind.temporalNode
         else
           out := NodeKind.combined
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
 -- axioms-end
@@ -78,15 +78,7 @@
   ensures out = dispatchKind selfKind conn lt rt
   do
     -- impl-start
-    let mut out := selfKind
-    if selfKind = NodeKind.combined then
-      if isIntervalMix lt rt then
-        out := NodeKind.durationNode
-      else
-        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
-          out := NodeKind.temporalNode
-        else
-          out := NodeKind.combined
+    let out := dispatchKind selfKind conn lt rt
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
 -- axioms-end
@@ -80,7 +80,7 @@
     -- impl-start
     let mut out := selfKind
     if selfKind = NodeKind.combined then
-      if isIntervalMix lt rt then
+      if (lt = some FieldTag.durationTag ∨ rt = some FieldTag.durationTag) then
         out := NodeKind.durationNode
       else
         if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
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
@@ -79,14 +79,12 @@
   do
     -- impl-start
     let mut out := selfKind
-    if selfKind = NodeKind.combined then
-      if isIntervalMix lt rt then
-        out := NodeKind.durationNode
-      else
-        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
-          out := NodeKind.temporalNode
-        else
-          out := NodeKind.combined
+    if isIntervalMix lt rt then
+      out := NodeKind.durationNode
+    else if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
+      out := NodeKind.temporalNode
+    else
+      out := NodeKind.combined
     return out
     -- impl-end
 
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
/- The output-type tag a resolved operand can carry. The four temporal/interval
   tags are distinguished; every other concrete tag (and the "no resolvable
   type" outcome, carried as `none` on the `Option`) collapses to `otherType`,
   since only these four participate in the selection below. -/
inductive FieldTag where
  | dateTag
  | dateTimeTag
  | timeTag
  | durationTag
  | otherType
  deriving DecidableEq, Inhabited

/- The binary connector joining the two operands. Only the difference connector
   participates in the temporal branch; every other connector behaves the same
   for the selection. -/
inductive Connector where
  | plus
  | minus
  deriving DecidableEq, Inhabited

/- The node kind of a binary expression. `combined` is the generic node; the
   other two are the specialised interval / temporal-difference nodes. -/
inductive NodeKind where
  | combined
  | durationNode
  | temporalNode
  deriving DecidableEq, Inhabited

/- The three tags whose pairwise difference denotes a point-in-time difference. -/
def isTemporalTag (t : Option FieldTag) : Prop :=
  t = some FieldTag.dateTag ∨ t = some FieldTag.dateTimeTag ∨ t = some FieldTag.timeTag

instance (t : Option FieldTag) : Decidable (isTemporalTag t) := by
  unfold isTemporalTag; infer_instance

/- The interval-mix predicate: exactly one operand carries the interval tag (the
   two tags differ and at least one of them is the interval tag). -/
def isIntervalMix (lt rt : Option FieldTag) : Prop :=
  (lt = some FieldTag.durationTag ∨ rt = some FieldTag.durationTag) ∧ lt ≠ rt

instance (lt rt : Option FieldTag) : Decidable (isIntervalMix lt rt) := by
  unfold isIntervalMix; infer_instance

/- The resolve-time selection of the result node kind from the operand type
   tags and the connector. A generic node is re-tagged to the interval node when
   the operands mix an interval with a non-interval type; otherwise to the
   temporal-difference node when the connector is a difference of two equal
   point-in-time types; otherwise it stays generic. A node that is already one
   of the specialised kinds keeps its kind. This is the deep model of the
   resolve-time selection (refinement.md A1; mapping.md §2/§3). -/
def dispatchKind (selfKind : NodeKind) (conn : Connector)
    (lt rt : Option FieldTag) : NodeKind :=
  if selfKind ≠ NodeKind.combined then selfKind
  else if isIntervalMix lt rt then NodeKind.durationNode
  else if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then NodeKind.temporalNode
  else NodeKind.combined
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveCombined (selfKind : NodeKind) (conn : Connector) (lt : Option FieldTag) (rt : Option FieldTag) return (out : NodeKind)
  ensures out = dispatchKind selfKind conn lt rt
  do
    -- impl-start
    let mut out := selfKind
    if selfKind = NodeKind.combined then
      if isIntervalMix lt rt then
        out := NodeKind.durationNode
      else
        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
          out := NodeKind.temporalNode
        else
          out := NodeKind.combined
    return out
    -- impl-end

prove_correct resolveCombined by
  loom_solve <;> simp_all [dispatchKind]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec structure: postcondition `ensures out = dispatchKind selfKind conn lt rt` pins the method output POINTWISE to the frozen total pure function dispatchKind (impl region is the only mutable region; axioms/pure/pre/post byte-identical, same_spec=True for all 8 attacks). Consequently any impl that VERIFIES is extensionally equal to dispatchKind = the gold resolve-time node-kind selection. There is no room for a verifying-but-wrong impl.

Attacks (all same_spec=True; verified via scripts/lean_verify.sh <f>):
- atk_1 = prepatch skeleton (`out := selfKind; return out`, no selection) -> exit 1 (unsolved goals). PREPATCH BUG REPRODUCED (matches Solution_prepatch.lean / G-DIFF).
- atk_2 partial-domain (temporal branch dropped) -> exit 1.
- atk_3 boundary (temporal branch fires without conn=minus) -> exit 1.
- atk_4 control-flow reorder (temporal checked before interval-mix; semantically equivalent) -> exit 1 (residual goal `¬isIntervalMix rt rt` the prove_correct tactic can't close). This is a false NEGATIVE (fails to verify though behaviorally correct); it does NOT threaten verify⇒correct.
- atk_5 boundary (temporal branch drops lt=rt) -> exit 1.
- atk_6 ungrounded-oracle echo (`out := dispatchKind selfKind conn lt rt`) -> exit 0 VERIFIES. Behaviorally identical to dispatchKind = gold selection; faithful refined patch = gold patch.
- atk_7 boundary (interval-mix drops lt!=rt) -> exit 1.
- atk_8 control-flow-effect (selfKind guard dropped, selection runs on already-specialized nodes) -> exit 1.

Only atk_6 verifies. MANDATORY resolve run executed: materialized atk_6's faithful patch (=gold, behaviorally equal) and ran it through the official harness: `run_resolve('django__django-13128', patch, timeout=1800, retries=1)` -> RESOLVED=True, COMPLETED=True, note='resolved', flaky=False. So the one verifying wrong-impl-slot's faithful patch RESOLVES => no verify⇏correct break.

Positive control (bundle Solution.lean copied verbatim) verifies: lean_verify.sh exit 0.

Refinement.md A-leg audit: NO axioms (axioms region empty; grep finds no `axiom`; G-AX=skip). mapping.md §3 confirms zero A-consumed and zero A-reference legs — the changed operation (resolve-time node-kind selection) is modeled DEEPLY by dispatchKind (the pure region IS the selection), not behind an axiom. All refinement legs are R (A1 NodeKind receiver-class bijection; A2 lt/rt = output_field.get_internal_type() with AttributeError/FieldError->None collapse as R-refined abstracted inputs; A7 observed node kind) or I (A3-A6 transliterated guards). No kind-3 (inexpressible-changed-op) legs. The R/I legs are G-CONF's domain (recorded pass, 100216 inputs, 0 disagreements, seed 13128) — spot-consistent with the bijection in mapping.md §2. Correspondence claims hold: DurationExpression<->durationNode, TemporalSubtraction<->temporalNode, CombinedExpression<->combined; SUB<->minus; datetime_fields set <-> isTemporalTag.

Verdict: SOUND — 8 attacks run, none breaks the spec; the sole verifying impl's materialized faithful patch resolves; positive control verifies; no A-leg defects.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
/- The output-type tag a resolved operand can carry. The four temporal/interval
   tags are distinguished; every other concrete tag (and the "no resolvable
   type" outcome, carried as `none` on the `Option`) collapses to `otherType`,
   since only these four participate in the selection below. -/
inductive FieldTag where
  | dateTag
  | dateTimeTag
  | timeTag
  | durationTag
  | otherType
  deriving DecidableEq, Inhabited

/- The binary connector joining the two operands. Only the difference connector
   participates in the temporal branch; every other connector behaves the same
   for the selection. -/
inductive Connector where
  | plus
  | minus
  deriving DecidableEq, Inhabited

/- The node kind of a binary expression. `combined` is the generic node; the
   other two are the specialised interval / temporal-difference nodes. -/
inductive NodeKind where
  | combined
  | durationNode
  | temporalNode
  deriving DecidableEq, Inhabited

/- The three tags whose pairwise difference denotes a point-in-time difference. -/
def isTemporalTag (t : Option FieldTag) : Prop :=
  t = some FieldTag.dateTag ∨ t = some FieldTag.dateTimeTag ∨ t = some FieldTag.timeTag

instance (t : Option FieldTag) : Decidable (isTemporalTag t) := by
  unfold isTemporalTag; infer_instance

/- The interval-mix predicate: exactly one operand carries the interval tag (the
   two tags differ and at least one of them is the interval tag). -/
def isIntervalMix (lt rt : Option FieldTag) : Prop :=
  (lt = some FieldTag.durationTag ∨ rt = some FieldTag.durationTag) ∧ lt ≠ rt

instance (lt rt : Option FieldTag) : Decidable (isIntervalMix lt rt) := by
  unfold isIntervalMix; infer_instance

/- The resolve-time selection of the result node kind from the operand type
   tags and the connector. A generic node is re-tagged to the interval node when
   the operands mix an interval with a non-interval type; otherwise to the
   temporal-difference node when the connector is a difference of two equal
   point-in-time types; otherwise it stays generic. A node that is already one
   of the specialised kinds keeps its kind. This is the deep model of the
   resolve-time selection (refinement.md A1; mapping.md §2/§3). -/
def dispatchKind (selfKind : NodeKind) (conn : Connector)
    (lt rt : Option FieldTag) : NodeKind :=
  if selfKind ≠ NodeKind.combined then selfKind
  else if isIntervalMix lt rt then NodeKind.durationNode
  else if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then NodeKind.temporalNode
  else NodeKind.combined
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveCombined (selfKind : NodeKind) (conn : Connector) (lt : Option FieldTag) (rt : Option FieldTag) return (out : NodeKind)
  ensures out = dispatchKind selfKind conn lt rt
  do
    -- impl-start
    let mut out := selfKind
    if selfKind = NodeKind.combined then
      if isIntervalMix lt rt then
        out := NodeKind.durationNode
      else
        if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
          out := NodeKind.temporalNode
        else
          out := NodeKind.combined
    return out
    -- impl-end

prove_correct resolveCombined by
  loom_solve <;> simp_all [dispatchKind]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec structure: postcondition `ensures out = dispatchKind selfKind conn lt rt` pins the method output POINTWISE to the frozen total pure function dispatchKind (impl region is the only mutable region; axioms/pure/pre/post byte-identical, same_spec=True for all 8 attacks). Consequently any impl that VERIFIES is extensionally equal to dispatchKind = the gold resolve-time node-kind selection. There is no room for a verifying-but-wrong impl.

Attacks (all same_spec=True; verified via scripts/lean_verify.sh <f>):
- atk_1 = prepatch skeleton (`out := selfKind; return out`, no selection) -> exit 1 (unsolved goals). PREPATCH BUG REPRODUCED (matches Solution_prepatch.lean / G-DIFF).
- atk_2 partial-domain (temporal branch dropped) -> exit 1.
- atk_3 boundary (temporal branch fires without conn=minus) -> exit 1.
- atk_4 control-flow reorder (temporal checked before interval-mix; semantically equivalent) -> exit 1 (residual goal `¬isIntervalMix rt rt` the prove_correct tactic can't close). This is a false NEGATIVE (fails to verify though behaviorally correct); it does NOT threaten verify⇒correct.
- atk_5 boundary (temporal branch drops lt=rt) -> exit 1.
- atk_6 ungrounded-oracle echo (`out := dispatchKind selfKind conn lt rt`) -> exit 0 VERIFIES. Behaviorally identical to dispatchKind = gold selection; faithful refined patch = gold patch.
- atk_7 boundary (interval-mix drops lt!=rt) -> exit 1.
- atk_8 control-flow-effect (selfKind guard dropped, selection runs on already-specialized nodes) -> exit 1.

Only atk_6 verifies. MANDATORY resolve run executed: materialized atk_6's faithful patch (=gold, behaviorally equal) and ran it through the official harness: `run_resolve('django__django-13128', patch, timeout=1800, retries=1)` -> RESOLVED=True, COMPLETED=True, note='resolved', flaky=False. So the one verifying wrong-impl-slot's faithful patch RESOLVES => no verify⇏correct break.

Positive control (bundle Solution.lean copied verbatim) verifies: lean_verify.sh exit 0.

Refinement.md A-leg audit: NO axioms (axioms region empty; grep finds no `axiom`; G-AX=skip). mapping.md §3 confirms zero A-consumed and zero A-reference legs — the changed operation (resolve-time node-kind selection) is modeled DEEPLY by dispatchKind (the pure region IS the selection), not behind an axiom. All refinement legs are R (A1 NodeKind receiver-class bijection; A2 lt/rt = output_field.get_internal_type() with AttributeError/FieldError->None collapse as R-refined abstracted inputs; A7 observed node kind) or I (A3-A6 transliterated guards). No kind-3 (inexpressible-changed-op) legs. The R/I legs are G-CONF's domain (recorded pass, 100216 inputs, 0 disagreements, seed 13128) — spot-consistent with the bijection in mapping.md §2. Correspondence claims hold: DurationExpression<->durationNode, TemporalSubtraction<->temporalNode, CombinedExpression<->combined; SUB<->minus; datetime_fields set <-> isTemporalTag.

Verdict: SOUND — 8 attacks run, none breaks the spec; the sole verifying impl's materialized faithful patch resolves; positive control verifies; no A-leg defects.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-13128 velvet bundle. Modeled function: CombinedExpression.resolve_expression (expressions.py:476), deep model dispatchKind, observed as the selected result node class (combined/durationNode/temporalNode).

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True — spec region (imports/axioms/pure/pre/post + method signature+ensures) is byte-identical between the verifying and prepatch twins; the only difference is the impl-start..impl-end body. Spec region is genuinely frozen.
2. Solution.lean elaborates clean under lean_verify.sh (exit 0), so the impl provably satisfies `out = dispatchKind selfKind conn lt rt`.
3. Gold patch (from dataset) confirms the modeled logic: (a) guard `not isinstance(self,(DurationExpression,TemporalSubtraction))` <-> `selfKind != combined => out = selfKind` (A3); (b) `'DurationField' in {lhs_type,rhs_type} and lhs_type!=rhs_type -> DurationExpression` <-> isIntervalMix -> durationNode (A4); (c) `connector==SUB and lhs_type in {DateField,DateTimeField,TimeField} and lhs_type==rhs_type -> TemporalSubtraction` <-> conn=minus and isTemporalTag lt and lt=rt -> temporalNode (A5); (d) fall-through -> combined (A6). Branch ORDER (duration-mix before temporal-diff) matches gold exactly.
4. DIFFERENTIAL EXECUTION against the REAL patched callee: ran the shadow (dispatchKind transliteration) vs the actual patched django.db.models.expressions.CombinedExpression.resolve_expression (patch already applied) over the full abstract product (3 kinds x 2 connectors x 6 tags x 6 tags = 216 boundary) + 100000 fuzzed configs (seed 13128). Result: 100216 inputs checked, 0 disagreements. The recursion abstraction is sound because constructing DurationExpression/TemporalSubtraction and re-resolving hits the isinstance guard and keeps its kind (A7), which the oracle exercises for real.

Abstraction-boundary review (all faithful, none over-constraining):
- Connector collapse (plus = all non-SUB): temporal branch requires SUB; duration branch is connector-independent, so every non-SUB connector is observationally identical to '+'. No repo connector value diverges.
- otherType/none collapse: no other get_internal_type() string equals the four named tags; the FieldError/AttributeError->None outcome is carried as `none` and only ever participates as a non-matching value. Correct.
- isTemporalTag checks only lt: sound because the temporal branch also requires lt=rt, so rt's tag is pinned equal.

No input was found on which the modeled function disagrees with the real callee. The spec is exactly as strong as the gold behavior on the observable (selected node kind). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (hard_failures=[]) and independent review confirms it. same_spec(Solution, Solution_prepatch)=True, so the consumer spec view is the genuine frozen spec region. Spec view scanned for every gold-edit-distinctive token: NONE present — no DurationExpression, TemporalSubtraction, resolve_expression, as_sql, output_field, get_internal_type, isinstance, no field-type string literals (DateField/DateTimeField/TimeField/DurationField), no 'expressions.py'/module path, no diff markers, no def/class symbol collision (distinctive patched symbols as_sql/compile/set_source_expressions are absent). Model is fully abstracted into neutral carriers (FieldTag, Connector, NodeKind, dispatchKind); comments describe selection behavior without naming the edit or narrating a bug/fix (no L3 narration hits). The public problem_statement already reveals the temporal-subtraction / mixed DateTimeField+DurationField / FieldError context, so the field-type concepts modeled are derivable from public info, not leaked. The only view token matching a common word was 'connector' (generic English, not a patched symbol). Bundle is not relaxed (no RELAXED_LEAKAGE.md, relaxed_leakage flag unset). Spec does not reveal the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
