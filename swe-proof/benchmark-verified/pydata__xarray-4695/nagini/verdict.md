# P2 adversarial audit — pydata__xarray-4695

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_3b.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(Acc(list_pred(values), 1 / 2))
     Requires(len(names) == len(values))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -94,8 +92,9 @@
     Ensures(ToSeq(Result()) == ToSeq(names))
     # post-conditions-end
     # impl-start
-    # Forward the mapping positionally: every entry, including one whose name
-    # equals RESERVED_NAME, is kept as an axis selector.
+    # NAME-KEYED forwarding (pre-fix): an entry whose name equals RESERVED_NAME
+    # is diverted into the reserved option slot and therefore NOT forwarded as
+    # an axis selector. The forwarded axis sequence loses every colliding entry.
     forwarded = []  # type: List[int]
     i = 0
     while i < len(names):
@@ -105,12 +104,10 @@
         Invariant(len(names) == len(values))
         Invariant(Acc(list_pred(forwarded)))
         Invariant(0 <= i and i <= len(names))
-        Invariant(ToSeq(forwarded) == ToSeq(names).take(i))
-        Invariant(MustTerminate(len(names) - i + 1))
         # invariants-end
-        forwarded.append(names[i])
+        if names[i] != RESERVED_NAME():
+            forwarded.append(names[i])
         i = i + 1
-    Assert(ToSeq(names).take(len(names)) == ToSeq(names))
     return forwarded
     # impl-end
 
@@ -125,7 +122,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(values),
                                             values[k] >= 0),
                                     [[values[k]]])))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -136,7 +132,9 @@
     Ensures(Result() == DEFAULT_OPTION())
     # post-conditions-end
     # impl-start
-    # Positional forwarding: the reserved option is not fed from the mapping.
-    option = DEFAULT_OPTION()
+    # NAME-KEYED routing (pre-fix): a colliding axis is bound to the reserved
+    # option slot, so the reserved option takes that entry's value instead of
+    # its default.
+    option = option_after_namekeyed(ToSeq(names), ToSeq(values))
     return option
     # impl-end
```

Attack 2 — `atk_3b.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(Acc(list_pred(values), 1 / 2))
     Requires(len(names) == len(values))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -94,23 +92,8 @@
     Ensures(ToSeq(Result()) == ToSeq(names))
     # post-conditions-end
     # impl-start
-    # Forward the mapping positionally: every entry, including one whose name
-    # equals RESERVED_NAME, is kept as an axis selector.
+    # ungrounded oracle: assume False, then return a WRONG (empty) forward
     forwarded = []  # type: List[int]
-    i = 0
-    while i < len(names):
-        # invariants-start
-        Invariant(Acc(list_pred(names), 1 / 2))
-        Invariant(Acc(list_pred(values), 1 / 2))
-        Invariant(len(names) == len(values))
-        Invariant(Acc(list_pred(forwarded)))
-        Invariant(0 <= i and i <= len(names))
-        Invariant(ToSeq(forwarded) == ToSeq(names).take(i))
-        Invariant(MustTerminate(len(names) - i + 1))
-        # invariants-end
-        forwarded.append(names[i])
-        i = i + 1
-    Assert(ToSeq(names).take(len(names)) == ToSeq(names))
     return forwarded
     # impl-end
 
@@ -125,7 +108,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(values),
                                             values[k] >= 0),
                                     [[values[k]]])))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
```

Attack 3 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(Acc(list_pred(values), 1 / 2))
     Requires(len(names) == len(values))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -94,11 +92,10 @@
     Ensures(ToSeq(Result()) == ToSeq(names))
     # post-conditions-end
     # impl-start
-    # Forward the mapping positionally: every entry, including one whose name
-    # equals RESERVED_NAME, is kept as an axis selector.
+    # boundary error: forward all but the last entry
     forwarded = []  # type: List[int]
     i = 0
-    while i < len(names):
+    while i < len(names) - 1:
         # invariants-start
         Invariant(Acc(list_pred(names), 1 / 2))
         Invariant(Acc(list_pred(values), 1 / 2))
@@ -106,11 +103,9 @@
         Invariant(Acc(list_pred(forwarded)))
         Invariant(0 <= i and i <= len(names))
         Invariant(ToSeq(forwarded) == ToSeq(names).take(i))
-        Invariant(MustTerminate(len(names) - i + 1))
         # invariants-end
         forwarded.append(names[i])
         i = i + 1
-    Assert(ToSeq(names).take(len(names)) == ToSeq(names))
     return forwarded
     # impl-end
 
@@ -125,7 +120,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(values),
                                             values[k] >= 0),
                                     [[values[k]]])))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
```

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(Acc(list_pred(values), 1 / 2))
     Requires(len(names) == len(values))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -106,7 +104,6 @@
         Invariant(Acc(list_pred(forwarded)))
         Invariant(0 <= i and i <= len(names))
         Invariant(ToSeq(forwarded) == ToSeq(names).take(i))
-        Invariant(MustTerminate(len(names) - i + 1))
         # invariants-end
         forwarded.append(names[i])
         i = i + 1
@@ -125,7 +122,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(values),
                                             values[k] >= 0),
                                     [[values[k]]])))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -136,7 +132,7 @@
     Ensures(Result() == DEFAULT_OPTION())
     # post-conditions-end
     # impl-start
-    # Positional forwarding: the reserved option is not fed from the mapping.
-    option = DEFAULT_OPTION()
+    # wrong: bind reserved option to 0 instead of DEFAULT_OPTION (-1)
+    option = 0
     return option
     # impl-end
```

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
     Requires(Acc(list_pred(names), 1 / 2))
     Requires(Acc(list_pred(values), 1 / 2))
     Requires(len(names) == len(values))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
@@ -94,8 +92,7 @@
     Ensures(ToSeq(Result()) == ToSeq(names))
     # post-conditions-end
     # impl-start
-    # Forward the mapping positionally: every entry, including one whose name
-    # equals RESERVED_NAME, is kept as an axis selector.
+    # wrong: append each name AND re-append the last (duplicates)
     forwarded = []  # type: List[int]
     i = 0
     while i < len(names):
@@ -105,12 +102,10 @@
         Invariant(len(names) == len(values))
         Invariant(Acc(list_pred(forwarded)))
         Invariant(0 <= i and i <= len(names))
-        Invariant(ToSeq(forwarded) == ToSeq(names).take(i))
-        Invariant(MustTerminate(len(names) - i + 1))
         # invariants-end
         forwarded.append(names[i])
+        forwarded.append(names[i])
         i = i + 1
-    Assert(ToSeq(names).take(len(names)) == ToSeq(names))
     return forwarded
     # impl-end
 
@@ -125,7 +120,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(values),
                                             values[k] >= 0),
                                     [[values[k]]])))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(names), 1 / 2))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-4695.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A label-based selection facade receives a mapping from axis names to label
  selectors and forwards it to an underlying label selector. The underlying
  selector exposes, besides the axis mapping, a small predefined collection of
  RESERVED option names (here: the inexact-match option, modelled as a single
  reserved name). The facade must forward EVERY entry of the incoming mapping as an
  axis selector, and must leave the reserved option at its default value,
  for ANY incoming mapping -- including a mapping whose axis name happens to
  coincide with a reserved option name.

  Concretely, given the incoming mapping presented as a parallel pair of
  sequences (axis-name ids `names`, label selectors `values`):

    * the axis selectors actually forwarded to the underlying selector are the
      WHOLE incoming mapping -- the forwarded axis-name sequence equals `names`
      in full, with no entry diverted away because its name collides with a
      reserved option name (`forward_axis_names`); and

    * the value bound to the reserved option is its DEFAULT sentinel, never a
      label selector taken from the incoming mapping (`bound_reserved_option`).

The load-bearing behaviour is that an axis whose name equals the reserved
option name (RESERVED_NAME) is still forwarded as an axis selector and does
NOT leak into the reserved option slot. The reserved option therefore stays
at DEFAULT_OPTION for every input, and the forwarded axes are complete.

Mapping entries are modelled as parallel `List[int]`: `names[k]` is an opaque
axis-name id, `values[k]` the (opaque) label selector for that axis. Names and
the reserved sentinels are small int ids. The specification is carried over
`PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms: the forwarding/routing behaviour is modelled deeply)
# axioms-end


# pure-start
@Pure
def RESERVED_NAME() -> int:
    """Axis-name id that collides with a reserved option name of the underlying
    selector (the inexact-match option). The discriminating input."""
    return 7


@Pure
def DEFAULT_OPTION() -> int:
    """Default value of the reserved option (its unset sentinel). Distinct from
    every label selector id used as a mapping value (selectors are >= 0)."""
    return -1


@Pure
def option_after_namekeyed(names: PSeq[int], values: PSeq[int]) -> int:
    """The value the reserved option would take under a NAME-KEYED routing that
    diverts a colliding axis into the reserved slot: the value of the last
    mapping entry whose axis name equals RESERVED_NAME, else the default
    sentinel. Front-recursive so one unfold is available per loop step. This is
    the routing the correct facade must NOT perform; it appears here only so
    the impl can compute and reject it."""
    Requires(len(names) == len(values))
    if len(names) == 0:
        return DEFAULT_OPTION()
    if names[len(names) - 1] == RESERVED_NAME():
        return values[len(values) - 1]
    return option_after_namekeyed(names.take(len(names) - 1),
                                  values.take(len(values) - 1))
# pure-end


def forward_axis_names(names: List[int], values: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(len(names) == len(values))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Every incoming entry is forwarded as an axis selector: the forwarded
    # axis-name sequence is the WHOLE incoming name sequence (no entry diverted
    # because its name collides with the reserved option name).
    Ensures(ToSeq(Result()) == ToSeq(names))
    # post-conditions-end
    # impl-start
    # Forward the mapping positionally: every entry, including one whose name
    # equals RESERVED_NAME, is kept as an axis selector.
    forwarded = []  # type: List[int]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(len(names) == len(values))
        Invariant(Acc(list_pred(forwarded)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(forwarded) == ToSeq(names).take(i))
        # invariants-end
        forwarded.append(names[i])
        i = i + 1
    Assert(ToSeq(names).take(len(names)) == ToSeq(names))
    return forwarded
    # impl-end


def bound_reserved_option(names: List[int], values: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(len(names) == len(values))
    # Label selectors are non-negative ids; the default sentinel (-1) is
    # reserved and never appears as a mapping value.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(values),
                                            values[k] >= 0),
                                    [[values[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(values), 1 / 2))
    # The reserved option keeps its default for EVERY input -- a colliding axis
    # (name == RESERVED_NAME) is forwarded as an axis selector, never bound to
    # the reserved option slot.
    Ensures(Result() == DEFAULT_OPTION())
    # post-conditions-end
    # impl-start
    # Positional forwarding: the reserved option is not fed from the mapping.
    option = DEFAULT_OPTION()
    return option
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of pydata__xarray-4695 nagini bundle (deeply-modeled, NO consumed @ContractOnly axioms; A-reference legs only). Gold hunk: `self.data_array.sel(**key)` -> `self.data_array.sel(key)` in _LocIndexer.__getitem__. Spec pins two clauses: forward_axis_names Ensures ToSeq(Result())==ToSeq(names); bound_reserved_option Ensures Result()==DEFAULT_OPTION(). Read-only inputs are held at Acc(list_pred,1/2) (closes the mutation/overwrite vacuity escape).

### ATTACK SUITE (all same-spec confirmed; verify via scripts/nagini_verify.sh; candidacy via `adversary weakness`):
- atk_1 (atk_1.py) = prepatch model_prepatch.py (name-keyed routing: forward drops RESERVED_NAME entries, bound=option_after_namekeyed). VERIFY exit=1 -> FAILS on both postconditions. PREPATCH REPRODUCED.
- atk_4 off-by-one (forward all but last, i<len-1): VERIFY exit=1 FAIL.
- atk_5 control-flow-effect (bound returns 0 instead of -1): VERIFY exit=1 FAIL.
- atk_6 partial-domain (duplicate each name): VERIFY exit=1 FAIL.
- atk_3b empty-forward WITHOUT Assume (return []): VERIFY exit=1 FAIL on 'Postcondition ToSeq(Result())==ToSeq(names) might not hold'.
  => Every TERMINATING, HYGIENE-LEGAL wrong impl is REJECTED. The spec is tight on functional behavior.

### CANDIDATES THAT VERIFY (all EXCLUDED-CLASS verifier artifacts, NOT genuine spec weaknesses):
- atk_2 (atk_2.py): non-terminating forward_axis_names (while True). `adversary weakness` -> CANDIDATE (exit 0, 12.4s). EXCLUDED: partial-correctness vacuity; model uses NO MustTerminate (quickref: 'Termination proofs are NOT required by default'; 80/500 nagini bundles use MustTerminate so absence is corpus-normal, not a defect specific here). A faithful patch would be an infinite loop in __getitem__; run_resolve on it can only TIME OUT -> completed=False -> INCONCLUSIVE by the runner's own derivation (build_one.py:_derive_audit_verdict treats non-completed resolve as inconclusive, never a break). Not submitted as a break.
- atk_7 (atk_7.py): non-terminating bound_reserved_option. `adversary weakness` -> CANDIDATE (exit 0, 12.0s). Same excluded class as atk_2.
- atk_3 (atk_3.py): Assume(False) then wrong empty forward. `adversary weakness` -> CANDIDATE (exit 0, 11.8s). EXCLUDED: verifies ONLY via the BANNED token Assume (nagini backend banned_tokens=('Assume(','Refute(') per src/swebench_unified/backends/nagini.py; eval/adapter.py: 'Assume/Refute can fake verification'). PROOF it is an Assume-cheat: atk_3b (identical impl, Assume line removed) FAILS verification (exit 1). Not a spec weakness.

MANDATORY EXECUTED run_resolve EVIDENCE (via swebench_unified.harness.run_resolve, docker):
- GOLD patch.diff: {completed:true, resolved:true, attempts:1} -> harness sane, F2P test_loc_dim_name_collision_with_sel_params discriminates.
- patch_atk3_emptyforward.diff (faithful TERMINATING wrong behavior = forward nothing: sel({}) ): {completed:true, resolved:false, attempts:3, flaky:false, note 'consistent - not flaky'} -> the terminating wrong-forward behavior does NOT resolve, matching that atk_3b/atk_1 FAIL verification. This confirms the postcondition ToSeq(Result())==ToSeq(names) is LOAD-BEARING (verify<->resolve aligned on the legal impl class).
No verifying wrong impl exists in the legitimate (terminating, hygiene-legal) class, so there is no faithful patch that verifies-but-does-not-resolve. patches={} accordingly.

REFINEMENT.md LEG AUDIT: all legs R or A-reference; NO consumed axioms; NO kind-3.
- A1/A3/B1 (R): dict key <-> parallel List[int] (names,values); forwarded seq <-> axis indexers. R-refinement, G-CONF-covered.
- A2 (A-reference): copy-every-name loop <-> sel(key) positional binding, either_dict_or_kwargs(key,{})==key whole. NO @ContractOnly consumed (routing modeled deeply). Correspondence VALIDATED by axiom_check.py check_positional (executed, exit 0: 11 boundary + 20000 fuzz, incl. {'dim1':'x','method':'a'} and all-three-reserved collisions).
- B2 (A-reference): option=DEFAULT_OPTION() unconditional <-> method/tolerance/drop stay at signature defaults; DEFAULT_OPTION==-1 <-> method=None. VALIDATED by axiom_check.py (method is None etc.), exit 0.
- Section C correctly documents no kind-3: the one changed op (indexer-mapping routing through sel's keyword binding) is modeled deeply, NOT axiomatized (axiomatizing the function-under-change would be forbidden per SPEC_GUIDE dir. 7). Correct.
G-CONF conformance_check.py additionally cross-checks the contract-stripped impl against the REAL patched _LocIndexer.__getitem__ over 1e5+ inputs (independent corroboration of R/I + A-reference legs).

VERDICT: SOUND. 5 same-spec attacks submitted (prepatch + 4 distinct terminating wrong impls) all rejected; positive control verifies; prepatch reproduced; gold resolves; a terminating wrong patch consistently does NOT resolve (executed). The only verifying candidates exploit non-termination / the banned Assume token -- excluded verifier artifacts that break no bundle's verify=>correct claim within G-EQ's scope. On the legitimate impl class verify=>correct holds and the refinement map is faithful.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_3b.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3b.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-4695.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A label-based selection facade receives a mapping from axis names to label
  selectors and forwards it to an underlying label selector. The underlying
  selector exposes, besides the axis mapping, a small predefined collection of
  RESERVED option names (here: the inexact-match option, modelled as a single
  reserved name). The facade must forward EVERY entry of the incoming mapping as an
  axis selector, and must leave the reserved option at its default value,
  for ANY incoming mapping -- including a mapping whose axis name happens to
  coincide with a reserved option name.

  Concretely, given the incoming mapping presented as a parallel pair of
  sequences (axis-name ids `names`, label selectors `values`):

    * the axis selectors actually forwarded to the underlying selector are the
      WHOLE incoming mapping -- the forwarded axis-name sequence equals `names`
      in full, with no entry diverted away because its name collides with a
      reserved option name (`forward_axis_names`); and

    * the value bound to the reserved option is its DEFAULT sentinel, never a
      label selector taken from the incoming mapping (`bound_reserved_option`).

The load-bearing behaviour is that an axis whose name equals the reserved
option name (RESERVED_NAME) is still forwarded as an axis selector and does
NOT leak into the reserved option slot. The reserved option therefore stays
at DEFAULT_OPTION for every input, and the forwarded axes are complete.

Mapping entries are modelled as parallel `List[int]`: `names[k]` is an opaque
axis-name id, `values[k]` the (opaque) label selector for that axis. Names and
the reserved sentinels are small int ids. The specification is carried over
`PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms: the forwarding/routing behaviour is modelled deeply)
# axioms-end


# pure-start
@Pure
def RESERVED_NAME() -> int:
    """Axis-name id that collides with a reserved option name of the underlying
    selector (the inexact-match option). The discriminating input."""
    return 7


@Pure
def DEFAULT_OPTION() -> int:
    """Default value of the reserved option (its unset sentinel). Distinct from
    every label selector id used as a mapping value (selectors are >= 0)."""
    return -1


@Pure
def option_after_namekeyed(names: PSeq[int], values: PSeq[int]) -> int:
    """The value the reserved option would take under a NAME-KEYED routing that
    diverts a colliding axis into the reserved slot: the value of the last
    mapping entry whose axis name equals RESERVED_NAME, else the default
    sentinel. Front-recursive so one unfold is available per loop step. This is
    the routing the correct facade must NOT perform; it appears here only so
    the impl can compute and reject it."""
    Requires(len(names) == len(values))
    if len(names) == 0:
        return DEFAULT_OPTION()
    if names[len(names) - 1] == RESERVED_NAME():
        return values[len(values) - 1]
    return option_after_namekeyed(names.take(len(names) - 1),
                                  values.take(len(values) - 1))
# pure-end


def forward_axis_names(names: List[int], values: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(len(names) == len(values))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Every incoming entry is forwarded as an axis selector: the forwarded
    # axis-name sequence is the WHOLE incoming name sequence (no entry diverted
    # because its name collides with the reserved option name).
    Ensures(ToSeq(Result()) == ToSeq(names))
    # post-conditions-end
    # impl-start
    # Forward the mapping positionally: every entry, including one whose name
    # equals RESERVED_NAME, is kept as an axis selector.
    forwarded = []  # type: List[int]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(len(names) == len(values))
        Invariant(Acc(list_pred(forwarded)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(forwarded) == ToSeq(names).take(i))
        # invariants-end
        forwarded.append(names[i])
        i = i + 1
    Assert(ToSeq(names).take(len(names)) == ToSeq(names))
    return forwarded
    # impl-end


def bound_reserved_option(names: List[int], values: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(len(names) == len(values))
    # Label selectors are non-negative ids; the default sentinel (-1) is
    # reserved and never appears as a mapping value.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(values),
                                            values[k] >= 0),
                                    [[values[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(values), 1 / 2))
    # The reserved option keeps its default for EVERY input -- a colliding axis
    # (name == RESERVED_NAME) is forwarded as an axis selector, never bound to
    # the reserved option slot.
    Ensures(Result() == DEFAULT_OPTION())
    # post-conditions-end
    # impl-start
    # Positional forwarding: the reserved option is not fed from the mapping.
    option = DEFAULT_OPTION()
    return option
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of pydata__xarray-4695 nagini bundle (deeply-modeled, NO consumed @ContractOnly axioms; A-reference legs only). Gold hunk: `self.data_array.sel(**key)` -> `self.data_array.sel(key)` in _LocIndexer.__getitem__. Spec pins two clauses: forward_axis_names Ensures ToSeq(Result())==ToSeq(names); bound_reserved_option Ensures Result()==DEFAULT_OPTION(). Read-only inputs are held at Acc(list_pred,1/2) (closes the mutation/overwrite vacuity escape).

### ATTACK SUITE (all same-spec confirmed; verify via scripts/nagini_verify.sh; candidacy via `adversary weakness`):
- atk_1 (atk_1.py) = prepatch model_prepatch.py (name-keyed routing: forward drops RESERVED_NAME entries, bound=option_after_namekeyed). VERIFY exit=1 -> FAILS on both postconditions. PREPATCH REPRODUCED.
- atk_4 off-by-one (forward all but last, i<len-1): VERIFY exit=1 FAIL.
- atk_5 control-flow-effect (bound returns 0 instead of -1): VERIFY exit=1 FAIL.
- atk_6 partial-domain (duplicate each name): VERIFY exit=1 FAIL.
- atk_3b empty-forward WITHOUT Assume (return []): VERIFY exit=1 FAIL on 'Postcondition ToSeq(Result())==ToSeq(names) might not hold'.
  => Every TERMINATING, HYGIENE-LEGAL wrong impl is REJECTED. The spec is tight on functional behavior.

### CANDIDATES THAT VERIFY (all EXCLUDED-CLASS verifier artifacts, NOT genuine spec weaknesses):
- atk_2 (atk_2.py): non-terminating forward_axis_names (while True). `adversary weakness` -> CANDIDATE (exit 0, 12.4s). EXCLUDED: partial-correctness vacuity; model uses NO MustTerminate (quickref: 'Termination proofs are NOT required by default'; 80/500 nagini bundles use MustTerminate so absence is corpus-normal, not a defect specific here). A faithful patch would be an infinite loop in __getitem__; run_resolve on it can only TIME OUT -> completed=False -> INCONCLUSIVE by the runner's own derivation (build_one.py:_derive_audit_verdict treats non-completed resolve as inconclusive, never a break). Not submitted as a break.
- atk_7 (atk_7.py): non-terminating bound_reserved_option. `adversary weakness` -> CANDIDATE (exit 0, 12.0s). Same excluded class as atk_2.
- atk_3 (atk_3.py): Assume(False) then wrong empty forward. `adversary weakness` -> CANDIDATE (exit 0, 11.8s). EXCLUDED: verifies ONLY via the BANNED token Assume (nagini backend banned_tokens=('Assume(','Refute(') per src/swebench_unified/backends/nagini.py; eval/adapter.py: 'Assume/Refute can fake verification'). PROOF it is an Assume-cheat: atk_3b (identical impl, Assume line removed) FAILS verification (exit 1). Not a spec weakness.

MANDATORY EXECUTED run_resolve EVIDENCE (via swebench_unified.harness.run_resolve, docker):
- GOLD patch.diff: {completed:true, resolved:true, attempts:1} -> harness sane, F2P test_loc_dim_name_collision_with_sel_params discriminates.
- patch_atk3_emptyforward.diff (faithful TERMINATING wrong behavior = forward nothing: sel({}) ): {completed:true, resolved:false, attempts:3, flaky:false, note 'consistent - not flaky'} -> the terminating wrong-forward behavior does NOT resolve, matching that atk_3b/atk_1 FAIL verification. This confirms the postcondition ToSeq(Result())==ToSeq(names) is LOAD-BEARING (verify<->resolve aligned on the legal impl class).
No verifying wrong impl exists in the legitimate (terminating, hygiene-legal) class, so there is no faithful patch that verifies-but-does-not-resolve. patches={} accordingly.

REFINEMENT.md LEG AUDIT: all legs R or A-reference; NO consumed axioms; NO kind-3.
- A1/A3/B1 (R): dict key <-> parallel List[int] (names,values); forwarded seq <-> axis indexers. R-refinement, G-CONF-covered.
- A2 (A-reference): copy-every-name loop <-> sel(key) positional binding, either_dict_or_kwargs(key,{})==key whole. NO @ContractOnly consumed (routing modeled deeply). Correspondence VALIDATED by axiom_check.py check_positional (executed, exit 0: 11 boundary + 20000 fuzz, incl. {'dim1':'x','method':'a'} and all-three-reserved collisions).
- B2 (A-reference): option=DEFAULT_OPTION() unconditional <-> method/tolerance/drop stay at signature defaults; DEFAULT_OPTION==-1 <-> method=None. VALIDATED by axiom_check.py (method is None etc.), exit 0.
- Section C correctly documents no kind-3: the one changed op (indexer-mapping routing through sel's keyword binding) is modeled deeply, NOT axiomatized (axiomatizing the function-under-change would be forbidden per SPEC_GUIDE dir. 7). Correct.
G-CONF conformance_check.py additionally cross-checks the contract-stripped impl against the REAL patched _LocIndexer.__getitem__ over 1e5+ inputs (independent corroboration of R/I + A-reference legs).

VERDICT: SOUND. 5 same-spec attacks submitted (prepatch + 4 distinct terminating wrong impls) all rejected; positive control verifies; prepatch reproduced; gold resolves; a terminating wrong patch consistently does NOT resolve (executed). The only verifying candidates exploit non-termination / the banned Assume token -- excluded verifier artifacts that break no bundle's verify=>correct claim within G-EQ's scope. On the legitimate impl class verify=>correct holds and the refinement map is faithful.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (drift) check for pydata__xarray-4695 nagini. Modeled funcs forward_axis_names (Ensures ToSeq(Result())==ToSeq(names)) and bound_reserved_option (Ensures Result()==DEFAULT_OPTION()) model _LocIndexer.__getitem__ after gold patch (self.data_array.sel(key), positional forwarding). Verified against the REAL patched repo at base_commit 51ef2a66 + patch.diff by driving the actual _LocIndexer over the bundle's conformance domain: 12 boundary + 100,000 fuzz inputs (seed 46950) via a sel-shaped probe using the repo's REAL either_dict_or_kwargs -> 100,012/100,012 agreements (shadow forwarded==real forwarded, option==default, eff==mapping, tolerance/drop default), including all collision cases (dim named 'method' at front/middle/back and collision-only). Type bridge (RESERVED_NAME=7<->'method', DEFAULT_OPTION=-1<->None, injective name domain) is documented and sound; the List[int] duplicate freedom is legitimately restricted to the injective domain since real dicts cannot hold duplicate keys, and the spec's postconditions hold on that domain matching the real callee. model.py verifies (nagini_verify.sh exit 0, 'Verification successful'); model_prepatch.py (name-keyed routing) genuinely fails both postcondition clauses (G-DIFF). Only conformance failure was smoke_real_selection, a pandas-3.0 env artifact (Index.get_loc no longer accepts method=), unrelated to spec routing semantics and not a spec/repo disagreement. No diverging input exists: spec is faithful, not too strong, no drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `self.data_array.sel(**key)` -> `self.data_array.sel(key)` in _LocIndexer.__getitem__ (xarray/core/dataarray.py:198) — forward the indexer mapping positionally instead of splatting into kwargs, so a dim named 'method' isn't captured by sel's reserved `method=` kwarg. The public problem_statement ALREADY fully discloses the desired behavior: naming a dimension 'method' must not break .loc, the resulting 'Invalid fill method' error, and that 'the dims are given to another method in unsanitized form' / 'the name of the dimension should be irrelevant'. The spec view (docstring + Requires/Ensures) restates exactly this in fully abstracted terms: opaque int axis-name ids, a single generic 'reserved option' with a DEFAULT sentinel (RESERVED_NAME=7, DEFAULT_OPTION=-1), and postconditions ToSeq(Result())==ToSeq(names) (forward the whole mapping) and Result()==DEFAULT_OPTION() (reserved option stays default). It NEVER names sel, kwargs, `**key`, dict-vs-positional forwarding, .loc, __getitem__, DataArray, or any code-level mechanism of the edit. The name-keyed helper `option_after_namekeyed` is presented as the routing the correct impl must NOT perform and lives in the pure/impl regions, not as a spec-only tell. Mechanical G-LEAK screen passes (0 hard failures): no diff markers, no reproduced gold line (>=8 char), no patched file path/module, no spec-view identifier embedding a patched repo symbol, no bug/fix narration. No relaxation in play (relaxed_leakage None, no RELAXED_LEAKAGE.md). same-spec vs model_prepatch.py returns exit 0 — the spec region is byte-identical and impl-agnostic (both patched and pre-patch skeletons share it). Nothing in the spec view reconstructs the gold edit beyond what problem_statement already publicly states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
