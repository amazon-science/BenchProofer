# refinement.md — django__django-15987

The operation-by-operation correspondence between `model.py`'s implementation
(the `default_dir_is_listed` impl region and the deep `any_match` fold) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee/operation by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The single change site — the duplicate-detection membership test

`fixture_dirs` cached property, `django/core/management/commands/loaddata.py:370`.

Gold hunk:
```
-            if app_dir in fixture_dirs:
+            if app_dir in [str(d) for d in fixture_dirs]:
                 raise ImproperlyConfigured(
                     "'%s' is a default fixture directory for the '%s' app "
                     "and cannot be listed in settings.FIXTURE_DIRS."
```

| # | model.py impl op (`default_dir_is_listed`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameters `value_matches`, `is_path_object: List[bool]` | the `FIXTURE_DIRS` entries iterated by the membership test (each a `str` or `pathlib.Path`); the comparison target `app_dir` | R | each entry `d_k` ↦ `(str(d_k)==app_dir, isinstance(d_k, PurePath))`; `app_dir` is captured by `value_matches` (mapping.md §2). |
| 2 | the loop accumulates `result = result or value_matches[k]` over all entries — i.e. compare each entry **by path string** to the default directory | `app_dir in [str(d) for d in fixture_dirs]` — membership of `app_dir` in the **str-coerced** entries | A-reference | the changed operation (string-coerced membership) is modeled **deeply**: the fold `any_match` IS the disjunction `∃k. value_matches[k]`, and `value_matches[k] = (str(d_k)==app_dir)`. There is no consumed axiom. The deep model is validated **== the real expression** out-of-band: G-AX (axiom_check.py) builds real `str`/`Path` configs and asserts `any_match == (app_dir in [str(d) for d in fixture_dirs])` (mapping.md §3.1). |
| 3 | `result` returned (a `bool`) decides whether detection occurred | the `if ...:` branch ⇒ `raise ImproperlyConfigured(...)` | I | the branch condition is the membership result; the raised message and the surrounding loop over `apps.get_app_configs()` are unchanged by the patch, and the F2P only observes whether the error is raised. |

The discriminating content of the change — a configured entry that is a path
**object** equal-by-string to the default directory must be detected — lives in
the right-hand side of the postcondition naming **only** `value_matches`
(`Result() == any_match(ToSeq(value_matches))`), with `is_path_object` pinned
out. The pre-patch raw membership `app_dir in fixture_dirs` instead misses a
path-object entry (a `PurePath` is never `==` a `str`); `model_prepatch.py`
reproduces that (`value_matches[k] and not is_path_object[k]`) and **fails** the
loop invariant `result == any_match(ToSeq(value_matches).drop(i))`, which is
exactly the spec sensing the change (G-DIFF).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the membership test over the string-coerced entries — is modeled
**deeply** (the spelled-out disjunction `any_match` over `value_matches`,
step 2, an **A-reference**), not hidden behind an axiom about the operation under
change. There is **no consumed `@ContractOnly` axiom** in this bundle; the only
out-of-band trust point is the A-reference's faithfulness to the real
`str()`/`pathlib` semantics, validated by G-AX.

## verify(model) ⇒ resolved

`default_dir_is_listed` verifies only if its output equals the exact disjunction
of per-entry path-string matches (step 2, with `is_path_object` excluded from the
postcondition RHS) — so a verifying impl detects a path-object entry that is
equal-by-string to the default directory, exactly as the corrected membership
does. By R (each entry ↦ its two booleans; `app_dir` captured by
`value_matches`; the raised message and the enclosing loop unchanged) the
verified decision equals `app_dir in [str(d) for d in fixture_dirs]`; by G-AX the
deep model `any_match` equals that real expression (A-reference) on boundary +
fuzz. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited A-reference — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
