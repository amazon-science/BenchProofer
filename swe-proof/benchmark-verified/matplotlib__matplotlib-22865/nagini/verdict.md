# P2 adversarial audit — matplotlib__matplotlib-22865

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.py`, `atk_2_boundary_start.py`, `atk_3_boundary_end.py`, `atk_4_partial_n2.py`, `atk_5_cfe_stride.py`, `atk_6_cfe_droplast.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7_echo_helpers.py`, `atk_8_echo_index.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # At least the two end-most separators exist (a divided scale always has
     # the two extreme boundaries among its candidate separators).
     Requires(len(segments) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segments), 1 / 2))
@@ -89,26 +87,22 @@
                 Result()[k] == segments[start_index(lower_open) + k])))
     # post-conditions-end
     # impl-start
-    start = 0 if lower_open else 1
-    end = len(segments) if upper_open else len(segments) - 1
+    # WRONG: pre-patch skeleton — drops both end-most separators unconditionally
+    start = 1
+    end = len(segments) - 1
     result = []  # type: List[int]
     i = start
     while i < end:
-        # invariants-start
         Invariant(Acc(list_pred(segments), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(start == start_index(lower_open))
-        Invariant(end == end_index(upper_open, len(segments)))
-        Invariant(0 <= start and start <= 1)
-        Invariant(end == len(segments) or end == len(segments) - 1)
+        Invariant(start == 1)
+        Invariant(end == len(segments) - 1)
         Invariant(start <= end)
         Invariant(start <= i and i <= end)
         Invariant(len(result) == i - start)
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < len(result),
                     result[k] == segments[start + k])))
-        Invariant(MustTerminate(end - i + 1))
-        # invariants-end
         result.append(segments[i])
         i = i + 1
     return result
```

Attack 2 — `atk_2_boundary_start.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # At least the two end-most separators exist (a divided scale always has
     # the two extreme boundaries among its candidate separators).
     Requires(len(segments) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segments), 1 / 2))
@@ -89,7 +87,8 @@
                 Result()[k] == segments[start_index(lower_open) + k])))
     # post-conditions-end
     # impl-start
-    start = 0 if lower_open else 1
+    # WRONG: start offset inverted (1 when lower_open, else 0)
+    start = 1 if lower_open else 0
     end = len(segments) if upper_open else len(segments) - 1
     result = []  # type: List[int]
     i = start
@@ -107,7 +106,6 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < len(result),
                     result[k] == segments[start + k])))
-        Invariant(MustTerminate(end - i + 1))
         # invariants-end
         result.append(segments[i])
         i = i + 1
```

Attack 3 — `atk_3_boundary_end.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # At least the two end-most separators exist (a divided scale always has
     # the two extreme boundaries among its candidate separators).
     Requires(len(segments) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segments), 1 / 2))
@@ -89,8 +87,9 @@
                 Result()[k] == segments[start_index(lower_open) + k])))
     # post-conditions-end
     # impl-start
+    # WRONG: always keep the end-most upper separator regardless of upper_open
     start = 0 if lower_open else 1
-    end = len(segments) if upper_open else len(segments) - 1
+    end = len(segments)
     result = []  # type: List[int]
     i = start
     while i < end:
@@ -107,7 +106,6 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < len(result),
                     result[k] == segments[start + k])))
-        Invariant(MustTerminate(end - i + 1))
         # invariants-end
         result.append(segments[i])
         i = i + 1
```

Attack 4 — `atk_4_partial_n2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # At least the two end-most separators exist (a divided scale always has
     # the two extreme boundaries among its candidate separators).
     Requires(len(segments) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segments), 1 / 2))
@@ -89,6 +87,11 @@
                 Result()[k] == segments[start_index(lower_open) + k])))
     # post-conditions-end
     # impl-start
+    # WRONG: partial-domain — returns empty for the minimal 2-row mesh,
+    # gold behaviour otherwise.
+    if len(segments) == 2:
+        empty = []  # type: List[int]
+        return empty
     start = 0 if lower_open else 1
     end = len(segments) if upper_open else len(segments) - 1
     result = []  # type: List[int]
@@ -107,7 +110,6 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < len(result),
                     result[k] == segments[start + k])))
-        Invariant(MustTerminate(end - i + 1))
         # invariants-end
         result.append(segments[i])
         i = i + 1
```

Attack 5 — `atk_5_cfe_stride.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # At least the two end-most separators exist (a divided scale always has
     # the two extreme boundaries among its candidate separators).
     Requires(len(segments) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segments), 1 / 2))
@@ -89,12 +87,12 @@
                 Result()[k] == segments[start_index(lower_open) + k])))
     # post-conditions-end
     # impl-start
+    # WRONG: control-flow effect — advances by 2, dropping alternate separators
     start = 0 if lower_open else 1
     end = len(segments) if upper_open else len(segments) - 1
     result = []  # type: List[int]
     i = start
     while i < end:
-        # invariants-start
         Invariant(Acc(list_pred(segments), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(start == start_index(lower_open))
@@ -102,14 +100,8 @@
         Invariant(0 <= start and start <= 1)
         Invariant(end == len(segments) or end == len(segments) - 1)
         Invariant(start <= end)
-        Invariant(start <= i and i <= end)
-        Invariant(len(result) == i - start)
-        Invariant(Forall(int, lambda k:
-            Implies(0 <= k and k < len(result),
-                    result[k] == segments[start + k])))
-        Invariant(MustTerminate(end - i + 1))
-        # invariants-end
+        Invariant(start <= i)
         result.append(segments[i])
-        i = i + 1
+        i = i + 2
     return result
     # impl-end
```

Attack 6 — `atk_6_cfe_droplast.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # At least the two end-most separators exist (a divided scale always has
     # the two extreme boundaries among its candidate separators).
     Requires(len(segments) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segments), 1 / 2))
@@ -89,26 +87,21 @@
                 Result()[k] == segments[start_index(lower_open) + k])))
     # post-conditions-end
     # impl-start
+    # WRONG: stops one short — drops the last element of the kept run
     start = 0 if lower_open else 1
-    end = len(segments) if upper_open else len(segments) - 1
+    end = (len(segments) if upper_open else len(segments) - 1) - 1
     result = []  # type: List[int]
     i = start
     while i < end:
-        # invariants-start
         Invariant(Acc(list_pred(segments), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(start == start_index(lower_open))
-        Invariant(end == end_index(upper_open, len(segments)))
         Invariant(0 <= start and start <= 1)
-        Invariant(end == len(segments) or end == len(segments) - 1)
-        Invariant(start <= end)
         Invariant(start <= i and i <= end)
         Invariant(len(result) == i - start)
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < len(result),
                     result[k] == segments[start + k])))
-        Invariant(MustTerminate(end - i + 1))
-        # invariants-end
         result.append(segments[i])
         i = i + 1
     return result
```

Attack 7 — `atk_7_echo_helpers.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # At least the two end-most separators exist (a divided scale always has
     # the two extreme boundaries among its candidate separators).
     Requires(len(segments) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segments), 1 / 2))
@@ -89,8 +87,9 @@
                 Result()[k] == segments[start_index(lower_open) + k])))
     # post-conditions-end
     # impl-start
-    start = 0 if lower_open else 1
-    end = len(segments) if upper_open else len(segments) - 1
+    # ECHO: behaviourally identical to gold, written via the @Pure helpers
+    start = start_index(lower_open)
+    end = end_index(upper_open, len(segments))
     result = []  # type: List[int]
     i = start
     while i < end:
@@ -107,7 +106,6 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < len(result),
                     result[k] == segments[start + k])))
-        Invariant(MustTerminate(end - i + 1))
         # invariants-end
         result.append(segments[i])
         i = i + 1
```

Attack 8 — `atk_8_echo_index.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
     # At least the two end-most separators exist (a divided scale always has
     # the two extreme boundaries among its candidate separators).
     Requires(len(segments) >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(segments), 1 / 2))
@@ -89,6 +87,7 @@
                 Result()[k] == segments[start_index(lower_open) + k])))
     # post-conditions-end
     # impl-start
+    # ECHO #2: gold-equivalent; appends segments[start + len(result)] instead of segments[i]
     start = 0 if lower_open else 1
     end = len(segments) if upper_open else len(segments) - 1
     result = []  # type: List[int]
@@ -107,9 +106,8 @@
         Invariant(Forall(int, lambda k:
             Implies(0 <= k and k < len(result),
                     result[k] == segments[start + k])))
-        Invariant(MustTerminate(end - i + 1))
         # invariants-end
-        result.append(segments[i])
+        result.append(segments[start + len(result)])
         i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-22865.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A colour scale is divided into a sequence of coloured cells separated by
  boundary separators.  The full set of candidate separators is an ordered
  list, one separator per internal mesh row, indexed 0 .. n-1; the two
  end-most separators (index 0 and index n-1) coincide with the two extreme
  limits of the scale.

  Either extreme limit may be "open ended": when a limit is open ended the
  scale grows a triangular/rectangular cap beyond that limit, and the end-most
  separator on that side is part of the cap rather than a real cell boundary,
  so it must be omitted.  When a limit is NOT open ended the end-most separator
  on that side is a genuine cell boundary at the very edge of the scale and
  must be kept.

  The desired behaviour is therefore: the drawn separators are the contiguous
  run of candidate separators that starts at index 0 when the lower limit is
  open ended and at index 1 otherwise, and ends at index n (inclusive of the
  last separator) when the upper limit is open ended and at index n-1
  otherwise.  In particular when BOTH limits are open ended every candidate
  separator is drawn; when NEITHER is, both end-most separators are dropped.

Separators are modelled as a `List[int]` whose elements are the distinct
positions of the candidate separators along the scale (each separator is fully
identified by its position).  The result is the kept sub-run, also a
`List[int]`.  The lower/upper open-ended states are two booleans.  The
discriminating clause pins each kept element to the candidate at the
position-shifted index, with the start/end offsets driven by the two booleans.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms — the changed slice-bound selection is modeled deeply
#  below; the unchanged open-ended-limit predicates appear only as the two
#  boolean inputs.  See refinement.md / mapping.md for the A-reference checked
#  by axiom_check.py.)
# axioms-end


# pure-start
@Pure
def start_index(lower_open: bool) -> int:
    """First candidate-separator index that is drawn: index 0 when the lower
    limit is open ended (its end-most separator is a real boundary that the cap
    must not hide), otherwise index 1 (the end-most lower separator belongs to
    the lower cap and is dropped)."""
    if lower_open:
        return 0
    return 1


@Pure
def end_index(upper_open: bool, n: int) -> int:
    """One past the last drawn candidate-separator index: n (keep the end-most
    upper separator) when the upper limit is open ended, otherwise n-1 (the
    end-most upper separator belongs to the upper cap and is dropped)."""
    if upper_open:
        return n
    return n - 1
# pure-end


def drawn_separators(segments: List[int], lower_open: bool,
                     upper_open: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(segments), 1 / 2))
    # At least the two end-most separators exist (a divided scale always has
    # the two extreme boundaries among its candidate separators).
    Requires(len(segments) >= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(segments), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The kept run is exactly segments[start:end] with the start/end offsets
    # selected by the two open-ended-limit booleans.
    Ensures(len(Result()) ==
            end_index(upper_open, len(segments)) -
            start_index(lower_open))
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()),
                Result()[k] == segments[start_index(lower_open) + k])))
    # post-conditions-end
    # impl-start
    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start
    while i < end:
        # invariants-start
        Invariant(Acc(list_pred(segments), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(start == start_index(lower_open))
        Invariant(end == end_index(upper_open, len(segments)))
        Invariant(0 <= start and start <= 1)
        Invariant(end == len(segments) or end == len(segments) - 1)
        Invariant(start <= end)
        Invariant(start <= i and i <= end)
        Invariant(len(result) == i - start)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < len(result),
                    result[k] == segments[start + k])))
        # invariants-end
        result.append(segments[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for matplotlib__matplotlib-22865 (nagini). All work done there; only impl region edited, spec/axioms/@Pure/Requires/Ensures byte-identical (adversary same-spec exit 0 on all 8 + positive control).

SPEC ANALYSIS: The postcondition pins Result() UNIQUELY over the entire Requires domain (len>=2): both the LENGTH clause (len(Result())==end_index(upper_open,n)-start_index(lower_open)) and the ELEMENT clause (Result()[k]==segments[start_index(lower_open)+k] for all valid k). Any verifying impl therefore computes exactly segments[start_index:end_index] on every reachable input. So the only verifying variants are behaviourally gold-equivalent (echoes), and every genuinely-wrong impl must fail to verify.

atk_1_prepatch.py (prepatch bug: unconditional segments[1:n-1]) -> EXIT 2 NOT-A-COUNTEREXAMPLE (verification failed). PREPATCH REPRODUCED as fail. This is exactly the G-DIFF witness: for extend='both' spec demands length n, prepatch yields n-2.
- atk_2_boundary_start.py (boundary: start offset inverted, 1 if lower_open else 0) -> EXIT 2 rejected.
- atk_3_boundary_end.py (boundary: end always len(segments), never drop last) -> EXIT 2 rejected.
- atk_4_partial_n2.py (partial-domain: returns [] for n==2, gold otherwise) -> EXIT 2 rejected.
- atk_5_cfe_stride.py (control-flow-effect: i+=2, drops alternate separators) -> EXIT 2 rejected.
- atk_6_cfe_droplast.py (control-flow-effect: stops one short, drops last kept element) -> EXIT 2 rejected.
- atk_7_echo_helpers.py (ungrounded-oracle echo: gold-equivalent via start_index/end_index helpers) -> EXIT 0 CANDIDATE (same-spec AND verifies).
- atk_8_echo_index.py (echo #2: gold-equivalent, appends segments[start+len(result)]) -> EXIT 0 CANDIDATE.

6/8 wrong impls (prepatch + 2 boundary + 1 partial-domain + 2 control-flow-effect) were REJECTED by the verifier — the spec is tight. 2/8 are gold-equivalent echoes (CANDIDATEs).

MANDATORY RESOLVE ON CANDIDATES: Both echoes are behaviourally identical to gold (compute segments[start_index:end_index] with the gold offsets), so their faithful refined patch IS the gold hunk. Materialized to faithful_atk_7.diff / faithful_atk_8.diff (identical text) and RUN through the official harness: `run_resolve('matplotlib__matplotlib-22865', <faithful patch>, run_id='sbu-audit-eq-echo-22865')`. RESULT: resolved=true. Report at experiments/logs/run_evaluation/sbu-audit-eq-echo-22865-2ba33c9c70-p3563623/sbu_patch/matplotlib__matplotlib-22865/report.json: FAIL_TO_PASS all 3 pass (test_colorbar_extend_drawedges[both/min/max]), PASS_TO_PASS all pass, zero failures. Both verifying candidates' faithful patches RESOLVE => verify=>correct holds; NOT a break.

POSITIVE CONTROL: pos_control.py (verbatim model.py) verifies via scripts/nagini_verify.sh, exit 0, 12.5s.

A-LEG / refinement.md AUDIT: legs tagged R (A1 List[int]<->np.dstack first-axis; A2/A3 unchanged _extend_lower/_extend_upper predicates as bool inputs; A7 set_segments/get_segments identity), I (A4 identical conditional), A-reference (A5 -1-vs-n-1 upper bound; A6 copy-loop<->basic slice). No kind-3 legs; no @ContractOnly consumed axiom shipped (correct — none exists; the changed slice-bound selection is modeled DEEPLY via start_index/end_index + verified copy loop). A5 normalization sound: Requires len>=2 => n>=2 => arr[s:-1]===arr[s:n-1] on every reachable input incl. n=2 boundary. axiom_check.py (G-AX) RUN: exit 0 (4 canonical + 56 exhaustive-small + 20000 fuzz configs, deep model == real np.dstack[start_idx:end_idx]). Correspondence to real callees holds.

VERDICT: SOUND. >=5 distinct wrong impls run (6 rejected across prepatch/boundary/partial-domain/control-flow-effect classes); both verifying candidates are gold-equivalent echoes whose materialized faithful patches were executed through run_resolve and RESOLVE. No verifying wrong impl whose faithful patch fails to resolve exists. Spec is neither too weak (rejects all wrong impls) nor drifted; A-references machine-validated.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.py`, `atk_2_boundary_start.py`, `atk_3_boundary_end.py`, `atk_4_partial_n2.py`, `atk_5_cfe_stride.py`, `atk_6_cfe_droplast.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7_echo_helpers.py`, `atk_8_echo_index.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_boundary_start.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary_end.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_partial_n2.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_cfe_stride.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_cfe_droplast.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_echo_helpers.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_echo_index.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-22865.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A colour scale is divided into a sequence of coloured cells separated by
  boundary separators.  The full set of candidate separators is an ordered
  list, one separator per internal mesh row, indexed 0 .. n-1; the two
  end-most separators (index 0 and index n-1) coincide with the two extreme
  limits of the scale.

  Either extreme limit may be "open ended": when a limit is open ended the
  scale grows a triangular/rectangular cap beyond that limit, and the end-most
  separator on that side is part of the cap rather than a real cell boundary,
  so it must be omitted.  When a limit is NOT open ended the end-most separator
  on that side is a genuine cell boundary at the very edge of the scale and
  must be kept.

  The desired behaviour is therefore: the drawn separators are the contiguous
  run of candidate separators that starts at index 0 when the lower limit is
  open ended and at index 1 otherwise, and ends at index n (inclusive of the
  last separator) when the upper limit is open ended and at index n-1
  otherwise.  In particular when BOTH limits are open ended every candidate
  separator is drawn; when NEITHER is, both end-most separators are dropped.

Separators are modelled as a `List[int]` whose elements are the distinct
positions of the candidate separators along the scale (each separator is fully
identified by its position).  The result is the kept sub-run, also a
`List[int]`.  The lower/upper open-ended states are two booleans.  The
discriminating clause pins each kept element to the candidate at the
position-shifted index, with the start/end offsets driven by the two booleans.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms — the changed slice-bound selection is modeled deeply
#  below; the unchanged open-ended-limit predicates appear only as the two
#  boolean inputs.  See refinement.md / mapping.md for the A-reference checked
#  by axiom_check.py.)
# axioms-end


# pure-start
@Pure
def start_index(lower_open: bool) -> int:
    """First candidate-separator index that is drawn: index 0 when the lower
    limit is open ended (its end-most separator is a real boundary that the cap
    must not hide), otherwise index 1 (the end-most lower separator belongs to
    the lower cap and is dropped)."""
    if lower_open:
        return 0
    return 1


@Pure
def end_index(upper_open: bool, n: int) -> int:
    """One past the last drawn candidate-separator index: n (keep the end-most
    upper separator) when the upper limit is open ended, otherwise n-1 (the
    end-most upper separator belongs to the upper cap and is dropped)."""
    if upper_open:
        return n
    return n - 1
# pure-end


def drawn_separators(segments: List[int], lower_open: bool,
                     upper_open: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(segments), 1 / 2))
    # At least the two end-most separators exist (a divided scale always has
    # the two extreme boundaries among its candidate separators).
    Requires(len(segments) >= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(segments), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The kept run is exactly segments[start:end] with the start/end offsets
    # selected by the two open-ended-limit booleans.
    Ensures(len(Result()) ==
            end_index(upper_open, len(segments)) -
            start_index(lower_open))
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()),
                Result()[k] == segments[start_index(lower_open) + k])))
    # post-conditions-end
    # impl-start
    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start
    while i < end:
        # invariants-start
        Invariant(Acc(list_pred(segments), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(start == start_index(lower_open))
        Invariant(end == end_index(upper_open, len(segments)))
        Invariant(0 <= start and start <= 1)
        Invariant(end == len(segments) or end == len(segments) - 1)
        Invariant(start <= end)
        Invariant(start <= i and i <= end)
        Invariant(len(result) == i - start)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < len(result),
                    result[k] == segments[start + k])))
        # invariants-end
        result.append(segments[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for matplotlib__matplotlib-22865 (nagini). All work done there; only impl region edited, spec/axioms/@Pure/Requires/Ensures byte-identical (adversary same-spec exit 0 on all 8 + positive control).

SPEC ANALYSIS: The postcondition pins Result() UNIQUELY over the entire Requires domain (len>=2): both the LENGTH clause (len(Result())==end_index(upper_open,n)-start_index(lower_open)) and the ELEMENT clause (Result()[k]==segments[start_index(lower_open)+k] for all valid k). Any verifying impl therefore computes exactly segments[start_index:end_index] on every reachable input. So the only verifying variants are behaviourally gold-equivalent (echoes), and every genuinely-wrong impl must fail to verify.

atk_1_prepatch.py (prepatch bug: unconditional segments[1:n-1]) -> EXIT 2 NOT-A-COUNTEREXAMPLE (verification failed). PREPATCH REPRODUCED as fail. This is exactly the G-DIFF witness: for extend='both' spec demands length n, prepatch yields n-2.
- atk_2_boundary_start.py (boundary: start offset inverted, 1 if lower_open else 0) -> EXIT 2 rejected.
- atk_3_boundary_end.py (boundary: end always len(segments), never drop last) -> EXIT 2 rejected.
- atk_4_partial_n2.py (partial-domain: returns [] for n==2, gold otherwise) -> EXIT 2 rejected.
- atk_5_cfe_stride.py (control-flow-effect: i+=2, drops alternate separators) -> EXIT 2 rejected.
- atk_6_cfe_droplast.py (control-flow-effect: stops one short, drops last kept element) -> EXIT 2 rejected.
- atk_7_echo_helpers.py (ungrounded-oracle echo: gold-equivalent via start_index/end_index helpers) -> EXIT 0 CANDIDATE (same-spec AND verifies).
- atk_8_echo_index.py (echo #2: gold-equivalent, appends segments[start+len(result)]) -> EXIT 0 CANDIDATE.

6/8 wrong impls (prepatch + 2 boundary + 1 partial-domain + 2 control-flow-effect) were REJECTED by the verifier — the spec is tight. 2/8 are gold-equivalent echoes (CANDIDATEs).

MANDATORY RESOLVE ON CANDIDATES: Both echoes are behaviourally identical to gold (compute segments[start_index:end_index] with the gold offsets), so their faithful refined patch IS the gold hunk. Materialized to faithful_atk_7.diff / faithful_atk_8.diff (identical text) and RUN through the official harness: `run_resolve('matplotlib__matplotlib-22865', <faithful patch>, run_id='sbu-audit-eq-echo-22865')`. RESULT: resolved=true. Report at experiments/logs/run_evaluation/sbu-audit-eq-echo-22865-2ba33c9c70-p3563623/sbu_patch/matplotlib__matplotlib-22865/report.json: FAIL_TO_PASS all 3 pass (test_colorbar_extend_drawedges[both/min/max]), PASS_TO_PASS all pass, zero failures. Both verifying candidates' faithful patches RESOLVE => verify=>correct holds; NOT a break.

POSITIVE CONTROL: pos_control.py (verbatim model.py) verifies via scripts/nagini_verify.sh, exit 0, 12.5s.

A-LEG / refinement.md AUDIT: legs tagged R (A1 List[int]<->np.dstack first-axis; A2/A3 unchanged _extend_lower/_extend_upper predicates as bool inputs; A7 set_segments/get_segments identity), I (A4 identical conditional), A-reference (A5 -1-vs-n-1 upper bound; A6 copy-loop<->basic slice). No kind-3 legs; no @ContractOnly consumed axiom shipped (correct — none exists; the changed slice-bound selection is modeled DEEPLY via start_index/end_index + verified copy loop). A5 normalization sound: Requires len>=2 => n>=2 => arr[s:-1]===arr[s:n-1] on every reachable input incl. n=2 boundary. axiom_check.py (G-AX) RUN: exit 0 (4 canonical + 56 exhaustive-small + 20000 fuzz configs, deep model == real np.dstack[start_idx:end_idx]). Correspondence to real callees holds.

VERDICT: SOUND. >=5 distinct wrong impls run (6 rejected across prepatch/boundary/partial-domain/control-flow-effect classes); both verifying candidates are gold-equivalent echoes whose materialized faithful patches were executed through run_resolve and RESOLVE. No verifying wrong impl whose faithful patch fails to resolve exists. Spec is neither too weak (rejects all wrong impls) nor drifted; A-references machine-validated.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for matplotlib__matplotlib-22865 nagini bundle. The bundle models the real gold patch to Colorbar._add_solids (colorbar.py): the divider-segment slice bounds become start_idx = 0 if _extend_lower() else 1, end_idx = len(X) if _extend_upper() else -1, kept = np.dstack([X,Y])[start_idx:end_idx]. Confirmed the bundle's spec corresponds to the actual dataset gold patch (base c6c7ec19). model.py verifies under pinned Nagini (12.66s). 

I independently (not trusting the bundle's own axiom_check) reimplemented the exact real patched slicing (real numpy basic first-axis slicing with literal end_idx=-1) and compared it element-for-element to the model's postcondition-defined function drawn_separators = segments[start_index(lower_open):end_index(upper_open,n)] with start_index=0/1 and end_index=n/(n-1). Across n=1..60 and all four (lower_open,upper_open) boolean pairs: 0 divergences. In particular the one nontrivial refinement step — the model normalising the real code's literal -1 upper bound to n-1 — is exact: for any array length n, arr[start:-1] == arr[start:n-1] (both drop exactly the last row). Precondition is len(segments)>=2; no divergence even below it. The bundle's axiom_check.py independently agrees (4 canonical + 56 small-exhaustive + 20000 fuzz, exit 0). 

The spec is not too strong and does not drift: the modeled function agrees with the real callee on every input in the domain. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, zero hard failures). Semantic review of the spec view (spec_view over model.py: docstring + imports + axioms/pure regions + signature/pre/post of drawn_separators, impl elided) confirms no leakage of the gold edit beyond the public problem_statement.

Public problem_statement already discloses: colorbar, drawedges=True, extend='both', edges at the extremities missing (i.e. should be drawn).

Gold edit (lib/matplotlib/colorbar.py, _add_solids): replace unconditional np.dstack([X,Y])[1:-1] with conditional slice [start_idx:end_idx], start_idx = 0 if self._extend_lower() else 1, end_idx = len(X) if self._extend_upper() else -1.

Spec-view findings:
- No diff markers; no patched file path 'lib/matplotlib/colorbar.py'; no module path; no [1:-1]/[start_idx:end_idx] slice literal; no np.dstack / set_segments / _extend_lower / _extend_upper tokens. Those repo-specific details live ONLY in mapping.md, refinement.md, axiom_check.py — which are audit artifacts, NOT the consumer spec view a solver works against.
- Only distinctive patched def/class symbol is 'add_solids' (from _add_solids); the spec uses abstract names drawn_separators / start_index / end_index / lower_open / upper_open, none embedding it. No L2/L5 identifier collision, no L2/L3 comment naming.
- No bug/fix narration; the docstring explicitly frames everything as 'desired behaviour, not as an edit'.

The spec necessarily encodes the correct target behaviour (start 0/1, end n/(n-1) driven by two booleans; full run when both open-ended), but that is the legitimate behavioral contract any spec must state, expressed in abstract separators/open-ended-limit vocabulary with no repo localization. A consumer reading the spec view cannot recover the file, function, or numpy-slicing mechanism to edit. Boundary G-PANEL-3 protects holds.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
