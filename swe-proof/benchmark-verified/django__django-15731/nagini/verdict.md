# P2 adversarial audit — django__django-15731

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -84,10 +83,6 @@
 
 class Func:
     def __init__(self) -> None:
-        # Straight-line constructor: no loops, no calls. Level 1 sits strictly
-        # below every builder that constructs a Func, so the caller has room to
-        # discharge its own obligation across this call.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and Acc(self.doc))  # type: ignore
         Ensures(Acc(self.wrapped) and Acc(self.target_sig))  # type: ignore
         Ensures(Acc(self.sig))  # type: ignore
@@ -112,7 +107,6 @@
     # only at fractional permission.
     Requires(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
     Requires(Acc(source.sig, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The source callable is left exactly as it was, untouched.
@@ -153,14 +147,13 @@
     # post-conditions-end
     # impl-start
     proxy = Func()
-    # proxy's own forwarding parameter list (def manager_method(self, *args,
-    # **kwargs)) -- its own sig is the forwarding signature.
     proxy.sig = SIG_FORWARDING()
-    # functools.wraps(source): copy the introspectable metadata AND record the
-    # original callable the proxy stands in for (so the resolver follows it).
     proxy.name = source.name
     proxy.doc = source.doc
-    proxy.wrapped = True
-    proxy.target_sig = source.sig
+    # Conditional recording: only record when the source's own signature
+    # differs from the forwarding one (a sub-domain restriction).
+    if source.sig != SIG_FORWARDING():
+        proxy.wrapped = True
+        proxy.target_sig = source.sig
     return proxy
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -84,10 +83,6 @@
 
 class Func:
     def __init__(self) -> None:
-        # Straight-line constructor: no loops, no calls. Level 1 sits strictly
-        # below every builder that constructs a Func, so the caller has room to
-        # discharge its own obligation across this call.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and Acc(self.doc))  # type: ignore
         Ensures(Acc(self.wrapped) and Acc(self.target_sig))  # type: ignore
         Ensures(Acc(self.sig))  # type: ignore
@@ -112,7 +107,6 @@
     # only at fractional permission.
     Requires(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
     Requires(Acc(source.sig, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The source callable is left exactly as it was, untouched.
@@ -153,14 +147,10 @@
     # post-conditions-end
     # impl-start
     proxy = Func()
-    # proxy's own forwarding parameter list (def manager_method(self, *args,
-    # **kwargs)) -- its own sig is the forwarding signature.
     proxy.sig = SIG_FORWARDING()
-    # functools.wraps(source): copy the introspectable metadata AND record the
-    # original callable the proxy stands in for (so the resolver follows it).
     proxy.name = source.name
     proxy.doc = source.doc
     proxy.wrapped = True
-    proxy.target_sig = source.sig
+    proxy.target_sig = SIG_FORWARDING()
     return proxy
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -84,10 +83,6 @@
 
 class Func:
     def __init__(self) -> None:
-        # Straight-line constructor: no loops, no calls. Level 1 sits strictly
-        # below every builder that constructs a Func, so the caller has room to
-        # discharge its own obligation across this call.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and Acc(self.doc))  # type: ignore
         Ensures(Acc(self.wrapped) and Acc(self.target_sig))  # type: ignore
         Ensures(Acc(self.sig))  # type: ignore
@@ -112,7 +107,6 @@
     # only at fractional permission.
     Requires(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
     Requires(Acc(source.sig, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The source callable is left exactly as it was, untouched.
@@ -153,13 +147,9 @@
     # post-conditions-end
     # impl-start
     proxy = Func()
-    # proxy's own forwarding parameter list (def manager_method(self, *args,
-    # **kwargs)) -- its own sig is the forwarding signature.
     proxy.sig = SIG_FORWARDING()
-    # functools.wraps(source): copy the introspectable metadata AND record the
-    # original callable the proxy stands in for (so the resolver follows it).
-    proxy.name = source.name
-    proxy.doc = source.doc
+    proxy.name = source.doc
+    proxy.doc = source.name
     proxy.wrapped = True
     proxy.target_sig = source.sig
     return proxy
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -84,10 +83,6 @@
 
 class Func:
     def __init__(self) -> None:
-        # Straight-line constructor: no loops, no calls. Level 1 sits strictly
-        # below every builder that constructs a Func, so the caller has room to
-        # discharge its own obligation across this call.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and Acc(self.doc))  # type: ignore
         Ensures(Acc(self.wrapped) and Acc(self.target_sig))  # type: ignore
         Ensures(Acc(self.sig))  # type: ignore
@@ -112,7 +107,6 @@
     # only at fractional permission.
     Requires(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
     Requires(Acc(source.sig, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The source callable is left exactly as it was, untouched.
@@ -153,14 +147,10 @@
     # post-conditions-end
     # impl-start
     proxy = Func()
-    # proxy's own forwarding parameter list (def manager_method(self, *args,
-    # **kwargs)) -- its own sig is the forwarding signature.
-    proxy.sig = SIG_FORWARDING()
-    # functools.wraps(source): copy the introspectable metadata AND record the
-    # original callable the proxy stands in for (so the resolver follows it).
     proxy.name = source.name
     proxy.doc = source.doc
     proxy.wrapped = True
     proxy.target_sig = source.sig
+    proxy.sig = source.sig
     return proxy
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -84,10 +83,6 @@
 
 class Func:
     def __init__(self) -> None:
-        # Straight-line constructor: no loops, no calls. Level 1 sits strictly
-        # below every builder that constructs a Func, so the caller has room to
-        # discharge its own obligation across this call.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and Acc(self.doc))  # type: ignore
         Ensures(Acc(self.wrapped) and Acc(self.target_sig))  # type: ignore
         Ensures(Acc(self.sig))  # type: ignore
@@ -112,7 +107,6 @@
     # only at fractional permission.
     Requires(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
     Requires(Acc(source.sig, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The source callable is left exactly as it was, untouched.
@@ -153,12 +147,7 @@
     # post-conditions-end
     # impl-start
     proxy = Func()
-    # proxy's own forwarding parameter list (def manager_method(self, *args,
-    # **kwargs)) -- its own sig is the forwarding signature.
     proxy.sig = SIG_FORWARDING()
-    # functools.wraps(source): copy the introspectable metadata AND record the
-    # original callable the proxy stands in for (so the resolver follows it).
-    proxy.name = source.name
     proxy.doc = source.doc
     proxy.wrapped = True
     proxy.target_sig = source.sig
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -84,10 +83,6 @@
 
 class Func:
     def __init__(self) -> None:
-        # Straight-line constructor: no loops, no calls. Level 1 sits strictly
-        # below every builder that constructs a Func, so the caller has room to
-        # discharge its own obligation across this call.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and Acc(self.doc))  # type: ignore
         Ensures(Acc(self.wrapped) and Acc(self.target_sig))  # type: ignore
         Ensures(Acc(self.sig))  # type: ignore
@@ -112,7 +107,6 @@
     # only at fractional permission.
     Requires(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
     Requires(Acc(source.sig, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The source callable is left exactly as it was, untouched.
@@ -153,14 +147,9 @@
     # post-conditions-end
     # impl-start
     proxy = Func()
-    # proxy's own forwarding parameter list (def manager_method(self, *args,
-    # **kwargs)) -- its own sig is the forwarding signature.
-    proxy.sig = SIG_FORWARDING()
-    # functools.wraps(source): copy the introspectable metadata AND record the
-    # original callable the proxy stands in for (so the resolver follows it).
     proxy.name = source.name
     proxy.doc = source.doc
+    proxy.target_sig = source.sig
     proxy.wrapped = True
-    proxy.target_sig = source.sig
     return proxy
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # pure-start
@@ -84,10 +83,6 @@
 
 class Func:
     def __init__(self) -> None:
-        # Straight-line constructor: no loops, no calls. Level 1 sits strictly
-        # below every builder that constructs a Func, so the caller has room to
-        # discharge its own obligation across this call.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and Acc(self.doc))  # type: ignore
         Ensures(Acc(self.wrapped) and Acc(self.target_sig))  # type: ignore
         Ensures(Acc(self.sig))  # type: ignore
@@ -112,7 +107,6 @@
     # only at fractional permission.
     Requires(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
     Requires(Acc(source.sig, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # The source callable is left exactly as it was, untouched.
@@ -153,14 +147,10 @@
     # post-conditions-end
     # impl-start
     proxy = Func()
-    # proxy's own forwarding parameter list (def manager_method(self, *args,
-    # **kwargs)) -- its own sig is the forwarding signature.
-    proxy.sig = SIG_FORWARDING()
-    # functools.wraps(source): copy the introspectable metadata AND record the
-    # original callable the proxy stands in for (so the resolver follows it).
+    proxy.wrapped = True
+    proxy.target_sig = source.sig
     proxy.name = source.name
     proxy.doc = source.doc
-    proxy.wrapped = True
-    proxy.target_sig = source.sig
+    proxy.sig = SIG_FORWARDING()
     return proxy
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15731.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A proxy callable is built that forwards to a source callable. The proxy's
  observable metadata must agree with the source so that introspection of the
  proxy reports the SAME information introspection of the source would report.
  Two pieces of metadata are observed here:

    (1) the proxy's display name and documentation equal the source's, and

    (2) the parameter signature reported for the proxy equals the source's
        declared signature -- NOT the proxy's own forwarding signature (which
        merely captures arbitrary positional/keyword arguments and would
        otherwise be reported).

  Property (2) is what makes signature introspection report the source's true
  parameters. The standard signature resolver, when a callable records the
  ORIGINAL callable it stands in for, reports that original callable's
  signature instead of the forwarding one. So the proxy must record the source
  it stands in for; recording only name and documentation is insufficient,
  because the resolver then falls back to the proxy's own forwarding signature.

  The desired behaviour is pinned exactly, not merely up to the reported
  observable:

    (3) the proxy's OWN declared signature is the forwarding parameter list
        (the change does not touch the proxy's own parameter list), and

    (4) the proxy ALWAYS records the source it stands in for -- the recording
        is unconditional (not, e.g., applied only when the source's signature
        happens to differ from the forwarding one) -- and what it records is
        the source's own signature.

  Clauses (3)/(4) close the free fields a rival implementation could vary
  while still meeting (1)/(2): they pin every metadata field of the built
  proxy to the value the desired builder actually produces.

A callable's introspectable metadata is modelled as a minimal record exposing
only the touched fields: a display-name code, a documentation code, a flag
recording whether the callable stands in for an original callable, and the
recorded original's signature code. Names / docstrings / signatures are
modelled as integer codes (the tested behaviour observes only equality between
the proxy's reported metadata and the source's). The signature resolver
(`reported_signature`) is the unchanged standard introspection callee: it is
axiomatized and its `Ensures` is consumed by the proof; its soundness against
the real resolver is validated out-of-band (axiom_check.py / G-AX).

`SIG_FORWARDING` is the signature code of the proxy's own forwarding parameter
list; any genuine source whose own signature differs from it (every real
proxied method here) is reported wrongly unless the source is recorded.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# pure-start
@Pure
def SIG_FORWARDING() -> int:
    """The signature code of the proxy's own forwarding parameter list (the
    one that captures arbitrary positional and keyword arguments). Reported for
    a proxy that records no original callable to stand in for."""
    return 0
# pure-end


# axioms-start
@Pure
@ContractOnly
def reported_signature(wrapped: bool, target_sig: int) -> int:
    """The signature an introspection of a callable reports (the unchanged
    standard resolver). When the callable records an original callable it
    stands in for (`wrapped`), the recorded original's signature
    (`target_sig`) is reported; otherwise the callable's own forwarding
    signature is reported. Provenance + executable soundness validation:
    mapping.md / axiom_check.py."""
    Ensures(Implies(wrapped, Result() == target_sig))
    Ensures(Implies(not wrapped, Result() == SIG_FORWARDING()))
# axioms-end


class Func:
    def __init__(self) -> None:
        Ensures(Acc(self.name) and Acc(self.doc))  # type: ignore
        Ensures(Acc(self.wrapped) and Acc(self.target_sig))  # type: ignore
        Ensures(Acc(self.sig))  # type: ignore
        Ensures(self.name == 0 and self.doc == 0)  # type: ignore
        Ensures(self.wrapped == False and self.target_sig == 0)  # type: ignore
        Ensures(self.sig == SIG_FORWARDING())  # type: ignore
        # name / doc: introspectable identity strings (as integer codes)
        self.name = 0  # type: int
        self.doc = 0  # type: int
        # wrapped: whether this callable records an original it stands in for
        self.wrapped = False  # type: bool
        # target_sig: the recorded original's signature code (meaningful only
        # when `wrapped`)
        self.target_sig = 0  # type: int
        # sig: this callable's own declared signature code
        self.sig = SIG_FORWARDING()  # type: int


def build_proxy(source: Func) -> Func:
    # pre-conditions-start
    # The source callable is read-only: its metadata is required (and ensured)
    # only at fractional permission.
    Requires(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
    Requires(Acc(source.sig, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The source callable is left exactly as it was, untouched.
    Ensures(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
    Ensures(Acc(source.sig, 1 / 2))
    Ensures(source.name == Old(source.name))
    Ensures(source.doc == Old(source.doc))
    Ensures(source.sig == Old(source.sig))

    # The proxy is a fully-owned, distinct object.
    Ensures(Acc(Result().name) and Acc(Result().doc))
    Ensures(Acc(Result().wrapped) and Acc(Result().target_sig))
    Ensures(Acc(Result().sig))
    Ensures(Result() is not source)

    # (1) The proxy's display name and documentation equal the source's.
    Ensures(Result().name == source.name)
    Ensures(Result().doc == source.doc)

    # (2) The signature reported for the proxy equals the source's declared
    # signature -- the discriminating guarantee. It holds because the proxy
    # records the source it stands in for, so the resolver reports the source's
    # signature rather than the proxy's own forwarding signature.
    Ensures(reported_signature(Result().wrapped, Result().target_sig)
            == source.sig)

    # (3) The proxy's OWN declared signature is the forwarding parameter list:
    # the change decorates the proxy, it does not alter the proxy's own
    # parameter list (def manager_method(self, *args, **kwargs) is unchanged).
    Ensures(Result().sig == SIG_FORWARDING())

    # (4) The recording of the original is UNCONDITIONAL, and what is recorded
    # is the source's own signature. The builder always records the source it
    # stands in for -- never only on a sub-domain of sources (e.g. only when
    # the source's signature differs from the forwarding one).
    Ensures(Result().wrapped)
    Ensures(Result().target_sig == source.sig)
    # post-conditions-end
    # impl-start
    proxy = Func()
    # proxy's own forwarding parameter list (def manager_method(self, *args,
    # **kwargs)) -- its own sig is the forwarding signature.
    proxy.sig = SIG_FORWARDING()
    # functools.wraps(source): copy the introspectable metadata AND record the
    # original callable the proxy stands in for (so the resolver follows it).
    proxy.name = source.name
    proxy.doc = source.doc
    proxy.wrapped = True
    proxy.target_sig = source.sig
    return proxy
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 All commands run with the swebench-lean venv activated.

SPEC SHAPE: build_proxy's postconditions FULLY DETERMINE the returned Func's abstract state — name==source.name, doc==source.doc, wrapped==True (clause 4), target_sig==source.sig (clause 4), sig==SIG_FORWARDING() (clause 3), Result() is not source, and source left untouched at fractional permission. No metadata field is left free, so a verifying-but-behaviorally-wrong impl has no under-constrained field to exploit.

MACHINE RESULTS (all via `python -m swebench_unified.adversary weakness nagini django__django-15731 <file>`; verify via scripts/nagini_verify.sh; resolve via harness.run_resolve). Ran concurrently in batches of 3 (each Nagini check spawns JVM+Z3):
- positive_control.py (= model.py): VERIFIES, exit 0, 12.39s.
- atk_prepatch.py (= model_prepatch.py, omits A6 recording): NOT-A-COUNTEREXAMPLE, verification FAILS (exit 2) on postcondition (2) reported_signature(...)==source.sig. Prepatch bug reproduced.
- atk_1.py PARTIAL-DOMAIN (record source only when source.sig!=SIG_FORWARDING; violates unconditional clause 4): REJECTED exit 2.
- atk_2.py BOUNDARY/ungrounded-oracle-echo (wrapped=True but target_sig=SIG_FORWARDING() not source.sig): REJECTED exit 2 (fails clause 2 & 4b when source.sig!=forwarding).
- atk_3.py CONTROL-FLOW-EFFECT (swap name<->doc): REJECTED exit 2.
- atk_4.py (proxy.sig=source.sig, violates clause 3 own-sig==SIG_FORWARDING): REJECTED exit 2.
- atk_5.py (omit name copy, leaves default 0): REJECTED exit 2 (fails clause 1 name==source.name).
- atk_6.py EQUIVALENT reorder, drops redundant proxy.sig assignment (constructor already sets SIG_FORWARDING()): CANDIDATE, verifies 14.1s. Same abstract state as gold. Faithful refined patch = gold @wraps(method) patch. run_resolve -> RESOLVED=True, COMPLETED=True, note='resolved'.
- atk_7.py EQUIVALENT reorder + explicit redundant sig set: CANDIDATE, verifies 14.3s. Same abstract state as gold. Faithful refined patch = gold @wraps(method) patch (byte-identical to atk_6's; saved as faithful_atk_6_7.diff). run_resolve -> RESOLVED=True.

Both verifying candidates' materialized faithful patches RESOLVE under the official Docker harness, so verify does NOT imply incorrect here — no verify⇏correct break found.

REFINEMENT.MD AUDIT (A-legs + correspondence): A1-A5 R/I; A6 R (wrapped/target_sig <-> functools.wraps' __wrapped__, unconditional, pinned by clauses 3/4 postconditions); A7 A-CONSUMED (reported_signature <-> inspect.signature default follow_wrapped=True, weakest-obligation contract, both Ensures branches validated by axiom_check.py/G-AX over 11 boundary + 5000 fuzz param lists incl. exact bulk_create shape); A8 I. NO kind-3 legs. The A-consumed axiom's correspondence to the real callee (inspect.signature following __wrapped__ set by functools.wraps) is sound and G-AX-validated. mapping.md bindings to django/db/models/manager.py:83 create_method @ base_commit 93cedc82 are consistent with patch.diff.

VERDICT: SOUND. 7 same-spec wrong-impl/variant attacks run (5 correctly rejected, 2 equivalent candidates verify and their faithful gold patch RESOLVES); prepatch reproduced; positive control verifies; refinement.md legs all R/A/I with holding A-correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15731.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A proxy callable is built that forwards to a source callable. The proxy's
  observable metadata must agree with the source so that introspection of the
  proxy reports the SAME information introspection of the source would report.
  Two pieces of metadata are observed here:

    (1) the proxy's display name and documentation equal the source's, and

    (2) the parameter signature reported for the proxy equals the source's
        declared signature -- NOT the proxy's own forwarding signature (which
        merely captures arbitrary positional/keyword arguments and would
        otherwise be reported).

  Property (2) is what makes signature introspection report the source's true
  parameters. The standard signature resolver, when a callable records the
  ORIGINAL callable it stands in for, reports that original callable's
  signature instead of the forwarding one. So the proxy must record the source
  it stands in for; recording only name and documentation is insufficient,
  because the resolver then falls back to the proxy's own forwarding signature.

  The desired behaviour is pinned exactly, not merely up to the reported
  observable:

    (3) the proxy's OWN declared signature is the forwarding parameter list
        (the change does not touch the proxy's own parameter list), and

    (4) the proxy ALWAYS records the source it stands in for -- the recording
        is unconditional (not, e.g., applied only when the source's signature
        happens to differ from the forwarding one) -- and what it records is
        the source's own signature.

  Clauses (3)/(4) close the free fields a rival implementation could vary
  while still meeting (1)/(2): they pin every metadata field of the built
  proxy to the value the desired builder actually produces.

A callable's introspectable metadata is modelled as a minimal record exposing
only the touched fields: a display-name code, a documentation code, a flag
recording whether the callable stands in for an original callable, and the
recorded original's signature code. Names / docstrings / signatures are
modelled as integer codes (the tested behaviour observes only equality between
the proxy's reported metadata and the source's). The signature resolver
(`reported_signature`) is the unchanged standard introspection callee: it is
axiomatized and its `Ensures` is consumed by the proof; its soundness against
the real resolver is validated out-of-band (axiom_check.py / G-AX).

`SIG_FORWARDING` is the signature code of the proxy's own forwarding parameter
list; any genuine source whose own signature differs from it (every real
proxied method here) is reported wrongly unless the source is recorded.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# pure-start
@Pure
def SIG_FORWARDING() -> int:
    """The signature code of the proxy's own forwarding parameter list (the
    one that captures arbitrary positional and keyword arguments). Reported for
    a proxy that records no original callable to stand in for."""
    return 0
# pure-end


# axioms-start
@Pure
@ContractOnly
def reported_signature(wrapped: bool, target_sig: int) -> int:
    """The signature an introspection of a callable reports (the unchanged
    standard resolver). When the callable records an original callable it
    stands in for (`wrapped`), the recorded original's signature
    (`target_sig`) is reported; otherwise the callable's own forwarding
    signature is reported. Provenance + executable soundness validation:
    mapping.md / axiom_check.py."""
    Ensures(Implies(wrapped, Result() == target_sig))
    Ensures(Implies(not wrapped, Result() == SIG_FORWARDING()))
# axioms-end


class Func:
    def __init__(self) -> None:
        Ensures(Acc(self.name) and Acc(self.doc))  # type: ignore
        Ensures(Acc(self.wrapped) and Acc(self.target_sig))  # type: ignore
        Ensures(Acc(self.sig))  # type: ignore
        Ensures(self.name == 0 and self.doc == 0)  # type: ignore
        Ensures(self.wrapped == False and self.target_sig == 0)  # type: ignore
        Ensures(self.sig == SIG_FORWARDING())  # type: ignore
        # name / doc: introspectable identity strings (as integer codes)
        self.name = 0  # type: int
        self.doc = 0  # type: int
        # wrapped: whether this callable records an original it stands in for
        self.wrapped = False  # type: bool
        # target_sig: the recorded original's signature code (meaningful only
        # when `wrapped`)
        self.target_sig = 0  # type: int
        # sig: this callable's own declared signature code
        self.sig = SIG_FORWARDING()  # type: int


def build_proxy(source: Func) -> Func:
    # pre-conditions-start
    # The source callable is read-only: its metadata is required (and ensured)
    # only at fractional permission.
    Requires(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
    Requires(Acc(source.sig, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The source callable is left exactly as it was, untouched.
    Ensures(Acc(source.name, 1 / 2) and Acc(source.doc, 1 / 2))
    Ensures(Acc(source.sig, 1 / 2))
    Ensures(source.name == Old(source.name))
    Ensures(source.doc == Old(source.doc))
    Ensures(source.sig == Old(source.sig))

    # The proxy is a fully-owned, distinct object.
    Ensures(Acc(Result().name) and Acc(Result().doc))
    Ensures(Acc(Result().wrapped) and Acc(Result().target_sig))
    Ensures(Acc(Result().sig))
    Ensures(Result() is not source)

    # (1) The proxy's display name and documentation equal the source's.
    Ensures(Result().name == source.name)
    Ensures(Result().doc == source.doc)

    # (2) The signature reported for the proxy equals the source's declared
    # signature -- the discriminating guarantee. It holds because the proxy
    # records the source it stands in for, so the resolver reports the source's
    # signature rather than the proxy's own forwarding signature.
    Ensures(reported_signature(Result().wrapped, Result().target_sig)
            == source.sig)

    # (3) The proxy's OWN declared signature is the forwarding parameter list:
    # the change decorates the proxy, it does not alter the proxy's own
    # parameter list (def manager_method(self, *args, **kwargs) is unchanged).
    Ensures(Result().sig == SIG_FORWARDING())

    # (4) The recording of the original is UNCONDITIONAL, and what is recorded
    # is the source's own signature. The builder always records the source it
    # stands in for -- never only on a sub-domain of sources (e.g. only when
    # the source's signature differs from the forwarding one).
    Ensures(Result().wrapped)
    Ensures(Result().target_sig == source.sig)
    # post-conditions-end
    # impl-start
    proxy = Func()
    # proxy's own forwarding parameter list (def manager_method(self, *args,
    # **kwargs)) -- its own sig is the forwarding signature.
    proxy.sig = SIG_FORWARDING()
    # functools.wraps(source): copy the introspectable metadata AND record the
    # original callable the proxy stands in for (so the resolver follows it).
    proxy.name = source.name
    proxy.doc = source.doc
    proxy.wrapped = True
    proxy.target_sig = source.sig
    return proxy
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 All commands run with the swebench-lean venv activated.

SPEC SHAPE: build_proxy's postconditions FULLY DETERMINE the returned Func's abstract state — name==source.name, doc==source.doc, wrapped==True (clause 4), target_sig==source.sig (clause 4), sig==SIG_FORWARDING() (clause 3), Result() is not source, and source left untouched at fractional permission. No metadata field is left free, so a verifying-but-behaviorally-wrong impl has no under-constrained field to exploit.

MACHINE RESULTS (all via `python -m swebench_unified.adversary weakness nagini django__django-15731 <file>`; verify via scripts/nagini_verify.sh; resolve via harness.run_resolve). Ran concurrently in batches of 3 (each Nagini check spawns JVM+Z3):
- positive_control.py (= model.py): VERIFIES, exit 0, 12.39s.
- atk_prepatch.py (= model_prepatch.py, omits A6 recording): NOT-A-COUNTEREXAMPLE, verification FAILS (exit 2) on postcondition (2) reported_signature(...)==source.sig. Prepatch bug reproduced.
- atk_1.py PARTIAL-DOMAIN (record source only when source.sig!=SIG_FORWARDING; violates unconditional clause 4): REJECTED exit 2.
- atk_2.py BOUNDARY/ungrounded-oracle-echo (wrapped=True but target_sig=SIG_FORWARDING() not source.sig): REJECTED exit 2 (fails clause 2 & 4b when source.sig!=forwarding).
- atk_3.py CONTROL-FLOW-EFFECT (swap name<->doc): REJECTED exit 2.
- atk_4.py (proxy.sig=source.sig, violates clause 3 own-sig==SIG_FORWARDING): REJECTED exit 2.
- atk_5.py (omit name copy, leaves default 0): REJECTED exit 2 (fails clause 1 name==source.name).
- atk_6.py EQUIVALENT reorder, drops redundant proxy.sig assignment (constructor already sets SIG_FORWARDING()): CANDIDATE, verifies 14.1s. Same abstract state as gold. Faithful refined patch = gold @wraps(method) patch. run_resolve -> RESOLVED=True, COMPLETED=True, note='resolved'.
- atk_7.py EQUIVALENT reorder + explicit redundant sig set: CANDIDATE, verifies 14.3s. Same abstract state as gold. Faithful refined patch = gold @wraps(method) patch (byte-identical to atk_6's; saved as faithful_atk_6_7.diff). run_resolve -> RESOLVED=True.

Both verifying candidates' materialized faithful patches RESOLVE under the official Docker harness, so verify does NOT imply incorrect here — no verify⇏correct break found.

REFINEMENT.MD AUDIT (A-legs + correspondence): A1-A5 R/I; A6 R (wrapped/target_sig <-> functools.wraps' __wrapped__, unconditional, pinned by clauses 3/4 postconditions); A7 A-CONSUMED (reported_signature <-> inspect.signature default follow_wrapped=True, weakest-obligation contract, both Ensures branches validated by axiom_check.py/G-AX over 11 boundary + 5000 fuzz param lists incl. exact bulk_create shape); A8 I. NO kind-3 legs. The A-consumed axiom's correspondence to the real callee (inspect.signature following __wrapped__ set by functools.wraps) is sound and G-AX-validated. mapping.md bindings to django/db/models/manager.py:83 create_method @ base_commit 93cedc82 are consistent with patch.diff.

VERDICT: SOUND. 7 same-spec wrong-impl/variant attacks run (5 correctly rejected, 2 equivalent candidates verify and their faithful gold patch RESOLVES); prepatch reproduced; positive control verifies; refinement.md legs all R/A/I with holding A-correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-15731 nagini bundle. Modeled build_proxy(source:Func) mirrors the gold-patched inner builder create_method (django/db/models/manager.py:83); gold adds @wraps(method) and removes the manual __name__/__doc__ copies. Mechanical facts: same-spec exit 0 (attack==bundle spec, spec region byte-identical); G-AX axiom_check.py exit 0 over 11 boundary + 5000 fuzz param lists incl. exact bulk_create shape; model.py VERIFIES (exit 0, 10.63s); model_prepatch.py (omits A6 recording) FAILS postcondition (exit 1) => spec senses the change (G-DIFF), not vacuous.

Every postcondition checked against the real callees and found not-too-strong / no drift:
(1) name/doc equality <- @wraps copies __name__/__doc__ (WRAPPER_ASSIGNMENTS), unconditional. Faithful.
(2) reported_signature(wrapped,target_sig)==source.sig <- inspect.signature (default follow_wrapped=True) follows __wrapped__ set by wraps, reporting source's sig. Axiom encodes only the WEAKEST obligation (wrapped=>target_sig; not-wrapped=>SIG_FORWARDING), so it does not over-constrain the real resolver. Confirmed sound by G-AX.
(3) Result().sig==SIG_FORWARDING() <- manager_method(self,*args,**kwargs) own param list unchanged by patch. Faithful.
(4) Result().wrapped and target_sig==source.sig, UNCONDITIONAL <- @wraps applies to every proxied method, always sets __wrapped__=method; no sub-domain restriction that would make the spec stronger than the code. Faithful.
Source-untouched (fractional perms) + distinct-proxy clauses match wraps returning a fresh wrapper that reads but never writes the source.

Searched free-field candidates a rival could vary (sources whose own sig==SIG_FORWARDING, zero-arg, keyword-only, positional-only, var-args) - all exercised by G-AX boundary+fuzz; NO input where the modeled function disagrees with the real repo callee. Spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK passes (leakage.screen: PASSED=True, zero hard failures) — no diff markers, no reproduced gold lines, no patched file/module path, no narration terms in the spec view. Semantic review: the impl region (build_proxy body, including the `functools.wraps(source)` comment on model.py:150/153) is ELIDED in the spec view and is not consumer-visible. The only edit-adjacent token remaining in the spec view is line 138 in the post-conditions region: `# parameter list (def manager_method(self, *args, **kwargs) is unchanged)`, naming the repo-local symbol `manager_method` and the forwarding signature. This does NOT leak beyond the public problem_statement, which already fully discloses the gold edit: it cites django/db/models/manager.py L84, states name/docstring are assigned on lines 87/88, and explicitly says 'The fix is to use functools.wraps instead of manually assigning name and docstring' — both `functools` and `wraps` appear verbatim in the public problem_statement. The gold patch is precisely `@wraps(method)` replacing manual __name__/__doc__ assignment, which is entirely public. The spec models desired behavior abstractly (proxy/source, integer signature codes, reported_signature resolver) rather than the edit mechanics; `manager_method` is a non-distinctive local-function name (changed-symbol set is only {'check'}, and manager_method isn't even a def/class touched-symbol) that adds no reconstruction leverage over the already-precise public statement. Leakage judged beyond problem_statement (not hints_text): nothing extra is revealed. No relaxed_leakage flag / RELAXED_LEAKAGE.md present, so this is a strict-mode clean pass, not a deferral.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
