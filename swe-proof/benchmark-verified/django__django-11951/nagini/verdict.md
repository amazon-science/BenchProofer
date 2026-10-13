# P2 adversarial audit — django__django-11951

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_11.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2.py`, `atk_10.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. Two attacks reached CANDIDATE (share spec AND verify): atk_2 (the recorded G-MUT survivor '<' -> '<=') and atk_10 (compare against the raw backend value, fall back to the clamp). Both are SEMANTICALLY EQUIVALENT to min(requested, clamped_max) on the declared domain (requested>=0, raw_backend_limit>=0), so they are correct-impl controls, not wrong impls. Both faithful refined patches were materialized and EXECUTED through the official harness: both RESOLVED with FAIL_TO_PASS test_explicit_batch_size_respects_max_batch_size passing and 21/21 PASS_TO_PASS green. No verifying impl produced a non-resolving faithful patch, so verify=>correct was not falsified.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,7 @@
     # impl-start
     max_batch_size = clamped_max(raw_backend_limit)
     if requested > 0:
-        if requested < max_batch_size:
-            result = requested
-        else:
-            result = max_batch_size
+        result = requested
     else:
         result = max_batch_size
     return result
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -83,7 +83,7 @@
     # impl-start
     max_batch_size = clamped_max(raw_backend_limit)
     if requested > 0:
-        if requested < max_batch_size:
+        if requested <= max_batch_size:
             result = requested
         else:
             result = max_batch_size
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,10 @@
     # impl-start
     max_batch_size = clamped_max(raw_backend_limit)
     if requested > 0:
-        if requested < max_batch_size:
+        if requested < max_batch_size + 1:
             result = requested
         else:
-            result = max_batch_size
+            result = max_batch_size + 1
     else:
         result = max_batch_size
     return result
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,13 @@
     # impl-start
     max_batch_size = clamped_max(raw_backend_limit)
     if requested > 0:
-        if requested < max_batch_size:
+        if raw_backend_limit < 100:
+            if requested < max_batch_size:
+                result = requested
+            else:
+                result = max_batch_size
+        else:
             result = requested
-        else:
-            result = max_batch_size
     else:
         result = max_batch_size
     return result
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,6 +86,9 @@
         if requested < max_batch_size:
             result = requested
         else:
+            while requested > 0:
+                Invariant(requested > 0)
+                result = max_batch_size
             result = max_batch_size
     else:
         result = max_batch_size
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,7 +86,7 @@
         if requested < max_batch_size:
             result = requested
         else:
-            result = max_batch_size
+            raise ValueError('requested batch size exceeds the backend maximum')
     else:
         result = max_batch_size
     return result
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,13 @@
     # impl-start
     max_batch_size = clamped_max(raw_backend_limit)
     if requested > 0:
-        if requested < max_batch_size:
+        if raw_backend_limit == 333:
+            if requested < max_batch_size:
+                result = requested
+            else:
+                result = max_batch_size
+        else:
             result = requested
-        else:
-            result = max_batch_size
     else:
         result = max_batch_size
     return result
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -88,6 +88,6 @@
         else:
             result = max_batch_size
     else:
-        result = max_batch_size
+        result = 1
     return result
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -82,11 +82,10 @@
     # post-conditions-end
     # impl-start
     max_batch_size = clamped_max(raw_backend_limit)
-    if requested > 0:
-        if requested < max_batch_size:
-            result = requested
-        else:
-            result = max_batch_size
+    if raw_backend_limit < 0:
+        result = effective_batch_size(requested, raw_backend_limit)
+    elif requested > 0:
+        result = requested
     else:
         result = max_batch_size
     return result
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -83,7 +83,7 @@
     # impl-start
     max_batch_size = clamped_max(raw_backend_limit)
     if requested > 0:
-        if requested < max_batch_size:
+        if requested < raw_backend_limit:
             result = requested
         else:
             result = max_batch_size
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -81,13 +81,13 @@
     Ensures(Implies(requested == 0, Result() == clamped_max(raw_backend_limit)))
     # post-conditions-end
     # impl-start
-    max_batch_size = clamped_max(raw_backend_limit)
+    max_batch_size = raw_backend_limit
     if requested > 0:
         if requested < max_batch_size:
             result = requested
         else:
             result = max_batch_size
     else:
-        result = max_batch_size
+        result = clamped_max(raw_backend_limit)
     return result
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -82,12 +82,6 @@
     # post-conditions-end
     # impl-start
     max_batch_size = clamped_max(raw_backend_limit)
-    if requested > 0:
-        if requested < max_batch_size:
-            result = requested
-        else:
-            result = max_batch_size
-    else:
-        result = max_batch_size
+    result = max_batch_size
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11951.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a bulk database write is split into batches, the size of each batch is
  governed by two numbers:

    * a caller-requested size (a positive integer when the caller asks for an
      explicit size, or absent/auto when the caller leaves it to the system),
      and
    * a backend-imposed maximum, which is whatever the backend reports as the
      largest workable batch, but never less than one.

  The effective batch size that drives the slicing of the work into batches
  must respect BOTH bounds:

    * if the caller requested an explicit size, the effective size is the
      smaller of that request and the backend maximum (so an over-large
      request can never exceed what the backend can actually handle), and
    * if the caller requested nothing, the effective size is the backend
      maximum.

  In particular the effective size is always at least one and never exceeds
  the backend maximum, regardless of how large a value the caller requested.
  The number of batches the work is divided into is the ceiling of the item
  count over the effective size, so a request that would have produced too few
  (too large) batches is correctly tightened down to the backend's capacity.

The values involved are ordinary non-negative integers; no string or float
modelling is needed. The backend maximum is modelled as an opaque non-negative
integer the backend reports (clamped up to one), and the auto/absent request is
modelled as the integer zero (a real explicit request is always strictly
positive). Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (no axiomatized callees: the clamp and the min/auto selection are modelled
#  deeply over plain integers)
# axioms-end

# pure-start
@Pure
def clamped_max(raw_backend_limit: int) -> int:
    """The backend-reported maximum, never allowed below one: the backend may
    report any non-negative integer, but the workable maximum is at least
    one."""
    Requires(raw_backend_limit >= 0)
    Ensures(Result() >= 1)
    Ensures(Implies(raw_backend_limit >= 1, Result() == raw_backend_limit))
    Ensures(Implies(raw_backend_limit < 1, Result() == 1))
    if raw_backend_limit >= 1:
        return raw_backend_limit
    return 1
# pure-end

def effective_batch_size(requested: int, raw_backend_limit: int) -> int:
    # pre-conditions-start
    # `requested == 0` models the auto/absent request; a real explicit request
    # is strictly positive. The backend value is a non-negative integer.
    Requires(requested >= 0)
    Requires(raw_backend_limit >= 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result respects the backend maximum (clamped to at least one) ...
    Ensures(Result() >= 1)
    Ensures(Result() <= clamped_max(raw_backend_limit))
    # ... and an explicit request additionally caps the result at that request,
    # the result being exactly the smaller of the two bounds.
    Ensures(Implies(requested > 0, Result() <= requested))
    Ensures(Implies(requested > 0,
                    Result() == (requested if requested <= clamped_max(raw_backend_limit)
                                 else clamped_max(raw_backend_limit))))
    # With no explicit request the result is exactly the backend maximum.
    Ensures(Implies(requested == 0, Result() == clamped_max(raw_backend_limit)))
    # post-conditions-end
    # impl-start
    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        if requested < max_batch_size:
            result = requested
        else:
            result = max_batch_size
    else:
        result = max_batch_size
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ALL WORK IN  Attacks built by gen.py, which splices ONLY the impl-region body of the frozen model.py; `adversary same-spec` returned exit 0 (SAME) for all 12 + the positive control, so axioms/@Pure/Requires/Ensures are byte-identical everywhere.

python -m swebench_unified.adversary weakness nagini django__django-11951 <path>
### RESULTS (exit 2 = spec REJECTED the impl = good; exit 0 = CANDIDATE):
atk_1  PREPATCH BUG re-encoded (explicit request used as-is). exit=2 REJECTED. Its impl region is byte-IDENTICAL to model_prepatch.py's (diff shown empty) => prepatch_reproduced. atk_2  G-MUT recorded survivor, line 86 '<'->'<='. exit=0 CANDIDATE -> patch materialized -> RESOLVED (see below). atk_3  BOUNDARY off-by-one: cap at max_batch_size+1. exit=2 REJECTED. atk_4  PARTIAL DOMAIN: gold min() only when raw_backend_limit<100, else prepatch bug (the F2P's own sqlite max is 999//3=333, inside the broken range). exit=2 REJECTED. atk_5  CONTROL-FLOW EFFECT / DIVERGENCE: infinite `while requested > 0` with Invariant on exactly the buggy path. exit=2 REJECTED -- method-level MustTerminate(2) does the work, so the postconditions cannot go vacuous on a diverging path. atk_6  EXCEPTIONAL EXIT: raise ValueError on the buggy path (no Exsures in the spec). exit=2 REJECTED. atk_7  UNGROUNDED ORACLE ECHO: hardcodes the F2P's raw_backend_limit == 333 and is otherwise the prepatch bug. exit=2 REJECTED. atk_8  AUTO-BRANCH CORRUPTION: gold explicit arm, but requested==0 returns 1 instead of the backend max. exit=2 REJECTED -- both arms of the truthiness split are pinned. atk_9  VACUOUS GUARDED SELF-CALL: gold hidden behind the infeasible guard raw_backend_limit<0, bug on the live path. exit=2 REJECTED. atk_10 SEMANTICS-PRESERVING RESTRUCTURE (declared control): compares against raw_backend_limit, else-arm uses the clamp. exit=0 CANDIDATE -> patch materialized -> RESOLVED. atk_11 DROPPED CLAMP: uses the raw backend value as the cap, so raw==0 yields effective 0 (range(0,n,0) is a repo ValueError).

Targets the max(.,1) half no other attack hits. exit=2 REJECTED (violates Result()>=1). atk_12 IGNORES THE CALLER (mirror over-correction): always returns the backend max, discarding a SMALLER explicit request. exit=2 REJECTED (violates Implies(requested>0, Result()<=requested)).

POSITIVE CONTROL: `adversary verify nagini django__django-11951 positive_control.py` (byte-identical copy of model.py, md5 4f2ccdcc81edc99d1e64a3d088140067) exit=0 VERIFIED.
NON-VACUITY CONTROL (ctl_vacuity.py, Assert(False) in the impl): `bash scripts/nagini_verify.sh` => 'Verification failed... Assertion False might not hold'. The body is genuinely reachable and checked, so every exit-2 above is a real rejection, not an unreachable/vacuous pass.

MANDATORY RESOLVE RUNS (both CANDIDATEs, faithful patches by mkpatch.py transliterating each attack's impl op-for-op via refinement.md's correspondence clamped_max<->max(bulk_batch_size,1), requested<->batch_size truthiness, generated with `git diff` against base_commit 3120490912 in a local clone):
  python resolve.py atk_2  -> swebench_unified.harness.run_resolve -> resolved=true, completed=true, attempts=2, flaky=true ('resolved on attempt 2/3'), F2P success=[test_explicit_batch_size_respects_max_batch_size], P2P 21/21 success, PASS_TO_FAIL empty. The first attempt was an INCOMPLETE measurement under concurrent load on the build host (no 'did not resolve' in the log), which the harness retry policy correctly re-measured rather than recording as a verdict.
  python resolve.py atk_10 -> resolved=true, completed=true, attempts=1, flaky=false, F2P success, P2P 21/21 success.
Both resolve JSONs saved (resolve_atk_2.json, resolve_atk_10.json). So neither CANDIDATE breaks the spec; the two that verified are precisely the two that are behaviourally gold.

WHY THE SPEC IS TIGHT: the postconditions form a TOTAL FUNCTIONAL specification -- Implies(requested>0, Result()==(requested if requested<=clamped_max else clamped_max)) and Implies(requested==0, Result()==clamped_max) pin the exact value on every point of the declared domain (requested>=0, raw_backend_limit>=0), with Result()>=1 and Result()<=clamped_max as redundant reinforcement. There is no room for a value-wrong impl; the only same-spec impls that can verify are min-equivalent restatements (atk_2, atk_10), and both resolve. MustTerminate(2) closes the divergence lane (atk_5) and the absence of an Exsures closes the exceptional lane (atk_6). Consequently the G-MUT survivor '<'->'<=' is a FALSE survivor -- an equivalent mutant, not a spec hole.

A-LEG AUDIT (refinement.md + mapping.md + meta.json). meta axioms==[] -- there is NO consumed @ContractOnly axiom, so there is no assumption surface whose Ensures the proof discharges. The single deep_model_reference is kind 'A-reference': raw_backend_limit as an input integer standing for the UNCHANGED callee ops.bulk_batch_size(fields, objs), plus the max(.,1) clamp modeled deeply as @Pure clamped_max. Leg tags: row1 R, row2 A-reference, row3 R, row4 I, row5 I, row6 R -- every leg is R / A-reference / I, NO kind-3, matching the doc's requirement.

A-reference correspondence CONFIRMED against the real tree at base_commit: I enumerated ALL three bulk_batch_size definitions (git grep 'def bulk_batch_size' => base/operations.py:68 `return len(objs)`; sqlite3/operations.py:27 `500 | max_query_params//len(fields) | len(objs)` with max_query_params=999; oracle/operations.py:624 `max_query_params//len(fields) | len(objs)` with max_query_params=2**16-1). Every branch returns a non-negative int, which is exactly and only the property the model relies on -- the model assumes nothing stronger (not positivity: the clamp max(.,1) is what lifts it, and atk_11 confirms the spec enforces that clamp). Calling it an A-reference rather than a consumed axiom is correct: the value enters solely as an integer parameter.

I re-ran axiom_check.py: exit 0, 'non-negative on 40012 obs; deep model == gold patch min/max arithmetic on 15 boundary + 200000 fuzz pairs'. The 0<->None carrier encoding is sound: bulk_create asserts `batch_size is None or batch_size > 0` (query.py:458), so `if batch_size` is falsy iff None, exactly the requested==0 / requested>0 split. 0 is unreachable at runtime, so encoding it as the auto case cannot misclassify a real input. Modeling-boundary note (not a defect): the model abstracts an expression, not the method, so the NUMBER of bulk_batch_size calls is outside it -- atk_10's faithful patch calls it once and binds the raw value, which is what the patch's own restructuring does too, and it resolved. The callee is a pure formula over len(objs)/len(fields)/max_query_params with no side effects, so call-count is unobservable and the elision is sound.

All 12 attacks + both resolves reached genuine verdicts -- no timeouts, no crashes, nothing inconclusive.

VERDICT: SOUND (advisory). 12 attacks run (>=5 required), all distinct failure modes incl. prepatch bug, G-MUT survivor, boundary, partial-domain, divergence, exception, oracle-echo, vacuous guard, dropped clamp, ignore-caller; 10 rejected; the 2 that verified had their faithful patches EXECUTED through the official harness and BOTH RESOLVED. verify=>correct not falsified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_11.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2.py`, `atk_10.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. Two attacks reached CANDIDATE (share spec AND verify): atk_2 (the recorded G-MUT survivor '<' -> '<=') and atk_10 (compare against the raw backend value, fall back to the clamp). Both are SEMANTICALLY EQUIVALENT to min(requested, clamped_max) on the declared domain (requested>=0, raw_backend_limit>=0), so they are correct-impl controls, not wrong impls. Both faithful refined patches were materialized and EXECUTED through the official harness: both RESOLVED with FAIL_TO_PASS test_explicit_batch_size_respects_max_batch_size passing and 21/21 PASS_TO_PASS green. No verifying impl produced a non-resolving faithful patch, so verify=>correct was not falsified.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11951.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a bulk database write is split into batches, the size of each batch is
  governed by two numbers:

    * a caller-requested size (a positive integer when the caller asks for an
      explicit size, or absent/auto when the caller leaves it to the system),
      and
    * a backend-imposed maximum, which is whatever the backend reports as the
      largest workable batch, but never less than one.

  The effective batch size that drives the slicing of the work into batches
  must respect BOTH bounds:

    * if the caller requested an explicit size, the effective size is the
      smaller of that request and the backend maximum (so an over-large
      request can never exceed what the backend can actually handle), and
    * if the caller requested nothing, the effective size is the backend
      maximum.

  In particular the effective size is always at least one and never exceeds
  the backend maximum, regardless of how large a value the caller requested.
  The number of batches the work is divided into is the ceiling of the item
  count over the effective size, so a request that would have produced too few
  (too large) batches is correctly tightened down to the backend's capacity.

The values involved are ordinary non-negative integers; no string or float
modelling is needed. The backend maximum is modelled as an opaque non-negative
integer the backend reports (clamped up to one), and the auto/absent request is
modelled as the integer zero (a real explicit request is always strictly
positive). Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (no axiomatized callees: the clamp and the min/auto selection are modelled
#  deeply over plain integers)
# axioms-end

# pure-start
@Pure
def clamped_max(raw_backend_limit: int) -> int:
    """The backend-reported maximum, never allowed below one: the backend may
    report any non-negative integer, but the workable maximum is at least
    one."""
    Requires(raw_backend_limit >= 0)
    Ensures(Result() >= 1)
    Ensures(Implies(raw_backend_limit >= 1, Result() == raw_backend_limit))
    Ensures(Implies(raw_backend_limit < 1, Result() == 1))
    if raw_backend_limit >= 1:
        return raw_backend_limit
    return 1
# pure-end

def effective_batch_size(requested: int, raw_backend_limit: int) -> int:
    # pre-conditions-start
    # `requested == 0` models the auto/absent request; a real explicit request
    # is strictly positive. The backend value is a non-negative integer.
    Requires(requested >= 0)
    Requires(raw_backend_limit >= 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result respects the backend maximum (clamped to at least one) ...
    Ensures(Result() >= 1)
    Ensures(Result() <= clamped_max(raw_backend_limit))
    # ... and an explicit request additionally caps the result at that request,
    # the result being exactly the smaller of the two bounds.
    Ensures(Implies(requested > 0, Result() <= requested))
    Ensures(Implies(requested > 0,
                    Result() == (requested if requested <= clamped_max(raw_backend_limit)
                                 else clamped_max(raw_backend_limit))))
    # With no explicit request the result is exactly the backend maximum.
    Ensures(Implies(requested == 0, Result() == clamped_max(raw_backend_limit)))
    # post-conditions-end
    # impl-start
    max_batch_size = clamped_max(raw_backend_limit)
    if requested > 0:
        if requested < max_batch_size:
            result = requested
        else:
            result = max_batch_size
    else:
        result = max_batch_size
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ALL WORK IN  Attacks built by gen.py, which splices ONLY the impl-region body of the frozen model.py; `adversary same-spec` returned exit 0 (SAME) for all 12 + the positive control, so axioms/@Pure/Requires/Ensures are byte-identical everywhere.

python -m swebench_unified.adversary weakness nagini django__django-11951 <path>
### RESULTS (exit 2 = spec REJECTED the impl = good; exit 0 = CANDIDATE):
atk_1  PREPATCH BUG re-encoded (explicit request used as-is). exit=2 REJECTED. Its impl region is byte-IDENTICAL to model_prepatch.py's (diff shown empty) => prepatch_reproduced. atk_2  G-MUT recorded survivor, line 86 '<'->'<='. exit=0 CANDIDATE -> patch materialized -> RESOLVED (see below). atk_3  BOUNDARY off-by-one: cap at max_batch_size+1. exit=2 REJECTED. atk_4  PARTIAL DOMAIN: gold min() only when raw_backend_limit<100, else prepatch bug (the F2P's own sqlite max is 999//3=333, inside the broken range). exit=2 REJECTED. atk_5  CONTROL-FLOW EFFECT / DIVERGENCE: infinite `while requested > 0` with Invariant on exactly the buggy path. exit=2 REJECTED -- method-level MustTerminate(2) does the work, so the postconditions cannot go vacuous on a diverging path. atk_6  EXCEPTIONAL EXIT: raise ValueError on the buggy path (no Exsures in the spec). exit=2 REJECTED. atk_7  UNGROUNDED ORACLE ECHO: hardcodes the F2P's raw_backend_limit == 333 and is otherwise the prepatch bug. exit=2 REJECTED. atk_8  AUTO-BRANCH CORRUPTION: gold explicit arm, but requested==0 returns 1 instead of the backend max. exit=2 REJECTED -- both arms of the truthiness split are pinned. atk_9  VACUOUS GUARDED SELF-CALL: gold hidden behind the infeasible guard raw_backend_limit<0, bug on the live path. exit=2 REJECTED. atk_10 SEMANTICS-PRESERVING RESTRUCTURE (declared control): compares against raw_backend_limit, else-arm uses the clamp. exit=0 CANDIDATE -> patch materialized -> RESOLVED. atk_11 DROPPED CLAMP: uses the raw backend value as the cap, so raw==0 yields effective 0 (range(0,n,0) is a repo ValueError).

Targets the max(.,1) half no other attack hits. exit=2 REJECTED (violates Result()>=1). atk_12 IGNORES THE CALLER (mirror over-correction): always returns the backend max, discarding a SMALLER explicit request. exit=2 REJECTED (violates Implies(requested>0, Result()<=requested)).

POSITIVE CONTROL: `adversary verify nagini django__django-11951 positive_control.py` (byte-identical copy of model.py, md5 4f2ccdcc81edc99d1e64a3d088140067) exit=0 VERIFIED.
NON-VACUITY CONTROL (ctl_vacuity.py, Assert(False) in the impl): `bash scripts/nagini_verify.sh` => 'Verification failed... Assertion False might not hold'. The body is genuinely reachable and checked, so every exit-2 above is a real rejection, not an unreachable/vacuous pass.

MANDATORY RESOLVE RUNS (both CANDIDATEs, faithful patches by mkpatch.py transliterating each attack's impl op-for-op via refinement.md's correspondence clamped_max<->max(bulk_batch_size,1), requested<->batch_size truthiness, generated with `git diff` against base_commit 3120490912 in a local clone):
  python resolve.py atk_2  -> swebench_unified.harness.run_resolve -> resolved=true, completed=true, attempts=2, flaky=true ('resolved on attempt 2/3'), F2P success=[test_explicit_batch_size_respects_max_batch_size], P2P 21/21 success, PASS_TO_FAIL empty. The first attempt was an INCOMPLETE measurement under concurrent load on the build host (no 'did not resolve' in the log), which the harness retry policy correctly re-measured rather than recording as a verdict.
  python resolve.py atk_10 -> resolved=true, completed=true, attempts=1, flaky=false, F2P success, P2P 21/21 success.
Both resolve JSONs saved (resolve_atk_2.json, resolve_atk_10.json). So neither CANDIDATE breaks the spec; the two that verified are precisely the two that are behaviourally gold.

WHY THE SPEC IS TIGHT: the postconditions form a TOTAL FUNCTIONAL specification -- Implies(requested>0, Result()==(requested if requested<=clamped_max else clamped_max)) and Implies(requested==0, Result()==clamped_max) pin the exact value on every point of the declared domain (requested>=0, raw_backend_limit>=0), with Result()>=1 and Result()<=clamped_max as redundant reinforcement. There is no room for a value-wrong impl; the only same-spec impls that can verify are min-equivalent restatements (atk_2, atk_10), and both resolve. MustTerminate(2) closes the divergence lane (atk_5) and the absence of an Exsures closes the exceptional lane (atk_6). Consequently the G-MUT survivor '<'->'<=' is a FALSE survivor -- an equivalent mutant, not a spec hole.

A-LEG AUDIT (refinement.md + mapping.md + meta.json). meta axioms==[] -- there is NO consumed @ContractOnly axiom, so there is no assumption surface whose Ensures the proof discharges. The single deep_model_reference is kind 'A-reference': raw_backend_limit as an input integer standing for the UNCHANGED callee ops.bulk_batch_size(fields, objs), plus the max(.,1) clamp modeled deeply as @Pure clamped_max. Leg tags: row1 R, row2 A-reference, row3 R, row4 I, row5 I, row6 R -- every leg is R / A-reference / I, NO kind-3, matching the doc's requirement.

A-reference correspondence CONFIRMED against the real tree at base_commit: I enumerated ALL three bulk_batch_size definitions (git grep 'def bulk_batch_size' => base/operations.py:68 `return len(objs)`; sqlite3/operations.py:27 `500 | max_query_params//len(fields) | len(objs)` with max_query_params=999; oracle/operations.py:624 `max_query_params//len(fields) | len(objs)` with max_query_params=2**16-1). Every branch returns a non-negative int, which is exactly and only the property the model relies on -- the model assumes nothing stronger (not positivity: the clamp max(.,1) is what lifts it, and atk_11 confirms the spec enforces that clamp). Calling it an A-reference rather than a consumed axiom is correct: the value enters solely as an integer parameter.

I re-ran axiom_check.py: exit 0, 'non-negative on 40012 obs; deep model == gold patch min/max arithmetic on 15 boundary + 200000 fuzz pairs'. The 0<->None carrier encoding is sound: bulk_create asserts `batch_size is None or batch_size > 0` (query.py:458), so `if batch_size` is falsy iff None, exactly the requested==0 / requested>0 split. 0 is unreachable at runtime, so encoding it as the auto case cannot misclassify a real input. Modeling-boundary note (not a defect): the model abstracts an expression, not the method, so the NUMBER of bulk_batch_size calls is outside it -- atk_10's faithful patch calls it once and binds the raw value, which is what the patch's own restructuring does too, and it resolved. The callee is a pure formula over len(objs)/len(fields)/max_query_params with no side effects, so call-count is unobservable and the elision is sound.

All 12 attacks + both resolves reached genuine verdicts -- no timeouts, no crashes, nothing inconclusive.

VERDICT: SOUND (advisory). 12 attacks run (>=5 required), all distinct failure modes incl. prepatch bug, G-MUT survivor, boundary, partial-domain, divergence, exception, oracle-echo, vacuous guard, dropped clamp, ignore-caller; 10 rejected; the 2 that verified had their faithful patches EXECUTED through the official harness and BOTH RESOLVED. verify=>correct not falsified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE DISCIPLINE: compared the model against the base_commit worktree WITH patch.diff APPLIED (verified `git apply --check` clean; the hunk at query.py:1212-1213 is the min/max form). Base commit 312049091 was used only for the untouched callee ops.bulk_batch_size, which is what the A-reference models. I did NOT judge the patch delta itself as a divergence.

SPEC REGION IDENTITY: recomputed markers.region_hashes(model.py, nagini) myself. It matches the fresh G-HYGIENE record byte-for-byte on all six regions (spec_view c6e5a2e9..., pre-conditions 590a5cd3...). `adversary same-spec` returns "SAME" (exit 0) on the bundle's own model.py, so I was reviewing the shipped spec. NOTE (bookkeeping only, not a defect in the spec): meta.json's stale TOP-LEVEL region_hashes copy disagrees with both the live file and its own G-HYGIENE gate entry on pre-conditions (7c31655... vs 590a5cd3...) and spec_view (74fa837... vs c6e5a2e9...). The gate record is the current one; the top-level block was not restamped after the 2026-08-14 model.py edit. Worth a restamp, but it does not affect faithfulness.

WHAT THE SPEC CLAIMS: the postconditions fully pin Result on the whole declared domain (no underdetermination to exploit for an over-claim): Result>=1; Result<=clamped_max(raw); requested>0 -> Result == min(requested, clamped_max(raw)); requested==0 -> Result == clamped_max(raw). So any real-behavior mismatch inside the domain would be a hard divergence. I looked for one three independent ways.

### MY OWN DIFFERENTIALS (independent of the bundle's conformance_check, which I did not reuse as evidence):
(1) range()-step spy — monkeypatched `range` in django.db.models.query to capture the REAL local `batch_size` the patched method binds, rather than inferring it from slice lengths. This reads the modeled value directly. Cross-checked against slice count == ceil(n/size) and first-slice length. 4,021 cases (boundaries incl. (0,0),(1,0),(2,0) clamp cases, (1001,1000), (2**31,3), (2**63,1), (10**18,17), (10**6,10**6)) + biased fuzz: 0 disagreements.

(2) EXHAUSTIVE grid — every (requested, raw) in [0,90]x[0,90], each run at 5 different object-list lengths (0, 1, m, m+1, 2m+1) to make sure the observation is not an artifact of a convenient list size: 41,445 observations, 0 disagreements. Also fed batch_size=0 DIRECTLY to the private _batched_insert (bypassing bulk_create's assert) to test the requested==0 <-> falsy mapping at its riskiest point: real returns clamped_max, model returns clamped_max. Agreement.

(3) END-TO-END through the PUBLIC API — real sqlite table, User.objects.bulk_create(13 objs, batch_size=...) under CaptureQueriesContext, counting actual INSERT statements for raw in {1,2,3,7,11} x requested in {None,1,2,raw-1,raw,raw+1,raw*10,10**6}: INSERT count == ceil(13/model(requested,raw)) and all 13 rows landed, in all 40 cases. This is the same observable the F2P test asserts.

### ABSTRACTION-BOUNDARY AUDIT (where a too-strong spec usually hides):
- requested==0 <-> batch_size=None: bulk_create asserts `batch_size is None or batch_size > 0` (query.py:458), which I confirmed at base_commit. I empirically verified the assert actually fires for -1, -5, and 0, so the ONLY falsy value reaching the hunk from the public path is None. The truthiness split `if batch_size` therefore coincides exactly with the model's `requested > 0` test. The mapping is not a convenient fiction.
- Requires(raw_backend_limit >= 0): enumerated all three real bulk_batch_size overrides at base_commit over their full argument domains (base=len(objs); sqlite=500 / 999//len(fields) / len(objs); oracle=(2**16-1)//len(fields) / len(objs)) — every return is a non-negative int; 0 non-negativity violations. raw==0 is genuinely REACHABLE (sqlite with >999 fields gives 999//1000==0), so the max(.,1) clamp the spec models is a live path, not dead weight.
- DOMAIN NARROWING is all in the SAFE direction: inputs the raw private method tolerates but the spec excludes (batch_size=-1 -> real returns -1; raw=-1 -> real returns 1) are ruled out by Requires, so the spec is SILENT there, not WRONG. Silence is weakness, not unfaithfulness — and both are unreachable from the public entry point anyway (the assert / non-negative backends block them). float/str batch_size TypeErrors likewise sit outside the int carrier.
- Unmodeled surroundings (NotSupportedError guard, ops lookup, slicing loop, _insert calls, inserted_rows) are verbatim-unchanged repo code per mapping.md; I confirmed the patch touches only the two batch-size lines and nothing else in the tree (git diff --stat: 1 file, +2/-1).

SUPPORTING GATE REPRODUCTION (secondary): gold model.py verifies under the pinned verifier (exit 0, 12.8s). model_prepatch.py FAILS on exactly the claimed postcondition — "Assertion (Result() <= clamped_max(raw_backend_limit)) might not hold" at line 73 — so the spec really does discriminate the bug it claims to, and is not vacuous. The bundle's own axiom_check.py (exit 0) and conformance_check.py (exit 0, 100,024 inputs) reproduce.

CONCLUSION: the spec is an exact, deeply-modeled encoding of the patched integer min/max decision, neither too strong nor drifted. FAITHFUL.

Counterexample / evidence:

```
None. No faithfulness counterexample exists; the spec does not over-claim.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** MEASURED, not inherited. No relaxation in this bundle: meta.json has no `relaxed_leakage` key (keys = axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version; `'relaxed_leakage' in meta` -> False) and there is no RELAXED_LEAKAGE.md (bundle dir = axiom_check.py, conformance_check.py, mapping.md, meta.json, model.py, model_prepatch.py, pbt_result.json, properties.py, refinement.md, verdict.md). So this is judged as a plain full-strength leakage review.

WHAT I INSPECTED. Consumer spec view derived myself, not read off the bundle: markers.spec_view(model.py, get_backend('nagini')) -> model.py with the impl region replaced by `...  # implementation elided`. sha256(spec_view) = c6e5a2e97a1f8704adf88e4111624859390c122b4daff6bf56103524b26e7964, matching meta.gates['G-HYGIENE'].data.region_hashes.spec_view, so the view I judged is the view the harness ships. Confirmed via src/swebench_unified/eval/{dataset.py:285,adapter.py:304-319,prompts.py:77-82} that the consumer prompt is built ONLY from task.spec_view (+ modeled_functions labels); refinement.md, mapping.md, verdict.md, meta.json, properties.py and patch.diff -- which do quote the gold hunk line-by-line -- are not in the consumer view, so they cannot leak into it.

PUBLIC BASELINE. problem_statement (data/swe_bench_verified/test.jsonl) titled 'bulk_create batch_size param overrides the compatible batch size calculation' links query.py#L1197, says bulk_update 'properly picks the minimum of two', and proposes VERBATIM: `batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size`. The gold patch is exactly that line plus hoisting `max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)`. The edit is therefore already fully public, hints_text is empty and unused.

LINE-BY-LINE. Every behavioral clause of the spec view is inside that public disclosure: docstring 'the effective size is the smaller of that request and the backend maximum' = the issue's min(); 'if the caller requested nothing, the effective size is the backend maximum' = the issue's `else max_batch_size`; 'never less than one' = the PRE-patch repo line's own `max(..., 1)` (I read base_commit 3120490 query.py:1212 out of the upstream repository: `batch_size = (batch_size or max(ops.bulk_batch_size(fields, objs), 1))`), i.e. not part of the edit at all. Contracts (Result()>=1; Result()<=clamped_max; Implies(requested>0, Result()==min-selection); Implies(requested==0, Result()==clamped_max)) restate the same min/max selection.

Grepped the view for leak vocabulary (bug|fix|patch|revert|previous|before|regress|override|min(|max(|query.py|bulk_create|bulk_update|_batched_insert|ops.|django|commit|issue|line N): only hits are the instance id in the title line and the model's own `clamped_max` identifier -- no repo symbol, file path, line number, commit, test name, or before/after framing. The docstring is explicitly phrased 'stated as desired behaviour, not as an edit'. The 'ceiling of the item count over the effective size' clause is a consequence of the UNCHANGED slicing loop `range(0, len(objs), batch_size)` at the very line the issue links, not a discriminator.

Machine confirmation: swebench_unified.leakage.screen(model.py, nagini, patch.diff, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]); leakage.reviewer_directed -> [] on model.py, properties.py, axiom_check.py, conformance_check.py.

DISCRIMINATOR-IS-IN-CONTRACTS CHECK (ran it anyway, as the de-narration control): stripped the whole module docstring to `"""m."""` and re-ran the pinned verifier -- gold impl still 'Verification successful' (0), model_prepatch.py still fails on exactly `Result() <= clamped_max(raw_backend_limit)` (1). So the prose narration is NOT load-bearing; the discriminator lives in the postconditions, and those postconditions are a restatement of the public issue's own proposed line. Nothing in the view is a leak that the public statement does not already give.

SUPPORTING GATES I RE-RAN MYSELF (not quoted): gold model.py verifies via scripts/nagini_verify.sh in.8s (exit 0); model_prepatch.py fails on the capping postcondition in 12.4s (exit 1) -- G-GOLD/G-DIFF sound, so the spec really does discriminate; `adversary same-spec nagini django__django-11951` on a byte copy -> 'SAME' (exit 0), confirming the spec region is byte-identical and my view is canonical.

OBSERVATIONS FOR THE RECORD (neither is a leak, and neither changed my verdict): (1) verdict.md is a backfilled prior-run record that pre-discloses the earlier panel verdicts including 'Role 4 -- G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)'. It describes the runner's protocol ('the agent's own verdict and notes are advisory context') and does not instruct me how to record, so I do not treat it as a reviewer-directed finding -- but I derived the verdict above from the spec view, the base_commit source and my own verifier runs, and did not adopt its conclusion. (2) The TOP-LEVEL meta.json region_hashes is stale relative to model.py on two entries: pre-conditions 7c31655... and spec_view 74fa837... vs computed 590a5cd... and c6e5a2e...; the per-gate G-HYGIENE copy matches the file exactly. That is a bundle-freshness nit for the hygiene lane, not leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.