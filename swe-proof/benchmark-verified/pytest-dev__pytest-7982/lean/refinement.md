# refinement.md — operation correspondence (impl ↔ patch.diff)

Tags: **R** type refinement · **A-consumed** proof uses this axiom · **A-reference**
deep model validated == real callee (G-AX) · **I** identical concrete op.

The patch changes one line of `visit`; the impl is the faithful skeleton of the
whole `visit` body (the change plus its surrounding control flow), so the table
covers every op of `implementation_visit`.

| # | `implementation_visit` op | `patch.diff` / `visit` counterpart | tag |
|---|---|---|---|
| 1 | `let entries := sortByName xs` | `entries = sorted(os.scandir(path), key=lambda e: e.name)` | R — `os.scandir(path)` ↦ the `List DirEntry` argument `xs`; `sorted(…, key=name)` ↦ `mergeSort` on name order. Name-keyed total order bijection (mapping.md). |
| 2 | `let mut acc := entries` then `return acc` after the loop, with `acc := entries` seeded | `yield from entries` (emit the whole level first) | I — the level's entries are emitted in order before any descent (breadth-first). |
| 3 | `for h : e in entries do …` | `for entry in entries:` | I — iterate the sorted level. |
| 4 | `if entryIsDir e.2 && recurse e then …` | `if entry.is_dir() and recurse(entry):` | R — `entry.is_dir()` (default `follow_symlinks=True`) ↦ `entryIsDir` (`FSNode.dir _ _ ↦ true`). This is the PATCHED predicate; the prepatch uses `!isSymlink` (= `is_dir(follow_symlinks=False)`). `recurse(entry)` ↦ `recurse e`. |
| 5 | `acc := acc ++ implementation_visit recurse ch` | `yield from visit(entry.path, recurse)` | R/I — the recursive `visit` call modeled DEEPLY by the recursive `implementation_visit` (descend into the entry's children `ch`), results appended in order. The recursion is the function under spec, not a callee → modeled, never axiomatized. |
| 6 | `match … | .file => pure ()` | (no-op: `is_dir()` already false for files) | I — files are never descended into. |

## Spec-side (`problem_spec_visit` / `collectTree`)
`collectTree` is the deep model of the desired walk: `entries ++ concat (for each
dir entry the caller selects, its recursive subtree walk)`. It uses the
follow-symlinks predicate implicitly — it descends into EVERY `FSNode.dir`
(symlink or not) the `recurse` filter selects, which is precisely the post-patch
behavior. `problem_spec_visit … result := result = collectTree recurse entries0`.

## A-tag inventory
- **A-consumed:** none. No `axiom <callee>_prop` is consumed.
- **A-reference:** none consumed as a dead axiom; the directory walk and the
  name-sort are modeled deeply (`collectTree`, `sortByName`) and are exercised by
  G-CONF on the R/I legs.

Every step is R, I, or a deep model — no changed-inexpressible op. `conf_skip =
false` (the impl region is all R/I, mechanically differential-tested by G-CONF).
