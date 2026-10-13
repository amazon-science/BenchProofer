# mapping.md — sympy__sympy-12489

## Instance
- repo: sympy/sympy
- base_commit: aa9780761ad8c3c0f68beeef3a0ce5caac9e100b
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change (one behavior, applied at many sites)
The object-creation machinery of the arrangement class always produced an
instance of the *base* class, even when invoked on a derived class. The gold
patch routes every construction through the receiver's class instead, so a
construction performed on behalf of a derived class yields an instance of that
derived class. Concretely the gold patch turns the internal
`Basic.__new__(Perm, perm)` constructor (reached through the static helper
`_af_new`) into a `classmethod` that builds `Basic.__new__(cls, perm)`, and
replaces every bare `_af_new(...)` / `Perm(...)` reference inside the class with
`self._af_new(...)` / `cls._af_new(...)` / `cls(...)`. The net observable effect,
exercised by the FAIL_TO_PASS test, is that an arrangement produced *by* an
operation on a value carries the **family/kind of that value** rather than always
the base family.

## Modeled representative — `Permutation.__mul__`
| field | value |
|---|---|
| file @ base_commit | `sympy/combinatorics/permutations.py` |
| function | `Permutation.__mul__` (def at line 1244; the patched site is `return _af_new(perm)` at line 1303 → post-patch `return self._af_new(perm)`) |
| role | modeled representative of the single logical change |

`__mul__` is the cleanest representative of the patched behavior that the F2P
test pins:

```python
assert type(p * q) == CustomPermutation   # p is a derived value, q the base value
assert type(q * p) == Permutation         # q.__mul__(p): left operand is base
```

Post-patch, `a * b` returns an object of `type(a)` (the LEFT operand's class).
Pre-patch it always returned an object of the base class. The underlying array
form (the composition itself) is byte-for-byte unchanged by the patch — only the
*class of the produced object* changed.

### `__mul__` body (unchanged composition + patched constructor)
```python
def __mul__(self, other):
    a = self.array_form
    b = other.array_form        # __rmul__ guarantees other is an arrangement
    if not b:
        perm = a
    else:
        b.extend(list(range(len(b), len(a))))   # pad b up to len(a)
        perm = [b[i] for i in a] + b[len(a):]
    return _af_new(perm)         # PRE-PATCH: always base class
    # return self._af_new(perm)  # POST-PATCH: class of the left operand
```

`_af_new(perm)` → `Basic.__new__(Perm, perm)` (pre) vs
`self._af_new(perm)` → `Basic.__new__(type(self), perm)` (post): only the bound
class differs; `perm` (the array form) is identical.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)
An arrangement object is modeled by the Lean structure `Perm`:

| Lean | Python | note |
|---|---|---|
| `Perm.arr : List Int` | `self.array_form` (a `list[int]`, a permutation of `range(n)`) | the underlying mapping |
| `Perm.fam : Nat` | the class/family of the object: `type(self)` | `0` denotes the base family; any other value denotes a distinct derived family |
| `implementation_mul self other : Perm` | `self.__mul__(other)` | result object |
| `result.arr` | `(self * other).array_form` | composition (frame component) |
| `result.fam` | family of `type(self * other)` | the discriminating component |
| `afMul a b : List Int` | the inline list-comprehension composition in `__mul__` | pure, unchanged by the patch |

The family bijection for G-CONF: an integer/string tag identifies each Python
class; the base class maps to family `0`, a custom subclass to a distinct tag.
G-CONF compares `(family-of-result, result.array_form)` of the real patched
`__mul__` against the shadow.

## Callee provenance / flag deps
- The array-form composition (`completeTo`/`composeArr`, the inline
  `b.extend(...)` + list-comprehension + slice) is **unchanged** by the patch and
  modeled DEEPLY in Lean. It carries no `opaque`/`axiom` contract (it is concrete
  Lean), so it is an **A-reference**: its deep model is validated by G-AX
  (`axiom_check.py`) to reproduce the real `Permutation.__mul__().array_form`
  bit-for-bit on boundary + fuzz. It is NOT a consumed axiom.
- The class-propagation step (`_af_new` → `self._af_new`) is the **changed** op,
  modeled directly as `result.fam := self.fam` (an **R** op, the class↔`Nat`
  family bijection). No `opaque`/`axiom` callee contract is needed anywhere.
- The proof of `correct_mul` consumes NO callee axiom (the axioms region is
  empty); both result components discharge by reflexivity/`simp`.
- No flag dependency (`__mul__` takes no flags).

## G-CONF fuzz seed
Pinned seed: **12489** (used in `conformance_check.py`).
