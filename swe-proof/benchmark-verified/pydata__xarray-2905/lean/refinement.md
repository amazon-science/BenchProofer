# refinement.md — pydata__xarray-2905

Maps every op in `implementation_prepare` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof-consumed axiom ·
**A-reference** deep-modeled callee (G-AX) · **I** identical concrete op.

| # | `implementation_prepare` op | `patch.diff` counterpart | tag |
|---|---|---|---|
| 1 | `let mut result := data` | implicit: `data` flows into the changed block | I |
| 2 | `if data.isContainer then` | `if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)):` | R — the `isinstance` over the recognized pandas container tuple is refined to the boolean trait `Obj.isContainer` (mapping.md bijection) |
| 3 | `result := data.payload.getD data` | `data = data.values` | R — `.values` attribute access refined to `Obj.payload`; the no-payload case is the identity (`getD data`), faithful since a real pandas container always exposes `.values` |
| 4 | `return result` | post-branch value of `data` | I |

Notes:
- No A-consumed and no A-reference rows: the changed decision is modeled
  deeply (structural case split + attribute model), so there is no
  unchanged-callee axiom and no deep-model callee to validate by G-AX.
- The R legs (#2, #3) are exactly what G-CONF differential-tests: the shadow
  builds an object with a configurable `isinstance`-membership and `.values`
  presence and checks the unwrap decision matches the gold patch over fuzzed
  inputs.
- Discriminating clause vs prepatch: the prepatch unwraps unconditionally
  (op #2 dropped, mirroring the old `getattr(data, "values", data)`), so on an
  object with `isContainer=false` and a payload it returns the payload while the
  spec demands the object unchanged — the F2P bug.
