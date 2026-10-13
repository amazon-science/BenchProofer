# SWE-Proof

SWE-Proof is a benchmark of real repository issues whose correctness criterion is
a machine-checked formal specification rather than a held-out test suite, together
with the pipeline that constructs one. This repository is both: it ships the two
corpora and the code that built them.

Held-out tests are a finite sample of the intended behaviour, so a patch that
passes them can still be wrong on inputs no test covers, and a solver optimising
against them can satisfy the sample without repairing the defect. Verification
quantifies over the whole specified domain instead. What has kept it out of
repository-scale evaluation is that a real fix is entangled with code it does not
change, and that the intent arrives as prose rather than as a contract. SWE-Proof
addresses both by modelling only the behaviour the fix introduces and summarising
its interaction with the surrounding code as axioms, which are then probed against
the real callees.

For every instance the release contains a formal specification of the required
behaviour, those axioms, a reference implementation that verifies against the
specification, the pre-fix implementation that must fail to verify, the equivalent
repository patch with an operation-by-operation correspondence to the
implementation, an adversarial battery of rival implementations with expected
verdicts, and the recorded outcome of every gate that admitted the instance. The
exception is an instance whose repository is under a copyleft license: it ships its
dataset row and its specifications only, and every other file is deliberately
omitted, to comply with the license; see [Copyleft material](#copyleft-material).

## The guarantee

One bundle asserts a biconditional between verification and issue resolution:

```
verify(impl, spec)  =>  resolve(patch)      the specification is strong enough
resolve(patch)      =>  verify(impl, spec)  the specification is not too strong
```

The two directions fail differently. A specification that accepts a wrong
implementation makes a verified answer not a correct one. A specification that
rejects a correct implementation makes the instance unsolvable by a faithful patch
of a different shape. Every gate in the suite attacks one of those directions or
protects an input the attacks depend on.

Because the claim is a relationship between artifacts, none of it can be
established by the party that produced them. No agent self-report is treated as
evidence anywhere in the pipeline: every recorded outcome comes from a mechanical
re-check performed afterwards by code that did not write the bundle.

## What is released

| corpus | task source | instances | bundles built | gate suite |
|---|---|---|---|---|
| `benchmark-verified/` | SWE-bench Verified, all 500 instances | 500 | 2000 | complete: every bundle green; 1,960 ship their gate records |
| `benchmark-pro/` | SWE-bench Pro, Python subset | 266 | 1064 | partial: 994 bundles green when built; none ship their gate records |

The counts are of what was built. What ships of the 276 copyleft-licensed instances
is less, and deliberately so: all 266 of `benchmark-pro/` and 10 of
`benchmark-verified/`, which ship their specifications and a pointer to the upstream
task, without the task's source, implementations or gate records; see
[Copyleft material](#copyleft-material).

Every instance is built independently under four backends, so a bundle is one
(instance, backend) cell and each corpus is a complete instance-by-backend matrix.
The two corpora differ in how far the gate suite has been run over them, and the
difference governs what may be assumed. `benchmark-verified/` passes it in full,
which `scripts/release_gate.py` decides. `benchmark-pro/` does not: its EARS lane
is complete, and of the cells elsewhere that are not green, most have not been
carried through the suite to completion, while the rest either await a property
battery or record an audit that found a defect. That count moves as construction
continues, and it is not a figure to be taken on trust: `scripts/green_check.py`
is the only authority for greenness in this repository, and it reports the reason
for each cell it does not call green. Such a cell should be read as a
specification awaiting a gate rather than as a certified one.

### Copyleft material

**Deliberately omitted, for license compliance.** The material listed in this section
is left out of the release on purpose, to comply with the copyleft licenses of the
task repositories it would be derived from. Its absence is not a defect in the corpus,
and it is not to be restored.

276 instances are under a copyleft license: `ansible/ansible` (96,
GPL-3.0-or-later), `internetarchive/openlibrary` (91, AGPL-3.0),
`qutebrowser/qutebrowser` (79, GPL-3.0-or-later) and `pylint-dev/pylint` (10,
GPL-2.0-or-later). From these projects the release carries only the specifications
derived from the fix, a pointer to the upstream task, and a script that restores the
task from it. In place of each instance's dataset row it ships `upstream.json`,
which names the SWE-bench Verified or SWE-bench Pro instance, its repository,
`base_commit` and license, and carries none of its text.
`scripts/restore_upstream.py` writes the row (issue text, fix patch, test patch)
back from that public dataset, after `scripts/fetch_dataset.py` has fetched it. The
release carries no source of these programs: no fix or test patch, no build and no
repository snapshot. The corresponding complete source is each project's own
repository at the `base_commit` recorded in the pointer, publicly available at
`https://github.com/<repo>`.

Nor does it carry anything else of theirs: no implementation derived from the
programs and no quotation of them. Removal is by whole file, never by editing one: a
file that carries any such material is omitted entire. The one exception is the
specification. A formal solution file (`model.py`, `Solution.lean`) holds the
specification and the reference implementation together, and it ships as its spec
view, the projection a solver is shown, with the implementation and proof regions
elided. So a copyleft instance's directory holds `upstream.json`,
`ears/requirements.md` (its EARS specification) and the spec view of each formal
backend's solution. Everything else is omitted whole: the dataset row (`instance.json`
and `patch.diff`), the pre-fix twins, `refinement.md` and `mapping.md`, `verdict.md` with
its attack implementations and equivalent diffs, `properties.py`,
`conformance_check.py`, `axiom_check.py`, the gate records (`meta.json`,
`result.json`, `pbt_result.json`, whose auditors' notes quote the code), and
`BLOCKED.md` and `RELAXED_LEAKAGE.md`. Outside the corpora the same rule omits the two
reports that walked the SWE-bench Pro cells one by one, an overturn investigation that
kept an instance's implementations, the test whose fixtures quoted their audit
records, and the six evaluation summaries under `experiments/eval/` in which a judge
wrote reasons about one of them. With no gate record shipped, these cells cannot be
counted green from the release, and they can be rebuilt and re-judged only once
`restore_upstream.py` has put their rows back. The upstream datasets are revised from
time to time, so a restored row is the one the dataset holds when it is fetched. It
may differ from the row the specification was built from, and an instance the dataset
has since dropped cannot be restored. `scripts/strip_copyleft.py` made the removal and
wrote the pointers, and [docs/copyleft-withheld.tsv](docs/copyleft-withheld.tsv)
lists the 8,416 files it omitted and the 763 solution files it replaced by their spec
view.

## Anatomy of an instance

```
<root>/<instance_id>/                 immutable inputs, shared by every backend
  instance.json                       the frozen dataset row, verbatim
  patch.diff                          the reference patch
  upstream.json                       a copyleft instance's pointer, shipped in
                                      place of the two files above
<root>/<instance_id>/<backend>/       one constructed bundle
  <solution>                          specification and implementation, plus a
                                      proof where the backend needs one
  <solution>_prepatch                 pre-fix twin: same specification, buggy
                                      implementation, and it must fail to verify
  refinement.md                       operation-by-operation map from the
                                      implementation to patch.diff
  mapping.md                          each formal symbol bound to the repository
                                      symbol it models
  axiom_check.py                      runtime probes of the axioms against the
                                      real callees, in the instance's image
  conformance_check.py                differential probe: implementation against
                                      the real repository
  properties.py                       adversarial specification-strength battery
  pbt_result.json                     that battery's per-case adjudicated outcomes
  meta.json                           gate verdicts and modelling metadata
  verdict.md                          the audit record in full
```

Names follow the backend's language: `model.py` under `nagini`, `Solution.lean`
under the Lean-family backends, `requirements.md` under `ears`. `<root>` comes
from `--benchmark-dir` or `SBU_BENCHMARK_DIR` and defaults to `benchmark/`, so
several corpora can be constructed side by side in one checkout. Grouping by
instance first and backend second keeps the four formalizations of one row
adjacent, and freezes the two immutable inputs once instead of once per backend,
where they could drift apart.

## Backends

| backend | specification language | how obligations are discharged |
|---|---|---|
| `nagini` | Python with Nagini contracts | automatic, through Viper to an SMT solver |
| `velvet` | Velvet, an imperative DSL embedded in Lean 4 | automatic and SMT-backed, checked by the Lean kernel |
| `lean` | Lean 4 with Mathlib | proofs written by an agent, accepted only by the kernel |
| `ears` | structured natural-language EARS requirements | no prover: structural lint plus an adversarial probe audit |

The spread is deliberate. It covers an imperative contract language, a proof
assistant with automatic discharge, one with hand-written proofs, and a
specification form with no prover at all, which is what forces the rest of the
system to be written against an interface rather than against a single verifier.

## Admission

An instance is admitted only when every gate that applies to it passes. The suite
has 13 gates, one module each under `src/swebench_unified/gates/`: eight static,
three run in the instance's Docker image, and two that score an adversarial audit.

| family | gates | what it defends |
|---|---|---|
| mechanical foundations | `G-VERIFY`, `G-DIFF`, `G-GOLD`, `G-MUT`, `G-RESOLVE` | the reference implementation verifies, the pre-fix twin fails under the same specification, mutants of the implementation stop verifying, and the equivalent patch resolves the instance in the official harness |
| modelling boundary | `G-AX`, `G-CONF`, `G-INTEGRITY`, `G-HYGIENE` | axioms are assumed rather than proved, so each is fuzzed against the real callee inside the instance's container, and the formal artifact is checked against the frozen task record and the verifier's admitted fragment |
| property-based falsification | `G-PBT` | a battery of rival implementations with machine-checkable expected outcomes, adjudicated by re-running the verifier under the frozen specification |
| adversarial audit | `G-EQ`, `G-PANEL` | auditors instructed to refute the instance, by exhibiting a correct implementation the specification rejects or an incorrect one it admits, produced no counterexample |
| evaluation integrity | `G-LEAK` | the specification view discloses no more of the fix than the public issue text already does |

Mechanical checks are necessary and not sufficient, which is what the adversarial
families are for: a single reproduced counterexample reopens the instance rather
than merely lowering a score. Verdicts are recorded in the bundle's `meta.json`,
stamped with the mode, a timestamp, the code version, and a digest of the judging
code, so a consumer of a released bundle can tell which judge ran on which bytes.

## The release criterion

Whether a corpus is releasable is not a judgment call. It has one executable
definition:

```bash
python scripts/release_gate.py --benchmark-dir benchmark-verified  # exit 0 = releasable
python scripts/release_gate.py --list         # the checks, and what each defends
python scripts/release_gate.py --only green   # one of them
```

It is a conjunction of independent checks: every cell green, every gate stamp
describing the bytes on disk, every audit verdict still describing the
specification it judged, every property battery still importable, no recorded
failure aimed at a specification the bundle no longer ships, every audit complete
under the current audit prompt, every recorded battery verdict reached by a
harness at least as strict as today's, and no build-time narration left in a
released record. A cell it cannot measure counts as a failure rather than a pass,
so exit 0 means every cell is known sound, not that nothing is known broken.
Section 7 of [docs/reproducing.md](docs/reproducing.md) describes each check.

Run on this release, the gate does not reach exit 0 over `benchmark-verified/`, and
there is nothing for it to check in `benchmark-pro/`. Neither is a finding about a
cell. Both come from what the release leaves out:

* `green` counts the 40 bundles of the 10 copyleft `pylint-dev/pylint` instances as
  not green, because they ship no gate record. For the same reason no cell of
  `benchmark-pro/` ships one (see [Copyleft material](#copyleft-material)).
* `freshness` and `audit-freshness` settle part of the corpus from the development
  repository's git history. Some stamps are dated by commit, and each audit's
  specification is recovered from the blob committed when the audit ran. The
  release ships without that history, so those cells read as undecided: 152 for
  `freshness` and 1,312 for `audit-freshness`.

The other five checks pass over the shipped cells. On the development tree at the
commit this release was cut from (`30bc8034d`), all eight passed over all 500
instances, and the 490 permissive instances ship byte-identical to that tree.

## Installation

```bash
pip install -e ".[dev,eval,viz,figures]"   # every extra the commands here use
npm install -g @anthropic-ai/claude-code   # the CLI every agentic phase spawns
swebench-unified fetch-dataset             # freeze the active benchmark's dataset
python scripts/setup_repos.py              # bare-clone and verify the task repos
bash install.sh                            # build the shared Lean workspace at its pins
bash scripts/fetch_vendor.sh               # the pinned third-party wheels and review-site
                                           # assets, which the release does not ship
bash scripts/setup_verifier_env.sh         # the imperative backend's verifier, in
                                           # its own conda env (it pins tooling that
                                           # cannot coexist with this package's)
```

Python 3.10 or newer. `SBU_BENCHMARK` selects the active benchmark (dataset,
images, oracle style) and `SBU_BENCHMARK_SPEC` can declare one from a JSON file
outside the checkout; see `src/swebench_unified/benchmarks.py`. Task repositories
are mirrors rather than submodules: `setup_repos.py` bare-clones them under
`repos/` (or `SBU_REPOS_ROOT`) and verifies that every commit the frozen dataset
pins is present. Full prerequisites, the configuration surface, and the
reproduction sequence are in [docs/reproducing.md](docs/reproducing.md).

The corpus was built with the Claude Code CLI, but nothing else in the pipeline depends on
it. Every agentic phase calls `run_agent_step` in `src/swebench_unified/agent.py`, so
another coding agent's command-line tool, such as Codex CLI or Kiro CLI, can take its
place: replace that function with one that runs the tool on the same system prompt and
prompt, in the same working directory and with the same tools, and returns the payload
the agent submits (the fields `STEP_SCHEMAS` in `src/swebench_unified/submit_result.py`
lists for the step) in the same `StepOutcome`.

## Constructing and re-judging

```bash
swebench-unified construct --backend <b> --instance <id>    # build one bundle
swebench-unified construct --backend <b> --all [--limit N]  # one agent run per cell
swebench-unified gates     --backend <b> <id> [--static-only | --docker-only]
```

Construction freezes the inputs, then runs a build agent against gate
counterexamples, then a proof phase for the backends that need one, then the
static gates, the container gates, and the adversarial audit. It is resumable, and
a principled block is a valid terminal outcome: an agent that cannot express an
instance inside its language's fragment records why instead of weakening a
contract. `gates` re-judges committed bundles, and `--no-record` judges without
touching the artifact.

Bringing a whole corpus to green is a different shape of work from either entry
point: the residue is a few dozen cells at a time, each red for its own reason.
The batch drivers under `scripts/` are one per reason (author a missing artifact,
re-judge, repair a specification an audit proved defective). Each takes a
worklist, runs its agents in parallel under a per-bundle lock, and decides the
outcome mechanically; the two that decide greenness call `green_check.classify`,
so no driver can report a cell done that the corpus census still counts red.
Section 8 of [docs/reproducing.md](docs/reproducing.md) covers them.

## Evaluating a solver

```bash
swebench-unified eval  --backend <b> --mode <m> --model <k>   # 9 modes
swebench-unified score --backend <b> ...
```

Most of the nine modes exist to disentangle two advantages a verification-aware
setup gives a solver, the verification signal and the edit localization, so that
neither is credited for the other. They range from an unaided baseline through
localization only, specification provided, and specification written from scratch,
to a mode that grades the specification a model produces without grading its
patch. One adapter keeps the information environment identical across backends, so
a difference between two rows is a difference in the specification language and
not in what the solver was told. Mode 101 is agent-side byte-identical to the
canonical baseline and adds only the adversarial counterexample audit to the pass
criterion, which isolates what the audit finds in patches a resolve-only verdict
already accepted. `score` is the mechanical consumer scorer: it reports the
probability of resolving given verification, where "verified" requires sharing the
frozen specification and passing a re-run conformance check rather than an assumed
one. Run output lands under `experiments/` (`SBU_EXPERIMENTS_DIR`).

## Analyses

Post-hoc studies over saved evaluation artifacts, under `scripts/eval/`:

```bash
python scripts/eval/audit_scratch_specs.py --runs <run-id>...   # blind spec re-audit
python scripts/eval/analyze_spec_impact.py                 # table and figures
```

The specification-impact study asks whether a specification-correctness failure
predicts a downstream failure to resolve the issue. Both scripts read the mode in
which the solver writes its own specification and then its patch, so one run saves
both artifacts and the question can be asked at all. The first re-runs the
five-property specification judge (axiom soundness, admissibility, soundness,
completeness, faithfulness) over the specifications a run built for itself, blind
to the outcome and to the solver's patch; the second joins those verdicts against
each instance's result and reports per-property failure rates split by whether the
instance resolved. Method and statistics are in
`src/swebench_unified/eval/spec_impact.py`; the figures need the `figures` extra.

## Review site

```bash
bash viz/serve.sh          # http://127.0.0.1:9000/
```

The gates decide everything mechanical, which leaves the two judgments they cannot
make: whether a specification is faithful to the behaviour it models, and whether
it discloses the fix. Both need the specification, the repository at
`base_commit`, and the gate notes side by side, across hundreds of instances.
`viz/` is that reading surface: one read-only server over the whole
benchmark-by-backend matrix, with optional review comments in an untracked SQLite
file. It adapts per backend rather than assuming one, so a new backend or
benchmark is a registry entry. See [viz/README.md](viz/README.md).

## Porting the pipeline

Nothing in the construction loop, the gate suite, or the evaluation harness is
specific to one dataset or one prover, so the same pipeline can convert another
benchmark into a formally verified twin. Pointing it at one takes a registry
entry, a row adapter if its records are not already the frozen schema, and an
oracle adapter, none of which has to be an edit to this repository:
`SBU_BENCHMARK_SPEC` declares a benchmark from a JSON file outside the checkout,
so a port can be run without forking. Adding a specification language is one
`Backend` subclass.

Two further benchmarks are registered here with no corpus of their own, so the
claim is measured rather than asserted: the SWE-bench-Live `verified` split, which
`tests/test_third_benchmark_smoke.py` drives from the fetch through construction,
prompt assembly, and the static gates, and the SWE-Gym `lite` split, whose records
exercise the parts of the frozen-schema contract Live leaves untouched. Three
more (SWE-rebench, SWE-smith, R2E-Gym) have been driven the same way while
declared entirely outside the checkout, one command each:

```bash
python scripts/benchmark_smoke.py --root DIR --benchmark NAME
```

None of the five required benchmark-specific code anywhere in the pipeline. The
two seams are documented in
[docs/adapting_a_benchmark.md](docs/adapting_a_benchmark.md) and
[docs/adding_a_backend.md](docs/adding_a_backend.md).

## Repository layout

```
src/swebench_unified/     the pipeline: cli, benchmarks, backends, construct,
                          gates, eval
scripts/                  verifier wrappers, fetch and setup scripts, corpus
                          drivers, post-hoc analyses
prompts/{shared,<backend>}/   every agent prompt as a swappable file
                              (override directory: SBU_PROMPTS_DIR)
benchmark-verified/       the SWE-bench Verified corpus (500 instances)
benchmark-pro/            the SWE-bench Pro corpus (266 instances)
lean_shared/              one pinned Lean workspace for both Lean-family backends
viz/                      the review site over the bundle matrix
vendor/wheels/            pinned wheels mounted into the gate containers
                          (fetched by scripts/fetch_vendor.sh, untracked)
data/, repos/             fetched by fetch-dataset and scripts/setup_repos.py
experiments/              evaluation output root (SBU_EXPERIMENTS_DIR)
docs/                     architecture, reproduction, and the two porting seams
tests/                    offline unit suite
```

## Documentation

| document | contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | the bundle, the construction loop, and every gate: what it checks and why it exists |
| [docs/reproducing.md](docs/reproducing.md) | building a corpus from an empty checkout |
| [docs/adapting_a_benchmark.md](docs/adapting_a_benchmark.md) | the seams a different benchmark plugs into |
| [docs/adding_a_backend.md](docs/adding_a_backend.md) | the `Backend` interface and what a bundle must contain |

## Tests

```bash
python -m pytest tests/       # the pipeline
python -m pytest viz/tests/   # the review site (needs the viz extra)
```

Neither suite needs Docker, a verifier, or model credentials. `tests/` covers the
gate framework, the marker and specification-view machinery, the
variant-admissibility and witness checks, the audit-verdict derivation, the prompt
and benchmark registries, and the oracle's retry policy. `viz/tests/` is a
separate root and is not collected by `pytest tests/`.

## License

Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0): the
`LICENSE.txt` at the root of the repository this directory is part of covers it. The
task data keeps its own terms (see [Upstream licenses](#upstream-licenses)).

**Generated by Claude; do not use for model training without Legal approval.** The
benchmark artifacts in `benchmark-verified/` and `benchmark-pro/`, other than the
dataset rows (`instance.json`, `patch.diff`) and the copyleft instances' pointers
(`upstream.json`), and the run records under `experiments/` were generated by Claude. They are licensed CC-BY-NC-4.0 and carry this notice.

### Upstream licenses

Each instance names its task repository and `base_commit`, in `instance.json` or, for
a copyleft instance, in `upstream.json`. The issue text, fix patch and test patch that
a permissive instance ships come from that repository and remain under that
repository's license, as stated by the license file at that commit. The table below
was checked against the license file at every instance's `base_commit`, and
[docs/upstream-licenses.tsv](docs/upstream-licenses.tsv) gives the pointer for each
instance: repository, commit, license and license file.
[THIRD-PARTY-NOTICES](THIRD-PARTY-NOTICES) reproduces each of those license files, and
SWE-bench's, as they read at the instances' base commits. The four copyleft
repositories are treated as described in [Copyleft material](#copyleft-material).

| repository | instances | license at `base_commit` | license file |
|---|---|---|---|
| `django/django` | 231 | BSD-3-Clause | `LICENSE` |
| `ansible/ansible` | 96 | GPL-3.0-or-later | `COPYING` |
| `internetarchive/openlibrary` | 91 | AGPL-3.0 | `LICENSE` |
| `qutebrowser/qutebrowser` | 79 | GPL-3.0-or-later | `LICENSE` |
| `sympy/sympy` | 75 | BSD-3-Clause | `LICENSE` |
| `sphinx-doc/sphinx` | 44 | BSD-2-Clause | `LICENSE` |
| `matplotlib/matplotlib` | 34 | Matplotlib license (PSF-based) | `LICENSE/LICENSE` |
| `scikit-learn/scikit-learn` | 32 | BSD-3-Clause | `COPYING` |
| `astropy/astropy` | 22 | BSD-3-Clause | `LICENSE.rst` |
| `pydata/xarray` | 22 | Apache-2.0 | `LICENSE` |
| `pytest-dev/pytest` | 19 | MIT | `LICENSE` |
| `pylint-dev/pylint` | 10 | GPL-2.0-or-later | `LICENSE` |
| `psf/requests` | 8 | Apache-2.0 | `LICENSE` |
| `mwaskom/seaborn` | 2 | BSD-3-Clause | `LICENSE.md` |
| `pallets/flask` | 1 | BSD-3-Clause | `LICENSE.rst` |

### Source-file headers

Each source file begins with the copyright notice and
`SPDX-License-Identifier: CC-BY-NC-4.0`, a header added for the release. Because
`harness_digest` hashes the judging code's bytes (`gates/`, `pbt_witness.py`,
`variant_scope.py`), that header changes the digest. The shipped judging code digests
to `ecce2ee4500e`. With the header removed it is byte-identical to the code that
stamped `7915e75e3dd0`, so a gate record carrying `7915e75e3dd0` was judged by the
judge shipped here. A record carrying any other digest was judged by an earlier
version.
