# refinement.md — operation correspondence (django__django-14311)

Maps every op in `implementation_relaunchModule` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python selects the module name to pass to `-m`: if the executed
module is an entry-point module (`spec.name == '__main__'` or
`spec.name.endswith('.__main__')`) AND it has a parent package, use the parent
package name; otherwise use the module's own name. We model that decision deeply.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `moduleName : List Char` | `spec.name` slot | R | str ↔ List Char bijection (mapping.md); the executed module's fully-qualified name |
| 2 | `parentPackage : List Char` | `spec.parent` slot | R | str ↔ List Char bijection; empty string ↔ `[]` |
| 3 | `moduleName == "__main__".toList` | `spec.name == '__main__'` | I | identical string equality |
| 4 | `(".__main__".toList).isSuffixOf moduleName` | `spec.name.endswith('.__main__')` | I | identical suffix test, per-character |
| 5 | `isMainEntry … && !parentPackage.isEmpty` | `(spec.name == '__main__' or spec.name.endswith('.__main__')) and spec.parent` | I | boolean `or`/`and`; `spec.parent` truthiness ↔ non-empty |
| 6 | `if … then return parentPackage else return moduleName` | `if … : name = spec.parent else: name = spec.name` | I | identical two-way selection (the changed op); produces the value passed to `-m` |

No A-consumed rows: the proof discharges the selection directly; no UNCHANGED
callee property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: every op (string equality, suffix test, boolean combination,
two-way selection) is reproduced concretely; nothing is abstracted behind a model
that needs G-AX validation. No changed-inexpressible op.

The discriminating clause is row 6 combined with the entry-point test (rows 3-5):
for a plain (non-entry) dotted module with a parent package — `moduleName =
"foo.bar.baz"`, `parentPackage = "foo.bar"` — `isMainEntry` is false, so the spec
requires `result = moduleName = "foo.bar.baz"`. The prepatch impl returns
`parentPackage = "foo.bar"` unconditionally (the actual bug: the parent package
name was always used when a parent existed). Hence prepatch `correct_relaunchModule`
cannot close on this input — the G-DIFF signal, matching the F2P test
`test_run_as_non_django_module_non_package`.
