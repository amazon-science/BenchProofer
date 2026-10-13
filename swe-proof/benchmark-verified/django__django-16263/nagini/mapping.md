# mapping.md — django__django-16263

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 321ecb40f4da842926e1bc07e11df4aabe53ca4b`, states the type
abstraction, and gives the provenance of the one deep-model reference (there are
no consumed axioms).

Repo files under change:
`django/db/models/sql/query.py` (the function under spec, `get_aggregation`),
`django/db/models/expressions.py` and `django/db/models/sql/where.py` (the new
`get_refs()` reference-gatherer the decision consumes),
`django/db/models/query_utils.py` (a threaded `summarize` flag, behaviourally
inert for the modelled decisions).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `existing_summary_forces_derived(selected, summ, filter_summary)` | the `has_existing_aggregation` computation that drives the subquery decision in `get_aggregation` — `django/db/models/sql/query.py:438` (the new `existing_annotations = {alias: annotation for ... in self.annotation_select.items() ...}` dict built from `annotation_select`, then `has_existing_aggregation = any(... contains_aggregate ... or ... contains_over_clause ...) or any(self.where.split_having_qualify()[1:])`, consumed in the `if (...)` at body line ~467) | modelled changed decision #1 (both axes): whether the SELECTED pre-existing annotations force the wrapping subquery |
| `inner_column_kept(alias, added, ref_tree)` | the inner-query annotation-mask computation in `get_aggregation` — `django/db/models/sql/query.py:489-503` (the new `annotation_mask = set(); for name in added_aggregate_names: annotation_mask.add(name); annotation_mask |= inner_query.annotations[name].get_refs(); inner_query.set_annotation_mask(annotation_mask)`) | modelled changed decision #2: which pre-existing annotation aliases survive the inner selection |
| `collect_refs(tree)` *(deep model — A-reference)* | `get_refs()` — `BaseExpression.get_refs` (`django/db/models/expressions.py:408` post-patch, union over sources), `Ref.get_refs` (`expressions.py:1176` post-patch, `return {self.refs}` — a hard LEAF), `WhereNode.get_refs` (`django/db/models/sql/where.py:230` post-patch, union over children) | pure spec: the references reachable from an expression; the deep model of the new recursive reference-gatherer, validated `collect_refs == get_refs` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `any_selected_summary(selected, summ)` | `any(getattr(annotation, "contains_aggregate", True) or getattr(annotation, "contains_over_clause", True) for annotation in existing_annotations.values())` where `existing_annotations` is built from `self.annotation_select` (`query.py:438` block) | pure spec: at least one SELECTED pre-existing annotation carries aggregation (the source-filter and the attribute disjunction in lock-step) |
| `seq_contains(s, x)` | set membership `x in <get_refs result>` / `name in annotation_mask` | pure spec: membership of a reference/alias code in a sequence |

The pre-patch repo expressions the change supersedes (for the refinement audit,
not referenced from the consumer spec view): the list comprehension
`existing_annotations = [annotation for alias, annotation in self.annotations.items() if alias not in added_aggregate_names]`
(`query.py:444-448`, built from `self.annotations` — ALL annotations, incl.
alias-only — and used truthy in the subquery `if`) and the unconditional
`inner_query.set_annotation_mask(self.annotation_select)` (`query.py:474`) which
kept every pre-existing annotation in the inner selection. The gold flips the
decision-#1 source from `self.annotations` to `self.annotation_select` (axis 1)
AND the predicate from truthiness to `contains_aggregate or contains_over_clause`
(axis 2); both axes are modelled.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| whether an existing annotation is SELECTED — i.e. its alias ∈ `self.annotation_select` (gold builds `existing_annotations` from `self.annotation_select.items()`, not `self.annotations.items()`) | `selected: List[int]`, `selected[k] != 0` ⇔ annotation k is in `annotation_select` | one int flag per existing annotation; `annotate(x=…)` ⇒ `add_annotation(…, select=True)` ⇒ `selected=1`; `alias(x=…)` ⇒ `add_annotation(…, select=False)` ⇒ `selected=0` (grounded in axiom_check `_selected_bit` against a real `Query`) |
| the resolved annotation objects, each inspected via `getattr(ann,"contains_aggregate",True) or getattr(ann,"contains_over_clause",True)` | `summ: List[int]`, `summ[k] != 0` ⇔ annotation k carries an aggregate or over-clause | one int flag per existing annotation; the disjunction of the two boolean attributes is the single observed bit |
| `any(self.where.split_having_qualify()[1:])` (a retained HAVING/QUALIFY filter exists) | `filter_summary: int`, `!= 0` ⇔ such a filter is present | a single observed bit |
| a resolved expression's tree (for `get_refs`) | `ref_tree: List[int]` — the flattened tree, a node coded `> 0` is a `Ref` LEAF contributing its referent's alias code (its source is NOT descended into), a node coded `0` is a non-referencing sub-expression whose children are still folded | `Ref(refs, src)` ↔ a positive code for `refs` ONLY (no source subtree — matching `Ref.get_refs() == {self.refs}`); any other node ↔ `0` then its children flattened; membership of a code in `collect_refs(flatten(tree))` ⇔ that alias ∈ real `get_refs()` |
| `added_aggregate_names` (the pushed-out summary names) | `added: List[int]` of alias codes | `name` ↔ its alias code |
| an alias / a `Ref.refs` string | `int` code | a stable code per distinct alias string (assigned in axiom_check.py) |
| a `set` of names / refs | the membership predicate `seq_contains` over the carrier sequence | the decisions observe only membership, never order or multiplicity, so a sequence-with-membership is observationally a set |
| the decision computations COMPLETE: `has_existing_aggregation` is an `any(...)` over the finite `existing_annotations` dict (plus one `split_having_qualify()` call) and the `annotation_mask` computation is a bounded `for name in added_aggregate_names` loop over finite `get_refs()` sets — both always return their answer to `get_aggregation` | `Requires(MustTerminate(2))` on both modelled decisions, discharged in each loop by the strictly decreasing measure `Invariant(MustTerminate(i))` / `Invariant(MustTerminate(j))` | the real evaluations are bounded, so every call terminates; the obligation pins that an implementation may not DIVERGE instead of answering (Nagini checks partial correctness by default, so without it a non-terminating same-spec body satisfies every `Ensures` vacuously — the audit's P1 witness class; its faithful real patch would hang the F2P/P2P aggregation tests and not resolve) |

`str` indexing/iteration and the live ORM `Query`/`Expression`/`WhereNode`
objects are not Nagini-expressible, so each decision is modelled over the
minimal `List[int]` carriers that record exactly the bits the decision reads.

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `collect_refs` deep model ↔ `get_refs()` (A-reference)
**Callee:** the recursive reference-gatherer the gold patch ADDS:

```python
# BaseExpression.get_refs (expressions.py)
def get_refs(self):
    refs = set()
    for expr in self.get_source_expressions():
        refs |= expr.get_refs()
    return refs

# Ref.get_refs (expressions.py)
def get_refs(self):
    return {self.refs}

# WhereNode.get_refs (where.py)
def get_refs(self):
    refs = set()
    for child in self.children:
        refs |= child.get_refs()
    return refs
```

`get_refs()` returns the set of alias strings referenced (transitively) by an
expression: a bare `Ref` contributes EXACTLY its own `refs` and is a **LEAF**
(`Ref.get_refs(self): return {self.refs}` — it does NOT recurse into
`self.source`); any composite node contributes the union of its
sub-expressions'. `model.py` models this DEEPLY as `collect_refs`: a
front-recursive fold over the expression's flattened tree where a `Ref` flattens
to its referent code ONLY (its source subtree is NOT emitted), and every other
node flattens to `0` + its folded children; the decision observes only set
membership. There is **no `get_refs` `@ContractOnly` axiom** the proof consumes;
the deep model is instead validated equal to the real `get_refs()` out-of-band by
axiom_check.py (G-AX): it constructs real Django expression trees (`Ref`,
`Value`, `Concat`, `ExpressionWrapper`, `Avg`, including **Refs whose source is
itself a Ref-bearing subtree** — `Ref("outer", Ref("inner", …))` etc. — and 5000
randomized trees whose Ref sources are themselves randomly-built subtrees), runs
the REAL `get_refs()`, and asserts `set(collect_refs(flatten(tree))) ==
get_refs(tree)` and the per-alias membership `seq_contains(collect_refs(flatten(tree)),
code) == (code ∈ get_refs)`. The nested-Ref cases exercise precisely the
leaf-vs-recurse region: real `get_refs(Ref("outer", Ref("inner", …))) == {outer}`,
so a source-recursing flatten that over-collected `{outer, inner}` is now caught.
The `flatten_expr` transcription `collect_refs` is also asserted to mirror the
model fold (front-recursive == iterative) on every tree, so the check drives the
actual modelled fold, not a divergent hand-copy.

### 3.2 Decision discriminators ↔ real expression attribute semantics
The two decision functions are spelled out deeply over the carriers; their
correspondence to the live Django semantics is the type abstraction of §2. The
F2P-observable instances of those semantics are checked in axiom_check.py
against real Django:

- The `selected` bit is GROUNDED: a real `Query` is built with
  `add_annotation(Count(...), "authors_count", select=True)` (what `annotate()`
  does) ⇒ `"authors_count" in query.annotation_select` ⇒ `selected=1`; and with
  `select=False` (what `alias()` does) ⇒ `"authors_count"` absent ⇒ `selected=0`.
  This is the source-switch axis (`self.annotations` → `self.annotation_select`).
- (axis 1) an ALIAS-ONLY aggregate `selected=[0], summ=[1]` ⇒ no wrapping
  (`test_unused_aliased_aggregate_pruned`: 1 SELECT). Only the
  `annotation_select` source stops it; the predicate alone would wrap.
- (axis 2) `Lower(Value("name"))` has `contains_aggregate is False` and
  `contains_over_clause is False` ⇒ `summ=0`; SELECTED non-aggregate
  `selected=[1], summ=[0]` ⇒ no wrapping (`test_non_aggregate_annotation_pruned`:
  1 SELECT).
- `Count(Value(1))` has `contains_aggregate is True` ⇒ `summ=1`; a SELECTED
  aggregate `selected=[1], summ=[1]` ⇒ wrapping (tests
  `test_unreferenced_aggregate_annotation_pruned`,
  `test_referenced_aggregate_annotation_kept`: 2 SELECTs).
- `Count("*").get_refs() == set()` ⇒ an unreferenced `authors_count` annotation
  is pruned from the inner select (`test_unreferenced_aggregate_annotation_pruned`:
  `authors_count` not in SQL).
- `Avg(Ref("authors_count", ...)).get_refs() == {"authors_count"}` ⇒ a
  referenced `authors_count` annotation is kept (`test_referenced_aggregate_annotation_kept`:
  `authors_count` appears twice).

No flag dependency: `get_refs()` and the `contains_*` attributes take no
configuration; `contains_aggregate` is read with the default `True` only for the
absent-attribute fallback, which never fires on the resolved annotations these
decisions inspect.

## 4. The `summarize` flag threading (behaviourally inert here)
The gold also threads a `summarize=False` keyword through `build_filter`,
`_add_q`, `solve_lookup_type`, and `Q.resolve_expression`/`query_utils.py`. That
threading only changes filter resolution when a summarized aggregate is filtered
on; it does not alter either modelled decision and is observed by none of the
three FAIL_TO_PASS pruning tests (which never filter on a summarized aggregate).
It is therefore carried verbatim in `patch.diff` (so G-RESOLVE is exact) but is
not part of the modelled behavioural core.

## G-CONF (differential conformance: shadow of the impl region vs the REAL patched repo function)

`conformance_check.py` refutes the refinement leg no other gate covers: that the
MODEL agrees with the real patched code. It is run in-container by G-CONF with
`patch.diff` applied to /testbed and `PYTHONPATH=/testbed`.

**Shadow.** The `# impl-start` / `# impl-end` regions of BOTH
`existing_summary_forces_derived` and `inner_column_kept`, copied VERBATIM with
only the contract calls removed (`Requires` / `Ensures` / `Invariant` / `Assert`
/ `MustTerminate` and the `# invariants-start` / `-end` markers) — nothing
restructured or renamed, including the `tail_refs` / `cons` intermediates inside
the reference scan. All three `@Pure` helpers (`collect_refs`,
`any_selected_summary`, `seq_contains`) are copied verbatim too, front-recursion
intact, over a tuple-backed `PSeq` shim (`take`/`drop`/`+`/`len`/`[]`/`==`,
`ToSeq`). No `@ContractOnly` callees exist in this bundle (§3), so nothing is
axiomatized away.

**Oracle — CALLED, not transliterated.** The real patched
`Query.get_aggregation` (`django/db/models/sql/query.py`, §1) is DRIVEN on a real
`Query` over a real model against a real sqlite connection, with real resolved
annotations; the real patched `Ref.get_refs` / `BaseExpression.get_refs` /
`WhereNode.get_refs` build the real mask, so §3.1's deep model is exercised here
too rather than assumed. (The velvet and lean siblings transliterate the patched
decision lines because their shadows are not Python; this one has no such
constraint.) Two observables are read off the real run:
`AggregateQuery.__init__` firing == the wrapping-subquery branch (decision 1),
with the real `has_existing_aggregation` local captured by frame inspection and
cross-checked against it; and the real `annotation_mask` set captured by identity
at the patched `inner_query.set_annotation_mask(annotation_mask)` call site
(decision 2). Every probe pins the four out-of-scope disjuncts of that `if`
(`isinstance(group_by, tuple)` / `is_sliced` / `distinct` / `combinator`) to
false and ASSERTS it, so the branch taken is exactly the modelled decision.

**Type bridge (§2, inverted).** Each carrier bit is READ OFF the real objects,
never assumed: `selected[k] != 0` ⇐ `alias_k in query.annotation_select`;
`summ[k] != 0` ⇐ `contains_aggregate or contains_over_clause` on the resolved
annotation; `filter_summary != 0` ⇐ `any(query.where.split_having_qualify()[1:])`
evaluated by the real `WhereNode`; `added` ⇐ the pushed-out summary names as
alias codes; `ref_tree` ⇐ the resolved added annotations flattened with a `Ref`
as a LEAF contributing its referent code (source NOT descended into) and every
other node contributing `0` then its children. Alias string ↔ `int` code =
index in `NAME_POOL` + 1 (`0` is reserved by the carrier).

**Inputs.** 100000 probes: 42 boundary shapes first (empty carrier; every
(selected × aggregate/non-aggregate/window) singleton; the three FAIL_TO_PASS
shapes and the referenced-kept control; HAVING and QUALIFY filters alone and
combined; refs to unselected aliases; phantom refs to never-annotated names; two
pushed-out summary names; deep and wide reference trees), then seeded fuzz. Every
branch of both impl regions is taken (`found` set / not set; `filter_summary`
alone forcing the derived form; `in_added` and `in_refs` both ways; `node == 0`
and `node != 0`), and the script hard-errors if the plan degenerates (zero
derived-form probes, zero non-derived probes, or zero mask probes). The Requires
are satisfied by construction — they are only permission and
`len(selected) == len(summ)` side conditions, and the bridge builds both carriers
in lock-step from one annotation list. Each probe carries one decision-1
comparison plus one decision-2 comparison per name in the probe's alias universe
when the derived form was taken: **550794 shadow-vs-real comparisons** over the
100000 probes.

**Pinned seed: `SEED = 16263`** (module constant).

**Recorded verdict:** `G-CONF=pass` — 0 disagreements. Negative controls run
during construction (each mutation of the shadow FAILS the check, so it is
capable of refuting): the pre-patch decision-1 source (`selected` conjunct
dropped), the pre-patch truthiness predicate, the pre-patch decision-2
(`return True`, the unconditional `set_annotation_mask(self.annotation_select)`),
the `filter_summary` disjunct dropped, and the reference-scan hit disabled. Run
against the UNPATCHED `get_aggregation` the script exits non-zero
(`status=error`), never a silent pass.
