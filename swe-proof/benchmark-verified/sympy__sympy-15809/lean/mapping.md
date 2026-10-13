# mapping.md — sympy__sympy-15809

## Symbol binding (file:line @ base_commit 28d913d3cead6c5646307ffa6540b21d65059dfd)

- Changed function: `MinMaxBase.__new__`
  — `sympy/functions/elementary/miscellaneous.py:341`
- Removed guard (the fix): `sympy/functions/elementary/miscellaneous.py:342-343`
  ```python
  if not args:
      raise ValueError("The Max/Min functions must have arguments.")
  ```
- Downstream identity return (UNCHANGED, now reachable for empty input):
  `miscellaneous.py:361-362` — `if not args: return cls.identity`
- Single-arg return (UNCHANGED): `miscellaneous.py:364-365` —
  `if len(args) == 1: return list(args).pop()`
- `≥2`-arg reduction pipeline (UNCHANGED callees):
  `_new_args_filter` (`:509`), `_collapse_arguments` (`:374`),
  `_find_localzeros` (`:536`) → frozenset object build (`:367-371`).
- Identity constants:
  - `Max.identity = S.NegativeInfinity` — `miscellaneous.py:731`
  - `Min.identity = S.Infinity` — `miscellaneous.py:796`

`Min` and `Max` are two concrete subclasses of `MinMaxBase`; the single deletion
in `__new__` fixes both. We model the two as `implementation_min` /
`implementation_max` (they differ only by identity element and the reduction
direction), with `test_Min` / `test_Max` as the two independently-observable
behaviors (one prepatch each).

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean |
|---|---|
| comparable real `Expr` argument | finite `EReal` (a `(x : ℝ)` coerced) |
| `S.Infinity` (`oo`) | `(⊤ : EReal)` |
| `S.NegativeInfinity` (`-oo`) | `(⊥ : EReal)` |
| `*args` tuple of comparable reals | `List EReal` (call order preserved) |
| normal return value | `Except.ok` of an `EReal` |
| `raise ValueError(...)` | `Except.error ()` |
| `Min(*args)` result | `implementation_min args` |
| `Max(*args)` result | `implementation_max args` |

Modeling scope: the **comparable-argument** case of `MinMaxBase` — exactly the
case the new F2P assertions (`Min()==oo`, `Min(x)==x`, numeric/`oo` reductions)
and the deleted-guard fix exercise. Non-comparable *symbolic* arguments
(which build an unevaluated `Min`/`Max` object) are out of model scope and are
documented here, not silently dropped.

## Callee provenance — none consumed as axioms

There are **no opaque callees and no consumed `_prop` axioms**. The UNCHANGED
≥2-argument reduction pipeline (`_new_args_filter` ∘ `_collapse_arguments` ∘
`_find_localzeros` ∘ object build), specialized to comparable reals, computes
the minimum (resp. maximum) of the argument multiset. Since `Min`/`Max` over
comparable reals are commutative-associative idempotent reductions, this is
modeled **deeply** as `args.foldl min ⊤` (resp. `args.foldl max ⊥`) — an **R**
(type-refinement) leg, NOT an axiom. G-CONF differential-tests the fold against
real sympy over comparable inputs (this is where the reduction faithfulness is
checked).

The identity initialiser is the heart of the fix: `Min.identity = S.Infinity`
→ `⊤`, `Max.identity = S.NegativeInfinity` → `⊥`. With the empty guard removed,
the empty fold returns the identity, which is exactly the new behavior.

No flag dependency: the deletion is unconditional (independent of the
`evaluate` assumption).

## G-CONF fuzz seed

Pinned seed: **15809**. Fuzz inputs are `*args` lists of comparable sympy
numbers drawn from `{Integer(k) | -50 ≤ k ≤ 50} ∪ {Rational(p,q)} ∪ {oo, -oo}`,
length 0..6 (length 0 and 1 oversampled — they are the R/I discriminating legs).
