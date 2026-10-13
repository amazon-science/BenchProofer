# mapping.md — django__django-13112

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 09914ccf688974e068941f55412b930729bafa06`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
stdlib operations the deep model is validated against by G-AX).

Repo file under change: `django/db/models/fields/related.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `normalize_reference(text)` | the value assigned to `kwargs['to']` in the `isinstance(self.remote_field.model, str)` branch of `ForeignObject.deconstruct` — `django/db/models/fields/related.py:584-585` (body of the method at `:575`) | the modeled changed behaviour (normalization of a lazy model reference string) |
| `normalized(s)` *(deep model — A-reference)* | the composite transform `'%s.%s' % (app_label, model_name.lower())` / `model.lower()` built from `str.split('.')`, `str.lower()`, `%`-format (post-patch, `related.py:584-589`) | pure spec: the normalized reference; deep model validated `normalized == gold_transform` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `normfold(s, keep)` | the per-character composition (keep prefix verbatim, lower-case the rest) implied by `'%s.%s' % (app_label, model_name.lower())` | pure spec: keep first `keep` code points verbatim, ASCII-lower-case the rest (front-recursive fold) |
| `first_dot(s)` | the position of the separator dot used by `'.' in model` / `model.split('.')` | pure spec: index of the first `.` (U+002E), or `len(s)` if absent |
| `keep_count(s)` | `len(app_label)` when `'.' in model`, else `0` | pure spec: number of leading code points preserved verbatim |
| `lower_cp(c)` | one code point of `str.lower()` on ASCII identifier text | pure spec: ASCII lower-casing of a single code point |

The pre-patch repo behaviour the change replaces (for the refinement audit, not
referenced from the consumer spec view): `kwargs['to'] = self.remote_field.model.lower()`
(`related.py:585` @ base_commit) — the whole reference string lower-cased,
which folds a qualifying application label to lower case too.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`self.remote_field.model`, and the assigned `kwargs['to']`) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` concatenation ↔ list `+`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `'.' in model` (membership test) | `first_dot(s) < len(s)` | the dot is code point `46`; `'.' in model` iff some index holds 46 iff `first_dot(s) < len(s)` |
| `model.split('.')` (in-domain: exactly one dot) | prefix `s.take(first_dot(s))` / suffix `s.drop(first_dot(s)+1)` | for the single-dot references Django produces, `split('.') == [prefix, suffix]`; the model uses the first-dot split |
| `str.lower()` on a substring | `lower_cp` per code point (ASCII) | identifiers are ASCII (letters/digits/underscore), where `str.lower()` is the per-code-point map U+0041..U+005A → +32, else identity (validated by G-AX, §3) |
| `'%s.%s' % (app_label, model_name.lower())` | `s.take(p) + PSeq(46) + lowered(s.drop(p+1))` ≡ `normfold(s, p)` since `lower_cp(46)==46` | string-format concatenation ↔ sequence concatenation |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### `normalized` deep model ↔ the gold reference transform (A-reference)
**Callees (all unchanged stdlib, composed by the gold patch):** `str.split('.')`,
`str.lower()`, `%`-formatting. There is **no consumed axiom** — the changed
operation (preserve the application-label case, lower-case only the model name)
is modeled **deeply** by the `@Pure` folds `normalized` / `normfold` /
`keep_count` / `first_dot` / `lower_cp`. The gold transform, with the same
stdlib operations:

```python
if '.' in model:
    app_label, model_name = model.split('.')
    kwargs['to'] = '%s.%s' % (app_label, model_name.lower())
else:
    kwargs['to'] = model.lower()
```

**Domain.** A lazy model reference is either a bare model name (no dot) or a
qualified name `app_label.model_name` with **exactly one dot** — the only shapes
Django produces and the only shapes the gold's tuple-unpack
(`app_label, model_name = model.split('.')`) accepts (two or more dots raise
`ValueError`). Identifiers are ASCII (letters/digits/underscore); this is exactly
the domain where the model's ASCII `lower_cp` agrees with `str.lower()`.

**Why preserving the application-label case matters.** App labels are
**case-sensitive** in Django's migration/app registry; lower-casing the label
(the pre-patch behaviour) yields a dangling lazy reference to an app that
"isn't installed" (the issue's `ValueError`). The fix keeps the label verbatim
and folds only the model name — the discriminating behaviour the F2P test
`test_reference_mixed_case_app_label` observes (app label `'MiXedCase_migrations'`).
Docs: model references / app labels —
https://docs.djangoproject.com/en/3.2/ref/applications/#configurable-attributes.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL gold transform
(`str.split('.')` / `str.lower()` / `%`-format) on 26 boundary inputs (bare and
single-dot, including the F2P `MiXedCase_migrations.author`, the issue's
`DJ_RegLogin.Category`, empty/dot-only/empty-half edge cases) plus 40 000
randomized fuzz inputs (20 000 bare names + 20 000 single-dot `app.model`,
ASCII identifier alphabet). It asserts the deep model `normalized` equals the
real transform on every input. Exit 0 iff sound. It imports only Python
builtins (`str` methods — the very operations the patch calls); nothing
repo-specific.
