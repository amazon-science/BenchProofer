# P2 adversarial audit — django__django-14534

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_prepatch.py`, `atk_2_always_none.py`, `atk_3_fab_on_absence.py`, `atk_4_fab_on_presence.py`, `atk_5_offby.py`, `atk_6_swap.py`, `atk_7_nonterm.py`, `atk_8_partial_domain.py`, `atk_10_const_id.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9_correct_variant.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,11 @@
     Ensures(Implies(not (id_key() in ctx.attrs), Result() is None))
     # post-conditions-end
     # impl-start
-    if id_key() in ctx.attrs:
-        return ctx.attrs[id_key()]
-    return None
+    # PRE-PATCH (buggy) skeleton: the reported identifier is fabricated solely
+    # from the choice's name token and its position, ignoring the attribute
+    # mapping entirely (and never reporting absence). This is the reconstruction
+    # the bug performs; it diverges from the recorded identifier whenever a
+    # prefix was configured and invents an identifier when none was recorded.
+    fabricated = ctx.name * 1000 + ctx.index  # type: int
+    return fabricated
     # impl-end
```

Attack 2 — `atk_2_always_none.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,5 @@
     Ensures(Implies(not (id_key() in ctx.attrs), Result() is None))
     # post-conditions-end
     # impl-start
-    if id_key() in ctx.attrs:
-        return ctx.attrs[id_key()]
     return None
     # impl-end
```

Attack 3 — `atk_3_fab_on_absence.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,5 +106,5 @@
     # impl-start
     if id_key() in ctx.attrs:
         return ctx.attrs[id_key()]
-    return None
+    return ctx.index
     # impl-end
```

Attack 4 — `atk_4_fab_on_presence.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,6 +105,6 @@
     # post-conditions-end
     # impl-start
     if id_key() in ctx.attrs:
-        return ctx.attrs[id_key()]
+        return ctx.name * 1000 + ctx.index
     return None
     # impl-end
```

Attack 5 — `atk_5_offby.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,6 +105,6 @@
     # post-conditions-end
     # impl-start
     if id_key() in ctx.attrs:
-        return ctx.attrs[id_key()]
+        return ctx.attrs[id_key()] + 1
     return None
     # impl-end
```

Attack 6 — `atk_6_swap.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,6 +105,6 @@
     # post-conditions-end
     # impl-start
     if id_key() in ctx.attrs:
-        return ctx.attrs[id_key()]
-    return None
+        return None
+    return ctx.name
     # impl-end
```

Attack 7 — `atk_7_nonterm.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,6 @@
     Ensures(Implies(not (id_key() in ctx.attrs), Result() is None))
     # post-conditions-end
     # impl-start
-    if id_key() in ctx.attrs:
-        return ctx.attrs[id_key()]
-    return None
+    while True:
+        pass
     # impl-end
```

Attack 8 — `atk_8_partial_domain.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,7 @@
     Ensures(Implies(not (id_key() in ctx.attrs), Result() is None))
     # post-conditions-end
     # impl-start
-    if id_key() in ctx.attrs:
+    if ctx.index == 0 and id_key() in ctx.attrs:
         return ctx.attrs[id_key()]
     return None
     # impl-end
```

Attack 9 — `atk_9_correct_variant.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -104,7 +104,8 @@
     Ensures(Implies(not (id_key() in ctx.attrs), Result() is None))
     # post-conditions-end
     # impl-start
+    result = None  # type: Optional[int]
     if id_key() in ctx.attrs:
-        return ctx.attrs[id_key()]
-    return None
+        result = ctx.attrs[id_key()]
+    return result
     # impl-end
```

Attack 10 — `atk_10_const_id.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,6 +105,6 @@
     # post-conditions-end
     # impl-start
     if id_key() in ctx.attrs:
-        return ctx.attrs[id_key()]
+        return id_key()
     return None
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14534.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A per-choice subwidget container (one entry produced for each choice of a
  multi-choice form widget) exposes the identifier that a rendered <label>
  should point at. Every such container carries the rendering context that was
  computed for that one choice, which includes the attribute mapping that will
  be placed on the rendered control. When the form was configured to generate
  identifiers, that attribute mapping already holds the *fully-resolved*
  identifier for this choice (the configured prefix applied and the per-choice
  index appended); when the form was configured NOT to generate identifiers,
  the attribute mapping holds no identifier at all.

  The label-target identifier this container reports must be exactly the
  identifier recorded in that attribute mapping:

    * if the attribute mapping records an identifier, the reported value is
      that recorded identifier verbatim (so the configured prefix is honoured);
    * if the attribute mapping records no identifier, the reported value is the
      absent value (None) — no identifier is fabricated from the choice's name
      and position.

  The consequence that matters: the reported identifier never diverges from the
  identifier actually used when rendering the control. A fabricated value built
  only from the choice's name token and position is forbidden, because it
  ignores the configured prefix and invents an identifier where none exists.

Modelling choices (Nagini fragment):
  * Identifiers and name tokens are `int` tokens (opaque identity). The tested
    behaviour only observes WHICH identifier is reported and whether one is
    reported at all, so integer identity is the faithful carrier (mapping.md
    §2). The carrier `None` models the genuine absence of an identifier.
  * The rendering context of a single choice is a minimal class exposing only
    the touched fields: the attribute mapping `attrs` (`Dict[int, int]`, keyed
    by an opaque identifier-key token) plus the choice's `name` token and its
    position `index` (the two values a name/position fabrication would consume).
  * `'id'` (the attribute-mapping key under which the resolved identifier is
    recorded) is a single constant opaque `int` token, returned by `id_key()`.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Optional, Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ChoiceContext:
    def __init__(self, attrs: Dict[int, int], name: int, index: int) -> None:
        Requires(Acc(dict_pred(attrs), 1 / 2))
        Ensures(Acc(self.attrs) and self.attrs is attrs)        # type: ignore
        Ensures(Acc(self.name) and self.name == name)           # type: ignore
        Ensures(Acc(self.index) and self.index == index)        # type: ignore
        Ensures(Acc(dict_pred(attrs), 1 / 2))
        self.attrs = attrs
        self.name = name
        self.index = index


# axioms-start
# No consumed axioms. The reported identifier is the behaviour under
# specification and is modelled deeply (a direct lookup of the recorded
# identifier in the attribute mapping). Ordinary mapping membership/lookup is
# validated against real Python semantics out-of-band by axiom_check.py (G-AX)
# as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def id_key() -> int:
    """The opaque attribute-mapping key under which a resolved identifier is
    recorded (the literal string key 'id' in the repository; an int token
    here)."""
    return 1
# pure-end


def label_target_id(ctx: ChoiceContext) -> Optional[int]:
    # pre-conditions-start
    Requires(Acc(ctx.attrs, 1 / 2))
    Requires(Acc(dict_pred(ctx.attrs), 1 / 2))
    Requires(Acc(ctx.name, 1 / 2))
    Requires(Acc(ctx.index, 1 / 2))
    # The reported identifier must be produced in bounded time: a diverging
    # (never-returning) execution cannot discharge this obligation, so the
    # postconditions below are never satisfied vacuously.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(ctx.attrs, 1 / 2))
    Ensures(Acc(dict_pred(ctx.attrs), 1 / 2))
    Ensures(Acc(ctx.name, 1 / 2))
    Ensures(Acc(ctx.index, 1 / 2))
    # The attribute mapping is left exactly as it was found.
    Ensures(ctx.attrs is Old(ctx.attrs))
    # (1) When the attribute mapping records an identifier, the reported value
    #     is that recorded identifier verbatim.
    Ensures(Implies(id_key() in ctx.attrs, Result() is not None))
    Ensures(Implies(id_key() in ctx.attrs, Result() == ctx.attrs[id_key()]))
    # (2) When the attribute mapping records no identifier, no identifier is
    #     reported.
    Ensures(Implies(not (id_key() in ctx.attrs), Result() is None))
    # post-conditions-end
    # impl-start
    if id_key() in ctx.attrs:
        return ctx.attrs[id_key()]
    return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins Result() uniquely as a total function of input: attrs[id_key()] when id_key() present, None when absent, PLUS read-only discipline (Acc(...,1/2) required+ensured, attrs is Old(attrs)) and Requires(MustTerminate(1)). No same-spec wrong impl verifies.

Protocol executed (project root; env python; SBU_BENCHMARK_DIR=benchmark-verified).

Positive control: `adversary verify nagini django__django-14534 pos_control.py` -> VERIFIED 10.6s.
Prepatch reproduced: atk_1 (fabricated = name*1000+index) -> weakness exit 2 NOT-A-COUNTEREXAMPLE (does not verify) -> spec senses the bug (G-DIFF).

All 10 attacks confirmed SAME-spec via `adversary same-spec` (only impl region edited; axioms/@Pure/Requires/Ensures byte-identical).
- atk_1 prepatch fabrication: REJECTED (exit 2)
- atk_2 always-None (present-branch boundary): REJECTED
- atk_3 fabricate-on-absence (return ctx.index): REJECTED
- atk_4 fabricate-on-presence (name*1000+index, ignore recorded id, ungrounded-oracle echo): REJECTED
- atk_5 off-by (+1 on recorded id, boundary value): REJECTED
- atk_6 swap present/absent branches (control-flow): REJECTED
- atk_7 non-termination (while True: pass) -> MustTerminate(1) obligation leak REJECTED (can't discharge Ensures vacuously)
- atk_8 partial-domain (correct only when index==0): REJECTED
- atk_9 correct-variant echo (result=None; if id_key() in attrs: result=attrs[id_key()]; return result): CANDIDATE (weakness exit 0 — same-spec AND verifies)
- atk_10 const-id (return id_key() when present): REJECTED

MANDATORY resolve for the one verifying candidate (atk_9): materialized faithful refined patch patch_atk_9.diff (translates atk_9's impl-region result-var form back to boundfield.py:id_for_label) and ran through the official harness `swebench_unified.harness.run_resolve('django__django-14534', ...)`: RESOLVED=True, COMPLETED=True, note='resolved'. FAIL_TO_PASS both pass (test_iterable_boundfield_select + auto_id id-generation test); all ~115 PASS_TO_PASS pass, 0 failures. So atk_9 is a CORRECT echo (verify=>correct holds), NOT a spec weakness — per current G-EQ/G-PANEL-1 policy a resolving same-spec candidate is not a break.

A-reference audit: axiom_check.py exit 0 (deep model == real id_for_label = attrs.get('id') on 7 boundary + 50000 fuzz inputs; real-Django path skipped host-side, exercised in eval container). refinement.md legs A1(R) A2(R+I, dict membership/lookup is A-reference validated by axiom_check, not consumed) A3(R) A4(I); Section B: no consumed @ContractOnly axioms; Section C: no kind-3 (unexpressible-changed-op) steps — every leg is R / A-reference / I. mapping.md binds label_target_id<->BoundWidget.id_for_label, id_key()<->'id', attrs<->self.data['attrs']; correspondence holds against gold patch (self.data['attrs'].get('id')).

No verifying wrong impl exists; the sole verifying candidate's faithful patch resolves. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_prepatch.py`, `atk_2_always_none.py`, `atk_3_fab_on_absence.py`, `atk_4_fab_on_presence.py`, `atk_5_offby.py`, `atk_6_swap.py`, `atk_7_nonterm.py`, `atk_8_partial_domain.py`, `atk_10_const_id.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9_correct_variant.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_always_none.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_fab_on_absence.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_fab_on_presence.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_offby.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_swap.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_nonterm.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_partial_domain.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_correct_variant.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_const_id.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14534.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A per-choice subwidget container (one entry produced for each choice of a
  multi-choice form widget) exposes the identifier that a rendered <label>
  should point at. Every such container carries the rendering context that was
  computed for that one choice, which includes the attribute mapping that will
  be placed on the rendered control. When the form was configured to generate
  identifiers, that attribute mapping already holds the *fully-resolved*
  identifier for this choice (the configured prefix applied and the per-choice
  index appended); when the form was configured NOT to generate identifiers,
  the attribute mapping holds no identifier at all.

  The label-target identifier this container reports must be exactly the
  identifier recorded in that attribute mapping:

    * if the attribute mapping records an identifier, the reported value is
      that recorded identifier verbatim (so the configured prefix is honoured);
    * if the attribute mapping records no identifier, the reported value is the
      absent value (None) — no identifier is fabricated from the choice's name
      and position.

  The consequence that matters: the reported identifier never diverges from the
  identifier actually used when rendering the control. A fabricated value built
  only from the choice's name token and position is forbidden, because it
  ignores the configured prefix and invents an identifier where none exists.

Modelling choices (Nagini fragment):
  * Identifiers and name tokens are `int` tokens (opaque identity). The tested
    behaviour only observes WHICH identifier is reported and whether one is
    reported at all, so integer identity is the faithful carrier (mapping.md
    §2). The carrier `None` models the genuine absence of an identifier.
  * The rendering context of a single choice is a minimal class exposing only
    the touched fields: the attribute mapping `attrs` (`Dict[int, int]`, keyed
    by an opaque identifier-key token) plus the choice's `name` token and its
    position `index` (the two values a name/position fabrication would consume).
  * `'id'` (the attribute-mapping key under which the resolved identifier is
    recorded) is a single constant opaque `int` token, returned by `id_key()`.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Optional, Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ChoiceContext:
    def __init__(self, attrs: Dict[int, int], name: int, index: int) -> None:
        Requires(Acc(dict_pred(attrs), 1 / 2))
        Ensures(Acc(self.attrs) and self.attrs is attrs)        # type: ignore
        Ensures(Acc(self.name) and self.name == name)           # type: ignore
        Ensures(Acc(self.index) and self.index == index)        # type: ignore
        Ensures(Acc(dict_pred(attrs), 1 / 2))
        self.attrs = attrs
        self.name = name
        self.index = index


# axioms-start
# No consumed axioms. The reported identifier is the behaviour under
# specification and is modelled deeply (a direct lookup of the recorded
# identifier in the attribute mapping). Ordinary mapping membership/lookup is
# validated against real Python semantics out-of-band by axiom_check.py (G-AX)
# as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def id_key() -> int:
    """The opaque attribute-mapping key under which a resolved identifier is
    recorded (the literal string key 'id' in the repository; an int token
    here)."""
    return 1
# pure-end


def label_target_id(ctx: ChoiceContext) -> Optional[int]:
    # pre-conditions-start
    Requires(Acc(ctx.attrs, 1 / 2))
    Requires(Acc(dict_pred(ctx.attrs), 1 / 2))
    Requires(Acc(ctx.name, 1 / 2))
    Requires(Acc(ctx.index, 1 / 2))
    # The reported identifier must be produced in bounded time: a diverging
    # (never-returning) execution cannot discharge this obligation, so the
    # postconditions below are never satisfied vacuously.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(ctx.attrs, 1 / 2))
    Ensures(Acc(dict_pred(ctx.attrs), 1 / 2))
    Ensures(Acc(ctx.name, 1 / 2))
    Ensures(Acc(ctx.index, 1 / 2))
    # The attribute mapping is left exactly as it was found.
    Ensures(ctx.attrs is Old(ctx.attrs))
    # (1) When the attribute mapping records an identifier, the reported value
    #     is that recorded identifier verbatim.
    Ensures(Implies(id_key() in ctx.attrs, Result() is not None))
    Ensures(Implies(id_key() in ctx.attrs, Result() == ctx.attrs[id_key()]))
    # (2) When the attribute mapping records no identifier, no identifier is
    #     reported.
    Ensures(Implies(not (id_key() in ctx.attrs), Result() is None))
    # post-conditions-end
    # impl-start
    if id_key() in ctx.attrs:
        return ctx.attrs[id_key()]
    return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec pins Result() uniquely as a total function of input: attrs[id_key()] when id_key() present, None when absent, PLUS read-only discipline (Acc(...,1/2) required+ensured, attrs is Old(attrs)) and Requires(MustTerminate(1)). No same-spec wrong impl verifies.

Protocol executed (project root; env python; SBU_BENCHMARK_DIR=benchmark-verified).

Positive control: `adversary verify nagini django__django-14534 pos_control.py` -> VERIFIED 10.6s.
Prepatch reproduced: atk_1 (fabricated = name*1000+index) -> weakness exit 2 NOT-A-COUNTEREXAMPLE (does not verify) -> spec senses the bug (G-DIFF).

All 10 attacks confirmed SAME-spec via `adversary same-spec` (only impl region edited; axioms/@Pure/Requires/Ensures byte-identical).
- atk_1 prepatch fabrication: REJECTED (exit 2)
- atk_2 always-None (present-branch boundary): REJECTED
- atk_3 fabricate-on-absence (return ctx.index): REJECTED
- atk_4 fabricate-on-presence (name*1000+index, ignore recorded id, ungrounded-oracle echo): REJECTED
- atk_5 off-by (+1 on recorded id, boundary value): REJECTED
- atk_6 swap present/absent branches (control-flow): REJECTED
- atk_7 non-termination (while True: pass) -> MustTerminate(1) obligation leak REJECTED (can't discharge Ensures vacuously)
- atk_8 partial-domain (correct only when index==0): REJECTED
- atk_9 correct-variant echo (result=None; if id_key() in attrs: result=attrs[id_key()]; return result): CANDIDATE (weakness exit 0 — same-spec AND verifies)
- atk_10 const-id (return id_key() when present): REJECTED

MANDATORY resolve for the one verifying candidate (atk_9): materialized faithful refined patch patch_atk_9.diff (translates atk_9's impl-region result-var form back to boundfield.py:id_for_label) and ran through the official harness `swebench_unified.harness.run_resolve('django__django-14534', ...)`: RESOLVED=True, COMPLETED=True, note='resolved'. FAIL_TO_PASS both pass (test_iterable_boundfield_select + auto_id id-generation test); all ~115 PASS_TO_PASS pass, 0 failures. So atk_9 is a CORRECT echo (verify=>correct holds), NOT a spec weakness — per current G-EQ/G-PANEL-1 policy a resolving same-spec candidate is not a break.

A-reference audit: axiom_check.py exit 0 (deep model == real id_for_label = attrs.get('id') on 7 boundary + 50000 fuzz inputs; real-Django path skipped host-side, exercised in eval container). refinement.md legs A1(R) A2(R+I, dict membership/lookup is A-reference validated by axiom_check, not consumed) A3(R) A4(I); Section B: no consumed @ContractOnly axioms; Section C: no kind-3 (unexpressible-changed-op) steps — every leg is R / A-reference / I. mapping.md binds label_target_id<->BoundWidget.id_for_label, id_key()<->'id', attrs<->self.data['attrs']; correspondence holds against gold patch (self.data['attrs'].get('id')).

No verifying wrong impl exists; the sole verifying candidate's faithful patch resolves. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical to bundle (same-spec on an identical copy -> exit 0); bundle model verifies (nagini_verify.sh, 10.4s). Real callee post-patch is BoundWidget.id_for_label = self.data['attrs'].get('id') (confirmed in boundfield.py:279-280 @ base_commit 910ecd1b). Spec clauses: (1) id_key() in attrs => Result() is not None and Result()==attrs[id_key()]; (2) id_key() not in attrs => Result() is None.

Empirically drove the real Django subwidget data path for the three pinned form configs plus fuzz: auto_id='prefix_%s'/CheckboxSelectMultiple, auto_id='id_%s'/RadioSelect, auto_id=False/Select, choice-count varied. For EVERY real subwidget, id_for_label == attrs.get('id') and clause (1) held (present-key => non-None). Model and real callee agree on every representable/tested input.

Examined the one boundary where the real .get('id') could return None for a PRESENT key: a falsy recorded id. It is reachable in the raw repo only via a synthetic widget attrs={'id': None} under auto_id=False, e.g. CheckboxSelectMultiple(attrs={'id': None}) -> create_option leaves option_attrs['id']=None -> real id_for_label returns None with 'id' still in attrs. Spec clause (1) would forbid that (present => non-None). BUT this is NOT a faithfulness break: (a) the model carrier is Dict[int,int] (values are non-None int tokens), so 'present key -> None' lies OUTSIDE the modeled domain / bijection image (mapping.md 2 maps a present 'id' to a fully-resolved id str <-> int token; genuine absence <-> the carrier None). Within the modeled domain every representable input maps to a real attrs whose 'id' value is a real resolved id str, and model == real callee there. (b) No F2P/P2P test exercises a falsy-but-present id; even the gold patch returns None there, so it does not affect the resolve verdict. The domain restriction is deliberate and sound, not a disagreement on a representable input. No diverging representable input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures): no diff markers, patched file path (django/forms/boundfield.py) absent, patched symbols (id_for_label, template_name) not embedded in any spec-view identifier or comment, no narration terms (bug/fix/patch/etc.), and the impl region is elided ('...  # implementation elided'). Gold changed lines ("return 'id_%s_%s' % (self.data['name'], self.data['index'])" and "return self.data['attrs'].get('id')") are not reproduced in the spec view.

Semantic assessment: leakage is judged relative to the PUBLIC problem_statement only. Here the problem_statement is maximally explicit and itself discloses the entire gold edit — it shows the buggy body verbatim, explains that widget['attrs']['id'] holds the id to use, and gives the exact fix ('By changing the code ... to return self.data[\'attrs\'][\'id\'] that function behaves as expected'). The spec view (report exactly the identifier recorded in ctx.attrs; None if absent; a name/index fabrication is forbidden) is a faithful behavioral abstraction that does NOT go beyond the already-fix-disclosing public issue. The 'configured prefix / auto_id' framing likewise mirrors the problem_statement's overridden auto_id discussion. Nothing in the spec view reveals the gold edit beyond problem_statement. Nagini impl properly elided; spec/pure/mapping content carries no gold-localizing detail absent from the public issue.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
