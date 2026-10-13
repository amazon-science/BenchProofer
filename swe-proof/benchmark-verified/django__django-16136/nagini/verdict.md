# P2 adversarial audit — django__django-16136

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Reply:
@@ -42,10 +41,6 @@
 
     def __init__(self, methods: List[int]) -> None:
         Requires(Acc(list_pred(methods), 1 / 2))
-        # Terminates outright: a single field store, no loop and no call. Level 2
-        # leaves room beneath the level-6 caller (obligation levels are ordinals;
-        # the caller's level must strictly exceed every callee's).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.methods))  # type: ignore
         Ensures(self.methods is methods)  # type: ignore
         Ensures(Acc(list_pred(methods), 1 / 2))
@@ -60,9 +55,6 @@
 
     def __init__(self, is_awaitable: bool, reply: Reply) -> None:
         Requires(Acc(reply.methods, 1 / 2))
-        # Terminates outright: two field stores, no loop and no call. Level 2 for
-        # the same reason as Reply.__init__.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_awaitable))  # type: ignore
         Ensures(Acc(self.reply))  # type: ignore
         Ensures(self.is_awaitable == is_awaitable)  # type: ignore
@@ -86,7 +78,6 @@
 def method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered:
     # pre-conditions-start
     Requires(Acc(list_pred(allowed_methods), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(allowed_methods), 1 / 2))
@@ -103,9 +94,6 @@
     # post-conditions-end
     # impl-start
     response = Reply(allowed_methods)
-    if async_mode:
-        result = Delivered(True, response)
-    else:
-        result = Delivered(False, response)
+    result = Delivered(False, response)
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Reply:
@@ -42,10 +41,6 @@
 
     def __init__(self, methods: List[int]) -> None:
         Requires(Acc(list_pred(methods), 1 / 2))
-        # Terminates outright: a single field store, no loop and no call. Level 2
-        # leaves room beneath the level-6 caller (obligation levels are ordinals;
-        # the caller's level must strictly exceed every callee's).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.methods))  # type: ignore
         Ensures(self.methods is methods)  # type: ignore
         Ensures(Acc(list_pred(methods), 1 / 2))
@@ -60,9 +55,6 @@
 
     def __init__(self, is_awaitable: bool, reply: Reply) -> None:
         Requires(Acc(reply.methods, 1 / 2))
-        # Terminates outright: two field stores, no loop and no call. Level 2 for
-        # the same reason as Reply.__init__.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_awaitable))  # type: ignore
         Ensures(Acc(self.reply))  # type: ignore
         Ensures(self.is_awaitable == is_awaitable)  # type: ignore
@@ -86,7 +78,6 @@
 def method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered:
     # pre-conditions-start
     Requires(Acc(list_pred(allowed_methods), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(allowed_methods), 1 / 2))
@@ -104,8 +95,8 @@
     # impl-start
     response = Reply(allowed_methods)
     if async_mode:
+        result = Delivered(False, response)
+    else:
         result = Delivered(True, response)
-    else:
-        result = Delivered(False, response)
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Reply:
@@ -42,10 +41,6 @@
 
     def __init__(self, methods: List[int]) -> None:
         Requires(Acc(list_pred(methods), 1 / 2))
-        # Terminates outright: a single field store, no loop and no call. Level 2
-        # leaves room beneath the level-6 caller (obligation levels are ordinals;
-        # the caller's level must strictly exceed every callee's).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.methods))  # type: ignore
         Ensures(self.methods is methods)  # type: ignore
         Ensures(Acc(list_pred(methods), 1 / 2))
@@ -60,9 +55,6 @@
 
     def __init__(self, is_awaitable: bool, reply: Reply) -> None:
         Requires(Acc(reply.methods, 1 / 2))
-        # Terminates outright: two field stores, no loop and no call. Level 2 for
-        # the same reason as Reply.__init__.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_awaitable))  # type: ignore
         Ensures(Acc(self.reply))  # type: ignore
         Ensures(self.is_awaitable == is_awaitable)  # type: ignore
@@ -86,7 +78,6 @@
 def method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered:
     # pre-conditions-start
     Requires(Acc(list_pred(allowed_methods), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(allowed_methods), 1 / 2))
@@ -103,9 +94,6 @@
     # post-conditions-end
     # impl-start
     response = Reply(allowed_methods)
-    if async_mode:
-        result = Delivered(True, response)
-    else:
-        result = Delivered(False, response)
+    result = Delivered(True, response)
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Reply:
@@ -42,10 +41,6 @@
 
     def __init__(self, methods: List[int]) -> None:
         Requires(Acc(list_pred(methods), 1 / 2))
-        # Terminates outright: a single field store, no loop and no call. Level 2
-        # leaves room beneath the level-6 caller (obligation levels are ordinals;
-        # the caller's level must strictly exceed every callee's).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.methods))  # type: ignore
         Ensures(self.methods is methods)  # type: ignore
         Ensures(Acc(list_pred(methods), 1 / 2))
@@ -60,9 +55,6 @@
 
     def __init__(self, is_awaitable: bool, reply: Reply) -> None:
         Requires(Acc(reply.methods, 1 / 2))
-        # Terminates outright: two field stores, no loop and no call. Level 2 for
-        # the same reason as Reply.__init__.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_awaitable))  # type: ignore
         Ensures(Acc(self.reply))  # type: ignore
         Ensures(self.is_awaitable == is_awaitable)  # type: ignore
@@ -86,7 +78,6 @@
 def method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered:
     # pre-conditions-start
     Requires(Acc(list_pred(allowed_methods), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(allowed_methods), 1 / 2))
@@ -102,7 +93,8 @@
     Ensures(Result().reply.methods is allowed_methods)
     # post-conditions-end
     # impl-start
-    response = Reply(allowed_methods)
+    fresh = []  # type: List[int]
+    response = Reply(fresh)
     if async_mode:
         result = Delivered(True, response)
     else:
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Reply:
@@ -42,10 +41,6 @@
 
     def __init__(self, methods: List[int]) -> None:
         Requires(Acc(list_pred(methods), 1 / 2))
-        # Terminates outright: a single field store, no loop and no call. Level 2
-        # leaves room beneath the level-6 caller (obligation levels are ordinals;
-        # the caller's level must strictly exceed every callee's).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.methods))  # type: ignore
         Ensures(self.methods is methods)  # type: ignore
         Ensures(Acc(list_pred(methods), 1 / 2))
@@ -60,9 +55,6 @@
 
     def __init__(self, is_awaitable: bool, reply: Reply) -> None:
         Requires(Acc(reply.methods, 1 / 2))
-        # Terminates outright: two field stores, no loop and no call. Level 2 for
-        # the same reason as Reply.__init__.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_awaitable))  # type: ignore
         Ensures(Acc(self.reply))  # type: ignore
         Ensures(self.is_awaitable == is_awaitable)  # type: ignore
@@ -86,7 +78,6 @@
 def method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered:
     # pre-conditions-start
     Requires(Acc(list_pred(allowed_methods), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(allowed_methods), 1 / 2))
@@ -103,9 +94,7 @@
     # post-conditions-end
     # impl-start
     response = Reply(allowed_methods)
-    if async_mode:
-        result = Delivered(True, response)
-    else:
-        result = Delivered(False, response)
+    dummy = Reply(allowed_methods)  # extra allocation, unused in the result
+    result = Delivered(async_mode, response)
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Reply:
@@ -42,10 +41,6 @@
 
     def __init__(self, methods: List[int]) -> None:
         Requires(Acc(list_pred(methods), 1 / 2))
-        # Terminates outright: a single field store, no loop and no call. Level 2
-        # leaves room beneath the level-6 caller (obligation levels are ordinals;
-        # the caller's level must strictly exceed every callee's).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.methods))  # type: ignore
         Ensures(self.methods is methods)  # type: ignore
         Ensures(Acc(list_pred(methods), 1 / 2))
@@ -60,9 +55,6 @@
 
     def __init__(self, is_awaitable: bool, reply: Reply) -> None:
         Requires(Acc(reply.methods, 1 / 2))
-        # Terminates outright: two field stores, no loop and no call. Level 2 for
-        # the same reason as Reply.__init__.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_awaitable))  # type: ignore
         Ensures(Acc(self.reply))  # type: ignore
         Ensures(self.is_awaitable == is_awaitable)  # type: ignore
@@ -86,7 +78,6 @@
 def method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered:
     # pre-conditions-start
     Requires(Acc(list_pred(allowed_methods), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(allowed_methods), 1 / 2))
@@ -104,8 +95,8 @@
     # impl-start
     response = Reply(allowed_methods)
     if async_mode:
-        result = Delivered(True, response)
+        result = Delivered(True, Reply(allowed_methods))
     else:
-        result = Delivered(False, response)
+        result = Delivered(False, Reply(allowed_methods))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16136.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A request-handler method produces the "method not allowed" reply for a view.
  It first builds the not-allowed reply object carrying the list of permitted
  methods. It must then deliver that reply in the calling convention the view's
  execution mode requires:

    (1) when the view runs in the asynchronous mode, the method returns an
        awaitable placeholder that resolves to the reply (so a caller may
        await it); the returned object is therefore recognised as an awaitable
        placeholder;

    (2) when the view runs in the synchronous mode, the method returns the
        reply object directly; the returned object is NOT an awaitable
        placeholder.

  In BOTH modes the reply that is ultimately delivered (the resolved value in
  the asynchronous mode, the direct value in the synchronous mode) is the SAME
  not-allowed reply object, carrying the same list of permitted methods. That
  is: deciding the delivery convention from the execution mode must not change
  which reply is delivered.

The view's execution mode is modelled by a boolean (the asynchronous-mode
flag). The not-allowed reply is a minimal object carrying only the touched
field (its list of permitted methods, a ``List[int]`` of method tokens). The
method's return value is a minimal result object exposing the two observable
facts a caller checks: whether the returned object is an awaitable placeholder,
and the not-allowed reply that is (eventually) delivered.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Reply:
    """The not-allowed reply object; carries only the touched field, the list
    of permitted method tokens."""

    def __init__(self, methods: List[int]) -> None:
        Requires(Acc(list_pred(methods), 1 / 2))
        Ensures(Acc(self.methods))  # type: ignore
        Ensures(self.methods is methods)  # type: ignore
        Ensures(Acc(list_pred(methods), 1 / 2))
        self.methods = methods  # type: List[int]


class Delivered:
    """The value returned by the handler: the two observable facts a caller
    inspects. ``is_awaitable`` records whether the returned object is an
    awaitable placeholder; ``reply`` is the not-allowed reply that is
    delivered (directly, or as the resolved value of the placeholder)."""

    def __init__(self, is_awaitable: bool, reply: Reply) -> None:
        Requires(Acc(reply.methods, 1 / 2))
        Ensures(Acc(self.is_awaitable))  # type: ignore
        Ensures(Acc(self.reply))  # type: ignore
        Ensures(self.is_awaitable == is_awaitable)  # type: ignore
        Ensures(self.reply is reply)  # type: ignore
        Ensures(Acc(reply.methods, 1 / 2))
        self.is_awaitable = is_awaitable  # type: bool
        self.reply = reply  # type: Reply


# axioms-start
# (no unchanged-callee axioms are required for this behaviour; the conditional
# delivery is modelled deeply below)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered:
    # pre-conditions-start
    Requires(Acc(list_pred(allowed_methods), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(allowed_methods), 1 / 2))
    Ensures(Acc(Result().is_awaitable))
    Ensures(Acc(Result().reply))
    Ensures(Acc(Result().reply.methods, 1 / 2))
    # (1)+(2): the returned object is an awaitable placeholder exactly when the
    # view runs in the asynchronous mode.
    Ensures(Result().is_awaitable == async_mode)
    # The reply delivered in BOTH modes is a not-allowed reply built from the
    # given permitted methods — deciding the delivery convention does not change
    # which reply is delivered.
    Ensures(Result().reply.methods is allowed_methods)
    # post-conditions-end
    # impl-start
    response = Reply(allowed_methods)
    if async_mode:
        result = Delivered(True, response)
    else:
        result = Delivered(False, response)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec pins BOTH caller-observables exactly: Ensures(Result().is_awaitable == async_mode) and Ensures(Result().reply.methods is allowed_methods). Positive control (bundle model.py) VERIFIES (10.1s). All 6 attacks are byte-identical spec (same-spec exit 0), impl-region only.

atk_1 (prepatch bug reproduced: Delivered(False, response) always) -> does NOT verify (fails is_awaitable==async_mode on async case). This IS the model_prepatch impl.
- atk_2 (inverted flag: awaitable iff SYNC) -> does NOT verify.
- atk_3 (partial-domain: always awaitable True) -> does NOT verify.
- atk_4 (boundary/ungrounded: builds Reply from a fresh empty list) -> does NOT verify (fails reply.methods is allowed_methods).
- atk_5 (control-flow echo: Delivered(async_mode, response) + unused extra HttpResponseNotAllowed alloc) -> CANDIDATE (verifies 12.7s).
- atk_6 (ungrounded-oracle echo: delivers a SECOND fresh HttpResponseNotAllowed carrying the same _allowed_methods()) -> CANDIDATE (verifies 12.8s).

Both CANDIDATE faithful patches materialized and run through the OFFICIAL harness (swebench_unified.harness.run_resolve, timeout 1800, docker):
- gold baseline: resolved=true, completed=true.
- atk_5 patch: resolved=true, completed=true (attempts=1).
- atk_6 patch: resolved=true, completed=true (attempts=1). NOTE: first atk_6 run reported completed=false 'no report/harness error' due to a MALFORMED hunk header on MY patch (@@ +148,18 with only 16 new lines); after correcting the count to +148,16 it RESOLVED. The infra 'not completed' was a patch-authoring artifact, not a spec weakness; re-run alone confirmed resolve. atk_6 resolves because the F2P test (test_http_method_not_allowed_responds_correctly) only checks asyncio.iscoroutine(response)==mode and isinstance(response, HttpResponseNotAllowed) after asyncio.run -- a fresh HttpResponseNotAllowed with the same methods still satisfies isinstance; identity of the object is NOT tested. The spec's stricter reply-identity clause (is allowed_methods) is a sound over-approximation: it only ADMITS impls that also resolve.

No verifying wrong impl produced a non-resolving refined patch => verify => correct held on all attacks.

refinement.md audit: A1/A2/A3 = R (bool<->bool, list[str]<->List[int] token encoding, HttpResponseNotAllowed<->Reply carrying only touched field); A4/A7 = I (identical control flow / return); A5/A6/B1 = A-reference (deep model of async def-wrap-iff-async delivery). NO consumed @ContractOnly axiom (axioms region empty), NO kind-3 unexpressible-changed-op leg. A-reference correspondence validated by axiom_check.py (G-AX rc=0: 'sound on 10 boundary + 4000 fuzz inputs') which reproduces the EXACT gold construct (async def func(): return response; func()) and asserts the three facts via asyncio.iscoroutine/asyncio.run -- the same predicates the F2P test uses. Correspondence to the real callees (View.http_method_not_allowed delivery, identical in shape to View.options) holds.

Commands:
  python -m swebench_unified.adversary same-spec nagini django__django-16136 <atk>   (all 6 -> SAME)
  python -m swebench_unified.adversary weakness  nagini django__django-16136 <atk>   (1-4 exit2; 5,6 exit0)
  bash scripts/nagini_verify.sh <pos_control>                                        (VERIFIED 10.1s)
  python <resolve_one.py> <name> <patch.diff>  (run_resolve; gold/atk5/atk6 all resolved=true)
  python benchmark-verified/django__django-16136/nagini/axiom_check.py               (G-AX rc=0)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16136.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A request-handler method produces the "method not allowed" reply for a view.
  It first builds the not-allowed reply object carrying the list of permitted
  methods. It must then deliver that reply in the calling convention the view's
  execution mode requires:

    (1) when the view runs in the asynchronous mode, the method returns an
        awaitable placeholder that resolves to the reply (so a caller may
        await it); the returned object is therefore recognised as an awaitable
        placeholder;

    (2) when the view runs in the synchronous mode, the method returns the
        reply object directly; the returned object is NOT an awaitable
        placeholder.

  In BOTH modes the reply that is ultimately delivered (the resolved value in
  the asynchronous mode, the direct value in the synchronous mode) is the SAME
  not-allowed reply object, carrying the same list of permitted methods. That
  is: deciding the delivery convention from the execution mode must not change
  which reply is delivered.

The view's execution mode is modelled by a boolean (the asynchronous-mode
flag). The not-allowed reply is a minimal object carrying only the touched
field (its list of permitted methods, a ``List[int]`` of method tokens). The
method's return value is a minimal result object exposing the two observable
facts a caller checks: whether the returned object is an awaitable placeholder,
and the not-allowed reply that is (eventually) delivered.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Reply:
    """The not-allowed reply object; carries only the touched field, the list
    of permitted method tokens."""

    def __init__(self, methods: List[int]) -> None:
        Requires(Acc(list_pred(methods), 1 / 2))
        Ensures(Acc(self.methods))  # type: ignore
        Ensures(self.methods is methods)  # type: ignore
        Ensures(Acc(list_pred(methods), 1 / 2))
        self.methods = methods  # type: List[int]


class Delivered:
    """The value returned by the handler: the two observable facts a caller
    inspects. ``is_awaitable`` records whether the returned object is an
    awaitable placeholder; ``reply`` is the not-allowed reply that is
    delivered (directly, or as the resolved value of the placeholder)."""

    def __init__(self, is_awaitable: bool, reply: Reply) -> None:
        Requires(Acc(reply.methods, 1 / 2))
        Ensures(Acc(self.is_awaitable))  # type: ignore
        Ensures(Acc(self.reply))  # type: ignore
        Ensures(self.is_awaitable == is_awaitable)  # type: ignore
        Ensures(self.reply is reply)  # type: ignore
        Ensures(Acc(reply.methods, 1 / 2))
        self.is_awaitable = is_awaitable  # type: bool
        self.reply = reply  # type: Reply


# axioms-start
# (no unchanged-callee axioms are required for this behaviour; the conditional
# delivery is modelled deeply below)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered:
    # pre-conditions-start
    Requires(Acc(list_pred(allowed_methods), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(allowed_methods), 1 / 2))
    Ensures(Acc(Result().is_awaitable))
    Ensures(Acc(Result().reply))
    Ensures(Acc(Result().reply.methods, 1 / 2))
    # (1)+(2): the returned object is an awaitable placeholder exactly when the
    # view runs in the asynchronous mode.
    Ensures(Result().is_awaitable == async_mode)
    # The reply delivered in BOTH modes is a not-allowed reply built from the
    # given permitted methods — deciding the delivery convention does not change
    # which reply is delivered.
    Ensures(Result().reply.methods is allowed_methods)
    # post-conditions-end
    # impl-start
    response = Reply(allowed_methods)
    if async_mode:
        result = Delivered(True, response)
    else:
        result = Delivered(False, response)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec pins BOTH caller-observables exactly: Ensures(Result().is_awaitable == async_mode) and Ensures(Result().reply.methods is allowed_methods). Positive control (bundle model.py) VERIFIES (10.1s). All 6 attacks are byte-identical spec (same-spec exit 0), impl-region only.

atk_1 (prepatch bug reproduced: Delivered(False, response) always) -> does NOT verify (fails is_awaitable==async_mode on async case). This IS the model_prepatch impl.
- atk_2 (inverted flag: awaitable iff SYNC) -> does NOT verify.
- atk_3 (partial-domain: always awaitable True) -> does NOT verify.
- atk_4 (boundary/ungrounded: builds Reply from a fresh empty list) -> does NOT verify (fails reply.methods is allowed_methods).
- atk_5 (control-flow echo: Delivered(async_mode, response) + unused extra HttpResponseNotAllowed alloc) -> CANDIDATE (verifies 12.7s).
- atk_6 (ungrounded-oracle echo: delivers a SECOND fresh HttpResponseNotAllowed carrying the same _allowed_methods()) -> CANDIDATE (verifies 12.8s).

Both CANDIDATE faithful patches materialized and run through the OFFICIAL harness (swebench_unified.harness.run_resolve, timeout 1800, docker):
- gold baseline: resolved=true, completed=true.
- atk_5 patch: resolved=true, completed=true (attempts=1).
- atk_6 patch: resolved=true, completed=true (attempts=1). NOTE: first atk_6 run reported completed=false 'no report/harness error' due to a MALFORMED hunk header on MY patch (@@ +148,18 with only 16 new lines); after correcting the count to +148,16 it RESOLVED. The infra 'not completed' was a patch-authoring artifact, not a spec weakness; re-run alone confirmed resolve. atk_6 resolves because the F2P test (test_http_method_not_allowed_responds_correctly) only checks asyncio.iscoroutine(response)==mode and isinstance(response, HttpResponseNotAllowed) after asyncio.run -- a fresh HttpResponseNotAllowed with the same methods still satisfies isinstance; identity of the object is NOT tested. The spec's stricter reply-identity clause (is allowed_methods) is a sound over-approximation: it only ADMITS impls that also resolve.

No verifying wrong impl produced a non-resolving refined patch => verify => correct held on all attacks.

refinement.md audit: A1/A2/A3 = R (bool<->bool, list[str]<->List[int] token encoding, HttpResponseNotAllowed<->Reply carrying only touched field); A4/A7 = I (identical control flow / return); A5/A6/B1 = A-reference (deep model of async def-wrap-iff-async delivery). NO consumed @ContractOnly axiom (axioms region empty), NO kind-3 unexpressible-changed-op leg. A-reference correspondence validated by axiom_check.py (G-AX rc=0: 'sound on 10 boundary + 4000 fuzz inputs') which reproduces the EXACT gold construct (async def func(): return response; func()) and asserts the three facts via asyncio.iscoroutine/asyncio.run -- the same predicates the F2P test uses. Correspondence to the real callees (View.http_method_not_allowed delivery, identical in shape to View.options) holds.

Commands:
  python -m swebench_unified.adversary same-spec nagini django__django-16136 <atk>   (all 6 -> SAME)
  python -m swebench_unified.adversary weakness  nagini django__django-16136 <atk>   (1-4 exit2; 5,6 exit0)
  bash scripts/nagini_verify.sh <pos_control>                                        (VERIFIED 10.1s)
  python <resolve_one.py> <name> <patch.diff>  (run_resolve; gold/atk5/atk6 all resolved=true)
  python benchmark-verified/django__django-16136/nagini/axiom_check.py               (G-AX rc=0)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo) confirmed for django__django-16136 nagini bundle.

Modeled function: method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered, mapping to View.http_method_not_allowed in django/views/generic/base.py:144-160 (patched, verified against worktree).

Spec (postconditions) asserts exactly two caller-observable facts:
  (1) Result().is_awaitable == async_mode  <->  asyncio.iscoroutine(return) == view_is_async (real returns a coroutine via `async def func()` iff view_is_async, else the bare response).
  (2) Result().reply.methods is allowed_methods  <->  the single HttpResponseNotAllowed(self._allowed_methods()) is built once (base.py:151) and delivered in BOTH branches, directly (sync) or as the coroutine's resolved value (async), preserving identity of the method list.

Checks run:
  - axiom_check.py (G-AX deep-model reference): exit 0; reproduces the exact gold construct (async def wrap iff async, bare else) and asserts iscoroutine==flag, reply identity, and method-list preservation over 10 boundary + 4000 fuzz inputs.
  - scripts/nagini_verify.sh model.py: 'Verification successful' (exit 0).

The spec neither over-constrains nor drifts: it captures precisely the discriminating change (awaitable-iff-async delivery) and the reply-preservation invariant, both of which the real patched method satisfies on every (bool, method-list) input. The omitted logger.warning side effect at base.py:145-150 is unchanged by the patch and does not affect the return value the F2P test inspects, so its omission is not a divergence. No input exists where the modeled function disagrees with the real callee's observable return behaviour.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Assessed the spec view (markers.spec_view over model.py via the nagini backend) against the PUBLIC problem_statement (not hints_text). Verdict: NO-LEAKAGE.

What the spec view exposes: docstring + the Reply/Delivered carrier classes + method_not_allowed's pre/postconditions. The discriminating postconditions are (i) Ensures(Result().is_awaitable == async_mode) and (ii) Ensures(Result().reply.methods is allowed_methods). The impl region (lines 96-101, the actual branch that constructs Delivered(True/False, response)) is ELIDED to `...` in the spec view.

Why this does not leak beyond problem_statement: the public problem_statement already fully discloses the core issue — 'object HttpResponseNotAllowed can't be used in await expression'; an async View with only an async post crashes on GET because the method-not-allowed response is not awaitable. Any fix therefore must make the not-allowed response awaitable exactly when the view is async, while still delivering the same not-allowed reply. The spec view merely formalizes that public observable contract abstractly ('awaitable placeholder exactly when the view runs in the asynchronous mode', same reply in both modes). This is a faithful abstraction of the public bug report, not a disclosure of the edit mechanism.

Lexical checks (all clean): (1) no diff markers (@@, +++, 'diff --git'); (2) none of the gold-patch changed lines reproduced — 'response = HttpResponseNotAllowed(self._allowed_methods())', 'if self.view_is_async:', 'async def func():', 'return func()' do not appear; the coroutine-wrap mechanism lives only in the elided impl region; (3) no patched file path 'django/views/generic/base.py' or dotted module path; (4) no repo symbols — model uses abstract carriers (method_not_allowed, async_mode, allowed_methods, Reply, Delivered); the discriminating repo names view_is_async / HttpResponseNotAllowed / _allowed_methods never appear; (5) no bug/fix narration in comments — the docstring explicitly frames behavior 'as desired behaviour, not as an edit'.

Empirical confirmation: swebench_unified.leakage.screen(model.py, nagini backend, gold patch_diff, problem_statement) returns passed=True, hard_failures=[], warnings=[]. Bundle is not relaxed (no RELAXED_LEAKAGE.md), so no deferral is needed; recorded meta G-LEAK status is 'pass' and G-PANEL-3 agent_verdict is NO-LEAKAGE — both consistent with this independent assessment.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
