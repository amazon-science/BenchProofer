# refinement.md — django__django-15104

Maps every operation in `implementation_relationAgnosticFields` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: `relationAgnosticFields` (`only_relation_agnostic_fields`)

Post-patch repo code (`patch.diff`):
```python
def only_relation_agnostic_fields(self, fields):
    fields_def = []
    for name, field in sorted(fields.items()):
        deconstruction = self.deep_deconstruct(field)
        if field.remote_field and field.remote_field.model:
            deconstruction[2].pop('to', None)        # gold fix (was: del deconstruction[2]['to'])
        fields_def.append(deconstruction)
    return fields_def
```

Lean impl (`implementation_relationAgnosticFields`): an `Id.run do` accumulator
loop over the visited fields, appending each field's transform in order, then
returning the collected list wrapped in `some` (the function always returns).

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `fields : List FieldDef` (`isRelation`, `decon`) | the loop's iteration sequence `sorted(fields.items())`, each element observed via `field.remote_field … .model` (truthiness) and `deep_deconstruct(field)` (mapping.md bijection) | **R** | `field.remote_field and field.remote_field.model` ↔ `FieldDef.isRelation : Bool`; `deep_deconstruct(field) = (path, args, kwargs)` ↔ `FieldDef.decon : Decon`. Both the relation test and the deconstruction are UNCHANGED, upstream of the changed op, so they are folded into the input representation — neither a consumed axiom nor an A-reference (mapping.md "deep_deconstruct is upstream"). The `sorted(...)` order is modeled as the input list order (R; the sort is upstream of the changed op). |
| 2 | `let mut acc : List Decon := []` | `fields_def = []` | **I** | identical empty-accumulator init. |
| 3 | `for f in fields do …` | `for name, field in sorted(fields.items()): …` | **I** | identical per-field loop; `name` is unused by the changed branch (and by the append), so it is dropped from the model. |
| 4 | `let d := if f.isRelation then removeTarget f.decon else f.decon` | `deconstruction = self.deep_deconstruct(field); if field.remote_field and field.remote_field.model: deconstruction[2].pop('to', None)` | **I** (the changed op, deeply modeled) | **the fixed operation.** Post-patch, a relation field's keyword mapping has its `'to'` entry removed *tolerantly* (`pop('to', None)` is a no-op when absent); a non-relation field is carried over unchanged. `removeTarget` models `pop('to', None)` as `kwargs.filter (key != "to")` — see row 5. The prepatch impl models the pre-patch `del deconstruction[2]['to']` by returning `none` (raise) when the relation field's kwargs lack `'to'`. |
| 5 | `removeTarget d = { d with kwargs := d.kwargs.filter (fun kv => kv.1 != "to") }` | `deconstruction[2].pop('to', None)` | **I** | a `dict` has unique keys, so at most one `'to'` entry exists; `filter (key != "to")` removes exactly that entry, and is a no-op when absent — identical to `pop('to', None)` (mapping.md "kwargs uniqueness"). `deconstruction[0]`/`[1]` (path/args) are untouched (`{ d with kwargs := … }` keeps them — directive 5 frame). |
| 6 | `acc := acc ++ [d]` | `fields_def.append(deconstruction)` | **I** | append the (possibly rewritten) deconstruction; preserves visit order. |
| 7 | `return some acc` | `return fields_def` | **R** | result modeled as `Option (List Decon)`; the post-patch function always returns, so it is always `some`. The `none` value of the carrier exists only to express the pre-patch `KeyError` raise (used by the prepatch impl); it is unreachable in the gold impl. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch `only_relation_agnostic_fields` per-field decision.

## Soundness check (verify ⟹ correct)

- `problem_spec_relationAgnosticFields` pins the result to EXACTLY
  `some (fields.map transformField)` — a single total equation. Every output
  component is grounded in the inputs (directive 8 — no ungrounded oracle: the
  result is *defined as* the elementwise transform of the actual input list, not
  echoed from an answer key) and nothing is left unconstrained (directive 5
  frame: length = input length, order = input order, each related field's path
  and positional args and non-`to` keyword entries carried verbatim, each
  non-relation field carried verbatim). A verifying impl must therefore return,
  in order, the `'to'`-stripped deconstruction of each relation field and the
  verbatim deconstruction of each other field — and must always return (never
  `none`).
- **The discriminating clause is totality.** The spec demands `result = some …`
  for ALL inputs, including a relation field whose keyword mapping records no
  `'to'` entry. The prepatch impl returns `none` on exactly that input (the real
  `KeyError`), so the carried gold proof's final `rw [h]; simp` step faces
  `none = some …` and fails to typecheck (G-DIFF/G-PANEL). This is exactly the
  F2P case `test_add_custom_fk_with_hardcoded_to`: a custom `ForeignKey` whose
  `deconstruct` omits `'to'` — pre-patch the autodetector raised `KeyError: 'to'`
  while detecting renamed models; post-patch it completes and produces the
  migration.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  per-field decision, over a structural edge set (relation/non-relation ×
  target-present/absent × varying kwargs × field-list length 0–3) plus ≥1e5
  fuzzed field lists (0 disagreements), including relation fields whose kwargs
  lack `'to'`.
