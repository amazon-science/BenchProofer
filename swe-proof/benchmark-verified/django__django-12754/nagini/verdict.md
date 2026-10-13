# P2 adversarial audit — django__django-12754

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_18.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_17.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,8 +98,9 @@
         c = candidates[i - 1]
         Assert(candidates.drop(i - 1)[0] == c)
         Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
-        if (not (c in parent_after)) and (c in child):
-            result = [c] + result
+        # Pre-patch: creating the child depends only on the parent existing; the
+        # withdrawal of a re-declared parent field is NOT made a prerequisite, so
+        # no qualifying name is ever emitted.
         i = i - 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(candidates)
+    i = len(candidates) - 1
     while i > 0:
         # invariants-start
         Invariant(Acc(set_pred(parent_after), 1 / 2))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
         c = candidates[i - 1]
         Assert(candidates.drop(i - 1)[0] == c)
         Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
-        if (not (c in parent_after)) and (c in child):
+        if c in child:
             result = [c] + result
         i = i - 1
     return result
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
         c = candidates[i - 1]
         Assert(candidates.drop(i - 1)[0] == c)
         Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
-        if (not (c in parent_after)) and (c in child):
+        if (not (c in parent_after)) or (c in child):
             result = [c] + result
         i = i - 1
     return result
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,6 +85,8 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
+    if len(candidates) > 1:
+        return result
     i = len(candidates)
     while i > 0:
         # invariants-start
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -101,5 +101,13 @@
         if (not (c in parent_after)) and (c in child):
             result = [c] + result
         i = i - 1
+    spin = 0
+    while spin >= 0:
+        Invariant(Acc(set_pred(parent_after), 1 / 2))
+        Invariant(Acc(set_pred(child), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(spin >= 0)
+        Invariant(ToSeq(result) == selected(candidates, parent_after, child))
+        spin = spin + 1
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -85,21 +85,16 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(candidates)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(selected(candidates, parent_after, child)):
         Invariant(Acc(set_pred(parent_after), 1 / 2))
         Invariant(Acc(set_pred(child), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(candidates))
-        Invariant(ToSeq(result) == selected(candidates.drop(i), parent_after, child))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = candidates[i - 1]
-        Assert(candidates.drop(i - 1)[0] == c)
-        Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
-        if (not (c in parent_after)) and (c in child):
-            result = [c] + result
-        i = i - 1
+        Invariant(0 <= i and i <= len(selected(candidates, parent_after, child)))
+        Invariant(ToSeq(result) == selected(candidates, parent_after, child).take(i))
+        Invariant(MustTerminate(len(selected(candidates, parent_after, child)) - i + 1))
+        result.append(selected(candidates, parent_after, child)[i])
+        i = i + 1
+    Assert(ToSeq(result) == selected(candidates, parent_after, child).take(i))
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,7 +99,8 @@
         Assert(candidates.drop(i - 1)[0] == c)
         Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
         if (not (c in parent_after)) and (c in child):
-            result = [c] + result
+            if len(result) == 0:
+                result = [c] + result
         i = i - 1
     return result
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,7 +99,8 @@
         Assert(candidates.drop(i - 1)[0] == c)
         Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
         if (not (c in parent_after)) and (c in child):
-            result = [c] + result
+            if len(result) == 0 or result[0] != c:
+                result = [c] + result
         i = i - 1
     return result
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
         c = candidates[i - 1]
         Assert(candidates.drop(i - 1)[0] == c)
         Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
-        if (not (c in parent_after)) and (c in child):
+        if (c in parent_after) and (not (c in child)):
             result = [c] + result
         i = i - 1
     return result
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -100,6 +100,6 @@
         Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
         if (not (c in parent_after)) and (c in child):
             result = [c] + result
-        i = i - 1
+        i = i - 2
     return result
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -100,6 +100,7 @@
         Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
         if (not (c in parent_after)) and (c in child):
             result = [c] + result
+            result = [c] + result
         i = i - 1
     return result
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -84,6 +84,7 @@
     Ensures(ToSeq(Result()) == selected(candidates, parent_after, child))
     # post-conditions-end
     # impl-start
+    Assert(False)
     result = []  # type: List[int]
     i = len(candidates)
     while i > 0:
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -101,5 +101,6 @@
         if (not (c in parent_after)) and (c in child):
             result = [c] + result
         i = i - 1
+    result = result + [424242]
     return result
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -101,5 +101,8 @@
         if (not (c in parent_after)) and (c in child):
             result = [c] + result
         i = i - 1
+    if len(candidates) > 0 and not (candidates[0] in parent_after):
+        if len(result) > 0 and result[0] == candidates[0]:
+            result = result[1:]
     return result
     # impl-end
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,21 +85,16 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(candidates)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(candidates):
         Invariant(Acc(set_pred(parent_after), 1 / 2))
         Invariant(Acc(set_pred(child), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(candidates))
-        Invariant(ToSeq(result) == selected(candidates.drop(i), parent_after, child))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = candidates[i - 1]
-        Assert(candidates.drop(i - 1)[0] == c)
-        Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
+        Invariant(MustTerminate(len(candidates) - i + 1))
+        c = candidates[i]
         if (not (c in parent_after)) and (c in child):
             result = [c] + result
-        i = i - 1
+        i = i + 1
     return result
     # impl-end
```

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -85,21 +85,15 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(candidates)
+    i = len(selected(candidates, parent_after, child))
     while i > 0:
-        # invariants-start
         Invariant(Acc(set_pred(parent_after), 1 / 2))
         Invariant(Acc(set_pred(child), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(candidates))
-        Invariant(ToSeq(result) == selected(candidates.drop(i), parent_after, child))
+        Invariant(0 <= i and i <= len(selected(candidates, parent_after, child)))
+        Invariant(ToSeq(result) == selected(candidates, parent_after, child).drop(i))
         Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = candidates[i - 1]
-        Assert(candidates.drop(i - 1)[0] == c)
-        Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
-        if (not (c in parent_after)) and (c in child):
-            result = [c] + result
+        result = [selected(candidates, parent_after, child)[i - 1]] + result
         i = i - 1
     return result
     # impl-end
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,21 +85,17 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(candidates)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(selected(candidates, parent_after, child)):
         Invariant(Acc(set_pred(parent_after), 1 / 2))
         Invariant(Acc(set_pred(child), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(candidates))
-        Invariant(ToSeq(result) == selected(candidates.drop(i), parent_after, child))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = candidates[i - 1]
-        Assert(candidates.drop(i - 1)[0] == c)
-        Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
-        if (not (c in parent_after)) and (c in child):
-            result = [c] + result
-        i = i - 1
+        Invariant(0 <= i and i <= len(selected(candidates, parent_after, child)))
+        Invariant(ToSeq(result) == selected(candidates, parent_after, child).take(i))
+        Invariant(MustTerminate(len(selected(candidates, parent_after, child)) - i + 1))
+        result.append(selected(candidates, parent_after, child)[i])
+        i = i + 1
+    if len(candidates) > 0 and len(result) == 0:
+        result.append(candidates[0])
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12754.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a newly introduced record kind inherits from an existing parent record
  kind, creating the child kind must be sequenced AFTER any field of the parent
  whose name the child re-declares has been withdrawn from the parent. Otherwise
  the two kinds would momentarily both own a field of the same name, which is
  not allowed for an inheriting kind.

  Concretely, three name-sets describe one parent: the names the parent owned
  in the prior state (``parent_before``), the names it owns in the target state
  (``parent_after``), and the names the child declares (``child``). A parent
  field name must be withdrawn-before-the-child precisely when it was owned by
  the parent before, is no longer owned by the parent after (i.e. it was
  withdrawn), AND is re-declared by the child (a clash). For each such name the
  child's creation gains an ordering prerequisite on that name's withdrawal; no
  other name contributes a prerequisite.

Field names are modelled as integer identifiers (the only operations performed
on them are set membership and equality — never any character-level operation);
the parent's target names and the child's names are ``PSet[int]``; the candidate
names iterated are the parent's prior names as a ``PSeq[int]``; the emitted
prerequisites are the ``List[int]`` filtered subsequence of qualifying names.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees. The qualifying-name selection is a set
# difference-then-intersection, modelled DEEPLY over PSet[int] / PSeq[int]: a
# name qualifies iff it is in the parent's prior names, absent from the parent's
# target names, and present in the child's names. The underlying set operations
# (membership, difference, intersection) are unchanged primitives refined to
# PSet membership, not axioms the proof consumes — see refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def qualifies(name: int, parent_after: PSet[int], child: PSet[int]) -> bool:
    """A candidate parent field name (already known to be a prior parent name)
    needs withdrawing-before-the-child exactly when it is no longer owned by the
    parent after (withdrawn) and is re-declared by the child (a clash)."""
    Requires(Acc(set_pred(parent_after), 1 / 4))
    Requires(Acc(set_pred(child), 1 / 4))
    return (not (name in parent_after)) and (name in child)


@Pure
def selected(candidates: PSeq[int], parent_after: PSet[int],
             child: PSet[int]) -> PSeq[int]:
    """The prerequisites for one parent: the subsequence of the parent's prior
    field names that qualify (withdrawn-from-parent AND re-declared-by-child),
    in candidate order. Front-recursive so a single unfold is available to the
    loop."""
    Requires(Acc(set_pred(parent_after), 1 / 4))
    Requires(Acc(set_pred(child), 1 / 4))
    if len(candidates) == 0:
        return PSeq(0).take(0)
    if qualifies(candidates[0], parent_after, child):
        return PSeq(candidates[0]) + selected(candidates.drop(1), parent_after, child)
    return selected(candidates.drop(1), parent_after, child)
# pure-end


def removed_base_field_prereqs(candidates: PSeq[int], parent_after: PSet[int],
                               child: PSet[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(set_pred(parent_after), 1 / 2))
    Requires(Acc(set_pred(child), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(parent_after), 1 / 2))
    Ensures(Acc(set_pred(child), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The emitted prerequisites are exactly the qualifying candidate names, in
    # candidate order: the deep set difference-then-intersection.
    Ensures(ToSeq(Result()) == selected(candidates, parent_after, child))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(candidates)
    while i > 0:
        # invariants-start
        Invariant(Acc(set_pred(parent_after), 1 / 2))
        Invariant(Acc(set_pred(child), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(candidates))
        Invariant(ToSeq(result) == selected(candidates.drop(i), parent_after, child))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = candidates[i - 1]
        Assert(candidates.drop(i - 1)[0] == c)
        Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
        if (not (c in parent_after)) and (c in child):
            result = [c] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, 18 attacks, all fully verified; no host-cap timeouts in any weakness log. Attacks edited ONLY the impl region (spliced programmatically around the `# impl-start`/`# impl-end` markers so axioms/@Pure/Requires/Ensures stay byte-identical).

**POSITIVE CONTROL:** pos_control.py (verbatim model.py) => CANDIDATE (shares spec AND verifies, 19.4s). PREPATCH REPRODUCED: atk_1.py = model_prepatch.py verbatim (loop emits nothing) => rc=2, verification failed, i.e. the spec senses the change (G-DIFF).

REJECTED (rc=2, spec caught them) — 16 of 18:
- atk_1 prepatch bug (emits no prerequisite at all)
- atk_2 boundary: starts at len(candidates)-1, drops a qualifying LAST prior name
- atk_3 over-emission: drops the withdrawn-from-parent conjunct (kept fields become prereqs)
- atk_4 wrong connective: `or` for `and`
- atk_5 partial domain: correct only when the parent had <=1 prior field, else emits nothing
- atk_6 control-flow effect: correct answer then a non-terminating `while spin >= 0` loop — MustTerminate(2) at the METHOD level rejects it (loop invariants alone would not)
- atk_8 first-only: emits at most one prerequisite (passes a 1-clash scenario, wrong for 2)
- atk_9 dedupe: at-most-once emission — behaviourally identical to gold in the real repo (set(old) has no dup keys) yet still rejected, so the spec is if anything tighter than needed here, not looser
- atk_10 swapped conjuncts: kept-by-parent AND not-re-declared
- atk_11 stride-2: inspects every other prior name
- atk_12 double emission: each qualifying name twice
- atk_13 VACUITY CONTROL: `Assert(False)` at the head of an otherwise-correct impl => REJECTED, so the precondition is satisfiable and none of the other verdicts are vacuous
- atk_14 fabricated prereq: appends a name (424242) that is not a prior parent field
- atk_15 partial domain on parent_after: drops the first qualifying name in a boundary case
- atk_16 order flip: same multiset, reversed order
- atk_18 ECHO + SHADOW BUG: oracle echo that ALSO emits a bogus prereq when nothing was withdrawn => REJECTED. This is the decisive control: the echo SHAPE cannot smuggle a real behavioural difference past the verifier, because the postcondition ToSeq(Result()) == selected(...) pins the output exactly.

CANDIDATES (rc=0, verify) — 2 of 18, both materialized and RUN through the official harness:
- atk_7.py (ungrounded-oracle echo: indexes the spec's own @Pure `selected` front-to-back instead of computing the filter). Faithful patch patch_atk7.diff (real set difference-then-intersection, prereqs emitted via an index `while` loop mirroring the model's indexed walk). Command: `python3 resolve.py patch_atk7.diff` calling swebench_unified.harness.run_resolve. RESULT: RESOLVED=True COMPLETED=True ATTEMPTS=2 FLAKY=True, patch_successfully_applied=true, F2P success=[test_add_model_with_field_removed_from_base_model], F2P failure=[], P2P failure=[]. => DOES resolve, not a counterexample.
- atk_17.py (second, structurally different echo: builds the answer back-to-front out of `selected`). Faithful patch patch_atk17.diff (back-to-front `emitted` list assembled from the real set expr, then appended). RESULT: RESOLVED=True COMPLETED=True ATTEMPTS=1 FLAKY=False, F2P failure=[], P2P failure=[]. => DOES resolve.

**HARNESS-LANE CONTROL:** the gold patch.diff run through the same resolve.py => RESOLVED=True COMPLETED=True (ATTEMPTS=2, FLAKY=True), so the lane is healthy and the two candidate resolves are trustworthy measurements rather than infra artifacts. NOTE on process: my FIRST atk_7 patch was hand-written and had a bad hunk header (`git apply --check` => 'corrupt patch at line 25'); that run returned RESOLVED=False COMPLETED=False, a harness NON-COMPLETION, and I discarded it rather than scoring it as a break — per the rule that a cap/infra failure is not a verdict. Both patches were then regenerated with `git diff` in a base_commit worktree and `git apply --check`-verified before resolving.

**Why the echoes are not breaks:** an oracle echo is behaviourally EQUAL to the spec's intent by construction, so its faithful refinement is the gold behaviour and it resolves. The echo is a proof-style artifact (it reads the answer from @Pure `selected` rather than recomputing it), not a wrong implementation — G-EQ asks for a WRONG impl that verifies. atk_18 demonstrates the boundary: as soon as the echo is perturbed to differ behaviourally, the verifier rejects it.

A-LEG AUDIT (refinement.md). Leg tags: 4 R + 1 A-reference + 1 I, zero A-consumed, and `grep -c @ContractOnly model.py` = 0, so the claim of no consumed axiom is literally true and §B's no-kind-3 statement holds. The single A-leg is A4, `selected` == `set(old).difference(new).intersection(model)`, an A-REFERENCE (deep model validated out-of-band, not consumed). Checked against the real tree at base_commit 18759b2209ff556aed7f20d83cbf23e3d234e41c in the upstream repository:
- cited line numbers are right: `for base in model_state.bases:` at autodetector.py:562, `dependencies.append((base_app_label, base_name, None, True))` at 565 (the first of two occurrences; the second at 691/694 is generate_created_proxies, correctly NOT the modeled site), `check_dependency` at 374 with the 'Removed field' branch at 399 requiring RemoveField + model_name_lower + name_lower — exactly the (base, base, field, False) tuple shape A5 claims.
- A5/A6 'order and duplication are immaterial' is CORROBORATED in the real code, not merely asserted: `_auto_deps` is consumed at line 288 into `dependencies = set()` / `operation_dependencies.add(...)` and at 352 into `dependency_graph[op].add(op2)` before `stable_topological_sort`. Both are set-valued, so the model pinning candidate ORDER is strictly stronger than the real code observes — the safe direction for a verify=>correct claim. atk_9 (dedupe) and atk_16 (order flip) being rejected confirms the model is tighter, never looser, on this axis.
- axiom_check.py (G-AX) exits 0: 'deep model `selected` == real set(old).difference(new).intersection(model) on 13 boundary + 20000 fuzz (int) + 5 str-name faithfulness cases, 0 mismatch'. It genuinely calls the CPython built-in set algebra (`set(old).difference(new).intersection(model)`) and asserts membership equality, and additionally re-runs with real `str` names, which validates the int-for-str R-refinement of mapping.md §2 (only membership/equality/hashing is performed on the keys). Every emitted name is also asserted to be a prior parent name, which is what closes the A1 candidates-enumerate-old side condition.
- the A1 guard note is correct: the modeled function is entered exactly under `if old_base_model_state and new_base_model_state:`, so the missing-state case is out of the modeled domain rather than silently mismodelled.
Minor, non-blocking: conformance_check.py cannot run in this shell (ModuleNotFoundError: django) — it needs the repo env; it is not a G-EQ artifact and its absence does not affect any A-leg conclusion above.

**VERDICT SOUND:** 18 attacks (>=5 required) all fully verified with no timeouts; 16 rejected including the prepatch bug and the Assert(False) vacuity control; the 2 that verified are oracle echoes whose materialized faithful patches BOTH resolved under the official harness (with a gold-patch lane control also resolving). No verifying wrong impl whose faithful refined patch fails to resolve was found; refinement.md's legs are all R / A-reference / I with the A-reference's correspondence to the real callee confirmed against the base_commit source.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_18.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_17.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 18 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12754.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a newly introduced record kind inherits from an existing parent record
  kind, creating the child kind must be sequenced AFTER any field of the parent
  whose name the child re-declares has been withdrawn from the parent. Otherwise
  the two kinds would momentarily both own a field of the same name, which is
  not allowed for an inheriting kind.

  Concretely, three name-sets describe one parent: the names the parent owned
  in the prior state (``parent_before``), the names it owns in the target state
  (``parent_after``), and the names the child declares (``child``). A parent
  field name must be withdrawn-before-the-child precisely when it was owned by
  the parent before, is no longer owned by the parent after (i.e. it was
  withdrawn), AND is re-declared by the child (a clash). For each such name the
  child's creation gains an ordering prerequisite on that name's withdrawal; no
  other name contributes a prerequisite.

Field names are modelled as integer identifiers (the only operations performed
on them are set membership and equality — never any character-level operation);
the parent's target names and the child's names are ``PSet[int]``; the candidate
names iterated are the parent's prior names as a ``PSeq[int]``; the emitted
prerequisites are the ``List[int]`` filtered subsequence of qualifying names.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees. The qualifying-name selection is a set
# difference-then-intersection, modelled DEEPLY over PSet[int] / PSeq[int]: a
# name qualifies iff it is in the parent's prior names, absent from the parent's
# target names, and present in the child's names. The underlying set operations
# (membership, difference, intersection) are unchanged primitives refined to
# PSet membership, not axioms the proof consumes — see refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def qualifies(name: int, parent_after: PSet[int], child: PSet[int]) -> bool:
    """A candidate parent field name (already known to be a prior parent name)
    needs withdrawing-before-the-child exactly when it is no longer owned by the
    parent after (withdrawn) and is re-declared by the child (a clash)."""
    Requires(Acc(set_pred(parent_after), 1 / 4))
    Requires(Acc(set_pred(child), 1 / 4))
    return (not (name in parent_after)) and (name in child)


@Pure
def selected(candidates: PSeq[int], parent_after: PSet[int],
             child: PSet[int]) -> PSeq[int]:
    """The prerequisites for one parent: the subsequence of the parent's prior
    field names that qualify (withdrawn-from-parent AND re-declared-by-child),
    in candidate order. Front-recursive so a single unfold is available to the
    loop."""
    Requires(Acc(set_pred(parent_after), 1 / 4))
    Requires(Acc(set_pred(child), 1 / 4))
    if len(candidates) == 0:
        return PSeq(0).take(0)
    if qualifies(candidates[0], parent_after, child):
        return PSeq(candidates[0]) + selected(candidates.drop(1), parent_after, child)
    return selected(candidates.drop(1), parent_after, child)
# pure-end


def removed_base_field_prereqs(candidates: PSeq[int], parent_after: PSet[int],
                               child: PSet[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(set_pred(parent_after), 1 / 2))
    Requires(Acc(set_pred(child), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(parent_after), 1 / 2))
    Ensures(Acc(set_pred(child), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The emitted prerequisites are exactly the qualifying candidate names, in
    # candidate order: the deep set difference-then-intersection.
    Ensures(ToSeq(Result()) == selected(candidates, parent_after, child))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(candidates)
    while i > 0:
        # invariants-start
        Invariant(Acc(set_pred(parent_after), 1 / 2))
        Invariant(Acc(set_pred(child), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(candidates))
        Invariant(ToSeq(result) == selected(candidates.drop(i), parent_after, child))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = candidates[i - 1]
        Assert(candidates.drop(i - 1)[0] == c)
        Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))
        if (not (c in parent_after)) and (c in child):
            result = [c] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, 18 attacks, all fully verified; no host-cap timeouts in any weakness log. Attacks edited ONLY the impl region (spliced programmatically around the `# impl-start`/`# impl-end` markers so axioms/@Pure/Requires/Ensures stay byte-identical).

**POSITIVE CONTROL:** pos_control.py (verbatim model.py) => CANDIDATE (shares spec AND verifies, 19.4s). PREPATCH REPRODUCED: atk_1.py = model_prepatch.py verbatim (loop emits nothing) => rc=2, verification failed, i.e. the spec senses the change (G-DIFF).

REJECTED (rc=2, spec caught them) — 16 of 18:
- atk_1 prepatch bug (emits no prerequisite at all)
- atk_2 boundary: starts at len(candidates)-1, drops a qualifying LAST prior name
- atk_3 over-emission: drops the withdrawn-from-parent conjunct (kept fields become prereqs)
- atk_4 wrong connective: `or` for `and`
- atk_5 partial domain: correct only when the parent had <=1 prior field, else emits nothing
- atk_6 control-flow effect: correct answer then a non-terminating `while spin >= 0` loop — MustTerminate(2) at the METHOD level rejects it (loop invariants alone would not)
- atk_8 first-only: emits at most one prerequisite (passes a 1-clash scenario, wrong for 2)
- atk_9 dedupe: at-most-once emission — behaviourally identical to gold in the real repo (set(old) has no dup keys) yet still rejected, so the spec is if anything tighter than needed here, not looser
- atk_10 swapped conjuncts: kept-by-parent AND not-re-declared
- atk_11 stride-2: inspects every other prior name
- atk_12 double emission: each qualifying name twice
- atk_13 VACUITY CONTROL: `Assert(False)` at the head of an otherwise-correct impl => REJECTED, so the precondition is satisfiable and none of the other verdicts are vacuous
- atk_14 fabricated prereq: appends a name (424242) that is not a prior parent field
- atk_15 partial domain on parent_after: drops the first qualifying name in a boundary case
- atk_16 order flip: same multiset, reversed order
- atk_18 ECHO + SHADOW BUG: oracle echo that ALSO emits a bogus prereq when nothing was withdrawn => REJECTED. This is the decisive control: the echo SHAPE cannot smuggle a real behavioural difference past the verifier, because the postcondition ToSeq(Result()) == selected(...) pins the output exactly.

CANDIDATES (rc=0, verify) — 2 of 18, both materialized and RUN through the official harness:
- atk_7.py (ungrounded-oracle echo: indexes the spec's own @Pure `selected` front-to-back instead of computing the filter). Faithful patch patch_atk7.diff (real set difference-then-intersection, prereqs emitted via an index `while` loop mirroring the model's indexed walk). Command: `python3 resolve.py patch_atk7.diff` calling swebench_unified.harness.run_resolve. RESULT: RESOLVED=True COMPLETED=True ATTEMPTS=2 FLAKY=True, patch_successfully_applied=true, F2P success=[test_add_model_with_field_removed_from_base_model], F2P failure=[], P2P failure=[]. => DOES resolve, not a counterexample.
- atk_17.py (second, structurally different echo: builds the answer back-to-front out of `selected`). Faithful patch patch_atk17.diff (back-to-front `emitted` list assembled from the real set expr, then appended). RESULT: RESOLVED=True COMPLETED=True ATTEMPTS=1 FLAKY=False, F2P failure=[], P2P failure=[]. => DOES resolve.

**HARNESS-LANE CONTROL:** the gold patch.diff run through the same resolve.py => RESOLVED=True COMPLETED=True (ATTEMPTS=2, FLAKY=True), so the lane is healthy and the two candidate resolves are trustworthy measurements rather than infra artifacts. NOTE on process: my FIRST atk_7 patch was hand-written and had a bad hunk header (`git apply --check` => 'corrupt patch at line 25'); that run returned RESOLVED=False COMPLETED=False, a harness NON-COMPLETION, and I discarded it rather than scoring it as a break — per the rule that a cap/infra failure is not a verdict. Both patches were then regenerated with `git diff` in a base_commit worktree and `git apply --check`-verified before resolving.

**Why the echoes are not breaks:** an oracle echo is behaviourally EQUAL to the spec's intent by construction, so its faithful refinement is the gold behaviour and it resolves. The echo is a proof-style artifact (it reads the answer from @Pure `selected` rather than recomputing it), not a wrong implementation — G-EQ asks for a WRONG impl that verifies. atk_18 demonstrates the boundary: as soon as the echo is perturbed to differ behaviourally, the verifier rejects it.

A-LEG AUDIT (refinement.md). Leg tags: 4 R + 1 A-reference + 1 I, zero A-consumed, and `grep -c @ContractOnly model.py` = 0, so the claim of no consumed axiom is literally true and §B's no-kind-3 statement holds. The single A-leg is A4, `selected` == `set(old).difference(new).intersection(model)`, an A-REFERENCE (deep model validated out-of-band, not consumed). Checked against the real tree at base_commit 18759b2209ff556aed7f20d83cbf23e3d234e41c in the upstream repository:
- cited line numbers are right: `for base in model_state.bases:` at autodetector.py:562, `dependencies.append((base_app_label, base_name, None, True))` at 565 (the first of two occurrences; the second at 691/694 is generate_created_proxies, correctly NOT the modeled site), `check_dependency` at 374 with the 'Removed field' branch at 399 requiring RemoveField + model_name_lower + name_lower — exactly the (base, base, field, False) tuple shape A5 claims.
- A5/A6 'order and duplication are immaterial' is CORROBORATED in the real code, not merely asserted: `_auto_deps` is consumed at line 288 into `dependencies = set()` / `operation_dependencies.add(...)` and at 352 into `dependency_graph[op].add(op2)` before `stable_topological_sort`. Both are set-valued, so the model pinning candidate ORDER is strictly stronger than the real code observes — the safe direction for a verify=>correct claim. atk_9 (dedupe) and atk_16 (order flip) being rejected confirms the model is tighter, never looser, on this axis.
- axiom_check.py (G-AX) exits 0: 'deep model `selected` == real set(old).difference(new).intersection(model) on 13 boundary + 20000 fuzz (int) + 5 str-name faithfulness cases, 0 mismatch'. It genuinely calls the CPython built-in set algebra (`set(old).difference(new).intersection(model)`) and asserts membership equality, and additionally re-runs with real `str` names, which validates the int-for-str R-refinement of mapping.md §2 (only membership/equality/hashing is performed on the keys). Every emitted name is also asserted to be a prior parent name, which is what closes the A1 candidates-enumerate-old side condition.
- the A1 guard note is correct: the modeled function is entered exactly under `if old_base_model_state and new_base_model_state:`, so the missing-state case is out of the modeled domain rather than silently mismodelled.
Minor, non-blocking: conformance_check.py cannot run in this shell (ModuleNotFoundError: django) — it needs the repo env; it is not a G-EQ artifact and its absence does not affect any A-leg conclusion above.

**VERDICT SOUND:** 18 attacks (>=5 required) all fully verified with no timeouts; 16 rejected including the prepatch bug and the Assert(False) vacuity control; the 2 that verified are oracle echoes whose materialized faithful patches BOTH resolved under the official harness (with a gold-patch lane control also resolving). No verifying wrong impl whose faithful refined patch fails to resolve was found; refinement.md's legs are all R / A-reference / I with the A-reference's correspondence to the real callee confirmed against the base_commit source.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Reference = base_commit worktree with patch.diff APPLIED (fresh clone of django_django.git at 18759b2209ff, patch applied clean). bundle untouched (read-only).

**MODELED FUNCTION:** removed_base_field_prereqs(candidates: PSeq[int], parent_after: PSet[int], child: PSet[int]) -> List[int], with the sole behavioral postcondition ToSeq(Result()) == selected(candidates, parent_after, child), where selected keeps candidates c with qualifies(c) = (c not in parent_after) and (c in child).

REAL CALLEE (post-patch autodetector.py:566-575): under the guard `if old_base_model_state and new_base_model_state:`, set(old_base_model_state.fields).difference(new_base_model_state.fields).intersection(model_state.fields), one dependency (base_app_label, base_name, removed_base_field, False) appended per element.

### WHAT I RAN (independent of the bundle's own harnesses):
1. Pinned verifier on model.py: 'Verification successful' (16.8s, exit 0).
2. Bundle harnesses reproduced: axiom_check.py exit 0; conformance_check.py against MY patched worktree -> 'G-CONF OK... 100001 modeled inputs, 0 disagreements'.
3. MY OWN differential harness (indep2.py) deliberately NOT reusing the bundle's duck types: real django.db.migrations.state.ModelState / ProjectState, real MigrationAutodetector.generate_created_models, real str field names, emissions read off the recorded CreateModel.`_auto_deps`. Two domains: (A) 601 cases through the FULLY REAL state-render path (to_state legal, i.e. child disjoint from parent_after -- Django's own FieldError blocks anything else); (B) 6000 cases with real ModelState dicts + stub apps covering the broader domain including states Django would reject. RESULT: 0 membership divergences in all 6601 cases. (An early run showed ~3600 'divergences' -- that was MY harness bug: ProjectState.add_model keys the registry by name_lower, so base string 'app.Parent' hit the guard arm every time. Fixed to 'app.parent'; divergences went to 0. Recording this so the false alarm is not mistaken for a finding.)

THE ONE REAL SEAM -- ORDER, and why it is not a divergence: the spec pins emission order to candidate order, whereas CPython set iteration order is arbitrary. My harness saw 69/601 and 928/6000 order-only mismatches (membership identical). I did NOT accept refinement.md's argument on this; I tested it. Both consumers of `_auto_deps` fold it into sets: `_build_migration_list` (dependencies = set(); operation_dependencies = set()) and `_sort_migrations` (dependency_graph[op] = set(), then stable_topological_sort whose layers are sets and whose stability derives from the OPERATION list order, not dep order). End-to-end test (order.py): for 400 sampled states restricted to >=2 qualifying fields (so order can matter), I monkeypatched add_operation to force arbitrary permutations of the removed-field dependency tuples and diffed the full `_detect_changes`() migration plan -- 896 permutation trials, 0 observable output differences. Order is unobservable; the spec pinning it is a strengthening of an unobservable, not a disagreement with the real callee on any observable.

OTHER SEAMS PROBED, all clean:
- int-for-str relabeling at its sharpest point: check_dependency compares dependency[2].lower() while the model uses exact int equality, so names colliding under.lower() are the danger. Tested ['Title','title'], ['aB','Ab','ab','AB'], ['ID','id'], ['f','F'] with various withdrawn/kept splits (casetest.py): 0 membership divergences. The modeled SITE performs only set membership/hashing/equality on the keys; the.lower() folding happens strictly downstream of the modeled function, so it is outside the model's scope and does not make the model too strong.
- guard arm: the model's precondition corresponds to `if old_base_model_state and new_base_model_state`. Confirmed ModelState defines neither `__bool__` nor `__len__`, so a ModelState with fields=={} is still truthy -- the guard is 'entry present', exactly what 'the modeled function is entered' means. No empty-fields state is silently excluded. My harness also asserted the real pass emits nothing for absent-prior / absent-target / dotless bases.
- duplicate candidates: the PSeq domain admits (1,1,2) where selected returns (1,1,2). Unreachable in reality -- candidates enumerates set(old_base_model_state.fields), and dict keys are distinct -- and a WIDER model domain cannot make the spec too strong on any reachable input.

No consumed @ContractOnly axiom exists in this bundle, so there is no axiom whose Ensures could over-promise; the changed set operation is modeled deeply and I validated it against real CPython set algebra directly.

**CONCLUSION:** for every input reachable at the modeled site, the modeled function's result set equals the real post-patch callee's emitted set. I found no diverging input. The only representational difference (emission order) is provably unobservable downstream by construction and by 896 end-to-end permutation trials. Spec is not too strong and does not drift from real repo behavior: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. No relaxation in this bundle: meta.json has no `relaxed_leakage` key (grep -c relaxed_leakage meta.json = 0; 'relaxed_leakage' not in json.dumps(meta)), there is no RELAXED_LEAKAGE.md, and gates.G-LEAK.status == 'pass' (not 'relaxed'). So this is an ordinary strict leakage judgement, not an inherited disposition.

### WHAT I MEASURED (not what the bundle asserts).
1. Canonical spec view, derived myself: markers.spec_view(model.py, get_backend('nagini')) -> sha256 5741d1acc773365e901c559f3ee11b62466a3e2cfd79a5d4d2ddb77e80ed166d, byte-equal to meta gates.G-HYGIENE.data.region_hashes.spec_view. same_spec(model.py, model_prepatch.py) = True and both spec views hash identically, so the view I judged is the frozen one and the prepatch twin shares it exactly.
2. Independent G-LEAK re-run (leakage.screen(model.py, nagini backend, instance['patch'], instance['problem_statement'], instance['test_patch'])): passed=True, hard_failures=[], warnings=[]. leakage.reviewer_directed() = [] on every bundle.py/.md (model.py, model_prepatch.py, refinement.md, mapping.md, verdict.md, axiom_check.py, conformance_check.py, properties.py).
3. Vocabulary sweep of the spec view against the SOLVER-VISIBLE problem_statement only (hints_text deliberately excluded). Absent from the spec view: autodetector, generate_created_models, dependencies/dependenc, from_state, to_state, ModelState,.fields, model_state, base_app_label, base_name, check_dependency, CreateModel, RemoveField, migrat*, FieldError, and the issue's concrete names (title/Readable/Book). No diff markers, no patched path django/db/migrations/autodetector.py, no dotted module path. Only 'django' appears (in the instance id in the docstring header), and it is public via the instance/problem statement.
4. Gold-added-token cross-check: of all identifier tokens on '+' lines of the gold hunk, the only non-stopword tokens appearing in the spec view are 'difference', 'intersection' (as the English prose 'difference-then-intersection', 3 occurrences) and 'removed_base_field' (as a substring of the model function name removed_base_field_prereqs). I judged both and neither leaks:
   - 'difference-then-intersection' is a restatement in words of the predicate the spec view ALREADY states formally and necessarily: qualifies(name, parent_after, child) == (not name in parent_after) and (name in child), over candidates that are the parent's prior names. The spec cannot exist without that membership condition, so the prose adds zero information over the contract it paraphrases; it names no file, function, repo API, or line.
   - removed_base_field_prereqs is not a repo symbol at base_commit: I grepped the base_commit worktree (git worktree add --detach 18759b2209ff556aed7f20d83cbf23e3d234e41c) for 'removed_base_field' and it does not exist anywhere in django/ (only unrelated base_field/base_fields in forms/, postgres/). It coincides with a LOCAL VARIABLE the gold hunk introduces, and its every component word is public in the problem_statement: 'RemoveField' (True), 'base class' (True), 'field' (True). A model-side name assembled from the issue's own vocabulary localizes nothing. leakage.`_patch_changed_symbols`(gold) = {'generate_created_models'} and no spec-view identifier embeds it (idents: Acc, Ensures, List, MustTerminate, PSeq, PSet, Pure, Requires, Result, ToSeq, bool, candidates, child, int, len, list_pred, name, parent_after, qualifies, removed_base_field_prereqs, selected, set_pred).
5. Load-bearing / de-narration control, run in /tmp (never in the bundle): I mechanically stripped the module docstring, both @Pure docstrings, and every non-marker comment from BOTH twins and re-ran the pinned verifier. denarrated_gold.py -> 'Verification successful' (exit 0); denarrated_prepatch.py -> 'Verification failed', loop invariant ToSeq(result) == selected(candidates.drop(i), parent_after, child) not preserved (exit 1). So the discriminator is carried ENTIRELY by the formal contract; no prose clause is load-bearing. That cuts the only way this could have been a hidden relaxation: the spec needs no narration to be faithful, and the narration it does carry is a paraphrase of the contract rather than a diagnosis of the edit.
6. Supporting gates I re-ran rather than read: bundle patch.diff == instance['patch'] verbatim (True). nagini_verify.sh model.py -> exit 0 (13.2s). nagini_verify.sh model_prepatch.py -> exit 1, same invariant (G-DIFF sound: the spec senses the change). axiom_check.py -> exit 0, 0 mismatch on 13 boundary + 20000 int fuzz + 5 str-name cases.

**DERIVABILITY.** The single behavioral claim the spec view formalizes -- a parent field name is a withdrawn-before-child ordering prerequisite iff owned-before AND absent-after AND re-declared-by-child -- is directly derivable from the public problem_statement, which gives the exact instance (title on Readable removed, title declared on subclass Book, resulting clash) and the required remedy verbatim ('Reversing the order of the migration operations makes it pass. The auto-detector should be able to use this order.'). Nothing in the spec view requires hints_text vocabulary; the hints-only diagnosis (adjust check_dependency / append (base_app_label, base_model_name, field_name, False) in generate_created_models) appears nowhere in the view. The concrete edit site and the dependency-tuple mechanism live only in mapping.md and refinement.md, which are audit documents and not part of the consumer spec view (eval/prompts.py:`_spec_block` ships task.spec_view alone; adapter.spec_view refuses an unelided view).

OBSERVATION worth recording (not a leakage finding, and not reviewer-directed text -- reviewer_directed() is clean on it). The bundle ships verdict.md, a generated summary that states this very role's prior outcome: 'Role 4 -- G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)', with its full reasoning. Nothing in it instructs me how to record or which verdict is honest, so it is not the artifact steering its reviewer in the reviewer_directed sense; but it does disclose the expected verdict for my own role to me before I judge, which is an anchoring surface a leakage panel should not normally be handed. My verdict above is derived from the measurements in items 1-6, all re-run in /tmp against the pinned verifier and the frozen instance row, and I reached NO-LEAKAGE on the spec view before consulting that section's argument. verdict.md is not part of the consumer spec view, so it leaks nothing to a solver.

**Housekeeping:** worktree and scratch are mine; the bundle was never modified (read-only access plus copies into /tmp).

**SCOPE.** No relaxation in this bundle: meta.json has no `relaxed_leakage` key (grep -c relaxed_leakage meta.json = 0; 'relaxed_leakage' not in json.dumps(meta)), there is no RELAXED_LEAKAGE.md, and gates.G-LEAK.status == 'pass' (not 'relaxed'). So this is an ordinary strict leakage judgement, not an inherited disposition.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
