# refinement.md — django__django-15268

The operation-by-operation correspondence between `model.py`'s implementation
(`commutes_through`, `pair_collapses_through`, and the deep `pure`-region
decision functions) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). **There are no axioms** in this bundle,
hence no A-consumed and no A-reference rows: the changed operation is a pure
boolean computation, modelled deeply, so every row is R or I.

## A. The extracted base predicate — gold hunk 1 (`models.py:34-42`)

Gold hunk:
```
 def reduce(self, operation, app_label):
     return (
         super().reduce(operation, app_label) or
-        not operation.references_model(self.name, app_label)
+        self.can_reduce_through(operation, app_label)
     )

+def can_reduce_through(self, operation, app_label):
+    return not operation.references_model(self.name, app_label)
```

This hunk is a **pure refactor**: `reduce`'s boolean fallback is extracted into
a `can_reduce_through` method whose body is *byte-for-byte* the old expression
`not operation.references_model(self.name, app_label)`. It changes no behaviour
on its own; it creates the override point hunk B uses.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `base_commutes_through(self_model, other_kind, other_model) == not touches_model(other_model, self_model)` | `can_reduce_through` body `not operation.references_model(self.name, app_label)` | R | `references_model(name)` for these model-scoped operations is `name.lower() == self.name_lower`, modelled as `touches_model(op_model, name) == (op_model == name)` (mapping.md §2). `app_label` is unused. |
| A2 | `commutes_through` returns the constraint-altering rule (hunk B), the boolean path of `reduce` | `reduce` returns `super().reduce(...) or self.can_reduce_through(...)` | R + I | `super().reduce()` (`Operation.reduce`) is `False` for these non-elidable operations (mapping.md §2), so the boolean path equals `can_reduce_through` — the `or False` is the identity. The dispatch to the overriding `can_reduce_through` is type-resolved by `kind` (mapping.md §2). |

## B. The different-family allowance — gold hunk 2 (`models.py:531-540`)

Gold hunk (added to `AlterTogetherOptionOperation`):
```
+def can_reduce_through(self, operation, app_label):
+    return (
+        super().can_reduce_through(operation, app_label) or (
+            isinstance(operation, AlterTogetherOptionOperation) and
+            type(operation) is not type(self)
+        )
+    )
```

This is the behavioural core: a constraint-altering operation may additionally
commute through a *same-model* neighbour that is itself a constraint-altering
operation of a **different concrete family**.

| # | model.py impl op (`commutes_through`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `if not touches_model(other.model_id, self_op.model_id): return True` | `super().can_reduce_through(operation, app_label)` (= `not operation.references_model(self.name, app_label)`) | R | the base clause from hunk A, dispatched via `super()`; `references_model` ↔ `touches_model` (mapping.md §2). |
| B2 | `return is_constraint_alteration(other.kind) and other.kind != self_op.kind` | `isinstance(operation, AlterTogetherOptionOperation) and type(operation) is not type(self)` | R | `isinstance(operation, AlterTogetherOptionOperation)` ↔ `is_constraint_alteration(other.kind)` (`other.kind >= 0`); `type(operation) is not type(self)` ↔ `other.kind != self_op.kind` (the two subclasses carry distinct family tags 0/1) (mapping.md §2). The `super() or (...)` short-circuit ↔ the `if base: True else (...)` control flow (I). |
| B3 | the spec `alter_commutes_through(self_kind, self_model, other_kind, other_model) == base_commutes_through(...) or (is_constraint_alteration(other_kind) and other_kind != self_kind)` | the whole `can_reduce_through` body | R + I | the modelled decision is exactly the gold body under the §2 bijection; the verified impl returns it (postcondition `Result() == alter_commutes_through(...)`). |

## C. The optimizer consequence — `pair_collapses_through` (`optimizer.py:40-69`)

The optimizer scans operations and, when it finds a reducible pair `(first,
second)` separated by `between`, performs the left reduction iff every
in-between operation can be commuted through `second`
(`all(op.reduce(other, app_label) is True for op in in_between)`,
`optimizer.py:53`). For the redundant same-family pair the fix targets, the
single in-between step is the cross-family alteration.

| # | model.py impl op (`pair_collapses_through`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| C1 | the in-between commute decision, inlined: `if not touches_model(second.model_id, between.model_id): res = True else: res = is_constraint_alteration(second.kind) and second.kind != between.kind` | `between.reduce(second, app_label) is True`, where `between.reduce` dispatches to `AlterTogetherOptionOperation.can_reduce_through` | I | the inlined body is the *same decision* as `commutes_through(between, second)` (identical concrete computation; the inline avoids a Nagini cross-call framing artefact, not a semantic change — see note). The optimizer's `is True` comparison ↔ the returned `bool`. |
| C2 | postcondition `Result() == (between.kind != first.kind)` | the pair collapses (4 ops → 2) exactly when `between` is the cross-family step | R + I | given `first`/`second` are the same family on the same model and `between` is a constraint-altering operation on that model, the base clause is false (same model) so the decision equals "different family from the pair" (`second.kind == first.kind`, so `between.kind != second.kind == between.kind != first.kind`). This is the observable the F2P tests check: the four-step sequence reduces to two. |

**Inline note (C1):** `pair_collapses_through` inlines the in-between operation's
own commute decision rather than calling `commutes_through`. The inlined code is
byte-equivalent to `commutes_through`'s body applied to `(between, second)`; the
inline is a Nagini proof-engineering choice (a method call across which the
verifier havocs heap-dependent pure-function values), not a behavioural
deviation. Under the refinement this is the optimizer evaluating
`between.reduce(second, app_label)`, i.e. the patched `can_reduce_through`.

## D. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step above is R or I. The operation that genuinely *changed* — the
different-family commute allowance — is modelled **deeply** (the spelled-out
boolean `is_constraint_alteration(other.kind) and other.kind != self_op.kind`),
not behind any axiom. There is no `@ContractOnly` in the bundle: `references_model`
and `super().can_reduce_through` are themselves trivial equality tests modelled
deeply, and the surrounding optimizer loop is unchanged context. Hence no
A-consumed and no A-reference rows, and no G-AX obligation.

## E. verify(model) ⇒ resolved

`commutes_through` verifies only if its result equals `alter_commutes_through`
(B3), which forces the different-family allowance (postcondition clause
`Implies(is_constraint_alteration(other.kind) and other.kind != self_op.kind,
Result())`). `pair_collapses_through` verifies only if the redundant pair
collapses exactly on the cross-family in-between step (C2). By R (class tag ↔
`kind`, model name ↔ `model_id`, `references_model` ↔ `touches_model`,
`super().reduce()` is `False`) the verified decision equals the gold
`can_reduce_through`/`reduce` on the operations the optimizer feeds it.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE: the F2P
autodetector tests now expect the collapsed two-operation sequences). The
pre-patch skeleton (base rule only, no different-family allowance) fails exactly
the `Result() == alter_commutes_through(...)` clause in BOTH functions (G-DIFF),
which is the spec sensing the bug. The only trust point that remains is
refinement fidelity (this document, G-EQ); there is no axiom-soundness trust
point because there are no axioms.
