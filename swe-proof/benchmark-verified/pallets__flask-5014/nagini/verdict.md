# P2 adversarial audit — pallets__flask-5014

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_8.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_5.py`, `atk_6.py`, `atk_9.py`, `atk_14.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 14 same-spec wrong impls were run; 10 were REJECTED by the frozen spec and the 4 that VERIFIED (atk_5, atk_6, atk_9, atk_14) all had their faithful refined patches materialized and executed through the official harness (run_resolve) — all 4 RESOLVED (F2P test_empty_name_not_allowed + 59/59 P2P green, patch applied). So no verifying wrong impl exhibits verify-and-not-resolve; the refinement claim survives falsification.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -176,8 +176,6 @@
     # post-conditions-end
     # impl-start
     init_base(import_name)
-    if len(name) == 0:
-        raise NameValidationError()
     if contains_dot(ToSeq(name)):
         raise NameValidationError()
     return
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -178,7 +178,7 @@
     init_base(import_name)
     if len(name) == 0:
         raise NameValidationError()
-    if contains_dot(ToSeq(name)):
+    if name[0] == 46:
         raise NameValidationError()
     return
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -176,7 +176,7 @@
     # post-conditions-end
     # impl-start
     init_base(import_name)
-    if len(name) == 0:
+    if len(name) <= 1:
         raise NameValidationError()
     if contains_dot(ToSeq(name)):
         raise NameValidationError()
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -178,7 +178,5 @@
     init_base(import_name)
     if len(name) == 0:
         raise NameValidationError()
-    if contains_dot(ToSeq(name)):
-        raise NameValidationError()
     return
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -176,9 +176,11 @@
     # post-conditions-end
     # impl-start
     init_base(import_name)
-    if len(name) == 0:
-        raise NameValidationError()
-    if contains_dot(ToSeq(name)):
+    if len(name) == 0 or contains_dot(ToSeq(name)):
+        try:
+            init_base(import_name)
+        except BaseInitError:
+            raise BaseInitError()
         raise NameValidationError()
     return
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -175,10 +175,14 @@
             and base_init_can_fail(ToSeq(import_name)))
     # post-conditions-end
     # impl-start
-    init_base(import_name)
-    if len(name) == 0:
-        raise NameValidationError()
-    if contains_dot(ToSeq(name)):
+    try:
+        init_base(import_name)
+    except BaseInitError:
+        if len(name) == 0 or contains_dot(ToSeq(name)):
+            init_base(import_name)
+            raise NameValidationError()
+        raise BaseInitError()
+    if len(name) == 0 or contains_dot(ToSeq(name)):
         raise NameValidationError()
     return
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -176,9 +176,12 @@
     # post-conditions-end
     # impl-start
     init_base(import_name)
-    if len(name) == 0:
-        raise NameValidationError()
-    if contains_dot(ToSeq(name)):
-        raise NameValidationError()
+    if len(name) == 0 or contains_dot(ToSeq(name)):
+        try:
+            validate_name(name, import_name)
+        except BaseInitError:
+            raise BaseInitError()
+        except NameValidationError:
+            raise NameValidationError()
     return
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -177,7 +177,9 @@
     # impl-start
     init_base(import_name)
     if len(name) == 0:
-        raise NameValidationError()
+        i = 0
+        while i >= 0:
+            i = i + 1
     if contains_dot(ToSeq(name)):
         raise NameValidationError()
     return
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -175,10 +175,9 @@
             and base_init_can_fail(ToSeq(import_name)))
     # post-conditions-end
     # impl-start
+    if len(name) == 0 or contains_dot(ToSeq(name)):
+        init_base(import_name)
+        raise NameValidationError()
     init_base(import_name)
-    if len(name) == 0:
-        raise NameValidationError()
-    if contains_dot(ToSeq(name)):
-        raise NameValidationError()
     return
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -176,9 +176,11 @@
     # post-conditions-end
     # impl-start
     init_base(import_name)
-    if len(name) == 0:
-        raise NameValidationError()
-    if contains_dot(ToSeq(name)):
+    if len(name) == 0 or contains_dot(ToSeq(name)):
+        try:
+            init_base(name)
+        except BaseInitError:
+            raise BaseInitError()
         raise NameValidationError()
     return
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -176,9 +176,12 @@
     # post-conditions-end
     # impl-start
     init_base(import_name)
-    if len(name) == 0:
-        raise NameValidationError()
-    if contains_dot(ToSeq(name)):
+    if len(name) == 0 or contains_dot(ToSeq(name)):
+        try:
+            init_base(import_name)
+        except BaseInitError:
+            Assert(False)
+            raise BaseInitError()
         raise NameValidationError()
     return
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -176,9 +176,7 @@
     # post-conditions-end
     # impl-start
     init_base(import_name)
-    if len(name) == 0:
-        raise NameValidationError()
-    if contains_dot(ToSeq(name)):
-        raise NameValidationError()
+    if len(name) == 0 or contains_dot(ToSeq(name)):
+        raise BaseInitError()
     return
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -178,7 +178,7 @@
     init_base(import_name)
     if len(name) == 0:
         raise NameValidationError()
-    if contains_dot(ToSeq(name)):
+    if contains_dot(ToSeq(import_name)):
         raise NameValidationError()
     return
     # impl-end
```

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -176,9 +176,12 @@
     # post-conditions-end
     # impl-start
     init_base(import_name)
-    if len(name) == 0:
-        raise NameValidationError()
-    if contains_dot(ToSeq(name)):
+    if len(name) == 0 or contains_dot(ToSeq(name)):
+        other = list(import_name)
+        try:
+            init_base(other)
+        except BaseInitError:
+            raise BaseInitError()
         raise NameValidationError()
     return
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pallets__flask-5014.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A blueprint object is constructed from a textual *name*. Construction
  validates that name before the object is usable. The name is rejected — the
  constructor signals the caller with a name-validation error instead of
  building the object — in exactly two situations:

    (1) the name is the empty text (no code points at all), and
    (2) the name contains the dot code point U+002E ('.').

  In every other case (a non-empty name with no dot) construction proceeds
  normally. The empty-name rejection is the behaviour pinned here: a name with
  zero code points must raise the validation error rather than yielding a
  usable object.

The name is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The dot-membership predicate is carried by a pure fold over
`PSeq[int]`. The validation error is a user-defined exception class (a builtin
exception in an `Exsures` crashes the translator). The base construction that
runs before name validation is axiomatised as an opaque callee that does not
touch the name: it either completes or fails as a unit before any name check,
so it cannot turn a rejected name into an accepted one or vice versa. WHICH of
the two happens is not a function of that callee's own argument: it also turns
on ambient state the callee reads (and can itself change) and on a further
optional argument of the construction, neither of which this specification
carries. So each exit hands back its own independent WITNESS over the base
callee's argument — `base_init_can_complete` on normal completion,
`base_init_can_fail` on failure-as-a-unit — and neither witness is the negation
of the other. The two exit channels are still pinned: a name rejection can
arise only once the base init has already completed, so it carries the SUCCESS
witness, while the base-init channel demands the FAILURE witness, obtainable
only from a base call that actually failed — so the base-init channel cannot
absorb a name rejection.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NameValidationError(Exception):
    """Signals that the supplied construction name is not acceptable. Stands in
    for the `ValueError` the desired behaviour requires (a builtin exception in
    an `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


class BaseInitError(Exception):
    """Signals that the base construction performed before name validation
    failed as a unit. User-defined stand-in for the exception the opaque base
    callee may raise on some inputs (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass


# axioms-start
@Pure
@ContractOnly
def base_init_can_complete(import_name: PSeq[int]) -> bool:
    """WITNESS for the base callee's normal-completion channel: the base
    initialisation is able to complete as a unit on this `import_name`. Stated
    over the base callee's OWN argument — it says nothing about, and never
    reads, the blueprint `name`, faithful to the real base init, which is not
    even handed the name. It is deliberately an ATTAINABILITY claim rather than
    a decision procedure: for one `import_name` the real base init can complete
    on one call and fail on another, because it also consults an ambient table
    it may itself populate and an optional root-path argument that skips the
    consultation entirely (mapping.md §3.2). Nothing here says this witness and
    `base_init_can_fail` exclude each other; both can hold for the same
    argument. The proof relies only on where the fact comes FROM — a base call
    that actually completed — never on its truth-value, which is opaque on every
    concrete `import_name` (checked against the real callee by G-AX /
    axiom_check.py). Provenance: mapping.md §3."""
    Ensures(True)


@Pure
@ContractOnly
def base_init_can_fail(import_name: PSeq[int]) -> bool:
    """WITNESS for the base callee's failure-as-a-unit channel: the base
    initialisation is able to fail as a unit on this `import_name`, before any
    name check runs. Same shape as `base_init_can_complete` — an attainability
    claim over the base callee's own argument, silent about the blueprint
    `name`, opaque on every concrete argument, obtainable only from a base call
    that actually failed — and it is NOT the negation of the success witness:
    the real outcome for one `import_name` also turns on ambient state and on
    the optional root-path argument, so the two witnesses can both hold.
    Provenance: mapping.md §3."""
    Ensures(True)


@ContractOnly
def init_base(import_name: List[int]) -> None:
    """The base initialisation performed before the name is validated. It is
    independent of the `name` argument and performs no name validation. It is
    an opaque callee that either completes normally or, on some inputs in some
    ambient states, fails as a unit before any name check runs. Provenance:
    mapping.md §3."""
    Requires(Acc(list_pred(import_name), 1 / 2))
    # Normal completion: hands back the import_name permission together with the
    # SUCCESS witness for this argument — the only way to obtain that witness.
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(import_name), 1 / 2))
    Ensures(base_init_can_complete(ToSeq(import_name)))
    # Failure as a unit: hands back the import_name permission together with the
    # FAILURE witness for this argument — the only way to obtain that one. The
    # two witnesses are independent, so a call that ended one way says nothing
    # about how a different call ends: this contract is not stronger than a
    # callee whose outcome also depends on state and on arguments the model does
    # not carry.
    Exsures(BaseInitError,
            Acc(list_pred(import_name), 1 / 2)
            and base_init_can_fail(ToSeq(import_name)))
# axioms-end


# pure-start
@Pure
def contains_dot(s: PSeq[int]) -> bool:
    """True iff the sequence contains the dot code point U+002E (46).
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return False
    return s[0] == 46 or contains_dot(s.drop(1))
# pure-end


def validate_name(name: List[int], import_name: List[int]) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(import_name), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs: returned at the same fractional permission they were
    # required at (directive 5) — the validator mutates nothing observable.
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(import_name), 1 / 2))
    # Normal return is reachable ONLY for an accepted name: non-empty AND
    # dot-free. (An empty name must NOT return normally — it must raise.) A
    # normal return also carries the base callee's SUCCESS witness, so it is
    # reachable only once the base init has actually completed.
    Ensures(len(name) > 0)
    Ensures(not contains_dot(ToSeq(name)))
    Ensures(base_init_can_complete(ToSeq(import_name)))
    # The validation error is raised on EXACTLY the rejected names: empty, or
    # containing a dot — AND only once the base init has already COMPLETED (the
    # name guards run strictly after `init_base` returns). So a name rejection
    # carries the base callee's SUCCESS witness. This pins the reject set to
    # THIS channel: the base-init channel below demands the FAILURE witness,
    # which is obtainable only from a base call that actually failed and never
    # from one that returned, so a name rejection cannot be routed through it.
    # The read-only inputs are held at their fractional permission in the
    # exceptional post-state too (so the value constraint can mention
    # `name`/`import_name`).
    Exsures(NameValidationError,
            Acc(list_pred(name), 1 / 2) and Acc(list_pred(import_name), 1 / 2)
            and base_init_can_complete(ToSeq(import_name))
            and (len(name) == 0 or contains_dot(ToSeq(name))))
    # The base construction runs first and may fail as a unit; that failure
    # aborts construction BEFORE any name check, so it propagates unchanged and
    # says nothing about the name (no len/dot constraint). It carries the base
    # callee's FAILURE witness for `import_name` — the fact only a base call
    # that failed hands out — which is what keeps this channel from absorbing a
    # name rejection. It is NOT the negation of the success witness the other
    # two channels carry: both witnesses may hold for one `import_name`, which
    # is what the real callee does when ambient state or the optional root-path
    # argument decides the outcome. The read-only input permissions are returned
    # so the value side is well-formed.
    Exsures(BaseInitError,
            Acc(list_pred(name), 1 / 2) and Acc(list_pred(import_name), 1 / 2)
            and base_init_can_fail(ToSeq(import_name)))
    # post-conditions-end
    # impl-start
    init_base(import_name)
    if len(name) == 0:
        raise NameValidationError()
    if contains_dot(ToSeq(name)):
        raise NameValidationError()
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT — pallets__flask-5014 (nagini).

METHOD / TOOLING SANITY
All 15 files (pos_control + 14 attacks) were generated mechanically by build.py/build2.py/build3.py, which splice a new body between the literal '    # impl-start\n' / '    # impl-end\n' markers of the bundle's model.py, so axioms/@Pure/Requires/Ensures are byte-identical by construction (asserted impl_only=True per file). pos_control.py hashes to sha256 223efccd2edc… == the model.py recorded in the G-GOLD/G-AX/G-HYGIENE/G-PBT stamps, i.e. I audited the frozen artifact. `adversary same-spec` returned exit 0 SAME for all 15. Positive control: `adversary weakness nagini pallets__flask-5014 pos_control.py` -> exit 0 CANDIDATE (19.0s), so the verifier lane was live for every run below — no rejection here is a dead-tool artifact. Verifications were run 2–3 concurrently as background jobs (schedule only; every attack fully verified).

PER-ATTACK RESULTS — cmd: `python -m swebench_unified.adversary weakness nagini pallets__flask-5014 <path>`
1. atk_1.py  PREPATCH BUG re-encoded (dot guard only, no empty guard) -> exit 2 NOT-A-CE (does not verify). Prepatch reproduced: the spec senses the change via Ensures(len(name)>0). Bundle's model_prepatch.py also confirmed same-spec (exit 0).
2. atk_2.py  PARTIAL DOMAIN (dot rejected only at position 0; 'a.b' accepted) -> exit 2, rejected.
3. atk_3.py  BOUNDARY over-reject (len<=1 treated as empty; 1-char names rejected) -> exit 2, rejected.
4. atk_4.py  UNDER-REJECT (dot guard dropped) -> exit 2, rejected.
5. atk_5.py  CONTROL-FLOW EFFECT: reject routed through the BASE-INIT channel, harvesting base_init_can_fail from a SECOND init_base(import_name) call -> exit 0 CANDIDATE (17.3s). VERIFIES.
6. atk_6.py  REVERSE CHANNEL SWAP: a genuine base-init failure on a rejected name converted into NameValidationError -> exit 0 CANDIDATE (16.8s). VERIFIES.
7. atk_7.py  UNGROUNDED-ORACLE via recursive self-call to harvest the failure witness -> exit 2, rejected.
8. atk_8.py  DIVERGENCE (empty name loops forever instead of raising) -> exit 2, rejected (MustTerminate(6) at the method level bites).
9. atk_9.py  REORDER: name guards evaluated before init_base -> exit 0 CANDIDATE (15.3s). VERIFIES.
10. atk_10.py WITNESS-ARGUMENT CONFUSION: harvest the failure witness from init_base(name) instead of init_base(import_name) -> exit 2, rejected. The witnesses' argument binding is genuinely enforced.
11. atk_11.py DEAD-CHANNEL CONTROL (atk_5 + Assert(False) inside the BaseInitError handler) -> exit 2, does NOT verify. This is the key non-vacuity control (per MEMORY: guarded self-calls can go vacuous): the verifier does NOT prove atk_5's second base-init failure unreachable, so atk_5's exceptional leg is a real, non-vacuous path and its CANDIDATE status is meaningful rather than an infeasible-guard artifact.
12. atk_12.py PURE UNGROUNDED ECHO: `raise BaseInitError()` directly on the name-reject set with NO failing base call -> exit 2, REJECTED. This is the decisive A-leg result: the provenance pin (Exsures(BaseInitError, … base_init_can_fail(import_name)) obtainable only from a base call that actually failed) really does close the verify-not-resolve hole that mapping.md §3.2 says it closes. Had this verified, its faithful patch would raise ImportError instead of ValueError on Blueprint('', `__name__`) and fail the sole F2P.
13. atk_13.py PREDICATE-ARGUMENT CONFUSION (dot membership tested on import_name instead of name) -> exit 2, rejected.
14. atk_14.py WITNESS LAUNDERING via a copy (`other = list(import_name)`; the witnesses are functions of the PSeq VALUE, so a call on an equal list mints the witness for import_name) -> exit 0 CANDIDATE (24.0s). VERIFIES.

MANDATORY RESOLVE RUNS — every CANDIDATE's faithful refined patch materialized and EXECUTED through the official harness (swebench_unified.harness.run_resolve, real Docker oracle):
- atk_5  -> patch_atk_5.diff  -> RESOLVED: True, completed, applied; F2P 1/1 (test_empty_name_not_allowed) success, P2P 60/60 success, 0 failures.
- atk_6  -> patch_atk_6.diff  -> RESOLVED: True, applied; F2P 1/1, P2P 59/59, no failures.
- atk_9  -> patch_atk_9.diff  -> RESOLVED: True, applied; F2P 1/1, P2P 59/59, no failures.
- atk_14 -> patch_atk_14.diff -> RESOLVED: True, applied; F2P 1/1, P2P 59/59, no failures.
WHY they resolve (and why this is not luck): each of the 4 verifying rivals differs from gold only in RE-RUNNING the base initialisation on the reject path (atk_5/atk_14/atk_9) or in converting a base-init failure (atk_6). The base init is idempotent-enough and side-effect-free w.r.t. the name decision, and on the oracle's import_name = `__name__` (a resolvable module) it always COMPLETES — so the ValueError still fires on the reject set and the accept set still constructs. The residual divergences (atk_6's ImportError->ValueError conversion, atk_5/14's second base call) are latent on the F2P/P2P input set, exactly as refinement.md §A2/§C predicts ('on the tested oracle import_name = `__name__` the base init completes, so the failure path is never hit'). So verify => resolve holds for all of them: no break.

### REFINEMENT.MD LEG AUDIT (A-legs, per instruction)
Every leg is tagged R / A-consumed / A-reference / I — no kind-3: A1 R (str<->List[int]), A2 A-consumed (init_base <-> Scaffold.`__init__` via super().`__init__`), A3 R+I (the discriminating new empty guard, modelled deeply as len(name)==0 — NOT hidden behind an axiom about the function under change), A4 R+I (pre-existing dot check), A5 R (normal completion abstracts the unchanged field assignments). Verified against the real tree at base_commit 7ee9ceb7 (git show of blueprints.py:172-206, scaffold.py:76-110, helpers.py:562-600):
- A2 correspondence HOLDS: super().`__init__`(import_name=…, root_path=root_path) is called FIRST, before the dot check, and `name` is not even a parameter of Scaffold.`__init__` — so the axiom's name-silence is structurally true, and it cannot pre-empt the name guards. Both posts are load-bearing (refinement.md and mapping.md §3.1 report the proof FAILS if validate_name's Exsures(BaseInitError,…) is dropped).
- A-reference legs (base_init_can_complete / base_init_can_fail) correspondence HOLDS: I read get_root_path and confirmed all six legs described in mapping.md §3.1 — B1 sys.modules early return, B2 pkgutil.get_loader raising, B3/B4 os.getcwd(), B5 loader.get_filename, B6 `__import__` + the RuntimeError for a None `__file__`. The 'two independent attainability witnesses rather than one predicate' design is the FAITHFUL choice, and I confirmed the reasons empirically present in the source: get_root_path reads sys.modules (helpers.py:572) and WRITES it via `__import__` (helpers.py:590), and root_path is not None skips get_root_path entirely (scaffold.py:96), so the outcome is genuinely not a function of import_name alone. axiom_check.py asserts precisely these obligations: name-silence (base_init_failed_observed(imp,'ok') == (…,'alsofine') for all probed import_names, with ValueError correctly classified as a name-guard rejection rather than a base-init failure) and INDEPENDENCE (exhibits an import_name on which the real base init both raises with root_path=None and returns with root_path='/tmp', else it fails with 'the two independent witnesses are unmotivated'). This design also repairs the G-PANEL-2 UNFAITHFUL finding against the older determinism over-claim; atk_10/atk_12's rejections show the repair did not cost the channel pin.

### OUT-OF-GATE OBSERVATIONS (bookkeeping, not G-EQ findings; flagged for the bundle owner)
(a) meta.json's `axioms[0]` and `deep_model_references` still describe the SUPERSEDED design: they name a single deterministic predicate `base_init_failed` ('deterministic predicate of import_name ALONE', 'makes the channels DISJOINT'), a symbol that does not exist in the current model.py, which instead carries the two independent witnesses base_init_can_complete / base_init_can_fail. refinement.md and mapping.md ARE current and correct; only the meta records are stale. Worth refreshing so the recorded A-leg metadata matches the frozen artifact.
(b) The G-EQ / G-PANEL-1/2/3 stamps carry sources.model.py = eb4545c14b5fffb5, while the current model.py is 223efccd2edc — those agentic stamps predate the axiom rework (the mechanical gates G-AX/G-CONF/G-DIFF/G-GOLD/G-HYGIENE/G-INTEGRITY/G-LEAK/G-MUT/G-PBT/G-VERIFY all stamp the current hash). This audit re-establishes G-EQ against the CURRENT artifact.

**VERDICT:** SOUND. 14 distinct same-spec wrong impls run (>= the required 5, spanning prepatch-bug, partial-domain, boundary, under-reject, control-flow-effect in both directions, reorder, divergence, self-call harvest, witness/predicate argument confusion, witness laundering, pure ungrounded-oracle echo, plus an Assert(False) non-vacuity control). 10 were rejected by the spec; all 4 that verified had their faithful patches materialized and RUN through the official harness, and all 4 RESOLVED. No verify-and-not-resolve counterexample exists among them, and the A-leg correspondence to the real callees (Scaffold.`__init__` / get_root_path) checks out against the repo at base_commit.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_7.py`, `atk_8.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_5.py`, `atk_6.py`, `atk_9.py`, `atk_14.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 14 same-spec wrong impls were run; 10 were REJECTED by the frozen spec and the 4 that VERIFIED (atk_5, atk_6, atk_9, atk_14) all had their faithful refined patches materialized and executed through the official harness (run_resolve) — all 4 RESOLVED (F2P test_empty_name_not_allowed + 59/59 P2P green, patch applied). So no verifying wrong impl exhibits verify-and-not-resolve; the refinement claim survives falsification.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pallets__flask-5014.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A blueprint object is constructed from a textual *name*. Construction
  validates that name before the object is usable. The name is rejected — the
  constructor signals the caller with a name-validation error instead of
  building the object — in exactly two situations:

    (1) the name is the empty text (no code points at all), and
    (2) the name contains the dot code point U+002E ('.').

  In every other case (a non-empty name with no dot) construction proceeds
  normally. The empty-name rejection is the behaviour pinned here: a name with
  zero code points must raise the validation error rather than yielding a
  usable object.

The name is modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The dot-membership predicate is carried by a pure fold over
`PSeq[int]`. The validation error is a user-defined exception class (a builtin
exception in an `Exsures` crashes the translator). The base construction that
runs before name validation is axiomatised as an opaque callee that does not
touch the name: it either completes or fails as a unit before any name check,
so it cannot turn a rejected name into an accepted one or vice versa. WHICH of
the two happens is not a function of that callee's own argument: it also turns
on ambient state the callee reads (and can itself change) and on a further
optional argument of the construction, neither of which this specification
carries. So each exit hands back its own independent WITNESS over the base
callee's argument — `base_init_can_complete` on normal completion,
`base_init_can_fail` on failure-as-a-unit — and neither witness is the negation
of the other. The two exit channels are still pinned: a name rejection can
arise only once the base init has already completed, so it carries the SUCCESS
witness, while the base-init channel demands the FAILURE witness, obtainable
only from a base call that actually failed — so the base-init channel cannot
absorb a name rejection.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NameValidationError(Exception):
    """Signals that the supplied construction name is not acceptable. Stands in
    for the `ValueError` the desired behaviour requires (a builtin exception in
    an `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


class BaseInitError(Exception):
    """Signals that the base construction performed before name validation
    failed as a unit. User-defined stand-in for the exception the opaque base
    callee may raise on some inputs (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass


# axioms-start
@Pure
@ContractOnly
def base_init_can_complete(import_name: PSeq[int]) -> bool:
    """WITNESS for the base callee's normal-completion channel: the base
    initialisation is able to complete as a unit on this `import_name`. Stated
    over the base callee's OWN argument — it says nothing about, and never
    reads, the blueprint `name`, faithful to the real base init, which is not
    even handed the name. It is deliberately an ATTAINABILITY claim rather than
    a decision procedure: for one `import_name` the real base init can complete
    on one call and fail on another, because it also consults an ambient table
    it may itself populate and an optional root-path argument that skips the
    consultation entirely (mapping.md §3.2). Nothing here says this witness and
    `base_init_can_fail` exclude each other; both can hold for the same
    argument. The proof relies only on where the fact comes FROM — a base call
    that actually completed — never on its truth-value, which is opaque on every
    concrete `import_name` (checked against the real callee by G-AX /
    axiom_check.py). Provenance: mapping.md §3."""
    Ensures(True)


@Pure
@ContractOnly
def base_init_can_fail(import_name: PSeq[int]) -> bool:
    """WITNESS for the base callee's failure-as-a-unit channel: the base
    initialisation is able to fail as a unit on this `import_name`, before any
    name check runs. Same shape as `base_init_can_complete` — an attainability
    claim over the base callee's own argument, silent about the blueprint
    `name`, opaque on every concrete argument, obtainable only from a base call
    that actually failed — and it is NOT the negation of the success witness:
    the real outcome for one `import_name` also turns on ambient state and on
    the optional root-path argument, so the two witnesses can both hold.
    Provenance: mapping.md §3."""
    Ensures(True)


@ContractOnly
def init_base(import_name: List[int]) -> None:
    """The base initialisation performed before the name is validated. It is
    independent of the `name` argument and performs no name validation. It is
    an opaque callee that either completes normally or, on some inputs in some
    ambient states, fails as a unit before any name check runs. Provenance:
    mapping.md §3."""
    Requires(Acc(list_pred(import_name), 1 / 2))
    # Normal completion: hands back the import_name permission together with the
    # SUCCESS witness for this argument — the only way to obtain that witness.
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(import_name), 1 / 2))
    Ensures(base_init_can_complete(ToSeq(import_name)))
    # Failure as a unit: hands back the import_name permission together with the
    # FAILURE witness for this argument — the only way to obtain that one. The
    # two witnesses are independent, so a call that ended one way says nothing
    # about how a different call ends: this contract is not stronger than a
    # callee whose outcome also depends on state and on arguments the model does
    # not carry.
    Exsures(BaseInitError,
            Acc(list_pred(import_name), 1 / 2)
            and base_init_can_fail(ToSeq(import_name)))
# axioms-end


# pure-start
@Pure
def contains_dot(s: PSeq[int]) -> bool:
    """True iff the sequence contains the dot code point U+002E (46).
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return False
    return s[0] == 46 or contains_dot(s.drop(1))
# pure-end


def validate_name(name: List[int], import_name: List[int]) -> None:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(import_name), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs: returned at the same fractional permission they were
    # required at (directive 5) — the validator mutates nothing observable.
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(import_name), 1 / 2))
    # Normal return is reachable ONLY for an accepted name: non-empty AND
    # dot-free. (An empty name must NOT return normally — it must raise.) A
    # normal return also carries the base callee's SUCCESS witness, so it is
    # reachable only once the base init has actually completed.
    Ensures(len(name) > 0)
    Ensures(not contains_dot(ToSeq(name)))
    Ensures(base_init_can_complete(ToSeq(import_name)))
    # The validation error is raised on EXACTLY the rejected names: empty, or
    # containing a dot — AND only once the base init has already COMPLETED (the
    # name guards run strictly after `init_base` returns). So a name rejection
    # carries the base callee's SUCCESS witness. This pins the reject set to
    # THIS channel: the base-init channel below demands the FAILURE witness,
    # which is obtainable only from a base call that actually failed and never
    # from one that returned, so a name rejection cannot be routed through it.
    # The read-only inputs are held at their fractional permission in the
    # exceptional post-state too (so the value constraint can mention
    # `name`/`import_name`).
    Exsures(NameValidationError,
            Acc(list_pred(name), 1 / 2) and Acc(list_pred(import_name), 1 / 2)
            and base_init_can_complete(ToSeq(import_name))
            and (len(name) == 0 or contains_dot(ToSeq(name))))
    # The base construction runs first and may fail as a unit; that failure
    # aborts construction BEFORE any name check, so it propagates unchanged and
    # says nothing about the name (no len/dot constraint). It carries the base
    # callee's FAILURE witness for `import_name` — the fact only a base call
    # that failed hands out — which is what keeps this channel from absorbing a
    # name rejection. It is NOT the negation of the success witness the other
    # two channels carry: both witnesses may hold for one `import_name`, which
    # is what the real callee does when ambient state or the optional root-path
    # argument decides the outcome. The read-only input permissions are returned
    # so the value side is well-formed.
    Exsures(BaseInitError,
            Acc(list_pred(name), 1 / 2) and Acc(list_pred(import_name), 1 / 2)
            and base_init_can_fail(ToSeq(import_name)))
    # post-conditions-end
    # impl-start
    init_base(import_name)
    if len(name) == 0:
        raise NameValidationError()
    if contains_dot(ToSeq(name)):
        raise NameValidationError()
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL AUDIT — pallets__flask-5014 (nagini).

METHOD / TOOLING SANITY
All 15 files (pos_control + 14 attacks) were generated mechanically by build.py/build2.py/build3.py, which splice a new body between the literal '    # impl-start\n' / '    # impl-end\n' markers of the bundle's model.py, so axioms/@Pure/Requires/Ensures are byte-identical by construction (asserted impl_only=True per file). pos_control.py hashes to sha256 223efccd2edc… == the model.py recorded in the G-GOLD/G-AX/G-HYGIENE/G-PBT stamps, i.e. I audited the frozen artifact. `adversary same-spec` returned exit 0 SAME for all 15. Positive control: `adversary weakness nagini pallets__flask-5014 pos_control.py` -> exit 0 CANDIDATE (19.0s), so the verifier lane was live for every run below — no rejection here is a dead-tool artifact. Verifications were run 2–3 concurrently as background jobs (schedule only; every attack fully verified).

PER-ATTACK RESULTS — cmd: `python -m swebench_unified.adversary weakness nagini pallets__flask-5014 <path>`
1. atk_1.py  PREPATCH BUG re-encoded (dot guard only, no empty guard) -> exit 2 NOT-A-CE (does not verify). Prepatch reproduced: the spec senses the change via Ensures(len(name)>0). Bundle's model_prepatch.py also confirmed same-spec (exit 0).
2. atk_2.py  PARTIAL DOMAIN (dot rejected only at position 0; 'a.b' accepted) -> exit 2, rejected.
3. atk_3.py  BOUNDARY over-reject (len<=1 treated as empty; 1-char names rejected) -> exit 2, rejected.
4. atk_4.py  UNDER-REJECT (dot guard dropped) -> exit 2, rejected.
5. atk_5.py  CONTROL-FLOW EFFECT: reject routed through the BASE-INIT channel, harvesting base_init_can_fail from a SECOND init_base(import_name) call -> exit 0 CANDIDATE (17.3s). VERIFIES.
6. atk_6.py  REVERSE CHANNEL SWAP: a genuine base-init failure on a rejected name converted into NameValidationError -> exit 0 CANDIDATE (16.8s). VERIFIES.
7. atk_7.py  UNGROUNDED-ORACLE via recursive self-call to harvest the failure witness -> exit 2, rejected.
8. atk_8.py  DIVERGENCE (empty name loops forever instead of raising) -> exit 2, rejected (MustTerminate(6) at the method level bites).
9. atk_9.py  REORDER: name guards evaluated before init_base -> exit 0 CANDIDATE (15.3s). VERIFIES.
10. atk_10.py WITNESS-ARGUMENT CONFUSION: harvest the failure witness from init_base(name) instead of init_base(import_name) -> exit 2, rejected. The witnesses' argument binding is genuinely enforced.
11. atk_11.py DEAD-CHANNEL CONTROL (atk_5 + Assert(False) inside the BaseInitError handler) -> exit 2, does NOT verify. This is the key non-vacuity control (per MEMORY: guarded self-calls can go vacuous): the verifier does NOT prove atk_5's second base-init failure unreachable, so atk_5's exceptional leg is a real, non-vacuous path and its CANDIDATE status is meaningful rather than an infeasible-guard artifact.
12. atk_12.py PURE UNGROUNDED ECHO: `raise BaseInitError()` directly on the name-reject set with NO failing base call -> exit 2, REJECTED. This is the decisive A-leg result: the provenance pin (Exsures(BaseInitError, … base_init_can_fail(import_name)) obtainable only from a base call that actually failed) really does close the verify-not-resolve hole that mapping.md §3.2 says it closes. Had this verified, its faithful patch would raise ImportError instead of ValueError on Blueprint('', `__name__`) and fail the sole F2P.
13. atk_13.py PREDICATE-ARGUMENT CONFUSION (dot membership tested on import_name instead of name) -> exit 2, rejected.
14. atk_14.py WITNESS LAUNDERING via a copy (`other = list(import_name)`; the witnesses are functions of the PSeq VALUE, so a call on an equal list mints the witness for import_name) -> exit 0 CANDIDATE (24.0s). VERIFIES.

MANDATORY RESOLVE RUNS — every CANDIDATE's faithful refined patch materialized and EXECUTED through the official harness (swebench_unified.harness.run_resolve, real Docker oracle):
- atk_5  -> patch_atk_5.diff  -> RESOLVED: True, completed, applied; F2P 1/1 (test_empty_name_not_allowed) success, P2P 60/60 success, 0 failures.
- atk_6  -> patch_atk_6.diff  -> RESOLVED: True, applied; F2P 1/1, P2P 59/59, no failures.
- atk_9  -> patch_atk_9.diff  -> RESOLVED: True, applied; F2P 1/1, P2P 59/59, no failures.
- atk_14 -> patch_atk_14.diff -> RESOLVED: True, applied; F2P 1/1, P2P 59/59, no failures.
WHY they resolve (and why this is not luck): each of the 4 verifying rivals differs from gold only in RE-RUNNING the base initialisation on the reject path (atk_5/atk_14/atk_9) or in converting a base-init failure (atk_6). The base init is idempotent-enough and side-effect-free w.r.t. the name decision, and on the oracle's import_name = `__name__` (a resolvable module) it always COMPLETES — so the ValueError still fires on the reject set and the accept set still constructs. The residual divergences (atk_6's ImportError->ValueError conversion, atk_5/14's second base call) are latent on the F2P/P2P input set, exactly as refinement.md §A2/§C predicts ('on the tested oracle import_name = `__name__` the base init completes, so the failure path is never hit'). So verify => resolve holds for all of them: no break.

### REFINEMENT.MD LEG AUDIT (A-legs, per instruction)
Every leg is tagged R / A-consumed / A-reference / I — no kind-3: A1 R (str<->List[int]), A2 A-consumed (init_base <-> Scaffold.`__init__` via super().`__init__`), A3 R+I (the discriminating new empty guard, modelled deeply as len(name)==0 — NOT hidden behind an axiom about the function under change), A4 R+I (pre-existing dot check), A5 R (normal completion abstracts the unchanged field assignments). Verified against the real tree at base_commit 7ee9ceb7 (git show of blueprints.py:172-206, scaffold.py:76-110, helpers.py:562-600):
- A2 correspondence HOLDS: super().`__init__`(import_name=…, root_path=root_path) is called FIRST, before the dot check, and `name` is not even a parameter of Scaffold.`__init__` — so the axiom's name-silence is structurally true, and it cannot pre-empt the name guards. Both posts are load-bearing (refinement.md and mapping.md §3.1 report the proof FAILS if validate_name's Exsures(BaseInitError,…) is dropped).
- A-reference legs (base_init_can_complete / base_init_can_fail) correspondence HOLDS: I read get_root_path and confirmed all six legs described in mapping.md §3.1 — B1 sys.modules early return, B2 pkgutil.get_loader raising, B3/B4 os.getcwd(), B5 loader.get_filename, B6 `__import__` + the RuntimeError for a None `__file__`. The 'two independent attainability witnesses rather than one predicate' design is the FAITHFUL choice, and I confirmed the reasons empirically present in the source: get_root_path reads sys.modules (helpers.py:572) and WRITES it via `__import__` (helpers.py:590), and root_path is not None skips get_root_path entirely (scaffold.py:96), so the outcome is genuinely not a function of import_name alone. axiom_check.py asserts precisely these obligations: name-silence (base_init_failed_observed(imp,'ok') == (…,'alsofine') for all probed import_names, with ValueError correctly classified as a name-guard rejection rather than a base-init failure) and INDEPENDENCE (exhibits an import_name on which the real base init both raises with root_path=None and returns with root_path='/tmp', else it fails with 'the two independent witnesses are unmotivated'). This design also repairs the G-PANEL-2 UNFAITHFUL finding against the older determinism over-claim; atk_10/atk_12's rejections show the repair did not cost the channel pin.

### OUT-OF-GATE OBSERVATIONS (bookkeeping, not G-EQ findings; flagged for the bundle owner)
(a) meta.json's `axioms[0]` and `deep_model_references` still describe the SUPERSEDED design: they name a single deterministic predicate `base_init_failed` ('deterministic predicate of import_name ALONE', 'makes the channels DISJOINT'), a symbol that does not exist in the current model.py, which instead carries the two independent witnesses base_init_can_complete / base_init_can_fail. refinement.md and mapping.md ARE current and correct; only the meta records are stale. Worth refreshing so the recorded A-leg metadata matches the frozen artifact.
(b) The G-EQ / G-PANEL-1/2/3 stamps carry sources.model.py = eb4545c14b5fffb5, while the current model.py is 223efccd2edc — those agentic stamps predate the axiom rework (the mechanical gates G-AX/G-CONF/G-DIFF/G-GOLD/G-HYGIENE/G-INTEGRITY/G-LEAK/G-MUT/G-PBT/G-VERIFY all stamp the current hash). This audit re-establishes G-EQ against the CURRENT artifact.

**VERDICT:** SOUND. 14 distinct same-spec wrong impls run (>= the required 5, spanning prepatch-bug, partial-domain, boundary, under-reject, control-flow-effect in both directions, reorder, divergence, self-call harvest, witness/predicate argument confusion, witness laundering, pure ungrounded-oracle echo, plus an Assert(False) non-vacuity control). 10 were rejected by the spec; all 4 that verified had their faithful patches materialized and RUN through the official harness, and all 4 RESOLVED. No verify-and-not-resolve counterexample exists among them, and the A-leg correspondence to the real callees (Scaffold.`__init__` / get_root_path) checks out against the repo at base_commit.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 faithfulness-break attack on pallets__flask-5014 (nagini). Reference =  copied to  with patch.diff APPLIED (verified the `if not name: raise ValueError` guard is present at blueprints.py:193). Verdict: I could not find any input on which the modeled function disagrees with the real post-patch callee.

### CHECKS THAT PASSED (measurements, not opinions):

1. Spec integrity. `adversary same-spec nagini pallets__flask-5014` on a verbatim copy of model.py -> exit 0 ("SAME"). Nagini verifier on the bundle model.py -> exit 0. Bundle axiom_check.py against the patched tree -> exit 0 (G-AX OK).

2. Name decision, 20015 inputs, ZERO divergences. Differential fuzz of the model predicate (normal return iff len>0 and 46 not in codepoints; reject iff len==0 or dot) against the real patched Blueprint.`__init__` with resolvable import_name='flask'. Boundary + adversarial alphabet incl. '', '.', '..', 'a.b', '.a', 'a.', '  ', '\x00', 'x'*1000, 'e-acute', U+FF0E fullwidth full stop, U+2024 one-dot leader, U+1F600, lone surrogate \ud800. Every real outcome was permitted by the spec. Notably the refinement `not name` <-> len(name)==0 is exact: '\x00' and '  ' are truthy str and the real repo ACCEPTS both, matching the model (a naive "falsy/blank" reading would have been a real over-claim; it is not what the model says). Fullwidth/one-dot-leader lookalikes are not U+002E and the real repo accepts them, matching contains_dot.

3. Base-init name-silence CONFIRMED. For each import_name in {'no.such.pkg5014','flask','sys'} the base-step outcome was identical across 7 distinct blueprint names -> the raise/return decision never reads `name` (it is not a parameter of Scaffold.`__init__`). So stating both witnesses over import_name alone is sound.

4. Exception-class keying by STEP is measurable. Over 6018 import_name shapes with an accepted name the outcome histogram was ImportError 4066 / RuntimeError 34 / AttributeError 2 / RETURN 1916 and **ValueError count = 0**. So a ValueError from the prologue is unambiguously a name-guard reject, which is exactly what mapping.md 2 claims; BaseInitError = "base step failed as a unit" is a faithful fold of ImportError/RuntimeError/AttributeError.

5. The witness-INDEPENDENCE claim is TRUE, and the spec is not secretly stronger. This is where the earlier recorded UNFAITHFUL verdict bit, and the current model.py is the REPAIRED revision. Reproduced both flip directions on the real callee: (a) root_path route - import_name='no.such.pkg5014' raises ImportError with root_path=None but RETURNS with root_path='/tmp' (S4 skipped); (b) ambient sys.modules route - a real namespace package 'zzns5014' RETURNS before `import zzns5014` and raises RuntimeError after (`__file__` is None, leg B6). So a single deterministic predicate p(import_name) WOULD have been unfaithful, and the model correctly uses two non-exclusive attainability witnesses. I confirmed the spec does not covertly make them exclusive with a Nagini vacuity control: assuming base_init_can_complete AND base_init_can_fail for one import_name and asserting False -> "Assert might fail" (verification failed), i.e. the both-hold state is FEASIBLE under the frozen spec, matching reality. Had that Assert(False) verified, the spec would have been too strong; it does not.

6. Channel pin is faithful to real control flow. name in {'', 'a.b', 'ok'} x import_name in {'no.such.pkg5014', '.', 'sys'} all abort in the base step (ImportError/ImportError/RuntimeError) regardless of the name - i.e. the base failure really does pre-empt the name guards, and a name reject really can only occur after super().`__init__` returned. The provenance-based pin (reject carries the SUCCESS witness) asserts nothing false about the callee.

### Non-defects I examined and deliberately did not report

- MustTerminate over-claim, judged NOT a repo-reachable divergence. init_base carries Requires(MustTerminate(2)), yet the real chain get_root_path -> pkgutil.get_loader -> find_spec IMPORTS the parent package and thus runs arbitrary module-level code. I built a package whose `__init__`.py loops forever and Blueprint('', 'hangpkg5014.sub') genuinely DIVERGED (timeout 124; faulthandler traceback pins the hang at helpers.py:578 pkgutil.get_loader, inside scaffold.py:97 <- blueprints.py:185). I am NOT reporting this as UNFAITHFUL because the divergence is not a function of the modeled input: it requires injecting foreign non-terminating code onto sys.path. For every import_name string over the repo's own actual module set (6018 shapes swept, all terminated promptly) the base init terminates, so MustTerminate is sound on the reachable domain and the F2P/P2P oracle (import_name=`__name__`) is unaffected. Flagging it would condemn a correct spec on an environment-injection artifact.

- meta.json is STALE, but this is bookkeeping, not a spec defect. meta.json's 'axioms', 'string_modeling', 'deep_model_references' and the recorded G-PANEL-2 entry all still describe the SUPERSEDED design: a single deterministic predicate base_init_failed(import_name) that pinned the channels DISJOINTLY ("a function of import_name alone", "outcome is deterministic per import_name"). That claim is exactly the one my probes in item 5 refute, and it is what the recorded UNFAITHFUL verdict (model.py hash eb4545c1...) correctly condemned. The CURRENT model.py is hash 223efccd2edc979c1096f7898864d11136afa69d60814cda727871546ce584e2, and grep shows zero occurrences of base_init_failed in model.py / mapping.md / refinement.md - all three authoritative artifacts consistently use the two independent witnesses base_init_can_complete / base_init_can_fail (11/12/10 occurrences). G-AX, G-VERIFY, G-DIFF, G-MUT and G-LEAK were all re-run green at 18:16-18:26 against this current hash. Consequently meta.json's region_hashes for axioms / pre-conditions / post-conditions / spec_view MISMATCH the recomputed hashes of the shipped model.py (impl and pure regions still match) - they are leftovers from the pre-repair revision, as is the G-PANEL-2/G-EQ/G-PANEL-1/G-PANEL-3 metadata. This is a metadata-refresh issue for the orchestrator, not a divergence between the modeled function and the real repo, so it does not change my verdict. Recommend refreshing meta.json region_hashes and the axiom/deep-model prose to the witness-pair design.

**CONCLUSION:** the spec is neither too strong nor drifted. The one axis on which it is genuinely stronger than the real callee (termination through `__import__`) is unreachable from repo inputs, and the determinism over-claim that previously made this bundle UNFAITHFUL has been properly repaired and is now verifier-confirmed non-exclusive.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ARTIFACT JUDGED: consumer spec view generated live the way eval does it (markers.spec_view(model.py, nagini backend) == what eval/adapter.py:304 exposes in modes 1/2), model.py sha256 223efccd2edc979c1096f7898864d11136afa69d60814cda727871546ce584e2 (the same sha G-LEAK/G-AX/G-CONF are stamped against). Impl region confirmed elided ('... # implementation elided'); projection idempotent under re-projection.

PUBLIC BASELINE (problem_statement ONLY, hints_text is empty for this row so there is no hints-only vocabulary to echo): 'Require a non-empty name for Blueprints / Things do not work correctly if a Blueprint is given an empty name (e.g. #4944). It would be helpful if a ValueError was raised when trying to do that.' GOLD EDIT (3 added lines in src/flask/blueprints.py): blank + 'if not name:' + 'raise ValueError("'name' may not be empty.")', inserted after super().`__init__`(...) and before the pre-existing dot check.

**DECISIVE POINT:** the gold edit's entire behavioral content — empty Blueprint name must raise ValueError — is stated verbatim in the public problem_statement. The spec view therefore has essentially nothing left to leak; restating the demanded behavior is exactly what a spec is for.

### MECHANICAL CHECKS (all clean):
- leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch): passed=True, hard_failures=[], warnings=[] — reproduced independently, not read off meta.json.
- No gold added line present verbatim or whitespace-normalized: 'if not name:' -> False; 'raise ValueError("'name' may not be empty.")' -> False. The gold error MESSAGE string appears nowhere ('may not be empty' -> False).
- No diff markers (@@, diff --git, +++ , --- , index).
- No patched file path / module path: 'blueprints.py' -> False, 'flask.blueprints' -> False. ('flask' occurs only inside the instance id 'pallets__flask-5014' in line 1, which the consumer already holds as instance_id/repo.)
- No patched-repo-symbol echo: `_patch_changed_symbols`(gold) is empty (the only def on a changed line/section header is `__init__`, non-distinctive). 'Blueprint(' -> False, 'root_path' -> False, 'super().`__init__`' -> False, 'ValueError' appears only as the named stand-in target, and 'Blueprint'/'blueprint' is public problem_statement vocabulary.
- No hidden-test leak: 'test_empty_name_not_allowed' / 'test_blueprints' -> 0 occurrences.
- Narration sweep beyond the mechanical `_NARRATION` list (bug/fix/patched/previously/incorrectly/wrong/broken/regression + my own extras: 'no longer', 'used to', 'currently', 'erroneously', 'missing', 'omitted', 'forgot', 'add a check', 'insert', 'get_root_path', 'pkgutil', 'sys.modules', 'raise ValueError'): only hits are 'guard' ('the name guards run strictly after init_base returns') and 'before the' ('validates that name before the object is usable'). Both describe contract structure / desired behavior, not a bug->fix mechanism or diagnosis. No 'the bug was X', no 'now raises', no pre/post-patch framing anywhere.

### Two non-obvious angles I checked rather than assumed
1) The spec view also states the DOT rejection rule (code point U+002E, contains_dot). That is NOT gold-edit information: I checked out the real repo at base_commit 7ee9ceb71e868944a46e1ff00b506772a53a4f1d (worktree) and src/flask/blueprints.py:194 ALREADY contains `raise ValueError("'name' may not contain a dot '.' character.")` pre-patch. The dot rule is pre-existing public repo behavior inside the very range the consumer is handed as localization (Blueprint.`__init__`, src/flask/blueprints.py:172-206), so carrying it is faithfulness to the unchanged surrounding contract, not edit disclosure. The docstring is explicit that the EMPTY-name rejection is the behavior pinned here — i.e. it points at the public problem_statement, not at a hidden discriminator.
2) The Exsures(NameValidationError, ... and base_init_can_complete(...)) channel does pin that name rejection happens only AFTER the base init completes, which matches where gold inserts its guard. I judged this non-leaking: at base_commit the ordering (super().`__init__`(...) first, name check after) is already visible public code in the localized range, so the constraint is derivable from the unpatched repo the solver holds and adds nothing about the EDIT. Crucially it does NOT pin the empty-vs-dot ordering that gold chose: I built an attack that swaps the two guards (dot checked before empty) and `adversary same-spec nagini pallets__flask-5014` returned 'SAME — attack shares the bundle's exact specification' (exit 0), proving the frozen spec is order-agnostic between the two rejections and so does not hand over gold's precise insertion point.

**VERDICT:** the spec view reads as an abstract behavioral contract over List[int] code points with witness-based exit channels; every behavioral fact in it is either in the public problem_statement or in pre-existing base_commit code. No line exceeds the public baseline.

OUT-OF-SCOPE OBSERVATION (not my gate, not the basis of this verdict, flagging for the integrity/hygiene lane): meta.json region_hashes is STALE w.r.t. the shipped model.py — recomputing markers.region_hashes on the current model.py matches for 'impl' and 'pure' but DIFFERS for 'axioms', 'pre-conditions', 'post-conditions' and 'spec_view' (recorded spec_view 60f0e431..., recomputed c0e927e1...); the recorded hashes match neither model.py nor model_prepatch.py, so the contract regions were edited after region_hashes was written. This does not weaken my finding: the consumer's spec view is projected live from model.py (adapter.spec_view), and G-LEAK/G-AX/G-CONF are all stamped against the current model.py sha, which is the artifact I screened.

**ARTIFACT JUDGED:** consumer spec view generated live the way eval does it (markers.spec_view(model.py, nagini backend) == what eval/adapter.py:304 exposes in modes 1/2), model.py sha256 223efccd2edc979c1096f7898864d11136afa69d60814cda727871546ce584e2 (the same sha G-LEAK/G-AX/G-CONF are stamped against). Impl region confirmed elided ('... # implementation elided'); projection idempotent under re-projection.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
