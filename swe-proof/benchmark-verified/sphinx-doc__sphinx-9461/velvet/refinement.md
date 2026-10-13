# refinement.md — sphinx-doc__sphinx-9461

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`assembleModifierTokens` `do` block plus the pure `annotationTokens` model it pins)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's property),
**A-reference** (a deep model validated == its real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
narrative is audited by **G-EQ**. Claim: any impl verifying against this frozen
spec, refined per the map below, produces the same rendered modifier prefix as
the gold patch on every flag combination, so the F2P test `test_pyproperty`
passes and the harness resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled site — `PyProperty.get_signature_prefix` (`sphinx/domains/python.py:866`)

Gold hunk (the modeled function):
```python
-        prefix = ['property']
+        prefix = []
         if 'abstractmethod' in self.options:
-            prefix.insert(0, 'abstract')
+            prefix.append('abstract')
+        if 'classmethod' in self.options:
+            prefix.append('class')

+        prefix.append('property')
         return ' '.join(prefix) + ' '
```
(plus the new option declaration `'classmethod': directives.flag` at `:855`).

| # | Solution.lean impl op (`assembleModifierTokens`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `firstFlag : Bool` | `'abstractmethod' in self.options` | R | dict-membership bool ↔ `Bool` (mapping.md §2). |
| A2 | param `secondFlag : Bool` | `'classmethod' in self.options` (NEW option) | R | dict-membership bool ↔ `Bool` (mapping.md §2). The new `'classmethod': directives.flag` declaration is what makes this dict key reachable; modeled as the second input flag. |
| A3 | `let mut toks := []` | `prefix = []` | I | identical empty-list seed (post-patch no longer seeds with the kind token). |
| A4 | `if firstFlag then toks := toks ++ ["abstract"]` | `if 'abstractmethod' in self.options: prefix.append('abstract')` | I | identical append of the abstract token, guarded by the first flag. Post-patch this is `append` (end), not the pre-patch `insert(0, …)` (front) — but with an empty seed and the kind token appended last (A6), the order coincides for the abstract case; the change that matters is the relative order vs. the new `class` token (A5). |
| A5 | `if secondFlag then toks := toks ++ ["class"]` | `if 'classmethod' in self.options: prefix.append('class')` | I | identical append of the class token, guarded by the second flag — the NEW behaviour. Placed AFTER the abstract token and BEFORE the kind token. |
| A6 | `toks := toks ++ ["property"]` | `prefix.append('property')` | I | identical append of the always-present kind token, last. |
| A7 | `return toks` | `return ' '.join(prefix) + ' '` | R | the returned `List String` ↔ the joined prefix string; the space-join + trailing space is the unchanged trailing op applied to the modeled token list (mapping.md §2). G-CONF compares the joined strings. |

`annotationTokens firstFlag secondFlag` (the pure region) is exactly the token list
A3–A6 build: `(abstract? ) ++ (class? ) ++ [property]`. The `ensures out =
annotationTokens firstFlag secondFlag` pins the produced list to this assembly; the
auxiliary `ensures`es pin the discriminating facts (the class token is present
whenever the second flag is set; the kind token is always present and last).

## B. The discriminating change

Pre-patch, `prefix` is seeded with `['property']` and only the first flag may
prepend its token (`insert(0, 'abstract')`); **there is no branch for the second
flag**, so a set `:classmethod:` is silently dropped and the rendered prefix is
just `"property "` / `"abstract property "`. Post-patch the second flag appends
`'class'`, yielding `"class property "` / `"abstract class property "`.

`Solution_prepatch.lean` reproduces the pre-patch skeleton (kind-token seed,
first-flag-only front-insert, no second-flag branch) and **fails** verification
on exactly the second-flag clauses:
- `ensures secondFlag = true → "class" ∈ out` — the prepatch never emits `"class"`;
- `ensures out = annotationTokens firstFlag secondFlag` — diverges whenever
  `secondFlag = true` (the model contains `"class"`, the prepatch does not).

This is G-DIFF: the spec sees the actual bug (the dropped class-method modifier).

## C. No kind-3 (inexpressible-changed-op) steps

Every modeled step is R or I; there is no axiom and no deep-model reference. The
genuinely-new behaviour — contributing the second modifier token in canonical
order — is modeled **concretely** (the `if secondFlag` branch, A5, and the
`annotationTokens` definition), not hidden behind an axiom.

The two co-changed files (`sphinx/util/inspect.py`,
`sphinx/ext/autodoc/__init__.py`) are **not** modeled: they are runtime
descriptor-protocol / MRO introspection (recognizing a `@classmethod @property`
and extracting its docstring) outside Velvet's expressible fragment, and it would
be unsound to axiomatize them since they are themselves changed functions
(directive 7). They are documented in mapping.md §3.2 as additional change sites.
The shipped `patch.diff` is the gold patch verbatim and resolves all three F2P
tests; only the cleanly-expressible rendering site (`get_signature_prefix`,
directly observed by `test_pyproperty`) carries a Velvet `method`. (Precedent:
sphinx-7590, sphinx-10673.)

## D. verify(Solution) ⇒ resolved

`assembleModifierTokens` verifies only if its output equals `annotationTokens
firstFlag secondFlag` for all flag combinations — i.e. it emits the abstract
token iff the first flag is set, the class token iff the second flag is set, in
that canonical order, with the kind token always last. By R (`bool ↔ Bool`, the
unchanged space-join A7) the verified function equals the post-patch
`get_signature_prefix` on every flag combination; by G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs (the four
flag combinations, exhaustively). Therefore a model satisfying this spec, refined
by the map above, is the gold patch's rendering behaviour up to type refinement —
and the gold patch (all three sites) resolves (G-RESOLVE). Trust points:
refinement fidelity (this doc, G-EQ + G-CONF). There are no axioms, so no
A-soundness trust point (G-AX skip).
