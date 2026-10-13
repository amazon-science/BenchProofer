# refinement.md — pytest-dev__pytest-7982

The operation-by-operation correspondence between `model.py`'s implementation
(the `descend_decisions` impl region, plus the deep `resolves_to_dir` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The descent guard — `visit()` (`src/_pytest/pathlib.py:561`)

Gold hunk:
```
-        if entry.is_dir(follow_symlinks=False) and recurse(entry):
+        if entry.is_dir() and recurse(entry):
             yield from visit(entry.path, recurse)
```

| # | model.py impl op (`descend_decisions`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | the level's `entries` ↔ parallel `kinds: PSeq[int]`, `selected: PSeq[bool]` of equal length; iterate `i` over them | `for entry in entries:` over the sorted `os.DirEntry` list | R | entry `i` ↔ `(kinds[i], selected[i])` (mapping.md §2); order preserved (entries pre-sorted, unchanged by the patch). |
| A2 | `resolves_to_dir(kinds[i])` (codes 1,2 → True) | `entry.is_dir()` (default `follow_symlinks=True`) | A-reference | the changed classification is modeled **deeply**: `resolves_to_dir` (the `@Pure` predicate in the `pure` region) IS the follow-symlinks classification. There is no consumed `is_directory` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `os.DirEntry.is_dir()` on a real tree (file/dir/link-to-dir/link-to-nondir/broken) and asserts `is_dir() == resolves_to_dir(code)`. The real callee follows the link, so a link-to-directory (code 2) is a directory (mapping.md §3.1). |
| A3 | `selected[i]` | `recurse(entry)` | R | the caller predicate's verdict for the entry, captured per-entry as a boolean (mapping.md §2); the predicate is a pure read of the entry under the tested inputs. |
| A4 | `decision = resolves_to_dir(kinds[i]) and selected[i]` | the guard `entry.is_dir() and recurse(entry)` (a short-circuit `and`) | I | identical boolean conjunction gating descent; `should_descend` names exactly this conjunction. |
| A5 | `Result()[i] == should_descend(kinds[i], selected[i])` (the descent decision for entry `i`) | `yield from visit(entry.path, recurse)` is executed iff the guard holds | R | the per-entry descent decision; the recursive `yield from visit(...)` is the unchanged tree-walk control flow that this decision gates. Each deeper level re-runs the same decision, so the per-level decision is the complete delta. |

The discriminating content of the change — a link-to-directory (code 2) is
classified as a directory under the follow-symlinks rule (`is_dir()`) but NOT
under the no-follow rule (`is_dir(follow_symlinks=False)`) — lives in
`resolves_to_dir(2) == True` (model) ⇔ `entry.is_dir()` (real). The pre-patch
`entry.is_dir(follow_symlinks=False)` returns `False` for code 2;
`model_prepatch.py` reproduces that (`decision = kinds[i] == 1 and selected[i]`)
and **fails** the obligation `decision == should_descend(kinds[i], selected[i])`
on the link-to-directory branch — exactly the spec sensing the change (G-DIFF).
This is the F2P case `test_collect_symlink_dir`: a selected symlinked directory
must be descended into and its test collected.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* — the
classification used to gate descent (`is_dir(follow_symlinks=False)` →
`is_dir()`) — is modeled **deeply** (the spelled-out `@Pure` predicate
`resolves_to_dir` consumed in `descend_decisions`, step A2, an **A-reference**),
not hidden behind an axiom about the function under change. There is **no
consumed axiom** in this bundle: the changed callee `os.DirEntry.is_dir()`
appears only as the **A-reference** that G-AX validates the deep model against,
and there is no unchanged opaque callee the proof relies on.

## C. verify(model) ⇒ resolved

`descend_decisions` verifies only if every per-entry decision equals
`resolves_to_dir(kinds[i]) and selected[i]` (A2, A4), i.e. a selected
link-to-directory (code 2) IS descended into. By R (entry ↔ `(kind, selected)`;
descent decision ↔ executing `yield from visit(entry.path, recurse)`) the
verified decision equals the gold guard `entry.is_dir() and recurse(entry)` on
the tested trees; by G-AX the deep model `resolves_to_dir` equals the real
`os.DirEntry.is_dir()` (A-reference) — in particular following a link to a
directory. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the audited callee — and the gold patch
resolves (G-RESOLVE). The single trust point is axiom soundness (G-AX) of the
A-reference; refinement fidelity is this document (G-EQ).
