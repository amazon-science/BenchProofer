# mapping.md — django__django-15022

Binds every `Solution.lean` symbol to the repository at
`base_commit = e1d673c373a7d032060872b690a92fc95496612e`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/contrib/admin/options.py` (method
`ModelAdmin.get_search_results`, `options.py:994`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `searchKeepsRow (records, terms, matchTerm)` | the search-term combination loop of `ModelAdmin.get_search_results` — `options.py:1031-1046` (the `for bit in smart_split(...)` loop + the final `queryset.filter(...)`) | the modeled changed decision: for ONE candidate outer row, whether the row is kept by the multi-word search over its related items |
| `anyRecord (matchTerm) (terms) (records)` *(pure)* | the post-patch combined filter `queryset.filter(models.Q(*term_queries))` evaluated row-by-row — "some related item satisfies the AND of all per-word OR-queries" | pure spec: ∃ related item r. ∀ word t. r matches t |
| `conjTerms (matchOf) (terms)` *(pure)* | the conjunction `models.Q(*term_queries)` = `Q(word₁) AND Q(word₂) AND …` applied to a single related item | pure spec: one item matches every word |
| `matchTerm : Nat → Nat → Bool` *(free input)* | `or_queries` for a word, evaluated against one related item: `models.Q(*((orm_lookup, bit) for orm_lookup in orm_lookups), _connector=OR)` — "does related item `r` match word `t` on at least one searched field" | the per-(item,word) match test; UNCHANGED by the patch, taken as a free input |

Inputs that are **free** (universally quantified — see §3):

| Solution.lean input | repo meaning |
|---|---|
| `records : List Nat` | the related items reachable from one candidate outer row through the searched multi-valued relation (e.g. the `Child` rows of one `Parent`); each `Nat` is an opaque item identity. For a search over only local (non-relational) fields this is the single implicit "self" item. |
| `terms : List Nat` | the search words `list(smart_split(search_term))` (after the quote-literal unwrap); each `Nat` is an opaque word identity. `require 0 < terms.length` mirrors the guard `if search_fields and search_term:` under which the loop runs at all. |
| `matchTerm : Nat → Nat → Bool` | `matchTerm r t` = "related item `r` matches search word `t` on at least one of the searched fields" — the per-word `or_queries` OR-of-fields predicate evaluated at item `r`. A total function of (item, word); UNCHANGED by the patch. |

The pre-patch repo behaviour the change removes (refinement audit only, not in the
consumer spec view): the **chained** `queryset = queryset.filter(or_queries)`
inside the loop, which re-joins the related table once per word and so keeps a
row when *each* word is matched by *some* (possibly different) related item.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the related items of one outer row (a multi-valued relation / multiset of rows) | `records : List Nat` | each related item ↔ a distinct `Nat` identity; the per-row decision depends only on the SET of items and their per-word match bits, so an opaque identity carrier is faithful; count ↔ `.length` |
| the search words `list(smart_split(search_term))` | `terms : List Nat` | each word ↔ a distinct `Nat`; order is irrelevant to the AND/OR aggregate (commutative), preserved anyway; count ↔ `.length` |
| `or_queries` evaluated at one related item for one word (OR over searched fields) | `matchTerm r t : Bool` | the composite "item r matches word t on some searched field" ↔ a total `Nat → Nat → Bool`; truthy ↔ `true` |
| `models.Q(*term_queries)` (AND of the per-word OR-queries) at one item | `conjTerms (matchTerm r) terms` | `Q(t₁) AND … AND Q(tₙ)` ↔ front-recursive conjunction; empty ↔ `true` (vacuous) |
| a row survives `queryset.filter(models.Q(*term_queries))` over its related items | `anyRecord matchTerm terms records` | a row is kept iff SOME related item satisfies the AND ↔ `∃ r ∈ records. conjTerms (matchTerm r) terms`; empty items ↔ `false` |
| the kept/dropped decision for one outer row | the `Bool` `result` | exact |

`require 0 < terms.length`: the modeled loop only runs when `search_fields and
search_term`, and `smart_split` of a non-empty search term yields ≥1 word; the
combined `Q(*term_queries)` is then a non-trivial AND. (With zero words the row
is unconditionally kept; that degenerate case is outside the modeled branch.)

## 3. Callee provenance — why there are NO axioms / NO A-references

The patch changes only the **combination logic**: how the per-word OR-queries are
combined into the final filter (chained `.filter` per word → a single
`.filter(Q(AND of all words))`). Everything the loop *calls* is unchanged
infrastructure or abstracted into a free input:

- **`smart_split(search_term)`, `unescape_string_literal(bit)`,
  `construct_search(...)` / `orm_lookups`** — UNCHANGED by the patch. They produce
  the word list and the per-field lookups identically pre- and post-patch. The
  word list is the free input `terms`; the per-field lookups feed `matchTerm`.
- **`models.Q(...)` with `_connector=OR` (`or_queries`) and the ORM evaluation of
  a query against a related item** — the per-word, per-item match test is
  UNCHANGED; only how the resulting `or_queries` are *combined* changes. The
  modeled decision makes **no behavioural claim** about how a single word matches
  a single item; it treats "item `r` matches word `t`" as the free input
  `matchTerm : Nat → Nat → Bool`. The spec is proven for **every** such function.
- **`queryset.filter(...)` / the SQL JOIN behaviour** — the JOIN-count regression
  (the performance symptom) is a *consequence* of the combination choice, not a
  separately modeled quantity; the observable correctness difference the F2P
  tests assert is the row-membership decision, which is exactly `anyRecord` (post)
  vs `∀word∃item` (pre). The `may_have_duplicates` tail (`options.py:1042-1045`)
  is byte-identical pre/post and not modeled.

Because every callee is unchanged and either bypassed by the modeled decision or
abstracted as a free input with no relied-on property, this bundle has
**`axioms: []`** and **`deep_model_references: []`** (cf. the structurally-twin
free-input boolean-decision bundle django__django-11149). Consequently **no
`axiom_check.py`** is shipped and **G-AX skips** ("no axioms in bundle"). The
single trust point is refinement fidelity (refinement.md, G-EQ + G-CONF).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15022`**. The R/I shadow
transliterates `conjTerms` + `anyRecord` + the `searchKeepsRow` fold from
`Solution.lean`; the oracle is the gold-patched combination logic transliterated
verbatim — `keep_row = any(all(match(r, t) for t in terms) for r in records)` —
which is the row-membership semantics of `queryset.filter(models.Q(*term_queries))`
(see the `conformance_check.py` docstring for why the real ORM/SQL is not driven
in-container). Both are exercised over exhaustive small (records × terms × match
bit-matrix) cubes plus seeded fuzz over random match matrices.
