# P2 adversarial audit — sympy__sympy-18189

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_hardcode_true.py`, `atk_3_negate.py`, `atk_4_skip_relabel.py`, `atk_5_empty.py`, `atk_6_double_relabel.py`, `atk_7_branch_echo.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_dead_recompute.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,9 +89,7 @@
     Ensures(len(Result()) == len(solve_family(expand)))
     # post-conditions-end
     # impl-start
-    # Re-derive the canonical family under the caller's option, then re-arrange
-    # every solution into the caller's ordering.
-    canonical = solve_family(expand)  # type: PSeq[int]
+    canonical = solve_family(False)  # type: PSeq[int]
     result = relabel_family(canonical)  # type: PSeq[int]
     return result
     # impl-end
```

Attack 2 — `atk_2_hardcode_true.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,9 +89,7 @@
     Ensures(len(Result()) == len(solve_family(expand)))
     # post-conditions-end
     # impl-start
-    # Re-derive the canonical family under the caller's option, then re-arrange
-    # every solution into the caller's ordering.
-    canonical = solve_family(expand)  # type: PSeq[int]
+    canonical = solve_family(True)  # type: PSeq[int]
     result = relabel_family(canonical)  # type: PSeq[int]
     return result
     # impl-end
```

Attack 3 — `atk_3_negate.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,9 +89,7 @@
     Ensures(len(Result()) == len(solve_family(expand)))
     # post-conditions-end
     # impl-start
-    # Re-derive the canonical family under the caller's option, then re-arrange
-    # every solution into the caller's ordering.
-    canonical = solve_family(expand)  # type: PSeq[int]
+    canonical = solve_family(not expand)  # type: PSeq[int]
     result = relabel_family(canonical)  # type: PSeq[int]
     return result
     # impl-end
```

Attack 4 — `atk_4_skip_relabel.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,9 +89,5 @@
     Ensures(len(Result()) == len(solve_family(expand)))
     # post-conditions-end
     # impl-start
-    # Re-derive the canonical family under the caller's option, then re-arrange
-    # every solution into the caller's ordering.
-    canonical = solve_family(expand)  # type: PSeq[int]
-    result = relabel_family(canonical)  # type: PSeq[int]
-    return result
+    return solve_family(expand)
     # impl-end
```

Attack 5 — `atk_5_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,9 +89,5 @@
     Ensures(len(Result()) == len(solve_family(expand)))
     # post-conditions-end
     # impl-start
-    # Re-derive the canonical family under the caller's option, then re-arrange
-    # every solution into the caller's ordering.
-    canonical = solve_family(expand)  # type: PSeq[int]
-    result = relabel_family(canonical)  # type: PSeq[int]
-    return result
+    return PSeq(0).take(0)
     # impl-end
```

Attack 6 — `atk_6_double_relabel.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,9 +89,7 @@
     Ensures(len(Result()) == len(solve_family(expand)))
     # post-conditions-end
     # impl-start
-    # Re-derive the canonical family under the caller's option, then re-arrange
-    # every solution into the caller's ordering.
     canonical = solve_family(expand)  # type: PSeq[int]
-    result = relabel_family(canonical)  # type: PSeq[int]
+    result = relabel_family(relabel_family(canonical))  # type: PSeq[int]
     return result
     # impl-end
```

Attack 7 — `atk_7_branch_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,9 +89,10 @@
     Ensures(len(Result()) == len(solve_family(expand)))
     # post-conditions-end
     # impl-start
-    # Re-derive the canonical family under the caller's option, then re-arrange
-    # every solution into the caller's ordering.
-    canonical = solve_family(expand)  # type: PSeq[int]
+    if expand:
+        canonical = solve_family(expand)  # type: PSeq[int]
+    else:
+        canonical = solve_family(False)  # type: PSeq[int]
     result = relabel_family(canonical)  # type: PSeq[int]
     return result
     # impl-end
```

Attack 8 — `atk_8_dead_recompute.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -89,8 +89,7 @@
     Ensures(len(Result()) == len(solve_family(expand)))
     # post-conditions-end
     # impl-start
-    # Re-derive the canonical family under the caller's option, then re-arrange
-    # every solution into the caller's ordering.
+    dead = solve_family(False)  # type: PSeq[int]
     canonical = solve_family(expand)  # type: PSeq[int]
     result = relabel_family(canonical)  # type: PSeq[int]
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-18189.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A solver computes the complete set of integer solution tuples of an equation.
  Its enumeration is governed by a boolean option `expand` (when True the solver
  enumerates the full family of solutions — sign and order variants included —
  rather than a single representative family). The public entry point also
  accepts a caller-chosen ordering of the unknowns. When that ordering differs
  from the solver's canonical ordering, the entry point re-derives the answer in
  the canonical ordering and then re-arranges every solution tuple's components
  into the caller's ordering (a single, injective relabelling applied to each
  solution).

  The behaviour that matters: re-arranging the components must NOT change which
  family of solutions is enumerated. The re-derivation that feeds the
  re-arrangement must be performed under the SAME `expand` option the caller
  requested, so the re-arranged answer is the relabelling of the very same
  complete solution family the canonical ordering would have produced.
  Re-ordering the unknowns is a relabelling of coordinates only; it must never
  silently collapse the enumerated family down to the un-expanded one.

Modelling choices (Nagini fragment):
  * The canonical solution family is a `PSeq[int]` of solution-tuple identity
    tokens — one entry per enumerated solution. Re-arranging a solution's
    components is an injective relabelling `relabel` on these tokens (a constant
    index permutation applied component-wise is, on the level the test observes,
    exactly an injective relabelling of solutions), so the re-arranged family is
    the element-wise `relabel` image of the canonical family. The tested
    behaviour observes the family as a set and the re-arrangement is the image
    of the canonical family under one constant bijection, so this carrier is
    faithful (mapping.md §2). Pure sequences carry no heap permission.
  * The option is a `bool`. The canonical solver is an unchanged callee
    `solve_family(expand)` — axiomatized: it is keyed on `expand`; its
    `expand=True` and `expand=False` families are deliberately NOT asserted
    equal (they differ in general — that is the whole point of the option).

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def solve_family(expand: bool) -> PSeq[int]:
    """The canonical-ordering solver (the unchanged callee the entry point
    re-invokes), as a sequence of solution-tuple identity tokens. Keyed on
    `expand` — the `True` and `False` families are NOT asserted equal (the
    option genuinely changes which family is enumerated). Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def relabel(token: int) -> int:
    """The single, injective re-arrangement applied to one solution when the
    caller's ordering of the unknowns differs from the canonical one. It is a
    bijection on solution identities (a coordinate relabelling), so it never
    merges two distinct solutions. Unchanged callee; provenance: mapping.md."""
# axioms-end


# pure-start
@Pure
def relabel_family(s: PSeq[int]) -> PSeq[int]:
    """The re-arranged family: each canonical solution is relabelled into the
    caller's ordering, in order. Front-recursive over `s` (peel the head,
    recurse on the tail), so a single unfold is available per element."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(relabel(s[0])) + relabel_family(s.drop(1))
# pure-end


def reorder_solution_family(expand: bool) -> PSeq[int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The re-arranged answer is the relabelling of the canonical family that the
    # SAME `expand` option produces. Re-ordering the unknowns never changes
    # which family is enumerated — it is enumerated under the caller's `expand`,
    # then relabelled component-wise. A derivation that ignores `expand` and uses
    # a default option cannot satisfy this when `expand` requests the full family.
    Ensures(Result() == relabel_family(solve_family(expand)))
    Ensures(len(Result()) == len(solve_family(expand)))
    # post-conditions-end
    # impl-start
    # Re-derive the canonical family under the caller's option, then re-arrange
    # every solution into the caller's ordering.
    canonical = solve_family(expand)  # type: PSeq[int]
    result = relabel_family(canonical)  # type: PSeq[int]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins the return value EXACTLY: Ensures(Result() == relabel_family(solve_family(expand))). solve_family is @ContractOnly/@Pure with NO True==False equality axiom, so any verifying impl must reproduce the caller's-option canonical family relabelled. Encoded 8 same-spec attacks (impl-region-only edits; same-spec confirmed by `adversary same-spec` exit 0 and byte-diff limited to impl region). Ran `python -m swebench_unified.adversary weakness nagini sympy__sympy-18189 <atk>` on each (parallel batches of 3, env).

RESULTS (weakness exit): atk_1_prepatch=2, atk_2_hardcode_true=2, atk_3_negate=2, atk_4_skip_relabel=2, atk_5_empty=2, atk_6_double_relabel=2, atk_7_branch_echo=2 (all NOT-A-COUNTEREXAMPLE: verification failed = spec correctly rejects the wrong impl). atk_8_dead_recompute=0 CANDIDATE (shares spec AND verifies, 16.5s) — a behaviourally gold-equivalent echo: a dead, discarded `solve_family(False)` plus the correct `solve_family(expand)`.

MATERIALIZED + RAN the faithful refined patch for the sole CANDIDATE (atk_8) through the official harness (run_evaluation, run_id sbu-atk8, cache_level env, image swebench/sweb.eval.x86_64.sympy_1776_sympy-18189): patch_successfully_applied=true, resolved=TRUE, FAIL_TO_PASS test_diophantine success, PASS_TO_PASS all 41 success, 0 failures. Faithful patch = gold single-token fix (permute=permute) + a discarded dead `_ = diophantine(eq, param)` mirroring the dead solve_family(False). It RESOLVES => not a weakness.

BASELINES: gold patch resolved=TRUE (run_id sbu-mg2, same image) — harness sanity. positive_control (model.py) verifies via scripts/nagini_verify.sh exit 0 (7.05s). prepatch_reproduced=true: atk_1 is byte-equal to model_prepatch.py's bug (canonical = solve_family(False)) and FAILS Nagini verification, i.e. the spec senses the change (G-DIFF): for expand==True it would need relabel_family(solve_family(False))==relabel_family(solve_family(True)), which the solve_family axiom deliberately does not grant.

REFINEMENT AUDIT (refinement.md): 4 legs. Leg1 expand:bool <-> permute keyword = R (bool identity). Leg2 solve_family(expand) <-> recursive diophantine(eq,param,permute=permute) = A-consumed (unchanged recursive callee; the CHANGED op — option propagation — is modelled DIRECTLY as the expand argument, pinned by the postcondition, NOT hidden in an axiom about the function-under-change). Leg3 relabel_family fold <-> set comprehension = A-consumed(relabel injectivity)+R(set<->PSeq). Leg4 return = R(set<->PSeq carrier). No kind-3 leg. A-legs correspond to the real unchanged callees; G-AX (axiom_check.py) validates solve_family option-dependence (permute True != False, True superset of False, exact F2P families {(2,3)} vs 8-elt sign/order family) and relabel bijectivity/cardinality-preservation over all symbol orderings. Correspondence holds.

HARNESS NOTE: initial concurrent resolve attempts returned completed=false (409 container-name conflict + cache_level=env removing the shared image while my duplicate same-instance runs raced, plus first-time image pull). Resolved by running gold and atk8 STRICTLY SEQUENTIALLY with distinct run_ids and cleaning only my own containers; both then completed with real graded reports. A large shared audit concurrent runs (other instances) was running concurrently and was not disturbed.

Conclusion: >=5 distinct wrong impls attacked; the spec's exact functional pin rejects every behaviourally-wrong impl (prepatch, hardcode, negate, skip-fold, empty, double-fold, branch-collapse); the single verifying impl is a gold-equivalent echo whose materialized faithful patch RESOLVES under the official harness. No verify-but-not-resolve witness exists. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_hardcode_true.py`, `atk_3_negate.py`, `atk_4_skip_relabel.py`, `atk_5_empty.py`, `atk_6_double_relabel.py`, `atk_7_branch_echo.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_dead_recompute.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_hardcode_true.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_negate.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_skip_relabel.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_empty.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_double_relabel.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_branch_echo.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_dead_recompute.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-18189.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A solver computes the complete set of integer solution tuples of an equation.
  Its enumeration is governed by a boolean option `expand` (when True the solver
  enumerates the full family of solutions — sign and order variants included —
  rather than a single representative family). The public entry point also
  accepts a caller-chosen ordering of the unknowns. When that ordering differs
  from the solver's canonical ordering, the entry point re-derives the answer in
  the canonical ordering and then re-arranges every solution tuple's components
  into the caller's ordering (a single, injective relabelling applied to each
  solution).

  The behaviour that matters: re-arranging the components must NOT change which
  family of solutions is enumerated. The re-derivation that feeds the
  re-arrangement must be performed under the SAME `expand` option the caller
  requested, so the re-arranged answer is the relabelling of the very same
  complete solution family the canonical ordering would have produced.
  Re-ordering the unknowns is a relabelling of coordinates only; it must never
  silently collapse the enumerated family down to the un-expanded one.

Modelling choices (Nagini fragment):
  * The canonical solution family is a `PSeq[int]` of solution-tuple identity
    tokens — one entry per enumerated solution. Re-arranging a solution's
    components is an injective relabelling `relabel` on these tokens (a constant
    index permutation applied component-wise is, on the level the test observes,
    exactly an injective relabelling of solutions), so the re-arranged family is
    the element-wise `relabel` image of the canonical family. The tested
    behaviour observes the family as a set and the re-arrangement is the image
    of the canonical family under one constant bijection, so this carrier is
    faithful (mapping.md §2). Pure sequences carry no heap permission.
  * The option is a `bool`. The canonical solver is an unchanged callee
    `solve_family(expand)` — axiomatized: it is keyed on `expand`; its
    `expand=True` and `expand=False` families are deliberately NOT asserted
    equal (they differ in general — that is the whole point of the option).

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def solve_family(expand: bool) -> PSeq[int]:
    """The canonical-ordering solver (the unchanged callee the entry point
    re-invokes), as a sequence of solution-tuple identity tokens. Keyed on
    `expand` — the `True` and `False` families are NOT asserted equal (the
    option genuinely changes which family is enumerated). Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def relabel(token: int) -> int:
    """The single, injective re-arrangement applied to one solution when the
    caller's ordering of the unknowns differs from the canonical one. It is a
    bijection on solution identities (a coordinate relabelling), so it never
    merges two distinct solutions. Unchanged callee; provenance: mapping.md."""
# axioms-end


# pure-start
@Pure
def relabel_family(s: PSeq[int]) -> PSeq[int]:
    """The re-arranged family: each canonical solution is relabelled into the
    caller's ordering, in order. Front-recursive over `s` (peel the head,
    recurse on the tail), so a single unfold is available per element."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(relabel(s[0])) + relabel_family(s.drop(1))
# pure-end


def reorder_solution_family(expand: bool) -> PSeq[int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The re-arranged answer is the relabelling of the canonical family that the
    # SAME `expand` option produces. Re-ordering the unknowns never changes
    # which family is enumerated — it is enumerated under the caller's `expand`,
    # then relabelled component-wise. A derivation that ignores `expand` and uses
    # a default option cannot satisfy this when `expand` requests the full family.
    Ensures(Result() == relabel_family(solve_family(expand)))
    Ensures(len(Result()) == len(solve_family(expand)))
    # post-conditions-end
    # impl-start
    # Re-derive the canonical family under the caller's option, then re-arrange
    # every solution into the caller's ordering.
    canonical = solve_family(expand)  # type: PSeq[int]
    result = relabel_family(canonical)  # type: PSeq[int]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins the return value EXACTLY: Ensures(Result() == relabel_family(solve_family(expand))). solve_family is @ContractOnly/@Pure with NO True==False equality axiom, so any verifying impl must reproduce the caller's-option canonical family relabelled. Encoded 8 same-spec attacks (impl-region-only edits; same-spec confirmed by `adversary same-spec` exit 0 and byte-diff limited to impl region). Ran `python -m swebench_unified.adversary weakness nagini sympy__sympy-18189 <atk>` on each (parallel batches of 3, env).

RESULTS (weakness exit): atk_1_prepatch=2, atk_2_hardcode_true=2, atk_3_negate=2, atk_4_skip_relabel=2, atk_5_empty=2, atk_6_double_relabel=2, atk_7_branch_echo=2 (all NOT-A-COUNTEREXAMPLE: verification failed = spec correctly rejects the wrong impl). atk_8_dead_recompute=0 CANDIDATE (shares spec AND verifies, 16.5s) — a behaviourally gold-equivalent echo: a dead, discarded `solve_family(False)` plus the correct `solve_family(expand)`.

MATERIALIZED + RAN the faithful refined patch for the sole CANDIDATE (atk_8) through the official harness (run_evaluation, run_id sbu-atk8, cache_level env, image swebench/sweb.eval.x86_64.sympy_1776_sympy-18189): patch_successfully_applied=true, resolved=TRUE, FAIL_TO_PASS test_diophantine success, PASS_TO_PASS all 41 success, 0 failures. Faithful patch = gold single-token fix (permute=permute) + a discarded dead `_ = diophantine(eq, param)` mirroring the dead solve_family(False). It RESOLVES => not a weakness.

BASELINES: gold patch resolved=TRUE (run_id sbu-mg2, same image) — harness sanity. positive_control (model.py) verifies via scripts/nagini_verify.sh exit 0 (7.05s). prepatch_reproduced=true: atk_1 is byte-equal to model_prepatch.py's bug (canonical = solve_family(False)) and FAILS Nagini verification, i.e. the spec senses the change (G-DIFF): for expand==True it would need relabel_family(solve_family(False))==relabel_family(solve_family(True)), which the solve_family axiom deliberately does not grant.

REFINEMENT AUDIT (refinement.md): 4 legs. Leg1 expand:bool <-> permute keyword = R (bool identity). Leg2 solve_family(expand) <-> recursive diophantine(eq,param,permute=permute) = A-consumed (unchanged recursive callee; the CHANGED op — option propagation — is modelled DIRECTLY as the expand argument, pinned by the postcondition, NOT hidden in an axiom about the function-under-change). Leg3 relabel_family fold <-> set comprehension = A-consumed(relabel injectivity)+R(set<->PSeq). Leg4 return = R(set<->PSeq carrier). No kind-3 leg. A-legs correspond to the real unchanged callees; G-AX (axiom_check.py) validates solve_family option-dependence (permute True != False, True superset of False, exact F2P families {(2,3)} vs 8-elt sign/order family) and relabel bijectivity/cardinality-preservation over all symbol orderings. Correspondence holds.

HARNESS NOTE: initial concurrent resolve attempts returned completed=false (409 container-name conflict + cache_level=env removing the shared image while my duplicate same-instance runs raced, plus first-time image pull). Resolved by running gold and atk8 STRICTLY SEQUENTIALLY with distinct run_ids and cleaning only my own containers; both then completed with real graded reports. A large shared audit concurrent runs (other instances) was running concurrently and was not disturbed.

Conclusion: >=5 distinct wrong impls attacked; the spec's exact functional pin rejects every behaviourally-wrong impl (prepatch, hardcode, negate, skip-fold, empty, double-fold, branch-collapse); the single verifying impl is a gold-equivalent echo whose materialized faithful patch RESOLVES under the official harness. No verify-but-not-resolve witness exists. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (G-PANEL-2 drift) check for sympy__sympy-18189/nagini. The modeled function `reorder_solution_family(expand)` asserts (postconditions) that its result equals `relabel_family(solve_family(expand))` and has length `len(solve_family(expand))`. Real callee = the patched `diophantine` reorder branch (`if syms != var:` returns `{tuple([t[dict_sym_index[i]] for i in var]) for t in diophantine(eq, param, permute=permute)}`).

Checks performed:
1. model.py verifies under pinned Nagini (scripts/nagini_verify.sh: 'Verification successful', 6.9s).
2. Set up patched testbed (base_commit worktree + gold patch line `permute=permute` present) and confirmed real behavior: for x**4+y**4-2**4-3**4, permute=True gives the 8-element sign/order family, permute=False gives {}; reorder with syms=(y,x) relabels correctly (True->full family, False->{}).
3. Ran the bundle's conformance_check.py against the patched repo: G-CONF OK, 0 disagreements on 100000 inputs (28 fresh (instantiation,option) points + 99972 fuzz draws).
4. Independent faithfulness probe (not using bundle harness): for 12 supported equations x every non-canonical symbol ordering x expand in {False,True}, compared the REAL reorder-path output against the SPEC composition {relabel(t) for t in diophantine(eq, permute=expand)} AND the cardinality claim len(spec)==len(canonical). Result: FAILS: 0. No input found where the modeled function disagrees with the real callee.
5. Axiom soundness confirmed: solve_family option-dependence (True != False, True superset of False on the F2P eq, exact families match) and relabel injectivity/bijectivity (cardinality-preserving component permutation over all orderings) both hold on the real sympy callee.
6. Spec-region markers (pre/post-conditions, axioms, pure, impl) extract cleanly.

The spec is not too strong and does not drift: it agrees with the real repo behavior on every probed input. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical with the bundle (same-spec exit 0); impl elided in the spec view ('...  # implementation elided — supplied by the consumer'). Gold edit: in diophantine's `if syms != var:` reorder branch, `diophantine(eq, param)` -> `diophantine(eq, param, permute=permute)` (forward caller's permute into the recursive re-derivation). Leakage judged against PUBLIC problem_statement only (hints_text, which contains the verbatim gold diff, excluded). The problem_statement already exhibits the exact symptom+diagnosis: diophantine(n**4+m**4-2**4-3**4, syms=(m,n), permute=True) yields the full 8-element family while syms=(n,m), permute=True yields {(3,2)} — results are order-dependent under permute=True, i.e. the option is not applied uniformly across the syms-reordering path. Line-by-line spec-view check: (1) only abstracted symbols — `expand` not `permute`; `solve_family`/`relabel`/`relabel_family` not `diophantine`; no file name, no line numbers, no `permute=permute` token anywhere. (2) Behavioral prose ('must be performed under the SAME expand option', 'must never silently collapse the enumerated family down to the un-expanded one') and postcondition Result() == relabel_family(solve_family(expand)) state DESIRED behavior — the legitimate G-DIFF discriminator and the direct behavioral counterpart of the order-dependent incompleteness the problem_statement already displays, not a disclosure beyond it. (3) The gold-equivalent impl operation (canonical = solve_family(expand)) is elided, so the consumer must supply the option-forwarding. No repo location, symbol, or edited token exposed; reveals nothing a reader of the public problem_statement could not already deduce. Faithful abstraction, not a leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
