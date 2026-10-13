# refinement.md — django__django-15561

Maps every operation in `implementation_requiresColumnChange` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: `requiresColumnChange` (`_field_should_be_altered`)

Post-patch repo code (`patch.diff`):
```python
def _field_should_be_altered(self, old_field, new_field):
    _, old_path, old_args, old_kwargs = old_field.deconstruct()
    _, new_path, new_args, new_kwargs = new_field.deconstruct()
    for attr in old_field.non_db_attrs:
        old_kwargs.pop(attr, None)
    for attr in new_field.non_db_attrs:
        new_kwargs.pop(attr, None)
    return self.quote_name(old_field.column) != self.quote_name(
        new_field.column
    ) or (old_path, old_args, old_kwargs) != (new_path, new_args, new_kwargs)
```
`Field.non_db_attrs` (added by the patch) is the tuple
`("blank", "choices", "db_column", "editable", "error_messages", "help_text",
"limit_choices_to", "on_delete", "related_name", "related_query_name",
"validators", "verbose_name")`.

Lean impl (`implementation_requiresColumnChange`): a Bool-valued decision with
the same structure — pop the ignored attributes from both kwargs lists, then OR
the quoted-column-name inequality with the structural inequality of the
`(path, args, kwargs)` triples.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `old new : FieldDesc` (`column`, `path`, `args`, `kwargs`) | the two `Field` arguments, observed through `.column` and `deconstruct()` → `(path, args, kwargs)` (mapping.md bijection) | **R** | `deconstruct()`'s leading name slot is never read and is dropped; `path`↔`str`, `args`↔`list`, `kwargs`↔`dict` modeled as assoc-`List` (same-class deconstruct ⇒ identical key order ⇒ list-eq = dict-eq; see mapping.md). |
| 2 | `for attr in [..."choices"...] do oldKwargs := oldKwargs.filter (·.1 != attr)` | `for attr in old_field.non_db_attrs: old_kwargs.pop(attr, None)` | **I** (the changed op, deeply modeled) | **the fixed operation.** The patch makes the popped set `Field.non_db_attrs`, which now INCLUDES `"choices"`. The Lean ignored-attr list carries `"choices"`, matching post-patch exactly. The prepatch impl's list OMITS `"choices"` (pre-patch hard-coded `non_database_attrs`). Popping by name iteration ↔ `filter` removing those names. |
| 3 | `for attr in [..."choices"...] do newKwargs := newKwargs.filter (·.1 != attr)` | `for attr in new_field.non_db_attrs: new_kwargs.pop(attr, None)` | **I** | same as #2 for the new field. (The patch pops the new side in its own loop; pre-patch popped both inside one loop — behaviorally identical, both sides get the same set removed.) |
| 4 | `quoteIdentifier old.column != quoteIdentifier new.column` | `self.quote_name(old_field.column) != self.quote_name(new_field.column)` | **A-reference** | `quote_name` is an UNCHANGED callee, `opaque quoteIdentifier`. Applied identically on both sides of `!=` in spec AND impl, so NO property is consumed (it cancels syntactically) — an A-reference, not a consumed axiom. G-AX skips (no `_prop`); G-CONF replicates the real SQLite quoting in both oracle and shadow. |
| 5 | `decide ((old.path, old.args, oldKwargs) ≠ (new.path, new.args, newKwargs))` | `(old_path, old_args, old_kwargs) != (new_path, new_args, new_kwargs)` | **I** | identical structural tuple inequality. `!=` on `(str, list, dict)` ↔ `≠` on `(String, List String, List (String×String))` (`decide` reflects the `DecidableEq`). |
| 6 | `… || …` returning `Bool` via `Id.run do` | `… or …` returning a Python bool | **R** | result modeled as `Bool`; the boolean disjunction is identical. |

All impl-region ops are **R / I / A-reference** — there is NO A-consumed (axiom)
content, so the impl is NOT all-A-tagged: `conf_skip = false`, and
`conformance_check.py` mechanically differential-tests the R/I shadow against an
in-process replica of the post-patch `_field_should_be_altered` decision.

## Soundness check (verify ⟹ correct)

- `problem_spec_requiresColumnChange` pins `result` to the FULL boolean
  expression over both inputs (directive 5 frame — `result` is completely
  determined, nothing left unconstrained; directive 8 — grounded in
  `quoteIdentifier`/`path`/`args`/`kwargs`, no oracle). A verifying impl must
  return exactly that disjunction.
- The discriminating behavior: when `old`/`new` differ ONLY in the `"choices"`
  keyword argument (same column, path, args, other kwargs), the post-patch spec
  drops `"choices"` from BOTH descriptions, so the structural triples become
  equal and (with equal columns) `result = false` — a NOOP. The prepatch impl's
  ignored set omits `"choices"`, so the differing `"choices"` kwarg survives, the
  triples differ, and it returns `true`. Hence the carried gold proof cannot
  close against the prepatch impl (G-DIFF / G-PANEL): on a choices-only change
  the spec demands `false` but the buggy impl yields `true`.
- This is exactly what `test_alter_field_choices_noop` exercises: a `CharField`
  gaining `choices=(("Jane","Jane"),("Joe","Joe"))` (same column, same
  `max_length`) must alter with zero queries (noop). Pre-patch it emitted SQL.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  `_field_should_be_altered`, over a structured exhaustive grid (column / path /
  args equal-or-changed × kwargs differing on an ignored attr — including the
  fixed `"choices"` — vs a column-relevant attr) plus ≥1e5 fuzzed field-pairs
  (0 disagreements).
