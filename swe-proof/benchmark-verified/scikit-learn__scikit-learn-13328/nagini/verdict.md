# P2 adversarial audit — scikit-learn__scikit-learn-13328

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_boundary.py`, `atk_3_ctrlflow_branch.py`, `atk_4_novalidation_consttag.py`, `atk_5_const_inputrep.py`, `atk_6_prepatch_claimfloat.py`, `atk_7_unnegated.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8_echo_branch.py`, `atk_9_float_only_logical.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -113,7 +112,6 @@
     modelled value carrier), so no value payload is threaded through."""
     Requires(0 <= input_rep and input_rep <= 2)
     # The validated representation is exactly the deeply-modelled one.
-    Requires(MustTerminate(2))
     Ensures(Result() == validated_rep(input_rep, request_floating))
     # Evidence that the matrix ACTUALLY has representation Result() now.
     Ensures(matrix_rep(input_rep, Result()))
@@ -142,7 +140,6 @@
     # The negation can only be performed when that actual representation
     # supports it (numpy `-` raises on a logical representation otherwise).
     Requires(supports_negation(rep))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(row_values), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The result is exactly the element-wise negation of the selected rows.
@@ -196,7 +193,6 @@
     # The input element representation is one of the three modelled kinds;
     # in particular it MAY be the logical representation (REP_LOGICAL == 0).
     Requires(0 <= input_rep and input_rep <= 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(row_values), 1 / 2))
@@ -218,9 +214,8 @@
     Ensures(negation_performed(input_rep, row_values))
     # post-conditions-end
     # impl-start
-    # Validation: request a floating representation so that the subsequent
-    # negation is well-defined regardless of the input representation.
-    rep = validate_matrix(input_rep, True)
+    # Pre-patch: validation WITHOUT requesting a floating representation.
+    rep = validate_matrix(input_rep, False)
     result = negate_rows(input_rep, rep, row_values)
     return result
     # impl-end
```

Attack 2 — `atk_2_boundary.py` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -113,7 +112,6 @@
     modelled value carrier), so no value payload is threaded through."""
     Requires(0 <= input_rep and input_rep <= 2)
     # The validated representation is exactly the deeply-modelled one.
-    Requires(MustTerminate(2))
     Ensures(Result() == validated_rep(input_rep, request_floating))
     # Evidence that the matrix ACTUALLY has representation Result() now.
     Ensures(matrix_rep(input_rep, Result()))
@@ -142,7 +140,6 @@
     # The negation can only be performed when that actual representation
     # supports it (numpy `-` raises on a logical representation otherwise).
     Requires(supports_negation(rep))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(row_values), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The result is exactly the element-wise negation of the selected rows.
@@ -196,7 +193,6 @@
     # The input element representation is one of the three modelled kinds;
     # in particular it MAY be the logical representation (REP_LOGICAL == 0).
     Requires(0 <= input_rep and input_rep <= 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(row_values), 1 / 2))
@@ -218,9 +214,7 @@
     Ensures(negation_performed(input_rep, row_values))
     # post-conditions-end
     # impl-start
-    # Validation: request a floating representation so that the subsequent
-    # negation is well-defined regardless of the input representation.
-    rep = validate_matrix(input_rep, True)
+    rep = validate_matrix(input_rep, input_rep >= 1)
     result = negate_rows(input_rep, rep, row_values)
     return result
     # impl-end
```

Attack 3 — `atk_3_ctrlflow_branch.py` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -113,7 +112,6 @@
     modelled value carrier), so no value payload is threaded through."""
     Requires(0 <= input_rep and input_rep <= 2)
     # The validated representation is exactly the deeply-modelled one.
-    Requires(MustTerminate(2))
     Ensures(Result() == validated_rep(input_rep, request_floating))
     # Evidence that the matrix ACTUALLY has representation Result() now.
     Ensures(matrix_rep(input_rep, Result()))
@@ -142,7 +140,6 @@
     # The negation can only be performed when that actual representation
     # supports it (numpy `-` raises on a logical representation otherwise).
     Requires(supports_negation(rep))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(row_values), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The result is exactly the element-wise negation of the selected rows.
@@ -196,7 +193,6 @@
     # The input element representation is one of the three modelled kinds;
     # in particular it MAY be the logical representation (REP_LOGICAL == 0).
     Requires(0 <= input_rep and input_rep <= 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(row_values), 1 / 2))
@@ -218,9 +214,10 @@
     Ensures(negation_performed(input_rep, row_values))
     # post-conditions-end
     # impl-start
-    # Validation: request a floating representation so that the subsequent
-    # negation is well-defined regardless of the input representation.
-    rep = validate_matrix(input_rep, True)
+    if input_rep == 0:
+        rep = validate_matrix(input_rep, False)
+    else:
+        rep = validate_matrix(input_rep, True)
     result = negate_rows(input_rep, rep, row_values)
     return result
     # impl-end
```

Attack 4 — `atk_4_novalidation_consttag.py` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -113,7 +112,6 @@
     modelled value carrier), so no value payload is threaded through."""
     Requires(0 <= input_rep and input_rep <= 2)
     # The validated representation is exactly the deeply-modelled one.
-    Requires(MustTerminate(2))
     Ensures(Result() == validated_rep(input_rep, request_floating))
     # Evidence that the matrix ACTUALLY has representation Result() now.
     Ensures(matrix_rep(input_rep, Result()))
@@ -142,7 +140,6 @@
     # The negation can only be performed when that actual representation
     # supports it (numpy `-` raises on a logical representation otherwise).
     Requires(supports_negation(rep))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(row_values), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The result is exactly the element-wise negation of the selected rows.
@@ -196,7 +193,6 @@
     # The input element representation is one of the three modelled kinds;
     # in particular it MAY be the logical representation (REP_LOGICAL == 0).
     Requires(0 <= input_rep and input_rep <= 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(row_values), 1 / 2))
@@ -218,9 +214,6 @@
     Ensures(negation_performed(input_rep, row_values))
     # post-conditions-end
     # impl-start
-    # Validation: request a floating representation so that the subsequent
-    # negation is well-defined regardless of the input representation.
-    rep = validate_matrix(input_rep, True)
-    result = negate_rows(input_rep, rep, row_values)
+    result = negate_rows(input_rep, 2, row_values)
     return result
     # impl-end
```

Attack 5 — `atk_5_const_inputrep.py` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -113,7 +112,6 @@
     modelled value carrier), so no value payload is threaded through."""
     Requires(0 <= input_rep and input_rep <= 2)
     # The validated representation is exactly the deeply-modelled one.
-    Requires(MustTerminate(2))
     Ensures(Result() == validated_rep(input_rep, request_floating))
     # Evidence that the matrix ACTUALLY has representation Result() now.
     Ensures(matrix_rep(input_rep, Result()))
@@ -142,7 +140,6 @@
     # The negation can only be performed when that actual representation
     # supports it (numpy `-` raises on a logical representation otherwise).
     Requires(supports_negation(rep))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(row_values), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The result is exactly the element-wise negation of the selected rows.
@@ -196,7 +193,6 @@
     # The input element representation is one of the three modelled kinds;
     # in particular it MAY be the logical representation (REP_LOGICAL == 0).
     Requires(0 <= input_rep and input_rep <= 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(row_values), 1 / 2))
@@ -218,9 +214,7 @@
     Ensures(negation_performed(input_rep, row_values))
     # post-conditions-end
     # impl-start
-    # Validation: request a floating representation so that the subsequent
-    # negation is well-defined regardless of the input representation.
-    rep = validate_matrix(input_rep, True)
-    result = negate_rows(input_rep, rep, row_values)
+    rep = validate_matrix(1, True)
+    result = negate_rows(1, rep, row_values)
     return result
     # impl-end
```

Attack 6 — `atk_6_prepatch_claimfloat.py` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -113,7 +112,6 @@
     modelled value carrier), so no value payload is threaded through."""
     Requires(0 <= input_rep and input_rep <= 2)
     # The validated representation is exactly the deeply-modelled one.
-    Requires(MustTerminate(2))
     Ensures(Result() == validated_rep(input_rep, request_floating))
     # Evidence that the matrix ACTUALLY has representation Result() now.
     Ensures(matrix_rep(input_rep, Result()))
@@ -142,7 +140,6 @@
     # The negation can only be performed when that actual representation
     # supports it (numpy `-` raises on a logical representation otherwise).
     Requires(supports_negation(rep))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(row_values), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The result is exactly the element-wise negation of the selected rows.
@@ -196,7 +193,6 @@
     # The input element representation is one of the three modelled kinds;
     # in particular it MAY be the logical representation (REP_LOGICAL == 0).
     Requires(0 <= input_rep and input_rep <= 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(row_values), 1 / 2))
@@ -218,9 +214,7 @@
     Ensures(negation_performed(input_rep, row_values))
     # post-conditions-end
     # impl-start
-    # Validation: request a floating representation so that the subsequent
-    # negation is well-defined regardless of the input representation.
-    rep = validate_matrix(input_rep, True)
-    result = negate_rows(input_rep, rep, row_values)
+    rep = validate_matrix(input_rep, False)
+    result = negate_rows(input_rep, 2, row_values)
     return result
     # impl-end
```

Attack 7 — `atk_7_unnegated.py` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -113,7 +112,6 @@
     modelled value carrier), so no value payload is threaded through."""
     Requires(0 <= input_rep and input_rep <= 2)
     # The validated representation is exactly the deeply-modelled one.
-    Requires(MustTerminate(2))
     Ensures(Result() == validated_rep(input_rep, request_floating))
     # Evidence that the matrix ACTUALLY has representation Result() now.
     Ensures(matrix_rep(input_rep, Result()))
@@ -142,7 +140,6 @@
     # The negation can only be performed when that actual representation
     # supports it (numpy `-` raises on a logical representation otherwise).
     Requires(supports_negation(rep))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(row_values), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The result is exactly the element-wise negation of the selected rows.
@@ -196,7 +193,6 @@
     # The input element representation is one of the three modelled kinds;
     # in particular it MAY be the logical representation (REP_LOGICAL == 0).
     Requires(0 <= input_rep and input_rep <= 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(row_values), 1 / 2))
@@ -218,9 +214,5 @@
     Ensures(negation_performed(input_rep, row_values))
     # post-conditions-end
     # impl-start
-    # Validation: request a floating representation so that the subsequent
-    # negation is well-defined regardless of the input representation.
-    rep = validate_matrix(input_rep, True)
-    result = negate_rows(input_rep, rep, row_values)
-    return result
+    return row_values
     # impl-end
```

Attack 8 — `atk_8_echo_branch.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -53,7 +53,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -113,7 +112,6 @@
     modelled value carrier), so no value payload is threaded through."""
     Requires(0 <= input_rep and input_rep <= 2)
     # The validated representation is exactly the deeply-modelled one.
-    Requires(MustTerminate(2))
     Ensures(Result() == validated_rep(input_rep, request_floating))
     # Evidence that the matrix ACTUALLY has representation Result() now.
     Ensures(matrix_rep(input_rep, Result()))
@@ -142,7 +140,6 @@
     # The negation can only be performed when that actual representation
     # supports it (numpy `-` raises on a logical representation otherwise).
     Requires(supports_negation(rep))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(row_values), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The result is exactly the element-wise negation of the selected rows.
@@ -196,7 +193,6 @@
     # The input element representation is one of the three modelled kinds;
     # in particular it MAY be the logical representation (REP_LOGICAL == 0).
     Requires(0 <= input_rep and input_rep <= 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(row_values), 1 / 2))
@@ -218,9 +214,10 @@
     Ensures(negation_performed(input_rep, row_values))
     # post-conditions-end
     # impl-start
-    # Validation: request a floating representation so that the subsequent
-    # negation is well-defined regardless of the input representation.
-    rep = validate_matrix(input_rep, True)
+    if input_rep == 0:
+        rep = validate_matrix(input_rep, True)
+    else:
+        rep = validate_matrix(input_rep, True)
     result = negate_rows(input_rep, rep, row_values)
     return result
     # impl-end
```

Attack 9 — `atk_9_float_only_logical.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -53,7 +53,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -113,7 +112,6 @@
     modelled value carrier), so no value payload is threaded through."""
     Requires(0 <= input_rep and input_rep <= 2)
     # The validated representation is exactly the deeply-modelled one.
-    Requires(MustTerminate(2))
     Ensures(Result() == validated_rep(input_rep, request_floating))
     # Evidence that the matrix ACTUALLY has representation Result() now.
     Ensures(matrix_rep(input_rep, Result()))
@@ -142,7 +140,6 @@
     # The negation can only be performed when that actual representation
     # supports it (numpy `-` raises on a logical representation otherwise).
     Requires(supports_negation(rep))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(row_values), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The result is exactly the element-wise negation of the selected rows.
@@ -196,7 +193,6 @@
     # The input element representation is one of the three modelled kinds;
     # in particular it MAY be the logical representation (REP_LOGICAL == 0).
     Requires(0 <= input_rep and input_rep <= 2)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(row_values), 1 / 2))
@@ -218,9 +214,9 @@
     Ensures(negation_performed(input_rep, row_values))
     # post-conditions-end
     # impl-start
-    # Validation: request a floating representation so that the subsequent
-    # negation is well-defined regardless of the input representation.
-    rep = validate_matrix(input_rep, True)
+    # Request floating ONLY for the logical input; integral/floating
+    # inputs already support negation without coercion.
+    rep = validate_matrix(input_rep, input_rep == 0)
     result = negate_rows(input_rep, rep, row_values)
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-13328.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the robust linear-regression estimator is fitted, the training feature
  matrix is first run through the input-validation step, which coerces it to a
  concrete element representation. Later, the gradient computation forms the
  *negation* of the rows of the (validated) feature matrix that are not
  treated as outliers.

  Element-wise negation of the validated matrix is well-defined for a
  floating-point element representation but RAISES for a logical (true/false)
  element representation: forming the negation is an operation that can FAIL,
  and whether it fails is determined by the element representation, not by the
  element values (the negated values would be identical either way). The
  desired behaviour is therefore:

    For ANY input element representation that the caller may supply -- including
    the logical (true/false) representation -- fitting must SUCCEED: the
    negation step must actually run to completion without raising. Concretely,
    the validation step must produce a validated matrix whose element
    representation supports negation, so that the subsequent gradient step is
    actually performed (not skipped, not raised) for every input.

The feature matrix is modelled as a `List[int]` of element values (the rows
selected for the squared-loss gradient, flattened), together with an integer
"element representation" tag. Three representations are modelled: the logical
representation `REP_LOGICAL == 0`, the integral representation
`REP_INTEGRAL == 1`, and the floating representation `REP_FLOATING == 2`.

`validated_rep` is the (deeply-modelled) representation produced by the
validation step, parameterised by whether a floating representation was
requested of the validator. `validate_matrix` is the validation step itself:
the only way to establish -- via the unforgeable capability token
`matrix_rep(input_rep, rep)` -- what element representation the matrix
ACTUALLY has after validation. `negate_rows` is the gradient step: the
negation operation that can only be performed when the matrix ACTUALLY HAS
(token-evidenced) a representation that supports negation (its precondition
can raise otherwise), which returns the element-wise negation, and which --
as evidence that the negation was ACTUALLY carried out for this input on
these very rows -- grants the unforgeable capability token
`negation_performed(input_rep, rows)`.
`fit_robust_regressor` is the modelled fitting routine: it validates then
negates, and its contract requires, for EVERY input representation, both the
element-wise negation result AND the `negation_performed` token for its own
rows -- so a verifying implementation must have actually run the negation
step on the caller's own rows, on a matrix whose ACTUAL representation
supports negation (which is only possible after validation coerced it to a
negation-supporting representation), for every input including the logical
one.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# Unforgeable capability token marking that the negation step was ACTUALLY
# CARRIED OUT, for a matrix that originated from the input representation
# `input_rep`, ON EXACTLY the row collection `rows` (the very selected
# row-slice the gradient step negates -- the reference itself, not merely
# something with equal contents). It is an abstract `@ContractOnly
# @Predicate` with NO body, so nothing can `Fold` it into existence: the ONLY
# producer is `negate_rows`'s postcondition (below), and `negate_rows` can
# only be entered with token evidence (`matrix_rep`) that the matrix ACTUALLY
# has a representation for which `supports_negation` holds. The token
# therefore certifies a control-flow effect -- "the negation ran to
# completion for this input, on these rows, rather than raising" -- that no
# value-level postcondition can witness (the negated values are identical
# whether the negation raises or not). Binding the `rows` reference into the
# token means it cannot be earned by negating some OTHER row collection (an
# empty stand-in, a copy, ...) while the caller's own rows are handled by a
# different route. `fit_robust_regressor`'s postcondition requires this token
# for its own `input_rep` and its own row collection, so the negation step is
# mandatory and cannot be inlined/bypassed. Provenance + soundness check:
# mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def negation_performed(input_rep: int, rows: List[int]) -> bool:
    pass

# Unforgeable capability token stating that the matrix originating from the
# input representation `input_rep` ACTUALLY HAS the element representation
# `rep` at this point -- i.e. the validation step ran on it and produced a
# matrix of representation `rep`. Abstract `@ContractOnly @Predicate` with NO
# body, so nothing can `Fold` it into existence: the ONLY producer is
# `validate_matrix`'s postcondition (below). It exists so the representation
# tag handed to the negation step CANNOT BE FABRICATED: without it, an
# implementation could pass an arbitrary negation-supporting tag while the
# matrix it negates still has a representation for which the negation is
# undefined -- claiming a success the operation would not deliver. Provenance
# + soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def matrix_rep(input_rep: int, rep: int) -> bool:
    pass

@ContractOnly
def validate_matrix(input_rep: int, request_floating: bool) -> int:
    """The input-validation step: the routine the fitting code runs the
    feature matrix through before any gradient work, parameterised by whether
    a floating representation is requested of it. Its result is the element
    representation of the VALIDATED matrix -- exactly the deep model
    `validated_rep` (validated == the real validation callee out-of-band by
    axiom_check.py / G-AX) -- and it grants the unforgeable
    `matrix_rep(input_rep, Result())` token: the evidence that the matrix now
    ACTUALLY HAS that representation (the sole producer of that token).
    Element values are preserved by the validation coercion (identity on the
    modelled value carrier), so no value payload is threaded through."""
    Requires(0 <= input_rep and input_rep <= 2)
    # The validated representation is exactly the deeply-modelled one.
    Ensures(Result() == validated_rep(input_rep, request_floating))
    # Evidence that the matrix ACTUALLY has representation Result() now.
    Ensures(matrix_rep(input_rep, Result()))

@ContractOnly
def negate_rows(input_rep: int, rep: int, row_values: List[int]) -> List[int]:
    """The gradient negation step (the downstream numpy unary `-` on the
    validated row-slice). It is an operation that CAN RAISE: it can only be
    carried out when the representation the matrix ACTUALLY has at this point
    supports negation. Both halves of that claim are demanded as evidence:
    the unforgeable `matrix_rep(input_rep, rep)` token (the matrix really has
    representation `rep` -- only the validation step can grant it) and
    `supports_negation(rep)` (negation is defined for that representation).
    On success it returns the element-wise negation of the selected rows AND
    grants the `negation_performed(input_rep, row_values)` token, the
    evidence that the negation actually ran for a matrix originating from
    `input_rep` on exactly these row values (the sole producer of that token).
    Provenance + executable soundness check: mapping.md / axiom_check.py (the
    value model `negated` and the definedness model `supports_negation` are
    validated == numpy)."""
    Requires(Acc(list_pred(row_values), 1 / 2))
    # The matrix must ACTUALLY have representation `rep` here: unforgeable
    # evidence from the validation step, so the tag cannot be fabricated.
    Requires(matrix_rep(input_rep, rep))
    # The negation can only be performed when that actual representation
    # supports it (numpy `-` raises on a logical representation otherwise).
    Requires(supports_negation(rep))
    Ensures(Acc(list_pred(row_values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the element-wise negation of the selected rows.
    Ensures(ToSeq(Result()) == negated(ToSeq(row_values)))
    # Evidence that the negation was ACTUALLY performed for `input_rep` on
    # exactly this row collection.
    Ensures(negation_performed(input_rep, row_values))
# axioms-end

# pure-start
@Pure
def supports_negation(rep: int) -> bool:
    """True iff element-wise negation is defined for the element
    representation `rep`. The logical (true/false) representation does not
    support negation (the operation raises); integral and floating
    representations do."""
    return rep != 0  # REP_LOGICAL == 0

@Pure
def validated_rep(input_rep: int, request_floating: bool) -> int:
    """The element representation of the matrix produced by validation, given
    the input representation `input_rep` and whether a floating representation
    was requested of the validator.

    - If a floating representation is requested, every input representation is
      coerced to the floating representation (`REP_FLOATING == 2`).
    - Otherwise the input representation is preserved unchanged (a logical
      input stays logical, an integral input stays integral, etc.).
    """
    if request_floating:
        return 2  # REP_FLOATING
    return input_rep

@Pure
def negated(vals: PSeq[int]) -> PSeq[int]:
    """Element-wise negation of the whole sequence. Front-recursive over
    `PSeq` (recurses on `vals.drop(1)`) so a single unfold is available to
    callers per loop step."""
    if len(vals) == 0:
        return PSeq(0).take(0)
    return PSeq(-vals[0]) + negated(vals.drop(1))
# pure-end

def fit_robust_regressor(input_rep: int, row_values: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(row_values), 1 / 2))
    # The input element representation is one of the three modelled kinds;
    # in particular it MAY be the logical representation (REP_LOGICAL == 0).
    Requires(0 <= input_rep and input_rep <= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(row_values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Fitting returns the element-wise negation of the selected rows (the result
    # is pinned to a structural function of the input, not an oracle).
    Ensures(ToSeq(Result()) == negated(ToSeq(row_values)))
    # AND, for EVERY input representation including the logical one, the negation
    # step must have ACTUALLY been performed (it must run, not raise) ON THESE
    # VERY row values: the result must carry the
    # `negation_performed(input_rep, row_values)` token. Because that
    # token is only granted by the negation step for the rows it actually
    # serviced -- and the negation step is only reachable with token evidence
    # that the matrix ACTUALLY has a negation-supporting representation, itself
    # only grantable by the validation step -- this forces the validation to
    # coerce a logical input before the (mandatory, non-bypassable) negation of
    # the caller's own rows. No implementation can satisfy this without doing
    # the coercion, for the logical input too.
    Ensures(negation_performed(input_rep, row_values))
    # post-conditions-end
    # impl-start
    request_float = True
    rep = validate_matrix(input_rep, request_float)
    result = negate_rows(input_rep, rep, row_values)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for scikit-learn__scikit-learn-13328 (nagini). Spec freeze confirmed via markers.py: only the impl region (model.py lines 216-222) is mutable; axioms/@Pure/pre/post are byte-identical across all attacks. All 10 files passed `adversary same-spec` (exit 0).

### 9 attacks, `adversary weakness nagini scikit-learn__scikit-learn-13328 <path>`
(1) atk_1_prepatch (validate_matrix(input_rep, False)) => NOT-A-COUNTEREXAMPLE, does not verify (fails supports_negation(rep) precondition of negate_rows for logical input) — REPRODUCES THE PREPATCH BUG (prepatch_reproduced=true; matches model_prepatch.py). exit 2.

(2) atk_2_boundary (float only when input_rep>=1) => NOT-A-COUNTEREXAMPLE, fails to verify (logical boundary input_rep=0 keeps rep=0, no supports_negation). exit 2.

(3) atk_3_ctrlflow_branch (prepatch route on the bool branch) => NOT-A-COUNTEREXAMPLE, fails on the logical branch (control-flow-effect attack). exit 2.

(4) atk_4_novalidation_consttag (skip validation, negate_rows(input_rep,2,...)) => NOT-A-COUNTEREXAMPLE, fails: no matrix_rep(input_rep,2) evidence held (ungrounded-oracle echo). exit 2.

(5) atk_5_const_inputrep (validate_matrix(1,True); negate_rows(1,...)) => NOT-A-COUNTEREXAMPLE, fails: token negation_performed(1,rows) != required negation_performed(input_rep,rows). exit 2.

(6) atk_6_prepatch_claimfloat (validate_matrix(input_rep,False); negate_rows(input_rep,2,...)) => NOT-A-COUNTEREXAMPLE, fails: matrix_rep held names the preserved rep, not the claimed 2. exit 2.

(7) atk_7_unnegated (return row_values) => NOT-A-COUNTEREXAMPLE, fails value postcondition + token. exit 2.

(8) atk_8_echo_branch (dead branch, always floating) => CANDIDATE (shares spec AND verifies, ~s). Faithful patch = unconditional gold dtype coercion.

(9) atk_9_float_only_logical (validate_matrix(input_rep, input_rep==0): request floating ONLY for the logical input — sharpest near-miss, since integral/float already support negation without coercion) => CANDIDATE (verifies, 16.5s). Faithful patch = CONDITIONAL coercion (coerce to float64/float32 only when X.dtype==bool, else 'numeric').
positive control pos_control (structurally-different correct always-floating impl) => verifies (CANDIDATE; non-vacuity confirmed).

== Materialized faithful patches run through the OFFICIAL harness (run_resolve, SWE-bench_Verified, image swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-13328:latest, base 06bc86b3b) ==
Both distinct patch texts apply cleanly (git apply --check OK) and RESOLVE:
  - gold_uncond (faithful for BOTH atk_8_echo and pos_control; == patch.diff verbatim): {resolved:true, completed:true, attempts:1, flaky:false, note:'resolved'}.
  - atk9_conditional (faithful for atk_9): {resolved:true, completed:true, attempts:1, flaky:false, note:'resolved'}.
Every verifying candidate's faithful refined patch RESOLVES => verify does NOT admit an unresolved impl. No BROKEN witness found.

### A-leg / refinement.md audit (§4 focus)
G-AX re-run: axiom_check.py exit 0 — validated_rep / supports_negation / negated deep models == real sklearn.utils.check_array + numpy negation over 6 rep×request combos, 5000 negation fuzz inputs, and the end-to-end patched/prepatch contract.
  - A3 validate_matrix (A-consumed + A-reference): axiomatizes the UNCHANGED check_X_y/check_array callee; the changed thing is the argument (impl-region literal True ⇔ dtype=[np.float64,np.float32]); value clause pinned to G-AX-validated validated_rep; matrix_rep token grounded. Correspondence holds.
  - A4 negate_rows (A-consumed + R): axiomatizes the UNCHANGED numpy unary '-' (huber.py:93); preconditions matrix_rep + supports_negation, postconditions negated + negation_performed, all grounded by G-AX-validated deep models. Correspondence holds.
  - §C no-kind-3 confirmed: every leg is R / A-consumed / A-reference / I; the genuinely-changed op (dtype arg + negation consequence) is captured by the impl-region argument to validate_matrix and negate_rows' preconditions, not an inexpressible changed op.
The two capability tokens (matrix_rep, negation_performed — bodyless @ContractOnly @Predicate, un-Fold-able, sole producers validate_matrix/negate_rows, row-reference-bound) close the two prior soundness holes: every verifying impl must route the caller's own row_values through a real validation choice that yields a supports_negation rep for EVERY input including logical (input_rep=0), which is only obtainable via validate_matrix(0,True)=2. Confirmed by the 7 rejected wrong impls covering partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, token-laundering (constant input_rep), and claimed-tag classes.

VERDICT: SOUND. 9 attacks run (≥5 distinct wrong-impl classes + prepatch reproduced); all 7 genuinely-wrong impls rejected by the verifier; the 3 verifying candidates are all behaviourally-correct and their (2 distinct) faithful patches both RESOLVE under the official harness. verify ⇒ correct on this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_boundary.py`, `atk_3_ctrlflow_branch.py`, `atk_4_novalidation_consttag.py`, `atk_5_const_inputrep.py`, `atk_6_prepatch_claimfloat.py`, `atk_7_unnegated.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8_echo_branch.py`, `atk_9_float_only_logical.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_boundary.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_ctrlflow_branch.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_novalidation_consttag.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_const_inputrep.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_prepatch_claimfloat.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_unnegated.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_echo_branch.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_float_only_logical.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-13328.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the robust linear-regression estimator is fitted, the training feature
  matrix is first run through the input-validation step, which coerces it to a
  concrete element representation. Later, the gradient computation forms the
  *negation* of the rows of the (validated) feature matrix that are not
  treated as outliers.

  Element-wise negation of the validated matrix is well-defined for a
  floating-point element representation but RAISES for a logical (true/false)
  element representation: forming the negation is an operation that can FAIL,
  and whether it fails is determined by the element representation, not by the
  element values (the negated values would be identical either way). The
  desired behaviour is therefore:

    For ANY input element representation that the caller may supply -- including
    the logical (true/false) representation -- fitting must SUCCEED: the
    negation step must actually run to completion without raising. Concretely,
    the validation step must produce a validated matrix whose element
    representation supports negation, so that the subsequent gradient step is
    actually performed (not skipped, not raised) for every input.

The feature matrix is modelled as a `List[int]` of element values (the rows
selected for the squared-loss gradient, flattened), together with an integer
"element representation" tag. Three representations are modelled: the logical
representation `REP_LOGICAL == 0`, the integral representation
`REP_INTEGRAL == 1`, and the floating representation `REP_FLOATING == 2`.

`validated_rep` is the (deeply-modelled) representation produced by the
validation step, parameterised by whether a floating representation was
requested of the validator. `validate_matrix` is the validation step itself:
the only way to establish -- via the unforgeable capability token
`matrix_rep(input_rep, rep)` -- what element representation the matrix
ACTUALLY has after validation. `negate_rows` is the gradient step: the
negation operation that can only be performed when the matrix ACTUALLY HAS
(token-evidenced) a representation that supports negation (its precondition
can raise otherwise), which returns the element-wise negation, and which --
as evidence that the negation was ACTUALLY carried out for this input on
these very rows -- grants the unforgeable capability token
`negation_performed(input_rep, rows)`.
`fit_robust_regressor` is the modelled fitting routine: it validates then
negates, and its contract requires, for EVERY input representation, both the
element-wise negation result AND the `negation_performed` token for its own
rows -- so a verifying implementation must have actually run the negation
step on the caller's own rows, on a matrix whose ACTUAL representation
supports negation (which is only possible after validation coerced it to a
negation-supporting representation), for every input including the logical
one.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# Unforgeable capability token marking that the negation step was ACTUALLY
# CARRIED OUT, for a matrix that originated from the input representation
# `input_rep`, ON EXACTLY the row collection `rows` (the very selected
# row-slice the gradient step negates -- the reference itself, not merely
# something with equal contents). It is an abstract `@ContractOnly
# @Predicate` with NO body, so nothing can `Fold` it into existence: the ONLY
# producer is `negate_rows`'s postcondition (below), and `negate_rows` can
# only be entered with token evidence (`matrix_rep`) that the matrix ACTUALLY
# has a representation for which `supports_negation` holds. The token
# therefore certifies a control-flow effect -- "the negation ran to
# completion for this input, on these rows, rather than raising" -- that no
# value-level postcondition can witness (the negated values are identical
# whether the negation raises or not). Binding the `rows` reference into the
# token means it cannot be earned by negating some OTHER row collection (an
# empty stand-in, a copy, ...) while the caller's own rows are handled by a
# different route. `fit_robust_regressor`'s postcondition requires this token
# for its own `input_rep` and its own row collection, so the negation step is
# mandatory and cannot be inlined/bypassed. Provenance + soundness check:
# mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def negation_performed(input_rep: int, rows: List[int]) -> bool:
    pass

# Unforgeable capability token stating that the matrix originating from the
# input representation `input_rep` ACTUALLY HAS the element representation
# `rep` at this point -- i.e. the validation step ran on it and produced a
# matrix of representation `rep`. Abstract `@ContractOnly @Predicate` with NO
# body, so nothing can `Fold` it into existence: the ONLY producer is
# `validate_matrix`'s postcondition (below). It exists so the representation
# tag handed to the negation step CANNOT BE FABRICATED: without it, an
# implementation could pass an arbitrary negation-supporting tag while the
# matrix it negates still has a representation for which the negation is
# undefined -- claiming a success the operation would not deliver. Provenance
# + soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def matrix_rep(input_rep: int, rep: int) -> bool:
    pass

@ContractOnly
def validate_matrix(input_rep: int, request_floating: bool) -> int:
    """The input-validation step: the routine the fitting code runs the
    feature matrix through before any gradient work, parameterised by whether
    a floating representation is requested of it. Its result is the element
    representation of the VALIDATED matrix -- exactly the deep model
    `validated_rep` (validated == the real validation callee out-of-band by
    axiom_check.py / G-AX) -- and it grants the unforgeable
    `matrix_rep(input_rep, Result())` token: the evidence that the matrix now
    ACTUALLY HAS that representation (the sole producer of that token).
    Element values are preserved by the validation coercion (identity on the
    modelled value carrier), so no value payload is threaded through."""
    Requires(0 <= input_rep and input_rep <= 2)
    # The validated representation is exactly the deeply-modelled one.
    Ensures(Result() == validated_rep(input_rep, request_floating))
    # Evidence that the matrix ACTUALLY has representation Result() now.
    Ensures(matrix_rep(input_rep, Result()))

@ContractOnly
def negate_rows(input_rep: int, rep: int, row_values: List[int]) -> List[int]:
    """The gradient negation step (the downstream numpy unary `-` on the
    validated row-slice). It is an operation that CAN RAISE: it can only be
    carried out when the representation the matrix ACTUALLY has at this point
    supports negation. Both halves of that claim are demanded as evidence:
    the unforgeable `matrix_rep(input_rep, rep)` token (the matrix really has
    representation `rep` -- only the validation step can grant it) and
    `supports_negation(rep)` (negation is defined for that representation).
    On success it returns the element-wise negation of the selected rows AND
    grants the `negation_performed(input_rep, row_values)` token, the
    evidence that the negation actually ran for a matrix originating from
    `input_rep` on exactly these row values (the sole producer of that token).
    Provenance + executable soundness check: mapping.md / axiom_check.py (the
    value model `negated` and the definedness model `supports_negation` are
    validated == numpy)."""
    Requires(Acc(list_pred(row_values), 1 / 2))
    # The matrix must ACTUALLY have representation `rep` here: unforgeable
    # evidence from the validation step, so the tag cannot be fabricated.
    Requires(matrix_rep(input_rep, rep))
    # The negation can only be performed when that actual representation
    # supports it (numpy `-` raises on a logical representation otherwise).
    Requires(supports_negation(rep))
    Ensures(Acc(list_pred(row_values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the element-wise negation of the selected rows.
    Ensures(ToSeq(Result()) == negated(ToSeq(row_values)))
    # Evidence that the negation was ACTUALLY performed for `input_rep` on
    # exactly this row collection.
    Ensures(negation_performed(input_rep, row_values))
# axioms-end

# pure-start
@Pure
def supports_negation(rep: int) -> bool:
    """True iff element-wise negation is defined for the element
    representation `rep`. The logical (true/false) representation does not
    support negation (the operation raises); integral and floating
    representations do."""
    return rep != 0  # REP_LOGICAL == 0

@Pure
def validated_rep(input_rep: int, request_floating: bool) -> int:
    """The element representation of the matrix produced by validation, given
    the input representation `input_rep` and whether a floating representation
    was requested of the validator.

    - If a floating representation is requested, every input representation is
      coerced to the floating representation (`REP_FLOATING == 2`).
    - Otherwise the input representation is preserved unchanged (a logical
      input stays logical, an integral input stays integral, etc.).
    """
    if request_floating:
        return 2  # REP_FLOATING
    return input_rep

@Pure
def negated(vals: PSeq[int]) -> PSeq[int]:
    """Element-wise negation of the whole sequence. Front-recursive over
    `PSeq` (recurses on `vals.drop(1)`) so a single unfold is available to
    callers per loop step."""
    if len(vals) == 0:
        return PSeq(0).take(0)
    return PSeq(-vals[0]) + negated(vals.drop(1))
# pure-end

def fit_robust_regressor(input_rep: int, row_values: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(row_values), 1 / 2))
    # The input element representation is one of the three modelled kinds;
    # in particular it MAY be the logical representation (REP_LOGICAL == 0).
    Requires(0 <= input_rep and input_rep <= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(row_values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Fitting returns the element-wise negation of the selected rows (the result
    # is pinned to a structural function of the input, not an oracle).
    Ensures(ToSeq(Result()) == negated(ToSeq(row_values)))
    # AND, for EVERY input representation including the logical one, the negation
    # step must have ACTUALLY been performed (it must run, not raise) ON THESE
    # VERY row values: the result must carry the
    # `negation_performed(input_rep, row_values)` token. Because that
    # token is only granted by the negation step for the rows it actually
    # serviced -- and the negation step is only reachable with token evidence
    # that the matrix ACTUALLY has a negation-supporting representation, itself
    # only grantable by the validation step -- this forces the validation to
    # coerce a logical input before the (mandatory, non-bypassable) negation of
    # the caller's own rows. No implementation can satisfy this without doing
    # the coercion, for the logical input too.
    Ensures(negation_performed(input_rep, row_values))
    # post-conditions-end
    # impl-start
    request_float = True
    rep = validate_matrix(input_rep, request_float)
    result = negate_rows(input_rep, rep, row_values)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for scikit-learn__scikit-learn-13328 (nagini). Spec freeze confirmed via markers.py: only the impl region (model.py lines 216-222) is mutable; axioms/@Pure/pre/post are byte-identical across all attacks. All 10 files passed `adversary same-spec` (exit 0).

### 9 attacks, `adversary weakness nagini scikit-learn__scikit-learn-13328 <path>`
(1) atk_1_prepatch (validate_matrix(input_rep, False)) => NOT-A-COUNTEREXAMPLE, does not verify (fails supports_negation(rep) precondition of negate_rows for logical input) — REPRODUCES THE PREPATCH BUG (prepatch_reproduced=true; matches model_prepatch.py). exit 2.

(2) atk_2_boundary (float only when input_rep>=1) => NOT-A-COUNTEREXAMPLE, fails to verify (logical boundary input_rep=0 keeps rep=0, no supports_negation). exit 2.

(3) atk_3_ctrlflow_branch (prepatch route on the bool branch) => NOT-A-COUNTEREXAMPLE, fails on the logical branch (control-flow-effect attack). exit 2.

(4) atk_4_novalidation_consttag (skip validation, negate_rows(input_rep,2,...)) => NOT-A-COUNTEREXAMPLE, fails: no matrix_rep(input_rep,2) evidence held (ungrounded-oracle echo). exit 2.

(5) atk_5_const_inputrep (validate_matrix(1,True); negate_rows(1,...)) => NOT-A-COUNTEREXAMPLE, fails: token negation_performed(1,rows) != required negation_performed(input_rep,rows). exit 2.

(6) atk_6_prepatch_claimfloat (validate_matrix(input_rep,False); negate_rows(input_rep,2,...)) => NOT-A-COUNTEREXAMPLE, fails: matrix_rep held names the preserved rep, not the claimed 2. exit 2.

(7) atk_7_unnegated (return row_values) => NOT-A-COUNTEREXAMPLE, fails value postcondition + token. exit 2.

(8) atk_8_echo_branch (dead branch, always floating) => CANDIDATE (shares spec AND verifies, ~s). Faithful patch = unconditional gold dtype coercion.

(9) atk_9_float_only_logical (validate_matrix(input_rep, input_rep==0): request floating ONLY for the logical input — sharpest near-miss, since integral/float already support negation without coercion) => CANDIDATE (verifies, 16.5s). Faithful patch = CONDITIONAL coercion (coerce to float64/float32 only when X.dtype==bool, else 'numeric').
positive control pos_control (structurally-different correct always-floating impl) => verifies (CANDIDATE; non-vacuity confirmed).

== Materialized faithful patches run through the OFFICIAL harness (run_resolve, SWE-bench_Verified, image swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-13328:latest, base 06bc86b3b) ==
Both distinct patch texts apply cleanly (git apply --check OK) and RESOLVE:
  - gold_uncond (faithful for BOTH atk_8_echo and pos_control; == patch.diff verbatim): {resolved:true, completed:true, attempts:1, flaky:false, note:'resolved'}.
  - atk9_conditional (faithful for atk_9): {resolved:true, completed:true, attempts:1, flaky:false, note:'resolved'}.
Every verifying candidate's faithful refined patch RESOLVES => verify does NOT admit an unresolved impl. No BROKEN witness found.

### A-leg / refinement.md audit (§4 focus)
G-AX re-run: axiom_check.py exit 0 — validated_rep / supports_negation / negated deep models == real sklearn.utils.check_array + numpy negation over 6 rep×request combos, 5000 negation fuzz inputs, and the end-to-end patched/prepatch contract.
  - A3 validate_matrix (A-consumed + A-reference): axiomatizes the UNCHANGED check_X_y/check_array callee; the changed thing is the argument (impl-region literal True ⇔ dtype=[np.float64,np.float32]); value clause pinned to G-AX-validated validated_rep; matrix_rep token grounded. Correspondence holds.
  - A4 negate_rows (A-consumed + R): axiomatizes the UNCHANGED numpy unary '-' (huber.py:93); preconditions matrix_rep + supports_negation, postconditions negated + negation_performed, all grounded by G-AX-validated deep models. Correspondence holds.
  - §C no-kind-3 confirmed: every leg is R / A-consumed / A-reference / I; the genuinely-changed op (dtype arg + negation consequence) is captured by the impl-region argument to validate_matrix and negate_rows' preconditions, not an inexpressible changed op.
The two capability tokens (matrix_rep, negation_performed — bodyless @ContractOnly @Predicate, un-Fold-able, sole producers validate_matrix/negate_rows, row-reference-bound) close the two prior soundness holes: every verifying impl must route the caller's own row_values through a real validation choice that yields a supports_negation rep for EVERY input including logical (input_rep=0), which is only obtainable via validate_matrix(0,True)=2. Confirmed by the 7 rejected wrong impls covering partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, token-laundering (constant input_rep), and claimed-tag classes.

VERDICT: SOUND. 9 attacks run (≥5 distinct wrong-impl classes + prepatch reproduced); all 7 genuinely-wrong impls rejected by the verifier; the 3 verifying candidates are all behaviourally-correct and their (2 distinct) faithful patches both RESOLVE under the official harness. verify ⇒ correct on this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee) checked rigorously; no divergence found. Deep models validated against the real callees:

1) validated_rep == sklearn.utils.check_array dtype-selection: verified over all 3 representations x {request_floating False/True}. Confirmed BOTH against host sklearn via axiom_check.py (G-AX exit 0) AND directly against base-commit source (sklearn/utils/validation.py:439-466,496,535 — default dtype='numeric' leaves bool/int/float unchanged; list dtype [float64,float32] not containing the input dtype selects float64) and via executable check with importable sklearn: all 6 combos OK (ir=0 rf=False->0, ir=0 rf=True->2, ir=1 rf=False->1, ir=1 rf=True->2, ir=2 either->2).
2) supports_negation == numpy unary '-' definedness: rep=0 (bool) False/real False, rep=1/2 True/real True — matches numpy raising TypeError on bool negation, succeeding on int/float.
3) negated == numpy element-wise negation: 5000-input fuzz, all match.

End-to-end: the modeled contract (for EVERY input_rep in {0,1,2} incl. logical, validation yields a negation-supporting rep and the negation runs) is exactly the gold-patched real behavior (check_X_y(..., dtype=[np.float64,np.float32]) coerces bool->float64 so -axis0_safe_slice never raises). Pre-patch behavior (default dtype leaves bool as bool -> TypeError at huber.py:93) is faithfully reproduced by model_prepatch.py (validate_matrix(ir, False) -> supports_negation(0) unsatisfiable). The spec does not over-demand: it requires exactly what the gold-patched callee delivers.

Domain: precondition 0<=input_rep<=2 restricts to the three modeled dtype kinds (bool/int/float) — a legitimate abstraction of the real fit's input domain, not a strengthening; within the modeled domain the modeled functions agree with the real callees on every input. The capability tokens (matrix_rep, negation_performed) are value-free @ContractOnly @Predicates whose only producers are the axiomatized callees; they add no claim the real callees don't support (soundness reduces to the A-reference deep models, all G-AX-validated). model.py verifies (Nagini, 14.1s). No input where the modeled function disagrees with the real repo callee exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-LEAK mechanical screen PASSES (status=pass, 'spec view clean'); I re-ran it and confirmed independently. Manual leakage review of the consumer spec view (model.py projection with impl elided):

Gold edit = adding `dtype=[np.float64, np.float32]` to the `check_X_y(...)` call in HuberRegressor.fit (sklearn/linear_model/huber.py), forcing bool->float coercion so `-axis0_safe_slice(X, ...)` no longer raises.

What the PUBLIC problem_statement already discloses: the TypeError on numpy boolean negation of X in huber.py fit (full traceback pinning huber.py:93 gradient step), and the expected fix in plain words: 'Boolean array is expected to be converted to float by HuberRegressor.fit as it is done by LinearRegression.'

Spec-view checks:
- No gold-patch line, diff marker, patched file path, or patched module path appears in the spec view (mechanical L1/L2 clean).
- No repo symbol tied to the edit is named: check_X_y/check_array, dtype, np.float64, np.float32 do NOT appear anywhere in the view. The identifiers validate_matrix, negate_rows, validated_rep, matrix_rep, supports_negation, negation_performed are the modeler's own abstractions, not repo identifiers, so they localize nothing.
- No bug/fix narration in spec-view comments (L3 clean).
- The abstract behavioral claim ('validation must coerce any input element representation -- including the logical/true-false one -- to a representation that supports negation, so the gradient negation runs rather than raises') is a faithful restatement of the publicly-expected behavior (convert bool to float so fit does not raise). It does NOT reveal the specific edit (which callee, which kwarg, which dtypes).

The heavy verbatim gold-patch quoting (the `check_X_y(..., dtype=[np.float64, np.float32])` hunk, huber.py line numbers) lives only in refinement.md and mapping.md, which are AUDIT documents, not the consumer spec view, and are not consumer-visible / not screened by G-LEAK.

Conclusion: the spec view leaks nothing about the gold edit beyond what the public problem_statement already states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.