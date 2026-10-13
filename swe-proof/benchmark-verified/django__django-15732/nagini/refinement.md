# refinement.md — django__django-15732

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_constraint_to_remove` impl region and the `disambiguates` pure
helper) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized/abstracted callee — split into **A-consumed**,
where the proof uses a `@ContractOnly` axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real changed operation by
`axiom_check.py` / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, performs the gold patch's constraint selection on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The selection site — `_delete_composed_index` (`schema.py:559`)

The gold changes the body of `_delete_composed_index` between discovering the
candidate set and the `len(constraint_names) != 1` check (gold hunk 2):

```
  constraint_names = self._constraint_names(model, columns, exclude=…, **constraint_kwargs)
+ if (
+     constraint_kwargs.get("unique") is True
+     and constraint_names
+     and self.connection.features.allows_multiple_constraints_on_same_fields
+ ):
+     default_name = str(self._unique_constraint_name(model._meta.db_table, columns, quote=False))
+     if default_name in constraint_names:
+         constraint_names = [default_name]
  if len(constraint_names) != 1:
      raise ValueError("Found wrong number (%s) of constraints …")
  self.execute(self._delete_constraint_sql(sql, model, constraint_names[0]))
```

| # | model.py impl op (`select_constraint_to_remove`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | input `candidates: List[int]` | `constraint_names` (`list[str]`) from `self._constraint_names(...)` | R | `list[str]` ↔ `List[int]` of name ids; only equality/membership/length/`[0]` are observable in the selection (mapping.md §2, §3.1). The discovery callee is unchanged; its result is the input. |
| A2 | input `default_name: int` | `str(self._unique_constraint_name(table, columns, quote=False))` | R | the composed rule's default name as one id; an unchanged deterministic name computation (mapping.md §3.2). Passed in as input. |
| A3 | input `unique: bool` | `constraint_kwargs.get("unique") is True` | R | identity; for `alter_unique_together` the kwargs carry `unique=True` (gold hunk 1). |
| A4 | input `feature_on: bool` | `self.connection.features.allows_multiple_constraints_on_same_fields` | R | identity (mapping.md §2). |
| A5 | `disambiguates(unique, feature_on, len(candidates))` = `unique and feature_on and len(candidates) >= 1` | the `if (… unique is True and constraint_names and …features.allows_multiple…)` guard | I (under R of A1/A3/A4) | `constraint_names` truthiness ⇔ `len(candidates) >= 1`; the boolean `and`-chain is identical. |
| A6 | `if default_name in ToSeq(candidates): narrowed_to_default = True` | `if default_name in constraint_names: constraint_names = [default_name]` | R + I | `in` membership refines `str`-membership to id-membership (A1/A2); setting `narrowed_to_default` ⇔ replacing the list with the one-element `[default_name]` — observationally identical for the subsequent count check and `[0]` access (mapping.md §2). |
| A7 | `if narrowed_to_default: return default_name` | (the narrowed `constraint_names == [default_name]` then `len == 1`, so `constraint_names[0] == default_name` is deleted) | R + I | after narrowing the sole element is `default_name`; returning it ⇔ deleting `constraint_names[0]`. |
| A8 | `if len(candidates) == 1: return candidates[0]` | `if len(constraint_names) != 1: raise …` else delete `constraint_names[0]` | R + I | when not narrowed, the surviving set must have exactly one element to proceed; that element `candidates[0]` is the deleted name. |
| A9 | `raise WrongConstraintCount()` | `raise ValueError("Found wrong number …")` | R | user-defined exception ↔ the `ValueError` (builtin-exception `Exsures` crashes Nagini; mapping.md §1). The raise CONDITION matches: not narrowed AND `len != 1`. |
| A10 | `return Result()` (the selected name) | `self.execute(self._delete_constraint_sql(sql, model, constraint_names[0]))` | R | the only observable of the delete is WHICH name is targeted; modeled as the returned name. The SQL build/execute is an unchanged downstream op (mapping.md §2). |

The whole changed selection is modeled **deeply** (A5–A9 spelled out over the
modelled carrier); there is no consumed `@ContractOnly` axiom. The deep model is
validated **== the gold selection algorithm** out-of-band by G-AX
(`axiom_check.py`, `gold_select == model_select` on 72 boundary + 200 000 fuzz
inputs) — an **A-reference** (mapping.md §3.3).

## B. The supporting hunks (gold hunks 1, 3, 4) — refactor + filter

These three hunks set up the inputs the selection consumes; they introduce no
new observable selection logic beyond A1–A10.

- **Hunk 1** (`alter_unique_together`, `schema.py:528–532`): the delete kwargs
  become `{"unique": True, "primary_key": False}` (was `{"unique": True}`). Tag
  **R+I**: this only changes the FILTER passed to the unchanged `_constraint_names`
  (mapping.md §3.1), so the discovered `candidates` exclude PK constraints. In
  the model this is reflected purely in the `candidates` input (the pk-field
  scenario then yields a single `_uniq` candidate; axiom_check.py boundary case
  `[UNIQ]`).
- **Hunk 3** (`_create_unique_sql`, `schema.py:1563–1577`): the inline
  `create_unique_name` closure + `IndexName(...)` is replaced by a call to the
  new `_unique_constraint_name(table, columns, quote=True)` helper. Tag **R+I**:
  a pure extraction; `name` is byte-identical to before (`quote=True` reproduces
  the old closure). No observable change; not modeled (it is the create path,
  not the delete-selection under spec).
- **Hunk 4** (new `_unique_constraint_name`, `schema.py:1606–1616`): the helper
  itself. With `quote=False` it yields the unquoted default `_uniq` name —
  exactly the `default_name` input the selection (A2/A6) consumes. Tag **R**:
  an unchanged deterministic name computation surfaced as the `default_name`
  input (mapping.md §3.2).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the disambiguating selection of the constraint to delete — is
modeled **deeply** (A5–A9, the spelled-out narrowing + count logic in
`select_constraint_to_remove`), not hidden behind an axiom about the function
under change. There is **no consumed `@ContractOnly` axiom**. The unchanged
operations the selection relies on (`_constraint_names`,
`_create_index_name`/`_unique_constraint_name`) are surfaced as INPUTS
(`candidates`, `default_name`), and the deep model is validated == the real
changed selection by G-AX (A-reference, mapping.md §3.3).

## D. The differential witness (G-DIFF)

The discriminating content of the change is: when a uniqueness removal is
performed on a column that ALSO carries an independent single-column uniqueness
constraint, the candidate set holds two names (the composed rule's `_uniq` and
the independent `_key`); the rule's own default `_uniq` name must be selected,
not a raise. `model_prepatch.py` reproduces the pre-patch skeleton — no
narrowing, straight to `if len(candidates) == 1 else raise` — and **fails** the
`Exsures(WrongConstraintCount, … and not (disambiguates(…) and default_name in
ToSeq(candidates)))` clause: on a two-candidate set containing the default with
`unique` and `feature_on`, the prepatch raises, but the spec forbids raising
there (it requires returning `default_name`). That is exactly the spec sensing
the missing disambiguation. This is the F2P case
`test_remove_unique_together_on_unique_field`; the P2P case
`test_remove_unique_together_on_pk_field` is the single-`_uniq`-candidate path
(A8), enabled by hunk 1's `primary_key=False` filter.

### D.1 Spec-strength: the normal-return domain (the `verify ⟹ correct` guard)

The `Exsures` above states only a *necessary* condition for raising; on its own
it does not FORBID a wrong impl from silently returning an arbitrary discovered
candidate (e.g. `candidates[0]`) on a non-resolvable set — precisely the
arbitrary-constraint deletion the issue forbids. The post-conditions therefore
also carry a positive normal-return-domain clause:

```
Ensures((disambiguates(unique, feature_on, len(candidates))
         and (default_name in ToSeq(candidates)))
        or (len(candidates) == 1))
```

This pins that a normal return is permitted ONLY when the discovered set
actually reduces to exactly one candidate (disambiguation narrows it to the
default, or it already holds one), making the refusal **required** in every
other case. It is grounded entirely in structural predicates over the actual
input carrier — `disambiguates` over `len(candidates)`, membership of
`default_name` in `ToSeq(candidates)`, and `len(candidates) == 1` — with no
oracle (SPEC_GUIDE directive 8). The faithful gold skeleton (A5–A9) satisfies it
because it returns only `default_name` (narrowed path) or the sole `candidates[0]`
(count-one path) and otherwise raises. A wrong impl that returns `candidates[0]`
on the disambig-non-member multi-candidate path is rejected at exactly this
clause. Applied identically to `model.py` and `model_prepatch.py` (same_spec).

## E. verify(model) ⇒ resolved

`select_constraint_to_remove` verifies only if, on the disambiguation path, it
returns the rule's default name (A6/A7) and on the sole-candidate path returns
that candidate (A8), and raises exactly when neither resolves (A9). By R (str ↔
id, list-narrowing ↔ flag, delete-target ↔ returned name) and A-reference (the
deep model == the gold selection, G-AX over 200 000 fuzz inputs), the verified
selection equals the gold patch's selection on every input — in particular the
F2P/P2P scenarios. The gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom/A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
