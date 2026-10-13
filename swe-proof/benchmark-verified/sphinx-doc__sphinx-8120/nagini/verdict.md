# P2 adversarial audit — sphinx-doc__sphinx-8120

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,80 +198,11 @@
         Result() == ToSeq(user_tr)[first_provider(ToSeq(user_defines))]))
     # post-conditions-end
     # impl-start
-    # Assemble the ordered source list:  default, then project sources, then
-    # the bundled fallback (project sources ahead of the bundled fallback).
-    defines = [system_defines]  # type: List[bool]
-    defines = defines + user_defines
-    defines = defines + [builtin_defines]
-    tr = [system_tr]  # type: List[int]
-    tr = tr + user_tr
-    tr = tr + [builtin_tr]
-
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(len(defines) == len(tr))
-
-    n = len(defines)
-    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
-    res = NO_TEXT()
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(defines)))
-        Invariant(Acc(list_pred(tr)))
-        Invariant(Acc(list_pred(user_defines), 1 / 2))
-        Invariant(Acc(list_pred(user_tr), 1 / 2))
-        Invariant(len(user_defines) == len(user_tr))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < len(user_defines) and user_defines[k], user_tr[k] >= 1),
-            [[user_defines[k]]])))
-        Invariant(len(defines) == n and len(tr) == n)
-        Invariant(0 <= i and i <= n)
-        Invariant(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-        Invariant(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-        Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
-        # invariants-end
-        Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
-        Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
-        Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
-        Assert(ToSeq(tr).drop(i - 1).drop(1) == ToSeq(tr).drop(i))
-        if defines[i - 1]:
-            res = tr[i - 1]
-        i = i - 1
-
-    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
-    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
-    # res now equals first-wins resolution over the whole assembled list.
-    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(res == resolved(seq_defines(system_defines, ToSeq(user_defines), builtin_defines),
-                           seq_tr(system_tr, ToSeq(user_tr), builtin_tr)))
-    Assert(res == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
-                                     ToSeq(user_tr), builtin_defines, builtin_tr))
-    out = res
-    if res == NO_TEXT():
-        out = message
-
-    # Relate the whole-list resolution to the project-prefix first provider
-    # (the decisive precedence clause). When some project source provides, the
-    # first provider's text is real (>= 1), so it is not the NO_TEXT sentinel
-    # and `out` keeps it.
-    if not system_defines and some_provides(ToSeq(user_defines)):
-        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
-                                      ToSeq(user_tr), builtin_defines, builtin_tr))
-        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
-        fp = first_provider(ToSeq(user_defines))
-        Assert(ToSeq(user_defines)[fp])
-        Assert(0 <= fp and fp < len(user_defines))
-        Assert(user_defines[fp])
-        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
-        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
-        Assert(user_tr[fp] >= 1)
-        Assert(res == ToSeq(user_tr)[fp])
-        Assert(res >= 1)
-        Assert(out == res)
-    return out
+    r = resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
+                           ToSeq(user_tr), builtin_defines, builtin_tr)
+    if r == NO_TEXT():
+        return message
+    return r
     # impl-end
 
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,80 +198,7 @@
         Result() == ToSeq(user_tr)[first_provider(ToSeq(user_defines))]))
     # post-conditions-end
     # impl-start
-    # Assemble the ordered source list:  default, then project sources, then
-    # the bundled fallback (project sources ahead of the bundled fallback).
-    defines = [system_defines]  # type: List[bool]
-    defines = defines + user_defines
-    defines = defines + [builtin_defines]
-    tr = [system_tr]  # type: List[int]
-    tr = tr + user_tr
-    tr = tr + [builtin_tr]
-
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(len(defines) == len(tr))
-
-    n = len(defines)
-    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
-    res = NO_TEXT()
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(defines)))
-        Invariant(Acc(list_pred(tr)))
-        Invariant(Acc(list_pred(user_defines), 1 / 2))
-        Invariant(Acc(list_pred(user_tr), 1 / 2))
-        Invariant(len(user_defines) == len(user_tr))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < len(user_defines) and user_defines[k], user_tr[k] >= 1),
-            [[user_defines[k]]])))
-        Invariant(len(defines) == n and len(tr) == n)
-        Invariant(0 <= i and i <= n)
-        Invariant(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-        Invariant(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-        Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
-        # invariants-end
-        Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
-        Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
-        Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
-        Assert(ToSeq(tr).drop(i - 1).drop(1) == ToSeq(tr).drop(i))
-        if defines[i - 1]:
-            res = tr[i - 1]
-        i = i - 1
-
-    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
-    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
-    # res now equals first-wins resolution over the whole assembled list.
-    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(res == resolved(seq_defines(system_defines, ToSeq(user_defines), builtin_defines),
-                           seq_tr(system_tr, ToSeq(user_tr), builtin_tr)))
-    Assert(res == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
-                                     ToSeq(user_tr), builtin_defines, builtin_tr))
-    out = res
-    if res == NO_TEXT():
-        out = message
-
-    # Relate the whole-list resolution to the project-prefix first provider
-    # (the decisive precedence clause). When some project source provides, the
-    # first provider's text is real (>= 1), so it is not the NO_TEXT sentinel
-    # and `out` keeps it.
-    if not system_defines and some_provides(ToSeq(user_defines)):
-        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
-                                      ToSeq(user_tr), builtin_defines, builtin_tr))
-        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
-        fp = first_provider(ToSeq(user_defines))
-        Assert(ToSeq(user_defines)[fp])
-        Assert(0 <= fp and fp < len(user_defines))
-        Assert(user_defines[fp])
-        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
-        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
-        Assert(user_tr[fp] >= 1)
-        Assert(res == ToSeq(user_tr)[fp])
-        Assert(res >= 1)
-        Assert(out == res)
-    return out
+    return message
     # impl-end
 
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,79 +198,29 @@
         Result() == ToSeq(user_tr)[first_provider(ToSeq(user_defines))]))
     # post-conditions-end
     # impl-start
-    # Assemble the ordered source list:  default, then project sources, then
-    # the bundled fallback (project sources ahead of the bundled fallback).
     defines = [system_defines]  # type: List[bool]
     defines = defines + user_defines
     defines = defines + [builtin_defines]
     tr = [system_tr]  # type: List[int]
     tr = tr + user_tr
     tr = tr + [builtin_tr]
-
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(len(defines) == len(tr))
-
     n = len(defines)
-    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
     res = NO_TEXT()
-    i = n
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < n:
         Invariant(Acc(list_pred(defines)))
         Invariant(Acc(list_pred(tr)))
         Invariant(Acc(list_pred(user_defines), 1 / 2))
         Invariant(Acc(list_pred(user_tr), 1 / 2))
         Invariant(len(user_defines) == len(user_tr))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < len(user_defines) and user_defines[k], user_tr[k] >= 1),
-            [[user_defines[k]]])))
         Invariant(len(defines) == n and len(tr) == n)
         Invariant(0 <= i and i <= n)
-        Invariant(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-        Invariant(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-        Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
-        # invariants-end
-        Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
-        Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
-        Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
-        Assert(ToSeq(tr).drop(i - 1).drop(1) == ToSeq(tr).drop(i))
-        if defines[i - 1]:
-            res = tr[i - 1]
-        i = i - 1
-
-    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
-    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
-    # res now equals first-wins resolution over the whole assembled list.
-    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(res == resolved(seq_defines(system_defines, ToSeq(user_defines), builtin_defines),
-                           seq_tr(system_tr, ToSeq(user_tr), builtin_tr)))
-    Assert(res == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
-                                     ToSeq(user_tr), builtin_defines, builtin_tr))
+        if defines[i]:
+            res = tr[i]
+        i = i + 1
     out = res
     if res == NO_TEXT():
         out = message
-
-    # Relate the whole-list resolution to the project-prefix first provider
-    # (the decisive precedence clause). When some project source provides, the
-    # first provider's text is real (>= 1), so it is not the NO_TEXT sentinel
-    # and `out` keeps it.
-    if not system_defines and some_provides(ToSeq(user_defines)):
-        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
-                                      ToSeq(user_tr), builtin_defines, builtin_tr))
-        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
-        fp = first_provider(ToSeq(user_defines))
-        Assert(ToSeq(user_defines)[fp])
-        Assert(0 <= fp and fp < len(user_defines))
-        Assert(user_defines[fp])
-        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
-        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
-        Assert(user_tr[fp] >= 1)
-        Assert(res == ToSeq(user_tr)[fp])
-        Assert(res >= 1)
-        Assert(out == res)
     return out
     # impl-end
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,39 +198,25 @@
         Result() == ToSeq(user_tr)[first_provider(ToSeq(user_defines))]))
     # post-conditions-end
     # impl-start
-    # Assemble the ordered source list:  default, then project sources, then
-    # the bundled fallback (project sources ahead of the bundled fallback).
     defines = [system_defines]  # type: List[bool]
+    defines = defines + [builtin_defines]
     defines = defines + user_defines
-    defines = defines + [builtin_defines]
     tr = [system_tr]  # type: List[int]
+    tr = tr + [builtin_tr]
     tr = tr + user_tr
-    tr = tr + [builtin_tr]
-
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
     Assert(len(defines) == len(tr))
-
     n = len(defines)
-    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
     res = NO_TEXT()
     i = n
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(defines)))
         Invariant(Acc(list_pred(tr)))
         Invariant(Acc(list_pred(user_defines), 1 / 2))
         Invariant(Acc(list_pred(user_tr), 1 / 2))
         Invariant(len(user_defines) == len(user_tr))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < len(user_defines) and user_defines[k], user_tr[k] >= 1),
-            [[user_defines[k]]])))
         Invariant(len(defines) == n and len(tr) == n)
         Invariant(0 <= i and i <= n)
-        Invariant(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-        Invariant(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
         Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
-        # invariants-end
         Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
         Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
         Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
@@ -238,39 +224,9 @@
         if defines[i - 1]:
             res = tr[i - 1]
         i = i - 1
-
-    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
-    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
-    # res now equals first-wins resolution over the whole assembled list.
-    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(res == resolved(seq_defines(system_defines, ToSeq(user_defines), builtin_defines),
-                           seq_tr(system_tr, ToSeq(user_tr), builtin_tr)))
-    Assert(res == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
-                                     ToSeq(user_tr), builtin_defines, builtin_tr))
     out = res
     if res == NO_TEXT():
         out = message
-
-    # Relate the whole-list resolution to the project-prefix first provider
-    # (the decisive precedence clause). When some project source provides, the
-    # first provider's text is real (>= 1), so it is not the NO_TEXT sentinel
-    # and `out` keeps it.
-    if not system_defines and some_provides(ToSeq(user_defines)):
-        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
-                                      ToSeq(user_tr), builtin_defines, builtin_tr))
-        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
-        fp = first_provider(ToSeq(user_defines))
-        Assert(ToSeq(user_defines)[fp])
-        Assert(0 <= fp and fp < len(user_defines))
-        Assert(user_defines[fp])
-        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
-        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
-        Assert(user_tr[fp] >= 1)
-        Assert(res == ToSeq(user_tr)[fp])
-        Assert(res >= 1)
-        Assert(out == res)
     return out
     # impl-end
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,80 +198,9 @@
         Result() == ToSeq(user_tr)[first_provider(ToSeq(user_defines))]))
     # post-conditions-end
     # impl-start
-    # Assemble the ordered source list:  default, then project sources, then
-    # the bundled fallback (project sources ahead of the bundled fallback).
-    defines = [system_defines]  # type: List[bool]
-    defines = defines + user_defines
-    defines = defines + [builtin_defines]
-    tr = [system_tr]  # type: List[int]
-    tr = tr + user_tr
-    tr = tr + [builtin_tr]
-
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(len(defines) == len(tr))
-
-    n = len(defines)
-    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
-    res = NO_TEXT()
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(defines)))
-        Invariant(Acc(list_pred(tr)))
-        Invariant(Acc(list_pred(user_defines), 1 / 2))
-        Invariant(Acc(list_pred(user_tr), 1 / 2))
-        Invariant(len(user_defines) == len(user_tr))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < len(user_defines) and user_defines[k], user_tr[k] >= 1),
-            [[user_defines[k]]])))
-        Invariant(len(defines) == n and len(tr) == n)
-        Invariant(0 <= i and i <= n)
-        Invariant(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-        Invariant(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-        Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
-        # invariants-end
-        Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
-        Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
-        Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
-        Assert(ToSeq(tr).drop(i - 1).drop(1) == ToSeq(tr).drop(i))
-        if defines[i - 1]:
-            res = tr[i - 1]
-        i = i - 1
-
-    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
-    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
-    # res now equals first-wins resolution over the whole assembled list.
-    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(res == resolved(seq_defines(system_defines, ToSeq(user_defines), builtin_defines),
-                           seq_tr(system_tr, ToSeq(user_tr), builtin_tr)))
-    Assert(res == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
-                                     ToSeq(user_tr), builtin_defines, builtin_tr))
-    out = res
-    if res == NO_TEXT():
-        out = message
-
-    # Relate the whole-list resolution to the project-prefix first provider
-    # (the decisive precedence clause). When some project source provides, the
-    # first provider's text is real (>= 1), so it is not the NO_TEXT sentinel
-    # and `out` keeps it.
-    if not system_defines and some_provides(ToSeq(user_defines)):
-        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
-                                      ToSeq(user_tr), builtin_defines, builtin_tr))
-        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
-        fp = first_provider(ToSeq(user_defines))
-        Assert(ToSeq(user_defines)[fp])
-        Assert(0 <= fp and fp < len(user_defines))
-        Assert(user_defines[fp])
-        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
-        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
-        Assert(user_tr[fp] >= 1)
-        Assert(res == ToSeq(user_tr)[fp])
-        Assert(res >= 1)
-        Assert(out == res)
-    return out
+    r = resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
+                           ToSeq(user_tr), builtin_defines, builtin_tr)
+    return r
     # impl-end
 
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,79 +198,27 @@
         Result() == ToSeq(user_tr)[first_provider(ToSeq(user_defines))]))
     # post-conditions-end
     # impl-start
-    # Assemble the ordered source list:  default, then project sources, then
-    # the bundled fallback (project sources ahead of the bundled fallback).
     defines = [system_defines]  # type: List[bool]
     defines = defines + user_defines
-    defines = defines + [builtin_defines]
     tr = [system_tr]  # type: List[int]
     tr = tr + user_tr
-    tr = tr + [builtin_tr]
-
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(len(defines) == len(tr))
-
     n = len(defines)
-    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
     res = NO_TEXT()
     i = n
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(defines)))
         Invariant(Acc(list_pred(tr)))
         Invariant(Acc(list_pred(user_defines), 1 / 2))
         Invariant(Acc(list_pred(user_tr), 1 / 2))
         Invariant(len(user_defines) == len(user_tr))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < len(user_defines) and user_defines[k], user_tr[k] >= 1),
-            [[user_defines[k]]])))
         Invariant(len(defines) == n and len(tr) == n)
         Invariant(0 <= i and i <= n)
-        Invariant(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-        Invariant(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-        Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
-        # invariants-end
-        Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
-        Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
-        Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
-        Assert(ToSeq(tr).drop(i - 1).drop(1) == ToSeq(tr).drop(i))
         if defines[i - 1]:
             res = tr[i - 1]
         i = i - 1
-
-    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
-    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
-    # res now equals first-wins resolution over the whole assembled list.
-    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(res == resolved(seq_defines(system_defines, ToSeq(user_defines), builtin_defines),
-                           seq_tr(system_tr, ToSeq(user_tr), builtin_tr)))
-    Assert(res == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
-                                     ToSeq(user_tr), builtin_defines, builtin_tr))
     out = res
     if res == NO_TEXT():
         out = message
-
-    # Relate the whole-list resolution to the project-prefix first provider
-    # (the decisive precedence clause). When some project source provides, the
-    # first provider's text is real (>= 1), so it is not the NO_TEXT sentinel
-    # and `out` keeps it.
-    if not system_defines and some_provides(ToSeq(user_defines)):
-        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
-                                      ToSeq(user_tr), builtin_defines, builtin_tr))
-        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
-        fp = first_provider(ToSeq(user_defines))
-        Assert(ToSeq(user_defines)[fp])
-        Assert(0 <= fp and fp < len(user_defines))
-        Assert(user_defines[fp])
-        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
-        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
-        Assert(user_tr[fp] >= 1)
-        Assert(res == ToSeq(user_tr)[fp])
-        Assert(res >= 1)
-        Assert(out == res)
     return out
     # impl-end
 
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,80 +198,9 @@
         Result() == ToSeq(user_tr)[first_provider(ToSeq(user_defines))]))
     # post-conditions-end
     # impl-start
-    # Assemble the ordered source list:  default, then project sources, then
-    # the bundled fallback (project sources ahead of the bundled fallback).
-    defines = [system_defines]  # type: List[bool]
-    defines = defines + user_defines
-    defines = defines + [builtin_defines]
-    tr = [system_tr]  # type: List[int]
-    tr = tr + user_tr
-    tr = tr + [builtin_tr]
-
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(len(defines) == len(tr))
-
-    n = len(defines)
-    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
-    res = NO_TEXT()
-    i = n
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(defines)))
-        Invariant(Acc(list_pred(tr)))
-        Invariant(Acc(list_pred(user_defines), 1 / 2))
-        Invariant(Acc(list_pred(user_tr), 1 / 2))
-        Invariant(len(user_defines) == len(user_tr))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < len(user_defines) and user_defines[k], user_tr[k] >= 1),
-            [[user_defines[k]]])))
-        Invariant(len(defines) == n and len(tr) == n)
-        Invariant(0 <= i and i <= n)
-        Invariant(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-        Invariant(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-        Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
-        # invariants-end
-        Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
-        Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
-        Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
-        Assert(ToSeq(tr).drop(i - 1).drop(1) == ToSeq(tr).drop(i))
-        if defines[i - 1]:
-            res = tr[i - 1]
-        i = i - 1
-
-    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
-    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
-    # res now equals first-wins resolution over the whole assembled list.
-    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
-    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
-    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
-    Assert(res == resolved(seq_defines(system_defines, ToSeq(user_defines), builtin_defines),
-                           seq_tr(system_tr, ToSeq(user_tr), builtin_tr)))
-    Assert(res == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
-                                     ToSeq(user_tr), builtin_defines, builtin_tr))
-    out = res
-    if res == NO_TEXT():
-        out = message
-
-    # Relate the whole-list resolution to the project-prefix first provider
-    # (the decisive precedence clause). When some project source provides, the
-    # first provider's text is real (>= 1), so it is not the NO_TEXT sentinel
-    # and `out` keeps it.
-    if not system_defines and some_provides(ToSeq(user_defines)):
-        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
-                                      ToSeq(user_tr), builtin_defines, builtin_tr))
-        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
-        fp = first_provider(ToSeq(user_defines))
-        Assert(ToSeq(user_defines)[fp])
-        Assert(0 <= fp and fp < len(user_defines))
-        Assert(user_defines[fp])
-        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
-        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
-        Assert(user_tr[fp] >= 1)
-        Assert(res == ToSeq(user_tr)[fp])
-        Assert(res >= 1)
-        Assert(out == res)
-    return out
+    if system_defines:
+        return system_tr
+    return message
     # impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8120.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A message catalog is assembled from an ORDERED list of catalog sources. Each
  source may or may not provide a translation for a given message, and when it
  does it provides a specific replacement text. The assembled catalog resolves
  a message by the conventional first-wins precedence: the translation is taken
  from the FIRST source, in order, that provides one for that message; if no
  source provides one, the message itself is returned untranslated. A later
  source only fills a gap no earlier source covered.

  There are three kinds of source, in a definite precedence order from most to
  least authoritative:

      (1) the environment's default source (placed first only as a conventional
          probe; for the catalogs in question it provides nothing);
      (2) the project-supplied sources, in their given order -- the
          translations a project author intends to apply;
      (3) the bundled fallback source shipped with the tool.

  The decisive desired behaviour: when a project-supplied source and the
  bundled fallback source BOTH provide a translation for the same message, the
  resolved translation is the PROJECT-supplied one. A project author's
  intentional override of a message wins over the value bundled with the tool;
  the bundled value is used only for messages no project source covers.

Translations are modelled abstractly as small `int` codes (each distinct text
is a distinct code); the spec is about WHICH source's text is selected, not
about the characters of any text, so the carrier is opaque identity. The
resolution precedence is modelled DEEPLY as a front-recursive fold over the
ordered source list; no library callee is consumed as an axiom (the first-wins
precedence of the merged catalog is spelled out and verified). A per-source
pair of parallel lists -- whether the source provides a translation for the
message, and which text it provides -- is plain input data, not an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The merged-catalog first-wins precedence used by the
#  resolution is modelled DEEPLY below (`resolved`, a front-recursive fold over
#  the ordered source list) and validated == the real merged-catalog lookup
#  out-of-band by axiom_check.py / G-AX, never consumed. The per-source catalog
#  facts -- whether a source provides a translation for the message and which
#  text it provides -- are plain input data, not axioms.)
# axioms-end


# pure-start
@Pure
def NO_TEXT() -> int:
    """The sentinel meaning "no translation" (the untranslated message stands
    in for itself). Distinct from every real translation code, which are >= 1.
    """
    return 0


@Pure
def seq_defines(system_defines: bool, ud: PSeq[bool], builtin_defines: bool) -> PSeq[bool]:
    """The assembled ordered "provides?" sequence: default, then project
    sources, then bundled fallback."""
    Ensures(len(Result()) == len(ud) + 2)
    return (PSeq(system_defines) + ud) + PSeq(builtin_defines)


@Pure
def seq_tr(system_tr: int, ut: PSeq[int], builtin_tr: int) -> PSeq[int]:
    """The assembled ordered "text" sequence, aligned with seq_defines."""
    Ensures(len(Result()) == len(ut) + 2)
    return (PSeq(system_tr) + ut) + PSeq(builtin_tr)


@Pure
def resolved(defines: PSeq[bool], tr: PSeq[int]) -> int:
    """First-wins resolution: the translation text of the FIRST source (in
    order) that provides one for the message, or NO_TEXT() if none does.
    Front-recursive so a single unfold is available per loop step. The two
    parallel sequences are aligned: `tr[i]` is the text source `i` provides,
    meaningful only where `defines[i]` holds."""
    Requires(len(defines) == len(tr))
    if len(defines) == 0:
        return NO_TEXT()
    if defines[0]:
        return tr[0]
    return resolved(defines.drop(1), tr.drop(1))


@Pure
def resolved_assembled(system_defines: bool, system_tr: int,
                       ud: PSeq[bool], ut: PSeq[int],
                       builtin_defines: bool, builtin_tr: int) -> int:
    """First-wins resolution over the fully assembled order (default ++ project
    ++ bundled). Wrapper so callers need only the project-list length equality;
    the assembled-length equality is discharged here."""
    Requires(len(ud) == len(ut))
    return resolved(seq_defines(system_defines, ud, builtin_defines),
                    seq_tr(system_tr, ut, builtin_tr))


@Pure
def some_provides(defines: PSeq[bool]) -> bool:
    """Whether ANY source in the order provides a translation for the message.
    Front-recursive so a single unfold is available per loop step."""
    if len(defines) == 0:
        return False
    if defines[0]:
        return True
    return some_provides(defines.drop(1))


@Pure
def first_provider(defines: PSeq[bool]) -> int:
    """Index of the FIRST source (in order) that provides a translation, given
    that some source does. Front-recursive."""
    Requires(some_provides(defines))
    if defines[0]:
        return 0
    return 1 + first_provider(defines.drop(1))


@Pure
def lemma_first_provider_bound(defines: PSeq[bool]) -> bool:
    """The first provider's index is in range and that source provides.
    Proven by front-recursion."""
    Requires(some_provides(defines))
    Ensures(Result())
    Ensures(0 <= first_provider(defines) and first_provider(defines) < len(defines))
    Ensures(defines[first_provider(defines)])
    if defines[0]:
        return True
    return lemma_first_provider_bound(defines.drop(1))


@Pure
def lemma_seq_len(system_defines: bool, ud: PSeq[bool], builtin_defines: bool,
                  system_tr: int, ut: PSeq[int], builtin_tr: int) -> bool:
    """The two assembled sequences have equal length when the project lists do
    (each adds the same two endpoints)."""
    Requires(len(ud) == len(ut))
    Ensures(Result())
    Ensures(len(seq_defines(system_defines, ud, builtin_defines))
            == len(seq_tr(system_tr, ut, builtin_tr)))
    return True
# pure-end


def select_translation(system_defines: bool, system_tr: int,
                     user_defines: List[bool], user_tr: List[int],
                     builtin_defines: bool, builtin_tr: int,
                     message: int) -> int:
    # pre-conditions-start
    # The project-supplied source facts are read only; fractional permission.
    Requires(Acc(list_pred(user_defines), 1 / 2))
    Requires(Acc(list_pred(user_tr), 1 / 2))
    Requires(len(user_defines) == len(user_tr))
    Requires(len(ToSeq(user_defines)) == len(ToSeq(user_tr)))
    # `message` is the (code for the) untranslated message. Real translations
    # are coded >= 1; NO_TEXT() (0) is reserved for "untranslated". A source
    # that PROVIDES a translation supplies a real (>= 1) text.
    Requires(message >= 1)
    Requires(Implies(system_defines, system_tr >= 1))
    Requires(Implies(builtin_defines, builtin_tr >= 1))
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < len(user_defines) and user_defines[i], user_tr[i] >= 1),
        [[user_defines[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(user_defines), 1 / 2))
    Ensures(Acc(list_pred(user_tr), 1 / 2))
    Ensures(len(user_defines) == len(user_tr))
    Ensures(len(ToSeq(user_defines)) == len(ToSeq(user_tr)))
    # The result is the first-wins resolution over the assembled order, with the
    # untranslated message standing in when no source provides a translation.
    Ensures(Implies(
        resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                           ToSeq(user_tr), builtin_defines, builtin_tr) == NO_TEXT(),
        Result() == message))
    Ensures(Implies(
        resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                           ToSeq(user_tr), builtin_defines, builtin_tr) != NO_TEXT(),
        Result() == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                                       ToSeq(user_tr), builtin_defines, builtin_tr)))
    # Decisive precedence: when the environment default provides nothing but a
    # project-supplied source provides a translation, the result is the FIRST
    # such project source's text -- NOT the bundled fallback's, even if the
    # bundled source also provides one. (`first_provider` over the project
    # sources is the least index that provides; the result is its text.)
    Ensures(Implies(
        not system_defines and some_provides(ToSeq(user_defines)),
        0 <= first_provider(ToSeq(user_defines))
        and first_provider(ToSeq(user_defines)) < len(user_defines)))
    Ensures(Implies(
        not system_defines and some_provides(ToSeq(user_defines)),
        Result() == ToSeq(user_tr)[first_provider(ToSeq(user_defines))]))
    # post-conditions-end
    # impl-start
    # Assemble the ordered source list:  default, then project sources, then
    # the bundled fallback (project sources ahead of the bundled fallback).
    defines = [system_defines]  # type: List[bool]
    defines = defines + user_defines
    defines = defines + [builtin_defines]
    tr = [system_tr]  # type: List[int]
    tr = tr + user_tr
    tr = tr + [builtin_tr]

    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
    Assert(len(defines) == len(tr))

    n = len(defines)
    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
    res = NO_TEXT()
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(defines)))
        Invariant(Acc(list_pred(tr)))
        Invariant(Acc(list_pred(user_defines), 1 / 2))
        Invariant(Acc(list_pred(user_tr), 1 / 2))
        Invariant(len(user_defines) == len(user_tr))
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < len(user_defines) and user_defines[k], user_tr[k] >= 1),
            [[user_defines[k]]])))
        Invariant(len(defines) == n and len(tr) == n)
        Invariant(0 <= i and i <= n)
        Invariant(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
        Invariant(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
        Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
        # invariants-end
        Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
        Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
        Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
        Assert(ToSeq(tr).drop(i - 1).drop(1) == ToSeq(tr).drop(i))
        if defines[i - 1]:
            res = tr[i - 1]
        i = i - 1

    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
    # res now equals first-wins resolution over the whole assembled list.
    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
    Assert(res == resolved(seq_defines(system_defines, ToSeq(user_defines), builtin_defines),
                           seq_tr(system_tr, ToSeq(user_tr), builtin_tr)))
    Assert(res == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                                     ToSeq(user_tr), builtin_defines, builtin_tr))
    out = res
    if res == NO_TEXT():
        out = message

    # Relate the whole-list resolution to the project-prefix first provider
    # (the decisive precedence clause). When some project source provides, the
    # first provider's text is real (>= 1), so it is not the NO_TEXT sentinel
    # and `out` keeps it.
    if not system_defines and some_provides(ToSeq(user_defines)):
        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
                                      ToSeq(user_tr), builtin_defines, builtin_tr))
        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
        fp = first_provider(ToSeq(user_defines))
        Assert(ToSeq(user_defines)[fp])
        Assert(0 <= fp and fp < len(user_defines))
        Assert(user_defines[fp])
        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
        Assert(user_tr[fp] >= 1)
        Assert(res == ToSeq(user_tr)[fp])
        Assert(res >= 1)
        Assert(out == res)
    return out
    # impl-end


# Helper @Pure lemmas for the postcondition proof (out of the spec regions;
# pure proof glue, no behavioural content).
@Pure
def _resolution_picks_user(system_defines: bool, system_tr: int,
                           ud: PSeq[bool], ut: PSeq[int],
                           builtin_defines: bool, builtin_tr: int) -> bool:
    """The whole-list first-wins resolution, when the default provides nothing
    and some project source provides, equals the first project source's text.
    The assembled list is [default] ++ project ++ [bundled]; with the default
    not providing, resolution descends into the project prefix, whose first
    provider wins (it precedes the bundled fallback)."""
    Requires(len(ud) == len(ut))
    Requires(not system_defines)
    Requires(some_provides(ud))
    Ensures(Result())
    Ensures(0 <= first_provider(ud) and first_provider(ud) < len(ud))
    Ensures(resolved(seq_defines(system_defines, ud, builtin_defines),
                     seq_tr(system_tr, ut, builtin_tr)) == ut[first_provider(ud)])
    # Peel the (non-providing) default head: seq_defines == [sys] ++ (ud++[builtin]).
    da = seq_defines(system_defines, ud, builtin_defines)  # type: PSeq[bool]
    ta = seq_tr(system_tr, ut, builtin_tr)  # type: PSeq[int]
    tail_d = ud + PSeq(builtin_defines)  # type: PSeq[bool]
    tail_t = ut + PSeq(builtin_tr)  # type: PSeq[int]
    Assert(da == PSeq(system_defines) + tail_d)
    Assert(ta == PSeq(system_tr) + tail_t)
    Assert(da[0] == system_defines)
    Assert(da.drop(1) == tail_d)
    Assert(ta.drop(1) == tail_t)
    # resolved(da, ta): da[0] is False, so it equals resolved(tail_d, tail_t).
    Assert(resolved(da, ta) == resolved(tail_d, tail_t))
    return _resolution_over_prefix(ud, ut, builtin_defines, builtin_tr)


@Pure
def _resolution_over_prefix(ud: PSeq[bool], ut: PSeq[int],
                            builtin_defines: bool, builtin_tr: int) -> bool:
    """If some source in `ud` provides, resolution over `ud ++ [bundled]`
    equals `ud`'s first provider's text (the bundled tail is never reached).
    Front-recursive on `ud`."""
    Requires(len(ud) == len(ut))
    Requires(some_provides(ud))
    Ensures(Result())
    Ensures(0 <= first_provider(ud) and first_provider(ud) < len(ud))
    Ensures(resolved(ud + PSeq(builtin_defines), ut + PSeq(builtin_tr))
            == ut[first_provider(ud)])
    cd = ud + PSeq(builtin_defines)  # type: PSeq[bool]
    ct = ut + PSeq(builtin_tr)  # type: PSeq[int]
    Assert(cd[0] == ud[0])
    Assert(ct[0] == ut[0])
    if ud[0]:
        return True
    Assert(cd.drop(1) == ud.drop(1) + PSeq(builtin_defines))
    Assert(ct.drop(1) == ut.drop(1) + PSeq(builtin_tr))
    Assert(some_provides(ud.drop(1)))
    Assert(lemma_first_provider_bound(ud.drop(1)))
    Assert(first_provider(ud) == 1 + first_provider(ud.drop(1)))
    Assert(ut.drop(1)[first_provider(ud.drop(1))] == ut[1 + first_provider(ud.drop(1))])
    Assert(ut.drop(1)[first_provider(ud.drop(1))] == ut[first_provider(ud)])
    return _resolution_over_prefix(ud.drop(1), ut.drop(1), builtin_defines, builtin_tr)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8120 (nagini). Ran ≥5 distinct same-spec wrong impls; ALL confirmed same-spec (byte-identical spec view, exit 0) AND all REJECTED by Nagini verification (weakness exit=2). Positive control (verbatim gold impl) verifies (nagini_verify.sh exit=0). No CANDIDATE (verifying wrong impl) emerged, so no faithful patch materialization / run_resolve was applicable.

WHY THE SPEC IS TIGHT: The two primary postconditions form a TOTAL pin on Result over the entire precondition-admissible domain — they partition on `resolved_assembled(...) == NO_TEXT()`: if NO_TEXT ⇒ Result==message; else Result==resolved_assembled(...). Any verifying impl must therefore equal the spec's deep-model function everywhere. The decisive precedence clause (Result==user_tr[first_provider(user_defines)] when default provides nothing and some project source provides) additionally forces the [default]++project++[bundled] order to be honored, requiring the proof glue (_resolution_picks_user / lemma_first_provider_bound establishing user_tr[fp]>=1). verify⇒correct holds by construction.

### ATTACK BATTERY (all same-spec exit 0; all weakness exit 2 = rejected):
- atk_1 ungrounded-oracle echo: returns resolved_assembled directly (behaviourally CORRECT) — REJECTED: bare return can't discharge the decisive precedence postcondition (needs the >=1 lemma glue), confirming the gate demands real proof, not a lucky echo.
- atk_2 return message always (partial/degenerate) — REJECTED on post2 when resolved!=NO_TEXT.
- atk_3 last-wins forward fold (control-flow-effect: bundled wins over project) — REJECTED on decisive precedence.
- atk_4 PREPATCH BUG re-encoded: assemble [default]++[bundled]++project (bundled ahead of project) with full prepatch proof scaffold — REJECTED (reproduces the gold bug; fails post2 + precedence exactly as model_prepatch.py does). prepatch_reproduced=true.
- atk_5 partial-domain: returns resolved_assembled without the NO_TEXT→message fallback — REJECTED on post1 (returns 0 instead of message when nothing provides).
- atk_6 boundary/off-by-one: drops the bundled source (omits builtin from the assembled list) — REJECTED.
- atk_7 control-flow-effect: returns system_tr when system_defines else message, ignoring the fold — REJECTED.

A-LEG AUDIT (refinement.md): Legs A1 (params↔three catalog sources) R; A2 (seq_defines/seq_tr list construction [default]++project++[bundled]) R+I; A3 (resolved ↔ gettext merge/lookup first-wins) A-REFERENCE; A4 (NO_TEXT→message ↔ gettext untranslated) A-REFERENCE; A5 (return code↔selected text) R; B1 (List[str]→List[Optional[str]] type widening) R annotation-only. §C explicitly confirms NO kind-3 steps and NO consumed @ContractOnly axiom (axioms region empty). The two A-reference legs (A3/A4) are the merged-catalog first-wins precedence; model↔callee correspondence VALIDATED by G-AX: ran axiom_check.py which builds REAL stdlib gettext NullTranslations objects, chains with genuine add_fallback, asserts merged.gettext==resolved over 14 boundary + 20000 fuzz orderings + decisive sphinx project-overrides-bundled scenario — exit 0 (SOUND). Correspondence holds.

### Commands
- same-spec: `python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-8120 <atk>` → all exit 0
- positive control: `bash scripts/nagini_verify.sh pos_control.py` → exit 0
- G-AX: `python3 axiom_check.py` → exit 0

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8120.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A message catalog is assembled from an ORDERED list of catalog sources. Each
  source may or may not provide a translation for a given message, and when it
  does it provides a specific replacement text. The assembled catalog resolves
  a message by the conventional first-wins precedence: the translation is taken
  from the FIRST source, in order, that provides one for that message; if no
  source provides one, the message itself is returned untranslated. A later
  source only fills a gap no earlier source covered.

  There are three kinds of source, in a definite precedence order from most to
  least authoritative:

      (1) the environment's default source (placed first only as a conventional
          probe; for the catalogs in question it provides nothing);
      (2) the project-supplied sources, in their given order -- the
          translations a project author intends to apply;
      (3) the bundled fallback source shipped with the tool.

  The decisive desired behaviour: when a project-supplied source and the
  bundled fallback source BOTH provide a translation for the same message, the
  resolved translation is the PROJECT-supplied one. A project author's
  intentional override of a message wins over the value bundled with the tool;
  the bundled value is used only for messages no project source covers.

Translations are modelled abstractly as small `int` codes (each distinct text
is a distinct code); the spec is about WHICH source's text is selected, not
about the characters of any text, so the carrier is opaque identity. The
resolution precedence is modelled DEEPLY as a front-recursive fold over the
ordered source list; no library callee is consumed as an axiom (the first-wins
precedence of the merged catalog is spelled out and verified). A per-source
pair of parallel lists -- whether the source provides a translation for the
message, and which text it provides -- is plain input data, not an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The merged-catalog first-wins precedence used by the
#  resolution is modelled DEEPLY below (`resolved`, a front-recursive fold over
#  the ordered source list) and validated == the real merged-catalog lookup
#  out-of-band by axiom_check.py / G-AX, never consumed. The per-source catalog
#  facts -- whether a source provides a translation for the message and which
#  text it provides -- are plain input data, not axioms.)
# axioms-end


# pure-start
@Pure
def NO_TEXT() -> int:
    """The sentinel meaning "no translation" (the untranslated message stands
    in for itself). Distinct from every real translation code, which are >= 1.
    """
    return 0


@Pure
def seq_defines(system_defines: bool, ud: PSeq[bool], builtin_defines: bool) -> PSeq[bool]:
    """The assembled ordered "provides?" sequence: default, then project
    sources, then bundled fallback."""
    Ensures(len(Result()) == len(ud) + 2)
    return (PSeq(system_defines) + ud) + PSeq(builtin_defines)


@Pure
def seq_tr(system_tr: int, ut: PSeq[int], builtin_tr: int) -> PSeq[int]:
    """The assembled ordered "text" sequence, aligned with seq_defines."""
    Ensures(len(Result()) == len(ut) + 2)
    return (PSeq(system_tr) + ut) + PSeq(builtin_tr)


@Pure
def resolved(defines: PSeq[bool], tr: PSeq[int]) -> int:
    """First-wins resolution: the translation text of the FIRST source (in
    order) that provides one for the message, or NO_TEXT() if none does.
    Front-recursive so a single unfold is available per loop step. The two
    parallel sequences are aligned: `tr[i]` is the text source `i` provides,
    meaningful only where `defines[i]` holds."""
    Requires(len(defines) == len(tr))
    if len(defines) == 0:
        return NO_TEXT()
    if defines[0]:
        return tr[0]
    return resolved(defines.drop(1), tr.drop(1))


@Pure
def resolved_assembled(system_defines: bool, system_tr: int,
                       ud: PSeq[bool], ut: PSeq[int],
                       builtin_defines: bool, builtin_tr: int) -> int:
    """First-wins resolution over the fully assembled order (default ++ project
    ++ bundled). Wrapper so callers need only the project-list length equality;
    the assembled-length equality is discharged here."""
    Requires(len(ud) == len(ut))
    return resolved(seq_defines(system_defines, ud, builtin_defines),
                    seq_tr(system_tr, ut, builtin_tr))


@Pure
def some_provides(defines: PSeq[bool]) -> bool:
    """Whether ANY source in the order provides a translation for the message.
    Front-recursive so a single unfold is available per loop step."""
    if len(defines) == 0:
        return False
    if defines[0]:
        return True
    return some_provides(defines.drop(1))


@Pure
def first_provider(defines: PSeq[bool]) -> int:
    """Index of the FIRST source (in order) that provides a translation, given
    that some source does. Front-recursive."""
    Requires(some_provides(defines))
    if defines[0]:
        return 0
    return 1 + first_provider(defines.drop(1))


@Pure
def lemma_first_provider_bound(defines: PSeq[bool]) -> bool:
    """The first provider's index is in range and that source provides.
    Proven by front-recursion."""
    Requires(some_provides(defines))
    Ensures(Result())
    Ensures(0 <= first_provider(defines) and first_provider(defines) < len(defines))
    Ensures(defines[first_provider(defines)])
    if defines[0]:
        return True
    return lemma_first_provider_bound(defines.drop(1))


@Pure
def lemma_seq_len(system_defines: bool, ud: PSeq[bool], builtin_defines: bool,
                  system_tr: int, ut: PSeq[int], builtin_tr: int) -> bool:
    """The two assembled sequences have equal length when the project lists do
    (each adds the same two endpoints)."""
    Requires(len(ud) == len(ut))
    Ensures(Result())
    Ensures(len(seq_defines(system_defines, ud, builtin_defines))
            == len(seq_tr(system_tr, ut, builtin_tr)))
    return True
# pure-end


def select_translation(system_defines: bool, system_tr: int,
                     user_defines: List[bool], user_tr: List[int],
                     builtin_defines: bool, builtin_tr: int,
                     message: int) -> int:
    # pre-conditions-start
    # The project-supplied source facts are read only; fractional permission.
    Requires(Acc(list_pred(user_defines), 1 / 2))
    Requires(Acc(list_pred(user_tr), 1 / 2))
    Requires(len(user_defines) == len(user_tr))
    Requires(len(ToSeq(user_defines)) == len(ToSeq(user_tr)))
    # `message` is the (code for the) untranslated message. Real translations
    # are coded >= 1; NO_TEXT() (0) is reserved for "untranslated". A source
    # that PROVIDES a translation supplies a real (>= 1) text.
    Requires(message >= 1)
    Requires(Implies(system_defines, system_tr >= 1))
    Requires(Implies(builtin_defines, builtin_tr >= 1))
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < len(user_defines) and user_defines[i], user_tr[i] >= 1),
        [[user_defines[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(user_defines), 1 / 2))
    Ensures(Acc(list_pred(user_tr), 1 / 2))
    Ensures(len(user_defines) == len(user_tr))
    Ensures(len(ToSeq(user_defines)) == len(ToSeq(user_tr)))
    # The result is the first-wins resolution over the assembled order, with the
    # untranslated message standing in when no source provides a translation.
    Ensures(Implies(
        resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                           ToSeq(user_tr), builtin_defines, builtin_tr) == NO_TEXT(),
        Result() == message))
    Ensures(Implies(
        resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                           ToSeq(user_tr), builtin_defines, builtin_tr) != NO_TEXT(),
        Result() == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                                       ToSeq(user_tr), builtin_defines, builtin_tr)))
    # Decisive precedence: when the environment default provides nothing but a
    # project-supplied source provides a translation, the result is the FIRST
    # such project source's text -- NOT the bundled fallback's, even if the
    # bundled source also provides one. (`first_provider` over the project
    # sources is the least index that provides; the result is its text.)
    Ensures(Implies(
        not system_defines and some_provides(ToSeq(user_defines)),
        0 <= first_provider(ToSeq(user_defines))
        and first_provider(ToSeq(user_defines)) < len(user_defines)))
    Ensures(Implies(
        not system_defines and some_provides(ToSeq(user_defines)),
        Result() == ToSeq(user_tr)[first_provider(ToSeq(user_defines))]))
    # post-conditions-end
    # impl-start
    # Assemble the ordered source list:  default, then project sources, then
    # the bundled fallback (project sources ahead of the bundled fallback).
    defines = [system_defines]  # type: List[bool]
    defines = defines + user_defines
    defines = defines + [builtin_defines]
    tr = [system_tr]  # type: List[int]
    tr = tr + user_tr
    tr = tr + [builtin_tr]

    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
    Assert(len(defines) == len(tr))

    n = len(defines)
    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
    res = NO_TEXT()
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(defines)))
        Invariant(Acc(list_pred(tr)))
        Invariant(Acc(list_pred(user_defines), 1 / 2))
        Invariant(Acc(list_pred(user_tr), 1 / 2))
        Invariant(len(user_defines) == len(user_tr))
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < len(user_defines) and user_defines[k], user_tr[k] >= 1),
            [[user_defines[k]]])))
        Invariant(len(defines) == n and len(tr) == n)
        Invariant(0 <= i and i <= n)
        Invariant(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
        Invariant(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
        Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
        # invariants-end
        Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
        Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
        Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
        Assert(ToSeq(tr).drop(i - 1).drop(1) == ToSeq(tr).drop(i))
        if defines[i - 1]:
            res = tr[i - 1]
        i = i - 1

    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
    # res now equals first-wins resolution over the whole assembled list.
    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
    Assert(res == resolved(seq_defines(system_defines, ToSeq(user_defines), builtin_defines),
                           seq_tr(system_tr, ToSeq(user_tr), builtin_tr)))
    Assert(res == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                                     ToSeq(user_tr), builtin_defines, builtin_tr))
    out = res
    if res == NO_TEXT():
        out = message

    # Relate the whole-list resolution to the project-prefix first provider
    # (the decisive precedence clause). When some project source provides, the
    # first provider's text is real (>= 1), so it is not the NO_TEXT sentinel
    # and `out` keeps it.
    if not system_defines and some_provides(ToSeq(user_defines)):
        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
                                      ToSeq(user_tr), builtin_defines, builtin_tr))
        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
        fp = first_provider(ToSeq(user_defines))
        Assert(ToSeq(user_defines)[fp])
        Assert(0 <= fp and fp < len(user_defines))
        Assert(user_defines[fp])
        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
        Assert(user_tr[fp] >= 1)
        Assert(res == ToSeq(user_tr)[fp])
        Assert(res >= 1)
        Assert(out == res)
    return out
    # impl-end


# Helper @Pure lemmas for the postcondition proof (out of the spec regions;
# pure proof glue, no behavioural content).
@Pure
def _resolution_picks_user(system_defines: bool, system_tr: int,
                           ud: PSeq[bool], ut: PSeq[int],
                           builtin_defines: bool, builtin_tr: int) -> bool:
    """The whole-list first-wins resolution, when the default provides nothing
    and some project source provides, equals the first project source's text.
    The assembled list is [default] ++ project ++ [bundled]; with the default
    not providing, resolution descends into the project prefix, whose first
    provider wins (it precedes the bundled fallback)."""
    Requires(len(ud) == len(ut))
    Requires(not system_defines)
    Requires(some_provides(ud))
    Ensures(Result())
    Ensures(0 <= first_provider(ud) and first_provider(ud) < len(ud))
    Ensures(resolved(seq_defines(system_defines, ud, builtin_defines),
                     seq_tr(system_tr, ut, builtin_tr)) == ut[first_provider(ud)])
    # Peel the (non-providing) default head: seq_defines == [sys] ++ (ud++[builtin]).
    da = seq_defines(system_defines, ud, builtin_defines)  # type: PSeq[bool]
    ta = seq_tr(system_tr, ut, builtin_tr)  # type: PSeq[int]
    tail_d = ud + PSeq(builtin_defines)  # type: PSeq[bool]
    tail_t = ut + PSeq(builtin_tr)  # type: PSeq[int]
    Assert(da == PSeq(system_defines) + tail_d)
    Assert(ta == PSeq(system_tr) + tail_t)
    Assert(da[0] == system_defines)
    Assert(da.drop(1) == tail_d)
    Assert(ta.drop(1) == tail_t)
    # resolved(da, ta): da[0] is False, so it equals resolved(tail_d, tail_t).
    Assert(resolved(da, ta) == resolved(tail_d, tail_t))
    return _resolution_over_prefix(ud, ut, builtin_defines, builtin_tr)


@Pure
def _resolution_over_prefix(ud: PSeq[bool], ut: PSeq[int],
                            builtin_defines: bool, builtin_tr: int) -> bool:
    """If some source in `ud` provides, resolution over `ud ++ [bundled]`
    equals `ud`'s first provider's text (the bundled tail is never reached).
    Front-recursive on `ud`."""
    Requires(len(ud) == len(ut))
    Requires(some_provides(ud))
    Ensures(Result())
    Ensures(0 <= first_provider(ud) and first_provider(ud) < len(ud))
    Ensures(resolved(ud + PSeq(builtin_defines), ut + PSeq(builtin_tr))
            == ut[first_provider(ud)])
    cd = ud + PSeq(builtin_defines)  # type: PSeq[bool]
    ct = ut + PSeq(builtin_tr)  # type: PSeq[int]
    Assert(cd[0] == ud[0])
    Assert(ct[0] == ut[0])
    if ud[0]:
        return True
    Assert(cd.drop(1) == ud.drop(1) + PSeq(builtin_defines))
    Assert(ct.drop(1) == ut.drop(1) + PSeq(builtin_tr))
    Assert(some_provides(ud.drop(1)))
    Assert(lemma_first_provider_bound(ud.drop(1)))
    Assert(first_provider(ud) == 1 + first_provider(ud.drop(1)))
    Assert(ut.drop(1)[first_provider(ud.drop(1))] == ut[1 + first_provider(ud.drop(1))])
    Assert(ut.drop(1)[first_provider(ud.drop(1))] == ut[first_provider(ud)])
    return _resolution_over_prefix(ud.drop(1), ut.drop(1), builtin_defines, builtin_tr)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8120 (nagini). Ran ≥5 distinct same-spec wrong impls; ALL confirmed same-spec (byte-identical spec view, exit 0) AND all REJECTED by Nagini verification (weakness exit=2). Positive control (verbatim gold impl) verifies (nagini_verify.sh exit=0). No CANDIDATE (verifying wrong impl) emerged, so no faithful patch materialization / run_resolve was applicable.

WHY THE SPEC IS TIGHT: The two primary postconditions form a TOTAL pin on Result over the entire precondition-admissible domain — they partition on `resolved_assembled(...) == NO_TEXT()`: if NO_TEXT ⇒ Result==message; else Result==resolved_assembled(...). Any verifying impl must therefore equal the spec's deep-model function everywhere. The decisive precedence clause (Result==user_tr[first_provider(user_defines)] when default provides nothing and some project source provides) additionally forces the [default]++project++[bundled] order to be honored, requiring the proof glue (_resolution_picks_user / lemma_first_provider_bound establishing user_tr[fp]>=1). verify⇒correct holds by construction.

### ATTACK BATTERY (all same-spec exit 0; all weakness exit 2 = rejected):
- atk_1 ungrounded-oracle echo: returns resolved_assembled directly (behaviourally CORRECT) — REJECTED: bare return can't discharge the decisive precedence postcondition (needs the >=1 lemma glue), confirming the gate demands real proof, not a lucky echo.
- atk_2 return message always (partial/degenerate) — REJECTED on post2 when resolved!=NO_TEXT.
- atk_3 last-wins forward fold (control-flow-effect: bundled wins over project) — REJECTED on decisive precedence.
- atk_4 PREPATCH BUG re-encoded: assemble [default]++[bundled]++project (bundled ahead of project) with full prepatch proof scaffold — REJECTED (reproduces the gold bug; fails post2 + precedence exactly as model_prepatch.py does). prepatch_reproduced=true.
- atk_5 partial-domain: returns resolved_assembled without the NO_TEXT→message fallback — REJECTED on post1 (returns 0 instead of message when nothing provides).
- atk_6 boundary/off-by-one: drops the bundled source (omits builtin from the assembled list) — REJECTED.
- atk_7 control-flow-effect: returns system_tr when system_defines else message, ignoring the fold — REJECTED.

A-LEG AUDIT (refinement.md): Legs A1 (params↔three catalog sources) R; A2 (seq_defines/seq_tr list construction [default]++project++[bundled]) R+I; A3 (resolved ↔ gettext merge/lookup first-wins) A-REFERENCE; A4 (NO_TEXT→message ↔ gettext untranslated) A-REFERENCE; A5 (return code↔selected text) R; B1 (List[str]→List[Optional[str]] type widening) R annotation-only. §C explicitly confirms NO kind-3 steps and NO consumed @ContractOnly axiom (axioms region empty). The two A-reference legs (A3/A4) are the merged-catalog first-wins precedence; model↔callee correspondence VALIDATED by G-AX: ran axiom_check.py which builds REAL stdlib gettext NullTranslations objects, chains with genuine add_fallback, asserts merged.gettext==resolved over 14 boundary + 20000 fuzz orderings + decisive sphinx project-overrides-bundled scenario — exit 0 (SOUND). Correspondence holds.

### Commands
- same-spec: `python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-8120 <atk>` → all exit 0
- positive control: `bash scripts/nagini_verify.sh pos_control.py` → exit 0
- G-AX: `python3 axiom_check.py` → exit 0

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check (spec-too-strong / drift): the modeled function select_translation agrees with the real callee (Sphinx._init_i18n -> locale.init -> gettext merge/lookup) on every reachable input.

Real callee behaviour (base_commit 795747b; gettext merge logic is stable and re-verified on the /tmp worktrees): the gold patch sets locale_dirs = [None] ++ list(repo.locale_dirs) ++ [package_dir/'locale'] and calls locale.init, which builds a gettext translator by taking the first found catalog as primary and appending the rest via translator.add_fallback(trans) in order; translator.gettext(message) returns the primary's entry if present else descends the fallback chain in order, else returns the message unchanged. I empirically confirmed gettext is FIRST-in-chain-wins (three-provider chain returns the first; gap-then-provider returns the provider; nobody-provides returns the message).

Model spec: seq_defines/seq_tr assemble [default] ++ project ++ [bundled]; resolved is a first-wins fold; the postconditions pin Result to resolved_assembled (with NO_TEXT->message), plus the decisive precedence clause (when default provides nothing and some project source provides, Result == user_tr[first_provider(user_defines)], i.e. project beats bundled).

Evidence of agreement: (1) the bundle's own G-AX axiom_check.py passes (14 boundary + 20000 fuzz orderings + decisive sphinx scenario), exit 0, importing the real stdlib gettext module the callee uses; (2) independent fuzz of 200,000 random source configurations comparing the model's assembled first-wins spec against real gettext add_fallback/gettext — INCLUDING system_defines=True cases the real repo never produces (the [None] system source provides nothing in reality) — yielded ZERO mismatches.

The spec is broader than the real repo's reachable domain (it permits the system/default source to provide), but on every such input it still coincides with real gettext first-wins semantics, so it never disagrees with the callee. A broader-but-consistent spec is not spec-too-strong / drift. No diverging input exists.

Spec-region integrity: axioms region is an empty documented no-op; resolved is a deep model (A-reference validated by G-AX), not a consumed axiom, so there is no over-strong axiom to exploit. verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + axioms + pure + pre/post-conditions regions; impl region ELIDED to '... implementation elided') does not reveal the gold edit beyond the public problem_statement.

Gold edit: reorder locale_dirs in sphinx/application.py._init_i18n so project sources (repo.locale_dirs) precede the bundled fallback (path.join(package_dir,'locale')), plus an Optional[str] typing change. Net effect: a project-supplied translation overrides the bundled/official one.

Problem statement already makes the DESIRED behavior public: the report states the project locale/da/.../sphinx.po is ignored and the official 'da' (bundled) translation is used instead, and the Expected-behavior section states the project's overriding caption labels ('Foobar 1','Whatever 1') should be used. So 'project translation should win over the bundled one' is public, non-leaking information.

Mechanical checks (all clean): swebench_unified.leakage.screen -> passed=True, hard_failures=[]. No diff markers; no gold-patch line reproduced; patched file paths (sphinx/application.py, sphinx/locale/__init__.py) absent; patched module paths absent; changed symbols {init, init_i18n, repr} do not appear in any spec-view identifier or comment; no bug/fix narration in spec-view comments/strings.

Semantic gold-reconstruction check: the spec models translation resolution as first-wins precedence over an ordered source list [default, project*, bundled], with the decisive clause 'project-supplied source wins over the bundled fallback'. This is the natural abstraction of the publicly-known desired behavior, not a disclosure of the specific list-reordering edit. The precise mechanism of the gold edit (that the fix REORDERS a list, that the pre-patch put the bundled source ahead) lives only in the IMPL region (model_prepatch.py's 'PRE-PATCH (buggy) assembly' comment) and the hidden impl of model.py — both elided from the consumer spec view. A solver seeing the spec learns only what the task already tells them (project override should win); they must still discover WHERE and HOW in the repo to make it so. No spec-view line leaks edit localization beyond the problem_statement.

region hashes: spec_view region present in meta; impl region is separately hashed and not part of spec_view. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
