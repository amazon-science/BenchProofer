# mapping.md — sphinx-doc__sphinx-8459

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 68aa4fb29e7dfe521749e1e14f750d7afabb3481`, states the type
abstraction, and gives the provenance of each axiom / deep-model reference
(callee source + the exact behaviour encoded).

Repo file under change: `sphinx/ext/autodoc/typehints.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `record_annotations(...)` | `record_typehints(app, objtype, name, obj, options, args, retann)` — `sphinx/ext/autodoc/typehints.py:23` (changed body line 30) | the modeled changed function: it records, into a per-object annotation mapping, the stringified annotation of each parameter (and the return) of a callable, with the annotation resolved through the configured alias map |
| `aliases` (param) | `app.config.autodoc_type_aliases` — the configuration value newly threaded into the signature call at `typehints.py:30` | the user-configured map from an annotation source token to its desired resolved token |
| `resolve(tok, aliases)` *(deep model — A-reference)* | the annotation-resolution performed by `inspect.signature(obj, type_aliases=...)` → `sphinx.util.typing.get_type_hints(subject, None, type_aliases)` (`sphinx/util/inspect.py:508`) → CPython `typing.get_type_hints` | pure spec: how one annotation source token is resolved to its recorded token given the alias map; validated against the real callee by axiom_check.py (G-AX), NOT consumed as an axiom |
| `expand(tok)` *(deep model — A-reference)* | the no-alias resolution: a bare annotation source (a forward reference under `from __future__ import annotations`) evaluated by `get_type_hints` with no `localns` overrides, i.e. expanded to its underlying definition (`myint` → `int`) | pure spec: the resolution a source token receives when NO alias governs it |
| `KEY_RETURN()` | the literal dict key `'return'` used at `typehints.py:35` (`annotation['return'] = ...`) | pure spec: the reserved name token under which the return annotation is recorded |
| result `Dict[int, int]` | `annotations.setdefault(name, OrderedDict())` — the per-object annotation mapping populated at `typehints.py:33,35` | pure spec: name token → recorded (resolved+stringified) annotation token |

The pre-patch repo symbol the change differs from (for the refinement audit, not
referenced from the consumer spec view): the bare call `inspect.signature(obj)`
at `typehints.py:30`, which defaults `type_aliases={}` (`sphinx/util/inspect.py:472`)
and so resolves every annotation with no alias overrides — `expand(tok)` for
every token.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a callable's parameter list `sig.parameters.values()` | three parallel lists `names: List[int]`, `raw: List[int]`, `has_annot: List[bool]`, indexed `0..n-1` | parameter `i` has name token `names[i]`, raw-annotation source token `raw[i]`, and `has_annot[i] == (param.annotation is not param.empty)` |
| `param.name` (a `str`) | `int` name token | distinct parameter names ↔ distinct tokens; only identity/membership is observed (the dict is keyed by name), so integer identity is the faithful carrier |
| `param.annotation` source / `typing.stringify(annotation)` (a `str`) | `int` annotation token | each distinct annotation *string* ↔ a distinct token; `stringify` is the identity on the carrier (a token already denotes the rendered annotation string), and `get_type_hints` resolution is modeled by `resolve` |
| `app.config.autodoc_type_aliases` (a `Dict[str, str]`) | `aliases: Dict[int, int]` | source-string token → resolved-string token; membership/lookup is the only operation |
| the per-object annotation mapping `OrderedDict[str, str]` | `Dict[int, int]` result | name token → recorded annotation token; the `'return'` slot is the reserved key `KEY_RETURN()` |
| `param.empty` sentinel (annotation absent) | `has_annot[i] == False` | a parameter with no annotation is skipped (not recorded), exactly as the `if param.annotation is not param.empty` guard |

`str` indexing/iteration is banned in Nagini, so parameter names and annotation
strings are interned as `int` tokens; the observable the downstream rendering
relies on is *which resolved annotation token is recorded under each name*.

## 3. Callee provenance (deep-model references — checked by G-AX / axiom_check.py)

### 3.1 `resolve` / `expand` deep model ↔ `get_type_hints(subject, None, type_aliases)` (A-reference)

**Callee:** `inspect.signature(obj, type_aliases=aliases)`
(`sphinx/util/inspect.py:471`) resolves each parameter's annotation by
```python
annotations = typing.get_type_hints(subject, None, type_aliases)   # inspect.py:508
parameters[i] = param.replace(annotation=annotations[param.name])  # inspect.py:511
```
and `sphinx.util.typing.get_type_hints(obj, None, localns)`
(`sphinx/util/typing.py:69`) calls CPython `typing.get_type_hints(obj, None, localns)`.
Under `from __future__ import annotations` every annotation is stored as a
*string* (a forward reference). `typing.get_type_hints` evaluates each such
string in a namespace; the `type_aliases` map is supplied as the **localns**, so
a name present in the alias map resolves to the alias's value rather than being
looked up as a module global and expanded.

The deep model encodes this as:

```
resolve(tok, aliases) = aliases[tok]   if tok in aliases     # alias governs the name
                      = expand(tok)    otherwise             # no alias: expand to underlying
```

where `expand(tok)` is the no-alias resolution (the forward reference evaluated
against module globals). In the tested configuration the function `sum` is
annotated `x: myint, y: myint -> myint` with module-level `myint = int` and
`from __future__ import annotations`; the alias map is `{'myint': 'myint'}`. So:
- with the alias map, `resolve('myint', {'myint':'myint'}) == 'myint'` — the
  alias name is preserved and recorded/rendered as `myint`;
- with no alias map (the pre-patch default `{}`), `resolve('myint', {}) ==
  expand('myint') == 'int'` — the forward reference expands to its underlying
  type and is recorded/rendered as `Dict[str, Any]` / `int`.

This is exactly the observed behaviour: `Dict[str, Any]` (or `int`) instead of
the alias. `resolve`/`expand` are modeled **deeply** (the per-token substitution
in the `pure` region); there is **no consumed `get_type_hints` axiom**.

**Scope of the `resolve(tok, aliases) = aliases[tok]` carrier (faithfulness
nuance).** The encoding `resolve(tok, aliases) = aliases[tok]` records the
configured alias value verbatim only for **name-preserving (self-alias)**
configurations — target token == source name, e.g. the tested `{'myint':
'myint'}` and the issue reproducer `{'JSONObject': 'types.JSONObject'}`. For a
non-self-alias resolvable target the real resolver records the resolved object's
qualified name, which need not be the literal target string. This is
**non-exploitable** for `verify ⟹ correct`: `resolve` is consumed symmetrically
in the spec and the impl (same expression on both sides of the discriminating
clause), and the tested config and issue reproducer are both name-preserving.
The bundle therefore scopes the `aliases[tok] == recorded` claim to
name-preserving alias configurations — exactly the inputs the F2P test and the
issue exercise. The deep
model is validated **== the real callee** out-of-band by axiom_check.py (G-AX):
it builds a function with `from __future__ import annotations` and an aliased
annotation, runs CPython `typing.get_type_hints` with and without the alias map
as `localns`, and asserts the recorded annotation matches `resolve` /
`expand` for both configurations. Docs:
https://docs.python.org/3/library/typing.html#typing.get_type_hints (the
`localns` parameter) and the `type_aliases` plumbing in
`sphinx/util/inspect.py:471-534`.

### 3.2 `stringify` ↔ `sphinx.util.typing.stringify` (identity on the carrier)
`typing.stringify(annotation)` (`sphinx/util/typing.py:278`) renders an
annotation object to its display string. In the model an annotation token
already denotes its rendered string, so `stringify` is the identity on the
carrier and needs no separate axiom — the resolution `resolve` is the only
behaviour the change affects (which annotation object is stringified, not how it
is rendered). The G-AX check exercises the end-to-end rendered string so this
identity is covered by §3.1.
