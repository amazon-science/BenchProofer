# P2 adversarial audit — sympy__sympy-13757

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| does not verify against this specification, so the specification excludes it | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
                          other_priority: float, other_evaluates: bool,
                          other_has_handler: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is the contribution of whichever operand the constant selection
@@ -78,7 +76,6 @@
 
 def polynomial_priority() -> float:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A polynomial's selection attribute is strictly greater than the baseline
@@ -95,13 +92,12 @@
     Ensures(Result() >= default_priority() + 1e-15)
     # post-conditions-end
     # impl-start
-    return 10.001
+    return 1000000000.0
     # impl-end
 
 
 def generic_times_polynomial() -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The required behaviour: the product of a generic expression and a
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
                          other_priority: float, other_evaluates: bool,
                          other_has_handler: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is the contribution of whichever operand the constant selection
@@ -78,7 +76,6 @@
 
 def polynomial_priority() -> float:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A polynomial's selection attribute is strictly greater than the baseline
@@ -95,13 +92,12 @@
     Ensures(Result() >= default_priority() + 1e-15)
     # post-conditions-end
     # impl-start
-    return 10.001
+    return 11.0
     # impl-end
 
 
 def generic_times_polynomial() -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The required behaviour: the product of a generic expression and a
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
                          other_priority: float, other_evaluates: bool,
                          other_has_handler: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is the contribution of whichever operand the constant selection
@@ -78,7 +76,6 @@
 
 def polynomial_priority() -> float:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A polynomial's selection attribute is strictly greater than the baseline
@@ -95,13 +92,12 @@
     Ensures(Result() >= default_priority() + 1e-15)
     # post-conditions-end
     # impl-start
-    return 10.001
+    return 10.01
     # impl-end
 
 
 def generic_times_polynomial() -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The required behaviour: the product of a generic expression and a
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
                          other_priority: float, other_evaluates: bool,
                          other_has_handler: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is the contribution of whichever operand the constant selection
@@ -78,7 +76,6 @@
 
 def polynomial_priority() -> float:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A polynomial's selection attribute is strictly greater than the baseline
@@ -95,13 +92,12 @@
     Ensures(Result() >= default_priority() + 1e-15)
     # post-conditions-end
     # impl-start
-    return 10.001
+    return 10.000000000000002
     # impl-end
 
 
 def generic_times_polynomial() -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The required behaviour: the product of a generic expression and a
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
                          other_priority: float, other_evaluates: bool,
                          other_has_handler: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is the contribution of whichever operand the constant selection
@@ -78,7 +76,6 @@
 
 def polynomial_priority() -> float:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A polynomial's selection attribute is strictly greater than the baseline
@@ -95,13 +92,13 @@
     Ensures(Result() >= default_priority() + 1e-15)
     # post-conditions-end
     # impl-start
-    return 10.001
+    base = default_priority()
+    return base + 5.0
     # impl-end
 
 
 def generic_times_polynomial() -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The required behaviour: the product of a generic expression and a
```

Attack 6 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
                          other_priority: float, other_evaluates: bool,
                          other_has_handler: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is the contribution of whichever operand the constant selection
@@ -78,7 +76,6 @@
 
 def polynomial_priority() -> float:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A polynomial's selection attribute is strictly greater than the baseline
@@ -95,13 +92,12 @@
     Ensures(Result() >= default_priority() + 1e-15)
     # post-conditions-end
     # impl-start
-    return 10.001
+    return float('inf')
     # impl-end
 
 
 def generic_times_polynomial() -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The required behaviour: the product of a generic expression and a
```

Attack 7 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
                          other_priority: float, other_evaluates: bool,
                          other_has_handler: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is the contribution of whichever operand the constant selection
@@ -78,7 +76,6 @@
 
 def polynomial_priority() -> float:
     # pre-conditions-start
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # A polynomial's selection attribute is strictly greater than the baseline
@@ -95,13 +92,12 @@
     Ensures(Result() >= default_priority() + 1e-15)
     # post-conditions-end
     # impl-start
-    return 10.001
+    return 10.0
     # impl-end
 
 
 def generic_times_polynomial() -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The required behaviour: the product of a generic expression and a
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-13757.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A product of two symbolic operands is resolved by a constant, side-agnostic
  rule that selects which operand contributes the result; that selection rule
  is not itself the subject of the desired behaviour. The result is either a
  fully-computed polynomial product or an unsimplified product expression,
  depending on which operand the rule selects.

  The desired behaviour: the product of a generic symbolic expression and a
  polynomial must come out fully computed (the polynomial product) regardless
  of which side the polynomial is written on. In particular the product with
  the generic expression written on the left must agree with the product with
  the polynomial written on the left — both must be the computed polynomial
  product, not an unsimplified expression.

The operand attributes that the constant selection rule reads are modelled as
interpreted real numbers (verified with `--float-encoding=real`): the selection
turns on the strict order of two reals, so they are kept as genuine, distinct
reals rather than faked with ints. Each operand is modelled by the two attributes
the rule and the observable outcome read — one real attribute and a boolean for
whether its contribution is the computed polynomial product — passed directly.
The constant selection rule is modelled deeply (it is unchanged); its provenance and
executable soundness check are in mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
def default_priority() -> float:
    """The selection attribute a generic symbolic expression carries (a constant
    baseline value common to ordinary expressions)."""
    Ensures(Result() == 10.0)
    return 10.0
# axioms-end


# pure-start
@Pure
def resolved_by_right(self_priority: float, other_priority: float,
                      other_has_handler: bool) -> bool:
    """The constant (unchanged) selection rule, as a pure predicate: the second
    operand contributes the result exactly when it is able to (the boolean) AND
    its selection attribute is strictly greater than the first operand's;
    otherwise the first operand contributes. Side-agnostic and not modified."""
    return other_has_handler and other_priority > self_priority
# pure-end


def product_is_evaluated(self_priority: float, self_evaluates: bool,
                         other_priority: float, other_evaluates: bool,
                         other_has_handler: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The result is the contribution of whichever operand the constant selection
    # rule picks; the outcome is the computed polynomial product exactly when
    # the selected operand's contribution is itself the computed product. The
    # observable is thus produced by the selection, so it cannot report
    # "computed" unless the operand that actually contributes is the one that
    # computes the product.
    Ensures(Result() == (other_evaluates if resolved_by_right(
        self_priority, other_priority, other_has_handler)
        else self_evaluates))
    # post-conditions-end
    # impl-start
    if resolved_by_right(self_priority, other_priority, other_has_handler):
        return other_evaluates
    return self_evaluates
    # impl-end


def polynomial_priority() -> float:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # A polynomial's selection attribute is strictly greater than the baseline
    # value an ordinary expression carries, by a margin no smaller than the
    # resolution of the runtime scalar carrier at the baseline's magnitude
    # (1e-15 at a baseline of 10.0). A margin-free strict order over the
    # interpreted reals would admit attribute values whose distance above the
    # baseline lies beneath that resolution; such a value collapses onto the
    # baseline when materialized as the executable's finite-precision scalar,
    # the comparison becomes a tie, and the selection rule no longer picks the
    # polynomial's (computing) contribution. The margin guarantees the strict
    # order survives materialization, so the selection rule picks the
    # polynomial for the product covered by the desired behaviour.
    Ensures(Result() >= default_priority() + 1e-15)
    # post-conditions-end
    # impl-start
    return 10.001
    # impl-end


def generic_times_polynomial() -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The required behaviour: the product of a generic expression and a
    # polynomial comes out as the computed polynomial product (reported True).
    # The impl below does not assert this constant directly; it derives the
    # value by running the constant selection rule on the two operands' modelled
    # attributes, and that derivation reaches True only because the polynomial's
    # attribute strictly exceeds the baseline. The discriminating property is
    # carried by polynomial_priority's postcondition, which is where the change
    # under specification lives.
    Ensures(Result() == True)
    # post-conditions-end
    # impl-start
    # The generic operand carries the baseline selection attribute, and its own
    # contribution to a product with a polynomial is NOT the computed product
    # (it would leave an unsimplified expression) -> left_evaluates False.
    left_priority = default_priority()
    left_evaluates = False
    # The polynomial operand is able to contribute (the boolean is True), its
    # contribution IS the computed product (right_evaluates True), and it
    # carries the polynomial selection attribute.
    right_priority = polynomial_priority()
    right_evaluates = True
    # Had the two operands carried the same attribute (no strict order, so the
    # first operand contributes), the outcome would be the unsimplified
    # expression: the generic operand does not itself compute the product. This
    # pins the generic operand as non-computing, so the computed result below is
    # attributable to the polynomial being selected, not to the generic operand.
    Assert(product_is_evaluated(left_priority, left_evaluates,
                                left_priority, right_evaluates, True)
           == False)
    # With the polynomial's attribute strictly greater and it being able to
    # contribute, the selection rule picks the polynomial and the product comes
    # out computed.
    return product_is_evaluated(left_priority, left_evaluates,
                                right_priority, right_evaluates, True)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-13757 (nagini). Frozen spec: the sole discriminating datum is polynomial_priority() with postcondition `Result() >= default_priority() + 1e-15` (default=10.0). This bound is UNBOUNDED ABOVE, whereas the gold patch chose `_op_priority = 10.001` deliberately just above the Expr default (10.0) but BELOW every specialized sympy class (matexpr/boolalg/quaternion/ndim_array = 11.0, dense/common matrices = 10.01, sequences=15, holonomic=20, tensor=12, vector/dyadic=12-13). PRIME FALSIFICATION VECTOR: a same-spec verifying attack returning a value larger than 10.001 would faithfully patch to `Poly._op_priority = <bigger>` and could flip Poly-vs-other-class binary dispatch, breaking PASS_TO_PASS.

Protocol executed (project root; PY=python; verifier fe=real from meta):
- 6 DISTINCT same-spec wrong impls (impl region only; axioms/@Pure/Requires/Ensures byte-identical), each `python -m swebench_unified.adversary weakness nagini sympy__sympy-13757 <atk>` => ALL exit 0 CANDIDATE (share spec AND verify):
  atk_1: return 1000000000.0 (extreme, outranks EVERY class)  -> CANDIDATE 12.3s
  atk_2: return 11.0 (ties matexpr/boolalg/quaternion/array)   -> CANDIDATE 12.2s
  atk_3: return 10.01 (ties dense/common matrices)             -> CANDIDATE 12.3s
  atk_4: return 10.000000000000002 (exactly 10.0+1e-15, boundary)-> CANDIDATE 10.7s
  atk_5: return default_priority()+5.0 == 15.0 (computed/control-flow variant) -> CANDIDATE 10.7s
  atk_7: return float('inf') (ungrounded/degenerate oracle echo)-> CANDIDATE 10.6s
- atk_6: return 10.0 (PREPATCH bug reproduction) => exit 2 NOT-A-COUNTEREXAMPLE 'attack does not verify' — spec correctly REJECTS it (fails polynomial_priority postcondition, matches model_prepatch.py / G-DIFF). prepatch_reproduced=true.
- positive_control = bundle model.py: `adversary verify ... --float-encoding=real` => VERIFIED 11.2s.

MANDATORY resolve step — materialized the faithful refined patch (gold patch with `_op_priority` value substituted per refinement.md A1: R-refinement, class-attr <-> modeled real) for EVERY verifying candidate and ran run_resolve (official harness, image swebench/sweb.eval.x86_64.sympy_1776_sympy-13757, timeout 1800, retries 0):
  gold_patch (10.001)             -> resolved=True, completed=True  (baseline sanity)
  atk_1 (1e9)                     -> resolved=True, completed=True
  atk_2 (11.0)                    -> resolved=True, completed=True
  atk_3 (10.01)                   -> resolved=True, completed=True
  atk_4 (10.0+1e-15)              -> resolved=True, completed=True
  atk_5 (15.0)                    -> resolved=True, completed=True
  atk_7 (inf)                     -> resolved=True, completed=True
EVERY verifying candidate's faithful patch RESOLVES. The unbounded-above vector does NOT break correctness: this instance's FAIL_TO_PASS=[test_issue_13079] + 166 PASS_TO_PASS never multiply Poly against a higher-priority class in a dispatch-flipping way, so any `_op_priority > 10.0` routes x*Poly(x) to Poly.__rmul__ and passes all tested behavior. No verify=>correct breakage found.

Refinement.md audit: legs A1=R (polynomial_priority 10.001 <-> +_op_priority=10.001, value-identical, carrier-only diff), A2=A-reference (default_priority()==Expr._op_priority==10.0, checked axiom_check.py L118; @Pure with body, not @ContractOnly => not a consumed axiom), A3=A-reference (resolved_by_right == real binary_op_wrapper, checked over 131 boundary+20000 fuzz triples, strict > faithful to decorators.py:125), A4=R+A-reference, A5=R+I. Section B 'no kind-3' holds: the single genuinely-changed op is modeled DIRECTLY as the A1 value; meta axioms:[] confirms NO A-consumed axiom. A-leg correspondence to real callees is sound (axiom_check.py imports only sympy, exits 0 in gold state). No leak concerns in scope.

Verdict: SOUND. >=6 distinct same-spec verifying wrong impls all resolve under the official harness; prepatch rejected; positive control verifies; refinement legs all R/A-reference/I with faithful callee correspondence and no kind-3.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| does not verify against this specification, so the specification excludes it | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-13757.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A product of two symbolic operands is resolved by a constant, side-agnostic
  rule that selects which operand contributes the result; that selection rule
  is not itself the subject of the desired behaviour. The result is either a
  fully-computed polynomial product or an unsimplified product expression,
  depending on which operand the rule selects.

  The desired behaviour: the product of a generic symbolic expression and a
  polynomial must come out fully computed (the polynomial product) regardless
  of which side the polynomial is written on. In particular the product with
  the generic expression written on the left must agree with the product with
  the polynomial written on the left — both must be the computed polynomial
  product, not an unsimplified expression.

The operand attributes that the constant selection rule reads are modelled as
interpreted real numbers (verified with `--float-encoding=real`): the selection
turns on the strict order of two reals, so they are kept as genuine, distinct
reals rather than faked with ints. Each operand is modelled by the two attributes
the rule and the observable outcome read — one real attribute and a boolean for
whether its contribution is the computed polynomial product — passed directly.
The constant selection rule is modelled deeply (it is unchanged); its provenance and
executable soundness check are in mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
def default_priority() -> float:
    """The selection attribute a generic symbolic expression carries (a constant
    baseline value common to ordinary expressions)."""
    Ensures(Result() == 10.0)
    return 10.0
# axioms-end


# pure-start
@Pure
def resolved_by_right(self_priority: float, other_priority: float,
                      other_has_handler: bool) -> bool:
    """The constant (unchanged) selection rule, as a pure predicate: the second
    operand contributes the result exactly when it is able to (the boolean) AND
    its selection attribute is strictly greater than the first operand's;
    otherwise the first operand contributes. Side-agnostic and not modified."""
    return other_has_handler and other_priority > self_priority
# pure-end


def product_is_evaluated(self_priority: float, self_evaluates: bool,
                         other_priority: float, other_evaluates: bool,
                         other_has_handler: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The result is the contribution of whichever operand the constant selection
    # rule picks; the outcome is the computed polynomial product exactly when
    # the selected operand's contribution is itself the computed product. The
    # observable is thus produced by the selection, so it cannot report
    # "computed" unless the operand that actually contributes is the one that
    # computes the product.
    Ensures(Result() == (other_evaluates if resolved_by_right(
        self_priority, other_priority, other_has_handler)
        else self_evaluates))
    # post-conditions-end
    # impl-start
    if resolved_by_right(self_priority, other_priority, other_has_handler):
        return other_evaluates
    return self_evaluates
    # impl-end


def polynomial_priority() -> float:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # A polynomial's selection attribute is strictly greater than the baseline
    # value an ordinary expression carries, by a margin no smaller than the
    # resolution of the runtime scalar carrier at the baseline's magnitude
    # (1e-15 at a baseline of 10.0). A margin-free strict order over the
    # interpreted reals would admit attribute values whose distance above the
    # baseline lies beneath that resolution; such a value collapses onto the
    # baseline when materialized as the executable's finite-precision scalar,
    # the comparison becomes a tie, and the selection rule no longer picks the
    # polynomial's (computing) contribution. The margin guarantees the strict
    # order survives materialization, so the selection rule picks the
    # polynomial for the product covered by the desired behaviour.
    Ensures(Result() >= default_priority() + 1e-15)
    # post-conditions-end
    # impl-start
    return 10.001
    # impl-end


def generic_times_polynomial() -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The required behaviour: the product of a generic expression and a
    # polynomial comes out as the computed polynomial product (reported True).
    # The impl below does not assert this constant directly; it derives the
    # value by running the constant selection rule on the two operands' modelled
    # attributes, and that derivation reaches True only because the polynomial's
    # attribute strictly exceeds the baseline. The discriminating property is
    # carried by polynomial_priority's postcondition, which is where the change
    # under specification lives.
    Ensures(Result() == True)
    # post-conditions-end
    # impl-start
    # The generic operand carries the baseline selection attribute, and its own
    # contribution to a product with a polynomial is NOT the computed product
    # (it would leave an unsimplified expression) -> left_evaluates False.
    left_priority = default_priority()
    left_evaluates = False
    # The polynomial operand is able to contribute (the boolean is True), its
    # contribution IS the computed product (right_evaluates True), and it
    # carries the polynomial selection attribute.
    right_priority = polynomial_priority()
    right_evaluates = True
    # Had the two operands carried the same attribute (no strict order, so the
    # first operand contributes), the outcome would be the unsimplified
    # expression: the generic operand does not itself compute the product. This
    # pins the generic operand as non-computing, so the computed result below is
    # attributable to the polynomial being selected, not to the generic operand.
    Assert(product_is_evaluated(left_priority, left_evaluates,
                                left_priority, right_evaluates, True)
           == False)
    # With the polynomial's attribute strictly greater and it being able to
    # contribute, the selection rule picks the polynomial and the product comes
    # out computed.
    return product_is_evaluated(left_priority, left_evaluates,
                                right_priority, right_evaluates, True)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-13757 (nagini). Frozen spec: the sole discriminating datum is polynomial_priority() with postcondition `Result() >= default_priority() + 1e-15` (default=10.0). This bound is UNBOUNDED ABOVE, whereas the gold patch chose `_op_priority = 10.001` deliberately just above the Expr default (10.0) but BELOW every specialized sympy class (matexpr/boolalg/quaternion/ndim_array = 11.0, dense/common matrices = 10.01, sequences=15, holonomic=20, tensor=12, vector/dyadic=12-13). PRIME FALSIFICATION VECTOR: a same-spec verifying attack returning a value larger than 10.001 would faithfully patch to `Poly._op_priority = <bigger>` and could flip Poly-vs-other-class binary dispatch, breaking PASS_TO_PASS.

Protocol executed (project root; PY=python; verifier fe=real from meta):
- 6 DISTINCT same-spec wrong impls (impl region only; axioms/@Pure/Requires/Ensures byte-identical), each `python -m swebench_unified.adversary weakness nagini sympy__sympy-13757 <atk>` => ALL exit 0 CANDIDATE (share spec AND verify):
  atk_1: return 1000000000.0 (extreme, outranks EVERY class)  -> CANDIDATE 12.3s
  atk_2: return 11.0 (ties matexpr/boolalg/quaternion/array)   -> CANDIDATE 12.2s
  atk_3: return 10.01 (ties dense/common matrices)             -> CANDIDATE 12.3s
  atk_4: return 10.000000000000002 (exactly 10.0+1e-15, boundary)-> CANDIDATE 10.7s
  atk_5: return default_priority()+5.0 == 15.0 (computed/control-flow variant) -> CANDIDATE 10.7s
  atk_7: return float('inf') (ungrounded/degenerate oracle echo)-> CANDIDATE 10.6s
- atk_6: return 10.0 (PREPATCH bug reproduction) => exit 2 NOT-A-COUNTEREXAMPLE 'attack does not verify' — spec correctly REJECTS it (fails polynomial_priority postcondition, matches model_prepatch.py / G-DIFF). prepatch_reproduced=true.
- positive_control = bundle model.py: `adversary verify ... --float-encoding=real` => VERIFIED 11.2s.

MANDATORY resolve step — materialized the faithful refined patch (gold patch with `_op_priority` value substituted per refinement.md A1: R-refinement, class-attr <-> modeled real) for EVERY verifying candidate and ran run_resolve (official harness, image swebench/sweb.eval.x86_64.sympy_1776_sympy-13757, timeout 1800, retries 0):
  gold_patch (10.001)             -> resolved=True, completed=True  (baseline sanity)
  atk_1 (1e9)                     -> resolved=True, completed=True
  atk_2 (11.0)                    -> resolved=True, completed=True
  atk_3 (10.01)                   -> resolved=True, completed=True
  atk_4 (10.0+1e-15)              -> resolved=True, completed=True
  atk_5 (15.0)                    -> resolved=True, completed=True
  atk_7 (inf)                     -> resolved=True, completed=True
EVERY verifying candidate's faithful patch RESOLVES. The unbounded-above vector does NOT break correctness: this instance's FAIL_TO_PASS=[test_issue_13079] + 166 PASS_TO_PASS never multiply Poly against a higher-priority class in a dispatch-flipping way, so any `_op_priority > 10.0` routes x*Poly(x) to Poly.__rmul__ and passes all tested behavior. No verify=>correct breakage found.

Refinement.md audit: legs A1=R (polynomial_priority 10.001 <-> +_op_priority=10.001, value-identical, carrier-only diff), A2=A-reference (default_priority()==Expr._op_priority==10.0, checked axiom_check.py L118; @Pure with body, not @ContractOnly => not a consumed axiom), A3=A-reference (resolved_by_right == real binary_op_wrapper, checked over 131 boundary+20000 fuzz triples, strict > faithful to decorators.py:125), A4=R+A-reference, A5=R+I. Section B 'no kind-3' holds: the single genuinely-changed op is modeled DIRECTLY as the A1 value; meta axioms:[] confirms NO A-consumed axiom. A-leg correspondence to real callees is sound (axiom_check.py imports only sympy, exits 0 in gold state). No leak concerns in scope.

Verdict: SOUND. >=6 distinct same-spec verifying wrong impls all resolve under the official harness; prepatch rejected; positive control verifies; refinement legs all R/A-reference/I with faithful callee correspondence and no kind-3.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same-spec exit 0); model verifies under bundle's declared --float-encoding=real (10.7s). Faithfulness confirmed against the real repo (worktree at gold, cross-checked pre-patch by reverting the _op_priority line): (1) default_priority()==10.0 == real Expr._op_priority; (2) polynomial_priority()==10.001 == real Poly._op_priority post-patch, and pre-patch it inherits 10.0 (matches G-DIFF); (3) resolved_by_right = other_has_handler and other_priority>self_priority matches the REAL binary_op_wrapper delegation decision over a 131-point grid + 20000 fuzz (axiom_check exit 0) and hand-probed ties/near-ties/no-handler cases — all MATCH; (4) product_is_evaluated selection semantics match x*Poly(x) evaluating to Poly(x**2,x,domain='ZZ') post-patch and staying inert (x*Poly(x,x,domain='ZZ')) pre-patch; (5) generic_times_polynomial()==True matches real x*Poly(x)==Poly(x)*x post-patch. The +1e-15 margin on polynomial_priority is a conservative strengthening but excludes no real input (real margin is 0.001 >> 1e-15), so it introduces no drift. No diverging input found; the spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit is `Poly._op_priority = 10.001` (dispatch-priority datum). Verified mechanically: (1) same_spec(model, model_prepatch)=True — spec region byte-identical, discriminator lives only in the elided impl (`return 10.001`); (2) the literal gold value 10.001 is ABSENT from the spec view, as are the repo symbol `_op_priority`, class `Poly`, file `polytools`, and dispatch symbols `__rmul__`/`call_highest_priority`; (3) lexical G-LEAK screen passes with hard_failures=[] (no diff markers, no reproduced gold line, no patched path, no symbol echo, no bug/fix narration). The only sympy-related token is the public instance id in the docstring header. Tokens `10.0` and `1e-15` do NOT leak: 10.0 is the UNCHANGED inherited Expr._op_priority baseline (default_priority(), a modeled datum, not the gold value which is 10.001 and differs), never appearing in a gold-patch line; 1e-15 is a real→runtime-scalar materialization margin, an artifact of the modeling not the edit. The postcondition `Result() >= default_priority() + 1e-15` states only the abstract discriminating property (polynomial priority strictly exceeds baseline) — legitimate specification content from which a solver cannot reconstruct `_op_priority = 10.001` or the symbol/file. No RELAXED_LEAKAGE.md and relaxed_leakage flag unset, so this is a genuine strict clean pass. The spec view reveals nothing about the gold edit beyond the public problem_statement (hints_text empty and irrelevant).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
