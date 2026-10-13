# mapping.md — django__django-13516

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b7da588e883e12b8ac3bb8a486e654e30fc1c6c8`, states the type
abstraction, and gives the provenance of the deep-model reference (the
underlying stream's drain primitive; checked by G-AX, not consumed as a
contract axiom).

Repo file under change: `django/core/management/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `drain_buffer(stream)` | `OutputWrapper.flush(self)` — the method ADDED by the gold patch at `django/core/management/base.py:143-145` (inserted between `__getattr__` and `isatty`) | the modeled changed function (the wrapper's buffer-drain method) |
| `OutputStream` / `stream` | the `OutputWrapper` instance `self` (`django/core/management/base.py:120` `class OutputWrapper(TextIOBase)`) | the text-output wrapper whose drain method the fix adds |
| `stream.out` | `self._out` (the wrapped stream, set in `OutputWrapper.__init__`, `base.py:136`) | reference to the underlying stream |
| `stream.out_can_drain` | `hasattr(self._out, 'flush')` (the guard in the added method, `base.py:144`) | cached capability bit: does the wrapped stream expose a `flush` attribute |
| `Sink` / `stream.out.drained` | the wrapped stream object and the observable effect of `self._out.flush()` (`base.py:145`) | underlying stream; `drained` counts invocations of its drain primitive. Held behind `@Predicate drain_count_pred`, read via `@Pure get_drained`, advanced only by `do_drain` (directive-8 echo hardening) |
| `Sink.do_drain(self)` | `self._out.flush()` (`base.py:145`) | the underlying stream's drain primitive (its sole tested effect: it ran) |

The gold patch (the only change) inserts:

```python
def flush(self):
    if hasattr(self._out, 'flush'):
        self._out.flush()
```

modelled by `drain_buffer`'s impl `if stream.out_can_drain: stream.out.do_drain()`.

### Why the pre-patch wrapper does nothing (the bug)

`OutputWrapper` subclasses `io.TextIOBase` (`base.py:120`). `TextIOBase`
already provides a `flush()` method (a no-op for an object with no real buffer
of its own). Because `flush` therefore EXISTS on the class, `OutputWrapper`'s
`__getattr__` (`base.py:140-141`, which forwards *missing* attributes to
`self._out`) is never consulted for `flush`. So pre-patch
`OutputWrapper.flush()` resolves to the inherited `TextIOBase.flush()` no-op and
the wrapped stream's own `flush()` is never called. Confirmed on the eval
interpreter: `hasattr(io.TextIOBase, 'flush') is True`; `io.StringIO` (the
F2P test's wrapped stream) does expose a real `flush`. The fix overrides
`flush` explicitly to forward to `self._out.flush()` under the `hasattr` guard.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `OutputWrapper` instance `self` (a `TextIOBase` subclass with `_out`, `style_func`, `ending`) | `OutputStream` (fields `out`, `out_can_drain`) | a minimal class carrying only the two touched pieces of state; `style_func`/`ending` are untouched by this behaviour and dropped |
| `self._out` (the wrapped file-like object) | `stream.out : Sink` | object reference; the method does not reassign it (read-only, fractional permission) |
| `hasattr(self._out, 'flush')` (a `bool`) | `stream.out_can_drain : bool` | the capability probe is captured as a cached boolean off the modelled state; the method does not change it (read-only, fractional permission). `True` ↔ the wrapped stream exposes a drain primitive; `False` ↔ it does not |
| the observable effect of `self._out.flush()` — that it was invoked (what the F2P mock `mocked_flush.called` checks) | `stream.out.drained : int`, a monotone invocation counter; one invocation ⇒ `+1` | the F2P test observes only *that* the underlying flush ran, via `mock.patch.object(out,'flush')` then `assertIs(mocked_flush.called, True)`. The counter abstracts "was it called / how many times": pre-patch `0`, post-patch (with a flushable stream) `1`. The wrapped stream's buffer contents and the actual byte-draining are not observed by the test and are not modelled |

`hasattr` is a Python builtin probe; Nagini cannot perform dynamic attribute
introspection, so its result is modelled as the concrete cached bool
`out_can_drain`. This is sound: the patch's `if hasattr(self._out, 'flush')`
gates the forward, and the modelled `if stream.out_can_drain` gates the
counter bump identically. For the F2P case the wrapped stream is a `StringIO`,
for which `hasattr(out, 'flush')` is `True` (so `out_can_drain == True`).

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `Sink.do_drain` / the `out_can_drain`-guarded forward ↔ the real `OutputWrapper.flush`

There is **no consumed `@ContractOnly` axiom**. The underlying drain
primitive's only tested effect — *that it was invoked* — is modelled DEEPLY as
the count bump in `Sink.do_drain` (an `Unfold` / `+1` / `Fold` of the
abstraction predicate `drain_count_pred`; the count is read only through
`@Pure get_drained`, so it can advance only by running `do_drain` — directive-8
echo hardening), and the capability probe is a pure boolean read. What G-AX
validates as an **A-reference** is that the REAL `OutputWrapper.flush`
(post-patch) reproduces this deep model:

- when the wrapped stream exposes a `flush` attribute (the F2P case,
  `StringIO`), calling `OutputWrapper.flush()` invokes the wrapped stream's
  `flush` **exactly once** (counter `0 → 1`) — matching
  `Implies(out_can_drain, drained == Old(drained) + 1)`;
- when the wrapped stream has NO `flush` attribute, calling
  `OutputWrapper.flush()` is a harmless no-op: it returns normally and never
  touches the wrapped stream (counter unchanged) — matching
  `Implies(not out_can_drain, drained == Old(drained))`;
- in both cases the wrapper is unchanged (still wraps the same stream, still
  reports the same capability) and no exception is raised.

It additionally confirms the **pre-patch** wrapper (inherited
`TextIOBase.flush`) leaves the counter at `0` even for a flushable stream —
the bug the spec senses (G-DIFF).

**Soundness check (G-AX):** `axiom_check.py` runs the real Django
`OutputWrapper` against `mock`-instrumented and concrete wrapped streams
(flushable `StringIO`, an explicit flush-counting stream, and a stream with
NO `flush` attribute), boundary + repeated, asserting every observation meets
the deep model above. It imports only Django + the standard library; nothing
test-private. Exit 0 iff sound. (Outside the container Django may be absent, in
which case it prints `G-AX SKIP` and returns 0; the orchestrator runs it
in-container.) The behaviour is flag-independent — `OutputWrapper.flush`
forwards under a plain `hasattr` guard regardless of any configuration.
