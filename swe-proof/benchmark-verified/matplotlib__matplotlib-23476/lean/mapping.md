# mapping.md — matplotlib__matplotlib-23476

## Instance
- repo: matplotlib/matplotlib
- base_commit: 33a0599711d26dc2b79f851c6daed4947df7c167
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch adds two lines to `Figure.__getstate__` in `lib/matplotlib/figure.py`
(the routine that builds the dict pickled when a figure is serialized):

```python
# discard any changes to the dpi due to pixel ratio changes
state["_dpi"] = state.get('_original_dpi', state['_dpi'])
```

Context: a figure's working resolution (`self._dpi`) may be temporarily scaled
up to match a high-density display surface. When a canvas is first attached, the
resolution is recorded as `self._original_dpi` (see `backend_bases.py:1656`,
`FigureCanvasBase.__init__`: `figure._original_dpi = figure.dpi`), and a later
device-pixel-ratio change rescales `self._dpi = ratio * self._original_dpi`
(`backend_bases.py:2104`). Before the patch, serializing a figure stored the
*scaled* `_dpi`; each save/restore cycle therefore re-applied the scaling and
the resolution grew without bound. The patch makes the serialized `_dpi` equal
the recorded baseline resolution when one exists, falling back to the current
`_dpi` otherwise — exactly the Python idiom `dict.get(key, default)`.

The F2P test `test_unpickle_with_device_pixel_ratio` builds `Figure(dpi=42)`,
scales the canvas device-pixel-ratio to 7 (so `fig.dpi == 42*7 == 294`), pickles
and unpickles, and asserts the restored `fig2.dpi == 42` (the baseline). With the
patch the pickled `_dpi` is `42` (the baseline); pre-patch it was `294`, and the
restored canvas re-recorded `_original_dpi = 294`, so repeated cycles doubled.

## Modeled function
I model the **selection of the resolution value recorded into a figure's
serialized state** — the single observable component the patch changes — as a
total function of two data items: the figure's current working resolution and
the optional recorded baseline resolution. This is the smallest unit whose
observable behavior the patch changes and the F2P test pins. It is a pure
`dict.get(key, default)` selection with no I/O; its whole observable behavior is
the returned resolution value.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_serializedFigureDpi` | the assignment `state["_dpi"] = state.get('_original_dpi', state['_dpi'])` inside `Figure.__getstate__` (`lib/matplotlib/figure.py:3026`, post-patch) |
| `problem_spec_serializedFigureDpi` | the post-condition the recorded resolution value must satisfy |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `currentDpi : Rat` | `state['_dpi']`, the figure's current working resolution at serialization time | exact rational ↔ the (always finite, positive) dpi float; the fix performs no arithmetic, only value selection, so `Rat` models it exactly. Float values used by the test/fuzzer (42, 294, …) are exact rationals. |
| `baselineDpi : Option Rat` | `state.get('_original_dpi', …)`: whether the figure carries a recorded `_original_dpi` attribute | `none ↔ "_original_dpi absent"` (no canvas ever attached → `dict.get` returns its default); `some d ↔ "_original_dpi == d"` |
| result `: Rat` | the value assigned to `state['_dpi']` | identity bijection on the dpi value domain |

`Rat` ↔ the Python "dpi value" domain is the identity bijection on the finite
positive rationals the resolution ever takes; selection (not arithmetic) is all
the fix does.

## Callee provenance / flag deps
- No unchanged repo callee is consumed. `dict.get(key, default)` is a total
  built-in selector modeled directly (the baseline-or-current cascade); the two
  resolution values enter as plain data. There is no `opaque` callee and no
  `axiom <callee>_prop`; the `axioms` region is empty and `axiom_check.py` is a
  skip stub.
- No flag dependency: the selection branches only on the presence of the
  recorded baseline, which G-CONF fuzzes (present vs absent).

## G-CONF fuzz seed
- pinned seed: `23476`
- ≥10^5 fuzzed `(currentDpi, baselineDpi)` tuples; resolutions drawn from a pool
  including the F2P-relevant `42` and `294` (= 42*7), typical dpi `72/100/200`,
  and random finite positives, with the baseline present vs absent uniformly
  mixed. The oracle exercises the real patched `Figure.__getstate__` and reads
  back `state['_dpi']`.
