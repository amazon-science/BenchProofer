# refinement.md — django__django-13516

The operation-by-operation correspondence between `model.py`'s implementation
(the `drain_buffer` impl region, the `Sink`/`OutputStream` constructors, and the
`Sink.do_drain` deep model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized/deep-modelled callee — split
into **A-consumed**, where the proof uses a `@ContractOnly` axiom's `Ensures`,
and **A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The wrapper's buffer-drain method — `OutputWrapper.flush` (`django/core/management/base.py:143-145`)

Gold hunk (the whole change — a newly added method):
```
     def __getattr__(self, name):
         return getattr(self._out, name)

+    def flush(self):
+        if hasattr(self._out, 'flush'):
+            self._out.flush()
+
     def isatty(self):
         return hasattr(self._out, 'isatty') and self._out.isatty()
```

`OutputWrapper` subclasses `io.TextIOBase`, which already defines a no-op
`flush`; so pre-patch the wrapper's `__getattr__` forwarder never fires for
`flush` and the wrapped stream's own `flush` is never called. The fix overrides
`flush` to forward explicitly, guarded by `hasattr(self._out, 'flush')`.

| # | model.py impl op (`drain_buffer`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `stream: OutputStream` with fields `stream.out`, `stream.out_can_drain` | the receiver `self` (the `OutputWrapper` instance), its `self._out`, and the `hasattr(self._out, 'flush')` capability | R | the wrapper modelled as a minimal class with only the two touched pieces of state; `self._out` ↔ `stream.out`, `hasattr(self._out, 'flush')` ↔ the cached bool `stream.out_can_drain` (mapping.md §1, §2). |
| A2 | `if stream.out_can_drain:` | `if hasattr(self._out, 'flush'):` | R | the same branch guard: "does the wrapped stream support draining". `hasattr` is a dynamic introspection Nagini cannot perform, so its boolean result is refined to the cached bit `out_can_drain` (mapping.md §2). The branch is taken on exactly the same condition. |
| A3 | `stream.out.do_drain()` (the deep model: invoking the underlying drain primitive advances its invocation count by one) | `self._out.flush()` | **A-reference** | the underlying stream's drain primitive. Modelled DEEPLY by `Sink.do_drain` (count `+1`, performed as `Unfold` / `+1` / `Fold` of the abstraction predicate `drain_count_pred`), NOT axiomatized; its sole tested effect (it was invoked, observed by the F2P mock's `.called`) is captured by the count. The count is hidden behind `@Predicate drain_count_pred` and read only via `@Pure get_drained`, so `do_drain` is the ONLY operation that can advance it (directive-8: the observable cannot be echoed by a direct field write). G-AX validates the real `self._out.flush()` against this deep model: invoked exactly once when the wrapped stream is flushable, never when it is not, no raise (mapping.md §3.1). |
| A4 | the implicit `else` (no statement) — when `not stream.out_can_drain`, the counter is untouched and the method returns normally | the absent `else` of `if hasattr(...)` — the method simply returns | I | identical control flow: when the guard is false nothing runs and the method returns normally (no exception). |

`OutputStream.__init__` / `Sink` / `Sink.do_drain` are modelling scaffolding
(the minimal carrier types and the deep model of the drain primitive's effect),
not extra repo operations; their correspondence is the R refinement of A1 and
the A-reference deep model of A3.

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: its `drain_buffer` body is the
inherited no-op (`pass`), exactly as the pre-patch wrapper resolves `flush` to
`TextIOBase.flush()` (a no-op) and never reaches `self._out.flush()`. With the
byte-identical frozen spec it **FAILS** verification on the discriminating
postcondition
`Ensures(Implies(stream.out_can_drain, stream.out.get_drained() == Old(stream.out.get_drained()) + 1))`
(`model_prepatch.py:126-127` — *Postcondition of drain_buffer might not hold:
Implies(stream.out_can_drain, get_drained() == Old(get_drained()) + 1)*).

That is precisely the behaviour the F2P test observes:
`test_outputwrapper_flush` wraps a `StringIO` (a flushable stream ⇒
`out_can_drain == True`), mocks its `flush`, runs a command that calls
`self.stdout.flush()`, and asserts `mocked_flush.called is True` — i.e. the
underlying flush was invoked at least once (counter advanced). No
implementation that fails to forward the drain on a flushable stream can
verify (spec sees the bug).

The companion clause
`Ensures(Implies(not stream.out_can_drain, stream.out.get_drained() == Old(stream.out.get_drained())))`
together with the wrapper-unchanged clauses
(`stream.out is Old(stream.out)`, `stream.out_can_drain == Old(stream.out_can_drain)`)
keep the spec faithful to the unchanged behaviour: forwarding happens *only*
when the stream supports it, the wrapper is not mutated, and (via the fractional
read-only permissions, directive 5) a wrong impl cannot satisfy the spec by
overwriting the wrapper's state. The exactly-`+1` count (rather than `>=1`)
forbids both under- and over-flushing.

**Directive-8 (no echoing the observable).** The invocation count
`Sink.drained` is hidden behind an abstraction predicate `drain_count_pred` and
observed only through `@Pure get_drained` (read at `1/2`). `drain_buffer`'s
pre/post hold `drain_count_pred()` and phrase the count clauses on
`get_drained()`, never on the raw field. Consequently the *only* operation that
can advance the count is the modelled drain primitive `Sink.do_drain`
(`Unfold` / `+1` / `Fold`); a wrong impl cannot discharge
`Implies(out_can_drain, get_drained() == Old(get_drained()) + 1)` by writing the
counter directly — the field write `stream.out.drained = Old(stream.out.drained) + 1`
is **rejected** ("insufficient permission to access stream.out.drained"). The
postcondition is therefore dischargeable only by *running* the drain primitive,
which is the gold patch's `self._out.flush()`. (The honest inline form —
`Unfold` / `+1` / `Fold` — is the literal `do_drain` body and verifies; it is
not an echo but the real increment work.)

**Termination obligation.** `drain_buffer`'s precondition carries
`Requires(MustTerminate(2))` (and the scaffolding methods `Sink.__init__`,
`Sink.do_drain`, `OutputStream.__init__` each carry `MustTerminate(1)` so a
terminating caller may invoke them). Draining the wrapper is bounded work — at
most one forwarded invocation — so the method must return; without this
obligation Nagini proves partial correctness only, and a body that never
returns would discharge every postcondition vacuously while its faithful
counterpart never completes at runtime. With the obligation, any non-returning
body (an infinite loop, or unbounded self-recursion) fails Nagini's
obligation-leak check and is rejected.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely
*changed* — adding the guarded forward of the drain request — is captured as an
**R** guard (A2, `hasattr` ↔ `out_can_drain`) plus an **A-reference** deep model
of the underlying primitive's effect (A3). There is **no consumed axiom**: the
proof uses only the deep model (`Sink.do_drain`'s `Ensures`, which is verified
code, not a `@ContractOnly`) and the pure boolean read. The real underlying
`flush` primitive that A3 stands in for is an *unchanged* callee of the changed
method; G-AX validates the deep model against it. We never axiomatize the
method under change.

## D. verify(model) ⇒ resolved

`drain_buffer` verifies only if (A2) it forwards the drain under the same
capability guard and (A3) forwarding invokes the underlying drain primitive
exactly once (count `+1` via `do_drain`), leaving the wrapper unchanged, and
(A4) does nothing when the stream is not flushable. By R (the wrapper and its
`_out` / `hasattr(_out,'flush')` ↔ `OutputStream.out` / `out_can_drain`) and the
A-reference deep model (the underlying `flush` primitive's "it ran exactly
once" effect ↔ the count bump), the verified method equals the gold method
`def flush(self): if hasattr(self._out, 'flush'): self._out.flush()` on the
tested inputs. By G-AX the real `self._out.flush()` meets the deep model it is
checked against (invoked once iff flushable, never raises). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited deep-model reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: deep-model /
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
