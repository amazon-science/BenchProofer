# mapping.md — pydata__xarray-2905

## Modeled function
- `as_compatible_data(data, fastpath=False)` —
  `xarray/core/variable.py:189` @ base_commit `6906eebf…` (worktree
  `$SCRATCH`). The single changed site is the
  "we don't want nested self-described arrays" unwrap step at line 221.

## The change (gold patch, line 221)
- before: `data = getattr(data, "values", data)` — unwrap the `.values`
  attribute from ANY object that exposes one.
- after: `if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)): data = data.values`
  — unwrap ONLY when the object is one of the recognized pandas container types.

All other lines of `as_compatible_data` are unchanged and irrelevant to the
fixed behavior (the F2P test reaches the function with a plain object whose
only notable trait is a `.values` attribute, exercising exactly this branch).

## Lean ↔ Python type bijection (G-CONF / G-AX use this)
| Python | Lean | notes |
|---|---|---|
| the incoming `data` object | `Obj` (`pure` region) | abstracted to the two observed traits |
| `isinstance(data, (pd.Series, pd.Index, pd.DataFrame))` | `Obj.isContainer : Bool` | true iff a recognized pandas container kind |
| `getattr(data, "values", <sentinel>)` presence/value | `Obj.payload : Option Obj` | `some p` iff object exposes a `.values` whose content is `p`; `none` if no `.values` attr |
| `data = data.values` (unwrap) | `data.payload.getD data` | replace by payload; payload-absent ⇒ unchanged |
| post-branch `data` | result `Obj` | what is handed to the rest of the pipeline |

Bijection note: `Option.getD data` models the post-condition that an unwrap on
an object lacking a payload is a no-op. In Python a recognized pandas container
always has `.values`, so the `payload = none` case never co-occurs with
`isContainer = true`; the model is total and the proof does not depend on that
co-occurrence.

## Callee provenance / flag deps
- No UNCHANGED callee is consumed as an axiom. The decision modeled is the
  `isinstance` type test + attribute unwrap, both expressed structurally on
  `Obj`. No `opaque`/`axiom` declarations are needed (deep model).
- `fastpath` flag: F2P path uses the default `fastpath=False`; not modeled
  (orthogonal early-return branch above the changed line).

## G-CONF fuzz seed
Pinned seed: `2905`.
