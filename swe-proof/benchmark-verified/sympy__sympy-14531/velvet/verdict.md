# P2 adversarial audit — sympy__sympy-14531

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 10 | `atk_2_probe_first.lean`, `atk_3_partial_domain.lean`, `atk_4_echo.lean`, `atk_5_limit_probe.lean`, `atk_9_probe_commit_order.lean`, `atk_10_split_proj.lean`, `atk_13_branch_on_probe.lean`, `atk_14_snapshot_restore.lean`, `atk_15_unrep_reg_branch.lean`, `atk_16_limit_snapshot.lean` |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_swap_rel.lean`, `atk_6_dropcfg.lean`, `atk_7_dup_commit.lean`, `atk_8_reuse_text.lean`, `atk_11_fresh_printer.lean`, `atk_12_limit_boundary.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. All 10 verifying wrong impls had their faithful refined patches materialized per mapping.md 2.2 and RUN through the official harness (run_resolve): every one measured resolved=True, completed=True, F2P success ['test_python_relational','test_Rational'], failure [], P2P 84/84. No verifying impl has a non-resolving faithful materialization, so verify=>correct is not falsified on the family explored.

The closest thing to a break is the negative control I built deliberately: negctl_naive_live.diff (the NAIVE reading of atk_14 -- the extra self._print(expr.rhs) taken LIVE on self WITHOUT the state restore that the model's `reg := ra.2` with ra read from the snapshot r0 demands) measured resolved=FALSE, completed=True, F2P failure ['test_python_relational'], P2P 84/84, 3 consistent attempts (not flaky). That is NOT a counterexample: it is the refinement of a DIFFERENT impl -- the committed three-step fold (b,a,b) -- and that impl is atk_7_dup_commit.lean, which the spec REJECTS at lean_verify EXIT=1 with residual `(renderSub cfg (renderSub cfg (renderSub cfg regOld b).2 a).2 b).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2`. The resolve/no-resolve split therefore tracks the materialization rule, not the impl -- which is exactly refinement.md F2's location claim, now reproduced from fresh scratch with the harness on both sides of the split.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_swap_rel.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,20 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
+    -- WRONG: render b first, then a.  Both steps are committed, but in the
+    -- other order, so the registry fold is b-then-a.
+    let rb := renderSub cfg reg b
+    reg := rb.2
     let ra := renderSub cfg reg a
     reg := ra.2
-    let rb := renderSub cfg reg b
-    reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +195,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 2 — `atk_2_probe_first.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,21 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
+    -- An extra application of renderSub on b, named ahead of the arm; its .2 is
+    -- NEVER written back and its .1 is NEVER emitted.  (mapping.md 2.2 rule 2)
+    let pre := renderSub cfg reg b
     let ra := renderSub cfg reg a
     reg := ra.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +196,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 3 — `atk_3_partial_domain.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,28 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let ra := renderSub cfg reg a
-    reg := ra.2
-    let rb := renderSub cfg reg b
-    reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
-    return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
+    -- PARTIAL DOMAIN: on the reg = [] slice take an extra (discarded) step on a
+    -- fabricated sub-object; elsewhere plain gold.
+    if reg = [] then
+      let junk := renderSub cfg reg (SubObj.mk 0)
+      let ra := renderSub cfg reg a
+      reg := ra.2
+      let rb := renderSub cfg reg b
+      reg := rb.2
+      return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
+    else
+      let ra := renderSub cfg reg a
+      reg := ra.2
+      let rb := renderSub cfg reg b
+      reg := rb.2
+      return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +203,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 4 — `atk_4_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,17 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let ra := renderSub cfg reg a
-    reg := ra.2
-    let rb := renderSub cfg reg b
-    reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
-    return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
+    -- ECHO: no steps at all, just the spec's own post-images.
+    let res := taggedPair cfg tag a b reg
+    reg := taggedPairReg cfg a b reg
+    return res
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +192,14 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let re := renderSub cfg reg e
-    reg := re.2
-    let rz := renderSub cfg reg z
-    reg := rz.2
-    let rz0 := renderSub cfg reg z0
-    reg := rz0.2
-    -- Assemble the comma-separated triple.
-    return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
-        ++ rz0.1 ++ ")".toList
+    -- ECHO at the ternary site.
+    let res := limitTriple cfg e z z0 reg
+    reg := limitTripleReg cfg e z z0 reg
+    return res
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 5 — `atk_5_limit_probe.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,18 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let ra := renderSub cfg reg a
     reg := ra.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +193,20 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
+    -- An extra discarded step on z0 ahead of the three committed ones.
+    let pre := renderSub cfg reg z0
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 6 — `atk_6_dropcfg.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,20 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let ra := renderSub cfg reg a
+    -- WRONG: the composite's configuration is dropped at the sub-object sites
+    -- (default `false`), though the registry is still threaded.
+    let ra := renderSub false reg a
     reg := ra.2
-    let rb := renderSub cfg reg b
+    let rb := renderSub false reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +195,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 7 — `atk_7_dup_commit.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,22 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
+    -- WRONG: the extra step on b is WRITTEN BACK, so the composite takes three
+    -- committed steps (b, a, b) instead of two.
+    let pre := renderSub cfg reg b
+    reg := pre.2
     let ra := renderSub cfg reg a
     reg := ra.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +197,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 8 — `atk_8_reuse_text.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,21 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
+    -- WRONG: the registry is gold's exactly, but b's TEXT is taken from the
+    -- step at the composite's INCOMING registry rather than the advanced one.
+    let pre := renderSub cfg reg b
     let ra := renderSub cfg reg a
     reg := ra.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
-    return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
+    return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ pre.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +196,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 9 — `atk_9_probe_commit_order.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,19 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
+    -- b's step is the only WRITTEN-BACK one; it is chained off the registry a's
+    -- step leaves, which is computed by an application whose .2 is discarded.
+    let rb := renderSub cfg (renderSub cfg reg a).2 b
     let ra := renderSub cfg reg a
-    reg := ra.2
-    let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +194,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 10 — `atk_10_split_proj.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,21 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let ra := renderSub cfg reg a
-    reg := ra.2
+    -- The text and the effect of a's step are read off TWO separate
+    -- applications at the same registry.
+    let r1 := renderSub cfg reg a
+    let r2 := renderSub cfg reg a
+    reg := r2.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
-    return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
+    return tag ++ "(".toList ++ r1.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +196,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 11 — `atk_11_fresh_printer.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,20 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let ra := renderSub cfg reg a
+    -- WRONG: both sub-objects rendered on a FRESH serializer of the right
+    -- configuration (empty incoming registry); its registry is written back.
+    let ra := renderSub cfg [] a
     reg := ra.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +195,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 12 — `atk_12_limit_boundary.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,18 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let ra := renderSub cfg reg a
     reg := ra.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +193,24 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
+    -- BOUNDARY: when z0 = z, reuse z's already-computed text for the third
+    -- slot and only commit two steps; gold elsewhere.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
-    let rz0 := renderSub cfg reg z0
-    reg := rz0.2
-    -- Assemble the comma-separated triple.
-    return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
-        ++ rz0.1 ++ ")".toList
+    if z0 = z then
+      return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
+          ++ rz.1 ++ ")".toList
+    else
+      let rz0 := renderSub cfg reg z0
+      reg := rz0.2
+      return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
+          ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 13 — `atk_13_branch_on_probe.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,28 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let ra := renderSub cfg reg a
-    reg := ra.2
-    let rb := renderSub cfg reg b
-    reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
-    return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
+    -- The discarded step's TEXT is genuinely consumed, as a branch condition
+    -- over two identical arms.
+    let pre := renderSub cfg reg b
+    if pre.1 = [] then
+      let ra := renderSub cfg reg a
+      reg := ra.2
+      let rb := renderSub cfg reg b
+      reg := rb.2
+      return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
+    else
+      let ra := renderSub cfg reg a
+      reg := ra.2
+      let rb := renderSub cfg reg b
+      reg := rb.2
+      return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +203,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 14 — `atk_14_snapshot_restore.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,24 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let ra := renderSub cfg reg a
+    -- The incoming registry is saved, an extra step on b is COMMITTED
+    -- (reg := pre.2 -- rule 1 => a LIVE call), and that commit is then erased by
+    -- re-deriving reg from the SNAPSHOT r0.  Final (out, reg) = gold's.
+    let r0 := reg
+    let pre := renderSub cfg reg b
+    reg := pre.2
+    let ra := renderSub cfg r0 a
     reg := ra.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +199,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 15 — `atk_15_unrep_reg_branch.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,29 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let ra := renderSub cfg reg a
-    reg := ra.2
-    let rb := renderSub cfg reg b
-    reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
-    return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
+    -- A step primed to a registry value that NO real serializer state encodes
+    -- (`tag`, e.g. "Eq", is not declaration text), consumed as a branch
+    -- condition over two identical arms.
+    let ghost := renderSub cfg tag b
+    if ghost.1 = [] then
+      let ra := renderSub cfg reg a
+      reg := ra.2
+      let rb := renderSub cfg reg b
+      reg := rb.2
+      return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
+    else
+      let ra := renderSub cfg reg a
+      reg := ra.2
+      let rb := renderSub cfg reg b
+      reg := rb.2
+      return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +204,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 16 — `atk_16_limit_snapshot.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,18 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let ra := renderSub cfg reg a
     reg := ra.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +193,23 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let re := renderSub cfg reg e
+    -- Ternary instance of the snapshot/restore lever: z0's step is COMMITTED
+    -- first (rule 1 => live), then erased from the snapshot r0.
+    let r0 := reg
+    let pre := renderSub cfg reg z0
+    reg := pre.2
+    let re := renderSub cfg r0 e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Attack 17 — `atk_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,14 +159,16 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let ra := renderSub cfg reg a
-    reg := ra.2
-    let rb := renderSub cfg reg b
-    reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
-    return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
+    -- PRE-IMAGE skeleton: each sub-object is rendered by a THROWAWAY serializer
+    -- built on the spot -- default configuration (`false`) and an empty registry
+    -- -- instead of by the composite's own serializer. So the composite's `cfg`
+    -- never reaches the sub-objects, `b`'s step does not start from the registry
+    -- `a`'s step left, and the composite's own registry `reg` is never extended.
+    -- The frozen spec pins `out = taggedPair cfg tag a b regOld` AND
+    -- `reg = taggedPairReg cfg a b regOld`, so `prove_correct` MUST fail on both.
+    let pa := renderSub false [] a
+    let pb := renderSub false [] b
+    return tag ++ "(".toList ++ pa.1 ++ ", ".toList ++ pb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
@@ -194,17 +196,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
-    let re := renderSub cfg reg e
-    reg := re.2
-    let rz := renderSub cfg reg z
-    reg := rz.2
-    let rz0 := renderSub cfg reg z0
-    reg := rz0.2
-    -- Assemble the comma-separated triple.
-    return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
-        ++ rz0.1 ++ ")".toList
+    -- PRE-IMAGE skeleton: each of the three sub-objects is rendered by a
+    -- THROWAWAY serializer -- default configuration (`false`), empty registry --
+    -- rather than by the composite's own serializer, so `cfg` is dropped, no
+    -- step starts from the registry the previous step left, and `reg` is never
+    -- extended. Both frozen clauses (`out = limitTriple cfg e z z0 regOld` and
+    -- `reg = limitTripleReg cfg e z z0 regOld`) are therefore violated and
+    -- `prove_correct` MUST fail.
+    let pe := renderSub false [] e
+    let pz := renderSub false [] z
+    let pz0 := renderSub false [] z0
+    return "Limit(".toList ++ pe.1 ++ ", ".toList ++ pz.1 ++ ", ".toList
+        ++ pz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,18 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let ra := renderSub cfg reg a
     reg := ra.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +193,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial review, instance sympy__sympy-14531, velvet. Base_commit worktree: at 205da797006360fc629110937e39a19c9561313e (left clean).

### Same-spec
All 18 .lean files (16 attacks + prepatch + pos_control) confirmed byte-identical spec:
  python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(<bundle Solution.lean>, <atk>, b.language))" -> True for every file.
Only the two impl regions were edited; axioms/pure/pre/post byte-identical. Solution.lean has 0 `sorry`, 0 `requires`, 4 `ensures`, 1 `opaque` (renderSub) and NO `axiom` declaration -- so there is no consumed axiom to launder unsoundness through.

### Commands
bash scripts/lean_verify.sh <name>.lean
python resolve1.py <name>
(calls swebench_unified.harness.run_resolve('sympy__sympy-14531', <name>.diff))
Every .diff checked with `git apply --check` in the base_commit worktree -> all 11 clean (10 attacks + negative control), plus gold_control.diff.

#### RESULTS: 16 attacks + prepatch + 2 controls
attack                      verify   resolve        F2P
atk_1_swap_rel              EXIT=1   n/a            (rejected)
atk_2_probe_first           EXIT=0   resolved=True  both ok, P2P 84/84
atk_3_partial_domain        EXIT=0   resolved=True  both ok, P2P 84/84
atk_4_echo                  EXIT=0   resolved=True  both ok, P2P 84/84
atk_5_limit_probe           EXIT=0   resolved=True  both ok, P2P 84/84
atk_6_dropcfg               EXIT=1   n/a            (rejected)
atk_7_dup_commit            EXIT=1   n/a            (rejected)
atk_8_reuse_text            EXIT=1   n/a            (rejected)
atk_9_probe_commit_order    EXIT=0   resolved=True  both ok, P2P 84/84
atk_10_split_proj           EXIT=0   resolved=True  both ok, P2P 84/84
atk_11_fresh_printer        EXIT=1   n/a            (rejected)
atk_12_limit_boundary       EXIT=1   n/a            (rejected)
atk_13_branch_on_probe      EXIT=0   resolved=True  both ok, P2P 84/84
atk_14_snapshot_restore     EXIT=0   resolved=True  both ok, P2P 84/84
atk_15_unrep_reg_branch     EXIT=0   resolved=True  both ok, P2P 84/84
atk_16_limit_snapshot       EXIT=0   resolved=True  both ok, P2P 84/84
atk_prepatch (PREPATCH BUG) EXIT=1   n/a            REPRODUCED
### Controls
pos_control (gold impl)     EXIT=0   resolved=True  both ok, P2P 84/84
negctl_naive_live           n/a      resolved=FALSE F2P failure ['test_python_relational'], 3 consistent attempts

### ATTACK FAMILY COVERAGE (well past the 4-6 distinct minimum)
Re-encoded from prior passes: atk_1_swap_rel (the FIRST recorded break, refinement.md E), atk_11_fresh_printer, atk_7_dup_commit (=weak-tagged-commit-extra-step), atk_8_reuse_text (=weak-tagged-reuse-probe-text), atk_2_probe_first (=atk_1_extra_step_b), atk_13_branch_on_probe (=atk_1d, ite_self), atk_3_partial_domain, atk_5_limit_probe (=atk_10_limit_extra), atk_4_echo (ungrounded-oracle echo), plus the prepatch bug.
Distinct shape classes exercised: partial-domain (atk_3, atk_12), boundary (atk_12 on z0=z), control-flow-effect (atk_13, atk_15), ungrounded-oracle echo (atk_4), step-order (atk_1), dropped-configuration (atk_6), throwaway/fresh serializer (atk_11, atk_prepatch), duplicated/committed step (atk_7), projection-splitting (atk_10), ternary-site parity (atk_5, atk_12, atk_16).

THREE NOVEL SHAPES not in the bundle's ledger, built specifically to attack the A-leg and the 2.2 rule's LEAST-specified branch (rule 1, write-back -> live call), which every prior pass probed only through rule 2 (discarded probe):
  * atk_14_snapshot_restore -- an extra step on b is genuinely WRITTEN BACK (`reg := pre.2`, so rule 1 forces a LIVE self.`_print`), and that commit is then ERASED by re-deriving reg from a snapshot of the incoming registry (`let r0 := reg; ... let ra := renderSub cfg r0 a; reg := ra.2`). This is the one shape where a verifying impl demands a live call with a real, later-cancelled effect, so the faithful materialization must include a state RESTORE. It VERIFIES (denotation = gold) and its faithful patch RESOLVES=True.
  * atk_16_limit_snapshot -- the same rule-1 lever at the ternary printLimit site (z0 committed first, then erased). VERIFIES, RESOLVES=True. The two sites agree.
  * atk_15_unrep_reg_branch -- `let ghost := renderSub cfg tag b`: a discarded step primed to `tag` (e.g. "Eq") USED AS A REGISTRY. `tag` is outside the image of the declaration-text encoding (every real registry is a concatenation of "<s> = Symbol('<s>')\n" / "<f> = Function('<f>')\n" lines), so NO real serializer state encodes that carrier value -- an attack on the mapping.md 2 `reg : List Char` bijection being onto. Its text is consumed as an ite_self branch. VERIFIES, RESOLVES=True: the un-encodable carrier value cannot reach either post-image, so it is harmless, and any primed probe materializes it.

### WHY THE NEGATIVE CONTROL MATTERS (anti-vacuity)
Ten resolved=True runs would be worthless if the harness could not distinguish anything. It can: negctl_naive_live.diff -- atk_14's arm with the extra live step but WITHOUT the restore -- measured resolved=FALSE (F2P failure ['test_python_relational'], P2P 84/84, 3 consistent attempts, not flaky). The impl that diff actually refines is atk_7_dup_commit.lean, which the spec REJECTS at EXIT=1. So the harness discriminates on exactly the observable the second `ensures` pins, and the split tracks the materialization rule rather than the impl.

#### Rejection residuals are semantic, not syntactic
All 6 rejected attacks + prepatch fail with genuine unsolved goals about renderSub, confirming both clauses do real work (no attack was rejected by a tactic/syntax artifact):
  atk_1_swap_rel   ensures_1: (renderSub cfg (renderSub cfg regOld b).2 a).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2
  atk_6_dropcfg    ensures_1: (renderSub false (renderSub false regOld a).2 b).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2
  atk_7_dup_commit ensures_1: (renderSub cfg (renderSub cfg (renderSub cfg regOld b).2 a).2 b).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2
  atk_8_reuse_text ensures_2: (renderSub cfg regOld b).1 = (renderSub cfg (renderSub cfg regOld a).2 b).1
  atk_11_fresh     ensures_1: (renderSub cfg (renderSub cfg [] a).2 b).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2
  atk_12_limit_bd  ensures_1: (renderSub cfg (renderSub cfg regOld e).2 z).2 = (renderSub cfg (renderSub cfg (renderSub cfg regOld e).2 z).2 z0).2
  atk_prepatch     ensures_1: regOld = (renderSub cfg (renderSub cfg regOld a).2 b).2   [prepatch bug REPRODUCED]
Note atk_8 refutes on the FIRST clause alone and atk_7 on the SECOND alone -- the two clauses are independently load-bearing, and atk_12 shows the clause is non-vacuous on a guarded slice.

#### refinement.md AUDIT (A-legs and model<->patch correspondence)
Leg tag census over tables A and B: 11 rows total -- 3 R, 3 A-reference, 3 A-reference/I, 2 I. NO kind-3 and no A-consumed leg anywhere; the only occurrence of "kind-3" is the section heading C asserting their absence. Every leg is R / A-reference / I as required.
A-leg correspondence checks I ran independently:
  * renderSub <-> Printer.`_print`: confirmed at base_commit. StrPrinter.`_default_settings` = {order, full_prec, sympy_integers, abbrev} (str.py:20) accepts sympy_integers but has no symbols/functions; PythonPrinter.`__init__` sets self.symbols/self.functions = [] (python.py:21-22) and ReprPrinter.`_default_settings` = {'order': None} only -- so the two-slice claim of mapping.md 2.1 (cfg realizable only on the StrPrinter slice, reg only on the PythonPrinter slice) is exactly right, and modeling them as one step with both parameters is a sound over-approximation for an `opaque` that pins nothing.
  * The registry-effect and dedup facts: PythonPrinter.`_print_Symbol` / `_print_Function` append under `if symbol not in self.symbols` (python.py:31-42) -- the real callee DOES deduplicate, and refinement.md C/E state plainly that the opaque model assumes nothing of the kind, i.e. the model is strictly WEAKER than the callee there. That is the sound direction, and it is the honest reason atk_7-style duplicate-step rivals could resolve; the doc records it rather than hiding it.
  * Left-to-right step order (G-AX check 8, refinement.md A5/B2): verified directly -- `'%s(%s, %s)' % ('T', f('lhs'), f('rhs'))` evaluates lhs then rhs, and `"Limit(%s, %s, %s)" % tuple(map(f, ('e','z','z0')))` evaluates e,z,z0 in order. So the argument-order fold in taggedPairReg/limitTripleReg is the gold arms' actual behaviour, not a modeling convenience.
  * Arm bindings: patch.diff's `_print_Relational` charmap arm (str.py:633) and `_print_Limit` dir=="+" arm (str.py:219) are exactly the two arms modeled, and they are the two the F2P tests exercise. Confirmed against the test_patch: test_python_relational now demands python(Eq(x,y)) == "x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)" (grades the REGISTRY leg AND its order) and test_Rational now demands sstr(Eq(x, Rational(2,3)), sympy_integers=True) == "Eq(x, S(2)/3)" and sstr(Limit(x, x, Rational(7,2)), sympy_integers=True) == "Limit(x, x, S(7)/2)" (grades the CONFIGURATION leg, at both the binary and the ternary site). Both legs of refinement.md 0 are genuinely graded, one test each, exactly as claimed.
  * mapping.md 2.2's probe construction matches conformance_check.py's probe_of verbatim (`__class__`.`__new__`, `__dict__`.update, dict(`_settings`), list copies of symbols/functions); I reused that same construction in my materializations, so the rule I applied is the one the bundle ships and checks.

#### Scope / what I did not check
axiom_check.py and conformance_check.py could not be executed in this scratch: the base_commit sympy needs a pre-3.10 interpreter (`from collections import Mapping` fails on the available python3.10), and both scripts import sympy. Those are G-AX's and G-CONF's own gates, not G-EQ's, and my verdict rests on lean_verify + run_resolve evidence only -- no A-leg claim is taken on faith where I could check it structurally (see above). This is a tooling note, not a defect and not a reason for INCONCLUSIVE: every attack verification and every needed resolve run completed.

#### Verdict: SOUND
16 same-spec wrong impls encoded (10 verifying), all 10 faithful patches materialized and executed through the official harness, all 10 resolved=True with F2P both and P2P 84/84. Prepatch bug reproduced (EXIT=1). Positive control verifies AND resolves. A deliberate negative control does NOT resolve, proving the runs are discriminating rather than vacuous, and the impl it refines is one the spec rejects. The verifying family is confined to applications of renderSub that reach NEITHER post-image (discarded probes, ite_self branches, split projections, and -- newly -- committed-then-restored steps and un-encodable registry primings); every such shape is the same program as gold in this carrier, and each materializes to code that resolves. refinement.md's leg tags are complete and correct with no kind-3.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 10 | `atk_2_probe_first.lean`, `atk_3_partial_domain.lean`, `atk_4_echo.lean`, `atk_5_limit_probe.lean`, `atk_9_probe_commit_order.lean`, `atk_10_split_proj.lean`, `atk_13_branch_on_probe.lean`, `atk_14_snapshot_restore.lean`, `atk_15_unrep_reg_branch.lean`, `atk_16_limit_snapshot.lean` |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_swap_rel.lean`, `atk_6_dropcfg.lean`, `atk_7_dup_commit.lean`, `atk_8_reuse_text.lean`, `atk_11_fresh_printer.lean`, `atk_12_limit_boundary.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. All 10 verifying wrong impls had their faithful refined patches materialized per mapping.md 2.2 and RUN through the official harness (run_resolve): every one measured resolved=True, completed=True, F2P success ['test_python_relational','test_Rational'], failure [], P2P 84/84. No verifying impl has a non-resolving faithful materialization, so verify=>correct is not falsified on the family explored.

The closest thing to a break is the negative control I built deliberately: negctl_naive_live.diff (the NAIVE reading of atk_14 -- the extra self._print(expr.rhs) taken LIVE on self WITHOUT the state restore that the model's `reg := ra.2` with ra read from the snapshot r0 demands) measured resolved=FALSE, completed=True, F2P failure ['test_python_relational'], P2P 84/84, 3 consistent attempts (not flaky). That is NOT a counterexample: it is the refinement of a DIFFERENT impl -- the committed three-step fold (b,a,b) -- and that impl is atk_7_dup_commit.lean, which the spec REJECTS at lean_verify EXIT=1 with residual `(renderSub cfg (renderSub cfg (renderSub cfg regOld b).2 a).2 b).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2`. The resolve/no-resolve split therefore tracks the materialization rule, not the impl -- which is exactly refinement.md F2's location claim, now reproduced from fresh scratch with the harness on both sides of the split.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_swap_rel.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_probe_first.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3_partial_domain.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5_limit_probe.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_dropcfg.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_dup_commit.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_reuse_text.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_probe_commit_order.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_split_proj.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_fresh_printer.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_limit_boundary.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_branch_on_probe.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14_snapshot_restore.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15_unrep_reg_branch.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_16_limit_snapshot.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -159,19 +159,18 @@
   ensures reg = taggedPairReg cfg a b regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let ra := renderSub cfg reg a
     reg := ra.2
     let rb := renderSub cfg reg b
     reg := rb.2
-    -- Assemble: tag, "(", a's text, ", ", b's text, ")".
     return tag ++ "(".toList ++ ra.1 ++ ", ".toList ++ rb.1 ++ ")".toList
     -- impl-end
 
 prove_correct printTaggedPair by
   loom_solve
-  all_goals simp only [taggedPair, taggedPairReg, renderText, renderReg]
+  all_goals try simp only [taggedPair, taggedPairReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [taggedPair, taggedPairReg, renderText, renderReg]
 
 /- Serialize the ternary `Limit(e, z, z0)` composite on the ACTIVE serializer.
    `cfg` is its configuration; `reg` is its declaration registry (`mut`, since
@@ -194,19 +193,18 @@
   ensures reg = limitTripleReg cfg e z z0 regOld
   do
     -- impl-start
-    -- One step of the composite's own serializer per sub-object, in argument
-    -- order: each step reads the registry the previous one left and extends it.
     let re := renderSub cfg reg e
     reg := re.2
     let rz := renderSub cfg reg z
     reg := rz.2
     let rz0 := renderSub cfg reg z0
     reg := rz0.2
-    -- Assemble the comma-separated triple.
     return "Limit(".toList ++ re.1 ++ ", ".toList ++ rz.1 ++ ", ".toList
         ++ rz0.1 ++ ")".toList
     -- impl-end
 
 prove_correct printLimit by
   loom_solve
-  all_goals simp only [limitTriple, limitTripleReg, renderText, renderReg]
+  all_goals try simp only [limitTriple, limitTripleReg, renderText, renderReg, ite_self]
+  all_goals try rfl
+  all_goals try simp [limitTriple, limitTripleReg, renderText, renderReg]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial review, instance sympy__sympy-14531, velvet. Base_commit worktree: at 205da797006360fc629110937e39a19c9561313e (left clean).

### Same-spec
All 18 .lean files (16 attacks + prepatch + pos_control) confirmed byte-identical spec:
  python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(<bundle Solution.lean>, <atk>, b.language))" -> True for every file.
Only the two impl regions were edited; axioms/pure/pre/post byte-identical. Solution.lean has 0 `sorry`, 0 `requires`, 4 `ensures`, 1 `opaque` (renderSub) and NO `axiom` declaration -- so there is no consumed axiom to launder unsoundness through.

### Commands
bash scripts/lean_verify.sh <name>.lean
python resolve1.py <name>
(calls swebench_unified.harness.run_resolve('sympy__sympy-14531', <name>.diff))
Every .diff checked with `git apply --check` in the base_commit worktree -> all 11 clean (10 attacks + negative control), plus gold_control.diff.

#### RESULTS: 16 attacks + prepatch + 2 controls
attack                      verify   resolve        F2P
atk_1_swap_rel              EXIT=1   n/a            (rejected)
atk_2_probe_first           EXIT=0   resolved=True  both ok, P2P 84/84
atk_3_partial_domain        EXIT=0   resolved=True  both ok, P2P 84/84
atk_4_echo                  EXIT=0   resolved=True  both ok, P2P 84/84
atk_5_limit_probe           EXIT=0   resolved=True  both ok, P2P 84/84
atk_6_dropcfg               EXIT=1   n/a            (rejected)
atk_7_dup_commit            EXIT=1   n/a            (rejected)
atk_8_reuse_text            EXIT=1   n/a            (rejected)
atk_9_probe_commit_order    EXIT=0   resolved=True  both ok, P2P 84/84
atk_10_split_proj           EXIT=0   resolved=True  both ok, P2P 84/84
atk_11_fresh_printer        EXIT=1   n/a            (rejected)
atk_12_limit_boundary       EXIT=1   n/a            (rejected)
atk_13_branch_on_probe      EXIT=0   resolved=True  both ok, P2P 84/84
atk_14_snapshot_restore     EXIT=0   resolved=True  both ok, P2P 84/84
atk_15_unrep_reg_branch     EXIT=0   resolved=True  both ok, P2P 84/84
atk_16_limit_snapshot       EXIT=0   resolved=True  both ok, P2P 84/84
atk_prepatch (PREPATCH BUG) EXIT=1   n/a            REPRODUCED
### Controls
pos_control (gold impl)     EXIT=0   resolved=True  both ok, P2P 84/84
negctl_naive_live           n/a      resolved=FALSE F2P failure ['test_python_relational'], 3 consistent attempts

### ATTACK FAMILY COVERAGE (well past the 4-6 distinct minimum)
Re-encoded from prior passes: atk_1_swap_rel (the FIRST recorded break, refinement.md E), atk_11_fresh_printer, atk_7_dup_commit (=weak-tagged-commit-extra-step), atk_8_reuse_text (=weak-tagged-reuse-probe-text), atk_2_probe_first (=atk_1_extra_step_b), atk_13_branch_on_probe (=atk_1d, ite_self), atk_3_partial_domain, atk_5_limit_probe (=atk_10_limit_extra), atk_4_echo (ungrounded-oracle echo), plus the prepatch bug.
Distinct shape classes exercised: partial-domain (atk_3, atk_12), boundary (atk_12 on z0=z), control-flow-effect (atk_13, atk_15), ungrounded-oracle echo (atk_4), step-order (atk_1), dropped-configuration (atk_6), throwaway/fresh serializer (atk_11, atk_prepatch), duplicated/committed step (atk_7), projection-splitting (atk_10), ternary-site parity (atk_5, atk_12, atk_16).

THREE NOVEL SHAPES not in the bundle's ledger, built specifically to attack the A-leg and the 2.2 rule's LEAST-specified branch (rule 1, write-back -> live call), which every prior pass probed only through rule 2 (discarded probe):
  * atk_14_snapshot_restore -- an extra step on b is genuinely WRITTEN BACK (`reg := pre.2`, so rule 1 forces a LIVE self.`_print`), and that commit is then ERASED by re-deriving reg from a snapshot of the incoming registry (`let r0 := reg; ... let ra := renderSub cfg r0 a; reg := ra.2`). This is the one shape where a verifying impl demands a live call with a real, later-cancelled effect, so the faithful materialization must include a state RESTORE. It VERIFIES (denotation = gold) and its faithful patch RESOLVES=True.
  * atk_16_limit_snapshot -- the same rule-1 lever at the ternary printLimit site (z0 committed first, then erased). VERIFIES, RESOLVES=True. The two sites agree.
  * atk_15_unrep_reg_branch -- `let ghost := renderSub cfg tag b`: a discarded step primed to `tag` (e.g. "Eq") USED AS A REGISTRY. `tag` is outside the image of the declaration-text encoding (every real registry is a concatenation of "<s> = Symbol('<s>')\n" / "<f> = Function('<f>')\n" lines), so NO real serializer state encodes that carrier value -- an attack on the mapping.md 2 `reg : List Char` bijection being onto. Its text is consumed as an ite_self branch. VERIFIES, RESOLVES=True: the un-encodable carrier value cannot reach either post-image, so it is harmless, and any primed probe materializes it.

### WHY THE NEGATIVE CONTROL MATTERS (anti-vacuity)
Ten resolved=True runs would be worthless if the harness could not distinguish anything. It can: negctl_naive_live.diff -- atk_14's arm with the extra live step but WITHOUT the restore -- measured resolved=FALSE (F2P failure ['test_python_relational'], P2P 84/84, 3 consistent attempts, not flaky). The impl that diff actually refines is atk_7_dup_commit.lean, which the spec REJECTS at EXIT=1. So the harness discriminates on exactly the observable the second `ensures` pins, and the split tracks the materialization rule rather than the impl.

#### Rejection residuals are semantic, not syntactic
All 6 rejected attacks + prepatch fail with genuine unsolved goals about renderSub, confirming both clauses do real work (no attack was rejected by a tactic/syntax artifact):
  atk_1_swap_rel   ensures_1: (renderSub cfg (renderSub cfg regOld b).2 a).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2
  atk_6_dropcfg    ensures_1: (renderSub false (renderSub false regOld a).2 b).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2
  atk_7_dup_commit ensures_1: (renderSub cfg (renderSub cfg (renderSub cfg regOld b).2 a).2 b).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2
  atk_8_reuse_text ensures_2: (renderSub cfg regOld b).1 = (renderSub cfg (renderSub cfg regOld a).2 b).1
  atk_11_fresh     ensures_1: (renderSub cfg (renderSub cfg [] a).2 b).2 = (renderSub cfg (renderSub cfg regOld a).2 b).2
  atk_12_limit_bd  ensures_1: (renderSub cfg (renderSub cfg regOld e).2 z).2 = (renderSub cfg (renderSub cfg (renderSub cfg regOld e).2 z).2 z0).2
  atk_prepatch     ensures_1: regOld = (renderSub cfg (renderSub cfg regOld a).2 b).2   [prepatch bug REPRODUCED]
Note atk_8 refutes on the FIRST clause alone and atk_7 on the SECOND alone -- the two clauses are independently load-bearing, and atk_12 shows the clause is non-vacuous on a guarded slice.

#### refinement.md AUDIT (A-legs and model<->patch correspondence)
Leg tag census over tables A and B: 11 rows total -- 3 R, 3 A-reference, 3 A-reference/I, 2 I. NO kind-3 and no A-consumed leg anywhere; the only occurrence of "kind-3" is the section heading C asserting their absence. Every leg is R / A-reference / I as required.
A-leg correspondence checks I ran independently:
  * renderSub <-> Printer.`_print`: confirmed at base_commit. StrPrinter.`_default_settings` = {order, full_prec, sympy_integers, abbrev} (str.py:20) accepts sympy_integers but has no symbols/functions; PythonPrinter.`__init__` sets self.symbols/self.functions = [] (python.py:21-22) and ReprPrinter.`_default_settings` = {'order': None} only -- so the two-slice claim of mapping.md 2.1 (cfg realizable only on the StrPrinter slice, reg only on the PythonPrinter slice) is exactly right, and modeling them as one step with both parameters is a sound over-approximation for an `opaque` that pins nothing.
  * The registry-effect and dedup facts: PythonPrinter.`_print_Symbol` / `_print_Function` append under `if symbol not in self.symbols` (python.py:31-42) -- the real callee DOES deduplicate, and refinement.md C/E state plainly that the opaque model assumes nothing of the kind, i.e. the model is strictly WEAKER than the callee there. That is the sound direction, and it is the honest reason atk_7-style duplicate-step rivals could resolve; the doc records it rather than hiding it.
  * Left-to-right step order (G-AX check 8, refinement.md A5/B2): verified directly -- `'%s(%s, %s)' % ('T', f('lhs'), f('rhs'))` evaluates lhs then rhs, and `"Limit(%s, %s, %s)" % tuple(map(f, ('e','z','z0')))` evaluates e,z,z0 in order. So the argument-order fold in taggedPairReg/limitTripleReg is the gold arms' actual behaviour, not a modeling convenience.
  * Arm bindings: patch.diff's `_print_Relational` charmap arm (str.py:633) and `_print_Limit` dir=="+" arm (str.py:219) are exactly the two arms modeled, and they are the two the F2P tests exercise. Confirmed against the test_patch: test_python_relational now demands python(Eq(x,y)) == "x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)" (grades the REGISTRY leg AND its order) and test_Rational now demands sstr(Eq(x, Rational(2,3)), sympy_integers=True) == "Eq(x, S(2)/3)" and sstr(Limit(x, x, Rational(7,2)), sympy_integers=True) == "Limit(x, x, S(7)/2)" (grades the CONFIGURATION leg, at both the binary and the ternary site). Both legs of refinement.md 0 are genuinely graded, one test each, exactly as claimed.
  * mapping.md 2.2's probe construction matches conformance_check.py's probe_of verbatim (`__class__`.`__new__`, `__dict__`.update, dict(`_settings`), list copies of symbols/functions); I reused that same construction in my materializations, so the rule I applied is the one the bundle ships and checks.

#### Scope / what I did not check
axiom_check.py and conformance_check.py could not be executed in this scratch: the base_commit sympy needs a pre-3.10 interpreter (`from collections import Mapping` fails on the available python3.10), and both scripts import sympy. Those are G-AX's and G-CONF's own gates, not G-EQ's, and my verdict rests on lean_verify + run_resolve evidence only -- no A-leg claim is taken on faith where I could check it structurally (see above). This is a tooling note, not a defect and not a reason for INCONCLUSIVE: every attack verification and every needed resolve run completed.

#### Verdict: SOUND
16 same-spec wrong impls encoded (10 verifying), all 10 faithful patches materialized and executed through the official harness, all 10 resolved=True with F2P both and P2P 84/84. Prepatch bug reproduced (EXIT=1). Positive control verifies AND resolves. A deliberate negative control does NOT resolve, proving the runs are discriminating rather than vacuous, and the impl it refines is one the spec rejects. The verifying family is confined to applications of renderSub that reach NEITHER post-image (discarded probes, ite_self branches, split projections, and -- newly -- committed-then-restored steps and un-encodable registry primings); every such shape is the same program as gold in this carrier, and each materializes to code that resolves. refinement.md's leg tags are complete and correct with no kind-3.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on sympy__sympy-14531/velvet. Reference = OWN clean worktree at base_commit 205da797006360fc629110937e39a19c9561313e with patch.diff APPLIED, created fresh from the upstream repository so that the reference carries the gold patch and nothing else. Reference confirmed GOLD: after also applying instance.json's test_patch, both F2P tests (test_str.py::test_Rational, test_python.py::test_python_relational) PASS. Base commit used only as the reference for the unchanged callee (self.`_print`), per the brief.

**PRELIMINARIES.** (a) Spec region byte-identical: markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) == True; spec_signature sha256 prefix 5846d09e456d6ed0. (b) scripts/lean_verify.sh Solution.lean -> exit 0, no sorry/error.

ATTACK 1 - arm-level differential, INDEPENDENT harness (diff1.py, seed 987654321, not the bundle's conformance_check.py). Transliterated the pure region VERBATIM (taggedPair/taggedPairReg/limitTriple/limitTripleReg) with renderSub = one real self.`_print` observed on a printer primed to the incoming registry, and diffed against the patched `_print_Relational` (charmap arm) and `_print_Limit` (dir=='+' arm). Text slice on StrPrinter under cfg in {False,True}; effect slice on PythonPrinter primed to fuzzed non-empty registries, comparing assembled text AND (symbols,functions) AND the emitted declaration preamble. 20,826 checks, 0 divergences.

ATTACK 2 - CALLER slice with model arms actually INSTALLED (diff2.py, seed 20260816). Materialized the model per mapping.md 2.2 (probe = `__class__`.`__new__` + `__dict__`.update + dict(`_settings`) + list(symbols/functions), write-back of each step's .2) and compared the WHOLE real entry-point output against gold's: sstr under both settings, end-to-end python(expr), and PythonPrinter primed to ['pre_a','lambda']/['pre_f'] (text + state + preamble). 10,103 cases including nested arms, Floats, Python-keyword symbols. 0 divergences.

ATTACK 3 - THE HIDDEN STATE CHANNEL (deep.py, seed 77777). The one piece of real printer state NOT in the model's (cfg,reg) carrier is self.`_print_level`, which StrPrinter.`_print_Float` READS (str.py:611, strip = self.`_print_level` > 1). This is a genuine over-approximation risk: my Attack-1 harness invoked the arms at level 0, which is NOT the reachable regime (I confirmed the discrepancy directly: p.`_print_Relational`(Eq(x,Float(1.0))) at level 0 gives 'Eq(x, 1.00000000000000)' but real sstr gives 'Eq(x, 1.0)'). So I instrumented every arm invocation and recorded `_print_level` at entry and after each sub-step: 112,154 `_print_Relational` and 21,446 `_print_Limit` invocations, at entry levels 1,2,3,4,5 (i.e. genuinely nested), and the number of invocations whose sub-steps ran at UNEQUAL `_print_level` was 0. `_print_level` is constant across the sub-steps of any single arm invocation, so it cannot desynchronize the fold and the (cfg,reg) carrier loses nothing observable. Same run: 23,743 exotic caller-slice cases, 0 divergences.

ATTACK 4 - CARRIER INJECTIVITY (inj.py, seed 4242). If reg : List Char (the declaration text) were not injective on the real (symbols,functions) state, renderSub could not be a function of (cfg,reg,sub) and both `ensures` clauses would be unsatisfiable on the real system. Brute-forced 400k states over an adversarial alphabet built from the emitted line grammar itself ("')", "\n", " = Symbol('", " = Function('", "a')\nb = Symbol('b", keywords lambda/class/if) so a name could try to forge a line boundary, respecting the real dedup invariant. 321,897 distinct states, 0 collisions - carrier is injective.

ATTACK 5 - CARRIER TYPE GAP (nonstr.py). If self.`_print` could return a non-str, '%s' would stringify it while the List Char model treats it as text. Instrumented Printer.`_print` over a 62-element exotic pool (Q.positive, Permutation, PermutationGroup, Range, SeqFormula, ZZ/QQ/ZZ[x]/frac_field, BlockMatrix, MatrixSlice, MatAdd/MatMul/Trace/Adjoint, Poly, Order, matrices, containers): 6,598 entry-point calls, 0 non-str returns.

ATTACK 6 - TWO-SLICE CLAIM (mapping.md 2.1) independently confirmed: PythonPrinter({'sympy_integers':True}) raises TypeError "Unknown setting 'sympy_integers'"; PythonPrinter.`_default_settings` == {'order': None}; StrPrinter has no .symbols attribute. So modeling cfg and reg as one step IS an over-approximation - but a sound one, because renderSub is `opaque` with NO axiom declared and none consumed, so it pins no value and every real behavior on either slice is an instance of it. Same reasoning disposes of the real registry's dedup (python.py:40-41): the model assumes nothing about it, which is the weaker/sound direction.

FINAL COMBINED RUN (final.py, seed 555): model arms installed, 10,860 cases over the exotic pool x 9 nesting wrappers x 3 primed registries x both settings x python() end-to-end. 0 divergences.

OVER-STRENGTH REVIEW OF THE ensures CLAUSES. Both clauses pin only what the gold patch's arms actually do: out as the left-to-right assembly and reg as the left-to-right fold of exactly the arm's steps. tag : List Char is generic and covers every charmap value (I exercised Eq, Ne, and Assignment via codegen.ast, all of which really do reach the charmap arm at level 1). Where the spec is NARROWER than the repo it is narrower, not stronger: the dir != '+' Limit branch and the non-charmap Relational fallback (parenthesize) are simply not modeled, and the patch's other 12 call sites (`_print_AppliedPredicate`, `_print_Lambda`, `_print_MatrixElement`, `_print_Normal`, `_print_Permutation`, `_print_PermutationGroup`, `_print_PolyRing`, `_print_FracField`, `_print_Uniform`, `_print_ExprCondPair`) are out of scope. Scope narrowing is a too-weak concern, not a faithfulness break, and is out of this gate's lane.

**TOTAL:** ~72,000 differential comparisons plus 322k injectivity states and 133,600 instrumented arm invocations, across 6 independent attack angles. ZERO inputs found on which the modeled function disagrees with the real patched repo. No diverging input exists to cite, so no defect can be claimed. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / GOLD-RECONSTRUCTION review of velvet/Solution.lean for sympy__sympy-14531 (band settings-propagation, spec_provenance cold). Judged against problem_statement ONLY; hints_text is empty (len 0) so nothing was excused by it.

**NO RELAXATION IN THIS BUNDLE.** `find -iname '*RELAX*'` over the whole instance dir => empty; meta.json keys are ['axioms','band','base_commit','changed_files','conf_fuzz_seed','conf_skip','deep_model_references','gates','instance_id','modeled_functions','pbt_audit','repo','schema_version','spec_provenance','string_modeling','version'] -- no `relaxed_leakage`. gates['G-LEAK'].mode == 'strict', status 'pass'. So there was no unavoidability argument on offer and none was inherited; I judged the spec view against the strict bar.

INTEGRITY / SCOPE. markers.same_spec(Solution.lean, itself, velvet backend) = True; parse_regions errors = []; spec_view elides impl and proof (ELISION_IMPL / ELISION_PROOF present at lines 162, 166, 188, 192); spec_signature sha256 prefix 5846d09e456d6ed0. same_spec(Solution.lean, Solution_prepatch.lean) = True -- the twins share one spec region, so the leak surface is a single 192-line view, which I dumped in full and read line by line rather than grepping. scripts/lean_verify.sh on the CURRENT bytes: RC=0.

**WHAT THE GOLD EDIT IS.** One mechanical rewrite applied 11 times in sympy/printing/str.py: every site interpolating a sub-object via implicit str()/'%s' is rerouted through `self._print(...)` (e.g. `'%s(%s, %s)' % (charmap[expr.rel_op], expr.lhs, expr.rhs)` -> `... self._print(expr.lhs), self._print(expr.rhs)`; `"Limit(%s, %s, %s)" % (e, z, z0)` -> `% tuple(map(self._print, (e, z, z0)))`). The reconstruction-critical token is the callee name `self._print`, which is NOT public: '`_print`' in problem_statement == False, 'self.`_print`' == False, 'str.py' == False, 'StrPrinter' == False, 'sympy_integers' IS public (it appears in the sstr examples) but no printer internal, file path, or callee is ever named there.

MEASUREMENT ON THE CURRENT SPEC VIEW -- CLEAN. Substring probes over the computed spec_view text (not the raw file): '`_print`' False, 'self.' False, '%s' False, '`__str__`' False, 'StrPrinter' False, 'sympy_integers' False, 'sympy/printing' False, 'str.py' False, 'Symbol(' False, 'throwaway printer' False, '@@' False, 'diff --git' False, '+++ ' False. Narration screen: leakage.`_NARRATION_RE`.findall(spec_view) == [] (no bug/fix/patched/wrong/incorrectly/previously).

I also enumerated every >=3-char identifier in the spec view and diffed it against problem_statement: the residue is entirely Lean/Velvet vocabulary (SubObj, renderSub, renderText, renderReg, taggedPair(Reg), limitTriple(Reg), printTaggedPair, printLimit, cfg, reg, regOld, List/Char/Bool/Nat, loom/set_option/prove_correct) plus English prose -- no repo symbol, no patched-file path, no changed def/class name. leakage.screen(...) independently: passed=True, hard_failures=[], warnings=[].

Its changed-symbol set is ['print_Exp1','print_Inverse','print_LatticeOp','print_MatrixBase','print_NegativeInfinity','print_Or','print_Permutation','print_Pi','print_Relational','print_TensAdd','print_Transpose'] and no spec-view identifier embeds any of them; I checked by hand rather than trusting the screen, since the def/class harvester structurally cannot see `self._print` (the inserted CALLEE, defined in unpatched printer.py) -- that blind spot is exactly what this layer exists to cover, so I probed the token directly and it is absent.

THIS IS A REPAIRED REVISION -- I CONFIRMED THE REPAIR RATHER THAN INHERITING IT. meta.json's stamped G-PANEL-3 record is agent_verdict LEAKAGE against sources Solution.lean = 45158b3d7c6e..., citing `self._print` named verbatim at spec-view line 56 next to the 'composite's OWN serializer' vs 'throwaway serializer' docstrings. Current Solution.lean is 90f95879eef9... -- a different revision. grep -c '`_print`' on the current file = 0 (the only 'print' hits are the method names printTaggedPair/printLimit and the `renderSub`/`renderText`/`renderReg` abstractions). The prior finding's leaking line no longer exists; the abstract phrasing the prior note said was available ('a configuration- and state-aware sub-dispatch of the active serializer') is what the current axiom comment uses. G-LEAK was re-stamped strict/pass at 2026-08-16T13:40:02 on the current hash. So the stale LEAKAGE stamp is a superseded record, not a live finding -- I did not re-judge it as the reject lane, and I did not read it as a disposition.

**RESIDUAL CONTENT IS WITHIN THE PUBLIC FACET.** What the spec view does say abstractly is that both sub-objects render under the composite's OWN configuration `cfg` rather than a default, and that the composite's declaration registry advances once per sub-object in argument order. Both facets are derivable from problem_statement alone: the settings half is its headline ('StrPrinter setting are not respected by certain subexpressions', with sstr(Eq(x, S(1)/2), sympy_integers=True) printing 'Eq(x, 1/2)' instead of 'Eq(x, S(1)/2)' and the Limit(x, x, S(1)/2) example), and the registry/ordering half is its third example, which states the expected `python(Eq(x, y))` output as "x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)" -- that literally exhibits the missing per-subexpression declarations AND their lhs-before-rhs order. The spec view restates the public symptom in domain-neutral serializer vocabulary; it does not name the mechanism that fixes it.

UNAVOIDABILITY / LOAD-BEARING CROSS-CHECK (re-derived, not assumed). Strip test in a fresh mktemp -d: removed every /- ... -/ block comment and every non-marker line comment from both twins, then built with scripts/lean_verify.sh. Stripped Solution.lean -> RC=0 (still verifies against the post-patch impl). Stripped Solution_prepatch.lean -> RC=1, failing with real semantic residuals over the opaque callee, e.g. "Limit(" ++ (renderSub false [] e).1 ++ ... = "Limit(" ++ (renderSub cfg regOld e).1 ++ (renderSub cfg (renderSub cfg regOld e).2 z).1 ++ ... So the discriminator is carried entirely by the four `ensures` clauses over renderText/renderReg -- cfg threading plus registry chaining -- which name no repo symbol. The prose is removable narration, which is the right disposition here: nothing needs to be relaxed, because the faithful spec never needed the callee token.

SUPPORTING GATES I CONFIRMED PASS ON THE CURRENT HASH (90f95879...): G-VERIFY pass (5.7s), G-HYGIENE pass (spec_view region hash d615dc46...), G-INTEGRITY pass (instance.json byte-identical, additions-only), G-GOLD pass (gold impl verifies, prepatch fails), G-DIFF pass (prepatch verification failed), G-MUT killed 20/20, G-RESOLVE resolved, G-AX exit 0, G-CONF exit 0 (450929 comparisons, 0 disagreements). G-PANEL-1 SOUND and G-PANEL-2 FAITHFUL are stamped on an earlier hash (45158b3d/eq lane) -- noted for the rollup's routing, not relied on for this verdict, which rests on my own measurements above.

**NO FILE ADDRESSED ME.** Grepped Solution.lean, Solution_prepatch.lean, mapping.md and refinement.md for panel-directed instruction ('G-PANEL-3', 'panel_3', 'attacker', 'NO-LEAKAGE', 'dear auditor/panel/reviewer', 'you should/must record|submit', 'the honest verdict', 'do not report|submit'): zero hits. The bundle documents its model and its checks and does not tell the panel what to conclude.

**VERDICT:** NO-LEAKAGE. The spec view contains no gold-diff line, no diff marker, no patched file path, no patched repo symbol, no fix narration, and no callee name; the residual abstract statement of the requirement is fully derivable from the public problem_statement, and the discriminator is load-bearing in the ensures clauses rather than in prose.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
