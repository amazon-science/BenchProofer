# P2 adversarial audit — sphinx-doc__sphinx-7910

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_const_none.py`, `atk_ignore_doc.py`, `atk_overinclude.py`, `atk_cat_swap.py`, `atk_return_true.py`, `atk_flip.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo.py`, `atk_canon_field.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -149,17 +149,9 @@
     member = obj.is_class_member
     if not doc:
         return None
-    # Resolve the owning class through the ORIGINAL (unwrapped) object's
-    # namespace -- the namespace that genuinely knows the class.
-    canon = canonical(obj)
-    Assert(canon.cls_name == obj.cls_name)
-    Assert(canon.is_class_member == member)
-    cls_is_owner = False
-    if obj.cls_name in canon.ns:
-        cls_is_owner = canon.ns[obj.cls_name]
-    # The unwrapped namespace lookup recovers the ground-truth ownership.
-    Assert(cls_is_owner == member)
-    if cls_is_owner:
+    # Ungrounded echo: consult the ground-truth membership field directly,
+    # never resolving ownership through the (unwrapped) namespace.
+    if member:
         if ((is_special and inc_special) or
                 (is_init and inc_init) or
                 (is_private and inc_private)):
```

Attack 2 — `atk_canon_field.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -146,20 +146,11 @@
     # post-conditions-end
     # impl-start
     doc = obj.has_doc
-    member = obj.is_class_member
     if not doc:
         return None
-    # Resolve the owning class through the ORIGINAL (unwrapped) object's
-    # namespace -- the namespace that genuinely knows the class.
     canon = canonical(obj)
-    Assert(canon.cls_name == obj.cls_name)
-    Assert(canon.is_class_member == member)
-    cls_is_owner = False
-    if obj.cls_name in canon.ns:
-        cls_is_owner = canon.ns[obj.cls_name]
-    # The unwrapped namespace lookup recovers the ground-truth ownership.
-    Assert(cls_is_owner == member)
-    if cls_is_owner:
+    member = canon.is_class_member
+    if member:
         if ((is_special and inc_special) or
                 (is_init and inc_init) or
                 (is_private and inc_private)):
```

Attack 3 — `atk_const_none.py` → rejected (same spec, does not verify — good)

```diff
@@ -145,24 +145,5 @@
               (is_private and inc_private))))
     # post-conditions-end
     # impl-start
-    doc = obj.has_doc
-    member = obj.is_class_member
-    if not doc:
-        return None
-    # Resolve the owning class through the ORIGINAL (unwrapped) object's
-    # namespace -- the namespace that genuinely knows the class.
-    canon = canonical(obj)
-    Assert(canon.cls_name == obj.cls_name)
-    Assert(canon.is_class_member == member)
-    cls_is_owner = False
-    if obj.cls_name in canon.ns:
-        cls_is_owner = canon.ns[obj.cls_name]
-    # The unwrapped namespace lookup recovers the ground-truth ownership.
-    Assert(cls_is_owner == member)
-    if cls_is_owner:
-        if ((is_special and inc_special) or
-                (is_init and inc_init) or
-                (is_private and inc_private)):
-            return False
     return None
     # impl-end
```

Attack 4 — `atk_ignore_doc.py` → rejected (same spec, does not verify — good)

```diff
@@ -145,21 +145,8 @@
               (is_private and inc_private))))
     # post-conditions-end
     # impl-start
-    doc = obj.has_doc
     member = obj.is_class_member
-    if not doc:
-        return None
-    # Resolve the owning class through the ORIGINAL (unwrapped) object's
-    # namespace -- the namespace that genuinely knows the class.
-    canon = canonical(obj)
-    Assert(canon.cls_name == obj.cls_name)
-    Assert(canon.is_class_member == member)
-    cls_is_owner = False
-    if obj.cls_name in canon.ns:
-        cls_is_owner = canon.ns[obj.cls_name]
-    # The unwrapped namespace lookup recovers the ground-truth ownership.
-    Assert(cls_is_owner == member)
-    if cls_is_owner:
+    if member:
         if ((is_special and inc_special) or
                 (is_init and inc_init) or
                 (is_private and inc_private)):
```

Attack 5 — `atk_overinclude.py` → rejected (same spec, does not verify — good)

```diff
@@ -149,20 +149,7 @@
     member = obj.is_class_member
     if not doc:
         return None
-    # Resolve the owning class through the ORIGINAL (unwrapped) object's
-    # namespace -- the namespace that genuinely knows the class.
-    canon = canonical(obj)
-    Assert(canon.cls_name == obj.cls_name)
-    Assert(canon.is_class_member == member)
-    cls_is_owner = False
-    if obj.cls_name in canon.ns:
-        cls_is_owner = canon.ns[obj.cls_name]
-    # The unwrapped namespace lookup recovers the ground-truth ownership.
-    Assert(cls_is_owner == member)
-    if cls_is_owner:
-        if ((is_special and inc_special) or
-                (is_init and inc_init) or
-                (is_private and inc_private)):
-            return False
+    if member:
+        return False
     return None
     # impl-end
```

Attack 6 — `atk_cat_swap.py` → rejected (same spec, does not verify — good)

```diff
@@ -149,19 +149,13 @@
     member = obj.is_class_member
     if not doc:
         return None
-    # Resolve the owning class through the ORIGINAL (unwrapped) object's
-    # namespace -- the namespace that genuinely knows the class.
     canon = canonical(obj)
-    Assert(canon.cls_name == obj.cls_name)
-    Assert(canon.is_class_member == member)
     cls_is_owner = False
     if obj.cls_name in canon.ns:
         cls_is_owner = canon.ns[obj.cls_name]
-    # The unwrapped namespace lookup recovers the ground-truth ownership.
-    Assert(cls_is_owner == member)
     if cls_is_owner:
-        if ((is_special and inc_special) or
-                (is_init and inc_init) or
+        if ((is_special and inc_init) or
+                (is_init and inc_special) or
                 (is_private and inc_private)):
             return False
     return None
```

Attack 7 — `atk_return_true.py` → rejected (same spec, does not verify — good)

```diff
@@ -149,20 +149,10 @@
     member = obj.is_class_member
     if not doc:
         return None
-    # Resolve the owning class through the ORIGINAL (unwrapped) object's
-    # namespace -- the namespace that genuinely knows the class.
-    canon = canonical(obj)
-    Assert(canon.cls_name == obj.cls_name)
-    Assert(canon.is_class_member == member)
-    cls_is_owner = False
-    if obj.cls_name in canon.ns:
-        cls_is_owner = canon.ns[obj.cls_name]
-    # The unwrapped namespace lookup recovers the ground-truth ownership.
-    Assert(cls_is_owner == member)
-    if cls_is_owner:
+    if member:
         if ((is_special and inc_special) or
                 (is_init and inc_init) or
                 (is_private and inc_private)):
-            return False
+            return True
     return None
     # impl-end
```

Attack 8 — `atk_flip.py` → rejected (same spec, does not verify — good)

```diff
@@ -149,17 +149,7 @@
     member = obj.is_class_member
     if not doc:
         return None
-    # Resolve the owning class through the ORIGINAL (unwrapped) object's
-    # namespace -- the namespace that genuinely knows the class.
-    canon = canonical(obj)
-    Assert(canon.cls_name == obj.cls_name)
-    Assert(canon.is_class_member == member)
-    cls_is_owner = False
-    if obj.cls_name in canon.ns:
-        cls_is_owner = canon.ns[obj.cls_name]
-    # The unwrapped namespace lookup recovers the ground-truth ownership.
-    Assert(cls_is_owner == member)
-    if cls_is_owner:
+    if not member:
         if ((is_special and inc_special) or
                 (is_init and inc_init) or
                 (is_private and inc_private)):
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7910.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documentation-tooling hook decides, for a documented special/init/private
  member of a class, whether that member should be INCLUDED in the generated
  documentation. The decision depends on whether the member's owning class can
  be recovered as the genuine owner of the member: the hook resolves the class
  by name through the member object's surrounding global namespace, then
  confirms the member is actually defined on that class.

  The member object handed to the hook may be a callable that has been WRAPPED
  by a decorator (the wrapper carries the original member's documentation and
  qualified name, but its surrounding global namespace is the decorator's, not
  the one in which the owning class is defined). The owning class must therefore
  be resolved through the ORIGINAL (unwrapped) member object's global namespace
  -- the namespace in which the member, and hence its class, is genuinely
  defined -- never through the wrapper's. Concretely:

    * the owning class is looked up by its name token in the global namespace of
      the canonical (unwrapped) member object, and the member is the class's own
      member iff that lookup both resolves the class AND records the member name
      among the class's own members;
    * a documented special/init/private member that IS its class's own member,
      and whose corresponding inclusion setting is enabled, is INCLUDED
      (Result() is False -- "do not skip"); otherwise the hook abstains
      (Result() is None) and leaves the default decision untouched.

  The behavioural consequence that matters: wrapping a member with a
  documentation-preserving decorator does not hide it from the docs, because the
  ownership lookup follows the unwrapped object's namespace, which still knows
  the class.

Modelling choices (Nagini fragment):
  * The member name and the owning class-name token are opaque ``int``
    identities; the tested behaviour only observes whether the ownership lookup
    succeeds, so integer identity is the faithful carrier (mapping.md s2).
  * The member object is a minimal class exposing only the touched fields: the
    ``has_doc`` flag, the ground-truth ``is_class_member`` flag, the owning
    class-name token ``cls_name`` (from the qualified name) and the surrounding
    global namespace ``ns`` (``Dict[int, bool]`` keyed by a class-name token; a
    present key records, for the class resolved at that name, whether the member
    is among the class's OWN members -- the repository's
    ``cls_path in globals and name in cls.__dict__`` collapsed into the single
    ``cls_is_owner`` outcome). For a decorated object this ``ns`` is the
    wrapper's and need not contain ``cls_name`` at all.
  * ``canonical`` is the unchanged library primitive that recovers the original
    member object from a wrapper (the identity on an un-wrapped object). It is
    axiomatized (A-consumed) and checked against the real callee out-of-band by
    axiom_check.py (G-AX). It is the WEAKEST contract the proof needs.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Optional, Dict
from nagini_contracts.contracts import *


class MemberObj:
    """Minimal view of the member object handed to the hook. ``ns`` maps a
    class-name token to whether the class resolved there owns this member."""

    def __init__(self, has_doc: bool, is_class_member: bool, cls_name: int,
                 ns: Dict[int, bool]) -> None:
        Requires(Acc(dict_pred(ns), 1 / 2))
        Ensures(Acc(self.has_doc) and self.has_doc == has_doc)        # type: ignore
        Ensures(Acc(self.is_class_member) and self.is_class_member == is_class_member)  # type: ignore
        Ensures(Acc(self.cls_name) and self.cls_name == cls_name)     # type: ignore
        Ensures(Acc(self.ns) and self.ns is ns)                       # type: ignore
        Ensures(Acc(dict_pred(ns), 1 / 2))
        self.has_doc = has_doc
        self.is_class_member = is_class_member
        self.cls_name = cls_name
        self.ns = ns


# axioms-start
@ContractOnly
def canonical(obj: MemberObj) -> MemberObj:
    """The unchanged library primitive that recovers the ORIGINAL member object
    from a (possibly decorator-wrapped) one, following the documentation-
    preserving wrapper chain to its end; the identity on an object that is not
    wrapped. The recovered object carries the SAME inclusion-relevant identity
    (has_doc / membership / class name) and exposes the global namespace in
    which the member -- and therefore its owning class -- is genuinely defined,
    so that resolving the class there agrees with the ground-truth membership.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    WEAKEST contract the proof needs.
    """
    Requires(Acc(obj.has_doc, 1 / 4) and Acc(obj.is_class_member, 1 / 4))
    Requires(Acc(obj.cls_name, 1 / 4))
    Ensures(Acc(obj.has_doc, 1 / 4) and Acc(obj.is_class_member, 1 / 4))
    Ensures(Acc(obj.cls_name, 1 / 4))
    Ensures(Result() is not None)
    Ensures(Acc(Result().has_doc, 1 / 2) and Acc(Result().is_class_member, 1 / 2))
    Ensures(Acc(Result().cls_name, 1 / 2))
    Ensures(Acc(Result().ns) and Acc(dict_pred(Result().ns)))
    Ensures(Result().has_doc == obj.has_doc)
    Ensures(Result().cls_name == obj.cls_name)
    Ensures(Result().is_class_member == obj.is_class_member)
    # The recovered object's namespace genuinely records ownership: the owning
    # class is resolvable there and owns the member EXACTLY when the member is a
    # genuine class member. (The wrapper's namespace need not -- that is the
    # whole point of recovering the original.)
    Ensures(obj.is_class_member ==
            (obj.cls_name in Result().ns and Result().ns[obj.cls_name]))
# axioms-end


# pure-start
# No pure helpers required.
# pure-end


def skip_decision(obj: MemberObj, is_special: bool, is_init: bool,
                  is_private: bool, inc_special: bool, inc_init: bool,
                  inc_private: bool) -> Optional[bool]:
    # pre-conditions-start
    # `obj` is read-only -- fractional permission on every touched field and on
    # its namespace (directive 5).
    Requires(Acc(obj.has_doc, 1 / 2) and Acc(obj.is_class_member, 1 / 2))
    Requires(Acc(obj.cls_name, 1 / 2) and Acc(obj.ns, 1 / 2))
    Requires(Acc(dict_pred(obj.ns), 1 / 4))
    # Exactly one inclusion category applies to a member (init / special /
    # private are mutually exclusive in the repository's classification).
    Requires(Implies(is_init, not is_special and not is_private))
    Requires(Implies(is_special, not is_init and not is_private))
    Requires(Implies(is_private, not is_init and not is_special))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(obj.has_doc, 1 / 2) and Acc(obj.is_class_member, 1 / 2))
    Ensures(Acc(obj.cls_name, 1 / 2) and Acc(obj.ns, 1 / 2))
    Ensures(Acc(dict_pred(obj.ns), 1 / 4))
    # The result is grounded in the TRUE ownership (recovered through the
    # unwrapped namespace), never in whether the wrapper's namespace happens to
    # contain the class:
    #   * a documented, genuinely-owned member whose category is enabled is
    #     INCLUDED -- Result() is False (do not skip);
    #   * any other case abstains -- Result() is None.
    Ensures(Result() is False or Result() is None)
    Ensures((Result() is False) ==
            (obj.has_doc and obj.is_class_member and
             ((is_special and inc_special) or
              (is_init and inc_init) or
              (is_private and inc_private))))
    # post-conditions-end
    # impl-start
    doc = obj.has_doc
    member = obj.is_class_member
    if not doc:
        return None
    # Resolve the owning class through the ORIGINAL (unwrapped) object's
    # namespace -- the namespace that genuinely knows the class.
    canon = canonical(obj)
    Assert(canon.cls_name == obj.cls_name)
    Assert(canon.is_class_member == member)
    cls_is_owner = False
    if obj.cls_name in canon.ns:
        cls_is_owner = canon.ns[obj.cls_name]
    # The unwrapped namespace lookup recovers the ground-truth ownership.
    Assert(cls_is_owner == member)
    if cls_is_owner:
        if ((is_special and inc_special) or
                (is_init and inc_init) or
                (is_private and inc_private)):
            return False
    return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Project root here; adversary/verify run via python with SBU_BENCHMARK_DIR=benchmark-verified and concurrent runs.

Positive control: cp of bundle model.py -> `bash scripts/nagini_verify.sh positive_control.py` => Verification successful (18.2s), exit 0.

Prepatch reproduced: atk_prepatch.py (=model_prepatch.py, single edit canon.ns->obj.ns) => same-spec exit 0; nagini_verify exit 1: 'Postcondition of skip_decision might not hold. Assertion ((Result() is False) == (obj.has_doc and obj.is_class_member and ...))' — the spec senses the changed __globals__ source (G-DIFF). prepatch_reproduced=true.

atk_echo (ungrounded-oracle echo: reads obj.is_class_member directly, ignoring canonical/ns): CANDIDATE (shares spec AND verifies, 20.6s, exit 0).
- atk_canon_field (reads canonical(obj).is_class_member directly): CANDIDATE (verifies, 22.0s, exit 0).
- atk_const_none (constant None / partial-domain): NOT-A-COUNTEREXAMPLE (does not verify — fails postcond).
- atk_ignore_doc (drops has_doc guard): NOT-A-COUNTEREXAMPLE (does not verify).
- atk_overinclude (control-flow-effect: return False before category check): NOT-A-COUNTEREXAMPLE (does not verify).
- atk_cat_swap (boundary: inc_init/inc_special swapped): NOT-A-COUNTEREXAMPLE (does not verify).
- atk_return_true (wrong codomain: return True): NOT-A-COUNTEREXAMPLE (does not verify).
- atk_flip (include when NOT owned): NOT-A-COUNTEREXAMPLE (does not verify).

Materialized+resolved every CANDIDATE. Faithful refined patch for BOTH echo candidates is the gold patch: mapping.md §2 refines MemberObj.is_class_member to the repo's ground-truth ownership `cls and hasattr(cls,name) and name in cls.__dict__` computed on the CANONICAL (unwrapped) object, i.e. exactly `inspect.unwrap(obj).__globals__[cls_path]` — so an impl reading is_class_member (or canonical(obj).is_class_member) refines to the gold ownership computation, not the pre-patch obj.__globals__ one. Ran under official harness: `run_resolve('sphinx-doc__sphinx-7910', <gold patch>, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, note='resolved', FLAKY=False. (First resolve attempt returned COMPLETED=False due to a missing base image; pulled swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-7910:latest via mirror.gcr.io + retag, then re-ran to a real COMPLETED verdict.) This is the sanctioned echo shape (the audit policy): same-spec + verifies + faithful patch RESOLVES => not a weakness.

A-leg / refinement.md audit: A3 (canonical <-> sphinx.util.inspect.unwrap, A-consumed) is the only consumed axiom, over the UNCHANGED library callee the patch newly invokes; its substantive clause is_class_member == (cls_name in Result().ns and Result().ns[cls_name]) corresponds to real ownership recovery through the unwrapped __globals__, and G-AX/axiom_check.py builds the real cross-module functools.wraps scenario against stdlib inspect.unwrap and exits 0 (meta.json G-AX exit:0). A5 is the proof bridge (A-consumed, discharged by A3). No A-reference and no kind-3 legs (§C): the one genuinely-changed operand is the canonical(obj) call. Every leg is R / A-consumed / I; correspondence to the real callees holds.

Conclusion: the postcondition fully pins Result() to has_doc ∧ is_class_member ∧ enabled-category; the 6 behaviorally-wrong impls all fail verification, and the only verifying variants are gold-equivalent echoes whose faithful patch RESOLVES. No verifying same-spec impl has a non-resolving faithful patch. verify ⇒ correct holds. G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_const_none.py`, `atk_ignore_doc.py`, `atk_overinclude.py`, `atk_cat_swap.py`, `atk_return_true.py`, `atk_flip.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo.py`, `atk_canon_field.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_canon_field.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_const_none.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_ignore_doc.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_overinclude.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_cat_swap.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_return_true.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_flip.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7910.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documentation-tooling hook decides, for a documented special/init/private
  member of a class, whether that member should be INCLUDED in the generated
  documentation. The decision depends on whether the member's owning class can
  be recovered as the genuine owner of the member: the hook resolves the class
  by name through the member object's surrounding global namespace, then
  confirms the member is actually defined on that class.

  The member object handed to the hook may be a callable that has been WRAPPED
  by a decorator (the wrapper carries the original member's documentation and
  qualified name, but its surrounding global namespace is the decorator's, not
  the one in which the owning class is defined). The owning class must therefore
  be resolved through the ORIGINAL (unwrapped) member object's global namespace
  -- the namespace in which the member, and hence its class, is genuinely
  defined -- never through the wrapper's. Concretely:

    * the owning class is looked up by its name token in the global namespace of
      the canonical (unwrapped) member object, and the member is the class's own
      member iff that lookup both resolves the class AND records the member name
      among the class's own members;
    * a documented special/init/private member that IS its class's own member,
      and whose corresponding inclusion setting is enabled, is INCLUDED
      (Result() is False -- "do not skip"); otherwise the hook abstains
      (Result() is None) and leaves the default decision untouched.

  The behavioural consequence that matters: wrapping a member with a
  documentation-preserving decorator does not hide it from the docs, because the
  ownership lookup follows the unwrapped object's namespace, which still knows
  the class.

Modelling choices (Nagini fragment):
  * The member name and the owning class-name token are opaque ``int``
    identities; the tested behaviour only observes whether the ownership lookup
    succeeds, so integer identity is the faithful carrier (mapping.md s2).
  * The member object is a minimal class exposing only the touched fields: the
    ``has_doc`` flag, the ground-truth ``is_class_member`` flag, the owning
    class-name token ``cls_name`` (from the qualified name) and the surrounding
    global namespace ``ns`` (``Dict[int, bool]`` keyed by a class-name token; a
    present key records, for the class resolved at that name, whether the member
    is among the class's OWN members -- the repository's
    ``cls_path in globals and name in cls.__dict__`` collapsed into the single
    ``cls_is_owner`` outcome). For a decorated object this ``ns`` is the
    wrapper's and need not contain ``cls_name`` at all.
  * ``canonical`` is the unchanged library primitive that recovers the original
    member object from a wrapper (the identity on an un-wrapped object). It is
    axiomatized (A-consumed) and checked against the real callee out-of-band by
    axiom_check.py (G-AX). It is the WEAKEST contract the proof needs.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Optional, Dict
from nagini_contracts.contracts import *


class MemberObj:
    """Minimal view of the member object handed to the hook. ``ns`` maps a
    class-name token to whether the class resolved there owns this member."""

    def __init__(self, has_doc: bool, is_class_member: bool, cls_name: int,
                 ns: Dict[int, bool]) -> None:
        Requires(Acc(dict_pred(ns), 1 / 2))
        Ensures(Acc(self.has_doc) and self.has_doc == has_doc)        # type: ignore
        Ensures(Acc(self.is_class_member) and self.is_class_member == is_class_member)  # type: ignore
        Ensures(Acc(self.cls_name) and self.cls_name == cls_name)     # type: ignore
        Ensures(Acc(self.ns) and self.ns is ns)                       # type: ignore
        Ensures(Acc(dict_pred(ns), 1 / 2))
        self.has_doc = has_doc
        self.is_class_member = is_class_member
        self.cls_name = cls_name
        self.ns = ns


# axioms-start
@ContractOnly
def canonical(obj: MemberObj) -> MemberObj:
    """The unchanged library primitive that recovers the ORIGINAL member object
    from a (possibly decorator-wrapped) one, following the documentation-
    preserving wrapper chain to its end; the identity on an object that is not
    wrapped. The recovered object carries the SAME inclusion-relevant identity
    (has_doc / membership / class name) and exposes the global namespace in
    which the member -- and therefore its owning class -- is genuinely defined,
    so that resolving the class there agrees with the ground-truth membership.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    WEAKEST contract the proof needs.
    """
    Requires(Acc(obj.has_doc, 1 / 4) and Acc(obj.is_class_member, 1 / 4))
    Requires(Acc(obj.cls_name, 1 / 4))
    Ensures(Acc(obj.has_doc, 1 / 4) and Acc(obj.is_class_member, 1 / 4))
    Ensures(Acc(obj.cls_name, 1 / 4))
    Ensures(Result() is not None)
    Ensures(Acc(Result().has_doc, 1 / 2) and Acc(Result().is_class_member, 1 / 2))
    Ensures(Acc(Result().cls_name, 1 / 2))
    Ensures(Acc(Result().ns) and Acc(dict_pred(Result().ns)))
    Ensures(Result().has_doc == obj.has_doc)
    Ensures(Result().cls_name == obj.cls_name)
    Ensures(Result().is_class_member == obj.is_class_member)
    # The recovered object's namespace genuinely records ownership: the owning
    # class is resolvable there and owns the member EXACTLY when the member is a
    # genuine class member. (The wrapper's namespace need not -- that is the
    # whole point of recovering the original.)
    Ensures(obj.is_class_member ==
            (obj.cls_name in Result().ns and Result().ns[obj.cls_name]))
# axioms-end


# pure-start
# No pure helpers required.
# pure-end


def skip_decision(obj: MemberObj, is_special: bool, is_init: bool,
                  is_private: bool, inc_special: bool, inc_init: bool,
                  inc_private: bool) -> Optional[bool]:
    # pre-conditions-start
    # `obj` is read-only -- fractional permission on every touched field and on
    # its namespace (directive 5).
    Requires(Acc(obj.has_doc, 1 / 2) and Acc(obj.is_class_member, 1 / 2))
    Requires(Acc(obj.cls_name, 1 / 2) and Acc(obj.ns, 1 / 2))
    Requires(Acc(dict_pred(obj.ns), 1 / 4))
    # Exactly one inclusion category applies to a member (init / special /
    # private are mutually exclusive in the repository's classification).
    Requires(Implies(is_init, not is_special and not is_private))
    Requires(Implies(is_special, not is_init and not is_private))
    Requires(Implies(is_private, not is_init and not is_special))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(obj.has_doc, 1 / 2) and Acc(obj.is_class_member, 1 / 2))
    Ensures(Acc(obj.cls_name, 1 / 2) and Acc(obj.ns, 1 / 2))
    Ensures(Acc(dict_pred(obj.ns), 1 / 4))
    # The result is grounded in the TRUE ownership (recovered through the
    # unwrapped namespace), never in whether the wrapper's namespace happens to
    # contain the class:
    #   * a documented, genuinely-owned member whose category is enabled is
    #     INCLUDED -- Result() is False (do not skip);
    #   * any other case abstains -- Result() is None.
    Ensures(Result() is False or Result() is None)
    Ensures((Result() is False) ==
            (obj.has_doc and obj.is_class_member and
             ((is_special and inc_special) or
              (is_init and inc_init) or
              (is_private and inc_private))))
    # post-conditions-end
    # impl-start
    doc = obj.has_doc
    member = obj.is_class_member
    if not doc:
        return None
    # Resolve the owning class through the ORIGINAL (unwrapped) object's
    # namespace -- the namespace that genuinely knows the class.
    canon = canonical(obj)
    Assert(canon.cls_name == obj.cls_name)
    Assert(canon.is_class_member == member)
    cls_is_owner = False
    if obj.cls_name in canon.ns:
        cls_is_owner = canon.ns[obj.cls_name]
    # The unwrapped namespace lookup recovers the ground-truth ownership.
    Assert(cls_is_owner == member)
    if cls_is_owner:
        if ((is_special and inc_special) or
                (is_init and inc_init) or
                (is_private and inc_private)):
            return False
    return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Project root here; adversary/verify run via python with SBU_BENCHMARK_DIR=benchmark-verified and concurrent runs.

Positive control: cp of bundle model.py -> `bash scripts/nagini_verify.sh positive_control.py` => Verification successful (18.2s), exit 0.

Prepatch reproduced: atk_prepatch.py (=model_prepatch.py, single edit canon.ns->obj.ns) => same-spec exit 0; nagini_verify exit 1: 'Postcondition of skip_decision might not hold. Assertion ((Result() is False) == (obj.has_doc and obj.is_class_member and ...))' — the spec senses the changed __globals__ source (G-DIFF). prepatch_reproduced=true.

atk_echo (ungrounded-oracle echo: reads obj.is_class_member directly, ignoring canonical/ns): CANDIDATE (shares spec AND verifies, 20.6s, exit 0).
- atk_canon_field (reads canonical(obj).is_class_member directly): CANDIDATE (verifies, 22.0s, exit 0).
- atk_const_none (constant None / partial-domain): NOT-A-COUNTEREXAMPLE (does not verify — fails postcond).
- atk_ignore_doc (drops has_doc guard): NOT-A-COUNTEREXAMPLE (does not verify).
- atk_overinclude (control-flow-effect: return False before category check): NOT-A-COUNTEREXAMPLE (does not verify).
- atk_cat_swap (boundary: inc_init/inc_special swapped): NOT-A-COUNTEREXAMPLE (does not verify).
- atk_return_true (wrong codomain: return True): NOT-A-COUNTEREXAMPLE (does not verify).
- atk_flip (include when NOT owned): NOT-A-COUNTEREXAMPLE (does not verify).

Materialized+resolved every CANDIDATE. Faithful refined patch for BOTH echo candidates is the gold patch: mapping.md §2 refines MemberObj.is_class_member to the repo's ground-truth ownership `cls and hasattr(cls,name) and name in cls.__dict__` computed on the CANONICAL (unwrapped) object, i.e. exactly `inspect.unwrap(obj).__globals__[cls_path]` — so an impl reading is_class_member (or canonical(obj).is_class_member) refines to the gold ownership computation, not the pre-patch obj.__globals__ one. Ran under official harness: `run_resolve('sphinx-doc__sphinx-7910', <gold patch>, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, note='resolved', FLAKY=False. (First resolve attempt returned COMPLETED=False due to a missing base image; pulled swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-7910:latest via mirror.gcr.io + retag, then re-ran to a real COMPLETED verdict.) This is the sanctioned echo shape (the audit policy): same-spec + verifies + faithful patch RESOLVES => not a weakness.

A-leg / refinement.md audit: A3 (canonical <-> sphinx.util.inspect.unwrap, A-consumed) is the only consumed axiom, over the UNCHANGED library callee the patch newly invokes; its substantive clause is_class_member == (cls_name in Result().ns and Result().ns[cls_name]) corresponds to real ownership recovery through the unwrapped __globals__, and G-AX/axiom_check.py builds the real cross-module functools.wraps scenario against stdlib inspect.unwrap and exits 0 (meta.json G-AX exit:0). A5 is the proof bridge (A-consumed, discharged by A3). No A-reference and no kind-3 legs (§C): the one genuinely-changed operand is the canonical(obj) call. Every leg is R / A-consumed / I; correspondence to the real callees holds.

Conclusion: the postcondition fully pins Result() to has_doc ∧ is_class_member ∧ enabled-category; the 6 behaviorally-wrong impls all fail verification, and the only verifying variants are gold-equivalent echoes whose faithful patch RESOLVES. No verifying same-spec impl has a non-resolving faithful patch. verify ⇒ correct holds. G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for nagini sphinx-doc__sphinx-7910. Setup confirmed: /tmp worktree HEAD=base_commit 27ac10de0 is pre-patch (cls = obj.__globals__[cls_path]); working tree carries the gold patch (cls = inspect.unwrap(obj).__globals__[cls_path]) — the single-operand change the model captures as canonical(obj).ns vs obj.ns. same-spec exits 0; pre/post-condition regions are byte-identical between model.py and model_prepatch.py. model.py verifies under the pinned Nagini (Verification successful, 18s).

Behavioral fidelity: I ran the gold-patched real _skip_member against the spec postcondition ((Result() is False) == (has_doc and is_class_member and enabled-category), else None) over an exhaustive matrix — {__special_doc__, __init__, _priv, __undoc__} x {owned on the class, inherited from a base} x all 8 (inc_special,inc_init,inc_private) settings, using functools.wraps cross-module decorators (the tested shape). is_class_member is taken as the real code's actual ownership computation: cls_path=obj.__qualname__.rpartition('.')[0], cls=inspect.unwrap(obj).__globals__[cls_path], name in cls.__dict__. Result: 64/64 exact agreement, 0 mismatches. Decorated members yield False (include) exactly where enabled + owned + documented, None otherwise — matching the gold patch on the discriminating F2P case (test_class_decorated_doc).

Boundary probes that appear to diverge are all explicitly OUT OF the modeled scope per mapping.md §2 and therefore not defects: (1) __weakref__ — documented getset_descriptor whose qualname is C.__weakref__ and which IS in C.__dict__, so the raw postcondition predicate would say False, but the real code returns None via the `name != '__weakref__'` guard; the mapping restricts the domain to non-weakref members. (2) the what=='module' branch and (3) the dotted-cls_path importlib branch — both excluded (single-component, documented class/exception member only), matching the F2P/P2P tested path where the changed line cls=<chosen>.__globals__[cls_path] is reached. These are honestly declared scope restrictions, not spec drift.

Conclusion: within its declared domain the spec agrees with the real callee on every input; it is neither too strong nor drifting. No diverging input exists in scope. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py with the impl region elided (confirmed via markers.spec_view for the nagini backend: impl-start/impl-end collapsed to a placeholder). The audit-side artifacts refinement.md / mapping.md / patch.diff quote the gold hunk verbatim, but they are NOT part of the consumer spec view, so their content does not count as spec-view leakage. The mechanical G-LEAK lexical screen passes clean (no hard failures, no warnings; no gold-diff line, diff markers, patched-file path, patched-symbol echo, or bug/fix narration).

Gold edit: `cls = obj.__globals__[cls_path]` -> `cls = inspect.unwrap(obj).__globals__[cls_path]` (+ `from sphinx.util import inspect`) in sphinx/ext/napoleon/__init__.py.

Baseline (public problem_statement, NOT hints): the problem_statement is EXTREMELY explicit already -- it names the exact offending line `cls = obj.__globals__[cls_path]`, states the object is a `functools.wraps`-decorated method whose `__globals__` no longer contains the class (so `cls_is_owner=False`), and names napoleon_include_init_with_doc. The fix (follow the wrapper to the original/unwrapped object) is essentially telegraphed by the public statement itself.

The spec view describes desired behaviour abstractly: resolve the owning class through the 'ORIGINAL (unwrapped)' / 'canonical' member object's global namespace rather than the wrapper's. It never names `inspect.unwrap`, `sphinx.util.inspect`, the file path, or any diff line, and it reproduces no gold-patch specifics. Everything the spec view reveals (wrapping preserves doc/qualname; owning class lives in the unwrapped object's namespace) is a strict subset of, and less concrete than, what the public problem_statement already discloses. Therefore the spec view leaks nothing about the gold edit beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
