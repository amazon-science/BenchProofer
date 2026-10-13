# mapping.md — sympy__sympy-24443

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 809c53c077485ca48a206cee78340389cb83b7f1`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `sympy/combinatorics/homomorphisms.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `evalWord (assign) (syllables)` | the internal `_image(r)` of `_check_homomorphism` — `sympy/combinatorics/homomorphisms.py:318` (nested def; the modeled changed operation) | the modeled changed function: value of a word/relator under a generator→image assignment |
| `wordProd (assign) (syllables)` | the value `_image(r)` computes (post-patch body, `homomorphisms.py:336-340`) | pure spec / **deep model** of `_image`: the ordered group product over the word's syllables |
| `assign : Nat → G` | `symbols_to_domain_generators` composed with `images` — i.e. `symbol ↦ images[symbols_to_domain_generators[symbol]]` (`homomorphisms.py:320-321,338-339`) | maps a generator *symbol* to its codomain image element |
| `syllables : List (Nat × Int)` | `r.array_form` — tuple of `(symbol, power)` pairs (`free_groups.py:372`, `homomorphisms.py:337`) | the relator's syllable decomposition |

There are **no axioms** and **no A-reference deep-model callees** in this bundle.
`_image` is the operation the patch *changes*; per SPEC §0.7 it is modeled
**deeply** (`wordProd`), never axiomatized, and its fidelity is checked by
G-CONF against the patched function (not by G-AX). See refinement.md §C.

The pre-patch repo logic the change removes (refinement audit only, not in the
consumer spec view): the dual-index `while i < len(r)` loop with the
`isinstance(domain, PermutationGroup) and r[i] in gens` test
(`homomorphisms.py:334-345`), which silently skipped inverted-generator
(negative-`power`) syllables for permutation-group domains.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| codomain group element (`Permutation`, or any `FreeGroupElement`/`FpGroupElement`) | `G` with `[Group G]` | element ↔ element; `codomain.identity` ↔ `(1 : G)`; group product `a*b` ↔ `a * b`; `a**p` for `p : int` ↔ `a ^ (p : Int)` (`zpow`, negative powers invert); `x.is_identity` ↔ `x = 1` |
| a generator symbol `sym = g.ext_rep[0]` | `Nat` (the symbol's identity, abstract) | distinct symbols ↔ distinct `Nat`s; only equality/lookup is used, so any injective coding is faithful |
| `r.array_form` = `((sym₀,p₀), …, (sym_{m-1},p_{m-1}))` | `List (Nat × Int)` | `len(array_form)` ↔ `.length`; the k-th pair ↔ `syllables[k]`; tuple `(sym,p)` ↔ `(sym, p) : Nat × Int` |
| `images[symbols_to_domain_generators[sym]]` | `assign sym : G` | the composite *symbol → domain generator → codomain image*; G-CONF builds the real composite, the model packages it as one function `assign` |
| `_image(r)` (the computed codomain element) | `evalWord assign syllables` (`= wordProd assign syllables`) | the ordered product `∏ₖ images[gen(symₖ)]^{pₖ}` ↔ `wordProd`’s left-to-right fold |

`G` is an **arbitrary** group (`[Group G]`, possibly non-abelian): the relator
syllables are multiplied **in order**, and exponents are **signed** integers
(`zpow`) so a negative power inverts. Both properties are load-bearing — the bug
was the silent omission of negative-power syllables. The carrier is a list of
`(symbol, power)` pairs because the operation is per-syllable.

## 3. Callee provenance — none consumed

No `axiom` is declared and no callee is consumed as an A-reference; the changed
operation is modeled deeply (refinement.md §C, SPEC §0.7). The repo machinery
the conformance bridge exercises — `domain.presentation()`, `pres.relators`,
`pres.generators`, `g.ext_rep`, `r.array_form`, and codomain group arithmetic
(`*`, `**`, `.identity`, `.is_identity`) — is run **for real** inside G-CONF on
BOTH the shadow and the oracle, so it needs no separate axiom soundness check
(there is no assumed contract to falsify). Consequently `axiom_check.py` is
absent and **G-AX is `skip`** for this bundle.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`24443`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `wordProd`/`evalWord` (R/I-tagged ops) to Python over real
`PermutationGroup`/`Permutation` values and compares the full
`_check_homomorphism` verdict (the patched oracle) over the identity- and
all-identity boundary assignments on each test group plus 10⁵ randomized
generator→element assignments. Scope is restricted to permutation-group
domain == codomain (the issue/F2P scenario whose verdict is exactly
`all(_image(r).is_identity)`); FpGroup codomains route through
`codomain.equals`/`make_confluent`, an observable the modeled op does not cover.
