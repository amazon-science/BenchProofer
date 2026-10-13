# refinement.md — django__django-11141

Maps every op in `implementation_migration_module_status` (Solution.lean) to its
`patch.diff` counterpart. Tags: **R** type-refinement, **A-consumed** axiom used
by proof, **A-reference** deep model validated == real callee by G-AX, **I**
identical concrete op.

The modeled function is the per-app success branch of `MigrationLoader.load_disk`.
The patch makes two behavioral changes; both are modeled deeply (no axioms).

| # | Lean impl op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `if !hasPath then return {migrated:=false, names:=[]}` | `if not hasattr(module, '__path__'): self.unmigrated_apps.add(label); continue` | R | `hasPath : Bool` ↔ `hasattr(module,'__path__')`. A non-package contributes no files. |
| 2 | (`hasFile` deliberately NOT consulted) | the REMOVED lines `if getattr(module,'__file__',None) is None: self.unmigrated_apps.add(label); continue` | R | Behavior A of the fix: the `__file__` gate is gone, so namespace packages (no `__file__`) reach the discovery step. Modeled by omission — `hasFile` is an input that never affects the result. |
| 3 | `for entry in entries do if (!entry.2) && validMigrationName entry.1 then names := names ++ [entry.1]` | `migration_names = {name for _,name,is_pkg in pkgutil.iter_modules(module.__path__) if not is_pkg and name[0] not in '_~'}` | R | `entries : List (String×Bool)` ↔ the `iter_modules` yield; set ⇒ G-CONF compares order-independently. `validMigrationName` deeply models `name[0] not in '_~'`. |
| 4 | `let migrated := (!names.isEmpty) || ignoreNoMigrations` | `if migration_names or self.ignore_no_migrations:` (else branch) | R/I | Behavior B of the fix: a package with no files (and no flag) is now unmigrated, not migrated. `names.isEmpty` ↔ `not migration_names`. |
| 5 | `return {migrated:=migrated, names:=names}` | `self.migrated_apps.add(label)` xor `self.unmigrated_apps.add(label)`, and `self.disk_migrations[label,name] = …` for each name | R | the result struct records the classification + discovered names; the actual `disk_migrations` values (Migration objects) are downstream and irrelevant to the modeled decision. |

No changed op is inexpressible. No row is A-tagged ⇒ `axiom_check.py` is a skip
stub and `meta.json axioms`/`deep_model_references` are empty.

## Prepatch correspondence (G-DIFF)

- `Solution_prepatch.lean` carries **behavior A** bug: an extra
  `if !hasFile then return {migrated:=false, names:=[]}` re-introduces the removed
  `__file__` gate, so a namespace package (`hasFile=false`, `hasPath=true`,
  files present) is wrongly classified unmigrated with no names — contradicting
  the `hasPath=true` clause. Unprovable ⇒ fails G-VERIFY.
- `Solution_prepatch_2.lean` carries **behavior B** bug: the final classification
  is `migrated := true` unconditionally, so an empty package with
  `ignoreNoMigrations=false` is wrongly migrated — contradicting
  `result.migrated = ((! filteredNames.isEmpty) || ignoreNoMigrations)`.
  Unprovable ⇒ fails G-VERIFY.
