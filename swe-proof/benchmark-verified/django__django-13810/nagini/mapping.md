# mapping.md — django__django-13810

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 429d089d0a8fbd400e0c010708df4f0d16218970`, states the type
abstraction, and gives the provenance of the deeply-modelled callees.

Repo file under change: `django/core/handlers/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assemble_chain(target_mode, declines, base_async)` | `BaseHandler.load_middleware(self, is_async=False)` — `django/core/handlers/base.py:26` (body loop lines 39-89) | the modelled changed function: the loop that threads the running handler / async-mode flag across the ordered middleware list |
| `target_mode[i]` | `middleware_is_async` computed at `base.py:43-51` for the i-th visited middleware | per-layer target async mode (0=sync, 1=async) |
| `declines[i]` | whether `mw_instance = middleware(adapted_handler)` raises `MiddlewareNotUsed` at `base.py:58-65` for the i-th visited middleware | per-layer decline flag (1=raises `MiddlewareNotUsed`, 0=participates) |
| `base_async` | the initial `handler_is_async = is_async` at `base.py:38` | initial running async-mode flag |
| `handler` (model: `List[int]` token trace) | the running `handler` local at `base.py:37,54-57,88,92` | the running request handler object threaded across iterations |
| `handler_is_async` | the running `handler_is_async` local at `base.py:38,89` | the running async-mode flag threaded across iterations |
| `adapt_token(h, m)` *(deep model — A-reference)* | `BaseHandler.adapt_method_mode(...)` — `base.py:97` (called at `base.py:54`) | unchanged callee: derives a new handler in the target mode |
| `wrap_token(h)` *(deep model — A-reference)* | `convert_exception_to_response(mw_instance)` — `django/core/handlers/exception.py` (called at `base.py:88`) | unchanged callee: derives a new wrapper handler |
| `committed_handler(h, m)` | the composition the loop commits per participating layer: `convert_exception_to_response(middleware(adapt_method_mode(handler, ...)))` (`base.py:54-58,88`) | pure spec: handler a participating layer commits forward |
| `final_handler / final_async` | the loop's running-state fold over the visited middleware (`base.py:39-89`) | pure spec: the assembled chain after the whole walk |

The pre-patch defect this bundle senses (for the refinement audit, not named in
the consumer spec view): at `base.py:54` the loop assigned the adapted handler
straight back into `handler` *before* the `middleware(...)` construction that
may raise `MiddlewareNotUsed`; on that raise the loop `continue`s (`base.py:65`)
leaving `handler` overwritten with the adapted value, which the next middleware
then inherits.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the running `handler` (an opaque callable, the wrapped response chain) | `List[int]` — the trace of adaptation/wrapper tokens applied to the base handler | identity of the handler object ↔ equality of its token trace; "a fresh derived handler" ↔ a longer trace; the base handler ↔ `[]` |
| `handler_is_async` (`bool`) | `int` in {0, 1} | `True` ↔ `1`, `False` ↔ `0` |
| `middleware_is_async` (`bool`, computed `base.py:43-51`) | `target_mode[i]` (`int` in {0,1}) | the mode-selection logic (`sync_capable`/`async_capable` vs `handler_is_async`) is **unchanged** by the patch; it is supplied as input data, not re-derived |
| raising `MiddlewareNotUsed` while constructing the layer | `declines[i] == 1` | the only observable effect on chain assembly is "this layer is skipped"; the exception path is the `continue` at `base.py:65` |
| the ordered middleware list `reversed(settings.MIDDLEWARE)` | parallel `List` columns `target_mode`, `declines` of equal length | the i-th visited middleware ↔ index i |
| `adapt_method_mode(handler, ...)` returning a fresh callable | `adapt_token(h, m) = h + [1, m]` | appends an adaptation token; never mutates the input (fresh value) |
| `convert_exception_to_response(mw_instance)` returning a fresh callable | `wrap_token(h) = h + [2]` | appends a wrapper token; never mutates the input (fresh value) |

`handler` is genuinely mutated by the loop (full `list_pred` permission, exact
post-state in `final_handler`); `target_mode` and `declines` are read-only
(`Acc(list_pred(·), 1/2)`, required AND ensured — SPEC_GUIDE directive 5).

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `adapt_token` / `wrap_token` deep models ↔ the unchanged handler-deriving callees
**Callees:** `BaseHandler.adapt_method_mode` (`base.py:97-122`) and
`convert_exception_to_response` (`django/core/handlers/exception.py`). Neither
is changed by the patch. Both DERIVE A NEW handler object from the old one and
return it — `adapt_method_mode` returns either the method unchanged or
`sync_to_async(...)` / `async_to_sync(...)` (a fresh wrapper); `convert_exception_to_response`
returns `inner` (a fresh closure wrapping the passed `get_response`). Neither
ever mutates the handler passed in. The only property the chain-assembly proof
relies on is exactly this *fresh-derivation, no-in-place-mutation* behaviour —
which makes the handler object's identity (its token trace) the observable
that distinguishes a committed adaptation from a discarded tentative one.

These callees take/return arbitrary callables, so there is no scalar value to
axiomatize; the changed operation (the *threading* of these results across the
loop, with rollback on decline) is what this bundle models, and it is modelled
**deeply** (the `committed_handler` fold). G-AX therefore validates the deep
models against the REAL patched loop semantics rather than against a value
contract: `axiom_check.py` reconstructs the gold loop's handler threading
(`adapted = adapt(...); except MiddlewareNotUsed: continue; else: handler =
adapted`) with token-recording callables and asserts, on 12 boundary + 50000
randomized layer sequences, that the resulting `(handler trace, async flag)`
equals the model fold `final_handler` / `final_async`, AND the
behaviour-pinning property that deleting a declining layer never changes the
assembled chain (a declining layer leaves no trace). There is **no consumed
`@ContractOnly` axiom** in this bundle.

**Soundness / flag dependencies:** `adapt_method_mode`'s "fresh derivation"
holds on every branch (`sync_to_async(method, thread_sensitive=True)`,
`async_to_sync(method)`, or `return method`); none mutates `method`.
`convert_exception_to_response` likewise returns a fresh closure. The
mode-selection arithmetic (`sync_capable`/`async_capable`) is unchanged and is
abstracted as the `target_mode` input, so G-AX does not need to fuzz it.
Source: `django/core/handlers/base.py:97-122`,
`django/core/handlers/exception.py` (`convert_exception_to_response`) at
`base_commit`.
