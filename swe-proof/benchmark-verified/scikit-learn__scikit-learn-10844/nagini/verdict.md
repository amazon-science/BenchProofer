# P2 adversarial audit — scikit-learn__scikit-learn-10844

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch.py`, `atk_2_sq_both.py`, `atk_2b_sq_noassert.py`, `atk_3_cross.py`, `atk_4_partial.py`, `atk_5_sq_one.py`, `atk_8_m_ratio.py`, `atk_9_m_root.py`, `atk_11_vacuity.py`, `atk_13_cross_hint.py`, `atk_14_rawdiv.py`, `atk_15_const_scale.py`, `atk_16_drop_qk.py`, `atk_17_unrooted.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6_boundary.py`, `atk_7_echo.py`, `atk_10_swap.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,14 +138,15 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
-        r_q = ratio(tk, qk, m)
-        result = mul(root(r_p, m), root(r_q, m))
+        # Pre-patch evaluation order: form the cross product of the two
+        # marginals FIRST and take the square root of that single combined
+        # quantity, then divide. The combined cross product can exceed the
+        # representable range of the working domain even when each marginal is
+        # itself representable, so the value handed to the square root is not
+        # known to be representable.
+        prod = pk * qk
+        denom = root(prod, m)
+        result = ratio(tk, denom, m)
     else:
         result = 0.0
     return result
```

Attack 2 — `atk_2_sq_both.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,13 +138,19 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
-        r_q = ratio(tk, qk, m)
+        # Each conditional ratio is formed by scaling numerator AND denominator
+        # by the same marginal: (tk*pk)/(pk*pk) == tk/pk, (tk*qk)/(qk*qk) == tk/qk.
+        Assert(tk > 0.0)
+        Assert(pk > 0.0)
+        Assert(qk > 0.0)
+        Assert(pk * pk > 0.0)
+        Assert(qk * qk > 0.0)
+        r_p = (tk * pk) / (pk * pk)
+        r_q = (tk * qk) / (qk * qk)
+        Assert(r_p == tk / pk)
+        Assert(r_q == tk / qk)
+        Assert(r_p >= 0.0 and r_p <= 1.0)
+        Assert(r_q >= 0.0 and r_q <= 1.0)
         result = mul(root(r_p, m), root(r_q, m))
     else:
         result = 0.0
```

Attack 3 — `atk_2b_sq_noassert.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,12 +138,7 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
+        r_p = (tk * pk) / (pk * pk)
         r_q = ratio(tk, qk, m)
         result = mul(root(r_p, m), root(r_q, m))
     else:
```

Attack 4 — `atk_3_cross.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,13 +138,17 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
-        r_q = ratio(tk, qk, m)
+        Assert(tk > 0.0)
+        Assert(pk > 0.0)
+        Assert(qk > 0.0)
+        prod = pk * qk
+        Assert(prod > 0.0)
+        r_p = (tk * qk) / prod
+        r_q = (tk * pk) / prod
+        Assert(r_p == tk / pk)
+        Assert(r_q == tk / qk)
+        Assert(r_p >= 0.0 and r_p <= 1.0)
+        Assert(r_q >= 0.0 and r_q <= 1.0)
         result = mul(root(r_p, m), root(r_q, m))
     else:
         result = 0.0
```

Attack 5 — `atk_4_partial.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,13 +138,21 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
-        r_q = ratio(tk, qk, m)
+        Assert(tk > 0.0)
+        Assert(pk > 0.0)
+        Assert(qk > 0.0)
+        if pk > qk:
+            Assert(pk * pk > 0.0)
+            Assert(qk * qk > 0.0)
+            r_p = (tk * pk) / (pk * pk)
+            r_q = (tk * qk) / (qk * qk)
+            Assert(r_p == tk / pk)
+            Assert(r_q == tk / qk)
+        else:
+            r_p = ratio(tk, pk, m)
+            r_q = ratio(tk, qk, m)
+        Assert(r_p >= 0.0 and r_p <= 1.0)
+        Assert(r_q >= 0.0 and r_q <= 1.0)
         result = mul(root(r_p, m), root(r_q, m))
     else:
         result = 0.0
```

Attack 6 — `atk_5_sq_one.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,12 +138,12 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
+        Assert(tk > 0.0)
+        Assert(pk > 0.0)
+        Assert(pk * pk > 0.0)
+        r_p = (tk * pk) / (pk * pk)
+        Assert(r_p == tk / pk)
+        Assert(r_p >= 0.0 and r_p <= 1.0)
         r_q = ratio(tk, qk, m)
         result = mul(root(r_p, m), root(r_q, m))
     else:
```

Attack 7 — `atk_6_boundary.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -137,16 +137,12 @@
     Ensures(Result() <= 1.0)
     # post-conditions-end
     # impl-start
-    if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
+    if tk > 0.0:
         r_p = ratio(tk, pk, m)
         r_q = ratio(tk, qk, m)
         result = mul(root(r_p, m), root(r_q, m))
     else:
+        Assert(tk == 0.0)
         result = 0.0
     return result
     # impl-end
```

Attack 8 — `atk_7_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -138,14 +138,7 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
-        r_q = ratio(tk, qk, m)
-        result = mul(root(r_p, m), root(r_q, m))
+        result = mul(root(ratio(tk, pk, m), m), root(ratio(tk, qk, m), m))
     else:
         result = 0.0
     return result
```

Attack 9 — `atk_8_m_ratio.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,13 +138,8 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
-        r_q = ratio(tk, qk, m)
+        r_p = ratio(tk, pk, pk)
+        r_q = ratio(tk, qk, qk)
         result = mul(root(r_p, m), root(r_q, m))
     else:
         result = 0.0
```

Attack 10 — `atk_9_m_root.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,14 +138,9 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
         r_p = ratio(tk, pk, m)
         r_q = ratio(tk, qk, m)
-        result = mul(root(r_p, m), root(r_q, m))
+        result = mul(root(r_p, 1.0), root(r_q, 1.0))
     else:
         result = 0.0
     return result
```

Attack 11 — `atk_10_swap.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

```diff
@@ -138,14 +138,9 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
         r_p = ratio(tk, pk, m)
         r_q = ratio(tk, qk, m)
-        result = mul(root(r_p, m), root(r_q, m))
+        result = mul(root(r_q, m), root(r_p, m))
     else:
         result = 0.0
     return result
```

Attack 12 — `atk_11_vacuity.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,15 +138,11 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
         r_p = ratio(tk, pk, m)
         r_q = ratio(tk, qk, m)
         result = mul(root(r_p, m), root(r_q, m))
     else:
         result = 0.0
+    Assert(False)
     return result
     # impl-end
```

Attack 13 — `atk_13_cross_hint.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,12 +138,16 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
+        Assert(tk > 0.0)
+        Assert(pk >= tk and pk > 0.0)
+        Assert(qk >= tk and qk > 0.0)
+        Assert(pk >= 1.0 or pk < 1.0)
+        prod = pk * qk
+        Assert(prod >= qk * tk)
+        Assert(prod > 0.0)
+        num = tk * qk
+        r_p = num / prod
+        Assert(r_p == tk / pk)
         r_q = ratio(tk, qk, m)
         result = mul(root(r_p, m), root(r_q, m))
     else:
```

Attack 14 — `atk_14_rawdiv.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,12 +138,9 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
+        Assert(pk > 0.0)
+        r_p = tk / pk
+        Assert(r_p <= 1.0)
         r_q = ratio(tk, qk, m)
         result = mul(root(r_p, m), root(r_q, m))
     else:
```

Attack 15 — `atk_15_const_scale.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,12 +138,12 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
-        r_p = ratio(tk, pk, m)
+        Assert(pk > 0.0)
+        num = tk * 2.0
+        den = pk * 2.0
+        Assert(den > 0.0)
+        r_p = num / den
+        Assert(r_p == tk / pk)
         r_q = ratio(tk, qk, m)
         result = mul(root(r_p, m), root(r_q, m))
     else:
```

Attack 16 — `atk_16_drop_qk.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,14 +138,8 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
         r_p = ratio(tk, pk, m)
-        r_q = ratio(tk, qk, m)
-        result = mul(root(r_p, m), root(r_q, m))
+        result = root(r_p, m)
     else:
         result = 0.0
     return result
```

Attack 17 — `atk_17_unrooted.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,14 +138,9 @@
     # post-conditions-end
     # impl-start
     if tk != 0.0:
-        # Form the two unit-interval conditional ratios FIRST; each is
-        # representable (<= 1 <= m), so neither operand fed to the root, nor the
-        # final product, can overflow the domain. The cross product of the two
-        # marginals is never formed. (A concordant pair forces both marginals
-        # strictly positive, since each marginal dominates the concordant count.)
         r_p = ratio(tk, pk, m)
         r_q = ratio(tk, qk, m)
-        result = mul(root(r_p, m), root(r_q, m))
+        result = mul(r_p, r_q)
     else:
         result = 0.0
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-10844.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A pair-counting similarity index between two clusterings is computed from
  three non-negative integer pair-counts derived from a contingency table:

    * `tk` — the number of concordant pairs (pairs grouped together in BOTH
      clusterings),
    * `pk` — the number of pairs grouped together in the first clustering,
    * `qk` — the number of pairs grouped together in the second clustering.

  Structurally a concordant pair is also counted by each marginal, so
  `0 <= tk <= pk` and `0 <= tk <= qk`; both marginals are positive whenever
  there is any concordant pair.

  The index is the geometric mean of the two conditional concordance ratios:
  it equals `sqrt(tk / pk) * sqrt(tk / qk)` when there is at least one
  concordant pair, and is `0` when there is none. Because each conditional
  ratio lies in the unit interval, the index is a similarity that always lies
  in `[0, 1]`; it must be a finite, well-defined number for EVERY admissible
  input, including the large-count regime where the two marginals are each
  enormous.

  The arithmetic that produces the index must stay within the representable
  range of the working numeric domain: every quantity formed while evaluating
  it — in particular every product, and every value handed to the square-root
  operation — must be representable (no greater than the domain's maximum
  magnitude `m`). Each marginal on its own is representable; the index must be
  obtained WITHOUT first forming the cross product of the two marginals, since
  that cross product can exceed the representable range even when each marginal
  does not. Forming the two unit-interval conditional ratios first keeps every
  intermediate representable and the result finite.

The pair-counts and the index are interpreted real numbers (verified with
`--float-encoding=real`) because the behaviour at stake is a real-valued
numeric computation that the tests probe to floating tolerance, and the
representability bound `m` models the finite numeric domain in which it runs.
The three numeric operations the computation uses — division, square root and
multiplication — are the unchanged numeric callees; they are axiomatized with
the weakest sufficient contracts (their true bounds plus the representability
precondition that gates an overflow value out of the domain), and validated
against the real operations out-of-band by axiom_check.py (G-AX). The
square-root's representability precondition is what forces an overflow-free
evaluation order.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def ratio(a: float, b: float, m: float) -> float:
    """Real division `a / b` of a non-negative numerator by a strictly positive
    representable denominator that dominates it (`0 <= a <= b <= m`). The
    quotient is then a real in the unit interval. The unchanged numeric division
    callee; provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(b > 0.0)
    Requires(a >= 0.0)
    Requires(a <= b)
    Requires(b <= m)
    Ensures(Result() == a / b)
    Ensures(Result() >= 0.0)
    Ensures(Result() <= 1.0)

@Pure
@ContractOnly
def root(x: float, m: float) -> float:
    """Non-negative square root of a representable non-negative real (the
    unchanged numeric square-root callee). Defined only on a value that is
    itself representable in the working domain (`0 <= x <= m`): a value that has
    already overflowed the domain cannot be fed to it. Returns a non-negative
    real, and a real in the unit interval when the argument is in the unit
    interval. Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(x >= 0.0)
    Requires(x <= m)
    Ensures(Result() >= 0.0)
    Ensures(Implies(x <= 1.0, Result() <= 1.0))

@Pure
@ContractOnly
def mul(x: float, y: float) -> float:
    """Real multiplication `x * y` of two unit-interval reals; the product is
    then itself in the unit interval. The unchanged numeric multiplication
    callee; provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(x >= 0.0 and x <= 1.0)
    Requires(y >= 0.0 and y <= 1.0)
    Ensures(Result() == x * y)
    Ensures(Result() >= 0.0)
    Ensures(Result() <= 1.0)
# axioms-end

# pure-start
# (no pure helpers needed — the index is the spelled-out arithmetic below)
# pure-end

def pair_similarity_index(tk: float, pk: float, qk: float, m: float) -> float:
    # pre-conditions-start
    # The representable bound is a genuine positive magnitude, large enough that
    # each marginal on its own is representable (the marginals are widened to a
    # domain that holds them) but NOT large enough to be assumed to hold their
    # cross product.
    Requires(m >= 1.0)
    # The pair-counts are non-negative reals and each marginal is representable.
    Requires(tk >= 0.0)
    Requires(pk >= 0.0 and pk <= m)
    Requires(qk >= 0.0 and qk <= m)
    # Structural facts of the contingency counting: a concordant pair is counted
    # by each marginal, so a concordant pair forces both marginals positive and
    # each conditional ratio into the unit interval.
    Requires(tk <= pk)
    Requires(tk <= qk)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # With at least one concordant pair the index is the geometric mean of the
    # two conditional concordance ratios.
    Ensures(Implies(tk > 0.0,
                    Result() == mul(root(ratio(tk, pk, m), m),
                                    root(ratio(tk, qk, m), m))))
    # With no concordant pair the index is exactly zero.
    Ensures(Implies(tk == 0.0, Result() == 0.0))
    # The index is a finite similarity in the unit interval for EVERY admissible
    # input — including the large-count regime — never an out-of-range or
    # ill-defined value.
    Ensures(Result() >= 0.0)
    Ensures(Result() <= 1.0)
    # post-conditions-end
    # impl-start
    if tk != 0.0:
        # Form the two unit-interval conditional ratios FIRST; each is
        # representable (<= 1 <= m), so neither operand fed to the root, nor the
        # final product, can overflow the domain. The cross product of the two
        # marginals is never formed. (A concordant pair forces both marginals
        # strictly positive, since each marginal dominates the concordant count.)
        r_p = ratio(tk, pk, m)
        r_q = ratio(tk, qk, m)
        result = mul(root(r_p, m), root(r_q, m))
    else:
        result = 0.0
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of scikit-learn__scikit-learn-10844 nagini bundle. VERDICT: SOUND. 17 same-spec attacks run (all confirmed byte-identical spec via `adversary same-spec`); 3 came back CANDIDATE and ALL THREE had their faithful refined patch materialized and EXECUTED through the official harness (run_resolve) -- all RESOLVED=True, so no verify->wrong-patch gap was found.

**POSITIVE CONTROL:** pos_control.py (bundle model.py verbatim, byte-identical by diff) -- `bash scripts/nagini_verify.sh pos_control.py --float-encoding=real` => Verification successful, EXIT=0 (8.47s). NOTE: my first run WITHOUT --float-encoding=real failed at axioms line 66 ('precondition of (a / b) might not hold'); the encoding is mandatory and the adversary CLI supplies it from meta.json automatically. Direct nagini_verify.sh calls must pass it explicitly or the control spuriously fails.

VACUITY CONTROL (essential -- without it every rejection below is void): atk_11_vacuity.py = correct impl + Assert(False). `adversary weakness` => NOT-A-COUNTEREXAMPLE (EXIT=2, does not verify). The impl region is genuinely reachable, so the rejections are real proof obligations, not an infeasible-path artifact.

PREPATCH REPRODUCED (true): atk_1_prepatch.py (bundle model_prepatch.py) => NOT-A-COUNTEREXAMPLE (EXIT=2). Exact error: `atk_1_prepatch.py:148:17: The precondition of function root might not hold. Assertion (x <= m) might not hold.` This is EXACTLY the discriminator refinement.md claims (root's representability gate on prod = `pk*qk`), so G-DIFF's stated mechanism is confirmed by execution, not assertion.

### THE THREE CANDIDATES AND THEIR EXECUTED RESOLVE RESULTS (mandatory step)
1. atk_6_boundary.py (guard rewritten `if tk > 0.0:` instead of `tk != 0.0`, with Assert(tk == 0.0) in the else). `adversary weakness` => CANDIDATE (verifies, 12.8s). Faithful patch patch_atk6.diff (gold hunk with `if tk > 0.` as the ternary guard). run_resolve => RESOLVED=True. Not a break: tk >= 0 is a precondition (and a true fact of the contingency counting, pk/qk marginals dominate tk), so tk > 0 and tk != 0 are extensionally identical on the admissible domain; the harness agrees.
2. atk_10_swap.py (mul operands swapped: root(r_q) * root(r_p)). => CANDIDATE (verifies, 12.5s). Faithful patch patch_atk10.diff (`np.sqrt(tk / qk) * np.sqrt(tk / pk)`). run_resolve => RESOLVED=True. Not a break: real multiplication commutes, and IEEE multiplication is commutative too (exactly, not just to tolerance), so the swap is bit-identical.
3. atk_7_echo.py (ungrounded-oracle echo: impl is literally the postcondition term `mul(root(ratio(tk,pk,m),m), root(ratio(tk,qk,m),m))`). => CANDIDATE (verifies, 14.8s). Faithful patch = the gold patch verbatim (diff against bundle patch.diff: IDENTICAL-TO-GOLD). run_resolve => RESOLVED=True, DETAIL=resolved. The echo lane is not a defect here: because the axioms are the real /, sqrt, * and the postcondition names exactly the gold arithmetic, the echo's refinement IS the gold patch. There is no axiom about the function under change itself, so the echo cannot launder a wrong value.

#### THE 14 REJECTED ATTACKS (spec did its job), with exact errors
The interesting structural point: the postcondition pins Result() EXACTLY (`Result() == mul(root(ratio(tk,pk,m),m), root(ratio(tk,qk,m),m))`) while `root` is OPAQUE (bounds only, no exact value). So a verifying impl must feed root arguments PROVABLY EQUAL IN REALS to tk/pk and tk/qk. That is what kills the whole overflow family:
- atk_2_sq_both.py (r_p=(`tk*pk`)/(`pk*pk`), r_q=(`tk*qk`)/(`qk*qk`) -- real-equal to tk/pk,tk/qk but int64 `pk*pk` overflows) => EXIT=2. Error: `Assert might fail. Assertion ((pk * pk) > 0.0) might not hold.`
- atk_2b_sq_noassert.py (same, scaffolding asserts removed -- the strongest overflow breaker attempt) => EXIT=2. Error: `The precondition of ((tk * pk) / (pk * pk)) might not hold.` Raw `/` IS gated (divisor-nonzero) and the nonlinear positivity `pk*pk` > 0 is not derivable from pk >= tk > 0. This is the load-bearing rejection.
- atk_3_cross.py (cross-product denominator prod=`pk*qk` on both sides) => EXIT=2.
- atk_4_partial.py (PARTIAL-DOMAIN: overflow-prone order only when pk > qk, correct order otherwise) => EXIT=2. A partial-domain wrong impl is rejected on its wrong branch.
- atk_5_sq_one.py (minimal: only the FIRST ratio squared-scaled) => EXIT=2. Error: `Assertion ((pk * pk) > 0.0) might not hold.`
- atk_13_cross_hint.py (case-split hints handing Z3 nonlinear positivity of prod) => EXIT=2. Error: `Assertion (r_p == (tk / pk)) might not hold.`
- atk_15_const_scale.py (constant-scaled (`tk*2`)/(`pk*2`), linearly-provable denominator positivity) => EXIT=2. Error: `Assertion (r_p == (tk / pk)) might not hold.` Even with a provably-positive scaled denominator, real-equality to tk/pk is not derivable, so the exact postcondition blocks it.
I verified OUT-OF-BAND (numpy int64, F2P labels) that these refinements really are wrong: with tk=3003497866, pk=5152663196, qk=3294371982, (`tk*pk`)/(`pk*pk`) wraps to -0.36661 and the result becomes nan -- i.e. had any of them verified it WOULD have been a genuine break (assert_all_finite fails). They were rejected, so the spec is strong exactly where it needs to be.
- atk_14_rawdiv.py (raw `tk / pk` bypassing the ratio axiom) => EXIT=2. Error: `Assertion (r_p <= 1.0) might not hold.` Raw division is uninterpreted for bounds, so the axiom is the only way to get the unit-interval fact -- the ratio axiom is genuinely consumed, not decorative.
- atk_16_drop_qk.py (WRONG VALUE: drops qk, returns root(tk/pk) -- finite and in [0,1], so the range postconditions alone would accept it) => EXIT=2. Only the exact clause rejects it; good, it is there.
- atk_17_unrooted.py (WRONG VALUE: un-rooted (tk/pk)*(tk/qk)) => EXIT=2.
- atk_8_m_ratio.py (A-LEG: ratio(tk,pk,pk) -- different representability bound) => EXIT=2. Error: `Postcondition ... Result() == mul(root(ratio(tk,pk,m),m), ...) might not hold.`
- atk_9_m_root.py (A-LEG: root(r_p, 1.0) -- a legal bound since r_p <= 1) => EXIT=2, same postcondition error. IMPORTANT strictness finding: root/ratio are uninterpreted in BOTH arguments, so the `m` argument is load-bearing in the postcondition term. An impl cannot silently retune the domain bound -- the representability gate that rejects the prepatch cannot be evaded by passing a smaller m.

#### refinement.md AUDIT (the A legs + model<->patch correspondence)
Leg tags: 2 R + 3 A-consumed + 3 I = 8 legs, ALL classified; NO kind-3 (the single 'kind-3' grep hit is the section heading asserting their absence). meta.json deep_model_references == [] which is CONSISTENT: the doc claims zero A-reference legs, so there is no deep-model reference whose correspondence could drift.
A-leg correspondence to the REAL callees, checked by execution on the exact argument tuples the impl feeds (incl. the F2P regime and the P2P small cases):
- step 5 ratio <-> real `/`: ratio(3003497866, 5152663196) = 0.5829020356563589, ratio(tk,qk) = 0.911705746166706, plus (4,12),(4,6),(1,4),(0,1) -- Ensures (Result()==a/b, 0<=Result()<=1) hold on every one.
- step 6 root <-> numpy.sqrt: sqrt(0.58290..) and sqrt(0.91170..) non-negative and unit-interval-preserved; np.sqrt == math.sqrt exactly on all probed points (the axiom is stated for numpy.sqrt and checked with math.sqrt in axiom_check.py -- that substitution is sound here). Gate load-bearing: `pk*qk` = 1.697479e19 > m = 9.223372e18, and the int64-wrapped np.sqrt(`pk*qk`) is literally nan -- the modeled precondition failure and the real-world non-finiteness coincide.
- step 7 mul <-> real `*`: mul(0.76348..,0.95483..) = 0.7289959776021899 == the gold patch's value on the F2P workload; Ensures hold.
Steps 1-2 (R): int counts -> interpreted reals, and .astype(np.int64) -> per-marginal `<= m`. The deliberate omission of `pk*qk <= m` is the crux and is correct -- I confirmed pk,qk <= INT64_MAX while `pk*qk` > INT64_MAX on the real failing-test labels. Steps 3,4,8 (I) are the same concrete inequalities/guard/return in both worlds.
Value-preservation cross-check: gold `np.sqrt(tk/pk)*np.sqrt(tk/qk)` = 0.7289959776021899 (finite, in [0,1]) on F2P; matches the model's impl term under the axioms.

**VERDICT COVERAGE:** no timeouts and no crashes -- every attack reached a real verifier verdict and all 3 needed resolve runs completed, so no leg of this audit is INCONCLUSIVE.

RESIDUAL RISK (advisory, not a break): the admitted variation is exactly the extensional-equivalence class of the gold line (guard tk>0 vs tk!=0 under tk>=0; commuted product). Both were executed against the official harness and resolved. The spec's exact postcondition + the opaque `root` + the `<= m` gate on root together close the overflow-reordering family, which is the entire behavioural content of this fix.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch.py`, `atk_2_sq_both.py`, `atk_2b_sq_noassert.py`, `atk_3_cross.py`, `atk_4_partial.py`, `atk_5_sq_one.py`, `atk_8_m_ratio.py`, `atk_9_m_root.py`, `atk_11_vacuity.py`, `atk_13_cross_hint.py`, `atk_14_rawdiv.py`, `atk_15_const_scale.py`, `atk_16_drop_qk.py`, `atk_17_unrooted.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6_boundary.py`, `atk_7_echo.py`, `atk_10_swap.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_sq_both.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2b_sq_noassert.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_cross.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_partial.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5_sq_one.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6_boundary.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_7_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_8_m_ratio.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_9_m_root.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10_swap.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 12 — `atk_11_vacuity.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_cross_hint.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_rawdiv.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_const_scale.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_drop_qk.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17_unrooted.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-10844.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A pair-counting similarity index between two clusterings is computed from
  three non-negative integer pair-counts derived from a contingency table:

    * `tk` — the number of concordant pairs (pairs grouped together in BOTH
      clusterings),
    * `pk` — the number of pairs grouped together in the first clustering,
    * `qk` — the number of pairs grouped together in the second clustering.

  Structurally a concordant pair is also counted by each marginal, so
  `0 <= tk <= pk` and `0 <= tk <= qk`; both marginals are positive whenever
  there is any concordant pair.

  The index is the geometric mean of the two conditional concordance ratios:
  it equals `sqrt(tk / pk) * sqrt(tk / qk)` when there is at least one
  concordant pair, and is `0` when there is none. Because each conditional
  ratio lies in the unit interval, the index is a similarity that always lies
  in `[0, 1]`; it must be a finite, well-defined number for EVERY admissible
  input, including the large-count regime where the two marginals are each
  enormous.

  The arithmetic that produces the index must stay within the representable
  range of the working numeric domain: every quantity formed while evaluating
  it — in particular every product, and every value handed to the square-root
  operation — must be representable (no greater than the domain's maximum
  magnitude `m`). Each marginal on its own is representable; the index must be
  obtained WITHOUT first forming the cross product of the two marginals, since
  that cross product can exceed the representable range even when each marginal
  does not. Forming the two unit-interval conditional ratios first keeps every
  intermediate representable and the result finite.

The pair-counts and the index are interpreted real numbers (verified with
`--float-encoding=real`) because the behaviour at stake is a real-valued
numeric computation that the tests probe to floating tolerance, and the
representability bound `m` models the finite numeric domain in which it runs.
The three numeric operations the computation uses — division, square root and
multiplication — are the unchanged numeric callees; they are axiomatized with
the weakest sufficient contracts (their true bounds plus the representability
precondition that gates an overflow value out of the domain), and validated
against the real operations out-of-band by axiom_check.py (G-AX). The
square-root's representability precondition is what forces an overflow-free
evaluation order.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def ratio(a: float, b: float, m: float) -> float:
    """Real division `a / b` of a non-negative numerator by a strictly positive
    representable denominator that dominates it (`0 <= a <= b <= m`). The
    quotient is then a real in the unit interval. The unchanged numeric division
    callee; provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(b > 0.0)
    Requires(a >= 0.0)
    Requires(a <= b)
    Requires(b <= m)
    Ensures(Result() == a / b)
    Ensures(Result() >= 0.0)
    Ensures(Result() <= 1.0)

@Pure
@ContractOnly
def root(x: float, m: float) -> float:
    """Non-negative square root of a representable non-negative real (the
    unchanged numeric square-root callee). Defined only on a value that is
    itself representable in the working domain (`0 <= x <= m`): a value that has
    already overflowed the domain cannot be fed to it. Returns a non-negative
    real, and a real in the unit interval when the argument is in the unit
    interval. Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(x >= 0.0)
    Requires(x <= m)
    Ensures(Result() >= 0.0)
    Ensures(Implies(x <= 1.0, Result() <= 1.0))

@Pure
@ContractOnly
def mul(x: float, y: float) -> float:
    """Real multiplication `x * y` of two unit-interval reals; the product is
    then itself in the unit interval. The unchanged numeric multiplication
    callee; provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(x >= 0.0 and x <= 1.0)
    Requires(y >= 0.0 and y <= 1.0)
    Ensures(Result() == x * y)
    Ensures(Result() >= 0.0)
    Ensures(Result() <= 1.0)
# axioms-end

# pure-start
# (no pure helpers needed — the index is the spelled-out arithmetic below)
# pure-end

def pair_similarity_index(tk: float, pk: float, qk: float, m: float) -> float:
    # pre-conditions-start
    # The representable bound is a genuine positive magnitude, large enough that
    # each marginal on its own is representable (the marginals are widened to a
    # domain that holds them) but NOT large enough to be assumed to hold their
    # cross product.
    Requires(m >= 1.0)
    # The pair-counts are non-negative reals and each marginal is representable.
    Requires(tk >= 0.0)
    Requires(pk >= 0.0 and pk <= m)
    Requires(qk >= 0.0 and qk <= m)
    # Structural facts of the contingency counting: a concordant pair is counted
    # by each marginal, so a concordant pair forces both marginals positive and
    # each conditional ratio into the unit interval.
    Requires(tk <= pk)
    Requires(tk <= qk)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # With at least one concordant pair the index is the geometric mean of the
    # two conditional concordance ratios.
    Ensures(Implies(tk > 0.0,
                    Result() == mul(root(ratio(tk, pk, m), m),
                                    root(ratio(tk, qk, m), m))))
    # With no concordant pair the index is exactly zero.
    Ensures(Implies(tk == 0.0, Result() == 0.0))
    # The index is a finite similarity in the unit interval for EVERY admissible
    # input — including the large-count regime — never an out-of-range or
    # ill-defined value.
    Ensures(Result() >= 0.0)
    Ensures(Result() <= 1.0)
    # post-conditions-end
    # impl-start
    if tk != 0.0:
        # Form the two unit-interval conditional ratios FIRST; each is
        # representable (<= 1 <= m), so neither operand fed to the root, nor the
        # final product, can overflow the domain. The cross product of the two
        # marginals is never formed. (A concordant pair forces both marginals
        # strictly positive, since each marginal dominates the concordant count.)
        r_p = ratio(tk, pk, m)
        r_q = ratio(tk, qk, m)
        result = mul(root(r_p, m), root(r_q, m))
    else:
        result = 0.0
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of scikit-learn__scikit-learn-10844 nagini bundle. VERDICT: SOUND. 17 same-spec attacks run (all confirmed byte-identical spec via `adversary same-spec`); 3 came back CANDIDATE and ALL THREE had their faithful refined patch materialized and EXECUTED through the official harness (run_resolve) -- all RESOLVED=True, so no verify->wrong-patch gap was found.

**POSITIVE CONTROL:** pos_control.py (bundle model.py verbatim, byte-identical by diff) -- `bash scripts/nagini_verify.sh pos_control.py --float-encoding=real` => Verification successful, EXIT=0 (8.47s). NOTE: my first run WITHOUT --float-encoding=real failed at axioms line 66 ('precondition of (a / b) might not hold'); the encoding is mandatory and the adversary CLI supplies it from meta.json automatically. Direct nagini_verify.sh calls must pass it explicitly or the control spuriously fails.

VACUITY CONTROL (essential -- without it every rejection below is void): atk_11_vacuity.py = correct impl + Assert(False). `adversary weakness` => NOT-A-COUNTEREXAMPLE (EXIT=2, does not verify). The impl region is genuinely reachable, so the rejections are real proof obligations, not an infeasible-path artifact.

PREPATCH REPRODUCED (true): atk_1_prepatch.py (bundle model_prepatch.py) => NOT-A-COUNTEREXAMPLE (EXIT=2). Exact error: `atk_1_prepatch.py:148:17: The precondition of function root might not hold. Assertion (x <= m) might not hold.` This is EXACTLY the discriminator refinement.md claims (root's representability gate on prod = `pk*qk`), so G-DIFF's stated mechanism is confirmed by execution, not assertion.

### THE THREE CANDIDATES AND THEIR EXECUTED RESOLVE RESULTS (mandatory step)
1. atk_6_boundary.py (guard rewritten `if tk > 0.0:` instead of `tk != 0.0`, with Assert(tk == 0.0) in the else). `adversary weakness` => CANDIDATE (verifies, 12.8s). Faithful patch patch_atk6.diff (gold hunk with `if tk > 0.` as the ternary guard). run_resolve => RESOLVED=True. Not a break: tk >= 0 is a precondition (and a true fact of the contingency counting, pk/qk marginals dominate tk), so tk > 0 and tk != 0 are extensionally identical on the admissible domain; the harness agrees.
2. atk_10_swap.py (mul operands swapped: root(r_q) * root(r_p)). => CANDIDATE (verifies, 12.5s). Faithful patch patch_atk10.diff (`np.sqrt(tk / qk) * np.sqrt(tk / pk)`). run_resolve => RESOLVED=True. Not a break: real multiplication commutes, and IEEE multiplication is commutative too (exactly, not just to tolerance), so the swap is bit-identical.
3. atk_7_echo.py (ungrounded-oracle echo: impl is literally the postcondition term `mul(root(ratio(tk,pk,m),m), root(ratio(tk,qk,m),m))`). => CANDIDATE (verifies, 14.8s). Faithful patch = the gold patch verbatim (diff against bundle patch.diff: IDENTICAL-TO-GOLD). run_resolve => RESOLVED=True, DETAIL=resolved. The echo lane is not a defect here: because the axioms are the real /, sqrt, * and the postcondition names exactly the gold arithmetic, the echo's refinement IS the gold patch. There is no axiom about the function under change itself, so the echo cannot launder a wrong value.

#### THE 14 REJECTED ATTACKS (spec did its job), with exact errors
The interesting structural point: the postcondition pins Result() EXACTLY (`Result() == mul(root(ratio(tk,pk,m),m), root(ratio(tk,qk,m),m))`) while `root` is OPAQUE (bounds only, no exact value). So a verifying impl must feed root arguments PROVABLY EQUAL IN REALS to tk/pk and tk/qk. That is what kills the whole overflow family:
- atk_2_sq_both.py (r_p=(`tk*pk`)/(`pk*pk`), r_q=(`tk*qk`)/(`qk*qk`) -- real-equal to tk/pk,tk/qk but int64 `pk*pk` overflows) => EXIT=2. Error: `Assert might fail. Assertion ((pk * pk) > 0.0) might not hold.`
- atk_2b_sq_noassert.py (same, scaffolding asserts removed -- the strongest overflow breaker attempt) => EXIT=2. Error: `The precondition of ((tk * pk) / (pk * pk)) might not hold.` Raw `/` IS gated (divisor-nonzero) and the nonlinear positivity `pk*pk` > 0 is not derivable from pk >= tk > 0. This is the load-bearing rejection.
- atk_3_cross.py (cross-product denominator prod=`pk*qk` on both sides) => EXIT=2.
- atk_4_partial.py (PARTIAL-DOMAIN: overflow-prone order only when pk > qk, correct order otherwise) => EXIT=2. A partial-domain wrong impl is rejected on its wrong branch.
- atk_5_sq_one.py (minimal: only the FIRST ratio squared-scaled) => EXIT=2. Error: `Assertion ((pk * pk) > 0.0) might not hold.`
- atk_13_cross_hint.py (case-split hints handing Z3 nonlinear positivity of prod) => EXIT=2. Error: `Assertion (r_p == (tk / pk)) might not hold.`
- atk_15_const_scale.py (constant-scaled (`tk*2`)/(`pk*2`), linearly-provable denominator positivity) => EXIT=2. Error: `Assertion (r_p == (tk / pk)) might not hold.` Even with a provably-positive scaled denominator, real-equality to tk/pk is not derivable, so the exact postcondition blocks it.
I verified OUT-OF-BAND (numpy int64, F2P labels) that these refinements really are wrong: with tk=3003497866, pk=5152663196, qk=3294371982, (`tk*pk`)/(`pk*pk`) wraps to -0.36661 and the result becomes nan -- i.e. had any of them verified it WOULD have been a genuine break (assert_all_finite fails). They were rejected, so the spec is strong exactly where it needs to be.
- atk_14_rawdiv.py (raw `tk / pk` bypassing the ratio axiom) => EXIT=2. Error: `Assertion (r_p <= 1.0) might not hold.` Raw division is uninterpreted for bounds, so the axiom is the only way to get the unit-interval fact -- the ratio axiom is genuinely consumed, not decorative.
- atk_16_drop_qk.py (WRONG VALUE: drops qk, returns root(tk/pk) -- finite and in [0,1], so the range postconditions alone would accept it) => EXIT=2. Only the exact clause rejects it; good, it is there.
- atk_17_unrooted.py (WRONG VALUE: un-rooted (tk/pk)*(tk/qk)) => EXIT=2.
- atk_8_m_ratio.py (A-LEG: ratio(tk,pk,pk) -- different representability bound) => EXIT=2. Error: `Postcondition ... Result() == mul(root(ratio(tk,pk,m),m), ...) might not hold.`
- atk_9_m_root.py (A-LEG: root(r_p, 1.0) -- a legal bound since r_p <= 1) => EXIT=2, same postcondition error. IMPORTANT strictness finding: root/ratio are uninterpreted in BOTH arguments, so the `m` argument is load-bearing in the postcondition term. An impl cannot silently retune the domain bound -- the representability gate that rejects the prepatch cannot be evaded by passing a smaller m.

#### refinement.md AUDIT (the A legs + model<->patch correspondence)
Leg tags: 2 R + 3 A-consumed + 3 I = 8 legs, ALL classified; NO kind-3 (the single 'kind-3' grep hit is the section heading asserting their absence). meta.json deep_model_references == [] which is CONSISTENT: the doc claims zero A-reference legs, so there is no deep-model reference whose correspondence could drift.
A-leg correspondence to the REAL callees, checked by execution on the exact argument tuples the impl feeds (incl. the F2P regime and the P2P small cases):
- step 5 ratio <-> real `/`: ratio(3003497866, 5152663196) = 0.5829020356563589, ratio(tk,qk) = 0.911705746166706, plus (4,12),(4,6),(1,4),(0,1) -- Ensures (Result()==a/b, 0<=Result()<=1) hold on every one.
- step 6 root <-> numpy.sqrt: sqrt(0.58290..) and sqrt(0.91170..) non-negative and unit-interval-preserved; np.sqrt == math.sqrt exactly on all probed points (the axiom is stated for numpy.sqrt and checked with math.sqrt in axiom_check.py -- that substitution is sound here). Gate load-bearing: `pk*qk` = 1.697479e19 > m = 9.223372e18, and the int64-wrapped np.sqrt(`pk*qk`) is literally nan -- the modeled precondition failure and the real-world non-finiteness coincide.
- step 7 mul <-> real `*`: mul(0.76348..,0.95483..) = 0.7289959776021899 == the gold patch's value on the F2P workload; Ensures hold.
Steps 1-2 (R): int counts -> interpreted reals, and .astype(np.int64) -> per-marginal `<= m`. The deliberate omission of `pk*qk <= m` is the crux and is correct -- I confirmed pk,qk <= INT64_MAX while `pk*qk` > INT64_MAX on the real failing-test labels. Steps 3,4,8 (I) are the same concrete inequalities/guard/return in both worlds.
Value-preservation cross-check: gold `np.sqrt(tk/pk)*np.sqrt(tk/qk)` = 0.7289959776021899 (finite, in [0,1]) on F2P; matches the model's impl term under the axioms.

**VERDICT COVERAGE:** no timeouts and no crashes -- every attack reached a real verifier verdict and all 3 needed resolve runs completed, so no leg of this audit is INCONCLUSIVE.

RESIDUAL RISK (advisory, not a break): the admitted variation is exactly the extensional-equivalence class of the gold line (guard tk>0 vs tk!=0 under tk>=0; commuted product). Both were executed against the official harness and resolved. The spec's exact postcondition + the opaque `root` + the `<= m` gate on root together close the overflow-reordering family, which is the entire behavioural content of this fix.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE USED: worktree at base_commit 97523985b3 with patch.diff APPLIED, plus the official SWE-bench container swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-10844 (/testbed, gold patch applied, numpy 1.19.2 / py3.6.13). Confirmed the loaded tail is `c = contingency_matrix(...).astype(np.int64)` + `return np.sqrt(tk / pk) * np.sqrt(tk / qk) if tk != 0. else 0.` (supervised.py:855-859). Base commit used only for the untouched numeric callees the axioms model (/, np.sqrt, *).

**MODELED FUNCTION:** pair_similarity_index(tk, pk, qk, m) <-> the score-assembly tail of fowlkes_mallows_score. Carrier: int64 counts -> interpreted reals (--float-encoding=real, pinned in meta.json float_encoding=real); m = float(np.iinfo(np.int64).max), the domain the .astype(np.int64) widening puts the marginals in.

### Machine-checked facts
1. Spec-region integrity: `adversary same-spec nagini scikit-learn__scikit-learn-10844` on a byte-copy of model.py -> exit 0, "SAME - attack shares the bundle's exact specification". Spec region is the one I reasoned about.
2. Verifier (pinned, WITH the meta.json-pinned flag): `nagini_verify.sh atkF2_model.py --float-encoding=real` -> "Verification successful" (9.79s). (Note: omitting --float-encoding=real spuriously fails at ratio's b>0.0 - that is my harness error, not a spec defect; the flag is recorded in meta.json.)
3. G-DIFF is live: model_prepatch.py (same spec byte-identical, pre-patch product-first order) -> "Verification failed: The precondition of function root might not hold. Assertion (x <= m) might not hold." at the `root(prod, m)` call. The spec genuinely rejects the buggy evaluation order at exactly the discriminating clause, and rejects it for BOTH failure modes (didn't widen / widened but didn't reorder), since pk<=m and qk<=m do not entail `pk*qk`<=m.
4. **G-AX:** axiom_check.py -> exit 0, 29 boundary + 600000 fuzz inputs sound; overflow discriminator confirmed.
5. **G-CONF:** conformance_check.py run inside the patched container -> exit 0, status=pass, 106296 Requires-satisfying inputs (14 boundary + 66282 exhaustive n<=4 + 40000 fuzz, seed 10844), 0 disagreements, branches tk==0: 44854 / tk!=0: 61442, large-count regime (`pk*qk`>m): 3. Negative control refuted all four wrong tails including prepatch-cross-product-first - the check can fail.
6. Repo test suite on the patched testbed: 17 passed (all P2P green, incl. test_fowlkes_mallows_score_properties). The F2P test name is absent at base_commit (it arrives with test_patch), as expected.

### MY OWN INDEPENDENT DIVERGENCE HUNT (not the bundle's scripts)
A. Precondition faithfulness (does the spec exclude reachable repo behavior?). Observed tk/pk/qk out of the REAL patched frame via sys.settrace and screened all six preconditions on: exhaustive label pairs n<=4, 30000 draws at n=5..6, 4000 draws up to n=3000 with adversarial cluster counts, giant inputs at n=1e5/3e5/1e6 (perfect / all-split / extreme-skew shapes), the F2P workload and its x1/x2/x3/x5/x10/x30 tilings. ZERO precondition violations, ZERO postcondition violations, ZERO shadow-vs-oracle mismatches.

B. Exotic label domains that could break the structural facts: NaN labels (one-sided, both-sided, mixed), +/-inf labels, negative labels, labels near `2**62`, string labels, bool labels, list inputs, empty, singleton. Every case satisfies 0<=tk<=pk<=m, tk<=qk<=m and lands in [0,1] finite; the only failure is object-dtype labels, where the oracle itself raises TypeError inside np.unique before reaching the modeled tail (out of the modeled region, not a spec defect).

C. The strongest available attack - int64->float64 rounding above `2**53`, where tk<=pk could conceivably round to a ratio >1 and break Ensures(Result()<=1.0). Tested: exhaustive adjacent triples across every binade boundary `2**53`..2**62 (dt in -8..8, dp/dq in 0..16), the exact diagonal tk==pk==qk at `2**e`+/-1 for e=0..62 and at M, M-1, M-2, and 500000 random ultra-close triples with pk in [`2**53`, M]. ZERO results >1.0, ZERO non-finite, max observed exactly 1.0. Also 200000 randomized checks that np.int64(a)/np.int64(b) == float(a)/float(b) for a<=b<`2**62`: 0 mismatches (numpy converts to float64 before dividing, so the model's real-carrier division is the same operation).

D. Full-domain shadow-vs-repo-tail equality on the abstract carrier (bypassing label generation): 400000 uniform triples over the whole admissible box plus 200000 near-1 huge-magnitude triples plus the boundary set incl. (M,M,M), (M-1,M,M), (`2**62`, `2**62`+1, `2**62`+3). ZERO mismatches, ZERO repo postcondition violations.

TOO-STRONG / DRIFT ANALYSIS (each candidate checked, none holds)
- Requires(pk <= m, qk <= m): NOT an over-restriction. pk,qk <= n^2 - n, and I solved for the smallest n making n^2-n > INT64_MAX: n = 3037000501, i.e. a 24.3 GB int64 label array per side. For every physically constructible input the bound holds, so the precondition excludes no reachable behavior. Crucially the spec does NOT assume `pk*qk` <= m - I confirmed the cross product overflows at n ~ 72485 (`pk*qk` = 2.76e19 > 9.22e18), well inside reachable sizes, which is why the prepatch fails. The bound is placed exactly where the widening puts it and nowhere stronger.
- Requires(tk <= pk), Requires(tk <= qk): genuine counting identities (sum of squares over a partition refinement <= square of the marginal sums). Empirically never violated across ~140k real repo observations, including NaN/inf/skew/giant shapes.
- Ensures(Result() <= 1.0): I verified the real function actually attains but never exceeds 1.0 (max observed exactly 1.0 on tk==pk==qk), so the postcondition is tight, not stronger than reality.
- Ensures(Implies(tk == 0.0, Result() == 0.0)): matches the repo's literal `else 0.` and holds on 44854 real tk==0 observations.
- root axiom carries only bounds (no exact value) - the weakest sufficient contract; ratio/mul carry exact value + bound, all three validated against the real /, math.sqrt/np.sqrt, * by G-AX.
- The `m` abstraction is honest about the wrap: I confirmed the real overflow is int64 wraparound (np.int64(5152663196)*np.int64(3294371982) = -1471954808124577144, so np.sqrt -> nan, tk/nan -> nan). Modeling that as a representability precondition on root rather than as signed wrap is a sound abstraction: it makes the pre-patch order unverifiable (the actual bug) without weakening anything the post-patch impl needs.
- Axiom-check magnitudes are real, not invented: I recomputed tk,pk,qk = 3003497866, 5152663196, 3294371982 from the actual F2P labels and reproduced prepatch = nan vs patched = 0.7289959776021899 = the real score.

**CONCLUSION:** no diverging input exists after ~1.4M targeted probes against the real patched callee, spanning the full admissible carrier box, the >`2**53` rounding regime, the overflow regime, and exotic label dtypes. The spec is neither too strong (no reachable input is excluded by a precondition) nor drifted (the postconditions are tight and the impl region matches the patched line exactly, bit-for-bit under exact float equality). All five gates I could run independently reproduce green, and the G-DIFF control fails for the right reason. I have no faithfulness break to report.

**REFERENCE USED:** worktree at base_commit 97523985b3 with patch.diff APPLIED, plus the official SWE-bench container swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-10844 (/testbed, gold patch applied, numpy 1.19.2 / py3.6.13). Confirmed the loaded tail is `c = contingency_matrix(...).astype(np.int64)` + `return np.sqrt(tk / pk) * np.sqrt(tk / qk) if tk != 0. else 0.` (supervised.py:855-859). Base commit used only for the untouched numeric callees the axioms model (/, np.sqrt, *).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Instance scikit-learn__scikit-learn-10844 (nagini). Judged the CONSUMER SPEC VIEW (markers.spec_view of model.py, i.e. module docstring + axioms + pure + pre/post regions, impl elided) against the solver-visible problem_statement ONLY, never hints_text.

### WHAT I CHECKED (facts, not impressions)

1. Spec view derived with the real projection, not by eye: swebench_unified.markers.spec_view(model.py, get_backend('nagini')). Impl region collapses to `...  # implementation elided`; lines 1-138 (docstring, ratio/root/mul axioms, pre/post) are what the consumer sees. Cached to a mktemp dir. A first attempt wrote a generically named specview.py that was overwritten before it was read, so I re-derived the projection under a per-instance name; the token counts below are from that copy.

2. Spec-region machinery exercised: copied model.py, changed ONLY the impl region (inlined r_p/r_q into one mul(root(...),root(...)) expression), ran `adversary same-spec nagini ... atk.py` -> "SAME — attack shares the bundle's exact specification", exit 0. Confirms the spec/impl boundary I judged is the boundary the harness enforces.

3. Mechanical screen, run directly: leakage.screen(model.py, ...) -> passed=True, hard_failures=[], warnings=[]. Matches meta.json gates.G-LEAK = pass "spec view clean", sources digest 93faa8a7..., mode strict. relaxed_leakage is None and no RELAXED_LEAKAGE.md exists, so this is a genuine strict pass, not an honored relaxation (leak.py would have reported "relaxed").

4. Lexical disclosure audit of the spec view: 'int64' 0, 'int32' 0, 'astype' 0, 'np.' 0, 'numpy' 0, 'fowlkes' 0, 'mallows' 0, 'supervised.py' 0, 'contingency_matrix' 0, '859'/'855' 0, 'dtype' 0. No diff markers ('@@', 'diff --git', '+++ ', '--- ') present. No gold-diff line reproduced. No spec-view identifier echoes a patched repo symbol (the modeled function is named pair_similarity_index / ratio / root / mul; the gold touches fowlkes_mallows_score).

5. Fix-narration vocabulary: regex over the full `_NARRATION` list (bug/buggy/fix/fixed/fixes/patch/patched/pre-patch/prepatch/post-patch/regression/previously/incorrectly/wrong/broken/off-by-one) matched NOTHING in the spec view. Notably the leak-narrating prose that DOES exist in this bundle lives in refinement.md ("Gold hunk:", the +/- diff, "the pre-patch order ... unverifiable", "1.7e19 > 9.2e18") and mapping.md — neither is part of the consumer spec view. That separation is the whole point and it holds here.

6. The one line worth attacking, examined and cleared. Spec-view line 110-112: "# each marginal on its own is representable (the marginals are widened to a / # domain that holds them) but NOT large enough to be assumed to hold their / # cross product." and docstring lines 29-31: "Each marginal on its own is representable; the index must be obtained WITHOUT first forming the cross product of the two marginals". This is the closest thing to a leak, so I tested it against the PS rather than guessing:
   - The PS quotes the PRE-patch line verbatim: `return tk / np.sqrt(pk * qk) if tk != 0. else 0.` (confirmed by substring test).
   - The PS quotes the GOLD replacement verbatim in its own "#### Fix" section: "I propose to use np.sqrt(tk / pk) * np.sqrt(tk / qk) instead, which gives same result and ensuring not bypassing int32" (confirmed by substring test).
   - The PS names the patched file and line: "sklearn\\metrics\\cluster\\supervised.py:859" (confirmed).
   - The PS names the diagnosis: "RuntimeWarning: overflow encountered in int_scalars when (pk * qk) is bigger than `2**32`", and the int32 width framing twice (confirmed).
   So "don't form the cross product `pk*qk`; form the two ratios first" is FULLY PUBLIC — the reporter literally proposed the gold reorder. The spec view states strictly LESS about the edit than the PS does: it gives the abstract representability contract with no dtype, no numpy, no file, no function, no line number. A solver handed the PS already has the exact replacement expression; the spec view adds no localization the PS lacks.

7. Checked the hints_text-only channel specifically, since that is the documented failure mode ("narrating the fix in the docstring using hints_text-only vocabulary"). 'int64' and 'astype' appear in hints_text but NOT in the PS — and the spec view contains NEITHER (counts 0/0 from step 4). So the non-public half of the gold (`.astype(np.int64)`) is not disclosed by identifier or by name anywhere in the consumer view. The word "widened" appears exactly once, in a parenthetical, without any width/dtype/type name; and even that notion is publicly implied by the PS's own two mentions of "bypassing the int32 limit".

8. Reconstruction-power sanity check in the real repo (worktree at base_commit 97523985b3,, bundle untouched): recomputed the F2P labels -> tk=3003497866, pk=5152663196, qk=3294371982; `pk*qk`=1.697e19 > INT64_MAX 9.223e18, and the pre-patch order raises "overflow encountered in scalar multiply" while sqrt(tk/pk)*sqrt(tk/qk)=0.72899... Also confirmed contingency_matrix's `dtype=np.int` is int64 on this Linux platform, so the gold's `.astype(np.int64)` is a NO-OP here and the load-bearing half of the gold is exactly the REORDER — the half the PS states verbatim. The spec view therefore cannot be leaking a discriminator the PS withholds; the discriminator it encodes (root's `Requires(x <= m)` representability gate) is the public one.

**CONCLUSION:** no gold-diff line quoted, no patched path/function/line named, no identifier echoing a patched symbol, no bug->fix narration, and no hints_text-only vocabulary. Everything the spec view reveals about the edit is a strict subset of what the public problem_statement already spells out (which in this instance includes the gold replacement expression itself). Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
