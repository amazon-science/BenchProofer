# P2 adversarial audit — django__django-13158

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py` |

**Non-vacuity.** The positive control `control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,22 +139,10 @@
     # post-conditions-end
     # impl-start
     q.where_empty = True
-    i = 0
-    while i < len(q.child_empty):
-        # invariants-start
-        Invariant(Acc(q.where_empty) and q.where_empty == True)
-        Invariant(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
-        Invariant(0 <= i and i <= len(q.child_empty))
-        Invariant(len(q.child_empty) == Old(len(q.child_empty)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                 q.child_empty[k] == True))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len - i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(q.child_empty) - i + 1))
-        # invariants-end
-        q.child_empty[i] = True
-        i = i + 1
+    # PRE-PATCH BUG re-encoded: only the query's own outer condition is forced
+    # to match nothing; every constituent is left matching something.
+    # invariants-start
+    # invariants-end
     # impl-end
 
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -186,24 +186,11 @@
     # impl-start
     obj = Query()
     obj.where_empty = q.where_empty
-    i = 0
-    while i < len(q.child_empty):
-        # invariants-start
-        Invariant(Acc(q.where_empty, 1 / 2))
-        Invariant(Acc(q.child_empty, 1 / 2) and Acc(list_pred(q.child_empty), 1 / 2))
-        Invariant(Acc(obj.where_empty) and obj.where_empty == q.where_empty)
-        Invariant(Acc(obj.child_empty) and Acc(list_pred(obj.child_empty)))
-        Invariant(0 <= i and i <= len(q.child_empty))
-        Invariant(len(obj.child_empty) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                 obj.child_empty[k] == q.child_empty[k]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len - i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(q.child_empty) - i + 1))
-        # invariants-end
-        obj.child_empty.append(q.child_empty[i])
-        i = i + 1
+    # PRE-PATCH BUG re-encoded: the copy SHARES the source's constituent
+    # sequence instead of duplicating it (the shallow __dict__.copy() alias).
+    obj.child_empty = q.child_empty
+    # invariants-start
+    # invariants-end
     return obj
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,22 +139,22 @@
     # post-conditions-end
     # impl-start
     q.where_empty = True
-    i = 0
-    while i < len(q.child_empty):
-        # invariants-start
-        Invariant(Acc(q.where_empty) and q.where_empty == True)
-        Invariant(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
-        Invariant(0 <= i and i <= len(q.child_empty))
-        Invariant(len(q.child_empty) == Old(len(q.child_empty)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                 q.child_empty[k] == True))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len - i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(q.child_empty) - i + 1))
-        # invariants-end
-        q.child_empty[i] = True
-        i = i + 1
+    # PARTIAL DOMAIN: the constituent descent happens only for compounds with
+    # at most three operands; wider compounds keep yielding their rows.
+    if len(q.child_empty) <= 3:
+        i = 0
+        while i < len(q.child_empty):
+            # invariants-start
+            Invariant(Acc(q.where_empty) and q.where_empty == True)
+            Invariant(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
+            Invariant(0 <= i and i <= len(q.child_empty))
+            Invariant(len(q.child_empty) == Old(len(q.child_empty)))
+            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                     q.child_empty[k] == True))))
+            Invariant(MustTerminate(len(q.child_empty) - i + 1))
+            # invariants-end
+            q.child_empty[i] = True
+            i = i + 1
     # impl-end
 
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -186,21 +186,17 @@
     # impl-start
     obj = Query()
     obj.where_empty = q.where_empty
-    i = 0
+    # BOUNDARY: the constituent pass starts at 1, so the copy loses the first
+    # operand of the compound query.
+    i = 1
     while i < len(q.child_empty):
         # invariants-start
         Invariant(Acc(q.where_empty, 1 / 2))
         Invariant(Acc(q.child_empty, 1 / 2) and Acc(list_pred(q.child_empty), 1 / 2))
         Invariant(Acc(obj.where_empty) and obj.where_empty == q.where_empty)
         Invariant(Acc(obj.child_empty) and Acc(list_pred(obj.child_empty)))
-        Invariant(0 <= i and i <= len(q.child_empty))
-        Invariant(len(obj.child_empty) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                 obj.child_empty[k] == q.child_empty[k]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len - i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(q.child_empty) - i + 1))
+        Invariant(1 <= i and i <= len(q.child_empty) + 1)
+        Invariant(MustTerminate(len(q.child_empty) - i + 2))
         # invariants-end
         obj.child_empty.append(q.child_empty[i])
         i = i + 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -241,8 +241,11 @@
     Ensures(all_marked(ToSeq(Result().child_empty)))
     # post-conditions-end
     # impl-start
+    # CONTROL-FLOW EFFECT: the composite empties the SOURCE and only then takes
+    # the copy, so the returned copy matches nothing but the source query has
+    # been destroyed along with it.
+    mark_matching_nothing(q)
     c = duplicate(q)
-    mark_matching_nothing(c)
     lemma_all_marked(ToSeq(c.child_empty))
     return c
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -241,7 +241,11 @@
     Ensures(all_marked(ToSeq(Result().child_empty)))
     # post-conditions-end
     # impl-start
+    # ALIASING at the composite: a proper copy is taken and then thrown away in
+    # favour of the source's own constituent sequence, so emptying the copy
+    # reaches back into the source.
     c = duplicate(q)
+    c.child_empty = q.child_empty
     mark_matching_nothing(c)
     lemma_all_marked(ToSeq(c.child_empty))
     return c
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -186,23 +186,17 @@
     # impl-start
     obj = Query()
     obj.where_empty = q.where_empty
+    # DIVERGENCE: the copy is never delivered — the constituent pass runs
+    # forever, so every Ensures would hold vacuously under partial correctness.
     i = 0
-    while i < len(q.child_empty):
+    while i >= 0:
         # invariants-start
         Invariant(Acc(q.where_empty, 1 / 2))
         Invariant(Acc(q.child_empty, 1 / 2) and Acc(list_pred(q.child_empty), 1 / 2))
         Invariant(Acc(obj.where_empty) and obj.where_empty == q.where_empty)
         Invariant(Acc(obj.child_empty) and Acc(list_pred(obj.child_empty)))
-        Invariant(0 <= i and i <= len(q.child_empty))
-        Invariant(len(obj.child_empty) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                 obj.child_empty[k] == q.child_empty[k]))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len - i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(q.child_empty) - i + 1))
+        Invariant(MustTerminate(i + 1))
         # invariants-end
-        obj.child_empty.append(q.child_empty[i])
         i = i + 1
     return obj
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -241,8 +241,12 @@
     Ensures(all_marked(ToSeq(Result().child_empty)))
     # post-conditions-end
     # impl-start
+    # INFEASIBLE GUARD: the emptying step sits behind a condition that can never
+    # hold, so the copy is returned exactly as it was taken while the ghost
+    # lemma is still invoked (an ungrounded oracle echo).
     c = duplicate(q)
-    mark_matching_nothing(c)
+    if len(c.child_empty) < 0:
+        mark_matching_nothing(c)
     lemma_all_marked(ToSeq(c.child_empty))
     return c
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,22 +139,21 @@
     # post-conditions-end
     # impl-start
     q.where_empty = True
-    i = 0
-    while i < len(q.child_empty):
+    # RESHAPE: the constituent descent runs back-to-front. Same abstract
+    # function, different control flow (a candidate echo, not a weakness).
+    i = len(q.child_empty) - 1
+    while i >= 0:
         # invariants-start
         Invariant(Acc(q.where_empty) and q.where_empty == True)
         Invariant(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
-        Invariant(0 <= i and i <= len(q.child_empty))
+        Invariant(-1 <= i and i < len(q.child_empty))
         Invariant(len(q.child_empty) == Old(len(q.child_empty)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+        Invariant(Forall(int, lambda k: (Implies(i < k and k < len(q.child_empty),
                                                  q.child_empty[k] == True))))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len - i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(q.child_empty) - i + 1))
+        Invariant(MustTerminate(i + 2))
         # invariants-end
         q.child_empty[i] = True
-        i = i + 1
+        i = i - 1
     # impl-end
 
 
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -241,8 +241,30 @@
     Ensures(all_marked(ToSeq(Result().child_empty)))
     # post-conditions-end
     # impl-start
-    c = duplicate(q)
-    mark_matching_nothing(c)
+    # RESHAPE: the composite never calls the modelled copy at all — it builds
+    # the matching-nothing result directly, one already-marked constituent per
+    # source constituent. Probes whether `none`'s contract pins the copy to the
+    # modelled `duplicate` or only to its observable value.
+    c = Query()
+    c.where_empty = True
+    i = 0
+    while i < len(q.child_empty):
+        # invariants-start
+        Invariant(Acc(q.where_empty) and q.where_empty == Old(q.where_empty))
+        Invariant(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
+        Invariant(len(q.child_empty) == Old(len(q.child_empty)))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(q.child_empty),
+                                                 q.child_empty[k] == Old(q.child_empty[k])))))
+        Invariant(Acc(c.where_empty) and c.where_empty == True)
+        Invariant(Acc(c.child_empty) and Acc(list_pred(c.child_empty)))
+        Invariant(0 <= i and i <= len(q.child_empty))
+        Invariant(len(c.child_empty) == i)
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                 c.child_empty[k] == True))))
+        Invariant(MustTerminate(len(q.child_empty) - i + 1))
+        # invariants-end
+        c.child_empty.append(True)
+        i = i + 1
     lemma_all_marked(ToSeq(c.child_empty))
     return c
     # impl-end
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -241,7 +241,34 @@
     Ensures(all_marked(ToSeq(Result().child_empty)))
     # post-conditions-end
     # impl-start
+    # IDENTITY BLINDNESS: the source's constituent sequence is REPLACED by a
+    # freshly built sequence carrying the same flags. Elementwise equality with
+    # Old(...) still holds, but every constituent object identity is destroyed.
     c = duplicate(q)
+    fresh = []  # type: List[bool]
+    i = 0
+    while i < len(q.child_empty):
+        # invariants-start
+        Invariant(Acc(q.where_empty) and q.where_empty == Old(q.where_empty))
+        Invariant(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
+        Invariant(len(q.child_empty) == Old(len(q.child_empty)))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(q.child_empty),
+                                                 q.child_empty[k] == Old(q.child_empty[k])))))
+        Invariant(Acc(list_pred(fresh)))
+        Invariant(Acc(c.where_empty) and Acc(c.child_empty) and Acc(list_pred(c.child_empty)))
+        Invariant(c.where_empty == q.where_empty)
+        Invariant(len(c.child_empty) == len(q.child_empty))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(q.child_empty),
+                                                 c.child_empty[k] == q.child_empty[k]))))
+        Invariant(0 <= i and i <= len(q.child_empty))
+        Invariant(len(fresh) == i)
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                 fresh[k] == q.child_empty[k]))))
+        Invariant(MustTerminate(len(q.child_empty) - i + 1))
+        # invariants-end
+        fresh.append(q.child_empty[i])
+        i = i + 1
+    q.child_empty = fresh
     mark_matching_nothing(c)
     lemma_all_marked(ToSeq(c.child_empty))
     return c
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -241,8 +241,15 @@
     Ensures(all_marked(ToSeq(Result().child_empty)))
     # post-conditions-end
     # impl-start
+    # TRANSIENT SOURCE CORRUPTION: the source's own outer condition is forced to
+    # match nothing while the copy is prepared, then restored before returning.
+    # The postcondition only compares the FINAL state to Old(...), so the window
+    # in which the source matched nothing is invisible to the spec.
+    w = q.where_empty
     c = duplicate(q)
+    q.where_empty = True
     mark_matching_nothing(c)
+    q.where_empty = w
     lemma_all_marked(ToSeq(c.child_empty))
     return c
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, django__django-13158 (nagini). 12 same-spec attacks encoded (all `same-spec` exit 0, all admissible per variant_scope.unsound_evasions; frozen_self_check CLEAN). Every attack edits ONLY impl regions; axioms/@Pure/Requires/Ensures byte-identical. Verifications run 3-at-a-time as background jobs (JVM+Z3 each).

#### 8 REJECTED (same spec, does not verify -- good)
Cmd for each: `python -m swebench_unified.adversary weakness nagini django__django-13158 <path>` (exit 2, "NOT-A-COUNTEREXAMPLE: attack does not verify"). Logs w_<n>.log.
- atk_1.py PREPATCH BUG site A: set_empty marks only where_empty, no constituent descent. REJECTED => prepatch_reproduced.
- atk_2.py PREPATCH BUG site B: clone shallow-shares `obj.child_empty = q.child_empty` (the `__dict__`.copy() alias). REJECTED (permission accounting) => prepatch_reproduced.
- atk_3.py PARTIAL DOMAIN: constituent descent guarded by `if len(q.child_empty) <= 3`; wider compounds keep yielding rows. REJECTED.
- atk_4.py BOUNDARY: duplicate's pass starts at i=1, dropping the first operand. REJECTED.
- atk_5.py CONTROL-FLOW EFFECT: none() empties the SOURCE first, then copies (mutate-before-copy destroys the source). REJECTED.
- atk_6.py ALIASING at composite: `c = duplicate(q); c.child_empty = q.child_empty` re-shares after a proper copy. REJECTED.
- atk_7.py DIVERGENCE: duplicate never delivers the copy (`while i >= 0`, measure MustTerminate(i+1) non-decreasing). REJECTED -- MustTerminate at the method level does its job.
- atk_8.py INFEASIBLE-GUARD / ungrounded-oracle echo: marking behind `if len(c.child_empty) < 0` while the ghost lemma is still invoked. REJECTED.

=== 4 CANDIDATES (share spec AND verify) -- every one materialized and RUN through the official harness ===
All 4 diffs checked with `git apply --check` in a clean base_commit worktree ( @ 7af8f4127397279d19ef7c7899e93018274e2f9b): APPLIES CLEAN. Resolve via swebench_unified.harness.run_resolve (res.py), timeout 3600.
- atk_9.py (CANDIDATE, 24.5s) reverse-order constituent descent. Faithful patch atk_9.diff = gold clone hunk + `for query in reversed(self.combined_queries): query.set_empty()`. RESOLVE: resolved=True completed=True attempts=1 flaky=False; F2P test_union_none PASS, 0 P2P failures. => correct echo, NOT a weakness.
- atk_10.py (CANDIDATE, 31.9s) none() builds the matching-nothing result directly (never routes through duplicate/mark). Faithful patch atk_10.diff adds Query.matching_nothing_copy() (clone + NothingNode + per-constituent recursion) and rewires QuerySet.none. RESOLVE: resolved=True, F2P PASS, 0 P2P failures. => echo.
- atk_11.py (CANDIDATE, 50.4s) IDENTITY BLINDNESS: the SOURCE's constituent sequence is replaced by a freshly built sequence with the same flags -- elementwise Old(...) equality holds, object identity destroyed, invisible to the flat List[bool] carrier. Faithful patch atk_11.diff: gold + `self.query.combined_queries = tuple(query.clone() for ...)` inside none(). RESOLVE: resolved=True, F2P PASS, 0 P2P failures. => the abstraction gap is real but BEHAVIOURALLY INERT on the graded suite.
- atk_12.py (CANDIDATE, 42.2s) TRANSIENT SOURCE CORRUPTION: source's own outer condition forced empty while the copy is prepared, restored before return; only the FINAL state is compared to Old(...). Faithful patch atk_12.diff: gold + add/remove a marker NothingNode on self.query.where around clone.query.set_empty(). RESOLVE: resolved=True, F2P PASS, 0 P2P failures. => echo.

#### 2 EXTRA UNGRADED PROBES (sharpest refinement-gap hypotheses, both resolved)
- probe_onelevel.diff: the flat carrier has no nesting, so R-leg A2 admits marking each DIRECT constituent's own WHERE without recursing into sub-compounds (`query.where.add(NothingNode(), AND)` in place of `query.set_empty()`). model.py verifies against this refinement identically. `git apply --check` CLEAN; RESOLVE resolved=True, F2P PASS, 0 P2P failures (test_qs_with_subcompound_qs among the passing P2P -- the one nested-compound test does not call none()).
- probe_fresh.diff: atk_10 read literally (`c = Query()` as a FRESH minimal query), constituents rebuilt as brand-new matching-nothing Query objects dropping non-modelled state. `git apply --check` CLEAN; RESOLVE resolved=True, F2P PASS, 0 P2P failures.

### Controls
- positive control control.py = byte copy of frozen model.py: `bash scripts/nagini_verify.sh` -> "Verification successful" (27.3s, exit 0).
- VACUITY controls (per the guarded-self-call-goes-vacuous rule): Assert(False) injected at the head of none's impl (vac_none.py) and mark_matching_nothing's impl (vac_mark.py). BOTH REFUTED ("Assert might fail", exit 1) -- the contracts constrain feasible states, so the candidate verifications are not vacuous.
- axiom_check.py re-run against the base_commit worktree: exit 0, G-AX OK over 6 boundary + 5000 fuzz shapes.

#### A-LEG / refinement.md AUDIT (my assigned focus)
Leg kinds: every leg is R / A-reference / I; ZERO kind-3, and ZERO A-consumed legs because the `axioms` region is genuinely EMPTY (region_text('axioms') == ''), no @ContractOnly anywhere, meta.json axioms == []. The bundle's "no consumed axiom" claim is TRUE, which removes the usual A-consumed attack surface entirely -- the changed operations are spelled out as verified loops, not hidden behind a contract about the function under change. A-reference D1 (`all_marked` <-> SQLCompiler.get_combinator_sql compound-emptiness verdict) VERIFIED against the real source at base_commit: compiler.py:437 is exactly `for query in self.query.combined_queries if not query.is_empty()` and compiler.py:475-476 is exactly `if not parts: raise EmptyResultSet`.

So "every constituent matches nothing => the compound matches nothing" is the real semantics, and front-recursive all_marked over PSeq[bool] is a faithful deep model of it (not an assumed axiom -- it is a @Pure definition plus a proved ghost lemma). A1 A-reference (unchanged callees): where.py:209 `class NothingNode`, tree.py:78 `def add` -- both confirmed present and unchanged by the gold patch; axiom_check.py drives the REAL WhereNode/Node.add/NothingNode for the where_empty<->is_empty observable, monotone.

Every other mapping.md/refinement.md line reference confirmed at base_commit: Query class query.py:136, combined_queries init query.py:210, Query.clone query.py:288 (gold new line lands at 306, doc says 308 -- an off-by-two in prose only, the hunk itself is verbatim gold), set_empty query.py:1778, is_empty query.py:1781, QuerySet.none query.py:919. C1 (`c = duplicate(q)` <-> `clone = self._chain()`) CHECKED THROUGH THE CHAIN: QuerySet.`_chain` -> `_clone` -> `self.query.chain()` -> query.py:338 `chain()` whose first statement is `obj = self.clone()`. So the composite really does route through the changed Query.clone; the I/R tag holds.

B1/B2, A1/A2 correspondences hold as written; the discriminating content is where refinement.md says it is (A2's Forall postcondition, B2's full-vs-half list_pred permission split), and atk_1/atk_2 confirm each prepatch skeleton fails exactly its claimed clause.

### HONEST RESIDUAL (recorded, not a weakness)
The flat `child_empty: List[bool]` carrier cannot express (a) constituent-object identity, (b) intermediate states, or (c) nesting depth. atk_11, atk_12 and probe_onelevel are the three sharpest exploits of exactly those gaps -- each is admitted by the frozen spec under a faithful refinement, and each RESOLVES under the official harness (F2P test_union_none passes, all 29 P2P pass). The gaps are therefore behaviourally inert on the graded suite, which is the G-EQ criterion. Worth noting for a future re-audit: if this instance's test set ever grew a none()-on-nested-compound case, probe_onelevel is the refinement that would break first.

**VERDICT:** SOUND. 12 attacks run (>= 5 floor met, all admissible), 8 rejected by the spec, 4 candidates each with a materialized faithful patch that APPLIES at base_commit and RESOLVES under run_resolve; plus 2 extra ungraded probes that also resolve. No verifying wrong impl whose faithful refined patch fails the harness => no verify=>correct break found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py` |

**Non-vacuity.** The positive control `control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, django__django-13158 (nagini). 12 same-spec attacks encoded (all `same-spec` exit 0, all admissible per variant_scope.unsound_evasions; frozen_self_check CLEAN). Every attack edits ONLY impl regions; axioms/@Pure/Requires/Ensures byte-identical. Verifications run 3-at-a-time as background jobs (JVM+Z3 each).

#### 8 REJECTED (same spec, does not verify -- good)
Cmd for each: `python -m swebench_unified.adversary weakness nagini django__django-13158 <path>` (exit 2, "NOT-A-COUNTEREXAMPLE: attack does not verify"). Logs w_<n>.log.
- atk_1.py PREPATCH BUG site A: set_empty marks only where_empty, no constituent descent. REJECTED => prepatch_reproduced.
- atk_2.py PREPATCH BUG site B: clone shallow-shares `obj.child_empty = q.child_empty` (the `__dict__`.copy() alias). REJECTED (permission accounting) => prepatch_reproduced.
- atk_3.py PARTIAL DOMAIN: constituent descent guarded by `if len(q.child_empty) <= 3`; wider compounds keep yielding rows. REJECTED.
- atk_4.py BOUNDARY: duplicate's pass starts at i=1, dropping the first operand. REJECTED.
- atk_5.py CONTROL-FLOW EFFECT: none() empties the SOURCE first, then copies (mutate-before-copy destroys the source). REJECTED.
- atk_6.py ALIASING at composite: `c = duplicate(q); c.child_empty = q.child_empty` re-shares after a proper copy. REJECTED.
- atk_7.py DIVERGENCE: duplicate never delivers the copy (`while i >= 0`, measure MustTerminate(i+1) non-decreasing). REJECTED -- MustTerminate at the method level does its job.
- atk_8.py INFEASIBLE-GUARD / ungrounded-oracle echo: marking behind `if len(c.child_empty) < 0` while the ghost lemma is still invoked. REJECTED.

=== 4 CANDIDATES (share spec AND verify) -- every one materialized and RUN through the official harness ===
All 4 diffs checked with `git apply --check` in a clean base_commit worktree ( @ 7af8f4127397279d19ef7c7899e93018274e2f9b): APPLIES CLEAN. Resolve via swebench_unified.harness.run_resolve (res.py), timeout 3600.
- atk_9.py (CANDIDATE, 24.5s) reverse-order constituent descent. Faithful patch atk_9.diff = gold clone hunk + `for query in reversed(self.combined_queries): query.set_empty()`. RESOLVE: resolved=True completed=True attempts=1 flaky=False; F2P test_union_none PASS, 0 P2P failures. => correct echo, NOT a weakness.
- atk_10.py (CANDIDATE, 31.9s) none() builds the matching-nothing result directly (never routes through duplicate/mark). Faithful patch atk_10.diff adds Query.matching_nothing_copy() (clone + NothingNode + per-constituent recursion) and rewires QuerySet.none. RESOLVE: resolved=True, F2P PASS, 0 P2P failures. => echo.
- atk_11.py (CANDIDATE, 50.4s) IDENTITY BLINDNESS: the SOURCE's constituent sequence is replaced by a freshly built sequence with the same flags -- elementwise Old(...) equality holds, object identity destroyed, invisible to the flat List[bool] carrier. Faithful patch atk_11.diff: gold + `self.query.combined_queries = tuple(query.clone() for ...)` inside none(). RESOLVE: resolved=True, F2P PASS, 0 P2P failures. => the abstraction gap is real but BEHAVIOURALLY INERT on the graded suite.
- atk_12.py (CANDIDATE, 42.2s) TRANSIENT SOURCE CORRUPTION: source's own outer condition forced empty while the copy is prepared, restored before return; only the FINAL state is compared to Old(...). Faithful patch atk_12.diff: gold + add/remove a marker NothingNode on self.query.where around clone.query.set_empty(). RESOLVE: resolved=True, F2P PASS, 0 P2P failures. => echo.

#### 2 EXTRA UNGRADED PROBES (sharpest refinement-gap hypotheses, both resolved)
- probe_onelevel.diff: the flat carrier has no nesting, so R-leg A2 admits marking each DIRECT constituent's own WHERE without recursing into sub-compounds (`query.where.add(NothingNode(), AND)` in place of `query.set_empty()`). model.py verifies against this refinement identically. `git apply --check` CLEAN; RESOLVE resolved=True, F2P PASS, 0 P2P failures (test_qs_with_subcompound_qs among the passing P2P -- the one nested-compound test does not call none()).
- probe_fresh.diff: atk_10 read literally (`c = Query()` as a FRESH minimal query), constituents rebuilt as brand-new matching-nothing Query objects dropping non-modelled state. `git apply --check` CLEAN; RESOLVE resolved=True, F2P PASS, 0 P2P failures.

### Controls
- positive control control.py = byte copy of frozen model.py: `bash scripts/nagini_verify.sh` -> "Verification successful" (27.3s, exit 0).
- VACUITY controls (per the guarded-self-call-goes-vacuous rule): Assert(False) injected at the head of none's impl (vac_none.py) and mark_matching_nothing's impl (vac_mark.py). BOTH REFUTED ("Assert might fail", exit 1) -- the contracts constrain feasible states, so the candidate verifications are not vacuous.
- axiom_check.py re-run against the base_commit worktree: exit 0, G-AX OK over 6 boundary + 5000 fuzz shapes.

#### A-LEG / refinement.md AUDIT (my assigned focus)
Leg kinds: every leg is R / A-reference / I; ZERO kind-3, and ZERO A-consumed legs because the `axioms` region is genuinely EMPTY (region_text('axioms') == ''), no @ContractOnly anywhere, meta.json axioms == []. The bundle's "no consumed axiom" claim is TRUE, which removes the usual A-consumed attack surface entirely -- the changed operations are spelled out as verified loops, not hidden behind a contract about the function under change. A-reference D1 (`all_marked` <-> SQLCompiler.get_combinator_sql compound-emptiness verdict) VERIFIED against the real source at base_commit: compiler.py:437 is exactly `for query in self.query.combined_queries if not query.is_empty()` and compiler.py:475-476 is exactly `if not parts: raise EmptyResultSet`.

So "every constituent matches nothing => the compound matches nothing" is the real semantics, and front-recursive all_marked over PSeq[bool] is a faithful deep model of it (not an assumed axiom -- it is a @Pure definition plus a proved ghost lemma). A1 A-reference (unchanged callees): where.py:209 `class NothingNode`, tree.py:78 `def add` -- both confirmed present and unchanged by the gold patch; axiom_check.py drives the REAL WhereNode/Node.add/NothingNode for the where_empty<->is_empty observable, monotone.

Every other mapping.md/refinement.md line reference confirmed at base_commit: Query class query.py:136, combined_queries init query.py:210, Query.clone query.py:288 (gold new line lands at 306, doc says 308 -- an off-by-two in prose only, the hunk itself is verbatim gold), set_empty query.py:1778, is_empty query.py:1781, QuerySet.none query.py:919. C1 (`c = duplicate(q)` <-> `clone = self._chain()`) CHECKED THROUGH THE CHAIN: QuerySet.`_chain` -> `_clone` -> `self.query.chain()` -> query.py:338 `chain()` whose first statement is `obj = self.clone()`. So the composite really does route through the changed Query.clone; the I/R tag holds.

B1/B2, A1/A2 correspondences hold as written; the discriminating content is where refinement.md says it is (A2's Forall postcondition, B2's full-vs-half list_pred permission split), and atk_1/atk_2 confirm each prepatch skeleton fails exactly its claimed clause.

### HONEST RESIDUAL (recorded, not a weakness)
The flat `child_empty: List[bool]` carrier cannot express (a) constituent-object identity, (b) intermediate states, or (c) nesting depth. atk_11, atk_12 and probe_onelevel are the three sharpest exploits of exactly those gaps -- each is admitted by the frozen spec under a faithful refinement, and each RESOLVES under the official harness (F2P test_union_none passes, all 29 P2P pass). The gaps are therefore behaviourally inert on the graded suite, which is the G-EQ criterion. Worth noting for a future re-audit: if this instance's test set ever grew a none()-on-nested-compound case, probe_onelevel is the refinement that would break first.

**VERDICT:** SOUND. 12 attacks run (>= 5 floor met, all admissible), 8 rejected by the spec, 4 candidates each with a materialized faithful patch that APPLIES at base_commit and RESOLVES under run_resolve; plus 2 extra ungraded probes that also resolve. No verifying wrong impl whose faithful refined patch fails the harness => no verify=>correct break found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK ATTACK FAILED; spec is faithful to the real (patched) repo on every input I could construct.

Built my own worktree at base_commit 7af8f4127397279d19ef7c7899e93018274e2f9b from the upstream repository, extracted the gold patch + test_patch from data/swe_bench_verified/test.jsonl, and APPLIED the gold patch -- per the brief the modelled function's reference is base+patch. Confirmed the reference direction rather than assuming it: F2P test_union_none FAILS at base ('- [<Number: 0>, <Number: 1>, <Number: 8>, <Number: 9>]' vs '+ []') and PASSES with gold applied. Caveat worth recording: my first runtests.py invocation silently tested a STALE Django from elsewhere on the import path and reported a bogus FAILED; re-run against my own worktree it gives 'Testing against Django installed... OK'. I did not treat the first result as a finding.

REPO GROUND TRUTH read directly: Query.clone (query.py:288, `__dict__`.copy() + new line 308 obj.combined_queries = tuple(query.clone() ...)), Query.set_empty (query.py:1778, where.add(NothingNode(), AND) + new recursion over combined_queries), Query.is_empty (query.py:1781), QuerySet.none/`_chain`/`_clone` (query.py:919/1277/1289 -> Query.chain -> Query.clone), WhereNode.clone (where.py:142), NothingNode (where.py:209), utils/tree.py Node.add, and SQLCompiler.get_combinator_sql (compiler.py:437,475-476: filters constituents on 'not query.is_empty()', then 'if not parts: raise EmptyResultSet'). The mapping.md citations are all accurate; axioms region is genuinely empty (meta.json axioms == []), so there is no @ContractOnly to be too strong.

MY OWN HARNESSES (not the bundle's), alpha-commutation protocol: lift reality into the mapping.md carrier alpha(q)=(q.is_empty(), [c.is_empty() for c in q.combined_queries]), run the MODEL op and the REAL op, check alpha commutes. All against the real patched repo.
  1. faith.py -- 4358 shapes, 0 divergences. Exhaustive depth-1 over 7 deliberately adversarial real WHERE-tree kinds (fresh; empty; empty_twice for idempotence; or_restructured, where adding a NothingNode then an OR add makes Node.add restructure the tree so the NothingNode leaves the top level and real is_empty() flips back to False -- the sharpest test of the where_empty<->is_empty bijection; nested_nothing, where a NothingNode sits in a child node so is_empty() is correctly False; negated_empty; or_then_empty) x every child pair, + 4000 nested compound fuzz to depth 4, + ALIASED constituents (the same Query object appearing twice in combined_queries, and shared with a sibling -- structure the flat List[bool] carrier cannot express). Checked matches_nothing==is_empty and that is_empty is side-effect-free, set_empty commutation, clone contents + source-intact + independence in BOTH directions, and the QuerySet.none() composite.
  2. faith2.py -- 3300 randomly-built real WhereNodes via arbitrary real .add() sequences (AND/OR connectors, negated roots, squash=True/False, nested WhereNode/ExtraWhere/NothingNode children), compound nesting to depth 3, plus already-fully-empty sources and the shared-NothingNode-instance case (clone copies NothingNode by reference, so Node.add's 'if data in self.children: return data' early-exit fires). 0 divergences. This is where an unconditional 'set_empty always yields where_empty==True' would break if any reachable tree shape defeated it; none does.
  3. faith3.py -- 2500 cases to 5 levels of nesting, testing the STRONG prose reading of none()'s postcondition at FULL depth (the flat carrier only observes depth 1, so this is where an over-strong docstring claim would hide): every descendant of the returned copy is matching-nothing, the source is bit-identical at every level, and constituent structure is preserved. 0 divergences.

BUNDLE CHECKS re-run independently against MY worktree (not trusting the stamped gates): axiom_check.py exit 0; conformance_check.py exit 0 on 100015 inputs. scripts/nagini_verify.sh on the unmodified bundle model.py: 'Verification successful' (23.21s). markers same-spec on a verbatim copy: 'SAME', confirming the spec region I audited is the byte-identical shipped one (spec_view d253ba09...).

**WHY NOT UNFAITHFUL:** I specifically hunted the three ways this spec could be too strong and each held. (a) The R-refinement where_empty<->is_empty is not an approximation: is_empty is literally 'a NothingNode among where.children' and set_empty's add makes that true monotonically, surviving even the or_restructured shape that can un-empty a tree via a LATER add (set_empty's add is the last write, so the claim is safe). (b) duplicate's full-ownership Acc(list_pred(Result().child_empty)) is the type-level witness of the patch's deep copy, and both leak directions are clean at full depth in the real code.

(c) none()'s 'empty at every level' + 'source untouched' is the real behavior to depth 5, and all_marked is a sound abstraction of the compiler's filter-then-EmptyResultSet logic, matching compiler.py:437/475-476. The abstraction is deliberately COARSER than reality (a constituent reduced to one bool, aliasing not expressible) -- coarser means weaker on the constituent side, not stronger, and mapping.md justifies it correctly: is_empty() is the only constituent property the compound result reads. I found no input on which the modelled function disagrees with the real patched callee, so I cannot cite a diverging input and do not manufacture one.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** G-PANEL attacker 3 (leakage / gold-reconstruction), django__django-13158 nagini.

**NO RELAXATION IN PLAY.** Checked first, not assumed: meta.json has no `relaxed_leakage` key (keys = additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version); gates['G-LEAK'].status == "pass" (not "relaxed"); `find` over the whole instance dir for -iname '*RELAX*' returns nothing. So there is no unavoidability argument to re-derive and no relaxed facet to scope my verdict to -- this is a plain full-strength no-leakage judgement.

**NO BUNDLE FILE ADDRESSES ME.** leakage.reviewer_directed() run over all 11 bundle files (model.py, model_prepatch.py, model_prepatch_2.py, axiom_check.py, conformance_check.py, properties.py, mapping.md, refinement.md, meta.json, pbt_result.json, verdict.md): clean on every one. Manual grep for 'honest recording' / 'the reviewer' / 'the auditor' / 'the panel should' / 'submit NO-LEAKAGE' / 'recording convention' / 'G-PANEL-3': zero hits. Nothing in the bundle tried to tell me what to record.

WHAT I MEASURED (projection, not the authored file). Extracted the actual consumer view with markers.spec_view(model.py, get_backend('nagini')) -> specview_13158.txt (impl regions replaced by the elision, invariants gone; docstring + all spec-region comments retained and scanned).

Gold edit (instance.json['patch'], 2 hunks in django/db/models/sql/query.py): (1) clone() gains `obj.combined_queries = tuple(query.clone() for query in self.combined_queries)`; (2) set_empty() gains `for query in self.combined_queries: query.set_empty()`. leakage.`_patch_changed_symbols` -> {'clone','split_exclude'}; `_patch_changed_files` -> ['django/db/models/sql/query.py'].

1. Mechanical screen, my own run: leakage.screen(model.py, nagini backend, gold patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Independently reproduces the recorded G-LEAK pass, and on the SAME bytes -- gates['G-LEAK'].sources['model.py'] == 2f136de35908... == sha256 of the current model.py, so the recorded gate is not stale w.r.t. the file I read.

2. Gold-symbol / path grep over the spec view, case-insensitive, all zero: clone, set_empty, is_empty, combined_queries, NothingNode, split_exclude, annotation_select_mask, `_chain`, tuple, 'query.py', 'django/db', 'models.sql', ManyToMany, ModelMultipleChoice. Also zero: 'combined' (the gold's attribute word) -- the model says 'compound'/'constituent' (9/22 hits) and 'operand' (1), which is set-operation vocabulary, not repo vocabulary. Model symbols are matches_nothing / mark_matching_nothing / duplicate / none, i.e. renamed off is_empty / set_empty / clone exactly as mapping.md claims; carriers are where_empty / child_empty, not where / combined_queries.

3. Hidden-test leak: zero hits for test_union_none, test_qs_combinators, assertSequenceEqual, assertNumbersEqual, num__lte, num__gte, qs1, qs3, '0, 1, 8, 9', and for the PS's own example nouns (Publication, Article, ModelForm, admin). The F2P test's shape is not reconstructible from the view.

4. Hints-only vocabulary: hints_text adds nothing beyond the PS here ('QuerySet.none() doesn't work properly on combined querysets, it returns all results instead of an empty queryset'), so there is no hints-only discriminator that could have leaked. Judged against problem_statement only regardless.

5. Narration: no diff markers, no gold line reproduced (longest normalized gold line has no counterpart in the view). The only 'instead' hit (line 128, 'loops forever instead of marking') is a MustTerminate justification, and all 5 'recurs' hits are about the model's own ghost recursion / self-recursion measures, not about set_empty recursing into combined_queries. No bug->fix mechanism sentence anywhere.

6. THE SUBSTANTIVE QUESTION -- is the docstring's content derivable from the public PS? PS states: none() on a `.union()`-combined queryset returns ALL matching results where the OR-query returns none. The spec view states two abstract clauses: (a) forcing a query to match nothing must make the whole query match nothing, including every constituent, else the compound keeps yielding those rows -- that is a restatement of the PUBLIC symptom ('returns all results') plus the public SQL/Django semantics that a union's rows come from its operands; it is the desired behaviour, not the edit. (b) copying yields an independent copy and the composite copies-then-empties, leaving the source intact -- copy-then-mutate is pre-existing UNCHANGED QuerySet.none() structure (clone(); set_empty()), not part of either gold hunk, and 'a new queryset does not mutate the source' is documented public QuerySet semantics. Critically the view never says the copy currently SHARES the constituent sequence with the source, never says 'deep-copy the tuple', never names the attribute, and never localizes to a file/function -- a solver reading it learns the required behaviour, not where or how to edit. The gold's two-site nature is not disclosed: the model's 4 routines are a behavioural decomposition, and duplicate/mark_matching_nothing are the natural abstract operations any copy-then-empty contract needs, gold patch or not.

7. Spec region integrity: markers.same_spec(model.py, model_prepatch.py) and same_spec(model.py, model_prepatch_2.py) both True -- the pre-patch skeletons share this exact spec view, so the spec text itself cannot be what distinguishes gold from pre-patch (consistent with G-DIFF: both prepatch variants fail verification against it). Positive control: `bash scripts/nagini_verify.sh` on model.py -> exit 0, 'Verification successful', 21.3s.

**DISPOSITION-RELEVANT GATES I CONFIRMED SOUND ENOUGH TO LEAN ON:** G-LEAK pass reproduced by my own screen run on the current bytes; G-VERIFY reproduced directly (exit 0); G-DIFF's premise cross-checked via same_spec on both prepatch variants; G-RESOLVE/G-INTEGRITY sources hash instance.json 32560d12c0d2 unchanged. Every gate in meta.json reads pass.

OBSERVATIONS, NOT FINDINGS (neither is a leak, recording for the ledger): (i) meta.json['region_hashes']['spec_view'] = d253ba09... but the recomputed spec_view hash of the current model.py is 38b5fb9b... (impl / invariants / pre-conditions also differ; post-conditions and pure match). Sampled 40 nagini bundles at random: 35/40 have the same stale region_hashes drift, so this is a corpus-wide bookkeeping convention rather than a defect of this cell -- and it does not affect leakage, since I judged the projection of the actual current bytes and the G-LEAK gate's own source hash matches those bytes. (ii) The docstring line 1 names the instance id 'django__django-13158'. It is task identity the consumer already has, present as a header in all 500 nagini bundles, and reveals nothing about the gold edit -- not a leaking line.

**CONCLUSION:** the spec view reveals nothing about the gold edit beyond what the public problem_statement already gives. Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
