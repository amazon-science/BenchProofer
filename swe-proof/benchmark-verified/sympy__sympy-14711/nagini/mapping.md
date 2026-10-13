# mapping.md — sympy__sympy-14711

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c6753448b5c34f95e250105d76709fe4d349ca1f`, states the type
abstraction, and gives the provenance of the axiomatized callee.

Repo file under change: `sympy/physics/vector/vector.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `vec_add(self, other)` | `Vector.__add__(self, other)` — `sympy/physics/vector/vector.py:58` (body lines 59-61) | the modeled changed function (vector add operator) |
| `Vec` / `Vec.terms` | `Vector` / `Vector.args` — `sympy/physics/vector/vector.py:10`, `args` set in `__init__` (line 38) | a vector and its component list (`List[int]` of opaque component-family tags) |
| `Operand` | the Python object passed as `other` to `__add__` (an `int` `0`, a `Vector`, or anything else) | the right-hand addend, with kind discriminators |
| `Operand.is_scalar_zero` | the predicate `other == 0` (the new guard added at line 60-61 of the patch) | the additive-identity discriminator |
| `Operand.is_vector` | `isinstance(other, Vector)` inside `_check_vector` (line 724) | the genuine-vector discriminator |
| `Operand.terms` | `other.args` (the addend's component list, read at line 61) | the addend's component list |
| `vector_guard(other)` *(axiom — A-consumed)* | `_check_vector(other)` — `sympy/physics/vector/vector.py:723-726` | unchanged callee: returns `other` if it is a `Vector`, else raises `TypeError` |
| `normal_form(s)` / `normalise(terms)` *(axiom — A-reference)* | `Vector.__init__(inlist)` — `sympy/physics/vector/vector.py:26-53` | unchanged merging constructor: frame-keyed summation of the argument list (folds same-frame terms, drops cancelling frames); modeled by `normal_form`, a `@Pure` deterministic function of the whole argument list with the content-bearing faithful contract `len(result) <= len(input)` AND determinism (equal inputs → equal normal forms). `normalise` is the impl helper that produces the stored list with `ToSeq(result) == normal_form(ToSeq(terms))`. |
| `NotAVector` (exception) | `TypeError('A Vector must be supplied')` raised by `_check_vector` (line 725) | the reject signal (user-defined; a builtin exception in `Exsures` crashes Nagini) |

The single operation the patch ADDS — the `if other == 0: return self`
short-circuit — is the `Operand.is_scalar_zero` branch of `vec_add`
(`if other.is_scalar_zero: return self`). It is modeled deeply (spelled out in
the impl), not axiomatized; `_check_vector` (the only unchanged callee) is the
`vector_guard` axiom.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Vector` (with attribute `.args`) | `Vec` (with attribute `.terms`) | `vector.args` ↔ `vec.terms`; the component list is the only touched facet |
| `Vector.args` — a Python `list` of `(measure, basis)` pairs | `List[int]` — each entry an opaque int tag for the component *family* (reference frame) | a component family ↔ a distinct int; the addition behaviour observes only the list **length**, never the pair payloads. (The exact element identities are not load-bearing because the result is re-normalised by a frame-keyed constructor — see the next row.) |
| `Vector(self.args + other.args)` — construct a new `Vector` from the **concatenated** argument list, which `Vector.__init__` then **frame-merges** (`__init__`, lines 26-53) | a two-step model: (A4a) build `combined == self.terms + other.terms` (the raw concatenation = the constructor's *argument*), then (A4b) `Vec(combined)`, whose stored list is `normal_form(ToSeq(combined))` | The `list` `+` argument is the append loop (A4a, R). The construction itself is **A-reference** (A4b): `Vector.__init__` builds a dict keyed by reference frame (`d[inp[1]] += inp[0]`), summing the measure-number matrices of same-frame terms and dropping zero-contribution frames — so it is **frame-keyed summation**, NOT verbatim concatenation. This merge **IS exercised by the F2P test** `test_Vector`: `v1 = x*A.x + y*A.y + z*A.z` and `v2 = x**2*A.x + …` are both entirely in frame A, `v3 = v1 + v2` goes through `__add__`, and `dot(v3, A.x) == x**2 + x` holds only because the same-frame terms merge (`v1.args` itself has length 1, not 3; `x*A.x + (-x)*A.x` collapses to length 0). The faithful, patch-invariant property modeled is therefore a **content-bearing** one: the result is `normal_form(self.terms ++ other.terms)`, where `normal_form` is a deterministic function with `len(result) <= len(input)`. This pins that the result combines **both** operands' components (so dropping `other` — `return self` etc. — fails the post), while not over-claiming verbatim concatenation. Validated against the real constructor by G-AX (§3.2) for both the length bound and the determinism. A mere length bound (the prior refinement) was too weak — it admitted other-dropping impls. |
| `other == 0` (the scalar additive identity; an `int`/`Integer` `0`) | `other.is_scalar_zero` (bool) | `True` iff the operand is the additive-identity zero — the seed `sum(...)` starts from. The F2P observes exactly `A.x + 0`. |
| `isinstance(other, Vector)` | `other.is_vector` (bool) | `True` iff the operand is a genuine `Vector` |
| `TypeError` raised by `_check_vector` | `NotAVector` (user-defined exception) | a builtin exception in an `Exsures` crashes the Nagini translator; the user-defined class stands in (SPEC_GUIDE §2). |

`str`/numeric payloads of the component terms are irrelevant to the addition
behaviour under specification, so the carrier is `List[int]` of opaque
component-family tags and the specification observes only the list length.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `vector_guard` ↔ `_check_vector` (A-consumed)
**Callee:** `sympy/physics/vector/vector.py:723-726` (unchanged by the patch):

```python
def _check_vector(other):
    if not isinstance(other, Vector):
        raise TypeError('A Vector must be supplied')
    return other
```

The axiom encodes only the obligations `__add__` relies on:
- when `other` IS a vector (`other.is_vector`), it returns `other` unchanged —
  the returned object's component list equals the operand's
  (`ToSeq(Result().terms) == ToSeq(other.terms)`) and `other.is_vector` holds;
- when `other` is NOT a vector (`not other.is_vector`), it raises (modeled as
  `NotAVector`).

This is the **weakest** contract the proof needs: it is exactly an identity
guard with a not-a-vector raise. It is `@ContractOnly` (no `@Pure`: it is not
used inside any `Ensures`, only called in the impl and its `Exsures` consumed).

**Flag/configuration dependency:** none. `_check_vector` takes a single
positional argument and consults only `isinstance(other, Vector)`; there is no
optional flag whose value the axiom depends on.

**Soundness check (G-AX):** `axiom_check.py` constructs `_check_vector`-style
inputs — genuine `Vector`s (the basis vectors `N.x`, sums, the zero vector
`Vector(0)`), the scalar zero `0` and `S(0)`, and a spread of non-vector
objects (ints, floats, strings, lists, `None`, symbols, the `sympify`'d zero) —
and asserts: every `Vector` input is returned unchanged (`is`-identity) and
every non-`Vector` input raises `TypeError`. In particular the scalar zero `0`
raises (it is NOT a vector), which is precisely why the pre-patch `__add__`
failed on `A.x + 0` and why the short-circuit is required. Exit 0 iff sound.
It imports only `sympy` (the repo under test); nothing else.

### 3.2 `normal_form` / `normalise` ↔ `Vector.__init__` (A-reference)
**Callee:** `sympy/physics/vector/vector.py:26-53` (unchanged by the patch) —
the `Vector` constructor that `__add__` calls on the concatenated argument list
`self.args + other.args`. Its body builds a dict keyed by reference frame and
sums measure-number matrices for same-frame terms:

```python
def __init__(self, inlist):
    self.args = []
    while ... :
        ...
        d = {}
        for inp in ar:                 # ar = the (matrix, frame) terms
            ...
            if inp[1] in d:
                d[inp[1]] += inp[0]    # same frame -> matrices summed
            else:
                d[inp[1]] = inp[0]
        for k, v in d.items():
            if v != zeroes:            # drop a frame whose sum vanished
                self.args.append((v, k))
```

So construction is **frame-keyed summation**, not verbatim concatenation: it
folds same-frame components and drops cancelling frames. It is, crucially, a
**deterministic function of its whole argument list** (same arg list → same
`.args`). The model captures exactly this: `normal_form(s)` is a `@Pure
@ContractOnly` function (so equal inputs give equal normal forms and differing
inputs are NOT provably equal) with the faithful length bound `len(result) <=
len(input)`. `normalise(terms)` is the non-`@Pure` impl helper that produces the
stored `List[int]` with `ToSeq(result) == normal_form(ToSeq(terms))`; it is
called when constructing the result `Vec`.

The post of `vec_add` pins `ToSeq(Result().terms) == normal_form(ToSeq(self.terms)
+ ToSeq(other.terms))` — the normal form of the **concatenation of both modeled
input carriers**. This is **grounded in the inputs**, not an answer-key oracle:
the argument `ToSeq(self.terms) + ToSeq(other.terms)` is an expressible
structural relation on the two actual inputs, and the impl must genuinely build
`Vec(self.terms ++ other.terms)` to satisfy it. An impl that drops `other`
(`return self`, `Vec(self.terms)`, `Vec([])`) produces `normal_form` of a
*different* sequence, which the opaque-function `normal_form` does not let the
verifier equate with `normal_form(self ++ other)`.

This is tagged **A-reference** (not A-consumed in the sense of a clever Ensures
the proof leans on, and definitely not R): the constructor changes the element
count, so it is a changed *operation* on the carrier, modeled shallowly and
validated == the real callee by G-AX — not declared an identity refinement.

**Flag/configuration dependency:** none. `Vector.__init__` takes a single
positional argument (the term list) and the frame-merge depends only on the
reference-frame key of each term.

**Soundness check (G-AX):** `axiom_check.py` constructs many real `Vector`s by
concatenating arbitrary same-frame and mixed-frame `(measure, frame)` term lists
(via real `__add__`/scalar multiply), and asserts the contract in THREE
directions: (a) faithfulness — `len(Vector(args1 + args2).args) <=
len(args1) + len(args2)` for every constructed sum (incl. the merge cases
`v1+v2` -> length 1 and the cancellation case -> length 0); (b) tightness — the
naive "length is preserved" over-claim is FALSIFIED by an exhibited same-frame
merge (`x*A.x + y*A.y` collapses 2 args to 1); and (c) the determinism /
distinguisher the content-bearing post relies on — the constructor returns the
SAME `.args` on the SAME argument list (it is a function), and `Vector(v1.args +
v2.args).args != Vector(v1.args).args` for the F2P merge (so `normal_form(self ++
other)` genuinely differs from `normal_form(self)` alone, which is exactly why
the dropped-other attacks fail the post). Exit 0 iff sound; verified RC=0 in the
pinned container. It imports only `sympy`.
