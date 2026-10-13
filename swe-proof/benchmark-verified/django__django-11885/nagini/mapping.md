# mapping.md — django__django-11885

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 04ac9b45a34440fa447feb6ae934687aacbfc5f4`, states the type
abstraction, and gives the provenance of the deep-model reference (no consumed
axiom).

Repo file under change: `django/db/models/deletion.py` (the `Collector`
fast-delete planning in `collect`); a coordinated signature change to
`Collector.related_objects` / `get_del_batches` and the `NestedObjects`
override in `django/contrib/admin/utils.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combined_fast_delete_count(related_tables)` | the fast-delete planning in `Collector.collect` — `django/db/models/deletion.py:174` (the `collect_related` body, lines 214-245; the removals appended at line 228 `self.fast_deletes.append(sub_objs)`) | the modeled changed behaviour: how many bulk fast-delete removals are issued for the fast-removable candidate relations |
| `distinct_count(s)` *(deep model — A-reference)* | the grouping `model_fast_deletes = defaultdict(list)` keyed by `related_model`, then one `self.fast_deletes.append(sub_objs)` per `model_fast_deletes.items()` entry (post-patch `deletion.py` `collect`) | pure spec: number of distinct related tables = number of combined removals; the deep model of the unchanged `collections.defaultdict(list)` grouping, validated `distinct_count == len(model_fast_deletes)` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `contains(s, x)` | membership test underlying the grouping (whether the related model already has a group / occurs again) | pure spec helper: identity membership in a sequence |

The pre-patch repo shape the change replaces (for the refinement audit, not
referenced from the consumer spec view): inside `collect`'s
`for related in get_candidate_relations_to_delete(...)` loop, the body computed
`sub_objs = self.related_objects(related, batch)` and, when fast-removable,
executed `self.fast_deletes.append(sub_objs)` **once per candidate relation**
(`deletion.py:225-228`). There was no grouping by related model, so two
candidate relations targeting the same related table produced two separate
fast-delete querysets.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the ordered run of fast-removable candidate relations (each a reverse FK `related` whose `related_model` is the table it targets) | `List[int]` `related_tables`, one entry per candidate, holding the integer identity of the candidate's `related_model` | candidate `j` ↔ `related_tables[j]`; two candidates targeting the same related model ↔ two equal entries; the F2P case (`SecondReferrer.referrer`, `SecondReferrer.other_referrer`, both → `Referrer`) ↔ `related_tables == [r, r]` |
| `model_fast_deletes = defaultdict(list)` keyed by `related_model` | the distinct-identity grouping of `related_tables` | a `defaultdict(list)` key ↔ a distinct identity; `len(model_fast_deletes)` ↔ `distinct_count(ToSeq(related_tables))` |
| `len(self.fast_deletes)` contributed by fast-removable candidates (number of bulk removal queries) | `Result()` of `combined_fast_delete_count` | one `self.fast_deletes.append` per distinct related model ↔ `Result() == distinct_count(...)` |
| the per-table combined predicate `reduce(operator.or_, Q(**{field__in: objs}) for field in related_fields)` built in `related_objects(related_model, related_fields, objs)` | (not modelled at value level) | only the *grouping cardinality* is observed by the F2P `assertNumQueries`; the predicate-construction is an unchanged-shape callee detail (see §3) carrying no count, so it is omitted from the carrier |

The relations / fields / querysets are rich Django objects; Nagini cannot carry
them. Only the integer identity of each candidate's related table is load-
bearing for the tested behaviour (the number of distinct tables = the number of
combined removals), so the carrier is `List[int]` and the specification is
phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee / reference provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `distinct_count` deep model ↔ `collections.defaultdict(list)` grouping (A-reference)
**Operation:** the gold patch replaces the per-candidate
`self.fast_deletes.append(sub_objs)` with a grouping by related model:

```python
model_fast_deletes = defaultdict(list)
for related in get_candidate_relations_to_delete(model._meta):
    ...
    related_model = related.related_model
    if self.can_fast_delete(related_model, from_field=field):
        model_fast_deletes[related_model].append(field)
        continue
    ...
for related_model, related_fields in model_fast_deletes.items():
    batches = self.get_del_batches(new_objs, related_fields)
    for batch in batches:
        sub_objs = self.related_objects(related_model, related_fields, batch)
        self.fast_deletes.append(sub_objs)
```

The number of bulk removals issued for the fast-removable candidates is exactly
`len(model_fast_deletes)` — the number of DISTINCT related models among the
candidates (a `defaultdict` has one key per distinct related model; appending
`field` to an existing key does not create a new group). This is modelled
**deeply** by the `@Pure` fold `distinct_count` (with `contains`) in the `pure`
region; there is **no `@ContractOnly` axiom** the proof consumes. The deep model
is validated equal to the real grouping out-of-band by axiom_check.py (G-AX),
which reproduces the grouping with the very `collections.defaultdict(list)`
primitive the patch uses and asserts `distinct_count(ids) == len(grouping)` on
11 boundary + 50 000 fuzz candidate runs, that no candidate column is dropped or
duplicated (`sum(len(fields)) == len(ids)`), and the bounds
`1 <= removals <= len(ids)` (non-empty). `collections.defaultdict` is the Python
standard library — the same module the gold patch imports. Docs:
https://docs.python.org/3/library/collections.html#collections.defaultdict.

### 3.2 Unchanged-shape callees NOT modelled (no consumed axiom, carry no count)
The patch also threads a *list* of fields through `related_objects` and
`get_del_batches` and builds the combined predicate with
`functools.reduce(operator.or_, Q(...))`, and uses `objs._meta.model` in
`can_fast_delete`. These change the *content* of each query (one combined
`WHERE col_a IN (...) OR col_b IN (...)`) but not the *number* of removals,
which is the only thing the F2P `assertNumQueries(2)` observes and the only
thing the model pins. They are therefore neither consumed axioms nor A-references
of the modelled count; they appear in the refinement table (refinement.md §B)
as type-refinement / identical-shape steps of the same patch, validated by
G-RESOLVE (the gold patch resolves), not by an axiom contract.
