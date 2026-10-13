# refinement.md — sphinx-doc__sphinx-9673

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`augmentTypeFields` `do` block plus the pure helpers it calls) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed** /
**A-reference** (axiomatized / deep-modeled callee — none here), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1). There are no A legs. Claim: any impl verifying against this frozen spec,
refined per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE; confirmed byte-identical
to `instance.json.patch`).

## A. The single change site — `augment_descriptions_with_types` (`sphinx/ext/autodoc/typehints.py:130`)

Gold hunk (two literal-comparison widenings):
```
-        elif parts[0] == 'return':
+        elif parts[0] in ('return', 'returns'):
             has_description.add('return')
...
-        if name == 'return':
+        if name in ('return', 'returns'):
             continue
```

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `fields : List (List Tok)`, `annotations : List (Tok × Tok)` (read-only, not `mut`) | `node` field-name strings, `annotations` dict | R | bijection mapping.md §2; both inputs read, neither mutated (directive 5 — `ensures` is a pure function of them, no `mut` param). |
| A2 | the first `while i < fields.length` loop: `s := classifyField fields[i]! s` | the `for field in fields:` classification loop (`typehints.py:136-155`) | I + R | one-to-one transliteration: `param`/`type`/`return`/`rtype` branches map to the same `add_desc`/`add_type` updates. The widened branch `p0 == returnTok || p0 == returnsTok → addDesc s returnKey` ⇔ gold `parts[0] in ('return','returns')`. R only on the token/`Sets` carrier. |
| A3 | the second `while j < annotations.length` loop: `result := emitStep s result annotations[j]!` | the `for name in annotations:` back-fill loop (`typehints.py:157-165`) | I + R | transliteration: skip when `name == returnTok || name == returnsTok` ⇔ gold `name in ('return','returns')`; else append `Field.typeOf name na.2` when `name ∈ hasDesc ∧ name ∉ hasType` ⇔ gold `name in has_description and name not in has_type`. |
| A4 | `return result ++ rtypeField s annotations` | the trailing `if 'return' in annotations: if 'return' in has_description and 'return' not in has_type:` block (`typehints.py:167-174`) | I | concrete: emit one `Field.rtype (lookupReturn annotations)` exactly when the result is annotated, described, and untyped — unchanged by the patch but part of the observed appended sequence. |

## B. The discriminating clause (G-DIFF)

The two widenings are **one coupled behavioural change**: a result documented
under the plural `returns` spelling must be recognized as described, so that when
the result is annotated and untyped a trailing `rtype` field is appended.

`Solution_prepatch.lean` reproduces the pre-patch skeleton: `classifyBuggy`
recognizes ONLY the short `return` token, and `emitBuggy` skips ONLY the short
token. On `fields = [["returns".toList]]`, `annotations = [("return", "int")]`
the buggy impl records no description for `returnKey`, so `rtypeField` emits `[]`,
whereas the frozen spec `buildFields` emits `[Field.rtype "int"]`. The carried
gold proof therefore cannot discharge `out = buildFields fields annotations` and
verification **fails** (G-DIFF). This is exactly the F2P case
(`test_autodoc_typehints_description_no_undoc`: a `:returns:`-documented function
must gain a `Return type:` field).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The changed operation is two literal-membership widenings,
modeled **concretely** in `classifyField`/`emitStep` (the `|| returnsTok` /
`name == returnsTok` disjuncts) — not hidden behind any axiom. There is **no
consumed axiom and no deep-model reference**: the function calls no unchanged
external callee whose contract the spec must assume (mapping.md §3). G-AX is
vacuous.

## D. verify(Solution) ⇒ resolved

`augmentTypeFields` verifies only if its output equals `buildFields fields
annotations`, whose `classifyField`/`emitStep` accept BOTH `return` and `returns`
spellings (A2, A3) and whose `rtypeField` then appends the trailing result-type
field (A4). By R (string↔`List Char` / dict↔assoc-list / set↔membership-list,
mapping.md §2) the verified impl equals the gold patched
`augment_descriptions_with_types` on the appended-field sequence; by G-CONF the
R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). There are
no axiom trust points; the only trust point is refinement fidelity (this doc +
G-CONF).
