# refinement.md — django__django-13786

Operation correspondence between `implementation_combineOptions` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed: the changed operation (overlay then clear of
managed keys not re-specified by the override) is modeled DEEPLY. Every row is
**R**, **A-reference**, or **I**. The R/I/A-reference legs are differential-
tested by G-CONF; G-AX is a skip stub (no consumed callee axiom).

## `implementation_combineOptions` ↔ the `AlterModelOptions` branch of `CreateModel.reduce`

The gold patch turns

```python
options={**self.options, **operation.options}                      # PRE-PATCH
```

into

```python
options = {**self.options, **operation.options}                    # POST-PATCH
for key in operation.ALTER_OPTION_KEYS:
    if key not in operation.options:
        options.pop(key, None)
...
options=options,
```

with the surrounding `CreateModel(self.name, fields=self.fields, …,
bases=self.bases, managers=self.managers)` reconstruction unchanged.

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `let mut options := mergeOpts base override` | `options = {**self.options, **operation.options}` | R | dict overlay ↦ assoc-list overlay (`override ++ base-keys-not-in-override`); `dict[str,Any]` ↦ `List (String × V)` |
| `for key in managedKeys do` | `for key in operation.ALTER_OPTION_KEYS:` | I | iterate the managed-key family |
| `if ! keyPresent override key then` | `if key not in operation.options:` | I | "override is silent about this managed key" |
| `options := dropKey options key` | `options.pop(key, None)` | A-reference | the EDITED op: clear a managed key the override omits. Modeled deeply as `filter (key ≠ ·)`; validated == real `reduce` by G-CONF. `pop(.,None)` ignores absence ↦ `dropKey` is a no-op when absent |
| `return options` | `options=options` field of the returned `CreateModel` | R | resulting `options` dict ↦ assoc list; observable is the dict (key→value), compared via `optLookup` |

The result is the precise observable: `CreateModel.reduce` returns a single
`CreateModel` whose `options` the optimizer then compares for equality against
the expected operation list. With the pre-patch overlay-only code, a meta option
the original `CreateModel` set but a later `AlterModelOptions` omitted survives,
so the squashed `CreateModel.options` does not equal the expected (cleared)
options and the F2P assertion fails.

## Spec strength (directive 4 / 8)

`problem_spec_combineOptions` has two conjuncts: (i) the result's keys are
distinct (`(result.map Prod.fst).Nodup`) — a Python `dict` has no duplicate
keys, so this rules out a wrong impl that matches every first-match lookup while
hiding shadowed duplicate keys; (ii) it pins the value at EVERY key
(`∀ k, optLookup result k = expectedLookup …`), grounded structurally in the two
input mappings and the managed-key list:
- override-mentioned key ⇒ override's value (overlay precedence),
- managed key the override omits ⇒ absent (the fix),
- any other key ⇒ base value survives.
No output key is left unconstrained, and the postcondition is dischargeable only
by actually performing the overlay-then-clear — a wrong impl that skips the clear
(the prepatch) violates the managed-omitted-key clause; one that over-clears a
non-managed key, drops an override key, or echoes an oracle violates the
corresponding clause.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: `options := mergeOpts base override` with the
  managed-key clearing loop removed entirely (the literal pre-patch code). The
  carried gold proof of `correct_combineOptions` fails to close on the
  managed-omitted-key clause: for a managed key `k` with `optLookup base k =
  some v` and `optLookup override k = none`, `expectedLookup … k = none` but the
  buggy `optLookup result k = some v`. This is the single fixed behavior.
  (FAIL_TO_PASS: `test_create_model_and_remove_model_options`.)
