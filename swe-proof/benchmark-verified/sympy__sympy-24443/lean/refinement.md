# refinement.md — operation correspondence (sympy__sympy-24443)

Maps every op in `implementation_checkRelators` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

## What the patch does
`patch.diff` rewrites the internal word-evaluation `_image(r)` inside
`_check_homomorphism` (`sympy/combinatorics/homomorphisms.py`) and the small
amount of setup it relies on. Pre-patch, `_image(r)` walked the relator with two
indices `i`/`j` and, for a `PermutationGroup` domain, recovered the generator for
each letter via

    if isinstance(domain, PermutationGroup) and r[i] in gens:   # pre-patch
        s = domain.generators[gens.index(r[i])]

The membership test `r[i] in gens` succeeds only for a **non-inverted** generator
letter; when `r[i]` is an *inverted* generator the test fails, `s` is set to the
raw letter, and the subsequent `images` lookup mishandles it — so a relator that
uses an inverted generator is evaluated incorrectly and a valid assignment is
rejected. The patch precomputes a `symbol → domain-generator` table

    symbols = [g.ext_rep[0] for g in gens]
    symbols_to_domain_generators = dict(zip(symbols, domain.generators))

and evaluates the word directly over its `(symbol, power)` pairs:

    w = identity
    for symbol, power in r.array_form:                          # post-patch
        g = symbols_to_domain_generators[symbol]
        w *= images[g]**power
    return w

Indexing by the *symbol* (not by testing the *letter* for membership) treats
inverted and non-inverted generators uniformly, and `**power` with a negative
`power` supplies the inverse — so inverted generators contribute correctly.

## Type bijection
`G` with `[Group G]` ↔ the codomain group (`*`, `** : Int`, `.identity`).
`Sym` ↔ a relator-word symbol (`g.ext_rep[0]`); `Gen` ↔ a domain generator.
`genOf : Sym → Gen` ↔ `symbols_to_domain_generators`; `imageOf : Gen → G` ↔
`images`. `List (Sym × Int)` ↔ one relator's `.array_form`; `rels : List (List
(Sym × Int))` ↔ `pres.relators`. Full table in mapping.md.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `for r in rels do` | `for r in rels:` (the relator loop in `_check_homomorphism`) | I | per-relator iteration in order |
| 2 | `let mut acc : G := 1` (inner) | `w = identity` (start of post-patch `_image`) | R | `1 : G` ↔ `codomain.identity`; group unit. |
| 3 | `for sp in r do` | `for symbol, power in r.array_form:` | R | a relator word ↔ `List (Sym × Int)`; `r.array_form` ↔ the list of `(symbol, power)` pairs. |
| 4 | `let g := genOf sp.1` | `g = symbols_to_domain_generators[symbol]` | R | the precomputed symbol→generator table ↔ `genOf` (total lookup input). This replaces the buggy `r[i] in gens` membership recovery — the heart of the fix. |
| 5 | `acc := acc * imageOf g ^ sp.2` | `w *= images[g]**power` | R | `imageOf g ^ (power : Int)` ↔ `images[g]**power`; integer power gives the inverse for negative `power` (inverted generator handled correctly). `*` ↔ codomain `*`. |
| 6 | `if w ≠ 1 then return false` | `s = _image(r).is_identity; if not s: return False` (PermutationGroup leg) | R | the relator is satisfied iff its word value is the identity; `w ≠ 1` ↔ `not _image(r).is_identity`. Early reject. |
| 7 | `return true` | `return True` (loop fell through) | I | all relators satisfied. |

No A-consumed and no A-reference rows: the word value is built directly from the
input lookups using the codomain group's own operations (modeled by Mathlib
`Group`), and the relator-satisfaction test is plain group equality. There is no
unchanged sympy callee whose contract the proof assumes (axiom_check.py is a skip
stub), and nothing in the impl region is left as a real callee (so `conf_skip` is
false — G-CONF differential-tests the whole R/I skeleton). No
changed-inexpressible op.

## Discriminating clause (G-DIFF)
The patched op is the word-evaluation, ops #4–#5. The prepatch impl drops any
word entry with a negative exponent (`if sp.2 ≥ 0 then …`) — the faithful image
of the pre-patch behavior, where an inverted generator letter fails the `in gens`
recovery and its factor is mishandled/omitted. On a relator word that contains an
inverted generator whose omission leaves the partial product non-identity (e.g. a
word `g · g⁻¹`-style entry, or D₃'s relators expressed via inverted generators —
exactly what `homomorphism(D3, D3, D3.generators, D3.generators)` produces), the
spec demands `result = true` (every relator evaluates to `1` under the genuine
integer powers), but the prepatch impl returns `false`. `true ≠ false`, so the
carried gold proof cannot close `correct_checkRelators` against the buggy impl.
That is the G-DIFF signal, and it mirrors the F2P test `test_homomorphism`
(`homomorphism(D3, D3, D3.generators, D3.generators)` must succeed and be an
isomorphism).
