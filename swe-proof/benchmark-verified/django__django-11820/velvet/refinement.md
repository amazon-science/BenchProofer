# refinement.md — django__django-11820

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`checkOrderingRef` `do` block + the deep `stepWalk`/`orderingRefInvalid` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I; no kind-3 (changed inexpressible op).

There are **NO axioms** in this bundle: the three schema accessors are free
inputs (mapping.md §2/§3), so no row is A-consumed or A-reference, and G-AX is
`skip`. The whole impl region is R/I, mechanically refuted by **G-CONF**
(`conformance_check.py`); the narrative below is audited by G-EQ.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The walk site — `_check_ordering`'s related-reference loop (`django/db/models/base.py:1705-1721`)

Gold hunk (the changed lines):
```
-                    fld = _cls._meta.get_field(part)
+                    # pk is an alias that won't be found by opts.get_field.
+                    if part == 'pk':
+                        fld = _cls._meta.pk
+                    else:
+                        fld = _cls._meta.get_field(part)
                     if fld.is_relation:
                         _cls = fld.get_path_info()[-1].to_opts.model
+                    else:
+                        _cls = None
```

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `cls0 : Model`, seed `initState cls0 = (some cls0, none, false)` | `_cls = cls; fld = None` (loop pre-state) before `for part in field.split(LOOKUP_SEP)` | R | `_cls` ↔ `Option Model` (`None` = off the model graph), `fld` ↔ `Option Field`, the appended-error flag ↔ `Bool`. mapping.md §2. |
| 2 | `while i < parts.length … st := stepWalk … st parts[i]!` (forward fold of `stepWalk` over `parts`) | `for part in field.split(LOOKUP_SEP):` body | I | one loop iteration per part; the backward-equivalent `take`-fold computes the same `foldl`. The proof's `walk_take_step` lemma is the per-step unfold. |
| 3 | `match cur with \| none => (none, last, flag ‖ flagOnUnresolved …)` | when `_cls` is `None`: `get_field` raises `AttributeError` (`None._meta`) → `except` branch | R | a part cannot resolve once off the model graph; the except-branch then flags unless the part is a registered transform of `fld`. `flagOnUnresolved` models `fld is None or fld.get_transform(part) is None`. |
| 4 | `if p.isAlias then let f := aliasField m; (if f.isRel …)` | `if part == 'pk': fld = _cls._meta.pk` then the `is_relation` branch | R + I | the **first** fixed behavior: the alias part resolves through `aliasField` (= `_cls._meta.pk`), never failing. `isAlias ↔ part == 'pk'`. mapping.md §4.1. |
| 5 | `else match lookup m p with \| some f => (if f.isRel then some f.relModel else none, some f, flag)` | `else: fld = _cls._meta.get_field(part)`; `if fld.is_relation: _cls = fld.get_path_info()[-1].to_opts.model` `else: _cls = None` | R + I | the **second** fixed behavior: on a non-relation field the chain steps off the model graph (`_cls = None`, modeled `none`); on a relation it descends to `relModel`. `lookup` ↔ `get_field` (resolves vs raises). mapping.md §4.2. |
| 6 | `\| none => (some m, last, flag ‖ flagOnUnresolved hasTransform last p)` | `except (FieldDoesNotExist, AttributeError): if fld is None or fld.get_transform(part) is None: errors.append(E015)` | R + I | a part `get_field` cannot resolve raises `FieldDoesNotExist`; `_cls` is unchanged (`some m`) and the reference is flagged unless `fld` is a registered transform host. `hasTransform f p ↔ f.get_transform(part) is not None`. |
| 7 | `return st.2.2` (the final flag) | "an `E015` error was appended for this reference" | R | the modeled observable is exactly *did this reference raise E015* — what both F2P tests assert (`Child.check()` equals `[Error(... E015)]` vs `[]`). |

### Why the spec sees each bug (G-DIFF)

- **prepatch_1** drops row 4's alias branch (always uses `lookup`). For an alias
  part, `lookup` returns `none` (the alias is not a plain field) → the reference
  is flagged. The frozen spec's `stepWalk` routes the alias through `aliasField`
  (resolves, no flag). The loop-body invariant `st = (take …).foldl stepWalk …`
  becomes unprovable → `prove_correct` fails. (`parent__pk` ⇒ wrongly invalid.)
- **prepatch_2** keeps `some m` after a non-relation field (row 5's `else`
  branch returns `some m` instead of `none`). The frozen `stepWalk` returns
  `none`. A following part then diverges (resolves against `m` instead of being
  unable to resolve) → invariant unprovable → `prove_correct` fails.
  (`parent__field1__field2` ⇒ wrongly valid.)

Both prepatches share the byte-identical spec (G-DIFF `same_spec`); each fails on
the `stepWalk` loop-body clause, the discriminating content of its bug.

## No kind-3

Every changed op is expressible: the patch is pure control-flow rerouting over
the abstracted accessors. Nothing inexpressible; no BLOCKED.
