# P2 adversarial audit — django__django-13516

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

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
@@ -74,7 +74,7 @@
     # pure-end
 
     def __init__(self) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
         self.drained = 0  # type: int
         Fold(self.drain_count_pred())
@@ -84,7 +84,7 @@
         # that it ran (the invocation count advances by one). This is the ONLY
         # operation that may advance the count. It is bounded work: it promises
         # termination to its callers.
-        Requires(MustTerminate(2))
+        Requires(MustTerminate(1))
         Requires(self.drain_count_pred())
         Ensures(self.drain_count_pred())
         Ensures(self.get_drained() == Old(self.get_drained()) + 1)
@@ -99,7 +99,7 @@
     the underlying stream supports draining."""
 
     def __init__(self, out: Sink, out_can_drain: bool) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Requires(Acc(out.drain_count_pred(), 1 / 2))
         Ensures(Acc(self.out) and self.out is out)  # type: ignore
         Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
@@ -119,7 +119,7 @@
     # Draining the wrapper is bounded work (at most one forwarded invocation),
     # so it must TERMINATE: without this obligation the postconditions could be
     # discharged vacuously by a body that never returns.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(stream.out, 1 / 2))
@@ -139,6 +139,5 @@
                     stream.out.get_drained() == Old(stream.out.get_drained())))
     # post-conditions-end
     # impl-start
-    if stream.out_can_drain:
-        stream.out.do_drain()
+    pass
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
     # pure-end
 
     def __init__(self) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
         self.drained = 0  # type: int
         Fold(self.drain_count_pred())
@@ -84,7 +84,7 @@
         # that it ran (the invocation count advances by one). This is the ONLY
         # operation that may advance the count. It is bounded work: it promises
         # termination to its callers.
-        Requires(MustTerminate(2))
+        Requires(MustTerminate(1))
         Requires(self.drain_count_pred())
         Ensures(self.drain_count_pred())
         Ensures(self.get_drained() == Old(self.get_drained()) + 1)
@@ -99,7 +99,7 @@
     the underlying stream supports draining."""
 
     def __init__(self, out: Sink, out_can_drain: bool) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Requires(Acc(out.drain_count_pred(), 1 / 2))
         Ensures(Acc(self.out) and self.out is out)  # type: ignore
         Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
@@ -119,7 +119,7 @@
     # Draining the wrapper is bounded work (at most one forwarded invocation),
     # so it must TERMINATE: without this obligation the postconditions could be
     # discharged vacuously by a body that never returns.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(stream.out, 1 / 2))
@@ -141,4 +141,5 @@
     # impl-start
     if stream.out_can_drain:
         stream.out.do_drain()
+        stream.out.do_drain()
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
     # pure-end
 
     def __init__(self) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
         self.drained = 0  # type: int
         Fold(self.drain_count_pred())
@@ -84,7 +84,7 @@
         # that it ran (the invocation count advances by one). This is the ONLY
         # operation that may advance the count. It is bounded work: it promises
         # termination to its callers.
-        Requires(MustTerminate(2))
+        Requires(MustTerminate(1))
         Requires(self.drain_count_pred())
         Ensures(self.drain_count_pred())
         Ensures(self.get_drained() == Old(self.get_drained()) + 1)
@@ -99,7 +99,7 @@
     the underlying stream supports draining."""
 
     def __init__(self, out: Sink, out_can_drain: bool) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Requires(Acc(out.drain_count_pred(), 1 / 2))
         Ensures(Acc(self.out) and self.out is out)  # type: ignore
         Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
@@ -119,7 +119,7 @@
     # Draining the wrapper is bounded work (at most one forwarded invocation),
     # so it must TERMINATE: without this obligation the postconditions could be
     # discharged vacuously by a body that never returns.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(stream.out, 1 / 2))
@@ -139,6 +139,5 @@
                     stream.out.get_drained() == Old(stream.out.get_drained())))
     # post-conditions-end
     # impl-start
-    if stream.out_can_drain:
-        stream.out.do_drain()
+    stream.out.do_drain()
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
     # pure-end
 
     def __init__(self) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
         self.drained = 0  # type: int
         Fold(self.drain_count_pred())
@@ -84,7 +84,7 @@
         # that it ran (the invocation count advances by one). This is the ONLY
         # operation that may advance the count. It is bounded work: it promises
         # termination to its callers.
-        Requires(MustTerminate(2))
+        Requires(MustTerminate(1))
         Requires(self.drain_count_pred())
         Ensures(self.drain_count_pred())
         Ensures(self.get_drained() == Old(self.get_drained()) + 1)
@@ -99,7 +99,7 @@
     the underlying stream supports draining."""
 
     def __init__(self, out: Sink, out_can_drain: bool) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Requires(Acc(out.drain_count_pred(), 1 / 2))
         Ensures(Acc(self.out) and self.out is out)  # type: ignore
         Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
@@ -119,7 +119,7 @@
     # Draining the wrapper is bounded work (at most one forwarded invocation),
     # so it must TERMINATE: without this obligation the postconditions could be
     # discharged vacuously by a body that never returns.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(stream.out, 1 / 2))
@@ -139,6 +139,6 @@
                     stream.out.get_drained() == Old(stream.out.get_drained())))
     # post-conditions-end
     # impl-start
-    if stream.out_can_drain:
+    if not stream.out_can_drain:
         stream.out.do_drain()
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
     # pure-end
 
     def __init__(self) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
         self.drained = 0  # type: int
         Fold(self.drain_count_pred())
@@ -84,7 +84,7 @@
         # that it ran (the invocation count advances by one). This is the ONLY
         # operation that may advance the count. It is bounded work: it promises
         # termination to its callers.
-        Requires(MustTerminate(2))
+        Requires(MustTerminate(1))
         Requires(self.drain_count_pred())
         Ensures(self.drain_count_pred())
         Ensures(self.get_drained() == Old(self.get_drained()) + 1)
@@ -99,7 +99,7 @@
     the underlying stream supports draining."""
 
     def __init__(self, out: Sink, out_can_drain: bool) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Requires(Acc(out.drain_count_pred(), 1 / 2))
         Ensures(Acc(self.out) and self.out is out)  # type: ignore
         Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
@@ -119,7 +119,7 @@
     # Draining the wrapper is bounded work (at most one forwarded invocation),
     # so it must TERMINATE: without this obligation the postconditions could be
     # discharged vacuously by a body that never returns.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(stream.out, 1 / 2))
@@ -139,6 +139,6 @@
                     stream.out.get_drained() == Old(stream.out.get_drained())))
     # post-conditions-end
     # impl-start
-    if stream.out_can_drain:
-        stream.out.do_drain()
+    while True:
+        Invariant(True)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
     # pure-end
 
     def __init__(self) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
         self.drained = 0  # type: int
         Fold(self.drain_count_pred())
@@ -84,7 +84,7 @@
         # that it ran (the invocation count advances by one). This is the ONLY
         # operation that may advance the count. It is bounded work: it promises
         # termination to its callers.
-        Requires(MustTerminate(2))
+        Requires(MustTerminate(1))
         Requires(self.drain_count_pred())
         Ensures(self.drain_count_pred())
         Ensures(self.get_drained() == Old(self.get_drained()) + 1)
@@ -99,7 +99,7 @@
     the underlying stream supports draining."""
 
     def __init__(self, out: Sink, out_can_drain: bool) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Requires(Acc(out.drain_count_pred(), 1 / 2))
         Ensures(Acc(self.out) and self.out is out)  # type: ignore
         Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
@@ -119,7 +119,7 @@
     # Draining the wrapper is bounded work (at most one forwarded invocation),
     # so it must TERMINATE: without this obligation the postconditions could be
     # discharged vacuously by a body that never returns.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(stream.out, 1 / 2))
@@ -139,6 +139,5 @@
                     stream.out.get_drained() == Old(stream.out.get_drained())))
     # post-conditions-end
     # impl-start
-    if stream.out_can_drain:
-        stream.out.do_drain()
+    drain_buffer(stream)
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -74,7 +74,7 @@
     # pure-end
 
     def __init__(self) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
         self.drained = 0  # type: int
         Fold(self.drain_count_pred())
@@ -84,7 +84,7 @@
         # that it ran (the invocation count advances by one). This is the ONLY
         # operation that may advance the count. It is bounded work: it promises
         # termination to its callers.
-        Requires(MustTerminate(2))
+        Requires(MustTerminate(1))
         Requires(self.drain_count_pred())
         Ensures(self.drain_count_pred())
         Ensures(self.get_drained() == Old(self.get_drained()) + 1)
@@ -99,7 +99,7 @@
     the underlying stream supports draining."""
 
     def __init__(self, out: Sink, out_can_drain: bool) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Requires(Acc(out.drain_count_pred(), 1 / 2))
         Ensures(Acc(self.out) and self.out is out)  # type: ignore
         Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
@@ -119,7 +119,7 @@
     # Draining the wrapper is bounded work (at most one forwarded invocation),
     # so it must TERMINATE: without this obligation the postconditions could be
     # discharged vacuously by a body that never returns.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(stream.out, 1 / 2))
@@ -140,5 +140,7 @@
     # post-conditions-end
     # impl-start
     if stream.out_can_drain:
-        stream.out.do_drain()
+        Unfold(stream.out.drain_count_pred())
+        stream.out.drained = stream.out.drained + 1
+        Fold(stream.out.drain_count_pred())
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
     # pure-end
 
     def __init__(self) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
         self.drained = 0  # type: int
         Fold(self.drain_count_pred())
@@ -84,7 +84,7 @@
         # that it ran (the invocation count advances by one). This is the ONLY
         # operation that may advance the count. It is bounded work: it promises
         # termination to its callers.
-        Requires(MustTerminate(2))
+        Requires(MustTerminate(1))
         Requires(self.drain_count_pred())
         Ensures(self.drain_count_pred())
         Ensures(self.get_drained() == Old(self.get_drained()) + 1)
@@ -99,7 +99,7 @@
     the underlying stream supports draining."""
 
     def __init__(self, out: Sink, out_can_drain: bool) -> None:
-        Requires(MustTerminate(6))
+        Requires(MustTerminate(1))
         Requires(Acc(out.drain_count_pred(), 1 / 2))
         Ensures(Acc(self.out) and self.out is out)  # type: ignore
         Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
@@ -119,7 +119,7 @@
     # Draining the wrapper is bounded work (at most one forwarded invocation),
     # so it must TERMINATE: without this obligation the postconditions could be
     # discharged vacuously by a body that never returns.
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(stream.out, 1 / 2))
@@ -140,5 +140,5 @@
     # post-conditions-end
     # impl-start
     if stream.out_can_drain:
-        stream.out.do_drain()
+        stream.out.drained = Old(stream.out.get_drained()) + 1
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13516.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A thin text-output wrapper forwards a buffer-draining request to the
  underlying stream it wraps. The request must reach the underlying stream:
  draining the wrapper drains the wrapped stream.

    (1) When the wrapped stream supports draining (it exposes a drain
        primitive), draining the wrapper invokes that underlying drain
        primitive exactly once. Any buffered output the wrapped stream holds is
        therefore pushed out immediately, rather than only when the program
        ends.

    (2) When the wrapped stream does NOT support draining, draining the wrapper
        is a harmless no-op: it completes normally and changes nothing.

  In both cases the wrapper itself is left exactly as it was -- it still wraps
  the same underlying stream and still reports the same drain-capability.

The wrapper is modelled as a minimal object exposing only the two touched
pieces of state: a reference to the underlying stream, and whether that stream
supports draining (a cached capability bit), captured as a bool. The underlying
drain primitive's observable effect -- that it was invoked -- is carried by a
monotone invocation count on the underlying stream; one invocation increments
it by one. That count is held behind an abstraction predicate and read only via
a pure accessor, so it can advance ONLY by running the underlying drain
primitive -- it cannot be fabricated by writing the count directly. The
whether-it-supports-draining probe is read directly off the modelled capability
bit; the underlying drain primitive's effect is modelled deeply (the count
bump) and validated against the real stream's drain primitive out-of-band by
axiom_check.py (G-AX, an A-reference), not consumed as a contract axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The capability probe (does the underlying stream support
# draining) is a pure boolean read off the modelled state, and the underlying
# drain primitive's observable effect (it was invoked) is modelled DEEPLY as a
# monotone count bump rather than axiomatized. The real underlying drain
# primitive is validated == this deep model out-of-band by axiom_check.py (G-AX)
# as an A-reference.
# axioms-end


class Sink:
    """The underlying stream the wrapper wraps. The only observable piece of
    state for this behaviour is how many times its drain primitive has been
    invoked (a monotone count). The count is held behind an abstraction
    predicate and exposed only through a pure accessor, so it advances ONLY by
    running the drain primitive -- never by writing the count directly."""

    # pure-start
    @Predicate
    def drain_count_pred(self) -> bool:
        # Abstraction over the underlying stream's invocation count: a holder
        # may observe the count (via get_drained) but cannot write it without
        # going through the drain primitive (do_drain), which is the only
        # operation permitted to unfold/advance/refold it.
        return Acc(self.drained)

    @Pure
    def get_drained(self) -> int:
        # Read the invocation count through the abstraction (fractional, so the
        # count can be observed in a postcondition without granting the power to
        # change it).
        Requires(Acc(self.drain_count_pred(), 1 / 2))
        return Unfolding(Acc(self.drain_count_pred(), 1 / 2), self.drained)
    # pure-end

    def __init__(self) -> None:
        Requires(MustTerminate(1))
        Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
        self.drained = 0  # type: int
        Fold(self.drain_count_pred())

    def do_drain(self) -> None:
        # The underlying stream's drain primitive: its sole observable effect is
        # that it ran (the invocation count advances by one). This is the ONLY
        # operation that may advance the count. It is bounded work: it promises
        # termination to its callers.
        Requires(MustTerminate(1))
        Requires(self.drain_count_pred())
        Ensures(self.drain_count_pred())
        Ensures(self.get_drained() == Old(self.get_drained()) + 1)
        Unfold(self.drain_count_pred())
        self.drained = self.drained + 1
        Fold(self.drain_count_pred())


class OutputStream:
    """The text-output wrapper. It holds a reference to the underlying stream
    (`out`) and the cached capability bit (`out_can_drain`) recording whether
    the underlying stream supports draining."""

    def __init__(self, out: Sink, out_can_drain: bool) -> None:
        Requires(MustTerminate(1))
        Requires(Acc(out.drain_count_pred(), 1 / 2))
        Ensures(Acc(self.out) and self.out is out)  # type: ignore
        Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
        Ensures(Acc(self.out.drain_count_pred(), 1 / 2))  # type: ignore
        self.out = out  # type: Sink
        self.out_can_drain = out_can_drain  # type: bool


def drain_buffer(stream: OutputStream) -> None:
    # pre-conditions-start
    # The wrapper itself is read-only (its underlying-stream reference and its
    # drain-capability bit are not changed) -> fractional permission. The
    # underlying stream's invocation count IS advanced -> full predicate.
    Requires(Acc(stream.out, 1 / 2))
    Requires(Acc(stream.out_can_drain, 1 / 2))
    Requires(stream.out.drain_count_pred())
    # Draining the wrapper is bounded work (at most one forwarded invocation),
    # so it must TERMINATE: without this obligation the postconditions could be
    # discharged vacuously by a body that never returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(stream.out, 1 / 2))
    Ensures(Acc(stream.out_can_drain, 1 / 2))
    Ensures(stream.out.drain_count_pred())
    # The wrapper is unchanged: same underlying stream, same capability bit.
    Ensures(stream.out is Old(stream.out))
    Ensures(stream.out_can_drain == Old(stream.out_can_drain))
    # (1) the underlying drain primitive is invoked exactly once iff the wrapped
    #     stream supports draining ... (the count is observed through the
    #     abstraction, so this clause is dischargeable only by running the
    #     primitive, never by writing the count).
    Ensures(Implies(stream.out_can_drain,
                    stream.out.get_drained() == Old(stream.out.get_drained()) + 1))
    # (2) ... and is left untouched (a harmless no-op) otherwise.
    Ensures(Implies(not stream.out_can_drain,
                    stream.out.get_drained() == Old(stream.out.get_drained())))
    # post-conditions-end
    # impl-start
    if stream.out_can_drain:
        stream.out.do_drain()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

RE-AUDIT of the REPAIRED bundle. The prior pass (987bv4b8) found this cell BROKEN because drain_buffer's precondition omitted MustTerminate(), so Nagini ran in partial-correctness mode and a non-terminating body vacuously discharged every postcondition. The current model.py (line 122) now carries Requires(MustTerminate(2)). This re-audit confirms the fix closes that defect and finds no residual weakness.

SBU_BENCHMARK_DIR=benchmark-verified; verifier env swebench-nagini-verifier.

POSITIVE CONTROL: positive_control.py = verbatim model.py. `bash scripts/nagini_verify.sh positive_control.py` => Verification successful (10.18s, exit 0). All 8 attacks are same-spec (adversary same-spec => SAME, exit 0 each) — only the impl region differs.

EXACT COMMANDS: for each: `python -m swebench_unified.adversary weakness nagini django__django-13516 <atk>.py` (run in parallel batches of <=3). Detailed rejection reasons captured via `bash scripts/nagini_verify.sh <atk>.py`.

### Per-attack results
- atk_1 (partial-domain, `pass` = prepatch inherited no-op): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Fails the discriminating postcondition Implies(out_can_drain, get_drained()==Old+1). Spec rejects. This IS the prepatch bug => prepatch_reproduced=true (model_prepatch.py body is `pass`).
- atk_2 (boundary/over-flush, do_drain() twice => +2): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Exactly-+1 clause forbids over-flush. GOOD.
- atk_3 (control-flow, unconditional do_drain() ignoring the guard): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Violates Implies(not out_can_drain, get_drained()==Old). GOOD.
- atk_4 (control-flow, INVERTED guard `if not out_can_drain: do_drain()`): weakness => NOT-A-COUNTEREXAMPLE (does not verify). GOOD.
- atk_5 (NON-TERMINATION, `while True: Invariant(True)` — the PRIOR BREAK): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Direct verify: exit 1, `atk_5.py:142:5:143:24: error: Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` NOW REJECTED by the MustTerminate(2) fix. GOOD.
- atk_6 (NON-TERMINATION, `drain_buffer(stream)` unbounded self-recursion — the PRIOR DEFINITIVE BREAK): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Direct verify: exit 1, `atk_6.py:142:5:142:25: error: Obligation leak check failed. Callee drain_buffer might not take all unsatisfied obligations from the caller.` NOW REJECTED by the fix. GOOD.
- atk_7 (ungrounded-oracle-echo, HONEST inline Unfold/+1/Fold under the guard — refinement.md §B's 'honest inline form'): weakness => CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, ~9-10s). Its faithful refinement per refinement.md/mapping.md IS the real increment work == gold behaviour `def flush(self): if hasattr(self._out,'flush'): self._out.flush()` => materialized as atk_7.patch and RUN through the official harness: `run_resolve('django__django-13516', atk_7.patch, retries=1)` => RESOLVED=True, COMPLETED=True, FLAKY=False, patch_successfully_applied=True, FAIL_TO_PASS success=[test_outputwrapper_flush], PASS_TO_PASS 43 success. A LEGITIMATE RESOLVING ECHO, exactly as the resolve-step policy expects — NOT a break.
- atk_8 (ungrounded-oracle-echo, DIRECT field write `stream.out.drained = Old(get_drained())+1` under the guard, directive-8 probe): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Direct verify: exit 1, `atk_8.py:143:9:143:63: error: Assignment might fail. There might be insufficient permission to access stream.out.drained.` The abstraction predicate/pure-accessor echo-hardening works. GOOD.

SUMMARY: 8 distinct same-spec wrong/echo impls encoded and machine-checked. 6 correctly REJECTED by the verifier (atk_1..6 incl. both prior non-termination breaks + atk_8 direct-write). 1 verifying CANDIDATE materialized + resolve-run (atk_7) => RESOLVES. No verifying same-spec wrong impl's faithful patch fails to resolve => verify does NOT imply incorrect here.

REFINEMENT.MD A-LEG AUDIT: A1=R (wrapper<->OutputStream minimal carrier, self._out<->stream.out, hasattr(_out,'flush')<->out_can_drain). A2=R (branch guard `if hasattr(...)` <-> `if out_can_drain`). A3=A-REFERENCE (deep model Sink.do_drain count-bump via Unfold/+1/Fold of drain_count_pred, read only through @Pure get_drained <-> real self._out.flush(); validated out-of-band by axiom_check.py/G-AX: invoked exactly once iff flushable, harmless no-op otherwise, wrapper unchanged, no raise; axiom_check.py exercises StringIO+mock (200x), a concrete CountingStream, and a NoFlushStream). A4=I (implicit else / method returns normally). NO consumed @ContractOnly axioms; NO kind-3 (unexpressible-changed-op) legs. The A3 A-reference correspondence to the real callee HOLDS and is not the defect. The prior defect (partial-correctness via missing termination obligation) is CLOSED by Requires(MustTerminate(2)) on drain_buffer (plus MustTerminate(1) on the scaffolding methods).

VERDICT: SOUND. >=5 attacks run (8 here), none breaks the spec; the sole verifying candidate resolves.

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
"""Twin-artifact model for django__django-13516.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A thin text-output wrapper forwards a buffer-draining request to the
  underlying stream it wraps. The request must reach the underlying stream:
  draining the wrapper drains the wrapped stream.

    (1) When the wrapped stream supports draining (it exposes a drain
        primitive), draining the wrapper invokes that underlying drain
        primitive exactly once. Any buffered output the wrapped stream holds is
        therefore pushed out immediately, rather than only when the program
        ends.

    (2) When the wrapped stream does NOT support draining, draining the wrapper
        is a harmless no-op: it completes normally and changes nothing.

  In both cases the wrapper itself is left exactly as it was -- it still wraps
  the same underlying stream and still reports the same drain-capability.

The wrapper is modelled as a minimal object exposing only the two touched
pieces of state: a reference to the underlying stream, and whether that stream
supports draining (a cached capability bit), captured as a bool. The underlying
drain primitive's observable effect -- that it was invoked -- is carried by a
monotone invocation count on the underlying stream; one invocation increments
it by one. That count is held behind an abstraction predicate and read only via
a pure accessor, so it can advance ONLY by running the underlying drain
primitive -- it cannot be fabricated by writing the count directly. The
whether-it-supports-draining probe is read directly off the modelled capability
bit; the underlying drain primitive's effect is modelled deeply (the count
bump) and validated against the real stream's drain primitive out-of-band by
axiom_check.py (G-AX, an A-reference), not consumed as a contract axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The capability probe (does the underlying stream support
# draining) is a pure boolean read off the modelled state, and the underlying
# drain primitive's observable effect (it was invoked) is modelled DEEPLY as a
# monotone count bump rather than axiomatized. The real underlying drain
# primitive is validated == this deep model out-of-band by axiom_check.py (G-AX)
# as an A-reference.
# axioms-end


class Sink:
    """The underlying stream the wrapper wraps. The only observable piece of
    state for this behaviour is how many times its drain primitive has been
    invoked (a monotone count). The count is held behind an abstraction
    predicate and exposed only through a pure accessor, so it advances ONLY by
    running the drain primitive -- never by writing the count directly."""

    # pure-start
    @Predicate
    def drain_count_pred(self) -> bool:
        # Abstraction over the underlying stream's invocation count: a holder
        # may observe the count (via get_drained) but cannot write it without
        # going through the drain primitive (do_drain), which is the only
        # operation permitted to unfold/advance/refold it.
        return Acc(self.drained)

    @Pure
    def get_drained(self) -> int:
        # Read the invocation count through the abstraction (fractional, so the
        # count can be observed in a postcondition without granting the power to
        # change it).
        Requires(Acc(self.drain_count_pred(), 1 / 2))
        return Unfolding(Acc(self.drain_count_pred(), 1 / 2), self.drained)
    # pure-end

    def __init__(self) -> None:
        Requires(MustTerminate(1))
        Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
        self.drained = 0  # type: int
        Fold(self.drain_count_pred())

    def do_drain(self) -> None:
        # The underlying stream's drain primitive: its sole observable effect is
        # that it ran (the invocation count advances by one). This is the ONLY
        # operation that may advance the count. It is bounded work: it promises
        # termination to its callers.
        Requires(MustTerminate(1))
        Requires(self.drain_count_pred())
        Ensures(self.drain_count_pred())
        Ensures(self.get_drained() == Old(self.get_drained()) + 1)
        Unfold(self.drain_count_pred())
        self.drained = self.drained + 1
        Fold(self.drain_count_pred())


class OutputStream:
    """The text-output wrapper. It holds a reference to the underlying stream
    (`out`) and the cached capability bit (`out_can_drain`) recording whether
    the underlying stream supports draining."""

    def __init__(self, out: Sink, out_can_drain: bool) -> None:
        Requires(MustTerminate(1))
        Requires(Acc(out.drain_count_pred(), 1 / 2))
        Ensures(Acc(self.out) and self.out is out)  # type: ignore
        Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
        Ensures(Acc(self.out.drain_count_pred(), 1 / 2))  # type: ignore
        self.out = out  # type: Sink
        self.out_can_drain = out_can_drain  # type: bool


def drain_buffer(stream: OutputStream) -> None:
    # pre-conditions-start
    # The wrapper itself is read-only (its underlying-stream reference and its
    # drain-capability bit are not changed) -> fractional permission. The
    # underlying stream's invocation count IS advanced -> full predicate.
    Requires(Acc(stream.out, 1 / 2))
    Requires(Acc(stream.out_can_drain, 1 / 2))
    Requires(stream.out.drain_count_pred())
    # Draining the wrapper is bounded work (at most one forwarded invocation),
    # so it must TERMINATE: without this obligation the postconditions could be
    # discharged vacuously by a body that never returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(stream.out, 1 / 2))
    Ensures(Acc(stream.out_can_drain, 1 / 2))
    Ensures(stream.out.drain_count_pred())
    # The wrapper is unchanged: same underlying stream, same capability bit.
    Ensures(stream.out is Old(stream.out))
    Ensures(stream.out_can_drain == Old(stream.out_can_drain))
    # (1) the underlying drain primitive is invoked exactly once iff the wrapped
    #     stream supports draining ... (the count is observed through the
    #     abstraction, so this clause is dischargeable only by running the
    #     primitive, never by writing the count).
    Ensures(Implies(stream.out_can_drain,
                    stream.out.get_drained() == Old(stream.out.get_drained()) + 1))
    # (2) ... and is left untouched (a harmless no-op) otherwise.
    Ensures(Implies(not stream.out_can_drain,
                    stream.out.get_drained() == Old(stream.out.get_drained())))
    # post-conditions-end
    # impl-start
    if stream.out_can_drain:
        stream.out.do_drain()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

RE-AUDIT of the REPAIRED bundle. The prior pass (987bv4b8) found this cell BROKEN because drain_buffer's precondition omitted MustTerminate(), so Nagini ran in partial-correctness mode and a non-terminating body vacuously discharged every postcondition. The current model.py (line 122) now carries Requires(MustTerminate(2)). This re-audit confirms the fix closes that defect and finds no residual weakness.

SBU_BENCHMARK_DIR=benchmark-verified; verifier env swebench-nagini-verifier.

POSITIVE CONTROL: positive_control.py = verbatim model.py. `bash scripts/nagini_verify.sh positive_control.py` => Verification successful (10.18s, exit 0). All 8 attacks are same-spec (adversary same-spec => SAME, exit 0 each) — only the impl region differs.

EXACT COMMANDS: for each: `python -m swebench_unified.adversary weakness nagini django__django-13516 <atk>.py` (run in parallel batches of <=3). Detailed rejection reasons captured via `bash scripts/nagini_verify.sh <atk>.py`.

### Per-attack results
- atk_1 (partial-domain, `pass` = prepatch inherited no-op): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Fails the discriminating postcondition Implies(out_can_drain, get_drained()==Old+1). Spec rejects. This IS the prepatch bug => prepatch_reproduced=true (model_prepatch.py body is `pass`).
- atk_2 (boundary/over-flush, do_drain() twice => +2): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Exactly-+1 clause forbids over-flush. GOOD.
- atk_3 (control-flow, unconditional do_drain() ignoring the guard): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Violates Implies(not out_can_drain, get_drained()==Old). GOOD.
- atk_4 (control-flow, INVERTED guard `if not out_can_drain: do_drain()`): weakness => NOT-A-COUNTEREXAMPLE (does not verify). GOOD.
- atk_5 (NON-TERMINATION, `while True: Invariant(True)` — the PRIOR BREAK): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Direct verify: exit 1, `atk_5.py:142:5:143:24: error: Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` NOW REJECTED by the MustTerminate(2) fix. GOOD.
- atk_6 (NON-TERMINATION, `drain_buffer(stream)` unbounded self-recursion — the PRIOR DEFINITIVE BREAK): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Direct verify: exit 1, `atk_6.py:142:5:142:25: error: Obligation leak check failed. Callee drain_buffer might not take all unsatisfied obligations from the caller.` NOW REJECTED by the fix. GOOD.
- atk_7 (ungrounded-oracle-echo, HONEST inline Unfold/+1/Fold under the guard — refinement.md §B's 'honest inline form'): weakness => CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, ~9-10s). Its faithful refinement per refinement.md/mapping.md IS the real increment work == gold behaviour `def flush(self): if hasattr(self._out,'flush'): self._out.flush()` => materialized as atk_7.patch and RUN through the official harness: `run_resolve('django__django-13516', atk_7.patch, retries=1)` => RESOLVED=True, COMPLETED=True, FLAKY=False, patch_successfully_applied=True, FAIL_TO_PASS success=[test_outputwrapper_flush], PASS_TO_PASS 43 success. A LEGITIMATE RESOLVING ECHO, exactly as the resolve-step policy expects — NOT a break.
- atk_8 (ungrounded-oracle-echo, DIRECT field write `stream.out.drained = Old(get_drained())+1` under the guard, directive-8 probe): weakness => NOT-A-COUNTEREXAMPLE (does not verify). Direct verify: exit 1, `atk_8.py:143:9:143:63: error: Assignment might fail. There might be insufficient permission to access stream.out.drained.` The abstraction predicate/pure-accessor echo-hardening works. GOOD.

SUMMARY: 8 distinct same-spec wrong/echo impls encoded and machine-checked. 6 correctly REJECTED by the verifier (atk_1..6 incl. both prior non-termination breaks + atk_8 direct-write). 1 verifying CANDIDATE materialized + resolve-run (atk_7) => RESOLVES. No verifying same-spec wrong impl's faithful patch fails to resolve => verify does NOT imply incorrect here.

REFINEMENT.MD A-LEG AUDIT: A1=R (wrapper<->OutputStream minimal carrier, self._out<->stream.out, hasattr(_out,'flush')<->out_can_drain). A2=R (branch guard `if hasattr(...)` <-> `if out_can_drain`). A3=A-REFERENCE (deep model Sink.do_drain count-bump via Unfold/+1/Fold of drain_count_pred, read only through @Pure get_drained <-> real self._out.flush(); validated out-of-band by axiom_check.py/G-AX: invoked exactly once iff flushable, harmless no-op otherwise, wrapper unchanged, no raise; axiom_check.py exercises StringIO+mock (200x), a concrete CountingStream, and a NoFlushStream). A4=I (implicit else / method returns normally). NO consumed @ContractOnly axioms; NO kind-3 (unexpressible-changed-op) legs. The A3 A-reference correspondence to the real callee HOLDS and is not the defect. The prior defect (partial-correctness via missing termination obligation) is CLOSED by Requires(MustTerminate(2)) on drain_buffer (plus MustTerminate(1) on the scaffolding methods).

VERDICT: SOUND. >=5 attacks run (8 here), none breaks the spec; the sole verifying candidate resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Axis = faithfulness/too-strong (G-PANEL-2). Spec region is byte-identical & frozen: markers.same_spec(model, model_prepatch) = True. Current model.py VERIFIES under the pinned Nagini verifier (exit 0, 9.98s) and now carries `from nagini_contracts.obligations import MustTerminate` + `Requires(MustTerminate(2))`. The spec's three postconditions are exactly the real behaviour: (1) exactly-one underlying invocation iff flushable, (2) no-op otherwise, (3) wrapper unchanged. My direct faithfulness probe (faith_probe_13516.py) emulating the gold `def flush(self): if hasattr(self._out,'flush'): self._out.flush()` on flushable and non-flushable streams shows no divergence — real callee satisfies every postcondition. This is corroborated by recorded machine gates: G-CONF pass (shadow verbatim impl == real patched repo function over 100003 Requires-satisfying inputs, 0 disagreements) and G-AX pass (299 observations, invoked exactly once iff flushable, no-op + no raise otherwise, wrapper unchanged). The spec is neither too strong nor drifting from repo behaviour. NOTE: the stale verdict.md (2026-08-12) records a G-EQ/G-PANEL-2 'BROKEN verify⇏correct' note, but that is the OPPOSITE (too-WEAK) direction — a non-terminating same-spec impl (self-recursion / infinite loop) verified vacuously because the spec at that time lacked a termination obligation. That is not a faithfulness/too-strong defect and is out of my axis; furthermore the current model.py has been repaired (MustTerminate(2) now present), which closes that hole and is why the model + a terminating faithful impl still verify.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py with the impl region elided (verified via markers.spec_view). It describes the behavior in fully abstracted terms ('buffer-draining wrapper', 'underlying stream', 'drain primitive', 'capability bit', monotone invocation count) and reveals NO gold-edit specific: token scan shows none of flush/_out/hasattr/OutputWrapper/TextIOBase/StringIO/base.py/stdout/stderr/migrate appear in the spec view. Mechanical leakage.screen() returns passed=True, zero hard_failures, zero warnings; no diff markers, no patched path, no spec-view identifier colliding with a patched repo symbol, no bug/fix narration. The behavioral clauses (forward the drain under a capability guard; exactly-once when supported; no-op otherwise; wrapper unchanged) are exactly the faithful desired behavior already implied by the public problem_statement ('flush() ... doesn't work' — it should reach the underlying stream), so they do not leak the gold edit beyond problem_statement — a solver could not recover that the fix is an added OutputWrapper.flush() forwarding to self._out.flush() under a hasattr guard from the spec view alone. The concrete gold-symbol naming lives only in mapping.md/refinement.md (auditor docs, not the solver-visible spec view). meta G-LEAK=pass, not relaxed; no RELAXED_LEAKAGE.md.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
