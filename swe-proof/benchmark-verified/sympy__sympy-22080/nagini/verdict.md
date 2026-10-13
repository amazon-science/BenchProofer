# P2 adversarial audit — sympy__sympy-22080

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -147,7 +147,7 @@
     Ensures(Implies(operand_level >= level_power(), Result() == False))
     # post-conditions-end
     # impl-start
-    return encloses(operand_level, leading_minus_cutoff(), False)
+    return operand_level <= leading_minus_cutoff()
     # impl-end
 
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -147,7 +147,7 @@
     Ensures(Implies(operand_level >= level_power(), Result() == False))
     # post-conditions-end
     # impl-start
-    return encloses(operand_level, leading_minus_cutoff(), False)
+    return encloses(operand_level, leading_minus_cutoff(), True)
     # impl-end
 
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,7 @@
     Ensures(level_additive() < Result() and Result() < level_power())
     # post-conditions-end
     # impl-start
-    return level_multiplicative()
+    return level_power()
     # impl-end
 
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,7 @@
     Ensures(level_additive() < Result() and Result() < level_power())
     # post-conditions-end
     # impl-start
-    return level_multiplicative()
+    return remainder_operand_level()
     # impl-end
 
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -172,6 +172,5 @@
     Ensures(Result() == True)
     # post-conditions-end
     # impl-start
-    s = remainder_operand_level()
-    return negated_single_operand_enclosed(s)
+    return False
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -147,7 +147,7 @@
     Ensures(Implies(operand_level >= level_power(), Result() == False))
     # post-conditions-end
     # impl-start
-    return encloses(operand_level, leading_minus_cutoff(), False)
+    return encloses(operand_level, leading_minus_cutoff(), operand_level > level_function())
     # impl-end
 
 
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -114,6 +114,8 @@
     Ensures(level_additive() < Result() and Result() < level_power())
     # post-conditions-end
     # impl-start
+    if level_additive() > level_power():
+        return level_function()
     return level_multiplicative()
     # impl-end
 
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -147,7 +147,7 @@
     Ensures(Implies(operand_level >= level_power(), Result() == False))
     # post-conditions-end
     # impl-start
-    return encloses(operand_level, leading_minus_cutoff(), False)
+    return operand_level < level_power()
     # impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-22080.

Behaviour under specification (stated as desired behaviour, not as an edit):

When a value-carrying expression is rendered as source code and the rendering
carries a leading minus sign in front of a single operand, the printed text must
parse back to the same value. Whether that one operand needs to be enclosed in
parentheses is decided by comparing how tightly the operand itself re-binds in
the target syntax against a constant cut-off applied to such a leading-minus
rendering. The result-determining contract is purely observable:

  (1) The enclose/leave-bare decision is monotone in how tightly the operand
      re-binds: an operand that re-binds no more tightly than the cut-off is
      enclosed in parentheses; an operand that re-binds more tightly is left
      bare. (The generic "enclose iff the operand does not re-bind strictly
      tighter than its context" rule.)

  (2) A "%"/remainder operand re-binds exactly as tightly as a "*"/product
      operand, and the cut-off applied to a leading-minus single operand sits
      above that level but below a "**"/power operand. Consequently a
      remainder operand and a product operand are both enclosed, while a power
      operand and a function-call operand are left bare. In particular a
      leading-minus remainder operand is enclosed, so e.g. negating a "%"
      expression renders as "-(... % ...)" rather than "-... % ..." and parses
      back to the negated remainder.

The re-binding levels are modelled as small ordered integers (additive <
multiplicative < power < function-call) — just an order-preserving carrier for
the comparisons the contract makes; nothing depends on their exact values, only
on the ordering, so an integer carrier is exact (refinement.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No @ContractOnly axiom is consumed. The re-binding-level ordering and the
#  enclose-in-parentheses rule are modelled deeply in the pure region below and
#  are validated == the real renderer's observable rendering out-of-band by
#  axiom_check.py / G-AX -- A-references, not consumed axioms.)
# axioms-end

# pure-start
@Pure
def level_additive() -> int:
    # re-binding level of an additive ("+"/"-") operand
    return 40

@Pure
def level_multiplicative() -> int:
    # re-binding level of a multiplicative ("*"/"%") operand
    return 50

@Pure
def level_power() -> int:
    # re-binding level of a power ("**") operand
    return 60

@Pure
def level_function() -> int:
    # re-binding level of a function-call operand
    return 70

@Pure
def encloses(operand_level: int, cutoff: int, strict: bool) -> bool:
    """The generic enclose-in-parentheses predicate: a rendered operand is
    enclosed iff it re-binds strictly more loosely than its context, or (in the
    non-strict mode used by default) exactly as loosely. Monotone decreasing in
    `operand_level`."""
    if operand_level < cutoff:
        return True
    if not strict:
        return operand_level <= cutoff
    return False

@Pure
def leading_minus_cutoff() -> int:
    """The cut-off applied to the single operand of a leading-minus rendering.
    It sits above the multiplicative level and below the power level, so a
    leading-minus product- or remainder-level operand is enclosed while a power
    operand need not be -- which is what makes the rendering parse back to the
    intended value."""
    Ensures(level_multiplicative() < Result() and Result() < level_power())
    return (level_power() + level_multiplicative()) // 2
# pure-end

def remainder_operand_level() -> int:
    """The re-binding level of a "%"/remainder operand.

    A remainder operand re-binds exactly as tightly as a "*"/product operand --
    and therefore more loosely than the leading-minus cut-off (so a leading-minus
    remainder operand is enclosed, item (2) above)."""
    # pre-conditions-start
    # total-correctness obligation: the level lookup must actually deliver an
    # answer. The verifier is partial-correctness by default, so without this
    # a diverging body would satisfy the value contract vacuously; the real
    # operation always returns.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # re-binds exactly as tightly as a multiplicative operand ...
    Ensures(Result() == level_multiplicative())
    # ... hence more loosely than a power and more tightly than an additive op.
    Ensures(level_additive() < Result() and Result() < level_power())
    # post-conditions-end
    # impl-start
    return level_multiplicative()
    # impl-end

def negated_single_operand_enclosed(operand_level: int) -> bool:
    """Whether the single operand of a leading-minus rendering is enclosed in
    parentheses, as a function of that operand's own re-binding level.

    The decision compares the operand against the leading-minus cut-off, in the
    default (non-strict) mode.
    """
    # pre-conditions-start
    Requires(level_additive() <= operand_level
             and operand_level <= level_function())
    # total-correctness obligation: the enclose/leave-bare decision must
    # actually be delivered (no diverging body satisfying the value contract
    # vacuously); the real decision procedure always returns.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # the operand is enclosed exactly per the generic rule against the
    # leading-minus cut-off (the default, non-strict mode).
    Ensures(Result() == encloses(operand_level, leading_minus_cutoff(), False))
    # consequences the issue demands, pinned independently of the cut-off's
    # exact value (they hold for ANY cut-off above multiplicative and below
    # power level):
    #   a product / additive / remainder operand (level <= multiplicative) is
    #   enclosed;
    Ensures(Implies(operand_level <= level_multiplicative(), Result() == True))
    #   a power / function operand (level >= power) stays bare.
    Ensures(Implies(operand_level >= level_power(), Result() == False))
    # post-conditions-end
    # impl-start
    return encloses(operand_level, leading_minus_cutoff(), False)
    # impl-end

def negated_remainder_is_enclosed() -> bool:
    """A worked instance: composing the two modelled obligations on a
    leading-minus remainder operand yields an enclosing (so "-(... % ...)"
    parses back correctly).

    Note: this composite is illustrative, not the locus of discrimination. The
    two obligations are each pinned by the standalone functions above
    (`remainder_operand_level` pins the remainder level; `negated_single_
    operand_enclosed` pins the enclose decision against the cut-off), and each
    is what a deviating implementation fails. The result here is a concrete
    `True` consequence and is not load-bearing for sensing the change."""
    # pre-conditions-start
    # total-correctness obligation for the composite: it must deliver its
    # answer. The strictly larger measure (2 > 1) lets it invoke the two
    # standalone obligations above without leaking its own.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == True)
    # post-conditions-end
    # impl-start
    s = remainder_operand_level()
    return negated_single_operand_enclosed(s)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ / refinement-fidelity adversarial audit for sympy__sympy-22080 (nagini).

SPEC STRUCTURE: model.py has 3 contracted impl functions; the @Pure helpers (level_*, encloses, leading_minus_cutoff) live in the FROZEN `pure` spec region so attacks cannot touch them. Attacks may only edit the 3 impl-start/impl-end bodies. Every impl postcondition FULLY value-pins the return: remainder_operand_level -> Result()==level_multiplicative() (=50); negated_single_operand_enclosed -> Result()==encloses(operand_level,55,False) plus <=Mul=>True and >=Pow=>False, and since encloses is a frozen @Pure this pins the bool for every integer operand_level in the precondition domain [40,70]; negated_remainder_is_enclosed -> Result()==True. MustTerminate obligations kill diverging bodies.

atk_1.py  negated_single_operand_enclosed -> `operand_level <= leading_minus_cutoff()` (echo of encloses(ol,55,False)): weakness EXIT 0 CANDIDATE (verifies 15.9s).
atk_6.py  negated_single_operand_enclosed -> `encloses(operand_level, leading_minus_cutoff(), operand_level > level_function())` (partial-domain: strict flag only flips for prec>70, out of the real domain): weakness EXIT 0 CANDIDATE (16.5s).
atk_7.py  remainder_operand_level -> dead-branch control-flow (`if level_additive()>level_power(): return level_function(); return level_multiplicative()`): weakness EXIT 0 CANDIDATE (18.1s).
atk_2.py  negated_single_operand_enclosed -> encloses(ol,55,True) (boundary: strict flips ol==55): weakness EXIT 2 NOT-A-COUNTEREXAMPLE (verification failed; spec rejected).
atk_3.py  remainder_operand_level -> level_power() (60): EXIT 2 rejected.
atk_4.py  remainder_operand_level -> self-recursion (violates MustTerminate(1)): EXIT 2 rejected.
atk_5.py  negated_remainder_is_enclosed -> False (violates Result()==True): EXIT 2 rejected.
atk_8.py  negated_single_operand_enclosed -> `operand_level < level_power()` (ol<60; differs from ol<=55 at ol in {56..59}, ungrounded-oracle off-by-one): EXIT 2 rejected.
Positive control (unmodified model.py copy): weakness EXIT 0 CANDIDATE (verifies 17.6s) -> baseline confirms harness setup.

prepatch_reproduced=true: bundle ships model_prepatch.py (cut-off reverted to level_additive()=40, sensed by negated_single_operand_enclosed's own postcondition) and model_prepatch_2.py (remainder level reverted to level_function()=70, sensed by remainder_operand_level's own postcondition). Both documented in refinement.md as failing at their standalone postconditions; the spec senses BOTH gold sites (G-DIFF).

MANDATORY RESOLVE STEP: the 3 CANDIDATEs (atk_1/atk_6/atk_7) are each EXACT semantic echoes of gold on the real operand domain, so each faithful refined patch is BYTE-IDENTICAL to the gold patch (sha1 86308c04...; all three .faithful.patch files hash-match gold.patch). Materialized and RAN through the official harness: `run_resolve('sympy__sympy-22080', <faithful patch>, timeout=1800)` -> RESOLVED: True, COMPLETED: True, note 'resolved', attempts=1, non-flaky; FAIL_TO_PASS all success (test_create_expand_pow_optimization, test_PythonCodePrinter, test_empty_modules), PASS_TO_PASS all success, no failures. Since resolve is content-addressed by patch sha1 and all three patches are identical, this single executed resolve covers all three candidates. Every verifying candidate's faithful patch RESOLVES -> verify => correct holds; no verify-but-wrong exists.

REFINEMENT.MD AUDIT: every leg is R / A-reference / I; axioms region is EMPTY so there are NO A-consumed legs and NO kind-3 (unexpressible-changed-op) legs. Carrier R (int PRECEDENCE 40/50/60/70; int midpoint 55 == float 55.0 because Pow+Mul=110 is even and the value is only used in precedence< / precedence<= comparisons against integer precedences) is exact. A-reference A1 (remainder_operand_level==level_multiplicative() <-> new `"Mod": PRECEDENCE["Mul"]`) and A-references B1/B2/B3 (leading_minus_cutoff / encloses / operand_level <-> `parenthesize(item, 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]), strict=False)` in the `_print_Mul` len(a)==1 & sign=='-' branch) all correspond to the real callees the gold patch edits; axiom_check.py validates them out-of-band against the REAL sympy in the patched container (precedence(Mod)==PRECEDENCE['Mul']; threshold strictly between Mul and Pow and == model midpoint; structural paren-presence wrap decision matches on strength classes 50/50/60/70; all 6 F2P renderings verbatim). Correspondence holds; no double-mask.

VERDICT: SOUND. 8 distinct same-spec wrong-impl attacks run (5 correctly rejected across boundary/wrong-level/divergence/wrong-composite/off-by-one classes; 3 are gold-equivalent echoes whose materialized faithful patches were executed through run_resolve and RESOLVED). The spec's fully value-pinning postconditions over frozen @Pure helpers admit no verify-but-incorrect implementation. verify => correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-22080.

Behaviour under specification (stated as desired behaviour, not as an edit):

When a value-carrying expression is rendered as source code and the rendering
carries a leading minus sign in front of a single operand, the printed text must
parse back to the same value. Whether that one operand needs to be enclosed in
parentheses is decided by comparing how tightly the operand itself re-binds in
the target syntax against a constant cut-off applied to such a leading-minus
rendering. The result-determining contract is purely observable:

  (1) The enclose/leave-bare decision is monotone in how tightly the operand
      re-binds: an operand that re-binds no more tightly than the cut-off is
      enclosed in parentheses; an operand that re-binds more tightly is left
      bare. (The generic "enclose iff the operand does not re-bind strictly
      tighter than its context" rule.)

  (2) A "%"/remainder operand re-binds exactly as tightly as a "*"/product
      operand, and the cut-off applied to a leading-minus single operand sits
      above that level but below a "**"/power operand. Consequently a
      remainder operand and a product operand are both enclosed, while a power
      operand and a function-call operand are left bare. In particular a
      leading-minus remainder operand is enclosed, so e.g. negating a "%"
      expression renders as "-(... % ...)" rather than "-... % ..." and parses
      back to the negated remainder.

The re-binding levels are modelled as small ordered integers (additive <
multiplicative < power < function-call) — just an order-preserving carrier for
the comparisons the contract makes; nothing depends on their exact values, only
on the ordering, so an integer carrier is exact (refinement.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No @ContractOnly axiom is consumed. The re-binding-level ordering and the
#  enclose-in-parentheses rule are modelled deeply in the pure region below and
#  are validated == the real renderer's observable rendering out-of-band by
#  axiom_check.py / G-AX -- A-references, not consumed axioms.)
# axioms-end

# pure-start
@Pure
def level_additive() -> int:
    # re-binding level of an additive ("+"/"-") operand
    return 40

@Pure
def level_multiplicative() -> int:
    # re-binding level of a multiplicative ("*"/"%") operand
    return 50

@Pure
def level_power() -> int:
    # re-binding level of a power ("**") operand
    return 60

@Pure
def level_function() -> int:
    # re-binding level of a function-call operand
    return 70

@Pure
def encloses(operand_level: int, cutoff: int, strict: bool) -> bool:
    """The generic enclose-in-parentheses predicate: a rendered operand is
    enclosed iff it re-binds strictly more loosely than its context, or (in the
    non-strict mode used by default) exactly as loosely. Monotone decreasing in
    `operand_level`."""
    if operand_level < cutoff:
        return True
    if not strict:
        return operand_level <= cutoff
    return False

@Pure
def leading_minus_cutoff() -> int:
    """The cut-off applied to the single operand of a leading-minus rendering.
    It sits above the multiplicative level and below the power level, so a
    leading-minus product- or remainder-level operand is enclosed while a power
    operand need not be -- which is what makes the rendering parse back to the
    intended value."""
    Ensures(level_multiplicative() < Result() and Result() < level_power())
    return (level_power() + level_multiplicative()) // 2
# pure-end

def remainder_operand_level() -> int:
    """The re-binding level of a "%"/remainder operand.

    A remainder operand re-binds exactly as tightly as a "*"/product operand --
    and therefore more loosely than the leading-minus cut-off (so a leading-minus
    remainder operand is enclosed, item (2) above)."""
    # pre-conditions-start
    # total-correctness obligation: the level lookup must actually deliver an
    # answer. The verifier is partial-correctness by default, so without this
    # a diverging body would satisfy the value contract vacuously; the real
    # operation always returns.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # re-binds exactly as tightly as a multiplicative operand ...
    Ensures(Result() == level_multiplicative())
    # ... hence more loosely than a power and more tightly than an additive op.
    Ensures(level_additive() < Result() and Result() < level_power())
    # post-conditions-end
    # impl-start
    return level_multiplicative()
    # impl-end

def negated_single_operand_enclosed(operand_level: int) -> bool:
    """Whether the single operand of a leading-minus rendering is enclosed in
    parentheses, as a function of that operand's own re-binding level.

    The decision compares the operand against the leading-minus cut-off, in the
    default (non-strict) mode.
    """
    # pre-conditions-start
    Requires(level_additive() <= operand_level
             and operand_level <= level_function())
    # total-correctness obligation: the enclose/leave-bare decision must
    # actually be delivered (no diverging body satisfying the value contract
    # vacuously); the real decision procedure always returns.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # the operand is enclosed exactly per the generic rule against the
    # leading-minus cut-off (the default, non-strict mode).
    Ensures(Result() == encloses(operand_level, leading_minus_cutoff(), False))
    # consequences the issue demands, pinned independently of the cut-off's
    # exact value (they hold for ANY cut-off above multiplicative and below
    # power level):
    #   a product / additive / remainder operand (level <= multiplicative) is
    #   enclosed;
    Ensures(Implies(operand_level <= level_multiplicative(), Result() == True))
    #   a power / function operand (level >= power) stays bare.
    Ensures(Implies(operand_level >= level_power(), Result() == False))
    # post-conditions-end
    # impl-start
    return encloses(operand_level, leading_minus_cutoff(), False)
    # impl-end

def negated_remainder_is_enclosed() -> bool:
    """A worked instance: composing the two modelled obligations on a
    leading-minus remainder operand yields an enclosing (so "-(... % ...)"
    parses back correctly).

    Note: this composite is illustrative, not the locus of discrimination. The
    two obligations are each pinned by the standalone functions above
    (`remainder_operand_level` pins the remainder level; `negated_single_
    operand_enclosed` pins the enclose decision against the cut-off), and each
    is what a deviating implementation fails. The result here is a concrete
    `True` consequence and is not load-bearing for sensing the change."""
    # pre-conditions-start
    # total-correctness obligation for the composite: it must deliver its
    # answer. The strictly larger measure (2 > 1) lets it invoke the two
    # standalone obligations above without leaking its own.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == True)
    # post-conditions-end
    # impl-start
    s = remainder_operand_level()
    return negated_single_operand_enclosed(s)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ / refinement-fidelity adversarial audit for sympy__sympy-22080 (nagini).

SPEC STRUCTURE: model.py has 3 contracted impl functions; the @Pure helpers (level_*, encloses, leading_minus_cutoff) live in the FROZEN `pure` spec region so attacks cannot touch them. Attacks may only edit the 3 impl-start/impl-end bodies. Every impl postcondition FULLY value-pins the return: remainder_operand_level -> Result()==level_multiplicative() (=50); negated_single_operand_enclosed -> Result()==encloses(operand_level,55,False) plus <=Mul=>True and >=Pow=>False, and since encloses is a frozen @Pure this pins the bool for every integer operand_level in the precondition domain [40,70]; negated_remainder_is_enclosed -> Result()==True. MustTerminate obligations kill diverging bodies.

atk_1.py  negated_single_operand_enclosed -> `operand_level <= leading_minus_cutoff()` (echo of encloses(ol,55,False)): weakness EXIT 0 CANDIDATE (verifies 15.9s).
atk_6.py  negated_single_operand_enclosed -> `encloses(operand_level, leading_minus_cutoff(), operand_level > level_function())` (partial-domain: strict flag only flips for prec>70, out of the real domain): weakness EXIT 0 CANDIDATE (16.5s).
atk_7.py  remainder_operand_level -> dead-branch control-flow (`if level_additive()>level_power(): return level_function(); return level_multiplicative()`): weakness EXIT 0 CANDIDATE (18.1s).
atk_2.py  negated_single_operand_enclosed -> encloses(ol,55,True) (boundary: strict flips ol==55): weakness EXIT 2 NOT-A-COUNTEREXAMPLE (verification failed; spec rejected).
atk_3.py  remainder_operand_level -> level_power() (60): EXIT 2 rejected.
atk_4.py  remainder_operand_level -> self-recursion (violates MustTerminate(1)): EXIT 2 rejected.
atk_5.py  negated_remainder_is_enclosed -> False (violates Result()==True): EXIT 2 rejected.
atk_8.py  negated_single_operand_enclosed -> `operand_level < level_power()` (ol<60; differs from ol<=55 at ol in {56..59}, ungrounded-oracle off-by-one): EXIT 2 rejected.
Positive control (unmodified model.py copy): weakness EXIT 0 CANDIDATE (verifies 17.6s) -> baseline confirms harness setup.

prepatch_reproduced=true: bundle ships model_prepatch.py (cut-off reverted to level_additive()=40, sensed by negated_single_operand_enclosed's own postcondition) and model_prepatch_2.py (remainder level reverted to level_function()=70, sensed by remainder_operand_level's own postcondition). Both documented in refinement.md as failing at their standalone postconditions; the spec senses BOTH gold sites (G-DIFF).

MANDATORY RESOLVE STEP: the 3 CANDIDATEs (atk_1/atk_6/atk_7) are each EXACT semantic echoes of gold on the real operand domain, so each faithful refined patch is BYTE-IDENTICAL to the gold patch (sha1 86308c04...; all three .faithful.patch files hash-match gold.patch). Materialized and RAN through the official harness: `run_resolve('sympy__sympy-22080', <faithful patch>, timeout=1800)` -> RESOLVED: True, COMPLETED: True, note 'resolved', attempts=1, non-flaky; FAIL_TO_PASS all success (test_create_expand_pow_optimization, test_PythonCodePrinter, test_empty_modules), PASS_TO_PASS all success, no failures. Since resolve is content-addressed by patch sha1 and all three patches are identical, this single executed resolve covers all three candidates. Every verifying candidate's faithful patch RESOLVES -> verify => correct holds; no verify-but-wrong exists.

REFINEMENT.MD AUDIT: every leg is R / A-reference / I; axioms region is EMPTY so there are NO A-consumed legs and NO kind-3 (unexpressible-changed-op) legs. Carrier R (int PRECEDENCE 40/50/60/70; int midpoint 55 == float 55.0 because Pow+Mul=110 is even and the value is only used in precedence< / precedence<= comparisons against integer precedences) is exact. A-reference A1 (remainder_operand_level==level_multiplicative() <-> new `"Mod": PRECEDENCE["Mul"]`) and A-references B1/B2/B3 (leading_minus_cutoff / encloses / operand_level <-> `parenthesize(item, 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]), strict=False)` in the `_print_Mul` len(a)==1 & sign=='-' branch) all correspond to the real callees the gold patch edits; axiom_check.py validates them out-of-band against the REAL sympy in the patched container (precedence(Mod)==PRECEDENCE['Mul']; threshold strictly between Mul and Pow and == model midpoint; structural paren-presence wrap decision matches on strength classes 50/50/60/70; all 6 F2P renderings verbatim). Correspondence holds; no double-mask.

VERDICT: SOUND. 8 distinct same-spec wrong-impl attacks run (5 correctly rejected across boundary/wrong-level/divergence/wrong-composite/off-by-one classes; 3 are gold-equivalent echoes whose materialized faithful patches were executed through run_resolve and RESOLVED). The spec's fully value-pinning postconditions over frozen @Pure helpers admit no verify-but-incorrect implementation. verify => correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of sympy__sympy-22080 nagini bundle. Real repo worktrees (_fb) at base_commit 3f8c8c2377 have the gold patch applied (precedence.py:43 `"Mod": PRECEDENCE["Mul"]`; codeprinter.py:490-495 single-factor leading-minus branch parenthesize(a[0], 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"])) = 55.0). Verified empirically with an mpmath-enabled interpreter against the real repo code:
(1) remainder_operand_level(): model Ensures Result()==level_multiplicative()==50; real precedence(Mod(x,y))==50. AGREE.

(2) encloses/leading_minus_cutoff/negated_single_operand_enclosed: real parenthesize(item, 55.0, strict=False) predicate is prec<=55.0; model encloses(level, 55, False) is identical. Exhaustively compared over integer operand levels 30..79 -> ZERO mismatches. Int carrier 55 vs float 55.0 yield identical comparison outcomes against integer precedences (Pow+Mul=110 even, so integer midpoint == float midpoint; mapping's precision-independence argument confirmed).

(3) Modeled consequences (level<=Mul=>enclosed, level>=Pow=>bare) match the real printer: doprint(-Mod(x,y))='-(x % y)' (wrapped), doprint(-sin(x))='-math.sin(x)' and doprint(-x**3)='-x**3' (bare). All six FAIL_TO_PASS rendering observations reproduce VERBATIM: -(x % y), (-x) % y, x % 2, -(x*x*x*x), -(x*x) + x*x*x*x, pow(x, i) - (x*x).

(4) MustTerminate(1)/(2) obligations faithful: real precedence lookup and parenthesization always return; total-correctness is not a strengthening beyond reality.

(5) Model verifies (scripts/nagini_verify.sh exit 0, 14.5s) and same-spec command returns SAME (exit 0) on the unmodified model, so the audited spec is genuine and byte-identical.
No input found where any modeled function disagrees with the real callee. The spec is neither too strong nor drifted from real repo behavior. Verdict FAITHFUL.

(1) remainder_operand_level(): model Ensures Result()==level_multiplicative()==50; real precedence(Mod(x,y))==50. AGREE.

(2) encloses/leading_minus_cutoff/negated_single_operand_enclosed: real parenthesize(item, 55.0, strict=False) predicate is prec<=55.0; model encloses(level, 55, False) is identical. Exhaustively compared over integer operand levels 30..79 -> ZERO mismatches. Int carrier 55 vs float 55.0 yield identical comparison outcomes against integer precedences (Pow+Mul=110 even, so integer midpoint == float midpoint; mapping's precision-independence argument confirmed).

(3) Modeled consequences (level<=Mul=>enclosed, level>=Pow=>bare) match the real printer: doprint(-Mod(x,y))='-(x % y)' (wrapped), doprint(-sin(x))='-math.sin(x)' and doprint(-x**3)='-x**3' (bare). All six FAIL_TO_PASS rendering observations reproduce VERBATIM: -(x % y), (-x) % y, x % 2, -(x*x*x*x), -(x*x) + x*x*x*x, pow(x, i) - (x*x).

(4) MustTerminate(1)/(2) obligations faithful: real precedence lookup and parenthesization always return; total-correctness is not a strengthening beyond reality.

(5) Model verifies (scripts/nagini_verify.sh exit 0, 14.5s) and same-spec command returns SAME (exit 0) on the unmodified model, so the audited spec is genuine and byte-identical.
No input found where any modeled function disagrees with the real callee. The spec is neither too strong nor drifted from real repo behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leakage.screen (nagini flavor) over the spec view of model.py returns PASSED with zero hard failures; independently re-verified each rule: (L1) no diff markers and no gold-patch changed line reproduced — the discriminators 'Mod: PRECEDENCE[Mul]', the '0.5*(PRECEDENCE[Pow]+PRECEDENCE[Mul])' parenthesize call, and the 'precedence, PRECEDENCE' import are all absent; (L2) neither patched file path (sympy/printing/precedence.py, codeprinter.py) nor dotted module appears; (L2/L5) no patched repo symbol (precedence, PRECEDENCE, parenthesize, _print_Mul, codeprinter) appears in any spec-view identifier or comment — the only 'mod' substrings are model/modelled/mode; (L3) no narration terms (bug/fix/wrong/regression/...). Semantic check: the spec states desired behavior abstractly (a '%'/remainder operand binds as tightly as '*'/product; the leading-minus cutoff sits between multiplicative and power so a negated remainder is enclosed and renders '-(... % ...)'). This is exactly the correct behavior the PUBLIC problem_statement already establishes (it shows pycode(-Mod(x,y)) must be '-(x % y)' not '-x % y' and says the precedence order for '-' and '%' is wrong). Specifying correct behavior is the spec's mandate; the actual edit mechanics (which dict/branch/threshold to change) live only in refinement.md/mapping.md — NOT the consumer spec view — and in the excluded hints_text. No relaxed_leakage flag or RELAXED_LEAKAGE.md present, and none needed. Spec view clean beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.