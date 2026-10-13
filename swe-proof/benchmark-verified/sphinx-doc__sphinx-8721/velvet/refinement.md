# refinement.md — sphinx-doc__sphinx-8721

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`gatedPageEmission` `do` block + the `isCombinedFormat`/`isEbookFormat`/
`shouldSuppress`/`collectedPages` deep models) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement; state the bijection),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (no consumed axioms). Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The gating site — `collect_pages()` (`sphinx/ext/viewcode.py:180`)

Gold hunk (inserted after the existing `if not hasattr(env, '_viewcode_modules'): return`):
```
+    if app.builder.name == "singlehtml":
+        return
+    if app.builder.name.startswith("epub") and not env.config.viewcode_enable_epub:
+        return
```

**Modeled scope (both inserted guards).** This bundle models the full gating
decision the gold patch installs: the single-combined-document guard AND the
e-book opt-in guard. The e-book guard is the behaviour the public issue
describes and the instance's F2P/P2P tests exercise (`make html epub` with
`viewcode_enable_epub=False`); the combined-document guard is the other early
return the same hunk inserts, and omitting it makes the model emit pages where
the real patched `collect_pages` provably emits nothing (a faithfulness
divergence). The combined-document clause is absent from the
`problem_statement` (`hints_text` is empty), so pinning it in the spec view
discloses non-public gold behaviour — dispositioned as relaxed leakage per
spec_guide directive 6 (`RELAXED_LEAKAGE.md`; `meta.json relaxed_leakage =
true`, `gates.G-LEAK.status = "relaxed"`): a faithful spec here MUST name the
discriminator, and an epub-only spec is provably unfaithful at that format.
The map below covers both guards.

| # | Solution.lean impl op (`gatedPageEmission`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `hasModules : Bool`; `if !hasModules then return []` | the pre-existing `if not hasattr(env, '_viewcode_modules'): return` guard (`viewcode.py:181-182`) | R + I | `hasattr(...)` ↔ `hasModules` (mapping.md §2). Unchanged by the patch but part of the modeled control flow: no modules ⇒ generator yields nothing ⇒ `out = []`. |
| A2 | `isCombinedFormat fmt = (fmt == "singlehtml".toList)`; `if isCombinedFormat fmt then return []` | `if app.builder.name == "singlehtml": return` | R + I | Python `str` equality ↔ `List Char` equality via the str↔`List Char` bijection (mapping.md §2). `return` ⇒ `out = []`. |
| A3 | `isEbookFormat fmt = "epub".toList.isPrefixOf fmt`; param `ebookOptIn : Bool`; `if isEbookFormat fmt && !ebookOptIn then return []` | `if app.builder.name.startswith("epub") and not env.config.viewcode_enable_epub: return` | R + I | `str.startswith("epub")` ↔ `List.isPrefixOf "epub".toList`; `not env.config.viewcode_enable_epub` ↔ `!ebookOptIn` (mapping.md §2,§3). The `and` ↔ `&&`. `return` ⇒ `out = []`. |
| A4 | `else return generated` (the carrier of the unchanged emission body) | the unchanged `for ... status_iterator(...)` loop + trailing index `yield` (`viewcode.py:189-279`) — reached only when no guard returns | I | the emission body is unchanged by the patch; modeled as the opaque carrier `generated` (mapping.md §1). When no guard fires the generator yields exactly those pages ⇒ `out = generated`. |
| A5 | result `out : List Page` | the page triples the generator yields (consumed by Sphinx, written as `_modules/<mod>.<suffix>` files) | R | `out = []` ⇔ no `_modules/...` files written; `out = generated` ⇔ the usual pages written. The F2P test observes file existence (mapping.md §2). |

The decision is pinned exactly by `shouldSuppress fmt ebookOptIn =
isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn)` and the emitted list
by `collectedPages`. The discriminating content of the change — under an e-book
build with the opt-in OFF, emit NOTHING (the issue's exact scenario:
`make html epub` with `viewcode_enable_epub=False`), and under the single
combined-document build emit NOTHING — lives in `shouldSuppress ⇒ out = []`.
`Solution_prepatch.lean` reproduces the pre-patch skeleton (only the
`hasModules` guard; neither inserted guard) and **fails**
`out = collectedPages ...` on exactly those clauses: with modules present and a
suppressing format it returns `generated` instead of `[]` (G-DIFF; verified —
unsolved goal `generated = collectedPages fmt ebookOptIn hasModules generated`).

## B. Modeled scope and the prepatch discriminant

The modeled fix is the pair of suppression decisions (A2, A3). The F2P test
`test_viewcode_epub_default` and the P2P `test_viewcode_epub_enabled` exercise
the e-book clause (opt-in OFF ⇒ suppress; opt-in ON ⇒ emit); the combined-
document clause is exercised mechanically by G-CONF against the real patched
`collect_pages` (which returns early on that format regardless of the opt-in).
The prepatch (no inserted guards) returns `generated` whenever either
suppressing path should fire, so it fails `out = collectedPages ...`.

## C. No kind-A axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom**: the operations the modeled
guards use (`==`, `startswith`, `not`, the `hasattr` guard) are all modeled
deeply over the input carriers (`List Char` equality, `List.isPrefixOf`, boolean
negation, a bool). There is no unchanged callee whose exact output values the
proof relies on, so there is no A-reference deep model to validate either —
hence no `axiom_check.py` and `G-AX: skip` (mapping.md §3). The operations that
genuinely *changed* — inserting the two suppression guards — are modeled deeply
as `isCombinedFormat` / `isEbookFormat` / `shouldSuppress` / `collectedPages`,
not hidden behind an axiom.

## D. verify(Solution) ⇒ resolved

`gatedPageEmission` verifies only if its output is `[]` exactly when no modules
were collected OR the format is the single combined document OR the e-book
family without opt-in, and `generated` otherwise (A1-A5). By R
(`app.builder.name ↔ fmt`, `viewcode_enable_epub ↔ ebookOptIn`,
`hasattr ↔ hasModules`, page-emission ↔ `List Page`) the verified gate equals
the patched `collect_pages` guard behaviour: under `make html epub` with
`viewcode_enable_epub=False` the e-book build emits no `_modules/...` pages
(F2P `test_viewcode_epub_default`), and with the flag `True` it emits them
(P2P `test_viewcode_epub_enabled`). By G-CONF the R/I transliteration of the
gating decision agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed
(format, opt-in, has-modules) inputs — including the combined-document format.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
single trust point is refinement fidelity (this doc, G-EQ + G-CONF); there is
no axiom-soundness trust point.
