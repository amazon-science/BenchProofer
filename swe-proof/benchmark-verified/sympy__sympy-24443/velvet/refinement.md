# refinement.md — sympy__sympy-24443

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `evalWord` `do` block plus the deep `wordProd` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed**/**A-reference**), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so the backward
`while` fold carries a `decreasing i` measure and a verifying impl must
TERMINATE and return `wordProd assign syllables`. (An earlier revision used
partial correctness, which a same-spec diverging impl — `while true` with a
trivial invariant — vacuously satisfied; the G-EQ/G-PANEL-1 audit found that
counterexample: a verifying impl whose translated patch loops forever inside
`_image` and so fails the hidden tests. Total semantics excludes the whole
class. The real post-patch `_image` trivially terminates: it is a bounded
`for` over `r.array_form`.)

## A. The image site — `_image(r)` inside `_check_homomorphism` (`homomorphisms.py:318`)

Gold hunk (the new `_image` and the symbol bookkeeping it relies on):
```
+    pres = domain if hasattr(domain, 'relators') else domain.presentation()
+    rels = pres.relators
+    gens = pres.generators
+    symbols = [g.ext_rep[0] for g in gens]
+    symbols_to_domain_generators = dict(zip(symbols, domain.generators))
     identity = codomain.identity
     def _image(r):
-        ... dual-index while loop; `if isinstance(domain, PermutationGroup) and r[i] in gens` ...
-        ... `i += abs(power)` (advances past negative-power syllables without
-            adding their factor when the `in gens` test fails) ...
+        w = identity
+        for symbol, power in r.array_form:
+            g = symbols_to_domain_generators[symbol]
+            w *= images[g]**power
+        return w
```

| # | Solution.lean impl op (`evalWord`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `syllables : List (Nat × Int)` | `r.array_form` (tuple of `(symbol, power)`) | R | `array_form` ↔ `List (Nat × Int)` (mapping.md §2). G-CONF bridges via the real `r.array_form`. |
| A2 | parameter `assign : Nat → G` | `symbol ↦ images[symbols_to_domain_generators[symbol]]` (`homomorphisms.py:320-321,338-339`) | R | the symbol→domain-generator→image composite; mapping.md §2. G-CONF builds the real composite. |
| A3 | `result := 1` (init) | `w = identity` | R + I | `(1 : G)` ↔ `codomain.identity` (mapping.md §2); concrete init. |
| A4 | loop body `result := assign s.1 ^ s.2 * result`, folding ALL syllables; total value `wordProd assign syllables` | `w *= images[g]**power` over `for symbol, power in r.array_form` | I + R | the changed op is modeled **deeply** by `wordProd`/`evalWord`: the backward `while` fold computes the same ordered product `∏ₖ assign(symₖ)^{pₖ}` the post-patch `for` loop computes. Group `*`/`^`/`1` are R (codomain ops, mapping.md §2); the fold structure is I. **Every** syllable contributes, including negative `power` (`zpow` inverts) — the behavioural core of the fix. |
| A5 | returned `result : G` (`= wordProd assign syllables`) | `return w` | R + I | `G` ↔ codomain element. The enclosing `_check_homomorphism` then tests `w.is_identity` per relator; `wordProd assign syllables = 1` ↔ `_image(r).is_identity` (mapping.md §2), which G-CONF exercises as the full verdict. |

Discriminating content of the change — a syllable with **negative exponent**
(an inverted generator, `power < 0`) must contribute its factor
`assign sym ^ power` to the product. In the model this is `wordProd`'s uniform
`assign sym ^ p` for every `p : Int` (no sign guard). The pre-patch code, for a
`PermutationGroup` domain, evaluated `r[i] in gens` which is **False** for an
inverted generator, fell through both `if s in images` / `elif s**-1 in images`
branches, and advanced `i += abs(power)` **without** multiplying that factor in —
silently dropping the syllable. `Solution_prepatch.lean` reproduces exactly this
(a `if s.2 ≥ 0 then assign s.1 ^ s.2 else 1` guard that zeroes the contribution
of negative-exponent syllables) and **fails** `out = wordProd assign syllables`
(G-DIFF), at precisely the goal
`s.2 < 0 → assign s.1 ^ s.2 = 1` — false in any nontrivial group.

## B. No second independently-fixed behavior

The patch also restructures the surrounding `_check_homomorphism` preamble
(`hasattr(domain,'relators')` branch → `pres = …`; building `gens`/`symbols`/
`symbols_to_domain_generators`). These are **R**-refinements feeding `assign`
(A2) — they compute the *same* relator list and symbol→image map the old code
used (`rels`, and the `gens`/`domain.generators` correspondence), just hoisted
and generalized to cover permutation domains uniformly. They introduce no
observable behavior beyond what `_image` consumes; their effect is entirely
captured by the verdict G-CONF differential-tests. Hence a single modeled method
and a single failing prepatch suffice.

## C. No kind-3 (inexpressible-changed-op) steps; no consumed axioms

Every step is R or I. The operation that genuinely *changed* — the per-syllable
group-product computation of `_image` — is modeled **deeply** (the spelled-out
front-recursive fold `wordProd`, step A4), NOT hidden behind an axiom about the
function under change (SPEC §0.7). There is therefore **no `imageOf` axiom** and
**no A-reference callee**: the group arithmetic (`*`, `^`, `1`, `is_identity`)
is the codomain's own operation, refined per mapping.md §2 and exercised for
real on both legs by G-CONF. Consequently **G-AX is `skip`** (no `axiom_check.py`,
no assumed callee contract to falsify) — shipping a dead axiom here would violate
SPEC §0.7.

## D. verify(Solution) ⇒ resolved

`evalWord` verifies only if its output equals the exact ordered group product
over **all** syllables with signed exponents (A4) — in particular contributing
each negative-power (inverted-generator) syllable. By R (`array_form ↔ List (Nat
× Int)`, symbol→image composite, codomain group-op identities) the verified fold
equals the patched `_image(r)` on permutation-group inputs; the enclosing
`_check_homomorphism` verdict is `all(_image(r).is_identity)`, which by mapping.md
§2 is `all (wordProd assign rᵢ = 1)`. By G-CONF the R/I transliteration of the
fold agrees with `patch.diff`'s `_check_homomorphism` verdict on the
identity/all-identity boundary assignments + 10⁵ fuzzed assignments (0
disagreements). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point of plan §1.1 that applies here is refinement
fidelity (this doc + G-CONF); there is no axiom-soundness trust point because
there are no axioms.
