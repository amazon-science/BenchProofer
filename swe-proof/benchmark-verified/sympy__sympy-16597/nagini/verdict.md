# P2 adversarial audit — sympy__sympy-16597

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 admissible attacks re-run of 8 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. The only CANDIDATE (atk_6: shares spec AND verifies, 47.4s / 54.3s on recheck) is NOT a behavioural counterexample. Machine-checked by extracting executable (non-comment) impl lines from all 31 deducers of atk_6.py and model.py: 30 of 31 are line-identical; the sole differing one (deduce_real_transcendental) has gold n=19 / atk_6 n=19 and sorted(gold)==sorted(atk6) -> True (only 'k.nonzero = True' moved earlier). A permutation of straight-line unconditional assignments to DISTINCT fields yields the identical final record, so atk_6's faithful refined patch IS gold. Executed anyway per protocol: run_resolve -> resolved=True, completed=True, F2P 3/3 pass, P2P 74/74 pass, PASS_TO_FAIL 0. Cannot witness verify=>correct. This independently reproduces the bundle's own recorded HONEST CAVEAT about atk_11 (refinement-map ambiguity, not a wrong impl).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -637,35 +637,20 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
     k.odd = True
-    # odd -> integer
     k.integer = True
-    # integer -> rational
     k.rational = True
-    # rational -> real
     k.real = True
-    # real -> !imaginary
     k.imaginary = False
-    # real -> hermitian (self-adjoint)
     k.hermitian = True
-    # rational -> algebraic
     k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
+    # PREPATCH: the old rule set has no `rational -> finite` edge, so
+    # boundedness is never resolved here.
     k.complex = True
-    # odd -> !even
     k.even = False
-    # integer -> !noninteger
     k.noninteger = False
-    # rational -> !irrational
     k.irrational = False
-    # algebraic -> !transcendental
     k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
-    # !even -> distinct from the (even) origin ; real & != 0 -> nonzero
     k.nonzero = True
     return k
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -1204,39 +1204,13 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
     k.infinite = True
-    # the seed
     k.real = True
-    # real -> !imaginary
     k.imaginary = False
-    # real -> hermitian (self-adjoint)
     k.hermitian = True
-    # real -> complex
     k.complex = True
-    # infinite -> !finite
     k.finite = False
-    # !finite -> !rational
-    k.rational = False
-    # !finite -> !algebraic
-    k.algebraic = False
-    # !finite -> !irrational
-    k.irrational = False
-    # !finite -> !transcendental
-    k.transcendental = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even
-    k.even = False
-    # !integer -> !odd
-    k.odd = False
-    # !integer -> !prime
-    k.prime = False
-    # !integer -> !composite
-    k.composite = False
-    # real & !integer -> noninteger
-    k.noninteger = True
-    # !finite -> at no finite distance from the origin ; real & != 0 -> nonzero
+    # PREPATCH: !finite propagates to nothing under the old rule set.
     k.nonzero = True
     return k
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -1515,8 +1515,10 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed; a denied parity propagates to nothing
     k.odd = False
+    # WRONG: reads boundedness off a DENIED parity (rule `!odd -> finite`).
+    k.finite = True
+    k.infinite = False
     return k
     # impl-end
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -1006,33 +1006,25 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
     k.integer = True
     k.nonnegative = True
-    # integer -> rational
     k.rational = True
-    # rational -> real
     k.real = True
-    # real -> !imaginary
     k.imaginary = False
-    # real -> hermitian (self-adjoint)
     k.hermitian = True
-    # rational -> algebraic
     k.algebraic = True
-    # rational / algebraic -> finite (bounded)
     k.finite = True
-    # real / algebraic -> complex
     k.complex = True
-    # nonnegative -> !negative
     k.negative = False
-    # integer -> !noninteger
     k.noninteger = False
-    # rational -> !irrational
     k.irrational = False
-    # algebraic -> !transcendental
     k.transcendental = False
-    # finite -> !infinite
     k.infinite = False
+    # WRONG: conflates the weak bound with the strict sign (`nonnegative ->
+    # positive`), which the origin refutes.
+    k.positive = True
+    k.nonpositive = False
+    k.nonzero = True
     return k
     # impl-end
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -823,28 +823,9 @@
     Ensures(Result().nonzero is None)
     # post-conditions-end
     # impl-start
-    k = KB()
-    # the seed
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
-    return k
+    # WRONG: the propagation re-enters itself, so the closure never drains and
+    # the queried status stays pending forever (the F2P query would hang).
+    return deduce_rational()
     # impl-end
 
 
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -1692,6 +1692,9 @@
     k.algebraic = False
     # transcendental -> finite (bounded)
     k.finite = True
+    # transcendental -> nonzero (the RIVAL containment edge: transcendence is
+    # taken to place the quantity at a definite distance from the origin)
+    k.nonzero = True
     # !algebraic -> !rational
     k.rational = False
     # !rational -> !integer
@@ -1709,8 +1712,6 @@
     k.complex = True
     # finite -> !infinite
     k.infinite = False
-    # !rational -> distinct from the (rational) origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -2641,37 +2641,23 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
     k.imaginary = True
     k.transcendental = True
-    # transcendental -> finite (bounded), independently of the real line
-    k.finite = True
-    # finite -> !infinite
-    k.infinite = False
-    # transcendental -> !algebraic
+    # WRONG: boundedness is taken to follow from transcendence only for
+    # quantities ON the real line, so off it boundedness stays Unknown.
     k.algebraic = False
-    # imaginary / transcendental -> complex
     k.complex = True
-    # imaginary -> antihermitian (anti-self-adjoint)
     k.antihermitian = True
-    # imaginary -> !real (off the real line)
     k.real = False
-    # !algebraic / !real -> !rational
     k.rational = False
-    # !rational -> !integer
     k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
     k.even = False
     k.odd = False
     k.prime = False
     k.composite = False
-    # !real -> !irrational
     k.irrational = False
-    # !real -> !noninteger
     k.noninteger = False
-    # !real -> !nonzero
     k.nonzero = False
-    # !real -> no sign region
     k.positive = False
     k.negative = False
     k.nonpositive = False
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -3132,15 +3132,14 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
     k.nonzero = True
-    # a definitely non-zero quantity lies on the real line
     k.real = True
-    # real -> complex
     k.complex = True
-    # real -> !imaginary
     k.imaginary = False
-    # real -> hermitian (self-adjoint)
     k.hermitian = True
+    # WRONG: a definite distance from the origin is taken to bound the
+    # quantity (`nonzero -> finite`), which an unbounded real quantity refutes.
+    k.finite = True
+    k.infinite = False
     return k
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -543,34 +543,20 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.odd = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
+    k.integer = True
     k.even = True
-    # even -> integer
-    k.integer = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # even -> !odd
-    k.odd = False
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -637,36 +623,21 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.even = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
+    k.integer = True
     k.odd = True
-    # odd -> integer
-    k.integer = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # odd -> !even
-    k.even = False
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
-    # !even -> distinct from the (even) origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
@@ -733,30 +704,18 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
     k.integer = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -824,26 +783,16 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
     k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -912,36 +861,21 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.infinite = False
+    k.noninteger = True
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.rational = False
+    k.complex = True
+    k.finite = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
     k.irrational = True
-    # irrational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # irrational -> finite (bounded)
-    k.finite = True
-    # real -> complex
-    k.complex = True
-    # irrational -> !rational
-    k.rational = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even
-    k.even = False
-    # !integer -> !odd
-    k.odd = False
-    # !integer -> !prime
-    k.prime = False
-    # !integer -> !composite
-    k.composite = False
-    # real & !integer -> noninteger
-    k.noninteger = True
-    # finite -> !infinite
-    k.infinite = False
-    # !rational -> distinct from the (rational) origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
@@ -1006,33 +940,20 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.negative = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
+    k.nonnegative = True
     k.integer = True
-    k.nonnegative = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # nonnegative -> !negative
-    k.negative = False
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -1098,36 +1019,22 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.composite = False
+    k.prime = False
+    k.positive = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
+    k.nonpositive = True
     k.integer = True
-    k.nonpositive = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # nonpositive -> !positive
-    k.positive = False
-    # !positive -> !prime ; !composite
-    k.prime = False
-    k.composite = False
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -1204,40 +1111,23 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.noninteger = True
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.transcendental = False
+    k.irrational = False
+    k.algebraic = False
+    k.rational = False
+    k.finite = False
+    k.complex = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
     k.infinite = True
-    # the seed
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # real -> complex
-    k.complex = True
-    # infinite -> !finite
-    k.finite = False
-    # !finite -> !rational
-    k.rational = False
-    # !finite -> !algebraic
-    k.algebraic = False
-    # !finite -> !irrational
-    k.irrational = False
-    # !finite -> !transcendental
-    k.transcendental = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even
-    k.even = False
-    # !integer -> !odd
-    k.odd = False
-    # !integer -> !prime
-    k.prime = False
-    # !integer -> !composite
-    k.composite = False
-    # real & !integer -> noninteger
-    k.noninteger = True
-    # !finite -> at no finite distance from the origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
@@ -1305,18 +1195,12 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
     k.rational = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even
-    k.even = False
-    # !integer -> !odd
-    k.odd = False
-    # !integer -> !prime
-    k.prime = False
-    # !integer -> !composite
-    k.composite = False
     return k
     # impl-end
 
@@ -1381,7 +1265,6 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed; nothing else follows from it
     k.irrational = False
     return k
     # impl-end
@@ -1448,7 +1331,6 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed; a denied parity propagates to nothing
     k.even = False
     return k
     # impl-end
@@ -1515,7 +1397,6 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed; a denied parity propagates to nothing
     k.odd = False
     return k
     # impl-end
@@ -1586,31 +1467,21 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.infinite = False
+    k.complex = True
+    k.noninteger = True
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.irrational = True
+    k.finite = True
+    k.rational = False
+    k.hermitian = True
+    k.imaginary = False
     k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    k.rational = False
-    k.finite = True
-    # the defining condition of irrationality is met
-    k.irrational = True
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # real & !integer -> noninteger
-    k.noninteger = True
-    # real -> complex
-    k.complex = True
-    # finite -> !infinite
-    k.infinite = False
-    # !rational -> distinct from the (rational) origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
@@ -1681,36 +1552,23 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.infinite = False
+    k.complex = True
+    k.noninteger = True
+    k.irrational = True
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.rational = False
+    k.finite = True
+    k.algebraic = False
+    k.transcendental = True
+    k.hermitian = True
+    k.imaginary = False
     k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    k.transcendental = True
-    # transcendental -> !algebraic
-    k.algebraic = False
-    # transcendental -> finite (bounded)
-    k.finite = True
-    # !algebraic -> !rational
-    k.rational = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # real & !rational & finite -> irrational
-    k.irrational = True
-    # real & !integer -> noninteger
-    k.noninteger = True
-    # real / transcendental -> complex
-    k.complex = True
-    # finite -> !infinite
-    k.infinite = False
-    # !rational -> distinct from the (rational) origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
@@ -1779,33 +1637,20 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
+    k.even = True
+    k.odd = False
     k.integer = True
-    k.odd = False
-    # the defining condition of evenness is met
-    k.even = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -1869,15 +1714,11 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.complex = True
+    k.finite = True
     k.algebraic = True
-    k.finite = True
-    # algebraic -> complex
-    k.complex = True
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -1940,13 +1781,10 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.composite = False
+    k.prime = False
+    k.positive = False
     k.nonnegative = False
-    # positive -> nonnegative, so !nonnegative -> !positive
-    k.positive = False
-    # a prime or composite quantity is positive, so !positive denies both
-    k.prime = False
-    k.composite = False
     return k
     # impl-end
 
@@ -2013,24 +1851,17 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.composite = False
+    k.prime = False
+    k.negative = True
+    k.nonpositive = True
+    k.positive = False
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.nonnegative = False
     k.real = True
-    k.nonnegative = False
-    # real -> complex ; real -> !imaginary ; real -> hermitian
-    k.complex = True
-    k.imaginary = False
-    k.hermitian = True
-    # positive -> nonnegative, so !nonnegative -> !positive
-    k.positive = False
-    # real & !positive -> nonpositive (bounded above by zero)
-    k.nonpositive = True
-    # nonnegative == real & !negative, so real & !nonnegative -> negative
-    k.negative = True
-    # !positive -> !prime ; !composite
-    k.prime = False
-    k.composite = False
-    # negative -> nonzero (strictly below zero)
-    k.nonzero = True
     return k
     # impl-end
 
@@ -2095,18 +1926,14 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.composite = False
+    k.prime = False
+    k.nonpositive = True
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.positive = False
     k.real = True
-    k.positive = False
-    # real -> complex ; real -> !imaginary ; real -> hermitian
-    k.complex = True
-    k.imaginary = False
-    k.hermitian = True
-    # nonpositive == real & !positive (the <- direction)
-    k.nonpositive = True
-    # !positive -> !prime ; !composite
-    k.prime = False
-    k.composite = False
     return k
     # impl-end
 
@@ -2171,15 +1998,12 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonnegative = True
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.negative = False
     k.real = True
-    k.negative = False
-    # real -> complex ; real -> !imaginary ; real -> hermitian
-    k.complex = True
-    k.imaginary = False
-    k.hermitian = True
-    # nonnegative == real & !negative (the <- direction)
-    k.nonnegative = True
     return k
     # impl-end
 
@@ -2245,42 +2069,27 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = False
+    k.composite = False
+    k.prime = False
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.real = True
+    k.rational = True
+    k.odd = False
+    k.integer = True
+    k.even = True
+    k.negative = False
+    k.positive = False
+    k.nonpositive = True
     k.nonnegative = True
-    k.nonpositive = True
-    # bounded above AND below by zero: neither strict sign is possible
-    k.positive = False
-    k.negative = False
-    # the only quantity with both bounds is zero: an even whole number
-    k.even = True
-    k.integer = True
-    # even -> !odd
-    k.odd = False
-    # integer -> rational
-    k.rational = True
-    # rational -> real ; rational -> algebraic
-    k.real = True
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # real -> !imaginary ; real -> hermitian (self-adjoint)
-    k.imaginary = False
-    k.hermitian = True
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
-    # !positive -> !prime ; !composite
-    k.prime = False
-    k.composite = False
-    # nonnegative & nonpositive -> the origin -> !nonzero
-    k.nonzero = False
     return k
     # impl-end
 
@@ -2346,39 +2155,25 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.nonnegative = True
+    k.nonpositive = False
+    k.negative = False
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.real = True
+    k.rational = True
+    k.composite = False
+    k.positive = True
+    k.integer = True
     k.prime = True
-    # prime -> integer ; prime -> positive
-    k.integer = True
-    k.positive = True
-    # a prime quantity is not composite
-    k.composite = False
-    # integer -> rational
-    k.rational = True
-    # rational -> real ; rational -> algebraic
-    k.real = True
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # real -> !imaginary ; real -> hermitian (self-adjoint)
-    k.imaginary = False
-    k.hermitian = True
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
-    # positive -> !negative ; !nonpositive ; nonnegative
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = True
-    # positive -> nonzero (strictly above zero)
-    k.nonzero = True
     return k
     # impl-end
 
@@ -2444,41 +2239,27 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.nonnegative = True
+    k.nonpositive = False
+    k.negative = False
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.real = True
+    k.rational = True
+    k.odd = False
+    k.integer = True
+    k.prime = True
+    k.even = True
+    k.positive = True
     k.composite = False
-    k.positive = True
-    k.even = True
-    # a strictly positive even whole number that is not composite is prime
-    k.prime = True
-    # even -> integer ; even -> !odd
-    k.integer = True
-    k.odd = False
-    # integer -> rational
-    k.rational = True
-    # rational -> real ; rational -> algebraic
-    k.real = True
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # real -> !imaginary ; real -> hermitian (self-adjoint)
-    k.imaginary = False
-    k.hermitian = True
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
-    # positive -> !negative ; !nonpositive ; nonnegative
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = True
-    # positive -> nonzero (strictly above zero)
-    k.nonzero = True
     return k
     # impl-end
 
@@ -2548,34 +2329,23 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonnegative = False
+    k.nonpositive = False
+    k.negative = False
+    k.positive = False
+    k.nonzero = False
+    k.noninteger = False
+    k.irrational = False
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.rational = False
+    k.real = False
+    k.antihermitian = True
+    k.complex = True
     k.imaginary = True
-    # imaginary -> complex
-    k.complex = True
-    # imaginary -> antihermitian (anti-self-adjoint)
-    k.antihermitian = True
-    # imaginary -> !real (off the real line)
-    k.real = False
-    # !real -> !rational
-    k.rational = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # !real -> !irrational (irrationality is a property OF the real line)
-    k.irrational = False
-    # !real -> !noninteger
-    k.noninteger = False
-    # !real -> !nonzero (no position on the line, no distance from the origin)
-    k.nonzero = False
-    # !real -> no sign region
-    k.positive = False
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = False
     return k
     # impl-end
 
@@ -2641,41 +2411,27 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonnegative = False
+    k.nonpositive = False
+    k.negative = False
+    k.positive = False
+    k.nonzero = False
+    k.noninteger = False
+    k.irrational = False
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.rational = False
+    k.real = False
+    k.antihermitian = True
+    k.complex = True
+    k.algebraic = False
+    k.infinite = False
+    k.finite = True
+    k.transcendental = True
     k.imaginary = True
-    k.transcendental = True
-    # transcendental -> finite (bounded), independently of the real line
-    k.finite = True
-    # finite -> !infinite
-    k.infinite = False
-    # transcendental -> !algebraic
-    k.algebraic = False
-    # imaginary / transcendental -> complex
-    k.complex = True
-    # imaginary -> antihermitian (anti-self-adjoint)
-    k.antihermitian = True
-    # imaginary -> !real (off the real line)
-    k.real = False
-    # !algebraic / !real -> !rational
-    k.rational = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # !real -> !irrational
-    k.irrational = False
-    # !real -> !noninteger
-    k.noninteger = False
-    # !real -> !nonzero
-    k.nonzero = False
-    # !real -> no sign region
-    k.positive = False
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = False
     return k
     # impl-end
 
@@ -2742,20 +2498,16 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.transcendental = False
+    k.irrational = False
+    k.algebraic = False
+    k.rational = False
     k.finite = False
-    # !finite -> !rational ; !algebraic ; !irrational ; !transcendental
-    k.rational = False
-    k.algebraic = False
-    k.irrational = False
-    k.transcendental = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
     return k
     # impl-end
 
@@ -2820,27 +2572,20 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonnegative = False
+    k.nonpositive = False
+    k.negative = False
+    k.positive = False
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.noninteger = False
+    k.irrational = False
+    k.rational = False
+    k.real = False
+    k.nonzero = False
     k.integer = False
-    k.nonzero = False
-    # at no distance from the origin AND not a whole number -> off the real line
-    k.real = False
-    # !real -> !rational
-    k.rational = False
-    # !real -> !irrational
-    k.irrational = False
-    # !real -> !noninteger
-    k.noninteger = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # !real -> no sign region
-    k.positive = False
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = False
     return k
     # impl-end
 
@@ -2905,10 +2650,8 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.imaginary = False
     k.antihermitian = False
-    # !antihermitian -> !imaginary
-    k.imaginary = False
     return k
     # impl-end
 
@@ -2973,9 +2716,6 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # The seed forces nothing at all, so the freshly-built all-Unknown record IS
-    # the closed one: no membership, no sign region and neither adjointness
-    # status may be read off order-independence.
     return k
     # impl-end
 
@@ -3044,30 +2784,24 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # !commutative -> !complex (the containment read contrapositively)
+    k.nonnegative = False
+    k.nonpositive = False
+    k.negative = False
+    k.positive = False
+    k.nonzero = False
+    k.noninteger = False
+    k.irrational = False
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.rational = False
+    k.transcendental = False
+    k.algebraic = False
+    k.imaginary = False
+    k.real = False
     k.complex = False
-    # !complex -> !real ; !imaginary
-    k.real = False
-    k.imaginary = False
-    # !complex -> !algebraic ; !transcendental
-    k.algebraic = False
-    k.transcendental = False
-    # !real -> !rational -> !integer
-    k.rational = False
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # !real -> !irrational ; !noninteger ; !nonzero ; no sign region
-    k.irrational = False
-    k.noninteger = False
-    k.nonzero = False
-    k.positive = False
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = False
     return k
     # impl-end
 
@@ -3132,15 +2866,10 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.real = True
     k.nonzero = True
-    # a definitely non-zero quantity lies on the real line
-    k.real = True
-    # real -> complex
-    k.complex = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    return k
-    # impl-end
+    return k
+    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT SOUND.** 8 same-spec impl attacks + 3 rule-level rivals graded end-to-end; no verify=>correct witness.

All attacks built by copying nagini/model.py and editing ONLY the impl region; all 9 files pass same-spec rc=0.

### PER-ATTACK (cmd: python -m swebench_unified.adversary {same-spec,weakness} nagini sympy__sympy-16597 <file>):
atk_1 prepatch FORWARD bug (deduce_odd stops before boundedness): same-spec rc=0; weakness rc=2 verification failed -> REJECTED. atk_2 prepatch BACKWARD bug (deduce_infinite drops the !finite cascade): rc=0; rc=2 -> REJECTED. atk_3 over-strong frontier (deduce_not_odd bounds it): rc=0; rc=2 -> REJECTED. atk_4 boundary/weak-vs-strict conflation (deduce_integer_nonnegative adds positive/nonzero): rc=0; rc=2 -> REJECTED. atk_5 control-flow-effect / divergence (deduce_rational self-call, closure never drains): rc=0; rc=2 -> REJECTED.

NOTE the first encoding (while True + Invariant) returned 'Translation failed / no verdict'; per policy a no-verdict is NOT a refutation, so it was re-encoded until a genuine 'verification failed' verdict was obtained. atk_6 ungrounded-oracle ECHO (nonzero hoisted, attributed to a transcendental->nonzero edge): rc=0; weakness rc=0 CANDIDATE -> patch materialized and RESOLVED=True (see counterexample field). Not a break. atk_7 partial-domain off-the-real-line (deduce_imaginary_transcendental omits finite/infinite): rc=0; rc=2 -> REJECTED. atk_8 ungrounded oracle (deduce_nonzero bounds it): rc=0; rc=2 -> REJECTED. pos_control (all 31 deducers' assignments order-REVERSED, provenance comments stripped): same-spec rc=0; adversary verify -> VERIFIED in 46.7s. So the spec is not vacuously rejecting. prepatch_reproduced=true: both directions of the real prepatch defect (atk_1 forward, atk_2 backward) are rejected.

DEEPER A-LEG ATTACK (the part G-CONF does not cover) — I attacked the RULE THEORY, not just the impls, because every A-leg is A-reference and refinement.md section D rests on the empirical claim 'of 107 candidate rule sets, every one that reproduces all thirty-one records was harness-run to resolved=TRUE'. I tried to falsify exactly that claim.
1. Pin fidelity: probed the real gold-patched engine (Symbol('s',**seed)) for all 31 seeds x 22 fields = 682 cells vs the pins regex-extracted from the FROZEN model.py -> 0 mismatches. The pin table IS the real engine's record.
2. Rule-set sweep: 2270 rivals via in-process FactRules/FactKB (every single added edge [!]A->[!]B over 24 facts, every gold-rule deletion, every multi-conjunct consequent weakening) -> 354 pin-clean.
3. Redundancy filter (the step that makes the sweep meaningful): compared each pin-clean rival's CLOSURE against gold's on 1152 probe seeds (every fact both ways + every satisfiable pair). Most pin-clean rivals are logically REDUNDANT restatements of edges gold already derives (ADD integer->rational, ADD even->integer, ADD prime->positive, ...) and so refine to the same library. Exactly 12 are pin-clean AND behaviourally DISTINCT from gold.
   The two conjunct-weakenings that looked most dangerous, 'WEAKEN rational -> real (was real & finite)' and 'WEAKEN zero -> even (was even & finite)', are NO-OPS: verified differs_on=0 over the probe set, because finite still arrives via rational->algebraic->complex & finite. Not counterexamples.
4. Re-confirmed all 12 through the REAL engine end-to-end (subprocess, rule injected into sympy/core/assumptions.py, original always restored in a finally:): each gives pin_mismatch=0 and gold_seedcell_diff=0 on the 682 cells. So the frozen spec genuinely CANNOT see these 12 — a real coverage question, which is why I graded them rather than reasoning about them.
5. Differential test screen by TEST NAME scoped to the graded set: gold has a fixed 17-failure env baseline but passes all 77 graded tests (F2P 3 + P2P 74); of the 12 rivals, 10 have a failure set IDENTICAL to gold's and 2 (composite->!antihermitian, antihermitian->!composite) newly fail only test_Mul_is_imaginary_real, which is NOT in the graded set.
6. HARNESS (mandatory executed evidence). Materialized 3 faithful refined patches = gold + one rival edge, chosen as the most semantically indefensible / most likely to break: r_infinite_hermitian ('infinite -> hermitian', false for zoo), r_composite_nonanti ('composite -> !antihermitian', the one that breaks an ungraded test), r_odd_nonzero ('odd -> nonzero'). All three git apply --check OK in a base_commit worktree, then run_resolve (concurrently, 3 at a time): ALL THREE resolved=True, completed=True, F2P 3/3, P2P 74/74, PASS_TO_FAIL 0. Plus atk_6_faithful resolved=True. Four executed resolve runs, zero non-resolving. Section D's claim survived my attempt to break it.

REFINEMENT.MD LEG AUDIT (section 3 of the protocol): legs A1, A2, A3, A3b-A3k, A4, A5. Every leg is tagged R or A-reference; there is NO A-consumed leg and NO kind-3 — consistent with model.py's '# axioms-start/end' region declaring no @ContractOnly axiom consumed (so no dead axiom, and adversary's unsound_evasions admissibility check is not in play). Section C's 'no kind-3' claim is accurate: the one operation that genuinely changed (the *->finite containments) is modelled DEEPLY as consistent_theory + the deducers' propagation, with the real FactKB.deduce_all_facts closure appearing only as the A-reference. A-leg correspondence to the real callees INDEPENDENTLY RE-VERIFIED: ran nagini/axiom_check.py against my own from-scratch base_commit+gold worktree -> rc=0, 'G-AX OK: deep model consistent_theory + deducers validated against the REAL sympy assumptions engine on 1389 observations'. A5's deliberate under-specification (boundedness unpinned for the bare algebraic/transcendental seeds) is sound in the same direction as my finding: pinning it would reject correct impls.

**CLOSURE OF THE PRIOR RECORDED FINDING:** verdict.md records a prior G-EQ fail whose rival was gold + 'transcendental -> nonzero'. Re-measured against the FROZEN (sixth-correction) spec it now shows 2 pin mismatches + 1 seed error, i.e. the hole is genuinely closed by A3k's six off-the-line seeds, not merely relabelled.

METHOD ERRORS I CAUGHT AND FIXED (recorded so the runner can discount none of the above): (a) my first screen ran base_commit TEST files, so GOLD itself 'failed' test_infinity — an F2P test that the test_patch must update; fixed by applying instance.json's test_patch (git apply --check OK) before screening. (b) F2P/P2P in instance.json are JSON STRINGS, so set() over them split per-character and silently made the graded scope 25 characters; fixed with json.loads, giving the true 3 F2P + 74 P2P (the '1740 P2P' figure is a string length, not a test count). Both bugs made the screen meaningless, not merely noisy, and every screen number above is post-fix. (c) /tmp reaping removed the first round of ss_*/wk_* logs; rather than report remembered results I RE-RAN all 8 same-spec + 8 weakness checks (3 at a time) so every reported rc is backed by a log now present in the scratch dir.

RESIDUAL RISK (honest, and the only thing I'd flag for a future pass): the spec observes 31 seeds. I proved 12 behaviourally-distinct rule sets are invisible to those 682 cells, and all 4 I harness-ran resolve; the remaining 8 were screened test-differentially (10/12 failure-set-identical to gold, 2/12 differing only on an ungraded test) but NOT harness-run. That is a bounded, disclosed coverage gap, not a demonstrated defect: no rule set I could construct that reproduces the pins fails the graded suite. Verdict SOUND on executed evidence; the gap is why I report it rather than claiming exhaustiveness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 admissible attacks re-run of 8 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. The only CANDIDATE (atk_6: shares spec AND verifies, 47.4s / 54.3s on recheck) is NOT a behavioural counterexample. Machine-checked by extracting executable (non-comment) impl lines from all 31 deducers of atk_6.py and model.py: 30 of 31 are line-identical; the sole differing one (deduce_real_transcendental) has gold n=19 / atk_6 n=19 and sorted(gold)==sorted(atk6) -> True (only 'k.nonzero = True' moved earlier). A permutation of straight-line unconditional assignments to DISTINCT fields yields the identical final record, so atk_6's faithful refined patch IS gold. Executed anyway per protocol: run_resolve -> resolved=True, completed=True, F2P 3/3 pass, P2P 74/74 pass, PASS_TO_FAIL 0. Cannot witness verify=>correct. This independently reproduces the bundle's own recorded HONEST CAVEAT about atk_11 (refinement-map ambiguity, not a wrong impl).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -543,34 +543,20 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.odd = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
+    k.integer = True
     k.even = True
-    # even -> integer
-    k.integer = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # even -> !odd
-    k.odd = False
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -637,36 +623,21 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.even = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
+    k.integer = True
     k.odd = True
-    # odd -> integer
-    k.integer = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # odd -> !even
-    k.even = False
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
-    # !even -> distinct from the (even) origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
@@ -733,30 +704,18 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
     k.integer = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -824,26 +783,16 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
     k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -912,36 +861,21 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.infinite = False
+    k.noninteger = True
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.rational = False
+    k.complex = True
+    k.finite = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
     k.irrational = True
-    # irrational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # irrational -> finite (bounded)
-    k.finite = True
-    # real -> complex
-    k.complex = True
-    # irrational -> !rational
-    k.rational = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even
-    k.even = False
-    # !integer -> !odd
-    k.odd = False
-    # !integer -> !prime
-    k.prime = False
-    # !integer -> !composite
-    k.composite = False
-    # real & !integer -> noninteger
-    k.noninteger = True
-    # finite -> !infinite
-    k.infinite = False
-    # !rational -> distinct from the (rational) origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
@@ -1006,33 +940,20 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.negative = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
+    k.nonnegative = True
     k.integer = True
-    k.nonnegative = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # nonnegative -> !negative
-    k.negative = False
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -1098,36 +1019,22 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.composite = False
+    k.prime = False
+    k.positive = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
+    k.nonpositive = True
     k.integer = True
-    k.nonpositive = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # nonpositive -> !positive
-    k.positive = False
-    # !positive -> !prime ; !composite
-    k.prime = False
-    k.composite = False
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -1204,40 +1111,23 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.noninteger = True
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.transcendental = False
+    k.irrational = False
+    k.algebraic = False
+    k.rational = False
+    k.finite = False
+    k.complex = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
     k.infinite = True
-    # the seed
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # real -> complex
-    k.complex = True
-    # infinite -> !finite
-    k.finite = False
-    # !finite -> !rational
-    k.rational = False
-    # !finite -> !algebraic
-    k.algebraic = False
-    # !finite -> !irrational
-    k.irrational = False
-    # !finite -> !transcendental
-    k.transcendental = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even
-    k.even = False
-    # !integer -> !odd
-    k.odd = False
-    # !integer -> !prime
-    k.prime = False
-    # !integer -> !composite
-    k.composite = False
-    # real & !integer -> noninteger
-    k.noninteger = True
-    # !finite -> at no finite distance from the origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
@@ -1305,18 +1195,12 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
     k.rational = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even
-    k.even = False
-    # !integer -> !odd
-    k.odd = False
-    # !integer -> !prime
-    k.prime = False
-    # !integer -> !composite
-    k.composite = False
     return k
     # impl-end
 
@@ -1381,7 +1265,6 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed; nothing else follows from it
     k.irrational = False
     return k
     # impl-end
@@ -1448,7 +1331,6 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed; a denied parity propagates to nothing
     k.even = False
     return k
     # impl-end
@@ -1515,7 +1397,6 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed; a denied parity propagates to nothing
     k.odd = False
     return k
     # impl-end
@@ -1586,31 +1467,21 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.infinite = False
+    k.complex = True
+    k.noninteger = True
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.irrational = True
+    k.finite = True
+    k.rational = False
+    k.hermitian = True
+    k.imaginary = False
     k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    k.rational = False
-    k.finite = True
-    # the defining condition of irrationality is met
-    k.irrational = True
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # real & !integer -> noninteger
-    k.noninteger = True
-    # real -> complex
-    k.complex = True
-    # finite -> !infinite
-    k.infinite = False
-    # !rational -> distinct from the (rational) origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
@@ -1681,36 +1552,23 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.infinite = False
+    k.complex = True
+    k.noninteger = True
+    k.irrational = True
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.rational = False
+    k.finite = True
+    k.algebraic = False
+    k.transcendental = True
+    k.hermitian = True
+    k.imaginary = False
     k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    k.transcendental = True
-    # transcendental -> !algebraic
-    k.algebraic = False
-    # transcendental -> finite (bounded)
-    k.finite = True
-    # !algebraic -> !rational
-    k.rational = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # real & !rational & finite -> irrational
-    k.irrational = True
-    # real & !integer -> noninteger
-    k.noninteger = True
-    # real / transcendental -> complex
-    k.complex = True
-    # finite -> !infinite
-    k.infinite = False
-    # !rational -> distinct from the (rational) origin ; real & != 0 -> nonzero
-    k.nonzero = True
     return k
     # impl-end
 
@@ -1779,33 +1637,20 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.hermitian = True
+    k.imaginary = False
+    k.real = True
+    k.rational = True
+    k.even = True
+    k.odd = False
     k.integer = True
-    k.odd = False
-    # the defining condition of evenness is met
-    k.even = True
-    # integer -> rational
-    k.rational = True
-    # rational -> real
-    k.real = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    # rational -> algebraic
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -1869,15 +1714,11 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.infinite = False
+    k.transcendental = False
+    k.complex = True
+    k.finite = True
     k.algebraic = True
-    k.finite = True
-    # algebraic -> complex
-    k.complex = True
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
     return k
     # impl-end
 
@@ -1940,13 +1781,10 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.composite = False
+    k.prime = False
+    k.positive = False
     k.nonnegative = False
-    # positive -> nonnegative, so !nonnegative -> !positive
-    k.positive = False
-    # a prime or composite quantity is positive, so !positive denies both
-    k.prime = False
-    k.composite = False
     return k
     # impl-end
 
@@ -2013,24 +1851,17 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.composite = False
+    k.prime = False
+    k.negative = True
+    k.nonpositive = True
+    k.positive = False
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.nonnegative = False
     k.real = True
-    k.nonnegative = False
-    # real -> complex ; real -> !imaginary ; real -> hermitian
-    k.complex = True
-    k.imaginary = False
-    k.hermitian = True
-    # positive -> nonnegative, so !nonnegative -> !positive
-    k.positive = False
-    # real & !positive -> nonpositive (bounded above by zero)
-    k.nonpositive = True
-    # nonnegative == real & !negative, so real & !nonnegative -> negative
-    k.negative = True
-    # !positive -> !prime ; !composite
-    k.prime = False
-    k.composite = False
-    # negative -> nonzero (strictly below zero)
-    k.nonzero = True
     return k
     # impl-end
 
@@ -2095,18 +1926,14 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.composite = False
+    k.prime = False
+    k.nonpositive = True
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.positive = False
     k.real = True
-    k.positive = False
-    # real -> complex ; real -> !imaginary ; real -> hermitian
-    k.complex = True
-    k.imaginary = False
-    k.hermitian = True
-    # nonpositive == real & !positive (the <- direction)
-    k.nonpositive = True
-    # !positive -> !prime ; !composite
-    k.prime = False
-    k.composite = False
     return k
     # impl-end
 
@@ -2171,15 +1998,12 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonnegative = True
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.negative = False
     k.real = True
-    k.negative = False
-    # real -> complex ; real -> !imaginary ; real -> hermitian
-    k.complex = True
-    k.imaginary = False
-    k.hermitian = True
-    # nonnegative == real & !negative (the <- direction)
-    k.nonnegative = True
     return k
     # impl-end
 
@@ -2245,42 +2069,27 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = False
+    k.composite = False
+    k.prime = False
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.real = True
+    k.rational = True
+    k.odd = False
+    k.integer = True
+    k.even = True
+    k.negative = False
+    k.positive = False
+    k.nonpositive = True
     k.nonnegative = True
-    k.nonpositive = True
-    # bounded above AND below by zero: neither strict sign is possible
-    k.positive = False
-    k.negative = False
-    # the only quantity with both bounds is zero: an even whole number
-    k.even = True
-    k.integer = True
-    # even -> !odd
-    k.odd = False
-    # integer -> rational
-    k.rational = True
-    # rational -> real ; rational -> algebraic
-    k.real = True
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # real -> !imaginary ; real -> hermitian (self-adjoint)
-    k.imaginary = False
-    k.hermitian = True
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
-    # !positive -> !prime ; !composite
-    k.prime = False
-    k.composite = False
-    # nonnegative & nonpositive -> the origin -> !nonzero
-    k.nonzero = False
     return k
     # impl-end
 
@@ -2346,39 +2155,25 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.nonnegative = True
+    k.nonpositive = False
+    k.negative = False
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.real = True
+    k.rational = True
+    k.composite = False
+    k.positive = True
+    k.integer = True
     k.prime = True
-    # prime -> integer ; prime -> positive
-    k.integer = True
-    k.positive = True
-    # a prime quantity is not composite
-    k.composite = False
-    # integer -> rational
-    k.rational = True
-    # rational -> real ; rational -> algebraic
-    k.real = True
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # real -> !imaginary ; real -> hermitian (self-adjoint)
-    k.imaginary = False
-    k.hermitian = True
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
-    # positive -> !negative ; !nonpositive ; nonnegative
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = True
-    # positive -> nonzero (strictly above zero)
-    k.nonzero = True
     return k
     # impl-end
 
@@ -2444,41 +2239,27 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonzero = True
+    k.nonnegative = True
+    k.nonpositive = False
+    k.negative = False
+    k.infinite = False
+    k.transcendental = False
+    k.irrational = False
+    k.noninteger = False
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.finite = True
+    k.algebraic = True
+    k.real = True
+    k.rational = True
+    k.odd = False
+    k.integer = True
+    k.prime = True
+    k.even = True
+    k.positive = True
     k.composite = False
-    k.positive = True
-    k.even = True
-    # a strictly positive even whole number that is not composite is prime
-    k.prime = True
-    # even -> integer ; even -> !odd
-    k.integer = True
-    k.odd = False
-    # integer -> rational
-    k.rational = True
-    # rational -> real ; rational -> algebraic
-    k.real = True
-    k.algebraic = True
-    # rational / algebraic -> finite (bounded)
-    k.finite = True
-    # real / algebraic -> complex
-    k.complex = True
-    # real -> !imaginary ; real -> hermitian (self-adjoint)
-    k.imaginary = False
-    k.hermitian = True
-    # integer -> !noninteger
-    k.noninteger = False
-    # rational -> !irrational
-    k.irrational = False
-    # algebraic -> !transcendental
-    k.transcendental = False
-    # finite -> !infinite
-    k.infinite = False
-    # positive -> !negative ; !nonpositive ; nonnegative
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = True
-    # positive -> nonzero (strictly above zero)
-    k.nonzero = True
     return k
     # impl-end
 
@@ -2548,34 +2329,23 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonnegative = False
+    k.nonpositive = False
+    k.negative = False
+    k.positive = False
+    k.nonzero = False
+    k.noninteger = False
+    k.irrational = False
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.rational = False
+    k.real = False
+    k.antihermitian = True
+    k.complex = True
     k.imaginary = True
-    # imaginary -> complex
-    k.complex = True
-    # imaginary -> antihermitian (anti-self-adjoint)
-    k.antihermitian = True
-    # imaginary -> !real (off the real line)
-    k.real = False
-    # !real -> !rational
-    k.rational = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # !real -> !irrational (irrationality is a property OF the real line)
-    k.irrational = False
-    # !real -> !noninteger
-    k.noninteger = False
-    # !real -> !nonzero (no position on the line, no distance from the origin)
-    k.nonzero = False
-    # !real -> no sign region
-    k.positive = False
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = False
     return k
     # impl-end
 
@@ -2641,41 +2411,27 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonnegative = False
+    k.nonpositive = False
+    k.negative = False
+    k.positive = False
+    k.nonzero = False
+    k.noninteger = False
+    k.irrational = False
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.rational = False
+    k.real = False
+    k.antihermitian = True
+    k.complex = True
+    k.algebraic = False
+    k.infinite = False
+    k.finite = True
+    k.transcendental = True
     k.imaginary = True
-    k.transcendental = True
-    # transcendental -> finite (bounded), independently of the real line
-    k.finite = True
-    # finite -> !infinite
-    k.infinite = False
-    # transcendental -> !algebraic
-    k.algebraic = False
-    # imaginary / transcendental -> complex
-    k.complex = True
-    # imaginary -> antihermitian (anti-self-adjoint)
-    k.antihermitian = True
-    # imaginary -> !real (off the real line)
-    k.real = False
-    # !algebraic / !real -> !rational
-    k.rational = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # !real -> !irrational
-    k.irrational = False
-    # !real -> !noninteger
-    k.noninteger = False
-    # !real -> !nonzero
-    k.nonzero = False
-    # !real -> no sign region
-    k.positive = False
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = False
     return k
     # impl-end
 
@@ -2742,20 +2498,16 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.transcendental = False
+    k.irrational = False
+    k.algebraic = False
+    k.rational = False
     k.finite = False
-    # !finite -> !rational ; !algebraic ; !irrational ; !transcendental
-    k.rational = False
-    k.algebraic = False
-    k.irrational = False
-    k.transcendental = False
-    # !rational -> !integer
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
     return k
     # impl-end
 
@@ -2820,27 +2572,20 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.nonnegative = False
+    k.nonpositive = False
+    k.negative = False
+    k.positive = False
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.noninteger = False
+    k.irrational = False
+    k.rational = False
+    k.real = False
+    k.nonzero = False
     k.integer = False
-    k.nonzero = False
-    # at no distance from the origin AND not a whole number -> off the real line
-    k.real = False
-    # !real -> !rational
-    k.rational = False
-    # !real -> !irrational
-    k.irrational = False
-    # !real -> !noninteger
-    k.noninteger = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # !real -> no sign region
-    k.positive = False
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = False
     return k
     # impl-end
 
@@ -2905,10 +2650,8 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.imaginary = False
     k.antihermitian = False
-    # !antihermitian -> !imaginary
-    k.imaginary = False
     return k
     # impl-end
 
@@ -2973,9 +2716,6 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # The seed forces nothing at all, so the freshly-built all-Unknown record IS
-    # the closed one: no membership, no sign region and neither adjointness
-    # status may be read off order-independence.
     return k
     # impl-end
 
@@ -3044,30 +2784,24 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # !commutative -> !complex (the containment read contrapositively)
+    k.nonnegative = False
+    k.nonpositive = False
+    k.negative = False
+    k.positive = False
+    k.nonzero = False
+    k.noninteger = False
+    k.irrational = False
+    k.composite = False
+    k.prime = False
+    k.odd = False
+    k.even = False
+    k.integer = False
+    k.rational = False
+    k.transcendental = False
+    k.algebraic = False
+    k.imaginary = False
+    k.real = False
     k.complex = False
-    # !complex -> !real ; !imaginary
-    k.real = False
-    k.imaginary = False
-    # !complex -> !algebraic ; !transcendental
-    k.algebraic = False
-    k.transcendental = False
-    # !real -> !rational -> !integer
-    k.rational = False
-    k.integer = False
-    # !integer -> !even ; !odd ; !prime ; !composite
-    k.even = False
-    k.odd = False
-    k.prime = False
-    k.composite = False
-    # !real -> !irrational ; !noninteger ; !nonzero ; no sign region
-    k.irrational = False
-    k.noninteger = False
-    k.nonzero = False
-    k.positive = False
-    k.negative = False
-    k.nonpositive = False
-    k.nonnegative = False
     return k
     # impl-end
 
@@ -3132,15 +2866,10 @@
     # post-conditions-end
     # impl-start
     k = KB()
-    # the seed
+    k.hermitian = True
+    k.imaginary = False
+    k.complex = True
+    k.real = True
     k.nonzero = True
-    # a definitely non-zero quantity lies on the real line
-    k.real = True
-    # real -> complex
-    k.complex = True
-    # real -> !imaginary
-    k.imaginary = False
-    # real -> hermitian (self-adjoint)
-    k.hermitian = True
-    return k
-    # impl-end
+    return k
+    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT SOUND.** 8 same-spec impl attacks + 3 rule-level rivals graded end-to-end; no verify=>correct witness.

All attacks built by copying nagini/model.py and editing ONLY the impl region; all 9 files pass same-spec rc=0.

### PER-ATTACK (cmd: python -m swebench_unified.adversary {same-spec,weakness} nagini sympy__sympy-16597 <file>):
atk_1 prepatch FORWARD bug (deduce_odd stops before boundedness): same-spec rc=0; weakness rc=2 verification failed -> REJECTED. atk_2 prepatch BACKWARD bug (deduce_infinite drops the !finite cascade): rc=0; rc=2 -> REJECTED. atk_3 over-strong frontier (deduce_not_odd bounds it): rc=0; rc=2 -> REJECTED. atk_4 boundary/weak-vs-strict conflation (deduce_integer_nonnegative adds positive/nonzero): rc=0; rc=2 -> REJECTED. atk_5 control-flow-effect / divergence (deduce_rational self-call, closure never drains): rc=0; rc=2 -> REJECTED.

NOTE the first encoding (while True + Invariant) returned 'Translation failed / no verdict'; per policy a no-verdict is NOT a refutation, so it was re-encoded until a genuine 'verification failed' verdict was obtained. atk_6 ungrounded-oracle ECHO (nonzero hoisted, attributed to a transcendental->nonzero edge): rc=0; weakness rc=0 CANDIDATE -> patch materialized and RESOLVED=True (see counterexample field). Not a break. atk_7 partial-domain off-the-real-line (deduce_imaginary_transcendental omits finite/infinite): rc=0; rc=2 -> REJECTED. atk_8 ungrounded oracle (deduce_nonzero bounds it): rc=0; rc=2 -> REJECTED. pos_control (all 31 deducers' assignments order-REVERSED, provenance comments stripped): same-spec rc=0; adversary verify -> VERIFIED in 46.7s. So the spec is not vacuously rejecting. prepatch_reproduced=true: both directions of the real prepatch defect (atk_1 forward, atk_2 backward) are rejected.

DEEPER A-LEG ATTACK (the part G-CONF does not cover) — I attacked the RULE THEORY, not just the impls, because every A-leg is A-reference and refinement.md section D rests on the empirical claim 'of 107 candidate rule sets, every one that reproduces all thirty-one records was harness-run to resolved=TRUE'. I tried to falsify exactly that claim.
1. Pin fidelity: probed the real gold-patched engine (Symbol('s',**seed)) for all 31 seeds x 22 fields = 682 cells vs the pins regex-extracted from the FROZEN model.py -> 0 mismatches. The pin table IS the real engine's record.
2. Rule-set sweep: 2270 rivals via in-process FactRules/FactKB (every single added edge [!]A->[!]B over 24 facts, every gold-rule deletion, every multi-conjunct consequent weakening) -> 354 pin-clean.
3. Redundancy filter (the step that makes the sweep meaningful): compared each pin-clean rival's CLOSURE against gold's on 1152 probe seeds (every fact both ways + every satisfiable pair). Most pin-clean rivals are logically REDUNDANT restatements of edges gold already derives (ADD integer->rational, ADD even->integer, ADD prime->positive, ...) and so refine to the same library. Exactly 12 are pin-clean AND behaviourally DISTINCT from gold.
   The two conjunct-weakenings that looked most dangerous, 'WEAKEN rational -> real (was real & finite)' and 'WEAKEN zero -> even (was even & finite)', are NO-OPS: verified differs_on=0 over the probe set, because finite still arrives via rational->algebraic->complex & finite. Not counterexamples.
4. Re-confirmed all 12 through the REAL engine end-to-end (subprocess, rule injected into sympy/core/assumptions.py, original always restored in a finally:): each gives pin_mismatch=0 and gold_seedcell_diff=0 on the 682 cells. So the frozen spec genuinely CANNOT see these 12 — a real coverage question, which is why I graded them rather than reasoning about them.
5. Differential test screen by TEST NAME scoped to the graded set: gold has a fixed 17-failure env baseline but passes all 77 graded tests (F2P 3 + P2P 74); of the 12 rivals, 10 have a failure set IDENTICAL to gold's and 2 (composite->!antihermitian, antihermitian->!composite) newly fail only test_Mul_is_imaginary_real, which is NOT in the graded set.
6. HARNESS (mandatory executed evidence). Materialized 3 faithful refined patches = gold + one rival edge, chosen as the most semantically indefensible / most likely to break: r_infinite_hermitian ('infinite -> hermitian', false for zoo), r_composite_nonanti ('composite -> !antihermitian', the one that breaks an ungraded test), r_odd_nonzero ('odd -> nonzero'). All three git apply --check OK in a base_commit worktree, then run_resolve (concurrently, 3 at a time): ALL THREE resolved=True, completed=True, F2P 3/3, P2P 74/74, PASS_TO_FAIL 0. Plus atk_6_faithful resolved=True. Four executed resolve runs, zero non-resolving. Section D's claim survived my attempt to break it.

REFINEMENT.MD LEG AUDIT (section 3 of the protocol): legs A1, A2, A3, A3b-A3k, A4, A5. Every leg is tagged R or A-reference; there is NO A-consumed leg and NO kind-3 — consistent with model.py's '# axioms-start/end' region declaring no @ContractOnly axiom consumed (so no dead axiom, and adversary's unsound_evasions admissibility check is not in play). Section C's 'no kind-3' claim is accurate: the one operation that genuinely changed (the *->finite containments) is modelled DEEPLY as consistent_theory + the deducers' propagation, with the real FactKB.deduce_all_facts closure appearing only as the A-reference. A-leg correspondence to the real callees INDEPENDENTLY RE-VERIFIED: ran nagini/axiom_check.py against my own from-scratch base_commit+gold worktree -> rc=0, 'G-AX OK: deep model consistent_theory + deducers validated against the REAL sympy assumptions engine on 1389 observations'. A5's deliberate under-specification (boundedness unpinned for the bare algebraic/transcendental seeds) is sound in the same direction as my finding: pinning it would reject correct impls.

**CLOSURE OF THE PRIOR RECORDED FINDING:** verdict.md records a prior G-EQ fail whose rival was gold + 'transcendental -> nonzero'. Re-measured against the FROZEN (sixth-correction) spec it now shows 2 pin mismatches + 1 seed error, i.e. the hole is genuinely closed by A3k's six off-the-line seeds, not merely relabelled.

METHOD ERRORS I CAUGHT AND FIXED (recorded so the runner can discount none of the above): (a) my first screen ran base_commit TEST files, so GOLD itself 'failed' test_infinity — an F2P test that the test_patch must update; fixed by applying instance.json's test_patch (git apply --check OK) before screening. (b) F2P/P2P in instance.json are JSON STRINGS, so set() over them split per-character and silently made the graded scope 25 characters; fixed with json.loads, giving the true 3 F2P + 74 P2P (the '1740 P2P' figure is a string length, not a test count). Both bugs made the screen meaningless, not merely noisy, and every screen number above is post-fix. (c) /tmp reaping removed the first round of ss_*/wk_* logs; rather than report remembered results I RE-RAN all 8 same-spec + 8 weakness checks (3 at a time) so every reported rc is backed by a log now present in the scratch dir.

RESIDUAL RISK (honest, and the only thing I'd flag for a future pass): the spec observes 31 seeds. I proved 12 behaviourally-distinct rule sets are invisible to those 682 cells, and all 4 I harness-ran resolve; the remaining 8 were screened test-differentially (10/12 failure-set-identical to gold, 2/12 differing only on an ungraded test) but NOT harness-run. That is a bounded, disclosed coverage gap, not a demonstrated defect: no rule set I could construct that reproduces the pins fails the graded suite. Verdict SOUND on executed evidence; the gap is why I report it rather than claiming exhaustiveness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

No input found on which the modelled function disagrees with the real (patched) repo callee. Reference: worktree = base_commit 6fd65310fa3167b9626c38a5487e171ca407d988 + instance-root patch.diff applied (note: patch.diff is at the instance root, NOT inside nagini/). Spec region byte-identity confirmed: `adversary same-spec nagini sympy__sympy-16597 model.py` -> 'SAME — attack shares the bundle's exact specification', exit 0.

I did NOT trust the bundle's own axiom_check.py. I rebuilt an independent harness: parse_pins.py re-extracts every `Ensures(Result().<prop> is <trit>)` pin straight out of model.py's post-condition regions (31 deducers, no duplicate pins, no unpinned KB field among the 22); seeds.py re-derives the 31 seed assumption sets myself from mapping.md's Symbol(...) bindings; parse_clauses.py re-extracts consistent_theory's clauses by brace-matching top-level Implies(...) with comments stripped -> 93 clauses.

Evidence, all against the PATCHED reference:
(1) check_pins.py: 31 seeds x 22 fields = 682/682 pins match Symbol('q', **seed) on the real patched engine. mismatches: 0. So no pin is stronger than the real callee.
(2) probe.py: the 93 clauses evaluated on every satisfiable single/pair/triple seed over 24 fact names (17344 combos -> 11300 real-engine records). violating: 0.
(3) probe4.py: all satisfiable 4-fact seeds, 76184 records. violating: 0. Total 87484 real-engine records, 0 closure violations.
(4) selfcons.py: all 31 pinned records are themselves closed under the 93 clauses (violating: 0) and differ from the real patched engine on 0 records — the spec is internally consistent, so no over-strong pin contradicts the closure predicate.

Only apparent counterexample, investigated and dismissed: numprobe.py over 38 concrete objects (oo, -oo, zoo, nan, Zero, One, Half, Pi, E, I, GoldenRatio, EulerGamma, Catalan, `2*I`, `oo*I`, `pi*I`, sqrt(2), exp(1), log(2), Rational(1,3), Float(1.5), r+I, `p*I`, i/2, `2**x`, pi+E, oo-oo, Integer(-1), Float(0), ...) reported 1 violation: Float(0) on clause `integer=T -> rational=T` (record integer=True, rational=None). Root cause is NOT the modelled callee: sympy/core/numbers.py:922-923 sets CLASS attributes `is_rational = None` / `is_irrational = None` on `class Float` ('A Float represents many real numbers, both rational and irrational'), which shadow the KB-backed properties. Float(0).`_assumptions` after forcing the query contains 'rational': True — the fact closure deduced it correctly. mapping.md 1/2 binds KB to the StdFactKB/FactKB fact table, so I re-ran at that exact carrier: kbprobe.py reads o.`_assumptions` for the 16 numeric singletons after forcing full closure -> objects 16, violating 0. Attribute shadowing sits outside the modelled function; not a faithfulness defect.

Patch-delta control (guards against condemning a correct spec by comparing to base). I also created a clean BASE worktree at 6fd65310 and re-ran check_pins.py there: 43 mismatches. I classified every one. 24 are `finite`/`infinite` pins. The remaining 19 all come from the two unbounded seeds (deduce_infinite {'infinite':True,'real':True}, deduce_unbounded {'finite':False}) and are contrapositives on !rational/!algebraic/!irrational/!transcendental/!integer/!even/!odd/!prime/!composite plus noninteger=True, each base=None -> spec=False/True. Zero mismatches lie off the patch axis.

This is exactly the closure of the four added `& finite` conjuncts ('rational -> real & finite', 'algebraic -> complex & finite', 'transcendental == complex & !algebraic & finite', 'irrational == real & !rational & finite') under deduce_alpha_implications' auto-derived contrapositives. So the base/patched difference is precisely the delta the patch introduces and nothing more — the model describes the fixed behavior, matches it exactly (0 mismatches patched), and correctly fails to match base only on the delta. This also confirms the spec is not vacuously satisfiable by the base engine, i.e. the pins genuinely bite.

Total correctness is pinned, not assumed: every deducer carries Requires(MustTerminate(2)) and the KB constructor Requires(MustTerminate(1)), at method level, so Nagini's default partial correctness cannot let a non-returning body satisfy the 22 field pins vacuously. Per-record closure vacuity is handled by the 31 full 22-field pin instantiations rather than by clause-shaped invariants alone.

Non-defect documentation note (not a faithfulness issue, no verdict impact): refinement.md and mapping.md both say consistent_theory has 'seventy-three clauses'; independent brace-matching counts 93 top-level Implies(...) clauses. The docs undercount; the spec itself is sound. Also per mapping.md 4, the power.py/tree.py/indexed.py hunks of the patch are deliberately not modelled (not F2P-exercised) — I confirmed no F2P behaviour depends on them, so this is a scope choice, not drift. This bundle consumes no @ContractOnly axiom, so there is no unvalidated base-commit callee to attack.

**Conclusion:** no diverging input exists among 87484 swept records, 682 field pins, 38 concrete objects and 16 KB-level singletons. Spec is FAITHFUL to the patched repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / GOLD-RECONSTRUCTION, re-derived from scratch against the CURRENT bundle text. Baseline = problem_statement only (hints_text excluded).

STALE-DOC CAVEAT (reported as a finding in its own right, not a verdict change): RELAXED_LEAKAGE.md claims to describe model.py sha256 b4000ef5...; the file on disk is ebcc571b... (3146 lines, 31 seeds / 31 deducers). The doc narrates a 2-seed model (deduce_even + deduce_infinite) and cites line numbers L14-17/L123/L128/L144/L148/L188/L249-258 that no longer correspond. I therefore treated NOTHING in it as inherited and re-measured every load-bearing claim myself. Its §4 numbers are also stale (G-VERIFY '17.2s' vs my 62.8s; G-AX '425 observations' vs the tool's actual 1389). No file in the bundle addressed me or told me which verdict to record; leakage.reviewer_directed(model.py) == [] (re-run) and the only reviewer-ish grep hits are neutral prose about G-LEAK status ('Only no-leakage relaxes'). So the doc is stale-and-overclaiming on provenance, but it does not direct the reviewer.

**FACET RE-CONFIRMED:** the abstract three-valued theory of the number sets -- containments, the four BOUNDEDNESS edges (rational/algebraic/irrational/transcendental -> finite), exclusions, two-directional closure, plus the per-seed resolved fact tables. Nothing beyond it.

UNAVOIDABILITY RE-DERIVED (not inherited). I rebuilt pristine base assumptions.py from HEAD in the /tmp worktree and ran each candidate rule with the real test_patch functions loaded by path (importlib, since 'sympy.core.tests' shadows under sys.path insertion):
  nothing (pre-patch): 3 FAIL, m.is_finite=None, first fail 'oo.is_integer is False'
  'even -> finite'    : 3 FAIL, m.is_finite=True,  first fail 'oo.is_integer is False'
  'integer -> finite' : 3 FAIL, m.is_finite=True,  first fail 'oo.is_rational is False'
  'rational -> real & finite' (the hints suggestion, alone): 3 FAIL, first fail 'oo.is_algebraic is False'; and it makes oo.is_irrational=True while the hidden test asserts False.
So three impls deliver exactly what the public text asks (is_finite on an even symbol stops being None) and still fail every F2P. The discriminator is WHICH sets force boundedness -- all four -- because the hidden assertions on oo/-oo are the contrapositives of exactly those edges. A problem_statement-only derivation of that discriminator does not exist; the file's claim on this point holds.

VOCABULARY re-derived word-bounded/case-insensitive over instance.json: problem_statement has even=2, finite=1, and ZERO occurrences of real, rational, integer, bounded, algebraic, irrational, transcendental, complex, odd, prime, composite, noninteger, infinite, infinity, contrapositive, closure. algebraic/irrational/transcendental/bounded/complex are 0x in hints too.

LOAD-BEARING TEST run in the prescribed direction, four ways:
 1. Docstring fully stripped (module docstring -> "Model."): gold model STILL verifies (62.7s) and model_prepatch_2 STILL fails on consistent_theory of deduce_infinite. So the prose is not what rejects -- the executable clauses are.
 2. Remove the 9 'finite is False ->' contrapositives from consistent_theory: prepatch_2 still rejected, now via Ensures(Result().integer is False).
 3. Remove those clauses AND the 10 boundedness-derived Ensures pins: prepatch_2 VERIFIES (64.7s). That is the removal that breaks verify=>correct, proving the disclosure is exactly the clause set that rejects the pre-patch impls.
 4. Fresh same-spec rival R2 (impl-only: unboundedness propagated to rational only = the hints fix transcribed): adversary same-spec SAME, adversary weakness -> NOT-A-COUNTEREXAMPLE, spec rejected it.

CORE GATES the relaxation leans on, all re-run by me: G-VERIFY model.py 'Verification successful' 62.80s exit 0. G-DIFF both twins same_spec True via swebench_unified.markers.same_spec and both FAIL -- model_prepatch.py on consistent_theory of deduce_even (+ the other bounded seeds), model_prepatch_2.py on consistent_theory of deduce_infinite. G-AX axiom_check.py OK on 1389 observations against the real patched engine, and correctly FAILS against the pre-patch engine ('F2P FAIL (deduce_even): even=True must give is_finite True, got None') -- so it discriminates rather than rubber-stamping. G-CONF 100012 observations, 0 disagreements. Mechanical screen leakage.screen(model.py, nagini tables, gold, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Worktree restored to gold after each engine swap (verified: 'rational -> real & finite' present, git diff --stat matches).

NOT DISCLOSED anywhere in the spec view (2494 lines, extracted via markers.spec_view): `_assume_rules`, FactRules, FactKB, deduce_all_facts, StdFactKB, Symbol, S.Infinity, NegativeInfinity, get_known_facts, ask_generated, extended_real, Q.finite, 'assumptions.py', 'patch', 'diff' all grep to 0. No F2P test name, no is_finite/is_even attribute spelling, no Symbol( literal (0 hits combined). The other gold hunks are absent: Idx, Indexed, `_eval_is_rational`, fuzzy_and, fuzzy_not, print_tree, as_base_exp, cnf/CNF all 0 -- so power.py/tree.py/indexed.py and the recompiled CNF mirror leak nothing. Narration scan for gold/patch/fix/bug/previously/'was extended'/'now correctly' found only innocuous ordinary-English 'too' and 'definite' matches. The one near-verbatim rule string, model.py:350 '# irrational == real & !rational & finite (the <- direction)', is a comment in the theory's own DSL-free notation naming the equivalence the clause below it encodes -- it is inside the disclosed facet (an equivalence the spec must state to reject R2), not a rendering of the diff, and it survives the strip test as non-load-bearing prose over a load-bearing clause.

**CONCLUSION:** the relaxation's argument holds on the text as it actually stands. The residual disclosure is carried by formal content that cannot be deleted without admitting an impl that fails F2P, it stays inside the number-set-theory facet, and the gates it leans on are sound and discriminating. NO-LEAKAGE. Flagging separately for bundle hygiene, not as a leak: RELAXED_LEAKAGE.md's stated sha256, line numbers, seed count, and G-VERIFY/G-AX figures are all stale relative to model.py and should be regenerated so the record is a measurement of the shipped text.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
