# P2 adversarial audit — django__django-10880

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_10.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec, Nagini-VERIFYING implementation was found whose faithful refined patch fails to resolve. The only three same-spec files that verified (positive_control, atk_5, atk_10) are all behaviour-preserving re-encodings of the gold render, and all three materialized faithful patches RESOLVED under the official harness (F2P test_count_distinct_expression success=1, P2P success=55, failure=0 on each). verify => correct holds on every probe run.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -140,11 +135,6 @@
         result.append(78)
         result.append(67)
         result.append(84)
-        result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
     k = 0
     while k < len(operands):
         # invariants-start
@@ -153,13 +143,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(operands))
         Invariant(ToSeq(result)
-                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
+                  == ToSeq(function) + open_paren() + (kw_distinct() if distinct else PSeq(0).take(0)) + ToSeq(operands).take(k))
         Invariant(MustTerminate(len(operands) - k + 1))
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -140,11 +135,8 @@
         result.append(78)
         result.append(67)
         result.append(84)
-        result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
+        if len(operands) > 0:
+            result.append(32)
     k = 0
     while k < len(operands):
         # invariants-start
@@ -153,13 +145,13 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(operands))
         Invariant(ToSeq(result)
-                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
+                  == ToSeq(function) + open_paren()
+                     + (kw_distinct() if distinct else PSeq(0).take(0))
+                     + (PSeq(sep()) if distinct and len(operands) > 0 else PSeq(0).take(0)) + ToSeq(operands).take(k))
         Invariant(MustTerminate(len(operands) - k + 1))
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,12 +125,9 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
+        result.append(32)
         result.append(68)
         result.append(73)
         result.append(83)
@@ -140,11 +136,6 @@
         result.append(78)
         result.append(67)
         result.append(84)
-        result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
     k = 0
     while k < len(operands):
         # invariants-start
@@ -153,13 +144,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(operands))
         Invariant(ToSeq(result)
-                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
+                  == ToSeq(function) + open_paren() + (PSeq(sep()) + kw_distinct() if distinct else PSeq(0).take(0)) + ToSeq(operands).take(k))
         Invariant(MustTerminate(len(operands) - k + 1))
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -141,10 +136,6 @@
         result.append(67)
         result.append(84)
         result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
     k = 0
     while k < len(operands):
         # invariants-start
@@ -158,8 +149,7 @@
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
+    operands.append(32)
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -140,11 +135,9 @@
         result.append(78)
         result.append(67)
         result.append(84)
-        result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
+        result.append(sep())
+        Assert(ToSeq(result) == ToSeq(function) + open_paren() + kw_distinct()
+               + PSeq(sep()))
     k = 0
     while k < len(operands):
         # invariants-start
@@ -158,8 +151,6 @@
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -140,11 +135,7 @@
         result.append(78)
         result.append(67)
         result.append(84)
-        result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
+        result.append(9)
     k = 0
     while k < len(operands):
         # invariants-start
@@ -153,13 +144,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(operands))
         Invariant(ToSeq(result)
-                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
+                  == ToSeq(function) + open_paren() + (kw_distinct() + PSeq(9) if distinct else PSeq(0).take(0)) + ToSeq(operands).take(k))
         Invariant(MustTerminate(len(operands) - k + 1))
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -141,10 +136,6 @@
         result.append(67)
         result.append(84)
         result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
     k = 0
     while k < len(operands):
         # invariants-start
@@ -153,13 +144,12 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(operands))
         Invariant(ToSeq(result)
-                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
-        Invariant(MustTerminate(len(operands) - k + 1))
+                  == ToSeq(function) + open_paren() + modifier(distinct)
+                  + ToSeq(operands).take(k))
         # invariants-end
-        result.append(operands[k])
-        k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
+        if operands[k] != 32:
+            result.append(operands[k])
+            k = k + 1
     result.append(41)
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -141,10 +136,7 @@
         result.append(67)
         result.append(84)
         result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
+        result.append(32)
     k = 0
     while k < len(operands):
         # invariants-start
@@ -153,13 +145,12 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(operands))
         Invariant(ToSeq(result)
-                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
+                  == ToSeq(function) + open_paren() + (kw_distinct() + PSeq(sep()) + PSeq(sep())
+                     if distinct else PSeq(0).take(0)) + ToSeq(operands).take(k))
         Invariant(MustTerminate(len(operands) - k + 1))
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
     return result
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -140,11 +135,6 @@
         result.append(78)
         result.append(67)
         result.append(84)
-        result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
     k = 0
     while k < len(operands):
         # invariants-start
@@ -153,13 +143,15 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(operands))
         Invariant(ToSeq(result)
-                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
+                  == ToSeq(function) + open_paren()
+                  + (kw_distinct() if distinct else PSeq(0).take(0))
+                  + ToSeq(operands).take(k))
         Invariant(MustTerminate(len(operands) - k + 1))
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
+    if distinct:
+        result.append(32)
     result.append(41)
     return result
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,25 +125,25 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
-        result.append(68)
-        result.append(73)
-        result.append(83)
-        result.append(84)
-        result.append(73)
-        result.append(78)
-        result.append(67)
-        result.append(84)
-        result.append(32)
+        mods = [68, 73, 83, 84, 73, 78, 67, 84, 32]  # type: List[int]
+        Assert(ToSeq(mods) == kw_distinct() + PSeq(sep()))
+        i = 0
+        while i < len(mods):
+            # invariants-start
+            Invariant(Acc(list_pred(function), 1 / 2))
+            Invariant(Acc(list_pred(mods)))
+            Invariant(Acc(list_pred(result)))
+            Invariant(ToSeq(mods) == kw_distinct() + PSeq(sep()))
+            Invariant(0 <= i and i <= len(mods))
+            Invariant(ToSeq(result)
+                      == ToSeq(function) + open_paren() + ToSeq(mods).take(i))
+            Invariant(MustTerminate(len(mods) - i + 1))
+            # invariants-end
+            result.append(mods[i])
+            i = i + 1
         Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
     k = 0
     while k < len(operands):
         # invariants-start
@@ -158,8 +157,6 @@
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
     return result
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -140,11 +135,7 @@
         result.append(78)
         result.append(67)
         result.append(84)
-        result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
+    result.append(32)
     k = 0
     while k < len(operands):
         # invariants-start
@@ -153,13 +144,12 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(operands))
         Invariant(ToSeq(result)
-                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
+                  == ToSeq(function) + open_paren() + (kw_distinct() if distinct else PSeq(0).take(0))
+                     + PSeq(sep()) + ToSeq(operands).take(k))
         Invariant(MustTerminate(len(operands) - k + 1))
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
     return result
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -141,10 +136,6 @@
         result.append(67)
         result.append(84)
         result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
     k = 0
     while k < len(operands):
         # invariants-start
@@ -158,8 +149,7 @@
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
+    function.append(41)
     return result
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # NAME
     j = 0
     while j < len(function):
         # invariants-start
@@ -126,11 +125,7 @@
         # invariants-end
         result.append(function[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(function))
-    # opening delimiter
     result.append(40)
-    Assert(ToSeq(result) == ToSeq(function) + open_paren())
-    # modifier
     if distinct:
         result.append(68)
         result.append(73)
@@ -140,11 +135,8 @@
         result.append(78)
         result.append(67)
         result.append(84)
-        result.append(32)
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
-    else:
-        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
-    # operands
+        if len(function) > 0:
+            result.append(32)
     k = 0
     while k < len(operands):
         # invariants-start
@@ -153,13 +145,13 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(operands))
         Invariant(ToSeq(result)
-                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
+                  == ToSeq(function) + open_paren()
+                     + (kw_distinct() if distinct else PSeq(0).take(0))
+                     + (PSeq(sep()) if distinct and len(function) > 0 else PSeq(0).take(0)) + ToSeq(operands).take(k))
         Invariant(MustTerminate(len(operands) - k + 1))
         # invariants-end
         result.append(operands[k])
         k = k + 1
-    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
-    # closing delimiter
     result.append(41)
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-10880.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A set-reducing query function renders to a SQL fragment of the shape

      NAME(<modifier><operands>)

  where NAME is the function keyword, <operands> is the rendered argument text,
  and <modifier> is an optional leading keyword that selects the
  duplicate-eliminating mode. When that mode is requested the modifier keyword
  must be SEPARATED from the operand text by a delimiter, so the keyword token
  does not fuse with the first operand token (which would make the fragment a
  single unintended identifier). When the mode is NOT requested the modifier is
  empty and the operands follow the opening delimiter directly.

  Concretely: with the duplicate-eliminating mode on, the rendered fragment is

      NAME + "(" + KEYWORD + SEP + operands + ")"

  i.e. the keyword DISTINCT is immediately followed by a single space before the
  operands; the code point that directly follows the keyword inside the rendered
  fragment is the separator, never the first operand code point.

Strings are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
fragment assembly (a template substitution) is the changed operation and is
modelled DEEPLY as the spelled-out concatenation; there is no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No consumed axioms: the assembled fragment is modelled deeply as a
#  concatenation of expressible pieces.)
# axioms-end

# pure-start
@Pure
def kw_distinct() -> PSeq[int]:
    """The duplicate-eliminating modifier keyword 'DISTINCT' as code points."""
    # D, I, S, T, I, N, C, T
    return PSeq(68, 73, 83, 84, 73, 78, 67, 84)

@Pure
def sep() -> int:
    """The delimiter code point between a modifier keyword and the operands
    (a single space, U+0020)."""
    return 32

@Pure
def open_paren() -> PSeq[int]:
    return PSeq(40)   # '('

@Pure
def close_paren() -> PSeq[int]:
    return PSeq(41)   # ')'

@Pure
def modifier(distinct: bool) -> PSeq[int]:
    """The leading modifier piece placed directly after the opening delimiter:
    when the duplicate-eliminating mode is requested it is the keyword followed
    by the separator; otherwise it is empty."""
    if distinct:
        return kw_distinct() + PSeq(sep())
    return PSeq(0).take(0)

@Pure
def fragment(function: PSeq[int], operands: PSeq[int], distinct: bool) -> PSeq[int]:
    """The whole rendered SQL fragment: NAME ( <modifier> <operands> )."""
    return function + open_paren() + modifier(distinct) + operands + close_paren()
# pure-end

def render_fragment(function: List[int], operands: List[int], distinct: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(function), 1 / 2))
    Requires(Acc(list_pred(operands), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(function), 1 / 2))
    Ensures(Acc(list_pred(operands), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered fragment is the deep template substitution.
    Ensures(ToSeq(Result()) == fragment(ToSeq(function), ToSeq(operands), distinct))
    # Structural separation guarantee: when the duplicate-eliminating mode is
    # requested, the keyword DISTINCT is present right after the opening
    # delimiter and the code point that immediately follows the keyword inside
    # the fragment is the separator (a space) — so the keyword token never
    # fuses with the first operand code point.
    Ensures(Implies(
        distinct,
        ToSeq(Result()).take(len(function) + 1 + len(kw_distinct())).drop(len(function) + 1)
        == kw_distinct()))
    Ensures(Implies(
        distinct,
        ToSeq(Result())[len(function) + 1 + len(kw_distinct())] == sep()))
    # Without the mode, the operands follow the opening delimiter directly (no
    # modifier is inserted).
    Ensures(Implies(
        not distinct,
        ToSeq(Result()) == ToSeq(function) + open_paren() + ToSeq(operands) + close_paren()))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # NAME
    j = 0
    while j < len(function):
        # invariants-start
        Invariant(Acc(list_pred(function), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(function))
        Invariant(ToSeq(result) == ToSeq(function).take(j))
        Invariant(MustTerminate(len(function) - j + 1))
        # invariants-end
        result.append(function[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(function))
    # opening delimiter
    result.append(40)
    Assert(ToSeq(result) == ToSeq(function) + open_paren())
    # modifier
    if distinct:
        result.append(68)
        result.append(73)
        result.append(83)
        result.append(84)
        result.append(73)
        result.append(78)
        result.append(67)
        result.append(84)
        result.append(32)
        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
    else:
        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
    # operands
    k = 0
    while k < len(operands):
        # invariants-start
        Invariant(Acc(list_pred(function), 1 / 2))
        Invariant(Acc(list_pred(operands), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(operands))
        Invariant(ToSeq(result)
                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
        Invariant(MustTerminate(len(operands) - k + 1))
        # invariants-end
        result.append(operands[k])
        k = k + 1
    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
    # closing delimiter
    result.append(41)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-10880/nagini. 13 attacks + positive control, all confirmed byte-identical spec via `python -m swebench_unified.adversary same-spec nagini django__django-10880 <f>` (all SAME). Attacks were built by a script (build.py) that splices ONLY the text between `# impl-start`/`# impl-end`, so axioms/@Pure/Requires/Ensures are byte-identical by construction.

### RESULTS (exit 2 = spec REJECTED the impl = good; exit 0 = CANDIDATE):
- atk_1  PREPATCH BUG re-encoding (separator never appended; = base_commit 'DISTINCT'): exit 2, NOT-A-COUNTEREXAMPLE. prepatch_reproduced=true. This also independently re-derives G-DIFF.
- atk_2  PARTIAL DOMAIN (separator only when len(operands)>0; correct on every non-empty operand text, wrong on the empty-operand boundary): exit 2. Direct verify shows the exact reason: `Postcondition of render_fragment might not hold. Assertion (ToSeq(Result()) == fragment(...)) might not hold.` -- a genuine spec rejection, not a parse/type error.
- atk_3  BOUNDARY/placement (separator emitted BEFORE the keyword -> NAME( DISTINCTOPERANDS)): exit 2.
- atk_4  CONTROL-FLOW EFFECT (output correct but impl mutates `operands` via append): exit 2, reason `The precondition of method append might not hold. There might be insufficient permission.` -- the frozen 1/2-permission precondition genuinely forbids the side effect.
- atk_5  UNGROUNDED-ORACLE ECHO (correct, but reads the discriminating value out of the spec via `result.append(sep())` instead of a literal): exit 0 CANDIDATE -> patch materialized + RESOLVED (see below).
- atk_6  WRONG SEPARATOR CODE POINT (tab 9 instead of U+0020): exit 2.
- atk_7  DIVERGENCE/VACUITY (skips space code points -> infinite loop on the real F2P operand text 'CASE WHEN pages > 300 THEN rating END'; MustTerminate invariant deliberately omitted): exit 2, reason `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` -- the method-level MustTerminate(2) does bite, so a hanging refinement cannot verify.
- atk_8  DOUBLE SEPARATOR (both explicit separation postconditions still hold verbatim; only the fragment equality can reject it): exit 2 -- confirms the equality clause does real work and the spec does not lean on the structural clauses alone.
- atk_9  SEPARATOR IN THE WRONG SLOT (space before the closing paren instead of after the keyword): exit 2.
- atk_10 SECOND CORRECT IMPL, structurally different (modifier copied out of a locally built list by a loop): exit 0 CANDIDATE -> patch materialized + RESOLVED (see below).
- atk_11 SPURIOUS SEPARATOR IN NON-DISTINCT MODE (the tempting 'just always add a space' fix -> NAME( OPERANDS)): exit 2.
- atk_12 CONTROL-FLOW EFFECT on the OTHER input (mutates `function`): exit 2.
- atk_13 PARTIAL DOMAIN on the OTHER boundary (separator dropped only when the function keyword is empty; correct for COUNT/SUM/AVG): exit 2.

MANDATORY RESOLVE RUNS (official harness, swebench_unified.harness.run_resolve via resolve_one.py; each patch first checked with `git apply --check` against a base_commit worktree -- all APPLIES_CLEAN):
- positive_control -> patch_pc.diff (the gold line): resolved=True, completed=True, F2P success=1, P2P success=55/failure=0.
- atk_5  -> patch_atk5.diff  (`extra_context['distinct'] = ('DISTINCT' + chr(32)) if self.distinct else ''`): resolved=True, completed=True, F2P success=1, P2P 55/0.
- atk_10 -> patch_atk10.diff (`extra_context['distinct'] = ''.join(['DISTINCT', ' ']) if self.distinct else ''`): resolved=True, completed=True, F2P success=1, P2P 55/0.
So EVERY verifying same-spec impl's faithful patch RESOLVES. No verify=>correct break. (Both candidates are provably behaviour-identical to gold: chr(32) and ''.join(['DISTINCT',' ']) both evaluate to the string 'DISTINCT ', confirmed by direct render comparison.)

### ORACLE DISCRIMINATION CONTROLS (proves a non-resolve is detectable here, so the three RESOLVEs above are not a dead oracle):
- patch_atk1.diff (prepatch value 'DISTINCT'): resolved=False, completed=True, 'did not resolve in 3 attempts (consistent -- not flaky)'.
- patch_atk9.diff (template '...%(expressions)s)', space in the wrong slot): resolved=False, completed=True, consistent.
- patch_atk11.diff (template '...%(distinct)s %(expressions)s', spurious space in non-distinct mode): resolved=False, completed=True, consistent.
The spec and the oracle AGREE on all six directions tested: everything the spec rejected that I refined also fails to resolve, and everything the spec admitted resolves. No over-strength and no under-strength observed.

A-LEG AUDIT (refinement.md), the focus of this role:
- Leg kinds: A1=R (str <-> List[int] code points), A2=I (bool carrier), A3=A-reference (modifier == the changed line's value), A4=A-reference (fragment == `template % data`), A5=I (literal parens). Every leg is R / A-reference / I. There is NO kind-3 (unexpressible-changed-op) step and NO A-consumed leg -- consistent with an EMPTY axioms region, which I verified directly: the axioms region text is only two comment lines, and meta.json `axioms` == [] with `additional_change_sites` == []. Nothing is assumed out of band except the two A-references.
- A3/A4 correspondence to the real callees CHECKED against the repo at base_commit 838e432e3e5519c5383d12018e6c78f8ec7833c1: `git show` confirms aggregates.py:17 `template = '%(function)s(%(distinct)s%(expressions)s)'`, aggregates.py:71 `extra_context['distinct'] = 'DISTINCT' if self.distinct else ''` (the pre-patch value), and expressions.py `Func.as_sql` ending `return template % data, params`. Line/quote citations in refinement.md and mapping.md are accurate.
- I independently re-ran the A-reference validation adversarially rather than trusting axiom_check.py: 882 payload pairs (21x21x2 modes) including format-specifier injection ('%(function)s', '%(distinct)s', '%(expressions)s', '%s', '%d', '%%', bare '%', '%(x)s'), the whole template as a payload, literal parens, backslash, braces, NUL \x00, max code point \U0010FFFF, tab/newline, and the keyword 'DISTINCT' itself as an operand: 0 divergences between `fragment` and the real `template % data`. The A-reference is sound on exactly the domain the spec quantifies over.
- Bundle's own checks re-run green: axiom_check.py exit 0 (56 boundary + 20000 fuzz, both modes); conformance_check.py exit 0 (100112 inputs, 0 disagreements).
- Model<->patch correspondence: region_hashes recomputed from model.py match meta.json byte-for-byte (impl 13333cbf..., post-conditions 7088e939..., spec_view e1357561...), so the audited text is the frozen text.
- Modeling-boundary check on the A-legs: I confirmed the changed value has exactly ONE consumer in the modeled path. `git grep` at base_commit shows the only 'DISTINCT' literal in django/db/models is aggregates.py:71, and the only other `%(distinct)s` templates are django/contrib/postgres/aggregates/general.py:13,54 -- those are separate class templates NOT touched by the patch and not in changed_files, and they consume the same value the same way (leading modifier immediately before the expressions), so the trailing-space fix is correct for them too. The filter branch of Aggregate.as_sql reuses the same extra_context['distinct'] through filter_template, i.e. the same substitution, so pinning the value-into-template render does capture the full changed behaviour. No unmodeled consumer of the changed value exists.

**CONCLUSION:** 13 distinct wrong/varied impls run (>= 5 required), covering prepatch re-encoding, two partial-domain shapes, two boundary/placement shapes, wrong separator code point, double separator, spurious separator in the off mode, two control-flow-effect shapes, a divergence/vacuity probe, and an ungrounded-oracle echo. Eight genuinely-wrong impls were all REJECTED by the frozen spec with attributable verifier reasons (postcondition equality, insufficient permission, obligation leak). The three impls that verified are behaviour-preserving and all three faithful patches RESOLVED under the official harness. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_10.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec, Nagini-VERIFYING implementation was found whose faithful refined patch fails to resolve. The only three same-spec files that verified (positive_control, atk_5, atk_10) are all behaviour-preserving re-encodings of the gold render, and all three materialized faithful patches RESOLVED under the official harness (F2P test_count_distinct_expression success=1, P2P success=55, failure=0 on each). verify => correct holds on every probe run.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-10880.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A set-reducing query function renders to a SQL fragment of the shape

      NAME(<modifier><operands>)

  where NAME is the function keyword, <operands> is the rendered argument text,
  and <modifier> is an optional leading keyword that selects the
  duplicate-eliminating mode. When that mode is requested the modifier keyword
  must be SEPARATED from the operand text by a delimiter, so the keyword token
  does not fuse with the first operand token (which would make the fragment a
  single unintended identifier). When the mode is NOT requested the modifier is
  empty and the operands follow the opening delimiter directly.

  Concretely: with the duplicate-eliminating mode on, the rendered fragment is

      NAME + "(" + KEYWORD + SEP + operands + ")"

  i.e. the keyword DISTINCT is immediately followed by a single space before the
  operands; the code point that directly follows the keyword inside the rendered
  fragment is the separator, never the first operand code point.

Strings are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
fragment assembly (a template substitution) is the changed operation and is
modelled DEEPLY as the spelled-out concatenation; there is no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No consumed axioms: the assembled fragment is modelled deeply as a
#  concatenation of expressible pieces.)
# axioms-end

# pure-start
@Pure
def kw_distinct() -> PSeq[int]:
    """The duplicate-eliminating modifier keyword 'DISTINCT' as code points."""
    # D, I, S, T, I, N, C, T
    return PSeq(68, 73, 83, 84, 73, 78, 67, 84)

@Pure
def sep() -> int:
    """The delimiter code point between a modifier keyword and the operands
    (a single space, U+0020)."""
    return 32

@Pure
def open_paren() -> PSeq[int]:
    return PSeq(40)   # '('

@Pure
def close_paren() -> PSeq[int]:
    return PSeq(41)   # ')'

@Pure
def modifier(distinct: bool) -> PSeq[int]:
    """The leading modifier piece placed directly after the opening delimiter:
    when the duplicate-eliminating mode is requested it is the keyword followed
    by the separator; otherwise it is empty."""
    if distinct:
        return kw_distinct() + PSeq(sep())
    return PSeq(0).take(0)

@Pure
def fragment(function: PSeq[int], operands: PSeq[int], distinct: bool) -> PSeq[int]:
    """The whole rendered SQL fragment: NAME ( <modifier> <operands> )."""
    return function + open_paren() + modifier(distinct) + operands + close_paren()
# pure-end

def render_fragment(function: List[int], operands: List[int], distinct: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(function), 1 / 2))
    Requires(Acc(list_pred(operands), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(function), 1 / 2))
    Ensures(Acc(list_pred(operands), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered fragment is the deep template substitution.
    Ensures(ToSeq(Result()) == fragment(ToSeq(function), ToSeq(operands), distinct))
    # Structural separation guarantee: when the duplicate-eliminating mode is
    # requested, the keyword DISTINCT is present right after the opening
    # delimiter and the code point that immediately follows the keyword inside
    # the fragment is the separator (a space) — so the keyword token never
    # fuses with the first operand code point.
    Ensures(Implies(
        distinct,
        ToSeq(Result()).take(len(function) + 1 + len(kw_distinct())).drop(len(function) + 1)
        == kw_distinct()))
    Ensures(Implies(
        distinct,
        ToSeq(Result())[len(function) + 1 + len(kw_distinct())] == sep()))
    # Without the mode, the operands follow the opening delimiter directly (no
    # modifier is inserted).
    Ensures(Implies(
        not distinct,
        ToSeq(Result()) == ToSeq(function) + open_paren() + ToSeq(operands) + close_paren()))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # NAME
    j = 0
    while j < len(function):
        # invariants-start
        Invariant(Acc(list_pred(function), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(function))
        Invariant(ToSeq(result) == ToSeq(function).take(j))
        Invariant(MustTerminate(len(function) - j + 1))
        # invariants-end
        result.append(function[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(function))
    # opening delimiter
    result.append(40)
    Assert(ToSeq(result) == ToSeq(function) + open_paren())
    # modifier
    if distinct:
        result.append(68)
        result.append(73)
        result.append(83)
        result.append(84)
        result.append(73)
        result.append(78)
        result.append(67)
        result.append(84)
        result.append(32)
        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(True))
    else:
        Assert(ToSeq(result) == ToSeq(function) + open_paren() + modifier(False))
    # operands
    k = 0
    while k < len(operands):
        # invariants-start
        Invariant(Acc(list_pred(function), 1 / 2))
        Invariant(Acc(list_pred(operands), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(operands))
        Invariant(ToSeq(result)
                  == ToSeq(function) + open_paren() + modifier(distinct) + ToSeq(operands).take(k))
        Invariant(MustTerminate(len(operands) - k + 1))
        # invariants-end
        result.append(operands[k])
        k = k + 1
    Assert(ToSeq(operands).take(len(operands)) == ToSeq(operands))
    # closing delimiter
    result.append(41)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-10880/nagini. 13 attacks + positive control, all confirmed byte-identical spec via `python -m swebench_unified.adversary same-spec nagini django__django-10880 <f>` (all SAME). Attacks were built by a script (build.py) that splices ONLY the text between `# impl-start`/`# impl-end`, so axioms/@Pure/Requires/Ensures are byte-identical by construction.

### RESULTS (exit 2 = spec REJECTED the impl = good; exit 0 = CANDIDATE):
- atk_1  PREPATCH BUG re-encoding (separator never appended; = base_commit 'DISTINCT'): exit 2, NOT-A-COUNTEREXAMPLE. prepatch_reproduced=true. This also independently re-derives G-DIFF.
- atk_2  PARTIAL DOMAIN (separator only when len(operands)>0; correct on every non-empty operand text, wrong on the empty-operand boundary): exit 2. Direct verify shows the exact reason: `Postcondition of render_fragment might not hold. Assertion (ToSeq(Result()) == fragment(...)) might not hold.` -- a genuine spec rejection, not a parse/type error.
- atk_3  BOUNDARY/placement (separator emitted BEFORE the keyword -> NAME( DISTINCTOPERANDS)): exit 2.
- atk_4  CONTROL-FLOW EFFECT (output correct but impl mutates `operands` via append): exit 2, reason `The precondition of method append might not hold. There might be insufficient permission.` -- the frozen 1/2-permission precondition genuinely forbids the side effect.
- atk_5  UNGROUNDED-ORACLE ECHO (correct, but reads the discriminating value out of the spec via `result.append(sep())` instead of a literal): exit 0 CANDIDATE -> patch materialized + RESOLVED (see below).
- atk_6  WRONG SEPARATOR CODE POINT (tab 9 instead of U+0020): exit 2.
- atk_7  DIVERGENCE/VACUITY (skips space code points -> infinite loop on the real F2P operand text 'CASE WHEN pages > 300 THEN rating END'; MustTerminate invariant deliberately omitted): exit 2, reason `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` -- the method-level MustTerminate(2) does bite, so a hanging refinement cannot verify.
- atk_8  DOUBLE SEPARATOR (both explicit separation postconditions still hold verbatim; only the fragment equality can reject it): exit 2 -- confirms the equality clause does real work and the spec does not lean on the structural clauses alone.
- atk_9  SEPARATOR IN THE WRONG SLOT (space before the closing paren instead of after the keyword): exit 2.
- atk_10 SECOND CORRECT IMPL, structurally different (modifier copied out of a locally built list by a loop): exit 0 CANDIDATE -> patch materialized + RESOLVED (see below).
- atk_11 SPURIOUS SEPARATOR IN NON-DISTINCT MODE (the tempting 'just always add a space' fix -> NAME( OPERANDS)): exit 2.
- atk_12 CONTROL-FLOW EFFECT on the OTHER input (mutates `function`): exit 2.
- atk_13 PARTIAL DOMAIN on the OTHER boundary (separator dropped only when the function keyword is empty; correct for COUNT/SUM/AVG): exit 2.

MANDATORY RESOLVE RUNS (official harness, swebench_unified.harness.run_resolve via resolve_one.py; each patch first checked with `git apply --check` against a base_commit worktree -- all APPLIES_CLEAN):
- positive_control -> patch_pc.diff (the gold line): resolved=True, completed=True, F2P success=1, P2P success=55/failure=0.
- atk_5  -> patch_atk5.diff  (`extra_context['distinct'] = ('DISTINCT' + chr(32)) if self.distinct else ''`): resolved=True, completed=True, F2P success=1, P2P 55/0.
- atk_10 -> patch_atk10.diff (`extra_context['distinct'] = ''.join(['DISTINCT', ' ']) if self.distinct else ''`): resolved=True, completed=True, F2P success=1, P2P 55/0.
So EVERY verifying same-spec impl's faithful patch RESOLVES. No verify=>correct break. (Both candidates are provably behaviour-identical to gold: chr(32) and ''.join(['DISTINCT',' ']) both evaluate to the string 'DISTINCT ', confirmed by direct render comparison.)

### ORACLE DISCRIMINATION CONTROLS (proves a non-resolve is detectable here, so the three RESOLVEs above are not a dead oracle):
- patch_atk1.diff (prepatch value 'DISTINCT'): resolved=False, completed=True, 'did not resolve in 3 attempts (consistent -- not flaky)'.
- patch_atk9.diff (template '...%(expressions)s)', space in the wrong slot): resolved=False, completed=True, consistent.
- patch_atk11.diff (template '...%(distinct)s %(expressions)s', spurious space in non-distinct mode): resolved=False, completed=True, consistent.
The spec and the oracle AGREE on all six directions tested: everything the spec rejected that I refined also fails to resolve, and everything the spec admitted resolves. No over-strength and no under-strength observed.

A-LEG AUDIT (refinement.md), the focus of this role:
- Leg kinds: A1=R (str <-> List[int] code points), A2=I (bool carrier), A3=A-reference (modifier == the changed line's value), A4=A-reference (fragment == `template % data`), A5=I (literal parens). Every leg is R / A-reference / I. There is NO kind-3 (unexpressible-changed-op) step and NO A-consumed leg -- consistent with an EMPTY axioms region, which I verified directly: the axioms region text is only two comment lines, and meta.json `axioms` == [] with `additional_change_sites` == []. Nothing is assumed out of band except the two A-references.
- A3/A4 correspondence to the real callees CHECKED against the repo at base_commit 838e432e3e5519c5383d12018e6c78f8ec7833c1: `git show` confirms aggregates.py:17 `template = '%(function)s(%(distinct)s%(expressions)s)'`, aggregates.py:71 `extra_context['distinct'] = 'DISTINCT' if self.distinct else ''` (the pre-patch value), and expressions.py `Func.as_sql` ending `return template % data, params`. Line/quote citations in refinement.md and mapping.md are accurate.
- I independently re-ran the A-reference validation adversarially rather than trusting axiom_check.py: 882 payload pairs (21x21x2 modes) including format-specifier injection ('%(function)s', '%(distinct)s', '%(expressions)s', '%s', '%d', '%%', bare '%', '%(x)s'), the whole template as a payload, literal parens, backslash, braces, NUL \x00, max code point \U0010FFFF, tab/newline, and the keyword 'DISTINCT' itself as an operand: 0 divergences between `fragment` and the real `template % data`. The A-reference is sound on exactly the domain the spec quantifies over.
- Bundle's own checks re-run green: axiom_check.py exit 0 (56 boundary + 20000 fuzz, both modes); conformance_check.py exit 0 (100112 inputs, 0 disagreements).
- Model<->patch correspondence: region_hashes recomputed from model.py match meta.json byte-for-byte (impl 13333cbf..., post-conditions 7088e939..., spec_view e1357561...), so the audited text is the frozen text.
- Modeling-boundary check on the A-legs: I confirmed the changed value has exactly ONE consumer in the modeled path. `git grep` at base_commit shows the only 'DISTINCT' literal in django/db/models is aggregates.py:71, and the only other `%(distinct)s` templates are django/contrib/postgres/aggregates/general.py:13,54 -- those are separate class templates NOT touched by the patch and not in changed_files, and they consume the same value the same way (leading modifier immediately before the expressions), so the trailing-space fix is correct for them too. The filter branch of Aggregate.as_sql reuses the same extra_context['distinct'] through filter_template, i.e. the same substitution, so pinning the value-into-template render does capture the full changed behaviour. No unmodeled consumer of the changed value exists.

**CONCLUSION:** 13 distinct wrong/varied impls run (>= 5 required), covering prepatch re-encoding, two partial-domain shapes, two boundary/placement shapes, wrong separator code point, double separator, spurious separator in the off mode, two control-flow-effect shapes, a divergence/vacuity probe, and an ungrounded-oracle echo. Eight genuinely-wrong impls were all REJECTED by the frozen spec with attributable verifier reasons (postcondition equality, insufficient permission, obligation leak). The three impls that verified are behaviour-preserving and all three faithful patches RESOLVED under the official harness. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Reference = base_commit worktree () with the gold patch APPLIED (, verified aggregates.py:71 reads "extra_context['distinct'] = 'DISTINCT ' if self.distinct else ''"). Base commit 838e432e3e5519c5383d12018e6c78f8ec7833c1 confirmed; Aggregate.template at aggregates.py:17 is verbatim '%(function)s(%(distinct)s%(expressions)s)' and Func.as_sql (expressions.py:621-622) is 'return template % data, params'.

**What the spec claims:** fragment(function,operands,distinct) = function + '(' + modifier(distinct) + operands + ')' with modifier(True)=DISTINCT(68,73,83,84,73,78,67,84)+space(32), modifier(False)=empty; plus two separation postconditions (keyword slice at [len(function)+1.. +8] == 'DISTINCT' and the code point at len(function)+1+8 == 32) and a no-modifier postcondition for distinct=False.

Evidence gathered (all against the REAL patched Django, imported from the worktree, not a re-implementation):
1. Positive control: bash scripts/nagini_verify.sh on the bundle model.py -> 'Verification successful' (20.1s). same-spec on the unmodified model returns SAME (exit 0), so region hashes/spec markers are intact.
2. axiom_check.py exit 0 (56 boundary + 20000 fuzz, both modes).
3. conformance_check.py run with PYTHONPATH pointed at the PATCHED worktree: 'G-CONF OK: shadow impl == real patched render on 100112 inputs' (112 boundary + 100000 fuzz, seed 10880), 0 disagreements. This drives the real Aggregate.as_sql -> Func.as_sql -> 'template % data' chain via a stub compiler, not a copy of it.
4. My own independent differential probe (atk2_probe.py) against the real patched Aggregate.as_sql: 1012 hand-picked boundary triples + 60000 fuzz triples, 0 divergences. Adversarial payloads specifically chosen to break a naive concatenation model: format-specifier injection in BOTH the function keyword and the operand text ('%s', '%%', '%', '%(function)s', '%(distinct)s', '%(expressions)s', '%(field)s', '%(template)s', '%(arg_joiner)s', '%(filter)s'), literal parens '(' ')' '((', the literal token 'DISTINCT' and 'DISTINCTCASE' as an operand, empty function keyword, empty operands, leading/trailing spaces in operands, NUL \x00, newline/tab, surrogate-adjacent U+D7FF, max code point U+10FFFF, U+1F600, non-ASCII 'ÜNÎ', 1000-char function, 500-char operand. Fuzz alphabet spanned U+0000..U+011F plus '%'/'%s'/'%(distinct)s'/parens/whitespace. No input makes the real render differ from the model: the percent substitution is single-pass, so injected specifiers in the VALUES are never re-expanded, which is exactly what the flat-concatenation deep model assumes.
5. Delta direction sanity-checked (guards against the trap in the brief): the PRE-patch worktree renders 'COUNT(DISTINCTCASE WHEN a THEN b END)' while the patched one renders 'COUNT(DISTINCT CASE WHEN a THEN b END)'. The spec agrees with the PATCHED value, i.e. the space in modifier(True) is the patch delta itself, not drift. I did not score that pre/post difference as a divergence.

Over-strength check (the specific way a faithfulness gate fails): the two separation postconditions are strict logical CONSEQUENCES of the fragment equality (given Result == f + '(' + 'DISTINCT' + ' ' + ops + ')', the slice at offset len(f)+1 is necessarily the keyword and the next code point is necessarily 32), so they add no obligation the real patched repo does not already satisfy — I confirmed both hold on every one of the 61012 real-render observations above, including when the operand text itself starts with a space or with 'DISTINCT'. Indexing is always in bounds under distinct (the fragment has >= len(function)+10 elements). The distinct=False postcondition also matches the real render exactly ('COUNT(rating)').

Modeling-boundary items I examined and judged declared-and-sound, not drift:
- filter branch of Aggregate.as_sql with supports_aggregate_filter_clause=True renders 'COUNT(DISTINCT CASE WHEN a THEN b END) FILTER (WHERE x > 1)' — a wrapping of the same base substitution via filter_template. mapping.md binds render_fragment to the plain Aggregate template, so the equality clause is scoped to that binding; notably the separation guarantee still holds verbatim on the filter render because filter_template only appends a suffix. The changed 'distinct' value flows identically into that branch, so the fix's content is captured.
- django/contrib/postgres/aggregates ArrayAgg/StringAgg override the template with extra %(ordering)s/%(delimiter)s fields; these are distinct render sites, not the modeled function, and they consume the same corrected 'DISTINCT ' value, so the modifier model remains the right abstraction there too.

**Conclusion:** I could not construct any input on which the modeled function disagrees with the real (patched) callee, and the spec adds no obligation beyond what the real code guarantees. Verdict FAITHFUL. All work done in /tmp worktrees; the bundle was not modified (read-only reads plus a copy of model.py to atk2_pos.py for the positive control).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** INDEPENDENT RE-DERIVATION (did not inherit verdict.md's prior 'pass (agent: NO-LEAKAGE)' for role 4; that file is a backfilled record of a prior run, and I treated its disposition as a claim, not a result).

**NO RELAXATION IN PLAY:** there is no RELAXED_LEAKAGE.md in the bundle and no `relaxed_leakage` key in meta.json (meta keys are exactly additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version). So this is judged as an ordinary, non-relaxed leakage review: the spec view must disclose nothing beyond the public problem_statement.

### WHAT I MEASURED:
1. Rendered the actual consumer artifact: markers.spec_view(model.py, get_backend('nagini')) -> sha256 e13575618f883a5c83e4c90b0e31c4a122883bad52def4fbb0161ba6ea54b22e, which is byte-for-byte the `spec_view` hash recorded under G-HYGIENE in meta.json. So the thing I judged IS the frozen spec view (docstring + axioms/pure/pre/post regions; impl region collapsed to `...  # implementation elided`).
2. Ran the mechanical screen: leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> hard_failures=[] and warnings=[]. No diff markers, no gold-patch line reproduced, no patched file/module path.
3. Symbol sweep over the rendered view for repo-specific disclosure: aggregates.py, expressions.py, extra_context, Aggregate, Func, as_sql, self.distinct, '%(function)s', '%(distinct)s', '%(expressions)s', "'DISTINCT '", COUNT, Count, Case, WHEN, patch, diff, bug, fix, 2.2, annotation -- ALL ABSENT. Only 'template' (a generic English word in the prose, not the repo template literal) and '10880' (the instance id, which the solver already has) appear. Full identifier list of the view contains no Django symbol.

DISCLOSURE COMPARISON vs the PUBLIC problem_statement (I used the frozen dataset row from data/swe_bench_verified/test.jsonl, NOT hints_text): the public statement is 'Query syntax error with condition and distinct combination... A Count annotation containing both a Case condition and a distinct=True param produces a query error on Django 2.2 (whatever the db backend). A space is missing at least (... COUNT(DISTINCTCASE WHEN...).' That public text already discloses, on its own: the DISTINCT keyword; that it sits directly after the function's opening paren; that the operand text follows it; that the two FUSE ('DISTINCTCASE'); and the diagnosis verbatim -- 'A space is missing'.

The spec view's strongest lines -- the docstring 'the keyword DISTINCT is immediately followed by a single space before the operands', kw_distinct()/sep()=32, modifier(True)=kw_distinct()+PSeq(sep()), and the postconditions ToSeq(Result()).take(len(function)+1+len(kw_distinct())).drop(len(function)+1)==kw_distinct() and ToSeq(Result())[len(function)+1+len(kw_distinct())]==sep() -- state exactly that same fact and nothing more. The gold edit is 'DISTINCT' -> 'DISTINCT ' (add trailing space); a solver reading only the public statement can already derive it. The spec view adds NO new discriminator: not the file, not the function, not the printf template, not the fact that the carrier is a dict entry, not the one-line shape of the hunk. It withholds strictly more than the public statement does about WHERE to change anything.

LOAD-BEARING CHECK (ran the pinned verifier myself, not read off meta): `bash scripts/nagini_verify.sh model.py` -> 'Verification successful' (exit 0, 21.3s), and `bash scripts/nagini_verify.sh model_prepatch.py` -> 'Verification failed', exit 1, with the error localized to the operands-loop invariant at model_prepatch.py:153: 'Loop invariant might not hold on entry. Assertion (ToSeq(result) == (((ToSeq(function) + open_paren()) + modifier(distinct)) + ToSeq(operands).take(k))) might not hold.' So the separator content is genuinely sensed by the spec (G-DIFF sound, reproduced live), i.e. the DISTINCT/space narration is discriminating spec content rather than decorative prose -- and since the public statement already names that same discriminator, naming it here costs nothing.

**NO FILE ADDRESSES THE REVIEWER:** grep for panel/auditor/reviewer/'you should'/'do not report'/'record.* verdict'/NO-LEAKAGE/honest over model.py, refinement.md, mapping.md returned nothing. verdict.md does carry prior per-role dispositions (including role 4 = NO-LEAKAGE) but it is a generated record ('generated by scripts/backfill_verdict_md.py') and does not instruct me how to record; I re-derived independently regardless. refinement.md and mapping.md DO contain the verbatim gold hunk and the exact post-patch string 'DISTINCT ', but those are audit artifacts outside the projected spec view (eval_mode_1/eval_mode_2 hand the solver the spec/contract, and markers.spec_view is what the leakage screen and same_spec pin), so they are out of scope for this gate -- and even if read, they disclose only the same missing-space fact the public statement states.

INCIDENTAL BOOKKEEPING NOTE (not a leakage finding, does not change the verdict): meta.json['patch_diff'] is not the verbatim gold diff -- it is the placeholder string 'gold patch verbatim (applies cleanly at base_commit; single-line modifier value change)'. meta base_commit does match the dataset (838e432e3e5519c5383d12018e6c78f8ec7833c1), and refinement.md quotes the correct hunk, so the gold edit under audit is not in doubt; but the bundle also ships no patch.diff file despite the task prompt listing one. Worth a hygiene look by whoever owns meta serialization.

**CONCLUSION:** the spec view's entire disclosure about the gold edit is co-extensive with the public problem_statement's own 'a space is missing after DISTINCT' diagnosis, and it names no repo location or symbol. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
