# refinement.md — django__django-15380

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`frameRenamedField` `do` block plus the deep models `lookupState` /
`renameLookup`) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — **A-consumed** where the proof
uses an axiom's `ensures`, **A-reference** where a deep model is validated == the
real callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, resolves the harness.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The state-resolution prologue — `generate_renamed_fields` (`autodetector.py:822`)

Gold hunk:
```
  old_model_name = self.renamed_models.get((app_label, model_name), model_name)
  old_model_state = self.from_state.models[app_label, old_model_name]
- new_model_state = self.to_state.models[app_label, old_model_name]
+ new_model_state = self.to_state.models[app_label, model_name]
```

| # | Solution.lean impl op (`frameRenamedField`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `priorModels`, `currentModels` : assoc lists of `(app,name) → ModelEntry` | `self.from_state.models`, `self.to_state.models` | R | dict ↔ assoc list; `d[k]`/`KeyError` ↔ `lookupState some/none` (mapping.md §2). |
| A2 | `renamed` : assoc list of `(app,name) → String` | `self.renamed_models` | R | dict ↔ assoc list (mapping.md §2). |
| A3 | `app`, `curModelName` : `String` | `app_label`, `model_name` (a *current* / `to_state` model name, from `new_field_keys`) | R | `str` ↔ `String`; `model_name` is a current name (mapping.md §1). |
| A4 | `priorName := renameLookup renamed (app, curModelName)` | `old_model_name = self.renamed_models.get((app_label, model_name), model_name)` | A-reference + I | `renameLookup` deeply models `dict.get(k, k[1])`; the `.get`-with-fallback is the *unchanged* primitive (G-AX validates `renameLookup == renamed_models.get`). The op itself is concrete/transliterated by G-CONF (I). |
| A5 | `oldState := lookupState priorModels (app, priorName)` | `old_model_state = self.from_state.models[app_label, old_model_name]` | A-reference + I | `lookupState` deeply models the name-keyed dict subscription (G-AX validates `lookupState == dict.get`). The prior-state map is keyed by prior names, so this resolves under `priorName` — UNCHANGED by the patch. |
| A6 | `newState := lookupState currentModels (app, curModelName)` | `new_model_state = self.to_state.models[app_label, model_name]` | A-reference + I | **the changed op.** The current-state map is keyed by *current* names; the entry is resolved under `curModelName`, not `priorName`. `lookupState` is the deep model (A-reference, G-AX); the *key choice* is the spec's discriminating content. |
| A7 | `return (oldState, newState)` | the two locals `old_model_state` / `new_model_state` feeding `new_model_state.get_field(field_name)` and the rename scan | R | the routine's downstream `.get_field`/deconstruct reads are an R-identity over the resolved entries; the bundle pins *which entries are resolved*, which is what the issue's `KeyError` is about. |

Discriminating content of the change — the **current-state** entry is resolved
under the model's **current** name (`curModelName`), not its prior name
(`priorName`) — lives in `ensures out.2 = lookupState currentModels (app,
curModelName)` (model) ⇔ `self.to_state.models[app_label, model_name]` (real,
post-patch). The pre-patch resolved it under `old_model_name`
(`to_state.models[app_label, old_model_name]`); `Solution_prepatch.lean`
reproduces that and **fails** the `out.2` clause (G-DIFF) — and, refined, that is
the `KeyError: ('test_one', 'mymodel')` the issue reports, because a renamed
model is absent from `to_state.models` under its prior name.

## B. No consumed axioms

`meta.json axioms == []`. The two foreign primitives (name-keyed dict lookup;
`dict.get` with fallback) are modeled **deeply** by `lookupState` / `renameLookup`
(A-reference, §3.1 of mapping.md), validated == the real primitives by G-AX, not
hidden behind a consumed axiom about the function under change. There is no dead
axiom.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the key the current-state lookup is given — is expressed directly (the `out.2`
postcondition and the `do` block's `lookupState currentModels (app,
curModelName)`), not hidden behind an axiom about `generate_renamed_fields`.

## D. verify(Solution) ⇒ resolved

`frameRenamedField` verifies only if the current-state entry is resolved under
`curModelName` (A6) — i.e. the gold key choice. By R (`dict ↔ assoc list`,
`str ↔ String`) and by G-AX (`lookupState`/`renameLookup` == the real dict
primitives, including that a renamed model is keyed under its current name and
absent under its prior name), the verified resolution equals what the gold-patched
`generate_renamed_fields` computes; by G-CONF the R/I transliteration agrees with
the patched autodetector's behaviour over fuzzed model+field-rename scenarios.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited primitives — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: deep-model soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
