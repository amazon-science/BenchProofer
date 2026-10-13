# mapping.md — psf__requests-1921

## Symbol binding
- Modeled function: `merge_setting(request_setting, session_setting, dict_class=OrderedDict)`
  at `requests/sessions.py:34` @ base_commit `3c88e520da24ae6f736929a750876e7654accc3d`.
  The gold patch changes lines 59–61 region (adds a final comprehension after the
  per-request `None`-deletion loop, before `return merged_setting`).
- Lean names (de-narrated, do NOT echo the repo symbol): `effectiveSetting`.
  - `problem_spec_effectiveSetting`, `implementation_effectiveSetting`,
    `correct_effectiveSetting`.

## Modeled branch
`merge_setting` has several early-return branches (lines 41–52): `session_setting
is None` → return request; `request_setting is None` → return session; non-`Mapping`
operands → return request (the "Bypass if not a dictionary, e.g. verify" branch).
**None of these branches are touched by the fix.** The fix is entirely in the
both-operands-are-`Mapping` tail (lines 54–62). We therefore model ONLY that tail:
both inputs are dictionaries, given directly as the two key/value lists. This is
the focused changed-behavior model (SPEC_GUIDE §3, "read the changed functions").

## Lean ↔ Python type bijection  (used by G-CONF and G-AX)
| Python (at base_commit)            | Lean model                              |
|------------------------------------|-----------------------------------------|
| a setting dict (OrderedDict)       | `List (String × Option String)` — insertion-ordered, unique keys |
| a dict value that is a real value  | `some s : Option String`                |
| a dict value that is `None`        | `none : Option String` (the null sentinel) |
| `to_key_val_list(d)` (= `d.items()`) | identity on the assoc-list model (I leg) |
| `dict_class(items)` / `OrderedDict`| `List` built left-to-right with in-place key update (`dictSet` fold) |
| `merged.update(req_items)`         | a `dictSet` fold over `req` (request value wins; existing key keeps its slot) |
| `del merged[k]`                    | `List.filter (key ≠ k)`                 |
| `dict((k,v) for (k,v) in items if v is not None)` (the NEW line) | `List.filter (·.2.isSome)` |

`dict_class` is the DEFAULT `OrderedDict` in this model (case-sensitive keys). The
header call site instantiates `dict_class=CaseInsensitiveDict`; case-insensitivity
is an orthogonal key-type refinement the fix does NOT touch, so G-CONF fuzzes the
default `OrderedDict` instantiation with distinct case-disjoint keys.

## Callee provenance / flag deps
- `to_key_val_list` — UNCHANGED callee; on a dict it returns `list(d.items())`. In
  the assoc-list model this is the identity (I leg). No axiom consumed.
- `dict.update`, `del`, the dict-comprehension filter — language primitives,
  modeled structurally (R/I). No opaque callee, no consumed axiom.
- No `opaque` callee is declared; the proof consumes no `_prop` axiom.
  ⇒ `axiom_check.py` is a skip stub; G-AX = skip.

## G-CONF fuzz seed
`SEED = 1921` (pinned in conformance_check.py).
