# P2 adversarial audit — astropy__astropy-7606

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,13 +77,6 @@
     #                       unit of the same (unparsed-name) kind as self;
     #   names_equal       — when the coercion succeeds and yields a same-kind
     #                       unit, that unit carries the same name as self.
-    # TERMINATION: this comparison must RETURN for every operand — the
-    # postconditions below are claimed of a run that reaches the return, so
-    # without this the spec would be satisfied vacuously by a run that never
-    # does. Level 7 (not 2) because the obligation level must strictly exceed
-    # that of any obligated callee, and a call to eq_unit (level 6) on this
-    # method's own argument shape must remain admissible.
-    Requires(MustTerminate(7))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer is produced for EVERY operand; the result is
@@ -106,10 +98,6 @@
     Ensures((Result() == RES_TRUE or Result() == RES_FALSE) == parse_succeeds)
     # post-conditions-end
     # impl-start
-    if not parse_succeeds:
-        # The silent unit-coercion could not denote this operand: decline to
-        # decide rather than fail.
-        return RES_NOTIMPL
     if parsed_same_kind and names_equal:
         return RES_TRUE
     return RES_FALSE
@@ -132,10 +120,6 @@
     #   effectively_unity — when convertible, the conversion factor is unity,
     #                       i.e. the two are the same unit.
     Requires(Implies(effectively_unity, convertible))
-    # TERMINATION: the comparison must RETURN for every operand, so that the
-    # postconditions below are total correctness and not merely partial.
-    # Level 6 leaves room beneath for any obligated callee.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer for EVERY operand; one of the three tags; never
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,13 +77,6 @@
     #                       unit of the same (unparsed-name) kind as self;
     #   names_equal       — when the coercion succeeds and yields a same-kind
     #                       unit, that unit carries the same name as self.
-    # TERMINATION: this comparison must RETURN for every operand — the
-    # postconditions below are claimed of a run that reaches the return, so
-    # without this the spec would be satisfied vacuously by a run that never
-    # does. Level 7 (not 2) because the obligation level must strictly exceed
-    # that of any obligated callee, and a call to eq_unit (level 6) on this
-    # method's own argument shape must remain admissible.
-    Requires(MustTerminate(7))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer is produced for EVERY operand; the result is
@@ -132,10 +124,6 @@
     #   effectively_unity — when convertible, the conversion factor is unity,
     #                       i.e. the two are the same unit.
     Requires(Implies(effectively_unity, convertible))
-    # TERMINATION: the comparison must RETURN for every operand, so that the
-    # postconditions below are total correctness and not merely partial.
-    # Level 6 leaves room beneath for any obligated callee.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer for EVERY operand; one of the three tags; never
@@ -167,9 +155,7 @@
     if is_same:
         return RES_TRUE
     if not parse_succeeds:
-        # The silent unit-coercion could not denote this operand: decline to
-        # decide rather than return a definite (and wrong) "not equal".
-        return RES_NOTIMPL
+        return RES_FALSE
     if not parsed_is_unit:
         return RES_NOTIMPL
     if convertible and effectively_unity:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,13 +77,6 @@
     #                       unit of the same (unparsed-name) kind as self;
     #   names_equal       — when the coercion succeeds and yields a same-kind
     #                       unit, that unit carries the same name as self.
-    # TERMINATION: this comparison must RETURN for every operand — the
-    # postconditions below are claimed of a run that reaches the return, so
-    # without this the spec would be satisfied vacuously by a run that never
-    # does. Level 7 (not 2) because the obligation level must strictly exceed
-    # that of any obligated callee, and a call to eq_unit (level 6) on this
-    # method's own argument shape must remain admissible.
-    Requires(MustTerminate(7))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer is produced for EVERY operand; the result is
@@ -107,10 +99,8 @@
     # post-conditions-end
     # impl-start
     if not parse_succeeds:
-        # The silent unit-coercion could not denote this operand: decline to
-        # decide rather than fail.
         return RES_NOTIMPL
-    if parsed_same_kind and names_equal:
+    if names_equal:
         return RES_TRUE
     return RES_FALSE
     # impl-end
@@ -132,10 +122,6 @@
     #   effectively_unity — when convertible, the conversion factor is unity,
     #                       i.e. the two are the same unit.
     Requires(Implies(effectively_unity, convertible))
-    # TERMINATION: the comparison must RETURN for every operand, so that the
-    # postconditions below are total correctness and not merely partial.
-    # Level 6 leaves room beneath for any obligated callee.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer for EVERY operand; one of the three tags; never
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,13 +77,6 @@
     #                       unit of the same (unparsed-name) kind as self;
     #   names_equal       — when the coercion succeeds and yields a same-kind
     #                       unit, that unit carries the same name as self.
-    # TERMINATION: this comparison must RETURN for every operand — the
-    # postconditions below are claimed of a run that reaches the return, so
-    # without this the spec would be satisfied vacuously by a run that never
-    # does. Level 7 (not 2) because the obligation level must strictly exceed
-    # that of any obligated callee, and a call to eq_unit (level 6) on this
-    # method's own argument shape must remain admissible.
-    Requires(MustTerminate(7))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer is produced for EVERY operand; the result is
@@ -132,10 +124,6 @@
     #   effectively_unity — when convertible, the conversion factor is unity,
     #                       i.e. the two are the same unit.
     Requires(Implies(effectively_unity, convertible))
-    # TERMINATION: the comparison must RETURN for every operand, so that the
-    # postconditions below are total correctness and not merely partial.
-    # Level 6 leaves room beneath for any obligated callee.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer for EVERY operand; one of the three tags; never
@@ -167,12 +155,12 @@
     if is_same:
         return RES_TRUE
     if not parse_succeeds:
-        # The silent unit-coercion could not denote this operand: decline to
-        # decide rather than return a definite (and wrong) "not equal".
         return RES_NOTIMPL
     if not parsed_is_unit:
         return RES_NOTIMPL
     if convertible and effectively_unity:
         return RES_TRUE
+    if not convertible:
+        return RES_NOTIMPL
     return RES_FALSE
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,13 +77,6 @@
     #                       unit of the same (unparsed-name) kind as self;
     #   names_equal       — when the coercion succeeds and yields a same-kind
     #                       unit, that unit carries the same name as self.
-    # TERMINATION: this comparison must RETURN for every operand — the
-    # postconditions below are claimed of a run that reaches the return, so
-    # without this the spec would be satisfied vacuously by a run that never
-    # does. Level 7 (not 2) because the obligation level must strictly exceed
-    # that of any obligated callee, and a call to eq_unit (level 6) on this
-    # method's own argument shape must remain admissible.
-    Requires(MustTerminate(7))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer is produced for EVERY operand; the result is
@@ -132,10 +124,6 @@
     #   effectively_unity — when convertible, the conversion factor is unity,
     #                       i.e. the two are the same unit.
     Requires(Implies(effectively_unity, convertible))
-    # TERMINATION: the comparison must RETURN for every operand, so that the
-    # postconditions below are total correctness and not merely partial.
-    # Level 6 leaves room beneath for any obligated callee.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer for EVERY operand; one of the three tags; never
@@ -166,9 +154,9 @@
     # impl-start
     if is_same:
         return RES_TRUE
+    if effectively_unity:
+        return RES_TRUE
     if not parse_succeeds:
-        # The silent unit-coercion could not denote this operand: decline to
-        # decide rather than return a definite (and wrong) "not equal".
         return RES_NOTIMPL
     if not parsed_is_unit:
         return RES_NOTIMPL
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,13 +77,6 @@
     #                       unit of the same (unparsed-name) kind as self;
     #   names_equal       — when the coercion succeeds and yields a same-kind
     #                       unit, that unit carries the same name as self.
-    # TERMINATION: this comparison must RETURN for every operand — the
-    # postconditions below are claimed of a run that reaches the return, so
-    # without this the spec would be satisfied vacuously by a run that never
-    # does. Level 7 (not 2) because the obligation level must strictly exceed
-    # that of any obligated callee, and a call to eq_unit (level 6) on this
-    # method's own argument shape must remain admissible.
-    Requires(MustTerminate(7))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer is produced for EVERY operand; the result is
@@ -107,12 +99,10 @@
     # post-conditions-end
     # impl-start
     if not parse_succeeds:
-        # The silent unit-coercion could not denote this operand: decline to
-        # decide rather than fail.
         return RES_NOTIMPL
     if parsed_same_kind and names_equal:
         return RES_TRUE
-    return RES_FALSE
+    return RES_NOTIMPL
     # impl-end
 
 
@@ -132,10 +122,6 @@
     #   effectively_unity — when convertible, the conversion factor is unity,
     #                       i.e. the two are the same unit.
     Requires(Implies(effectively_unity, convertible))
-    # TERMINATION: the comparison must RETURN for every operand, so that the
-    # postconditions below are total correctness and not merely partial.
-    # Level 6 leaves room beneath for any obligated callee.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer for EVERY operand; one of the three tags; never
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,13 +77,6 @@
     #                       unit of the same (unparsed-name) kind as self;
     #   names_equal       — when the coercion succeeds and yields a same-kind
     #                       unit, that unit carries the same name as self.
-    # TERMINATION: this comparison must RETURN for every operand — the
-    # postconditions below are claimed of a run that reaches the return, so
-    # without this the spec would be satisfied vacuously by a run that never
-    # does. Level 7 (not 2) because the obligation level must strictly exceed
-    # that of any obligated callee, and a call to eq_unit (level 6) on this
-    # method's own argument shape must remain admissible.
-    Requires(MustTerminate(7))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer is produced for EVERY operand; the result is
@@ -132,10 +124,6 @@
     #   effectively_unity — when convertible, the conversion factor is unity,
     #                       i.e. the two are the same unit.
     Requires(Implies(effectively_unity, convertible))
-    # TERMINATION: the comparison must RETURN for every operand, so that the
-    # postconditions below are total correctness and not merely partial.
-    # Level 6 leaves room beneath for any obligated callee.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer for EVERY operand; one of the three tags; never
@@ -167,12 +155,10 @@
     if is_same:
         return RES_TRUE
     if not parse_succeeds:
-        # The silent unit-coercion could not denote this operand: decline to
-        # decide rather than return a definite (and wrong) "not equal".
         return RES_NOTIMPL
     if not parsed_is_unit:
         return RES_NOTIMPL
-    if convertible and effectively_unity:
+    if effectively_unity:
         return RES_TRUE
     return RES_FALSE
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,13 +77,6 @@
     #                       unit of the same (unparsed-name) kind as self;
     #   names_equal       — when the coercion succeeds and yields a same-kind
     #                       unit, that unit carries the same name as self.
-    # TERMINATION: this comparison must RETURN for every operand — the
-    # postconditions below are claimed of a run that reaches the return, so
-    # without this the spec would be satisfied vacuously by a run that never
-    # does. Level 7 (not 2) because the obligation level must strictly exceed
-    # that of any obligated callee, and a call to eq_unit (level 6) on this
-    # method's own argument shape must remain admissible.
-    Requires(MustTerminate(7))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer is produced for EVERY operand; the result is
@@ -132,10 +124,6 @@
     #   effectively_unity — when convertible, the conversion factor is unity,
     #                       i.e. the two are the same unit.
     Requires(Implies(effectively_unity, convertible))
-    # TERMINATION: the comparison must RETURN for every operand, so that the
-    # postconditions below are total correctness and not merely partial.
-    # Level 6 leaves room beneath for any obligated callee.
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # TOTAL: a definite answer for EVERY operand; one of the three tags; never
@@ -166,13 +154,11 @@
     # impl-start
     if is_same:
         return RES_TRUE
-    if not parse_succeeds:
-        # The silent unit-coercion could not denote this operand: decline to
-        # decide rather than return a definite (and wrong) "not equal".
+    if parse_succeeds:
+        if parsed_is_unit:
+            if convertible and effectively_unity:
+                return RES_TRUE
+            return RES_FALSE
         return RES_NOTIMPL
-    if not parsed_is_unit:
-        return RES_NOTIMPL
-    if convertible and effectively_unity:
-        return RES_TRUE
-    return RES_FALSE
+    return RES_NOTIMPL
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-7606.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Equality of a unit value against an arbitrary operand. The operation first
  tries to coerce the operand into a unit using the silent-parse path of the
  unit factory; that coercion is a PARTIAL operation — it succeeds for some
  operands (strings, existing units, numbers) and is undefined for others (for
  example the ``None`` object, or any object that simply cannot denote a unit).

  The desired behaviour is that the comparison is TOTAL: it must produce an
  answer for EVERY operand and must never propagate a failure to the caller.
  When the operand cannot be coerced into a unit, the comparison declines to
  decide and yields the "not-applicable" sentinel (the value that asks Python
  to let the other operand try, which for ``==`` collapses to "not equal" and
  for membership/``!=`` to the expected result) — it does NOT yield a definite
  decision and it does NOT fail. When the operand CAN be coerced, the
  comparison decides definitely: it is equal exactly when the coerced operand
  is a unit of the same kind carrying the same name (for the unparsed-name
  unit) or, more generally, when the two units are dimensionally the same unit.

  The single behaviour pinned here for the unparsed-name unit is that
  comparison against a non-coercible operand (e.g. ``None``) must yield the
  not-applicable sentinel rather than failing, while comparison against a
  coercible operand still decides equality by same-kind-and-name; and the
  general unit comparison likewise yields the not-applicable sentinel — not a
  definite "not equal" — for an operand that cannot be coerced into a unit.

The three-valued outcome of a comparison (definitely-equal, definitely-not-
equal, or not-applicable/defer) is modelled by a small integer tag. The
partial coercion is characterised by its OBSERVABLE predicates on the operand
(whether the silent parse succeeds, and, when it does, the same-kind / equal-
name / convertibility predicates of the coerced unit) — exactly the predicates
the comparison reads — so the discriminating observable is purely WHICH outcome
the comparison produces, never that it fails.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized library callee: the comparison reads only the observable
#  predicates of the operand's silent unit-coercion — whether that partial
#  coercion succeeds, and, when it does, the same-kind / equal-name /
#  convertibility predicates of the resulting unit. These are modelled
#  abstractly as the input predicates, exactly as the comparison reads them;
#  the coercion factory and the dimensional-comparison helper are unchanged and
#  appear only as the operand predicates, not as consumed axioms. Their fidelity
#  to the real callees is validated out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
# The three-valued comparison outcome (a single integer tag):
#   RES_FALSE   — the comparison decided the operands are NOT equal;
#   RES_TRUE    — the comparison decided the operands ARE equal;
#   RES_NOTIMPL — the comparison declined to decide (the not-applicable
#                 sentinel asking Python to let the other operand try). This is
#                 the outcome required for an operand the coercion cannot handle.
RES_FALSE = 0
RES_TRUE = 1
RES_NOTIMPL = 2
# pure-end


def eq_unparsed_name(parse_succeeds: bool, parsed_same_kind: bool,
                     names_equal: bool) -> int:
    # pre-conditions-start
    # The operand is characterised by the observable predicates the comparison
    # reads off it (plain booleans, no heap permission):
    #   parse_succeeds    — the silent unit-coercion of the operand returns
    #                       normally (False for an operand it cannot denote,
    #                       e.g. None);
    #   parsed_same_kind  — when the coercion succeeds, the coerced operand is a
    #                       unit of the same (unparsed-name) kind as self;
    #   names_equal       — when the coercion succeeds and yields a same-kind
    #                       unit, that unit carries the same name as self.
    # pre-conditions-end
    # post-conditions-start
    # TOTAL: a definite answer is produced for EVERY operand; the result is
    # always one of the three tags and the comparison never fails.
    Ensures(Result() == RES_FALSE or Result() == RES_TRUE
            or Result() == RES_NOTIMPL)
    # NON-COERCIBLE operand -> the not-applicable sentinel, NEVER a failure and
    # NEVER a definite decision. (The discriminating clause: an operand the
    # coercion cannot handle, such as None, defers instead of raising.)
    Ensures(Implies(not parse_succeeds, Result() == RES_NOTIMPL))
    # COERCIBLE operand -> a DEFINITE decision: equal exactly when the coerced
    # operand is a same-kind unit carrying the same name; not equal otherwise.
    Ensures(Implies(parse_succeeds and parsed_same_kind and names_equal,
                    Result() == RES_TRUE))
    Ensures(Implies(parse_succeeds and not (parsed_same_kind and names_equal),
                    Result() == RES_FALSE))
    # A definite decision is reached ONLY for a coercible operand; conversely a
    # non-coercible operand never yields a definite decision.
    Ensures((Result() == RES_TRUE or Result() == RES_FALSE) == parse_succeeds)
    # post-conditions-end
    # impl-start
    if not parse_succeeds:
        # The silent unit-coercion could not denote this operand: decline to
        # decide rather than fail.
        return RES_NOTIMPL
    if parsed_same_kind and names_equal:
        return RES_TRUE
    return RES_FALSE
    # impl-end


def eq_unit(is_same: bool, parse_succeeds: bool, parsed_is_unit: bool,
            convertible: bool, effectively_unity: bool) -> int:
    # pre-conditions-start
    # The general unit comparison reads these observable predicates:
    #   is_same           — the operand is the very same unit object as self;
    #   parse_succeeds    — the silent unit-coercion of the operand returns
    #                       normally (False for a non-coercible operand, e.g.
    #                       None);
    #   parsed_is_unit    — when coercion succeeds, the coerced operand is a
    #                       genuine unit value (vs. some other unit-like object);
    #   convertible       — when the coerced operand is a unit, it is
    #                       dimensionally convertible to self (no conversion
    #                       failure);
    #   effectively_unity — when convertible, the conversion factor is unity,
    #                       i.e. the two are the same unit.
    Requires(Implies(effectively_unity, convertible))
    # pre-conditions-end
    # post-conditions-start
    # TOTAL: a definite answer for EVERY operand; one of the three tags; never
    # fails.
    Ensures(Result() == RES_FALSE or Result() == RES_TRUE
            or Result() == RES_NOTIMPL)
    # The same object is equal to itself.
    Ensures(Implies(is_same, Result() == RES_TRUE))
    # NON-COERCIBLE operand (and not the same object) -> the not-applicable
    # sentinel; NEVER a definite "not equal" and NEVER a failure. (The
    # discriminating clause: a non-coercible operand such as None defers — it
    # does not collapse to a definite decision.)
    Ensures(Implies(not is_same and not parse_succeeds,
                    Result() == RES_NOTIMPL))
    # A coercible operand that is not a genuine unit value -> defer as well
    # (let the operand try).
    Ensures(Implies(not is_same and parse_succeeds and not parsed_is_unit,
                    Result() == RES_NOTIMPL))
    # A coercible genuine unit -> a DEFINITE decision: equal iff the conversion
    # factor is unity; a conversion failure means not equal.
    Ensures(Implies(not is_same and parse_succeeds and parsed_is_unit
                    and convertible and effectively_unity,
                    Result() == RES_TRUE))
    Ensures(Implies(not is_same and parse_succeeds and parsed_is_unit
                    and not (convertible and effectively_unity),
                    Result() == RES_FALSE))
    # post-conditions-end
    # impl-start
    if is_same:
        return RES_TRUE
    if not parse_succeeds:
        # The silent unit-coercion could not denote this operand: decline to
        # decide rather than return a definite (and wrong) "not equal".
        return RES_NOTIMPL
    if not parsed_is_unit:
        return RES_NOTIMPL
    if convertible and effectively_unity:
        return RES_TRUE
    return RES_FALSE
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

NO-AXIOM bundle (meta.json axioms:[], deep_model_references:[]; refinement.md §C confirms every leg R or I, no A-consumed / A-reference deep-model legs). The A-legs reduce to refinement fidelity of the boolean-predicate + three-valued-tag abstraction of the two post-patch dunders (UnrecognizedUnit.__eq__, UnitBase.__eq__); G-PANEL-2 validated that against the real post-patch astropy over ~60 operands. I concentrated adversarial effort on model↔patch correspondence and the determinacy of both spec functions.

SPEC DETERMINACY: both eq_unparsed_name and eq_unit are FULLY pinned by their postconditions on their entire input domains (eq_unit under Requires(Implies(effectively_unity, convertible))). Every in-domain input has exactly one postcondition-forced output tag, so any differing impl cannot verify. The ONLY unconstrained region is eq_unit's precondition-excluded / physically-unreachable combo (not convertible & effectively_unity) — atk_7 targets it.

atk_1 (F2P-load-bearing prepatch: eq_unparsed_name drops the `not parse_succeeds` guard) -> NOT-A-COUNTEREXAMPLE, verification failed (exit 2). Reproduces model_prepatch.py; spec rejects it => prepatch_reproduced=true.
- atk_2 (eq_unit prepatch: RES_FALSE on not parse_succeeds; = model_prepatch_2.py) -> verification failed (exit 2).
- atk_3 (boundary: drop parsed_same_kind conjunct, TRUE when only names_equal) -> verification failed (exit 2).
- atk_4 (ungrounded-oracle: NOTIMPL instead of definite FALSE when not convertible in eq_unit) -> verification failed (exit 2).
- atk_5 (ungrounded-oracle echo: TRUE whenever effectively_unity, before parse/is_unit guards) -> verification failed (exit 2).
- atk_6 (partial-domain: NOTIMPL instead of definite FALSE for coercible non-match in eq_unparsed_name) -> verification failed (exit 2).
- atk_7 (deepest break candidate: drops `convertible and` in eq_unit final branch; differs from gold ONLY on precondition-excluded/unreachable combo) -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 13.4s, exit 0).
- atk_8 (control-flow-effect ECHO: pure nested reorder of eq_unit, same output on every input) -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 13.6s, exit 0).

CANDIDATE RESOLVE (protocol step 2 — MANDATORY materialize+run): both atk_7 and atk_8 are behaviorally identical to gold under the refinement map (atk_8 = pure boolean-tag reorder; atk_7 differs only on not-convertible&effectively_unity, which the precondition excludes and which is physically unreachable since effectively_unity = is_effectively_unity(self._to(other)) is only observed after _to succeeds). Their faithful refined patches are therefore BYTE-IDENTICAL to the gold patch.diff (verified via diff against benchmark-verified/astropy__astropy-7606/patch.diff). Materialized as faithful_patch.diff and EXECUTED through the official harness: swebench_unified.harness.run_resolve('astropy__astropy-7606', <faithful_patch>, run_id='sbu-audit-eq-l1yb1db0', timeout=1800) -> ResolveResult.resolved = True (log resolve_gold.log: 'RESOLVED: True'). Both faithful patches resolve.

Positive control: gold model.py copied to positive_control.py -> CANDIDATE (verifies, 12.9s).

refinement.md AUDIT: legs A1 (R), A2 (R+I), A3 (R+I), B1-B4 (R+I); §C states no kind-3 and empty axiom inventory, consistent with meta.json. No A-consumed/A-reference legs to falsify; the NotImplemented↔RES_NOTIMPL, True↔RES_TRUE, False↔RES_FALSE tag bijection and the parse/kind/name/convertible/effectively_unity observable mapping match the two gold hunks exactly.

VERDICT: SOUND. 8 attacks run (6 correctly rejected by the spec; 2 verifying echoes whose materialized faithful patches are gold and RESOLVE under the official harness). No verifying wrong impl exists whose faithful patch fails to resolve — verify does NOT imply incorrect here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-7606.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Equality of a unit value against an arbitrary operand. The operation first
  tries to coerce the operand into a unit using the silent-parse path of the
  unit factory; that coercion is a PARTIAL operation — it succeeds for some
  operands (strings, existing units, numbers) and is undefined for others (for
  example the ``None`` object, or any object that simply cannot denote a unit).

  The desired behaviour is that the comparison is TOTAL: it must produce an
  answer for EVERY operand and must never propagate a failure to the caller.
  When the operand cannot be coerced into a unit, the comparison declines to
  decide and yields the "not-applicable" sentinel (the value that asks Python
  to let the other operand try, which for ``==`` collapses to "not equal" and
  for membership/``!=`` to the expected result) — it does NOT yield a definite
  decision and it does NOT fail. When the operand CAN be coerced, the
  comparison decides definitely: it is equal exactly when the coerced operand
  is a unit of the same kind carrying the same name (for the unparsed-name
  unit) or, more generally, when the two units are dimensionally the same unit.

  The single behaviour pinned here for the unparsed-name unit is that
  comparison against a non-coercible operand (e.g. ``None``) must yield the
  not-applicable sentinel rather than failing, while comparison against a
  coercible operand still decides equality by same-kind-and-name; and the
  general unit comparison likewise yields the not-applicable sentinel — not a
  definite "not equal" — for an operand that cannot be coerced into a unit.

The three-valued outcome of a comparison (definitely-equal, definitely-not-
equal, or not-applicable/defer) is modelled by a small integer tag. The
partial coercion is characterised by its OBSERVABLE predicates on the operand
(whether the silent parse succeeds, and, when it does, the same-kind / equal-
name / convertibility predicates of the coerced unit) — exactly the predicates
the comparison reads — so the discriminating observable is purely WHICH outcome
the comparison produces, never that it fails.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized library callee: the comparison reads only the observable
#  predicates of the operand's silent unit-coercion — whether that partial
#  coercion succeeds, and, when it does, the same-kind / equal-name /
#  convertibility predicates of the resulting unit. These are modelled
#  abstractly as the input predicates, exactly as the comparison reads them;
#  the coercion factory and the dimensional-comparison helper are unchanged and
#  appear only as the operand predicates, not as consumed axioms. Their fidelity
#  to the real callees is validated out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
# The three-valued comparison outcome (a single integer tag):
#   RES_FALSE   — the comparison decided the operands are NOT equal;
#   RES_TRUE    — the comparison decided the operands ARE equal;
#   RES_NOTIMPL — the comparison declined to decide (the not-applicable
#                 sentinel asking Python to let the other operand try). This is
#                 the outcome required for an operand the coercion cannot handle.
RES_FALSE = 0
RES_TRUE = 1
RES_NOTIMPL = 2
# pure-end


def eq_unparsed_name(parse_succeeds: bool, parsed_same_kind: bool,
                     names_equal: bool) -> int:
    # pre-conditions-start
    # The operand is characterised by the observable predicates the comparison
    # reads off it (plain booleans, no heap permission):
    #   parse_succeeds    — the silent unit-coercion of the operand returns
    #                       normally (False for an operand it cannot denote,
    #                       e.g. None);
    #   parsed_same_kind  — when the coercion succeeds, the coerced operand is a
    #                       unit of the same (unparsed-name) kind as self;
    #   names_equal       — when the coercion succeeds and yields a same-kind
    #                       unit, that unit carries the same name as self.
    # pre-conditions-end
    # post-conditions-start
    # TOTAL: a definite answer is produced for EVERY operand; the result is
    # always one of the three tags and the comparison never fails.
    Ensures(Result() == RES_FALSE or Result() == RES_TRUE
            or Result() == RES_NOTIMPL)
    # NON-COERCIBLE operand -> the not-applicable sentinel, NEVER a failure and
    # NEVER a definite decision. (The discriminating clause: an operand the
    # coercion cannot handle, such as None, defers instead of raising.)
    Ensures(Implies(not parse_succeeds, Result() == RES_NOTIMPL))
    # COERCIBLE operand -> a DEFINITE decision: equal exactly when the coerced
    # operand is a same-kind unit carrying the same name; not equal otherwise.
    Ensures(Implies(parse_succeeds and parsed_same_kind and names_equal,
                    Result() == RES_TRUE))
    Ensures(Implies(parse_succeeds and not (parsed_same_kind and names_equal),
                    Result() == RES_FALSE))
    # A definite decision is reached ONLY for a coercible operand; conversely a
    # non-coercible operand never yields a definite decision.
    Ensures((Result() == RES_TRUE or Result() == RES_FALSE) == parse_succeeds)
    # post-conditions-end
    # impl-start
    if not parse_succeeds:
        # The silent unit-coercion could not denote this operand: decline to
        # decide rather than fail.
        return RES_NOTIMPL
    if parsed_same_kind and names_equal:
        return RES_TRUE
    return RES_FALSE
    # impl-end


def eq_unit(is_same: bool, parse_succeeds: bool, parsed_is_unit: bool,
            convertible: bool, effectively_unity: bool) -> int:
    # pre-conditions-start
    # The general unit comparison reads these observable predicates:
    #   is_same           — the operand is the very same unit object as self;
    #   parse_succeeds    — the silent unit-coercion of the operand returns
    #                       normally (False for a non-coercible operand, e.g.
    #                       None);
    #   parsed_is_unit    — when coercion succeeds, the coerced operand is a
    #                       genuine unit value (vs. some other unit-like object);
    #   convertible       — when the coerced operand is a unit, it is
    #                       dimensionally convertible to self (no conversion
    #                       failure);
    #   effectively_unity — when convertible, the conversion factor is unity,
    #                       i.e. the two are the same unit.
    Requires(Implies(effectively_unity, convertible))
    # pre-conditions-end
    # post-conditions-start
    # TOTAL: a definite answer for EVERY operand; one of the three tags; never
    # fails.
    Ensures(Result() == RES_FALSE or Result() == RES_TRUE
            or Result() == RES_NOTIMPL)
    # The same object is equal to itself.
    Ensures(Implies(is_same, Result() == RES_TRUE))
    # NON-COERCIBLE operand (and not the same object) -> the not-applicable
    # sentinel; NEVER a definite "not equal" and NEVER a failure. (The
    # discriminating clause: a non-coercible operand such as None defers — it
    # does not collapse to a definite decision.)
    Ensures(Implies(not is_same and not parse_succeeds,
                    Result() == RES_NOTIMPL))
    # A coercible operand that is not a genuine unit value -> defer as well
    # (let the operand try).
    Ensures(Implies(not is_same and parse_succeeds and not parsed_is_unit,
                    Result() == RES_NOTIMPL))
    # A coercible genuine unit -> a DEFINITE decision: equal iff the conversion
    # factor is unity; a conversion failure means not equal.
    Ensures(Implies(not is_same and parse_succeeds and parsed_is_unit
                    and convertible and effectively_unity,
                    Result() == RES_TRUE))
    Ensures(Implies(not is_same and parse_succeeds and parsed_is_unit
                    and not (convertible and effectively_unity),
                    Result() == RES_FALSE))
    # post-conditions-end
    # impl-start
    if is_same:
        return RES_TRUE
    if not parse_succeeds:
        # The silent unit-coercion could not denote this operand: decline to
        # decide rather than return a definite (and wrong) "not equal".
        return RES_NOTIMPL
    if not parsed_is_unit:
        return RES_NOTIMPL
    if convertible and effectively_unity:
        return RES_TRUE
    return RES_FALSE
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

NO-AXIOM bundle (meta.json axioms:[], deep_model_references:[]; refinement.md §C confirms every leg R or I, no A-consumed / A-reference deep-model legs). The A-legs reduce to refinement fidelity of the boolean-predicate + three-valued-tag abstraction of the two post-patch dunders (UnrecognizedUnit.__eq__, UnitBase.__eq__); G-PANEL-2 validated that against the real post-patch astropy over ~60 operands. I concentrated adversarial effort on model↔patch correspondence and the determinacy of both spec functions.

SPEC DETERMINACY: both eq_unparsed_name and eq_unit are FULLY pinned by their postconditions on their entire input domains (eq_unit under Requires(Implies(effectively_unity, convertible))). Every in-domain input has exactly one postcondition-forced output tag, so any differing impl cannot verify. The ONLY unconstrained region is eq_unit's precondition-excluded / physically-unreachable combo (not convertible & effectively_unity) — atk_7 targets it.

atk_1 (F2P-load-bearing prepatch: eq_unparsed_name drops the `not parse_succeeds` guard) -> NOT-A-COUNTEREXAMPLE, verification failed (exit 2). Reproduces model_prepatch.py; spec rejects it => prepatch_reproduced=true.
- atk_2 (eq_unit prepatch: RES_FALSE on not parse_succeeds; = model_prepatch_2.py) -> verification failed (exit 2).
- atk_3 (boundary: drop parsed_same_kind conjunct, TRUE when only names_equal) -> verification failed (exit 2).
- atk_4 (ungrounded-oracle: NOTIMPL instead of definite FALSE when not convertible in eq_unit) -> verification failed (exit 2).
- atk_5 (ungrounded-oracle echo: TRUE whenever effectively_unity, before parse/is_unit guards) -> verification failed (exit 2).
- atk_6 (partial-domain: NOTIMPL instead of definite FALSE for coercible non-match in eq_unparsed_name) -> verification failed (exit 2).
- atk_7 (deepest break candidate: drops `convertible and` in eq_unit final branch; differs from gold ONLY on precondition-excluded/unreachable combo) -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 13.4s, exit 0).
- atk_8 (control-flow-effect ECHO: pure nested reorder of eq_unit, same output on every input) -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 13.6s, exit 0).

CANDIDATE RESOLVE (protocol step 2 — MANDATORY materialize+run): both atk_7 and atk_8 are behaviorally identical to gold under the refinement map (atk_8 = pure boolean-tag reorder; atk_7 differs only on not-convertible&effectively_unity, which the precondition excludes and which is physically unreachable since effectively_unity = is_effectively_unity(self._to(other)) is only observed after _to succeeds). Their faithful refined patches are therefore BYTE-IDENTICAL to the gold patch.diff (verified via diff against benchmark-verified/astropy__astropy-7606/patch.diff). Materialized as faithful_patch.diff and EXECUTED through the official harness: swebench_unified.harness.run_resolve('astropy__astropy-7606', <faithful_patch>, run_id='sbu-audit-eq-l1yb1db0', timeout=1800) -> ResolveResult.resolved = True (log resolve_gold.log: 'RESOLVED: True'). Both faithful patches resolve.

Positive control: gold model.py copied to positive_control.py -> CANDIDATE (verifies, 12.9s).

refinement.md AUDIT: legs A1 (R), A2 (R+I), A3 (R+I), B1-B4 (R+I); §C states no kind-3 and empty axiom inventory, consistent with meta.json. No A-consumed/A-reference legs to falsify; the NotImplemented↔RES_NOTIMPL, True↔RES_TRUE, False↔RES_FALSE tag bijection and the parse/kind/name/convertible/effectively_unity observable mapping match the two gold hunks exactly.

VERDICT: SOUND. 8 attacks run (6 correctly rejected by the spec; 2 verifying echoes whose materialized faithful patches are gold and RESOLVE under the official harness). No verifying wrong impl exists whose faithful patch fails to resolve — verify does NOT imply incorrect here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec models the POST-patch behavior of UnrecognizedUnit.__eq__ (eq_unparsed_name) and UnitBase.__eq__ (eq_unit), abstracting the operand to the boolean observables the comparison reads. Faithfulness verified against the real callee (installed astropy 5.2.2 carries the exact post-patch source: catches from Unit(...); returns NotImplemented on coercion failure; isinstance(other,type(self)) for unparsed-name). Same-spec toolkit: identical model attack -> SAME (exit 0); model verifies with Nagini in 11.7s.

DIFFERENTIAL FUZZ: 120,000 structured + 200,000 randomized in-domain (self, operand) pairs across diverse selves (m, cm, kg, s, km, g, dimensionless, percent, rad, deg, mol, K, UnrecognizedUnit) and operands (None/object/containers, recognised/unrecognised strings, numbers, unit values, Quantities, composite/scaled units) => 0 disagreements between the model's three-valued tag and the raw dunder return.

TOTALITY-BOUNDARY ANALYSIS (the one place the spec could be too strong): the spec claims totality (Result() is always RES_FALSE/RES_TRUE/RES_NOTIMPL; never fails). The real repo DOES raise on some operands, e.g. u.dimensionless_unscaled == 0 -> ZeroDivisionError (also percent==0, ==0.0, ==False, ==Unit('dimensionless with scale 0')). However EVERY raising input coincides EXACTLY with the region where the mapping's convertible/effectively_unity observable is UNDEFINED: _to() divides by zero and raises a non-UnitsError, and mapping.md defines convertible as '_to does not raise UnitsError'. Such an operand has no faithful boolean assignment => it is outside the abstraction domain. conformance_check.py explicitly discloses and excludes zero for precisely this reason ('the conversion callee divides by zero ... outside the callee's operating domain'). A 200k-operand in-domain raise hunt found ZERO in-domain raises; the only raises are out-of-domain ZeroDivisionError. Thus there is NO operand with well-defined observables where the model disagrees with (or over-claims totality relative to) the real callee.

F2P test_unknown_unit3 (unit=='FOO', unit!=u.m, unit!=None, unit not in (None,u.m)) and P2P test_compare_with_none (not(u.m==None), u.m!=None) both exercise only well-defined-observable operands and agree with the model. The zero-divide raises are a legitimate, documented domain restriction, not spec drift. No diverging in-domain input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-LEAK lexical screen passes (rep.passed=True, hard_failures=[]; recorded meta status 'pass'; no relaxation flag). I independently reviewed the rendered spec view (spec_view over model.py, nagini) for gold-reconstruction beyond the public problem_statement.

Public problem_statement already discloses: `x = u.Unit('asdf', parse_strict='silent'); x == None` raises TypeError in UnrecognizedUnit.__eq__, and the maintainer note that '== should never fail' (so None comparison must return not-equal, not raise). Note: hints_text is NOT counted as public.

Gold edit (patch.diff): wrap `Unit(other, parse_strict='silent')` in try/except returning NotImplemented, and change UnitBase.__eq__'s failure path from `return False` to `return NotImplemented`, plus `isinstance(other, UnrecognizedUnit)` -> `isinstance(other, type(self))`.

Spec-view leak checks:
- L1 diff markers: none. ('try' hit is the English word 'tries' in prose, not a diff/code marker.)
- L1 reproduced gold-patch lines: none (verified: no 'return False', 'NotImplemented', 'type(self)', 'except' etc.).
- L2 patched file/module path: 'astropy/units/core.py' and dotted module absent from spec view.
- L2/L5 patched repo symbols: 'UnrecognizedUnit', '_unrecognized_operator', 'parse_strict', 'isinstance', '__eq__', 'type(self)', 'NotImplemented' all ABSENT from the spec view. Changed-symbol set {'unrecognized_operator'} does not appear.
- L3 narration (bug/fix/patch/previously/wrong/...): none.

The spec describes desired behavior abstractly: comparison is TOTAL, never propagates a failure, yields a 'not-applicable / defer' sentinel (modeled as an integer tag RES_NOTIMPL, NOT named NotImplemented) for non-coercible operands else a definite same-kind/same-name (or dimensional) decision. This is a behavioral specification of exactly what the public problem statement demands ('== should never fail' / None -> not equal), expressed via abstract boolean observables and a three-valued tag. It does not name the sentinel value, the try/except construct, the isinstance(type(self)) generalization, or the patched symbols — so it does not reconstruct the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
