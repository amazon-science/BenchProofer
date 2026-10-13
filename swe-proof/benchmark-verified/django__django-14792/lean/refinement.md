# refinement.md — django__django-14792

Maps every operation in `implementation_getTimezoneName` to its `patch.diff`
counterpart in `django/utils/timezone.py::_get_timezone_name`. Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
deep-modeled changed op validated == real callee, **I** identical concrete op.

## Patch (post-patch `_get_timezone_name`)
```python
def _get_timezone_name(timezone):
    return timezone.tzname(None) or str(timezone)
```

## Operation correspondence
| # | Lean op (`implementation_getTimezoneName`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut name := tzStr` | `str(timezone)` (the right operand of `or`, the fallback) | R | `str(timezone) : str ↔ tzStr : String`. Initialize accumulator to the full textual form (the value used when the label is falsy). |
| 2 | `match tzLabel with \| some s => if s ≠ "" then name := s` | `timezone.tzname(None) or …` selecting the left operand when truthy | R | `timezone.tzname(None) : str\|None ↔ tzLabel : Option String`. Python `or` keeps the left operand iff it is truthy; for a `str`/`None` value the truthy case is exactly `some s` with `s ≠ ""`. Modeled as a `match` on the optional plus the non-empty test. |
| 3 | `\| none => pure ()` | left operand `None` is falsy ⇒ `or` yields the right operand | R | `None ↔ none`; falls through to the already-initialized `tzStr`. |
| 4 | `return name` | `return <selected operand>` | I | return the chosen display name. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the real patched `_get_timezone_name` behavior over ≥10^5
fuzzed inputs (real time-zone objects + synthetic optional/str pairs).
`conf_skip = false`.

## Prepatch is the real bug
`Solution_prepatch.lean` ships the pre-patch impl: `name := tzStr; return name`
— it always returns the full textual form and never consults the short label.
This is exactly `return str(timezone)` (the pre-patch body). It cannot satisfy
the spec's discriminating clause (`tzLabel = some s, s ≠ "" ⇒ result = s`): when
the label is present and non-empty the prepatch returns `tzStr`, which need not
equal `s`, so `correct_getTimezoneName` is unclosable (G-DIFF). This is the F2P
behavior: a fixed-offset zone such as `Etc/GMT-10` must display as its offset
label `+10` rather than its full textual form.
