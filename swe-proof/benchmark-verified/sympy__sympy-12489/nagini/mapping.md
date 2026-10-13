# mapping.md — sympy__sympy-12489

Binds every `model.py` symbol to its repository counterpart at
`base_commit = aa9780761ad8c3c0f68beeef3a0ce5caac9e100b`, states the type
abstraction, and gives the provenance of the deep-model reference (there is no
consumed axiom).

Repo file under change: `sympy/combinatorics/permutations.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `Arrangement` (class with `kind: int`, `array: List[int]`) | `Permutation(Basic)` — `sympy/combinatorics/permutations.py:464` | minimal stand-in carrying only the two touched attributes (its runtime class identity + its array form) |
| `Arrangement.kind` | the runtime class of the constructed object (`type(obj)`) | the family identifier; base family `Permutation` ↔ `kind == 0`, any subclass ↔ a distinct nonzero `kind` |
| `Arrangement.array` | `Permutation._array_form` (set in `_af_new` / `__new__`) | the array form content (unchanged by the fix) |
| `make(kind, array)` | `Permutation._af_new(perm)` — `permutations.py:927-950` (the internal builder) | modeled changed function (site 1): the builder all internal creation funnels through |
| `combine(self, other, product)` | `Permutation.__mul__(self, other)` — `permutations.py:1244-1303` | modeled changed function (site 2): a representative binary combination that creates its result through the left operand's class |

The pre-patch repo symbols the change removes/rewrites (for the refinement
audit; not referenced from the consumer spec view): the module-level aliases
`Perm = Permutation` and `_af_new = Perm._af_new` (`permutations.py:2830-2831`),
which hard-bound every internal creation to the base class.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the runtime class of a `Permutation`/subclass object (`type(obj)`) | `Arrangement.kind : int` | `type(obj) is Permutation` ↔ `kind == 0`; `type(obj) is SomeSubclass` ↔ a fixed distinct nonzero `kind`. The fix's only observable on the F2P test is *which class* the result is — `kind` is precisely that observable. |
| `Permutation._array_form` (`list` of ints) | `Arrangement.array : List[int]` | identity on the list of points; `make`/`combine` carry it through unchanged. |
| the classmethod first argument `cls` of `_af_new` / `__new__` | `make`'s `kind` parameter | the family the builder is reached through; `cls is Permutation` ↔ `kind == 0`, `cls is Sub` ↔ the subclass's `kind`. |
| `self` (the left operand of `__mul__`, a classmethod-bound instance) | `combine`'s `self.kind` | `type(self)` ↔ `self.kind`; `self._af_new(...)` (post-patch) reaches the builder through `type(self)`. |
| the numeric product array `[b[i] for i in a] + b[len(a):]` (`__mul__`) | `combine`'s `product` parameter | the unchanged numeric content; passed through directly because the product computation is identical pre/post-patch (the patch touches only which class wraps it). |

`Permutation` is a rich `Basic` subclass; only the two attributes the fix can
change observably (the runtime class and the array form) are modelled. All
numeric machinery (`_af_rmul`, `Cycle`, range padding, dedup checks) is
unchanged by the patch and is abstracted into the `product` / `array` carriers.

## 3. Deep-model reference (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `make` / `combine` deep model ↔ real `Permutation._af_new` / `__mul__`

**Callee under reference:** the patched repository construction routines.
The family-propagating construction is modelled **deeply** (the `make` /
`combine` impls spell out "the result's family identifier equals the family the
builder was reached through"); there is **no `@ContractOnly` axiom** the proof
consumes.

Post-patch source (the relevant lines):

```python
@classmethod
def _af_new(cls, perm):                 # was @staticmethod, fixed Perm
    p = Basic.__new__(cls, perm)        # was Basic.__new__(Perm, perm)
    p._array_form = perm
    p._size = len(perm)
    return p

def __mul__(self, other):
    ...
    return self._af_new(perm)           # was _af_new(perm) == Perm._af_new(perm)
```

`Basic.__new__(cls, perm)` constructs an instance of exactly `cls`; the
classmethod binds `cls` to whatever class `_af_new` was invoked on, so a value
built through a subclass is an instance of that subclass (`make(kind,·).kind ==
kind`). `__mul__` reaches the builder via `self._af_new`, binding `cls` to
`type(self)`, so the product is of the left operand's class
(`combine(self,·).kind == self.kind`). Pre-patch, `_af_new` was a
`@staticmethod` calling `Basic.__new__(Perm, perm)` and `__mul__` called the
module-level `_af_new` (`Perm._af_new`), so every result collapsed onto the base
class.

**Soundness check (G-AX):** `axiom_check.py` constructs a genuine subclass
`CustomPermutation(Permutation)` (mirroring the hidden F2P test's subclass,
including its `__call__`/`__eq__`/`__hash__` overrides, none of which touch the
construction routines) and runs the REAL `Permutation._af_new` and `__mul__`:

  - clause (1): `type(Cls._af_new(perm)) is Cls` and the array form is preserved,
    for `Cls ∈ {Permutation, CustomPermutation}`, exhaustively over all
    permutations of sizes 0..5 plus 3000 randomized sizes up to 12;
  - clause (2): `type(left * right) is type(left)` for every family pairing of
    `left`/`right`, exhaustively over equal-size pairs of sizes 1..4 plus 3000
    randomized pairs, with the product array equal to the real `__mul__` output;
  - the F2P headline witnesses verbatim: `type(p*q) is CustomPermutation`,
    `type(q*p) is Permutation`, `p == q`.

It imports only `sympy` (the repository under test; the gold patch is applied in
the container). Exit 0 iff every observation meets the model's claims. Validated
here: PASSES on the patched source (6771 observations + F2P), FAILS on the
pre-patch source (`builder lost family … got Permutation, model.make claims
kind=1`) — confirming the reference is discriminating, not vacuous.
