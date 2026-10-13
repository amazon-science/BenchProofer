# refinement.md — django__django-13158

The operation-by-operation correspondence between `model.py`'s implementation
(the `mark_matching_nothing`, `duplicate`, `none`, `matches_nothing` impl
regions + the deep `all_marked` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses the axiom's `Ensures`, **A-reference** where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This is a **multi-site** change: two independently-fixed behaviours, one per
gold hunk, with one verification-failing `model_prepatch*` each.

## A. The emptying site — `Query.set_empty` (`query.py:1778`)

Gold hunk:
```
 def set_empty(self):
     self.where.add(NothingNode(), AND)
+    for query in self.combined_queries:
+        query.set_empty()
```

| # | model.py impl op (`mark_matching_nothing`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `q.where_empty = True` | `self.where.add(NothingNode(), AND)` | R | `where_empty` is the boolean abstraction of "the WHERE tree contains a `NothingNode`" = `is_empty()` (mapping.md §2). Adding a `NothingNode` makes `is_empty()` True ⟺ `where_empty := True`. The real `Node.add`/`NothingNode` are unchanged callees validated by axiom_check.py §(1) (**A-reference** for this op). |
| A2 | `while i < len(q.child_empty): q.child_empty[i] = True` | `for query in self.combined_queries: query.set_empty()` | R | each constituent `Query` is abstracted to its `is_empty()` flag `child_empty[i]` (mapping.md §2). `query.set_empty()` sets that constituent's own WHERE empty ⟹ its `is_empty()` becomes True ⟺ `child_empty[i] := True`. The recursion bottoms out at leaf constituents (the F2P scenario), so the per-element marking is the faithful observable of the descent. |

The discriminating content of this hunk — the constituents being marked empty —
is the `mark_matching_nothing` postcondition `Forall(k: q.child_empty[k] == True)`.
`model_prepatch.py` reverts `mark_matching_nothing` to set only `where_empty`
(no loop), exactly the pre-patch body, and **fails** that postcondition (the
spec sensing the missing recursion, G-DIFF).

## B. The copy site — `Query.clone` (`query.py:288`)

Gold hunk:
```
     else:
         obj.annotation_select_mask = self.annotation_select_mask.copy()
+    obj.combined_queries = tuple(query.clone() for query in self.combined_queries)
```
(`clone` otherwise builds `obj` from `self.__dict__.copy()`, line 296, which
shallow-shares `combined_queries`; the new line replaces that shared tuple with
an independently deep-cloned one.)

| # | model.py impl op (`duplicate`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `obj = Query(); obj.where_empty = q.where_empty` | `obj = Empty(); obj.__class__ = ...; obj.__dict__ = self.__dict__.copy()` (carries `where`/`where_empty` value across) | R | the copy starts with the source's own-emptiness value; modelled as copying the `where_empty` bool. The other `__dict__` fields are untouched by this instance and omitted (mapping.md §2). |
| B2 | loop `obj.child_empty.append(q.child_empty[i])` building a FRESH list with the same flags | `obj.combined_queries = tuple(query.clone() for query in self.combined_queries)` | R | each `query.clone()` is an INDEPENDENT constituent object; the abstraction is a fresh `child_empty` list, fully owned by `obj`, holding the same flags. Nagini full-ownership of `Result().child_empty` disjoint from `q.child_empty` is the type-level witness of "deep copy". |

The discriminating content of this hunk — the copy's constituents being
**independent** of the source — is carried by the permission accounting:
`duplicate`'s postcondition grants full `Acc(list_pred(Result().child_empty))`
while the source keeps its own half, which only a fresh list can satisfy.
`model_prepatch_2.py` reverts `duplicate` to `obj.child_empty = q.child_empty`
(the shallow alias, exactly the pre-patch `__dict__.copy()` sharing) and
**fails** with *insufficient permission to access `list_pred(Result().child_empty)`*
— the spec sensing the shared (non-independent) constituents (G-DIFF).

## C. The composite — `QuerySet.none` (`django/db/models/query.py:919`)

| # | model.py impl op (`none`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| C1 | `c = duplicate(q)` | `clone = self._chain()` (a `Query.clone()`) | I/R | `none` copies first; `_chain` clones the query. Under spec (the modelled `duplicate`), this is the same operation (its faithfulness is B1–B2). |
| C2 | `mark_matching_nothing(c)` | `clone.query.set_empty()` | I | empty the COPY, not the source — identical control flow; faithfulness is A1–A2. |
| C3 | `lemma_all_marked(ToSeq(c.child_empty))`; `return c` | `return clone` | I + proof-only | the lemma is a ghost step (no run-time effect) discharging `all_marked` from the elementwise flags; `return c` ⟺ `return clone`. |

`none`'s postconditions encode the exact F2P observable
(`test_union_none`): the returned copy matches nothing at every level
(`Result().where_empty == True` and `Forall(k: Result().child_empty[k] == True)`,
hence `all_marked` ⇒ the compound emits no rows, so `qs3.none() == []`), while
the **source is unchanged** (`q.where_empty == Old(q.where_empty)` and
`Forall(k: q.child_empty[k] == Old(q.child_empty[k]))`, so `qs3` still returns
`[0,1,8,9]`). The first family needs hunk A (recursion); the second needs hunk B
(independent copy). Both gold hunks are therefore required for `none` to verify.

## D. `all_marked` deep model (A-reference, NOT a consumed axiom)

| # | model.py construct | repo counterpart | tag | justification |
|---|---|---|---|---|
| D1 | `all_marked(flags)` (front-recursive: every constituent flag set) | `SQLCompiler.get_combinator_sql`: keeps only `combined_queries` with `not query.is_empty()`; `if not parts: raise EmptyResultSet` (`compiler.py:437,475-476`) | A-reference | the changed structural property is modelled **deeply** (`all_marked` spelled out, plus the per-element `child_empty` loop). There is **no consumed axiom**: the `axioms` region is empty. `all_marked` is validated against the real semantics by axiom_check.py / G-AX (real `WhereNode`/`NothingNode` `is_empty`, and the gold `clone`/`set_empty` data flow), not consumed as a contract. |

## E. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operations that genuinely
*changed* — `set_empty`'s constituent recursion and `clone`'s constituent
deep-copy — are modelled **deeply** (verified loops over `child_empty` whose
independence is enforced by Nagini's permission system), not hidden behind any
axiom about the functions under change. The only repo callees the new code
*invokes* (`WhereNode.add` / `NothingNode`, both unchanged) appear only as the
**A-reference** the deep model's `where_empty`/`is_empty` observable is validated
against by G-AX. No `@ContractOnly` is shipped; nothing is dead or mislabelled.

## E2. Termination obligations (total correctness)

| # | model.py construct | repo counterpart | tag | justification |
|---|---|---|---|---|
| E2.1 | `Requires(MustTerminate(...))` on `matches_nothing` (2), `mark_matching_nothing` (2), `duplicate` (3), `none` (len+4), `Query.__init__` (2), ghost `lemma_all_marked` (len+1); loop `Invariant(MustTerminate(len - i + 1))` in the two constituent passes | the real `is_empty` / `set_empty` / `clone` / `QuerySet.none` are bounded computations that always return to their caller (a finite scan, one `add` plus a finite descent, one dict copy plus a finite tuple build, a three-statement composite) | R | total-correctness obligation: the real operations always ANSWER. Nagini verifies partial correctness by default, so without the obligation a diverging or self-recursive same-spec impl satisfies every `Ensures` vacuously (the audited G-PANEL-1 counterexample). The measures are strictly layered (`none` > `duplicate`/`mark_matching_nothing` > builtin steps), so each routine may call its helpers but cannot re-invoke itself; the loops consume the obligation with the decreasing, bounded-below measure `len - i`. |

## F. verify(model) ⇒ resolved

`set_empty` verifies only if it marks every constituent empty (A2), and `clone`
verifies only if the copy's constituents are an independent list (B2); `none`
verifies only if BOTH hold (copy empty everywhere AND source untouched, C). By R
(WHERE-tree ↔ `where_empty` via the unchanged `NothingNode`/`is_empty`
observable; constituent `Query` ↔ its `is_empty()` flag; deep copy ↔ fresh
owned list; recursion ↔ per-element marking) the verified model equals the gold
patch's `clone`/`set_empty`, composed by `none`, on the tested inputs; G-AX
validates the deep model == the real Django semantics (D1, the A-reference).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited (unchanged) callees — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom/
deep-model soundness (G-AX) and refinement fidelity (this document, G-EQ).
