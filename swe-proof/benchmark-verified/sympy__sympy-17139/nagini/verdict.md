# P2 adversarial audit — sympy__sympy-17139

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.py`, `atk_oddeven.py`, `atk_perfectneg.py`, `atk_value1.py`, `atk_squared_collapse.py`, `atk_fourth_unchanged.py`, `atk_at_max.py`, `atk_no_gtmax.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Expon:
@@ -120,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
     Requires(max >= 4)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
@@ -172,8 +170,6 @@
     # impl-start
     if not is_target:
         return 0
-    if not exp.real:
-        return 0
     if order_lt_zero(exp) == True:
         return 0
     if order_gt_max(exp, max) == True:
```

Attack 2 — `atk_oddeven.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Expon:
@@ -120,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
     Requires(max >= 4)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
@@ -186,7 +184,7 @@
         if exp.value == 4:
             return 2
         elif not pow:
-            if exp.value % 2 == 1:
+            if exp.value % 2 == 0:
                 return 0
             return 2
         else:
```

Attack 3 — `atk_perfectneg.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Expon:
@@ -120,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
     Requires(max >= 4)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
@@ -190,7 +188,7 @@
                 return 0
             return 2
         else:
-            if not is_perfect_power(exp.value):
+            if is_perfect_power(exp.value):
                 return 0
             return 2
     # impl-end
```

Attack 4 — `atk_value1.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Expon:
@@ -120,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
     Requires(max >= 4)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
@@ -179,7 +177,7 @@
     if order_gt_max(exp, max) == True:
         return 0
     if exp.value == 1:
-        return 0
+        return 2
     if exp.value == 2:
         return 1
     else:
```

Attack 5 — `atk_squared_collapse.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Expon:
@@ -120,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
     Requires(max >= 4)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
@@ -181,7 +179,7 @@
     if exp.value == 1:
         return 0
     if exp.value == 2:
-        return 1
+        return 2
     else:
         if exp.value == 4:
             return 2
```

Attack 6 — `atk_fourth_unchanged.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Expon:
@@ -120,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
     Requires(max >= 4)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
@@ -184,7 +182,7 @@
         return 1
     else:
         if exp.value == 4:
-            return 2
+            return 0
         elif not pow:
             if exp.value % 2 == 1:
                 return 0
```

Attack 7 — `atk_at_max.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Expon:
@@ -120,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
     Requires(max >= 4)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
@@ -178,6 +176,8 @@
         return 0
     if order_gt_max(exp, max) == True:
         return 0
+    if exp.value == max:
+        return 0
     if exp.value == 1:
         return 0
     if exp.value == 2:
```

Attack 8 — `atk_no_gtmax.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Expon:
@@ -120,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
     Requires(max >= 4)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
@@ -176,8 +174,6 @@
         return 0
     if order_lt_zero(exp) == True:
         return 0
-    if order_gt_max(exp, max) == True:
-        return 0
     if exp.value == 1:
         return 0
     if exp.value == 2:
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-17139.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A node transformer rewrites a power of a designated base function
  (``base ** exponent``) into an equivalent trigonometric form, but only when
  the exponent is an ordinary real number on which the ordering predicates
  ``exponent < 0`` and ``exponent > max`` are meaningful. The ordering of a
  symbolic quantity against a real bound is only defined when that quantity is
  itself real; ordering a genuinely complex (non-real) quantity against a real
  number is undefined and must never be attempted.

  Therefore, for a power whose exponent is NOT real, the transformer must leave
  the node unchanged and must not evaluate any ordering of that exponent. Only
  for a real exponent may the transformer test the sign / magnitude of the
  exponent and then dispatch on its integer magnitude.

  For an in-range real exponent the dispatch reproduces the established rewrite
  selection: the first-power magnitude is left unchanged and the squared case is
  special (its own form); the fourth-power case is always rewritten. For the
  remaining magnitudes, when the caller admits every even power (``pow`` false)
  only an even magnitude is rewritten while an odd magnitude is left unchanged;
  when the caller restricts to perfect powers (``pow`` true) the magnitude is
  rewritten exactly when it is a perfect power, otherwise the node is left
  unchanged.

The exponent is modelled by a minimal carrier class with the two touched
attributes: whether it is real, and (when real) its integer value. The two
ordering predicates against the exponent are unchanged library operations whose
SAFE DOMAIN is the real exponents; they are axiomatized (`@Pure @ContractOnly`)
with that domain as their precondition, mirroring that the real comparison
raises a TypeError on a non-real operand. The perfect-power test on the integer
magnitude is likewise an unchanged library predicate, modelled as an
(A-reference) pure callee validated against the real predicate. The transformer
dispatch itself is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class Expon:
    """The exponent of the power node under inspection: only the two attributes
    the transformer touches are modelled.

      - ``real``  : the exponent is a real quantity (its ordering against a real
                    bound is defined). For a genuinely complex exponent this is
                    False and no ordering may be evaluated.
      - ``value`` : the integer magnitude used by the rewrite dispatch; only
                    meaningful (and only read) when ``real`` holds.
    """

    def __init__(self, real: bool, value: int) -> None:
        self.real = real      # type: bool
        self.value = value    # type: int
        Ensures(Acc(self.real) and Acc(self.value))
        Ensures(self.real == real and self.value == value)


# axioms-start
@Pure
@ContractOnly
def order_lt_zero(e: Expon) -> bool:
    """The ordering predicate ``exponent < 0``. This is an UNCHANGED library
    operation; its safe (non-raising) domain is the real exponents, so it is
    Required real. (Provenance + executable soundness check: mapping.md /
    axiom_check.py.) On a real exponent it is True iff the exponent value is
    negative."""
    Requires(Acc(e.real, 1 / 4) and Acc(e.value, 1 / 4))
    Requires(e.real)
    Ensures(Result() == (e.value < 0))


@Pure
@ContractOnly
def order_gt_max(e: Expon, m: int) -> bool:
    """The ordering predicate ``exponent > max``. Unchanged library operation;
    safe domain is the real exponents (Required real). On a real exponent it is
    True iff the exponent value exceeds the bound ``m``."""
    Requires(Acc(e.real, 1 / 4) and Acc(e.value, 1 / 4))
    Requires(e.real)
    Ensures(Result() == (e.value > m))


@Pure
@ContractOnly
def is_perfect_power(n: int) -> bool:
    """Whether the non-negative integer magnitude ``n`` is a perfect power
    (some integer base raised to an integer exponent >= 2). Unchanged library
    predicate; modelled as a pure callee whose value is validated against the
    real predicate (A-reference, axiom_check.py / G-AX). For the even, non-2,
    non-4 magnitudes the dispatch keys on it; the only fact the proof needs is
    that it is a deterministic function of ``n`` (the dispatch branches on its
    boolean value), which `@Pure` already guarantees, so no value is claimed
    here beyond that."""
    Requires(n >= 0)
# axioms-end


# pure-start
# (no module-level pure helpers required)
# pure-end


def transform_power(is_target: bool, exp: Expon, max: int, pow: bool) -> int:
    """Inspect a node and report which rewrite branch fires, as a result code:

        0  -> the node is returned UNCHANGED
        1  -> rewritten via the squared-base case (exponent magnitude == 2)
        2  -> rewritten via the general power case

    ``is_target`` is whether the node is a power of the designated base
    function (only such nodes are eligible). ``pow`` selects whether only
    magnitudes that are perfect powers are admitted among the even cases. The
    exponent ``exp`` is read only; its ordering may be evaluated solely when it
    is real.
    """
    # pre-conditions-start
    Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
    Requires(max >= 4)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
    # A non-eligible node is unchanged.
    Ensures(Implies(not is_target, Result() == 0))
    # The discriminating guarantee: a power with a NON-REAL exponent is left
    # unchanged (no ordering of that exponent is ever attempted).
    Ensures(Implies(is_target and not exp.real, Result() == 0))
    # A real, negative, or over-large exponent leaves the node unchanged.
    Ensures(Implies(is_target and exp.real and exp.value < 0, Result() == 0))
    Ensures(Implies(is_target and exp.real and exp.value > max, Result() == 0))
    # A real first-power magnitude is left unchanged.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value == 1, Result() == 0))
    # The squared-base case rewrites via the squared form (result code 1).
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value == 2, Result() == 1))
    # The fourth-power case is always rewritten (code 2), independent of ``pow``.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value == 4, Result() == 2))
    # When every even power is admitted (``pow`` false), an in-range magnitude
    # other than the first-power, squared and fourth-power cases is rewritten
    # exactly when it is even; an odd magnitude is left UNCHANGED.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and not pow
        and exp.value % 2 == 1, Result() == 0))
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and not pow
        and exp.value % 2 == 0, Result() == 2))
    # Under ``pow`` an in-range magnitude other than the first-power, squared and
    # fourth-power cases is rewritten exactly when it is a perfect power,
    # otherwise (whatever its parity) it is left UNCHANGED.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and pow
        and is_perfect_power(exp.value), Result() == 2))
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and pow
        and not is_perfect_power(exp.value), Result() == 0))
    # The result is always one of the three branch tags.
    Ensures(Result() == 0 or Result() == 1 or Result() == 2)
    # post-conditions-end
    # impl-start
    if not is_target:
        return 0
    if not exp.real:
        return 0
    if order_lt_zero(exp) == True:
        return 0
    if order_gt_max(exp, max) == True:
        return 0
    if exp.value == 1:
        return 0
    if exp.value == 2:
        return 1
    else:
        if exp.value == 4:
            return 2
        elif not pow:
            if exp.value % 2 == 1:
                return 0
            return 2
        else:
            if not is_perfect_power(exp.value):
                return 0
            return 2
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-17139 (nagini).

TIGHTNESS ANALYSIS: transform_power's postconditions pin Result() exhaustively over the entire Requires domain: not-target=>0; target&not-real=>0; real&(value<0 or value>max)=>0; then for 0<=value<=max the arms {value==1=>0, ==2=>1, ==4=>2, else parity(not pow) / is_perfect_power(pow)} each have a dedicated Ensures, closed by Result()==0|1|2. So any behavioral deviation must violate a postcondition. Crucially the non-real short-circuit is mandated by an INDEPENDENT postcondition (Implies(is_target and not exp.real, Result()==0)), not merely by the axiom precondition.

### ATTACKS (all copied from model.py, ONLY impl region edited; all confirmed SAME-SPEC by adversary same-spec, exit 0):
- atk_prepatch.py: the recorded prepatch bug (omits the `if not exp.real: return 0` guard). weakness EXIT=2. Direct verify FAILED in 16.5s at atk_prepatch.py:173 `precondition of order_lt_zero might not hold. Assertion e.real might not hold` -- fails at exactly the A-consumed A3 leg (order_lt_zero Requires(e.real)), reproducing the spec sensing the bug (mirrors real TypeError). prepatch_reproduced=true.
- atk_oddeven.py: parity flipped in not-pow arm (even->unchanged, odd->rewrite). weakness EXIT=2 (verification failed).
- atk_perfectneg.py: perfect-power test negated in pow arm (A-reference echo attack). weakness EXIT=2 (verification failed).
- atk_value1.py: first-power magnitude rewritten (return 2) instead of unchanged. weakness EXIT=2.
- atk_squared_collapse.py: value==2 returns general code 2 instead of squared code 1. weakness EXIT=2.
- atk_fourth_unchanged.py: value==4 left unchanged (0) instead of always-rewrite (2). weakness EXIT=2.
- atk_at_max.py: off-by-one boundary, value==max forced unchanged. weakness EXIT=2.
- atk_no_gtmax.py: partial-domain, drops the order_gt_max guard so over-large exponents get dispatched/rewritten. weakness EXIT=2.

Commands (per attack): `python -m swebench_unified.adversary weakness nagini sympy__sympy-17139 atk_N.py`. Positive control: `adversary verify ... positive_control.py` => VERIFIED in 14.7s (EXIT 0).

RESULT: 0 of 8 same-spec wrong impls verified (every weakness EXIT=2 = NOT-A-COUNTEREXAMPLE, spec rejected the impl). No CANDIDATE arose, so no faithful refined patch needed materializing/resolving (patches={}). All attacks fully executed and reported; none could break the spec.

REFINEMENT.MD A-LEG AUDIT: A3/A4 A-consumed (order_lt_zero/order_gt_max <-> Expr.__lt__/__gt__): Requires(e.real) mirrors the real TypeError on non-real operands; the proof genuinely CONSUMES the precondition (prepatch fails precisely there). A10 A-reference (is_perfect_power <-> bool(perfect_power)): proof consumes only @Pure determinism; correspondence validated by axiom_check.py faithfulness cross-check (model_outcome==gold_outcome over value in [1,m], m in {4,6,10,20,30}, both pow, plus F2P shapes) -- atk_perfectneg (negating it) is correctly rejected. Every leg is R / A-consumed / A-reference / I; no kind-3 leg. A-legs' correspondence to the real callees holds. verify=>correct upheld.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_prepatch.py`, `atk_oddeven.py`, `atk_perfectneg.py`, `atk_value1.py`, `atk_squared_collapse.py`, `atk_fourth_unchanged.py`, `atk_at_max.py`, `atk_no_gtmax.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_oddeven.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_perfectneg.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_value1.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_squared_collapse.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_fourth_unchanged.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_at_max.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_no_gtmax.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-17139.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A node transformer rewrites a power of a designated base function
  (``base ** exponent``) into an equivalent trigonometric form, but only when
  the exponent is an ordinary real number on which the ordering predicates
  ``exponent < 0`` and ``exponent > max`` are meaningful. The ordering of a
  symbolic quantity against a real bound is only defined when that quantity is
  itself real; ordering a genuinely complex (non-real) quantity against a real
  number is undefined and must never be attempted.

  Therefore, for a power whose exponent is NOT real, the transformer must leave
  the node unchanged and must not evaluate any ordering of that exponent. Only
  for a real exponent may the transformer test the sign / magnitude of the
  exponent and then dispatch on its integer magnitude.

  For an in-range real exponent the dispatch reproduces the established rewrite
  selection: the first-power magnitude is left unchanged and the squared case is
  special (its own form); the fourth-power case is always rewritten. For the
  remaining magnitudes, when the caller admits every even power (``pow`` false)
  only an even magnitude is rewritten while an odd magnitude is left unchanged;
  when the caller restricts to perfect powers (``pow`` true) the magnitude is
  rewritten exactly when it is a perfect power, otherwise the node is left
  unchanged.

The exponent is modelled by a minimal carrier class with the two touched
attributes: whether it is real, and (when real) its integer value. The two
ordering predicates against the exponent are unchanged library operations whose
SAFE DOMAIN is the real exponents; they are axiomatized (`@Pure @ContractOnly`)
with that domain as their precondition, mirroring that the real comparison
raises a TypeError on a non-real operand. The perfect-power test on the integer
magnitude is likewise an unchanged library predicate, modelled as an
(A-reference) pure callee validated against the real predicate. The transformer
dispatch itself is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class Expon:
    """The exponent of the power node under inspection: only the two attributes
    the transformer touches are modelled.

      - ``real``  : the exponent is a real quantity (its ordering against a real
                    bound is defined). For a genuinely complex exponent this is
                    False and no ordering may be evaluated.
      - ``value`` : the integer magnitude used by the rewrite dispatch; only
                    meaningful (and only read) when ``real`` holds.
    """

    def __init__(self, real: bool, value: int) -> None:
        self.real = real      # type: bool
        self.value = value    # type: int
        Ensures(Acc(self.real) and Acc(self.value))
        Ensures(self.real == real and self.value == value)


# axioms-start
@Pure
@ContractOnly
def order_lt_zero(e: Expon) -> bool:
    """The ordering predicate ``exponent < 0``. This is an UNCHANGED library
    operation; its safe (non-raising) domain is the real exponents, so it is
    Required real. (Provenance + executable soundness check: mapping.md /
    axiom_check.py.) On a real exponent it is True iff the exponent value is
    negative."""
    Requires(Acc(e.real, 1 / 4) and Acc(e.value, 1 / 4))
    Requires(e.real)
    Ensures(Result() == (e.value < 0))


@Pure
@ContractOnly
def order_gt_max(e: Expon, m: int) -> bool:
    """The ordering predicate ``exponent > max``. Unchanged library operation;
    safe domain is the real exponents (Required real). On a real exponent it is
    True iff the exponent value exceeds the bound ``m``."""
    Requires(Acc(e.real, 1 / 4) and Acc(e.value, 1 / 4))
    Requires(e.real)
    Ensures(Result() == (e.value > m))


@Pure
@ContractOnly
def is_perfect_power(n: int) -> bool:
    """Whether the non-negative integer magnitude ``n`` is a perfect power
    (some integer base raised to an integer exponent >= 2). Unchanged library
    predicate; modelled as a pure callee whose value is validated against the
    real predicate (A-reference, axiom_check.py / G-AX). For the even, non-2,
    non-4 magnitudes the dispatch keys on it; the only fact the proof needs is
    that it is a deterministic function of ``n`` (the dispatch branches on its
    boolean value), which `@Pure` already guarantees, so no value is claimed
    here beyond that."""
    Requires(n >= 0)
# axioms-end


# pure-start
# (no module-level pure helpers required)
# pure-end


def transform_power(is_target: bool, exp: Expon, max: int, pow: bool) -> int:
    """Inspect a node and report which rewrite branch fires, as a result code:

        0  -> the node is returned UNCHANGED
        1  -> rewritten via the squared-base case (exponent magnitude == 2)
        2  -> rewritten via the general power case

    ``is_target`` is whether the node is a power of the designated base
    function (only such nodes are eligible). ``pow`` selects whether only
    magnitudes that are perfect powers are admitted among the even cases. The
    exponent ``exp`` is read only; its ordering may be evaluated solely when it
    is real.
    """
    # pre-conditions-start
    Requires(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
    Requires(max >= 4)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(exp.real, 1 / 2) and Acc(exp.value, 1 / 2))
    # A non-eligible node is unchanged.
    Ensures(Implies(not is_target, Result() == 0))
    # The discriminating guarantee: a power with a NON-REAL exponent is left
    # unchanged (no ordering of that exponent is ever attempted).
    Ensures(Implies(is_target and not exp.real, Result() == 0))
    # A real, negative, or over-large exponent leaves the node unchanged.
    Ensures(Implies(is_target and exp.real and exp.value < 0, Result() == 0))
    Ensures(Implies(is_target and exp.real and exp.value > max, Result() == 0))
    # A real first-power magnitude is left unchanged.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value == 1, Result() == 0))
    # The squared-base case rewrites via the squared form (result code 1).
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value == 2, Result() == 1))
    # The fourth-power case is always rewritten (code 2), independent of ``pow``.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value == 4, Result() == 2))
    # When every even power is admitted (``pow`` false), an in-range magnitude
    # other than the first-power, squared and fourth-power cases is rewritten
    # exactly when it is even; an odd magnitude is left UNCHANGED.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and not pow
        and exp.value % 2 == 1, Result() == 0))
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and not pow
        and exp.value % 2 == 0, Result() == 2))
    # Under ``pow`` an in-range magnitude other than the first-power, squared and
    # fourth-power cases is rewritten exactly when it is a perfect power,
    # otherwise (whatever its parity) it is left UNCHANGED.
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and pow
        and is_perfect_power(exp.value), Result() == 2))
    Ensures(Implies(
        is_target and exp.real and 0 <= exp.value and exp.value <= max
        and exp.value != 1 and exp.value != 2 and exp.value != 4 and pow
        and not is_perfect_power(exp.value), Result() == 0))
    # The result is always one of the three branch tags.
    Ensures(Result() == 0 or Result() == 1 or Result() == 2)
    # post-conditions-end
    # impl-start
    if not is_target:
        return 0
    if not exp.real:
        return 0
    if order_lt_zero(exp) == True:
        return 0
    if order_gt_max(exp, max) == True:
        return 0
    if exp.value == 1:
        return 0
    if exp.value == 2:
        return 1
    else:
        if exp.value == 4:
            return 2
        elif not pow:
            if exp.value % 2 == 1:
                return 0
            return 2
        else:
            if not is_perfect_power(exp.value):
                return 0
            return 2
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-17139 (nagini).

TIGHTNESS ANALYSIS: transform_power's postconditions pin Result() exhaustively over the entire Requires domain: not-target=>0; target&not-real=>0; real&(value<0 or value>max)=>0; then for 0<=value<=max the arms {value==1=>0, ==2=>1, ==4=>2, else parity(not pow) / is_perfect_power(pow)} each have a dedicated Ensures, closed by Result()==0|1|2. So any behavioral deviation must violate a postcondition. Crucially the non-real short-circuit is mandated by an INDEPENDENT postcondition (Implies(is_target and not exp.real, Result()==0)), not merely by the axiom precondition.

### ATTACKS (all copied from model.py, ONLY impl region edited; all confirmed SAME-SPEC by adversary same-spec, exit 0):
- atk_prepatch.py: the recorded prepatch bug (omits the `if not exp.real: return 0` guard). weakness EXIT=2. Direct verify FAILED in 16.5s at atk_prepatch.py:173 `precondition of order_lt_zero might not hold. Assertion e.real might not hold` -- fails at exactly the A-consumed A3 leg (order_lt_zero Requires(e.real)), reproducing the spec sensing the bug (mirrors real TypeError). prepatch_reproduced=true.
- atk_oddeven.py: parity flipped in not-pow arm (even->unchanged, odd->rewrite). weakness EXIT=2 (verification failed).
- atk_perfectneg.py: perfect-power test negated in pow arm (A-reference echo attack). weakness EXIT=2 (verification failed).
- atk_value1.py: first-power magnitude rewritten (return 2) instead of unchanged. weakness EXIT=2.
- atk_squared_collapse.py: value==2 returns general code 2 instead of squared code 1. weakness EXIT=2.
- atk_fourth_unchanged.py: value==4 left unchanged (0) instead of always-rewrite (2). weakness EXIT=2.
- atk_at_max.py: off-by-one boundary, value==max forced unchanged. weakness EXIT=2.
- atk_no_gtmax.py: partial-domain, drops the order_gt_max guard so over-large exponents get dispatched/rewritten. weakness EXIT=2.

Commands (per attack): `python -m swebench_unified.adversary weakness nagini sympy__sympy-17139 atk_N.py`. Positive control: `adversary verify ... positive_control.py` => VERIFIED in 14.7s (EXIT 0).

RESULT: 0 of 8 same-spec wrong impls verified (every weakness EXIT=2 = NOT-A-COUNTEREXAMPLE, spec rejected the impl). No CANDIDATE arose, so no faithful refined patch needed materializing/resolving (patches={}). All attacks fully executed and reported; none could break the spec.

REFINEMENT.MD A-LEG AUDIT: A3/A4 A-consumed (order_lt_zero/order_gt_max <-> Expr.__lt__/__gt__): Requires(e.real) mirrors the real TypeError on non-real operands; the proof genuinely CONSUMES the precondition (prepatch fails precisely there). A10 A-reference (is_perfect_power <-> bool(perfect_power)): proof consumes only @Pure determinism; correspondence validated by axiom_check.py faithfulness cross-check (model_outcome==gold_outcome over value in [1,m], m in {4,6,10,20,30}, both pow, plus F2P shapes) -- atk_perfectneg (negating it) is correctly rejected. Every leg is R / A-consumed / A-reference / I; no kind-3 leg. A-legs' correspondence to the real callees holds. verify=>correct upheld.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for sympy__sympy-17139 (nagini). The modeled function transform_power abstracts the inner _f(rv) dispatch of _TR56 (sympy/simplify/fu.py:496-522, gold patch adds `if not rv.exp.is_real: return rv` before the ordering tests). I transcribed the REAL gold _f branch-for-branch and compared its result code (0 unchanged / 1 squared / 2 general) against the model's mandated postcondition result across the whole modeled domain.

Method & evidence:
1. Spec vs. gold transcription over mx in {4,6,10,20,30}, value in [0,mx+4], both pow, both real, both is_target: 0 mismatches.
2. Spec vs. REAL library-backed _f on actual symbolic Pow(sin(x),v) nodes (v>=1, unevaluated Pows so is_Pow holds), mx in {4,6,10,20}, both pow: 0 mismatches. Negative integer exponents (-1,-2,-3,-5) -> code 0, match. Non-real exponents (I, 2*I+1, 3*I, 2+3*I, 1-I, -I): real _f returns unchanged (short-circuit at the added guard, is_real False), spec mandates 0 — match.
3. The only apparent discrepancy (value==0 -> real 0 / naive-spec 2, plus perfect_power(0) ValueError) is NOT reachable: sin(x)**0 auto-evaluates to 1 so rv.is_Pow is False; mapping.md §3.2 explicitly documents exp==0 as unreachable and Requires(n>=0) with dispatch guards keeping is_perfect_power off n==0. The model's own guards (value==1 short-circuit before the perfect_power arm; value<0 / value>max leave unchanged) never call is_perfect_power on 0.
4. Model verifies against its own spec (Nagini: Verification successful, 15.6s) — spec is satisfiable/not over-constrained by the faithful impl.
5. same-spec on the identity copy returns SAME (exit 0); spec region byte-identical.

The abstraction (real:bool + integer value carrier, ordering predicates axiomatized with Requires(real) domain mirroring the real TypeError, is_perfect_power A-reference) does not over-strengthen: on every realizable input the modeled function agrees with the real callee. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-LEAK lexical screen passes (screen(model.py) -> passed=True). Semantic check against the PUBLIC problem_statement (not hints_text): the problem_statement is the full traceback, which already names fu.py / _TR56 / _f, shows the exact failing line `if (rv.exp < 0) == True:`, and shows `TypeError: Invalid comparison of complex I` on `simplify(cos(x)**I)`. Thus the public task already pinpoints that ordering a non-real (complex) exponent at that site is the fault. The spec view's discriminating statement -- 'for a power whose exponent is NOT real, the transformer must leave the node unchanged and must not evaluate any ordering of that exponent' -- is directly derivable from that public traceback and reveals no location, symbol, or mechanism beyond it. It does not quote the gold-added line `if not rv.exp.is_real: return rv`, contains no diff markers, no patched file path (fu.py absent from the spec view), and no bug/fix narration. The remaining postconditions (first-power/squared/fourth-power/pow perfect-power dispatch) model UNCHANGED pre-existing rewrite-selection behavior, not the edit, so they do not leak the gold discriminator. Gold-patch verbatim text appears only in refinement.md and mapping.md, which are auditor-facing derivation artifacts, NOT the consumer spec_view that G-LEAK screens. No RELAXED_LEAKAGE flag needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
