# mapping.md — django__django-12050

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b93a0e34d9b9b99d41103782b7e7aeabf47517e3`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_iterable_value(value)` | the `elif isinstance(value, (list, tuple))` branch of `Query.resolve_lookup_value(self, value, can_reuse, allow_joins, simple_col)` — `django/db/models/sql/query.py:1053` (branch at line 1059, body lines 1062–1076) | the modeled changed function (the iterable-normalisation branch) |
| `Iterable` (fields `kind: int`, `items: List[int]`) | the iterable `value` (`list` or `tuple`) and its ordered items | minimal object exposing the two touched aspects: concrete container type + ordered items |
| `normalise_item(item)` *(axiom — A-consumed)* | `self.resolve_lookup_value(sub_value, can_reuse, allow_joins, simple_col)` applied to ONE sub-value (post-patch) / equivalently the inlined per-item `resolve_expression`-or-passthrough rule (pre-patch) | unchanged per-item normalisation the branch performs on each item |

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): `value = tuple(resolved_values)`
(`query.py:1076`) — the unconditional coercion to `tuple`, replaced by
`return type(value)(...)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the iterable `value`'s concrete type (`list` or `tuple`) | `kind: int` ∈ {0, 1} | `kind == 0 ⇔ value is a list`; `kind == 1 ⇔ value is a tuple`. `type(value)(...)` constructs the same concrete type, i.e. `out.kind == value.kind`. |
| the ordered items of `value` | `items: List[int]` of opaque item identities | `value[k]` ↔ `items[k]`; `len(value)` ↔ `len(items)`; item ordering preserved. An item's normalised value is its identity under `normalise_item`. |
| `type(value)(generator)` (the result construction) | `Iterable(value.kind)` filled in order | a fresh container of the input's concrete type holding the per-item normalisations, in order. The Python builtin call evaluates the generator left-to-right and constructs a `list`/`tuple`; the model loop appends in the same order. |

The items are opaque identities (`int`): the patch does not change *what* each
item resolves to, only the surrounding container type, so the item carrier need
only support equality and ordering — `List[int]`/`PSeq` suffices.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `normalise_item` ↔ per-item `resolve_lookup_value` (A-consumed)
**Callee:** `Query.resolve_lookup_value(self, sub_value, can_reuse, allow_joins,
simple_col)` applied to a single sub-value (the recursive call the gold patch
introduces), `django/db/models/sql/query.py:1053`. Its per-item behaviour is:

- a sub-value WITHOUT `resolve_expression` (a plain scalar, e.g. the strings
  `'a'`, `'b'` of the F2P test) → returned unchanged (the recursive call hits
  neither the expression branch nor the list/tuple branch);
- a sub-value WITH `resolve_expression` → `sub.resolve_expression(self,
  reuse=can_reuse, allow_joins=allow_joins[, simple_col=simple_col if F])` —
  the resolved expression.

This per-item rule is **UNCHANGED** by the patch: pre-patch the branch inlined
exactly this rule (the `F`/non-`F` `resolve_expression` dispatch and the plain
passthrough, lines 1064–1075); post-patch it delegates to the recursive call,
which computes the identical result for a single sub-value. The ONLY change is
the surrounding container construction (`tuple(...)` → `type(value)(...)`). The
axiom's contract is therefore the weakest possible, `Ensures(True)`: the proof
needs only that the result's i-th item equals `normalise_item(input_i)`, a
deterministic function of the item alone.

The load-bearing soundness fact (validated, not assumed): `normalise_item` is
**container-independent** — resolving a sub-value yields the same result whether
its parent was a list or a tuple. This is what makes "preserve the container
type" the sole observable change.

**Soundness check (G-AX):** `axiom_check.py`
- (A) transcribes the gold normalisation (`type(value)(self.resolve_lookup_value(
  sub, …) for sub in value)`) and the pre-patch (`tuple(resolved_values)`)
  VERBATIM over a recording per-item stub, and asserts over 7 boundary + 20000
  fuzz item-sequences (mixing plain values and expression-bearing items) that:
  the gold preserves the concrete iterable type (list→list, tuple→tuple) while
  the pre-patch coerces to tuple; every item equals the per-item normalisation
  of the corresponding input; and the per-item result is IDENTICAL between the
  list and tuple containers (container-independence ⇒ the axiom is sound);
- (B) drives the REAL `django.db.models.sql.query.Query.resolve_lookup_value`
  (minimal in-memory settings, no DB access) on the F2P scenario: a list value
  of plain items returns a list (`repr == "['a', 'b']"`), a tuple returns a
  tuple, a scalar passes through, and a nested list keeps every level a list.

It imports only the standard library plus Django (the package the changed
method lives in); no DB connection is opened. Exit 0 iff every obligation holds.
