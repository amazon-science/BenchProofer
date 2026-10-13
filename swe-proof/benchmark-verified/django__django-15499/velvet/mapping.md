# mapping.md — django__django-15499

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d90e34c61b27fba2527834806639eebbcfab9631`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. This bundle has **no axioms and no deep-model references**:
the optimization under spec is a pure data-flow modeled directly, so G-AX has
nothing to check (it skips) and the full mechanical burden is G-CONF.

Repo file under change: `django/db/migrations/operations/models.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduceManagers (self : ModelCreate) (op : AlterManagers)` | `CreateModel.reduce(self, operation, app_label)` — `django/db/migrations/operations/models.py:136` (the new arm at body lines 173–185 post-patch) | the modeled changed function: the optimizer reducer of a `CreateModel`, restricted to the case where the following `operation` is an `AlterModelManagers` |
| `ModelCreate` | `CreateModel` operation (`models.py:41`) — its `name`/`name_lower` (`ModelOperation`, `models.py:21-27`) and its `fields`/`options`/`bases`/`managers` (`CreateModel.__init__`, `models.py:46-66`) | the model-creation operation; only the five components the reducer reads/reproduces are carried |
| `AlterManagers` | `AlterModelManagers` operation (`models.py:732`) — its `name_lower` and `managers` (`__init__`, `models.py:737-739`) | the manager-alteration operation |
| `ReduceResult` | the return protocol of `Operation.reduce` (`operations/base.py:129-139`): a `list` of operations, or a boolean | the three observable shapes the reducer reports (see §2) |
| `reduceManagersSpec` | the post-patch dispatch logic of the new `elif` arm + the same-model/other-model fall-through | pure spec: the optimization's input→output map; modeled directly (no foreign callee) |

There are **no axioms** (`axioms` region empty) and **no deep-model references**:
the only behavior under spec is the reducer's own dispatch, which is the changed
operation itself — never axiomatized (SPEC_GUIDE §0.7).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the real repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `CreateModel` operation | `ModelCreate` | `self.name_lower` ↔ `nameLower`; `self.fields` ↔ `fields`; `self.options` ↔ `options`; `self.bases` ↔ `bases`; `self.managers` ↔ `managers`. The element shapes (`fields`/`bases`/`managers` are lists of `(name, obj)` / classes; `options` a dict) are **opaque to the optimization** — it only copies or replaces whole components — so G-CONF models them by distinct integer/`(str,int)` tokens that compare equal iff the real components are the same object-list (mapping below). |
| `AlterModelManagers` operation | `AlterManagers` | `operation.name_lower` ↔ `nameLower`; `operation.managers` ↔ `managers`. |
| a model name `str` | `String` | `s` ↔ `s`; case-folding (`name.lower()`) is applied on BOTH sides before comparison, so `nameLower` already holds `name.lower()` (the bijection compares case-folded names — `self.name_lower == operation.name_lower`). |
| `reduce` returns `[CreateModel(...)]` | `ReduceResult.replace [c]` | a one-element list of operations ↔ `replace [c]`; the single created op's components ↔ the fields of `c`. |
| `reduce` returns `True` | `ReduceResult.reduceThrough` | `super().reduce` → `can_reduce_through` returns `True` (a truthy non-list) when `operation` does NOT reference this model — the optimizer may reorder across it. |
| `reduce` returns `False` | `ReduceResult.cannotReduce` | `super().reduce` → `can_reduce_through` returns `False` when `operation` references this model and no arm collapsed the pair — the two operations cannot be combined. (Pre-patch behavior for a same-model `AlterModelManagers`; see Solution_prepatch.) |

`fields`/`options`/`bases` are carried through the same-model collapse
**unchanged**, `managers` is **replaced** by `op.managers`. The structure-update
`{ self with managers := op.managers }` is exactly the gold
`CreateModel(self.name, fields=self.fields, options=self.options,
bases=self.bases, managers=operation.managers)` under this bijection (the name,
fields, options, bases come from `self`; managers from `operation`).

### 2.1 Component-token modeling (G-CONF)

The optimization never inspects inside a field/option/base/manager entry; it
only preserves a component verbatim or swaps the whole `managers` list. G-CONF
therefore represents each repo component by an opaque identity token (the
`id()`-keyed index of the actual Python list object passed to the constructor)
and checks that the reducer's output reuses the SAME component object the gold
constructor uses. This makes the differential test sensitive to any wrong
component routing (e.g. taking managers from `self` instead of `op`, or dropping
`options`) without depending on field/manager internals.

## 3. Callee provenance

**None.** No unchanged foreign callee is consulted by the modeled behavior:
`CreateModel.reduce`'s new arm performs a `name_lower` comparison (a `str`
attribute, modeled by `String` equality) and reassembles a `CreateModel` from
already-held components. The `name_lower` `cached_property` is `self.name.lower()`
— an attribute read, modeled as the carried `nameLower`, not an axiom. There is
thus no consumed axiom and no A-reference (`meta.json axioms=[]`,
`deep_model_references=[]`); **G-AX skips** (no `axiom_check.py`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15499`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `reduceManagersSpec` to Python (a name comparison + component
reassembly) and compares against `patch.diff`'s behaviour: the patched real
`CreateModel.reduce(AlterModelManagers(...))` applied at base_commit. The impl
region is **pure R/I** (no A-tagged callees in the computed output), so
`conf_skip=false` and G-CONF carries the mechanical burden.
