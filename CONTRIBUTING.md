# Contributing

Thank you for wanting to work on this. Benchproofer exists to make claims about
benchmark artifacts checkable by someone who did not produce them, so the bar for a
change is not "does it work here" but "can a stranger re-run it and get the same
answer".

## Set up

The three commands in the [README](README.md#install) are the whole setup:

```bash
conda env create -f environment.yml
conda activate benchproofer
bash scripts/setup.sh
```

Add the external provers if you are touching them, or if you want the offline smoke
suite to cover every backend:

```bash
make toolchains        # Dafny 4.11.0, Lean 4.33.0, Nagini 1.3.1, into .toolchains/
benchproofer doctor    # what this machine can now do
```

Velvet is a separate command, `make velvet`, because it builds a Lean workspace of
several gigabytes and takes far longer than the other three together. The offline smoke
suite does not need it: its case is one of the slow ones.

## Before you open a pull request

```bash
make check             # format, lint, types, tests, offline smoke
```

That is the same script CI runs. It takes about five minutes on a laptop, most of it in
the tests and the smoke suite. Individual steps are available when you want a faster loop:

```bash
make format                          # reformat and apply the autofixable lint rules
make typecheck
python -m pytest tests/unit/test_markers.py -k region
benchproofer smoke gates.tampered    # one smoke case
```

The smoke step of `make check` reports a case whose verifier is not installed as
skipped rather than as a failure, so a checkout without the provers still passes. To
hold yourself to the bar CI's `strict` job applies:

```bash
make toolchains
bash scripts/check.sh --strict-smoke
```

A change that adds a data file the package reads at runtime needs one more check, since
an editable install reads the checkout and hides a build that forgot to carry it:

```bash
make package           # build a wheel, install it alone, run the offline suite from it
```

Optionally, `pre-commit install` runs the formatter, the linter, and the type checker
before each commit. The hooks call the tools in your environment rather than pinning
their own, so they cannot disagree with `make check`.

## What CI runs

| job | what it establishes |
| --- | --- |
| `check` | `scripts/check.sh` on Linux, on the locked dependency tree |
| `test` | the tests and the offline smoke suite on Python 3.10 and 3.12, and on macOS |
| `strict` | the setup in the README, then the offline smoke suite with the pinned provers installed, where a skipped case is a failure |
| `package` | a wheel installs into an empty environment and runs there, data files included |
| `docs` | `mkdocs build --strict` finds no broken link and no unlisted page |
| nightly | the network smoke profiles: every benchmark adapter against real upstream rows |
| velvet | weekly: the pinned Velvet workspace still resolves, builds, and decides |

Python 3.11 on Linux is the interpreter `constraints/` is locked for, so the formatter
and the type checker that decide in `check` are the versions the lock records. The
`test` entries resolve their dependencies freely, which is how an upstream release that
breaks the project shows up in CI rather than in someone's checkout. Linting is not
repeated there: it is a property of the source, and running it against four tool
versions produces noise rather than signal.

## What a change needs

* **A test that fails without it.** For a bug fix, the test reproduces the bug. For a
  gate, one of the tests proves the gate can *fail*, because a gate that passes
  everything is worse than no gate.
* **A verdict, never an exception, out of a gate.** `Gate.run` records a crash as
  `error`, and an error is a defect in the tool rather than a finding about an
  artifact. Keep it that way.
* **`unknown` for anything undecided.** A timeout, a crash, a solver that gave up, and
  output you cannot classify are all undecided. Mapping any of them to a refutation
  turns machine load into apparent defects in artifacts, which is the failure this
  project is built to avoid.
* **Documentation in the same pull request** when behavior a user sees changes. The
  pages under `docs/` are part of the interface.
* **An entry in [CHANGELOG.md](CHANGELOG.md)** under `Unreleased` for anything a user
  would notice.

## Adding a component

Benchmarks, backends, oracles, gates, model providers, and agent sessions are plugins.
Write yours in your own package first: the entry-point groups the built-in components use
are the same ones you get, so nothing has to be merged here for your component to work.

* [Add a benchmark](docs/guides/add-a-benchmark.md)
* [Add a backend](docs/guides/add-a-backend.md)
* [Add a gate](docs/guides/add-a-gate.md)
* [Bring your own model](docs/guides/bring-your-own-model.md)

A component belongs in this repository when it is one most users would want and it is
maintainable here: a public benchmark, a widely used verifier, a provider protocol
with several implementations. Open an issue before writing it, so nobody duplicates
work.

Two changes deserve an issue and a discussion first, because they change what a
published verdict means:

* **Adding a gate to the required set** in `pipeline/adjudicate.py`. The argument to
  make is that a bundle passing the current gates can still be unsound in the way your
  gate catches. It also invalidates existing corpora, which have to be judged again.
* **Changing how an existing gate decides.** A recorded verdict carries the digest of
  the gate that produced it, so a change in the logic is detectable, but everything
  judged before it still has to be re-judged to be comparable.

## Style

Ruff and mypy decide, and both are configured in `pyproject.toml`. What they cannot
check:

* Modules stay small and single-purpose. One gate per module, one command per module,
  one benchmark adapter per module.
* Docstrings say what a thing is for, not what the next line does. A comment explains
  why the code is the way it is, especially when the obvious version would be wrong.
* Error messages name the thing that failed and, where one exists, the command that
  fixes it. `benchproofer doctor` prints those hints, so they earn their keep.
* No em dashes, and no exclamation marks in output the tool prints.

## Dependencies and pins

New runtime dependencies need a reason a reviewer agrees with; the runtime tree is
deliberately short. Optional features go in an extra in `pyproject.toml`.

Nothing installs itself outside a pinned command. If you add a dependency or bump one:

```bash
bash scripts/lock.sh     # rewrite constraints/<platform>-<interpreter>.txt from what is installed
```

Commit the regenerated lock file with the change. A downloaded toolchain is pinned by
version and SHA-256 in `scripts/install/`, and a dataset by revision and SHA-256 in
its adapter. An unverified download is worse than a missing one, because it silently
changes what a verdict means.

## Releasing

`pyproject.toml` holds the version, and everything else reads it from the installed
metadata, so `benchproofer --version` and the provenance stamped into every verdict
cannot disagree with the distribution. To cut a release:

```bash
make check && make package     # the two bars: the checkout passes, and a wheel works alone
```

Then move the `Unreleased` entries of [CHANGELOG.md](CHANGELOG.md) under a heading for
the version with today's date, bump `version` in `pyproject.toml`, commit, and tag the
commit `v<version>`.

## Reporting

* A bug or a feature request: open an issue in the project's issue tracker. The
  templates ask for the output of `benchproofer doctor`, which usually answers the
  first three questions a maintainer would have.
* A question about how something is meant to work: start a discussion, or open an
  issue if you cannot tell whether the behavior is intended.
* Conduct: this project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).

## License

Contributions are made under the [CC-BY-NC-4.0 license](LICENSE.txt) that covers this
repository.
