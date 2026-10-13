# refinement.md — django__django-13297

Maps every operation in `implementation_wrapContextKwargs` to its `patch.diff`
counterpart in `_wrap_url_kwargs_with_deprecation_warning`
(`django/views/generic/base.py`). Tags: **R** type-refinement, **A-consumed**
proof uses a callee axiom, **A-reference** deep-modeled changed op validated ==
real callee, **I** identical concrete op.

## Patch (post-patch)
```python
def _wrap_url_kwargs_with_deprecation_warning(url_kwargs):
    context_kwargs = {}
    for key, value in url_kwargs.items():
        # Bind into function closure.
        def access_value(key=key, value=value):
            warnings.warn('... Reference %s ...' % key, RemovedInDjango40Warning, stacklevel=2)
            return value
        context_kwargs[key] = lazy(access_value, type(value))()
    return context_kwargs
```
The modeled value is the dict `context_kwargs` of deferred wrappers: for each
captured kwarg, a wrapper that (a) resolves to `value`, (b) is keyed to `key` for
its notice, and (c) presents `type(value)` as its type interface.

## Operation correspondence
| # | Lean op (`implementation_wrapContextKwargs`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut context := []` | `context_kwargs = {}` | R | empty accumulator ↔ empty dict; the result is built by appending in iteration order, so a `List (String × _)` keyed by name is the order-preserving bijection of an insertion-ordered dict (mapping.md). |
| 2 | `for (key, value) in urlKwargs do` | `for key, value in url_kwargs.items():` | R | iterate the captured kwargs in order; `url_kwargs.items()` ↔ `urlKwargs : List (String × UrlValue)`. |
| 3 | `presentedType := value.pytype` | `lazy(access_value, type(value))()` — the proxy class is prepared from `type(value)`, so the wrapper exposes the underlying value's type | A-reference | the CHANGED op, modeled DEEPLY: the proxy builder's effect on the presented type is spelled out as `presentedType = value.pytype`, not axiomatized. G-AX validates that the real `lazy(f, type(v))()` presents `type(v)` (and that pre-patch `SimpleLazyObject(f)` does not). |
| 4 | `resolved := value` | `access_value()` returns `value` (`return value`) | I | the wrapper resolves to exactly the captured value; nothing added/dropped. |
| 5 | `noticeKey := key` | `'... Reference %s ...' % key` inside `access_value` | I | the emitted notice is keyed to this kwarg's name. |
| 6 | `context := context ++ [(key, wrapper)]` | `context_kwargs[key] = <wrapper>` | R | store the wrapper under `key`, preserving insertion order ↔ list append. |
| 7 | `return context` | `return context_kwargs` | I | return the collection of wrappers. |

Op #3 is the only **A-reference** (the changed proxy-builder, deep-modeled and
G-AX-validated == the real callee on the presented-type facet). Ops #1,#2,#6 are
**R** (dict↔ordered-list bijection); #4,#5,#7 are **I**. No A-consumed axiom (the
proof consumes no callee contract; op #3's property is validated by G-AX, and the
impl spells out the construction). Therefore `meta.json axioms = []`,
`deep_model_references = ["lazy_proxy_presented_type"]`.

## R/I legs ⇒ G-CONF
The impl is R/I apart from the A-reference op #3, whose effect (presented type ==
value type) is itself a pure, mechanically-checkable function of the input
(`pytype`). The whole impl is therefore a pure function of `urlKwargs` and is
differential-tested by `conformance_check.py` against the patched behavior over
≥10^5 fuzzed inputs. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, line 170 decorates `access_value` with `@SimpleLazyObject` and line
180 stores `context_kwargs[key] = access_value` — i.e. each wrapper is a
`SimpleLazyObject`, a SINGLE generic deferred-object type ("compound objects of
unknown type") that exposes no specific result type. The prepatch impl
(`implementation_wrapContextKwargs` with `presentedType := genericDeferredType`,
the same fixed tag for every kwarg) is exactly this: every wrapper advertises the
generic deferred type instead of the underlying value's type. It therefore cannot
satisfy `problem_spec_wrapContextKwargs` on the discriminating conjunct of
`wrapsValue` (`out.2.presentedType = inp.2.pytype`) whenever a captured value's
type is not the generic deferred type — precisely the F2P case
`test_template_params_filtering`: the captured `artist_name` is a `str`, the
wrapper must present `str` so the ORM `.get(name=...)` lookup binds it, but the
`SimpleLazyObject` wrapper presents the generic type and the query crashes
("Error binding parameter 0 — probably unsupported type"). The carried gold proof
fails to typecheck against the buggy impl (G-DIFF). `resolved`/`noticeKey` are
unchanged between pre/post, so those conjuncts alone never discriminate — only
`presentedType` does, which is exactly what the patch fixes.
