# P2 adversarial audit — django__django-15732

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec WRONG impl verifies. The only impl that shares the spec AND verifies is pos_control, which is the exact gold selection algorithm (a resolving gold echo, explicitly NOT a weakness under the resolve-based policy); its faithful refined patch is patch.diff verbatim, which RESOLVES under the official harness. Therefore no verify⇎resolve gap exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AmbiguousConstraintSelection(Exception):
@@ -81,7 +80,6 @@
     # (read-only here: it is inspected, never mutated — fractional permission,
     # directive 5, so no impl can satisfy a postcondition by overwriting it).
     Requires(Acc(list_pred(candidates), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(candidates), 1 / 2))
@@ -124,18 +122,6 @@
                      and (default_name in ToSeq(candidates))))
     # post-conditions-end
     # impl-start
-    # Start from the full discovered set; narrow it when disambiguation applies
-    # and the rule's default name is among the candidates.
-    narrowed_to_default = False
-    if disambiguates(unique, feature_on, len(candidates)):
-        if default_name in ToSeq(candidates):
-            narrowed_to_default = True
-    # After (optional) narrowing, exactly one of the following holds:
-    #   * narrowed_to_default      -> the single name is ``default_name``
-    #   * len(candidates) == 1     -> the single name is ``candidates[0]``
-    # otherwise selection is impossible.
-    if narrowed_to_default:
-        return default_name
     if len(candidates) == 1:
         return candidates[0]
     raise AmbiguousConstraintSelection()
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AmbiguousConstraintSelection(Exception):
@@ -81,7 +80,6 @@
     # (read-only here: it is inspected, never mutated — fractional permission,
     # directive 5, so no impl can satisfy a postcondition by overwriting it).
     Requires(Acc(list_pred(candidates), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(candidates), 1 / 2))
@@ -124,19 +122,7 @@
                      and (default_name in ToSeq(candidates))))
     # post-conditions-end
     # impl-start
-    # Start from the full discovered set; narrow it when disambiguation applies
-    # and the rule's default name is among the candidates.
-    narrowed_to_default = False
-    if disambiguates(unique, feature_on, len(candidates)):
-        if default_name in ToSeq(candidates):
-            narrowed_to_default = True
-    # After (optional) narrowing, exactly one of the following holds:
-    #   * narrowed_to_default      -> the single name is ``default_name``
-    #   * len(candidates) == 1     -> the single name is ``candidates[0]``
-    # otherwise selection is impossible.
-    if narrowed_to_default:
-        return default_name
-    if len(candidates) == 1:
+    if len(candidates) >= 1:
         return candidates[0]
     raise AmbiguousConstraintSelection()
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AmbiguousConstraintSelection(Exception):
@@ -81,7 +80,6 @@
     # (read-only here: it is inspected, never mutated — fractional permission,
     # directive 5, so no impl can satisfy a postcondition by overwriting it).
     Requires(Acc(list_pred(candidates), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(candidates), 1 / 2))
@@ -124,18 +122,9 @@
                      and (default_name in ToSeq(candidates))))
     # post-conditions-end
     # impl-start
-    # Start from the full discovered set; narrow it when disambiguation applies
-    # and the rule's default name is among the candidates.
-    narrowed_to_default = False
     if disambiguates(unique, feature_on, len(candidates)):
         if default_name in ToSeq(candidates):
-            narrowed_to_default = True
-    # After (optional) narrowing, exactly one of the following holds:
-    #   * narrowed_to_default      -> the single name is ``default_name``
-    #   * len(candidates) == 1     -> the single name is ``candidates[0]``
-    # otherwise selection is impossible.
-    if narrowed_to_default:
-        return default_name
+            return candidates[0]
     if len(candidates) == 1:
         return candidates[0]
     raise AmbiguousConstraintSelection()
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AmbiguousConstraintSelection(Exception):
@@ -81,7 +80,6 @@
     # (read-only here: it is inspected, never mutated — fractional permission,
     # directive 5, so no impl can satisfy a postcondition by overwriting it).
     Requires(Acc(list_pred(candidates), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(candidates), 1 / 2))
@@ -124,17 +122,7 @@
                      and (default_name in ToSeq(candidates))))
     # post-conditions-end
     # impl-start
-    # Start from the full discovered set; narrow it when disambiguation applies
-    # and the rule's default name is among the candidates.
-    narrowed_to_default = False
     if disambiguates(unique, feature_on, len(candidates)):
-        if default_name in ToSeq(candidates):
-            narrowed_to_default = True
-    # After (optional) narrowing, exactly one of the following holds:
-    #   * narrowed_to_default      -> the single name is ``default_name``
-    #   * len(candidates) == 1     -> the single name is ``candidates[0]``
-    # otherwise selection is impossible.
-    if narrowed_to_default:
         return default_name
     if len(candidates) == 1:
         return candidates[0]
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AmbiguousConstraintSelection(Exception):
@@ -81,7 +80,6 @@
     # (read-only here: it is inspected, never mutated — fractional permission,
     # directive 5, so no impl can satisfy a postcondition by overwriting it).
     Requires(Acc(list_pred(candidates), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(candidates), 1 / 2))
@@ -124,17 +122,7 @@
                      and (default_name in ToSeq(candidates))))
     # post-conditions-end
     # impl-start
-    # Start from the full discovered set; narrow it when disambiguation applies
-    # and the rule's default name is among the candidates.
-    narrowed_to_default = False
-    if disambiguates(unique, feature_on, len(candidates)):
-        if default_name in ToSeq(candidates):
-            narrowed_to_default = True
-    # After (optional) narrowing, exactly one of the following holds:
-    #   * narrowed_to_default      -> the single name is ``default_name``
-    #   * len(candidates) == 1     -> the single name is ``candidates[0]``
-    # otherwise selection is impossible.
-    if narrowed_to_default:
+    if default_name in ToSeq(candidates):
         return default_name
     if len(candidates) == 1:
         return candidates[0]
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AmbiguousConstraintSelection(Exception):
@@ -81,7 +80,6 @@
     # (read-only here: it is inspected, never mutated — fractional permission,
     # directive 5, so no impl can satisfy a postcondition by overwriting it).
     Requires(Acc(list_pred(candidates), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(candidates), 1 / 2))
@@ -124,19 +122,13 @@
                      and (default_name in ToSeq(candidates))))
     # post-conditions-end
     # impl-start
-    # Start from the full discovered set; narrow it when disambiguation applies
-    # and the rule's default name is among the candidates.
     narrowed_to_default = False
     if disambiguates(unique, feature_on, len(candidates)):
         if default_name in ToSeq(candidates):
             narrowed_to_default = True
-    # After (optional) narrowing, exactly one of the following holds:
-    #   * narrowed_to_default      -> the single name is ``default_name``
-    #   * len(candidates) == 1     -> the single name is ``candidates[0]``
-    # otherwise selection is impossible.
     if narrowed_to_default:
         return default_name
     if len(candidates) == 1:
-        return candidates[0]
+        return default_name
     raise AmbiguousConstraintSelection()
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AmbiguousConstraintSelection(Exception):
@@ -81,7 +80,6 @@
     # (read-only here: it is inspected, never mutated — fractional permission,
     # directive 5, so no impl can satisfy a postcondition by overwriting it).
     Requires(Acc(list_pred(candidates), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(candidates), 1 / 2))
@@ -124,19 +122,7 @@
                      and (default_name in ToSeq(candidates))))
     # post-conditions-end
     # impl-start
-    # Start from the full discovered set; narrow it when disambiguation applies
-    # and the rule's default name is among the candidates.
-    narrowed_to_default = False
-    if disambiguates(unique, feature_on, len(candidates)):
-        if default_name in ToSeq(candidates):
-            narrowed_to_default = True
-    # After (optional) narrowing, exactly one of the following holds:
-    #   * narrowed_to_default      -> the single name is ``default_name``
-    #   * len(candidates) == 1     -> the single name is ``candidates[0]``
-    # otherwise selection is impossible.
-    if narrowed_to_default:
+    if disambiguates(unique, feature_on, len(candidates)) and default_name in ToSeq(candidates):
         return default_name
-    if len(candidates) == 1:
-        return candidates[0]
-    raise AmbiguousConstraintSelection()
+    return candidates[0]
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AmbiguousConstraintSelection(Exception):
@@ -81,7 +80,6 @@
     # (read-only here: it is inspected, never mutated — fractional permission,
     # directive 5, so no impl can satisfy a postcondition by overwriting it).
     Requires(Acc(list_pred(candidates), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(candidates), 1 / 2))
@@ -124,19 +122,11 @@
                      and (default_name in ToSeq(candidates))))
     # post-conditions-end
     # impl-start
-    # Start from the full discovered set; narrow it when disambiguation applies
-    # and the rule's default name is among the candidates.
-    narrowed_to_default = False
-    if disambiguates(unique, feature_on, len(candidates)):
-        if default_name in ToSeq(candidates):
-            narrowed_to_default = True
-    # After (optional) narrowing, exactly one of the following holds:
-    #   * narrowed_to_default      -> the single name is ``default_name``
-    #   * len(candidates) == 1     -> the single name is ``candidates[0]``
-    # otherwise selection is impossible.
-    if narrowed_to_default:
+    if disambiguates(unique, feature_on, len(candidates)) and default_name in ToSeq(candidates):
         return default_name
     if len(candidates) == 1:
         return candidates[0]
+    if len(candidates) >= 1:
+        return candidates[0]
     raise AmbiguousConstraintSelection()
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15732.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composed-uniqueness constraint is being removed from a table. The set of
  candidate constraint names that were discovered on the affected column(s) is
  given, together with the DEFAULT name that the composed-uniqueness rule would
  itself generate for those column(s). Exactly one constraint must be selected
  for removal; if the candidates cannot be reduced to exactly one, selection is
  refused rather than removing an arbitrary constraint.

  The desired selection discipline:

    * If the discovered set already contains exactly one candidate, that
      candidate is the one removed.

    * If the operation is a uniqueness removal AND the backend permits several
      uniqueness constraints to coexist on the same column(s), then a discovered
      set that also contains the rule's own DEFAULT name is disambiguated to
      that default name alone — so the constraint that belongs to the composed
      rule is the one removed, even when an independent single-column uniqueness
      constraint is present on the same column.

    * In every other situation where the discovered set does not reduce to a
      single candidate (no candidate; several candidates none of which is the
      default; or disambiguation is unavailable), selection is impossible and
      the operation fails rather than removing an arbitrary constraint.

  The pinned behaviour is exactly that: the removed name is the rule's default
  whenever disambiguation applies and the default is among the candidates;
  otherwise the sole candidate; and a non-resolvable set raises the
  ambiguous-selection failure and never removes an arbitrary constraint.

Constraint names are modelled as distinct integer identifiers; the discovered
set is a `List[int]` of such identifiers and the rule's default name is one
identifier. The discriminating observable is purely WHICH name is selected (or
that selection fails), not the characters of any name. The ambiguous-selection
failure is a user-defined exception class (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class AmbiguousConstraintSelection(Exception):
    """Signals that the discovered candidate set does not reduce to exactly one
    constraint, so no single constraint can be removed. User-defined stand-in
    for the not-exactly-one-constraint failure the desired behaviour raises; a
    builtin exception in an `Exsures` crashes the Nagini translator (mapping.md
    §2)."""


# axioms-start
# (no callee is axiomatized: the discovery of the candidate set and the
# generation of the rule's default name are UNCHANGED upstream operations whose
# results are passed in as inputs; the changed operation — the disambiguating
# selection over those inputs — is spelled out directly over the modelled
# carrier. There is no unchanged opaque callee whose contract the proof
# consumes inside the changed operation. mapping.md §3.)
# axioms-end


# pure-start
@Pure
def disambiguates(unique: bool, feature_on: bool, n_candidates: int) -> bool:
    """The condition under which a multi-candidate discovered set may be
    narrowed to the rule's own default name: a uniqueness removal, on a backend
    that allows several uniqueness constraints to coexist on the same
    column(s), with at least one candidate discovered."""
    return unique and feature_on and n_candidates >= 1
# pure-end


def select_constraint_to_remove(candidates: List[int], default_name: int,
                                 unique: bool, feature_on: bool) -> int:
    # pre-conditions-start
    # ``candidates`` is the set of constraint names discovered on the column(s)
    # (read-only here: it is inspected, never mutated — fractional permission,
    # directive 5, so no impl can satisfy a postcondition by overwriting it).
    Requires(Acc(list_pred(candidates), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(candidates), 1 / 2))
    # Normal-return domain: a single constraint is returned ONLY when the
    # discovered set actually reduces to exactly one candidate — either because
    # disambiguation applies and the rule's own default name is among the
    # candidates (the set narrows to that one name), or because the set already
    # holds exactly one candidate. In every other situation no normal return is
    # permitted (the operation must refuse rather than remove an arbitrary
    # constraint); this makes the refusal REQUIRED, not merely allowed, closing
    # the silent-arbitrary-selection hole.
    Ensures((disambiguates(unique, feature_on, len(candidates))
             and (default_name in ToSeq(candidates)))
            or (len(candidates) == 1))
    # Disambiguation path: when narrowing applies AND the rule's own default
    # name is among the discovered candidates, the SELECTED name is exactly that
    # default name — and it is a genuine member of the discovered set (it is the
    # candidate that belongs to the composed rule, not an invented value).
    Ensures(Implies(disambiguates(unique, feature_on, len(candidates))
                    and (default_name in ToSeq(candidates)),
                    Result() == default_name))
    Ensures(Implies(disambiguates(unique, feature_on, len(candidates))
                    and (default_name in ToSeq(candidates)),
                    Result() in ToSeq(candidates)))
    # Sole-candidate path: when the discovered set holds exactly one candidate,
    # that candidate is the selected name. (This also covers the unique removal
    # whose single discovered candidate happens to be the default.)
    Ensures(Implies(len(candidates) == 1, Result() == candidates[0]))
    # Whatever is selected is always one of the discovered candidates: a removal
    # never targets a name that was not discovered.
    Ensures(Result() in ToSeq(candidates))
    # The ambiguous-selection failure: when selection cannot reduce the
    # discovered set to a single candidate — i.e. it is NOT the case that there
    # is exactly one candidate, NOR that disambiguation applies with the default
    # among the candidates — the operation raises and removes nothing.
    Exsures(AmbiguousConstraintSelection,
            Acc(list_pred(candidates), 1 / 2)
            and (len(candidates) != 1)
            and not (disambiguates(unique, feature_on, len(candidates))
                     and (default_name in ToSeq(candidates))))
    # post-conditions-end
    # impl-start
    narrowed_to_default = False
    if disambiguates(unique, feature_on, len(candidates)):
        if default_name in ToSeq(candidates):
            narrowed_to_default = True
    if narrowed_to_default:
        return default_name
    if len(candidates) == 1:
        return candidates[0]
    raise AmbiguousConstraintSelection()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: select_constraint_to_remove pins Result() on every allowed normal return (disambig-path+member → default_name; sole-path → candidates[0]; global Result()∈candidates), and the normal-return-domain clause `(disambiguates(...) and default_name∈ToSeq(candidates)) or len(candidates)==1` + the Exsures(AmbiguousConstraintSelection, len!=1 and not(disambiguates and default∈candidates)) jointly REQUIRE a raise in every non-resolvable case — closing the silent-arbitrary-selection hole. Read-only via Acc(list_pred,1/2).

ATTACKS (all copied model.py, edited impl region ONLY; axioms/@Pure/Requires/Ensures/Exsures byte-identical; all confirmed SAME-SPEC exit0):
- atk_1 (prepatch bug / missing disambiguation: only len==1 else raise): cmd `adversary weakness nagini django__django-15732 atk_1.py` → exit2 NOT-A-COUNTEREXAMPLE 'attack does not verify'. Prepatch reproduced ✓ (fails disambig-path Ensures Result()==default_name).
- atk_2 (partial-domain: return candidates[0] whenever ≥1 else raise): exit2, does not verify (violates disambig-path + Exsures).
- atk_3 (boundary: disambig-path returns candidates[0] not default_name): exit2, does not verify.
- atk_4 (control-flow-effect: return default_name whenever disambiguates, ignoring membership — ungrounded): exit2, does not verify (violates Result()∈candidates when default absent).
- atk_5 (ungrounded-oracle echo: return default_name whenever member, no disambig guard): exit2, does not verify.
- atk_6 (sole-path corruption: len==1 returns default_name not candidates[0]): exit2, does not verify.
- atk_7 (silent arbitrary: disambig+member→default else return candidates[0] always): exit2, does not verify.
- atk_8 (issue bug preserved-disambig but silent arbitrary on non-resolvable multi-set): exit2, does not verify (hits normal-return-domain clause + Exsures).
Each output explicitly 'verification failed' (spec rejected), NOT timeout/infra — so none is INCONCLUSIVE.

POSITIVE CONTROL: pos_control.py = exact gold impl → `adversary weakness ... pos_control.py` exit0 CANDIDATE-COUNTEREXAMPLE 'shares spec AND verifies (12.3s)'. Per protocol its faithful refined patch (= gold patch.diff verbatim) was materialized and RUN through run_resolve: `run_resolve('django__django-15732', patch.diff, timeout=1800)` → completed=True, resolved=True, note='resolved'. So the sole verifying candidate RESOLVES → no verify⇎correct gap.

G-AX (A-reference): ran axiom_check.py → exit0, 'deep model == gold selection on 72 boundary + 200000 fuzz, 0 disagreements'. gold_select is a faithful verbatim transcription of patch.diff hunk 2.

REFINEMENT AUDIT: refinement.md legs A1–A10 + hunks 1/3/4 are all R / I / A-reference. Axioms region is empty by design (mapping.md §3: NO consumed @ContractOnly axiom). §C confirms NO kind-3: the one genuinely-changed op (disambiguating selection) is modeled deeply (A5–A9 over the carrier) and validated ==gold by G-AX, not hidden behind an axiom. A-reference correspondence holds (unique-is-True↔typed bool, list-truthiness↔len>=1, narrow-to-[default_name]↔return default_name, constraint_names[0]↔returned name). No A-consumed leg to audit.

VERDICT: SOUND — ≥8 distinct same-spec wrong impls (prepatch + partial-domain + boundary + control-flow-effect + ungrounded-oracle echo + sole-path + silent-arbitrary variants) all fail to verify; the only verifying same-spec impl is the gold echo whose materialized faithful patch RESOLVES. verify⇒correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec WRONG impl verifies. The only impl that shares the spec AND verifies is pos_control, which is the exact gold selection algorithm (a resolving gold echo, explicitly NOT a weakness under the resolve-based policy); its faithful refined patch is patch.diff verbatim, which RESOLVES under the official harness. Therefore no verify⇎resolve gap exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15732.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composed-uniqueness constraint is being removed from a table. The set of
  candidate constraint names that were discovered on the affected column(s) is
  given, together with the DEFAULT name that the composed-uniqueness rule would
  itself generate for those column(s). Exactly one constraint must be selected
  for removal; if the candidates cannot be reduced to exactly one, selection is
  refused rather than removing an arbitrary constraint.

  The desired selection discipline:

    * If the discovered set already contains exactly one candidate, that
      candidate is the one removed.

    * If the operation is a uniqueness removal AND the backend permits several
      uniqueness constraints to coexist on the same column(s), then a discovered
      set that also contains the rule's own DEFAULT name is disambiguated to
      that default name alone — so the constraint that belongs to the composed
      rule is the one removed, even when an independent single-column uniqueness
      constraint is present on the same column.

    * In every other situation where the discovered set does not reduce to a
      single candidate (no candidate; several candidates none of which is the
      default; or disambiguation is unavailable), selection is impossible and
      the operation fails rather than removing an arbitrary constraint.

  The pinned behaviour is exactly that: the removed name is the rule's default
  whenever disambiguation applies and the default is among the candidates;
  otherwise the sole candidate; and a non-resolvable set raises the
  ambiguous-selection failure and never removes an arbitrary constraint.

Constraint names are modelled as distinct integer identifiers; the discovered
set is a `List[int]` of such identifiers and the rule's default name is one
identifier. The discriminating observable is purely WHICH name is selected (or
that selection fails), not the characters of any name. The ambiguous-selection
failure is a user-defined exception class (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class AmbiguousConstraintSelection(Exception):
    """Signals that the discovered candidate set does not reduce to exactly one
    constraint, so no single constraint can be removed. User-defined stand-in
    for the not-exactly-one-constraint failure the desired behaviour raises; a
    builtin exception in an `Exsures` crashes the Nagini translator (mapping.md
    §2)."""


# axioms-start
# (no callee is axiomatized: the discovery of the candidate set and the
# generation of the rule's default name are UNCHANGED upstream operations whose
# results are passed in as inputs; the changed operation — the disambiguating
# selection over those inputs — is spelled out directly over the modelled
# carrier. There is no unchanged opaque callee whose contract the proof
# consumes inside the changed operation. mapping.md §3.)
# axioms-end


# pure-start
@Pure
def disambiguates(unique: bool, feature_on: bool, n_candidates: int) -> bool:
    """The condition under which a multi-candidate discovered set may be
    narrowed to the rule's own default name: a uniqueness removal, on a backend
    that allows several uniqueness constraints to coexist on the same
    column(s), with at least one candidate discovered."""
    return unique and feature_on and n_candidates >= 1
# pure-end


def select_constraint_to_remove(candidates: List[int], default_name: int,
                                 unique: bool, feature_on: bool) -> int:
    # pre-conditions-start
    # ``candidates`` is the set of constraint names discovered on the column(s)
    # (read-only here: it is inspected, never mutated — fractional permission,
    # directive 5, so no impl can satisfy a postcondition by overwriting it).
    Requires(Acc(list_pred(candidates), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(candidates), 1 / 2))
    # Normal-return domain: a single constraint is returned ONLY when the
    # discovered set actually reduces to exactly one candidate — either because
    # disambiguation applies and the rule's own default name is among the
    # candidates (the set narrows to that one name), or because the set already
    # holds exactly one candidate. In every other situation no normal return is
    # permitted (the operation must refuse rather than remove an arbitrary
    # constraint); this makes the refusal REQUIRED, not merely allowed, closing
    # the silent-arbitrary-selection hole.
    Ensures((disambiguates(unique, feature_on, len(candidates))
             and (default_name in ToSeq(candidates)))
            or (len(candidates) == 1))
    # Disambiguation path: when narrowing applies AND the rule's own default
    # name is among the discovered candidates, the SELECTED name is exactly that
    # default name — and it is a genuine member of the discovered set (it is the
    # candidate that belongs to the composed rule, not an invented value).
    Ensures(Implies(disambiguates(unique, feature_on, len(candidates))
                    and (default_name in ToSeq(candidates)),
                    Result() == default_name))
    Ensures(Implies(disambiguates(unique, feature_on, len(candidates))
                    and (default_name in ToSeq(candidates)),
                    Result() in ToSeq(candidates)))
    # Sole-candidate path: when the discovered set holds exactly one candidate,
    # that candidate is the selected name. (This also covers the unique removal
    # whose single discovered candidate happens to be the default.)
    Ensures(Implies(len(candidates) == 1, Result() == candidates[0]))
    # Whatever is selected is always one of the discovered candidates: a removal
    # never targets a name that was not discovered.
    Ensures(Result() in ToSeq(candidates))
    # The ambiguous-selection failure: when selection cannot reduce the
    # discovered set to a single candidate — i.e. it is NOT the case that there
    # is exactly one candidate, NOR that disambiguation applies with the default
    # among the candidates — the operation raises and removes nothing.
    Exsures(AmbiguousConstraintSelection,
            Acc(list_pred(candidates), 1 / 2)
            and (len(candidates) != 1)
            and not (disambiguates(unique, feature_on, len(candidates))
                     and (default_name in ToSeq(candidates))))
    # post-conditions-end
    # impl-start
    narrowed_to_default = False
    if disambiguates(unique, feature_on, len(candidates)):
        if default_name in ToSeq(candidates):
            narrowed_to_default = True
    if narrowed_to_default:
        return default_name
    if len(candidates) == 1:
        return candidates[0]
    raise AmbiguousConstraintSelection()
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: select_constraint_to_remove pins Result() on every allowed normal return (disambig-path+member → default_name; sole-path → candidates[0]; global Result()∈candidates), and the normal-return-domain clause `(disambiguates(...) and default_name∈ToSeq(candidates)) or len(candidates)==1` + the Exsures(AmbiguousConstraintSelection, len!=1 and not(disambiguates and default∈candidates)) jointly REQUIRE a raise in every non-resolvable case — closing the silent-arbitrary-selection hole. Read-only via Acc(list_pred,1/2).

ATTACKS (all copied model.py, edited impl region ONLY; axioms/@Pure/Requires/Ensures/Exsures byte-identical; all confirmed SAME-SPEC exit0):
- atk_1 (prepatch bug / missing disambiguation: only len==1 else raise): cmd `adversary weakness nagini django__django-15732 atk_1.py` → exit2 NOT-A-COUNTEREXAMPLE 'attack does not verify'. Prepatch reproduced ✓ (fails disambig-path Ensures Result()==default_name).
- atk_2 (partial-domain: return candidates[0] whenever ≥1 else raise): exit2, does not verify (violates disambig-path + Exsures).
- atk_3 (boundary: disambig-path returns candidates[0] not default_name): exit2, does not verify.
- atk_4 (control-flow-effect: return default_name whenever disambiguates, ignoring membership — ungrounded): exit2, does not verify (violates Result()∈candidates when default absent).
- atk_5 (ungrounded-oracle echo: return default_name whenever member, no disambig guard): exit2, does not verify.
- atk_6 (sole-path corruption: len==1 returns default_name not candidates[0]): exit2, does not verify.
- atk_7 (silent arbitrary: disambig+member→default else return candidates[0] always): exit2, does not verify.
- atk_8 (issue bug preserved-disambig but silent arbitrary on non-resolvable multi-set): exit2, does not verify (hits normal-return-domain clause + Exsures).
Each output explicitly 'verification failed' (spec rejected), NOT timeout/infra — so none is INCONCLUSIVE.

POSITIVE CONTROL: pos_control.py = exact gold impl → `adversary weakness ... pos_control.py` exit0 CANDIDATE-COUNTEREXAMPLE 'shares spec AND verifies (12.3s)'. Per protocol its faithful refined patch (= gold patch.diff verbatim) was materialized and RUN through run_resolve: `run_resolve('django__django-15732', patch.diff, timeout=1800)` → completed=True, resolved=True, note='resolved'. So the sole verifying candidate RESOLVES → no verify⇎correct gap.

G-AX (A-reference): ran axiom_check.py → exit0, 'deep model == gold selection on 72 boundary + 200000 fuzz, 0 disagreements'. gold_select is a faithful verbatim transcription of patch.diff hunk 2.

REFINEMENT AUDIT: refinement.md legs A1–A10 + hunks 1/3/4 are all R / I / A-reference. Axioms region is empty by design (mapping.md §3: NO consumed @ContractOnly axiom). §C confirms NO kind-3: the one genuinely-changed op (disambiguating selection) is modeled deeply (A5–A9 over the carrier) and validated ==gold by G-AX, not hidden behind an axiom. A-reference correspondence holds (unique-is-True↔typed bool, list-truthiness↔len>=1, narrow-to-[default_name]↔return default_name, constraint_names[0]↔returned name). No A-consumed leg to audit.

VERDICT: SOUND — ≥8 distinct same-spec wrong impls (prepatch + partial-domain + boundary + control-flow-effect + ungrounded-oracle echo + sole-path + silent-arbitrary variants) all fail to verify; the only verifying same-spec impl is the gold echo whose materialized faithful patch RESOLVES. verify⇒correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo) confirmed. Modeled function: the disambiguating constraint-selection block inside BaseDatabaseSchemaEditor._delete_composed_index (django/db/backends/base/schema.py, post-patch worktree @ ce69e34). Checks performed:

1. Nagini verification of the bundle model.py: PASS (exit 0, 12.2s).
2. G-AX A-reference (axiom_check.py): model_select == gold _delete_composed_index selection on 72 boundary + 200000 fuzz inputs, 0 disagreements.
3. INDEPENDENT sweep (I transcribed the REAL repo selection directly from the /tmp worktree, NOT from axiom_check): compared the SPEC's mandated behavior (derived from the Ensures normal-return-domain clause + the disambiguation/sole-candidate value clauses + the Exsures raise condition) against the real repo selection over 500000 randomized (candidates, default_name, unique, feature_on) inputs. 0 divergences.

Key abstractions vetted:
- unique:bool is defined at the modeling boundary as the result of `constraint_kwargs.get("unique") is True` (mapping.md A3), so the real repo's identity-check semantics are captured; conformance_check.py additionally fuzzes truthy-non-True kwargs confirming unique==(kwargs.get('unique') is True). Not a drift source.
- List[int] for list[str] is sound: only name equality/membership/length/[0] are observable in the selection; characters never affect the decision.
- The narrowing (constraint_names=[default_name]) <-> narrowed_to_default flag returning default_name is observationally identical for the subsequent len!=1 check and [0] access.
- The positive normal-return-domain Ensures makes refusal REQUIRED on non-resolvable sets, exactly matching the real repo (which raises ValueError there). The spec neither forbids a behavior the repo exhibits nor mandates one it does not.

Spec region byte-identity was implicitly confirmed by nagini_verify + axiom_check operating on the frozen model; no divergence found. Verdict: FAITHFUL (spec is not too strong and does not drift from real repo behavior).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (not hints_text), on a bundle with NO relaxation in force (meta.relaxed_leakage=None, no RELAXED_LEAKAGE.md), so a leak would be a real fail.

Mechanical G-LEAK screen: PASS (spec view clean, hard_failures=[]). Confirmed directly: (a) no diff markers; (b) no gold-patch changed line reproduced (>=8 normalized chars); (c) patched file path 'django/db/backends/base/schema.py' and its module path absent from the spec view; (d) NO patched repo symbol (_delete_composed_index, _unique_constraint_name, alter_unique_together, allows_multiple_constraints_on_same_fields, constraint_names) appears in any spec-view identifier, comment, or docstring (grep + _patch_changed_symbols screen); (e) no fix/bug/patch/regression narration in comments.

Semantic check beyond the lexical screen: the spec view (docstring + disambiguates helper + pre/post-conditions of select_constraint_to_remove) describes DESIRED behavior over an abstract modeled carrier (candidates:List[int], default_name:int, unique/feature_on bools) — select the composed rule's own default name when several uniqueness constraints coexist on the same column(s) and the default is among the candidates, else the sole candidate, else refuse rather than remove an arbitrary constraint. This is exactly the scenario the PUBLIC problem_statement already lays out (a column carrying two uniqueness constraints — the PK/independent unique and the unique_together's own — where the migration wrongly expects exactly one). Encoding that the correct constraint must be chosen among the candidates is the legitimate, unavoidable content of a behavioral spec; it discloses no edit-localization (which file/function/lines were changed) beyond the public task framing. The 'default_name'/'disambiguates' abstraction reveals the required outcome, not the gold edit.

Conclusion: the spec view does not reconstruct the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
