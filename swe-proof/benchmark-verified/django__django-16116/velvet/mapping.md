# mapping.md — django__django-16116

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5d36a8266c7d5d1994d7a7eeb4016f80d9cb0401`, states the type
abstraction, and gives the provenance of the one referenced callee.

Repo file under change:
`django/core/management/commands/makemigrations.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `runCheckedWrite (checkOnly update : Bool)` | the `else:` branch of `Command.handle` — `django/core/management/commands/makemigrations.py:251-257` (the branch taken when `changes` is non-empty: it decides whether to emit a migration artifact and/or terminate with a non-zero status) | the modeled changed function: what the step does with a detected non-empty change set |
| `checkOnly` (param) | `check_changes = options["check_changes"]` (`handle`, set from the `--check` flag wired in `add_arguments`, `makemigrations.py:69-76`) | whether the run is a check-only query ("are migrations missing?") |
| `update` (param) | `self.update` (`handle`, set from the `--update` flag) | whether detected changes should be folded into the most recent existing migration rather than emitted as a fresh migration |
| `WriteKind` / `out.written` | which migration artifact (if any) the step emits: `noWrite` (none), `latest` (`self.write_to_last_migration_files(changes)`, `:254`), `standard` (`self.write_migration_files(changes)`, `:256`) | the emitted-artifact observable |
| `out.exited` | whether the process terminates with a non-zero status (`sys.exit(1)`, `makemigrations.py:253` post-patch / `:257` pre-patch) | the abort observable |
| `stepOutcome checkOnly update` | the pure spec of the desired branch behaviour (deep model of the `else:` branch) | pins both observables together |

The pre-patch repo control flow this change re-orders (for the refinement
audit, not referenced from the consumer spec view):

```python
else:                                   # base_commit :251
    if self.update:
        self.write_to_last_migration_files(changes)
    else:
        self.write_migration_files(changes)
    if check_changes:
        sys.exit(1)
```

i.e. the artifact is emitted **first**, then (only in check-only mode) the
process aborts — so a check-only query leaves a migration artifact behind. The
gold patch moves the `if check_changes: sys.exit(1)` guard **above** the
write block, so in check-only mode the abort fires before any write runs and no
artifact is emitted.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `check_changes` (a `bool` option) | `checkOnly : Bool` | `True ↔ true`, `False ↔ false` |
| `self.update` (a `bool` option) | `update : Bool` | `True ↔ true`, `False ↔ false` |
| which write method ran (or none) | `WriteKind` (`noWrite`/`latest`/`standard`) | `write_to_last_migration_files(changes)` ↔ `latest`; `write_migration_files(changes)` ↔ `standard`; neither invoked ↔ `noWrite` |
| process terminated with a non-zero status via `sys.exit(1)` | `out.exited : Bool` | a `SystemExit` raised with a non-zero code ↔ `exited = true`; normal fall-through ↔ `exited = false` |
| the pair (artifact emitted, aborted?) | `StepOutcome { written, exited }` | the two observable effects of the branch, recorded together |

The branch operates on a fixed non-empty `changes` set (the `else:` arm is only
reached `if changes`); the value of `changes` is orthogonal to the modeled
decision, so it is not carried (mapping per SPEC_GUIDE §2: model only the
touched observables).

## 3. Callee provenance — the abort primitive (A-reference)

**Callee:** `sys.exit` (CPython standard library), invoked as `sys.exit(1)` at
`django/core/management/commands/makemigrations.py:253` (post-patch) / `:257`
(pre-patch).

It is an **unchanged** callee — the gold patch does not modify `sys.exit`; it
re-orders the *caller* so the `sys.exit(1)` guard runs before the write block.
There is therefore **no consumed axiom** in `Solution.lean`: the abort outcome
is modeled deeply (the check-only branch returns `{ written := noWrite,
exited := true }`). The one runtime property the deep model relies on is the
behaviour of the abort primitive, modeled as an **A-reference** (validated
against the real stdlib callee by `axiom_check.py` / G-AX):

> `sys.exit(n)` with `n ≠ 0` raises `SystemExit` carrying the non-zero code,
> and that exception **unwinds the stack** — so any statement sequenced *after*
> the `sys.exit(1)` in the same function body does **not** execute, and the
> process terminates with a non-zero status.

This is exactly the property that makes the gold re-ordering correct: with the
abort placed *before* the write block, a check-only run aborts and **no** write
statement runs, so no migration artifact is emitted. `axiom_check.py` validates
this against the real `sys.exit` (G-AX). No flag-dependent configuration applies
(the primitive's raise-and-unwind behaviour is unconditional for a non-zero
argument).

## 4. G-CONF disposition / fuzz seed

`meta.json conf_skip = true`. The only observable the fix produces is a **side
effect**: whether a migration artifact is emitted on disk and whether the
process terminates with a non-zero status. Reproducing it requires the full
migration machinery (a populated app registry, a `MigrationLoader`, a
`MigrationAutodetector` returning a non-empty `changes`, the
`write_migration_files` / `write_to_last_migration_files` filesystem writers and
a temporary migration module) — i.e. the F2P integration test
`MakeMigrationsTests.test_makemigrations_check`
(`tests/migrations/test_commands.py`), not a DB-free transliteration this gate
can fuzz over ≥10⁵ inputs. The discriminating fact is the statement **order**
(abort vs write), exercised only by the live `sys.exit` + write machinery and
covered by `axiom_check.py` (G-AX). The R/I content of the branch reduces to the
constant truth table `stepOutcome(checkOnly, update)` over two mode flags — there
is no input-content-dependent computation to differentially refute. Soundness is
carried by G-VERIFY (the spec provably forces `checkOnly ⇒ written = noWrite`),
G-DIFF (the prepatch, which writes then aborts, fails exactly that clause), and
G-AX (the real `sys.exit(1)` raises-and-unwinds so a statement after it does not
run). No conformance fuzz seed is used (status=skip stub).
