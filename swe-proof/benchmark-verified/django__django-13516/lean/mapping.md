# mapping.md — django__django-13516

## Instance
- repo: django/django
- base_commit: b7da588e883e12b8ac3bb8a486e654e30fc1c6c8
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
A stream-wrapper object (`OutputWrapper`, django/core/management/base.py:120)
delegates to an underlying stream `self._out`. It exposes a `flush` request, but
at `base_commit` no explicit `flush` method exists: the wrapper inherits the
no-op `flush` from its `TextIOBase` superclass, and the wrapper's
`__getattr__`-based delegation only fires for attributes that are NOT already
present — `flush` already resolves to the inherited no-op, so it is never
delegated to `self._out`. A caller that flushes the wrapper therefore never
flushes the underlying stream, so buffered output is not pushed out until the
end. The gold patch adds an explicit forwarding method:

```python
+    def flush(self):
+        if hasattr(self._out, 'flush'):
+            self._out.flush()
```

i.e. when the underlying stream supports flushing, the wrapper's flush request is
forwarded to it (invoking the underlying stream's flush once); when it does not,
the request is a no-op.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_flush` | `OutputWrapper.flush` (the method added at django/core/management/base.py:143 by the patch) |
| `problem_spec_flush`   | the post-condition this method must satisfy |
| `Stream.hasFlush`      | the predicate `hasattr(self._out, 'flush')` on the underlying stream |
| `Stream.flushCount`    | the observable count of times the underlying stream's `flush` has been invoked |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `Stream` | the underlying stream object `self._out` (only its flush-relevant observables) | structure with the two touched observables |
| `s.hasFlush : Bool` | `hasattr(self._out, 'flush')` (bool) | whether the underlying stream supports flushing; `true ↔ True` |
| `s.flushCount : Nat` | number of times `self._out.flush()` has been invoked | observable side-effect counter (a mock's `call_count`) |
| result `: Stream` | the underlying stream's observable state after one wrapper flush request | `hasFlush` unchanged; `flushCount` advanced iff supported |

A wrapper flush request returns `None` in Python; its OBSERVABLE effect is the
state of the underlying stream, which is what the result `Stream` carries.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The two operations the fix
  performs — testing whether the underlying stream supports flushing
  (`hasattr(..., 'flush')`) and invoking that stream's `flush` once — are modeled
  structurally over the `Stream` observables (`hasFlush`, `flushCount`). There is
  no `opaque`/`axiom` callee, so `axiom_check.py` is a skip stub.
- Flag dependency: the forwarding is conditioned on `hasFlush` (the underlying
  stream's flush-support). G-CONF fuzzes both `hasFlush ∈ {True, False}` and the
  initial invocation count.

## G-CONF fuzz seed
- pinned seed: `13516`
- ≥10^5 fuzzed `(hasFlush, initialCount)` inputs. For each, the oracle is the REAL
  patched `OutputWrapper.flush` wrapping a stand-in stream that either exposes a
  call-counting `flush` (`hasFlush=True`) or exposes no `flush` attribute
  (`hasFlush=False`); the shadow is the Lean impl transliterated. Both the
  invocation-count delta and the support-flag frame are compared.
