# refinement.md — operation correspondence (sympy__sympy-20590)

Maps every op in `implementation_immutableInstances` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) ·
**I** identical op.

## What the patch does
`patch.diff` adds `__slots__ = ()` to the printing-support mixin class
(`sympy/core/_print_helpers.py`). In CPython, an instance carries a per-instance
attribute dictionary (`__dict__`, making it freely mutable) iff at least one
class in its ancestry — other than `object` — fails to declare an empty
`__slots__`. Every ancestry layer of the reported concrete type already pinned
its layout EXCEPT this mixin; the patch flips the one offending layer.

We model this behaviour deeply: the abstract observable is `result : Bool` (the
instance is immutable, i.e. has no `__dict__`), determined by the conjunction of
the per-layer layout-pinning flags. The post-patch mixin layer pins its layout,
contributing the `true` initial accumulator; the remaining ancestry layers'
flags are the `otherLayers` input.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut immutable := true` | the patched mixin layer now declares `__slots__ = ()` → it pins its layout, adding no `__dict__` | R | the changed layer's contribution is the boolean `true` (pins layout). Bool ↔ "declares empty `__slots__`" bijection (mapping.md). This is the line the patch adds. |
| 2 | `for pins in otherLayers do` | CPython walks the type's ancestry layers when deciding the instance layout | I | per-ancestry-layer iteration |
| 3 | `immutable := immutable && pins` | a single ancestry layer that leaves its layout open reopens `__dict__` for the instance (conjunction of all layers' pinning) | I | concrete conjunction-fold of the layout rule; modeled deeply, NOT axiomatized |
| 4 | `return immutable` | the resulting instance has no `__dict__` (is immutable) iff all layers pinned | I | the observable result |

No A-consumed rows and no A-reference rows: the layout rule is a pure fold over
the inputs, invoking no unchanged repo callee. The proof discharges `allPin`
directly. No changed-inexpressible op (the whole fix is the layout rule, modeled
exactly). G-AX = skip.

## Discriminating clause (G-DIFF)
The single op the patch adds is the changed layer pinning its layout (impl op #1,
`let mut immutable := true`). The prepatch impl initialises the accumulator to
`false` (the mixin layer leaves its layout open, contributing a `__dict__`
regardless of the others), so its result is `allPin otherLayers && false = false`
for every input — it can NEVER equal `allPin otherLayers` (which is `true` when
all other layers pin, e.g. `otherLayers = []`). Therefore the carried gold proof
cannot close `correct_immutableInstances` against the buggy impl. That is the
G-DIFF signal, and it mirrors the F2P test `test_immutable`
(`assert not hasattr(b1, '__dict__')`).
