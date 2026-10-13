# refinement.md — django__django-10914

Maps every operation in `implementation_effectiveFilePermissionsMode` to its
`patch.diff` counterpart. The patch is a one-line default-constant change; the
observable behavior it governs is the permission-mode resolution in
`FileSystemStorage.file_permissions_mode` (see mapping.md). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
deep-modeled changed op validated == real callee, **I** identical concrete op.

## Patch (post-patch)
```python
# django/conf/global_settings.py
FILE_UPLOAD_PERMISSIONS = 0o644          # was: None
```
governing, unchanged:
```python
# django/core/files/storage.py
def _value_or_setting(self, value, setting):
    return setting if value is None else value
@cached_property
def file_permissions_mode(self):
    return self._value_or_setting(self._file_permissions_mode,
                                  settings.FILE_UPLOAD_PERMISSIONS)
```

## Operation correspondence
| # | Lean op (`implementation_effectiveFilePermissionsMode`) | patch.diff / governed op | tag | note |
|---|---|---|---|---|
| 1 | `let mut setting : Option Nat := defaultUploadMode` | `FILE_UPLOAD_PERMISSIONS = 0o644` (the changed default) seeded as the base value of `settings.FILE_UPLOAD_PERMISSIONS` | I | the post-fix built-in default; `defaultUploadMode = some 0o644`. THIS is the line the patch changes (prepatch seeds `none`). |
| 2 | `match projectSetting with \| some v => setting := v \| none => pure ()` | resolving `settings.FILE_UPLOAD_PERMISSIONS`: a project `settings.py` declaration overrides the built-in default; absence leaves the default | R | `Option (Option Nat)` models "declared (`some v`) vs. left-at-default (`none`)"; the inner `Option Nat` is the mode-or-None the project pinned. |
| 3 | `match storageOverride with \| some m => return some m \| none => return setting` | `_value_or_setting(self._file_permissions_mode, setting) = setting if value is None else value` | R | `self._file_permissions_mode : (int \| None) ↔ storageOverride : Option Nat`; Python `setting if value is None else value` ↔ Lean `none => setting / some m => some m`. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the patched repo behavior (the resolved
`FileSystemStorage.file_permissions_mode`) over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
`Solution_prepatch.lean` seeds the default with `none` (the literal pre-patch
`FILE_UPLOAD_PERMISSIONS = None`) instead of `defaultUploadMode = some 0o644`.
With no per-instance override and no project override (`storageOverride = none`,
`projectSetting = none`) it returns `none`, but the spec's no-override clause
demands `result = defaultUploadMode = some 0o644`. The carried gold proof fails
to typecheck on exactly that discriminating clause — precisely the behavior the
FAIL_TO_PASS test `test_override_file_upload_permissions` asserts (default
storage's mode must be `0o644`, not `None`). The spec is byte-identical between
the two files (only the impl initializer differs).

## patch.diff == gold
`patch.diff` is the gold patch verbatim (the one-line `global_settings.py`
change); it applies at `base_commit` and the harness resolves.
