# mapping.md — django__django-13821

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e64c1d8055a3e476122633da141f16b50f0c4a2d`, states the type
abstraction, and gives the provenance of the A-reference deep model (the real
callee its deep model is validated against).

Repo file under change: `django/db/backends/sqlite3/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `check_supported_version(version)` | `check_sqlite_version()` — `django/db/backends/sqlite3/base.py:66-68` | the modeled changed function (the start-up minimum-version guard) |
| `min_version()` | the minimum-version literal `(3, 9, 0)` in the patched comparison (`base.py:67` post-patch) | pure spec: the supported minimum version, 3.9.0, as a component sequence |
| `lt_lex(a, b)` *(deep model — A-reference)* | the tuple comparison operator `<` applied to `Database.sqlite_version_info < (3, 9, 0)` (`base.py:67`) | pure spec: component-wise (lexicographic) strict-less; the deep model of the unchanged Python tuple-comparison operation the guard performs, validated `lt_lex == tuple <` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `UnsupportedConfiguration` (exception) | `django.core.exceptions.ImproperlyConfigured` (raised at `base.py:68`) | user-defined stand-in for the configuration error raised on an unsupported runtime (a builtin/3rd-party exception in an `Exsures` crashes the Nagini translator) |
| `Requires(MustTerminate(2))` | `check_sqlite_version()` is straight-line bounded code executed at import time (`base.py:71`): it always terminates (returns or raises) | total-correctness obligation: forbids a same-spec impl that diverges (hangs) instead of deciding — such an impl satisfies the value postconditions only vacuously, and its faithful patch hangs Django start-up and the F2P test (the partial-correctness gap a G-EQ audit demonstrated) |

The pre-patch repo value the change replaces (for the refinement audit, not
referenced from the consumer spec view): the old minimum tuple `(3, 8, 3)` and
its message `'SQLite 3.8.3 or later is required (found %s).'` (`base.py:67-68`).

`Database` is `sqlite3.dbapi2`; `Database.sqlite_version_info` is the embedded
SQLite library version as a tuple of ints (e.g. `(3, 8, 11, 1)`), and
`Database.sqlite_version` is its dotted-string form used only to format the
message. The decision the change makes is solely about
`sqlite_version_info < (3, 9, 0)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Database.sqlite_version_info` (a `tuple` of ints, variable length) | `version: List[int]` of release components | `version_info[k]` ↔ `version[k]`; `len(version_info)` ↔ `len(version)`; specification carried by `PSeq[int]` via `ToSeq` |
| the literal `(3, 9, 0)` | `min_version() == PSeq(3, 9, 0)` and the impl literal `[3, 9, 0]` | the three components 3, 9, 0 |
| `version_info < (3, 9, 0)` (Python tuple `<`) | `lt_lex(ToSeq(version), min_version())` | Python tuple `<` IS lexicographic strict-less on the components (validated component-for-component by G-AX) |
| `raise ImproperlyConfigured(...)` | `raise UnsupportedConfiguration()` + the `Exsures` clause | the *fact and condition* of the raise is what the F2P test observes (`assertRaisesMessage(ImproperlyConfigured, msg)`); the message string is formatted from `sqlite_version`, observationally a presentation detail not modeled in the carrier — see §4 |

Python tuple operations beyond plain `<` are not exercised; the carrier is
`List[int]` and the comparison is spelled out as the `lt_lex` fold (Nagini does
not provide tuple-`<` over heap sequences).

## 3. Callee provenance — the A-reference (checked by G-AX / axiom_check.py)

### 3.1 `lt_lex` deep model ↔ Python tuple comparison `<` (A-reference)
**Callee:** Python's built-in tuple comparison operator, applied as
`Database.sqlite_version_info < (3, 9, 0)`. Tuple comparison in CPython is
lexicographic: corresponding elements are compared in order; the first unequal
pair decides; if no unequal pair is found, the shorter tuple is the smaller
(CPython `Objects/tupleobject.c`, `tuplerichcompare`; language reference
"Comparisons" → "Sequences ... are compared lexicographically").

The changed decision (which minimum to compare against) is modeled **deeply**
by the `@Pure` front-recursive fold `lt_lex` (with `min_version`) in the `pure`
region; there is **no consumed `@ContractOnly` axiom**. The deep model is
validated equal to the real operation out-of-band by `axiom_check.py` (G-AX),
which runs Python's real `tuple <` on boundary version tuples (incl. the F2P
discriminator `(3, 8, 11, 1)`, the new minimum `(3, 9, 0)`, and prefix/empty
edge cases) plus 50 000 randomized component-sequence pairs and asserts
`lt_lex(a, b) == (tuple(a) < tuple(b))` and that the reject decision
`lt_lex(version, (3, 9, 0))` equals `version_info < (3, 9, 0)`. Exit 0 iff sound.
It imports nothing repo-specific (tuple `<` is a language operation).

## 4. The raise and the message string

The F2P test `test_check_sqlite_version` (in `tests/backends/sqlite/tests.py`)
mocks `sqlite_version_info = (3, 8, 11, 1)` and `sqlite_version = '3.8.11.1'`
and asserts that `check_sqlite_version()` raises `ImproperlyConfigured` with
message `'SQLite 3.9.0 or later is required (found 3.8.11.1).'`.

Two observable facts of the change:
  1. the *condition* of the raise — `(3, 8, 11, 1) < (3, 9, 0)` is now True
     where `(3, 8, 11, 1) < (3, 8, 3)` was False — i.e. the runtime is now
     rejected where it previously was not. **This is what the model pins**
     (the `Exsures` condition `lt_lex(ToSeq(version), min_version())`).
  2. the message names `3.9.0` and echoes the runtime's `sqlite_version`
     string. The `'found %s'` half is a verbatim copy of `Database.sqlite_version`
     (a presentation string formatted from the same version, unchanged in
     mechanism), and the `'3.9.0'` half is the dotted form of the same minimum
     `(3, 9, 0)` the condition uses. The message is therefore a *presentation*
     of the modeled minimum, carrying no behavioural information beyond the
     reject condition the contract already pins; it is not separately modeled
     in the `List[int]` carrier (string formatting of an int tuple is a
     presentation detail, and the test's message difference is entirely driven
     by the threshold change the condition captures).
