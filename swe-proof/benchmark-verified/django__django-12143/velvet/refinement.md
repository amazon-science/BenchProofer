# refinement.md — django__django-12143

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`editedObjectPks` `do` block and the deep `matchesKey`/`editedPks` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I** (identical
concrete op). EVERY step is R, A, or I.

This bundle has **no A-tagged steps**: the changed operation is the in-function
key matcher, modeled deeply (no external callee axiom). The R/I legs are
mechanically refuted by **G-CONF** (`conformance_check.py`, §4.1); the narrative
is audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `_get_edited_object_pks()` (`django/contrib/admin/options.py:1633`)

Gold hunk:
```
- pk_pattern = re.compile(r'{}-\d+-{}$'.format(prefix, self.model._meta.pk.name))
+ pk_pattern = re.compile(
+     r'{}-\d+-{}$'.format(re.escape(prefix), self.model._meta.pk.name)
+ )
  return [value for key, value in request.POST.items() if pk_pattern.match(key)]
```

The change escapes `prefix` so it is matched as a **literal** sequence of
characters rather than as a regex pattern. The frozen spec models the matcher as
a literal match (`stripPrefix`), so the spec already encodes the post-patch
behaviour; the pre-patch (unescaped) skeleton fails against it (G-DIFF).

| # | Solution.lean impl op (`editedObjectPks`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `pfx : List Char` | `prefix: str` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | param `pkname : List Char` | `self.model._meta.pk.name` (a `str`, a Python identifier) | R | `str` ↔ `List Char`. Bound as data, not a callee; pk.name is an identifier so it has no regex metacharacters and the post-patch regex matches it literally — exactly `stripPrefix pkname`. |
| A3 | param `items : List (List Char × List Char)` | `request.POST.items()` | R | the ordered (key, value) multidict items ↔ a list of char-pair tuples, order-preserving (mapping.md §2). |
| A4 | `editedPks pfx pkname items` (the per-item selection, computed by the backward `while` fold) | `[value for key, value in request.POST.items() if pk_pattern.match(key)]` | I | the comprehension is the in-order keep-if-match selection; `editedPks` is exactly that, front-recursive. The backward `while` loop computes it (drop-step lemma). Concrete, transliterated by G-CONF. |
| A5 | `matchesKey pfx pkname kv.1` (the per-key decision: literal `pfx`, `'-'`, nonempty digit run, `'-'`, literal `pkname`, end) | `pk_pattern.match(key)` for `pk_pattern = re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pk.name))` | I (deep model) | the changed operation, modeled DEEPLY in the `pure` region: `stripPrefix`/`takeDigits`/`atEnd` ARE the anchored literal+`\d+`+`$` match of the **escaped** pattern. No consumed axiom; the matcher's fidelity to the real `re` engine is the R/I leg G-CONF differential-tests against the real patched regex. mapping.md §2,§2.1,§2.2. |
| A6 | `result` returned (`List (List Char)`) | the comprehension's `list` result (the POST values) | R | list of value `str` ↔ `List (List Char)`, order preserved. |

Discriminating content of the change — `prefix` matched **literally** vs as a
**pattern** — lives in `stripPrefix pfx key` (model: exact char-sequence match)
⇔ `re.escape(prefix)` (real). When `prefix` carries a regex metacharacter the two
diverge: e.g. with `prefix = "form$"`, the pre-patch unescaped pattern treats the
`$` as an end-of-input anchor inside the prefix, so a real key like
`form$-0-uuid` is NOT matched and its value is silently dropped (the data loss in
the issue). `Solution_prepatch.lean` reproduces the unescaped behaviour (the
`if pfx.contains '$' then false` skeleton standing in for "prefix interpreted as
a pattern, so a `$`-bearing prefix mis-anchors") and **fails** `out = editedPks
pfx pkname items` (G-DIFF).

## B. No A (axiom / callee) steps

There is no unchanged external callee in the changed line: `re.escape`,
`re.compile`, `.match`, `.format`, and `.items()` are all part of the modeled
matcher/selection and are transliterated as concrete (I) ops or refined types
(R). The matcher is modeled deeply, so there is no consumed axiom and no
A-reference deep model of an external callee. `axiom_check.py` therefore records
"no axioms" and exits 0 (G-AX skip-equivalent).

## B2. Termination semantics (spec-strengthening, audit repair)

The bundle uses `loom.semantics.termination "total"` (`TotalCorrectness`), not
`"partial"`. A prior audit (G-EQ / G-PANEL-1) exhibited a same-spec
counterexample under partial correctness: a diverging implementation (a
non-terminating loop in place of the single finite pass over `items`) verified
vacuously, because partial correctness constrains only terminating executions —
and its translated patch would hang the request handler, so it does not resolve
(verify⇏correct). The real `_get_edited_object_pks` is a single list
comprehension over the finite `request.POST.items()` — it always terminates —
so total correctness is the faithful semantics: it rejects every diverging impl
(a loop whose `decreasing` measure cannot be discharged is unprovable under
total semantics) while the verified backward fold here carries `decreasing i`
and is unaffected. The `set_option`/`open` lines are part of the frozen spec
view shared byte-identical by both twins.

## B3. Digit-class fidelity (faithfulness repair)

A prior faithfulness audit (G-PANEL-2) exhibited a divergence on keys whose
index run uses non-Latin decimal digits: the real matcher's digit class is
Unicode-aware (it accepts every decimal number system's digits), while the
model's `isDigit` was previously ASCII-only (`Char.isDigit`), making the spec
strictly stronger than the real callee on such keys. Repaired: `isDigit` now
tests membership in `digitRanges`, the exact inclusive code-point bounds of
the Unicode decimal-digit (Nd) runs per the instance image's Unicode data,
extracted mechanically in-container (mapping.md §2.2). The A5/I leg is thus
faithful on the full input domain; G-CONF's shadow transliterates the same
range table and its fuzzer now injects non-Latin digits and digit-like
non-digit near-misses on both the should-match and should-not-match paths.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — interpreting
`prefix` as a literal instead of a regex pattern — is modeled **deeply** as the
literal `stripPrefix` match (A5), not hidden behind an axiom about the function
under change. There are no consumed axioms.

## D. verify(Solution) ⇒ resolved

`editedObjectPks` verifies only if its output equals `editedPks pfx pkname items`,
i.e. the in-order selection of values whose key matches `matchesKey` — the
anchored **literal**-prefix + `\d+` + literal-pkname + end pattern (A4, A5). By R
(`str ↔ List Char`, order-preserving items, pk.name literal) the verified
selection equals the post-patch comprehension over `request.POST.items()` with
`re.escape(prefix)` on the tested `str` inputs. By G-CONF the R/I transliteration
of the matcher + fold agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed inputs
(including regex-metacharacter prefixes and trailing-`\n` keys). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms (G-AX trivial).
