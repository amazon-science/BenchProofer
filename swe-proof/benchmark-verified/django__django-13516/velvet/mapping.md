# mapping.md — django__django-13516

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b7da588e883e12b8ac3bb8a486e654e30fc1c6c8`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/core/management/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `propagateFlush (mut sink : OutputSink)` | the flush request handler on the output-stream wrapper `OutputWrapper` — `django/core/management/base.py:120` (class), behavior added at body line 143 post-patch | the modeled changed function |
| `OutputSink.flushable` | `hasattr(self._out, 'flush')` — `django/core/management/base.py:144` (post-patch guard) | does the wrapped underlying stream expose a flush operation |
| `OutputSink.flushes` | the number of `self._out.flush()` invocations driven through to the wrapped stream — `django/core/management/base.py:145` (post-patch body) | the outward observable effect the F2P test asserts (`mocked_flush.called`) |

The pre-patch repo reality the change fixes (refinement audit only, not in the
consumer spec view): `OutputWrapper` subclasses `io.TextIOBase`, whose generic
`flush()` is a no-op that never reaches `self._out`; and `__getattr__`
(`base.py:140`) — which would forward unknown attributes to `self._out` — is
NOT consulted for `flush`, because the attribute already resolves on the base
class. So `wrapper.flush()` silently does nothing pre-patch.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo objects. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `OutputWrapper` instance, restricted to flush-relevant state | `OutputSink` | a wrapper `w` ↔ `⟨hasattr(w._out,'flush'), k⟩` where `k` = number of `w._out.flush()` calls observed so far. The non-flush state of `w` (`_out` content, `ending`, `style_func`) is invariant under a flush and is omitted from the carrier. |
| `hasattr(self._out, 'flush')` (a fixed property of the wrapped stream) | `OutputSink.flushable : Bool` | `True` ↔ `true`, `False` ↔ `false`. Read-only across a flush. |
| count of forwarded `self._out.flush()` invocations | `OutputSink.flushes : Nat` | Python `int` count ↔ `Nat`; one forwarded flush ↔ `+1`. The F2P test observes the boolean `flushes ≥ 1` via `mock`'s `called` flag; `Nat` is the faithful exact-count refinement of that observable. |
| a flush request `wrapper.flush()` | the method `propagateFlush` (mutates `sink`) | calling `wrapper.flush()` once ↔ running `propagateFlush` once on the corresponding `sink`. |

There is no `str`/`List Char` modeling here: the changed behavior is a control-
flow + side-effect propagation, not a string transformation. The carrier is the
minimal observable state a single flush request can read or affect.

## 3. Callee provenance

### 3.1 No consumed axioms, no deep-model references
The modeled operation is spelled out **directly** over the observable carrier:
`propagateFlush` *is* the conditional forward (`if flushable then flushes+1`),
which is exactly the gold body `if hasattr(self._out,'flush'): self._out.flush()`
under the §2 bijection. There is therefore:

* **no `axiom` consumed by the proof** — the bundle declares zero consumed
  axioms in meta.json; the proof discharges by `loom_solve` over the spelled-out
  branch, and there is no `axiom_check.py`;
* **no A-reference deep model** of an unchanged callee — the only callee the
  gold body invokes, the underlying stream's own `flush()`, is precisely the
  operation whose *forwarding* is the fix; its single observable contribution
  (it gets called, and only when present) is modeled directly as the `flushes`
  increment guarded by `flushable`. We do NOT axiomatize what the underlying
  `flush()` does internally — that is irrelevant to the observable the F2P test
  and the issue care about (that it is reached at all). By directive 7 the
  changed op must not be axiomatized; it is an **I** op, checked by G-CONF (which
  applies `patch.diff`). G-AX runs the *unpatched* testbed and validates
  contracts on UNCHANGED callees, so it has nothing to check here and is
  **skipped** (precedent: django__django-11451).

### 3.2 Flag / branch dependency
The single branch dependency is `flushable` (`hasattr(self._out, 'flush')`):

* `flushable = true`  → the wrapped stream exposes flush → the request is
  forwarded exactly once (`flushes` += 1). This is the F2P configuration
  (`StringIO` exposes `flush`).
* `flushable = false` → the wrapped stream has no flush → the request is a
  no-op (`flushes` unchanged) and must not raise.

`conformance_check.py` (G-CONF) fuzzes BOTH configurations against the real
patched `OutputWrapper` (it applies `patch.diff` first) so the boolean guard is
validated against the real callee. There is no `axiom_check.py`: G-AX runs the
unpatched testbed and has no unchanged-callee contract to validate (§3.1).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13516`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the `propagateFlush` `do` block to Python (`if flushable: flushes += 1`) and
compares its observable (whether a flush reached the wrapped stream, and how
many times) against the real patched `OutputWrapper.flush()` driven on a wrapped
stream that records its flush count, over flushable and non-flushable streams.
