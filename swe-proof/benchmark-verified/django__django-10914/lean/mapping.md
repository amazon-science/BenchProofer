# mapping.md — django__django-10914

## Instance
- repo: django/django
- base_commit: e7fd69d051eaa67cb17f172a39b57253e9cb831a
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch changes ONE line in `django/conf/global_settings.py`: the built-in
default of the `FILE_UPLOAD_PERMISSIONS` setting goes from `None` to `0o644`. The
edit is a one-line constant change, but its *observable* behavior — the behavior
the FAIL_TO_PASS test asserts — surfaces through the permission-mode resolution
performed by `FileSystemStorage`:

```python
# django/core/files/storage.py @ base_commit
def _value_or_setting(self, value, setting):
    return setting if value is None else value

@cached_property
def file_permissions_mode(self):
    return self._value_or_setting(self._file_permissions_mode,
                                  settings.FILE_UPLOAD_PERMISSIONS)
```

`self._file_permissions_mode` is the per-instance override passed to the storage
constructor; `settings.FILE_UPLOAD_PERMISSIONS` is the project-resolved setting,
which is the project's `settings.py` value when one is declared and otherwise the
built-in default from `global_settings.py` (the constant the patch changes).

The F2P test `test_override_file_upload_permissions` constructs the default
storage with NO per-instance override and NO project override, and asserts
`default_storage.file_permissions_mode == 0o644` (pre-patch it was `None`); it
also checks that a project override `FILE_UPLOAD_PERMISSIONS=0o777` still wins.

## Modeled function
I model the **effective permission-mode resolution** — the value
`FileSystemStorage.file_permissions_mode` resolves to — as a total function of
its three data layers. This is the smallest unit whose observable behavior the
patch changes and the F2P test pins. It is pure (`_value_or_setting` is a
two-line total selector) with no I/O, so its whole observable behavior is the
returned mode.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_effectiveFilePermissionsMode` | `FileSystemStorage.file_permissions_mode` resolution via `_value_or_setting` (`django/core/files/storage.py:198,215`) layered over the changed default (`django/conf/global_settings.py:307`) |
| `problem_spec_effectiveFilePermissionsMode` | the post-condition the resolved mode must satisfy |
| `defaultUploadMode` | the built-in default of `FILE_UPLOAD_PERMISSIONS` (post-fix `0o644`) |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `storageOverride : Option Nat` | the `file_permissions_mode=` ctor argument stored as `self._file_permissions_mode` | `none ↔ None` (no per-instance override); `some m ↔ int m` (octal mode `m`) |
| `projectSetting : Option (Option Nat)` | whether `settings.FILE_UPLOAD_PERMISSIONS` is left at its built-in default vs. pinned by the project | OUTER `none ↔ "not declared in settings.py"` (built-in default applies); OUTER `some v ↔ "declared as v"`, where INNER `none ↔ None` and `some k ↔ int k` |
| result `: Option Nat` | `storage.file_permissions_mode` return | `none ↔ None`; `some m ↔ int m` |

`Option Nat` ↔ the Python "permission mode or None" domain is the identity
bijection: `None ↔ none`, integer mode `m ↔ some m`. Octal `0o644` (Python) =
`0o644` (Lean) = `420`.

## Callee provenance / flag deps
- No unchanged repo callee is consumed. `_value_or_setting` is a two-line total
  selector modeled directly (the `most-specific-wins` cascade), and the changed
  default is the literal `some 0o644`. There is no `opaque` callee and no
  `axiom <callee>_prop`; the `axioms` region is empty and `axiom_check.py` is a
  skip stub.
- No flag dependency: the resolution does not branch on any unrelated flag. The
  only data are the three permission layers, all fuzzed by G-CONF.

## G-CONF fuzz seed
- pinned seed: `10914`
- ≥10^5 fuzzed `(storageOverride, projectSetting)` tuples; modes drawn from a pool
  including `None`, the new default `0o644`, the old-behavior-relevant `0o600`,
  `0o777` (the F2P override), `0`, and random `0..0o777`, with project-setting
  left-at-default vs. pinned uniformly mixed.
