# refinement.md — operation correspondence (pytest-dev__pytest-5631)

Maps every op in `implementation_num_mock_patch_args` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The post-patch Python is:

```python
patchings = getattr(function, "patchings", None)
if not patchings:
    return 0
mock_sentinel = getattr(sys.modules.get("mock"), "DEFAULT", object())
ut_mock_sentinel = getattr(sys.modules.get("unittest.mock"), "DEFAULT", object())
return len(
    [p for p in patchings
     if not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel)]
)
```

The change replaces an equality-membership test (`p.new in sentinels`) with an
identity test (`p.new is mock_sentinel or p.new is ut_mock_sentinel`). Identity
is total; the count never depends on the (possibly ambiguous) truth value of an
equality comparison. We model the classifier deeply as `isCounted`.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `patchings : List Patching` | `function.patchings` (list of decoration objects) | R | decoration-list ↔ `List Patching`; each decoration abstracted to `(attributeName, isSentinel, eqWellDefined)` per mapping.md |
| 2 | `if patchings.isEmpty then return some 0` | `if not patchings: return 0` | I | empty/missing list short-circuits to 0 |
| 3 | `let mut count := 0` | `len([...])` accumulator (list comprehension building the counted set) | I | concrete count init |
| 4 | `for p in patchings do` | `[p for p in patchings ...]` | I | per-decoration iteration |
| 5 | `if isCounted p then count := count + 1` | `if not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel)` | A-reference | the introduced identity-based classifier modeled deeply (`!attributeName && isSentinel`); validated == the real post-patch classifier by G-AX (incl. numpy-like replacements). NOT axiomatized. |
| 6 | `return some count` | `return len(...)` (always an int) | R | result always present → `some _`; the `Option` codes the never-taken raise path |

No A-consumed rows: the proof discharges `isCounted` / the `for` loop directly;
no UNCHANGED callee property is assumed. No changed-inexpressible op.

## Discriminating clause (G-DIFF)
Op 5/6 against the prepatch. The pre-patch classifier compares `p.new` for
**equality** against the sentinels; for a non-attribute decoration whose
replacement has an ambiguous equality truth value (`eqWellDefined = false`, the
numpy-array case), that comparison aborts the whole computation. The prepatch
skeleton models this as an early `return none`. For any input list containing
such a decoration, the prepatch returns `none`, which cannot equal the spec's
`some ((patchings.filter isCounted).length)`; its `correct_num_mock_patch_args`
cannot close against the frozen `problem_spec_num_mock_patch_args`. That is the
G-DIFF signal, and it is exactly the F2P observation
(`test_mock_sentinel_check_against_numpy_like`: collection succeeds — no
`ValueError` — when a patch replaces with a numpy-like array).
