# refinement.md — django__django-13112

Maps every operation in `implementation_modelRef` to its `patch.diff` counterpart
in the string-reference branch of `ForeignKey.deconstruct`
(django/db/models/fields/related.py:584). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** op left as the real repo
callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (post-patch string-reference branch)
```python
 if isinstance(self.remote_field.model, str):
-    kwargs['to'] = self.remote_field.model.lower()
+    if '.' in self.remote_field.model:
+        app_label, model_name = self.remote_field.model.split('.')
+        kwargs['to'] = '%s.%s' % (app_label, model_name.lower())
+    else:
+        kwargs['to'] = self.remote_field.model.lower()
```

The changed behavior: for a qualified reference `app_label.ModelName`, the
app-label segment is now preserved VERBATIM and only the model-name segment is
lowercased. A bare reference (no `.`) is still lowercased whole (unchanged
branch).

## Modeling decision
The modeled object is the lazy reference string and its normalized `to` value.
Post-patch normalization is, by shape of the token:
- separator present (`'.' ∈ t.chars`): `prefixSeg t.chars` (verbatim) `++ '.' ::`
  `(nameSeg t.chars).map Char.toLower` — prefix preserved, name lowercased;
- no separator (`'.' ∉ t.chars`): `t.chars.map Char.toLower` — whole token
  lowercased.

The input is a `RefToken`: the character list of the reference string packaged
with the two domain constraints (at most one separator, all-ASCII) as structure
fields, so the domain restriction lives in the type.

- `str.split('.')` is spelled out deeply as `prefixSeg`/`nameSeg`
  (takeWhile/dropWhile on `≠ '.'`); for the modeled single-separator domain these
  equal `split('.')[0]` / `split('.')[1]`.
- `str.lower` is spelled out deeply as per-character `Char.toLower` (ASCII case
  fold), so the model needs no axiom. `Char.toLower` equals the real `str.lower`
  callee only on ASCII code points, so the input type `RefToken` carries an
  `ascii` field (`asciiToken chars`, i.e. `∀ c ∈ chars, c.val < 128`) alongside
  the single-separator field; non-ASCII tokens (where Python's Unicode fold
  `Σ`→`σ`, `İ`→`i̇`, `ẞ`→`ß` diverges from the ASCII-only fold) are formally
  outside the modeled domain. Carrying both constraints in the TYPE (not as
  theorem hypotheses) leaves the correctness theorem hypothesis-free: it pins
  the output on every expressible input, with no unconstrained region an
  alternative implementation could exploit.
- The pre-patch bug being fixed: the whole reference (including the app label)
  was lowercased, so a mixed-case app label like `DJ_RegLogin` became
  `dj_reglogin`, breaking the lazy reference. The post-patch model preserves the
  prefix.

## Operation correspondence
| # | Lean op (`implementation_modelRef`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if '.' ∈ t.chars then …` | `if '.' in self.remote_field.model:` | I | identical separator test selecting the qualified branch. |
| 2 | `let prefixPart := prefixSeg t.chars` | `app_label, _ = self.remote_field.model.split('.')` (the `app_label` part) | R | `prefixSeg` (text before the first `.`) ↔ `split('.')[0]` on the single-separator domain; both return the prefix verbatim. |
| 3 | `let namePart := nameSeg t.chars` | `_, model_name = self.remote_field.model.split('.')` (the `model_name` part) | R | `nameSeg` (text after the first `.`) ↔ `split('.')[1]` on the single-separator domain. |
| 4 | `return prefixPart ++ '.' :: namePart.map Char.toLower` | `kwargs['to'] = '%s.%s' % (app_label, model_name.lower())` | R + A-reference | reassemble: verbatim prefix, the `.` separator, then the lowercased name. `namePart.map Char.toLower` ↔ `model_name.lower()`; `Char.toLower` is the unchanged per-char case fold, bound to the REAL `str.lower` in G-CONF. |
| 5 | `else return t.chars.map Char.toLower` | `else: kwargs['to'] = self.remote_field.model.lower()` | R + A-reference | bare-token branch (unchanged by the patch); `map Char.toLower` ↔ `.lower()`. |

The behavior-changing ops are #2–#4: pre-patch the qualified branch did not exist
and the whole token was lowercased (`t.chars.map Char.toLower`); post-patch the prefix
is preserved. The prepatch impl encodes the pre-patch whole-token lowercasing, so
on `MiXedCase_migrations.Author` it returns `mixedcase_migrations.author` while
the spec forces `MiXedCase_migrations.author` — the exact discrimination behind
the F2P test `test_reference_mixed_case_app_label`.

## R/I legs ⇒ G-CONF
Ops 1 (I) and 2–5 (R) are the full impl content; `Char.toLower` inside ops 4/5 is
the A-reference. G-CONF builds the shadow (separator test, verbatim prefix,
lowercased name / whole) with `Char.toLower` bound to the REAL `str.lower` and
differential-tests it against the REAL patched `ForeignKey.deconstruct`
`kwargs['to']` value over ≥10^5 fuzzed single-separator tokens. `conf_skip =
false`: the impl region has genuine R/I content (the prefix-preserving
normalization is the fixed behavior).

## No A-consumed row
The proof consumes no axiom: `prefixSeg`, `nameSeg`, and `Char.toLower` are all
concrete `def`s / library functions, fully spelled out, so the proof reasons
about them directly. `meta.json axioms = []`. There is no `opaque`/`axiom`
declaration in `Solution.lean`; `axiom_check.py` is a skip stub.

## F2P / issue alignment
- F2P `test_reference_mixed_case_app_label (migrations.test_state.StateTests)`:
  three models in app `MiXedCase_migrations` with FKs/M2M between them. The FK
  deconstruction must keep the mixed-case app label so the lazy reference
  resolves and `project_state.apps.get_models()` finds all 3 models. The spec
  forces the prefix-preserving normalization (`MiXedCase_migrations.author`),
  while the prepatch (whole lowercase → `mixedcase_migrations.author`) breaks it.
- The issue's headline crash (`'dj_reglogin.category'` not installed because app
  is `DJ_RegLogin`) is the same discriminator: the post-patch normalization keeps
  `DJ_RegLogin`. `patch.diff` (gold verbatim) makes the harness resolve.
