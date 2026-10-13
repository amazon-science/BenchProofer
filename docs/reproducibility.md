# Reproducibility

Two claims are worth separating. The weaker one is that you can install Benchproofer and
get the same dependency tree as everyone else. The stronger one is that a corpus someone
published can be re-judged by a stranger and produce the same verdicts. Both are
addressed below, and so is what remains genuinely irreproducible.

## Installing

Three commands, all of them in this repository:

```bash
conda env create -f environment.yml
conda activate benchproofer
bash scripts/setup.sh
```

* `environment.yml` pins the interpreter to Python 3.11 and provides the system tools the
  project shells out to: `git` for the adapters that read a repository, `curl`, `unzip`,
  and `zstd` for the toolchain installers, `make` for the entry points in the `Makefile`.
* `scripts/setup.sh` runs one editable install of this package with its extras, applying
  the version lock in `constraints/<platform>-<interpreter>.txt`. Every Python dependency
  is declared in `pyproject.toml`, so that one install is the whole of it.

The lock file is a constraint file, not a requirements file. Nothing in it is installed
unless `pyproject.toml` asks for it, directly or through another package, so it pins
versions without adding dependencies. Regenerate it after changing a dependency:

```bash
bash scripts/lock.sh          # writes constraints/<platform>-<interpreter>.txt
```

On a platform with no lock, `setup.sh` says so and resolves freely, which is a weaker
guarantee that the run reports rather than hides.

## Verifier toolchains

The external provers are separate, versioned installs, each pinned by the script that
performs it and each written under `.toolchains/`:

```bash
bash scripts/install/dafny.sh     # Dafny 4.11.0
bash scripts/install/lean.sh      # Lean 4.33.0
bash scripts/install/nagini.sh    # Nagini 1.3.1, with the interpreter and JVM it needs
make toolchains                   # all three of the above
bash scripts/install/velvet.sh    # Velvet, with Lean 4.24.0 and its libraries
```

Dafny and Lean are one release archive each, checked against a SHA-256 recorded in the
script before it is unpacked. An unverified verifier is worse than a missing one,
because it silently changes what a verdict means.

Nagini is a Python package that drives Viper on a JVM, so it gets a conda prefix of its
own under `.toolchains/nagini`: one pinned interpreter, one pinned JDK, and
`nagini==1.3.1`, whose own metadata pins the mypy and Z3 it verifies with. Nothing is
installed into the environment you work in, which is why the version of mypy this
project is developed against is not decided by a verifier. The script checks each piece
separately and finishes by verifying a real module, so a partial install names itself
instead of turning into a prover that reaches no verdict on every file.

Velvet is a Lean library rather than a release archive, so what is pinned is a commit and
a dependency graph: the installer clones Velvet at one commit, checks that the commit's
own `lean-toolchain` agrees with the Lean release it downloaded, and then compares the
resolved revision of every transitive library against
`scripts/install/velvet/lake-manifest.json` both before and after the build. A revision
that differs from that file names itself and stops the install, because a proof replayed
against a different Mathlib is not the proof that was checked. The workspace records its
Lean and Velvet versions only after a real method verifies in it, so a half-built
workspace reads as unavailable rather than as a prover that refutes everything. It is
also the one install that is not relocatable: Velvet's solvers are fetched to a path
relative to the workspace root, so moving the directory means reinstalling it.

Every installer is idempotent: it reports what is already pinned in place and exits,
and `--force` reinstalls.

The Lean backend, under the plain `lean` executable, uses the kernel alone and imports no
external library, Mathlib included, so there is no library revision to pin beyond the
toolchain itself. Where `BENCHPROOFER_LEAN_WORKSPACE` names a built Lake workspace, it
elaborates there instead, and a solution may import that workspace's packages, Mathlib
among them, at the revisions the workspace pins; that workspace is then part of what
decided a verdict. Velvet is the opposite case, and the paragraph above is how that is
handled.

Backends resolve their executable in a fixed order, and the repository-local directory
comes before `PATH`, so a checkout with pinned toolchains is not silently judged by
whatever else is installed on the machine. See
[Backends](backends.md#finding-the-executable).

## Docker

Docker is needed only for benchmarks whose tests run in a container, which among the
built-in adapters means SWE-bench. It cannot be installed from conda, and this project
does not try: install it from your distribution or from Docker's own packages, and then

```bash
benchproofer doctor      # the docker oracle row reports the daemon version
```

Without it, everything else still works. The container oracle reports
`oracle_unavailable`, `check --level oracle` leaves those bundles `incomplete` rather
than rejected, and `--level static` is unaffected.

Image provenance is upstream's. A SWE-bench task names its image, and that image is built
and published by the benchmark's maintainers; what Benchproofer pins is which image the
task names.

## Inputs

* A task is frozen at ingestion into `task.json` and never rewritten without
  `--refresh`, so a bundle cannot be re-judged against a different task than the one it
  was built from.
* Every dataset is named by repository *and* revision, never a branch, and every
  downloaded file is checked against a recorded SHA-256. QuixBugs, which is a repository
  rather than a dataset file, is pinned to a commit.
* Task selection is deterministic: explicit ids, or the first N in the adapter's own
  stable order. There is no sampling flag, because a subset that changes between runs
  cannot be compared between runs.
* `--offline` refuses network access and uses only cached and shipped inputs, so a
  cache miss becomes an error instead of a silent download.

## Verdicts

* Judging writes no artifact and consults no language model. `benchproofer check` over a
  corpus someone else built re-checks every verdict in it.
* Every verdict carries the version of Benchproofer that produced it and a digest of the
  judge that produced it, so a record made by an older gate is detectable rather than
  merely old. The digest covers the sources that can reach a verdict, so it changes when
  the judge changes and not when an unrelated file does.
* Every verdict names the artifacts it read, with their digests. `artifact.integrity`
  (the paper's task-identity check) is what notices a solution edited after it was
  judged.
* `classify` is the only place that turns a bundle's verdicts into an outcome, so a
  report and a `--strict` exit code cannot disagree about what is certified.
* A gate that crashes records an error, never a finding, and a bounded refuter that
  found nothing records `inconclusive`. Neither a loaded machine nor a broken gate can
  manufacture a defect in a sound artifact.
* A review is evidence, not a verdict. Every implementation a reviewer submitted is
  re-run here rather than believed, and every conclusion a reviewer drew names the files
  it was reached from, so it is reported only while those files still have the digests
  they had when they were read. Re-judging someone's corpus therefore re-checks what
  their review established, not just what it said.

To check a published corpus yourself:

```bash
benchproofer check --bundle-root their-corpus --level audited
benchproofer report --bundle-root their-corpus --level audited --out reports/
```

Both sets of verdicts are then on disk, and a verdict that differs is a difference
between the two installations, which the stamps localize.

## Model runs

Three stages consult a language model (drafting, reviewing, and repairing), and a
language model's output is not reproducible. Drafting the solution, each auditor, the
repair and the proof sessions are agent sessions, whose turns depend on what the
filesystem said as they ran; the rest of drafting (the pre-fix implementation, the
property-based test suite, `correspondence.md`, `conformance.py` and `axioms.py`) is
requests. Running a run again does not reproduce it. What it leaves does:

```bash
benchproofer run humaneval --backend dafny --provider anthropic --record --limit 20
```

* **The bundles.** Each holds every artifact the gates judged, what the review submitted
  and concluded, and the repair record (`provenance.repairs` in `manifest.json`) of what
  each repair addressed.
* **The recorded requests.** `--record` writes a cassette per language-model exchange,
  keyed by the digest of the request, holding the request and the reply.
* **The transcripts.** `--record` keeps what each agent session was asked under
  `<cassette dir>/sessions/`, named by the session id Claude Code keeps its transcript
  under.

Judging a bundle is deterministic, so anyone with the bundles derives every verdict again
(`check`, above) without an API key. Recording is the same code path as a normal run plus
a file write, so a recorded run and a live one differ in nothing but the file write.

No gate consults a language model, which is what keeps the irreproducible stages out of the
evidence: a review is recorded as artifacts, the implementations it submitted and the
conclusions it drew, and the gates that report it re-run those artifacts here.

## What is not reproducible, and what that costs

| not reproducible | consequence | what limits the damage |
| --- | --- | --- |
| a language model's output | two runs draft different artifacts | verdicts come from gates over the artifacts, not from the session; the bundles, the recorded requests and the transcripts say what a run did, and judging its bundles again gives its verdicts |
| a reviewer's output | two reviews attack a specification differently | every submission is re-run here, and a review that decided too few attacks is `inconclusive` rather than a pass, so a weak review cannot certify a bundle |
| solver time | a checker that reached its verdict in 100s may time out at a lower budget | a timeout is recorded as undecided, never as a refutation, so the bundle is `incomplete` rather than rejected |
| a bounded search | a falsifier may or may not find a given counterexample | a shortfall under a falsifier is `inconclusive`, and the report names the backend |
| upstream availability | a dataset or image can disappear | the cache holds what was fetched; the pin makes a substitution detectable |
| SWE-bench images | built by upstream, not here | the docker oracle records the tests' output, and `oracle.reference_resolves` (the paper's resolution check) fails loudly when the original benchmark's reproduction code is broken |
| a machine's load | slow runs, evicted caches | nothing that depends on wall clock is treated as evidence about an artifact |

The pattern is the same in every row: what cannot be pinned is prevented from becoming
evidence.

## Reproducing this repository's own checks

```bash
make check                  # format, lint, types, tests, offline smoke
make toolchains             # the three provers, so no case has to be skipped
bash scripts/smoke.sh ci    # the offline suite, where a skipped case is a failure
```

That is exactly what continuous integration runs, on the locked dependency tree. The
order matters: `make check` reports a case whose verifier is missing as skipped, and the
`ci` profile turns that skip into a failure, so the toolchains have to be there first.
