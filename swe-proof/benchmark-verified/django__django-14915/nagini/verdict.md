# P2 adversarial audit — django__django-14915

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2_recursion.py`, `atk_3_partial.py`, `atk_4_unbounded.py`, `atk_5_raise.py`, `atk_6_prepatch.py`, `atk_7_const.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_1_infloop.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_infloop.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -86,5 +86,7 @@
         Ensures(Result() == value_identity(self.value))
         # post-conditions-end
         # impl-start
+        while True:
+            pass
         return value_identity(self.value)
         # impl-end
```

Attack 2 — `atk_2_recursion.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,5 +86,7 @@
         Ensures(Result() == value_identity(self.value))
         # post-conditions-end
         # impl-start
+        if self.value == self.value:
+            return self.membership_identity()
         return value_identity(self.value)
         # impl-end
```

Attack 3 — `atk_3_partial.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,5 +86,8 @@
         Ensures(Result() == value_identity(self.value))
         # post-conditions-end
         # impl-start
-        return value_identity(self.value)
+        if self.value >= 0:
+            return value_identity(self.value)
+        while True:
+            pass
         # impl-end
```

Attack 4 — `atk_4_unbounded.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,5 +86,8 @@
         Ensures(Result() == value_identity(self.value))
         # post-conditions-end
         # impl-start
+        i = 0
+        while i >= 0:
+            i = i + 1
         return value_identity(self.value)
         # impl-end
```

Attack 5 — `atk_5_raise.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,5 +86,5 @@
         Ensures(Result() == value_identity(self.value))
         # post-conditions-end
         # impl-start
-        return value_identity(self.value)
+        raise Exception('boom')
         # impl-end
```

Attack 6 — `atk_6_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,5 +86,5 @@
         Ensures(Result() == value_identity(self.value))
         # post-conditions-end
         # impl-start
-        return value_identity(self.value)
+        return value_identity(self.instance)
         # impl-end
```

Attack 7 — `atk_7_const.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,5 +86,5 @@
         Ensures(Result() == value_identity(self.value))
         # post-conditions-end
         # impl-start
-        return value_identity(self.value)
+        return value_identity(0)
         # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14915.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lightweight wrapper that carries a stored lookup value together with the
  domain object it was derived from must be usable as a dictionary key / set
  member. Its membership identity is the membership identity of the *stored
  value* it wraps, and ONLY that value: the object it was derived from does
  not participate. Consequently two wrappers carrying the same stored value
  share one membership identity even when they were derived from different
  domain objects (or from none at all), and a wrapper carrying value ``v`` has
  the same membership identity as the bare value ``v`` would. Distinct stored
  values keep the distinct membership identities the values themselves have.

  Concretely: the wrapper's membership identity equals the membership identity
  of its wrapped value (``Result() == value_identity(self.value)``), computed
  from ``value`` alone and never from the derived-object field.

The wrapper is modelled as a minimal class carrying only the two touched
facets: the stored value (an integer key) and an integer standing for the
identity of the derived domain object. The membership identity of a bare
stored value is the one unchanged stdlib callee the operation defers to; it is
axiomatized as a single pure (hence deterministic) function of its argument.

The operation is a bounded, straight-line delegation to that primitive: it
MUST terminate (a total-correctness obligation, carried as MustTerminate in
the precondition). An implementation that diverges — e.g. hangs instead of
returning the wrapped value's identity — would satisfy the value
postconditions only vacuously and would hang every membership lookup (and
the F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def value_identity(v: int) -> int:
    """The unchanged stdlib membership-identity primitive applied to a bare
    stored value. As a `@Pure` function it is a single mathematical function of
    its one argument: the same value always yields the same identity, and
    the result is derived from `v` and nothing else. This is the weakest
    sufficient contract; it deliberately does NOT claim global injectivity,
    which the primitive does not provide (distinct values may, in principle,
    collide). Provenance + executable soundness check: mapping.md /
    axiom_check.py.
    """
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

class ChoiceValue:
    def __init__(self, value: int, instance: int) -> None:
        Ensures(Acc(self.value) and self.value == value)        # type: ignore
        Ensures(Acc(self.instance) and self.instance == instance)  # type: ignore
        self.value = value
        self.instance = instance

    def membership_identity(self) -> int:
        # pre-conditions-start
        Requires(Acc(self.value, 1 / 2) and Acc(self.instance, 1 / 2))
        # Total correctness: the real operation is a bounded, straight-line
        # delegation to the unchanged stdlib primitive — it must TERMINATE.
        # Without this obligation a diverging impl (e.g. an infinite loop)
        # satisfies every value postcondition vacuously yet would hang every
        # membership lookup (and the F2P test) forever.
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.value, 1 / 2) and Acc(self.instance, 1 / 2))
        # The wrapper is read-only: its facets are unchanged.
        Ensures(self.value == Old(self.value))
        Ensures(self.instance == Old(self.instance))
        # The discriminating guarantee: the membership identity is exactly the
        # membership identity of the WRAPPED VALUE, computed from `value` alone.
        # It therefore does not depend on the derived-object facet `instance`,
        # so two wrappers with equal `value` agree, and a wrapper agrees with
        # the bare value it wraps.
        Ensures(Result() == value_identity(self.value))
        # post-conditions-end
        # impl-start
        return value_identity(self.value)
        # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: adversarial G-EQ (refinement fidelity, plan §4) for nagini bundle django__django-14915. FROZEN spec: ChoiceValue.membership_identity Requires(Acc(value,1/2) and Acc(instance,1/2)) + MustTerminate(1); Ensures fields unchanged AND Result()==value_identity(self.value), with value_identity a @Pure @ContractOnly uninterpreted deterministic fn of one arg (models built-in hash). Gold patch = adds `def __hash__(self): return hash(self.value)` to ModelChoiceIteratorValue.

PROTOCOL. verifier via python -m swebench_unified.adversary and scripts/nagini_verify.sh. Encoded 7 DISTINCT wrong impls (only the impl region edited; axioms/@Pure/Requires/Ensures byte-identical — confirmed same-spec exit 0 for all 7 and positive_control). Ran weakness checks concurrently in batches of ≤3 (each spawns JVM+Z3). ALL 7 came back exit=2 (NOT-A-COUNTEREXAMPLE: verifies=False); no attack was a CANDIDATE, so NO faithful patch needed materializing/run_resolve. Positive control verifies (nagini_verify.sh rc=0, 6.35s). Each rejection except atk_1_infloop confirmed a genuine SEMANTIC verification failure (fast 2.5-7.9s, not timeout/infra) via `verify`; atk_1_infloop never reached the verifier, so the spec never ruled on it:

atk_1_infloop  (`while True: pass` then correct return)  -> exit2; Type error dead.code @91 — a front-end translation refusal, so NOT JUDGED: the spec never ruled on it and it counts in neither tally; the shape is unexpressible in nagini's fragment, so it did not exercise method-level MustTerminate.

CMD: adversary weakness nagini django__django-14915 atk_1_infloop.py. atk_2_recursion (self-recursion guarded)                 -> exit2; Obligation leak: callee membership_identity might not take all unsatisfied obligations (MustTerminate rejects unbounded recursion). atk_3_partial  (correct on value>=0, diverges else)       -> exit2; Obligation leak on loop (partial-domain divergence rejected). atk_4_unbounded (i=0; while i>=0: i+=1)                    -> exit2; Obligation leak: loop might not take all unsatisfied obligations. atk_5_raise    (raise Exception('boom'))                   -> exit2; Exhale might fail: 'method raises no exceptions' (control-flow-effect blocked). atk_6_prepatch (return value_identity(self.instance))      -> exit2; Postcondition Result()==value_identity(self.value) might not hold (PREPATCH BUG reproduced — identity keyed on derived object not wrapped value). atk_7_const    (return value_identity(0))                  -> exit2; Postcondition Result()==value_identity(self.value) might not hold (uninterpreted value_identity forces the argument to be exactly self.value; boundary/ungrounded-oracle echo rejected).

Each command form: `python -m swebench_unified.adversary weakness nagini django__django-14915 atk_N.py` (exit 2 for all), corroborated by `... verify ...` (FAILED with the error lines above). Logs: *.log, verify_positive.log.

REFINEMENT.MD AUDIT. Legs A1=R (ChoiceValue<->ModelChoiceIteratorValue, value/instance field bijection), A2=I (self.value read), A3=A-consumed (value_identity<->built-in hash; proof consumes determinism to discharge postcondition; G-AX validates real hash), A4=I (return callee result), A5=I (MustTerminate total-correctness leg on straight-line gold body). No kind-3 leg; §B explicitly argues the added operation is a delegation to the UNCHANGED stdlib hash primitive (A-consumed), and the changed op (the __hash__ method definition) is modeled directly & verified, not axiomatized. No deep-model A-reference exists to falsify. The single A-leg correspondence (value_identity == hash on int keys) is exactly what axiom_check.py exercises (determinism on boundary+20000 fuzz + F2P non-collision hash(c1.pk)!=hash(c2.pk)). A5's teeth were empirically confirmed by atk_2-4 being rejected under MustTerminate (atk_1_infloop never reached the verifier — the front end refused it, so it bears neither way on the clause) — the leg is load-bearing, not decorative.

VERDICT: SOUND. ≥5 (7 encoded, 6 machine-checked — atk_1_infloop was refused by the front end and never judged) distinct verifying-wrong-impl attacks; none shares-spec-AND-verifies, so verify⇒correct holds on the exhibited attack surface (termination/divergence, control-flow-effect, wrong-field/prepatch, boundary/ungrounded-oracle). No verifying wrong impl exists whose faithful patch could fail resolve, so no run_resolve was required. Positive control verifies; prepatch reproduced. Advisory only — runner re-runs the artifacts.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2_recursion.py`, `atk_3_partial.py`, `atk_4_unbounded.py`, `atk_5_raise.py`, `atk_6_prepatch.py`, `atk_7_const.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_1_infloop.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_infloop.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 2 — `atk_2_recursion.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_partial.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_unbounded.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_raise.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_prepatch.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_const.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14915.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lightweight wrapper that carries a stored lookup value together with the
  domain object it was derived from must be usable as a dictionary key / set
  member. Its membership identity is the membership identity of the *stored
  value* it wraps, and ONLY that value: the object it was derived from does
  not participate. Consequently two wrappers carrying the same stored value
  share one membership identity even when they were derived from different
  domain objects (or from none at all), and a wrapper carrying value ``v`` has
  the same membership identity as the bare value ``v`` would. Distinct stored
  values keep the distinct membership identities the values themselves have.

  Concretely: the wrapper's membership identity equals the membership identity
  of its wrapped value (``Result() == value_identity(self.value)``), computed
  from ``value`` alone and never from the derived-object field.

The wrapper is modelled as a minimal class carrying only the two touched
facets: the stored value (an integer key) and an integer standing for the
identity of the derived domain object. The membership identity of a bare
stored value is the one unchanged stdlib callee the operation defers to; it is
axiomatized as a single pure (hence deterministic) function of its argument.

The operation is a bounded, straight-line delegation to that primitive: it
MUST terminate (a total-correctness obligation, carried as MustTerminate in
the precondition). An implementation that diverges — e.g. hangs instead of
returning the wrapped value's identity — would satisfy the value
postconditions only vacuously and would hang every membership lookup (and
the F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def value_identity(v: int) -> int:
    """The unchanged stdlib membership-identity primitive applied to a bare
    stored value. As a `@Pure` function it is a single mathematical function of
    its one argument: the same value always yields the same identity, and
    the result is derived from `v` and nothing else. This is the weakest
    sufficient contract; it deliberately does NOT claim global injectivity,
    which the primitive does not provide (distinct values may, in principle,
    collide). Provenance + executable soundness check: mapping.md /
    axiom_check.py.
    """
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

class ChoiceValue:
    def __init__(self, value: int, instance: int) -> None:
        Ensures(Acc(self.value) and self.value == value)        # type: ignore
        Ensures(Acc(self.instance) and self.instance == instance)  # type: ignore
        self.value = value
        self.instance = instance

    def membership_identity(self) -> int:
        # pre-conditions-start
        Requires(Acc(self.value, 1 / 2) and Acc(self.instance, 1 / 2))
        # Total correctness: the real operation is a bounded, straight-line
        # delegation to the unchanged stdlib primitive — it must TERMINATE.
        # Without this obligation a diverging impl (e.g. an infinite loop)
        # satisfies every value postcondition vacuously yet would hang every
        # membership lookup (and the F2P test) forever.
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.value, 1 / 2) and Acc(self.instance, 1 / 2))
        # The wrapper is read-only: its facets are unchanged.
        Ensures(self.value == Old(self.value))
        Ensures(self.instance == Old(self.instance))
        # The discriminating guarantee: the membership identity is exactly the
        # membership identity of the WRAPPED VALUE, computed from `value` alone.
        # It therefore does not depend on the derived-object facet `instance`,
        # so two wrappers with equal `value` agree, and a wrapper agrees with
        # the bare value it wraps.
        Ensures(Result() == value_identity(self.value))
        # post-conditions-end
        # impl-start
        return value_identity(self.value)
        # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: adversarial G-EQ (refinement fidelity, plan §4) for nagini bundle django__django-14915. FROZEN spec: ChoiceValue.membership_identity Requires(Acc(value,1/2) and Acc(instance,1/2)) + MustTerminate(1); Ensures fields unchanged AND Result()==value_identity(self.value), with value_identity a @Pure @ContractOnly uninterpreted deterministic fn of one arg (models built-in hash). Gold patch = adds `def __hash__(self): return hash(self.value)` to ModelChoiceIteratorValue.

PROTOCOL. verifier via python -m swebench_unified.adversary and scripts/nagini_verify.sh. Encoded 7 DISTINCT wrong impls (only the impl region edited; axioms/@Pure/Requires/Ensures byte-identical — confirmed same-spec exit 0 for all 7 and positive_control). Ran weakness checks concurrently in batches of ≤3 (each spawns JVM+Z3). ALL 7 came back exit=2 (NOT-A-COUNTEREXAMPLE: verifies=False); no attack was a CANDIDATE, so NO faithful patch needed materializing/run_resolve. Positive control verifies (nagini_verify.sh rc=0, 6.35s). Each rejection except atk_1_infloop confirmed a genuine SEMANTIC verification failure (fast 2.5-7.9s, not timeout/infra) via `verify`; atk_1_infloop never reached the verifier, so the spec never ruled on it:

atk_1_infloop  (`while True: pass` then correct return)  -> exit2; Type error dead.code @91 — a front-end translation refusal, so NOT JUDGED: the spec never ruled on it and it counts in neither tally; the shape is unexpressible in nagini's fragment, so it did not exercise method-level MustTerminate.

CMD: adversary weakness nagini django__django-14915 atk_1_infloop.py. atk_2_recursion (self-recursion guarded)                 -> exit2; Obligation leak: callee membership_identity might not take all unsatisfied obligations (MustTerminate rejects unbounded recursion). atk_3_partial  (correct on value>=0, diverges else)       -> exit2; Obligation leak on loop (partial-domain divergence rejected). atk_4_unbounded (i=0; while i>=0: i+=1)                    -> exit2; Obligation leak: loop might not take all unsatisfied obligations. atk_5_raise    (raise Exception('boom'))                   -> exit2; Exhale might fail: 'method raises no exceptions' (control-flow-effect blocked). atk_6_prepatch (return value_identity(self.instance))      -> exit2; Postcondition Result()==value_identity(self.value) might not hold (PREPATCH BUG reproduced — identity keyed on derived object not wrapped value). atk_7_const    (return value_identity(0))                  -> exit2; Postcondition Result()==value_identity(self.value) might not hold (uninterpreted value_identity forces the argument to be exactly self.value; boundary/ungrounded-oracle echo rejected).

Each command form: `python -m swebench_unified.adversary weakness nagini django__django-14915 atk_N.py` (exit 2 for all), corroborated by `... verify ...` (FAILED with the error lines above). Logs: *.log, verify_positive.log.

REFINEMENT.MD AUDIT. Legs A1=R (ChoiceValue<->ModelChoiceIteratorValue, value/instance field bijection), A2=I (self.value read), A3=A-consumed (value_identity<->built-in hash; proof consumes determinism to discharge postcondition; G-AX validates real hash), A4=I (return callee result), A5=I (MustTerminate total-correctness leg on straight-line gold body). No kind-3 leg; §B explicitly argues the added operation is a delegation to the UNCHANGED stdlib hash primitive (A-consumed), and the changed op (the __hash__ method definition) is modeled directly & verified, not axiomatized. No deep-model A-reference exists to falsify. The single A-leg correspondence (value_identity == hash on int keys) is exactly what axiom_check.py exercises (determinism on boundary+20000 fuzz + F2P non-collision hash(c1.pk)!=hash(c2.pk)). A5's teeth were empirically confirmed by atk_2-4 being rejected under MustTerminate (atk_1_infloop never reached the verifier — the front end refused it, so it bears neither way on the clause) — the leg is load-bearing, not decorative.

VERDICT: SOUND. ≥5 (7 encoded, 6 machine-checked — atk_1_infloop was refused by the front end and never judged) distinct verifying-wrong-impl attacks; none shares-spec-AND-verifies, so verify⇒correct holds on the exhibited attack surface (termination/divergence, control-flow-effect, wrong-field/prepatch, boundary/ungrounded-oracle). No verifying wrong impl exists whose faithful patch could fail resolve, so no run_resolve was required. Positive control verifies; prepatch reproduced. Advisory only — runner re-runs the artifacts.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack fails to find drift; spec is FAITHFUL (not too strong).

Real callee: gold patch adds `ModelChoiceIteratorValue.__hash__` = `return hash(self.value)` (django/forms/models.py, verified at base_commit 903aaa35e5). Modeled function: `ChoiceValue.membership_identity` with postcondition `Result() == value_identity(self.value)` where `value_identity` is `@Pure @ContractOnly` (uninterpreted, deterministic function of one int argument).

Why faithful (spec is if anything WEAKER, never stronger, than the real callee):
1. value_identity carries the weakest sufficient contract — a deterministic function of `value` alone. It deliberately does NOT claim injectivity, so it never over-constrains: any impl returning hash(self.value) satisfies it. Confirmed real `hash` is deterministic (axiom_check.py G-AX exit 0: 22 boundary + 20000 fuzz keys).
2. Instance-independence matches the gold: real __hash__ reads only self.value, never instance; spec forbids result depending on instance (Acc 1/2, Old-preserved). No divergence.
3. MustTerminate(1) matches gold's straight-line single-expression body (always terminates). Not an over-claim — the real callee genuinely terminates on every input.
4. Empirical sweep: 200,018 int values × 5 instance objects — the postcondition-required value hash(self.value) equals the real callee ModelChoiceIteratorValue.__hash__ on EVERY input; 0 divergences.

Cross-checks: model.py verifies (Nagini exit 0, 5.95s); axiom_check.py exit 0; spec region byte-identical (same-spec self-check returns SAME). model_prepatch.py (return value_identity(self.instance)) correctly FAILS the postcondition, so the spec genuinely senses the change (G-DIFF). No diverging input exists within the modeled int domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: add `def __hash__(self): return hash(self.value)` to ModelChoiceIteratorValue in django/forms/models.py. Public problem_statement already discloses the class name (ModelChoiceIteratorValue), the defect (unhashable -> TypeError, must be usable as dict key), and the hashability concept.

Spec view (model.py with impl region elided) reviewed in full. Findings:
- No diff markers (@@, +++, ---, diff --git, index) present.
- No gold-patch changed line reproduced. `return hash(self.value)` does NOT appear; it is abstracted to the postcondition `Result() == value_identity(self.value)` over the model symbols `ChoiceValue`/`membership_identity`. The impl region is elided ('...  # implementation elided').
- Patched file path `django/forms/models.py` / dotted module `django.forms.models` absent from the spec view.
- Patched repo symbols are abstracted, not echoed: the spec uses invented names ChoiceValue / membership_identity / value_identity, never `ModelChoiceIteratorValue` or `__hash__`. The only distinctive changed symbol `__hash__` normalizes to 'hash', which is already public via 'hashable' in the problem statement, so it is not a leak (leak.py correctly skips symbols present in the problem statement).
- No bug/fix narration tokens (bug, fix, patch, prepatch, regression, previously, wrong, broken, ...) in any spec-view comment or docstring. Comments describe desired behavior and Nagini mechanics (permissions, MustTerminate) only.

Mechanical G-LEAK screen (swebench_unified.leakage.screen over spec_view) run directly: passed=True, hard_failures=[]. Confirmed against the frozen problem_statement (not hints_text).

Semantic check: the spec view reveals LESS edit-localization than the public problem statement (it hides the real class/method/file the statement already names). The behavioral guarantee it states (a wrapper's membership identity is the identity of its wrapped value, independent of the derived object) is the specification itself — pinning correct behavior is required of a spec and is not leakage of the gold edit. No line points a solver to `__hash__`/`return hash(self.value)` beyond what the public statement already implies.

Spec region byte-identity is not at issue for this gate (this is the reference bundle's own spec view); no attack file was needed to reach a leakage verdict.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
