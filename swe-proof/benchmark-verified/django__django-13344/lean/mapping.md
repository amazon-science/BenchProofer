# mapping.md — symbol binding (django__django-13344)

## Instance summary
A request-processing component is constructed from an optional request handler.
The component declares itself capable of asynchronous operation. The defect: the
component's constructor failed to run the asynchronous-capability check, so a
component built from an *asynchronous* handler was NOT marked asynchronous. The
fix routes construction through the shared base constructor, which performs that
check. F2P `test_coroutine` is the discriminating behavior.

## Function under spec
The shared base-class initialization behavior that every patched constructor now
delegates to (`super().__init__(get_response)`):

  `django/utils/deprecation.py :: MiddlewareMixin.__init__`  (lines 94–98 @ base_commit)
    - `self._get_response_none_deprecation(get_response)`  (line 95) — emit a
      notice when no handler is supplied (`get_response is None`).
    - `self.get_response = get_response`                   (line 96) — store handler.
    - `self._async_check()`                                (line 97) — set the
      asynchronous marker when the handler is a coroutine function.

The patched constructors that now call this (gold patch.diff):
  - `django/contrib/sessions/middleware.py :: SessionMiddleware.__init__`  (l. 14 @ base)
  - `django/middleware/cache.py :: UpdateCacheMiddleware.__init__`         (l. 66 @ base)
  - `django/middleware/cache.py :: FetchFromCacheMiddleware.__init__`      (l. 130 @ base)
  - `django/middleware/cache.py :: CacheMiddleware.__init__`               (l. 174 @ base)
  - `django/middleware/security.py :: SecurityMiddleware.__init__`         (l. 11 @ base)

All five pre-patch constructors performed the deprecation notice + handler store
*inline* but omitted `_async_check()`. The fix is identical in all five
(delegate to the base constructor). We model the single shared behavior once;
its prepatch (omit the async check) is the common bug.

## Callees
- `_async_check()` (`MiddlewareMixin._async_check`, deprecation.py l.100):
  `if asyncio.iscoroutinefunction(self.get_response): self._is_coroutine = ...`.
  The observable effect is: the component is marked asynchronous iff the handler
  is a coroutine function. **A-reference** — modeled deeply; the underlying
  `asyncio.iscoroutinefunction` predicate is carried into the model as the input
  bit `Handler.isAsync`. Validated against the real callee by G-CONF.
- `_get_response_none_deprecation(get_response)` (deprecation.py l.141):
  emits the notice iff `get_response is None`. **A-reference** — modeled deeply
  as `handler.isNone`. Unchanged by the fix (called both pre- and post-patch);
  framed in the spec.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)
| Python | Lean |
|---|---|
| `get_response` (callable, possibly `None`) | `handler : Option Handler` (`none` ↔ `None`) |
| `asyncio.iscoroutinefunction(get_response)` | `Handler.isAsync : Bool` (the only observed property of a present handler) |
| constructed component instance | `Component` (structure) |
| `self.get_response` after init | `Component.handler` |
| `asyncio.iscoroutinefunction(instance)` (the `_is_coroutine` marker) | `Component.reportsAsync : Bool` |
| deprecation notice emitted during init | `Component.missingHandlerFlagged : Bool` |

`Handler` carries only `isAsync` because that is the sole property of the handler
the constructor's behavior depends on (`iscoroutinefunction`). The component's
subclass-specific configuration fields (settings reads) are unchanged by the fix
and orthogonal to the modeled behavior, so they are not part of the model.

## Flag dependencies
None. `iscoroutinefunction` takes no flag here.

## G-CONF fuzz seed
SEED = 13344 (pinned; see conformance_check.py).
