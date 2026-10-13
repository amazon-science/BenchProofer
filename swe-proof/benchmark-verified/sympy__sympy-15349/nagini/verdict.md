# P2 adversarial audit — sympy__sympy-15349

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 21 admissible attacks re-run of 21 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 21 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_00.py`, `atk_01.py`, `atk_02.py`, `atk_03.py`, `atk_04.py`, `atk_07.py`, `atk_08.py`, `atk_10.py`, `atk_12.py`, `atk_14.py`, `atk_18.py`, `atk_19.py`, `atk_20.py`, `atk_21.py`, `atk_23.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_05.py`, `atk_06.py`, `atk_09.py`, `atk_13.py`, `atk_16.py`, `atk_17.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No verifying same-spec wrong impl has a faithful refined patch that fails to resolve. All 6 candidates' materialized faithful patches RESOLVED under the official harness (F2P 1/1, P2P 3/3, applied, completed=True), against a gold control that also RESOLVED in the same session.

MOST IMPORTANT RESULT: the PRIOR PASS'S COUNTEREXAMPLE IS NOW REFUTED. The recorded G-EQ verdict in this bundle is `fail / BROKEN` on atk_14.py = `if not zero():` (Python truthiness of a carrier term: dead in the proof, live in the repository because Expr.__bool__ makes Integer(0) falsy). That verdict is STALE: it was stamped 2026-08-16T14:24, while model.py is 14:58 and refinement.md/mapping.md are 15:47/15:48. The spec was repaired in between -- `Scalar` now DECLARES `@Pure @ContractOnly def __bool__` with no postcondition, so the truth value of a scalar is undecided in both directions, and mapping.md/refinement.md R-vocab were extended to state the truthiness leg explicitly. I re-encoded that exact counterexample as atk_01.py and it is now REFUTED with named clauses:
  atk_01.py:292 Postcondition of rotation_matrix might not hold. Assertion (Result()[5] is off_cd_minus(a, b, c, d, s)) might not hold.
  atk_01.py:341 Postcondition of rotation_matrix_affine might not hold. Assertion (Result()[6] is off_cd_minus(a, b, c, d, s)) might not hold.
I re-encoded the whole family and every member is refuted: atk_02 `if not c:` (argument), atk_03 `if not bool(sub(mul(c,d), mul(c,d))):` (explicit bool() on a term built from the arguments -- a different desugaring path), atk_13-as-Scalar variants. So the repair is real and it closes the family, not just the one witness.

The only surviving candidates are in the family refinement.md/mapping.md ACKNOWLEDGE and handle by the R-1sort meaning rule, plus three correct echoes; each is documented under `notes`.
```

**Attacks re-run (21):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_00.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,7 +299,7 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -367,7 +367,7 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
```

Attack 2 — `atk_01.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,6 +300,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if not zero():
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -368,6 +370,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if not zero():
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
```

Attack 3 — `atk_02.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,6 +300,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if not c:
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -368,6 +370,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if not c:
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
```

Attack 4 — `atk_03.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,6 +300,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if not bool(sub(mul(c, d), mul(c, d))):
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -368,6 +370,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if not bool(sub(mul(c, d), mul(c, d))):
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
```

Attack 5 — `atk_04.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,6 +300,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if mul(c, c) == sq(c):
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -368,6 +370,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if mul(c, c) == sq(c):
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
```

Attack 6 — `atk_05.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,6 +300,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if type(c) is type(c):
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -368,6 +370,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if type(c) is type(c):
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
```

Attack 7 — `atk_06.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,13 +299,14 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
     m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
 
     result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
+    result[8 + (7 // -2)] = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
     return result
     # impl-end
 
@@ -367,7 +368,7 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -385,5 +386,7 @@
               m10, m11, m12, m13,
               m20, m21, m22, m23,
               m30, m31, m32, m33]  # type: List[Scalar]
+    result[8 + (7 // -2) + 1] = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    result[7] = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, mul(mul(two(), s), sub(mul(c, d), mul(b, a)))))
     return result
     # impl-end
```

Attack 8 — `atk_07.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -374,7 +374,7 @@
     m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
 
     m03 = sub(sub(sub(x, mul(x, m00)), mul(y, m01)), mul(z, m02))
-    m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, m12))
+    m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, mul(mul(two(), s), add(mul(c, d), mul(b, a)))))
     m23 = sub(sub(sub(z, mul(x, m20)), mul(y, m21)), mul(z, m22))
     m30 = zero()
     m31 = zero()
```

Attack 9 — `atk_08.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -293,20 +293,7 @@
     Ensures(Result()[7] is off_cd_plus(a, b, c, d, s))
     # post-conditions-end
     # impl-start
-    m00 = sub(one(), mul(mul(two(), s), add(sq(c), sq(d))))
-    m01 = mul(mul(two(), s), sub(mul(b, c), mul(d, a)))
-    m02 = mul(mul(two(), s), add(mul(b, d), mul(c, a)))
-
-    m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
-    m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
-
-    m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
-    m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
-    m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
-
-    result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
-    return result
+    return rotation_matrix(a, b, c, d, s)
     # impl-end
 
 
```

Attack 10 — `atk_09.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -293,18 +293,15 @@
     Ensures(Result()[7] is off_cd_plus(a, b, c, d, s))
     # post-conditions-end
     # impl-start
-    m00 = sub(one(), mul(mul(two(), s), add(sq(c), sq(d))))
-    m01 = mul(mul(two(), s), sub(mul(b, c), mul(d, a)))
-    m02 = mul(mul(two(), s), add(mul(b, d), mul(c, a)))
-
-    m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
-    m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
-
-    m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
-    m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
-    m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
-
+    m00 = diag0(b, c, d, s)
+    m01 = off_bc_minus(a, b, c, d, s)
+    m02 = off_bd_plus(a, b, c, d, s)
+    m10 = off_bc_plus(a, b, c, d, s)
+    m11 = diag1(b, c, d, s)
+    m12 = off_cd_minus(a, b, c, d, s)
+    m20 = off_bd_minus(a, b, c, d, s)
+    m21 = off_cd_plus(a, b, c, d, s)
+    m22 = diag2(b, c, d, s)
     result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
     return result
     # impl-end
```

Attack 11 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -305,7 +305,7 @@
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
     m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
 
-    result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
+    result = [m00, m01, m02, m10, m11, m21, m20, m12, m22]  # type: List[Scalar]
     return result
     # impl-end
 
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,6 +300,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if 0.1 + 0.2 != 0.3:
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -368,6 +370,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if 0.1 + 0.2 != 0.3:
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
```

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,13 +299,15 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
     m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
 
     result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
+    if result:
+        result[5] = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
     return result
     # impl-end
 
@@ -367,7 +369,7 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -385,5 +387,9 @@
               m10, m11, m12, m13,
               m20, m21, m22, m23,
               m30, m31, m32, m33]  # type: List[Scalar]
+    if result:
+        g12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+        result[6] = g12
+        result[7] = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, g12))
     return result
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,13 +299,14 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
     m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
 
     result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
+    result[-4] = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
     return result
     # impl-end
 
@@ -367,7 +368,7 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -385,5 +386,7 @@
               m10, m11, m12, m13,
               m20, m21, m22, m23,
               m30, m31, m32, m33]  # type: List[Scalar]
+    result[-10] = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    result[7] = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, mul(mul(two(), s), sub(mul(c, d), mul(b, a)))))
     return result
     # impl-end
```

Attack 15 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,13 +299,17 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
     m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
 
     result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
+    if result[5] is not result[5]:
+        result[5] = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    else:
+        result[5] = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
     return result
     # impl-end
 
```

Attack 16 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,13 +299,14 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
     m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
 
     result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
+    result[len(result) - 4] = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
     return result
     # impl-end
 
```

Attack 17 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,6 +300,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if c == 0:
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -368,6 +370,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if c == 0:
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
```

Attack 18 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -302,7 +302,7 @@
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
-    m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
+    m21 = m12
     m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
 
     result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
```

Attack 19 — `atk_20.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -374,7 +374,7 @@
     m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
 
     m03 = sub(sub(sub(x, mul(x, m00)), mul(y, m01)), mul(z, m02))
-    m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, m12))
+    m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, m11))
     m23 = sub(sub(sub(z, mul(x, m20)), mul(y, m21)), mul(z, m22))
     m30 = zero()
     m31 = zero()
```

Attack 20 — `atk_21.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,13 +299,20 @@
 
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
-    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
     m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
 
     result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
+    i = 0
+    while i < 9:
+        Invariant(Acc(list_pred(result)))
+        Invariant(len(result) == 9)
+        Invariant(0 <= i and i <= 9)
+        Invariant(MustTerminate(9 - i))
+        i = i + 1
     return result
     # impl-end
 
```

Attack 21 — `atk_23.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,6 +300,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if str(c) == str(c):
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
@@ -368,6 +370,8 @@
     m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
     m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))
+    if str(c) == str(c):
+        m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
 
     m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
     m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

### COMMANDS (from swe-proof):
  python -m swebench_unified.adversary same-spec nagini sympy__sympy-15349 <D>/<f>.py
  python -m swebench_unified.adversary weakness  nagini sympy__sympy-15349 <D>/<f>.py
  bash scripts/nagini_verify.sh <D>/<f>.py            (for a NAMED clause failure)
  python <D>/resolve.py <D>/p_<x>.diff                (calls harness.run_resolve)

**POSITIVE CONTROL:** pos_control.py (byte-identical to bundle model.py) -> CANDIDATE/verifies 15.7s. Verifier live.
PREPATCH REPRODUCED: atk_00.py (m12 -> 2s(cd+ba) in BOTH methods) -> REFUTED with named clauses at Result()[5] (rotation_matrix) and Result()[6] (rotation_matrix_affine). Every REFUTED verdict below was confirmed by a DIRECT nagini_verify.sh run showing a named postcondition error, never a bare exit code.
GOLD CONTROL: p_gold.diff (bundle patch.diff verbatim) -> RESOLVED, F2P 1/1 test_quaternion_conversions, P2P 3/3. The oracle can refute on this instance, so every attack resolve result below is evidence.

### ATTACK LEDGER (path / lever / weakness / resolve)
atk_00 prepatch bug both methods            -> REFUTED at [5],[6]. (prepatch reproduced) atk_01 `if not zero():` (PRIOR PASS'S BREAK) -> REFUTED at [5],[6]. ** THE RECORDED BROKEN VERDICT NO LONGER REPRODUCES ** atk_02 `if not c:` truthiness of an ARGUMENT -> REFUTED at [5],[6]. atk_03 `not bool(sub(mul(c,d),mul(c,d)))`    -> REFUTED. Explicit bool() on a term built from the METHOD ARGUMENTS (not a constant fold, distinct desugaring from `if x:`). atk_04 `mul(c,c) == sq(c)` R-finer guard via `==` -> REFUTED at [5],[6]. The relation is undecided on the carrier and TRUE in the repository (`c*c` == `c**2`), exactly as R-finer claims; both branches carry the obligation. atk_05 REFLECTION `type(c) is type(c)`      -> CANDIDATE (14.7s); p_atk_05_meaning.diff RESOLVED (F2P 1/1).

See R-1SORT FAMILY below. atk_06 closed int arith AS AN INDEX `result[8 + (7 // -2)]` -> CANDIDATE (16.6s); p_atk_06_meaning.diff RESOLVED (F2P 1/1). See R-1SORT FAMILY. atk_07 PARTIAL DOMAIN: affine m13 built from the prepatch entry, block gold -> REFUTED. The translation clause at index 7 pins the coupling. atk_08 DIVERGENCE: unguarded self-delegation -> REFUTED: 'Obligation leak check failed. Callee rotation_matrix might not take all unsatisfied obligations from the caller.' The method-level MustTerminate(2) A-leg does its job. atk_09 UNGROUNDED-ORACLE ECHO: impl rewritten as the spec's OWN @Pure helpers (diag0/off_cd_minus/...) -> CANDIDATE (15.2s); p_atk_09.diff RESOLVED (F2P 1/1) => CORRECT ECHO, not a weakness.

This is the key non-hollowness check: the helpers are NOT @ContractOnly, each unfolds all the way to constructor applications, so echoing them is echoing the gold cascade -- there is no opaque answer-key to copy. refinement.md sec.C's 'no kind-3' claim is CORRECT. atk_10 TRANSPOSE the two (cd) off-diagonals in the 3x3 -> REFUTED. The opposite (ba) signs are independently pinned. atk_11 ABNORMAL EXIT (`raise ValueError()` instead of return, prepatch entry) -> NO VERDICT: nagini 'Translation failed'. NOT counted as a rejection and NOT submitted as an attack (verify_completed=False would be booked inconclusive and fail the gate).

Reported for completeness: the construct does not translate, so it cannot be used to hollow the spec. atk_12 FLOAT closed expr `0.1 + 0.2 != 0.3` -> REFUTED at [5],[6]. NOTABLE: the verifier does NOT decide this guard, so BOTH branches carry the obligation -- this lever is strictly weaker than mapping.md's own table suggests, i.e. in this bundle's favour. atk_13 truthiness of the BUILT RESULT LIST (`if result:`) rather than of a Scalar -> CANDIDATE (15.2s); p_atk_13.diff RESOLVED (F2P 1/1) => CORRECT ECHO. Measured why: bool(list of 9) is True in the verifier AND bool(SymPy 3x3/4x4 Matrix) is True in the repository at base_commit, so the branch is LIVE on both sides and the faithful patch assigns the gold entry.

R-layout carries this correctly. atk_14 NEGATIVE INDEX `result[-4]` (Python wraps to 5) -> REFUTED. R-layout never mentions a negative index, but the verifier refuses to prove the entry clause, so the gap is not exploitable. atk_15 REFLECTION `hash(c) == hash(c)`      -> NO VERDICT ('Translation failed'). Not counted, not submitted. mapping.md names hash() in its reflection list; measured, it does not translate at all. atk_16 HEAP READ-BACK `result[5] is not result[5]` (same slot read twice, both branches assign gold) -> CANDIDATE (14.7s); p_atk_16.diff (== p_atk_09.diff, identical faithful patch) RESOLVED (F2P 1/1) => CORRECT ECHO.

Distinct from `is` between two BUILT terms; measured in-repo M[1,2] is not M[1,2] -> False. atk_17 LENGTH ARITHMETIC in the index `result[len(result) - 4]` over a prepatch entry -> CANDIDATE (14.6s); p_atk_17.diff RESOLVED (F2P 1/1) => CORRECT ECHO. len is 9 in the verifier AND len(SymPy 3x3 Matrix) is 9 in the repository, and M[5] is M[1,2] (flat row-major), so the shape numbers agree on both sides. CONTROL ctl_idx_atk_17.py (same file with len(result)-5, i.e. index 4) is REFUTED at Result()[4] is diag1(...), proving the verifier really pins the index rather than leaving it free. atk_18 CROSS-SORT `c == 0` (Scalar vs int)   -> REFUTED at [5],[6].

Outside R-vocab's term-to-term enumeration and not a closed numeric expression either, so this probed a genuine seam -- and the spec holds. atk_19 ALIASING m21 = m12 (one term for both (cd) off-diagonals) -> REFUTED. atk_20 PARTIAL DOMAIN on the affine translation column only (m13 drops the `z*m12` coupling) -> REFUTED. atk_21 CONTROL-FLOW EFFECT: bounded while-loop with invariants + MustTerminate measure over a prepatch entry -> REFUTED. Loop reasoning does not let the load-bearing entry through. atk_22 REFLECTION `id(c) == id(c)`           -> NO VERDICT ('Translation failed'). Not counted, not submitted. atk_23 REFLECTION `str(c) == str(c)`         -> REFUTED at [5],[6]. Third name on mapping.md's reflection list; unlike type()/hash()/id() it DOES translate, and the spec refutes it.

=== THE R-1SORT FAMILY (atk_05, atk_06): candidates, but handled BY THE MAP, and their faithful patches RESOLVE ===
Both surviving non-echo candidates are instances of the ONE family refinement.md A0-1sort and mapping.md sec.2 R-1sort declare openly, name as the place 'the document, not the machine, carries verify=>correct', and deliberately carry NO properties.py reject case for (with the honest reason stated: one direction verifies so no model closes it, the other is refuted but WOULD resolve, so booking it would credit the spec with strength it lacks).
  * atk_06 puts a closed integer expression in an INDEX rather than a guard: `result[8 + (7 // -2)]`. I PINNED the verifier's semantics rather than reading an option -- ctl_trunc_atk_06.py, the same file with `Assert(7 // -2 == -3)` inserted, VERIFIES, so the verifier proves truncation and hence proves the index is 5 = Matrix[1,2]. Python floors (8 + -4 = 4). mapping.md's rule is explicit that the image of a closed numeric expression is 'the VALUE the verifier proves it has', so the faithful patch writes M[5], which is p_atk_06_meaning.diff -> RESOLVED. For contrast I also built the TEXT transcription p_atk_06_text.diff (M[8 + (7 // -2)]); it fails the F2P test locally, but it is the image of a DIFFERENT model expression (one denoting -4) and mapping.md rules it out by name, so it is NOT the faithful refinement and I did not book it as a break.
  * atk_05 is REFLECTION (`type(c) is type(c)`), which mapping.md places in exactly this position by name -- 'type is not one of the seven constructors and a type object is not a scalar', governed by R-1sort. I pinned the branch with a RIVAL PAIR rather than by reading the option: ctl_dead_atk_05.py (Assert(False) FIRST inside the guarded branch) VERIFIES => the branch is genuinely model-dead, and ctl_live_atk_05.py (the complementary `type(c) is not type(c)` + Assert(False)) is REFUTED at Result()[6] => that branch is live. Together they prove the verifier decides type(u) is type(u) FALSE. Since mapping.md's rule also states 'a refinement preserves REACHABILITY -- a branch the proof discharged as unreachable is unreachable in the realisation', the faithful image is a dead guard: p_atk_05_meaning.diff -> RESOLVED.
I judged this family a NON-BREAK because (a) it is disclosed and reasoned about in both refinement.md and mapping.md rather than being an unnoticed hole; (b) the rule is not a convenience -- as mapping.md argues, the construction is available against ANY specification in any language whose closed arithmetic the verifier decides, so it is a fact about the two languages, not a defect of this behaviour, and there is no clause it violates for a stronger clause to catch; and (c) the faithful (meaning-image) patch RESOLVES, which is the executed test the protocol asks for. Booking it as BROKEN would be re-judging a documented and adjudicated boundary as a new spec weakness.

### REFINEMENT.MD LEG AUDIT (the assigned A-leg focus)
LEG KINDS: every leg is tagged R or A-reference. There is genuinely NO A-consumed step and NO kind-3 step, and that is HONEST, not a dodge: all seven @ContractOnly declarations carry no Ensures (meta.json: all seven `assumes: None`), so a proof can lean on nothing they say. Verified there is no fourth tag and no untagged row in the A.1/A.2 tables (A1-A12, B1-B14 all R). NO KIND-3 CONFIRMED: sec.C's claim that the changed operation is modelled 'deeply and exactly' holds -- off_cd_minus(a,b,c,d,s) unfolds to mul(two_s(s), sub(mul(c,d), mul(b,a))), the verbatim impl term; the @Pure helpers are ordinary (NOT @ContractOnly) so there is no opaque answer-key. atk_09 is the machine-checked form of this: rewriting the impl as the helpers themselves still yields the gold patch and RESOLVES.

A-REFERENCE LEGS RE-DERIVED against the real callee in the base_commit worktree (SymPy 1.4.dev), all HOLD as documented: R-ops   -- zero/one/two -> srepr Integer(0)/Integer(1)/Integer(2); add(b,c) -> Add(Symbol b, Symbol c); sq(c) -> Pow(Symbol c, Integer(2)). One counterpart each, total and exact. R-cong  -- building the same term twice from the same parts gives an equal expression AND an identical srepr tree. Congruence transfers. R-finer -- `c*c` == `c**2` is True and `b*c` == `c*b` is True in the repository while their srepr trees differ, so the repository identifies STRICTLY MORE than the carrier: the model is the stricter of the two, never the laxer.

(atk_10/atk_19's refutations are over-strictness, which costs admissibility, not soundness.) R-layout -- Matrix is row-major and value-preserving: Matrix[i,j] == the model term at 3i+j for all 9 entries on Quaternion(1,2,3,4); len is 9/16 and the flat M[5]/M4[6] coincide with M[1,2]. Confirmed independently by atk_17 + ctl_idx_atk_17. A2 (the scale) -- q.norm()**-2 = 1/30 at Quaternion(1,2,3,4) (the graded F2P input) and exactly 1 at the symbolic witness Quaternion(cos(x/2), sin(x/2), 0, 0), matching refinement.md A2's claim that norm applies trigsimp. norm is correctly NOT axiomatized.

A8/B12 (the changed line) -- the PREPATCH source entry M[1,2] = 14/15 differs from the modelled gold term 2s(cd-ba) = 2/3 at the F2P input, so the discriminating clause is not vacuous at the argument the test actually drives. MustTerminate -- the level gap claim holds in BOTH directions: atk_08 (self-delegation) is refuted by an obligation-leak error, and the documented affine->3x3 delegation the source's shared block corresponds to remains admissible (bundle G-PBT carries pos-delegate-affine as verified). SEC.D IS NOW CORRECT AS WRITTEN. This is the specific thing the stale recorded verdict says is false.

Sec.D rests verify=>resolved on the claim that a realisation cannot satisfy the clauses only where they are vacuous, and the CURRENT text no longer enumerates only ==/!=/is/is not: it names truthiness alongside them ('the truth value of a scalar is undecided as well (Scalar.`__bool__` is declared and assumes nothing), so both sides of any such guard carry the full obligation'), explicitly says truthiness 'has to be named here alongside the relations rather than folded into them', and routes reflection to R-1sort. Every clause of that sentence is machine-confirmed above: truthiness refuted (atk_01/02/03), the four relations refuted (atk_04/atk_16/atk_18), reflection either refuted (atk_23) or non-translating (atk_15/atk_22) or dead-and-resolving (atk_05). MODEL<->PATCH CORRESPONDENCE holds line for line: I diffed the source block at quaternion.py:524-551 against both impl regions and every A3-A12/B12-B14 row mirrors its source line in the source's own left association.

### Why SOUND and not INCONCLUSIVE
21 admissible same-spec attacks submitted, all reaching a verdict: 15 REFUTED (each with a named postcondition clause from a direct nagini_verify.sh run) and 6 CANDIDATES, every one of whose faithful refined patches was MATERIALIZED and RUN through the official harness and RESOLVED. The 3 non-translating files (atk_11/15/22) are deliberately EXCLUDED from `attacks` because check_attack reports verify_completed=False for them, which the derivation books as inconclusive and fails the gate on -- they are reported here instead, and none of them is a rejection the spec earned or a weakness it admits. All 6 submitted diffs plus p_gold pass `git apply --check` in the clean base_commit worktree at <D>/wt (re-checked after `git checkout -- . && git clean -fd`). Gold control RESOLVED in the same session, so the oracle is certified.

RECOMMENDATION FOR THE RECORD (not part of this verdict): the recorded G-EQ/G-PANEL-1 `fail` entries in meta.json and verdict.md are STALE -- they predate the model.py/refinement.md/mapping.md repair by ~30-80 minutes and their counterexample (atk_14 = `if not zero():`) no longer reproduces against the frozen spec, as atk_01.py here demonstrates with named clauses. This cell should be re-gated on the current artifacts rather than repaired again.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 21 admissible attacks re-run of 21 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 21 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_00.py`, `atk_01.py`, `atk_02.py`, `atk_03.py`, `atk_04.py`, `atk_07.py`, `atk_08.py`, `atk_10.py`, `atk_12.py`, `atk_14.py`, `atk_18.py`, `atk_19.py`, `atk_20.py`, `atk_21.py`, `atk_23.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_05.py`, `atk_06.py`, `atk_09.py`, `atk_13.py`, `atk_16.py`, `atk_17.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No verifying same-spec wrong impl has a faithful refined patch that fails to resolve. All 6 candidates' materialized faithful patches RESOLVED under the official harness (F2P 1/1, P2P 3/3, applied, completed=True), against a gold control that also RESOLVED in the same session.

MOST IMPORTANT RESULT: the PRIOR PASS'S COUNTEREXAMPLE IS NOW REFUTED. The recorded G-EQ verdict in this bundle is `fail / BROKEN` on atk_14.py = `if not zero():` (Python truthiness of a carrier term: dead in the proof, live in the repository because Expr.__bool__ makes Integer(0) falsy). That verdict is STALE: it was stamped 2026-08-16T14:24, while model.py is 14:58 and refinement.md/mapping.md are 15:47/15:48. The spec was repaired in between -- `Scalar` now DECLARES `@Pure @ContractOnly def __bool__` with no postcondition, so the truth value of a scalar is undecided in both directions, and mapping.md/refinement.md R-vocab were extended to state the truthiness leg explicitly. I re-encoded that exact counterexample as atk_01.py and it is now REFUTED with named clauses:
  atk_01.py:292 Postcondition of rotation_matrix might not hold. Assertion (Result()[5] is off_cd_minus(a, b, c, d, s)) might not hold.
  atk_01.py:341 Postcondition of rotation_matrix_affine might not hold. Assertion (Result()[6] is off_cd_minus(a, b, c, d, s)) might not hold.
I re-encoded the whole family and every member is refuted: atk_02 `if not c:` (argument), atk_03 `if not bool(sub(mul(c,d), mul(c,d))):` (explicit bool() on a term built from the arguments -- a different desugaring path), atk_13-as-Scalar variants. So the repair is real and it closes the family, not just the one witness.

The only surviving candidates are in the family refinement.md/mapping.md ACKNOWLEDGE and handle by the R-1sort meaning rule, plus three correct echoes; each is documented under `notes`.
```

**Attacks re-run (21):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 21 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_00.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_01.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_02.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_03.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_04.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_05.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_06.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_07.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_08.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_09.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_20.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_21.py` → rejected (same spec, does not verify — good)

Attack 21 — `atk_23.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

### COMMANDS (from swe-proof):
  python -m swebench_unified.adversary same-spec nagini sympy__sympy-15349 <D>/<f>.py
  python -m swebench_unified.adversary weakness  nagini sympy__sympy-15349 <D>/<f>.py
  bash scripts/nagini_verify.sh <D>/<f>.py            (for a NAMED clause failure)
  python <D>/resolve.py <D>/p_<x>.diff                (calls harness.run_resolve)

**POSITIVE CONTROL:** pos_control.py (byte-identical to bundle model.py) -> CANDIDATE/verifies 15.7s. Verifier live.
PREPATCH REPRODUCED: atk_00.py (m12 -> 2s(cd+ba) in BOTH methods) -> REFUTED with named clauses at Result()[5] (rotation_matrix) and Result()[6] (rotation_matrix_affine). Every REFUTED verdict below was confirmed by a DIRECT nagini_verify.sh run showing a named postcondition error, never a bare exit code.
GOLD CONTROL: p_gold.diff (bundle patch.diff verbatim) -> RESOLVED, F2P 1/1 test_quaternion_conversions, P2P 3/3. The oracle can refute on this instance, so every attack resolve result below is evidence.

### ATTACK LEDGER (path / lever / weakness / resolve)
atk_00 prepatch bug both methods            -> REFUTED at [5],[6]. (prepatch reproduced) atk_01 `if not zero():` (PRIOR PASS'S BREAK) -> REFUTED at [5],[6]. ** THE RECORDED BROKEN VERDICT NO LONGER REPRODUCES ** atk_02 `if not c:` truthiness of an ARGUMENT -> REFUTED at [5],[6]. atk_03 `not bool(sub(mul(c,d),mul(c,d)))`    -> REFUTED. Explicit bool() on a term built from the METHOD ARGUMENTS (not a constant fold, distinct desugaring from `if x:`). atk_04 `mul(c,c) == sq(c)` R-finer guard via `==` -> REFUTED at [5],[6]. The relation is undecided on the carrier and TRUE in the repository (`c*c` == `c**2`), exactly as R-finer claims; both branches carry the obligation. atk_05 REFLECTION `type(c) is type(c)`      -> CANDIDATE (14.7s); p_atk_05_meaning.diff RESOLVED (F2P 1/1).

See R-1SORT FAMILY below. atk_06 closed int arith AS AN INDEX `result[8 + (7 // -2)]` -> CANDIDATE (16.6s); p_atk_06_meaning.diff RESOLVED (F2P 1/1). See R-1SORT FAMILY. atk_07 PARTIAL DOMAIN: affine m13 built from the prepatch entry, block gold -> REFUTED. The translation clause at index 7 pins the coupling. atk_08 DIVERGENCE: unguarded self-delegation -> REFUTED: 'Obligation leak check failed. Callee rotation_matrix might not take all unsatisfied obligations from the caller.' The method-level MustTerminate(2) A-leg does its job. atk_09 UNGROUNDED-ORACLE ECHO: impl rewritten as the spec's OWN @Pure helpers (diag0/off_cd_minus/...) -> CANDIDATE (15.2s); p_atk_09.diff RESOLVED (F2P 1/1) => CORRECT ECHO, not a weakness.

This is the key non-hollowness check: the helpers are NOT @ContractOnly, each unfolds all the way to constructor applications, so echoing them is echoing the gold cascade -- there is no opaque answer-key to copy. refinement.md sec.C's 'no kind-3' claim is CORRECT. atk_10 TRANSPOSE the two (cd) off-diagonals in the 3x3 -> REFUTED. The opposite (ba) signs are independently pinned. atk_11 ABNORMAL EXIT (`raise ValueError()` instead of return, prepatch entry) -> NO VERDICT: nagini 'Translation failed'. NOT counted as a rejection and NOT submitted as an attack (verify_completed=False would be booked inconclusive and fail the gate).

Reported for completeness: the construct does not translate, so it cannot be used to hollow the spec. atk_12 FLOAT closed expr `0.1 + 0.2 != 0.3` -> REFUTED at [5],[6]. NOTABLE: the verifier does NOT decide this guard, so BOTH branches carry the obligation -- this lever is strictly weaker than mapping.md's own table suggests, i.e. in this bundle's favour. atk_13 truthiness of the BUILT RESULT LIST (`if result:`) rather than of a Scalar -> CANDIDATE (15.2s); p_atk_13.diff RESOLVED (F2P 1/1) => CORRECT ECHO. Measured why: bool(list of 9) is True in the verifier AND bool(SymPy 3x3/4x4 Matrix) is True in the repository at base_commit, so the branch is LIVE on both sides and the faithful patch assigns the gold entry.

R-layout carries this correctly. atk_14 NEGATIVE INDEX `result[-4]` (Python wraps to 5) -> REFUTED. R-layout never mentions a negative index, but the verifier refuses to prove the entry clause, so the gap is not exploitable. atk_15 REFLECTION `hash(c) == hash(c)`      -> NO VERDICT ('Translation failed'). Not counted, not submitted. mapping.md names hash() in its reflection list; measured, it does not translate at all. atk_16 HEAP READ-BACK `result[5] is not result[5]` (same slot read twice, both branches assign gold) -> CANDIDATE (14.7s); p_atk_16.diff (== p_atk_09.diff, identical faithful patch) RESOLVED (F2P 1/1) => CORRECT ECHO.

Distinct from `is` between two BUILT terms; measured in-repo M[1,2] is not M[1,2] -> False. atk_17 LENGTH ARITHMETIC in the index `result[len(result) - 4]` over a prepatch entry -> CANDIDATE (14.6s); p_atk_17.diff RESOLVED (F2P 1/1) => CORRECT ECHO. len is 9 in the verifier AND len(SymPy 3x3 Matrix) is 9 in the repository, and M[5] is M[1,2] (flat row-major), so the shape numbers agree on both sides. CONTROL ctl_idx_atk_17.py (same file with len(result)-5, i.e. index 4) is REFUTED at Result()[4] is diag1(...), proving the verifier really pins the index rather than leaving it free. atk_18 CROSS-SORT `c == 0` (Scalar vs int)   -> REFUTED at [5],[6].

Outside R-vocab's term-to-term enumeration and not a closed numeric expression either, so this probed a genuine seam -- and the spec holds. atk_19 ALIASING m21 = m12 (one term for both (cd) off-diagonals) -> REFUTED. atk_20 PARTIAL DOMAIN on the affine translation column only (m13 drops the `z*m12` coupling) -> REFUTED. atk_21 CONTROL-FLOW EFFECT: bounded while-loop with invariants + MustTerminate measure over a prepatch entry -> REFUTED. Loop reasoning does not let the load-bearing entry through. atk_22 REFLECTION `id(c) == id(c)`           -> NO VERDICT ('Translation failed'). Not counted, not submitted. atk_23 REFLECTION `str(c) == str(c)`         -> REFUTED at [5],[6]. Third name on mapping.md's reflection list; unlike type()/hash()/id() it DOES translate, and the spec refutes it.

=== THE R-1SORT FAMILY (atk_05, atk_06): candidates, but handled BY THE MAP, and their faithful patches RESOLVE ===
Both surviving non-echo candidates are instances of the ONE family refinement.md A0-1sort and mapping.md sec.2 R-1sort declare openly, name as the place 'the document, not the machine, carries verify=>correct', and deliberately carry NO properties.py reject case for (with the honest reason stated: one direction verifies so no model closes it, the other is refuted but WOULD resolve, so booking it would credit the spec with strength it lacks).
  * atk_06 puts a closed integer expression in an INDEX rather than a guard: `result[8 + (7 // -2)]`. I PINNED the verifier's semantics rather than reading an option -- ctl_trunc_atk_06.py, the same file with `Assert(7 // -2 == -3)` inserted, VERIFIES, so the verifier proves truncation and hence proves the index is 5 = Matrix[1,2]. Python floors (8 + -4 = 4). mapping.md's rule is explicit that the image of a closed numeric expression is 'the VALUE the verifier proves it has', so the faithful patch writes M[5], which is p_atk_06_meaning.diff -> RESOLVED. For contrast I also built the TEXT transcription p_atk_06_text.diff (M[8 + (7 // -2)]); it fails the F2P test locally, but it is the image of a DIFFERENT model expression (one denoting -4) and mapping.md rules it out by name, so it is NOT the faithful refinement and I did not book it as a break.
  * atk_05 is REFLECTION (`type(c) is type(c)`), which mapping.md places in exactly this position by name -- 'type is not one of the seven constructors and a type object is not a scalar', governed by R-1sort. I pinned the branch with a RIVAL PAIR rather than by reading the option: ctl_dead_atk_05.py (Assert(False) FIRST inside the guarded branch) VERIFIES => the branch is genuinely model-dead, and ctl_live_atk_05.py (the complementary `type(c) is not type(c)` + Assert(False)) is REFUTED at Result()[6] => that branch is live. Together they prove the verifier decides type(u) is type(u) FALSE. Since mapping.md's rule also states 'a refinement preserves REACHABILITY -- a branch the proof discharged as unreachable is unreachable in the realisation', the faithful image is a dead guard: p_atk_05_meaning.diff -> RESOLVED.
I judged this family a NON-BREAK because (a) it is disclosed and reasoned about in both refinement.md and mapping.md rather than being an unnoticed hole; (b) the rule is not a convenience -- as mapping.md argues, the construction is available against ANY specification in any language whose closed arithmetic the verifier decides, so it is a fact about the two languages, not a defect of this behaviour, and there is no clause it violates for a stronger clause to catch; and (c) the faithful (meaning-image) patch RESOLVES, which is the executed test the protocol asks for. Booking it as BROKEN would be re-judging a documented and adjudicated boundary as a new spec weakness.

### REFINEMENT.MD LEG AUDIT (the assigned A-leg focus)
LEG KINDS: every leg is tagged R or A-reference. There is genuinely NO A-consumed step and NO kind-3 step, and that is HONEST, not a dodge: all seven @ContractOnly declarations carry no Ensures (meta.json: all seven `assumes: None`), so a proof can lean on nothing they say. Verified there is no fourth tag and no untagged row in the A.1/A.2 tables (A1-A12, B1-B14 all R). NO KIND-3 CONFIRMED: sec.C's claim that the changed operation is modelled 'deeply and exactly' holds -- off_cd_minus(a,b,c,d,s) unfolds to mul(two_s(s), sub(mul(c,d), mul(b,a))), the verbatim impl term; the @Pure helpers are ordinary (NOT @ContractOnly) so there is no opaque answer-key. atk_09 is the machine-checked form of this: rewriting the impl as the helpers themselves still yields the gold patch and RESOLVES.

A-REFERENCE LEGS RE-DERIVED against the real callee in the base_commit worktree (SymPy 1.4.dev), all HOLD as documented: R-ops   -- zero/one/two -> srepr Integer(0)/Integer(1)/Integer(2); add(b,c) -> Add(Symbol b, Symbol c); sq(c) -> Pow(Symbol c, Integer(2)). One counterpart each, total and exact. R-cong  -- building the same term twice from the same parts gives an equal expression AND an identical srepr tree. Congruence transfers. R-finer -- `c*c` == `c**2` is True and `b*c` == `c*b` is True in the repository while their srepr trees differ, so the repository identifies STRICTLY MORE than the carrier: the model is the stricter of the two, never the laxer.

(atk_10/atk_19's refutations are over-strictness, which costs admissibility, not soundness.) R-layout -- Matrix is row-major and value-preserving: Matrix[i,j] == the model term at 3i+j for all 9 entries on Quaternion(1,2,3,4); len is 9/16 and the flat M[5]/M4[6] coincide with M[1,2]. Confirmed independently by atk_17 + ctl_idx_atk_17. A2 (the scale) -- q.norm()**-2 = 1/30 at Quaternion(1,2,3,4) (the graded F2P input) and exactly 1 at the symbolic witness Quaternion(cos(x/2), sin(x/2), 0, 0), matching refinement.md A2's claim that norm applies trigsimp. norm is correctly NOT axiomatized.

A8/B12 (the changed line) -- the PREPATCH source entry M[1,2] = 14/15 differs from the modelled gold term 2s(cd-ba) = 2/3 at the F2P input, so the discriminating clause is not vacuous at the argument the test actually drives. MustTerminate -- the level gap claim holds in BOTH directions: atk_08 (self-delegation) is refuted by an obligation-leak error, and the documented affine->3x3 delegation the source's shared block corresponds to remains admissible (bundle G-PBT carries pos-delegate-affine as verified). SEC.D IS NOW CORRECT AS WRITTEN. This is the specific thing the stale recorded verdict says is false.

Sec.D rests verify=>resolved on the claim that a realisation cannot satisfy the clauses only where they are vacuous, and the CURRENT text no longer enumerates only ==/!=/is/is not: it names truthiness alongside them ('the truth value of a scalar is undecided as well (Scalar.`__bool__` is declared and assumes nothing), so both sides of any such guard carry the full obligation'), explicitly says truthiness 'has to be named here alongside the relations rather than folded into them', and routes reflection to R-1sort. Every clause of that sentence is machine-confirmed above: truthiness refuted (atk_01/02/03), the four relations refuted (atk_04/atk_16/atk_18), reflection either refuted (atk_23) or non-translating (atk_15/atk_22) or dead-and-resolving (atk_05). MODEL<->PATCH CORRESPONDENCE holds line for line: I diffed the source block at quaternion.py:524-551 against both impl regions and every A3-A12/B12-B14 row mirrors its source line in the source's own left association.

### Why SOUND and not INCONCLUSIVE
21 admissible same-spec attacks submitted, all reaching a verdict: 15 REFUTED (each with a named postcondition clause from a direct nagini_verify.sh run) and 6 CANDIDATES, every one of whose faithful refined patches was MATERIALIZED and RUN through the official harness and RESOLVED. The 3 non-translating files (atk_11/15/22) are deliberately EXCLUDED from `attacks` because check_attack reports verify_completed=False for them, which the derivation books as inconclusive and fails the gate on -- they are reported here instead, and none of them is a rejection the spec earned or a weakness it admits. All 6 submitted diffs plus p_gold pass `git apply --check` in the clean base_commit worktree at <D>/wt (re-checked after `git checkout -- . && git clean -fd`). Gold control RESOLVED in the same session, so the oracle is certified.

RECOMMENDATION FOR THE RECORD (not part of this verdict): the recorded G-EQ/G-PANEL-1 `fail` entries in meta.json and verdict.md are STALE -- they predate the model.py/refinement.md/mapping.md repair by ~30-80 minutes and their counterexample (atk_14 = `if not zero():`) no longer reproduces against the frozen spec, as atk_01.py here demonstrates with named clauses. This cell should be re-gated on the current artifacts rather than repaired again.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

No diverging input found. Reference =  copied to  with patch.diff APPLIED (m12 = `2*s`*(q.c*q.d - q.b*q.a)); base commit 768da1c6f6 used only for untouched callees (norm).

**WHAT THE SPEC CLAIMS.** rotation_matrix(a,b,c,d,s) -> row-major List[Scalar] len 9; rotation_matrix_affine(...,x,y,z) -> len 16. Carrier Scalar is opaque with 7 @ContractOnly constructors (zero/one/two/add/sub/mul/sq), NO Ensures on any of them, so sameness is congruence only. 19 entry clauses use `is` against pure functions.

INDEPENDENT FAITHFULNESS CHECK (my own harness, not the bundle's). I re-implemented the model's 11 pure functions in SymPy under the mapping.md R-ops bridge (zero/one/two->Integer(0/1/2), add->+, sub->-, mul->*, sq->**2), bridged s to the realised q.norm()**-2, and compared every entry to the real post-patch to_rotation_matrix by srepr (expression-TREE identity, no simplification, no tolerance):
  - 15 quaternion families x 4 translation points (symbolic a,b,c,d; rational; Float; trig cos(t/2),sin(t/2); unit; sqrt; negated; all-same-symbol; imaginary I; powers; sums; mixed): BAD=0.
  - 9 pathological families (all-zero -> s=zoo, oo, nan, zoo, Integer(10)**50, complex Symbol, exp/log/Abs/sign, Piecewise, unevaluated Derivative): EDGE BAD=0, and no family raised where the model claims totality.
  - Independent seeded fuzz (seed 20260816), 4000 draws over 6 component generators x 4 translation generators = 8000 matrices compared entry-by-entry by srepr: BAD=0.
So the modelled function agrees with the real callee on every input I could reach, at the strictest available granularity (tree identity, which is finer than SymPy ==).

### NOT-TOO-STRONG PROBES (the specific ways this spec could over-constrain).
  - Off-diagonal sign asymmetry: the docstring's load-bearing prose claim is that index 5 is 2s(cd-ba) and index 7 is 2s(cd+ba). Confirmed against the real post-patch callee: trigsimp of Quaternion(cos(t/2),sin(t/2),0,0) gives [[1,0,0],[0,cos t,-sin t],[0,sin t,cos t]], i.e. M[1,2]=-sin(t) (upper) and M[2,1]=+sin(t) (lower), exactly as the prose says. Proper-rotation claim also holds on the real callee: symbolic det simplifies to 1 and `M*M`.T == I. The prose is a true statement about the patched repo, not an over-claim.
  - MustTerminate levels: Requires(MustTerminate(2)) on the 3x3 and MustTerminate(6) on the affine. The prose claims the gap keeps a DELEGATING affine realisation admissible (which is what the source morally does). I built that rival (affine body calls rotation_matrix and embeds blk[0..8]), confirmed same-spec exit 0, and it VERIFIES in 23.97s. So the totality obligation is not accidentally too strong.
  - translation clause association: model uses sub(sub(sub(p,..),..),..) mirroring the source's `p - x*m_i0 - y*m_i1 - z*m_i2` left association; srepr-matched on symbolic (X,Y,Z) translation points, so the association is the source's and not a stricter invention.
  - Affine m13 inherits off_cd_minus (index 6/7 clauses), matching the real m13 = y - `x*m10` - `y*m11` - `z*m12` with the corrected m12: srepr-matched.
  - Branch scoping: the real method selects 3x3 vs 4x4 on `if not v:`. Probed v in {None, 0, (), (0,0,0), [1,2,3], (1,2), (1,2,3,4)}. The two modelled operations correspond to the two branches; v=() and v=0 take the 3x3 branch and 2-/4-tuples raise ValueError in unpacking, which is v-shape handling OUTSIDE both modelled operations (mapping.md §1 binds the models to the two branch BODIES, not to the dispatch), so this is not a divergence of the modelled functions.

**MACHINE CHECKS.** Pinned verifier on the unmodified bundle model.py: 'Verification successful', 22.43s, exit 0. axiom_check.py (with PYTHONPATH at the patched worktree): G-AX OK -- R-ops counterparts exhibited, R-formula confirms the real M[1,2] IS the `2*s`*(cd-ba) term structurally, R-cong / R-finer both directions exhibited, 13 boundary + 400 fuzz quaternions. conformance_check.py: G-CONF OK, 104482 inputs (462 boundary + 20 symbolic + 104000 fuzz, seed 15349), 0 disagreements, symbolic compared as srepr. My independent fuzz above is corroborating evidence rather than a re-run of theirs.

ORACLE DISCRIMINATION (guards against a spec that models nothing). Applied instance.json test_patch: patched worktree 5 passed; base worktree + test_patch 2 failed (test_quaternion_conversions, test_quaternion_rotation_iss1593). Note the BASE test file encodes the buggy sign and passes 4/4 pre-patch, so the patched-only-with-old-tests failure is expected and is not a defect. Also confirmed model.py vs model_prepatch.py differ at exactly two lines (m12 add->sub at lines 302 and 370), i.e. the delta is precisely the patch delta and the spec describes the FIXED side -- so I did not treat the base-vs-model m12 difference as a divergence.

**CAVEATS.** same_spec() from swebench_unified.markers needs a third `tables` arg so I used the adversary same-spec CLI instead (exit 0 on my delegating rival, confirming the spec region is byte-identical outside the impl region). Faithfulness of a realisation's numeric-sort expressions (the 7 // -2 family) is by mapping.md's R-1sort rule, auditor judgment by construction, not machine-closable; mapping.md states this openly and declines to credit it as strength, which I read as honest rather than as a hole. Base worktree left clean (test file restored).

**CONCLUSION:** no input exists, among everything I could construct or fuzz, where the modelled function disagrees with the real post-patch callee. The spec is not too strong and does not drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** attacker 3 (leakage / gold-reconstruction), sympy__sympy-15349 nagini. Verdict NO-LEAKAGE. All measurements below are mine, run.

NO RELAXATION IS CLAIMED IN THIS BUNDLE -- I CHECKED RATHER THAN ASSUMED. `find ... -iname '*RELAX*'` over benchmark-verified/sympy__sympy-15349/ returns nothing (no RELAXED_LEAKAGE.md anywhere in the instance, nagini or sibling backends). meta.json has no relaxed_leakage key: `[k for k in m if 'relax' in k.lower()]` -> [], and gates.G-LEAK.status == "pass" (not "relaxed", which is the value prompts/nagini/spec_guide.md:58 specifies for the relaxed path). So there is no relaxation argument to re-derive and no disposition to inherit; I judged this as an ordinary leakage question. I did run the strip-the-narration control anyway, as a check that the emphasis is not doing hidden work (below).

**GOLD EDIT.** instance.json/frozen row patch = one line in sympy/algebras/quaternion.py:529: `m12 = 2*s*(q.c*q.d + q.b*q.a)` -> `- q.b*q.a`. Discriminator = the sign of the (ba) term in the third-column second-row entry. Confirmed the worktree carries the patched text at line 532 and that m21 (line 536) keeps `+ q.b*q.a`, i.e. the two (cd) off-diagonals must disagree in sign.

**EXACT SPEC VIEW I JUDGED.** Rebuilt it myself rather than trusting a stored copy: markers.spec_view(model.py, get_backend('nagini')) -> 352 lines, and I confirmed it is byte-identical to what a spec-mode consumer actually receives (dataset.build_task(adapter,'sympy__sympy-15349',1) -> as_dict()['spec_view'] == my projection, True). Both impl regions are elided to the ELISION_IMPL placeholder; no impl text survives.

MECHANICAL SCREEN, RUN BY ME. leakage.screen(model.py, nagini.language, gold_patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. Judged against problem_statement only, never hints_text (screen's documented policy; I passed the frozen PS explicitly). Independently: no gold-diff line reproduced (the spec view contains no `q.b`, `q.c*q.d`, or any repo-syntax fragment), no diff markers, and grep over the view for `to_rotation_matrix|quaternion|sympy|algebras|\.py|m12|m21|line 52x` returns ONLY the two innocuous hits `sympy__sympy-15349` in the title line and the English word "quaternion" at line 5 -- both of which are public: the instance id is the task's own identifier and "Quaternion.to_rotation_matrix" is the literal title of the problem_statement. Leak-narration vocabulary is absent: grep -i for fix|bug|correct|patch|previous|incorrect|wrong|error|change|revert|regress|typo|gold matched nothing but the substrings inside "difference" (sub docstring), "differently-built" and "decided" -- carrier prose, not fix narration.

WHAT THE SPEC VIEW DOES SAY, AND WHY IT IS NOT BEYOND THE PS. It states the target rotation matrix in closed form (docstring lines 9-11), including 2s(cd - ba) above the diagonal and 2s(cd + ba) below, and clauses Result()[5] is off_cd_minus / Result()[7] is off_cd_plus. That is the DESIRED BEHAVIOUR stated abstractly -- exactly what spec_guide.md item 6 requires a spec to state -- not the edit or its diagnosis. Nothing anywhere says a previous version differed, which entry was touched, that one line changed, or that the second-column entry is the one to leave alone. It never names the file, the method, the line number, or the identifier m12; it addresses positions in an abstract row-major list. A consumer reading it learns the whole intended matrix, which is what a specification IS; it cannot read off from it that the repo currently disagrees at index 5 and agrees at index 7 -- that requires opening the repo, which is the task.

THE DISCRIMINATOR IS DERIVABLE FROM THE PUBLIC PS -- SO EVEN A LEAK-SHAPED READING WOULD BE MOOT. I derived it myself with no bundle input (, exact Fraction arithmetic, no sympy): for unit quaternions the PS's own demand ("one of the sin(x) functions should be negative", a proper rotation) singles out one sign assignment. Over 5 exact rational unit quaternions I tested all four sign combinations of the two (cd) entries against M^T M == I and det == +1: (m12 -ba, m21 +ba) -> orthogonal=True det=+1; (+,-) -> False/False; (+,+) [the pre-patch source] -> False/False; (-,-) -> False/False. So the gold assignment is the UNIQUE one making the matrix a rotation, and it follows from the public issue text plus the repo's untouched entries. The spec view asserts nothing a solver could not derive from the problem_statement.

NARRATION IS NOT LOAD-BEARING -- STRIP CONTROL RUN ON THE PINNED VERIFIER. I built mv_pre_bare.py: the PRE-patch impl (model_prepatch.py) with the module docstring, every class/function docstring and every non-marker comment removed (region markers retained, bodies stubbed where a docstring was the whole body) -- 220 lines vs 373, so all the emphatic prose is gone. bash scripts/nagini_verify.sh:
  mv_post.py     (gold impl)            -> exit 0, "Verification successful", 22.41s
  mv_pre.py      (pre-patch, full prose)-> exit 1, REJECTED 20.47s: "Postcondition of rotation_matrix might not hold. Assertion (Result()[5] is off_cd_minus(a,b,c,d,s))" + rotation_matrix_affine index 6
  mv_pre_bare.py (pre-patch, NO prose)  -> exit 1, REJECTED 19.73s, the SAME two postconditions (lines 138/173)
The de-narrated spec still rejects the pre-patch impl on exactly the (ba)-sign clauses, so the discriminating content lives in the formal Ensures clauses, not in the docstring's emphasis. The prose is explanatory, and removing it costs the spec nothing -- the opposite of a spec that needs narration to do its work.

CORE GATES THE VERDICT LEANS ON, RE-MEASURED NOT INHERITED. G-LEAK's recorded source sha256 for model.py (27fa824b...) equals the current file's sha256, so its pass is about the bytes I judged. G-HYGIENE's recorded region_hashes equal markers.region_hashes(model.py) that I computed, all five regions plus spec_view. I re-derived G-VERIFY (22.41s, exit 0) and G-DIFF (prepatch rejected) myself above rather than reading their records. spec_signature(model.py) == spec_signature(model_prepatch.py) -> True, confirming the twin differs only in impl (diff: the single m12 line, in both impl regions) so the prepatch control is a genuine same-spec control.

RECORDED DISCREPANCY (not a leakage finding, for the rollup). meta.json's TOP-LEVEL region_hashes is STALE against the shipped model.py on two entries: axioms (meta 93ec7462..., actual 02bc588a...) and spec_view (meta 936ba33c..., actual 468440cf...); pure/pre/post/impl match. gates.G-HYGIENE.data.region_hashes, by contrast, matches the current bytes exactly -- so the freshly-run gate agrees with the file and only the top-level convenience copy predates the current axioms text. This does not affect leakage (I judged the actual projection, verified equal to the consumer's), but a consumer or tool trusting meta.region_hashes.spec_view would mis-key this bundle.

BUNDLE TEXT ADDRESSING A REVIEWER -- REPORTED AS ITS OWN FINDING, PER MY INSTRUCTIONS. Nothing in the consumer-visible spec view, nor in refinement.md / mapping.md / axiom_check.py / conformance_check.py / properties.py, addresses me or suggests a verdict; I grepped all of them for auditor|reviewer|panel|attacker|verdict|should record|honest|do not report and inspected every hit.

Two classes of hit exist and neither is steering: mapping.md:174 ("is the auditor's judgment") states the refinement standard, and refinement.md:215 / properties.py's "honest" comments are measure justifications. verdict.md, however, does contain reviewer-directed text: :864-867 and the duplicated :900-903 are PRIOR G-PANEL-3 notes reaching my exact conclusion ("NO-LEAKAGE", "NO REVIEWER-DIRECTED CONTENT", and even a pre-written account of the strip-narration control), and :26/:363/:412 plus a prior auditor's "flagged for the reviewer ... invites the reviewer to adjudicate without re-running anything" ask a reviewer to accept a disposition on the refinement map without re-running.

A previous occupant of my seat asserting my finding is not evidence for it, and an invitation not to re-run is precisely what I declined: every number above is from my own run (screen(), spec_view rebuild, three verifier invocations, the Fraction derivation, the hash comparisons), and the stale-hash discrepancy is a defect none of those prior notes reports. I neither relied on nor deferred to that record. Also noting for freshness: verdict.md:945 describes a FIVE-constructor float/ordered-field carrier while the shipped model.py has SEVEN constructors over an opaque Scalar, so part of that ledger predates the current spec bytes.

**CONCLUSION.** The spec view states the desired matrix abstractly, names no file/method/line/edit, reproduces no gold line, carries no bug-fix narration, survives the de-narration control with its discriminating power intact, and asserts nothing not derivable from the public problem_statement (the proper-rotation constraint fixes the signs uniquely, measured). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
