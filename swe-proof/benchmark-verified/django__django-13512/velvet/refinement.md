# refinement.md — django__django-13512

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `serializeStringValue` `do` block plus the deep `jsonEscapedSeq` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-reference** (deep model validated == the real callee by G-AX), or **I**
(identical concrete op). There are no **A-consumed** axioms in this bundle.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg and this narrative are audited by **G-EQ** /
`axiom_check.py`. Claim: any impl verifying against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The two changed call sites — one shared behaviour

Both hunks make the same edit: add `ensure_ascii=False` to a `json.dumps(...)`
call so non-ASCII code points render literally instead of as `\uXXXX` escapes.

Gold hunk 1 — `django/forms/fields.py:1261` (`JSONField.prepare_value`):
```
- return json.dumps(value, cls=self.encoder)
+ return json.dumps(value, ensure_ascii=False, cls=self.encoder)
```

Gold hunk 2 — `django/contrib/admin/utils.py:403` (`display_for_field`, JSONField
branch); the pre-patch `field.get_prep_value(value)` IS
`json.dumps(value, cls=self.encoder)` (`db/models/fields/json.py:84`):
```
- return field.get_prep_value(value)
+ return json.dumps(value, ensure_ascii=False, cls=field.encoder)
```

Both sites collapse to the same modeled behaviour — `json.dumps(·,
ensure_ascii=False, cls=encoder)` — so a single `method` models both. The `import
json` line added to `utils.py` is import bookkeeping (no behaviour).

| # | Solution.lean impl op (`serializeStringValue`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text : List Char` | the `str` leaf inside `value` passed to `json.dumps` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | result is `'"' :: (jsonEscapedSeq text ++ ['"'])`: a quote, the per-code-point JSON rendering, a quote, computed by the backward `while` fold | `json.dumps(value, ensure_ascii=False, cls=encoder)` restricted to a `str` leaf | A-reference + I | the changed rendering is modeled **deeply**: `jsonChar`/`jsonEscapedSeq` (pure region) and the verified loop ARE the encoder's string-literal output. No consumed encode axiom. The fold ops (`jsonChar c`, `++`, the loop, the quote framing) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `json.dumps(·, ensure_ascii=False)` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A3 | `jsonChar`'s `else [c]` clause (code points ≥ U+0020 not in the escape set, incl. **all** ≥ U+0080) emit the code point itself | the effect of `ensure_ascii=False`: non-ASCII passes through literally | A-reference + I | THE discriminating clause. Pre-patch (`ensure_ascii=True`) emits `\uXXXX` for ≥ U+0080. mapping.md §3.1. |
| A4 | `cls`/encoder choice — omitted | `cls=self.encoder` / `cls=field.encoder` | R | `DjangoJSONEncoder` only extends `default()` for non-`str` leaves; identity on the `str` carrier (mapping.md §3.2). |

Discriminating content of the change — a code point `v ≥ 0x80` renders as itself
(one `Char`), NOT as a `\uXXXX` escape — lives in `jsonChar`'s `else [c]` arm
(model) ⇔ the `ensure_ascii=False` flag (real). `Solution_prepatch.lean`
reproduces the pre-patch all-ASCII mode (escape `v ≥ 128`) and **fails**
`out = '"' :: (jsonEscapedSeq text ++ ['"'])` (G-DIFF): on any non-ASCII input
the two diverge, so `prove_correct` leaves unsolved goals.

## B. No second independently-fixed behaviour

The two hunks are the SAME behavioural fix applied at two call sites (one shared
modeled behaviour, mapping.md §1), not two independent behaviours. The F2P tests
confirm this: `test_prepare_value` exercises `fields.py` and
`test_json_display_for_field` exercises `utils.py`, but both fail/pass on the
identical "non-ASCII renders literally" property. Hence ONE
`Solution_prepatch.lean` (escaping non-ASCII) discriminates both sites — no
separate `Solution_prepatch_2.lean` is needed. (`test_label_for_field` is in the
F2P list only because the test module's import graph changes; it asserts nothing
about JSON serialization and passes once the module imports cleanly.)

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the string-literal encoder's treatment of non-ASCII code points — is modeled
**deeply** (the spelled-out fold `jsonEscapedSeq`/`jsonChar`, steps A2/A3, an
A-reference + I), not hidden behind an axiom about the function under change.
There are **no consumed axioms** at all.

## D. verify(Solution) ⇒ resolved

`serializeStringValue` verifies only if its output equals the exact
per-code-point JSON rendering with non-ASCII passed through literally (A2/A3).
By R (`str ↔ List Char`, encoder = identity on `str`) the verified renderer
equals `json.dumps(text, ensure_ascii=False, cls=encoder)` on the tested `str`
inputs; by G-AX the deep model `jsonEscapedSeq` equals the real
`json.dumps(·, ensure_ascii=False)` (A-reference); by G-CONF the R/I
transliteration of the fold agrees with `patch.diff`'s patched `prepare_value`
on ≥10⁵ inputs and container framing is unchanged. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited callee — and the gold patch resolves (G-RESOLVE). The single trust
point is the A-reference soundness (G-AX); there is no consumed-axiom trust
point.
