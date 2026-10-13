Instance: {instance_id}

Work ONLY in your scratch dir {scratch} (already created). The repo checkout
with the AGENT PATCH applied is at {wt} (read-only exploration; run code
against the instance image via the probe runner, not this checkout's env).

Materials:
- EARS requirements (what the coding agent saw, IF its mode provided them):
  {bundle}/requirements.md
- FORMAL ground-truth spec (lean sibling, spec regions): {scratch}/formal_spec.lean
- The agent's accepted patch: {scratch}/agent.patch
- The issue: `problem_statement` in {inst}/instance.json
- Hidden tests (privileged, for coverage analysis): `test_patch`,
  `FAIL_TO_PASS`, `PASS_TO_PASS` in {inst}/instance.json

Probe runner (from the project root {root}):
- under the AGENT patch: `python -m swebench_unified.nl_attack probe {instance_id} {scratch}/cex.py --patch {scratch}/agent.patch`
- under the GOLD patch:  `python -m swebench_unified.nl_attack probe {instance_id} {scratch}/cex.py`
Exit 0 = the behavior HOLDS on that tree.

Deliverable: call submit_result with
{{"verdict": "counterexample"|"clean",
  "counterexample": "<absolute path of your cex script, if any>",
  "diverging_input": "<one line: the input and the two observed behaviors>",
  "notes": "<what you probed and why you believe the verdict>"}}
A "counterexample" verdict REQUIRES that you ran both probe legs and saw
VIOLATED under the agent patch and HOLDS under gold.
