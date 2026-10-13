You are given a FORMAL SPECIFICATION (a Lean 4 contract) of the behaviour the fix must have, shown below. Your task has two deliverables:
  (1) Produce a Lean model file (e.g. {workdir}/Solution.lean) that fills in the implementation and correctness proof under the given spec and VERIFIES — use `lean_verify` to check it.
  (2) Edit {workdir} so the real code implements the same behaviour and resolves the issue (a separate grader runs the hidden tests on your patch).
The model you submit must verify, your patch must resolve the issue, and the two must be logically equivalent (an independent judge checks equivalence). Call `submit` with model_path set to your verified model file.
