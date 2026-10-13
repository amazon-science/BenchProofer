# mapping.md — symbol binding & type bijection (django__django-13821)

## Modeled function
- **Lean** `implementation_checkSqliteVersion : List Nat → List Char → Except (List Char) Unit`
- **Python** `check_sqlite_version()` — `django/db/backends/sqlite3/base.py:66-68 @ e64c1d8`
  (post-patch: raises `ImproperlyConfigured('SQLite 3.9.0 or later is required (found %s).' % Database.sqlite_version)`
  when `Database.sqlite_version_info < (3, 9, 0)`).

The function reads two module-level inputs of the DB-API driver and either
returns normally or raises a configuration error. We model those two reads as
explicit arguments:
- `Database.sqlite_version_info` (a tuple of ints) → `versionInfo : List Nat`
- `Database.sqlite_version` (the version string) → `versionStr : List Char`

The observable behavior demanded by the F2P test is purely the comparison
threshold: a runtime whose version tuple is `(3, 8, 11, 1)` must now be rejected
(it sits below the required minimum but above the old minimum), and the error
message must report the new minimum and the actual version string.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `sqlite_version_info` (`tuple[int, ...]`) | `List Nat` | lexicographic order; Python compares tuples element-wise, a strict prefix being smaller |
| `sqlite_version` (`str`) | `List Char` | per-code-point value carrier; substituted verbatim into the message |
| `(3, 9, 0)` threshold literal | `[3, 9, 0] : List Nat` | the required-minimum tuple |
| normal return (`None`) | `Except.ok ()` | no error raised |
| `raise ImproperlyConfigured(msg)` | `Except.error (msg : List Char)` | the raised message text is the error payload |
| `'…(found %s).' % version` | `"…(found ".toList ++ versionStr ++ ").".toList` | `%`-formatting modeled deeply as concatenation |

Python tuple `<` is lexicographic with the prefix rule (`() < (1,)`,
`(3, 8, 11, 1) < (3, 9, 0)` because `8 < 9` at index 1). `versionLt` reproduces
this exactly (see pure region), so it is an **I/R** op, not an axiom.

## Callee provenance
- No UNCHANGED callee is consumed as an axiom and none is declared `opaque`.
  Tuple comparison and `%`-formatting are language primitives modeled deeply
  (versionLt + string concatenation). `ImproperlyConfigured` is an exception
  constructor, modeled as the `Except.error` carrier. The axioms region is empty.

## Flag dependency
None. The function takes no flags; behavior depends only on the version tuple.

## G-CONF fuzz seed
Pinned seed: **13821**. ≥10^5 fuzzed version tuples (lengths 0–6, components
oversampling the boundary values 3, 8, 9, 0 and the exact threshold neighborhood)
plus deterministic boundary cases including the F2P tuple `(3, 8, 11, 1)`.
