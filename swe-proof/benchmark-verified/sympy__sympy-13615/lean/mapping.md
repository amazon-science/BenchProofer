# mapping.md — sympy__sympy-13615

## Symbol binding (file:line @ base_commit 50d8a102f0)

- Modeled function: `Set._complement(self, other)`, the **`FiniteSet` branch**,
  `sympy/sets/sets.py:217-219` @ base_commit (the single line replaced by the
  gold patch; post-patch body at `sympy/sets/sets.py:219-229`).
- Lean triple: `problem_spec_partitionByMembership` /
  `implementation_partitionByMembership` / `correct_partitionByMembership`.

## What the branch computes

For the relative-complement `other - self` when `other` is a finite collection
of elements, each element `el` of `other` is classified by a three-valued
membership test of `el` against `self`:

- definitely a member  → the element is removed from the difference;
- definitely NOT a member → the element is retained directly;
- undetermined (the membership query yields neither a definite yes nor a
  definite no, e.g. a free symbol against a numeric interval) → the element is
  kept aside in an *unevaluated* difference, NOT asserted to be outside `self`.

The pre-patch code lumped "definitely-not" and "undetermined" together (it
retained every element whose membership test was not exactly the definite-yes
sentinel), wrongly asserting undetermined elements lie outside `self`.

## The membership classifier (callee provenance)

`self.contains(el)` (`Set.contains`, `sympy/sets/sets.py`) is an **unchanged**
callee the branch CALLS but does NOT modify. The gold patch's local
`ternary_sift` normalizes its result:

```python
def ternary_sift(el):
    contains = self.contains(el)
    return contains if contains in [True, False] else None
```

i.e. it maps the raw membership result to one of three buckets. In Lean this
normalized classifier is modeled as an **input parameter**
`contains : α → Option Bool` with the bijection:

| sympy `self.contains(el)` | `ternary_sift(el)` | Lean `contains el` |
|---|---|---|
| `True`  (sympy `S.true` / Python `True`) | `True`  | `some true`  |
| `False` (sympy `S.false` / Python `False`) | `False` | `some false` |
| anything else (symbolic / undetermined)   | `None`  | `none`       |

Because the classifier is a parameter (not an opaque global), the spec is
grounded directly in it and the proof consumes **no callee axiom**. The real
callee is exercised by G-CONF (`conformance_check.py`), which drives the real
`Set._complement` and decomposes its result; G-AX is therefore a skip stub.

## Lean ↔ Python type bijection (G-CONF / G-AX)

| Python | Lean |
|---|---|
| element of `other` (a sympy `Expr`/`Symbol`/`Number`) | `α` (abstract carrier) |
| `other` (a `FiniteSet`, iterated) | `other : List α` (iteration order; raw, pre-dedup) |
| ternary key `{True,False,None}` | `Option Bool` (`some true` / `some false` / `none`) |
| `sifted[False]` (retained-directly list) | `result.kept : List α` |
| `sifted[None]` (undetermined list)        | `result.unresolved : List α` |
| `sifted[True]` (removed; appears nowhere)  | — (in neither output list) |
| `Union(FiniteSet(*sifted[False]), Complement(FiniteSet(*sifted[None]), self, evaluate=False) if sifted[None] else S.EmptySet)` | `{ kept := …, unresolved := … } : ComplementResult α` |

The `Union`/`FiniteSet`/`Complement(...evaluate=False)`/`EmptySet` assembly is an
**R** (type-refinement) op: the structured result object ↦ the two-field
`ComplementResult` carrier. When `unresolved = []`, the Python builds
`Union(FiniteSet(*kept), S.EmptySet) == FiniteSet(*kept)`, represented by
`{ kept, unresolved := [] }` — equivalent.

`FiniteSet(*xs)` canonicalizes (dedup + sort); the Lean lists are the raw
order-preserving `sift` output before that canonicalization. G-CONF compares the
*assembled set objects* (`==`) so canonicalization is on both sides equally.

## Flag dependencies

None. The branch has no mode flag.

## Pinned G-CONF fuzz seed

`conf_seed = 13615`.
