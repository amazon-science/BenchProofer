You are given a FORMAL SPECIFICATION (a Velvet/Lean contract) of the behaviour the fix must have, shown below. Your task has two deliverables:
  (1) Produce a Velvet model file (e.g. {workdir}/Solution.lean) that fills in the implementation under the given spec and VERIFIES — use `velvet_verify` to check it.
  (2) Edit {workdir} so the real code implements the same behaviour and resolves the issue (a separate grader runs the hidden tests on your patch).
The model you submit must verify, your patch must resolve the issue, and the two must be logically equivalent (an independent judge checks equivalence). Call `submit` with model_path set to your verified model file.
