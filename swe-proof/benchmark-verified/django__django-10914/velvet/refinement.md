# refinement.md — django__django-10914

Correspondence between `Solution.lean`'s `defaultFileMode` impl and `patch.diff`
(the gold patch changes the default file-upload permission mode). `patch.diff`
is the gold verbatim (applies at base_commit, resolves — G-RESOLVE).

## A. The changed default — `FILE_UPLOAD_PERMISSIONS`

Gold hunk:
```
-FILE_UPLOAD_PERMISSIONS = None
+FILE_UPLOAD_PERMISSIONS = 0o644
```

| # | Solution.lean impl op (`defaultFileMode`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `return 420` | `FILE_UPLOAD_PERMISSIONS = 0o644` | R | value-level refinement: Python octal `int` `0o644` ↔ Lean `Nat` `420` (mapping.md §2). The provider yields the module-level default value; the `do` block returns it directly. Concrete-value identity under the int↔Nat bijection. |

No A (axiom) steps; no kind-3 (changed inexpressible) steps. The single op is the
default mode value, modeled deeply and tagged **R** (numeric-carrier refinement
`0o644 = 420`).

## B. verify(Solution) ⇒ resolved

`defaultFileMode` verifies only if `mode = 420` (B1). By R (the int↔Nat value
bijection) the verified result equals the patched `FILE_UPLOAD_PERMISSIONS`
(`0o644`). The F2P test
(`test_override_file_upload_permissions`) asserts
`default_storage.file_permissions_mode == 0o644`; that mode IS the default
provided by this setting, so the test passes iff the default is `0o644` —
exactly what the spec pins. G-CONF differential-tests B1 (the R leg) against the
patched repo's `FILE_UPLOAD_PERMISSIONS`. The prepatch (`return 0`, the unset
sentinel) fails `mode = 420` (G-DIFF). No trust points beyond the type bijection
(mapping.md §2): there are no axioms.
