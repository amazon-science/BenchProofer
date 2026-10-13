# refinement.md — operation correspondence (django__django-14725)

Maps every op in `implementation_saveFormset` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python body is:
```python
if self.edit_only:
    return self.save_existing_objects(commit)
else:
    return self.save_existing_objects(commit) + self.save_new_objects(commit)
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `editOnly : Bool` read in `if editOnly then` | `if self.edit_only:` | R | Python `bool` attribute ↔ Lean `Bool` argument (mapping.md). The flag-plumbing factory hunks set this attribute; no behavior of its own. |
| 2 | `return existing` (then-branch) | `return self.save_existing_objects(commit)` | R | `save_existing_objects(commit)`'s returned `list` ↔ input `existing : List α`. The callee is UNCHANGED; only its returned list is consumed. |
| 3 | `return existing ++ new` (else-branch) | `return self.save_existing_objects(commit) + self.save_new_objects(commit)` | R | same R refinement for both lists; Python list `+` ↔ Lean `++` (order-preserving append). |

No A-consumed rows: the proof discharges the selection directly; no UNCHANGED
callee *property* is assumed (only their returned lists are taken as inputs).
No A-reference rows: the changed operation is the branch itself, modeled
concretely. No changed-inexpressible op.

The discriminating clause is row 2 vs row 3 under `editOnly = true`: the
post-patch `save` returns `existing` alone, whereas the pre-patch `save` (no
edit-only branch) always returns `existing ++ new`. The prepatch impl returns
`existing ++ new` unconditionally, so its `correct_saveFormset` cannot close
against the frozen `problem_spec_saveFormset` (which pins `existing` in the
`editOnly = true` case) whenever `new ≠ []`. That is the G-DIFF signal, and it is
exactly the bug the issue reports: in edit-only mode, extra forms still created
new objects.
