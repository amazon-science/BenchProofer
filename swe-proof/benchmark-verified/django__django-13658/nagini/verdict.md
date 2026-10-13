# P2 adversarial audit — django__django-13658

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-13658 nagini bundle. All machine checks pass: same-spec exit 0 (analyzed model == bundle spec byte-identical over spec region); Nagini verify of model.py succeeds (12s); axiom_check.py (G-AX) passes on 11 boundary + 20000 fuzz inputs. Real repo confirmed at base_commit worktree: post-patch execute() builds CommandParser(prog=self.prog_name, usage=..., add_help=False, allow_abbrev=False) where self.prog_name = os.path.basename(self.argv[0]) with '__main__.py'->'python -m django'. The postcondition Ensures(ToSeq(Result().prog) == program_name(ToSeq(self.argv0_basename))) exactly models this: prog derived from the utility's OWN first-argument basename, with bootstrap exception. I probed edge cases the RNG fuzz may skip and could not produce a divergence: (a) empty prog — axiom_check skips via `if prog:` but argparse.ArgumentParser(prog='') reports '' , matching model (basename of ''/trailing-slash paths -> ''); (b) argv0 ending in '/' -> basename '' -> parser.prog ''; (c) '.'/'..' basenames pass through unchanged; (d) '__main__.py' with and without dir prefix maps to 'python -m django'; (e) literal 'python -m django' as argv0 passes through (no double-mapping issue since only the exact bootstrap basename maps). All matched real argparse .prog. Type abstraction str<->List[int] via ToSeq is sound and basename split is at the boundary, consistent with __init__ storing os.path.basename(...). No consumed axioms; program_name is a deep model validated == real by G-AX. The spec ties prog to argv0_basename and is invariant under sys_argv0_basename, correctly capturing the embedded-caller fix (model_prepatch.py deriving from sys_argv0_basename fails the postcondition when sources disagree = correct G-DIFF sensitivity). No spec-too-strong/drift defect found; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage question: does the spec view reveal the gold edit BEYOND the public problem_statement? Baseline is unusually high here: the problem_statement is maximal, quoting the gold patch VERBATIM -- it shows both the before line `parser = CommandParser(usage='%(prog)s subcommand [options] [args]', add_help=False, allow_abbrev=False)` and the exact fix `parser = CommandParser(prog=self.prog_name, usage=..., add_help=False, allow_abbrev=False)`, the `__init__` computation `self.prog_name = os.path.basename(self.argv[0])` with the `'__main__.py' -> 'python -m django'` special case, and the prose thesis that `%(prog)s` wrongly refers to `sys.argv[0]` and should refer to `self.prog_name`.

Every discriminating element of the spec view maps to information already public in that statement: (a) docstring 'parser's program name MUST be the program name the utility already computed from its OWN argument vector ... must NOT be re-derived from the ambient/process-wide argument vector' == the problem statement's own argv[0] vs sys.argv[0] thesis; (b) pure functions bootstrap_name/module_invocation/program_name encoding `__main__.py` -> `python -m django` == the __init__ snippet quoted verbatim in the statement; (c) the two-source Utility (argv0_basename vs sys_argv0_basename) and the embedded-caller/unusable-sys.argv[0] scenario == the reporter's `sys.argv[0] is incorrectly None` embedded-environment description; (d) postcondition ToSeq(Result().prog) == program_name(ToSeq(self.argv0_basename)) restates the desired behavior already shown as code.

Spec is phrased as desired behavior (not as an edit), introduces no edit-site file/line, no consumed axiom, no callee, and no implementation detail absent from the public text. Because the problem_statement already discloses the exact patch, the spec view cannot leak the gold edit BEYOND it. Consistent with G-LEAK=pass ('spec view clean'). Verified spec view via swebench_unified.markers.spec_view over model.py; impl region correctly elided.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
