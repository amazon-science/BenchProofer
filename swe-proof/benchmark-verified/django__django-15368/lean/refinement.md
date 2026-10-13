# refinement.md — django__django-15368

Maps every operation in `implementation_bulkUpdateBranches` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

The modeled function is the per-field inner loop of `QuerySet.bulk_update`
(`django/db/models/query.py:668-674`). The post-patch loop is:

```python
when_statements = []
for obj in batch_objs:
    attr = getattr(obj, field.attname)
    if not hasattr(attr, 'resolve_expression'):     # <-- the patched line
        attr = Value(attr, output_field=field)
    when_statements.append(When(pk=obj.pk, then=attr))
```

| # | `implementation_bulkUpdateBranches` op | `patch.diff` / post-patch counterpart | tag | notes |
|---|---|---|---|---|
| 1 | `let mut whenStatements : List CaseBranch := []` | `when_statements = []` | I | accumulator init |
| 2 | `for obj in objs do` | `for obj in batch_objs:` | R | a batch object ↔ `(pk, attr) : Nat × AttrValue` (mapping.md bijection) |
| 3 | `let pk := obj.1` | `obj.pk` | R | pk identity ↔ `Nat` |
| 4 | `let attr := obj.2` | `attr = getattr(obj, field.attname)` | R | the read attribute value ↔ `AttrValue` (identity + behavioral kind). The read itself is unchanged by the patch; modeled as a projection of the pre-paired value |
| 5 | `if !resolvesToReference attr.kind then wrapped := true` | `if not hasattr(attr, 'resolve_expression'): attr = Value(attr, output_field=field)` | R | **the changed decision, modeled DEEPLY.** `hasattr(attr,'resolve_expression')` ↔ `resolvesToReference attr.kind` (true for `directExpression`/`fieldReference`, false for `plainValue`). The literal-wrap (`Value(...)`) is modeled as the boolean `wrapped` flag on the branch; the underlying value identity is preserved either way (`Value` stores its argument verbatim — unchanged behavior, not modeled internally) |
| 6 | `whenStatements := whenStatements ++ [⟨pk, wrapped, attr.ident⟩]` | `when_statements.append(When(pk=obj.pk, then=attr_or_wrapped))` | R | one `When` branch ↔ one `CaseBranch`; `then` carries the (possibly wrapped) value whose identity is `attr.ident` |
| 7 | `return whenStatements` | the assembled `when_statements` (consumed by `Case(*when_statements, …)`) | I | the produced branch list, in object order |

## No axioms

- **No A-consumed rows.** The behavior the patch changes — whether a value is
  wrapped as a literal — is modeled DEEPLY by `resolvesToReference` over the
  value's behavioral kind `ValueKind` (SPEC_GUIDE §3: a deeply-modeled changed
  decision is never axiomatized). No external callee property is consumed by the
  proof, so the `axioms` region is empty and **G-AX skips**.
- **No A-reference rows.** Nothing in the impl delegates to an opaque callee whose
  real behavior the spec needs validated. `getattr`, `Value`, `When`, `Case`,
  `Cast`, the batching and transaction machinery are all either unchanged or not
  observed by the modeled decision (mapping.md "Callee provenance").

## Bug visibility (G-DIFF)

The pre-patch decision is the narrow `isinstance(attr, Expression)` test, modeled
as `attr.kind = directExpression` (an `Expression` instance) — which EXCLUDES
`fieldReference` (the `F('…')` case, an instance of `Combinable`, not
`Expression`). `Solution_prepatch.lean` carries this buggy decision (`if attr.kind
!= ValueKind.directExpression then wrapped := true`) together with the carried-over
gold proof; on a `fieldReference` input the buggy impl sets `wrapped = true` where
the spec demands `wrapped = !resolvesToReference fieldReference = false`, so the
proof's `rfl` bridge no longer holds and verification FAILS — exactly the
discriminating behavior of the FAIL_TO_PASS test `test_f_expression` (a plain
`F('note')` must resolve to the column, not be stored as the literal `'F(note)'`).

## Conformance (G-CONF)

The impl region is genuine R/I content (the wrapping decision + branch assembly),
so `conf_skip = false`. `conformance_check.py` builds the R/I shadow (wrap iff
`kind = plainValue`) and differential-tests it against an in-process replica of the
POST-PATCH loop (`hasattr(attr,'resolve_expression')` ⇒ no wrap) over ≥1e5 fuzzed
batches, with the `fieldReference` case well-represented.
