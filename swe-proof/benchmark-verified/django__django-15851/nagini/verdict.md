# P2 adversarial audit — django__django-15851

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch.py`, `atk_3_order.py`, `atk_4_partial.py`, `atk_5_boundary.py`, `atk_6_extra.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(parameters), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -72,12 +70,15 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(prefix))
         Invariant(ToSeq(result) == ToSeq(prefix).take(i))
-        Invariant(MustTerminate(len(prefix) - i + 1))
         # invariants-end
         result.append(prefix[i])
         Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
         i = i + 1
     Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
+    # PRE-PATCH BUG: the database-name token is appended BEFORE the extra
+    # arguments, so the extras follow the database name and are ignored.
+    if has_dbname:
+        result.append(dbname)
     j = 0
     while j < len(parameters):
         # invariants-start
@@ -85,15 +86,15 @@
         Invariant(Acc(list_pred(parameters), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(parameters))
-        Invariant(ToSeq(result) == ToSeq(prefix) + ToSeq(parameters).take(j))
-        Invariant(MustTerminate(len(parameters) - j + 1))
+        Invariant(ToSeq(result)
+                  == ToSeq(prefix)
+                  + (PSeq(dbname) if has_dbname else PSeq(dbname).take(0))
+                  + ToSeq(parameters).take(j))
         # invariants-end
         result.append(parameters[j])
         Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
                == ToSeq(parameters).take(j + 1))
         j = j + 1
     Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
-    if has_dbname:
-        result.append(dbname)
     return result
     # impl-end
```

Attack 2 — `atk_3_order.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(parameters), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -64,36 +62,27 @@
                     ToSeq(Result()) == ToSeq(prefix) + ToSeq(parameters)))
     # post-conditions-end
     # impl-start
+
     result = []  # type: List[int]
     i = 0
     while i < len(prefix):
-        # invariants-start
         Invariant(Acc(list_pred(prefix), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(prefix))
         Invariant(ToSeq(result) == ToSeq(prefix).take(i))
-        Invariant(MustTerminate(len(prefix) - i + 1))
-        # invariants-end
         result.append(prefix[i])
         Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
         i = i + 1
     Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
+    if has_dbname:
+        result.append(dbname)
     j = 0
     while j < len(parameters):
-        # invariants-start
         Invariant(Acc(list_pred(prefix), 1 / 2))
         Invariant(Acc(list_pred(parameters), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(parameters))
-        Invariant(ToSeq(result) == ToSeq(prefix) + ToSeq(parameters).take(j))
-        Invariant(MustTerminate(len(parameters) - j + 1))
-        # invariants-end
         result.append(parameters[j])
-        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
-               == ToSeq(parameters).take(j + 1))
         j = j + 1
-    Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
-    if has_dbname:
-        result.append(dbname)
     return result
     # impl-end
```

Attack 3 — `atk_4_partial.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(parameters), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -64,35 +62,18 @@
                     ToSeq(Result()) == ToSeq(prefix) + ToSeq(parameters)))
     # post-conditions-end
     # impl-start
+
     result = []  # type: List[int]
     i = 0
     while i < len(prefix):
-        # invariants-start
         Invariant(Acc(list_pred(prefix), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(prefix))
         Invariant(ToSeq(result) == ToSeq(prefix).take(i))
-        Invariant(MustTerminate(len(prefix) - i + 1))
-        # invariants-end
         result.append(prefix[i])
         Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
         i = i + 1
     Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
-    j = 0
-    while j < len(parameters):
-        # invariants-start
-        Invariant(Acc(list_pred(prefix), 1 / 2))
-        Invariant(Acc(list_pred(parameters), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(parameters))
-        Invariant(ToSeq(result) == ToSeq(prefix) + ToSeq(parameters).take(j))
-        Invariant(MustTerminate(len(parameters) - j + 1))
-        # invariants-end
-        result.append(parameters[j])
-        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
-               == ToSeq(parameters).take(j + 1))
-        j = j + 1
-    Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
     if has_dbname:
         result.append(dbname)
     return result
```

Attack 4 — `atk_5_boundary.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(parameters), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -64,35 +62,26 @@
                     ToSeq(Result()) == ToSeq(prefix) + ToSeq(parameters)))
     # post-conditions-end
     # impl-start
+
     result = []  # type: List[int]
     i = 0
     while i < len(prefix):
-        # invariants-start
         Invariant(Acc(list_pred(prefix), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(prefix))
         Invariant(ToSeq(result) == ToSeq(prefix).take(i))
-        Invariant(MustTerminate(len(prefix) - i + 1))
-        # invariants-end
         result.append(prefix[i])
         Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
         i = i + 1
     Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
     j = 0
-    while j < len(parameters):
-        # invariants-start
+    while j < len(parameters) - 1:
         Invariant(Acc(list_pred(prefix), 1 / 2))
         Invariant(Acc(list_pred(parameters), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(parameters))
-        Invariant(ToSeq(result) == ToSeq(prefix) + ToSeq(parameters).take(j))
-        Invariant(MustTerminate(len(parameters) - j + 1))
-        # invariants-end
         result.append(parameters[j])
-        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
-               == ToSeq(parameters).take(j + 1))
         j = j + 1
-    Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
     if has_dbname:
         result.append(dbname)
     return result
```

Attack 5 — `atk_6_extra.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -48,7 +47,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(prefix), 1 / 2))
     Requires(Acc(list_pred(parameters), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -64,36 +62,29 @@
                     ToSeq(Result()) == ToSeq(prefix) + ToSeq(parameters)))
     # post-conditions-end
     # impl-start
+
     result = []  # type: List[int]
     i = 0
     while i < len(prefix):
-        # invariants-start
         Invariant(Acc(list_pred(prefix), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(prefix))
         Invariant(ToSeq(result) == ToSeq(prefix).take(i))
-        Invariant(MustTerminate(len(prefix) - i + 1))
-        # invariants-end
         result.append(prefix[i])
         Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
         i = i + 1
     Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
     j = 0
     while j < len(parameters):
-        # invariants-start
         Invariant(Acc(list_pred(prefix), 1 / 2))
         Invariant(Acc(list_pred(parameters), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(parameters))
         Invariant(ToSeq(result) == ToSeq(prefix) + ToSeq(parameters).take(j))
-        Invariant(MustTerminate(len(parameters) - j + 1))
-        # invariants-end
         result.append(parameters[j])
-        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
-               == ToSeq(parameters).take(j + 1))
+        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j]) == ToSeq(parameters).take(j + 1))
         j = j + 1
     Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
-    if has_dbname:
-        result.append(dbname)
+    result.append(dbname)
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15851.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An interactive database-shell invocation is assembled as an ordered argument
  vector for the client program. The vector is built in three ordered segments:

    (1) a leading segment of connection flags (program name plus any
        user / host / port options), assembled first;
    (2) the caller-supplied extra arguments, passed through verbatim and in
        order;
    (3) the target database name, when one is in effect, as a single trailing
        token.

  The required ordering is segment (1), then (2), then (3): every caller-supplied
  extra argument precedes the database-name token, because the client program
  treats only the arguments that come before the database name as options and
  silently ignores anything that follows it. When no database name is in effect,
  the vector is just segment (1) followed by segment (2).

Argument tokens are modelled as `List[int]` of opaque token identities (Nagini
bans `str` indexing); the specification is carried by `PSeq[int]` via `ToSeq`.
The leading flag segment and the extra arguments are read-only inputs; the
result vector is freshly constructed. There are no axiomatized callees: the
operation is pure list construction.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none — the modelled behaviour is pure list construction; no library callee
# is invoked by the changed operation.)
# axioms-end

# pure-start
# (no pure specification helpers needed; ordering is expressed directly with
# PSeq concatenation in the postconditions.)
# pure-end

def build_argv(prefix: List[int], parameters: List[int],
               has_dbname: bool, dbname: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(prefix), 1 / 2))
    Requires(Acc(list_pred(parameters), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prefix), 1 / 2))
    Ensures(Acc(list_pred(parameters), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the flag segment, then the extra arguments, then the
    # database-name token when one is in effect. Every extra argument precedes
    # the database-name token.
    Ensures(Implies(has_dbname,
                    ToSeq(Result())
                    == ToSeq(prefix) + ToSeq(parameters) + PSeq(dbname)))
    Ensures(Implies(not has_dbname,
                    ToSeq(Result()) == ToSeq(prefix) + ToSeq(parameters)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(prefix):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(prefix))
        Invariant(ToSeq(result) == ToSeq(prefix).take(i))
        # invariants-end
        result.append(prefix[i])
        Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
        i = i + 1
    Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
    j = 0
    while j < len(parameters):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(parameters), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(parameters))
        Invariant(ToSeq(result) == ToSeq(prefix) + ToSeq(parameters).take(j))
        # invariants-end
        result.append(parameters[j])
        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
               == ToSeq(parameters).take(j + 1))
        j = j + 1
    Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
    if has_dbname:
        result.append(dbname)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. build_argv's spec is a COMPLETE, TOTAL functional specification: Ensures(Implies(has_dbname, ToSeq(Result())==ToSeq(prefix)+ToSeq(parameters)+PSeq(dbname))) and Ensures(Implies(not has_dbname, ToSeq(Result())==ToSeq(prefix)+ToSeq(parameters))) pin the full result sequence in BOTH branches of has_dbname; Ensures(Acc(list_pred(Result()))) gives full ownership; inputs are read-only (1/2 permission). meta.json has axioms=[] and deep_model_references=[] — no A-legs to break, no @Pure/ungrounded oracle to echo. All legs R/I (refinement.md sections A-C: A1-A6 all R or I; section C confirms no kind-3; no axiom_check.py, G-AX vacuous). refinement.md/mapping.md correspondence audited and confirmed: prefix=args as built by [executable]+optional -U/-h/-p; parameters=the parameters arg; (has_dbname,dbname)=`if dbname:` guard + settings_dict.get('NAME') defaulted to 'postgres'; env/tuple omitted (unchanged by patch). Verified against the frozen gold patch (client.py: `args.extend(parameters)` moved BEFORE `if dbname: args += [dbname]`).

BATTERY (7 attacks, all same-spec exit 0). Command form: `python -m swebench_unified.adversary weakness nagini django__django-15851 <path>`; direct verify: `bash scripts/nagini_verify.sh <path>`.
- atk_1_prepatch.py (prepatch bug: dbname appended before params loop) -> nagini_verify EXIT=1, weakness EXIT=2 REJECTED. Reproduces the prepatch bug; spec senses the change (G-DIFF holds).
- atk_3_order.py (params loop AFTER dbname append) -> EXIT=1 REJECTED.
- atk_4_partial.py (partial-domain: omit params loop entirely) -> EXIT=1 REJECTED.
- atk_5_boundary.py (off-by-one: params loop `while j < len(parameters)-1`) -> EXIT=1 REJECTED.
- atk_6_extra.py (control-flow-effect: append dbname unconditionally) -> EXIT=1 REJECTED.
Every TERMINATING deviation is rejected by the postcondition — the spec has zero functional freedom.

NON-TERMINATION CANDIDATES (partial-correctness artifact, investigated + resolve-run per protocol; NOT valid falsifications, so excluded from the submitted attack floor):
- atk_2_nonterm.py (`while True: result.append(0)`): same-spec exit0, nagini_verify EXIT=0, weakness EXIT=0 CANDIDATE.
- atk_7_nonterm2.py (spin loop `while i>=0: i=i+1`): same-spec exit0, nagini_verify EXIT=0, weakness EXIT=0 CANDIDATE.
Both verify only because Nagini uses PARTIAL correctness (no MustTerminate; quickref.md: 'Termination proofs are NOT required by default'; ~420/500 nagini bundles lack MustTerminate — this is a universal methodology choice, not a defect of THIS spec). MATERIALIZED FAITHFUL PATCH + RESOLVE (mandatory step, EXECUTED): patch_nonterm.diff inserts a divergent loop into DatabaseClient.settings_to_cmd_args_env before the dbname block (faithful refinement of the non-terminating model impl). Ran the real harness (`docker -c ... swebench_unified.run_evaluation ----instance_ids django__django-15851`). RESULT: 'django__django-15851: Test timed out after 180 seconds.

Instances resolved: 0 Instances unresolved: 0'; Evaluation error=1; NO per-instance report.json written => run_resolve returns completed=False. In _derive_audit_verdict this hits the INCONCLUSIVE-by-design branch (not r.completed), NOT the BROKEN condition (r.completed and not r.resolved). A non-terminating patch times out DETERMINISTICALLY and can therefore NEVER satisfy the BROKEN condition; moreover it applies identically to every partial-correctness bundle irrespective of spec fidelity, so it carries no information about this spec. It is not a valid G-EQ counterexample.

POSITIVE CONTROLS (executed): positive_control.py (= bundle model.py) verifies (nagini_verify EXIT=0). GOLD patch resolve run (real harness): report.json resolved=true, FAIL_TO_PASS test_parameters PASS + 8 PASS_TO_PASS pass — model<->patch correspondence exact (the earlier 'no report' from run_resolve was a make_run_report/list_images RACE with a concurrent nagini concurrent runs at load~300, not a patch failure; the per-instance report.json is written before that aggregation and shows resolved=true).

CONCLUSION: No terminating same-spec verifying impl produces wrong output; the two non-terminating candidates are an accepted partial-correctness property whose faithful patches time out (completed=False, inconclusive-by-design, structurally not-BROKEN). Refinement fidelity holds; A-leg audit vacuously correct (no axioms/deep refs). Verdict SOUND. (Falsification floor met: 5 submitted terminating attacks all rejected, prepatch reproduced, positive control verifies; patches={} since none of the 5 submitted attacks verify, so no resolve run is triggered in re-derivation.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch.py`, `atk_3_order.py`, `atk_4_partial.py`, `atk_5_boundary.py`, `atk_6_extra.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3_order.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4_partial.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5_boundary.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6_extra.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15851.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An interactive database-shell invocation is assembled as an ordered argument
  vector for the client program. The vector is built in three ordered segments:

    (1) a leading segment of connection flags (program name plus any
        user / host / port options), assembled first;
    (2) the caller-supplied extra arguments, passed through verbatim and in
        order;
    (3) the target database name, when one is in effect, as a single trailing
        token.

  The required ordering is segment (1), then (2), then (3): every caller-supplied
  extra argument precedes the database-name token, because the client program
  treats only the arguments that come before the database name as options and
  silently ignores anything that follows it. When no database name is in effect,
  the vector is just segment (1) followed by segment (2).

Argument tokens are modelled as `List[int]` of opaque token identities (Nagini
bans `str` indexing); the specification is carried by `PSeq[int]` via `ToSeq`.
The leading flag segment and the extra arguments are read-only inputs; the
result vector is freshly constructed. There are no axiomatized callees: the
operation is pure list construction.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none — the modelled behaviour is pure list construction; no library callee
# is invoked by the changed operation.)
# axioms-end

# pure-start
# (no pure specification helpers needed; ordering is expressed directly with
# PSeq concatenation in the postconditions.)
# pure-end

def build_argv(prefix: List[int], parameters: List[int],
               has_dbname: bool, dbname: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(prefix), 1 / 2))
    Requires(Acc(list_pred(parameters), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prefix), 1 / 2))
    Ensures(Acc(list_pred(parameters), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the flag segment, then the extra arguments, then the
    # database-name token when one is in effect. Every extra argument precedes
    # the database-name token.
    Ensures(Implies(has_dbname,
                    ToSeq(Result())
                    == ToSeq(prefix) + ToSeq(parameters) + PSeq(dbname)))
    Ensures(Implies(not has_dbname,
                    ToSeq(Result()) == ToSeq(prefix) + ToSeq(parameters)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(prefix):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(prefix))
        Invariant(ToSeq(result) == ToSeq(prefix).take(i))
        # invariants-end
        result.append(prefix[i])
        Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
        i = i + 1
    Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
    j = 0
    while j < len(parameters):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(parameters), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(parameters))
        Invariant(ToSeq(result) == ToSeq(prefix) + ToSeq(parameters).take(j))
        # invariants-end
        result.append(parameters[j])
        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
               == ToSeq(parameters).take(j + 1))
        j = j + 1
    Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
    if has_dbname:
        result.append(dbname)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. build_argv's spec is a COMPLETE, TOTAL functional specification: Ensures(Implies(has_dbname, ToSeq(Result())==ToSeq(prefix)+ToSeq(parameters)+PSeq(dbname))) and Ensures(Implies(not has_dbname, ToSeq(Result())==ToSeq(prefix)+ToSeq(parameters))) pin the full result sequence in BOTH branches of has_dbname; Ensures(Acc(list_pred(Result()))) gives full ownership; inputs are read-only (1/2 permission). meta.json has axioms=[] and deep_model_references=[] — no A-legs to break, no @Pure/ungrounded oracle to echo. All legs R/I (refinement.md sections A-C: A1-A6 all R or I; section C confirms no kind-3; no axiom_check.py, G-AX vacuous). refinement.md/mapping.md correspondence audited and confirmed: prefix=args as built by [executable]+optional -U/-h/-p; parameters=the parameters arg; (has_dbname,dbname)=`if dbname:` guard + settings_dict.get('NAME') defaulted to 'postgres'; env/tuple omitted (unchanged by patch). Verified against the frozen gold patch (client.py: `args.extend(parameters)` moved BEFORE `if dbname: args += [dbname]`).

BATTERY (7 attacks, all same-spec exit 0). Command form: `python -m swebench_unified.adversary weakness nagini django__django-15851 <path>`; direct verify: `bash scripts/nagini_verify.sh <path>`.
- atk_1_prepatch.py (prepatch bug: dbname appended before params loop) -> nagini_verify EXIT=1, weakness EXIT=2 REJECTED. Reproduces the prepatch bug; spec senses the change (G-DIFF holds).
- atk_3_order.py (params loop AFTER dbname append) -> EXIT=1 REJECTED.
- atk_4_partial.py (partial-domain: omit params loop entirely) -> EXIT=1 REJECTED.
- atk_5_boundary.py (off-by-one: params loop `while j < len(parameters)-1`) -> EXIT=1 REJECTED.
- atk_6_extra.py (control-flow-effect: append dbname unconditionally) -> EXIT=1 REJECTED.
Every TERMINATING deviation is rejected by the postcondition — the spec has zero functional freedom.

NON-TERMINATION CANDIDATES (partial-correctness artifact, investigated + resolve-run per protocol; NOT valid falsifications, so excluded from the submitted attack floor):
- atk_2_nonterm.py (`while True: result.append(0)`): same-spec exit0, nagini_verify EXIT=0, weakness EXIT=0 CANDIDATE.
- atk_7_nonterm2.py (spin loop `while i>=0: i=i+1`): same-spec exit0, nagini_verify EXIT=0, weakness EXIT=0 CANDIDATE.
Both verify only because Nagini uses PARTIAL correctness (no MustTerminate; quickref.md: 'Termination proofs are NOT required by default'; ~420/500 nagini bundles lack MustTerminate — this is a universal methodology choice, not a defect of THIS spec). MATERIALIZED FAITHFUL PATCH + RESOLVE (mandatory step, EXECUTED): patch_nonterm.diff inserts a divergent loop into DatabaseClient.settings_to_cmd_args_env before the dbname block (faithful refinement of the non-terminating model impl). Ran the real harness (`docker -c ... swebench_unified.run_evaluation ----instance_ids django__django-15851`). RESULT: 'django__django-15851: Test timed out after 180 seconds.

Instances resolved: 0 Instances unresolved: 0'; Evaluation error=1; NO per-instance report.json written => run_resolve returns completed=False. In _derive_audit_verdict this hits the INCONCLUSIVE-by-design branch (not r.completed), NOT the BROKEN condition (r.completed and not r.resolved). A non-terminating patch times out DETERMINISTICALLY and can therefore NEVER satisfy the BROKEN condition; moreover it applies identically to every partial-correctness bundle irrespective of spec fidelity, so it carries no information about this spec. It is not a valid G-EQ counterexample.

POSITIVE CONTROLS (executed): positive_control.py (= bundle model.py) verifies (nagini_verify EXIT=0). GOLD patch resolve run (real harness): report.json resolved=true, FAIL_TO_PASS test_parameters PASS + 8 PASS_TO_PASS pass — model<->patch correspondence exact (the earlier 'no report' from run_resolve was a make_run_report/list_images RACE with a concurrent nagini concurrent runs at load~300, not a patch failure; the per-instance report.json is written before that aggregation and shows resolved=true).

CONCLUSION: No terminating same-spec verifying impl produces wrong output; the two non-terminating candidates are an accepted partial-correctness property whose faithful patches time out (completed=False, inconclusive-by-design, structurally not-BROKEN). Refinement fidelity holds; A-leg audit vacuously correct (no axioms/deep refs). Verdict SOUND. (Falsification floor met: 5 submitted terminating attacks all rejected, prepatch reproduced, positive control verifies; patches={} since none of the 5 submitted attacks verify, so no resolve run is triggered in re-derivation.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check of the modeled build_argv against the real callee DatabaseClient.settings_to_cmd_args_env at base_commit b4817d20 (django/db/backends/postgresql/client.py). Model verifies under pinned Nagini (exit 0, 15.4s).

Real post-patch behavior: args = [psql] + optional [-U user]/[-h host]/[-p port] (prefix); then args.extend(parameters); then if dbname: args += [dbname]. So Result = prefix ++ parameters ++ ([dbname] if dbname else []). The dbname default (if not dbname and not service: dbname='postgres') and the `if dbname:` guard together decide whether a trailing name token appears.

Model abstraction is faithful on every input:
- prefix: read-only opaque sequence = the unchanged flag segment ([psql] + -U/-h/-p). Correct — the patch does not touch it.
- parameters: read-only, appended in order = args.extend(parameters). Correct.
- (has_dbname, dbname): folds the `if dbname:` guard truth value and its token; the default-to-'postgres' logic is subsumed since has_dbname ranges over both truth values. Both branches (name present / absent) are specified by the two Implies postconditions and match the real callee.
- Ordering pinned by postcondition ToSeq(Result)==ToSeq(prefix)+ToSeq(parameters)+PSeq(dbname) is exactly the post-patch order (parameters before dbname). Not too strong: it equals gold behavior, not a stronger guarantee.
- Omitted env dict / (args, env) tuple: env is built identically pre- and post-patch from the ssl/passfile/passwd blocks below the hunk and is untouched by the patch, so projecting it away introduces no divergence on the behavior under change.

Under the token bijection (str token <-> opaque int, tokens compared only by equality/position, matching list-equality tests), the modeled function agrees with the real callee on all inputs. No diverging input found. Spec is neither too strong nor drifting; model_prepatch correctly fails exactly the ordering postcondition (G-DIFF sensed). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen) passes clean: no hard failures, no warnings. Vectors checked individually: (L1) no diff markers, and the gold changed line 'args.extend(parameters)' does not appear in the spec view (impl region is elided to '...'); (L2) patched file path 'django/db/backends/postgresql/client.py' and patched symbol 'settings_to_cmd_args_env' are absent — the model uses generic identifiers (build_argv, prefix, parameters, dbname); (L3) no bug/fix/patch narration in comments/docstrings.

Semantic assessment vs the PUBLIC problem_statement (not hints): the spec's postconditions state the desired ordering flags -> parameters -> dbname (every caller-supplied extra argument precedes the database-name token; no dbname => flags then parameters). This ordering IS exactly what the public problem statement demands: the title says 'dbshell additional parameters should be passed before dbname on PostgreSQL', and the body states 'psql expects all options to proceed the database name... the args list just need to be constructed in the proper order, leaving the database name for the end of the args list.' The spec therefore reveals nothing about the gold edit beyond what the solver-visible task already specifies. It states desired behaviour, not the edit mechanics (i.e. it does not disclose that the fix is to move args.extend(parameters) above the dbname branch). same_spec/byte-identical spec region not disturbed (this is a leakage-only judgment).

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).