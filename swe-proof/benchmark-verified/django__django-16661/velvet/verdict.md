# P2 adversarial audit — django__django-16661

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,8 +85,6 @@
   ensures out = keepMask hops
   do
     -- impl-start
-    -- Backward scan over the walked segments, deciding the descent flag of each
-    -- with the genuine-descent rule. `hops` is read-only (not mutated).
     let mut result : List Bool := []
     let mut i := hops.length
     while i > 0
@@ -96,7 +94,8 @@
       decreasing i
     do
       let h := hops[i - 1]!
-      result := keepSegment h :: result
+      let keep : Bool := h.isFirst || (h.priorIsRelation && !h.targetOfPrior)
+      result := keep :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,8 +85,6 @@
   ensures out = keepMask hops
   do
     -- impl-start
-    -- Backward scan over the walked segments, deciding the descent flag of each
-    -- with the genuine-descent rule. `hops` is read-only (not mutated).
     let mut result : List Bool := []
     let mut i := hops.length
     while i > 0
@@ -96,7 +94,8 @@
       decreasing i
     do
       let h := hops[i - 1]!
-      result := keepSegment h :: result
+      let keep : Bool := h.isFirst || (h.priorIsRelation && !h.concreteParentLink && !h.redundantLocalValue)
+      result := keep :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,8 +85,6 @@
   ensures out = keepMask hops
   do
     -- impl-start
-    -- Backward scan over the walked segments, deciding the descent flag of each
-    -- with the genuine-descent rule. `hops` is read-only (not mutated).
     let mut result : List Bool := []
     let mut i := hops.length
     while i > 0
@@ -96,7 +94,8 @@
       decreasing i
     do
       let h := hops[i - 1]!
-      result := keepSegment h :: result
+      let keep : Bool := h.isFirst
+      result := keep :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,8 +85,6 @@
   ensures out = keepMask hops
   do
     -- impl-start
-    -- Backward scan over the walked segments, deciding the descent flag of each
-    -- with the genuine-descent rule. `hops` is read-only (not mutated).
     let mut result : List Bool := []
     let mut i := hops.length
     while i > 0
@@ -96,7 +94,8 @@
       decreasing i
     do
       let h := hops[i - 1]!
-      result := keepSegment h :: result
+      let keep : Bool := h.isFirst || (h.priorIsRelation && h.concreteParentLink && !h.redundantLocalValue && (!h.hasRedundantLocalValue || !h.priorAlreadyCovers))
+      result := keep :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,8 +85,6 @@
   ensures out = keepMask hops
   do
     -- impl-start
-    -- Backward scan over the walked segments, deciding the descent flag of each
-    -- with the genuine-descent rule. `hops` is read-only (not mutated).
     let mut result : List Bool := []
     let mut i := hops.length
     while i > 0
@@ -95,7 +93,7 @@
       done_with i = 0
       decreasing i
     do
-      let h := hops[i - 1]!
+      let h := hops[i]!
       result := keepSegment h :: result
       i := i - 1
     return result
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,8 +85,6 @@
   ensures out = keepMask hops
   do
     -- impl-start
-    -- Backward scan over the walked segments, deciding the descent flag of each
-    -- with the genuine-descent rule. `hops` is read-only (not mutated).
     let mut result : List Bool := []
     let mut i := hops.length
     while i > 0
@@ -96,7 +94,7 @@
       decreasing i
     do
       let h := hops[i - 1]!
-      result := keepSegment h :: result
+      result := result ++ [keepSegment h]
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,8 +85,6 @@
   ensures out = keepMask hops
   do
     -- impl-start
-    -- Backward scan over the walked segments, deciding the descent flag of each
-    -- with the genuine-descent rule. `hops` is read-only (not mutated).
     let mut result : List Bool := []
     let mut i := hops.length
     while i > 0
@@ -96,7 +94,8 @@
       decreasing i
     do
       let h := hops[i - 1]!
-      result := keepSegment h :: result
+      let keep : Bool := h.isFirst || (!h.concreteParentLink && !h.redundantLocalValue && (!h.hasRedundantLocalValue || !h.priorAlreadyCovers))
+      result := keep :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-segment facts the step decision consults are
--  read-only per-hop inputs (tagged R in refinement.md), not contracts the proof
--  consumes, so no axiom and no axiom_check are needed. Their repo provenance is
--  in mapping.md. Only the way these facts are COMBINED into the keep decision is
--  modeled below.)
-- axioms-end

-- pure-start
/- The per-segment facts a step of the lookup path exposes, as it is walked one
   hop at a time. Each field is a single read-only boolean about the segment; the
   repo introspection each abstracts is recorded in mapping.md. They are exposed
   here only so the keep decision can be stated structurally.

   * `isFirst`            — this is the first segment of the path (no prior step
                            yet).
   * `priorIsRelation`    — the prior step entered a further record.
   * `concreteParentLink` — the segment merely re-reaches a concrete ancestor
                            record (the PS concrete-inheritance shortcut case).
   * `redundantLocalValue`     — an opaque per-segment redundancy flag (A).
   * `hasRedundantLocalValue`  — an opaque per-record flag enabling clause (C) (B).
   * `priorAlreadyCovers`      — an opaque per-segment redundancy flag (C).
   * `targetOfPrior`      — an alternative, coarser redundancy flag (consulted
                            only by the pre-image skeleton, not by the rule
                            below). -/
structure Hop where
  isFirst               : Bool
  priorIsRelation       : Bool
  concreteParentLink    : Bool
  redundantLocalValue   : Bool
  hasRedundantLocalValue: Bool
  priorAlreadyCovers    : Bool
  targetOfPrior         : Bool
deriving DecidableEq, Inhabited, Repr

/- Whether a single segment is RECORDED as a real step of the lookup path.

   A segment is recorded exactly when it is the first segment, OR the prior step
   entered a further record and the segment is NOT locally redundant. The segment
   is locally redundant precisely when ANY of three opaque conditions holds:
   `concreteParentLink` (the concrete-inheritance shortcut case from the PS),
   `redundantLocalValue`, or (`hasRedundantLocalValue` AND `priorAlreadyCovers`).
   Otherwise the segment is recorded. The repo meaning of each flag is in
   mapping.md; here only their Boolean combination is pinned. -/
def keepSegment (h : Hop) : Bool :=
  h.isFirst ||
  (h.priorIsRelation
    && !h.concreteParentLink
    && !h.redundantLocalValue
    && (!h.hasRedundantLocalValue || !h.priorAlreadyCovers))

/- The recorded/not-recorded flag of every segment of a walked path: the
   per-segment expansion of the input hops via `keepSegment`. Front-recursive so a
   single unfold is available per loop step (the backward-fold pattern, plan §5.4). -/
def keepMask : List Hop → List Bool
  | []      => []
  | h :: hs => keepSegment h :: keepMask hs

@[grind] lemma keepMask_nil : keepMask [] = [] := rfl
@[grind] lemma keepMask_cons (h : Hop) (hs : List Hop) :
    keepMask (h :: hs) = keepSegment h :: keepMask hs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide, for each segment of an already-walked lookup path, whether that
   segment is recorded as a real step. The frozen guarantee is that the result is
   exactly the per-segment expansion `keepMask hops`: each flag is the keep
   decision for the corresponding hop, computed by the rule in `keepSegment`.
   `hops` is read-only — the method builds and returns a fresh flag list and
   never mutates its input. -/
method keptSegments (hops : List Hop) return (out : List Bool)
  ensures out = keepMask hops
  do
    -- impl-start
    -- Backward scan over the walked segments, deciding the descent flag of each
    -- with the genuine-descent rule. `hops` is read-only (not mutated).
    let mut result : List Bool := []
    let mut i := hops.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ hops.length
      invariant result = keepMask (hops.drop i)
      done_with i = 0
      decreasing i
    do
      let h := hops[i - 1]!
      result := keepSegment h :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer hop exposes the segment at `i-1`
   on the front, so `keepMask` peels one flag. The single goal `loom_solve`
   leaves for the loop body. -/
lemma keepMask_drop_step (hops : List Hop) (i : Nat)
    (hi : 0 < i) (hle : i ≤ hops.length) :
    keepMask (hops.drop (i - 1))
      = keepSegment hops[i - 1]! :: keepMask (hops.drop i) := by
  have hlt : i - 1 < hops.length := by omega
  have hcons : hops.drop (i - 1) = hops[i - 1]! :: hops.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keepMask_cons]

prove_correct keptSegments by
  loom_solve
  rw [keepMask_drop_step hops i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins output totally: `method keptSegments (hops : List Hop) return (out : List Bool) ensures out = keepMask hops`. keepMask/keepSegment live in the (non-elided) `pure` region, so they are frozen in the spec signature; same_spec compares the spec view (impl region + prove_correct body elided). The postcondition is therefore a TOTAL FUNCTIONAL EQUALITY to the frozen pure model — any verifying impl must produce exactly `keepMask hops`. This structurally forecloses a verify⇏correct break: no wrong-decision impl can verify, so there is no verifying wrong impl whose faithful refined patch could fail to resolve. patches={} because NO attack verified (nothing to materialize/resolve).

A-LEG AUDIT (refinement.md §B/§C, mapping.md §2/§3): NO axioms and NO A-reference legs — confirmed. axioms region is empty prose only; G-AX has nothing to check. Every Hop field is a read-only per-hop boolean (R) from UNCHANGED Django introspection; the sole changed op (the append guard) is modeled DEEPLY as keepSegment (A7, an I op), not axiomatized.

Model↔patch correspondence verified faithful: gold post-patch guard `not prev_field or (prev_field.is_relation and field not in model._meta.parents.values() and field is not model._meta.auto_field and (model._meta.auto_field is None or part not in getattr(prev_field,'to_fields',[])))` transliterates exactly to `isFirst || (priorIsRelation && !concreteParentLink && !redundantLocalValue && (!hasRedundantLocalValue || !priorAlreadyCovers))` under the mapping.md §2 bijection (isFirst↔not prev_field, priorIsRelation↔is_relation, concreteParentLink↔field in parents.values(), redundantLocalValue↔field is auto_field, hasRedundantLocalValue↔auto_field is not None, priorAlreadyCovers↔part in to_fields; or↔||, and↔&&, not↔!). No kind-3 steps. The backward while-fold (A8) computes the same per-segment stream as the forward append; loop invariant `result = keepMask (hops.drop i)` ties it to the model.

MANDATORY PROTOCOL EXECUTED (all; verifier scripts/lean_verify.sh; same_spec via swebench_unified.markers.same_spec + get_backend('velvet')). same_spec=True for ALL 10 files. Verification (exit 0=verifies, 1=error):
- positive_control.lean (original keepSegment fold): `bash scripts/lean_verify.sh .../positive_control.lean` -> EXIT 0 VERIFIES (sanity).
- atk_altcorrect.lean (equivalent correct impl `return keepMask hops`, prove_correct body adjusted — body is elided so same_spec stays True): EXIT 0 VERIFIES — confirms spec accepts a DIFFERENT-shape correct impl, so failures below are semantic, not shape artifacts.
- atk_1.lean = PREPATCH BUG re-encoded (coarse `isFirst || (priorIsRelation && !targetOfPrior)`): EXIT 1 FAILS — unsolved goals on invariant `result = keepMask (hops.drop i)`. Prepatch reproduced (also prepatch.lean from bundle: EXIT 1).
- atk_2.lean (partial-domain: drop the disjunctive clause): EXIT 1 FAILS.
- atk_3.lean (ungrounded-oracle echo: `keep := isFirst` only): EXIT 1 FAILS.
- atk_4.lean (flipped negation polarity on concreteParentLink): EXIT 1 FAILS.
- atk_5.lean (boundary/off-by-one control-flow: index hops[i]! instead of hops[i-1]!): EXIT 1 FAILS.
- atk_6.lean (control-flow-effect: append at end `result ++ [keepSegment h]` reversing order): EXIT 1 FAILS.
- atk_7.lean (partial-domain: drop the priorIsRelation guard): EXIT 1 FAILS.
All 8 wrong impls fail with genuine `error: unsolved goals` on the postcondition-derived loop invariant (verified via grep of .out logs) — the fully-pinning spec rejecting them semantically, NOT syntax errors. Verifications were run concurrently in background batches of 4.

7 DISTINCT wrong-impl attacks (partial-domain x2, boundary, control-flow-effect, ungrounded-oracle echo, polarity flip, prepatch coarse rule) + prepatch bundle file, exceeding the >=5 requirement; none verifies, so none required a resolve run. No resolve run was NEEDED because the break condition (a verifying wrong impl) never occurred. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-segment facts the step decision consults are
--  read-only per-hop inputs (tagged R in refinement.md), not contracts the proof
--  consumes, so no axiom and no axiom_check are needed. Their repo provenance is
--  in mapping.md. Only the way these facts are COMBINED into the keep decision is
--  modeled below.)
-- axioms-end

-- pure-start
/- The per-segment facts a step of the lookup path exposes, as it is walked one
   hop at a time. Each field is a single read-only boolean about the segment; the
   repo introspection each abstracts is recorded in mapping.md. They are exposed
   here only so the keep decision can be stated structurally.

   * `isFirst`            — this is the first segment of the path (no prior step
                            yet).
   * `priorIsRelation`    — the prior step entered a further record.
   * `concreteParentLink` — the segment merely re-reaches a concrete ancestor
                            record (the PS concrete-inheritance shortcut case).
   * `redundantLocalValue`     — an opaque per-segment redundancy flag (A).
   * `hasRedundantLocalValue`  — an opaque per-record flag enabling clause (C) (B).
   * `priorAlreadyCovers`      — an opaque per-segment redundancy flag (C).
   * `targetOfPrior`      — an alternative, coarser redundancy flag (consulted
                            only by the pre-image skeleton, not by the rule
                            below). -/
structure Hop where
  isFirst               : Bool
  priorIsRelation       : Bool
  concreteParentLink    : Bool
  redundantLocalValue   : Bool
  hasRedundantLocalValue: Bool
  priorAlreadyCovers    : Bool
  targetOfPrior         : Bool
deriving DecidableEq, Inhabited, Repr

/- Whether a single segment is RECORDED as a real step of the lookup path.

   A segment is recorded exactly when it is the first segment, OR the prior step
   entered a further record and the segment is NOT locally redundant. The segment
   is locally redundant precisely when ANY of three opaque conditions holds:
   `concreteParentLink` (the concrete-inheritance shortcut case from the PS),
   `redundantLocalValue`, or (`hasRedundantLocalValue` AND `priorAlreadyCovers`).
   Otherwise the segment is recorded. The repo meaning of each flag is in
   mapping.md; here only their Boolean combination is pinned. -/
def keepSegment (h : Hop) : Bool :=
  h.isFirst ||
  (h.priorIsRelation
    && !h.concreteParentLink
    && !h.redundantLocalValue
    && (!h.hasRedundantLocalValue || !h.priorAlreadyCovers))

/- The recorded/not-recorded flag of every segment of a walked path: the
   per-segment expansion of the input hops via `keepSegment`. Front-recursive so a
   single unfold is available per loop step (the backward-fold pattern, plan §5.4). -/
def keepMask : List Hop → List Bool
  | []      => []
  | h :: hs => keepSegment h :: keepMask hs

@[grind] lemma keepMask_nil : keepMask [] = [] := rfl
@[grind] lemma keepMask_cons (h : Hop) (hs : List Hop) :
    keepMask (h :: hs) = keepSegment h :: keepMask hs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide, for each segment of an already-walked lookup path, whether that
   segment is recorded as a real step. The frozen guarantee is that the result is
   exactly the per-segment expansion `keepMask hops`: each flag is the keep
   decision for the corresponding hop, computed by the rule in `keepSegment`.
   `hops` is read-only — the method builds and returns a fresh flag list and
   never mutates its input. -/
method keptSegments (hops : List Hop) return (out : List Bool)
  ensures out = keepMask hops
  do
    -- impl-start
    -- Backward scan over the walked segments, deciding the descent flag of each
    -- with the genuine-descent rule. `hops` is read-only (not mutated).
    let mut result : List Bool := []
    let mut i := hops.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ hops.length
      invariant result = keepMask (hops.drop i)
      done_with i = 0
      decreasing i
    do
      let h := hops[i - 1]!
      result := keepSegment h :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer hop exposes the segment at `i-1`
   on the front, so `keepMask` peels one flag. The single goal `loom_solve`
   leaves for the loop body. -/
lemma keepMask_drop_step (hops : List Hop) (i : Nat)
    (hi : 0 < i) (hle : i ≤ hops.length) :
    keepMask (hops.drop (i - 1))
      = keepSegment hops[i - 1]! :: keepMask (hops.drop i) := by
  have hlt : i - 1 < hops.length := by omega
  have hcons : hops.drop (i - 1) = hops[i - 1]! :: hops.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keepMask_cons]

prove_correct keptSegments by
  loom_solve
  rw [keepMask_drop_step hops i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins output totally: `method keptSegments (hops : List Hop) return (out : List Bool) ensures out = keepMask hops`. keepMask/keepSegment live in the (non-elided) `pure` region, so they are frozen in the spec signature; same_spec compares the spec view (impl region + prove_correct body elided). The postcondition is therefore a TOTAL FUNCTIONAL EQUALITY to the frozen pure model — any verifying impl must produce exactly `keepMask hops`. This structurally forecloses a verify⇏correct break: no wrong-decision impl can verify, so there is no verifying wrong impl whose faithful refined patch could fail to resolve. patches={} because NO attack verified (nothing to materialize/resolve).

A-LEG AUDIT (refinement.md §B/§C, mapping.md §2/§3): NO axioms and NO A-reference legs — confirmed. axioms region is empty prose only; G-AX has nothing to check. Every Hop field is a read-only per-hop boolean (R) from UNCHANGED Django introspection; the sole changed op (the append guard) is modeled DEEPLY as keepSegment (A7, an I op), not axiomatized.

Model↔patch correspondence verified faithful: gold post-patch guard `not prev_field or (prev_field.is_relation and field not in model._meta.parents.values() and field is not model._meta.auto_field and (model._meta.auto_field is None or part not in getattr(prev_field,'to_fields',[])))` transliterates exactly to `isFirst || (priorIsRelation && !concreteParentLink && !redundantLocalValue && (!hasRedundantLocalValue || !priorAlreadyCovers))` under the mapping.md §2 bijection (isFirst↔not prev_field, priorIsRelation↔is_relation, concreteParentLink↔field in parents.values(), redundantLocalValue↔field is auto_field, hasRedundantLocalValue↔auto_field is not None, priorAlreadyCovers↔part in to_fields; or↔||, and↔&&, not↔!). No kind-3 steps. The backward while-fold (A8) computes the same per-segment stream as the forward append; loop invariant `result = keepMask (hops.drop i)` ties it to the model.

MANDATORY PROTOCOL EXECUTED (all; verifier scripts/lean_verify.sh; same_spec via swebench_unified.markers.same_spec + get_backend('velvet')). same_spec=True for ALL 10 files. Verification (exit 0=verifies, 1=error):
- positive_control.lean (original keepSegment fold): `bash scripts/lean_verify.sh .../positive_control.lean` -> EXIT 0 VERIFIES (sanity).
- atk_altcorrect.lean (equivalent correct impl `return keepMask hops`, prove_correct body adjusted — body is elided so same_spec stays True): EXIT 0 VERIFIES — confirms spec accepts a DIFFERENT-shape correct impl, so failures below are semantic, not shape artifacts.
- atk_1.lean = PREPATCH BUG re-encoded (coarse `isFirst || (priorIsRelation && !targetOfPrior)`): EXIT 1 FAILS — unsolved goals on invariant `result = keepMask (hops.drop i)`. Prepatch reproduced (also prepatch.lean from bundle: EXIT 1).
- atk_2.lean (partial-domain: drop the disjunctive clause): EXIT 1 FAILS.
- atk_3.lean (ungrounded-oracle echo: `keep := isFirst` only): EXIT 1 FAILS.
- atk_4.lean (flipped negation polarity on concreteParentLink): EXIT 1 FAILS.
- atk_5.lean (boundary/off-by-one control-flow: index hops[i]! instead of hops[i-1]!): EXIT 1 FAILS.
- atk_6.lean (control-flow-effect: append at end `result ++ [keepSegment h]` reversing order): EXIT 1 FAILS.
- atk_7.lean (partial-domain: drop the priorIsRelation guard): EXIT 1 FAILS.
All 8 wrong impls fail with genuine `error: unsolved goals` on the postcondition-derived loop invariant (verified via grep of .out logs) — the fully-pinning spec rejecting them semantically, NOT syntax errors. Verifications were run concurrently in background batches of 4.

7 DISTINCT wrong-impl attacks (partial-domain x2, boundary, control-flow-effect, ungrounded-oracle echo, polarity flip, prepatch coarse rule) + prepatch bundle file, exceeding the >=5 requirement; none verifies, so none required a resolve run. No resolve run was NEEDED because the break condition (a verifying wrong impl) never occurred. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift). Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec -> True). Solution.lean verifies (lean_verify.sh exit 0).

The modeled per-segment decision keepSegment is an EXACT Boolean transliteration of the gold-patched guard in django/contrib/admin/options.py:461-471 (base_commit d687febce5868545f99974d2499a91f81a32fef5):
  Real (post-patch): not prev_field or (prev_field.is_relation and field not in model._meta.parents.values() and field is not model._meta.auto_field and (model._meta.auto_field is None or part not in getattr(prev_field,'to_fields',[])))
  Model: isFirst || (priorIsRelation && !concreteParentLink && !redundantLocalValue && (!hasRedundantLocalValue || !priorAlreadyCovers))
Every sub-condition maps 1:1 (or<->||, and<->&&, negations aligned; isFirst<->not prev_field, priorIsRelation<->is_relation, concreteParentLink<->parents.values() membership, redundantLocalValue<->is auto_field, hasRedundantLocalValue<->auto_field is not None, priorAlreadyCovers<->part in to_fields).

Faithfulness probes, no divergence found:
- Unrealizable flag combos (e.g. redundantLocalValue=true while hasRedundantLocalValue=false, impossible in repo) never cause a wrong output: !redundantLocalValue=false already zeroes the conjunction, so the over-free abstraction is behaviorally harmless on every realizable input.
- Return-value modeling: spec pins the full keepMask flag stream (positionally stronger than the real filtered relation_parts), but the modeling boundary is the per-segment keep decision, which equals the real per-iteration append-guard on all inputs. Stronger-but-consistent, not drifted/too-strong in a way the real callee would violate.
- First-segment short-circuit matches (isFirst || dominance == not prev_field).
- G-CONF passed exhaustively: all 128 single-Hop configs + 100131 fuzzed paths (seed 16661), 0 disagreements between the R/I shadow and the patch append-guard transcribed independently from patch.diff.

No input exists where the modeled function disagrees with the real callee. The spec faithfully models the patched behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Re-verified the accepted relaxed-leakage disposition rather than rubber-stamping. (1) same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True — spec region byte-identical, so G-DIFF is a genuine discrimination test. (2) Core sound: Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean fails (exit 1) precisely on the discriminating keepSegment goal ((isFirst || (priorIsRelation && !targetOfPrior)) = keepSegment h) for the FK-as-PK shape. (3) meta.json relaxed_leakage=true, G-LEAK=relaxed, RELAXED_LEAKAGE.md present. (4) Lexical scan of the computed spec_view: 0 hits for auto_field, to_fields, target_fields, _meta, parents, lookup_allowed, relation_parts, options.py, path_infos, prev_field, is_relation, foreign/primary key narration, django/admin symbols — no gold-diff quoting and no bug->fix narration. The ONLY disclosure beyond problem_statement is exactly the dispositioned facet: the two extra opaque redundancy discriminators beyond the PS-public concreteParentLink clause — !redundantLocalValue (gold `field is not model._meta.auto_field`) and the disjunction (!hasRedundantLocalValue || !priorAlreadyCovers) (gold auto_field-is-None / to_fields membership) — carried structurally via opaque mechanism-free flag names/docstrings. Unavoidability re-derived: the auto-PK drop is load-bearing for the F2P assertion restaurant__place__country__id__exact (must drop `id` to keep the joined lookup in list_filter) yet is absent from both problem_statement and hints_text (single bisect hash); no PS-only keep rule can both pass the F2P and reject the prepatch. Found NO new leaking line beyond the dispositioned facet and no broken disposition. Per _audit.py convention (relaxed-leakage panel recorded as pass + note), the honest recording is NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.