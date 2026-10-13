# refinement.md — django__django-14017

Operation correspondence between `implementation_mergeFilters` (Solution.lean)
and the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op).

## Modeled function: `Q._combine(self, other, conn)`

The patch changes exactly one line — the operand guard in `_combine`. Pre-patch
the guard accepts only `Q` instances; post-patch it also accepts any operand
whose `conditional` attribute is `True` (a standalone boolean-valued condition,
e.g. `Exists`). The remainder of `_combine` (the empty short-circuits and the
combined-node construction) is unchanged but is pinned in `problem_spec` for
frame discipline (directive 5), so a wrong impl cannot fill those outcomes.

| # | `implementation_mergeFilters` op | `patch.diff` / source counterpart | tag | justification |
|---|---|---|---|---|
| 1 | inputs `self : FilterNode`, `other : Operand`, `conn : Connector` | `_combine(self, other, conn)` | R | `FilterNode.empty` ↔ `not bool(self)`; `Operand.{isFilter,conditional,empty}` ↔ `isinstance(other,Q)` / `getattr(other,'conditional',False) is True` / `isinstance(other,Q) and not bool(other)`; `Connector` ↔ `Q.AND/Q.OR` (see mapping.md). |
| 2 | `if !(other.isFilter \|\| other.conditional) then return MergeResult.rejected` | post-patch guard `if not(isinstance(other, Q) or getattr(other,'conditional',False) is True): raise TypeError(other)` | R | The changed line, modeled deeply as the boolean test `isFilter ∨ conditional`. `isinstance(other,Q)` ↔ `other.isFilter`; `getattr(other,'conditional',False) is True` ↔ `other.conditional`. Rejection ↔ `MergeResult.rejected`. This is the bug-fixing op (G-DIFF: prepatch drops the `conditional` disjunct). |
| 3 | `if other.empty then return MergeResult.keepLeft` | `if not other: _,args,kwargs = self.deconstruct(); return type(self)(*args,**kwargs)` | R | empty-`other` short-circuit: result is a copy of `self`. `not other` ↔ `other.empty` (`tree.Node.__bool__`). Unchanged op, pinned for frame. |
| 4 | `if self.empty then return MergeResult.keepRight` | `elif not self: _,args,kwargs = other.deconstruct(); return type(other)(...)` | R | empty-`self` short-circuit: result is a copy of `other`. `not self` ↔ `self.empty`. Unchanged op, pinned for frame. |
| 5 | `return MergeResult.merged conn` | `obj = type(self)(); obj.connector = conn; obj.add(self, conn); obj.add(other, conn); return obj` | R | general branch: a fresh node joining both operands under `conn`. The internal `tree.Node.add` squashing shape is outside the fixed behavior; the model records only that a combined-under-`conn` node is produced. Unchanged op, pinned for frame. |

No op in `implementation_mergeFilters` is changed-inexpressible: the guard and
all branch outcomes are functions of observable operand attributes carried as
struct fields. There is **no consumed axiom** and **no opaque callee** (the
`axioms` region is empty); the proof discharges by case analysis on the boolean
fields. The `conditional`/`empty`/`isFilter` attribute reads are language-level
observations of the input carriers (Python attribute access / `bool()`), fully
captured by the modeled struct fields via the mapping.md bijection — there is no
external repo callee whose behavior the proof depends on, so **G-AX is a skip
stub**. The bijection itself is validated end-to-end by `conformance_check.py`
(G-CONF), which builds each abstract operand from a REAL Django object via the
mapping.md bijection and diffs the shadow against the real patched `Q._combine`.

## conf_skip

`conf_skip = false`: the impl region is all-R (no A-tagged-only branches), so
`conformance_check.py` builds the R/I shadow and differential-tests it against
the real `Q._combine` behaviour over fuzzed operands.
