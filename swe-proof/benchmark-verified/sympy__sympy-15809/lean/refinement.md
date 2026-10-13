# refinement.md — sympy__sympy-15809

Maps every operation in `implementation_min` / `implementation_max` to its
`patch.diff` counterpart. Tags: **R** = type refinement, **A-consumed** = proof
uses an axiom's property, **A-reference** = deep model validated == real callee
(G-AX), **I** = identical concrete op.

The gold patch is a single deletion (the empty-args `ValueError` guard) inside
`MinMaxBase.__new__`. The fix's observable effect: with the guard gone, an empty
argument tuple falls through to `if not args: return cls.identity`
(`miscellaneous.py:361-362`), returning `cls.identity` — `S.Infinity` for `Min`,
`S.NegativeInfinity` for `Max`. The reduction body (`_new_args_filter`,
`_collapse_arguments`, `_find_localzeros`, object build) is UNCHANGED.

## implementation_min

| Lean op | patch.diff / repo counterpart | tag |
|---|---|---|
| `args : List EVal` ← `*args` comparable-real tuple | `WithTop (WithBot ℚ)` ↔ comparable real / `oo` / `-oo` (mapping.md) | R |
| `acc := ⊤` (initial) | `Min.identity = S.Infinity` (`miscellaneous.py:796`) — the neutral element the empty case falls through to once the guard is deleted | R |
| `for x in args do acc := min acc x` | UNCHANGED reduction `_new_args_filter ∘ _collapse_arguments ∘ _find_localzeros ∘ object-build`, specialized to comparable reals = minimum of the multiset; modeled deeply as a `min`-fold | R |
| `return Except.ok acc` | normal return of the `Min` value (never raises for comparable args) | R |
| (NO `if not args: return Except.error ()`) | the DELETED guard — its absence is the fix; empty → identity, not error | I (the edit itself) |

## implementation_max

Symmetric: `acc := ⊥` ↔ `Max.identity = S.NegativeInfinity`
(`miscellaneous.py:731`); `max`-fold ↔ same UNCHANGED reduction (maximum);
deleted guard absent.

## Notes

- No A-consumed axioms; no A-reference opaque callees. The whole reduction is
  modeled deeply as a commutative-associative idempotent fold (R), so G-CONF
  (not G-AX) carries the faithfulness check. `axiom_check.py` is a skip stub.
- No changed-inexpressible op: the deletion's effect (empty → identity vs raise)
  is captured by the `args = [] → v = ⊤/⊥` clause in `problem_spec` together
  with the always-`Except.ok` existential. The prepatch impls reintroduce the
  guard (`return Except.error ()` on empty), which the spec's `∃ v, result =
  Except.ok v` clause refutes — the discriminating clause is exactly the bug.
