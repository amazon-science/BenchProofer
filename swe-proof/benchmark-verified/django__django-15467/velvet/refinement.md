# refinement.md — django__django-15467

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `emptyLabelFor` `do` block, plus the deep `resolvedLabel`/`defaultLabel`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The empty-placeholder resolution — `formfield_for_foreignkey` (`options.py:272`)

Gold hunk (the radio-fields branch of `formfield_for_foreignkey`):
```
- kwargs["empty_label"] = _("None") if db_field.blank else None
+ kwargs["empty_label"] = (
+     kwargs.get("empty_label", _("None")) if db_field.blank else None
+ )
```

| # | Solution.lean impl op (`emptyLabelFor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `allowsBlank : Bool` | `db_field.blank` | R | `bool ↔ Bool` (mapping.md §2). |
| A2 | param `override : Option (Option String)` | the `kwargs` empty-placeholder entry, read by `kwargs.get("empty_label", …)` | R | key-presence bijection `absent ↔ none`, `present v ↔ some v`, `present None ↔ some none` (mapping.md §2). The nested option preserves the three-way distinction `kwargs.get` observes. |
| A3 | `if allowsBlank then … else return none` | `… if db_field.blank else None` | I | identical concrete conditional: the non-blank branch yields no placeholder. |
| A4 | `override.getD defaultLabel` (blank branch) | `kwargs.get("empty_label", _("None"))` | R + (A-reference for `defaultLabel`) | `dict.get(key, d) ↔ Option.getD` (mapping.md §2): keep the caller's value when the key is present, else the fallback `d`. The fallback `d = _("None")` is modeled deeply as `defaultLabel = some "None"`; that the deep model equals the real `gettext("None")` under the test locale is the **A-reference** G-AX validates (mapping.md §3.1). No consumed axiom. |
| A5 | `out : Option String` returned | the value assigned to `kwargs["empty_label"]`, becoming the constructed field's `empty_label` | R | `Option String ↔ str|None` (mapping.md §2); `ModelChoiceField.__init__` stores `empty_label` as-is (with the orthogonal `RadioSelect ∧ not blank ⇒ None` rule, which coincides with A3's non-blank branch — see §D), and the F2P test reads `ff.empty_label`. |

Discriminating content of the change — when an empty selection is admitted
(`allowsBlank = true`) and the caller supplied a placeholder (`override = some v`),
the result is `v`, **not** the fallback `defaultLabel`. This lives in
`override.getD defaultLabel` (model) ⇔ `kwargs.get("empty_label", _("None"))`
(real). The pre-patch expression `_("None") if db_field.blank else None` always
returned the fallback in the blank branch; `Solution_prepatch.lean` reproduces
that (`let e := defaultLabel`) and **fails** `out = resolvedLabel allowsBlank
override` precisely on `allowsBlank = true ∧ override = some v` with `v ≠
defaultLabel` (G-DIFF; the verifier leaves exactly the goal
`defaultLabel = resolvedLabel allowsBlank override`, unsolvable for such inputs).

## B. No consumed axioms

The modeled slice calls no unchanged imperative callee whose contract the proof
consumes. The single external value, `_("None")`, is an **unchanged** callee's
*value* reproduced by the deep model `defaultLabel` (A-reference, §A4 / mapping
§3.1) — not an `axiom` the proof discharges with. There is therefore no
A-consumed row and no dead axiom (SPEC_GUIDE §0.7, §3).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
blank-branch placeholder choice — is modeled **directly** as the closed function
`resolvedLabel` (`override.getD defaultLabel`), an exact transliteration of
`kwargs.get(key, _("None"))`, not hidden behind an axiom about the function under
change. Nothing is inexpressible.

## D. verify(Solution) ⇒ resolved

`emptyLabelFor` verifies only if its output equals `resolvedLabel`: in the blank
branch it must keep a caller-supplied placeholder (`override.getD defaultLabel`,
A4) and fall back to `defaultLabel` only when none was supplied; in the non-blank
branch it must yield `none` (A3). By R (`bool ↔ Bool`, the key-presence carrier,
`dict.get ↔ Option.getD`, `str|None ↔ Option String`) the verified resolution
equals the post-patch `kwargs["empty_label"] = kwargs.get("empty_label",
_("None")) if db_field.blank else None`.

Downstream, `ModelChoiceField.__init__` stores `empty_label` verbatim except for
the independent rule "`RadioSelect` widget ∧ `not blank` ⇒ `empty_label = None`"
(`forms/models.py:1467`). That rule only fires when `not blank`, where A3 already
yields `none`; on the blank branch (the only branch where the change is
observable) it never fires, so the stored `empty_label` is exactly `out`. Hence
the F2P test `test_radio_fields_foreignkey_formfield_overrides_empty_label`
(blank ForeignKey `Inventory.parent`, `formfield_overrides` supplying
`empty_label="Custom empty label"`) observes `ff.empty_label == "Custom empty
label"` ⇔ `out = some "Custom empty label"`; and the PASS_TO_PASS
`test_radio_fields_ForeignKey` (non-blank `Event.main_band`, no override)
observes `ff.empty_label is None` ⇔ `out = none`.

By G-AX the deep model `defaultLabel` equals the real `gettext("None")`
(A-reference) under the test locale; by G-CONF the R/I transliteration of
`resolvedLabel` agrees with the real patched `formfield_for_foreignkey`'s
observable `empty_label` over ≥10⁵ fuzzed `(blank, override)` configurations.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited callee value — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: the
A-reference value soundness (G-AX) and refinement fidelity (this doc, G-EQ +
G-CONF).
