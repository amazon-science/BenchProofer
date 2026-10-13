# refinement.md — django__django-10914

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_storage_mode` impl region + the `default_mode` pure reference) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed** / **A-reference**), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The project-wide default value — `global_settings.py:307`

Gold hunk (the one change):
```
-FILE_UPLOAD_PERMISSIONS = None
+FILE_UPLOAD_PERMISSIONS = 0o644
```

This module-level setting is the project-wide default numeric mode applied to
newly stored files. It is consumed by the unchanged resolver
`FileSystemStorage.file_permissions_mode` (`storage.py:215-217`):
`return self._value_or_setting(self._file_permissions_mode, settings.FILE_UPLOAD_PERMISSIONS)`,
where `_value_or_setting(value, setting) = setting if value is None else value`
(`storage.py:198-199`). For `default_storage`, `self._file_permissions_mode is
None`, so the resolved mode is exactly `settings.FILE_UPLOAD_PERMISSIONS`.

| # | model.py impl op (`resolve_storage_mode`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `override: Optional[int]` | `self._file_permissions_mode` (the per-store override; `None` for `default_storage`) | R | a numeric file mode / unspecified ↔ `Optional[int]` (`None` ⇔ absent); mapping.md §2. |
| A2 | `default = 420` (the impl literal, `# 0o644`) | `FILE_UPLOAD_PERMISSIONS = 0o644` — the changed setting value | **I** (under R on the carrier) | the FIX. The literal octal mode the gold patch installs as the default, `0o644 == 420`; identical concrete value, refined only by the `Optional[int]` carrier (mapping.md §2). The pre-patch value `None` is exactly what `model_prepatch.py` uses. |
| A3 | `if override is None: return default` else `return override` | `setting if value is None else value` — `_value_or_setting` body (`storage.py:198-199`) consumed by the `file_permissions_mode` property (`storage.py:217`) | **I** (under R) | identical concrete control/data flow: the unchanged fallback resolver, `value`↔`override`, `setting`↔`default` (mapping.md §2). UNCHANGED by the patch and fully expressible, so modeled directly, not axiomatized. |

The discriminating content of the change — the default goes from absent
(`None`) to the definite mode `0o644` — lives in step **A2** (`default = 420`).
`model_prepatch.py` reverts exactly that one literal to `None` (the pre-patch
setting value) and **fails** the postconditions
`Implies(override is None, Result() is not None)` and
`Implies(override is None, Result() == 420)` — the spec sensing the change
(G-DIFF). The override branch (`override is not None ⟹ Result() is override`)
verifies in both, mirroring that the `with self.settings(FILE_UPLOAD_PERMISSIONS=
0o777)` case already passed pre-patch.

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it sets `default = None`
(the absent pre-patch `FILE_UPLOAD_PERMISSIONS`) instead of `default = 420`,
exactly the gold hunk reverted. With the byte-identical frozen spec it **fails**
verification on `Implies(override is None, Result() is not None)`
(`model_prepatch.py:54`). That is precisely the behaviour the F2P test
`test_override_file_upload_permissions` observes: with no override configured,
`default_storage.file_permissions_mode` must equal `0o644` (post-patch); pre
patch it is `None` (`assertIsNone` → `assertEqual(..., 0o644)`). The spec is
therefore strong enough that no implementation leaving the default unspecified
can verify (spec sees the bug).

The companion clause `Implies(override is not None, Result() is override)` pins
the override-passthrough so a wrong impl cannot satisfy the spec by ignoring a
configured override (e.g. always returning `420`), keeping the resolution
faithful to the unchanged `_value_or_setting` rule. (`test_override_file_upload_
permissions` and the sibling `test_override_file_upload_directory_permissions`
P2P test both exercise the override branch.)

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — installing
the definite default mode `0o644` in place of the absent `None` — is an **I**
step (step A2, the same concrete value, refined only by the `Optional[int]`
carrier). The surrounding fallback resolution (`_value_or_setting`) is unchanged
and also an **I** step (A3). There is **no axiom** (no opaque callee on this
path; mapping.md §3) and therefore **no A-consumed / A-reference row** and no
`axiom_check.py`. We never axiomatize the value under change; it is modeled
directly as a concrete literal.

## D. verify(model) ⇒ resolved

`resolve_storage_mode` verifies only if (A2) its fallback default equals the
definite mode `0o644` and (A3) it returns the override verbatim when one is
configured. By R (`Optional[int]` ↔ numeric file mode / unspecified) and the two
**I** steps, the verified resolution equals the gold composition
`_value_or_setting(self._file_permissions_mode, 0o644)` on the tested inputs:
with no override → `0o644`, with an override → the override. There are no
callees to audit (no axioms), so the only trust point is refinement fidelity
(this document, G-EQ); the gold patch resolves (G-RESOLVE). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to the
type refinement of file modes to `Optional[int]`.
