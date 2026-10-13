# refinement.md — operation correspondence (django__django-13344)

Maps every op in `implementation_initComponent` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-CONF/G-AX) · **I** identical op.

The fix replaces each middleware constructor's inline prologue
(`self._get_response_none_deprecation(get_response); self.get_response =
get_response`, with the async check omitted) by a single delegation to the
shared base constructor `super().__init__(get_response)`. That base constructor
(`MiddlewareMixin.__init__`) runs three steps: the missing-handler notice, the
handler store, and the async-capability check (`self._async_check()`). The
pre-patch bug is precisely the *omission* of the async check in the five
subclass constructors. We model the shared post-patch behavior once.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `handler : Option Handler` | `get_response` (callable or `None`) | R | `None ↔ none`; a present handler observed only through `isAsync` (mapping.md bijection). |
| 2 | `if handler.isNone then missingFlag := true` | `self._get_response_none_deprecation(get_response)` (notice iff `get_response is None`) | A-reference | the unchanged notice callee modeled deeply as `Option.isNone`; validated by G-CONF against the real `is None` predicate. Unchanged by the fix (called pre- and post-patch). |
| 3 | `let stored := handler` | `self.get_response = get_response` (inside `super().__init__`) | I | store the handler verbatim. |
| 4 | `if handlerIsAsync stored then async := true` | `self._async_check()` — sets the async marker iff `asyncio.iscoroutinefunction(self.get_response)` | A-reference | the async-capability check modeled deeply as `Handler.isAsync` (= `iscoroutinefunction`). This is the behavior the fix RESTORES; validated by G-CONF against the real predicate. NOT axiomatized. |
| 5 | `return { handler, missingHandlerFlagged, reportsAsync }` | constructed instance with `.get_response`, notice side effect, and `_is_coroutine` marker | I | assemble the observable construction state. |

No A-consumed rows: the proof discharges the three conjuncts of
`problem_spec_initComponent` directly from the impl; no UNCHANGED-callee
*property* is assumed as an axiom. No changed-inexpressible op.

The discriminating clause is row 4 (`reportsAsync = handlerIsAsync handler`).
The prepatch impl hard-codes `async := false` (the real bug: the async check is
never run), so its `correct_initComponent` cannot close against the frozen
`problem_spec_initComponent` on an async handler (where the spec demands
`reportsAsync = true`). That is the G-DIFF signal, and it is exactly what F2P
`test_coroutine` exercises.
