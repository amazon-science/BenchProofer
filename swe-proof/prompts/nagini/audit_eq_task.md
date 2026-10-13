Bundle: {bundle_dir}/ (model.py, refinement.md, mapping.md, patch.diff, axiom_check.py, conformance_check.py) for instance {instance_id}. WORK ONLY in your fresh scratch dir {scratch} (already created, empty — do NOT use any other /tmp path; ignore stray files elsewhere).

Tools (copy-paste; run from the repository root):
- Same-spec + verifies in one shot: `python -m swebench_unified.adversary weakness nagini {instance_id} {scratch}/atk_N.py` (exit 0 = CANDIDATE: shares the spec AND verifies; exit 2 = not a counterexample).
- Same-spec only: `python -m swebench_unified.adversary same-spec nagini {instance_id} {scratch}/atk_N.py` (exit 0 = spec byte-identical).
- Verify directly: `bash scripts/nagini_verify.sh {scratch}/atk_N.py` (exit 0 = verifies).

Build each attack by copying {bundle_dir}/model.py into {scratch} and editing ONLY the impl region (leave axioms/@Pure/Requires/Ensures byte-identical). Be rigorous; a rubber-stamp is worse than useless.

Submit the machine-checked artifacts (the runner RE-RUNS them; your verdict is advisory): call submit_result with {{gate, verdict, attacks (absolute {scratch} paths of your same-spec wrong-impl files), positive_control (absolute path of the correct impl that must verify), prepatch_reproduced (bool), patches ({{attack_path: faithful_patch_text}} for every attack that verifies), counterexample, notes}}. PATCHES VALUES MUST BE RAW UNIFIED-DIFF TEXT (starting `diff --git` or `--- `/`+++ ` hunks) that git-apply can consume at the repo root — NEVER a prose description, a pointer like 'SEE FILE ...', or a bare file path: the machine feeds the VALUE itself to git-apply, a non-diff value derives INCONCLUSIVE and fails the gate. For an attack that is an ECHO of the gold behavior, the faithful patch is the bundle's gold patch.diff VERBATIM (or the refinement-mapping-faithful transliteration) — do not invent a concretization that violates the declared mapping.
