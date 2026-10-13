# P2 adversarial audit — django__django-15916

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     # pre-conditions-start
     Requires(meta_own >= 0)
     Requires(meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The selected builder is exactly the one resolvable from the options
@@ -74,10 +72,7 @@
     Ensures(Implies(meta_own != 0, Result() != 0))
     # post-conditions-end
     # impl-start
-    # The options object stores its resolved builder; the constructor reads it
-    # straight from there to drive field construction.
-    stored = resolve_attr(meta_own, meta_inherited)
-    return stored
+    return meta_own
     # impl-end
 
 
@@ -92,7 +87,6 @@
     Requires(passed >= 0)
     Requires(base_meta_own >= 0)
     Requires(base_meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The produced options object's own builder is the one passed to the
@@ -119,12 +113,8 @@
     )
     # post-conditions-end
     # impl-start
-    # The factory records the passed builder on the produced options object
-    # only when one was given; it never injects an overriding "no builder".
-    # The produced options object therefore resolves (passed shadows the
-    # inherited base builder), and the constructor reads that resolved value.
     produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
-    produced_own = passed  # 0 when nothing was passed -> inherited is seen
+    produced_own = passed
     stored = resolve_attr(produced_own, produced_inherited)
     return stored
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     # pre-conditions-start
     Requires(meta_own >= 0)
     Requires(meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The selected builder is exactly the one resolvable from the options
@@ -74,10 +72,7 @@
     Ensures(Implies(meta_own != 0, Result() != 0))
     # post-conditions-end
     # impl-start
-    # The options object stores its resolved builder; the constructor reads it
-    # straight from there to drive field construction.
-    stored = resolve_attr(meta_own, meta_inherited)
-    return stored
+    return meta_inherited
     # impl-end
 
 
@@ -92,7 +87,6 @@
     Requires(passed >= 0)
     Requires(base_meta_own >= 0)
     Requires(base_meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The produced options object's own builder is the one passed to the
@@ -119,12 +113,8 @@
     )
     # post-conditions-end
     # impl-start
-    # The factory records the passed builder on the produced options object
-    # only when one was given; it never injects an overriding "no builder".
-    # The produced options object therefore resolves (passed shadows the
-    # inherited base builder), and the constructor reads that resolved value.
     produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
-    produced_own = passed  # 0 when nothing was passed -> inherited is seen
+    produced_own = passed
     stored = resolve_attr(produced_own, produced_inherited)
     return stored
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     # pre-conditions-start
     Requires(meta_own >= 0)
     Requires(meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The selected builder is exactly the one resolvable from the options
@@ -74,8 +72,6 @@
     Ensures(Implies(meta_own != 0, Result() != 0))
     # post-conditions-end
     # impl-start
-    # The options object stores its resolved builder; the constructor reads it
-    # straight from there to drive field construction.
     stored = resolve_attr(meta_own, meta_inherited)
     return stored
     # impl-end
@@ -92,7 +88,6 @@
     Requires(passed >= 0)
     Requires(base_meta_own >= 0)
     Requires(base_meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The produced options object's own builder is the one passed to the
@@ -119,12 +114,5 @@
     )
     # post-conditions-end
     # impl-start
-    # The factory records the passed builder on the produced options object
-    # only when one was given; it never injects an overriding "no builder".
-    # The produced options object therefore resolves (passed shadows the
-    # inherited base builder), and the constructor reads that resolved value.
-    produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
-    produced_own = passed  # 0 when nothing was passed -> inherited is seen
-    stored = resolve_attr(produced_own, produced_inherited)
-    return stored
+    return passed
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     # pre-conditions-start
     Requires(meta_own >= 0)
     Requires(meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The selected builder is exactly the one resolvable from the options
@@ -74,10 +72,9 @@
     Ensures(Implies(meta_own != 0, Result() != 0))
     # post-conditions-end
     # impl-start
-    # The options object stores its resolved builder; the constructor reads it
-    # straight from there to drive field construction.
-    stored = resolve_attr(meta_own, meta_inherited)
-    return stored
+    if meta_own > 1:
+        return meta_own
+    return meta_inherited
     # impl-end
 
 
@@ -92,7 +89,6 @@
     Requires(passed >= 0)
     Requires(base_meta_own >= 0)
     Requires(base_meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The produced options object's own builder is the one passed to the
@@ -119,12 +115,8 @@
     )
     # post-conditions-end
     # impl-start
-    # The factory records the passed builder on the produced options object
-    # only when one was given; it never injects an overriding "no builder".
-    # The produced options object therefore resolves (passed shadows the
-    # inherited base builder), and the constructor reads that resolved value.
     produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
-    produced_own = passed  # 0 when nothing was passed -> inherited is seen
+    produced_own = passed
     stored = resolve_attr(produced_own, produced_inherited)
     return stored
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     # pre-conditions-start
     Requires(meta_own >= 0)
     Requires(meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The selected builder is exactly the one resolvable from the options
@@ -74,10 +72,9 @@
     Ensures(Implies(meta_own != 0, Result() != 0))
     # post-conditions-end
     # impl-start
-    # The options object stores its resolved builder; the constructor reads it
-    # straight from there to drive field construction.
-    stored = resolve_attr(meta_own, meta_inherited)
-    return stored
+    if meta_own == 3:
+        return 999
+    return resolve_attr(meta_own, meta_inherited)
     # impl-end
 
 
@@ -92,7 +89,6 @@
     Requires(passed >= 0)
     Requires(base_meta_own >= 0)
     Requires(base_meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The produced options object's own builder is the one passed to the
@@ -119,12 +115,8 @@
     )
     # post-conditions-end
     # impl-start
-    # The factory records the passed builder on the produced options object
-    # only when one was given; it never injects an overriding "no builder".
-    # The produced options object therefore resolves (passed shadows the
-    # inherited base builder), and the constructor reads that resolved value.
     produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
-    produced_own = passed  # 0 when nothing was passed -> inherited is seen
+    produced_own = passed
     stored = resolve_attr(produced_own, produced_inherited)
     return stored
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     # pre-conditions-start
     Requires(meta_own >= 0)
     Requires(meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The selected builder is exactly the one resolvable from the options
@@ -74,8 +72,6 @@
     Ensures(Implies(meta_own != 0, Result() != 0))
     # post-conditions-end
     # impl-start
-    # The options object stores its resolved builder; the constructor reads it
-    # straight from there to drive field construction.
     stored = resolve_attr(meta_own, meta_inherited)
     return stored
     # impl-end
@@ -92,7 +88,6 @@
     Requires(passed >= 0)
     Requires(base_meta_own >= 0)
     Requires(base_meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The produced options object's own builder is the one passed to the
@@ -119,12 +114,8 @@
     )
     # post-conditions-end
     # impl-start
-    # The factory records the passed builder on the produced options object
-    # only when one was given; it never injects an overriding "no builder".
-    # The produced options object therefore resolves (passed shadows the
-    # inherited base builder), and the constructor reads that resolved value.
     produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
-    produced_own = passed  # 0 when nothing was passed -> inherited is seen
-    stored = resolve_attr(produced_own, produced_inherited)
-    return stored
+    if produced_inherited != 0:
+        return produced_inherited
+    return passed
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     # pre-conditions-start
     Requires(meta_own >= 0)
     Requires(meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The selected builder is exactly the one resolvable from the options
@@ -74,9 +72,10 @@
     Ensures(Implies(meta_own != 0, Result() != 0))
     # post-conditions-end
     # impl-start
-    # The options object stores its resolved builder; the constructor reads it
-    # straight from there to drive field construction.
-    stored = resolve_attr(meta_own, meta_inherited)
+    if meta_own != 0:
+        stored = meta_own
+    else:
+        stored = meta_inherited
     return stored
     # impl-end
 
@@ -92,7 +91,6 @@
     Requires(passed >= 0)
     Requires(base_meta_own >= 0)
     Requires(base_meta_inherited >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The produced options object's own builder is the one passed to the
@@ -119,12 +117,9 @@
     )
     # post-conditions-end
     # impl-start
-    # The factory records the passed builder on the produced options object
-    # only when one was given; it never injects an overriding "no builder".
-    # The produced options object therefore resolves (passed shadows the
-    # inherited base builder), and the constructor reads that resolved value.
-    produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
-    produced_own = passed  # 0 when nothing was passed -> inherited is seen
-    stored = resolve_attr(produced_own, produced_inherited)
-    return stored
+    if passed != 0:
+        return passed
+    if base_meta_own != 0:
+        return base_meta_own
+    return base_meta_inherited
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15916.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a model-backed form class is constructed, the per-field builder that
  turns each model field into a form field is selected from the form's own
  options/configuration object. The selection follows ordinary attribute
  resolution on that options object:

    - if the options object declares its own builder, that builder is used;
    - otherwise the builder inherited from the options object's parent (the
      base form's options) is used;
    - otherwise no custom builder is used (the model's default applies).

  This rule holds uniformly for two construction paths:

    (1) a class declared directly with a model-backed options object that
        carries a builder; and
    (2) a class produced by the run-time factory from a base form whose
        options object carries a builder (with no builder passed to the
        factory) -- and likewise for any further subclass of that produced
        class.

  In every case the builder that ends up driving field construction is the one
  resolvable from the options object, never silently replaced by "no builder".

Identities (callbacks / builders, options objects) are modelled as small
integer codes: 0 denotes "absent / no builder"; any positive value denotes a
specific builder identity. An options object is modelled as a pair (own
builder, inherited builder) capturing attribute resolution through its parent.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: this behaviour is a pure attribute-resolution / data-flow change,
# modelled deeply over integer identity codes; no unchanged opaque callee is
# consumed inside a contract.)
# axioms-end


# pure-start
@Pure
def resolve_attr(own: int, inherited: int) -> int:
    """Ordinary attribute resolution on an options object: an attribute set
    directly on the object (own != 0) shadows the one inherited from its
    parent (inherited); when the object sets nothing of its own (own == 0) the
    inherited value is seen. 0 denotes "attribute absent" on either level."""
    if own != 0:
        return own
    return inherited
# pure-end


def declared_form_callback(meta_own: int, meta_inherited: int) -> int:
    # The builder selected for a form class declared directly from a
    # model-backed options object carrying (meta_own, meta_inherited).
    # pre-conditions-start
    Requires(meta_own >= 0)
    Requires(meta_inherited >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The selected builder is exactly the one resolvable from the options
    # object: own shadows inherited; absence of both yields "no builder".
    Ensures(Result() == resolve_attr(meta_own, meta_inherited))
    Ensures(Implies(meta_own != 0, Result() == meta_own))
    Ensures(Implies(meta_own == 0, Result() == meta_inherited))
    # A builder declared on the options object is never lost.
    Ensures(Implies(meta_own != 0, Result() != 0))
    # post-conditions-end
    # impl-start
    # The options object stores its resolved builder; the constructor reads it
    # straight from there to drive field construction.
    stored = resolve_attr(meta_own, meta_inherited)
    return stored
    # impl-end


def factory_form_callback(
    passed: int, base_meta_own: int, base_meta_inherited: int
) -> int:
    # The builder selected for a form class produced by the run-time factory:
    #   `passed`            -- builder handed to the factory (0 == none given);
    #   base_meta_own/...   -- the base form's options-object builder, which the
    #                          produced options object inherits.
    # pre-conditions-start
    Requires(passed >= 0)
    Requires(base_meta_own >= 0)
    Requires(base_meta_inherited >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The produced options object's own builder is the one passed to the
    # factory (when one was passed); otherwise it inherits the base options
    # object's resolved builder. The constructor then selects via the same
    # attribute-resolution rule -- so a builder reachable through the base
    # form's options is preserved when the factory is given none.
    Ensures(Result() == resolve_attr(passed, resolve_attr(base_meta_own, base_meta_inherited)))
    Ensures(Implies(passed != 0, Result() == passed))
    Ensures(
        Implies(
            passed == 0,
            Result() == resolve_attr(base_meta_own, base_meta_inherited),
        )
    )
    # When the factory is given no builder but the base options carry one, the
    # produced class still drives field construction with that builder.
    Ensures(Implies(passed == 0 and base_meta_own != 0, Result() == base_meta_own))
    Ensures(
        Implies(
            passed == 0 and base_meta_own == 0 and base_meta_inherited != 0,
            Result() == base_meta_inherited,
        )
    )
    # post-conditions-end
    # impl-start
    # The factory records the passed builder on the produced options object
    # only when one was given; it never injects an overriding "no builder".
    # The produced options object therefore resolves (passed shadows the
    # inherited base builder), and the constructor reads that resolved value.
    produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
    produced_own = passed  # 0 when nothing was passed -> inherited is seen
    stored = resolve_attr(produced_own, produced_inherited)
    return stored
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec: postconditions TOTALLY pin Result()==resolve_attr(...) over the entire Requires domain (own/inherited/passed >= 0) for BOTH declared_form_callback and factory_form_callback (declared: Ensures Result()==resolve_attr(meta_own,meta_inherited) plus own-shadows and never-lost clauses; factory: Ensures Result()==resolve_attr(passed, resolve_attr(base_own,base_inh)) plus per-branch clauses). No free/underspecified behaviour exists, so any verifying impl must compute exactly resolve_attr.

POSITIVE CONTROL: bash scripts/nagini_verify.sh positive_control.py -> Verification successful (10.0s), exit 0.

atk_1 (partial-domain: declared returns meta_own, drops inherited): weakness exit=2, verification failed. Spec rejected.
- atk_2 (prepatch-declared echo: declared returns meta_inherited): weakness exit=2, verification failed. Spec rejected. (== real prepatch declared bug; model_prepatch.py also rejected: nagini_verify exit 1.)
- atk_3 (prepatch-factory echo: factory returns passed): weakness exit=2, verification failed. Spec rejected. (== real prepatch factory bug; model_prepatch_2.py also rejected: nagini_verify exit 1.)
- atk_4 (boundary/off-by: declared uses meta_own>1 so own==1 wrongly falls through): weakness exit=2, verification failed. Spec rejected.
- atk_5 (control-flow-effect/ungrounded-oracle spike: declared returns 999 when meta_own==3): weakness exit=2, verification failed. Spec rejected.
- atk_6 (factory resolution-order swap: inherited shadows passed): weakness exit=2, verification failed. Spec rejected.
- atk_7 (equivalent inline restructure: both functions compute resolve_attr via inline if/else branches instead of calling the helper): weakness exit=0 -> CANDIDATE (shares spec AND verifies, 10.9s).

CANDIDATE RESOLVE (mandatory): atk_7 is behaviourally identical to gold (it inlines resolve_attr byte-for-byte: declared = own if own!=0 else inherited; factory = passed if passed!=0 elif base_own!=0 else base_inh). Its faithful refined patch is therefore the gold patch (patch.diff verbatim). RAN it through the official harness: swebench_unified.harness.run_resolve("django__django-15916", gold_patch, run_id sbu-audit-eq-15916-atk7-73afaort) -> RESOLVED=True, completed=True, attempts=1, flaky=False. FAIL_TO_PASS both pass (test_custom_callback_in_meta, test_custom_callback_from_base_form_meta); all ~150 PASS_TO_PASS pass; 0 failures. So the only verifying candidate's faithful patch DOES resolve -> no verify-not-correct gap.

REFINEMENT.MD AUDIT (A-legs + correspondence): axioms region empty -> NO consumed @ContractOnly axiom (matches refinement.md sec C). Legs A1/B1 = R (builder callable/None <-> int identity code 0=absent; Meta-attr-with-inheritance <-> (own,inherited) pair). A2, B2, B3, B4 = A-reference + I: resolve_attr is a DEEP model of CPython getattr(meta,'formfield_callback',None) over the Meta type MRO; validated == real Python resolution by G-AX. No kind-3 (unexpressible-changed-op) leg; the one genuinely changed operation (select builder via options-object attribute resolution rather than bases/attrs lookup) is modeled deeply, not hidden behind an axiom. Correspondence holds: the A-reference callee resolve_attr matches the real callees on both F2P scenarios + fuzz.

G-AX corroboration: benchmark-verified/.../axiom_check.py -> 'G-AX OK: resolve_attr deep model == real Python attribute resolution on the 2 FAIL_TO_PASS scenarios + 40002 fuzz resolutions; no consumed axiom', exit 0. Executes REAL type()/getattr/staticmethod resolution incl. further-subclass (InheritedForm) case. (G-CONF/conformance_check.py present, driving real Django metaclass+modelform_factory over an exhaustive 0..7 grid + 100k fuzz; consistent with the mapping.)

All 6 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, order-swap, both prepatch echoes) fail to verify; the sole verifying candidate resolves. Spec discriminates the real bug in both directions (both prepatch models rejected). No counterexample; verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15916.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a model-backed form class is constructed, the per-field builder that
  turns each model field into a form field is selected from the form's own
  options/configuration object. The selection follows ordinary attribute
  resolution on that options object:

    - if the options object declares its own builder, that builder is used;
    - otherwise the builder inherited from the options object's parent (the
      base form's options) is used;
    - otherwise no custom builder is used (the model's default applies).

  This rule holds uniformly for two construction paths:

    (1) a class declared directly with a model-backed options object that
        carries a builder; and
    (2) a class produced by the run-time factory from a base form whose
        options object carries a builder (with no builder passed to the
        factory) -- and likewise for any further subclass of that produced
        class.

  In every case the builder that ends up driving field construction is the one
  resolvable from the options object, never silently replaced by "no builder".

Identities (callbacks / builders, options objects) are modelled as small
integer codes: 0 denotes "absent / no builder"; any positive value denotes a
specific builder identity. An options object is modelled as a pair (own
builder, inherited builder) capturing attribute resolution through its parent.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: this behaviour is a pure attribute-resolution / data-flow change,
# modelled deeply over integer identity codes; no unchanged opaque callee is
# consumed inside a contract.)
# axioms-end


# pure-start
@Pure
def resolve_attr(own: int, inherited: int) -> int:
    """Ordinary attribute resolution on an options object: an attribute set
    directly on the object (own != 0) shadows the one inherited from its
    parent (inherited); when the object sets nothing of its own (own == 0) the
    inherited value is seen. 0 denotes "attribute absent" on either level."""
    if own != 0:
        return own
    return inherited
# pure-end


def declared_form_callback(meta_own: int, meta_inherited: int) -> int:
    # The builder selected for a form class declared directly from a
    # model-backed options object carrying (meta_own, meta_inherited).
    # pre-conditions-start
    Requires(meta_own >= 0)
    Requires(meta_inherited >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The selected builder is exactly the one resolvable from the options
    # object: own shadows inherited; absence of both yields "no builder".
    Ensures(Result() == resolve_attr(meta_own, meta_inherited))
    Ensures(Implies(meta_own != 0, Result() == meta_own))
    Ensures(Implies(meta_own == 0, Result() == meta_inherited))
    # A builder declared on the options object is never lost.
    Ensures(Implies(meta_own != 0, Result() != 0))
    # post-conditions-end
    # impl-start
    # The options object stores its resolved builder; the constructor reads it
    # straight from there to drive field construction.
    stored = resolve_attr(meta_own, meta_inherited)
    return stored
    # impl-end


def factory_form_callback(
    passed: int, base_meta_own: int, base_meta_inherited: int
) -> int:
    # The builder selected for a form class produced by the run-time factory:
    #   `passed`            -- builder handed to the factory (0 == none given);
    #   base_meta_own/...   -- the base form's options-object builder, which the
    #                          produced options object inherits.
    # pre-conditions-start
    Requires(passed >= 0)
    Requires(base_meta_own >= 0)
    Requires(base_meta_inherited >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The produced options object's own builder is the one passed to the
    # factory (when one was passed); otherwise it inherits the base options
    # object's resolved builder. The constructor then selects via the same
    # attribute-resolution rule -- so a builder reachable through the base
    # form's options is preserved when the factory is given none.
    Ensures(Result() == resolve_attr(passed, resolve_attr(base_meta_own, base_meta_inherited)))
    Ensures(Implies(passed != 0, Result() == passed))
    Ensures(
        Implies(
            passed == 0,
            Result() == resolve_attr(base_meta_own, base_meta_inherited),
        )
    )
    # When the factory is given no builder but the base options carry one, the
    # produced class still drives field construction with that builder.
    Ensures(Implies(passed == 0 and base_meta_own != 0, Result() == base_meta_own))
    Ensures(
        Implies(
            passed == 0 and base_meta_own == 0 and base_meta_inherited != 0,
            Result() == base_meta_inherited,
        )
    )
    # post-conditions-end
    # impl-start
    # The factory records the passed builder on the produced options object
    # only when one was given; it never injects an overriding "no builder".
    # The produced options object therefore resolves (passed shadows the
    # inherited base builder), and the constructor reads that resolved value.
    produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)
    produced_own = passed  # 0 when nothing was passed -> inherited is seen
    stored = resolve_attr(produced_own, produced_inherited)
    return stored
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec: postconditions TOTALLY pin Result()==resolve_attr(...) over the entire Requires domain (own/inherited/passed >= 0) for BOTH declared_form_callback and factory_form_callback (declared: Ensures Result()==resolve_attr(meta_own,meta_inherited) plus own-shadows and never-lost clauses; factory: Ensures Result()==resolve_attr(passed, resolve_attr(base_own,base_inh)) plus per-branch clauses). No free/underspecified behaviour exists, so any verifying impl must compute exactly resolve_attr.

POSITIVE CONTROL: bash scripts/nagini_verify.sh positive_control.py -> Verification successful (10.0s), exit 0.

atk_1 (partial-domain: declared returns meta_own, drops inherited): weakness exit=2, verification failed. Spec rejected.
- atk_2 (prepatch-declared echo: declared returns meta_inherited): weakness exit=2, verification failed. Spec rejected. (== real prepatch declared bug; model_prepatch.py also rejected: nagini_verify exit 1.)
- atk_3 (prepatch-factory echo: factory returns passed): weakness exit=2, verification failed. Spec rejected. (== real prepatch factory bug; model_prepatch_2.py also rejected: nagini_verify exit 1.)
- atk_4 (boundary/off-by: declared uses meta_own>1 so own==1 wrongly falls through): weakness exit=2, verification failed. Spec rejected.
- atk_5 (control-flow-effect/ungrounded-oracle spike: declared returns 999 when meta_own==3): weakness exit=2, verification failed. Spec rejected.
- atk_6 (factory resolution-order swap: inherited shadows passed): weakness exit=2, verification failed. Spec rejected.
- atk_7 (equivalent inline restructure: both functions compute resolve_attr via inline if/else branches instead of calling the helper): weakness exit=0 -> CANDIDATE (shares spec AND verifies, 10.9s).

CANDIDATE RESOLVE (mandatory): atk_7 is behaviourally identical to gold (it inlines resolve_attr byte-for-byte: declared = own if own!=0 else inherited; factory = passed if passed!=0 elif base_own!=0 else base_inh). Its faithful refined patch is therefore the gold patch (patch.diff verbatim). RAN it through the official harness: swebench_unified.harness.run_resolve("django__django-15916", gold_patch, run_id sbu-audit-eq-15916-atk7-73afaort) -> RESOLVED=True, completed=True, attempts=1, flaky=False. FAIL_TO_PASS both pass (test_custom_callback_in_meta, test_custom_callback_from_base_form_meta); all ~150 PASS_TO_PASS pass; 0 failures. So the only verifying candidate's faithful patch DOES resolve -> no verify-not-correct gap.

REFINEMENT.MD AUDIT (A-legs + correspondence): axioms region empty -> NO consumed @ContractOnly axiom (matches refinement.md sec C). Legs A1/B1 = R (builder callable/None <-> int identity code 0=absent; Meta-attr-with-inheritance <-> (own,inherited) pair). A2, B2, B3, B4 = A-reference + I: resolve_attr is a DEEP model of CPython getattr(meta,'formfield_callback',None) over the Meta type MRO; validated == real Python resolution by G-AX. No kind-3 (unexpressible-changed-op) leg; the one genuinely changed operation (select builder via options-object attribute resolution rather than bases/attrs lookup) is modeled deeply, not hidden behind an axiom. Correspondence holds: the A-reference callee resolve_attr matches the real callees on both F2P scenarios + fuzz.

G-AX corroboration: benchmark-verified/.../axiom_check.py -> 'G-AX OK: resolve_attr deep model == real Python attribute resolution on the 2 FAIL_TO_PASS scenarios + 40002 fuzz resolutions; no consumed axiom', exit 0. Executes REAL type()/getattr/staticmethod resolution incl. further-subclass (InheritedForm) case. (G-CONF/conformance_check.py present, driving real Django metaclass+modelform_factory over an exhaustive 0..7 grid + 100k fuzz; consistent with the mapping.)

All 6 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, order-swap, both prepatch echoes) fail to verify; the sole verifying candidate resolves. Spec discriminates the real bug in both directions (both prepatch models rejected). No counterexample; verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-15916 nagini bundle. The spec models two changed-behaviour functions over an integer abstraction of formfield_callback identity (0=absent, positive=distinct builder): declared_form_callback = resolve_attr(meta_own, meta_inherited) and factory_form_callback = resolve_attr(passed, resolve_attr(base_meta_own, base_meta_inherited)), where resolve_attr(own,inh)=own if own!=0 else inh.

Checks run:
1. same-spec on the bundle's own model.py -> exit 0 (spec region byte-identical, sanity baseline).
2. axiom_check.py (G-AX) -> pass: deep model == an independent re-implementation of Python getattr/MRO/staticmethod resolution over 40002 configs, 0 mismatch.
3. DIRECT comparison against the REAL patched Django worktree at base_commit 88e67a54 (gold applied): built real ModelForm/modelform_factory scenarios and read NewForm._meta.formfield_callback -- the exact value the metaclass at :311 feeds to fields_for_model, i.e. the observable the F2P tests pin (widget type). Compared to the modeled functions across the full abstract domain (absent + 3 distinct builder identities at each of own/inherited/passed/base levels):
   - declared path: 3000 randomized configs -> 0 mismatch
   - factory path: 3000 randomized configs -> 0 mismatch
   - factory-produced subclass (InheritedForm, F2P #2): 2000 configs -> 0 mismatch

The abstraction is sound: staticmethod is identity on which callable is selected; Meta-MRO attribute resolution is exactly own-shadows-inherited-else-absent; the per-field fold collapses to the single selected builder identity. The postconditions (Result()==resolve_attr(...), own!=0 => Result()==own, etc.) hold on the real callee for every tested input and are neither too strong (no verifying-but-diverging input found) nor drifting from real repo behaviour. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: spec view of model.py (via markers.spec_view), judged against public problem_statement only (not hints_text). Mechanical G-LEAK screen passes (no diff markers, no gold-patch line reproduced, no patched file path, no spec-view identifier/comment echoing a patched repo symbol). Manual leakage review of the spec view confirms NO-LEAKAGE:

1. Fully abstracted vocabulary: the spec view says 'builder' (never `formfield_callback`), 'options/configuration object' (never `ModelFormOptions`/`Meta`), 'run-time factory' (never `modelform_factory` verbatim), 'attribute resolution' (never `getattr`/MRO). Patched symbols (`ModelFormOptions`, `ModelFormMetaclass`, `fields_for_model`, `formfield_callback`, changed file `django/forms/models.py`) appear nowhere in the view — only in refinement.md/mapping.md, which are AUDITOR artifacts, not the consumer spec view.

2. The specified behavior is a higher-altitude restatement of what problem_statement ALREADY discloses publicly: that Meta.formfield_callback should be used, that modelform_factory should honor the base form's callback rather than overwriting it 'with the default argument None'. The spec view's rule (own shadows inherited; factory preserves base builder when given none; never silently replaced by no-builder) reveals LESS concrete implementation than the problem statement's own code example.

3. The only spec detail not literally in the problem statement — 'any further subclass of that produced class' — is a test-scenario elaboration (consistent with 'other Meta options'), not a localization of the edit; the gold patch adds no subclass-specific code.

No spec-view line discloses the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
