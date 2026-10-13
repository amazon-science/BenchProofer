# refinement.md — django__django-13810

The operation-by-operation correspondence between `model.py`'s implementation
(the `assemble_chain` impl region and the deep `final_handler` / `final_async`
folds) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, the proof
uses the axiom's `Ensures`, and **A-reference**, a deep model validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`
and is the real correctness oracle, G-RESOLVE).

## A. The middleware-walk loop — `load_middleware` (`django/core/handlers/base.py:39-89`)

Gold hunk:
```
             try:
                 # Adapt handler, if needed.
-                handler = self.adapt_method_mode(
+                adapted_handler = self.adapt_method_mode(
                     middleware_is_async, handler, handler_is_async,
                     debug=settings.DEBUG, name='middleware %s' % middleware_path,
                 )
-                mw_instance = middleware(handler)
+                mw_instance = middleware(adapted_handler)
             except MiddlewareNotUsed as exc:
                 ...
                 continue
+            else:
+                handler = adapted_handler
```

| # | model.py impl op (`assemble_chain`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `target_mode: List[int]`, `declines: List[int]`, `base_async: int` | the loop's per-iteration inputs: `middleware_is_async` (`base.py:43-51`), the `MiddlewareNotUsed`-raise outcome of `middleware(...)` (`base.py:58`), and `handler_is_async = is_async` (`base.py:38`) | R | `bool` ↔ `int{0,1}`; the ordered middleware list ↔ parallel `List` columns indexed by visit order; the raise outcome ↔ `declines[i]` (mapping.md §2). The unchanged mode-selection arithmetic is abstracted as the `target_mode` input. |
| A2 | `handler = []` (the base handler trace); `handler_is_async = base_async` | `handler = convert_exception_to_response(get_response...)`; `handler_is_async = is_async` (`base.py:37-38`) | R | the base handler object ↔ the empty token trace `[]`; `handler_is_async` carries identically (mapping.md §2). |
| A3 | `adapted = handler + [ADAPT_TOKEN, target_mode[i]]` | `adapted_handler = self.adapt_method_mode(middleware_is_async, handler, handler_is_async, ...)` | A-reference | the unchanged callee `adapt_method_mode` is modelled **deeply** as `adapt_token` (it derives a FRESH handler, recorded as an appended adaptation token; it never mutates `handler`). The deep model is validated == the real callee's threading by G-AX (mapping.md §3.1). Note the gold assigns into the **fresh local `adapted_handler`**, not into `handler` — A3 mirrors that with the fresh local `adapted`. |
| A4 | `if declines[i] == 1: i = i + 1; continue` | `except MiddlewareNotUsed as exc: ... continue` | R + I | the decline path: the layer is skipped. Identical control flow (`continue`); the exception is abstracted to `declines[i]` (mapping.md §2). Crucially `handler` / `handler_is_async` are NOT reassigned on this path — matching the gold, where `handler = adapted_handler` lives only in the `else`, so the `continue` leaves the running state untouched. |
| A5 | `handler = adapted + [WRAP_TOKEN]` (participating path) | `else: handler = adapted_handler` (`base.py:66-67`) then `handler = convert_exception_to_response(mw_instance)` (`base.py:88`) | R + A-reference | the participating path commits the adapted handler into the running `handler`, then wraps it (`convert_exception_to_response`, modelled deeply as `wrap_token`). Composed, this is `committed_handler(handler, target_mode[i])` = `wrap_token(adapt_token(handler, target_mode[i]))`. The commit happens **only** when the layer did not decline — the gold's `else`. |
| A6 | `handler_is_async = target_mode[i]` (participating path) | `handler_is_async = middleware_is_async` (`base.py:89`) | R + I | the running async-mode flag advances to the layer's target mode, only on the participating path. |
| A7 | `return handler, handler_is_async` | the post-loop running pair fed to `self.adapt_method_mode(is_async, handler, handler_is_async)` / `self._middleware_chain` (`base.py:91-95`) | R + I | the assembled chain is the final running pair. The post-loop top-of-stack adaptation (`base.py:92`) is the same unchanged `adapt_method_mode` callee; it consumes exactly this pair, so pinning the pair pins what it receives. |

The discriminating content of the change — a **declining** layer must leave the
running `(handler, handler_is_async)` exactly as it was before that layer — lives
in A4/A5: the commit (`handler = adapted + [WRAP_TOKEN]`, the `else`-only
assignment) is reached only on the participating branch, so a declining layer's
tentative `adapted` is discarded. The pre-patch loop committed the adaptation
into `handler` *before* the decline check (`handler = adapt_method_mode(...)`
then `middleware(handler)`), so a declining layer poisoned the running handler.
`model_prepatch.py` reproduces that (`handler = handler + [ADAPT_TOKEN, ...]`
before the decline test, no rollback) and **fails** the loop invariant
`final_handler(ToSeq(handler), handler_is_async, ..., i) == final_handler([],
base_async, ..., 0)` — exactly the spec sensing the change (G-DIFF): the
declining branch then carries an extra adaptation token forward that the fold
does not account for.

## B. No consumed axiom; no kind-3 step

Every step above is R, A-reference, or I. There is **no consumed `@ContractOnly`
axiom** (the `axioms` region is empty): the two callees the walk invokes
(`adapt_method_mode`, `convert_exception_to_response`) are **unchanged**, and the
operation that genuinely *changed* — the *threading/rollback* of their results
across the loop — is modelled **deeply** (the `committed_handler` /
`final_handler` / `final_async` folds and the verified loop), not hidden behind
an axiom. Those callees appear only as the **A-reference** deep models
`adapt_token` / `wrap_token`, which G-AX validates against the real patched loop
semantics (mapping.md §3.1, axiom_check.py). No row is a "changed operation
Nagini cannot express" — the change is expressed directly.

## C. verify(model) ⇒ resolved

`assemble_chain` verifies only if its returned `(handler, handler_is_async)`
equals the fold that skips declining layers without carrying their tentative
adaptation forward (A4/A5/A6) — the postconditions
`ToSeq(Result()[0]) == final_handler([], base_async, ...)` and
`Result()[1] == final_async([], base_async, ...)`. By R (bool ↔ int{0,1},
handler-object ↔ token trace, ordered list ↔ parallel columns) and the A-reference
deep models validated == the real `adapt_method_mode` / `convert_exception_to_response`
threading (G-AX), the verified loop equals the gold patch's `load_middleware`
loop on the visited middleware. The gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: A-reference deep-model soundness (G-AX)
and refinement fidelity (this document, G-EQ).
