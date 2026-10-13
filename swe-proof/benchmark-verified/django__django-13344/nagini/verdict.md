# P2 adversarial audit — django__django-13344

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,12 +40,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Handler:
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
         Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
         Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
@@ -92,7 +90,6 @@
     Requires(Acc(handler.producer))
     Requires(Acc(handler.async_advertised))
     Requires(Acc(handler.absence_signalled))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -111,7 +108,6 @@
     else:
         handler.absence_signalled = False
     handler.producer = producer
-    handler.async_advertised = producer_is_async(producer)
     # impl-end
 
 
@@ -124,7 +120,6 @@
     Requires(Acc(handler.absence_signalled))
     Requires(Acc(handler.store_name))
     Requires(Acc(handler.store))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -150,11 +145,8 @@
     else:
         handler.absence_signalled = False
     handler.producer = producer
-    handler.async_advertised = producer_is_async(producer)
-    # Defaults established first (as super().__init__ -> base init does):
     handler.store_name = default_name
     handler.store = resolve_store(handler.store_name)
-    # An explicit override re-selects the name AND re-resolves the store from it:
     if override_name is not None:
         handler.store_name = override_name
         handler.store = resolve_store(handler.store_name)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,12 +40,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Handler:
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
         Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
         Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
@@ -92,7 +90,6 @@
     Requires(Acc(handler.producer))
     Requires(Acc(handler.async_advertised))
     Requires(Acc(handler.absence_signalled))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -110,8 +107,8 @@
         handler.absence_signalled = True
     else:
         handler.absence_signalled = False
+        handler.async_advertised = producer_is_async(producer)
     handler.producer = producer
-    handler.async_advertised = producer_is_async(producer)
     # impl-end
 
 
@@ -124,7 +121,6 @@
     Requires(Acc(handler.absence_signalled))
     Requires(Acc(handler.store_name))
     Requires(Acc(handler.store))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -150,13 +146,11 @@
     else:
         handler.absence_signalled = False
     handler.producer = producer
-    handler.async_advertised = producer_is_async(producer)
-    # Defaults established first (as super().__init__ -> base init does):
     handler.store_name = default_name
     handler.store = resolve_store(handler.store_name)
-    # An explicit override re-selects the name AND re-resolves the store from it:
     if override_name is not None:
         handler.store_name = override_name
         handler.store = resolve_store(handler.store_name)
+    handler.async_advertised = producer_is_async(producer)
     return handler.store
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,12 +40,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Handler:
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
         Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
         Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
@@ -92,7 +90,6 @@
     Requires(Acc(handler.producer))
     Requires(Acc(handler.async_advertised))
     Requires(Acc(handler.absence_signalled))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -111,7 +108,7 @@
     else:
         handler.absence_signalled = False
     handler.producer = producer
-    handler.async_advertised = producer_is_async(producer)
+    handler.async_advertised = False
     # impl-end
 
 
@@ -124,7 +121,6 @@
     Requires(Acc(handler.absence_signalled))
     Requires(Acc(handler.store_name))
     Requires(Acc(handler.store))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -150,13 +146,11 @@
     else:
         handler.absence_signalled = False
     handler.producer = producer
-    handler.async_advertised = producer_is_async(producer)
-    # Defaults established first (as super().__init__ -> base init does):
     handler.store_name = default_name
     handler.store = resolve_store(handler.store_name)
-    # An explicit override re-selects the name AND re-resolves the store from it:
     if override_name is not None:
         handler.store_name = override_name
         handler.store = resolve_store(handler.store_name)
+    handler.async_advertised = producer_is_async(producer)
     return handler.store
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,12 +40,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Handler:
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
         Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
         Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
@@ -92,7 +90,6 @@
     Requires(Acc(handler.producer))
     Requires(Acc(handler.async_advertised))
     Requires(Acc(handler.absence_signalled))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -107,9 +104,9 @@
     # post-conditions-end
     # impl-start
     if producer is None:
+        handler.absence_signalled = False
+    else:
         handler.absence_signalled = True
-    else:
-        handler.absence_signalled = False
     handler.producer = producer
     handler.async_advertised = producer_is_async(producer)
     # impl-end
@@ -124,7 +121,6 @@
     Requires(Acc(handler.absence_signalled))
     Requires(Acc(handler.store_name))
     Requires(Acc(handler.store))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -150,13 +146,11 @@
     else:
         handler.absence_signalled = False
     handler.producer = producer
-    handler.async_advertised = producer_is_async(producer)
-    # Defaults established first (as super().__init__ -> base init does):
     handler.store_name = default_name
     handler.store = resolve_store(handler.store_name)
-    # An explicit override re-selects the name AND re-resolves the store from it:
     if override_name is not None:
         handler.store_name = override_name
         handler.store = resolve_store(handler.store_name)
+    handler.async_advertised = producer_is_async(producer)
     return handler.store
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,12 +40,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Handler:
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
         Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
         Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
@@ -92,7 +90,6 @@
     Requires(Acc(handler.producer))
     Requires(Acc(handler.async_advertised))
     Requires(Acc(handler.absence_signalled))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -124,7 +121,6 @@
     Requires(Acc(handler.absence_signalled))
     Requires(Acc(handler.store_name))
     Requires(Acc(handler.store))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -150,13 +146,11 @@
     else:
         handler.absence_signalled = False
     handler.producer = producer
-    handler.async_advertised = producer_is_async(producer)
-    # Defaults established first (as super().__init__ -> base init does):
     handler.store_name = default_name
     handler.store = resolve_store(handler.store_name)
-    # An explicit override re-selects the name AND re-resolves the store from it:
     if override_name is not None:
         handler.store_name = override_name
         handler.store = resolve_store(handler.store_name)
+    handler.async_advertised = True
     return handler.store
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,12 +40,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Handler:
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
         Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
         Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
@@ -92,7 +90,6 @@
     Requires(Acc(handler.producer))
     Requires(Acc(handler.async_advertised))
     Requires(Acc(handler.absence_signalled))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -124,7 +121,6 @@
     Requires(Acc(handler.absence_signalled))
     Requires(Acc(handler.store_name))
     Requires(Acc(handler.store))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -150,13 +146,10 @@
     else:
         handler.absence_signalled = False
     handler.producer = producer
-    handler.async_advertised = producer_is_async(producer)
-    # Defaults established first (as super().__init__ -> base init does):
     handler.store_name = default_name
     handler.store = resolve_store(handler.store_name)
-    # An explicit override re-selects the name AND re-resolves the store from it:
     if override_name is not None:
         handler.store_name = override_name
-        handler.store = resolve_store(handler.store_name)
+    handler.async_advertised = producer_is_async(producer)
     return handler.store
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -40,12 +40,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Handler:
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
         Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
         Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
@@ -92,7 +90,6 @@
     Requires(Acc(handler.producer))
     Requires(Acc(handler.async_advertised))
     Requires(Acc(handler.absence_signalled))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -106,10 +103,7 @@
     Ensures(handler.async_advertised == producer_is_async(producer))
     # post-conditions-end
     # impl-start
-    if producer is None:
-        handler.absence_signalled = True
-    else:
-        handler.absence_signalled = False
+    handler.absence_signalled = (producer is None)
     handler.producer = producer
     handler.async_advertised = producer_is_async(producer)
     # impl-end
@@ -124,7 +118,6 @@
     Requires(Acc(handler.absence_signalled))
     Requires(Acc(handler.store_name))
     Requires(Acc(handler.store))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -145,18 +138,13 @@
     Ensures(Result() == handler.store)
     # post-conditions-end
     # impl-start
-    if producer is None:
-        handler.absence_signalled = True
-    else:
-        handler.absence_signalled = False
+    handler.absence_signalled = (producer is None)
     handler.producer = producer
     handler.async_advertised = producer_is_async(producer)
-    # Defaults established first (as super().__init__ -> base init does):
-    handler.store_name = default_name
-    handler.store = resolve_store(handler.store_name)
-    # An explicit override re-selects the name AND re-resolves the store from it:
     if override_name is not None:
         handler.store_name = override_name
-        handler.store = resolve_store(handler.store_name)
+    else:
+        handler.store_name = default_name
+    handler.store = resolve_store(handler.store_name)
     return handler.store
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,12 +40,10 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Handler:
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
         Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
         Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
@@ -92,7 +90,6 @@
     Requires(Acc(handler.producer))
     Requires(Acc(handler.async_advertised))
     Requires(Acc(handler.absence_signalled))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -124,7 +121,6 @@
     Requires(Acc(handler.absence_signalled))
     Requires(Acc(handler.store_name))
     Requires(Acc(handler.store))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(handler.producer))
@@ -150,13 +146,11 @@
     else:
         handler.absence_signalled = False
     handler.producer = producer
-    handler.async_advertised = producer_is_async(producer)
-    # Defaults established first (as super().__init__ -> base init does):
     handler.store_name = default_name
     handler.store = resolve_store(handler.store_name)
-    # An explicit override re-selects the name AND re-resolves the store from it:
     if override_name is not None:
         handler.store_name = override_name
         handler.store = resolve_store(handler.store_name)
-    return handler.store
+    handler.async_advertised = producer_is_async(producer)
+    return resolve_store(default_name)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13344.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A class-based request/response handler is configured at construction from a
  single supplied response-producer. Configuration MUST establish three
  observable facts about the constructed handler, for EVERY such handler kind:

    (1) the absence of a supplied producer is reported through the legacy
        configuration-time signal: that signal fires exactly when the supplied
        producer is the absent value, and not otherwise;

    (2) the supplied producer is retained on the handler so the handler can
        later invoke it;

    (3) the handler advertises the *same* asynchronous capability as its
        supplied producer: the handler is recognised as asynchronous exactly
        when the supplied producer is itself asynchronous, and as synchronous
        otherwise. This is what lets a downstream consumer in a chain receive a
        materialised result rather than an unresolved asynchronous placeholder.

  A handler variant that additionally selects a backing store by name must,
  beyond the three facts above, keep its selected store CONSISTENT with the
  selected name: the resolved store is always the store that the currently
  selected name designates, whether that name is the configured default or an
  explicit override supplied at construction. Overriding the name re-resolves
  the store from the new name; leaving it as the default keeps the
  default-resolved store. (This is the observable invariant a constructor of
  such a variant must maintain across the default, explicit-default, and
  explicit-custom construction paths.)

The supplied producer is modelled by an opaque token (``Optional[int]``; the
absent value is ``None``). Whether a given producer is asynchronous is decided
by an unchanged runtime predicate, axiomatized as a pure deterministic callee.
The store-name -> store resolution is likewise an unchanged registry lookup,
axiomatized as a pure deterministic callee. The handler is a minimal class
carrying only the touched fields.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

class Handler:
    def __init__(self) -> None:
        Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
        Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
        Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
        Ensures(Acc(self.store_name) and self.store_name == 0)  # type: ignore
        Ensures(Acc(self.store) and self.store == 0)  # type: ignore
        self.producer = None  # type: Optional[int]
        self.async_advertised = False  # type: bool
        self.absence_signalled = False  # type: bool
        self.store_name = 0  # type: int
        self.store = 0  # type: int

# axioms-start
@Pure
@ContractOnly
def producer_is_async(producer: Optional[int]) -> bool:
    """Unchanged runtime predicate deciding whether a supplied producer is an
    asynchronous producer (the coroutine-function test). Deterministic in the
    producer token; the absent producer is not asynchronous. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(producer is None, Result() is False))

@Pure
@ContractOnly
def resolve_store(store_name: int) -> int:
    """Unchanged registry lookup resolving a store-name token to its store
    token. Deterministic in the name (it is a plain mapping read); two distinct
    names need not resolve to distinct stores, but the same name always
    resolves to the same store. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def configure_handler(handler: Handler, producer: Optional[int]) -> None:
    # pre-conditions-start
    Requires(Acc(handler.producer))
    Requires(Acc(handler.async_advertised))
    Requires(Acc(handler.absence_signalled))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(handler.producer))
    Ensures(Acc(handler.async_advertised))
    Ensures(Acc(handler.absence_signalled))
    # (2) the supplied producer is retained.
    Ensures(handler.producer is producer)
    # (1) the absence signal fires exactly when the producer is the absent value.
    Ensures(handler.absence_signalled == (producer is None))
    # (3) the handler advertises async exactly when the producer is async.
    Ensures(handler.async_advertised == producer_is_async(producer))
    # post-conditions-end
    # impl-start
    if producer is None:
        handler.absence_signalled = True
    else:
        handler.absence_signalled = False
    handler.producer = producer
    handler.async_advertised = producer_is_async(producer)
    # impl-end

def configure_settings_handler(handler: Handler, producer: Optional[int],
                               default_name: int,
                               override_name: Optional[int]) -> int:
    # pre-conditions-start
    Requires(Acc(handler.producer))
    Requires(Acc(handler.async_advertised))
    Requires(Acc(handler.absence_signalled))
    Requires(Acc(handler.store_name))
    Requires(Acc(handler.store))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(handler.producer))
    Ensures(Acc(handler.async_advertised))
    Ensures(Acc(handler.absence_signalled))
    Ensures(Acc(handler.store_name))
    Ensures(Acc(handler.store))
    # The shared three facts hold for a store-selecting handler too.
    Ensures(handler.producer is producer)
    Ensures(handler.absence_signalled == (producer is None))
    Ensures(handler.async_advertised == producer_is_async(producer))
    # The selected name is the override when one is supplied, else the default.
    Ensures(handler.store_name == (override_name if override_name is not None else default_name))
    # The load-bearing invariant: the resolved store is ALWAYS the store the
    # selected name designates -- on every construction path.
    Ensures(handler.store == resolve_store(handler.store_name))
    # The configured store is reported back to the caller.
    Ensures(Result() == handler.store)
    # post-conditions-end
    # impl-start
    if producer is None:
        handler.absence_signalled = True
    else:
        handler.absence_signalled = False
    handler.producer = producer
    handler.async_advertised = producer_is_async(producer)
    # Defaults established first (as super().__init__ -> base init does):
    handler.store_name = default_name
    handler.store = resolve_store(handler.store_name)
    # An explicit override re-selects the name AND re-resolves the store from it:
    if override_name is not None:
        handler.store_name = override_name
        handler.store = resolve_store(handler.store_name)
    return handler.store
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-13344 (nagini). adversary run under python from project root. 8 same-spec attacks encoded (all pass `adversary same-spec` exit 0). Results: atk_1 PREPATCH bug (omit async_advertised in BOTH funcs) -> NOT-A-COUNTEREXAMPLE (does not verify, exit 2) => prepatch reproduced. atk_2 partial-domain (async set only in non-None branch) -> rejected. atk_3 boundary/wrong-constant (async_advertised=False) -> rejected. atk_4 control-flow-effect (inverted absence signal) -> rejected. atk_5 ungrounded-oracle echo (async_advertised=True) -> rejected. atk_6 store-inconsistency (skip re-resolve of store after override_name) -> rejected. atk_8 wrong Result (return resolve_store(default_name) instead of final store) -> rejected. atk_7 legitimate echo (identical modeled facts via different control flow: absence_signalled=(producer is None); store re-resolved from final store_name on both paths) -> CANDIDATE (exit 0: shares spec AND verifies, 13s).

Positive control = bundle model.py verbatim -> verifies (Verification successful, 13.0s). Per protocol, atk_7's faithful refined patch materialized = the gold delegation patch (super().__init__ + cache restructure; behaviorally identical to atk_7 on every modeled facet) and RUN through the official harness: run_resolve('django__django-13344', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, note='resolved' (run_id sbu-resolve-...-3f06afe996-p3292568, patch sha1 3f06afe99662...). So the single verifying candidate is NOT a weakness (verify AND resolve agree).

The spec postconditions fully pin all five modeled fields + Result, leaving no behavioral slack for a wrong impl to verify. refinement.md leg-kind audit: all legs are R / A-consumed / A-reference / I (A1 R, A2 R, A3 A-reference, A4 I, A5 A-consumed+A-reference; B1 A-reference+A-consumed+I, B2 R+A-consumed, B3 R+A-consumed, B4 I) -- NO kind-3. A-legs' correspondence holds: producer_is_async <-> asyncio.iscoroutinefunction (A-consumed: None->False, determinism) and resolve_store <-> caches[alias] (A-consumed: determinism), both validated by axiom_check.py (G-AX) which also reproduces the super().__init__ marker mechanism (A-reference) and the CacheMiddleware store-selection control flow (A-reference). Verdict: SOUND -- >=5 distinct wrong impls run and rejected, the lone verifying candidate's faithful patch resolves.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

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

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13344.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A class-based request/response handler is configured at construction from a
  single supplied response-producer. Configuration MUST establish three
  observable facts about the constructed handler, for EVERY such handler kind:

    (1) the absence of a supplied producer is reported through the legacy
        configuration-time signal: that signal fires exactly when the supplied
        producer is the absent value, and not otherwise;

    (2) the supplied producer is retained on the handler so the handler can
        later invoke it;

    (3) the handler advertises the *same* asynchronous capability as its
        supplied producer: the handler is recognised as asynchronous exactly
        when the supplied producer is itself asynchronous, and as synchronous
        otherwise. This is what lets a downstream consumer in a chain receive a
        materialised result rather than an unresolved asynchronous placeholder.

  A handler variant that additionally selects a backing store by name must,
  beyond the three facts above, keep its selected store CONSISTENT with the
  selected name: the resolved store is always the store that the currently
  selected name designates, whether that name is the configured default or an
  explicit override supplied at construction. Overriding the name re-resolves
  the store from the new name; leaving it as the default keeps the
  default-resolved store. (This is the observable invariant a constructor of
  such a variant must maintain across the default, explicit-default, and
  explicit-custom construction paths.)

The supplied producer is modelled by an opaque token (``Optional[int]``; the
absent value is ``None``). Whether a given producer is asynchronous is decided
by an unchanged runtime predicate, axiomatized as a pure deterministic callee.
The store-name -> store resolution is likewise an unchanged registry lookup,
axiomatized as a pure deterministic callee. The handler is a minimal class
carrying only the touched fields.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

class Handler:
    def __init__(self) -> None:
        Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
        Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
        Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
        Ensures(Acc(self.store_name) and self.store_name == 0)  # type: ignore
        Ensures(Acc(self.store) and self.store == 0)  # type: ignore
        self.producer = None  # type: Optional[int]
        self.async_advertised = False  # type: bool
        self.absence_signalled = False  # type: bool
        self.store_name = 0  # type: int
        self.store = 0  # type: int

# axioms-start
@Pure
@ContractOnly
def producer_is_async(producer: Optional[int]) -> bool:
    """Unchanged runtime predicate deciding whether a supplied producer is an
    asynchronous producer (the coroutine-function test). Deterministic in the
    producer token; the absent producer is not asynchronous. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(producer is None, Result() is False))

@Pure
@ContractOnly
def resolve_store(store_name: int) -> int:
    """Unchanged registry lookup resolving a store-name token to its store
    token. Deterministic in the name (it is a plain mapping read); two distinct
    names need not resolve to distinct stores, but the same name always
    resolves to the same store. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def configure_handler(handler: Handler, producer: Optional[int]) -> None:
    # pre-conditions-start
    Requires(Acc(handler.producer))
    Requires(Acc(handler.async_advertised))
    Requires(Acc(handler.absence_signalled))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(handler.producer))
    Ensures(Acc(handler.async_advertised))
    Ensures(Acc(handler.absence_signalled))
    # (2) the supplied producer is retained.
    Ensures(handler.producer is producer)
    # (1) the absence signal fires exactly when the producer is the absent value.
    Ensures(handler.absence_signalled == (producer is None))
    # (3) the handler advertises async exactly when the producer is async.
    Ensures(handler.async_advertised == producer_is_async(producer))
    # post-conditions-end
    # impl-start
    if producer is None:
        handler.absence_signalled = True
    else:
        handler.absence_signalled = False
    handler.producer = producer
    handler.async_advertised = producer_is_async(producer)
    # impl-end

def configure_settings_handler(handler: Handler, producer: Optional[int],
                               default_name: int,
                               override_name: Optional[int]) -> int:
    # pre-conditions-start
    Requires(Acc(handler.producer))
    Requires(Acc(handler.async_advertised))
    Requires(Acc(handler.absence_signalled))
    Requires(Acc(handler.store_name))
    Requires(Acc(handler.store))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(handler.producer))
    Ensures(Acc(handler.async_advertised))
    Ensures(Acc(handler.absence_signalled))
    Ensures(Acc(handler.store_name))
    Ensures(Acc(handler.store))
    # The shared three facts hold for a store-selecting handler too.
    Ensures(handler.producer is producer)
    Ensures(handler.absence_signalled == (producer is None))
    Ensures(handler.async_advertised == producer_is_async(producer))
    # The selected name is the override when one is supplied, else the default.
    Ensures(handler.store_name == (override_name if override_name is not None else default_name))
    # The load-bearing invariant: the resolved store is ALWAYS the store the
    # selected name designates -- on every construction path.
    Ensures(handler.store == resolve_store(handler.store_name))
    # The configured store is reported back to the caller.
    Ensures(Result() == handler.store)
    # post-conditions-end
    # impl-start
    if producer is None:
        handler.absence_signalled = True
    else:
        handler.absence_signalled = False
    handler.producer = producer
    handler.async_advertised = producer_is_async(producer)
    # Defaults established first (as super().__init__ -> base init does):
    handler.store_name = default_name
    handler.store = resolve_store(handler.store_name)
    # An explicit override re-selects the name AND re-resolves the store from it:
    if override_name is not None:
        handler.store_name = override_name
        handler.store = resolve_store(handler.store_name)
    return handler.store
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-13344 (nagini). adversary run under python from project root. 8 same-spec attacks encoded (all pass `adversary same-spec` exit 0). Results: atk_1 PREPATCH bug (omit async_advertised in BOTH funcs) -> NOT-A-COUNTEREXAMPLE (does not verify, exit 2) => prepatch reproduced. atk_2 partial-domain (async set only in non-None branch) -> rejected. atk_3 boundary/wrong-constant (async_advertised=False) -> rejected. atk_4 control-flow-effect (inverted absence signal) -> rejected. atk_5 ungrounded-oracle echo (async_advertised=True) -> rejected. atk_6 store-inconsistency (skip re-resolve of store after override_name) -> rejected. atk_8 wrong Result (return resolve_store(default_name) instead of final store) -> rejected. atk_7 legitimate echo (identical modeled facts via different control flow: absence_signalled=(producer is None); store re-resolved from final store_name on both paths) -> CANDIDATE (exit 0: shares spec AND verifies, 13s).

Positive control = bundle model.py verbatim -> verifies (Verification successful, 13.0s). Per protocol, atk_7's faithful refined patch materialized = the gold delegation patch (super().__init__ + cache restructure; behaviorally identical to atk_7 on every modeled facet) and RUN through the official harness: run_resolve('django__django-13344', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, note='resolved' (run_id sbu-resolve-...-3f06afe996-p3292568, patch sha1 3f06afe99662...). So the single verifying candidate is NOT a weakness (verify AND resolve agree).

The spec postconditions fully pin all five modeled fields + Result, leaving no behavioral slack for a wrong impl to verify. refinement.md leg-kind audit: all legs are R / A-consumed / A-reference / I (A1 R, A2 R, A3 A-reference, A4 I, A5 A-consumed+A-reference; B1 A-reference+A-consumed+I, B2 R+A-consumed, B3 R+A-consumed, B4 I) -- NO kind-3. A-legs' correspondence holds: producer_is_async <-> asyncio.iscoroutinefunction (A-consumed: None->False, determinism) and resolve_store <-> caches[alias] (A-consumed: determinism), both validated by axiom_check.py (G-AX) which also reproduces the super().__init__ marker mechanism (A-reference) and the CacheMiddleware store-selection control flow (A-reference). Verdict: SOUND -- >=5 distinct wrong impls run and rejected, the lone verifying candidate's faithful patch resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-13344 nagini bundle. Independently rebuilt the real patched repo at base_commit e39e727d and applied the gold patch cleanly. Ran the bundle's conformance_check.py (a direct contract-stripped shadow of the model's impl region, with the two @ContractOnly callees bridged into the REAL asyncio.iscoroutinefunction and django.core.cache.caches[...]) against the REAL patched constructors (SecurityMiddleware, SessionMiddleware, UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware): 100120 inputs (120 boundary + 100000 fuzz, seed 133440), 0 disagreements. G-AX (axiom_check.py) passes: producer_is_async (None->False, determinism, exact match vs asyncio.iscoroutinefunction), the config deep model (stored/signalled/advertised triple == real super().__init__ marker mechanism), resolve_store determinism, and the store-selection invariant store==resolve_store(store_name) across default/explicit-default/explicit-custom/explicit-None paths on 9 boundary + 4000 fuzz tokens. Nagini verifies model.py (10.5s). Spec postconditions cover only the touched field-coupled facets (producer retention; absence_signalled == (producer is None); async_advertised == producer_is_async(producer); store_name/store selection invariant). Incidental scalar settings (cache_timeout, page_timeout, key_prefix) the gold cache hunk restructures are explicitly OUT of model scope (enforced by G-RESOLVE), so the spec cannot over-claim on them. The one field-coupled invariant a wrong refinement could break (cache == caches[cache_alias]) is modeled deeply and matches the real patched code on every path tested. No input found on which the modeled functions disagree with the real patched callees. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures): no diff markers, no patched file paths, no repo-symbol echoes, no bug/fix narration in spec-view comments. Spec region confirmed byte-identical via markers/same-spec projection.

Semantic review: the spec view abstracts every gold-edit specific behind opaque tokens (handler/producer/store/store_name). None of the concrete gold-patch elements — super().__init__(get_response), _async_check(), MiddlewareMixin, the five subclass __init__ sites, caches[...]/cache_alias, _get_response_none_deprecation — appear in any form.

The one discriminating fact (fact 3: 'handler advertises the same asynchronous capability as its supplied producer ... lets a downstream consumer in a chain receive a materialised result rather than an unresolved asynchronous placeholder') is a faithful desired-behaviour restatement of exactly what the PUBLIC problem_statement already discloses (ASGI async: the first middleware in the chain receives a coroutine instead of an HttpResponse). It adds no localization beyond the public statement. The store-consistency invariant (store == resolve_store(store_name)) is a non-discriminating property that held both pre- and post-patch per refinement.md, phrased generically over tokens; it does not point at the edit. A solver could not reconstruct the concrete super().__init__ delegation edit or its sites from the spec view — only the already-public async behaviour. Leakage judged against problem_statement only (not hints_text).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `refinement.md`, which ships in this bundle, so a reader can start there.
