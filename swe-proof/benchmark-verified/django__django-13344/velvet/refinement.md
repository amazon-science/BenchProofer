# refinement.md — django__django-13344

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`initMiddleware` `do` block and the deep `construct` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized /
deeply-modeled callee — **A-consumed** where the proof uses an axiom's `ensures`,
**A-reference** where a deep model is validated == the real callee by G-AX), or
**I** (identical concrete op).

The R/I legs would be mechanically refuted by **G-CONF**; here the impl region is
all-A-tagged so G-CONF is skipped (conf_skip=true, mapping.md §4) and the A leg
is audited by **G-AX**. The narrative is audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The construction site — the five changed `__init__` constructors

The five changed constructors (`SecurityMiddleware`, `SessionMiddleware`,
`UpdateCacheMiddleware`, `FetchFromCacheMiddleware`, `CacheMiddleware`) share one
behavioural skeleton. Representative gold hunk (`security.py`):

```
-        self._get_response_none_deprecation(get_response)
+        super().__init__(get_response)
         self.sts_seconds = settings.SECURE_HSTS_SECONDS
         ...
-        self.get_response = get_response
```

| # | Solution.lean impl op (`initMiddleware`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `handlerIsAsync : Bool` | the `get_response` handler argument | R | a callable `get_response` ↔ its async classification `Bool` (mapping.md §2). The behaviour observes only `asyncio.iscoroutinefunction(get_response)`. G-AX bridges the classification. |
| A2 | `out := construct handlerIsAsync` | `super().__init__(get_response)` — runs the canonical `MiddlewareMixin.__init__` → `_async_check`, recording async-capability on the instance | A-reference | the construction is modeled **deeply**: `construct` (pure region) IS the canonical routine's observable effect (`asyncCapable := handlerIsAsync`). The callee is the UNCHANGED `MiddlewareMixin.__init__`/`_async_check`; the patch merely makes the subclass delegate to it. Equality of the deep model to the real routine is the **A-reference** G-AX validates (mapping.md §3.1). No consumed axiom; the function under change is the constructor, which is NOT axiomatized. |
| A3 | `return out` (`Middleware`, field `asyncCapable`) | the constructed `self` (whose `_is_coroutine`, set by `_async_check`, makes `iscoroutinefunction(self)` True iff the handler is async) | R | instance ↔ `{ asyncCapable := iscoroutinefunction(instance) }` (mapping.md §2); the F2P `test_coroutine` compares exactly this observable. |

Discriminating content of the change — a middleware built around an async
handler must itself report `asyncCapable = true`. This lives in
`out.asyncCapable = handlerIsAsync` (spec) ⇔ the `_async_check` step the
canonical routine performs (real), reached via `super().__init__`. The pre-image
inlined constructors set `self.get_response` and warned but SKIPPED
`_async_check`, so an async handler yielded a non-async middleware;
`Solution_prepatch.lean` reproduces that (`out := { asyncCapable := false }`) and
**fails** `out.asyncCapable = handlerIsAsync` for an async handler (G-DIFF).

## B. Multi-site note

All five changed constructors are modeled by the single `initMiddleware` because
they share one observable behavioural change (build through the canonical routine
so async-capability is recorded). The F2P `test_coroutine` exercises the same
discriminating clause for every one of them; pre-patch, the four that inlined the
prologue (`SecurityMiddleware`, `UpdateCacheMiddleware`, `FetchFromCacheMiddleware`,
`CacheMiddleware`) fail identically (verified in-container). `SessionMiddleware`
additionally dropped an explicit `_async_check()` call in its inline body; the
gold patch's `super().__init__` restores it — the same modeled clause. One
prepatch suffices because there is one independently-observable fixed behaviour
(async-capability recording), shared by all sites.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely changed — delegating
construction to the canonical routine so async-capability is recorded — is
modeled by the **A-reference** `construct` (step A2), the deep model of the
UNCHANGED callee `MiddlewareMixin.__init__`/`_async_check`, validated == the real
routine by G-AX. There is no consumed axiom, and the function under change (the
constructor) is itself the modeled `method`, never axiomatized. The impl region
is all-A-tagged → G-CONF skipped (conf_skip=true).

## D. verify(Solution) ⇒ resolved

`initMiddleware` verifies only if its output satisfies
`out.asyncCapable = handlerIsAsync` (A2/A3): an async handler yields an
async-capable middleware, a sync handler a non-async one. By R
(`handler ↔ handlerIsAsync`, `instance ↔ asyncCapable`) the verified construction
equals `super().__init__(get_response)`'s observable on the tested handlers; by
G-AX the deep model `construct` equals the real canonical routine (A-reference).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited unchanged callee — and the gold patch
resolves (G-RESOLVE). Trust points: A-reference soundness (G-AX, §3.1) and
refinement fidelity (this doc, G-EQ).
