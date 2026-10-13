# P2 adversarial audit — matplotlib__matplotlib-23299

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch.py`, `atk_2_no_revert_other.py`, `atk_3_diverge.py`, `atk_4_spurious.py`, `atk_6_partial_domain.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5_echo.py`, `atk_7_direct.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_8_del_drop.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,19 +123,19 @@
                                           k in params and params[k] == Old(params[k]))))
     # post-conditions-end
     # impl-start
-    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
-    # distinguished key from the snapshot. The net data flow — a snapshot that
-    # excludes the distinguished key — is realised here by recording into the
-    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
-    # key, but NOT the distinguished key.
+    # Snapshot the mapping (orig = rcParams.copy()): record BOTH observed keys'
+    # entry values, including the distinguished key.
     saved = {}  # type: Dict[int, int]
+    saved[key_resolved()] = params[key_resolved()]
     saved[key_other()] = params[key_other()]
     # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
     params[key_resolved()] = new_resolved
     params[key_other()] = other_override
-    # Restore (dict.update over the snapshot's keys): the snapshot covers only
-    # the ordinary key, so only it is reverted; the distinguished key, absent
-    # from the snapshot, keeps the body-set value.
+    # Restore (dict.update over the snapshot's keys): the snapshot covers BOTH
+    # keys, so both are reverted to their entry values — the value set inside the
+    # context for the distinguished key does not survive.
+    if key_resolved() in saved:
+        params[key_resolved()] = saved[key_resolved()]
     if key_other() in saved:
         params[key_other()] = saved[key_other()]
     # impl-end
```

Attack 2 — `atk_2_no_revert_other.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,19 +123,11 @@
                                           k in params and params[k] == Old(params[k]))))
     # post-conditions-end
     # impl-start
-    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
-    # distinguished key from the snapshot. The net data flow — a snapshot that
-    # excludes the distinguished key — is realised here by recording into the
-    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
-    # key, but NOT the distinguished key.
+
+    # WRONG: snapshot then OVERRIDE the ordinary key but never revert it.
     saved = {}  # type: Dict[int, int]
     saved[key_other()] = params[key_other()]
-    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
     params[key_resolved()] = new_resolved
     params[key_other()] = other_override
-    # Restore (dict.update over the snapshot's keys): the snapshot covers only
-    # the ordinary key, so only it is reverted; the distinguished key, absent
-    # from the snapshot, keeps the body-set value.
-    if key_other() in saved:
-        params[key_other()] = saved[key_other()]
+    # (revert deliberately omitted: key_other keeps the body override)
     # impl-end
```

Attack 3 — `atk_3_diverge.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,19 +123,15 @@
                                           k in params and params[k] == Old(params[k]))))
     # post-conditions-end
     # impl-start
-    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
-    # distinguished key from the snapshot. The net data flow — a snapshot that
-    # excludes the distinguished key — is realised here by recording into the
-    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
-    # key, but NOT the distinguished key.
+
+    # WRONG: establish the post-state then spin forever (partial correctness
+    # would satisfy every postcondition vacuously; MustTerminate must reject).
     saved = {}  # type: Dict[int, int]
     saved[key_other()] = params[key_other()]
-    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
     params[key_resolved()] = new_resolved
     params[key_other()] = other_override
-    # Restore (dict.update over the snapshot's keys): the snapshot covers only
-    # the ordinary key, so only it is reverted; the distinguished key, absent
-    # from the snapshot, keeps the body-set value.
     if key_other() in saved:
         params[key_other()] = saved[key_other()]
+    while new_resolved == new_resolved:
+        pass
     # impl-end
```

Attack 4 — `atk_4_spurious.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,19 +123,14 @@
                                           k in params and params[k] == Old(params[k]))))
     # post-conditions-end
     # impl-start
-    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
-    # distinguished key from the snapshot. The net data flow — a snapshot that
-    # excludes the distinguished key — is realised here by recording into the
-    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
-    # key, but NOT the distinguished key.
+
+    # WRONG: correct revert, but the restore INVENTS a key (2) that need not
+    # have been present on entry.
     saved = {}  # type: Dict[int, int]
     saved[key_other()] = params[key_other()]
-    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
     params[key_resolved()] = new_resolved
     params[key_other()] = other_override
-    # Restore (dict.update over the snapshot's keys): the snapshot covers only
-    # the ordinary key, so only it is reverted; the distinguished key, absent
-    # from the snapshot, keeps the body-set value.
     if key_other() in saved:
         params[key_other()] = saved[key_other()]
+    params[key_other() + 1] = new_resolved
     # impl-end
```

Attack 5 — `atk_5_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -123,19 +123,14 @@
                                           k in params and params[k] == Old(params[k]))))
     # post-conditions-end
     # impl-start
-    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
-    # distinguished key from the snapshot. The net data flow — a snapshot that
-    # excludes the distinguished key — is realised here by recording into the
-    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
-    # key, but NOT the distinguished key.
+
+    # ECHO of the gold: snapshot BOTH keys, override both, then revert ONLY the
+    # ordinary key (distinguished key excluded from the revert -> survives).
     saved = {}  # type: Dict[int, int]
+    saved[key_resolved()] = params[key_resolved()]
     saved[key_other()] = params[key_other()]
-    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
     params[key_resolved()] = new_resolved
     params[key_other()] = other_override
-    # Restore (dict.update over the snapshot's keys): the snapshot covers only
-    # the ordinary key, so only it is reverted; the distinguished key, absent
-    # from the snapshot, keeps the body-set value.
-    if key_other() in saved:
-        params[key_other()] = saved[key_other()]
+    # revert excludes the distinguished key
+    params[key_other()] = saved[key_other()]
     # impl-end
```

Attack 6 — `atk_6_partial_domain.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,19 +123,13 @@
                                           k in params and params[k] == Old(params[k]))))
     # post-conditions-end
     # impl-start
-    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
-    # distinguished key from the snapshot. The net data flow — a snapshot that
-    # excludes the distinguished key — is realised here by recording into the
-    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
-    # key, but NOT the distinguished key.
+
+    # WRONG (partial-domain): only revert the ordinary key on SOME inputs.
     saved = {}  # type: Dict[int, int]
     saved[key_other()] = params[key_other()]
-    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
     params[key_resolved()] = new_resolved
     params[key_other()] = other_override
-    # Restore (dict.update over the snapshot's keys): the snapshot covers only
-    # the ordinary key, so only it is reverted; the distinguished key, absent
-    # from the snapshot, keeps the body-set value.
-    if key_other() in saved:
-        params[key_other()] = saved[key_other()]
+    if new_resolved != entry_resolved:
+        if key_other() in saved:
+            params[key_other()] = saved[key_other()]
     # impl-end
```

Attack 7 — `atk_7_direct.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -123,19 +123,9 @@
                                           k in params and params[k] == Old(params[k]))))
     # post-conditions-end
     # impl-start
-    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
-    # distinguished key from the snapshot. The net data flow — a snapshot that
-    # excludes the distinguished key — is realised here by recording into the
-    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
-    # key, but NOT the distinguished key.
-    saved = {}  # type: Dict[int, int]
-    saved[key_other()] = params[key_other()]
-    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
+
+    # Achieve the exact post-state directly, no snapshot: distinguished key gets
+    # the body value, ordinary key set straight to its entry value.
     params[key_resolved()] = new_resolved
-    params[key_other()] = other_override
-    # Restore (dict.update over the snapshot's keys): the snapshot covers only
-    # the ordinary key, so only it is reverted; the distinguished key, absent
-    # from the snapshot, keeps the body-set value.
-    if key_other() in saved:
-        params[key_other()] = saved[key_other()]
+    params[key_other()] = entry_other
     # impl-end
```

Attack 8 — `atk_8_del_drop.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -123,19 +123,15 @@
                                           k in params and params[k] == Old(params[k]))))
     # post-conditions-end
     # impl-start
-    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
-    # distinguished key from the snapshot. The net data flow — a snapshot that
-    # excludes the distinguished key — is realised here by recording into the
-    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
-    # key, but NOT the distinguished key.
+
+    # ATTACK: revert correctly, then DROP the ordinary key (del). If del were in
+    # the fragment and clause 4 vacuous on absent keys, a dropped key would slip
+    # past -> its faithful patch would break P2P. (del is expected out-of-fragment.)
     saved = {}  # type: Dict[int, int]
     saved[key_other()] = params[key_other()]
-    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
     params[key_resolved()] = new_resolved
     params[key_other()] = other_override
-    # Restore (dict.update over the snapshot's keys): the snapshot covers only
-    # the ordinary key, so only it is reverted; the distinguished key, absent
-    # from the snapshot, keeps the body-set value.
     if key_other() in saved:
         params[key_other()] = saved[key_other()]
+    del params[key_other()]
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-23299.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A context manager temporarily overrides entries of a settings mapping: on
  entry it snapshots the mapping, the body it guards may override some entries,
  and on exit it reverts the snapshotted entries. One distinguished key
  (`key_resolved()`) is special: a value written to it inside the context must
  SURVIVE the context's exit, rather than being reverted to the entry value
  along with the ordinary keys. Concretely, after the context exits:

  (1) the distinguished key holds exactly the value the body set inside the
      context (it is NOT reverted to its entry value);
  (2) every ordinary key the snapshot covered is reverted to its entry value
      (the temporary override is undone);
  (3) the restore introduces no key that the mapping did not already carry.

  The consequence that matters: a value established for the distinguished key
  within the context is preserved across the exit, so a later read of that key
  observes the value set inside — not a stale entry value that would force the
  distinguished setting to be re-derived.

Modelling choices (Nagini fragment):
  * The settings mapping is a ``Dict[int, int]`` from a key token to a value
    token; only the membership and values of the two observed keys matter, so
    integer identity is the faithful carrier (mapping.md §2). The distinguished
    key is the module-level constant ``key_resolved()``; a representative
    ordinary key is ``key_other()``.
  * The body's only observable effect on the tested behaviour is the value each
    key holds just before the exit-time revert, captured as the explicit
    parameters ``new_resolved`` (the body's write to the distinguished key) and
    ``other_override`` (the body's write to the ordinary key). The entry values
    are pinned by the parameters ``entry_resolved`` / ``entry_other``, which are
    genuine pre-state facts about the input.

The mapping is genuinely mutated in place, so it is held at FULL permission and
its exact post-state is stated. No string indexing is used (Nagini bans it).
The whole behaviour is modelled deeply (snapshot, the distinguished-key drop,
and the per-key revert are spelled out in the impl region); there is no
axiomatised callee. The restore must actually COMPLETE and hand control back:
Nagini checks partial correctness by default, so a diverging body would satisfy
every post-state claim vacuously; the contract therefore carries an explicit
``MustTerminate`` obligation rejecting non-terminating implementations.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the snapshot, the distinguished-key drop, and the per-key revert
# are the behaviour under specification and are spelled out deeply in the impl
# region over a real Dict[int,int]. There is no unchanged opaque callee to
# axiomatise — only CPython dict primitives (copy / del / update), validated as
# an A-reference by axiom_check.py (G-AX).
# axioms-end


# pure-start
@Pure
def key_resolved() -> int:
    # The distinguished key whose body-set value must survive the context exit.
    return 0


@Pure
def key_other() -> int:
    # A representative ordinary key whose body-set value is reverted on exit.
    return 1
# pure-end


def restore_after_temporary_overrides(params: Dict[int, int],
                                      entry_resolved: int,
                                      entry_other: int,
                                      new_resolved: int,
                                      other_override: int) -> None:
    # pre-conditions-start
    # The restore must terminate: a diverging exit path would satisfy any
    # post-state claim vacuously (partial correctness), so termination is an
    # explicit obligation. The work is bounded and loop-free, so measure 2
    # suffices.
    Requires(MustTerminate(2))
    # The mapping is genuinely mutated, so FULL permission is required.
    Requires(Acc(dict_pred(params)))
    # Both observed keys are present on entry, and the parameters pin their
    # entry values. These are pre-state facts about the input, bound before any
    # mutation, so the survive/revert guarantees gate on the genuine entry state
    # rather than on a membership query an implementation could perturb.
    Requires(key_resolved() in params)
    Requires(key_other() in params)
    Requires(params[key_resolved()] == entry_resolved)
    Requires(params[key_other()] == entry_other)
    # The two observed keys are distinct (the distinguished key is not the
    # ordinary key).
    Requires(key_resolved() != key_other())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(params)))
    # (1) The distinguished key SURVIVES: after exit it holds the value the body
    #     set inside the context (new_resolved), NOT the entry value. This is the
    #     guarantee the change introduces — the temporary-override revert must
    #     leave this key alone.
    Ensures(key_resolved() in params)
    Ensures(params[key_resolved()] == new_resolved)
    # (2) The ordinary key is REVERTED: after exit it holds its entry value,
    #     undoing the body's temporary override.
    Ensures(key_other() in params)
    Ensures(params[key_other()] == entry_other)
    # (3) The restore introduces no key the mapping did not already carry: any
    #     key present on exit must have been present on entry. Stated forward so
    #     it constrains body/restore-added keys.
    Ensures(Forall(int, lambda k: (Implies(k in params, Old(k in params)))))
    # (4) FRAME / full-revert: every key present on entry, other than the
    #     distinguished key, is reverted to its entry value (ordinary keys
    #     are restored, not corrupted/dropped). This pins the full-revert
    #     behaviour in the spec — the snapshot's temporary override is undone
    #     for ALL non-distinguished keys, not merely the one observed ordinary
    #     key — so an impl that corrupts any third pre-existing key cannot
    #     satisfy the contract.
    Ensures(Forall(int, lambda k: Implies(k in params and k != key_resolved(),
                                          k in params and params[k] == Old(params[k]))))
    # post-conditions-end
    # impl-start
    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
    # distinguished key from the snapshot. The net data flow — a snapshot that
    # excludes the distinguished key — is realised here by recording into the
    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
    # key, but NOT the distinguished key.
    saved = {}  # type: Dict[int, int]
    saved[key_other()] = params[key_other()]
    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
    params[key_resolved()] = new_resolved
    params[key_other()] = other_override
    # Restore (dict.update over the snapshot's keys): the snapshot covers only
    # the ordinary key, so only it is reverted; the distinguished key, absent
    # from the snapshot, keeps the body-set value.
    if key_other() in saved:
        params[key_other()] = saved[key_other()]
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for matplotlib__matplotlib-23299 (nagini).

BASELINE: positive_control.py (verbatim model.py) VERIFIES (bash scripts/nagini_verify.sh -> exit 0, 16.6s). atk_1_prepatch.py (verbatim model_prepatch.py) FAILS the survive postcondition `params[key_resolved()] == new_resolved` (exit 1) -> prepatch bug reproduced (G-DIFF sense confirmed).

ATTACK BATTERY (all 8 confirmed same-spec via `adversary same-spec`; spec/@Pure/Requires/Ensures byte-identical, only impl region edited). weakness command: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-23299 <atk>`; direct reject reason via nagini_verify.sh. Ran in background batches of <=3 (each = JVM+Z3).
  * atk_1_prepatch (control-flow: snapshots+reverts distinguished key): NOT-A-COUNTEREXAMPLE, fails survive postcond (exit1).
  * atk_2_no_revert_other (control-flow-effect: never reverts ordinary key): NOT-A-COUNTEREXAMPLE, fails revert clause (2) `params[key_other()]==entry_other` (exit1).
  * atk_3_diverge (non-termination: establishes post-state then `while: pass`): NOT-A-COUNTEREXAMPLE, fails 'Obligation leak check' i.e. MustTerminate(2) (exit1). Confirms partial-correctness hole is closed.
  * atk_4_spurious (ungrounded/boundary: invents key key_other()+1): NOT-A-COUNTEREXAMPLE, fails no-spurious-key clause (3) Forall(k in params -> Old(k in params)) (exit1).
  * atk_5_echo (gold-faithful echo: snapshot BOTH keys, revert only ordinary key): CANDIDATE (same-spec AND verifies, exit0). Faithful patch = gold `del orig['backend']` structure. run_resolve -> RESOLVED=True completed=True (not flaky).
  * atk_6_partial_domain (partial-domain: revert ordinary key only when new_resolved!=entry_resolved): NOT-A-COUNTEREXAMPLE, fails revert clause (2) (exit1).
  * atk_7_direct (direct post-state, no snapshot: params[key_resolved()]=new_resolved; params[key_other()]=entry_other): CANDIDATE (same-spec AND verifies, exit0). Faithful patch realized as `orig.pop('backend', None)` (behaviorally identical net snapshot-minus-backend). run_resolve -> RESOLVED=True completed=True (not flaky).
  * atk_8_del_drop (drop attack: revert then `del params[key_other()]`): NOT-A-COUNTEREXAMPLE, rejected by Nagini as 'Not supported: del' (out-of-fragment parse error, exit1) -> a front-end refusal, not a spec ruling: the drop SHAPE is unexpressible in nagini's fragment, so clause (3)/(4) went untested against a dropped key and this attack does not settle whether they would reject a translatable drop rival.

RESOLVE (official harness, run_resolve, image swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-23299:latest, timeout 1800): patch_atk5 RESOLVED, patch_atk7 RESOLVED, and gold-patch positive control RESOLVED (harness path validated). Every verifying candidate's materialized faithful refined patch RESOLVES -> verify does NOT admit an unresolved impl. F2P: test_no_backend_reset_rccontext.

WHY SOUND (verify=>correct holds): the spec fully pins the observable mapping post-state: (1) survive `params[key_resolved()]==new_resolved`; (2) revert `params[key_other()]==entry_other`; (3) no-spurious-key forward Forall; (4) FRAME/full-revert Forall(k != key_resolved() -> params[k]==Old(params[k])) subsuming all non-distinguished pre-existing keys; plus MustTerminate(2). Any impl that verifies against this contract yields exactly the gold's mapping state on the tested input, so its faithful patch resolves. The two verifying attacks are genuine echoes of the gold and both resolve.

REFINEMENT.md LEG AUDIT (task §4 leg-kind + A-correspondence): A1 (RcParams->Dict[int,int])=R; A2 ('backend'->key_resolved()==0)=R; A3 (non-backend key->key_other()==1)=R; A4 (snapshot-excluding-distinguished <-> dict(rcParams.copy());del orig['backend'])=R + A-reference; A5 (body writes <-> yield/rcParams.update)=R; A6 (per-key revert <-> dict.update(rcParams,orig))=R + A-reference. NO kind-3 (unexpressible-changed-op) leg; NO consumed @ContractOnly axiom (axioms list empty). The two A-reference legs (A4,A6) correspond to real CPython dict copy/del/update primitives the gold composes; axiom_check.py reproduces the gold's exact control flow over a real dict and passes: 'G-AX OK ... 7 boundary + 20000 fuzz cases' (exit0). Correspondence holds.

VERDICT: SOUND. 8 distinct same-spec attacks run; the 5 wrong impls that reached the verifier are each rejected for the correct spec-relevant reason (revert/frame/no-spurious/terminate), and the 6th (del-drop) was refused by the front end rather than judged by the spec; the 2 verifying impls are gold echoes whose faithful patches both RESOLVE under the official harness. No verifying-but-unresolved impl exists among the attacks; spec is not too weak.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch.py`, `atk_2_no_revert_other.py`, `atk_3_diverge.py`, `atk_4_spurious.py`, `atk_6_partial_domain.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5_echo.py`, `atk_7_direct.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_8_del_drop.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_no_revert_other.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_diverge.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_spurious.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_partial_domain.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_direct.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_del_drop.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-23299.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A context manager temporarily overrides entries of a settings mapping: on
  entry it snapshots the mapping, the body it guards may override some entries,
  and on exit it reverts the snapshotted entries. One distinguished key
  (`key_resolved()`) is special: a value written to it inside the context must
  SURVIVE the context's exit, rather than being reverted to the entry value
  along with the ordinary keys. Concretely, after the context exits:

  (1) the distinguished key holds exactly the value the body set inside the
      context (it is NOT reverted to its entry value);
  (2) every ordinary key the snapshot covered is reverted to its entry value
      (the temporary override is undone);
  (3) the restore introduces no key that the mapping did not already carry.

  The consequence that matters: a value established for the distinguished key
  within the context is preserved across the exit, so a later read of that key
  observes the value set inside — not a stale entry value that would force the
  distinguished setting to be re-derived.

Modelling choices (Nagini fragment):
  * The settings mapping is a ``Dict[int, int]`` from a key token to a value
    token; only the membership and values of the two observed keys matter, so
    integer identity is the faithful carrier (mapping.md §2). The distinguished
    key is the module-level constant ``key_resolved()``; a representative
    ordinary key is ``key_other()``.
  * The body's only observable effect on the tested behaviour is the value each
    key holds just before the exit-time revert, captured as the explicit
    parameters ``new_resolved`` (the body's write to the distinguished key) and
    ``other_override`` (the body's write to the ordinary key). The entry values
    are pinned by the parameters ``entry_resolved`` / ``entry_other``, which are
    genuine pre-state facts about the input.

The mapping is genuinely mutated in place, so it is held at FULL permission and
its exact post-state is stated. No string indexing is used (Nagini bans it).
The whole behaviour is modelled deeply (snapshot, the distinguished-key drop,
and the per-key revert are spelled out in the impl region); there is no
axiomatised callee. The restore must actually COMPLETE and hand control back:
Nagini checks partial correctness by default, so a diverging body would satisfy
every post-state claim vacuously; the contract therefore carries an explicit
``MustTerminate`` obligation rejecting non-terminating implementations.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the snapshot, the distinguished-key drop, and the per-key revert
# are the behaviour under specification and are spelled out deeply in the impl
# region over a real Dict[int,int]. There is no unchanged opaque callee to
# axiomatise — only CPython dict primitives (copy / del / update), validated as
# an A-reference by axiom_check.py (G-AX).
# axioms-end


# pure-start
@Pure
def key_resolved() -> int:
    # The distinguished key whose body-set value must survive the context exit.
    return 0


@Pure
def key_other() -> int:
    # A representative ordinary key whose body-set value is reverted on exit.
    return 1
# pure-end


def restore_after_temporary_overrides(params: Dict[int, int],
                                      entry_resolved: int,
                                      entry_other: int,
                                      new_resolved: int,
                                      other_override: int) -> None:
    # pre-conditions-start
    # The restore must terminate: a diverging exit path would satisfy any
    # post-state claim vacuously (partial correctness), so termination is an
    # explicit obligation. The work is bounded and loop-free, so measure 2
    # suffices.
    Requires(MustTerminate(2))
    # The mapping is genuinely mutated, so FULL permission is required.
    Requires(Acc(dict_pred(params)))
    # Both observed keys are present on entry, and the parameters pin their
    # entry values. These are pre-state facts about the input, bound before any
    # mutation, so the survive/revert guarantees gate on the genuine entry state
    # rather than on a membership query an implementation could perturb.
    Requires(key_resolved() in params)
    Requires(key_other() in params)
    Requires(params[key_resolved()] == entry_resolved)
    Requires(params[key_other()] == entry_other)
    # The two observed keys are distinct (the distinguished key is not the
    # ordinary key).
    Requires(key_resolved() != key_other())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(params)))
    # (1) The distinguished key SURVIVES: after exit it holds the value the body
    #     set inside the context (new_resolved), NOT the entry value. This is the
    #     guarantee the change introduces — the temporary-override revert must
    #     leave this key alone.
    Ensures(key_resolved() in params)
    Ensures(params[key_resolved()] == new_resolved)
    # (2) The ordinary key is REVERTED: after exit it holds its entry value,
    #     undoing the body's temporary override.
    Ensures(key_other() in params)
    Ensures(params[key_other()] == entry_other)
    # (3) The restore introduces no key the mapping did not already carry: any
    #     key present on exit must have been present on entry. Stated forward so
    #     it constrains body/restore-added keys.
    Ensures(Forall(int, lambda k: (Implies(k in params, Old(k in params)))))
    # (4) FRAME / full-revert: every key present on entry, other than the
    #     distinguished key, is reverted to its entry value (ordinary keys
    #     are restored, not corrupted/dropped). This pins the full-revert
    #     behaviour in the spec — the snapshot's temporary override is undone
    #     for ALL non-distinguished keys, not merely the one observed ordinary
    #     key — so an impl that corrupts any third pre-existing key cannot
    #     satisfy the contract.
    Ensures(Forall(int, lambda k: Implies(k in params and k != key_resolved(),
                                          k in params and params[k] == Old(params[k]))))
    # post-conditions-end
    # impl-start
    # Snapshot the mapping (orig = dict(rcParams.copy())), then drop the
    # distinguished key from the snapshot. The net data flow — a snapshot that
    # excludes the distinguished key — is realised here by recording into the
    # snapshot only the keys the exit-time revert is meant to touch: the ordinary
    # key, but NOT the distinguished key.
    saved = {}  # type: Dict[int, int]
    saved[key_other()] = params[key_other()]
    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
    params[key_resolved()] = new_resolved
    params[key_other()] = other_override
    # Restore (dict.update over the snapshot's keys): the snapshot covers only
    # the ordinary key, so only it is reverted; the distinguished key, absent
    # from the snapshot, keeps the body-set value.
    if key_other() in saved:
        params[key_other()] = saved[key_other()]
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for matplotlib__matplotlib-23299 (nagini).

BASELINE: positive_control.py (verbatim model.py) VERIFIES (bash scripts/nagini_verify.sh -> exit 0, 16.6s). atk_1_prepatch.py (verbatim model_prepatch.py) FAILS the survive postcondition `params[key_resolved()] == new_resolved` (exit 1) -> prepatch bug reproduced (G-DIFF sense confirmed).

ATTACK BATTERY (all 8 confirmed same-spec via `adversary same-spec`; spec/@Pure/Requires/Ensures byte-identical, only impl region edited). weakness command: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-23299 <atk>`; direct reject reason via nagini_verify.sh. Ran in background batches of <=3 (each = JVM+Z3).
  * atk_1_prepatch (control-flow: snapshots+reverts distinguished key): NOT-A-COUNTEREXAMPLE, fails survive postcond (exit1).
  * atk_2_no_revert_other (control-flow-effect: never reverts ordinary key): NOT-A-COUNTEREXAMPLE, fails revert clause (2) `params[key_other()]==entry_other` (exit1).
  * atk_3_diverge (non-termination: establishes post-state then `while: pass`): NOT-A-COUNTEREXAMPLE, fails 'Obligation leak check' i.e. MustTerminate(2) (exit1). Confirms partial-correctness hole is closed.
  * atk_4_spurious (ungrounded/boundary: invents key key_other()+1): NOT-A-COUNTEREXAMPLE, fails no-spurious-key clause (3) Forall(k in params -> Old(k in params)) (exit1).
  * atk_5_echo (gold-faithful echo: snapshot BOTH keys, revert only ordinary key): CANDIDATE (same-spec AND verifies, exit0). Faithful patch = gold `del orig['backend']` structure. run_resolve -> RESOLVED=True completed=True (not flaky).
  * atk_6_partial_domain (partial-domain: revert ordinary key only when new_resolved!=entry_resolved): NOT-A-COUNTEREXAMPLE, fails revert clause (2) (exit1).
  * atk_7_direct (direct post-state, no snapshot: params[key_resolved()]=new_resolved; params[key_other()]=entry_other): CANDIDATE (same-spec AND verifies, exit0). Faithful patch realized as `orig.pop('backend', None)` (behaviorally identical net snapshot-minus-backend). run_resolve -> RESOLVED=True completed=True (not flaky).
  * atk_8_del_drop (drop attack: revert then `del params[key_other()]`): NOT-A-COUNTEREXAMPLE, rejected by Nagini as 'Not supported: del' (out-of-fragment parse error, exit1) -> a front-end refusal, not a spec ruling: the drop SHAPE is unexpressible in nagini's fragment, so clause (3)/(4) went untested against a dropped key and this attack does not settle whether they would reject a translatable drop rival.

RESOLVE (official harness, run_resolve, image swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-23299:latest, timeout 1800): patch_atk5 RESOLVED, patch_atk7 RESOLVED, and gold-patch positive control RESOLVED (harness path validated). Every verifying candidate's materialized faithful refined patch RESOLVES -> verify does NOT admit an unresolved impl. F2P: test_no_backend_reset_rccontext.

WHY SOUND (verify=>correct holds): the spec fully pins the observable mapping post-state: (1) survive `params[key_resolved()]==new_resolved`; (2) revert `params[key_other()]==entry_other`; (3) no-spurious-key forward Forall; (4) FRAME/full-revert Forall(k != key_resolved() -> params[k]==Old(params[k])) subsuming all non-distinguished pre-existing keys; plus MustTerminate(2). Any impl that verifies against this contract yields exactly the gold's mapping state on the tested input, so its faithful patch resolves. The two verifying attacks are genuine echoes of the gold and both resolve.

REFINEMENT.md LEG AUDIT (task §4 leg-kind + A-correspondence): A1 (RcParams->Dict[int,int])=R; A2 ('backend'->key_resolved()==0)=R; A3 (non-backend key->key_other()==1)=R; A4 (snapshot-excluding-distinguished <-> dict(rcParams.copy());del orig['backend'])=R + A-reference; A5 (body writes <-> yield/rcParams.update)=R; A6 (per-key revert <-> dict.update(rcParams,orig))=R + A-reference. NO kind-3 (unexpressible-changed-op) leg; NO consumed @ContractOnly axiom (axioms list empty). The two A-reference legs (A4,A6) correspond to real CPython dict copy/del/update primitives the gold composes; axiom_check.py reproduces the gold's exact control flow over a real dict and passes: 'G-AX OK ... 7 boundary + 20000 fuzz cases' (exit0). Correspondence holds.

VERDICT: SOUND. 8 distinct same-spec attacks run; the 5 wrong impls that reached the verifier are each rejected for the correct spec-relevant reason (revert/frame/no-spurious/terminate), and the 6th (del-drop) was refused by the front end rather than judged by the spec; the 2 verifying impls are gold echoes whose faithful patches both RESOLVE under the official harness. No verifying-but-unresolved impl exists among the attacks; spec is not too weak.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for matplotlib__matplotlib-23299 nagini. Real post-patch callee at base_commit worktree (3eadeacc06): rc_context -> orig = dict(rcParams.copy()); del orig['backend']; body; finally dict.update(rcParams, orig). Model verifies (nagini_verify exit 0, 14.9s). Spec region is the standard rc_context contract (checked against model_prepatch spec region: identical Requires/Ensures). Differential test of the model impl vs the real gold-patched callee over the modeled domain (20000 randomized dicts including a third untouched pre-existing key; body writing the two observed keys): 0/20000 divergences. Each postcondition matches real behavior: (1) distinguished key survives with body value because del orig['backend'] excludes it from the revert; (2) ordinary key reverted to entry value; (4) frame clause reverts every non-distinguished pre-existing key to its entry value (matches dict.update over full-minus-backend snapshot); (3) no-new-key clause holds within the modeled domain since the body abstraction writes only the two pre-existing observed keys. The only clause that could conceivably be stronger than the raw callee is (3) 'no new key on exit' — the real callee would retain a body-ADDED key across the finally revert — but the model deliberately and explicitly abstracts the body's observable effect to writes on the two observed keys (documented in refinement.md A5 and mapping.md §2); the modeled function admits no body-added key, so clause (3) is a sound domain restriction, not an input on which the model disagrees with the real callee. No diverging input found. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Properly-dispositioned relaxed-leakage instance (meta.relaxed_leakage=true, gates.G-LEAK.status='relaxed', RELAXED_LEAKAGE.md present). Independently re-verified, not rubber-stamped:

(1) CORE SOUNDNESS INTACT. `bash scripts/nagini_verify.sh model.py` -> exit 0 (Verification successful, 16.84s). model_prepatch.py FAILS at 106:13 with exactly `Postcondition ... Assertion (params[key_resolved()] == new_resolved) might not hold` (prepatch keeps the distinguished key in the snapshot and reverts it, so the body-set value does not survive) — G-DIFF/G-EQ discriminator is load-bearing. `adversary same-spec nagini` -> SAME (exit 0) and markers.same_spec(model, prepatch) == True: spec regions + docstring are byte-identical, only impl differs.

(2) UNAVOIDABILITY RE-DERIVED. problem_statement is a pure symptom report ('get_backend() clears figures from Gcf.figs if they were created under rc_context'); it never names the rcParams snapshot/revert mechanism. The gold discriminator (orig = dict(rcParams.copy()); del orig['backend'] — the distinguished key excluded from the exit-time revert so a body-set value SURVIVES) lives only in hints_text/gold internals. A faithful spec must pin survive-vs-revert (else prepatch would not fail), but no PS-only (Gcf.figs/get_backend-symptom) reformulation models the gold snapshot-exclusion fix. Faithful + PS-only-non-leaking is therefore provably impossible. Disposition sound.

(3) NEW-LEAK SCAN over the actual spec view (impl region elided by markers.spec_view). Lexical scan for gold-specific vocabulary: backend / rcparams / rc_context / get_backend / gcf / switch_backend / 'del orig' / '.copy()' / sentinel / 're-resolve' / lib/matplotlib / __init__ / 'diff --git' / rc_file / figure — ALL ABSENT from the spec view. The impl-region text that quotes gold internals (rcParams.copy(), rc_file, yield, dict.update) is correctly elided and not part of the consumer view. The only 'matplotlib' occurrence is the instance-id header line present in every bundle (not an edit narration). No leaking line found beyond the accepted, documented survive-vs-revert facet (docstring lifecycle narration + key_resolved/key_other tokens + survive/revert/no-spurious/full-revert postconditions).

Honest recording per RELAXED_LEAKAGE.md panel convention: NO-LEAKAGE (pass). LEAKAGE would be reserved for a NEW leak beyond the dispositioned facet or a broken disposition; neither is present.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `model.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
