# P2 adversarial audit — django__django-12273

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_13.py` |

**Non-vacuity.** The positive control `control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,38 +75,7 @@
                                     [[store[i]]])))
     # post-conditions-end
     # impl-start
-    k = 0
-    n = len(target)
-    while k < n:
-        # invariants-start
-        Invariant(Acc(list_pred(store)))
-        Invariant(Acc(list_pred(target), 1 / 2))
-        Invariant(Acc(list_pred(active), 1 / 2))
-        Invariant(len(active) == len(target))
-        Invariant(n == len(target))
-        Invariant(0 <= k and k <= n)
-        Invariant(len(store) == Old(len(store)))
-        Invariant(0 <= pk_idx and pk_idx < len(store))
-        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
-                                                 0 <= target[j] and target[j] < len(store)),
-                                          [[target[j]]])))
-        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
-                                                 Implies(active[j] == 1, target[j] != pk_idx)),
-                                          [[target[j]]])))
-        # slots written so far hold `value`
-        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
-                                                 Implies(active[j] == 1, store[target[j]] == value)),
-                                          [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
-        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
-                                                 Forall(int, lambda j: (Implies(0 <= j and j < k,
-                                                                                Implies(active[j] == 1, target[j] != i)))),
-                                                 store[i] == Old(store[i])),
-                                          [[store[i]]])))
-        Invariant(MustTerminate(n - k + 1))
-        # invariants-end
-        if active[k] == 1:
-            store[target[k]] = value
-        k = k + 1
+    # WRONG (pre-patch behaviour): identity write only, no cascade to the
+    # linked identity slots.
     store[pk_idx] = value
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,11 +93,9 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                  Implies(active[j] == 1, store[target[j]] == value)),
                                           [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
         Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                  Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                 Implies(active[j] == 1, target[j] != i)))),
@@ -108,5 +106,4 @@
         if active[k] == 1:
             store[target[k]] = value
         k = k + 1
-    store[pk_idx] = value
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -77,6 +77,7 @@
     # impl-start
     k = 0
     n = len(target)
+    done = 0
     while k < n:
         # invariants-start
         Invariant(Acc(list_pred(store)))
@@ -93,20 +94,11 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
-        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
-                                                 Implies(active[j] == 1, store[target[j]] == value)),
-                                          [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
-        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
-                                                 Forall(int, lambda j: (Implies(0 <= j and j < k,
-                                                                                Implies(active[j] == 1, target[j] != i)))),
-                                                 store[i] == Old(store[i])),
-                                          [[store[i]]])))
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if active[k] == 1:
+        if active[k] == 1 and done == 0:
             store[target[k]] = value
+            done = 1
         k = k + 1
     store[pk_idx] = value
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
     # impl-start
     k = 0
     n = len(target)
-    while k < n:
+    while k < n - 1:
         # invariants-start
         Invariant(Acc(list_pred(store)))
         Invariant(Acc(list_pred(target), 1 / 2))
@@ -93,11 +93,9 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                  Implies(active[j] == 1, store[target[j]] == value)),
                                           [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
         Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                  Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                 Implies(active[j] == 1, target[j] != i)))),
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,19 +93,12 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                  Implies(active[j] == 1, store[target[j]] == value)),
                                           [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
-        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
-                                                 Forall(int, lambda j: (Implies(0 <= j and j < k,
-                                                                                Implies(active[j] == 1, target[j] != i)))),
-                                                 store[i] == Old(store[i])),
-                                          [[store[i]]])))
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if active[k] == 1:
+        if active[k] != 0:
             store[target[k]] = value
         k = k + 1
     store[pk_idx] = value
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,6 +75,7 @@
                                     [[store[i]]])))
     # post-conditions-end
     # impl-start
+    store[0] = value
     k = 0
     n = len(target)
     while k < n:
@@ -93,16 +94,9 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                  Implies(active[j] == 1, store[target[j]] == value)),
                                           [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
-        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
-                                                 Forall(int, lambda j: (Implies(0 <= j and j < k,
-                                                                                Implies(active[j] == 1, target[j] != i)))),
-                                                 store[i] == Old(store[i])),
-                                          [[store[i]]])))
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
         if active[k] == 1:
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,11 +93,6 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
-        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
-                                                 Implies(active[j] == 1, store[target[j]] == value)),
-                                          [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
         Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                  Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                 Implies(active[j] == 1, target[j] != i)))),
@@ -105,7 +100,7 @@
                                           [[store[i]]])))
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if active[k] == 1:
+        if active[k] == 1 and target[k] != 0:
             store[target[k]] = value
         k = k + 1
     store[pk_idx] = value
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -77,6 +77,7 @@
     # impl-start
     k = 0
     n = len(target)
+    store[pk_idx] = value
     while k < n:
         # invariants-start
         Invariant(Acc(list_pred(store)))
@@ -93,12 +94,11 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
+        Invariant(store[pk_idx] == value)
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                  Implies(active[j] == 1, store[target[j]] == value)),
                                           [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
-        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
+        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and i != pk_idx and
                                                  Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                 Implies(active[j] == 1, target[j] != i)))),
                                                  store[i] == Old(store[i])),
@@ -108,5 +108,4 @@
         if active[k] == 1:
             store[target[k]] = value
         k = k + 1
-    store[pk_idx] = value
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -77,6 +77,7 @@
     # impl-start
     k = 0
     n = len(target)
+    store[pk_idx] = value
     while k < n:
         # invariants-start
         Invariant(Acc(list_pred(store)))
@@ -93,12 +94,11 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
+        Invariant(store[pk_idx] == value)
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                  Implies(active[j] == 1, store[target[j]] == value)),
                                           [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
-        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
+        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and i != pk_idx and
                                                  Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                 Implies(active[j] == 1, target[j] != i)))),
                                                  store[i] == Old(store[i])),
@@ -106,7 +106,6 @@
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
         if active[k] == 1:
-            store[target[k]] = value
+            store[target[k]] = store[pk_idx]
         k = k + 1
-    store[pk_idx] = value
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -93,11 +93,9 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                  Implies(active[j] == 1, store[target[j]] == value)),
                                           [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
         Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                  Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                 Implies(active[j] == 1, target[j] != i)))),
@@ -105,7 +103,7 @@
                                           [[store[i]]])))
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if active[k] == 1:
+        if active[k] == 1 and target[k] != pk_idx:
             store[target[k]] = value
         k = k + 1
     store[pk_idx] = value
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,38 +75,55 @@
                                     [[store[i]]])))
     # post-conditions-end
     # impl-start
+    fresh = []  # type: List[int]
+    c = 0
+    while c < len(store):
+        # invariants-start
+        Invariant(Acc(list_pred(store)))
+        Invariant(Acc(list_pred(fresh)))
+        Invariant(Acc(list_pred(target), 1 / 2))
+        Invariant(Acc(list_pred(active), 1 / 2))
+        Invariant(0 <= c and c <= len(store))
+        Invariant(len(fresh) == c)
+        Invariant(len(store) == Old(len(store)))
+        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < c,
+                                                 fresh[i] == store[i]),
+                                          [[fresh[i]]])))
+        Invariant(MustTerminate(len(store) - c + 1))
+        # invariants-end
+        fresh.append(store[c])
+        c = c + 1
     k = 0
     n = len(target)
     while k < n:
         # invariants-start
         Invariant(Acc(list_pred(store)))
+        Invariant(Acc(list_pred(fresh)))
         Invariant(Acc(list_pred(target), 1 / 2))
         Invariant(Acc(list_pred(active), 1 / 2))
         Invariant(len(active) == len(target))
         Invariant(n == len(target))
         Invariant(0 <= k and k <= n)
+        Invariant(len(fresh) == len(store))
         Invariant(len(store) == Old(len(store)))
         Invariant(0 <= pk_idx and pk_idx < len(store))
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  0 <= target[j] and target[j] < len(store)),
                                           [[target[j]]])))
-        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
-                                                 Implies(active[j] == 1, target[j] != pk_idx)),
+        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
+                                                 Implies(active[j] == 1, fresh[target[j]] == value)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
-        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
-                                                 Implies(active[j] == 1, store[target[j]] == value)),
-                                          [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
         Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                  Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                 Implies(active[j] == 1, target[j] != i)))),
-                                                 store[i] == Old(store[i])),
-                                          [[store[i]]])))
+                                                 fresh[i] == store[i]),
+                                          [[fresh[i]]])))
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
         if active[k] == 1:
-            store[target[k]] = value
+            fresh[target[k]] = value
         k = k + 1
-    store[pk_idx] = value
+    fresh[pk_idx] = value
+    # rebind the parameter name: the caller's list is never mutated.
+    store = fresh
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -77,36 +77,32 @@
     # impl-start
     k = 0
     n = len(target)
-    while k < n:
+    if n == 1:
+        while k < n:
         # invariants-start
-        Invariant(Acc(list_pred(store)))
-        Invariant(Acc(list_pred(target), 1 / 2))
-        Invariant(Acc(list_pred(active), 1 / 2))
-        Invariant(len(active) == len(target))
-        Invariant(n == len(target))
-        Invariant(0 <= k and k <= n)
-        Invariant(len(store) == Old(len(store)))
-        Invariant(0 <= pk_idx and pk_idx < len(store))
-        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
-                                                 0 <= target[j] and target[j] < len(store)),
-                                          [[target[j]]])))
-        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
-                                                 Implies(active[j] == 1, target[j] != pk_idx)),
-                                          [[target[j]]])))
-        # slots written so far hold `value`
-        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
-                                                 Implies(active[j] == 1, store[target[j]] == value)),
-                                          [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
-        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
-                                                 Forall(int, lambda j: (Implies(0 <= j and j < k,
-                                                                                Implies(active[j] == 1, target[j] != i)))),
-                                                 store[i] == Old(store[i])),
-                                          [[store[i]]])))
-        Invariant(MustTerminate(n - k + 1))
+            Invariant(Acc(list_pred(store)))
+            Invariant(Acc(list_pred(target), 1 / 2))
+            Invariant(Acc(list_pred(active), 1 / 2))
+            Invariant(len(active) == len(target))
+            Invariant(n == len(target))
+            Invariant(0 <= k and k <= n)
+            Invariant(len(store) == Old(len(store)))
+            Invariant(0 <= pk_idx and pk_idx < len(store))
+            Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
+                                                     0 <= target[j] and target[j] < len(store)),
+                                              [[target[j]]])))
+            Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
+                                                     Implies(active[j] == 1, store[target[j]] == value)),
+                                              [[target[j]]])))
+            Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
+                                                     Forall(int, lambda j: (Implies(0 <= j and j < k,
+                                                                                    Implies(active[j] == 1, target[j] != i)))),
+                                                     store[i] == Old(store[i])),
+                                              [[store[i]]])))
+            Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if active[k] == 1:
-            store[target[k]] = value
-        k = k + 1
+            if active[k] == 1:
+                store[target[k]] = value
+            k = k + 1
     store[pk_idx] = value
     # impl-end
```

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -93,11 +93,9 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                  Implies(active[j] == 1, store[target[j]] == value)),
                                           [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
         Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                  Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                 Implies(active[j] == 1, target[j] != i)))),
@@ -106,7 +104,11 @@
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
         if active[k] == 1:
-            store[target[k]] = value
+            if target[k] == pk_idx:
+                # DEAD under the frozen precondition -- deliberately wrong here.
+                store[target[k]] = value + 1
+            else:
+                store[target[k]] = value
         k = k + 1
     store[pk_idx] = value
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,11 +93,9 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                  Implies(active[j] == 1, store[target[j]] == value)),
                                           [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
         Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                  Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                 Implies(active[j] == 1, target[j] != i)))),
@@ -105,7 +103,7 @@
                                           [[store[i]]])))
         Invariant(MustTerminate(n - k + 1))
         # invariants-end
-        if active[k] == 1:
+        if active[k] == 1 and value != 0:
             store[target[k]] = value
         k = k + 1
     store[pk_idx] = value
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,20 +93,17 @@
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                  Implies(active[j] == 1, target[j] != pk_idx)),
                                           [[target[j]]])))
-        # slots written so far hold `value`
         Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                  Implies(active[j] == 1, store[target[j]] == value)),
                                           [[target[j]]])))
-        # slots not (yet) targeted by an active link keep their entry value
         Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                  Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                 Implies(active[j] == 1, target[j] != i)))),
                                                  store[i] == Old(store[i])),
                                           [[store[i]]])))
-        Invariant(MustTerminate(n - k + 1))
         # invariants-end
         if active[k] == 1:
             store[target[k]] = value
-        k = k + 1
+        k = k + 0
     store[pk_idx] = value
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `control.py`

```python
"""Twin-artifact model for django__django-12273.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An instance keeps its attribute values in a slot store. One slot is the
  identity slot (the value returned and accepted as the instance's identity).
  Some other slots are "linked identity" slots: they hold the identity value of
  a related ancestor record and, structurally, must always agree with the
  instance's own identity for the record to denote the same logical row.

  Assigning a new identity value to the instance must keep this agreement:
  after the assignment the identity slot holds the new value AND every linked
  identity slot that is genuinely a distinct linked slot (present, and not the
  identity slot itself) also holds the new value. Every unrelated slot keeps
  its previous value.

  This is what lets a fresh identity (e.g. clearing the identity to request a
  brand-new record) take effect across every level of an ancestor chain instead
  of silently keeping the linked slots pointing at the original record.

The instance store is modelled as a `List[int]` of slot values (Nagini bans
attribute reflection). The set of linked-identity slots and which of them are
active (present and distinct from the identity slot) is carried by read-only
metadata lists. The specification is phrased over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# axioms-end

# pure-start
# pure-end

def assign_identity(store: List[int], target: List[int], active: List[int],
                    pk_idx: int, value: int) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(store)))
    Requires(Acc(list_pred(target), 1 / 2))
    Requires(Acc(list_pred(active), 1 / 2))
    Requires(len(active) == len(target))
    Requires(0 <= pk_idx and pk_idx < len(store))
    # each linked slot indexes a real store slot
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                            0 <= target[j] and target[j] < len(store)),
                                     [[target[j]]])))
    # an active linked slot is a distinct slot (not the identity slot itself)
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                            Implies(active[j] == 1, target[j] != pk_idx)))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(store)))
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(active), 1 / 2))
    Ensures(len(store) == Old(len(store)))
    # the identity slot takes the new value
    Ensures(store[pk_idx] == value)
    # every active linked slot also takes the new value
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(target) and j < len(active) and
                                           0 <= target[j] and target[j] < len(store),
                                           Implies(active[j] == 1, store[target[j]] == value)),
                                    [[target[j]]])))
    # every other slot is unchanged
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and i != pk_idx and
                                           Forall(int, lambda j: (Implies(0 <= j and j < len(target) and j < len(active),
                                                                          Implies(active[j] == 1, target[j] != i)))),
                                           store[i] == Old(store[i])),
                                    [[store[i]]])))
    # post-conditions-end
    # impl-start
    k = 0
    n = len(target)
    while k < n:
        # invariants-start
        Invariant(Acc(list_pred(store)))
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(active), 1 / 2))
        Invariant(len(active) == len(target))
        Invariant(n == len(target))
        Invariant(0 <= k and k <= n)
        Invariant(len(store) == Old(len(store)))
        Invariant(0 <= pk_idx and pk_idx < len(store))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                 0 <= target[j] and target[j] < len(store)),
                                          [[target[j]]])))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                 Implies(active[j] == 1, target[j] != pk_idx)),
                                          [[target[j]]])))
        # slots written so far hold `value`
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                 Implies(active[j] == 1, store[target[j]] == value)),
                                          [[target[j]]])))
        # slots not (yet) targeted by an active link keep their entry value
        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                 Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                Implies(active[j] == 1, target[j] != i)))),
                                                 store[i] == Old(store[i])),
                                          [[store[i]]])))
        Invariant(MustTerminate(n - k + 1))
        # invariants-end
        if active[k] == 1:
            store[target[k]] = value
        k = k + 1
    store[pk_idx] = value
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-12273 (nagini). 15 same-spec attacks built by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); `adversary same-spec` returned SAME for all 15 + the control. Verifications were run 3-at-a-time as background jobs (each Nagini check spawns JVM+Z3); every attack was still individually verified. Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-12273 <D>/atk_N.py`.

**WHY THIS SPEC IS TIGHT:** the three postconditions pin the ENTIRE final abstract store, not just part of it — (1) store[pk_idx]==value, (2) every active linked slot ==value, (3) every slot that is neither pk_idx nor an active target is Old(store[i]). Together with len(store)==Old(len(store)) that is a total function of the inputs, so no residual freedom is left for a wrong impl to exploit. That is what the results below show empirically.

REJECTED (exit 2 = same spec, does NOT verify — the spec caught them). 11 of 15:
- atk_1 PREPATCH BUG re-encoded (impl = `store[pk_idx] = value`, no cascade) -> rejected; the missing-cascade postcondition fires. G-DIFF reproduced independently of model_prepatch.py.
- atk_2 cascade but NO identity write (drops the patch-unchanged A5 op) -> rejected.
- atk_3 PARTIAL DOMAIN: cascades to the FIRST active linked slot only (`done` flag) -> rejected.
- atk_4 BOUNDARY: `while k < n - 1`, last linked slot never considered -> rejected.
- atk_5 UNGROUNDED-ORACLE guard: `active[k] != 0` instead of `== 1`, writes slots that must stay unchanged -> rejected by the frame postcondition.
- atk_6 CONTROL-FLOW EFFECT: correct cascade + stray `store[0] = value` -> rejected by the frame postcondition.
- atk_7 PARTIAL DOMAIN 2: refuses to cascade into slot 0 -> rejected.
- atk_11 FRAMING/ALIAS: does all the work on a private copy and rebinds the parameter (`store = fresh`), leaving the caller's list untouched -> rejected. The spec is not satisfiable by a no-op on the real store.
- atk_12 PARTIAL DOMAIN on the F2P split: cascades only when n == 1, so multi-inheritance (Congressman) keeps stale linked identities -> rejected. This is the exact single-vs-multi inheritance distinction of the two F2P tests.
- atk_14 VALUE-CONDITIONAL: cascades only when `value != 0`, special-casing the clear-identity path -> rejected.
- atk_15 DIVERGENCE: correct writes but `k = k + 0` (non-terminating), MustTerminate dropped from the invariants -> rejected. Total correctness is enforced at the method level, not just by loop invariants.

CANDIDATES (exit 0 = same spec AND verifies). 4 of 15 — for EVERY ONE the faithful refined patch was materialized and RUN through the official harness (`python <D>/resolve.py <D>/atk_N.patch <D>/logs/atk_N.resolve.json` -> harness.run_resolve, the real SWE-bench docker oracle). ALL FOUR RESOLVED, i.e. each is a correct ECHO of the gold, not a spec weakness:
- atk_8 (reshape: identity write FIRST, then the cascade) -> completed=True resolved=True note=resolved.
- atk_9 (identity write first; cascade copies store[pk_idx] rather than `value`) -> completed=True resolved=True note=resolved.
- atk_10 (gold order + extra guard `target_field.attname != pk.attname`) -> completed=True resolved=True note=resolved.
- atk_13 (gold order, but the branch the frozen PRECONDITION declares dead — an active parent link whose target slot IS the identity slot — writes `value + 1`) -> completed=True resolved=True attempts=1 flaky=False note=resolved.
Patch-generation machinery was validated first: regenerating the GOLD body through the same path produced a diff whose body is byte-identical to the bundle's patch.diff, and all four attack patches passed `git apply --check` against a worktree at base_commit 927c903f3c. So a non-resolve would have been attributable to the impl, not to my editing.

**POSITIVE CONTROL:** control.py is a byte-identical copy of model.py (md5 39446851fb18b6d97d917b9c4fa6f307 both) -> `weakness` exit 0 (same spec AND verifies).

A-LEG AUDIT (the assignment). The axioms region is EMPTY and there is no @ContractOnly anywhere in model.py, so there is no consumed axiom and no dead axiom — confirmed by grep, and consistent with meta.json axioms == []. The single deep-model reference (meta.json deep_model_references, kind 'A-reference') is assign_identity itself plus its target/active/pk_idx metadata inputs. I did NOT take the bundle's word for the correspondence; I re-derived it three ways against real Django (gold-patched Django 3.2 confirmed by inspect.getsource showing the `parent_link != self._meta.pk` cascade):
1. <D>/aleg_probe2.py — transliterated assign_identity over an attname-keyed slot store, refined exactly per mapping.md 2 (parents.values() ORDER included, active[k] = pl and pl != `_meta`.pk, target[k] = slot(pl.target_field.attname)), and compared it slot-for-slot against the REAL `instance.pk = value` on the actual F2P models (Profile(User), Congressman(Person,Politician)) plus Senator (3-level chain), over value in {None,0,1,-3,12345,`2**31`,`2**63`+7}. 21/21 observations agree exactly, including the None/clear-identity F2P path. Observed: Profile pk=profile_id active=['id']; Congressman pk=person_ptr_id active=['politician_id'] (the promoted-pk parent link person_ptr correctly EXCLUDED); Senator pk=congressman_ptr_id active=[] (empty-active case). This is the A2/A4/A5 correspondence of refinement.md, independently reproduced.
2. <D>/aleg_probe.py — reachability of the precondition `active[j]==1 ==> target[j] != pk_idx` across 8 structural shapes, including adversarial ones (explicit parent_link used AS the pk, two parent links to different parents, explicit non-pk parent_link alongside an own pk, 3-level chain). NO shape reaches an active parent link whose target_field.attname equals `_meta`.pk.attname.
3. <D>/aleg_probe3.py — attacked the only route that could violate it, an attname COLLISION between the child's own pk and an ancestor's pk. Django's ModelBase metaclass REJECTS all three collision shapes with FieldError ("Local field 'id' in class 'Kid1' clashes with field of the same name from base class 'Base1'"). So the precondition is STRUCTURALLY GUARANTEED by Django, not an assumption that narrows the claim away from inputs the real callee receives — which is exactly why atk_13's deliberately-corrupted branch is dead in the real code too and its patch resolves.

**REFINEMENT.MD LEG AUDIT:** 5 legs, tags A1=R, A2=R + A-reference, A3=R, A4=I (under R for the carriers), A5=I (under R). Every leg is R / A-reference / I; there are ZERO A-consumed legs (consistent with the empty axioms region) and NO kind-3 step. The one genuinely CHANGED operation — the propagation loop — is modeled DEEPLY as the spelled-out guarded write loop (A4), not hidden behind an axiom about the function under change, which is the property that matters most for verify=>correct here. Sections B/C/D of refinement.md accurately describe what I re-measured; the claimed A-reference correspondence holds.

OBSERVATION (not a G-EQ defect, flagged for the record): meta.json records G-AX status=pass with detail "G-AX SKIP: Django not configurable in this environment: ModuleNotFoundError('No module named axcheck')" — i.e. the recorded G-AX run SKIPPED (axiom_check.py's main() returns 0 on that path) and never executed its assertions. I hit the identical failure and fixed it by creating a real importable app package, then ran the equivalent checks myself; they PASS (probes 1-3 above). So the A-reference is in fact sound, but the bundle's own G-AX stamp is not evidence of it — the pass came from the skip branch, and that is worth repairing in axiom_check.py / the gate wiring so a genuinely-false A-reference could not pass the same way.

**VERDICT:** SOUND. 15 admissible same-spec attacks run (11 rejected by the spec, 4 verifying candidates all of whose faithful refined patches RESOLVE under the official docker oracle), prepatch bug reproduced and rejected, positive control verifies. No verifying wrong impl whose faithful patch fails to resolve was found, so no verify=>correct break is exhibited.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_13.py` |

**Non-vacuity.** The positive control `control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `control.py`

```python
"""Twin-artifact model for django__django-12273.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An instance keeps its attribute values in a slot store. One slot is the
  identity slot (the value returned and accepted as the instance's identity).
  Some other slots are "linked identity" slots: they hold the identity value of
  a related ancestor record and, structurally, must always agree with the
  instance's own identity for the record to denote the same logical row.

  Assigning a new identity value to the instance must keep this agreement:
  after the assignment the identity slot holds the new value AND every linked
  identity slot that is genuinely a distinct linked slot (present, and not the
  identity slot itself) also holds the new value. Every unrelated slot keeps
  its previous value.

  This is what lets a fresh identity (e.g. clearing the identity to request a
  brand-new record) take effect across every level of an ancestor chain instead
  of silently keeping the linked slots pointing at the original record.

The instance store is modelled as a `List[int]` of slot values (Nagini bans
attribute reflection). The set of linked-identity slots and which of them are
active (present and distinct from the identity slot) is carried by read-only
metadata lists. The specification is phrased over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# axioms-end

# pure-start
# pure-end

def assign_identity(store: List[int], target: List[int], active: List[int],
                    pk_idx: int, value: int) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(store)))
    Requires(Acc(list_pred(target), 1 / 2))
    Requires(Acc(list_pred(active), 1 / 2))
    Requires(len(active) == len(target))
    Requires(0 <= pk_idx and pk_idx < len(store))
    # each linked slot indexes a real store slot
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                            0 <= target[j] and target[j] < len(store)),
                                     [[target[j]]])))
    # an active linked slot is a distinct slot (not the identity slot itself)
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                            Implies(active[j] == 1, target[j] != pk_idx)))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(store)))
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(active), 1 / 2))
    Ensures(len(store) == Old(len(store)))
    # the identity slot takes the new value
    Ensures(store[pk_idx] == value)
    # every active linked slot also takes the new value
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(target) and j < len(active) and
                                           0 <= target[j] and target[j] < len(store),
                                           Implies(active[j] == 1, store[target[j]] == value)),
                                    [[target[j]]])))
    # every other slot is unchanged
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and i != pk_idx and
                                           Forall(int, lambda j: (Implies(0 <= j and j < len(target) and j < len(active),
                                                                          Implies(active[j] == 1, target[j] != i)))),
                                           store[i] == Old(store[i])),
                                    [[store[i]]])))
    # post-conditions-end
    # impl-start
    k = 0
    n = len(target)
    while k < n:
        # invariants-start
        Invariant(Acc(list_pred(store)))
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(active), 1 / 2))
        Invariant(len(active) == len(target))
        Invariant(n == len(target))
        Invariant(0 <= k and k <= n)
        Invariant(len(store) == Old(len(store)))
        Invariant(0 <= pk_idx and pk_idx < len(store))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                 0 <= target[j] and target[j] < len(store)),
                                          [[target[j]]])))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(target),
                                                 Implies(active[j] == 1, target[j] != pk_idx)),
                                          [[target[j]]])))
        # slots written so far hold `value`
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                 Implies(active[j] == 1, store[target[j]] == value)),
                                          [[target[j]]])))
        # slots not (yet) targeted by an active link keep their entry value
        Invariant(Forall(int, lambda i: (Implies(0 <= i and i < len(store) and
                                                 Forall(int, lambda j: (Implies(0 <= j and j < k,
                                                                                Implies(active[j] == 1, target[j] != i)))),
                                                 store[i] == Old(store[i])),
                                          [[store[i]]])))
        Invariant(MustTerminate(n - k + 1))
        # invariants-end
        if active[k] == 1:
            store[target[k]] = value
        k = k + 1
    store[pk_idx] = value
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-12273 (nagini). 15 same-spec attacks built by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); `adversary same-spec` returned SAME for all 15 + the control. Verifications were run 3-at-a-time as background jobs (each Nagini check spawns JVM+Z3); every attack was still individually verified. Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-12273 <D>/atk_N.py`.

**WHY THIS SPEC IS TIGHT:** the three postconditions pin the ENTIRE final abstract store, not just part of it — (1) store[pk_idx]==value, (2) every active linked slot ==value, (3) every slot that is neither pk_idx nor an active target is Old(store[i]). Together with len(store)==Old(len(store)) that is a total function of the inputs, so no residual freedom is left for a wrong impl to exploit. That is what the results below show empirically.

REJECTED (exit 2 = same spec, does NOT verify — the spec caught them). 11 of 15:
- atk_1 PREPATCH BUG re-encoded (impl = `store[pk_idx] = value`, no cascade) -> rejected; the missing-cascade postcondition fires. G-DIFF reproduced independently of model_prepatch.py.
- atk_2 cascade but NO identity write (drops the patch-unchanged A5 op) -> rejected.
- atk_3 PARTIAL DOMAIN: cascades to the FIRST active linked slot only (`done` flag) -> rejected.
- atk_4 BOUNDARY: `while k < n - 1`, last linked slot never considered -> rejected.
- atk_5 UNGROUNDED-ORACLE guard: `active[k] != 0` instead of `== 1`, writes slots that must stay unchanged -> rejected by the frame postcondition.
- atk_6 CONTROL-FLOW EFFECT: correct cascade + stray `store[0] = value` -> rejected by the frame postcondition.
- atk_7 PARTIAL DOMAIN 2: refuses to cascade into slot 0 -> rejected.
- atk_11 FRAMING/ALIAS: does all the work on a private copy and rebinds the parameter (`store = fresh`), leaving the caller's list untouched -> rejected. The spec is not satisfiable by a no-op on the real store.
- atk_12 PARTIAL DOMAIN on the F2P split: cascades only when n == 1, so multi-inheritance (Congressman) keeps stale linked identities -> rejected. This is the exact single-vs-multi inheritance distinction of the two F2P tests.
- atk_14 VALUE-CONDITIONAL: cascades only when `value != 0`, special-casing the clear-identity path -> rejected.
- atk_15 DIVERGENCE: correct writes but `k = k + 0` (non-terminating), MustTerminate dropped from the invariants -> rejected. Total correctness is enforced at the method level, not just by loop invariants.

CANDIDATES (exit 0 = same spec AND verifies). 4 of 15 — for EVERY ONE the faithful refined patch was materialized and RUN through the official harness (`python <D>/resolve.py <D>/atk_N.patch <D>/logs/atk_N.resolve.json` -> harness.run_resolve, the real SWE-bench docker oracle). ALL FOUR RESOLVED, i.e. each is a correct ECHO of the gold, not a spec weakness:
- atk_8 (reshape: identity write FIRST, then the cascade) -> completed=True resolved=True note=resolved.
- atk_9 (identity write first; cascade copies store[pk_idx] rather than `value`) -> completed=True resolved=True note=resolved.
- atk_10 (gold order + extra guard `target_field.attname != pk.attname`) -> completed=True resolved=True note=resolved.
- atk_13 (gold order, but the branch the frozen PRECONDITION declares dead — an active parent link whose target slot IS the identity slot — writes `value + 1`) -> completed=True resolved=True attempts=1 flaky=False note=resolved.
Patch-generation machinery was validated first: regenerating the GOLD body through the same path produced a diff whose body is byte-identical to the bundle's patch.diff, and all four attack patches passed `git apply --check` against a worktree at base_commit 927c903f3c. So a non-resolve would have been attributable to the impl, not to my editing.

**POSITIVE CONTROL:** control.py is a byte-identical copy of model.py (md5 39446851fb18b6d97d917b9c4fa6f307 both) -> `weakness` exit 0 (same spec AND verifies).

A-LEG AUDIT (the assignment). The axioms region is EMPTY and there is no @ContractOnly anywhere in model.py, so there is no consumed axiom and no dead axiom — confirmed by grep, and consistent with meta.json axioms == []. The single deep-model reference (meta.json deep_model_references, kind 'A-reference') is assign_identity itself plus its target/active/pk_idx metadata inputs. I did NOT take the bundle's word for the correspondence; I re-derived it three ways against real Django (gold-patched Django 3.2 confirmed by inspect.getsource showing the `parent_link != self._meta.pk` cascade):
1. <D>/aleg_probe2.py — transliterated assign_identity over an attname-keyed slot store, refined exactly per mapping.md 2 (parents.values() ORDER included, active[k] = pl and pl != `_meta`.pk, target[k] = slot(pl.target_field.attname)), and compared it slot-for-slot against the REAL `instance.pk = value` on the actual F2P models (Profile(User), Congressman(Person,Politician)) plus Senator (3-level chain), over value in {None,0,1,-3,12345,`2**31`,`2**63`+7}. 21/21 observations agree exactly, including the None/clear-identity F2P path. Observed: Profile pk=profile_id active=['id']; Congressman pk=person_ptr_id active=['politician_id'] (the promoted-pk parent link person_ptr correctly EXCLUDED); Senator pk=congressman_ptr_id active=[] (empty-active case). This is the A2/A4/A5 correspondence of refinement.md, independently reproduced.
2. <D>/aleg_probe.py — reachability of the precondition `active[j]==1 ==> target[j] != pk_idx` across 8 structural shapes, including adversarial ones (explicit parent_link used AS the pk, two parent links to different parents, explicit non-pk parent_link alongside an own pk, 3-level chain). NO shape reaches an active parent link whose target_field.attname equals `_meta`.pk.attname.
3. <D>/aleg_probe3.py — attacked the only route that could violate it, an attname COLLISION between the child's own pk and an ancestor's pk. Django's ModelBase metaclass REJECTS all three collision shapes with FieldError ("Local field 'id' in class 'Kid1' clashes with field of the same name from base class 'Base1'"). So the precondition is STRUCTURALLY GUARANTEED by Django, not an assumption that narrows the claim away from inputs the real callee receives — which is exactly why atk_13's deliberately-corrupted branch is dead in the real code too and its patch resolves.

**REFINEMENT.MD LEG AUDIT:** 5 legs, tags A1=R, A2=R + A-reference, A3=R, A4=I (under R for the carriers), A5=I (under R). Every leg is R / A-reference / I; there are ZERO A-consumed legs (consistent with the empty axioms region) and NO kind-3 step. The one genuinely CHANGED operation — the propagation loop — is modeled DEEPLY as the spelled-out guarded write loop (A4), not hidden behind an axiom about the function under change, which is the property that matters most for verify=>correct here. Sections B/C/D of refinement.md accurately describe what I re-measured; the claimed A-reference correspondence holds.

OBSERVATION (not a G-EQ defect, flagged for the record): meta.json records G-AX status=pass with detail "G-AX SKIP: Django not configurable in this environment: ModuleNotFoundError('No module named axcheck')" — i.e. the recorded G-AX run SKIPPED (axiom_check.py's main() returns 0 on that path) and never executed its assertions. I hit the identical failure and fixed it by creating a real importable app package, then ran the equivalent checks myself; they PASS (probes 1-3 above). So the A-reference is in fact sound, but the bundle's own G-AX stamp is not evidence of it — the pass came from the skip branch, and that is worth repairing in axiom_check.py / the gate wiring so a genuinely-false A-reference could not pass the same way.

**VERDICT:** SOUND. 15 admissible same-spec attacks run (11 rejected by the spec, 4 verifying candidates all of whose faithful refined patches RESOLVE under the official docker oracle), prepatch bug reproduced and rejected, positive control verifies. No verifying wrong impl whose faithful patch fails to resolve was found, so no verify=>correct break is exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SPEC REGION INTEGRITY
- `python -m swebench_unified.adversary same-spec nagini django__django-12273 ident.py` -> exit 0 ("SAME — attack shares the bundle's exact specification"). Spec region byte-identical; I did not modify the bundle (all work).

### REFERENCE SETUP (per instructions: base_commit worktree WITH patch.diff APPLIED)
- Cloned django/django at base_commit 927c903f3cd25c817c21738328b53991c035b415 to, applied the gold hunk to django/db/models/base.py:571 (`_set_pk_val`), and confirmed the 3 added lines are present. All probes ran against THAT patched tree (verified via runtests banner "Testing against Django installed in ''" — an earlier run accidentally resolved a stale  worktree and was re-run pinned with PYTHONPATH).

### WHAT THE SPEC CLAIMS (modeled fn: Model.`_set_pk_val`, base.py:571, via the pk property setter)
  POST1 store[pk_idx]==value; POST2 every active[j]==1 -> store[target[j]]==value; POST3 every other slot unchanged.
  active[k] == (parent_link and parent_link != self.`_meta`.pk); target[k] == slot(parent_link.target_field.attname).

EVIDENCE 1 — spec is not too strong against a gold-faithful impl
- `bash scripts/nagini_verify.sh model.py` -> "Verification successful" (27.8s), exit 0. The gold-shaped impl (guarded cascade loop + pk write) discharges all three postconditions.

EVIDENCE 2 — the real patched callee satisfies all three postconditions, slot-for-slot
Drove the REAL patched `instance.pk = value` and re-derived pk_attname/active from the REAL `_meta` the same way the model abstracts it. Shapes and their measured metadata:
  Profile(User)         pk=profile_id      active=['id']                  <- exact F2P shape 1
  Congressman(Person,Politician) pk=person_ptr_id active=['politician_id'] <- exact F2P shape 2 (promoted-pk link person_ptr correctly EXCLUDED)
  Kid(Mid(GP)) own pks  pk=kid_id          active=['mid_id']
  A2(A1(A0)) promoted   pk=a1_ptr_id       active=[]
  Expl(PB,QB) explicit  pk=pb_ptr_id       active=['qb_id']
  AbsKid abstract-mid   pk=gp_ptr_id       active=[]
  User (no parents)     pk=id              active=[]
  D2(D1,D0) diamond     pk=d1_ptr_id       active=['id']
  G1(H0,G0) to_field    pk=h0_ptr_id       active=['code']   <- cascade target is a NON-pk unique CharField
  C2(P2) to_field-pk    pk=p2_ptr_id       active=[]
  L3 4-level mixed      pk=l3_id           active=['l1_ptr_id']
  TC(T1,T2,T3) triple   pk=t1_ptr_id       active=['t2_id','t3_id']  <- TWO active links, both cascaded
  F1 proxy              pk=id              active=[]  <- parent_link is None, guard's `parent_link and` half exercised
  MX abstract-mixin     pk=f0_ptr_id       active=[]
Each shape x {None,0,1,7,-3,-5,`2**31`,`2**63`+7,'strval'}, every attname slot pre-seeded with a distinct sentinel so POST3 is maximally sensitive.
  => POSTCONDITION VIOLATIONS: 0. PRECONDITION EXCLUSIONS: 0. Non-attname `__dict__` churn: NONE.
- Bundle's own axiom_check.py against the patched tree -> "G-AX OK... 12 observations", exit 0.

EVIDENCE 3 — the guard encoding is exactly right, incl. the subtle field-vs-slot question
The gold guard compares FIELDS (`parent_link != self._meta.pk`, and Field.`__eq__` compares creation_counter) while the spec precondition compares SLOTS (`target[j] != pk_idx`). I specifically hunted for a divergence between those two comparisons and could not construct a check()-clean one (see counterexample). In every valid shape, field-inequality and slot-inequality coincide. Notably in Congressman and Expl the promoted parent link IS the pk and is excluded, and its target slot equals pk_idx — consistent, because active=0 there so the precondition's implication is not triggered.

EVIDENCE 4 — G-DIFF: the cascade postcondition is non-vacuous
- `nagini_verify.sh model_prepatch.py` -> "Verification failed", and the single reported error is precisely the cascade postcondition (POST2, model_prepatch.py:66-69). Confirms POST2 has real discriminating content and is not trivially satisfiable.
- F2P tests on the patched worktree: `runtests.py model_inheritance_regress` -> Ran 30 tests, OK (expected failures=1), including both F2P tests.

ONE UNMODELED EFFECT — examined and judged NOT a faithfulness defect
When a cascade target attname is itself an FK attname, its descriptor is ForeignKeyDeferredAttribute, whose `__set__` evicts the cached related object. Measured on L3: `_state.fields_cache` went from ['l1_ptr','l2_ptr'] to ['l2_ptr'] across `obj.pk = None`. This is real state the List[int] slot abstraction does not carry. It is nevertheless NOT an unfaithfulness:
  (a) it contradicts no postcondition — POST3 quantifies over attname-indexed concrete-field slots, and `_state`.fields_cache is not such a slot; the slot deltas were exactly {l1_ptr_id, l3_id}, i.e. precisely POST1+POST2 and nothing else, so POST3 held.
  (b) it is a consequence of the very setattr the model models, and the gold patch produces it identically — so it cannot make a spec-satisfying impl diverge from gold or break resolution.
  (c) a spec being SILENT about an extra effect is an under-specification (a G-PANEL-1 spec-too-weak axis), not a too-strong claim; this gate asks whether the modeled function DISAGREES with the real callee, and it does not.

**CONCLUSION:** FAITHFUL. The spec is neither too strong nor drifted. Its preconditions are genuine structural invariants of real Django `_meta` (every attempt to violate them yields a model Django rejects with models.E006 or a class-creation FieldError), and its postconditions match the real patched `_set_pk_val` slot-for-slot on 90+ observations spanning 15 MTI shapes — single/multi/diamond/triple inheritance, promoted and own pks, to_field parent links, proxies (parent_link=None), abstract mid-levels, and 4-level chains. Positive control verifies; prepatch control fails exactly the cascade clause.

Counterexample / evidence:

```
Attempted precondition-breach shapes, all rejected by Django itself so they are not real inputs:

(A4) class GP(Model){gp_id=AutoField(pk)}; class Mid(GP){}; class Kid(Mid){gp_ptr_id=AutoField(primary_key=True)}
  -> Mid promotes gp_ptr, so Mid._meta.pk.attname=='gp_ptr_id'; Kid declares its own pk literally named 'gp_ptr_id'.
  -> RESULT: pk='gp_ptr_id', link ('mid_ptr','gp_ptr_id',active=1) => active target == pk slot, breaching the precondition.
  -> BUT Kid.check() == [models.E006 (level=40) "The field 'gp_ptr_id' clashes with the field 'gp_ptr' from model 'px.mid'"]. Hard system-check error; not a valid Django model.

(A1) class Pa(Model){x}; class Pb(Model){pa_ptr_id=CharField(unique=True, primary_key=True)}; class Ch1(Pa,Pb){}
  -> pk='pa_ptr_id', links [('pa_ptr','id',0), ('pb_ptr','pa_ptr_id',1)] => active target == pk slot.
  -> BUT Ch1.check() == [models.E006 (level=40)]. Also rejected.

(A3) class Ch3(Ra,Rb){rb_id=AutoField(primary_key=True)} -> rejected even harder, at class-creation time: FieldError "Local field 'rb_id' in class 'Ch3' clashes with field of the same name from base class 'Rb'."

(A2) class Ch2(Qa,Qb){qa_ptr=OneToOneField(Qa,parent_link=True,primary_key=True,to_field='qa_id')} -> check() CLEAN, but pk='qa_ptr_id' and the only active link is ('qb_ptr','qb_id',1); target != pk. Precondition SATISFIED, all 3 postconditions hold. No breach.

SUMMARY: check()-clean models breaching the spec precondition = NONE. The precondition is a real structural invariant of Django _meta, not a smuggled-in strengthening that excludes inputs the real callee receives.
```

### Spec region integrity
- `python -m swebench_unified.adversary same-spec nagini django__django-12273 ident.py` -> exit 0 ("SAME — attack shares the bundle's exact specification"). Spec region byte-identical; I did not modify the bundle (all work).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. No relaxation in this bundle: meta.json has no `relaxed_leakage` key (checked: `'relaxed_leakage' in meta` -> False) and there is no RELAXED_LEAKAGE.md anywhere under benchmark-verified/django__django-12273/ (find -iname '*RELAX*' -> empty). So this is judged as an ordinary strict no-leakage review, not a relaxation review.

**WHAT THE CONSUMER SEES.** Reconstructed the consumer view myself with markers.spec_view(model.py, get_backend('nagini').language): docstring + imports + empty axioms/pure regions + `assign_identity(store, target, active, pk_idx, value)` signature + pre/post-conditions; impl region replaced by the elision placeholder (invariants are inside impl and are gone with it). Spec region is byte-identical to the bundle's: `adversary same-spec nagini django__django-12273 atk.py` -> exit 0 ("SAME"). Recomputed markers.region_hashes on the current model.py and it matches the digests recorded under gates.G-HYGIENE.data.region_hashes exactly (spec_view 88a5198e..., pre ee64d2ae..., post e43251a2..., impl bc5034c8..., invariants 7d134c98...), so the view I judged is the view the gates were stamped on.

BASELINE RE-DERIVED (and a correction to the prior record). Leakage baseline = problem_statement ONLY. The PS is just the bug report: `Item` with `uid = AutoField(primary_key=True)`, `class Derived(Item)`, `reset()` setting `self.uid = None`, and "setting the primary key to None does not work (so that the existing object is overwritten on save())", plus the failing TestCase and "Django 2.1.2". IMPORTANT: the previously recorded G-PANEL-3 justification (meta.json gates.G-PANEL.data.roles['G-PANEL-3'].detail, echoed in verdict.md) defends itself by quoting "create a copy of a Derived object... all fields of the Derived model and all fields of its base models... several levels of inheritance" as being "ALREADY public in problem_statement". That text is NOT in problem_statement -- it is in hints_text (Victor's replies), which is explicitly excluded from the baseline, and hints_text also carries a literal candidate diff for `_set_pk_val`. The prior record therefore judged against an inflated baseline. I re-ran the judgement on the narrower PS-only baseline and still reach NO-LEAKAGE, for the reasons below.

### Why NO-LEAKAGE on the ps-only baseline
(1) No gold identifier, path, or diff line reaches the view. Spec-view identifiers are `assign_identity`, `store`, `target`, `active`, `pk_idx`, `value` -- none of `_set_pk_val`, `_meta`, `parents`, `parent_link`, `target_field`, `attname`, `setattr`, `item_ptr`, `django/db/models/base.py`. Tokenized the view (len>3, lowercased) against the gold patch's tokens: the only intersection is {none, value, values}, all generic. Words present in hints_text but absent from problem_statement were all ordinary English (after, also, assignment, instance, keep, level, only, other, real, some, target, this, what, which, with) -- no hints-only technical vocabulary (nothing like `parent_link`/`item_ptr`/`target_field`) is echoed. Re-ran the mechanical screen independently (leakage.screen on the raw model.py with the frozen patch + PS + test_patch): passed=True, hard_failures=[], warnings=[], consistent with the recorded G-LEAK "spec view clean".

(2) The gold's actual discriminating MECHANICS are absent. The gold edit is `for parent_link in self._meta.parents.values(): if parent_link and parent_link != self._meta.pk: setattr(self, parent_link.target_field.attname, value)`. In the view, the whole guard is collapsed into an OPAQUE input flag `active[k]==1`; nothing tells a consumer that `active` means "present AND not the pk field", nor that the write target is `target_field.attname`, nor that the iteration is over `_meta.parents.values()`. The `Requires(... Implies(active[j]==1, target[j] != pk_idx))` clause reads as a well-formedness assumption on the caller's inputs (an active link is a distinct slot), not as the promoted-pk exclusion a solver must invent. That Django-level vocabulary lives only in mapping.md §3.2 and refinement.md A2/A4, which are auditor-only and not in the spec view.

(3) What the view DOES state is the behavioral obligation of the modeled function, which is what a spec is for -- and it does not exceed the PS. The postconditions say: identity slot takes `value`; every active linked slot takes `value`; every other slot unchanged. Also note mode 1/2 hands the consumer the repo localization separately (prompts.py renders "Modeled function(s): model_symbol (<-> repo_symbol)"), so knowing WHERE is by design; the spec view's remaining job is WHAT, and stating the post-state of the assignment is unavoidable for any spec of this function. The PS itself supplies the symptom this abstracts ("the existing object is overwritten on save()" == the record still denotes the original row), and that an MTI child carries the ancestor's identity is public Django structure visible at base_commit, not hidden-test or hints content.

(4) No test reconstruction. The view names none of Profile/User/Congressman/Person/Politician, no test path/name/id, and enumerates no cases mirroring the two F2P tests; `target`/`active` as parallel lists is the general form, not the tests' single- vs multi-inheritance parametrization.

LOAD-BEARING CHECK (usual test, run even though no relaxation is claimed). The prose is NOT what discriminates -- the postconditions are -- so there is no "the narration had to stay" argument being smuggled in, and nothing to relax. Ran the pinned verifier directly: gold model.py -> exit 0 ("Verification successful", 25.3s); model_prepatch.py (impl = the single `store[pk_idx] = value` write, no loop) -> exit 1, failing exactly `Forall(j... Implies(active[j]==1, store[target[j]] == value))`, i.e. the cascade postcondition, reproducing the recorded G-DIFF. I also probed the one precondition that could have been doing hidden work: deleting the `Implies(active[j]==1, target[j] != pk_idx)` Requires makes the model fail (loop invariant not established on entry), so it is a genuine input assumption, not a smuggled fix instruction.

ADVISORY (not a leak, so not submitted as one). The docstring's last sentence -- "... instead of silently keeping the linked slots pointing at the original record" -- is the closest thing to fix-narration in the view: it states the pre-change behavior. I judged it non-leaking because it adds nothing beyond (a) the PS's own "the existing object is overwritten on save()" and (b) the formal postconditions already in the view, and because it is not load-bearing (see above), so it could be dropped at zero cost if a future pass wants the view tighter. Similarly "across every level of an ancestor chain" over-generalizes relative to the gold (which iterates one level of `_meta.parents`, non-recursively), so it under-describes rather than reconstructs the edit.

**BUNDLE HYGIENE OBSERVATIONS.** (a) Nothing in the bundle addresses the reviewer or prescribes a verdict: leakage.reviewer_directed(meta.json) -> [], and a grep for reviewer/panel/attacker/record-directed phrasing across model.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, properties.py found nothing. verdict.md does carry the PRIOR panel verdicts including a prior "NO-LEAKAGE" for this role; it is a backfill-generated record rather than an instruction, but it is anchoring material, so I derived the view, the baseline, and every measurement above independently before reading it, and I am reporting its PS/hints mis-attribution as a finding against it.

(b) meta.json's TOP-LEVEL `region_hashes` block is stale relative to the current model.py (impl d0340b5b..., pre 4ec46ff9..., invariants ce9376c2..., spec_view b92c7f1f... -- only post-conditions matches). It disagrees with the per-gate hashes recorded by G-HYGIENE, which DO match the current file. I traced consumers: region_hashes is only ever recomputed live in gates/hygiene.py (lines 70/175/376) and defined in markers.py:338; the top-level meta field is read by no gate, so this is stale bookkeeping from an earlier revision rather than an unsound gate -- worth cleaning, but it does not affect this verdict.

(c) Recorded G-AX is a SKIP-as-pass ("Django not configurable in this environment: No module named 'axcheck'"), i.e. axiom_check.py's A-reference was not actually executed in that stamp. That is a G-AX/faithfulness concern, not a leakage one, and it does not bear on whether the view discloses the edit; flagging it so it is on the record.

**EVIDENCE COMMANDS.** markers.spec_view + markers.region_hashes (recomputed, matched G-HYGIENE); `python -m swebench_unified.adversary same-spec nagini django__django-12273 atk.py` -> 0; `bash scripts/nagini_verify.sh atk.py` -> 0; `bash scripts/nagini_verify.sh model_prepatch.py` -> 1 (cascade postcondition); `bash scripts/nagini_verify.sh nopre.py` (distinctness Requires removed) -> 1; leakage.screen(model.py,...) -> passed, no failures; token-overlap analysis of the view against patch/hints/PS. the bundle was not modified.

**SCOPE.** No relaxation in this bundle: meta.json has no `relaxed_leakage` key (checked: `'relaxed_leakage' in meta` -> False) and there is no RELAXED_LEAKAGE.md anywhere under benchmark-verified/django__django-12273/ (find -iname '*RELAX*' -> empty). So this is judged as an ordinary strict no-leakage review, not a relaxation review.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
