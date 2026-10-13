# mapping.md — django__django-13158

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7af8f4127397279d19ef7c7899e93018274e2f9b`, states the type
abstraction, and records callee provenance. This bundle consumes **no
`@ContractOnly` axiom** — the change is pure object/structure logic, modelled
deeply; the structural facts the deep model rests on are validated against the
real Django runtime by `axiom_check.py` (G-AX).

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| class `Query` (fields `where_empty`, `child_empty`) | `django.db.models.sql.query.Query` — `query.py:136`; touched fields are the WHERE tree `self.where` (`query.py` constructor) and `self.combined_queries` (`query.py:210`) | the query object under change, abstracted to its two touched aspects |
| `matches_nothing(q)` | `Query.is_empty` — `query.py:1781` (`return any(isinstance(c, NothingNode) for c in self.where.children)`) | unchanged observation: does the query's own WHERE force the empty result (model symbol named off the repo name `is_empty` to keep the spec view leakage-clean, G-LEAK) |
| `mark_matching_nothing(q)` | `Query.set_empty` — `query.py:1778` (changed hunk) | the changed emptying operation (now recurses into `combined_queries`); model symbol named off the repo name `set_empty` to keep the spec view leakage-clean (G-LEAK) |
| `duplicate(q)` | `Query.clone` — `query.py:288` (changed hunk, new line at 308) | the changed lightweight copy (now deep-copies `combined_queries`); model symbol renamed off the repo name to keep the spec view leakage-clean (G-LEAK) |
| `none(q)` | `QuerySet.none` — `django/db/models/query.py:919` (`clone = self._chain(); clone.query.set_empty(); return clone`) | the public composite that copies then empties; the F2P-observed behaviour |
| `all_marked(flags)` | the compound-result emptiness condition read by `SQLCompiler.get_combinator_sql` — `compiler.py:437,475-476` (`for query in self.query.combined_queries if not query.is_empty()`; `if not parts: raise EmptyResultSet`) | pure spec: every constituent matches-nothing ⇒ the compound matches nothing |

Pre-patch repo state the change fixes (for the refinement audit, not referenced
from the consumer spec view): `Query.set_empty` (`query.py:1778-1779`) added a
`NothingNode` to the outer WHERE only; `Query.clone` (`query.py:288-336`) left
`combined_queries` as the shallow `self.__dict__.copy()` alias of the source's
tuple (line 296), so it was shared between source and copy.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.where` (a `WhereNode` tree) and `Query.is_empty()` over it | `where_empty: bool` | `where_empty == True` ⟺ `self.where.children` contains a `NothingNode` ⟺ `is_empty()` returns `True`. `set_empty`'s `self.where.add(NothingNode(), AND)` ⟺ `where_empty := True` (idempotent: adding more `NothingNode`s keeps `is_empty()` True). Validated against the real `WhereNode`/`NothingNode` by axiom_check.py §(1). |
| `self.combined_queries` (a `tuple` of constituent `Query` objects) | `child_empty: List[bool]` | one bool per constituent = that constituent's `is_empty()`. The ONLY constituent property the compound result reads is `query.is_empty()` (`compiler.py:437`), so a constituent is faithfully abstracted by its matching-nothing flag. `len(combined_queries)` ⟺ `len(child_empty)`; constituent order preserved. |
| `tuple(query.clone() for query in self.combined_queries)` (deep copy) | building a FRESH `List[bool]` by copying each flag into a new list owned by the result | a deep-copied constituent is an independent object; the abstraction is an independent `child_empty` list (full Nagini ownership of `Result().child_empty`, disjoint from `q.child_empty`). The shallow (pre-patch) alias ⟺ `obj.child_empty = q.child_empty` (shared permission — unprovable, see refinement.md). |
| `for query in self.combined_queries: query.set_empty()` (recursive descent) | loop setting each `child_empty[i] := True` | the F2P scenario's constituents are leaves (`combined_queries == ()`), so the real recursion bottoms out in one level; the model's per-element marking captures the observable (each constituent's `is_empty()` becomes True). |
| `QuerySet.none()` = `_chain()` (a clone) then `query.set_empty()` | `none(q)` = `duplicate(q)` then `mark_matching_nothing(...)` | `_chain` clones the query (`Query.clone()`); the model composes the two modelled functions exactly. |

`str`/rich-object graphs are banned/intractable in Nagini, so the constituent
sequence is carried as `List[bool]` (its observable emptiness vector) with
specification phrased over `PSeq[bool]` via `ToSeq`.

## 3. Callee provenance — NO consumed axioms

There is **no `@ContractOnly` axiom** in `model.py` (the `axioms` region is
empty). The two changed operations are Django's own object logic, modelled
deeply:

- `set_empty`'s recursion and `clone`'s deep-copy are spelled out as verified
  loops over `child_empty` (model.py impl regions). Their faithfulness to the
  real `Query.set_empty` / `Query.clone` data flow is audited by refinement.md
  (G-EQ) and validated executably by axiom_check.py / G-AX, which transcribes
  the gold patch's `clone` / `set_empty` bodies VERBATIM over the real
  `WhereNode`/`NothingNode` emptiness observable.

- The only repo callees the changed code invokes are
  `WhereNode.add(NothingNode(), AND)` (via `django.utils.tree.Node.add`,
  `tree.py:78`) and `NothingNode` (`where.py:209`), both **unchanged** and used
  only to realise the `where_empty`/`is_empty` boolean the model abstracts.
  axiom_check.py §(1) runs the real ones: a fresh `WhereNode` is not empty;
  after `add(NothingNode(), AND)` it is, monotonically. No flag dependencies.

**Soundness check (G-AX):** `axiom_check.py` imports only the standard library
plus `django.db.models.sql.where` (the very layer the patch calls) and that
layer's transitive imports (`django.utils.tree`, `asgiref`, `pytz`); it requires
no database connection or settings configuration. It checks the real `is_empty`
observable, then drives a
faithful `RealQuery` whose `clone`/`set_empty` are the gold patch verbatim over
real `WhereNode` emptiness, asserting (over 6 boundary + 5000 fuzz compound
shapes) that `none()` empties the copy at every level and leaves the source
intact, and that both pre-patch skeletons violate exactly the clauses the two
`model_prepatch*` files fail on. Exit 0 iff sound.

## 4. Termination (total correctness)

Every modelled operation in the real repo is a bounded computation that always
returns to its caller: `Query.is_empty` is a finite `any(...)` scan,
`Query.set_empty` is one `WhereNode.add` plus one pass over the finite
`combined_queries` tuple, `Query.clone` is one `__dict__.copy()` plus one pass
building the deep-cloned tuple, and `QuerySet.none` is `_chain()` +
`set_empty()` + `return clone`. The model carries this as
`Requires(MustTerminate(...))` on each contracted function (Nagini is a
partial-correctness verifier by default, so without the obligation a
non-terminating implementation — bare self-recursion or an endless loop —
would satisfy every `Ensures` vacuously). The measures are strictly layered so
each routine may invoke its helpers but may NOT re-invoke itself:
`none` carries `len(child_empty) + 4`, exceeding `duplicate`'s 3 and
`mark_matching_nothing`'s 2, which exceed `Query()`'s 2 / the builtin steps;
the ghost `lemma_all_marked` recurses on `len(s) + 1` (the tail is strictly
shorter). The constituent loops discharge the obligation with the decreasing,
bounded-below measure `len - i`. Verified during repair: self-recursive and
endless-loop same-spec rivals of `none`, `duplicate`, and
`mark_matching_nothing` are all rejected, while `model.py` still verifies.
