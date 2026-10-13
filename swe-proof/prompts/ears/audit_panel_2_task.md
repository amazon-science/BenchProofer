Bundle: {bundle_dir}/ (requirements.md, meta.json; patch.diff one level up) for instance {instance_id}. Work only in your fresh scratch dir {scratch}; do NOT modify the bundle.

Machine-checkable toolkit (turn claims into facts, not opinions), run from the project root:
- `python -m swebench_unified.nl_attack probe {instance_id} {scratch}/probe.py` — run a standalone python probe on the gold-PATCHED tree in the instance image (exit 0 = behavior holds).
- `... --base` — same probe at the unpatched base_commit.

Judge the requirements against the ACTUAL change: read the issue (instance.json problem_statement), the gold patch.diff, and the patched code's real behavior (probe it). The commonest real defect is a wrong modeling BOUNDARY — requirements pinning one branch or one helper instead of the changed observable behavior. Be rigorous; a rubber-stamp is worse than useless. Call submit_result with {{gate, verdict (FAITHFUL|UNFAITHFUL), diverging_input (the requirement number + concrete input/observation where the requirements disagree with the patched code — REQUIRED for UNFAITHFUL, and cite why none exists for FAITHFUL), counterexample, notes}}.

SUBMITTING IS THE ONLY THING THAT RECORDS YOUR REVIEW. Your prose is discarded -- nothing but the `submit_result` call is read back. A review that ends in a closing message instead of that call is recorded as `INCONCLUSIVE (no verdict submitted)`, which FAILS this gate on a spec you may have just found sound; this is a common failure in practice, not a hypothetical one. So call `submit_result` FIRST, before you write any summary, and call it in every case: a clean review submits FAITHFUL with the evidence you checked, exactly as a finding submits UNFAITHFUL.
