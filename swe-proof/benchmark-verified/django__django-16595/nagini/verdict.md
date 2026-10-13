# P2 adversarial audit — django__django-16595

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_18.py`, `atk_19.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_17.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,8 +281,7 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
-    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
-            and is_same_field(this, nxt):
+    if nxt.kind == KIND_REMOVE and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
         return res, False
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,6 +281,8 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
+    probe = MigrationStep(KIND_RENAME, this.model_name_lower, this.name_lower,
+                          this.name_lower, this.has_explicit_column, False)
     if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
             and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
@@ -289,7 +291,7 @@
             and not this.has_explicit_column:
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                 nxt.new_name_lower, nxt.new_name_lower,
-                                this.has_explicit_column, False)
+                                probe.has_explicit_column, False)
         res2 = [nxt, carried]  # type: List[MigrationStep]
         return res2, False
     elif this.elidable:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,12 +281,14 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
+    probe = MigrationStep(KIND_RENAME, this.model_name_lower, this.name_lower,
+                          this.name_lower, this.has_explicit_column, False)
     if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
             and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
         return res, False
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
-            and not this.has_explicit_column:
+            and not probe.has_explicit_column:
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                 nxt.new_name_lower, nxt.new_name_lower,
                                 this.has_explicit_column, False)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,12 +281,14 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
+    probe = MigrationStep(KIND_OTHER, this.model_name_lower, this.name_lower,
+                          this.name_lower, this.has_explicit_column, False)
     if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
             and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
         return res, False
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
-            and not this.has_explicit_column:
+            and not probe.has_explicit_column:
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                 nxt.new_name_lower, nxt.new_name_lower,
                                 this.has_explicit_column, False)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,8 +281,7 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
-    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
-            and is_same_field(this, nxt):
+    if nxt.kind == KIND_ALTER and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
         return res, False
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -285,8 +285,7 @@
             and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
         return res, False
-    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
-            and not this.has_explicit_column:
+    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt):
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                 nxt.new_name_lower, nxt.new_name_lower,
                                 this.has_explicit_column, False)
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,7 +281,13 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
-    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
+    if this.elidable:
+        res3 = [nxt]  # type: List[MigrationStep]
+        return res3, False
+    elif nxt.elidable:
+        res4 = [this]  # type: List[MigrationStep]
+        return res4, False
+    elif (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
             and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
         return res, False
@@ -292,11 +298,5 @@
                                 this.has_explicit_column, False)
         res2 = [nxt, carried]  # type: List[MigrationStep]
         return res2, False
-    elif this.elidable:
-        res3 = [nxt]  # type: List[MigrationStep]
-        return res3, False
-    elif nxt.elidable:
-        res4 = [this]  # type: List[MigrationStep]
-        return res4, False
     return None, not nxt_references_altered_field
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -298,5 +298,5 @@
     elif nxt.elidable:
         res4 = [this]  # type: List[MigrationStep]
         return res4, False
-    return None, not nxt_references_altered_field
+    return None, not is_same_field(this, nxt)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,6 +281,7 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
+    eager = nxt.new_name_lower  # type: int
     if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
             and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
@@ -288,7 +289,7 @@
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
             and not this.has_explicit_column:
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
-                                nxt.new_name_lower, nxt.new_name_lower,
+                                eager, eager,
                                 this.has_explicit_column, False)
         res2 = [nxt, carried]  # type: List[MigrationStep]
         return res2, False
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -287,8 +287,11 @@
         return res, False
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
             and not this.has_explicit_column:
+        probe = MigrationStep(KIND_RENAME, this.model_name_lower,
+                              this.name_lower, nxt.new_name_lower,
+                              False, False)
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
-                                nxt.new_name_lower, nxt.new_name_lower,
+                                probe.new_name_lower, probe.new_name_lower,
                                 this.has_explicit_column, False)
         res2 = [nxt, carried]  # type: List[MigrationStep]
         return res2, False
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,15 +281,17 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
+    probe = MigrationStep(KIND_ALTER, this.model_name_lower, this.name_lower,
+                          this.name_lower, this.has_explicit_column, False)
     if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
             and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
         return res, False
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
-            and not this.has_explicit_column:
+            and not probe.has_explicit_column:
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                 nxt.new_name_lower, nxt.new_name_lower,
-                                this.has_explicit_column, False)
+                                probe.has_explicit_column, False)
         res2 = [nxt, carried]  # type: List[MigrationStep]
         return res2, False
     elif this.elidable:
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,15 +281,17 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
+    probe = MigrationStep(KIND_REMOVE, this.model_name_lower, this.name_lower,
+                          this.name_lower, this.has_explicit_column, False)
     if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
             and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
         return res, False
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
-            and not this.has_explicit_column:
+            and not probe.has_explicit_column:
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                 nxt.new_name_lower, nxt.new_name_lower,
-                                this.has_explicit_column, False)
+                                probe.has_explicit_column, False)
         res2 = [nxt, carried]  # type: List[MigrationStep]
         return res2, False
     elif this.elidable:
```

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -287,8 +287,11 @@
         return res, False
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
             and not this.has_explicit_column:
-        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
-                                nxt.new_name_lower, nxt.new_name_lower,
+        probe = MigrationStep(KIND_OTHER, this.model_name_lower,
+                              nxt.new_name_lower, nxt.new_name_lower,
+                              False, False)
+        carried = MigrationStep(KIND_ALTER, probe.model_name_lower,
+                                probe.name_lower, probe.name_lower,
                                 this.has_explicit_column, False)
         res2 = [nxt, carried]  # type: List[MigrationStep]
         return res2, False
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -287,8 +287,11 @@
         return res, False
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
             and not this.has_explicit_column:
+        first = MigrationStep(KIND_ALTER, this.model_name_lower,
+                              nxt.new_name_lower, nxt.new_name_lower,
+                              this.has_explicit_column, False)
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
-                                nxt.new_name_lower, nxt.new_name_lower,
+                                first.new_name_lower, first.new_name_lower,
                                 this.has_explicit_column, False)
         res2 = [nxt, carried]  # type: List[MigrationStep]
         return res2, False
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -286,7 +286,7 @@
         res = [nxt]  # type: List[MigrationStep]
         return res, False
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
-            and not this.has_explicit_column:
+            and not nxt.has_explicit_column:
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                 nxt.new_name_lower, nxt.new_name_lower,
                                 this.has_explicit_column, False)
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,6 +281,10 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
+    i = 0  # type: int
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
     if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
             and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
```

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,12 +281,14 @@
                 or elides_to_one_step(this, nxt)))
     # post-conditions-end
     # impl-start
-    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
+    probe = MigrationStep(KIND_ALTER, this.model_name_lower, this.name_lower,
+                          this.name_lower, this.has_explicit_column, True)
+    if probe.elidable and (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \
             and is_same_field(this, nxt):
         res = [nxt]  # type: List[MigrationStep]
         return res, False
-    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
-            and not this.has_explicit_column:
+    elif probe.elidable and nxt.kind == KIND_RENAME \
+            and is_same_field(this, nxt) and not this.has_explicit_column:
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                 nxt.new_name_lower, nxt.new_name_lower,
                                 this.has_explicit_column, False)
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -288,7 +288,7 @@
     elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \
             and not this.has_explicit_column:
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
-                                nxt.new_name_lower, nxt.new_name_lower,
+                                nxt.new_name_lower, this.new_name_lower,
                                 this.has_explicit_column, False)
         res2 = [nxt, carried]  # type: List[MigrationStep]
         return res2, False
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -289,7 +289,7 @@
             and not this.has_explicit_column:
         carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                 nxt.new_name_lower, nxt.new_name_lower,
-                                this.has_explicit_column, False)
+                                this.has_explicit_column, True)
         res2 = [nxt, carried]  # type: List[MigrationStep]
         return res2, False
     elif this.elidable:
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. 19 attacks encoded, ALL same-spec (adversary same-spec exit 0 on every one; spec region byte-identical, only the impl region edited). 14 REJECTED by the spec; 5 verified as CANDIDATEs; ALL 5 candidate patches materialized and RUN through the OFFICIAL harness (run_resolve) -- every one RESOLVED (F2P 1/1, P2P 37/37, completed=True, attempts=1, flaky=False). No verifying same-spec impl has a faithful refined patch that fails to resolve, so verify=>correct held under every attack I could construct.

### The prior pass's defect is repaired
The previous G-EQ recorded BROKEN on an UNCONDITIONAL constructor grant of has_explicit_column, which let an impl BUILD a KIND_RENAME/KIND_OTHER step purely to read its pinned-column status back (a facet whose repo counterpart cannot exist: RenameField.`__init__` takes no field, so.field is None; a bare Operation has no.field at all). model.py:110-112 now carries the suggested repair, `Ensures(Implies(kind == KIND_ALTER or kind == KIND_REMOVE, Acc(self.has_explicit_column) and self.has_explicit_column == has_explicit_column))`. I re-encoded that exact counterexample in all three of its shapes and all three are now REJECTED for INSUFFICIENT PERMISSION -- the repair holds and is not merely re-described in prose:
 * atk_2 (rename-kind probe, value-carried) -> exit 2; `atk_2.py:292: Method call might fail. There might be insufficient permission to access probe.has_explicit_column.`
 * atk_3 (same read made GUARD-load-bearing) -> exit 2, same insufficient-permission error.
 * atk_4 (KIND_OTHER probe, guard-load-bearing) -> exit 2, same.

### ATTACK-BY-ATTACK (path / weakness result / resolve result)
REJECTED (14) -- same spec, does not verify:
 * atk_1.py THE PREPATCH BUG re-encoded (guard reverted to KIND_REMOVE only) -> exit 2. Verifier: `Postcondition... Implies(((nxt.kind == KIND_ALTER) and is_same_field(this, nxt)),...)` might not hold -- the discriminating clause (G-DIFF) is what catches it. prepatch_reproduced=true.
 * atk_2/atk_3/atk_4 the prior counterexample, three shapes -> exit 2 (insufficient permission), above.
 * atk_5.py PARTIAL-DOMAIN, dual of the bug: collapse same-field ALTER but LOSE the unchanged same-field REMOVE arm -> exit 2; `Postcondition... Implies(((nxt.kind == KIND_REMOVE) and is_same_field(...)),...)`.
 * atk_6.py BOUNDARY: drop the rename branch's pinned-column guard so the carry-across fires even with an explicit column pinned -> exit 2; caught via the elidable fall-through clause (`Implies(not joined_by_field_rule(this,nxt) and this.elidable,...)`), i.e. joined_by_field_rule's boundary is load-bearing.
 * atk_7.py CONTROL-FLOW-EFFECT: test the generic elidable marks BEFORE the method's own same-field rules, so an elidable later step beats the same-field collapse -> exit 2; two postcondition errors (KIND_REMOVE collapse, and len==2 on the rename carry).
 * atk_8.py UNGROUNDED-ORACLE ECHO: derive the reordering verdict from the pair's own state (`not is_same_field(this,nxt)`) instead of the supplied nxt_references_altered_field query -> exit 2. The verdict's VALUE is genuinely pinned, not erased.
 * atk_9.py EAGER read of nxt.new_name_lower before the operand's kind is known -> exit 2 (the conditional lending is load-bearing).
 * atk_14.py the sibling read-back: build the carried ALTER step, then read ITS OWN new-name slot to name a second build -> exit 2 (constructor grants that slot only for kind==KIND_RENAME).
 * atk_15.py read the OPERAND's has_explicit_column instead of the reducing step's -> exit 2 (never granted; the real method reads only self.field.db_column).
 * atk_16.py TOTAL CORRECTNESS: diverge (unbounded while loop) before returning gold's answer -> exit 2. MustTerminate(6) is load-bearing, so the Ensures are not vacuously satisfiable.
 * atk_18.py read the REDUCING step's own new_name_lower -> exit 2 (no Acc(this.new_name_lower) is lent at all, matching AlterField defining no new_name).
 * atk_19.py build the carried alteration WITH the elidable mark set -> exit 2. The step-6 content pin `not Result()[0][1].elidable` is load-bearing (a real behavioural difference: the optimizer would elide across the carry).

CANDIDATES (5) -- same spec AND verify; every patch MATERIALIZED and RESOLVED:
 * atk_10.py (verifies 25.2s) the DUAL of the repaired hole on the *accept* side: build a KIND_RENAME probe and read ITS new name back to name the carry. Refined: `probe = RenameField(model_name=self.model_name, old_name=self.name, new_name=operation.new_name)` then `name=probe.new_name`. RenameField really does define new_name, so the read is a VALUE. resolve: resolved=True, completed=True, F2P 1/1, P2P 37/37. Correctly admitted -- conditioning it out would be spec-too-strong.
 * atk_11.py (26.6s) the ALTER side of the repaired grant's boundary: build a KIND_ALTER probe, guard-load-bearing column read. Refined via AlterField(model_name=self.model_name, name=self.name, field=self.field) -> probe.field.db_column. resolve: resolved=True, F2P 1/1, P2P 37/37.
 * atk_12.py (29.7s) the REMOVE side of that boundary -- the bundle's own claimed ACCEPT case (pos-remove-probe-column). RemoveField inherits FieldOperation's optional field=, so probe.field.db_column is a value. resolve: resolved=True, F2P 1/1, P2P 37/37. CONFIRMS the grant stops at exactly the right kind: one kind tighter would reject a resolving rival.
 * atk_13.py (28.8s) KIND_OTHER probe reading back the facets still granted unconditionally (model name + field name), load-bearing as the carried step's own model/name. Refined with AddField -- the other-kind FieldOperation that ACCEPTS those two names. resolve: resolved=True, F2P 1/1, P2P 37/37.
 * atk_17.py (25.0s) NEW ANGLE, the elidable facet on a step the reduction BUILDS: the constructor grants `self.elidable == elidable` for EVERY kind and either value, though in the repo elidable is a CLASS attribute (base.py:32, default False) and no field-operation constructor takes an elidable= kwarg. Built an ALTER probe declared elidable and made the read load-bearing in both collapse guards. Refined the way the instance's OWN test suite makes an operation elidable (assignment; tests/migrations/test_optimizer.py:1096-1097), honouring the constructor's Ensures. resolve: resolved=True, F2P 1/1, P2P 37/37. So the unconditioned elidable grant is NOT a hole of the has_explicit_column kind: unlike field/new_name, `elidable` is defined on every Operation and is settable, so the read has a real refinement.

### FALSE POSITIVES I CAUGHT AND DISCARDED (methodology)
Before trusting the five accepts I built a registry-free transcription of the real classes (local_probe.py) and compared each refinement's (shape, surviving-op IDENTITY, carry facets) against gold over 14 boundary pairs (db_column present/absent x same/diff field x same/diff model x elidable on either side). All five candidates are VALUE-IDENTICAL to gold on 14/14 -- consistent with them resolving, and the reason I did not report any of them as a weakness.
I also materialized and resolved two DIAGNOSTIC alternate readings to show the harness would in fact have caught a real defect here, i.e. that my resolve leg is not blind:
 * patch_alt_13_operation.diff -- atk_13's probe read off a bare `Operation()` instead of AddField: local probe RAISES `AttributeError: 'Operation' object has no attribute 'model_name'`; OFFICIAL harness resolved=False, completed=True, attempts=3 (consistent -- not flaky), P2P 36/37, failing 'RenameField should optimize to the other side of AlterField,'. That is the same failure signature the prior BROKEN pass reported. But it is an UNFAITHFUL refinement of atk_13: the model's constructor call carries a model name AND a field name, and the class that accepts both is AddField, not a bare Operation; picking the crashing class would have INVENTED a spec weakness.
 * patch_alt_17_noset.diff -- atk_17's probe WITHOUT the elidable assignment: differs from gold on 5/14 local inputs (it never collapses), so it is not a faithful refinement of an impl whose constructor postcondition says the built step's elidable IS True.
These two are reported as evidence, NOT submitted as attack patches; the resolve leg demonstrably distinguishes resolving from non-resolving refinements on this instance.
Gold-patch control: my materialization pipeline reproduces the bundle's patch.diff BYTE-FOR-BYTE from the base_commit file (patch_gold.diff == patch.diff), so the five attack patches differ from gold only by the intended edit.

### Positive control
pos_control.py (bundle model.py verbatim, gold impl) -> CANDIDATE, verifies in 32.1s.

#### A-LEG / DEEP-MODEL AUDIT (refinement.md)
meta.json: axioms=[], deep_model_references=[]. model.py's axioms region is empty prose and there is NO @ContractOnly / Assume / Inhale / @Predicate anywhere in the file (grepped) -- so the 'no axiom trust point' claim is structurally TRUE, and refinement.md's 8 legs tag out as 6 R + 2 I with NO kind-3 and no A-consumed/A-reference leg to audit. That is the correct tagging for this bundle.
The one leg that reaches OUTSIDE the patched hunk is leg 7 (`super().reduce(operation, app_label)`), which is the substantive deep-model reference, so I audited its correspondence against the REAL Django classes rather than a transcription: extracted the tree at base_commit f9fe062de5 and imported django.db.migrations.operations directly (aleg_check.py, 20/20 obligations OK):
 * (a) AlterField.`__mro__` == [AlterField, FieldOperation, Operation, object] and the class OWNING the next reduce is FieldOperation -- so super() binds FieldOperation.reduce, NOT Operation.reduce. The two earlier revisions mapping.md admits recorded G-CONF fail were each one MRO hop short; the current claim is the right one.
 * (b) FieldOperation.reduce really is `super().reduce(...) or not operation.references_field(self.model_name, self.name, app_label)`.
 * (c) Operation.reduce is the two-arm elidable form with the SELF arm tested FIRST (earlier-step precedence), elidable defaulting to False as a class attribute.
 * (d) the composite FOUR-state exercised on real operation objects: self.elidable -> ('list','OP'); operation.elidable -> ('list','SELF'); neither+no-ref -> ('flag',True); neither+references -> ('flag',False); both elidable -> earlier mark wins. Exactly the model's ([nxt],False)/([this],False)/(None,True)/(None,False), distinguished by IDENTITY not length, and both verdict values reachable -- so modelling the fall-through as a single None or a constant bool would indeed be wrong.
 * (e) every partiality claim the conditional Acc's encode holds on the real classes: new_name defined ONLY on RenameField (and absent from a CONSTRUCTED carried AlterField); RenameField.field is None so.field.db_column raises AttributeError; a bare Operation has no.field; RemoveField CAN be given a field (so the grant correctly stops at ALTER|REMOVE and not one kind tighter -- atk_12's resolve confirms this from the other direction); AddField accepts model_name/name/field (so atk_13 has a real refinement); CreateModel/DeleteModel have name_lower but NO model_name_lower, the calibration note for the deliberately UNconditioned model-name slot; and elidable is settable on a constructed op (atk_17).
 * (f) leg 3's 'I' tag: is_same_field_operation is the unchanged model_name_lower AND name_lower compare, case-folded.
 * (g) at base_commit AlterField.reduce carries the PRE-patch guard, reads operation.new_name exactly once and self.field.db_column exactly once and only off self -- so refinement.md's read-site counts are accurate and the patch touches one method.
One documentation nit, not a defect and not a spec hole: refinement.md's 'No kind-3' section says 'There is no axiomatized callee (A)', which is true of @ContractOnly axioms, but leg 7 IS a deep model of a callee chain outside the changed hunk (FieldOperation.reduce -> Operation.reduce -> references_field). It is modeled deeply and it is correct (verified above, and G-CONF measures it against the real chain called over 101,670 pairs with 0 disagreements), so the refinement claim stands; the label just under-advertises how much of leg 7 is a cross-file model. Nothing about the correspondence is wrong.

#### Scope / residual risk
What I could not break: the discriminating alter-then-alter clause, the unchanged remove arm, the rename carry-across's identity AND all five content pins (kind, model, renamed name, column status, absence of an elidable mark), the four-state fall-through with earlier-step precedence, the reordering verdict's value, total correctness, and the conditional lending of BOTH partial facets on the operand, on the reducing step, and on a step the reduction builds. The three facets whose constructor grant remains unconditional (model_name_lower, name_lower, elidable) are each backed by an ACCEPT-side measurement: reads of them have faithful refinements that RESOLVE (atk_13, atk_17), so conditioning them would be spec-too-strong rather than a repair. Attack budget was 19 same-spec impls across partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, divergence, read-back/probe and eager-read families; 5 verified and all 5 resolved on the official harness. No INCONCLUSIVE runs: every weakness check reached a verdict and every needed resolve completed (completed=True on all 8 harness runs, including the 2 diagnostics).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_18.py`, `atk_19.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_17.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 19 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. 19 attacks encoded, ALL same-spec (adversary same-spec exit 0 on every one; spec region byte-identical, only the impl region edited). 14 REJECTED by the spec; 5 verified as CANDIDATEs; ALL 5 candidate patches materialized and RUN through the OFFICIAL harness (run_resolve) -- every one RESOLVED (F2P 1/1, P2P 37/37, completed=True, attempts=1, flaky=False). No verifying same-spec impl has a faithful refined patch that fails to resolve, so verify=>correct held under every attack I could construct.

### The prior pass's defect is repaired
The previous G-EQ recorded BROKEN on an UNCONDITIONAL constructor grant of has_explicit_column, which let an impl BUILD a KIND_RENAME/KIND_OTHER step purely to read its pinned-column status back (a facet whose repo counterpart cannot exist: RenameField.`__init__` takes no field, so.field is None; a bare Operation has no.field at all). model.py:110-112 now carries the suggested repair, `Ensures(Implies(kind == KIND_ALTER or kind == KIND_REMOVE, Acc(self.has_explicit_column) and self.has_explicit_column == has_explicit_column))`. I re-encoded that exact counterexample in all three of its shapes and all three are now REJECTED for INSUFFICIENT PERMISSION -- the repair holds and is not merely re-described in prose:
 * atk_2 (rename-kind probe, value-carried) -> exit 2; `atk_2.py:292: Method call might fail. There might be insufficient permission to access probe.has_explicit_column.`
 * atk_3 (same read made GUARD-load-bearing) -> exit 2, same insufficient-permission error.
 * atk_4 (KIND_OTHER probe, guard-load-bearing) -> exit 2, same.

### ATTACK-BY-ATTACK (path / weakness result / resolve result)
REJECTED (14) -- same spec, does not verify:
 * atk_1.py THE PREPATCH BUG re-encoded (guard reverted to KIND_REMOVE only) -> exit 2. Verifier: `Postcondition... Implies(((nxt.kind == KIND_ALTER) and is_same_field(this, nxt)),...)` might not hold -- the discriminating clause (G-DIFF) is what catches it. prepatch_reproduced=true.
 * atk_2/atk_3/atk_4 the prior counterexample, three shapes -> exit 2 (insufficient permission), above.
 * atk_5.py PARTIAL-DOMAIN, dual of the bug: collapse same-field ALTER but LOSE the unchanged same-field REMOVE arm -> exit 2; `Postcondition... Implies(((nxt.kind == KIND_REMOVE) and is_same_field(...)),...)`.
 * atk_6.py BOUNDARY: drop the rename branch's pinned-column guard so the carry-across fires even with an explicit column pinned -> exit 2; caught via the elidable fall-through clause (`Implies(not joined_by_field_rule(this,nxt) and this.elidable,...)`), i.e. joined_by_field_rule's boundary is load-bearing.
 * atk_7.py CONTROL-FLOW-EFFECT: test the generic elidable marks BEFORE the method's own same-field rules, so an elidable later step beats the same-field collapse -> exit 2; two postcondition errors (KIND_REMOVE collapse, and len==2 on the rename carry).
 * atk_8.py UNGROUNDED-ORACLE ECHO: derive the reordering verdict from the pair's own state (`not is_same_field(this,nxt)`) instead of the supplied nxt_references_altered_field query -> exit 2. The verdict's VALUE is genuinely pinned, not erased.
 * atk_9.py EAGER read of nxt.new_name_lower before the operand's kind is known -> exit 2 (the conditional lending is load-bearing).
 * atk_14.py the sibling read-back: build the carried ALTER step, then read ITS OWN new-name slot to name a second build -> exit 2 (constructor grants that slot only for kind==KIND_RENAME).
 * atk_15.py read the OPERAND's has_explicit_column instead of the reducing step's -> exit 2 (never granted; the real method reads only self.field.db_column).
 * atk_16.py TOTAL CORRECTNESS: diverge (unbounded while loop) before returning gold's answer -> exit 2. MustTerminate(6) is load-bearing, so the Ensures are not vacuously satisfiable.
 * atk_18.py read the REDUCING step's own new_name_lower -> exit 2 (no Acc(this.new_name_lower) is lent at all, matching AlterField defining no new_name).
 * atk_19.py build the carried alteration WITH the elidable mark set -> exit 2. The step-6 content pin `not Result()[0][1].elidable` is load-bearing (a real behavioural difference: the optimizer would elide across the carry).

CANDIDATES (5) -- same spec AND verify; every patch MATERIALIZED and RESOLVED:
 * atk_10.py (verifies 25.2s) the DUAL of the repaired hole on the *accept* side: build a KIND_RENAME probe and read ITS new name back to name the carry. Refined: `probe = RenameField(model_name=self.model_name, old_name=self.name, new_name=operation.new_name)` then `name=probe.new_name`. RenameField really does define new_name, so the read is a VALUE. resolve: resolved=True, completed=True, F2P 1/1, P2P 37/37. Correctly admitted -- conditioning it out would be spec-too-strong.
 * atk_11.py (26.6s) the ALTER side of the repaired grant's boundary: build a KIND_ALTER probe, guard-load-bearing column read. Refined via AlterField(model_name=self.model_name, name=self.name, field=self.field) -> probe.field.db_column. resolve: resolved=True, F2P 1/1, P2P 37/37.
 * atk_12.py (29.7s) the REMOVE side of that boundary -- the bundle's own claimed ACCEPT case (pos-remove-probe-column). RemoveField inherits FieldOperation's optional field=, so probe.field.db_column is a value. resolve: resolved=True, F2P 1/1, P2P 37/37. CONFIRMS the grant stops at exactly the right kind: one kind tighter would reject a resolving rival.
 * atk_13.py (28.8s) KIND_OTHER probe reading back the facets still granted unconditionally (model name + field name), load-bearing as the carried step's own model/name. Refined with AddField -- the other-kind FieldOperation that ACCEPTS those two names. resolve: resolved=True, F2P 1/1, P2P 37/37.
 * atk_17.py (25.0s) NEW ANGLE, the elidable facet on a step the reduction BUILDS: the constructor grants `self.elidable == elidable` for EVERY kind and either value, though in the repo elidable is a CLASS attribute (base.py:32, default False) and no field-operation constructor takes an elidable= kwarg. Built an ALTER probe declared elidable and made the read load-bearing in both collapse guards. Refined the way the instance's OWN test suite makes an operation elidable (assignment; tests/migrations/test_optimizer.py:1096-1097), honouring the constructor's Ensures. resolve: resolved=True, F2P 1/1, P2P 37/37. So the unconditioned elidable grant is NOT a hole of the has_explicit_column kind: unlike field/new_name, `elidable` is defined on every Operation and is settable, so the read has a real refinement.

### FALSE POSITIVES I CAUGHT AND DISCARDED (methodology)
Before trusting the five accepts I built a registry-free transcription of the real classes (local_probe.py) and compared each refinement's (shape, surviving-op IDENTITY, carry facets) against gold over 14 boundary pairs (db_column present/absent x same/diff field x same/diff model x elidable on either side). All five candidates are VALUE-IDENTICAL to gold on 14/14 -- consistent with them resolving, and the reason I did not report any of them as a weakness.
I also materialized and resolved two DIAGNOSTIC alternate readings to show the harness would in fact have caught a real defect here, i.e. that my resolve leg is not blind:
 * patch_alt_13_operation.diff -- atk_13's probe read off a bare `Operation()` instead of AddField: local probe RAISES `AttributeError: 'Operation' object has no attribute 'model_name'`; OFFICIAL harness resolved=False, completed=True, attempts=3 (consistent -- not flaky), P2P 36/37, failing 'RenameField should optimize to the other side of AlterField,'. That is the same failure signature the prior BROKEN pass reported. But it is an UNFAITHFUL refinement of atk_13: the model's constructor call carries a model name AND a field name, and the class that accepts both is AddField, not a bare Operation; picking the crashing class would have INVENTED a spec weakness.
 * patch_alt_17_noset.diff -- atk_17's probe WITHOUT the elidable assignment: differs from gold on 5/14 local inputs (it never collapses), so it is not a faithful refinement of an impl whose constructor postcondition says the built step's elidable IS True.
These two are reported as evidence, NOT submitted as attack patches; the resolve leg demonstrably distinguishes resolving from non-resolving refinements on this instance.
Gold-patch control: my materialization pipeline reproduces the bundle's patch.diff BYTE-FOR-BYTE from the base_commit file (patch_gold.diff == patch.diff), so the five attack patches differ from gold only by the intended edit.

### Positive control
pos_control.py (bundle model.py verbatim, gold impl) -> CANDIDATE, verifies in 32.1s.

#### A-LEG / DEEP-MODEL AUDIT (refinement.md)
meta.json: axioms=[], deep_model_references=[]. model.py's axioms region is empty prose and there is NO @ContractOnly / Assume / Inhale / @Predicate anywhere in the file (grepped) -- so the 'no axiom trust point' claim is structurally TRUE, and refinement.md's 8 legs tag out as 6 R + 2 I with NO kind-3 and no A-consumed/A-reference leg to audit. That is the correct tagging for this bundle.
The one leg that reaches OUTSIDE the patched hunk is leg 7 (`super().reduce(operation, app_label)`), which is the substantive deep-model reference, so I audited its correspondence against the REAL Django classes rather than a transcription: extracted the tree at base_commit f9fe062de5 and imported django.db.migrations.operations directly (aleg_check.py, 20/20 obligations OK):
 * (a) AlterField.`__mro__` == [AlterField, FieldOperation, Operation, object] and the class OWNING the next reduce is FieldOperation -- so super() binds FieldOperation.reduce, NOT Operation.reduce. The two earlier revisions mapping.md admits recorded G-CONF fail were each one MRO hop short; the current claim is the right one.
 * (b) FieldOperation.reduce really is `super().reduce(...) or not operation.references_field(self.model_name, self.name, app_label)`.
 * (c) Operation.reduce is the two-arm elidable form with the SELF arm tested FIRST (earlier-step precedence), elidable defaulting to False as a class attribute.
 * (d) the composite FOUR-state exercised on real operation objects: self.elidable -> ('list','OP'); operation.elidable -> ('list','SELF'); neither+no-ref -> ('flag',True); neither+references -> ('flag',False); both elidable -> earlier mark wins. Exactly the model's ([nxt],False)/([this],False)/(None,True)/(None,False), distinguished by IDENTITY not length, and both verdict values reachable -- so modelling the fall-through as a single None or a constant bool would indeed be wrong.
 * (e) every partiality claim the conditional Acc's encode holds on the real classes: new_name defined ONLY on RenameField (and absent from a CONSTRUCTED carried AlterField); RenameField.field is None so.field.db_column raises AttributeError; a bare Operation has no.field; RemoveField CAN be given a field (so the grant correctly stops at ALTER|REMOVE and not one kind tighter -- atk_12's resolve confirms this from the other direction); AddField accepts model_name/name/field (so atk_13 has a real refinement); CreateModel/DeleteModel have name_lower but NO model_name_lower, the calibration note for the deliberately UNconditioned model-name slot; and elidable is settable on a constructed op (atk_17).
 * (f) leg 3's 'I' tag: is_same_field_operation is the unchanged model_name_lower AND name_lower compare, case-folded.
 * (g) at base_commit AlterField.reduce carries the PRE-patch guard, reads operation.new_name exactly once and self.field.db_column exactly once and only off self -- so refinement.md's read-site counts are accurate and the patch touches one method.
One documentation nit, not a defect and not a spec hole: refinement.md's 'No kind-3' section says 'There is no axiomatized callee (A)', which is true of @ContractOnly axioms, but leg 7 IS a deep model of a callee chain outside the changed hunk (FieldOperation.reduce -> Operation.reduce -> references_field). It is modeled deeply and it is correct (verified above, and G-CONF measures it against the real chain called over 101,670 pairs with 0 disagreements), so the refinement claim stands; the label just under-advertises how much of leg 7 is a cross-file model. Nothing about the correspondence is wrong.

#### Scope / residual risk
What I could not break: the discriminating alter-then-alter clause, the unchanged remove arm, the rename carry-across's identity AND all five content pins (kind, model, renamed name, column status, absence of an elidable mark), the four-state fall-through with earlier-step precedence, the reordering verdict's value, total correctness, and the conditional lending of BOTH partial facets on the operand, on the reducing step, and on a step the reduction builds. The three facets whose constructor grant remains unconditional (model_name_lower, name_lower, elidable) are each backed by an ACCEPT-side measurement: reads of them have faithful refinements that RESOLVE (atk_13, atk_17), so conditioning them would be spec-too-strong rather than a repair. Attack budget was 19 same-spec impls across partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, divergence, read-back/probe and eager-read families; 5 verified and all 5 resolved on the official harness. No INCONCLUSIVE runs: every weakness check reached a verdict and every needed resolve completed (completed=True on all 8 harness runs, including the 2 diagnostics).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** METHOD (independent of the bundle's own axiom_check.py / conformance_check.py, which I did not rely on). I created my own worktree at base_commit f9fe062de5fc0896d6bbbf3f260b5c44473b3c77 () and applied benchmark-verified/django__django-16595/patch.diff, per the brief that the PATCHED tree is the reference for the modeled function. I then wrote a harness that, for each real (AlterField self, arbitrary operand) pair: abstracts the pair onto the MigrationStep carrier per mapping.md §2 (runtime class -> kind tag; injective case-folded name interner str->int; field.db_column is not None -> has_explicit_column; op.elidable -> elidable; op.references_field(self.model_name, self.name, app_label) -- the REAL predicate, called -- -> the nxt_references_altered_field ARGUMENT); CALLS the real patched AlterField.reduce (the genuine chain through FieldOperation.reduce at fields.py:69-72 and Operation.reduce at base.py:129-139, including each operand class's own references_field override, e.g. RenameField's at fields.py:337-340 -- not a replica); normalises list -> (list, False) and bool b -> (None, b); and then evaluates EVERY ONE of model.py's ten postcondition clauses (P1 exclusivity/bool-normalisation, P2 same-field REMOVE collapse, P3 same-field ALTER collapse [the patch delta], P4 symmetry, P5 rename carry-across shape AND full carried-step content, P6 earlier-elidable precedence, P7 later-elidable, P8 fall-through verdict VALUE, P9 different-field verdict, P10 combined-exactly-when) against that real answer. A violated clause = the spec asserting something the real callee does not do = UNFAITHFUL. None violated.

SPECIFIC OVER-STRENGTH HYPOTHESES I TRIED TO BREAK, ALL SURVIVED:
1. P5's carried-step content pins (the strongest clauses in the spec: kind==KIND_ALTER, model_name_lower==this.model_name_lower, name_lower==nxt.new_name_lower, has_explicit_column==this.has_explicit_column, not elidable, plus freshness `is not nxt and is not this`). Exercised 563-640 times per campaign plus 4 dedicated corners. I re-abstracted the REAL constructed AlterField (fields.py:258-264) and compared every pinned facet; all hold, including rename-to-the-same-name, case-shifted new name (RenameField('BOOK','TITLE','TiTlE')), operand-elidable, and self-elidable renames. Freshness holds because it is a genuine construction.
2. Guard-vs-fall-through precedence. The spec's P2/P3/P4/P5 are UNCONDITIONAL on the elidable marks, so they claim AlterField.reduce's own guards beat super()'s elidable arms. Verified real: 'same-field alter, operand elidable' -> [nxt] (not [this]); 'same-field remove, self elidable' -> [nxt]; 'rename carry, self elidable' and 'rename carry, operand elidable' both -> [nxt, carried]. The real method returns before delegating, so the unconditional form is correct, not over-strong.
3. P6's earlier-step precedence over P7 (`not this.elidable and nxt.elidable` on P7). Real Operation.reduce tests `if self.elidable` first, so [operation] wins when both are elidable; the both-elidable case is covered in the grid and 12k+ times in fuzz.
4. P8/P9's fall-through VALUE claim `Result()[1] == (not nxt_references_altered_field)`. This is where the two prior recorded G-CONF failures lived, so I attacked it hardest. Both bool values are reachable and both matched: FieldOperation.reduce is `super().reduce(...) or not operation.references_field(...)`, and since the Operation.reduce base returns False on the neither-elidable path, the answer is exactly `not references_field(...)`. Confirmed on operands whose references_field is a nontrivial override (RenameField: True for rename-to-old-name AND rename-to-new-name) and on remote reaches (ForeignObject with from_fields=['title'] -> refs True, verdict False). No constant reproduces it, consistent with the bundle's claim.
5. The SAME-field pair that reaches the fall-through because the rename guard's `self.field.db_column is None` rejects it. This is why P6-P10 are guarded on `not joined_by_field_rule(...)` rather than on 'different field'. Verified: AlterField('Book','title',CF(db_column='c')) + RenameField('Book','title','subtitle') -> real None/False, and the model's joined_by_field_rule is correctly False there. Also tested db_column == the field name.
6. P10's iff (`(Result()[0] is not None) == (joined_by_field_rule or elides_to_one_step)`) -- the tightest clause, since it forbids a list on every other input. Held on all 122k+ inputs; no real input returns a list outside those two conditions, and none returns a non-list inside them.
7. Aliasing: `this is nxt` (the same object handed twice), elidable and not. Real -> [nxt]; the spec's identity pins are satisfied (nxt.real is this.real, so `Result()[0][0] is nxt` holds and P5 is not triggered).
8. Partiality/PRECONDITION-narrowing check: the conditional resource lending (`Requires(Implies(nxt.kind == KIND_RENAME, Acc(nxt.new_name_lower, 1/2)))`, and the constructor's conditional grants on new_name_lower / has_explicit_column) narrows nothing in the VALUE domain -- every operand pair remains admissible, which my harness confirms by never having to exclude an input for precondition reasons (0 skips; the only Requires is this.kind == KIND_ALTER, matching that the method IS AlterField.reduce). The narrowing is on permission, and it mirrors real partial attributes I confirmed in the tree: new_name is defined only by RenameField.`__init__` (fields.py:273-276); AlterField.`__init__` (fields.py:204) and RemoveField (fields.py:154) define none; RenameField takes no field, so its.field is None and.field.db_column is an AttributeError; a bare Operation has no.field at all. So these are strengthenings that reject unfaithful impls, not spec-too-strong claims about behavior. I also confirmed the calibration boundary the bundle claims: RemoveField DOES accept a field (fields.py:154 inherits FieldOperation's optional param), which is why the constructor grant extends to KIND_REMOVE -- conditioning it out would reject a resolving rival.
9. No AlterField/RemoveField subclasses exist in the tree that could make the kind tag non-injective (grepped: only fields.py:198 and fields.py:154), so the isinstance-tuple <-> kind-disjunction refinement is sound.

DELTA CONTROL (guards against the trap the brief warns about): I did NOT compare against the base version. I confirmed the modeled function tracks the PATCHED behavior and that the spec is nonetheless discriminating: model.py verifies (Verification successful, 34.71s, pinned scripts/nagini_verify.sh), while model_prepatch.py -- same spec, pre-patch impl -- FAILS on precisely the delta clause: 'Postcondition of reduce might not hold. Assertion Implies(((nxt.kind == KIND_ALTER) and is_same_field(this, nxt)), ((Result()[0] is not None) and (len(Result()[0]) == 1) and (Result()[0][0] is nxt)))'. So the spec both matches the real patched callee and senses the bug.

**CONCLUSION:** the spec is faithful. Every postcondition is a true statement about the real patched AlterField.reduce on every input I could construct, including the whole abstract input grid instantiated with real witnesses. I found no diverging input, so I have no basis to claim spec-too-strong or drift. Worked only in /tmp; the bundle was not modified (verified by running the verifier read-only against it and writing all harnesses).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** MEASURED, not inherited. No relaxation in this bundle: no RELAXED_LEAKAGE.md anywhere under benchmark-verified/django__django-16595/, and meta.json has no relaxed_leakage key ([k for k in meta if 'relax' in k.lower()] == []). So this is judged as a plain full-strength leakage review.

What I ran:
1. Spec view projected myself with swebench_unified.markers.spec_view(nagini backend) -> gp3_specview.txt, sha256 eb9f76bb31069cea5ace49b8825322f8bb34b49fcc9cf1af68ef55967356db89. markers.same_spec(model.py, model_prepatch.py) == True and spec_view(gold) == spec_view(prepatch) byte-identical, so the twin pair differs ONLY in the impl region (diff = one line: `if nxt.kind == KIND_REMOVE and is_same_field(...)` vs `if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) and is_same_field(...)`). The spec view is therefore genuinely the same document either side of the edit.
2. Core gates re-derived, not read off meta.json. scripts/nagini_verify.sh on my /tmp copies: model.py exit 0 (verifies), model_prepatch.py exit 1 with `Postcondition of reduce might not hold. Assertion Implies(((nxt.kind == KIND_ALTER) and is_same_field(this, nxt)),...)`. G-GOLD/G-DIFF/G-VERIFY reproduce.
3. Narration-strip (the load-bearing test). Rebuilt both twins with the entire module docstring replaced by a stub and EVERY non-marker comment and helper docstring deleted, leaving only signatures + Requires/Ensures + pure bodies: model_gold_bare.py exit 0, model_pre_bare.py exit 1 on the same KIND_ALTER postcondition. So the discrimination is carried wholly by the FORMAL contracts; the prose is descriptive scaffolding and removing all of it changes no verdict. A leaking sentence would be one whose removal costs the spec its discriminating power -- there is none here.
4. Redundancy check: even with the case-(2) Ensures AND the symmetry Ensures both deleted from prepatch, it still fails, now on the biconditional `(Result()[0] is not None) == (joined_by_field_rule(this, nxt) or elides_to_one_step(this, nxt))` (via joined_by_field_rule's KIND_ALTER disjunct). The behaviour is pinned in three independent places, i.e. it is a property of the specified behaviour rather than a single planted tell.

Leak-vocabulary sweep over the spec view: zero hits for fix/fixed/patch/bug/regression/previously/used to/no longer/missing/omitted/oversight/should now/added/widen/gold/commit/PR/upstream, zero repo identifiers (no AlterField/RemoveField/RenameField/isinstance/fields.py/django/db_column/optimizer/super()/line numbers, no test names such as test_alter_alter_field). The only repo-ish token is the instance id in the docstring title and `reduce` as the function name, both structural bundle framing rather than edit disclosure. Line 3 explicitly frames the doc as "stated as desired behaviour, not as an edit" and the text keeps that stance.

The closest-call lines, and why each is within the public problem_statement: (a) lines 5-12 name both collapsing cases (remove, and alter-again); (b) lines 20-23 "The behaviour must be symmetric... Failing to collapse the alter-then-alter case (case 2) leaves a redundant alteration that should not survive."; (c) lines 213-218 the symmetry Ensures. These do state the discriminator -- but the public problem_statement states it MORE strongly and in repo terms: its title is "Migration optimizer does not reduce multiple AlterField", it explains "AlterField.reduce does not consider the case where operation is also an AlterField", and it closes by spelling out the fix as source code, `if isinstance(operation, AlterField) and self.is_same_field_operation(operation): return [operation]`. The spec view says strictly less than that: it names the desired behaviour but never the guard, the isinstance tuple, the file, or the branch. Nothing in the spec view is derivable only from hints_text or from the diff. Cross-checked hints_text separately and used none of it.

Also checked for bundle-to-reviewer address per my instructions: grepped refinement.md, mapping.md, model.py, model_prepatch.py, axiom_check.py, conformance_check.py for attacker/panel/G-PANEL/honest verdict/submit_result/record-NO-LEAKAGE style instructions -- no hits. No file in this bundle attempts to tell a reviewer what to submit; nothing to report on that axis.

Out of scope for this gate but noted for the record: meta.json carries G-EQ fail and G-PANEL-1 fail (atk_11.py verifies yet breaks P2P "RenameField should optimize to the other side of AlterField"), i.e. a spec-too-weak finding on the rename branch. That is a strength question, not a leakage one, and does not affect this verdict.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
