# refinement.md — operation correspondence (pydata__xarray-6938)

Maps every op in `implementation_toIndexVariable` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) ·
**I** identical op.

The patched Python (`IndexVariable.to_index_variable`) replaces `return self`
with `return self.copy()`. `IndexVariable.copy` builds a structural duplicate
(`self._replace(data=self._data.copy(...))`) — same `dims`/`data`, but a NEW
object. We model the live-object universe as a heap (`Array VarRec`) so the
"new object vs same object" distinction is expressible; producing the
independent object is modeled DEEPLY as appending a fresh slot duplicating the
source record.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `heap : Array VarRec`, `src : Nat` | the live objects + `self` reference | R | object-set ↔ heap, reference ↔ handle bijection (mapping.md) |
| 2 | `let fresh := h[src]!` | `self._replace(data=self._data.copy(...))` copies the source's fields | R | the changed op modeled deeply: the produced object carries the SAME `dims`/`data` as the source. (`copy` preserves these fields; index data is immutable so the copy is value-identical.) |
| 3 | `let handle := h.size` | the *identity* of the object `copy()` returns — a NEW object (`a is not b`) | R | the **fix** modeled deeply: the produced object's identity is a brand-new handle (`= heap.size`), distinct from every pre-existing handle incl. `src`. Pre-patch `return self` reuses `src`. |
| 4 | `h := h.push fresh` | allocation of the new object by `copy()` | R | appending a fresh slot = materializing a new, independent object; existing slots are framed unchanged (the source is untouched). |
| 5 | `return (h, handle)` | `return self.copy()` | I | return the produced object together with the (grown) object universe |

No A-consumed rows: the proof discharges the freshness/frame/content spec
directly from the `push` semantics; no UNCHANGED callee property is assumed
(axioms region empty, G-AX is a skip stub).

No A-reference rows: the copy semantics are not abstracted behind an opaque
callee — they ARE the modeled changed op (rows 2–4), exercised end-to-end by
G-CONF. There is no isolated real callee to validate, so G-AX has nothing to
check.

No changed-inexpressible op.

## Discriminating clause (G-DIFF)
The spec clause `result.2 = heap.size` (freshness) together with
`result.1.size = heap.size + 1` (the universe grows by one) is the
discriminator. The prepatch impl `return (heap, src)` (the actual bug,
`return self`) yields `result.2 = src` and `result.1.size = heap.size`. With the
precondition `src < heap.size` we have `src ≠ heap.size`, so the freshness
clause is false; and the size clause is `heap.size = heap.size + 1`, also false.
Hence prepatch `correct_toIndexVariable` cannot close — the G-DIFF signal — and
no aliasing implementation can satisfy the frozen `problem_spec_toIndexVariable`.
