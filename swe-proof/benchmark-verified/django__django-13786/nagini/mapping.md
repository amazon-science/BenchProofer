# mapping.md — django__django-13786

Binds every `model.py` symbol to its repository counterpart at
`base_commit = bb64b99b78a579cb2f6178011a4cf9366e634438`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/db/migrations/operations/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduced_create_options(self_options, operation_options)` | the `AlterModelOptions` branch of `CreateModel.reduce(self, operation, app_label)` — `django/db/migrations/operations/models.py:138-147` (the branch computing the new `CreateModel`'s `options`) | the modeled changed behaviour: the options of the `CreateModel` produced when a `CreateModel` is reduced with a following `AlterModelOptions` on the same model |
| `self_options` | `self.options` (the `CreateModel`'s options dict) | read-only input mapping |
| `operation_options` | `operation.options` (the `AlterModelOptions`'s options dict) | read-only input mapping |
| `is_managed_option(k)` | membership in `AlterModelOptions.ALTER_OPTION_KEYS` — `django/db/migrations/operations/models.py:643-655` | pure spec: whether an option name is a managed-option name the alter step may set/compare/clear |
| `key_managed_a()` / `key_managed_b()` | two distinct members of `ALTER_OPTION_KEYS` (e.g. `'verbose_name'`, `'verbose_name_plural'`) | pure spec: representative managed option names |
| `key_other()` | an option name NOT in `ALTER_OPTION_KEYS` (e.g. `'proxy'`, `'indexes'`, `'db_table'`) | pure spec: representative non-managed option name |
| `merge_options(a, b)` *(axiom — A-consumed)* | the dict-display merge `{**self.options, **operation.options}` — `django/db/migrations/operations/models.py:148` (post-patch: line `options = {**self.options, **operation.options}`) | unchanged language primitive (PEP 448 mapping unpacking) the changed code composes |
| `without_key(d, k)` *(axiom — A-consumed)* | `dict.pop(key, None)` residue — `django/db/migrations/operations/models.py:151` (post-patch: `options.pop(key, None)`) | unchanged language primitive (remove one key; no-op if absent) the changed code composes |

The reference behaviour the change MATCHES is `AlterModelOptions.state_forwards`
(`django/db/migrations/operations/models.py:672-678`):
```python
model_state.options = {**model_state.options, **self.options}
for key in self.ALTER_OPTION_KEYS:
    if key not in self.options:
        model_state.options.pop(key, False)
```
The reduce-options computation must produce the same options that applying the
`AlterModelOptions` to the freshly-created model would. (For the audit only —
not referenced from the consumer spec view.)

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.options` / `operation.options` — `dict` from option-name `str` to an option value (`str`, `bool`, `list`, `tuple`, …) | `Dict[int, int]` from an option-name token to an option-value token | option name `str` ↔ a distinct `int` token; option value ↔ a distinct `int` token. Only membership (`name in opts`) and per-name value equality are observed by `reduce`'s options computation and by the equality the optimizer test asserts (`assertOptimizesTo` deconstructs and compares operations, whose options compare by `==`). Integer identity is the faithful carrier: it preserves `in`, `==` at a key, and key distinctness. |
| `ALTER_OPTION_KEYS` membership test (`key in operation.ALTER_OPTION_KEYS`) | `is_managed_option(k)` over the representative tokens | `key_managed_a()/_b()` are members; `key_other()` is a non-member. The behaviours provided→wins and other-unprovided→kept are quantified over EVERY name; managed-unprovided→cleared is stated per member of the finite managed family (= `is_managed_option`), which covers every managed name — the partition the loop induces. |
| `{**self.options, **operation.options}` | `merge_options` axiom | A-consumed callee (§3.1) |
| `options.pop(key, None)` | `without_key` axiom | A-consumed callee (§3.2) |

`str` keys/values are NOT indexed or iterated character-wise anywhere in the
modeled computation (only dict membership and per-key value matter), so the
`str→List[int]` rule does not apply; the faithful carrier for the keys/values
is opaque `int` identity tokens.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `merge_options` ↔ dict-display merge `{**a, **b}` (A-consumed)
**Callee:** CPython mapping unpacking `{**a, **b}` (PEP 448; bytecode
`BUILD_MAP` + `DICT_UPDATE`). The gold patch's first step is
`options = {**self.options, **operation.options}`. Standard semantics: a FRESH
dict containing every key of `a` and `b`; for a key in both, `b`'s value wins
(later mapping overrides); neither `a` nor `b` is mutated. The axiom encodes
exactly these (weakest sufficient) obligations:
`b` wins on overlap, `a`'s value elsewhere, union of keys, fresh result.

### 3.2 `without_key` ↔ `dict.pop(k, None)` residue (A-consumed)
**Callee:** CPython `dict.pop(key, default)` with `default=None`
(`Objects/dictobject.c`, `dict_pop_impl`). The gold patch's clearing step is
`options.pop(key, None)` (remove `key` if present, no-op otherwise; the `None`
default suppresses `KeyError`). The model takes the functional view (the residue
mapping with `key` removed); the in-place `pop` in the gold yields the same
key/value contents on the dict. The axiom encodes: `k` absent from the result;
every other key carried with its value; no spurious/changed key. Docs:
https://docs.python.org/3/library/stdtypes.html#dict.pop.

**Why these are A-consumed, not the changed op:** the operation the gold patch
ADDS is the *control logic* deciding which managed keys to clear
(`for key in ALTER_OPTION_KEYS: if key not in operation.options: …`). That logic
is modelled DEEPLY in the impl region (the two guarded clearing branches);
neither `merge_options` nor `without_key` is the changed operation — both are
unchanged language primitives the new logic composes. Axiomatizing them is sound
(directive 7) and they are the weakest contracts the proof needs.

**Soundness check (G-AX):** `axiom_check.py` runs the real `{**a, **b}` merge
and the real `dict.pop(k, None)` residue on the 2 F2P scenarios + 10 boundary
pairs (incl. all-managed-cleared, op-value-wins, non-managed-survives) + the
int-carrier cases + 20 000 randomized fuzz pairs over the real `ALTER_OPTION_KEYS`
plus non-managed names, and asserts every observation meets the axioms' Ensures.
It also checks the COMPOSITION (`merge` then drop-each-managed-not-in-op) equals
the gold patch's exact `reduce` options computation on every case. Imports only
the standard library (the very constructs the gold patch calls). Exit 0 iff sound.
