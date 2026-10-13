# mapping.md — symbol binding & type bijection (sympy__sympy-24443)

## Instance summary
A routine decides whether a chosen assignment of a group's generators to
elements of another group extends to a homomorphism. It does so by checking that
every defining relator of a presentation of the domain, when its generators are
replaced by their assigned images, multiplies out to the identity of the
codomain. Evaluating a relator means walking the relator word — a sequence of
`(generator-symbol, exponent)` pairs — and multiplying the running product by the
assigned image of that generator raised to the exponent. The old word-evaluation
walked the word with two indices and, for a permutation-group domain, recovered
the generator from the relator letter via a membership test that only succeeded
for **non-inverted** letters; an inverted generator (a negative exponent) failed
that test and its factor was handled wrongly, so a perfectly valid assignment was
rejected. The fix evaluates the word directly over its `(symbol, exponent)`
pairs, looking each symbol's generator up in a precomputed table, so inverted
generators are handled exactly like the non-inverted ones.

## Modeled function (the changed behavior under spec)
The relator-checking loop together with its inner word-evaluation. Given the
defining relator words and the two lookups it needs (relator-symbol → domain
generator, and domain generator → assigned codomain element), it returns `true`
iff every relator word evaluates to the codomain identity.

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_checkRelators` / `problem_spec_checkRelators` / `correct_checkRelators` | `_check_homomorphism` (its `for r in rels` loop) together with the inner `_image(r)` it calls | `sympy/combinatorics/homomorphisms.py:310-368` (`_image` word-evaluation at `318-346`, the patched logic; the relator loop at `348-368`) |
| `evalWord genOf imageOf r` (front-recursive product over the word) | the post-patch `_image(r)`: `w = identity; for symbol, power in r.array_form: w *= images[symbols_to_domain_generators[symbol]]**power` | `sympy/combinatorics/homomorphisms.py:318-346 (post-patch)` |

## Type bijection (used by G-CONF)
| Python reality | Lean model |
|---|---|
| the codomain (a `PermutationGroup`) with `*`, `**`, `.identity` | a type `G` with `[Group G] [DecidableEq G]` (Mathlib group; `1`, `*`, `^ (· : Int)`) |
| a relator-word symbol `g.ext_rep[0]` of a presentation generator | an element of an opaque symbol type `Sym` |
| a domain generator (a `Permutation`) | an element of an opaque type `Gen` |
| `symbols_to_domain_generators = dict(zip(symbols, domain.generators))` | `genOf : Sym → Gen` (total lookup) |
| `images` dict: domain generator → codomain element | `imageOf : Gen → G` (total lookup) |
| a relator's `.array_form`: `[(symbol, power), …]` | `List (Sym × Int)` (one relator word) |
| `pres.relators` (all relator words of the presentation) | `rels : List (List (Sym × Int))` |
| `_image(r)` = `∏ images[genOf[symbol]]**power` over `r.array_form` | `evalWord genOf imageOf r` |
| `codomain.identity` | `(1 : G)` |
| `_image(r).is_identity` test, and the loop's final `True`/`False` | `evalWord … r = 1`, and the `Bool` result |

`Int` exponents carry the sign that the bug mishandled: a negative `power` is an
inverted generator. In Mathlib, `g ^ (p : Int)` is the genuine integer group
power (`g ^ (-1) = g⁻¹`), so the model treats inverted and non-inverted letters
uniformly — exactly the post-patch behavior.

## Callee provenance / flag deps
- Group multiplication, integer power, and identity are **language primitives**
  of the codomain group (Mathlib `Group`), modeled directly — neither
  axiomatized nor an A-reference.
- The two lookups (`genOf`, `imageOf`) and the relator words `rels` are the
  UNCHANGED scaffold that `_check_homomorphism` computes once before the modeled
  loop (presentation, `ext_rep`, `array_form`, the `zip`). They are taken as
  already-computed **inputs** to the modeled loop (their construction is
  unchanged by the patch). In the G-CONF shadow they are rebuilt from the SAME
  real objects, so the shadow exercises the real scaffold and differs from the
  real routine only in transliterating the patched word-evaluation + relator
  loop (R/I rows in refinement.md). No consumed axiom, no A-reference deep model.
- **Flag dependency:** the patched branch is identical for all domain types; the
  bug was specifically observable when the domain is a `PermutationGroup` (its
  relator letters are full permutations, so the old membership test misfired on
  inverted letters). G-CONF therefore fuzzes `PermutationGroup` domains and
  codomains (the issue's setting); FpGroup codomains, whose relator check goes
  through `codomain.equals`/rewriting, are out of the modeled scope and excluded.

## G-CONF fuzz seed
`conf_seed = 24443` (pinned).
