# mapping.md — django__django-15368

## Symbol binding (file:line @ base_commit e972620ada4f9ed7bc57f28e133e85c85b0a7b20)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_bulkUpdateBranches` / `problem_spec_bulkUpdateBranches` | the per-field inner loop of `QuerySet.bulk_update` that builds the conditional update branches | `django/db/models/query.py:668-674` |
| `CaseBranch` (pure structure) | one `When(pk=obj.pk, then=attr)` conditional branch | `django/db/models/query.py:674` |
| `AttrValue` (pure structure) | the per-object attribute value `attr = getattr(obj, field.attname)` | `django/db/models/query.py:671` |
| `ValueKind` (`plainValue` / `directExpression` / `fieldReference`) | the runtime category of `attr` w.r.t. resolving to a query reference | see classification below |
| `resolvesToReference` (pure helper) | the post-patch discriminator `hasattr(attr, 'resolve_expression')` | `django/db/models/query.py:672` (post-patch) |
| `CaseBranch.wrapped` | whether `attr` was replaced by `Value(attr, output_field=field)` | `django/db/models/query.py:673` |
| `CaseBranch.pk` | `obj.pk` carried into `When(pk=obj.pk, …)` | `django/db/models/query.py:674` |

The modeled function is the loop body of `QuerySet.bulk_update` (`query.py:668-674`),
the only place whose behavior the patch changes and the locus observed by the
FAIL_TO_PASS test `test_f_expression`.

### What the code does (base_commit)

```python
when_statements = []
for obj in batch_objs:
    attr = getattr(obj, field.attname)
    if not isinstance(attr, Expression):          # <-- the changed line (too narrow)
        attr = Value(attr, output_field=field)
    when_statements.append(When(pk=obj.pk, then=attr))
case_statement = Case(*when_statements, output_field=field)
```

Step by step, per object in the batch (for one field):
1. read the attribute value `attr = getattr(obj, field.attname)`;
2. decide whether `attr` is an already-resolvable query expression; if NOT,
   replace it with `Value(attr, output_field=field)` — a wrapper that stores the
   value verbatim (its string repr);
3. append `When(pk=obj.pk, then=attr)` (the possibly-wrapped value).

The CASE/WHEN expression assembled from these branches becomes the per-row
`SET col = CASE WHEN pk=… THEN <then> …` of the UPDATE.

### The bug and the fix

`attr` can be (a) a plain Python value (str/int/…), (b) an `Expression` instance,
or (c) a field reference such as `F('name')`. Plain values must be wrapped in
`Value(...)` so they are stored verbatim; expression-like values (b and c) must be
passed through unwrapped so the database resolves them (e.g. `F('name')` resolves
to the `name` column).

At base_commit the discriminator is `isinstance(attr, Expression)`. But `F`
subclasses `Combinable`, **not** `Expression` (django/db/models/expressions.py:582
`class F(Combinable)` vs :394 `class Expression(BaseExpression, Combinable)`),
while still defining `resolve_expression` (:595). So a plain `F('name')` fails the
`isinstance` check, gets wrapped in `Value`, and is stored as the literal string
`'F(name)'` instead of resolving to the referenced column — exactly the reported
defect.

The fix replaces the type test with the duck-typed `hasattr(attr, 'resolve_expression')`,
which is true for every resolvable expression (`Expression` and `F` alike) and
false for plain values, so field references are no longer wrapped.

### Lean modeling

- A batch is modeled as `objs : List (Nat × AttrValue)`: each entry is `(pk, attr)`
  where `pk : Nat` is `obj.pk` and `attr : AttrValue` is the per-object value.
- `AttrValue` carries `ident : Nat` (an opaque identity of the underlying value —
  only equality / pass-through is observed) and `kind : ValueKind`.
- `ValueKind` is the runtime category that governs wrapping:
  * `plainValue` — a plain value (str/int/…); NOT resolvable ⇒ must be wrapped;
  * `directExpression` — an `Expression` instance; resolvable ⇒ passed through;
  * `fieldReference` — a field reference (`F('…')`); resolvable but **not** an
    `Expression` instance ⇒ the discriminating case.
- `resolvesToReference kind` is the post-patch discriminator: `false` for
  `plainValue`, `true` for `directExpression` and `fieldReference` (i.e. anything
  that resolves to a query reference). The pre-patch narrow check is
  `kind = directExpression`, which wrongly excludes `fieldReference`.
- The produced branch `CaseBranch` records `pk` (carried through unchanged),
  `wrapped` (whether the stored value was replaced by a `Value` literal wrapper),
  and `valueIdent` (the identity of the underlying value, preserved by both the
  wrapped and pass-through branches).

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| one batch of `(obj, attr)` for a single field | `objs : List (Nat × AttrValue)` | `obj.pk ↔ .1`; `attr ↔ .2` |
| `obj.pk` | `Nat` (first component) | distinct pk ↔ distinct `Nat` |
| `attr = getattr(obj, field.attname)` | `AttrValue` | identity of `attr` ↔ `ident`; runtime category ↔ `kind` |
| plain value / `Expression` instance / `F(...)` | `ValueKind.plainValue` / `.directExpression` / `.fieldReference` | `isinstance(attr, Expression)` ↔ `kind = directExpression`; `hasattr(attr,'resolve_expression')` ↔ `kind ≠ plainValue` |
| `When(pk=obj.pk, then=attr_or_wrapped)` | `CaseBranch ⟨pk, wrapped, valueIdent⟩` | one When ↔ one branch; `then` wrapped in `Value` ↔ `wrapped = true` |
| `attr = Value(attr, output_field=field)` taken | `wrapped = true` | the literal-wrap branch |

The result of the modeled loop is the list of `When` branches `when_statements`,
in object order; modeled as `result : List CaseBranch`.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — the wrapping
  decision — is modeled DEEPLY by `resolvesToReference` over the value's runtime
  category `ValueKind` (SPEC_GUIDE §3: a deeply-modeled changed decision is never
  axiomatized). The branch assembly (`When(pk, then)`) is modeled deeply by
  `CaseBranch`. No property of an external callee is consumed by the proof, so the
  `axioms` region is empty and **G-AX skips**.
- `getattr(obj, field.attname)` is the attribute read; modeled as projecting the
  `AttrValue` already paired with the pk. Not a behavioral callee.
- `Value(attr, output_field=field)` is the literal wrapper; the patch does not
  change it. Whether it is applied is the modeled decision (`wrapped`); its
  internal behavior (storing the verbatim value) is not modeled because it is
  unchanged and the fix turns only on *whether* it is applied.
- `When` / `Case` / `Cast` constructors and the surrounding batching, transaction,
  and `.update()` calls (`query.py:675-684`) are unchanged by the patch and do not
  bear on the wrapping decision; they are not modeled (model only the touched
  behavior; SPEC_GUIDE §3). Their omission constrains no output component the spec
  leaves free — the spec pins every produced branch (pk, wrapped flag, value
  identity) for every input.

## G-CONF fuzz seed

Pinned LCG seed: **15368** (see `conformance_check.py` `SEED`). Corpus: randomized
batches of 0–8 objects, each object's `attr` drawn uniformly from the three
categories — a plain literal, a genuine `Expression` instance, and an `F(...)`
field reference (so the discriminating `fieldRef` case is well-represented) — with
distinct pk values, over ≥1e5 fuzzed inputs. The R/I shadow of
`implementation_bulkUpdateBranches` (wrap iff `kind = literal`) is diffed against
an in-process replica of the POST-PATCH loop (`hasattr(attr,'resolve_expression')`
⇒ no wrap). Hand-picked edge case pins the discriminating clause: an `F(...)`
attribute must yield `wrapped = false`.
