# P2 adversarial audit — django__django-14349

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_3_prepatch.py`, `atk_4_boundary_last.py`, `atk_6_diverge.py`, `atk_8_mutate.py`, `atk_9_skip_first.py`, `atk_10_overreject.py`, `atk_11_extra_char.py`, `atk_12_partial_len.py`, `atk_15_overreject2.py`, `atk_16_drop_cr.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1_reorder.py`, `atk_2_echo.py`, `atk_5_chain_then_raise.py`, `atk_7_chain_in_loop.py`, `atk_14_accepted_guarded.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_13_other_exc.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl produced a non-resolving faithful patch. FIVE same-spec impls VERIFY (atk_1_reorder, atk_2_echo, atk_5_chain_then_raise, atk_7_chain_in_loop, atk_14_accepted_guarded); all five faithful refined patches were materialized and RUN through the official harness (run_resolve) and ALL FIVE RESOLVED (resolved=True, completed=True, patch_successfully_applied=True, F2P 1/1 ['test_validators (validators.tests.TestValidators)'], P2P 18/18). Root reason the spec survives placement permutation: the postcondition is a strict BICONDITIONAL over the two observables (normal return <=> no-forbidden-code-point AND accepted; Exsures InvalidValue <=> forbidden OR not-accepted). Sequencing the unchanged downstream chain before, after, inside, or under a guard on the screen cannot change the raise-vs-return outcome, because the downstream chain is (on the tested corpus) a pure 2-valued verdict function with no observable side effect and no divergence — so every placement permutation is externally equal to the gold placement. A NOTED but non-breaking A-leg imprecision is reported in notes (the axiom's stated 2-valued domain is slightly over-claimed) — it is unreachable by the F2P/P2P oracle, hence not a G-EQ resolve break.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_reorder.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -126,21 +126,17 @@
                  or accepted is False))
     # post-conditions-end
     # impl-start
+    downstream_validate(accepted)
     i = 0
     while i < len(value):
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
         if is_forbidden(value[i]):
             raise InvalidValue()
         i = i + 1
-    downstream_validate(accepted)
     # impl-end
```

Attack 2 — `atk_2_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -131,16 +131,13 @@
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
         if is_forbidden(value[i]):
             raise InvalidValue()
         i = i + 1
-    downstream_validate(accepted)
+    if not accepted:
+        raise InvalidValue()
     # impl-end
```

Attack 3 — `atk_3_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,21 +126,5 @@
                  or accepted is False))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(value):
-        # invariants-start
-        Invariant(Acc(list_pred(value), 1 / 2))
-        Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(value) - i + 1))
-        # invariants-end
-        if is_forbidden(value[i]):
-            raise InvalidValue()
-        i = i + 1
     downstream_validate(accepted)
     # impl-end
```

Attack 4 — `atk_4_boundary_last.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,16 +127,12 @@
     # post-conditions-end
     # impl-start
     i = 0
-    while i < len(value):
+    while i < len(value) - 1:
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
         if is_forbidden(value[i]):
```

Attack 5 — `atk_5_chain_then_raise.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -131,15 +131,12 @@
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
         if is_forbidden(value[i]):
+            downstream_validate(accepted)
             raise InvalidValue()
         i = i + 1
     downstream_validate(accepted)
```

Attack 6 — `atk_6_diverge.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,17 +126,19 @@
                  or accepted is False))
     # post-conditions-end
     # impl-start
+    if len(value) == 0:
+        while True:
+            # invariants-start
+            Invariant(Acc(list_pred(value), 1 / 2))
+            # invariants-end
+            i = 0
     i = 0
     while i < len(value):
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
         if is_forbidden(value[i]):
```

Attack 7 — `atk_7_chain_in_loop.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -131,14 +131,11 @@
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
+        downstream_validate(accepted)
         if is_forbidden(value[i]):
             raise InvalidValue()
         i = i + 1
```

Attack 8 — `atk_8_mutate.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,17 +126,14 @@
                  or accepted is False))
     # post-conditions-end
     # impl-start
+    value[0] = 0
     i = 0
     while i < len(value):
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
         if is_forbidden(value[i]):
```

Attack 9 — `atk_9_skip_first.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,17 +126,13 @@
                  or accepted is False))
     # post-conditions-end
     # impl-start
-    i = 0
+    i = 1
     while i < len(value):
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
         if is_forbidden(value[i]):
```

Attack 10 — `atk_10_overreject.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,21 +126,5 @@
                  or accepted is False))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(value):
-        # invariants-start
-        Invariant(Acc(list_pred(value), 1 / 2))
-        Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(value) - i + 1))
-        # invariants-end
-        if is_forbidden(value[i]):
-            raise InvalidValue()
-        i = i + 1
-    downstream_validate(accepted)
+    raise InvalidValue()
     # impl-end
```

Attack 11 — `atk_11_extra_char.py` → rejected (same spec, does not verify — good)

```diff
@@ -131,15 +131,11 @@
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
-        if is_forbidden(value[i]):
+        if is_forbidden(value[i]) or value[i] == 47:
             raise InvalidValue()
         i = i + 1
     downstream_validate(accepted)
```

Attack 12 — `atk_12_partial_len.py` → rejected (same spec, does not verify — good)

```diff
@@ -126,21 +126,18 @@
                  or accepted is False))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(value):
-        # invariants-start
-        Invariant(Acc(list_pred(value), 1 / 2))
-        Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(value) - i + 1))
-        # invariants-end
-        if is_forbidden(value[i]):
-            raise InvalidValue()
-        i = i + 1
+    if len(value) >= 4:
+        i = 0
+        while i < len(value):
+            # invariants-start
+            Invariant(Acc(list_pred(value), 1 / 2))
+            Invariant(0 <= i and i <= len(value))
+            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                      not is_forbidden(value[k])))))
+            Invariant(MustTerminate(len(value) - i + 1))
+            # invariants-end
+            if is_forbidden(value[i]):
+                raise InvalidValue()
+            i = i + 1
     downstream_validate(accepted)
     # impl-end
```

Attack 13 — `atk_13_other_exc.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -131,16 +131,12 @@
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
         if is_forbidden(value[i]):
-            raise InvalidValue()
+            raise ValueError()
         i = i + 1
     downstream_validate(accepted)
     # impl-end
```

Attack 14 — `atk_14_accepted_guarded.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -126,21 +126,18 @@
                  or accepted is False))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(value):
-        # invariants-start
-        Invariant(Acc(list_pred(value), 1 / 2))
-        Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(value) - i + 1))
-        # invariants-end
-        if is_forbidden(value[i]):
-            raise InvalidValue()
-        i = i + 1
+    if accepted:
+        i = 0
+        while i < len(value):
+            # invariants-start
+            Invariant(Acc(list_pred(value), 1 / 2))
+            Invariant(0 <= i and i <= len(value))
+            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                      not is_forbidden(value[k])))))
+            Invariant(MustTerminate(len(value) - i + 1))
+            # invariants-end
+            if is_forbidden(value[i]):
+                raise InvalidValue()
+            i = i + 1
     downstream_validate(accepted)
     # impl-end
```

Attack 15 — `atk_15_overreject2.py` → rejected (same spec, does not verify — good)

```diff
@@ -131,16 +131,13 @@
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
         if is_forbidden(value[i]):
             raise InvalidValue()
         i = i + 1
     downstream_validate(accepted)
+    raise InvalidValue()
     # impl-end
```

Attack 16 — `atk_16_drop_cr.py` → rejected (same spec, does not verify — good)

```diff
@@ -131,15 +131,11 @@
         # invariants-start
         Invariant(Acc(list_pred(value), 1 / 2))
         Invariant(0 <= i and i <= len(value))
-        # no forbidden code point has been seen in the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not is_forbidden(value[k])))))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(value) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(value) - i + 1))
         # invariants-end
-        if is_forbidden(value[i]):
+        if value[i] == 9 or value[i] == 10:
             raise InvalidValue()
         i = i + 1
     downstream_validate(accepted)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14349.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual value is screened before it is accepted as a well-formed locator.
  Three control code points are categorically forbidden anywhere in the value:
  the horizontal tab (U+0009), the line feed (U+000A) and the carriage return
  (U+000D). Their presence must be reported as a rejection, and that rejection
  must take precedence over — and be independent of — the remaining structural
  validation of the value.

  The behaviour pinned here is therefore:

    * If the value contains ANY of the three forbidden control code points
      (anywhere, not only at the ends), the screen REJECTS the value
      (signals a validation failure), regardless of whether the rest of the
      value is otherwise well-formed. This must hold even for a value that the
      remaining structural validation would, on its own, have accepted.

    * If the value contains NONE of the three forbidden code points, the screen
      defers entirely to the remaining structural validation: it returns
      normally exactly when that validation accepts, and reports a rejection
      exactly when that validation rejects. The forbidden-character screen
      neither rescues nor rejects an otherwise-decided value in this case.

  Screening is a bounded scan of the value followed by the downstream verdict:
  the operation MUST actually deliver its answer — return normally or signal
  the rejection (a total-correctness obligation, carried as MustTerminate in
  the precondition). An implementation that diverges before answering would
  satisfy the value postconditions only vacuously and would never validate
  anything.

The value is modelled as a ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); membership of a forbidden code point is stated as an
existential over the code-point list.
The remaining structural validation is an unchanged callee whose only observable
datum is whether it accepts the value (``accepted``); it is axiomatized as a
contract-only function that returns normally iff it accepts and signals a
rejection otherwise. The rejection is a user-defined exception class (a builtin
exception in an ``Exsures`` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class InvalidValue(Exception):
    """The rejection the screen signals when the value is not accepted. A
    user-defined stand-in for the validation error the desired behaviour
    requires (a builtin exception in an ``Exsures`` crashes the Nagini
    translator; mapping.md §2)."""
    pass

# axioms-start
@ContractOnly
def downstream_validate(accepted: bool) -> None:
    """The unchanged remaining structural validation of the value, the callee
    the screen defers to once the forbidden-character check has passed. Its
    only observable datum is ``accepted``: whether this validation accepts the
    value. It returns normally exactly when the value is accepted and signals a
    rejection (the same out-of-band rejection) exactly when it is not.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    # pre-conditions-start
    # The real downstream chain (scheme split, regex, IDN retry, IPv6 recheck)
    # is a bounded computation that always delivers its verdict — it returns
    # or raises, never diverges (exercised on every axiom_check.py input). It
    # therefore takes and discharges a termination obligation, so a caller
    # holding one may defer to it.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal completion is reachable EXACTLY on the accepted case.
    Ensures(accepted is True)
    # Rejection is signalled out of band EXACTLY on the not-accepted case.
    Exsures(InvalidValue, accepted is False)
    # post-conditions-end
# axioms-end

# pure-start
@Pure
def is_forbidden(c: int) -> bool:
    """A single code point is forbidden iff it is the horizontal tab (9), the
    line feed (10) or the carriage return (13)."""
    return c == 9 or c == 10 or c == 13
# pure-end

def validate_url(value: List[int], accepted: bool) -> None:
    # pre-conditions-start
    # ``value`` is only READ (fractional permission, directive 5). ``accepted``
    # is the abstract world-state datum consumed by the remaining structural
    # validation: whether that validation accepts the value.
    Requires(Acc(list_pred(value), 1 / 2))
    # TERMINATION: the screen is a bounded scan of the value followed by the
    # downstream verdict; it must actually ANSWER (return or raise). Nagini is
    # a partial-correctness verifier by default, so without this obligation a
    # diverging implementation (e.g. `while True: pass` inserted after the
    # screen) satisfies every Ensures/Exsures vacuously; the real validator
    # always delivers its verdict.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The value is read-only: returned untouched at the same fractional
    # permission (so the screen cannot have mutated it, directive 5).
    Ensures(Acc(list_pred(value), 1 / 2))
    # Normal completion is reachable EXACTLY when the value has no forbidden
    # control code point AND the remaining structural validation accepts it.
    # The forbidden-character screen alone forces a rejection: a value carrying
    # a forbidden code point can NEVER return normally, even if it would
    # otherwise have been accepted.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
                                           not is_forbidden(value[k])))))
    Ensures(accepted is True)
    # Rejection is signalled EXACTLY when the value carries a forbidden code
    # point OR the remaining structural validation rejects it — the forbidden
    # screen taking precedence (its branch is independent of ``accepted``). The
    # read-only value is re-established on the rejecting path as well.
    Exsures(InvalidValue,
            Acc(list_pred(value), 1 / 2)
            and (Exists(int, lambda k: (0 <= k and k < len(value)
                                        and is_forbidden(value[k])))
                 or accepted is False))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(value):
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= len(value))
        # no forbidden code point has been seen in the visited prefix.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  not is_forbidden(value[k])))))
        # the scan consumes the caller's termination obligation with a
        # strictly decreasing, bounded-below measure (len(value) - i),
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(value) - i + 1))
        # invariants-end
        if is_forbidden(value[i]):
            raise InvalidValue()
        i = i + 1
    downstream_validate(accepted)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. 16 attacks built by copying the bundle model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures/Exsures byte-identical); all 16 + positive_control confirmed byte-identical spec via `python -m swebench_unified.adversary same-spec nagini django__django-14349 <atk>` (16/16 SAME). Verifications run as concurrent background batches of 3 (each Nagini check = 1 JVM+Z3) via `python -m swebench_unified.adversary weakness nagini django__django-14349 <atk>` with SBU_ATTACK_VERIFY_TIMEOUT=600. Schedule-only parallelism; every attack fully verified and reported.

### WEAKNESS RESULTS (exit 0 = CANDIDATE, exit 2 = spec rejected).
### Candidates (5)
- atk_1_reorder.py — downstream chain FIRST, forbidden scan AFTER: CANDIDATE (exit 0, 20.6s).
- atk_2_echo.py — ungrounded-oracle echo: scan, then `if not accepted: raise`, downstream never called: CANDIDATE (exit 0, 19.9s).
- atk_5_chain_then_raise.py — control-flow-EFFECT: on a forbidden code point run the whole downstream chain FIRST, then raise: CANDIDATE (exit 0, 27.7s).
- atk_7_chain_in_loop.py — downstream chain invoked once PER code point, before the per-char screen: CANDIDATE (exit 0, 20.7s).
- atk_14_accepted_guarded.py — PARTIAL DOMAIN keyed on the abstract oracle bit: screen runs ONLY when `accepted` (so the screen is no longer independent of the downstream verdict, contra refinement.md A3): CANDIDATE (exit 0, 15.7s/24.1s two runs).
SPEC-REJECTED (11), each with the real Viper error:
- atk_3_prepatch.py — PREPATCH BUG re-encoded (no screen, straight downstream): 'Postcondition of validate_url might not hold. Assertion Forall(int, lambda k: Implies(0<=k..., not is_forbidden(value[k])))'. PREPATCH REPRODUCED.
- atk_4_boundary_last.py — loop `< len(value)-1`, last char unscreened: same Forall postcondition failure.
- atk_6_diverge.py — partial-domain DIVERGENCE (`while True` on the empty value): 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context' => MustTerminate (refinement.md A5) is load-bearing.
- atk_8_mutate.py — `value[0] = 0`: 'The precondition of value[0] = 0 might not hold. There might be insufficient permission' => the 1/2 read-only permission is load-bearing.
- atk_9_skip_first.py — loop starts i=1: 'Loop invariant might not hold on entry'.
- atk_11_extra_char.py — OVER-BROAD set (also screens '/'): 'Postcondition ... Assertion (Exists(int, ...is_forbidden(value[k])) or accepted is False) might not hold'.
- atk_12_partial_len.py — PARTIAL DOMAIN by length (screen only when len>=4): Forall postcondition failure.
- atk_15_overreject2.py — OVER-REJECTION (screen, defer, then unconditional raise): 'Postcondition ... (Exists(...) or accepted is False) might not hold'.
- atk_16_drop_cr.py — WRONG SET, drops CR (the G-CONF (c) refutation shape): 'Loop invariant might not be preserved'.
- atk_10_overreject.py / atk_13_other_exc.py — NOT credited as spec tightness: these failed for TRANSLATOR reasons, not a spec rejection (atk_13: 'Translation failed / Not supported: Unsupported builtin function' on `raise ValueError()`; atk_10: a nagini main.py AttributeError crash on `to_string`). Because a translator crash proves nothing about the spec, I RE-ENCODED both shapes in translatable form as atk_15_overreject2 (over-rejection) and atk_16_drop_cr (wrong forbidden set) and both are genuinely rejected with real Viper postcondition/invariant errors.
positive_control.py (bundle gold impl, byte-identical) VERIFIES (23.7s, `adversary verify` exit 0).

MANDATORY G-EQ RESOLVE STEP — EXECUTED FOR ALL 5 VERIFYING CANDIDATES, NOT SPECULATED. Faithful patches were built mechanically from the REAL base_commit source: `git show a708f39ce67af174df90c5b5e50ad1976cec7cb8:django/core/validators.py` (the upstream repository) -> validators_base.py; the UNCHANGED remainder of URLValidator.__call__ (lines 103-143, i.e. everything after the isinstance guard: scheme check, super().__call__ regex, urlsplit/punycode IDN retry, IPv6 recheck, 253-byte hostname check) was extracted BYTE-IDENTICALLY into `_downstream_validate` — the concrete realization of the `downstream_validate` callee the model axiomatizes — and each attack's impl-region control flow was transliterated into the new `__call__` over it, with `unsafe_chars = frozenset('\t\r\n')` added per mapping.md §2 and InvalidValue -> ValidationError(self.message, code=self.code, params={'value': value}). Each generated file was compile()-gated.
### EXECUTED RESULTS (all completed=True, no timeouts, no ImageNotFound, attempts=1):
- atk_1_reorder -> patch_atk_1_reorder.diff -> RESOLVED=True, applied=True, F2P 1/1, P2P 18/18 (resolve_atk_1_reorder.json)
- atk_2_echo -> patch_atk_2_echo.diff -> RESOLVED=True, applied=True, F2P 1/1, P2P 18/18 (resolve_atk_2_echo.json)
- atk_5_chain_then_raise -> patch_atk_5_chain_then_raise.diff -> RESOLVED=True, applied=True, F2P 1/1, P2P 18/18 (resolve_atk_5_chain_then_raise.json)
- atk_7_chain_in_loop -> patch_atk_7_chain_in_loop.diff -> RESOLVED=True, applied=True, F2P 1/1, P2P 18/18 (resolve_atk_7_chain_in_loop.json)
- atk_14_accepted_guarded -> patch_atk_14_accepted_guarded.diff -> RESOLVED=True, applied=True, F2P 1/1, P2P 18/18 (resolve_atk_14_accepted_guarded.json)
A pre-check inside the eval image (docker run swebench/sweb.eval.x86_64.django_1776_django-14349:latest, test_patch applied, `./tests/runtests.py validators`) independently showed all four early patches at 'Ran 19 tests ... OK' before the harness runs, agreeing with the harness verdicts. NO verifying wrong impl produced a non-resolving patch => verify=>resolve is NOT falsified.

A-LEG / CORRESPONDENCE AUDIT (refinement.md; R/I legs left to G-CONF). Every leg is R, A-consumed, or I — no kind-3, confirmed against meta.json (axioms: 1 entry kind=A-consumed; deep_model_references=[] so there is NO A-reference deep model to audit, and no dead axiom: the axiom's Ensures/Exsures are both consumed to discharge validate_url's postcondition on the no-forbidden-char path).
- A1 (value: List[int] <-> the `str` argument of __call__) R: verified, str indexing is banned in Nagini; bijection value[k] <-> ord(value[k]).
- A2 (code-point scan <-> `self.unsafe_chars.intersection(value)` with unsafe_chars=frozenset('\t\r\n')) R+I: verified against the gold hunk in patch.diff and against base_commit; frozenset('\t\r\n') iterates the str's characters so truthiness == Exists k. value[k] in {9,10,13} == is_forbidden. Set is exactly {9,10,13}; no flag dependency (both are fixed literals) — mapping.md's empty flag-dependency record is correct.
- A3 (raise InvalidValue <-> raise ValidationError(...)) R: verified; the F2P assertions are assertRaises(ValidationError), so only the raise/no-raise control flow is observed and the message/code/params payload is genuinely unobserved. NOTE the payload claim is only sound because atk_13 (raising a DIFFERENT exception type) is not even expressible/translatable in this model — the spec's Exsures names only InvalidValue, so an undeclared-channel rejection is out of scope rather than proven impossible; harmless here since the refinement fixes ValidationError.
- A4 (downstream_validate <-> the UNCHANGED remainder of URLValidator.__call__) A-consumed: correspondence CHECKED against the real source at base_commit. The gold patch is a single hunk inserting the early check plus one class attribute; I diffed the remainder and it is byte-for-byte unchanged pre/post-patch, and the repo_location in meta.json (validators.py:105-135 pre / :107-137 post, RegexValidator.__call__ :43-51, encoding.py:203 punycode, validators.py:278 validate_ipv6_address) matches the extracted chain. Position (strictly AFTER the new check) also matches. Correspondence HOLDS.
- A5 (Requires(MustTerminate(2)) / axiom's MustTerminate(1)) I: a total-correctness obligation, not an operation, and empirically load-bearing — atk_6_diverge is rejected precisely by the obligation-leak check, so without it a diverging impl would satisfy every Ensures/Exsures vacuously.

NOTED A-LEG IMPRECISION (advisory, does NOT break G-EQ; belongs to G-AX/mapping precision, not refinement fidelity). mapping.md §3.1 and axiom_check.py state the axiom's domain is ALL forbidden-character-free `str` values and that the real callee is total over {accept->None, reject->ValidationError} there.

That is OVER-CLAIMED: I ran the REAL unpatched URLValidator inside the eval image and `'http://?@[::1]'` — which contains NO TAB/LF/CR, so it is squarely inside the stated domain — raises TypeError (from `len(urlsplit(value).hostname)` where hostname is None), a THIRD outcome the 2-valued axiom does not model. axiom_check.py misses it because its fuzz alphabet/oracle fixtures never generate that netloc shape (its 5000 fuzz inputs only assert kind in ('accept','reject'), and the corpus contains no such value); conformance_check.py is honest about the same class, excluding ~2283 of ~102300 generated inputs for exactly this reason, so the defect is a mapping/axiom_check wording+coverage gap rather than a G-CONF flaw.

I attempted to WEAPONIZE it: on `'http://\t?@[::1]'` gold gives ValidationError (the screen fires first) while atk_1/atk_5/atk_7/atk_14 all let the chain run first and escape TypeError — a REAL behavioural divergence from gold, exactly the kind that should break resolve. It does not, because the witness is unreachable by the oracle: I injected each of TAB/LF/CR at every position of all 164 corpus values (fixtures valid_urls.txt/invalid_urls.txt at base_commit + every literal URLValidator TEST_DATA value pre- and post-test_patch), 16140 injected values, and the only non-ValidationError outcomes are the 24 variants of `'http://?@[::1]'`, which is NOT in the F2P/P2P corpus; over the asserted corpus gold vs every attack diverges on 0 values.

Hence all five resolves are genuine and the gate criterion (a verifying wrong impl whose faithful patch does NOT resolve) is not met. Recommend tightening mapping.md §3.1 / axiom_check.py to state the axiom's domain as forbidden-char-free values whose unchanged remainder is 2-valued (and to add the `'http://?@[::1]'` witness), but this is a documentation-precision item for G-AX, not a G-EQ break.

EVIDENCE FILES: atk_*.py, positive_control.py, atk_*.weakness.log (per-attack weakness output + EXIT=), patch_atk_*.diff (5 faithful patches), validators_atk_*.py (5 full patched sources), resolve_atk_*.json (5 executed harness reports with tests_status), resolve_atk_*.log, validators_base.py (base_commit source), probe.py/axprobe.py/aleg.py + their in-container output (A-leg witness and reachability scan), precheck.sh, testpatch.diff.

VERDICT: SOUND — 16 attacks encoded and all fully verified (>=5 required), 5 verifying candidates ALL had faithful patches materialized and RUN through the official harness with executed RESOLVED=True/completed=True, 11 wrong impls correctly rejected by the spec with real Viper errors, prepatch bug reproduced (atk_3), positive control verifies, refinement.md A-legs' correspondence holds with no kind-3 leg. No verifying wrong impl breaks resolve. One advisory axiom-domain over-claim documented above, provably unreachable by the resolve oracle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_3_prepatch.py`, `atk_4_boundary_last.py`, `atk_6_diverge.py`, `atk_8_mutate.py`, `atk_9_skip_first.py`, `atk_10_overreject.py`, `atk_11_extra_char.py`, `atk_12_partial_len.py`, `atk_15_overreject2.py`, `atk_16_drop_cr.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1_reorder.py`, `atk_2_echo.py`, `atk_5_chain_then_raise.py`, `atk_7_chain_in_loop.py`, `atk_14_accepted_guarded.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_13_other_exc.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl produced a non-resolving faithful patch. FIVE same-spec impls VERIFY (atk_1_reorder, atk_2_echo, atk_5_chain_then_raise, atk_7_chain_in_loop, atk_14_accepted_guarded); all five faithful refined patches were materialized and RUN through the official harness (run_resolve) and ALL FIVE RESOLVED (resolved=True, completed=True, patch_successfully_applied=True, F2P 1/1 ['test_validators (validators.tests.TestValidators)'], P2P 18/18). Root reason the spec survives placement permutation: the postcondition is a strict BICONDITIONAL over the two observables (normal return <=> no-forbidden-code-point AND accepted; Exsures InvalidValue <=> forbidden OR not-accepted). Sequencing the unchanged downstream chain before, after, inside, or under a guard on the screen cannot change the raise-vs-return outcome, because the downstream chain is (on the tested corpus) a pure 2-valued verdict function with no observable side effect and no divergence — so every placement permutation is externally equal to the gold placement. A NOTED but non-breaking A-leg imprecision is reported in notes (the axiom's stated 2-valued domain is slightly over-claimed) — it is unreachable by the F2P/P2P oracle, hence not a G-EQ resolve break.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_reorder.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3_prepatch.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_boundary_last.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_chain_then_raise.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_diverge.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_chain_in_loop.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_mutate.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_skip_first.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_overreject.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_extra_char.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_partial_len.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_other_exc.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 14 — `atk_14_accepted_guarded.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15_overreject2.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_drop_cr.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14349.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual value is screened before it is accepted as a well-formed locator.
  Three control code points are categorically forbidden anywhere in the value:
  the horizontal tab (U+0009), the line feed (U+000A) and the carriage return
  (U+000D). Their presence must be reported as a rejection, and that rejection
  must take precedence over — and be independent of — the remaining structural
  validation of the value.

  The behaviour pinned here is therefore:

    * If the value contains ANY of the three forbidden control code points
      (anywhere, not only at the ends), the screen REJECTS the value
      (signals a validation failure), regardless of whether the rest of the
      value is otherwise well-formed. This must hold even for a value that the
      remaining structural validation would, on its own, have accepted.

    * If the value contains NONE of the three forbidden code points, the screen
      defers entirely to the remaining structural validation: it returns
      normally exactly when that validation accepts, and reports a rejection
      exactly when that validation rejects. The forbidden-character screen
      neither rescues nor rejects an otherwise-decided value in this case.

  Screening is a bounded scan of the value followed by the downstream verdict:
  the operation MUST actually deliver its answer — return normally or signal
  the rejection (a total-correctness obligation, carried as MustTerminate in
  the precondition). An implementation that diverges before answering would
  satisfy the value postconditions only vacuously and would never validate
  anything.

The value is modelled as a ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); membership of a forbidden code point is stated as an
existential over the code-point list.
The remaining structural validation is an unchanged callee whose only observable
datum is whether it accepts the value (``accepted``); it is axiomatized as a
contract-only function that returns normally iff it accepts and signals a
rejection otherwise. The rejection is a user-defined exception class (a builtin
exception in an ``Exsures`` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class InvalidValue(Exception):
    """The rejection the screen signals when the value is not accepted. A
    user-defined stand-in for the validation error the desired behaviour
    requires (a builtin exception in an ``Exsures`` crashes the Nagini
    translator; mapping.md §2)."""
    pass

# axioms-start
@ContractOnly
def downstream_validate(accepted: bool) -> None:
    """The unchanged remaining structural validation of the value, the callee
    the screen defers to once the forbidden-character check has passed. Its
    only observable datum is ``accepted``: whether this validation accepts the
    value. It returns normally exactly when the value is accepted and signals a
    rejection (the same out-of-band rejection) exactly when it is not.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    # pre-conditions-start
    # The real downstream chain (scheme split, regex, IDN retry, IPv6 recheck)
    # is a bounded computation that always delivers its verdict — it returns
    # or raises, never diverges (exercised on every axiom_check.py input). It
    # therefore takes and discharges a termination obligation, so a caller
    # holding one may defer to it.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal completion is reachable EXACTLY on the accepted case.
    Ensures(accepted is True)
    # Rejection is signalled out of band EXACTLY on the not-accepted case.
    Exsures(InvalidValue, accepted is False)
    # post-conditions-end
# axioms-end

# pure-start
@Pure
def is_forbidden(c: int) -> bool:
    """A single code point is forbidden iff it is the horizontal tab (9), the
    line feed (10) or the carriage return (13)."""
    return c == 9 or c == 10 or c == 13
# pure-end

def validate_url(value: List[int], accepted: bool) -> None:
    # pre-conditions-start
    # ``value`` is only READ (fractional permission, directive 5). ``accepted``
    # is the abstract world-state datum consumed by the remaining structural
    # validation: whether that validation accepts the value.
    Requires(Acc(list_pred(value), 1 / 2))
    # TERMINATION: the screen is a bounded scan of the value followed by the
    # downstream verdict; it must actually ANSWER (return or raise). Nagini is
    # a partial-correctness verifier by default, so without this obligation a
    # diverging implementation (e.g. `while True: pass` inserted after the
    # screen) satisfies every Ensures/Exsures vacuously; the real validator
    # always delivers its verdict.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The value is read-only: returned untouched at the same fractional
    # permission (so the screen cannot have mutated it, directive 5).
    Ensures(Acc(list_pred(value), 1 / 2))
    # Normal completion is reachable EXACTLY when the value has no forbidden
    # control code point AND the remaining structural validation accepts it.
    # The forbidden-character screen alone forces a rejection: a value carrying
    # a forbidden code point can NEVER return normally, even if it would
    # otherwise have been accepted.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value),
                                           not is_forbidden(value[k])))))
    Ensures(accepted is True)
    # Rejection is signalled EXACTLY when the value carries a forbidden code
    # point OR the remaining structural validation rejects it — the forbidden
    # screen taking precedence (its branch is independent of ``accepted``). The
    # read-only value is re-established on the rejecting path as well.
    Exsures(InvalidValue,
            Acc(list_pred(value), 1 / 2)
            and (Exists(int, lambda k: (0 <= k and k < len(value)
                                        and is_forbidden(value[k])))
                 or accepted is False))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(value):
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= len(value))
        # no forbidden code point has been seen in the visited prefix.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  not is_forbidden(value[k])))))
        # the scan consumes the caller's termination obligation with a
        # strictly decreasing, bounded-below measure (len(value) - i),
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(value) - i + 1))
        # invariants-end
        if is_forbidden(value[i]):
            raise InvalidValue()
        i = i + 1
    downstream_validate(accepted)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. 16 attacks built by copying the bundle model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures/Exsures byte-identical); all 16 + positive_control confirmed byte-identical spec via `python -m swebench_unified.adversary same-spec nagini django__django-14349 <atk>` (16/16 SAME). Verifications run as concurrent background batches of 3 (each Nagini check = 1 JVM+Z3) via `python -m swebench_unified.adversary weakness nagini django__django-14349 <atk>` with SBU_ATTACK_VERIFY_TIMEOUT=600. Schedule-only parallelism; every attack fully verified and reported.

### WEAKNESS RESULTS (exit 0 = CANDIDATE, exit 2 = spec rejected).
### Candidates (5)
- atk_1_reorder.py — downstream chain FIRST, forbidden scan AFTER: CANDIDATE (exit 0, 20.6s).
- atk_2_echo.py — ungrounded-oracle echo: scan, then `if not accepted: raise`, downstream never called: CANDIDATE (exit 0, 19.9s).
- atk_5_chain_then_raise.py — control-flow-EFFECT: on a forbidden code point run the whole downstream chain FIRST, then raise: CANDIDATE (exit 0, 27.7s).
- atk_7_chain_in_loop.py — downstream chain invoked once PER code point, before the per-char screen: CANDIDATE (exit 0, 20.7s).
- atk_14_accepted_guarded.py — PARTIAL DOMAIN keyed on the abstract oracle bit: screen runs ONLY when `accepted` (so the screen is no longer independent of the downstream verdict, contra refinement.md A3): CANDIDATE (exit 0, 15.7s/24.1s two runs).
SPEC-REJECTED (11), each with the real Viper error:
- atk_3_prepatch.py — PREPATCH BUG re-encoded (no screen, straight downstream): 'Postcondition of validate_url might not hold. Assertion Forall(int, lambda k: Implies(0<=k..., not is_forbidden(value[k])))'. PREPATCH REPRODUCED.
- atk_4_boundary_last.py — loop `< len(value)-1`, last char unscreened: same Forall postcondition failure.
- atk_6_diverge.py — partial-domain DIVERGENCE (`while True` on the empty value): 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context' => MustTerminate (refinement.md A5) is load-bearing.
- atk_8_mutate.py — `value[0] = 0`: 'The precondition of value[0] = 0 might not hold. There might be insufficient permission' => the 1/2 read-only permission is load-bearing.
- atk_9_skip_first.py — loop starts i=1: 'Loop invariant might not hold on entry'.
- atk_11_extra_char.py — OVER-BROAD set (also screens '/'): 'Postcondition ... Assertion (Exists(int, ...is_forbidden(value[k])) or accepted is False) might not hold'.
- atk_12_partial_len.py — PARTIAL DOMAIN by length (screen only when len>=4): Forall postcondition failure.
- atk_15_overreject2.py — OVER-REJECTION (screen, defer, then unconditional raise): 'Postcondition ... (Exists(...) or accepted is False) might not hold'.
- atk_16_drop_cr.py — WRONG SET, drops CR (the G-CONF (c) refutation shape): 'Loop invariant might not be preserved'.
- atk_10_overreject.py / atk_13_other_exc.py — NOT credited as spec tightness: these failed for TRANSLATOR reasons, not a spec rejection (atk_13: 'Translation failed / Not supported: Unsupported builtin function' on `raise ValueError()`; atk_10: a nagini main.py AttributeError crash on `to_string`). Because a translator crash proves nothing about the spec, I RE-ENCODED both shapes in translatable form as atk_15_overreject2 (over-rejection) and atk_16_drop_cr (wrong forbidden set) and both are genuinely rejected with real Viper postcondition/invariant errors.
positive_control.py (bundle gold impl, byte-identical) VERIFIES (23.7s, `adversary verify` exit 0).

MANDATORY G-EQ RESOLVE STEP — EXECUTED FOR ALL 5 VERIFYING CANDIDATES, NOT SPECULATED. Faithful patches were built mechanically from the REAL base_commit source: `git show a708f39ce67af174df90c5b5e50ad1976cec7cb8:django/core/validators.py` (the upstream repository) -> validators_base.py; the UNCHANGED remainder of URLValidator.__call__ (lines 103-143, i.e. everything after the isinstance guard: scheme check, super().__call__ regex, urlsplit/punycode IDN retry, IPv6 recheck, 253-byte hostname check) was extracted BYTE-IDENTICALLY into `_downstream_validate` — the concrete realization of the `downstream_validate` callee the model axiomatizes — and each attack's impl-region control flow was transliterated into the new `__call__` over it, with `unsafe_chars = frozenset('\t\r\n')` added per mapping.md §2 and InvalidValue -> ValidationError(self.message, code=self.code, params={'value': value}). Each generated file was compile()-gated.
### EXECUTED RESULTS (all completed=True, no timeouts, no ImageNotFound, attempts=1):
- atk_1_reorder -> patch_atk_1_reorder.diff -> RESOLVED=True, applied=True, F2P 1/1, P2P 18/18 (resolve_atk_1_reorder.json)
- atk_2_echo -> patch_atk_2_echo.diff -> RESOLVED=True, applied=True, F2P 1/1, P2P 18/18 (resolve_atk_2_echo.json)
- atk_5_chain_then_raise -> patch_atk_5_chain_then_raise.diff -> RESOLVED=True, applied=True, F2P 1/1, P2P 18/18 (resolve_atk_5_chain_then_raise.json)
- atk_7_chain_in_loop -> patch_atk_7_chain_in_loop.diff -> RESOLVED=True, applied=True, F2P 1/1, P2P 18/18 (resolve_atk_7_chain_in_loop.json)
- atk_14_accepted_guarded -> patch_atk_14_accepted_guarded.diff -> RESOLVED=True, applied=True, F2P 1/1, P2P 18/18 (resolve_atk_14_accepted_guarded.json)
A pre-check inside the eval image (docker run swebench/sweb.eval.x86_64.django_1776_django-14349:latest, test_patch applied, `./tests/runtests.py validators`) independently showed all four early patches at 'Ran 19 tests ... OK' before the harness runs, agreeing with the harness verdicts. NO verifying wrong impl produced a non-resolving patch => verify=>resolve is NOT falsified.

A-LEG / CORRESPONDENCE AUDIT (refinement.md; R/I legs left to G-CONF). Every leg is R, A-consumed, or I — no kind-3, confirmed against meta.json (axioms: 1 entry kind=A-consumed; deep_model_references=[] so there is NO A-reference deep model to audit, and no dead axiom: the axiom's Ensures/Exsures are both consumed to discharge validate_url's postcondition on the no-forbidden-char path).
- A1 (value: List[int] <-> the `str` argument of __call__) R: verified, str indexing is banned in Nagini; bijection value[k] <-> ord(value[k]).
- A2 (code-point scan <-> `self.unsafe_chars.intersection(value)` with unsafe_chars=frozenset('\t\r\n')) R+I: verified against the gold hunk in patch.diff and against base_commit; frozenset('\t\r\n') iterates the str's characters so truthiness == Exists k. value[k] in {9,10,13} == is_forbidden. Set is exactly {9,10,13}; no flag dependency (both are fixed literals) — mapping.md's empty flag-dependency record is correct.
- A3 (raise InvalidValue <-> raise ValidationError(...)) R: verified; the F2P assertions are assertRaises(ValidationError), so only the raise/no-raise control flow is observed and the message/code/params payload is genuinely unobserved. NOTE the payload claim is only sound because atk_13 (raising a DIFFERENT exception type) is not even expressible/translatable in this model — the spec's Exsures names only InvalidValue, so an undeclared-channel rejection is out of scope rather than proven impossible; harmless here since the refinement fixes ValidationError.
- A4 (downstream_validate <-> the UNCHANGED remainder of URLValidator.__call__) A-consumed: correspondence CHECKED against the real source at base_commit. The gold patch is a single hunk inserting the early check plus one class attribute; I diffed the remainder and it is byte-for-byte unchanged pre/post-patch, and the repo_location in meta.json (validators.py:105-135 pre / :107-137 post, RegexValidator.__call__ :43-51, encoding.py:203 punycode, validators.py:278 validate_ipv6_address) matches the extracted chain. Position (strictly AFTER the new check) also matches. Correspondence HOLDS.
- A5 (Requires(MustTerminate(2)) / axiom's MustTerminate(1)) I: a total-correctness obligation, not an operation, and empirically load-bearing — atk_6_diverge is rejected precisely by the obligation-leak check, so without it a diverging impl would satisfy every Ensures/Exsures vacuously.

NOTED A-LEG IMPRECISION (advisory, does NOT break G-EQ; belongs to G-AX/mapping precision, not refinement fidelity). mapping.md §3.1 and axiom_check.py state the axiom's domain is ALL forbidden-character-free `str` values and that the real callee is total over {accept->None, reject->ValidationError} there.

That is OVER-CLAIMED: I ran the REAL unpatched URLValidator inside the eval image and `'http://?@[::1]'` — which contains NO TAB/LF/CR, so it is squarely inside the stated domain — raises TypeError (from `len(urlsplit(value).hostname)` where hostname is None), a THIRD outcome the 2-valued axiom does not model. axiom_check.py misses it because its fuzz alphabet/oracle fixtures never generate that netloc shape (its 5000 fuzz inputs only assert kind in ('accept','reject'), and the corpus contains no such value); conformance_check.py is honest about the same class, excluding ~2283 of ~102300 generated inputs for exactly this reason, so the defect is a mapping/axiom_check wording+coverage gap rather than a G-CONF flaw.

I attempted to WEAPONIZE it: on `'http://\t?@[::1]'` gold gives ValidationError (the screen fires first) while atk_1/atk_5/atk_7/atk_14 all let the chain run first and escape TypeError — a REAL behavioural divergence from gold, exactly the kind that should break resolve. It does not, because the witness is unreachable by the oracle: I injected each of TAB/LF/CR at every position of all 164 corpus values (fixtures valid_urls.txt/invalid_urls.txt at base_commit + every literal URLValidator TEST_DATA value pre- and post-test_patch), 16140 injected values, and the only non-ValidationError outcomes are the 24 variants of `'http://?@[::1]'`, which is NOT in the F2P/P2P corpus; over the asserted corpus gold vs every attack diverges on 0 values.

Hence all five resolves are genuine and the gate criterion (a verifying wrong impl whose faithful patch does NOT resolve) is not met. Recommend tightening mapping.md §3.1 / axiom_check.py to state the axiom's domain as forbidden-char-free values whose unchanged remainder is 2-valued (and to add the `'http://?@[::1]'` witness), but this is a documentation-precision item for G-AX, not a G-EQ break.

EVIDENCE FILES: atk_*.py, positive_control.py, atk_*.weakness.log (per-attack weakness output + EXIT=), patch_atk_*.diff (5 faithful patches), validators_atk_*.py (5 full patched sources), resolve_atk_*.json (5 executed harness reports with tests_status), resolve_atk_*.log, validators_base.py (base_commit source), probe.py/axprobe.py/aleg.py + their in-container output (A-leg witness and reachability scan), precheck.sh, testpatch.diff.

VERDICT: SOUND — 16 attacks encoded and all fully verified (>=5 required), 5 verifying candidates ALL had faithful patches materialized and RUN through the official harness with executed RESOLVED=True/completed=True, 11 wrong impls correctly rejected by the spec with real Viper errors, prepatch bug reproduced (atk_3), positive control verifies, refinement.md A-legs' correspondence holds with no kind-3 leg. No verifying wrong impl breaks resolve. One advisory axiom-domain over-claim documented above, provably unreachable by the resolve oracle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK LANE: is the spec too strong / does the modeled function disagree with the real callee on some input? I could NOT exhibit a diverging input on the bridge-defined domain. Verdict FAITHFUL.

ENVIRONMENT: fresh worktrees in /tmp. @ a708f39ce6 (base), @ base + patch.diff. python 3.10.20.

### Baselines reproduced
- same-spec on the bundle model itself: SAME, exit 0 (identity baseline for the spec region).
- nagini_verify.sh on bundle model.py: 'Verification successful', 16.27s, exit 0.
- model_prepatch.py FAILS on exactly the discriminating clause: 'Postcondition of validate_url might not hold. Assertion Forall(int, lambda k: Implies(0<=k<len(value), not is_forbidden(value[k]))) might not hold' (exit 1). The spec genuinely senses the change (G-DIFF); it is not vacuous.
- axiom_check.py: exit 0. Seed-robustness: re-ran under 7 alternative fuzz seeds (1,2,7,123,999,31337,424242) - all exit 0, so the totality claim is not seed-luck.
- conformance_check.py: exit 0, 100000 checked inputs, 0 disagreements, all four branches hit (raise=43664 empty=2976 defer-accept=19246 defer-reject=34114), 2283 exclusions reported not hidden.

### INDEPENDENT PROBES (my own alphabet/seeds/exclusion logic, not the bundle's)
1. Differential sweep, 3 seeds x 40k = 120k inputs, alphabet including exotic Unicode (lone surrogate, NUL, VT, FF, NEL, NBSP, ZWSP, BOM, LS U+2028, PS U+2029, ideographic space, U+1F600): 0 model-vs-real disagreements on every seed.
2. EXHAUSTIVE sweep over all strings of length 0-2 over an 18-char alphabet (all three forbidden chars + near-miss whitespace + crash-family chars) appended to 7 deep-reaching prefixes ('', 'http://', 'http://a.com', 'http://[::1]', 'http://?@[::1]', 'ftp://a.co', 'http://localhost'): 2374 checked, 0 disagreements. Separately: the real patched validator ACCEPTED a forbidden-char value 0 times across the entire sweep.
3. OVER-STRONG DIRECTION (the core of my lane). The spec mandates unconditional rejection whenever TAB/LF/CR is present, so it is refuted if the real patched code ever ACCEPTS such a value. (a) systematic injection of each of TAB/LF/CR at EVERY position of 16 known-valid URLs = 1215 inputs; (b) 200000 randomized multi-injections (1-3 forbidden chars) into those valid URLs. Result: 'SPEC mandates reject but REAL ACCEPTED: 0'. (c) converse leg, 120000 forbidden-char-free bridge-defined inputs: 0 model-vs-real disagreements.
4. Repo's OWN oracle fixtures: valid_urls.txt 81/81 checked, 0 mismatches; invalid_urls.txt 67/68 checked, 0 mismatches.
5. All 8 F2P inputs from the test patch: real=reject, model=reject on every one. None falls in the excluded class.
6. Forbidden-set correspondence is exact, not approximate: frozenset('\t\r\n') enumerates to code points {9,10,13}, identical to is_forbidden's {9,10,13}. Verified by enumeration over the full 0x110000 code-point range.
7. Callee determinism (the bridge assumes 'accepted' is a function of the value): 400 varied inputs called 3x each against both the oracle and the neutralized remainder - 0 nondeterministic inputs.
8. MustTerminate(1)/(2) stress: historical catastrophic-backtracking shapes (trailing junk, repeated labels, dash runs, colon runs) at n=20..1280. Worst single call 0.0261s, no divergence. The totality claim is well-founded, and it is load-bearing (it is what rejects a 'while True' same-spec rival).

THE ONE GAP I FOUND, AND WHY IT IS NOT A FAITHFULNESS BREAK There is a real third outcome of the unchanged code: forbidden-char-free values like 'http://?@[::1]', 'ftp://?@[::1]', 'https://?@[::1]', 'ftp://?q@[::ffff:1.2.3.4]', 'http://#@[::1]' raise TypeError ("object of type 'NoneType' has no len()") from len(urlsplit(value).hostname), not ValidationError. On those inputs no boolean 'accepted' models the callee, so the two-valued axiom has no faithful instance. I confirmed this is a genuine hole in the axiom's stated domain by injecting 'http://?@[::1]' into axiom_check.py's invalid partition: it fails loudly with 'downstream axiom unsound: real URLValidator did NOT reject with ValidationError' (exit 1).

However this does NOT make the spec too strong or unfaithful, for four independently checked reasons: (i) it is DISCLOSED, not hidden - mapping.md G-CONF and conformance_check.py's DOMAIN section name this exact class, name the exact TypeError and the exact input 'http://?@[::1]', and the driver COUNTS and REPORTS the 2283 exclusions rather than dropping them; (ii) it is PRE-EXISTING and patch-orthogonal - I reproduced the identical TypeError at base_commit with no unsafe_chars attribute present, so the patch neither causes nor is required to fix it; (iii) the exclusion is bridge-scoped and CANNOT launder the discriminating behaviour - I checked all 45 crash-family variants WITH a forbidden char injected (pre/mid/post x TAB/LF/CR x 5 bases): on the PATCHED repo all 45 are rejected and the model agrees on all 45 (mismatches=0), i.e. the new screen correctly takes precedence over the downstream crash and those inputs are KEPT, not excluded; on the unpatched base the same 45 still TypeError, which is precisely the model_prepatch failure; (iv) the excluded class is disjoint from the oracle - none of the 8 F2P inputs is in it, and only 1 of 149 repo fixture URLs ('http://[::1:2::3]:8080/', a urlsplit ValueError on py3.10) falls in it.

### ENVIRONMENT ARTIFACT (not a spec defect, flagged for the record)
Running the F2P test on the patched repo shows 1 ERROR on value='http://[::1:2::3]:8080/' - a ValueError from python 3.10.20's urllib _check_bracketed_netloc, a stdlib version artifact of this local env, not of the patch. Proof it is patch-independent: on the UNPATCHED base with the same test patch the run is 'FAILED (failures=8, errors=1)' - the same 1 error plus exactly the 8 forbidden-char failures the patch is meant to fix; patched drops the 8 failures and leaves only that 1 pre-existing stdlib error. Per MEMORY, I am NOT scoring this as a spec defect.

CONCLUSION: no diverging input found. The spec's mandated behaviour matches the real patched callee on ~440k independent inputs plus an exhaustive short-string sweep, both fixture oracles, and all 8 F2P inputs; the forbidden set is exactly {9,10,13}; the axiom is seed-robust and its one domain hole is disclosed, pre-existing, oracle-disjoint, and unable to hide the discriminating behaviour. Verdict FAITHFUL. NOTE: 'FAITHFUL' here is my attack failing to break the spec, which per the instructions is not itself a defect - I supply no diverging_input because I found none.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker role 3 (leakage / gold-reconstruction) for django__django-14349/nagini. Audited the ACTUAL consumer projection, not the raw bundle: markers.spec_view(model.py, nagini) — impl region (lines 128-146, incl. the nested invariants) collapses to `...  # implementation elided`; docstring, imports, InvalidValue class, axioms, pure, pre/post-conditions pass through. Spec-region byte-identity confirmed independently: `adversary same-spec nagini django__django-14349 atk.py` -> exit 0 ("SAME"). G-VERIFY re-run: model.py "Verification successful", 23.02s. Only spec_view + modeled_functions + localization reach the agent (eval/dataset.as_dict + eval/prompts._spec_block); mapping.md, patch.diff, refinement.md, meta.json are NEVER in the agent view, so mapping.md §1 quoting the verbatim gold hunk (`unsafe_chars = frozenset('\t\r\n')`, `self.unsafe_chars.intersection(value)`) is out of scope for this gate.

### MECHANICAL EVIDENCE (all clean):
(1) leakage.screen(model.py, nagini, patch.diff) => LeakageReport(hard_failures=[], warnings=[]) — zero findings, no relaxation invoked.

(2) Gold-line reproduction, re-tested by hand with whitespace normalization and WITHOUT the trivial-fragment exemptions (so no false negative from the allowlist): all three added gold lines ABSENT from the spec view.

(3) Gold-symbol collision via AST over the spec view (Name + FunctionDef/ClassDef + Attribute ids): `unsafe_chars`, `frozenset`, `intersection`, `URLValidator`, `ValidationError`, `schemes`, `message`, `code`, `params` all CLEAN. Only `value` collides — the argument name, non-distinctive and localizing nothing. Model identifiers (`validate_url`, `is_forbidden`, `downstream_validate`, `InvalidValue`, `accepted`) name behaviour, not the edit; none echoes a patched repo symbol.

(4) No diff markers, and the patched path `django/core/validators.py` never appears in the spec view. No `scheme`/`regex`/`IDN`/`punycode`/`IPv6` internals leak into the view's contract surface.

(5) Narration scan: the only hits are "...not as an edit" (an explicit ANTI-narration disclaimer), "screened before it is accepted", "diverges before answering", and "`while True: pass` inserted after the screen" (a Nagini partial-correctness justification for MustTerminate). None narrates bug->fix mechanism; no "fix"/"bug"/"patch"/"previously"/"regression"/"bpo" token. Per MEMORY ("G-LEAK rejects 'fixed' and 'copy'") I checked these are measure/termination prose, not fix narration — correct.

SEMANTIC / RECONSTRUCTION TEST (the binding half, judged against problem_statement ONLY, never hints_text): every discriminating concept in the spec view is present in the PUBLIC problem_statement. Token map (PS / hints / test_patch): LF (YES/--/--), CR (YES/--/--), tab (YES/--/YES), "forbidden" (YES/--/--), "reject" (YES/--/YES), "early" (YES/--/--), "all instances" i.e. anywhere-not-just-trailing (YES/--/--), ValidationError (YES/--/YES). The PS verbatim states "the bpo-43882 fix changes URL splitting behavior to strip all instances of LF, CR and tab characters" and "One option is to reject URLs containing the forbidden characters early" — which is precisely and only what the spec pins: the exact three code points {9,10,13} (`is_forbidden`), rejection anywhere in the value (the Exists postcondition), and precedence/independence over the remaining structural validation (the branch independent of `accepted`). The word "forbidden", the three-character set, "reject", "early", and "all instances" are ALL public. Nothing in the spec view is hints_text-only — hints_text here is pure release chatter (duplicate-of-#32074, Python 3.9.5 backport) and contributes zero vocabulary to the view.

ADVERSARIAL CROSS-CHECK: this is deliberately NOT the relaxed-leakage shape (no RELAXED_LEAKAGE.md, no meta.json relaxed_leakage flag, G-LEAK status "pass" not "relaxed") — and it does not need one. Unlike django-15252 / django-14011, there is NO PS<->gold mismatch: the gold implements exactly the first of the two options the PS itself enumerates. The spec does resolve the PS's stated ambiguity (reject-early vs. strip-silently) in favour of reject — but that is the specification's job (a spec must pin ONE behaviour to be faithful), the chosen alternative is quoted verbatim in the public text, and the F2P test outcome ("ValidationError not raised" = a rejection was expected) is itself public in the PS traceback. So the resolution is PS-derivable, not gold-derived.

The gold's MECHANISM — a `frozenset` class attribute intersected against the value, positioned after the isinstance guard — is fully absent; the spec states set membership as an existential over a List[int] code-point carrier (a Nagini-forced abstraction, per mapping.md §2, since Nagini bans str indexing), which is a strictly weaker, mechanism-free formulation. A consumer reading the spec view learns the required behaviour, which is what modes 1/2 intend to give them, and cannot reconstruct the gold edit's shape, symbols, or location.

Note for the panel: meta.json records G-EQ=fail and G-PANEL-1=fail (the spec-too-weak lane). Those are attacker-1's territory and are NOT re-judged here; per MEMORY ("retained attack labels carry the oracle verdict") I did not import that verdict into this gate. The leakage axis is independently clean.

VERDICT: NO-LEAKAGE. No leaking line found; nothing in the spec view exceeds the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
