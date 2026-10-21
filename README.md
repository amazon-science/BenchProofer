# Benchproofer

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)](LICENSE.txt)

Turn a real-world benchmark into a formally verified one.

> This code is being released solely for academic and scientific reproducibility purposes, in
> support of the methods and findings described in the associated publication. Pull requests
> are not being accepted in order to maintain the code exactly as it was used in the paper.

Benchproofer takes the tasks of an existing benchmark (SWE-bench, HumanEval, MBPP,
QuixBugs, GSM8K, BigCodeBench, or your own file of tasks), formalizes each one into a
specification plus an implementation a verifier checks, has each formalization attacked
by a language model that did not write it, and then adjudicates the result mechanically.
Every claim about a task is a verdict some gate produced and recorded, so anyone can
re-run the gates on someone else's artifacts and get the same verdicts. Nothing certifies
itself.

How one task goes through drafting, the checks, the review and repair, for every backend:
[docs/workflow.md](docs/workflow.md).

The output is a corpus of *bundles*. Each bundle holds one task formalized in one
verification backend, the artifacts that make the formalization attackable, and its
verdicts, recorded in `manifest.json`:

```
bundles/humaneval/HumanEval_32/dafny/
    manifest.json      digests, provenance, and one verdict per gate
    solution.dfy       specification and implementation, in marker regions
    twins/             the pre-fix implementation, under the same specification
    rivals/            the property-based test suite, each case with the verdict it claims
    correspondence.md  how the implementation corresponds to the fix, operation by operation
    audit/             what an independent review submitted and concluded
    evidence/          what each gate wrote to support its verdict
```

## Why gates rather than a score

A specification can be vacuous, can restate the golden patch, or can hold only
because a bounded search gave up. None of that shows up in a verifier's exit code, so
a bundle is certified only when every required gate reaches a favorable judgment, and
four outcomes are kept apart:

| outcome | meaning |
| --- | --- |
| `certified` | every required gate judged the bundle favorably |
| `rejected` | a gate found something wrong with the bundle |
| `incomplete` | a gate could not decide, crashed, or never ran |
| `dropped` | the task's golden patch fails the task's own tests here, so nothing is judged |

`incomplete` is the outcome that makes the rest trustworthy. A verifier that timed
out, a toolchain that is not installed, and a falsifier that found no counterexample
within its budget are all recorded as undecided rather than as passes, and a gate that
crashes is a defect in Benchproofer rather than a finding about the artifacts.

Seventeen gates run, in three nested sets. Seven need nothing but the artifacts and a
verifier; three more put the verified implementation, and whatever its specification
assumes of an unchanged callee, to the benchmark's own environment; and seven report an
adversarial review by a language model that did not draft the bundle. That last set is
there because two questions cannot be decided by a program: whether the specification is
strong enough to be worth proving anything about, and whether it describes the task it
claims to. A review addresses the first by submitting implementations, wrong ones the
specification should rule out and correct ones it should accept, and every one of them is
re-run through the checker and the benchmark's tests, so a reviewer supplies evidence and
never a verdict. See [docs/gates.md](docs/gates.md).

Realistic code calls things nobody is going to verify, so a specification may assume a
callee instead of modeling it. An assumption is declared in the solution's `axioms`
region and then put to the callee itself: the bundle ships `axioms.py`, which exercises
the real callee where the benchmark's own tests run, and a review writes an independent
fuzzer against the same assumption. A proof modulo an assumption is only worth what the
assumption is, which is why both of those are gates rather than prose.

### The gates and the SWE-Proof paper

Every construction step and correctness gate of the SWE-Proof paper (Section 3, Table 1) has
a counterpart here:

| paper | Benchproofer |
| --- | --- |
| Specification synthesis | the solution draft (specification and reference implementation), and the pre-fix implementation |
| Environment axiomatization | assumptions proposed against the checker, and `axioms.py`, which checks each one against the real callee |
| Verification | `spec.verifies` |
| Discrimination | `spec.discriminates` |
| Mutation | `spec.strength.mutation` |
| Hygiene | `spec.hygiene` |
| Resolution check | `oracle.reference_resolves` |
| Axiom soundness | `audit.axiom_soundness` (independent fuzzers); `spec.axioms_grounded` (the bundle's own `axioms.py`); the paper's check that each axiomatized function is genuinely unchanged is made by `audit.equivalence`, whose `axiom` rows stand only for callees the golden patch does not change |
| Conformance | `impl.conformance` |
| Soundness and completeness | `audit.spec_soundness` (correct implementations it must accept); `audit.spec_completeness` (wrong ones it must rule out) |
| Property-based falsification | `spec.strength.battery` |
| Equivalence | `audit.equivalence` |
| Leakage | `spec.no_leakage` (the mechanical screen); `audit.no_disclosure` (the adversarial reading) |

Three gates are not in that table:
- `artifact.integrity` is the paper's task-identity check (its Table 11).
- `audit.faithfulness` is the attacker panel's unfaithfulness role, and it judges whether the
  specification covers what the fix changes.
- `audit.independence` is new here: it reports a review written by the language model
  that drafted the bundle.

## Install

Everything is pinned and every step is a command in this repository.

```bash
git clone <repository-url> benchproofer
cd benchproofer
conda env create -f environment.yml     # interpreter, git, make, curl, unzip, zstd
conda activate benchproofer
bash scripts/setup.sh                   # pip install -e . against constraints/
```

`scripts/setup.sh` performs an editable install of this package with the extras
declared in `pyproject.toml`, constrained by the lock file for your platform under
`constraints/`, and then reports what works:

```bash
benchproofer doctor
```

The backends that are Python wheels (`falsifier`, `crosshair`, `smt`) come with the
install above. The external provers are optional and separately pinned:

```bash
bash scripts/install/dafny.sh           # Dafny 4.11.0 into .toolchains/
bash scripts/install/lean.sh            # Lean 4.33.0 into .toolchains/
bash scripts/install/nagini.sh          # Nagini 1.3.1 into .toolchains/
make toolchains                         # or all three at once
bash scripts/install/velvet.sh          # Velvet and its Lean libraries; large and slow
```

Docker is needed only for benchmarks whose tests run in a container, such as SWE-bench.
It cannot be installed from conda; see [docs/reproducibility.md](docs/reproducibility.md).

## Quickstart

Check the installation against the fixture corpus that ships with Benchproofer. This runs
offline, needs no language model and no container runtime, and covers the whole pipeline:

```bash
bash scripts/smoke.sh                   # 24 cases, a few minutes
```

Then run it against real benchmarks, which downloads datasets and builds containers:

```bash
bash scripts/smoke.sh benchmarks        # every benchmark adapter, real rows
bash scripts/smoke.sh oracles           # SWE-bench and QuixBugs judged for real
```

To formalize tasks of your own, freeze the inputs first, then draft and judge:

```bash
benchproofer ingest humaneval --limit 20
benchproofer run humaneval --backend dafny --provider anthropic --limit 20
benchproofer report humaneval
```

`run` is every stage in one command: it drafts each bundle, judges it, and repairs what
the gates found until the bundle certifies or the repair budget is spent, at every level;
at `--level audited` it also reviews each bundle, and reviews it again once a repair changed
what the review read. The drafting, the review and the repair are agent sessions, the
review one session per auditor; each but the disclosure auditor, which reads blind, has the
checker and the task's environment at hand. Each stage is available on its own, because the
inputs of a run should be inspectable before anything is drafted, and judging should be
repeatable by someone who did not do the drafting:

```bash
benchproofer audit humaneval -b dafny --audit-model claude-sonnet-5  # have it attacked
benchproofer check humaneval --level audited                         # judge what is on disk
```

Judging needs no language model and no credentials. Drafting, reviewing, and repairing
need a provider and an agent session: install `benchproofer[agent]` and the `claude`
command-line tool. The `claude-code` session is one plug-in, and another coding agent's
command-line tool, such as Codex CLI or Kiro CLI, can take its place: see
[Bring your own agent](docs/guides/bring-your-own-agent.md).

## Benchmarks

| adapter | tasks | oracle | network |
| --- | --- | --- | --- |
| `swebench-verified` | 500 | container | yes |
| `swebench-lite` | 300 | container | yes |
| `swebench-pro` | 266 | container | yes |
| `bigcodebench` | 1140 | inline tests | yes |
| `gsm8k` | 1319 | numeric answer | yes |
| `humaneval` | 164 | inline tests | yes |
| `mbpp` | 500 | inline tests | yes |
| `quixbugs` | 40 | pytest | yes |
| `jsonl` | your file | declared per task | no |

`benchproofer catalog benchmarks` prints this table for your installation, licenses
and dataset URLs included. Adding an adapter is one class and one entry point; see
[docs/guides/add-a-benchmark.md](docs/guides/add-a-benchmark.md).

## Backends

| backend | language | produces | needs |
| --- | --- | --- | --- |
| `dafny` | Dafny | a proof | `scripts/install/dafny.sh` |
| `lean4` | Lean 4 | a proof | `scripts/install/lean.sh` |
| `nagini` | annotated Python | a proof | `scripts/install/nagini.sh` |
| `velvet` | Lean 4 (Velvet) | a proof | `scripts/install/velvet.sh` |
| `smt` | SMT-LIB2 | a proof | installed with Benchproofer |
| `crosshair` | Python | a refutation | installed with Benchproofer |
| `falsifier` | Python | a refutation | installed with Benchproofer |

A prover that verifies has shown the specification holds. A falsifier that finds
nothing has not, which is why the strength gates report `incomplete` rather than
`pass` when a bounded search comes back empty.

## Extending

Benchmarks, backends, oracles, gates, model providers, and agent sessions are all plugins,
resolved through `importlib.metadata` entry points. The built-in components use the same
six groups a third-party package would, so nothing about them is privileged:

```toml
[project.entry-points."benchproofer.benchmarks"]
my-benchmark = "my_package.adapter:MyBenchmark"
```

Guides: [add a benchmark](docs/guides/add-a-benchmark.md),
[add a backend](docs/guides/add-a-backend.md),
[add a gate](docs/guides/add-a-gate.md),
[bring your own model](docs/guides/bring-your-own-model.md),
[bring your own agent](docs/guides/bring-your-own-agent.md).

## Reproducibility

* Setup is three commands, all of them in this repository, all of them pinned.
* Inputs are frozen per task and never rewritten without `--refresh`, so a bundle
  cannot be re-judged against a different task than the one it was built from.
* Verdicts carry the digest of the gate that produced them and the version of
  Benchproofer that ran it, so a stale record is detectable rather than invisible.
* Judging is separate from building and consults no language model.
* `--record` writes a cassette for every language-model request and keeps what each agent
  session was asked. With the bundles and the session transcripts, that is what reproduces
  a run, and judging a bundle again gives its verdicts.
* `--offline` refuses network access and uses only cached and shipped inputs.

Details, including what is not reproducible and why, are in
[docs/reproducibility.md](docs/reproducibility.md).

## Repository layout

```
src/benchproofer/
    core/        tasks, bundles, marker regions, verdicts, plugin registry
    benchmarks/  adapters that normalize upstream rows into tasks
    formalize/   the drafting session: prompts, extraction, repair attempts
    audit/       the review: one agent session per auditor, and what is recorded
    backends/    verifiers and falsifiers
    oracles/     the benchmark's own correctness check
    gates/       one gate per property certification depends on
    pipeline/    ingest, build, audit, adjudicate, repair, report
    llm/         model providers, agent sessions, recording
    smoke/       the installation check and its fixture corpus
    cli/         one module per command
scripts/         setup, lock, checks, toolchain installers, smoke profiles
docs/            concepts, architecture, reference, guides
tests/           unit and integration tests
swe-proof/       SWE-Proof: the SWE-bench Verified and Pro corpora formalized under four
                 backends, and the pipeline that built them (its own package and tests)
```

## Contributing

`make check` runs the formatter, the linter, the type checker, the test suite, and the
offline smoke suite, which is exactly what continuous integration runs. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0). See
[LICENSE.txt](LICENSE.txt), which covers the whole repository, `swe-proof/` included.
The benchmark artifacts in `swe-proof/` were generated by Claude. **Generated by
Claude; do not use for model training without Legal approval.**
Material derived from the four copyleft-licensed task repositories (ansible,
openlibrary, qutebrowser, pylint) is deliberately omitted from `swe-proof/`, to comply
with their licenses. Those instances ship only their specifications (formal ones as
their spec view, with the implementation elided) and a pointer to the upstream
SWE-bench instance, which `swe-proof/scripts/restore_upstream.py` restores the task
from. Every other file of theirs, the issue text and the patches included, is omitted
whole. See "Copyleft material" in [swe-proof/README.md](swe-proof/README.md). The material
the other instances carry from their task repositories and from SWE-bench Verified stays
under those licenses, which
[swe-proof/THIRD-PARTY-NOTICES](swe-proof/THIRD-PARTY-NOTICES) reproduces.

Benchmarks and datasets keep their own licenses; `benchproofer catalog benchmarks`
reports each one.
