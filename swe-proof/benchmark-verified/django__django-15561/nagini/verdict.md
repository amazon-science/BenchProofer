# P2 adversarial audit — django__django-15561

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
@@ -65,7 +65,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -153,7 +152,6 @@
 
 def schema_irrelevant_attrs() -> PSet[int]:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The schema-irrelevant set is pinned EXACTLY (set equality, not mere
@@ -179,7 +177,7 @@
     s = PSet(attr_choices(), attr_blank(), attr_db_column(), attr_editable(),
              attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
              attr_on_delete(), attr_related_name(), attr_related_query_name(),
-             attr_validators(), attr_verbose_name())
+             attr_validators())
     return s
     # impl-end
 
@@ -191,7 +189,6 @@
     Requires(Acc(set_pred(non_db), 1 / 2))
     # The listed attributes and their two value vectors are aligned.
     Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(non_db), 1 / 2))
@@ -214,7 +211,6 @@
         Invariant(Forall(int, lambda k: Implies(
             0 <= k and k < i,
             (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
-        Invariant(MustTerminate(len(attrs) - i + 1))
         # invariants-end
         if not (attrs[i] in non_db):
             if old_vals[i] != new_vals[i]:
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -153,7 +152,6 @@
 
 def schema_irrelevant_attrs() -> PSet[int]:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The schema-irrelevant set is pinned EXACTLY (set equality, not mere
@@ -179,7 +177,7 @@
     s = PSet(attr_choices(), attr_blank(), attr_db_column(), attr_editable(),
              attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
              attr_on_delete(), attr_related_name(), attr_related_query_name(),
-             attr_validators(), attr_verbose_name())
+             attr_validators(), attr_verbose_name(), 99)
     return s
     # impl-end
 
@@ -191,7 +189,6 @@
     Requires(Acc(set_pred(non_db), 1 / 2))
     # The listed attributes and their two value vectors are aligned.
     Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(non_db), 1 / 2))
@@ -214,7 +211,6 @@
         Invariant(Forall(int, lambda k: Implies(
             0 <= k and k < i,
             (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
-        Invariant(MustTerminate(len(attrs) - i + 1))
         # invariants-end
         if not (attrs[i] in non_db):
             if old_vals[i] != new_vals[i]:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -153,7 +152,6 @@
 
 def schema_irrelevant_attrs() -> PSet[int]:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The schema-irrelevant set is pinned EXACTLY (set equality, not mere
@@ -191,7 +189,6 @@
     Requires(Acc(set_pred(non_db), 1 / 2))
     # The listed attributes and their two value vectors are aligned.
     Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(non_db), 1 / 2))
@@ -203,22 +200,5 @@
                          or disagrees_relevant(attrs, old_vals, new_vals, non_db)))
     # post-conditions-end
     # impl-start
-    if other_differs:
-        return True
-    i = 0
-    while i < len(attrs):
-        # invariants-start
-        Invariant(Acc(set_pred(non_db), 1 / 2))
-        Invariant(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
-        Invariant(0 <= i and i <= len(attrs))
-        Invariant(Forall(int, lambda k: Implies(
-            0 <= k and k < i,
-            (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
-        Invariant(MustTerminate(len(attrs) - i + 1))
-        # invariants-end
-        if not (attrs[i] in non_db):
-            if old_vals[i] != new_vals[i]:
-                return True
-        i = i + 1
-    return False
+    return other_differs
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -153,7 +152,6 @@
 
 def schema_irrelevant_attrs() -> PSet[int]:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The schema-irrelevant set is pinned EXACTLY (set equality, not mere
@@ -191,7 +189,6 @@
     Requires(Acc(set_pred(non_db), 1 / 2))
     # The listed attributes and their two value vectors are aligned.
     Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(non_db), 1 / 2))
@@ -205,7 +202,7 @@
     # impl-start
     if other_differs:
         return True
-    i = 0
+    i = 1
     while i < len(attrs):
         # invariants-start
         Invariant(Acc(set_pred(non_db), 1 / 2))
@@ -214,7 +211,6 @@
         Invariant(Forall(int, lambda k: Implies(
             0 <= k and k < i,
             (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
-        Invariant(MustTerminate(len(attrs) - i + 1))
         # invariants-end
         if not (attrs[i] in non_db):
             if old_vals[i] != new_vals[i]:
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -153,7 +152,6 @@
 
 def schema_irrelevant_attrs() -> PSet[int]:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The schema-irrelevant set is pinned EXACTLY (set equality, not mere
@@ -191,7 +189,6 @@
     Requires(Acc(set_pred(non_db), 1 / 2))
     # The listed attributes and their two value vectors are aligned.
     Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(non_db), 1 / 2))
@@ -214,9 +211,8 @@
         Invariant(Forall(int, lambda k: Implies(
             0 <= k and k < i,
             (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
-        Invariant(MustTerminate(len(attrs) - i + 1))
         # invariants-end
-        if not (attrs[i] in non_db):
+        if (attrs[i] in non_db):
             if old_vals[i] != new_vals[i]:
                 return True
         i = i + 1
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -153,7 +152,6 @@
 
 def schema_irrelevant_attrs() -> PSet[int]:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The schema-irrelevant set is pinned EXACTLY (set equality, not mere
@@ -191,7 +189,6 @@
     Requires(Acc(set_pred(non_db), 1 / 2))
     # The listed attributes and their two value vectors are aligned.
     Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(non_db), 1 / 2))
@@ -214,10 +211,9 @@
         Invariant(Forall(int, lambda k: Implies(
             0 <= k and k < i,
             (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
-        Invariant(MustTerminate(len(attrs) - i + 1))
         # invariants-end
         if not (attrs[i] in non_db):
-            if old_vals[i] != new_vals[i]:
+            if old_vals[i] == new_vals[i]:
                 return True
         i = i + 1
     return False
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -65,7 +65,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -153,7 +152,6 @@
 
 def schema_irrelevant_attrs() -> PSet[int]:
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The schema-irrelevant set is pinned EXACTLY (set equality, not mere
@@ -176,10 +174,10 @@
     Ensures(attr_choices() in Result())
     # post-conditions-end
     # impl-start
-    s = PSet(attr_choices(), attr_blank(), attr_db_column(), attr_editable(),
-             attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
-             attr_on_delete(), attr_related_name(), attr_related_query_name(),
-             attr_validators(), attr_verbose_name())
+    s = PSet(attr_verbose_name(), attr_validators(), attr_related_query_name(),
+             attr_related_name(), attr_on_delete(), attr_limit_choices_to(),
+             attr_help_text(), attr_error_messages(), attr_editable(),
+             attr_db_column(), attr_blank(), attr_choices())
     return s
     # impl-end
 
@@ -191,7 +189,6 @@
     Requires(Acc(set_pred(non_db), 1 / 2))
     # The listed attributes and their two value vectors are aligned.
     Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(non_db), 1 / 2))
@@ -214,7 +211,6 @@
         Invariant(Forall(int, lambda k: Implies(
             0 <= k and k < i,
             (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
-        Invariant(MustTerminate(len(attrs) - i + 1))
         # invariants-end
         if not (attrs[i] in non_db):
             if old_vals[i] != new_vals[i]:
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15561.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a schema editor is asked to reconcile an existing column definition with
  a proposed one, it must decide whether the underlying table actually needs to
  be rebuilt. Each definition is summarised by its column name plus a bag of
  configuration attributes (an attribute-code together with its value). Some of
  those attributes have NO bearing on the physical column -- presentation,
  validation and relation-management options among them -- so a difference in
  any of THOSE attributes alone must never trigger a rebuild.

  Two facts are pinned here:

    (1) The set of attributes that do not affect a column definition is EXACTLY
        the enumeration-of-permitted-values attribute together with the eleven
        further presentation, validation and relation-management options
        (attr_blank() ... attr_verbose_name()) -- and nothing else. A field
        whose only change is to gain, drop, or alter the enumeration carries an
        identical physical column; it is therefore one of the schema-irrelevant
        attributes and is ignored when deciding whether to rebuild. Every
        attribute OUTSIDE this twelve-element set is schema-relevant: it MUST
        keep participating in the rebuild decision (a larger set would wrongly
        suppress rebuilds on schema-relevant changes).

    (2) The rebuild decision is TRUE exactly when EITHER the non-attribute part
        of the two definitions differs (column name or any other structural
        component), OR the two attribute bags disagree on at least one attribute
        that IS schema-relevant -- i.e. on an attribute OUTSIDE the
        schema-irrelevant set. Disagreement confined entirely to
        schema-irrelevant attributes (the enumeration attribute among them)
        yields FALSE: no rebuild.

  The consequence that matters: altering ONLY the enumeration of permitted values
  on a field, with the column name and every schema-relevant attribute unchanged,
  is a no-op -- the editor issues no table rebuild.

Modelling choices (Nagini fragment):
  * Each attribute is an ``int`` code; the enumeration-of-permitted-values
    attribute is the module-level constant ``attr_choices()``. The eleven
    further schema-irrelevant attribute codes are ``attr_blank()`` ... etc.
  * The schema-irrelevant attribute set is a ``PSet[int]`` of attribute codes,
    produced by ``schema_irrelevant_attrs()`` (the first modelled site); its postcondition
    pins the result EXACTLY: it equals the twelve-element set of the enumeration
    attribute plus the eleven legacy codes (set equality, so neither a subset
    nor a superset is admitted -- an extra member would silently mark a
    schema-RELEVANT attribute as irrelevant and suppress required rebuilds).
  * The two attribute bags to compare are modelled as aligned read-only
    sequences: ``attrs: PSeq[int]`` lists the attribute codes that appear in
    either bag, and ``old_vals`` / ``new_vals`` carry, for each listed attribute,
    the value token on each side. An attribute absent from one side is faithfully
    a value-token mismatch (a distinct absence token), so "membership disagrees"
    and "value disagrees" are the same elementwise test (mapping.md §2). Object
    / value identity is carried by integer equality.
  * The non-attribute structural comparison (column name plus the path / leading
    arguments of the two definitions) is summarised by a single read-only
    ``bool`` parameter ``other_differs``; booleans need no permission.

The compared bags and the schema-irrelevant set are read-only inputs, held at
fractional permission (Required AND Ensured). The whole behaviour is modelled
deeply: ``schema_irrelevant_attrs`` builds the set explicitly, and ``field_alteration_needed``
spells out the "structural difference OR a schema-relevant attribute disagrees"
scan as an existential discharged by a loop. There is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the schema-irrelevant attribute set and the rebuild decision are the
# behaviour under specification and are spelled out deeply in the impl regions.
# There is no unchanged opaque callee whose Ensures the proof consumes.
# axioms-end


# pure-start
@Pure
def attr_choices() -> int:
    # Attribute code for the enumeration of permitted values.
    return 0


@Pure
def attr_blank() -> int:
    return 1


@Pure
def attr_db_column() -> int:
    return 2


@Pure
def attr_editable() -> int:
    return 3


@Pure
def attr_error_messages() -> int:
    return 4


@Pure
def attr_help_text() -> int:
    return 5


@Pure
def attr_limit_choices_to() -> int:
    return 6


@Pure
def attr_on_delete() -> int:
    return 7


@Pure
def attr_related_name() -> int:
    return 8


@Pure
def attr_related_query_name() -> int:
    return 9


@Pure
def attr_validators() -> int:
    return 10


@Pure
def attr_verbose_name() -> int:
    return 11


@Pure
def disagrees_relevant(attrs: PSeq[int], old_vals: PSeq[int], new_vals: PSeq[int],
                       non_db: PSet[int]) -> bool:
    """The two attribute bags disagree on at least one SCHEMA-RELEVANT attribute:
    some listed attribute is OUTSIDE the schema-irrelevant set and yet carries
    different value tokens on the two sides. This is the existential over the
    listed attributes of the per-attribute "relevant and disagreeing" test."""
    Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
    return Exists(int, lambda j: 0 <= j and j < len(attrs)
                  and not (attrs[j] in non_db)
                  and old_vals[j] != new_vals[j])
# pure-end


def schema_irrelevant_attrs() -> PSet[int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The schema-irrelevant set is pinned EXACTLY (set equality, not mere
    # membership): it is the enumeration-of-permitted-values attribute together
    # with the eleven further presentation / validation / relation-management
    # attributes, and NOTHING ELSE. Equality (rather than one-sided membership)
    # is load-bearing in both directions: a set missing the enumeration
    # attribute makes a choices-only change trigger a rebuild (the behaviour
    # the problem statement rules out), and a set with ANY extra member would
    # mark a schema-RELEVANT attribute as irrelevant, silently suppressing
    # required rebuilds.
    Ensures(Result() == PSet(attr_choices(), attr_blank(), attr_db_column(),
                             attr_editable(), attr_error_messages(),
                             attr_help_text(), attr_limit_choices_to(),
                             attr_on_delete(), attr_related_name(),
                             attr_related_query_name(), attr_validators(),
                             attr_verbose_name()))
    # In particular the enumeration-of-permitted-values attribute is a member:
    # a difference confined to it never warrants a rebuild.
    Ensures(attr_choices() in Result())
    # post-conditions-end
    # impl-start
    s = PSet(attr_choices(), attr_blank(), attr_db_column(), attr_editable(),
             attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
             attr_on_delete(), attr_related_name(), attr_related_query_name(),
             attr_validators(), attr_verbose_name())
    return s
    # impl-end


def field_alteration_needed(attrs: PSeq[int], old_vals: PSeq[int],
                            new_vals: PSeq[int], non_db: PSet[int],
                            other_differs: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(non_db), 1 / 2))
    # The listed attributes and their two value vectors are aligned.
    Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(non_db), 1 / 2))
    # A rebuild is needed exactly when the non-attribute structural part differs,
    # OR the bags disagree on some SCHEMA-RELEVANT attribute. Disagreement
    # confined to schema-irrelevant attributes (the enumeration attribute among
    # them, when it is in ``non_db``) yields FALSE.
    Ensures(Result() == (other_differs
                         or disagrees_relevant(attrs, old_vals, new_vals, non_db)))
    # post-conditions-end
    # impl-start
    if other_differs:
        return True
    i = 0
    while i < len(attrs):
        # invariants-start
        Invariant(Acc(set_pred(non_db), 1 / 2))
        Invariant(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
        Invariant(0 <= i and i <= len(attrs))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
        # invariants-end
        if not (attrs[i] in non_db):
            if old_vals[i] != new_vals[i]:
                return True
        i = i + 1
    return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. gold patch lives at benchmark-verified/django__django-15561/patch.diff (one level above nagini/). PATH prepends (has swebench_unified).

BASELINES: positive_control.py (verbatim model.py) VERIFIES (exit 0, 12.2s). prepatch.py (model_prepatch, set built WITHOUT attr_choices()) FAILS verification on 'Postcondition of schema_irrelevant_attrs might not hold' (exit 1) => prepatch bug reproduced (G-DIFF). axiom_check.py (G-AX) exits 0: model set == gold non_db_attrs (12 codes incl. choices, set EQUALITY); field_alteration_needed == gold _field_should_be_altered on 9 boundary + 20000 fuzz pairs; F2P choices-only no-op confirmed both directions.

SPEC TIGHTNESS: both modeled functions have output-pinning postconditions. schema_irrelevant_attrs: Result() == PSet(12 exact codes) (set equality, both directions) + redundant attr_choices() in Result(). field_alteration_needed: Result() == (other_differs or disagrees_relevant(...)) — output fully determined by inputs. No under-determination for a wrong impl to slip through.

atk_1 partial-domain (set): drop attr_verbose_name() -> 11-elt subset. weakness exit 2 (NOT-A-CE). Direct verify: FAIL 'Postcondition of schema_irrelevant_attrs might not hold' (set equality).
- atk_2 boundary/superset: add extra relevant code 99 -> 13-elt superset (would suppress required rebuilds). weakness exit 2. verify FAIL same postcondition (set equality rejects supersets too).
- atk_3 dropped-disjunct (control-flow-effect): field_alteration_needed returns only other_differs, drops relevant-attr scan. weakness exit 2. verify FAIL 'Postcondition of field_alteration_needed might not hold'.
- atk_4 off-by-one control flow: loop start i=1 skipping index 0. weakness exit 2. verify FAIL 'Loop invariant might not hold on entry (i <= len(attrs))'.
- atk_5 membership polarity flip: `attrs[i] in non_db` (relevant/irrelevant swapped). weakness exit 2. verify FAIL 'Postcondition of field_alteration_needed might not hold'.
- atk_6 value-equality polarity flip (ungrounded-oracle echo): return True on old==new instead of !=. weakness exit 2. verify FAIL 'Postcondition of field_alteration_needed might not hold'.
- atk_7 echo/gold-equivalent: reordered 12-elt set + identical loop. weakness exit 0 => CANDIDATE (shares spec AND verifies, 11.5s).

MANDATORY RESOLVE: atk_7 is the only CANDIDATE. Being gold-equivalent (same exact 12-code set, identical decision loop), its faithful refined patch IS the gold patch (benchmark-verified/django__django-15561/patch.diff). Materialized to atk_7_faithful_patch.diff and RAN through official harness via swebench_unified.harness.run_resolve('django__django-15561', patch, timeout=1800, retries=1): RESOLVED=True, COMPLETED=True, NOTE='resolved', FLAKY=False. The verifying candidate's faithful patch RESOLVES => spec is NOT broken by it.

REFINEMENT.MD AUDIT: no @ContractOnly axiom in bundle (axioms-start/end empty by design). All legs are R (A1 str<->int code / tuple<->PSet, B1/B2/B3 dict<->aligned PSeq, quote_name injective), A-reference (A2 exact set equality <-> gold non_db_attrs tuple; B4 disagreement scan <-> residual dict.pop + tuple-!=), or I (B5 Python `or`). No A-consumed, no kind-3 (unexpressible-changed-op). The two A-reference correspondences validated by axiom_check.py/G-AX (exit 0). §C claim (single behavioral delta = choices joining the set, site B a pure R-refactor) holds and is consistent with prepatch reproduction. Correspondence to real callees sound.

VERDICT: SOUND. 6 distinct wrong impls (partial-domain, boundary/superset, dropped-disjunct, off-by-one, membership-flip, value-eq-flip) all rejected by the spec on genuine obligations (postcondition / loop invariant); the sole verifying candidate's materialized faithful patch RESOLVES under the official harness. No verify=>!resolve witness found. verify==>correct upheld for this bundle.

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
"""Twin-artifact model for django__django-15561.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a schema editor is asked to reconcile an existing column definition with
  a proposed one, it must decide whether the underlying table actually needs to
  be rebuilt. Each definition is summarised by its column name plus a bag of
  configuration attributes (an attribute-code together with its value). Some of
  those attributes have NO bearing on the physical column -- presentation,
  validation and relation-management options among them -- so a difference in
  any of THOSE attributes alone must never trigger a rebuild.

  Two facts are pinned here:

    (1) The set of attributes that do not affect a column definition is EXACTLY
        the enumeration-of-permitted-values attribute together with the eleven
        further presentation, validation and relation-management options
        (attr_blank() ... attr_verbose_name()) -- and nothing else. A field
        whose only change is to gain, drop, or alter the enumeration carries an
        identical physical column; it is therefore one of the schema-irrelevant
        attributes and is ignored when deciding whether to rebuild. Every
        attribute OUTSIDE this twelve-element set is schema-relevant: it MUST
        keep participating in the rebuild decision (a larger set would wrongly
        suppress rebuilds on schema-relevant changes).

    (2) The rebuild decision is TRUE exactly when EITHER the non-attribute part
        of the two definitions differs (column name or any other structural
        component), OR the two attribute bags disagree on at least one attribute
        that IS schema-relevant -- i.e. on an attribute OUTSIDE the
        schema-irrelevant set. Disagreement confined entirely to
        schema-irrelevant attributes (the enumeration attribute among them)
        yields FALSE: no rebuild.

  The consequence that matters: altering ONLY the enumeration of permitted values
  on a field, with the column name and every schema-relevant attribute unchanged,
  is a no-op -- the editor issues no table rebuild.

Modelling choices (Nagini fragment):
  * Each attribute is an ``int`` code; the enumeration-of-permitted-values
    attribute is the module-level constant ``attr_choices()``. The eleven
    further schema-irrelevant attribute codes are ``attr_blank()`` ... etc.
  * The schema-irrelevant attribute set is a ``PSet[int]`` of attribute codes,
    produced by ``schema_irrelevant_attrs()`` (the first modelled site); its postcondition
    pins the result EXACTLY: it equals the twelve-element set of the enumeration
    attribute plus the eleven legacy codes (set equality, so neither a subset
    nor a superset is admitted -- an extra member would silently mark a
    schema-RELEVANT attribute as irrelevant and suppress required rebuilds).
  * The two attribute bags to compare are modelled as aligned read-only
    sequences: ``attrs: PSeq[int]`` lists the attribute codes that appear in
    either bag, and ``old_vals`` / ``new_vals`` carry, for each listed attribute,
    the value token on each side. An attribute absent from one side is faithfully
    a value-token mismatch (a distinct absence token), so "membership disagrees"
    and "value disagrees" are the same elementwise test (mapping.md §2). Object
    / value identity is carried by integer equality.
  * The non-attribute structural comparison (column name plus the path / leading
    arguments of the two definitions) is summarised by a single read-only
    ``bool`` parameter ``other_differs``; booleans need no permission.

The compared bags and the schema-irrelevant set are read-only inputs, held at
fractional permission (Required AND Ensured). The whole behaviour is modelled
deeply: ``schema_irrelevant_attrs`` builds the set explicitly, and ``field_alteration_needed``
spells out the "structural difference OR a schema-relevant attribute disagrees"
scan as an existential discharged by a loop. There is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the schema-irrelevant attribute set and the rebuild decision are the
# behaviour under specification and are spelled out deeply in the impl regions.
# There is no unchanged opaque callee whose Ensures the proof consumes.
# axioms-end


# pure-start
@Pure
def attr_choices() -> int:
    # Attribute code for the enumeration of permitted values.
    return 0


@Pure
def attr_blank() -> int:
    return 1


@Pure
def attr_db_column() -> int:
    return 2


@Pure
def attr_editable() -> int:
    return 3


@Pure
def attr_error_messages() -> int:
    return 4


@Pure
def attr_help_text() -> int:
    return 5


@Pure
def attr_limit_choices_to() -> int:
    return 6


@Pure
def attr_on_delete() -> int:
    return 7


@Pure
def attr_related_name() -> int:
    return 8


@Pure
def attr_related_query_name() -> int:
    return 9


@Pure
def attr_validators() -> int:
    return 10


@Pure
def attr_verbose_name() -> int:
    return 11


@Pure
def disagrees_relevant(attrs: PSeq[int], old_vals: PSeq[int], new_vals: PSeq[int],
                       non_db: PSet[int]) -> bool:
    """The two attribute bags disagree on at least one SCHEMA-RELEVANT attribute:
    some listed attribute is OUTSIDE the schema-irrelevant set and yet carries
    different value tokens on the two sides. This is the existential over the
    listed attributes of the per-attribute "relevant and disagreeing" test."""
    Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
    return Exists(int, lambda j: 0 <= j and j < len(attrs)
                  and not (attrs[j] in non_db)
                  and old_vals[j] != new_vals[j])
# pure-end


def schema_irrelevant_attrs() -> PSet[int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The schema-irrelevant set is pinned EXACTLY (set equality, not mere
    # membership): it is the enumeration-of-permitted-values attribute together
    # with the eleven further presentation / validation / relation-management
    # attributes, and NOTHING ELSE. Equality (rather than one-sided membership)
    # is load-bearing in both directions: a set missing the enumeration
    # attribute makes a choices-only change trigger a rebuild (the behaviour
    # the problem statement rules out), and a set with ANY extra member would
    # mark a schema-RELEVANT attribute as irrelevant, silently suppressing
    # required rebuilds.
    Ensures(Result() == PSet(attr_choices(), attr_blank(), attr_db_column(),
                             attr_editable(), attr_error_messages(),
                             attr_help_text(), attr_limit_choices_to(),
                             attr_on_delete(), attr_related_name(),
                             attr_related_query_name(), attr_validators(),
                             attr_verbose_name()))
    # In particular the enumeration-of-permitted-values attribute is a member:
    # a difference confined to it never warrants a rebuild.
    Ensures(attr_choices() in Result())
    # post-conditions-end
    # impl-start
    s = PSet(attr_choices(), attr_blank(), attr_db_column(), attr_editable(),
             attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
             attr_on_delete(), attr_related_name(), attr_related_query_name(),
             attr_validators(), attr_verbose_name())
    return s
    # impl-end


def field_alteration_needed(attrs: PSeq[int], old_vals: PSeq[int],
                            new_vals: PSeq[int], non_db: PSet[int],
                            other_differs: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(non_db), 1 / 2))
    # The listed attributes and their two value vectors are aligned.
    Requires(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(non_db), 1 / 2))
    # A rebuild is needed exactly when the non-attribute structural part differs,
    # OR the bags disagree on some SCHEMA-RELEVANT attribute. Disagreement
    # confined to schema-irrelevant attributes (the enumeration attribute among
    # them, when it is in ``non_db``) yields FALSE.
    Ensures(Result() == (other_differs
                         or disagrees_relevant(attrs, old_vals, new_vals, non_db)))
    # post-conditions-end
    # impl-start
    if other_differs:
        return True
    i = 0
    while i < len(attrs):
        # invariants-start
        Invariant(Acc(set_pred(non_db), 1 / 2))
        Invariant(len(attrs) == len(old_vals) and len(attrs) == len(new_vals))
        Invariant(0 <= i and i <= len(attrs))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (attrs[k] in non_db) or old_vals[k] == new_vals[k])))
        # invariants-end
        if not (attrs[i] in non_db):
            if old_vals[i] != new_vals[i]:
                return True
        i = i + 1
    return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. gold patch lives at benchmark-verified/django__django-15561/patch.diff (one level above nagini/). PATH prepends (has swebench_unified).

BASELINES: positive_control.py (verbatim model.py) VERIFIES (exit 0, 12.2s). prepatch.py (model_prepatch, set built WITHOUT attr_choices()) FAILS verification on 'Postcondition of schema_irrelevant_attrs might not hold' (exit 1) => prepatch bug reproduced (G-DIFF). axiom_check.py (G-AX) exits 0: model set == gold non_db_attrs (12 codes incl. choices, set EQUALITY); field_alteration_needed == gold _field_should_be_altered on 9 boundary + 20000 fuzz pairs; F2P choices-only no-op confirmed both directions.

SPEC TIGHTNESS: both modeled functions have output-pinning postconditions. schema_irrelevant_attrs: Result() == PSet(12 exact codes) (set equality, both directions) + redundant attr_choices() in Result(). field_alteration_needed: Result() == (other_differs or disagrees_relevant(...)) — output fully determined by inputs. No under-determination for a wrong impl to slip through.

atk_1 partial-domain (set): drop attr_verbose_name() -> 11-elt subset. weakness exit 2 (NOT-A-CE). Direct verify: FAIL 'Postcondition of schema_irrelevant_attrs might not hold' (set equality).
- atk_2 boundary/superset: add extra relevant code 99 -> 13-elt superset (would suppress required rebuilds). weakness exit 2. verify FAIL same postcondition (set equality rejects supersets too).
- atk_3 dropped-disjunct (control-flow-effect): field_alteration_needed returns only other_differs, drops relevant-attr scan. weakness exit 2. verify FAIL 'Postcondition of field_alteration_needed might not hold'.
- atk_4 off-by-one control flow: loop start i=1 skipping index 0. weakness exit 2. verify FAIL 'Loop invariant might not hold on entry (i <= len(attrs))'.
- atk_5 membership polarity flip: `attrs[i] in non_db` (relevant/irrelevant swapped). weakness exit 2. verify FAIL 'Postcondition of field_alteration_needed might not hold'.
- atk_6 value-equality polarity flip (ungrounded-oracle echo): return True on old==new instead of !=. weakness exit 2. verify FAIL 'Postcondition of field_alteration_needed might not hold'.
- atk_7 echo/gold-equivalent: reordered 12-elt set + identical loop. weakness exit 0 => CANDIDATE (shares spec AND verifies, 11.5s).

MANDATORY RESOLVE: atk_7 is the only CANDIDATE. Being gold-equivalent (same exact 12-code set, identical decision loop), its faithful refined patch IS the gold patch (benchmark-verified/django__django-15561/patch.diff). Materialized to atk_7_faithful_patch.diff and RAN through official harness via swebench_unified.harness.run_resolve('django__django-15561', patch, timeout=1800, retries=1): RESOLVED=True, COMPLETED=True, NOTE='resolved', FLAKY=False. The verifying candidate's faithful patch RESOLVES => spec is NOT broken by it.

REFINEMENT.MD AUDIT: no @ContractOnly axiom in bundle (axioms-start/end empty by design). All legs are R (A1 str<->int code / tuple<->PSet, B1/B2/B3 dict<->aligned PSeq, quote_name injective), A-reference (A2 exact set equality <-> gold non_db_attrs tuple; B4 disagreement scan <-> residual dict.pop + tuple-!=), or I (B5 Python `or`). No A-consumed, no kind-3 (unexpressible-changed-op). The two A-reference correspondences validated by axiom_check.py/G-AX (exit 0). §C claim (single behavioral delta = choices joining the set, site B a pure R-refactor) holds and is consistent with prepatch reproduction. Correspondence to real callees sound.

VERDICT: SOUND. 6 distinct wrong impls (partial-domain, boundary/superset, dropped-disjunct, off-by-one, membership-flip, value-eq-flip) all rejected by the spec on genuine obligations (postcondition / loop invariant); the sole verifying candidate's materialized faithful patch RESOLVES under the official harness. No verify=>!resolve witness found. verify==>correct upheld for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) assessment for django__django-15561 nagini bundle. The bundle models two gold-changed sites: (1) schema_irrelevant_attrs() -> Field.non_db_attrs (the 12-element tuple: choices + 11 legacy attrs), and (2) field_alteration_needed() -> BaseDatabaseSchemaEditor._field_should_be_altered.

Methodology: built a base_commit worktree, applied the verbatim gold patch (from the SWE-bench dataset test.jsonl, matching meta.patch_diff), and differentially compared the model's contract-stripped impl regions against the REAL patched repo callees.

Results:
- G-AX (axiom_check.py) exit 0: model set == gold non_db_attrs codes (set EQUALITY, exactly 12, choices a member); model decision == gold on 9 boundary + 20000 fuzz pairs.
- G-CONF (conformance_check.py) run against the actually-patched /tmp repo: exit 0, 100015 field pairs (15 boundary + 100000 fuzz, seed 15561), 0 disagreements; shadow schema-irrelevant set == real Field.non_db_attrs.
- Coverage gap I identified: the conformance fuzz KWARG_POOL never exercises the 4 relational non_db attrs (on_delete, related_name, related_query_name, limit_choices_to) because those need relational fields. I independently fuzzed 30000 ForeignKey(User) pairs varying on_delete/related_name/related_query_name/limit_choices_to/db_column/null/db_index plus targeted boundary cases; ALL 12 non_db attrs and schema-relevant attrs match the real repo (0 disagreements).

Abstraction fidelity: the model folds both old_field.non_db_attrs and new_field.non_db_attrs into a single non_db set. This is faithful because only Field defines non_db_attrs in the gold and no field subclass overrides it (grep over django/ finds no override), so both loops strip the same key set. The other_differs bool faithfully summarizes the injective quote_name(column) plus (path, args) tuple comparison; key absence is modeled as a distinct ABSENCE value token, making membership-disagreement and value-disagreement one elementwise test, which the real dict.pop + tuple-!= semantics confirm.

The spec is neither too strong (it does not reject any impl the gold would accept) nor drifted: the modeled functions agree with the real callees on the entire tested input domain, including every non_db attribute and schema-relevant attributes. No diverging input found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Public problem_statement already discloses the target behavior explicitly: 'AlterField operation should be noop when adding/changing choices on SQLite ... adding choices still generates sql ... even though this shouldn't be needed' — i.e. a choices-only field change must not trigger a table rebuild.

Scope of judgment = consumer spec view = spec_view(model.py) (module docstring + @Pure helpers attr_choices()..attr_verbose_name() + disagrees_relevant + the pre/post-conditions of schema_irrelevant_attrs and field_alteration_needed). The impl regions are elided ('... supplied by the consumer') and are NOT part of the spec view.

Mechanical screen: leakage.screen() PASSES (hard_failures=[]); recorded G-LEAK=pass 'spec view clean'; relaxed_leakage flag is None and no RELAXED_LEAKAGE.md — so this is a plain, non-relaxed pass, and my job is the semantic overlay.

Semantic assessment — NO-LEAKAGE:
1. The spec formalizes exactly the publicly-stated behavior (choices/enumeration attribute is schema-irrelevant => no rebuild; disagreement confined to schema-irrelevant attrs yields FALSE). This is the same fact the problem_statement gives publicly, encoded in ABSTRACTED vocabulary (int attribute codes, PSet[int] schema-irrelevant set, PSeq[int] aligned value bags, bool other_differs), phrased as desired behavior rather than as an edit.
2. The spec view never names the real gold symbol `non_db_attrs`, never names the patched files (django/db/backends/base/schema.py, django/db/models/fields/__init__.py), never mentions the two-site refactor (class attribute + re-sourced loop), and never narrates the pre-patch bug (that 'choices' was missing from the legacy list).
3. Spec regions are byte-identical between model.py and model_prepatch.py (confirmed): the spec is invariant across the gold edit, so the discriminating content lives solely in the elided impl region the solver must supply — the spec view does not hand over the edit.
4. The 11 legacy codes attr_blank()..attr_verbose_name() are pre-existing repo context, not the edit; the edit is the addition of the enumeration attribute, which is exactly what the public statement already reveals. Naming the enumeration attribute as schema-irrelevant is REQUIRED to specify the public behavior and does not go beyond problem_statement.
5. Gold-revealing material (verbatim patch, exact non_db_attrs tuple with 'choices', file paths, pre-patch omission) lives only in mapping.md / refinement.md — G-EQ/G-AX auditor artifacts, NOT the consumer spec view.

No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
