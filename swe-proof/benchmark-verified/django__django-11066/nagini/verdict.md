# P2 adversarial audit — django__django-11066

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,8 @@
     Ensures(alias_eq(ToSeq(Result()), ToSeq(db)))
     # post-conditions-end
     # impl-start
-    # using = explicit_alias or routing_policy_choice
-    # An explicit alias is supplied (== db), so it is used directly; the
-    # routing-policy fallback is reached only when no explicit alias is given.
-    src = db if len(db) > 0 else routed  # type: List[int]
-    # Copy the chosen alias into a fresh result carrier.
+    # PRE-PATCH BUG: no explicit alias, resolution falls to routing policy.
+    src = routed  # type: List[int]
     target = []  # type: List[int]
     i = 0
     while i < len(src):
@@ -74,7 +71,7 @@
         Invariant(Acc(list_pred(routed), 1 / 2))
         Invariant(Acc(list_pred(target)))
         Invariant(len(db) > 0)
-        Invariant(ToSeq(src) == ToSeq(db))
+        Invariant(ToSeq(src) == ToSeq(routed))
         Invariant(0 <= i and i <= len(src))
         Invariant(ToSeq(target) == ToSeq(src).take(i))
         # invariants-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,8 @@
     Ensures(alias_eq(ToSeq(Result()), ToSeq(db)))
     # post-conditions-end
     # impl-start
-    # using = explicit_alias or routing_policy_choice
-    # An explicit alias is supplied (== db), so it is used directly; the
-    # routing-policy fallback is reached only when no explicit alias is given.
-    src = db if len(db) > 0 else routed  # type: List[int]
-    # Copy the chosen alias into a fresh result carrier.
+    # PARTIAL DOMAIN: only honor explicit alias on 'long' aliases; else route.
+    src = db if len(db) > 5 else routed  # type: List[int]
     target = []  # type: List[int]
     i = 0
     while i < len(src):
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -61,14 +61,11 @@
     Ensures(alias_eq(ToSeq(Result()), ToSeq(db)))
     # post-conditions-end
     # impl-start
-    # using = explicit_alias or routing_policy_choice
-    # An explicit alias is supplied (== db), so it is used directly; the
-    # routing-policy fallback is reached only when no explicit alias is given.
-    src = db if len(db) > 0 else routed  # type: List[int]
-    # Copy the chosen alias into a fresh result carrier.
+    # BOUNDARY off-by-one: drop the last code point of db.
+    src = db  # type: List[int]
     target = []  # type: List[int]
     i = 0
-    while i < len(src):
+    while i < len(src) - 1:
         # invariants-start
         Invariant(Acc(list_pred(db), 1 / 2))
         Invariant(Acc(list_pred(routed), 1 / 2))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -61,25 +61,7 @@
     Ensures(alias_eq(ToSeq(Result()), ToSeq(db)))
     # post-conditions-end
     # impl-start
-    # using = explicit_alias or routing_policy_choice
-    # An explicit alias is supplied (== db), so it is used directly; the
-    # routing-policy fallback is reached only when no explicit alias is given.
-    src = db if len(db) > 0 else routed  # type: List[int]
-    # Copy the chosen alias into a fresh result carrier.
+    # CONTROL-FLOW: never enter the copy loop; return empty carrier.
     target = []  # type: List[int]
-    i = 0
-    while i < len(src):
-        # invariants-start
-        Invariant(Acc(list_pred(db), 1 / 2))
-        Invariant(Acc(list_pred(routed), 1 / 2))
-        Invariant(Acc(list_pred(target)))
-        Invariant(len(db) > 0)
-        Invariant(ToSeq(src) == ToSeq(db))
-        Invariant(0 <= i and i <= len(src))
-        Invariant(ToSeq(target) == ToSeq(src).take(i))
-        # invariants-end
-        target = target + [src[i]]
-        Assert(ToSeq(src).take(i) + PSeq(src[i]) == ToSeq(src).take(i + 1))
-        i = i + 1
     return target
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -61,25 +61,6 @@
     Ensures(alias_eq(ToSeq(Result()), ToSeq(db)))
     # post-conditions-end
     # impl-start
-    # using = explicit_alias or routing_policy_choice
-    # An explicit alias is supplied (== db), so it is used directly; the
-    # routing-policy fallback is reached only when no explicit alias is given.
-    src = db if len(db) > 0 else routed  # type: List[int]
-    # Copy the chosen alias into a fresh result carrier.
-    target = []  # type: List[int]
-    i = 0
-    while i < len(src):
-        # invariants-start
-        Invariant(Acc(list_pred(db), 1 / 2))
-        Invariant(Acc(list_pred(routed), 1 / 2))
-        Invariant(Acc(list_pred(target)))
-        Invariant(len(db) > 0)
-        Invariant(ToSeq(src) == ToSeq(db))
-        Invariant(0 <= i and i <= len(src))
-        Invariant(ToSeq(target) == ToSeq(src).take(i))
-        # invariants-end
-        target = target + [src[i]]
-        Assert(ToSeq(src).take(i) + PSeq(src[i]) == ToSeq(src).take(i + 1))
-        i = i + 1
-    return target
+    # UNGROUNDED ORACLE ECHO: alias the input db object as the result.
+    return db
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,8 @@
     Ensures(alias_eq(ToSeq(Result()), ToSeq(db)))
     # post-conditions-end
     # impl-start
-    # using = explicit_alias or routing_policy_choice
-    # An explicit alias is supplied (== db), so it is used directly; the
-    # routing-policy fallback is reached only when no explicit alias is given.
-    src = db if len(db) > 0 else routed  # type: List[int]
-    # Copy the chosen alias into a fresh result carrier.
+    # WRONG BRANCH: pick routed on even-length db, db on odd-length.
+    src = db if (len(db) % 2 == 1) else routed  # type: List[int]
     target = []  # type: List[int]
     i = 0
     while i < len(src):
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,8 @@
     Ensures(alias_eq(ToSeq(Result()), ToSeq(db)))
     # post-conditions-end
     # impl-start
-    # using = explicit_alias or routing_policy_choice
-    # An explicit alias is supplied (== db), so it is used directly; the
-    # routing-policy fallback is reached only when no explicit alias is given.
-    src = db if len(db) > 0 else routed  # type: List[int]
-    # Copy the chosen alias into a fresh result carrier.
+    # BOUNDARY over-copy: copy db then append an extra code point.
+    src = db  # type: List[int]
     target = []  # type: List[int]
     i = 0
     while i < len(src):
@@ -81,5 +78,6 @@
         target = target + [src[i]]
         Assert(ToSeq(src).take(i) + PSeq(src[i]) == ToSeq(src).take(i + 1))
         i = i + 1
+    target = target + [0]
     return target
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11066.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A persistence step is given two things: an explicitly named target data
  store (an alias that is always present) and the alias that an external
  write-routing policy would otherwise select. The persisted-to data store
  must be the EXPLICITLY NAMED one, so that the write lands in the store the
  caller named rather than wherever an independent routing policy would send
  it. The routing policy is consulted only as a fallback, when no explicit
  store is named at all.

  Concretely: the resolved target is the explicit alias when one is present
  (which it always is here), and equals it regardless of which alias the
  routing policy would have chosen — even when the policy would pick a
  different store.

Connection aliases are modelled as `List[int]` of Unicode code points (Nagini
bans `str` indexing); equality of two aliases is `PSeq[int]` equality. The
routing policy's choice is modelled as a free input alias, because the policy
is wholly independent of the explicitly named store and may select any alias.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the resolution is modelled deeply; the routing policy's choice is a
# free input alias `routed`, an A-reference validated by axiom_check.py, not a
# consumed @ContractOnly. See refinement.md / mapping.md §3.)
# axioms-end


# pure-start
@Pure
def alias_eq(a: PSeq[int], b: PSeq[int]) -> bool:
    """Two connection aliases denote the same data store iff their code-point
    sequences are equal."""
    return a == b
# pure-end


def persisted_db(db: List[int], routed: List[int]) -> List[int]:
    # pre-conditions-start
    # `db` is the explicitly named target alias and is always present
    # (non-empty); `routed` is the alias the external routing policy would
    # otherwise pick — an arbitrary present alias, read-only here.
    Requires(Acc(list_pred(db), 1 / 2))
    Requires(Acc(list_pred(routed), 1 / 2))
    Requires(len(db) > 0)
    Requires(len(routed) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(db), 1 / 2))
    Ensures(Acc(list_pred(routed), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The write is committed to the EXPLICITLY NAMED store — its alias equals
    # `db` — no matter what the routing policy would have chosen.
    Ensures(alias_eq(ToSeq(Result()), ToSeq(db)))
    # post-conditions-end
    # impl-start
    # using = explicit_alias or routing_policy_choice
    # An explicit alias is supplied (== db), so it is used directly; the
    # routing-policy fallback is reached only when no explicit alias is given.
    src = db if len(db) > 0 else routed  # type: List[int]
    # Copy the chosen alias into a fresh result carrier.
    target = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(db), 1 / 2))
        Invariant(Acc(list_pred(routed), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(len(db) > 0)
        Invariant(ToSeq(src) == ToSeq(db))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(target) == ToSeq(src).take(i))
        # invariants-end
        target = target + [src[i]]
        Assert(ToSeq(src).take(i) + PSeq(src[i]) == ToSeq(src).take(i + 1))
        i = i + 1
    return target
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC:** persisted_db(db, routed) must return an alias whose PSeq equals db's, regardless of the free `routed` input. The postcondition alias_eq(ToSeq(Result()), ToSeq(db)) FULLY pins the output sequence to db; combined with Ensures(Acc(list_pred(Result()))) at FULL permission (result must be a fresh carrier) and the inputs held at only Acc(...,1/2), the spec is tight and hard to satisfy incorrectly.

 Correct interpreter is python (repo root). 7 DISTINCT wrong impls, each edits ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; confirmed same-spec exit 0 for all 7 via `python -m swebench_unified.adversary same-spec nagini django__django-11066 <f>`).

ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini django__django-11066 <f>`; ran concurrently ≤3 at a time as background jobs):
- atk_1 PRE-PATCH BUG (src=routed): weakness EXIT=2 NOT-A-COUNTEREXAMPLE (does not verify). This is the prepatch reproduction.
- atk_2 partial-domain (src = db if len(db)>5 else routed): EXIT=2 rejected.
- atk_3 boundary off-by-one (copy db[:-1], loop to len(src)-1): EXIT=2 rejected.
- atk_4 control-flow-effect (skip loop, return empty carrier): EXIT=2 rejected.
- atk_5 ungrounded-oracle echo (return db input object directly): EXIT=2 rejected — blocked by Ensures(Acc(list_pred(Result()))) full-permission requirement (result must be fresh, cannot alias the 1/2-held input).
- atk_6 wrong-branch (src = db on odd len(db) else routed): EXIT=2 rejected.
- atk_7 boundary over-copy (copy db then append sentinel 0): EXIT=2 rejected.
NO attack returned CANDIDATE (exit 0). Hence NO faithful patch to materialize; run_resolve step is vacuous — nothing to break the spec.

**POSITIVE CONTROL:** positive_control.py = bundle model.py verbatim → `bash scripts/nagini_verify.sh` EXIT=0 'Verification successful' (13.36s).
PREPATCH: model_prepatch.py verbatim → EXIT=1, error at prepatch.py:61 'Postcondition of persisted_db might not hold. Assertion alias_eq(ToSeq(Result()), ToSeq(db)) might not hold' — G-DIFF sound, spec senses the change at exactly the postcondition line. prepatch_reproduced=true.

A-LEG AUDIT (refinement.md): bundle has NO consumed @ContractOnly axiom; the single axioms block is a comment. The one callee router.db_for_write is UNCHANGED and BYPASSED by the fix, modelled as free input `routed` = A-reference (leg A2). All legs classified R / A-reference / I — NO kind-3 (unexpressible-changed-op). The discriminating op (which alias resolves as write target) is modelled DEEPLY via A3 ternary (src = db if len(db)>0 else routed), not hidden behind an axiom.

G-AX (A-reference soundness): copied bundle axiom_check.py (byte-identical, confirmed via diff -q) and ran against REAL Django at base_commit 4b45b6c8e4d7c9701a332e80d3b1c84209dc36e2 (git worktree from repos_cache/django__django, PYTHONPATH set): EXIT=0 'G-AX OK ... over 5 boundary + 5000 fuzz alias pairs'. Both reference properties hold against real ConnectionRouter.db_for_write and the real `using or router.db_for_write(...)` resolution rule.

**CORRESPONDENCE:** gold patch.diff (bundle root) is the one-token edit adding using=db to content_type.save(...); `git apply --check` APPLIES CLEANLY at base_commit — A4/mapping correspondence to the real persist site holds.

**CONCLUSION:** ≥5 distinct attacks run (7 total: prepatch + partial-domain + 2 boundary + control-flow + ungrounded-echo + wrong-branch), none verifies (no CANDIDATE), positive control verifies, prepatch fails at the postcondition, G-AX sound, gold applies. verify⇒correct not falsified. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11066.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A persistence step is given two things: an explicitly named target data
  store (an alias that is always present) and the alias that an external
  write-routing policy would otherwise select. The persisted-to data store
  must be the EXPLICITLY NAMED one, so that the write lands in the store the
  caller named rather than wherever an independent routing policy would send
  it. The routing policy is consulted only as a fallback, when no explicit
  store is named at all.

  Concretely: the resolved target is the explicit alias when one is present
  (which it always is here), and equals it regardless of which alias the
  routing policy would have chosen — even when the policy would pick a
  different store.

Connection aliases are modelled as `List[int]` of Unicode code points (Nagini
bans `str` indexing); equality of two aliases is `PSeq[int]` equality. The
routing policy's choice is modelled as a free input alias, because the policy
is wholly independent of the explicitly named store and may select any alias.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the resolution is modelled deeply; the routing policy's choice is a
# free input alias `routed`, an A-reference validated by axiom_check.py, not a
# consumed @ContractOnly. See refinement.md / mapping.md §3.)
# axioms-end


# pure-start
@Pure
def alias_eq(a: PSeq[int], b: PSeq[int]) -> bool:
    """Two connection aliases denote the same data store iff their code-point
    sequences are equal."""
    return a == b
# pure-end


def persisted_db(db: List[int], routed: List[int]) -> List[int]:
    # pre-conditions-start
    # `db` is the explicitly named target alias and is always present
    # (non-empty); `routed` is the alias the external routing policy would
    # otherwise pick — an arbitrary present alias, read-only here.
    Requires(Acc(list_pred(db), 1 / 2))
    Requires(Acc(list_pred(routed), 1 / 2))
    Requires(len(db) > 0)
    Requires(len(routed) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(db), 1 / 2))
    Ensures(Acc(list_pred(routed), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The write is committed to the EXPLICITLY NAMED store — its alias equals
    # `db` — no matter what the routing policy would have chosen.
    Ensures(alias_eq(ToSeq(Result()), ToSeq(db)))
    # post-conditions-end
    # impl-start
    # using = explicit_alias or routing_policy_choice
    # An explicit alias is supplied (== db), so it is used directly; the
    # routing-policy fallback is reached only when no explicit alias is given.
    src = db if len(db) > 0 else routed  # type: List[int]
    # Copy the chosen alias into a fresh result carrier.
    target = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(db), 1 / 2))
        Invariant(Acc(list_pred(routed), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(len(db) > 0)
        Invariant(ToSeq(src) == ToSeq(db))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(target) == ToSeq(src).take(i))
        # invariants-end
        target = target + [src[i]]
        Assert(ToSeq(src).take(i) + PSeq(src[i]) == ToSeq(src).take(i + 1))
        i = i + 1
    return target
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC:** persisted_db(db, routed) must return an alias whose PSeq equals db's, regardless of the free `routed` input. The postcondition alias_eq(ToSeq(Result()), ToSeq(db)) FULLY pins the output sequence to db; combined with Ensures(Acc(list_pred(Result()))) at FULL permission (result must be a fresh carrier) and the inputs held at only Acc(...,1/2), the spec is tight and hard to satisfy incorrectly.

 Correct interpreter is python (repo root). 7 DISTINCT wrong impls, each edits ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; confirmed same-spec exit 0 for all 7 via `python -m swebench_unified.adversary same-spec nagini django__django-11066 <f>`).

ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini django__django-11066 <f>`; ran concurrently ≤3 at a time as background jobs):
- atk_1 PRE-PATCH BUG (src=routed): weakness EXIT=2 NOT-A-COUNTEREXAMPLE (does not verify). This is the prepatch reproduction.
- atk_2 partial-domain (src = db if len(db)>5 else routed): EXIT=2 rejected.
- atk_3 boundary off-by-one (copy db[:-1], loop to len(src)-1): EXIT=2 rejected.
- atk_4 control-flow-effect (skip loop, return empty carrier): EXIT=2 rejected.
- atk_5 ungrounded-oracle echo (return db input object directly): EXIT=2 rejected — blocked by Ensures(Acc(list_pred(Result()))) full-permission requirement (result must be fresh, cannot alias the 1/2-held input).
- atk_6 wrong-branch (src = db on odd len(db) else routed): EXIT=2 rejected.
- atk_7 boundary over-copy (copy db then append sentinel 0): EXIT=2 rejected.
NO attack returned CANDIDATE (exit 0). Hence NO faithful patch to materialize; run_resolve step is vacuous — nothing to break the spec.

**POSITIVE CONTROL:** positive_control.py = bundle model.py verbatim → `bash scripts/nagini_verify.sh` EXIT=0 'Verification successful' (13.36s).
PREPATCH: model_prepatch.py verbatim → EXIT=1, error at prepatch.py:61 'Postcondition of persisted_db might not hold. Assertion alias_eq(ToSeq(Result()), ToSeq(db)) might not hold' — G-DIFF sound, spec senses the change at exactly the postcondition line. prepatch_reproduced=true.

A-LEG AUDIT (refinement.md): bundle has NO consumed @ContractOnly axiom; the single axioms block is a comment. The one callee router.db_for_write is UNCHANGED and BYPASSED by the fix, modelled as free input `routed` = A-reference (leg A2). All legs classified R / A-reference / I — NO kind-3 (unexpressible-changed-op). The discriminating op (which alias resolves as write target) is modelled DEEPLY via A3 ternary (src = db if len(db)>0 else routed), not hidden behind an axiom.

G-AX (A-reference soundness): copied bundle axiom_check.py (byte-identical, confirmed via diff -q) and ran against REAL Django at base_commit 4b45b6c8e4d7c9701a332e80d3b1c84209dc36e2 (git worktree from repos_cache/django__django, PYTHONPATH set): EXIT=0 'G-AX OK ... over 5 boundary + 5000 fuzz alias pairs'. Both reference properties hold against real ConnectionRouter.db_for_write and the real `using or router.db_for_write(...)` resolution rule.

**CORRESPONDENCE:** gold patch.diff (bundle root) is the one-token edit adding using=db to content_type.save(...); `git apply --check` APPLIES CLEANLY at base_commit — A4/mapping correspondence to the real persist site holds.

**CONCLUSION:** ≥5 distinct attacks run (7 total: prepatch + partial-domain + 2 boundary + control-flow + ungrounded-echo + wrong-branch), none verifies (no CANDIDATE), positive control verifies, prepatch fails at the postcondition, G-AX sound, gold applies. verify⇒correct not falsified. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift-from-real-callee) assessment for django__django-11066 nagini.

**SPEC UNDER TEST:** persisted_db(db, routed) with Requires len(db)>0 and len(routed)>0; postcondition alias_eq(ToSeq(Result()), ToSeq(db)) — i.e. the resolved write-target alias equals the explicitly named alias db, regardless of the routing-policy choice routed.

**REAL CALLEE:** the gold patch adds `using=db` to content_type.save(...) in RenameContentType.`_rename`. Model.save_base resolves `using = using or router.db_for_write(...)` (base.py:761); with a truthy present alias `using=db`, the `or` short-circuits to db and the router is never consulted. Thus the real write target is always db for every present alias, independent of routed. The model postcondition matches this exactly.

**DOMAIN FIDELITY:** precondition len(db)>0 & len(routed)>0 faithfully reflects reality — db = schema_editor.connection.alias and routed = router.db_for_write(...) are both always non-empty configured alias strings. The precondition does not narrow the domain below the real input space, so the spec is not too strong.

### Machine-checked evidence
1. same-spec tool: bundle model.py shares its exact spec region (exit 0), confirming spec region integrity.
2. Independent re-run of conformance_check.py against a fresh base-commit worktree with patch.diff applied: G-CONF OK — shadow (contract-stripped impl region) == real patched persist-step alias resolution on 100000 inputs (seed 11066), 0 disagreements. Input domain includes equal pairs, differing pairs, 'default' on either side, and a non-ASCII alias ('défaut'), driving the REAL `_rename` → Model.save → save_base `using or router.db_for_write(...)` resolution end-to-end with a real ConnectionRouter whose db_for_write returns the free input `routed`.
3. G-AX already validated the A-reference property (router.db_for_write is independent of db and may return an alias != db; using=db short-circuits regardless of router) over 5 boundary + 5000 fuzz pairs.

The modeled function agrees with the real repo callee on every input in the (faithful) precondition domain. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the SOLVER-VISIBLE problem_statement only (not hints_text). The public problem_statement for django__django-11066 already discloses the entire gold edit verbatim: it states 'content_type.save(update_fields={'model'}) should be content_type.save(using=db, update_fields={'model'})' and explains that the single-field write must land in the alias from schema_editor.connection.alias (the explicitly named db) rather than wherever the dynamic database router would send it (the default database). The behavior the spec encodes — resolved write target is the EXPLICITLY NAMED alias `db`, equal to it regardless of which alias the routing policy would have chosen, with the policy consulted only as a fallback — is therefore fully derivable from public information.

**Spec view contents examined:** (1) docstring prose describes 'persist to the explicitly named store rather than the routing policy's choice' — a faithful abstract restatement of already-public behavior, not the edit; (2) pure alias_eq definition; (3) persisted_db signature with pre/postconditions (db/routed present non-empty, Result alias == db). No diff markers, no gold-patch line, no patched file path (django/contrib/contenttypes/management/`__init__`.py), no patched module path, no repo symbol names (RenameContentType, `_rename`, save, db_for_write, ContentType) appear in the spec view. No bug/fix narration terms.

**Machine screen:** swebench_unified.leakage.screen(model.py spec_view, nagini, gold_patch, problem_statement) returns passed=True with zero hard_failures. The changed gold symbol under-4-chars/non-distinctive filter is moot since the edit adds no def/class. spec_view confirms impl region is elided ('...'), so no implementation detail leaks either. The distinctive discriminator (write to explicit alias vs router fallback) is already public in the problem_statement; the model does not reveal anything beyond it. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
