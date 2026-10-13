# mapping.md — django__django-13810

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 429d089d0a8fbd400e0c010708df4f0d16218970`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `django/core/handlers/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `loadPipeline (init : Chain) (stages : List Stage)` | `BaseHandler.load_middleware(self, is_async)` — `django/core/handlers/base.py:26` (assembly loop at `base.py:39-89`) | the modeled changed function (middleware-chain assembler) |
| `Stage` | one entry of `reversed(settings.MIDDLEWARE)`: the imported middleware factory plus its capability flags | a configured pipeline stage |
| `Stage.canSync` | `getattr(middleware, 'sync_capable', True)` (`base.py:41`) | the stage's synchronous capability |
| `Stage.canAsync` | `getattr(middleware, 'async_capable', False)` (`base.py:42`) | the stage's asynchronous capability |
| `Stage.usable` | whether `middleware(handler)` constructs without raising `MiddlewareNotUsed` (`base.py:58-65`) | whether the stage installs itself or is skipped |
| `Chain.flag` | the loop-carried `handler_is_async` variable (`base.py:37,89`) | the execution mode the running chain is RECORDED to run in |
| `Chain.hmode` | the actual execution mode of the loop-carried `handler` callable (`asyncio.iscoroutinefunction(handler)`) | the mode the running chain ACTUALLY runs in |
| `stageMode (flag) (s)` | the `if/elif/else` mode-selection ladder choosing `middleware_is_async` (`base.py:43-51`) | the mode a stage is wired under, given the recorded chain mode |
| `adaptedMode (hmode flag target)` *(deep model — A-reference)* | `BaseHandler.adapt_method_mode(...)`'s effect on the running handler's actual execution mode (`base.py:54-56,97-122`) | pure spec: the running chain's actual mode after the adapter coerces it to `target`; validated `adaptedMode == adapt_method_mode` (consistent regime) by axiom_check.py (G-AX) |
| `wireStage` / `assemble` | one loop iteration / the whole `for middleware_path in reversed(settings.MIDDLEWARE)` fold (`base.py:39-89`) | wire one stage / assemble the chain |
| `Chain.consistent` | the implicit health condition `handler_is_async == iscoroutinefunction(handler)` the assembler must preserve | recorded mode equals actual mode |

The pre-patch defect (refinement audit only, not in the consumer spec view):
`base.py:54` overwrites the loop-carried `handler` with the adapted callable
BEFORE the `try` knows whether the stage installs; on the `except
MiddlewareNotUsed: … continue` path (`base.py:59-65`) that overwrite is carried
forward while `handler_is_async` (set only at `base.py:89`, never reached on the
skip) is left behind — desyncing recorded mode from actual mode and mis-wiring
every later stage. The gold fix moves the commit to the no-exception `else:
handler = adapted_handler` branch.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `settings.MIDDLEWARE` (a list of dotted paths), consumed in **processing order** `reversed(MIDDLEWARE)` | `stages : List Stage` | the i-th processed middleware ↔ `stages[i]`; `len(reversed(MIDDLEWARE))` ↔ `stages.length`; processing order is the fold order |
| `sync_capable` / `async_capable` class attributes (bool, defaults `True`/`False`) | `Stage.canSync` / `Stage.canAsync` (`Bool`) | identity on booleans; the `getattr(..., default)` defaults are applied before the value reaches the carrier |
| "the stage raises `MiddlewareNotUsed` from `__init__`" | `Stage.usable = false` | `usable = not raises_MiddlewareNotUsed`; identity otherwise |
| `is_async` argument of `load_middleware` | `init.flag` AND `init.hmode` | the base chain `convert_exception_to_response(get_response)` is built in mode `is_async` and recorded as `is_async`, so it starts CONSISTENT: `init.flag = init.hmode = is_async` (the `require`) |
| `handler_is_async` (bool) | `Chain.flag` (`Bool`) | identity on booleans |
| `iscoroutinefunction(handler)` (bool) | `Chain.hmode` (`Bool`) | identity on booleans |

A stage that advertises NEITHER capability (`sync_capable = async_capable =
False`) triggers `raise RuntimeError` at `base.py:43-47` and aborts assembly
before any wiring; such a stage never reaches the fold, so the modeled `stages`
list contains only stages with `canSync ∨ canAsync` (G-AX checks the
`RuntimeError` boundary; G-CONF excludes them, matching the real callee that
also aborts). This restriction is irrelevant to the modeled property
(consistency is preserved regardless), so it is not encoded as a `require`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `adaptedMode` deep model ↔ `adapt_method_mode` (A-reference)
**Callee:** `BaseHandler.adapt_method_mode(is_async, method, method_is_async)`
(`base.py:97-122`), an UNCHANGED method the assembler calls. Its effect on the
running chain that matters to the assembly invariant is the actual execution
mode of the returned callable. Source (base_commit, unchanged by the patch):

```python
def adapt_method_mode(self, is_async, method, method_is_async=None, debug=False, name=None):
    if method_is_async is None:
        method_is_async = asyncio.iscoroutinefunction(method)
    ...
    if is_async:
        if not method_is_async:
            return sync_to_async(method, thread_sensitive=True)   # -> async
    elif method_is_async:
        return async_to_sync(method)                               # -> sync
    return method                                                  # unchanged
```

In the assembler `method_is_async` is always passed explicitly as
`handler_is_async` (the recorded mode = `flag`) and `is_async` is the chosen
`target`. The returned callable's actual mode is therefore: `target` when the
recorded mode `flag` differs from `target` (a `sync_to_async`/`async_to_sync`
wrap flips it to `target`), and the chain's current actual mode `hmode` when
`flag == target` (the `return method` no-op leaves it). That is exactly
`adaptedMode hmode flag target = if flag = target then hmode else target`.

The changed operation is modeled **deeply** (`adaptedMode` spelled out in the
`pure` region); there is **no consumed `adapt` axiom**. G-AX validates
`adaptedMode == adapt_method_mode`'s actual-mode effect against the real callee.

**Note (consistent regime).** `adapt_method_mode` is only *called by a
well-formed assembler* when the chain is consistent (`flag == hmode == actual`);
in that regime the real callee is total and `adaptedMode` matches it exactly
(G-AX checks all four `flag==hmode` × `target` combinations). When `flag !=
actual` the real `asgiref` adapter raises `TypeError` ("sync_to_async can only
be applied to sync functions") — which is precisely the runtime poisoning the
pre-patch produces and the spec's `out.consistent` postcondition forbids.

### 3.2 `stageMode` ↔ the `middleware_is_async` selection ladder (A-reference / I)
**Callee:** the inline `if/elif/else` at `base.py:43-51`:

```python
if not middleware_can_sync and not middleware_can_async:
    raise RuntimeError(...)                       # excluded from `stages` (§2)
elif not handler_is_async and middleware_can_sync:
    middleware_is_async = False
else:
    middleware_is_async = middleware_can_async
```

Over stages with `canSync ∨ canAsync` this is `stageMode flag s = if (flag =
false ∧ s.canSync) then false else s.canAsync` — a concrete transliteration
(I), validated by G-AX over all `flag × canSync × canAsync` combinations.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13810`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `stageMode`/`wireStage`/`assemble` (R/I-tagged ops) to Python and
runs the REAL `BaseHandler.load_middleware` at the gold commit as the oracle,
observing the assembled chain's consistency (`handler_is_async ==
iscoroutinefunction(self._middleware_chain)` plus per-stage consistency captured
by instrumenting `adapt_method_mode`). The deep-model callee `adaptedMode`
(A-reference) is left as the real `adapt_method_mode` in the oracle leg (G-AX
owns its soundness).
