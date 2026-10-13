# mapping.md — django__django-16136

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 19e6efa50b603af325e7f62058364f278596758f`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the one callee this routine consumes.

Repo file under change: `django/views/generic/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `notAllowedResponse (asynchronous : Bool) (allowed : List String)` | `View.http_method_not_allowed(self, request, *args, **kwargs)` — `django/views/generic/base.py:142` (changed body lines 151–159 post-patch) | the modeled changed function (the 405 "method not allowed" handler) |
| `asynchronous : Bool` | `self.view_is_async` — the `classproperty` `View.view_is_async` (`django/views/generic/base.py:60`), read inside the handler | whether the view runs asynchronously |
| `allowed : List String` | `self._allowed_methods()` — `django/views/generic/base.py:161` | the permitted-methods list passed to `HttpResponseNotAllowed` |
| `NotAllowed` (structure, field `allowed`) | the `HttpResponseNotAllowed(self._allowed_methods())` object | the 405 response; only its permitted-methods content is observed |
| `Delivery` (`immediate` / `awaitable`) | the object the handler `return`s — either `response` directly, or `func()` (a coroutine) | how the response is handed back |
| `deliverNotAllowed` (deep model — pure region) | the post-patch handler tail (lines 151–159): `response = HttpResponseNotAllowed(...)`; `if self.view_is_async: return func()` (coroutine) `else: return response` | pure spec of the delivery decision; modeled DEEPLY, not consumed as an axiom |

The pre-patch body the change replaces (refinement audit only, not in the
consumer spec view): the single statement
`return HttpResponseNotAllowed(self._allowed_methods())`
(`django/views/generic/base.py:151` pre-patch) — always the plain response
object, with no awaitable branch.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.view_is_async` (a `bool`) | `asynchronous : Bool` | `True` ↔ `true`, `False` ↔ `false` |
| `self._allowed_methods()` (a `list[str]`) | `allowed : List String` | element-wise `str` ↔ `String`; passed through verbatim — neither the handler nor the model inspects or reorders it |
| `HttpResponseNotAllowed(allowed)` | `NotAllowed { allowed }` | the response carries exactly the permitted-methods list; the F2P test observes only that the delivered object is an `HttpResponseNotAllowed`, i.e. a `NotAllowed` response |
| the returned object | `Delivery` | `return response` ↔ `Delivery.immediate resp`; `return func()` (an `async def func(): return response`, i.e. a coroutine) ↔ `Delivery.awaitable resp` |
| "is the returned object a coroutine?" — `asyncio.iscoroutine(response)` | `Delivery.isAwaitable` | the F2P test's `assertIs(asyncio.iscoroutine(response), is_coroutine)` ↔ `out.isAwaitable = asynchronous` |
| "the response obtained (directly or after awaiting) is a 405" — `asyncio.run(response)` then `assertIsInstance(..., HttpResponseNotAllowed)` | `Delivery.response` | awaiting the coroutine yields the wrapped `response` ↔ `out.response = { allowed := allowed }` |

The carriers are exact: the decision is a pure dispatch on one `Bool` and the
delivered object is one of two finite shapes wrapping the same response, so the
model is total and faithful.

## 3. Callee provenance — why there is NO axiom and NO A-reference

- `self._allowed_methods()` is an **unchanged** helper. The handler only passes
  its result into the 405 response; the change never touches it and the modeled
  behaviour does not depend on its contents. It is therefore taken as the
  read-only free input `allowed : List String`, owed no contract. Nothing to
  check against a real callee — hence **no axiom and no G-AX** for it.
- `self.view_is_async` is likewise an **unchanged** `classproperty`. Its value is
  taken as the read-only free input `asynchronous : Bool`. The spec holds for
  BOTH values, so again no contract is consumed.
- `async def func(): return response` / `HttpResponseNotAllowed(...)` are the
  delivery constructs the patch itself introduces. The changed behaviour — wrap
  in an awaitable iff async — is modeled **deeply** by `deliverNotAllowed`
  (`Delivery.awaitable` vs `Delivery.immediate`), NOT behind a consumed axiom.

Consequently `axioms` is empty, `deep_model_references` is empty, and
`axiom_check.py` is a no-op stub recording `status=skip` (meta.json
`gates.G-AX.status = "skip"`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16136`**. The R/I shadow
it builds transliterates `deliverNotAllowed` (the pure dispatch) to Python and
compares it against the post-patch handler tail transliterated verbatim, over
the full finite decision space (`asynchronous ∈ {False, True}` × sampled
`allowed` lists) plus seeded fuzz. There are no A-tagged callees in the computed
result, so the shadow is pure R/I.
