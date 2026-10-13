# P2 adversarial audit — sphinx-doc__sphinx-8475

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # 2=unbounded-relocation, 3=other) of the light and full probe forms.
     Requires(0 <= head_kind and head_kind <= 3)
     Requires(0 <= get_kind and get_kind <= 3)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # If the light probe already succeeds, that is the outcome (no full probe).
@@ -81,11 +79,7 @@
     Ensures(0 <= Result() and Result() <= 3)
     # post-conditions-end
     # impl-start
-    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
-    # light probe failed with a retryable kind (is_retryable is false for a
-    # success, kind 0); otherwise the light-probe outcome (a success, or a
-    # non-retryable failure) stands.
-    if is_retryable(head_kind):
+    if head_kind == 1:
         result = get_kind
     else:
         result = head_kind
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # 2=unbounded-relocation, 3=other) of the light and full probe forms.
     Requires(0 <= head_kind and head_kind <= 3)
     Requires(0 <= get_kind and get_kind <= 3)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # If the light probe already succeeds, that is the outcome (no full probe).
@@ -81,11 +79,7 @@
     Ensures(0 <= Result() and Result() <= 3)
     # post-conditions-end
     # impl-start
-    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
-    # light probe failed with a retryable kind (is_retryable is false for a
-    # success, kind 0); otherwise the light-probe outcome (a success, or a
-    # non-retryable failure) stands.
-    if is_retryable(head_kind):
+    if head_kind == 2:
         result = get_kind
     else:
         result = head_kind
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # 2=unbounded-relocation, 3=other) of the light and full probe forms.
     Requires(0 <= head_kind and head_kind <= 3)
     Requires(0 <= get_kind and get_kind <= 3)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # If the light probe already succeeds, that is the outcome (no full probe).
@@ -81,11 +79,7 @@
     Ensures(0 <= Result() and Result() <= 3)
     # post-conditions-end
     # impl-start
-    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
-    # light probe failed with a retryable kind (is_retryable is false for a
-    # success, kind 0); otherwise the light-probe outcome (a success, or a
-    # non-retryable failure) stands.
-    if is_retryable(head_kind):
+    if head_kind != 0:
         result = get_kind
     else:
         result = head_kind
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # 2=unbounded-relocation, 3=other) of the light and full probe forms.
     Requires(0 <= head_kind and head_kind <= 3)
     Requires(0 <= get_kind and get_kind <= 3)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # If the light probe already succeeds, that is the outcome (no full probe).
@@ -81,13 +79,6 @@
     Ensures(0 <= Result() and Result() <= 3)
     # post-conditions-end
     # impl-start
-    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
-    # light probe failed with a retryable kind (is_retryable is false for a
-    # success, kind 0); otherwise the light-probe outcome (a success, or a
-    # non-retryable failure) stands.
-    if is_retryable(head_kind):
-        result = get_kind
-    else:
-        result = head_kind
+    result = get_kind
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # 2=unbounded-relocation, 3=other) of the light and full probe forms.
     Requires(0 <= head_kind and head_kind <= 3)
     Requires(0 <= get_kind and get_kind <= 3)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # If the light probe already succeeds, that is the outcome (no full probe).
@@ -81,12 +79,11 @@
     Ensures(0 <= Result() and Result() <= 3)
     # post-conditions-end
     # impl-start
-    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
-    # light probe failed with a retryable kind (is_retryable is false for a
-    # success, kind 0); otherwise the light-probe outcome (a success, or a
-    # non-retryable failure) stands.
     if is_retryable(head_kind):
-        result = get_kind
+        if head_kind == 2 and get_kind == 3:
+            result = 1
+        else:
+            result = get_kind
     else:
         result = head_kind
     return result
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # 2=unbounded-relocation, 3=other) of the light and full probe forms.
     Requires(0 <= head_kind and head_kind <= 3)
     Requires(0 <= get_kind and get_kind <= 3)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # If the light probe already succeeds, that is the outcome (no full probe).
@@ -81,13 +79,9 @@
     Ensures(0 <= Result() and Result() <= 3)
     # post-conditions-end
     # impl-start
-    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
-    # light probe failed with a retryable kind (is_retryable is false for a
-    # success, kind 0); otherwise the light-probe outcome (a success, or a
-    # non-retryable failure) stands.
-    if is_retryable(head_kind):
+    if not is_retryable(head_kind):
+        result = head_kind
+    else:
         result = get_kind
-    else:
-        result = head_kind
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # 2=unbounded-relocation, 3=other) of the light and full probe forms.
     Requires(0 <= head_kind and head_kind <= 3)
     Requires(0 <= get_kind and get_kind <= 3)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # If the light probe already succeeds, that is the outcome (no full probe).
@@ -81,13 +79,6 @@
     Ensures(0 <= Result() and Result() <= 3)
     # post-conditions-end
     # impl-start
-    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
-    # light probe failed with a retryable kind (is_retryable is false for a
-    # success, kind 0); otherwise the light-probe outcome (a success, or a
-    # non-retryable failure) stands.
-    if is_retryable(head_kind):
-        result = get_kind
-    else:
-        result = head_kind
+    result = 0
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,7 +60,6 @@
     # 2=unbounded-relocation, 3=other) of the light and full probe forms.
     Requires(0 <= head_kind and head_kind <= 3)
     Requires(0 <= get_kind and get_kind <= 3)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # If the light probe already succeeds, that is the outcome (no full probe).
@@ -81,13 +79,6 @@
     Ensures(0 <= Result() and Result() <= 3)
     # post-conditions-end
     # impl-start
-    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
-    # light probe failed with a retryable kind (is_retryable is false for a
-    # success, kind 0); otherwise the light-probe outcome (a success, or a
-    # non-retryable failure) stands.
-    if is_retryable(head_kind):
-        result = get_kind
-    else:
-        result = head_kind
+    result = head_kind
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8475.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A reachability probe for a single network locator first attempts a light
  probe form, then -- if that light probe fails in a way that some servers
  exhibit only for the light form -- falls back to a full probe form. The
  outcome the surrounding reporter observes is an OUTCOME KIND:

    0  the probe succeeded (the reporter records the locator as reachable);
    1  the probe failed with a status-level error;
    2  the probe failed because the light form was bounced through an
       unbounded chain of relocations (a failure mode produced ONLY by the
       light form on certain servers -- the full form does not loop);
    3  the probe failed for any other reason.

  The desired behaviour: the light probe is retried with the full probe
  whenever the light probe fails with EITHER a status-level error (kind 1) OR
  an unbounded-relocation failure (kind 2) -- both are failure modes a server
  may exhibit for the light form yet not for the full form, so the full form is
  the authoritative outcome. Any OTHER light-probe failure (kind 3) is taken as
  authoritative and is NOT retried.

  Consequently, for a locator whose light probe is bounced through an unbounded
  relocation chain (kind 2) but whose full probe succeeds, the observed outcome
  is success (kind 0), NOT the unbounded-relocation failure -- the locator is
  recorded as reachable.

The outcome of each probe form is modelled as an integer OUTCOME KIND in
{0,1,2,3} (an abstraction of the response-or-raised-condition the real probe
produces); the function returns the effective outcome kind handed to the
reporter. No callee is axiomatized: the retried-failure classification is the
operation under specification and is modelled directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def is_retryable(kind: int) -> bool:
    """A light-probe outcome kind is retried with the full probe iff it is a
    status-level error (kind 1) OR an unbounded-relocation failure (kind 2):
    both are failure modes that the light form may show yet the full form may
    not, so the full form's outcome is authoritative. Every other failure
    (kind 3) is taken as authoritative and not retried."""
    return kind == 1 or kind == 2
# pure-end


def probe_outcome(head_kind: int, get_kind: int) -> int:
    # pre-conditions-start
    # head_kind / get_kind are the outcome kinds (0=success, 1=status error,
    # 2=unbounded-relocation, 3=other) of the light and full probe forms.
    Requires(0 <= head_kind and head_kind <= 3)
    Requires(0 <= get_kind and get_kind <= 3)
    # pre-conditions-end
    # post-conditions-start
    # If the light probe already succeeds, that is the outcome (no full probe).
    Ensures(Implies(head_kind == 0, Result() == 0))
    # If the light probe fails with a RETRYABLE kind (status error OR unbounded
    # relocation), the effective outcome is the FULL probe's outcome -- so a
    # locator bounced through an unbounded relocation chain on the light form
    # but reachable on the full form is reported as reachable (Result()==0
    # whenever get_kind==0), not as the failure.
    Ensures(Implies(head_kind != 0 and is_retryable(head_kind), Result() == get_kind))
    # A non-retryable light-probe failure (kind 3) is authoritative: it is the
    # effective outcome and the full probe is never consulted.
    Ensures(Implies(head_kind != 0 and not is_retryable(head_kind), Result() == head_kind))
    # The effective outcome is always one of the two probes' kinds (no
    # invented outcome), hence still in range.
    Ensures(Result() == head_kind or Result() == get_kind)
    Ensures(0 <= Result() and Result() <= 3)
    # post-conditions-end
    # impl-start
    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
    # light probe failed with a retryable kind (is_retryable is false for a
    # success, kind 0); otherwise the light-probe outcome (a success, or a
    # non-retryable failure) stands.
    if is_retryable(head_kind):
        result = get_kind
    else:
        result = head_kind
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sphinx-doc__sphinx-8475/nagini. VERDICT: SOUND.

 All attacks built by copying model.py and editing ONLY the impl region (axioms/pure/Requires/Ensures byte-identical); same-spec exit 0 confirmed for all 8.

SPEC SHAPE: probe_outcome(head_kind,get_kind) over outcome-KIND {0,1,2,3}^2. The four Ensures postconditions PIN Result() UNIQUELY at every one of the 16 domain points (proved exhaustively in /tmp: head==0->0; head in{1,2}(retryable)->get_kind; head==3->3; plus Result in {head,get} and 0<=Result<=3). Because Result is fully determined at all reachable inputs, verify => behaviorally-correct is provable; no verifying impl can diverge from gold behavior.

### ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8475 <path>):
- atk_1.py prepatch bug (retry kind1 only, `if head_kind==1`): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). Reproduces model_prepatch.py; prepatch_reproduced=true.
- atk_2.py boundary (retry kind2 only, `if head_kind==2`): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_3.py control-flow-effect overcatch (`if head_kind!=0`, retries kind3): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_4.py ungrounded (always result=get_kind): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_5.py partial-domain (correct except (head==2,get==3)->1): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_6.py correct-echo via negated branch (`if not is_retryable(head_kind): result=head_kind else: result=get_kind`): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (11.9s, exit 0). This is a behaviorally-IDENTICAL rewrite of the gold model (branch order flipped). Per protocol its faithful refined patch was materialized (= the gold patch verbatim, since is_retryable(head)->get / else head is exactly gold semantics) at atk_6_patch.diff and RUN through the official harness: `run_resolve('sphinx-doc__sphinx-8475', patch)` => RESOLVED=True, completed=True, note=resolved. F2P tests/test_build_linkcheck.py::test_TooManyRedirects_on_HEAD PASSED; all 15 PASS_TO_PASS PASSED; no failures. A RESOLVING echo of the gold is NOT a weakness (per 2026-08-06 policy: same-spec verifying attack fails only if its refined patch does NOT resolve). Spec NOT broken.
- atk_7.py constant (result=0): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_8.py ungrounded echo (always result=head_kind): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).

POSITIVE CONTROL: pos_control.py (model.py verbatim) VERIFIED in 12.7s (adversary verify exit 0).

REFINEMENT.MD AUDIT: legs A1,A2 = R (response/exception -> outcome-kind); A3 = A-reference + R (deep model is_retryable == real `except (HTTPError,TooManyRedirects)` match set); A4 = I + R (unchanged control decisions). No kind-3 (unexpressible-changed-op) legs; axioms region empty (no consumed axiom, no dead axiom). The single A-reference correspondence is machine-validated by axiom_check.py over 15 requests.exceptions classes (disjoint kinds 1/2, TooManyRedirects not subclass of HTTPError, kind2 uncaught pre-patch) + 20000 fuzz pairs -> exit 0; consistent with pbt_result.json axiom_cases holds(rc0). Minor doc nit: refinement.md sec B/C reference an 'A5' not present in the sec-A table (labeling typo for A4) -- no soundness impact. Correspondence to real callees holds.

CONCLUSION: 8 distinct same-spec impls run (7 wrong shapes all rejected + 1 correct-shape echo). The ONLY verifying attack (atk_6) is behaviorally correct and its materialized faithful patch RESOLVES under run_resolve. No verifying-yet-wrong impl exists (spec pins Result uniquely). verify => correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8475.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A reachability probe for a single network locator first attempts a light
  probe form, then -- if that light probe fails in a way that some servers
  exhibit only for the light form -- falls back to a full probe form. The
  outcome the surrounding reporter observes is an OUTCOME KIND:

    0  the probe succeeded (the reporter records the locator as reachable);
    1  the probe failed with a status-level error;
    2  the probe failed because the light form was bounced through an
       unbounded chain of relocations (a failure mode produced ONLY by the
       light form on certain servers -- the full form does not loop);
    3  the probe failed for any other reason.

  The desired behaviour: the light probe is retried with the full probe
  whenever the light probe fails with EITHER a status-level error (kind 1) OR
  an unbounded-relocation failure (kind 2) -- both are failure modes a server
  may exhibit for the light form yet not for the full form, so the full form is
  the authoritative outcome. Any OTHER light-probe failure (kind 3) is taken as
  authoritative and is NOT retried.

  Consequently, for a locator whose light probe is bounced through an unbounded
  relocation chain (kind 2) but whose full probe succeeds, the observed outcome
  is success (kind 0), NOT the unbounded-relocation failure -- the locator is
  recorded as reachable.

The outcome of each probe form is modelled as an integer OUTCOME KIND in
{0,1,2,3} (an abstraction of the response-or-raised-condition the real probe
produces); the function returns the effective outcome kind handed to the
reporter. No callee is axiomatized: the retried-failure classification is the
operation under specification and is modelled directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def is_retryable(kind: int) -> bool:
    """A light-probe outcome kind is retried with the full probe iff it is a
    status-level error (kind 1) OR an unbounded-relocation failure (kind 2):
    both are failure modes that the light form may show yet the full form may
    not, so the full form's outcome is authoritative. Every other failure
    (kind 3) is taken as authoritative and not retried."""
    return kind == 1 or kind == 2
# pure-end


def probe_outcome(head_kind: int, get_kind: int) -> int:
    # pre-conditions-start
    # head_kind / get_kind are the outcome kinds (0=success, 1=status error,
    # 2=unbounded-relocation, 3=other) of the light and full probe forms.
    Requires(0 <= head_kind and head_kind <= 3)
    Requires(0 <= get_kind and get_kind <= 3)
    # pre-conditions-end
    # post-conditions-start
    # If the light probe already succeeds, that is the outcome (no full probe).
    Ensures(Implies(head_kind == 0, Result() == 0))
    # If the light probe fails with a RETRYABLE kind (status error OR unbounded
    # relocation), the effective outcome is the FULL probe's outcome -- so a
    # locator bounced through an unbounded relocation chain on the light form
    # but reachable on the full form is reported as reachable (Result()==0
    # whenever get_kind==0), not as the failure.
    Ensures(Implies(head_kind != 0 and is_retryable(head_kind), Result() == get_kind))
    # A non-retryable light-probe failure (kind 3) is authoritative: it is the
    # effective outcome and the full probe is never consulted.
    Ensures(Implies(head_kind != 0 and not is_retryable(head_kind), Result() == head_kind))
    # The effective outcome is always one of the two probes' kinds (no
    # invented outcome), hence still in range.
    Ensures(Result() == head_kind or Result() == get_kind)
    Ensures(0 <= Result() and Result() <= 3)
    # post-conditions-end
    # impl-start
    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
    # light probe failed with a retryable kind (is_retryable is false for a
    # success, kind 0); otherwise the light-probe outcome (a success, or a
    # non-retryable failure) stands.
    if is_retryable(head_kind):
        result = get_kind
    else:
        result = head_kind
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for sphinx-doc__sphinx-8475/nagini. VERDICT: SOUND.

 All attacks built by copying model.py and editing ONLY the impl region (axioms/pure/Requires/Ensures byte-identical); same-spec exit 0 confirmed for all 8.

SPEC SHAPE: probe_outcome(head_kind,get_kind) over outcome-KIND {0,1,2,3}^2. The four Ensures postconditions PIN Result() UNIQUELY at every one of the 16 domain points (proved exhaustively in /tmp: head==0->0; head in{1,2}(retryable)->get_kind; head==3->3; plus Result in {head,get} and 0<=Result<=3). Because Result is fully determined at all reachable inputs, verify => behaviorally-correct is provable; no verifying impl can diverge from gold behavior.

### ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8475 <path>):
- atk_1.py prepatch bug (retry kind1 only, `if head_kind==1`): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). Reproduces model_prepatch.py; prepatch_reproduced=true.
- atk_2.py boundary (retry kind2 only, `if head_kind==2`): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_3.py control-flow-effect overcatch (`if head_kind!=0`, retries kind3): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_4.py ungrounded (always result=get_kind): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_5.py partial-domain (correct except (head==2,get==3)->1): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_6.py correct-echo via negated branch (`if not is_retryable(head_kind): result=head_kind else: result=get_kind`): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (11.9s, exit 0). This is a behaviorally-IDENTICAL rewrite of the gold model (branch order flipped). Per protocol its faithful refined patch was materialized (= the gold patch verbatim, since is_retryable(head)->get / else head is exactly gold semantics) at atk_6_patch.diff and RUN through the official harness: `run_resolve('sphinx-doc__sphinx-8475', patch)` => RESOLVED=True, completed=True, note=resolved. F2P tests/test_build_linkcheck.py::test_TooManyRedirects_on_HEAD PASSED; all 15 PASS_TO_PASS PASSED; no failures. A RESOLVING echo of the gold is NOT a weakness (per 2026-08-06 policy: same-spec verifying attack fails only if its refined patch does NOT resolve). Spec NOT broken.
- atk_7.py constant (result=0): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).
- atk_8.py ungrounded echo (always result=head_kind): NOT-A-COUNTEREXAMPLE, verification failed (exit 2).

POSITIVE CONTROL: pos_control.py (model.py verbatim) VERIFIED in 12.7s (adversary verify exit 0).

REFINEMENT.MD AUDIT: legs A1,A2 = R (response/exception -> outcome-kind); A3 = A-reference + R (deep model is_retryable == real `except (HTTPError,TooManyRedirects)` match set); A4 = I + R (unchanged control decisions). No kind-3 (unexpressible-changed-op) legs; axioms region empty (no consumed axiom, no dead axiom). The single A-reference correspondence is machine-validated by axiom_check.py over 15 requests.exceptions classes (disjoint kinds 1/2, TooManyRedirects not subclass of HTTPError, kind2 uncaught pre-patch) + 20000 fuzz pairs -> exit 0; consistent with pbt_result.json axiom_cases holds(rc0). Minor doc nit: refinement.md sec B/C reference an 'A5' not present in the sec-A table (labeling typo for A4) -- no soundness impact. Correspondence to real callees holds.

CONCLUSION: 8 distinct same-spec impls run (7 wrong shapes all rejected + 1 correct-shape echo). The ONLY verifying attack (atk_6) is behaviorally correct and its materialized faithful patch RESOLVES under run_resolve. No verifying-yet-wrong impl exists (spec pins Result uniquely). verify => correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for the modeled function probe_outcome(head_kind, get_kind) vs the real inner HEAD->GET fallback block of CheckExternalLinksBuilder.check_thread.check_uri (sphinx/builders/linkcheck.py:168-180 @ base 3ea1ec84), under the outcome-kind abstraction stated in mapping.md (0=success/no raise, 1=HTTPError, 2=TooManyRedirects, 3=other RequestException).

Modeled function is total over its precondition domain {0,1,2,3}^2 (16 inputs). Exhaustively compared each against the REAL post-patch behavior (`except (HTTPError, TooManyRedirects): retry with GET`):
- head_kind==0: except not entered -> HEAD outcome stands -> 0. Model Ensures Result()==0. AGREE (all 4 get_kind).
- head_kind==1 (HTTPError): caught -> retry GET -> outcome==get_kind. Model Result()==get_kind. AGREE.
- head_kind==2 (TooManyRedirects): caught by the widened tuple -> retry GET -> outcome==get_kind. Model Result()==get_kind. AGREE (this is the discriminating post-patch behavior; notably head=2,get=0 -> 0/working).
- head_kind==3 (other RequestException): NOT in tuple -> propagates unchanged -> outcome==head_kind==3. Model Result()==head_kind. AGREE.
All 16 pairs match; no diverging input.

The model is NOT too strong: the extra postconditions (Result()==head_kind or Result()==get_kind; 0<=Result()<=3) are exactly guaranteed by the real block (the effective outcome is always precisely one of the two probes' kinds; no invented value). The modeled slice correctly stops at the inner block's outcome kind and does not over-model the outer 401/503/broken reporter mapping (out of scope, correctly excluded).

Load-bearing abstraction soundness verified against pinned requests 2.31.0: issubclass(TooManyRedirects, HTTPError)=False and issubclass(HTTPError, TooManyRedirects)=False (disjoint => kind 2 is a genuinely separate failure the pre-patch `except HTTPError` did not catch), both are RequestException subclasses. So the kind-1/kind-2 disjointness and the kind-3 exclusion the spec relies on are real, not assumed. axiom_check.py encodes these same obligations (env lacked `requests` module so I re-derived them directly in a python3 with requests present).

Spec region well-formed and the full model.py verifies under the pinned Nagini (Verification successful, 10.3s). No spec/behavior divergence found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + pure region + probe_outcome pre/post + elided impl) leaks nothing about the gold edit beyond the public problem_statement.

Gold edit: sphinx/builders/linkcheck.py — widen the retried-failure `except HTTPError:` to `except (HTTPError, TooManyRedirects):` (plus matching import) inside check_uri's HEAD→GET fallback.

Public problem_statement ALREADY reveals the whole fix in the clear: HEAD requests, GET fallback, `TooManyRedirects`, infinite redirect loops, and 'extends the except clause to retry with a GET request for such scenarios'. So the behavior the spec encodes is public by construction.

Spec view is fully abstracted and carries NO gold-edit localizer beyond that public content:
- Never names HEAD/GET/requests/raise_for_status/except/import; uses 'light probe form' / 'full probe form' and integer OUTCOME KINDs 0..3.
- kind 2 = 'unbounded chain of relocations' is a paraphrase of the public 'Too Many Redirects / infinite redirect loops'; kind 1 = 'status-level error' corresponds to the PRE-existing HTTPError retry (not the edit).
- The discriminating behavior 'retry on kind 1 OR kind 2' is exactly the public problem_statement's stated fix; a spec must state target behavior, and here that behavior is already solver-visible.
- No patched file path (linkcheck.py), no patched module path, no diff markers, no reproduced gold-patch line, no exception class names.

Mechanical G-LEAK screen: PASS (rep.passed=True, hard_failures=[]). Only patch-changed distinctive symbol is `check_uri`, which does NOT appear anywhere in the spec view. No narration tokens (bug/fix/patched/etc.). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
