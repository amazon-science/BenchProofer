# refinement.md — operation correspondence (pydata__xarray-7393)

Each op of `implementation_arrayConvert` ↔ its `patch.diff` counterpart.
Tags: **R** type refinement, **A-consumed** axiom property consumed by proof,
**A-reference** deep model validated == real callee by G-AX, **I** identical op.

| # | Lean op (`implementation_arrayConvert`) | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut dtype := dtypeArg; if dtype.isNone then dtype := some selfDtype` | `if dtype is None:\n    dtype = self.dtype` (post-patch, lines added) | R | The optional requested dtype is defaulted to the adapter's stored original dtype. `None ↔ none`; `self.dtype ↔ selfDtype`. |
| 2 | `let d := dtype.getD selfDtype` | the value of `dtype` after the defaulting (`= self.dtype` when `None` was passed, else the requested dtype) | R | `d` is the EFFECTIVE dtype = `effectiveDtype selfDtype dtypeArg`. `getD selfDtype` is total and agrees with the post-defaulting value (after op 1, `dtype` is never `none`). |
| 3 | `match level with \| some _ => return castArray d rawArray.data` | `if self.level is not None:\n    return np.asarray(self.array.get_level_values(self.level).values, dtype=dtype)` | R | Selected level ⟶ re-present the raw level values at the effective dtype. `self.array.get_level_values(self.level).values ↔ rawArray.data`; `np.asarray(_, dtype=dtype) ↔ castArray d`. Bijection (dtype + in-range values) in mapping.md. |
| 4 | `\| none => return superArray d` | `else:\n    return super().__array__(dtype)` | R | No selected level ⟶ defer to the unchanged non-level conversion at the effective dtype. `super().__array__ ↔ superArray`. (`super().__array__` itself defaults `None`→`self.dtype`; post-patch `dtype` is already defaulted, and the value passed is identical either way — see mapping.md.) |

Every op is **R** (type refinement). There are no **A-consumed** axioms (no callee
contract is consumed — see mapping.md callee provenance) and no **I** ops beyond
the structural `match` control flow. There is no changed-inexpressible op: the
entire fix is the dtype defaulting (op 1–2) plus the level re-cast (op 3), both
modeled deeply over `Dtype`/`NpArray`.

`conf_skip = false` — the impl region is all-R (no A-tagged ops), so G-CONF
mechanically differential-tests it against the real patched `__array__`.
