# P2 adversarial audit — django__django-11999

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies (2 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_5_transient_clobber.py`, `atk_6_same_value_rewrite.py`, `atk_8_bounded_busywork.py`, `atk_9_infeasible_guard_bug.py`, `atk_11_regenerate_if_generated.py`, `atk_13_rewrite_other_same_value.py` |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch_unconditional.py`, `atk_2_diverge_loop.py`, `atk_3_selfcall_reentry.py`, `atk_4_frame_extra_writes.py`, `atk_12_raise_after.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_7_transient_delete.py`, `atk_10_transient_delete_other.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_unconditional.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,8 +123,7 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
-    if accessor_name not in cls:
-        cls[accessor_name] = generated_accessor()
+    cls[accessor_name] = generated_accessor()
     # impl-end
 
 
@@ -161,6 +160,5 @@
     Ensures(Forall(int, lambda k: (Implies(k != accessor_name and k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
-    if accessor_name not in cls:
-        cls[accessor_name] = generated_accessor()
+    cls[accessor_name] = generated_accessor()
     # impl-end
```

Attack 2 — `atk_2_diverge_loop.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,8 +123,9 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
-    if accessor_name not in cls:
-        cls[accessor_name] = generated_accessor()
+    while True:
+        Invariant(dict_pred(cls))
+        pass
     # impl-end
 
 
```

Attack 3 — `atk_3_selfcall_reentry.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,6 +123,8 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
+    if accessor_name in cls:
+        preserve_existing_accessor(cls, accessor_name)
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
     # impl-end
@@ -162,5 +164,6 @@
     # post-conditions-end
     # impl-start
     if accessor_name not in cls:
+        install_missing_accessor(cls, accessor_name)
         cls[accessor_name] = generated_accessor()
     # impl-end
```

Attack 4 — `atk_4_frame_extra_writes.py` → rejected (same spec, does not verify — good)

```diff
@@ -125,6 +125,7 @@
     # impl-start
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
+    cls[other_name()] = generated_accessor()
     # impl-end
 
 
@@ -163,4 +164,5 @@
     # impl-start
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
+    cls[555] = generated_accessor()
     # impl-end
```

Attack 5 — `atk_5_transient_clobber.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -123,8 +123,9 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
-    if accessor_name not in cls:
-        cls[accessor_name] = generated_accessor()
+    saved = cls[accessor_name]
+    cls[accessor_name] = generated_accessor()
+    cls[accessor_name] = saved
     # impl-end
 
 
@@ -162,5 +163,6 @@
     # post-conditions-end
     # impl-start
     if accessor_name not in cls:
+        cls[accessor_name] = other_name()
         cls[accessor_name] = generated_accessor()
     # impl-end
```

Attack 6 — `atk_6_same_value_rewrite.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -123,8 +123,8 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
-    if accessor_name not in cls:
-        cls[accessor_name] = generated_accessor()
+    saved = cls[accessor_name]
+    cls[accessor_name] = saved
     # impl-end
 
 
```

Attack 7 — `atk_7_transient_delete.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -123,8 +123,9 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
-    if accessor_name not in cls:
-        cls[accessor_name] = generated_accessor()
+    saved = cls[accessor_name]
+    del cls[accessor_name]
+    cls[accessor_name] = saved
     # impl-end
 
 
```

Attack 8 — `atk_8_bounded_busywork.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -123,6 +123,11 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
+    i = 0
+    while i < 100:
+        Invariant(i >= 0 and i <= 100)
+        Invariant(MustTerminate(100 - i + 1))
+        i = i + 1
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
     # impl-end
```

Attack 9 — `atk_9_infeasible_guard_bug.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -123,6 +123,8 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
+    if other_name() == accessor_name:
+        cls[accessor_name] = generated_accessor()
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
     # impl-end
@@ -161,6 +163,8 @@
     Ensures(Forall(int, lambda k: (Implies(k != accessor_name and k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
+    if other_name() == accessor_name:
+        cls[other_name()] = generated_accessor()
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
     # impl-end
```

Attack 10 — `atk_10_transient_delete_other.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -123,6 +123,9 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
+    saved = cls[other_name()]
+    del cls[other_name()]
+    cls[other_name()] = saved
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
     # impl-end
@@ -161,6 +164,9 @@
     Ensures(Forall(int, lambda k: (Implies(k != accessor_name and k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
+    saved = cls[other_name()]
+    del cls[other_name()]
+    cls[other_name()] = saved
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
     # impl-end
```

Attack 11 — `atk_11_regenerate_if_generated.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -123,7 +123,7 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
-    if accessor_name not in cls:
+    if cls[accessor_name] == generated_accessor():
         cls[accessor_name] = generated_accessor()
     # impl-end
 
```

Attack 12 — `atk_12_raise_after.py` → rejected (same spec, does not verify — good)

```diff
@@ -125,6 +125,7 @@
     # impl-start
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
+    raise Exception()
     # impl-end
 
 
@@ -163,4 +164,5 @@
     # impl-start
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
+    raise Exception()
     # impl-end
```

Attack 13 — `atk_13_rewrite_other_same_value.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -123,6 +123,8 @@
     Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
+    saved_other = cls[other_name()]
+    cls[other_name()] = saved_other
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
     # impl-end
@@ -161,6 +163,8 @@
     Ensures(Forall(int, lambda k: (Implies(k != accessor_name and k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
     # post-conditions-end
     # impl-start
+    saved_other = cls[other_name()]
+    cls[other_name()] = saved_other
     if accessor_name not in cls:
         cls[accessor_name] = generated_accessor()
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11999.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a model class is being assembled and one of its fields offers a
  predetermined set of selectable values, the class is given a generated
  accessor that
  returns the human-readable label for the field's stored value. The accessor
  is published on the class under a name derived from the field's name (the
  conventional ``get_<field>_display`` accessor name).

  The behaviour that matters: the generated accessor must be installed ONLY
  when the class does not already provide an accessor under that name.

    * If the class already defines its own accessor of that name -- for
      instance a hand-written method the author wrote to compute a custom
      display value -- that existing accessor MUST be preserved and the
      generated one MUST NOT overwrite it.
    * If no accessor of that name exists yet, the generated one is installed.

  Either way, after assembly an accessor of that name is present on the class,
  and the operation concerns ONLY the accessor name: no other attribute is
  added, removed, or rebound — every other name keeps exactly the membership
  and bound value it had before assembly.

  The accessor-installation step is also a BOUNDED step of class assembly: it
  always runs to completion in finitely many steps and hands control back, so
  the class finishes being assembled and becomes usable. Every claim above is a
  claim about an operation that finishes; an assembly step that never hands
  control back does not realise this behaviour, however it may look on the
  attribute namespace.

These are the two observable behaviours of the single guarded-installation
operation. They are modelled as two functions sharing one byte-identical
installation skeleton, each under the clean precondition that distinguishes
its case (``preserve_existing_accessor``: the name is already provided;
``install_missing_accessor``: the name is not yet provided).

Modelling choices (Nagini fragment):
  * The class attribute namespace is a ``Dict[int, int]`` from an
    attribute-name token to a method-identity token: the value records WHICH
    callable is bound under that name. Only membership (does the class provide
    that name) and per-name identity (which callable is bound) are observed, so
    integer identity is the faithful carrier (mapping.md §2).
  * The accessor name derived from the field is a parameter (an attribute-name
    token). The generated accessor's identity is the module-level constant
    ``generated_accessor()``; an author-defined accessor is any other identity.
  * Presence of the accessor name as a key models "the class already provides
    that name" (the resolvability test); absence models "no such name yet".

The class namespace is genuinely mutated in place (an accessor may be added to
it), so it is held at full permission and its exact post-state is stated. No
string indexing is used (Nagini bans it). Boundedness of the step is stated as a
termination obligation, so the accessor claims are total rather than conditional
on the step happening to finish. The behaviour is modelled deeply (the guarded
installation is spelled out in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions; per-function
regions repeat, one set per modelled function.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No axioms: the guarded accessor installation is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end

# pure-start
@Pure
def generated_accessor() -> int:
    # The method-identity token of the generated display accessor that
    # assembly would install for a field offering selectable values.
    return 0

@Pure
def other_name() -> int:
    # A representative pre-existing, unrelated class-attribute name (some other
    # method or attribute the class already carries). It witnesses that the
    # operation leaves attributes other than the accessor name untouched.
    return 1
# pure-end

def preserve_existing_accessor(cls: Dict[int, int], accessor_name: int) -> None:
    # pre-conditions-start
    # The class attribute namespace is mutated in place; full permission.
    Requires(dict_pred(cls))
    # This case: the class ALREADY provides an accessor of this name (the
    # author wrote one, or it was inherited).
    Requires(accessor_name in cls)
    # A representative unrelated attribute is already present on the class.
    Requires(other_name() in cls)
    Requires(other_name() != accessor_name)
    # The step is BOUNDED: it runs to completion in finitely many steps and
    # hands control back, so class assembly finishes and the class becomes
    # usable. This makes the accessor claims below TOTAL — they are claims about
    # a step that finishes, not claims held only of runs that happen to reach
    # the end. The budget (2) is what the single guarded namespace write costs.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(cls))
    # The accessor of this name remains present ...
    Ensures(accessor_name in cls)
    # ... and the accessor bound under this name is exactly the one that was
    # already there: the generated accessor is not installed over it. This is
    # the clause that lets an author-defined accessor of the same name stand.
    Ensures(cls[accessor_name] == Old(cls[accessor_name]))
    # A representative unrelated attribute keeps its exact bound identity: the
    # operation does not disturb a name other than the accessor name.
    Ensures(other_name() in cls)
    Ensures(cls[other_name()] == Old(cls[other_name()]))
    # Whole-namespace frame: in this case the operation performs NO write at
    # all, so no name's membership changes and every name that was present
    # keeps its exact bound identity. (Explicit triggers keep the quantifiers
    # tractable for the verifier.)
    Ensures(Forall(int, lambda k: ((k in cls) == Old(k in cls), [[k in cls]])))
    Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
    # post-conditions-end
    # impl-start
    if accessor_name not in cls:
        cls[accessor_name] = generated_accessor()
    # impl-end

def install_missing_accessor(cls: Dict[int, int], accessor_name: int) -> None:
    # pre-conditions-start
    # The class attribute namespace is mutated in place; full permission.
    Requires(dict_pred(cls))
    # This case: the class does NOT yet provide an accessor of this name.
    Requires(accessor_name not in cls)
    # A representative unrelated attribute is already present on the class.
    Requires(other_name() in cls)
    Requires(other_name() != accessor_name)
    # The step is BOUNDED: it runs to completion in finitely many steps and
    # hands control back, so class assembly finishes and the class becomes
    # usable. This makes the accessor claims below TOTAL — they are claims about
    # a step that finishes, not claims held only of runs that happen to reach
    # the end. The budget (2) is what the single guarded namespace write costs.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(cls))
    # The generated accessor is now installed and present under this name.
    Ensures(accessor_name in cls)
    Ensures(cls[accessor_name] == generated_accessor())
    # A representative unrelated attribute keeps its exact bound identity: the
    # operation does not disturb a name other than the accessor name.
    Ensures(other_name() in cls)
    Ensures(cls[other_name()] == Old(cls[other_name()]))
    # Whole-namespace frame: the operation writes AT MOST the accessor name.
    # Membership changes for the accessor name only, and every OTHER name that
    # was present keeps its exact bound identity. (Explicit triggers keep the
    # quantifiers tractable for the verifier.)
    Ensures(Forall(int, lambda k: (Implies(k != accessor_name, (k in cls) == Old(k in cls)), [[k in cls]])))
    Ensures(Forall(int, lambda k: (Implies(k != accessor_name and k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
    # post-conditions-end
    # impl-start
    if accessor_name not in cls:
        cls[accessor_name] = generated_accessor()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND (advisory). 13 same-spec attacks (all `adversary same-spec` exit 0), 6 CANDIDATEs, and EVERY candidate's materialized faithful patch RESOLVED under the official harness (F2P 1/1, P2P 30/30, completed=True, attempt 1, non-flaky). No verify=>correct break found. Positive control pos_control.py (byte copy of frozen model.py) verifies: `bash scripts/nagini_verify.sh` exit 0, 46.3s.

EVERY command was `python -m swebench_unified.adversary weakness nagini django__django-11999 <path>` from the repo root; resolves were `harness.run_resolve('django__django-11999', <patch text>)` (records at <path>.patch.resolve.json). Verifications ran 3-at-a-time as background jobs.

### REJECTED (exit 2 = spec rejected; error line quoted from `adversary verify`):
* atk_1_prepatch_unconditional.py -- PREPATCH BUG re-encoded (unconditional install in BOTH functions = base_commit). `model.py:113: Postcondition of preserve_existing_accessor might not hold. Assertion (cls[accessor_name] == Old(cls[accessor_name])) might not hold.` => prepatch_reproduced=True, and the failure is exactly the clause refinement.md/meta.json name (localized to preserve; install unaffected).
* atk_2_diverge_loop.py -- CONTROL-FLOW-EFFECT: `while True: pass` in preserve. `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` MustTerminate(2) (refinement.md step 6) is load-bearing.
* atk_3_selfcall_reentry.py -- the PRIOR AUDIT's named counterexample: unchanged-argument re-entry inside the guarded skeleton, BOTH functions. Two errors: `Callee preserve_existing_accessor / install_missing_accessor might not take all unsatisfied obligations from the caller.` VACUITY CONTROL ctl_3_vacuity_selfcall.py (Assert(False) immediately before the self-call) FAILS with `Assert might fail. Assertion False might not hold.` => the program point is reachable and the recursion genuinely taken, so the rejection is non-vacuous, confirming the repair refinement.md §"Boundedness" claims.
* atk_4_frame_extra_writes.py -- FRAME: correct accessor behaviour + rebinds other_name() (preserve) and adds fresh key 555 (install). Both frame axes fire: `cls[other_name()] == Old(cls[other_name()]) might not hold` and the quantified `Forall(k: k != accessor_name ==> (k in cls) == Old(k in cls)) might not hold`. The quantified whole-namespace frame is non-vacuous, as refinement.md §"Frame fidelity" claims.
* atk_12_raise_after.py -- ABNORMAL TERMINATION: post-state established, then `raise Exception()`. `Exhale might fail. Assertion "method raises no exceptions" might not hold` on BOTH functions. Exception freedom is enforced, so the total-correctness reading also covers the abnormal-exit axis (an axis refinement.md step 6 does not mention; reporting as a strength, not a defect).
* atk_7_transient_delete.py / atk_10_transient_delete_other.py -- NOT EVIDENCE EITHER WAY, stated explicitly rather than counted: `del cls[k]` is a Nagini FRAGMENT limit (`Translation failed / Not supported: del cls[accessor_name]`), so the verifier never judged the spec. check_attack reports verifies=False, verify_completed=True (summary "verification failed"), which OVERSTATES the spec's strength here; I do not lean on these two. They are retained in `attacks` for the record and are harmless (they cannot manufacture a break), but the 5-attack floor is met without them: atk_1/2/3/4/12 are genuine spec rejections.

CANDIDATEs (shares spec AND verifies) -- ALL 6 faithful patches EXECUTED through run_resolve, ALL RESOLVED:
* atk_5_transient_clobber.py (verifies 29.5s) -- POST-STATE BLINDNESS: preserve CLOBBERS the author accessor with the generated one and restores it; install transiently binds a non-generated identity. Refined = setattr(generated); setattr(saved). RESOLVED (F2P 1/1, P2P 30/30). Why it is harmless: the clobber is not observable by any test, because contribute_to_class runs during class assembly, before any instance exists, and the final binding is correct.
* atk_6_same_value_rewrite.py (47.3s) -- BOUNDARY write-vs-no-write: preserve performs setattr(cls, n, getattr(cls, n)) where gold performs NO write. Dict post-state identical, so the spec cannot see it. I confirmed this IS observable in real Django: with the author accessor on an abstract PARENT, gold leaves 'get_foo_bar_display' out of the child `__dict__` while this refinement moves it IN (probe printed `gold: in CHILD __dict__ = False` vs `atk6: True`), and getattr on a partialmethod yields a plain function that re-sets cleanly. RESOLVED anyway (F2P 1/1, P2P 30/30) -- no test observes attribute ownership, only resolution.
* atk_8_bounded_busywork.py (34.9s) -- resource axis: a bounded counting loop (measure supplied, MustTerminate discharged) before the guarded install. Refines to the gold guard plus dead work. RESOLVED (correct reshape; the intended outcome).
* atk_9_infeasible_guard_bug.py (32.5s) -- PARTIAL-DOMAIN: the buggy unconditional install kept behind `other_name() == accessor_name`, which Requires(other_name() != accessor_name) makes unsatisfiable. RESOLVED. VACUITY CONTROL ctl_9_vacuity_infeasible.py (Assert(False) in that branch) VERIFIES (exit 0, 16.7s) => the branch is genuinely DEAD, so this attack proved nothing about the spec; recorded as vacuous rather than as a spec strength.
* atk_11_regenerate_if_generated.py (21.0s) -- IDENTITY-TOKEN COLLAPSE: every generated accessor maps to the single token 0, so `if cls[accessor_name] == generated_accessor(): cls[accessor_name] = generated_accessor()` is a no-op in the model but in reality REPLACES an inherited field's partialmethod with THIS field's. RESOLVED (F2P 1/1, P2P 30/30).
* atk_13_rewrite_other_same_value.py (14.6s) -- THE SHARPEST ONE, and the closest this bundle comes to a break. The step rewrites the representative UNRELATED attribute with its own value: saved = cls[other_name()]; cls[other_name()] = saved. In the Dict carrier NOTHING changes, so cls[other_name()] == Old(...) AND both quantified frame clauses hold -- the frame is blind by construction, because it is a value/membership frame and this preserves both. Refined per mapping.md (other_name() <-> "any other attribute name already present on the class (e.g. an unrelated method)"), with `other` = the classmethod `from_db`, setattr(cls, 'from_db', getattr(cls, 'from_db')) rebinds a BOUND method over the classmethod descriptor, freezing cls. I verified real corruption in the base_commit tree with the patch applied: `Sub.from_db(...)` returns an M, not a Sub. RESOLVED ANYWAY (F2P 1/1, P2P 30/30) -- the 31 graded tests simply never call from_db on a proxy subclass of a choices model. So this is a real (if narrow) gap between "verifies" and "cannot corrupt the class", but NOT a G-EQ break: the criterion is resolve, and it resolves.

### A-LEG AUDIT (my assignment; R/I left to G-CONF):
* Step 4 (A-reference, the ONLY A-leg; meta.json axioms == [] so there is no consumed axiom and no kind-3 to hide behind) -- I re-derived the correspondence INDEPENDENTLY of axiom_check.py in aref_audit.py against the base_commit worktree, self-applying the gold guard at runtime, and extended coverage where axiom_check.py is thin: it only ever puts the author accessor in the SAME class body as the field (two declaration orders), so I added PARENT and GRANDPARENT placements. All 4 placements match the deep model (absent->'first' installed; own/parent/grandparent->'author-value' preserved), and hasattr-membership tracked `accessor_name in cls` exactly. A-reference SOUND, including the inherited placements the bundle's own check does not exercise.
* Step 6 (boundedness) -- correspondence holds: the patched branch is straight-line (one hasattr, at most one setattr) and unconditionally returns, and the obligation is what rejects atk_2/atk_3 with ctl_3 proving non-vacuity. Budget 2 is paid by the frozen impl (positive control verifies).
* Kind-3 scan -- every row is R / A-reference / I; no A-consumed row exists to check, consistent with axioms == [] and no @ContractOnly in model.py. No kind-3.
* Model<->patch correspondence -- patch.diff is the gold hunk verbatim; the two modeled functions collapse onto the ONE real site (fields/`__init__`.py:765-767) under their disjoint preconditions, and the frozen impl region refines to exactly `if not hasattr: setattr`.

### HONEST RESIDUAL FINDINGS (documentation-accuracy, not gate failures; no repair requested since none breaks resolve):
1. mapping.md §2 calls the class-namespace <-> Dict[int,int] correspondence a "bijection". It is not one: the carrier cannot express (a) OWN vs INHERITED attribute placement -- demonstrated by atk_6, whose refinement provably relocates the accessor into the child `__dict__` while the model sees no change; (b) intermediate namespace states -- atk_5 clobbers the author accessor mid-step and the spec cannot see it; (c) distinct generated accessors from different fields, all collapsed onto token 0 -- atk_11; (d) descriptor semantics, so a same-value rewrite of an unrelated classmethod is invisible -- atk_13, which I showed really does break Sub.from_db. "Abstraction" would be accurate; "bijection" overstates it. All four resolve, so the claim "verify => resolves" survives; the claim "the model is behaviourally EQUAL to the gold patch" (refinement.md's own wording) is slightly stronger than what is true.
2. refinement.md §"Frame fidelity" says an impl that "rebind[s] a pre-existing one" fails verification. True only for a rebinding to a DIFFERENT value (atk_4 fails as advertised); a same-value rebinding verifies (atk_13). The sentence should say "changes the bound value of".
3. mapping.md §2 represents the `self.choices is not None` trigger "by the functions being invoked at all" rather than as a parameter. I probed whether that convention is load-bearing by refining the frozen impl with the choices guard DROPPED (probe_no_choices_guard.patch): it RESOLVED too (F2P 1/1, P2P 30/30), so the omission does not cost correctness on the graded tests -- but it does mean the frozen spec does not pin the trigger, and a solver could install a display accessor on choice-less fields without the spec objecting. Worth a line in refinement.md.

**HYGIENE:** all work (the assigned dir; nothing written elsewhere in /tmp). The base_commit worktree was created with mktemp -d INSIDE that dir, used read-only apart from git-apply/git-checkout cycles, and removed with `git worktree remove --force` + `worktree prune` (clean; the pre-existing stash in the shared bare repo was NOT touched, per the never-git-stash-during-a-wave rule). Bundle unmodified: model.py md5 809424a25f4570a2f8fbadac1537f4fc before and after, and `git status` shows no change under benchmark-verified/django__django-11999/nagini/. Every resolve completed=True on attempt 1 (no host-saturation INCONCLUSIVE).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies (2 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_5_transient_clobber.py`, `atk_6_same_value_rewrite.py`, `atk_8_bounded_busywork.py`, `atk_9_infeasible_guard_bug.py`, `atk_11_regenerate_if_generated.py`, `atk_13_rewrite_other_same_value.py` |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1_prepatch_unconditional.py`, `atk_2_diverge_loop.py`, `atk_3_selfcall_reentry.py`, `atk_4_frame_extra_writes.py`, `atk_12_raise_after.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_7_transient_delete.py`, `atk_10_transient_delete_other.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch_unconditional.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_diverge_loop.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_selfcall_reentry.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_frame_extra_writes.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_transient_clobber.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_same_value_rewrite.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_transient_delete.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 8 — `atk_8_bounded_busywork.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_infeasible_guard_bug.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_transient_delete_other.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 11 — `atk_11_regenerate_if_generated.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_raise_after.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_rewrite_other_same_value.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11999.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a model class is being assembled and one of its fields offers a
  predetermined set of selectable values, the class is given a generated
  accessor that
  returns the human-readable label for the field's stored value. The accessor
  is published on the class under a name derived from the field's name (the
  conventional ``get_<field>_display`` accessor name).

  The behaviour that matters: the generated accessor must be installed ONLY
  when the class does not already provide an accessor under that name.

    * If the class already defines its own accessor of that name -- for
      instance a hand-written method the author wrote to compute a custom
      display value -- that existing accessor MUST be preserved and the
      generated one MUST NOT overwrite it.
    * If no accessor of that name exists yet, the generated one is installed.

  Either way, after assembly an accessor of that name is present on the class,
  and the operation concerns ONLY the accessor name: no other attribute is
  added, removed, or rebound — every other name keeps exactly the membership
  and bound value it had before assembly.

  The accessor-installation step is also a BOUNDED step of class assembly: it
  always runs to completion in finitely many steps and hands control back, so
  the class finishes being assembled and becomes usable. Every claim above is a
  claim about an operation that finishes; an assembly step that never hands
  control back does not realise this behaviour, however it may look on the
  attribute namespace.

These are the two observable behaviours of the single guarded-installation
operation. They are modelled as two functions sharing one byte-identical
installation skeleton, each under the clean precondition that distinguishes
its case (``preserve_existing_accessor``: the name is already provided;
``install_missing_accessor``: the name is not yet provided).

Modelling choices (Nagini fragment):
  * The class attribute namespace is a ``Dict[int, int]`` from an
    attribute-name token to a method-identity token: the value records WHICH
    callable is bound under that name. Only membership (does the class provide
    that name) and per-name identity (which callable is bound) are observed, so
    integer identity is the faithful carrier (mapping.md §2).
  * The accessor name derived from the field is a parameter (an attribute-name
    token). The generated accessor's identity is the module-level constant
    ``generated_accessor()``; an author-defined accessor is any other identity.
  * Presence of the accessor name as a key models "the class already provides
    that name" (the resolvability test); absence models "no such name yet".

The class namespace is genuinely mutated in place (an accessor may be added to
it), so it is held at full permission and its exact post-state is stated. No
string indexing is used (Nagini bans it). Boundedness of the step is stated as a
termination obligation, so the accessor claims are total rather than conditional
on the step happening to finish. The behaviour is modelled deeply (the guarded
installation is spelled out in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions; per-function
regions repeat, one set per modelled function.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No axioms: the guarded accessor installation is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end

# pure-start
@Pure
def generated_accessor() -> int:
    # The method-identity token of the generated display accessor that
    # assembly would install for a field offering selectable values.
    return 0

@Pure
def other_name() -> int:
    # A representative pre-existing, unrelated class-attribute name (some other
    # method or attribute the class already carries). It witnesses that the
    # operation leaves attributes other than the accessor name untouched.
    return 1
# pure-end

def preserve_existing_accessor(cls: Dict[int, int], accessor_name: int) -> None:
    # pre-conditions-start
    # The class attribute namespace is mutated in place; full permission.
    Requires(dict_pred(cls))
    # This case: the class ALREADY provides an accessor of this name (the
    # author wrote one, or it was inherited).
    Requires(accessor_name in cls)
    # A representative unrelated attribute is already present on the class.
    Requires(other_name() in cls)
    Requires(other_name() != accessor_name)
    # The step is BOUNDED: it runs to completion in finitely many steps and
    # hands control back, so class assembly finishes and the class becomes
    # usable. This makes the accessor claims below TOTAL — they are claims about
    # a step that finishes, not claims held only of runs that happen to reach
    # the end. The budget (2) is what the single guarded namespace write costs.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(cls))
    # The accessor of this name remains present ...
    Ensures(accessor_name in cls)
    # ... and the accessor bound under this name is exactly the one that was
    # already there: the generated accessor is not installed over it. This is
    # the clause that lets an author-defined accessor of the same name stand.
    Ensures(cls[accessor_name] == Old(cls[accessor_name]))
    # A representative unrelated attribute keeps its exact bound identity: the
    # operation does not disturb a name other than the accessor name.
    Ensures(other_name() in cls)
    Ensures(cls[other_name()] == Old(cls[other_name()]))
    # Whole-namespace frame: in this case the operation performs NO write at
    # all, so no name's membership changes and every name that was present
    # keeps its exact bound identity. (Explicit triggers keep the quantifiers
    # tractable for the verifier.)
    Ensures(Forall(int, lambda k: ((k in cls) == Old(k in cls), [[k in cls]])))
    Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
    # post-conditions-end
    # impl-start
    if accessor_name not in cls:
        cls[accessor_name] = generated_accessor()
    # impl-end

def install_missing_accessor(cls: Dict[int, int], accessor_name: int) -> None:
    # pre-conditions-start
    # The class attribute namespace is mutated in place; full permission.
    Requires(dict_pred(cls))
    # This case: the class does NOT yet provide an accessor of this name.
    Requires(accessor_name not in cls)
    # A representative unrelated attribute is already present on the class.
    Requires(other_name() in cls)
    Requires(other_name() != accessor_name)
    # The step is BOUNDED: it runs to completion in finitely many steps and
    # hands control back, so class assembly finishes and the class becomes
    # usable. This makes the accessor claims below TOTAL — they are claims about
    # a step that finishes, not claims held only of runs that happen to reach
    # the end. The budget (2) is what the single guarded namespace write costs.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(cls))
    # The generated accessor is now installed and present under this name.
    Ensures(accessor_name in cls)
    Ensures(cls[accessor_name] == generated_accessor())
    # A representative unrelated attribute keeps its exact bound identity: the
    # operation does not disturb a name other than the accessor name.
    Ensures(other_name() in cls)
    Ensures(cls[other_name()] == Old(cls[other_name()]))
    # Whole-namespace frame: the operation writes AT MOST the accessor name.
    # Membership changes for the accessor name only, and every OTHER name that
    # was present keeps its exact bound identity. (Explicit triggers keep the
    # quantifiers tractable for the verifier.)
    Ensures(Forall(int, lambda k: (Implies(k != accessor_name, (k in cls) == Old(k in cls)), [[k in cls]])))
    Ensures(Forall(int, lambda k: (Implies(k != accessor_name and k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))
    # post-conditions-end
    # impl-start
    if accessor_name not in cls:
        cls[accessor_name] = generated_accessor()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND (advisory). 13 same-spec attacks (all `adversary same-spec` exit 0), 6 CANDIDATEs, and EVERY candidate's materialized faithful patch RESOLVED under the official harness (F2P 1/1, P2P 30/30, completed=True, attempt 1, non-flaky). No verify=>correct break found. Positive control pos_control.py (byte copy of frozen model.py) verifies: `bash scripts/nagini_verify.sh` exit 0, 46.3s.

EVERY command was `python -m swebench_unified.adversary weakness nagini django__django-11999 <path>` from the repo root; resolves were `harness.run_resolve('django__django-11999', <patch text>)` (records at <path>.patch.resolve.json). Verifications ran 3-at-a-time as background jobs.

### REJECTED (exit 2 = spec rejected; error line quoted from `adversary verify`):
* atk_1_prepatch_unconditional.py -- PREPATCH BUG re-encoded (unconditional install in BOTH functions = base_commit). `model.py:113: Postcondition of preserve_existing_accessor might not hold. Assertion (cls[accessor_name] == Old(cls[accessor_name])) might not hold.` => prepatch_reproduced=True, and the failure is exactly the clause refinement.md/meta.json name (localized to preserve; install unaffected).
* atk_2_diverge_loop.py -- CONTROL-FLOW-EFFECT: `while True: pass` in preserve. `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` MustTerminate(2) (refinement.md step 6) is load-bearing.
* atk_3_selfcall_reentry.py -- the PRIOR AUDIT's named counterexample: unchanged-argument re-entry inside the guarded skeleton, BOTH functions. Two errors: `Callee preserve_existing_accessor / install_missing_accessor might not take all unsatisfied obligations from the caller.` VACUITY CONTROL ctl_3_vacuity_selfcall.py (Assert(False) immediately before the self-call) FAILS with `Assert might fail. Assertion False might not hold.` => the program point is reachable and the recursion genuinely taken, so the rejection is non-vacuous, confirming the repair refinement.md §"Boundedness" claims.
* atk_4_frame_extra_writes.py -- FRAME: correct accessor behaviour + rebinds other_name() (preserve) and adds fresh key 555 (install). Both frame axes fire: `cls[other_name()] == Old(cls[other_name()]) might not hold` and the quantified `Forall(k: k != accessor_name ==> (k in cls) == Old(k in cls)) might not hold`. The quantified whole-namespace frame is non-vacuous, as refinement.md §"Frame fidelity" claims.
* atk_12_raise_after.py -- ABNORMAL TERMINATION: post-state established, then `raise Exception()`. `Exhale might fail. Assertion "method raises no exceptions" might not hold` on BOTH functions. Exception freedom is enforced, so the total-correctness reading also covers the abnormal-exit axis (an axis refinement.md step 6 does not mention; reporting as a strength, not a defect).
* atk_7_transient_delete.py / atk_10_transient_delete_other.py -- NOT EVIDENCE EITHER WAY, stated explicitly rather than counted: `del cls[k]` is a Nagini FRAGMENT limit (`Translation failed / Not supported: del cls[accessor_name]`), so the verifier never judged the spec. check_attack reports verifies=False, verify_completed=True (summary "verification failed"), which OVERSTATES the spec's strength here; I do not lean on these two. They are retained in `attacks` for the record and are harmless (they cannot manufacture a break), but the 5-attack floor is met without them: atk_1/2/3/4/12 are genuine spec rejections.

CANDIDATEs (shares spec AND verifies) -- ALL 6 faithful patches EXECUTED through run_resolve, ALL RESOLVED:
* atk_5_transient_clobber.py (verifies 29.5s) -- POST-STATE BLINDNESS: preserve CLOBBERS the author accessor with the generated one and restores it; install transiently binds a non-generated identity. Refined = setattr(generated); setattr(saved). RESOLVED (F2P 1/1, P2P 30/30). Why it is harmless: the clobber is not observable by any test, because contribute_to_class runs during class assembly, before any instance exists, and the final binding is correct.
* atk_6_same_value_rewrite.py (47.3s) -- BOUNDARY write-vs-no-write: preserve performs setattr(cls, n, getattr(cls, n)) where gold performs NO write. Dict post-state identical, so the spec cannot see it. I confirmed this IS observable in real Django: with the author accessor on an abstract PARENT, gold leaves 'get_foo_bar_display' out of the child `__dict__` while this refinement moves it IN (probe printed `gold: in CHILD __dict__ = False` vs `atk6: True`), and getattr on a partialmethod yields a plain function that re-sets cleanly. RESOLVED anyway (F2P 1/1, P2P 30/30) -- no test observes attribute ownership, only resolution.
* atk_8_bounded_busywork.py (34.9s) -- resource axis: a bounded counting loop (measure supplied, MustTerminate discharged) before the guarded install. Refines to the gold guard plus dead work. RESOLVED (correct reshape; the intended outcome).
* atk_9_infeasible_guard_bug.py (32.5s) -- PARTIAL-DOMAIN: the buggy unconditional install kept behind `other_name() == accessor_name`, which Requires(other_name() != accessor_name) makes unsatisfiable. RESOLVED. VACUITY CONTROL ctl_9_vacuity_infeasible.py (Assert(False) in that branch) VERIFIES (exit 0, 16.7s) => the branch is genuinely DEAD, so this attack proved nothing about the spec; recorded as vacuous rather than as a spec strength.
* atk_11_regenerate_if_generated.py (21.0s) -- IDENTITY-TOKEN COLLAPSE: every generated accessor maps to the single token 0, so `if cls[accessor_name] == generated_accessor(): cls[accessor_name] = generated_accessor()` is a no-op in the model but in reality REPLACES an inherited field's partialmethod with THIS field's. RESOLVED (F2P 1/1, P2P 30/30).
* atk_13_rewrite_other_same_value.py (14.6s) -- THE SHARPEST ONE, and the closest this bundle comes to a break. The step rewrites the representative UNRELATED attribute with its own value: saved = cls[other_name()]; cls[other_name()] = saved. In the Dict carrier NOTHING changes, so cls[other_name()] == Old(...) AND both quantified frame clauses hold -- the frame is blind by construction, because it is a value/membership frame and this preserves both. Refined per mapping.md (other_name() <-> "any other attribute name already present on the class (e.g. an unrelated method)"), with `other` = the classmethod `from_db`, setattr(cls, 'from_db', getattr(cls, 'from_db')) rebinds a BOUND method over the classmethod descriptor, freezing cls. I verified real corruption in the base_commit tree with the patch applied: `Sub.from_db(...)` returns an M, not a Sub. RESOLVED ANYWAY (F2P 1/1, P2P 30/30) -- the 31 graded tests simply never call from_db on a proxy subclass of a choices model. So this is a real (if narrow) gap between "verifies" and "cannot corrupt the class", but NOT a G-EQ break: the criterion is resolve, and it resolves.

### A-LEG AUDIT (my assignment; R/I left to G-CONF):
* Step 4 (A-reference, the ONLY A-leg; meta.json axioms == [] so there is no consumed axiom and no kind-3 to hide behind) -- I re-derived the correspondence INDEPENDENTLY of axiom_check.py in aref_audit.py against the base_commit worktree, self-applying the gold guard at runtime, and extended coverage where axiom_check.py is thin: it only ever puts the author accessor in the SAME class body as the field (two declaration orders), so I added PARENT and GRANDPARENT placements. All 4 placements match the deep model (absent->'first' installed; own/parent/grandparent->'author-value' preserved), and hasattr-membership tracked `accessor_name in cls` exactly. A-reference SOUND, including the inherited placements the bundle's own check does not exercise.
* Step 6 (boundedness) -- correspondence holds: the patched branch is straight-line (one hasattr, at most one setattr) and unconditionally returns, and the obligation is what rejects atk_2/atk_3 with ctl_3 proving non-vacuity. Budget 2 is paid by the frozen impl (positive control verifies).
* Kind-3 scan -- every row is R / A-reference / I; no A-consumed row exists to check, consistent with axioms == [] and no @ContractOnly in model.py. No kind-3.
* Model<->patch correspondence -- patch.diff is the gold hunk verbatim; the two modeled functions collapse onto the ONE real site (fields/`__init__`.py:765-767) under their disjoint preconditions, and the frozen impl region refines to exactly `if not hasattr: setattr`.

### HONEST RESIDUAL FINDINGS (documentation-accuracy, not gate failures; no repair requested since none breaks resolve):
1. mapping.md §2 calls the class-namespace <-> Dict[int,int] correspondence a "bijection". It is not one: the carrier cannot express (a) OWN vs INHERITED attribute placement -- demonstrated by atk_6, whose refinement provably relocates the accessor into the child `__dict__` while the model sees no change; (b) intermediate namespace states -- atk_5 clobbers the author accessor mid-step and the spec cannot see it; (c) distinct generated accessors from different fields, all collapsed onto token 0 -- atk_11; (d) descriptor semantics, so a same-value rewrite of an unrelated classmethod is invisible -- atk_13, which I showed really does break Sub.from_db. "Abstraction" would be accurate; "bijection" overstates it. All four resolve, so the claim "verify => resolves" survives; the claim "the model is behaviourally EQUAL to the gold patch" (refinement.md's own wording) is slightly stronger than what is true.
2. refinement.md §"Frame fidelity" says an impl that "rebind[s] a pre-existing one" fails verification. True only for a rebinding to a DIFFERENT value (atk_4 fails as advertised); a same-value rebinding verifies (atk_13). The sentence should say "changes the bound value of".
3. mapping.md §2 represents the `self.choices is not None` trigger "by the functions being invoked at all" rather than as a parameter. I probed whether that convention is load-bearing by refining the frozen impl with the choices guard DROPPED (probe_no_choices_guard.patch): it RESOLVED too (F2P 1/1, P2P 30/30), so the omission does not cost correctness on the graded tests -- but it does mean the frozen spec does not pin the trigger, and a solver could install a display accessor on choice-less fields without the spec objecting. Worth a line in refinement.md.

**HYGIENE:** all work (the assigned dir; nothing written elsewhere in /tmp). The base_commit worktree was created with mktemp -d INSIDE that dir, used read-only apart from git-apply/git-checkout cycles, and removed with `git worktree remove --force` + `worktree prune` (clean; the pre-existing stash in the shared bare repo was NOT touched, per the never-git-stash-during-a-wave rule). Bundle unmodified: model.py md5 809424a25f4570a2f8fbadac1537f4fc before and after, and `git status` shows no change under benchmark-verified/django__django-11999/nagini/. Every resolve completed=True on attempt 1 (no host-saturation INCONCLUSIVE).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SPEC INTEGRITY FIRST. `adversary same-spec nagini django__django-11999 atk2f_11999_same.py` on a verbatim copy of the frozen model.py => exit 0 (SAME - attack shares the bundle's exact specification), so the marker-delimited spec regions I reasoned about are the frozen ones. `scripts/nagini_verify.sh model.py` => exit 0, 20.24s (Verification successful). Bundle NOT modified (model.py mtime unchanged). All work in a throwaway detached worktree of the upstream repository at base_commit 84633905, created with mktemp -d, gold patch applied there, worktree removed + pruned at the end. A pre-existing stash@{0} exists in the shared bare repo; I did NOT touch it (per my never-git-stash-during-a-wave note).

**WHAT I ATTACKED.** The spec models the gold patch's choices-branch of Field.contribute_to_class as two functions over a Dict[int,int] name-token -> identity-token carrier: preserve_existing_accessor (Requires accessor_name in cls; Ensures NO write at all + quantified whole-namespace frame) and install_missing_accessor (Requires accessor_name not in cls; Ensures cls[acc]==generated_accessor() + frame preserving all k != acc), both with Requires(other_name() in cls), other_name() != accessor_name, MustTerminate(2). To break FAITHFULness I needed an input where the modeled Ensures disagree with the real patched callee.

**HARNESS.** Branch-isolated: I wrapped the REAL Field.contribute_to_class and neutralised ONLY the display branch (by temporarily clearing self.choices) so all other real work (set_attributes_from_name, `_meta`.add_field, descriptor_class install) still runs; that yields a GENUINE pre-branch Old(cls) rather than a proxy sibling class. I then execute the gold branch verbatim and snapshot the post state. I asserted via inspect.getsource that the ambient method carries the patched guard, so I can never silently diff against the base_commit bug.

**RESULT:** ZERO DIVERGENCES. (a) 16 hand-built structural cases: accessor absent / own-before / own-after (the F2P shape both orders), accessor bound to property / classmethod / staticmethod / non-callable str / None / False, inherited from abstract parent, from a concrete parent (MTI), from a grandparent, class overriding `_get_FIELD_display` (the ticket's documented 2.2+ recipe), field renamed via name=, grouped choices. 11 preserve + 5 install, 0 Ensures violations. (b) 3000-case seeded randomized sweep (seed 11999) over 6 field types, 5 choice shapes incl. grouped and empty, 5 field names, 5 placements, 10 author bindings, 0-2 inheritance levels: 2415 preserve + 585 install, 0 violations. (c) STRONGEST test, closing the one bridge weakness I found: a value-level check of the QUANTIFIED frame Ensures over EVERY key in the flattened MRO (not just a few tracked names) - 6000 cases, 4795 preserve + 1205 install, 0 violations.

HARNESS PROVEN LIVE (a green check is worthless until shown it can go red). Injected mutants all fire: base_commit unguarded install -> RED on cls[acc]==Old(cls[acc]) and the Forall value clause; a branch that clobbers an unrelated tracked key -> RED 4x; a branch that rebinds an UNTRACKED existing name (save) -> RED on both preserve and install value-Forall; a branch adding a fresh unrelated key -> RED on both membership-Forall clauses. So the 0-violation results are real signal.

BRIDGE WEAKNESSES FOUND IN conformance_check.py - real, but NOT spec unfaithfulness. (1) Membership is realised as an MRO-`__dict__` walk (`_mro_lookup`, lines 199-203), not the normative hasattr of mapping.md sec2. (2) The whole-namespace frame Ensures is checked only as a key-SET diff plus 5 tracked identities (lines 219-225, 325-331), so a value-level rebinding of an untracked name would pass undetected; `_SKIP_KEYS` also excludes `__qualname__`/`__doc__`/`__dict__`/`__weakref__`. (3) Old(cls) is a sibling class assembled with choices=None, not a true pre-state. I did not take these on faith: my own harness fixes all three (normative hasattr, genuine pre-state, value-level Forall over all MRO keys) and STILL found 0 divergences. So the bundle's green is not an artifact of these gaps - the spec is faithful under the stronger reading too. These are hardening suggestions for the bridge, not spec defects.

**CANDIDATE BREAKS I CHASED AND REFUTED.** (i) A descriptor under the accessor name whose `__get__` raises AttributeError: hasattr=False while MRO-dict membership=True (readings DISAGREE, confirmed). Under the bridge's MRO reading this would dispatch to preserve and the real branch then clobbers -> violation; but under mapping.md sec2's NORMATIVE hasattr reading it correctly dispatches to install_missing_accessor and every clause holds (verified: the generated partialmethod is installed). A bridge/spec-text mismatch in a corner unreachable from AUTHOR_IDENTITIES (all plain functions/string, where the readings coincide) - not spec drift. (ii) Metaclass `__getattr__` making hasattr always True: dispatches to preserve, and the gold branch performs NO write, so preserve's no-write Ensures HOLDS (verified). (iii) A metaclass `__setattr__` that swallows the write would falsify install's accessor_name in cls - but ModelBase defines no `__setattr__` (confirmed) and Django never ships such a metaclass, so it is outside the modeled operation's domain.

ONE GENUINE EDGE, correctly outside the model: a descriptor raising a NON-AttributeError under the accessor name makes the patched branch exit exceptionally (verified: gold raises RuntimeError where base_commit's unguarded setattr returned normally). This is a property of the gold patch Django shipped, and the spec abstracts the gold patch, so it is not drift. It does not falsify MustTerminate(2), which constrains boundedness/handing control back, not normal-vs-exceptional exit; and a dict key-membership test cannot raise, so it is outside the Dict[int,int] carrier by construction. No F2P/P2P test builds such a descriptor.

**SPEC-TOO-STRONG CHECK.** No over-claiming found. The frame clauses are correctly ASYMMETRIC (preserve: no write at all; install: at most the accessor key) and I confirmed the real branch adds exactly {get_foo_bar_display} and removes nothing. Requires are satisfiable and satisfied by real Django classes. choices=[] is not None so the branch still runs and installs - matching the model. MustTerminate(2) is budget-adequate (frozen impl verifies).

ORACLE DISCRIMINATION (end-to-end, real tests). F2P test_overriding_FIELD_display FAILS at base_commit (AssertionError: 'foo' != 'something') and PASSES with gold; full model_fields suite: Ran 311 tests, OK (skipped=2). Declaration order, the crux of the ticket: BOTH orders preserve the author accessor end-to-end ('something'), so the gold fix is order-insensitive and the model's hasattr-keyed two-case split faithfully captures it.

**BUNDLE GATES REPRODUCED INDEPENDENTLY:** G-CONF exit 0 (100000 inputs, 0 disagreements, preserve=74877 install=25123, discrimination self-test 3/3); G-AX exit 0 (4 boundary + 2000 fuzz assemblies, both declaration orders, clobber confirmed under the unguarded state). Note G-AX's oracle is a transliteration of the guard rather than the ambient method, so it would pass on an unpatched tree - a weakness of that gate, but G-CONF does assert the ambient patch lexically, so the pair is sound.

**CONCLUSION:** FAITHFUL. Across ~9000 real-callee executions under a harness strictly stronger than the bundle's own bridge, I could not produce an input on which the modeled functions disagree with the real patched callee. I am explicitly NOT claiming FAITHFUL-is-a-defect: I have no diverging input.

**SPEC INTEGRITY FIRST.** `adversary same-spec nagini django__django-11999 atk2f_11999_same.py` on a verbatim copy of the frozen model.py => exit 0 (SAME - attack shares the bundle's exact specification), so the marker-delimited spec regions I reasoned about are the frozen ones. `scripts/nagini_verify.sh model.py` => exit 0, 20.24s (Verification successful). Bundle NOT modified (model.py mtime unchanged). All work in a throwaway detached worktree of the upstream repository at base_commit 84633905, created with mktemp -d, gold patch applied there, worktree removed + pruned at the end. A pre-existing stash@{0} exists in the shared bare repo; I did NOT touch it (per my never-git-stash-during-a-wave note).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ROLE: attacker 3 (leakage / gold-reconstruction). Judged the CONSUMER-VISIBLE spec view against the solver-visible problem_statement ONLY; hints_text deliberately excluded from the baseline per the G-LEAK rule (a hints-only term is not public, so screening against it would excuse a real leak).

SCOPE — WHAT THE CONSUMER ACTUALLY SEES (established from code, not assumed). eval/prompts.py:`_spec_block` renders (a) task.spec_view and (b) meta.json modeled_functions as 'model_symbol (<-> repo_symbol)' pairs. dataset.py:264-284 populates these only for MODES_WITH_SPEC={1,2}. I therefore audited spec_view PLUS that rendered pair line — a wider surface than model.py-minus-impl alone. refinement.md and mapping.md are NOT consumer-visible (no reader anywhere under src/swebench_unified/eval/ loads them; the only hits are a comment in audit.py and a docstring in score.py). This matters: refinement.md:19-30 quotes the gold hunk VERBATIM including "if not hasattr(cls, 'get_%s_display' % self.name):", and mapping.md:9 names the patched file. Those would be flagrant leaks if served — they are not, so they are not charged.

NO DRIFT — AND THIS INSTANCE HAD A POST-GATE EDIT. Per my standing rule I did not inherit the recorded pass: the bundle was revised after the earlier panel run (the MustTerminate/boundedness repair, refinement.md:59-87 documents it). Recomputed every region hash live via markers.region_hashes: all six match meta.json exactly, and live spec_view = 8d05d527ec49df967a9db56f123d0d87b4bebee4bdc2f19dca7b3e7150a20443 == the hash verdict.md cites. So the boundedness repair landed BEFORE the recorded gate and the prior reasoning does describe the text I screened. Official screen re-run live: passed=True, hard_failures=[], warnings=[]. meta G-LEAK status is 'pass', not 'relaxed' — no RELAXED_LEAKAGE.md is being honored, so the strict bar applies and is met. same-spec on an identity copy: exit 0 (spec region byte-identical).

SCREEN PROVEN LIVE — AND ONE BLIND SPOT FOUND. Injected six mutants into the same screen. Five fired: bug->fix narration -> L3; the gold line pasted verbatim -> L1; django/db/models/fields/`__init__`.py -> L2; a pure helper renamed contribute_to_class_token -> L2/L5 identifier echo; 'This models Field.contribute_to_class' in a comment -> L2/L3. The SIXTH did NOT fire: '# The installed callable is a partialmethod.' passes clean, because `_patch_changed_symbols` only harvests def/class names, so hints-only mechanism vocabulary that is not a def/class name is invisible to the mechanical gate.

I did not let the green stand on that axis — I hand-swept it: partialmethod, hasattr, setattr, ModelBase, attname, flatchoices, add_to_class, descriptor, metaclass, `__set_name__`, 'order of attrs', regression, a68ea231, 2.1/2.2 are ALL absent from the spec view. Also hand-swept hidden-TEST identity (the screen's formal flavor ignores test_patch entirely): test_overriding_FIELD_display, GetFieldDisplayTests, model_fields, tests/model_fields/tests.py, IntegerField, assertEqual — all absent. foo_bar/FooBar/'something'/get_foo_bar_display are absent too and would have been public anyway (all verbatim in the problem statement).

GOLD-RECONSTRUCTION, THRESHOLD LOWERED. The official L1 check uses a >=8-char normalized floor. I re-ran it with NO floor and additionally slid a 12-char window over the concatenated normalized gold changed-lines: zero slices occur in the spec view. The only 'match' at no-floor is the 1-char ')'. Nothing of the gold's lexical shape survives into the view.

THE CENTRAL QUESTION — does the docstring hand over the edit? The strongest candidate is model.py:12-19, 'the generated accessor must be installed ONLY when the class does not already provide an accessor under that name', with the preserve/install split, and its formal echo Ensures(cls[accessor_name] == Old(cls[accessor_name])). I weighed charging this as a mechanism leak, since it is one refinement step from 'if not hasattr: setattr'. I reject the charge. The problem statement says the author cannot override get_FOO_display and states 'What I expect is that I should be able to override this function.' 'An author-defined accessor must survive and the generated one must not replace it' IS that stated expectation turned into a contract — the requirement, not the diagnosis.

The view fixes no file, no function, no predicate name, no guard site. Crucially, a spec that declined to say this would be spec-too-weak: the sole F2P discriminator (test_overriding_FIELD_display asserts the hand-written get_foo_bar_display returning 'something' survives) would be unpinned, and G-PANEL-1 would break it. Leakage and faithfulness are traded here, and the resolution is forced by the problem statement's own wording.

**LOCALIZATION PARITY.** MODES_WITH_SPEC={1,2} is a strict subset of MODES_WITH_LOCALIZATION={0,1,2,100}, so every mode served spec_view ALSO sanctions changed_files + repo_symbol as baseline inputs. Hence the rendered 'preserve_existing_accessor (<-> django.db.models.fields.Field.contribute_to_class)' pair carries ZERO incremental leakage — mode 0 hands the same localization with no spec at all, by design (prompts.py:95 calls it 'the SAME information the spec modes get'). Note the rendered pair exposes only model_symbol and repo_symbol; meta's role/carrier_type/repo_location fields (whose 'role' text does describe the preserve/install behaviours, and repo_location gives line 749/765-767) are NOT rendered.

RESIDUAL RISK (stated, not charged): the preserve/install behavioural split is inherently close to the gold's shape, and the mechanical screen is demonstrably blind to non-def/class hints vocabulary (mutant M6). The first is the unavoidable cost of pinning the F2P discriminator; the second I covered by hand sweep rather than by trusting the gate. Recording both so the panel sees they were weighed, not waved through.

**VERDICT:** NO-LEAKAGE. No gold-diff line at any threshold, no diff marker, no patched file/module path, no identifier or comment echoing a patched repo symbol, no hints-only mechanism vocabulary, no hidden-test identity, no bug->fix narration; hashes prove the text I screened is the shipped text; screen proven red on five injected leak shapes with its one blind spot covered manually.

**ROLE:** attacker 3 (leakage / gold-reconstruction). Judged the CONSUMER-VISIBLE spec view against the solver-visible problem_statement ONLY; hints_text deliberately excluded from the baseline per the G-LEAK rule (a hints-only term is not public, so screening against it would excuse a real leak).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.