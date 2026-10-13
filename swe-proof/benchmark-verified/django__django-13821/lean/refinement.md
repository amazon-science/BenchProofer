# refinement.md — operation correspondence (django__django-13821)

Maps every op in `implementation_ensureSupportedVersion` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The post-patch Python is:
```python
def check_sqlite_version():
    if Database.sqlite_version_info < (3, 9, 0):
        raise ImproperlyConfigured(
            'SQLite 3.9.0 or later is required (found %s).' % Database.sqlite_version
        )
```
The module reads `Database.sqlite_version_info` (a tuple of ints) and
`Database.sqlite_version` (a string); we lift those two reads to the explicit
arguments `versionInfo : List Nat` and `versionStr : List Char`.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `versionInfo : List Nat` ← `Database.sqlite_version_info` | the tuple read in the `if` | R | tuple[int] ↔ List Nat bijection (mapping.md); the read is an input |
| 2 | `versionStr : List Char` ← `Database.sqlite_version` | the `% Database.sqlite_version` operand | R | str ↔ List Char bijection (mapping.md); the read is an input |
| 3 | `if versionLt versionInfo requiredMin` | `if Database.sqlite_version_info < (3, 9, 0)` | I | `versionLt` reproduces Python tuple lexicographic `<` exactly; `requiredMin = [3,9,0]` is the literal `(3, 9, 0)` |
| 4 | `return Except.error (errorMessage versionStr)` | `raise ImproperlyConfigured('SQLite 3.9.0 or later is required (found %s).' % Database.sqlite_version)` | I | `%`-substitution modeled deeply as string concatenation; `ImproperlyConfigured(msg)` ↔ `Except.error msg` |
| 5 | `return Except.ok ()` | implicit fall-through (no raise → `None`) | I | normal-return path |

No A-consumed rows (axioms region empty) and no A-reference rows: every op is a
concrete I/R op modeled directly. There is no UNCHANGED callee — tuple `<` and
`%`-formatting are language primitives modeled deeply, so G-CONF (not G-AX)
exercises the whole impl. No changed-inexpressible op.

The discriminating clause is rows 3+4: the accepted-version threshold. The gold
fix raises the minimum from components `(3, 8, 3)` to `(3, 9, 0)` and updates the
message accordingly. A runtime at `(3, 8, 11, 1)` (the F2P test input) satisfies
`versionLt [3,8,11,1] [3,9,0] = true` but `versionLt [3,8,11,1] [3,8,3] = false`.
The prepatch impl uses `requiredMinBug = [3,8,3]` + `errorMessageBug`, so on that
input it returns `Except.ok ()` while the frozen `problem_spec` demands
`Except.error (errorMessage …)`; its `correct_ensureSupportedVersion` cannot
close. That is the G-DIFF signal.
