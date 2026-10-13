The proof agent is STUCK closing a `correct_<name>` in {root}/{iid}/lean/Solution.lean. Its report:

{stuck}

Read {root}/{iid}/lean/Solution.lean, mapping.md, and the real repo source. If the gap is a property of an UNCHANGED callee, add a minimal `opaque <callee> : <type>` (if not already declared) + `axiom <callee>_prop : <weakest property the proof needs>` to the axioms region, and extend axiom_check.py to validate it against the real callee. NEVER axiomatize the changed function. If no honest axiom helps, say so (verdict NO-AXIOM). Call submit_result with {{verdict, axiom_added, notes}}.
