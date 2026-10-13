# mapping.md — django__django-15741

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 8c0886b068ba4e224dd78104b93c9638b860b398`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/utils/formats.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `lookup_format(format_type)` | `get_format(format_type, lang=None, use_l10n=None)` — `django/utils/formats.py:100` | the modeled changed function (localisation format lookup) |
| `FormatType` (`deferred`, `content`) | the `format_type` argument of `get_format` — a value that is either a real `str` (already-resolved) or a lazy string proxy (`django.utils.functional.lazy(...)` / `gettext_lazy(...)`, a `__proxy__`, deferred) | the string-valued requested name in either of its two forms |
| `resolve(ft)` *(deep model — A-reference)* | `str(format_type)` — the coercion the patch inserts at `django/utils/formats.py:116` (post-patch) | pure spec: the resolved character sequence of the name, independent of the deferred flag. Validated `resolve == str()` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `format_value(name)` *(axiom — A-consumed)* | the unchanged downstream lookup `get_format`'s body performs on the (now-resolved) name: `cache_key = (format_type, lang)`, `_format_cache` lookup, `getattr(module, format_type, None)` over `get_format_modules(lang)`, `format_type in FORMAT_SETTINGS` / `ISO_INPUT_FORMATS`, `getattr(settings, format_type)` (`django/utils/formats.py:116-143`) | pure spec: the value of the unchanged lookup as a deterministic function of the resolved character sequence |
| `do_lookup(name)` *(axiom — A-consumed companion)* | the same unchanged lookup, as the list-producing operation that returns the value | the value-producing form of `format_value` (returns a list whose content is `format_value` of the resolved name) |

The single pre-patch → post-patch delta the change introduces (for the
refinement audit, not referenced from the consumer spec view): the inserted
line `format_type = str(format_type)  # format_type may be lazy.` at
`django/utils/formats.py:116` (post-patch numbering), immediately before
`cache_key = (format_type, lang)`. Pre-patch, the un-coerced `format_type`
flows into `getattr(module, format_type, None)` (line 128) and
`getattr(settings, format_type)` (line 134); `getattr` requires a real `str`
name and raises `TypeError: attribute name must be string` on a lazy proxy.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `format_type` argument: a real `str` **or** a lazy string proxy | `FormatType` with `deferred: bool` and `content: List[int]` of Unicode code points | `deferred == False` ↔ a real `str`; `deferred == True` ↔ a lazy proxy; `content[k] == ord(c_k)` where `c_1…c_n` are the characters of the string the argument denotes (the proxy's underlying string for the lazy case). `len(content)` ↔ string length |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises a list as a `PSeq`; `resolve(ft)` ↔ the `str`-content `str(format_type)` denotes |
| the lookup's returned format value (a `str`, or a `list`/`tuple` for the `*_INPUT_FORMATS` names) | `List[int]` whose `ToSeq` is `format_value(resolved name)` | the F2P tests compare the returned value by equality; modeled as a value keyed only on the resolved name |
| `str(format_type)` coercion (`formats.py:116`, post-patch) | `resolve(ft)` = `ToSeq(ft.content)` | for a real `str`, `str(x) == x` (identity); for a lazy proxy, `str(proxy)` evaluates the proxy and returns the underlying `str`. In both cases the result is the underlying character sequence — independent of the deferred flag |

`str` indexing/iteration is banned in Nagini, so the name's characters are
carried as `List[int]`; the specification is phrased over `PSeq[int]` via
`ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `resolve` deep model ↔ `str(format_type)` (A-reference)
**Callee:** Python `str()` applied to the `format_type` argument. The changed
context is modeled **deeply** by the `@Pure` function `resolve` (returns the
object's underlying character sequence regardless of `deferred`); there is **no
consumed coercion axiom**. The deep model is validated equal to the real
coercion out-of-band by axiom_check.py (G-AX).

Why `resolve` ignores the deferred flag: a lazy string is produced by
`django.utils.functional.lazy(func, str)` (`django/utils/functional.py:87`),
whose `__proxy__.__str__` (`functional.py:171-174`) evaluates the wrapped
function and returns `str` of its result — the underlying string. For a real
`str`, `str(x)` is the identity. Hence

  `str(already_resolved_name) == name == str(deferred_name)`,

i.e. the coercion's result depends only on the denoted string, not on whether
the value arrived deferred. `gettext_lazy` (`django/utils/translation/__init__`)
is exactly such a `lazy(..., str)` proxy. axiom_check.py asserts
`resolve == str()` on both forms over boundary + 5000 fuzz names, including the
F2P witnesses (`"DATE_FORMAT"`, `"H:i"`).

### 3.2 `format_value` / `do_lookup` ↔ the unchanged downstream lookup (A-consumed)
**Callee:** the body of `get_format` from `cache_key = (format_type, lang)`
onward (`django/utils/formats.py:116-143`): the `_format_cache` lookup, the
`getattr(module, format_type, None)` scan over `get_format_modules(lang)`, the
`format_type in FORMAT_SETTINGS` / `ISO_INPUT_FORMATS` membership tests, and
the `getattr(settings, format_type)` fallback. None of this is changed by the
patch.

The axiom encodes only the property the proof needs: **the value is a
deterministic function of the resolved character sequence of the name** —
nothing about it depends on whether the name arrived deferred or already
resolved. This is the weakest sufficient contract (`format_value(name)` is
`@Pure`, so a function of its argument; `do_lookup` returns a list whose
content equals `format_value` of the resolved name). It is NOT the full lookup
semantics (locale modules, cache, settings fallback) — only its functional
dependence on the resolved name.

This contract is sound precisely because every use of `format_type` inside the
lookup (the cache key, both `getattr` name arguments, the membership tests) is
keyed on the **string value** of `format_type`; once the patch coerces it to a
real `str`, two requests whose names resolve to the same string are
indistinguishable to the lookup. (Pre-patch this property is violated only by a
crash — `getattr` rejects the non-`str` lazy name — not by a different value;
the patch removes the crash by coercing first.)

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`django.utils.formats.get_format` (post-patch) on every format name in both
forms and asserts `get_format(gettext_lazy(name)) == get_format(name)` — i.e.
the value is keyed only on the resolved name, the exact obligation
`format_value` / `do_lookup` stand for. It also asserts the F2P witness
`get_format(gettext_lazy("DATE_FORMAT")) == get_format("DATE_FORMAT")`. The
A-reference (`resolve == str()`) is checked on the same inputs. It imports only
the standard library plus the repo's own `django.utils.functional.lazy`,
`gettext_lazy`, and `get_format` — the very symbols the patch touches and
calls. Exit 0 iff sound.

Note: run against the *base_commit* (pre-patch) source, the lookup half of
axiom_check.py reproduces the real bug verbatim
(`TypeError: attribute name must be string, not '__proxy__'`) — confirming the
modeled behaviour is exactly the one the patch fixes. The axiom is validated
against the **post-patch** (corrected) callee that the bundle ships.
