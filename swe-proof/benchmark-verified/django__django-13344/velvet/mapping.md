# mapping.md — django__django-13344

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e39e727ded673e74016b5d3658d23cbe20234d11`, states the type
abstraction (the bijection G-AX uses to bridge Lean↔Python), and gives the
provenance of the deeply-modeled callee.

Repo files under change (the changed functions delegate to an UNCHANGED
canonical routine): `django/contrib/sessions/middleware.py`,
`django/middleware/cache.py`, `django/middleware/security.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `initMiddleware (handlerIsAsync : Bool)` | the changed middleware constructors — `SecurityMiddleware.__init__` (`django/middleware/security.py:11`), `SessionMiddleware.__init__` (`django/contrib/sessions/middleware.py:15`), `UpdateCacheMiddleware.__init__` (`django/middleware/cache.py:66`), `FetchFromCacheMiddleware.__init__` (`django/middleware/cache.py:130`), `CacheMiddleware.__init__` (`django/middleware/cache.py:175`) | the modeled changed function: construct a middleware around its response handler. All five share one behavioural skeleton (build through the canonical routine), so one `method` models them. |
| `construct (handlerIsAsync : Bool)` *(deep model — A-reference)* | the UNCHANGED canonical construction routine `MiddlewareMixin.__init__` → `_async_check` (`django/utils/deprecation.py:94,100`) | pure spec: the canonical construction records the wrapped handler's async-capability on the result. Deep model of the unchanged callee, validated `construct == real routine` by axiom_check.py (G-AX), NOT a consumed axiom. |
| `Middleware` (`structure`, field `asyncCapable : Bool`) | a constructed middleware instance; `asyncCapable` ↔ `asyncio.iscoroutinefunction(instance)` | the observable face of a middleware: whether it advertises asynchronous operation. |

The pre-image repo code the change removes (refinement audit only, not in the
consumer spec view): the inlined constructor bodies that set
`self.get_response = get_response` and call `self._get_response_none_deprecation`
WITHOUT the async-capability registration step — e.g. `security.py:12-22`,
`cache.py:67-74`. The gold patch replaces each inlined body's
construction-prologue with `super().__init__(get_response)`, which runs the
canonical `MiddlewareMixin.__init__` (calling `_async_check`).

## 2. Type abstraction (the Lean↔Python bijection)

This is the table G-AX uses to translate values between the Lean value domain
and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the response handler `get_response` (a callable) | classified to `handlerIsAsync : Bool` | `handler` ↔ `asyncio.iscoroutinefunction(handler)`. The behaviour observes ONLY this one bit of the handler (whether it is a coroutine function); nothing else about the handler is relevant (the construction's async decision depends on exactly this). |
| a constructed middleware instance | Lean `Middleware` (only the touched field) | `instance` ↔ `{ asyncCapable := asyncio.iscoroutinefunction(instance) }`. The structure carries ONLY `asyncCapable` because that is the only field the desired behaviour and the F2P test (`test_coroutine`) observe; all other instance attributes (`cache`, `key_prefix`, `sts_seconds`, …) are orthogonal to this fix and out of the modeled frame. |
| `get_response = None` (the deprecation path) | not modeled | orthogonal: the deprecation-warning behaviour is unchanged by the fix (the canonical routine still warns), so it is outside the modeled frame. |

The handler is the read-only input (`handlerIsAsync` is NOT `mut`): construction
consumes its classification and never alters it (directive 5). The post-state of
the result is pinned exactly (`out = construct handlerIsAsync`,
`out.asyncCapable = handlerIsAsync`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `construct` deep model ↔ the unchanged canonical routine (A-reference)
**Callee:** `MiddlewareMixin.__init__` (`django/utils/deprecation.py:94`), which
calls `_async_check` (`:100`):

```python
def __init__(self, get_response=None):
    self._get_response_none_deprecation(get_response)
    self.get_response = get_response
    self._async_check()           # <-- records async-capability
    super().__init__()

def _async_check(self):
    if asyncio.iscoroutinefunction(self.get_response):
        self._is_coroutine = asyncio.coroutines._is_coroutine
```

Setting `self._is_coroutine` is exactly what makes
`asyncio.iscoroutinefunction(instance)` return True. So the constructed
middleware advertises asynchronous operation **iff** the wrapped handler is a
coroutine function — i.e. `asyncCapable = handlerIsAsync`, which is what
`construct` encodes. This routine is NOT changed by the patch; the patch makes
the five subclasses *delegate* to it (`super().__init__(get_response)`) instead
of inlining a prologue that skipped `_async_check`. Hence `construct` is an
**A-reference** (deep model of an unchanged callee), not a consumed axiom and not
the function-under-change.

**Soundness check (G-AX):** `axiom_check.py` instantiates the REAL
`MiddlewareMixin` on boundary handlers (plain async/sync functions, lambdas,
bound methods, async methods) plus 2000 randomized async/sync handlers and
asserts `asyncio.iscoroutinefunction(instance) == construct(handlerIsAsync).asyncCapable
== handlerIsAsync` in every case. Imports only stdlib `asyncio` + the unchanged
`django.utils.deprecation`. Exit 0 iff sound.

### 3.2 Flag/configuration dependence
None. The async classification depends only on the handler itself
(`asyncio.iscoroutinefunction`), with no settings flag, so G-AX fuzzes the
handler shape directly.

## 4. G-CONF — skipped (conf_skip=true)

The impl region of `initMiddleware` is the single A-reference call
`out := construct handlerIsAsync` (no R/I op). There is no input-dependent R/I
shadow to differential-test, so `meta.json conf_skip=true` and
`conformance_check.py` is a `status=skip` stub. The A leg is covered by G-AX
(§3.1); spec strength and discrimination by G-VERIFY and G-DIFF. No fuzz seed is
consumed by the skip stub; `axiom_check.py` pins its fuzz seed to **`13344`**.
