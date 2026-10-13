# Reproducing the benchmark from scratch

This document builds the verified twin of a SWE-bench-style benchmark from an
empty checkout. It assumes [architecture.md](architecture.md) for what the
artifacts mean. To point the pipeline at a *different* benchmark, see
[adapting_a_benchmark.md](adapting_a_benchmark.md).

A clone ships the pipeline, the prompt corpus, the Lean workspace manifest, and
whichever constructed bundles the release includes. It deliberately does **not**
ship the dataset (`data/`), the task-repository mirrors (`repos/`), the built
Lean object files (`lean_shared/.lake`, several GB), the container images, or any
run artifacts (`experiments/`). All of those are reconstructible from pinned
identifiers, and committing them would put mutable multi-gigabyte state under
version control.

## 1. Prerequisites

Only the parts you use are required. Static gates need much less than the full
suite.

| for | you need |
|---|---|
| everything documented here | Python >= 3.10; `pip install -e ".[dev,eval,viz,figures]"` -- the tests and the linter, the evaluation providers, the review site, and the analysis figures. `pip install -e .` alone is enough for construction, the gates, `fetch-dataset` and `score` |
| freezing a dataset | network access to the HuggingFace Hub. None of the registered benchmarks is a gated dataset, so an anonymous fetch works, but the Hub rate-limits unauthenticated requests and says so on stderr; `hf auth login` (older `huggingface-hub` releases ship that CLI as `huggingface-cli login`) or `HF_TOKEN=...` raises that limit, and a token is required outright for a benchmark whose dataset is gated or private |
| the Docker gates and the correctness oracle | a Docker daemon this account can reach, and enough disk for per-instance images (they are pulled on demand, one per instance) |
| the same, when daemon access comes from a unix group | membership of the daemon's group -- but normally no configuration, because the pipeline *probes* how it reaches the daemon rather than assuming: plain `docker` first, then `sg <group> -c`, which is what picks up a group held only as a *supplementary* one. `SBU_DOCKER_CMD` names the command outright for anything a probe cannot discover (podman, `sudo -n docker`, a remote client); see section 10 |
| the imperative verifier backend | `conda` (Miniforge or Miniconda), then `bash scripts/setup_verifier_env.sh`, which builds a separate env holding the verifier, its pinned SMT solver and a JVM. `bash scripts/setup_verifier_env.sh --check` validates such an env without installing anything (section 4) |
| the Lean-family backends | `elan`, then one build of the shared Lean workspace (section 4). `curl https://elan.lean-lang.org/elan-init.sh -sSf \| sh -s -- -y` installs it; `install.sh` prepends `$HOME/.elan/bin` to `PATH` but installs nothing itself, and stops with that command if `elan` is not found |
| any agentic phase (construct, prove, audit, eval) | the **Claude Code CLI** on `PATH`, plus credentials. Every agentic phase runs through `claude_agent_sdk`, which spawns the CLI as a subprocess, so the package's own dependencies are not sufficient: install it with `npm install -g @anthropic-ai/claude-code` and check with `claude --version`. Credentials must be in the launching process's own environment on one of the routes the preflight accepts: `CLAUDE_CODE_USE_BEDROCK=1`, `CLAUDE_CODE_USE_VERTEX=1`, `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`, or a login the CLI itself stored in `~/.claude/.credentials.json`. The corpus was built with this CLI; another coding agent's command-line tool, such as Codex CLI or Kiro CLI, can take its place through `run_agent_step` (see Installation in the README) |

Two deliberate design points about the prerequisites:

* **The verifier lives outside the package.** Each backend is invoked through a
  single wrapper script that owns the environment selection, the wall clock, and
  the exit protocol (`0` verified, `124` timed out, and for proof-carrying
  backends `3` "only proof obligations remain"). Nothing else in the pipeline
  knows how to run a verifier. That is why a missing verifier environment exits
  with a distinct code instead of looking like a verification failure: the two
  must never be confusable, because one is an infrastructure fault and the other
  is a fact about an artifact.
* **The Lean workspace is one workspace, pinned by commit.** Every Lean-family
  backend elaborates against the same toolchain and the same dependency
  revisions, recorded in `lean_shared/PINS.md` and `lean_shared/lean-toolchain`.
  A verdict is only meaningful relative to the prover it was produced by, so the
  pins are part of the artifact, not a convenience, and `install.sh` fails rather
  than hand back a workspace that has drifted from them (section 4).

## 2. Freeze the dataset

```bash
swebench-unified fetch-dataset          # writes data/<benchmark>/test.jsonl
```

One script, `scripts/fetch_dataset.py`, serves every registered benchmark: it
downloads the rows the registry entry names, keeps only the subset the pipeline
targets, normalizes them into the frozen row schema, writes them deterministically
(sorted by instance id, one compact JSON object per line), and prints a sha256 of
the result. `--benchmark <name>` freezes one other than the active one, and
`--limit N` takes a smoke slice, which is refused unless `SBU_DATA_ROOT` points the
write away from the corpus data root.

Determinism here is load-bearing. `instance.json` inside every bundle is a copy
of one of these rows, and the integrity gate compares the two. If the frozen file
were written in a different order or with different formatting on another
machine, every bundle in the corpus would read as tampered with. Printing the
checksum lets anyone confirm they hold the same dataset without diffing every row.

## 3. Mirror the task repositories

```bash
python scripts/setup_repos.py           # bare-clone + verify every pinned SHA
python scripts/setup_repos.py --verify  # verify only, no network
```

This creates bare mirrors under `repos/` (or `SBU_REPOS_ROOT`) and then verifies
that every commit the frozen dataset pins is actually present. Construction never
writes to a mirror: it materializes a disposable worktree per instance and
removes it on every exit path. A single construction can also be pointed at an
existing clone with `construct --repo PATH`.

Repositories are mirrors rather than submodules on purpose. A submodule would pin
a superproject-visible commit and make the benchmark's own history depend on
upstream repository availability, while what the pipeline actually needs is
"these SHAs are fetchable", which is exactly what the verify pass checks.

### Precompute the evaluation localization

```bash
python scripts/build_eval_localization.py          # writes data/<benchmark>/eval_localization.json
python scripts/build_eval_localization.py --check   # compare against the file on disk
```

The evaluation modes whose signal *is* edit localization (0 and its audited twin
100, section 9) tell the solver which repository functions the reference patch
touches. That is derived from the patch, so it is precomputed here, offline, and
never in a process that talks to a solver. This script is the derivation: for each
changed Python file it reads the file as of `base_commit` out of the mirror and
records the innermost function or class enclosing each changed line, together with
the patch's file list. Same dataset plus same mirrors gives the same bytes, and
`--check` reports field-by-field agreement against a file already on disk instead
of overwriting it.

Run it before evaluating in a localization mode. A formal backend's bundle may
already record the same facts in its `meta.json`, and that stays the primary source
where it is present; this file fills in per field and is the only source for a
backend whose bundle records neither. When neither has anything, those modes refuse
to build the task rather than quietly presenting the solver with the baseline's
information and reporting it under another mode's label. The other modes do not
read the file, so a benchmark can be constructed and smoke-tested before it exists.

## 4. Build the verifier environments

```bash
bash install.sh                       # one shared Lean workspace: builds against
                                      # the recorded pins, fetches prebuilt object
                                      # files, builds the local anchor
bash scripts/setup_verifier_env.sh    # the imperative backend's verifier env
```

`install.sh` is idempotent. It fetches prebuilt object files for the large
mathematical library rather than compiling it, which turns roughly an hour of
build into a download.

It builds against the pins rather than re-resolving them, and that distinction is
the whole point of pinning here. `lean_shared/lake-manifest.json` is the pin:
`lake build` materializes every dependency at the revision recorded there, while
`lake update` re-resolves each one from the *ref* the lakefile requests -- which
for 9 of the 12 packages is a branch (`main` or `master`) -- and rewrites
`lean-toolchain` as well. So the install never updates. After the build it
compares the workspace against `lean_shared/PINS.md`, dependency revisions and
toolchain, and exits non-zero naming every difference: a workspace built from
other revisions is a different prover, and its verdicts would not describe the
artifact being shipped. Re-resolution is available as `SBU_LEAN_REPIN=1`, which
says on stdout that it moves the pins; doing it means updating PINS.md to match
and accepting that every recorded Lean verdict describes the previous revisions.

That comparison is `python scripts/lean_pins.py`, which needs neither a
toolchain nor a build, so the pins can be checked before committing to one; the
test suite runs it against the checkout for the same reason.

`setup_verifier_env.sh` is idempotent too, and needs only a `conda` executable
(Miniforge, Miniconda, or anything with `conda info --base`; point `SBN_CONDA` at
the binary if it is not on `PATH`) and network access. It creates the env
`swebench-nagini-verifier` -- override the name with
`SWEBENCH_NAGINI_VERIFIER_ENV` or the location with
`SWEBENCH_NAGINI_VERIFIER_PREFIX` -- containing Python 3.10 (`SBN_SETUP_PYTHON`;
the verifier's pinned `typed-ast==1.5.4` declares support no further than 3.10 and
ships ABI-tagged wheels to match), a conda-forge JDK *inside* the env at
`<prefix>/lib/jvm` (openjdk 17 by default, `SBN_SETUP_JDK`; a system JDK is not
picked up, because that path is the `JAVA_HOME` the wrapper exports), and the
verifier at the pin declared by the `verifier-nagini` extra in `pyproject.toml`,
which is the single source of that version -- the script reads it from there rather
than repeating it.

The shipped corpus was verified with the env a fresh build reproduces: Python
3.10, `nagini==1.2.0`, the versions that pin carries with it (`z3-solver==4.8.7.0`,
`mypy==0.900`, `typed-ast==1.5.4`, `jpype1==1.5.0`), Viper/Silicon from inside the
nagini wheel, and openjdk 17 in the env. The script prints the interpreter, nagini,
Z3 and JDK versions it found and lists the Viper backend jars, so an env can be
compared against this list without reading any code.

Add `--check` to validate an existing env and install nothing: every missing or
off-pin piece becomes an error naming the command that would supply it, which is
the form to run at the start of a batch run or a CI job. `SBN_SETUP_DRY_RUN=1`
prints what a build would do and installs nothing; `SBN_SETUP_SMOKE=0` skips the
closing end-to-end verification of a one-function module; `--help` lists the rest.

The environment is separate from the pipeline's own on purpose: everything the
verifier depends on is an exact pin, and some of it is tooling this package also
uses -- the verifier requires `pytest==7.0.0`, the `dev` extra requires
`pytest>=8.0`, and the pinned `typed-ast==1.5.4` stops at Python 3.10 while the
package itself requires 3.10 or newer. One env for both therefore resolves at
least one of them to a version the other rejects. Nothing activates the verifier
env -- the wrapper script finds the prefix and runs the verifier out of it. The
setup script's last two steps are the ones worth understanding, because both
failures they catch are otherwise invisible: it proves `scripts/nagini_verify.sh`
resolves *this* env on its own, since a complete env the wrapper does not search
reads downstream as "no verdict" and a same-named env it finds first yields
verdicts from a verifier you did not check, and then verifies a trivial module to
prove the JVM, the solver and the Viper backends actually cooperate.

One tuning note that generalizes to any SMT-backed verifier: the wrapper caps the
verifier's *internal* parallelism (`SBN_PARALLEL_VERIFIERS`, default 1). Left
alone, such a tool sizes its solver pool to the host's core count, so one
verification fans out across the whole machine and fights whatever outer
per-instance parallelism the caller has chosen. The cap is not only about speed:
on a module that must be *refuted*, a fanned-out solver may not converge at all
and the refutation is recorded as "no verdict", which the gates charge to the
specification. Set the outer job count for throughput and leave the inner cap low.

## 5. Construct

One cell, which is also how to confirm the setup before spending anything:

```bash
swebench-unified construct --backend <b> --instance <id>
```

What a run would cost, launching nothing:

```bash
swebench-unified construct --backend <b> --all --dry-run
```

A sample, or an explicit worklist:

```bash
swebench-unified construct --backend <b> --all --limit 5 --jobs 4
swebench-unified construct --backend <b> --all --only <id> [<id> ...]
swebench-unified construct --backend <b> --all --instances FILE   # one id per line
```

Every instance in the benchmark:

```bash
swebench-unified construct --backend <b> --all --jobs 12
```

Start with `--dry-run`, then the bounded forms. `--all` with no worklist flag
means every instance in the frozen dataset -- 500 of them for SWE-bench Verified
-- and each one is a construction subprocess that runs agents against your model
credentials for as long as its wall clock allows, so the cost scales with the
worklist and not with `--jobs`, which only decides how much of it runs at once.
The dry run prints the resolved worklist, the corpus root it would write to, how
many cells are already green (skipped without `--force`), and every precondition
that would otherwise fail one child at a time: the frozen dataset, a provider for
the agent CLI, and a mirror for each task repo. It exits 1 if any of those would
block. `scripts/green_check.py` (section 7) answers the same greenness question
across a whole corpus.

Useful flags, and why they exist:

| flag | effect |
|---|---|
| `--max-rounds N` | refine-round budget for the construction agent (default 8) |
| `--pbt` | run the optional phase that authors the adversarial spec-strength battery against the frozen, verifying solution, before the recorded gate sweep judges it |
| `--audit` | run the adversarial audit stage (three agents, verdicts re-derived mechanically) |
| `--skip-docker` | static gates only; use when no daemon is available |
| `--force` | re-build a cell that is already green |
| `--model` | model id for the agentic phases |
| `--repo PATH` | use this clone instead of the mirror directory |
| `--limit N` (`--all`) | build only the first N of the shuffled worklist |
| `--seed N` (`--all`) | the shuffle seed |
| `--wall-seconds N` (`--all`) | per-instance wall clock |
| `--only ID...`, `--instances FILE` (`--all`) | an explicit worklist instead of the whole benchmark |
| `--dry-run` (`--all`) | report the worklist and every precondition, launch nothing (exit 1 if a real run would be blocked) |

The rows marked `(--all)` are the driver's own flags; the rest belong to the
single-cell builder, and the driver passes anything it does not recognize through
to each child build, so `--all --pbt --audit` reaches every cell of the worklist.
That is why `construct --all --help` lists fewer flags than this table.

The `--all` driver shuffles the worklist under a fixed seed, so `--limit N` yields
a uniform random sample of the benchmark rather than an alphabetical prefix, and a
partial run is reportable. It runs one subprocess per instance so a fatal error
in one cell cannot poison its siblings, enforces the wall clock with SIGTERM then
SIGKILL (the builder's signal handler removes its worktree), and writes a job log
plus per-instance stdout under `experiments/construct/<backend>/`.

Construction is resumable and idempotent in both directions: an already-green cell
is skipped unless forced, and a cell that ended in a *principled block* (the agent
established that the instance cannot be specified inside the backend's fragment
and wrote `BLOCKED.md`) is terminal and its explanation is never overwritten.
"Already green" is read from the cell's recorded gate verdicts, by the same
predicate the release gate and the review site use, so resume works on a corpus
you cloned rather than built: pointing `--all` at the shipped bundles builds
nothing instead of re-spending an agent run per cell.

`--benchmark-dir NAME` (a global flag, before the subcommand) sets the bundle
root, so several benchmarks or several experiments can be constructed side by
side in one checkout. The value propagates to the `--all` driver's child processes
through the environment, so it survives the respawns.

## 6. Re-judge existing bundles

The gate suite is a separate entry point precisely because it must be runnable by
someone who did not build the bundles:

```bash
swebench-unified gates --backend <b> <id>...              # all mechanical gates
swebench-unified gates --backend <b> <id>... --static-only
swebench-unified gates --backend <b> <id>... --docker-only
swebench-unified gates --backend <b> <id>... --gates G-MUT G-PBT
swebench-unified gates --backend <b> <id>... --no-record  # judge, do not write
```

Verdicts are recorded into each bundle's `meta.json`, stamped with the mode, a
timestamp, the code version, and a digest of the gate harness itself. `--no-record`
exists so that an independent re-judgement can be performed without mutating a
released artifact.

`--mode feedback` reproduces the leniency construction uses mid-loop. It is
recorded in the result, so a feedback verdict can never be mistaken for a strict
one.

## 7. Decide what is done

```bash
python scripts/green_check.py --benchmark-dir <root> --backend <b> [--only-ok]
```

Prints one line per instance: `GREEN`, `NOTGREEN`, or `NORESULT`. It reads only
`meta.json`, never a log line, a driver summary, or an agent's self-report.
Section 8 of [architecture.md](architecture.md) states the exact criterion,
including why certain skips ("no battery authored yet", "no conformance probe
yet", "this benchmark's oracle is not wired up") do not count as green even
though they are recorded as skips rather than failures.

### The release criterion

`green_check.py` answers the question for one cell. Whether a whole corpus is
*releasable* is a conjunction of several such questions, and `release_gate.py` is
that conjunction, executable:

```bash
python scripts/release_gate.py --benchmark-dir <root>   # every check; exit 0 = releasable
python scripts/release_gate.py --list                  # the checks and what each defends
python scripts/release_gate.py --only green            # run one check
python scripts/release_gate.py --skip freshness --json report.json
```

A green run -- exit 0, every selected check passed -- is the criterion this corpus
is released against. Each check wraps a tool under `scripts/` that can also be run
on its own:

| check | tool | what it defends |
|---|---|---|
| `green` | `green_check.py` (once per backend) | every cell's gates recorded and OK: the release claim itself |
| `freshness` | `check_stamp_freshness.py --certify-unchanged --strict` | every stamp describes the bytes on disk, so no cell is green on a verdict about a superseded spec |
| `audit-freshness` | `audit_freshness.py` | every audit verdict still describes the spec on disk, compared by spec signature -- the half of freshness a digest cannot decide, since a spec that *gained* an obligation keeps its audit while one that lost a conjunct does not |
| `batteries` | `battery_integrity.py` | every `properties.py` still imports; a battery that does not caps its cell red however strong the spec is |
| `stale-fails` | `stale_fail_triage.py` | no recorded failure describes a spec the bundle no longer ships, which would route a repair at a defect that is already gone |
| `audit-complete` | `pbt_audit_completeness.py` | every cell carries a complete audit under the *current* audit prompt, not a partial or superseded one |
| `certify` | `pbt_certify.py` | each cell's recorded G-PBT verdict was reached by a harness at least as strict as the current one, has a reject lane at all, and had every reject witness actually checked -- a corpus of green records is otherwise only as good as the oldest harness any of them was judged by |
| `prose` | `verdict_prose_lint.py` | no released record publishes build-time narration: scratch paths that no longer exist, one machine's absolute paths, its load |

Two of the checks need a fetched input, and say so rather than degrading. The
frozen dataset (`swebench-unified fetch-dataset`) is the only proof `freshness` has
for `instance.json` and `patch.diff`, the two files nobody authors: without it that
check exits 2 naming the missing dataset, and the gate prints the same warning
before it starts. `freshness` also reports which proof carried each digest-less
record -- `certified by: content=..., git=..., mtime=...`. Only the first two travel
with the repository: `git clone` resets every mtime, so the `mtime` count is exactly
the set of records a consumer will see as `uncertified`, and closing it means
re-running those gates so the records carry digests.

Three things it deliberately does not distinguish in the exit status: a check that
reports a defect, a check that could not measure a cell (the bundle was locked by a
running driver, or its record is unreadable), and a check that crashed or timed
out. The question is not "is anything known to be broken" but "is every cell known
to be sound", and an unmeasured cell is not known to be sound -- so run it on a
quiescent tree, and read a report full of busy cells as a scheduling answer rather
than a verdict about the corpus. For the same reason a check that reports having
walked *zero* cells fails however it exited.

Nothing in it is specific to this benchmark: `--benchmark-dir` and `--backends`
select the corpus, `--backends` defaults to every backend that has bundles under
that root (a backend with no verifier is included -- `green_check.py` judges each
bundle on the gates that apply to it, so what a no-verifier backend needs is its
other gates recorded and OK, and leaving it out would exit 0 having never asked
the release question of it), and adding a check means adding one entry to `CHECKS`
with its argv and how to read its output.

## 8. Close the residue at scale

`construct` and `gates` handle one cell or one uniform sweep. Bringing a whole
corpus to green is a different shape of work: the residue is a few dozen cells at
a time, each red for its own reason, and the reasons need different treatments.
The batch drivers under `scripts/` are those treatments. Each one takes a worklist,
runs its agents in parallel, and then decides the outcome mechanically rather than
from the agent's self-report, so a driver's own summary can be trusted no more than
a cell's `meta.json`.

| driver | what it closes |
|---|---|
| `regate_resume.py` | construct-or-re-judge a whole cell -- one cell, a lane, or every cell of a benchmark -- until strictly green, resumably |
| `restamp_gate.py` | re-measure a NAMED subset of gates on cells that are already built, when only that measurement is stale: `--gates G-CONF,G-AX` with either a `--cells` TSV or a repeatable `--cell <instance_id> <backend>` |
| `audit_refresh.py` | re-run the P2 audit stage over a `--lane-file`, for cells whose spec has moved since the audit that judged it |
| `pbt_port_fleet.py` | author the G-PBT spec-strength battery for a batch of cells |
| `pbt_audit_fleet.py` | audit those batteries with agents that did not write them |
| `spec_repair_fleet.py` | repair a spec an audit proved too weak, unfaithful, or leaking, then re-audit it with fresh attacks (worklist as `--lane-file`, one `<instance_id><tab><backend>` per line) |

Three properties are what make one of these safe to leave running unattended, and
a driver of your own needs all three.

**Cells are claimed with a flock** on a sidecar file per bundle
(`pbt_port_fleet.cell_lock`, which the other five import), so two drivers pointed
at overlapping worklists cannot both author the same artifact. The claim is
non-blocking and records the holder's pid, so a busy cell is skipped with the name
of who held it. Pointing a second driver at the same worklist is therefore a safe
way to add throughput, and killing one releases its cells at once.

**Resume is against what is recorded**, never against a driver's own log, so one
that dies loses only the cell it held. `regate_resume.py` needs no flag: it
re-classifies every cell and skips the ones already green or parked with a
`BLOCKED.md`; the authoring and repair fleets take `--resume`, which skips cells
whose recorded verdict already says the work is done. The two re-measurement tools
cannot skip a recorded cell, since re-measuring exactly those is what they were
asked for, so they resume on what a pass could not measure and both name the cells
they failed to claim (`restamp_gate.py --unmeasured-out` writes them as a lane
file a relaunch takes directly), because a lane that silently skips half its cells
and exits 0 reads as a lane that cleared them.

**Green is decided by calling `green_check.classify`**, the authority section 7
uses (`regate_resume.py`, `spec_repair_fleet.py` and `audit_refresh.py` all do,
the last before and after, so its report says what the fresh measurement did to
each cell's standing), and a narrower question -- is this one gate's recorded
verdict a real one -- by importing the same predicate rather than restating it
(`swebench_unified.greenness.conf_is_real_verdict`). Re-deriving greenness locally
is how a driver's count of what it fixed starts disagreeing with the release gate
about the very cells it was repairing.

`--dry-run` prints the worklist a driver would take and launches nothing
(`regate_resume.py`, `pbt_port_fleet.py`, `pbt_audit_fleet.py`,
`spec_repair_fleet.py`). `regate_resume.py --force` is the opposite question, the
bytes rather than the record: it re-measures a cell that already classifies GREEN,
every mechanical gate plus a fresh audit stage, and refuses to run without
`--instances` or `--instances-file`, because a corpus-wide forced audit is hours of
agent time per cell that nothing said was wrong.

Reporting tools read only what is already recorded, so they are safe to run while
drivers are in flight: `pbt_coverage.py` (what a battery actually defends),
`pbt_signature_tiers.py` (the evidence behind each passing reject case),
`pbt_static_audit.py` (corpus-wide structural forgeries, no builds), and
`pbt_certify.py` (whether every recorded G-PBT verdict would still be reached by
the current judge, which a green status cannot answer).

Three single-cell tools sit under the fleets rather than beside them.
`python scripts/pbt_gate.py <id> --backend <b>` (`nagini`, `velvet` or `lean`;
`ears` has no battery) runs G-PBT on one bundle and records the stamped verdict,
which is what a port task's success is measured by (a `pbt_missing_manifest` skip
exits 1, matching `green_check`). It takes no `--benchmark-dir`, so the bundle
root is `SBU_BENCHMARK_DIR`; `--validate-only` is the mechanical scope check with
no verifier and no record. `self_audit.py` hands a repair agent the judge it
will face: the real `eq` audit role, same prompt and same attack floor, recording
nothing -- because a repair that kills the attack it was shown can still be refuted
by a fresh attack the same hole admits. `audit_recheck.py` repairs the *record*
rather than the artifact and runs no agent: it re-derives a recorded audit verdict
from the attacks already retained in `verdict.md`, which clears a role that reached
no verdict without re-running the reviewer. It reports before it repairs; writing
needs `--write`.

## 9. Evaluate a model against the benchmark

```bash
swebench-unified eval --backend <b> --mode <m> --model <k> [--all | --instances ID...]
swebench-unified score --backend <b> ...
```

There are 9 modes (`--mode` accepts 0, 1, 2, 3, 4, 10, 11, 100, 101). Most of them
exist to disentangle two confounded advantages a verification-aware setup gives a
solver, the *verification signal* and the *edit localization*, so that neither is
credited for the other:

| mode | inputs | pass criterion |
|---|---|---|
| 10 | issue + repository only, bash only | resolve (the canonical baseline) |
| 0 | + edit localization | resolve |
| 2 | + spec view + verifier (optional aid) | resolve |
| 1 | + spec view + verifier | verify and resolve and judged equivalent |
| 3 | issue + repository, prompted to build a spec and model | resolve |
| 4 | as 3, formal work scored | verify and resolve and judged equivalent |
| 11 | issue + repository; construct spec plus verifying witness, no patch graded | witness verifies, the contract is not fake, and the adversarial spec audit passes |
| 100 | mode 0's inputs plus the verifier; spec constructed from scratch as in 4 | verify and resolve and judged equivalent |
| 101 | identical to mode 10 -- issue + repository, bash only, no spec, no verifier | resolve **and** the adversarial counterexample audit finds no real ground-truth violation |

The differences are the measurements: (2 minus 0) isolates spec plus verifier
given localization, (0 minus 3) isolates localization, (3 minus 10) isolates the
verification method under identical inputs, and (1 minus 4) separates a given
spec from a constructed one.

Mode 101 is the one addition that is not an ablation of the information given to
the solver. What the agent sees is byte-identical to mode 10 (the same prompt file
is loaded), so the only difference is in the grading: a submission that resolves is
then attacked, and the pass is withdrawn if the audit confirms a behavior where the
accepted patch diverges from the formal ground truth. (101 minus 10) is therefore
the share of leaderboard-passing patches that a counterexample search can still
break. Because the audit grounds in the Lean formal specification rather than in
the backend under test, mode-101 numbers are comparable across backend labels.

Three properties of the harness matter for reproducibility:

* **The task view is a projection that drops withheld fields.** The gold patch,
  the test patch, and the hidden test lists are not merely unused, they are never
  placed in the evaluated process's memory, and an explicit assertion re-checks
  the assembled view for leaks before an agent sees it. Auxiliary hint text is
  excluded by default. The container's own git history is the other half of that
  surface: `scripts/eval/sanitize_repo.sh` runs inside it before the agent starts
  and prunes every object that is not an ancestor of `base_commit`, because refs,
  reflog, packed-refs and tags expose the solution commit even with HEAD detached
  at the base (SWE-bench issue #465). It prints a `SANITIZE-OK` line that
  `eval/container.py` requires, so a container whose `.git` was never touched
  cannot pass for a sanitized one.
* **Every trajectory is persisted and audited.** Per run you get the config, and
  per instance the status, the full trajectory, the exact task view the agent saw,
  the submission, the grade, and an anti-cheat audit of the trajectory. A pass
  whose trajectory shows the agent reading something it should not have is not a
  pass, and that can only be established after the fact from a saved record.
* **Judged criteria use multiple votes.** The equivalence judge is polled several
  times and the majority decides, because a single sample from a model is not a
  reproducible measurement.
* **The localization the modes hand out is a build artifact, not a hand-written
  file.** It comes from `scripts/build_eval_localization.py` (section 3), and modes
  0 and 100 refuse to run without it, so "the localization ablation" cannot silently
  degrade into a second copy of the baseline.

A backend with no verifier redefines that table rather than inheriting it, since
neither the verify criterion nor the equivalence judge is available to it. Every
mode is scored on resolution, and modes 100, 2 and 4 are the audited twins of 0, 1
and 3: a twin passes only if an adversarial counterexample audit finds no real
ground-truth violation, and is agent-side byte-identical to the mode it audits, so
the pair isolates the audit. Mode 11 grades nothing but a verifying witness and is
therefore rejected for such a backend before any work starts, rather than
producing a number that cannot mean anything.

`score` is the mechanical consumer scorer over (solution, patch) predictions: it
reports the conditional probability of resolving given verified, where "verified"
requires that the candidate shares the frozen spec, that conformance is re-run
rather than assumed, and that the axiom verdict is carried over from the bundle.

## 10. Configuration surface

The pipeline is configured by flags where a choice belongs to one invocation and
by environment variables where it belongs to a host or a checkout. The ones worth
knowing:

| variable | purpose |
|---|---|
| `SBU_BENCHMARK` | which benchmark is active (dataset, images, oracle style) |
| `SBU_BENCHMARK_SPEC` | JSON file(s) declaring a benchmark from outside the checkout, so a port needs no source edit ([adapting a benchmark](adapting_a_benchmark.md) §3a) |
| `SBU_BENCHMARK_DIR` | bundle root; also settable with the global `--benchmark-dir` |
| `SBU_REPOS_ROOT` | where the task-repository mirrors live |
| `SBU_PROMPTS_DIR` | an override directory searched before the shipped prompts |
| `SBU_RUN_PREFIX` | per-checkout isolation for container run ids and temporary worktrees |
| `SBU_PYTHON` | interpreter to use for self-respawns |
| `SBU_MODEL` | default model for agentic phases |
| `SBU_BEDROCK_REGION` | region for the hosted-model providers, overriding each preset's own default (below) |
| `SBU_RESOLVE_SLOTS` | host-wide cap on concurrent oracle containers |
| `SBU_RESOLVE_CPUS` | cores one oracle container may use; `0` turns the cap off |
| `SBU_DOCKER_CMD` | the command that reaches the docker daemon, for the deployments a probe cannot discover (below) |
| `SBU_DOCKER_WRAPPER`, `SBU_DOCKER_GROUP` | older, narrower spellings of the same choice: a wrapper argv, and the group name for the `sg` form |
| `SBU_DOCKER_PROBE_TIMEOUT` | seconds one daemon probe may take (default 60) |
| `SBU_VENDOR_WHEELS` | directory holding the vendored wheels mounted into containers, for a deployment that installed the package rather than the source tree |
| `SBU_PIP_NETWORK` | `1` lets a container fetch the pinned fuzzer from an index when no vendored wheel was found |
| `SBU_EXPERIMENTS_DIR` | where run output goes (construction logs, eval artifacts, harness reports); default `experiments/` inside the checkout, which a read-only or network-mounted clone cannot host |
| `SBU_LEAN_SHARED` | a copy of `lean_shared/` to build against instead, used only while its dependency pins fingerprint-match the original |
| `SBU_LEAN_SLOTS` | host-wide cap on concurrent Lean builds; unset means no cap |
| `SBU_LEAN_REPIN` | `1` makes `install.sh` re-resolve the Lean dependencies instead of building at the pinned revisions, which moves the pins (section 4) |
| per-gate timeouts, worker counts and slot caps | one variable each; the ones you are likely to need are in the second table below |

Docker access is the first thing to check on a new host, because getting it wrong
makes every oracle measurement fail identically -- but on most hosts there is
nothing to set, because the pipeline *probes* how it reaches the daemon rather than
assuming. The order is: `SBU_DOCKER_CMD` if set (and it is never probed, because an
operator naming a command means that command), then `SBU_DOCKER_WRAPPER`, then
`SBU_DOCKER_GROUP` -- naming a group is itself a request for the `sg` form -- then a
probe of plain `docker`, then a probe of `sg docker -c`, and only then an error that
names `SBU_DOCKER_CMD`. Each probe asks the *daemon* for its version, since a
client with no reachable daemon still answers for itself. Plain `docker` covers
Docker Desktop, a rootless daemon, root, CI, and any account already in the
daemon's group. The `sg` step covers the case only a probe can find: an account
holding that group as a *supplementary* one, which a process launched from a
non-interactive parent (cron, a detached driver, a service manager) carries in its
list without it being active, so `docker` returns a permission error while `sg`
starts a subshell where it is active.

Set `SBU_DOCKER_CMD` when the client is not `docker`, or needs an escalation no
probe should guess: `SBU_DOCKER_CMD=podman`, `SBU_DOCKER_CMD='sudo -n docker'`. A
value ending in `-c` is taken as a wrapper that receives the whole command as one
string (`SBU_DOCKER_CMD='sg <group> -c'`, `SBU_DOCKER_CMD='sudo -n sh -c'`);
anything else is the client argv itself. Both shapes exist because not everything
that must reach the daemon is a `docker` call -- the correctness oracle runs a Python
process that talks to it. Only a successful resolution is cached, so a daemon that
was down at startup does not stay "unavailable" for the life of a long-running
driver, and each probe is bounded by `SBU_DOCKER_PROBE_TIMEOUT`.

`SBU_VENDOR_WHEELS` and `SBU_PIP_NETWORK` matter for one gate, G-CONF. The
task-repo images do not ship the fuzzer the conformance shadow is compared with, so
it is mounted in from `vendor/wheels/` and installed offline at a pin -- an unpinned
install would make the input distribution whatever an index served that day, and a
G-CONF verdict would stop being reproducible from the artifact. The release ships
no third-party code, so `vendor/wheels/` starts empty: `bash scripts/fetch_vendor.sh
wheels` downloads the pinned wheels into it and checks each against its sha256.
It is not part of the installed package either, so point `SBU_VENDOR_WHEELS` at a
copy of it if you installed the package rather than the tree, or set `SBU_PIP_NETWORK=1` to let images that can reach an index fetch the
same pin themselves. A configured directory that does not exist is treated as no
wheels at all rather than falling back to a discovered one. Neither failure is
fatal: most conformance scripts fall back to their own built-in fuzzer, so what is
lost is input coverage, and every branch says on stderr which one it took -- read
that line before trusting a G-CONF pass you did not provision for.

`SBU_BEDROCK_REGION` deserves the same early attention, for the same reason in a
different place:
which region hosts a given model is a property of the *account*, not of this
pipeline, so each model preset carries a region default rather than sharing a
constant, and the shipped defaults are the ones each model was reachable in from
the account this was written for. Another account may have the same model
elsewhere, or may not be entitled to that region at all -- and the failure is
misleading, because the access error names the *model*, so a region mismatch reads
as "we do not have this model" and sends you to the wrong console page.
`SBU_BEDROCK_REGION` overrides every preset at once; `AWS_REGION` and
`AWS_DEFAULT_REGION` are honored next, because they are what the rest of an AWS
toolchain already reads and these providers pass the region explicitly, which would
otherwise silently beat a setting the caller has already made. A variable exported
empty counts as unset.

Two more deserve a note. `SBU_RUN_PREFIX` exists because container run ids
and temporary worktree names would otherwise be keyed only by instance id, so two
checkouts building the same instance would collide and delete each other's
in-flight state. And `SBU_RESOLVE_SLOTS` bounds the *oracle*, the one shared
rate-limited resource in the pipeline: each correctness measurement is a container
building and running a repository's test suite, and oversubscribing it does not
merely slow things down, it makes runs fail to produce a report at all. Since a
measurement that did not complete is reported as incomplete rather than as "did
not resolve", host oversubscription would otherwise be indistinguishable from a
defect in the artifact under test. The cap is a cross-process semaphore, held only
around the container run, so queueing never counts against an attempt's own
timeout and a killed holder cannot leak a slot. Choose the value from a
measurement on your own host, using reference patches, which resolve by
definition, so that any failure is infrastructure.

### The caps that decide whether a verdict is a measurement

Every variable below bounds how much of a machine one piece of work may take. They
are worth setting deliberately, because in this pipeline a cap that the *host*
rather than the artifact runs into does not just cost time: a check that never
reached a verdict is recorded, and for the gates that conclude from a *rejection*
(mutation, the falsification battery, an audit attack) a missing verdict is
charged to the specification. Under-provisioning therefore manufactures spec
defects, and the failure looks exactly like a real one.

| variable | default | raise it / lower it when |
|---|---|---|
| `SBU_RESOLVE_SLOTS` | 12 | host-wide oracle containers. `0` disables the semaphore (single-cell debugging). Above the host's measured ceiling, runs stop producing a report at all |
| `SBU_RESOLVE_CPUS` | a quarter of the host's cores, floored at 8 | cores one oracle container may use, so that one evaluation cannot starve the concurrent verifiers; `0` turns the cap off, and a value at or above the core count is not a limit at all |
| `SBU_RESOLVE_TIMEOUT` | 3600 | wall clock for one G-RESOLVE oracle run |
| `SBN_PARALLEL_VERIFIERS` | 1 | the imperative verifier's *internal* solver pool. `0` leaves the tool's own default (the core count), which self-fans-out and, on a module that must be refuted, may not converge at all -- the refutation is then lost as "no verdict" |
| `SBN_VERIFY_TIMEOUT` | 300 | wall clock for one verifier invocation; exit 124 is the timeout, never a verification failure |
| `SBU_MUTATION_WORKERS` | 2 | mutants verified in parallel within one cell, i.e. verifier processes one G-MUT run puts on the host. Size it by verifiers that do not slow each other down, not by core count |
| `SBU_MUTATION_CAP` | 20 | how many mutants are generated per bundle |
| `SBU_MUTATION_TIMEOUT` | 0 (use the cell's own `timeout_seconds`) | a mutant can be much harder to decide than the solution it mutates; the value wins only when it asks for **more** than the cell recorded, so it cannot silently lower a declared cap |
| `SBU_PBT_WORKERS` | 8 | battery cases verified in parallel within one cell. Each case is a full verification, so this is the same trade-off as `SBU_MUTATION_WORKERS` and 8 is high for a host that is also running other cells |
| `SBU_PBT_VERIFY_TIMEOUT` | 300 | per-case verifier cap for G-PBT; also `max`ed with the cell's own `timeout_seconds` |
| `SBU_ATTACK_VERIFY_TIMEOUT` | 300 | per-attack cap inside an audit role. Too low and `verify_completed` is false, which the audit derivation must treat as inconclusive, so a wide fan-out turns a sound cell's audit into a fail |
| `SBU_AGENT_SLOTS` | 64 | host-wide cap on concurrent agent CLI launches. It is a backstop against a runaway, deliberately above normal operation, and it **fails open**: a launch that cannot get a slot proceeds unslotted, so the value bounds the wait, not the concurrency |
| `SBU_AGENT_CONTAINER_MEM` / `SBU_AGENT_CONTAINER_CPUS` | `8g` / `4` | what one evaluated agent's container may take, in docker's own units. These belong to the deployment, not to an instance |

The integer caps above (`SBU_RESOLVE_SLOTS`, `SBU_RESOLVE_TIMEOUT`, the
`SBU_MUTATION_*` and `SBU_PBT_*` variables, `SBU_ATTACK_VERIFY_TIMEOUT`) are parsed
with a digits-only test, so a value that is not a plain non-negative integer --
`12.5`, `-1`, a stray space -- is ignored and the default silently stands. Confirm
a setting took effect rather than assuming it did.

### The rest of the surface

| variable | default | purpose |
|---|---|---|
| `SBU_DATA_ROOT` | `data/` in the checkout | where the frozen datasets live; a relative value is taken under the project root, so a fetch can be tried out without writing into the tree |
| `SBU_SCRATCH` | `experiments/scratch` | where a source string is materialized to be checked. It must stay inside the tree, because relative dependencies such as `lean_shared` have to resolve from it |
| `SBU_AUDIT_TIMEOUT` | 10800 | wall clock for one audit role. A role that overruns yields an empty payload, which is inconclusive and therefore a gate fail, so a cap below what a working role needs inverts the meaning of the result |
| `SBU_AUDIT_JOBS` | one per role | audit roles run concurrently within a cell |
| `SBU_AUDIT_RETRIES` / `SBU_AUDIT_RETRY_WAIT` | 2 / 120 | re-runs of a role that reached no verdict, and the linear backoff between them; `0` retries immediately |
| `SBU_AUDIT_ONLY` | unset | comma-separated audit roles to run; an unknown name is an error, not a silent skip |
| `SBU_ATTACK_VERIFY_RETRY` | 3.0 | factor a timed-out attack verification is retried at, capped at 1800s; a value at or below 1 disables the retry |
| `SBU_ADVERSARY_TIMEOUT` | 1800 | wall clock for the eval-side counterexample audit agent (mode 101, and the audited twins a no-verifier backend uses) |
| `SBU_CONTAINER_TIMEOUT` | 1800 | wall clock for one G-AX or G-CONF container run |
| `SBU_PROOF_GEN_TIMEOUT` | 300 | **total** budget for the proof phase, shared across attempts, not a per-attempt cap |
| `SBU_MAX_PROOF_ATTEMPTS` | 1 | proof attempts per bundle |
| `SBU_AXIOM_REFINEMENT` / `SBU_MAX_AXIOM_ITERATIONS` | off / 10 | whether a stuck proof drives the axiom-propose loop, and how many iterations it may take |
| `SBU_AGENT_TRACE` | unset | directory for one line per tool use while an agent works |
| `SBU_LAUNCH_RETRIES` / `SBU_LAUNCH_BACKOFF` | 2 / 10 | retries, and seconds between them, for an agent process that fails to start |

None of these tables is the whole set. The remainder is markers the pipeline sets
for its own subprocesses, which are not configuration, plus per-tool knobs -- slot,
lock and log directories, auth and readiness waits, janitor intervals -- which
each tool's `--help` or module docstring names. The review site has its own `VIZ_*` set, documented in
[viz/README.md](../viz/README.md). The full list of what the pipeline reads is
greppable:

```bash
grep -rhoIE '\b(SBU|SBN|SWEBENCH)_[A-Z0-9_]+' src scripts | sort -u
```

## 11. Tests

```bash
python -m pytest tests/              # the pipeline
python -m pytest viz/tests/          # the review site (needs the `viz` extra)
```

The unit suite needs no Docker, no verifier, and no model credentials; the two
tests that would fetch a dataset skip unless `SBU_SMOKE_NETWORK=1`. It covers
the gate framework, the marker and spec-view machinery, the variant-admissibility
and witness checks, the audit-verdict derivation (including that a self-reported
pass cannot survive a contradicting artifact), the prompt registry, the benchmark
registry, the oracle's retry policy, and repository hygiene. Running it is the
cheapest way to confirm a port of the pipeline to a new benchmark or backend has
not broken an invariant.

The review site's suite is a **separate test root** and is not collected by
`pytest tests/`; run it explicitly, as above. It is offline too, apart from one
test that reaches a model and is skipped unless `VIZ_LIVE_AGENT=1`.
