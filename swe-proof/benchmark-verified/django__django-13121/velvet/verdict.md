# P2 adversarial audit — django__django-13121

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `out = dispatchNode native conn lt rt` is a total, unconditional exact-equality over all 2·2·6·6 input configurations, so it admits no behaviourally-wrong same-spec impl. Every wrong impl attempted failed to verify; the only verifying candidate (atk5_echo) is behaviourally correct and its faithful patch resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -110,8 +110,16 @@
   ensures out = dispatchNode native conn lt rt
   do
     -- impl-start
+    -- Pre-image skeleton: the interval branch fires whenever the backend lacks a
+    -- native interval type AND at least one operand carries the interval tag,
+    -- WITHOUT requiring the two operand tags to differ. Consequently two
+    -- interval-typed operands (e.g. an interval column summed with an interval
+    -- literal) are routed to the interval renderer instead of the generic
+    -- renderer. The frozen spec (dispatchNode / isIntervalMix) requires that
+    -- two equal interval tags fall through to the generic renderer, so
+    -- prove_correct MUST fail on that clause.
     let mut out := NodeKind.combined
-    if native = false ∧ isIntervalMix lt rt then
+    if native = false ∧ (lt = some FieldTag.durationTag ∨ rt = some FieldTag.durationTag) then
       out := NodeKind.durationNode
     else
       if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
```

Attack 2 — `atk1.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -110,14 +110,7 @@
   ensures out = dispatchNode native conn lt rt
   do
     -- impl-start
-    let mut out := NodeKind.combined
-    if native = false ∧ isIntervalMix lt rt then
-      out := NodeKind.durationNode
-    else
-      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
-        out := NodeKind.temporalNode
-      else
-        out := NodeKind.combined
+    let out := NodeKind.combined
     return out
     -- impl-end
 
```

Attack 3 — `atk2.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -114,7 +114,7 @@
     if native = false ∧ isIntervalMix lt rt then
       out := NodeKind.durationNode
     else
-      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
+      if conn = Connector.plus ∧ isTemporalTag lt ∧ lt = rt then
         out := NodeKind.temporalNode
       else
         out := NodeKind.combined
```

Attack 4 — `atk3.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -111,7 +111,7 @@
   do
     -- impl-start
     let mut out := NodeKind.combined
-    if native = false ∧ isIntervalMix lt rt then
+    if native = false ∧ (lt = some FieldTag.durationTag ∧ rt = some FieldTag.durationTag) then
       out := NodeKind.durationNode
     else
       if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
```

Attack 5 — `atk4.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -111,7 +111,7 @@
   do
     -- impl-start
     let mut out := NodeKind.combined
-    if native = false ∧ isIntervalMix lt rt then
+    if isIntervalMix lt rt then
       out := NodeKind.durationNode
     else
       if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
```

Attack 6 — `atk5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -110,14 +110,7 @@
   ensures out = dispatchNode native conn lt rt
   do
     -- impl-start
-    let mut out := NodeKind.combined
-    if native = false ∧ isIntervalMix lt rt then
-      out := NodeKind.durationNode
-    else
-      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
-        out := NodeKind.temporalNode
-      else
-        out := NodeKind.combined
+    let out := dispatchNode native conn lt rt
     return out
     -- impl-end
 
```

Attack 7 — `atk6.lean` → rejected (same spec, does not verify — good)

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
 /- No unchanged callee is axiomatized for this bundle. The behaviour under spec
@@ -114,10 +114,7 @@
     if native = false ∧ isIntervalMix lt rt then
       out := NodeKind.durationNode
     else
-      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
-        out := NodeKind.temporalNode
-      else
-        out := NodeKind.combined
+      out := NodeKind.temporalNode
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
/- No unchanged callee is axiomatized for this bundle. The behaviour under spec
   is a pure decision over the resolved output-type tags of two operands, the
   joining connector, and whether the backend exposes a native interval type.
   The downstream renderers reached on each branch (the generic combine, the
   interval renderer, the point-in-time-difference renderer) are a shared
   continuation reached once a renderer is chosen, so nothing about them is
   assumed: no consumed axiom, no deep-model reference to a foreign callee. -/
-- axioms-end

-- pure-start
/- The resolved output-type tag an operand can carry. The four temporal/interval
   tags are distinguished; every other concrete tag collapses to `otherType`
   (only these four ever participate in the selection below). An operand whose
   output type cannot be resolved is carried as `none` on the surrounding
   `Option`. -/
inductive FieldTag where
  | dateTag
  | dateTimeTag
  | timeTag
  | durationTag
  | otherType
  deriving DecidableEq, Inhabited

/- The binary connector joining the two operands. Only the difference connector
   participates in the point-in-time-difference branch; every other connector is
   indistinguishable for this selection, so they all collapse to `plus`. -/
inductive Connector where
  | plus
  | minus
  deriving DecidableEq, Inhabited

/- Which renderer is selected for a binary arithmetic node. `combined` is the
   generic renderer; the other two are the specialised interval renderer and the
   point-in-time-difference renderer. -/
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

/- The interval-mix predicate: the operands MIX an interval-typed operand with a
   differently-typed one — at least one operand carries the interval tag AND the
   two tags differ. The key consequence is that two interval-typed operands do
   NOT mix (their tags are equal), so a sum/difference of two intervals is left
   to the generic renderer, not the interval renderer. -/
def isIntervalMix (lt rt : Option FieldTag) : Prop :=
  (lt = some FieldTag.durationTag ∨ rt = some FieldTag.durationTag) ∧ lt ≠ rt

instance (lt rt : Option FieldTag) : Decidable (isIntervalMix lt rt) := by
  unfold isIntervalMix; infer_instance

/- The renderer selected for a generic binary arithmetic node, from the backend
   capability, the connector, and the two operand type tags.

   * When the backend has no native interval type AND the operands mix an
     interval with a non-interval operand, the interval renderer is selected.
     Two interval-typed operands do NOT mix, so they fall through to the generic
     renderer rather than the interval renderer.
   * Otherwise, when the connector is a difference of two equal point-in-time
     types, the point-in-time-difference renderer is selected.
   * Otherwise the generic renderer is selected.

   `native = true` (a backend with a native interval type) disables the first
   branch entirely. This is the deep model of the selection (refinement.md §A;
   mapping.md §2/§3). -/
def dispatchNode (native : Bool) (conn : Connector)
    (lt rt : Option FieldTag) : NodeKind :=
  if native = false ∧ isIntervalMix lt rt then NodeKind.durationNode
  else if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then NodeKind.temporalNode
  else NodeKind.combined
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the renderer for a generic binary arithmetic node. All four inputs are
   read-only and unchanged by the selection (none is `mut`): `native` reports the
   backend's native-interval capability; `conn` is the connector; `lt`/`rt` are
   the resolved output-type tags of the left and right operands (`none` when an
   operand has no resolvable output type).

   Desired behaviour: the interval renderer is chosen only when the backend lacks
   a native interval type and the operands MIX an interval-typed operand with a
   differently-typed operand — so two interval-typed operands are summed by the
   generic renderer; the point-in-time-difference renderer is chosen for a
   difference of two equal point-in-time types; otherwise the generic renderer is
   chosen. The selected renderer is the one that finally produces the node's SQL,
   so it fully determines the rendering. -/
method selectRenderer (native : Bool) (conn : Connector)
    (lt : Option FieldTag) (rt : Option FieldTag) return (out : NodeKind)
  ensures out = dispatchNode native conn lt rt
  do
    -- impl-start
    let mut out := NodeKind.combined
    if native = false ∧ isIntervalMix lt rt then
      out := NodeKind.durationNode
    else
      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
        out := NodeKind.temporalNode
      else
        out := NodeKind.combined
    return out
    -- impl-end

prove_correct selectRenderer by
  loom_solve <;> simp only [dispatchNode] <;> split_ifs <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier: python; scripts/lean_verify.sh via `bash scripts/lean_verify.sh <f>`.

SAME-SPEC: all 7 attacks + positive_control return same_spec=True (velvet backend, markers.same_spec) — impl region is the ONLY edit; axioms/pure/pre/post byte-identical.

positive_control.lean = 0 (VERIFIES) ✓ positive control sound.
- atk_prepatch.lean = 1 (FAILS) — prepatch bug reproduced: interval branch fires on `lt=durationTag ∨ rt=durationTag` with no `lt≠rt`, so both-durationTag mis-routes to durationNode; prove_correct unsolved goals at line 132. prepatch_reproduced=true.
- atk1.lean (partial-domain: always `combined`) = 1 FAIL.
- atk2.lean (control-flow: temporal branch keyed on `plus` not `minus`) = 1 FAIL.
- atk3.lean (boundary: interval branch requires BOTH operands durationTag) = 1 FAIL.
- atk4.lean (ungrounded: interval branch drops the `native=false` guard) = 1 FAIL.
- atk6.lean (control-flow-effect: else-branch collapses to `temporalNode`) = 1 FAIL.
- atk5_echo.lean (ungrounded-oracle echo: `let out := dispatchNode native conn lt rt`) = 0 VERIFIES.

RESOLVE (mandatory for every verifying impl): atk5_echo returns dispatchNode verbatim ⇒ behaviourally CORRECT ⇒ its faithful refined patch is the gold patch (refinement.md: patch.diff is gold verbatim). Ran run_resolve('django__django-13121', gold_patch, timeout=1800) via swebench_unified.harness → ResolveResult.resolved=True, ran=True, msg='resolved'. This is the fixed G-PANEL-1/G-EQ policy (a resolving echo is NOT a weakness). No verifying wrong impl has a non-resolving faithful patch ⇒ no verify⇏correct gap.

REFINEMENT AUDIT: refinement.md legs A1–A5 + §B all R or I; NO kind-3, NO axioms (mapping.md §3 confirms no consumed axiom / no A-reference — G-AX has nothing to check). The changed dispatch is modeled DEEPLY (dispatchNode/isIntervalMix/isTemporalTag), not hidden behind a callee contract. Model↔patch correspondence verified: A2 isIntervalMix ≡ post-patch `'DurationField' ∈ {lt,rt} ∧ lt≠rt` (incl. the new lt≠rt conjunct); A3 ≡ `connector==SUB and lhs_type in datetime_fields and lhs_type==rhs_type`; A4 fall-through ≡ generic combine. Type bijection (mapping.md §2) sound: FieldTag/Connector/NodeKind ↔ get_internal_type()/connector/renderer-class, none↔FieldError arm.

WHY SOUND: postcondition is a total exact-equality with no preconditions, so verify ⇒ impl == gold dispatch on every configuration ⇒ correct. ≥5 distinct wrong impls attempted (6 + prepatch), none broke it; the sole verifying candidate is correct and resolves. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen postcondition `out = dispatchNode native conn lt rt` is a total, unconditional exact-equality over all 2·2·6·6 input configurations, so it admits no behaviourally-wrong same-spec impl. Every wrong impl attempted failed to verify; the only verifying candidate (atk5_echo) is behaviourally correct and its faithful patch resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behaviour under spec
   is a pure decision over the resolved output-type tags of two operands, the
   joining connector, and whether the backend exposes a native interval type.
   The downstream renderers reached on each branch (the generic combine, the
   interval renderer, the point-in-time-difference renderer) are a shared
   continuation reached once a renderer is chosen, so nothing about them is
   assumed: no consumed axiom, no deep-model reference to a foreign callee. -/
-- axioms-end

-- pure-start
/- The resolved output-type tag an operand can carry. The four temporal/interval
   tags are distinguished; every other concrete tag collapses to `otherType`
   (only these four ever participate in the selection below). An operand whose
   output type cannot be resolved is carried as `none` on the surrounding
   `Option`. -/
inductive FieldTag where
  | dateTag
  | dateTimeTag
  | timeTag
  | durationTag
  | otherType
  deriving DecidableEq, Inhabited

/- The binary connector joining the two operands. Only the difference connector
   participates in the point-in-time-difference branch; every other connector is
   indistinguishable for this selection, so they all collapse to `plus`. -/
inductive Connector where
  | plus
  | minus
  deriving DecidableEq, Inhabited

/- Which renderer is selected for a binary arithmetic node. `combined` is the
   generic renderer; the other two are the specialised interval renderer and the
   point-in-time-difference renderer. -/
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

/- The interval-mix predicate: the operands MIX an interval-typed operand with a
   differently-typed one — at least one operand carries the interval tag AND the
   two tags differ. The key consequence is that two interval-typed operands do
   NOT mix (their tags are equal), so a sum/difference of two intervals is left
   to the generic renderer, not the interval renderer. -/
def isIntervalMix (lt rt : Option FieldTag) : Prop :=
  (lt = some FieldTag.durationTag ∨ rt = some FieldTag.durationTag) ∧ lt ≠ rt

instance (lt rt : Option FieldTag) : Decidable (isIntervalMix lt rt) := by
  unfold isIntervalMix; infer_instance

/- The renderer selected for a generic binary arithmetic node, from the backend
   capability, the connector, and the two operand type tags.

   * When the backend has no native interval type AND the operands mix an
     interval with a non-interval operand, the interval renderer is selected.
     Two interval-typed operands do NOT mix, so they fall through to the generic
     renderer rather than the interval renderer.
   * Otherwise, when the connector is a difference of two equal point-in-time
     types, the point-in-time-difference renderer is selected.
   * Otherwise the generic renderer is selected.

   `native = true` (a backend with a native interval type) disables the first
   branch entirely. This is the deep model of the selection (refinement.md §A;
   mapping.md §2/§3). -/
def dispatchNode (native : Bool) (conn : Connector)
    (lt rt : Option FieldTag) : NodeKind :=
  if native = false ∧ isIntervalMix lt rt then NodeKind.durationNode
  else if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then NodeKind.temporalNode
  else NodeKind.combined
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the renderer for a generic binary arithmetic node. All four inputs are
   read-only and unchanged by the selection (none is `mut`): `native` reports the
   backend's native-interval capability; `conn` is the connector; `lt`/`rt` are
   the resolved output-type tags of the left and right operands (`none` when an
   operand has no resolvable output type).

   Desired behaviour: the interval renderer is chosen only when the backend lacks
   a native interval type and the operands MIX an interval-typed operand with a
   differently-typed operand — so two interval-typed operands are summed by the
   generic renderer; the point-in-time-difference renderer is chosen for a
   difference of two equal point-in-time types; otherwise the generic renderer is
   chosen. The selected renderer is the one that finally produces the node's SQL,
   so it fully determines the rendering. -/
method selectRenderer (native : Bool) (conn : Connector)
    (lt : Option FieldTag) (rt : Option FieldTag) return (out : NodeKind)
  ensures out = dispatchNode native conn lt rt
  do
    -- impl-start
    let mut out := NodeKind.combined
    if native = false ∧ isIntervalMix lt rt then
      out := NodeKind.durationNode
    else
      if conn = Connector.minus ∧ isTemporalTag lt ∧ lt = rt then
        out := NodeKind.temporalNode
      else
        out := NodeKind.combined
    return out
    -- impl-end

prove_correct selectRenderer by
  loom_solve <;> simp only [dispatchNode] <;> split_ifs <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier: python; scripts/lean_verify.sh via `bash scripts/lean_verify.sh <f>`.

SAME-SPEC: all 7 attacks + positive_control return same_spec=True (velvet backend, markers.same_spec) — impl region is the ONLY edit; axioms/pure/pre/post byte-identical.

positive_control.lean = 0 (VERIFIES) ✓ positive control sound.
- atk_prepatch.lean = 1 (FAILS) — prepatch bug reproduced: interval branch fires on `lt=durationTag ∨ rt=durationTag` with no `lt≠rt`, so both-durationTag mis-routes to durationNode; prove_correct unsolved goals at line 132. prepatch_reproduced=true.
- atk1.lean (partial-domain: always `combined`) = 1 FAIL.
- atk2.lean (control-flow: temporal branch keyed on `plus` not `minus`) = 1 FAIL.
- atk3.lean (boundary: interval branch requires BOTH operands durationTag) = 1 FAIL.
- atk4.lean (ungrounded: interval branch drops the `native=false` guard) = 1 FAIL.
- atk6.lean (control-flow-effect: else-branch collapses to `temporalNode`) = 1 FAIL.
- atk5_echo.lean (ungrounded-oracle echo: `let out := dispatchNode native conn lt rt`) = 0 VERIFIES.

RESOLVE (mandatory for every verifying impl): atk5_echo returns dispatchNode verbatim ⇒ behaviourally CORRECT ⇒ its faithful refined patch is the gold patch (refinement.md: patch.diff is gold verbatim). Ran run_resolve('django__django-13121', gold_patch, timeout=1800) via swebench_unified.harness → ResolveResult.resolved=True, ran=True, msg='resolved'. This is the fixed G-PANEL-1/G-EQ policy (a resolving echo is NOT a weakness). No verifying wrong impl has a non-resolving faithful patch ⇒ no verify⇏correct gap.

REFINEMENT AUDIT: refinement.md legs A1–A5 + §B all R or I; NO kind-3, NO axioms (mapping.md §3 confirms no consumed axiom / no A-reference — G-AX has nothing to check). The changed dispatch is modeled DEEPLY (dispatchNode/isIntervalMix/isTemporalTag), not hidden behind a callee contract. Model↔patch correspondence verified: A2 isIntervalMix ≡ post-patch `'DurationField' ∈ {lt,rt} ∧ lt≠rt` (incl. the new lt≠rt conjunct); A3 ≡ `connector==SUB and lhs_type in datetime_fields and lhs_type==rhs_type`; A4 fall-through ≡ generic combine. Type bijection (mapping.md §2) sound: FieldTag/Connector/NodeKind ↔ get_internal_type()/connector/renderer-class, none↔FieldError arm.

WHY SOUND: postcondition is a total exact-equality with no preconditions, so verify ⇒ impl == gold dispatch on every configuration ⇒ correct. ≥5 distinct wrong impls attempted (6 + prepatch), none broke it; the sole verifying candidate is correct and resolves. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-13121/velvet. The modeled function selectRenderer (deep model dispatchNode over inputs native:Bool, conn:Connector, lt/rt:Option FieldTag) is checked against the real patched CombinedExpression.as_sql renderer-selection head from patch.diff.

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — spec region (axioms/pure/pre/post + signature + `ensures out = dispatchNode native conn lt rt`) is byte-identical; the prepatch differs only in the elided impl region. Spec view is clean.
2. scripts/lean_verify.sh on Solution.lean → EXIT 0 (gold-faithful impl verifies against the spec).
3. Independent from-scratch transliteration of the PATCHED as_sql control flow (patch.diff L97-108): interval branch `not has_native_duration_field and 'DurationField' in {lhs_type,rhs_type} and lhs_type != rhs_type → DurationExpression`; temporal branch `connector==SUB and lhs_type in {DateField,DateTimeField,TimeField} and lhs_type==rhs_type → TemporalSubtraction`; else generic combine. Compared to the Lean dispatchNode over the FULL abstract product (2·2·6·6 = 144 configs): 0 divergences.

Boundary cases specifically confirmed faithful:
- Both operands durationTag (native=False): real → lt==rt so NOT interval-mix → combined; model isIntervalMix requires lt≠rt → combined. Matches (this is the whole point of the fix).
- None/FieldError operand tags (Option none): 'DurationField' not in {None,...} unless the other is duration with None≠duration handled; temporal branch None not in datetime_fields → combined. Model matches (none carrier).
- native=True disables interval branch on both sides.
- Temporal branch post-patch correctly dropped the pre-patch `lhs_output and rhs_output` guard; model checks only lt (lt==rt subsumes rt), observationally identical since a None lt is not in the temporal set.

The abstraction is not too strong: it does not over-constrain relative to the real callee, and it does not omit a reachable behavior. The connector-collapse (all non-SUB → plus) and tag-collapse (all non-{date,datetime,time,duration} → otherType) are sound because only SUB and those four tags participate in any branch. G-CONF (100144 inputs, seed 13121) independently records 0 disagreements against the in-container patched as_sql; conformance_check.py errors here only because django is not importable outside the container (expected). No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction) for django__django-13121 velvet. Method: computed the actual consumer spec view via swebench_unified.markers.spec_view with the velvet backend and ran leakage.screen against the frozen instance row. Findings: (1) same_spec(Solution.lean, Solution_prepatch.lean)=True — the spec region (imports/set_options, axioms comment, pure region [FieldTag/Connector/NodeKind inductives, isTemporalTag, isIntervalMix, dispatchNode], empty pre/post, selectRenderer signature+ensures) is byte-identical; only the elided impl region differs (prepatch drops the `lt ≠ rt` conjunct). So the spec under judgment is genuinely frozen. (2) Mechanical screen PASSES with zero hard failures: no diff markers, no gold-patch line reproduced (>=8-char normalized), no patched file path/module path in the view, no spec-view identifier embedding any patched repo symbol (as_sql, Combinable, DurationValue, date_interval_sql, resolve_expression, etc.), no patched symbol named in a comment/docstring, no bug/fix narration tokens. (3) Semantic gold-reconstruction (the part the lexical screen can miss): the public problem_statement already discloses the exact failing scenario — F('estimated_time') + timedelta, two DurationField operands, failing on SQLite/MySQL (native=False) with decimal.ConversionSyntax. The spec's discriminating content — the `lt ≠ rt` conjunct forcing two equal interval tags to the generic renderer — is directly implied by that public failing case, not information beyond it. All comments describe behavior in abstracted terms (interval renderer / generic renderer / point-in-time-difference renderer / native interval type) and never name the Django repo symbols under change (CombinedExpression.as_sql, DurationExpression, TemporalSubtraction, has_native_duration_field); the temporal-branch structure shown is unchanged context, not the edit. No line of the spec view leaks the gold edit beyond the public problem_statement (hints_text excluded from consideration). meta.json G-LEAK=pass 'spec view clean'; bundle is NOT relaxed (no RELAXED_LEAKAGE.md, relaxed_leakage flag unset), so no deferral needed. Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
