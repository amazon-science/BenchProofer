# refinement.md — django__django-15741

Maps every operation in `implementation_localizedFormat` to its `patch.diff`
counterpart in `django.utils.formats.get_format`. Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** deep-modeled changed op
validated == real callee, **I** identical concrete op.

## Patch (post-patch `get_format`, relevant lines)
```python
def get_format(format_type, lang=None, use_l10n=None):
    ...
    if use_l10n and lang is None:
        lang = get_language()
    format_type = str(format_type)  # format_type may be lazy.   <-- the fix
    cache_key = (format_type, lang)
    try:
        return _format_cache[cache_key]
    except KeyError:
        pass
    # ... unchanged downstream resolution (format modules getattr cascade,
    #     settings/FORMAT_SETTINGS fallback) ...
    return val
```

## Operation correspondence
| # | Lean op (`implementation_localizedFormat`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let key := realizeName name` | `format_type = str(format_type)  # format_type may be lazy.` | **R** | the coercion the patch adds. `realizeName : FmtName → String` ↔ Python `str(·)`: `concrete s ↦ s` (Python `str(s) == s`, idempotent), `deferred s ↦ s` (the lazy proxy's `__str__` materializes its concrete name `s`). Type bijection in mapping.md. |
| 2 | `return some (lookupFormat key lang)` | the unchanged downstream resolution on the now-`str` `format_type` (cache lookup + format-module `getattr` cascade + settings fallback), returning `val` | **I** | identical concrete op: `lookupFormat` is the unchanged callee applied to the already-concrete name; `get_format` always returns a value at this call site, modeled as `some _`. |

Every op is **R** or **I**; **no A row** — no axiom is consumed (the proof is a
definitional `rfl` over `realizeName`) and no changed op is deep-modeled as a
reference. `lookupFormat` is declared `opaque` (signature only) with **no**
`axiom lookupFormat_prop`. Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow — `get_format(str(format_type), lang)` (pre-coercing the name,
then deferring to the unchanged downstream resolution = the real patched
`get_format` on a concrete name) — against the oracle `get_format(format_type,
lang)` (the real patched function on the raw, possibly-lazy name), over ≥10^5
fuzzed inputs presenting each name BOTH as a plain `str` and as a lazy proxy.
`conf_skip = false`.

## Why the prepatch is the real bug
`Solution_prepatch.lean` resolves only when the name arrives in concrete shape
(`directName` is `some` only for `.concrete`); a `deferred` name yields `none` —
it fails to resolve. That mirrors the pre-patch Python exactly: without
`str(format_type)`, a lazy proxy reaches `getattr(module, format_type, ...)` /
`getattr(settings, format_type)`, which raises `TypeError: getattr(): attribute
name must be string` — the function fails to produce a format for a deferred
name. The prepatch's carried gold proof (`rfl`) therefore fails to typecheck on
the `deferred` case (`none ≠ some (lookupFormat …)`) — exactly the G-DIFF signal.
This is the behavior the FAIL_TO_PASS tests exercise
(`test_get_format_lazy_format`, `test_date_lazy`): a lazy format name must
resolve to the same format a concrete name would.
