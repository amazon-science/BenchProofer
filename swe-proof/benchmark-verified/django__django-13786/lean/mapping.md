# mapping.md — django__django-13786

## Symbol binding (file:line @ base_commit bb64b99b78)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_combineOptions` / `problem_spec_combineOptions` / `correct_combineOptions` | the `AlterModelOptions` branch of `CreateModel.reduce` — computing the `options` of the squashed `CreateModel` | `django/db/migrations/operations/models.py:139-148` @ base_commit (edited hunk lines 137-147) |
| `mergeOpts base override` | `{**self.options, **operation.options}` | `models.py:144` (pre-patch sole expression; post-patch the initial value of `options`) |
| `managedKeys` | `operation.ALTER_OPTION_KEYS` | `models.py:643-655` (class attribute of `AlterModelOptions`) |
| the managed-key clearing loop | `for key in operation.ALTER_OPTION_KEYS: if key not in operation.options: options.pop(key, None)` | gold patch, `models.py:140-143` (NEW post-patch) |

The modeled function is `CreateModel.reduce`, restricted to the branch
`isinstance(operation, AlterModelOptions) and self.name_lower ==
operation.name_lower`. In that branch `reduce` returns a single replacement
`CreateModel` that is identical to `self` except for its `options`. The only
field the patch touches is that `options` dict; every other field
(`name`, `fields`, `bases`, `managers`) is copied verbatim from `self` and is
out of scope for this fix (frame: see below).

```python
# POST-PATCH (gold):
options = {**self.options, **operation.options}
for key in operation.ALTER_OPTION_KEYS:
    if key not in operation.options:
        options.pop(key, None)
return [CreateModel(self.name, fields=self.fields, options=options,
                    bases=self.bases, managers=self.managers)]
```

`AlterModelOptions.ALTER_OPTION_KEYS` is the fixed list of meta-option keys that
`AlterModelOptions` fully owns (`state_forwards` clears exactly these when its
own `options` omits them — `models.py:672-678`). The PRE-PATCH `reduce` used
`{**self.options, **operation.options}` directly, with no clearing — so a meta
option present on the original `CreateModel` but dropped by a later
`AlterModelOptions(options={})` survived into the squashed `CreateModel`, the
reported bug.

## Frame (directive 5)

The squashed `CreateModel`'s `name`, `fields`, `bases`, `managers` equal
`self`'s. Those are untouched by the patch and are not part of the modeled
operation (the bijection below models only the `options` dict). The full
`reduce` return shape is `[CreateModel(...)]`; the modeled observable is that
single object's `options`. The other fields are independently exercised by the
PASS_TO_PASS optimizer tests and are not at risk from this edit.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self.options : dict[str, Any]` | `base : List (String × V)` | dict ↦ assoc list; keys distinct (a dict has no dup keys → `base.map Prod.fst` is `Nodup`) |
| `operation.options : dict[str, Any]` | `override : List (String × V)` | as above (`override.map Prod.fst` `Nodup`) |
| `operation.ALTER_OPTION_KEYS : list[str]` | `managedKeys : List String` | the managed-key family, verbatim |
| resulting `CreateModel.options : dict[str, Any]` | `result : List (String × V)` | result dict ↦ assoc list; compared as a dict (key→value, membership) via `optLookup` |
| `key in operation.options` | `keyPresent override key` | dict membership |
| `options.pop(key, None)` | `dropKey options key` | remove all entries with that key |
| `{**a, **b}` | `mergeOpts a b` | overlay: `b` wins; `a`-only keys survive |

Option **values** are heterogeneous in Python (`str`, `bool`, tuples, …). The
fix is *key-structural* — it adds/removes whole keys and never inspects or
transforms a value. The Lean model is therefore polymorphic in the value type
`V`; G-CONF instantiates `V = str` (and exercises distinct values so a wrong
overlay/clear is observable).

## Callee provenance + flag dependencies

- No callee axiom is consumed. The changed operation (the overlay-then-clear of
  managed keys) is exactly what the patch introduces, so it is modeled DEEPLY
  (an A-reference validated by G-CONF against the real `CreateModel.reduce`),
  never axiomatized (§0.7).
- `ALTER_OPTION_KEYS` is a constant list reproduced as the `managedKeys` input
  (G-CONF passes the real `AlterModelOptions.ALTER_OPTION_KEYS`). No flag
  dependency: the branch is selected purely by `isinstance(operation,
  AlterModelOptions)` and the name match, both held fixed by G-CONF.

## G-CONF fuzz seed

`SEED = 20240627` (pinned in `conformance_check.py`).
