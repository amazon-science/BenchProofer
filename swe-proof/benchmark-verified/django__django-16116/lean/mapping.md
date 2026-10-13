# mapping.md — django__django-16116

## Symbol binding (file:line @ base_commit `5d36a8266c`)

- Modeled function: `Command.handle(self, *app_labels, **options)` in
  `django/core/management/commands/makemigrations.py`, lines 192–256
  @ base_commit. The changed region is the final `else:` arm of the
  "changes / no-changes" branch, lines 248–256.
- Lean modeled symbol: `implementation_processChanges` /
  `problem_spec_processChanges` / `correct_processChanges` in `Solution.lean`.

## The change (gold patch, lines 248–256 @ base_commit)

Pre-patch (buggy) control flow when changes were detected (`else:` arm):
```python
else:
    if self.update:
        self.write_to_last_migration_files(changes)
    else:
        self.write_migration_files(changes)
    if check_changes:
        sys.exit(1)
```
Post-patch:
```python
else:
    if check_changes:
        sys.exit(1)
    if self.update:
        self.write_to_last_migration_files(changes)
    else:
        self.write_migration_files(changes)
```
The fix hoists the `if check_changes: sys.exit(1)` above the writers, so in
verification-only mode the command exits BEFORE emitting any migration output.

(The patch also rewords the `--check` argument help string, lines 70–73. That is
a non-behavioral documentation string with no observable effect on any
FAIL_TO_PASS / PASS_TO_PASS test; it is carried verbatim in `patch.diff` for
gold fidelity and is tagged I-doc / non-modeled in refinement.md.)

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `bool(changes)` — were model changes detected | `hasChanges : Bool` | `True ↔ true` |
| `check_changes` (the `--check` flag) | `checkOnly : Bool` | `True ↔ true` |
| `self.update` (the `--update` flag) | `mergeIntoLast : Bool` | `True ↔ true` |
| `self.write_to_last_migration_files(changes)` executed | `result.wroteToLast = true` | did-run ↔ true |
| `self.write_migration_files(changes)` executed | `result.wroteNew = true` | did-run ↔ true |
| `sys.exit(1)` requested | `result.exitCode = some 1` | exit(n) ↔ some n |
| run completes without `sys.exit` | `result.exitCode = none` | normal ↔ none |

Only the observable "did this writer run?" / "what exit was requested?" matters
for the F2P test (`test_makemigrations_check`: asserts `SystemExit` is raised
AND the migration module directory does NOT exist afterwards — i.e. no writer
ran). The writers' file-content behavior is unchanged and irrelevant to this fix,
so they are modeled by a Boolean "ran" flag, not abstracted behind an opaque
callee.

## Callee provenance + flag deps

- No consumed axiom, no A-reference deep model. The two writer procedures are
  unchanged side-effecting steps; their only fix-relevant observable (whether
  they execute) is reproduced concretely by the impl's control flow (R/I).
- Flag deps: branch order is governed by `hasChanges` (outer), then `checkOnly`
  (the hoisted guard), then `mergeIntoLast` (writer selection). G-CONF fuzzes all
  2³ = 8 combinations.

## Pinned G-CONF fuzz seed
`SEED = 16116`
