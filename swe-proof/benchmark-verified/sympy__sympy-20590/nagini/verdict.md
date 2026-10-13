# P2 adversarial audit — sympy__sympy-20590

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_14.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -112,6 +112,8 @@
     Exsures(AttributeBindingRefused, all_closed_layout(chain))
     # post-conditions-end
     # impl-start
+    if len(chain) == 0:
+        return True
     if all_closed_layout(chain):
         raise AttributeBindingRefused()
     return True
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -112,7 +112,7 @@
     Exsures(AttributeBindingRefused, all_closed_layout(chain))
     # post-conditions-end
     # impl-start
-    if all_closed_layout(chain):
+    if len(chain) == 0 or chain[0]:
         raise AttributeBindingRefused()
     return True
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,7 +135,7 @@
     Ensures(Result() is True)
     # post-conditions-end
     # impl-start
-    return True
+    return False
     # impl-end
 
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -112,6 +112,10 @@
     Exsures(AttributeBindingRefused, all_closed_layout(chain))
     # post-conditions-end
     # impl-start
+    i = 0
+    while i < len(chain):
+        Invariant(i <= 0)
+        i = i - 1
     if all_closed_layout(chain):
         raise AttributeBindingRefused()
     return True
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -154,25 +154,9 @@
     Ensures(Result() is False)
     # post-conditions-end
     # impl-start
-    # The chain of the core expression type (root excluded): the type itself and
-    # its other contributing types pin closed layouts; the remaining contributing
-    # type pins a closed layout iff trait_pins_closed_layout() says so.
     trait = trait_pins_closed_layout()
     Assert(trait is True)
-    chain = PSeq(True, True, trait)  # type: PSeq[bool]
-    empty = PSeq()  # type: PSeq[bool]
-    Assert(all_closed_layout(empty))
-    one = PSeq(trait)  # type: PSeq[bool]
-    Assert(one.drop(len(one)) == empty)
-    Assert(all_closed_layout(one))
-    two = PSeq(True, trait)  # type: PSeq[bool]
-    Assert(two.drop(len(one)) == one)
-    Assert(all_closed_layout(two))
-    Assert(chain.drop(len(two)) == one)
-    Assert(chain.drop(len(one)) == two)
-    Assert(all_closed_layout(chain.drop(len(one))))
-    Assert(all_closed_layout(chain))
-    return instance_admits_namespace(chain)
+    return False
     # impl-end
 
 
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -154,23 +154,7 @@
     Ensures(Result() is False)
     # post-conditions-end
     # impl-start
-    # The chain of the core expression type (root excluded): the type itself and
-    # its other contributing types pin closed layouts; the remaining contributing
-    # type pins a closed layout iff trait_pins_closed_layout() says so.
-    trait = trait_pins_closed_layout()
-    Assert(trait is True)
-    chain = PSeq(True, True, trait)  # type: PSeq[bool]
-    empty = PSeq()  # type: PSeq[bool]
-    Assert(all_closed_layout(empty))
-    one = PSeq(trait)  # type: PSeq[bool]
-    Assert(one.drop(len(one)) == empty)
-    Assert(all_closed_layout(one))
-    two = PSeq(True, trait)  # type: PSeq[bool]
-    Assert(two.drop(len(one)) == one)
-    Assert(all_closed_layout(two))
-    Assert(chain.drop(len(two)) == one)
-    Assert(chain.drop(len(one)) == two)
-    Assert(all_closed_layout(chain.drop(len(one))))
+    chain = PSeq()  # type: PSeq[bool]
     Assert(all_closed_layout(chain))
     return instance_admits_namespace(chain)
     # impl-end
@@ -193,20 +177,7 @@
     Exsures(AttributeBindingRefused, True)
     # post-conditions-end
     # impl-start
-    trait = trait_pins_closed_layout()
-    Assert(trait is True)
-    chain = PSeq(True, True, trait)  # type: PSeq[bool]
-    empty = PSeq()  # type: PSeq[bool]
-    Assert(all_closed_layout(empty))
-    one = PSeq(trait)  # type: PSeq[bool]
-    Assert(one.drop(len(one)) == empty)
-    Assert(all_closed_layout(one))
-    two = PSeq(True, trait)  # type: PSeq[bool]
-    Assert(two.drop(len(one)) == one)
-    Assert(all_closed_layout(two))
-    Assert(chain.drop(len(two)) == one)
-    Assert(chain.drop(len(one)) == two)
-    Assert(all_closed_layout(chain.drop(len(one))))
+    chain = PSeq()  # type: PSeq[bool]
     Assert(all_closed_layout(chain))
     return bind_undeclared_attribute(chain)
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -154,23 +154,10 @@
     Ensures(Result() is False)
     # post-conditions-end
     # impl-start
-    # The chain of the core expression type (root excluded): the type itself and
-    # its other contributing types pin closed layouts; the remaining contributing
-    # type pins a closed layout iff trait_pins_closed_layout() says so.
     trait = trait_pins_closed_layout()
     Assert(trait is True)
-    chain = PSeq(True, True, trait)  # type: PSeq[bool]
-    empty = PSeq()  # type: PSeq[bool]
-    Assert(all_closed_layout(empty))
-    one = PSeq(trait)  # type: PSeq[bool]
-    Assert(one.drop(len(one)) == empty)
-    Assert(all_closed_layout(one))
-    two = PSeq(True, trait)  # type: PSeq[bool]
-    Assert(two.drop(len(one)) == one)
-    Assert(all_closed_layout(two))
-    Assert(chain.drop(len(two)) == one)
-    Assert(chain.drop(len(one)) == two)
-    Assert(all_closed_layout(chain.drop(len(one))))
+    chain = PSeq(trait)  # type: PSeq[bool]
+    Assert(all_closed_layout(chain.drop(1)))
     Assert(all_closed_layout(chain))
     return instance_admits_namespace(chain)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -193,20 +193,5 @@
     Exsures(AttributeBindingRefused, True)
     # post-conditions-end
     # impl-start
-    trait = trait_pins_closed_layout()
-    Assert(trait is True)
-    chain = PSeq(True, True, trait)  # type: PSeq[bool]
-    empty = PSeq()  # type: PSeq[bool]
-    Assert(all_closed_layout(empty))
-    one = PSeq(trait)  # type: PSeq[bool]
-    Assert(one.drop(len(one)) == empty)
-    Assert(all_closed_layout(one))
-    two = PSeq(True, trait)  # type: PSeq[bool]
-    Assert(two.drop(len(one)) == one)
-    Assert(all_closed_layout(two))
-    Assert(chain.drop(len(two)) == one)
-    Assert(chain.drop(len(one)) == two)
-    Assert(all_closed_layout(chain.drop(len(one))))
-    Assert(all_closed_layout(chain))
-    return bind_undeclared_attribute(chain)
+    raise AttributeBindingRefused()
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,6 +114,10 @@
     # impl-start
     if all_closed_layout(chain):
         raise AttributeBindingRefused()
+    b = True
+    while b:
+        Invariant(True)
+        b = True
     return True
     # impl-end
 
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,7 +135,7 @@
     Ensures(Result() is True)
     # post-conditions-end
     # impl-start
-    return True
+    raise AttributeBindingRefused()
     # impl-end
 
 
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -195,18 +195,5 @@
     # impl-start
     trait = trait_pins_closed_layout()
     Assert(trait is True)
-    chain = PSeq(True, True, trait)  # type: PSeq[bool]
-    empty = PSeq()  # type: PSeq[bool]
-    Assert(all_closed_layout(empty))
-    one = PSeq(trait)  # type: PSeq[bool]
-    Assert(one.drop(len(one)) == empty)
-    Assert(all_closed_layout(one))
-    two = PSeq(True, trait)  # type: PSeq[bool]
-    Assert(two.drop(len(one)) == one)
-    Assert(all_closed_layout(two))
-    Assert(chain.drop(len(two)) == one)
-    Assert(chain.drop(len(one)) == two)
-    Assert(all_closed_layout(chain.drop(len(one))))
-    Assert(all_closed_layout(chain))
-    return bind_undeclared_attribute(chain)
+    return True
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -154,25 +154,9 @@
     Ensures(Result() is False)
     # post-conditions-end
     # impl-start
-    # The chain of the core expression type (root excluded): the type itself and
-    # its other contributing types pin closed layouts; the remaining contributing
-    # type pins a closed layout iff trait_pins_closed_layout() says so.
     trait = trait_pins_closed_layout()
     Assert(trait is True)
-    chain = PSeq(True, True, trait)  # type: PSeq[bool]
-    empty = PSeq()  # type: PSeq[bool]
-    Assert(all_closed_layout(empty))
-    one = PSeq(trait)  # type: PSeq[bool]
-    Assert(one.drop(len(one)) == empty)
-    Assert(all_closed_layout(one))
-    two = PSeq(True, trait)  # type: PSeq[bool]
-    Assert(two.drop(len(one)) == one)
-    Assert(all_closed_layout(two))
-    Assert(chain.drop(len(two)) == one)
-    Assert(chain.drop(len(one)) == two)
-    Assert(all_closed_layout(chain.drop(len(one))))
-    Assert(all_closed_layout(chain))
-    return instance_admits_namespace(chain)
+    return True
     # impl-end
 
 
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -112,7 +112,7 @@
     Exsures(AttributeBindingRefused, all_closed_layout(chain))
     # post-conditions-end
     # impl-start
-    if all_closed_layout(chain):
+    if all_closed_layout(chain) or len(chain) > 5:
         raise AttributeBindingRefused()
     return True
     # impl-end
```

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -154,18 +154,15 @@
     Ensures(Result() is False)
     # post-conditions-end
     # impl-start
-    # The chain of the core expression type (root excluded): the type itself and
-    # its other contributing types pin closed layouts; the remaining contributing
-    # type pins a closed layout iff trait_pins_closed_layout() says so.
     trait = trait_pins_closed_layout()
     Assert(trait is True)
-    chain = PSeq(True, True, trait)  # type: PSeq[bool]
+    chain = PSeq(True, True, True)  # type: PSeq[bool]
     empty = PSeq()  # type: PSeq[bool]
     Assert(all_closed_layout(empty))
-    one = PSeq(trait)  # type: PSeq[bool]
+    one = PSeq(True)  # type: PSeq[bool]
     Assert(one.drop(len(one)) == empty)
     Assert(all_closed_layout(one))
-    two = PSeq(True, trait)  # type: PSeq[bool]
+    two = PSeq(True, True)  # type: PSeq[bool]
     Assert(two.drop(len(one)) == one)
     Assert(all_closed_layout(two))
     Assert(chain.drop(len(two)) == one)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-20590.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An instance of the core expression type must carry NO open per-instance
  namespace, so that binding an attribute name that the type did not pre-declare
  is rejected rather than silently stored.

  Whether an instance carries such an open namespace is decided entirely by the
  chain of types it is built from (its method-resolution order, excluding the
  universal root, which never contributes a namespace). The rule is the one the
  runtime applies:

    * an instance carries an open namespace iff AT LEAST ONE type in that chain
      leaves its instance layout open (does not pin a closed set of attribute
      slots);
    * equivalently, an instance carries NO open namespace iff EVERY type in the
      chain pins a closed layout.

  The behaviour pinned here is the consequence for attribute binding:

    * if the instance carries no open namespace (every type in the chain pins a
      closed layout) then binding an undeclared attribute name is REFUSED — the
      runtime signals the caller with an attribute error and stores nothing;
    * otherwise the open namespace absorbs the binding and it succeeds.

  In particular, for the core expression type's own chain — in which EVERY type
  is required to pin a closed layout — an instance must carry no open namespace,
  so binding an undeclared attribute must be refused.

The inheritance chain is modelled as a `PSeq[bool]`: one flag per type (root
excluded), True iff that type pins a closed layout. The closed-layout predicate
folds front-recursively so a single unfold is available per chain step. The
attribute error is a user-defined exception class (a builtin exception in an
`Exsures` crashes the Nagini translator; mapping.md). No callee is axiomatized:
the layout/namespace rule is modelled deeply.

TERMINATION. Every modelled operation is a bounded, loop-free decision the real
runtime always completes (attribute binding either stores or raises; reading a
class's slot declaration is immediate). Nagini verifies partial correctness
only, so each function carries a `MustTerminate` obligation: without it a
diverging body (an infinite loop before the return) would satisfy every
postcondition vacuously — in particular `Ensures(False)` — yet never deliver
its result, which does not resolve the F2P.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class AttributeBindingRefused(Exception):
    """Signals that binding an undeclared attribute name was refused because the
    instance carries no open namespace. Stands in for the `AttributeError` the
    runtime raises (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md §2)."""
    pass

# axioms-start
# (no axiomatized callees: the layout/namespace rule and the chain assembly are
# modelled deeply. The only operation this specification observes is whether the
# instance carries an open namespace, which is a pure function of the layout
# flags of the types in its chain — spelled out below — and the attribute-
# binding decision that follows from it.)
# axioms-end

# pure-start
@Pure
def all_closed_layout(chain: PSeq[bool]) -> bool:
    """True iff EVERY type in the chain pins a closed instance layout. Front-
    recursive over the chain so one unfold is available per step: the head must
    pin a closed layout and so must the tail."""
    if len(chain) == 0:
        return True
    return chain[0] and all_closed_layout(chain.drop(1))

@Pure
def instance_admits_namespace(chain: PSeq[bool]) -> bool:
    """True iff an instance built from this chain carries an open per-instance
    namespace: that happens iff at least one type leaves its layout open, i.e.
    iff NOT every type pins a closed layout."""
    return not all_closed_layout(chain)
# pure-end

def bind_undeclared_attribute(chain: PSeq[bool]) -> bool:
    # pre-conditions-start
    # `chain` is the instance's type chain (root excluded), one closed-layout
    # flag per type. A pure value sequence: no heap permission needed. The
    # attribute name being bound is one the types did not pre-declare (the
    # observed case).
    # TERMINATION: the runtime's attribute-binding step is a bounded, loop-free
    # decision — it either stores the binding or raises; it never diverges.
    # Nagini verifies partial correctness only, so without this obligation an
    # implementation that loops forever would satisfy the postconditions
    # vacuously. The smallest measure (1) lets every caller holding a strictly
    # larger obligation invoke this step without leaking its own obligation.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Binding succeeds (returns True, recording the binding in the namespace)
    # ONLY when the instance carries an open namespace, i.e. some type leaves its
    # layout open.
    Ensures(instance_admits_namespace(chain))
    Ensures(Result() is True)
    # Binding is REFUSED with the attribute error on EXACTLY the no-namespace
    # case: every type in the chain pins a closed layout.
    Exsures(AttributeBindingRefused, all_closed_layout(chain))
    # post-conditions-end
    # impl-start
    if all_closed_layout(chain):
        raise AttributeBindingRefused()
    return True
    # impl-end

def trait_pins_closed_layout() -> bool:
    # pre-conditions-start
    # TERMINATION: reading a class-level slot declaration is immediate — the
    # flag must actually be DELIVERED (total correctness), not merely never
    # contradicted by a diverging body. Measure 2 sits strictly between the
    # binding step's (1) and the observation functions' (3), so both call
    # directions discharge their obligations without leaking.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Every type contributing to the core expression type's chain pins a closed
    # instance layout (declares no open namespace of its own), so that combining
    # it with the other types does not re-open the layout of the types that use
    # it. This is the per-type flag the chain-level rule below quantifies over.
    Ensures(Result() is True)
    # post-conditions-end
    # impl-start
    return True
    # impl-end

def core_expression_instance_admits_namespace() -> bool:
    # pre-conditions-start
    # TERMINATION: the observation (does a fresh instance carry a __dict__?) is
    # a bounded query the real interpreter always completes; the F2P test's
    # `assert not hasattr(b1, '__dict__')` only passes if it RETURNS. Under
    # partial correctness a diverging body satisfies Ensures(Result() is False)
    # vacuously; this obligation rejects any such implementation.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The core expression type's instances carry NO open per-instance namespace:
    # every type in their chain pins a closed layout.
    Ensures(Result() is False)
    # post-conditions-end
    # impl-start
    # The chain of the core expression type (root excluded): the type itself and
    # its other contributing types pin closed layouts; the remaining contributing
    # type pins a closed layout iff trait_pins_closed_layout() says so.
    trait = trait_pins_closed_layout()
    Assert(trait is True)
    chain = PSeq(True, True, trait)  # type: PSeq[bool]
    empty = PSeq()  # type: PSeq[bool]
    Assert(all_closed_layout(empty))
    one = PSeq(trait)  # type: PSeq[bool]
    Assert(one.drop(len(one)) == empty)
    Assert(all_closed_layout(one))
    two = PSeq(True, trait)  # type: PSeq[bool]
    Assert(two.drop(len(one)) == one)
    Assert(all_closed_layout(two))
    Assert(chain.drop(len(two)) == one)
    Assert(chain.drop(len(one)) == two)
    Assert(all_closed_layout(chain.drop(len(one))))
    Assert(all_closed_layout(chain))
    return instance_admits_namespace(chain)
    # impl-end

def core_expression_bind_undeclared_attribute() -> bool:
    # pre-conditions-start
    # TERMINATION: the F2P test's `with raises(AttributeError): b1.x = 1` only
    # passes if the binding attempt COMPLETES by raising — an implementation
    # that hangs forever never raises and does not resolve. Under partial
    # correctness a diverging body satisfies Ensures(False) vacuously (no
    # normal exit is ever reached); this obligation forces the refusal to
    # actually be delivered.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # Binding an undeclared attribute on a core-expression instance is refused
    # with the attribute error: it never returns normally (no namespace exists).
    Ensures(False)
    Exsures(AttributeBindingRefused, True)
    # post-conditions-end
    # impl-start
    trait = trait_pins_closed_layout()
    Assert(trait is True)
    chain = PSeq(True, True, trait)  # type: PSeq[bool]
    empty = PSeq()  # type: PSeq[bool]
    Assert(all_closed_layout(empty))
    one = PSeq(trait)  # type: PSeq[bool]
    Assert(one.drop(len(one)) == empty)
    Assert(all_closed_layout(one))
    two = PSeq(True, trait)  # type: PSeq[bool]
    Assert(two.drop(len(one)) == one)
    Assert(all_closed_layout(two))
    Assert(chain.drop(len(two)) == one)
    Assert(chain.drop(len(one)) == two)
    Assert(all_closed_layout(chain.drop(len(one))))
    Assert(all_closed_layout(chain))
    return bind_undeclared_attribute(chain)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Positive control = byte-identical model.py copy: `bash scripts/nagini_verify.sh pos_control.py` -> Verification successful, 13.4s, exit 0.

Command form for every attack: `python -m swebench_unified.adversary weakness nagini sympy__sympy-20590 atk_N.py`.

### REJECTED (exit 2, spec rejected the wrong impl — 9):
- atk_1 partial-domain: bind returns True on len(chain)==0. Rejected by Ensures(instance_admits_namespace(chain)).
- atk_2 boundary/head-only: decision reads chain[0] only, ignores the tail. Rejected (wrong on [F,T]-shaped chains).
- atk_3 THE PREPATCH BUG: trait_pins_closed_layout returns False (= model_prepatch verbatim, Printable without __slots__). Rejected by its constant Ensures(Result() is True) => prepatch_reproduced=True.
- atk_4 control-flow-effect: input-dependent unbounded loop (`while i < len(chain): i = i - 1`) before the correct branch. Rejected by MustTerminate(1).
- atk_9 PARTIAL-DOMAIN DIVERGENCE (the sharpest new attack): correct on the all-closed F2P chain, hangs forever only on open-namespace chains — vacuity confined to the branch the F2P never takes. Rejected by MustTerminate(1) (measureless loop => obligation leak). This is the residual of the P1 hole and it is closed.
- atk_10 trait declaration raises (faithful patch = Printable class body raising at import; sympy unimportable). Rejected: uncovered exception, no Exsures on trait_pins_closed_layout.
- atk_11 F2P binding observation returns normally instead of refusing. Rejected by Ensures(False).
- atk_12 F2P namespace observation echoes True (Basic keeps a __dict__). Rejected by Ensures(Result() is False).
- atk_13 over-refusal boundary: also raises when len(chain) > 5. Rejected by Exsures(..., all_closed_layout(chain)).

CANDIDATES (exit 0, share spec AND verify — 5). EVERY ONE had its faithful refined patch MATERIALIZED and RUN through the official harness via swebench_unified.harness.run_resolve (timeout 3600, distinct run_ids geq-audit-atk{5,6,7,8,14}); ALL FIVE RESOLVED, so none is a weakness:
- atk_5 ungrounded-oracle echo: core_expression_instance_admits_namespace returns the literal `False` after calling trait_pins_closed_layout, without consulting all_closed_layout. resolve -> {"resolved": true, "completed": true, "attempts": 1}.
- atk_6 wrong deep-model chain: BOTH observations model the EMPTY chain (Basic's MRO dropped entirely; trait flag never consumed). resolve -> resolved: true.
- atk_7 RE-ENCODING OF THE PRIOR PASS'S UNRESOLVED CANDIDATE (verdict.md Role-1 atk_6, recorded "candidate; resolve did not complete — inconclusive", which is why the recorded G-EQ status is `fail`): namespace observation uses the 1-entry chain PSeq(trait) instead of PSeq(True,True,trait). resolve -> {"resolved": true, "completed": true, "attempts": 1}. The prior INCONCLUSIVE was a harness non-completion, NOT a spec defect; it is now discharged with an executed resolve.
- atk_8 re-encoding of the prior pass's correct-echo (verdict.md atk_7): the binding observation raises unconditionally. resolve -> resolved: true.
- atk_14 ungrounded chain literal: trait flag is called and asserted but its value discarded; the chain is hard-coded PSeq(True,True,True). resolve -> resolved: true.

Why all five are harmless rather than weaknesses (this is the load-bearing G-EQ argument, refinement.md §D): the observation functions core_expression_* are F2P-observation PINS, not the discrimination anchor. Refinement.md §D states this explicitly and correctly — it concedes that core_expression_instance_admits_namespace verifies for ANY all-closed chain (including a shorter or empty one) and does not by itself force Basic's exact MRO. Every candidate exploits exactly that stated slack, and in every case the faithful refined patch is unchanged (the gold hunk `Printable.__slots__ = ()`) because the discriminating clause the candidates leave untouched — trait_pins_closed_layout's Ensures(Result() is True), leg A1 — is what the real edit refines. A candidate that weakens only a downstream observation restates the same source edit, hence resolves. Conversely every attack that touched the anchor or the general chain-parametric contract (atk_3, atk_1/2/13, atk_11/12) was rejected. So the slack is documented, bounded, and non-load-bearing: verify => resolved holds on all 14.

### A-LEG AUDIT (my focus; R/I legs are G-CONF's).
- refinement.md legs are A1 I/R, A2 R, A3 A-reference, B1 A-reference+I, B2 A-reference+I, B3 I. NO kind-3 (unexpressible-changed-op) leg, and the §C claim of zero A-consumed rows is TRUE mechanically: model.py has no @ContractOnly and no Assume(); the axioms-start/axioms-end region contains only comments (zero declarations); meta.json axioms == [] with exactly 1 deep_model_reference. Confirmed by grep + region extraction.
- A3/B1/B2 (the single A-reference, CPython's __slots__ -> __dict__/AttributeError rule modelled deeply as the front-recursive conjunction all_closed_layout): `python axiom_check.py` -> exit 0, "modelled rule matches the interpreter on 4008 chains (boundary + fuzz)", including the gold [T,T,T] and prepatch [T,T,F] shapes. The rule is transcribed into the check from model.py and the interpreter side genuinely builds classes via type(...) and observes hasattr/AttributeError, so it is a real A-reference validation, not a self-comparison.
- A1 correspondence to the real callee: verified at base_commit cffd4e0f in the upstream repository — sympy/core/_print_helpers.py `class Printable:` (line 8) has NO __slots__ (grep returns nothing), and patch.diff adds `__slots__ = ()` to that class body. So `trait=False` really is the base_commit state and `trait=True` really is the gold edit; the discrimination anchor binds to the changed line.
- A2 correspondence (MRO <-> PSeq[bool]): verified at base_commit — basic.py:28 `class Basic(Printable, metaclass=ManagedProperties):` (single base), basic.py:72 `__slots__ = ('_mhash', ...)`, basic.py:1825 `Atom.__slots__ = ()`. I re-ran the structural shape through the real interpreter (mro_probe.py in the scratch dir, replicating a metaclass'd Basic over a Printable base): MRO-minus-object == ['Basic','Printable'] (TWO entries), flags [True,True] with Printable slotted -> hasattr __dict__ False and binding raises AttributeError; flags [True,False] unslotted -> __dict__ True and binding STORES. This confirms mapping.md's §2/D4 self-correction: the model's PSeq(True,True,trait) carries ONE EXTRA leading True beyond the real 2-entry MRO. The probe also confirms the padding is inert for both trait values (all_closed_layout is a conjunction, so [T,trait] and [T,T,trait] agree), so the discrepancy is disclosed, benign, and does not break correspondence. mapping.md states it accurately rather than claiming a nonexistent third abstract base — and G-CONF's L1 diffs the padded vs faithful chain, so the claim is tested rather than trusted.

VERDICT: SOUND. 14 attacks encoded and fully verified (>= the required 5, spanning partial-domain, boundary, control-flow-effect/divergence incl. the F2P-branch-confined variant, ungrounded-oracle echo, wrong-chain deep-model, import-time raise, plus the prepatch bug and both prior-pass named candidates). 9 rejected; all 5 verifying candidates had their faithful patches materialized and RESOLVED under the official harness (executed, not speculated). No verify-but-not-resolve witness exists. The prior recorded G-EQ fail was an infrastructure non-completion on the atk_6/atk_7 shape, and this pass discharges it with executed resolve results.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_14.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-20590.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An instance of the core expression type must carry NO open per-instance
  namespace, so that binding an attribute name that the type did not pre-declare
  is rejected rather than silently stored.

  Whether an instance carries such an open namespace is decided entirely by the
  chain of types it is built from (its method-resolution order, excluding the
  universal root, which never contributes a namespace). The rule is the one the
  runtime applies:

    * an instance carries an open namespace iff AT LEAST ONE type in that chain
      leaves its instance layout open (does not pin a closed set of attribute
      slots);
    * equivalently, an instance carries NO open namespace iff EVERY type in the
      chain pins a closed layout.

  The behaviour pinned here is the consequence for attribute binding:

    * if the instance carries no open namespace (every type in the chain pins a
      closed layout) then binding an undeclared attribute name is REFUSED — the
      runtime signals the caller with an attribute error and stores nothing;
    * otherwise the open namespace absorbs the binding and it succeeds.

  In particular, for the core expression type's own chain — in which EVERY type
  is required to pin a closed layout — an instance must carry no open namespace,
  so binding an undeclared attribute must be refused.

The inheritance chain is modelled as a `PSeq[bool]`: one flag per type (root
excluded), True iff that type pins a closed layout. The closed-layout predicate
folds front-recursively so a single unfold is available per chain step. The
attribute error is a user-defined exception class (a builtin exception in an
`Exsures` crashes the Nagini translator; mapping.md). No callee is axiomatized:
the layout/namespace rule is modelled deeply.

TERMINATION. Every modelled operation is a bounded, loop-free decision the real
runtime always completes (attribute binding either stores or raises; reading a
class's slot declaration is immediate). Nagini verifies partial correctness
only, so each function carries a `MustTerminate` obligation: without it a
diverging body (an infinite loop before the return) would satisfy every
postcondition vacuously — in particular `Ensures(False)` — yet never deliver
its result, which does not resolve the F2P.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class AttributeBindingRefused(Exception):
    """Signals that binding an undeclared attribute name was refused because the
    instance carries no open namespace. Stands in for the `AttributeError` the
    runtime raises (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md §2)."""
    pass

# axioms-start
# (no axiomatized callees: the layout/namespace rule and the chain assembly are
# modelled deeply. The only operation this specification observes is whether the
# instance carries an open namespace, which is a pure function of the layout
# flags of the types in its chain — spelled out below — and the attribute-
# binding decision that follows from it.)
# axioms-end

# pure-start
@Pure
def all_closed_layout(chain: PSeq[bool]) -> bool:
    """True iff EVERY type in the chain pins a closed instance layout. Front-
    recursive over the chain so one unfold is available per step: the head must
    pin a closed layout and so must the tail."""
    if len(chain) == 0:
        return True
    return chain[0] and all_closed_layout(chain.drop(1))

@Pure
def instance_admits_namespace(chain: PSeq[bool]) -> bool:
    """True iff an instance built from this chain carries an open per-instance
    namespace: that happens iff at least one type leaves its layout open, i.e.
    iff NOT every type pins a closed layout."""
    return not all_closed_layout(chain)
# pure-end

def bind_undeclared_attribute(chain: PSeq[bool]) -> bool:
    # pre-conditions-start
    # `chain` is the instance's type chain (root excluded), one closed-layout
    # flag per type. A pure value sequence: no heap permission needed. The
    # attribute name being bound is one the types did not pre-declare (the
    # observed case).
    # TERMINATION: the runtime's attribute-binding step is a bounded, loop-free
    # decision — it either stores the binding or raises; it never diverges.
    # Nagini verifies partial correctness only, so without this obligation an
    # implementation that loops forever would satisfy the postconditions
    # vacuously. The smallest measure (1) lets every caller holding a strictly
    # larger obligation invoke this step without leaking its own obligation.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Binding succeeds (returns True, recording the binding in the namespace)
    # ONLY when the instance carries an open namespace, i.e. some type leaves its
    # layout open.
    Ensures(instance_admits_namespace(chain))
    Ensures(Result() is True)
    # Binding is REFUSED with the attribute error on EXACTLY the no-namespace
    # case: every type in the chain pins a closed layout.
    Exsures(AttributeBindingRefused, all_closed_layout(chain))
    # post-conditions-end
    # impl-start
    if all_closed_layout(chain):
        raise AttributeBindingRefused()
    return True
    # impl-end

def trait_pins_closed_layout() -> bool:
    # pre-conditions-start
    # TERMINATION: reading a class-level slot declaration is immediate — the
    # flag must actually be DELIVERED (total correctness), not merely never
    # contradicted by a diverging body. Measure 2 sits strictly between the
    # binding step's (1) and the observation functions' (3), so both call
    # directions discharge their obligations without leaking.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Every type contributing to the core expression type's chain pins a closed
    # instance layout (declares no open namespace of its own), so that combining
    # it with the other types does not re-open the layout of the types that use
    # it. This is the per-type flag the chain-level rule below quantifies over.
    Ensures(Result() is True)
    # post-conditions-end
    # impl-start
    return True
    # impl-end

def core_expression_instance_admits_namespace() -> bool:
    # pre-conditions-start
    # TERMINATION: the observation (does a fresh instance carry a __dict__?) is
    # a bounded query the real interpreter always completes; the F2P test's
    # `assert not hasattr(b1, '__dict__')` only passes if it RETURNS. Under
    # partial correctness a diverging body satisfies Ensures(Result() is False)
    # vacuously; this obligation rejects any such implementation.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The core expression type's instances carry NO open per-instance namespace:
    # every type in their chain pins a closed layout.
    Ensures(Result() is False)
    # post-conditions-end
    # impl-start
    # The chain of the core expression type (root excluded): the type itself and
    # its other contributing types pin closed layouts; the remaining contributing
    # type pins a closed layout iff trait_pins_closed_layout() says so.
    trait = trait_pins_closed_layout()
    Assert(trait is True)
    chain = PSeq(True, True, trait)  # type: PSeq[bool]
    empty = PSeq()  # type: PSeq[bool]
    Assert(all_closed_layout(empty))
    one = PSeq(trait)  # type: PSeq[bool]
    Assert(one.drop(len(one)) == empty)
    Assert(all_closed_layout(one))
    two = PSeq(True, trait)  # type: PSeq[bool]
    Assert(two.drop(len(one)) == one)
    Assert(all_closed_layout(two))
    Assert(chain.drop(len(two)) == one)
    Assert(chain.drop(len(one)) == two)
    Assert(all_closed_layout(chain.drop(len(one))))
    Assert(all_closed_layout(chain))
    return instance_admits_namespace(chain)
    # impl-end

def core_expression_bind_undeclared_attribute() -> bool:
    # pre-conditions-start
    # TERMINATION: the F2P test's `with raises(AttributeError): b1.x = 1` only
    # passes if the binding attempt COMPLETES by raising — an implementation
    # that hangs forever never raises and does not resolve. Under partial
    # correctness a diverging body satisfies Ensures(False) vacuously (no
    # normal exit is ever reached); this obligation forces the refusal to
    # actually be delivered.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # Binding an undeclared attribute on a core-expression instance is refused
    # with the attribute error: it never returns normally (no namespace exists).
    Ensures(False)
    Exsures(AttributeBindingRefused, True)
    # post-conditions-end
    # impl-start
    trait = trait_pins_closed_layout()
    Assert(trait is True)
    chain = PSeq(True, True, trait)  # type: PSeq[bool]
    empty = PSeq()  # type: PSeq[bool]
    Assert(all_closed_layout(empty))
    one = PSeq(trait)  # type: PSeq[bool]
    Assert(one.drop(len(one)) == empty)
    Assert(all_closed_layout(one))
    two = PSeq(True, trait)  # type: PSeq[bool]
    Assert(two.drop(len(one)) == one)
    Assert(all_closed_layout(two))
    Assert(chain.drop(len(two)) == one)
    Assert(chain.drop(len(one)) == two)
    Assert(all_closed_layout(chain.drop(len(one))))
    Assert(all_closed_layout(chain))
    return bind_undeclared_attribute(chain)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Positive control = byte-identical model.py copy: `bash scripts/nagini_verify.sh pos_control.py` -> Verification successful, 13.4s, exit 0.

Command form for every attack: `python -m swebench_unified.adversary weakness nagini sympy__sympy-20590 atk_N.py`.

### REJECTED (exit 2, spec rejected the wrong impl — 9):
- atk_1 partial-domain: bind returns True on len(chain)==0. Rejected by Ensures(instance_admits_namespace(chain)).
- atk_2 boundary/head-only: decision reads chain[0] only, ignores the tail. Rejected (wrong on [F,T]-shaped chains).
- atk_3 THE PREPATCH BUG: trait_pins_closed_layout returns False (= model_prepatch verbatim, Printable without __slots__). Rejected by its constant Ensures(Result() is True) => prepatch_reproduced=True.
- atk_4 control-flow-effect: input-dependent unbounded loop (`while i < len(chain): i = i - 1`) before the correct branch. Rejected by MustTerminate(1).
- atk_9 PARTIAL-DOMAIN DIVERGENCE (the sharpest new attack): correct on the all-closed F2P chain, hangs forever only on open-namespace chains — vacuity confined to the branch the F2P never takes. Rejected by MustTerminate(1) (measureless loop => obligation leak). This is the residual of the P1 hole and it is closed.
- atk_10 trait declaration raises (faithful patch = Printable class body raising at import; sympy unimportable). Rejected: uncovered exception, no Exsures on trait_pins_closed_layout.
- atk_11 F2P binding observation returns normally instead of refusing. Rejected by Ensures(False).
- atk_12 F2P namespace observation echoes True (Basic keeps a __dict__). Rejected by Ensures(Result() is False).
- atk_13 over-refusal boundary: also raises when len(chain) > 5. Rejected by Exsures(..., all_closed_layout(chain)).

CANDIDATES (exit 0, share spec AND verify — 5). EVERY ONE had its faithful refined patch MATERIALIZED and RUN through the official harness via swebench_unified.harness.run_resolve (timeout 3600, distinct run_ids geq-audit-atk{5,6,7,8,14}); ALL FIVE RESOLVED, so none is a weakness:
- atk_5 ungrounded-oracle echo: core_expression_instance_admits_namespace returns the literal `False` after calling trait_pins_closed_layout, without consulting all_closed_layout. resolve -> {"resolved": true, "completed": true, "attempts": 1}.
- atk_6 wrong deep-model chain: BOTH observations model the EMPTY chain (Basic's MRO dropped entirely; trait flag never consumed). resolve -> resolved: true.
- atk_7 RE-ENCODING OF THE PRIOR PASS'S UNRESOLVED CANDIDATE (verdict.md Role-1 atk_6, recorded "candidate; resolve did not complete — inconclusive", which is why the recorded G-EQ status is `fail`): namespace observation uses the 1-entry chain PSeq(trait) instead of PSeq(True,True,trait). resolve -> {"resolved": true, "completed": true, "attempts": 1}. The prior INCONCLUSIVE was a harness non-completion, NOT a spec defect; it is now discharged with an executed resolve.
- atk_8 re-encoding of the prior pass's correct-echo (verdict.md atk_7): the binding observation raises unconditionally. resolve -> resolved: true.
- atk_14 ungrounded chain literal: trait flag is called and asserted but its value discarded; the chain is hard-coded PSeq(True,True,True). resolve -> resolved: true.

Why all five are harmless rather than weaknesses (this is the load-bearing G-EQ argument, refinement.md §D): the observation functions core_expression_* are F2P-observation PINS, not the discrimination anchor. Refinement.md §D states this explicitly and correctly — it concedes that core_expression_instance_admits_namespace verifies for ANY all-closed chain (including a shorter or empty one) and does not by itself force Basic's exact MRO. Every candidate exploits exactly that stated slack, and in every case the faithful refined patch is unchanged (the gold hunk `Printable.__slots__ = ()`) because the discriminating clause the candidates leave untouched — trait_pins_closed_layout's Ensures(Result() is True), leg A1 — is what the real edit refines. A candidate that weakens only a downstream observation restates the same source edit, hence resolves. Conversely every attack that touched the anchor or the general chain-parametric contract (atk_3, atk_1/2/13, atk_11/12) was rejected. So the slack is documented, bounded, and non-load-bearing: verify => resolved holds on all 14.

### A-LEG AUDIT (my focus; R/I legs are G-CONF's).
- refinement.md legs are A1 I/R, A2 R, A3 A-reference, B1 A-reference+I, B2 A-reference+I, B3 I. NO kind-3 (unexpressible-changed-op) leg, and the §C claim of zero A-consumed rows is TRUE mechanically: model.py has no @ContractOnly and no Assume(); the axioms-start/axioms-end region contains only comments (zero declarations); meta.json axioms == [] with exactly 1 deep_model_reference. Confirmed by grep + region extraction.
- A3/B1/B2 (the single A-reference, CPython's __slots__ -> __dict__/AttributeError rule modelled deeply as the front-recursive conjunction all_closed_layout): `python axiom_check.py` -> exit 0, "modelled rule matches the interpreter on 4008 chains (boundary + fuzz)", including the gold [T,T,T] and prepatch [T,T,F] shapes. The rule is transcribed into the check from model.py and the interpreter side genuinely builds classes via type(...) and observes hasattr/AttributeError, so it is a real A-reference validation, not a self-comparison.
- A1 correspondence to the real callee: verified at base_commit cffd4e0f in the upstream repository — sympy/core/_print_helpers.py `class Printable:` (line 8) has NO __slots__ (grep returns nothing), and patch.diff adds `__slots__ = ()` to that class body. So `trait=False` really is the base_commit state and `trait=True` really is the gold edit; the discrimination anchor binds to the changed line.
- A2 correspondence (MRO <-> PSeq[bool]): verified at base_commit — basic.py:28 `class Basic(Printable, metaclass=ManagedProperties):` (single base), basic.py:72 `__slots__ = ('_mhash', ...)`, basic.py:1825 `Atom.__slots__ = ()`. I re-ran the structural shape through the real interpreter (mro_probe.py in the scratch dir, replicating a metaclass'd Basic over a Printable base): MRO-minus-object == ['Basic','Printable'] (TWO entries), flags [True,True] with Printable slotted -> hasattr __dict__ False and binding raises AttributeError; flags [True,False] unslotted -> __dict__ True and binding STORES. This confirms mapping.md's §2/D4 self-correction: the model's PSeq(True,True,trait) carries ONE EXTRA leading True beyond the real 2-entry MRO. The probe also confirms the padding is inert for both trait values (all_closed_layout is a conjunction, so [T,trait] and [T,T,trait] agree), so the discrepancy is disclosed, benign, and does not break correspondence. mapping.md states it accurately rather than claiming a nonexistent third abstract base — and G-CONF's L1 diffs the padded vs faithful chain, so the claim is tested rather than trusted.

VERDICT: SOUND. 14 attacks encoded and fully verified (>= the required 5, spanning partial-domain, boundary, control-flow-effect/divergence incl. the F2P-branch-confined variant, ungrounded-oracle echo, wrong-chain deep-model, import-time raise, plus the prepatch bug and both prior-pass named candidates). 9 rejected; all 5 verifying candidates had their faithful patches materialized and RESOLVED under the official harness (executed, not speculated). No verify-but-not-resolve witness exists. The prior recorded G-EQ fail was an infrastructure non-completion on the atk_6/atk_7 shape, and this pass discharges it with executed resolve results.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region integrity first: markers.region_hashes(model.py, NaginiBackend) reproduces all six meta.json hashes byte-identically (spec_view a2b2be11..., impl dfc9947a..., pure f12b3f4c...), so the spec view I audited is authoritative. model.py verifies under the pinned Nagini verifier (exit 0, 13.98s).

Ground truth established in a CLEAN worktree at base_commit cffd4e0f86 (git worktree from the upstream repository; the pre-existing was dirty, so I did not trust it). Real MRO of Basic, object excluded, is exactly [Basic, Printable] — 2 entries.

PREPATCH (base_commit, Printable has no __slots__): hasattr(Basic(),'__dict__')==True, Basic().x=1 STORES, __dictoffset__==16. Model's prepatch chain PSeq(True,True,False) predicts admits_namespace=True and a successful bind. AGREES; and it fails the spec's Ensures(Result() is False)/Ensures(False), which is the correct discrimination (G-DIFF).

GOLD (added `__slots__ = ()` to Printable): hasattr==False, __dictoffset__==0, Basic().x=1 raises AttributeError('Basic' object has no attribute 'x'), and the real F2P test_immutable PASSES. Model's gold chain PSeq(True,True,True) predicts admits_namespace=False and a refusal. AGREES. trait_pins_closed_layout()'s Ensures(Result() is True) maps exactly onto Printable.__dict__['__slots__']==() being declared.

I attacked the abstraction itself rather than re-running the bundle's own harness:

(1) Independent reimplementation of all_closed_layout/instance_admits_namespace differentially tested against the real interpreter on 6047 real class chains built via type() (exhaustive lengths 0..10 + seeded fuzz to length 14): 0 mismatches.

(2) Exhaustive too-strong AND too-weak probe over all 8191 chains of length 0..12: zero chains where the spec demands a refusal but the runtime stores, and zero where it permits a store but the runtime refuses. The Exsures/Ensures split is exactly the runtime's iff.

(3) Empty-chain boundary (chain==[] denotes object itself): model says all_closed_layout([])==True so bind must raise; real object().x=1 raises AttributeError and object() has no __dict__. AGREES — the base case is not vacuous or backwards.

(4) Padding claim (mapping.md §2) TESTED, not trusted: real flag chain is [True,True] but the model uses PSeq(True,True,True). Under the front-recursive conjunction the extra leading True is provably inert — all_closed_layout([True,True])==all_closed_layout([True,True,True])==True — so the padding neither adds nor removes a namespace. Benign.

(5) Lossy-edge probes where a flag-chain abstraction of an MRO could plausibly break: multiple-inheritance diamonds all-slotted (model False / real no-__dict__, agree) and with one un-slotted arm (model True / real has __dict__ and stores, agree); and __slots__ containing '__dict__' (X.__slots__=('__dict__',) really DOES get a __dict__ — the naive 'declares' reading would be WRONG here, but mapping.md §2's bridge explicitly excludes chains listing '__dict__', so the documented bridge is the correct one).

(6) Independent sweep over 1672 real classes across 701 patched sympy modules: layout leg 1476 checked, behaviour leg 40 checked, 0 divergences after applying the documented scope. Restricted to Basic's own subclass tree: 25 behaviourally-eligible subclasses, 0 divergences (including the many subclasses that omit __slots__ and legitimately DO accept assignment — the model predicts admits=True for those, matching; the spec constrains Basic's chain, not every subclass).

HARNESS CAVEAT (not a spec defect, but should be logged). The bundle's recorded G-CONF=pass does NOT reproduce on this interpreter: conformance_check.py exits 1 with 1 disagreement at checked=455 — 'L2 instance_admits_namespace != real open-namespace observation, input operator.attrgetter MRO=['attrgetter'] flags=(False,), shadow True, real False'.

I attributed this precisely and it is NOT unfaithfulness of the spec: the fault is in the harness's forward bridge, not the model's rule. operator.attrgetter, _thread._local and array.array are C extension types that carry Py_TPFLAGS_HEAPTYPE (so all_heap() admits them) yet are Py_TPFLAGS_IMMUTABLETYPE with __dictoffset__==0 and no Python-level __slots__ in their body — so declares_closed_layout() proxies them to False while their real layout is closed. mapping.md §'Domain' already declares exactly this category out of the bridge's denotation ('__slots__ is a heap-type mechanism, so the flag has no denotation there'); all_heap() just under-implements that stated intent by testing only the HEAPTYPE bit.

Proof of attribution: feeding the same three types' LAYOUT-TRUTH flags (dictoffset==0) into the model's rule reproduces the interpreter exactly, and widening all_heap() to also exclude Py_TPFLAGS_IMMUTABLETYPE makes the bundle's own unmodified checker exit 0 with 109784 inputs / 0 disagreements (1468 real classes by layout, 108207 synthetic chains, both branches exercised 42339 refused / 65868 stored). So the divergence lives entirely in the observation's denotation on stdlib C types that are not in Basic's chain and are not what the spec quantifies over; the modeled functions never disagree with the real callee. Likely a CPython-version drift (3.10.20 here) in which stdlib C types became heap-flagged. Recommend tightening all_heap() so G-CONF stays reproducible.

Also independently reran axiom_check.py: exit 0, 4008 chains, 0 mismatch.

Conclusion: the spec is neither too strong nor drifting. On every input the spec constrains — the empty chain, all 8191 chains up to length 12, real diamonds, and Basic's actual [Basic, Printable] chain in both prepatch and gold states — the modeled functions agree with the real repo and the real interpreter. AttributeBindingRefused <-> AttributeError is behaviourally faithful, and the MustTerminate(1/2/3) obligations correctly pin totality for operations that really are bounded and loop-free. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE/INTEGRITY. Generated the real consumer projection via swebench_unified.markers.spec_view(model.py, nagini) = 178 lines. Recomputed region_hashes and compared to meta.json: ALL SIX MATCH (axioms/pure/pre/post/impl/spec_view = a2b2be11...), so I audited the frozen spec view, not a drifted copy. `adversary same-spec` on an identity copy exits 0. Confirmed via eval/adapter.py + eval/prompts.py that ONLY spec_view reaches consumers; refinement.md and mapping.md (which name Printable and quote the gold line freely) are construction-side and are NOT rendered into the agent prompt. Worktree at base_commit created under /tmp, used read-only, then `git worktree remove`d.

MECHANICAL SCREEN. leakage.screen(...) with the frozen row's real gold_patch/problem_statement: PASSED, zero hard failures, zero warnings. I proved this is NOT a vacuous pass by building five negative controls, each of which FIRES: (C1) naming 'Printable' in a comment -> L2/L3; (C2) renaming the helper to printable_pins_closed_layout -> L2/L5; (C3) inserting the patched path -> L2; (C4) reproducing the gold line -> L1; (C5) inserting 'fixes the bug' -> L3. The screen genuinely refutes on this instance, so the clean result is meaningful.

MANUAL SUBSTANCE (what the lexer cannot do). Gold edit = add `__slots__ = ()` to class Printable in sympy/core/_print_helpers.py. Grepped the spec view for every distinctive token of the edit and of its hints_text-only diagnosis: 'Printable', '__slots__', 'Basic', 'Symbol', '_print_helpers', 'mixin', 'Mixin', 'DefaultPrinting', 'EvalfMixin', '19425' -> ALL ABSENT. The view is de-identified into runtime-generic vocabulary ('core expression type', 'chain of types', 'pins a closed layout', 'open per-instance namespace'). The hints_text-only material (bisect to #19425, 'Basic now inherits DefaultPrinting', the EvalfMixin precedent) appears nowhere, which is the failure mode the guide flags as most common.

DECISIVE COUNTERFACTUAL. Leakage means info BEYOND problem_statement, so I ran two blinded localizer agents on a real base_commit checkout, both barred from git history, test files, and the network. (a) SPEC-VIEW-ONLY: reached sympy/core/_print_helpers.py::Printable + `__slots__ = ()`, but reported explicitly that the spec view named neither the file, the class, nor even Basic, and that identification came from its own MRO audit plus chasing the printing/defaults.py alias. (b) PROBLEM-STATEMENT-ONLY (control): reached the IDENTICAL file/class/line in 3 tool calls, and stated the report itself gave away the mechanism verbatim ('introduced because some parent class accidentally stopped defining __slots__'). The PS-only control localized the edit with LESS effort than the spec-view agent. Since the public issue already supplies the mechanism, the observable (__dict__ / AttributeError on assignment), and the entry point (Symbol/__slots__), and since one MRO walk mechanically yields the unique culprit, the spec view adds no localizing information beyond problem_statement. That is the definition of no leakage.

### Candidates considered and rejected

(1) The helper name `trait_pins_closed_layout`: Printable's own docstring says 'Mix in this trait into a class', so 'trait' echoes repo prose. Rejected as a leak because grep for 'trait' in sympy/ returns 4 unrelated sites (core/sympify.py:33, polys/domains/domainelement.py:1 and :11, printing/rust.py) besides _print_helpers.py:14, so the word is not uniquely identifying; it is a generic mixin noun, and the concept 'mixin' is already implied by the issue's 'some parent class'.

(2) Spec-view comments quoting the F2P assertions `assert not hasattr(b1, '__dict__')` and `with raises(AttributeError): b1.x = 1` (spec-view lines 144 and 161). This is the closest call in the bundle: it is verbatim hidden-test code, and `b1` is a test-local name. I did not raise it as LEAKAGE because (i) the nagini G-LEAK policy is gold-edit oriented, not test-leak oriented (the test-leak rules are the ears flavor's, per leakage.py's _ears_screen, and the formal flavors are documented to ignore test_patch); and (ii) substantively both assertions are direct restatements of the public issue, which already shows the AttributeError traceback on __dict__ access, so they reveal no edit location. Flagging for maintainer awareness, not as a gate failure.

(3) Chain shape PSeq(True, True, trait): mapping.md admits the middle True is inert padding beyond Basic's real 2-entry MRO, so the arity does not even disclose the true MRO length.

VERDICT NO-LEAKAGE. The spec view states abstract desired behaviour plus the general CPython layout rule; it never names the patched file, class, or symbol, never reproduces a gold line, never carries a diff marker or bug/fix narration, and confers no localization advantage over the solver-visible problem_statement, as demonstrated by the PS-only control reaching the same one-line fix faster.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
