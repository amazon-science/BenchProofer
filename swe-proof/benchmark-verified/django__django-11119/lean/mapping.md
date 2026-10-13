# mapping.md — django__django-11119

## Instance
- repo: django/django
- base_commit: d4df5e1b0b1c643fe0fc521add0236764ec8e92a
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`Engine.render_to_string` (django/template/engine.py:149) builds the rendering
`Context` for plain-data callers WITHOUT passing the engine's configured
`autoescape` attribute, so a `Context` is constructed with its default
`autoescape=True`. An engine created with `autoescape=False` was therefore
ignored: plain-data renders were always autoescaped. The gold patch threads the
engine's `autoescape` into the freshly-built `Context`:

```python
-            return t.render(Context(context))
+            return t.render(Context(context, autoescape=self.autoescape))
```

The autoescape flag carried by the rendering `Context` is read downstream by
`render_value_in_context` (django/template/base.py:962): when the flag is true
the interpolated value is passed through `conditional_escape`, otherwise it is
emitted as a plain string. Literal text nodes are unaffected by the flag.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_renderToString` | `Engine.render_to_string` (django/template/engine.py:149) — specifically the context-construction branch at :160-163 |
| `problem_spec_renderToString`   | the post-condition this function must satisfy |
| `renderValue` (parameter)       | the unchanged downstream value-rendering step `render_value_in_context` (django/template/base.py:962), a function of `context.autoescape` (Bool) and the value (str) |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `engineAutoescape : Bool` | `self.autoescape` (bool) | engine's configured escaping setting; `true ↔ True` |
| `suppliedIsContext : Bool` | `isinstance(context, Context)` (bool) | whether the caller passed a ready-made `Context` (vs plain data / `None`) |
| `suppliedCtxAutoescape : Bool` | `context.autoescape` of the supplied `Context` (bool) | only meaningful when `suppliedIsContext = True` |
| `leading : String` | the literal template text before the interpolated value | byte-for-byte `str` |
| `value : String` | the data value interpolated for the single template variable | byte-for-byte `str` |
| `trailing : String` | the literal template text after the interpolated value | byte-for-byte `str` |
| `renderValue : Bool → String → String` | `render_value_in_context(value, context)` with `context.autoescape` as the Bool | unchanged downstream callee; modeled abstractly (see refinement.md) and bound to the REAL callee in G-CONF |
| result `: String` | the rendered output string | byte-for-byte `str` |

`String` ↔ Python `str` is the identity bijection (byte-for-byte).

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The downstream value-rendering
  step `render_value_in_context` is left as a universally-quantified parameter
  `renderValue` (the spec holds for EVERY value-renderer), so the proof consumes
  no property of it and there is no `axiom <callee>_prop`. The modeled change is
  solely WHICH escaping flag is selected for that step. `axiom_check.py` is a skip
  stub.
- Flag dependency: the selected escaping flag depends on `isinstance(context,
  Context)` and either the supplied context's `autoescape` or the engine's
  `autoescape`. G-CONF fuzzes all three booleans plus the value/literal strings.

## G-CONF fuzz seed
- pinned seed: `11119`
- ≥10^5 fuzzed `(engineAutoescape, suppliedIsContext, suppliedCtxAutoescape,
  value)` tuples over a fixed literal-framed template (`obj:{{ obj }}\n`), with
  values drawn from a pool exercising the HTML-significant characters
  (`< > & " '`) plus random strings. `renderValue` is bound to the REAL
  `render_value_in_context` callee.
