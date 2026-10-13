# refinement.md — django__django-13212

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`checkValue` `do` block + the deep `buildReport`/`checkOutcome` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
which drives the *real* patched validators); the A legs + narrative by G-EQ.
This bundle has **no A-consumed and no A-reference rows** — see §C.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The error-construction sites — every validator failure branch

The gold patch repeats one edit across twelve `validators.py` sites (mapping.md
§1.1): a `ValidationError` raised on a validity-failure branch gains
`params={'value': value}` (or `'value': value` appended to an existing `params`).
The shape is uniform; the representative hunk:

```
-            raise ValidationError(self.message, code=self.code)
+            raise ValidationError(self.message, code=self.code, params={'value': value})
```

and the dict-appending variant (`DecimalValidator`, `FileExtensionValidator`):

```
-                params={'max': self.max_digits},
+                params={'max': self.max_digits, 'value': value},
```

| # | Solution.lean impl op (`checkValue`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value : List Char` | the validator argument `value` as `%(value)s` stringifies it (`str(value)`) | R | `str(value)` ↔ `List Char` (mapping.md §2). G-CONF bridges via `str(value)`; the F2P tests assert `form.errors == {'field': [str(value)]}`. |
| A2 | `isValid : Bool` deciding `if isValid then ok else error` | the per-site validity test (`not self.regex.search(...)`, `IPv4Address(value)` raising, `'@' not in value`, `exponent in {'F','n','N'}`, `extension not in allowed`, `'\x00' in str(value)`, …) | R + I | the test is **unchanged** by the patch; abstracted as a free Bool. G-CONF lets the *real* validator decide the branch and mirrors it (`is_valid = oracle[0]`). |
| A3 | `Except.ok ()` on the passing branch | no `raise` (validator returns `None`) | I | acceptance is observationally "no error". |
| A4 | `Except.error (buildReport code oldParams value)` on the failing branch — `buildReport` appends `("value", value)` to `oldParams` | `raise ValidationError(msg, code=code, params={**oldParams, 'value': value})` | I (deep model) | the CHANGED op, modeled **deeply** (`buildReport`/`checkOutcome`, pure region): the report keeps its `code` and pre-existing bindings and additionally binds `"value"`. Transliterated concretely; G-CONF refutes it against the real patched error's `params`. |
| A5 | `code : List Char` carried unchanged into the report; `oldParams` carried unchanged before the append | `code=self.code` / `code='invalid'`; the pre-existing `{'max': …}` / `{'extension': …, 'allowed_extensions': …}` entries | R + I | identity on `code` characters; pre-existing bindings preserved (the `lookupKey_append_pres` postcondition / directive-5 frame). The non-finite `DecimalValidator` site also gains `code='invalid'`, captured by the modeled `code` field. |

Discriminating content of the change — the rejection report now resolves
`%(value)s` to the offending input — lives in
`lookupKey "value" (buildReport …).params = some value` (the A4/A5 postconditions).
`Solution_prepatch.lean` reproduces the pre-patch error (report carrying only
`code`+`oldParams`, no `"value"`) and **fails** the clause
`out = Except.error (buildReport code oldParams value)` (G-DIFF) — the report it
builds lacks the appended binding, so `lookupKey "value"` would return `none`.

## B. The `forms/fields.py` removal — `DecimalField.validate`

Gold hunk: `DecimalField.validate` (a redundant value-less `ValidationError(...,
code='invalid')` for non-finite decimals) is deleted, so the **value-carrying**
`DecimalValidator.__call__` `invalid` error (site A, the non-finite branch)
surfaces instead.

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (no new node) — the modeled failing branch already returns the value-carrying `buildReport` for the `invalid` code | deletion of the duplicate value-less raise in `DecimalField.validate` | I | the removal carries no new modeled op: it eliminates a value-less *duplicate* of the same failure so the modeled value-carrying path is the one observed. Captured by `checkValue` modeling the surviving (value-carrying) `DecimalValidator` `invalid` branch. The F2P `test_value_placeholder_with_decimal_field` `'NaN'` case observes exactly this. |

No separate failing prepatch for site B: it is a deletion whose entire
behavioural content is that the **site-A** value-carrying decimal-`invalid`
report is what reaches the form. Site A's prepatch already exercises the shared
"report must bind `value`" clause for that very code; G-CONF drives the
`DecimalValidator` `invalid` branch on `'NaN'`, `'Infinity'`, `'-Infinity'`.

## C. No A rows; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom and no deep-model
reference**: the one unchanged callee (the per-site validity test) is a **free
Boolean** the postconditions quantify over for every value — owed no contract
(directive 7), so nothing for G-AX to check (the bundle ships no `axiom_check.py`;
G-AX is `skip` by design, the django-16667 precedent). The one operation that
genuinely *changed* — building the rejection report so it carries the input — is
modeled **deeply** (`buildReport`/`checkOutcome`, an I + R step), not hidden
behind an axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`checkValue` verifies only if, on the failing branch, the constructed report
binds `"value"` to `value` while preserving `code` and every pre-existing
binding (A4/A5). By R (`str(value) ↔ List Char`, `code` identity, params dict ↔
assoc list) the verified report equals the gold-patched
`ValidationError(..., params={**oldParams, 'value': value})` on every input; by
G-CONF the R/I transliteration of the error construction agrees with the **real
patched validators**' `params['value']` over 4000+ fuzzed inputs across the
twelve sites (and disagrees with the unpatched validators, confirming the
binding IS the change). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms to trust.
