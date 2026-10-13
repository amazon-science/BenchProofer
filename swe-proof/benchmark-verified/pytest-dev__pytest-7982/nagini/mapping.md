# mapping.md — pytest-dev__pytest-7982

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a7e38c5c61928033a2dc1915cbee8caa8544a4d0`, states the type
abstraction, and gives the provenance of the deep-model reference (the callee
the deep model is validated against by G-AX).

Repo file under change: `src/_pytest/pathlib.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `descend_decisions(kinds, selected)` | `visit(path, recurse)` — `src/_pytest/pathlib.py:551` (loop body line 560-562) | the modeled changed function: the per-entry descent decision of one directory level of the walk |
| `kinds[i]` | the classification of `entry` (an `os.DirEntry`) at the loop body `for entry in entries:` (`pathlib.py:560`) | per-entry kind code (0 file / 1 dir / 2 link-to-dir / 3 link-to-nondir) |
| `selected[i]` | `recurse(entry)` (`pathlib.py:561`) | the caller-supplied recursion predicate's verdict for the entry |
| `resolves_to_dir(kind)` *(deep model — A-reference)* | `entry.is_dir()` (default `follow_symlinks=True`) — `os.DirEntry.is_dir`, CPython stdlib `Modules/posixmodule.c` / `Lib/os.py` (called at `pathlib.py:561` post-patch) | pure spec: whether an entry resolves to a directory, following links; the deep model of the unchanged callee `os.DirEntry.is_dir()`, validated `resolves_to_dir == is_dir()` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `should_descend(kind, selected)` | the whole guard `entry.is_dir() and recurse(entry)` (`pathlib.py:561` post-patch) | pure spec: the conjunction that gates `yield from visit(entry.path, recurse)` |
| `Result()[i]` | whether the walk executes `yield from visit(entry.path, recurse)` for entry `i` (`pathlib.py:562`) | per-entry descent decision |

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): `entry.is_dir(follow_symlinks=False)`
(`pathlib.py:561` @ base_commit), introduced in
`b473e515bc57ff1133fe650f1e7e6d7e22e5d841` (pytest 6.1.0). With
`follow_symlinks=False`, a link whose target is a directory is classified as a
non-directory, so a selected link-to-directory is never descended into.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| one directory level's `entries` (a sorted `list` of `os.DirEntry`) | two parallel `PSeq` of equal length: `kinds: PSeq[int]`, `selected: PSeq[bool]` | the `i`-th entry ↔ `(kinds[i], selected[i])`; `len(entries)` ↔ `len(kinds) == len(selected)`. Order is preserved (the entries are pre-sorted at `pathlib.py:558`; sorting is unchanged by the patch and irrelevant to the descent decision, so it is not modeled). |
| `os.DirEntry` classification of one entry (file / dir / link-to-dir / link-to-nondir/broken) | `kinds[i] ∈ {0,1,2,3}` | 0 = a `DirEntry` that is not a directory and not a directory link (regular file etc.); 1 = a plain directory; 2 = a symlink whose target is a directory; 3 = a symlink whose target is not a directory or that resolves to none (broken). |
| `recurse(entry)` (a `Callable[[DirEntry], bool]`) | `selected[i]: bool` | the predicate is a pure read of the entry under the F2P/P2P inputs (it inspects name/path, never mutates the tree); its verdict for entry `i` is captured as `selected[i]`. |
| the guard `entry.is_dir() and recurse(entry)` controlling `yield from visit(...)` | `should_descend(kinds[i], selected[i])` and the produced `Result()[i]` | the walk descends into entry `i` iff this conjunction holds; `Result()` is the per-entry descent decision for one level. The recursive `yield from visit(entry.path, recurse)` is the descent that this decision gates; the recursion itself is the unchanged tree-walk control flow and is not part of the modeled delta (each level repeats the same decision). |

`PSeq` carries no heap permission, so the two input views are read-only by
construction — directive 5's fractional permission is satisfied trivially (there
is nothing to mutate, and a wrong impl cannot overwrite a `PSeq`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `resolves_to_dir` deep model ↔ `os.DirEntry.is_dir()` (A-reference)
**Callee:** CPython `os.DirEntry.is_dir(*, follow_symlinks=True)`. The changed
operation is the classification used to gate descent; it is modeled **deeply**
by the `@Pure` predicate `resolves_to_dir` in the `pure` region. There is **no
`is_directory` axiom** the proof consumes. The deep model is validated equal to
the real callee out-of-band by axiom_check.py (G-AX).

Documented semantics (https://docs.python.org/3/library/os.html#os.DirEntry.is_dir):
`os.DirEntry.is_dir(*, follow_symlinks=True)` returns `True` if the entry is a
directory **or a symbolic link pointing to a directory** when `follow_symlinks`
is `True` (the default); returns `False` if the entry is or points to anything
else, or if it no longer exists. With `follow_symlinks=False` it returns `True`
only if the entry is a directory (a symlink is never followed, so a
link-to-directory returns `False`). The result is cached.

Mapping onto the model codes:

| code | entry | `is_dir()` (follow, post-patch) | `is_dir(follow_symlinks=False)` (no-follow, pre-patch) | `resolves_to_dir(code)` |
|---|---|---|---|---|
| 0 | regular file | False | False | False |
| 1 | plain directory | True | True | True |
| 2 | link → directory | **True** | **False** | **True** |
| 3 | link → non-dir / broken | False | False | False |

The deep model `resolves_to_dir(code) = (code == 1 or code == 2)` equals the
post-patch `is_dir()` (follow) column exactly. The single discriminating row is
code 2 (link-to-directory): follow says directory (descend), no-follow says not
(skip). That is precisely the F2P case `test_collect_symlink_dir` (a symlinked
directory containing a test must be collected, i.e. descended into).

**Soundness check (G-AX):** `axiom_check.py` builds a real on-disk tree with one
entry of each code (regular file, plain directory, link-to-directory,
link-to-nondir and broken link), `os.scandir`s it, and for every entry asserts
`entry.is_dir() == resolves_to_dir(code)` (the deep model == the real follow
callee) and `entry.is_dir(follow_symlinks=False) == (code == 1)` (documenting the
pre-patch callee and confirming it disagrees exactly on code 2). Boundary trees
(each code alone, empty dir) plus 2000 random mixed-code trees. Imports only the
standard library (`os`, `tempfile`, `random`). Exit 0 iff sound.
