# mapping.md — sphinx-doc__sphinx-8459

## Symbol binding (file:line @ base_commit 68aa4fb29e)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_aliasedLabels` / `problem_spec_aliasedLabels` / `correct_aliasedLabels` | `record_typehints` — the body that fills the per-name `annotation` table from a callable's signature | `sphinx/ext/autodoc/typehints.py:23-37` @ base_commit (edited line `30`, hunk `@@ -27,7 +27,7 @@`) |
| `render : String → String` | `typing.stringify` — the default per-annotation label renderer | `sphinx/util/typing.py:278` (`typehints.py:33,35`) |
| `aliases : List (String × String)` | `app.config.autodoc_type_aliases` — the configured `{name: replacement}` map | introduced into the call at `typehints.py:30` (gold) |
| `renderName render aliases nm` | the POST-patch resolved label of one annotation: alias replacement if `nm` is a configured alias, else `stringify(nm)` | `typehints.py:30` (alias-aware signature) → `:33`/`:35` (`stringify`) |
| `params : List (String × Option String)` | `sig.parameters.values()` — each parameter's `.name` and its declared annotation name (`None` when `param.annotation is param.empty`) | `typehints.py:31-33` |
| `ret : Option String` | `sig.return_annotation`'s declared name, or `None` when `sig.return_annotation is sig.empty` | `typehints.py:34-35` |
| `annotation := annotation ++ [(name, …)]` (loop) | `annotation[param.name] = typing.stringify(param.annotation)` | `typehints.py:32-33` |
| return-entry append (key `"return"`) | `annotation['return'] = typing.stringify(sig.return_annotation)` | `typehints.py:34-35` |

## The modeled function and the fix

`record_typehints` records, into `app.env.temp_data['annotations'][name]`, an
ordered table mapping each annotated parameter (and the return value) to the
*type label* that will later be shown in the documentation. It iterates the
callable's signature parameters in order, emitting `param.name → stringify(ann)`
for each parameter whose annotation is present, and finally `'return' →
stringify(return_annotation)` when the return is annotated.

The bug: the signature is resolved by `inspect.signature(obj)`, which renders
annotations by their default form and **ignores the user-configured
`autodoc_type_aliases`**. So when `autodoc_typehints = 'description'` (the path
that feeds the recorded table into the description), a configured alias such as
`{'myint': 'myint'}` has no effect — the parameter and return labels show the
default rendering of the underlying type instead of the alias.

The gold fix threads the alias table into signature resolution:

```python
# POST-PATCH (gold)
sig = inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)
```

`sphinx.util.inspect.signature` then calls `typing.get_type_hints(subject, None,
type_aliases)`, which makes each annotation resolve to its configured alias when
one is registered (else the default). Concretely, for the modeled table this
means every emitted label becomes *alias-aware*: `aliases.get(name,
stringify(name))` rather than `stringify(name)`.

## Modeled input / output (Lean ↔ Python type bijection)

| Python | Lean | note |
|---|---|---|
| ordered `sig.parameters.values()` | `params : List (String × Option String)` | `(param.name, declared annotation name)`; `none` ⇔ `param.annotation is param.empty` (no entry emitted) |
| declared return type name or absent | `ret : Option String` | `none` ⇔ `sig.return_annotation is sig.empty` |
| `app.config.autodoc_type_aliases` (`dict[str,str]`) | `aliases : List (String × String)` | ordered key→replacement pairs; first match wins (Python dict keys are unique, so order is immaterial) |
| `typing.stringify` (default label of an annotation) | `render : String → String` | the UNCHANGED default renderer; a *free input* of the theorem, quantified over all renderers |
| recorded `annotation` `OrderedDict[str,str]` | `result : List (String × String)` | insertion-ordered `(key, label)` pairs; params in declaration order, then `"return"` |
| `annotation['return']` reserved key | the literal key `"return"` | matches Python's reserved `'return'` slot |

The recorded table is an `OrderedDict`; modeling it as an ordered
`List (String × String)` is exact for both order and content (no duplicate
parameter names in a signature, and `'return'` cannot collide with a parameter
name because it is added after the loop from `sig.return_annotation`).

## Callee provenance + flag deps

- `typing.stringify` (the default annotation renderer) is UNCHANGED by the fix.
  Its output is the *baseline* label that the alias table overrides; it is
  modeled as the free input `render`, quantified universally in the theorem, not
  axiomatized and not pinned to specific values.
- The aliasing behaviour (`inspect.signature(obj, type_aliases=…)` ⇒
  `get_type_hints(subject, None, type_aliases)`) is the operation the fix
  introduces. It is modeled DEEPLY as `renderName` (alias lookup with default
  fallback) — an **A-reference** row, validated by `conformance_check.py`
  (G-CONF) against the alias-resolution behaviour, NOT a consumed axiom.
- Flag dependency: the recorded table is consumed as displayed type labels only
  when `autodoc_typehints == 'description'` (the path `merge_typehints` /
  `record_typehints` jointly serve, and the path the F2P test exercises via
  `confoverrides={'autodoc_typehints': "description", 'autodoc_type_aliases':
  {'myint': 'myint'}}`). The recording function itself runs regardless; the alias
  resolution it now performs is what the description path needs.

## G-CONF fuzz seed

Pinned seed: `20240630` (see `meta.json.verifier_pins.conf_seed`).
