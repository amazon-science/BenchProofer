# refinement.md — django__django-13346

The operation-by-operation correspondence between `model.py`'s implementation
(the `process_membership_rhs` impl region and the deep `slots_sql` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real operation by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The membership-lookup right-hand side — new `KeyTransformIn.process_rhs`

Gold hunk (`django/db/models/fields/json.py`): a new lookup `KeyTransformIn`
subclassing `lookups.In`, registered on `KeyTransform`, overriding
`process_rhs` so that on a non-native-JSON backend each value slot of the
comparison string is wrapped in the document-scalar extraction:

```python
class KeyTransformIn(lookups.In):
    def process_rhs(self, compiler, connection):
        rhs, rhs_params = super().process_rhs(compiler, connection)
        if not connection.features.has_native_json_field:
            func = ()
            ...
            elif connection.vendor in {'sqlite', 'mysql'}:
                func = ("JSON_EXTRACT(%s, '$')",) * len(rhs_params)
            rhs = rhs % func
        return rhs, rhs_params

KeyTransform.register_lookup(KeyTransformIn)
```

| # | model.py impl op (`process_membership_rhs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `num_values: int` (`>= 1`) | `len(rhs_params)`, the count of right-hand-side values returned by `super().process_rhs` | R | the value count is the carrier; the membership set is non-empty when comparison-string production is reached (`In.process_rhs` raises `EmptyResultSet` for empty rhs), giving `num_values >= 1` (mapping.md §2). |
| A2 | (no node — the base placeholder structure) | `rhs, rhs_params = super().process_rhs(...)` producing `'(' + ', '.join(['%s']*n) + ')'` | R | the unchanged base-class placeholder structure (parens + comma joins) is the type-refinement boundary; the fix changes only the per-slot content, so the model omits the identical parens and reproduces only the inner per-slot expansion (mapping.md §2, §3.1). |
| A3 | the result is `slots_sql(num_values)`, i.e. each of the `num_values` slots is the wrapped form `JSON_EXTRACT(%s, '$')`, `', '`-joined, computed by the backward fold over the slots | `rhs % func` with `func = ("JSON_EXTRACT(%s, '$')",) * len(rhs_params)` (the `sqlite`/`mysql` branch) | A-reference | the changed string operation is modeled **deeply**: `slots_sql` (the spelled-out per-slot fold in the `pure` region) and the verified loop in `process_membership_rhs` ARE the substitution. There is no consumed `process_rhs` axiom — the proof never depends on one. The deep model is validated **== the real operation** out-of-band: G-AX (axiom_check.py) reproduces `rhs % func` exactly and asserts `slots_sql(n) ==` its inner expansion on boundary (incl. the single-element case) + 5000 fuzz counts (mapping.md §3.1). The model loop and the real `%`-substitution compute the same string. |
| A4 | `result` returned (a `List[int]`) | the wrapped `rhs` string returned from `process_rhs` (with `rhs_params` unchanged) | R | `str` ↔ `List[int]` code points (mapping.md §2); the bind parameters pass through unchanged on this branch and are not part of the modeled output. |

The discriminating content of the change — every value slot must be
`JSON_EXTRACT(%s, '$')` rather than the bare `%s` — lives in
`slots_sql`'s use of `wrapped_slot()` (model) ⇔ the `func = ("JSON_EXTRACT(%s,
'$')",) * len(rhs_params); rhs = rhs % func` step of `KeyTransformIn.process_rhs`
(real). Pre-patch there is **no** `KeyTransformIn`, so the inherited
`In.process_rhs` returns the bare `'(' + ', '.join(['%s']*n) + ')'` placeholder;
`model_prepatch.py` reproduces that (`bare_slot()` content `[37, 115]` per slot)
and **fails** the postcondition `ToSeq(Result()) == slots_sql(num_values)`,
which is exactly the spec sensing the change (G-DIFF). The single-element case
(`num_values == 1`) — the case the issue is specifically about — is included:
the prepatch's one bare `%s` ≠ the required one `JSON_EXTRACT(%s, '$')`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the per-slot wrapping of the membership comparison string — is
modeled **deeply** (the spelled-out per-slot fold `slots_sql` consumed in
`process_membership_rhs`, step A3, an **A-reference**), not hidden behind an
axiom about the function under change: there is **no consumed axiom** in this
bundle. The only opaque thing the new code calls is `super().process_rhs`
(the unchanged base-class placeholder producer), which is an **R**-refinement
boundary (A2), not an axiom — its parenthesised comma-joined structure is
identical pre- and post-fix and carries none of the discriminating content.

## C. verify(model) ⇒ resolved

`process_membership_rhs` verifies only if its output equals the exact
per-slot expansion with **every** slot wrapped as `JSON_EXTRACT(%s, '$')` (A3).
By R (str ↔ List[int]; the unchanged parenthesised base placeholder; the
unchanged bind parameters) the verified comparison string equals
`rhs % (("JSON_EXTRACT(%s, '$')",) * n)` on the tested SQLite path; by G-AX the
deep model `slots_sql` equals that real `%`-substitution (A-reference) on the
single-element case and fuzz. Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The single trust point here is PLAN §1.1's refinement
fidelity (this document, G-EQ) plus the A-reference soundness check (G-AX);
there is no consumed axiom to trust.
