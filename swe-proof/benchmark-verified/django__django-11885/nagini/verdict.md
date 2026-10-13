# P2 adversarial audit — django__django-11885

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition Result() == distinct_count(ToSeq(related_tables)) pins Result() to a deterministic pure function of the input, so every verifying impl is behaviorally equal to the gold count-of-distinct-related-tables. The only same-spec attack that verified (atk_4, the direct-oracle echo `return distinct_count(ToSeq(related_tables))`) is behaviorally CORRECT; its faithful refined patch is the gold patch and RESOLVED=True under the official harness. No verifying wrong impl exists whose faithful patch fails to resolve; verify⇒correct holds.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -92,21 +92,10 @@
     count = 0
     i = len(related_tables)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(related_tables), 1 / 2))
         Invariant(0 <= i and i <= len(related_tables))
-        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
-        Invariant(count >= 0 and count <= len(related_tables) - i)
-        # invariants-end
-        table = related_tables[i - 1]
-        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
-        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
-        # A related table is counted at its FIRST occurrence: count it iff it
-        # does not appear later in the run (i.e. in the already-processed
-        # suffix). This combines the columns of a table that recurs into one
-        # removal.
-        if not contains(ToSeq(related_tables).drop(i), table):
-            count = count + 1
+        Invariant(count == len(related_tables) - i)
+        count = count + 1
         i = i - 1
     return count
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,24 +89,5 @@
     Ensures(Implies(len(related_tables) > 0, Result() >= 1))
     # post-conditions-end
     # impl-start
-    count = 0
-    i = len(related_tables)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(related_tables), 1 / 2))
-        Invariant(0 <= i and i <= len(related_tables))
-        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
-        Invariant(count >= 0 and count <= len(related_tables) - i)
-        # invariants-end
-        table = related_tables[i - 1]
-        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
-        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
-        # A related table is counted at its FIRST occurrence: count it iff it
-        # does not appear later in the run (i.e. in the already-processed
-        # suffix). This combines the columns of a table that recurs into one
-        # removal.
-        if not contains(ToSeq(related_tables).drop(i), table):
-            count = count + 1
-        i = i - 1
-    return count
+    return len(related_tables)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,23 +90,15 @@
     # post-conditions-end
     # impl-start
     count = 0
-    i = len(related_tables)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(related_tables):
         Invariant(Acc(list_pred(related_tables), 1 / 2))
         Invariant(0 <= i and i <= len(related_tables))
-        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
-        Invariant(count >= 0 and count <= len(related_tables) - i)
-        # invariants-end
-        table = related_tables[i - 1]
-        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
-        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
-        # A related table is counted at its FIRST occurrence: count it iff it
-        # does not appear later in the run (i.e. in the already-processed
-        # suffix). This combines the columns of a table that recurs into one
-        # removal.
-        if not contains(ToSeq(related_tables).drop(i), table):
+        Invariant(count == distinct_count(ToSeq(related_tables).take(i)))
+        Invariant(count >= 0 and count <= i)
+        table = related_tables[i]
+        if not contains(ToSeq(related_tables).take(i), table):
             count = count + 1
-        i = i - 1
+        i = i + 1
     return count
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -89,24 +89,5 @@
     Ensures(Implies(len(related_tables) > 0, Result() >= 1))
     # post-conditions-end
     # impl-start
-    count = 0
-    i = len(related_tables)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(related_tables), 1 / 2))
-        Invariant(0 <= i and i <= len(related_tables))
-        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
-        Invariant(count >= 0 and count <= len(related_tables) - i)
-        # invariants-end
-        table = related_tables[i - 1]
-        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
-        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
-        # A related table is counted at its FIRST occurrence: count it iff it
-        # does not appear later in the run (i.e. in the already-processed
-        # suffix). This combines the columns of a table that recurs into one
-        # removal.
-        if not contains(ToSeq(related_tables).drop(i), table):
-            count = count + 1
-        i = i - 1
-    return count
+    return distinct_count(ToSeq(related_tables))
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,24 +89,8 @@
     Ensures(Implies(len(related_tables) > 0, Result() >= 1))
     # post-conditions-end
     # impl-start
-    count = 0
-    i = len(related_tables)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(related_tables), 1 / 2))
-        Invariant(0 <= i and i <= len(related_tables))
-        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
-        Invariant(count >= 0 and count <= len(related_tables) - i)
-        # invariants-end
-        table = related_tables[i - 1]
-        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
-        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
-        # A related table is counted at its FIRST occurrence: count it iff it
-        # does not appear later in the run (i.e. in the already-processed
-        # suffix). This combines the columns of a table that recurs into one
-        # removal.
-        if not contains(ToSeq(related_tables).drop(i), table):
-            count = count + 1
-        i = i - 1
-    return count
+    base = distinct_count(ToSeq(related_tables))
+    if len(related_tables) > 0:
+        return base + 1
+    return base
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,24 +89,7 @@
     Ensures(Implies(len(related_tables) > 0, Result() >= 1))
     # post-conditions-end
     # impl-start
-    count = 0
-    i = len(related_tables)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(related_tables), 1 / 2))
-        Invariant(0 <= i and i <= len(related_tables))
-        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
-        Invariant(count >= 0 and count <= len(related_tables) - i)
-        # invariants-end
-        table = related_tables[i - 1]
-        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
-        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
-        # A related table is counted at its FIRST occurrence: count it iff it
-        # does not appear later in the run (i.e. in the already-processed
-        # suffix). This combines the columns of a table that recurs into one
-        # removal.
-        if not contains(ToSeq(related_tables).drop(i), table):
-            count = count + 1
-        i = i - 1
-    return count
+    if len(related_tables) > 0:
+        return len(related_tables)
+    return 0
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -89,24 +89,7 @@
     Ensures(Implies(len(related_tables) > 0, Result() >= 1))
     # post-conditions-end
     # impl-start
-    count = 0
-    i = len(related_tables)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(related_tables), 1 / 2))
-        Invariant(0 <= i and i <= len(related_tables))
-        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
-        Invariant(count >= 0 and count <= len(related_tables) - i)
-        # invariants-end
-        table = related_tables[i - 1]
-        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
-        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
-        # A related table is counted at its FIRST occurrence: count it iff it
-        # does not appear later in the run (i.e. in the already-processed
-        # suffix). This combines the columns of a table that recurs into one
-        # removal.
-        if not contains(ToSeq(related_tables).drop(i), table):
-            count = count + 1
-        i = i - 1
-    return count
+    if len(related_tables) > 0:
+        return 1
+    return 0
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -92,20 +92,10 @@
     count = 0
     i = len(related_tables)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(related_tables), 1 / 2))
         Invariant(0 <= i and i <= len(related_tables))
-        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
-        Invariant(count >= 0 and count <= len(related_tables) - i)
-        # invariants-end
         table = related_tables[i - 1]
-        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
-        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
-        # A related table is counted at its FIRST occurrence: count it iff it
-        # does not appear later in the run (i.e. in the already-processed
-        # suffix). This combines the columns of a table that recurs into one
-        # removal.
-        if not contains(ToSeq(related_tables).drop(i), table):
+        if contains(ToSeq(related_tables).drop(i), table):
             count = count + 1
         i = i - 1
     return count
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11885.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When cascading deletion plans the set of "fast" bulk removals it can issue
  without first fetching rows into memory, several distinct relations may point
  at the SAME related table (e.g. two foreign keys of one model both referencing
  another model). Each such relation contributes one referencing column.

  The plan must issue ONE bulk removal per distinct related table, combining all
  the columns that reference it, rather than one removal per referencing column.
  Concretely, the number of bulk removals issued equals the number of DISTINCT
  related tables among the fast-removable relations -- so two relations that
  share a related table are served by a single combined removal, never two.

  Every fast-removable relation is accounted for (no related table is dropped),
  and a related table is counted once no matter how many of its columns
  participate; a related table referenced by k relations still yields exactly
  one removal whose combined predicate covers all k referencing columns.

Each fast-removable candidate relation is modelled by the integer identity of
the related table it targets; the ordered run of candidates is a `List[int]` of
those identities, with the specification carried over `PSeq[int]` via `ToSeq`.
The count of distinct related tables is spelled out deeply as a front-recursive
fold (`distinct_count`), paired with a matching loop. No callee is axiomatized:
the grouping is membership/counting logic over the candidate identities,
modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions; provenance
binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axiom: the combine-by-related-table grouping is membership /
# counting logic over the candidate related-table identities, modelled deeply
# below. The unchanged callees that decide fast-removability and that build the
# per-table combined query from a list of referencing columns are independent of
# this count and are not invoked by the modelled behaviour; their provenance is
# recorded in mapping.md.)
# axioms-end


# pure-start
@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff related-table identity `x` occurs in sequence `s`. Front-
    recursive so a single unfold is available per fold/loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


@Pure
def distinct_count(s: PSeq[int]) -> int:
    """Number of DISTINCT related-table identities in `s`: the number of
    combined bulk removals to issue. An identity is counted at its FIRST
    occurrence -- i.e. it is counted iff it does not occur anywhere later in the
    sequence. Front-recursive so a single unfold is available per loop step."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    Ensures(Implies(len(s) > 0, Result() >= 1))
    if len(s) == 0:
        return 0
    rest = distinct_count(s.drop(1))
    if contains(s.drop(1), s[0]):
        return rest
    return 1 + rest
# pure-end


def combined_fast_delete_count(related_tables: List[int]) -> int:
    # pre-conditions-start
    # The candidate run is read-only: required and ensured at fractional
    # permission only.
    Requires(Acc(list_pred(related_tables), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(related_tables), 1 / 2))
    # The number of bulk removals issued equals the number of DISTINCT related
    # tables among the fast-removable candidates: two candidates sharing a
    # related table are served by one combined removal, never two.
    Ensures(Result() == distinct_count(ToSeq(related_tables)))
    # At least one removal per non-empty candidate run, and never more than one
    # per candidate (the combining never increases the number of removals).
    Ensures(Result() >= 0 and Result() <= len(related_tables))
    Ensures(Implies(len(related_tables) > 0, Result() >= 1))
    # post-conditions-end
    # impl-start
    count = 0
    i = len(related_tables)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(related_tables), 1 / 2))
        Invariant(0 <= i and i <= len(related_tables))
        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
        Invariant(count >= 0 and count <= len(related_tables) - i)
        # invariants-end
        table = related_tables[i - 1]
        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
        # A related table is counted at its FIRST occurrence: count it iff it
        # does not appear later in the run (i.e. in the already-processed
        # suffix). This combines the columns of a table that recurs into one
        # removal.
        if not contains(ToSeq(related_tables).drop(i), table):
            count = count + 1
        i = i - 1
    return count
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** model.py's combined_fast_delete_count carries Ensures(Result() == distinct_count(ToSeq(related_tables))) plus bound/non-empty ensures. This equality fully pins Result() to a pure fold over the input (distinct_count = number of distinct related-table identities). Any impl that verifies MUST return exactly distinct_count everywhere, hence is behaviorally equal to the gold combine-by-related-table count. This is the tightest possible G-EQ shape.

### ATTACKS (all same-spec byte-identical, `adversary same-spec` exit 0 for all 8 + pos_control):
- atk_1 (PREPATCH BUG, count==len, one removal per candidate, no grouping): `weakness` exit 2 — REJECTED (fails postcond when a table recurs). prepatch_reproduced=true.
- atk_2 (partial-domain `return len(related_tables)`): exit 2 REJECTED.
- atk_3 (last/prefix-occurrence counting via .take; behaviorally correct but not provable under given invariant): exit 2 REJECTED (rejection is fine — spec admits no wrong impl regardless).
- atk_4 (direct-oracle echo `return distinct_count(ToSeq(related_tables))`): weakness exit 0 CANDIDATE (verifies, 11.2s). Behaviorally CORRECT.
- atk_5 (boundary off-by-one `distinct_count+1` when non-empty): exit 2 REJECTED.
- atk_6 (control-flow-effect early `return len` when non-empty): exit 2 REJECTED.
- atk_7 (ungrounded-oracle echo `return 1` when non-empty — satisfies bounds/non-empty ensures but not equality): exit 2 REJECTED.
- atk_8 (flipped membership: count iff appears later): exit 2 REJECTED.

COMMANDS (per attack): `python -m swebench_unified.adversary same-spec nagini django__django-11885 <atk>` and `... weakness nagini django__django-11885 <atk>`. Weakness runs launched concurrently in background batches of <=3 (JVM+Z3 each): batch A {1,2,3}, B {4,5,6}, C {7,8}. Exit summary in w_exits.txt: 4 => exit 0; 1,2,3,5,6,7,8 => exit 2.

CANDIDATE RESOLVE (mandatory): atk_4 is behaviorally correct, so its faithful refined patch is the gold patch verbatim (materialized at atk_4_faithful.patch from data/swe_bench_verified/test.jsonl). Ran run_resolve('django__django-11885', patch, timeout=1800) via swebench_unified.harness => RESOLVED=True, COMPLETED=True, NOTE='resolved'. So the only verifying impl's faithful patch DOES resolve — no verify⇏correct break.

A-REFERENCE AUDIT (refinement.md §A/§C, mapping.md §3.1): No consumed axiom. The sole deep-model reference is distinct_count ↔ collections.defaultdict(list) grouping keyed by related_model (len(model_fast_deletes)). Ran axiom_check.py (G-AX) => exit 0: 'distinct_count deep model == real defaultdict-grouped combined-removal count on 11 boundary + 50000 fuzz candidate runs; no column dropped/duplicated; bounds hold.' Legs: A1=R (candidate relation ↔ related_model identity; can_fast_delete filter = membership condition on the input run), A2/A3=R + A-reference (per-first-occurrence increment = defaultdict key creation; Result()=distinct_count=len(model_fast_deletes)=fast_deletes appends), B1-B4=R/I (list-of-fields threading, get_del_batches, can_fast_delete on related_model, defaultdict container refactor — carry no count, validated by G-RESOLVE). §C confirmed: no kind-3 step; the one genuinely-changed op (collapse per-candidate removals into one-per-distinct-table) is modelled DEEPLY, not axiomatized. Correspondence holds.

**POSITIVE CONTROL:** pos_control.py = exact original model.py impl; `adversary verify` => VERIFIED in 11.9s.

**CONCLUSION:** SOUND. >=5 distinct wrong impls attacked (prepatch + partial-domain + boundary + control-flow-effect + ungrounded-oracle echo + flipped-condition), all rejected by the equality postcondition; the lone verifying candidate (echo) is correct and its faithful (gold) patch resolves under the executed harness. verify⇒correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition Result() == distinct_count(ToSeq(related_tables)) pins Result() to a deterministic pure function of the input, so every verifying impl is behaviorally equal to the gold count-of-distinct-related-tables. The only same-spec attack that verified (atk_4, the direct-oracle echo `return distinct_count(ToSeq(related_tables))`) is behaviorally CORRECT; its faithful refined patch is the gold patch and RESOLVED=True under the official harness. No verifying wrong impl exists whose faithful patch fails to resolve; verify⇒correct holds.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11885.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When cascading deletion plans the set of "fast" bulk removals it can issue
  without first fetching rows into memory, several distinct relations may point
  at the SAME related table (e.g. two foreign keys of one model both referencing
  another model). Each such relation contributes one referencing column.

  The plan must issue ONE bulk removal per distinct related table, combining all
  the columns that reference it, rather than one removal per referencing column.
  Concretely, the number of bulk removals issued equals the number of DISTINCT
  related tables among the fast-removable relations -- so two relations that
  share a related table are served by a single combined removal, never two.

  Every fast-removable relation is accounted for (no related table is dropped),
  and a related table is counted once no matter how many of its columns
  participate; a related table referenced by k relations still yields exactly
  one removal whose combined predicate covers all k referencing columns.

Each fast-removable candidate relation is modelled by the integer identity of
the related table it targets; the ordered run of candidates is a `List[int]` of
those identities, with the specification carried over `PSeq[int]` via `ToSeq`.
The count of distinct related tables is spelled out deeply as a front-recursive
fold (`distinct_count`), paired with a matching loop. No callee is axiomatized:
the grouping is membership/counting logic over the candidate identities,
modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions; provenance
binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axiom: the combine-by-related-table grouping is membership /
# counting logic over the candidate related-table identities, modelled deeply
# below. The unchanged callees that decide fast-removability and that build the
# per-table combined query from a list of referencing columns are independent of
# this count and are not invoked by the modelled behaviour; their provenance is
# recorded in mapping.md.)
# axioms-end


# pure-start
@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff related-table identity `x` occurs in sequence `s`. Front-
    recursive so a single unfold is available per fold/loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


@Pure
def distinct_count(s: PSeq[int]) -> int:
    """Number of DISTINCT related-table identities in `s`: the number of
    combined bulk removals to issue. An identity is counted at its FIRST
    occurrence -- i.e. it is counted iff it does not occur anywhere later in the
    sequence. Front-recursive so a single unfold is available per loop step."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    Ensures(Implies(len(s) > 0, Result() >= 1))
    if len(s) == 0:
        return 0
    rest = distinct_count(s.drop(1))
    if contains(s.drop(1), s[0]):
        return rest
    return 1 + rest
# pure-end


def combined_fast_delete_count(related_tables: List[int]) -> int:
    # pre-conditions-start
    # The candidate run is read-only: required and ensured at fractional
    # permission only.
    Requires(Acc(list_pred(related_tables), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(related_tables), 1 / 2))
    # The number of bulk removals issued equals the number of DISTINCT related
    # tables among the fast-removable candidates: two candidates sharing a
    # related table are served by one combined removal, never two.
    Ensures(Result() == distinct_count(ToSeq(related_tables)))
    # At least one removal per non-empty candidate run, and never more than one
    # per candidate (the combining never increases the number of removals).
    Ensures(Result() >= 0 and Result() <= len(related_tables))
    Ensures(Implies(len(related_tables) > 0, Result() >= 1))
    # post-conditions-end
    # impl-start
    count = 0
    i = len(related_tables)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(related_tables), 1 / 2))
        Invariant(0 <= i and i <= len(related_tables))
        Invariant(count == distinct_count(ToSeq(related_tables).drop(i)))
        Invariant(count >= 0 and count <= len(related_tables) - i)
        # invariants-end
        table = related_tables[i - 1]
        Assert(ToSeq(related_tables).drop(i - 1)[0] == table)
        Assert(ToSeq(related_tables).drop(i - 1).drop(1) == ToSeq(related_tables).drop(i))
        # A related table is counted at its FIRST occurrence: count it iff it
        # does not appear later in the run (i.e. in the already-processed
        # suffix). This combines the columns of a table that recurs into one
        # removal.
        if not contains(ToSeq(related_tables).drop(i), table):
            count = count + 1
        i = i - 1
    return count
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** model.py's combined_fast_delete_count carries Ensures(Result() == distinct_count(ToSeq(related_tables))) plus bound/non-empty ensures. This equality fully pins Result() to a pure fold over the input (distinct_count = number of distinct related-table identities). Any impl that verifies MUST return exactly distinct_count everywhere, hence is behaviorally equal to the gold combine-by-related-table count. This is the tightest possible G-EQ shape.

### ATTACKS (all same-spec byte-identical, `adversary same-spec` exit 0 for all 8 + pos_control):
- atk_1 (PREPATCH BUG, count==len, one removal per candidate, no grouping): `weakness` exit 2 — REJECTED (fails postcond when a table recurs). prepatch_reproduced=true.
- atk_2 (partial-domain `return len(related_tables)`): exit 2 REJECTED.
- atk_3 (last/prefix-occurrence counting via .take; behaviorally correct but not provable under given invariant): exit 2 REJECTED (rejection is fine — spec admits no wrong impl regardless).
- atk_4 (direct-oracle echo `return distinct_count(ToSeq(related_tables))`): weakness exit 0 CANDIDATE (verifies, 11.2s). Behaviorally CORRECT.
- atk_5 (boundary off-by-one `distinct_count+1` when non-empty): exit 2 REJECTED.
- atk_6 (control-flow-effect early `return len` when non-empty): exit 2 REJECTED.
- atk_7 (ungrounded-oracle echo `return 1` when non-empty — satisfies bounds/non-empty ensures but not equality): exit 2 REJECTED.
- atk_8 (flipped membership: count iff appears later): exit 2 REJECTED.

COMMANDS (per attack): `python -m swebench_unified.adversary same-spec nagini django__django-11885 <atk>` and `... weakness nagini django__django-11885 <atk>`. Weakness runs launched concurrently in background batches of <=3 (JVM+Z3 each): batch A {1,2,3}, B {4,5,6}, C {7,8}. Exit summary in w_exits.txt: 4 => exit 0; 1,2,3,5,6,7,8 => exit 2.

CANDIDATE RESOLVE (mandatory): atk_4 is behaviorally correct, so its faithful refined patch is the gold patch verbatim (materialized at atk_4_faithful.patch from data/swe_bench_verified/test.jsonl). Ran run_resolve('django__django-11885', patch, timeout=1800) via swebench_unified.harness => RESOLVED=True, COMPLETED=True, NOTE='resolved'. So the only verifying impl's faithful patch DOES resolve — no verify⇏correct break.

A-REFERENCE AUDIT (refinement.md §A/§C, mapping.md §3.1): No consumed axiom. The sole deep-model reference is distinct_count ↔ collections.defaultdict(list) grouping keyed by related_model (len(model_fast_deletes)). Ran axiom_check.py (G-AX) => exit 0: 'distinct_count deep model == real defaultdict-grouped combined-removal count on 11 boundary + 50000 fuzz candidate runs; no column dropped/duplicated; bounds hold.' Legs: A1=R (candidate relation ↔ related_model identity; can_fast_delete filter = membership condition on the input run), A2/A3=R + A-reference (per-first-occurrence increment = defaultdict key creation; Result()=distinct_count=len(model_fast_deletes)=fast_deletes appends), B1-B4=R/I (list-of-fields threading, get_del_batches, can_fast_delete on related_model, defaultdict container refactor — carry no count, validated by G-RESOLVE). §C confirmed: no kind-3 step; the one genuinely-changed op (collapse per-candidate removals into one-per-distinct-table) is modelled DEEPLY, not axiomatized. Correspondence holds.

**POSITIVE CONTROL:** pos_control.py = exact original model.py impl; `adversary verify` => VERIFIED in 11.9s.

**CONCLUSION:** SOUND. >=5 distinct wrong impls attacked (prepatch + partial-domain + boundary + control-flow-effect + ungrounded-oracle echo + flipped-condition), all rejected by the equality postcondition; the lone verifying candidate (echo) is correct and its faithful (gold) patch resolves under the executed harness. verify⇒correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness audit of combined_fast_delete_count vs the real fast-delete planning in Collector.collect (django/db/models/deletion.py). Machine-checked: (1) model.py verifies (nagini_verify exit 0, 11.35s); (2) adversary same-spec confirms model_prepatch.py shares the byte-identical spec; (3) the prepatch twin FAILS verification on Result()==distinct_count(ToSeq(related_tables)) — the spec genuinely senses the combine-by-distinct-table change (the [r,r]->1 F2P case); (4) axiom_check.py confirms the deep model distinct_count equals the real collections.defaultdict(list) key count non-vacuously over 50011 inputs; (5) I reproduced the actual F2P models (Origin/Referrer/SecondReferrer, two cascade FKs) inside the registered `delete` test app and confirmed candidate run [r,r] -> distinct_count=1 == real single-object collect len(fast_deletes)=1, and the gold patch's full delete suite passes (44 OK). The model faithfully captures the number of distinct related tables = number of combined fast-delete removals that the F2P assertNumQueries(2) observes. NOTE ON MODELING BOUNDARY (not a break): the List[int] carrier deliberately abstracts away the number of deleted objects, so for a multi-batch delete (e.g. 2999 objects) the real len(fast_deletes)=7 while the model returns distinct_count=1. This get_del_batches batching factor is identical pre- and post-patch, is orthogonal to the patch's discriminating combining behavior, is documented in mapping.md/refinement.md §B, and is not exercised by the F2P test (single-object -> single batch). Within the modeled domain (the tested single-batch scenario, which is the G-RESOLVE oracle) the modeled function agrees with the real callee on every input. CAVEAT: the G-CONF conformance_check.py oracle is effectively vacuous as written (synthetic models are built with app_labels not in INSTALLED_APPS, so get_candidate_relations_to_delete returns 0 -> every extract_run is [] and oracle_count is 0; all 107500 comparisons are 0==0). That is a weakness of the conformance script's coverage, not a faithfulness defect of the model — I independently confirmed the non-vacuous correspondence via the real F2P models and via axiom_check. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes cleanly (no hard failures): no diff markers, no verbatim gold-patch lines, no patched file/module paths, no spec-view identifier or comment echoing a patched repo symbol, no bug/fix narration.

Semantic review of the spec view (docstring + `contains`/`distinct_count` pure region + `combined_fast_delete_count` pre/postconditions; impl elided) confirms NO-LEAKAGE beyond the public problem_statement:

- The discriminating fix — 'combine fast-delete queries by table into ONE bulk removal per distinct related table rather than one per relation/column' — is ALREADY stated in full by the public problem_statement, which says 'the collection logic should combine such queries by table to reduce the number of roundtrips' and gives a worked example collapsing N queries into one via OR (`DELETE FROM entry WHERE created_by_id = :id OR updated_by = :id`). So the behavioral crux is public, not leaked.
- The spec view restates this at the same 'desired behaviour' altitude: 'ONE bulk removal per distinct related table', 'the number of bulk removals equals the number of DISTINCT related tables'. This is a faithful abstraction of the public issue, not a reveal of the edit.
- None of the gold-edit specifics appear in the spec view: no patched paths (django/db/models/deletion.py, django/contrib/admin/utils.py — confined to the elided mapping.md), no patched symbols (collect, fast_deletes, related_objects, get_del_batches, model_fast_deletes, defaultdict, reduce/operator.or_, Q, related_model, related_fields, can_fast_delete). The carrier is a generic List[int] of opaque table identities and the mechanism is generic first-occurrence membership counting; nothing localizes the edit or discloses the implementation strategy.

**Verdict:** NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, which ships in this bundle, so a reader can start there.
