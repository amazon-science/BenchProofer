# P2 adversarial audit — sympy__sympy-15345

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_1_prepatch.lean`, `atk_2_partial_empty_args.lean`, `atk_3_boundary_multiarg.lean`, `atk_4_diverge.lean`, `atk_5_vacuous_pick.lean`, `atk_6_mismatched_pair.lean`, `atk_7_arm_swap.lean`, `atk_8_diagonal.lean`, `atk_11_partial_long_args.lean`, `atk_12_space_before_close.lean`, `atk_13_head_upcased.lean`, +5 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9_echo_render.lean` |

**Non-vacuity.** The positive control `pos_control_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,14 +69,10 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
       match kind with
       | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
+      | .extremum    => head ++ ['('] ++ args ++ [')']
       | .plainExpr   => head ++ ['('] ++ args ++ [')']
     return result
     -- impl-end
```

Attack 2 — `atk_2_partial_empty_args.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,8 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
+      if args = [] then head else
       match kind with
       | .functionApp => head ++ ['['] ++ args ++ [']']
       | .extremum    => head ++ ['['] ++ args ++ [']']
```

Attack 3 — `atk_3_boundary_multiarg.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,15 +69,12 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
+      let a := if args.any (fun c => c == ',') then args.reverse else args
       match kind with
-      | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
-      | .plainExpr   => head ++ ['('] ++ args ++ [')']
+      | .functionApp => head ++ ['['] ++ a ++ [']']
+      | .extremum    => head ++ ['['] ++ a ++ [']']
+      | .plainExpr   => head ++ ['('] ++ a ++ [')']
     return result
     -- impl-end
 
```

Attack 4 — `atk_4_diverge.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,18 +69,19 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
+    let mut i : Nat := 0
+    while i < 1
+    invariant i = 0
+    do
+      i := 0
     let result : List Char :=
       match kind with
       | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
+      | .extremum    => head ++ ['('] ++ args ++ [')']
       | .plainExpr   => head ++ ['('] ++ args ++ [')']
     return result
     -- impl-end
 
 prove_correct renderNode by
   loom_solve
-  cases kind <;> simp_all [render]
+  all_goals simp_all [render]
```

Attack 5 — `atk_5_vacuous_pick.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,18 +69,15 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
+    let junk :| (junk : Nat) = 0 ∧ junk = 1
     let result : List Char :=
       match kind with
       | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
+      | .extremum    => head ++ ['('] ++ args ++ [')']
       | .plainExpr   => head ++ ['('] ++ args ++ [')']
     return result
     -- impl-end
 
 prove_correct renderNode by
   loom_solve
-  cases kind <;> simp_all [render]
+  all_goals simp_all [render]
```

Attack 6 — `atk_6_mismatched_pair.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,14 +69,10 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
       match kind with
       | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
+      | .extremum    => head ++ ['['] ++ args ++ [')']
       | .plainExpr   => head ++ ['('] ++ args ++ [')']
     return result
     -- impl-end
```

Attack 7 — `atk_7_arm_swap.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,15 +69,11 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
       match kind with
-      | .functionApp => head ++ ['['] ++ args ++ [']']
+      | .functionApp => head ++ ['('] ++ args ++ [')']
       | .extremum    => head ++ ['['] ++ args ++ [']']
-      | .plainExpr   => head ++ ['('] ++ args ++ [')']
+      | .plainExpr   => head ++ ['['] ++ args ++ [']']
     return result
     -- impl-end
 
```

Attack 8 — `atk_8_diagonal.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,15 +69,12 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
+      let h := if head = args then [] else head
       match kind with
-      | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
-      | .plainExpr   => head ++ ['('] ++ args ++ [')']
+      | .functionApp => h ++ ['['] ++ args ++ [']']
+      | .extremum    => h ++ ['['] ++ args ++ [']']
+      | .plainExpr   => h ++ ['('] ++ args ++ [')']
     return result
     -- impl-end
 
```

Attack 9 — `atk_9_echo_render.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,18 +69,9 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
-    let result : List Char :=
-      match kind with
-      | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
-      | .plainExpr   => head ++ ['('] ++ args ++ [')']
-    return result
+    return (render head args kind)
     -- impl-end
 
 prove_correct renderNode by
   loom_solve
-  cases kind <;> simp_all [render]
+  all_goals (cases kind <;> simp_all [render])
```

Attack 10 — `atk_11_partial_long_args.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,15 +69,12 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
+      let a := if args.length < 40 then args else args.take 40
       match kind with
-      | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
-      | .plainExpr   => head ++ ['('] ++ args ++ [')']
+      | .functionApp => head ++ ['['] ++ a ++ [']']
+      | .extremum    => head ++ ['['] ++ a ++ [']']
+      | .plainExpr   => head ++ ['('] ++ a ++ [')']
     return result
     -- impl-end
 
```

Attack 11 — `atk_12_space_before_close.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,14 +69,10 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
       match kind with
       | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
+      | .extremum    => head ++ ['['] ++ args ++ [' ', ']']
       | .plainExpr   => head ++ ['('] ++ args ++ [')']
     return result
     -- impl-end
```

Attack 12 — `atk_13_head_upcased.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,14 +69,11 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
+      let h := head.map (fun c => c.toUpper)
       match kind with
-      | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
+      | .functionApp => h ++ ['['] ++ args ++ [']']
+      | .extremum    => h ++ ['['] ++ args ++ [']']
       | .plainExpr   => head ++ ['('] ++ args ++ [')']
     return result
     -- impl-end
```

Attack 13 — `atk_14_echo_kind_remap.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,18 +69,11 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
-    let result : List Char :=
-      match kind with
-      | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
-      | .plainExpr   => head ++ ['('] ++ args ++ [')']
-    return result
+    return (render head args (match kind with
+      | .plainExpr => .functionApp
+      | k          => k))
     -- impl-end
 
 prove_correct renderNode by
   loom_solve
-  cases kind <;> simp_all [render]
+  all_goals (cases kind <;> simp_all [render])
```

Attack 14 — `atk_15_partial_lowercase_head.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,13 +69,13 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
+      let upper := match head with
+                   | []     => true
+                   | c :: _ => c.isUpper
       match kind with
-      | .functionApp => head ++ ['['] ++ args ++ [']']
+      | .functionApp => if upper then head ++ ['['] ++ args ++ [']']
+                        else head ++ ['('] ++ args ++ [')']
       | .extremum    => head ++ ['['] ++ args ++ [']']
       | .plainExpr   => head ++ ['('] ++ args ++ [')']
     return result
```

Attack 15 — `atk_16_assert_false_control.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,18 +69,16 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
+    assert (with_name_prefix `probe
+      (['('] = (['['] : List Char)))
     let result : List Char :=
       match kind with
       | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
+      | .extremum    => head ++ ['('] ++ args ++ [')']
       | .plainExpr   => head ++ ['('] ++ args ++ [')']
     return result
     -- impl-end
 
 prove_correct renderNode by
   loom_solve
-  cases kind <;> simp_all [render]
+  all_goals (cases kind <;> simp_all [render])
```

Attack 16 — `atk_17_always_bracket.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,15 +69,7 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
-    let result : List Char :=
-      match kind with
-      | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
-      | .plainExpr   => head ++ ['('] ++ args ++ [')']
+    let result : List Char := head ++ ['['] ++ args ++ [']']
     return result
     -- impl-end
 
```

Attack 17 — `atk_18_boundary_space_args.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,15 +69,12 @@
   ensures kind = NodeKind.plainExpr   → out = head ++ ['('] ++ args ++ [')']
   do
     -- impl-start
-    -- Dispatch on the node's kind to choose the surrounding delimiter pair.
-    -- A named-function application and the extremum operators take the square
-    -- bracket form `head[args]`; any other node takes the round-parenthesis
-    -- fallback `head(args)`.
     let result : List Char :=
+      let a := if args.any (fun c => c == ' ') then args.filter (fun c => c != ' ') else args
       match kind with
-      | .functionApp => head ++ ['['] ++ args ++ [']']
-      | .extremum    => head ++ ['['] ++ args ++ [']']
-      | .plainExpr   => head ++ ['('] ++ args ++ [')']
+      | .functionApp => head ++ ['['] ++ a ++ [']']
+      | .extremum    => head ++ ['['] ++ a ++ [']']
+      | .plainExpr   => head ++ ['('] ++ a ++ [')']
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, sympy__sympy-15345 (velvet). VERDICT: SOUND. 17 same-spec attacks encoded and machine-verified; the only one that verifies is behaviourally gold-equivalent, and its faithful patch RESOLVED under the official harness.

SPEC SHAPE (why the A-legs are cheap here): Solution.lean declares NO axiom (grep: 0 axiom decls; meta.json axioms==[], deep_model_references==[]), so there is no A-consumed / A-reference leg and no opaque callee to echo. The behaviour under change is modeled DEEPLY as the transparent `def render` over a finite 3-valued `NodeKind`, and the contract is a TOTAL FUNCTIONAL PIN: master clause `out = render head args kind` plus three per-kind clauses. `render` is grounded solely in the method's own three arguments, so the usual ungrounded-oracle-echo lever cannot express a wrong impl (proved: atk_9 vs atk_14 below).

ALL ATTACKS (same_spec True for every file, checked with swebench_unified.markers.same_spec + VelvetBackend.language; verified with `bash scripts/lean_verify.sh <f>` from the repo root; run 4-at-a-time as concurrent background jobs):
- atk_1_prepatch.lean  PREPATCH BUG re-encoded (.extremum => parens) -> EXIT 1 (unsolved goals on ensures_2). Prepatch reproduced.
- atk_2_partial_empty_args.lean  PARTIAL-DOMAIN: bare head when args=[] -> EXIT 1 (goal `¬args = []`).
- atk_3_boundary_multiarg.lean  BOUNDARY: reverses args only when a comma is present (correct on every 1-arg node, wrong exactly on the >=2-arg F2P shape) -> EXIT 1.
- atk_4_diverge.lean  CONTROL-FLOW-EFFECT: prepatch value returned after a non-terminating `while i < 1` -> EXIT 1. The total-correctness lever is genuinely closed: "Decreasing annotations are required in total correctness semantics" + failed loop VC. Divergence CANNOT buy vacuity on this bundle.
- atk_5_vacuous_pick.lean  VACUITY: infeasible demonic `let junk :| junk = 0 ∧ junk = 1` ahead of the prepatch value -> EXIT 1 with goal `⊢ False` in case choice_1. Under demonic choice the infeasible pick is an OBLIGATION, not an assumption.
- atk_6_mismatched_pair.lean  near-miss: '[' opened / ')' closed on .extremum -> EXIT 1.
- atk_7_arm_swap.lean  satisfies the load-bearing extremum clause but swaps the two UNCHANGED endpoints (functionApp->parens, plainExpr->brackets) -> EXIT 1.
- atk_8_diagonal.lean  PARTIAL-DOMAIN on the never-fuzzed diagonal head=args (drops head there) -> EXIT 1 (goal `head = args -> args = []`).
- atk_9_echo_render.lean  UNGROUNDED-ORACLE-ECHO probe: `return (render head args kind)` -> EXIT 0, VERIFIES. See RESOLVE below.
- atk_11_partial_long_args.lean  PARTIAL-DOMAIN beyond the fuzzed range: truncates args at 40 chars (every G-CONF/G-PBT probe is shorter) -> EXIT 1. The master clause pins args verbatim at every length.
- atk_12_space_before_close.lean  whitespace near-miss `Max[x, y, z ]` (still "the bracket form") -> EXIT 1.
- atk_13_head_upcased.lean  head remapped (upper-cased) on both bracket arms — aimed at refinement §B's "mapped name == fallthrough head name" claim -> EXIT 1.
- atk_14_echo_kind_remap.lean  the SHARPEST A-leg probe: same echo lever as atk_9 but feeds `render` a remapped kind (plainExpr->functionApp), i.e. 2 arms right / fallback wrong -> EXIT 1. This is the decisive control: the echo verifies ONLY when it echoes the model at the method's OWN kind, so `render` is not an answer key.
- atk_15_partial_lowercase_head.lean  PARTIAL-DOMAIN keyed on head case: bracket form for every upper-case head (Max/Min and every known_functions image), parens for a lower-case head. Had it verified, its faithful patch would pass the F2P extremum assertion yet break the SAME test's `mcode(f(x, y, z)) == "f[x, y, z]"` -> EXIT 1.
- atk_16_assert_false_control.lean  ADMISSIBILITY CONTROL: in-impl `assert (['('] = ['['])` ahead of the prepatch value -> EXIT 1 with `⊢ False` in all three kind cases. In-region asserts are PROVED, not assumed, so no in-impl claim can be smuggled in.
- atk_17_always_bracket.lean  OVER-FIX: ignores `kind`, always brackets -> EXIT 1 (`⊢ False` on the plainExpr clause). The spec pins the fallback too, not merely "some delimiter pair".
- atk_18_boundary_space_args.lean  BOUNDARY on the REAL F2P text shape: the actual joined args for Max(x,y,z) is "x, y, z", which CONTAINS SPACES; this collapses ", "->"," exactly when a space is present and is correct on every space-free probe -> EXIT 1.
POSITIVE CONTROL pos_control_gold.lean -> EXIT 0 (verifies).

MANDATORY RESOLVE (the only verifying attack): atk_9_echo_render.lean. Materialized its faithful refined patch at atk_9_faithful.diff — an explicit `def _print_MinMaxBase(self, expr): return expr.func.__name__ + "[%s]" % self.stringify(expr.args, ", ")` (the refinement of `render(head,args,.extremum) = head ++ '[' ++ args ++ ']'`), deliberately materialized WITHOUT the gold `known_functions` Max/Min entries so it is not a copy of patch.diff. `git apply --check` in the base_commit worktree (@ 9ef28fba5b) -> APPLY_CHECK_OK. Then `python -c "from swebench_unified.harness import run_resolve; run_resolve('sympy__sympy-15345', <diff>, run_id='geq-atk9-ytq0bzmu')"` -> RESOLVED=True, COMPLETED=True, FAIL_TO_PASS {'success': ['test_Function'], 'failure': []}, PASS_TO_PASS 8/8 success, PASS_TO_FAIL/FAIL_TO_FAIL empty. So the one verifying impl resolves: NO verify⇏ correct witness. (Bonus: this executed resolve independently CONFIRMS refinement.md §B — the alias half alone is sufficient to resolve.)

A-LEG / MODEL↔PATCH CORRESPONDENCE AUDIT (run against the real repo, not taken on trust; three worktrees at base_commit: pristine, +gold, +dict-half-only):
- .extremum <-> MinMaxBase: PRE Max(2,a)->'Max(2, a)', Max(a,b,c)->'Max(a, b, c)', Min(b,c)->'Min(b, c)' (round parens, via emptyPrinter/str fallback); POST 'Max[2, a]', 'Max[a, b, c]', 'Min[b, c]'. Matches the `.extremum => head ++ ['['] ++ args ++ [']']` arm and confirms the prepatch routing. MRO check: Max.`__mro__` = Max, MinMaxBase, Expr, LatticeOp, AssocOp, Application — and printer.py:280-284 keeps `*Base`-suffixed classes in the dispatch list, which is exactly WHY the `_print_MinMaxBase` alias is reachable. mapping.md §1's binding is correct.
- .functionApp: g(a,b,c)->'g[a, b, c]' and sin(a)->'Sin[a]' unchanged pre and post (MCodePrinter.`_print_Function` always brackets). Matches the arm; correctly recorded as an unchanged endpoint.
- .plainExpr: Eq(a,b)->'Eq(a, b)' unchanged pre and post (round-paren generic fallback). Matches the arm.
- refinement.md §B inertness claim, MEASURED not assumed: dict-half-only worktree renders Max(a,b,c)->'Max(a, b, c)' and the F2P expr ->'Max(a, b, c)*Min(b, c)' (i.e. the dict entries change NOTHING); gold renders 'Max[a, b, c]*Min[b, c]'. Confirms the alias is load-bearing and the dict half is behaviourally inert, so modeling it as identity (no do-block node) is honest, and no separate failing prepatch is owed for it.
- **LEG TAGS:** refinement.md §A has exactly 4 legs tagged R, R+I, R, I — all R/I, zero kind-3, zero A-legs; §C's "no consumed axiom and no A-reference deep model" is consistent with the artifact (0 axiom decls, meta.json axioms==[]/deep_model_references==[]), so G-AX=skip is correctly justified. The discriminating-content claim (§A last para: the `.extremum` bracket arm <-> the `_print_MinMaxBase` alias) is exactly what my atk_1 (rejected) and atk_9 (verified + resolved) bracket from both sides. No inexpressible-changed-op is hidden anywhere.

**EVIDENCE HYGIENE:** atk_10_assert_false_control.lean is EXCLUDED from the attack list — it exited 1 on a SYNTAX error ("Failed to parse an assertion without names", bare `assert (1 = 0)`), which is not a semantic rejection and would be inadmissible as evidence; atk_16 is its correctly-encoded (`with_name_prefix`) replacement and rejects semantically with `⊢ False`. Solution.lean sha256 7f00ed615c4a29266203e71ad8e6b339c621194a160379c7efba7c75e11bf6ba matches meta.json's G-VERIFY/G-CONF sources, so this audit describes the shipped spec; 0 sorry/admit. only (base_wt worktree left in place for apply-check reproducibility; the two probe worktrees were removed).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_1_prepatch.lean`, `atk_2_partial_empty_args.lean`, `atk_3_boundary_multiarg.lean`, `atk_4_diverge.lean`, `atk_5_vacuous_pick.lean`, `atk_6_mismatched_pair.lean`, `atk_7_arm_swap.lean`, `atk_8_diagonal.lean`, `atk_11_partial_long_args.lean`, `atk_12_space_before_close.lean`, `atk_13_head_upcased.lean`, +5 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9_echo_render.lean` |

**Non-vacuity.** The positive control `pos_control_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_empty_args.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary_multiarg.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_diverge.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_vacuous_pick.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_mismatched_pair.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_arm_swap.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_diagonal.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_echo_render.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_11_partial_long_args.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_12_space_before_close.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_13_head_upcased.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_14_echo_kind_remap.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_15_partial_lowercase_head.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_16_assert_false_control.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_17_always_bracket.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_18_boundary_space_args.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, sympy__sympy-15345 (velvet). VERDICT: SOUND. 17 same-spec attacks encoded and machine-verified; the only one that verifies is behaviourally gold-equivalent, and its faithful patch RESOLVED under the official harness.

SPEC SHAPE (why the A-legs are cheap here): Solution.lean declares NO axiom (grep: 0 axiom decls; meta.json axioms==[], deep_model_references==[]), so there is no A-consumed / A-reference leg and no opaque callee to echo. The behaviour under change is modeled DEEPLY as the transparent `def render` over a finite 3-valued `NodeKind`, and the contract is a TOTAL FUNCTIONAL PIN: master clause `out = render head args kind` plus three per-kind clauses. `render` is grounded solely in the method's own three arguments, so the usual ungrounded-oracle-echo lever cannot express a wrong impl (proved: atk_9 vs atk_14 below).

ALL ATTACKS (same_spec True for every file, checked with swebench_unified.markers.same_spec + VelvetBackend.language; verified with `bash scripts/lean_verify.sh <f>` from the repo root; run 4-at-a-time as concurrent background jobs):
- atk_1_prepatch.lean  PREPATCH BUG re-encoded (.extremum => parens) -> EXIT 1 (unsolved goals on ensures_2). Prepatch reproduced.
- atk_2_partial_empty_args.lean  PARTIAL-DOMAIN: bare head when args=[] -> EXIT 1 (goal `¬args = []`).
- atk_3_boundary_multiarg.lean  BOUNDARY: reverses args only when a comma is present (correct on every 1-arg node, wrong exactly on the >=2-arg F2P shape) -> EXIT 1.
- atk_4_diverge.lean  CONTROL-FLOW-EFFECT: prepatch value returned after a non-terminating `while i < 1` -> EXIT 1. The total-correctness lever is genuinely closed: "Decreasing annotations are required in total correctness semantics" + failed loop VC. Divergence CANNOT buy vacuity on this bundle.
- atk_5_vacuous_pick.lean  VACUITY: infeasible demonic `let junk :| junk = 0 ∧ junk = 1` ahead of the prepatch value -> EXIT 1 with goal `⊢ False` in case choice_1. Under demonic choice the infeasible pick is an OBLIGATION, not an assumption.
- atk_6_mismatched_pair.lean  near-miss: '[' opened / ')' closed on .extremum -> EXIT 1.
- atk_7_arm_swap.lean  satisfies the load-bearing extremum clause but swaps the two UNCHANGED endpoints (functionApp->parens, plainExpr->brackets) -> EXIT 1.
- atk_8_diagonal.lean  PARTIAL-DOMAIN on the never-fuzzed diagonal head=args (drops head there) -> EXIT 1 (goal `head = args -> args = []`).
- atk_9_echo_render.lean  UNGROUNDED-ORACLE-ECHO probe: `return (render head args kind)` -> EXIT 0, VERIFIES. See RESOLVE below.
- atk_11_partial_long_args.lean  PARTIAL-DOMAIN beyond the fuzzed range: truncates args at 40 chars (every G-CONF/G-PBT probe is shorter) -> EXIT 1. The master clause pins args verbatim at every length.
- atk_12_space_before_close.lean  whitespace near-miss `Max[x, y, z ]` (still "the bracket form") -> EXIT 1.
- atk_13_head_upcased.lean  head remapped (upper-cased) on both bracket arms — aimed at refinement §B's "mapped name == fallthrough head name" claim -> EXIT 1.
- atk_14_echo_kind_remap.lean  the SHARPEST A-leg probe: same echo lever as atk_9 but feeds `render` a remapped kind (plainExpr->functionApp), i.e. 2 arms right / fallback wrong -> EXIT 1. This is the decisive control: the echo verifies ONLY when it echoes the model at the method's OWN kind, so `render` is not an answer key.
- atk_15_partial_lowercase_head.lean  PARTIAL-DOMAIN keyed on head case: bracket form for every upper-case head (Max/Min and every known_functions image), parens for a lower-case head. Had it verified, its faithful patch would pass the F2P extremum assertion yet break the SAME test's `mcode(f(x, y, z)) == "f[x, y, z]"` -> EXIT 1.
- atk_16_assert_false_control.lean  ADMISSIBILITY CONTROL: in-impl `assert (['('] = ['['])` ahead of the prepatch value -> EXIT 1 with `⊢ False` in all three kind cases. In-region asserts are PROVED, not assumed, so no in-impl claim can be smuggled in.
- atk_17_always_bracket.lean  OVER-FIX: ignores `kind`, always brackets -> EXIT 1 (`⊢ False` on the plainExpr clause). The spec pins the fallback too, not merely "some delimiter pair".
- atk_18_boundary_space_args.lean  BOUNDARY on the REAL F2P text shape: the actual joined args for Max(x,y,z) is "x, y, z", which CONTAINS SPACES; this collapses ", "->"," exactly when a space is present and is correct on every space-free probe -> EXIT 1.
POSITIVE CONTROL pos_control_gold.lean -> EXIT 0 (verifies).

MANDATORY RESOLVE (the only verifying attack): atk_9_echo_render.lean. Materialized its faithful refined patch at atk_9_faithful.diff — an explicit `def _print_MinMaxBase(self, expr): return expr.func.__name__ + "[%s]" % self.stringify(expr.args, ", ")` (the refinement of `render(head,args,.extremum) = head ++ '[' ++ args ++ ']'`), deliberately materialized WITHOUT the gold `known_functions` Max/Min entries so it is not a copy of patch.diff. `git apply --check` in the base_commit worktree (@ 9ef28fba5b) -> APPLY_CHECK_OK. Then `python -c "from swebench_unified.harness import run_resolve; run_resolve('sympy__sympy-15345', <diff>, run_id='geq-atk9-ytq0bzmu')"` -> RESOLVED=True, COMPLETED=True, FAIL_TO_PASS {'success': ['test_Function'], 'failure': []}, PASS_TO_PASS 8/8 success, PASS_TO_FAIL/FAIL_TO_FAIL empty. So the one verifying impl resolves: NO verify⇏ correct witness. (Bonus: this executed resolve independently CONFIRMS refinement.md §B — the alias half alone is sufficient to resolve.)

A-LEG / MODEL↔PATCH CORRESPONDENCE AUDIT (run against the real repo, not taken on trust; three worktrees at base_commit: pristine, +gold, +dict-half-only):
- .extremum <-> MinMaxBase: PRE Max(2,a)->'Max(2, a)', Max(a,b,c)->'Max(a, b, c)', Min(b,c)->'Min(b, c)' (round parens, via emptyPrinter/str fallback); POST 'Max[2, a]', 'Max[a, b, c]', 'Min[b, c]'. Matches the `.extremum => head ++ ['['] ++ args ++ [']']` arm and confirms the prepatch routing. MRO check: Max.`__mro__` = Max, MinMaxBase, Expr, LatticeOp, AssocOp, Application — and printer.py:280-284 keeps `*Base`-suffixed classes in the dispatch list, which is exactly WHY the `_print_MinMaxBase` alias is reachable. mapping.md §1's binding is correct.
- .functionApp: g(a,b,c)->'g[a, b, c]' and sin(a)->'Sin[a]' unchanged pre and post (MCodePrinter.`_print_Function` always brackets). Matches the arm; correctly recorded as an unchanged endpoint.
- .plainExpr: Eq(a,b)->'Eq(a, b)' unchanged pre and post (round-paren generic fallback). Matches the arm.
- refinement.md §B inertness claim, MEASURED not assumed: dict-half-only worktree renders Max(a,b,c)->'Max(a, b, c)' and the F2P expr ->'Max(a, b, c)*Min(b, c)' (i.e. the dict entries change NOTHING); gold renders 'Max[a, b, c]*Min[b, c]'. Confirms the alias is load-bearing and the dict half is behaviourally inert, so modeling it as identity (no do-block node) is honest, and no separate failing prepatch is owed for it.
- **LEG TAGS:** refinement.md §A has exactly 4 legs tagged R, R+I, R, I — all R/I, zero kind-3, zero A-legs; §C's "no consumed axiom and no A-reference deep model" is consistent with the artifact (0 axiom decls, meta.json axioms==[]/deep_model_references==[]), so G-AX=skip is correctly justified. The discriminating-content claim (§A last para: the `.extremum` bracket arm <-> the `_print_MinMaxBase` alias) is exactly what my atk_1 (rejected) and atk_9 (verified + resolved) bracket from both sides. No inexpressible-changed-op is hidden anywhere.

**EVIDENCE HYGIENE:** atk_10_assert_false_control.lean is EXCLUDED from the attack list — it exited 1 on a SYNTAX error ("Failed to parse an assertion without names", bare `assert (1 = 0)`), which is not a semantic rejection and would be inadmissible as evidence; atk_16 is its correctly-encoded (`with_name_prefix`) replacement and rejects semantically with `⊢ False`. Solution.lean sha256 7f00ed615c4a29266203e71ad8e6b339c621194a160379c7efba7c75e11bf6ba matches meta.json's G-VERIFY/G-CONF sources, so this audit describes the shipped spec; 0 sorry/admit. only (base_wt worktree left in place for apply-check reproducibility; the two probe worktrees were removed).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS AUDIT (attacker role 2, spec-too-strong / drift) for sympy__sympy-15345 velvet bundle. Verdict: FAITHFUL. No input found where the modelled function disagrees with the real repo callee inside the bound abstraction domain.

#### Setup / provenance
- Bundle: benchmark-verified/sympy__sympy-15345/velvet/ (Solution.lean, Solution_prepatch.lean, refinement.md, mapping.md, conformance_check.py).
- Reference for the modelled function = base_commit worktree WITH patch.diff applied:  (git HEAD 9ef28fba5b, `git diff --stat` = sympy/printing/mathematica.py | 4 ++++, matching patch.diff exactly). I did NOT judge against the base version, so the patch delta itself is not miscounted as drift.
- Clean base copy for control only:  (git checkout of mathematica.py, MinMaxBase absent).
- sympy is py2/3-era and the host lacked mpmath; resolved by unpacking mpmath-1.4.1 to  and running PYTHONPATH=:<worktree>. Real repo executes fine.

### SPEC BYTE-IDENTITY (prerequisite)
swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) == True; spec_view equality also True. Only the impl region differs (.extremum arm: '[' ']' vs '(' ')'). So the prepatch is a legitimate same-spec control.

#### Discrimination / controls
- scripts/lean_verify.sh Solution.lean -> exit 0 (gold verifies).
- scripts/lean_verify.sh Solution_prepatch.lean -> exit 1, 'unsolved goals' at Solution_prepatch.lean:85 (the frozen clause `kind = .extremum -> out = head ++ ['['] ++ args ++ [']']`). The spec is discriminating, not vacuous.
- F2P direction confirmed on the real repo: applied instance test_patch. BASE+test_patch -> test_Function FAILS (reproduces bug); GOLD+test_patch -> test_Function PASSES. The modelled delta is the real fix.
- G-CONF (conformance_check.py, seed 15345) re-run BY ME on the patched worktree: 'G-CONF OK ... 83100 node renders, 0 disagreements'. Re-run on the BASE worktree: 'G-CONF FAIL: 5 disagreements', all kind=extremum (Max(2,a) shadow Max[2,a] vs oracle Max(2,a), etc.). The check bites exactly the load-bearing hunk and is not a rubber stamp.

### INDEPENDENT DIVERGENCE HUNT (my own, not the bundle's)
1. Extremum clause stress: 6176 randomized Max/Min nodes (symbols, Integers, Rationals, pi, E, Float, oo/-oo, sin/cos/Add/Mul/Pow args, arity 2-5) plus nested cases Max(a,Min(b,c)), Min(Max(a,b),c), Max(a,Max(b,c)+1), Max(sin(Max(a,b)),c). ZERO violations of `out = head ++ '[' ++ args ++ ']'`. Settings variations (user_functions Max->MyMax and cond-list form, allow_unknown_functions, order=lex, precision=5) all still render Max[a, b].
2. Structural proof of the extremum clause: post-patch `MCodePrinter._print_MinMaxBase is MCodePrinter._print_Function` is True, and the source of MCodePrinter.`_print_Function` contains '[%s]' on BOTH return paths and no '(%s)' at all. So a MinMaxBase node cannot render with parens post-patch by construction, not merely by sampling.
3. functionApp arm: 67 nodes dispatching to `_print_Function` (sin cos tan exp log Abs floor ceiling factorial gamma zeta erf sign re im conjugate LambertW Ei loggamma harmonic Chi Si Ci besselj polygamma Mod, user Functions g/h, Piecewise) -> all bracketed, 0 non-bracket.
4. plainExpr arm on genuinely un-dispatched nodes (dispatch landing on the generic `_print_Expr`/`_print_Basic` fallback): Trace, Determinant, Adjoint, Contains, Implies, ITE, Range, KroneckerProduct, DiagonalMatrix, DiagonalOf, FunctionMatrix, and two synthetic fresh Expr subclasses (Frob/Wibble, the cleanest test of 'a node the printer has no dedicated form for') -> ALL render exactly head(args), matching the plainExpr arm.
5. Broad 39-node zoo diffed end-to-end against the model with kind assigned by mapping.md A3's rule: agree=39, DIVERGENCES=0.

### CANDIDATE DIVERGENCES INVESTIGATED AND DISMISSED (why each is not spec drift)
(a) known_functions RENAMING (sharpest candidate). If one binds `head := expr.func.__name__` literally, the model predicts 'sin[a]' while the real printer emits 'Sin[a]' (also exp/Exp, log/Log, conjugate/Conjugate, acsch/ArcCsch, atanh/ArcTanh). NOT drift: `head` is an INPUT to renderNode, not a modelled output. mapping.md §2 binds head as 'identity on the character content; an INPUT to renderNode (unchanged by the patch)', and G-CONF feeds the model the head RECOVERED FROM THE REAL RENDER on both sides. The spec makes no claim about which name is chosen; it only fixes the delimiter pair around a given head/args. The renaming is the unchanged `known_functions` lookup, identical pre- and post-patch, so it cannot be a divergence on the modelled behaviour. Note mapping.md §1's parenthetical 'expr.func.`__name__`' is loose prose, but §2's binding (head is a recovered input) governs and is what G-CONF implements.

(b) Hold[...] wrappers: Integral -> 'Hold[Integrate[x^2, x]]', Sum -> 'Hold[Sum[...]]', Derivative -> 'Hold[D[...]]'. A naive regex parse yields head='Hold' with a bracket pair, whereas kind=plainExpr predicts 'Hold(...)'. NOT drift: these classes have DEDICATED methods defined in MCodePrinter itself (`_print_Integral`/`_print_Sum`/`_print_Derivative`, confirmed present in MCodePrinter.`__dict__`), so they are neither un-dispatched nor `_print_Function`-dispatched. They fall OUTSIDE the three-kind domain mapping.md §2 binds (.plainExpr := 'a node with no dedicated `_print_`* in MCodePrinter'). Reading them as plainExpr misapplies the abstraction rather than exposing a too-strong clause.

(c) Indexed -> 'A[1]', Idx('i') -> 'i', Product/SeqFormula limit tuples rendering '(a, 1, c)' vs a stringify-based '{a, 1, c}'. These dispatch to `_print_Expr`, and in codeprinter.py line 390 `_print_Expr = _print_Function` — i.e. they are aliased to the FUNCTION path, not the generic paren fallback, so under mapping.md A3 they classify as .functionApp/out-of-domain, not .plainExpr. Indexed additionally overrides its own str form. Again a misclassification artifact, not a clause the real repo falsifies. Crucially none of these is a MinMaxBase node, so none can touch the load-bearing .extremum clause.

(d) refinement.md §B inertness claim independently VERIFIED by building two half-patches: dict-only (known_functions Max/Min added, alias withheld) -> Max(a,b,c) still renders 'Max(a, b, c)' (parens, inert); alias-only (`_print_MinMaxBase` = `_print_Function`, dict withheld) -> 'Max[a, b, c]' (fix already achieved). So the dict hunk is genuinely observationally inert and modelling it as identity is correct.

### Conclusion
The three ensures clauses are each satisfied by the patched real printer on every input inside the domain mapping.md §2 binds, and the extremum clause is true by construction (the alias makes the extremum method literally be `_print_Function`, whose every return path is bracketed). The clauses are not stronger than the patched repo behaviour. Every apparent counterexample I found is either an input outside the bound abstraction domain (dedicated MCodePrinter methods; `_print_Expr`-aliased classes) or concerns `head`, which is a fixed input rather than modelled output. No diverging input exists to cite, so I cannot and do not claim a defect. Verdict: FAITHFUL.

Minor, non-defect observation for the record (no verdict impact): mapping.md §1's gloss of head as 'expr.func.`__name__`' is imprecise given known_functions renaming; §2's binding (head recovered from the real render, held fixed on both G-CONF sides) is the operative one and is implemented correctly. Also mapping.md §1's plainExpr row cites 'StrPrinter.`_print_`...' loosely where the generic path is really CodePrinter.`_print_Expr`/`_print_Basic`. Both are prose polish, not spec drift — and per the retained-attack rule I did not inflate either into a reject verdict.

No bundle files were modified; all scratch under /tmp (worktree copies, mpmath unpack, half-patch trees).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Instance sympy__sympy-15345 (velvet). No relaxation in this bundle: meta.json has no `relaxed_leakage` key and there is no RELAXED_LEAKAGE.md anywhere under the instance dir (grep -ril relaxed hits only the sibling nagini/ bundle). Judged as a standard leakage review.

### WHAT I MEASURED (my own runs, not the stored record):
1. Spec byte-identity: PYTHONPATH=src python3 -> markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) == True. Recomputed markers.spec_view() on both files and diffed: the only difference between gold and prepatch is inside the elided impl region (prepatch: `.extremum => head ++ ['('] ++ args ++ [')']` plus its own impl comment). The consumer-visible view is identical.
2. Verifier: scripts/lean_verify.sh Solution.lean -> exit 0. Solution_prepatch.lean -> exit 1, unsolved goals at :85 on `ensures_2: kind = NodeKind.extremum -> out = head ++ ['['] ++ args ++ [']']` (goal reduces to False) plus the `out = render head args kind` clause. So the extremum bracket clause is what pins the fix.
3. Load-bearing control (the strip-and-see-if-prepatch-verifies test): copied Solution_prepatch.lean to a mktemp dir, deleted the `kind = NodeKind.extremum -> ... ['['] ...` ensures line and flipped render's extremum arm to parens; lean_verify.sh then returns exit 0. Confirms the extremum clause (not prose) carries the discriminator, i.e. a spec that omits it does not pin the gold behaviour.
4. Mechanical screen re-run independently: leakage.screen(Solution.lean, VelvetBackend.language, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. leakage.reviewer_directed() over every file in the bundle dir -> empty for all, so no file in the bundle addresses the reviewer or tries to dictate a verdict/recording. (meta.json/verdict.md do carry a prior G-PANEL-3 NO-LEAKAGE record; I treated that as a record and did not inherit it -- everything above is my measurement.)
5. Consumer surface: eval/adapter.py exposes only spec_view(model_src) (with hard elision guards for impl and prove_correct bodies) plus selected meta fields. mapping.md / refinement.md are auditor-facing and never handed to the solver -- and those are the files that do name mathematica.py, MCodePrinter, `_print_MinMaxBase = _print_Function`, known_functions, and stringify. Correct side of the line.

SPEC VIEW vs PUBLIC problem_statement (hints_text explicitly excluded): The statement discloses the whole discriminating behaviour: mathematica_code(Max(x,2)) should give 'Max[x,2]' but gives 'Max(2, x)'. So publicly known: the extremum operator must render as Head[args] (square brackets, called out as valid Mathematica), and the parenthesised form is the wrong fallback; argument reordering (2, x) is visible and is NOT part of the fix (mapping.md 2 note, and the model correctly treats args as a fixed input). Spec-view content: inductive NodeKind {functionApp, extremum, plainExpr}; render/renderNode with functionApp -> brackets, extremum -> brackets, plainExpr -> parens.

The load-bearing clause restates exactly the public requirement. functionApp-uses-brackets is generic Mathematica call syntax, already shown by the statement writing Max[x,2]. plainExpr-uses-parens is the pre-existing fallback, shown by the buggy 'Max(2, x)'. Grepped the spec view for every mechanism token in the gold diff: mathematica, MCodePrinter, `_print_Function`, MinMaxBase, known_functions, stringify, sympy, printer.py -> zero hits. The view is written abstractly ('this code printer', 'the target language', 'the maximum/minimum operators'), and its identifiers (NodeKind, functionApp, extremum, plainExpr, render, renderNode) echo no patched repo symbol -- 'extremum' in particular avoids the MinMax class name. Narration check: the only 'patch' substring hit is inside the word 'dispatch', which the word-boundary `_NARRATION_RE` correctly does not match; no bug/fix/wrong/previously narration, no diff markers, no gold line reproduced.

The one item I weighed and cleared: the spec view says 'maximum/minimum', while problem_statement names only Max (Min appears only in hints_text and in the hidden FAIL_TO_PASS assertion mcode(Max(x,y,z)*Min(y,z))). That is behavioural scope the spec owes to be faithful and resolve-implying, not disclosure of the gold edit: it is a trivial generalisation of the public fact that any Mathematica function application uses square brackets, it does not name the MinMaxBase class or the alias, and it does not force the class-level mechanism (per-operator `_print_Max`/`_print_Min` would satisfy the spec equally). It localises no edit. Nothing in the spec view reveals where or how the repo changes beyond what the problem statement already makes public.

**Verdict:** NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
