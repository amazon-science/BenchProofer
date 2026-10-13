# P2 adversarial audit — sympy__sympy-14976

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 25 admissible attacks re-run of 25 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 25 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 22 | `atk_1_prepatch.lean`, `atk_2_config_blind_qualified.lean`, `atk_3_config_blind_bare.lean`, `atk_4_config_inverted.lean`, `atk_5_import_dropped.lean`, `atk_6_import_only_when_qualified.lean`, `atk_7_boundary_q1.lean`, `atk_8_numerator_only.lean`, `atk_10_double_resolve.lean`, `atk_11_import_duplicated.lean`, +12 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_9_oracle_echo.lean`, `atk_22_branch_split.lean`, `atk_23_render_regrouped.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying wrong impl exists: of 25 same-spec attacks, 22 were REJECTED by lean_verify.sh (exit 1) and the 3 that VERIFIED (atk_9_oracle_echo, atk_22_branch_split, atk_23_render_regrouped) are each behaviourally equal to the gold patch on every observable, and each one's materialized faithful patch RESOLVED under the official harness (F2P test_MpmathPrinter + all 13 P2P green). The two prior-pass counterexamples that this spec revision was repaired against were re-encoded and are both rejected: weak-config-blind-qualified => atk_2_config_blind_qualified (unsolved goal '"mpmath.mpf" ++ ... = render qualified p q', i.e. the spec now pins the spelling PER BRANCH) and weak-import-dropped => atk_5_import_dropped (unsolved goal '[] = mpfImport', i.e. the effect clause is live). The prepatch bug also reproduces as a refutation.
```

**Attacks re-run (25):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,10 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
-    let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    -- Pre-patch path: inherited StrPrinter._print_Rational, bare integer ratio
+    -- and no recorded import.
+    let text : String := if q = 1 then toString p else toString p ++ "/" ++ toString q
+    return (text, ([] : List (String × String)))
     -- impl-end
 
 prove_correct mpfRational by
```

Attack 2 — `atk_2_config_blind_qualified.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,10 +76,9 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
-    let m : String := mpfName qualified
+    -- Pins the resolver to the module-qualified spelling regardless of the
+    -- ambient configuration (the previous revision's own model).
+    let m : String := "mpmath.mpf"
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
```

Attack 3 — `atk_3_config_blind_bare.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,10 +76,9 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
-    let m : String := mpfName qualified
+    -- Pins the resolver to the bare constructor name regardless of the
+    -- ambient configuration.
+    let m : String := "mpf"
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
```

Attack 4 — `atk_4_config_inverted.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,10 +76,8 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
-    let m : String := mpfName qualified
+    -- Reads the configuration but the wrong way round.
+    let m : String := if qualified then "mpf" else "mpmath.mpf"
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
```

Attack 5 — `atk_5_import_dropped.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,11 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- Correct rendering, but resolving records nothing: generated code is left
+    -- with an unbound constructor name.
     let m : String := mpfName qualified
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    return (text, ([] : List (String × String)))
     -- impl-end
 
 prove_correct mpfRational by
```

Attack 6 — `atk_6_import_only_when_qualified.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,12 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- PARTIAL-DOMAIN on the effect: records the import only when the
+    -- module-qualified spelling is used, i.e. exactly where it is NOT needed.
     let m : String := mpfName qualified
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    let imports : List (String × String) := if qualified then mpfImport else []
+    return (text, imports)
     -- impl-end
 
 prove_correct mpfRational by
```

Attack 7 — `atk_7_boundary_q1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,11 +76,11 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- BOUNDARY: correct except at a unit denominator, where it drops the
+    -- quotient and emits only the wrapped numerator (the StrPrinter habit).
     let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
+    let text : String := if q = 1 then m ++ "(" ++ toString p ++ ")"
+      else m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
 
```

Attack 8 — `atk_8_numerator_only.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,11 +76,10 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- HALF FIX: wraps only the numerator, leaving the denominator a bare
+    -- integer, so the quotient is still evaluated at reduced precision.
     let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
+    let text : String := m ++ "(" ++ toString p ++ ")/" ++ toString q
     return (text, mpfImport)
     -- impl-end
 
```

Attack 9 — `atk_9_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,9 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
-    let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    -- UNGROUNDED-ORACLE ECHO: returns the post-condition's own oracle terms
+    -- verbatim, doing no independent work at all.
+    return (render qualified p q, mpfImport)
     -- impl-end
 
 prove_correct mpfRational by
```

Attack 10 — `atk_10_double_resolve.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,12 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
-    let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    -- CONTROL-FLOW-EFFECT: resolves the constructor name once per position
+    -- (two calls, not one) and assembles the quotient from the two factors, so
+    -- the string is regrouped and the recording happens twice.
+    let num : String := mpfName qualified ++ "(" ++ toString p ++ ")"
+    let den : String := mpfName qualified ++ "(" ++ toString q ++ ")"
+    return (num ++ "/" ++ den, mpfImport)
     -- impl-end
 
 prove_correct mpfRational by
```

Attack 11 — `atk_11_import_duplicated.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,11 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- Records the same pair twice: under the set abstraction of mapping.md
+    -- section 2 this is the SAME delta (set.add is idempotent).
     let m : String := mpfName qualified
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    return (text, mpfImport ++ mpfImport)
     -- impl-end
 
 prove_correct mpfRational by
```

Attack 12 — `atk_12_import_transposed.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,10 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- Records the pair the other way round: name as module, module as name.
     let m : String := mpfName qualified
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    return (text, [("mpf", "mpmath")])
     -- impl-end
 
 prove_correct mpfRational by
```

Attack 13 — `atk_13_zero_numerator.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,11 +76,11 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- PARTIAL-DOMAIN on the value: short-circuits a zero numerator to a bare
+    -- wrapped zero, dropping the denominator entirely.
     let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
+    let text : String := if p = 0 then m ++ "(0)"
+      else m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
 
```

Attack 14 — `atk_15_divergence.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,11 +76,16 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- DIVERGENCE probe: semantics.termination is "total", so a loop with no
+    -- decreasing measure that never exits must be REJECTED even though the
+    -- returned value would satisfy both clauses.
     let m : String := mpfName qualified
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
+    let mut k : Nat := 1
+    while k > 0
+    invariant k > 0
+    do
+      k := k + 1
     return (text, mpfImport)
     -- impl-end
 
```

Attack 15 — `atk_16_guarded_wrong_branch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,11 +76,11 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- The wrong rendering is guarded by a condition that IS reachable
+    -- (q = 2 is the F2P input's denominator), so it must be rejected.
     let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
+    let text : String := if q = 2 then m ++ "(" ++ toString p ++ ")" ++ "/" ++ toString q
+      else m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
 
```

Attack 16 — `atk_17_negative_numerator.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,11 +76,12 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- BOUNDARY on sign: a negative numerator is rendered by negating outside
+    -- the constructor call instead of inside it.
     let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
+    let text : String := if p < 0
+      then "-" ++ m ++ "(" ++ toString (-p) ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
+      else m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
 
```

Attack 17 — `atk_18_inlined_resolver.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,11 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
-    let m : String := mpfName qualified
+    -- Does not call the resolver: inlines its two branches and records the
+    -- import by hand. Same value, same delta -- an A4/A5 correspondence probe.
+    let m : String := if qualified = true then "mpmath.mpf" else "mpf"
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    return (text, [("mpmath", "mpf")])
     -- impl-end
 
 prove_correct mpfRational by
```

Attack 18 — `atk_19_extra_import.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,11 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- Records a SUPERSET: the needed pair plus an unrelated one, so generated
+    -- code carries an import the operation never justified.
     let m : String := mpfName qualified
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    return (text, mpfImport ++ [("mpmath", "mpc")])
     -- impl-end
 
 prove_correct mpfRational by
```

Attack 19 — `atk_20_wrong_separator.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,11 +76,10 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- CONTROL-FLOW/text defect: emits the two wrapped factors joined by "*"
+    -- instead of "/", i.e. a product rather than a quotient.
     let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
+    let text : String := m ++ "(" ++ toString p ++ ")*" ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
 
```

Attack 20 — `atk_21_swapped.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,11 +76,9 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- Renders the reciprocal: denominator over numerator.
     let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
+    let text : String := m ++ "(" ++ toString q ++ ")/" ++ m ++ "(" ++ toString p ++ ")"
     return (text, mpfImport)
     -- impl-end
 
```

Attack 21 — `atk_22_branch_split.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,10 +76,8 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
-    let m : String := mpfName qualified
+    -- Branches on the configuration explicitly and resolves per branch.
+    let m : String := if qualified then mpfName true else mpfName false
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
```

Attack 22 — `atk_23_render_regrouped.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,11 +76,10 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- Same characters, assembled by naming render's factors separately.
     let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
+    let lhs : String := m ++ "(" ++ toString p ++ ")/"
+    let text : String := lhs ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
 
```

Attack 23 — `atk_24_double_negation.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,10 +76,8 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
-    let m : String := mpfName qualified
+    -- Reads the setting through a double negation that collapses to a constant.
+    let m : String := mpfName (qualified && !qualified)
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
     return (text, mpfImport)
     -- impl-end
```

Attack 24 — `atk_25_import_module_from_branch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,12 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
+    -- Derives the recorded module from the spelling actually emitted, so in the
+    -- bare configuration it records the wrong (empty-prefix) module.
     let m : String := mpfName qualified
     let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    let imports : List (String × String) := if qualified then [("mpmath","mpf")] else [("", "mpf")]
+    return (text, imports)
     -- impl-end
 
 prove_correct mpfRational by
```

Attack 25 — `atk_26_vacuity_constant.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -76,12 +76,9 @@
   ensures out.2 = mpfImport
   do
     -- impl-start
-    -- Resolve the constructor's name once under the ambient configuration, wrap
-    -- both parts of the quotient in it, and report the import that resolving
-    -- recorded.
-    let m : String := mpfName qualified
-    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
-    return (text, mpfImport)
+    -- VACUITY CONTROL: ignores every input and returns a constant that cannot
+    -- satisfy either clause. If this VERIFIES the obligations are vacuous.
+    return ("VACUOUS", ([] : List (String × String)))
     -- impl-end
 
 prove_correct mpfRational by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** base_commit worktree (git worktree add --detach 9cbea134220b0b951587e11b63e2c832c7246cbc). Bundle left byte-unmodified (git status --porcelain on benchmark-verified/sympy__sympy-14976/ empty); worktree left clean. Every attack copied Solution.lean editing ONLY the impl region; same_spec(Solution.lean, atk_N.lean, velvet) == True for ALL 25 attacks + the positive control (verified via swebench_unified.markers.same_spec, printed PASS for each).

**POSITIVE CONTROL.** pos_control.lean (impl byte-identical to the bundle): `bash scripts/lean_verify.sh pos_control.lean` => EXIT 0 in 3.4s. Toolchain is live and the spec is satisfiable.

**SCHEDULE.** Attack verifications were run as concurrent background jobs, 4 at a time (xargs -P 4 over scripts/lean_verify.sh); the 3 resolve runs were launched concurrently as detached background jobs. Pass criteria unchanged: all 25 verifies and all 3 resolves ran to completion.

### VERIFY TALLY (exit 0 = verifies, 1 = rejected; command per file: `bash scripts/lean_verify.sh <name>.lean`):
REJECTED (22) — 20 with clean `error: unsolved goals` naming the failing ensures clause, 1 on totality, 1 on syntax: atk_1_prepatch=1 (BOTH clauses fail: '[] = mpfImport' AND '(if q = 1 then toString p else toString p ++ "/" ++ toString q) = render qualified p q') — PREPATCH REPRODUCED atk_2_config_blind_qualified=1, atk_3_config_blind_bare=1, atk_4_config_inverted=1, atk_24_double_negation=1 (value leg: config-blindness in all four directions) atk_5_import_dropped=1, atk_6_import_only_when_qualified=1, atk_11_import_duplicated=1, atk_12_import_transposed=1, atk_19_extra_import=1, atk_25_import_module_from_branch=1 (effect leg: dropped, partial-domain, duplicated, transposed, over-recorded, wrong module) atk_7_boundary_q1=1, atk_13_zero_numerator=1, atk_17_negative_numerator=1 (boundary/partial-domain at q=1, p=0, p<0) atk_8_numerator_only=1, atk_20_wrong_separator=1, atk_21_swapped=1, atk_10_double_resolve=1, atk_16_guarded_wrong_branch=1 (half-fix, product-not-quotient, reciprocal, regrouping, reachable guarded wrong branch) atk_15_divergence=1 — 'Decreasing annotations are required in total correctness semantics'; the total-correctness setting IS enforced, a diverging impl cannot sneak a correct return value through. atk_26_vacuity_constant=1 — VACUITY CONTROL: returning a constant "VACUOUS" with no import fails BOTH clauses with clean unsolved goals.

The obligations are non-vacuous. VERIFIED (3): atk_9_oracle_echo=0, atk_22_branch_split=0, atk_23_render_regrouped=0. DISCLOSURE: my first vacuity probe atk_14_vacuity_control used an unsupported `assert (1 = 0)` spelling and died on a PARSE error, not a semantic refutation, so it is NOT counted as a reject; atk_26 replaces it and refutes cleanly. atk_14 is excluded from the submitted attack list.

MANDATORY RESOLVE LEG — every verifying impl's faithful patch materialized and EXECUTED through the official harness (`run_resolve('sympy__sympy-14976', patch, timeout=3600)` via swebench_unified.harness). All three checked with `git apply --check` in the base_commit worktree FIRST (all three apply clean; atk_23's hunk header needed a count fix, corrected and re-checked).
  patch_atk_9_oracle_echo.diff  => RESOLVED true. F2P test_MpmathPrinter success, PASS_TO_PASS 13/13 success, 0 failures.
  patch_atk_22_branch_split.diff => RESOLVED true. F2P success, P2P 13/13, 0 failures.
  patch_atk_23_render_regrouped.diff => RESOLVED true. F2P success, P2P 13/13, 0 failures.
No verifying wrong impl exists, hence NO materialized faithful patch failed to resolve => verify⇏correct is NOT exhibited. Reports saved *.json.

WHY atk_22 IS THE SHARPEST A-LEG PROBE. Its faithful patch does NOT call `_module_format` at all: it branches on self.`_settings`['fully_qualified_modules'] inline, hardcodes 'mpmath.mpf'/'mpf' per branch, and performs self.module_imports['mpmath'].add('mpf') BY HAND. This is the strongest test of whether the A4/A5 A-references over-constrain (forcing the literal callee) or under-constrain (letting a divergent replay through). It resolved — so replaying both observables faithfully is sufficient, exactly as the A-reference contract claims. Interesting asymmetry, recorded for completeness: atk_18_inlined_resolver expresses the SAME Python-level behaviour but was REJECTED, because loom_solve does not unfold the `mpfImport`/`mpfName` definitions when the impl spells their bodies out literally. That is a false-REJECT (spec slightly too strong on an artefact of the proof automation, not the semantics) — it can only lose a correct impl, never admit a wrong one, so it is not a verify⇏correct hole and not a G-EQ defect.

A-LEG CORRESPONDENCE, CHECKED BY EXECUTION (aleg.py, run against the gold-patched worktree; ALL PASS): A4 (mpfName ↔ `_module_format`('mpmath.mpf') return value): equality holds in BOTH configurations (True=>'mpmath.mpf', False=>'mpf'); default-settings printer == the True branch; the two branches DIFFER (non-vacuity, so the Bool binder is observable). Source read at base_commit pycode.py:113-121 confirms the two-branch shape; default declared at pycode.py:95. A5 (mpfImport ↔ the same call's side effect): law post-state = pre-state ∪ delta verified from 5 pre-states × 2 configurations (fresh, unrelated entries, delta already present, same module other name, mixed) — all 10 PASS; idempotence under double resolution PASS; delta non-empty PASS.

Justifies the delta-as-output-component modelling: the underlying op is set.add, so the delta is order- and pre-state-independent, and a `mut` list post-state would have over-fitted an order the real callee lacks. A3 (Bool binder ↔ the setting): default is True; an explicit {'fully_qualified_modules': False} override takes. BOTH branches confirmed reachable in the real caller — lambdify.py:416 hardcodes the False printer, so refinement.md's refusal to narrow the domain with `require qualified = true` is correct; narrowing would have excluded a live input. A6 (toString ↔ str(int)): agreement on 0, ±1, 5, -232, ±10^50. Cross-check of the three verifying patches vs gold on all observables (qualified render, bare render, recorded imports in both configs, q=1 integer case, negative numerator): byte-identical in every cell.

**REFINEMENT.MD LEG AUDIT.** 8 legs A1–A8, tagged 4×R (A1,A2,A3,A8), 2×I (A6,A7), 2×A-reference (A4,A5), 0 A-consumed, and NO kind-3 — consistent with meta.json axioms == [] and deep_model_references == [mpfName, mpfImport]. The single mention of 'kind-3' is section B's heading asserting their absence. The discriminating content of the change (each part of the quotient wrapped in the constructor) sits in the I-tagged deep `render` concatenation, not behind an axiom about the function under change, so the changed operation is genuinely modelled rather than assumed. Sections C.1 and mapping.md §3.2 accurately and self-critically record the prior revision's refuted claims; I re-encoded both named counterexamples (atk_2, atk_5) and both are now rejected, so the corrected record is truthful, not merely asserted.

**CONCLUSION.** 25 same-spec attacks executed (22 rejected incl. prepatch, a vacuity control and a divergence control), 3 verifying impls all behaviourally gold-equal with materialized faithful patches all RESOLVED under the official harness, and both A-reference legs independently confirmed by execution against the real callee in both configurations and from fuzzed pre-states. No verify⇏correct counterexample. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 25 admissible attacks re-run of 25 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 25 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 22 | `atk_1_prepatch.lean`, `atk_2_config_blind_qualified.lean`, `atk_3_config_blind_bare.lean`, `atk_4_config_inverted.lean`, `atk_5_import_dropped.lean`, `atk_6_import_only_when_qualified.lean`, `atk_7_boundary_q1.lean`, `atk_8_numerator_only.lean`, `atk_10_double_resolve.lean`, `atk_11_import_duplicated.lean`, +12 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_9_oracle_echo.lean`, `atk_22_branch_split.lean`, `atk_23_render_regrouped.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying wrong impl exists: of 25 same-spec attacks, 22 were REJECTED by lean_verify.sh (exit 1) and the 3 that VERIFIED (atk_9_oracle_echo, atk_22_branch_split, atk_23_render_regrouped) are each behaviourally equal to the gold patch on every observable, and each one's materialized faithful patch RESOLVED under the official harness (F2P test_MpmathPrinter + all 13 P2P green). The two prior-pass counterexamples that this spec revision was repaired against were re-encoded and are both rejected: weak-config-blind-qualified => atk_2_config_blind_qualified (unsolved goal '"mpmath.mpf" ++ ... = render qualified p q', i.e. the spec now pins the spelling PER BRANCH) and weak-import-dropped => atk_5_import_dropped (unsolved goal '[] = mpfImport', i.e. the effect clause is live). The prepatch bug also reproduces as a refutation.
```

**Attacks re-run (25):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 25 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_config_blind_qualified.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_config_blind_bare.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_config_inverted.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_import_dropped.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_import_only_when_qualified.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_boundary_q1.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_numerator_only.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 10 — `atk_10_double_resolve.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_import_duplicated.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_import_transposed.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_zero_numerator.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_15_divergence.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_16_guarded_wrong_branch.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_17_negative_numerator.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_18_inlined_resolver.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_19_extra_import.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_20_wrong_separator.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_21_swapped.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk_22_branch_split.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 22 — `atk_23_render_regrouped.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 23 — `atk_24_double_negation.lean` → rejected (same spec, does not verify — good)

Attack 24 — `atk_25_import_module_from_branch.lean` → rejected (same spec, does not verify — good)

Attack 25 — `atk_26_vacuity_constant.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** base_commit worktree (git worktree add --detach 9cbea134220b0b951587e11b63e2c832c7246cbc). Bundle left byte-unmodified (git status --porcelain on benchmark-verified/sympy__sympy-14976/ empty); worktree left clean. Every attack copied Solution.lean editing ONLY the impl region; same_spec(Solution.lean, atk_N.lean, velvet) == True for ALL 25 attacks + the positive control (verified via swebench_unified.markers.same_spec, printed PASS for each).

**POSITIVE CONTROL.** pos_control.lean (impl byte-identical to the bundle): `bash scripts/lean_verify.sh pos_control.lean` => EXIT 0 in 3.4s. Toolchain is live and the spec is satisfiable.

**SCHEDULE.** Attack verifications were run as concurrent background jobs, 4 at a time (xargs -P 4 over scripts/lean_verify.sh); the 3 resolve runs were launched concurrently as detached background jobs. Pass criteria unchanged: all 25 verifies and all 3 resolves ran to completion.

### VERIFY TALLY (exit 0 = verifies, 1 = rejected; command per file: `bash scripts/lean_verify.sh <name>.lean`):
REJECTED (22) — 20 with clean `error: unsolved goals` naming the failing ensures clause, 1 on totality, 1 on syntax: atk_1_prepatch=1 (BOTH clauses fail: '[] = mpfImport' AND '(if q = 1 then toString p else toString p ++ "/" ++ toString q) = render qualified p q') — PREPATCH REPRODUCED atk_2_config_blind_qualified=1, atk_3_config_blind_bare=1, atk_4_config_inverted=1, atk_24_double_negation=1 (value leg: config-blindness in all four directions) atk_5_import_dropped=1, atk_6_import_only_when_qualified=1, atk_11_import_duplicated=1, atk_12_import_transposed=1, atk_19_extra_import=1, atk_25_import_module_from_branch=1 (effect leg: dropped, partial-domain, duplicated, transposed, over-recorded, wrong module) atk_7_boundary_q1=1, atk_13_zero_numerator=1, atk_17_negative_numerator=1 (boundary/partial-domain at q=1, p=0, p<0) atk_8_numerator_only=1, atk_20_wrong_separator=1, atk_21_swapped=1, atk_10_double_resolve=1, atk_16_guarded_wrong_branch=1 (half-fix, product-not-quotient, reciprocal, regrouping, reachable guarded wrong branch) atk_15_divergence=1 — 'Decreasing annotations are required in total correctness semantics'; the total-correctness setting IS enforced, a diverging impl cannot sneak a correct return value through. atk_26_vacuity_constant=1 — VACUITY CONTROL: returning a constant "VACUOUS" with no import fails BOTH clauses with clean unsolved goals.

The obligations are non-vacuous. VERIFIED (3): atk_9_oracle_echo=0, atk_22_branch_split=0, atk_23_render_regrouped=0. DISCLOSURE: my first vacuity probe atk_14_vacuity_control used an unsupported `assert (1 = 0)` spelling and died on a PARSE error, not a semantic refutation, so it is NOT counted as a reject; atk_26 replaces it and refutes cleanly. atk_14 is excluded from the submitted attack list.

MANDATORY RESOLVE LEG — every verifying impl's faithful patch materialized and EXECUTED through the official harness (`run_resolve('sympy__sympy-14976', patch, timeout=3600)` via swebench_unified.harness). All three checked with `git apply --check` in the base_commit worktree FIRST (all three apply clean; atk_23's hunk header needed a count fix, corrected and re-checked).
  patch_atk_9_oracle_echo.diff  => RESOLVED true. F2P test_MpmathPrinter success, PASS_TO_PASS 13/13 success, 0 failures.
  patch_atk_22_branch_split.diff => RESOLVED true. F2P success, P2P 13/13, 0 failures.
  patch_atk_23_render_regrouped.diff => RESOLVED true. F2P success, P2P 13/13, 0 failures.
No verifying wrong impl exists, hence NO materialized faithful patch failed to resolve => verify⇏correct is NOT exhibited. Reports saved *.json.

WHY atk_22 IS THE SHARPEST A-LEG PROBE. Its faithful patch does NOT call `_module_format` at all: it branches on self.`_settings`['fully_qualified_modules'] inline, hardcodes 'mpmath.mpf'/'mpf' per branch, and performs self.module_imports['mpmath'].add('mpf') BY HAND. This is the strongest test of whether the A4/A5 A-references over-constrain (forcing the literal callee) or under-constrain (letting a divergent replay through). It resolved — so replaying both observables faithfully is sufficient, exactly as the A-reference contract claims. Interesting asymmetry, recorded for completeness: atk_18_inlined_resolver expresses the SAME Python-level behaviour but was REJECTED, because loom_solve does not unfold the `mpfImport`/`mpfName` definitions when the impl spells their bodies out literally. That is a false-REJECT (spec slightly too strong on an artefact of the proof automation, not the semantics) — it can only lose a correct impl, never admit a wrong one, so it is not a verify⇏correct hole and not a G-EQ defect.

A-LEG CORRESPONDENCE, CHECKED BY EXECUTION (aleg.py, run against the gold-patched worktree; ALL PASS): A4 (mpfName ↔ `_module_format`('mpmath.mpf') return value): equality holds in BOTH configurations (True=>'mpmath.mpf', False=>'mpf'); default-settings printer == the True branch; the two branches DIFFER (non-vacuity, so the Bool binder is observable). Source read at base_commit pycode.py:113-121 confirms the two-branch shape; default declared at pycode.py:95. A5 (mpfImport ↔ the same call's side effect): law post-state = pre-state ∪ delta verified from 5 pre-states × 2 configurations (fresh, unrelated entries, delta already present, same module other name, mixed) — all 10 PASS; idempotence under double resolution PASS; delta non-empty PASS.

Justifies the delta-as-output-component modelling: the underlying op is set.add, so the delta is order- and pre-state-independent, and a `mut` list post-state would have over-fitted an order the real callee lacks. A3 (Bool binder ↔ the setting): default is True; an explicit {'fully_qualified_modules': False} override takes. BOTH branches confirmed reachable in the real caller — lambdify.py:416 hardcodes the False printer, so refinement.md's refusal to narrow the domain with `require qualified = true` is correct; narrowing would have excluded a live input. A6 (toString ↔ str(int)): agreement on 0, ±1, 5, -232, ±10^50. Cross-check of the three verifying patches vs gold on all observables (qualified render, bare render, recorded imports in both configs, q=1 integer case, negative numerator): byte-identical in every cell.

**REFINEMENT.MD LEG AUDIT.** 8 legs A1–A8, tagged 4×R (A1,A2,A3,A8), 2×I (A6,A7), 2×A-reference (A4,A5), 0 A-consumed, and NO kind-3 — consistent with meta.json axioms == [] and deep_model_references == [mpfName, mpfImport]. The single mention of 'kind-3' is section B's heading asserting their absence. The discriminating content of the change (each part of the quotient wrapped in the constructor) sits in the I-tagged deep `render` concatenation, not behind an axiom about the function under change, so the changed operation is genuinely modelled rather than assumed. Sections C.1 and mapping.md §3.2 accurately and self-critically record the prior revision's refuted claims; I re-encoded both named counterexamples (atk_2, atk_5) and both are now rejected, so the corrected record is truthful, not merely asserted.

**CONCLUSION.** 25 same-spec attacks executed (22 rejected incl. prepatch, a vacuity control and a divergence control), 3 verifying impls all behaviourally gold-equal with materialized faithful patches all RESOLVED under the official harness, and both A-reference legs independently confirmed by execution against the real callee in both configurations and from fuzzed pre-states. No verify⇏correct counterexample. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**REFERENCE DISCIPLINE.** Reference =, sympy at base_commit 9cbea134220b0b951587e11b63e2c832c7246cbc with patch.diff APPLIED (the modeled function's reference, per instructions). Confirmed byte-identical: `diff <(git diff sympy/printing/pycode.py | grep -v '^index ') <(grep -v '^index ' patch.diff)` => IDENTICAL. The only callee, `_module_format`, is UNTOUCHED by the patch, so base_commit is its correct reference; `git show HEAD:sympy/printing/pycode.py` confirms base `_module_format` is byte-identical to patched. Base commit has NO `_print_Rational` in pycode.py (inherits StrPrinter), so I did NOT judge the patch delta as a divergence.

SPEC REGION INTEGRITY (clean). markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend().language) == True. Recomputed markers.region_hashes(Solution.lean) = {axioms 69ccb30fad12..., pure 592a3a92871e..., impl 03070eb077e6..., spec_view c8a907333f2e...} and it matches meta.json G-HYGIENE.data.region_hashes byte-for-byte. So the spec view I attacked IS the one the recorded gates screened. Solution.lean elaborates clean: scripts/lean_verify.sh exit 0, no sorry/error.

### What I attacked and why each attack failed

(1) VALUE LEG — the classic over-strength attack, and the one this bundle previously failed on. Prior revision pinned `def mpfName : String := "mpmath.mpf"` unconditionally, so it demanded 'mpmath.mpf(1)/mpmath.mpf(2)' where the real callee under lambdify's hardcoded `fully_qualified_modules=False` returns 'mpf(1)/mpf(2)'. The CURRENT spec carries the setting as the `qualified : Bool` parameter with the two-branch model `if qualified then "mpmath.mpf" else "mpf"`. Executed against the real repo, BOTH branches now agree exactly: MpmathPrinter().`_print_Rational`(Rational(1,2)) -> 'mpmath.mpf(1)/mpmath.mpf(2)' == render true 1 2, and MpmathPrinter({'fully_qualified_modules': False}) -> 'mpf(1)/mpf(2)' == render false 1 2. The old counterexample is DEAD.

(2) LEAN-SIDE ORACLE EQUALITY (not merely typechecking). I extracted the frozen spec region and appended kernel-decided equalities against strings captured from the real patched repo: 26 boundary rows (F2P 1/2, test_nsolve_rational 1/3, problem-statement 232/3, zero/unit numerators, both signs, 10^50-scale) plus 180 fuzzed rows over 2^63/2^64/10^100/10^30-magnitude values, both configurations. `render` EVALUATES to the real repo's exact bytes in every row: lean_verify.sh exit 0. This closes the toString(Int) vs Python str(int) bridge (refinement.md A6) empirically, not by assertion.

(3) EFFECT LEG — the second prior defect (dropped side effect). Now modeled as `ensures out.2 = mpfImport` with the delta [("mpmath","mpf")]. I attacked the DELTA-vs-SET-DIFFERENCE ambiguity, the most plausible remaining over-strength: when the pre-state ALREADY contains ('mpmath','mpf'), the observed set difference after-before is EMPTY, not the model's one-element delta. That does not make the spec too strong, because mapping.md §3.1 and refinement.md A5 state the contract as the union law post = pre UNION delta, not as the difference. Executed over 4 pre-states x 2 configurations: `after == before | {('mpmath','mpf')}` held in 8/8 (including the two where the raw difference is empty). G-CONF re-confirms on 2,000 fuzzed non-empty pre-states.

Union-law reading is exact because the underlying op is set.add (idempotent, pre-state independent), and I verified `_module_format` is called EXACTLY ONCE per `_print_Rational` (call spy: [('mpmath.mpf', True)]), so no multiplicity freedom is hidden. mapping.md §2 also justifies delta-as-output over a mut binder precisely to AVOID pinning a list order the real defaultdict(set) lacks — i.e. this choice makes the spec weaker/safer, not stronger.

(4) TOTALITY / DOMAIN over-strength. The post-condition is total in (p,q) with no precondition, so I probed outside canonical Rational invariants (q>=1, gcd=1) where a total spec is most likely to over-claim: q=0, q<0, p=q=0, |v| > 10^200. Real callee MATCHED the model on all 12 such observations in both configurations. Unconstrained Int is therefore sound, matching mapping.md §2's claim that the renderer never inspects those invariants.

(5) HIDDEN AMBIENT STATE — could the spec be too strong by omitting another setting the callee reads? Swept all 10 MpmathPrinter.`_default_settings` keys (contract, error_on_reserved, full_prec, fully_qualified_modules, human, inline, order, precision, reserved_word_suffix, user_functions), flipping each bool: only `fully_qualified_modules` changes the rendered value. The single Bool parameter is thus the COMPLETE ambient dependency; nothing else needed modeling. (Non-bool truthy overrides, e.g. 1/''/None/[0], follow Python truthiness and land in the corresponding modeled branch — outside the Bool carrier but consistent with it, per the mapping.md §2 bool<->Bool bijection.)

(6) GATE-BLINDNESS RE-AUDIT. The prior failure mode was shadow and model sharing one error, so I re-ran the bundle's own checkers rather than trusting their recorded status. axiom_check.py exit 0, and it now asserts BOTH branches as hard obligations plus a non-vacuity assertion that the branches differ. conformance_check.py exit 0 with its 3 liveness probes each FIRING as required: flag-blind 'mpmath.mpf' DISAGREES at (False,1,2); bare-pinned 'mpf' DISAGREES at (True,1,2); empty import delta DISAGREES ([] vs [('mpmath','mpf')]). The exact previous defect is now mechanically caught by the gate that once passed it. F2P confirmed green: test_MpmathPrinter and test_nsolve_rational both pass on the reference worktree.

RECORDED G-PANEL-2 FAIL IS STALE — DO NOT RE-JUDGE IT AS MY VERDICT. meta.json carries G-PANEL-2 status=fail / agent_verdict=UNFAITHFUL at checked_at 2026-08-16T03:28:30Z. That note quotes `def mpfName : String := "mpmath.mpf"`, text which is ABSENT from the current Solution.lean (now `def mpfName (qualified : Bool) : String`). Solution.lean mtime 04:02:43Z, i.e. the spec was repaired ~34 min AFTER that fail was stamped; axiom_check.py 04:03, conformance_check.py 04:04, mapping.md 04:15, refinement.md 04:17, with G-AX/G-CONF re-checked at 04:18. Both defects that note cites — (a) the flag-blind constant spelling and (b) the dropped registration effect — are the two things the repair addresses, and I independently re-tested both above and could not reproduce either. Per the retained-attack-labels and stale-fail-routing rules, this fail judges a superseded spec and must not be echoed as a fresh reject; the failing G-PANEL rollup is an echo of this G-PANEL-2 role, so it means re-audit (this run), not repair.

RESIDUAL WEAKNESS, NOT A FAITHFULNESS DEFECT (my lane is over-strength; recording for the panel). The spec models the recording as an output component rather than a mut post-state, so it constrains the delta but not that the impl performs a real mutation on printer state; refinement.md/mapping.md justify this to avoid pinning a nonexistent list order. This makes the spec WEAKER, never stronger, so it cannot ground an UNFAITHFUL verdict here.

**WORKTREE HYGIENE DISCLOSURE.** One `git stash push` fired in the reference worktree mid-review (a heredoc guard did not suppress it as intended); it reverted patch.diff. Caught immediately, restored with `git stash pop`, then re-verified: `git status --porcelain` shows the same 3 modified files, `git stash list` is empty, the pycode.py diff is byte-identical to patch.diff again, and G-AX re-run exit 0. All evidence above was collected against the correctly patched worktree; the worktree is left exactly as found.

**CONCLUSION:** no diverging input exists on the modeled domain. The spec is neither stronger nor drifted from the real patched callee. FAITHFUL.

Counterexample / evidence:

```
None. The negative control PROVES the harness is live rather than blind: ATK2FAITH14976_neg.lean asserting `render true 1 2 = "mpf(1)/mpf(2)"` is REJECTED by the Lean kernel — `error: Tactic native_decide evaluated that the proposition render true 1 2 = "mpf(1)/mpf(2)" is false`, exit 1. A real divergence would therefore have surfaced.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**NO RELAXATION IN THIS BUNDLE.** There is no RELAXED_LEAKAGE.md in /velvet/ and `relaxed_leakage` is absent from meta.json (`'relaxed_leakage' in meta == False`); meta.json gates.G-LEAK.status == "pass", not "relaxed". So I judged this as an ordinary strict-leakage review, not a relaxation disposition. No file in the bundle addresses me: I ran swebench_unified.leakage.reviewer_directed over all 9 bundle files (Solution.lean, Solution_prepatch.lean, axiom_check.py, conformance_check.py, mapping.md, meta.json, properties.py, refinement.md, verdict.md) and every one returned [] -- nothing instructs the panel how to record or which verdict is honest.

SPEC-REGION IDENTITY (as instructed). markers.same_spec(Solution.lean, Solution_prepatch.lean, backend=velvet) == True; per-region byte equality confirmed individually via markers.region_text for all four SPEC_REGIONS: axioms (682 B), pure (2113 B), pre-conditions (0), post-conditions (0) -- all byte-identical. spec_signature agrees. So the view I screened is the one the consumer sees and the prepatch cannot smuggle a different contract.

**WHAT I ACTUALLY SCREENED.** I derived the consumer view myself with markers.spec_view(Solution.lean, get_backend('velvet').language) rather than trusting the stamped G-LEAK, and confirmed impl and prove_correct bodies are elided ("-- implementation elided", "-- proof elided"). Then ran leakage.screen(sol, velvet, patch.diff, instance.problem_statement, instance.test_patch) fresh: hard_failures == [], warnings == []. Confirmed patch.diff is byte-equal to instance.json's `patch` field, so I screened against the real gold.

GOLD-EDIT LOCALIZATION IS ABSENT FROM THE VIEW -- the substantive check, done by hand token-by-token, not just via the mechanical screen. Gold changes sympy/printing/pycode.py, adding MpmathPrinter.`_print_Rational`; leakage.`_patch_changed_symbols`(gold) == {print_Rational, print_Float}; `_patch_changed_files` == sympy/printing/pycode.py. NONE of the edit-localizing tokens occur anywhere in the view: I tested each of pycode, printing, printer, print_, `_print_Rational`, MpmathPrinter, `_module_format`, fully_qualified_modules, module_imports, StrPrinter, doprint, test_ -- all in_view=False.

No gold changed line is reproduced (I checked each of the 6 normalized changed lines against the normalized view; `self._module_format('mpmath.mpf'),` and `def _print_Rational(self, e):` are both absent). No diff markers, no patched file/dotted-module path. The method identifier is `mpfRational`, which embeds neither changed symbol. The axioms/pure prose is deliberately de-named: it says "the helper that resolves the backend float constructor's dotted name" where the repo symbol is `_module_format`, and "the ambient name-spelling configuration" where the repo symbol is `fully_qualified_modules` -- exactly the de-narration the guide asks for, so a solver still has to find the class, the method, and the helper themselves.

THE TWO NON-PUBLIC-VERBATIM TOKENS, AND WHY NEITHER LEAKS. I diffed every >=4-char prose token and every code string literal in the view against problem_statement. `mpmath` and `rational`/`Rational` and `Float` are literally public ("lambdify(modules='mpmath') doesn't wrap rationals"). Only `mpf` / `mpmath.mpf` (string literals in `mpfName`, and the `mpf` fragment of `mpfRational`) are not verbatim in problem_statement. Both are publicly derivable WITHOUT the gold patch: at base_commit 9cbea134220b0b951587e11b63e2c832c7246cbc, the UNPATCHED pycode.py already contains `self._module_format('mpmath.mpf')` at line 332 in the sibling `_print_Float` of the very same class (I read it out of the worktree with `git show 9cbea134...:sympy/printing/pycode.py`, i.e. the pre-patch blob, not the dirty tree). So the mpmath float-constructor spelling is pre-existing repo content one grep away, plus `mpf` is mpmath's public API name. It localizes no edit.

**STATING THE CORRECTED BEHAVIOUR IS NOT LEAKAGE.** The view's `render` does spell out that numerator and denominator are EACH wrapped, and a comment says "instead of as a bare integer ratio". Both are restatements of public content: the problem_statement title is literally "doesn't wrap rationals", it shows the generated source emitting the bare ratio `232/3`, and it says that is why precision is reduced. A spec that withheld the target behaviour would be vacuous, and the leakage rule targets edit reconstruction (path, symbol, diff line, bug/fix narration), not the contract itself. No word from the `_NARRATION` set appears in any spec-view comment (verified by re-running the screen; "change"/"behaviour under change" are not in that vocabulary and carry no pre-patch narration).

**NO HINTS LEAKAGE:** instance.json hints_text is empty, so there is nothing hints-only to echo.

SPEC IS DISCRIMINATING (so the view is not leaking in exchange for a vacuous contract). I ran scripts/lean_verify.sh on both files myself: Solution.lean elaborates clean (exit 0), and Solution_prepatch.lean FAILS at line 89 with the two expected unsolved goals -- `[] = mpfImport` and `(if q = 1 then toString p else toString p ++ "/" ++ toString q) = render qualified p q`. Live G-DIFF, matching refinement.md's claim.

RECORD-HYGIENE OBSERVATION (not my verdict, for the routing layer). Current Solution.lean sha256 is 0f610abe81fa...; G-AX, G-CONF, G-DIFF, G-GOLD, G-HYGIENE, G-INTEGRITY, G-LEAK, G-MUT, G-PBT, G-VERIFY all carry that sha and pass. The three stamped G-PANEL rows (and G-EQ) still carry the SUPERSEDED sha 1e76a95bf384..., and the recorded G-PANEL-2 failure is the config-blind constant-`mpfName` defect that refinement.md §C.1 documents as already repaired (the current view carries the two-branch `mpfName (qualified : Bool)` and the `mpfImport` delta). Per the stale-fail routing rule this cell needs a panel re-audit, which is what this run is; the stale G-PANEL fail is not evidence of a live leak and I did not treat it as one.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
