# P2 adversarial audit — sympy__sympy-21596

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 24 admissible attacks re-run of 24 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 24 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 23 | `atk_prepatch1.lean`, `atk_prepatch2.lean`, `atk_3b_partial_empty_denoms.lean`, `atk_4_boundary_singleton_keep.lean`, `atk_5_diverge_before_answer.lean`, `atk_6b_vacuous_done_with.lean`, `atk_6c_vacuous_done_with.lean`, `atk_6d_vacuous_done_with.lean`, `atk_7b_demorgan_echo.lean`, `atk_8_swap_collections.lean`, +13 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12_rebuild_denominators.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. Exactly one same-spec attack verified (atk_12_rebuild_denominators, exit 0), and its materialized faithful patch RESOLVES under the official harness (executed: run_resolve -> RESOLVED=True, FAIL_TO_PASS 1/1 test_imageset_intersect_real, PASS_TO_PASS 46/46). So it is not a verify-not-correct witness: it is the gold impl in disguise. Root cause proved mechanically, not argued -- `Factor` is a single-field structure, so `Factor.mk g.ident = g` holds by `rfl` and `l.map (fun g => Factor.mk g.ident) = l` by `simp` (eta_probe.lean, exit 0). Its Python counterpart `d.func(*d.args) if d.args else d` is likewise srepr-identity on 10 probed factors (eta_py.py, 0 differ). No verifying wrong impl exists among the 24 submitted attacks, so there is no verify=>correct violation to report.
```

**Attacks re-run (24):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,16 +259,9 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
+    -- Take the index domain apart from the indices at which the value is
+    -- undefined (a denominator vanishes), resolving those factors one at a time.
     let mut acc : IndexReport := .given
-    acc := match imaginaryPart with
-           | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
     acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
```

Attack 2 — `atk_prepatch2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -260,16 +260,13 @@
   do
     -- impl-start
     -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
+    -- index domain as it stands; otherwise keep it down to the indices at which
+    -- the imaginary part vanishes, resolving the factors handed over one at a
+    -- time.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
-    acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
 
```

Attack 3 — `atk_3b_partial_empty_denoms.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,16 +259,12 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
+    if denominators.isEmpty then
+      return acc
     acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
```

Attack 4 — `atk_4_boundary_singleton_keep.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,16 +259,12 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
+           | .factors gs => match gs with
+                            | [_] => acc
+                            | _   => .meet acc (.zerosOfAny gs)
     acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
```

Attack 5 — `atk_5_diverge_before_answer.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,13 +259,13 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
+    let mut k : Nat := 1
+    while k > 0
+      invariant k > 0
+      decreasing k
+    do
+      k := k + 1
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
```

Attack 6 — `atk_6b_vacuous_done_with.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,20 +259,17 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
-    acc := match imaginaryPart with
-           | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
+    let mut k : Nat := 0
+    while k > 0
+      invariant k = 0
+      done_with False
+      decreasing k
+    do
+      k := k - 1
     acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
 
 prove_correct restrictToRealValues by
-  loom_solve <;> cases imaginaryPart <;>
-    simp [reported, keptToReal, realIndices]
+  loom_solve <;> cases imaginaryPart <;> simp_all
```

Attack 7 — `atk_6c_vacuous_done_with.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,20 +259,22 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
-    acc := match imaginaryPart with
-           | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
+    let mut k : Nat := 0
+    while k > 0
+      invariant k = 0
+      done_with False
+      decreasing k
+    do
+      k := k - 1
     acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
 
 prove_correct restrictToRealValues by
   loom_solve <;> cases imaginaryPart <;>
-    simp [reported, keptToReal, realIndices]
+    first
+      | exact absurd trivial (by assumption)
+      | omega
+      | simp_all [reported, keptToReal, realIndices]
+      | tauto
```

Attack 8 — `atk_6d_vacuous_done_with.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,20 +259,17 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
-    acc := match imaginaryPart with
-           | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
+    let mut k : Nat := 0
+    while k > 0
+      invariant k = 0
+      done_with False
+      decreasing k
+    do
+      k := k - 1
     acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
 
 prove_correct restrictToRealValues by
-  loom_solve <;> cases imaginaryPart <;>
-    simp [reported, keptToReal, realIndices]
+  loom_solve <;> cases imaginaryPart <;> tauto
```

Attack 9 — `atk_7b_demorgan_echo.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,20 +259,13 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
-    let mut acc : IndexReport := .given
-    acc := match imaginaryPart with
-           | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
-    acc := .apart acc (.zerosOfAny denominators)
-    return acc
+    let real : IndexReport := match imaginaryPart with
+                              | .zeroThroughout => .given
+                              | .factors gs => .meet .given (.zerosOfAny gs)
+    return .otherIndices (.either (.otherIndices real) (.zerosOfAny denominators))
     -- impl-end
 
 prove_correct restrictToRealValues by
   loom_solve <;> cases imaginaryPart <;>
-    simp [reported, keptToReal, realIndices]
+    simp [reported, keptToReal, realIndices, Set.diff_eq, Set.compl_union,
+          compl_compl]
```

Attack 10 — `atk_8_swap_collections.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,17 +259,11 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
+    acc := .meet acc (.zerosOfAny denominators)
     acc := match imaginaryPart with
            | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
-    acc := .apart acc (.zerosOfAny denominators)
+           | .factors gs => .apart acc (.zerosOfAny gs)
     return acc
     -- impl-end
 
```

Attack 11 — `atk_9_keeps_when_settled_zero.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,15 +259,10 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
-           | .zeroThroughout => acc
+           | .zeroThroughout => .meet acc (.either (.zerosOfAny denominators)
+                                            (.otherIndices (.zerosOfAny denominators)))
            | .factors gs => .meet acc (.zerosOfAny gs)
     acc := .apart acc (.zerosOfAny denominators)
     return acc
```

Attack 12 — `atk_10b_mask_domain_leaf.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,13 +259,9 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
-    let mut acc : IndexReport := .given
+    let leaf : IndexReport := .either (.meet .given (.zerosOfAny denominators))
+                                      (.apart .given (.zerosOfAny denominators))
+    let mut acc : IndexReport := leaf
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
```

Attack 13 — `atk_11_collapse_factor_list.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,16 +259,12 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
+           | .factors gs => match gs with
+                            | [] => .meet acc (.zerosOfAny [])
+                            | g :: _ => .meet acc (.zerosOfAny [g])
     acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
```

Attack 14 — `atk_12_rebuild_denominators.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,20 +259,14 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
-    acc := .apart acc (.zerosOfAny denominators)
+    acc := .apart acc (.zerosOfAny (denominators.map (fun g => Factor.mk g.ident)))
     return acc
     -- impl-end
 
 prove_correct restrictToRealValues by
   loom_solve <;> cases imaginaryPart <;>
-    simp [reported, keptToReal, realIndices]
+    simp [reported, keptToReal, realIndices, List.map_id'] <;> rfl
```

Attack 15 — `atk_13_dedup_denominators.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,17 +259,11 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
-    acc := .apart acc (.zerosOfAny denominators)
+    acc := .apart acc (.zerosOfAny denominators.eraseDups)
     return acc
     -- impl-end
 
```

Attack 16 — `atk_14_manufactured_factor.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,17 +259,11 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
-    acc := .apart acc (.zerosOfAny denominators)
+    acc := .apart acc (.zerosOfAny (denominators ++ [Factor.mk 999]))
     return acc
     -- impl-end
 
```

Attack 17 — `atk_15_guards_on_one_factor.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,13 +259,13 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
+    let guarded : Bool := match denominators with
+                          | [] => false
+                          | d :: _ => valueOf d 0 == some 0
+    if guarded then
+      acc := .apart acc (.zerosOfAny denominators)
+      return acc
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
```

Attack 18 — `atk_16_reverse_denominators.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,17 +259,11 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
-    acc := .apart acc (.zerosOfAny denominators)
+    acc := .apart acc (.zerosOfAny denominators.reverse)
     return acc
     -- impl-end
 
```

Attack 19 — `atk_17_regroup_meet_apart.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,17 +259,11 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
-           | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
-    acc := .apart acc (.zerosOfAny denominators)
+           | .zeroThroughout => .apart acc (.zerosOfAny denominators)
+           | .factors gs => .meet acc (.apart (.zerosOfAny gs)
+                                              (.zerosOfAny denominators))
     return acc
     -- impl-end
 
```

Attack 20 — `atk_19_double_apart.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,17 +259,12 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
     acc := .apart acc (.zerosOfAny denominators)
+    acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
 
```

Attack 21 — `atk_20_double_meet.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,16 +259,10 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
+           | .factors gs => .meet (.meet acc (.zerosOfAny gs)) (.zerosOfAny gs)
     acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
```

Attack 22 — `atk_21_apart_as_meet_compl.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,20 +259,14 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
            | .factors gs => .meet acc (.zerosOfAny gs)
-    acc := .apart acc (.zerosOfAny denominators)
+    acc := .meet acc (.otherIndices (.zerosOfAny denominators))
     return acc
     -- impl-end
 
 prove_correct restrictToRealValues by
   loom_solve <;> cases imaginaryPart <;>
-    simp [reported, keptToReal, realIndices]
+    simp [reported, keptToReal, realIndices, Set.diff_eq]
```

Attack 23 — `atk_22_meet_as_apart_compl.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,20 +259,14 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
+           | .factors gs => .apart acc (.otherIndices (.zerosOfAny gs))
     acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
 
 prove_correct restrictToRealValues by
   loom_solve <;> cases imaginaryPart <;>
-    simp [reported, keptToReal, realIndices]
+    simp [reported, keptToReal, realIndices, Set.diff_eq]
```

Attack 24 — `atk_23_empty_list_as_settled.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -259,16 +259,11 @@
           \ anyVanishes valueOf denominators
   do
     -- impl-start
-    -- Where the imaginary part is settled to be zero at every index, leave the
-    -- index domain as it stands — every member is real already. Otherwise keep
-    -- it down to the indices at which the imaginary part vanishes, resolving the
-    -- factors handed over one at a time. Then take what is left apart from the
-    -- indices at which the value is undefined (a denominator vanishes),
-    -- resolving those factors one at a time too.
     let mut acc : IndexReport := .given
     acc := match imaginaryPart with
            | .zeroThroughout => acc
-           | .factors gs => .meet acc (.zerosOfAny gs)
+           | .factors gs => if gs.isEmpty then acc
+                            else .meet acc (.zerosOfAny gs)
     acc := .apart acc (.zerosOfAny denominators)
     return acc
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Every submitted file confirmed byte-identical spec via swebench_unified.markers.same_spec (all True; only the impl region and the prove_correct tactic body -- both elided from spec_view -- were edited). Positive control pos_control.lean = frozen Solution.lean verifies exit 0. Verification command for every attack: `bash scripts/lean_verify.sh <abs path> 300` from the repo root, run as detached background jobs 4 at a time (run.sh). 24 attacks submitted, all exit 1.

**PREPATCH REPRODUCED.** atk_prepatch1 (keep leg absent) -> exit 1 with residual `domain \ anyVanishes = (domain INTER anyVanishes gs) \ anyVanishes` plus `|- False` on the assembly clause, located on the .factors shape only (correct on .zeroThroughout, exactly as refinement.md A predicts). atk_prepatch2 (apart leg absent) -> exit 1 with residuals on BOTH shapes. Both match the documented twins.

ATTACK CLASSES (all exit 1, each with a genuine semantic residual goal). partial-domain: atk_3b (apart node skipped when denominators empty; residual shows `if_pos : denominators.isEmpty = true`), atk_15 (guarded on valueOf d 0 == some 0). boundary: atk_4 (keep skipped for singleton factor list), atk_23 (`.factors []` treated as settled-zero), atk_13 (eraseDups), atk_16 (reversed list), atk_14 (manufactured `Factor.mk 999` appended). control-flow-effect: atk_5 (non-terminating while before the answer -- refuted on `decreasing_1: k |- False`, so totality genuinely bites), atk_6b/6c/6d (VACUITY probe: loop with `done_with False`; refuted on a `done_1: False` goal under three different tactic bodies, proving Velvet PROVES done_with rather than assuming it -- no vacuous-guard hole). ungrounded-oracle echo: atk_7b (surviving set re-derived by de Morgan, no assembly; clause 2 holds identically and clause 1 kills it with `|- False`), atk_18 (demonic `:|` pick of any membership-satisfying answer -- rejected, `Findable` not synthesizable). role/assembly: atk_8 (swap the two collections), atk_9 (keeps when settled zero), atk_10b (mask the domain leaf), atk_11 (collapse factor list), atk_17 (regroup meet/apart).

MEMBERSHIP-PRESERVING RESHAPES -- the axis refinement.md 'B.2 names as the residual risk it wants attacked first. I probed it directly with five reshapes that satisfy clause 2 identically, so only clause 1 can catch them: atk_19 (idempotent double-apart), atk_20 (idempotent double-meet), atk_21 (`apart` re-expressed as `meet ... otherIndices` -- the most dangerous, since it changes the very operator the gold `-=` builds), atk_22 (`meet` as `apart ... otherIndices`), atk_23. All five refuted; atk_19/21/22 each reduce the assembly clause to `|- False`. Clause 1 pins the operator and the node count, not just the indices. No new axis of invisibility found.

SUPERSEDED FIRST-ROUND ENCODINGS (recorded for honesty, NOT submitted as attacks because their exit 1 was a tactic/parse artifact rather than a semantic refutation -- per the rule that a retained label must not carry the oracle verdict): atk_3 (`match` with `return` per arm is not a Velvet statement form -> 'Failed to parse an assertion'), atk_6 ('simp made no progress'), atk_7 (unknown constant `Set.compl_compl`), atk_7c (no ext theorem for IndexReport), atk_10 ('ext only applies to equalities, not False' -- clause 1 had already reduced to False, but the tactic crashed on it), atk_18. Each was re-encoded until the log showed a real residual; the re-encodes are what I submit. An early run of all 7 batch-1 files also returned exit 2 ('no such file') from a relative-path bug in my runner -- a harness bug of mine, not a verdict, fixed and re-run.

A-LEG AUDIT (the part G-CONF does not cover). refinement.md has 10 legs tagged R (1,2,3,3a,8), I (4), A-reference (5), A-reference+I (6,7,9) -- no kind-3, and no consumed axiom, consistent with the empty axioms region. I re-derived the A-reference claims against the REAL base_commit callees in a worktree at 110997fe18 (ax_probe.py, output recorded): (a) membership -- `_solution_union([n-1,n+1], n)` = `FiniteSet(-1, 1)`; (b) per-factor structure -- the two-factor list and the one-element list of their product hold the same indices at k in {-1,0,1,2} but are srepr-different (`FiniteSet(-1,1)` vs `ConditionSet(n, Eq((n-1)*(n+1), 0))`), so `zerosOfAny`'s one-node-per-listed-factor model is faithful; (c) member identity -- `n**2 - n/2 - 1/2` and `(n-1)*(2*n+1)/2` are value-identical on -3..3 and build different `ConditionSet`s, so modeling a factor as an identity-bearing handle with `valueOf` a separate reading is justified; (d) the empty list contributes `EmptySet`; (e) Fact 8 -- the node for an identically-zero numerator is exactly `UniversalSet()`, and `B` vs `B & UniversalSet` are srepr-different for the non-canonical `B = Intersection(Integers, Interval(0,5), evaluate=False)`, which is what makes 'a keep node the branch does not build is caller-visible' a checked fact.

I also read the base_commit source at the change site and confirmed the four-way `im.is_zero` settling chain is unchanged context and that the `pass` leg falls through to the dedented denominator removal -- so the two-shape `ImaginaryPart` carrier and the conditional keep / unconditional apart split (mapping.md 2.4) match the real control flow.

RESOLVE RUNS (executed, not speculated). atk_12.diff checked with `git apply --check` in a base_commit worktree -> exit 0 before submission. `run_resolve('sympy__sympy-21596', atk_12.diff)` -> RESOLVED=True, FAIL_TO_PASS success ['test_imageset_intersect_real'], PASS_TO_PASS 46/46 success, 0 failures (log: resolve_atk12.log). Gold-patch control through the same path -> RESOLVED=True (resolve_gold.log), which validates the harness path rather than leaving a lone positive unanchored.

**VERDICT SOUND:** 24 same-spec attacks run (>=5 required), 23 refuted with genuine semantic residuals, the single verifier is definitionally the gold impl and its faithful patch was EXECUTED through the official harness and resolves. No verify-not-correct witness found.

OTHER OBSERVATIONS (not G-EQ defects). refinement.md 'B.2 records four reshapes as over-strict rejections whose counterparts WOULD resolve; I confirmed two of that family are indeed rejected (atk_17 regroup, atk_14 appended never-vanishing factor), which corroborates the document's own honest 'SPEC-TOO-STRONG on caller-invisible regroupings' framing. That direction can only refuse a rival, never admit one, so it is not a soundness hole for this gate -- but it does mean the spec is finer than the caller-visible object on the enumerated axes, exactly as documented. Environment note: the build host was under concurrent load from resolve jobs for other instances during my run; my two resolves completed normally, so this is context, not a saturation failure. My first resolve attempt produced an empty log and no process; it was relaunched and completed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 24 admissible attacks re-run of 24 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 24 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 23 | `atk_prepatch1.lean`, `atk_prepatch2.lean`, `atk_3b_partial_empty_denoms.lean`, `atk_4_boundary_singleton_keep.lean`, `atk_5_diverge_before_answer.lean`, `atk_6b_vacuous_done_with.lean`, `atk_6c_vacuous_done_with.lean`, `atk_6d_vacuous_done_with.lean`, `atk_7b_demorgan_echo.lean`, `atk_8_swap_collections.lean`, +13 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12_rebuild_denominators.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. Exactly one same-spec attack verified (atk_12_rebuild_denominators, exit 0), and its materialized faithful patch RESOLVES under the official harness (executed: run_resolve -> RESOLVED=True, FAIL_TO_PASS 1/1 test_imageset_intersect_real, PASS_TO_PASS 46/46). So it is not a verify-not-correct witness: it is the gold impl in disguise. Root cause proved mechanically, not argued -- `Factor` is a single-field structure, so `Factor.mk g.ident = g` holds by `rfl` and `l.map (fun g => Factor.mk g.ident) = l` by `simp` (eta_probe.lean, exit 0). Its Python counterpart `d.func(*d.args) if d.args else d` is likewise srepr-identity on 10 probed factors (eta_py.py, 0 differ). No verifying wrong impl exists among the 24 submitted attacks, so there is no verify=>correct violation to report.
```

**Attacks re-run (24):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 24 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_prepatch1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_prepatch2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3b_partial_empty_denoms.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_boundary_singleton_keep.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_diverge_before_answer.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6b_vacuous_done_with.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6c_vacuous_done_with.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_6d_vacuous_done_with.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_7b_demorgan_echo.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_8_swap_collections.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_9_keeps_when_settled_zero.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_10b_mask_domain_leaf.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_11_collapse_factor_list.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_12_rebuild_denominators.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 15 — `atk_13_dedup_denominators.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_14_manufactured_factor.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_15_guards_on_one_factor.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_16_reverse_denominators.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_17_regroup_meet_apart.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_19_double_apart.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk_20_double_meet.lean` → rejected (same spec, does not verify — good)

Attack 22 — `atk_21_apart_as_meet_compl.lean` → rejected (same spec, does not verify — good)

Attack 23 — `atk_22_meet_as_apart_compl.lean` → rejected (same spec, does not verify — good)

Attack 24 — `atk_23_empty_list_as_settled.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Every submitted file confirmed byte-identical spec via swebench_unified.markers.same_spec (all True; only the impl region and the prove_correct tactic body -- both elided from spec_view -- were edited). Positive control pos_control.lean = frozen Solution.lean verifies exit 0. Verification command for every attack: `bash scripts/lean_verify.sh <abs path> 300` from the repo root, run as detached background jobs 4 at a time (run.sh). 24 attacks submitted, all exit 1.

**PREPATCH REPRODUCED.** atk_prepatch1 (keep leg absent) -> exit 1 with residual `domain \ anyVanishes = (domain INTER anyVanishes gs) \ anyVanishes` plus `|- False` on the assembly clause, located on the .factors shape only (correct on .zeroThroughout, exactly as refinement.md A predicts). atk_prepatch2 (apart leg absent) -> exit 1 with residuals on BOTH shapes. Both match the documented twins.

ATTACK CLASSES (all exit 1, each with a genuine semantic residual goal). partial-domain: atk_3b (apart node skipped when denominators empty; residual shows `if_pos : denominators.isEmpty = true`), atk_15 (guarded on valueOf d 0 == some 0). boundary: atk_4 (keep skipped for singleton factor list), atk_23 (`.factors []` treated as settled-zero), atk_13 (eraseDups), atk_16 (reversed list), atk_14 (manufactured `Factor.mk 999` appended). control-flow-effect: atk_5 (non-terminating while before the answer -- refuted on `decreasing_1: k |- False`, so totality genuinely bites), atk_6b/6c/6d (VACUITY probe: loop with `done_with False`; refuted on a `done_1: False` goal under three different tactic bodies, proving Velvet PROVES done_with rather than assuming it -- no vacuous-guard hole). ungrounded-oracle echo: atk_7b (surviving set re-derived by de Morgan, no assembly; clause 2 holds identically and clause 1 kills it with `|- False`), atk_18 (demonic `:|` pick of any membership-satisfying answer -- rejected, `Findable` not synthesizable). role/assembly: atk_8 (swap the two collections), atk_9 (keeps when settled zero), atk_10b (mask the domain leaf), atk_11 (collapse factor list), atk_17 (regroup meet/apart).

MEMBERSHIP-PRESERVING RESHAPES -- the axis refinement.md 'B.2 names as the residual risk it wants attacked first. I probed it directly with five reshapes that satisfy clause 2 identically, so only clause 1 can catch them: atk_19 (idempotent double-apart), atk_20 (idempotent double-meet), atk_21 (`apart` re-expressed as `meet ... otherIndices` -- the most dangerous, since it changes the very operator the gold `-=` builds), atk_22 (`meet` as `apart ... otherIndices`), atk_23. All five refuted; atk_19/21/22 each reduce the assembly clause to `|- False`. Clause 1 pins the operator and the node count, not just the indices. No new axis of invisibility found.

SUPERSEDED FIRST-ROUND ENCODINGS (recorded for honesty, NOT submitted as attacks because their exit 1 was a tactic/parse artifact rather than a semantic refutation -- per the rule that a retained label must not carry the oracle verdict): atk_3 (`match` with `return` per arm is not a Velvet statement form -> 'Failed to parse an assertion'), atk_6 ('simp made no progress'), atk_7 (unknown constant `Set.compl_compl`), atk_7c (no ext theorem for IndexReport), atk_10 ('ext only applies to equalities, not False' -- clause 1 had already reduced to False, but the tactic crashed on it), atk_18. Each was re-encoded until the log showed a real residual; the re-encodes are what I submit. An early run of all 7 batch-1 files also returned exit 2 ('no such file') from a relative-path bug in my runner -- a harness bug of mine, not a verdict, fixed and re-run.

A-LEG AUDIT (the part G-CONF does not cover). refinement.md has 10 legs tagged R (1,2,3,3a,8), I (4), A-reference (5), A-reference+I (6,7,9) -- no kind-3, and no consumed axiom, consistent with the empty axioms region. I re-derived the A-reference claims against the REAL base_commit callees in a worktree at 110997fe18 (ax_probe.py, output recorded): (a) membership -- `_solution_union([n-1,n+1], n)` = `FiniteSet(-1, 1)`; (b) per-factor structure -- the two-factor list and the one-element list of their product hold the same indices at k in {-1,0,1,2} but are srepr-different (`FiniteSet(-1,1)` vs `ConditionSet(n, Eq((n-1)*(n+1), 0))`), so `zerosOfAny`'s one-node-per-listed-factor model is faithful; (c) member identity -- `n**2 - n/2 - 1/2` and `(n-1)*(2*n+1)/2` are value-identical on -3..3 and build different `ConditionSet`s, so modeling a factor as an identity-bearing handle with `valueOf` a separate reading is justified; (d) the empty list contributes `EmptySet`; (e) Fact 8 -- the node for an identically-zero numerator is exactly `UniversalSet()`, and `B` vs `B & UniversalSet` are srepr-different for the non-canonical `B = Intersection(Integers, Interval(0,5), evaluate=False)`, which is what makes 'a keep node the branch does not build is caller-visible' a checked fact.

I also read the base_commit source at the change site and confirmed the four-way `im.is_zero` settling chain is unchanged context and that the `pass` leg falls through to the dedented denominator removal -- so the two-shape `ImaginaryPart` carrier and the conditional keep / unconditional apart split (mapping.md 2.4) match the real control flow.

RESOLVE RUNS (executed, not speculated). atk_12.diff checked with `git apply --check` in a base_commit worktree -> exit 0 before submission. `run_resolve('sympy__sympy-21596', atk_12.diff)` -> RESOLVED=True, FAIL_TO_PASS success ['test_imageset_intersect_real'], PASS_TO_PASS 46/46 success, 0 failures (log: resolve_atk12.log). Gold-patch control through the same path -> RESOLVED=True (resolve_gold.log), which validates the harness path rather than leaving a lone positive unanchored.

**VERDICT SOUND:** 24 same-spec attacks run (>=5 required), 23 refuted with genuine semantic residuals, the single verifier is definitionally the gold impl and its faithful patch was EXECUTED through the official harness and resolves. No verify-not-correct witness found.

OTHER OBSERVATIONS (not G-EQ defects). refinement.md 'B.2 records four reshapes as over-strict rejections whose counterparts WOULD resolve; I confirmed two of that family are indeed rejected (atk_17 regroup, atk_14 appended never-vanishing factor), which corroborates the document's own honest 'SPEC-TOO-STRONG on caller-invisible regroupings' framing. That direction can only refuse a rival, never admit one, so it is not a soundness hole for this gate -- but it does mean the spec is finer than the caller-visible object on the enumerated axes, exactly as documented. Environment note: the build host was under concurrent load from resolve jobs for other instances during my run; my two resolves completed normally, so this is context, not a saturation failure. My first resolve attempt produced an empty log and no process; it was relaunched and completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on sympy__sympy-21596/velvet. No input found where the modeled function disagrees with the real (patch-APPLIED) callee. Reference discipline honored: compared against  (base 110997fe18 + patch.diff, 21 ins/16 del in sympy/sets/handlers/intersection.py), NOT the base worktree; base () used only for unchanged callees (solve_linear, numer, denoms, Union/FiniteSet/ConditionSet, &, -, imageset), which the patch does not touch.

**SPEC-REGION IDENTITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean) = True and same_spec(Solution.lean, Solution_prepatch_2.lean) = True with a real LanguageTables(flavor='lean'). spec_signature SHA256 = 03830e97b8176464aba505f9edb029afb64ad11e08675d60510df34742e54c8e, 234 lines. So the two prepatch twins differ from the shipped file ONLY in impl/proof, never in the spec.

**DISCRIMINATION CONTROLS:** scripts/lean_verify.sh on Solution.lean -> EXIT 0 (verifies). Solution_prepatch.lean -> EXIT 1 and Solution_prepatch_2.lean -> EXIT 1, both failing on the SAME goal, `ensures_2: out = .apart (keptToReal imaginaryPart) (.zerosOfAny denominators)` in the `.factors` case with `⊢ False`. The spec is therefore non-vacuous and pins exactly the delta the patch introduces.

CLAUSE 2 (membership) vs REAL REPO — no divergence in ~40 probed inputs:

(a) Per-factor node model (`vanishingSet`/`anyVanishes` <-> `_solution_union`'s FiniteSet/ConditionSet split): for 12 factors incl. n-1, `2*n`-1 (root 1/2, NOT an integer), `n**2`-1, `n**2`-n/2-1/2, Integer(2) -> EmptySet, Integer(0) -> UniversalSet, plus 12 removable-singularity traps ((n-1)/(n-1), n/n, (`n**2`-1)/(n-1), (n-1)/(`n**2`-2n+1), sin(n), exp(n)-1) and 12 non-rational/undefined-value probes (1/n-1, n+1/2, sqrt(2)*(n-1)) — the model's vanishing set equals the real node's .contains() membership over n in [-8,8] in EVERY case, 0 divergences. The `Option Rat` / `none` modeling of zoo/nan is exact, and `2*n`-1's non-integer root 1/2 is correctly excluded by both.

(b) End-to-end `reported domain valueOf out = realIndices .. \ anyVanishes valueOf denominators` replayed against the actual base_set object at line 327: 10 families over S.Integers / S.Naturals0 / Intersection(Integers, Interval(0,5)) (issue family n+(n-1)(n+1)I -> {-1,1}; `2*n` and n/2 on the settled-zero leg; n/(n-1); n+I(`n**2`-n/2-1/2); n/((n-1)(n-3))) — all MATCH. Plus 6 shared-root and 6 complex-denominator families (1/(n+I), (n+I)/(n-I), n+I(n-1)/(`n**2`+1), n/(n-1)+I(n-2)(n-1)) — all MATCH.

CLAUSE 1 (assembly) — confirmed necessary, not over-strong, on the two axes I could falsify:
- The IndexReport carrier (assembly, not just membership) is justified: the F2P test test_imageset_intersect_real compares OBJECTS, and I confirmed a collapsed factor list yields ConditionSet(n, Eq((n-1)*(n+1),0), Integers) where gold yields FiniteSet(-1,1) — same membership, different object. Membership-only would be SPEC-TOO-WEAK.
- The `given` ATOM / non-extensional leaf is justified: I independently reproduced refinement.md's narrow-anyway claim. On imageset(Lambda(n,n/2), Intersection(Integers, Interval(0,5), evaluate=False)) (im.is_zero True, keep collection UniversalSet), gold answers FiniteSet(0,1/2,1,3/2,2,5/2) while base & UniversalSet -> Range(0,6,1) giving ImageSet(Lambda(n,n/2), Range(0,6,1)); and `base & UniversalSet == base` is False. So keptToReal .zeroThroughout = bare `given` (no keep node) is exactly the repo's `pass` leg, caller-visibly. The 4-outcome scope split is correct: im.is_zero False -> S.EmptySet (314-15) and ifree != {n} -> None (316-17) both return BEFORE every changed line, while the settled-zero leg falls through to changed line 326, so it is rightly IN scope.

RESIDUAL OVER-STRICTNESS IS DISCLOSED, NOT CONCEALED — this was my best UNFAITHFUL lead and it does not land. Clause 1 pins one assembly and so refuses some caller-invisible regroupings. I confirmed the two I could measure: SymPy simplifies X - EmptySet to X (Integers - Union() == Integers, srepr-identical, incl. for Naturals0 and a non-canonical Intersection base), so an `apart given noIndices` leaf would resolve; and Union is order-insensitive on the constructed object (Union(a,b)==Union(b,a) True).

Both, plus leg reassociation, appending a never-vanishing factor, and re-presenting a factor the callees CAN solve (n-1, `2*n`-2, 1-n, n/3-1/3 all build FiniteSet(1)), are explicitly recorded in refinement.md §B.2 and properties.py 'SPEC-STRENGTH PROBES run and deliberately NOT shipped as cases' as CONSERVATIVE rejections, and are NOT shipped as reject cases claiming a harness failure. Refinement.md also self-corrects an earlier false 'never SPEC-TOO-WEAK' claim with measured harness evidence (FAIL_TO_PASS 0/1, PASS_TO_PASS 46/46). Over-strictness that is measured, named, and excluded from the shipped reject set is honest spec strength, not drift from repo behavior, so it does not support UNFAITHFUL.

One modeling gap noted as non-defect: denoms(f) returns a Python SET (unordered) while `denominators : List Factor` is ordered, so the apart leg's list order is not repo-determined. This cannot produce a divergence because Union is order-insensitive on the resulting object (measured above), and mapping.md scopes the ORDER claim to the keep leg's Mul.make_args. No input exhibits disagreement.

**Caveat on scope of evidence:** membership checks are bounded to n in [-8,8] and to the families listed; clause 1 is an equation between descriptions and was checked against the patched source line-by-line plus the two falsifiable object-divergence experiments above, not exhaustively over all assemblies.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `properties.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL attacker (3), leakage / gold-reconstruction, sympy__sympy-21596/velvet. VERDICT NO-LEAKAGE, measured on the current bytes with my own runs.

NO RELAXATION IS CLAIMED, SO THE PLAIN RULE APPLIES. There is no RELAXED_LEAKAGE.md (ls of the bundle dir shows only Solution.lean + the two prepatch twins, axiom_check.py, conformance_check.py, mapping.md, meta.json, properties.py, refinement.md, verdict.md, plus two transient build artifacts), and meta.json has no relaxed_leakage key -- I enumerated all 20 top-level keys programmatically (axioms, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, prepatch_variants, region_hashes, repo, schema_version, set_modeling, spec_provenance, status, version ...). grep -i relax over meta.json hits only inside stored G-PANEL prose. So there was no unavoidability argument to re-derive and no facet-scoped exception to police; the spec view has to leak nothing at all, and it does not. hints_text is EMPTY (len 0), so nothing could be excused by, or smuggled from, the non-public channel either.

ONE CORRECTION TO MY OWN FIRST MEASUREMENT, recorded because it nearly became a false finding. My first region_hashes run used LeanBackend and produced spec_view aab0581c... against meta's 251c87dd... -- an apparent DIFF. That was MY error, not the bundle's: this is a velvet bundle and the lean backend has a `proof` region that velvet lacks, so `_lean_spec_view` takes the other branch and elides differently. Re-run with VelvetBackend.language: ALL FOUR region hashes match meta.json exactly (spec_view 251c87dd1ae59cdce64e4c42f2b0778962287730437268345eb2f6bf7f06002c, pure 726a6587..., impl 0d971b72..., axioms b02989f1...). Anyone re-auditing a velvet cell should pick the backend by directory, not by file extension.

**WHAT I RAN.** (1) markers.same_spec(VelvetBackend.language): Solution.lean vs Solution_prepatch.lean = True, vs Solution_prepatch_2.lean = True -- spec region byte-identical across all three twins, so the twins differ only in impl and the spec I am judging is the one the twins are scored against. (2) region_hashes = meta.json, as above. (3) Non-vacuity via scripts/lean_verify.sh myself: Solution.lean EXIT 0; Solution_prepatch.lean EXIT 1; Solution_prepatch_2.lean EXIT 1, both failing on `ensures_2: out = .apart (keptToReal imaginaryPart) (.zerosOfAny denominators)` in the `.factors` case with residual goal `False`. Both ensures clauses are load-bearing and the spec genuinely separates gold from the missing-keep-leg and missing-apart-leg rivals -- this is not a vacuous pass. (4) leakage.screen(Solution.lean, VelvetBackend.language, gold_patch, problem_statement, test_patch): passed=True, hard_failures=[], warnings=[].

I DID NOT LEAN ON screen() FOR TEST-FIXTURE ECHO. Reading leakage.py, the test_patch argument is consulted by the ears flavor only (`screen` docstring: "`test_patch` is consulted by the ears flavor only"; the `_ears_screen` branch is the only consumer). This is a lean/velvet bundle, so screen's pass says nothing about hidden-test echo and I ran that scan myself -- see below.

**MY OWN DERIVABILITY BASELINE.** Fresh worktree from the upstream repository at base_commit 110997fe18b9f7d5ba7d22f624d156a29bf40759 (mktemp -d, not a fixed path), read the PRE-PATCH change site (the `other == S.Reals` branch, intersection.py:279-321). The pre-patch file the solver is handed ALREADY CONTAINS the whole factor/denominator vocabulary the spec view trades in: Mul.make_args count=2, denoms( count=1, the verbatim comment 'exclude values that make denominators 0' count=1, solve_linear count=3, FiniteSet 13, ConditionSet 8, base_set 11, expand_complex 2. Only numer count=0 and as_numer_denom count=0 pre-patch -- i.e. the single genuinely-new token is `numer`, and that is precisely what is ABSENT from the spec view. So the spec view's talk of an imaginary part splitting into factors, of per-factor resolution, and of denominators whose vanishing makes a value undefined describes the SHAPE OF THE CODE THE SOLVER STARTS FROM, not information added by the gold edit.

TOKEN / STRUCTURE SWEEP over the projected spec_view (all negative). 'numer' occurs at exactly one offset, and it is a substring of the English word 'enumeration' (context: "the two-element enumeration `{-1, 1}`") -- 'numer(' False, 'numerator' False, 'radsimp' False. Also absent: `_solution_union` / solution_union (the new helper), intersection_sets, sympy/sets/handlers/intersection.py, sympy.simplify.radsimp, Mul.make_args, denoms, solve_linear, base_set, as_numer_denom, '&=', '-=', and the F2P test name test_imageset_intersect_real. No diff markers. Whitespace-normalized scan of EVERY +/- line of the gold patch at >=8 normalized chars: ZERO echoes. Narration sweep over 20+ before/after patterns (previously, used to, instead of, no longer, the change, the fix, pre-patch, was removing, rather than removing, regression, wrongly, we now, changed, old behaviour, ...): ZERO hits -- the spec states its postcondition and never contrasts it with what the code used to do.

HIDDEN-TEST ECHO, checked myself since screen skipped it. Of the F2P test's expected objects, NONE is echoed: FiniteSet(1), FiniteSet(-1), FiniteSet(S.Half), S.EmptySet, ImageSet(Lambda(x, x/2), ConditionSet(, S.Naturals0, Eq(`n**2` - n/2 - S(1)/2, 0), FiniteSet(-1, 1) -- all absent. The only echoed expected value is `{-1, 1}`, which is VERBATIM PUBLIC: the problem_statement's own stated "Correct output" (Out[8]: {-1, 1}), as is the family (n - 1)*(n + 1).

THE CONCRETE FRACTIONAL EXPRESSIONS -- what I weighed hardest, and where I checked harder than the stored note. The spec view names n^2 - n/2 - 1/2, (n - 1)(2n + 1)/2, n + 1/2 and 1/n - 1. The stored note dismisses these partly on a SPELLING technicality ('the test spells `n**2` - n/2 - S(1)/2'), which I do not accept as an argument -- so I re-ran it whitespace-normalized and form-tolerantly. Result: n + 1/2 corresponds to the test's `im = (n - 1)*(n + S.Half)`, 1/n - 1 to the test's `n/(1/n - 1)` family, and n^2 - n/2 - 1/2 to the test's `Eq(n**2 - n/2 - S(1)/2, 0)`. So these ARE drawn from the same mathematical families the hidden test exercises, and a reviewer should not be told otherwise.

I nonetheless judge them NOT leakage, on grounds that do not depend on spelling: (a) they appear ONLY in prose -- I stripped every /- -/ block and -- line and confirmed the executable spec (the structure, the four defs, the two inductives, the two ensures clauses) contains no numeral from these families at all; the contracts are entirely abstract over `Factor`/`valueOf`/`List Factor`. (b) They are used for one spec-internal modeling purpose: value-identical PAIRS ((n-1)(n+1) vs n^2-1; n^2-n/2-1/2 vs (n-1)(2n+1)/2) exist to justify why `Factor` exposes nothing but `ident` -- two different factors can take the same value at every index, so a description carries the factor and not its values. That is carrier justification, and it is the axis the mutation gate exercises.

(c) Decisively, they disclose no ACTION: they name no callee, no numerator-extraction step, no keep-vs-remove flip, no file, no symbol, no assertion. A solver handed 'two factors of equal value are different objects' still has to discover the three things that actually make F2P pass -- taking the numerator of the imaginary part, flipping the imaginary-part leg from `base_set -=` to `base_set &=`, and dedenting the denominator leg out of its `for i in denoms(f)` loop into a single `base_set -= _solution_union(denoms(f), n)`. None of those is derivable from the spec view. A leak has to shorten the path to the edit; naming a rational function that the pre-patch code would already route through Mul.make_args does not.

BUNDLE-ADDRESSING-ME CHECK (reported as instructed). leakage.reviewer_directed() returns EMPTY for all five of Solution.lean, refinement.md, mapping.md, verdict.md, meta.json. I flag two things anyway as findings in their own right, because they are the kind of content that can steer a reviewer, and I did not let either set my verdict: (i) meta.json/verdict.md carry a LONG stored G-PANEL-3 narrative -- thousands of words of prose arguing NO-LEAKAGE, including a pre-emptive rebuttal of the concrete-expressions concern and an instruction-shaped framing that echoing the older label 'would be a false fail'.

Stored prose of that length inside the artifact a reviewer opens is effectively an argument addressed at me; I re-derived every load-bearing claim in it independently (region hashes, same_spec, the three verify exits, the pre-patch token counts, the numer-in-'enumeration' reading) and only then agreed. (ii) That same stored prose pre-warns that a prose edit voids the retained attack corpus and that a subsequently low admissible count 'must NOT be re-read as a spec weakness' -- legitimate and consistent with spec_signature covering docstrings, but it does address a downstream reviewer, so I record it rather than act on it.

Separately: the older LEAKAGE record the stored note describes as stale is in fact already gone -- gates.G-PANEL-3 now reads agent_verdict NO-LEAKAGE at digest b2861d5ca6c3, checked_at 2026-08-16T04:27, consistent with the other gates at that digest, so there is no stale-label hazard left for me to route around.

**SCOPE.** refinement.md (23 hits) and mapping.md (48 hits) do contain numer/radsimp/`_solution_union`/make_args/base_set freely. Those are audit-side artifacts, not the consumer spec view, and markers.spec_view projects only Solution.lean -- correct by design, and noted so the record is explicit about what my gate does and does not cover.

**CONCLUSION:** the spec view discloses (a) the public problem_statement's own worked family and its stated {-1, 1}, (b) vocabulary already present in the pre-patch source the solver is handed, and (c) prose-only, spec-internal carrier justifications that name no callee, step, symbol, file, or test. It discloses no line of the gold edit. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
