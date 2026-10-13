# refinement.md — django__django-12858

Maps every operation in `implementation_orderingFieldCheck` to its `patch.diff`
counterpart in `Model._check_ordering` (django/db/models/base.py, changed line
:1747). Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** op left as the real repo callee in G-CONF (not axiomatized),
**I** identical concrete op.

## Patch (post-patch report condition)
```python
except (FieldDoesNotExist, AttributeError):
    if fld is None or (
        fld.get_transform(part) is None and fld.get_lookup(part) is None
    ):                                   # was: fld is None or fld.get_transform(part) is None
        errors.append(checks.Error("'ordering' refers to the nonexistent "
            "field, related field, or lookup '%s'." % field, ..., id='models.E015'))
```

The single changed expression is the report condition for an UNRESOLVED segment:
`fld is None or get_transform(part) is None` becomes
`fld is None or (get_transform(part) is None and get_lookup(part) is None)`.
A segment that is a registered lookup (not a transform) of the preceding field
is therefore no longer reported.

## Modeling decision
The fixed behavior is the per-entry E015-report decision of the relation-field
walk. The model walks the entry's segments (`parts : List String`) from the
originating model (`start`), threading:

- `fld : Option Field` — the last successfully resolved field (`none` until the
  first segment resolves), mirroring Python's `fld` (initialized to `None`);
- `ctx : Option Model` — the current model context (`some start` initially;
  `some (descend f)` after a relation field; `none` after a non-relation field
  or once exhausted), mirroring `_cls` and the `_cls = None`/`AttributeError`
  exhaustion path.

For each segment:
- if the context resolves the segment to a field `f` (`getField m part = some
  f`), set `fld := some f` and `ctx := if isRelation f then some (descend f)
  else none` — the `try` block's success path;
- otherwise (the segment is unresolved: `getField m part = none`, or the context
  is exhausted `ctx = none`) — the `except` branch — report iff `reportSegment`,
  which is `fld = none → report; some f → ¬hasTransform f part ∧ ¬hasLookup f
  part`. This is the POST-PATCH condition.

The entry is reported iff any segment is reported (`errors.append` is reached at
least once for this `field`; the spec/impl return that disjunction).

The machinery (`getField`, `isRelation`, `descend`, `hasTransform`, `hasLookup`)
is universally quantified, so the only thing pinned is the walk + report
structure — exactly what the patch changed.

## Operation correspondence
| # | Lean op (`implementation_orderingFieldCheck`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut fld := none; let mut ctx := some start; let mut err := false` | `fld = None`, `_cls = cls`, the per-entry `errors` accumulation | I | walk state init; `err` accumulates the entry's report flag. |
| 2 | `for part in parts do` | `for part in field.split(LOOKUP_SEP):` | R | `parts : List String` ↔ the split segments. |
| 3 | `match ctx with \| some m => match getField m part with \| some f => fld := some f; ctx := if isRelation f then some (descend f) else none` | the `try` block: `fld = _cls._meta.get_field(part)` (or `pk`); `if fld.is_relation: _cls = fld.get_path_info()[-1].to_opts.model else: _cls = None` | R + A-reference | resolved-segment success path; `getField`/`isRelation`/`descend` are the unchanged real machinery, left abstract and bound to the real model in G-CONF. |
| 4 | `\| none => if reportSegment hasTransform hasLookup fld part then err := true` (and the `ctx = none` branch) | the `except (FieldDoesNotExist, AttributeError):` branch with the POST-PATCH condition `fld is None or (get_transform(part) is None and get_lookup(part) is None)` | R + A-reference | **the changed op.** `reportSegment` encodes the post-patch condition: report unless the segment is a transform OR a registered lookup of `fld`. `hasTransform`/`hasLookup` are the unchanged real callees. |
| 5 | `return err` | whether `errors` gained an E015 entry for this `field` | I | the per-entry report decision. |

The behavior-changing op is #4: pre-patch `reportSegment` omitted the
`hasLookup` disjunct (a lookup-only segment was reported); post-patch it spares a
registered-lookup segment. The prepatch impl encodes the pre-patch condition
(`report = fld = none ∨ ¬hasTransform f part`), so on a lookup-only segment it
reports `true` while the spec forces `false`.

## R/I legs ⇒ G-CONF
Ops 1–5 are all R/I structure (the walk + report disjunction), with
`getField`/`isRelation`/`descend`/`hasTransform`/`hasLookup` as A-references left
as the REAL model machinery. G-CONF does NOT substitute axiom models for the
machinery; it builds a synthetic model graph, binds the five parameters to the
real field/option machinery, and differential-tests the shadow against the REAL
patched `_check_ordering` walk over ≥10^5 fuzzed entries. `conf_skip = false`:
the impl region's R/I content (the walk + the post-patch report condition) is
exactly the fixed behavior.

## No A-consumed row
The proof consumes no property of any machinery parameter (all universally
quantified), so `meta.json axioms = []`. There is no `opaque`/`axiom`
declaration in `Solution.lean`; `axiom_check.py` is a skip stub. The five
parameters are A-references documenting the G-CONF binding only.

## F2P alignment
- `test_ordering_pointing_to_lookup_not_transform`: a model with
  `ordering = ('test__isnull',)`, where `test` is a `CharField`. `test` resolves
  to a non-relation field, exhausting the context; `isnull` is unresolved as a
  field but IS a registered lookup of `CharField` (and is NOT a transform). The
  spec pins `result = false` (no E015) — the post-patch behavior. The prepatch
  impl (transform-only condition) returns `result = true` (E015), so it cannot
  satisfy the discriminating clause. This is the FAIL_TO_PASS test.
- The PASS_TO_PASS ordering tests (`test_ordering_allows_registered_lookups`,
  `test_ordering_pointing_to_*`) continue to hold: a transform-or-lookup segment
  is spared, a genuinely nonexistent segment (neither transform nor lookup, or no
  preceding field) is still reported.
`patch.diff` (gold verbatim) makes the harness resolve.
