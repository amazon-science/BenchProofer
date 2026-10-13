# mapping.md — pytest-dev__pytest-7982

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a7e38c5c61928033a2dc1915cbee8caa8544a4d0`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled value. **There are no axioms and no `:|` callee
stubs in this bundle** (G-AX is skipped, like sphinx-doc__sphinx-8551 /
django__django-13449): the changed operation is modeled deeply and the only
callees involved are observed as abstract read-only booleans.

Repo file under change: `src/_pytest/pathlib.py` (one line).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `descendableEntries (entries : List DirChild)` | the descent-selection performed by the `for entry in entries:` loop inside the directory walk — `src/_pytest/pathlib.py:560-562` | the modeled changed function: which children of one directory level are recursed into |
| `DirChild` | one `os.DirEntry[str]` child of a level, observed through three booleans | record carrying only the touched observations |
| `DirChild.isDirectory` | `entry.is_dir()` — `os.DirEntry.is_dir()` with the default `follow_symlinks=True` (the **post-patch** directory test) | the directory test resolving symbolic links |
| `DirChild.isDirectoryNoFollow` | `entry.is_dir(follow_symlinks=False)` (the **pre-patch** directory test; pre-image only) | the directory test NOT resolving symbolic links |
| `DirChild.shouldRecurse` | `recurse(entry)` — the `recurse` callable argument of the walk (pytest's `Session._recurse` / `Package._recurse`, `src/_pytest/main.py`, `src/_pytest/python.py:664`) | the walk's recursion predicate, unchanged |
| `descend (e)` | the loop guard `entry.is_dir() and recurse(entry)` (`pathlib.py:561` post-patch) | per-child descent decision |
| `descendableSeq (es)` | the children the loop recurses into, in `sorted(...)` encounter order | deep model of the per-level selection |

The walk function itself (`def visit(path, recurse)`, `pathlib.py:551`) is the
enclosing recursive generator. Its structure — `entries = sorted(os.scandir);
yield from entries; for entry in entries: if <guard>: yield from
visit(entry.path, recurse)` — is **unchanged** by the patch except for the
guard. The deeper recursion is the identical step (refinement.md §B, I-tagged);
the modeled `method` isolates the one CHANGED operation, the per-child guard.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the ordered children of one level: `sorted(os.scandir(path), key=name)` | `entries : List DirChild` | the Python list of `os.DirEntry` ↔ the `List DirChild`, positionally; `len` ↔ `.length`; encounter order preserved (the spec keeps order) |
| `entry.is_dir()` (bool, follows links) | `DirChild.isDirectory : Bool` | identity on `Bool`; `True ↔ true` |
| `entry.is_dir(follow_symlinks=False)` (bool) | `DirChild.isDirectoryNoFollow : Bool` | identity on `Bool`; used only by the pre-patch skeleton |
| `recurse(entry)` (bool) | `DirChild.shouldRecurse : Bool` | identity on `Bool`; the same predicate drives SHADOW and ORACLE in G-CONF |
| the set of children selected for descent | `out : List DirChild` (a sublist of `entries`, order-preserving) | membership + order; G-CONF observes it through the literal yielded entry paths of the whole walk (`os.path.normpath(entry.path)`, NOT symlink-resolved, so a followed symlinked directory is distinguishable) |

`List` indexing in Lean is total and sound; the carrier is `List DirChild`
because the operation is a per-child, order-preserving filter at one level.

## 3. Callee provenance

No callee is axiomatized or `:|`-stubbed. The two callees the guard reads —
`os.DirEntry.is_dir(...)` and the `recurse` predicate — are CPython/pytest
built-ins observed as the abstract booleans `isDirectory` / `isDirectoryNoFollow`
/ `shouldRecurse` (mapping.md §2). They are R-tagged INPUTS, not assumed
behaviours: G-CONF drives the real `visit` and the shadow with the SAME real
`recurse` predicate and the SAME real `os.DirEntry` objects, so no contract about
them is taken on faith. Hence the bundle has no `axiom`, no `axiom_check.py`, and
G-AX is `skip`.

`os.DirEntry.is_dir()` semantics (Python docs,
https://docs.python.org/3/library/os.html#os.DirEntry.is_dir): with the default
`follow_symlinks=True` it returns `True` for a directory OR a symbolic link
pointing to a directory; with `follow_symlinks=False` it returns `True` only for
a real directory (a link to a directory yields `False`). The one-line change
swaps the second form for the first, so symlinked directories are now followed.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7982`**. It builds, per
input, a random on-disk directory tree mixing regular files, real
subdirectories, symlinks to directories, symlinks to files, and broken symlinks
(and hidden / `__pycache__` names the recursion predicate rejects), then compares
the literal yielded-path set of the patched real `visit` (ORACLE) against the
shadow (`descendableSeq` + the unchanged depth recursion). Self-validated:
shadow == patched `visit` on every tree; shadow disagrees with the UNPATCHED
`visit` on ~35% of trees (those containing a followed symlinked directory) — the
behaviour the F2P `test_collect_symlink_dir` observes.
