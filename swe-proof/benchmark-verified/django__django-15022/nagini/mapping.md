# mapping.md — django__django-15022

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e1d673c373a7d032060872b690a92fc95496612e`, states the type
abstraction, and gives the provenance of the modelled relation.

Repo file under change: `django/contrib/admin/options.py`
(method `ModelAdmin.get_search_results`, body lines 1029-1046).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `search_retains_object(rows, terms)` | the per-candidate effect of `get_search_results` — `django/contrib/admin/options.py:994` (search body 1029-1046) | the modelled changed combination: for one candidate object, does the search retain it? |
| `matches(row, term)` *(uninterpreted relation)* | the truth of one per-term OR-query `models.Q(*((orm_lookup, bit) for orm_lookup in orm_lookups), _connector=OR)` evaluated against ONE related row (`options.py:1037-1040`) | abstract per-(related-row, search-term) match: at least one searched field of that row matches that term |
| `row_matches_all(row, terms)` *(deep model)* | the conjunction of all per-term OR-queries holding on a SINGLE related row — i.e. the body of one `models.Q(*term_queries)` (AND of the collected per-term queries) checked against one row | pure spec: a single row clears every term |
| `some_row_matches_all(rows, terms)` *(deep model)* | the result of `queryset.filter(models.Q(*term_queries))` over a multi-valued relation: a candidate is kept iff some related row clears the whole conjunction | pure spec: retention predicate (exists-row, for-all-terms) |
| `terms` (a `PSeq[int]` of term ids) | the search bits produced by `for bit in smart_split(search_term)` (`options.py:1034`), each unquoted by `unescape_string_literal` | abstraction of the search-term list |
| `rows` (a `PSeq[int]` of row ids) | the set of related rows reachable from the candidate via the multi-valued relation named in `search_fields` | abstraction of the related-row collection for one candidate |

The pre-patch repo construct the change removes/replaces (for the refinement
audit, not referenced from the consumer spec view): the in-loop
`queryset = queryset.filter(or_queries)` re-assignment (`options.py:1042`),
which chains one `.filter()` per search term. The patch replaces it with an
accumulator `term_queries = []`, `term_queries.append(or_queries)` inside the
loop, and a single post-loop `queryset = queryset.filter(models.Q(*term_queries))`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the list of search bits from `smart_split(search_term)` | `terms: PSeq[int]` of opaque term ids | `len(terms)` ↔ number of bits; identity of a term is irrelevant — only its `matches` truth per row matters |
| the multi-valued related rows of one candidate | `rows: PSeq[int]` of opaque row ids | `len(rows)` ↔ number of related rows; a row's identity matters only through `matches` |
| one per-term OR-query truth against one row (`models.Q(*((orm_lookup, bit) …), _connector=OR)`) | `matches(row, term): bool` | the OR over searched fields collapses to a single boolean per (row, term); the model does not re-derive that boolean (the field comparison is unchanged) |
| `queryset.filter(Q_and)` over a multi-valued relation, where `Q_and` ANDs the per-term sub-queries | `some_row_matches_all(rows, terms)` | Django joins the related table once and requires a SINGLE joined row to satisfy the whole conjunction (one `.filter()` ⇒ one join ⇒ same-row semantics) |
| chained `qs.filter(q1).filter(q2)…` (pre-patch) | `every_term_matched_somewhere` (only in the audit / prepatch reasoning) | each `.filter()` adds a fresh join, so different terms may be satisfied by different related rows (for-all-terms, exists-row) |

`str` indexing/iteration is banned in Nagini; the search-term and related-row
collections are carried as `PSeq[int]` of opaque identifiers because only their
cardinality and their per-pair `matches` truth are observable to the
combination semantics.

## 3. Relation provenance (the modelled combination)

### 3.1 The single-`.filter()` AND-on-one-row semantics (the fix)
**Construct:** `queryset.filter(models.Q(*term_queries))` where
`term_queries` is the list of per-term OR-queries
(`options.py:1037-1045`, post-patch). `models.Q` defaults to
`connector = AND` (`django/db/models/query_utils.py`: `Q.default = AND`), so the
combined node is `AND_t ( OR_lookups (orm_lookup, bit_t) )`.

A single `QuerySet.filter()` call that spans a multi-valued relation reuses one
join, so the whole conjunction must be satisfied by the SAME related row. Hence
a candidate is retained iff **some related row satisfies every term**:
`some_row_matches_all(rows, terms)` — exists-row, then for-all-terms. This is
the documented Django semantics that distinguishes a single `.filter(A & B)`
from chained `.filter(A).filter(B)` across multi-valued relationships
(Django docs, "Spanning multi-valued relationships":
https://docs.djangoproject.com/en/4.1/topics/db/queries/#spanning-multi-valued-relationships).

### 3.2 The chained-`.filter()` semantics (the pre-patch bug)
**Construct (removed):** `for bit … : queryset = queryset.filter(or_queries)`
(`options.py:1042`, pre-patch). Each `.filter()` introduces a NEW join, so each
term may be matched by a DIFFERENT related row: the candidate is retained iff
**every term is matched by some (possibly different) related row** —
for-all-terms, then exists-row (`every_term_matched_somewhere`). It also emits
one join per term, the performance defect the issue reports.

These two set-theoretic semantics — `∃r ∀t` (fix) vs `∀t ∃r` (bug) — are
exhaustively contrasted over small relational domains in `axiom_check.py`
(G-AX): for every match matrix it confirms the model's deep predicate
`some_row_matches_all` equals the single-filter-AND result and differs from the
chained-filter result exactly when the quantifier order matters. There is **no
stdlib/library callee to axiomatize** here: the changed operation is the
query-combination semantics, modelled deeply; `matches` is an uninterpreted
relation standing for the (unchanged) per-field comparison and the proof relies
on NO property of it (its contract is the tautology `Implies(R, R)`).

## 4. G-CONF (conformance_check.py)

Differential fuzz seed pinned to the instance number: **15022**. The shadow is
the contract-stripped impl region of `search_retains_object`; the oracle is
the real patched `ModelAdmin.get_search_results` run against materialized
Parent/Child rows whose per-(row, term) token containment realizes the
abstract `matches` matrix (`search_fields = ["children__tag"]`).
