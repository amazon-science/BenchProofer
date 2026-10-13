# mapping.md — django__django-13786

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = bb64b99b78a579cb2f6178011a4cf9366e634438`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one A-reference.

Repo file under change: `django/db/migrations/operations/models.py`.

Cold provenance: spec derived from scratch from `problem_statement`, the gold
`patch`, and the real source at `base_commit`. `spec_provenance: "cold"`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `combineTrackedSettings (baseMap newMap : SettingMap) (trackedKeys : List String)` | the `options=` argument computation inside the `elif isinstance(operation, AlterModelOptions) …` branch of `CreateModel.reduce` — `django/db/migrations/operations/models.py:139-148` (the changed `options=…` expression is line 144 pre-patch) | the modeled changed operation: the combined settings map a reduction produces |
| `mergeMaps (a b : SettingMap)` | the Python merge `{**self.options, **operation.options}` (`models.py:144`) | pure spec: `b` overrides `a`, union of keys |
| `pruneTracked` / `pruneStep` / `eraseKey` | the new pruning loop `for key in operation.ALTER_OPTION_KEYS: if key not in operation.options: options.pop(key, None)` (gold patch, inserted at `models.py:140-143` post-patch) | pure spec: drop every tracked key the override map does not supply |
| `trackedKeys` *(A-reference — checked by G-AX)* | `AlterModelOptions.ALTER_OPTION_KEYS` — `django/db/migrations/operations/models.py:643-655` | the fixed list of managed option keys; bound to a free `List String` input, validated == the real class constant by axiom_check.py |

The modeled operation is the **changed op itself** (the `options=` value the
reduction emits), modeled DEEPLY by `mergeMaps`/`pruneTracked`. There is NO
axiomatized callee of the function under change and NO consumed axiom; dict
merge / `dict.pop` are language builtins (trusted like `List.++`), not repo
callees. The only repo datum the spec references is the constant key list
`ALTER_OPTION_KEYS` (an A-reference, §3).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an options `dict[str, Any]` (`self.options`, `operation.options`, the emitted `options`) | `SettingMap := List (String × String)` | a Python dict ↔ a `List (String × String)` of its items; **compared as a set of key→value pairs** (Python `dict.__eq__` is order-insensitive, and dict keys are unique). Value payloads are carried as `String` tokens — only the *key set* and *which map a key’s value comes from* are behaviourally observed by the F2P test; G-CONF uses distinct string values to witness override precedence. |
| a dict key (an option name `str`) | `String` | identity on the option-name string; key membership ↔ `keyPresent`; deletion of a key ↔ `eraseKey` (removes every pair with that key — a dict has at most one, so this is `dict.pop(k, None)`) |
| `{**a, **b}` (PEP-448 dict merge) | `mergeMaps a b` = `b ++ a.filter (key ∉ b)` | set-of-pairs equal to `{k:b[k]} ∪ {k:a[k] | k∉b}`; `b` (the override) wins on shared keys. Order differs from CPython’s insertion order but the comparison is order-insensitive. |
| `operation.ALTER_OPTION_KEYS` | `trackedKeys : List String` | the pinned list (§3); each element a key string |
| the surrounding `[CreateModel(self.name, fields=self.fields, options=<this>, bases=self.bases, managers=self.managers)]` wrapper | omitted | the reduction copies `name`/`fields`/`bases`/`managers` through unchanged in BOTH pre- and post-patch; the ONLY value the fix changes is the `options=` map. The wrapper is identity on the modeled observable (the options dict the F2P `assertOptimizesTo` compares). |

Lean `List`/`String` are total and sound; the carrier is an association list
because the operation is per-key (membership, deletion, merge).

## 3. A-reference: `trackedKeys` ↔ `AlterModelOptions.ALTER_OPTION_KEYS`

**Reference (NOT a consumed axiom):** the deep model treats `trackedKeys` as the
set of managed option keys. In the real reduction this set is the class constant
`AlterModelOptions.ALTER_OPTION_KEYS` (`models.py:643-655`), verbatim:

```python
ALTER_OPTION_KEYS = [
    "base_manager_name", "default_manager_name", "default_related_name",
    "get_latest_by", "managed", "ordering", "permissions",
    "default_permissions", "select_on_save", "verbose_name",
    "verbose_name_plural",
]
```

**Soundness check (G-AX, `axiom_check.py`):** asserts the pinned key list this
bundle binds to `trackedKeys` is **byte-equal, in order**, to the real
`AlterModelOptions.ALTER_OPTION_KEYS` imported from the repo (the A-reference).
That constant is UNCHANGED by the fix — the patch only adds the loop that
*iterates* it — so the assertion holds identically on the base tree and the
patched tree. Imports only `django.db.migrations` (to read the untouched
constant) + stdlib. Exit 0 iff sound.

**Scope note — why G-AX does not re-check the deep model against `reduce`.**
G-AX runs against the REAL repo at `base_commit` **without** applying
`patch.diff` (it validates references to *unchanged* callees; only G-CONF applies
the gold patch). The deeply-modeled operation here is the `options=` value emitted
by `CreateModel.reduce(AlterModelOptions(...))` — i.e. the **function under change
itself**. At `base_commit` that is the buggy pre-fix code (managed options not
cleared), so it *deliberately* disagrees with the deep model, which encodes the
fixed behavior. Hence the deep-model-vs-real-`reduce` equivalence is **not** a
G-AX obligation: it is exactly what **G-CONF** validates, against the **patched**
tree (`apply_gold=True`), over ≥10⁵ inputs (§4). Asserting it here against the
unpatched callee would be unsound by construction and redundant with G-CONF.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13786`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`mergeMaps`/`pruneTracked`/`eraseKey` (R/I-tagged ops) to Python over real
`dict`s and binds `trackedKeys` to the real `ALTER_OPTION_KEYS`; it is diffed
against `patch.diff`’s behaviour — the patched real
`CreateModel.reduce(AlterModelOptions(...))` options output — over ≥10⁵ fuzzed
(base, override) map pairs. No A-tagged callee appears in the computed `out`, so
the shadow is pure R/I. Exit 0 iff zero disagreements.
