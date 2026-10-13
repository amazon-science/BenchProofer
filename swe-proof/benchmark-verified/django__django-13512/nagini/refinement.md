# refinement.md — django__django-13512

The operation-by-operation correspondence between `model.py`'s implementation
(the `json_render_text` impl region and the deep `json_string_body` / `json_char`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There is **no consumed axiom** in this bundle. The single changed operation —
serialising text to JSON while keeping non-ASCII literal — is modelled
**deeply** (`json_string_body` / `json_char`) and validated against the real
`json.dumps(..., ensure_ascii=False)` by G-AX (an **A-reference**).

## A. The forms site — `JSONField.prepare_value` (`django/forms/fields.py:1258`)

Gold hunk:
```
- return json.dumps(value, cls=self.encoder)
+ return json.dumps(value, ensure_ascii=False, cls=self.encoder)
```

| # | model.py impl op (`json_render_text`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text: List[int]` | the text scalar `value: str` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | `result = [34] + body + [34]` where `body == json_string_body(ToSeq(text))`, the per-code-point JSON encoding (`"` → `\"`, `\` → `\\`, else literal incl. all non-ASCII) | `json.dumps(value, ensure_ascii=False, cls=self.encoder)` | A-reference | the changed serialisation is modelled **deeply**: `json_string_body`/`json_char` (the spelled-out per-code-point fold in the `pure` region) and the verified loop in `json_render_text` ARE the `ensure_ascii=False` string encoding. No serialiser axiom is consumed. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `json.dumps(s, ensure_ascii=False)` on the F2P inputs + full `0x20–0xFFFF` index sweep + astral + 40k fuzz and asserts equality, incl. the discriminator (every `c >= 128` kept literal). `cls=self.encoder` is the identity on a text scalar (mapping.md §3.1). |

## B. The admin site — `display_for_field` JSONField branch (`django/contrib/admin/utils.py:401`)

Gold hunk (plus the added `import json` at the top of the module):
```
- return field.get_prep_value(value)
+ return json.dumps(value, ensure_ascii=False, cls=field.encoder)
```

`field.get_prep_value(value)` is `json.dumps(value, cls=self.encoder)`
(`django/db/models/fields/json.py:84`, the pre-patch default `ensure_ascii=True`).
The fix replaces it with the same `json.dumps(..., ensure_ascii=False, cls=…)`
call as site A.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the SAME modelled behaviour `json_render_text` (= `'"' + json_string_body(text) + '"'` for a text scalar) | `json.dumps(value, ensure_ascii=False, cls=field.encoder)` | A-reference | identical serialisation to site A; the admin branch previously delegated to `get_prep_value` (= `json.dumps(value, cls)`, `ensure_ascii=True`) and now calls `json.dumps(..., ensure_ascii=False, cls)` directly. The per-character behaviour the F2P tests pin (`'你好 世界'` rendered literally inside the JSON text) is exactly `json_string_body`, validated by G-AX (mapping.md §3.1). The added module-level `import json` is a bookkeeping import the new call needs (no behaviour of its own). |

Both sites converge on one modelled behaviour, so they share one contracted
function (`json_render_text`). The discriminating content of the change — a
non-ASCII code point (`>= U+0080`) is emitted literally rather than as a
`\uXXXX` escape — lives in `json_char(c) == PSeq(c)` for `c >= 128` (model)
⇔ the `ensure_ascii=False` argument (real). The pre-patch default
`ensure_ascii=True` escapes non-ASCII; `model_prepatch.py` reproduces that (a
non-ASCII branch that emits a backslash-`u` escape sequence) and **fails** the
loop invariant `ToSeq(body) == json_string_body(ToSeq(text).drop(i))`, which is
exactly the spec sensing the change (G-DIFF). One `model_prepatch` suffices:
both hunks are the identical `ensure_ascii=True → False` change, so a single
differential witness covers both independently-observable behaviours.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely
*changed* — the JSON serialiser's per-character handling of non-ASCII text —
is modelled **deeply** (the spelled-out per-code-point fold `json_string_body`
consumed in `json_render_text`, steps A2/B1, an **A-reference**), not hidden
behind an axiom about the function under change. There is **no consumed axiom**.
The serialiser appears only as the **A-reference** that G-AX validates the deep
model against.

## D. verify(model) ⇒ resolved

`json_render_text` verifies only if its output equals `'"' +
json_string_body(text) + '"'` (A2/B1) with the deep per-character encoding that
keeps non-ASCII literal (the discriminating clause `json_char(c) == PSeq(c)`
for `c >= 128`). By R (str ↔ List[int]) the verified renderer equals
`json.dumps(text, ensure_ascii=False, cls=…)` on the tested text scalars; by
G-AX the deep model `json_string_body` equals the real
`json.dumps(..., ensure_ascii=False)` (A-reference) over the entire modelled
domain (full BMP sweep + astral + 40k fuzz). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited reference callee — and the gold patch resolves (G-RESOLVE). The trust
points reduce to the single one of PLAN §1.1 that applies here: refinement
fidelity (this document, G-EQ) and the A-reference soundness check (G-AX);
there is no consumed-axiom trust point.
