# refinement.md — django__django-13810

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`implementation_loadPipeline` `Id.run do` loop, the deep `stageMode`/`adaptedMode`
models, and the `wireStage`/`assemble` fold) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (deep-modeled callee —
**A-reference** where a deep model is validated `==` the real callee by G-AX), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves. `patch.diff` is the gold
patch **verbatim** (G-RESOLVE).

## A. The chain-assembly site — `load_middleware` (`django/core/handlers/base.py:39-89`)

Gold hunk:
```
-                handler = self.adapt_method_mode(
+                adapted_handler = self.adapt_method_mode(
                     middleware_is_async, handler, handler_is_async, ...)
-                mw_instance = middleware(handler)
+                mw_instance = middleware(adapted_handler)
             except MiddlewareNotUsed as exc:
                 ...
                 continue
+            else:
+                handler = adapted_handler
```

The gold edit renames the adapter's output to a fresh local and only commits it
to the loop-carried `handler` in the no-exception `else:` branch, so a stage that
raises `MiddlewareNotUsed` (and `continue`s) leaves the running handler
untouched.

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `init : Chain`, `stages : List Stage` | `self` (carrying `handler`/`handler_is_async`), `reversed(settings.MIDDLEWARE)` | R | `is_async` ↔ `init.flag = init.hmode`; each processed middleware ↔ `stages[i]` (mapping §2). G-CONF bridges via the capability/usable booleans. |
| A2 | `let target := stageMode chain.flag s` | the `if/elif/else` choosing `middleware_is_async` (`base.py:43-51`) | A-reference + I | the selection ladder modeled directly as `stageMode`; concrete (I), and its equality to the real ladder over stages with `canSync ∨ canAsync` is the A-reference G-AX validates (mapping §3.2). |
| A3 | `let amode := adaptedMode chain.hmode chain.flag target` | `self.adapt_method_mode(middleware_is_async, handler, handler_is_async, …)`'s effect on the handler's actual mode (`base.py:54-56`) | A-reference | the unchanged adapter modeled deeply: `adaptedMode` IS the running chain's actual mode after coercion to `target`. G-AX validates `adaptedMode == adapt_method_mode` (mapping §3.1). |
| A4 | `chain := if s.usable then { flag := target, hmode := amode } else chain` | `mw_instance = middleware(adapted_handler)`; on success `else: handler = adapted_handler` and `handler_is_async = middleware_is_async` (`base.py:89`); on `MiddlewareNotUsed` `continue` (running handler untouched) | I | the control/data flow of the gold hunk exactly: an installed stage advances BOTH the recorded mode (`flag := target`, the `base.py:89` write) and the actual mode (`hmode := amode`, the `else: handler = adapted_handler` write); a declined stage (`usable = false`) leaves the running chain unchanged — the gold `else`-branch frame. |
| A5 | `assemble`/`wireStage` fold via the `Id.run` `for s in stages` loop | the `for middleware_path in reversed(settings.MIDDLEWARE)` loop | I | left-to-right fold; G-CONF transliterates it and diffs against the real loop. |
| A6 | `init.consistent → result.consistent` (postcondition) | the health condition the gold hunk restores: `handler_is_async == iscoroutinefunction(handler)` at every step and at the final `adapt_method_mode(is_async, handler, handler_is_async)` (`base.py:92`) | I | the assembled chain runs in the mode it reports; this is what makes the async F2P test await a coroutine rather than a `HttpResponse`. |

Discriminating content — on a DECLINED stage the running chain must be left
untouched — lives in `wireStage`'s `else chain` (model) ⇔ the gold's moving
`handler = adapted_handler` into the no-exception `else:` (real).
`Solution_prepatch.lean` reproduces the pre-patch data-flow in its impl `do`
block (`else { flag := chain.flag, hmode := amode }`: a declined stage commits
the adapter's coercion to the actual mode while leaving the recorded mode behind)
and **fails** G-VERIFY exactly because the assembled chain no longer equals
`assemble init stages` and the `result.consistent` conjunct is broken when a
declined stage would have flipped the actual mode. `conformance_check.py`
confirms this pre-patch data-flow diverges from the post-patch oracle on the
fuzzed inputs (`skip_path_exercised`).

## B. No second independently-fixed behaviour

The patch is a single hunk at one site; there is exactly one independently
observable fixed behaviour (the skip-path frame), so one failing prepatch
suffices (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The two operations the changed function CALLS but does
not change — the mode-selection ladder and `adapt_method_mode` — are modeled
DEEPLY (`stageMode`, `adaptedMode` in the `pure` region), each an A-reference
validated `==` the real callee by G-AX, not hidden behind an axiom. There is no
consumed axiom: the property is a pure control/data-flow over the read-only
`stages` list.

## D. verify(Solution) ⇒ resolved

`loadPipeline` verifies only if (A4) an installed stage advances recorded and
actual modes together and a declined stage leaves the chain untouched, AND (A6)
the assembled chain is consistent given a consistent base. By R (`is_async ↔
init.flag = init.hmode`, capability/usable booleans) the verified assembler is
the gold `load_middleware`'s loop; by G-AX the deep models `stageMode` /
`adaptedMode` equal the real ladder / `adapt_method_mode` (A-reference); by
G-CONF the R/I transliteration of the fold agrees with the post-patch
`load_middleware`'s observable chain consistency over the fuzzed configuration
space. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and audited callees — and the gold patch
resolves (G-RESOLVE). The async F2P test passes precisely because the assembled
chain is consistent, so the final chain is the coroutine the ASGI path awaits.
