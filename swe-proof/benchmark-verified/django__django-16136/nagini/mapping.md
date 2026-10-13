# mapping.md — django__django-16136

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 19e6efa50b603af325e7f62058364f278596758f`, states the type
abstraction, and gives the provenance of the (one) deep-model reference.

Repo file under change: `django/views/generic/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `method_not_allowed(async_mode, allowed_methods)` | `View.http_method_not_allowed(self, request, *args, **kwargs)` — `django/views/generic/base.py:144` | the modeled changed function |
| `async_mode` (param) | `self.view_is_async` — `django/views/generic/base.py:62-77` (the `@classproperty` read at line 153 post-patch) | unchanged async-mode flag the patched branch tests; an input here |
| `allowed_methods` (param) | `self._allowed_methods()` — `django/views/generic/base.py:168-169` | unchanged list of permitted method tokens; an input here |
| `Reply` (class, field `methods`) | `HttpResponseNotAllowed(self._allowed_methods())` — built at `base.py:151` (pre) / `base.py:151` (post) | the not-allowed reply object; only the touched field (its permitted-method list) is modeled |
| `Delivered` (class, fields `is_awaitable`, `reply`) | the *value returned* by `http_method_not_allowed` — either the bare response (sync) or the coroutine `func()` (async) | the two observable facts a caller checks: whether the return is an awaitable (coroutine) placeholder, and the reply it delivers |

The logging call at `base.py:145-150` (`logger.warning(...)`) is unchanged by
the patch, has no observable effect on the return value the F2P test inspects,
and is omitted from the model (it is not part of the modeled return behaviour).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.view_is_async` (`bool` from the `@classproperty`) | `async_mode: bool` parameter | identity on `bool`; the property read is hoisted to an input (the patch does not change the property, only branches on it) |
| `self._allowed_methods()` (`list[str]` of upper-cased method names) | `allowed_methods: List[int]` | the method-name list ↔ a `List[int]` of opaque method tokens; the patch never inspects the contents, only carries the list, so any 1:1 token encoding is faithful |
| `HttpResponseNotAllowed(methods)` | `Reply(methods)` | the response object ↔ a minimal object carrying only its permitted-method list (the only touched field); the patch does not change the response class, only how the object is delivered |
| return value: bare `response` (sync) / `func()` coroutine (async) | `Delivered(is_awaitable, reply)` | `asyncio.iscoroutine(return) == is_awaitable`; the resolved/direct value ↔ `reply`. The F2P test reads exactly these two facts (`asyncio.iscoroutine(response)` and, after `asyncio.run`, `isinstance(response, HttpResponseNotAllowed)`). |

`Delivered` reifies, as two plain fields, the two facts the F2P test observes
through `asyncio.iscoroutine` / `asyncio.run`; Nagini cannot model real
coroutine objects, so the "is this an awaitable placeholder?" fact is carried
as the `is_awaitable` boolean and the "what does it resolve to?" fact as the
`reply` reference. The refinement (refinement.md) ties each model construct to
the patched delivery op.

## 3. Deep-model reference (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `method_not_allowed` / `Delivered` deep model ↔ the gold delivery (A-reference)

The one operation that *changed* — wrapping the reply in an awaitable when the
view is async — is modeled **deeply** (the `if view_is_async:` branch in the
impl, constructing `Delivered(True, …)` vs `Delivered(False, …)`); there is
**no consumed `@ContractOnly` axiom**. The deep model is validated equal to the
real delivery mechanism out-of-band by axiom_check.py (G-AX).

**Real mechanism** (gold patch, `django/views/generic/base.py:151-160`,
identical in shape to the pre-existing `View.options` at `base.py:159-166`):

```python
response = HttpResponseNotAllowed(self._allowed_methods())
if self.view_is_async:

    async def func():
        return response

    return func()
else:
    return response
```

Calling an `async def` returns a **coroutine object**, for which
`asyncio.iscoroutine(...)` is `True`; awaiting/`asyncio.run`-ing it yields the
captured `response`. A bare `HttpResponseNotAllowed` instance is **not** a
coroutine (`asyncio.iscoroutine(...)` is `False`). Hence the value returned is
an awaitable placeholder **exactly when** `self.view_is_async` is `True`, and in
both modes the delivered reply is the same `HttpResponseNotAllowed` carrying
`self._allowed_methods()`. This is exactly what `Delivered.is_awaitable ==
view_is_async` and `Delivered.reply.methods is allowed_methods` encode.

**Soundness check (G-AX):** `axiom_check.py` reproduces the real delivery
construct with stdlib-only code (an `async def func(): return response` wrap,
gated on the async flag — the same construct the patch uses; the response class
is stood in by a minimal object since the patch does not change it) and asserts,
on 10 boundary + 4000 randomized fuzz inputs, the three facts via the very
predicates the F2P test uses: `asyncio.iscoroutine(return) == view_is_async`,
and after `asyncio.run` the delivered object is the reply carrying the given
permitted-method list. It imports only `asyncio` and `random` (the same
machinery the gold patch relies on); nothing repo-specific. Exit 0 iff sound.

There is no flag dependency: the construct's coroutine-ness follows from
`async def` and Python's `asyncio.iscoroutine`, independent of configuration.
