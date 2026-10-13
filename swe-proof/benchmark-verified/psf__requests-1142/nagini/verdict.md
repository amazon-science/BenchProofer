# P2 adversarial audit — psf__requests-1142

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,17 +91,6 @@
     Requires(size_header() not in headers)
     # A seekable stream is always a present body (the non-bodyless case).
     Requires(Implies(seekable, body_present))
-    # Termination is demanded of every call, so what the postconditions below
-    # claim is TOTAL correctness: an implementation that never reaches the
-    # return no longer satisfies them vacuously. The level is arg-dependent
-    # rather than a bare constant because a callee must sit STRICTLY below its
-    # caller, so no constant could ever admit a delegation to this same
-    # operation against itself (it would need n > n). Announcing the size for a
-    # body-present call is one level above the bodyless case, which leaves
-    # exactly the room such a delegation needs. Both levels are finite, so
-    # termination is demanded just as strongly on every input -- this orders the
-    # obligation, it does not weaken it.
-    Requires(MustTerminate(3 if body_present else 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(headers))
@@ -145,10 +133,9 @@
     Ensures(method == Old(method))
     # post-conditions-end
     # impl-start
+    headers[size_header()] = 0
     if seekable:
         headers[size_header()] = stream_len
     elif body_present:
         headers[size_header()] = body_len
-    elif method != method_get() and method != method_head():
-        headers[size_header()] = 0
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,17 +91,6 @@
     Requires(size_header() not in headers)
     # A seekable stream is always a present body (the non-bodyless case).
     Requires(Implies(seekable, body_present))
-    # Termination is demanded of every call, so what the postconditions below
-    # claim is TOTAL correctness: an implementation that never reaches the
-    # return no longer satisfies them vacuously. The level is arg-dependent
-    # rather than a bare constant because a callee must sit STRICTLY below its
-    # caller, so no constant could ever admit a delegation to this same
-    # operation against itself (it would need n > n). Announcing the size for a
-    # body-present call is one level above the bodyless case, which leaves
-    # exactly the room such a delegation needs. Both levels are finite, so
-    # termination is demanded just as strongly on every input -- this orders the
-    # obligation, it does not weaken it.
-    Requires(MustTerminate(3 if body_present else 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(headers))
@@ -149,6 +137,6 @@
         headers[size_header()] = stream_len
     elif body_present:
         headers[size_header()] = body_len
-    elif method != method_get() and method != method_head():
+    else:
         headers[size_header()] = 0
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,17 +91,6 @@
     Requires(size_header() not in headers)
     # A seekable stream is always a present body (the non-bodyless case).
     Requires(Implies(seekable, body_present))
-    # Termination is demanded of every call, so what the postconditions below
-    # claim is TOTAL correctness: an implementation that never reaches the
-    # return no longer satisfies them vacuously. The level is arg-dependent
-    # rather than a bare constant because a callee must sit STRICTLY below its
-    # caller, so no constant could ever admit a delegation to this same
-    # operation against itself (it would need n > n). Announcing the size for a
-    # body-present call is one level above the bodyless case, which leaves
-    # exactly the room such a delegation needs. Both levels are finite, so
-    # termination is demanded just as strongly on every input -- this orders the
-    # obligation, it does not weaken it.
-    Requires(MustTerminate(3 if body_present else 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(headers))
@@ -150,5 +138,5 @@
     elif body_present:
         headers[size_header()] = body_len
     elif method != method_get() and method != method_head():
-        headers[size_header()] = 0
+        headers[size_header()] = 1
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,17 +91,6 @@
     Requires(size_header() not in headers)
     # A seekable stream is always a present body (the non-bodyless case).
     Requires(Implies(seekable, body_present))
-    # Termination is demanded of every call, so what the postconditions below
-    # claim is TOTAL correctness: an implementation that never reaches the
-    # return no longer satisfies them vacuously. The level is arg-dependent
-    # rather than a bare constant because a callee must sit STRICTLY below its
-    # caller, so no constant could ever admit a delegation to this same
-    # operation against itself (it would need n > n). Announcing the size for a
-    # body-present call is one level above the bodyless case, which leaves
-    # exactly the room such a delegation needs. Both levels are finite, so
-    # termination is demanded just as strongly on every input -- this orders the
-    # obligation, it does not weaken it.
-    Requires(MustTerminate(3 if body_present else 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(headers))
@@ -151,4 +139,5 @@
         headers[size_header()] = body_len
     elif method != method_get() and method != method_head():
         headers[size_header()] = 0
+    headers[size_header() + 1] = 7
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,17 +91,6 @@
     Requires(size_header() not in headers)
     # A seekable stream is always a present body (the non-bodyless case).
     Requires(Implies(seekable, body_present))
-    # Termination is demanded of every call, so what the postconditions below
-    # claim is TOTAL correctness: an implementation that never reaches the
-    # return no longer satisfies them vacuously. The level is arg-dependent
-    # rather than a bare constant because a callee must sit STRICTLY below its
-    # caller, so no constant could ever admit a delegation to this same
-    # operation against itself (it would need n > n). Announcing the size for a
-    # body-present call is one level above the bodyless case, which leaves
-    # exactly the room such a delegation needs. Both levels are finite, so
-    # termination is demanded just as strongly on every input -- this orders the
-    # obligation, it does not weaken it.
-    Requires(MustTerminate(3 if body_present else 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(headers))
@@ -145,10 +133,12 @@
     Ensures(method == Old(method))
     # post-conditions-end
     # impl-start
-    if seekable:
+    payload_method = method != method_get() and method != method_head()
+    if not seekable and not body_present:
+        if payload_method:
+            headers[size_header()] = 0
+    elif seekable:
         headers[size_header()] = stream_len
-    elif body_present:
+    else:
         headers[size_header()] = body_len
-    elif method != method_get() and method != method_head():
-        headers[size_header()] = 0
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,17 +91,6 @@
     Requires(size_header() not in headers)
     # A seekable stream is always a present body (the non-bodyless case).
     Requires(Implies(seekable, body_present))
-    # Termination is demanded of every call, so what the postconditions below
-    # claim is TOTAL correctness: an implementation that never reaches the
-    # return no longer satisfies them vacuously. The level is arg-dependent
-    # rather than a bare constant because a callee must sit STRICTLY below its
-    # caller, so no constant could ever admit a delegation to this same
-    # operation against itself (it would need n > n). Announcing the size for a
-    # body-present call is one level above the bodyless case, which leaves
-    # exactly the room such a delegation needs. Both levels are finite, so
-    # termination is demanded just as strongly on every input -- this orders the
-    # obligation, it does not weaken it.
-    Requires(MustTerminate(3 if body_present else 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(headers))
@@ -146,7 +134,7 @@
     # post-conditions-end
     # impl-start
     if seekable:
-        headers[size_header()] = stream_len
+        headers[size_header()] = body_len
     elif body_present:
         headers[size_header()] = body_len
     elif method != method_get() and method != method_head():
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,17 +91,6 @@
     Requires(size_header() not in headers)
     # A seekable stream is always a present body (the non-bodyless case).
     Requires(Implies(seekable, body_present))
-    # Termination is demanded of every call, so what the postconditions below
-    # claim is TOTAL correctness: an implementation that never reaches the
-    # return no longer satisfies them vacuously. The level is arg-dependent
-    # rather than a bare constant because a callee must sit STRICTLY below its
-    # caller, so no constant could ever admit a delegation to this same
-    # operation against itself (it would need n > n). Announcing the size for a
-    # body-present call is one level above the bodyless case, which leaves
-    # exactly the room such a delegation needs. Both levels are finite, so
-    # termination is demanded just as strongly on every input -- this orders the
-    # obligation, it does not weaken it.
-    Requires(MustTerminate(3 if body_present else 2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(dict_pred(headers))
@@ -149,6 +137,6 @@
         headers[size_header()] = stream_len
     elif body_present:
         headers[size_header()] = body_len
-    elif method != method_get() and method != method_head():
+    elif method == method_get() or method == method_head():
         headers[size_header()] = 0
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for psf__requests-1142.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An outgoing HTTP request is being finalised, and a header that announces the
  size of the message body must be set on the request's header map. The size to
  announce depends on the body that will be sent:

    * If the body is a seekable stream (it can report its own position), the
      announced size is the stream's measured length.
    * Otherwise, if a body is actually present, the announced size is the
      length of that body.
    * Otherwise there is no body at all. A size MUST be announced only when the
      request method is one that carries a payload; for the payload-less
      methods that conventionally have no body (the read-only retrieval method
      and the headers-only method) NO size header is announced at all -- the
      header map is left without it. This is the behaviour that matters: a
      bodyless request using one of those two methods carries no body-size
      header, whereas a bodyless request using any other method announces a
      zero size.

  In every case the announced size, when present, equals the size determined
  above, and the request method itself is never altered by this operation.
  The operation writes AT MOST the body-size header: no other header of the
  map is added, removed, or changed.

Modelling choices (Nagini fragment):
  * The request's header map is a ``Dict[int, int]`` from a header-name token to
    the announced size. Membership of the body-size header's name token models
    "the size header is present"; its value models the announced size. Only
    presence and the per-name value are observed, so the integer carrier is
    faithful (mapping.md S2).
  * The HTTP method is a method-identity token (an ``int``); the two payload-
    less methods are the module constants ``method_get()`` and ``method_head()``
    and any other token is a payload-carrying method.
  * The body is described by the observations the operation makes on it: whether
    it is a seekable stream (``seekable``) and, if so, its measured length
    (``stream_len``); whether a non-stream body is present (``body_present``)
    and, if so, its length (``body_len``). ``not seekable and not body_present``
    is the bodyless case.

The header map is genuinely mutated in place, so it is held at full permission
and its exact post-state is stated; the read-only method token is not mutated.
The behaviour is modelled deeply (the guarded size announcement is spelled out
in the impl region); there is no axiomatised callee. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the guarded body-size announcement is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def size_header() -> int:
    # The header-name token of the body-size header. Its presence as a key in
    # the header map models "the body-size header is announced".
    return 0


@Pure
def method_get() -> int:
    # Identity token of the read-only retrieval method (a payload-less method).
    return 1


@Pure
def method_head() -> int:
    # Identity token of the headers-only method (a payload-less method).
    return 2
# pure-end


def announce_body_size(headers: Dict[int, int], method: int,
                       seekable: bool, stream_len: int,
                       body_present: bool, body_len: int) -> None:
    # pre-conditions-start
    # The header map is mutated in place; full permission.
    Requires(dict_pred(headers))
    # The size header has not yet been announced when this operation runs: the
    # header map was just built fresh for this request and no body-size header
    # is present yet. The operation only ever announces the header, never
    # removes one, so for the bodyless payload-less case the header is absent
    # exactly because it was never announced.
    Requires(size_header() not in headers)
    # A seekable stream is always a present body (the non-bodyless case).
    Requires(Implies(seekable, body_present))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(headers))
    # (1) Seekable stream: the size header is announced and equals the stream's
    #     measured length.
    Ensures(Implies(seekable,
                    size_header() in headers and
                    headers[size_header()] == stream_len))
    # (2) Non-stream body present: the size header is announced and equals the
    #     body's length.
    Ensures(Implies(not seekable and body_present,
                    size_header() in headers and
                    headers[size_header()] == body_len))
    # (3) Bodyless: a size header is announced (with zero size) for a payload-
    #     carrying method, and is NOT announced for either payload-less method.
    #     This is the discriminating clause: presence is conditioned on the
    #     method, so a bodyless retrieval/headers-only request carries no size
    #     header, while a bodyless request of any other method announces zero.
    Ensures(Implies(not seekable and not body_present,
                    (size_header() in headers) ==
                    (method != method_get() and method != method_head())))
    Ensures(Implies(not seekable and not body_present and
                    method != method_get() and method != method_head(),
                    headers[size_header()] == 0))
    # (4) Whole-map frame: the operation writes AT MOST the body-size header.
    #     Every OTHER header name keeps its membership, and every other header
    #     that was present keeps its exact value. Without this frame the spec
    #     would admit an implementation that smuggles an extra header into the
    #     request (e.g. a spurious probe header) — the operation under
    #     specification never touches any other entry of the header map.
    #     (Explicit triggers keep the quantifiers tractable for the verifier.)
    Ensures(Forall(int, lambda k: (Implies(k != size_header(),
                                           (k in headers) == Old(k in headers)),
                                   [[k in headers]])))
    Ensures(Forall(int, lambda k: (Implies(k != size_header() and
                                           k in headers and Old(k in headers),
                                           headers[k] == Old(headers[k])),
                                   [[headers[k]]])))
    # (5) The method token is never altered by this operation.
    Ensures(method == Old(method))
    # post-conditions-end
    # impl-start
    if seekable:
        headers[size_header()] = stream_len
    elif body_present:
        headers[size_header()] = body_len
    elif method != method_get() and method != method_head():
        headers[size_header()] = 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit of psf__requests-1142 nagini bundle.

SPEC SHAPE: The frozen spec pins the ENTIRE observable post-state of announce_body_size: exact value in each of the 3 branches (stream_len / body_len / 0), the discriminating presence-iff-payload-method condition in the bodyless case (clause 3), a whole-map FRAME (clause 4: no other key added/removed/mutated), and method-unchanged (clause 5). This is a tight, deep model with NO axioms.

### ATTACKS (all confirmed same-spec exit 0; verifications run concurrently in 3 batches, <=3 JVMs each):
- atk_1.py PREPATCH BUG (unconditional leading headers[size_header()]=0 then seek/body branches, no method guard). weakness cmd -> exit 2 NOT-A-COUNTEREXAMPLE (verification failed): spec senses the change via clause 3. prepatch_reproduced=true.
- atk_2.py partial-domain: drop method guard, always announce 0 in bodyless case. exit 2 (verify FAIL).
- atk_3.py boundary/off-by: bodyless payload-carrying method announces 1 instead of 0. exit 2 (verify FAIL).
- atk_4.py control-flow-effect: correct branches PLUS smuggles extra header headers[size_header()+1]=7 (frame clause 4 violation). exit 2 (verify FAIL) -> frame clause is load-bearing.
- atk_5.py ungrounded-oracle echo: logically-equivalent restructuring (if not seekable and not body_present: if payload: =0; elif seekable: =stream_len; else: =body_len). weakness cmd -> exit 0 CANDIDATE (shares spec AND verifies, 15.0s). PER PROTOCOL materialized its faithful refined patch (atk_5_patch.diff, mirrors the body-is-None-first control flow) and ran harness.run_resolve('psf__requests-1142', patch): RESOLVED=True, COMPLETED=True, flaky=False, attempts=1. F2P test_no_content_length PASS; all 5 P2P PASS. A verifying echo whose faithful patch RESOLVES is NOT a weakness (per 2026-08-06 G-PANEL-1 echo policy) -> does not break the spec.
- atk_6.py wrong value: seekable branch announces body_len instead of stream_len. exit 2 (verify FAIL).
- atk_7.py inverted method guard: bodyless GET/HEAD announces 0, others absent. exit 2 (verify FAIL).

No timeouts / infra errors in any run (grep for 'timed out|TIMED OUT|infra|inconclusive' over out_atk_*.txt returned nothing) -> all exit-2 results are GENUINE verification failures, not guillotines. Positive control (bundle model.py impl) verifies (bash scripts/nagini_verify.sh -> exit 0).

REFINEMENT AUDIT: refinement.md legs 1-7 are all R (type refinements: header-name<->int key token, method<->int token, str(n)<->int value, body observations lifted to params) and leg 8 is I (deletion of leading unconditional write reflected as absence of pre-branch write). NO kind-3 (unexpressible-changed-op) leg. NO A-legs: the changed operation (guarded body-size announcement + new method guard) is modeled DEEPLY in the impl region; mapping.md §3 confirms no @ContractOnly callee. The A-soundness trust point is vacuous. axiom_check.py runs the deep-model self-consistency oracle (gold-patched prepare_content_length vs model_spec decision table over 25 boundary + 50000 fuzz inputs) -> G-AX OK exit 0, incl. explicit bodyless-GET/HEAD-no-header and bodyless-payload-zero discriminators.

CONCLUSION: >=5 distinct wrong impls (partial-domain, boundary, control-flow-effect/frame, value-swap, guard-inversion) all fail verification; the only verifying candidate is a faithful echo whose materialized patch RESOLVES under the official harness. verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for psf__requests-1142.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An outgoing HTTP request is being finalised, and a header that announces the
  size of the message body must be set on the request's header map. The size to
  announce depends on the body that will be sent:

    * If the body is a seekable stream (it can report its own position), the
      announced size is the stream's measured length.
    * Otherwise, if a body is actually present, the announced size is the
      length of that body.
    * Otherwise there is no body at all. A size MUST be announced only when the
      request method is one that carries a payload; for the payload-less
      methods that conventionally have no body (the read-only retrieval method
      and the headers-only method) NO size header is announced at all -- the
      header map is left without it. This is the behaviour that matters: a
      bodyless request using one of those two methods carries no body-size
      header, whereas a bodyless request using any other method announces a
      zero size.

  In every case the announced size, when present, equals the size determined
  above, and the request method itself is never altered by this operation.
  The operation writes AT MOST the body-size header: no other header of the
  map is added, removed, or changed.

Modelling choices (Nagini fragment):
  * The request's header map is a ``Dict[int, int]`` from a header-name token to
    the announced size. Membership of the body-size header's name token models
    "the size header is present"; its value models the announced size. Only
    presence and the per-name value are observed, so the integer carrier is
    faithful (mapping.md S2).
  * The HTTP method is a method-identity token (an ``int``); the two payload-
    less methods are the module constants ``method_get()`` and ``method_head()``
    and any other token is a payload-carrying method.
  * The body is described by the observations the operation makes on it: whether
    it is a seekable stream (``seekable``) and, if so, its measured length
    (``stream_len``); whether a non-stream body is present (``body_present``)
    and, if so, its length (``body_len``). ``not seekable and not body_present``
    is the bodyless case.

The header map is genuinely mutated in place, so it is held at full permission
and its exact post-state is stated; the read-only method token is not mutated.
The behaviour is modelled deeply (the guarded size announcement is spelled out
in the impl region); there is no axiomatised callee. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the guarded body-size announcement is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def size_header() -> int:
    # The header-name token of the body-size header. Its presence as a key in
    # the header map models "the body-size header is announced".
    return 0


@Pure
def method_get() -> int:
    # Identity token of the read-only retrieval method (a payload-less method).
    return 1


@Pure
def method_head() -> int:
    # Identity token of the headers-only method (a payload-less method).
    return 2
# pure-end


def announce_body_size(headers: Dict[int, int], method: int,
                       seekable: bool, stream_len: int,
                       body_present: bool, body_len: int) -> None:
    # pre-conditions-start
    # The header map is mutated in place; full permission.
    Requires(dict_pred(headers))
    # The size header has not yet been announced when this operation runs: the
    # header map was just built fresh for this request and no body-size header
    # is present yet. The operation only ever announces the header, never
    # removes one, so for the bodyless payload-less case the header is absent
    # exactly because it was never announced.
    Requires(size_header() not in headers)
    # A seekable stream is always a present body (the non-bodyless case).
    Requires(Implies(seekable, body_present))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(headers))
    # (1) Seekable stream: the size header is announced and equals the stream's
    #     measured length.
    Ensures(Implies(seekable,
                    size_header() in headers and
                    headers[size_header()] == stream_len))
    # (2) Non-stream body present: the size header is announced and equals the
    #     body's length.
    Ensures(Implies(not seekable and body_present,
                    size_header() in headers and
                    headers[size_header()] == body_len))
    # (3) Bodyless: a size header is announced (with zero size) for a payload-
    #     carrying method, and is NOT announced for either payload-less method.
    #     This is the discriminating clause: presence is conditioned on the
    #     method, so a bodyless retrieval/headers-only request carries no size
    #     header, while a bodyless request of any other method announces zero.
    Ensures(Implies(not seekable and not body_present,
                    (size_header() in headers) ==
                    (method != method_get() and method != method_head())))
    Ensures(Implies(not seekable and not body_present and
                    method != method_get() and method != method_head(),
                    headers[size_header()] == 0))
    # (4) Whole-map frame: the operation writes AT MOST the body-size header.
    #     Every OTHER header name keeps its membership, and every other header
    #     that was present keeps its exact value. Without this frame the spec
    #     would admit an implementation that smuggles an extra header into the
    #     request (e.g. a spurious probe header) — the operation under
    #     specification never touches any other entry of the header map.
    #     (Explicit triggers keep the quantifiers tractable for the verifier.)
    Ensures(Forall(int, lambda k: (Implies(k != size_header(),
                                           (k in headers) == Old(k in headers)),
                                   [[k in headers]])))
    Ensures(Forall(int, lambda k: (Implies(k != size_header() and
                                           k in headers and Old(k in headers),
                                           headers[k] == Old(headers[k])),
                                   [[headers[k]]])))
    # (5) The method token is never altered by this operation.
    Ensures(method == Old(method))
    # post-conditions-end
    # impl-start
    if seekable:
        headers[size_header()] = stream_len
    elif body_present:
        headers[size_header()] = body_len
    elif method != method_get() and method != method_head():
        headers[size_header()] = 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit of psf__requests-1142 nagini bundle.

SPEC SHAPE: The frozen spec pins the ENTIRE observable post-state of announce_body_size: exact value in each of the 3 branches (stream_len / body_len / 0), the discriminating presence-iff-payload-method condition in the bodyless case (clause 3), a whole-map FRAME (clause 4: no other key added/removed/mutated), and method-unchanged (clause 5). This is a tight, deep model with NO axioms.

### ATTACKS (all confirmed same-spec exit 0; verifications run concurrently in 3 batches, <=3 JVMs each):
- atk_1.py PREPATCH BUG (unconditional leading headers[size_header()]=0 then seek/body branches, no method guard). weakness cmd -> exit 2 NOT-A-COUNTEREXAMPLE (verification failed): spec senses the change via clause 3. prepatch_reproduced=true.
- atk_2.py partial-domain: drop method guard, always announce 0 in bodyless case. exit 2 (verify FAIL).
- atk_3.py boundary/off-by: bodyless payload-carrying method announces 1 instead of 0. exit 2 (verify FAIL).
- atk_4.py control-flow-effect: correct branches PLUS smuggles extra header headers[size_header()+1]=7 (frame clause 4 violation). exit 2 (verify FAIL) -> frame clause is load-bearing.
- atk_5.py ungrounded-oracle echo: logically-equivalent restructuring (if not seekable and not body_present: if payload: =0; elif seekable: =stream_len; else: =body_len). weakness cmd -> exit 0 CANDIDATE (shares spec AND verifies, 15.0s). PER PROTOCOL materialized its faithful refined patch (atk_5_patch.diff, mirrors the body-is-None-first control flow) and ran harness.run_resolve('psf__requests-1142', patch): RESOLVED=True, COMPLETED=True, flaky=False, attempts=1. F2P test_no_content_length PASS; all 5 P2P PASS. A verifying echo whose faithful patch RESOLVES is NOT a weakness (per 2026-08-06 G-PANEL-1 echo policy) -> does not break the spec.
- atk_6.py wrong value: seekable branch announces body_len instead of stream_len. exit 2 (verify FAIL).
- atk_7.py inverted method guard: bodyless GET/HEAD announces 0, others absent. exit 2 (verify FAIL).

No timeouts / infra errors in any run (grep for 'timed out|TIMED OUT|infra|inconclusive' over out_atk_*.txt returned nothing) -> all exit-2 results are GENUINE verification failures, not guillotines. Positive control (bundle model.py impl) verifies (bash scripts/nagini_verify.sh -> exit 0).

REFINEMENT AUDIT: refinement.md legs 1-7 are all R (type refinements: header-name<->int key token, method<->int token, str(n)<->int value, body observations lifted to params) and leg 8 is I (deletion of leading unconditional write reflected as absence of pre-branch write). NO kind-3 (unexpressible-changed-op) leg. NO A-legs: the changed operation (guarded body-size announcement + new method guard) is modeled DEEPLY in the impl region; mapping.md §3 confirms no @ContractOnly callee. The A-soundness trust point is vacuous. axiom_check.py runs the deep-model self-consistency oracle (gold-patched prepare_content_length vs model_spec decision table over 25 boundary + 50000 fuzz inputs) -> G-AX OK exit 0, incl. explicit bodyless-GET/HEAD-no-header and bodyless-payload-zero discriminators.

CONCLUSION: >=5 distinct wrong impls (partial-domain, boundary, control-flow-effect/frame, value-swap, guard-inversion) all fail verification; the only verifying candidate is a faithful echo whose materialized patch RESOLVES under the official harness. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for psf__requests-1142 nagini, modeling PreparedRequest.prepare_content_length at base_commit 22623bd8.

### Verification checks
1. Spec region byte-identical between model.py and model_prepatch.py (pre/post-conditions diff empty) — spec is frozen.
2. model.py verifies under pinned Nagini (Verification successful, 12.80s, exit 0).
3. Real base repo confirmed at commit 22623bd8...; gold patch is the standard diff (drop unconditional 'Content-Length'='0'; add `elif self.method not in ('GET','HEAD'): ...='0'`).

DIFFERENTIAL FAITHFULNESS (bundle's own conformance_check.py, adapted with py3.10 + stdlib shims for cgi/collections.MutableMapping since the vendored old requests predates their removal): shadow = verbatim impl region over model carriers; oracle = REAL patched requests.models.PreparedRequest.prepare_content_length. Result: G-CONF OK, 100077 inputs (77 boundary covering full decision table GET/HEAD/POST/PUT/DELETE x stream/non-stream/bodyless x 0/1/3 pre-seeded frame headers, + 100000 fuzz, seed 1142), ZERO disagreements.

CLAUSE-BY-CLAUSE the postcondition matches the real callee within its precondition domain:
- (1) seekable -> header == stream_len  <->  str(body.tell()) after seek(0,2)
- (2) non-stream body_present -> header == body_len  <->  str(len(body))
- (3) bodyless -> (header present iff method payload-carrying)  <->  `elif self.method not in ('GET','HEAD')` — the discriminating clause, exactly the gold behavior
- (4) whole-map frame: real function writes AT MOST 'Content-Length'; every other header survives — verified by the frame-header seeding in the differential
- (5) method unchanged: real function never mutates self.method

The precondition `size_header() not in headers` restricts to the fresh-request path (headers built fresh in prepare_headers, models.py:324-330). This narrows the observed domain but is a documented, justified scoping choice, not drift; within that domain no input makes the modeled function disagree with the real callee. No spec clause is stronger than the real behavior — no diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Reviewed the consumer spec view (spec_view over model.py, nagini backend) against the public problem_statement only (NOT hints_text). Mechanical G-LEAK screen passes with zero hard failures; independently re-run.

Checks confirmed absent from the spec view:
- Diff markers (@@, diff --git, +++, ---): none.
- Patched file path: 'models.py'/'requests/models.py' absent.
- Patched repo symbols: 'prepare_content_length', 'self.method', 'self.headers', 'super_len', 'seek(', '.tell' all absent. Spec-view identifiers (size_header, method_get, method_head, announce_body_size, headers, method, seekable, stream_len, body_present, body_len) are model tokens/abstractions, not repo symbols. _patch_changed_symbols yields {'prepare_body'} (section-header artifact), which does not appear in the view.
- Repo literals: 'Content-Length', 'GET', 'HEAD' all absent; behavior is carried by opaque integer tokens (size_header()=0, method_get()=1, method_head()=2). The only 'seek' substrings are the abstraction word 'seekable', not the repo's body.seek() call.
- Narration: no bug/fix/patch/regression narration in comments/docstrings. Docstring is explicitly framed 'as desired behaviour, not as an edit'.

Gold-reconstruction analysis beyond the lexical screen: the one behavioral fact going beyond the public problem_statement (which names only GET + content-length) is the exemption of the headers-only method (HEAD) alongside the retrieval method. It is stated functionally/abstractly ('the read-only retrieval method' / 'the headers-only method') via opaque tokens, never via the repo literal 'HEAD', the diff, the file path, or fix narration. A spec that fully constrains the intended behavior (consumer must supply a verifying impl) is by design and does not localize or quote the gold edit. This is legitimate behavioral specification, not gold-edit leakage.

Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
