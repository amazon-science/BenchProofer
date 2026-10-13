# mapping.md — django__django-16116

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5d36a8266c7d5d1994d7a7eeb4016f80d9cb0401`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change:
`django/core/management/commands/makemigrations.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `produce_changes_or_report(store, check_mode, update_variant)` | the `else:` branch of `Command.handle` (`django/core/management/commands/makemigrations.py:250-256`, the changes-present branch) | the modeled changed control-flow region |
| `CheckFailureExit` (exception) | `sys.exit(1)` (`makemigrations.py:256` pre-patch / `:253` post-patch) | the process-exit the command performs in check mode to report missing migrations |
| `write_update_artifacts(store)` *(axiom — A-consumed)* | `Command.write_to_last_migration_files` (`makemigrations.py:258`, called at `:252`) | unchanged "update" artefact writer the changes-present branch invokes |
| `write_fresh_artifacts(store)` *(axiom — A-consumed)* | `Command.write_migration_files` (`makemigrations.py:330`, called at `:254`; appends to `self.written_files` at `:363`) | unchanged fresh-migration artefact writer the changes-present branch invokes |
| `store: List[int]` | `self.written_files` (`makemigrations.py:103`, a `list`; appended at `:363`) and, behaviourally, the on-disk set of produced migration files | the produced-migration-artefact set the writers grow |
| `check_mode: bool` | `check_changes` local = `options["check_changes"]` (the `--check` flag, declared `makemigrations.py:69-74`) | check-mode flag |
| `update_variant: bool` | `self.update` = `options["update"]` (the `--update` flag, declared `makemigrations.py:84-92`) | update-variant flag |
| `LEDGER.produced` (ambient tally, held at `Acc(…, 1/2)`) | the number of migration-artefact writes committed to the durable medium: one per `open(writer.path, "w")` that the writers perform for a migration file (`makemigrations.py:361`, and the same statement reached through the update writer's delegation) | "an artefact really reached the medium", independent of which list recorded it |
| `ProducingStepDeclined` (exception) | the `CommandError`s `write_to_last_migration_files` raises when the most recent migration cannot be folded into — applied / squashed (`replaces`) / depended-on / no leaf migration (`makemigrations.py:264-292`) | the refusal outcome the update writer reports before committing anything |
| `ProducingStepFailed` (exception) | the error a writer reports when it cannot render the pending changes into artefacts — `MigrationWriter.as_string()` raising (e.g. `ValueError("Cannot serialize …")`, `makemigrations.py:360`), or the medium refusing the artefact at `open(writer.path, "w")` (`:361`) | the non-completion outcome, reachable from BOTH writers (the update writer delegates to the fresh one at `:328`, so `:330` runs for both) |
| `fresh_artifact_yield()` / `update_artifact_yield()` *(opaque `@Pure @ContractOnly`, `>= 1`)* | the number of migration files ONE complete run of that writer produces for the pending changes at hand = `sum(len(v) for v in changes.values())` (`makemigrations.py:335-390` loops over every migration in `changes`) | how much one run of that step yields — unpinned, because `changes` is not a model parameter |
| `update_step_declines()` *(opaque `@Pure @ContractOnly`)* | whether the foldability guards at `makemigrations.py:264-292` fire for the repository state | the condition under which the refusal outcome, and only it, is available |
| `update_step_fails()` / `fresh_step_fails()` *(opaque `@Pure @ContractOnly`)* | whether that step's rendering of the pending changes cannot be carried through (the `as_string()`/write step at `:360-362` raising) | the condition under which the non-completion outcome, and only it, is available; ONE PER STEP because the two steps render different artefacts (the update step re-renders the amended leaf migration and then removes the previous file, `:378`) so either can be unable to proceed where the other is not |

The pre-patch repo control flow the change reorders (for the refinement audit):
```python
else:
    if self.update:                                  # writer reached FIRST
        self.write_to_last_migration_files(changes)
    else:
        self.write_migration_files(changes)
    if check_changes:                                # exit AFTER writing
        sys.exit(1)
```
The post-patch (gold) control flow:
```python
else:
    if check_changes:                                # exit FIRST
        sys.exit(1)
    if self.update:                                  # writer reached only if not check
        self.write_to_last_migration_files(changes)
    else:
        self.write_migration_files(changes)
```

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.written_files` (`list`) + on-disk produced migration files | `List[int]` of artefact-kind tokens | each produced migration file ↔ one token appended to `store`; "an artefact was produced" ↔ `len(store)` grew; "no artefact produced" ↔ `store` unchanged. The token VALUE encodes the KIND of producing step that emitted it: `0` = a fresh-migration-file artefact (`write_migration_files`), `1` = a fold-into-most-recent artefact (`write_to_last_migration_files`). The two steps have observably different on-disk outcomes (a new file vs. the most recent migration file rewritten/replaced), so WHICH kind of artefact was produced is part of the observable. Observed: growth/unchanged, prefix-preservation, and the kind of every new token (no file content beyond kind). |
| `check_changes` (`bool` from `--check`) | `check_mode: bool` | identity |
| `self.update` (`bool` from `--update`) | `update_variant: bool` | identity |
| `sys.exit(1)` (process exit / `SystemExit`) | `raise CheckFailureExit()` | a non-returning failure outcome the caller observes; a builtin exception in an `Exsures` crashes the Nagini translator, so a user-defined class stands in (SPEC_GUIDE §2). |
| `changes` dict (the pending changes, always non-empty in this branch) | (implicit) | the branch is entered only when changes exist; the writers consume `changes` and produce ≥1 artefact. Not carried as a parameter — the branch's precondition is "changes present", and each writer's effect (≥1 token) encodes that ≥1 artefact results. |
| artefact writes committed to the durable medium (the count of `open(<migrations>/<name>.py, "w")` calls the writers make, `makemigrations.py:361`) | `LEDGER.produced: int`, an ambient field held at `Acc(…, 1/2)` throughout | "N artefacts really reached the medium" ↔ `LEDGER.produced` advanced by N. Counted at the medium, so it is INDEPENDENT of which list the writer recorded the paths in — this is why it senses a producing run whose tokens went to another record. EXCLUDED from the count, deliberately: the `__init__.py` package marker (`:357` — not a migration artefact), the `os.remove(prev_path)` of the superseded file on the update path (`:378` — a deletion, not a production), and `run_formatters(self.written_files)` (`:390` — reformats artefacts already committed and recorded, producing none). Held at HALF permission because the medium is not the caller's variable: the subject may READ the tally but only a writer axiom may advance it. |
| `ValueError("Cannot serialize …")` (and any error the medium raises for the artefact write) propagating out of the branch | `raise ProducingStepFailed()` | a non-returning outcome the caller observes; user-defined because a builtin in an `Exsures` crashes the translator. The real state at that point is PARTIAL and input-dependent — measured on the real callee: one unserializable app commits 0 of a yield of 1; two apps good-then-bad commit 1 of a yield of 2 — so the model bounds it (`≤` one run's yield, prefix kept, no token without a commit) rather than pinning a count. |
| `CommandError("Cannot update …")` propagating out of the branch | `raise ProducingStepDeclined()` | same refinement; the real callee raises this BEFORE any artefact write for that run (the guards precede the build/write, `:264-292` vs `:328`), which is what licenses the "nothing committed, nothing recorded" conjuncts. |

The control flow (`if check_mode: raise … ; if update_variant: …`) is **I**
(identical concrete `if`/`raise`/call structure under the flag and exception
refinements above).

## 3. Callee provenance (kind-A, A-consumed — checked by G-AX / axiom_check.py)

Both writers are **unchanged** callees the patch does NOT touch; the patch only
moves the `sys.exit(1)` ahead of them. They are axiomatised with the weakest
fact the proof needs: **invoking the writer appends AT LEAST one produced-file
token to `store`, keeping the previously-produced tokens as a prefix, and every
token it appends carries that writer's kind (`1` for the update writer, `0` for
the fresh writer)** — i.e. each writer is a genuine artefact-PRODUCING step of
its own observable kind. The kind conjunct is what lets the function's
postcondition bind the variant flag to WHICH writer ran (the two writers are
behaviourally distinct in the repo — folding into and rewriting the most recent
migration file vs. emitting a new one — so an impl that swaps or collapses the
dispatch is observably wrong). The exact append count
tracks the number of migrations in `changes` (one per migration: a one-app
changes dict grows the store by 1, a two-app dict by 2, an empty dict by 0),
which the axiom does NOT pin — `Requires(list_pred(store))` imposes no
constraint on `changes`, so the only contract sound for every `changes` is
growth (`len(store) >= len(Old) + 1`), never an exact `== +1`. (An `== +1`
axiom would be strictly stronger than the real callee and therefore unsound:
G-AX would observe a two-app changes dict append two tokens.)

### 3.1 `write_fresh_artifacts` ↔ `Command.write_migration_files`
**Callee:** `django/core/management/commands/makemigrations.py:330`. For each
migration in `changes` it constructs a `MigrationWriter`, and (unless dry-run)
writes the migration file to disk (`open(writer.path, "w")…fh.write(...)`,
`:361-362`) and records it: `self.written_files.append(writer.path)` (`:363`).
So a non-dry-run call on a non-empty `changes` appends one path per migration
(≥1) to `self.written_files` and creates that many files on disk. The axiom's
"at least one token" (`len(store) >= len(Old) + 1`) is the weakest non-vacuous
form (≥1 artefact produced; the proof needs only that the store GREW, never the
exact count). It deliberately avoids `== +1`, which the real callee violates for
a multi-migration `changes` (G-AX fuzzes a two-app dict and observes +2). The
previously-recorded paths are untouched (append only).

### 3.2 `write_update_artifacts` ↔ `Command.write_to_last_migration_files`
**Callee:** `django/core/management/commands/makemigrations.py:258`. It folds
the pending changes into the latest migration and ultimately writes the updated
migration file (delegating to `MigrationWriter` / file writes), likewise
producing a migration artefact and recording it. Same axiom shape: invoking it
produces ≥1 artefact (store grows), previously-produced tokens kept.

### 3.3 The steps of one writer run, and which have an observable

One run of the real fresh writer does the following, in order (base_commit line
numbers). Each step is either an observable an axiom leg carries, or a step
deliberately without one — the enumeration is what makes "the axiom has a leg
for everything the callee does" checkable:

1. per-app heading log (`:336-337`) — no observable.
2. per-migration `MigrationWriter` construction, the verbose listing and the
   `--scriptable` echo (`:340-350`) — no observable of its own, but note that
   `writer.path` (`:344`, `:352`, `:361`) **CAN RAISE** too: it resolves through
   `MigrationWriter.basedir`, which raises `ValueError("Django can't create
   migrations for app … because migrations have been disabled via the
   MIGRATION_MODULES setting.")` when the app's migrations module is `None`
   (`django/db/migrations/writer.py:205-216`). Measured below; it is the same
   non-completion leg, entered before anything is committed.
3. `os.makedirs(...)` and the `__init__.py` package marker (`:352-357`) — creates
   a package marker, NOT a migration artefact: excluded from the tally (§2).
4. `migration_string = writer.as_string()` (`:360`) — **CAN RAISE** when the
   change set holds something the serializer cannot render. This is the
   non-completion leg: `Exsures(ProducingStepFailed, …)`.
5. `open(writer.path, "w") … fh.write(migration_string)` and then
   `self.written_files.append(writer.path)` (`:361-363`) — the commit-then-record
   pair, in that order and inside the same `with`. This ordering is exactly why
   the non-completion leg can assert `LEDGER.produced >= Old + (record growth)`
   (the record never gains a token the medium did not take an artefact for) but
   cannot assert an equality with the yield: the run may stop before the
   remaining migrations of the same `changes` dict.
6. update path only: `os.remove(prev_path)` of the superseded migration, or the
   manual-porting warning in its place (`:369-380`) — a deletion or a log; no
   production, so the tally does not move.
7. `run_formatters(self.written_files)` (`:390`) — a WHOLE-CONTAINER pass over
   the record, including the tokens that were already in it when the branch was
   entered. It reformats files already committed and already recorded: it
   produces no artefact and records none, so it has no observable in this model
   (and it is reached only on the completed path, never on the raising one).

So steps 1-3, 6 and 7 carry nothing, and steps 4-5 are precisely the two legs
each writer axiom now states:
* normal return — `len(store) == len(Old) + <step>_artifact_yield()`,
  `LEDGER.produced == Old + <step>_artifact_yield()`, every newly-recorded token
  of that step's kind, prefix kept, and `not <step>_step_fails()`;
* `ProducingStepFailed` — prefix kept, new tokens still of that step's kind,
  `len(store) <= len(Old) + yield()`, and
  `Old + (record growth) <= LEDGER.produced <= Old + yield()`.

The growth clause is stated as an equality against the OPAQUE yield symbol
rather than a literal for the reason given above §3.1; that is what makes it
sound for a one-app and a two-app `changes` dict alike.

The update writer (`:258`) has the same two legs, because after its foldability
guards it DELEGATES to the fresh writer (`:328`) — measured: `--update` on an
unserializable change set raises the same `ValueError` having committed nothing.
It carries, in addition, the refusal leg (`ProducingStepDeclined`), whose guards
run before anything is written.

**Measured extents of the non-completion leg** (each case in a fresh process with
a fresh app tree, gold worktree; the tally instrumented at `open(...,"w")` per
§2):

| input | real outcome | record growth | tally | one run's yield |
|---|---|---|---|---|
| one app, unserializable default | `ValueError` | +0 | +0 | 1 |
| two apps, good then bad | `ValueError` | +1 (kind `0`, prefix kept) | +1 | 2 |
| two apps, bad then good | `ValueError` | +0 | +0 | 2 |
| `--update`, unserializable | `ValueError` | +0 | +0 | 1 |
| migrations module disabled (`MIGRATION_MODULES: None`) | `ValueError` | +0 | +0 | 1 |
| `--check`, unserializable | `SystemExit(1)` | +0 | +0 | 1 |

The extent is input-order dependent, which is why the leg states an envelope
rather than a count; and check mode never reaches the step at all, which is why
the leg carries `not check_mode`.

**Why the axiom is the weakest sufficient contract.** The proof depends on two
facts about each writer: (a) it is artefact-producing (the store grows when a
writer runs), and (b) the artefacts it produces are of ITS kind (`1` update /
`0` fresh) — nothing about how many files, their paths, or any content beyond
the kind. The check-mode discriminating clause — *in check mode the store is
left exactly as it was* — is violated by the pre-patch order purely because a
writer ran (and produced an artefact) before the exit; the exact growth is
immaterial. The variant-binding clauses — *every new token's kind matches the
requested variant* — are dischargeable only by dispatching to the matching
writer, which is what makes a swapped/collapsed/doubled writer dispatch
unverifiable. `len(store) >= len(Old) + 1` (paired with the prefix-preservation
conjunct and the per-writer kind conjunct) is the concrete carrier of "grew by
a positive amount of this writer's kind, prefix preserved", which is all the
differential needs.

**Soundness check (G-AX):** `axiom_check.py` is split into a **patch-state-independent
authoritative portion (A)** and a **patch-state-aware informational portion (B)**,
so it returns 0 whether run at `base_commit` or with the gold patch applied
(the axioms are about the UNCHANGED writers; `meta.json axiom_check_requires: any`).
- Portion A (drives the rc): runs the REAL `Command.write_migration_files` on
  real `changes` dicts built by the real `MigrationAutodetector.changes`, and
  asserts the **weakened** contract: a one-app dict grows `written_files` by 1,
  a **two-app dict by 2** (proving `>= +1` is required and `== +1` would be
  UNSOUND), an empty dict by 0; the previously-produced tokens are kept as a
  prefix and each recorded file exists on disk.
- Portion B (informational): runs `makemigrations` WITHOUT `--check` and asserts
  it writes a file (writer reached in both patch states); runs `makemigrations
  --check` and asserts it raises `SystemExit`, then observes whether it ALSO
  wrote a file — at `base_commit` it does (the bug), with the gold fix it does
  NOT (the F2P observable) — reporting the detected state without failing.
stdlib + Django only; exit 0 iff the axiom-soundness obligations (A) hold.

**Flag dependency:** the writers produce on-disk artefacts only when
`self.dry_run is False` (`makemigrations.py:350`). This branch's behaviour is
specified for the non-dry-run command (the F2P test calls
`makemigrations --check` without `--dry-run`); `axiom_check.py` sets
`dry_run=False`, matching the tested configuration.

## G-CONF (differential conformance)

`conformance_check.py` diffs the SHADOW (the `# impl-start`/`# impl-end` region
of `produce_changes_or_report`, copied verbatim with the contract calls stripped;
no `@Pure` helpers exist to copy) against the ORACLE (the REAL patched
`Command.handle` changes-present branch, §1), driven live in the instance
container with the gold patch applied.

**Oracle — called, not transliterated.** `call_command(Command(), <labels>,
"--check"?, "--update"?)` runs the real patched `handle` against a fixture app
tree whose `0001_initial` omits a field that `models.py` declares, so the real
`MigrationAutodetector` reports genuine pending changes and the modeled branch is
really entered (asserted per run — an input that missed the branch cannot pass).
The two `@ContractOnly` callees have no body to copy, so they resolve to the REAL
writers they axiomatise (§3): `write_update_artifacts` →
`Command.write_to_last_migration_files`, `write_fresh_artifacts` →
`Command.write_migration_files`, invoked on a real `Command` with
`written_files` pre-seeded to the model prefix. Nothing is stubbed; the real
writers serialize real migrations to disk (and run black) on every observation.
The producing step behind each appended entry is read off the real execution by
delegating observers that record the OUTERMOST writer in progress (the update
writer delegates to the fresh one).

**Type bridge (§2, inverted).** `store: List[int]` ↔ `Command.written_files`: a
model prefix of length k is realized as k real pre-existing produced-file paths
pre-seeded into `written_files`; a real appended path maps back to its kind token
(0 = fresh file, 1 = fold-into-most-recent) by its producing step. `check_mode` ↔
`--check`, `update_variant` ↔ `--update` (identity). `CheckFailureExit` ↔ the
real `sys.exit(1)`/`SystemExit`, with the status required to be exactly 1. The
`changes` dict is not a model parameter, so its size is a generated dimension
(`napps` ∈ {1,2} → real growth +1/+2, exercising why §3's axiom is `>= +1`).
Non-dry-run only, per §3's flag dependency.

**Inputs.** Pinned seed **`SEED = 16116`**, `N_FUZZ = 100000`, total **100160**
Requires-satisfying inputs. The decision space `check_mode × update_variant ×
napps` is FINITE (8 classes) and is ENUMERATED EXHAUSTIVELY against the real
patched `handle`, each class re-run `REAL_REPEATS = 3` times and required to
reproduce itself (nondeterminism is a failure); the real writers are invoked
directly at prefix lengths `(0,1,2,3,5,8)` to establish append-only
prefix-independence, and the handle-observed kinds are cross-checked against the
directly-invoked writer kinds. 88 real repo invocations total. Because one real
run costs ~0.2–0.7 s (real migration serialization + black), the ≥1e5 fuzz inputs
replay those recorded real observations; the shadow's growth is keyed by
`(update_variant, napps)` from the real WRITER observation while the oracle's is
keyed by `(check_mode, update_variant, napps)` from the real HANDLE observation,
so the two sides never read the same slot and a wrong dispatch or a wrong
exit/write order still disagrees.

**Recorded verdict: `G-CONF=pass`** (0 disagreements). Refutation capability was
verified, not assumed: the same script run against the UNPATCHED /testbed FAILS
on the F2P shape (`check_mode=True`: real `store=[0]` — an artefact written
before the exit — vs shadow `store=[]`), a shadow with the writer dispatch
swapped FAILS (kind `[1]` vs real `[0]`), and a shadow restored to the pre-patch
statement order FAILS.
