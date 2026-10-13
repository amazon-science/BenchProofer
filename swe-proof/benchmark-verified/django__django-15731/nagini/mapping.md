# mapping.md — django__django-15731

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 93cedc82f29076c824d476354527af1150888e4f`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/db/models/manager.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_proxy(source)` | `create_method(name, method)` — the inner builder in `BaseManager._get_queryset_methods` (`django/db/models/manager.py:83`, body lines 84-89) | the modeled changed function: it builds the forwarding proxy `manager_method` and copies the source method's introspectable metadata onto it |
| `source: Func` | `method` — the queryset method being proxied (`django/db/models/manager.py:83`, the second argument of `create_method`; supplied by `inspect.getmembers(queryset_class, ...)` at lines 92-94) | the source callable whose metadata the proxy must mirror |
| `Result(): Func` | `manager_method` — the inner forwarding function (`django/db/models/manager.py:84`) | the proxy callable returned to be installed on the manager |
| `reported_signature(wrapped, target_sig)` *(axiom — A-consumed)* | `inspect.signature` (CPython stdlib `Lib/inspect.py`, default `follow_wrapped=True`); invoked by the F2P test `inspect.signature(Article.objects.bulk_create)` | unchanged community callee: the signature resolver the F2P test runs on the proxy |
| `SIG_FORWARDING()` | the signature of `manager_method(self, *args, **kwargs)` (`django/db/models/manager.py:84`) | pure spec: the proxy's own forwarding parameter list signature |
| `Func.name` / `Func.doc` | `manager_method.__name__` / `manager_method.__doc__` (set at `django/db/models/manager.py:87-88` pre-patch; covered by `functools.wraps`'s `WRAPPER_ASSIGNMENTS` post-patch) | introspectable identity strings |
| `Func.wrapped` / `Func.target_sig` | the `__wrapped__` attribute `functools.wraps` records (CPython `Lib/functools.py`, `WRAPPER_ASSIGNMENTS`+`__wrapped__`) and the signature it makes `inspect.signature` follow | whether the proxy records the original it stands in for, and that original's signature |
| `Func.sig` | the proxy's own declared signature (`manager_method`'s `(self, *args, **kwargs)`) | the forwarding signature, reported when nothing is recorded |

The pre-patch repo lines the change removes (for the refinement audit, not
referenced from the consumer spec view): the manual `manager_method.__name__ =
method.__name__` and `manager_method.__doc__ = method.__doc__`
(`manager.py:87-88`). The added line is the `@wraps(method)` decorator on
`manager_method` (`manager.py:85` post-patch) plus the `from functools import
wraps` import.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a callable object's introspectable metadata (`manager_method` / `method`) | a minimal `Func` object exposing only the touched fields (`name`, `doc`, `wrapped`, `target_sig`, `sig`) | the only metadata the F2P/P2P tests observe is the display name, the docstring, and the reported signature; each is carried by an `int` code (`Func.name`, `Func.doc`, the signature codes) or a `bool` (`Func.wrapped`) |
| a `__name__` / `__doc__` string | `int` identity code | the tests compare equality of name/doc between proxy and source (`test_manager_method_attributes`); only equality is observed, so a code suffices (Nagini bans `str` indexing) |
| a parameter signature (`inspect.Signature`) | `int` code | the F2P `test_manager_method_signature` compares the proxy's reported signature for equality with the source's; only equality is observed, so a code suffices |
| `functools.wraps(method)` setting `method` as the proxy's `__wrapped__` | `proxy.wrapped = True; proxy.target_sig = source.sig` | `wraps` records the original callable; the model records the boolean fact plus the original's signature code (the only consequence `inspect.signature` observes) |
| copying `__name__`/`__doc__` (manual pre-patch, or via `wraps`' `WRAPPER_ASSIGNMENTS` post-patch) | `proxy.name = source.name; proxy.doc = source.doc` | identical assignments in both worlds |

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `reported_signature` ↔ `inspect.signature` (A-consumed)
**Callee:** CPython `inspect.signature(callable, *, follow_wrapped=True)` —
`Lib/inspect.py`. With its default `follow_wrapped=True`, `inspect.signature`
unwraps the chain of `__wrapped__` attributes (unless an explicit
`__signature__` is set) and returns the signature of the unwrapped callable;
absent `__wrapped__`, it returns the callable's own signature.
Docs: https://docs.python.org/3/library/inspect.html#inspect.signature
("If the given object is a function decorated with functools.wraps(), ...
follow_wrapped controls whether the wrapped function is followed").

The axiom encodes only the two obligations the proxy site relies on:

  * `wrapped` ⇒ the reported signature is the recorded original's signature
    (`target_sig`) — this is `follow_wrapped` following `__wrapped__`;
  * `not wrapped` ⇒ the reported signature is the proxy's own forwarding
    signature (`SIG_FORWARDING()`).

This is the **weakest** contract the postcondition needs; it is NOT the full
`inspect.signature` behaviour (descriptor handling, `__signature__` overrides,
class/builtin handling — none of which the proxy uses).

**Flag dependency:** the axiom is sound under `follow_wrapped=True`, which is
the CPython default and exactly what the F2P test invokes
(`inspect.signature(Article.objects.bulk_create)` with no keyword). Recorded
here so G-AX fuzzes that configuration.

**`functools.wraps` provenance (the mechanism that sets `wrapped`):** CPython
`functools.wraps` / `functools.update_wrapper` (`Lib/functools.py`) copies
`WRAPPER_ASSIGNMENTS` (`__module__ __name__ __qualname__ __doc__
__annotations__ ...`) and, crucially, sets `wrapper.__wrapped__ = wrapped`. It
is `__wrapped__` that `inspect.signature` follows. The pre-patch code copied
only `__name__` and `__doc__` and never set `__wrapped__`, so `inspect.signature`
fell back to `manager_method`'s own `(*args, **kwargs)`.

**Soundness check (G-AX):** `axiom_check.py` runs the real `functools.wraps` and
`inspect.signature` on 11 boundary parameter lists (including the exact
`bulk_create` list from the F2P test, plus the forwarding shape, zero-arg,
keyword-only, positional-only, var-args, ...) plus 5000 randomized parameter
lists. For each source it builds the proxy two ways — the gold mechanism
(`@functools.wraps(source)`, `wrapped=True`) and the pre-fix manual copy
(`wrapped=False`) — and asserts: (i) the wrapped proxy's reported signature
equals the source's; (ii) the unwrapped proxy's reported signature equals the
forwarding signature; (iii) end-to-end, the gold mechanism makes the proxy's
reported signature equal the source's while the pre-fix copy does not (whenever
the source differs from the forwarding shape); and that name/doc are copied in
both worlds. Exit 0 iff sound. It imports only the standard-library `inspect`
and `functools` modules (the very modules the F2P test and the gold patch use);
nothing repo-specific.
