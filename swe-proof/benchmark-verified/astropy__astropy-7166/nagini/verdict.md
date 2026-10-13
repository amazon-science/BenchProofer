# P2 adversarial audit — astropy__astropy-7166

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
                  doc: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
@@ -100,15 +98,6 @@
              and Acc(m.is_computed_attribute, 1 / 2)
              and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
              and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
-    # Termination obligation. This method owns no loop, so the level only has to
-    # leave room beneath the caller for the obligated callees it may reach:
-    # Member.__init__ (level 2). The level is heap-dependent rather than a bare
-    # constant because a self-call needs the caller's level to be STRICTLY
-    # greater than the callee's, which no constant can satisfy against itself.
-    # A member already reported as a computed attribute sits at 3; any other
-    # member sits at 4, so a call whose argument is a computed-attribute member
-    # (as the F2P discriminator is) strictly decreases 4 -> 3 and terminates.
-    Requires(MustTerminate(3 if m.is_computed_attribute else 4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(m.is_callable_member, 1 / 2)
@@ -135,7 +124,6 @@
                     m.doc == Old(m.doc)))
     # post-conditions-end
     # impl-start
-    if ((m.is_callable_member or m.is_computed_attribute)
-            and m.is_public and not m.has_own_doc):
+    if m.is_callable_member and m.is_public and not m.has_own_doc:
         m.doc = m.inherited_doc
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
                  doc: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
@@ -100,15 +98,6 @@
              and Acc(m.is_computed_attribute, 1 / 2)
              and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
              and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
-    # Termination obligation. This method owns no loop, so the level only has to
-    # leave room beneath the caller for the obligated callees it may reach:
-    # Member.__init__ (level 2). The level is heap-dependent rather than a bare
-    # constant because a self-call needs the caller's level to be STRICTLY
-    # greater than the callee's, which no constant can satisfy against itself.
-    # A member already reported as a computed attribute sits at 3; any other
-    # member sits at 4, so a call whose argument is a computed-attribute member
-    # (as the F2P discriminator is) strictly decreases 4 -> 3 and terminates.
-    Requires(MustTerminate(3 if m.is_computed_attribute else 4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(m.is_callable_member, 1 / 2)
@@ -135,7 +124,6 @@
                     m.doc == Old(m.doc)))
     # post-conditions-end
     # impl-start
-    if ((m.is_callable_member or m.is_computed_attribute)
-            and m.is_public and not m.has_own_doc):
+    if m.is_computed_attribute and m.is_public and not m.has_own_doc:
         m.doc = m.inherited_doc
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
                  doc: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
@@ -100,15 +98,6 @@
              and Acc(m.is_computed_attribute, 1 / 2)
              and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
              and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
-    # Termination obligation. This method owns no loop, so the level only has to
-    # leave room beneath the caller for the obligated callees it may reach:
-    # Member.__init__ (level 2). The level is heap-dependent rather than a bare
-    # constant because a self-call needs the caller's level to be STRICTLY
-    # greater than the callee's, which no constant can satisfy against itself.
-    # A member already reported as a computed attribute sits at 3; any other
-    # member sits at 4, so a call whose argument is a computed-attribute member
-    # (as the F2P discriminator is) strictly decreases 4 -> 3 and terminates.
-    Requires(MustTerminate(3 if m.is_computed_attribute else 4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(m.is_callable_member, 1 / 2)
@@ -135,7 +124,7 @@
                     m.doc == Old(m.doc)))
     # post-conditions-end
     # impl-start
-    if ((m.is_callable_member or m.is_computed_attribute)
+    if ((m.is_callable_member and m.is_computed_attribute)
             and m.is_public and not m.has_own_doc):
         m.doc = m.inherited_doc
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
                  doc: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
@@ -100,15 +98,6 @@
              and Acc(m.is_computed_attribute, 1 / 2)
              and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
              and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
-    # Termination obligation. This method owns no loop, so the level only has to
-    # leave room beneath the caller for the obligated callees it may reach:
-    # Member.__init__ (level 2). The level is heap-dependent rather than a bare
-    # constant because a self-call needs the caller's level to be STRICTLY
-    # greater than the callee's, which no constant can satisfy against itself.
-    # A member already reported as a computed attribute sits at 3; any other
-    # member sits at 4, so a call whose argument is a computed-attribute member
-    # (as the F2P discriminator is) strictly decreases 4 -> 3 and terminates.
-    Requires(MustTerminate(3 if m.is_computed_attribute else 4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(m.is_callable_member, 1 / 2)
@@ -135,7 +124,5 @@
                     m.doc == Old(m.doc)))
     # post-conditions-end
     # impl-start
-    if ((m.is_callable_member or m.is_computed_attribute)
-            and m.is_public and not m.has_own_doc):
-        m.doc = m.inherited_doc
+    m.doc = m.inherited_doc
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
                  doc: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
@@ -100,15 +98,6 @@
              and Acc(m.is_computed_attribute, 1 / 2)
              and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
              and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
-    # Termination obligation. This method owns no loop, so the level only has to
-    # leave room beneath the caller for the obligated callees it may reach:
-    # Member.__init__ (level 2). The level is heap-dependent rather than a bare
-    # constant because a self-call needs the caller's level to be STRICTLY
-    # greater than the callee's, which no constant can satisfy against itself.
-    # A member already reported as a computed attribute sits at 3; any other
-    # member sits at 4, so a call whose argument is a computed-attribute member
-    # (as the F2P discriminator is) strictly decreases 4 -> 3 and terminates.
-    Requires(MustTerminate(3 if m.is_computed_attribute else 4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(m.is_callable_member, 1 / 2)
@@ -135,7 +124,6 @@
                     m.doc == Old(m.doc)))
     # post-conditions-end
     # impl-start
-    if ((m.is_callable_member or m.is_computed_attribute)
-            and m.is_public and not m.has_own_doc):
+    if False:
         m.doc = m.inherited_doc
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
                  doc: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
@@ -100,15 +98,6 @@
              and Acc(m.is_computed_attribute, 1 / 2)
              and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
              and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
-    # Termination obligation. This method owns no loop, so the level only has to
-    # leave room beneath the caller for the obligated callees it may reach:
-    # Member.__init__ (level 2). The level is heap-dependent rather than a bare
-    # constant because a self-call needs the caller's level to be STRICTLY
-    # greater than the callee's, which no constant can satisfy against itself.
-    # A member already reported as a computed attribute sits at 3; any other
-    # member sits at 4, so a call whose argument is a computed-attribute member
-    # (as the F2P discriminator is) strictly decreases 4 -> 3 and terminates.
-    Requires(MustTerminate(3 if m.is_computed_attribute else 4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(m.is_callable_member, 1 / 2)
@@ -137,5 +126,5 @@
     # impl-start
     if ((m.is_callable_member or m.is_computed_attribute)
             and m.is_public and not m.has_own_doc):
-        m.doc = m.inherited_doc
+        m.doc = 0
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
                  doc: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
@@ -100,15 +98,6 @@
              and Acc(m.is_computed_attribute, 1 / 2)
              and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
              and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
-    # Termination obligation. This method owns no loop, so the level only has to
-    # leave room beneath the caller for the obligated callees it may reach:
-    # Member.__init__ (level 2). The level is heap-dependent rather than a bare
-    # constant because a self-call needs the caller's level to be STRICTLY
-    # greater than the callee's, which no constant can satisfy against itself.
-    # A member already reported as a computed attribute sits at 3; any other
-    # member sits at 4, so a call whose argument is a computed-attribute member
-    # (as the F2P discriminator is) strictly decreases 4 -> 3 and terminates.
-    Requires(MustTerminate(3 if m.is_computed_attribute else 4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(m.is_callable_member, 1 / 2)
@@ -135,7 +124,6 @@
                     m.doc == Old(m.doc)))
     # post-conditions-end
     # impl-start
-    if ((m.is_callable_member or m.is_computed_attribute)
-            and m.is_public and not m.has_own_doc):
+    if (m.is_callable_member or m.is_computed_attribute) and not m.has_own_doc:
         m.doc = m.inherited_doc
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
                  doc: int) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
@@ -100,15 +98,6 @@
              and Acc(m.is_computed_attribute, 1 / 2)
              and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
              and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
-    # Termination obligation. This method owns no loop, so the level only has to
-    # leave room beneath the caller for the obligated callees it may reach:
-    # Member.__init__ (level 2). The level is heap-dependent rather than a bare
-    # constant because a self-call needs the caller's level to be STRICTLY
-    # greater than the callee's, which no constant can satisfy against itself.
-    # A member already reported as a computed attribute sits at 3; any other
-    # member sits at 4, so a call whose argument is a computed-attribute member
-    # (as the F2P discriminator is) strictly decreases 4 -> 3 and terminates.
-    Requires(MustTerminate(3 if m.is_computed_attribute else 4))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(m.is_callable_member, 1 / 2)
@@ -135,7 +124,7 @@
                     m.doc == Old(m.doc)))
     # post-conditions-end
     # impl-start
-    if ((m.is_callable_member or m.is_computed_attribute)
-            and m.is_public and not m.has_own_doc):
+    if not ((not m.is_callable_member and not m.is_computed_attribute)
+            or not m.is_public or m.has_own_doc):
         m.doc = m.inherited_doc
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for astropy__astropy-7166.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A class-construction helper fills in a missing docstring on a member of a
  newly-built class from the corresponding member resolved along the base
  classes. For one such member, the docstring is filled in EXACTLY when all
  three conditions hold:

    (1) the member is a kind whose docstring participates in this inheritance:
        either an ordinary callable member, OR a computed-attribute member
        (one exposed through the descriptor protocol, such as a managed
        attribute whose access runs code). BOTH kinds participate; the second
        is the behaviour pinned here.
    (2) the member is a public member of the class, and
    (3) the member does not already carry its own docstring.

  When all three hold the member's docstring becomes the docstring resolved
  from the base classes (the inherited docstring). When any one fails the
  member's docstring is left exactly as it was.

A member is modelled as a minimal object carrying the two kind predicates that
the standard introspection callees report for it (`is_callable_member`,
`is_computed_attribute`), whether it is public (`is_public`), whether it
already has its own docstring (`has_own_doc`), the docstring resolved from the
base classes (`inherited_doc`), and its current docstring (`doc`). A docstring
is modelled as an `int` identity (0 denotes "no docstring"); the discriminating
observable is *whether and to what* the docstring is assigned, not its
characters (Nagini bans `str` indexing).

The two kind predicates are the results of unchanged standard introspection
callees; their classification of the two member kinds (a computed-attribute
member is NOT reported callable but IS reported as a descriptor) is validated
against the real callees out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms are consumed: the introspection-callee results and
# the base-class docstring resolution are carried on the member as already-
# computed fields — type refinements of unchanged callees, validated against
# the real callees by axiom_check.py / G-AX. See refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def fills_docstring(is_callable_member: bool, is_computed_attribute: bool,
                    is_public: bool, has_own_doc: bool) -> bool:
    """The member participates in docstring inheritance and is eligible to be
    filled: it is a callable member OR a computed-attribute member, it is
    public, and it has no docstring of its own."""
    return ((is_callable_member or is_computed_attribute)
            and is_public and not has_own_doc)
# pure-end


class Member:
    """A member of a newly-built class: the two introspection predicates that
    classify its kind, whether it is public, whether it already has a docstring,
    the docstring resolved from the base classes, and its current docstring
    (`doc`; 0 denotes no docstring)."""

    def __init__(self, is_callable_member: bool, is_computed_attribute: bool,
                 is_public: bool, has_own_doc: bool, inherited_doc: int,
                 doc: int) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
                and Acc(self.is_public) and Acc(self.has_own_doc)
                and Acc(self.inherited_doc) and Acc(self.doc))
        Ensures(self.is_callable_member == is_callable_member)
        Ensures(self.is_computed_attribute == is_computed_attribute)
        Ensures(self.is_public == is_public)
        Ensures(self.has_own_doc == has_own_doc)
        Ensures(self.inherited_doc == inherited_doc)
        Ensures(self.doc == doc)
        # post-conditions-end
        # impl-start
        self.is_callable_member = is_callable_member      # type: bool
        self.is_computed_attribute = is_computed_attribute  # type: bool
        self.is_public = is_public                        # type: bool
        self.has_own_doc = has_own_doc                    # type: bool
        self.inherited_doc = inherited_doc                # type: int
        self.doc = doc                                    # type: int
        # impl-end


def apply_inheritance(m: Member) -> None:
    # pre-conditions-start
    Requires(Acc(m.is_callable_member, 1 / 2)
             and Acc(m.is_computed_attribute, 1 / 2)
             and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
             and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(m.is_callable_member, 1 / 2)
            and Acc(m.is_computed_attribute, 1 / 2)
            and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
            and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
    # The kind predicates, public flag, own-doc flag and resolved inherited
    # docstring are read-only: unchanged across the call.
    Ensures(m.is_callable_member == Old(m.is_callable_member))
    Ensures(m.is_computed_attribute == Old(m.is_computed_attribute))
    Ensures(m.is_public == Old(m.is_public))
    Ensures(m.has_own_doc == Old(m.has_own_doc))
    Ensures(m.inherited_doc == Old(m.inherited_doc))
    # When the member is eligible (callable OR computed-attribute, public, no
    # own docstring) its docstring becomes the one resolved from the bases.
    Ensures(Implies(fills_docstring(Old(m.is_callable_member),
                                    Old(m.is_computed_attribute),
                                    Old(m.is_public), Old(m.has_own_doc)),
                    m.doc == Old(m.inherited_doc)))
    # Otherwise the docstring is left exactly as it was.
    Ensures(Implies(not fills_docstring(Old(m.is_callable_member),
                                        Old(m.is_computed_attribute),
                                        Old(m.is_public), Old(m.has_own_doc)),
                    m.doc == Old(m.doc)))
    # post-conditions-end
    # impl-start
    if ((m.is_callable_member or m.is_computed_attribute)
            and m.is_public and not m.has_own_doc):
        m.doc = m.inherited_doc
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND (verify DOES imply correct for this bundle). verifier env swebench-nagini-verifier; harness env swebench-lean.

SPEC ANALYSIS: apply_inheritance's postcondition fully pins the observable m.doc: (i) fills_docstring(...) => m.doc==Old(inherited_doc); (ii) not fills_docstring(...) => m.doc==Old(doc); plus frame conditions holding all five kind/public/own-doc/inherited fields == Old. fills_docstring = (is_callable_member or is_computed_attribute) and is_public and not has_own_doc — the exact post-patch disjunctive guard. This leaves NO behavioral slack: any same-spec verifying impl must set m.doc identically to gold on every input. So the spec should admit only behaviorally-gold impls.

### ATTACKS (all confirmed same-spec via `adversary same-spec`; verification run concurrently ≤3 JVMs via `adversary weakness`):
- atk_1 (prepatch, isfunction-only guard `m.is_callable_member and m.is_public and not m.has_own_doc`): same-spec, NOT-A-COUNTEREXAMPLE — does not verify (fails the eligible=>m.doc==inherited_doc postcondition on the property witness is_callable=False,is_computed=True). PREPATCH REPRODUCED.
- atk_2 (partial-domain, isdatadescriptor-only guard): same-spec, does not verify (fails on callable member is_callable=True,is_computed=False).
- atk_3 (boundary, AND instead of OR between the two kind predicates): same-spec, does not verify.
- atk_4 (control-flow-effect, unconditional `m.doc=m.inherited_doc`): same-spec, does not verify (violates the not-eligible => m.doc==Old(doc) frame).
- atk_5 (control-flow-effect, never fill / `if False`): same-spec, does not verify (violates eligible => m.doc==inherited_doc).
- atk_6 (ungrounded-oracle echo, fill with 0 not inherited_doc): same-spec, does not verify.
- atk_7 (partial-domain, drop public check): same-spec, does not verify (over-fills private members, violates not-eligible frame).
- atk_8 (De Morgan-EQUIVALENT correct guard `not((not is_callable and not is_computed) or not is_public or has_own_doc)`): same-spec, VERIFIES (15.5s) => CANDIDATE. Per protocol I materialized its faithful refined patch (patch_atk_8.diff — gold hunk with the guard rewritten to the De Morgan-equivalent 3-line form) and RAN it through the official harness: run_resolve completed=True, resolved=True (run_id sbu-audit-atk8-fixed). It RESOLVES, so it is NOT a weakness (a resolving equivalent impl is expected, per G-CONF/G-EQ echo policy). Positive control (unmodified model.py) VERIFIED (16.9s). Gold baseline patch.diff independently confirmed resolved=True (run_id sbu-audit-gold-base) — proving the harness/image are healthy.

RESOLVE PROVENANCE for atk_8 (not a gate result): multiple early resolve attempts returned completed=False from a `clean_images` ImageNotFound at harness startup, which is an image-store artifact and NOT a patch property -- correctly treated as inconclusive, never as 'did not resolve'. Gold resolving in the same window confirms the image was present throughout, which is what rules that reading out. One attempt failed with 'malformed patch at line 33' from a hunk line-count mismatch in my FIRST draft of patch_atk_8.diff (2-line guard vs gold's 9/9 counts); I corrected the diff to a 3-line equivalent form and it applied and resolved cleanly.

REFINEMENT.MD AUDIT: legs A1/A2/A4/A7 = R / A-reference (unchanged callee results carried as fields), A3/A6/A8 = I (identical concrete ops — A3 is the disjunctive `or` that IS the fix). No A-consumed leg and no @ContractOnly axiom (axioms region is an empty comment, model.py L42-47) => no dead axiom, no kind-3 (unexpressible-changed-op). The A-reference correspondence is validated by axiom_check.py (G-AX), which I RAN: exit 0 — real inspect.isfunction/isdatadescriptor classify property->(False,True), function->(True,False), plain->(False,False); is_public_member matches on dunder/public/private keys; and check_behaviour_equivalence re-derives the full patched guard with the REAL callees over member-kind x public x own-doc and matches fills_docstring exactly, spelling out the discriminating witness (public undocumented property filled under patched guard, not under isfunction-only). Model↔patch correspondence holds.

CONCLUSION: 7 distinct wrong impls (prepatch + partial-domain + boundary + 2 control-flow-effect + ungrounded-oracle echo + dropped-guard) are ALL rejected by the spec; the single verifying same-spec impl is behaviorally equivalent to gold and its faithful patch RESOLVES under the official harness; prepatch reproduced; positive control verifies; G-AX sound; refinement legs clean. verify => correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for astropy__astropy-7166.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A class-construction helper fills in a missing docstring on a member of a
  newly-built class from the corresponding member resolved along the base
  classes. For one such member, the docstring is filled in EXACTLY when all
  three conditions hold:

    (1) the member is a kind whose docstring participates in this inheritance:
        either an ordinary callable member, OR a computed-attribute member
        (one exposed through the descriptor protocol, such as a managed
        attribute whose access runs code). BOTH kinds participate; the second
        is the behaviour pinned here.
    (2) the member is a public member of the class, and
    (3) the member does not already carry its own docstring.

  When all three hold the member's docstring becomes the docstring resolved
  from the base classes (the inherited docstring). When any one fails the
  member's docstring is left exactly as it was.

A member is modelled as a minimal object carrying the two kind predicates that
the standard introspection callees report for it (`is_callable_member`,
`is_computed_attribute`), whether it is public (`is_public`), whether it
already has its own docstring (`has_own_doc`), the docstring resolved from the
base classes (`inherited_doc`), and its current docstring (`doc`). A docstring
is modelled as an `int` identity (0 denotes "no docstring"); the discriminating
observable is *whether and to what* the docstring is assigned, not its
characters (Nagini bans `str` indexing).

The two kind predicates are the results of unchanged standard introspection
callees; their classification of the two member kinds (a computed-attribute
member is NOT reported callable but IS reported as a descriptor) is validated
against the real callees out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms are consumed: the introspection-callee results and
# the base-class docstring resolution are carried on the member as already-
# computed fields — type refinements of unchanged callees, validated against
# the real callees by axiom_check.py / G-AX. See refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def fills_docstring(is_callable_member: bool, is_computed_attribute: bool,
                    is_public: bool, has_own_doc: bool) -> bool:
    """The member participates in docstring inheritance and is eligible to be
    filled: it is a callable member OR a computed-attribute member, it is
    public, and it has no docstring of its own."""
    return ((is_callable_member or is_computed_attribute)
            and is_public and not has_own_doc)
# pure-end


class Member:
    """A member of a newly-built class: the two introspection predicates that
    classify its kind, whether it is public, whether it already has a docstring,
    the docstring resolved from the base classes, and its current docstring
    (`doc`; 0 denotes no docstring)."""

    def __init__(self, is_callable_member: bool, is_computed_attribute: bool,
                 is_public: bool, has_own_doc: bool, inherited_doc: int,
                 doc: int) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
                and Acc(self.is_public) and Acc(self.has_own_doc)
                and Acc(self.inherited_doc) and Acc(self.doc))
        Ensures(self.is_callable_member == is_callable_member)
        Ensures(self.is_computed_attribute == is_computed_attribute)
        Ensures(self.is_public == is_public)
        Ensures(self.has_own_doc == has_own_doc)
        Ensures(self.inherited_doc == inherited_doc)
        Ensures(self.doc == doc)
        # post-conditions-end
        # impl-start
        self.is_callable_member = is_callable_member      # type: bool
        self.is_computed_attribute = is_computed_attribute  # type: bool
        self.is_public = is_public                        # type: bool
        self.has_own_doc = has_own_doc                    # type: bool
        self.inherited_doc = inherited_doc                # type: int
        self.doc = doc                                    # type: int
        # impl-end


def apply_inheritance(m: Member) -> None:
    # pre-conditions-start
    Requires(Acc(m.is_callable_member, 1 / 2)
             and Acc(m.is_computed_attribute, 1 / 2)
             and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
             and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(m.is_callable_member, 1 / 2)
            and Acc(m.is_computed_attribute, 1 / 2)
            and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
            and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
    # The kind predicates, public flag, own-doc flag and resolved inherited
    # docstring are read-only: unchanged across the call.
    Ensures(m.is_callable_member == Old(m.is_callable_member))
    Ensures(m.is_computed_attribute == Old(m.is_computed_attribute))
    Ensures(m.is_public == Old(m.is_public))
    Ensures(m.has_own_doc == Old(m.has_own_doc))
    Ensures(m.inherited_doc == Old(m.inherited_doc))
    # When the member is eligible (callable OR computed-attribute, public, no
    # own docstring) its docstring becomes the one resolved from the bases.
    Ensures(Implies(fills_docstring(Old(m.is_callable_member),
                                    Old(m.is_computed_attribute),
                                    Old(m.is_public), Old(m.has_own_doc)),
                    m.doc == Old(m.inherited_doc)))
    # Otherwise the docstring is left exactly as it was.
    Ensures(Implies(not fills_docstring(Old(m.is_callable_member),
                                        Old(m.is_computed_attribute),
                                        Old(m.is_public), Old(m.has_own_doc)),
                    m.doc == Old(m.doc)))
    # post-conditions-end
    # impl-start
    if ((m.is_callable_member or m.is_computed_attribute)
            and m.is_public and not m.has_own_doc):
        m.doc = m.inherited_doc
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND (verify DOES imply correct for this bundle). verifier env swebench-nagini-verifier; harness env swebench-lean.

SPEC ANALYSIS: apply_inheritance's postcondition fully pins the observable m.doc: (i) fills_docstring(...) => m.doc==Old(inherited_doc); (ii) not fills_docstring(...) => m.doc==Old(doc); plus frame conditions holding all five kind/public/own-doc/inherited fields == Old. fills_docstring = (is_callable_member or is_computed_attribute) and is_public and not has_own_doc — the exact post-patch disjunctive guard. This leaves NO behavioral slack: any same-spec verifying impl must set m.doc identically to gold on every input. So the spec should admit only behaviorally-gold impls.

### ATTACKS (all confirmed same-spec via `adversary same-spec`; verification run concurrently ≤3 JVMs via `adversary weakness`):
- atk_1 (prepatch, isfunction-only guard `m.is_callable_member and m.is_public and not m.has_own_doc`): same-spec, NOT-A-COUNTEREXAMPLE — does not verify (fails the eligible=>m.doc==inherited_doc postcondition on the property witness is_callable=False,is_computed=True). PREPATCH REPRODUCED.
- atk_2 (partial-domain, isdatadescriptor-only guard): same-spec, does not verify (fails on callable member is_callable=True,is_computed=False).
- atk_3 (boundary, AND instead of OR between the two kind predicates): same-spec, does not verify.
- atk_4 (control-flow-effect, unconditional `m.doc=m.inherited_doc`): same-spec, does not verify (violates the not-eligible => m.doc==Old(doc) frame).
- atk_5 (control-flow-effect, never fill / `if False`): same-spec, does not verify (violates eligible => m.doc==inherited_doc).
- atk_6 (ungrounded-oracle echo, fill with 0 not inherited_doc): same-spec, does not verify.
- atk_7 (partial-domain, drop public check): same-spec, does not verify (over-fills private members, violates not-eligible frame).
- atk_8 (De Morgan-EQUIVALENT correct guard `not((not is_callable and not is_computed) or not is_public or has_own_doc)`): same-spec, VERIFIES (15.5s) => CANDIDATE. Per protocol I materialized its faithful refined patch (patch_atk_8.diff — gold hunk with the guard rewritten to the De Morgan-equivalent 3-line form) and RAN it through the official harness: run_resolve completed=True, resolved=True (run_id sbu-audit-atk8-fixed). It RESOLVES, so it is NOT a weakness (a resolving equivalent impl is expected, per G-CONF/G-EQ echo policy). Positive control (unmodified model.py) VERIFIED (16.9s). Gold baseline patch.diff independently confirmed resolved=True (run_id sbu-audit-gold-base) — proving the harness/image are healthy.

RESOLVE PROVENANCE for atk_8 (not a gate result): multiple early resolve attempts returned completed=False from a `clean_images` ImageNotFound at harness startup, which is an image-store artifact and NOT a patch property -- correctly treated as inconclusive, never as 'did not resolve'. Gold resolving in the same window confirms the image was present throughout, which is what rules that reading out. One attempt failed with 'malformed patch at line 33' from a hunk line-count mismatch in my FIRST draft of patch_atk_8.diff (2-line guard vs gold's 9/9 counts); I corrected the diff to a 3-line equivalent form and it applied and resolved cleanly.

REFINEMENT.MD AUDIT: legs A1/A2/A4/A7 = R / A-reference (unchanged callee results carried as fields), A3/A6/A8 = I (identical concrete ops — A3 is the disjunctive `or` that IS the fix). No A-consumed leg and no @ContractOnly axiom (axioms region is an empty comment, model.py L42-47) => no dead axiom, no kind-3 (unexpressible-changed-op). The A-reference correspondence is validated by axiom_check.py (G-AX), which I RAN: exit 0 — real inspect.isfunction/isdatadescriptor classify property->(False,True), function->(True,False), plain->(False,False); is_public_member matches on dunder/public/private keys; and check_behaviour_equivalence re-derives the full patched guard with the REAL callees over member-kind x public x own-doc and matches fills_docstring exactly, spelling out the discriminating witness (public undocumented property filled under patched guard, not under isfunction-only). Model↔patch correspondence holds.

CONCLUSION: 7 distinct wrong impls (prepatch + partial-domain + boundary + 2 control-flow-effect + ungrounded-oracle echo + dropped-guard) are ALL rejected by the spec; the single verifying same-spec impl is behaviorally equivalent to gold and its faithful patch RESOLVES under the official harness; prepatch reproduced; positive control verifies; G-AX sound; refinement legs clean. verify => correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) audit for astropy__astropy-7166 nagini. Model VERIFIES (nagini_verify.sh: 'Verification successful', 14s). Spec region uses no @ContractOnly axioms; the two introspection predicate results and the resolved base docstring are carried as Member fields (R / A-reference), validated by axiom_check.py.

Base commit confirmed: /tmp worktree at 26d147868f shows the pre-patch guard `inspect.isfunction(val) and is_public_member(key) and val.__doc__ is None` and the exact `is_public_member` rule mapping.md/axiom_check.py claim. Gold change widens the guard to `(inspect.isfunction(val) or inspect.isdatadescriptor(val)) and is_public_member(key) and val.__doc__ is None`.

Model semantics: fills_docstring = (is_callable_member OR is_computed_attribute) AND is_public AND NOT has_own_doc; apply_inheritance sets m.doc = m.inherited_doc when eligible else leaves m.doc unchanged. This is exactly the patched loop body abstracted (the unchanged MRO getattr walk is carried as the given inherited_doc input).

Differential faithfulness test (the attack): applied the gold patch to a base_commit worktree and ran a self-contained harness comparing the modeled apply_inheritance against the REAL patched InheritDocstrings metaclass loop body over the full cross product: 9 member kinds (function, function_doc, lambda, property, property_doc, staticmethod, classmethod, custom data descriptor with __set__, plain data attr) x 7 keys (public/private/dunder/short-dunder boundary '____'/'_') x 4 base-chain shapes (none/base_doc/base_nodoc/grandparent). Result: 0 mismatches. The real inspect.isfunction/isdatadescriptor classify each kind exactly as the fields assume (property -> not function, is data descriptor; classmethod/staticmethod -> neither; custom __set__ descriptor -> data descriptor), and the eligibility+assignment observable matches the model everywhere.

(Note: conformance_check.py could not run against the old astropy in-tree here due to Python 3.11 collections.Mapping removal — that runs in the Docker testbed under G-CONF; my out-of-band replica of the exact patched callee is equivalent for the drift question.)

No input found where the modeled function disagrees with the real callee. The spec is not too strong and does not drift. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen over spec_view, nagini/python flavor) PASSES with zero hard failures and zero warnings: no diff markers, no gold-patch line reproduced (>=8 chars), no patched file path (astropy/utils/misc.py) or module path, no spec-view identifier or comment embedding a patched repo symbol, and no bug/fix narration.

Semantic assessment beyond the mechanical screen: the public problem_statement already discloses the full requirement — 'InheritDocstrings metaclass doesn't work for properties ... it uses inspect.isfunction which returns False for properties.' This publicly names the feature (docstring inheritance), the failing case (properties), and the root cause (isfunction excludes properties). The spec view only states, in abstract terms, that a docstring is filled when a member is 'an ordinary callable member OR a computed-attribute member (one exposed through the descriptor protocol...)', is public, and lacks its own docstring — i.e. that properties/descriptors participate, which is exactly the publicly-known requirement, not the private edit.

The spec view never names the gold edit's mechanism: it does not mention `inspect`, `isfunction`, `isdatadescriptor`, `InheritDocstrings`, the file `astropy/utils/misc.py`, nor reproduces the disjunctive guard line. It uses only abstraction-level vocabulary ('class-construction helper', 'standard introspection callees', 'descriptor protocol'). The specific added callee `inspect.isdatadescriptor` and the diff's structure are not revealed.

The repo symbols/file path DO appear in mapping.md and refinement.md, but those are audit-only artifacts (G-AX/refinement audit), not the consumer spec view that G-PANEL-3 / G-LEAK judges. Specifying correct behaviour (that properties should inherit docstrings) is mandatory for a faithful spec and is fully within the public problem_statement, so it does not constitute leakage of the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
