# mapping.md — django__django-10914

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e7fd69d051eaa67cb17f172a39b57253e9cb831a`, states the type
abstraction, and records the provenance of the modeled values/operations.

Repo files involved:
- `django/conf/global_settings.py` (the one changed file — the project-wide
  default value).
- `django/core/files/storage.py` (the resolution rule that consumes the
  default — read but UNCHANGED by the patch).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_storage_mode(override)` | `FileSystemStorage.file_permissions_mode` property — `django/core/files/storage.py:215-217` (`return self._value_or_setting(self._file_permissions_mode, settings.FILE_UPLOAD_PERMISSIONS)`) composed with the resolver `_value_or_setting` (`storage.py:198-199`) | the modeled effective-mode resolution: per-store override falling back to the project-wide default |
| `override` (parameter, `Optional[int]`) | `self._file_permissions_mode` — the per-store override (`storage.py:182`, ctor arg `file_permissions_mode=None`, default `None`) | the per-store override; `None` ⇔ no override configured |
| the `default = 420` impl literal | `settings.FILE_UPLOAD_PERMISSIONS` — `django/conf/global_settings.py:307` | the project-wide default mode; the gold patch changes its value from `None` to `0o644` |
| `default_mode()` *(pure spec)* | the DESIRED value of `settings.FILE_UPLOAD_PERMISSIONS` (`0o644`) | pure spec: the definite default the issue requires; frozen reference for the postcondition |

The behaviour the F2P test observes
(`test_override_file_upload_permissions`, `tests/test_utils/tests.py:1096`):
`default_storage` is a `FileSystemStorage` constructed with no explicit
`file_permissions_mode`, so `self._file_permissions_mode is None` and
`file_permissions_mode` resolves to `settings.FILE_UPLOAD_PERMISSIONS`. Post
patch the test asserts that resolved value equals `0o644`; pre patch it was
`None`. (The override branch — `with self.settings(FILE_UPLOAD_PERMISSIONS=0o777)`
→ `0o777` — already passed pre-patch and is unaffected.)

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a numeric file mode you'd pass to `os.chmod` (e.g. `0o644`, `0o777`), or `None` for "unspecified" | `Optional[int]` | `None` ⇔ absent/unspecified mode; an octal-mode int ⇔ the same `int` (`0o644 == 420`, `0o777 == 511`); these are pure value comparisons, the only thing the test observes |
| `self._value_or_setting(value, setting) = setting if value is None else value` (`storage.py:198-199`) | `resolve_storage_mode`'s body: `default if override is None else override` | identical concrete control/data flow (kind I); `value` ⇔ `override`, `setting` ⇔ `default` |
| `self._file_permissions_mode` (per-store override, `None` for `default_storage`) | `override` parameter | identity on the `Optional[int]` value |
| `settings.FILE_UPLOAD_PERMISSIONS` (the global default the patch edits) | the `default` impl literal (`420` post-patch / `None` pre-patch) | identity on the `Optional[int]` value; `0o644 == 420` |

The modes are plain immutable scalars (`int`/`None`), so no heap permissions
(`Acc`) are needed; the property the test checks is value equality only.

## 3. Callee provenance

None. The patch changes a module-level configuration **value**
(`FILE_UPLOAD_PERMISSIONS = None` → `0o644`), and the resolution that consumes
it (`_value_or_setting`, an unchanged two-line `if value is None` expression) is
fully expressible in Nagini and modeled **directly** as the kind-I body of
`resolve_storage_mode`. There is no opaque library callee on this path, hence
**no `@ContractOnly` axiom and no `axiom_check.py`** (nothing for G-AX to
execute). The changed value and the resolution are both modeled deeply; see
refinement.md for the operation-by-operation correspondence.
