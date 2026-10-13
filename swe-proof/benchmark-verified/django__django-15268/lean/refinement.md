# refinement.md — django__django-15268

Modeled function: `AlterTogetherOptionOperation.can_reduce_through(self, operation, app_label)`
(NEW method introduced by the patch — the entire behavioral delta of the fix).
Lean: `implementation_canOptimizeAcross`.

## Operation correspondence

`implementation_canOptimizeAcross selfKind selfName operation =`
`  baseCanOptimizeAcross selfName operation || (isAlterTogether operation.ty && decide (operation.ty ≠ kindTag selfKind))`

| # | Lean op (implementation_canOptimizeAcross) | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `baseCanOptimizeAcross selfName operation` = `!(affectsModel operation selfName)` | `super().can_reduce_through(operation, app_label)` which is `not operation.references_model(self.name, app_label)` (the NEW base-class `ModelOperation.can_reduce_through`) | A-reference | `references_model` is an UNCHANGED callee; its boolean value is observed but no property is consumed by the proof (it appears symbolically). Validated == real callee by G-AX. `!`/`not` is `I`. |
| 2 | `isAlterTogether operation.ty` | `isinstance(operation, AlterTogetherOptionOperation)` | R | type-tag bijection: `ty ∈ {alterUnique, alterIndex}` ⟺ `isinstance(...AlterTogetherOptionOperation)`. mapping.md. |
| 3 | `decide (operation.ty ≠ kindTag selfKind)` | `type(operation) is not type(self)` | R | exact-type inequality bijection: for two alter-together ops, exact-type differs ⟺ flavours differ ⟺ `operation.ty ≠ kindTag selfKind`. (Only reached under op #2, where both are alter-together.) |
| 4 | `&&` | `and` (Python `and`) | I | identical boolean conjunction |
| 5 | `\|\|` | `or` (Python `or`) | I | identical boolean disjunction |

Every op is R, A-reference, or I. No op is changed-inexpressible; no op is
axiomatized. No A-consumed axiom is used (the proof never consumes a `_prop`
property of `affectsModel` — it reasons about its boolean value symbolically),
so there is no dead axiom.

## reduce delegation (NOT separately modeled — behavior-preserving)

The patch also rewrites `ModelOperation.reduce`'s inline
`not operation.references_model(self.name, app_label)` into a call
`self.can_reduce_through(operation, app_label)` and introduces the base
`ModelOperation.can_reduce_through` returning exactly that old expression. For
`ModelOperation` (and any subclass that does not override `can_reduce_through`)
this is a pure refactor with identical behavior — tagged `I` (delegation) and
folded into row 1's `baseCanOptimizeAcross`. The ONLY observable behavior change
is the new `AlterTogetherOptionOperation.can_reduce_through` override, which is
exactly what the triple models. Hence one modeled function and one prepatch
(one independently-observable fixed behavior: cross-flavour reduction).

## Conformance (G-CONF) coverage

R/I legs (rows 1–5) are mechanically differential-tested by conformance_check.py:
the Python shadow builds the real `AlterUniqueTogether`/`AlterIndexTogether`/other
operations and calls the REAL `can_reduce_through` (A-reference leg row 1 uses the
real `references_model`), diffing against the Lean impl's R/I logic over ≥10⁵
fuzzed inputs. A-reference row 1 is additionally validated by axiom_check.py.
