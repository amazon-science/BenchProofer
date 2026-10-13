# refinement.md — django__django-13033

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`orderingExpansionDecision` `do` block and the deep `appendRelatedDefaultOrdering`
/ `terminalSegment` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — none here), or **I**
(identical concrete op).

The R/I legs would be mechanically refuted by **G-CONF**; here G-CONF is SKIPPED
(`conf_skip = true`, mapping.md §4 — no DB-free oracle for the lookup
resolution), so the R/I legs' soundness is carried by **G-VERIFY** + **G-DIFF**,
audited narratively by **G-EQ**. `patch.diff` is the gold patch **verbatim**
(applies at `base_commit`, resolves — G-RESOLVE).

## A. The relation-default-ordering guard — `SQLCompiler.find_ordering_name`

Gold hunk (pre-patch → post-patch), `django/db/models/sql/compiler.py:730`:
```python
- if field.is_relation and opts.ordering and getattr(field, 'attname', None) != name and name != 'pk':
+ if (
+     field.is_relation and
+     opts.ordering and
+     getattr(field, 'attname', None) != pieces[-1] and
+     name != 'pk'
+ ):
```

| # | Solution.lean impl op (`orderingExpansionDecision`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `fieldIsRelation`, `modelHasDefaultOrdering : Bool`; `fieldAttr : Option (List Char)`; `segments : List (List Char)`; `lookup : List Char` | the resolved operands `field.is_relation`, `opts.ordering`, `getattr(field,'attname',None)`, `pieces`, `name` | R | type bijection (mapping.md §2): `bool`↔`Bool`, truthiness of `opts.ordering`↔`Bool`, `str`/`None`↔`Option (List Char)`, `list[str]`↔`List (List Char)`. All produced by the UNCHANGED `_setup_joins`, shared by both branches. |
| A2 | `fieldIsRelation` | `field.is_relation` (1st conjunct) | I | identical boolean conjunct, unchanged by the patch. |
| A3 | `modelHasDefaultOrdering` | `opts.ordering` (2nd conjunct, truthiness) | I | identical conjunct; Python `and` consumes the truthiness, abstracted to `Bool` (mapping.md §2). Unchanged by the patch. |
| A4 | `fieldAttr != some (terminalSegment segments)` (`endsAtStoredAttr`) | `getattr(field,'attname',None) != pieces[-1]` (3rd conjunct) | I | **the changed conjunct**, modeled deeply: `terminalSegment segments = segments.getLast!` ↔ `pieces[-1]`; `Option` inequality ↔ `!=` against the `str`/`None`. This is the entire behavioral content of the fix. |
| A5 | `lookup != "pk".toList` (`notPkShortcut`) | `name != 'pk'` (4th conjunct) | I | identical conjunct; `"pk".toList` ↔ the literal `'pk'`. Unchanged by the patch. |
| A6 | `&&` chain returning `out` | `and` chain as the `if` condition's boolean value | I | Python `and` short-circuits to operand truthiness; every operand is modeled at `Bool`/equality level, so `&&` is observationally the same boolean (mapping.md §2). |

Discriminating content of the change — comparing the field's stored attribute
against the **terminal lookup segment** (`pieces[-1]`) rather than the **whole
joined path** (`name`) — lives in A4: `fieldAttr != some (terminalSegment
segments)` (model) ⇔ `getattr(field,'attname',None) != pieces[-1]` (real). The
pre-patch compared against `name`; `Solution_prepatch.lean` reproduces that with
`fieldAttr != some lookup` and **fails** the `out = appendRelatedDefaultOrdering …`
postcondition on any multi-segment lookup that ends at the field's own stored
attribute (`segments = [.., a]`, `lookup = a‥a` the full join, `fieldAttr =
some a`): the whole-path comparison is `true` (forcing a spurious expansion of
the related model's default ordering — the reported wrong DESC + extra join)
while the terminal-segment comparison is `false` (order the column directly).
That is exactly the F2P bug `test_order_by_self_referential_fk` observes
(G-DIFF).

## B. No A (axiom) steps, no kind-3

Every step is R or I. There is no consumed `axiom` and no A-reference deep model
of an outside callee: the operand-producing callee `_setup_joins` is UNCHANGED
and shared by both branches, so it is context, not a contract the proof consumes
(mapping.md §3). The one operation that genuinely *changed* — the third
conjunct's comparison operand — is modeled deeply (`terminalSegment`/
`appendRelatedDefaultOrdering`), not hidden behind an axiom about the function
under change. No *changed-op-inexpressible* (kind-3) step.

This is why there is no `axiom_check.py` (no axioms / A-references to validate)
and why G-CONF is skipped (no DB-free R/I shadow of a guard whose operands are
resolved against a live ORM model graph — mapping.md §4): the deeply-modeled
content is a boolean decision over metadata that is not producible without the
model classes and a compiled query. Soundness rests on G-VERIFY + G-DIFF, the
django__django-13315 precedent.

## C. verify(Solution) ⇒ resolved

`orderingExpansionDecision` verifies only if `out = appendRelatedDefaultOrdering
… segments lookup` — i.e. the guard appends the related model's default ordering
exactly when the field is a relation, the model has a default ordering, the
field's stored attribute is NOT named by the **terminal** lookup segment, and
the lookup is not `pk`. This is precisely what
`test_order_by_self_referential_fk` demands: ordering a self-referential FK by
its stored `<rel>_id` attribute (`order_by('author__editor_id')`,
`pieces[-1] == 'editor_id' == field.attname`) must order that column directly
(ASC, single join), NOT expand the related model's `-pk` default ordering;
ordering by the relation itself (`order_by('author__editor')`,
`pieces[-1] == 'editor' != 'editor_id'`) still expands the default ordering
(DESC) — both legs of the test.

By the R bijection (mapping.md §2) the verified guard corresponds to the patched
`if` condition. The prepatch impl (`fieldAttr != some lookup`) compares against
the whole joined path; for the `order_by('author__editor_id')` case it is `true`
(the stored attribute never equals the full `author__editor_id` path), forcing
the spurious default-ordering expansion — exactly the gold pre-patch bug. It
fails the `out = appendRelatedDefaultOrdering …` clause (G-DIFF), the observable
of the wrong-DESC/extra-join bug. No trust points beyond the type bijection:
there are no axioms, and G-CONF's absence is justified by the live-DB nature of
the operand resolution (mapping.md §4), carried by G-VERIFY + G-DIFF as in the
django__django-13315 precedent.
