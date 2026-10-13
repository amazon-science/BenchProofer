# mapping.md — django__django-12209

## Symbol binding (file:line @ base_commit 5a68f024987e6d16c2626a31bf653a2edddea579)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_saveDecision` / `problem_spec_saveDecision` / `correct_saveDecision` | the fresh-insert routing decision inside `Model._save_table` (the "Skip an UPDATE when adding …" block + the `if pk_set and not force_insert:` update-attempt guard) | `django/db/models/base.py:829-868` (decision block at 849-858; update guard at 859) |
| `forcesFreshInsert` (pure helper) | the `force_insert = True` block computing the effective force-insert verdict | `django/db/models/base.py:849-857` |

## Lean ↔ Python type / value bijection (used by G-CONF and G-AX)

The modeled value is the PURE routing decision `_save_table` makes from five
booleans it has in hand at the decision point. The real method then *executes*
the chosen DB strategy (UPDATE/INSERT); that I/O is out of scope — only the
decision is modeled.

| Lean input | Python expression at the decision point | type |
|---|---|---|
| `verbatimLoad` | `raw` (the `_save_table(self, raw=False, …)` parameter; set `True` by the deserialization/`loaddata` framework) | `bool` |
| `forceFresh`   | `force_insert` (the `_save_table` parameter), as it stands just before the block | `bool` |
| `isNew`        | `self._state.adding` | `bool` |
| `keyHasDefault`| `bool(self._meta.pk.default) and self._meta.pk.default is not NOT_PROVIDED` | `bool` |
| `keySet`       | `pk_set` (`pk_val is not None` after `get_pk_value_on_save`) | `bool` |

| Lean output (`SaveDecision`) | Python | meaning |
|---|---|---|
| `result.forcesFresh` | the value of `force_insert` AFTER the decision block | True ⟹ skip UPDATE, go straight to INSERT |
| `result.attemptsUpdate` | the truth of the guard `pk_set and not force_insert` controlling the `_do_update` attempt | True ⟹ an in-place UPDATE is tried before any INSERT |

### Boolean modeling notes
- `keyHasDefault` collapses Python's two-part test (`self._meta.pk.default` truthy
  AND `is not NOT_PROVIDED`) into one boolean — the decision only consumes its
  truth value. `pk.default` truthiness and the `NOT_PROVIDED` sentinel are
  unchanged by the patch and out of the modeled boundary; their conjunction is the
  input `keyHasDefault`.
- The patched line adds the conjunct `not raw` to the force-insert block; in the
  model this is the `!verbatimLoad` conjunct inside `forcesFreshInsert`.

## Callee provenance / flag deps
- No unchanged callee is consumed as an axiom. `_get_pk_val`,
  `get_pk_value_on_save`, `_do_update`, `_do_insert` are downstream of the modeled
  decision and not part of the routing logic; their results are summarized by the
  input booleans (`keySet`) or are out of scope (the executed DB op).

## G-CONF fuzz seed
`conf_seed = 20240627` (pinned in meta.json). The decision is a 5-boolean
function (32 total points); G-CONF enumerates all 32 exhaustively and then fuzzes
≥1e5 random boolean tuples against the same oracle.
