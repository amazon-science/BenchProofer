Bundle: {bundle_dir}/ (model.py, refinement.md, mapping.md, patch.diff, axiom_check.py, conformance_check.py) for instance {instance_id}. The real repo at base_commit is in a worktree under /tmp. Work only in /tmp; do NOT modify the bundle.

Machine-checkable toolkit (turn attacks into facts, not opinions), run from the project root:
- `python -m swebench_unified.adversary same-spec nagini {instance_id} /tmp/atk.py` — exit 0 iff the attack shares the bundle's exact spec (only the impl region differs).
- `python -m swebench_unified.adversary weakness nagini {instance_id} /tmp/atk.py` — exit 0 iff the attack is a CANDIDATE counterexample (shares the spec AND verifies). A spec-too-weak attack must keep the spec and change only the impl.
- `bash scripts/nagini_verify.sh <model.py>` — the pinned Nagini verifier directly (exit 0 = verifies).

Verify the spec region is byte-identical with swebench_unified.markers.same_spec (or the same-spec command). Be rigorous; a rubber-stamp is worse than useless. Call submit_result with {{gate, verdict, leaking_line (the spec-view line that leaks the gold edit beyond problem_statement, for a LEAKAGE finding), counterexample, notes}}.

SUBMITTING IS THE ONLY THING THAT RECORDS YOUR REVIEW. Your prose is discarded -- nothing but the `submit_result` call is read back. A review that ends in a closing message instead of that call is recorded as `INCONCLUSIVE (no verdict submitted)`, which FAILS this gate on a spec you may have just found sound; this is a common failure in practice, not a hypothetical one. So call `submit_result` FIRST, before you write any summary, and call it in every case: a clean review submits NO-LEAKAGE with the evidence you checked, exactly as a finding submits LEAKAGE.
