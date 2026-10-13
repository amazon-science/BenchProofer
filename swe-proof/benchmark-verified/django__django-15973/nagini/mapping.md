# mapping.md — django__django-15973

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 2480554dc4ada4ecf3f6a08e318735a2e50783f3`, states the type
abstraction, and gives the provenance of the deep-model reference (the unchanged
callee the model is validated against by G-AX).

Repo file under change: `django/db/migrations/autodetector.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `through_dependency(primary_ref, through_ref)` | `_get_dependencies_for_foreign_key(app_label, model_name, field, project_state)` — `django/db/migrations/autodetector.py:1398` (the intermediary-dependency hunk, body lines 1423-1429) | the modeled changed function, projected to the intermediary ("through") dependency it contributes |
| `ref_app(ref)` / `ref_name(ref)` *(deep model — A-reference)* | `resolve_relation(model, app_label, model_name)` — `django/db/migrations/utils.py:27` (the string-reference branch, lines 34-49) | pure spec: the (app_label, object_name) the resolver returns for an `"app.Object"` token; the deep model of the UNCHANGED callee, validated `ref_app/ref_name == resolve_relation` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `dot_index(ref, i)` | the `"." in model` test + `model.split(".", 1)` (`utils.py:42-43`) | pure spec helper: index of the first dot (the split point) |
| `lowered(s)` / `lower_cp(c)` | `model_name.lower()` (`utils.py:44`) | pure spec helper: the case fold the resolver applies to the object-name part (ASCII identifier domain — see §2) |

`primary_ref` ↔ the resolver argument for the field's **primary** related
reference: `remote_field_model` (`autodetector.py:1399-1410,1417-1418`), the
field's `remote_field.model` (or the relations-table fallback string).
`through_ref` ↔ the field's **intermediary** reference,
`field.remote_field.through` (`autodetector.py:1423`, the `getattr(...,
"through", None)` guard).

The pre-patch repo expression the change corrects (for the refinement audit, not
referenced from the consumer spec view): at the intermediary-dependency call
(`autodetector.py:1424-1428`) the resolver argument was `remote_field_model`
(the primary reference) instead of `field.remote_field.through` (the
intermediary reference).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `"app.Object"` reference `str` (the resolver's `model` argument when it is a string reference; and its returned `app_label` / `object_name`) | `List[int]` of Unicode code points | `s[k]` ↔ `ref[k] == ord(s[k])`; `len(s)` ↔ `len(ref)`; the first-dot split ↔ `dot_index`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes a list as a `PSeq`; `PSeq` `take`/`drop`/`len`/`[i]`/`+` mirror `str` slice/`len`/index/`+` |
| the `(app_label, object_name)` 2-tuple the resolver returns | `Tuple[List[int], List[int]]` | `Result()[0]` ↔ `app_label`, `Result()[1]` ↔ `object_name` |
| `model_name.lower()` (`utils.py:44`) | `lowered` (ASCII fold `lower_cp`) | App labels and model references are Python identifiers — ASCII letters / digits / underscore — so `str.lower()` is the ASCII fold on this domain. Non-ASCII *cased* letters are out of domain (real model names are ASCII; the F2P inputs are all ASCII). G-AX fuzzes exactly this domain (§3). |
| the FK-target dependency (`autodetector.py:1422`), the swappable-setting branch (1412-1415), the `relations`-table fallback (1402-1410), and the resolver's NON-string (model-class) branch (`utils.py:50`) | omitted | unchanged by the patch and not observed by the F2P test's intermediary-dependency assertion; the modeled projection is the single hunk that changed |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `ref_app` / `ref_name` deep model ↔ `resolve_relation` (A-reference)
**Callee:** Django `django.db.migrations.utils.resolve_relation(model,
app_label, model_name)` — UNCHANGED by the patch. For a **string** reference
(`isinstance(model, str)`) it splits on the first dot and lower-cases the name:

```python
def resolve_relation(model, app_label=None, model_name=None):
    if isinstance(model, str):
        if model == RECURSIVE_RELATIONSHIP_CONSTANT:   # "self"
            ...
        if "." in model:
            app_label, model_name = model.split(".", 1)
            return app_label, model_name.lower()       # <- the relevant arm
        if app_label is None:
            raise TypeError(...)
        return app_label, model.lower()
    return model._meta.app_label, model._meta.model_name
```

The intermediary references resolved by `_get_dependencies_for_foreign_key`'s
`through` branch are dotted `"app.Object"` strings (e.g.
`"contract.Contract"`, `"fonte_variavel.FonteVariavelModel"`), so the relevant
arm is `model.split(".", 1)` → `(app_label, model_name.lower())`. The deep
model encodes exactly this:

  `ref_app(ref)`  = code points before the first dot, **verbatim** (the app
                    label is NOT lower-cased — `model.split` returns it as-is),
  `ref_name(ref)` = code points after the first dot, **lower-cased**.

`model.split(".", 1)` splits on the FIRST dot only, so any further dots stay in
the object-name part — matched by `dot_index` returning the first dot and
`ref_name` taking the whole remainder. The change the patch makes is *which*
reference is fed to this resolver for the intermediary dependency; the resolver
itself is unchanged, hence it is an **A-reference** (deep model validated equal
to the real callee), not a consumed axiom.

**Soundness check (G-AX):** `axiom_check.py` imports the real
`resolve_relation` (in-container) and asserts `ref_app(token) == app_label` and
`ref_name(token) == object_name` for 13 boundary dotted tokens (the issue's and
F2P's app.Object strings, minimal `a.B`, multi-dot `x.y.z` / `ABC.A.B.C`,
mixed-case names, already-lower names) plus 20 000 randomized dotted tokens over
the ASCII-identifier domain (upper/lower/digit/underscore). Exit 0 iff every
observation matches. Source/docs: the function body above
(`django/db/migrations/utils.py:27-50`).

## 4. No consumed axioms

The `axioms` region is empty. The only callee the changed code invokes
(`resolve_relation`) is modeled **deeply** (A-reference, §3.1) and validated by
G-AX; the proof consumes no `@ContractOnly`. The behaviour the F2P test demands
— the intermediary dependency resolves the intermediary reference's own app and
name — is modeled deeply (the dot-split + lower-case fold spelled out in the
`pure` region and computed by the verified loops in `through_dependency`).
