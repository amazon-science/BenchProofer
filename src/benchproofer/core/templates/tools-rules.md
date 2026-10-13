Run these from the workspace root, the directory this session starts in:

* `./tools verify FILE` puts FILE to the checker, on this machine, as `spec.verifies` puts the
  solution file to it, and changes nothing in the bundle. It prints the checker's status, a
  detail and what the checker printed (8,000 characters at most), and exits 0 when the checker
  accepts the file. The checker stops on a file after $checker_limit seconds.$closure
* `./tools try FILE --as attack`, or `--as control`, with `--patch PATCH` for an attack's
  equivalent patch, judges one submission as the review's gates will, `audit.spec_completeness`
  an attack and `audit.spec_soundness` a control, on a copy of the bundle without its review:
  whether FILE keeps the shipped specification, what the checker says of it, whether executing
  the two on the same drawn inputs, or a proof, shows it does what the reference
  implementation does, what `conformance.py` with FILE's implementation in it finds against the
  repository, and for an attack what the benchmark's tests say of PATCH, applied in place of the
  golden patch and run again up to three times when they reject it. `--test TEST`, with
  `--cites TEXT` for an attack, gives the witness test filed with it, and `--refutation WITNESS` a
  control's refutation witness, which the gate judges the submission by as well; an attack whose
  witness test passes on the fixed code and fails with PATCH is left to the attack validation
  auditor, who rules whether what TEXT cites asks for what TEST checks. It prints the
  submission's row, the gate's verdict, and what the gate established of a submission it leaves
  to the attack validation auditor. `conformance.py`, the tests and a witness test run where
  `./tools run` runs a program; a run of `conformance.py` stops after $program_limit seconds,
  and one of the tests or of a witness test after $run_limit.
* `./tools fuzz FILE --callee NAME` runs FILE as a fuzzer of the unchanged callee NAME, as
  `audit.axiom_soundness` will: as `./tools run` runs a program, with the golden patch
  applied only where FILE asks for it (`# benchproofer:axioms apply-fix`) or NAME is defined in
  a file the golden patch changes. It prints the gate's verdict and FILE's log, and stops FILE
  after $program_limit seconds.
* `./tools run FILE` runs the Python program FILE where the benchmark's tests run, with the
  golden patch applied and with no network unless the task's tests use one. FILE is sent
  alone, as `/bp/<its name>`: no other file of this workspace is there, `scratch/` included, so
  a program that needs one holds it itself. Nothing is set up beyond what the environment
  holds: set up first what the repository's own tests set up before they run -- a Django
  project's settings, say, with `settings.configure(...)` and then `django.setup()`, as its
  test settings do -- or the code fails on the setup it lacks, not on your input. It prints
  the status (`resolved` when FILE exits 0), a detail and what FILE printed (8,000 characters
  at most), and stops FILE after $run_limit seconds.$check_rules

$image_rules A program stopped at its time limit returns only what it printed by then: give a
call that may not end, on an input that makes the code loop or grow without end, a limit of
its own, such as `signal.alarm`, and print with `flush=True` as you go, so a program that is
stopped still shows how far it got.

Each Bash call runs in bash and in the foreground, and one still running after
$command_limit seconds is stopped. The shell keeps its working directory from one call to the
next: the paths given here are relative to the workspace root, so after a `cd` elsewhere give
them from the workspace root again, or in full. Your temporary directory is `tmp/` in the
workspace, which `$$TMPDIR` names; `/tmp` is not yours. A tool call that names a path outside
the workspace, the toolchains the checker uses and the system directories is refused, and the
file tools write only in `scratch/`, in `tmp/` and to the files this session is asked to write.

This session started at $started and is stopped at $stops, $budget minutes later; `date -u`
prints the time now.
