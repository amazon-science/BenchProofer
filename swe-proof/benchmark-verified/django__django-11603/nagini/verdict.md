# P2 adversarial audit — django__django-11603

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_8.py` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -69,7 +69,7 @@
     # never diverges. The strictly smaller measure (1 < 2) lets a family
     # constructor holding MustTerminate(2) invoke the prologue without leaking
     # its own obligation.
-    Requires(MustTerminate(2))
+    Requires(MustTerminate(1))
     # pre-conditions-end
     # post-conditions-start
     # Normal return is reachable ONLY when the request is honourable: either no
@@ -99,7 +99,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The arithmetic-mean family MUST honour a deduplicate request: construction
@@ -109,7 +109,7 @@
     Ensures(Result() == dedup)
     # post-conditions-end
     # impl-start
-    return construct_dedup(True, dedup)
+    return construct_dedup(False, dedup)
     # impl-end
 
 
@@ -122,7 +122,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The running-total family MUST honour a deduplicate request: construction
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,7 +69,7 @@
     # never diverges. The strictly smaller measure (1 < 2) lets a family
     # constructor holding MustTerminate(2) invoke the prologue without leaking
     # its own obligation.
-    Requires(MustTerminate(2))
+    Requires(MustTerminate(1))
     # pre-conditions-end
     # post-conditions-start
     # Normal return is reachable ONLY when the request is honourable: either no
@@ -99,7 +99,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The arithmetic-mean family MUST honour a deduplicate request: construction
@@ -109,7 +109,7 @@
     Ensures(Result() == dedup)
     # post-conditions-end
     # impl-start
-    return construct_dedup(True, dedup)
+    return dedup
     # impl-end
 
 
@@ -122,7 +122,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The running-total family MUST honour a deduplicate request: construction
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,7 +69,7 @@
     # never diverges. The strictly smaller measure (1 < 2) lets a family
     # constructor holding MustTerminate(2) invoke the prologue without leaking
     # its own obligation.
-    Requires(MustTerminate(2))
+    Requires(MustTerminate(1))
     # pre-conditions-end
     # post-conditions-start
     # Normal return is reachable ONLY when the request is honourable: either no
@@ -99,7 +99,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The arithmetic-mean family MUST honour a deduplicate request: construction
@@ -109,7 +109,9 @@
     Ensures(Result() == dedup)
     # post-conditions-end
     # impl-start
-    return construct_dedup(True, dedup)
+    if dedup:
+        return construct_dedup(True, True)
+    return construct_dedup(True, False)
     # impl-end
 
 
@@ -122,7 +124,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The running-total family MUST honour a deduplicate request: construction
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,7 +69,7 @@
     # never diverges. The strictly smaller measure (1 < 2) lets a family
     # constructor holding MustTerminate(2) invoke the prologue without leaking
     # its own obligation.
-    Requires(MustTerminate(2))
+    Requires(MustTerminate(1))
     # pre-conditions-end
     # post-conditions-start
     # Normal return is reachable ONLY when the request is honourable: either no
@@ -83,10 +83,9 @@
     Exsures(CapabilityError, dedup is True and allow_dedup is False)
     # post-conditions-end
     # impl-start
-    if dedup and not allow_dedup:
+    if not allow_dedup and dedup:
         raise CapabilityError()
-    stored = dedup
-    return stored
+    return dedup
     # impl-end
 
 
@@ -99,7 +98,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The arithmetic-mean family MUST honour a deduplicate request: construction
@@ -122,7 +121,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The running-total family MUST honour a deduplicate request: construction
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -69,7 +69,7 @@
     # never diverges. The strictly smaller measure (1 < 2) lets a family
     # constructor holding MustTerminate(2) invoke the prologue without leaking
     # its own obligation.
-    Requires(MustTerminate(2))
+    Requires(MustTerminate(1))
     # pre-conditions-end
     # post-conditions-start
     # Normal return is reachable ONLY when the request is honourable: either no
@@ -99,7 +99,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The arithmetic-mean family MUST honour a deduplicate request: construction
@@ -122,7 +122,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The running-total family MUST honour a deduplicate request: construction
@@ -132,5 +132,5 @@
     Ensures(Result() == dedup)
     # post-conditions-end
     # impl-start
-    return construct_dedup(True, dedup)
+    return construct_dedup(False, dedup)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -69,7 +69,7 @@
     # never diverges. The strictly smaller measure (1 < 2) lets a family
     # constructor holding MustTerminate(2) invoke the prologue without leaking
     # its own obligation.
-    Requires(MustTerminate(2))
+    Requires(MustTerminate(1))
     # pre-conditions-end
     # post-conditions-start
     # Normal return is reachable ONLY when the request is honourable: either no
@@ -99,7 +99,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The arithmetic-mean family MUST honour a deduplicate request: construction
@@ -109,6 +109,9 @@
     Ensures(Result() == dedup)
     # post-conditions-end
     # impl-start
+    i = 0
+    while i >= 0:
+        i = i + 1
     return construct_dedup(True, dedup)
     # impl-end
 
@@ -122,7 +125,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The running-total family MUST honour a deduplicate request: construction
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,7 +69,7 @@
     # never diverges. The strictly smaller measure (1 < 2) lets a family
     # constructor holding MustTerminate(2) invoke the prologue without leaking
     # its own obligation.
-    Requires(MustTerminate(2))
+    Requires(MustTerminate(1))
     # pre-conditions-end
     # post-conditions-start
     # Normal return is reachable ONLY when the request is honourable: either no
@@ -99,7 +99,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The arithmetic-mean family MUST honour a deduplicate request: construction
@@ -109,7 +109,7 @@
     Ensures(Result() == dedup)
     # post-conditions-end
     # impl-start
-    return construct_dedup(True, dedup)
+    return construct_dedup(dedup, dedup)
     # impl-end
 
 
@@ -122,7 +122,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The running-total family MUST honour a deduplicate request: construction
@@ -132,5 +132,5 @@
     Ensures(Result() == dedup)
     # post-conditions-end
     # impl-start
-    return construct_dedup(True, dedup)
+    return construct_dedup(dedup, dedup)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,7 +69,7 @@
     # never diverges. The strictly smaller measure (1 < 2) lets a family
     # constructor holding MustTerminate(2) invoke the prologue without leaking
     # its own obligation.
-    Requires(MustTerminate(2))
+    Requires(MustTerminate(1))
     # pre-conditions-end
     # post-conditions-start
     # Normal return is reachable ONLY when the request is honourable: either no
@@ -99,7 +99,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The arithmetic-mean family MUST honour a deduplicate request: construction
@@ -109,7 +109,8 @@
     Ensures(Result() == dedup)
     # post-conditions-end
     # impl-start
-    return construct_dedup(True, dedup)
+    result = construct_dedup(True, dedup)
+    return result
     # impl-end
 
 
@@ -122,7 +123,7 @@
     # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
     # the constructed object to its caller; the real constructor always
     # returns. This obligation rejects any such implementation.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The running-total family MUST honour a deduplicate request: construction
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11603.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A family of summary-computation constructors share a common construction
  prologue. The prologue takes a *deduplicate* request (a boolean asking that
  repeated input values be collapsed before the summary is computed) together
  with a per-family *capability* flag stating whether that family is permitted
  to honour deduplication. The prologue's decision is:

    * if deduplication is requested by a family that is NOT permitted to honour
      it, the constructor refuses — it signals the caller with a capability
      error instead of building the object; otherwise
    * the constructor proceeds and records the deduplicate request as the
      object's state, so that a later request reads back exactly what was asked.

  The behaviour pinned here is which families are permitted to honour the
  deduplicate request. Two specific families — the arithmetic-mean family and
  the running-total family — MUST be permitted to honour it: constructing
  either with deduplication requested must succeed and record the request,
  never refuse. (A third family, the plain tally, was already permitted.)
  Families with the capability disabled must still refuse a deduplicate
  request.

The deduplicate request and the capability flag are plain booleans; no string
or heap modelling is needed. The capability error is a user-defined exception
class (a builtin exception in an `Exsures` crashes the Nagini translator). The
shared prologue is modelled deeply as its own contracted function; each family
constructor is modelled as a separate function that invokes the prologue with
its family's capability flag, so the per-family capability is the discriminating
datum.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CapabilityError(Exception):
    """Signals that the requested deduplication is not permitted for this
    family. Stands in for the `TypeError` the desired behaviour raises (a
    builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
# (no axiomatized callees: the shared prologue is modelled deeply as
# construct_dedup below; the only operations the family constructors perform
# that this specification observes are that prologue's decision and the state
# it records. Everything else the real constructor delegates to is unchanged,
# independent of the capability/deduplicate decision, and unobserved here.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the decision is a boolean predicate
# stated inline in the contracts.)
# pure-end


def construct_dedup(allow_dedup: bool, dedup: bool) -> bool:
    # pre-conditions-start
    # Both inputs are plain booleans (no heap permission needed). `allow_dedup`
    # is the per-family capability; `dedup` is the caller's deduplicate request.
    # TERMINATION: the prologue is a bounded, loop-free decision — every call
    # either returns the recorded request or raises the capability error; it
    # never diverges. The strictly smaller measure (1 < 2) lets a family
    # constructor holding MustTerminate(2) invoke the prologue without leaking
    # its own obligation.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal return is reachable ONLY when the request is honourable: either no
    # deduplication was requested, or the family is permitted to honour it.
    Ensures(dedup is False or allow_dedup is True)
    # When the constructor proceeds, the recorded state is EXACTLY the request
    # that was made (read-back fidelity).
    Ensures(Result() == dedup)
    # The capability error is raised on EXACTLY the refused case: a deduplicate
    # request from a family that is not permitted to honour it.
    Exsures(CapabilityError, dedup is True and allow_dedup is False)
    # post-conditions-end
    # impl-start
    if dedup and not allow_dedup:
        raise CapabilityError()
    stored = dedup
    return stored
    # impl-end


def build_mean(dedup: bool) -> bool:
    # pre-conditions-start
    # `dedup` is the caller's deduplicate request for the arithmetic-mean family.
    # TERMINATION: constructing the family object is bounded straight-line work
    # and MUST actually complete (total correctness). Under partial-correctness
    # semantics a diverging body (e.g. an endless loop before the return)
    # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
    # the constructed object to its caller; the real constructor always
    # returns. This obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The arithmetic-mean family MUST honour a deduplicate request: construction
    # always succeeds (no Exsures clause => never raises) and records the
    # request exactly, for EVERY value of `dedup` including a request to
    # deduplicate.
    Ensures(Result() == dedup)
    # post-conditions-end
    # impl-start
    return construct_dedup(True, dedup)
    # impl-end


def build_total(dedup: bool) -> bool:
    # pre-conditions-start
    # `dedup` is the caller's deduplicate request for the running-total family.
    # TERMINATION: constructing the family object is bounded straight-line work
    # and MUST actually complete (total correctness). Under partial-correctness
    # semantics a diverging body (e.g. an endless loop before the return)
    # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
    # the constructed object to its caller; the real constructor always
    # returns. This obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The running-total family MUST honour a deduplicate request: construction
    # always succeeds (no Exsures clause => never raises) and records the
    # request exactly, for EVERY value of `dedup` including a request to
    # deduplicate.
    Ensures(Result() == dedup)
    # post-conditions-end
    # impl-start
    return construct_dedup(True, dedup)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND.

### Attack outcomes
- atk_1 (prepatch mean bug: build_mean->construct_dedup(False,dedup)): weakness EXIT=2, does NOT verify (dedup=True hits refuse branch -> raises CapabilityError, violating Ensures(Result()==dedup) with no Exsures). Reproduces model_prepatch.py.
- atk_5 (prepatch total bug: build_total->construct_dedup(False,dedup)): weakness EXIT=2, does NOT verify. Reproduces model_prepatch_2.py.
- atk_6 (control-flow/divergence: `while i>=0: i+=1` before return in build_mean): weakness EXIT=2, does NOT verify — MustTerminate(2) SOUNDLY rejects the partial-correctness vacuity impl (refinement.md leg A4 holds). This is the recorded G-PANEL-1 witness class; the obligation closes it.
- atk_2 (build_mean: `return dedup`, bypass prologue): CANDIDATE (same-spec + verifies).
- atk_3 (build_mean: branch then construct_dedup(True,·)): CANDIDATE.
- atk_4 (construct_dedup rewrite: reordered guard `if not allow_dedup and dedup: raise; return dedup`): CANDIDATE.
- atk_7 (build_mean & build_total: construct_dedup(dedup,dedup)): CANDIDATE.
- atk_8 (build_mean: local var then return): CANDIDATE.

MATERIALIZED FAITHFUL PATCHES + OFFICIAL HARNESS (run_resolve, SBU_BENCHMARK=swe_bench_verified):
- atk_2/atk_3/atk_7/atk_8 all refine to the exact gold patch (allow_distinct=True on Avg and Sum): faithful_gold.diff -> run_resolve RESOLVED=True COMPLETED=True flaky=False (`sbu-eq-gold-qriw1niu`).
- atk_4 refines to a behavior-preserving __init__ guard reorder + the gold class-attr additions (the prologue maps to the UNCHANGED Aggregate.__init__; the reorder `not self.allow_distinct and distinct` is logically identical to `distinct and not self.allow_distinct`): faithful_atk4.diff -> run_resolve RESOLVED=True COMPLETED=True flaky=False (`sbu-eq-atk4-qriw1niu`). Built by editing reset to base_commit f618e033ac.
Every verifying candidate's faithful patch RESOLVES => verify⇒correct holds; no counterexample.

POSITIVE CONTROL: positive_control.py (== bundle model.py) -> nagini_verify.sh 'Verification successful' (10.10s), exit 0.

REFINEMENT.MD A-LEG AUDIT: meta.json axioms=[] and deep_model_references=[] — there are NO A-consumed and NO A-reference callee legs; the axioms/pure regions are empty comments. The only deep-model correspondence is construct_dedup <-> the UNCHANGED real Aggregate.__init__ deduplication prologue (legs A1-A3, tagged R/I). This correspondence is validated against EXECUTED real Django by axiom_check.py/G-AX: exit 0 against the base tree — model refuse-predicate (distinct and not allow_distinct) + read-back fidelity match real __init__ over all 7 families × {False,True}; base tree: only Count accepts distinct, Avg/Sum refuse (the capability the gold adds). construct_dedup pins the FULL boolean truth table (FF->ret F, FT->raise, TF->ret F, TT->ret T), so the deep model is exact, not an over-approximation. build_mean/build_total legs B1/B2 (allow_dedup=True <- Avg/Sum allow_distinct=True) are the genuine gold change, modeled deeply not axiomatized. No kind-3 (unexpressible-changed-op) leg exists; every leg is R or I. Correspondence holds.

CAVEAT: meta.json records a stale G-PANEL-1=fail (WEAK, echo at atk_6.py of a prior scratch dir) alongside G-EQ=pass — per the audit policy the echo-shaped G-PANEL-1 is a resolving echo of gold (NOT a real weakness) and should convert on audit re-run; my independent battery reproduces exactly this: all verifying candidates are resolving echoes/equivalents of the gold, none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_8.py` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11603.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A family of summary-computation constructors share a common construction
  prologue. The prologue takes a *deduplicate* request (a boolean asking that
  repeated input values be collapsed before the summary is computed) together
  with a per-family *capability* flag stating whether that family is permitted
  to honour deduplication. The prologue's decision is:

    * if deduplication is requested by a family that is NOT permitted to honour
      it, the constructor refuses — it signals the caller with a capability
      error instead of building the object; otherwise
    * the constructor proceeds and records the deduplicate request as the
      object's state, so that a later request reads back exactly what was asked.

  The behaviour pinned here is which families are permitted to honour the
  deduplicate request. Two specific families — the arithmetic-mean family and
  the running-total family — MUST be permitted to honour it: constructing
  either with deduplication requested must succeed and record the request,
  never refuse. (A third family, the plain tally, was already permitted.)
  Families with the capability disabled must still refuse a deduplicate
  request.

The deduplicate request and the capability flag are plain booleans; no string
or heap modelling is needed. The capability error is a user-defined exception
class (a builtin exception in an `Exsures` crashes the Nagini translator). The
shared prologue is modelled deeply as its own contracted function; each family
constructor is modelled as a separate function that invokes the prologue with
its family's capability flag, so the per-family capability is the discriminating
datum.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CapabilityError(Exception):
    """Signals that the requested deduplication is not permitted for this
    family. Stands in for the `TypeError` the desired behaviour raises (a
    builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
# (no axiomatized callees: the shared prologue is modelled deeply as
# construct_dedup below; the only operations the family constructors perform
# that this specification observes are that prologue's decision and the state
# it records. Everything else the real constructor delegates to is unchanged,
# independent of the capability/deduplicate decision, and unobserved here.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the decision is a boolean predicate
# stated inline in the contracts.)
# pure-end


def construct_dedup(allow_dedup: bool, dedup: bool) -> bool:
    # pre-conditions-start
    # Both inputs are plain booleans (no heap permission needed). `allow_dedup`
    # is the per-family capability; `dedup` is the caller's deduplicate request.
    # TERMINATION: the prologue is a bounded, loop-free decision — every call
    # either returns the recorded request or raises the capability error; it
    # never diverges. The strictly smaller measure (1 < 2) lets a family
    # constructor holding MustTerminate(2) invoke the prologue without leaking
    # its own obligation.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal return is reachable ONLY when the request is honourable: either no
    # deduplication was requested, or the family is permitted to honour it.
    Ensures(dedup is False or allow_dedup is True)
    # When the constructor proceeds, the recorded state is EXACTLY the request
    # that was made (read-back fidelity).
    Ensures(Result() == dedup)
    # The capability error is raised on EXACTLY the refused case: a deduplicate
    # request from a family that is not permitted to honour it.
    Exsures(CapabilityError, dedup is True and allow_dedup is False)
    # post-conditions-end
    # impl-start
    if dedup and not allow_dedup:
        raise CapabilityError()
    stored = dedup
    return stored
    # impl-end


def build_mean(dedup: bool) -> bool:
    # pre-conditions-start
    # `dedup` is the caller's deduplicate request for the arithmetic-mean family.
    # TERMINATION: constructing the family object is bounded straight-line work
    # and MUST actually complete (total correctness). Under partial-correctness
    # semantics a diverging body (e.g. an endless loop before the return)
    # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
    # the constructed object to its caller; the real constructor always
    # returns. This obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The arithmetic-mean family MUST honour a deduplicate request: construction
    # always succeeds (no Exsures clause => never raises) and records the
    # request exactly, for EVERY value of `dedup` including a request to
    # deduplicate.
    Ensures(Result() == dedup)
    # post-conditions-end
    # impl-start
    return construct_dedup(True, dedup)
    # impl-end


def build_total(dedup: bool) -> bool:
    # pre-conditions-start
    # `dedup` is the caller's deduplicate request for the running-total family.
    # TERMINATION: constructing the family object is bounded straight-line work
    # and MUST actually complete (total correctness). Under partial-correctness
    # semantics a diverging body (e.g. an endless loop before the return)
    # satisfies Ensures(Result() == dedup) only vacuously yet never delivers
    # the constructed object to its caller; the real constructor always
    # returns. This obligation rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The running-total family MUST honour a deduplicate request: construction
    # always succeeds (no Exsures clause => never raises) and records the
    # request exactly, for EVERY value of `dedup` including a request to
    # deduplicate.
    Ensures(Result() == dedup)
    # post-conditions-end
    # impl-start
    return construct_dedup(True, dedup)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND.

### Attack outcomes
- atk_1 (prepatch mean bug: build_mean->construct_dedup(False,dedup)): weakness EXIT=2, does NOT verify (dedup=True hits refuse branch -> raises CapabilityError, violating Ensures(Result()==dedup) with no Exsures). Reproduces model_prepatch.py.
- atk_5 (prepatch total bug: build_total->construct_dedup(False,dedup)): weakness EXIT=2, does NOT verify. Reproduces model_prepatch_2.py.
- atk_6 (control-flow/divergence: `while i>=0: i+=1` before return in build_mean): weakness EXIT=2, does NOT verify — MustTerminate(2) SOUNDLY rejects the partial-correctness vacuity impl (refinement.md leg A4 holds). This is the recorded G-PANEL-1 witness class; the obligation closes it.
- atk_2 (build_mean: `return dedup`, bypass prologue): CANDIDATE (same-spec + verifies).
- atk_3 (build_mean: branch then construct_dedup(True,·)): CANDIDATE.
- atk_4 (construct_dedup rewrite: reordered guard `if not allow_dedup and dedup: raise; return dedup`): CANDIDATE.
- atk_7 (build_mean & build_total: construct_dedup(dedup,dedup)): CANDIDATE.
- atk_8 (build_mean: local var then return): CANDIDATE.

MATERIALIZED FAITHFUL PATCHES + OFFICIAL HARNESS (run_resolve, SBU_BENCHMARK=swe_bench_verified):
- atk_2/atk_3/atk_7/atk_8 all refine to the exact gold patch (allow_distinct=True on Avg and Sum): faithful_gold.diff -> run_resolve RESOLVED=True COMPLETED=True flaky=False (`sbu-eq-gold-qriw1niu`).
- atk_4 refines to a behavior-preserving __init__ guard reorder + the gold class-attr additions (the prologue maps to the UNCHANGED Aggregate.__init__; the reorder `not self.allow_distinct and distinct` is logically identical to `distinct and not self.allow_distinct`): faithful_atk4.diff -> run_resolve RESOLVED=True COMPLETED=True flaky=False (`sbu-eq-atk4-qriw1niu`). Built by editing reset to base_commit f618e033ac.
Every verifying candidate's faithful patch RESOLVES => verify⇒correct holds; no counterexample.

POSITIVE CONTROL: positive_control.py (== bundle model.py) -> nagini_verify.sh 'Verification successful' (10.10s), exit 0.

REFINEMENT.MD A-LEG AUDIT: meta.json axioms=[] and deep_model_references=[] — there are NO A-consumed and NO A-reference callee legs; the axioms/pure regions are empty comments. The only deep-model correspondence is construct_dedup <-> the UNCHANGED real Aggregate.__init__ deduplication prologue (legs A1-A3, tagged R/I). This correspondence is validated against EXECUTED real Django by axiom_check.py/G-AX: exit 0 against the base tree — model refuse-predicate (distinct and not allow_distinct) + read-back fidelity match real __init__ over all 7 families × {False,True}; base tree: only Count accepts distinct, Avg/Sum refuse (the capability the gold adds). construct_dedup pins the FULL boolean truth table (FF->ret F, FT->raise, TF->ret F, TT->ret T), so the deep model is exact, not an over-approximation. build_mean/build_total legs B1/B2 (allow_dedup=True <- Avg/Sum allow_distinct=True) are the genuine gold change, modeled deeply not axiomatized. No kind-3 (unexpressible-changed-op) leg exists; every leg is R or I. Correspondence holds.

CAVEAT: meta.json records a stale G-PANEL-1=fail (WEAK, echo at atk_6.py of a prior scratch dir) alongside G-EQ=pass — per the audit policy the echo-shaped G-PANEL-1 is a resolving echo of gold (NOT a real weakness) and should convert on audit re-run; my independent battery reproduces exactly this: all verifying candidates are resolving echoes/equivalents of the gold, none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found between the modeled functions and the real Django callee. Bundle model.py verifies (Nagini, 11.2s). Base worktree at base_commit f618e033 with gold applied (Avg line 102, Sum line 146 both allow_distinct=True). Exhaustively enumerated the FULL modeled input domain (two booleans allow_dedup, dedup) against real django.db.models.aggregates: (1) build_mean/build_total model Avg/Sum with allow_dedup=True — real Avg/Sum accept distinct in {False,True} and record it: MATCH on all inputs incl. the discriminating dedup=True (record fidelity: obj.distinct==requested). (2) construct_dedup prologue matches every real family: Aggregate/Max/Min/StdDev/Variance (allow=False) refuse distinct=True & accept False; Count (allow=True) accepts both — all MATCH. The MustTerminate(1)/(2) obligations only reject diverging impls; the real loop-free straight-line __init__ always terminates, so they exclude no correct real behavior and cannot render the spec too strong. CapabilityError<->TypeError and the dropped construction tail (self.filter=..., super().__init__) are outside the spec's observable projection (raise-vs-not + recorded distinct), which matches. No input on which the modeled function disagrees with the real repo behavior exists. Spec is faithful; not too strong; no drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leakage.screen passes (0 hard failures); no relaxed_leakage flag. Semantic review of spec_view: the spec is fully abstracted — construct_dedup/build_mean/build_total, 'deduplicate request', 'capability flag', 'arithmetic-mean family'/'running-total family'/'plain tally'. It never names Avg, Sum, Count, distinct, allow_distinct, aggregates.py, django.db.models, or TypeError; no diff markers, no patched file/module path, no bug/fix narration (the CapabilityError note is a modeling-constraint explanation, not edit narration). Crucially, the discriminating content it pins (mean+total families must honour dedup, disabled families refuse) is strictly a subset of the PUBLIC problem_statement, which already says 'Add DISTINCT support for Avg and Sum' and 'setting these classes as allowing DISTINCT' — i.e. the gold edit is already public. The spec view is more abstract than the task text and reveals nothing beyond it. The concrete Avg/Sum bindings appear only in mapping.md/refinement.md, which are auditor docs, not the consumer spec view. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
