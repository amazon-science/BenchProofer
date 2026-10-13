# refinement.md — pydata__xarray-6721

Modeled function: `get_chunksizes(variables)` (`xarray/core/common.py`).
Lean: `implementation_getChunksizes` (Solution.lean impl region).

Every operation of `implementation_getChunksizes` mapped to its `patch.diff`
(post-patch `get_chunksizes`) counterpart. Tags: **R** type refinement,
**I** identical concrete op, **A-consumed** proof-consumed axiom, **A-reference**
deep-modeled callee validated by G-AX.

| # | Lean op (impl region) | Python op (post-patch) | tag | note |
|---|---|---|---|---|
| 1 | `let mut chunks := []` | `chunks: dict = {}` | I | empty accumulator. `List (String × List Nat)` ↔ `dict[str, tuple[int,...]]` (R for the carrier type). |
| 2 | `for v in vars do` | `for v in variables:` | I | iterate variables front-to-back. |
| 3 | `if v.hasChunks then` | `if hasattr(v._data, "chunks"):` | R | `hasChunks : Bool` refines the truthiness of `hasattr(v._data, "chunks")` — a metadata-only predicate read off the underlying handle without materializing the variable. |
| 4 | `for p in v.chunksizes do` | `for dim, c in v.chunksizes.items():` | R | `chunksizes : List (String × List Nat)` refines `v.chunksizes : Mapping[str, tuple[int,...]]`, in dimension order. |
| 5 | `match chunks.lookup p.1 with \| some c' => if c' ≠ p.2 then return .error ()` | `if dim in chunks and c != chunks[dim]: raise ValueError(...)` | I | the inconsistent-chunk rejection. The message text is abstracted to `.error ()` (R on the error payload — the F2P concerns whether it raises, not the wording). |
| 6 | `\| none => chunks := chunks ++ [p]` and the agreeing-`some` fallthrough | `chunks[dim] = c` | I | append a new dimension (first-seen order) / leave an agreeing dimension unchanged. `dict` assignment with an equal value is a no-op; a new key appends in insertion order — matched by `lookup`/`++`. |
| 7 | `return .ok chunks` | `return Frozen(chunks)` | R | `Frozen` is a read-only view over the same mapping; `.ok` wraps the success result. |

No row is **A-consumed** or **A-reference**: the modeled function calls no
unchanged callee whose behavior the proof must assume — `hasChunks`,
`chunksizes`, `isDuckArray`, `materializeRaises` are observable *inputs*
(properties of each `Variable`), and the merge/rejection is spelled out (I).
Hence `conf_skip = false` (impl is R/I, mechanically differential-tested by
G-CONF) and G-AX is a skip stub.

## The fix, in refinement terms
The gold patch changes op #3's *source operand* from `v.data` to `v._data`.
Both yield the **same** `hasattr(..., "chunks")` truth value for every variable
(a chunks-bearing array is always a duck array, so `v.data` returns `_data`
unchanged). The only difference is a **side effect**: `v.data` forces
`v.values` (materialization) for a non-duck `_data`, which raises for an
inaccessible store. `implementation_getChunksizes` (Solution.lean) inspects the
metadata predicate `hasChunks` directly and never materializes — modeling the
post-patch behavior. The prepatch (`Solution_prepatch.lean`) inserts the
materialization side effect (`if !v.isDuckArray && v.materializeRaises then
return .error ()`), so it diverges from the spec exactly on a variable that is
unchunked, non-duck, and whose store is inaccessible — which is the GH6538 F2P
scenario.
