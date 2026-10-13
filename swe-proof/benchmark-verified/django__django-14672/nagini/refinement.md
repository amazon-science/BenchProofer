# refinement.md — django__django-14672

The operation-by-operation correspondence between `model.py`'s implementation
(the `identity_name_component` impl region and the deep `canonical_names` /
`canonical_items` / `is_hashable` model) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The identity through-fields slot — `ManyToManyRel.identity` (`django/db/models/fields/reverse_related.py:313`)

Gold hunk:
```
     def identity(self):
         return super().identity + (
             self.through,
-            self.through_fields,
+            make_hashable(self.through_fields),
             self.db_constraint,
         )
```

| # | model.py impl op (`identity_name_component`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `names: Optional[List[int]]` | `self.through_fields` (`Optional[list/tuple of str]`) | R | `Optional[list of str]` ↔ `Optional[List[int]]`; each name string ↔ an `int` atom; `None` ↔ `None` (mapping.md §2). |
| A2 | `if names is None: return Value(KIND_ABSENT, ...)` | `make_hashable(None)` → `None` | A-reference | `make_hashable` is modeled deeply: `hash(None)` succeeds, so the absent value passes through unchanged and is hashable. The deep model (`canonical_names(None) == KIND_ABSENT`, `is_hashable` true) is validated == the real callee by G-AX (mapping.md §3.1). |
| A3 | `return Value(KIND_IMMUTABLE, ToSeq(names))` | `make_hashable(self.through_fields)` for the present-list case | A-reference | the changed operation is modeled **deeply**: a present sequence canonicalises to the immutable (hashable) form carrying the same names in the same order. There is **no consumed axiom** — the deep model (`canonical_names(list) == KIND_IMMUTABLE`, `canonical_items == ToSeq(names)`, `is_hashable` true) is validated **== the real `make_hashable`** by G-AX (axiom_check.py): a `list` is not hashable, so `make_hashable` returns `tuple(map(make_hashable, value))`, and each name is an already-hashable `str` left untouched ⇒ same names, in order, as a hashable tuple (mapping.md §3.1). |
| A4 | the value joins the identity tuple (the slot the function returns) | `super().identity + ( self.through, <slot>, self.db_constraint, )` | R / I | the surrounding tuple concatenation and the unchanged neighbouring components (`self.through`, `self.db_constraint`, the `super().identity` prefix) are unchanged by the patch and already hashable; only the through-fields slot changed, so only it is modeled. The identity is hashable iff every slot is — captured by the `is_hashable(Result())` postcondition on the modeled slot. |

The discriminating content of the change — the through-fields slot must be
**hashable** (so `hash(self.identity)` does not raise) while preserving the
names — lives in `Value(KIND_IMMUTABLE, ...)` with `is_hashable` true (model)
⇔ `make_hashable(self.through_fields)` (real). The pre-patch carried the raw
list into the identity; `model_prepatch.py` reproduces that
(`Value(KIND_MUTABLE, ToSeq(names))`) and **fails** the postcondition
`is_hashable(Result())`, which is exactly the spec sensing the change (G-DIFF):
`is_hashable(KIND_MUTABLE) == False`, modeling `TypeError: unhashable type:
'list'`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I/R. The one operation that genuinely
*changed* — wrapping the through-fields slot with the canonicaliser — is
modeled **deeply** (the spelled-out `canonical_names` / `canonical_items`
functions and the `is_hashable` property over the `Value` carrier, an
**A-reference**), not hidden behind an axiom about the operation under change:
there is **no consumed `make_hashable` `@ContractOnly` axiom** (the axioms
region is empty). The unchanged stdlib/Django callee `make_hashable` appears
only as the **A-reference** that G-AX validates the deep model against. No
axiom is consumed, so there is no A-consumed row.

## C. verify(model) ⇒ resolved

`identity_name_component` verifies only if the slot it produces is hashable
(A3/A2, `is_hashable(Result())`) and preserves the names in order
(`Result().items == canonical_items(names)`, `Result().kind ==
canonical_names(names)`). By R (Optional[list of str] ↔ Optional[List[int]],
the unchanged neighbouring tuple components) the verified slot equals
`make_hashable(self.through_fields)` on the tested inputs; by G-AX the deep
model equals the real `make_hashable` (A-reference). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE).
The trust point is exactly one of the two of PLAN §1.1: refinement fidelity
(this document, G-EQ); axiom soundness reduces to the single A-reference check
(G-AX), since no axiom is consumed.

Why equal relations hash equally (the F2P
`test_reverse_inherited_m2m_with_through_fields_list_hashable`,
`hash(reverse_m2m) == hash(inherited_reverse_m2m)`): two relations whose
through-fields collections are element-wise equal produce equal canonical
components (`canonical_names` + `canonical_items` are functions of the names
only), hence equal identity tuples, hence equal hashes — and, crucially, both
hashes are now *computable* (no `TypeError`), which the pre-patch could not do.
