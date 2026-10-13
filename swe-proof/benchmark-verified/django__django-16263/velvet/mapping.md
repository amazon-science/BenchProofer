# mapping.md — django__django-16263

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 321ecb40f4da842926e1bc07e11df4aabe53ca4b`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo files under change (gold): `django/db/models/sql/query.py`,
`django/db/models/query_utils.py`, `django/db/models/expressions.py`,
`django/db/models/sql/where.py`.

The modeled, F2P-discriminating kernel lives entirely in
`Query.get_aggregation` (`django/db/models/sql/query.py:438`), the function the
patch rewrites. The other hunks are supporting plumbing (see §5).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `countQueryShape (annos, added, groupByTuple, isSliced, distinct, combinator, havingFilter)` | `Query.get_aggregation(self, using, added_aggregate_names)` — `django/db/models/sql/query.py:438` | the modeled changed function: decides whether the aggregation runs in a nested query and which annotations survive |
| `Annotation` (`name`, `selected`, `isAggregate`, `isWindow`) | an entry of `self.annotation_select` / `self.annotations`, projected to: its alias, membership in the visible SELECT set, `getattr(annotation, "contains_aggregate", True)`, `getattr(annotation, "contains_over_clause", True)` | a previously-declared annotation |
| `Added` (`name`, `expr`) | an entry of `added_aggregate_names` together with `self.annotations[name]` (the summary expression and its reference tree) | an annotation added for the summary itself (e.g. the `__count`) |
| `Expr` (`reference` / `composite`) | an `Expression` tree: `Ref(refs, source)` ↔ `reference refs`; any other node ↔ `composite [children]` | the expression shape `get_refs` walks |
| `referencedNames` *(deep model — A-reference)* | `BaseExpression.get_refs` / `Ref.get_refs` / `WhereNode.get_refs` (the new methods: `django/db/models/expressions.py:408,1176`; `django/db/models/sql/where.py:230`) | the set of annotation aliases an expression refers to; deep model, validated `referencedNames == get_refs` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `needsNesting` (pure) | the `if (... or has_existing_aggregation or ...)` subquery decision — `query.py:466-473` post-patch (`has_existing_aggregation`, `query.py:449-456`) | whether a nested AggregateQuery is required |
| `keptNames` / `maskFold` (pure) | the inner-query annotation mask at the nesting decision: baseline `inner_query.set_annotation_mask(self.annotation_select)` (`query.py:483` post-patch), narrowed to `added_aggregate_names ∪ get_refs` ONLY inside the `if not inner_query.distinct:` guard (`query.py:486`, mask built at `query.py:498-503`) — under query-level `distinct` the narrowing is skipped and every selected annotation survives; plus the `existing_annotations` branch's `set_annotation_mask(added_aggregate_names)` (`query.py:534-547`) | which annotation aliases are retained in the produced SQL |
| `Plan` (`needsNesting`, `keptNames`) | the observable outcome: subquery-or-not, and the alias set appearing in the SELECT | the decided plan whose two coordinates the F2P tests observe via the emitted SQL |

The pre-patch repo expressions the change replaces (refinement audit only, not
in the consumer spec view): the list comprehension `existing_annotations`
(`query.py:444-448` pre-patch) and the `has_existing_aggregate_annotations`
recomputation (`query.py:485-491` pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.annotation_select` / `self.annotations` entry | `Annotation` | alias `str` ↔ `name : String`; `alias in annotation_select` ↔ `selected : Bool`; `getattr(a,"contains_aggregate",True)` ↔ `isAggregate : Bool`; `getattr(a,"contains_over_clause",True)` ↔ `isWindow : Bool` |
| an `added_aggregate_names` entry + its `self.annotations[name]` | `Added` | name `str` ↔ `name : String`; the expression tree ↔ `expr : Expr` |
| `Ref(refs, source)` | `Expr.reference refs` | the only node whose `get_refs` returns a non-empty singleton `{refs}` |
| any other `Expression` with `get_source_expressions()` | `Expr.composite [children]` | `get_refs` unions over children — modeled as concatenation; membership/length up to dedup is what is observed (§3.1) |
| `isinstance(self.group_by, tuple)` | `groupByTuple : Bool` | one structural trigger |
| `self.is_sliced` | `isSliced : Bool` | one structural trigger |
| `self.distinct` | `distinct : Bool` | one structural trigger |
| `self.combinator` | `combinator : Bool` | one structural trigger |
| `any(self.where.split_having_qualify()[1:])` | `havingFilter : Bool` | presence of a HAVING/QUALIFY filter against aliased aggregates/windows |
| the produced annotation-mask name set | `List String` (order-/dup-insensitive; compared as a set) | `set(...)` ↔ `List String`; G-CONF compares as sets |

`set` semantics: the real code builds Python `set`s (`annotation_mask`,
`get_refs`'s `refs`). Lean carriers are `List String`; **G-CONF and the
postcondition compare them as sets** (membership), so concatenation in
`maskFold`/`referencedNamesList` faithfully models set union.

## 3. Callee provenance

### 3.1 `referencedNames` deep model ↔ `get_refs` (A-reference)
**Callee:** the new `get_refs` family added by the patch
(`BaseExpression.get_refs`, `Ref.get_refs`, `WhereNode.get_refs`). The recursive
collector is modeled **deeply** by `referencedNames`/`referencedNamesList` in
the `pure` region; there is **no `get_refs` axiom** the proof consumes. Real
shape:

```python
# Ref.get_refs:            return {self.refs}
# BaseExpression.get_refs: refs = set(); 
#                          for expr in self.get_source_expressions(): refs |= expr.get_refs()
#                          return refs
```

`referencedNames (.reference s) = [s]` ↔ `Ref.get_refs`; `referencedNames
(.composite es)` unions over children ↔ `BaseExpression.get_refs`. Equality
holds as **sets** of aliases.

**Soundness check (G-AX):** `axiom_check.py` builds real Django `Ref` / `Func`
expression trees in-container, runs the real `get_refs`, and asserts
`set(referencedNames(model_tree)) == real_expr.get_refs()` over boundary
(single `Ref`, nested composites, no-ref leaves) + fuzzed random trees.

**Note — `get_refs` is patch-ADDED, not an unchanged base callee.** Unlike a
classic A-reference (an unchanged callee present at `base_commit`), the
`get_refs` family is INTRODUCED by the gold patch and does not exist at
`base_commit`. The G-AX harness runs `axiom_check.py` WITHOUT applying the gold
patch (only G-CONF gets `apply_gold`), so the script applies the gold patch
(mounted read-only at `/work/patch.diff`) to `/testbed` itself before importing
Django, then validates the deep model against the genuine patched `get_refs`.
This is the one place the deep model `referencedNames` is actually exercised
against the real callee: G-CONF shares the SAME real `get_refs` result between
its shadow and oracle (the A-reference leg is out of G-CONF scope by design), so
model↔callee equality is exclusively G-AX's obligation. The composite node is
built with `Func(*children, function="F")` (any arity ≥ 1) rather than
`Coalesce` (which demands ≥ 2 args and crashes on single-child composites).

### 3.2 The nesting predicate & mask are NOT axioms
`needsNesting`, `anyPriorAggregate`, `keptNames`, `maskFold` are pure spec
functions over the explicit method inputs. The inputs they consume
(`groupByTuple`, `isSliced`, `distinct`, `combinator`, `havingFilter`, and each
`Annotation`'s `selected`/`isAggregate`/`isWindow`) are **observable projections
of `self`** at the call (LESSONS "abstracted-input-not-axiom"): an unchanged
read of state, tagged **R** in refinement.md, needing no axiom and no G-AX entry.
`havingFilter` abstracts `any(self.where.split_having_qualify()[1:])`
(`where.py:38`), an UNCHANGED callee whose boolean result the decision reads; it
is an R-input, not a consumed axiom.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`16263`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`needsNesting`/`anyPriorAggregate`/`keptNames`/`maskFold`/`referencedNames`
(R/I-tagged pure ops) to Python and diffs against a faithful Python re-encoding
of `patch.diff`'s `get_aggregation` decision over ≥10⁵ fuzzed query shapes.

## 5. Out-of-scope supporting plumbing (not modeled; behaviour-neutral to F2P)

The gold patch also threads a `summarize` keyword through
`Q.resolve_expression` (`query_utils.py:90`), `Query.solve_lookup_type`
(`query.py:1195`), `Query.build_filter`, `Query._add_q`, and changes
`refs_expression` to return the alias (not the expression) and `None`/`False`.
These hunks support filtering against aliased aggregates inside the summary
(`Ref`-wrapping in `solve_lookup_type`). **None is exercised by the four
F2P/PASS tests of `AggregateAnnotationPruningTests`**, which call `.count()` /
`.aggregate(Avg(...))` with no filter argument. The modeled kernel
(`get_aggregation`'s nesting + mask decision) is the necessary and sufficient
locus for those tests; the `summarize` plumbing is a no-op on them. Modeling it
would add inputs the F2P tests never vary — recorded here for completeness, left
out of the spec by the "model the touched behaviour the tests observe" rule.
