# P2 adversarial audit — sphinx-doc__sphinx-8638

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch_name_role.py`, `atk_2_diverge_self_invoke.py`, `atk_3_diverge_loop.py`, `atk_4_skip_normalisation.py`, `atk_5_overeager_normalisation.py`, `atk_6_partial_domain_make_xref.py`, `atk_7_boundary_positive_role.py`, `atk_9_recursive_role_substitution.py`, `atk_10_extra_token.py`, +5 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_ungrounded_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_name_role.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,10 +135,9 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
-    name_role = 0
+    # PREPATCH BUG: the attribute/instance-variable field still configures a
+    # present (object-reference) role for its name token.
+    name_role = NULL_ROLE
     name_node = make_xref(name_role)
     type_node = make_xref(rendered_role(type_role, type_target_is_null))
     par = [name_node, type_node]  # type: List[FieldNode]
```

Attack 2 — `atk_2_diverge_self_invoke.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,12 +135,8 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
-    name_role = 0
-    name_node = make_xref(name_role)
-    type_node = make_xref(rendered_role(type_role, type_target_is_null))
-    par = [name_node, type_node]  # type: List[FieldNode]
+    # DIVERGENCE: never delivers an entry; under partial correctness every
+    # postcondition (including the discriminating name-token clause) is vacuous.
+    par = build_variable_field_entry(type_role, type_target_is_null)
     return par
     # impl-end
```

Attack 3 — `atk_3_diverge_loop.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,12 +135,17 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
     name_role = 0
     name_node = make_xref(name_role)
     type_node = make_xref(rendered_role(type_role, type_target_is_null))
     par = [name_node, type_node]  # type: List[FieldNode]
+    while type_role != 0:
+        Invariant(Acc(list_pred(par)) and len(par) == 2)
+        Invariant(Acc(par[0].is_xref) and Acc(par[0].reftype))
+        Invariant(Acc(par[1].is_xref) and Acc(par[1].reftype))
+        Invariant(par[0].is_xref is False and par[0].reftype == 0)
+        Invariant(par[1].is_xref is True)
+        Invariant(par[1].reftype == rendered_role(type_role, type_target_is_null))
+        type_role = type_role
     return par
     # impl-end
```

Attack 4 — `atk_4_skip_normalisation.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,12 +135,12 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
     name_role = 0
     name_node = make_xref(name_role)
-    type_node = make_xref(rendered_role(type_role, type_target_is_null))
+    # A3b DELETED: the configured type role is used verbatim, so on the null
+    # type target this renders under the type role where the real renderer
+    # falls back to the object role.
+    type_node = make_xref(type_role)
     par = [name_node, type_node]  # type: List[FieldNode]
     return par
     # impl-end
```

Attack 5 — `atk_5_overeager_normalisation.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,12 +135,14 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
     name_role = 0
     name_node = make_xref(name_role)
-    type_node = make_xref(rendered_role(type_role, type_target_is_null))
+    # A3b WIDENED: normalisation applied on the null target regardless of the
+    # configured role's identity (the real guard also tests the role).
+    if type_target_is_null:
+        type_node = make_xref(NULL_ROLE)
+    else:
+        type_node = make_xref(type_role)
     par = [name_node, type_node]  # type: List[FieldNode]
     return par
     # impl-end
```

Attack 6 — `atk_6_partial_domain_make_xref.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,8 +103,12 @@
     Ensures(Result().reftype == role)
     # post-conditions-end
     # impl-start
+    # A1 PARTIAL DOMAIN: only the two named role identities are carried
+    # faithfully; every other present role is collapsed onto the type role.
+    if role == TYPE_ROLE or role == NULL_ROLE:
+        return FieldNode(True, role)
     if role != 0:
-        return FieldNode(True, role)
+        return FieldNode(True, TYPE_ROLE)
     return FieldNode(False, 0)
     # impl-end
 
```

Attack 7 — `atk_7_boundary_positive_role.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,7 +103,9 @@
     Ensures(Result().reftype == role)
     # post-conditions-end
     # impl-start
-    if role != 0:
+    # A1 BOUNDARY: role presence tested as a positive code rather than a
+    # non-zero one, so a negative role code renders as a plain node.
+    if role > 0:
         return FieldNode(True, role)
     return FieldNode(False, 0)
     # impl-end
```

Attack 8 — `atk_8_ungrounded_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -135,12 +135,11 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
+    # ORACLE ECHO: the token emitter (the A-reference deep model) is never
+    # called; the two nodes are fabricated straight from the postcondition.
     name_role = 0
-    name_node = make_xref(name_role)
-    type_node = make_xref(rendered_role(type_role, type_target_is_null))
+    name_node = FieldNode(False, name_role)
+    type_node = FieldNode(True, rendered_role(type_role, type_target_is_null))
     par = [name_node, type_node]  # type: List[FieldNode]
     return par
     # impl-end
```

Attack 9 — `atk_9_recursive_role_substitution.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,9 +135,11 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
+    # CONTROL-FLOW EFFECT: on the null type target the entry is re-rendered by
+    # self-delegation under the already-normalised role instead of normalising
+    # in place.
+    if type_role == TYPE_ROLE and type_target_is_null:
+        return build_variable_field_entry(NULL_ROLE, type_target_is_null)
     name_role = 0
     name_node = make_xref(name_role)
     type_node = make_xref(rendered_role(type_role, type_target_is_null))
```

Attack 10 — `atk_10_extra_token.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,12 +135,10 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
     name_role = 0
     name_node = make_xref(name_role)
     type_node = make_xref(rendered_role(type_role, type_target_is_null))
-    par = [name_node, type_node]  # type: List[FieldNode]
+    extra = make_xref(0)
+    par = [name_node, type_node, extra]  # type: List[FieldNode]
     return par
     # impl-end
```

Attack 11 — `atk_11_alias_single_node.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,12 +135,8 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
-    name_role = 0
-    name_node = make_xref(name_role)
-    type_node = make_xref(rendered_role(type_role, type_target_is_null))
-    par = [name_node, type_node]  # type: List[FieldNode]
+    # A4 ALIASING: a single rendered node is placed in both token slots.
+    node = make_xref(rendered_role(type_role, type_target_is_null))
+    par = [node, node]  # type: List[FieldNode]
     return par
     # impl-end
```

Attack 12 — `atk_12_control_assert_false.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,12 +135,7 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
-    name_role = 0
-    name_node = make_xref(name_role)
-    type_node = make_xref(rendered_role(type_role, type_target_is_null))
-    par = [name_node, type_node]  # type: List[FieldNode]
+    Assert(False)
+    par = build_variable_field_entry(type_role, type_target_is_null)
     return par
     # impl-end
```

Attack 13 — `atk_13_xref_loses_reftype.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,8 +103,9 @@
     Ensures(Result().reftype == role)
     # post-conditions-end
     # impl-start
+    # A1 MASKED: a linking token is emitted without its reference kind.
     if role != 0:
-        return FieldNode(True, role)
+        return FieldNode(True, 0)
     return FieldNode(False, 0)
     # impl-end
 
```

Attack 14 — `atk_14_entry_partial_domain.py` → rejected (same spec, does not verify — good)

```diff
@@ -135,12 +135,14 @@
     Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
     # post-conditions-end
     # impl-start
-    # The attribute / instance-variable field configures no role for its name
-    # token, so the name slot is built under an absent role (code 0);
-    # normalisation is the identity on an absent role, for every name target.
-    name_role = 0
-    name_node = make_xref(name_role)
-    type_node = make_xref(rendered_role(type_role, type_target_is_null))
+    # ENTRY-LEVEL PARTIAL DOMAIN: the guarantees are honoured only on the
+    # single (type_role, target) shape the hidden test exercises.
+    if type_role == TYPE_ROLE and not type_target_is_null:
+        name_node = make_xref(0)
+        type_node = make_xref(TYPE_ROLE)
+    else:
+        name_node = make_xref(NULL_ROLE)
+        type_node = make_xref(rendered_role(type_role, type_target_is_null))
     par = [name_node, type_node]  # type: List[FieldNode]
     return par
     # impl-end
```

Attack 15 — `atk_15_diverge_in_make_xref.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,9 +103,9 @@
     Ensures(Result().reftype == role)
     # post-conditions-end
     # impl-start
-    if role != 0:
-        return FieldNode(True, role)
-    return FieldNode(False, 0)
+    # DIVERGENCE inside the A-reference deep model itself: the token is never
+    # delivered, so make_xref's own postconditions go vacuous.
+    return make_xref(role)
     # impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8638.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A typed documentation field renders one entry as a paragraph consisting of a
  *name* token followed by a parenthesised *type* token. Each token is turned
  into an interlinking cross-reference node IF AND ONLY IF the role configured
  for that token slot is present; with no configured role the token is emitted
  as a plain inline text node that links nowhere, and when it does link it
  carries the role it is RENDERED under as its reference kind.

  A configured role is normalised against the token's own target before the
  token links: a slot configured with the type-reference role whose target
  names the null value renders under the fallback object-reference role
  instead, the null value not being a type. Normalisation is the identity in
  every other case — in particular on an absent role, for every target.

  Rendering an entry is a bounded step of the field transformation: the entry
  is always delivered, so every guarantee below is owed on every entry rather
  than only on the ones an implementation gets round to producing.

  The field type used to document attributes / instance variables configures NO
  role for its name token. Therefore the rendered name token of such an entry
  must be a PLAIN inline node (it must NOT become a cross-reference), while its
  type token — whose type-role is present — must be a cross-reference whose
  reference kind equals that type-role NORMALISED against the type target.

A configured role is modelled as an ``int`` role code: ``0`` denotes "no role
configured" (an absent / empty role); any non-zero value denotes a present role
identified by that code. Two role identities are named (``TYPE_ROLE``,
``NULL_ROLE``) because normalisation is defined in terms of them. The only
properties of a role the behaviour depends on are its presence (zero vs
non-zero) and, when present, its identity — both captured by the code. A
rendered token is a minimal node carrying only the two touched fields: whether
it is a cross-reference (``is_xref``) and, when it is, the reference kind it
carries (``reftype``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class FieldNode:
    def __init__(self, xref: bool, ref: int) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_xref) and self.is_xref == xref)    # type: ignore
        Ensures(Acc(self.reftype) and self.reftype == ref)     # type: ignore
        self.is_xref = xref
        self.reftype = ref

# axioms-start
# (no unchanged opaque callee is consumed; the token-emission decision, the
#  role normalisation and the field-entry construction are modelled deeply.)
# axioms-end

# pure-start
# Role identities the rendering distinguishes. Code ``0`` is an absent role; a
# non-zero code identifies a present role. Two identities are named because the
# role normalisation below is defined in terms of them.
TYPE_ROLE = 1   # the type-reference role a typed slot is configured with
NULL_ROLE = 2   # the role a token falls back to when its target names the null
                # value (which is not a type)

@Pure
def rendered_role(role: int, target_is_null: bool) -> int:
    """The role a token is actually rendered under.

    A token configured with the type-reference role whose target names the null
    value renders under the fallback role instead; every other configuration —
    an absent role included — renders under exactly its configured role.
    """
    if role == TYPE_ROLE and target_is_null:
        return NULL_ROLE
    return role
# pure-end

def make_xref(role: int) -> FieldNode:
    """Emit the node for one token under the *role* code it renders under.

    With a present role (non-zero code) the token becomes a cross-reference
    carrying that role as its reference kind; with no role (code ``0``) the
    token is a plain inline node that links nowhere. The presence of the role is
    the sole determinant of whether the token links.
    """
    # pre-conditions-start
    # emitting one token is a bounded step of the rendering: the node is always
    # delivered, so the guarantees below are owed on every role.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().is_xref) and Acc(Result().reftype))
    # a token cross-references exactly when the role it renders under is present
    Ensures(Result().is_xref == (role != 0))
    # the rendered token carries exactly that role as the reference kind: the
    # present role when it links, and the "no role" sentinel (0) otherwise (a
    # plain inline node has no reference kind).
    Ensures(Result().reftype == role)
    # post-conditions-end
    # impl-start
    if role != 0:
        return FieldNode(True, role)
    return FieldNode(False, 0)
    # impl-end

def build_variable_field_entry(type_role: int,
                               type_target_is_null: bool) -> List[FieldNode]:
    # pre-conditions-start
    # the type slot of this field carries a present (type-reference) role
    Requires(type_role != 0)
    # rendering one entry is a bounded step of the transformation: the entry is
    # always delivered, so the guarantees below are owed on every admissible
    # input rather than only on the inputs an implementation chooses to answer.
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # the entry has exactly two rendered tokens: the name then the type
    Ensures(len(Result()) == 2)
    Ensures(Acc(Result()[0].is_xref) and Acc(Result()[0].reftype))
    Ensures(Acc(Result()[1].is_xref) and Acc(Result()[1].reftype))
    # the NAME token must be a plain inline node — never a cross-reference,
    # and a plain node carries no reference kind (the "no role" sentinel 0)
    Ensures(Result()[0].is_xref is False)
    Ensures(Result()[0].reftype == 0)
    # the TYPE token must be a cross-reference carrying its type-role as
    # NORMALISED against the type target
    Ensures(Result()[1].is_xref is True)
    Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
    # post-conditions-end
    # impl-start
    # The attribute / instance-variable field configures no role for its name
    # token, so the name slot is built under an absent role (code 0);
    # normalisation is the identity on an absent role, for every name target.
    name_role = 0
    name_node = make_xref(name_role)
    type_node = make_xref(rendered_role(type_role, type_target_is_null))
    par = [name_node, type_node]  # type: List[FieldNode]
    return par
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND (verify=>correct holds). 15 same-spec wrong impls run through `adversary weakness`; 14 REJECTED, the 1 CANDIDATE's materialized faithful patch RESOLVED under the official harness, so it is a correct alternative impl, not a counterexample.

DECISIVE CONTEXT — THE PRIOR BROKEN FINDING IS ALREADY REPAIRED, AND meta.json's G-EQ RECORD IS STALE. meta.json gates.G-EQ says "BROKEN ... atk_8_diverge_self_invoke.py verifies but its patch does not resolve", but that was recorded against model.py sha bd3a9868...; the CURRENT frozen model.py is de3e756f... and now carries `from nagini_contracts.obligations import MustTerminate` plus `Requires(MustTerminate(2/6/10))` on FieldNode.`__init__` / make_xref / build_variable_field_entry — exactly the repair that verdict.md's REPAIR section prescribed. G-VERIFY/G-GOLD/G-DIFF/G-AX/G-CONF/G-MUT/G-PBT/G-RESOLVE are all recorded pass at the new sha. I re-encoded the named counterexample verbatim and confirmed it is now KILLED (see atk_2 below), so the recorded G-EQ/G-PANEL-1 fail is a stale label on a superseded model.py, not a live defect. Per the retained-attack-labels lesson I did not inherit that verdict; I judged the bundle fresh.

COMMANDS (all files built by copying the frozen model.py and editing ONLY impl-region bytes; every one confirmed spec-byte-identical first):
  python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-8638 <f>   # 16/16 SAME, exit 0
  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-8638 <f>
No timeouts and no crashes -- all 16 verifications returned a real verdict (16-18s each).

### PER-ATTACK RESULTS (exit 2 = rejected = good; exit 0 = CANDIDATE):
 1. atk_1_prepatch_name_role.py            PREPATCH BUG REPRODUCED. name_role = NULL_ROLE (the pre-patch rolename='obj'). exit 2, verification failed -> the spec senses the bug (refinement.md B leg, Ensures(Result()[0].is_xref is False)).
 2. atk_2_diverge_self_invoke.py           PRIOR NAMED COUNTEREXAMPLE, re-encoded verbatim: `par = build_variable_field_entry(type_role, type_target_is_null)`. exit 2, verification failed. The MustTerminate(10) obligation now rejects the divergence that formerly made every postcondition vacuous. THE PREVIOUSLY-BROKEN LEG IS CLOSED.
 3. atk_3_diverge_loop.py                  Control-flow-effect: non-decreasing `while type_role != 0` carrying the full postcondition in Invariants. exit 2 (MustTerminate needs the method level AND kills the loop). 
 4. atk_4_skip_normalisation.py            A3b DELETED: type token built from the bare `type_role`. exit 2 -> the type-token reftype clause really is stated THROUGH rendered_role; drop it and the null-target case fails.
 5. atk_5_overeager_normalisation.py       A3b WIDENED: normalise on the null target for EVERY role identity, ignoring the role half of the real guard. exit 2 -> A3b is pinned from BOTH sides, not just one.
 6. atk_6_partial_domain_make_xref.py      A1 PARTIAL DOMAIN: deep model faithful only on TYPE_ROLE/NULL_ROLE, collapsing every other present role onto TYPE_ROLE. exit 2 -> make_xref's `reftype == role` is total over role codes, not just the two named identities.
 7. atk_7_boundary_positive_role.py        A1 BOUNDARY: presence tested `role > 0` instead of `role != 0`, so a negative code renders plain. exit 2 -> the presence predicate is pinned at the exact zero boundary.
 8. atk_8_ungrounded_echo.py               UNGROUNDED-ORACLE ECHO: bypasses the A1 deep model entirely; both nodes fabricated straight from the postcondition (FieldNode(False, 0) / FieldNode(True, rendered_role(...))). exit 0 CANDIDATE (shares spec AND verifies, 17.8s). => RESOLVE-CHECKED, SEE BELOW.
 9. atk_9_recursive_role_substitution.py   Control-flow effect: on the null target, re-render by TERMINATING self-delegation under the pre-normalised role. exit 2 (the recursive call cannot discharge the caller's MustTerminate budget).
10. atk_10_extra_token.py                  A4 SHAPE: a third rendered token appended. exit 2 (len(Result()) == 2).
11. atk_11_alias_single_node.py            A4 ALIASING: one node placed in BOTH slots, so the name slot inherits the type token's xref. exit 2 -> the two slots are separately pinned; the model's list is not satisfiable by aliasing.
12. atk_12_control_assert_false.py         VACUITY CONTROL for the self-call path: `Assert(False)` before the same self-delegation. exit 2, verification failed -> confirms the guarded-self-call trap is not what is rejecting attacks 2/9; those sit on FEASIBLE paths and are killed by the obligation, not by an infeasible guard.
13. atk_13_xref_loses_reftype.py           A1 MASKED: a linking token emitted with reftype 0. exit 2.
14. atk_14_entry_partial_domain.py         ENTRY-LEVEL PARTIAL DOMAIN: honours the guarantees only on the exact F2P shape (TYPE_ROLE, not null) and re-introduces the pre-patch name link everywhere else. exit 2 -> the spec's claim is universally quantified over its declared domain, so it cannot be satisfied by teaching to the hidden test.
15. atk_15_diverge_in_make_xref.py         DIVERGENCE AT THE OTHER SITE: the A1 deep model itself never delivers (`return make_xref(role)`). exit 2 -> MustTerminate(6) is present on make_xref too, so the obligation is not just on the entry builder.

THE ONE CANDIDATE, RESOLVE-CHECKED (mandatory step, executed — not speculated): Faithful patch: patch_atk8.diff (submitted in `patches`), built in my own git worktree of sphinx-doc_sphinx.git at base_commit 4b452338f. It refines atk_8's impl exactly: a PyVariableField subclass whose handle_item CONSTRUCTS both tokens directly (literal_strong name node; pending_xref type node under the in-place normalised role) instead of routing each token through make_xref, and it carries the gold delta (the 'variable' field no longer sets a name rolename). Everything the abstraction does not observe (mixin refspecific/module+class context, the ' (' / ')' / ' -- ' literals, description content, the .pop() aliasing note) is preserved verbatim.

Command: swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8638', patch_atk8.diff) Result (resolve_atk8.json): completed=True, RESOLVED=TRUE, note='resolved', attempts=1, patch_successfully_applied=True, FAIL_TO_PASS 1/1 SUCCESS (tests/test_domain_py.py::test_info_field_list_var), PASS_TO_PASS 34/34 SUCCESS, 0 failures. => atk_8 is NOT a counterexample. It is behaviourally EQUAL to gold under the mapping.md abstraction (it inlines the node construction the deep model would have performed), so verify=>correct is upheld, not refuted. Inlining an A-reference deep model rather than calling it is a legitimate alternative implementation; the spec correctly admits it.

POSITIVE CONTROL (non-vacuity): pos_control.py, a byte-identical copy of the frozen impl, exit 0 CANDIDATE 'shares spec AND verifies' (16.7s). The spec is satisfiable, so the 14 rejections above are real discrimination and not a spec that rejects everything.

**REGION-AUDIT CONTROL:** ctl_15_fieldnode_init_edit.py edits FieldNode.`__init__` (outside every impl region) and same-spec reports DIFFERENT. So FieldNode's constructor contract is spec-frozen and an attack cannot weaken the node carrier itself — the attack surface really is the impl regions only.

REFINEMENT.MD AUDIT (step 3) — every leg is R / A-reference / I; NO kind-3, and no A-CONSUMED axiom exists in this bundle (the axioms region is a comment; meta.json axioms=[] ), so nothing is assumed rather than established. I verified each A-leg's line references against the real source at base_commit by git show: A1 make_xref -> Field.make_xref, sphinx/util/docfields.py:63-73. CONFIRMED verbatim: `if not rolename: return contnode or innernode(target, target)` else `pending_xref(..., reftype=rolename, ...)`. The node KIND is decided solely by role truthiness, which is exactly `is_xref == (role != 0)` / `reftype == role`. A-reference (deep model, not consumed) — correct classification.

A2 name_role = 0 -> the gold delta. patch.diff at the instance root is byte-identical to instance.json['patch'] (diffed), and removes exactly `rolename='obj'` from the 'variable' PyTypedField. Tagged I under the role-carrier R — correct: 0 <-> rolename absent/None, both taking make_xref's falsy branch. A3 type token -> make_xrefs(self.typerolename, ...) at docfields.py:186; typerolename='class' untouched by the patch. CONFIRMED. Tagged I under R — correct. A3b rendered_role -> PyTypedField.make_xref, sphinx/domains/python.py:326-333. CONFIRMED verbatim: `if rolename == 'class' and target == 'None': rolename = 'obj'` then super(). A-reference.

This is the subtlest leg and it is RIGHT: stating the type-token reftype through rendered_role rather than pinning type_role is NECESSARY, because on :vartype: None the real renderer emits 'obj', not 'class'. Attacks 4 and 5 confirm the clause is refutable from both directions. A4 par = [name_node, type_node] -> handle_item's paragraph, docfields.py:174-193. CONFIRMED: the real paragraph is [name, ' (', type, ')', ' -- ', content], and the model abstracts to the two role-bearing tokens in order. Tagged R — correct; attacks 10/11 show the shape and slot identity are genuinely pinned. The env stand-in claim also checks out: Domain.process_field_xref's body is `pass` (sphinx/domains/`__init__`.py:311-315) and PythonDomain does not override it, so omitting it touches neither observable.

INDEPENDENT A-LEG DIFFERENTIAL PROBE (mine, NOT derived from the bundle's conformance_check.py): aleg_probe.py, run against my own worktree with patch.diff APPLIED. 4406 checks, 0 divergences: (a) real PyTypedField.make_xref over 14 roles x 13 targets incl. 'None', near misses 'NoneType'/'none'/'None_'/'NONE'/'nOne'/'None ' and the trimming prefixes '.None'/'~None' — only literal 'None' normalises, so rendered_role's exact-match guard is exact; (b) real Field.make_xref node-kind over falsy {None, '', } and truthy roles incl.

'0'/'False'; (c) real TypedField.make_field entry over the LIVE post-patch 'variable' field read out of PyObject.doc_field_types (confirmed rolename=None, typerolename='class') and over all 12 type-role identities x 13 targets; (d) 4000 seeded in-domain fuzz entries with forced null-target draws and varied real env ref_context. DISCRIMINATION CONTROL: the same probe on the pre-patch config (rolename='obj') DIVERGES, real=[(True,2),(True,1)] vs model=[(False,0),(True,1)] — so the probe is capable of failing and is not vacuous. (One host-compat note, my worktree only, not the bundle: this sphinx predates jinja2 3.1's removal of `environmentfilter`, so my probe shims those aliases before importing; it touches nothing on the rendering path.)

**WHY I DID NOT FIND A HOLE.** The formerly-open hole was structural — partial-correctness vacuity — and it is now closed at BOTH call sites (attacks 2, 3, 9, 15 all die on the obligation, with attack 12 proving those paths are feasible rather than vacuously guarded). Beyond that, every observable the patch's delta touches is pinned totally over the declared domain: name-token plainness AND its zero reference kind, type-token linkage AND its normalised reference kind, the two-token shape, and slot distinctness. Partial-domain attacks fail at both the token level (6) and the entry level (14); the boundary of the presence predicate is exact (7); the reference-kind carrier cannot be masked (13) or aliased (11). The one impl that verifies is genuinely correct and resolves 35/35.

**HOUSEKEEPING:** my git worktree was removed (`git worktree remove --force`) and pruned; the bundle is byte-unmodified (model.py still de3e756f51201829e2b2b637697f628260943a5ccb2a652fb8e1816ce6179fb0, git status clean for the instance dir). All work stayed in 

ADVISORY FOR THE OWNER (does not affect this verdict): meta.json gates.G-EQ, gates.G-PANEL and gates.G-PANEL-1 still carry the pre-repair BROKEN/fail records against the superseded model.py sha bd3a9868..., and meta.json's top-level region_hashes block is stale relative to G-HYGIENE's recorded values (pre-conditions and post-conditions changed when MustTerminate landed; G-PANEL-3 flagged the same staleness). Re-stamping G-EQ at the current sha de3e756f... would clear it.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch_name_role.py`, `atk_2_diverge_self_invoke.py`, `atk_3_diverge_loop.py`, `atk_4_skip_normalisation.py`, `atk_5_overeager_normalisation.py`, `atk_6_partial_domain_make_xref.py`, `atk_7_boundary_positive_role.py`, `atk_9_recursive_role_substitution.py`, `atk_10_extra_token.py`, +5 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8_ungrounded_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch_name_role.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_diverge_self_invoke.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_diverge_loop.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_skip_normalisation.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_overeager_normalisation.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_partial_domain_make_xref.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_boundary_positive_role.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_ungrounded_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_recursive_role_substitution.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_extra_token.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_alias_single_node.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_control_assert_false.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_xref_loses_reftype.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_entry_partial_domain.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_diverge_in_make_xref.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8638.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A typed documentation field renders one entry as a paragraph consisting of a
  *name* token followed by a parenthesised *type* token. Each token is turned
  into an interlinking cross-reference node IF AND ONLY IF the role configured
  for that token slot is present; with no configured role the token is emitted
  as a plain inline text node that links nowhere, and when it does link it
  carries the role it is RENDERED under as its reference kind.

  A configured role is normalised against the token's own target before the
  token links: a slot configured with the type-reference role whose target
  names the null value renders under the fallback object-reference role
  instead, the null value not being a type. Normalisation is the identity in
  every other case — in particular on an absent role, for every target.

  Rendering an entry is a bounded step of the field transformation: the entry
  is always delivered, so every guarantee below is owed on every entry rather
  than only on the ones an implementation gets round to producing.

  The field type used to document attributes / instance variables configures NO
  role for its name token. Therefore the rendered name token of such an entry
  must be a PLAIN inline node (it must NOT become a cross-reference), while its
  type token — whose type-role is present — must be a cross-reference whose
  reference kind equals that type-role NORMALISED against the type target.

A configured role is modelled as an ``int`` role code: ``0`` denotes "no role
configured" (an absent / empty role); any non-zero value denotes a present role
identified by that code. Two role identities are named (``TYPE_ROLE``,
``NULL_ROLE``) because normalisation is defined in terms of them. The only
properties of a role the behaviour depends on are its presence (zero vs
non-zero) and, when present, its identity — both captured by the code. A
rendered token is a minimal node carrying only the two touched fields: whether
it is a cross-reference (``is_xref``) and, when it is, the reference kind it
carries (``reftype``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class FieldNode:
    def __init__(self, xref: bool, ref: int) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_xref) and self.is_xref == xref)    # type: ignore
        Ensures(Acc(self.reftype) and self.reftype == ref)     # type: ignore
        self.is_xref = xref
        self.reftype = ref

# axioms-start
# (no unchanged opaque callee is consumed; the token-emission decision, the
#  role normalisation and the field-entry construction are modelled deeply.)
# axioms-end

# pure-start
# Role identities the rendering distinguishes. Code ``0`` is an absent role; a
# non-zero code identifies a present role. Two identities are named because the
# role normalisation below is defined in terms of them.
TYPE_ROLE = 1   # the type-reference role a typed slot is configured with
NULL_ROLE = 2   # the role a token falls back to when its target names the null
                # value (which is not a type)

@Pure
def rendered_role(role: int, target_is_null: bool) -> int:
    """The role a token is actually rendered under.

    A token configured with the type-reference role whose target names the null
    value renders under the fallback role instead; every other configuration —
    an absent role included — renders under exactly its configured role.
    """
    if role == TYPE_ROLE and target_is_null:
        return NULL_ROLE
    return role
# pure-end

def make_xref(role: int) -> FieldNode:
    """Emit the node for one token under the *role* code it renders under.

    With a present role (non-zero code) the token becomes a cross-reference
    carrying that role as its reference kind; with no role (code ``0``) the
    token is a plain inline node that links nowhere. The presence of the role is
    the sole determinant of whether the token links.
    """
    # pre-conditions-start
    # emitting one token is a bounded step of the rendering: the node is always
    # delivered, so the guarantees below are owed on every role.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().is_xref) and Acc(Result().reftype))
    # a token cross-references exactly when the role it renders under is present
    Ensures(Result().is_xref == (role != 0))
    # the rendered token carries exactly that role as the reference kind: the
    # present role when it links, and the "no role" sentinel (0) otherwise (a
    # plain inline node has no reference kind).
    Ensures(Result().reftype == role)
    # post-conditions-end
    # impl-start
    if role != 0:
        return FieldNode(True, role)
    return FieldNode(False, 0)
    # impl-end

def build_variable_field_entry(type_role: int,
                               type_target_is_null: bool) -> List[FieldNode]:
    # pre-conditions-start
    # the type slot of this field carries a present (type-reference) role
    Requires(type_role != 0)
    # rendering one entry is a bounded step of the transformation: the entry is
    # always delivered, so the guarantees below are owed on every admissible
    # input rather than only on the inputs an implementation chooses to answer.
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # the entry has exactly two rendered tokens: the name then the type
    Ensures(len(Result()) == 2)
    Ensures(Acc(Result()[0].is_xref) and Acc(Result()[0].reftype))
    Ensures(Acc(Result()[1].is_xref) and Acc(Result()[1].reftype))
    # the NAME token must be a plain inline node — never a cross-reference,
    # and a plain node carries no reference kind (the "no role" sentinel 0)
    Ensures(Result()[0].is_xref is False)
    Ensures(Result()[0].reftype == 0)
    # the TYPE token must be a cross-reference carrying its type-role as
    # NORMALISED against the type target
    Ensures(Result()[1].is_xref is True)
    Ensures(Result()[1].reftype == rendered_role(type_role, type_target_is_null))
    # post-conditions-end
    # impl-start
    # The attribute / instance-variable field configures no role for its name
    # token, so the name slot is built under an absent role (code 0);
    # normalisation is the identity on an absent role, for every name target.
    name_role = 0
    name_node = make_xref(name_role)
    type_node = make_xref(rendered_role(type_role, type_target_is_null))
    par = [name_node, type_node]  # type: List[FieldNode]
    return par
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND (verify=>correct holds). 15 same-spec wrong impls run through `adversary weakness`; 14 REJECTED, the 1 CANDIDATE's materialized faithful patch RESOLVED under the official harness, so it is a correct alternative impl, not a counterexample.

DECISIVE CONTEXT — THE PRIOR BROKEN FINDING IS ALREADY REPAIRED, AND meta.json's G-EQ RECORD IS STALE. meta.json gates.G-EQ says "BROKEN ... atk_8_diverge_self_invoke.py verifies but its patch does not resolve", but that was recorded against model.py sha bd3a9868...; the CURRENT frozen model.py is de3e756f... and now carries `from nagini_contracts.obligations import MustTerminate` plus `Requires(MustTerminate(2/6/10))` on FieldNode.`__init__` / make_xref / build_variable_field_entry — exactly the repair that verdict.md's REPAIR section prescribed. G-VERIFY/G-GOLD/G-DIFF/G-AX/G-CONF/G-MUT/G-PBT/G-RESOLVE are all recorded pass at the new sha. I re-encoded the named counterexample verbatim and confirmed it is now KILLED (see atk_2 below), so the recorded G-EQ/G-PANEL-1 fail is a stale label on a superseded model.py, not a live defect. Per the retained-attack-labels lesson I did not inherit that verdict; I judged the bundle fresh.

COMMANDS (all files built by copying the frozen model.py and editing ONLY impl-region bytes; every one confirmed spec-byte-identical first):
  python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-8638 <f>   # 16/16 SAME, exit 0
  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-8638 <f>
No timeouts and no crashes -- all 16 verifications returned a real verdict (16-18s each).

### PER-ATTACK RESULTS (exit 2 = rejected = good; exit 0 = CANDIDATE):
 1. atk_1_prepatch_name_role.py            PREPATCH BUG REPRODUCED. name_role = NULL_ROLE (the pre-patch rolename='obj'). exit 2, verification failed -> the spec senses the bug (refinement.md B leg, Ensures(Result()[0].is_xref is False)).
 2. atk_2_diverge_self_invoke.py           PRIOR NAMED COUNTEREXAMPLE, re-encoded verbatim: `par = build_variable_field_entry(type_role, type_target_is_null)`. exit 2, verification failed. The MustTerminate(10) obligation now rejects the divergence that formerly made every postcondition vacuous. THE PREVIOUSLY-BROKEN LEG IS CLOSED.
 3. atk_3_diverge_loop.py                  Control-flow-effect: non-decreasing `while type_role != 0` carrying the full postcondition in Invariants. exit 2 (MustTerminate needs the method level AND kills the loop). 
 4. atk_4_skip_normalisation.py            A3b DELETED: type token built from the bare `type_role`. exit 2 -> the type-token reftype clause really is stated THROUGH rendered_role; drop it and the null-target case fails.
 5. atk_5_overeager_normalisation.py       A3b WIDENED: normalise on the null target for EVERY role identity, ignoring the role half of the real guard. exit 2 -> A3b is pinned from BOTH sides, not just one.
 6. atk_6_partial_domain_make_xref.py      A1 PARTIAL DOMAIN: deep model faithful only on TYPE_ROLE/NULL_ROLE, collapsing every other present role onto TYPE_ROLE. exit 2 -> make_xref's `reftype == role` is total over role codes, not just the two named identities.
 7. atk_7_boundary_positive_role.py        A1 BOUNDARY: presence tested `role > 0` instead of `role != 0`, so a negative code renders plain. exit 2 -> the presence predicate is pinned at the exact zero boundary.
 8. atk_8_ungrounded_echo.py               UNGROUNDED-ORACLE ECHO: bypasses the A1 deep model entirely; both nodes fabricated straight from the postcondition (FieldNode(False, 0) / FieldNode(True, rendered_role(...))). exit 0 CANDIDATE (shares spec AND verifies, 17.8s). => RESOLVE-CHECKED, SEE BELOW.
 9. atk_9_recursive_role_substitution.py   Control-flow effect: on the null target, re-render by TERMINATING self-delegation under the pre-normalised role. exit 2 (the recursive call cannot discharge the caller's MustTerminate budget).
10. atk_10_extra_token.py                  A4 SHAPE: a third rendered token appended. exit 2 (len(Result()) == 2).
11. atk_11_alias_single_node.py            A4 ALIASING: one node placed in BOTH slots, so the name slot inherits the type token's xref. exit 2 -> the two slots are separately pinned; the model's list is not satisfiable by aliasing.
12. atk_12_control_assert_false.py         VACUITY CONTROL for the self-call path: `Assert(False)` before the same self-delegation. exit 2, verification failed -> confirms the guarded-self-call trap is not what is rejecting attacks 2/9; those sit on FEASIBLE paths and are killed by the obligation, not by an infeasible guard.
13. atk_13_xref_loses_reftype.py           A1 MASKED: a linking token emitted with reftype 0. exit 2.
14. atk_14_entry_partial_domain.py         ENTRY-LEVEL PARTIAL DOMAIN: honours the guarantees only on the exact F2P shape (TYPE_ROLE, not null) and re-introduces the pre-patch name link everywhere else. exit 2 -> the spec's claim is universally quantified over its declared domain, so it cannot be satisfied by teaching to the hidden test.
15. atk_15_diverge_in_make_xref.py         DIVERGENCE AT THE OTHER SITE: the A1 deep model itself never delivers (`return make_xref(role)`). exit 2 -> MustTerminate(6) is present on make_xref too, so the obligation is not just on the entry builder.

THE ONE CANDIDATE, RESOLVE-CHECKED (mandatory step, executed — not speculated): Faithful patch: patch_atk8.diff (submitted in `patches`), built in my own git worktree of sphinx-doc_sphinx.git at base_commit 4b452338f. It refines atk_8's impl exactly: a PyVariableField subclass whose handle_item CONSTRUCTS both tokens directly (literal_strong name node; pending_xref type node under the in-place normalised role) instead of routing each token through make_xref, and it carries the gold delta (the 'variable' field no longer sets a name rolename). Everything the abstraction does not observe (mixin refspecific/module+class context, the ' (' / ')' / ' -- ' literals, description content, the .pop() aliasing note) is preserved verbatim.

Command: swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8638', patch_atk8.diff) Result (resolve_atk8.json): completed=True, RESOLVED=TRUE, note='resolved', attempts=1, patch_successfully_applied=True, FAIL_TO_PASS 1/1 SUCCESS (tests/test_domain_py.py::test_info_field_list_var), PASS_TO_PASS 34/34 SUCCESS, 0 failures. => atk_8 is NOT a counterexample. It is behaviourally EQUAL to gold under the mapping.md abstraction (it inlines the node construction the deep model would have performed), so verify=>correct is upheld, not refuted. Inlining an A-reference deep model rather than calling it is a legitimate alternative implementation; the spec correctly admits it.

POSITIVE CONTROL (non-vacuity): pos_control.py, a byte-identical copy of the frozen impl, exit 0 CANDIDATE 'shares spec AND verifies' (16.7s). The spec is satisfiable, so the 14 rejections above are real discrimination and not a spec that rejects everything.

**REGION-AUDIT CONTROL:** ctl_15_fieldnode_init_edit.py edits FieldNode.`__init__` (outside every impl region) and same-spec reports DIFFERENT. So FieldNode's constructor contract is spec-frozen and an attack cannot weaken the node carrier itself — the attack surface really is the impl regions only.

REFINEMENT.MD AUDIT (step 3) — every leg is R / A-reference / I; NO kind-3, and no A-CONSUMED axiom exists in this bundle (the axioms region is a comment; meta.json axioms=[] ), so nothing is assumed rather than established. I verified each A-leg's line references against the real source at base_commit by git show: A1 make_xref -> Field.make_xref, sphinx/util/docfields.py:63-73. CONFIRMED verbatim: `if not rolename: return contnode or innernode(target, target)` else `pending_xref(..., reftype=rolename, ...)`. The node KIND is decided solely by role truthiness, which is exactly `is_xref == (role != 0)` / `reftype == role`. A-reference (deep model, not consumed) — correct classification.

A2 name_role = 0 -> the gold delta. patch.diff at the instance root is byte-identical to instance.json['patch'] (diffed), and removes exactly `rolename='obj'` from the 'variable' PyTypedField. Tagged I under the role-carrier R — correct: 0 <-> rolename absent/None, both taking make_xref's falsy branch. A3 type token -> make_xrefs(self.typerolename, ...) at docfields.py:186; typerolename='class' untouched by the patch. CONFIRMED. Tagged I under R — correct. A3b rendered_role -> PyTypedField.make_xref, sphinx/domains/python.py:326-333. CONFIRMED verbatim: `if rolename == 'class' and target == 'None': rolename = 'obj'` then super(). A-reference.

This is the subtlest leg and it is RIGHT: stating the type-token reftype through rendered_role rather than pinning type_role is NECESSARY, because on :vartype: None the real renderer emits 'obj', not 'class'. Attacks 4 and 5 confirm the clause is refutable from both directions. A4 par = [name_node, type_node] -> handle_item's paragraph, docfields.py:174-193. CONFIRMED: the real paragraph is [name, ' (', type, ')', ' -- ', content], and the model abstracts to the two role-bearing tokens in order. Tagged R — correct; attacks 10/11 show the shape and slot identity are genuinely pinned. The env stand-in claim also checks out: Domain.process_field_xref's body is `pass` (sphinx/domains/`__init__`.py:311-315) and PythonDomain does not override it, so omitting it touches neither observable.

INDEPENDENT A-LEG DIFFERENTIAL PROBE (mine, NOT derived from the bundle's conformance_check.py): aleg_probe.py, run against my own worktree with patch.diff APPLIED. 4406 checks, 0 divergences: (a) real PyTypedField.make_xref over 14 roles x 13 targets incl. 'None', near misses 'NoneType'/'none'/'None_'/'NONE'/'nOne'/'None ' and the trimming prefixes '.None'/'~None' — only literal 'None' normalises, so rendered_role's exact-match guard is exact; (b) real Field.make_xref node-kind over falsy {None, '', } and truthy roles incl.

'0'/'False'; (c) real TypedField.make_field entry over the LIVE post-patch 'variable' field read out of PyObject.doc_field_types (confirmed rolename=None, typerolename='class') and over all 12 type-role identities x 13 targets; (d) 4000 seeded in-domain fuzz entries with forced null-target draws and varied real env ref_context. DISCRIMINATION CONTROL: the same probe on the pre-patch config (rolename='obj') DIVERGES, real=[(True,2),(True,1)] vs model=[(False,0),(True,1)] — so the probe is capable of failing and is not vacuous. (One host-compat note, my worktree only, not the bundle: this sphinx predates jinja2 3.1's removal of `environmentfilter`, so my probe shims those aliases before importing; it touches nothing on the rendering path.)

**WHY I DID NOT FIND A HOLE.** The formerly-open hole was structural — partial-correctness vacuity — and it is now closed at BOTH call sites (attacks 2, 3, 9, 15 all die on the obligation, with attack 12 proving those paths are feasible rather than vacuously guarded). Beyond that, every observable the patch's delta touches is pinned totally over the declared domain: name-token plainness AND its zero reference kind, type-token linkage AND its normalised reference kind, the two-token shape, and slot distinctness. Partial-domain attacks fail at both the token level (6) and the entry level (14); the boundary of the presence predicate is exact (7); the reference-kind carrier cannot be masked (13) or aliased (11). The one impl that verifies is genuinely correct and resolves 35/35.

**HOUSEKEEPING:** my git worktree was removed (`git worktree remove --force`) and pruned; the bundle is byte-unmodified (model.py still de3e756f51201829e2b2b637697f628260943a5ccb2a652fb8e1816ce6179fb0, git status clean for the instance dir). All work stayed in 

ADVISORY FOR THE OWNER (does not affect this verdict): meta.json gates.G-EQ, gates.G-PANEL and gates.G-PANEL-1 still carry the pre-repair BROKEN/fail records against the superseded model.py sha bd3a9868..., and meta.json's top-level region_hashes block is stale relative to G-HYGIENE's recorded values (pre-conditions and post-conditions changed when MustTerminate landed; G-PANEL-3 flagged the same staleness). Re-stamping G-EQ at the current sha de3e756f... would clear it.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE: fresh worktree of sphinx-doc_sphinx.git at base_commit 4b452338f914d4f6b54704222d70ae8a746e3db5 with patch.diff APPLIED (), per instructions. Control worktree at base WITHOUT the patch (*) used only to prove my harness discriminates. Env note: the repo needs jinja2<3.1 shims (environmentfilter/pass_environment) to import under the available interpreter; a 4-line alias shim was injected, touching nothing in the call path under test.

### WHAT THE SPEC CLAIMS (build_variable_field_entry, Requires type_role != 0):
  len(Result())==2; Result()[0].is_xref is False and reftype==0; Result()[1].is_xref is True and reftype == rendered_role(type_role, type_target_is_null), where rendered_role(r,n) = NULL_ROLE if (r==TYPE_ROLE and n) else r. Modeled callees: Field.make_xref (node kind by `if not rolename`) and PyTypedField.make_xref's role rewrite (`rolename=='class' and target=='None' -> 'obj'`).

INDEPENDENT DIFFERENTIAL PROBES I WROTE MYSELF (not the bundle's checks), all calling the REAL patched TypedField.make_field / PyTypedField.make_xref on the LIVE 'variable' PyTypedField read out of PyObject.doc_field_types (confirmed rolename=None, typerolename='class', class PyTypedField, so the normalisation override is genuinely in the call path):
  1. g2fa_fuzz.py — 6000 random + ~600 exhaustive entry renderings: live field x 30 identifier type targets (incl. 'None' and the near misses 'NoneType','none','None_','nONE','NONE','NoneT','None.None','.None','~mod.None'); 15 alternate typerolename identities x those targets; live field x 30 identifier NAME targets on both 'int' and 'None' type targets. Result: 0 mismatches on the patched tree.
  2. g2fa_tok.py — 225 token-level probes of the real PyTypedField.make_xref over 15 roles (incl. None, '', 'class ',' class','classs','Class','CLASS') x 15 targets (incl. 'None ',' None'). 0 mismatches. Enumerated the pairs the REAL code normalises: exactly [('class','None')] — matching rendered_role's single-pair rewrite, so the model is neither over- nor under-eager.
  3. g2fa_uniq.py — 12960 token probes over 216 role strings (200 random) x random targets with 'None' forced at 30%. 0 mismatches; real normalising pairs again exactly [('class','None')].
  4. g2fa_shape.py — verified the real paragraph layout is [literal_strong 'attr', ' (', pending_xref reftype='class' 'int', ')', ' -- ', desc], i.e. mapping.md's Result()[0]=child 0, Result()[1]=child 2 bridge is the real layout; and on :vartype: None the reftype really is 'obj'. Matches the F2P test's assert_node shape verbatim.
  5. Real PythonDomain.process_field_xref confirmed to BE Domain.process_field_xref with a `pass` body, so the model's omission of that step (and conformance_check's no-op env stand-in) is exact, not an approximation.

DISCRIMINATION CONTROL (proves the probe is not vacuous): the SAME harness run against the unpatched tree reports 297 mismatches, every one of form name=(True,2) — the real pre-patch name token is an 'obj' pending_xref where the spec demands a plain node. So the probe would have caught an unfaithful name-token clause.

STRENGTH LEG (spec is not too weak either): model_prepatch.py is byte-identical in spec (`adversary same-spec` -> SAME, exit 0) and FAILS Nagini at model_prepatch.py:130 'Assertion (Result()[0].is_xref is False) might not hold'. model.py itself verifies (Verification successful, 16.6s). Bundle's own axiom_check.py exits 0 (3/3 layers) and conformance_check.py exits 0 (100000 inputs, 9638 on the null target, seed 86380, 0 disagreements) against my independently-built patched worktree.

### ATTEMPTED BREAKS THAT DID NOT LAND (and why they are out of domain, not spec drift):
  - Multi-token type targets ('List[int]', 'int or None', 'Optional[None]'): the real make_xrefs splits on the delimiter regex `(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+)`, yielding 8-9 paragraph children instead of 6, so len(Result())==2 does not describe them. Explicitly excluded by mapping.md §G-CONF ('identifier-ish targets, since make_xrefs splits on [](),/or') and by the two-token entry abstraction of §2/A4 — a declared domain restriction stated BEFORE I probed, not a post-hoc excuse, and the F2P test's `:var int attr:` is inside it.
  - Empty name target (''): handle_item is only reached with a truthy fieldarg in the modeled shape; '' yields a 5-child paragraph. Same declared restriction.
  - Delimiter-only type targets ('(', ')', ',', ' or ', '[]'): real code emits a plain literal_emphasis, not a pending_xref, so Result()[1].is_xref is True would fail — but these are pure-delimiter strings the same declared identifier-ish domain excludes; they are not admissible type names in any real docstring. Whitespace-only ('  ', '\t') and the bare word 'or' DO stay a pending_xref under 'class', consistent with the spec.
  - Multi-item / no-type / non-Text-type entries produce a bullet_list or a 3-child paragraph rather than the modeled single collapsed 6-child paragraph — again the declared entry shape (can_collapse single item WITH a type), and each list_item's inner paragraph individually still satisfies the spec's two-token claim.
  - Tried to break rendered_role from both sides: no role string other than exactly 'class' normalises, and no target other than exactly 'None' triggers it, over 13185 real observations. The spec is exactly as strong as the real rewrite.
  - Checked PyXrefMixin.make_xref (the ./~ trimming and refspecific/py:module/py:class attributes) does not alter node KIND or reftype — the only two observables of the §2 bridge — confirmed empirically on '.None' and '~mod.None' targets.

**CONCLUSION:** I found no input inside the declared abstraction domain on which the modeled function disagrees with the real patched repo. The spec states the type-token reference kind THROUGH rendered_role rather than pinning 'class' unconditionally, which is precisely what keeps it faithful on the :vartype: None input where a naive spec would have been too strong. No faithfulness break found.

**REFERENCE:** fresh worktree of sphinx-doc_sphinx.git at base_commit 4b452338f914d4f6b54704222d70ae8a746e3db5 with patch.diff APPLIED (), per instructions. Control worktree at base WITHOUT the patch (*) used only to prove my harness discriminates. Env note: the repo needs jinja2<3.1 shims (environmentfilter/pass_environment) to import under the available interpreter; a 4-line alias shim was injected, touching nothing in the call path under test.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE + PROVENANCE. Judged the consumer-visible projection. Reproduced it two ways in /tmp (bundle byte-unmodified): markers.spec_view(model.py, nagini) and the guarded exposure path eval/dataset.build_task(adapter,'sphinx-doc__sphinx-8638',mode) for modes 1 and 2. All three renders are byte-identical, sha256 f2deee8118ae2261cf2f490e13a9cd389821e9cdffdfa4cdbf92a42baddaa4b6, which matches meta.json gates.G-HYGIENE.data.region_hashes.spec_view; model.py sha256 de3e756f... matches the gates' recorded source. Confirmed via grep of eval/dataset.py + eval/prompts.py that only spec_view (+ problem_statement / localization / modeled_functions) reaches a solver, so refinement.md and mapping.md -- which DO quote the gold hunk verbatim -- are audit-only artifacts and out of scope (they are also on audit.py's our-bundle-access tripwire list).

**NO RELAXATION IN THIS BUNDLE.** There is no meta.json `relaxed_leakage` key (keys: additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version) and no RELAXED_LEAKAGE.md anywhere under the instance directory. So this is a plain full-strength leakage judgement, not an inherited disposition. I also ran leakage.reviewer_directed() over every bundle file (model.py, model_prepatch.py, refinement.md, mapping.md, properties.py, axiom_check.py, conformance_check.py, meta.json, verdict.md, pbt_result.json): all clean -- no artifact addresses this role or tells it what to record. A manual grep for 'you must submit' / 'the honest verdict' / 'record as pass' also returned nothing.

**DECISIVE CONTEXT:** hints_text for this instance is the EMPTY STRING (verified repr('') on the frozen row, and t.hints_text=='' on the built task). The classic leakage mode -- narrating the fix in hints-only vocabulary -- is structurally impossible here; every term in the view came from the PS or from the model's own int-role-code abstraction.

### MECHANICAL CHECKS I RAN (on the frozen row, not eyeballed):
- leakage.screen(model.py, nagini, patch, problem_statement, test_patch): passed=True, hard_failures=[], warnings=[] -- I re-ran the screen myself rather than trusting gates.G-LEAK.
- Gold changed lines (both PyTypedField('variable', ...) forms): whitespace-normalized, ABSENT from the normalized view.
- Diff markers: none. Patched path 'sphinx/domains/python.py' and dotted 'sphinx.domains.python': 0 hits. Patched symbol set = {PyObject} (leakage.`_patch_changed_symbols`): absent from the 25 spec-view identifiers and from all comments/docstrings.
- Edit-literal sweep, case-insensitive, over the whole view: ZERO hits for rolename, typerolename, PyTypedField, PyObject, doc_field_types, docfields, make_field, handle_item, make_xrefs, pending_xref, literal_strong, vartype, ivar, cvar, can_collapse, typenames, label, paramtype, autodoc, apidoc. The only hits for the edit-adjacent words are non-localizing: 'obj' once inside the English 'object-reference role' (line 14), 'variable(s)' in 'instance variables' (line 22, PS vocabulary) and in the model's own function name build_variable_field_entry (line 110), 'sphinx' only in the instance id 'sphinx-doc__sphinx-8638' (line 1, the instance id the solver already has), 'none' only in 'names the null value'.
- Narration: leakage.`_NARRATION_RE` over the view = empty set. Temporal sweep: the sole 'used to' is 'the field type USED TO DOCUMENT attributes' (purpose, not history). The pre-patch literal 'obj' as a role name is unrecoverable from the view.
- Test identity: 0 hits for test_, info_field_list, assert_node, restructuredtext, reftarget, refdomain, attr.
- Impl elided: ELISION_IMPL present in both impl regions; the discriminating literals name_role, FieldNode(True, FieldNode(False, 'par =', 'return par' are all ABSENT from the view.
- `adversary same-spec nagini sphinx-doc__sphinx-8638` on an identity copy: exit 0 (spec region is the one I judged).

LOAD-BEARING TEST (my own measurement, the test named in my brief). I built model_denarrated.py: module docstring replaced by '"""denarrated"""', every function docstring and every non-marker comment stripped, contracts and impl byte-preserved. It VERIFIES (nagini_verify.sh: 'Verification successful', 13.0s). I then swapped only its impl to the pre-patch discriminator (name_role = NULL_ROLE) -> model_denarrated_prepatch.py: 'Verification failed', 'Postcondition of build_variable_field_entry might not hold. Assertion (Result()[0].is_xref is False) might not hold' -- the same failure and the same clause as the bundle's own model_prepatch.py (which I also re-ran: same error at line 130). So ALL discriminating power lives in the Ensures clauses, and NONE in the prose. The narration is therefore not load-bearing, which is the direction that favors the bundle: the prose could be deleted entirely without weakening the spec, so it is not smuggling the edit in as a necessary hint.

STRONGEST ATTACK I COULD BUILD, AND WHY I REJECT IT. Docstring lines 22-26 plus Ensures(Result()[0].is_xref is False) do assert the post-fix outcome: the name token of an attribute/instance-variable entry must be a PLAIN node and must not become a cross-reference. That is the required behaviour, and stating it is a spec's job -- the PS demands it in almost those words: 'That the class variable documentation not be linked to any other', with 'instance variable', 'class variable', 'not be linked', 'autolinking' and 'the user can decide to document it as such with a simple reference' all literally present (I checked each substring against the frozen PS).

The view discloses no file, no repo symbol, no config keyword, no edit direction and no removal framing; a solver reading it learns WHAT must hold (already public) not WHERE or WHICH keyword to delete. The second candidate -- the null-target normalisation clause (a type-reference role whose target names the null value renders under the fallback object role) -- is UNCHANGED repo behaviour preserved so a cheat impl cannot satisfy the spec by dropping the type link or deleting the normalisation (properties.py rivals rival-skip-normalisation / rival-overeager-normalisation). That is spec strength, not the gold edit; and it points AWAY from the edit site (docfields/PyTypedField.make_xref), not at it.

### TWO OBSERVATIONS FOR THE OWNER (neither changes my verdict; both strictly outside the spec_view string I was asked to judge):
1. prompts.py `_spec_block` renders meta.json modeled_functions[].repo_symbol into the mode-1/2 prompt. I printed the built task: that string is "sphinx.util.docfields.TypedField.make_field / handle_item driven by the 'variable' PyTypedField in sphinx.domains.python.PyObject.doc_field_types" -- it names the patched module path, the patched symbol PyObject, and the exact 'variable' PyTypedField config entry, i.e. strictly more localizing than the intentionally-shipped changed_files=['sphinx/domains/python.py']. leakage.screen() only scans spec_view, so this channel is never screened. It is the documented purpose of the model_symbol<->repo_symbol pairing in localization-bearing modes, so I treat it as a platform design property, not a defect of this bundle. (The far more explicit `role` and `repo_location` sub-fields are NOT rendered into the prompt -- localization mode 0 renders repo_location, spec modes do not.)
2. meta.json's TOP-LEVEL region_hashes is stale: its post-conditions (5f182e34...), pre-conditions (6d372f18...) and spec_view (66755a39...) disagree with G-HYGIENE's values, and my freshly computed hashes match G-HYGIENE exactly. Provenance/cosmetic only, but a reader comparing against the top-level block would get a spurious mismatch.

**CORE GATES THE VERDICT LEANS ON:** G-LEAK pass (re-ran the screen myself, clean), G-HYGIENE pass (hash reproduced), G-DIFF pass (reproduced the prepatch rejection myself, and again on my denarrated variant), G-VERIFY (model.py verifies, 13.2s). G-EQ / G-PANEL-1 are recorded 'fail' (a verify-but-not-resolve weakness attack); that is a spec-strength finding for lane 1 and does not bear on leakage -- a spec that is too weak cannot be leaking the edit through the clause it is missing. I did not inherit any prior panel label; verdict.md's earlier all-roles fail/INCONCLUSIVE entries are recorded as agent-launch errors, not spec findings.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
