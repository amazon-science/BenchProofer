# P2 adversarial audit — matplotlib__matplotlib-24970

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_prepatch.lean`, `atk_1_fabricate.lean`, `atk_2_launder.lean`, `atk_3_unsigned_wide.lean`, `atk_4_row_collapse_above.lean`, `atk_5_row_below_to_index.lean`, `atk_9_boundary_carrier.lean`, `atk_10_partial_empty.lean`, `atk_11_swap_under_over.lean`, `atk_12_rewrite_boundary_to_above.lean`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_6_double_call.lean`, `atk_7_narrow_int16.lean`, `atk_8_wide_signed.lean`, `atk_14_discard_second.lean`, `atk_16_row_collapse_proved.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying same-spec wrong impl was exhibited: all 5 impls that verified (atk_6, atk_7, atk_8, atk_14, atk_16) had their faithful refined patches materialized and RESOLVED under the official harness (resolved=true, F2P 1/1, zero P2P failures), so each is a behaviourally-correct impl rather than a counterexample. verify=>correct held on every probe.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,21 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    -- Pre-image skeleton: the reserved-marker assignment is carried out on the
+    -- input element's OWN container. For the integer-dtype input the widening runs
+    -- only inside the float branch, so the element keeps the container it arrived
+    -- in: an unsigned one (`admitsNegative = false`) whose non-negative extent is
+    -- only `paletteSize` (it admits just the ordinary indices `0 .. paletteSize-1`).
+    -- Neither end of it admits what the assignment does: the reserved markers up to
+    -- `invalidSlot paletteSize = paletteSize + 2` are outside its extent, and the
+    -- below-range selection is not even live in it. So the callee obligations
+    -- `admitsNegative = true` — here `false = true` — and `paletteSize + 3 ≤ carrier`
+    -- — here `paletteSize + 3 ≤ paletteSize` — cannot be discharged at the call
+    -- site, the `markersAdmitted` capability is never granted, and the
+    -- postcondition cannot be proved. Both obligations are INDEPENDENT of `cells`
+    -- (they fail even for an empty or wholly-in-range row), so prove_correct MUST
+    -- fail.
+    let out <- assignReserved cells paletteSize false paletteSize
     return out
     -- impl-end
 
```

Attack 2 — `atk_1_fabricate.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,20 +254,7 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
-    return out
+    return rowOf (slotSeq paletteSize cells)
     -- impl-end
 
 prove_correct resolveSlots by
```

Attack 3 — `atk_2_launder.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,20 +254,8 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
-    return out
+    let r <- assignReserved cells paletteSize true (paletteSize + 3)
+    return rowOf (slotsOf r)
     -- impl-end
 
 prove_correct resolveSlots by
```

Attack 4 — `atk_3_unsigned_wide.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,7 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved cells paletteSize false (max 65536 (paletteSize + 3))
     return out
     -- impl-end
 
```

Attack 5 — `atk_4_row_collapse_above.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,9 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved (cells.map (fun c => match c with
+      | Cell.aboveRange => Cell.inPalette paletteSize
+      | c => c)) paletteSize true (paletteSize + 3)
     return out
     -- impl-end
 
```

Attack 6 — `atk_5_row_below_to_index.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,9 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved (cells.map (fun c => match c with
+      | Cell.belowRange => Cell.inPalette paletteSize
+      | c => c)) paletteSize true (paletteSize + 3)
     return out
     -- impl-end
 
```

Attack 7 — `atk_6_double_call.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,18 +254,7 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
+    let _r1 <- assignReserved cells paletteSize true (paletteSize + 3)
     let out <- assignReserved cells paletteSize true (paletteSize + 3)
     return out
     -- impl-end
```

Attack 8 — `atk_7_narrow_int16.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 3] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,7 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved cells paletteSize true (max 32768 (paletteSize + 3))
     return out
     -- impl-end
 
```

Attack 9 — `atk_8_wide_signed.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,7 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved cells paletteSize true (max 65536 (paletteSize + 3))
     return out
     -- impl-end
 
```

Attack 10 — `atk_9_boundary_carrier.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,7 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved cells paletteSize true (paletteSize + 2)
     return out
     -- impl-end
 
```

Attack 11 — `atk_10_partial_empty.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,20 +254,11 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
-    return out
+    if cells.isEmpty then
+      return rowOf []
+    else
+      let out <- assignReserved cells paletteSize true (paletteSize + 3)
+      return out
     -- impl-end
 
 prove_correct resolveSlots by
```

Attack 12 — `atk_11_swap_under_over.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,10 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved (cells.map (fun c => match c with
+      | Cell.belowRange => Cell.aboveRange
+      | Cell.aboveRange => Cell.belowRange
+      | c => c)) paletteSize true (paletteSize + 3)
     return out
     -- impl-end
 
```

Attack 13 — `atk_12_rewrite_boundary_to_above.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,9 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved (cells.map (fun c => match c with
+      | Cell.inPalette k => if paletteSize <= k then Cell.aboveRange else Cell.inPalette k
+      | c => c)) paletteSize true (paletteSize + 3)
     return out
     -- impl-end
 
```

Attack 14 — `atk_13_drop_element.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,7 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved cells.tail paletteSize true (paletteSize + 3)
     return out
     -- impl-end
 
```

Attack 15 — `atk_14_discard_second.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,8 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
     let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let _bogus <- assignReserved [] paletteSize true (paletteSize + 3)
     return out
     -- impl-end
 
```

Attack 16 — `atk_15_constant_slots.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,19 +254,7 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved (cells.map (fun _ => Cell.invalid)) paletteSize true (paletteSize + 3)
     return out
     -- impl-end
 
```

Attack 17 — `atk_16_row_collapse_proved.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -254,21 +254,20 @@
   ensures markersAdmitted out paletteSize
   do
     -- impl-start
-    -- Carry out the reserved-marker assignment on a container that admits BOTH ends
-    -- of what the assignment does to it, and hand on the container it produced:
-    --   * it represents values below zero, so the below-range selection is live and
-    --     a below-range element reaches `underSlot` instead of keeping the index the
-    --     above-range selection stored (the call's `admitsNegative = true`);
-    --   * its non-negative extent admits every reserved index written — the largest
-    --     is `invalidSlot paletteSize = paletteSize + 2`, so admitting
-    --     `0 .. paletteSize+2` (representable range `paletteSize + 3`) is enough
-    --     (the call's `paletteSize + 3 ≤ carrier`).
-    -- The input element's own container need have neither property. Establishing
-    -- both of them here is what lets the assignment complete and grant the
-    -- capability the result requires.
-    let out <- assignReserved cells paletteSize true (paletteSize + 3)
+    let out <- assignReserved (cells.map (fun c => match c with
+      | Cell.aboveRange => Cell.inPalette paletteSize
+      | c => c)) paletteSize true (paletteSize + 3)
     return out
     -- impl-end
 
 prove_correct resolveSlots by
-  loom_solve
+  have key : ∀ (cs : List Cell),
+      slotSeq paletteSize (cs.map (fun c => match c with
+        | Cell.aboveRange => Cell.inPalette paletteSize
+        | c => c)) = slotSeq paletteSize cs := by
+    intro cs
+    induction cs with
+    | nil => rfl
+    | cons c cs ih =>
+      cases c <;> simp [slotSeq_cons, ih, slotOf, overSlot]
+  loom_solve <;> simp_all [key]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, matplotlib__matplotlib-24970/velvet. 17 same-spec files + positive control; same_spec=True verified for EVERY file (checked individually with swebench_unified.markers.same_spec, velvet language). All verifies via `bash scripts/lean_verify.sh <file>` from repo root; 4-way concurrent background batches. Worktree at base_commit a3011dfd1aaa2487cce8aa7369475533133ef777 =.

**CONTROLS:** pos_control EXIT=0 (verifies). atk_prepatch (Solution_prepatch.lean, `assignReserved cells paletteSize false paletteSize`) EXIT=1 -> PREPATCH BUG REPRODUCED, failing goal `false = true` as refinement.md A.diff claims.

### REJECTED (EXIT=1, 11 distinct wrong impls):
- atk_1_fabricate `return rowOf (slotSeq paletteSize cells)` -> unsolved `markersAdmitted (rowOf ...)`; capability unforgeable (ungrounded-oracle echo).
- atk_2_launder gated call then `return rowOf (slotsOf r)` -> same residual goal; capability untransferable across a value-equal rebuild.
- atk_3_unsigned_wide `false (max 65536 (paletteSize+3))` -> rejected on `false = true`; width alone insufficient, signedness obligation is live.
- atk_9_boundary_carrier `true (paletteSize+2)` -> off-by-one BOUNDARY probe; rejected, so `paletteSize+3 <= carrier` is the exact tight bound.
- atk_4_row_collapse_above / atk_12_rewrite_boundary_to_above / atk_5_row_below_to_index / atk_11_swap_under_over / atk_15_constant_slots -> row rewrites, all EXIT=1 on `slotsOf r = slotSeq paletteSize cells`.
- atk_13_drop_element `cells.tail` -> length/value clause fails.
- atk_10_partial_empty (PARTIAL-DOMAIN: correct call on non-empty, `rowOf []` on empty) -> rejected on the empty branch; the effect obligation binds even where values are vacuously right.

VERIFIED (EXIT=0) => MANDATORY RESOLVE RUNS. All 5 patches passed `git apply --check` in the base_commit worktree before submission, and each was run with swebench_unified.harness.run_resolve (official Docker oracle, timeout 3600):
- atk_7_narrow_int16 (carrier `max 32768 (paletteSize+3)`, int16 container) -> RESOLVED (attempt 3/3, flagged flaky: earlier attempts did not complete on a loaded host; resolved-on-any-attempt per the velvet retry policy). F2P 1/1, 0 P2P failures.
- atk_8_wide_signed (carrier `max 65536 (paletteSize+3)`, int32) -> RESOLVED (1 attempt).
- atk_6_double_call (admitting assignment carried out TWICE, second container handed on) -> RESOLVED (1 attempt).
- atk_14_discard_second (CONTROL-FLOW-EFFECT: correct call kept, extra admitting assignment over the empty row discarded) -> RESOLVED (1 attempt).
- atk_16_row_collapse_proved (aboveRange re-spelled as `inPalette paletteSize`, with a hand-proved `slotSeq` congruence lemma so the earlier atk_4 rejection could not be dismissed as a tactic artefact) -> RESOLVED (1 attempt). This is the key non-rubber-stamp result: the collapse IS semantically benign (slotOf ps (.inPalette ps) = overSlot ps), atk_4 failed only because loom_solve lacks the congruence; once proved it verifies AND resolves, so the fibre collision the spec deliberately admits is sound, not a hole.

A-LEG AUDIT (the assigned focus). refinement.md legs are R / A-consumed / A-reference / I with NO kind-3; the single axiom in meta.json is `assignReserved_contract` (plus `rowOf`/`slotsOf_rowOf` about the UNCHANGED array construction) — no axiom about the function under change. Correspondence checked against the real callees at base_commit colors.py:715-738: A5's three sequential stores match `xa[xa>N-1]=_i_over; xa[xa<0]=_i_under; xa[mask_bad]=_i_bad` including the load-bearing ORDER; A3's `slotOf` guard (`.inPalette k` with paletteSize<=k -> overSlot) is exactly what the first selection does, and I independently confirmed the two documented self-corrections in refinement.md are the ones the frozen text supports.

A4's carrier-scope claim was independently re-measured in numpy: int16 vs platform int AGREE on the whole float path and on every graded integer dtype (uint8/int/float16 at value 0, 0.5, 1.0, 255), and DIVERGE only on integer-dtype magnitudes >32767 ([40000]->256 vs 257, [100000]->256 vs 257), which the graded suite never feeds — so atk_7's resolve is the CORRECT outcome and refinement.md's A4 scope caveat is accurate rather than an over-claim. Grep of the graded tests confirms no integer input above 1416 and no int16/int32/uint16 dtype anywhere.

**VERDICT SOUND:** 16 distinct wrong-impl attacks run (>=5 required) spanning partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, launder, fabrication, row-rewrite and carrier-extent families; 11 rejected, 5 verified and ALL 5 materialized-and-executed resolve runs came back resolved. No verifying impl whose faithful patch fails to resolve was found, so verify=>correct is not falsified on this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_prepatch.lean`, `atk_1_fabricate.lean`, `atk_2_launder.lean`, `atk_3_unsigned_wide.lean`, `atk_4_row_collapse_above.lean`, `atk_5_row_below_to_index.lean`, `atk_9_boundary_carrier.lean`, `atk_10_partial_empty.lean`, `atk_11_swap_under_over.lean`, `atk_12_rewrite_boundary_to_above.lean`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_6_double_call.lean`, `atk_7_narrow_int16.lean`, `atk_8_wide_signed.lean`, `atk_14_discard_second.lean`, `atk_16_row_collapse_proved.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying same-spec wrong impl was exhibited: all 5 impls that verified (atk_6, atk_7, atk_8, atk_14, atk_16) had their faithful refined patches materialized and RESOLVED under the official harness (resolved=true, F2P 1/1, zero P2P failures), so each is a behaviourally-correct impl rather than a counterexample. verify=>correct held on every probe.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_fabricate.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2_launder.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_unsigned_wide.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_row_collapse_above.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5_row_below_to_index.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6_double_call.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_7_narrow_int16.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 3]

Attack 9 — `atk_8_wide_signed.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 10 — `atk_9_boundary_carrier.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10_partial_empty.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_11_swap_under_over.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12_rewrite_boundary_to_above.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_13_drop_element.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_14_discard_second.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 16 — `atk_15_constant_slots.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_16_row_collapse_proved.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, matplotlib__matplotlib-24970/velvet. 17 same-spec files + positive control; same_spec=True verified for EVERY file (checked individually with swebench_unified.markers.same_spec, velvet language). All verifies via `bash scripts/lean_verify.sh <file>` from repo root; 4-way concurrent background batches. Worktree at base_commit a3011dfd1aaa2487cce8aa7369475533133ef777 =.

**CONTROLS:** pos_control EXIT=0 (verifies). atk_prepatch (Solution_prepatch.lean, `assignReserved cells paletteSize false paletteSize`) EXIT=1 -> PREPATCH BUG REPRODUCED, failing goal `false = true` as refinement.md A.diff claims.

### REJECTED (EXIT=1, 11 distinct wrong impls):
- atk_1_fabricate `return rowOf (slotSeq paletteSize cells)` -> unsolved `markersAdmitted (rowOf ...)`; capability unforgeable (ungrounded-oracle echo).
- atk_2_launder gated call then `return rowOf (slotsOf r)` -> same residual goal; capability untransferable across a value-equal rebuild.
- atk_3_unsigned_wide `false (max 65536 (paletteSize+3))` -> rejected on `false = true`; width alone insufficient, signedness obligation is live.
- atk_9_boundary_carrier `true (paletteSize+2)` -> off-by-one BOUNDARY probe; rejected, so `paletteSize+3 <= carrier` is the exact tight bound.
- atk_4_row_collapse_above / atk_12_rewrite_boundary_to_above / atk_5_row_below_to_index / atk_11_swap_under_over / atk_15_constant_slots -> row rewrites, all EXIT=1 on `slotsOf r = slotSeq paletteSize cells`.
- atk_13_drop_element `cells.tail` -> length/value clause fails.
- atk_10_partial_empty (PARTIAL-DOMAIN: correct call on non-empty, `rowOf []` on empty) -> rejected on the empty branch; the effect obligation binds even where values are vacuously right.

VERIFIED (EXIT=0) => MANDATORY RESOLVE RUNS. All 5 patches passed `git apply --check` in the base_commit worktree before submission, and each was run with swebench_unified.harness.run_resolve (official Docker oracle, timeout 3600):
- atk_7_narrow_int16 (carrier `max 32768 (paletteSize+3)`, int16 container) -> RESOLVED (attempt 3/3, flagged flaky: earlier attempts did not complete on a loaded host; resolved-on-any-attempt per the velvet retry policy). F2P 1/1, 0 P2P failures.
- atk_8_wide_signed (carrier `max 65536 (paletteSize+3)`, int32) -> RESOLVED (1 attempt).
- atk_6_double_call (admitting assignment carried out TWICE, second container handed on) -> RESOLVED (1 attempt).
- atk_14_discard_second (CONTROL-FLOW-EFFECT: correct call kept, extra admitting assignment over the empty row discarded) -> RESOLVED (1 attempt).
- atk_16_row_collapse_proved (aboveRange re-spelled as `inPalette paletteSize`, with a hand-proved `slotSeq` congruence lemma so the earlier atk_4 rejection could not be dismissed as a tactic artefact) -> RESOLVED (1 attempt). This is the key non-rubber-stamp result: the collapse IS semantically benign (slotOf ps (.inPalette ps) = overSlot ps), atk_4 failed only because loom_solve lacks the congruence; once proved it verifies AND resolves, so the fibre collision the spec deliberately admits is sound, not a hole.

A-LEG AUDIT (the assigned focus). refinement.md legs are R / A-consumed / A-reference / I with NO kind-3; the single axiom in meta.json is `assignReserved_contract` (plus `rowOf`/`slotsOf_rowOf` about the UNCHANGED array construction) — no axiom about the function under change. Correspondence checked against the real callees at base_commit colors.py:715-738: A5's three sequential stores match `xa[xa>N-1]=_i_over; xa[xa<0]=_i_under; xa[mask_bad]=_i_bad` including the load-bearing ORDER; A3's `slotOf` guard (`.inPalette k` with paletteSize<=k -> overSlot) is exactly what the first selection does, and I independently confirmed the two documented self-corrections in refinement.md are the ones the frozen text supports.

A4's carrier-scope claim was independently re-measured in numpy: int16 vs platform int AGREE on the whole float path and on every graded integer dtype (uint8/int/float16 at value 0, 0.5, 1.0, 255), and DIVERGE only on integer-dtype magnitudes >32767 ([40000]->256 vs 257, [100000]->256 vs 257), which the graded suite never feeds — so atk_7's resolve is the CORRECT outcome and refinement.md's A4 scope caveat is accurate rather than an over-claim. Grep of the graded tests confirms no integer input above 1416 and no int16/int32/uint16 dtype anywhere.

**VERDICT SOUND:** 16 distinct wrong-impl attacks run (>=5 required) spanning partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, launder, fabrication, row-rewrite and carrier-extent families; 11 rejected, 5 verified and ALL 5 materialized-and-executed resolve runs came back resolved. No verifying impl whose faithful patch fails to resolve was found, so verify=>correct is not falsified on this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**FAITHFULNESS-BREAK ATTACK:** no divergence found between the modelled function and the real repo. Reference tree used correctly = base_commit a3011dfd1a + patch.diff applied (I located a true reference install, mpl 3.7.0.dev1362+ga3011dfd1, numpy 1.25.2, confirmed by 'We need this cast for unsigned ints' present in Colormap.`__call__`; the  worktree also carries the patch applied). Base was used only for the unchanged callee (the three reserved-marker stores), which the patch does not touch.

### Evidence
(1) Spec region byte-identical: markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend()) = True; spec_signature sha256 cd06f3a2c48de504f2833dde6c1f7dd6f137bf880037f923fefc8a25b35dbd03. diff shows the ONLY delta is inside impl-start/impl-end (assignReserved cells paletteSize true (paletteSize+3) vs ... false paletteSize).
(2) Twin behaviour: lean_verify.sh Solution.lean -> EXIT 0; Solution_prepatch.lean -> fails with sole residual goal 'false = true' at line 276, i.e. the first container obligation. Matches refinement.md A.diff exactly.
(3) Deep value model (slotOf/slotSeq) vs the REAL reference tree, end-to-end through Colormap.`__call__` with slots recovered from output RGBA against `_lut`: 3000 random cases / 10551 elements, 0 divergences. Coverage: int8/16/32/64, uint8/16/32/64, bool, float16/32/64, masked arrays, non-native byteorder, nan/+-inf, dtype extremes, paletteSize in {1,2,3,4,6,7,8,16,64,255,256,257,300}. A separate store-block differential added paletteSize 0 and 1000 and the uint64 signed threshold: 704 + 7092 + 1326 more elements, 0 divergences.
(4) The two load-bearing modelling choices I tried hardest to break, both confirmed against real numpy:
  - Selection-order guard on slotOf (.inPalette k) = if k < paletteSize then k else overSlot. Attempted counterexample: an ordinary index carrying a reserved marker value. Real reference tree at N=6 resolves uint64 6/7/300 -> slot 7 (overSlot), never keeping the index; 1326-case signed-container readback sweep (int8/16/32/64 x every N with N+3<=carrier, all four classes incl. inPalette k>=N and the mask) found 0 disagreements. The identity reading (k kept) is the one that diverges, so the guard is required, not over-strong.
  - Post-cast classification, incl. the unsigned wrapping region. Reference tree at N=6: uint64 `2**63`-1 -> 7 (overSlot), `2**63` / `2**63`+1 / `2**64`-1 -> 6 (underSlot). Threshold is exactly the signed max, as mapping.md 2.1 claims.
(5) Axiom preconditions are neither too strong nor too weak (this is where an over-strong spec would show):
  - paletteSize+3 <= carrier coincides EXACTLY with real numpy store legality. Swept uint8/int8/uint16/int16/uint32/int32 across N in [carrier-4, carrier+1] under warnings-as-errors on BOTH numpys (1.25.2 -> DeprecationWarning, the actual F2P mechanism; 2.2.6 -> OverflowError): 0 mismatches. The boundary flips at exactly N+3 > carrier because the largest marker is `_i_bad` = N+2. Also confirmed input-independent (fires on empty and on wholly-in-range uint8 input), matching the F2P.
  - admitsNegative = true is NECESSARY, not decorative: unsigned width-sufficient containers (uint16/32/64 at N=6/256/1000, all satisfying N+3<=carrier) resolve a below-range element to overSlot N+1 where slotSeq says underSlot N -> the readback claim would be FALSE without the obligation. And it is SUFFICIENT: every signed container with N+3<=carrier (int16/32/64 x N=6/256/1000/30000) agrees with slotSeq on all four classes, 0 disagreements. So the contract does not over-constrain to the platform int; int16 at N=256 satisfies both and is correctly admitted.
(6) paletteSize edge cases with no precondition in the spec: N=0/1/2, empty row, and inPalette k>N all agree with the real store block. Length claim (slotsOf out).length = cells.length holds for 0/1/5 elements.
(7) Bundle self-checks: axiom_check.py ALL SOUND (exit 0); properties.py exit 0.

HARNESS DEFECT FOUND (NOT a spec defect, do not route as repair): conformance_check.py reported 'G-CONF FAIL: 5 R/I disagreement(s) over 34 inputs', all in the uint64 region (dtype-extremes-uint64, uint64-signed-threshold, uint64-order-probe, 2x int-fuzz). Root cause is its ORACLE, not the spec: oracle_slots imports matplotlib from sys.path, which in this env resolves to the installed matplotlib 3.10.9 at colors.py, whose Colormap.`__call__` was REWRITTEN upstream long after this instance -- it pre-computes mask_under = xa < 0 and mask_over = xa >= self.N BEFORE the astype(int) cast, so uint64 values >= `2**63` never wrap into the below-range class and it answers overSlot. Re-running the exact 3 failing rows against the TRUE reference tree gives [0,1,5,7,7,6,6] / [7,7,6,6,6] / [5,6,7,0] -- byte-identical to the spec's shadow, and it is the 3.10.9 oracle that is wrong. Note conformance_check.py still exits 0, so this does not gate; it needs its oracle pinned to the reference tree (PYTHONPATH or an installed 3.7.0.dev1362+ga3011dfd1) rather than to sys.path. Filed here as an environment issue so a future wave does not re-read it as spec weakness.

**CONCLUSION:** I could not construct any input on which the modelled function disagrees with the reference tree. The spec is not too strong (both callee obligations are exactly the two selection boundaries, each measured to flip at the real boundary, and neither excludes a container the reference tree agrees with), and it is not drifted (10551+ elements of end-to-end differential against the real patched repo, 0 divergences). Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Attacker-3 (leakage / gold-reconstruction), velvet bundle matplotlib__matplotlib-24970. FRESH re-measurement; I inherited nothing. The retained G-PANEL-3 stamp (pass, checked_at 08:05) is STALE: its sources.Solution.lean = d0ea1c79..., while the current file hashes 6c31e699... (sha256sum). Its own note even asserts "current d0ea1c79", so the spec has been prose-edited AGAIN since that stamp was written; under the prose-edit rule it does not describe this artifact. Same staleness applies to G-EQ / G-PANEL / G-PANEL-1 (all stamped d0ea1c79). Every gate my verdict rests on is fresh at 6c31e699: G-VERIFY, G-GOLD, G-DIFF, G-AX, G-CONF, G-LEAK, G-MUT, G-PBT, G-HYGIENE, G-INTEGRITY.

**RELAXATION STATUS:** NONE. No top-level `relaxed_leakage` key in meta.json (keys: axioms, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, repo, schema_version, spec_provenance, string_modeling, version); `find -iname '*RELAX*'` over the whole instance dir returns empty; meta G-LEAK status is "pass" ("spec view clean"), mode "strict", not "relaxed". The only 'relax' substrings anywhere are inside prior agents' notes saying there is no relaxation. So there is NO unavoidability argument to adjudicate and I judged the spec view on the STRICT standard throughout.

### WHAT I RAN (my own, from src/ not the shipped checks)
1. markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) -> True. Spec region byte-identical. Full-file diff shows the twins differ ONLY inside impl-start..impl-end (gold: `assignReserved cells paletteSize true (paletteSize + 3)`; pre: `... false paletteSize`) — elided from the spec view.
2. markers.spec_view() computed (261 lines) and read end to end. Confirmed the impl body and prove_correct body are replaced by "elided — supplied by the consumer"; grep for `paletteSize + 3)` / `true (paletteSize` / `rowOf (slotSeq` in the spec view -> no hits, so the discriminating ARGUMENTS never appear, only the abstract obligation.
3. leakage.screen(Solution.lean, velvet, patch.diff, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[] (zero, not merely no-hard-fail).
4. leakage.reviewer_directed() over all 9 bundle files -> [] for every one. Plus my own grep for attacker/G-PANEL/reviewer/auditor/"honest verdict"/NO-LEAKAGE/"do not submit"/"must record" across Solution*.lean, mapping.md, refinement.md, properties.py, axiom_check.py, conformance_check.py -> NO hits. NO file in this bundle addresses me or tells me what to record. (verdict.md does contain prior agents' own notes describing their verdicts, but that is a transcript ledger, not an instruction directed at me.)
5. Vocabulary grep on the SPEC VIEW for gold-edit localizers: astype, errstate, dtype, kind, clip, byteswap, newbyteorder, cast, hoist, unconditional, signed, unsigned, uint, int8, int64, numpy, np., colors.py, patch, gold, fix, bug, previously, "no longer", deprecat, warn, conversion, out-of-bound, branch, float, 256, 257, 258, mask_bad, `_i_over`, `_i_under`, `_i_bad`, self.N, Colormap, `__call__`, platform, widen, promote, wrap, overflow -> ALL ZERO. The only `xa` hits were substrings of "examination"/"exactly"/"exact" (word-boundary \bxa\b -> []). The complete set of integer literals in the spec view is {0,1,2,3,4} — nothing near 256/257/258. `width` appears 3x purely as abstract container-representation prose.
6. LOAD-BEARING STRIP TEST (scripts/lean_verify.sh, 900s cap, scratch under mktemp -d):
   - Solution.lean -> exit 0.
   - Solution_prepatch.lean -> exit 1, sole residual `false = true`.
   - Launder impl `return rowOf (slotSeq paletteSize cells)` under the FULL spec -> exit 1, residual set includes `markersAdmitted (rowOf (slotSeq paletteSize cells)) paletteSize`.
   - Same launder with the `ensures markersAdmitted out paletteSize` clause DELETED -> still exit 1, but the capability goal is GONE from the residual set.
   So the discriminating clause is measured load-bearing, not decorative narration — the strip test confirms the clause carries the proof obligation rather than merely narrating the edit.

BEYOND-PROBLEM_STATEMENT DERIVATION (the leakage question proper; hints_text deliberately NOT used — that is where the maintainer literally proposes the widening fix)
Every discriminating fact in the spec view is derivable from the SOLVER-VISIBLE problem_statement:
- Reserved trailing slots underSlot=N / overSlot=N+1 / invalidSlot=N+2: the public traceback quotes "conversion of 256 to uint8" against `xa[xa < 0] = self._i_under`, "257" against `xa[xa > self.N - 1] = self._i_over`, and "258" against `xa[mask_bad] = self._i_bad`, at default N=256. That IS N, N+1, N+2 keyed to the three stores, publicly, with file and line numbers (colors.py:730-732).
- Carrier obligation `paletteSize + 3 <= carrier`: the public warning is exactly "NumPy will stop allowing conversion of out-of-bound Python integers to integer arrays ... to uint8 will fail" on those three lines — i.e. the container is too narrow to hold the markers. Restating that requirement adds no localization.
- `admitsNegative = true`: derived from `xa[xa < 0] = self._i_under`, reproduced verbatim in the public traceback; in an unsigned container that comparison is dead. Preserve-existing-behaviour, not a disclosure of what moved.
- "resolved slot VALUE is the same regardless of container width": public Actual vs Expected is warnings-only vs "No warnings" — no value discrepancy is reported, so value-invariance is precisely the public requirement.
What a gold reconstruction still needs and the spec view withholds entirely: nothing about `astype(int)`, nothing about the `if xa.dtype.kind == "f":` branch, nothing about hoisting that cast out of the branch to run unconditionally, nothing about `np.errstate(invalid="ignore")`, no dtype name, no diff marker, no repo symbol (xa, `_i_over`, `_i_under`, `_i_bad`, self.N, Colormap.`__call__` all absent; spec identifiers are re-namings: paletteSize / carrier / admitsNegative / assignReserved / markersAdmitted / IndexRow / rowOf / Cell). The spec view is dtype-agnostic, which is exactly the part that would localize the edit — the gold edit's essence is "the cast currently runs only for floats", and the spec view never mentions floats or branches at all. The edit-site information is the non-public part, and it is fully withheld.
7. The lone G-MUT survivor (L269 '3'->'4') sits in the ELIDED impl (`let out <- assignReserved cells paletteSize true (paletteSize + 3)`), confirmed by reading L265-272 — not spec-view content, so not a leakage surface.

ROUTING NOTE (not a leakage finding): G-EQ / G-PANEL / G-PANEL-1 fail, all stamped against the stale d0ea1c79 spec. Those are spec-too-weak / equivalence defects — the opposite direction from disclosure, and a spec that is too weak can still leak nothing. Because there is no relaxation here, my verdict leans on none of them. They do mean the cell is not green and layers 1/2 need re-audit against 6c31e699.

**VERDICT:** NO-LEAKAGE. Spec region byte-identical between twins, screen clean with zero warnings, zero gold-edit vocabulary in the spec view, discriminator measured load-bearing by strip test, and every discriminating fact independently derivable from the public problem_statement alone.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.