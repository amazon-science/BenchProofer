# mapping.md — django__django-13810

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 429d089d0a8fbd400e0c010708df4f0d16218970`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `django/core/handlers/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `loadPipeline (init : Chain) (stages : List Stage)` | `BaseHandler.load_middleware(self, is_async)` — `django/core/handlers/base.py:26` (assembly loop `base.py:39-89`) | the modeled changed function (middleware-chain assembler) |
| `Stage` | one entry of `reversed(settings.MIDDLEWARE)`: an imported middleware factory plus its capability flags | a configured pipeline stage |
| `Stage.canSync` | `getattr(middleware, 'sync_capable', True)` (`base.py:41`) | the stage's synchronous capability |
| `Stage.canAsync` | `getattr(middleware, 'async_capable', False)` (`base.py:42`) | the stage's asynchronous capability |
| `Stage.usable` | whether `middleware(handler)` constructs without raising `MiddlewareNotUsed` (`base.py:58-65`) | whether the stage installs itself or is skipped |
| `Chain.flag` | the loop-carried `handler_is_async` variable (`base.py:37,89`) | the mode the running chain is RECORDED to run in |
| `Chain.hmode` | the actual mode of the loop-carried `handler` callable (`asyncio.iscoroutinefunction(handler)`) | the mode the running chain ACTUALLY runs in |
| `stageMode (flag) (s)` | the `if/elif/else` mode-selection ladder choosing `middleware_is_async` (`base.py:43-51`) | the mode a stage is wired under, given the recorded chain mode |
| `adaptedMode (hmode flag target)` *(deep model — A-reference)* | `BaseHandler.adapt_method_mode(...)`'s effect on the running handler's actual mode (`base.py:54-56,97-122`) | the running chain's actual mode after the adapter coerces it to `target`; validated `adaptedMode == adapt_method_mode` by axiom_check.py (G-AX) |
| `wireStage` / `assemble` | one loop iteration / the whole `for middleware_path in reversed(settings.MIDDLEWARE)` fold (`base.py:39-89`) | wire one stage / assemble the chain |
| `Chain.consistent` | the health condition `handler_is_async == iscoroutinefunction(handler)` the assembler must preserve | recorded mode equals actual mode |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `settings.MIDDLEWARE`, consumed in processing order `reversed(MIDDLEWARE)` | `stages : List Stage` | the i-th processed middleware ↔ `stages[i]`; processing order is the fold order |
| `sync_capable` / `async_capable` class attributes (bool, defaults `True`/`False`) | `Stage.canSync` / `Stage.canAsync` (`Bool`) | identity on booleans; the `getattr(..., default)` defaults are applied before the value reaches the carrier |
| "the stage raises `MiddlewareNotUsed` from `__init__`" | `Stage.usable = false` | `usable = not raises_MiddlewareNotUsed`; identity otherwise |
| `is_async` argument of `load_middleware` | `init.flag` AND `init.hmode` | the base chain `convert_exception_to_response(get_response)` is built in mode `is_async` and recorded as `is_async`, so it starts CONSISTENT: `init.flag = init.hmode = is_async` (the postcondition's `init.consistent` antecedent) |
| `handler_is_async` (bool) | `Chain.flag` (`Bool`) | identity on booleans |
| `iscoroutinefunction(handler)` (bool) | `Chain.hmode` (`Bool`) | identity on booleans |

A stage advertising NEITHER capability (`sync_capable = async_capable = False`)
triggers `raise RuntimeError` at `base.py:43-47` and aborts assembly before any
wiring; such a stage never reaches the fold, so the modeled `stages` list
contains only stages with `canSync ∨ canAsync` (axiom_check.py checks the
`RuntimeError` boundary; conformance_check.py excludes them, matching the real
callee that also aborts). This restriction is irrelevant to the modeled property
(consistency is preserved regardless), so it is not encoded as a hypothesis.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

No `opaque` callee and no `axiom <callee>_prop` are declared in Solution.lean.
The two primitives the assembler uses are modeled DEEPLY as plain `def`s in the
`pure` region and are A-references: each is validated value-for-value against the
real unchanged callee by axiom_check.py.

### 3.1 `adaptedMode` deep model ↔ `adapt_method_mode` (A-reference)
**Callee:** `BaseHandler.adapt_method_mode(is_async, method, method_is_async)`
(`base.py:97-122`), an UNCHANGED method the assembler calls. Source (base_commit,
unchanged by the patch):

```python
if is_async:
    if not method_is_async:
        return sync_to_async(method, thread_sensitive=True)   # -> async
elif method_is_async:
    return async_to_sync(method)                               # -> sync
return method                                                  # unchanged
```

In the assembler `method_is_async` is always passed explicitly as
`handler_is_async` (the recorded mode = `flag`) and `is_async` is the chosen
`target`. The returned callable's actual mode is therefore `target` when the
recorded mode `flag` differs from `target` (a `sync_to_async`/`async_to_sync`
wrap flips it), and the chain's current actual mode `hmode` when `flag == target`
(the `return method` no-op). That is exactly
`adaptedMode hmode flag target = if flag = target then hmode else target`.
axiom_check.py validates `adaptedMode` against `adapt_method_mode`'s actual-mode
effect over the consistent regime (`flag == hmode`) × `target` — exhaustive over
booleans.

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
false ∧ s.canSync) then false else s.canAsync` — a concrete transliteration (I),
validated by axiom_check.py over all `flag × canSync × canAsync` combinations
(and the `RuntimeError` boundary for the neither-capable stage).

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`13810`**. The R/I shadow
transliterates `stageMode`/`wireStage`/`assemble` and diffs the final assembled
chain's `(recorded, actual)` mode pair against the POST-PATCH `load_middleware`
assembly loop reproduced verbatim in mode-tracking form (the oracle). The
deep-model callee `adaptedMode` (A-reference) is left as the real
`adapt_method_mode` actual-mode effect in the oracle leg (G-AX owns its
soundness). The fuzzer spans `is_async ∈ {False, True}` and 0..8-stage lists over
the capability/usable abstraction; it also confirms the discriminating skip path
is exercised (`skip_path_exercised`).
