# P2 adversarial audit — sympy__sympy-17630

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -110,28 +110,17 @@
                     == (num_scalars > 0 and not has_explicit_matrix)))
     # post-conditions-end
     # impl-start
+
     if num_scalars > 0:
         if not is_sum:
-            # Product with a scalar coefficient: absorb it into an explicit
-            # matrix factor when one is present, leaving only matrix factors.
             absorbed = has_explicit_matrix  # type: bool
             if absorbed:
                 return Combo(num_matrices, False)
-            # No explicit matrix to absorb into: the scalar coefficient leads
-            # the matrix-domain product.
             return Combo(num_matrices, True)
         else:
-            # Sum with a genuine scalar term: the scalar is held apart; the
-            # matrix-domain sum is formed from the matrix terms alone.
             return Combo(num_matrices, False)
-    # No genuine scalar term remains.
     if is_sum:
-        # Build the matrix-domain sum from the matrix terms alone; do NOT
-        # collapse the empty scalar collection into the additive identity and
-        # inject it as an argument.
-        return Combo(num_matrices, False)
-    # Product with no scalar term: the matrix-domain product is the matrix
-    # factors alone (the empty scalar collection collapses to the multiplicative
-    # identity, which the product constructor drops — no scalar argument).
+        # PREPATCH BUG: additive identity injected into the matrix-domain sum
+        return Combo(num_matrices, True)
     return Combo(num_matrices, False)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -110,28 +110,15 @@
                     == (num_scalars > 0 and not has_explicit_matrix)))
     # post-conditions-end
     # impl-start
+
     if num_scalars > 0:
         if not is_sum:
-            # Product with a scalar coefficient: absorb it into an explicit
-            # matrix factor when one is present, leaving only matrix factors.
             absorbed = has_explicit_matrix  # type: bool
             if absorbed:
                 return Combo(num_matrices, False)
-            # No explicit matrix to absorb into: the scalar coefficient leads
-            # the matrix-domain product.
             return Combo(num_matrices, True)
         else:
-            # Sum with a genuine scalar term: the scalar is held apart; the
-            # matrix-domain sum is formed from the matrix terms alone.
             return Combo(num_matrices, False)
-    # No genuine scalar term remains.
-    if is_sum:
-        # Build the matrix-domain sum from the matrix terms alone; do NOT
-        # collapse the empty scalar collection into the additive identity and
-        # inject it as an argument.
-        return Combo(num_matrices, False)
-    # Product with no scalar term: the matrix-domain product is the matrix
-    # factors alone (the empty scalar collection collapses to the multiplicative
-    # identity, which the product constructor drops — no scalar argument).
-    return Combo(num_matrices, False)
+    # partial-domain: ignores is_sum, always claims a scalar arg
+    return Combo(num_matrices, True)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -110,28 +110,17 @@
                     == (num_scalars > 0 and not has_explicit_matrix)))
     # post-conditions-end
     # impl-start
+
     if num_scalars > 0:
         if not is_sum:
-            # Product with a scalar coefficient: absorb it into an explicit
-            # matrix factor when one is present, leaving only matrix factors.
             absorbed = has_explicit_matrix  # type: bool
             if absorbed:
                 return Combo(num_matrices, False)
-            # No explicit matrix to absorb into: the scalar coefficient leads
-            # the matrix-domain product.
             return Combo(num_matrices, True)
         else:
-            # Sum with a genuine scalar term: the scalar is held apart; the
-            # matrix-domain sum is formed from the matrix terms alone.
             return Combo(num_matrices, False)
-    # No genuine scalar term remains.
     if is_sum:
-        # Build the matrix-domain sum from the matrix terms alone; do NOT
-        # collapse the empty scalar collection into the additive identity and
-        # inject it as an argument.
-        return Combo(num_matrices, False)
-    # Product with no scalar term: the matrix-domain product is the matrix
-    # factors alone (the empty scalar collection collapses to the multiplicative
-    # identity, which the product constructor drops — no scalar argument).
+        # boundary: off-by-one matrix count
+        return Combo(num_matrices + 1, False)
     return Combo(num_matrices, False)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -110,28 +110,17 @@
                     == (num_scalars > 0 and not has_explicit_matrix)))
     # post-conditions-end
     # impl-start
+
     if num_scalars > 0:
         if not is_sum:
-            # Product with a scalar coefficient: absorb it into an explicit
-            # matrix factor when one is present, leaving only matrix factors.
             absorbed = has_explicit_matrix  # type: bool
             if absorbed:
                 return Combo(num_matrices, False)
-            # No explicit matrix to absorb into: the scalar coefficient leads
-            # the matrix-domain product.
             return Combo(num_matrices, True)
         else:
-            # Sum with a genuine scalar term: the scalar is held apart; the
-            # matrix-domain sum is formed from the matrix terms alone.
             return Combo(num_matrices, False)
-    # No genuine scalar term remains.
     if is_sum:
-        # Build the matrix-domain sum from the matrix terms alone; do NOT
-        # collapse the empty scalar collection into the additive identity and
-        # inject it as an argument.
-        return Combo(num_matrices, False)
-    # Product with no scalar term: the matrix-domain product is the matrix
-    # factors alone (the empty scalar collection collapses to the multiplicative
-    # identity, which the product constructor drops — no scalar argument).
+        while True:
+            pass
     return Combo(num_matrices, False)
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -110,28 +110,7 @@
                     == (num_scalars > 0 and not has_explicit_matrix)))
     # post-conditions-end
     # impl-start
-    if num_scalars > 0:
-        if not is_sum:
-            # Product with a scalar coefficient: absorb it into an explicit
-            # matrix factor when one is present, leaving only matrix factors.
-            absorbed = has_explicit_matrix  # type: bool
-            if absorbed:
-                return Combo(num_matrices, False)
-            # No explicit matrix to absorb into: the scalar coefficient leads
-            # the matrix-domain product.
-            return Combo(num_matrices, True)
-        else:
-            # Sum with a genuine scalar term: the scalar is held apart; the
-            # matrix-domain sum is formed from the matrix terms alone.
-            return Combo(num_matrices, False)
-    # No genuine scalar term remains.
-    if is_sum:
-        # Build the matrix-domain sum from the matrix terms alone; do NOT
-        # collapse the empty scalar collection into the additive identity and
-        # inject it as an argument.
-        return Combo(num_matrices, False)
-    # Product with no scalar term: the matrix-domain product is the matrix
-    # factors alone (the empty scalar collection collapses to the multiplicative
-    # identity, which the product constructor drops — no scalar argument).
-    return Combo(num_matrices, False)
+
+    scalar_present = (not is_sum) and (num_scalars > 0) and (not has_explicit_matrix)  # type: bool
+    return Combo(num_matrices, scalar_present)
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -110,28 +110,11 @@
                     == (num_scalars > 0 and not has_explicit_matrix)))
     # post-conditions-end
     # impl-start
-    if num_scalars > 0:
-        if not is_sum:
-            # Product with a scalar coefficient: absorb it into an explicit
-            # matrix factor when one is present, leaving only matrix factors.
-            absorbed = has_explicit_matrix  # type: bool
-            if absorbed:
-                return Combo(num_matrices, False)
-            # No explicit matrix to absorb into: the scalar coefficient leads
-            # the matrix-domain product.
-            return Combo(num_matrices, True)
-        else:
-            # Sum with a genuine scalar term: the scalar is held apart; the
-            # matrix-domain sum is formed from the matrix terms alone.
-            return Combo(num_matrices, False)
-    # No genuine scalar term remains.
-    if is_sum:
-        # Build the matrix-domain sum from the matrix terms alone; do NOT
-        # collapse the empty scalar collection into the additive identity and
-        # inject it as an argument.
-        return Combo(num_matrices, False)
-    # Product with no scalar term: the matrix-domain product is the matrix
-    # factors alone (the empty scalar collection collapses to the multiplicative
-    # identity, which the product constructor drops — no scalar argument).
-    return Combo(num_matrices, False)
+
+    sp = False  # type: bool
+    if not is_sum:
+        if num_scalars > 0:
+            if not has_explicit_matrix:
+                sp = True
+    return Combo(num_matrices, sp)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -110,28 +110,17 @@
                     == (num_scalars > 0 and not has_explicit_matrix)))
     # post-conditions-end
     # impl-start
+
     if num_scalars > 0:
         if not is_sum:
-            # Product with a scalar coefficient: absorb it into an explicit
-            # matrix factor when one is present, leaving only matrix factors.
             absorbed = has_explicit_matrix  # type: bool
             if absorbed:
                 return Combo(num_matrices, False)
-            # No explicit matrix to absorb into: the scalar coefficient leads
-            # the matrix-domain product.
-            return Combo(num_matrices, True)
+            # WRONG: scalar coefficient leads but we drop the scalar arg
+            return Combo(num_matrices, False)
         else:
-            # Sum with a genuine scalar term: the scalar is held apart; the
-            # matrix-domain sum is formed from the matrix terms alone.
             return Combo(num_matrices, False)
-    # No genuine scalar term remains.
     if is_sum:
-        # Build the matrix-domain sum from the matrix terms alone; do NOT
-        # collapse the empty scalar collection into the additive identity and
-        # inject it as an argument.
         return Combo(num_matrices, False)
-    # Product with no scalar term: the matrix-domain product is the matrix
-    # factors alone (the empty scalar collection collapses to the multiplicative
-    # identity, which the product constructor drops — no scalar argument).
     return Combo(num_matrices, False)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -110,28 +110,10 @@
                     == (num_scalars > 0 and not has_explicit_matrix)))
     # post-conditions-end
     # impl-start
-    if num_scalars > 0:
-        if not is_sum:
-            # Product with a scalar coefficient: absorb it into an explicit
-            # matrix factor when one is present, leaving only matrix factors.
-            absorbed = has_explicit_matrix  # type: bool
-            if absorbed:
-                return Combo(num_matrices, False)
-            # No explicit matrix to absorb into: the scalar coefficient leads
-            # the matrix-domain product.
-            return Combo(num_matrices, True)
-        else:
-            # Sum with a genuine scalar term: the scalar is held apart; the
-            # matrix-domain sum is formed from the matrix terms alone.
-            return Combo(num_matrices, False)
-    # No genuine scalar term remains.
+
     if is_sum:
-        # Build the matrix-domain sum from the matrix terms alone; do NOT
-        # collapse the empty scalar collection into the additive identity and
-        # inject it as an argument.
         return Combo(num_matrices, False)
-    # Product with no scalar term: the matrix-domain product is the matrix
-    # factors alone (the empty scalar collection collapses to the multiplicative
-    # identity, which the product constructor drops — no scalar argument).
+    if num_scalars > 0 and not has_explicit_matrix:
+        return Combo(num_matrices, True)
     return Combo(num_matrices, False)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-17630.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A symbolic combination (a commutative sum, or a product) of terms is
  post-processed for the matrix-expression domain. Its terms are partitioned
  into matrix-valued terms and ordinary scalar terms, and a single combined
  expression is rebuilt for the matrix domain. The result is described only by
  two observable facets: how many matrix terms feed the rebuilt matrix-domain
  combination, and whether the rebuilt matrix-domain combination is fed a
  scalar coefficient term as one of its top-level arguments.

  (1) For a SUM with at least one matrix term, the rebuilt matrix-domain sum is
      formed from the matrix terms ALONE. No scalar coefficient is ever placed
      among its arguments: when the sum has no genuine scalar term, the empty
      collection of scalars must NOT be collapsed into the additive identity and
      injected as an argument. Consequently the rebuilt sum stays a matrix
      expression, so a sum of matrix terms remains in the matrix domain (and an
      all-zero such sum stays a matrix zero, not a bare scalar zero). When the
      sum does carry a genuine scalar term, that scalar is held apart from the
      matrix-domain sum, which is still formed from the matrix terms alone.

  (2) For a PRODUCT with at least one matrix term, any scalar coefficient is
      first absorbed into one of the matrix factors when an explicit matrix
      factor is present, leaving only matrix factors for the matrix-domain
      product; otherwise the scalar coefficient multiplies the matrix-domain
      product as its leading factor.

The combination is modelled by a minimal class carrying only the two touched
facets: ``matrix_arg_count`` (how many matrix terms feed the matrix-domain
combination) and ``scalar_arg_present`` (whether a scalar term sits among its
top-level arguments). The concrete term payloads are irrelevant to the
behaviour under specification.

Rebuilding the combination is a bounded, straight-line computation: the
post-processor MUST terminate and return its combination (a total-correctness
obligation, carried as MustTerminate in the precondition). An implementation
that diverges before returning would satisfy the value postconditions only
vacuously and would never deliver the rebuilt combination to the constructor
pipeline.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Combo:
    """The rebuilt matrix-domain combination, described by its two touched
    facets: the number of matrix terms it combines and whether a scalar
    coefficient term sits among its top-level arguments."""

    def __init__(self, matrix_arg_count: int, scalar_arg_present: bool) -> None:
        Requires(matrix_arg_count >= 0)
        # Constructing the combination terminates (a straight-line field
        # initialisation); takes the caller's termination obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.matrix_arg_count) and self.matrix_arg_count == matrix_arg_count)  # type: ignore
        Ensures(Acc(self.scalar_arg_present) and self.scalar_arg_present == scalar_arg_present)  # type: ignore
        self.matrix_arg_count = matrix_arg_count
        self.scalar_arg_present = scalar_arg_present


# axioms-start
# (no @ContractOnly axioms: the unchanged matrix-domain constructors and the
# scalar-collapse / scalar-absorb helpers contribute nothing to the touched
# facets beyond what the impl spells out deeply — see refinement.md
# A-reference rows. The axioms region is intentionally empty.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def postprocess(is_sum: bool, num_matrices: int, num_scalars: int,
                has_explicit_matrix: bool) -> Combo:
    """Rebuild the matrix-domain combination for a sum (``is_sum``) or a product
    of ``num_matrices`` matrix terms and ``num_scalars`` scalar terms; for a
    product, ``has_explicit_matrix`` records whether an explicit matrix factor is
    present to absorb a scalar coefficient. Pre-condition: at least one matrix
    term (the no-matrix case is handled before this point)."""
    # pre-conditions-start
    Requires(num_matrices >= 1)
    Requires(num_scalars >= 0)
    # Rebuilding the combination is a bounded, straight-line computation: the
    # post-processor MUST terminate and return its Combo (total correctness).
    # A diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver the rebuilt combination to the
    # constructor pipeline.
    Requires(MustTerminate(2))
    # post-conditions-end is below; this is the pre block
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().matrix_arg_count) and Acc(Result().scalar_arg_present))
    # The matrix-domain combination is always formed from exactly the matrix
    # terms (a product whose scalar is absorbed loses no matrix factor; a sum
    # never folds a scalar into the matrix-domain combination).
    Ensures(Result().matrix_arg_count == num_matrices)
    # (1) A SUM never receives a scalar coefficient among the matrix-domain
    # arguments — including when there is no genuine scalar term, where the
    # additive identity must NOT be collapsed in. The rebuilt sum therefore
    # stays a matrix expression.
    Ensures(Implies(is_sum, Result().scalar_arg_present == False))
    # (2) A PRODUCT keeps a scalar coefficient argument exactly when it has a
    # genuine scalar term that no explicit matrix factor can absorb.
    Ensures(Implies(not is_sum,
                    Result().scalar_arg_present
                    == (num_scalars > 0 and not has_explicit_matrix)))
    # post-conditions-end
    # impl-start
    if num_scalars > 0:
        if not is_sum:
            # Product with a scalar coefficient: absorb it into an explicit
            # matrix factor when one is present, leaving only matrix factors.
            absorbed = has_explicit_matrix  # type: bool
            if absorbed:
                return Combo(num_matrices, False)
            # No explicit matrix to absorb into: the scalar coefficient leads
            # the matrix-domain product.
            return Combo(num_matrices, True)
        else:
            # Sum with a genuine scalar term: the scalar is held apart; the
            # matrix-domain sum is formed from the matrix terms alone.
            return Combo(num_matrices, False)
    # No genuine scalar term remains.
    if is_sum:
        # Build the matrix-domain sum from the matrix terms alone; do NOT
        # collapse the empty scalar collection into the additive identity and
        # inject it as an argument.
        return Combo(num_matrices, False)
    # Product with no scalar term: the matrix-domain product is the matrix
    # factors alone (the empty scalar collection collapses to the multiplicative
    # identity, which the product constructor drops — no scalar argument).
    return Combo(num_matrices, False)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins BOTH observable facets for every input: matrix_arg_count == num_matrices (always), and scalar_arg_present == False if is_sum else (num_scalars>0 and not has_explicit_matrix). So any verifying impl must agree with gold on both facets pointwise; there is no room for a behaviorally-divergent verifying impl. Empirically confirmed with 8 same-spec attacks (all confirmed same-spec via `adversary same-spec`, exit 0) run through `adversary weakness nagini sympy__sympy-17630` (project root, env python, SBU_BENCHMARK_DIR=benchmark-verified).

POSITIVE CONTROL: pos_control.py (copy of model.py) -> `bash scripts/nagini_verify.sh` => Verification successful, 8.19s, exit 0.

### ATTACK RESULTS (weakness cmd):
- atk_1.py (PREPATCH BUG: is_sum & num_scalars==0 -> Combo(num_matrices, True), injecting the collapsed additive identity): NOT-A-COUNTEREXAMPLE, does not verify (verification failed). Prepatch bug reproduced & correctly rejected by Ensures(Implies(is_sum, scalar_arg_present==False)).
- atk_2.py (PARTIAL-DOMAIN: no-scalar branch always returns scalar_arg_present=True ignoring is_sum): NOT-A-COUNTEREXAMPLE, does not verify.
- atk_3.py (BOUNDARY: off-by-one, Combo(num_matrices+1, False) in sum-no-scalar branch): NOT-A-COUNTEREXAMPLE, does not verify (matrix_arg_count==num_matrices leg holds).
- atk_4.py (CONTROL-FLOW-EFFECT / nontermination: `while True: pass` in the discriminating branch): NOT-A-COUNTEREXAMPLE, does not verify -> MustTerminate(2) obligation (A1t) rejects it.
- atk_7.py (WRONG Mul-facet: Mul no-explicit-matrix branch returns False instead of True): NOT-A-COUNTEREXAMPLE, does not verify (product postcondition leg holds).
- atk_5.py, atk_6.py, atk_8.py (UNGROUNDED-ORACLE ECHOES: closed-form boolean / branch-reshuffle / early-return-reorder, each computing the IDENTICAL facet values as gold): CANDIDATE-COUNTEREXAMPLE (share spec AND verify, ~8.5-9.3s each). Per protocol, materialized each candidate's faithful refined patch. Because all three are pure behavioral echoes of gold (identical facets on every input), each faithful patch is byte-identical to the gold patch (sha1 ead7d180a0e9 for all three, matching benchmark-verified/sympy__sympy-17630/patch.diff). Ran through the official harness: `run_resolve('sympy__sympy-17630', patch, timeout=1800, retries=0)` => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, tests_status present, patch_successfully_applied. So every verifying candidate's refined patch RESOLVES -> NOT a weakness (resolving echoes; consistent with the fixed G-PANEL-1/G-EQ candidate->resolve policy).

REFINEMENT.MD AUDIT: axioms region intentionally EMPTY (verified in model.py lines 64-69), so NO consumed @ContractOnly axioms. Every leg is R / A-reference / I -- NO kind-3 (unexpressible-changed-op): A1=R (carrier refinement is_sum<->cls==Add, counts<->len, has_explicit_matrix<->absorbable factor), A1t=I (MustTerminate; empirically load-bearing per atk_4 rejection), A2=I, A3=R+A-reference (Mul absorb), A4=R+I (Add genuine-scalar held apart), A5=I+R (the inserted MatAdd fix -- discriminating step, empirically load-bearing per atk_1 rejection), A6=A-reference (Mul no-scalar identity dropped), B1/B2=A-reference. A-reference correspondence to the real _postprocessor (matexpr.py:597-631) is validated by axiom_check.py/G-AX, which reproduces the exact F2P witnesses block_collapse(b*b*b) and Add(ZeroMatrix,ZeroMatrix)==ZeroMatrix. The load-bearing facet scalar_arg_present is exactly what separates prepatch from gold. Correspondence holds; no gap between the deep facet model and the real callee.

CONCLUSION: prepatch reproduced & rejected; all non-echo wrong impls (partial-domain, boundary, nontermination, wrong-facet) rejected by the spec; all verifying impls are gold-behavior echoes whose materialized faithful patches resolve. verify => correct holds for this bundle. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-17630.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A symbolic combination (a commutative sum, or a product) of terms is
  post-processed for the matrix-expression domain. Its terms are partitioned
  into matrix-valued terms and ordinary scalar terms, and a single combined
  expression is rebuilt for the matrix domain. The result is described only by
  two observable facets: how many matrix terms feed the rebuilt matrix-domain
  combination, and whether the rebuilt matrix-domain combination is fed a
  scalar coefficient term as one of its top-level arguments.

  (1) For a SUM with at least one matrix term, the rebuilt matrix-domain sum is
      formed from the matrix terms ALONE. No scalar coefficient is ever placed
      among its arguments: when the sum has no genuine scalar term, the empty
      collection of scalars must NOT be collapsed into the additive identity and
      injected as an argument. Consequently the rebuilt sum stays a matrix
      expression, so a sum of matrix terms remains in the matrix domain (and an
      all-zero such sum stays a matrix zero, not a bare scalar zero). When the
      sum does carry a genuine scalar term, that scalar is held apart from the
      matrix-domain sum, which is still formed from the matrix terms alone.

  (2) For a PRODUCT with at least one matrix term, any scalar coefficient is
      first absorbed into one of the matrix factors when an explicit matrix
      factor is present, leaving only matrix factors for the matrix-domain
      product; otherwise the scalar coefficient multiplies the matrix-domain
      product as its leading factor.

The combination is modelled by a minimal class carrying only the two touched
facets: ``matrix_arg_count`` (how many matrix terms feed the matrix-domain
combination) and ``scalar_arg_present`` (whether a scalar term sits among its
top-level arguments). The concrete term payloads are irrelevant to the
behaviour under specification.

Rebuilding the combination is a bounded, straight-line computation: the
post-processor MUST terminate and return its combination (a total-correctness
obligation, carried as MustTerminate in the precondition). An implementation
that diverges before returning would satisfy the value postconditions only
vacuously and would never deliver the rebuilt combination to the constructor
pipeline.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Combo:
    """The rebuilt matrix-domain combination, described by its two touched
    facets: the number of matrix terms it combines and whether a scalar
    coefficient term sits among its top-level arguments."""

    def __init__(self, matrix_arg_count: int, scalar_arg_present: bool) -> None:
        Requires(matrix_arg_count >= 0)
        # Constructing the combination terminates (a straight-line field
        # initialisation); takes the caller's termination obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.matrix_arg_count) and self.matrix_arg_count == matrix_arg_count)  # type: ignore
        Ensures(Acc(self.scalar_arg_present) and self.scalar_arg_present == scalar_arg_present)  # type: ignore
        self.matrix_arg_count = matrix_arg_count
        self.scalar_arg_present = scalar_arg_present


# axioms-start
# (no @ContractOnly axioms: the unchanged matrix-domain constructors and the
# scalar-collapse / scalar-absorb helpers contribute nothing to the touched
# facets beyond what the impl spells out deeply — see refinement.md
# A-reference rows. The axioms region is intentionally empty.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def postprocess(is_sum: bool, num_matrices: int, num_scalars: int,
                has_explicit_matrix: bool) -> Combo:
    """Rebuild the matrix-domain combination for a sum (``is_sum``) or a product
    of ``num_matrices`` matrix terms and ``num_scalars`` scalar terms; for a
    product, ``has_explicit_matrix`` records whether an explicit matrix factor is
    present to absorb a scalar coefficient. Pre-condition: at least one matrix
    term (the no-matrix case is handled before this point)."""
    # pre-conditions-start
    Requires(num_matrices >= 1)
    Requires(num_scalars >= 0)
    # Rebuilding the combination is a bounded, straight-line computation: the
    # post-processor MUST terminate and return its Combo (total correctness).
    # A diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver the rebuilt combination to the
    # constructor pipeline.
    Requires(MustTerminate(2))
    # post-conditions-end is below; this is the pre block
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().matrix_arg_count) and Acc(Result().scalar_arg_present))
    # The matrix-domain combination is always formed from exactly the matrix
    # terms (a product whose scalar is absorbed loses no matrix factor; a sum
    # never folds a scalar into the matrix-domain combination).
    Ensures(Result().matrix_arg_count == num_matrices)
    # (1) A SUM never receives a scalar coefficient among the matrix-domain
    # arguments — including when there is no genuine scalar term, where the
    # additive identity must NOT be collapsed in. The rebuilt sum therefore
    # stays a matrix expression.
    Ensures(Implies(is_sum, Result().scalar_arg_present == False))
    # (2) A PRODUCT keeps a scalar coefficient argument exactly when it has a
    # genuine scalar term that no explicit matrix factor can absorb.
    Ensures(Implies(not is_sum,
                    Result().scalar_arg_present
                    == (num_scalars > 0 and not has_explicit_matrix)))
    # post-conditions-end
    # impl-start
    if num_scalars > 0:
        if not is_sum:
            # Product with a scalar coefficient: absorb it into an explicit
            # matrix factor when one is present, leaving only matrix factors.
            absorbed = has_explicit_matrix  # type: bool
            if absorbed:
                return Combo(num_matrices, False)
            # No explicit matrix to absorb into: the scalar coefficient leads
            # the matrix-domain product.
            return Combo(num_matrices, True)
        else:
            # Sum with a genuine scalar term: the scalar is held apart; the
            # matrix-domain sum is formed from the matrix terms alone.
            return Combo(num_matrices, False)
    # No genuine scalar term remains.
    if is_sum:
        # Build the matrix-domain sum from the matrix terms alone; do NOT
        # collapse the empty scalar collection into the additive identity and
        # inject it as an argument.
        return Combo(num_matrices, False)
    # Product with no scalar term: the matrix-domain product is the matrix
    # factors alone (the empty scalar collection collapses to the multiplicative
    # identity, which the product constructor drops — no scalar argument).
    return Combo(num_matrices, False)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins BOTH observable facets for every input: matrix_arg_count == num_matrices (always), and scalar_arg_present == False if is_sum else (num_scalars>0 and not has_explicit_matrix). So any verifying impl must agree with gold on both facets pointwise; there is no room for a behaviorally-divergent verifying impl. Empirically confirmed with 8 same-spec attacks (all confirmed same-spec via `adversary same-spec`, exit 0) run through `adversary weakness nagini sympy__sympy-17630` (project root, env python, SBU_BENCHMARK_DIR=benchmark-verified).

POSITIVE CONTROL: pos_control.py (copy of model.py) -> `bash scripts/nagini_verify.sh` => Verification successful, 8.19s, exit 0.

### ATTACK RESULTS (weakness cmd):
- atk_1.py (PREPATCH BUG: is_sum & num_scalars==0 -> Combo(num_matrices, True), injecting the collapsed additive identity): NOT-A-COUNTEREXAMPLE, does not verify (verification failed). Prepatch bug reproduced & correctly rejected by Ensures(Implies(is_sum, scalar_arg_present==False)).
- atk_2.py (PARTIAL-DOMAIN: no-scalar branch always returns scalar_arg_present=True ignoring is_sum): NOT-A-COUNTEREXAMPLE, does not verify.
- atk_3.py (BOUNDARY: off-by-one, Combo(num_matrices+1, False) in sum-no-scalar branch): NOT-A-COUNTEREXAMPLE, does not verify (matrix_arg_count==num_matrices leg holds).
- atk_4.py (CONTROL-FLOW-EFFECT / nontermination: `while True: pass` in the discriminating branch): NOT-A-COUNTEREXAMPLE, does not verify -> MustTerminate(2) obligation (A1t) rejects it.
- atk_7.py (WRONG Mul-facet: Mul no-explicit-matrix branch returns False instead of True): NOT-A-COUNTEREXAMPLE, does not verify (product postcondition leg holds).
- atk_5.py, atk_6.py, atk_8.py (UNGROUNDED-ORACLE ECHOES: closed-form boolean / branch-reshuffle / early-return-reorder, each computing the IDENTICAL facet values as gold): CANDIDATE-COUNTEREXAMPLE (share spec AND verify, ~8.5-9.3s each). Per protocol, materialized each candidate's faithful refined patch. Because all three are pure behavioral echoes of gold (identical facets on every input), each faithful patch is byte-identical to the gold patch (sha1 ead7d180a0e9 for all three, matching benchmark-verified/sympy__sympy-17630/patch.diff). Ran through the official harness: `run_resolve('sympy__sympy-17630', patch, timeout=1800, retries=0)` => RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, tests_status present, patch_successfully_applied. So every verifying candidate's refined patch RESOLVES -> NOT a weakness (resolving echoes; consistent with the fixed G-PANEL-1/G-EQ candidate->resolve policy).

REFINEMENT.MD AUDIT: axioms region intentionally EMPTY (verified in model.py lines 64-69), so NO consumed @ContractOnly axioms. Every leg is R / A-reference / I -- NO kind-3 (unexpressible-changed-op): A1=R (carrier refinement is_sum<->cls==Add, counts<->len, has_explicit_matrix<->absorbable factor), A1t=I (MustTerminate; empirically load-bearing per atk_4 rejection), A2=I, A3=R+A-reference (Mul absorb), A4=R+I (Add genuine-scalar held apart), A5=I+R (the inserted MatAdd fix -- discriminating step, empirically load-bearing per atk_1 rejection), A6=A-reference (Mul no-scalar identity dropped), B1/B2=A-reference. A-reference correspondence to the real _postprocessor (matexpr.py:597-631) is validated by axiom_check.py/G-AX, which reproduces the exact F2P witnesses block_collapse(b*b*b) and Add(ZeroMatrix,ZeroMatrix)==ZeroMatrix. The load-bearing facet scalar_arg_present is exactly what separates prepatch from gold. Correspondence holds; no gap between the deep facet model and the real callee.

CONCLUSION: prepatch reproduced & rejected; all non-echo wrong impls (partial-domain, boundary, nontermination, wrong-facet) rejected by the spec; all verifying impls are gold-behavior echoes whose materialized faithful patches resolve. verify => correct holds for this bundle. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sympy__sympy-17630 nagini. The modeled function `postprocess(is_sum, num_matrices, num_scalars, has_explicit_matrix)` abstracts the matrix-expression constructor post-processor `get_postprocessor(cls)._postprocessor` (matexpr.py:597-631, gold-patched) via two touched facets: matrix_arg_count and scalar_arg_present.

Method: I built a patched repo copy (at base_commit 58e78209 + the gold `if mat_class == MatAdd: return mat_class(*matrices).doit(deep=False)` hunk) and ran TWO independent differentials against the REAL callee, distinct from the bundle's own conformance_check.py:
  (1) Structured drive through the REAL public Add/Mul constructors and the actually-registered post-processor, capturing the mapping.md abstraction at entry (is_sum<->cls==Add; num_matrices<->len(matrices); num_scalars<->len(nonmatrices); has_explicit_matrix<->an explicit non-MatrixExpr matrix factor) and the real facets from the splat fed to MatAdd/MatMul: 2880 trials over is_sum x {matrix symbols, explicit dense matrices, zero/identity matrices} x {0..2 scalars}. 0 mismatches.
  (2) Direct closure invocation over its raw reachable duck-typed input domain: 30,000 fuzz draws (seed 17630). 0 disagreements.

Boundary cases specifically probed for a too-strong spec: SUM of matrices with no genuine scalar (the fixed case) -> real MatAdd(*matrices) carries no scalar arg, matching Implies(is_sum, scalar_arg_present==False); SUM with genuine scalar held apart (scalar not fed to MatAdd); PRODUCT scalar absorbed into explicit matrix -> scalar_arg_present==False; PRODUCT scalar coefficients that reduce toward One (2*1/2, 3*1/3, -1*-1) -> real Mul._from_args does NOT collapse to S.One (yields 2/2, (-1)*3/3 etc.), so scalar_arg_present==True, matching the model's (num_scalars>0 and not has_explicit_matrix); all-zero matrix sum stays a matrix zero. Every case the model's postconditions match the real callee.

The model verifies under the pinned Nagini verifier (Verification successful, 6.72s). Its postconditions are exact equalities/implications tightly matching the impl region and the real callee — no over-constraint, no drift on any reachable input. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage check of the spec view (model.py docstring + Combo class + pre/post-condition regions; impl region stripped) against the PUBLIC problem_statement (hints_text excluded) for sympy__sympy-17630.

Gold edit (matexpr.py:628-629, _postprocessor): `if mat_class == MatAdd: return mat_class(*matrices).doit(deep=False)` — rebuild the matrix-domain sum from the matrix terms alone, never injecting the scalar additive identity (Add._from_args([]) == Zero()).

Public problem_statement ALREADY discloses the root cause: block-multiplying a BlockMatrix with ZeroMatrix blocks 3x throws "'Zero' object has no attribute 'cols'", and the reporter explicitly diagnoses that "the zeros in b._blockmul(b) are not ZeroMatrix but Zero" (scalar Zero contaminating a matrix domain). So the public issue itself pins the scalar-Zero-in-matrix-sum mechanism.

Spec view findings:
1. The spec describes desired behavior abstractly (matrix terms vs scalar terms, additive identity NOT collapsed into the matrix-domain sum, scalar_arg_present==False for sums). Encoding correct behavior is the task, not leakage.
2. NO repo-specific identifiers appear in the spec view: no matexpr.py, no _postprocessor/get_postprocessor, no MatAdd/MatMul/Add/Mul, no line numbers, no gold-patch code snippet or patch shape. Those repo bindings live only in mapping.md and refinement.md, which are auditor-only artifacts OUTSIDE the consumer spec view.
3. The one mechanism the spec highlights (empty scalar collection must not collapse to the additive identity and be injected as an argument) is exactly the root cause already public in problem_statement (Zero vs ZeroMatrix). It reveals nothing beyond the public issue.
4. A solver still must locate the real _postprocessor callee, map the abstraction back, and author the fix — no gold-reconstruction shortcut is provided.

Corroboration: G-LEAK lexical screen recorded pass ("spec view clean", no failures). No RELAXED_LEAKAGE.md present; strict panel_3 basis applies. Spec region confirmed byte-identical per same-spec/G-HYGIENE region_hashes. Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
