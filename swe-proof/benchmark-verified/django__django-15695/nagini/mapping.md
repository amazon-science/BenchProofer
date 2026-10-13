# mapping.md — django__django-15695

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 647480166bfe7532e8c471fef0146e3a17e6c0c9`, states the type
abstraction, and gives the provenance of each modelled callee.

Repo file under change: `django/db/migrations/operations/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `rename_existing_index(editor, old_index, new_name)` | `RenameIndex.database_forwards(self, app_label, schema_editor, from_state, to_state)` — `django/db/migrations/operations/models.py:934` (the join point at lines 960-966, where the gold guard is added) | the modeled changed function (the schema-altering rename step) |
| `ExistingIndex` (field `name`) | the `old_index` object computed at `models.py:956-959` (`models.Index(fields=…, name=matching_index_name[0])`, the unnamed/`old_fields` branch) or `models.py:961-962` (`from_model_state.get_index_by_name(self.old_name)`, the named branch); its `.name` attribute | the existing DB index whose current name is read and compared |
| `ExistingIndex.name` | `old_index.name` (`models.py:965` in the gold guard `old_index.name == self.new_name`) | the existing index's current name |
| `new_name` (parameter) | `self.new_name` (`models.py:965`, the target name; `new_index = to_model_state.get_index_by_name(self.new_name)`, `models.py:964-965`) | the target index name |
| `SchemaEditor` (fields `rename_issued`, `renamed_to`) | `schema_editor` — `BaseDatabaseSchemaEditor`; whether/how its `rename_index` was invoked | observable record of the rename decision |
| `issue_rename(editor, old_index, new_name)` *(deep model — A-reference)* | `schema_editor.rename_index(model, old_index, new_index)` — `django/db/backends/base/schema.py:496` (called at `models.py:966`) | deep model of the unchanged backend rename primitive; validated == the real callee's *observable effect* by axiom_check.py (G-AX), NOT consumed as an opaque axiom |

The gold patch adds, between line 962 (`old_index = …`) and line 964
(`to_model_state = …`):

```python
# Don't alter when the index name is not changed.
if old_index.name == self.new_name:
    return
```

i.e. the early-return no-op guard at the join of the two `old_index`-computing
branches, before `schema_editor.rename_index(...)` is called.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an index name (`str`, e.g. `"new_pony_test_idx"`) | `int` identifier | names are only ever **compared for equality** in this change (`old_index.name == self.new_name`); never indexed/sliced. Two names are equal in the repo iff their `int` identifiers are equal in the model. (Distinct names ↔ distinct ints; the `int 0` chosen for the initial `renamed_to` sentinel is an unused "no rename target yet" marker, never a real name in a tested scenario.) |
| `old_index` (a `models.Index` with `.name`) | `ExistingIndex` with field `.name: int` | only the touched field — the index's current name — is modelled; `old_index.name` ↔ `ExistingIndex.name`. The two branches that *compute* `old_index` (unnamed `old_fields` via `_constraint_names` → `matching_index_name[0]`, and named via `get_index_by_name(old_name)`) both yield an object whose `.name` is the index's current DB name; that single produced field is the carrier (refinement.md A1/A2). |
| `self.new_name` (`str`) | `new_name: int` | the target name; same name↔int equality bijection. |
| `schema_editor` (`BaseDatabaseSchemaEditor`) | `SchemaEditor` with `rename_issued: bool`, `renamed_to: int` | the editor object; we model only the **observable rename decision** — whether `rename_index` was called and the target name it was called with. `renamed_to` is observed in **both** cases, not only when a rename happened: on the no-alteration path the real editor is never engaged (the guard returns before `models.py:966`, hence `assertNumQueries(0)`), so its record of what it was last told to rename to must be unchanged. That is what the spec's complete-no-op clause states, and it is what distinguishes "did not alter" from "altered and reported otherwise". |
| `schema_editor.rename_index(model, old_index, new_index)` | `issue_rename(editor, old_index, new_name)` | the backend rename primitive; modelled deeply as: it records `rename_issued = True`, `renamed_to = new_name`, and effects `old_index.name = new_name` (its observable effect on the index name). It is the **unchanged** callee the new code still invokes on the non-no-op branch. |

`self.new_name` equals `new_index.name` because `new_index =
to_model_state.get_index_by_name(self.new_name)` (`state.py:955-959` returns the
index whose `.name == self.new_name`), so comparing `old_index.name` to
`self.new_name` is comparing the existing index's current name to the target
index's name. The model parameter `new_name` carries this single target name.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `issue_rename` deep model ↔ `BaseDatabaseSchemaEditor.rename_index` (A-reference)
**Callee:** `schema_editor.rename_index(model, old_index, new_index)` —
`django/db/backends/base/schema.py:496-504`:

```python
def rename_index(self, model, old_index, new_index):
    if self.connection.features.can_rename_index:
        self.execute(
            self._rename_index_sql(model, old_index.name, new_index.name),
            params=None,
        )
    else:
        self.remove_index(model, old_index)
        self.add_index(model, new_index)
```

The unchanged backend rename primitive. Its **observable effect** that this
change reasons about: it issues a rename of the existing index from its current
name (`old_index.name`) to the target name (`new_index.name == self.new_name`).
The change does NOT modify `rename_index`; it only decides whether to *call* it.
The deep model `issue_rename` captures exactly this observable effect (a rename
was issued; its target is `new_name`; afterwards the index carries `new_name`).

The defect this change fixes: when `old_index.name == new_index.name` (which
arises after the backward operation of an unnamed index is a no-op, leaving the
DB index already at the new name), calling `rename_index` asks the backend to
rename `X` → `X`, which fails on PostgreSQL with
`relation "<name>" already exists`. Hence the only sound behaviour is to NOT
call the primitive in that case — the modelled "issue a rename iff the names
differ" decision.

**Soundness check (G-AX):** `axiom_check.py` exercises the real decision logic
of `database_forwards` at the join point — for every (current name, target
name) pair drawn from a boundary + fuzz set it asserts that a rename is issued
**iff** the two names differ, mirroring the gold guard `if old_index.name ==
self.new_name: return`, and that the no-op path issues zero backend calls (the
`assertNumQueries(0)` the F2P test relies on). It also confirms the real
`rename_index`'s contract (it renames `old_index.name` → `new_index.name`) so
that the deep model's recorded effect matches the real callee. stdlib-only
imports; exit 0 iff sound.

## G-CONF — differential conformance (`conformance_check.py`)

**Pinned fuzz seed: `SEED = 15695`** (module constant in `conformance_check.py`).

| aspect | choice |
|---|---|
| shadow | the impl regions of `model.py` (`issue_rename` + `rename_existing_index`, plus the `ExistingIndex` / `SchemaEditor` carriers) copied **verbatim**, with only the contract calls (`Requires` / `Ensures` / `MustTerminate` / `Acc`) and region markers deleted. Provenance `direct`: the model IS Python, so nothing is transliterated. No `@ContractOnly` axiom exists in this model (§3 records the rename primitive as a *deep* model, not a consumed axiom) and no `PSeq` carrier appears, so neither axiom delegation nor a sequence shim is needed. |
| oracle | **called, not transliterated** — the REAL patched `RenameIndex.database_forwards` (§1; `django/db/migrations/operations/models.py:934`, join at 960-966). The gate applies `patch.diff` and sets `PYTHONPATH=/testbed`, and the script additionally asserts via `inspect.getsource` that the imported `database_forwards` really contains `old_index.name == self.new_name` — an unpatched oracle is reported, never silently passed. Contrast the velvet sibling, which must transliterate the guard because Lean cannot drive Django. |
| type bridge (§2 inverted) | generation runs in the **`str`** direction so the real function is fed real index names; an exact-match interning table `str -> int` (fresh id per distinct name, ids from 1 so the `renamed_to` sentinel `0` is never a real name) lowers each name to the model's `int` carrier. Equal strings ↔ equal ints by construction, which is exactly the equality bijection §2 claims. Case-variant, prefix and near-miss name pairs are generated on purpose, so a model comparing names case-insensitively or by prefix would be refuted. |
| input domain | every generated input satisfies the model's `Requires`: the only real constraint is `editor.rename_issued is False` on entry, and each drive constructs a fresh `SchemaEditor()`; the names themselves are unconstrained. The space of name pairs is infinite, so it is sampled, not enumerated. |
| count | **100 024** comparisons: leg A 100 000 (32 boundary + seeded fuzz), leg B 7, leg C 17. |

Three legs, all driving the real patched function:

* **Leg A** (100 000) — real `ProjectState` / `ModelState` / `models.Index` objects plus a recording stand-in for `schema_editor`; observable = whether `rename_index` was called and its target name, diffed against the shadow's `rename_issued` / `renamed_to` / post-state index name. **Both** `old_index` producers are exercised, since §2 / refinement.md A1 abstract both to the single field `ExistingIndex.name`: the named branch (`get_index_by_name(self.old_name)`, models.py:961-962) and the unnamed `old_fields` branch (`_constraint_names(...)` → `matching_index_name[0]`, models.py:939-959). A green run is required to have taken both guard branches on both producers (`named_equal` / `named_differ` / `unnamed_equal` / `unnamed_differ` all non-zero) — a run that missed one is reported as vacuous rather than passed.
* **Leg B** (7) — the same real function driven with the REAL `BaseDatabaseSchemaEditor` from `connection.schema_editor()` against a real sqlite table carrying a real index. Grounds two observables a recording fake cannot: the count of SQL statements actually emitted (→ the shadow's `rename_issued`; zero on the no-op path is the `assertNumQueries(0)` the F2P test relies on) and the index names present on the table afterwards (→ the model's post-state claim `old_index.name == new_name` in *both* cases). This closes the loop the deep model `issue_rename` leaves open against the real `rename_index` (§3.1). Includes the exact F2P shape of `test_rename_index_unnamed_index`: forward rename to `new_pony_test_idx`, then **re-apply** forward, which must emit zero SQL and leave the index in place.
* **Leg C** (17) — checks the bridge assumption §2 states rather than assuming it: `get_index_by_name(self.new_name).name == self.new_name` on the real `ModelState`, which is what licenses the model's single `new_name` parameter standing for both `self.new_name` and `new_index.name`. The shadow's own obligation `Requires(old_index.name != new_name)` on `issue_rename` is also *observed* (not assumed): reaching the backend primitive with equal names is reported as a disagreement, since it is precisely the rename-X-to-X the guard exists to prevent.

Boundary cases: equal names; differing names; the exact F2P name `new_pony_test_idx`; case variants (`NEW_PONY_TEST_IDX`, `New_Pony_Test_Idx`); empty current and empty target name; strict-prefix pairs; Django's auto-generated `pony_pink_<hex>_idx` shape; `Index.max_name_length` (30) names differing in one character.

Refutation capability was verified by mutation before acceptance — each of the following makes the script exit 1: pre-patch (unguarded) oracle; shadow with the guard removed; shadow with the guard inverted; shadow comparing names case-insensitively; shadow renaming to the wrong target. Legs B and C each refute independently with the other legs neutered. `conf_skip` is **not** set: the impl region is genuinely executable computation (the guard is modelled deeply / tagged **I**), so a real differential test applies.
