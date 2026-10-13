# mapping.md — symbol binding & type bijection (django__django-16136)

## Modeled function
- **Lean** `implementation_disallowedResponse : Bool → List String → DisallowedResponse`
- **Python** `View.http_method_not_allowed(self, request, *args, **kwargs)` —
  `django/views/generic/base.py:144-151 @ base_commit` (the disallowed-method
  handler of the generic `View` base class).

The base (buggy) handler builds the HTTP-405 response and returns it directly:

```python
# base (buggy)
return HttpResponseNotAllowed(self._allowed_methods())
```

The patched handler mirrors the sibling `options()` handler: it builds the
response, then returns an awaitable wrapper around it when the view operates in
asynchronous mode, and the bare response otherwise:

```python
# patched
response = HttpResponseNotAllowed(self._allowed_methods())
if self.view_is_async:
    async def func():
        return response
    return func()
else:
    return response
```

## What is modeled
The observable behavior the F2P test pins (`test_http_method_not_allowed_responds_correctly`):
1. `asyncio.iscoroutine(response) is view_is_async` — the returned object is an
   awaitable/coroutine exactly when the view is async.
2. After awaiting (when async), the value is an `HttpResponseNotAllowed` carrying
   the allowed methods — identical in both modes.

The 405 response object is modeled by the `DisallowedResponse` structure with two
touched fields:
- `awaitable : Bool` — whether the returned object is an awaitable wrapper
  (= `asyncio.iscoroutine(result)`),
- `allowed : List String` — the permitted method names the response carries
  (= `self._allowed_methods()`).

`self.view_is_async` is the unchanged classproperty (`View.view_is_async`,
base.py:62-77); it is an input to the handler and is modeled by the `isAsync`
parameter. `self._allowed_methods()` (base.py:168-169) is likewise unchanged and
modeled by the `allowed` parameter. Neither is altered by the patch, so neither
is abstracted behind a Lean callee — both are read-only inputs.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `self.view_is_async` (bool) | `isAsync : Bool` | unchanged classproperty; async-mode flag |
| `self._allowed_methods()` (`list[str]`) | `allowed : List String` | unchanged; permitted method names |
| returned object | `result : DisallowedResponse` | the handler's return value |
| `asyncio.iscoroutine(result)` (bool) | `result.awaitable : Bool` | True iff an awaitable wrapper was returned |
| allowed methods carried by the (awaited) response | `result.allowed : List String` | the 405 payload, mode-independent |

## Callee provenance
- `HttpResponseNotAllowed(...)` is the unchanged response constructor; the patch
  does not change which methods it carries, so its payload is reproduced
  concretely as the `allowed` field (R/I), not axiomatized.
- `self.view_is_async` and `self._allowed_methods()` are unchanged inputs (read
  only); modeled as parameters, no callee property consumed.
- No UNCHANGED callee property is consumed: the axioms region is empty; G-AX is a
  skip stub.

## Flag dependency
The branch is gated on `self.view_is_async`. G-CONF fuzzes both `isAsync ∈
{False, True}` configurations so the discriminating async branch is exercised.

## G-CONF fuzz seed
Pinned seed: **16136**. ≥10^5 fuzzed inputs over `(isAsync, allowed)` pairs:
`isAsync` drawn uniformly from `{False, True}`, `allowed` a random list of
method-name tokens (incl. empty). The oracle observes coroutine-ness via real
`asyncio.iscoroutine` after running the patched control flow, exactly as the F2P
test does.
