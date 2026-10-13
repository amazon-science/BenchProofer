# P2 adversarial audit — django__django-15280

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_dropcached.lean`, `atk_inverted.lean`, `atk_offbyone.lean`, `atk_reverse.lean`, `atk_const.lean`, `atk_echomap.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = resolvedSeq lookup children` is a TOTAL functional equality under `loom.semantics.termination "total"` with NO axioms and NO A-legs (meta.json axioms=[], deep_model_references=[]). Every verifying implementation must produce EXACTLY resolvedSeq lookup children (cached child keeps existingParent = some p; uncached child = lookup key), which under the mapping.md bijection is precisely the patched get_prefetch_queryset loop body. Hence any verifying impl's faithful refined patch is behaviorally the gold patch and resolves. No verify⇏correct gap exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,6 +97,11 @@
   ensures out = resolvedSeq lookup children
   do
     -- impl-start
+    -- Pre-image skeleton: the association the grouping key implies is written
+    -- onto EVERY child unconditionally, discarding whatever association the
+    -- child already carried. The frozen spec requires `resolvedSeq` (which keeps
+    -- a pre-existing association), so prove_correct MUST fail on any child whose
+    -- `existingParent` is `some p` with `p ≠ lookup c.key`.
     let mut result : List Nat := []
     let mut i : Nat := children.length
     while i > 0
@@ -106,12 +111,7 @@
       decreasing i
     do
       let c := children[i - 1]!
-      -- A child carrying no association yet is associated with the parent its
-      -- key maps to; a child that already carries one keeps it untouched.
-      let parent : Nat :=
-        match c.existingParent with
-        | some p => p
-        | none   => lookup c.key
+      let parent : Nat := lookup c.key
       result := parent :: result
       i := i - 1
     return result
```

Attack 2 — `atk_dropcached.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,12 +106,9 @@
       decreasing i
     do
       let c := children[i - 1]!
-      -- A child carrying no association yet is associated with the parent its
-      -- key maps to; a child that already carries one keeps it untouched.
-      let parent : Nat :=
-        match c.existingParent with
+      let parent : Nat := match c.existingParent with
         | some p => p
-        | none   => lookup c.key
+        | none   => 0
       result := parent :: result
       i := i - 1
     return result
@@ -120,8 +117,5 @@
 prove_correct linkChildrenToParents by
   loom_solve <;>
     first
-    | -- loop-entry: drop children.length = [], the fold is nil.
-      (rw [List.drop_length]; simp)
-    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
-      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
-      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
+    | (rw [List.drop_length]; simp)
+    | (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
```

Attack 3 — `atk_inverted.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,12 +106,9 @@
       decreasing i
     do
       let c := children[i - 1]!
-      -- A child carrying no association yet is associated with the parent its
-      -- key maps to; a child that already carries one keeps it untouched.
-      let parent : Nat :=
-        match c.existingParent with
-        | some p => p
-        | none   => lookup c.key
+      let parent : Nat := match c.existingParent with
+        | some _p => lookup c.key
+        | none    => lookup c.key
       result := parent :: result
       i := i - 1
     return result
@@ -120,8 +117,5 @@
 prove_correct linkChildrenToParents by
   loom_solve <;>
     first
-    | -- loop-entry: drop children.length = [], the fold is nil.
-      (rw [List.drop_length]; simp)
-    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
-      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
-      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
+    | (rw [List.drop_length]; simp)
+    | (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
```

Attack 4 — `atk_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,12 +106,7 @@
       decreasing i
     do
       let c := children[i - 1]!
-      -- A child carrying no association yet is associated with the parent its
-      -- key maps to; a child that already carries one keeps it untouched.
-      let parent : Nat :=
-        match c.existingParent with
-        | some p => p
-        | none   => lookup c.key
+      let parent : Nat := resolveOne lookup children[i]!
       result := parent :: result
       i := i - 1
     return result
@@ -120,8 +115,5 @@
 prove_correct linkChildrenToParents by
   loom_solve <;>
     first
-    | -- loop-entry: drop children.length = [], the fold is nil.
-      (rw [List.drop_length]; simp)
-    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
-      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
-      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
+    | (rw [List.drop_length]; simp)
+    | (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
```

Attack 5 — `atk_reverse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,30 +98,18 @@
   do
     -- impl-start
     let mut result : List Nat := []
-    let mut i : Nat := children.length
-    while i > 0
+    let mut i : Nat := 0
+    while i < children.length
       invariant 0 ≤ i ∧ i ≤ children.length
-      invariant result = resolvedSeq lookup (children.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = resolvedSeq lookup (children.take i)
+      done_with i = children.length
+      decreasing children.length - i
     do
-      let c := children[i - 1]!
-      -- A child carrying no association yet is associated with the parent its
-      -- key maps to; a child that already carries one keeps it untouched.
-      let parent : Nat :=
-        match c.existingParent with
-        | some p => p
-        | none   => lookup c.key
-      result := parent :: result
-      i := i - 1
+      let c := children[i]!
+      result := resolveOne lookup c :: result
+      i := i + 1
     return result
     -- impl-end
 
 prove_correct linkChildrenToParents by
-  loom_solve <;>
-    first
-    | -- loop-entry: drop children.length = [], the fold is nil.
-      (rw [List.drop_length]; simp)
-    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
-      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
-      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
+  loom_solve <;> simp_all [resolvedSeq, resolveOne, List.take]
```

Attack 6 — `atk_const.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,31 +97,8 @@
   ensures out = resolvedSeq lookup children
   do
     -- impl-start
-    let mut result : List Nat := []
-    let mut i : Nat := children.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ children.length
-      invariant result = resolvedSeq lookup (children.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := children[i - 1]!
-      -- A child carrying no association yet is associated with the parent its
-      -- key maps to; a child that already carries one keeps it untouched.
-      let parent : Nat :=
-        match c.existingParent with
-        | some p => p
-        | none   => lookup c.key
-      result := parent :: result
-      i := i - 1
-    return result
+    return List.replicate children.length 0
     -- impl-end
 
 prove_correct linkChildrenToParents by
-  loom_solve <;>
-    first
-    | -- loop-entry: drop children.length = [], the fold is nil.
-      (rw [List.drop_length]; simp)
-    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
-      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
-      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
+  loom_solve <;> simp_all [resolvedSeq]
```

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -97,31 +97,8 @@
   ensures out = resolvedSeq lookup children
   do
     -- impl-start
-    let mut result : List Nat := []
-    let mut i : Nat := children.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ children.length
-      invariant result = resolvedSeq lookup (children.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := children[i - 1]!
-      -- A child carrying no association yet is associated with the parent its
-      -- key maps to; a child that already carries one keeps it untouched.
-      let parent : Nat :=
-        match c.existingParent with
-        | some p => p
-        | none   => lookup c.key
-      result := parent :: result
-      i := i - 1
-    return result
+    return resolvedSeq lookup children
     -- impl-end
 
 prove_correct linkChildrenToParents by
-  loom_solve <;>
-    first
-    | -- loop-entry: drop children.length = [], the fold is nil.
-      (rw [List.drop_length]; simp)
-    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
-      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
-      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
+  loom_solve
```

Attack 8 — `atk_echomap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,31 +97,8 @@
   ensures out = resolvedSeq lookup children
   do
     -- impl-start
-    let mut result : List Nat := []
-    let mut i : Nat := children.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ children.length
-      invariant result = resolvedSeq lookup (children.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := children[i - 1]!
-      -- A child carrying no association yet is associated with the parent its
-      -- key maps to; a child that already carries one keeps it untouched.
-      let parent : Nat :=
-        match c.existingParent with
-        | some p => p
-        | none   => lookup c.key
-      result := parent :: result
-      i := i - 1
-    return result
+    return children.map (resolveOne lookup)
     -- impl-end
 
 prove_correct linkChildrenToParents by
-  loom_solve <;>
-    first
-    | -- loop-entry: drop children.length = [], the fold is nil.
-      (rw [List.drop_length]; simp)
-    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
-      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
-      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
+  loom_solve <;> simp_all [resolvedSeq, List.map]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the linking loop must COMPLETE (the real
-- routine is a bounded for-loop over the fetched batch that always
-- terminates), so the spec must also rule out diverging implementations —
-- under partial correctness a non-terminating body would vacuously satisfy
-- every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms and no A-reference deep model of an outside callee. The
--  per-element behaviour this routine pins is a pure function of its inputs: each
--  child object carries an OPTIONAL pre-existing association to a parent object
--  (`existingParent`), and a lookup maps a child's grouping key to the parent it
--  belongs to. Both the optional association and the lookup are produced by
--  UNCHANGED machinery; they enter as the free inputs `children` / `lookup`, and
--  the decision claims nothing about how either is computed — it holds for EVERY
--  value they could take. There is therefore nothing to validate against a real
--  callee: no module-level `axiom`, no G-AX. mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- One child object as far as this routine observes it:
   * `key`            — the grouping key by which the child is matched to the
                        parent it belongs to (an opaque identity token);
   * `existingParent` — the parent association the child already carries, if any
                        (`some p`), or `none` when the child carries none yet.
   Everything else about the child is orthogonal (mapping.md §2). -/
structure Child where
  key            : Nat
  existingParent : Option Nat
deriving Inhabited, DecidableEq

/- The parent a single child ends up associated with. A child that ALREADY
   carries an association keeps it untouched; a child that carries none is
   associated with the parent its key maps to under `lookup`. This is the
   desired behaviour: a pre-existing, more specific association is never
   discarded in favour of the one implied by the grouping key. -/
def resolveOne (lookup : Nat → Nat) (c : Child) : Nat :=
  match c.existingParent with
  | some p => p
  | none   => lookup c.key

/- The parents the whole batch of children ends up associated with, in batch
   order. Front-recursive so a single unfold is available per loop step (the
   fold pattern, plan §5.4). -/
def resolvedSeq (lookup : Nat → Nat) : List Child → List Nat
  | []      => []
  | c :: cs => resolveOne lookup c :: resolvedSeq lookup cs

@[simp] lemma resolvedSeq_nil (lookup : Nat → Nat) : resolvedSeq lookup [] = [] := rfl
lemma resolvedSeq_cons (lookup : Nat → Nat) (c : Child) (cs : List Child) :
    resolvedSeq lookup (c :: cs) = resolveOne lookup c :: resolvedSeq lookup cs := rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (cs : List Child) (i : Nat) (hi : i < cs.length) :
    cs.drop i = cs[i]! :: cs.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-child fold step: dropping one fewer element exposes child `i-1` on the
   front, so `resolvedSeq` peels its resolved parent. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma resolvedSeq_drop_step (lookup : Nat → Nat) (cs : List Child) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cs.length) :
    resolvedSeq lookup (cs.drop (i - 1)) =
      resolveOne lookup cs[i - 1]! :: resolvedSeq lookup (cs.drop i) := by
  have hlt : i - 1 < cs.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  rw [drop_cons_eq cs (i - 1) hlt, hsucc, resolvedSeq_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Associate a batch of child objects with the parent objects they belong to,
   and report, in batch order, the parent each child ends up associated with.

   `lookup` maps a child's grouping key to the parent it belongs to. The desired
   behaviour (`resolvedSeq`): a child that ALREADY carries a parent association
   keeps that association untouched; only a child carrying none is associated
   with the parent its key maps to. A pre-existing, more specific association is
   never overwritten by the one implied by the grouping key.

   `children` and `lookup` are read-only (neither `mut`): the routine consults
   the batch and the mapping and builds a fresh list of outcomes, mutating
   nothing it is handed (directive 5). -/
method linkChildrenToParents (children : List Child) (lookup : Nat → Nat) return (out : List Nat)
  ensures out = resolvedSeq lookup children
  do
    -- impl-start
    let mut result : List Nat := []
    let mut i : Nat := children.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ children.length
      invariant result = resolvedSeq lookup (children.drop i)
      done_with i = 0
      decreasing i
    do
      let c := children[i - 1]!
      -- A child carrying no association yet is associated with the parent its
      -- key maps to; a child that already carries one keeps it untouched.
      let parent : Nat :=
        match c.existingParent with
        | some p => p
        | none   => lookup c.key
      result := parent :: result
      i := i - 1
    return result
    -- impl-end

prove_correct linkChildrenToParents by
  loom_solve <;>
    first
    | -- loop-entry: drop children.length = [], the fold is nil.
      (rw [List.drop_length]; simp)
    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
```

Prepatch bug re-encoded as an attack: `True`.

### Baselines
- positive_control.lean (byte-identical impl of gold): same_spec=True; `bash scripts/lean_verify.sh positive_control.lean` -> exit 0 (VERIFIES).
- atk_prepatch.lean (bundle's Solution_prepatch.lean, unconditional `parent := lookup c.key`): same_spec=True; verify -> exit 1 (FAILS) at the exact discriminating goal `lookup c.key = match existingParent | some p => p | none => lookup c.key` (matches refinement.md's G-DIFF claim). prepatch_reproduced=True.

8 DISTINCT SAME-SPEC (all confirmed True via swebench_unified.markers.same_spec) WRONG IMPLS, verified with `bash scripts/lean_verify.sh <f>`, run concurrently in batches of <=4:
1. atk_prepatch (bug/unconditional lookup) -> exit 1 FAIL (rejected).
2. atk_dropcached (partial-domain: none=>0, drops lookup for uncached) -> exit 1 FAIL.
3. atk_inverted (guard-swap: both branches lookup, discards cached parent) -> exit 1 FAIL.
4. atk_offbyone (boundary: children[i]! instead of [i-1]!) -> exit 1 FAIL.
5. atk_reverse (control-flow-effect: forward index accumulating with cons -> reversed order) -> exit 1 FAIL.
6. atk_const (degenerate ungrounded: List.replicate len 0) -> exit 1 FAIL.
7. atk_echomap (ungrounded map echo, weaker proof) -> exit 1 FAIL (simp_all no progress).
8. atk_echo (ungrounded-oracle ECHO: `return resolvedSeq lookup children`) -> exit 0 VERIFIES.

MANDATORY RESOLVE STEP for the ONLY verifying wrong-impl (echo): its faithful refined patch computes exactly resolvedSeq (cached kept, uncached looked up) => under the mapping this IS the gold patch. Materialized patch_echo.diff and ran through the official harness: `run_resolve('django__django-15280', patch_echo, timeout=1800, retries=1)` (harness.py, via `docker`) -> RESOLVED=True, COMPLETED=True, NOTE='resolved'. The verifying attack's faithful patch RESOLVES => does NOT break the spec. This is the resolving-echo case explicitly NOT a weakness under the 2026-08-06 G-PANEL-1/G-EQ policy.

### REFINEMENT.MD AUDIT (§4 focus, A-legs + correspondence):
- No A-legs to audit: meta.json axioms=[], deep_model_references=[]; refinement.md §B/§C and mapping.md §3 correctly declare no consumed axiom, no A-reference deep model, no G-AX. The genuinely-changed op (the `if not is_cached` guard) is modeled DEEPLY (resolveOne's `match existingParent`, leg A4), not hidden behind an axiom -> no kind-3.
- Legs A1-A5 are all R / R+I / I and their model<->callee correspondence holds: queryset<->List Child (A1), rel_obj_attr+instances_dict<->lookup (A2), is_cached<->Option existingParent (A3), patched body<->resolveOne (A4), post-loop relation<->out (A5). is_cached/get_local_related_value/instances_dict are all UNCHANGED by the patch and correctly folded into free inputs.
- Independent cross-check: ran conformance_check.py standalone -> 'G-CONF OK ... 0 disagreements' over 100009 inputs (seed 15280); the oracle quotes the patched loop verbatim and agrees with the R/I shadow.

CONCLUSION: >=5 attacks run (8 total, spanning partial-domain, boundary, guard-swap, control-flow-effect, degenerate, and ungrounded-oracle echo); 7 correctly fail to verify, and the sole verifying impl's faithful refined patch RESOLVES under the official Docker harness. verify => correct holds for this bundle. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_dropcached.lean`, `atk_inverted.lean`, `atk_offbyone.lean`, `atk_reverse.lean`, `atk_const.lean`, `atk_echomap.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = resolvedSeq lookup children` is a TOTAL functional equality under `loom.semantics.termination "total"` with NO axioms and NO A-legs (meta.json axioms=[], deep_model_references=[]). Every verifying implementation must produce EXACTLY resolvedSeq lookup children (cached child keeps existingParent = some p; uncached child = lookup key), which under the mapping.md bijection is precisely the patched get_prefetch_queryset loop body. Hence any verifying impl's faithful refined patch is behaviorally the gold patch and resolves. No verify⇏correct gap exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_dropcached.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_inverted.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_reverse.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_const.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_echomap.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the linking loop must COMPLETE (the real
-- routine is a bounded for-loop over the fetched batch that always
-- terminates), so the spec must also rule out diverging implementations —
-- under partial correctness a non-terminating body would vacuously satisfy
-- every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms and no A-reference deep model of an outside callee. The
--  per-element behaviour this routine pins is a pure function of its inputs: each
--  child object carries an OPTIONAL pre-existing association to a parent object
--  (`existingParent`), and a lookup maps a child's grouping key to the parent it
--  belongs to. Both the optional association and the lookup are produced by
--  UNCHANGED machinery; they enter as the free inputs `children` / `lookup`, and
--  the decision claims nothing about how either is computed — it holds for EVERY
--  value they could take. There is therefore nothing to validate against a real
--  callee: no module-level `axiom`, no G-AX. mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- One child object as far as this routine observes it:
   * `key`            — the grouping key by which the child is matched to the
                        parent it belongs to (an opaque identity token);
   * `existingParent` — the parent association the child already carries, if any
                        (`some p`), or `none` when the child carries none yet.
   Everything else about the child is orthogonal (mapping.md §2). -/
structure Child where
  key            : Nat
  existingParent : Option Nat
deriving Inhabited, DecidableEq

/- The parent a single child ends up associated with. A child that ALREADY
   carries an association keeps it untouched; a child that carries none is
   associated with the parent its key maps to under `lookup`. This is the
   desired behaviour: a pre-existing, more specific association is never
   discarded in favour of the one implied by the grouping key. -/
def resolveOne (lookup : Nat → Nat) (c : Child) : Nat :=
  match c.existingParent with
  | some p => p
  | none   => lookup c.key

/- The parents the whole batch of children ends up associated with, in batch
   order. Front-recursive so a single unfold is available per loop step (the
   fold pattern, plan §5.4). -/
def resolvedSeq (lookup : Nat → Nat) : List Child → List Nat
  | []      => []
  | c :: cs => resolveOne lookup c :: resolvedSeq lookup cs

@[simp] lemma resolvedSeq_nil (lookup : Nat → Nat) : resolvedSeq lookup [] = [] := rfl
lemma resolvedSeq_cons (lookup : Nat → Nat) (c : Child) (cs : List Child) :
    resolvedSeq lookup (c :: cs) = resolveOne lookup c :: resolvedSeq lookup cs := rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (cs : List Child) (i : Nat) (hi : i < cs.length) :
    cs.drop i = cs[i]! :: cs.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-child fold step: dropping one fewer element exposes child `i-1` on the
   front, so `resolvedSeq` peels its resolved parent. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma resolvedSeq_drop_step (lookup : Nat → Nat) (cs : List Child) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cs.length) :
    resolvedSeq lookup (cs.drop (i - 1)) =
      resolveOne lookup cs[i - 1]! :: resolvedSeq lookup (cs.drop i) := by
  have hlt : i - 1 < cs.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  rw [drop_cons_eq cs (i - 1) hlt, hsucc, resolvedSeq_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Associate a batch of child objects with the parent objects they belong to,
   and report, in batch order, the parent each child ends up associated with.

   `lookup` maps a child's grouping key to the parent it belongs to. The desired
   behaviour (`resolvedSeq`): a child that ALREADY carries a parent association
   keeps that association untouched; only a child carrying none is associated
   with the parent its key maps to. A pre-existing, more specific association is
   never overwritten by the one implied by the grouping key.

   `children` and `lookup` are read-only (neither `mut`): the routine consults
   the batch and the mapping and builds a fresh list of outcomes, mutating
   nothing it is handed (directive 5). -/
method linkChildrenToParents (children : List Child) (lookup : Nat → Nat) return (out : List Nat)
  ensures out = resolvedSeq lookup children
  do
    -- impl-start
    let mut result : List Nat := []
    let mut i : Nat := children.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ children.length
      invariant result = resolvedSeq lookup (children.drop i)
      done_with i = 0
      decreasing i
    do
      let c := children[i - 1]!
      -- A child carrying no association yet is associated with the parent its
      -- key maps to; a child that already carries one keeps it untouched.
      let parent : Nat :=
        match c.existingParent with
        | some p => p
        | none   => lookup c.key
      result := parent :: result
      i := i - 1
    return result
    -- impl-end

prove_correct linkChildrenToParents by
  loom_solve <;>
    first
    | -- loop-entry: drop children.length = [], the fold is nil.
      (rw [List.drop_length]; simp)
    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
```

Prepatch bug re-encoded as an attack: `True`.

### Baselines
- positive_control.lean (byte-identical impl of gold): same_spec=True; `bash scripts/lean_verify.sh positive_control.lean` -> exit 0 (VERIFIES).
- atk_prepatch.lean (bundle's Solution_prepatch.lean, unconditional `parent := lookup c.key`): same_spec=True; verify -> exit 1 (FAILS) at the exact discriminating goal `lookup c.key = match existingParent | some p => p | none => lookup c.key` (matches refinement.md's G-DIFF claim). prepatch_reproduced=True.

8 DISTINCT SAME-SPEC (all confirmed True via swebench_unified.markers.same_spec) WRONG IMPLS, verified with `bash scripts/lean_verify.sh <f>`, run concurrently in batches of <=4:
1. atk_prepatch (bug/unconditional lookup) -> exit 1 FAIL (rejected).
2. atk_dropcached (partial-domain: none=>0, drops lookup for uncached) -> exit 1 FAIL.
3. atk_inverted (guard-swap: both branches lookup, discards cached parent) -> exit 1 FAIL.
4. atk_offbyone (boundary: children[i]! instead of [i-1]!) -> exit 1 FAIL.
5. atk_reverse (control-flow-effect: forward index accumulating with cons -> reversed order) -> exit 1 FAIL.
6. atk_const (degenerate ungrounded: List.replicate len 0) -> exit 1 FAIL.
7. atk_echomap (ungrounded map echo, weaker proof) -> exit 1 FAIL (simp_all no progress).
8. atk_echo (ungrounded-oracle ECHO: `return resolvedSeq lookup children`) -> exit 0 VERIFIES.

MANDATORY RESOLVE STEP for the ONLY verifying wrong-impl (echo): its faithful refined patch computes exactly resolvedSeq (cached kept, uncached looked up) => under the mapping this IS the gold patch. Materialized patch_echo.diff and ran through the official harness: `run_resolve('django__django-15280', patch_echo, timeout=1800, retries=1)` (harness.py, via `docker`) -> RESOLVED=True, COMPLETED=True, NOTE='resolved'. The verifying attack's faithful patch RESOLVES => does NOT break the spec. This is the resolving-echo case explicitly NOT a weakness under the 2026-08-06 G-PANEL-1/G-EQ policy.

### REFINEMENT.MD AUDIT (§4 focus, A-legs + correspondence):
- No A-legs to audit: meta.json axioms=[], deep_model_references=[]; refinement.md §B/§C and mapping.md §3 correctly declare no consumed axiom, no A-reference deep model, no G-AX. The genuinely-changed op (the `if not is_cached` guard) is modeled DEEPLY (resolveOne's `match existingParent`, leg A4), not hidden behind an axiom -> no kind-3.
- Legs A1-A5 are all R / R+I / I and their model<->callee correspondence holds: queryset<->List Child (A1), rel_obj_attr+instances_dict<->lookup (A2), is_cached<->Option existingParent (A3), patched body<->resolveOne (A4), post-loop relation<->out (A5). is_cached/get_local_related_value/instances_dict are all UNCHANGED by the patch and correctly folded into free inputs.
- Independent cross-check: ran conformance_check.py standalone -> 'G-CONF OK ... 0 disagreements' over 100009 inputs (seed 15280); the oracle quotes the patched loop verbatim and agrees with the R/I shadow.

CONCLUSION: >=5 attacks run (8 total, spanning partial-domain, boundary, guard-swap, control-flow-effect, degenerate, and ungrounded-oracle echo); 7 correctly fail to verify, and the sole verifying impl's faithful refined patch RESOLVES under the official Docker harness. verify => correct holds for this bundle. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real repo callee. (1) Spec region is byte-identical across twins (same_spec=True over the velvet backend); the only difference is inside the consumer impl region. (2) Solution.lean verifies (exit 0); Solution_prepatch.lean fails at exactly the discriminating goal `lookup key = match existingParent with some p => p | none => lookup key`, so the ensures `out = resolvedSeq lookup children` genuinely discriminates the added `if not self.field.is_cached` guard — spec is not vacuous/rubber-stamped. (3) conformance_check.py (R/I shadow vs faithful transliteration of the patched loop) passes 100009 inputs, seed 15280, 0 disagreements, including boundary seeds (empty, single cached/uncached, cached==lookup, duplicate keys, falsy parent id 0). (4) Real repo at base_commit 973fa566 (related_descriptors.py:636-639, reverse-many-to-one manager) confirms the pre-patch unconditional loop and the patch adds precisely the is_cached guard; resolveOne's some/none branches map exactly. Faithfulness-specific scrutiny: modeling `lookup` as a TOTAL function (vs real instances_dict raising KeyError on missing key) is a weakening under universal quantification, not a strengthening, and is justified because the prefetch query `{field__in: instances}` guarantees every queryset child has a matching parent (unreachable KeyError path). Total-correctness termination is a justified spec-strengthening (the real for-loop over the fetched batch is bounded and always terminates; the verified impl carries `decreasing i`). No reachable input yields disagreement. Spec is FAITHFUL — neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec == True). Generated consumer spec view (velvet _lean_spec_view: impl elided, prove_correct body elided) contains NO repo symbols, file paths, or gold-patch specifics: scanned for is_cached / rel_obj / instances_dict / setattr / get_prefetch_queryset / get_local_related_value / related_descriptors / .py / django / base_commit / test names (Profile/User/Room/House/deferred/fields_cache/queryset) — zero hits. The spec's behavioral content ('a child that already carries a parent association keeps it; a child carrying none is looked up by grouping key', modeled via abstract Child/existingParent/lookup/resolveOne/resolvedSeq) is a legitimate abstract correctness specification stated in domain-neutral vocabulary. It does not reveal the gold edit's mechanism (the added `if not self.field.is_cached(rel_obj):` guard) or its file/line location beyond what the public problem_statement already communicates (the reported bug: prefetched inner instances wrongly inherit deferred-field state instead of preserving the already-resolved relation). All repo-specific mapping (is_cached guard, related_descriptors.py:646-648 anchors) lives only in refinement.md / mapping.md, which are audit artifacts outside the spec view. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
