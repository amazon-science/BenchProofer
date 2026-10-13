# refinement.md — operation correspondence (django__django-16136)

Maps every op in `implementation_disallowedResponse` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The patched Python adapts `View.http_method_not_allowed` so that the HTTP-405
response is wrapped in an awaitable when the view is async (mirroring `options()`),
and returned directly when sync. The modeled function decides the returned
object's awaitable-ness and its permitted-method payload.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `isAsync : Bool` | `self.view_is_async` | R | bool ↔ Bool; unchanged async-mode classproperty read as input (mapping.md) |
| 2 | `allowed : List String` | `self._allowed_methods()` | R | `list[str]` ↔ `List String`; unchanged permitted-methods list read as input |
| 3 | `let response := { awaitable := false, allowed := allowed }` | `response = HttpResponseNotAllowed(self._allowed_methods())` | R/I | construct the 405 response carrying the permitted methods; not-yet-wrapped (bare) value |
| 4 | `if isAsync then return { response with awaitable := true }` | `if self.view_is_async: async def func(): return response; return func()` | R | the **changed op**: in async mode return an awaitable wrapper around the response. `asyncio.iscoroutine(result)` ↔ `result.awaitable = true`; the wrapped value's payload is unchanged (`response`) |
| 5 | `else return response` | `else: return response` | I | in sync mode return the bare response directly (awaitable stays false) |

No A-consumed rows: the proof discharges the two-field postcondition
(`awaitable = isAsync`, `allowed = allowed`) directly by case analysis on
`isAsync`; no UNCHANGED callee property is assumed (axioms region empty, G-AX is
a skip stub).
No A-reference rows: the response constructor and the allowed-methods list are
unchanged context reproduced concretely as R/I ops, not abstracted behind a model
needing G-AX validation. No changed-inexpressible op.

The discriminating clause is row 4 (the async branch). The prepatch impl always
returns the bare response (`awaitable = false`), so on `isAsync = true` it returns
`awaitable = false` while `problem_spec_disallowedResponse` requires
`result.awaitable = isAsync = true`. Hence the prepatch `correct_disallowedResponse`
cannot close on that clause — the G-DIFF signal. (In sync mode both impls agree;
the bug is observable only in async mode, exactly as the F2P test asserts.)
