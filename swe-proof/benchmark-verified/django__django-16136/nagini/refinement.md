# refinement.md — django__django-16136

The operation-by-operation correspondence between `model.py`'s implementation
(the `method_not_allowed` impl region, with the `Reply` / `Delivered` minimal
objects) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `Ensures`, **A-reference** where a deep model is validated == the real
callee/mechanism by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The delivery site — `View.http_method_not_allowed` (`django/views/generic/base.py:144`)

Gold hunk:
```
-        return HttpResponseNotAllowed(self._allowed_methods())
+        response = HttpResponseNotAllowed(self._allowed_methods())
+
+        if self.view_is_async:
+
+            async def func():
+                return response
+
+            return func()
+        else:
+            return response
```

| # | model.py impl op (`method_not_allowed`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `async_mode: bool` | the `self.view_is_async` read in `if self.view_is_async:` | R | `bool` ↔ `bool`; the unchanged `@classproperty` read is hoisted to an input (mapping.md §2). The patch only branches on it; it does not change the property. |
| A2 | parameter `allowed_methods: List[int]` | `self._allowed_methods()` | R | unchanged callee result; `list[str]` ↔ `List[int]` of opaque method tokens (mapping.md §2). Carried, never inspected. |
| A3 | `response = Reply(allowed_methods)` | `response = HttpResponseNotAllowed(self._allowed_methods())` | R | the response object ↔ `Reply` carrying only the touched field (its permitted-method list); the patch does not change the response class (mapping.md §2). |
| A4 | `if async_mode:` … `else:` | `if self.view_is_async:` … `else:` | I | identical control flow on the same boolean. |
| A5 | async branch: `result = Delivered(True, response)` | `async def func(): return response; return func()` | A-reference | the changed delivery operation is modeled **deeply**: calling an `async def` returns a coroutine (`asyncio.iscoroutine(...) is True`) whose resolved value is `response`. `Delivered(True, response)` reifies exactly those two facts (`is_awaitable == True`, `reply is response`). There is no consumed axiom; G-AX (axiom_check.py) runs the real `async def`-wrap construct and asserts `asyncio.iscoroutine(return) is True` and `asyncio.run(return) is response` (mapping.md §3.1). |
| A6 | sync branch: `result = Delivered(False, response)` | `return response` | A-reference | a bare response object is **not** a coroutine (`asyncio.iscoroutine(...) is False`) and is itself the delivered reply. `Delivered(False, response)` reifies those two facts. G-AX asserts `asyncio.iscoroutine(return) is False` and the return is `response` (mapping.md §3.1). |
| A7 | `return result` | the two `return …` statements | I | the modeled function returns the `Delivered` reification of whatever the patched method returns. |

The discriminating content of the change — *the returned object is an awaitable
placeholder iff the view is async* — lives in the `if async_mode:` branch
producing `Delivered(True, …)` (model) ⇔ `return func()` for an `async def func`
(real). The pre-patch code returned the bare response unconditionally;
`model_prepatch.py` reproduces that (`Delivered(False, …)` regardless of
`async_mode`) and **fails** the postcondition
`Result().is_awaitable == async_mode`, which is exactly the spec sensing the
change on the async-view case (G-DIFF).

## B. The reply-preservation obligation

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `Ensures(Result().reply.methods is allowed_methods)` | the `response` object is the SAME in both branches (built once, line 151) and is what is delivered (directly, or as the coroutine's resolved value) | I + A-reference | the reply delivered in both modes is the one not-allowed response carrying `self._allowed_methods()`. Deciding the delivery convention does not change which reply is delivered. G-AX confirms `asyncio.run(func())` returns the same `response` object that the sync branch returns, carrying the given methods. This is the second half of the F2P assertion (`isinstance(response, HttpResponseNotAllowed)` after `asyncio.run`). |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — conditionally wrapping the reply in an awaitable — is modeled
**deeply** (the `if view_is_async:` branch building `Delivered(True/False, …)`,
steps A5/A6, **A-reference**), not hidden behind an axiom about the function
under change. There is **no consumed `@ContractOnly` axiom** in this bundle (the
`axioms` region is empty); the deep model is validated == the real `async def`
wrap mechanism by G-AX. Nagini cannot represent real coroutine objects, so the
two caller-observable facts (`asyncio.iscoroutine` and the `asyncio.run`-resolved
value) are reified as the `Delivered.is_awaitable` / `Delivered.reply` fields and
checked against the real mechanism out-of-band (mapping.md §3.1).

## D. verify(model) ⇒ resolved

`method_not_allowed` verifies only if its result is an awaitable placeholder
exactly when `async_mode` (A5/A6, the `Result().is_awaitable == async_mode`
clause) and only if the delivered reply carries the given permitted methods in
both modes (B1). By R (`bool` ↔ `bool`, response class unchanged, method-list
token encoding) and by G-AX (the deep model's two facts == the real `async def`
wrap / bare-return mechanism, A-reference), the verified function equals the gold
patch's delivery on the tested inputs: a coroutine resolving to the
`HttpResponseNotAllowed` for an async view, the bare `HttpResponseNotAllowed`
for a sync view — which is exactly what
`test_http_method_not_allowed_responds_correctly` checks. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited deep-model reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: deep-model /
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ); here there
is no consumed axiom, only the A-reference G-AX validates.
