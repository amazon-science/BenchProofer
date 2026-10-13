# refinement.md — django__django-11119

Maps every operation in `implementation_renderToString` to its `patch.diff`
counterpart in `Engine.render_to_string` (django/template/engine.py:149). Tags:
**R** type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
op left as the real repo callee in G-CONF (not axiomatized), **I** identical
concrete op.

## Patch (post-patch `render_to_string`, context-construction branch)
```python
def render_to_string(self, template_name, context=None):
    ...
    if isinstance(context, Context):
        return t.render(context)
    else:
        return t.render(Context(context, autoescape=self.autoescape))
```

The single changed token is the `autoescape=self.autoescape` keyword added to the
freshly-built `Context`; everything else is the framing render. The downstream
`t.render(...)` ultimately escapes-or-emits the interpolated value through
`render_value_in_context`, which branches on `context.autoescape`. Literal text
nodes pass through unchanged.

## Modeling decision
The observable behavior of `render_to_string` is the rendered output string. For a
template that is literal text framing a single interpolated value, that output is

    leading ++ render_value_in_context(value, context) ++ trailing

where `render_value_in_context` reads exactly one thing off the context — its
`autoescape` flag. The fix changes WHICH flag the context carries in the
plain-data branch (engine's flag, not the hard-wired default). So the model:

- selects the effective escaping flag from `(suppliedIsContext, suppliedCtxAutoescape,
  engineAutoescape)` exactly as `render_to_string` selects which `Context` /
  flag governs the render;
- applies an arbitrary `renderValue : Bool → String → String` (standing for the
  unchanged downstream value-rendering step) to that flag and the value;
- frames it with the unchanged literal text.

Universally quantifying `renderValue` makes the spec hold for EVERY value-renderer,
so the only thing it can pin is that the correct flag reaches the step — which is
exactly the bug.

## Operation correspondence
| # | Lean op (`implementation_renderToString`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut autoescape := suppliedCtxAutoescape` | `isinstance(context, Context)` branch returns `t.render(context)` — renders with the supplied context's own `autoescape` | R | `context.autoescape : bool ↔ suppliedCtxAutoescape : Bool`; the ready-made-context branch uses the supplied flag. |
| 2 | `if !suppliedIsContext then autoescape := engineAutoescape` | `else: ... Context(context, autoescape=self.autoescape)` | R | plain-data branch builds a fresh context carrying the ENGINE's flag (`self.autoescape : bool ↔ engineAutoescape : Bool`). This is the fixed token. |
| 3 | `renderValue autoescape value` | `render_value_in_context(value, context)` reading `context.autoescape` | A-reference | unchanged downstream callee; left abstract (universally quantified) in the spec/proof and bound to the REAL `render_value_in_context` in G-CONF. No property is consumed, so it is NOT an `axiom` (not A-consumed) and NOT deep-modeled. |
| 4 | `leading ++ renderValue autoescape value ++ trailing` | the literal text nodes surrounding the variable node in the rendered output | I | string concatenation ↔ the template renderer concatenating node outputs; literal nodes are unaffected by the flag. |
| 5 | `return ...` | `return t.render(...)` | I | return the rendered string. |

## R/I legs ⇒ G-CONF
Ops 1, 2 (flag selection, R) and 4, 5 (string framing, I) are the R/I content.
Op 3 is the A-reference: G-CONF leaves it as the REAL `render_value_in_context`
(it does NOT substitute an axiom model), which is precisely how the R/I flag-
selection legs are isolated and tested. `conf_skip = false`: the impl region has
genuine R/I content (the flag selection is the fixed behavior), so
`conformance_check.py` differential-tests the shadow (flag selection + framing,
with `render_value_in_context` as the oracle's value step) against the patched
`render_to_string`'s rendered output over ≥10^5 fuzzed inputs.

## No A-consumed row
The proof consumes no property of `renderValue` (it is universally quantified), so
`meta.json axioms = []`. Op 3 is recorded as an A-reference solely to document the
G-CONF binding to the real callee; there is no `opaque`/`axiom` declaration in
`Solution.lean` and `axiom_check.py` is a skip stub.

## F2P alignment
`test_autoescape_off` builds `Engine(autoescape=False)` and renders
`test_context.html` (`obj:{{ obj }}\n`) with `{'obj': '<script>'}` (plain data,
not a `Context`), expecting `obj:<script>\n` (UN-escaped). Pre-patch the fresh
context carried the default `autoescape=True`, so the value was escaped to
`&lt;script&gt;` — the discriminating clause `problem_spec_renderToString` pins
(plain-data ⇒ engine flag governs) and the prepatch impl (else-branch hard-wires
`true`) cannot satisfy. `patch.diff` (gold verbatim) makes the harness resolve.
