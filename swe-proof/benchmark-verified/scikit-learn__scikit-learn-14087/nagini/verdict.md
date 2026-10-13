# P2 adversarial audit — scikit-learn__scikit-learn-14087

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 24 admissible attacks re-run of 26 submitted, none breaks the spec; positive control verifies (2 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 26 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_18.py`, `atk_19.py`, `atk_25.py`, `atk_26.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 9 | `atk_6.py`, `atk_7.py`, `atk_16.py`, `atk_17.py`, `atk_20.py`, `atk_21.py`, `atk_22.py`, `atk_23.py`, `atk_24.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_4.py`, `atk_15.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (26):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,9 +295,8 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
-    use_joint_layout = resolved_strategy != INDEPENDENT
+    # PREPATCH (site 1): drive the read arity by the UNRESOLVED form.
+    use_joint_layout = unresolved_form != INDEPENDENT
     w = read_across_folds(use_joint_layout, table_axes, summary_token)
     return w
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,10 +295,8 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
-    use_joint_layout = resolved_strategy != INDEPENDENT
-    w = read_across_folds(use_joint_layout, table_axes, summary_token)
+    # UNGROUNDED ORACLE ECHO (site 1): deliver the token with no read at all.
+    w = summary_token
     return w
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,8 +295,9 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
+    # EXTRA READ AT A SELF-NAMED RANK (site 1): a second index expression
+    # against a rank the layout may not have, in ADDITION to the honest read.
+    joint_extra = read_across_folds(True, 4, summary_token)
     use_joint_layout = resolved_strategy != INDEPENDENT
     w = read_across_folds(use_joint_layout, table_axes, summary_token)
     return w
```

Attack 4 — `atk_4.py` → not a counterexample (the checker could not translate this program, so the spec never judged it) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,8 +295,10 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
+    # FORGE (site 1): try to conjure a summary table laid out at a rank of this
+    # body's own choosing, then read against it.
+    Fold(summary_table(4))
+    extra = read_across_folds(True, 4, summary_token)
     use_joint_layout = resolved_strategy != INDEPENDENT
     w = read_across_folds(use_joint_layout, table_axes, summary_token)
     return w
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,10 +295,12 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
+    # CONTROL-FLOW EFFECT / TOTALITY (site 1): honest read, then diverge.
     use_joint_layout = resolved_strategy != INDEPENDENT
     w = read_across_folds(use_joint_layout, table_axes, summary_token)
+    spin = 0
+    while spin >= 0:
+        spin = spin + 1
     return w
     # impl-end
 
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,9 +295,10 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
+    # DUPLICATE HONEST READ (site 1): the arity-matching read of the held table
+    # performed twice; the first result is unused.
     use_joint_layout = resolved_strategy != INDEPENDENT
+    first = read_across_folds(use_joint_layout, table_axes, summary_token)
     w = read_across_folds(use_joint_layout, table_axes, summary_token)
     return w
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,10 +295,11 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
+    # VALUE PROVENANCE (site 1): perform the honest arity-matching read, discard
+    # its result, deliver the token.
     use_joint_layout = resolved_strategy != INDEPENDENT
-    w = read_across_folds(use_joint_layout, table_axes, summary_token)
+    unused = read_across_folds(use_joint_layout, table_axes, summary_token)
+    w = summary_token
     return w
     # impl-end
 
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -360,16 +360,7 @@
     Ensures(Implies(family_has_mixing, mixing_selected()))
     # post-conditions-end
     # impl-start
-    if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
-        entry = select_mixing_value(family_has_mixing, selected_index,
-                                    candidates_len,
-                                    mixing_value)  # type: Optional[int]
-    else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
-        entry = None
+    # PREPATCH (site 2): always record the table-derived value.
+    entry = mixing_value  # type: Optional[int]
     return entry
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -361,15 +361,12 @@
     # post-conditions-end
     # impl-start
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
-        entry = select_mixing_value(family_has_mixing, selected_index,
-                                    candidates_len,
+        # PRIOR COUNTEREXAMPLE RE-ENCODED: select at position `candidates_len`,
+        # declaring the held table one entry longer than it is.
+        entry = select_mixing_value(family_has_mixing, candidates_len,
+                                    candidates_len + 1,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
     return entry
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -361,15 +361,13 @@
     # post-conditions-end
     # impl-start
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
-        entry = select_mixing_value(family_has_mixing, selected_index,
-                                    candidates_len,
+        # Same forged-bound shape, offsetting the REAL selected position past
+        # the end of the real table.
+        entry = select_mixing_value(family_has_mixing,
+                                    selected_index + candidates_len,
+                                    selected_index + candidates_len + 1,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
     return entry
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -360,16 +360,13 @@
     Ensures(Implies(family_has_mixing, mixing_selected()))
     # post-conditions-end
     # impl-start
-    if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
-        entry = select_mixing_value(family_has_mixing, selected_index,
+    # PARTIAL DOMAIN (site 2): guard on the candidate table's extent instead of
+    # on the regularisation family.
+    if candidates_len > 1:
+        entry = select_mixing_value(True, selected_index,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
     return entry
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -360,16 +360,12 @@
     Ensures(Implies(family_has_mixing, mixing_selected()))
     # post-conditions-end
     # impl-start
-    if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
-        entry = select_mixing_value(family_has_mixing, selected_index,
+    # BOUNDARY (site 2): guard on the selected position instead of the family.
+    if selected_index > 0:
+        entry = select_mixing_value(True, selected_index,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
     return entry
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -360,16 +360,13 @@
     Ensures(Implies(family_has_mixing, mixing_selected()))
     # post-conditions-end
     # impl-start
+    # RECORD-CORRECTING (site 2): select from the table for EVERY family, then
+    # overwrite the record with the absent marker for the no-mixing family.
+    taken = select_mixing_value(True, selected_index, candidates_len,
+                                mixing_value)
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
-        entry = select_mixing_value(family_has_mixing, selected_index,
-                                    candidates_len,
-                                    mixing_value)  # type: Optional[int]
+        entry = taken  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
     return entry
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -360,16 +360,15 @@
     Ensures(Implies(family_has_mixing, mixing_selected()))
     # post-conditions-end
     # impl-start
+    # CONTROL-FLOW EFFECT / TOTALITY (site 2): right record, then diverge.
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
         entry = select_mixing_value(family_has_mixing, selected_index,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
+    spin = 0
+    while spin >= 0:
+        spin = spin + 1
     return entry
     # impl-end
```

Attack 15 — `atk_15.py` → not a counterexample (the checker could not translate this program, so the spec never judged it) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -361,15 +361,15 @@
     # post-conditions-end
     # impl-start
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
         entry = select_mixing_value(family_has_mixing, selected_index,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
+        # FORGE (site 2): conjure a table whose entries this body declares real,
+        # and one entry longer than the table it was handed.
+        Fold(candidate_table(True, candidates_len + 1))
+        extra = select_mixing_value(True, candidates_len,
+                                    candidates_len + 1, mixing_value)
         entry = None
     return entry
     # impl-end
```

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -361,15 +361,12 @@
     # post-conditions-end
     # impl-start
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
-        entry = select_mixing_value(family_has_mixing, selected_index,
+        # DECLARED RESIDUAL FREEDOM (refinement.md D): select at a DIFFERENT
+        # but provably IN-RANGE position of the held candidate table.
+        entry = select_mixing_value(family_has_mixing, 0,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
     return entry
     # impl-end
```

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -361,15 +361,14 @@
     # post-conditions-end
     # impl-start
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
+        # An EXTRA in-range selection of the held table, in addition to the
+        # delivering one.
+        extra = select_mixing_value(family_has_mixing, 0, candidates_len,
+                                    mixing_value)
         entry = select_mixing_value(family_has_mixing, selected_index,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
     return entry
     # impl-end
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,10 +295,10 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
+    # VACUITY CONTROL (site 1): if this VERIFIES the contract path is dead.
     use_joint_layout = resolved_strategy != INDEPENDENT
     w = read_across_folds(use_joint_layout, table_axes, summary_token)
+    Assert(False)
     return w
     # impl-end
 
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -360,16 +360,13 @@
     Ensures(Implies(family_has_mixing, mixing_selected()))
     # post-conditions-end
     # impl-start
+    # VACUITY CONTROL (site 2): if this VERIFIES the contract path is dead.
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
         entry = select_mixing_value(family_has_mixing, selected_index,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
+    Assert(False)
     return entry
     # impl-end
```

Attack 20 — `atk_20.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -361,15 +361,16 @@
     # post-conditions-end
     # impl-start
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
         entry = select_mixing_value(family_has_mixing, selected_index,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
+    if candidates_len < 1:
+        # DEAD IN THE MODEL (Requires candidates_len >= 1). If the model's
+        # admissible domain is NARROWER than reality this refines to a LIVE
+        # out-of-range selection.
+        dead = select_mixing_value(True, candidates_len, candidates_len + 1,
+                                   mixing_value)
     return entry
     # impl-end
```

Attack 21 — `atk_21.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -361,15 +361,14 @@
     # post-conditions-end
     # impl-start
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
-        entry = select_mixing_value(family_has_mixing, selected_index,
+        # Reversed position: in-range in the model for every admissible input.
+        # In reality `selected_index` is an ARRAY, so this probes whether the
+        # int abstraction hides an element that reverses out of range.
+        entry = select_mixing_value(family_has_mixing,
+                                    candidates_len - 1 - selected_index,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
     return entry
     # impl-end
```

Attack 22 — `atk_22.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -361,15 +361,10 @@
     # post-conditions-end
     # impl-start
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
-        entry = select_mixing_value(family_has_mixing, selected_index,
+        entry = select_mixing_value(family_has_mixing, candidates_len - 1,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
         entry = None
     return entry
     # impl-end
```

Attack 23 — `atk_23.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,10 +295,11 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
     use_joint_layout = resolved_strategy != INDEPENDENT
     w = read_across_folds(use_joint_layout, table_axes, summary_token)
+    if table_axes == 5:
+        # DEAD IN THE MODEL (table_axes == table_rank(resolved) in {3,4}).
+        w = read_across_folds(True, 5, summary_token)
     return w
     # impl-end
 
```

Attack 24 — `atk_24.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,9 +295,12 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
-    use_joint_layout = resolved_strategy != INDEPENDENT
+    # Drive the arity off the UNRESOLVED form where it provably agrees with the
+    # resolved strategy, else off the resolved one.
+    if unresolved_form == resolved_strategy:
+        use_joint_layout = unresolved_form != INDEPENDENT
+    else:
+        use_joint_layout = resolved_strategy != INDEPENDENT
     w = read_across_folds(use_joint_layout, table_axes, summary_token)
     return w
     # impl-end
```

Attack 25 — `atk_25.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,10 +295,10 @@
     Ensures(summary_table(table_axes))
     # post-conditions-end
     # impl-start
-    # Address the table with the arity determined by the strategy actually in
-    # effect, so the index arity always equals the table's axis rank.
-    use_joint_layout = resolved_strategy != INDEPENDENT
-    w = read_across_folds(use_joint_layout, table_axes, summary_token)
+    # SELF-CONSISTENT FORGED RANK (site 1): always request the joint read and
+    # name rank 4 for it, so gather_arity(True)==4 holds of ITSELF -- but the
+    # held table's actual rank may be 3.
+    w = read_across_folds(True, 4, summary_token)
     return w
     # impl-end
 
```

Attack 26 — `atk_26.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -361,15 +361,14 @@
     # post-conditions-end
     # impl-start
     if family_has_mixing:
-        # The family carries a mixing parameter: select the value from the
-        # candidate table and record it.
         entry = select_mixing_value(family_has_mixing, selected_index,
                                     candidates_len,
                                     mixing_value)  # type: Optional[int]
     else:
-        # No mixing parameter for this family: the candidate table holds only
-        # the absent placeholder, so nothing is selected from it — record the
-        # explicit absent marker.
+        # Select from the PLACEHOLDER table at an in-range position, then record
+        # the marker anyway (no Fold; uses the resource the step actually holds).
+        extra = select_mixing_value(False, selected_index, candidates_len,
+                                    mixing_value)
         entry = None
     return entry
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) on scikit-learn__scikit-learn-14087 nagini. VERDICT: SOUND. 26 same-spec attacks + positive control, all run; every CANDIDATE materialized as a faithful refined patch and RUN through the official harness. No verifying wrong impl's patch failed to resolve.

#### The recorded fail is stale: the spec was repaired
verdict.md / meta.json record G-EQ=fail against model.py sha256 424b714a624b696f00a181950ac74581b6f0b66eaa85ac94e48b52e9027a855e, with counterexample atk_8 = 'site-2 forged selection bound' (select at position candidates_len declaring the table candidates_len+1 long). The model.py IN THE BUNDLE TODAY is sha256 5436d5460e959dbe6d4bcdf56364e9903d2a60ffde2212e627ce3edd3611f6f4 (mtime 19:36, i.e. AFTER the 19:08 fail was stamped), and it CONTAINS the repair the prior pass itself prescribed: candidate_table now carries the extent -- candidate_table(holds_mixing_values, actual_len) -- and select_mixing_value requires candidate_table(holds_mixing_values, candidates_len), so the bound a selection is checked against is the HELD table's own extent rather than a number the caller names.

Per MEMORY 'SPEC-MOVED is about the record, not the bytes' I did NOT inherit the label: I re-encoded the prior counterexample verbatim in shape and re-ran it. RESULT: the prior counterexample is now REJECTED. atk_9  (select at candidates_len, declaring candidates_len+1) -> weakness exit 2; verifier: 'The precondition of method select_mixing_value might not hold. There might be insufficient permission to access candidate_table(holds_mixing_values, candidates_len).' atk_10 (same shape, offsetting the REAL position past the end) -> weakness exit 2; same message. The site-1-style held-resource repair has been propagated to site 2 and it works.

#### COMMANDS (from repo root swe-proof), D=
  python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-14087 $D/<atk>.py   # all 27 exit 0
  python -m swebench_unified.adversary weakness  nagini scikit-learn__scikit-learn-14087 $D/<atk>.py   # 0=CANDIDATE, 2=rejected
  bash scripts/nagini_verify.sh $D/<atk>.py                                                           # exact error text
  python $D/route.py <name>   # wraps harness.run_resolve + build_one's OWN attribution helpers
Generated by $D/gen.py from $D/base_model.py, a byte-identical copy of the bundle model.py (diff base_model.py positive_control.py empty). Only the two impl regions are spliced; all 27 files pass same-spec exit 0. Weakness/verify/resolve all ran 3-at-a-time as background jobs (drivers run_weakness.sh / run_verify.sh / run_resolve.sh) because each Nagini check spawns a JVM+Z3.

#### Positive control / vacuity
  positive_control.py (byte-identical to bundle model.py) -> weakness exit 0 (verifies, 12s). NON-VACUITY OK.
  atk_18 (site-1 Assert(False)) -> REJECTED 'Assert might fail. Assertion False might not hold.'
  atk_19 (site-2 Assert(False)) -> REJECTED same. Both contract paths are REACHABLE, so neither proof is vacuous (MEMORY: 'Guarded self-calls can go vacuous' -- Assert(False) is the control).

#### 15 REJECTED ATTACKS (spec correctly turns each down), with the verifier's own words
  atk_1  PREPATCH SITE 1 (unresolved operand drives the read arity) <= PREPATCH REPRODUCED
         'precondition of method read_across_folds might not hold. Assertion (gather_arity(use_joint_layout) == table_rank) might not hold.'
  atk_8  PREPATCH SITE 2 (unconditional table value, never the marker) <= PREPATCH REPRODUCED
         'Postcondition of mixing_record might not hold. Assertion Implies((not family_has_mixing), (Result() is None)) might not hold.'
  atk_2  ungrounded-oracle echo site 1 (w = summary_token, no read at all)
         'Postcondition of gather_per_class might not hold. There might be insufficient permission to access read_admissible(table_axes).'
  atk_3  EXTRA read at a SELF-NAMED rank in ADDITION to the honest read
         'precondition of read_across_folds ... insufficient permission to access summary_table(table_rank).'  <= site-1 held-table resource WORKS
  atk_25 SELF-CONSISTENT forged rank REPLACING the honest read (read_across_folds(True, 4, tok): gather_arity(True)==4 holds of ITSELF)
         'precondition of read_across_folds ... insufficient permission to access summary_table(table_rank).'  <= a self-consistent rank is not the HELD table's
atk_4  Fold(summary_table(4)) forge -> 'Translation failed / Invalid program: abstract.predicate.fold' (structurally un-forgeable: a front-end refusal, so it counts in neither tally -- the forgery is unexpressible rather than rejected by a clause) atk_15 Fold(candidate_table(True, candidates_len + 1)) forge -> the same abstract.predicate.fold refusal at translation (also counts in neither tally) atk_5  control-flow-effect/totality site 1: honest read then diverge -> 'Obligation leak check failed.

Loop might not take all unsatisfied obligations from the context.' atk_14 control-flow-effect/totality site 2: right record then diverge -> same obligation-leak rejection (MustTerminate at the method level does its job) atk_9  PRIOR RECORDED COUNTEREXAMPLE re-encoded (forged selection bound) -> insufficient permission to access candidate_table(holds_mixing_values, candidates_len) atk_10 forged bound, offsetting the real position past the end -> same atk_13 record-correcting (select for EVERY family, then overwrite with the marker) -> same insufficient-permission on candidate_table: the placeholder table is never averaged atk_26 select from the PLACEHOLDER table at an in-range position, record the marker anyway (no Fold; uses the resource actually held)
         'precondition of select_mixing_value might not hold. Assertion holds_mixing_values might not hold.'  <= partiality is real
  atk_11 partial-domain site 2 (guard on candidates_len > 1 instead of the family) -> 'Postcondition ... Implies(family_has_mixing, ((Result() is not None) and (Result() == mixing_value))) might not hold.'
  atk_12 boundary site 2 (guard on selected_index > 0 instead of the family) -> same postcondition rejection

#### 11 CANDIDATES (verify) -- EVERY ONE MATERIALIZED AND RUN THROUGH THE OFFICIAL HARNESS
INFRA CONTROL FIRST: gold_control, materialized by the SAME generator ($D/mkpatch.py) -> resolved=TRUE, F2P 3/3, P2P 172/172. Its +/- lines are BYTE-IDENTICAL to the dataset gold patch (checked programmatically), so the generator and the oracle are both sound here and a non-resolve would have carried information (cf. `_oracle_cannot_refute_here`).

All 9 attack patches apply cleanly at base_commit a5743ed36f (git apply --check). atk_6  duplicate honest read of the held table, deliver the second   -> resolved=TRUE F2P 3/3 P2P 172/172 atk_7  value provenance: honest read discarded, deliver the token    -> resolved=TRUE F2P 3/3 P2P 172/172 atk_16 select at ANOTHER in-range position (position 0)              -> resolved=TRUE F2P 3/3 P2P 172/172 atk_17 EXTRA in-range selection in addition to the delivering one    -> resolved=TRUE F2P 3/3 P2P 172/172 atk_20 infeasible-guard vacuity site 2 (dead `candidates_len < 1` arm carrying an out-of-range select) -> resolved=TRUE 172/172 atk_21 REVERSED but provably in-range position (probes the int-vs-ARRAY abstraction: refined to l1_ratios_[len-1-best_indices_l1], a real ndarray index) -> resolved=TRUE 172/172 atk_22 select the LAST entry of the held table                       -> resolved=TRUE F2P 3/3 P2P 172/172 atk_23 infeasible-guard vacuity site 1 (dead `ndim == 5` arm carrying a 5-axis read) -> resolved=TRUE 172/172 atk_24 unresolved operand used where it PROVABLY AGREES with the resolved local -> resolved=TRUE 172/172 Every one is real residual freedom that refinement.md D explicitly declares benign, and the oracle agrees on all nine. atk_16/atk_22 are the 'which in-range entry' freedom; I confirmed it is genuinely not oracle-visible by reading the tests: the only no-refit test (test_LogisticRegressionCV_no_refit, test_logistic.py:1535-1556) asserts ONLY C_.shape / l1_ratio_.shape / coef_.shape, and the one l1_ratio_ VALUE assertion in the suite (test_LogisticRegressionCV_GridSearchCV_elastic_net, :1499 'gs.best_params_[l1_ratio] == lrcv.l1_ratio_[0]') runs with refit defaulting to TRUE, i.e. through the refit arm this hunk does not touch (grep 'refit=False' over the test file returns exactly ONE hit, at :1550, the shape-only test). So pinning the position would be SPEC-TOO-STRONG, exactly as refinement.md D claims.

### A-LEG AUDIT (refinement.md)
LEG KINDS: PASS. All 11 rows carry a legal tag and there is NO kind-3 (unexpressible-changed-op): A1 R, A2 R, A3 R, A4 I, A5 '**A-consumed** + R', A6 R, B1 R, B2 R, B3 'R + **A-consumed**', B4 I, B5 R. Plus two A-reference facts (the l1_ratios_ [None] sentinel; the A3 rank table). INVENTORY DEFECT FROM THE PRIOR PASS: FIXED. refinement.md C is now titled 'Axiom inventory (TWO consumed axioms, four abstract predicates, two A-reference facts)' and mapping.md 3 now says 'The proof consumes TWO axioms, one per site' -- matching model.py's actual two @ContractOnly methods (read_across_folds, select_mixing_value) and four abstract predicates (read_admissible, summary_table, candidate_table, mixing_selected). C's prose now enumerates BOTH axioms with their predicate pairs.

A5 (A-consumed, read_across_folds): correspondence HOLDS. Requires(summary_table(table_rank)) makes the rank EVERY read is checked against the held array's real ndim, not one the reader names; the predicate is abstract so it cannot be Folded. Confirmed empirically three ways, two of them verifier verdicts: atk_3 (extra read at a self-named rank) and atk_25 (self-consistent forged rank replacing the honest read) both die on insufficient permission to access summary_table(table_rank), while atk_4 (Fold) dies at TRANSLATION with abstract.predicate.fold -- a front-end refusal, so it shows the forgery is unexpressible rather than that a clause rejected it.

Grounded in the real code: coefs_paths is bound once at logistic.py:2084, reshaped by the RESOLVED multi_class at :2086-2106 (4 axes for multinomial via reshape+two swapaxes, 3 otherwise), rebound per class only in the ovr arm at :2124 -- so 'the step holds one table at table_axes' is a true statement about the real state at :2172-2178. B3 (A-consumed, select_mixing_value): correspondence NOW HOLDS -- this is precisely the leg the prior pass judged FAILING, and the repair closes it.

The claim 'one axiom call <-> one real IN-RANGE averaged lookup of the single real l1_ratios_' holds for EVERY call, not just the delivering one, because BOTH the entry-reality AND the extent are carried by the held resource candidate_table(holds_mixing_values, candidates_len): the reality half is enforced (atk_26 dies on 'Assertion holds_mixing_values might not hold') and the extent half is now enforced too (atk_9/atk_10/atk_13 die on insufficient permission to access candidate_table(..., candidates_len)). mapping.md's bijection row has been updated in step -- it now describes candidate_table as 'an abstract resource carrying BOTH whether its entries are real mixing values AND how many entries it has', so the doc no longer claims a bound the contract fails to enforce.

Grounded in the real code: in the no-refit branch there is exactly ONE l1_ratios_ in scope, bound once at logistic.py:1971 (user ratios, elasticnet) or :1978 (the one-element [None] placeholder) and never rebound; the real index best_indices // len(self.Cs_) is bounded by len(l1_ratios_) because scores.shape[1] == len(self.Cs_) * len(l1_ratios_) (reshape at :2108). A-REFERENCE (l1_ratios_ [None] sentinel): holds. axiom_check.py R3 checks np.mean over the sentinel is not a real number; the absent marker is therefore forced, matching post-patch :2187. A-REFERENCE (A3 rank table): holds. table_rank(resolved) in {3,4} == the real coefs_paths.ndim, and `_check_multi_class` (:457-471) resolves 'auto' away so the resolved value is never UNRESOLVED; axiom_check.py R1/R2/R4 drive the real callees.

#### WHY A BREAK, IF ONE EXISTED, WOULD HAVE TO BE AT SITE 2 (oracle-visibility)
Under every F2P/P2P no-refit parameter combination the test uses (n_classes=3, solver='saga'), the site-1 PREPATCH read is ALREADY in-bounds: self.multi_class and the resolved multi_class induce the same arity for ovr (3/3), multinomial (4/4) and auto (4/4, since n_classes=3>2 resolves to multinomial). The three l2 F2P tests fail pre-patch at site 2 (l1_ratios_[ndarray] on the LIST [None]). So site 2 carries the oracle-visible behaviour and the three elasticnet no_refit P2P cases are what a site-2 range violation breaks -- which is exactly what the prior atk_8/atk_9 exhibited and exactly what the current spec now rejects. I therefore concentrated the site-2 attack surface (13 of 26 attacks) on that lane and found no surviving hole.

#### Residual freedom, measured not assumed
The spec leaves exactly three freedoms, and all three were run through the oracle rather than argued: (i) value provenance at site 1 (atk_7), (ii) repeated in-bounds reads / in-range selections (atk_6, atk_17), (iii) which in-range entry site 2 selects (atk_16, atk_22). All resolve 172/172, so refinement.md D's boundary claim is correct on every axis it declares -- the contract is 'every read is arity-checked against the actual layout and at least one such read happens' and 'every selection is of an entry the held table actually has', neither more nor less. Additionally, the two infeasible-guard shapes (atk_20 site 2, atk_23 site 1) verify because their guards are dead in the model; their FAITHFUL refinements keep the guard, and since the model's admissible domain is not narrower than reality (candidates_len>=1 is真 of the real len(l1_ratios_); table_axes in {3,4} is真 of the real ndim, per G-PANEL-2's 270 traced fits) the guarded code is dead in reality too -- both resolve 172/172, confirming the abstraction does not hide a live path.

**CONCLUSION:** SOUND. 26 same-spec attacks run to completion (15 rejected on their own site's stated reason, 11 verifying), positive control verifies, both vacuity controls reject, the prepatch bug is reproduced at BOTH sites, the gold infra control resolves, and every one of the 11 verifying impls has a materialized faithful patch that RESOLVES under the official harness (F2P 3/3, P2P 172/172). The prior recorded counterexample was re-encoded and is now rejected by the repaired candidate_table(_, actual_len) resource. No verify-but-not-correct impl found; verify => correct holds for this frozen spec on every shape I could construct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 24 admissible attacks re-run of 26 submitted, none breaks the spec; positive control verifies (2 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 26 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_18.py`, `atk_19.py`, `atk_25.py`, `atk_26.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 9 | `atk_6.py`, `atk_7.py`, `atk_16.py`, `atk_17.py`, `atk_20.py`, `atk_21.py`, `atk_22.py`, `atk_23.py`, `atk_24.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_4.py`, `atk_15.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (26):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 26 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 21 — `atk_21.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 22 — `atk_22.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 23 — `atk_23.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 24 — `atk_24.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 25 — `atk_25.py` → rejected (same spec, does not verify — good)

Attack 26 — `atk_26.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) on scikit-learn__scikit-learn-14087 nagini. VERDICT: SOUND. 26 same-spec attacks + positive control, all run; every CANDIDATE materialized as a faithful refined patch and RUN through the official harness. No verifying wrong impl's patch failed to resolve.

#### The recorded fail is stale: the spec was repaired
verdict.md / meta.json record G-EQ=fail against model.py sha256 424b714a624b696f00a181950ac74581b6f0b66eaa85ac94e48b52e9027a855e, with counterexample atk_8 = 'site-2 forged selection bound' (select at position candidates_len declaring the table candidates_len+1 long). The model.py IN THE BUNDLE TODAY is sha256 5436d5460e959dbe6d4bcdf56364e9903d2a60ffde2212e627ce3edd3611f6f4 (mtime 19:36, i.e. AFTER the 19:08 fail was stamped), and it CONTAINS the repair the prior pass itself prescribed: candidate_table now carries the extent -- candidate_table(holds_mixing_values, actual_len) -- and select_mixing_value requires candidate_table(holds_mixing_values, candidates_len), so the bound a selection is checked against is the HELD table's own extent rather than a number the caller names.

Per MEMORY 'SPEC-MOVED is about the record, not the bytes' I did NOT inherit the label: I re-encoded the prior counterexample verbatim in shape and re-ran it. RESULT: the prior counterexample is now REJECTED. atk_9  (select at candidates_len, declaring candidates_len+1) -> weakness exit 2; verifier: 'The precondition of method select_mixing_value might not hold. There might be insufficient permission to access candidate_table(holds_mixing_values, candidates_len).' atk_10 (same shape, offsetting the REAL position past the end) -> weakness exit 2; same message. The site-1-style held-resource repair has been propagated to site 2 and it works.

#### COMMANDS (from repo root swe-proof), D=
  python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-14087 $D/<atk>.py   # all 27 exit 0
  python -m swebench_unified.adversary weakness  nagini scikit-learn__scikit-learn-14087 $D/<atk>.py   # 0=CANDIDATE, 2=rejected
  bash scripts/nagini_verify.sh $D/<atk>.py                                                           # exact error text
  python $D/route.py <name>   # wraps harness.run_resolve + build_one's OWN attribution helpers
Generated by $D/gen.py from $D/base_model.py, a byte-identical copy of the bundle model.py (diff base_model.py positive_control.py empty). Only the two impl regions are spliced; all 27 files pass same-spec exit 0. Weakness/verify/resolve all ran 3-at-a-time as background jobs (drivers run_weakness.sh / run_verify.sh / run_resolve.sh) because each Nagini check spawns a JVM+Z3.

#### Positive control / vacuity
  positive_control.py (byte-identical to bundle model.py) -> weakness exit 0 (verifies, 12s). NON-VACUITY OK.
  atk_18 (site-1 Assert(False)) -> REJECTED 'Assert might fail. Assertion False might not hold.'
  atk_19 (site-2 Assert(False)) -> REJECTED same. Both contract paths are REACHABLE, so neither proof is vacuous (MEMORY: 'Guarded self-calls can go vacuous' -- Assert(False) is the control).

#### 15 REJECTED ATTACKS (spec correctly turns each down), with the verifier's own words
  atk_1  PREPATCH SITE 1 (unresolved operand drives the read arity) <= PREPATCH REPRODUCED
         'precondition of method read_across_folds might not hold. Assertion (gather_arity(use_joint_layout) == table_rank) might not hold.'
  atk_8  PREPATCH SITE 2 (unconditional table value, never the marker) <= PREPATCH REPRODUCED
         'Postcondition of mixing_record might not hold. Assertion Implies((not family_has_mixing), (Result() is None)) might not hold.'
  atk_2  ungrounded-oracle echo site 1 (w = summary_token, no read at all)
         'Postcondition of gather_per_class might not hold. There might be insufficient permission to access read_admissible(table_axes).'
  atk_3  EXTRA read at a SELF-NAMED rank in ADDITION to the honest read
         'precondition of read_across_folds ... insufficient permission to access summary_table(table_rank).'  <= site-1 held-table resource WORKS
  atk_25 SELF-CONSISTENT forged rank REPLACING the honest read (read_across_folds(True, 4, tok): gather_arity(True)==4 holds of ITSELF)
         'precondition of read_across_folds ... insufficient permission to access summary_table(table_rank).'  <= a self-consistent rank is not the HELD table's
atk_4  Fold(summary_table(4)) forge -> 'Translation failed / Invalid program: abstract.predicate.fold' (structurally un-forgeable: a front-end refusal, so it counts in neither tally -- the forgery is unexpressible rather than rejected by a clause) atk_15 Fold(candidate_table(True, candidates_len + 1)) forge -> the same abstract.predicate.fold refusal at translation (also counts in neither tally) atk_5  control-flow-effect/totality site 1: honest read then diverge -> 'Obligation leak check failed.

Loop might not take all unsatisfied obligations from the context.' atk_14 control-flow-effect/totality site 2: right record then diverge -> same obligation-leak rejection (MustTerminate at the method level does its job) atk_9  PRIOR RECORDED COUNTEREXAMPLE re-encoded (forged selection bound) -> insufficient permission to access candidate_table(holds_mixing_values, candidates_len) atk_10 forged bound, offsetting the real position past the end -> same atk_13 record-correcting (select for EVERY family, then overwrite with the marker) -> same insufficient-permission on candidate_table: the placeholder table is never averaged atk_26 select from the PLACEHOLDER table at an in-range position, record the marker anyway (no Fold; uses the resource actually held)
         'precondition of select_mixing_value might not hold. Assertion holds_mixing_values might not hold.'  <= partiality is real
  atk_11 partial-domain site 2 (guard on candidates_len > 1 instead of the family) -> 'Postcondition ... Implies(family_has_mixing, ((Result() is not None) and (Result() == mixing_value))) might not hold.'
  atk_12 boundary site 2 (guard on selected_index > 0 instead of the family) -> same postcondition rejection

#### 11 CANDIDATES (verify) -- EVERY ONE MATERIALIZED AND RUN THROUGH THE OFFICIAL HARNESS
INFRA CONTROL FIRST: gold_control, materialized by the SAME generator ($D/mkpatch.py) -> resolved=TRUE, F2P 3/3, P2P 172/172. Its +/- lines are BYTE-IDENTICAL to the dataset gold patch (checked programmatically), so the generator and the oracle are both sound here and a non-resolve would have carried information (cf. `_oracle_cannot_refute_here`).

All 9 attack patches apply cleanly at base_commit a5743ed36f (git apply --check). atk_6  duplicate honest read of the held table, deliver the second   -> resolved=TRUE F2P 3/3 P2P 172/172 atk_7  value provenance: honest read discarded, deliver the token    -> resolved=TRUE F2P 3/3 P2P 172/172 atk_16 select at ANOTHER in-range position (position 0)              -> resolved=TRUE F2P 3/3 P2P 172/172 atk_17 EXTRA in-range selection in addition to the delivering one    -> resolved=TRUE F2P 3/3 P2P 172/172 atk_20 infeasible-guard vacuity site 2 (dead `candidates_len < 1` arm carrying an out-of-range select) -> resolved=TRUE 172/172 atk_21 REVERSED but provably in-range position (probes the int-vs-ARRAY abstraction: refined to l1_ratios_[len-1-best_indices_l1], a real ndarray index) -> resolved=TRUE 172/172 atk_22 select the LAST entry of the held table                       -> resolved=TRUE F2P 3/3 P2P 172/172 atk_23 infeasible-guard vacuity site 1 (dead `ndim == 5` arm carrying a 5-axis read) -> resolved=TRUE 172/172 atk_24 unresolved operand used where it PROVABLY AGREES with the resolved local -> resolved=TRUE 172/172 Every one is real residual freedom that refinement.md D explicitly declares benign, and the oracle agrees on all nine. atk_16/atk_22 are the 'which in-range entry' freedom; I confirmed it is genuinely not oracle-visible by reading the tests: the only no-refit test (test_LogisticRegressionCV_no_refit, test_logistic.py:1535-1556) asserts ONLY C_.shape / l1_ratio_.shape / coef_.shape, and the one l1_ratio_ VALUE assertion in the suite (test_LogisticRegressionCV_GridSearchCV_elastic_net, :1499 'gs.best_params_[l1_ratio] == lrcv.l1_ratio_[0]') runs with refit defaulting to TRUE, i.e. through the refit arm this hunk does not touch (grep 'refit=False' over the test file returns exactly ONE hit, at :1550, the shape-only test). So pinning the position would be SPEC-TOO-STRONG, exactly as refinement.md D claims.

### A-LEG AUDIT (refinement.md)
LEG KINDS: PASS. All 11 rows carry a legal tag and there is NO kind-3 (unexpressible-changed-op): A1 R, A2 R, A3 R, A4 I, A5 '**A-consumed** + R', A6 R, B1 R, B2 R, B3 'R + **A-consumed**', B4 I, B5 R. Plus two A-reference facts (the l1_ratios_ [None] sentinel; the A3 rank table). INVENTORY DEFECT FROM THE PRIOR PASS: FIXED. refinement.md C is now titled 'Axiom inventory (TWO consumed axioms, four abstract predicates, two A-reference facts)' and mapping.md 3 now says 'The proof consumes TWO axioms, one per site' -- matching model.py's actual two @ContractOnly methods (read_across_folds, select_mixing_value) and four abstract predicates (read_admissible, summary_table, candidate_table, mixing_selected). C's prose now enumerates BOTH axioms with their predicate pairs.

A5 (A-consumed, read_across_folds): correspondence HOLDS. Requires(summary_table(table_rank)) makes the rank EVERY read is checked against the held array's real ndim, not one the reader names; the predicate is abstract so it cannot be Folded. Confirmed empirically three ways, two of them verifier verdicts: atk_3 (extra read at a self-named rank) and atk_25 (self-consistent forged rank replacing the honest read) both die on insufficient permission to access summary_table(table_rank), while atk_4 (Fold) dies at TRANSLATION with abstract.predicate.fold -- a front-end refusal, so it shows the forgery is unexpressible rather than that a clause rejected it.

Grounded in the real code: coefs_paths is bound once at logistic.py:2084, reshaped by the RESOLVED multi_class at :2086-2106 (4 axes for multinomial via reshape+two swapaxes, 3 otherwise), rebound per class only in the ovr arm at :2124 -- so 'the step holds one table at table_axes' is a true statement about the real state at :2172-2178. B3 (A-consumed, select_mixing_value): correspondence NOW HOLDS -- this is precisely the leg the prior pass judged FAILING, and the repair closes it.

The claim 'one axiom call <-> one real IN-RANGE averaged lookup of the single real l1_ratios_' holds for EVERY call, not just the delivering one, because BOTH the entry-reality AND the extent are carried by the held resource candidate_table(holds_mixing_values, candidates_len): the reality half is enforced (atk_26 dies on 'Assertion holds_mixing_values might not hold') and the extent half is now enforced too (atk_9/atk_10/atk_13 die on insufficient permission to access candidate_table(..., candidates_len)). mapping.md's bijection row has been updated in step -- it now describes candidate_table as 'an abstract resource carrying BOTH whether its entries are real mixing values AND how many entries it has', so the doc no longer claims a bound the contract fails to enforce.

Grounded in the real code: in the no-refit branch there is exactly ONE l1_ratios_ in scope, bound once at logistic.py:1971 (user ratios, elasticnet) or :1978 (the one-element [None] placeholder) and never rebound; the real index best_indices // len(self.Cs_) is bounded by len(l1_ratios_) because scores.shape[1] == len(self.Cs_) * len(l1_ratios_) (reshape at :2108). A-REFERENCE (l1_ratios_ [None] sentinel): holds. axiom_check.py R3 checks np.mean over the sentinel is not a real number; the absent marker is therefore forced, matching post-patch :2187. A-REFERENCE (A3 rank table): holds. table_rank(resolved) in {3,4} == the real coefs_paths.ndim, and `_check_multi_class` (:457-471) resolves 'auto' away so the resolved value is never UNRESOLVED; axiom_check.py R1/R2/R4 drive the real callees.

#### WHY A BREAK, IF ONE EXISTED, WOULD HAVE TO BE AT SITE 2 (oracle-visibility)
Under every F2P/P2P no-refit parameter combination the test uses (n_classes=3, solver='saga'), the site-1 PREPATCH read is ALREADY in-bounds: self.multi_class and the resolved multi_class induce the same arity for ovr (3/3), multinomial (4/4) and auto (4/4, since n_classes=3>2 resolves to multinomial). The three l2 F2P tests fail pre-patch at site 2 (l1_ratios_[ndarray] on the LIST [None]). So site 2 carries the oracle-visible behaviour and the three elasticnet no_refit P2P cases are what a site-2 range violation breaks -- which is exactly what the prior atk_8/atk_9 exhibited and exactly what the current spec now rejects. I therefore concentrated the site-2 attack surface (13 of 26 attacks) on that lane and found no surviving hole.

#### Residual freedom, measured not assumed
The spec leaves exactly three freedoms, and all three were run through the oracle rather than argued: (i) value provenance at site 1 (atk_7), (ii) repeated in-bounds reads / in-range selections (atk_6, atk_17), (iii) which in-range entry site 2 selects (atk_16, atk_22). All resolve 172/172, so refinement.md D's boundary claim is correct on every axis it declares -- the contract is 'every read is arity-checked against the actual layout and at least one such read happens' and 'every selection is of an entry the held table actually has', neither more nor less. Additionally, the two infeasible-guard shapes (atk_20 site 2, atk_23 site 1) verify because their guards are dead in the model; their FAITHFUL refinements keep the guard, and since the model's admissible domain is not narrower than reality (candidates_len>=1 is真 of the real len(l1_ratios_); table_axes in {3,4} is真 of the real ndim, per G-PANEL-2's 270 traced fits) the guarded code is dead in reality too -- both resolve 172/172, confirming the abstraction does not hide a live path.

**CONCLUSION:** SOUND. 26 same-spec attacks run to completion (15 rejected on their own site's stated reason, 11 verifying), positive control verifies, both vacuity controls reject, the prepatch bug is reproduced at BOTH sites, the gold infra control resolves, and every one of the 11 verifying impls has a materialized faithful patch that RESOLVES under the official harness (F2P 3/3, P2P 172/172). The prior recorded counterexample was re-encoded and is now rejected by the repaired candidate_table(_, actual_len) resource. No verify-but-not-correct impl found; verify => correct holds for this frozen spec on every shape I could construct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on scikit-learn__scikit-learn-14087/nagini. Reference = the /tmp worktree WITH patch.diff applied (base commit a5743ed36f only for patch-untouched callees). No diverging input found; every candidate divergence I raised traced back to my own probe, not to the spec.

**SPEC IDENTITY:** `adversary same-spec` on a verbatim copy of model.py -> exit 0 ("SAME - attack shares the bundle's exact specification"). Positive control: `scripts/nagini_verify.sh` on model.py -> exit 0, "Verification successful" in 12.12s. So the spec region I reviewed is the frozen one and it is live.

### WHAT THE SPEC CLAIMS (2 modeled sites, both in the no-refit `else:` of LogisticRegressionCV.fit, logistic.py:2169-2187):
- gather_per_class: use_joint_layout = resolved_strategy != INDEPENDENT; read arity must equal the held summary_table's actual rank (3 for ovr layout, 4 for multinomial). Models patch hunk 1 (`self.multi_class` -> `multi_class`).
- mixing_record: family_has_mixing => record a selected value + hold mixing_selected(); else => record the explicit None marker and perform NO selection. Models patch hunk 2 (the `if self.penalty == 'elasticnet': ... else: append(None)` guard).

### MACHINE CHECKS RUN IN THE REAL IMAGE (swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-14087):
1. Bundle G-CONF, gold patch applied: exit 0 - shadow of both impl regions agrees with the REAL patched no-refit statements (extracted from the patched module AST and exec'd) on 100072 fuzzed inputs (seed 140870) + 6 full refit=False fits, 0 disagreements.
2. Bundle G-AX at base commit (apply_gold=False): exit 0 - R1 resolver never returns 'auto' + rank table matches np.reshape; R2 arity-match <=> in-bounds, over-arity raises IndexError; R4 one summary table per iteration at the modeled rank; R3/R3b [None] sentinel does not average to a real number and the lookup is usable EXACTLY when the table holds real values; R5 extent admissibility exact.
3. **F2P:** all 3 target params of test_LogisticRegressionCV_no_refit (ovr-l2, multinomial-l2, auto-l2) pass with gold patch -> 6 passed.

MY OWN INDEPENDENT PROBES (not the bundle's scripts), 216 configs over n_classes x multi_class x penalty x n_Cs x n_l1 x cv, reconstructing each Requires/Ensures clause from REAL fitted state: PROBE OK, no clause disagrees. Plus a sys.settrace probe measuring coefs_paths.ndim AT the read site (logistic.py:2172) against table_rank in every config: OK. Plus corner probes: (a) penalty l2/l1 WITH l1_ratios supplied (warning path) still yields the 1-entry [None] sentinel at the read site, so Requires(not family_has_mixing => candidates_len == 1) holds, and the record is [None,None,None]; (b) exhaustive sweep of every reachable flat position over n_Cs in {1,2,4,5} x n_l1 in {1,2,3,5}: flat // len(Cs_) is always inside len(l1_ratios_), so Requires(0 <= selected_index < candidates_len) is a fact about the real code, not a restriction on it.

### TWO CANDIDATE DIVERGENCES I CHASED AND RULED OUT (recording so they are not re-raised):
- 'PRE table_axes mismatch real=4 modeled=3' (and real=5 vs 4) on every elasticnet config. NOT a spec defect: my probe read the post-fit `coefs_paths_` attribute, but fit() reshapes it AGAIN for elasticnet at logistic.py:2205-2213 (`if self.l1_ratios is not None: coefs_paths_[cls].reshape((len(folds), Cs_.size, l1_ratios_.size, -1))`), adding a dimension after the modeled block ran. The read-site array is the pre-2205 one; the settrace probe confirms real ndim == table_rank there in every config. The bundle's own G-AX R4 avoids this by only using the attribute under refit=True.
- TypeError('only integer scalar arrays can be converted to a scalar index') when l1_ratios is a python list/tuple rather than an ndarray (real fit raises, refit=False only). NOT the patch delta and NOT a spec defect: measured identically with apply_gold=True AND apply_gold=False, so it is a pre-existing base-commit repo defect on `l1_ratios_[best_indices_l1]` with a list-typed table, outside this instance's delta and outside the F2P domain (the tests pass np.linspace). Per the brief, base behavior the patch does not touch is not a faithfulness break; and the model deliberately abstracts the table extent/entry-reality rather than the container type (mapping.md section 2, refinement.md B2).

STRENGTH CHECK (is the spec too strong?): the preconditions are each measured facts of the real code, not convenient restrictions - resolved_strategy != UNRESOLVED (real `_check_multi_class` never returns 'auto', logistic.py:457-471); table_axes == table_rank(resolved) (traced at the read site); candidates_len >= 1 and not-mixing => 1 (the [None] sentinel at logistic.py:1978, confirmed even on the l1_ratios-supplied warning path); 0 <= selected_index < candidates_len (exhaustive reachable-position sweep). The held-table resources (summary_table / candidate_table) are returned rather than consumed, so repeated in-bounds reads and repeated in-range lookups stay expressible - the contract does not forbid anything the real code does. Postconditions match the real post-patch observables: ovr/multinomial reads are in-bounds, and l1_ratio_ entries are real averages for elasticnet and literal None otherwise.

**VERDICT:** FAITHFUL. The modeled functions agree with the patched repo on every input I could construct inside the stated domain; no diverging input exists to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / GOLD-RECONSTRUCTION review of scikit-learn__scikit-learn-14087 nagini. No relaxation present: meta.json has no `relaxed_leakage` key (verified by key dump -> 'relaxed_leakage' in meta == False) and no RELAXED_LEAKAGE.md exists anywhere under the instance dir (find -iname '*RELAX*' empty). So this was judged as a plain, unrelaxed leakage review. I also ran swebench_unified.leakage.reviewer_directed over every readable file in the bundle: zero hits -- no file in this bundle addresses or instructs this role, and nothing told me what to submit.

**ARTIFACT IDENTITY.** Recomputed markers.region_hashes(model.py, NaginiBackend) and compared to meta G-HYGIENE data: all six regions match byte-for-byte (spec_view d1ac5f26ef021b90, axioms 6c9d8246, pure 220e66a8, pre-conditions da3b81cf, post-conditions 37ed1ba2, impl b37938ef). model.py sha256 5436d5460e959dbe...11f6f4 equals the sha recorded in G-LEAK/G-AX/G-CONF/G-GOLD/G-EQ sources, so the spec view I screened is the one the gates screened. `bash scripts/nagini_verify.sh model.py` -> 'Verification successful' in 11.12s, exit 0 (core gate re-confirmed, not inherited).

MECHANICAL SCREEN, RE-RUN. leakage.screen(model.py, NaginiBackend, gold_patch, problem_statement, test_patch) from the frozen instance row: passed=True, hard_failures=[], warnings=[]. I did NOT stop there, because I measured that this screen's symbol check is VACUOUS on this instance: `_patch_changed_symbols`(gold) returns the empty set (the only def the hunks touch is `fit`, len 3, below the len>=4 distinctiveness threshold), so branches (a)/(b) of the repo-symbol check screen nothing at all here. The pass is therefore real but weak evidence, and the substantive judgement had to be done by hand.

HAND CROSS-CHECK, SPEC VIEW vs PROBLEM_STATEMENT. Projected the consumer spec view with markers.spec_view and grepped 23 edit-localizing repo tokens against it, comparing each to the problem_statement. Result: every one of multi_class, ovr, multinomial, auto, elasticnet, penalty, l1_ratio, l1_ratios_, coefs_paths, best_indices, Cs_, logistic, sklearn, LogisticRegression, refit, np.mean, argmax, IndexError, ndim, reshape, n_classes, scores, sample_weight is ABSENT from the spec view. Note the direction of the finding: several of these (coefs_paths, best_indices, Cs_, refit, IndexError, np.mean, sklearn.linear_model.logistic) ARE public in the problem_statement traceback and the spec view still declines to use them. The view names no patched file path, no module path, no diff marker, and reproduces no gold line. Narration scan: the only hits for 'change'/'edit'/'diff'/'self.' are false positives on 'unchanged', 'differently-laid-out', 'not as an edit', and 'itself'/'table's' -- no bug->fix mechanism narration.

GOLD-RECONSTRUCTION TEST (the real question). The gold edit has two hunks: (1) `self.multi_class` -> `multi_class` at the read guard, (2) wrap the l1_ratio_ append in `if self.penalty == 'elasticnet': ... else: append(None)`. The spec view describes both facets ABSTRACTLY -- an unresolved-vs-resolved categorical and a table whose index arity must match its rank; a regularisation family that carries a mixing parameter vs one whose candidate table holds only an absent placeholder. Neither the attribute-vs-local distinction nor the string 'elasticnet' nor the identifier l1_ratio_ appears, so a consumer cannot read the edit off the view; it must still localize `fit`, find the no-refit branch, discover that the layout is keyed on the resolved local, and discover which setting selects the placeholder table.

The facet worth the most scrutiny is site 2, since 'elasticnet'/l1_ratio_ appear NOWHERE in the problem_statement (measured above) -- so the concern is that the spec view reveals a second bug the public statement never mentions. I tested reachability with real numpy rather than arguing it: the public repro uses default penalty='l2', which drives logistic.py:1978 to set l1_ratios_ = [None] (read at base_commit in the /tmp worktree).

With len(Cs_)=10 and scores.shape[1]=10, best_indices_l1 = best_indices // len(Cs_) = all zeros -- in-bounds, so the extent is not the issue; but the pre-patch `l1_ratios_[best_indices_l1]` on the plain list raises TypeError('only integer scalar arrays can be converted to a scalar index'), and np.mean(np.asarray([None])[idx]) raises TypeError('unsupported operand type(s) for +: NoneType and NoneType').

So site 2 is on the SAME public execution path: the moment the traceback's IndexError at site 1 is fixed, the problem_statement's own verbatim repro (`LogisticRegressionCV(cv=5, solver='saga', tol=1e-2, refit=False).fit(X, y)`) crashes at site 2. 'No error is thrown' -- the stated Expected Result -- therefore entails the site-2 behaviour by public derivation, and describing it is faithfulness to the stated expectation, not disclosure of a hidden second bug. This is consistent with F2P including the [ovr-l2]/[multinomial-l2]/[auto-l2] (non-elasticnet) cases.

SUPPORTING GATES RE-CONFIRMED, not inherited: G-VERIFY re-run above; region hashes recomputed; G-DIFF's three prepatch impl regions read directly -- model_prepatch (site-1 read keyed on the unresolved form), model_prepatch_2 (site-2 unconditional selection), model_prepatch_1 (value echo with no read) -- each differs from model.py only in the impl region, confirming the spec view's abstractions are load-bearing discriminators rather than restatements of the diff. G-AX/G-CONF/G-EQ/G-MUT/G-PBT all recorded pass against this same model.py sha.

**CONCLUSION:** the spec view leaks nothing beyond the solver-visible problem_statement -- it in fact uses strictly less repo vocabulary than the statement makes public. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.