# refinement.md — matplotlib__matplotlib-23476

Maps every operation in `implementation_serializedFigureDpi` to its
`patch.diff` counterpart. The patch adds one assignment inside the figure's
state-capture routine; the observable behavior it governs is the resolution
value recorded into the serialized figure state (see mapping.md). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
deep-modeled changed op validated == real callee, **I** identical concrete op.

## Patch (post-patch)
```python
# lib/matplotlib/figure.py, Figure.__getstate__
# discard any changes to the dpi due to pixel ratio changes
state["_dpi"] = state.get('_original_dpi', state['_dpi'])
```
`state['_dpi']` is the figure's current working resolution at capture time;
`state.get('_original_dpi', state['_dpi'])` returns the recorded baseline
resolution `state['_original_dpi']` when that key is present, else falls back to
the current working resolution.

## Operation correspondence
| # | Lean op (`implementation_serializedFigureDpi`) | patch.diff / governed op | tag | note |
|---|---|---|---|---|
| 1 | `let mut value := currentDpi` | the `default` argument of `state.get('_original_dpi', state['_dpi'])`, i.e. `state['_dpi']` (the current working resolution) | R | `currentDpi : Rat ↔ state['_dpi'] : float`; identity bijection on the finite positive resolution domain. This is the fallback value used when no baseline is recorded. |
| 2 | `match baselineDpi with \| some d => value := d \| none => pure ()` | `dict.get('_original_dpi', default)`: when the figure carries a recorded baseline `_original_dpi`, that value is taken; when absent, the default is kept | R | `baselineDpi : Option Rat` models `state.get('_original_dpi', …)`: `some d ↔ "_original_dpi == d"` (key present), `none ↔ "key absent"` (dict.get returns its default). |
| 3 | `return value` | the assignment `state["_dpi"] = …` (the selected value becomes the recorded resolution) | I | the function's returned value IS the value written into the serialized state. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the real patched serialization behavior (the value
`Figure.__getstate__` writes into `state['_dpi']`) over ≥10^5 fuzzed inputs.
