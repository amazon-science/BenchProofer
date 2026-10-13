# refinement.md — django__django-13516

Maps every operation in `implementation_flush` to its `patch.diff` counterpart in
`OutputWrapper.flush` (django/core/management/base.py:143, added by the patch).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** op left as the real repo callee in G-CONF (not axiomatized),
**I** identical concrete op.

## Patch (post-patch `OutputWrapper.flush`)
```python
def flush(self):
    if hasattr(self._out, 'flush'):
        self._out.flush()
```

At `base_commit` no `flush` method exists on `OutputWrapper`; it inherits the
no-op `TextIOBase.flush`, and the wrapper's `__getattr__` delegation only fires
for ABSENT attributes, so a wrapper flush never reaches `self._out`. The patch
adds an explicit method that forwards the flush to the underlying stream when the
stream supports it.

## Modeling decision
The observable effect of a single wrapper flush request is the state of the
underlying stream `self._out`, seen through two observables: whether it supports
flushing (`hasattr(self._out, 'flush')`) and how many times its `flush` has been
invoked (a mock's `call_count`). The method:

- tests the support flag;
- when supported, invokes the underlying stream's flush exactly once (advancing
  the invocation count by one);
- when not supported, does nothing.

Both observables are modeled structurally over the `Stream` carrier, so the impl
region is all R/I content (no axiomatized callee).

## Operation correspondence
| # | Lean op (`implementation_flush`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if s.hasFlush then …` | `if hasattr(self._out, 'flush'):` | R | `hasattr(self._out, 'flush') : bool ↔ s.hasFlush : Bool`; the flush-support test. |
| 2 | `return { s with flushCount := s.flushCount + 1 }` | `self._out.flush()` | R | invoking the underlying stream's flush once ↔ advancing its observable invocation count by one (`call_count += 1`). |
| 3 | `return s` (else path) | the implicit fall-through when `hasattr` is false (method does nothing) | I | the underlying stream is left untouched. |

The support flag `s.hasFlush` is never modified by any branch (directive 5
frame): both result branches carry `s.hasFlush` through unchanged.

## R/I legs ⇒ G-CONF
Ops 1, 2, 3 are all R/I content (flag test + count increment + no-op). There is
no A-tagged op, so `conf_skip = false`: `conformance_check.py` differential-tests
the shadow (test the support flag; increment the observed invocation count iff
supported) against the REAL patched `OutputWrapper.flush` wrapping a stand-in
stream, over ≥10^5 fuzzed `(hasFlush, initialCount)` inputs.

## No axiom row
No property of any unchanged callee is consumed: the support test and the flush
invocation are modeled structurally. `meta.json axioms = []`,
`deep_model_references = []`; there is no `opaque`/`axiom` in `Solution.lean` and
`axiom_check.py` is a skip stub.

## F2P alignment
`test_outputwrapper_flush` mocks the underlying stream's `flush` and asserts it
WAS called after a command calls `self.stdout.flush()` (`mocked_flush.called is
True`). The discriminating clause `problem_spec_flush` pins is: when the stream
supports flushing, the invocation count advances by one. The prepatch impl (the
real bug) absorbs the flush as a no-op even when supported, so the count never
advances — it cannot satisfy the discriminating clause, exactly the failing test.
`patch.diff` (gold verbatim) makes the harness resolve.
