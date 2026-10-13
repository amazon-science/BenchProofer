# refinement.md — django__django-12308

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`displayJson` `do` block + the deep `jsonDisplay` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A-consumed** (proof
uses an axiom's `ensures`), **A-reference** (deep model validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The display dispatch — `display_for_field` (`django/contrib/admin/utils.py:380`)

Gold hunk (inserted branch + the pre-existing fall-through it precedes):
```
+    elif isinstance(field, models.JSONField) and value:
+        try:
+            return field.get_prep_value(value)
+        except TypeError:
+            return display_for_value(value, empty_value_display)
     else:
         return display_for_value(value, empty_value_display)
```

| # | Solution.lean impl op (`displayJson`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `v : ValueView` | `value` (rendered for a `field` that is a `JSONField`) | R | the renderer reads only three observable facts of `value`; the bijection (mapping.md §2) packs them into `ValueView`. The `isinstance(field, models.JSONField)` type guard is R-collapsed (this method IS the JSON branch). |
| A2 | `if v.present then …` | the `and value` truthiness conjunct of `isinstance(field, models.JSONField) and value` | R + I | `v.present ↔ bool(value)` (mapping.md §2). When false the JSON arm is skipped and control reaches `display_for_value` — modeled by the `else v.generic` branch. |
| A3 | `match v.prep with \| json text => text` | `try: return field.get_prep_value(value)` (success) | A-reference + I | `v.prep` is the deeply-modeled JSON-serialization outcome (`get_prep_value` = `json.dumps`, mapping.md §3.1, an A-reference G-AX validates); returning `text` on success is **I** (concrete). |
| A4 | `\| unserializable => v.generic` | `except TypeError: return display_for_value(value, empty_value_display)` | A-reference + I | a non-serializable value (`json.dumps` raises `TypeError`) ↔ `PrepResult.unserializable`; the fallback is `v.generic` = `display_for_value(...)` (mapping.md §3.2, A-reference). **I** control flow (the `except` arm). |
| A5 | `else v.generic` (the `¬present` branch) | the trailing `else: return display_for_value(value, empty_value_display)` | A-reference + I | an absent JSON value skips the new arm and hits the pre-existing fall-through; `v.generic` is the same `display_for_value` call, which itself maps `None`/absent to `empty_value_display`. **I**. |

Discriminating content of the change — a **present, JSON-serializable** value is
shown as its JSON text (`v.prep = json text ⇒ out = text`), where pre-patch it
fell through to the generic Python rendering (`out = v.generic`, e.g.
`{'foo': 'bar'}` instead of `{"foo": "bar"}`). This lives in the `match v.prep`
arm of `jsonDisplay`. `Solution_prepatch.lean` reproduces the pre-patch
fall-through (`out := v.generic` unconditionally) and **fails** `out =
jsonDisplay v` on exactly that clause (`v.present = true → v.generic = text`),
i.e. G-DIFF.

## B. No consumed axioms

There is **no** module-level `axiom`. The two helpers the new branch calls
(`get_prep_value`/`json.dumps`, `display_for_value`) are **unchanged** by the
patch; their outcomes are carried as the observable fields `v.prep` / `v.generic`
(deep-model **A-references**, G-AX-validated against the real callees), not
consumed as `ensures` facts in the proof. The proof of `displayJson` discharges
purely by `loom_solve; simp [jsonDisplay]` — the impl is the spec's branch
ladder verbatim.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
**addition of a JSON-typed dispatch arm with a serialization-failure fallback** —
is modeled **deeply** (`jsonDisplay`'s if-ladder + `match`, steps A2-A5), not
hidden behind an axiom about the function under change. The unchanged callees are
deep-model references validated by G-AX, never consumed axioms.

## D. verify(Solution) ⇒ resolved

`displayJson` verifies only if its output equals `jsonDisplay v`: JSON text for a
present serializable value (A3), the generic rendering for a present
non-serializable value (A4) and for an absent value (A5). By R (the value-view
bijection, mapping.md §2) the verified branch ladder equals
`display_for_field(value, JSONField(), empty)` post-patch on the tested inputs;
by G-AX the deep-model fields `prep`/`generic`/`present` equal the real
`get_prep_value` / `display_for_value` / `bool` (A-references); by G-CONF the R/I
transliteration of `jsonDisplay` agrees with `patch.diff`'s behaviour on ≥10⁵
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and audited callees — and the gold patch
resolves (G-RESOLVE). The sole trust point is refinement fidelity (this doc,
G-EQ + G-CONF) plus deep-model-reference soundness (G-AX); there are no consumed
axioms to trust.
