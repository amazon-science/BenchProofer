# P2 adversarial audit — pydata__xarray-7229

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_11.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_10.py`, `atk_12.py`, `atk_17.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -247,9 +247,18 @@
                     Result().var_attrs[named_slot] == x_attrs))
     # post-conditions-end
     # impl-start
+    # Pre-patch skeleton: the single callable handed to the merge machinery (the
+    # old `keep_attrs is True` strategy) returns the source's TOP-LEVEL mapping,
+    # and that callable is applied at EVERY merge level -- the top level, every
+    # sub-variable, and every coordinate -- so every level is overwritten with
+    # that single top-level mapping instead of the level's OWN mapping. This is
+    # the bug: coordinates (and, in the promotion regime, the global level)
+    # receive the source's top-level mapping rather than the level-appropriate
+    # value.
     coord_src = ToSeq(x_coord_attrs)  # type: PSeq[int]
     var_src = ToSeq(x_var_attrs)  # type: PSeq[int]
-    # always fill coord attrs from the SAME source coordinate (every case)
+    # BUG: each coordinate is filled with the source's single top-level mapping,
+    # not the coordinate's OWN mapping.
     out_coords = []  # type: List[int]
     i = 0
     while i < len(x_coord_attrs):
@@ -259,67 +268,27 @@
         Invariant(ToSeq(x_coord_attrs) == coord_src)
         Invariant(0 <= i and i <= len(coord_src))
         Invariant(len(out_coords) == i)
-        Invariant(ToSeq(out_coords) == coord_src.take(i))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < i,
-                    out_coords[k] == x_coord_attrs[k]),
-            [[out_coords[k]]])))
         Invariant(MustTerminate(len(x_coord_attrs) - i + 1))
         # invariants-end
-        out_coords.append(x_coord_attrs[i])
+        out_coords.append(x_attrs)
         i = i + 1
-    Assert(coord_src.take(len(coord_src)) == coord_src)
-    # fill sub-variable attrs per case (two cases, two loops -- each loop
-    # carries a single per-element rule so the Forall trigger stays simple)
+    # BUG: each sub-variable is likewise filled with the source's single
+    # top-level mapping rather than that sub-variable's OWN mapping.
     out_vars = []  # type: List[int]
-    if not top_unmatched:
-        # each output sub-variable slot is the SAME-INDEX source sub-variable
-        # slot.
-        j = 0
-        while j < len(x_var_attrs):
-            # invariants-start
-            Invariant(Acc(list_pred(x_var_attrs), 1 / 4))
-            Invariant(Acc(list_pred(out_vars)))
-            Invariant(ToSeq(x_var_attrs) == var_src)
-            Invariant(0 <= j and j <= len(var_src))
-            Invariant(len(out_vars) == j)
-            Invariant(ToSeq(out_vars) == var_src.take(j))
-            Invariant(Forall(int, lambda k: (
-                Implies(0 <= k and k < j, out_vars[k] == x_var_attrs[k]),
-                [[out_vars[k]]])))
-            Invariant(MustTerminate(len(x_var_attrs) - j + 1))
-            # invariants-end
-            out_vars.append(x_var_attrs[j])
-            j = j + 1
-        Assert(var_src.take(len(var_src)) == var_src)
-    else:
-        # the sub-variable bearing the source's name takes the source's
-        # WHOLE-OBJECT mapping; the other slots are left as the upstream
-        # computation produced them (modelled here as the empty mapping -- the
-        # contract makes no claim about them).
-        j = 0
-        while j < len(x_var_attrs):
-            # invariants-start
-            Invariant(Acc(list_pred(x_var_attrs), 1 / 4))
-            Invariant(Acc(list_pred(out_vars)))
-            Invariant(ToSeq(x_var_attrs) == var_src)
-            Invariant(-1 <= named_slot and named_slot < len(var_src))
-            Invariant(0 <= j and j <= len(var_src))
-            Invariant(len(out_vars) == j)
-            # the matching slot, once written, holds the source's top-level map
-            Invariant(Implies(0 <= named_slot and named_slot < j,
-                              out_vars[named_slot] == x_attrs))
-            Invariant(MustTerminate(len(x_var_attrs) - j + 1))
-            # invariants-end
-            if j == named_slot:
-                out_vars.append(x_attrs)
-            else:
-                out_vars.append(0)
-            Assert(out_vars[j] == (x_attrs if j == named_slot else 0))
-            j = j + 1
-    if top_unmatched:
-        top = 0
-    else:
-        top = x_attrs
+    j = 0
+    while j < len(x_var_attrs):
+        # invariants-start
+        Invariant(Acc(list_pred(x_var_attrs), 1 / 4))
+        Invariant(Acc(list_pred(out_vars)))
+        Invariant(ToSeq(x_var_attrs) == var_src)
+        Invariant(0 <= j and j <= len(var_src))
+        Invariant(len(out_vars) == j)
+        Invariant(MustTerminate(len(x_var_attrs) - j + 1))
+        # invariants-end
+        out_vars.append(x_attrs)
+        j = j + 1
+    # BUG: the global level is the broadcast top-level mapping in EVERY regime,
+    # including the promotion regime (where it must instead be empty).
+    top = x_attrs
     return WhereResult(top, out_coords, out_vars)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -249,7 +249,9 @@
     # impl-start
     coord_src = ToSeq(x_coord_attrs)  # type: PSeq[int]
     var_src = ToSeq(x_var_attrs)  # type: PSeq[int]
-    # always fill coord attrs from the SAME source coordinate (every case)
+    # WRONG: every coordinate gets the source's single TOP-LEVEL mapping
+    # (the headline pre-patch bug), while the top level / sub-variables are
+    # rebuilt correctly.
     out_coords = []  # type: List[int]
     i = 0
     while i < len(x_coord_attrs):
@@ -259,22 +261,12 @@
         Invariant(ToSeq(x_coord_attrs) == coord_src)
         Invariant(0 <= i and i <= len(coord_src))
         Invariant(len(out_coords) == i)
-        Invariant(ToSeq(out_coords) == coord_src.take(i))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < i,
-                    out_coords[k] == x_coord_attrs[k]),
-            [[out_coords[k]]])))
         Invariant(MustTerminate(len(x_coord_attrs) - i + 1))
         # invariants-end
-        out_coords.append(x_coord_attrs[i])
+        out_coords.append(x_attrs)
         i = i + 1
-    Assert(coord_src.take(len(coord_src)) == coord_src)
-    # fill sub-variable attrs per case (two cases, two loops -- each loop
-    # carries a single per-element rule so the Forall trigger stays simple)
     out_vars = []  # type: List[int]
     if not top_unmatched:
-        # each output sub-variable slot is the SAME-INDEX source sub-variable
-        # slot.
         j = 0
         while j < len(x_var_attrs):
             # invariants-start
@@ -293,10 +285,6 @@
             j = j + 1
         Assert(var_src.take(len(var_src)) == var_src)
     else:
-        # the sub-variable bearing the source's name takes the source's
-        # WHOLE-OBJECT mapping; the other slots are left as the upstream
-        # computation produced them (modelled here as the empty mapping -- the
-        # contract makes no claim about them).
         j = 0
         while j < len(x_var_attrs):
             # invariants-start
@@ -306,7 +294,6 @@
             Invariant(-1 <= named_slot and named_slot < len(var_src))
             Invariant(0 <= j and j <= len(var_src))
             Invariant(len(out_vars) == j)
-            # the matching slot, once written, holds the source's top-level map
             Invariant(Implies(0 <= named_slot and named_slot < j,
                               out_vars[named_slot] == x_attrs))
             Invariant(MustTerminate(len(x_var_attrs) - j + 1))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -317,9 +317,8 @@
                 out_vars.append(0)
             Assert(out_vars[j] == (x_attrs if j == named_slot else 0))
             j = j + 1
-    if top_unmatched:
-        top = 0
-    else:
-        top = x_attrs
+    # WRONG: the global level keeps the source's top-level mapping in EVERY
+    # regime, including the promotion regime where it must be empty.
+    top = x_attrs
     return WhereResult(top, out_coords, out_vars)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -266,7 +266,12 @@
             [[out_coords[k]]])))
         Invariant(MustTerminate(len(x_coord_attrs) - i + 1))
         # invariants-end
-        out_coords.append(x_coord_attrs[i])
+        # WRONG (off-by-one): every coordinate slot after the first takes the
+        # PRECEDING coordinate's mapping.
+        if i == 0:
+            out_coords.append(x_coord_attrs[0])
+        else:
+            out_coords.append(x_coord_attrs[i - 1])
         i = i + 1
     Assert(coord_src.take(len(coord_src)) == coord_src)
     # fill sub-variable attrs per case (two cases, two loops -- each loop
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -266,7 +266,12 @@
             [[out_coords[k]]])))
         Invariant(MustTerminate(len(x_coord_attrs) - i + 1))
         # invariants-end
-        out_coords.append(x_coord_attrs[i])
+        # WRONG (partial domain): the level-by-level rule is honoured only for
+        # a single-coordinate output; a richer coordinate roster is dropped.
+        if len(x_coord_attrs) == 1:
+            out_coords.append(x_coord_attrs[i])
+        else:
+            out_coords.append(0)
         i = i + 1
     Assert(coord_src.take(len(coord_src)) == coord_src)
     # fill sub-variable attrs per case (two cases, two loops -- each loop
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -266,7 +266,12 @@
             [[out_coords[k]]])))
         Invariant(MustTerminate(len(x_coord_attrs) - i + 1))
         # invariants-end
-        out_coords.append(x_coord_attrs[i])
+        # WRONG: the coordinate rule is honoured only in the ordinary regime;
+        # under promotion each coordinate is left with the empty mapping.
+        if top_unmatched:
+            out_coords.append(0)
+        else:
+            out_coords.append(x_coord_attrs[i])
         i = i + 1
     Assert(coord_src.take(len(coord_src)) == coord_src)
     # fill sub-variable attrs per case (two cases, two loops -- each loop
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -269,6 +269,13 @@
         out_coords.append(x_coord_attrs[i])
         i = i + 1
     Assert(coord_src.take(len(coord_src)) == coord_src)
+    # WRONG: walks its levels forever instead of delivering an output.
+    while len(x_coord_attrs) > 0:
+        # invariants-start
+        Invariant(Acc(list_pred(x_coord_attrs), 1 / 4))
+        Invariant(ToSeq(x_coord_attrs) == coord_src)
+        # invariants-end
+        i = i + 1
     # fill sub-variable attrs per case (two cases, two loops -- each loop
     # carries a single per-element rule so the Forall trigger stays simple)
     out_vars = []  # type: List[int]
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -321,5 +321,7 @@
         top = 0
     else:
         top = x_attrs
-    return WhereResult(top, out_coords, out_vars)
+    # WRONG: the output aliases the source's own coordinate storage rather
+    # than owning freshly built storage.
+    return WhereResult(top, x_coord_attrs, out_vars)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -311,11 +311,13 @@
                               out_vars[named_slot] == x_attrs))
             Invariant(MustTerminate(len(x_var_attrs) - j + 1))
             # invariants-end
+            # WRONG: the promoted source reaches its slot by name, so that slot
+            # must take the source's WHOLE-OBJECT mapping; here it takes the
+            # same-index sub-variable mapping instead.
             if j == named_slot:
-                out_vars.append(x_attrs)
+                out_vars.append(x_var_attrs[j])
             else:
                 out_vars.append(0)
-            Assert(out_vars[j] == (x_attrs if j == named_slot else 0))
             j = j + 1
     if top_unmatched:
         top = 0
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -311,11 +311,10 @@
                               out_vars[named_slot] == x_attrs))
             Invariant(MustTerminate(len(x_var_attrs) - j + 1))
             # invariants-end
-            if j == named_slot:
-                out_vars.append(x_attrs)
-            else:
-                out_vars.append(0)
-            Assert(out_vars[j] == (x_attrs if j == named_slot else 0))
+            # Exploits the unconstrained region: EVERY promotion slot, matching
+            # or not, is given the source's whole-object mapping.
+            out_vars.append(x_attrs)
+            Assert(out_vars[j] == x_attrs)
             j = j + 1
     if top_unmatched:
         top = 0
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -283,15 +283,12 @@
             Invariant(ToSeq(x_var_attrs) == var_src)
             Invariant(0 <= j and j <= len(var_src))
             Invariant(len(out_vars) == j)
-            Invariant(ToSeq(out_vars) == var_src.take(j))
-            Invariant(Forall(int, lambda k: (
-                Implies(0 <= k and k < j, out_vars[k] == x_var_attrs[k]),
-                [[out_vars[k]]])))
             Invariant(MustTerminate(len(x_var_attrs) - j + 1))
             # invariants-end
-            out_vars.append(x_var_attrs[j])
+            # WRONG: every sub-variable gets the source's single TOP-LEVEL
+            # mapping instead of its own same-named mapping.
+            out_vars.append(x_attrs)
             j = j + 1
-        Assert(var_src.take(len(var_src)) == var_src)
     else:
         # the sub-variable bearing the source's name takes the source's
         # WHOLE-OBJECT mapping; the other slots are left as the upstream
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -311,11 +311,14 @@
                               out_vars[named_slot] == x_attrs))
             Invariant(MustTerminate(len(x_var_attrs) - j + 1))
             # invariants-end
-            if j == named_slot:
+            # Exploits the silence at named_slot == -1: with no slot bearing the
+            # source's name, EVERY slot is given the source's whole-object mapping.
+            if named_slot < 0:
+                out_vars.append(x_attrs)
+            elif j == named_slot:
                 out_vars.append(x_attrs)
             else:
                 out_vars.append(0)
-            Assert(out_vars[j] == (x_attrs if j == named_slot else 0))
             j = j + 1
     if top_unmatched:
         top = 0
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -297,6 +297,7 @@
         # WHOLE-OBJECT mapping; the other slots are left as the upstream
         # computation produced them (modelled here as the empty mapping -- the
         # contract makes no claim about them).
+        Assert(False)  # VACUITY CONTROL: must NOT verify
         j = 0
         while j < len(x_var_attrs):
             # invariants-start
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -321,5 +321,6 @@
         top = 0
     else:
         top = x_attrs
+    Assert(False)  # VACUITY CONTROL: must NOT verify
     return WhereResult(top, out_coords, out_vars)
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -317,9 +317,10 @@
                 out_vars.append(0)
             Assert(out_vars[j] == (x_attrs if j == named_slot else 0))
             j = j + 1
+    # WRONG: the two regimes' top-level placement is swapped.
     if top_unmatched:
+        top = x_attrs
+    else:
         top = 0
-    else:
-        top = x_attrs
     return WhereResult(top, out_coords, out_vars)
     # impl-end
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -311,11 +311,12 @@
                               out_vars[named_slot] == x_attrs))
             Invariant(MustTerminate(len(x_var_attrs) - j + 1))
             # invariants-end
-            if j == named_slot:
+            # WRONG (boundary): slot 0 never receives the source's whole-object
+            # mapping even when it is the slot bearing the source's name.
+            if j == named_slot and j > 0:
                 out_vars.append(x_attrs)
             else:
                 out_vars.append(0)
-            Assert(out_vars[j] == (x_attrs if j == named_slot else 0))
             j = j + 1
     if top_unmatched:
         top = 0
```

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -311,11 +311,13 @@
                               out_vars[named_slot] == x_attrs))
             Invariant(MustTerminate(len(x_var_attrs) - j + 1))
             # invariants-end
+            # Exploits the unconstrained region a third way: the non-matching
+            # promotion slots take the source's same-index sub-variable mapping
+            # (the ordinary regime's rule) instead of the empty mapping.
             if j == named_slot:
                 out_vars.append(x_attrs)
             else:
-                out_vars.append(0)
-            Assert(out_vars[j] == (x_attrs if j == named_slot else 0))
+                out_vars.append(x_var_attrs[j])
             j = j + 1
     if top_unmatched:
         top = 0
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for pydata__xarray-7229/nagini. 17 same-spec attacks built by copying model.py and editing ONLY the rebuild_attrs impl region (spec byte-identical: `adversary same-spec` returned SAME for all 17 and for the positive control). Focus per instructions on the A legs (A6/A7 A-reference deep models) and the model<->patch correspondence; R/I legs left to G-CONF.

POSITIVE CONTROL positive_control.py (verbatim model.py impl): `adversary weakness` -> CANDIDATE (shares spec AND verifies, 19.0s), i.e. it verifies.

PREPATCH REPRODUCED: atk_1.py is model_prepatch.py's impl body re-encoded into model.py's impl region (coords AND sub-variables get the single top-level mapping; top = x_attrs in every regime). `weakness` rc=2, rejected on `Implies(top_unmatched, Result().attrs == 0)`.

### COMMANDS (all from repo root, swe-proof):
  python -m swebench_unified.adversary weakness nagini pydata__xarray-7229 atk_N.py
run 3-at-a-time as background jobs; plus `bash scripts/nagini_verify.sh <file>` for the quoted error lines.

REJECTED (rc=2, 14 of 17) with the clause that killed each:
  atk_1  prepatch bug (coord + var + global over-broadcast) -> Postcondition Implies(top_unmatched, Result().attrs == 0) [model.py:224]
  atk_2  coord over-broadcast ONLY (headline A6 bug in isolation, top level correct) -> Forall k. Result().coord_attrs[k] == x_coord_attrs[k] [model.py:230-233]
  atk_3  promotion GLOBAL over-broadcast ONLY (coords correct) -> Implies(top_unmatched, Result().attrs == 0)
  atk_4  BOUNDARY/off-by-one: coord slot i takes x_coord_attrs[i-1]
  atk_5  PARTIAL DOMAIN: level-by-level coord rule honoured only when len(x_coord_attrs)==1, else 0
  atk_6  A6 REGIME leg: coords filled level-by-level only when not top_unmatched; empty under promotion (drops the patch's "always fill coord attrs of x (BOTH regimes)")
  atk_7  CONTROL-FLOW EFFECT / divergence: added non-terminating loop -> Obligation leak check failed (MustTerminate(6) at the METHOD level does the work)
  atk_8  EFFECT/ALIASING: returns the SOURCE's list as the output's coord storage instead of fresh storage
  atk_9  A7 leg: promotion named slot takes x_var_attrs[j] instead of the whole-object x_attrs
  atk_11 ordinary sub-variable over-broadcast (every sub-variable gets x_attrs)
  atk_13 VACUITY CONTROL Assert(False) inside the promotion branch -> "Assertion False might not hold" (branch is FEASIBLE, not vacuous)
  atk_14 VACUITY CONTROL Assert(False) before the return -> rejected (method not vacuous)
  atk_15 regimes SWAPPED at the top level
  atk_16 BOUNDARY on named_slot: slot 0 never receives x_attrs

CANDIDATES (rc=0: share spec AND verify) -- 3, ALL occupying the one region the contract deliberately leaves unconstrained (promotion-regime NON-matching sub-variable slots / named_slot == -1), which refinement.md A7+SSB and model.py:90-92,245,296-299 disclose explicitly:
  atk_10 every promotion slot (matching or not) takes x's whole-object mapping
  atk_12 when named_slot == -1 (no slot bears x's name) every slot takes x's whole-object mapping
  atk_17 non-matching promotion slots take x's same-index sub-variable mapping

MANDATORY RESOLVE RUNS -- for EVERY candidate I materialized the faithful refined patch and RAN the official harness. Patches were built by extracting xarray/core/computation.py at base_commit 3aa75c8, editing `where()`, and `git diff` (each verified `git apply --check` clean against the extracted base BEFORE submission -- the prior G-EQ attempt failed as INCONCLUSIVE on "patch does not apply", so this was checked first). Command:
  python resolve_one.py <10|12|17>   (calls swebench_unified.harness.run_resolve)
### OBSERVED RESULTS (all completed=True, patch_successfully_applied=True):
  atk_10 -> RESOLVED (F2P 1/1 success, P2P 280/280 success)
  atk_12 -> RESOLVED (F2P 1/1, P2P 280/280)
  atk_17 -> RESOLVED (F2P 1/1, P2P 280/280)
So all three are CORRECT ECHOES, not weaknesses: verify AND resolve. No verifying wrong impl's faithful patch failed to resolve => no verify=>correct break. JSON reports {10,12,17}.json.

DISCRIMINATION CONTROL (so "resolved" is informative and not a rubber stamp -- guards against an oracle/pipeline that cannot refute anything here): I also materialized faithful patches for two REJECTED attacks and ran the same oracle.
  patch_neg2.diff (atk_2's coord over-broadcast) -> NOT RESOLVED, completed=True, 3 consistent attempts, F2P test_where_attrs FAILS, P2P 280/280 pass
  patch_neg3.diff (atk_3's promotion-global over-broadcast) -> NOT RESOLVED, completed=True, 3 consistent attempts, F2P test_where_attrs FAILS, P2P 280/280 pass
This closes the loop in BOTH directions on this bundle: the two impls the SPEC rejects produce patches the ORACLE also rejects (and for the right reason -- the F2P test, with all 280 P2P intact, so the patch is not merely broken), and the three impls the spec ADMITS produce patches that resolve. The spec's accept/reject boundary tracks the oracle's on every pair I could construct.

### REFINEMENT.MD LEG AUDIT (every leg is R / A-reference / I; NO kind-3, NO A-consumed row -- there is no @ContractOnly axiom, so nothing is assumed):
  A1,A2,A3,A4 = R; A5 = I-under-R; A6 = A-reference; A7 = A-reference(ordinary) + I-under-R(promotion slot); A8 = R+I. Correspondence to the real callees CHECKS OUT on the load-bearing points:
  * A2/A3's hardest claim -- "x's mapping AT a name" resolved ON x by getattr, NOT by membership in x.coords/x.data_vars -- is the correct reading of patch.diff's getattr(getattr(x, c, None), "attrs", {}), and axiom_check.py:_check_name_resolution pins the names where the two readings disagree (T/variable/real/imag -> x_attrs, values/shape/zzz -> 0) against the real callee. This is the leg most likely to be quietly wrong and it is right.
  * A5's regime split matches patch.diff exactly (result.attrs = {} promotion / getattr(x,"attrs",{}) ordinary); atk_3 + patch_neg3 confirm it is load-bearing on the F2P test.
  * A4's named_slot == -1 case is faithful because patch.diff:35 short-circuits (getattr(x,"name",None) is None; `None in result.data_vars` is False; x.name is never evaluated).
  * A7's silence about non-matching promotion slots matches the gold patch, which writes only result.attrs={} and the one keyed slot. atk_10/12/17 confirm the silence is genuinely harmless: all three occupants of that region resolve. The unconstrained region is therefore correctly scoped, not a hole.

NON-BLOCKING DOC/EVIDENCE DEFECTS FOUND (none changes the verdict; all are citation/coverage accuracy in the A-reference EVIDENCE, not unsoundness of the spec -- and G-CONF covers the gaps):
  1. axiom_check.py:112 calls xr.where(cond, ds_x, ds_x, keep_attrs=True) -- it passes ds_x as BOTH x and y, so the 2-Datasets assertions at :114/:118/:122 cannot discriminate an impl that sourced attrs from y. main() builds the real ds_y at :397 but only for promotion. refinement.md:120-121, mapping.md:148-150 and meta.json deep_model_references[0].checked_by all describe this as one of "the 7 F2P scenarios" verbatim; it is not. (The DataArray scenarios DO discriminate, since y carries distinct attrs.) _check_two_datasets's 3rd parameter `x` is dead, a symptom of the same slip.
  2. Every Dataset in axiom_check.py has exactly ONE data-var, so named_slot is always 0 and len(var_attrs) always 1: A7's "same-INDEX / per-element" content and the named_slot>=1 and named_slot==-1 corner cases are NOT witnessed at G-AX, though refinement.md:52,119-121 cites G-AX for them. They ARE witnessed by conformance_check.py (G-CONF) -- so the bundle covers them; the citation names the wrong gate.
  3. mapping.md:130-133 justifies the positional coord/var carriers by join="exact" alignment making the output's coords correspond one-to-one with x's -- stale and false (it contradicts mapping.md's own SS1 and the F2P scalar-x scenario where x has no coords at all). Wrong justification, right conclusion: the carriers are faithful because they are DEFINED per output level name via getattr on x, needing no x<->output name correspondence.
  4. refinement.md:49 (A4) cites the patch op as `result.data_vars.index(x.name)`; the patch computes no index (keyed write result[x.name].attrs=..., and DataVariables has no .index). named_slot is a modelling device over roster order; the cell paraphrases rather than quotes.
  5. refinement.md:52 tags the promotion loop I-under-R, but model.py:317's `out_vars.append(0)` has no counterpart in the gold patch (which leaves those slots as apply_ufunc produced). Sound because the contract is silent there and atk_10/12/17 now show the silence costs nothing, but "identical concrete operation" is not accurate for that line.
  6. mapping.md:148 says 2000 fuzz cases "(DataArray and promotion)"; axiom_check.py:402,418 runs 2000 DataArray and ~1000 promotion (coin flip) -- ~2x over-count of the promotion leg.
  7. axiom_check.py's expectation helper _level_attrs (:73) is a verbatim transliteration of the callee's own getattr expression, so the coord/data-var oracle is somewhat self-referential; mitigated because x is built from literals and the not-broadcast guard (:90-93) + literal {} anchors (:133, :193-200) are independent -- but that guard exists only in _check_da, not in _check_two_datasets or _check_promotion.

VERDICT: SOUND. 17 same-spec attacks run (>=5 required), positive control verifies, prepatch bug reproduced and rejected, 14 rejected, and for all 3 CANDIDATEs the faithful refined patch was materialized and RUN through the official harness -- every one RESOLVED (correct echoes). Two rejected attacks' patches were also run and correctly did NOT resolve, so the oracle discriminates on this instance. No verify=>correct break found. Recommend the bundle owner fix axiom_check.py:112 (use ds_y) and re-cite the named_slot/per-element rows to G-CONF; neither is a spec defect.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_11.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_10.py`, `atk_12.py`, `atk_17.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

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

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for pydata__xarray-7229/nagini. 17 same-spec attacks built by copying model.py and editing ONLY the rebuild_attrs impl region (spec byte-identical: `adversary same-spec` returned SAME for all 17 and for the positive control). Focus per instructions on the A legs (A6/A7 A-reference deep models) and the model<->patch correspondence; R/I legs left to G-CONF.

POSITIVE CONTROL positive_control.py (verbatim model.py impl): `adversary weakness` -> CANDIDATE (shares spec AND verifies, 19.0s), i.e. it verifies.

PREPATCH REPRODUCED: atk_1.py is model_prepatch.py's impl body re-encoded into model.py's impl region (coords AND sub-variables get the single top-level mapping; top = x_attrs in every regime). `weakness` rc=2, rejected on `Implies(top_unmatched, Result().attrs == 0)`.

### COMMANDS (all from repo root, swe-proof):
  python -m swebench_unified.adversary weakness nagini pydata__xarray-7229 atk_N.py
run 3-at-a-time as background jobs; plus `bash scripts/nagini_verify.sh <file>` for the quoted error lines.

REJECTED (rc=2, 14 of 17) with the clause that killed each:
  atk_1  prepatch bug (coord + var + global over-broadcast) -> Postcondition Implies(top_unmatched, Result().attrs == 0) [model.py:224]
  atk_2  coord over-broadcast ONLY (headline A6 bug in isolation, top level correct) -> Forall k. Result().coord_attrs[k] == x_coord_attrs[k] [model.py:230-233]
  atk_3  promotion GLOBAL over-broadcast ONLY (coords correct) -> Implies(top_unmatched, Result().attrs == 0)
  atk_4  BOUNDARY/off-by-one: coord slot i takes x_coord_attrs[i-1]
  atk_5  PARTIAL DOMAIN: level-by-level coord rule honoured only when len(x_coord_attrs)==1, else 0
  atk_6  A6 REGIME leg: coords filled level-by-level only when not top_unmatched; empty under promotion (drops the patch's "always fill coord attrs of x (BOTH regimes)")
  atk_7  CONTROL-FLOW EFFECT / divergence: added non-terminating loop -> Obligation leak check failed (MustTerminate(6) at the METHOD level does the work)
  atk_8  EFFECT/ALIASING: returns the SOURCE's list as the output's coord storage instead of fresh storage
  atk_9  A7 leg: promotion named slot takes x_var_attrs[j] instead of the whole-object x_attrs
  atk_11 ordinary sub-variable over-broadcast (every sub-variable gets x_attrs)
  atk_13 VACUITY CONTROL Assert(False) inside the promotion branch -> "Assertion False might not hold" (branch is FEASIBLE, not vacuous)
  atk_14 VACUITY CONTROL Assert(False) before the return -> rejected (method not vacuous)
  atk_15 regimes SWAPPED at the top level
  atk_16 BOUNDARY on named_slot: slot 0 never receives x_attrs

CANDIDATES (rc=0: share spec AND verify) -- 3, ALL occupying the one region the contract deliberately leaves unconstrained (promotion-regime NON-matching sub-variable slots / named_slot == -1), which refinement.md A7+SSB and model.py:90-92,245,296-299 disclose explicitly:
  atk_10 every promotion slot (matching or not) takes x's whole-object mapping
  atk_12 when named_slot == -1 (no slot bears x's name) every slot takes x's whole-object mapping
  atk_17 non-matching promotion slots take x's same-index sub-variable mapping

MANDATORY RESOLVE RUNS -- for EVERY candidate I materialized the faithful refined patch and RAN the official harness. Patches were built by extracting xarray/core/computation.py at base_commit 3aa75c8, editing `where()`, and `git diff` (each verified `git apply --check` clean against the extracted base BEFORE submission -- the prior G-EQ attempt failed as INCONCLUSIVE on "patch does not apply", so this was checked first). Command:
  python resolve_one.py <10|12|17>   (calls swebench_unified.harness.run_resolve)
### OBSERVED RESULTS (all completed=True, patch_successfully_applied=True):
  atk_10 -> RESOLVED (F2P 1/1 success, P2P 280/280 success)
  atk_12 -> RESOLVED (F2P 1/1, P2P 280/280)
  atk_17 -> RESOLVED (F2P 1/1, P2P 280/280)
So all three are CORRECT ECHOES, not weaknesses: verify AND resolve. No verifying wrong impl's faithful patch failed to resolve => no verify=>correct break. JSON reports {10,12,17}.json.

DISCRIMINATION CONTROL (so "resolved" is informative and not a rubber stamp -- guards against an oracle/pipeline that cannot refute anything here): I also materialized faithful patches for two REJECTED attacks and ran the same oracle.
  patch_neg2.diff (atk_2's coord over-broadcast) -> NOT RESOLVED, completed=True, 3 consistent attempts, F2P test_where_attrs FAILS, P2P 280/280 pass
  patch_neg3.diff (atk_3's promotion-global over-broadcast) -> NOT RESOLVED, completed=True, 3 consistent attempts, F2P test_where_attrs FAILS, P2P 280/280 pass
This closes the loop in BOTH directions on this bundle: the two impls the SPEC rejects produce patches the ORACLE also rejects (and for the right reason -- the F2P test, with all 280 P2P intact, so the patch is not merely broken), and the three impls the spec ADMITS produce patches that resolve. The spec's accept/reject boundary tracks the oracle's on every pair I could construct.

### REFINEMENT.MD LEG AUDIT (every leg is R / A-reference / I; NO kind-3, NO A-consumed row -- there is no @ContractOnly axiom, so nothing is assumed):
  A1,A2,A3,A4 = R; A5 = I-under-R; A6 = A-reference; A7 = A-reference(ordinary) + I-under-R(promotion slot); A8 = R+I. Correspondence to the real callees CHECKS OUT on the load-bearing points:
  * A2/A3's hardest claim -- "x's mapping AT a name" resolved ON x by getattr, NOT by membership in x.coords/x.data_vars -- is the correct reading of patch.diff's getattr(getattr(x, c, None), "attrs", {}), and axiom_check.py:_check_name_resolution pins the names where the two readings disagree (T/variable/real/imag -> x_attrs, values/shape/zzz -> 0) against the real callee. This is the leg most likely to be quietly wrong and it is right.
  * A5's regime split matches patch.diff exactly (result.attrs = {} promotion / getattr(x,"attrs",{}) ordinary); atk_3 + patch_neg3 confirm it is load-bearing on the F2P test.
  * A4's named_slot == -1 case is faithful because patch.diff:35 short-circuits (getattr(x,"name",None) is None; `None in result.data_vars` is False; x.name is never evaluated).
  * A7's silence about non-matching promotion slots matches the gold patch, which writes only result.attrs={} and the one keyed slot. atk_10/12/17 confirm the silence is genuinely harmless: all three occupants of that region resolve. The unconstrained region is therefore correctly scoped, not a hole.

NON-BLOCKING DOC/EVIDENCE DEFECTS FOUND (none changes the verdict; all are citation/coverage accuracy in the A-reference EVIDENCE, not unsoundness of the spec -- and G-CONF covers the gaps):
  1. axiom_check.py:112 calls xr.where(cond, ds_x, ds_x, keep_attrs=True) -- it passes ds_x as BOTH x and y, so the 2-Datasets assertions at :114/:118/:122 cannot discriminate an impl that sourced attrs from y. main() builds the real ds_y at :397 but only for promotion. refinement.md:120-121, mapping.md:148-150 and meta.json deep_model_references[0].checked_by all describe this as one of "the 7 F2P scenarios" verbatim; it is not. (The DataArray scenarios DO discriminate, since y carries distinct attrs.) _check_two_datasets's 3rd parameter `x` is dead, a symptom of the same slip.
  2. Every Dataset in axiom_check.py has exactly ONE data-var, so named_slot is always 0 and len(var_attrs) always 1: A7's "same-INDEX / per-element" content and the named_slot>=1 and named_slot==-1 corner cases are NOT witnessed at G-AX, though refinement.md:52,119-121 cites G-AX for them. They ARE witnessed by conformance_check.py (G-CONF) -- so the bundle covers them; the citation names the wrong gate.
  3. mapping.md:130-133 justifies the positional coord/var carriers by join="exact" alignment making the output's coords correspond one-to-one with x's -- stale and false (it contradicts mapping.md's own SS1 and the F2P scalar-x scenario where x has no coords at all). Wrong justification, right conclusion: the carriers are faithful because they are DEFINED per output level name via getattr on x, needing no x<->output name correspondence.
  4. refinement.md:49 (A4) cites the patch op as `result.data_vars.index(x.name)`; the patch computes no index (keyed write result[x.name].attrs=..., and DataVariables has no .index). named_slot is a modelling device over roster order; the cell paraphrases rather than quotes.
  5. refinement.md:52 tags the promotion loop I-under-R, but model.py:317's `out_vars.append(0)` has no counterpart in the gold patch (which leaves those slots as apply_ufunc produced). Sound because the contract is silent there and atk_10/12/17 now show the silence costs nothing, but "identical concrete operation" is not accurate for that line.
  6. mapping.md:148 says 2000 fuzz cases "(DataArray and promotion)"; axiom_check.py:402,418 runs 2000 DataArray and ~1000 promotion (coin flip) -- ~2x over-count of the promotion leg.
  7. axiom_check.py's expectation helper _level_attrs (:73) is a verbatim transliteration of the callee's own getattr expression, so the coord/data-var oracle is somewhat self-referential; mitigated because x is built from literals and the not-broadcast guard (:90-93) + literal {} anchors (:133, :193-200) are independent -- but that guard exists only in _check_da, not in _check_two_datasets or _check_promotion.

VERDICT: SOUND. 17 same-spec attacks run (>=5 required), positive control verifies, prepatch bug reproduced and rejected, 14 rejected, and for all 3 CANDIDATEs the faithful refined patch was materialized and RUN through the official harness -- every one RESOLVED (correct echoes). Two rejected attacks' patches were also run and correctly did NOT resolve, so the oracle discriminates on this instance. No verify=>correct break found. Recommend the bundle owner fix axiom_check.py:112 (use ds_y) and re-cite the named_slot/per-element rows to G-CONF; neither is a spec defect.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

REFERENCE ORIENTATION (per instructions): built a fresh worktree from the upstream repository at base_commit 3aa75c8d and applied the gold patch (data/swe_bench_verified test.jsonl `patch`, identical to the refinement.md hunk). Confirmed this is the right reference by running the F2P body (test_where_attrs, all 7 sub-cases) inline against it -> PASS. Also created an UNPATCHED base worktree purely as a discrimination control.

**SPEC INTEGRITY:** `adversary same-spec nagini pydata__xarray-7229 <copy of bundle model.py>` -> exit 0, "SAME — attack shares the bundle's exact specification". Bundle model.py verifies under the pinned verifier (scripts/nagini_verify.sh): "Verification successful", 22.2s.

**METHOD:** wrote a differential harness that, for each concrete (cond,x,y), computes the model carriers from the REAL x by mapping.md §2's abstraction function using the callee's OWN expression getattr(getattr(x,name,None),'attrs',{}), then calls the real patched xr.where(cond,x,y,keep_attrs=True) and tests every postcondition of rebuild_attrs as a dict-equality: C1 (not top_unmatched -> Result().attrs==x_attrs), C2 (top_unmatched -> Result().attrs==0), C3 (len + per-index coord_attrs[k]==x_coord_attrs[k], EVERY regime), C4 (ordinary var_attrs[k]==x_var_attrs[k]), C5 (promotion var_attrs[named_slot]==x_attrs), plus RO (x's top/coord/data_var attrs unchanged across the call) and TOT (no raise). A stricter second harness aligned carriers against the REAL result's own coords/data_vars roster rather than a keep_attrs=False skeleton, so no skeleton dependency could mask a divergence. top_unmatched was computed as the patch's own guard isinstance(y,Dataset) and not isinstance(x,Dataset); named_slot as list(result.data_vars).index(getattr(x,'name',None)) or -1.

EVIDENCE - NO DIVERGENCE FOUND (~9,000 in-domain calls, 0 clause failures):
1. 7 F2P scenarios: all clauses hold.
2. Targeted structural sweep (34 cases): MultiIndex coords on Dataset/DataArray incl. level coords 'one'/'two' (write sticks, C3 holds); Variable-as-x with Dataset y; cond-as-Dataset; x Dataset + y DataArray; promotion with multiple data_vars and x.name matching / =None / not present (named_slot=-1 -> C5 vacuous, matches the contract making no claim); non-index and scalar (0-d) coords; datetime64 coords; 0-d DataArrays.
3. THE NAME-RESOLUTION CLASS the docstring/mapping.md §1 hinges on: coord names 'T','variable','real','imag' (derived views of x -> must contribute x_attrs, NOT 0) and 'values','shape','zzz','dtype','name','attrs','data' (no mapping -> 0), each in both regimes. All 22 pass, confirming the spec's non-obvious "derived view contributes x_attrs" gloss is the callee's actual behavior, not an over-claim.
4. Randomized fuzz, 4000 draws over cond/x/y ∈ {scalar, DataArray, Dataset, Variable, ndarray} × random coord-name subsets from a 14-name pool × random x.name: 3939 in-domain checked, 0 clause failures. Regime coverage measured: 2818 ordinary / 540 promotion, 49 with C5 actually exercised, coords_checked 0..3 — so the clauses were genuinely tested, not vacuous.
5. READ-ONLY (the Requires/Ensures at 1/2 permission + ToSeq==Old(ToSeq)): 0 violations. Corroborated structurally — every attrs setter (Variable:957, DataArray:870, Dataset:648) rebinds via `self._attrs = dict(value)` rather than mutating in place, and DataArray.`_copy` (dataarray.py:1183) copies coord Variables. I specifically chased the one aliasing path that could break this: build_output_coords_and_indexes' skip-merge branch does `merged_vars = dict(unpacked_coords.variables)` and DOES share x's coord Variable objects (verified directly: sharing True at that level, and DataArray(fastpath) preserves it). But deep_align(copy=False) upstream returns a copy (Aligner.align -> obj.copy(deep=False)), so the sharing never survives to `result`: an explicit Variable-identity check between x and the real result over all 3939 in-domain fuzz cases found 0 shared Variables. Hence the rebuild's `result[c].attrs = ...` writes cannot reach x.
6. **TOTALITY:** separate probe over 6000 draws found 5201 inputs that COMBINE (keep_attrs=False succeeds with attr levels). Of these, keep_attrs=True raised on 118 — and every one is covered by a carve-out the docstring states explicitly (a declined name interrogation, e.g. a coord named 'dt' -> TypeError "'.dt' accessor only available for DataArray with datetime64", or a non-walkable/bogus roster). GENUINE totality violations: 0.
7. The docstring's bogus-roster carve-out was probed directly by shadowing x.attrs['data_vars'] / ['coords'] with ['a'], [], 'a', ['a','a'] (walkable rosters of carried names -> spec says INSIDE the domain: all clauses hold, confirmed) vs ['nope'] and 5 (TypeError) -> raises, matching the spec's exclusion. Also tested x.attrs keys colliding with an output coord name where the value itself HAS .attrs. The positive half of that carve-out ("walkable roster => every mapping holds") is therefore not an over-claim.

DISCRIMINATION CONTROLS (the spec is not trivially true): the same harness run against the UNPATCHED base worktree fails 6 of 7 F2P scenarios — C3 e.g. "coord 'a': got {'attr':'x_da'} expected {'attr':'x_coord'}" (the coordinate over-broadcast) and C2 "promotion global: got {'attr':'x_da'} expected {}". Independently, model_prepatch.py FAILS the pinned verifier on exactly Implies(top_unmatched, Result().attrs == 0) (pre.py:224). So the clauses pin precisely the patch delta and the C2 promotion-global clause — the field refinement.md flags as a previously-over-claimed defect — is now correct and load-bearing.

**ASSESSMENT:** I could not construct an input on which the modelled rebuild_attrs disagrees with the real patched callee. The spec is notably careful where it would otherwise be too strong: it states the top-level mapping per-regime (0 under promotion) rather than unconditionally, leaves the promotion regime's non-matching data_var slots unconstrained (the patch does leave them as apply_ufunc produced), reads no entries of x_var_attrs in the promotion regime, and carves out declined lookups and bogus rosters — each carve-out I probed corresponds to real callee behavior rather than to a convenient exclusion of a counterexample. No faithfulness break found.

REFERENCE ORIENTATION (per instructions): built a fresh worktree from the upstream repository at base_commit 3aa75c8d and applied the gold patch (data/swe_bench_verified test.jsonl `patch`, identical to the refinement.md hunk). Confirmed this is the right reference by running the F2P body (test_where_attrs, all 7 sub-cases) inline against it -> PASS. Also created an UNPATCHED base worktree purely as a discrimination control.

SPEC INTEGRITY: `adversary same-spec nagini pydata__xarray-7229 <copy of bundle model.py>` -> exit 0, "SAME — attack shares the bundle's exact specification". Bundle model.py verifies under the pinned verifier (scripts/nagini_verify.sh): "Verification successful", 22.2s.

METHOD: wrote a differential harness that, for each concrete (cond,x,y), computes the model carriers from the REAL x by mapping.md §2's abstraction function using the callee's OWN expression getattr(getattr(x,name,None),'attrs',{}), then calls the real patched xr.where(cond,x,y,keep_attrs=True) and tests every postcondition of rebuild_attrs as a dict-equality: C1 (not top_unmatched -> Result.attrs==x_attrs), C2 (top_unmatched -> Result.attrs==0), C3 (len + per-index coord_attrs[k]==x_coord_attrs[k], EVERY regime), C4 (ordinary var_attrs[k]==x_var_attrs[k]), C5 (promotion var_attrs[named_slot]==x_attrs), plus RO (x's top/coord/data_var attrs unchanged across the call) and TOT (no raise). A stricter second harness aligned carriers against the REAL result's own coords/data_vars roster rather than a keep_attrs=False skeleton, so no skeleton dependency could mask a divergence. top_unmatched was computed as the patch's own guard isinstance(y,Dataset) and not isinstance(x,Dataset); named_slot as list(result.data_vars).index(getattr(x,'name',None)) or -1.

EVIDENCE - NO DIVERGENCE FOUND (~9,000 in-domain calls, 0 clause failures):
1. 7 F2P scenarios: all clauses hold.
2. Targeted structural sweep (34 cases): MultiIndex coords on Dataset/DataArray incl. level coords 'one'/'two' (write sticks, C3 holds); Variable-as-x with Dataset y; cond-as-Dataset; x Dataset + y DataArray; promotion with multiple data_vars and x.name matching / =None / not present (named_slot=-1 -> C5 vacuous, matches the contract making no claim); non-index and scalar (0-d) coords; datetime64 coords; 0-d DataArrays.
3. THE NAME-RESOLUTION CLASS the docstring/mapping.md §1 hinges on: coord names 'T','variable','real','imag' (derived views of x -> must contribute x_attrs, NOT 0) and 'values','shape','zzz','dtype','name','attrs','data' (no mapping -> 0), each in both regimes. All 22 pass, confirming the spec's non-obvious "derived view contributes x_attrs" gloss is the callee's actual behavior, not an over-claim.
4. Randomized fuzz, 4000 draws over cond/x/y ∈ {scalar, DataArray, Dataset, Variable, ndarray} × random coord-name subsets from a 14-name pool × random x.name: 3939 in-domain checked, 0 clause failures. Regime coverage measured: 2818 ordinary / 540 promotion, 49 with C5 actually exercised, coords_checked 0..3 — so the clauses were genuinely tested, not vacuous.
5. READ-ONLY (the Requires/Ensures at 1/2 permission + ToSeq==Old(ToSeq)): 0 violations. Corroborated structurally — every attrs setter (Variable:957, DataArray:870, Dataset:648) rebinds via `self._attrs = dict(value)` rather than mutating in place, and DataArray._copy (dataarray.py:1183) copies coord Variables. I specifically chased the one aliasing path that could break this: build_output_coords_and_indexes' skip-merge branch does `merged_vars = dict(unpacked_coords.variables)` and DOES share x's coord Variable objects (verified directly: sharing True at that level, and DataArray(fastpath) preserves it). But deep_align(copy=False) upstream returns a copy (Aligner.align -> obj.copy(deep=False)), so the sharing never survives to `result`: an explicit Variable-identity check between x and the real result over all 3939 in-domain fuzz cases found 0 shared Variables. Hence the rebuild's `result[c].attrs =...` writes cannot reach x.
6. TOTALITY: separate probe over 6000 draws found 5201 inputs that COMBINE (keep_attrs=False succeeds with attr levels). Of these, keep_attrs=True raised on 118 — and every one is covered by a carve-out the docstring states explicitly (a declined name interrogation, e.g. a coord named 'dt' -> TypeError "'.dt' accessor only available for DataArray with datetime64", or a non-walkable/bogus roster). GENUINE totality violations: 0.
7. The docstring's bogus-roster carve-out was probed directly by shadowing x.attrs['data_vars'] / ['coords'] with ['a'],, 'a', ['a','a'] (walkable rosters of carried names -> spec says INSIDE the domain: all clauses hold, confirmed) vs ['nope'] and 5 (TypeError) -> raises, matching the spec's exclusion. Also tested x.attrs keys colliding with an output coord name where the value itself HAS.attrs. The positive half of that carve-out ("walkable roster => every mapping holds") is therefore not an over-claim.

DISCRIMINATION CONTROLS (the spec is not trivially true): the same harness run against the UNPATCHED base worktree fails 6 of 7 F2P scenarios — C3 e.g. "coord 'a': got {'attr':'x_da'} expected {'attr':'x_coord'}" (the coordinate over-broadcast) and C2 "promotion global: got {'attr':'x_da'} expected {}". Independently, model_prepatch.py FAILS the pinned verifier on exactly Implies(top_unmatched, Result.attrs == 0) (pre.py:224). So the clauses pin precisely the patch delta and the C2 promotion-global clause — the field refinement.md flags as a previously-over-claimed defect — is now correct and load-bearing.

ASSESSMENT: I could not construct an input on which the modelled rebuild_attrs disagrees with the real patched callee. The spec is notably careful where it would otherwise be too strong: it states the top-level mapping per-regime (0 under promotion) rather than unconditionally, leaves the promotion regime's non-matching data_var slots unconstrained (the patch does leave them as apply_ufunc produced), reads no entries of x_var_attrs in the promotion regime, and carves out declined lookups and bogus rosters — each carve-out I probed corresponds to real callee behavior rather than to a convenient exclusion of a counterexample. No faithfulness break found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** panel_3: leakage accepted per RELAXED_LEAKAGE.md (agent flagged: leakage)

**What the spec view discloses.** Quoted from this bundle's own `RELAXED_LEAKAGE.md`, "1. What the spec view discloses":

> The first half — *rebuild every level from the same-named level of the source, coordinates included* — is derivable from the public `problem_statement` and is not a disclosure. The statement itself contrasts two levels and says which way round they belong ("coordinate attributes are getting overwritten by variable attributes … Coordinate attributes should be preserved"), so *each level keeps its own mapping* is the minimal reading of the reported defect, and the per-sub-variable clause is that same rule at the level the statement names as the one doing the overwriting.

**Why the disclosure is accepted.** The same file's account of why the disclosure is forced rather than avoidable, "3. Why faithful + non-leaking is impossible here":

> So a spec that dropped this sub-behaviour would verify an implementation that does not pass the instance's test — the exact failure `verify ⟹ correct` forbids. The disclosure is in the **behaviour**, not in prose that could be deleted.

**The second facet the reviewer flagged.** The reviewer's finding was that the argument quoted above reaches the structural facet only, and not the roster paragraph at `model.py:59-74` that a later docstring revision put on the spec view. That paragraph now carries its own disposition in the same file, "7. The roster carve-out is faithfulness-forced, not test-forced", and the disposition it records is not the one quoted above:

> Its disposition is **FAITHFULNESS-FORCED, not test-forced**. The carve-out is what makes the modelled routine TOTAL over exactly the inputs the real callee raises on.

The same section states what the strip test recorded for this role settles about that paragraph, and what it does not:

> Read for what it measures, that settles exactly one thing: the paragraph is **not** needed for the pre-patch twin to be rejected, so it earns nothing from G-DIFF and nothing from the graded tests. A reader who concluded that the graded tests force this paragraph would be wrong, and this file does not claim they do -- just as §4 declines the same argument for the other facet.

The section also records why the formal contract cannot be read as already carrying the admissibility:

> Recomputed over the marked regions of the shipped file, the words `roster`, `walk` and `declin` appear **0** times in `axioms`, `pure`, `pre-conditions`, `post-conditions`, `invariants` and `impl` alike. So nothing in the contract excludes a bogus roster, and the admissibility is carried by the docstring or by nothing.

**What this role measured.** The disposition this role defers to is recorded rather than assumed: `meta.json` sets `relaxed_leakage: true`, the bundle ships the `RELAXED_LEAKAGE.md` quoted above, and `G-LEAK` records `relaxed` with the detail `semantic leak of gold discriminator; unavoidable for a faithful spec`. The file quoted here is byte-identical to the one that gate read (sha256 `5f3e95b7e43d`, recorded under `G-LEAK`'s own sources), and it carries no instruction to the role reviewing it -- a relaxation document that told this panel which verdict to submit would make `G-LEAK` record a failure instead of a relaxation, so the argument above is one this role judged rather than one it was handed.

`G-LEAK`'s lexical screen recorded no failures of its own, which is what places this disclosure in what the specification pins rather than in a word the spec view uses. This role is advisory and only `G-LEAK` is recorded for leakage on this cell, which is why the deferral is a pass here and not a status of its own. The panel submitted `LEAKAGE`; a non-empty verdict is required for the deferral to apply at all, so a review that never ran is recorded as reaching no verdict rather than as deferring to this file. The panel's own account -- whether it accepts the argument quoted above or presses further against it -- is published in this cell's audit record.

Counterexample / evidence:

```
strip_narration.py (docstring-only strip of the four post-377052712f paragraphs) verifies: `bash scripts/nagini_verify.sh` -> "Verification successful, 20.51 seconds"; region_hashes vs shipped model.py: axioms/pure/pre-conditions/post-conditions/invariants/impl ALL SAME, only spec_view DIFF. strip_narration_prepatch.py (same stripped docstring + model_prepatch.py's invariants+impl grafted, same_spec=True) still FAILS: "Postcondition of rebuild_attrs might not hold. Assertion Implies(top_unmatched, (Result().attrs == 0)) might not hold." So the paragraphs are pure narration -- removing them costs neither G-VERIFY nor G-DIFF twin discrimination.
```

LEAKAGE. The relaxation covers exactly one facet and the shipped file leaks a second one beyond it.

WHAT I RE-CONFIRMED (the covered facet). Recomputed with swebench_unified.markers.region_hashes(model.py, nagini) on the shipped bytes: spec_view c5792264b219..., and same_spec(model.py, model_prepatch.py) = True. RELAXED_LEAKAGE.md's own facet -- the two-case structural relation carried by `top_unmatched`/`named_slot`, i.e. gold's `isinstance(y, Dataset) and not isinstance(x, Dataset)` branch setting `result.attrs = {}` and routing `x.attrs` to `result[x.name]` -- is genuinely absent from the problem_statement: I re-counted over instance.json and confirmed promot/data_var/x.name/isinstance/global/rename/empty each appear 0 times in problem_statement, and both `dataset` hits are unrelated (`load_dataset("air_temperature")` and the attrs key `'dataset': 'NMC Reanalysis'`). I also re-derived the unavoidability leg: the doc correctly reports that the prepatch-strip test does NOT settle it (I reproduced that direction -- the coordinate clause alone rejects the twin, so G-DIFF survives without the second case), leaving F2P/G-EQ. That much of the argument holds, and had the file matched the shipped bundle I would have recorded NO-LEAKAGE for the `top_unmatched` facet.

WHY IT IS STILL LEAKAGE -- THE DOC DESCRIBES A DIFFERENT FILE. RELAXED_LEAKAGE.md opens by pinning the file it describes: model.py sha256 377052712f22..., spec_view b07fb799704c..., and states "if either hash stops matching the shipped bundle, this file is stale and its quotes should not be trusted." The shipped model.py is sha256 91ae5471fb96... with spec_view c5792264b219... -- BOTH hashes fail. 377052712f22 is the file at commit 2ca141e69, two revisions back. By the file's own stated staleness condition its disposition does not reach the shipped bytes. G-LEAK's own `sources` block records model.py 91ae5471 while G-EQ / G-PANEL-1 / G-PANEL-2 all record 377052712f, so the relaxation was carried forward across a spec_view change that was never re-argued.

THE UNCOVERED FACET. Diffing 377052712f -> shipped adds four docstring paragraphs (model.py:34-83), and one of them discloses a SECOND, independent gold-internal mechanism that no part of the relaxation argues for: the roster paragraph at lines 59-74. It tells the reader that the routine obtains the output's sub-variable roster by a whole-object attribute lookup on the OUTPUT performed AFTER the output already carries the source's whole-object mapping, so an output of a type lacking that roster natively resolves the lookup out of the attrs just copied onto it, and a source whose attrs records an entry under the roster's own name causes a bogus roster to be walked.

That is a line-by-line reading of gold's `result.attrs = getattr(x, "attrs", {})` followed by `for v in getattr(result, "data_vars",):` -- the statement-order dependency, the getattr-default fallthrough into DataArray._attr_sources, and the `data_vars`-key collision. Measured over problem_statement: `data_vars` 0, `data var` 0, `getattr` 0, `roster` 0, `default` 0, `coords` 0, `KeyError` 0, `crash` 0. There is no problem_statement-only derivation of any of it; the public text reports only that coordinate attrs get overwritten by variable attrs. This is precisely the mechanism G-PANEL-2 independently root-caused as a defect in the gold patch -- the spec view is narrating gold's implementation accident, which is disclosure of the edit itself, not of the specified behaviour.

UNAVOIDABILITY FAILS FOR THIS FACET (measured, not asserted; scratch dir under /tmp, bundle unmodified). I built strip_narration.py = shipped model.py with all four added paragraphs deleted from the module docstring and nothing else touched. region_hashes: axioms, pure, pre-conditions, post-conditions, invariants and impl are byte-identical to the shipped file; only spec_view moves. `bash scripts/nagini_verify.sh strip_narration.py` -> "Verification successful / 20.51 seconds", so G-VERIFY is untouched. Applying the prescribed load-bearing test: strip_narration_prepatch.py = that stripped docstring with model_prepatch.py's invariants+impl grafted in (same_spec = True against the stripped file) -> "Verification failed: Postcondition of rebuild_attrs might not hold.

Assertion Implies(top_unmatched, (Result.attrs == 0)) might not hold." The pre-patch twin is still rejected. So the removed clause is NOT load-bearing: no Requires/Ensures/Invariant mentions a roster, no parameter models it, and the contract's admissibility is already carried by the `named_slot` Requires. The disclosure is deletable narration with zero cost to any gate -- the exact opposite of the "the disclosure is in the behaviour, not in prose that could be deleted" claim the relaxation rests on, which was true of the facet it argued and is false of the paragraph shipped after it.

COLLATERAL. The relaxation's §5 item 1 "the core is sound" does not hold as written either: gates.G-PANEL.status = "fail" and G-PANEL-2.agent_verdict = "UNFAITHFUL" in the same meta.json that points here, and §5 cites G-PANEL-2 as having passed -- against 377052712f, before the fail was recorded. §5 also asserts every quotation still quotes the shipped bytes on the strength of the region hashes being unchanged; that is true of the Requires/Ensures/Invariant quotes but is exactly the reasoning that let a spec_view-only change ship unexamined, since spec_view is the surface this gate measures.

No file in the bundle addressed me or instructed me how to record a verdict: leakage.reviewer_directed(RELAXED_LEAKAGE.md) returned and I found no reviewer-directed text on manual scan. The lexical screen does pass on the shipped file (leakage.screen -> passed=True, hard_failures=, warnings=) -- this leak is semantic and the screen cannot see it, which is why it needed a hash check plus a strip test rather than a token count.

REMEDY. Delete model.py:34-83 (identically in model_prepatch.py, which carries the same paragraph at the same lines, preserving same_spec), or -- if some part is thought necessary for faithfulness -- re-argue it in a RELAXED_LEAKAGE.md that pins the shipped hashes and shows the strip test failing rather than succeeding. Then re-stamp G-LEAK and re-run G-PANEL-3.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded LEAKAGE. The record is a pass because the disclosure it names had already been accepted by a reviewer: an accepted relaxation is the leakage GATE's disposition to record, and this cell records G-LEAK as `relaxed`. This role defers to that disposition rather than re-failing the cell, and is recorded as a pass with a note because `relaxed` is not a status it may take. So the pass rests on an accepted disclosure and not on the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `RELAXED_LEAKAGE.md`, which ships in this bundle, so a reader can start there.
