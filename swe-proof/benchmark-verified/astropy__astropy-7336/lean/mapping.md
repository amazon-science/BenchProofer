# mapping.md — astropy__astropy-7336

## Symbol binding (file:line @ base_commit)

Modeled function: the return-finalizing epilogue of the unit-validating function
wrapper `QuantityInput.__call__.<locals>.wrapper`.
- File: `astropy/units/decorators.py`
- `def wrapper(*func_args, **func_kwargs):` at line 162 @ base_commit.
- Modeled lines: 223–226 (the epilogue, after the wrapped function has produced
  `return_`):
  ```python
  if wrapped_signature.return_annotation is not inspect.Signature.empty:   # line 223 (pre-patch)
      return return_.to(wrapped_signature.return_annotation)               # line 224
  else:                                                                    # line 225
      return return_                                                       # line 226
  ```
- Gold-patch edit: line 223 — the guard becomes
  `if wrapped_signature.return_annotation not in (inspect.Signature.empty, None):`.

## Lean ↔ Python type bijection

| Lean | Python |
|---|---|
| `RetVal` (`{ payload : Nat }`) | the produced value `return_` (the wrapped function's raw return) — internal structure irrelevant to the contract; treated abstractly |
| `UnitObj` (opaque) | a concrete `astropy.units` unit object (e.g. `u.deg`) |
| `RetAnnotation.empty` | `wrapped_signature.return_annotation is inspect.Signature.empty` — no return annotation given |
| `RetAnnotation.noUnit` | `wrapped_signature.return_annotation is None` — an explicit `-> None` annotation |
| `RetAnnotation.unit u` | `wrapped_signature.return_annotation` is a concrete unit `u` (neither the sentinel nor `None`) |
| `convertTo ret u` | `return_.to(u)` — the real `Quantity.to` value conversion, applied only to a concrete unit `u` |
| `Except FinalizeError RetVal` | the finalize outcome: `.ok v` = the wrapper returned value `v`; `.error {}` = a conversion was attempted against a non-unit target and raised (the `None.to(...)` → `AttributeError` bug) |
| result `: Except FinalizeError RetVal` | the wrapper's finalize outcome |

The PATCHED guard `return_annotation not in (inspect.Signature.empty, None)` is
modeled by the `match` selector: only `.unit u` takes the conversion arm; both
`.empty` and `.noUnit` pass through.

The three-way `RetAnnotation` is the type refinement that makes the guard
expressible: Python's `not in (empty, None)` partitions annotations into
{`empty`, `None`} (passthrough) vs everything-else (concrete unit → convert);
`empty`↔`.empty`, `None`↔`.noUnit`, concrete↔`.unit u`. `convertTo` takes a
`UnitObj` (not a `RetAnnotation`) so the conversion primitive cannot be applied
to a non-unit target — the failure mode is represented by the `.noUnit` arm of
the impl returning `.error`, not by feeding a bad annotation to `convertTo`.

## Callee provenance + flag deps

- `convertTo` — A-reference. Models the UNCHANGED value conversion
  `Quantity.to(unit)` invoked on the concrete-unit branch (line 224). The patch
  does NOT modify this callee; it only changes WHEN the branch is taken. G-AX
  exercises the real `Quantity.to` and confirms (a) on the concrete-unit branch
  the wrapper's result equals `produced.to(unit)` with `result.unit == unit`, and
  (b) on the `empty`/`None` branches the value is passed through unchanged with no
  conversion attempted (the prepatch's `None.to(...)` would `AttributeError`).
  No flag dependency.

## Proof obligations

`correct_applyReturnAnnotation` is closed by case analysis on `annot`
(`empty`/`noUnit`/`unit u`); it consumes NO property axiom about `convertTo`.
Both `_prop` slots are therefore empty (the proof agent should not need the
axiom-propose loop).

## G-CONF fuzz seed

Pinned seed: `7336`. `conformance_check.py` differential-tests the R leg (the
three-way guard classification) and the I leg (passthrough) against the real
patched decorator over 1e5 fuzzed (produced-value, annotation) pairs, performing
the concrete-unit conversion with the real `Quantity.to`.
