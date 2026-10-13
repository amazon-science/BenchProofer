# P2 adversarial audit — pydata__xarray-2905

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
                     Result() == data.identity))
     # post-conditions-end
     # impl-start
-    if data.is_recognized_container:
+    if data.exposes_values:
         result = data.values_identity
     else:
         result = data.identity
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -91,8 +91,8 @@
     # post-conditions-end
     # impl-start
     if data.is_recognized_container:
+        result = data.identity
+    else:
         result = data.values_identity
-    else:
-        result = data.identity
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,9 +90,6 @@
                     Result() == data.identity))
     # post-conditions-end
     # impl-start
-    if data.is_recognized_container:
-        result = data.values_identity
-    else:
-        result = data.identity
+    result = data.identity
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,9 +90,6 @@
                     Result() == data.identity))
     # post-conditions-end
     # impl-start
-    if data.is_recognized_container:
-        result = data.values_identity
-    else:
-        result = data.identity
+    result = data.values_identity
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,6 +93,8 @@
     if data.is_recognized_container:
         result = data.values_identity
     else:
+        result = data.values_identity
+        data.identity = data.values_identity
         result = data.identity
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
                     Result() == data.identity))
     # post-conditions-end
     # impl-start
-    if data.is_recognized_container:
+    if data.is_recognized_container and not data.exposes_values:
         result = data.values_identity
     else:
         result = data.identity
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,9 +90,8 @@
                     Result() == data.identity))
     # post-conditions-end
     # impl-start
+    result = data.identity
     if data.is_recognized_container:
         result = data.values_identity
-    else:
-        result = data.identity
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-2905.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an arbitrary incoming value is prepared for storage, there is a single
  normalization step that decides whether to replace the value with the
  contents exposed under its ``values`` attribute (so that an already
  self-describing container is not nested inside another container).

  The desired behaviour: this replacement is performed ONLY when the value is
  one of the specific self-describing container kinds the system recognizes.
  For every other value — INCLUDING a plain object that merely happens to
  expose a ``values`` attribute — the value must pass through this step
  UNCHANGED, so that such objects are stored as themselves rather than being
  silently coerced to whatever their ``values`` attribute holds. Merely
  exposing a ``values`` attribute is NOT sufficient to trigger the replacement.

The incoming value is modelled as a minimal class carrying only the facts this
step inspects: whether it is one of the recognized self-describing container
kinds, whether it exposes a ``values`` attribute, and the identity tags of the
value itself and of its ``values`` contents. The step returns the identity tag
of the value that survives normalization.

A real-world invariant constrains the inputs: every recognized self-describing
container kind does expose a ``values`` attribute (so being a recognized kind
is a strictly more specific condition than merely exposing the attribute).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class Incoming:
    """A value arriving at the normalization step. ``identity`` tags the value
    itself; ``values_identity`` tags what its ``values`` attribute holds (only
    meaningful when ``exposes_values``)."""

    def __init__(self, is_recognized_container: bool, exposes_values: bool,
                 identity: int, values_identity: int) -> None:
        Requires(Implies(is_recognized_container, exposes_values))
        Ensures(Acc(self.is_recognized_container, 1 / 2))  # type: ignore
        Ensures(Acc(self.exposes_values, 1 / 2))           # type: ignore
        Ensures(Acc(self.identity, 1 / 2))                 # type: ignore
        Ensures(Acc(self.values_identity, 1 / 2))          # type: ignore
        Ensures(self.is_recognized_container == is_recognized_container)  # type: ignore
        Ensures(self.exposes_values == exposes_values)     # type: ignore
        Ensures(self.identity == identity)                 # type: ignore
        Ensures(self.values_identity == values_identity)   # type: ignore
        Ensures(Implies(self.is_recognized_container, self.exposes_values))  # type: ignore
        self.is_recognized_container = is_recognized_container
        self.exposes_values = exposes_values
        self.identity = identity
        self.values_identity = values_identity


# axioms-start
# (no @ContractOnly callees: the changed decision is modelled deeply below.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def normalize_self_describing(data: Incoming) -> int:
    # pre-conditions-start
    Requires(Acc(data.is_recognized_container, 1 / 2))
    Requires(Acc(data.exposes_values, 1 / 2))
    Requires(Acc(data.identity, 1 / 2))
    Requires(Acc(data.values_identity, 1 / 2))
    # the real-world invariant: a recognized container always exposes .values.
    Requires(Implies(data.is_recognized_container, data.exposes_values))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(data.is_recognized_container, 1 / 2))
    Ensures(Acc(data.exposes_values, 1 / 2))
    Ensures(Acc(data.identity, 1 / 2))
    Ensures(Acc(data.values_identity, 1 / 2))
    # the read-only input is unchanged.
    Ensures(data.is_recognized_container == Old(data.is_recognized_container))
    Ensures(data.exposes_values == Old(data.exposes_values))
    Ensures(data.identity == Old(data.identity))
    Ensures(data.values_identity == Old(data.values_identity))
    # The surviving value is the .values contents iff the input is a recognized
    # self-describing container; otherwise the value passes through unchanged.
    Ensures(Implies(data.is_recognized_container,
                    Result() == data.values_identity))
    Ensures(Implies(not data.is_recognized_container,
                    Result() == data.identity))
    # post-conditions-end
    # impl-start
    if data.is_recognized_container:
        result = data.values_identity
    else:
        result = data.identity
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec is a COMPLETE functional specification: the two postconditions Implies(is_recognized_container, Result()==values_identity) and Implies(not is_recognized_container, Result()==identity) TOTALLY determine Result() for every input; the four Ensures(field==Old(field)) clauses + Acc(...,1/2) fractional permissions block mutation-based vacuity. Any verifying impl must reproduce gold behaviour exactly.

ENV: adversary/harness run under python (PATH prepend);

ATTACKS (all built editing ONLY the impl region; same-spec exit 0 for all 7; pos_control also same-spec). Cmd form: `python -m swebench_unified.adversary weakness nagini pydata__xarray-2905 <path>`:
- atk_1.py PREPATCH BUG (issue's HasValues): `if data.exposes_values: result=values_identity else identity`. weakness exit=2 (NOT-A-COUNTEREXAMPLE, verification failed) => prepatch_reproduced=True. Spec rejects unwrapping on mere .values exposure.
- atk_2.py swapped branches (identity when recognized, values when not): weakness exit=2 (fails postcond).
- atk_3.py always return data.identity (never unwrap): weakness exit=2 (fails recognized-branch postcond).
- atk_4.py always return data.values_identity (always unwrap): weakness exit=2 (fails not-recognized postcond).
- atk_5.py control-flow-effect: attempts `data.identity = data.values_identity` mutation in else branch: weakness exit=2 (blocked by Acc 1/2 read-only + Old-equality).
- atk_6.py partial-domain/boundary: unwrap only when `is_recognized_container and not exposes_values` (vacuous under invariant): weakness exit=2 (fails recognized postcond).
- atk_7.py ECHO (behaviourally identical to gold): `result=data.identity; if data.is_recognized_container: result=data.values_identity`. weakness exit=0 => CANDIDATE (shares spec AND verifies). PER PROTOCOL materialized faithful refined patch (patch_atk_7.diff, == gold isinstance-unwrap since impl is behaviourally identical to gold model) and RAN it through the official harness via swebench_unified.harness.run_resolve('pydata__xarray-2905', patch, run_id='sbu-atk7-eq'): RESOLVED=True, completed=True, note='resolved', attempts=1, flaky=False. FAIL_TO_PASS test_unsupported_type SUCCESS, all PASS_TO_PASS success, zero failures. Because the candidate's faithful patch RESOLVES, it is a legitimate echo, NOT a spec weakness (echo policy).

POSITIVE CONTROL: pos_control.py = exact model.py impl; `bash scripts/nagini_verify.sh` exit=0 (verifies).

REFINEMENT.MD LEG AUDIT (A-legs focus, R/I covered by G-CONF): A1=R (arbitrary value -> Incoming record + identity tags). A2=A-reference, the ONLY A-leg: bool is_recognized_container deeply models real isinstance(data,(pd.Series,pd.Index,pd.DataFrame)); NO consumed @ContractOnly axiom (meta.axioms=[], §C confirmed). Correspondence validated by axiom_check.py/G-AX (recorded strict pass, exit 0): real as_compatible_data unwraps exactly the 3 pandas kinds and passes through non-recognized .values-bearing objects (item() is original), incl. issue's scalar-.values object + Variable(dims=()) F2P oracle; model invariant recognized=>exposes_values holds on real pandas types. A3=R (values_identity <-> data.values rebinding). A4=I (else keeps input == gold has no else). A5=R (result tag <-> surviving local data). No kind-3 legs. G-AX A-reference faithfulness independently corroborated by run_resolve resolving on the gold-equivalent behaviour.

No verifying wrong impl exists whose faithful patch fails to resolve. >=5 distinct attacks (7 total) run to completion, prepatch reproduced, positive control verifies, sole candidate's materialized patch RESOLVED under the official harness. verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-2905.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an arbitrary incoming value is prepared for storage, there is a single
  normalization step that decides whether to replace the value with the
  contents exposed under its ``values`` attribute (so that an already
  self-describing container is not nested inside another container).

  The desired behaviour: this replacement is performed ONLY when the value is
  one of the specific self-describing container kinds the system recognizes.
  For every other value — INCLUDING a plain object that merely happens to
  expose a ``values`` attribute — the value must pass through this step
  UNCHANGED, so that such objects are stored as themselves rather than being
  silently coerced to whatever their ``values`` attribute holds. Merely
  exposing a ``values`` attribute is NOT sufficient to trigger the replacement.

The incoming value is modelled as a minimal class carrying only the facts this
step inspects: whether it is one of the recognized self-describing container
kinds, whether it exposes a ``values`` attribute, and the identity tags of the
value itself and of its ``values`` contents. The step returns the identity tag
of the value that survives normalization.

A real-world invariant constrains the inputs: every recognized self-describing
container kind does expose a ``values`` attribute (so being a recognized kind
is a strictly more specific condition than merely exposing the attribute).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class Incoming:
    """A value arriving at the normalization step. ``identity`` tags the value
    itself; ``values_identity`` tags what its ``values`` attribute holds (only
    meaningful when ``exposes_values``)."""

    def __init__(self, is_recognized_container: bool, exposes_values: bool,
                 identity: int, values_identity: int) -> None:
        Requires(Implies(is_recognized_container, exposes_values))
        Ensures(Acc(self.is_recognized_container, 1 / 2))  # type: ignore
        Ensures(Acc(self.exposes_values, 1 / 2))           # type: ignore
        Ensures(Acc(self.identity, 1 / 2))                 # type: ignore
        Ensures(Acc(self.values_identity, 1 / 2))          # type: ignore
        Ensures(self.is_recognized_container == is_recognized_container)  # type: ignore
        Ensures(self.exposes_values == exposes_values)     # type: ignore
        Ensures(self.identity == identity)                 # type: ignore
        Ensures(self.values_identity == values_identity)   # type: ignore
        Ensures(Implies(self.is_recognized_container, self.exposes_values))  # type: ignore
        self.is_recognized_container = is_recognized_container
        self.exposes_values = exposes_values
        self.identity = identity
        self.values_identity = values_identity


# axioms-start
# (no @ContractOnly callees: the changed decision is modelled deeply below.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def normalize_self_describing(data: Incoming) -> int:
    # pre-conditions-start
    Requires(Acc(data.is_recognized_container, 1 / 2))
    Requires(Acc(data.exposes_values, 1 / 2))
    Requires(Acc(data.identity, 1 / 2))
    Requires(Acc(data.values_identity, 1 / 2))
    # the real-world invariant: a recognized container always exposes .values.
    Requires(Implies(data.is_recognized_container, data.exposes_values))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(data.is_recognized_container, 1 / 2))
    Ensures(Acc(data.exposes_values, 1 / 2))
    Ensures(Acc(data.identity, 1 / 2))
    Ensures(Acc(data.values_identity, 1 / 2))
    # the read-only input is unchanged.
    Ensures(data.is_recognized_container == Old(data.is_recognized_container))
    Ensures(data.exposes_values == Old(data.exposes_values))
    Ensures(data.identity == Old(data.identity))
    Ensures(data.values_identity == Old(data.values_identity))
    # The surviving value is the .values contents iff the input is a recognized
    # self-describing container; otherwise the value passes through unchanged.
    Ensures(Implies(data.is_recognized_container,
                    Result() == data.values_identity))
    Ensures(Implies(not data.is_recognized_container,
                    Result() == data.identity))
    # post-conditions-end
    # impl-start
    if data.is_recognized_container:
        result = data.values_identity
    else:
        result = data.identity
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec is a COMPLETE functional specification: the two postconditions Implies(is_recognized_container, Result()==values_identity) and Implies(not is_recognized_container, Result()==identity) TOTALLY determine Result() for every input; the four Ensures(field==Old(field)) clauses + Acc(...,1/2) fractional permissions block mutation-based vacuity. Any verifying impl must reproduce gold behaviour exactly.

ENV: adversary/harness run under python (PATH prepend);

ATTACKS (all built editing ONLY the impl region; same-spec exit 0 for all 7; pos_control also same-spec). Cmd form: `python -m swebench_unified.adversary weakness nagini pydata__xarray-2905 <path>`:
- atk_1.py PREPATCH BUG (issue's HasValues): `if data.exposes_values: result=values_identity else identity`. weakness exit=2 (NOT-A-COUNTEREXAMPLE, verification failed) => prepatch_reproduced=True. Spec rejects unwrapping on mere .values exposure.
- atk_2.py swapped branches (identity when recognized, values when not): weakness exit=2 (fails postcond).
- atk_3.py always return data.identity (never unwrap): weakness exit=2 (fails recognized-branch postcond).
- atk_4.py always return data.values_identity (always unwrap): weakness exit=2 (fails not-recognized postcond).
- atk_5.py control-flow-effect: attempts `data.identity = data.values_identity` mutation in else branch: weakness exit=2 (blocked by Acc 1/2 read-only + Old-equality).
- atk_6.py partial-domain/boundary: unwrap only when `is_recognized_container and not exposes_values` (vacuous under invariant): weakness exit=2 (fails recognized postcond).
- atk_7.py ECHO (behaviourally identical to gold): `result=data.identity; if data.is_recognized_container: result=data.values_identity`. weakness exit=0 => CANDIDATE (shares spec AND verifies). PER PROTOCOL materialized faithful refined patch (patch_atk_7.diff, == gold isinstance-unwrap since impl is behaviourally identical to gold model) and RAN it through the official harness via swebench_unified.harness.run_resolve('pydata__xarray-2905', patch, run_id='sbu-atk7-eq'): RESOLVED=True, completed=True, note='resolved', attempts=1, flaky=False. FAIL_TO_PASS test_unsupported_type SUCCESS, all PASS_TO_PASS success, zero failures. Because the candidate's faithful patch RESOLVES, it is a legitimate echo, NOT a spec weakness (echo policy).

POSITIVE CONTROL: pos_control.py = exact model.py impl; `bash scripts/nagini_verify.sh` exit=0 (verifies).

REFINEMENT.MD LEG AUDIT (A-legs focus, R/I covered by G-CONF): A1=R (arbitrary value -> Incoming record + identity tags). A2=A-reference, the ONLY A-leg: bool is_recognized_container deeply models real isinstance(data,(pd.Series,pd.Index,pd.DataFrame)); NO consumed @ContractOnly axiom (meta.axioms=[], §C confirmed). Correspondence validated by axiom_check.py/G-AX (recorded strict pass, exit 0): real as_compatible_data unwraps exactly the 3 pandas kinds and passes through non-recognized .values-bearing objects (item() is original), incl. issue's scalar-.values object + Variable(dims=()) F2P oracle; model invariant recognized=>exposes_values holds on real pandas types. A3=R (values_identity <-> data.values rebinding). A4=I (else keeps input == gold has no else). A5=R (result tag <-> surviving local data). No kind-3 legs. G-AX A-reference faithfulness independently corroborated by run_resolve resolving on the gold-equivalent behaviour.

No verifying wrong impl exists whose faithful patch fails to resolve. >=5 distinct attacks (7 total) run to completion, prepatch reproduced, positive control verifies, sole candidate's materialized patch RESOLVED under the official harness. verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real callee) FAILS — the spec is faithful to the real post-patch as_compatible_data (xarray/core/variable.py:220-221). Method: created a base_commit worktree (7c4e2ac8) and applied the gold hunk (getattr(data,'values',data) -> if isinstance(data,(pd.Series,pd.Index,pd.DataFrame)): data=data.values). Ran the bundle's own differential checks against the patched testbed: conformance_check.py = 0 disagreements over 100021 inputs (21 boundary + 100000 fuzz, seed 290520), exit 0; axiom_check.py exit 0; model.py verifies under the pinned Nagini (Verification successful, 7.4s). Independent hand-probes confirmed the model's postcondition on the real callee: (a) recognized containers unwrap to .values content for Series/Index/DataFrame incl. tz/Period/Categorical/datetime/Interval/MultiIndex subclasses; (b) non-recognized .values-bearing objects (the issue's HasValues scalar, array-values, bare) pass through unchanged (self survives). CAVEAT / red-herring: my initial probes showed 'DIVERGE' for WithMasked and WithDatetimeVals — that was only because I first ran against PRE-PATCH code (the bug itself); against the gold-patched callee those vanish. GENUINE-BUT-BELOW-ABSTRACTION subtlety: pd.Index is in NON_NUMPY_SUPPORTED_ARRAY_TYPES and is intercepted at variable.py:207 (early `return _maybe_wrap_data(data)`) BEFORE the modeled step at line 221, so the real surviving OBJECT is the Index itself (wrapped in a lazy PandasIndexAdapter), whereas the model claims survivor==values_identity. This is not spec drift: (1) the model's abstraction (mapping.md §2) is over identity of the value that survives *content-wise*, and np.asarray(PandasIndexAdapter(idx)) == idx.values elementwise for all tested Index kinds (int/float/str/RangeIndex/datetime/tz/period/interval/multi); (2) no observable behavioral difference and no effect on G-RESOLVE; (3) the bundle's content-based conformance oracle (which detects survivor by content, not raw Python identity) reports full agreement. So this is a legitimate modeling choice, not a case where the modeled function disagrees with the real callee on a tested/observable input. Spec region byte-identical to model_prepatch (only impl differs) — no spec tampering. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures) and manual review confirms it. The gold edit is: in xarray/core/variable.py, replace `data = getattr(data, "values", data)` with `if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)): data = data.values`. The spec view discloses NONE of the concrete discriminators of that edit: `as_compatible_data`, `variable.py`, `isinstance`, `getattr`, `pd.Series`, `pd.Index`, `pd.DataFrame`, `pandas`, `DataFrame` all test False in the spec-view text. No diff markers, no patched file path, no narration terms (bug/fix/patch/etc.), and the only distinctive changed symbol (`as_compatible_data`) does not appear in any spec-view identifier or comment. No RELAXED_LEAKAGE.md / relaxed flag. The spec stays at the behavioral-contract altitude already public in problem_statement, which itself states the bug: objects with a `.values` property get silently coerced on storage and should instead be stored as themselves. The spec view's abstract framing — replacement happens ONLY for 'recognized self-describing container kinds the system recognizes', and any other value (incl. one merely exposing `.values`) passes through unchanged — mirrors the problem_statement's expected behavior without revealing WHICH concrete types (the pd.Series/Index/DataFrame list). That concrete type list lives only in hints_text, which is correctly excluded from the leak baseline and is NOT echoed in the spec view. The single spec-view term overlapping a repo concept ('coerced') is itself present verbatim in the public problem_statement. Nothing leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
