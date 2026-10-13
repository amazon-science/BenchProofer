# refinement.md — django__django-11820

The operation-by-operation correspondence between `model.py`'s implementation
(the `check_related_path` impl region and the deep `walk_err` fold) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model is validated == the real callee by axiom_check.py / G-AX, NOT consumed as
a value axiom), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, computes the same per-path E015 verdict as the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed inner loop — `_check_ordering` (`django/db/models/base.py:1709-1723`)

Gold hunk (the per-name body inside `for part in field.split(LOOKUP_SEP)`):
```
- fld = _cls._meta.get_field(part)
+ # pk is an alias that won't be found by opts.get_field.
+ if part == 'pk':
+     fld = _cls._meta.pk
+ else:
+     fld = _cls._meta.get_field(part)
  if fld.is_relation:
      _cls = fld.get_path_info()[-1].to_opts.model
+ else:
+     _cls = None
  except (FieldDoesNotExist, AttributeError):
      if fld is None or fld.get_transform(part) is None:
          errors.append( ... E015 ... )
```

| # | model.py impl op (`check_related_path` / `walk_err`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `path: List[int]` of name ids; loop variable `name = path[i]` | `field.split(LOOKUP_SEP)` → `for part in ...` | R | the related path string, already split on `LOOKUP_SEP`, ↔ a `List[int]` of name ids; the alias string `'pk'` ↔ id `0` (mapping.md §2). |
| A2 | `model` (int, `-1` = none); `root` initial | `_cls = cls` initialised per related field; `_cls = None` | R | model class ↔ int id; `None` ↔ `-1` (mapping.md §2). |
| A3 | `fld_model`/`fld_name` (`-1` = none) | `fld = None`; `fld = ...` | R | the last found field ↔ `(fld_model, fld_name)`; `fld is None` ↔ `fld_name == -1`. |
| A4 | `if name == 0: ... pk_kind(model) ...` (pk alias resolved against the model's primary key) | `if part == 'pk': fld = _cls._meta.pk` | A-reference + I | the **fixed** control-flow branch is spelled out in the impl (`I`); the pk field's relation kind / target come from the unchanged `_meta.pk` lookup, modelled by `pk_kind`/`pk_target` (A-reference, mapping.md §3). This is the first fixed behaviour: `'pk'` no longer routes through `get_field` (which raises). |
| A5 | `else: k = resolve_kind(model, name)` and the `k==0/1/2` branches | `else: fld = _cls._meta.get_field(part)` then `if fld.is_relation:` | A-reference + I | ordinary name resolution; `resolve_kind` packs `get_field` (raise ⇒ 0) + `is_relation` (1) / not (2). The `k==0` raise ↔ the `except (FieldDoesNotExist, AttributeError)` arm. |
| A6 | `k == 1: model = relation_target(model, name)` | `if fld.is_relation: _cls = fld.get_path_info()[-1].to_opts.model` | A-reference + I | advance to the related model on a relation field. |
| A7 | `k == 2: model = -1` (and `fld_model=model, fld_name=name`) | `else: _cls = None` | I | the **second** fixed behaviour, spelled out: after a non-relation field there is no model to continue from, so `_cls` becomes `None` (`-1`). A name that follows then resolves to nothing. |
| A8 | `model == -1` branch / `k == 0` branch: `if fld_name == -1 or not transform_present(fld_model, fld_name, name): acc = True` | `except (...): if fld is None or fld.get_transform(part) is None: errors.append(E015)` | A-reference + I | the error condition; `transform_present` is the unchanged `get_transform(...) is not None` (A-reference). The `model == -1` branch is the AttributeError-from-`None._meta` case the fix newly reaches. |
| A9 | `acc` (any error along the path) returned as `bool` | `errors.append(E015)` having fired for this path | R | the per-path boolean ↔ "this path contributed an E015 error"; the outer related-field loop and message formatting are the identity over this boolean (mapping.md §2). |
| A10 | `Requires(MustTerminate(2))`; the loop's `Invariant(MustTerminate(n - i + 1))` | the real inner walk is a bounded `for part in field.split(LOOKUP_SEP)` loop that always completes and returns its verdict | I | totality: the real function always terminates (finitely many parts, straight-line body). Nagini is partial-correctness by default, so the obligation excludes diverging implementations that would satisfy the value postcondition vacuously while never delivering the verdict (mapping.md §4). |

The discriminating content of the change lives in TWO independently-observable
fixed behaviours, each spelled out deeply (no axiom hides them):

* **pk alias (A4).** `model.py` resolves `name == 0` via `pk_kind`/`pk_target`
  instead of `resolve_kind` (which returns 0 = "resolves to nothing" for the
  `pk` alias, i.e. `get_field('pk')` raises). `model_prepatch_1.py` removes the
  `name == 0` branch (routes `'pk'` through `resolve_kind`) and **fails** the
  invariant tying the computed walk to `walk_err` — exactly the spec sensing
  this behaviour (G-DIFF).
* **non-relation reset (A7).** `model.py` sets `model = -1` after a
  non-relation field. `model_prepatch_2.py` leaves `model` unchanged (the
  pre-fix code) and **fails** the same invariant.

`model_prepatch.py` reproduces BOTH pre-fix behaviours (the literal gold
pre-image) and likewise fails.

## B. No kind-3 (unexpressible-changed-op) steps

Every step is R, A-reference, or I. The two operations that genuinely *changed*
— the `pk`-alias resolution and the post-non-relation `_cls` reset — are
modelled **deeply** (spelled out as branches in `walk_err` and the impl loop),
not hidden behind an axiom about the function under change. There is **no
consumed (`A-consumed`) axiom**: the five `@ContractOnly` graph functions cover
**unchanged** name-resolution callees (`get_field`, `is_relation`,
`get_path_info`, `_meta.pk`, `get_transform`) and the proof consumes only their
return-range facts for branch totality; their behaviour is validated against the
real callees end-to-end by G-AX (A-reference, mapping.md §3).

## C. verify(model) ⇒ resolved

`check_related_path` verifies only if its returned boolean equals
`walk_err(ToSeq(path), root, root, -1)` — the deterministic per-name fold that
(i) resolves the `pk` alias against the primary key (A4) and (ii) abandons the
current model after a non-relation field (A7). By R (path-string ↔ `List[int]`,
model ↔ int, `None` ↔ `-1`, field ↔ `(model,name)`) this is exactly the per-path
verdict the gold inner loop computes. By G-AX the deep fold `walk_err`, backed by
the real `get_field`/`is_relation`/`pk`/`get_path_info`/`get_transform`,
reproduces the real `_check_ordering` E015 verdict on the F2P, P2P, and
adversarial scenarios (A-reference). Therefore a model satisfying this spec,
refined by the map above, computes the same E015 verdicts as the gold patch —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: callee soundness (G-AX, the A-reference validation) and refinement
fidelity (this document, G-EQ).
