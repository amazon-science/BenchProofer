# refinement.md — django__django-16136

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`notAllowedResponse` `do` block + the deep `deliverNotAllowed` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (mapping.md §3). Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The 405 handler — `View.http_method_not_allowed` (`django/views/generic/base.py:142`)

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

| # | Solution.lean impl op (`notAllowedResponse`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `allowed : List String` | `self._allowed_methods()` value | R | `list[str]` ↔ `List String` (mapping.md §2). Unchanged callee's result, taken as a free input. |
| A2 | parameter `asynchronous : Bool` | `self.view_is_async` | R | `bool` ↔ `Bool` (mapping.md §2). Unchanged `classproperty`, taken as a free input. |
| A3 | `let resp : NotAllowed := { allowed := allowed }` | `response = HttpResponseNotAllowed(self._allowed_methods())` | R + I | constructing the 405 response carrying the permitted-methods list. `NotAllowed { allowed }` ↔ the `HttpResponseNotAllowed(...)` object (mapping.md §2); the construction op itself is I. |
| A4 | `if asynchronous then Delivery.awaitable resp else Delivery.immediate resp` | `if self.view_is_async: ... return func() else: return response` | I | the delivery dispatch: an awaitable in the async case, the plain response object otherwise. `Delivery.awaitable resp` ↔ `func()` (the `async def func(): return response` coroutine, an awaitable yielding `response`); `Delivery.immediate resp` ↔ `return response`. Concrete control/data flow, transliterated 1:1 by G-CONF. |
| A5 | `return out` (`Delivery`) | the `return func()` / `return response` statements | I | the handler's return value is exactly the chosen delivery. |

Discriminating content of the change — when `asynchronous` (`view_is_async`) is
true, the response is delivered as an **awaitable** (`Delivery.awaitable`,
i.e. `func()`), not the plain object — lives in clause `out.isAwaitable =
asynchronous` and `asynchronous = true → out = Delivery.awaitable {...}`. The
pre-patch body returned `HttpResponseNotAllowed(...)` unconditionally;
`Solution_prepatch.lean` reproduces that (`out := Delivery.immediate resp`) and
**fails** those clauses (G-DIFF), which is exactly the bug the F2P
`test_http_method_not_allowed_responds_correctly` observes
(`asyncio.iscoroutine(response)` must be `True` for `AsyncView`).

The companion F2P `test_mixed_views_raise_error` and the PASS_TO_PASS suite
exercise UNCHANGED machinery (`view_is_async`'s all-sync-or-all-async check,
`options()`); they are untouched by this patch and pass because the patch is a
strict, content-preserving addition to one handler — captured by the unchanged
frame: `out.response = { allowed := allowed }` (the 405 content is identical in
both delivery modes).

## B. No axioms / no A-reference

mapping.md §3: `_allowed_methods()` and `view_is_async` are unchanged callees,
modeled as read-only free inputs (`allowed`, `asynchronous`) with no contract
consumed; the changed delivery behaviour is modeled **deeply** by
`deliverNotAllowed`. There is no `axiom`, no A-consumed and no A-reference row,
so `axiom_check.py` is a `status=skip` stub.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — wrapping the
response in an awaitable when the view is async — is modeled **deeply** (the
`Delivery` sum + the `if asynchronous` dispatch, step A4), not hidden behind an
axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`notAllowedResponse` verifies only if its output (i) is an awaitable exactly when
`asynchronous` is true (`out.isAwaitable = asynchronous`), (ii) carries the 405
response listing `allowed` either way (`out.response = { allowed := allowed }`),
and (iii) takes the exact `awaitable`/`immediate` shape per branch. By R
(`bool ↔ Bool`, `list[str] ↔ List String`, `HttpResponseNotAllowed ↔ NotAllowed`,
`func()` coroutine ↔ `Delivery.awaitable`) the verified handler equals the gold
patch's tail on every input; by G-CONF the R/I transliteration of the dispatch
agrees with `patch.diff`'s behaviour on the full finite space + fuzz. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). There are no axioms,
so the single trust point is refinement fidelity (this doc, G-EQ + G-CONF).
