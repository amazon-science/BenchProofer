# refinement.md — pydata__xarray-6599

Operation-by-operation correspondence between `implementation_coerceToFloat`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `to_floatable`
helper of `_ensure_numeric`). Tags: **R** type refinement, **A-consumed** proof
uses an axiom's property, **A-reference** deep model validated == real callee,
**I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if x.kind = ValKind.datetime then return datetimeToFloat x.raw` | `if x.dtype.kind == "M": return x.copy(data=datetime_to_numeric(x.data, offset=np.datetime64("1970-01-01"), datetime_unit="ns"))` | R (kind char ↔ `ValKind`; `x.copy(data=…)` carries values, modeled as the value list) + A-reference (the unchanged `datetime_to_numeric` callee, carried as the opaque `datetimeToFloat`) |
| 2 | `else if x.kind = ValKind.duration then return x.raw.map Float.ofInt` | `elif x.dtype.kind == "m": return x.astype(float)` | R (the int64-ns-buffer → float cast modeled deeply, element-wise `Float.ofInt`) |
| 3 | `else return x.data` | `return x` (the unchanged array, values as-is) | R (`x` returned unchanged ↔ its value list) |

Notes:

- **The fix is op 2.** Pre-patch, `to_floatable` had a single `if x.dtype.kind in
  "mM"` clause routing BOTH datetime and duration through `datetime_to_numeric`;
  the patch splits it into `== "M"` (op 1, unchanged behavior) and a NEW `elif ==
  "m"` (op 2, `x.astype(float)`). The duration branch is the only changed
  behavior and the only one the F2P test observes.
- **No A-consumed axiom.** The datetime callee `datetime_to_numeric` (op 1) is
  declared `opaque datetimeToFloat` and appears IDENTICALLY in the spec helper
  `coerceResult` and the impl, so the datetime branch closes by reflexivity — the
  proof consumes no *property* of it. It is therefore an **A-reference** (the
  unchanged callee carried by signature), not a consumed axiom; there is no
  `_prop` and **G-AX skips**. SPEC_GUIDE §3 forbids axiomatizing the changed op
  (op 2), so it is modeled deeply instead.
- **R legs (1–3) are mechanically refuted by G-CONF**: the Python shadow of the
  impl is diffed against an in-process replica of the post-patch `to_floatable`
  branch selection over ≥1e5 fuzzed inputs. The datetime reduction is modeled as
  the SAME stand-in on both oracle and shadow (it is unchanged and identical in
  spec and impl), so G-CONF tests the soundness-critical part: the branch
  *selection* by kind and the duration cast — never re-routing a duration through
  the datetime reduction.
- **Frame discipline (directive 5):** `problem_spec_coerceToFloat` pins the FULL
  result list to `coerceResult x` — no output component left free. The numeric
  branch is pinned to the input `data` (unchanged-component framing), the duration
  branch to the element-wise cast of `raw`, the datetime branch to the carried
  reduction.
