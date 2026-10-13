# refinement.md — pytest-dev__pytest-7982

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `descendableEntries` `do` block plus the deep `descendableSeq` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** / **A-reference** (none in this bundle), or
**I** (identical concrete op). EVERY step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are no axioms, so **G-AX is
skipped** and there is no `axiom_check.py` (cf. sphinx-doc__sphinx-8551,
django__django-13449).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The descent-selection site — the walk's per-level loop (`src/_pytest/pathlib.py:561`)

Gold hunk:
```
-        if entry.is_dir(follow_symlinks=False) and recurse(entry):
+        if entry.is_dir() and recurse(entry):
             yield from visit(entry.path, recurse)
```

The CHANGED operation is the per-child descent guard. The modeled `method`
`descendableEntries` computes, for one directory level, the order-preserving
sublist of children the (patched) guard descends into; `descendableSeq` is the
deep model of that selection.

| # | Solution.lean impl op (`descendableEntries`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `entries : List DirChild` | the `entries` list, `sorted(os.scandir(path), key=name)` | R | the ordered children of one level ↔ `List DirChild`, positionally (mapping.md §2). Order preserved both sides. |
| A2 | `e.isDirectory` read | `entry.is_dir()` (post-patch, follows links) | R | identity on `Bool` (mapping.md §2). This is the changed sub-expression: `is_dir()` vs `is_dir(follow_symlinks=False)`. |
| A3 | `e.shouldRecurse` read | `recurse(entry)` | R | identity on `Bool` (mapping.md §2); same predicate drives both legs in G-CONF. |
| A4 | guard `if e.isDirectory && e.shouldRecurse` selecting `e` | `if entry.is_dir() and recurse(entry):` | I | identical boolean conjunction guarding descent. The backward `while` fold computes exactly the left-to-right filter `descendableSeq`. |
| A5 | `out = descendableSeq entries` (the kept sublist, in order) | the children `visit` recurses into (`yield from visit(entry.path, recurse)` for each accepted `entry`) | I | concrete order-preserving filter; G-CONF transliterates it and the depth recursion to Python (§B). |

The discriminating content of the change — a symbolic link to a directory is
now FOLLOWED — lives in A2: `isDirectory` (`is_dir()`, follows links) is `true`
for a link-to-directory, whereas the pre-patch `isDirectoryNoFollow`
(`is_dir(follow_symlinks=False)`) is `false`. `Solution_prepatch.lean`
reproduces the pre-patch guard (reads `isDirectoryNoFollow`) and **fails**
`out = descendableSeq entries` on exactly that clause (G-DIFF; the unsolved goal
is `isDirectoryNoFollow … = isDirectory …`).

## B. The unchanged depth recursion — `visit` itself (I)

The enclosing generator `visit` — `entries = sorted(os.scandir(path));
yield from entries; for entry in entries: if <guard>: yield from
visit(entry.path, recurse)` — is **unchanged** by the patch apart from the §A
guard. The modeled `method` isolates the one changed operation (the per-level
selection); the deeper recursion into each selected child is the **identical**
step.

| # | construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (not modeled in the `method`; replicated by G-CONF's `shadow_visit`) | `yield from visit(entry.path, recurse)` recursing into each selected child by the SAME rule | I | identical recursion; the model proves the per-level selection rule, and the same rule applies at every level by structural induction on the tree. G-CONF transliterates the recursion directly and diffs the whole-tree yielded-path set against the real patched `visit`. |
| B2 | `yield from entries` (every child emitted at each level) | `yield from entries` | I | unchanged; every entry at a level is yielded regardless of the guard. Both shadow and oracle emit it. |

No separate failing prepatch for §B: the recursion structure is unchanged, so a
byte-identical-spec prepatch can only differ in the §A guard (which it does).
The depth recursion's fidelity is checked by G-CONF over multi-level trees.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the descent
guard's directory test — is modeled **deeply** (the spelled-out filter
`descendableSeq` and the verified loop ARE the selection, step A4), not hidden
behind an axiom about the function under change. There is no consumed axiom and
no deep-model reference: the callees the guard reads (`is_dir`, `recurse`) are
R-tagged abstract boolean inputs (mapping.md §3), driven identically on both
legs by G-CONF.

## D. verify(Solution) ⇒ resolved

`descendableEntries` verifies only if its output equals the exact
order-preserving per-child selection with the descent guard reading
`isDirectory` (`is_dir()`, links followed) — step A4/A5. By R (`List DirChild ↔
sorted DirEntry children`, `Bool` identities) the verified selection equals the
patched guard's selection at every level; by the unchanged depth recursion (B1,
structural induction) the whole-tree walk equals the patched `visit`; by G-CONF
the R/I transliteration agrees with `patch.diff`'s behaviour on thousands of
random symlink-bearing directory trees (and diverges from the unpatched base on
the symlink-dir trees — the bug). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The single trust point (plan §1.1) is refinement
fidelity (this doc, G-EQ + G-CONF); there are no axioms to trust (G-AX skipped).
