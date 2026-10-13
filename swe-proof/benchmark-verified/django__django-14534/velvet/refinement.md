# refinement.md — django__django-14534

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`labelIdentifier` `do` block plus the deep `recordedId` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no axioms** (A) in this
bundle. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The label-identifier site — `BoundWidget.id_for_label`

Gold hunk (`django/forms/boundfield.py:278-280`):
```
     @property
     def id_for_label(self):
-        return 'id_%s_%s' % (self.data['name'], self.data['index'])
+        return self.data['attrs'].get('id')
```

| # | Solution.lean impl op (`labelIdentifier`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `attrs : Attrs` (`List (String × String)`) | `self.data['attrs']` (the widget's recorded attributes `dict`) | R | the recorded-attributes mapping ↔ an ordered key/value list (mapping.md §2); `dict.get(k)` ↔ `List.lookup k`. G-CONF bridges via the same table. |
| A2 | parameters `name : String`, `index : String` | `self.data['name']`, `self.data['index']` | R | the widget's recorded name and position; read-only here, and (post-patch) NOT consulted by the result — present in the signature so the spec can pin that the result does not depend on them (directive 5 / spec-strength). |
| A3 | `return attrs.lookup "id"`; `ensures out = recordedId attrs` | `return self.data['attrs'].get('id')` | I | the single recorded-`"id"` lookup, modeled deeply: `recordedId attrs = attrs.lookup "id"`. `dict.get('id')` (`some v` / `None`) ↔ `List.lookup "id" attrs` (`some v` / `none`) under the `Option`/`None` bijection (mapping.md §2). G-CONF refutes any divergence. |

Discriminating content of the change — the identifier must be the one the
surrounding rendering ALREADY RECORDED for this widget under `"id"` (including
any caller-chosen `auto_id` prefix), rather than a string SYNTHESIZED from the
widget's name and position — lives in `out = recordedId attrs` (model) ⇔ the
replacement of `'id_%s_%s' % (name, index)` by `self.data['attrs'].get('id')`
(real). The pre-patch synthesized `id_<name>_<index>` independently of `attrs`;
`Solution_prepatch.lean` reproduces that (`some ("id_" ++ name ++ "_" ++ index)`,
ignoring `attrs`) and **fails** the postcondition `out = recordedId attrs`,
leaving the goal `some ("id_" ++ name ++ "_" ++ index) = List.lookup "id" attrs`
(G-DIFF). This is exactly the two observable failures the F2P tests exercise:
(1) `test_boundfield_subwidget_id_for_label` — with `auto_id='prefix_%s'` the
recorded id is `prefix_field_0`, not the synthesized `id_field_0`; (2)
`test_iterable_boundfield_select` — with `auto_id=False` no id is recorded, so
the result must be `None`, not the synthesized `id_name_0`.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The changed read is expressed concretely (A3, a total
`List.lookup` over the recorded attributes); nothing inexpressible is hidden, and
no callee is axiomatized. The `name`/`index` parameters are carried so the
postcondition can pin that the result depends ONLY on the recorded attributes —
the precise property the synthesized pre-patch violates.

## C. verify(Solution) ⇒ resolved

`labelIdentifier` verifies only if its output equals `recordedId attrs =
attrs.lookup "id"` — i.e. it must return the recorded `"id"` attribute (`some v`
when present, `none` when absent) and must NOT synthesize an identifier from
`name`/`index` (A3). By R (`self.data['attrs'] ↔ Attrs`, `dict.get('id') ↔
List.lookup "id"`, `None ↔ none`, mapping.md §2) the verified read equals the
gold patch's `self.data['attrs'].get('id')`; by G-CONF the R/I transliteration
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs across recorded-id (with and
without caller prefixes, index-bearing ids) and absent-id cases. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The sole trust point
is refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom trust point.
