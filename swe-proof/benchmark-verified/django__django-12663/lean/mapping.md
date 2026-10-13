# mapping.md — django__django-12663

## Symbol binding (file:line @ base_commit fa5e7e46d875d4143510944f19d79df7b1739bab)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_outputType` / `problem_spec_outputType` | `Query.output_field` (a `@property`) | `django/db/models/sql/query.py:233-238` |
| `selections : List Selection` | `self.select` (the tuple of selected expressions) | `query.py:235` (`len(self.select)`) |
| `annotations : List AnnExpr` | `self.annotation_select` (ordered mapping of annotation expressions) | `query.py:237` (`len(self.annotation_select)`, `.values()`) |
| `Selection.base : Option Field` | the selected expression's underlying referenced attribute (`Col.target`); absent for expressions that have none | `query.py:236` (post-patch `getattr(select, 'target', None)`) |
| `Selection.declared : Field` | the selected expression's declared output type (`Expression.field`, an alias of `Expression.output_field`) | `query.py:236` (`select.field`) |
| `AnnExpr.outputField : Field` | the single annotation expression's `.output_field` | `query.py:238` (`next(iter(self.annotation_select.values())).output_field`) |
| `baseOrDeclared` (pure helper) | the post-patch single-column choice `getattr(select, 'target', None) or select.field` | the changed lines `query.py:235-236` |
| `Field` (`Nat`) | a model field / column type descriptor object (only its identity is observed here) | the object returned by `output_field` |

The modeled function is the `Query.output_field` property. It is the only
function whose behavior changes and the only one observed by the FAIL_TO_PASS
test (`test_subquery_filter_by_lazy`), which filters a nested-subquery annotation
against a lazily-evaluated related object and asserts the query resolves
correctly (rather than raising a `TypeError` while preparing the lookup value).

### What the function does (base_commit)

```python
@property
def output_field(self):
    if len(self.select) == 1:
        return self.select[0].field                # base_commit (buggy)
    elif len(self.annotation_select) == 1:
        return next(iter(self.annotation_select.values())).output_field
    # implicit `return None` otherwise
```

Post-patch the single-column branch becomes:

```python
        select = self.select[0]
        return getattr(select, 'target', None) or select.field
```

Step by step (post-patch):
1. if exactly one column is selected: return that column's underlying referenced
   attribute (`select.target`) when it has one; otherwise its declared output
   type (`select.field`).
2. else if exactly one annotation is selected: return that annotation's declared
   output type (`.output_field`).
3. otherwise: return `None`.

### Why the choice matters

For an ordinary freshly-built column the underlying referenced attribute and the
declared output type coincide, so the result is unchanged. They diverge when a
column's declared output type has been resolved to a different field object than
the attribute it actually references — which is what happens through a nested
subquery annotation. Returning the underlying referenced attribute (rather than
the declared output type) lets the downstream lookup machinery perform the
related-field value coercion (turning a lazily-evaluated related object into the
stored key), instead of attempting a raw numeric coercion that fails.

### Lean modeling

- `selections : List Selection` models `self.select`. Each `Selection` carries
  the two observable candidate field-descriptors of one selected expression:
  `base : Option Field` (the underlying referenced attribute; `none` when the
  expression has none) and `declared : Field` (the declared output type, always
  present).
- `annotations : List AnnExpr` models `self.annotation_select` (ordered); the
  only observable here is each annotation's `outputField : Field`.
- `Field := Nat` — a field/column type descriptor; only its identity (equality)
  is observed by this function, so an injective `Nat` encoding suffices.
- `baseOrDeclared s = s.base.getD s.declared` models
  `getattr(select, 'target', None) or select.field`. A real model-field object
  is always truthy, so `getattr(select, 'target', None) or select.field` reduces
  to "`target` if it exists, otherwise `field`", i.e. `Option.getD`. (See the
  truthiness note below; `conformance_check.py` keeps both legs faithful to it.)
- The result is `Option Field`: `some f` ↔ a returned field object `f`; `none` ↔
  the implicit Python `None` return.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.select` (tuple of selected expressions) | `selections : List Selection` | element order = tuple order; only `len == 1` and the single element are observed. |
| `self.annotation_select` (ordered dict) | `annotations : List AnnExpr` | values in insertion order; only `len == 1` and the single value are observed. |
| `select.target` (may be absent) | `Selection.base : Option Field` | a present, truthy attribute ↔ `some f`; absent ↔ `none`. |
| `select.field` (== `select.output_field`) | `Selection.declared : Field` | the declared output type object ↔ a `Field` id. |
| `annotation.output_field` | `AnnExpr.outputField : Field` | the annotation's declared output type ↔ a `Field` id. |
| a model-field object | `Field` (`Nat`) | distinct field objects ↔ distinct `Nat`s; field objects are always truthy ⇒ ids are taken ≥ 1 in the fuzzer. |
| `getattr(select, 'target', None) or select.field` | `baseOrDeclared select` | `some t ⇒ t`, `none ⇒ declared`. |
| the property's return value | `result : Option Field` | a field object ↔ `some f`; `None` ↔ `none`. |

### Truthiness note (faithfulness of `or`)

The patched expression uses Python `or`: `getattr(select, 'target', None) or
select.field`. This falls back to `select.field` when `target` is `None` **or**
any other falsy value. Real Django model-field objects do not define a falsy
`__bool__`/`__len__`, so a present `target` is always truthy and the expression
is exactly "`target` if not `None` else `field`" — which is `Option.getD`. The
conformance fuzzer therefore draws field ids ≥ 1 (always truthy), and the
oracle still applies the genuine Python `or` so the differential remains a real
test of the modeling.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The single-column choice — the only behavior the
  patch changes — is modeled DEEPLY by `baseOrDeclared` over the optional
  underlying attribute (`Option Field`) versus the declared type (SPEC_GUIDE §3:
  a deeply-modeled changed decision is never axiomatized). The annotation branch
  returns an observable field carried directly as data (`AnnExpr.outputField`);
  no property of an external callee is consumed by the proof, so the `axioms`
  region is empty and **G-AX skips**.
- `getattr` / Python's `or` — language built-ins, modeled deeply by
  `Option.getD` (see the truthiness note); not callees.
- `next(iter(self.annotation_select.values()))` — selects the single annotation
  value; modeled as `annotations.headI` over the single-element list. Unchanged
  by the patch.
- The `.output_field` of the single annotation (annotation branch) is itself a
  recursive property in the repo, but it is UNCHANGED by the patch and its value
  is carried directly as `AnnExpr.outputField`; the F2P fix turns solely on the
  single-column branch, so the annotation branch is modeled as an opaque carried
  field with no consumed property.

## G-CONF fuzz seed

Pinned LCG seed: **12663** (see `conformance_check.py` `SEED`). Corpus: randomized
`selections` lists (length 0–3, so the `len == 1` guard both fires and does not),
each `Selection` with `base ∈ {none} ∪ {some id}` and a `declared` id (ids ≥ 1,
sometimes equal to `base`, sometimes different — the divergence the fix turns on),
crossed with `annotations` lists (length 0–3), over ≥1e5 fuzzed inputs. The R/I
shadow of `implementation_outputType` is diffed against an in-process replica of
the POST-PATCH `output_field` property (`getattr(select, 'target', None) or
select.field`, then the annotation branch, then `None`). Hand-picked edge cases
pin the discriminating clause: a single selection whose `base` is present and
differs from `declared`.
