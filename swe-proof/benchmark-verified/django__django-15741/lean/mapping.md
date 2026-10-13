# mapping.md — django__django-15741

## Instance
- repo: django/django
- base_commit: 8c0886b068ba4e224dd78104b93c9638b860b398
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch adds a single line to `django.utils.formats.get_format`:

```python
format_type = str(format_type)  # format_type may be lazy.
```

inserted just before `cache_key = (format_type, lang)`. The caller may pass a
*lazy* string proxy (e.g. produced by `gettext_lazy(...)`) as `format_type`,
as happens for `some_date|date:_('Y-m-d')`. Pre-patch, the lazy proxy flows
unchanged into the `cache_key` tuple and into `getattr(module, format_type, ...)`
/ `getattr(settings, format_type)`, where CPython's `getattr` rejects a non-`str`
attribute name with `TypeError: getattr(): attribute name must be string`. The
fix coerces `format_type` to a real `str` first (lazy `__str__` materializes the
concrete name), after which every downstream use — cache key, the format-module
`getattr` cascade, the settings `getattr` — proceeds exactly as before.

The behavior is therefore: *accept the format name in either shape (already a
concrete string, or a lazy proxy that denotes a concrete string), realize it to
its concrete string, and resolve the localized format for that concrete name.*

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_localizedFormat` | `django.utils.formats.get_format` (django/utils/formats.py:100) — the changed coercion at line 116 (post-patch) |
| `problem_spec_localizedFormat`   | the post-condition `get_format` must satisfy |
| `realizeName`                    | `str(format_type)` — the lazy→concrete coercion the patch adds (formats.py:116 post-patch) |
| `lookupFormat`                   | the unchanged downstream resolution: `cache_key`/`_format_cache` lookup + the `get_format_modules` `getattr` cascade + the `getattr(settings, format_type)` / FORMAT_SETTINGS fallback (formats.py:117–143) |
| `FmtName.concrete`               | a `format_type` that is already a plain `str` |
| `FmtName.deferred`               | a `format_type` that is a lazy proxy (`__proxy__`) carrying its eventual concrete name |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `name : FmtName` | `format_type` (str OR lazy `__proxy__`) | `concrete s ↔` a real `str` whose value is `s`; `deferred s ↔` a lazy proxy whose `str(...)` is `s` |
| `realizeName name : String` | `str(format_type)` | concrete: `str(s) == s`; deferred: `str(proxy)` materializes `s`. Identity-preserving on concrete names (`str` is idempotent). |
| `lang : String` | `lang` (the resolved language) | the active language key into the format cache |
| `lookupFormat : String → String → String` | the unchanged downstream resolution applied to an ALREADY-`str` name | held `opaque` (signature only); its identity-as-the-real-callee is exercised by G-CONF, which leaves it as the real patched `get_format` on the coerced name |
| result `: Option String` | return value | `get_format` always returns a value here; `some _` (never `none`) — pinned by the spec |

`String` ↔ Python `str` is the identity bijection (byte-for-byte).

## Callee provenance / flag deps
- `lookupFormat` is the UNCHANGED downstream resolution. It is held `opaque`
  (signature only) and its `_prop` is NOT consumed by the proof (the proof is a
  definitional `rfl` over `realizeName`), so the bundle declares **no** `axiom
  lookupFormat_prop`. It is therefore neither an A-consumed axiom nor a
  deep-modeled A-reference; for G-CONF it is left as the real repo callee (the
  shadow calls the real patched `get_format` on the pre-coerced name).
- The only operation the patch changes is `str(format_type)` (`realizeName`), an
  **R** op (type-refinement: `FmtName → String` ↔ Python `str(·)` over
  str/lazy). G-CONF differential-tests this leg.
- Flag dependency: none relevant to the coercion. The lazy-acceptance behavior is
  unconditional on `use_l10n`/`lang`; G-CONF fuzzes names both in and out of
  `FORMAT_SETTINGS` and both concrete and lazy.

## G-CONF fuzz seed
- pinned seed: `15741`
- ≥10^5 fuzzed `(format_type, lang)` tuples; `format_type` drawn from a pool of
  real format names (`DATE_FORMAT`, `TIME_FORMAT`, `DECIMAL_SEPARATOR`, …), names
  absent from `FORMAT_SETTINGS`, and random strings — each presented BOTH as a
  plain `str` and as a lazy proxy.
