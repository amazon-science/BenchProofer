# refinement.md — operation correspondence (astropy__astropy-14369)

Maps every op in `implementation_divChain` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patch changes one grammar production. Pre-patch:
```
division_of_units : DIVISION unit_expression
                  | unit_expression DIVISION combined_units      # right-recursive
    if len(p) == 3: p[0] = p[2] ** -1
    else:           p[0] = p[1] / p[3]
```
Post-patch:
```
division_of_units : DIVISION unit_expression
                  | combined_units DIVISION unit_expression      # left-recursive
    if len(p) == 3: p[0] = p[2] ** -1
    else:           p[0] = p[1] / p[3]
```
The handler body is byte-identical; only the recursion side flips. The effect on
a flat division chain `A/B/C/…`: post-patch it associates left, so the value is
`(((A / B) / C) / …) = A / (B · C · …)`; pre-patch it associates right,
`A / (B / (C / …))`, which alternates the trailing terms' signs.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `head : G`, `rest : List G` inputs | the leading `combined_units` and the ordered trailing `unit_expression` terms of a division chain | R | a parsed unit value ↔ an element of the unit `CommGroup` (free abelian group on base units / exponent vector); the flat chain ↔ `(head, rest)` (mapping.md). |
| 2 | `let mut acc := head` | the chain's leading term is the initial accumulator | I | identity initialisation; matches left-associative reduction starting from the first term. |
| 3 | `for u in rest do acc := acc / u` | left-recursive `combined_units DIVISION unit_expression` with `p[0] = p[1] / p[3]`, applied left-to-right over the chain | A-reference | THE FIX. Each trailing term divides the running result (group `/`, i.e. `a * b⁻¹`). Left-association is the post-patch grammar's reduction order. `core` unit `/`/`*`/`**-1` validated == `CommGroup` ops by G-AX. NOT axiomatized. |
| 4 | `return acc` | the reduced `division_of_units` value `p[0]` | I | the accumulated chain value is the result. |

Closed form (spec): the loop accumulates `head / rest₀ / rest₁ / … = head /
(rest₀ · rest₁ · …) = head / rest.prod`. The proof agent proves the `forIn`
loop equals this product form by the Route B accumulator induction
(`List.forIn_cons`, generalising `acc`), using `CommGroup` laws
(`div_div`, `mul_comm`, `List.prod_cons`).

No A-consumed rows: the proof discharges the loop↔`prod` reduction with Mathlib
`CommGroup` lemmas; no UNCHANGED callee property is *assumed* — the group laws
are G-AX-validated facts about the real callee, hence A-reference. No
changed-inexpressible op (the associativity change is modeled exactly).

## Discriminating clause (G-DIFF)
Row 3 is the fix. For a chain of length ≥ 2 the two associations differ.
Concretely on `head=1, rest=[b,c]` (a `B/C` tail): post-patch the spec pins
`1 / (b·c) = b⁻¹·c⁻¹`; the pre-patch impl computes `b / c⁻¹`-style right nesting
= `head / (c / b) = b·c⁻¹` (mechanically checked: `pre (m 0) [m 1, m 2, m 4] ≠
head / prod`, while `post … = head / prod`). The pre-patch `correct_divChain`
therefore cannot close against the frozen `problem_spec_divChain`, which is the
G-DIFF signal. This is exactly the issue's jumbled output: `10+3J/m/s/kpc2` came
out as `J·s/(kpc2·m)` (the `s` exponent sign flipped) instead of the correct
`J/(m·s·kpc2)`.
