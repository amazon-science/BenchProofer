# mapping.md — sympy__sympy-24443

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 809c53c077485ca48a206cee78340389cb83b7f1`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sympy/combinatorics/homomorphisms.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `relator_image(block_elems, block_pows)` | the nested helper `_image(r)` inside `_check_homomorphism` — `sympy/combinatorics/homomorphisms.py:318-346` | the modeled changed function: the image of a single relator word under the generator→image assignment |
| `image_fold(acc, elems, pows)` *(deep model — A-reference)* | the per-block accumulation loop of `_image` (`w = w*images[g]**power` over `r.array_form`) — `homomorphisms.py:341/343` (pre-patch) → the post-patch `for symbol, power in r.array_form: w *= images[g]**power` | pure spec: the left-to-right product of the per-block factors; the deep model of the changed image computation, validated `image_fold == real _image` by axiom_check.py (G-AX) |
| `gid()` *(axiom — A-consumed)* | `codomain.identity` — `homomorphisms.py:316`; e.g. `PermutationGroup.identity` / `FreeGroup.identity` | unchanged callee: the codomain group identity, the initial accumulator |
| `gmul(a, b)` *(axiom — A-consumed)* | group element `__mul__` (`*`) — e.g. `FreeGroupElement.__mul__` `free_groups.py:505`; `Permutation.__mul__` | unchanged callee: the codomain group product `w * x` |
| `gpow(g, e)` *(axiom — A-consumed)* | group element `__pow__` (`**`) — e.g. `FreeGroupElement.__pow__` `free_groups.py:488` (defined for every integer `n`, with `n<0` → `(self.inverse())**(-n)`); `Permutation.__pow__` | unchanged callee: the codomain integer power `images[g]**power`, total over every integer exponent including negative ones |

The pre-patch repo symbols the change removes / rewrites (for the refinement
audit, not referenced from the consumer spec view): the two-index `while i <
len(r)` walk with the `isinstance(domain, PermutationGroup) and r[i] in gens`
generator-lookup branch and the `s in images` / `s**-1 in images` dispatch
(`homomorphisms.py:323-345`). The post-patch code resolves each block directly:

```python
symbols = [g.ext_rep[0] for g in gens]
symbols_to_domain_generators = dict(zip(symbols, domain.generators))
...
for symbol, power in r.array_form:
    g = symbols_to_domain_generators[symbol]
    w *= images[g]**power
```

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `r.array_form` — a tuple of `(symbol, power)` blocks of the relator word (`FreeGroupElement.array_form`, `free_groups.py:372`) | two parallel `List[int]`: `block_pows[k]` = the integer exponent of block `k`; `block_elems[k]` = the resolved codomain element for block `k`'s generator | `len(array_form)` ↔ `len(block_pows) == len(block_elems)`; the order of blocks is preserved (the product is order-sensitive); block `k`'s `power` ↔ `block_pows[k]` |
| the resolved per-block image `images[symbols_to_domain_generators[symbol]]` (the composition: relator symbol → domain generator → its codomain image) | `block_elems[k]` (an opaque `int` handle for the codomain element) | the symbol→generator→image lookup is a TOTAL unchanged map (every relator symbol is a presentation generator, every domain generator has an image — guaranteed by `homomorphism()` extending `images` to all generators, `homomorphisms.py:302-304`); modeling its *result* per block is sound because the lookup chain is not what changed — only how blocks are enumerated changed |
| a codomain group element | opaque `int` handle | identity established by the opaque `gid`/`gmul`/`gpow` axioms; the int is only a tag, the operations are uninterpreted (so non-commutativity is preserved) |
| `w * images[g]**power` (codomain product of the running word image with the block factor) | `gmul(w, gpow(block_elems[k], block_pows[k]))` | `*` ↔ `gmul`, `**` ↔ `gpow`; left-to-right accumulation preserved |

`str`/symbol indexing of free-group words is banned in Nagini and irrelevant to
the tested behaviour; the relator is carried by the two `List[int]` block
arrays, and the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `gid` / `gmul` / `gpow` — the opaque codomain monoid (A-consumed)
**Callees:** the codomain group's `identity` attribute, element `__mul__` and
element `__pow__`. These are the operations `_image` *calls* and does **not**
change. They are modeled as opaque, **non-commutative** monoid operations:

  - `gid()` — the identity element (the initial accumulator `w = identity`).
  - `gmul(a, b)` — the group product `a*b`; uninterpreted, so the spec does NOT
    assume `a*b == b*a` (the real codomains include non-abelian
    `PermutationGroup`s). Associativity and identity are real group laws;
    G-AX exercises them, but the *proof* only needs the opaque contract
    (`Ensures(True)`) — the discriminating power comes from the fold structure
    (every block's factor must appear, in order), not from any algebraic law.
  - `gpow(g, e)` — the integer power `g**e`, **total over every integer
    exponent** `e`: positive, zero, and NEGATIVE. `FreeGroupElement.__pow__`
    (`free_groups.py:488`) handles `n<0` by `(self.inverse())**(-n)`, and
    `Permutation.__pow__` likewise — so a relator block with a negative
    exponent (an inverted generator) has a well-defined factor `gpow(g, e)`,
    `e<0`. This totality is exactly what the buggy pre-patch failed to honour:
    it dropped the factor of an inverted generator.

The contracts are the **weakest sufficient** ones (`Ensures(True)`): the proof
needs only that these are deterministic group operations applied in the fold;
it never relies on any particular value, so the axioms cannot over-claim. Their
soundness is therefore trivial, and G-AX additionally validates the laws it
uses (identity, associativity, negative powers).

### 3.2 `image_fold` deep model ↔ the real `_image` per-relator product (A-reference)
**Callee modeled deeply:** the changed image computation `_image(r)`
(`homomorphisms.py:318-346`). The fold

```
image_fold(acc, elems, pows) = acc                                     if empty
                             = image_fold(gmul(acc, gpow(elems[0], pows[0])),
                                          elems[1:], pows[1:])          otherwise
```

is the **per-block left-to-right product** — the spelled-out model of the fixed
`_image`. It is NOT a consumed value-axiom; it is validated **equal to the real
`_image`** out-of-band by `axiom_check.py` (G-AX). The real `_image`, post-fix,
is exactly: for each `(symbol, power)` in `r.array_form`, multiply `w` by
`images[symbols_to_domain_generators[symbol]] ** power`, left to right — i.e.
`image_fold(identity, [images[g_k]], [power_k])` under `gmul = *`, `gpow = **`.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL sympy group
machinery — `DihedralGroup`, `CyclicGroup`, `AlternatingGroup`,
`SymmetricGroup` (the `PermutationGroup`s the issue is about), and `FpGroup` /
`FreeGroup` domains — resolves every relator's blocks exactly as the fixed
`_image` does, and asserts the deep `image_fold` reproduces the real per-relator
image on all 23 relators across 9 group cases, **including relators that contain
inverted generators (negative exponents)** — the case the bug dropped. It also
checks the monoid laws (identity, associativity, `g*g**-1 == identity`,
`g**-2 == (g**-1)**2`). It imports only the standard library and `sympy` (the
module the gold patch touches). Exit 0 iff every obligation holds.
