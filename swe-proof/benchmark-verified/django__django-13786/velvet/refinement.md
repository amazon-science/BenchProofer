# refinement.md — django__django-13786

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`combineTrackedSettings` `do` block plus the deep `mergeMaps`/`pruneFold` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-reference** (a deep model / repo datum validated == the real artifact by
G-AX), or **I** (identical concrete op). There are no **A-consumed** axioms.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A-reference + this narrative are audited by **G-AX** / **G-EQ**. `patch.diff` is
the gold patch **verbatim** (G-RESOLVE).

## A. The combined-options site — `CreateModel.reduce` vs `AlterModelOptions`

Gold hunk (`django/db/migrations/operations/models.py`, the
`elif isinstance(operation, AlterModelOptions) …` branch):
```
+ options = {**self.options, **operation.options}
+ for key in operation.ALTER_OPTION_KEYS:
+     if key not in operation.options:
+         options.pop(key, None)
  return [
      CreateModel(
          self.name,
          fields=self.fields,
-         options={**self.options, **operation.options},
+         options=options,
          bases=self.bases,
          managers=self.managers,
      ),
  ]
```

| # | Solution.lean impl op (`combineTrackedSettings`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `baseMap : SettingMap` | `self.options` (the `CreateModel`’s options dict) | R | `dict[str,Any]` ↔ `List (String × String)`, compared as a set of key→value pairs (mapping.md §2). |
| A2 | param `newMap : SettingMap` | `operation.options` (the `AlterModelOptions`’s options dict) | R | same dict bijection (mapping.md §2). |
| A3 | param `trackedKeys : List String` | `operation.ALTER_OPTION_KEYS` | A-reference | the managed-key list, bound to a free input and validated byte-equal to the real class constant by G-AX (mapping.md §3). Not consumed as an axiom — it is concrete data the loop iterates. |
| A4 | `result := mergeMaps baseMap newMap` (loop seed) | `options = {**self.options, **operation.options}` | I | PEP-448 dict merge ↔ `mergeMaps` (override map wins; mapping.md §2). Concrete, transliterated by G-CONF. |
| A5 | the `while` fold: for each `k` in `trackedKeys`, `if keyPresent k newMap then result else eraseKey k result` | `for key in operation.ALTER_OPTION_KEYS: if key not in operation.options: options.pop(key, None)` | I | per-key prune ↔ `pruneFold` step (`keyPresent`↔`in`, `eraseKey`↔`dict.pop(key, None)`; pop of an absent key is a no-op, as is `eraseKey` on a key with no binding). Concrete, transliterated by G-CONF. |
| A6 | `out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)` (postcondition) | the emitted `options=options` value | R + I | the result map (set of pairs) equals the patched `options` dict. The surrounding `CreateModel(self.name, fields=…, bases=…, managers=…)` wrapper is unchanged by the fix (identical pre/post-patch) and is omitted (mapping.md §2). |

Discriminating content of the change — a **managed key present in `self.options`
but absent from `operation.options` must be CLEARED**, not carried through — lives
in the prune fold (A5): `entity` of a managed key `k ∉ newMap` is `eraseKey k`.
The pre-patch merged without pruning; `Solution_prepatch.lean` returns
`mergeMaps baseMap newMap` and **fails** `out = pruneFold …` (G-DIFF) on exactly
this case. The F2P `test_create_model_and_remove_model_options` exercises it:
`AlterModelOptions(options={})` must clear `verbose_name`, and
`AlterModelOptions(options={'verbose_name': …})` must clear `verbose_name_plural`
while keeping `verbose_name`.

## B. No A-consumed axioms

Map union (`{**a, **b}`) and key deletion (`dict.pop(k, None)`) are language
builtins — the analogue of `List.++` — modeled deeply as `mergeMaps`/`eraseKey`,
NOT axiomatized. The function under change (`CreateModel.reduce`) is itself the
modeled function; nothing it calls is replaced by an axiom. The single repo datum
the spec references, `trackedKeys ↔ ALTER_OPTION_KEYS`, is an **A-reference**
(G-AX checks byte-equality to the real constant), not a consumed contract.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely changed — adding
the managed-key restriction to the merged options — is modeled **deeply** (the
spelled-out `pruneFold`, step A5), not hidden behind an axiom about the function
under change.

## D. verify(Solution) ⇒ resolved

`combineTrackedSettings` verifies only if its output equals the merge **with** the
managed-key restriction (A4+A5+A6). By R (`dict ↔ List (String × String)`,
set-of-pairs comparison, wrapper identity) the verified map equals the patched
`reduce`’s emitted `options` dict on every input; by G-AX `trackedKeys` equals
the real `ALTER_OPTION_KEYS` (A-reference, base tree — the constant is untouched
by the fix); by G-CONF the deep model / R/I
transliteration agrees with `patch.diff`’s behaviour on ≥10⁵ inputs. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this doc, G-EQ + G-CONF) plus the A-reference key list
(G-AX).
