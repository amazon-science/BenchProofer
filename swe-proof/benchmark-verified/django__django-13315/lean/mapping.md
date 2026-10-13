# mapping.md — django__django-13315

## Symbol binding (file:line @ base_commit 36bc47069ce071e80c8129500de3b8664d2058a7)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_applyChoiceLimit` / `problem_spec_applyChoiceLimit` | `django.forms.models.apply_limit_choices_to_to_formfield` | `django/forms/models.py:98-103` |
| `Candidate` (pure helper) | one candidate object of `formfield.queryset` together with how many related rows it matches the constraint on | see field table below |

The modeled function is `apply_limit_choices_to_to_formfield`. It is the only
function whose behavior changes and the only one observed by the FAIL_TO_PASS
test (`test_limit_choices_to_no_duplicates`), which asserts that the resulting
queryset (the form field's choices) contains each eligible candidate exactly
once — no duplicates — when the constraint involves a multi-valued relation.

### What the function does (base_commit)

```python
def apply_limit_choices_to_to_formfield(formfield):
    if hasattr(formfield, 'queryset') and hasattr(formfield, 'get_limit_choices_to'):
        limit_choices_to = formfield.get_limit_choices_to()
        if limit_choices_to is not None:
            formfield.queryset = formfield.queryset.complex_filter(limit_choices_to)
```

When the form field carries no `queryset`/`get_limit_choices_to` attribute pair,
or the returned constraint is "absent", the queryset is left untouched.
Otherwise the queryset is filtered by the constraint.

`complex_filter(constraint)` walks the constraint and, when it spans a
multi-valued relation (a join to a related table), the underlying SQL join
emits ONE row per matching related row. A candidate that matches the constraint
through `k ≥ 1` distinct related rows therefore appears `k` times in the
resulting queryset — the duplicate-options defect described in the issue.

The post-fix behavior keeps each matching candidate exactly ONCE: a candidate is
included iff at least one related row satisfies the constraint, regardless of how
many do.

### `Candidate` field ↔ Python expression bijection

The decision for each candidate object reduces to one observation: the number of
related rows that satisfy the constraint when the candidate is joined against it.

| `Candidate` field | Python meaning | notes |
|---|---|---|
| `id` | the candidate object's primary key (`pk`) | identity carrier; lets us observe multiplicity (how many copies of the same candidate the join yields). Modeled as `Nat`. |
| `matchRows` | the number of related rows joined to this candidate that satisfy the constraint | `Nat`. This is the join multiplicity `complex_filter` exposes. `matchRows = 0` ⇒ candidate excluded by the constraint; `matchRows = k ≥ 1` ⇒ candidate satisfies the constraint through `k` related rows. The pre-fix join lists the candidate `k` times; the post-fix `Exists()` lists it once. |

The whole input is `(constraintActive : Bool, base : List Candidate)`:

| Lean input | Python meaning |
|---|---|
| `constraintActive` | truthiness of `limit_choices_to` (`limit_choices_to is not None` pre-fix / `if limit_choices_to:` post-fix — both gate whether the filter is applied at all). `false` ⇒ queryset returned unchanged. |
| `base` | the form field's incoming `queryset`, as the multiset of candidate objects with their per-candidate constraint match-multiplicity. |
| `applicable` | whether the form field exposes the `queryset` + `get_limit_choices_to` attribute pair (`hasattr` guard). `false` ⇒ queryset returned unchanged. |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `formfield.queryset` (an ordered collection of candidate objects, with join multiplicity) | `List Candidate` | each list element ↔ one logical candidate object; `matchRows` ↔ how many related rows the join attaches to it under the constraint. |
| the resulting `formfield.queryset` rows | `List Candidate` | identity on the carrier; the post-fix result lists each eligible candidate once, the pre-fix result lists it `matchRows` times. |
| `limit_choices_to is not None` / `if limit_choices_to:` | `constraintActive : Bool` | the constraint-present gate. |
| `hasattr(...) and hasattr(...)` | `applicable : Bool` | the attribute-pair gate. |

The function returns by mutating `formfield.queryset`; we model it as a pure
function returning the new queryset row-list.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — collapsing a
  join's per-related-row multiplicity to an at-most-once membership — is modeled
  DEEPLY as a list transformation over the candidates' match-multiplicities, not
  axiomatized (SPEC_GUIDE §3: a deeply-modeled changed decision is never
  axiomatized). `complex_filter` / `filter(Exists(...))` are the operations the
  patch swaps; their differing multiplicity semantics ARE the modeled content,
  so there is no opaque callee whose contract the proof consumes.
- **Gate dependency.** Both the pre-fix (`is not None`) and post-fix (`if
  limit_choices_to:`) guards, plus the `hasattr` pair, gate whether any filtering
  happens. When either gate is falsy the queryset is returned unchanged; the
  modeled `constraintActive`/`applicable` booleans capture this exactly. (The
  `is not None` → truthiness change is a separate minor behavior; the
  duplicate-elimination is the F2P-observed fix and the discriminating clause.)
- **Constraint normalization (`Q(**dict)` vs `Q`).** The patch normalizes a dict
  constraint into a `Q` object before anding `Q(pk=OuterRef('pk'))`. This is a
  representation detail of building the same constraint; it does not change which
  candidates match, only how the constraint object is assembled, so it is not
  part of the observable choice-set behavior and is abstracted into
  `constraintActive` + the per-candidate `matchRows`.

## G-CONF fuzz seed

Pinned LCG seed: **13315** (see `conformance_check.py` `SEED`). Corpus:
randomized candidate lists (length 0–8, each candidate's `matchRows` drawn from
`0..4`, ids possibly repeated) crossed with `constraintActive ∈ {True, False}`
and `applicable ∈ {True, False}`, over ≥1e5 fuzzed inputs, diffed against an
in-process replica of the post-patch behavior (each eligible candidate kept
exactly once when the constraint is applied; queryset unchanged otherwise).
