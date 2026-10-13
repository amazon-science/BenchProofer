# P2 adversarial audit — sphinx-doc__sphinx-11510

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_18.py`, `atk_19.py`, `atk_20.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no attack was a CANDIDATE. All 19 same-spec wrong implementations were REJECTED by the frozen spec (adversary weakness exit 2 in every case), so there is no verifying wrong impl whose faithful patch could fail to resolve, and no attack patch was materializable.

The model.py under audit (sha256 92d07730344a5121d53737fbe16452b179d65bb25eb891790934854634aa17dd) is a REPAIRED spec: it now carries an IO/effect discipline absent from the version a prior G-EQ pass recorded as BROKEN. `hook_offer_io(t_pre, region, t_post)` is an @IOOperation parameterised by the offered region; the step arrives with token(t_pre, 3) plus a licence naming exactly ONE offer of ToSeq(lines).take(len-2), emit_and_collect spends licence+token, and Ensures(token(t_post)) forces the offer to have happened. I re-encoded the prior breaker class directly and it is now dead:

  atk_3  (== prior BREAKER atk_12: extra offer of the WHOLE gathered sequence, framing markers included, fresh copy, yield discarded, forwarded value bit-identical to gold)
    -> atk_3.py:177: The precondition of method emit_and_collect might not hold. There might be insufficient permission to access hook_offer_io(t_pre, ToSeq(body), t_post).
  atk_4  (== prior atk_13: extra offer of just the two framing markers) -> same insufficient-permission rejection.
  atk_13 (SHARPEST, my own escalation: extra offer of a FRESH, VALUE-EQUAL copy of exactly the LICENSED body region, yield discarded, value bit-identical to gold — the case a value-only contract and a region-keyed-but-non-linear licence would both miss) -> also rejected, insufficient permission hook_offer_io.

That last one is the decisive evidence: hook_offer_io behaves as a LINEAR resource, so a second offer of the very same region value has no licence to spend. The prior pass's whole defect class (dispatch invisible to a pure value contract) is closed, and closed at the mechanism level, not by accident.
```

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,7 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
-    markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
-    new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    ignored = emit_and_collect(t_pre, body)
+    return lines[:n]
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,6 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
-    body = lines[:n - 2]
-    markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
-    new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    Assert(False)
+    return lines[:n]
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,11 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
     result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
+    whole = lines[:n]
+    ignored = emit_and_collect(t_pre, whole)
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,11 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
     result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
+    extra = lines[n - 2:]
+    ignored = emit_and_collect(t_pre, extra)
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,9 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
-    new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    first = emit_and_collect(t_pre, body)
+    second = emit_and_collect(t_pre, body)
+    return second + markers
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,9 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
+    pre = emit_and_collect(t_pre, markers)
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    return new_body + markers
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,8 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
-    body = lines[:n - 2]
-    markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
+    body = lines[:n - 1]
+    markers = lines[n - 1:]
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    return new_body + markers
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,11 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
     result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
+    if n == 2:
+        return lines[:n]
     return result
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,10 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
-    new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    if n > 3:
+        new_body = emit_and_collect(t_pre, body)
+        return new_body + markers
+    return lines[:n]
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,12 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
     result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
+    i = 0
+    while i >= 0:
+        i = i + 1
     return result
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,8 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    return markers + new_body
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,9 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    twice = emit_and_collect(t_pre, new_body)
+    return twice + markers
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,11 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
     result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
+    again = lines[:n - 2]
+    ignored = emit_and_collect(t_pre, again)
     return result
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,18 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
-    body = lines[:n - 2]
-    markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
-    new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    goal = transformed(ToSeq(lines))
+    res = []  # type: List[int]
+    i = 0
+    while i < len(goal):
+        Invariant(Acc(list_pred(res)))
+        Invariant(Acc(list_pred(lines), 1 / 2))
+        Invariant(0 <= i and i <= len(goal))
+        Invariant(goal == transformed(ToSeq(lines)))
+        Invariant(ToSeq(res) == goal.take(i))
+        Invariant(MustTerminate(len(goal) - i))
+        res.append(goal[i])
+        i = i + 1
+    Assert(ToSeq(res) == goal)
+    return res
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,19 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
-    markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
-    new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    ignored = emit_and_collect(t_pre, body)
+    goal = transformed(ToSeq(lines))
+    res = []  # type: List[int]
+    i = 0
+    while i < len(goal):
+        Invariant(Acc(list_pred(res)))
+        Invariant(Acc(list_pred(lines), 1 / 2))
+        Invariant(0 <= i and i <= len(goal))
+        Invariant(goal == transformed(ToSeq(lines)))
+        Invariant(ToSeq(res) == goal.take(i))
+        Invariant(MustTerminate(len(goal) - i))
+        res.append(goal[i])
+        i = i + 1
+    return res
     # impl-end
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,7 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
-    body = lines[:n - 2]
-    markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
-    new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    copy = lines[:n]
+    inner = forward_with_source_read(t_pre, copy)
+    return inner
     # impl-end
```

Attack 17 — `atk_18.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,7 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
-    markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    return new_body
     # impl-end
```

Attack 18 — `atk_19.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,8 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
     body = lines[:n - 2]
     markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
     new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    return new_body + markers + markers
     # impl-end
```

Attack 19 — `atk_20.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,19 +169,8 @@
     )
     # impl-start
     n = len(lines)
-    # Split off the authored body (all but the final two framing markers) and
-    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
-    body = lines[:n - 2]
-    markers = lines[n - 2:]
-    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
-    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
-    # Offer the body to the content-transformation hook, spending the step's one
-    # licence; its (possibly rewritten) result replaces the body region.
-    new_body = emit_and_collect(t_pre, body)
-    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
-    # Re-attach the framing markers, in their original positions, after the
-    # transformed body, and forward the result.
-    result = new_body + markers
-    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
-    return result
+    short = lines[:n - 3]
+    rest = lines[n - 3:]
+    new_short = emit_and_collect(t_pre, short)
+    return new_short + rest
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-11510.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When textual content that has been gathered for inclusion into a document is
  handed on to the parser, that content first passes through the document-set's
  content-transformation hook, so that any registered transformer observes and
  may rewrite it before it is parsed -- exactly as the content of a primary
  document does.

  The gathered content arrives as a sequence of lines whose final two entries
  are internal book-keeping markers that frame the inserted region; they are
  not part of the authored content. The transformation therefore applies to the
  AUTHORED body only -- every line except the final two -- while the two framing
  markers are carried through unchanged and re-attached, in their original
  positions, after the (possibly rewritten) body. The result is the line
  sequence forwarded to the parser.

  Consequently: the forwarded sequence is the transformed body followed by the
  two original framing markers; the two framing markers are preserved verbatim;
  and the body region is precisely what the transformation hook is offered.

  Offering content to the hook is an EFFECT, seen by the registered transformers
  themselves, and it is NOT recoverable from the forwarded sequence: two steps
  can forward one and the same sequence while having shown the transformers
  different content, or having shown them content more than once. Which content
  is offered, and how many times, is therefore part of the behaviour specified
  here and not an implementation's free choice. A forwarding step is licensed
  for exactly ONE offer, of exactly the authored body region, and forwarding is
  conditional on spending that licence: a step that forwards content it never
  offered, or that offers a region other than the authored body, or that offers
  a second time, is not this behaviour -- whatever sequence it hands back.

  That obligation is carried the standard way effects are carried here. An offer
  is an operation (`hook_offer_io`) parameterised by the region it shows; a step
  receives a token at a place together with the licence naming the one offer
  permitted there, an offer spends licence and token and yields the token at the
  place the licence names, and the step must hand a token at that place back to
  its caller. So the offer cannot be skipped (the token is only obtainable by
  making it), cannot show another region (the licence names the region), and
  cannot happen twice (there is one licence and a step cannot mint one).

Lines are modelled as `List[int]` of opaque per-line identities (the content of
a line is a value; the line-text round trip "join the lines, hand to the hook,
split again" is the identity at line granularity for content with no embedded
line breaks, which is the regime the behaviour concerns). The content
transformation hook is an opaque, uninterpreted pure function on the body line
sequence (`hook`): it stands for arbitrary registered transformer code, so the
specification constrains only WHICH region is offered to it, how often, and that
the framing markers bypass it, never what it computes. The specification is
carried over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def hook(body: PSeq[int]) -> PSeq[int]:
    """The document-set content-transformation hook, applied to the authored
    body line sequence. Uninterpreted: it stands for arbitrary registered
    transformer code, so it carries NO Ensures -- the specification pins only
    that it is offered exactly the body region (framing markers excluded) and
    that its result replaces that region, never what it returns. (mapping.md)"""
    Requires(True)

@IOOperation
def hook_offer_io(t_pre: Place, region: PSeq[int], t_post: Place = Result()) -> bool:
    """The observable EFFECT of the forwarding step: the content-transformation
    hook is shown the line sequence `region` -- one offer -- carrying the step
    from place `t_pre` to place `t_post`. It models the offer itself, not what
    the hook computes from it (`hook` above does that): what it pins is that an
    offer HAPPENED and WHICH region it showed. A step holds one instance of this
    operation per offer it is permitted to make and an offer spends one; a step
    cannot mint an instance, so how many offers are made and which region each
    one shows are settled by the step's contract instead of chosen by its
    implementation. An offer terminates."""
    Terminates(True)

@ContractOnly
def emit_and_collect(t_pre: Place, body: List[int]) -> List[int]:
    """Offer the authored body to the content-transformation hook and collect
    the (possibly rewritten) body it yields. Models the unchanged content-
    dispatch machinery together with the line<->text round trip around it: the
    result is `hook` applied to the body. The body is read at a fractional share
    and returned unchanged; the yielded sequence is a fresh list. Offering is an
    effect, so this also spends one licence to show exactly `body` plus the token
    that reaches it, and hands back the token at the place that licence names: it
    is callable only where the caller's own contract licenses an offer of exactly
    that region. (mapping.md)"""
    IOExists1(Place)(
        lambda t_post: (
        Requires(Acc(list_pred(body), 1 / 2)),
        Requires(token(t_pre, 2) and hook_offer_io(t_pre, ToSeq(body), t_post)),
        Requires(MustTerminate(2)),
        Ensures(token(t_post)),
        Ensures(Acc(list_pred(body), 1 / 2)),
        Ensures(Acc(list_pred(Result()))),
        Ensures(ToSeq(Result()) == hook(ToSeq(body))),
        )
    )
# axioms-end

# pure-start
@Pure
def transformed(lines: PSeq[int]) -> PSeq[int]:
    """The line sequence forwarded to the parser: the hook-transformed authored
    body (every line but the final two) followed by the two framing markers,
    re-attached verbatim in their original positions. The two framing markers
    are always present in the gathered content; when fewer than two lines are
    present (never, in the modelled regime) the whole sequence is treated as
    body, keeping the function total so the precondition is trivially met."""
    if len(lines) < 2:
        return hook(lines)
    return hook(lines.take(len(lines) - 2)) + lines.drop(len(lines) - 2)
# pure-end

def forward_with_source_read(t_pre: Place, lines: List[int]) -> List[int]:
    IOExists1(Place)(
        lambda t_post: (
        # pre-conditions-start
        # The gathered line sequence is read-only here (it is consumed to build
        # the forwarded sequence, never mutated in place); fractional permission,
        # required and ensured, so no caller may satisfy a postcondition
        # vacuously by overwriting the input. The final two entries are the
        # framing markers, so at least two lines are present.
        Requires(Acc(list_pred(lines), 1 / 2)),
        Requires(len(lines) >= 2),
        # The step arrives holding a token and a licence for exactly ONE offer,
        # of exactly the authored body region (the gathered lines minus the two
        # framing markers). That is the whole effect budget it is given: no
        # second offer, and no offer of any other region, is available to it.
        Requires(token(t_pre, 3) and
                 hook_offer_io(t_pre, ToSeq(lines).take(len(lines) - 2), t_post)),
        Requires(MustTerminate(3)),
        # pre-conditions-end
        # post-conditions-start
        # The licensed offer has been MADE: the token handed back sits at the
        # place the licence names, which is reachable only by showing the hook
        # exactly the authored body region. So content is never forwarded
        # unoffered, and the offer that happened showed that region and no
        # other.
        Ensures(token(t_post)),
        Ensures(Acc(list_pred(lines), 1 / 2)),
        Ensures(Acc(list_pred(Result()))),
        # The forwarded sequence is the hook-transformed authored body followed
        # by the two original framing markers: the body region is exactly what
        # the hook is offered, and the result replaces that region.
        Ensures(ToSeq(Result()) == transformed(ToSeq(lines))),
        # The two framing markers are preserved verbatim, in their original
        # order and position (the last two lines of the output equal the last
        # two lines of the input).
        Ensures(len(Result()) >= 2),
        Ensures(ToSeq(Result()).drop(len(Result()) - 2) == ToSeq(lines).drop(len(lines) - 2)),
        # The authored body region (everything but the final two output lines)
        # is precisely the region offered to and replaced by the hook.
        Ensures(ToSeq(Result()).take(len(Result()) - 2) == hook(ToSeq(lines).take(len(lines) - 2))),
        # post-conditions-end
        )
    )
    # impl-start
    n = len(lines)
    # Split off the authored body (all but the final two framing markers) and
    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
    body = lines[:n - 2]
    markers = lines[n - 2:]
    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
    # Offer the body to the content-transformation hook, spending the step's one
    # licence; its (possibly rewritten) result replaces the body region.
    new_body = emit_and_collect(t_pre, body)
    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
    # Re-attach the framing markers, in their original positions, after the
    # transformed body, and forward the result.
    result = new_body + markers
    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** 19 distinct same-spec wrong impls, generated by gen.py which copies the bundle model.py and rewrites ONLY the text between # impl-start / # impl-end. All 19 confirmed `adversary same-spec` = SAME, and I additionally checked PROGRAMMATICALLY (via markers.parse_regions) that every file's text OUTSIDE the impl span is byte-identical to the frozen model, head and tail — so axioms/@Pure/Requires/Ensures/docstring are untouched. Verifications were run as concurrent background batches of 3 (each Nagini check spawns JVM+Z3), per instruction; results collected per-attack.

### CONTROLS (all four ran):
- pos_control.py, byte-identical copy: `bash scripts/nagini_verify.sh` -> 'Verification successful', 16.61s, rc=0. Toolchain reaches real verdicts.
- pos_alt.py, BEHAVIOURALLY CORRECT but rewritten (offers a value-equal fresh copy of the body region, appends the two markers one at a time) -> 'Verification successful', 13.54s. So the 19 rejections are the spec discriminating BEHAVIOUR, not pinning the frozen syntax; the spec is not rejecting everything.
- atk_2.py VACUITY CONTROL (`Assert(False)` in the impl): REJECTED, 'Assertion False might not hold'. The token+licence precondition is SATISFIABLE on entry, so the IO discipline is not verifying vacuously through an infeasible precondition. This mattered: an IO/obligation spec is exactly where a guarded self-call or unsatisfiable place assumption can verify while proving nothing.
- prepatch_reproduced: atk_1.py re-encodes model_prepatch.py's bug in the strongest available form — it MAKES the licensed offer (so the token obligation is discharged) but DISCARDS the hook's yield and forwards the gathered lines verbatim. Rejected on Postcondition ToSeq(Result()) == transformed(ToSeq(lines)). G-DIFF holds.

PER-ATTACK (cmd in every case: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-11510 <path>`; all exit 2 = NOT-A-COUNTEREXAMPLE; reason from `bash scripts/nagini_verify.sh <path>`):
  atk_1  prepatch, offer made + yield discarded, verbatim forward -> Postcond transformed
  atk_3  extra offer WHOLE gathered seq (prior breaker)          -> insufficient permission hook_offer_io
  atk_4  extra offer of the two FRAMING MARKERS (prior atk_13)   -> insufficient permission hook_offer_io
  atk_5  body offered TWICE, 2nd yield forwarded                 -> insufficient permission hook_offer_io
  atk_6  markers offered FIRST, then body (last-write-wins mask)  -> insufficient permission hook_offer_io
  atk_7  BOUNDARY split n-1, a marker swallowed into offered body-> insufficient permission hook_offer_io (licence names the exact region)
  atk_8  PARTIAL DOMAIN, verbatim at the n==2 boundary            -> Postcond transformed
  atk_9  CONTROL-FLOW EFFECT, offer only on the n>3 branch        -> insufficient permission token(t_post) (offer cannot be skipped on any path)
  atk_10 DIVERGENCE, correct value but infinite loop              -> 'Obligation leak check failed' (method-level MustTerminate(3) bites)
  atk_11 ORDERING, markers + new_body                            -> Postcond transformed
  atk_12 DOUBLE TRANSFORM hook(hook(body))                       -> insufficient permission hook_offer_io
  atk_13 value bit-identical to gold + extra offer of a FRESH value-equal copy of the LICENSED region -> insufficient permission hook_offer_io  [the decisive linearity result]
  atk_14 UNGROUNDED ORACLE ECHO: result built element-by-element out of the pure `transformed`, no offer at all -> insufficient permission token(t_post)
  atk_15 oracle echo WITH the offer made but its yield discarded  -> Postcond markers-drop equality
  atk_16 LICENCE LAUNDERING via self-call on a value-equal copy   -> precondition token(t_pre, 3) insufficient (a step cannot mint/relend a licence)
  atk_18 markers DROPPED                                         -> Postcond transformed
  atk_19 markers DUPLICATED (present but not in original position)-> Postcond transformed
  atk_20 TRUNCATED offer, a proper SUBSET of the body region      -> insufficient permission hook_offer_io
Note the two rejection families are complementary and both real: value postconditions kill wrong FORWARDED SEQUENCES, the licence/token discipline kills wrong OFFERS (extra, wider, narrower, misordered, skipped, relent). atk_14 in particular shows the result must be PRODUCED BY the dispatch rather than equated to an oracle value (directive 8).

EXCLUDED, NOT COUNTED AS SPEC STRENGTH: atk_17.py (marker rebuild using `del`) returned 'Translation failed — Not supported: Unsupported operator', i.e. a Nagini FRONT-END artifact and NO VERDICT, not a rejection by the spec. I did not submit it and take no strength credit for it; its intent was re-encoded as atk_18 and atk_19, which translate and are genuinely rejected. (Same discipline as retained-attack-label hygiene: an echo/timeout must never be re-judged into the reject lane.)

**RESOLVE RUNS.** No attack was a CANDIDATE, so `patches` is empty and there is no attack patch to run — the BROKEN branch is unreachable here by construction, not by omission. To ensure a SOUND verdict does not rest on an oracle lane I never touched (a silently unavailable Docker oracle would otherwise let 'nothing failed to resolve' mean 'nothing ran'), I ran the gold patch through the OFFICIAL harness: `python resolve.py patch_gold.diff goldctl` -> swebench_unified.harness.run_resolve -> resolved=True, completed=True, FAIL_TO_PASS 2/2 success, PASS_TO_PASS 7/7 success (report saved as resolve_goldctl.json). The resolve lane is live and the base lane intact.

REFINEMENT.MD LEG AUDIT (A legs; R/I mechanically covered by G-CONF). Legs A1(R), A2(R+I), A3(I), A4(A-consumed), A5(R+I), A6(R). No kind-3 leg is DECLARED, and — unlike at the prior pass — the claim now holds: the one genuinely-changed operation (route the body through the hook, splice the result back inside the framing markers) is modeled structurally in `transformed`/`forward_with_source_read`, AND the offer EFFECT that the prior pass found unexpressible is now expressed, by hook_offer_io + the licence/token threading. mapping.md §3.1's stated obligation ('the markers include_lines[-2:] must be passed through untouched — they are never offered to the event') is no longer prose-only: atk_3/atk_4/atk_7/atk_20 show the frozen contract itself now enforces which region is offered.

The single A-consumed axiom emit_and_collect binds to EventManager.emit('source-read', docname, arg) plus the '\n'.join / str.splitlines round trip; G-AX (recorded pass, 8 boundary + 20 000 fuzz line sets against the REAL EventManager and real os_path) exercises marker exclusion, marker reattachment, event-text == join(lines[:-2]), round-trip identity and hook propagation. hook stays an uninterpreted @Pure symbol with no Ensures, so it is not an oracle the result is pinned to. F2P test_include_source_read_event asserts on the OFFERED text and that is now inside the spec's reach — which is precisely the leg that failed before.

DOCUMENTATION DEFECT (advisory, NOT a verify=>correct break; nothing to do with the machine verdict). refinement.md is STALE with respect to the repaired model and under-describes the very machinery that now carries the proof:
- refinement.md (dated Aug 5) has ZERO mentions of hook_offer_io / token / Place / licence, while model.py (Aug 14) has 24. Its A4 leg still writes the callee as `emit_and_collect(body)` and its §A table row for A1 as `lines: List[int]`, but the real signatures are `emit_and_collect(t_pre: Place, body)` and `forward_with_source_read(t_pre: Place, lines)`. The `t_pre`/`t_post` place threading — the entire reason the offer effect is now pinned, and the entire reason this bundle is no longer BROKEN — has NO refinement leg at all, and §D's verify=>resolved argument is still argued purely from the value postconditions.
- meta.json's `axioms` entry likewise documents only the Ensures `ToSeq(Result()) == hook(ToSeq(body))` and never mentions the licence/token conjunct that is doing the discriminating work; `deep_model_references` is empty.
- conformance_check.py §Shadow claims the impl region is copied VERBATIM, but its shadow is `forward_with_source_read(lines)` calling `emit_and_collect(body)` — the pre-repair, place-free signature. The value legs it checks are still sound (the places are ghost/effect state with no value content, so the 101 512-input agreement still transfers), but the 'VERBATIM' wording is now inaccurate and the shadow exercises none of the effect discipline.
Recommend refreshing refinement.md with an explicit A-leg for the place/licence threading (what in the real closure the ONE licensed offer corresponds to: the single `events.emit('source-read', docname, arg)` call), and correcting the meta/conformance prose. This is a docs-fidelity finding for the maintainers; it does not admit a wrong implementation, and I confirmed that mechanically rather than asserting it.

**VERDICT:** SOUND. 19 attacks run to completion (>= the required 5), spanning the prior pass's exact breaker plus partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, divergence, licence-laundering, ordering and marker-integrity classes; zero CANDIDATEs; positive control and a rewritten-correct control both verify; vacuity control correctly fails; resolve lane proven live on gold. No evidence is missing and no needed run was skipped.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_18.py`, `atk_19.py`, `atk_20.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no attack was a CANDIDATE. All 19 same-spec wrong implementations were REJECTED by the frozen spec (adversary weakness exit 2 in every case), so there is no verifying wrong impl whose faithful patch could fail to resolve, and no attack patch was materializable.

The model.py under audit (sha256 92d07730344a5121d53737fbe16452b179d65bb25eb891790934854634aa17dd) is a REPAIRED spec: it now carries an IO/effect discipline absent from the version a prior G-EQ pass recorded as BROKEN. `hook_offer_io(t_pre, region, t_post)` is an @IOOperation parameterised by the offered region; the step arrives with token(t_pre, 3) plus a licence naming exactly ONE offer of ToSeq(lines).take(len-2), emit_and_collect spends licence+token, and Ensures(token(t_post)) forces the offer to have happened. I re-encoded the prior breaker class directly and it is now dead:

  atk_3  (== prior BREAKER atk_12: extra offer of the WHOLE gathered sequence, framing markers included, fresh copy, yield discarded, forwarded value bit-identical to gold)
    -> atk_3.py:177: The precondition of method emit_and_collect might not hold. There might be insufficient permission to access hook_offer_io(t_pre, ToSeq(body), t_post).
  atk_4  (== prior atk_13: extra offer of just the two framing markers) -> same insufficient-permission rejection.
  atk_13 (SHARPEST, my own escalation: extra offer of a FRESH, VALUE-EQUAL copy of exactly the LICENSED body region, yield discarded, value bit-identical to gold — the case a value-only contract and a region-keyed-but-non-linear licence would both miss) -> also rejected, insufficient permission hook_offer_io.

That last one is the decisive evidence: hook_offer_io behaves as a LINEAR resource, so a second offer of the very same region value has no licence to spend. The prior pass's whole defect class (dispatch invisible to a pure value contract) is closed, and closed at the mechanism level, not by accident.
```

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 19 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_20.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-11510.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When textual content that has been gathered for inclusion into a document is
  handed on to the parser, that content first passes through the document-set's
  content-transformation hook, so that any registered transformer observes and
  may rewrite it before it is parsed -- exactly as the content of a primary
  document does.

  The gathered content arrives as a sequence of lines whose final two entries
  are internal book-keeping markers that frame the inserted region; they are
  not part of the authored content. The transformation therefore applies to the
  AUTHORED body only -- every line except the final two -- while the two framing
  markers are carried through unchanged and re-attached, in their original
  positions, after the (possibly rewritten) body. The result is the line
  sequence forwarded to the parser.

  Consequently: the forwarded sequence is the transformed body followed by the
  two original framing markers; the two framing markers are preserved verbatim;
  and the body region is precisely what the transformation hook is offered.

  Offering content to the hook is an EFFECT, seen by the registered transformers
  themselves, and it is NOT recoverable from the forwarded sequence: two steps
  can forward one and the same sequence while having shown the transformers
  different content, or having shown them content more than once. Which content
  is offered, and how many times, is therefore part of the behaviour specified
  here and not an implementation's free choice. A forwarding step is licensed
  for exactly ONE offer, of exactly the authored body region, and forwarding is
  conditional on spending that licence: a step that forwards content it never
  offered, or that offers a region other than the authored body, or that offers
  a second time, is not this behaviour -- whatever sequence it hands back.

  That obligation is carried the standard way effects are carried here. An offer
  is an operation (`hook_offer_io`) parameterised by the region it shows; a step
  receives a token at a place together with the licence naming the one offer
  permitted there, an offer spends licence and token and yields the token at the
  place the licence names, and the step must hand a token at that place back to
  its caller. So the offer cannot be skipped (the token is only obtainable by
  making it), cannot show another region (the licence names the region), and
  cannot happen twice (there is one licence and a step cannot mint one).

Lines are modelled as `List[int]` of opaque per-line identities (the content of
a line is a value; the line-text round trip "join the lines, hand to the hook,
split again" is the identity at line granularity for content with no embedded
line breaks, which is the regime the behaviour concerns). The content
transformation hook is an opaque, uninterpreted pure function on the body line
sequence (`hook`): it stands for arbitrary registered transformer code, so the
specification constrains only WHICH region is offered to it, how often, and that
the framing markers bypass it, never what it computes. The specification is
carried over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def hook(body: PSeq[int]) -> PSeq[int]:
    """The document-set content-transformation hook, applied to the authored
    body line sequence. Uninterpreted: it stands for arbitrary registered
    transformer code, so it carries NO Ensures -- the specification pins only
    that it is offered exactly the body region (framing markers excluded) and
    that its result replaces that region, never what it returns. (mapping.md)"""
    Requires(True)

@IOOperation
def hook_offer_io(t_pre: Place, region: PSeq[int], t_post: Place = Result()) -> bool:
    """The observable EFFECT of the forwarding step: the content-transformation
    hook is shown the line sequence `region` -- one offer -- carrying the step
    from place `t_pre` to place `t_post`. It models the offer itself, not what
    the hook computes from it (`hook` above does that): what it pins is that an
    offer HAPPENED and WHICH region it showed. A step holds one instance of this
    operation per offer it is permitted to make and an offer spends one; a step
    cannot mint an instance, so how many offers are made and which region each
    one shows are settled by the step's contract instead of chosen by its
    implementation. An offer terminates."""
    Terminates(True)

@ContractOnly
def emit_and_collect(t_pre: Place, body: List[int]) -> List[int]:
    """Offer the authored body to the content-transformation hook and collect
    the (possibly rewritten) body it yields. Models the unchanged content-
    dispatch machinery together with the line<->text round trip around it: the
    result is `hook` applied to the body. The body is read at a fractional share
    and returned unchanged; the yielded sequence is a fresh list. Offering is an
    effect, so this also spends one licence to show exactly `body` plus the token
    that reaches it, and hands back the token at the place that licence names: it
    is callable only where the caller's own contract licenses an offer of exactly
    that region. (mapping.md)"""
    IOExists1(Place)(
        lambda t_post: (
        Requires(Acc(list_pred(body), 1 / 2)),
        Requires(token(t_pre, 2) and hook_offer_io(t_pre, ToSeq(body), t_post)),
        Requires(MustTerminate(2)),
        Ensures(token(t_post)),
        Ensures(Acc(list_pred(body), 1 / 2)),
        Ensures(Acc(list_pred(Result()))),
        Ensures(ToSeq(Result()) == hook(ToSeq(body))),
        )
    )
# axioms-end

# pure-start
@Pure
def transformed(lines: PSeq[int]) -> PSeq[int]:
    """The line sequence forwarded to the parser: the hook-transformed authored
    body (every line but the final two) followed by the two framing markers,
    re-attached verbatim in their original positions. The two framing markers
    are always present in the gathered content; when fewer than two lines are
    present (never, in the modelled regime) the whole sequence is treated as
    body, keeping the function total so the precondition is trivially met."""
    if len(lines) < 2:
        return hook(lines)
    return hook(lines.take(len(lines) - 2)) + lines.drop(len(lines) - 2)
# pure-end

def forward_with_source_read(t_pre: Place, lines: List[int]) -> List[int]:
    IOExists1(Place)(
        lambda t_post: (
        # pre-conditions-start
        # The gathered line sequence is read-only here (it is consumed to build
        # the forwarded sequence, never mutated in place); fractional permission,
        # required and ensured, so no caller may satisfy a postcondition
        # vacuously by overwriting the input. The final two entries are the
        # framing markers, so at least two lines are present.
        Requires(Acc(list_pred(lines), 1 / 2)),
        Requires(len(lines) >= 2),
        # The step arrives holding a token and a licence for exactly ONE offer,
        # of exactly the authored body region (the gathered lines minus the two
        # framing markers). That is the whole effect budget it is given: no
        # second offer, and no offer of any other region, is available to it.
        Requires(token(t_pre, 3) and
                 hook_offer_io(t_pre, ToSeq(lines).take(len(lines) - 2), t_post)),
        Requires(MustTerminate(3)),
        # pre-conditions-end
        # post-conditions-start
        # The licensed offer has been MADE: the token handed back sits at the
        # place the licence names, which is reachable only by showing the hook
        # exactly the authored body region. So content is never forwarded
        # unoffered, and the offer that happened showed that region and no
        # other.
        Ensures(token(t_post)),
        Ensures(Acc(list_pred(lines), 1 / 2)),
        Ensures(Acc(list_pred(Result()))),
        # The forwarded sequence is the hook-transformed authored body followed
        # by the two original framing markers: the body region is exactly what
        # the hook is offered, and the result replaces that region.
        Ensures(ToSeq(Result()) == transformed(ToSeq(lines))),
        # The two framing markers are preserved verbatim, in their original
        # order and position (the last two lines of the output equal the last
        # two lines of the input).
        Ensures(len(Result()) >= 2),
        Ensures(ToSeq(Result()).drop(len(Result()) - 2) == ToSeq(lines).drop(len(lines) - 2)),
        # The authored body region (everything but the final two output lines)
        # is precisely the region offered to and replaced by the hook.
        Ensures(ToSeq(Result()).take(len(Result()) - 2) == hook(ToSeq(lines).take(len(lines) - 2))),
        # post-conditions-end
        )
    )
    # impl-start
    n = len(lines)
    # Split off the authored body (all but the final two framing markers) and
    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
    body = lines[:n - 2]
    markers = lines[n - 2:]
    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))
    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))
    # Offer the body to the content-transformation hook, spending the step's one
    # licence; its (possibly rewritten) result replaces the body region.
    new_body = emit_and_collect(t_pre, body)
    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))
    # Re-attach the framing markers, in their original positions, after the
    # transformed body, and forward the result.
    result = new_body + markers
    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** 19 distinct same-spec wrong impls, generated by gen.py which copies the bundle model.py and rewrites ONLY the text between # impl-start / # impl-end. All 19 confirmed `adversary same-spec` = SAME, and I additionally checked PROGRAMMATICALLY (via markers.parse_regions) that every file's text OUTSIDE the impl span is byte-identical to the frozen model, head and tail — so axioms/@Pure/Requires/Ensures/docstring are untouched. Verifications were run as concurrent background batches of 3 (each Nagini check spawns JVM+Z3), per instruction; results collected per-attack.

### CONTROLS (all four ran):
- pos_control.py, byte-identical copy: `bash scripts/nagini_verify.sh` -> 'Verification successful', 16.61s, rc=0. Toolchain reaches real verdicts.
- pos_alt.py, BEHAVIOURALLY CORRECT but rewritten (offers a value-equal fresh copy of the body region, appends the two markers one at a time) -> 'Verification successful', 13.54s. So the 19 rejections are the spec discriminating BEHAVIOUR, not pinning the frozen syntax; the spec is not rejecting everything.
- atk_2.py VACUITY CONTROL (`Assert(False)` in the impl): REJECTED, 'Assertion False might not hold'. The token+licence precondition is SATISFIABLE on entry, so the IO discipline is not verifying vacuously through an infeasible precondition. This mattered: an IO/obligation spec is exactly where a guarded self-call or unsatisfiable place assumption can verify while proving nothing.
- prepatch_reproduced: atk_1.py re-encodes model_prepatch.py's bug in the strongest available form — it MAKES the licensed offer (so the token obligation is discharged) but DISCARDS the hook's yield and forwards the gathered lines verbatim. Rejected on Postcondition ToSeq(Result()) == transformed(ToSeq(lines)). G-DIFF holds.

PER-ATTACK (cmd in every case: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-11510 <path>`; all exit 2 = NOT-A-COUNTEREXAMPLE; reason from `bash scripts/nagini_verify.sh <path>`):
  atk_1  prepatch, offer made + yield discarded, verbatim forward -> Postcond transformed
  atk_3  extra offer WHOLE gathered seq (prior breaker)          -> insufficient permission hook_offer_io
  atk_4  extra offer of the two FRAMING MARKERS (prior atk_13)   -> insufficient permission hook_offer_io
  atk_5  body offered TWICE, 2nd yield forwarded                 -> insufficient permission hook_offer_io
  atk_6  markers offered FIRST, then body (last-write-wins mask)  -> insufficient permission hook_offer_io
  atk_7  BOUNDARY split n-1, a marker swallowed into offered body-> insufficient permission hook_offer_io (licence names the exact region)
  atk_8  PARTIAL DOMAIN, verbatim at the n==2 boundary            -> Postcond transformed
  atk_9  CONTROL-FLOW EFFECT, offer only on the n>3 branch        -> insufficient permission token(t_post) (offer cannot be skipped on any path)
  atk_10 DIVERGENCE, correct value but infinite loop              -> 'Obligation leak check failed' (method-level MustTerminate(3) bites)
  atk_11 ORDERING, markers + new_body                            -> Postcond transformed
  atk_12 DOUBLE TRANSFORM hook(hook(body))                       -> insufficient permission hook_offer_io
  atk_13 value bit-identical to gold + extra offer of a FRESH value-equal copy of the LICENSED region -> insufficient permission hook_offer_io  [the decisive linearity result]
  atk_14 UNGROUNDED ORACLE ECHO: result built element-by-element out of the pure `transformed`, no offer at all -> insufficient permission token(t_post)
  atk_15 oracle echo WITH the offer made but its yield discarded  -> Postcond markers-drop equality
  atk_16 LICENCE LAUNDERING via self-call on a value-equal copy   -> precondition token(t_pre, 3) insufficient (a step cannot mint/relend a licence)
  atk_18 markers DROPPED                                         -> Postcond transformed
  atk_19 markers DUPLICATED (present but not in original position)-> Postcond transformed
  atk_20 TRUNCATED offer, a proper SUBSET of the body region      -> insufficient permission hook_offer_io
Note the two rejection families are complementary and both real: value postconditions kill wrong FORWARDED SEQUENCES, the licence/token discipline kills wrong OFFERS (extra, wider, narrower, misordered, skipped, relent). atk_14 in particular shows the result must be PRODUCED BY the dispatch rather than equated to an oracle value (directive 8).

EXCLUDED, NOT COUNTED AS SPEC STRENGTH: atk_17.py (marker rebuild using `del`) returned 'Translation failed — Not supported: Unsupported operator', i.e. a Nagini FRONT-END artifact and NO VERDICT, not a rejection by the spec. I did not submit it and take no strength credit for it; its intent was re-encoded as atk_18 and atk_19, which translate and are genuinely rejected. (Same discipline as retained-attack-label hygiene: an echo/timeout must never be re-judged into the reject lane.)

**RESOLVE RUNS.** No attack was a CANDIDATE, so `patches` is empty and there is no attack patch to run — the BROKEN branch is unreachable here by construction, not by omission. To ensure a SOUND verdict does not rest on an oracle lane I never touched (a silently unavailable Docker oracle would otherwise let 'nothing failed to resolve' mean 'nothing ran'), I ran the gold patch through the OFFICIAL harness: `python resolve.py patch_gold.diff goldctl` -> swebench_unified.harness.run_resolve -> resolved=True, completed=True, FAIL_TO_PASS 2/2 success, PASS_TO_PASS 7/7 success (report saved as resolve_goldctl.json). The resolve lane is live and the base lane intact.

REFINEMENT.MD LEG AUDIT (A legs; R/I mechanically covered by G-CONF). Legs A1(R), A2(R+I), A3(I), A4(A-consumed), A5(R+I), A6(R). No kind-3 leg is DECLARED, and — unlike at the prior pass — the claim now holds: the one genuinely-changed operation (route the body through the hook, splice the result back inside the framing markers) is modeled structurally in `transformed`/`forward_with_source_read`, AND the offer EFFECT that the prior pass found unexpressible is now expressed, by hook_offer_io + the licence/token threading. mapping.md §3.1's stated obligation ('the markers include_lines[-2:] must be passed through untouched — they are never offered to the event') is no longer prose-only: atk_3/atk_4/atk_7/atk_20 show the frozen contract itself now enforces which region is offered.

The single A-consumed axiom emit_and_collect binds to EventManager.emit('source-read', docname, arg) plus the '\n'.join / str.splitlines round trip; G-AX (recorded pass, 8 boundary + 20 000 fuzz line sets against the REAL EventManager and real os_path) exercises marker exclusion, marker reattachment, event-text == join(lines[:-2]), round-trip identity and hook propagation. hook stays an uninterpreted @Pure symbol with no Ensures, so it is not an oracle the result is pinned to. F2P test_include_source_read_event asserts on the OFFERED text and that is now inside the spec's reach — which is precisely the leg that failed before.

DOCUMENTATION DEFECT (advisory, NOT a verify=>correct break; nothing to do with the machine verdict). refinement.md is STALE with respect to the repaired model and under-describes the very machinery that now carries the proof:
- refinement.md (dated Aug 5) has ZERO mentions of hook_offer_io / token / Place / licence, while model.py (Aug 14) has 24. Its A4 leg still writes the callee as `emit_and_collect(body)` and its §A table row for A1 as `lines: List[int]`, but the real signatures are `emit_and_collect(t_pre: Place, body)` and `forward_with_source_read(t_pre: Place, lines)`. The `t_pre`/`t_post` place threading — the entire reason the offer effect is now pinned, and the entire reason this bundle is no longer BROKEN — has NO refinement leg at all, and §D's verify=>resolved argument is still argued purely from the value postconditions.
- meta.json's `axioms` entry likewise documents only the Ensures `ToSeq(Result()) == hook(ToSeq(body))` and never mentions the licence/token conjunct that is doing the discriminating work; `deep_model_references` is empty.
- conformance_check.py §Shadow claims the impl region is copied VERBATIM, but its shadow is `forward_with_source_read(lines)` calling `emit_and_collect(body)` — the pre-repair, place-free signature. The value legs it checks are still sound (the places are ghost/effect state with no value content, so the 101 512-input agreement still transfers), but the 'VERBATIM' wording is now inaccurate and the shadow exercises none of the effect discipline.
Recommend refreshing refinement.md with an explicit A-leg for the place/licence threading (what in the real closure the ONE licensed offer corresponds to: the single `events.emit('source-read', docname, arg)` call), and correcting the meta/conformance prose. This is a docs-fidelity finding for the maintainers; it does not admit a wrong implementation, and I confirmed that mechanically rather than asserting it.

**VERDICT:** SOUND. 19 attacks run to completion (>= the required 5), spanning the prior pass's exact breaker plus partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, divergence, licence-laundering, ordering and marker-integrity classes; zero CANDIDATEs; positive control and a rewritten-correct control both verify; vacuity control correctly fails; resolve lane proven live on gold. No evidence is missing and no needed run was skipped.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE SETUP. Fresh worktree from the upstream repository at base_commit 6cb783c0024a873722952a67ebb9f41771c8eb6d, with patch.diff APPLIED (per instructions the modelled function's reference is the patched tree). Confirmed the patched closure is live: sphinx/directives/other.py:380 `_insert_input`, installed at:406 behind the `events.listeners.get('source-read')` gate.

**SPEC REGION INTEGRITY.** model.py verifies under the pinned verifier (scripts/nagini_verify.sh -> "Verification successful", 15.45s). G-DIFF control holds: model_prepatch.py (forwards lines verbatim) FAILS at model_prepatch.py:152 ("Postcondition... might not hold... insufficient permission to access token(t_post)") -- the IO/obligation encoding genuinely senses the delta the patch introduces, so the spec is not vacuous.

INDEPENDENT DIFFERENTIAL PROBES (mine, not the bundle's). I lifted the REAL patched `Include.run.<locals>._insert_input` off a real Include instance (asserting `_insert_input` in `__qualname__` so a non-patched tree cannot silently pass), drove it through the REAL EventManager/os_path/Project.path2doc and the REAL docutils StateMachine.insert_input, and read the forwarded sequence back out of `input_lines`. A priority-0 non-mutating spy listener recorded WHICH region was offered and HOW MANY times, and also satisfied the patch's listener gate so the closure installs in every configuration. Checked all seven model.py obligations per input: input-not-mutated (the 1/2 permission), exactly ONE offer (the IO licence), offered region == "\n".join(lines[:-2]) with the real emitted docname (the licence's region argument), len(Result())>=2, markers verbatim in final position, Result().take(len-2)==hook(body), and the full Result()==transformed(lines).
  - probe.py: 4576 observations (576 boundary x 16 shapes x 4 paths x 9 listener configs, + 4000 fuzz) -> 0 divergences.
  - probe3.py: 6640 observations with adversarial UNRESTRICTED listener output -- every str.splitlines() boundary char (\r, \r\n, \v, \f, \x1c, \x1d, \x1e, \x85, LS, PS), empty output, 200-line output, leading/trailing/only-newlines, output that re-emits the marker text, and three chained listeners in priority order -> 0 divergences.
  Shapes deliberately included OUT-OF-REGIME inputs the mapping's stated regime excludes (body lines with embedded \r, \x85, LS, and a literal \n; empty body len(lines)==2; body ending in a blank line so the join/splitlines round trip is NOT the identity; arbitrary non-docutils marker strings). All still hold, because `hook: PSeq[int]->PSeq[int]` is uninterpreted and length-changing, so it absorbs the join/split behaviour rather than assuming it -- the spec is if anything weaker than the stated regime, not stronger.

BUNDLE CHECKS REPRODUCED in my own patched worktree: axiom_check.py exit 0 (8 boundary + 20000 fuzz, real EventManager + real os_path); conformance_check.py exit 0 (101512 inputs, 0 disagreements, all 5 shadow mutants refuted, oracle guarded as the real patched closure).

STRONGEST ATTACK I MOUNTED, AND WHY IT FAILS (probe2.py). model.py's `hook` is @Pure on the body line sequence ALONE, whereas the real dispatch is `emit('source-read', docname, arg)` with docname = path2doc(os_path(path)). I built a docname-branching listener (an ordinary Sphinx pattern) and showed the real closure forwards ['Baz[baz/baz] was here.',...] for path='baz/baz.rst' but ['Baz[foo] was here.',...] for path='foo.rst' on the SAME `lines`; likewise a stateful listener yields 'call1:'/'call2:' on two calls with identical (lines, path). This is NOT a faithfulness defect: `forward_with_source_read` takes no path parameter and the postcondition is per-call, so the spec makes no cross-call claim. `emit_and_collect` and `transformed` apply the same uninterpreted `hook` symbol to the same `body` value, so for every single execution the per-call net listener effect is a satisfying interpretation -- which is precisely what probe3 confirmed by instantiating `hook` per execution and finding 0 failures. Reporting this as UNFAITHFUL would require comparing two distinct calls, which is not a diverging INPUT.

Other too-strong candidates ruled out: len(Result())>=2 (real always reattaches exactly 2 markers); MustTerminate(3) (documented raise-path scoping -- emit can raise ExtensionError via a listener, but then the real closure never returns and never reaches the parser, so the postcondition is only claimed in the returning regime); Requires(len(lines)>=2) narrows the DOMAIN, which weakens rather than strengthens, and is justified by docutils' insert_into_input_lines unconditionally appending ['', '.. end of inclusion from "..."'] (misc.py:277).

ENVIRONMENT CAVEAT (not a spec finding, per prior host-saturation/environment guidance). The two F2P tests ERROR under pytest in this worktree, but on a fixture/version mismatch (installed docutils 0.23 + sphinxcontrib RemovedInSphinx80Warning), not on the modelled behaviour: docutils 0.23 restructured Include.run into read_file/insert_into_input_lines. This is an environment defect in my ad-hoc worktree, not evidence about the spec -- the correctness signal comes from conformance_check.py, which CALLS the real patched closure and its whole real downstream path and reports 0 disagreements over 101512 inputs.

**CONCLUSION:** no input exists on which the modelled function disagrees with the real patched callee. The spec is not too strong and does not drift from real repo behavior. FAITHFUL.

**REFERENCE SETUP.** Fresh worktree from the upstream repository at base_commit 6cb783c0024a873722952a67ebb9f41771c8eb6d, with patch.diff APPLIED (per instructions the modelled function's reference is the patched tree). Confirmed the patched closure is live: sphinx/directives/other.py:380 `_insert_input`, installed at:406 behind the `events.listeners.get('source-read')` gate.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** RELAXED_LEAKAGE.md re-checked as a CLAIM, not inherited. Verdict NO-LEAKAGE: the spec view leaks nothing beyond the one facet the relaxation covers (the two-marker frame), and I re-derived the unavoidability argument and the core gates myself rather than taking the file's word.

FACET RE-CONFIRMED (the only non-public increment): the spec view narrates the two-marker frame -- model.py docstring 'The gathered content arrives as a sequence of lines whose final two entries are internal book-keeping markers that frame the inserted region', plus the post-condition comments and the executable clauses transformed() = hook(lines.take(len-2)) + lines.drop(len-2) / Ensures(...drop(len(Result())-2) ==...). Token matrix I ran over problem_statement / hints_text / spec_view (computed via markers.spec_view, sha256 ae37fd07b124e872..., == meta.json G-HYGIENE region_hashes.spec_view): marker/framing/book-keeping/'final two' = ABSENT from problem_statement AND ABSENT from hints_text, PRESENT in spec view. Fix MECHANISM stays hidden: insert_input/StateMachine/splitlines/'".join'/monkey are in hints_text only and ABSENT from the spec view; os_path/path2doc absent everywhere in the view. Mechanical scan: 0 gold-diff added lines appear verbatim in the spec view, and 0 of {Include, insert_input, StateMachine, `_insert_input`, os_path, path2doc, sphinx/directives/other.py, events.emit, include_lines, docutils} appear.

UNAVOIDABILITY RE-DERIVED INDEPENDENTLY (strip-the-narration test, not inherited). Built model_deleak.py: a marker-AGNOSTIC spec using only problem_statement vocabulary (transformed(lines) = hook(lines), licence for one offer of the WHOLE gathered sequence, no take/drop, no marker prose). Results: (a) it VERIFIES with the whole-lines impl (11.53s) -- so de-narration is possible syntactically; (b) its prepatch twin (result = lines[:n], no offer) FAILS at model_deleak_prepatch.py:69 token(t_post) -- so the removed clause was not what senses the prepatch; (c) decisively, the GOLD-FAITHFUL impl (offer lines[:n-2], reattach lines[n-2:]) is REJECTED under the de-leaked spec (model_deleak_goldimpl.py:80: precondition of emit_and_collect might not hold, hook_offer_io(t_pre, ToSeq(body), t_post)). So the marker-agnostic spec admits exactly the impl the gold rejects and rejects the gold -- the marker clause is load-bearing, not lazy narration.

And the marker exclusion is a genuinely TESTED discriminator -- I measured it in-repo, not from the file. Fresh worktree at base_commit 6cb783c0024a873722952a67ebb9f41771c8eb6d (the upstream repository), gold patch.diff + test_patch applied, venv sphinx 7.2.0 / docutils 0.20.1. Gold: source-read handler records '\nBaz was here.' (the F2P-asserted value). Variant with the marker exclusion removed ('\n'.join(include_lines) and text.splitlines() with no reattach): records '\nBaz was here.\n\n.. end of inclusion from ".../baz/baz.rst"' -> test_include_source_read_event FAILS. (Both runs also show a benign env artifact: the docname key is the pytest tmp srcdir path, so that assert fails on docname in my ad-hoc venv either way; the RECORDED TEXT, which is the discriminator, is unambiguous.) No problem_statement-only derivation of the two-marker structure exists: it is docutils' Include appending ['', '.. end of inclusion from "%s"'], and the public issue is a pure symptom report (&REPLACE_ME; reaches a primary doc, not an included one).

CORE GATES THE RELAXATION LEANS ON -- RE-RUN BY ME, ALL PASS: G-VERIFY: model.py 'Verification successful' 19.93s. G-DIFF: model_prepatch.py FAILS at:152 token(t_post); markers.same_spec(model, model_prepatch) = True. G-AX: axiom_check.py rc=0 against the real EventManager('source-read') + os_path, 8 boundary + 20000 fuzz. G-CONF: conformance_check.py rc=0, real patched Include.run.`_insert_input` closure, 101512 inputs (1512 boundary incl. both F2P shapes + 100000 fuzz seed=11510), 21512 transformed() cross-checks, 5 shadow mutants refuted, 0 disagreements. NON-VACUITY control: Assert(False) spliced into the impl FAILS ('Assertion False might not hold'), so the verification is not vacuous. PROSE-STRIP control: stripping the module docstring, every function docstring and every non-marker comment still verifies (14.05s) -- the marker discriminator lives in the EXECUTABLE contracts, so it is spec content, not decoration.

STALE-FAIL RESOLVED IN THE SPEC'S FAVOUR (I did not treat the recorded fails as live). meta.json records G-EQ fail and G-PANEL/-1/-2/-3 fail, all on model.py hash 296e85952b2f -- NOT the current 92d07730344a. The old breakers were extra/duplicate hook offers invisible to a pure value contract. I rebuilt all three against the CURRENT spec (atk_12 extra offer of the whole gathered seq; atk_13 extra offer of the two markers; atk_8 body offered twice): 'adversary same-spec' = SAME for 3/3 (spec byte-identical), and 'adversary weakness' = rc=2 NOT-A-COUNTEREXAMPLE for 3/3 -- all rejected. The current model adds 'from nagini_contracts.io_contracts import *' with hook_offer_io/token/licence, which is precisely the fix direction the old verdict.md prescribed. So the core is sound NOW and the recorded G-EQ fail is stale, not a broken disposition.

### BUNDLE FINDINGS (flagged per instruction, none of which changes the verdict):
1. **WIRING CLAIM IS FALSE.** RELAXED_LEAKAGE.md line 154-155 asserts 'meta.json records gates.G-LEAK.status = "relaxed" with a pointer to this document.' It does not. meta.json has G-LEAK.status = "pass" (detail 'spec view clean', failures []) and there is NO relaxed_leakage key anywhere in meta.json (checked top-level keys and a regex over the whole serialized blob: 0 hits for 'relax'). So the documented relaxation is NOT wired into the record -- the bundle presents itself as a clean mechanical G-LEAK pass while carrying an un-referenced relaxation memo. The gate precondition as described to me (meta.json relaxed_leakage + RELAXED_LEAKAGE.md) is only half-present.
2. **SELF-SERVING MISDESCRIPTION OF THE RECORD.** The memo asserts 'the verification CORE is fully SOUND (G-VERIFY/G-DIFF/G-MUT/G-EQ/G-AX/faithfulness clean)' (line 16-17) and 'G-EQ: SOUND/TIGHT' (line 121), which meta.json flatly contradicts (G-EQ fail, G-PANEL-1/2/3 fail). My own re-run shows the SUBSTANCE is now correct -- the breakers are dead against the current spec -- but the memo states a clean G-EQ as fact rather than disclosing that G-EQ is recorded fail on a superseded hash. A reviewer who inherited the memo would have recorded a soundness claim the bundle's own metadata denies.
3. REVIEWER-DIRECTED / DISPOSITION-ASSERTING LANGUAGE. 'Disposition: ACCEPTED under the relaxed-leakage policy' (line 3), 'KEEP under the relaxed-leakage policy' (Conclusion), and 'The adversarial reconstruction judgment is binding' (line 143) attempt to hand the reader a settled disposition and to characterize a prior panel's judgement as binding on this one. I treated all of it as a claim to check; every load-bearing fact above is my own measurement (commands and outputs cited), and the NO-LEAKAGE verdict rests on my de-narration experiment and my gate re-runs, not on the memo's acceptance.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
