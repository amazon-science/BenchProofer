# P2 adversarial audit — matplotlib__matplotlib-14623

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 24 admissible attacks re-run of 24 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 24 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_01_setter_sibling_echo__p0.lean`, `atk_01_setter_sibling_echo__p1.lean`, `atk_01_setter_sibling_echo__p2.lean`, `atk_01_setter_sibling_echo__p3.lean`, `atk_02_setter_oracle_echo__p0.lean`, `atk_02_setter_oracle_echo__p1.lean`, `atk_02_setter_oracle_echo__p2.lean`, `atk_02_setter_oracle_echo__p3.lean`, +8 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_03_member_axiom_echo__p0.lean`, `atk_04_setter_chain_reversed_probe__p0.lean`, `atk_05_setter_chain_nested_probe__p0.lean`, `atk_08_stub_chain_double__p0.lean`, `atk_09_setter_guard_not_le__p2.lean`, `atk_10_member_rewiden_probe__p0.lean`, `atk_11_setter_origin_chain_probe__p0.lean`, +1 more |

**Non-vacuity.** The positive control `atk_00_positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying same-spec wrong impl was found whose faithful refined patch fails to resolve. 12 distinct attack families were encoded (each in up to 4 proof-script variants, since prove_correct bodies are ELIDED from the spec view and therefore mutable while staying same_spec -- a surface the prior pass did not exercise). 4 families were REJECTED under EVERY proof script with genuinely-false residual goals; 8 families verified, and all 8 faithful refined patches were materialized, git-apply-checked at base_commit, and EXECUTED through the official harness: all 8 resolved at exact gold parity (1/1 F2P, 400/400 P2P), matching the gold control. The 8 verifying impls are all behaviourally equal to gold on the observable committed pair -- they differ only in the NUMBER/ARGUMENTS of invisible callee invocations, or in inlining a symmetric callee. Notably the strongest break candidate (atk_11, a discarded chain probe at originEndpoint, which refines to a literal nonsingular(0,0) whose LogLocator branch emits a spurious 'Data has no positive values' warning gold never emits, on the F2P test's own log-scale leg) still resolved: the harness runs plain `pytest -rA` with no -W error, and no P2P test asserts warning counts around limit setting.
```

**Attacks re-run (24):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_01_setter_sibling_echo__p0.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,12 +283,10 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
+    let _n ← normalizeRange lo hi
     let swapped := lo > hi
-    let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
-    let out := if swapped then (n.2, n.1) else (n.1, n.2)
+    let m := defaultMemberPair lo hi
+    let out := if swapped then (m.2, m.1) else (m.1, m.2)
     return out
     -- impl-end
 
```

Attack 2 — `atk_01_setter_sibling_echo__p1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,12 +283,10 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
+    let _n ← normalizeRange lo hi
     let swapped := lo > hi
-    let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
-    let out := if swapped then (n.2, n.1) else (n.1, n.2)
+    let m := defaultMemberPair lo hi
+    let out := if swapped then (m.2, m.1) else (m.1, m.2)
     return out
     -- impl-end
 
@@ -304,8 +302,5 @@
   loom_solve
 
 prove_correct commitLimits by
-  loom_solve <;>
-    intros <;>
-    split <;>
-    simp_all [asymm, not_lt] <;>
-    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)
+  loom_solve <;> intros <;>
+    simp_all [committedLimits, defaultMemberPair, asymm, not_lt, lt_iff_le_not_le]
```

Attack 3 — `atk_01_setter_sibling_echo__p2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,12 +283,10 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
+    let _n ← normalizeRange lo hi
     let swapped := lo > hi
-    let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
-    let out := if swapped then (n.2, n.1) else (n.1, n.2)
+    let m := defaultMemberPair lo hi
+    let out := if swapped then (m.2, m.1) else (m.1, m.2)
     return out
     -- impl-end
 
@@ -304,8 +302,8 @@
   loom_solve
 
 prove_correct commitLimits by
-  loom_solve <;>
-    intros <;>
-    split <;>
-    simp_all [asymm, not_lt] <;>
-    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)
+  loom_solve <;> intros <;> first
+    | rfl
+    | (split <;> simp_all [committedLimits, defaultMemberPair, asymm, not_lt])
+    | simp_all [committedLimits, defaultMemberPair, asymm, not_lt]
+    | grind
```

Attack 4 — `atk_01_setter_sibling_echo__p3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,12 +283,10 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
+    let _n ← normalizeRange lo hi
     let swapped := lo > hi
-    let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
-    let out := if swapped then (n.2, n.1) else (n.1, n.2)
+    let m := defaultMemberPair lo hi
+    let out := if swapped then (m.2, m.1) else (m.1, m.2)
     return out
     -- impl-end
 
@@ -304,8 +302,4 @@
   loom_solve
 
 prove_correct commitLimits by
-  loom_solve <;>
-    intros <;>
-    split <;>
-    simp_all [asymm, not_lt] <;>
-    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)
+  loom_solve <;> intros <;> grind [committedLimits, defaultMemberPair]
```

Attack 5 — `atk_02_setter_oracle_echo__p0.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,13 +283,7 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
-    let swapped := lo > hi
-    let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
-    let out := if swapped then (n.2, n.1) else (n.1, n.2)
-    return out
+    return committedLimits lo hi
     -- impl-end
 
 end
```

Attack 6 — `atk_02_setter_oracle_echo__p1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,13 +283,7 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
-    let swapped := lo > hi
-    let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
-    let out := if swapped then (n.2, n.1) else (n.1, n.2)
-    return out
+    return committedLimits lo hi
     -- impl-end
 
 end
@@ -304,8 +298,5 @@
   loom_solve
 
 prove_correct commitLimits by
-  loom_solve <;>
-    intros <;>
-    split <;>
-    simp_all [asymm, not_lt] <;>
-    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)
+  loom_solve <;> intros <;>
+    simp_all [committedLimits, defaultMemberPair, asymm, not_lt, lt_iff_le_not_le]
```

Attack 7 — `atk_02_setter_oracle_echo__p2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,13 +283,7 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
-    let swapped := lo > hi
-    let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
-    let out := if swapped then (n.2, n.1) else (n.1, n.2)
-    return out
+    return committedLimits lo hi
     -- impl-end
 
 end
@@ -304,8 +298,8 @@
   loom_solve
 
 prove_correct commitLimits by
-  loom_solve <;>
-    intros <;>
-    split <;>
-    simp_all [asymm, not_lt] <;>
-    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)
+  loom_solve <;> intros <;> first
+    | rfl
+    | (split <;> simp_all [committedLimits, defaultMemberPair, asymm, not_lt])
+    | simp_all [committedLimits, defaultMemberPair, asymm, not_lt]
+    | grind
```

Attack 8 — `atk_02_setter_oracle_echo__p3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,13 +283,7 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
-    let swapped := lo > hi
-    let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
-    let out := if swapped then (n.2, n.1) else (n.1, n.2)
-    return out
+    return committedLimits lo hi
     -- impl-end
 
 end
@@ -304,8 +298,4 @@
   loom_solve
 
 prove_correct commitLimits by
-  loom_solve <;>
-    intros <;>
-    split <;>
-    simp_all [asymm, not_lt] <;>
-    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)
+  loom_solve <;> intros <;> grind [committedLimits, defaultMemberPair]
```

Attack 9 — `atk_03_member_axiom_echo__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,13 +177,10 @@
     out.1 ≤ out.2
   do
     -- impl-start
-    -- Sort the two arguments, adjust, and report the adjusted pair AS IS: the
-    -- order the arguments arrived in is not reinstated here.
-    let reversed := e1 < e0
-    let a := if reversed then e1 else e0
-    let b := if reversed then e0 else e1
-    let e ← expandRange a b
-    return e
+    if e1 < e0 then
+      return expandAscending e1 e0
+    else
+      return expandAscending e0 e1
     -- impl-end
 
 /- The normalizer chain's VOCABULARY, introduced HERE — at the level of
```

Attack 10 — `atk_04_setter_chain_reversed_probe__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,11 +283,9 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
     let swapped := lo > hi
+    let _probe ← normalizeRange hi lo
     let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
     let out := if swapped then (n.2, n.1) else (n.1, n.2)
     return out
     -- impl-end
```

Attack 11 — `atk_05_setter_chain_nested_probe__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,11 +283,9 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
     let swapped := lo > hi
     let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
+    let _probe ← normalizeRange n.1 n.2
     let out := if swapped then (n.2, n.1) else (n.1, n.2)
     return out
     -- impl-end
```

Attack 12 — `atk_06_member_partial_sign_hi__p0.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,9 +177,7 @@
     out.1 ≤ out.2
   do
     -- impl-start
-    -- Sort the two arguments, adjust, and report the adjusted pair AS IS: the
-    -- order the arguments arrived in is not reinstated here.
-    let reversed := e1 < e0
+    let reversed := e1 < e0 ∧ originEndpoint < e1
     let a := if reversed then e1 else e0
     let b := if reversed then e0 else e1
     let e ← expandRange a b
```

Attack 13 — `atk_06_member_partial_sign_hi__p1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,9 +177,7 @@
     out.1 ≤ out.2
   do
     -- impl-start
-    -- Sort the two arguments, adjust, and report the adjusted pair AS IS: the
-    -- order the arguments arrived in is not reinstated here.
-    let reversed := e1 < e0
+    let reversed := e1 < e0 ∧ originEndpoint < e1
     let a := if reversed then e1 else e0
     let b := if reversed then e0 else e1
     let e ← expandRange a b
@@ -298,7 +296,8 @@
   loom_solve
 
 prove_correct defaultMemberAdjust by
-  loom_solve
+  loom_solve <;> intros <;>
+    simp_all [defaultMemberPair, asymm, not_lt]
 
 prove_correct normalizeRange by
   loom_solve
```

Attack 14 — `atk_06_member_partial_sign_hi__p2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,9 +177,7 @@
     out.1 ≤ out.2
   do
     -- impl-start
-    -- Sort the two arguments, adjust, and report the adjusted pair AS IS: the
-    -- order the arguments arrived in is not reinstated here.
-    let reversed := e1 < e0
+    let reversed := e1 < e0 ∧ originEndpoint < e1
     let a := if reversed then e1 else e0
     let b := if reversed then e0 else e1
     let e ← expandRange a b
@@ -298,7 +296,11 @@
   loom_solve
 
 prove_correct defaultMemberAdjust by
-  loom_solve
+  loom_solve <;> intros <;> first
+    | rfl
+    | (split <;> simp_all [defaultMemberPair, asymm, not_lt])
+    | simp_all [defaultMemberPair, asymm, not_lt]
+    | grind
 
 prove_correct normalizeRange by
   loom_solve
```

Attack 15 — `atk_06_member_partial_sign_hi__p3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,9 +177,7 @@
     out.1 ≤ out.2
   do
     -- impl-start
-    -- Sort the two arguments, adjust, and report the adjusted pair AS IS: the
-    -- order the arguments arrived in is not reinstated here.
-    let reversed := e1 < e0
+    let reversed := e1 < e0 ∧ originEndpoint < e1
     let a := if reversed then e1 else e0
     let b := if reversed then e0 else e1
     let e ← expandRange a b
@@ -298,7 +296,7 @@
   loom_solve
 
 prove_correct defaultMemberAdjust by
-  loom_solve
+  loom_solve <;> intros <;> grind [defaultMemberPair]
 
 prove_correct normalizeRange by
   loom_solve
```

Attack 16 — `atk_07_setter_boundary_degenerate__p0.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,11 +283,8 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
-    let swapped := lo > hi
+    let swapped := hi < lo ∨ (lo = hi ∧ originEndpoint < lo)
     let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
     let out := if swapped then (n.2, n.1) else (n.1, n.2)
     return out
     -- impl-end
```

Attack 17 — `atk_07_setter_boundary_degenerate__p1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,11 +283,8 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
-    let swapped := lo > hi
+    let swapped := hi < lo ∨ (lo = hi ∧ originEndpoint < lo)
     let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
     let out := if swapped then (n.2, n.1) else (n.1, n.2)
     return out
     -- impl-end
@@ -304,8 +301,5 @@
   loom_solve
 
 prove_correct commitLimits by
-  loom_solve <;>
-    intros <;>
-    split <;>
-    simp_all [asymm, not_lt] <;>
-    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)
+  loom_solve <;> intros <;>
+    simp_all [committedLimits, defaultMemberPair, asymm, not_lt, lt_iff_le_not_le]
```

Attack 18 — `atk_07_setter_boundary_degenerate__p2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,11 +283,8 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
-    let swapped := lo > hi
+    let swapped := hi < lo ∨ (lo = hi ∧ originEndpoint < lo)
     let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
     let out := if swapped then (n.2, n.1) else (n.1, n.2)
     return out
     -- impl-end
@@ -304,8 +301,8 @@
   loom_solve
 
 prove_correct commitLimits by
-  loom_solve <;>
-    intros <;>
-    split <;>
-    simp_all [asymm, not_lt] <;>
-    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)
+  loom_solve <;> intros <;> first
+    | rfl
+    | (split <;> simp_all [committedLimits, defaultMemberPair, asymm, not_lt])
+    | simp_all [committedLimits, defaultMemberPair, asymm, not_lt]
+    | grind
```

Attack 19 — `atk_07_setter_boundary_degenerate__p3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,11 +283,8 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
-    let swapped := lo > hi
+    let swapped := hi < lo ∨ (lo = hi ∧ originEndpoint < lo)
     let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
     let out := if swapped then (n.2, n.1) else (n.1, n.2)
     return out
     -- impl-end
@@ -304,8 +301,4 @@
   loom_solve
 
 prove_correct commitLimits by
-  loom_solve <;>
-    intros <;>
-    split <;>
-    simp_all [asymm, not_lt] <;>
-    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)
+  loom_solve <;> intros <;> grind [committedLimits, defaultMemberPair]
```

Attack 20 — `atk_08_stub_chain_double__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -237,6 +237,7 @@
   ensures r = normalize a b
   do
     -- impl-start
+    let _first :| _first = normalize a b
     let r :| r = normalize a b
     return r
     -- impl-end
```

Attack 21 — `atk_09_setter_guard_not_le__p2.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,11 +283,8 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
-    let swapped := lo > hi
+    let swapped := ¬ (lo ≤ hi)
     let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
     let out := if swapped then (n.2, n.1) else (n.1, n.2)
     return out
     -- impl-end
@@ -304,8 +301,8 @@
   loom_solve
 
 prove_correct commitLimits by
-  loom_solve <;>
-    intros <;>
-    split <;>
-    simp_all [asymm, not_lt] <;>
-    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)
+  loom_solve <;> intros <;> first
+    | rfl
+    | (split <;> simp_all [committedLimits, defaultMemberPair, asymm, not_lt])
+    | simp_all [committedLimits, defaultMemberPair, asymm, not_lt]
+    | grind
```

Attack 22 — `atk_10_member_rewiden_probe__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -177,12 +177,11 @@
     out.1 ≤ out.2
   do
     -- impl-start
-    -- Sort the two arguments, adjust, and report the adjusted pair AS IS: the
-    -- order the arguments arrived in is not reinstated here.
     let reversed := e1 < e0
     let a := if reversed then e1 else e0
     let b := if reversed then e0 else e1
     let e ← expandRange a b
+    let _again ← expandRange e.1 e.2
     return e
     -- impl-end
 
```

Attack 23 — `atk_11_setter_origin_chain_probe__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,11 +283,9 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
     let swapped := lo > hi
+    let _probe ← normalizeRange originEndpoint originEndpoint
     let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
     let out := if swapped then (n.2, n.1) else (n.1, n.2)
     return out
     -- impl-end
```

Attack 24 — `atk_12_setter_origin_member_probe__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,11 +283,9 @@
   ensures (normalize lo hi).1 < (normalize lo hi).2 → ((lo > hi) ↔ out.2 < out.1)
   do
     -- impl-start
-    -- Read the requested orientation BEFORE consulting the normalizer: its
-    -- answer no longer records which way round the request was.
     let swapped := lo > hi
+    let _probe ← defaultMemberAdjust originEndpoint originEndpoint
     let n ← normalizeRange lo hi
-    -- Commit the normalizer's endpoints in the requested orientation.
     let out := if swapped then (n.2, n.1) else (n.1, n.2)
     return out
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_00_positive_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** adversarial G-EQ (refinement fidelity, docs/architecture.md §5), focused on the A legs and model<->patch correspondence per instructions (R/I legs are G-CONF's).

**SAME-SPEC:** all 24 submitted attack files + positive control confirmed same_spec=True via swebench_unified.markers.same_spec with backend velvet. Command: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(<bundle>/Solution.lean).read(), open(<atk>).read(), b.language))".

**VERIFY:** bash scripts/lean_verify.sh <file>, run 4-concurrent via xargs -P 4.
  POSITIVE CONTROL atk_00_positive_control.lean (byte-copy of Solution.lean): EXIT=0 -- verifier live, non-vacuous.
  PREPATCH REPRODUCED (both halves): pre1.lean (bundle Solution_prepatch.lean; base_commit commit block, gold member) EXIT=1; pre2.lean (Solution_prepatch2.lean; gold commit block, base_commit member reinstating received order) EXIT=1. Each half independently refuted, so neither can be dropped.

METHOD NOTE (new surface vs the prior pass): markers.`_lean_spec_view` collapses impl regions AND elides prove_correct bodies, so a rival may ship its OWN proof script and stay same_spec. The prior G-EQ pass reused gold's script for all 20 attacks, so any 'rejected' verdict there could have been a TACTIC failure rather than spec teeth. I therefore ran each semantic rival under up to 4 scripts (gold's; simp_all with committedLimits/defaultMemberPair unfolded; a `first`-combinator cascade; grind). This also widened the mutable surface to the `:|` CALLEE STUB impls (atk_08), which are collapsed too.

ATTACKS REJECTED under ALL 4 proof scripts (spec has real teeth; residual goals are genuinely false, not tactic misses):
  atk_01_setter_sibling_echo -- setter commits the SIBLING oracle defaultMemberPair (= bare Locator.nonsingular) instead of the CHAIN normalize (= nonsingular THEN limit_range_for_scale). Refined this DROPS limit_range_for_scale and would break the log F2P leg. Killed by Q6: residual goal `(expandAscending hi lo).1 < (expandAscending hi lo).2` is unprovable -- the widener is not assumed to order its answer. This is the single most dangerous rival class (it substitutes one real callee for another) and the spec catches it.
  atk_02_setter_oracle_echo -- ungrounded ORACLE ECHO `return committedLimits lo hi`, no stub consulted. Killed by Q6.
  atk_06_member_partial_sign_hi -- PARTIAL DOMAIN: member sorts only where originEndpoint < e1 (fresh boundary; prior pass gated on e0). Killed by P2/P4.
  atk_07_setter_boundary_degenerate -- BOUNDARY: also swaps at lo = hi (positive lo). Killed by Q3/Q6/Q1 -- exactly Q6's <= direction at the degenerate point.

ATTACKS THAT VERIFIED -> all 8 faithful patches materialized in a clean base_commit worktree (git worktree add --detach d65c9ca20d), each checked with `git apply --check` (all rc=0), each EXECUTED via swebench_unified.harness.run_resolve(timeout=3600), 4-concurrent: GOLD CONTROL gold_control.diff -- rebuilt through the same patch machinery and confirmed to produce trees BYTE-IDENTICAL to the bundle patch.diff (md5 over all 3 touched files): resolved=True, 1/1 F2P, 400/400 P2P.

G-RESOLVE claim independently reproduced. atk_03_member_axiom_echo (member answers via the bare axiom, bypassing the expandRange stub): RESOLVED 1/1, 400/400. atk_04_setter_chain_reversed_probe (discarded chain call on the REVERSED pair): RESOLVED 1/1, 400/400 [attempt 2/3, harness flake]. atk_05_setter_chain_nested_probe (chain re-invoked on its OWN output, discarded): RESOLVED 1/1, 400/400 [attempt 2/3, flake]. atk_08_stub_chain_double (the CHAIN STUB resolves the chain twice, keeps the second): RESOLVED 1/1, 400/400. atk_09_setter_guard_not_le (guard spelled `not (lo <= hi)`; refines to `not (left <= right)`, which differs from `left > right` ONLY on NaN -- probes whether the R-leg finiteness claim is load-bearing): RESOLVED 1/1, 400/400.

Sound because `_validate_converted_limits` raises ValueError on non-finite requests upstream of the block, so the NaN-discriminating input is unreachable -- mapping.md §2's claim, confirmed in source. atk_10_member_rewiden_probe (member widens a second time over its own answer, discarded): RESOLVED 1/1, 400/400 [attempt 2/3, flake]. atk_11_setter_origin_chain_probe (STRONGEST candidate -- discarded chain probe at originEndpoint, refining to nonsingular(0,0); LogLocator.nonsingular hits `if vmax <= 0` and emits cbook.`_warn_external`('Data has no positive values, and therefore cannot be log-scaled.'), a warning gold NEVER emits, on the F2P test's own log leg): RESOLVED 1/1, 400/400.

Confirmed harmless: swebench test_cmd is plain `pytest -rA` (no -W error), pytest.ini sets no filterwarnings, and of the 400 P2P tests only test_eventplot_problem_kwargs and test_pathological_hexbin assert warning COUNTS, neither of which touches log-scale limit setting. atk_12_setter_origin_member_probe (discarded MEMBER probe at the origin -- the pure contrast that isolates warning-vs-extra-call): RESOLVED 1/1, 400/400.

A-LEG AUDIT (the G-EQ focus). Both consumed axioms are BARE function types (axiom normalize / axiom expandAscending) with no value and no ordering assumption, so A3/B4 are honest -- no part of the change is smuggled into an assumption; expandAscending is deliberately NOT assumed to order its answer, and P4 conditions on that observable instead. I independently re-derived the load-bearing A-leg facts by running the REAL post-patch transforms.nonsingular arithmetic over 576 pairs (probe_ax.py; boundary set incl. +/-0.0, +/-1e-300, +/-1e300, 1e-16, DBL_MIN, DBL_MAX, 1-1e-7, and the F2P test's own 4/-5, 5/-3, 10/1): B2 symmetry (what makes the model's caller-side sort lift faithful): 576/576 agree, 0 asymmetric.

MEMBER SHADOW composed identity Locator.nonsingular(v0,v1) == expandAscending(min,max): 576/576. B5 observability (what makes the ticker.py hunk an independently modeled op -- the atk_17_callee_unchanged hole refinement.md §B self-corrects): base_commit increasing=False differs from post-patch at 274/576. The hunk IS independently observable, so §B's correction is right and modeling only site A would satisfy Q1-Q6 without resolving. P4 antecedent: post-patch widener never reports descending (0/576) -- conditioning is conservative, not gratuitous.

A3 order-freedom: the chain family genuinely DISAGREES on output order between members at the same request (245/576 comparing Locator vs DateLocator.nonsingular, which does not sort), so treating the callee's order as an OBSERVABLE rather than a promise is faithful, and Q4/Q5/Q6's antecedents are not vacuous. Structural claims re-checked in source at base_commit: AutoLocator and MaxNLocator do NOT define nonsingular (so the edited Locator base method is the member reached on the F2P test's linear axis -- §B's load-bearing fact); the three mplot3d setters contain NO '<= 0' guard and no log-scale test, while set_xlim/set_ylim gate theirs on get_?scale()=='log', so the EMPTY precondition is faithful and a `0 < lo` precondition would have excluded the F2P test's own (4,-5)/(5,-3) linear legs.

Carrier: order-only opaque Endpoint is right -- no arithmetic is applied to an endpoint inside either modeled block (all widening lives in the axiomatized callees), and `_validate_converted_limits` rejects non-finite requests upstream, so the bijection (finite float viewed through < alone) is exact.

LAYERING FENCE verified MECHANICALLY, not taken on prose: spec_view preserves full declaration order (Endpoint, instEndpointLinearOrder, originEndpoint, expandAscending, defaultMemberPair, expandRange, defaultMemberAdjust, normalize, committedLimits, normalizeRange, commitLimits), and moving `axiom normalize` above the member makes same_spec FALSE -- so an implementation genuinely cannot restore the chain vocabulary to the member's level and stay same-spec. The round-1/round-2 holes recorded in refinement.md §0.1 are closed by a frozen constraint, not by an assertion.

**LEG TAGS:** all 10 legs extracted and tagged R / I / A-consumed (A1 R, A2 I, A3 A-consumed, A4 I, A5 R, B1 R, B2 I, B3 I, B4 A-consumed, B5 I). NO kind-3 / inexpressible step. Both genuinely-changed operations are modeled CONCRETELY (A2/A4 and B2/B3/B5 all I); the two axioms cover callees only. refinement.md §B's one previously-prose-only claim is now carried by an executable hard assertion (conformance_check.py::check_halves_independent, which I read and which matches my independent probe row-for-row).

**CONCLUSION:** SOUND. The residual freedom is exactly the invisibility of callee INVOCATIONS -- their count, arguments and nesting -- which no `ensures` over the returned pair can observe. The bundle handles this the only way a model can, by SCOPE, and the frozen declaration order genuinely enforces it. Within that fence every impl that still verifies is behaviourally equal to gold on the committed pair, and all 8 faithful patches were EXECUTED and resolved at gold parity. No verify-but-not-resolve witness exists across 12 attack families spanning callee-substitution, ungrounded-oracle-echo, partial-domain, boundary, control-flow-effect (5 distinct invocation shapes incl. two at the origin with a real spurious warning), stub-level mutation, and NaN-discriminating guard classes.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 24 admissible attacks re-run of 24 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 24 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_01_setter_sibling_echo__p0.lean`, `atk_01_setter_sibling_echo__p1.lean`, `atk_01_setter_sibling_echo__p2.lean`, `atk_01_setter_sibling_echo__p3.lean`, `atk_02_setter_oracle_echo__p0.lean`, `atk_02_setter_oracle_echo__p1.lean`, `atk_02_setter_oracle_echo__p2.lean`, `atk_02_setter_oracle_echo__p3.lean`, +8 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_03_member_axiom_echo__p0.lean`, `atk_04_setter_chain_reversed_probe__p0.lean`, `atk_05_setter_chain_nested_probe__p0.lean`, `atk_08_stub_chain_double__p0.lean`, `atk_09_setter_guard_not_le__p2.lean`, `atk_10_member_rewiden_probe__p0.lean`, `atk_11_setter_origin_chain_probe__p0.lean`, +1 more |

**Non-vacuity.** The positive control `atk_00_positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying same-spec wrong impl was found whose faithful refined patch fails to resolve. 12 distinct attack families were encoded (each in up to 4 proof-script variants, since prove_correct bodies are ELIDED from the spec view and therefore mutable while staying same_spec -- a surface the prior pass did not exercise). 4 families were REJECTED under EVERY proof script with genuinely-false residual goals; 8 families verified, and all 8 faithful refined patches were materialized, git-apply-checked at base_commit, and EXECUTED through the official harness: all 8 resolved at exact gold parity (1/1 F2P, 400/400 P2P), matching the gold control. The 8 verifying impls are all behaviourally equal to gold on the observable committed pair -- they differ only in the NUMBER/ARGUMENTS of invisible callee invocations, or in inlining a symmetric callee. Notably the strongest break candidate (atk_11, a discarded chain probe at originEndpoint, which refines to a literal nonsingular(0,0) whose LogLocator branch emits a spurious 'Data has no positive values' warning gold never emits, on the F2P test's own log-scale leg) still resolved: the harness runs plain `pytest -rA` with no -W error, and no P2P test asserts warning counts around limit setting.
```

**Attacks re-run (24):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 24 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_01_setter_sibling_echo__p0.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_01_setter_sibling_echo__p1.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_01_setter_sibling_echo__p2.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_01_setter_sibling_echo__p3.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_02_setter_oracle_echo__p0.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_02_setter_oracle_echo__p1.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_02_setter_oracle_echo__p2.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_02_setter_oracle_echo__p3.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_03_member_axiom_echo__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_04_setter_chain_reversed_probe__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_05_setter_chain_nested_probe__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_06_member_partial_sign_hi__p0.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_06_member_partial_sign_hi__p1.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_06_member_partial_sign_hi__p2.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_06_member_partial_sign_hi__p3.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_07_setter_boundary_degenerate__p0.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_07_setter_boundary_degenerate__p1.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_07_setter_boundary_degenerate__p2.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_07_setter_boundary_degenerate__p3.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_08_stub_chain_double__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 21 — `atk_09_setter_guard_not_le__p2.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 22 — `atk_10_member_rewiden_probe__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 23 — `atk_11_setter_origin_chain_probe__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 24 — `atk_12_setter_origin_member_probe__p0.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_00_positive_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** adversarial G-EQ (refinement fidelity, docs/architecture.md §5), focused on the A legs and model<->patch correspondence per instructions (R/I legs are G-CONF's).

**SAME-SPEC:** all 24 submitted attack files + positive control confirmed same_spec=True via swebench_unified.markers.same_spec with backend velvet. Command: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(<bundle>/Solution.lean).read(), open(<atk>).read(), b.language))".

**VERIFY:** bash scripts/lean_verify.sh <file>, run 4-concurrent via xargs -P 4.
  POSITIVE CONTROL atk_00_positive_control.lean (byte-copy of Solution.lean): EXIT=0 -- verifier live, non-vacuous.
  PREPATCH REPRODUCED (both halves): pre1.lean (bundle Solution_prepatch.lean; base_commit commit block, gold member) EXIT=1; pre2.lean (Solution_prepatch2.lean; gold commit block, base_commit member reinstating received order) EXIT=1. Each half independently refuted, so neither can be dropped.

METHOD NOTE (new surface vs the prior pass): markers.`_lean_spec_view` collapses impl regions AND elides prove_correct bodies, so a rival may ship its OWN proof script and stay same_spec. The prior G-EQ pass reused gold's script for all 20 attacks, so any 'rejected' verdict there could have been a TACTIC failure rather than spec teeth. I therefore ran each semantic rival under up to 4 scripts (gold's; simp_all with committedLimits/defaultMemberPair unfolded; a `first`-combinator cascade; grind). This also widened the mutable surface to the `:|` CALLEE STUB impls (atk_08), which are collapsed too.

ATTACKS REJECTED under ALL 4 proof scripts (spec has real teeth; residual goals are genuinely false, not tactic misses):
  atk_01_setter_sibling_echo -- setter commits the SIBLING oracle defaultMemberPair (= bare Locator.nonsingular) instead of the CHAIN normalize (= nonsingular THEN limit_range_for_scale). Refined this DROPS limit_range_for_scale and would break the log F2P leg. Killed by Q6: residual goal `(expandAscending hi lo).1 < (expandAscending hi lo).2` is unprovable -- the widener is not assumed to order its answer. This is the single most dangerous rival class (it substitutes one real callee for another) and the spec catches it.
  atk_02_setter_oracle_echo -- ungrounded ORACLE ECHO `return committedLimits lo hi`, no stub consulted. Killed by Q6.
  atk_06_member_partial_sign_hi -- PARTIAL DOMAIN: member sorts only where originEndpoint < e1 (fresh boundary; prior pass gated on e0). Killed by P2/P4.
  atk_07_setter_boundary_degenerate -- BOUNDARY: also swaps at lo = hi (positive lo). Killed by Q3/Q6/Q1 -- exactly Q6's <= direction at the degenerate point.

ATTACKS THAT VERIFIED -> all 8 faithful patches materialized in a clean base_commit worktree (git worktree add --detach d65c9ca20d), each checked with `git apply --check` (all rc=0), each EXECUTED via swebench_unified.harness.run_resolve(timeout=3600), 4-concurrent: GOLD CONTROL gold_control.diff -- rebuilt through the same patch machinery and confirmed to produce trees BYTE-IDENTICAL to the bundle patch.diff (md5 over all 3 touched files): resolved=True, 1/1 F2P, 400/400 P2P.

G-RESOLVE claim independently reproduced. atk_03_member_axiom_echo (member answers via the bare axiom, bypassing the expandRange stub): RESOLVED 1/1, 400/400. atk_04_setter_chain_reversed_probe (discarded chain call on the REVERSED pair): RESOLVED 1/1, 400/400 [attempt 2/3, harness flake]. atk_05_setter_chain_nested_probe (chain re-invoked on its OWN output, discarded): RESOLVED 1/1, 400/400 [attempt 2/3, flake]. atk_08_stub_chain_double (the CHAIN STUB resolves the chain twice, keeps the second): RESOLVED 1/1, 400/400. atk_09_setter_guard_not_le (guard spelled `not (lo <= hi)`; refines to `not (left <= right)`, which differs from `left > right` ONLY on NaN -- probes whether the R-leg finiteness claim is load-bearing): RESOLVED 1/1, 400/400.

Sound because `_validate_converted_limits` raises ValueError on non-finite requests upstream of the block, so the NaN-discriminating input is unreachable -- mapping.md §2's claim, confirmed in source. atk_10_member_rewiden_probe (member widens a second time over its own answer, discarded): RESOLVED 1/1, 400/400 [attempt 2/3, flake]. atk_11_setter_origin_chain_probe (STRONGEST candidate -- discarded chain probe at originEndpoint, refining to nonsingular(0,0); LogLocator.nonsingular hits `if vmax <= 0` and emits cbook.`_warn_external`('Data has no positive values, and therefore cannot be log-scaled.'), a warning gold NEVER emits, on the F2P test's own log leg): RESOLVED 1/1, 400/400.

Confirmed harmless: swebench test_cmd is plain `pytest -rA` (no -W error), pytest.ini sets no filterwarnings, and of the 400 P2P tests only test_eventplot_problem_kwargs and test_pathological_hexbin assert warning COUNTS, neither of which touches log-scale limit setting. atk_12_setter_origin_member_probe (discarded MEMBER probe at the origin -- the pure contrast that isolates warning-vs-extra-call): RESOLVED 1/1, 400/400.

A-LEG AUDIT (the G-EQ focus). Both consumed axioms are BARE function types (axiom normalize / axiom expandAscending) with no value and no ordering assumption, so A3/B4 are honest -- no part of the change is smuggled into an assumption; expandAscending is deliberately NOT assumed to order its answer, and P4 conditions on that observable instead. I independently re-derived the load-bearing A-leg facts by running the REAL post-patch transforms.nonsingular arithmetic over 576 pairs (probe_ax.py; boundary set incl. +/-0.0, +/-1e-300, +/-1e300, 1e-16, DBL_MIN, DBL_MAX, 1-1e-7, and the F2P test's own 4/-5, 5/-3, 10/1): B2 symmetry (what makes the model's caller-side sort lift faithful): 576/576 agree, 0 asymmetric.

MEMBER SHADOW composed identity Locator.nonsingular(v0,v1) == expandAscending(min,max): 576/576. B5 observability (what makes the ticker.py hunk an independently modeled op -- the atk_17_callee_unchanged hole refinement.md §B self-corrects): base_commit increasing=False differs from post-patch at 274/576. The hunk IS independently observable, so §B's correction is right and modeling only site A would satisfy Q1-Q6 without resolving. P4 antecedent: post-patch widener never reports descending (0/576) -- conditioning is conservative, not gratuitous.

A3 order-freedom: the chain family genuinely DISAGREES on output order between members at the same request (245/576 comparing Locator vs DateLocator.nonsingular, which does not sort), so treating the callee's order as an OBSERVABLE rather than a promise is faithful, and Q4/Q5/Q6's antecedents are not vacuous. Structural claims re-checked in source at base_commit: AutoLocator and MaxNLocator do NOT define nonsingular (so the edited Locator base method is the member reached on the F2P test's linear axis -- §B's load-bearing fact); the three mplot3d setters contain NO '<= 0' guard and no log-scale test, while set_xlim/set_ylim gate theirs on get_?scale()=='log', so the EMPTY precondition is faithful and a `0 < lo` precondition would have excluded the F2P test's own (4,-5)/(5,-3) linear legs.

Carrier: order-only opaque Endpoint is right -- no arithmetic is applied to an endpoint inside either modeled block (all widening lives in the axiomatized callees), and `_validate_converted_limits` rejects non-finite requests upstream, so the bijection (finite float viewed through < alone) is exact.

LAYERING FENCE verified MECHANICALLY, not taken on prose: spec_view preserves full declaration order (Endpoint, instEndpointLinearOrder, originEndpoint, expandAscending, defaultMemberPair, expandRange, defaultMemberAdjust, normalize, committedLimits, normalizeRange, commitLimits), and moving `axiom normalize` above the member makes same_spec FALSE -- so an implementation genuinely cannot restore the chain vocabulary to the member's level and stay same-spec. The round-1/round-2 holes recorded in refinement.md §0.1 are closed by a frozen constraint, not by an assertion.

**LEG TAGS:** all 10 legs extracted and tagged R / I / A-consumed (A1 R, A2 I, A3 A-consumed, A4 I, A5 R, B1 R, B2 I, B3 I, B4 A-consumed, B5 I). NO kind-3 / inexpressible step. Both genuinely-changed operations are modeled CONCRETELY (A2/A4 and B2/B3/B5 all I); the two axioms cover callees only. refinement.md §B's one previously-prose-only claim is now carried by an executable hard assertion (conformance_check.py::check_halves_independent, which I read and which matches my independent probe row-for-row).

**CONCLUSION:** SOUND. The residual freedom is exactly the invisibility of callee INVOCATIONS -- their count, arguments and nesting -- which no `ensures` over the returned pair can observe. The bundle handles this the only way a model can, by SCOPE, and the frozen declaration order genuinely enforces it. Within that fence every impl that still verifies is behaviourally equal to gold on the committed pair, and all 8 faithful patches were EXECUTED and resolved at gold parity. No verify-but-not-resolve witness exists across 12 attack families spanning callee-substitution, ungrounded-oracle-echo, partial-domain, boundary, control-flow-effect (5 distinct invocation shapes incl. two at the origin with a real spurious warning), stub-level mutation, and NaN-discriminating guard classes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on matplotlib__matplotlib-14623/velvet. No divergence found between the modelled functions and the real patched repo; I could not construct an input on which the spec disagrees with matplotlib.

**SETUP.** Base-commit worktrees from the upstream repository at d65c9ca20dd (one clean, one with patch.diff applied); executable oracle = the SWE-bench testbed container (matplotlib 3.1.0.post258, /testbed) with patch.diff applied, so the reference is the PATCHED tree per the brief. Verified the two modelled operations correspond to the two coordinated halves of the gold patch: the caller-side capture/restore at the five limit-setter sites (`_base`.py:3267-3270, :3647-3650; axes3d.py:626-628, :684-686, :742-744) -> commitLimits, and Locator.nonsingular (ticker.py:1523-1525, increasing=False -> default) -> defaultMemberAdjust. Confirmed AutoLocator -> MaxNLocator -> Locator overrides nonsingular nowhere, so the base member really is on the linear F2P path.

### WHAT I MEASURED (all against the REAL patched code, exact float bit-comparison via struct.pack, not ==).

1. P1/P2/P3/P4 vs the real patched Locator.nonsingular. 41,187 + 61,208 observations (boundary grid incl. +/-0.0, subnormals 5e-324, 1e+/-300, DBL_MAX, tiny-interval near-equal pairs, random bit-patterns, degenerate e0=e1, both orders, both signs). 0 disagreements, 0 clause violations. Also 0 on non-finite arguments (inf/-inf/nan, 81 pairs).

2. Q1-Q6 end-to-end vs the five real patched setters. 146,664 observations across 12 (scale x major locator) members incl. the DateLocator member that does NOT sort, with upstream_request emulated for the 2D log guard. 0 disagreements on the committed pair; 0 Q4/Q5/Q6 violations evaluated on matplotlib's OWN returned pair. Return value == viewLim interval at every probe (0 mismatches), so modelling the return is the same as modelling the commit.

3. The factorization's load-bearing hypothesis. P1/P2/P3 sort in the CALLER and apply expandAscending to the sorted pair, whereas the real method sorts INSIDE mtransforms.nonsingular. That is faithful only if the widener is symmetric. I attacked it with 300,900 probes deliberately aimed at the branches that could break it (both-near-overflow so expansion overflows to inf, maxabsvalue-below-threshold subnormal branch, vmax-vmin<=`maxabs*tiny` near-equal branch, raw 64-bit random doubles, inf/nan): 0 asymmetries. Confirmed textually too: post-patch `increasing` is never False, so the un-sort at transforms.py:2840-2841 is unreachable from this member.

4. The sharpest abstraction seam I found, and it holds. Endpoint is an opaque LinearOrder. Antisymmetry FORCES 0.0 and -0.0 to be the SAME Endpoint (float `<` orders neither below the other), yet the real callees do distinguish them: I measured 14 argument-distinguishing pairs on the real member and outputs that genuinely contain -0.0 (e.g. E(1.0,-0.0)=(-0.0,1.0)). So I checked whether the order-quotient is WELL-DEFINED: over 625 zero-variant probes on the widener, the member, the full chain, and the real setters, inputs differing only in zero-sign produced outputs differing only in zero-sign AND with the identical internal order signature (<, >, =), and `lo > hi` never differed across zero variants. 0 violations. The quotient is respected, so the LinearOrder carrier is sound here rather than merely convenient. This was my best candidate for a divergence and it did not break.

5. Chain functionality/determinism, which Q4-Q6 need because they reference `normalize lo hi` several times while the do-block calls the callee once. Repeat-stable, no axis mutation (get_ylim/get_minpos unchanged), stable under interleaved unrelated chain calls, identical on a freshly built identical axis, and correct under state-chaining where a previous call moved viewLim. 0 violations across 8 configs incl. axes carrying data.

6. Totality / the deliberately absent precondition. The mapping's claim checks out: non-positive endpoints really do reach the block. On a 3D axis there is no guard at all -- 38,400 observations over 96 (axis x scale x locator) configs incl. log/symlog/logit 3D, 0 disagreements and 0 Q violations. A `require 0 < lo` precondition would have been the unfaithful choice; its absence is correct. Non-finite ENTRY pairs are reachable (set_ylim(DBL_MAX,DBL_MAX) commits (1.7078e308, inf), which then re-enters via None-defaulting past `_validate_converted_limits`): 864 non-finite-entry observations, 0 Q violations, and the order-only carrier needs no special case for them. NaN was never reachable in viewLim (4000-trial adversarial search) and `_validate_converted_limits` rejects it upstream, so its exclusion is justified rather than assumed.

7. Direction-of-reference check (the trap in the brief). Every divergence I probed for was measured against the PATCHED tree. I did not report the patch delta as a defect: at base_commit the member passes increasing=False and there is no swapped capture, which is exactly the behaviour Solution_prepatch.lean / Solution_prepatch2.lean are supposed to fail. expandAscending's referent (mtransforms.nonsingular, transforms.py:2791-2842) is untouched by the patch, so validating it against base is equivalent -- I checked the file is byte-identical between the two worktrees.

**HYGIENE.** scripts/lean_verify.sh on the shipped Solution.lean: exit 0 (one cosmetic <;> linter warning only). markers.region_hashes recomputed from the file on disk reproduces the G-HYGIENE record EXACTLY (axioms/pure/impl/spec_view all four). markers.same_spec(Solution, Solution_prepatch) and same_spec(Solution, Solution_prepatch2) both True, so the frozen spec region is byte-identical across the gold and both prepatch twins and the G-DIFF twins are same-spec as required. NOTE (bookkeeping, not a faithfulness defect and not my gate): the TOP-LEVEL meta.json['region_hashes'] block holds four stale digests that do not reproduce from the current file, while the G-HYGIENE gate record's copy does; that is a stale-mirror artifact of a prose revision, and since scripts/check_stamp_freshness.py reads the gate record's copy the freshness check is unaffected. Worth a bookkeeping pass, but no clause changed.

**CONCLUSION.** The spec is if-anything conservatively weak, not too strong: the one place it could have over-claimed -- asserting the normalizer returns its pair ascending -- is exactly what was removed, and I independently reproduced the refutation that forced it (ORDER CENSUS: at the same descending request (10,1), linear/AutoLocator reports ascending while linear/AutoDateLocator reports descending; census shows asc-only for 8 members and both for the 4 date/log members). Q4/Q5/Q6 correctly take that order as a per-call HYPOTHESIS. No diverging input exists that I could find over ~590k real-code observations. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**MY OWN MEASUREMENT ON CURRENT BYTES.** Solution.lean sha256 40f9354625d13f6fecea11b01eaf0546ae23eda69ef444d0800c30b0d618afdb; spec_view sha256 6a4be7dfcde59cc2cf3beb6de2a026a622d94b24c802ed2951e6f2e3b8176155; instance.json 4bdf88b74cc41a1d494d1dd5eeb6ba15c6d92aab47ca37994b5f21cc3dd32245.

(0) NO RELAXATION IS CLAIMED OR NEEDED -- checked, not assumed. `[k for k in meta if 'relax' in k.lower()] == []`; `find matplotlib__matplotlib-14623 -iname '*RELAX*'` is EMPTY; gates.G-LEAK.status == 'pass' (mode strict, detail 'spec view clean'), not 'relaxed'. So I judged this as a plain STRICT leakage review and did NOT inherit or re-derive anybody's unavoidability argument -- there is none in this bundle to re-derive. I also confirmed the strict path is the one the harness itself took: gates/leak.py only honors a relaxation on `status=='relaxed'` or (`relaxed_leakage is True` AND RELAXED_LEAKAGE.md exists), and neither holds.

(0b) NO FILE IN THIS BUNDLE ADDRESSES ME. Ran leakage.reviewer_directed() over mapping.md, refinement.md and verdict.md -> [] for all three (all four rules: addresses-the-reviewer, prescribes-the-verdict x2, recording-convention). Hand-grepped Solution.lean/mapping.md/refinement.md/properties.py/conformance_check.py/axiom_check.py for panel|auditor|reviewer|leakage|'record this as'|'verdict should'|NO-LEAKAGE: the single hit is mapping.md:109 '(G-PANEL-2). A numeric carrier would have had to exclude the case or defend', a provenance citation, not an instruction. Nothing steers this verdict.

(1) SPEC REGION BYTE-IDENTICAL ACROSS ALL THREE TWINS. markers.spec_view/same_spec with the real velvet LanguageTables (VelvetBackend().language -- markers.`_tables` rejects a bare 'lean' string): Solution.lean, Solution_prepatch.lean, Solution_prepatch2.lean all yield spec_view sha 6a4be7df... and same_spec()==True pairwise, while the FILE shas differ (40f93546 / 8ca3570e / 821e83ff). All divergence is inside the elided `impl` do-blocks. spec_view is idempotent (spec_view(spec_view(s))==spec_view(s)). region_hashes I recomputed now equal gates.G-HYGIENE.data.region_hashes exactly (axioms 6a5a7ef4, pure a4109f60, impl a2febd33, spec_view 6a4be7df) -- byte-current, not a stale echo.

(2) THE DISCRIMINATOR IS IN THE ELIDED IMPL, MEASURED. scripts/lean_verify.sh (real exit codes, captured -- not via a pipe): Solution.lean exit 0, 0 errors (one unnecessarySeqFocus linter warning at 310:29). Solution_prepatch.lean exit 1, 4 errors -- open goal `(x.1,x.2) = committedLimits lo hi` with `ensures_1 : x = normalize lo hi` (caller half: orientation never reinstated). Solution_prepatch2.lean exit 1, 1 error -- open goal `(if e1 < e0 then (x.2,x.1) else (x.1,x.2)) = defaultMemberPair e0 e1` (callee half: the member wrongly reinstating the order it received). One shared spec view refutes BOTH gold halves independently, so the view carries the required behavior while the gold edit text stays inside the elided region.

(3) MECHANICAL SCREEN, RE-RUN BY ME. leakage.screen(src, velvet.language, instance['patch'], instance['problem_statement'], test_patch) -> passed=True, hard_failures=[], warnings=[]. Per-line check of every changed gold line: the 4 distinctive ones ('swapped = left > right', 'left, right = right, left', '"""Expand a range as needed to avoid singularities."""', 'return mtransforms.nonsingular(v0, v1, expander=.05)') are all >=8 normalized chars and NONE appears in the normalized view. No diff marker. No patched path: lib/matplotlib/axes/`_base`.py, lib/matplotlib/ticker.py, lib/mpl_toolkits/mplot3d/axes3d.py absent, and so are their dotted module spellings. Narration regex clean (bug|fix|patch|patched|regression|previously|incorrectly|wrong|broken|off-by-one: zero hits).

(4) I DID NOT STOP AT THE MECHANICAL GATE. `_patch_changed_symbols` only harvests def/class names off CHANGED lines plus hunk headers, so it yielded only ['raise_if_exceeds','set_xlim','set_xlim3d','set_ylim','set_ylim3d','set_zlim3d'] and structurally never screened `nonsingular` or `Locator` (the ticker.py hunk rewrites the docstring + return, not the `def nonsingular` line). Two independent sweeps of my own: (a) case-insensitive grep of the view for nonsingular, singular, increasing, expander, .05, mtransforms, viewLim, intervalx, intervaly, ticker, matplotlib, mpl_toolkits, axes3d, get_major_locator, LogLocator, LogitLocator, DateLocator, limit_range_for_scale, set_xlim, set_ylim, set_zlim3d, swapped, cbook, `_warn_external` -> ZERO hits for every one.

(b) the complement direction: extracted EVERY [A-Za-z_]\w{2,} token from instance['patch'] and substring-matched it against the lowercased view. Only 17 matched, and after removing the ones already in the public problem_statement the residue is {Expand, False, None, def, diff, endpoints, left, range, results, return, self, top} -- every one an English word or Lean keyword occurring in unrelated positions ('Expand'/'expandAscending' is model vocabulary; 'diff' only in 'different/difference'; 'left'/'top' inside 'left entirely open'/'topological-free prose'). No repo symbol survives. Also: no numeric literal anywhere in the view -- none of the F2P legs (4,-5)/(5,-3)/(10,1), no 1000e2, no test name test_inverted_limits, no test_patch content.

(5) THE JUDGMENT CALL I ACTUALLY WEIGHED. The view's densest prose (lines 70-79, 111-138, 151-177) explains the DIVISION OF LABOUR between the two halves -- the member must NOT reinstate the order it received, because the caller reinstates it and a second exchange would commit a reversed interval. That is the sharpest available leakage candidate, since the callee half is nowhere in the public problem_statement (which speaks only of ax.set_ylim(y.max(), y.min()) failing to invert a log axis). I rejected it on two grounds.

(i) It adds NOTHING over the ensures clauses: P1-P3 (`out = defaultMemberPair e0 e1`, `e1 < e0 -> out = expandAscending e1 e0`) already pin that behavior exactly, and the clause block IS the spec -- a benchmark whose G-DIFF requires the spec to refute the pre-patch impl cannot then call the refuting clause a leak. The prose is motivation for a contract the reader already has. (ii) It is stated abstractly and counterfactually about a HYPOTHETICAL rival member, never historically about this repo: no 'used to', no 'previously', no repo symbol, no file, no version. A consumer holding only this view learns what two abstract operations must do; nothing tells them the site is matplotlib's Locator.nonsingular or that `increasing=False` is the token to delete. The gold discriminator `increasing=False` / `expander=.05` appears nowhere.

(6) LEDGER NOTE, NOT LEAKAGE. Top-level meta.json['region_hashes'] still carries a pre-repair set (axioms 22e4441e, impl 7e6efc35, pure f302854c, spec_view ca40e699) matching none of the current bytes; the per-gate G-HYGIENE record is the fresh one, and every gate's `sources` digest for Solution.lean equals the current 40f93546. meta.json is not part of spec_view and is not consumer-visible, so this is artifact drift worth a restamp, not a leak and not a broken disposition my verdict leans on. (Prior G-PANEL-2 and G-PANEL-3 both flagged the same drift; I reproduced it rather than took it.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.