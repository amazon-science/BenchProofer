# refinement.md — operation correspondence (astropy__astropy-13977)

Each op of `implementation_dispatchOp` ↔ its `patch.diff` counterpart.
Tags: **R** type refinement, **A-consumed** axiom property consumed by proof,
**A-reference** deep model validated == real callee by G-AX, **I** identical op.

| # | Lean op (`implementation_dispatchOp`) | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `match inner with \| Outcome.completes r => return Result.value r` | the `try` body running to completion and returning `result` / `self._result_as_quantity(result, unit, out)` (lines 643-682, now inside the `try`) | R | The whole `try` body is abstracted to its OUTCOME `inner`. `Outcome.completes r` ⟷ "body returned `r`"; the value is handed back unchanged. Bijection in mapping.md. |
| 2 | `match inner with \| Outcome.fails => …` | `except (TypeError, ValueError) as e:` clause (lines 678-682) entered | R | `Outcome.fails` ⟷ "body raised `TypeError`/`ValueError`". |
| 3 | `let mut allDefer := true; for o in operands do allDefer := allDefer && o.defersToDefault` | `all(getattr(type(io), "__array_ufunc__", None) in ignored_ufunc for io in inputs_and_outputs)` | R | The Python `all(...)` generator over `inputs + out_normalized` ⟷ the `for`-loop conjunction over `operands`. Each `defersToDefault` ⟷ the per-operand membership test `... in ignored_ufunc`. `List.all` semantics on `[]` = `true`, matching `all([])` = `True`. |
| 4 | `if allDefer then return Result.surfacedError` | `else: raise e` (line 682) | R | All operands defer ⟹ no foreign handler exists ⟹ surface the original error. `Result.surfacedError` ⟷ re-raise `e`. |
| 5 | `else return Result.unhandled` | `if not all(...): return NotImplemented` (lines 679-681) | R | Some operand overrides ufunc dispatch ⟹ return `NotImplemented` so its handler is tried. `Result.unhandled` ⟷ `NotImplemented`. |

Every op is **R** (type refinement). There are no **A-consumed** axioms (no
callee contract is needed — see mapping.md callee provenance) and no **I** ops
beyond the structural control flow. There is no changed-inexpressible op: the
entire fix is the relocation of the body under a `try` plus the recovery
decision, both modeled deeply.

`conf_skip = false` — the impl region is all-R (no A-tagged ops), so G-CONF
mechanically differential-tests it against the real patched wrapper.
