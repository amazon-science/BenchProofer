# refinement.md — django__django-13109

The operation-by-operation correspondence between `model.py`'s implementation
(the `validate_reference` impl region, the deep `present` membership model, and
the live `choice_permitted` axiom) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The reference-check site — `validate()` (`related.py:917`)

Gold hunk:
```
- qs = self.remote_field.model._default_manager.using(using).filter(
+ qs = self.remote_field.model._base_manager.using(using).filter(
      **{self.remote_field.field_name: value}
  )
  qs = qs.complex_filter(self.get_limit_choices_to())
  if not qs.exists():
      raise exceptions.ValidationError(... 'invalid' ...)
```

| # | model.py impl op (`validate_reference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: int` | `value` (the candidate reference) | R | the ORM compares `field_name == value` for equality; modelling the key as `int` is exact (mapping.md §2). |
| A2 | parameter `complete_rows: List[int]` | `self.remote_field.model._base_manager.using(using)` queryset | R | a queryset of related rows ↔ the `List[int]` of those rows' referenced-field keys; `_base_manager` is the unfiltered manager returning every stored row (mapping.md §2, §3.2). This is the POST-patch source. |
| A3 | parameter `curated_rows: List[int]` | `self.remote_field.model._default_manager.using(using)` queryset (pre-patch source) | R | the default manager's queryset ↔ its key list, a SUBSET of `complete_rows`. Present in the signature so the prepatch can consult it; the post-patch impl ignores it (mapping.md §3.2). |
| A4 | the backward scan computing `found == present(value, complete_rows)` | `.filter(**{field_name: value})` then `qs.exists()` on the base-manager queryset | R + I | `.filter(field_name=value).exists()` ↔ `value` ∈ the key list ↔ `present(value, complete_rows)`, modelled DEEPLY as the per-element membership fold over the COMPLETE collection. The membership operation is unchanged; only WHICH collection it runs over changed (base vs default), captured by passing `complete_rows`. |
| A5 | `choice_permitted(value)` conjoined into the no-raise condition | `qs.complex_filter(self.get_limit_choices_to())` narrowing | A-consumed | the unchanged `limit_choices_to` restriction; the proof consumes its determinism as the second conjunct of `reference_holds`. Same callee both pre- and post-patch (mapping.md §3.1). |
| A6 | `if not (found and choice_permitted(value)): raise ReferenceInvalid()` else return | `if not qs.exists(): raise exceptions.ValidationError(...)` | R + I | the raise/no-raise decision: raise iff no matching, choice-permitted row exists. `ValidationError` ↔ `ReferenceInvalid` (builtin-exception `Exsures` banned; mapping.md §2). The F2P tests observe only the raise/no-raise outcome (`is_valid()` / `full_clean()`), not the message. |
| A7 | `Requires(MustTerminate(2))` on `validate_reference`; loop `Invariant(MustTerminate(i + 1))` in the scan | the real `validate()` reference check is one bounded queryset probe (`.filter(...).exists()`) that always returns to its caller | R | total-correctness obligation: the real operation always ANSWERS (returns or raises). Nagini verifies partial correctness by default, so without the obligation a diverging same-spec impl (bare self-recursion, or an endless loop) satisfies every `Ensures`/`Exsures` vacuously — the audited G-PANEL-1 counterexample (`atk_recurse_reject.py`). Measure 2 lets the impl invoke the `@Pure` helpers but forbids re-invoking `validate_reference` itself; the scan loop consumes the obligation with the strictly decreasing, bounded-below measure `i + 1`. |

The discriminating content of the change — consulting the COMPLETE collection
(`_base_manager`) instead of the curated default collection (`_default_manager`)
— lives in step A2/A4: the post-patch impl scans `complete_rows`, the spec's
`Ensures(reference_holds(value, ToSeq(complete_rows)))` / `Exsures(...
not reference_holds(value, ToSeq(complete_rows)))` decide over `complete_rows`.
`model_prepatch.py` reproduces the bug (scans `curated_rows`) and **fails** the
`Exsures` clause `(not reference_holds(value, ToSeq(complete_rows)))`: a `value`
present in `complete_rows` but hidden from `curated_rows` (and choice-permitted)
makes the buggy impl raise while the spec demands it return — exactly the spec
sensing the change (G-DIFF). This mirrors the F2P tests
(`test_FK_validates_using_base_manager`,
`test_validate_foreign_key_to_model_with_overridden_manager`): an archived row,
hidden by the default manager but present in the base manager, must validate.

## B. The membership operation is modeled deeply, not axiomatized

The `.filter(...).exists()` membership test (step A4) is the unchanged ORM
primitive whose only *change* is the queryset it runs over. It is modeled
DEEPLY as the front-recursive `present` fold + the matching backward loop — not
behind an axiom — because integer-set membership is fully expressible in
Nagini's fragment. There is therefore no consumed "exists" axiom; the only
consumed axiom is `choice_permitted` (A-consumed, the unchanged
`limit_choices_to` callee, step A5).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — which manager's row collection the check consults — is modelled
DEEPLY (membership of `value` over `complete_rows` rather than `curated_rows`),
not hidden behind an axiom about the function under change. The manager
subset relationship (`curated_rows ⊆ complete_rows`) is validated against the
real Django managers by axiom_check.py (G-AX, mapping.md §3.2), establishing
that the witness class the prepatch fails on (present in base, hidden by
default) is realizable.

## D. verify(model) ⇒ resolved

`validate_reference` verifies only if it returns normally exactly when the
COMPLETE collection holds the referenced, choice-permitted key (A2/A4/A6) and
raises otherwise. By R (queryset ↔ key list, `ValidationError` ↔
`ReferenceInvalid`, `value:int` exact) the verified check equals the gold
patch's `_base_manager...exists()` decision on the tested inputs; by A-consumed
the `choice_permitted` conjunct equals the unchanged `complex_filter` narrowing
(G-AX); the deep membership model equals `.filter().exists()` on the chosen
queryset (mapping.md §2). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and one audited callee — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX, `choice_permitted` + the manager subset
relationship) and refinement fidelity (this document, G-EQ).
