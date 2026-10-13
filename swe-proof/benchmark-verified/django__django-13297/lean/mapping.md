# mapping.md — django__django-13297

## Symbol binding (file:line @ base_commit 8954f255bb)
Modeled function: `_wrap_url_kwargs_with_deprecation_warning(url_kwargs)`,
`django/views/generic/base.py:168-181` (@ base). It is called from
`TemplateView.get` (`base.py:161`) to turn the URL-captured kwargs into the
deferred values that are passed to `get_context_data`. The gold patch rewrites
how each kwarg's deferred wrapper is built.

Lean modeled function name: `wrapContextKwargs` (deliberately neutral — it names
the *behavior* "wrap the URL kwargs into deferred context values", not the
patched symbol; see G-LEAK note).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `wrapContextKwargs` (modeled) | `_wrap_url_kwargs_with_deprecation_warning`, `base.py:168-181` |
| `urlKwargs : List (String × UrlValue)` | `url_kwargs` (`dict`) iterated as `for key, value in url_kwargs.items()`, `base.py:171` |
| `UrlValue.data` | `value` (the captured route value's content), `base.py:171` |
| `UrlValue.pytype` | `type(value)` (the value's runtime type), used post-patch at `base.py:180` |
| `DeferredValue` | the per-kwarg deferred wrapper object stored in `context_kwargs[key]` |
| `DeferredValue.resolved` | the value the wrapper produces when consumed = `value` returned by `access_value()` (`base.py:179`) |
| `DeferredValue.noticeKey` | the kwarg name `key` the emitted deprecation notice is keyed to (`'... Reference %s ...' % key`, `base.py:175-176`) |
| `DeferredValue.presentedType` | the type identity the wrapper exposes to consumers |
| result `List (String × DeferredValue)` | `context_kwargs` (`dict`), built in iteration order, `base.py:169-181` |

### The patched line (the decisive facet)
```python
# pre-patch  (base.py:170,180)
@SimpleLazyObject
def access_value(key=key, value=value): ... ; return value
context_kwargs[key] = access_value          # wrapper of generic deferred type

# post-patch
def access_value(key=key, value=value): ... ; return value
context_kwargs[key] = lazy(access_value, type(value))()   # wrapper presents type(value)
```
Pre-patch each wrapper is a `SimpleLazyObject` — a single generic deferred-object
type, "compound objects of unknown type" (its own docstring), exposing no
specific result type. Post-patch each wrapper is built by `lazy(access_value,
type(value))()`, whose proxy class is *prepared from `type(value)`* (the
`resultclasses` argument), so the wrapper exposes the underlying value's own type
interface to consumers. Both wrappers resolve to the same `value` and emit the
same `key`-keyed notice; only the PRESENTED TYPE differs. That difference is what
lets a type-directed consumer (e.g. a DB parameter bind that inspects the value's
type) accept the wrapper post-patch but reject it pre-patch.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `url_kwargs.items()` — `list[(str, value)]` in dict/insertion order | `urlKwargs : List (String × UrlValue)` (order preserved) |
| `key : str` | first projection `String` |
| `value` content | `UrlValue.data : String` (a stand-in for the value's content; only carried through, never inspected) |
| `type(value)` runtime type identity | `UrlValue.pytype : Nat` (injective tag over distinct runtime types; only `=`/`≠` observed) |
| the deferred wrapper's resolved value | `DeferredValue.resolved : UrlValue` (= the input value) |
| the kwarg name the notice is keyed to | `DeferredValue.noticeKey : String` (= `key`) |
| the type interface the wrapper presents | `DeferredValue.presentedType : Nat` (post: `= pytype`; pre: a fixed generic tag) |
| `context_kwargs` (dict, insertion order) | `result : List (String × DeferredValue)` |

### Type-identity modeling note
Python runtime types (`str`, `int`, `Account`, …) are modeled as distinct `Nat`
tags via an injective encoding; the spec only ever compares type identities for
equality (`presentedType = pytype`), never inspects their structure, so the
`Nat` tag is a sound bijection on the observed facet. The "generic deferred-object
type" (`SimpleLazyObject`'s own type) is itself one fixed tag, distinct from the
underlying value tags whenever the value is not of that type — which is the
discriminating case the F2P test exercises (the value is a `str` slug / model
instance, never a `SimpleLazyObject`).

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. The deferred-wrapping primitive
  itself (the proxy builder) is the operation the patch CHANGES, so it is modeled
  DEEPLY (structurally, as the `DeferredValue` it constructs) — never axiomatized
  (SPEC_GUIDE §0.7, §3). The notice emission is a side effect orthogonal to the
  modeled value (it is keyed to `key`, carried as `noticeKey`); it consumes no
  callee contract.
- No flag dependency: every captured kwarg is wrapped the same way; the loop is
  unconditional over `url_kwargs.items()`.

## G-LEAK
The problem_statement DOES contain `SimpleLazyObject` (the reporter names it
verbatim as the observed crashing type). It does NOT contain `lazy`,
`_wrap_url_kwargs_with_deprecation_warning`, `access_value`, `resultclasses`, or
`type(value)`. The spec view names none of the patched symbols: the modeled
identifier `wrapContextKwargs` shares no patched def/class substring
(`access_value`, the wrapper-building function), and the comments describe the
behavior ("present the same type interface as the underlying value") without
naming the edit (no `lazy` vs `SimpleLazyObject`, no diagnosis). The neutral
"generic deferred-object type" phrasing in the *prepatch* impl region is not part
of the spec view (impl region is elided).

## Pinned G-CONF fuzz seed
`13297`.
