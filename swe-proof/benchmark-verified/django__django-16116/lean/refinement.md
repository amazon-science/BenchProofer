# refinement.md — django__django-16116

Every op in `implementation_processChanges` ↔ its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom property),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op).

| # | Lean impl op | patch.diff (post-patch) counterpart | tag |
|---|---|---|---|
| 1 | `let mut eff := { wroteToLast := false, wroteNew := false, exitCode := none }` | initial state: no writer has run, no exit requested | I |
| 2 | `if !hasChanges then return eff` | the `if not changes:` arm — "No changes detected", nothing emitted, normal completion | R (the no-changes log is modeled as "no effect"; only the emit/exit observables are pinned) |
| 3 | `if checkOnly then return { eff with exitCode := some 1 }` | `if check_changes: sys.exit(1)` — the HOISTED guard, now BEFORE the writers | R (`sys.exit(1)` ↔ `exitCode := some 1`; emits nothing) |
| 4 | `if mergeIntoLast then eff := { eff with wroteToLast := true }` | `if self.update: self.write_to_last_migration_files(changes)` | R (writer-ran ↔ `wroteToLast = true`; file-content behavior unchanged, not modeled) |
| 5 | `else eff := { eff with wroteNew := true }` | `else: self.write_migration_files(changes)` | R (writer-ran ↔ `wroteNew = true`) |
| 6 | `return eff` | fall through, normal completion (`exitCode = none`) | I |

Doc-only, non-modeled op carried in `patch.diff` for gold fidelity:

| Lean impl op | patch.diff counterpart | tag |
|---|---|---|
| (none) | reword of the `--check` argument `help=` string (lines 70–73) | I-doc — a help/documentation string; no observable effect on any F2P/P2P test |

## Audit
- No A-consumed and no A-reference rows ⇒ `axiom_check.py` is a skip stub; the
  `axioms` region is empty.
- The impl region is entirely R/I ⇒ `conf_skip = false`; `conformance_check.py`
  runs a real fuzz over all 8 input combinations.
- The single behavioral change is the relative ORDER of the exit guard and the
  writers (op 3 moved ahead of ops 4–5). The prepatch impl reproduces the
  pre-patch order (writers, then exit), so in the `hasChanges ∧ checkOnly` case it
  sets a writer flag while the spec forbids it — exactly the discriminating clause
  G-DIFF needs.
