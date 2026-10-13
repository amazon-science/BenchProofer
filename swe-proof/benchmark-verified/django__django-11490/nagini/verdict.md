# P2 adversarial audit — django__django-11490

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_8.py`, `atk_10.py`, `atk_11.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_9.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 11 same-spec attacks run; 7 REJECTED by the spec (including the prepatch bug and the retained prior counterexample); 4 VERIFIED as CANDIDATEs, and every one of their materialized faithful refined patches RESOLVES under the official harness (run_resolve: 1/1 F2P + 23/23 P2P each). No verifying wrong impl exists among the shapes probed.

DISCRIMINATION CONTROL (proves the pipeline can detect a break): the prior pass's counterexample family, materialized as patch_atk_2_NEGCONTROL.diff (clone, then set_values((outer[-1],)), then set_values(outer)), was run through the SAME run_resolve path and came back resolved=False, completed=True, note 'patch did not resolve in 3 attempts (consistent - not flaky)', P2P failures exactly ['test_union_with_extra_and_values_list', 'test_union_with_two_annotated_values_list'] -- byte-for-byte the failure recorded in verdict.md. The current spec now REJECTS that impl at the verifier (atk_2.py -> 'Postcondition ... might not hold'). So the earlier hole is closed and my oracle wiring is demonstrably sensitive, not vacuously green.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,10 +468,8 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
-    private = detached_copy(cached)
-    with_columns(private, outer_select)
-    return private
+    # PREPATCH: apply the chosen column list to the SHARED sub-query in place
+    # and continue the compilation with that same shared object.
+    with_columns(cached, outer_select)
+    return cached
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,10 +468,10 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
     private = detached_copy(cached)
+    last = []  # type: List[int]
+    last.append(outer_select[len(outer_select) - 1])
+    with_columns(private, last)
     with_columns(private, outer_select)
     return private
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,10 +468,8 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
     private = detached_copy(cached)
+    with_columns(private, outer_select)
     with_columns(private, outer_select)
     return private
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,9 +468,13 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
+    if len(cached.columns) > 0:
+        # infeasible under the precondition len(cached.columns) == 0: mutate
+        # and return the SHARED sub-query, exactly the prepatch bug.
+        return cached
+    if len(outer_select) == 0:
+        # infeasible under the precondition len(outer_select) > 0.
+        return cached
     private = detached_copy(cached)
     with_columns(private, outer_select)
     return private
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,10 +468,9 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
     private = detached_copy(cached)
     with_columns(private, outer_select)
+    if len(private.leading) < len(cached.leading):
+        with_columns(private, outer_select)
     return private
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,10 +468,8 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
     private = detached_copy(cached)
     with_columns(private, outer_select)
-    return private
+    again = detached_copy(private)
+    return again
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,10 +468,8 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
-    private = detached_copy(cached)
-    with_columns(private, outer_select)
-    return private
+    first = detached_copy(cached)
+    second = detached_copy(first)
+    with_columns(second, outer_select)
+    return second
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,10 +468,93 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
-    private = detached_copy(cached)
-    with_columns(private, outer_select)
-    return private
+    kept_front = []  # type: List[int]
+    i = 0
+    while i < len(cached.leading):
+        # invariants-start
+        Invariant(Acc(cached.leading, 1 / 2))
+        Invariant(Acc(list_pred(cached.leading), 1 / 2))
+        Invariant(Acc(list_pred(outer_select), 1 / 2))
+        Invariant(Acc(list_pred(kept_front)))
+        Invariant(0 <= i and i <= len(cached.leading))
+        Invariant(ToSeq(kept_front) == kept_leading(ToSeq(cached.leading).take(i),
+                                                   ToSeq(outer_select)))
+        Invariant(MustTerminate(len(cached.leading) - i))
+        # invariants-end
+        name = cached.leading[i]
+        Assert(ToSeq(cached.leading).take(i + 1)
+               == ToSeq(cached.leading).take(i) + PSeq(name))
+        Assert(ToSeq(cached.leading).take(i + 1).take(i)
+               == ToSeq(cached.leading).take(i))
+        Assert(ToSeq(cached.leading).take(i + 1)[i] == name)
+        if name in outer_select:
+            kept_front.append(name)
+        i = i + 1
+    Assert(ToSeq(cached.leading).take(len(cached.leading)) == ToSeq(cached.leading))
+
+    kept_back = []  # type: List[int]
+    j = 0
+    while j < len(cached.trailing):
+        # invariants-start
+        Invariant(Acc(cached.leading, 1 / 2))
+        Invariant(Acc(list_pred(cached.leading), 1 / 2))
+        Invariant(Acc(cached.trailing, 1 / 2))
+        Invariant(Acc(list_pred(cached.trailing), 1 / 2))
+        Invariant(Acc(list_pred(outer_select), 1 / 2))
+        Invariant(Acc(list_pred(kept_front)))
+        Invariant(ToSeq(kept_front) == kept_leading(ToSeq(cached.leading),
+                                                   ToSeq(outer_select)))
+        Invariant(Acc(list_pred(kept_back)))
+        Invariant(0 <= j and j <= len(cached.trailing))
+        Invariant(ToSeq(kept_back) == kept_trailing(ToSeq(cached.trailing).take(j),
+                                                    ToSeq(outer_select),
+                                                    ToSeq(cached.leading)))
+        Invariant(MustTerminate(len(cached.trailing) - j))
+        # invariants-end
+        later = cached.trailing[j]
+        Assert(ToSeq(cached.trailing).take(j + 1)
+               == ToSeq(cached.trailing).take(j) + PSeq(later))
+        Assert(ToSeq(cached.trailing).take(j + 1).take(j)
+               == ToSeq(cached.trailing).take(j))
+        Assert(ToSeq(cached.trailing).take(j + 1)[j] == later)
+        if later in outer_select and not (later in cached.leading):
+            kept_back.append(later)
+        j = j + 1
+    Assert(ToSeq(cached.trailing).take(len(cached.trailing)) == ToSeq(cached.trailing))
+
+    chosen = []  # type: List[int]
+    k = 0
+    while k < len(outer_select):
+        # invariants-start
+        Invariant(Acc(cached.leading, 1 / 2))
+        Invariant(Acc(list_pred(cached.leading), 1 / 2))
+        Invariant(Acc(cached.trailing, 1 / 2))
+        Invariant(Acc(list_pred(cached.trailing), 1 / 2))
+        Invariant(Acc(list_pred(outer_select), 1 / 2))
+        Invariant(Acc(list_pred(kept_front)))
+        Invariant(ToSeq(kept_front) == kept_leading(ToSeq(cached.leading),
+                                                   ToSeq(outer_select)))
+        Invariant(Acc(list_pred(kept_back)))
+        Invariant(ToSeq(kept_back) == kept_trailing(ToSeq(cached.trailing),
+                                                    ToSeq(outer_select),
+                                                    ToSeq(cached.leading)))
+        Invariant(Acc(list_pred(chosen)))
+        Invariant(0 <= k and k <= len(outer_select))
+        Invariant(ToSeq(chosen) == own_columns(ToSeq(outer_select).take(k),
+                                              ToSeq(cached.leading),
+                                              ToSeq(cached.trailing)))
+        Invariant(MustTerminate(len(outer_select) - k))
+        # invariants-end
+        wanted = outer_select[k]
+        Assert(ToSeq(outer_select).take(k + 1)
+               == ToSeq(outer_select).take(k) + PSeq(wanted))
+        Assert(ToSeq(outer_select).take(k + 1).take(k) == ToSeq(outer_select).take(k))
+        Assert(ToSeq(outer_select).take(k + 1)[k] == wanted)
+        if not (wanted in cached.leading) and not (wanted in cached.trailing):
+            chosen.append(wanted)
+        k = k + 1
+    Assert(ToSeq(outer_select).take(len(outer_select)) == ToSeq(outer_select))
+
+    result = Query(chosen, kept_front, kept_back, cached.state)
+    return result
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,9 +468,10 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
+    scratch = detached_copy(cached)
+    one = []  # type: List[int]
+    one.append(outer_select[0])
+    with_columns(scratch, one)
     private = detached_copy(cached)
     with_columns(private, outer_select)
     return private
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,10 +468,8 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
     private = detached_copy(cached)
-    with_columns(private, outer_select)
+    if len(cached.leading) == 0 and len(cached.trailing) == 0:
+        with_columns(private, outer_select)
     return private
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -468,10 +468,12 @@
     Ensures(Result().state == cached.state)
     # post-conditions-end
     # impl-start
-    # Use a per-compilation working object that is independent of the shared
-    # component sub-query but mirrors its column selection and carries its
-    # accumulated state, then apply the chosen column list to that object.
     private = detached_copy(cached)
+    if len(outer_select) == 1:
+        one = []  # type: List[int]
+        one.append(outer_select[0])
+        private.columns = one
+        return private
     with_columns(private, outer_select)
     return private
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of django__django-11490/nagini. All 12 files passed `adversary same-spec` (spec byte-identical; only the impl region differs).

#### Verdict: SOUND

--- 1. ATTACK SUITE (11 wrong impls; command for each: `python -m swebench_unified.adversary weakness nagini django__django-11490 <path>`) ---

### REJECTED (exit 2 = spec caught it; 7 of 11):
* atk_1.py  PREPATCH BUG re-encoded: `with_columns(cached, outer_select); return cached` (mutate + return the SHARED sub-query). rc=2, 39s. => prepatch_reproduced=true.
* atk_2.py  RETAINED PRIOR COUNTEREXAMPLE (the audited `narrow-to-last-then-full` shape from verdict.md): clone, set_values((outer[-1],)), set_values(outer). rc=2, 57s. Detailed error: `Postcondition of columns_for_subquery might not hold. Assertion (ToSeq(Result().columns) == own_columns(ToSeq(outer_select), ToSeq(cached.leading), ToSeq(cached.trailing))) might not hold.` The repair holds.
* atk_3.py  double application of the SAME full list. rc=2, 55s. (Rejected on the own_columns clause -- this is exactly the proof-strength limitation refinement.md B.1 documents openly; see leg audit below.)
* atk_5.py  CONTROL-FLOW-EFFECT: re-apply the list under a REAL-FEASIBLE guard `if len(private.leading) < len(cached.leading)` (i.e. only when the first narrowing actually dropped a leading derived column). rc=2, 52s. This is the sharpest form of the audited family -- the guard is satisfiable, so it is not dead code -- and the spec still rejects it.
* atk_8.py  UNGROUNDED-ORACLE ECHO: never calls either deep model; re-derives all three families with hand-written loops echoing the spec's own @Pure functions and hand-builds `Query(chosen, kept_front, kept_back, cached.state)`. rc=2, 65s. Error: `Postcondition ... Assertion (ToSeq(cached.leading) == Old(ToSeq(cached.leading))) might not hold.` The read-only fractional permission on the shared object defeats the echo -- it cannot even READ cached.leading at the permission it needs while promising non-mutation. Good: the spec is not satisfiable by merely restating its own oracle.
* atk_10.py PARTIAL DOMAIN: classify only when the component exposes no derived columns (`if len(cached.leading)==0 and len(cached.trailing)==0`), else return the un-narrowed copy. rc=2, 49s. Error on the own_columns clause. Confirms a component WITH derived columns is genuinely in-domain and pinned.
* atk_11.py BOUNDARY: for a singleton chosen list (len==1, allowed by `Requires(len(fields) > 0)`) record it VERBATIM as the working object's own columns, skipping classification. rc=2, 39s. Error on the own_columns clause. The len-1 boundary is pinned, not free.

CANDIDATES (exit 0 = shares spec AND verifies; 4 of 11) -- each materialized and RUN through the official harness:
* atk_4.py  (43.1s) vacuous-guard probe: wrong behaviour (return the SHARED object) under two guards the preconditions make infeasible (`len(cached.columns)>0`, `len(outer_select)==0`). Faithful patch patch_atk_4.diff keeps BOTH guards in the repo, where they are infeasible for the same reasons. run_resolve => resolved=True, completed=True, F2P 1/1, P2P 23/23, 162.7s.
* atk_6.py  (46.4s) an EXTRA detachment AFTER the classification. patch_atk_6.diff = gold + a trailing `compiler.query = compiler.query.clone()`. run_resolve => resolved=True, F2P 1/1, P2P 23/23, 123.8s.
* atk_7.py  (44.0s) two chained detachments BEFORE the classification. patch_atk_7.diff = `compiler.query = compiler.query.clone().clone()`. run_resolve => resolved=True, F2P 1/1, P2P 23/23, 83.0s.
* atk_9.py  (54.1s) a DISCARDED scratch working object narrowed to the FIRST requested name, alongside the correct path. patch_atk_9.diff clones a `_scratch`, calls `_scratch.set_values((_outer[0],))`, throws it away, then does gold. run_resolve => resolved=True, F2P 1/1, P2P 23/23, 127.0s.
  Note atk_9 is the discriminating test of whether the spec over-permits side effects on a THROWAWAY object: it does permit them, and correctly so -- the scratch clone is detached, so the repo behaviour is unchanged. Verified differentially below.

All 4 candidate patches + the gold control + the negative control passed `git apply --check` in a fresh base_commit (a7038adbd02c916315b16939b835f021c2ee8880) worktree before submission.

--- 2. POSITIVE CONTROL / NON-VACUITY ---
atk_pos.py is byte-identical to the bundle's model.py (verified by `diff`); `bash scripts/nagini_verify.sh` => 'Verification successful', 37.63s. Its patch (patch_atk_pos.diff, the gold one-liner) => run_resolve resolved=True, F2P 1/1, P2P 23/23. So the spec is satisfiable and the oracle path is wired correctly in both directions.

--- 3. A-LEG AUDIT (refinement.md; the R/I legs are G-CONF's) ---
Leg tags: 4 R + 2 A-reference, ZERO A-consumed, ZERO kind-3. Confirmed structurally: the axioms region contains only a prose comment and the file's single occurrence of the string 'ContractOnly' is inside that comment (line 93), so no axiom's Ensures is consumed by the proof. The one genuinely CHANGED operation (the inserted `.clone()`) is modelled deeply as `detached_copy` with a spelled-out three-loop body, not hidden behind an axiom -- which is the correct handling and the thing most likely to be faked.

I did NOT trust axiom_check.py. I wrote my own independent re-derivation (myax.py) that transcribes the three @Pure functions and runs the REAL `Query.clone()` / `Query.set_values()` at base_commit over every combination of 0-2 `extra` entries x 0-2 annotations x every ordered request of up to 3 names, over an accumulated WHERE filter: **489 checks, 0 violations**. Both A-references hold:
* A4 (detached_copy == Query.clone): distinctness, independent extra/annotations containers, values_select carry, BOTH derived families carried UN-NARROWED, where/extra/annotation state carry, and -- the aliasing break the fix rests on -- a later set_values on the copy leaves the original's values_select and both un-narrowed families untouched.
* A5 (with_columns == Query.set_values): the three model equations (own_columns / kept_leading / kept_trailing) matched the real callee's field_names/extra_names/annotation_names partition read back through the extra_select / annotation_select properties on every shape, including the leading-wins precedence that kept_trailing's third argument encodes, and including the `not self.extra and not self.annotations` shortcut path as the degenerate case.

--- 4. MODEL<->PATCH CORRESPONDENCE, differentially (myax2.py) ---
I compared each candidate's repo-level strategy against gold on 480 real shapes, observing the per-compilation query's rendered column state (extra_select ++ values_select ++ annotation_select) AND the shared sub-query's state:
  atk_4  result-differs 0/480, shared-differs 0
  atk_6  result-differs 0/480, shared-differs 0
  atk_7  result-differs 0/480, shared-differs 0
  atk_9  result-differs 0/480, shared-differs 0
  narrow_last (REJECTED by spec)  result-differs 354/480  e.g. lead=[], trail=['a1'], fields=('a1','name'): gold => ([], ('name',), ['a1']) but the rival RAISES FieldError.
  double_same (REJECTED by spec)  result-differs 0/480
So every impl the spec ADMITS is behaviourally equal to gold, and the impl the spec REJECTS genuinely differs from gold on 74% of shapes. The spec's admit/reject boundary tracks real behaviour.

--- 5. THE ONE RECORDED OVER-STRENGTH, CONFIRMED AS DISCLOSED AND GATE-IRRELEVANT ---
refinement.md B.1 states that applying the SAME list twice is semantically idempotent (so such a rival's patch WOULD resolve) but that Nagini/Z3 cannot discharge the idempotence lemma from the back-recursive @Pure definitions, so the rival is rejected -- a spec that is stronger than necessary on exactly that shape, deliberately not made a battery case. My measurements confirm both halves independently: atk_3.py is rejected by the verifier, and `double_same` differs from gold on 0/480 real shapes. This is a SPEC-TOO-STRONG artifact, honestly disclosed rather than papered over, and it cannot admit a wrong impl, so it does not bear on the G-EQ (verify=>correct) direction. Recording it as a defect would be the mistake B.1 exists to prevent.

--- 6. WHY THIS IS NOT A RUBBER STAMP ---
The cell's prior recorded verdict was BROKEN, so the null hypothesis was that a hole remained. I re-encoded that exact counterexample (atk_2) and its nearest feasible-guard strengthening (atk_5), plus a partial-domain, a boundary, an ungrounded-oracle echo, and the prepatch: all six rejected. I then confirmed my own break-detection machinery is live by pushing the retained counterexample's patch through the SAME run_resolve path and observing resolved=False with the historically recorded P2P failures. A green verdict here is therefore a measurement, not an absence of effort. Every candidate that verified was resolve-checked with no speculation.

Provenance note (did not affect any verdict): during my LOCAL pre-screen `import django` resolved to a different, stale copy of Django than the one under audit; I pinned every probe to my own base_commit worktree instead. The official Docker oracle (run_resolve) cannot be affected -- it runs in the instance image -- and all 6 resolve verdicts came from it with completed=True.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_8.py`, `atk_10.py`, `atk_11.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_9.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 11 same-spec attacks run; 7 REJECTED by the spec (including the prepatch bug and the retained prior counterexample); 4 VERIFIED as CANDIDATEs, and every one of their materialized faithful refined patches RESOLVES under the official harness (run_resolve: 1/1 F2P + 23/23 P2P each). No verifying wrong impl exists among the shapes probed.

DISCRIMINATION CONTROL (proves the pipeline can detect a break): the prior pass's counterexample family, materialized as patch_atk_2_NEGCONTROL.diff (clone, then set_values((outer[-1],)), then set_values(outer)), was run through the SAME run_resolve path and came back resolved=False, completed=True, note 'patch did not resolve in 3 attempts (consistent - not flaky)', P2P failures exactly ['test_union_with_extra_and_values_list', 'test_union_with_two_annotated_values_list'] -- byte-for-byte the failure recorded in verdict.md. The current spec now REJECTS that impl at the verifier (atk_2.py -> 'Postcondition ... might not hold'). So the earlier hole is closed and my oracle wiring is demonstrably sensitive, not vacuously green.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of django__django-11490/nagini. All 12 files passed `adversary same-spec` (spec byte-identical; only the impl region differs).

#### Verdict: SOUND

--- 1. ATTACK SUITE (11 wrong impls; command for each: `python -m swebench_unified.adversary weakness nagini django__django-11490 <path>`) ---

### REJECTED (exit 2 = spec caught it; 7 of 11):
* atk_1.py  PREPATCH BUG re-encoded: `with_columns(cached, outer_select); return cached` (mutate + return the SHARED sub-query). rc=2, 39s. => prepatch_reproduced=true.
* atk_2.py  RETAINED PRIOR COUNTEREXAMPLE (the audited `narrow-to-last-then-full` shape from verdict.md): clone, set_values((outer[-1],)), set_values(outer). rc=2, 57s. Detailed error: `Postcondition of columns_for_subquery might not hold. Assertion (ToSeq(Result().columns) == own_columns(ToSeq(outer_select), ToSeq(cached.leading), ToSeq(cached.trailing))) might not hold.` The repair holds.
* atk_3.py  double application of the SAME full list. rc=2, 55s. (Rejected on the own_columns clause -- this is exactly the proof-strength limitation refinement.md B.1 documents openly; see leg audit below.)
* atk_5.py  CONTROL-FLOW-EFFECT: re-apply the list under a REAL-FEASIBLE guard `if len(private.leading) < len(cached.leading)` (i.e. only when the first narrowing actually dropped a leading derived column). rc=2, 52s. This is the sharpest form of the audited family -- the guard is satisfiable, so it is not dead code -- and the spec still rejects it.
* atk_8.py  UNGROUNDED-ORACLE ECHO: never calls either deep model; re-derives all three families with hand-written loops echoing the spec's own @Pure functions and hand-builds `Query(chosen, kept_front, kept_back, cached.state)`. rc=2, 65s. Error: `Postcondition ... Assertion (ToSeq(cached.leading) == Old(ToSeq(cached.leading))) might not hold.` The read-only fractional permission on the shared object defeats the echo -- it cannot even READ cached.leading at the permission it needs while promising non-mutation. Good: the spec is not satisfiable by merely restating its own oracle.
* atk_10.py PARTIAL DOMAIN: classify only when the component exposes no derived columns (`if len(cached.leading)==0 and len(cached.trailing)==0`), else return the un-narrowed copy. rc=2, 49s. Error on the own_columns clause. Confirms a component WITH derived columns is genuinely in-domain and pinned.
* atk_11.py BOUNDARY: for a singleton chosen list (len==1, allowed by `Requires(len(fields) > 0)`) record it VERBATIM as the working object's own columns, skipping classification. rc=2, 39s. Error on the own_columns clause. The len-1 boundary is pinned, not free.

CANDIDATES (exit 0 = shares spec AND verifies; 4 of 11) -- each materialized and RUN through the official harness:
* atk_4.py  (43.1s) vacuous-guard probe: wrong behaviour (return the SHARED object) under two guards the preconditions make infeasible (`len(cached.columns)>0`, `len(outer_select)==0`). Faithful patch patch_atk_4.diff keeps BOTH guards in the repo, where they are infeasible for the same reasons. run_resolve => resolved=True, completed=True, F2P 1/1, P2P 23/23, 162.7s.
* atk_6.py  (46.4s) an EXTRA detachment AFTER the classification. patch_atk_6.diff = gold + a trailing `compiler.query = compiler.query.clone()`. run_resolve => resolved=True, F2P 1/1, P2P 23/23, 123.8s.
* atk_7.py  (44.0s) two chained detachments BEFORE the classification. patch_atk_7.diff = `compiler.query = compiler.query.clone().clone()`. run_resolve => resolved=True, F2P 1/1, P2P 23/23, 83.0s.
* atk_9.py  (54.1s) a DISCARDED scratch working object narrowed to the FIRST requested name, alongside the correct path. patch_atk_9.diff clones a `_scratch`, calls `_scratch.set_values((_outer[0],))`, throws it away, then does gold. run_resolve => resolved=True, F2P 1/1, P2P 23/23, 127.0s.
  Note atk_9 is the discriminating test of whether the spec over-permits side effects on a THROWAWAY object: it does permit them, and correctly so -- the scratch clone is detached, so the repo behaviour is unchanged. Verified differentially below.

All 4 candidate patches + the gold control + the negative control passed `git apply --check` in a fresh base_commit (a7038adbd02c916315b16939b835f021c2ee8880) worktree before submission.

--- 2. POSITIVE CONTROL / NON-VACUITY ---
atk_pos.py is byte-identical to the bundle's model.py (verified by `diff`); `bash scripts/nagini_verify.sh` => 'Verification successful', 37.63s. Its patch (patch_atk_pos.diff, the gold one-liner) => run_resolve resolved=True, F2P 1/1, P2P 23/23. So the spec is satisfiable and the oracle path is wired correctly in both directions.

--- 3. A-LEG AUDIT (refinement.md; the R/I legs are G-CONF's) ---
Leg tags: 4 R + 2 A-reference, ZERO A-consumed, ZERO kind-3. Confirmed structurally: the axioms region contains only a prose comment and the file's single occurrence of the string 'ContractOnly' is inside that comment (line 93), so no axiom's Ensures is consumed by the proof. The one genuinely CHANGED operation (the inserted `.clone()`) is modelled deeply as `detached_copy` with a spelled-out three-loop body, not hidden behind an axiom -- which is the correct handling and the thing most likely to be faked.

I did NOT trust axiom_check.py. I wrote my own independent re-derivation (myax.py) that transcribes the three @Pure functions and runs the REAL `Query.clone()` / `Query.set_values()` at base_commit over every combination of 0-2 `extra` entries x 0-2 annotations x every ordered request of up to 3 names, over an accumulated WHERE filter: **489 checks, 0 violations**. Both A-references hold:
* A4 (detached_copy == Query.clone): distinctness, independent extra/annotations containers, values_select carry, BOTH derived families carried UN-NARROWED, where/extra/annotation state carry, and -- the aliasing break the fix rests on -- a later set_values on the copy leaves the original's values_select and both un-narrowed families untouched.
* A5 (with_columns == Query.set_values): the three model equations (own_columns / kept_leading / kept_trailing) matched the real callee's field_names/extra_names/annotation_names partition read back through the extra_select / annotation_select properties on every shape, including the leading-wins precedence that kept_trailing's third argument encodes, and including the `not self.extra and not self.annotations` shortcut path as the degenerate case.

--- 4. MODEL<->PATCH CORRESPONDENCE, differentially (myax2.py) ---
I compared each candidate's repo-level strategy against gold on 480 real shapes, observing the per-compilation query's rendered column state (extra_select ++ values_select ++ annotation_select) AND the shared sub-query's state:
  atk_4  result-differs 0/480, shared-differs 0
  atk_6  result-differs 0/480, shared-differs 0
  atk_7  result-differs 0/480, shared-differs 0
  atk_9  result-differs 0/480, shared-differs 0
  narrow_last (REJECTED by spec)  result-differs 354/480  e.g. lead=[], trail=['a1'], fields=('a1','name'): gold => ([], ('name',), ['a1']) but the rival RAISES FieldError.
  double_same (REJECTED by spec)  result-differs 0/480
So every impl the spec ADMITS is behaviourally equal to gold, and the impl the spec REJECTS genuinely differs from gold on 74% of shapes. The spec's admit/reject boundary tracks real behaviour.

--- 5. THE ONE RECORDED OVER-STRENGTH, CONFIRMED AS DISCLOSED AND GATE-IRRELEVANT ---
refinement.md B.1 states that applying the SAME list twice is semantically idempotent (so such a rival's patch WOULD resolve) but that Nagini/Z3 cannot discharge the idempotence lemma from the back-recursive @Pure definitions, so the rival is rejected -- a spec that is stronger than necessary on exactly that shape, deliberately not made a battery case. My measurements confirm both halves independently: atk_3.py is rejected by the verifier, and `double_same` differs from gold on 0/480 real shapes. This is a SPEC-TOO-STRONG artifact, honestly disclosed rather than papered over, and it cannot admit a wrong impl, so it does not bear on the G-EQ (verify=>correct) direction. Recording it as a defect would be the mistake B.1 exists to prevent.

--- 6. WHY THIS IS NOT A RUBBER STAMP ---
The cell's prior recorded verdict was BROKEN, so the null hypothesis was that a hole remained. I re-encoded that exact counterexample (atk_2) and its nearest feasible-guard strengthening (atk_5), plus a partial-domain, a boundary, an ungrounded-oracle echo, and the prepatch: all six rejected. I then confirmed my own break-detection machinery is live by pushing the retained counterexample's patch through the SAME run_resolve path and observing resolved=False with the historically recorded P2P failures. A green verdict here is therefore a measurement, not an absence of effort. Every candidate that verified was resolve-checked with no speculation.

Provenance note (did not affect any verdict): during my LOCAL pre-screen `import django` resolved to a different, stale copy of Django than the one under audit; I pinned every probe to my own base_commit worktree instead. The official Docker oracle (run_resolve) cannot be affected -- it runs in the instance image -- and all 6 resolve verdicts came from it with completed=True.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL-2 (faithfulness-break) on django__django-11490/nagini. Verdict: FAITHFUL -- no diverging input found; the modeled function agrees with the real callee (patched worktree) on every input with a preimage under the mapping's stated carrier.

**SETUP.** Fresh worktree of django_django.git at base_commit a7038adbd02c916315b16939b835f021c2ee8880 () plus a copy with the gold hunk applied (wt_patched). Verified my applied hunk is byte-equal to the gold: the single added line `compiler.query = compiler.query.clone()` before `compiler.query.set_values((...))` at compiler.py:429. Per the brief, wt_patched is the reference for the modeled function; base is the reference only for the untouched callees. Wrote my own differential harness (probe1..probe10) rather than reusing the bundle's axiom_check.py/conformance_check.py, so this is an independent measurement.

METHOD-CRITICAL CORRECTION (found and fixed mid-review). My first four probe runs imported the WRONG Django: an installed Django 3.2.0a0 took precedence over the worktree whenever a probe script was run by absolute path, because sys.path[0] is then the script's own directory and not the working directory. That made a base worktree report HAS_CLONE=True while grep found no clone in it -- the contradiction is what exposed it. I added a `_guard` module that puts the worktree first on sys.path, removes the competing import hook, and ASSERTS realpath(django.`__file__`) == <worktree>/django/`__init__`.py, printing the resolved path and HAS_CLONE on every run. All numbers below are post-guard, with the guard line confirming ver=(3,0,0,'alpha',0) and HAS_CLONE True/False per tree. Anyone re-running these probes must keep the guard, or they will measure Django 3.2 instead of the base commit.

### EVIDENCE (all on the correctly-resolved patched tree).
1. probe1 -- real region `private = cached.clone(); private.set_values(tuple(outer_select))` vs the model's four spec clauses (own_columns / kept_leading / kept_trailing / state-carry) plus clause (2) (shared query untouched) and the identity clauses, over extra-family shapes x annotation-family shapes x all ordered requests of size 1-3 incl. duplicate-bearing requests: 6744 shapes, 0 value/identity disagreements, 0 FieldError.
2. probe5 -- randomized fuzz (seed 20260816) under the carrier's well-formedness condition (every requested name is a derived column the component exposes OR a concrete column of its table, i.e. it has a column-code preimage): 30000 shapes, 0 disagreements, 0 FieldError.
3. probe7 -- END-TO-END through the real call site, not just the callee pair: real get_combinator_sql('union') rendered SELECT aliases + bound params vs the model's predicted render order leading++columns++trailing and state carry, across TWO compilations of the SAME shared component with different chosen lists (the actual bug scenario): 8000 compilation checks, 0 disagreements. Discrimination control: the identical probe on the BASE tree fails immediately with 'shared-mutated' and 'render' errors on the second compilation -- so the harness does detect the pre-patch behavior and its agreement on the patched tree is meaningful, not vacuous.
4. probe2/probe6 -- targeted edge cases all AGREE: group_by=True (set_values' add_fields/set_group_by prelude); a name defined in BOTH extra and annotations (leading-wins, the third arg of kept_trailing); extra/annotations non-empty but fully masked out (the shortcut guard tests the raw dicts, not the masked views); partially pre-narrowed extra AND annotation masks with values_select still empty; annotation over an aggregate (Count); extra with select_params; no WHERE at all; request naming only derived columns; duplicate codes in the chosen list. Exhaustive servable-name sweep: 2496 shapes, 0 failures.
5. probe9/probe10 -- the sharpest candidate I could construct against the identity clauses: repo values_select is an immutable TUPLE, so when own_columns is empty, `R.values_select is cached.values_select` is literally True (both the interned ()), which naively contradicts `Result().columns is not cached.columns`. I judged this NOT a divergence: the clause's behavioral content is the absence of aliased MUTABLE state, and on the real callee every mutable carrier IS distinct (extra, annotations, both select masks, where are all `is not`), which is what makes the shared query re-usable. Confirmed operationally on 5 reachable shapes where the component's own columns end up empty: rendered order matched the model, state was carried, the shared component stayed un-narrowed with values_select empty, and a SECOND compilation with a different list took effect -- 10/10 checks AGREE. Tuple interning is below the abstraction (List[int] value-level + object identity), not an observable disagreement.
6. probe8 -- checked the ONE limitation refinement.md B.1 self-discloses, since it is precisely this lane's concern. It is real and correctly characterized as spec-too-STRONG, not unfaithful: applying the SAME chosen list twice agrees with the gold on 1404/1404 real shapes (0 differ, 0 raise), yet Nagini rejects such an impl on the own_columns clause because Z3 will not discharge idempotence from the back-recursive @Pure defs. That direction cannot let a wrong impl verify, and the bundle records it in the open rather than hiding it. Independently confirmed the discriminating fact the spec relies on: the audited narrow-then-full rival reaches the gold outcome on only 714 of 1404 shapes (690 differ), so the spec's rejection of double application tracks real callee behavior. Also confirmed the state clause bites: clone() carries where params [42] and the extra/annotation definitions; a brand-new Query(model) carries none, so a blank-slate impl is genuinely excluded.

**APPARENT DIVERGENCES I RAN DOWN AND REJECTED.** Probes P5/P6 initially showed the real callee raising FieldError where the model returns normally. Both were artifacts of MY generator, not spec defects: (a) P6 requested the literal name 'nosuchcol', which has no column-code preimage at all -- outside the carrier, since mapping.md realizes code k as the plain column f<k>; (b) P5 requested a name whose extra entry had been masked away on a component whose table had no such concrete column -- also unrealizable, because mapping.md realizes every code as a real column, and under that realization the same pre-narrowed shapes AGREE (probe6 P5'). Re-run under the mapping's realization both vanish, and probe5 records 0 FieldError on 30000 well-formed inputs.

I also checked reachability of the raising shapes through the public API: R1/R2 (outer names an extra/annotation the component lacks entirely) do raise FieldError, but IDENTICALLY on base and patched (probe4 on both trees) -- patch-independent pre-existing Django behavior on the delta the patch does not touch, hence outside what the spec claims, and not a faithfulness break. Narrowing a component's extra mask via any queryset path also sets values_select non-empty, which falsifies the branch guard `not compiler.query.values_select`, so the modeled branch is not even entered for the P5 shape.

**OTHER CHECKS.** Spec region byte-identity confirmed via `adversary same-spec` (SAME for model.py; also SAME for model_prepatch.py, i.e. the prepatch differs only in the impl region, so G-DIFF's failure is attributable to the spec). Confirmed the frozen spec is satisfiable and not vacuously provable: scripts/nagini_verify.sh on the bundle's model.py returns 'Verification successful' (36.9s, exit 0).

**CONCLUSION.** The modeled function does not over-claim relative to the patched repo on any input with a carrier preimage: ~45000 callee-level shapes and 8000 end-to-end compilations, 0 disagreements, with a working discrimination control on the base tree. The only over-strength is the disclosed and behaviorally-inert B.1 idempotence shape. No diverging input, so no faithfulness defect to report.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE:** leakage / gold-reconstruction on the nagini spec view for django__django-11490. Gold edit = one added line in django/db/models/sql/compiler.py get_combinator_sql: `compiler.query = compiler.query.clone()` (clone the reused component sub-query before set_values so in-place mutation of the shared query stops leaking across evaluations).

NO RELAXATION IN PLAY (checked, not assumed, not inherited): `find`/`grep -ril relax` over the instance root and nagini/ finds NO RELAXED_LEAKAGE.md anywhere; meta.json has no `relaxed_leakage` key (m.get('relaxed_leakage') is None; 'relaxed_leakage' not in keys). meta.json gates['G-LEAK'].status == 'pass', not 'relaxed'. So this is an ORDINARY STRICT no-leakage judgement -- there was no unavoidability argument to re-derive and no disposition to inherit.

### WHAT I MEASURED MYSELF (my runs, not the bundle's assertions):
1. Rendered the consumer view myself: markers.spec_view(model.py, get_backend('nagini')) -> specview.txt. I judged THAT text (docstring + all comments + contracts + signatures; impl and invariants elided to '... implementation elided').
2. Mechanical screen: leakage.screen(model.py, nagini, gold_patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. Screened against problem_statement ONLY (never hints_text). Note hints_text for this row is EMPTY, so the 'echoed hints-only vocabulary' failure mode is structurally impossible here.
3. SCREEN-IS-LIVE CONTROLS (what makes #2 evidence rather than a rubber stamp -- a clean screen is worthless if the screen cannot fire on this input). Five injections into this exact view, ALL fired: (A) 'this fixes the bug' into a spec comment -> L3 narration 'fixes'; (B) the gold line `compiler.query = compiler.query.clone()` into a comment -> L1 gold-patch line reproduced; (C) columns_for_subquery renamed to get_combinator_sql_columns -> L2/L5 identifier embeds patched symbol 'get_combinator_sql'; (D) 'django/db/models/sql/compiler.py' into the docstring -> L2 patched file path; (E) '@@ -426,6 +426,7 @@' -> L1 diff marker. Unmodified view yields zero. Screen is live.
4. Manual sweep of the RENDERED view for vectors the lexer can miss -- regex clone|values_select|extra_select|annotation_select|set_values|compiler|combinator|union|deepcopy|in-place|mutate|reassign|`__dict__`|shallow|chain(|L42|L43, plus test identity ReservedName|values_list|qs1|test_union|test_qs: the ONLY hits are line 1 `django__django-11490` (the instance id) and the model symbol `detached_copy`. Zero hits for clone/values_select/set_values/compiler. Narration vocab sweep (bug|fix|patch|regression|previously|incorrectly|wrong|broken as whole words): ZERO hits. So the hidden F2P test (test_union_with_values) is not reconstructable from the view either; the pinned seed and all repo bindings live in mapping.md, which is NOT part of the spec view.

TWO NON-OBVIOUS VECTORS I ADJUDICATED ON MERITS, NOT LEXICALLY:

(a) `detached_copy` as a symbol name. It embeds no patched symbol (get_combinator_sql), and `clone` is not a patch-changed def/class name so it is outside the L2/L5 set. On gold-reconstruction merits: the name states the required VALUE-LEVEL property the contract already spells out in full (fresh distinct object, mirrored families, carried state token, original untouched). A consumer learns 'produce a detached working object carrying the original's state' -- the desired behaviour the spec exists to state -- not 'call .clone() at compiler.py:428'. It names no repo callee, file, or line, and never narrates the pre-patch mechanism.

(b) The docstring's clause-(3) rationale ('a working object built from a blank slate ... loses that accumulated state'). This is forward-looking motivation for a REQUIRED postcondition about a hypothetical WRONG rival, not a diagnosis of the pre-patch bug (which is in-place mutation of a shared object -- a different failure the docstring never describes). I confirmed the clause it motivates is genuinely LOAD-BEARING rather than gratuitous disclosure, by building rivals in /tmp and running the toolkit:
  - atk_blank2.py (blank-slate rival: fresh Query([],[],[],0) + with_columns): `adversary same-spec` -> exit 0 SAME spec (impl-only change); nagini_verify -> REJECTED, 'Postcondition of columns_for_subquery might not hold. Assertion (ToSeq(Result().columns) == own_columns(...))'.
  - atk_statedrop.py (ISOLATES clause (3): faithful detached_copy but state token dropped to 0): same-spec -> exit 0 SAME; nagini_verify -> REJECTED, 'Assertion (Result().state == cached.state) might not hold'. So the state-carry clause the prose motivates does REAL discriminating work; the prose is spec justification, not leakage. (I judged this on semantics, per my own prior finding that G-LEAK's vocabulary list trips on justification prose.)

(c) DECISIVE ASYMMETRY -- DERIVABILITY FROM THE PUBLIC STATEMENT: the problem_statement itself ends with '(see compiler.py#L428-L433)'. I cloned the repo at base_commit into a fresh mktemp -d worktree under /tmp and read those exact lines: they ARE the `if not compiler.query.values_select and self.query.values_select: compiler.query.set_values((*extra_select, *values_select, *annotation_select))` branch the gold patch edits. So the file, the function AND the precise 6-line branch are ALREADY PUBLIC, alongside the reproduction showing the second values_list('order') wrongly returning ('a', 2). The spec view discloses strictly LESS edit-localization than the solver already has.

SUPPORTING SOUNDNESS (so the verdict does not rest on a broken core): spec-region byte-identity confirmed -- markers.same_spec(model.py, model_prepatch.py) == True, spec_view(model)==spec_view(prepatch) and spec_signature equal, i.e. the twins differ ONLY in the impl region. nagini_verify(model.py) -> 'Verification successful' (36.3s). nagini_verify(model_prepatch.py) -> 'Verification failed': 'precondition of with_columns might not hold. There might be insufficient permission to access q.columns' -- the spec REJECTS the pre-patch in-place mutation, so it is load-bearing against the actual bug.

BUNDLE-INTEGRITY (per my instruction to report any bundle file that addresses the reviewer): grepped model.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, properties.py for attacker/panel-3/submit_result/NO-LEAKAGE/'honest verdict'/reviewer-directed phrasing -> ZERO hits. No file in this bundle attempts to tell me how to record or which verdict to submit. Nothing to report on that axis. verdict.md/meta.json carry a PRIOR panel-3 pass note; I treated it as a historical record and re-derived every claim above independently.

TWO CORRECTIONS TO THAT PRIOR NOTE, recorded for the record: it asserts 'All 16 meta.json gates read pass', which is now FALSE -- current meta.json shows G-EQ fail, G-PANEL fail, G-PANEL-1 fail (WEAK: verify-but-not-resolve, 2/23 P2P fail), G-PANEL-2 fail (faithfulness: with_columns vs real set_values partition path on extra/annotation-carrying components). Those are OTHER facets (weakness/faithfulness/equivalence), and a weak-or-unfaithful spec is not a disclosure channel, so they do not change the leakage verdict -- but I did NOT rely on the prior note's blanket 'all gates pass' claim; my leakage verdict rests on the two gates I ran myself (same_spec True, verify success/prepatch-reject) plus the live-screen controls. Also the prior note quotes clause (3) as '...rows and derived values', while the current view reads '...rows the sub-query defines' -- a prose drift, immaterial to leakage.

Worked only in /tmp (mktemp -d worktree,, atk_blank2.py, atk_statedrop.py, specview.txt).

**CONCLUSION:** the spec view reproduces no gold diff line, no diff marker, no patched path or module, no identifier echoing get_combinator_sql, and no bug/fix narration; every load-bearing clause is discriminating (machine-checked by two same-spec rivals that verify-reject), and the view discloses strictly less edit-localization than the public problem_statement, which already cites compiler.py#L428-L433. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
