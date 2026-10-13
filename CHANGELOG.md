# Changelog

Notable changes to Benchproofer, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[semantic versioning](https://semver.org/spec/v2.0.0.html).

Entries describe what a user would notice. Anything internal that changes no behavior
belongs in the commit message instead.

## Unreleased

The first release. Everything below is new.

### Added

* **The pipeline.** `benchproofer ingest`, `formalize`, `audit`, `repair`, `check`, and
  `report`, plus `run` for all of them at once, `catalog` and `doctor` for what an
  installation can do, and `smoke` to prove it works here.
* **Five kinds of plugin**, all resolved through entry points, so a component from
  another package is indistinguishable from a built-in one: 9 benchmark adapters
  (including `jsonl` for your own tasks), 7 verification backends, 5 correctness
  oracles, 18 gates, and 5 model providers. See
  [examples/plugin](examples/plugin) for a package that adds two of them.
* **Seven checkers behind one interface.** Proofs from Dafny, Lean 4, Nagini (annotated
  Python on Viper), Velvet (program verification in Lean, discharged by a solver) and an
  SMT solver; bounded refutation from CrossHair and Hypothesis. What the two kinds
  establish is not conflated: a strength shortfall under a bounded search is recorded as
  `inconclusive` rather than as a finding, and every report names the backend that
  answered. `scripts/install/dafny.sh`, `lean.sh` and `nagini.sh` install the pinned
  prover toolchains under `.toolchains/`, each one idempotent and each finishing by
  verifying a real file; `velvet.sh` does the same for a Lean workspace pinned to a
  commit and to the revision of every library it resolves.
* **Three evidence levels.** `static` requires 8 gates and needs nothing but the
  artifacts; `oracle` adds the three gates that connect a verified artifact, and what its
  specification assumes of an unmodeled callee, to the task the benchmark poses, which
  usually means a container runtime; `audited` adds the seven that report an independent
  adversarial review. Each required set contains the one below it, so a higher
  certification means strictly more.
* **Adversarial review, and the gates that report it.** `benchproofer audit` asks a
  model that did not draft the bundle for implementations the specification should have
  refused and implementations it should have accepted, plus a judgment on each of the
  three questions no program can pose to itself. Every submission is re-run: spliced
  under the shipped specification for the checker, and put to the benchmark's own
  oracle, so `audit.spec_completeness` reports what the tool observed rather than what
  the reviewer claimed, and `audit.spec_soundness` reads the same rows for the opposite
  question. Before a submission is filed, an answer the checker reached without deciding
  anything about the specification goes back to the reviewer with the checker's own output
  (`audit_fix_rounds`, once by default): a file it could not read settles nothing either
  way, under a prover a file it read and could not prove may be missing only the proof a
  prover expects the implementation region to carry, and a control a falsifier refuted is a
  finding only if the input it names is one the task allows. Each of those would otherwise
  be recorded as a specification that refuses a correct implementation.
  `audit.faithfulness`, `audit.equivalence`, and `audit.no_disclosure` report
  a conclusion only while every file it was reached from is unchanged.
  `audit.equivalence` additionally demands a form the reviewer does not get to choose:
  the implementation's operations set against the benchmark's answer one by one, each
  correspondence an identical operation, a refinement over a narrower type, or a callee
  assumed by contract.
* **Assumed callees, grounded rather than trusted.** A realistic task calls things nobody
  is going to verify, so a specification may model a callee in its `axioms` region and
  declare that the model stands for the real thing. The declaration is what makes the
  proof's qualifier checkable: `spec.axioms_grounded` runs the bundle's own `axioms.py`
  where the benchmark's tests run and requires it to report every declared callee, and
  `audit.axiom_soundness` re-runs the fuzzers an independent review wrote against the same
  assumptions. A disagreement observed at run time is a finding under a falsifier exactly
  as much as under a prover, an assumption nobody attacked leaves the audited gate
  undecided, and a reviewer's program that crashes on its own bug is set aside instead of
  counted as a refutation.
* **Repair as a session, not a patch.** `benchproofer repair` reads a bundle's recorded
  verdicts and drafts it again to answer them, redrafting everything that depended on
  the specification, because an artifact drafted against the old one says nothing about
  the new one. Submissions already on record are re-aimed at the repaired specification
  and kept, so a repair cannot answer one finding by shedding the others, and the
  judgments it invalidated are dropped, which is what makes the bundle ask to be
  reviewed again. `benchproofer run --level audited` is then the whole loop: draft,
  review, judge, repair, review again, until each bundle certifies or `max_repairs`
  rounds are spent.
* **Verdicts that distinguish absence of evidence from evidence.** A crashed gate, a
  timeout, and a bounded search that found nothing are recorded as undecided, never as
  a finding about an artifact, and only a `not_applicable` skip is compatible with
  certification.
* **Drafting that answers the checker rather than itself.** A session repairs a
  solution the checker rejected, redrafts a file the checker could not read, and reads
  its own correspondence document back with the same function the gate uses, so a gap
  costs a turn instead of a bundle. What a second attempt cannot fix is kept and noted:
  the gates decide, not the session. A reply that ran out of room is reported as cut off
  rather than as unreadable, and `max_output_tokens` is the setting that gives a model
  that reasons before it answers room for both. Answers are streamed, so a model that
  spends minutes on one is not mistaken for a stalled connection and asked again.
* **Recorded runs.** `--record` writes a cassette per model exchange for every stage
  that consults one, and the `replay` provider serves them back, so a corpus someone
  else built can be rebuilt offline with no model access and no API key.
* **Reproducibility machinery.** A conda environment, a pinned constraints file, a
  hermetic test suite, and a smoke suite whose cases declare what they need from the
  machine and skip with a reason rather than passing vacuously. A prover that is
  installed but cannot say which version it is counts as unavailable and repeats its own
  explanation, so a half-configured machine produces a skip rather than a red run.
  `scripts/package.sh` installs a built wheel into an empty environment and runs the
  offline suite from outside the checkout, which is the only way to see what a user who
  never clones gets.
* **A smoke suite that reaches the top of the ladder without a credential.** Four of
  its 25 offline cases drive review and repair with a scripted provider that answers
  each prompt from a fixture, so the audited gates, the ones a program cannot decide for
  itself and therefore the easiest to leave untested, are checked on every
  installation: a reviewed bundle certifies, rewriting a reviewed specification expires
  the review of it, a bundle that fails review is repaired, reviewed again, and
  certified, and an assumed callee is certified only once a reviewer's own fuzzer has
  been run against it.
* **Exit codes a script can read.** 1 is the tool failing, 2 is a command line the tool
  did not understand, and 3 is `--strict` reporting that the evidence did not meet the
  bar. A bundle the gates reject is a result rather than a failure, so it exits 0.
* **A ledger that records artifacts, not byproducts.** Bytecode written next to a
  bundle's Python while it is being judged is not digested and is not copied, so a
  bundle judged on one interpreter is not reported as tampered with on another.
