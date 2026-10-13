# mapping.md — django__django-13569

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 257f8495d6c93e30ab0f52af4c488d7344bcf112`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of every callee. `spec_provenance: cold`.

Repo file under change: `django/db/models/functions/math.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `groupingColumns (e : Expr)` | `Random.get_group_by_cols(self, alias=None)` — `django/db/models/functions/math.py:144` (the `Random` class; the method is **added** by the patch immediately after `as_sqlite`, body line 154) | the modeled changed function: the grouping-column contribution of a `RANDOM()` value-generator expression |
| `Expr` (structure) | a `django.db.models.expressions.Expression` node, abstracted to the one observation that decides the contribution: `isNondetGenerator` ↔ "is this an instance of `Random`?" | rich-object → structure with only the touched field (SPEC_GUIDE §2) |
| `groupingContribution (e : Expr)` | the per-node decision the patched method now realises for `Random`, contrasted with the inherited generic rule it overrides | pure spec: grouping columns one leaf contributes |

The pre-patch repo behaviour the change overrides (refinement audit only, NOT in
the consumer spec view): `Random` carries **no** `get_group_by_cols` of its own,
so it inherits `BaseExpression.get_group_by_cols`
(`django/db/models/expressions.py:349`). For a node with
`contains_aggregate == False` (true of `Random`, which has no source
expressions) that method returns `[self]`. Hence pre-patch a `Random()` used for
ordering contributes itself as a grouping column — the observed defect
(`GROUP BY ..., RANDOM()`), which breaks the aggregation grouping.

## 2. Type abstraction (R-refinement) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a resolved SQL `Expression` node, observed only through whether it is a `Random` (a non-deterministic value generator) | `Expr` with field `isNondetGenerator : Bool` | `isNondetGenerator = true` ↔ `isinstance(node, Random)`; the modeled method exists only on `Random`, so the spec is taken under `require isNondetGenerator = true` (the `Random` receiver) |
| the list returned by `get_group_by_cols()` (a `list` of column expressions) | `List Expr` | empty Python `list` ↔ `[]`; a singleton `[self]` ↔ `[e]`. Only emptiness vs. self-inclusion is observed (mapping.md §3) — that is the full behavioural content of the change. |

`get_group_by_cols` ignores its `alias` argument for `Random` (the patched body
is `return []` regardless of `alias`); the model omits `alias` accordingly.

## 3. Callee provenance

The modeled function `Random.get_group_by_cols` is the **changed** function
itself. Its post-patch body (`return []`) calls **no** other callee, and the
behaviour it overrides (`BaseExpression.get_group_by_cols` →
`[self]` for a non-aggregate) is modeled **deeply** by the `else` branch of
`groupingContribution` — it is NOT an axiom the proof consumes. There is
therefore **no axiomatized callee** in this bundle (no `axiom_check.py`, G-AX
skipped — cf. the no-axiom exemplar `django__django-12406`).

The grounding the spec relies on (validated by G-CONF / G-RESOLVE, not assumed):

- post-patch, `Random().get_group_by_cols()` returns `[]` (the patched body);
- pre-patch, `Random().get_group_by_cols()` returns `[Random()]` (i.e. `[self]`,
  inherited via `BaseExpression.get_group_by_cols`, `contains_aggregate=False`).

Both observations are executed directly against the real repo classes by
`conformance_check.py` (it imports `django.db.models.functions.Random` and
`django.db.models.expressions.BaseExpression`), so the R/I shadow is checked
against the genuine `Random` node, not a hand-copied rule.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13569`** so the
consumer-side verdict (§11.3) is reproducible. The input space (whether the leaf
is a `Random` generator vs. an ordinary column-bearing expression) is small and
enumerated exhaustively; the seed governs only the synthesis of additional
ordinary-column fuzz expressions used to confirm the non-generator leg.
