# mapping.md — django__django-12209

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5a68f024987e6d16c2626a31bf653a2edddea579`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/db/models/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `decideForceInsert` *(method)* | the INSERT-forcing decision inside `Model._save_table`, the `if (...)` block at `django/db/models/base.py:851-856` whose body is `force_insert = True` (`:857`) | the modeled changed behaviour: the resolved value of the local `force_insert` flag after the guard |
| `decidedForceInsert (raw forceInsert adding pkDefaultTruthy pkDefaultProvided)` *(pure, deep model)* | the whole `if (...): force_insert = True` block (`base.py:851-857`) | pure spec: the resolved INSERT-forcing flag |
| `pkHasUsableDefault (pkDefaultTruthy pkDefaultProvided)` *(pure, deep model)* | the two pk-default conjuncts `self._meta.pk.default and self._meta.pk.default is not NOT_PROVIDED` (`base.py:854-855`) | pure spec: does the primary key carry a usable default value |

Pre-patch repo symbol the change modifies (refinement audit only, not in the
consumer spec view): the same `if (...)` guard at `base.py:851-856`, which in
the pre-patch lacks the leading `not raw and` conjunct, so it forces an
INSERT-only path even for a direct/unprocessed data load.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `raw` — the `_save_table(raw=False, ...)` parameter; whether this is a direct/unprocessed data load (e.g. `loaddata`/deserialization saving) | `raw : Bool` | truthy `raw` ↔ `true`; `False` ↔ `false`. |
| `force_insert` — the incoming `_save_table` parameter requesting an INSERT | `forceInsert : Bool` | truthy ↔ `true`; `False` ↔ `false`. The modeled value is the flag **as it enters the guard**; `out` is its value after the guard. |
| `self._state.adding` — whether the instance is being added for the first time | `adding : Bool` | `True` ↔ `true`; `False` ↔ `false`. |
| `bool(self._meta.pk.default)` — truthiness of the primary key's declared default | `pkDefaultTruthy : Bool` | truthy default object (a callable like `uuid.uuid4`, a non-empty value) ↔ `true`; falsy (`None`, `0`, `''`, `False`) ↔ `false`. |
| `self._meta.pk.default is not NOT_PROVIDED` — whether a default was actually declared (`NOT_PROVIDED` is the sentinel for "no default") | `pkDefaultProvided : Bool` | default is not the `NOT_PROVIDED` sentinel ↔ `true`; is the sentinel ↔ `false`. |
| the resolved local `force_insert` after the `if (...): force_insert = True` block | `out : Bool` | the post-guard flag value; `true` ↔ forcing an INSERT-only path, `false` ↔ leaving the UPDATE-probe path available. |

The decision is modeled as a closed boolean function of five boolean inputs
because the operation is a **flag resolution**: no object content beyond these
five observations is inspected, and the body simply sets `force_insert = True`.
`out` is the flag that downstream (`base.py:859 if pk_set and not force_insert:`)
consults to decide whether to attempt an UPDATE before the INSERT.

## 3. Callee provenance & flag dependencies

### 3.1 `decidedForceInsert` / `pkHasUsableDefault` deep model ↔ the guard (deep model, R/I — NOT an axiom)
**Operation:** the changed guarded assignment (post-patch):
```python
updated = False
# Skip an UPDATE when adding an instance and primary key has a default.
if (
    not raw and
    not force_insert and
    self._state.adding and
    self._meta.pk.default and
    self._meta.pk.default is not NOT_PROVIDED
):
    force_insert = True
```
Modeled DEEPLY as
`decidedForceInsert raw forceInsert adding pkDefaultTruthy pkDefaultProvided =
if !raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)
then true else forceInsert`, with `pkHasUsableDefault = pkDefaultTruthy &&
pkDefaultProvided` spelling out the two pk-default conjuncts. Each Python
sub-expression is abstracted to a boolean input (R refinement, §2); there is
**no consumed axiom** — the whole decision is spelled out and G-CONF validates
it against the real `_save_table` guard.

**No callee changes.** The patch does not change any function `_save_table`
calls; it only adds the `not raw and` conjunct to a boolean guard over attribute
reads (`raw`, `self._state.adding`, `self._meta.pk.default`). The downstream
calls `_do_update` / `_do_insert` (`base.py:864,887`) are unchanged and
orthogonal to the modeled flag value — they are not modeled (they fire
identically for a given resolved `force_insert`). Hence there is no axiomatized
callee and **G-AX is skipped** (`meta.json axioms = []`,
`deep_model_references = []`; no `axiom_check.py`).

**Flag dependency:** the only newly-significant flag is `raw`. The behavioural
change is precisely that the INSERT-only path is no longer forced when
`raw=True`. G-CONF fuzzes the full cross product of the five booleans
(including both `raw` values) and confirms the resolved flag matches the real
patched guard, and that the only configurations whose outcome differs from the
pre-patch are those with `raw=True` AND the other four conjuncts holding.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12209`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`pkHasUsableDefault`/`decidedForceInsert` to Python and exercises the decision
against the REAL patched guard logic exactly as `_save_table` evaluates it
(`not raw and not force_insert and self._state.adding and self._meta.pk.default
and self._meta.pk.default is not NOT_PROVIDED`), over boundary (full cross
product) + fuzzed boolean configurations, confirming the resolved
`force_insert` matches. The pk-default conjuncts are exercised with the real
`NOT_PROVIDED` sentinel and representative truthy/falsy default objects
(`uuid.uuid4`, `None`).
