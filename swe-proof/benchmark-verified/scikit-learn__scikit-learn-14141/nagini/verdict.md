# P2 adversarial audit — scikit-learn__scikit-learn-14141

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -153,33 +153,10 @@
             or n == name_parallel()))))
     # post-conditions-end
     # impl-start
-    # The dependency roster, assembled exactly as the routine builds it: one
-    # name token per relevant dependency, including the parallel-execution
-    # dependency. Each rostered name becomes a key of the result mapped to the
-    # version observed for that module. (The roster has constant, statically known
-    # membership, so the per-name population is spelled out one entry per name;
-    # refinement.md maps this to the routine's loop over the roster list.)
-    deps = [
-        name_pip(),
-        name_setuptools(),
-        name_sklearn(),
-        name_numpy(),
-        name_scipy(),
-        name_cython(),
-        name_pandas(),
-        name_matplotlib(),
-        name_parallel(),
-    ]  # type: List[int]
-    Assert(len(deps) == 9)
+    # ATTACK: diverge instead of answering (partial-correctness vacuity channel).
+    b = True
+    while b:  # type: ignore
+        Invariant(True)
     deps_info = {}  # type: Dict[int, int]
-    deps_info[name_pip()] = version_of(name_pip())
-    deps_info[name_setuptools()] = version_of(name_setuptools())
-    deps_info[name_sklearn()] = version_of(name_sklearn())
-    deps_info[name_numpy()] = version_of(name_numpy())
-    deps_info[name_scipy()] = version_of(name_scipy())
-    deps_info[name_cython()] = version_of(name_cython())
-    deps_info[name_pandas()] = version_of(name_pandas())
-    deps_info[name_matplotlib()] = version_of(name_matplotlib())
-    deps_info[name_parallel()] = version_of(name_parallel())
     return deps_info
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -153,24 +153,7 @@
             or n == name_parallel()))))
     # post-conditions-end
     # impl-start
-    # The dependency roster, assembled exactly as the routine builds it: one
-    # name token per relevant dependency, including the parallel-execution
-    # dependency. Each rostered name becomes a key of the result mapped to the
-    # version observed for that module. (The roster has constant, statically known
-    # membership, so the per-name population is spelled out one entry per name;
-    # refinement.md maps this to the routine's loop over the roster list.)
-    deps = [
-        name_pip(),
-        name_setuptools(),
-        name_sklearn(),
-        name_numpy(),
-        name_scipy(),
-        name_cython(),
-        name_pandas(),
-        name_matplotlib(),
-        name_parallel(),
-    ]  # type: List[int]
-    Assert(len(deps) == 9)
+    # ATTACK: never store the parallel-execution dependency key.
     deps_info = {}  # type: Dict[int, int]
     deps_info[name_pip()] = version_of(name_pip())
     deps_info[name_setuptools()] = version_of(name_setuptools())
@@ -180,6 +163,5 @@
     deps_info[name_cython()] = version_of(name_cython())
     deps_info[name_pandas()] = version_of(name_pandas())
     deps_info[name_matplotlib()] = version_of(name_matplotlib())
-    deps_info[name_parallel()] = version_of(name_parallel())
     return deps_info
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -153,24 +153,7 @@
             or n == name_parallel()))))
     # post-conditions-end
     # impl-start
-    # The dependency roster, assembled exactly as the routine builds it: one
-    # name token per relevant dependency, including the parallel-execution
-    # dependency. Each rostered name becomes a key of the result mapped to the
-    # version observed for that module. (The roster has constant, statically known
-    # membership, so the per-name population is spelled out one entry per name;
-    # refinement.md maps this to the routine's loop over the roster list.)
-    deps = [
-        name_pip(),
-        name_setuptools(),
-        name_sklearn(),
-        name_numpy(),
-        name_scipy(),
-        name_cython(),
-        name_pandas(),
-        name_matplotlib(),
-        name_parallel(),
-    ]  # type: List[int]
-    Assert(len(deps) == 9)
+    # ATTACK: an out-of-roster key (999) is stored too.
     deps_info = {}  # type: Dict[int, int]
     deps_info[name_pip()] = version_of(name_pip())
     deps_info[name_setuptools()] = version_of(name_setuptools())
@@ -181,5 +164,6 @@
     deps_info[name_pandas()] = version_of(name_pandas())
     deps_info[name_matplotlib()] = version_of(name_matplotlib())
     deps_info[name_parallel()] = version_of(name_parallel())
+    deps_info[999] = version_of(name_pip())
     return deps_info
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -153,24 +153,7 @@
             or n == name_parallel()))))
     # post-conditions-end
     # impl-start
-    # The dependency roster, assembled exactly as the routine builds it: one
-    # name token per relevant dependency, including the parallel-execution
-    # dependency. Each rostered name becomes a key of the result mapped to the
-    # version observed for that module. (The roster has constant, statically known
-    # membership, so the per-name population is spelled out one entry per name;
-    # refinement.md maps this to the routine's loop over the roster list.)
-    deps = [
-        name_pip(),
-        name_setuptools(),
-        name_sklearn(),
-        name_numpy(),
-        name_scipy(),
-        name_cython(),
-        name_pandas(),
-        name_matplotlib(),
-        name_parallel(),
-    ]  # type: List[int]
-    Assert(len(deps) == 9)
+    # ATTACK: joblib key present but bound to the WRONG version marker.
     deps_info = {}  # type: Dict[int, int]
     deps_info[name_pip()] = version_of(name_pip())
     deps_info[name_setuptools()] = version_of(name_setuptools())
@@ -180,6 +163,6 @@
     deps_info[name_cython()] = version_of(name_cython())
     deps_info[name_pandas()] = version_of(name_pandas())
     deps_info[name_matplotlib()] = version_of(name_matplotlib())
-    deps_info[name_parallel()] = version_of(name_parallel())
+    deps_info[name_parallel()] = version_of(name_pip())
     return deps_info
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -153,24 +153,7 @@
             or n == name_parallel()))))
     # post-conditions-end
     # impl-start
-    # The dependency roster, assembled exactly as the routine builds it: one
-    # name token per relevant dependency, including the parallel-execution
-    # dependency. Each rostered name becomes a key of the result mapped to the
-    # version observed for that module. (The roster has constant, statically known
-    # membership, so the per-name population is spelled out one entry per name;
-    # refinement.md maps this to the routine's loop over the roster list.)
-    deps = [
-        name_pip(),
-        name_setuptools(),
-        name_sklearn(),
-        name_numpy(),
-        name_scipy(),
-        name_cython(),
-        name_pandas(),
-        name_matplotlib(),
-        name_parallel(),
-    ]  # type: List[int]
-    Assert(len(deps) == 9)
+    # ATTACK: joblib stored only inside a branch the verifier cannot force true.
     deps_info = {}  # type: Dict[int, int]
     deps_info[name_pip()] = version_of(name_pip())
     deps_info[name_setuptools()] = version_of(name_setuptools())
@@ -180,6 +163,7 @@
     deps_info[name_cython()] = version_of(name_cython())
     deps_info[name_pandas()] = version_of(name_pandas())
     deps_info[name_matplotlib()] = version_of(name_matplotlib())
-    deps_info[name_parallel()] = version_of(name_parallel())
+    if version_of(name_parallel()) == version_of(name_pip()):
+        deps_info[name_parallel()] = version_of(name_parallel())
     return deps_info
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -153,26 +153,9 @@
             or n == name_parallel()))))
     # post-conditions-end
     # impl-start
-    # The dependency roster, assembled exactly as the routine builds it: one
-    # name token per relevant dependency, including the parallel-execution
-    # dependency. Each rostered name becomes a key of the result mapped to the
-    # version observed for that module. (The roster has constant, statically known
-    # membership, so the per-name population is spelled out one entry per name;
-    # refinement.md maps this to the routine's loop over the roster list.)
-    deps = [
-        name_pip(),
-        name_setuptools(),
-        name_sklearn(),
-        name_numpy(),
-        name_scipy(),
-        name_cython(),
-        name_pandas(),
-        name_matplotlib(),
-        name_parallel(),
-    ]  # type: List[int]
-    Assert(len(deps) == 9)
+    # ATTACK: store an ungrounded literal instead of the observed version marker.
     deps_info = {}  # type: Dict[int, int]
-    deps_info[name_pip()] = version_of(name_pip())
+    deps_info[name_pip()] = 0
     deps_info[name_setuptools()] = version_of(name_setuptools())
     deps_info[name_sklearn()] = version_of(name_sklearn())
     deps_info[name_numpy()] = version_of(name_numpy())
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -153,12 +153,9 @@
             or n == name_parallel()))))
     # post-conditions-end
     # impl-start
-    # The dependency roster, assembled exactly as the routine builds it: one
-    # name token per relevant dependency, including the parallel-execution
-    # dependency. Each rostered name becomes a key of the result mapped to the
-    # version observed for that module. (The roster has constant, statically known
-    # membership, so the per-name population is spelled out one entry per name;
-    # refinement.md maps this to the routine's loop over the roster list.)
+    # ATTACK: the roster list omits the parallel dependency (8 names), yet the
+    # dict is populated with all nine explicit assignments. Tests whether the
+    # model's roster<->population decoupling admits a divergent faithful refinement.
     deps = [
         name_pip(),
         name_setuptools(),
@@ -168,9 +165,8 @@
         name_cython(),
         name_pandas(),
         name_matplotlib(),
-        name_parallel(),
     ]  # type: List[int]
-    Assert(len(deps) == 9)
+    Assert(len(deps) == 8)
     deps_info = {}  # type: Dict[int, int]
     deps_info[name_pip()] = version_of(name_pip())
     deps_info[name_setuptools()] = version_of(name_setuptools())
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -153,33 +153,17 @@
             or n == name_parallel()))))
     # post-conditions-end
     # impl-start
-    # The dependency roster, assembled exactly as the routine builds it: one
-    # name token per relevant dependency, including the parallel-execution
-    # dependency. Each rostered name becomes a key of the result mapped to the
-    # version observed for that module. (The roster has constant, statically known
-    # membership, so the per-name population is spelled out one entry per name;
-    # refinement.md maps this to the routine's loop over the roster list.)
-    deps = [
-        name_pip(),
-        name_setuptools(),
-        name_sklearn(),
-        name_numpy(),
-        name_scipy(),
-        name_cython(),
-        name_pandas(),
-        name_matplotlib(),
-        name_parallel(),
-    ]  # type: List[int]
-    Assert(len(deps) == 9)
+    # ATTACK (echo): all nine keys, reordered, joblib stored first and again last.
     deps_info = {}  # type: Dict[int, int]
+    deps_info[name_parallel()] = version_of(name_parallel())
+    deps_info[name_matplotlib()] = version_of(name_matplotlib())
+    deps_info[name_pandas()] = version_of(name_pandas())
+    deps_info[name_cython()] = version_of(name_cython())
+    deps_info[name_scipy()] = version_of(name_scipy())
+    deps_info[name_numpy()] = version_of(name_numpy())
+    deps_info[name_sklearn()] = version_of(name_sklearn())
+    deps_info[name_setuptools()] = version_of(name_setuptools())
     deps_info[name_pip()] = version_of(name_pip())
-    deps_info[name_setuptools()] = version_of(name_setuptools())
-    deps_info[name_sklearn()] = version_of(name_sklearn())
-    deps_info[name_numpy()] = version_of(name_numpy())
-    deps_info[name_scipy()] = version_of(name_scipy())
-    deps_info[name_cython()] = version_of(name_cython())
-    deps_info[name_pandas()] = version_of(name_pandas())
-    deps_info[name_matplotlib()] = version_of(name_matplotlib())
     deps_info[name_parallel()] = version_of(name_parallel())
     return deps_info
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-14141.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A diagnostic routine reports the installed version of each of the project's
  relevant runtime dependencies. It works from a predetermined roster of
  dependency module names; for every name on that roster it records, in the returned
  mapping, an entry keyed by that name whose value is the version observed for
  that module (a version marker, or the absent marker when the module cannot be
  imported). The returned mapping therefore has exactly one entry per name on
  the roster, and a name appears as a key of the result if and only if it is on
  the roster.

  The roster of relevant dependencies must include the parallel-execution
  dependency the project relies on at this version, alongside the package
  manager, the build/packaging helpers, the project itself, the numerical
  array library, the scientific-computing library, the compiled-extension
  toolchain, the dataframe library, and the plotting library. In particular the
  parallel-execution dependency's name must be reported among the result's keys,
  just as every other rostered dependency is.

Modelling choices (Nagini fragment):
  * A dependency module name is an `int` identity token; the nine roster tokens
    (the eight long-standing ones and the parallel-execution dependency) are
    module-level `@Pure` constants (mapping.md ss1). The tested behaviour only
    observes WHICH names appear as keys of the result, so integer identity is
    the faithful carrier (mapping.md ss2).
  * The roster is a `List[int]` of name tokens, built in the impl region exactly
    as the routine builds its dependency roster.
  * The observed version of a module is an unchanged opaque callee (importing
    the module and reading its version, or the absent marker on failure),
    axiomatised as `version_of` -- the value is not observed by the tested
    behaviour, only the presence of the key.
  * The result is a `Dict[int, int]` from a name token to its version marker.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.

Termination: the real routine is loop-free straight-line work (build a static
list, populate a dict, return), so every call returns. Nagini checks partial
correctness by default, so without a termination obligation a same-spec impl
that spins forever satisfies every Ensures vacuously while its real
counterpart would hang the F2P. `Requires(MustTerminate(2))` pins totality; it
adds no behaviour beyond what the real code already has, so it cannot exclude
a correct implementation.
"""
from typing import List, Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def version_of(name: int) -> int:
    """The version marker observed for a dependency module name: the imported
    module's reported version, or the absent marker when the module cannot be
    imported. An unchanged opaque callee (import + version read); its value is
    not part of the tested behaviour. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Ensures(True)
# axioms-end

# pure-start
@Pure
def name_pip() -> int:
    return 0

@Pure
def name_setuptools() -> int:
    return 1

@Pure
def name_sklearn() -> int:
    return 2

@Pure
def name_numpy() -> int:
    return 3

@Pure
def name_scipy() -> int:
    return 4

@Pure
def name_cython() -> int:
    return 5

@Pure
def name_pandas() -> int:
    return 6

@Pure
def name_matplotlib() -> int:
    return 7

@Pure
def name_parallel() -> int:
    # the parallel-execution dependency this version relies on
    return 8
# pure-end

def collect_deps_versions() -> Dict[int, int]:
    # pre-conditions-start
    # No inputs: the roster is predetermined and built internally.
    # Totality obligation: the real _get_deps_info() is loop-free straight-line
    # code — every call returns. Without this, a same-spec impl that diverges
    # (e.g. `while b: Invariant(True)`) verifies vacuously under Nagini's
    # partial-correctness default while its real counterpart hangs the F2P.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # Every pre-existing rostered dependency name is reported as a key of the
    # result, and carries the version observed for that module.
    Ensures(name_pip() in Result()
            and Result()[name_pip()] == version_of(name_pip()))
    Ensures(name_setuptools() in Result()
            and Result()[name_setuptools()] == version_of(name_setuptools()))
    Ensures(name_sklearn() in Result()
            and Result()[name_sklearn()] == version_of(name_sklearn()))
    Ensures(name_numpy() in Result()
            and Result()[name_numpy()] == version_of(name_numpy()))
    Ensures(name_scipy() in Result()
            and Result()[name_scipy()] == version_of(name_scipy()))
    Ensures(name_cython() in Result()
            and Result()[name_cython()] == version_of(name_cython()))
    Ensures(name_pandas() in Result()
            and Result()[name_pandas()] == version_of(name_pandas()))
    Ensures(name_matplotlib() in Result()
            and Result()[name_matplotlib()] == version_of(name_matplotlib()))
    # The discriminating clause: the parallel-execution dependency must also be
    # reported among the result's keys, carrying its observed version.
    Ensures(name_parallel() in Result()
            and Result()[name_parallel()] == version_of(name_parallel()))
    # No spurious keys: every key of the result is one of the rostered names.
    Ensures(Forall(int, lambda n: (Implies(n in Result(),
            n == name_pip() or n == name_setuptools() or n == name_sklearn()
            or n == name_numpy() or n == name_scipy() or n == name_cython()
            or n == name_pandas() or n == name_matplotlib()
            or n == name_parallel()))))
    # post-conditions-end
    # impl-start
    # The dependency roster, assembled exactly as the routine builds it: one
    # name token per relevant dependency, including the parallel-execution
    # dependency. Each rostered name becomes a key of the result mapped to the
    # version observed for that module. (The roster has constant, statically known
    # membership, so the per-name population is spelled out one entry per name;
    # refinement.md maps this to the routine's loop over the roster list.)
    deps = [
        name_pip(),
        name_setuptools(),
        name_sklearn(),
        name_numpy(),
        name_scipy(),
        name_cython(),
        name_pandas(),
        name_matplotlib(),
        name_parallel(),
    ]  # type: List[int]
    Assert(len(deps) == 9)
    deps_info = {}  # type: Dict[int, int]
    deps_info[name_pip()] = version_of(name_pip())
    deps_info[name_setuptools()] = version_of(name_setuptools())
    deps_info[name_sklearn()] = version_of(name_sklearn())
    deps_info[name_numpy()] = version_of(name_numpy())
    deps_info[name_scipy()] = version_of(name_scipy())
    deps_info[name_cython()] = version_of(name_cython())
    deps_info[name_pandas()] = version_of(name_pandas())
    deps_info[name_matplotlib()] = version_of(name_matplotlib())
    deps_info[name_parallel()] = version_of(name_parallel())
    return deps_info
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### Verdict: SOUND

BASELINE: positive_control.py (bundle model.py) same-spec exit 0, VERIFIED 21.6s. prepatch (model_prepatch.py: 8-name roster, no name_parallel() assignment) same-spec exit 0 and fails postcondition name_parallel() in Result() (G-DIFF) -> prepatch bug reproduced.

8 DISTINCT same-spec attacks (all same-spec exit 0), each run through `adversary weakness nagini scikit-learn__scikit-learn-14141 <atk>`:
- atk_1 (control-flow / non-termination: while b: Invariant(True)): NOT-A-COUNTEREXAMPLE, does not verify -> MustTerminate(2) rejects divergence.
- atk_2 (partial-domain: omit joblib assignment, dict form of prepatch bug): NOT-A-COUNTEREXAMPLE, fails name_parallel() in Result().
- atk_3 (boundary/spurious key: also stores deps_info[999]): NOT-A-COUNTEREXAMPLE, fails no-spurious-keys Forall.
- atk_4 (ungrounded-oracle echo: joblib key bound to version_of(name_pip()) not version_of(name_parallel())): NOT-A-COUNTEREXAMPLE, fails value-binding postcondition.
- atk_5 (control-flow-effect: joblib stored only inside `if version_of(name_parallel())==version_of(name_pip())` branch verifier cannot force): NOT-A-COUNTEREXAMPLE.
- atk_6 (ungrounded literal value: deps_info[name_pip()] = 0 instead of version_of): NOT-A-COUNTEREXAMPLE.
- atk_7 (CANDIDATE: deps LIST omits name_parallel() -> 8 entries, but the returned dict receives all 9 explicit assignments incl. joblib): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (20.7s).
- atk_8 (CANDIDATE / echo: all 9 keys reordered, joblib stored first and duplicated last): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (19.4s).

CANDIDATE RESOLVE (mandatory materialize + run_resolve, official harness under `docker`, timeout 1800, retries 0): Both candidates' only observable is Result() (the returned dict). atk_7's 8-element `deps` list is dead/unobserved; its Result() contains all 9 keys incl joblib. atk_8 is a reorder+dup echo. So the FAITHFUL refined patch for BOTH is: add "joblib" to the real _get_deps_info() roster = the gold patch (the population loop `for modname in deps` is unchanged, so the roster IS the observable determinant; a faithful refinement whose real deps_info contains joblib must add joblib to the roster). Materialized patch_atk7.diff == patch_atk8.diff == gold hunk.
  run_resolve('scikit-learn__scikit-learn-14141', gold-hunk) => RESOLVED=True COMPLETED=True NOTE=resolved. Therefore both verifying candidates' faithful patches RESOLVE -> neither breaks the spec.

ORACLE DISCRIMINATION CONTROLS: (a) clean negative control patch_neg.diff (applies to roster region but does NOT add joblib) => RESOLVED=False COMPLETED=True NOTE='patch did not resolve' -- proving the harness genuinely tests joblib presence (F2P test_get_deps_info asserts 'joblib' in deps_info). (b) empty patch => COMPLETED=False (degenerate, un-appliable) -- superseded by patch_neg as the real negative control.

### Exact commands
  export SBU_BENCHMARK_DIR=benchmark-verified
  python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-14141 <atk>   # all 8 + control + prepatch: exit 0
  python -m swebench_unified.adversary verify   nagini scikit-learn__scikit-learn-14141 positive_control.py   # VERIFIED 21.6s
  python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-14141 <atk>   # atk_1..6 exit 2; atk_7, atk_8 exit 0 (CANDIDATE)
  python run_resolve.py patch_gold.diff <run_id>   # (=atk7/atk8 faithful) RESOLVED=True
  python run_resolve.py patch_neg.diff  <run_id>   # RESOLVED=False (control)

REFINEMENT.MD LEG AUDIT: A1=R (str name<->int token; list-of-9<->tokens), A2=R+A-consumed (unroll static-length roster == loop; per-name value consumed via Result()[name_X()]==version_of(name_X())), A3=R (Dict[int,int]<->Dict[str,Optional[str]]), A4=R (MustTerminate(2) totality obligation, closes partial-correctness vacuity; adds no behaviour real code lacks). B1=version_of (A-consumed): weakest total int-valued contract Ensures(True), correspondence to the real per-module import+version observation (lines 54,59-67) validated total by G-AX/axiom_check.py against real _get_deps_info() (every rostered name incl 'joblib' is a key; no spurious keys; import-failure branch keeps key with None).

Section C: NO kind-3 step; the one genuinely-changed op (roster extension) is modeled DEEPLY (name_parallel() explicit 9th token + explicit assignment), NOT hidden behind an axiom about the function-under-change; no A-reference deep model in this bundle. A-legs' correspondence to real callees holds. Spec pins: exact key-set (Forall no-spurious-keys), per-key value binding to version_of, all 9 rostered names present incl name_parallel(), MustTerminate. No verifying wrong impl found whose faithful patch fails to resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-14141.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A diagnostic routine reports the installed version of each of the project's
  relevant runtime dependencies. It works from a predetermined roster of
  dependency module names; for every name on that roster it records, in the returned
  mapping, an entry keyed by that name whose value is the version observed for
  that module (a version marker, or the absent marker when the module cannot be
  imported). The returned mapping therefore has exactly one entry per name on
  the roster, and a name appears as a key of the result if and only if it is on
  the roster.

  The roster of relevant dependencies must include the parallel-execution
  dependency the project relies on at this version, alongside the package
  manager, the build/packaging helpers, the project itself, the numerical
  array library, the scientific-computing library, the compiled-extension
  toolchain, the dataframe library, and the plotting library. In particular the
  parallel-execution dependency's name must be reported among the result's keys,
  just as every other rostered dependency is.

Modelling choices (Nagini fragment):
  * A dependency module name is an `int` identity token; the nine roster tokens
    (the eight long-standing ones and the parallel-execution dependency) are
    module-level `@Pure` constants (mapping.md ss1). The tested behaviour only
    observes WHICH names appear as keys of the result, so integer identity is
    the faithful carrier (mapping.md ss2).
  * The roster is a `List[int]` of name tokens, built in the impl region exactly
    as the routine builds its dependency roster.
  * The observed version of a module is an unchanged opaque callee (importing
    the module and reading its version, or the absent marker on failure),
    axiomatised as `version_of` -- the value is not observed by the tested
    behaviour, only the presence of the key.
  * The result is a `Dict[int, int]` from a name token to its version marker.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.

Termination: the real routine is loop-free straight-line work (build a static
list, populate a dict, return), so every call returns. Nagini checks partial
correctness by default, so without a termination obligation a same-spec impl
that spins forever satisfies every Ensures vacuously while its real
counterpart would hang the F2P. `Requires(MustTerminate(2))` pins totality; it
adds no behaviour beyond what the real code already has, so it cannot exclude
a correct implementation.
"""
from typing import List, Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def version_of(name: int) -> int:
    """The version marker observed for a dependency module name: the imported
    module's reported version, or the absent marker when the module cannot be
    imported. An unchanged opaque callee (import + version read); its value is
    not part of the tested behaviour. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Ensures(True)
# axioms-end

# pure-start
@Pure
def name_pip() -> int:
    return 0

@Pure
def name_setuptools() -> int:
    return 1

@Pure
def name_sklearn() -> int:
    return 2

@Pure
def name_numpy() -> int:
    return 3

@Pure
def name_scipy() -> int:
    return 4

@Pure
def name_cython() -> int:
    return 5

@Pure
def name_pandas() -> int:
    return 6

@Pure
def name_matplotlib() -> int:
    return 7

@Pure
def name_parallel() -> int:
    # the parallel-execution dependency this version relies on
    return 8
# pure-end

def collect_deps_versions() -> Dict[int, int]:
    # pre-conditions-start
    # No inputs: the roster is predetermined and built internally.
    # Totality obligation: the real _get_deps_info() is loop-free straight-line
    # code — every call returns. Without this, a same-spec impl that diverges
    # (e.g. `while b: Invariant(True)`) verifies vacuously under Nagini's
    # partial-correctness default while its real counterpart hangs the F2P.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # Every pre-existing rostered dependency name is reported as a key of the
    # result, and carries the version observed for that module.
    Ensures(name_pip() in Result()
            and Result()[name_pip()] == version_of(name_pip()))
    Ensures(name_setuptools() in Result()
            and Result()[name_setuptools()] == version_of(name_setuptools()))
    Ensures(name_sklearn() in Result()
            and Result()[name_sklearn()] == version_of(name_sklearn()))
    Ensures(name_numpy() in Result()
            and Result()[name_numpy()] == version_of(name_numpy()))
    Ensures(name_scipy() in Result()
            and Result()[name_scipy()] == version_of(name_scipy()))
    Ensures(name_cython() in Result()
            and Result()[name_cython()] == version_of(name_cython()))
    Ensures(name_pandas() in Result()
            and Result()[name_pandas()] == version_of(name_pandas()))
    Ensures(name_matplotlib() in Result()
            and Result()[name_matplotlib()] == version_of(name_matplotlib()))
    # The discriminating clause: the parallel-execution dependency must also be
    # reported among the result's keys, carrying its observed version.
    Ensures(name_parallel() in Result()
            and Result()[name_parallel()] == version_of(name_parallel()))
    # No spurious keys: every key of the result is one of the rostered names.
    Ensures(Forall(int, lambda n: (Implies(n in Result(),
            n == name_pip() or n == name_setuptools() or n == name_sklearn()
            or n == name_numpy() or n == name_scipy() or n == name_cython()
            or n == name_pandas() or n == name_matplotlib()
            or n == name_parallel()))))
    # post-conditions-end
    # impl-start
    # The dependency roster, assembled exactly as the routine builds it: one
    # name token per relevant dependency, including the parallel-execution
    # dependency. Each rostered name becomes a key of the result mapped to the
    # version observed for that module. (The roster has constant, statically known
    # membership, so the per-name population is spelled out one entry per name;
    # refinement.md maps this to the routine's loop over the roster list.)
    deps = [
        name_pip(),
        name_setuptools(),
        name_sklearn(),
        name_numpy(),
        name_scipy(),
        name_cython(),
        name_pandas(),
        name_matplotlib(),
        name_parallel(),
    ]  # type: List[int]
    Assert(len(deps) == 9)
    deps_info = {}  # type: Dict[int, int]
    deps_info[name_pip()] = version_of(name_pip())
    deps_info[name_setuptools()] = version_of(name_setuptools())
    deps_info[name_sklearn()] = version_of(name_sklearn())
    deps_info[name_numpy()] = version_of(name_numpy())
    deps_info[name_scipy()] = version_of(name_scipy())
    deps_info[name_cython()] = version_of(name_cython())
    deps_info[name_pandas()] = version_of(name_pandas())
    deps_info[name_matplotlib()] = version_of(name_matplotlib())
    deps_info[name_parallel()] = version_of(name_parallel())
    return deps_info
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### Verdict: SOUND

BASELINE: positive_control.py (bundle model.py) same-spec exit 0, VERIFIED 21.6s. prepatch (model_prepatch.py: 8-name roster, no name_parallel() assignment) same-spec exit 0 and fails postcondition name_parallel() in Result() (G-DIFF) -> prepatch bug reproduced.

8 DISTINCT same-spec attacks (all same-spec exit 0), each run through `adversary weakness nagini scikit-learn__scikit-learn-14141 <atk>`:
- atk_1 (control-flow / non-termination: while b: Invariant(True)): NOT-A-COUNTEREXAMPLE, does not verify -> MustTerminate(2) rejects divergence.
- atk_2 (partial-domain: omit joblib assignment, dict form of prepatch bug): NOT-A-COUNTEREXAMPLE, fails name_parallel() in Result().
- atk_3 (boundary/spurious key: also stores deps_info[999]): NOT-A-COUNTEREXAMPLE, fails no-spurious-keys Forall.
- atk_4 (ungrounded-oracle echo: joblib key bound to version_of(name_pip()) not version_of(name_parallel())): NOT-A-COUNTEREXAMPLE, fails value-binding postcondition.
- atk_5 (control-flow-effect: joblib stored only inside `if version_of(name_parallel())==version_of(name_pip())` branch verifier cannot force): NOT-A-COUNTEREXAMPLE.
- atk_6 (ungrounded literal value: deps_info[name_pip()] = 0 instead of version_of): NOT-A-COUNTEREXAMPLE.
- atk_7 (CANDIDATE: deps LIST omits name_parallel() -> 8 entries, but the returned dict receives all 9 explicit assignments incl. joblib): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (20.7s).
- atk_8 (CANDIDATE / echo: all 9 keys reordered, joblib stored first and duplicated last): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (19.4s).

CANDIDATE RESOLVE (mandatory materialize + run_resolve, official harness under `docker`, timeout 1800, retries 0): Both candidates' only observable is Result() (the returned dict). atk_7's 8-element `deps` list is dead/unobserved; its Result() contains all 9 keys incl joblib. atk_8 is a reorder+dup echo. So the FAITHFUL refined patch for BOTH is: add "joblib" to the real _get_deps_info() roster = the gold patch (the population loop `for modname in deps` is unchanged, so the roster IS the observable determinant; a faithful refinement whose real deps_info contains joblib must add joblib to the roster). Materialized patch_atk7.diff == patch_atk8.diff == gold hunk.
  run_resolve('scikit-learn__scikit-learn-14141', gold-hunk) => RESOLVED=True COMPLETED=True NOTE=resolved. Therefore both verifying candidates' faithful patches RESOLVE -> neither breaks the spec.

ORACLE DISCRIMINATION CONTROLS: (a) clean negative control patch_neg.diff (applies to roster region but does NOT add joblib) => RESOLVED=False COMPLETED=True NOTE='patch did not resolve' -- proving the harness genuinely tests joblib presence (F2P test_get_deps_info asserts 'joblib' in deps_info). (b) empty patch => COMPLETED=False (degenerate, un-appliable) -- superseded by patch_neg as the real negative control.

### Exact commands
  export SBU_BENCHMARK_DIR=benchmark-verified
  python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-14141 <atk>   # all 8 + control + prepatch: exit 0
  python -m swebench_unified.adversary verify   nagini scikit-learn__scikit-learn-14141 positive_control.py   # VERIFIED 21.6s
  python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-14141 <atk>   # atk_1..6 exit 2; atk_7, atk_8 exit 0 (CANDIDATE)
  python run_resolve.py patch_gold.diff <run_id>   # (=atk7/atk8 faithful) RESOLVED=True
  python run_resolve.py patch_neg.diff  <run_id>   # RESOLVED=False (control)

REFINEMENT.MD LEG AUDIT: A1=R (str name<->int token; list-of-9<->tokens), A2=R+A-consumed (unroll static-length roster == loop; per-name value consumed via Result()[name_X()]==version_of(name_X())), A3=R (Dict[int,int]<->Dict[str,Optional[str]]), A4=R (MustTerminate(2) totality obligation, closes partial-correctness vacuity; adds no behaviour real code lacks). B1=version_of (A-consumed): weakest total int-valued contract Ensures(True), correspondence to the real per-module import+version observation (lines 54,59-67) validated total by G-AX/axiom_check.py against real _get_deps_info() (every rostered name incl 'joblib' is a key; no spurious keys; import-failure branch keeps key with None).

Section C: NO kind-3 step; the one genuinely-changed op (roster extension) is modeled DEEPLY (name_parallel() explicit 9th token + explicit assignment), NOT hidden behind an axiom about the function-under-change; no A-reference deep model in this bundle. A-legs' correspondence to real callees holds. Spec pins: exact key-set (Forall no-spurious-keys), per-key value binding to version_of, all 9 rostered names present incl name_parallel(), MustTerminate. No verifying wrong impl found whose faithful patch fails to resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / too-strong) check for the nagini model of _get_deps_info(). The base_commit worktree is pre-patch (8 deps); the bundle correctly models the POST-patch gold behavior (9-name roster incl. 'joblib'), which is what G-RESOLVE resolves against. Model verifies (nagini_verify exit 0, 16.9s).

Real post-patch _get_deps_info(): deps_info is built SOLELY by the loop over the static 9-name deps list [pip,setuptools,sklearn,numpy,scipy,Cython,pandas,matplotlib,joblib]; each iteration adds exactly one key = modname, value = version or None (except ImportError keeps the key). So the result key-set is EXACTLY those 9 names — every rostered name present, no spurious keys.

Spec postconditions match exactly: (a) each of the 9 name_*() tokens in Result carrying version_of(name); (b) Forall n. n in Result ⇒ n is one of the 9 tokens. Neither clause over-claims — the gold function satisfies all of them, so the spec is not too strong. The postconditions are precisely the tested observable (test_get_deps_info asserts 'joblib' in deps_info; key-presence only, never values).

Type abstraction is a faithful bijection: distinct str names ↔ distinct int tokens 0..8, Dict[str,Optional[str]] ↔ Dict[int,int], values opaque via version_of(Ensures(True)) — tested behavior observes only key presence. version_of-as-total is sound: the real loop's try/except ImportError stores None otherwise, so every rostered name becomes a key (matches totality); the only real inputs are the 9 installed deps whose modules have __version__, so no AttributeError raise path is reachable in the tested domain. MustTerminate(2) reflects the real loop-free straight-line routine and excludes no correct impl.

No input exists on which the modeled function disagrees with the real (patched) callee. Spec is FAITHFUL; it also correctly senses the change (model_prepatch fails name_parallel() in Result()).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = the elided model.py (docstring + spec/pre/post regions; impl replaced by `...`). Public problem_statement already discloses the gold edit at full specificity: 'Add joblib in show_versions ... joblib should be added to the dependencies listed in show_versions'. The gold patch merely appends the literal "joblib" to the deps list in _get_deps_info().

The spec view is STRICTLY LESS revealing than the problem_statement about the edit:
- It never names 'joblib' — the discriminating dependency is abstracted as 'the parallel-execution dependency' / name_parallel() (token 8). It never inspects/echoes the string.
- It never names the patched file (sklearn/utils/_show_versions.py) or the patched symbol (_get_deps_info); model uses collect_deps_versions / int identity tokens. That binding lives only in mapping.md/refinement.md, which are NOT part of the spec view.
- The other eight rostered names (pip, setuptools, sklearn, numpy, scipy, cython, pandas, matplotlib) are pre-existing public code, not the edit; enumerating them localizes nothing.
- No diff markers, no reproduced gold-diff line, no patched path, no bug/fix narration.

Mechanical G-LEAK screen (leakage.screen over spec_view) PASSES: hard_failures=[], warnings=[]. hints_text is empty and irrelevant. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.