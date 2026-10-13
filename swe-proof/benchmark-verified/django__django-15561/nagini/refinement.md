# refinement.md — django__django-15561

The operation-by-operation correspondence between `model.py`'s implementation
(the deep models `schema_irrelevant_attrs` and `field_alteration_needed`, with
the pure `disagrees_relevant`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, proof uses the axiom's `Ensures`, and **A-reference**, a deep
model validated == the real operation by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This bundle has **no `@ContractOnly` axiom**: every operation the gold composes
is a Python language primitive (tuple membership, `dict.pop`, tuple `!=`), so
the two changed sites are modelled DEEPLY and validated against those primitives
(A-reference), not consumed as axioms.

## A. Site 1 — the schema-irrelevant attribute set (`Field.non_db_attrs`)

Gold hunk (`django/db/models/fields/__init__.py`), adds a class attribute:
```python
+ non_db_attrs = (
+     "blank", "choices", "db_column", "editable", "error_messages",
+     "help_text", "limit_choices_to",
+     "on_delete", "related_name", "related_query_name",
+     "validators", "verbose_name",
+ )
```

| # | model.py impl op (`schema_irrelevant_attrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `PSet(attr_choices(), attr_blank(), …, attr_verbose_name())` — the 12 attribute codes | the `non_db_attrs` tuple of 12 attribute-name strings | R | attribute name (`str`) ↔ attribute code (`int`); `tuple` (used only for membership while popping) ↔ `PSet[int]` (mapping.md §2). The set built is exactly the 12-element gold tuple. |
| A2 | postcondition `Ensures(Result() == PSet(attr_choices(), …, attr_verbose_name()))` — EXACT set equality — plus the redundant load-bearing membership `Ensures(attr_choices() in Result())` | the literal `non_db_attrs` tuple: `"choices"` plus the eleven legacy names, and NOTHING else | A-reference | the changed set is modelled DEEPLY (built explicitly); no axiom is consumed. Set EQUALITY pins the set in both directions: an implementation omitting any member (e.g. the pre-patch bug omitting `choices`) fails, and one ADDING a member (a schema-relevant attribute smuggled into the ignore-set, which would suppress required rebuilds and fail the P2P alter tests) fails too. G-AX (axiom_check.py) asserts the model's code set == the gold tuple's code set, with the enumeration attribute (`choices`) a member. |

The discriminating content — `choices` is a member of the schema-irrelevant set
— lives in the exact-set postcondition (and the redundant membership clause
`attr_choices() in Result()`). The pre-patch local list omitted `choices`;
`model_prepatch.py` reproduces that (the impl builds the set WITHOUT
`attr_choices()`) and **fails** the exact-set postcondition (the returned
11-code set is not equal to the pinned 12-code set), which is exactly the spec
sensing the change (G-DIFF).

## B. Site 2 — the rebuild decision (`_field_should_be_altered`)

Gold hunk (`django/db/backends/base/schema.py`), replaces the local list +
single loop with two per-field loops over the class attribute:
```python
- non_database_attrs = [ "blank", "db_column", … "verbose_name" ]   # (no "choices")
- for attr in non_database_attrs:
-     old_kwargs.pop(attr, None)
-     new_kwargs.pop(attr, None)
+ for attr in old_field.non_db_attrs:
+     old_kwargs.pop(attr, None)
+ for attr in new_field.non_db_attrs:
+     new_kwargs.pop(attr, None)
  return self.quote_name(old_field.column) != self.quote_name(new_field.column) or (
      old_path, old_args, old_kwargs) != (new_path, new_args, new_kwargs)
```

| # | model.py impl op (`field_alteration_needed`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `non_db: PSet[int]` parameter | `old_field.non_db_attrs` / `new_field.non_db_attrs` consumed in the loops | R | the schema-irrelevant set (site A's result) is passed in; both fields carry the SAME class attribute so the two loops strip the same key set (mapping.md §1). |
| B2 | `attrs: PSeq[int]`, `old_vals`/`new_vals: PSeq[int]` (aligned) | the two `dict`s `old_kwargs`, `new_kwargs` from `deconstruct()` | R | `dict` ↔ aligned key/value sequences; key absence ↔ a distinct ABSENCE value token (mapping.md §2). |
| B3 | `if other_differs: return True` | `quote_name(old.column) != quote_name(new.column)` (and the path/args part of the final tuple inequality) | R | `quote_name` is injective so column inequality is preserved; the non-kwarg structural comparison is summarised by `other_differs` (mapping.md §2). |
| B4 | the loop scanning for `not (attrs[i] in non_db) and old_vals[i] != new_vals[i]` → `disagrees_relevant` | strip `non_db_attrs` keys from both kwargs, then `old_kwargs != new_kwargs` on the residuals | A-reference | popping `k ∈ non_db_attrs` from both dicts ↔ excluding `attrs[i] ∈ non_db` from the disagreement scan; the residual dict inequality ↔ ∃ a remaining key whose values disagree (or present-on-one-side-only) = `disagrees_relevant`. Modelled DEEPLY; G-AX reconstructs the gold body over real `dict.pop`/tuple-`!=` and asserts equality on 9 boundary + 20 000 fuzz pairs. |
| B5 | `return other_differs or disagrees_relevant(...)` | `return <column-differs> or (<old residual tuple> != <new residual tuple>)` | I + R | Python `or` ↔ logical `or` (I); the operands are B3 (R) and B4 (A-reference). The bool result is the rebuild decision (`True` = alter needed). |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — that `choices` is now stripped before the residual comparison — is
modelled DEEPLY at two coupled sites: site A puts the enumeration attribute into
the schema-irrelevant set (`attr_choices() in Result()`), and site B excludes
every schema-irrelevant attribute from the disagreement scan
(`not (attrs[i] in non_db)`). There is **no consumed axiom**; the only trust
point beyond refinement fidelity is the A-reference equality `model ==
gold operation`, validated by G-AX.

Why one failing `model_prepatch` suffices: the entire observable change is "the
enumeration attribute joins the schema-irrelevant set." Site B's logic is
identical pre- and post-patch *given the set*; the gold's site-B edit only
re-sources the set from the per-field class attribute (a pure R-refactor with no
behavioural delta — both fields carry the same tuple). The single
independently-fixed behaviour therefore lives at site A, and `model_prepatch.py`
(the set built WITHOUT the enumeration attribute) fails on exactly the
exact-set postcondition (its 11-code result is not the pinned 12-code set,
whose distinguished missing member is `attr_choices()`). With the enumeration
attribute missing,
`field_alteration_needed` would (correctly, per its own spec) report a rebuild on
a choices-only change — the very SQL the issue says should not be generated.

## D. verify(model) ⇒ resolved

`schema_irrelevant_attrs` verifies only if its result IS the pinned 12-code set
— containing the enumeration attribute code and NOT containing any extra,
schema-relevant code (A-reference A2), and `field_alteration_needed` verifies only if
its result is exactly `other_differs or disagrees_relevant(...)` — the rebuild
decision that ignores any difference confined to the schema-irrelevant set (B4,
B5). By R (str↔code, dict↔aligned sequences, tuple↔set, injective `quote_name`)
the verified decision equals the gold `_field_should_be_altered` over
`field.non_db_attrs`; by G-AX the deep models equal the real gold operations
over 9 boundary + 20 000 fuzz field pairs (A-reference §3 of mapping.md),
including the F2P choices-only no-op in both directions. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited primitives — and the gold patch resolves (G-RESOLVE,
F2P `test_alter_field_choices_noop`). The trust points are exactly the two of
PLAN §1.1: A-reference soundness (G-AX) and refinement fidelity (this document,
G-EQ).
