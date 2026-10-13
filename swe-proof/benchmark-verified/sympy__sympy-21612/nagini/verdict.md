# P2 adversarial audit — sympy__sympy-21612

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.py`, `atk_form_ge1.py`, `atk_parts_gt1.py`, `atk_form_only.py`, `atk_const_true.py`, `atk_swap.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Factor:
@@ -76,7 +75,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
         Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
         [[factors[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -108,10 +106,9 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == needs_brackets(factors[k].parts, factors[k].form)),
             [[result[k]], [factors[k]]])))
-        Invariant(MustTerminate(len(factors) - i + 1))
         # invariants-end
         f = factors[i]
-        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
+        flag = f.parts != 1 and (f.form == 1)
         result.append(flag)
         i = i + 1
     return result
```

Attack 2 — `atk_form_ge1.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Factor:
@@ -76,7 +75,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
         Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
         [[factors[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -108,10 +106,9 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == needs_brackets(factors[k].parts, factors[k].form)),
             [[result[k]], [factors[k]]])))
-        Invariant(MustTerminate(len(factors) - i + 1))
         # invariants-end
         f = factors[i]
-        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
+        flag = f.parts != 1 and f.form >= 1
         result.append(flag)
         i = i + 1
     return result
```

Attack 3 — `atk_parts_gt1.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Factor:
@@ -76,7 +75,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
         Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
         [[factors[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -108,10 +106,9 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == needs_brackets(factors[k].parts, factors[k].form)),
             [[result[k]], [factors[k]]])))
-        Invariant(MustTerminate(len(factors) - i + 1))
         # invariants-end
         f = factors[i]
-        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
+        flag = f.parts > 1 and (f.form == 1 or f.form == 2)
         result.append(flag)
         i = i + 1
     return result
```

Attack 4 — `atk_form_only.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Factor:
@@ -76,7 +75,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
         Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
         [[factors[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -108,10 +106,9 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == needs_brackets(factors[k].parts, factors[k].form)),
             [[result[k]], [factors[k]]])))
-        Invariant(MustTerminate(len(factors) - i + 1))
         # invariants-end
         f = factors[i]
-        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
+        flag = (f.form == 1 or f.form == 2)
         result.append(flag)
         i = i + 1
     return result
```

Attack 5 — `atk_const_true.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Factor:
@@ -76,7 +75,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
         Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
         [[factors[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -108,10 +106,9 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == needs_brackets(factors[k].parts, factors[k].form)),
             [[result[k]], [factors[k]]])))
-        Invariant(MustTerminate(len(factors) - i + 1))
         # invariants-end
         f = factors[i]
-        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
+        flag = True
         result.append(flag)
         i = i + 1
     return result
```

Attack 6 — `atk_swap.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Factor:
@@ -76,7 +75,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
         Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
         [[factors[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -108,10 +106,9 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == needs_brackets(factors[k].parts, factors[k].form)),
             [[result[k]], [factors[k]]])))
-        Invariant(MustTerminate(len(factors) - i + 1))
         # invariants-end
         f = factors[i]
-        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
+        flag = f.form != 1 and (f.parts == 1 or f.parts == 2)
         result.append(flag)
         i = i + 1
     return result
```

Attack 7 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Factor:
@@ -76,7 +75,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
         Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
         [[factors[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(factors), 1 / 2))
@@ -108,10 +106,9 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == needs_brackets(factors[k].parts, factors[k].form)),
             [[result[k]], [factors[k]]])))
-        Invariant(MustTerminate(len(factors) - i + 1))
         # invariants-end
         f = factors[i]
-        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
+        flag = needs_brackets(f.parts, f.form)
         result.append(flag)
         i = i + 1
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-21612.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A quotient is rendered as a numerator followed by a sequence of denominator
  factors joined by the division operator. To keep the rendered text from being
  misread as iterated left-to-right division, each denominator factor that is
  itself a *composite* reciprocal must be wrapped in brackets; a factor that is
  a single atomic symbol is left bare.

  A denominator factor is "composite" exactly when BOTH of the following hold:

    (1) the reciprocated quantity is built from more than one part (its part
        count differs from one); and
    (2) that quantity's structural form is a multiplicative or a power form
        (i.e. a product of factors, or a base raised to an exponent) rather
        than a bare atom.

  When both hold the factor is bracketed; otherwise it is not. The decision is
  taken independently for every denominator factor, and the result is the list
  of per-factor bracket flags in factor order.

Each denominator factor is modelled as a minimal class carrying only the two
touched facets used by the decision: the part count of the reciprocated
quantity (a non-negative int) and an integer tag for its structural form
(0 = atomic, 1 = product, 2 = power). The element payload is irrelevant to the
bracketing behaviour under specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Factor:
    """A single denominator factor, abstracted to the two facets the bracketing
    decision inspects: ``parts`` (the part count of the reciprocated quantity)
    and ``form`` (its structural form tag: 0 atomic, 1 product, 2 power)."""

    def __init__(self, parts: int, form: int) -> None:
        Requires(parts >= 0 and form >= 0)
        Ensures(Acc(self.parts) and self.parts == parts)   # type: ignore
        Ensures(Acc(self.form) and self.form == form)       # type: ignore
        self.parts = parts
        self.form = form


# axioms-start
# (no @ContractOnly axioms: the structural-form test and the part-count test
#  the decision performs are modelled deeply as integer/boolean reasoning over
#  the abstracted facets — see refinement.md, all rows are R or I.)
# axioms-end


# pure-start
@Pure
def is_composite_form(form: int) -> bool:
    """A structural form is composite when it is a product (1) or a power (2).
    A bare atom (0) is not composite. This is the form test used by the
    bracketing decision."""
    return form == 1 or form == 2


@Pure
def needs_brackets(parts: int, form: int) -> bool:
    """A denominator factor is bracketed exactly when its reciprocated quantity
    has more than one part AND its form is composite."""
    return parts != 1 and is_composite_form(form)
# pure-end


def bracket_flags(factors: List[Factor]) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
        Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
        [[factors[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
        Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
        [[factors[k]]])))
    Ensures(Acc(list_pred(Result())))
    # One flag per factor, in factor order.
    Ensures(len(Result()) == len(factors))
    # Each flag is the per-factor bracketing decision: bracket exactly when the
    # reciprocated quantity has more than one part and a composite (product or
    # power) form.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
        Result()[k] == needs_brackets(factors[k].parts, factors[k].form)),
        [[Result()[k]], [factors[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    i = 0
    while i < len(factors):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
            Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
            [[factors[k]]])))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(factors))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == needs_brackets(factors[k].parts, factors[k].form)),
            [[result[k]], [factors[k]]])))
        # invariants-end
        f = factors[i]
        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
        result.append(flag)
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec is a TOTAL functional spec: bracket_flags's postcondition fixes len(Result())==len(factors) AND Forall k: Result()[k]==needs_brackets(factors[k].parts, factors[k].form), where needs_brackets/is_composite_form are frozen @Pure helpers in the spec view. Any verifying impl must therefore compute EXACTLY needs_brackets(parts,form)=(parts!=1 and form in {1,2}) over the whole abstract domain (parts>=0, form>=0); no behavioral slack for a divergent verifying impl.

Protocol executed (python=python, SBU_BENCHMARK_DIR=benchmark-verified). All 8 files same-spec exit 0 (only impl region edited; axioms/@Pure/Requires/Ensures/Invariant byte-identical). Weakness runs (adversary weakness nagini sympy__sympy-21612 <file>), scheduled in background batches of <=3 (JVM+Z3 each):
- positive_control (byte model.py): CANDIDATE (verifies, 16.0s).
- atk_echo (flag = needs_brackets(f.parts, f.form)): CANDIDATE (verifies, 14.8s) -- semantically identical to gold.
- atk_prepatch (flag = f.parts!=1 and (f.form==1)) [prepatch Mul-only bug]: NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Spec senses the delta (prepatch_reproduced=true).
- atk_form_ge1 (parts!=1 and form>=1) [partial-domain/boundary, wrongly brackets form>=3]: does not verify (exit 2).
- atk_parts_gt1 (parts>1 and form in{1,2}) [boundary at parts==0]: does not verify (exit 2).
- atk_form_only (form in{1,2}, drops parts guard) [control-flow-effect at parts==1]: does not verify (exit 2).
- atk_const_true (flag=True) [ungrounded-oracle echo]: does not verify (exit 2).
- atk_swap (form!=1 and (parts==1 or parts==2)) [swapped operands]: does not verify (exit 2).

7 distinct wrong impls all rejected by the spec; only the semantically-identical echo (and the byte control) verify.

CANDIDATE->resolve (mandatory): atk_echo's faithful refined patch == gold patch.diff VERBATIM (echo computes needs_brackets == parts!=1 and form in{Mul,Pow} == gold guard len(item.args[0].args)!=1 and isinstance(item.base,(Mul,Pow))). Materialized to patch_atk_echo.diff and run through official run_resolve('sympy__sympy-21612', ...): RESOLVED=True, completed=True, attempts=1, flaky=False; FAIL_TO_PASS test_Mul success, all ~110 PASS_TO_PASS success, no PASS_TO_FAIL. (First attempt returned RESOLVED=False from a cold-image/infra flake with a crash on a stale .summary attr; clean re-run resolved on attempt 1.) A resolving echo is NOT a weakness (per repo policy: same-spec verifying attack fails only if its refined patch does NOT resolve). No verifying wrong impl's patch failed to resolve => verify does NOT imply incorrect here.

A-leg / G-AX audit: axiom_check.py run against real sympy (1.14.0) exit 0 -- 'deep model needs_brackets == real post-patch guard on 2 denominator factors; exactly 1 pre/post disagreement (the issue power-form reciprocal 1/y); #14160 unchanged; issue str=x/(1/y)'. Confirms the two A-reference bijections are faithful to the real callees: parts<->len(item.args[0].args) (only op is !=1, identity) and form in{1,2}<->isinstance(item.base,(Mul,Pow)) (Mul/Pow disjoint classes; form_tag 1=Mul,2=Pow,0=other makes form in{1,2} iff isinstance(_,(Mul,Pow))).

refinement.md audit: rows A1-A5 tagged R/I; A3 is the changed op modeled DEEPLY as an A-reference (validated by G-AX), not a consumed axiom. §B confirms NO @ContractOnly / A-consumed rows. §C confirms NO kind-3 (unexpressible-changed-op) step -- the added Pow form lives in the form==2 disjunct of the spelled-out needs_brackets. All legs are R / A-reference / I; A-reference correspondence to real callees holds (G-AX). No missing-leg found.

Verdict: SOUND -- 7 distinct wrong impls encoded and all rejected; the only verifying candidates are semantically the gold, whose materialized faithful patch RESOLVED under the official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.py`, `atk_form_ge1.py`, `atk_parts_gt1.py`, `atk_form_only.py`, `atk_const_true.py`, `atk_swap.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_form_ge1.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_parts_gt1.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_form_only.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_const_true.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_swap.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-21612.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A quotient is rendered as a numerator followed by a sequence of denominator
  factors joined by the division operator. To keep the rendered text from being
  misread as iterated left-to-right division, each denominator factor that is
  itself a *composite* reciprocal must be wrapped in brackets; a factor that is
  a single atomic symbol is left bare.

  A denominator factor is "composite" exactly when BOTH of the following hold:

    (1) the reciprocated quantity is built from more than one part (its part
        count differs from one); and
    (2) that quantity's structural form is a multiplicative or a power form
        (i.e. a product of factors, or a base raised to an exponent) rather
        than a bare atom.

  When both hold the factor is bracketed; otherwise it is not. The decision is
  taken independently for every denominator factor, and the result is the list
  of per-factor bracket flags in factor order.

Each denominator factor is modelled as a minimal class carrying only the two
touched facets used by the decision: the part count of the reciprocated
quantity (a non-negative int) and an integer tag for its structural form
(0 = atomic, 1 = product, 2 = power). The element payload is irrelevant to the
bracketing behaviour under specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Factor:
    """A single denominator factor, abstracted to the two facets the bracketing
    decision inspects: ``parts`` (the part count of the reciprocated quantity)
    and ``form`` (its structural form tag: 0 atomic, 1 product, 2 power)."""

    def __init__(self, parts: int, form: int) -> None:
        Requires(parts >= 0 and form >= 0)
        Ensures(Acc(self.parts) and self.parts == parts)   # type: ignore
        Ensures(Acc(self.form) and self.form == form)       # type: ignore
        self.parts = parts
        self.form = form


# axioms-start
# (no @ContractOnly axioms: the structural-form test and the part-count test
#  the decision performs are modelled deeply as integer/boolean reasoning over
#  the abstracted facets — see refinement.md, all rows are R or I.)
# axioms-end


# pure-start
@Pure
def is_composite_form(form: int) -> bool:
    """A structural form is composite when it is a product (1) or a power (2).
    A bare atom (0) is not composite. This is the form test used by the
    bracketing decision."""
    return form == 1 or form == 2


@Pure
def needs_brackets(parts: int, form: int) -> bool:
    """A denominator factor is bracketed exactly when its reciprocated quantity
    has more than one part AND its form is composite."""
    return parts != 1 and is_composite_form(form)
# pure-end


def bracket_flags(factors: List[Factor]) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
        Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
        [[factors[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
        Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
        [[factors[k]]])))
    Ensures(Acc(list_pred(Result())))
    # One flag per factor, in factor order.
    Ensures(len(Result()) == len(factors))
    # Each flag is the per-factor bracketing decision: bracket exactly when the
    # reciprocated quantity has more than one part and a composite (product or
    # power) form.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
        Result()[k] == needs_brackets(factors[k].parts, factors[k].form)),
        [[Result()[k]], [factors[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    i = 0
    while i < len(factors):
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(factors),
            Acc(factors[k].parts, 1 / 2) and Acc(factors[k].form, 1 / 2)),
            [[factors[k]]])))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(factors))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == needs_brackets(factors[k].parts, factors[k].form)),
            [[result[k]], [factors[k]]])))
        # invariants-end
        f = factors[i]
        flag = f.parts != 1 and (f.form == 1 or f.form == 2)
        result.append(flag)
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec is a TOTAL functional spec: bracket_flags's postcondition fixes len(Result())==len(factors) AND Forall k: Result()[k]==needs_brackets(factors[k].parts, factors[k].form), where needs_brackets/is_composite_form are frozen @Pure helpers in the spec view. Any verifying impl must therefore compute EXACTLY needs_brackets(parts,form)=(parts!=1 and form in {1,2}) over the whole abstract domain (parts>=0, form>=0); no behavioral slack for a divergent verifying impl.

Protocol executed (python=python, SBU_BENCHMARK_DIR=benchmark-verified). All 8 files same-spec exit 0 (only impl region edited; axioms/@Pure/Requires/Ensures/Invariant byte-identical). Weakness runs (adversary weakness nagini sympy__sympy-21612 <file>), scheduled in background batches of <=3 (JVM+Z3 each):
- positive_control (byte model.py): CANDIDATE (verifies, 16.0s).
- atk_echo (flag = needs_brackets(f.parts, f.form)): CANDIDATE (verifies, 14.8s) -- semantically identical to gold.
- atk_prepatch (flag = f.parts!=1 and (f.form==1)) [prepatch Mul-only bug]: NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Spec senses the delta (prepatch_reproduced=true).
- atk_form_ge1 (parts!=1 and form>=1) [partial-domain/boundary, wrongly brackets form>=3]: does not verify (exit 2).
- atk_parts_gt1 (parts>1 and form in{1,2}) [boundary at parts==0]: does not verify (exit 2).
- atk_form_only (form in{1,2}, drops parts guard) [control-flow-effect at parts==1]: does not verify (exit 2).
- atk_const_true (flag=True) [ungrounded-oracle echo]: does not verify (exit 2).
- atk_swap (form!=1 and (parts==1 or parts==2)) [swapped operands]: does not verify (exit 2).

7 distinct wrong impls all rejected by the spec; only the semantically-identical echo (and the byte control) verify.

CANDIDATE->resolve (mandatory): atk_echo's faithful refined patch == gold patch.diff VERBATIM (echo computes needs_brackets == parts!=1 and form in{Mul,Pow} == gold guard len(item.args[0].args)!=1 and isinstance(item.base,(Mul,Pow))). Materialized to patch_atk_echo.diff and run through official run_resolve('sympy__sympy-21612', ...): RESOLVED=True, completed=True, attempts=1, flaky=False; FAIL_TO_PASS test_Mul success, all ~110 PASS_TO_PASS success, no PASS_TO_FAIL. (First attempt returned RESOLVED=False from a cold-image/infra flake with a crash on a stale .summary attr; clean re-run resolved on attempt 1.) A resolving echo is NOT a weakness (per repo policy: same-spec verifying attack fails only if its refined patch does NOT resolve). No verifying wrong impl's patch failed to resolve => verify does NOT imply incorrect here.

A-leg / G-AX audit: axiom_check.py run against real sympy (1.14.0) exit 0 -- 'deep model needs_brackets == real post-patch guard on 2 denominator factors; exactly 1 pre/post disagreement (the issue power-form reciprocal 1/y); #14160 unchanged; issue str=x/(1/y)'. Confirms the two A-reference bijections are faithful to the real callees: parts<->len(item.args[0].args) (only op is !=1, identity) and form in{1,2}<->isinstance(item.base,(Mul,Pow)) (Mul/Pow disjoint classes; form_tag 1=Mul,2=Pow,0=other makes form in{1,2} iff isinstance(_,(Mul,Pow))).

refinement.md audit: rows A1-A5 tagged R/I; A3 is the changed op modeled DEEPLY as an A-reference (validated by G-AX), not a consumed axiom. §B confirms NO @ContractOnly / A-consumed rows. §C confirms NO kind-3 (unexpressible-changed-op) step -- the added Pow form lives in the form==2 disjunct of the spelled-out needs_brackets. All legs are R / A-reference / I; A-reference correspondence to real callees holds (G-AX). No missing-leg found.

Verdict: SOUND -- 7 distinct wrong impls encoded and all rejected; the only verifying candidates are semantically the gold, whose materialized faithful patch RESOLVED under the official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed: the spec does NOT drift from / overconstrain the real repo behavior. The modeled function `needs_brackets(parts, form) = parts != 1 and form in {1,2}` maps exactly to the gold post-patch guard `len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow))` under the stated R-refinement (parts <-> len(item.args[0].args); form in {1,2} <-> isinstance(base, (Mul, Pow)); form==0 <-> other class).

Machine-checked on the real repo (base_commit b4777fdcef, verified: base has `isinstance(item.base, Mul)`; has `(Mul, Pow)`):
- G-CONF (conformance_check.py) against PYTHONPATH=patched repo: 100000 product expressions, 0 disagreements between model-driven decision + unchanged scaffolding and the real StrPrinter output. EXIT 0.
- G-AX (axiom_check.py): needs_brackets == real post-patch guard on all denominator factors; exactly 1 pre/post disagreement (the issue's power-form reciprocal 1/y), #14160 preserved. Passes against both patched (issue str='x/(1/y)') and base (issue str='x/1/y') repos. EXIT 0.
- scripts/nagini_verify.sh model.py: Verification successful (11.5s).
- Adversarial exotic-base probe (18 structurally diverse reciprocal bases: atoms, products of 2/3 parts, powers, negative-exp powers, sums, applied functions f(x)/f(x,y), sin, exp, reciprocal-of-reciprocal, coefficient-carrying products) run against the real patched sympy: model decision matched the real `len(...)!=1 and isinstance(base,(Mul,Pow))` guard on every input, 0 mismatches.

The spec reproduces the gold guard exactly (no strengthening), the model verifies against the frozen spec, and the mapping bijection holds on real sympy structures. No input found where the modeled function disagrees with the real callee. Note: the bundle contains no patch.diff file in the nagini dir (patch is verbatim gold per refinement.md), but this does not bear on the faithfulness question, which concerns spec vs. real repo behavior — confirmed FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified byte-identical to the frozen spec (spec_view hash 9f2ed71… matches meta.json; `same-spec nagini sympy__sympy-21612` on a byte copy of model.py -> exit 0). Impl region genuinely elided in the solver view (`...  # implementation elided`).

Gold edit: isinstance(item.base, Mul) -> isinstance(item.base, (Mul, Pow)) at sympy/printing/str.py:335-336, i.e. power-form reciprocal denominators must now also be bracketed. The delta maps ENTIRELY to the impl region (prepatch `flag = f.parts != 1 and (f.form == 1)` -> patched `... (f.form == 1 or f.form == 2)`, lines 111-113), outside the solver's spec view.

The spec view's pure/postcondition region pins the CORRECT target behaviour (power forms bracketed via `is_composite_form(form)=form==1 or form==2` and `needs_brackets=parts!=1 and composite`). That is intrinsic to any deep twin model and is not per se leakage. The leakage test is whether the spec reveals the edit-specific delta beyond the public problem_statement — it does not:
1. The public problem_statement itself exhibits the bug on `\frac{1}{c^2}` (a power-form reciprocal 1/c**2, i.e. Pow) rendering with missing brackets, expected `((a**3 + b)/c)/(1/(c**2))`. So 'power-form denominators need bracketing' is exactly what the bug report already conveys.
2. The spec describes complete correct behaviour, not a diff; it never distinguishes the pre-existing Mul disjunct from the newly-added Pow disjunct, and the docstring explicitly states behaviour 'not as an edit'.
3. The only line revealing the product-only->product-or-power delta is the pre-patch skeleton comment in the impl region (model_prepatch.py / lines 111-113), outside the spec view.
4. Lexical G-LEAK screen over the spec view is clean: no str.py, isinstance, item.base, item.args, pow_paren, #14160, Pow(, _print_Mul, prepatch, or patch tokens.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
