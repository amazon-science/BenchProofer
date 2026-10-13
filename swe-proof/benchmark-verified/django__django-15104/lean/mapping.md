# mapping.md — django__django-15104

## Symbol binding (file:line @ base_commit a7e7043c87)
Modeled function: the per-field loop body of
`MigrationAutodetector.only_relation_agnostic_fields(self, fields)`,
`django/db/migrations/autodetector.py:89-101`.

```python
def only_relation_agnostic_fields(self, fields):
    fields_def = []
    for name, field in sorted(fields.items()):
        deconstruction = self.deep_deconstruct(field)      # -> (path, args, kwargs)
        if field.remote_field and field.remote_field.model:
            del deconstruction[2]['to']                    # gold: .pop('to', None)
        fields_def.append(deconstruction)
    return fields_def
```

The gold patch changes the relation-field branch from `del deconstruction[2]['to']`
to `deconstruction[2].pop('to', None)`: removing the target-model key from a
relation field's deconstructed keyword mapping must tolerate the key already
being absent (the real `del` raises `KeyError`; `pop(..., None)` does not).

Lean modeled function name: `relationAgnosticFields` — names the *behavior*
("normalize each field's deconstruction so the related target is ignored"); the
public `problem_statement` already names `only_relation_agnostic_fields`,
`deep_deconstruct`, `deconstruction`, `remote_field`, and the `'to'` key.

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `fields : List FieldDef` | the loop's iteration sequence `sorted(fields.items())`, one element per `(name, field)`; observed through the two components the loop reads (autodetector.py:96-100) |
| `FieldDef.isRelation` | the branch guard `field.remote_field and field.remote_field.model` truthiness (autodetector.py:98) |
| `FieldDef.decon` | `deconstruction = self.deep_deconstruct(field)` — the 3-tuple `(path, args, kwargs)` (autodetector.py:97, `deep_deconstruct` at autodetector.py:46-87) |
| `Decon.path` | `deconstruction[0]` (the import path; carried verbatim) |
| `Decon.args` | `deconstruction[1]` (positional args; carried verbatim) |
| `Decon.kwargs` | `deconstruction[2]` (the keyword mapping; the only component rewritten) — modeled as an association list of `(key, valueRepr)` |
| `removeTo d` | `del d.kwargs['to']` / `d.kwargs.pop('to', None)` — drop the `'to'` entry from the keyword mapping (autodetector.py:99) |
| result `Option (List Decon)` | the returned `fields_def` list; `some L` = the function returned `L`; `none` = the function raised (the `KeyError` the real `del` produces when `'to'` is absent) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| iteration sequence `sorted(fields.items())` | `fields : List FieldDef` (loop order; the sort is upstream of the changed op — see note) |
| `field.remote_field and field.remote_field.model` (truthy/falsy) | `FieldDef.isRelation : Bool` |
| `deep_deconstruct(field)` = `(path, args, kwargs)` | `FieldDef.decon : Decon` with `path : String`, `args : List String`, `kwargs : List (String × String)` |
| `deconstruction[2]` (a `dict[str, Any]`, unique keys) | `Decon.kwargs : List (String × String)` (key→value-repr assoc list, unique keys) |
| `d.pop('to', None)` (post-patch) | `removeTo d = { d with kwargs := d.kwargs.filter (fun kv => kv.1 != "to") }` |
| `del d['to']` (pre-patch; raises if absent) | prepatch impl: `return none` when no `'to'` key present, else the filter |
| returned `fields_def : list` | `some (fields.map transformField) : Option (List Decon)` |
| function raises `KeyError` | `none` |

### Modeling notes
- **deep_deconstruct is upstream, not consumed.** `deep_deconstruct(field)` is an
  UNCHANGED callee whose *result* (the `(path, args, kwargs)` tuple) is the input
  the changed branch reads. We fold it into the input representation
  (`FieldDef.decon`) rather than re-deriving it, so it is neither an A-consumed
  axiom nor an A-reference; no `opaque`/`axiom` callee contract is required.
  Likewise `field.remote_field … .model` is folded into `FieldDef.isRelation`.
- **The sort is upstream of the changed op.** `sorted(fields.items())` only fixes
  the order in which fields are visited; the loop appends the transform of each
  visited field in that order, so output order = visit order. We model the input
  AS the post-sort visit sequence (`fields : List FieldDef`); the bijection on the
  preceding `dict → sorted-items` step is a pure R refinement and does not touch
  the modeled (changed) behavior.
- **kwargs uniqueness.** A real `dict` has unique keys, so at most one `'to'`
  entry exists. `filter (key != "to")` removes that single entry exactly as
  `pop('to', None)` does; on absence it is a no-op, matching `pop`'s default.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** The modeled computation is
  exactly: for each visited field, if it is a relation field, drop the `'to'`
  keyword entry; append the (possibly rewritten) deconstruction. Removal is
  modeled deeply as an association-list filter; the relation test and the
  deconstruction are folded into the input. ⇒ `axioms = []`,
  `deep_model_references = []`, `axiom_check.py` is a skip stub (G-AX skips).
- No flag dependency.

## G-LEAK
The solver-visible `problem_statement` publicly names `only_relation_agnostic_fields`,
`deep_deconstruct`, `deconstruction`, `remote_field`, the `'to'` key, and even
quotes both the old (`del deconstruction[2]['to']`) and suggested
(`deconstruction[2].pop('to', None)`) lines. The spec view nonetheless avoids
reproducing any gold-diff line verbatim, names no patched file path, embeds no
narration word, and describes the abstract per-field normalization behavior only.
The sole `def`/`class` symbol on the gold hunk header
(`only_relation_agnostic_fields`) is public in the problem statement, so even an
identifier echoing it would pass; the Lean names stay abstract regardless.

## Pinned G-CONF fuzz seed
`15104`.
