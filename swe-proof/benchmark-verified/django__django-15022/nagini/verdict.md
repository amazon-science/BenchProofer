# P2 adversarial audit — django__django-15022

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk6.py`, `atk7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,35 +75,23 @@
     Ensures(Result() == some_row_matches_all(rows, terms))
     # post-conditions-end
     # impl-start
-    # Skeleton of the patch: every per-term query is accumulated and the object
-    # is retained only if a single related row clears the whole conjunction.
-    retained = False
-    i = len(rows)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(rows))
-        Invariant(retained == some_row_matches_all(rows.drop(i), terms))
-        # invariants-end
-        row = rows[i - 1]
-        Assert(rows.drop(i - 1)[0] == row)
-        Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
-        # all_clear: does this single related row satisfy every term?
-        all_clear = True
-        j = len(terms)
-        while j > 0:
-            # invariants-start
-            Invariant(0 <= j and j <= len(terms))
-            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
-            # invariants-end
-            term = terms[j - 1]
-            Assert(terms.drop(j - 1)[0] == term)
-            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
-            if not matches(row, term):
-                all_clear = False
-            j = j - 1
-        Assert(all_clear == row_matches_all(row, terms))
-        if all_clear:
-            retained = True
-        i = i - 1
+    # Pre-patch chained-filter skeleton: retained iff EVERY term is matched by
+    # SOME (possibly different) row. Wrong quantifier order.
+    retained = True
+    j = len(terms)
+    while j > 0:
+        Invariant(0 <= j and j <= len(terms))
+        term = terms[j - 1]
+        term_seen = False
+        i = len(rows)
+        while i > 0:
+            Invariant(0 <= i and i <= len(rows))
+            row = rows[i - 1]
+            if matches(row, term):
+                term_seen = True
+            i = i - 1
+        if not term_seen:
+            retained = False
+        j = j - 1
     return retained
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,33 +75,21 @@
     Ensures(Result() == some_row_matches_all(rows, terms))
     # post-conditions-end
     # impl-start
-    # Skeleton of the patch: every per-term query is accumulated and the object
-    # is retained only if a single related row clears the whole conjunction.
+    # Off-by-one: iterate rows but stop one short (i starts at len(rows)-1),
+    # so the last row can never be the witness.
     retained = False
-    i = len(rows)
+    i = len(rows) - 1
     while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(rows))
-        Invariant(retained == some_row_matches_all(rows.drop(i), terms))
-        # invariants-end
+        Invariant(-1 <= i and i <= len(rows))
         row = rows[i - 1]
-        Assert(rows.drop(i - 1)[0] == row)
-        Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
-        # all_clear: does this single related row satisfy every term?
         all_clear = True
         j = len(terms)
         while j > 0:
-            # invariants-start
             Invariant(0 <= j and j <= len(terms))
-            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
-            # invariants-end
             term = terms[j - 1]
-            Assert(terms.drop(j - 1)[0] == term)
-            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
             if not matches(row, term):
                 all_clear = False
             j = j - 1
-        Assert(all_clear == row_matches_all(row, terms))
         if all_clear:
             retained = True
         i = i - 1
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,26 +75,23 @@
     Ensures(Result() == some_row_matches_all(rows, terms))
     # post-conditions-end
     # impl-start
-    # Skeleton of the patch: every per-term query is accumulated and the object
-    # is retained only if a single related row clears the whole conjunction.
+    # Partial-domain: shortcut True when there is at least one row, else the
+    # exact predicate. Wrong: a single row that clears NO term must drop.
+    if len(rows) > 0:
+        return True
     retained = False
     i = len(rows)
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(rows))
         Invariant(retained == some_row_matches_all(rows.drop(i), terms))
-        # invariants-end
         row = rows[i - 1]
         Assert(rows.drop(i - 1)[0] == row)
         Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
-        # all_clear: does this single related row satisfy every term?
         all_clear = True
         j = len(terms)
         while j > 0:
-            # invariants-start
             Invariant(0 <= j and j <= len(terms))
             Invariant(all_clear == row_matches_all(row, terms.drop(j)))
-            # invariants-end
             term = terms[j - 1]
             Assert(terms.drop(j - 1)[0] == term)
             Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,35 +75,7 @@
     Ensures(Result() == some_row_matches_all(rows, terms))
     # post-conditions-end
     # impl-start
-    # Skeleton of the patch: every per-term query is accumulated and the object
-    # is retained only if a single related row clears the whole conjunction.
-    retained = False
-    i = len(rows)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(rows))
-        Invariant(retained == some_row_matches_all(rows.drop(i), terms))
-        # invariants-end
-        row = rows[i - 1]
-        Assert(rows.drop(i - 1)[0] == row)
-        Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
-        # all_clear: does this single related row satisfy every term?
-        all_clear = True
-        j = len(terms)
-        while j > 0:
-            # invariants-start
-            Invariant(0 <= j and j <= len(terms))
-            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
-            # invariants-end
-            term = terms[j - 1]
-            Assert(terms.drop(j - 1)[0] == term)
-            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
-            if not matches(row, term):
-                all_clear = False
-            j = j - 1
-        Assert(all_clear == row_matches_all(row, terms))
-        if all_clear:
-            retained = True
-        i = i - 1
+    # Control-flow: ignore inputs, always retain.
+    retained = True
     return retained
     # impl-end
```

Attack 5 — `atk5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -75,35 +75,5 @@
     Ensures(Result() == some_row_matches_all(rows, terms))
     # post-conditions-end
     # impl-start
-    # Skeleton of the patch: every per-term query is accumulated and the object
-    # is retained only if a single related row clears the whole conjunction.
-    retained = False
-    i = len(rows)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(rows))
-        Invariant(retained == some_row_matches_all(rows.drop(i), terms))
-        # invariants-end
-        row = rows[i - 1]
-        Assert(rows.drop(i - 1)[0] == row)
-        Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
-        # all_clear: does this single related row satisfy every term?
-        all_clear = True
-        j = len(terms)
-        while j > 0:
-            # invariants-start
-            Invariant(0 <= j and j <= len(terms))
-            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
-            # invariants-end
-            term = terms[j - 1]
-            Assert(terms.drop(j - 1)[0] == term)
-            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
-            if not matches(row, term):
-                all_clear = False
-            j = j - 1
-        Assert(all_clear == row_matches_all(row, terms))
-        if all_clear:
-            retained = True
-        i = i - 1
-    return retained
+    return some_row_matches_all(rows, terms)
     # impl-end
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,35 +75,19 @@
     Ensures(Result() == some_row_matches_all(rows, terms))
     # post-conditions-end
     # impl-start
-    # Skeleton of the patch: every per-term query is accumulated and the object
-    # is retained only if a single related row clears the whole conjunction.
+    # exists-row exists-term: retained if ANY row matches ANY term. Too weak.
     retained = False
     i = len(rows)
     while i > 0:
-        # invariants-start
         Invariant(0 <= i and i <= len(rows))
-        Invariant(retained == some_row_matches_all(rows.drop(i), terms))
-        # invariants-end
         row = rows[i - 1]
-        Assert(rows.drop(i - 1)[0] == row)
-        Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
-        # all_clear: does this single related row satisfy every term?
-        all_clear = True
         j = len(terms)
         while j > 0:
-            # invariants-start
             Invariant(0 <= j and j <= len(terms))
-            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
-            # invariants-end
             term = terms[j - 1]
-            Assert(terms.drop(j - 1)[0] == term)
-            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
-            if not matches(row, term):
-                all_clear = False
+            if matches(row, term):
+                retained = True
             j = j - 1
-        Assert(all_clear == row_matches_all(row, terms))
-        if all_clear:
-            retained = True
         i = i - 1
     return retained
     # impl-end
```

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,35 +75,19 @@
     Ensures(Result() == some_row_matches_all(rows, terms))
     # post-conditions-end
     # impl-start
-    # Skeleton of the patch: every per-term query is accumulated and the object
-    # is retained only if a single related row clears the whole conjunction.
+    # Only inspect rows[0] as the possible all-terms witness (drops rest).
     retained = False
-    i = len(rows)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(rows))
-        Invariant(retained == some_row_matches_all(rows.drop(i), terms))
-        # invariants-end
-        row = rows[i - 1]
-        Assert(rows.drop(i - 1)[0] == row)
-        Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
-        # all_clear: does this single related row satisfy every term?
+    if len(rows) > 0:
+        row = rows[0]
         all_clear = True
         j = len(terms)
         while j > 0:
-            # invariants-start
             Invariant(0 <= j and j <= len(terms))
-            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
-            # invariants-end
             term = terms[j - 1]
-            Assert(terms.drop(j - 1)[0] == term)
-            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
             if not matches(row, term):
                 all_clear = False
             j = j - 1
-        Assert(all_clear == row_matches_all(row, terms))
         if all_clear:
             retained = True
-        i = i - 1
     return retained
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for django__django-15022.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A keyword search over a list of search terms is performed against the related
  rows reachable from one candidate object. For the candidate there is a finite
  sequence of related rows and a finite sequence of search terms. The relation
  `matches(row, term)` holds when that related row satisfies that search term
  (at least one searched field of the row matches the term).

  The candidate object is RETAINED by the search exactly when a SINGLE related
  row satisfies EVERY search term simultaneously:

        retained  <=>  exists a related row that, for all terms, matches.

  In particular, when no single row satisfies all the terms together the
  candidate is dropped, even if every individual term is satisfied by some
  (different) related row. The quantifier order is "exists-row then for-all-
  terms", never "for-all-terms then exists-row".

The related-row and search-term collections are modelled by `PSeq[int]`
sequences of opaque identifiers; the per-(row, term) comparison is the abstract
relation `matches`. No machinery internal to a single field/term comparison is
modelled (it is unchanged). The specification pins only the combination
semantics — which row must satisfy which terms for the object to be retained.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def matches(row: int, term: int) -> bool:
    """Abstract per-(row, term) match relation: related row `row` satisfies
    search term `term` (the OR over that row's searched fields for the term).
    An uninterpreted total relation on the identifier domains; the combination
    semantics under specification do not depend on how a single comparison is
    computed. Provenance: mapping.md (the per-term OR-query evaluated against
    one related row by the database)."""
    Ensures(Implies(Result(), Result()))
# axioms-end


# pure-start
@Pure
def row_matches_all(row: int, terms: PSeq[int]) -> bool:
    """Related row `row` satisfies every term in the sequence. Front-recursive
    so a single unfold is available per loop step."""
    if len(terms) == 0:
        return True
    return matches(row, terms[0]) and row_matches_all(row, terms.drop(1))


@Pure
def some_row_matches_all(rows: PSeq[int], terms: PSeq[int]) -> bool:
    """Some related row satisfies every term: exists-row then for-all-terms.
    This is the retention predicate. Front-recursive over the rows."""
    if len(rows) == 0:
        return False
    return row_matches_all(rows[0], terms) or \
        some_row_matches_all(rows.drop(1), terms)
# pure-end


def search_retains_object(rows: PSeq[int], terms: PSeq[int]) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The object is retained exactly when one related row satisfies all terms
    # together (exists-row, for-all-terms) — not when each term is met by some
    # (possibly different) row.
    Ensures(Result() == some_row_matches_all(rows, terms))
    # post-conditions-end
    # impl-start
    retained = False
    i = len(rows)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(rows))
        Invariant(retained == some_row_matches_all(rows.drop(i), terms))
        # invariants-end
        row = rows[i - 1]
        Assert(rows.drop(i - 1)[0] == row)
        Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
        all_clear = True
        j = len(terms)
        while j > 0:
            # invariants-start
            Invariant(0 <= j and j <= len(terms))
            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
            # invariants-end
            term = terms[j - 1]
            Assert(terms.drop(j - 1)[0] == term)
            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
            if not matches(row, term):
                all_clear = False
            j = j - 1
        Assert(all_clear == row_matches_all(row, terms))
        if all_clear:
            retained = True
        i = i - 1
    return retained
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-15022 (nagini). VERDICT: SOUND.

SPEC SHAPE: The frozen postcondition is a TOTAL FUNCTIONAL EQUALITY with an EMPTY precondition: `Ensures(Result() == some_row_matches_all(rows, terms))`. This pins the return value exactly, as a pure function of the inputs, on ALL inputs (no precondition to carve out a partial domain). It is the strongest possible spec shape: any verifying impl must be functionally identical to `some_row_matches_all` (exists-row, for-all-terms). This makes a verify⇏ correct break essentially impossible unless a wrong impl can still discharge the exact-equality postcondition, which cannot happen for a function that differs from `some_row_matches_all` on any input.

SAME-SPEC: all 8 files (pc + atk1..atk7) confirmed spec-byte-identical via `python -m swebench_unified.adversary same-spec nagini django__django-15022 <f>` (exit 0 each). Only the impl region was edited; axioms/@Pure predicates/Requires/Ensures byte-identical.

pc.py (positive control = exact correct model impl): EXIT 0 = CANDIDATE (verifies). Expected — it is the correct impl; establishes the toolchain verifies the gold model.
- atk1.py PREPATCH BUG (chained-filter: for-all-terms/exists-row, `retained` starts True, drop iff some term matched by no row): EXIT 2 = does not verify (spec rejected). Prepatch reproduced.
- atk2.py BOUNDARY off-by-one (i starts at len(rows)-1, last row never a witness): EXIT 2 = does not verify.
- atk3.py PARTIAL-DOMAIN (`if len(rows)>0: return True` else exact): EXIT 2 = does not verify.
- atk4.py CONTROL-FLOW-EFFECT (unconditional `return True`): EXIT 2 = does not verify.
- atk6.py WRONG-QUANTIFIER (exists-row exists-term: any row matches any term): EXIT 2 = does not verify.
- atk7.py FIRST-ROW-ONLY (only rows[0] can be the all-terms witness): EXIT 2 = does not verify.
- atk5.py UNGROUNDED-ORACLE ECHO (`return some_row_matches_all(rows, terms)`): EXIT 0 = CANDIDATE (shares spec AND verifies). This is functionally IDENTICAL to the gold combination semantics, so its faithful refined patch IS the gold single-filter-AND patch.

MANDATORY RESOLVE ON EVERY VERIFYING CANDIDATE: atk5 materialized to atk5_patch.diff (= gold patch verbatim from frozen dataset row) and executed through the official harness: `run_resolve('django__django-15022', patch)` => RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1. A resolving echo is NOT a weakness (2026-08-06 policy: candidate fails the gate only if its refined patch does NOT resolve). No verifying wrong impl exists whose faithful patch fails to resolve, so verify⇒correct is not falsified.

6 DISTINCT wrong impls exercised (partial-domain=atk3, boundary=atk2, control-flow-effect=atk4, ungrounded-oracle-echo=atk5 [resolves], prepatch=atk1, plus wrong-quantifier=atk6, first-row-only=atk7) — all 6 wrong ones rejected by the exact-equality postcondition; the 1 that verified is a correct echo that resolves.

REFINEMENT.MD A-LEG AUDIT: legs A1/A2 = R (terms/rows ↔ PSeq[int] id abstraction); A3 = modeling primitive (`matches` uninterpreted, contract is tautology Implies(R,R), proof uses no property of it — correctly NOT an axiom); A4 = A-reference (`some_row_matches_all`/`row_matches_all` deep-models the patched single `.filter(models.Q(*term_queries))` semantics; validated == real Django single-filter-AND by axiom_check.py); A5 = R/I (bool ↔ candidate membership in returned queryset). NO kind-3 (unexpressible-changed-op) leg; NO A-consumed axiom (meta axioms: []). A-reference correspondence verified: `python axiom_check.py` => exit 0, 'G-AX OK: some_row_matches_all == single-filter-AND on all match matrices up to 3x4 + 20000 fuzz + F2P scenarios; no library callee to axiomatize'. The A4 deep model faithfully corresponds to the real callee (queryset.filter over multi-valued relation) and matches the mapping.md §3.1 provenance.

CONCLUSION: The spec is a tight exact-equality postcondition that rejects every functionally-wrong impl and admits only functionally-gold impls (whose faithful patch resolves). Refinement legs are all R/A-reference/I with a G-AX-validated A-reference. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk6.py`, `atk7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for django__django-15022.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A keyword search over a list of search terms is performed against the related
  rows reachable from one candidate object. For the candidate there is a finite
  sequence of related rows and a finite sequence of search terms. The relation
  `matches(row, term)` holds when that related row satisfies that search term
  (at least one searched field of the row matches the term).

  The candidate object is RETAINED by the search exactly when a SINGLE related
  row satisfies EVERY search term simultaneously:

        retained  <=>  exists a related row that, for all terms, matches.

  In particular, when no single row satisfies all the terms together the
  candidate is dropped, even if every individual term is satisfied by some
  (different) related row. The quantifier order is "exists-row then for-all-
  terms", never "for-all-terms then exists-row".

The related-row and search-term collections are modelled by `PSeq[int]`
sequences of opaque identifiers; the per-(row, term) comparison is the abstract
relation `matches`. No machinery internal to a single field/term comparison is
modelled (it is unchanged). The specification pins only the combination
semantics — which row must satisfy which terms for the object to be retained.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def matches(row: int, term: int) -> bool:
    """Abstract per-(row, term) match relation: related row `row` satisfies
    search term `term` (the OR over that row's searched fields for the term).
    An uninterpreted total relation on the identifier domains; the combination
    semantics under specification do not depend on how a single comparison is
    computed. Provenance: mapping.md (the per-term OR-query evaluated against
    one related row by the database)."""
    Ensures(Implies(Result(), Result()))
# axioms-end


# pure-start
@Pure
def row_matches_all(row: int, terms: PSeq[int]) -> bool:
    """Related row `row` satisfies every term in the sequence. Front-recursive
    so a single unfold is available per loop step."""
    if len(terms) == 0:
        return True
    return matches(row, terms[0]) and row_matches_all(row, terms.drop(1))


@Pure
def some_row_matches_all(rows: PSeq[int], terms: PSeq[int]) -> bool:
    """Some related row satisfies every term: exists-row then for-all-terms.
    This is the retention predicate. Front-recursive over the rows."""
    if len(rows) == 0:
        return False
    return row_matches_all(rows[0], terms) or \
        some_row_matches_all(rows.drop(1), terms)
# pure-end


def search_retains_object(rows: PSeq[int], terms: PSeq[int]) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The object is retained exactly when one related row satisfies all terms
    # together (exists-row, for-all-terms) — not when each term is met by some
    # (possibly different) row.
    Ensures(Result() == some_row_matches_all(rows, terms))
    # post-conditions-end
    # impl-start
    retained = False
    i = len(rows)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(rows))
        Invariant(retained == some_row_matches_all(rows.drop(i), terms))
        # invariants-end
        row = rows[i - 1]
        Assert(rows.drop(i - 1)[0] == row)
        Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
        all_clear = True
        j = len(terms)
        while j > 0:
            # invariants-start
            Invariant(0 <= j and j <= len(terms))
            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
            # invariants-end
            term = terms[j - 1]
            Assert(terms.drop(j - 1)[0] == term)
            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
            if not matches(row, term):
                all_clear = False
            j = j - 1
        Assert(all_clear == row_matches_all(row, terms))
        if all_clear:
            retained = True
        i = i - 1
    return retained
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-15022 (nagini). VERDICT: SOUND.

SPEC SHAPE: The frozen postcondition is a TOTAL FUNCTIONAL EQUALITY with an EMPTY precondition: `Ensures(Result() == some_row_matches_all(rows, terms))`. This pins the return value exactly, as a pure function of the inputs, on ALL inputs (no precondition to carve out a partial domain). It is the strongest possible spec shape: any verifying impl must be functionally identical to `some_row_matches_all` (exists-row, for-all-terms). This makes a verify⇏ correct break essentially impossible unless a wrong impl can still discharge the exact-equality postcondition, which cannot happen for a function that differs from `some_row_matches_all` on any input.

SAME-SPEC: all 8 files (pc + atk1..atk7) confirmed spec-byte-identical via `python -m swebench_unified.adversary same-spec nagini django__django-15022 <f>` (exit 0 each). Only the impl region was edited; axioms/@Pure predicates/Requires/Ensures byte-identical.

pc.py (positive control = exact correct model impl): EXIT 0 = CANDIDATE (verifies). Expected — it is the correct impl; establishes the toolchain verifies the gold model.
- atk1.py PREPATCH BUG (chained-filter: for-all-terms/exists-row, `retained` starts True, drop iff some term matched by no row): EXIT 2 = does not verify (spec rejected). Prepatch reproduced.
- atk2.py BOUNDARY off-by-one (i starts at len(rows)-1, last row never a witness): EXIT 2 = does not verify.
- atk3.py PARTIAL-DOMAIN (`if len(rows)>0: return True` else exact): EXIT 2 = does not verify.
- atk4.py CONTROL-FLOW-EFFECT (unconditional `return True`): EXIT 2 = does not verify.
- atk6.py WRONG-QUANTIFIER (exists-row exists-term: any row matches any term): EXIT 2 = does not verify.
- atk7.py FIRST-ROW-ONLY (only rows[0] can be the all-terms witness): EXIT 2 = does not verify.
- atk5.py UNGROUNDED-ORACLE ECHO (`return some_row_matches_all(rows, terms)`): EXIT 0 = CANDIDATE (shares spec AND verifies). This is functionally IDENTICAL to the gold combination semantics, so its faithful refined patch IS the gold single-filter-AND patch.

MANDATORY RESOLVE ON EVERY VERIFYING CANDIDATE: atk5 materialized to atk5_patch.diff (= gold patch verbatim from frozen dataset row) and executed through the official harness: `run_resolve('django__django-15022', patch)` => RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1. A resolving echo is NOT a weakness (2026-08-06 policy: candidate fails the gate only if its refined patch does NOT resolve). No verifying wrong impl exists whose faithful patch fails to resolve, so verify⇒correct is not falsified.

6 DISTINCT wrong impls exercised (partial-domain=atk3, boundary=atk2, control-flow-effect=atk4, ungrounded-oracle-echo=atk5 [resolves], prepatch=atk1, plus wrong-quantifier=atk6, first-row-only=atk7) — all 6 wrong ones rejected by the exact-equality postcondition; the 1 that verified is a correct echo that resolves.

REFINEMENT.MD A-LEG AUDIT: legs A1/A2 = R (terms/rows ↔ PSeq[int] id abstraction); A3 = modeling primitive (`matches` uninterpreted, contract is tautology Implies(R,R), proof uses no property of it — correctly NOT an axiom); A4 = A-reference (`some_row_matches_all`/`row_matches_all` deep-models the patched single `.filter(models.Q(*term_queries))` semantics; validated == real Django single-filter-AND by axiom_check.py); A5 = R/I (bool ↔ candidate membership in returned queryset). NO kind-3 (unexpressible-changed-op) leg; NO A-consumed axiom (meta axioms: []). A-reference correspondence verified: `python axiom_check.py` => exit 0, 'G-AX OK: some_row_matches_all == single-filter-AND on all match matrices up to 3x4 + 20000 fuzz + F2P scenarios; no library callee to axiomatize'. The A4 deep model faithfully corresponds to the real callee (queryset.filter over multi-valued relation) and matches the mapping.md §3.1 provenance.

CONCLUSION: The spec is a tight exact-equality postcondition that rejects every functionally-wrong impl and admits only functionally-gold impls (whose faithful patch resolves). Refinement legs are all R/A-reference/I with a G-AX-validated A-reference. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified: (1) model.py verifies under pinned Nagini (12.4s, exit 0). (2) Spec region delimited by post-conditions markers pins Result()==some_row_matches_all(rows,terms), i.e. exists-row for-all-terms retention. (3) I independently reproduced the REAL patched ModelAdmin.get_search_results semantics against an in-memory Django DB at base_commit with the single-AND-filter change (search_fields=['children__tag']): swap witness 'danielle 19' over children each covering one term => real drops candidate (False) = spec; single child clearing all terms => real keeps (True) = spec; split rows => False = spec; childless candidate + real term => False = spec. Every input where the patch's discriminating ∃∀-vs-∀∃ behavior manifests is faithfully modeled. (4) Bundle G-CONF ran 100082 real-ORM probes (exhaustive 3x4 + boundary + 95000 fuzz, seed 15022) with 0 disagreements between the contract-stripped impl shadow and the real patched callee; I confirmed the check is genuine (real ModelAdmin, real DB, materialization self-validated). The spec is not too strong / does not drift within its declared domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified byte-frozen (sha256 159437111659feac9dcabe5391b8fd6f3cfbc8b109c38280d38ed441181cda7d == meta region_hashes.spec_view). Impl region correctly elided to '...  # implementation elided — supplied by the consumer'; the one mechanism-revealing comment ('Skeleton of the patch: every per-term query is accumulated ... clears the whole conjunction', model.py:78-79) lives inside impl-start/impl-end and is NOT in the consumer view. Programmatic scan of the exact spec view finds NO repo machinery: queryset, models.Q, .filter, filter(, smart_split, orm_lookup, term_queries, construct_search, options.py, JOIN, accumulate, conjunction, append, contrib, admin — all absent. No file path, diff marker, patch.diff quote, or patched symbol appears (the only 'diff' substring is the English word 'different'). The spec view legitimately states the DESIRED behavior abstractly — postcondition Result() == some_row_matches_all(rows, terms) over opaque PSeq[int] ids and an uninterpreted matches relation, with prose describing exists-row-then-for-all-terms retention. The public problem_statement frames the issue PURELY as a performance/JOIN defect ('Unnecessary joins in admin changelist query', 'django/admin stalled', 'each word ... additional JOIN because of qs = qs.filter(...) pattern') and never states the retention/quantifier semantics. Revealing the target retention predicate is REQUIRED specification (G-DIFF must sense the change) — it exposes WHAT behavior to achieve, not the HOW of the Django code edit (term_queries=[] before the loop, .append(or_queries) inside, single post-loop queryset.filter(models.Q(*term_queries))). A consumer cannot reconstruct the gold patch from the spec view. Concur with recorded G-PANEL-3=pass.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
