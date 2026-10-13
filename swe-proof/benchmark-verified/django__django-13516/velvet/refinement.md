# refinement.md — django__django-13516

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`propagateFlush` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
this axiom's `ensures`), **A-reference** (a deep model validated == the real
callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.
This bundle has **no A-tagged steps**: it consumes no axiom and references no
unchanged callee. Every step is R or I, so the whole refinement is mechanically
refuted by **G-CONF** and there is nothing for G-AX to check (G-AX = skip).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The flush site — `OutputWrapper.flush()` (`django/core/management/base.py`)

Gold hunk (added method, base.py body lines 143-146 post-patch):
```
+    def flush(self):
+        if hasattr(self._out, 'flush'):
+            self._out.flush()
```

| # | Solution.lean impl op (`propagateFlush`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `mut sink : OutputSink` | the `self` (an `OutputWrapper` instance) of `flush()` | R | an `OutputWrapper` `w`, restricted to flush-relevant state, ↔ `⟨hasattr(w._out,'flush'), k⟩` where `k` = number of `w._out.flush()` calls observed (mapping.md §2). Non-flush state (`_out` content, `ending`, `style_func`) is invariant under a flush and omitted from the carrier. |
| A2 | guard `if sink.flushable then …` | `if hasattr(self._out, 'flush'):` | R + I | the boolean guard is identical control flow; `sink.flushable : Bool` ↔ `hasattr(self._out,'flush')` (mapping.md §2). G-CONF transliterates the branch directly. |
| A3 | `sink := { sink with flushes := sink.flushes + 1 }` (taken branch) | `self._out.flush()` | I | the *forwarding* of the request to the underlying stream is the operation the patch ADDS. Its single observable contribution — the underlying `flush` gets driven exactly once when present — is modeled directly as the guarded `flushes` increment, an **I** concrete op transliterated by G-CONF. We do NOT axiomatize what the underlying `flush()` does internally; that is irrelevant to the issue and the F2P test, which observe only *that it is reached* (`mocked_flush.called`). Because this IS the operation under change, directive 7 forbids hiding it behind an axiom: it is modeled directly and checked by **G-CONF** — which applies `patch.diff` and confirms "one forwarded flush per request when flushable, none otherwise" against the real patched `OutputWrapper.flush` over ≥10⁵ inputs. It is **not** an A-reference: an A-reference deeply models an *unchanged* callee, and there is no unchanged callee in this hunk. |
| A4 | `else return` / fallthrough `return (u : Unit)` | implicit fallthrough (non-flushable: method body is a no-op; returns `None`) | R + I | when `flushable = false` the request is a no-op leaving state unchanged and must not raise; `Unit` ↔ Python `None` return. Frame: `ensures sink.flushable = sinkOld.flushable` pins the read-only `flushable` aspect exactly (directive 5 `mut`-frame). |

Discriminating content of the change — a flush request, when the underlying
stream is flushable, is forwarded **exactly once** (`flushes = flushesOld + 1`) —
lives in the postcondition `sinkOld.flushable = true → sink.flushes =
sinkOld.flushes + 1`. The pre-patch reality the change fixes: `OutputWrapper`
subclasses `io.TextIOBase`, whose generic `flush()` is a no-op that never
reaches `self._out`, and `__getattr__` is not consulted because the attribute
already resolves on the base class — so `wrapper.flush()` silently does nothing.
`Solution_prepatch.lean` reproduces that (a bare `return`, no increment) and
**fails** the `flushes + 1` clause (G-DIFF; confirmed: the unsolved goal is
exactly `sinkOld.flushable = true → sinkOld.flushes = sinkOld.flushes + 1`).

## B. No second site

The patch is a single added method on one class. There is no urlize-style
callee-swap second site, no flag-dependent second behavior beyond the single
`flushable` guard.

## C. No A-tagged steps, no kind-3 steps

Every step is R or I — there is **no A leg at all**. The single operation that
genuinely *changed* — forwarding the flush to the underlying stream — is modeled
**directly** over the observable carrier (the guarded `flushes` increment, step
A3, an **I** op), not hidden behind an axiom about the function under change.
There is therefore:

* **no `axiom` consumed by the proof** (`meta.json` declares zero consumed
  axioms); the proof discharges by `loom_solve` over the spelled-out branch.
* **no A-reference deep model of an *unchanged* callee.** This is the key
  soundness point: the only callee the gold body invokes (the underlying
  stream's own `flush()`) is precisely the operation whose *forwarding* is the
  fix. By directive 7 one must **not** axiomatize the operation the patch
  changes, so it is modeled directly (an I op) and validated by **G-CONF**,
  which applies `patch.diff` and runs the real patched callee. G-AX, which runs
  the *unpatched* testbed and exists to validate contracts on UNCHANGED callees,
  has nothing to check here and is correctly **skipped** (precedent:
  django__django-11451, a side-effect short-circuit with G-AX=skip). Shipping an
  axiom_check.py that drove the changed callee was the prior attempt's error: it
  ran the base-commit `OutputWrapper.flush` (the inherited `TextIOBase` no-op),
  so a flush request drove zero underlying flushes and the script failed — a
  symptom of mislabeling the changed op as an A-reference, not a real soundness
  defect. Removed.

## D. verify(Solution) ⇒ resolved

`propagateFlush` verifies only if its output increments `flushes` exactly once
when `flushable` (A3) and leaves state unchanged otherwise (A4), with
`flushable` read-only (A1, frame). By R (`OutputWrapper` ↔ `OutputSink`,
`hasattr(_out,'flush')` ↔ `flushable`, one forwarded flush ↔ `+1`) the verified
method equals the gold `if hasattr(self._out,'flush'): self._out.flush()` on the
tested configurations; by G-CONF the R/I transliteration of the branch — driving
the real patched `OutputWrapper.flush` on flushable and non-flushable underlying
streams — agrees with `patch.diff`'s behaviour (one forwarded call when present,
none otherwise, never raises) over ≥10⁵ fuzzed inputs. There is no A leg, so no
G-AX obligation. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The F2P test
(`test_outputwrapper_flush`) asserts `mocked_flush.called is True`, the
observable refinement of `flushes ≥ 1`, which the verified spec guarantees in
the flushable configuration.
