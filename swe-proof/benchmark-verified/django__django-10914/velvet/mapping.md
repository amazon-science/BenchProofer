# mapping.md — django__django-10914

Binds `Solution.lean` symbols to the repo at
`base_commit = e7fd69d051eaa67cb17f172a39b57253e9cb831a`.

Repo file under change: `django/conf/global_settings.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `defaultFileMode` (returns `mode : Nat`) | `FILE_UPLOAD_PERMISSIONS` — `django/conf/global_settings.py:306` | the default-mode provider (the module-level setting value) |
| `mode = 420` | the patched value `0o644` (= decimal 420) | the pinned default mode |

No callee is axiomatized: the default mode is a constant the provider supplies
directly, modeled deeply as its numeric value.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `FILE_UPLOAD_PERMISSIONS` : `int` octal `0o644` (post-patch) | `Nat` | exact: `0o644` ↔ `420`. Octal literal `0o644 = 6*64+4*8+4 = 420` in decimal; Python `int` and Lean `Nat` agree on the value. |
| pre-patch `None` (no definite mode) | unset sentinel, modeled as `0` (prepatch only) | absent default ↔ the buggy `0`; never equals `420`. |

The setting is consumed downstream as `Storage.file_permissions_mode`, which the
OS receives as the chmod argument; the F2P test asserts
`default_storage.file_permissions_mode == 0o644`. The provider's returned value
IS that mode, so pinning `mode = 420` pins the test-observed behavior.

## 3. Callee provenance

None (no axioms). The whole behavior is the constant default value, modeled
deeply as the literal `420`.

## 4. G-CONF fuzz seed

`conformance_check.py` seeds with **10914**. The R/I shadow is the constant
`420` (= 0o644); the oracle is the patched repo's
`django.conf.global_settings.FILE_UPLOAD_PERMISSIONS`, read in-container. The
provider takes no input, so the relation is a constant; the comparison is
repeated over the ≥10⁵ fuzz budget for harness parity.
