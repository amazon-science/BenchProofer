# P2 adversarial audit — django__django-10999

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     Requires(1 <= len(fields) and len(fields) <= 3)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                              fields[k] >= 0), [[fields[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -107,10 +105,15 @@
     # impl-start
     if inner_sign_seen:
         return None
-    # Accumulate the positional magnitude right-to-left (seconds, minutes,
-    # hours) so the front-recursive clock_value unfolds one field per step.
+    # Pre-patch skeleton: the leading sign is attached to only the FIRST
+    # field's magnitude, not to the whole clock value. We accumulate the
+    # positional magnitude right-to-left; the leading field's contribution
+    # (hours when 3 fields, minutes when 2, seconds when 1) is captured as it
+    # is consumed (last iteration, i == 1) and then sign-flipped on its own,
+    # leaving the rest of the value positive.
     total = 0  # type: int
     weight = 1  # type: int
+    lead_contrib = 0  # type: int
     i = len(fields)
     while i > 0:
         # invariants-start
@@ -118,16 +121,18 @@
         Invariant(0 <= i and i <= len(fields))
         Invariant(weight == pow60(len(fields) - i))
         Invariant(total == clock_value(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
         Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
-        total = fields[i - 1] * weight + total
+        contrib = fields[i - 1] * weight
+        total = contrib + total
+        if i == 1:
+            lead_contrib = contrib
         weight = weight * 60
         i = i - 1
     Assert(total == clock_value(ToSeq(fields)))
     if leading_minus:
-        return -total
+        return total - 2 * lead_contrib
     return total
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     Requires(1 <= len(fields) and len(fields) <= 3)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                              fields[k] >= 0), [[fields[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -105,10 +103,10 @@
                     Result() == signed_total(ToSeq(fields), leading_minus)))
     # post-conditions-end
     # impl-start
-    if inner_sign_seen:
-        return None
-    # Accumulate the positional magnitude right-to-left (seconds, minutes,
-    # hours) so the front-recursive clock_value unfolds one field per step.
+    # Pre-patch skeleton: a sign character after a separator was NOT rejected
+    # (each field carried its own optional sign), so such a literal still
+    # produced a value instead of the absent value. We therefore do not
+    # short-circuit on `inner_sign_seen`; the clock total is computed as usual.
     total = 0  # type: int
     weight = 1  # type: int
     i = len(fields)
@@ -118,7 +116,6 @@
         Invariant(0 <= i and i <= len(fields))
         Invariant(weight == pow60(len(fields) - i))
         Invariant(total == clock_value(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     Requires(1 <= len(fields) and len(fields) <= 3)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                              fields[k] >= 0), [[fields[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -107,19 +105,14 @@
     # impl-start
     if inner_sign_seen:
         return None
-    # Accumulate the positional magnitude right-to-left (seconds, minutes,
-    # hours) so the front-recursive clock_value unfolds one field per step.
     total = 0  # type: int
     weight = 1  # type: int
     i = len(fields)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(weight == pow60(len(fields) - i))
         Invariant(total == clock_value(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
         Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
@@ -127,7 +120,6 @@
         weight = weight * 60
         i = i - 1
     Assert(total == clock_value(ToSeq(fields)))
-    if leading_minus:
-        return -total
+    # WRONG: sign flag ignored entirely (never negates).
     return total
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     Requires(1 <= len(fields) and len(fields) <= 3)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                              fields[k] >= 0), [[fields[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -107,19 +105,14 @@
     # impl-start
     if inner_sign_seen:
         return None
-    # Accumulate the positional magnitude right-to-left (seconds, minutes,
-    # hours) so the front-recursive clock_value unfolds one field per step.
     total = 0  # type: int
     weight = 1  # type: int
     i = len(fields)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(weight == pow60(len(fields) - i))
         Invariant(total == clock_value(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
         Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
@@ -127,6 +120,9 @@
         weight = weight * 60
         i = i - 1
     Assert(total == clock_value(ToSeq(fields)))
+    # WRONG: single-field literals wrongly report the absent value.
+    if len(fields) == 1:
+        return None
     if leading_minus:
         return -total
     return total
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     Requires(1 <= len(fields) and len(fields) <= 3)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                              fields[k] >= 0), [[fields[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -105,21 +103,14 @@
                     Result() == signed_total(ToSeq(fields), leading_minus)))
     # post-conditions-end
     # impl-start
-    if inner_sign_seen:
-        return None
-    # Accumulate the positional magnitude right-to-left (seconds, minutes,
-    # hours) so the front-recursive clock_value unfolds one field per step.
     total = 0  # type: int
     weight = 1  # type: int
     i = len(fields)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(weight == pow60(len(fields) - i))
         Invariant(total == clock_value(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
         Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
@@ -127,7 +118,10 @@
         weight = weight * 60
         i = i - 1
     Assert(total == clock_value(ToSeq(fields)))
-    if leading_minus:
-        return -total
-    return total
+    # WRONG: inverted validity rule (value when inner-sign, None otherwise).
+    if inner_sign_seen:
+        if leading_minus:
+            return -total
+        return total
+    return None
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     Requires(1 <= len(fields) and len(fields) <= 3)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                              fields[k] >= 0), [[fields[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -107,24 +105,19 @@
     # impl-start
     if inner_sign_seen:
         return None
-    # Accumulate the positional magnitude right-to-left (seconds, minutes,
-    # hours) so the front-recursive clock_value unfolds one field per step.
     total = 0  # type: int
     weight = 1  # type: int
     i = len(fields)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(weight == pow60(len(fields) - i))
         Invariant(total == clock_value(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
         Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
         total = fields[i - 1] * weight + total
-        weight = weight * 60
+        weight = weight * 10
         i = i - 1
     Assert(total == clock_value(ToSeq(fields)))
     if leading_minus:
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     Requires(1 <= len(fields) and len(fields) <= 3)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                              fields[k] >= 0), [[fields[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -107,27 +105,5 @@
     # impl-start
     if inner_sign_seen:
         return None
-    # Accumulate the positional magnitude right-to-left (seconds, minutes,
-    # hours) so the front-recursive clock_value unfolds one field per step.
-    total = 0  # type: int
-    weight = 1  # type: int
-    i = len(fields)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(fields), 1 / 2))
-        Invariant(0 <= i and i <= len(fields))
-        Invariant(weight == pow60(len(fields) - i))
-        Invariant(total == clock_value(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
-        Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
-        Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
-        total = fields[i - 1] * weight + total
-        weight = weight * 60
-        i = i - 1
-    Assert(total == clock_value(ToSeq(fields)))
-    if leading_minus:
-        return -total
-    return total
+    return signed_total(ToSeq(fields), leading_minus)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     Requires(1 <= len(fields) and len(fields) <= 3)
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                              fields[k] >= 0), [[fields[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(fields), 1 / 2))
@@ -107,19 +105,14 @@
     # impl-start
     if inner_sign_seen:
         return None
-    # Accumulate the positional magnitude right-to-left (seconds, minutes,
-    # hours) so the front-recursive clock_value unfolds one field per step.
     total = 0  # type: int
     weight = 1  # type: int
     i = len(fields)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(fields), 1 / 2))
         Invariant(0 <= i and i <= len(fields))
         Invariant(weight == pow60(len(fields) - i))
         Invariant(total == clock_value(ToSeq(fields).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
         Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
         Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
@@ -127,7 +120,8 @@
         weight = weight * 60
         i = i - 1
     Assert(total == clock_value(ToSeq(fields)))
+    # WRONG: constant +1 offset.
     if leading_minus:
-        return -total
-    return total
+        return -total + 1
+    return total + 1
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-10999.

Behavioural contract (the result a correct interpretation must produce):

  The operation interprets a colon-separated clock literal into a single
  signed total measured in the smallest unit (seconds). Its inputs are the
  already-extracted carrier of the literal:

    * `fields`  — the 1..3 ordered non-negative field magnitudes;
    * `leading_minus` — whether the literal carried a sign;
    * `inner_sign_seen` — whether the literal's shape is the malformed one
      that has no interpretation.

  The contract on the result, formalised by the `Ensures` clauses below:

    * When the literal has an interpretation, the result equals
      `signed_total(fields, leading_minus)` — the positional base-60
      combination of the fields (`clock_value`) under the sign flag. The
      `clock_value` / `signed_total` helpers spell this arithmetic out so the
      contract is grounded in the inputs, not pinned to an external oracle.

    * When `inner_sign_seen` holds, the literal has no interpretation and the
      result is the absent value.

  The field magnitudes and the two flags are the type-refinement carrier of
  the underlying string literal; the unchanged field-magnitude extraction (a
  run of decimal digits read as a non-negative integer) is the refinement
  boundary documented in mapping.md.

Strings/fields are modelled as `List[int]` of non-negative field magnitudes
(Nagini bans `str` indexing); the specification is carried by `PSeq[int]`. The
absent value is `None`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof: the signed-total
#  interpretation and the validity rule are the changed behaviour and are
#  modelled deeply below. The unchanged decimal-digit field extraction is a
#  type refinement, documented in mapping.md, not an axiom.)
# axioms-end


# pure-start
@Pure
def clock_value(fields: PSeq[int]) -> int:
    """Positional base-60 combination of 1..3 non-negative clock fields, read
    right-to-left: the last field is seconds, the previous minutes, the first
    hours. Front-recursive so a single unfold is available per step.

    For `[H, M, S]` -> `H*3600 + M*60 + S`; `[M, S]` -> `M*60 + S`;
    `[S]` -> `S`; `[]` -> 0.
    """
    if len(fields) == 0:
        return 0
    # The leading field's positional weight is 60**(len-1): hours when 3
    # fields remain, minutes when 2, seconds when 1.
    return fields[0] * pow60(len(fields) - 1) + clock_value(fields.drop(1))


@Pure
def pow60(k: int) -> int:
    """60 ** k for the clock positions k in {0, 1, 2}."""
    Requires(k >= 0)
    Ensures(Result() >= 1)
    if k == 0:
        return 1
    return 60 * pow60(k - 1)


@Pure
def signed_total(fields: PSeq[int], leading_minus: bool) -> int:
    """The signed total: `clock_value(fields)` under the sign flag, i.e.
    `-clock_value(fields)` when `leading_minus` else `clock_value(fields)`."""
    if leading_minus:
        return -clock_value(fields)
    return clock_value(fields)
# pure-end


def parse_clock_seconds(fields: List[int], leading_minus: bool,
                        inner_sign_seen: bool) -> Optional[int]:
    # pre-conditions-start
    # `fields` are the extracted non-negative field magnitudes (read-only);
    # 1..3 of them (seconds; or minutes:seconds; or hours:minutes:seconds).
    Requires(Acc(list_pred(fields), 1 / 2))
    Requires(1 <= len(fields) and len(fields) <= 3)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                             fields[k] >= 0), [[fields[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fields), 1 / 2))
    # The malformed shape has no interpretation: the absent value.
    Ensures(Implies(inner_sign_seen, Result() is None))
    # Otherwise the result is the grounded signed positional total of the
    # fields under the sign flag (clock_value / signed_total).
    Ensures(Implies(not inner_sign_seen,
                    Result() is not None and
                    Result() == signed_total(ToSeq(fields), leading_minus)))
    # post-conditions-end
    # impl-start
    if inner_sign_seen:
        return None
    # Accumulate the positional magnitude right-to-left (seconds, minutes,
    # hours) so the front-recursive clock_value unfolds one field per step.
    total = 0  # type: int
    weight = 1  # type: int
    i = len(fields)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(0 <= i and i <= len(fields))
        Invariant(weight == pow60(len(fields) - i))
        Invariant(total == clock_value(ToSeq(fields).drop(i)))
        # invariants-end
        Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
        Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
        Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
        total = fields[i - 1] * weight + total
        weight = weight * 60
        i = i - 1
    Assert(total == clock_value(ToSeq(fields)))
    if leading_minus:
        return -total
    return total
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-10999 (nagini).

**SPEC SHAPE:** the postcondition TOTALLY pins Result on the entire precondition domain (1<=len(fields)<=3, non-negative). Ensures(Implies(inner_sign_seen, Result() is None)) and Ensures(Implies(not inner_sign_seen, Result() is not None and Result()==signed_total(ToSeq(fields), leading_minus))). signed_total/clock_value/pow60 are FROZEN @Pure spec functions (unchanged region). So any verifying impl is behaviorally determined = gold behaviour up to type refinement.

ATTACKS (all confirmed SAME-spec via `python -m swebench_unified.adversary same-spec nagini django__django-10999 <f>`; then `... weakness ...` for verify).
- atk_1.py (=model_prepatch, whole-value sign bug: total-`2*lead_contrib`): weakness exit=2, verification FAILED -> spec rejects (prepatch bug 1 reproduced).
- atk_2.py (=model_prepatch_2, no inner-sign short-circuit): weakness exit=2, FAILED -> rejected (prepatch bug 2 reproduced).
- atk_3.py (partial-domain: ignore leading_minus, never negate): exit=2, FAILED -> rejected.
- atk_4.py (boundary: return None for single-field literals): exit=2, FAILED -> rejected.
- atk_5.py (control-flow-effect: inverted validity — value on inner-sign, None otherwise): exit=2, FAILED -> rejected.
- atk_6.py (base-10 positional weight instead of base-60): exit=2, FAILED -> rejected.
- atk_7.py (ungrounded-oracle ECHO: return signed_total(ToSeq(fields), leading_minus)): weakness exit=0, CANDIDATE (shares spec AND verifies, 11.9s). This is the CORRECT-behaviour echo, NOT a weakness.
- atk_8.py (+1 constant offset): exit=2, FAILED -> rejected.

POSITIVE CONTROL pos_control.py (=model.py): weakness exit=0, CANDIDATE, verifies 12.0s.

VERIFYING CANDIDATES -> MATERIALIZED FAITHFUL PATCH + run_resolve (protocol step 2): both pos_control and atk_7 are behaviorally identical to the frozen spec (signed_total on valid, None on inner-sign), so the faithful refined patch for each is the gold patch verbatim. meta.json patch_diff is a placeholder ('gold patch verbatim'); extracted the real gold patch from data/swe_bench_verified/test.jsonl -> gold_patch.diff. Ran harness.run_resolve('django__django-10999', gold_patch, run_id='sbu-audit-eq-jcuw8t6-goldresolve'): RESOLVED=True, COMPLETED=True, attempts=1, flaky=False. FAIL_TO_PASS both pass (test_negative, test_parse_postgresql_format); all 10 PASS_TO_PASS pass. So the verifying candidates' faithful patches DO resolve -> spec is NOT broken.

A-LEG / correspondence audit: refinement.md has A1,A2,A3,A5 = R (type refinements), A4 = A-reference (deep model validated ==real by G-AX). No A-consumed axioms (axioms region is a comment only), no kind-3. Ran axiom_check.py (G-AX): exit 0, 'deep model == real post-patch standard_duration_re + parse_duration sign logic on 25 boundary + 50000 fuzz literals'. A-reference correspondence to the real post-patch callee holds. conformance_check.py present (G-CONF) and consistent with mapping.md type bridge.

**CONCLUSION:** >=5 distinct wrong impls (6 genuinely-wrong: 2 prepatch + sign-ignore + single-field-None + inverted-validity + base10-weight + offset) all REJECTED by verification; the only verifying same-spec impls are behaviorally correct and their materialized faithful patch RESOLVES. No verifying wrong impl exists. verify=>correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-10999.

Behavioural contract (the result a correct interpretation must produce):

  The operation interprets a colon-separated clock literal into a single
  signed total measured in the smallest unit (seconds). Its inputs are the
  already-extracted carrier of the literal:

    * `fields`  — the 1..3 ordered non-negative field magnitudes;
    * `leading_minus` — whether the literal carried a sign;
    * `inner_sign_seen` — whether the literal's shape is the malformed one
      that has no interpretation.

  The contract on the result, formalised by the `Ensures` clauses below:

    * When the literal has an interpretation, the result equals
      `signed_total(fields, leading_minus)` — the positional base-60
      combination of the fields (`clock_value`) under the sign flag. The
      `clock_value` / `signed_total` helpers spell this arithmetic out so the
      contract is grounded in the inputs, not pinned to an external oracle.

    * When `inner_sign_seen` holds, the literal has no interpretation and the
      result is the absent value.

  The field magnitudes and the two flags are the type-refinement carrier of
  the underlying string literal; the unchanged field-magnitude extraction (a
  run of decimal digits read as a non-negative integer) is the refinement
  boundary documented in mapping.md.

Strings/fields are modelled as `List[int]` of non-negative field magnitudes
(Nagini bans `str` indexing); the specification is carried by `PSeq[int]`. The
absent value is `None`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof: the signed-total
#  interpretation and the validity rule are the changed behaviour and are
#  modelled deeply below. The unchanged decimal-digit field extraction is a
#  type refinement, documented in mapping.md, not an axiom.)
# axioms-end


# pure-start
@Pure
def clock_value(fields: PSeq[int]) -> int:
    """Positional base-60 combination of 1..3 non-negative clock fields, read
    right-to-left: the last field is seconds, the previous minutes, the first
    hours. Front-recursive so a single unfold is available per step.

    For `[H, M, S]` -> `H*3600 + M*60 + S`; `[M, S]` -> `M*60 + S`;
    `[S]` -> `S`; `[]` -> 0.
    """
    if len(fields) == 0:
        return 0
    # The leading field's positional weight is 60**(len-1): hours when 3
    # fields remain, minutes when 2, seconds when 1.
    return fields[0] * pow60(len(fields) - 1) + clock_value(fields.drop(1))


@Pure
def pow60(k: int) -> int:
    """60 ** k for the clock positions k in {0, 1, 2}."""
    Requires(k >= 0)
    Ensures(Result() >= 1)
    if k == 0:
        return 1
    return 60 * pow60(k - 1)


@Pure
def signed_total(fields: PSeq[int], leading_minus: bool) -> int:
    """The signed total: `clock_value(fields)` under the sign flag, i.e.
    `-clock_value(fields)` when `leading_minus` else `clock_value(fields)`."""
    if leading_minus:
        return -clock_value(fields)
    return clock_value(fields)
# pure-end


def parse_clock_seconds(fields: List[int], leading_minus: bool,
                        inner_sign_seen: bool) -> Optional[int]:
    # pre-conditions-start
    # `fields` are the extracted non-negative field magnitudes (read-only);
    # 1..3 of them (seconds; or minutes:seconds; or hours:minutes:seconds).
    Requires(Acc(list_pred(fields), 1 / 2))
    Requires(1 <= len(fields) and len(fields) <= 3)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                             fields[k] >= 0), [[fields[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fields), 1 / 2))
    # The malformed shape has no interpretation: the absent value.
    Ensures(Implies(inner_sign_seen, Result() is None))
    # Otherwise the result is the grounded signed positional total of the
    # fields under the sign flag (clock_value / signed_total).
    Ensures(Implies(not inner_sign_seen,
                    Result() is not None and
                    Result() == signed_total(ToSeq(fields), leading_minus)))
    # post-conditions-end
    # impl-start
    if inner_sign_seen:
        return None
    # Accumulate the positional magnitude right-to-left (seconds, minutes,
    # hours) so the front-recursive clock_value unfolds one field per step.
    total = 0  # type: int
    weight = 1  # type: int
    i = len(fields)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(0 <= i and i <= len(fields))
        Invariant(weight == pow60(len(fields) - i))
        Invariant(total == clock_value(ToSeq(fields).drop(i)))
        # invariants-end
        Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
        Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
        Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
        total = fields[i - 1] * weight + total
        weight = weight * 60
        i = i - 1
    Assert(total == clock_value(ToSeq(fields)))
    if leading_minus:
        return -total
    return total
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-10999 (nagini).

**SPEC SHAPE:** the postcondition TOTALLY pins Result on the entire precondition domain (1<=len(fields)<=3, non-negative). Ensures(Implies(inner_sign_seen, Result() is None)) and Ensures(Implies(not inner_sign_seen, Result() is not None and Result()==signed_total(ToSeq(fields), leading_minus))). signed_total/clock_value/pow60 are FROZEN @Pure spec functions (unchanged region). So any verifying impl is behaviorally determined = gold behaviour up to type refinement.

ATTACKS (all confirmed SAME-spec via `python -m swebench_unified.adversary same-spec nagini django__django-10999 <f>`; then `... weakness ...` for verify).
- atk_1.py (=model_prepatch, whole-value sign bug: total-`2*lead_contrib`): weakness exit=2, verification FAILED -> spec rejects (prepatch bug 1 reproduced).
- atk_2.py (=model_prepatch_2, no inner-sign short-circuit): weakness exit=2, FAILED -> rejected (prepatch bug 2 reproduced).
- atk_3.py (partial-domain: ignore leading_minus, never negate): exit=2, FAILED -> rejected.
- atk_4.py (boundary: return None for single-field literals): exit=2, FAILED -> rejected.
- atk_5.py (control-flow-effect: inverted validity — value on inner-sign, None otherwise): exit=2, FAILED -> rejected.
- atk_6.py (base-10 positional weight instead of base-60): exit=2, FAILED -> rejected.
- atk_7.py (ungrounded-oracle ECHO: return signed_total(ToSeq(fields), leading_minus)): weakness exit=0, CANDIDATE (shares spec AND verifies, 11.9s). This is the CORRECT-behaviour echo, NOT a weakness.
- atk_8.py (+1 constant offset): exit=2, FAILED -> rejected.

POSITIVE CONTROL pos_control.py (=model.py): weakness exit=0, CANDIDATE, verifies 12.0s.

VERIFYING CANDIDATES -> MATERIALIZED FAITHFUL PATCH + run_resolve (protocol step 2): both pos_control and atk_7 are behaviorally identical to the frozen spec (signed_total on valid, None on inner-sign), so the faithful refined patch for each is the gold patch verbatim. meta.json patch_diff is a placeholder ('gold patch verbatim'); extracted the real gold patch from data/swe_bench_verified/test.jsonl -> gold_patch.diff. Ran harness.run_resolve('django__django-10999', gold_patch, run_id='sbu-audit-eq-jcuw8t6-goldresolve'): RESOLVED=True, COMPLETED=True, attempts=1, flaky=False. FAIL_TO_PASS both pass (test_negative, test_parse_postgresql_format); all 10 PASS_TO_PASS pass. So the verifying candidates' faithful patches DO resolve -> spec is NOT broken.

A-LEG / correspondence audit: refinement.md has A1,A2,A3,A5 = R (type refinements), A4 = A-reference (deep model validated ==real by G-AX). No A-consumed axioms (axioms region is a comment only), no kind-3. Ran axiom_check.py (G-AX): exit 0, 'deep model == real post-patch standard_duration_re + parse_duration sign logic on 25 boundary + 50000 fuzz literals'. A-reference correspondence to the real post-patch callee holds. conformance_check.py present (G-CONF) and consistent with mapping.md type bridge.

**CONCLUSION:** >=5 distinct wrong impls (6 genuinely-wrong: 2 prepatch + sign-ignore + single-field-None + inverted-validity + base10-weight + offset) all REJECTED by verification; the only verifying same-spec impls are behaviorally correct and their materialized faithful patch RESOLVES. No verifying wrong impl exists. verify=>correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled callee: post-patch standard_duration_re + django.utils.dateparse.parse_duration sign logic (sign * timedelta(**kw)), verified present in the worktree (post-patch (?P<sign>-?) + \d+ fields, sign = -1 if kw.pop('sign','+')=='-' else 1). No consumed @ContractOnly axiom; changed behaviour modeled deeply (clock_value/signed_total/inner_sign_seen==>None).

Differential evidence (model reproduced as plain Python vs the REAL patched parse_duration):
- 300k randomized fuzz over the colon-form domain (1-3 fields, leading '-'/none, inner-sign '-'/'+', 1-3 digit runs, zero-padding): 0 divergences.
- 15 boundary literals all agree, including whole-value negation (-15:30 -> -930, -00:01:01 -> -61) and inner-sign rejection (-01:-01, 01:-01, 15:-30, 1:15:-30, -1:-15:30 -> None), plus -0:00:00 -> 0 and leading-zero runs (007:008 -> 428).
- 500k multi-field (H:M:S up to 1e6 each) and 200k single-field up to 1e15: 0 value-level (returned) disagreements; the ~86.4e12 s threshold is where real begins raising OverflowError (below it, exact agreement).

The two discriminating behaviours (single leading sign negates the WHOLE clock value; a sign after a separator yields no standard match -> None) match the real post-patch callee exactly. The spec does not reject inputs the real code accepts, nor force a value the real code does not produce, on the modeled/tested domain. It is faithful, not too strong. (Independent of the separate G-PANEL-3 leakage finding, which concerns problem-statement leakage, not faithfulness.)

**Modeled callee:** post-patch standard_duration_re + django.utils.dateparse.parse_duration sign logic (sign * timedelta(**kw)), verified present in the worktree (post-patch (?P<sign>-?) + \d+ fields, sign = -1 if kw.pop('sign','+')=='-' else 1). No consumed @ContractOnly axiom; changed behaviour modeled deeply (clock_value/signed_total/inner_sign_seen==>None).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the consumer spec view (markers.spec_view over model.py: docstring + axioms/pure/pre-conditions/post-conditions regions; impl elided). The spec view discloses the target BEHAVIOR (leading sign negates the whole clock value via signed_total; inner-sign literals -> absent value; base-60 positional clock_value) but not the gold EDIT.

Mechanical G-LEAK screen passes (rep.passed=True, hard_failures=[]). Verified against public problem_statement only (not hints_text). Confirmed the spec view contains: no diff markers (@@, diff --git, +++, ---, index); no patched file path 'django/utils/dateparse.py' or dotted module 'django.utils.dateparse'; no gold-patch changed line reproduced (>=8 chars); no repo symbols 'parse_duration'/'standard_duration_re'/'timedelta'/'dateparse'; no regex fragments '\d+'/'(?P<sign>-?)'/'re.compile'; no narration terms (bug/fix/patch/...). The patch touches no def/class, so `_patch_changed_symbols` is empty. Only token 'django' present is the instance_id in the docstring title (already public via the task).

All repo-binding specifics (the regex diff, parse_duration sign logic, timedelta arithmetic) live exclusively in mapping.md / refinement.md / axiom_check.py, which are auditor artifacts NOT part of the consumer spec view. A solver reading the spec view learns the contract but cannot reconstruct the gold diff/file/symbols beyond what the public problem_statement already reveals (the problem_statement itself quotes standard_duration_re and the regex, so even the regex identity is public, though it does not appear in the spec view).

meta.json: relaxed_leakage=None, G-LEAK status=pass; no RELAXED_LEAKAGE.md, so no relaxation deferral applies. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
