# Adapting the pipeline to another benchmark

The pipeline is a general construction loop for turning an
issue-plus-repository-plus-hidden-tests benchmark into a formally verified twin.
Nothing about the loop, the gate suite, or the evaluation harness is specific to
any one dataset. This document is the concrete list of seams a new benchmark plugs
into, and what each one owes the rest of the system.

Four benchmarks are registered: the two the release ships corpora for (SWE-bench
Verified and the SWE-bench Pro Python subset) and two more registered with no
corpus, so that the generality claim is something the test suite measures rather
than something this document asserts. The SWE-bench-Live `verified` split is the
worked example of everything below: its entry, its row adapter and
`tests/test_third_benchmark_smoke.py` walk the whole path from a bare dataset id to
gate records. The SWE-Gym `lite` split is the same seam entered from a different
angle, and is what says how little a port can be: rows that carry a real `version`
and nothing worth preserving outside the frozen schema, a third `hf_split` value,
and an adapter whose whole body is two normalizations: list-valued test fields
re-emitted as the JSON strings every reader parses, and an
`environment_setup_commit` synthesized from `base_commit` because that curator
publishes no such column.

Read [architecture.md](architecture.md) first for what the gates are judging. To
add a new specification *language* rather than a new dataset, see
[adding_a_backend.md](adding_a_backend.md).

## 0. What the pipeline assumes about a benchmark

Exactly this, and nothing more:

1. **Rows.** A finite set of instances, each identified by a stable id, each
   naming a repository and a commit at which the issue reproduces.
2. **An issue.** A natural-language problem statement that is what a solver is
   given.
3. **A reference patch.** A diff that fixes the issue. Used as the construction
   agent's ground truth and as the subject of the anchoring correctness check.
4. **A correctness oracle.** Some mechanical procedure that decides whether a
   candidate patch resolves the instance, typically a hidden test set plus a
   runner.
5. **A reproducible execution environment**, usually a per-instance container
   image, in which that oracle can be run.

If your benchmark has all five, the port is a registry entry, plus a row adapter if
its upstream rows are not already the frozen schema, plus an oracle adapter if its
grading is not one the pipeline already drives. If it lacks the
oracle or the environment, you can still construct and run every static gate; the
three Docker gates will record explicit skips and the corpus will be honestly
labelled as unanchored rather than silently weaker.

## 1. The frozen row schema

Every downstream reader assumes a JSONL file, one row per line, carrying at
least:

| field | meaning |
|---|---|
| `instance_id` | stable unique id; also the bundle directory name |
| `repo` | `owner/name` of the task repository |
| `base_commit` | commit the issue reproduces at |
| `patch` | the reference fix |
| `test_patch` | the test changes that accompany the fix |
| `problem_statement` | the solver-visible issue text |
| `FAIL_TO_PASS` | tests that must go from failing to passing |
| `PASS_TO_PASS` | tests that must keep passing |
| `environment_setup_commit` | commit whose dependency state the images were built at |

Construction and all eight static gates need only these. The Docker gates
additionally need per-instance images and a compatible oracle.

The table is machine-checked, per row, before anything is written:
`scripts/fetch_dataset.py:row_complaints` is its one definition, and
`tests/test_benchmarks.py` is the control that the registry's own column contract
still agrees with it. What it checks past presence is what a reader cannot recover
from: everything above except `test_patch` is a non-empty string, `FAIL_TO_PASS`
and `PASS_TO_PASS` are JSON *strings* holding arrays of test ids, and
`FAIL_TO_PASS` is non-empty because an oracle with no required test grades
nothing. Every other column -- `hints_text`, `version`, `created_at`, a
benchmark's own sub-object -- is optional, so a curator who publishes none of them
still fetches; `created_at` is the one optional column with a checked shape
(`YYYY-MM-DDThh:mm:ssZ`, whenever it is published at all), because a frozen column
must mean one thing across benchmarks.

`environment_setup_commit` is in the list because `setup_repos.py` reads it
without a default when it decides which commits to have on disk, so a row
without it is a `KeyError` rather than a degraded clone. Upstream datasets do not
all carry it; when there is no separate field, set it to `base_commit`, which is
what all three shipped row adapters do.

Two conventions are worth preserving rather than reinventing. Keep any
benchmark-specific extra fields under a single nested sub-object (the shipped
examples use `pro` and `live`) so a new benchmark's fields never collide with the
schema or with another benchmark's. And normalize list-valued fields into JSON
strings that every reader can parse uniformly, even if the upstream dataset stores
them in some other serialization; one normalization in the adapter is much cheaper
than a per-reader special case forever.

## 2. Seam one: the row adapter (often nothing)

There is **one** fetch script for every benchmark, `scripts/fetch_dataset.py`. It
takes the source (`hf_dataset`, `hf_split`, and `hf_config` / `hf_data_files` for
a dataset that is not one loadable split), the destination (`data_subdir`) and
the column contract (`upstream_columns`, `frozen_columns`) from the registry entry
of section 3, so a benchmark whose upstream rows already *are* the frozen schema
needs no edit here at all -- that is what
`tests/test_fetch_dataset.py::test_an_unmapped_benchmark_needs_no_edit_here` pins.

```bash
swebench-unified fetch-dataset                          # the active benchmark
python scripts/fetch_dataset.py --benchmark <name>      # or name it
SBU_DATA_ROOT=$(mktemp -d) python scripts/fetch_dataset.py \
    --benchmark <name> --limit 4                        # a smoke slice
```

`--limit` is refused unless `SBU_DATA_ROOT` points the write away from the corpus
data root, because a 4-row `test.jsonl` there would make the integrity gate report
every other instance as absent from the frozen dataset.

When the upstream rows are *not* the frozen schema, add one `_ADAPTERS` entry
keyed by benchmark name: a row filter (or `None`) and a row normalizer that returns
exactly the frozen keys. All three shipped mappings are worked examples -- Pro
filters to the Python rows and re-emits its Python-repr test lists as JSON strings;
Live re-emits real lists and a `datetime` in the one spelling that column carries
across benchmarks; Gym re-emits the lists and nothing else, which is the floor.
Declare the emitted key order in `frozen_columns`. A benchmark declared outside
this repository instead names its own pair as `row_filter` / `row_map` in its
entry (section 3a) and needs no line in that table.

Three properties of the write are load-bearing, and you inherit all three:

* **Deterministic.** Rows sorted by instance id, one compact JSON object per line,
  the declared key order. The integrity gate compares each bundle's frozen
  `instance.json` against this file, so a nondeterministic write would make every
  bundle in the corpus read as tampered with.
* **Checksummed.** A sha256 of the result is printed. That is how a third party
  confirms they hold the same dataset without diffing every row.
* **Fetched, never copied.** `data/` is reconstructible from pinned identifiers
  and is not committed. Copying a frozen file from a sibling checkout destroys
  the only provenance the corpus has.

Two contracts are checked before anything is written. The upstream COLUMN set
(`upstream_columns`) is checked exactly, order included, for an unmapped benchmark
(its upstream order *is* the frozen key order), and for presence only where an
adapter maps the rows, so an upstream schema drift aborts the fetch instead of
silently rewriting every line. The frozen ROW schema of section 1 is then checked
on exactly the rows about to be written, after any `--limit` slice: a violation
names the instance id and the field, says whether to fix the row mapping or the
registry entry, and exits non-zero with nothing written. Offending rows are
refused, never skipped, because the frozen file *is* the corpus's row set --
dropping them would shrink it silently, move the printed sha256, and make a slice
depend on which rows happened to be malformed. Every complaint is printed at once
(capped, with the remainder counted) so one run is enough to fix an adapter. Two
things a fetch used to freeze with a sha256 and an exit 0, and which now name
themselves: a `row_map` leaving `FAIL_TO_PASS` a Python list, and a split whose
gold `patch` is withheld.

## 3. Seam two: the benchmark registry entry

`src/swebench_unified/benchmarks.py` holds a frozen `Benchmark` dataclass and a
`REGISTRY` keyed by name. The active benchmark is resolved once from
`SBU_BENCHMARK`, and `paths.py` reads the active benchmark's dataset locations at
import, so every existing consumer of `DATASET_JSONL` is unchanged by a port.

The entry is the single place that knows where a benchmark's data lives, how its
container images are named, and how its oracle grades. Adding one is what replaces
the scatter of edits a hard-coded benchmark would require.

Fields, grouped by what they answer:

*Where the data is*

| field | meaning |
|---|---|
| `name` | registry key; the value of `SBU_BENCHMARK` |
| `data_subdir` | frozen data lives under `data/<data_subdir>/` (`SBU_DATA_ROOT` moves the root) |
| `hf_dataset`, `hf_split` | upstream dataset id (or a local directory) and split the fetch script pulls. Pick a split upstream does not grow: the integrity gate compares every bundle against the frozen file |
| `hf_config`, `hf_data_files` | the configuration name, and the file or glob to read inside the dataset repository. Both empty for a dataset whose default configuration loads on its own, which is every shipped benchmark |
| `upstream_columns` | the columns the fetch expects to find, checked before any write, so an upstream schema change aborts instead of rewriting the corpus's inputs |
| `frozen_columns` | the emitted key order when an adapter maps the rows; empty means "same as upstream" |
| `repo_url_template` | where `setup_repos.py` mirrors each row's `repo` from; defaults to `https://github.com/{repo}.git`, which is where both shipped benchmarks' repositories live |

A dataset id and a split are not always enough to name one table.
`ByteDance-Seed/Multi-SWE-bench` publishes 48 per-language files under a single
`train` split, and loading it by id alone fails inside `datasets` on their
unmergeable schemas; `"hf_data_files": "c/jqlang__jq_dataset.jsonl"` selects the
one to read, and `hf_config` is the same lever for a dataset that publishes named
configurations. Leaving both empty makes exactly the `load_dataset(id, split=...)`
call the fetch made before they existed, which is what keeps the two shipped
datasets' sha256 unmoved. `hf_dataset` may also be a local directory of `.jsonl`
files, which is the same seam offline and the way in for a layout no `data_files`
expression selects: fetch or convert the rows yourself, then point the entry at the
directory and the column check, the row check and the deterministic write are
unchanged.

`repo_url_template` is the only statement of where task repositories come from, so
a benchmark whose repositories are not on GitHub uses `setup_repos.py` unchanged.
It must contain `{repo}`, and the constructor refuses a template that does not,
because every task repository would otherwise be mirrored from one URL. A
benchmark whose `repo` is not `owner/name` at all -- some curators publish a bare
project name, and `R2E-Gym/R2E-Gym-Lite` is one -- is not mirrorable from any host,
and its instances are built against a checkout named directly instead
(`build_one.py --repo PATH`).

*What the pipeline is allowed to do*

| field | meaning |
|---|---|
| `supports_docker_oracle` | gates the anchoring correctness check. False means construction runs static gates only, and the Docker gates record an explicit skip with a reason |
| `supports_generated_script_gates` | gates the two gates that run the bundle's own generated probe scripts inside the instance image. Separate from the flag above because a benchmark can have a working oracle while its images lack the environment those scripts assume |

Keeping these two flags distinct is the point: an unsupported capability yields a
clean, stamped skip rather than a construction that reports blocked, and a reader
of the corpus can tell "this gate disagreed" from "this gate was never available
here".

*How the oracle grades*

| field | meaning |
|---|---|
| `resolve_style` | which oracle implementation to use |
| `dataset_name`, `namespace`, `image_tag` | parameters passed through to a standard external harness |

*How to name and enter a container*

| field | meaning |
|---|---|
| `image_template`, `image_id_sub` | derive the image name from the instance id |
| `image_from_row_key`, `image_repo` | or read the image tag out of the row itself, at a dotted path into it (`pro.dockerhub_tag`, or a top-level column) |
| `pull_via_mirror` | whether the image can be fetched through a registry mirror |
| `container_workdir` | where the repository checkout lives inside the image |
| `container_env_activate` | shell prefix that activates the in-image interpreter environment, empty when the system one is correct |
| `container_entrypoint` | override the image default when it is not a shell |
| `container_agent_pythonpath` | whether the shell handed to an evaluated agent needs `PYTHONPATH` pointed at the checkout, for an image that keeps the package in a subdirectory while a stale copy sits in site-packages |

These four container fields are the ONLY description of how to enter a container,
and both container paths read them: the construction-time one that runs a
generated probe script, and the evaluation one that gives an agent a shell.
Neither restates a default of its own -- the checkout directory, the activation
prefix, the entrypoint and the `PYTHONPATH` are the registry entry's to state, so
a port that gets them right gets both halves right at once. The one thing they do
NOT share is how the activation prefix is *joined*: a probe script chains it with
`&&` (a failed activation must abort the check) and an agent's shell with `;` (an
agent must still get its command run). That is the caller's decision about
failure, not a container fact, so it stays in the caller.

The image-naming method deliberately supports both derivation from the id and
lookup from the row, because benchmarks do both, and `image_name()` **raises**
rather than guessing when it lacks what it needs. Pulling a wrong image would run
the oracle against the wrong repository state and produce a confidently wrong
verdict, which is worse than a crash by a wide margin.

The dataclass is frozen and the properties (`dataset_jsonl`, `eval_localization`,
`frozen_instances`) derive paths from `data_subdir`, so a port cannot half-apply.
Every field has a default shaped like the first benchmark, which is what makes a
new entry short and also what lets one be silently wrong, so the constructor
refuses the incoherent combinations outright: a clone URL naming no `{repo}`, a
declared Docker oracle that names no image, a row-keyed image with no repository,
an unknown `resolve_style`, the external harness with no `dataset_name`.
`tests/test_benchmarks.py` is the control
for each of those, and it also requires every entry to declare its frozen column
contract -- run it first after adding one.

### 3a. Declaring a benchmark without editing this repository

The entry does not have to be a source edit. `SBU_BENCHMARK_SPEC` names a JSON
file (or several, separated by the platform path separator) holding the same
fields, and it is read at call time by `registry()`, which every consumer goes
through -- `active()`, the CLI's `--benchmark` choices, the fetch script:

```jsonc
// ~/acme.json
{ "name": "acme_bench",
  "data_subdir": "acme",
  "hf_dataset": "acme/acme-bench",
  "supports_docker_oracle": false,          // static gates only, for a first run
  "upstream_columns": ["instance_id", "repo", "base_commit", "..."],
  "row_map": "acme_adapters:to_frozen" }    // optional; see seam one
```

```bash
export SBU_BENCHMARK_SPEC=~/acme.json SBU_BENCHMARK=acme_bench
export SBU_DATA_ROOT=~/acme-data SBU_BENCHMARK_DIR=~/acme-bundles
python scripts/fetch_dataset.py --limit 4
```

The row mapping of seam one comes with it: `row_filter` and `row_map` are
`module:function` references resolved off `PYTHONPATH`, so a benchmark whose
upstream rows are not the frozen schema brings its own mapping rather than
needing a line added to the fetch script's table. A built-in benchmark leaves
both empty and keeps using that table.

Every refusal above still applies, and two more are specific to an external
entry: an unknown field is named rather than ignored, and a name that would
shadow a built-in is rejected. Both matter because the failure they replace is
silent -- a typo would otherwise leave the default benchmark active while the
operator believes their own is. `tests/test_external_benchmark_spec.py` is the
control.

With this and the four relocation variables (`SBU_DATA_ROOT`,
`SBU_BENCHMARK_DIR`, `SBU_REPOS_ROOT`, `SBU_PROMPTS_DIR`), a port can be run
entirely outside a checkout, which is also how this pipeline is smoke-tested
against benchmarks whose artifacts are not committed here.

## 4. Seam three: the oracle adapter

`harness.run_resolve(instance_id, patch, run_id=None, timeout=..., retries=...)`
is the single interface the rest of the system uses to ask "does this patch
resolve this instance". It returns a `ResolveResult` carrying `resolved`,
`completed`, the raw report, a note, the attempt count, and a flakiness flag.
The anchoring gate, the construction loop, the audit derivation, and the eval
scorer all go through it and know nothing else about your oracle.

To add an oracle, add a `resolve_style` and dispatch to a module exposing the
same signature and return type. The shipped example does exactly this: one style
delegates to a standard external harness; another is a self-contained in-container
runner that resets the repository, applies the candidate, runs the benchmark's own
selected tests, and grades by checking that every required test id appears as
passing.

Policies your adapter must preserve, because callers depend on them:

* **Completed and resolved are different bits.** A run that never produced a
  report (a timeout, an image pull failure, a daemon refusing a container) is a
  failed *measurement*. Return `completed=False`, never `resolved=False`.
  Downstream, an incomplete resolve makes an audit derivation inconclusive; if you
  collapse the two, host load becomes indistinguishable from a real defect in the
  artifact under test.
* **Retry both outcomes.** A correct patch resolves deterministically, so a flip
  means flakiness: resolved on any attempt counts as resolved, flagged flaky when
  attempts disagree, which prevents a spurious "verified but not resolved" from
  being recorded as a benchmark defect. Incomplete attempts must be retried too.
  Retrying only the deterministic outcome inverts the intended policy and is
  observable in a corpus as the same patch resolving under one derivation and not
  completing under another, minutes apart.
* **Content-address any cache key.** If your oracle caches per-instance reports,
  key the run on a hash of the patch. A harness that short-circuits on an existing
  report will otherwise hand back a verdict computed for a different patch. Make
  run directories single-use and purge them, or the cache reintroduces the same
  problem from the other side.
* **Surface the oracle's own last words on failure.** "No report" without the
  runner's stderr tail is untriageable, and it is the most common failure mode
  under load, which is exactly when the cause matters.
* **Respect the host-wide concurrency cap.** Hold a slot around the container run
  only, so queueing does not count against the attempt's own timeout. Use a
  cross-process semaphore, not an in-process one: audit agents resolve from inside
  per-cell subprocesses, where an in-process semaphore cannot see its siblings.

### 4a. Suites that need a live service

A few suites in any real benchmark do not exercise a pure function: they drive a
network client against a live HTTP service. When that service is down or
rate-limiting, every one of those tests fails whatever patch is applied, so the
oracle grades the third party's uptime and records "the reference patch does not
fix the bug". Retrying does not help, because the outage lasts as long as it lasts.

Suites that do this almost always ship their own endpoint override for exactly
this reason. So run the service locally and point the suite at it. This is not a
relaxation: the same assertions run against the same service implementation, and
the only thing that leaves the verdict is somebody else's availability.

`oracle_services` is the seam. Declare the image, ports and override variable in
`SERVICES`, map the repositories that need it in `REPO_SERVICES`, and the oracle's
in-container command list picks up the export. Two policies matter:

* **A service you cannot provide must change nothing.** If the container will not
  start or never answers its readiness probe, emit no override and let the suite
  keep its own default. Handing the suite a URL you did not verify turns an outage
  into a closed port, which is the same failure caused by the fix instead.
* **Probe readiness, do not assume it.** A started container is not a running
  service. The first request after `run` normally loses to the server's own boot,
  and a single immediate probe reports a healthy service as unavailable.

Occasionally one assertion cannot be answered by a local instance at all -- for
example a test that re-addresses the same host under several URL schemes, which a
public host answers on default ports but a single local port cannot. Exclude that
assertion, keyed by repository rather than by instance, since it belongs to the
suite and not to one issue. Excluding a test that cannot grade the patch is sound;
excluding one that can is not, so record which it was and why.

## 5. Seam four: in-container execution for the generated probes

Two gates run the bundle's own generated scripts inside the instance image: the
axiom-soundness probe and the differential conformance probe. Both go through one
execution helper, and everything image-shaped it needs comes from the registry
entry: the image name, whether to pull through a mirror, the working directory,
the environment-activation prefix, and the entrypoint.

For a new benchmark this usually means filling in those five fields correctly and
nothing else. If the images cannot host a generated script at all, leave
`supports_generated_script_gates` false; the two gates then record a skip with a
reason, and the green criterion (see [architecture.md](architecture.md) section 8)
knows that such a skip is not a verdict and will not count the cell as done.

## 6. Seam five: the prompt corpus

Every agent prompt in the pipeline is a file under
`prompts/{shared,<backend>}/<name>.md`. Lookup order is

1. `<override>/<backend>/<name>.md`
2. `<override>/shared/<name>.md`
3. `prompts/<backend>/<name>.md`
4. `prompts/shared/<name>.md`

where `<override>` is `SBU_PROMPTS_DIR` when set; that variable is the only
override and there is no flag. A missing prompt raises rather than falling back to
a default, so a partial override directory fails loudly instead of silently running
a different experiment than the one you configured.

This is the main tuning surface for a new benchmark. A different corpus often
needs different guidance about what to model and where to draw the modeling
boundary, and prompts-as-files means you can ship an override directory alongside
your benchmark and diff it against the shipped corpus, which you cannot do with
prompt text embedded in Python.

Rules to keep the corpus portable:

* **Substitution is strict.** Placeholders are filled with `str.format`, and
  substitution runs only when values are passed. Files that take placeholders must
  escape literal braces; files loaded with no values keep braces verbatim (the
  JSON schema hints rely on this).
* **Only reusable prompt text lives in the file.** Per-instance material (the
  issue, a candidate artifact, localization blocks) is assembled in code. A prompt
  file that inlines instance-specific content cannot be reused and cannot be
  diffed.
* **Never hard-code the bundle root.** Prompts receive it as a substituted value,
  because it is configurable; a prompt that hard-codes a directory name makes
  agents write bundles the pipeline never reads.
* **Never hard-code the checkout directory.** The evaluation prompts receive
  `{workdir}` from the registry's `container_workdir`. This is the same rule and
  for a sharper reason: a prompt that says `/testbed` to an agent whose image
  checks out at `/app` sends it to a directory that does not exist, and the run
  looks like a solver that could not find the code. It also means every
  evaluation mode prompt is now a `str.format` target, so a literal brace in one
  -- including in your override directory -- must be doubled; `load_prompt` names
  the offending file if it is not.

## 7. Seam six: evaluation localization

The evaluation modes that give a solver *edit localization* read it from a
precomputed file under the benchmark's data directory, so the evaluated process
never opens the reference patch. Producing that file is a per-benchmark offline
step: derive, from the reference patch, only the repository-side facts (the changed
files, the changed symbol, its location) and none of the modeling or verification
detail.

For a Python benchmark, the generator is already generic over the registry:

```bash
python scripts/build_eval_localization.py --benchmark <name>
python scripts/build_eval_localization.py --benchmark <name> --check
```

It needs the frozen rows (section 8, step 2) and the mirrors (step 3) and nothing
else -- no network, no Docker. Each entry is the innermost function or class of the
`base_commit` file that encloses a changed line, so the line numbers describe the
tree the solver is given. If your rows are not Python, this is the seam to
reimplement, and `--check` is how you compare a new derivation against the file
you are already shipping.

Two notes. The formal backends can instead read the modeled functions out of a
bundle's `meta.json`, which is often the better source since it is what the
construction actually modeled. And this is the one seam where a leak is
catastrophic and silent, which is why it is precomputed offline rather than
derived at evaluation time: the derivation itself must not happen in a process
that ever talks to a solver.

The modes that are *defined* by localization (0 and its audited twin) refuse to
build a task when an instance has no entry, so a port that skips this step fails
loudly there instead of reporting baseline numbers under a localization label. The
remaining modes never read the file, which is what lets you smoke-test a benchmark
before it exists.

## 8. Order of work for a port

Add the registry entry first, with **both capability flags false** and the row
adapter only if section 2 says you need one. Nothing below needs a Docker daemon;
steps 1 to 3 need no credentials at all, and step 4 needs a model plus the
backend's verifier:

```bash
export SBU_BENCHMARK=<name>

# 1. the entry itself: coherence, the frozen column contract, image naming
python -m pytest tests/test_benchmarks.py tests/test_fetch_dataset.py -q

# 2. smoke the fetch off the corpus data root, then freeze for real
SBU_DATA_ROOT=$(mktemp -d) python scripts/fetch_dataset.py --limit 4
swebench-unified fetch-dataset            # re-run it: the sha256 must not move

# 3. mirror the task repositories and prove every pinned commit is present
python scripts/setup_repos.py
python scripts/setup_repos.py --verify

# 4. one cell, all eight static gates, no daemon
swebench-unified --benchmark-dir benchmark-<name> construct \
    --backend <b> --instance <id> --skip-docker

# 5. re-judge it as a third party would, without touching the artifact
swebench-unified --benchmark-dir benchmark-<name> gates \
    --backend <b> <id> --static-only --no-record
```

`scripts/benchmark_smoke.py` is that whole sequence as one command, for any
benchmark including one only your `SBU_BENCHMARK_SPEC` knows about:

```bash
python scripts/benchmark_smoke.py --root "$(mktemp -d)" --benchmark <name>
```

It confines every path it touches to `--root` (frozen slice, bundle corpus,
repository mirror, dataset cache), stands in a placeholder specification so no
model is needed, runs every gate that needs neither a verifier nor a daemon,
tampers with the frozen inputs to prove the integrity verdict is not vacuous, and
writes `report.json`: the slice's sha256, every schema complaint, both prompt
paths verbatim, every gate verdict, and the release gate's own exit codes. It
asserts nothing -- you read the report -- and its exit code separates the three
answers that matter: `1` a defect in the pipeline or the port, `3` the dataset hub
was unreachable (not a verdict), `0` a report was written.

Three further benchmarks have been driven this way with **nothing added to this
repository**, each declared entirely from a JSON spec and an adapter module
outside the checkout, and each measuring a different depth of the seam:
`nebius/SWE-rebench` (a near-frozen schema: one timestamp spelling, two list
encodings, nine curator extras preserved under a sub-object);
`SWE-bench/SWE-smith` (a `row_filter`, because 18033 of its 59136 rows carry no
issue text at all, and a `base_commit` recoverable only from the mirror
repository's own name); and `R2E-Gym/R2E-Gym-Lite` (no `instance_id`, no `patch`,
no `test_patch` and no test lists -- the patches are rebuilt from the parsed
commit's before/after file contents and the test lists from the two pytest runs
the curator recorded). The deepest of the three is the argument for `row_map`
being a `module:function` outside the package: that is derivation, not mapping,
and it has no business in a table inside this repository.

`tests/test_third_benchmark_smoke.py` is that sequence as an executable template:
it drives the shipped third benchmark from the fetch through the frozen row schema,
construction P0, both prompt-assembly paths and the pure-Python gates, and asserts
a *skip* wherever this host cannot reach further. Run it with
`SBU_SMOKE_NETWORK=1` for the fetch half; without the flag it skips and names what
it would have downloaded. The same flag also enables
`tests/test_fetch_dataset.py::test_fourth_benchmark_freezes_from_its_entry_alone`,
which does the fetch half only, for the fourth benchmark, and pins the digest of
its four-row freeze.

Then, in order:

1. Turn on `supports_docker_oracle` and wire the oracle adapter. Validate it on
   *reference* patches first: they resolve by definition, so any failure is
   infrastructure, and that is also how you calibrate the concurrency cap for your
   host.
2. Turn on `supports_generated_script_gates` once you have confirmed the images
   can run a generated probe script and that the container fields are right.
3. Precompute the evaluation localization file if you intend to run the modes that
   use it: `python scripts/build_eval_localization.py --benchmark <name>` (section
   7).
4. Adjust prompts through an override directory, not by editing the shipped
   corpus, until you are confident the changes are general.

## 9. The spec-strength battery, on a benchmark that has none yet

The battery is the part of a port that no seam can do for you: `properties.py` is
authored per cell, against that cell's frozen specification. The *contract* is
benchmark-independent and is stated in
[docs/architecture.md](architecture.md) section 7 (the case schema, the
byte-identical spec requirement, the admissible variant scope, the mandatory
reject lane), and `construct --pbt` runs the authoring phase against a frozen,
verifying solution and then has G-PBT judge it. What the contract cannot tell you
is how to write cases that measure something, so this section records what
authoring 500 of them measured.

**A battery does not run the specification.** Nothing here evaluates a contract
as code, and on some backends it could not: measured in the Nagini verifier
environment, `Implies(True, False)` returns `None`, `Forall(...)` returns `None`,
and a `PSeq` is not iterable, because those primitives are static markers the
Viper backend interprets rather than Python functions. A battery is therefore two
machines, and a port needs to know which of them it is building:

| lane | a case is | decided by | where it runs |
|---|---|---|---|
| spec | a candidate *implementation* swapped into the impl region | the backend's verifier plus `same_spec` | the verifier environment, no container |
| axiom | a concrete *input* to a callee the specification axiomatised | executing the real callee and comparing against the axiom's postcondition | the instance's container image |

**The four questions a case can ask.** Each names the defect it would establish,
and a case that cannot name one is decoration:

1. *admissibility* -- is the precondition too strong? A positive control calls the
   modeled function on an in-domain input shaped like the benchmark's own tests.
   If the precondition cannot be established for a legitimate input, the finding
   is `PRECOND-TOO-STRONG`.
2. *soundness* -- is the postcondition too strong? A structurally different but
   correct implementation must verify; if no faithful one does, `SPEC-TOO-STRONG`.
3. *uniqueness* -- is the postcondition too weak? Rivals share the specification
   exactly and differ only in the impl region; if one *verifies*, `SPEC-TOO-WEAK`,
   the strongest finding available. The five weakness classes worth targeting are
   an ungrounded-oracle echo (return the answer key a pure function already
   states, doing none of the work), a frame mutation (overwrite a read-only input
   until the postcondition holds vacuously), a value-level double mask (an
   index-level claim checked only through a value proxy that drops the
   disagreeing indices), a control-flow effect (a raise or early return the value
   abstraction cannot see), and a partial domain (pin only part of the input
   domain the tests exercise). A rival must also argue why the *real* patch would
   not have resolved it, or a hit is an artefact of the rival rather than a
   `verify` that fails to imply correctness.
4. *axioms* -- `AXIOM-UNSOUND` (the real callee violates the axiom on an input
   inside the axiom's own domain) and `AXIOM-TOO-WEAK-FOR-CALLER` (an input the
   modeled function actually reaches lies outside that domain). The second is
   containment, not coverage: a callee typed for floats whose caller only ever
   passes integers is correctly axiomatised over integers.

**Volume, calibrated rather than guessed.** The 500 verified batteries hold 4908
cases: 2887 uniqueness, 897 soundness, 513 admissibility, 379 axiom-soundness,
232 axiom-containment. That is roughly six spec cases plus one or two axiom cases
per cell, deliberately uniqueness-heavy, since that is the lane that can find the
strongest defect. Parity with a sibling formalization is the wrong target for the
reason architecture.md section 7 gives.

**The six authoring bugs, and why the default reading of a flagged case is "the
case is wrong".** The verified round's first sweep flagged 85 cells; 81 of those
were defects in the *test*, not in the artifact. At a 95% false-positive rate,
a flagged positive control means "this case has a proof gap" until shown
otherwise, and `SPEC-TOO-STRONG` is real only once no faithful in-region proof
admits any structurally different correct implementation. The six:

1. a malformed type comment. In Nagini it attaches to an assignment, `with` or
   `for` target and never to a bare `return []`, and the text must be exactly
   `# type: T`. A translation failure then arrives as "verification failed" and
   reads as `SPEC-TOO-STRONG`.
2. a positive control that drops a framing assert or lemma. Keep the invariants
   and change only the executable shape, or the failure is about a proof trigger.
3. a forward append against a front-recursive pure fold, which needs a
   distributivity lemma the verifier will not discharge. Reorder branches or
   reshape a local instead of flipping a loop's direction.
4. an axiom probe that reads the callee's *source* instead of calling it. A regex
   over `inspect.getsource` matched a docstring in the pilot. Execute the callee.
5. a container read without an explicit encoding: evaluation images default to an
   ASCII locale.
6. a probe that assumes a bundle file is mounted. The runner mounts the probe
   script alone, so anything else it needs must be read on the host at
   manifest-load time and embedded in the probe source.

**Judge a battery under load and it will report timeouts as verdicts about the
specification.** Run the authoring and the gate sweep at low width with a
generous per-case budget (`SBN_VERIFY_TIMEOUT`, `SBU_MUTATION_TIMEOUT`), and
reproduce any failure read-only before believing it. Porting a finished battery to
a sibling backend is a separate, cheaper lane: `scripts/pbt_port_fleet.py
--backend <b>` reads the cell's sibling battery through
`prompts/shared/pbt_port.md` instead of authoring from scratch, and has its own
`--dry-run`.

## 10. Seams you should not need to touch

If a port requires editing any of these, that is a signal the interface needs
splitting rather than a signal to add a special case:

* the gate modules (they take a `Bundle` and a `Backend`, and know nothing about
  which benchmark is active except through the capability flags),
* the construction loop's phase structure,
* the marker, spec-view, mutation, leakage, variant-admissibility, or witness
  machinery (all keyed on the backend's language tables, not on the dataset),
* the evaluation mode table and its pass criteria (that is the measurement
  definition; changing it per benchmark makes results incomparable),
* the green criterion.

The one honest exception is prompts, which are data, not code, and are meant to be
replaced.
