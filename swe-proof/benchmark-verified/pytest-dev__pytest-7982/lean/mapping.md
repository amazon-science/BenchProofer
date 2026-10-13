# mapping.md — symbol binding & type bijection

## Instance
`pytest-dev__pytest-7982` — base_commit `a7e38c5c61928033a2dc1915cbee8caa8544a4d0`.
Spec provenance: **cold** (derived from `problem_statement` + gold `patch` +
repo source at base_commit only).

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_visit` / `problem_spec_visit` / `correct_visit` | `visit(path, recurse)` | `src/_pytest/pathlib.py:551-560` @ base_commit |
| `sortByName` | `sorted(os.scandir(path), key=lambda entry: entry.name)` | `pathlib.py:558` |
| `collectTree` (spec model) | the recursive breadth-first walk performed by `visit` (the `yield from entries` + `for entry … yield from visit(entry.path, recurse)` loop) | `pathlib.py:558-560` |
| `entryIsDir` | `entry.is_dir()` (post-patch) | `pathlib.py:560` |
| `recurse` (function param) | `recurse: Callable[[os.DirEntry[str]], bool]` | `visit` parameter |

## The change (gold patch)
`pathlib.py:560`: `entry.is_dir(follow_symlinks=False)` → `entry.is_dir()`.
`os.DirEntry.is_dir(follow_symlinks=True)` (the default) reports `True` for an
entry that is a **symbolic link pointing at a directory**; with
`follow_symlinks=False` such an entry reports `False` and the walk never descends
into it. The fix restores following symlinked directories during collection.

## Type bijection (used by G-CONF / G-AX)

| Python | Lean |
|---|---|
| a directory tree rooted at `path` | `List DirEntry` — the entries of one directory level, each `(name, FSNode)` |
| `os.DirEntry` that is a plain file / non-dir | `FSNode.file` |
| `os.DirEntry` for a directory; `is_symlink()` true/false | `FSNode.dir isSymlink children`, where `isSymlink : Bool` mirrors `entry.is_symlink()` and `children` is the resolved directory's entries |
| `entry.name` | `(e : DirEntry).1` |
| `entry.is_dir()` (follow symlinks) | `entryIsDir e.2` (post): `FSNode.dir _ _ ↦ true`, `FSNode.file ↦ false` |
| `entry.is_dir(follow_symlinks=False)` | `entryIsDir e.2` (prepatch): `FSNode.dir s _ ↦ !s`, `FSNode.file ↦ false` |
| `sorted(scandir(path), key=name)` | `sortByName` = `mergeSort` on `(·.1 ≤ ·.1)` |
| `recurse(entry)` | `recurse e : Bool` |
| the in-order sequence yielded by `visit` | the `List DirEntry` returned (entry names, in yield order) |

### Modeling notes
- `os.DirEntry.is_dir()` with default `follow_symlinks=True` follows symlinks;
  `os.DirEntry.is_dir(follow_symlinks=False)` does not. This is the SOLE
  behavioral difference the patch exercises, captured by the two `entryIsDir`
  variants. A symlink whose target is NOT a directory reports `False` under both
  (modeled: such an entry is an `FSNode.file`, never `FSNode.dir _ _`).
- `visit` is breadth-first per the docstring ("breadth-first order"): it yields
  ALL entries of the current level first (`yield from entries`), then recurses.
  `collectTree` mirrors this: `entries ++ (concat of recursive subtree walks)`.
- The real `visit` yields `os.DirEntry` objects; the conformance bridge compares
  the **sequence of entry names** (relative walk order), which is the
  collection-order observable the F2P test depends on.
- The recursion (`visit(entry.path, recurse)`) is the function under spec calling
  ITSELF — modeled deeply as the recursive `collectTree` / `implementation_visit`,
  NOT axiomatized.

## Callee provenance / flag deps
- No UNCHANGED external callee is consumed as an axiom. `os.scandir` + `sorted`
  collapse to `sortByName` (a deep model). `recurse` is an opaque caller-supplied
  predicate, modeled as a function parameter (universally quantified in the
  theorem), so no axiom is needed.
- Flag dependency: `is_dir`'s `follow_symlinks` flag is the discriminator; G-AX
  fuzzes both a real symlinked-directory entry and a real regular directory entry
  to confirm `is_dir()` (no flag) follows symlinks while `is_dir(follow_symlinks
  =False)` does not.

## G-CONF fuzz seed
`conf_seed = 7982` (pinned).
