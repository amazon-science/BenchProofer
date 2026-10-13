# Quickstart

## 1. Install

```bash
git clone <repository-url> benchproofer
cd benchproofer
conda env create -f environment.yml
conda activate benchproofer
bash scripts/setup.sh
```

The conda environment provides the interpreter and the few system tools the toolchain
installers need (`git`, `make`, `curl`, `unzip`, `zstd`). `scripts/setup.sh` installs
this package in editable mode against the lock file for your platform in
`constraints/`. Nothing else is installed by hand at any point.

Check what the installation can do:

```bash
benchproofer doctor
```

Every component that is not ready prints the command that makes it ready. Nothing in
the quickstart below needs a component that `scripts/setup.sh` did not install.

## 2. Prove the installation works

```bash
bash scripts/smoke.sh
```

Twenty-four cases, a few minutes, no network and no containers. They exercise the
registry, every backend but Velvet (whose case is slow), the local benchmark adapter,
three oracles, every gate, and the whole pipeline: a scripted formalization session whose
artifacts are compared byte for byte with the fixture it was scripted from, and a bundle
that is reviewed, rejected, repaired, reviewed again, and certified. See [Smoke suite](smoke.md) for what each case
asks.

## 3. Formalize your own tasks

Write a JSON Lines file where each line is a task:

```json
{"task_id": "coin-change", "statement": "Return the fewest US coins that make an amount.", "oracle": {"kind": "inline-tests", "tests": ["assert impl(30) == (1, 0, 1, 0)\n"]}}
```

Freeze it, formalize it, and judge it:

```bash
benchproofer ingest jsonl --extra source=my-tasks.jsonl --extra name=my-suite
benchproofer formalize my-suite --backend falsifier --provider anthropic
benchproofer check my-suite --level oracle
```

`ingest` writes `task.json` next to where the bundles will go and never rewrites it
without `--refresh`. `formalize` drafts the artifacts. `check` runs the gates and
records one verdict each.

Without language-model credentials, use the fixture corpus instead: it ships four bundles
that were drafted this way, two sound and two defective, and `bash scripts/smoke.sh`
judges all four.

## 4. Have it attacked

A specification can be verified, strong against every mutant, and still too weak to be
worth proving anything about. That question is decided by asking someone who did not
write it:

```bash
benchproofer audit my-suite --backend falsifier --audit-model claude-sonnet-5
benchproofer check my-suite --level audited
```

The review is asked for implementations the specification should have ruled out and
implementations it should have accepted, and every one of them is re-run through the
checker and the benchmark's own tests, so nothing a reviewer claims is taken on trust. A
bundle the review breaks is repaired to address what it found, and reviewed again:

```bash
benchproofer repair my-suite --level audited
benchproofer audit my-suite --backend falsifier --audit-model claude-sonnet-5
```

`benchproofer run --level audited` is that loop in one command. See
[Audited gates](gates.md#audited-gates) for what each of the seven reports.

## 5. Read the result

```bash
benchproofer report my-suite
benchproofer report my-suite --out reports/   # report.json and report.md
```

A bundle is listed as `certified`, `rejected`, `incomplete`, or `dropped`, and an
unfinished bundle is listed with the gates that objected. Reporting runs nothing: it
reads the verdicts in each `manifest.json`, so it says exactly what was recorded.

## 6. Take it to a real benchmark

```bash
benchproofer run humaneval --backend dafny --provider anthropic --limit 20 --report reports/
```

`run` is every stage in one command, and at `--level audited` that includes the
review-and-repair loop. It needs a prover for a proof backend
(`bash scripts/install/dafny.sh`) and a model provider for drafting. For a benchmark
whose tests run in a container, such as SWE-bench, add `--level oracle` and make sure
Docker is running:

```bash
benchproofer run swebench-verified --backend falsifier --level oracle --limit 5
```

## Exit codes

| code | meaning |
| --- | --- |
| 0 | the command did what it was asked |
| 1 | Benchproofer could not do its job |
| 2 | the command line was wrong |
| 3 | Benchproofer worked, and the result did not meet the bar `--strict` set |

Code 3 is how continuous integration tells "benchproofer broke" apart from
"benchproofer worked and the specifications did not hold up".
