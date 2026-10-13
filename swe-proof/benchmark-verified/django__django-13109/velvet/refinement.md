# refinement.md — django__django-13109

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`validateExists` `do` block and the deep `existsMatch`/`matchesTarget` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs would be mechanically refuted by **G-CONF**; here G-CONF is SKIPPED
(`conf_skip = true`, mapping.md §4 — no DB-free oracle for the live-DB existence
test), so the R/I legs' soundness is carried by **G-VERIFY** + **G-DIFF**,
audited narratively by **G-EQ**. `patch.diff` is the gold patch **verbatim**
(applies at `base_commit`, resolves — G-RESOLVE).

## A. The existence-test step — `ForeignKey.validate`

Gold hunk (pre-patch → post-patch):
```python
  using = router.db_for_read(self.remote_field.model, instance=model_instance)
- qs = self.remote_field.model._default_manager.using(using).filter(
+ qs = self.remote_field.model._base_manager.using(using).filter(
      **{self.remote_field.field_name: value}
  )
  qs = qs.complex_filter(self.get_limit_choices_to())
  if not qs.exists():
      raise exceptions.ValidationError(...)
```

| # | Solution.lean impl op (`validateExists`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `rows : List Record` | the consulted manager queryset (`self.remote_field.model.<manager>.using(using)`) | R | `QuerySet` ↔ `List Record`; referenced field value ↔ `key`; default-view exclusion ↔ `hidden` (mapping.md §2). Post-patch, `rows` is the COMPLETE row set (base manager); the spec's `existsMatch` ranges over all of it. |
| A2 | `matchesTarget target r = (r.key == target)` (per-record match, folded by the loop) | `.filter(**{self.remote_field.field_name: value})` | I | the filter matches a row iff its referenced field equals `value` — exactly `r.key == target`. The match predicate is UNCHANGED by the patch; both managers apply the same filter. |
| A3 | `existsMatch target rows` consults EVERY record (hidden or not), via the disjunction folded by the loop | `_base_manager` (post-patch) supplying the complete row set to `.exists()` | I | the changed source op is modeled deeply: `existsMatch`/`matchesTarget` over the full `rows`. The base manager imposes no default view filter, so a hidden (e.g. archived) matching row still makes the test true — `matchesTarget target r` ignores `r.hidden`. No consumed axiom. |
| A4 | result `out = existsMatch target rows`, returned | `qs.exists()` → `if not qs.exists(): raise` (true ⇒ no raise ⇒ validation passes) | R | `exists()` truth ↔ `out`; `validate` raises iff `out = false`. The F2P tests observe validation PASSING for an archived target — i.e. `out = true` because the matching archived row is in the complete set. |

Upstream/downstream ops UNCHANGED by the patch and therefore not behavioral
nodes of `out`: `using = router.db_for_read(...)` (same DB for both managers) and
`.complex_filter(self.get_limit_choices_to())` (same post-filter). They are R
(routing/post-filter shared by both managers); the spec abstracts them away
because the patch leaves them identical. The early guards
(`self.remote_field.parent_link` return, `super().validate`, `value is None`
return) are pre-conditions upstream of the modeled existence test and unchanged.

Discriminating content of the change — a matching record HIDDEN from the
everyday view (archived) is consulted by the complete-collection test — lives in
`matchesTarget target r` ignoring `r.hidden` (= the row counts even if hidden) ⇔
the `_base_manager` source (no default view filter). The pre-patch
`_default_manager` omitted hidden rows; `Solution_prepatch.lean` reproduces that
with `matchesTarget target r && !r.hidden` and **fails**
`out = existsMatch target rows` on any input whose only matching row is hidden
(G-DIFF) — precisely the "archived instance does not exist" bug.

## B. No A (axiom) steps, no kind-3

Every step is R or I. There is no consumed `axiom` and no A-reference deep model
of an outside callee: the modeled behavior is entirely *which rows the existence
test ranges over*, and its two endpoints (default-filtered view vs. complete
view) are abstracted to `hidden` ↦ included-always-vs-only-in-complete-view. The
one operation that genuinely *changed* — the source manager / consulted
collection — is modeled deeply (`existsMatch` over the complete `rows`, with
`hidden` marking default-view exclusion), not hidden behind an axiom about the
function under change. No *changed-op-inexpressible* (kind-3) step.

This is why there is no `axiom_check.py` (no axioms / A-references to validate)
and why G-CONF is skipped (no DB-free R/I shadow of a live manager-queryset
`.exists()` — mapping.md §4): the deeply-modeled content is data flow whose
endpoints are not executable without a live DB. Soundness rests on
G-VERIFY + G-DIFF.

## C. verify(Solution) ⇒ resolved

`validateExists` verifies only if `out = existsMatch target rows` — i.e. the
result is true iff SOME record in the COMPLETE collection matches the target,
regardless of whether that record is hidden from the everyday view. This is
precisely what the F2P tests demand: an archived (hidden) related row whose pk is
referenced must make validation PASS when the form is wired to the complete
record set (`test_validate_foreign_key_to_model_with_overridden_manager`,
`test_FK_validates_using_base_manager`), instead of raising "instance does not
exist."

By the R bijection (mapping.md §2) the verified result corresponds to the patched
existence test: complete row set ⇒ matching archived row found ⇒ `exists()` true
⇒ no `ValidationError`. The prepatch impl (`matchesTarget target r && !r.hidden`)
consults only non-hidden rows — exactly the gold pre-patch `_default_manager`
behavior — and fails the `out = existsMatch target rows` clause (G-DIFF) on any
input whose only match is hidden, which is the observable of the bug. No trust
points beyond the type bijection: there are no axioms, and G-CONF's absence is
justified by the live-DB nature of the existence test (mapping.md §4), carried by
G-VERIFY + G-DIFF as in the django__django-13315 / django__django-13089
precedents.
