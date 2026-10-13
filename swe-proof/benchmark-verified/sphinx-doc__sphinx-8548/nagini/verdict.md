# P2 adversarial audit — sphinx-doc__sphinx-8548

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -145,32 +145,9 @@
                                      ToSeq(edoc)))
     # post-conditions-end
     # impl-start
-    c = 0
-    while c < len(mro):
-        # invariants-start
-        Invariant(Acc(list_pred(mro), 1 / 2))
-        Invariant(Acc(list_pred(ens), 1 / 2))
-        Invariant(Acc(list_pred(enm), 1 / 2))
-        Invariant(Acc(list_pred(edoc), 1 / 2))
-        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
-        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
-        Invariant(0 <= c and c <= len(mro))
-        # every MRO class before `c` owned no record for `nm`
-        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), 0) ==
-                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), c))
-        # The loop consumes the termination obligation: len(mro) - c is the
-        # strictly decreasing, bounded-below measure.
-        Invariant(MustTerminate(len(mro) - c))
-        # invariants-end
-        owner = mro[c]
-        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
-                                 ToSeq(edoc), 0)
-        if found != ABSENT:
-            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                                ToSeq(edoc), c) == found)
-            return found
-        c = c + 1
-    return ABSENT
+    if len(mro) == 0:
+        return ABSENT
+    own = mro[0]
+    found = lookup_owner_doc(own, nm, ToSeq(ens), ToSeq(enm), ToSeq(edoc), 0)
+    return found
     # impl-end
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -145,32 +145,5 @@
                                      ToSeq(edoc)))
     # post-conditions-end
     # impl-start
-    c = 0
-    while c < len(mro):
-        # invariants-start
-        Invariant(Acc(list_pred(mro), 1 / 2))
-        Invariant(Acc(list_pred(ens), 1 / 2))
-        Invariant(Acc(list_pred(enm), 1 / 2))
-        Invariant(Acc(list_pred(edoc), 1 / 2))
-        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
-        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
-        Invariant(0 <= c and c <= len(mro))
-        # every MRO class before `c` owned no record for `nm`
-        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), 0) ==
-                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), c))
-        # The loop consumes the termination obligation: len(mro) - c is the
-        # strictly decreasing, bounded-below measure.
-        Invariant(MustTerminate(len(mro) - c))
-        # invariants-end
-        owner = mro[c]
-        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
-                                 ToSeq(edoc), 0)
-        if found != ABSENT:
-            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                                ToSeq(edoc), c) == found)
-            return found
-        c = c + 1
-    return ABSENT
+    return resolved_doc(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm), ToSeq(edoc))
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -145,32 +145,7 @@
                                      ToSeq(edoc)))
     # post-conditions-end
     # impl-start
-    c = 0
-    while c < len(mro):
-        # invariants-start
-        Invariant(Acc(list_pred(mro), 1 / 2))
-        Invariant(Acc(list_pred(ens), 1 / 2))
-        Invariant(Acc(list_pred(enm), 1 / 2))
-        Invariant(Acc(list_pred(edoc), 1 / 2))
-        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
-        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
-        Invariant(0 <= c and c <= len(mro))
-        # every MRO class before `c` owned no record for `nm`
-        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), 0) ==
-                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), c))
-        # The loop consumes the termination obligation: len(mro) - c is the
-        # strictly decreasing, bounded-below measure.
-        Invariant(MustTerminate(len(mro) - c))
-        # invariants-end
-        owner = mro[c]
-        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
-                                 ToSeq(edoc), 0)
-        if found != ABSENT:
-            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                                ToSeq(edoc), c) == found)
-            return found
-        c = c + 1
-    return ABSENT
+    if len(mro) == 0:
+        return ABSENT
+    return resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm), ToSeq(edoc), 1)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -146,8 +146,8 @@
     # post-conditions-end
     # impl-start
     c = 0
+    result = ABSENT
     while c < len(mro):
-        # invariants-start
         Invariant(Acc(list_pred(mro), 1 / 2))
         Invariant(Acc(list_pred(ens), 1 / 2))
         Invariant(Acc(list_pred(enm), 1 / 2))
@@ -155,22 +155,11 @@
         Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
         Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
         Invariant(0 <= c and c <= len(mro))
-        # every MRO class before `c` owned no record for `nm`
-        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), 0) ==
-                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), c))
-        # The loop consumes the termination obligation: len(mro) - c is the
-        # strictly decreasing, bounded-below measure.
         Invariant(MustTerminate(len(mro) - c))
-        # invariants-end
         owner = mro[c]
-        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
-                                 ToSeq(edoc), 0)
+        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm), ToSeq(edoc), 0)
         if found != ABSENT:
-            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                                ToSeq(edoc), c) == found)
-            return found
+            result = found
         c = c + 1
-    return ABSENT
+    return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -147,7 +147,6 @@
     # impl-start
     c = 0
     while c < len(mro):
-        # invariants-start
         Invariant(Acc(list_pred(mro), 1 / 2))
         Invariant(Acc(list_pred(ens), 1 / 2))
         Invariant(Acc(list_pred(enm), 1 / 2))
@@ -155,22 +154,7 @@
         Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
         Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
         Invariant(0 <= c and c <= len(mro))
-        # every MRO class before `c` owned no record for `nm`
-        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), 0) ==
-                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), c))
-        # The loop consumes the termination obligation: len(mro) - c is the
-        # strictly decreasing, bounded-below measure.
         Invariant(MustTerminate(len(mro) - c))
-        # invariants-end
-        owner = mro[c]
-        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
-                                 ToSeq(edoc), 0)
-        if found != ABSENT:
-            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                                ToSeq(edoc), c) == found)
-            return found
         c = c + 1
     return ABSENT
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -145,32 +145,18 @@
                                      ToSeq(edoc)))
     # post-conditions-end
     # impl-start
-    c = 0
-    while c < len(mro):
-        # invariants-start
+    j = 0
+    while j < len(ens):
         Invariant(Acc(list_pred(mro), 1 / 2))
         Invariant(Acc(list_pred(ens), 1 / 2))
         Invariant(Acc(list_pred(enm), 1 / 2))
         Invariant(Acc(list_pred(edoc), 1 / 2))
         Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
         Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
-        Invariant(0 <= c and c <= len(mro))
-        # every MRO class before `c` owned no record for `nm`
-        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), 0) ==
-                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), c))
-        # The loop consumes the termination obligation: len(mro) - c is the
-        # strictly decreasing, bounded-below measure.
-        Invariant(MustTerminate(len(mro) - c))
-        # invariants-end
-        owner = mro[c]
-        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
-                                 ToSeq(edoc), 0)
-        if found != ABSENT:
-            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                                ToSeq(edoc), c) == found)
-            return found
-        c = c + 1
+        Invariant(0 <= j and j <= len(ens))
+        Invariant(MustTerminate(len(ens) - j))
+        if enm[j] == nm:
+            return edoc[j]
+        j = j + 1
     return ABSENT
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -145,32 +145,7 @@
                                      ToSeq(edoc)))
     # post-conditions-end
     # impl-start
-    c = 0
-    while c < len(mro):
-        # invariants-start
-        Invariant(Acc(list_pred(mro), 1 / 2))
-        Invariant(Acc(list_pred(ens), 1 / 2))
-        Invariant(Acc(list_pred(enm), 1 / 2))
-        Invariant(Acc(list_pred(edoc), 1 / 2))
-        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
-        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
-        Invariant(0 <= c and c <= len(mro))
-        # every MRO class before `c` owned no record for `nm`
-        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), 0) ==
-                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                               ToSeq(edoc), c))
-        # The loop consumes the termination obligation: len(mro) - c is the
-        # strictly decreasing, bounded-below measure.
-        Invariant(MustTerminate(len(mro) - c))
-        # invariants-end
-        owner = mro[c]
-        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
-                                 ToSeq(edoc), 0)
-        if found != ABSENT:
-            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
-                                ToSeq(edoc), c) == found)
-            return found
-        c = c + 1
-    return ABSENT
+    if len(mro) == 2:
+        return lookup_owner_doc(mro[0], nm, ToSeq(ens), ToSeq(enm), ToSeq(edoc), 0)
+    return resolved_doc(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm), ToSeq(edoc))
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8548.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the documented members of a class are gathered with inheritance enabled,
  the comment-derived documentation of a data attribute must be found for the
  attribute no matter WHICH class along the class's method-resolution order
  (MRO) the attribute's documentation was recorded under -- not only the
  documentation recorded directly under the class itself.

  A documentation record is keyed by a pair (owner, attribute-name), where
  `owner` identifies the class whose source the documentation comment was read
  from. The resolution for a queried attribute name is:

    * the name resolves to a documentation body exactly when some record names
      it whose `owner` is one of the classes on the MRO (the class itself OR
      any of its base classes) -- so an attribute documented only on a base
      class still resolves;

    * when several records name the attribute under different MRO classes, the
      record whose `owner` sits EARLIEST on the MRO wins (the class itself
      overrides its bases); among records of that same owner, the first-recorded
      one wins;

    * if no MRO class owns a matching record, the name resolves to the absent
      marker.

  Resolution is a bounded scan of the finite MRO against the finite record
  table: the operation MUST terminate and return its answer (a total-
  correctness obligation, carried as MustTerminate in the precondition).

  The discriminating guarantee: an attribute documented ONLY on a base class
  resolves (to that base class's documentation), and an attribute documented on
  both the class and a base class resolves to the class's own documentation. A
  resolution that matches records only against the class's own `owner` does NOT
  satisfy this -- it leaves every base-only attribute absent.

Identifiers (class owners, attribute names, documentation bodies) are modelled
as integer codes; the MRO and the record table are `List[int]` carriers, with
the specification carried by `PSeq[int]` via `ToSeq`. No callee is axiomatized:
the membership/precedence resolution is the changed decision logic and is
modelled deeply (pure `resolve_from` / `lookup_owner_doc`), paired with a
verified nested-loop implementation that mirrors it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. The operation that changed -- the rule deciding which
# documentation record resolves a given attribute name (own-owner match vs.
# any-MRO-owner match, with earliest-MRO-owner precedence) -- is the decision
# logic under specification, so it is modelled DEEPLY here (the pure
# `resolve_from` / `lookup_owner_doc` spec and the verified nested loop), never
# hidden behind an axiom.
# axioms-end

# pure-start
ABSENT = -1  # "no documentation record resolves this name"

@Pure
def lookup_owner_doc(owner: int, nm: int, ens: PSeq[int], enm: PSeq[int],
                     edoc: PSeq[int], j: int) -> int:
    """Documentation body of the first record (scanning entries `j, j+1, ...`
    to the end) whose owner is `owner` and whose attribute-name is `nm`;
    `ABSENT` if none. Front-recursive over the entry suffix start `j` so one
    unfold is available per inner-loop step."""
    Requires(len(ens) == len(enm) and len(enm) == len(edoc))
    Requires(0 <= j and j <= len(ens))
    if j == len(ens):
        return ABSENT
    if ens[j] == owner and enm[j] == nm:
        return edoc[j]
    return lookup_owner_doc(owner, nm, ens, enm, edoc, j + 1)

@Pure
def resolve_from(nm: int, mro: PSeq[int], ens: PSeq[int], enm: PSeq[int],
                 edoc: PSeq[int], c: int) -> int:
    """Documentation body resolving attribute name `nm`, considering MRO
    classes `mro[c], mro[c+1], ...` to the end: take the first MRO class (from
    `c`) that owns a record named `nm`, and within it that record's doc body;
    `ABSENT` if no such MRO class owns one. Front-recursive over the MRO start
    `c`, so the earliest MRO class wins."""
    Requires(len(ens) == len(enm) and len(enm) == len(edoc))
    Requires(0 <= c and c <= len(mro))
    if c == len(mro):
        return ABSENT
    if lookup_owner_doc(mro[c], nm, ens, enm, edoc, 0) != ABSENT:
        return lookup_owner_doc(mro[c], nm, ens, enm, edoc, 0)
    return resolve_from(nm, mro, ens, enm, edoc, c + 1)

@Pure
def resolved_doc(nm: int, mro: PSeq[int], ens: PSeq[int], enm: PSeq[int],
                 edoc: PSeq[int]) -> int:
    """The documentation body resolving attribute name `nm` under the full MRO,
    or `ABSENT` if `nm` is documented on no MRO class."""
    Requires(len(ens) == len(enm) and len(enm) == len(edoc))
    return resolve_from(nm, mro, ens, enm, edoc, 0)
# pure-end

def resolve_attribute_doc(nm: int, mro: List[int], ens: List[int],
                          enm: List[int], edoc: List[int]) -> int:
    """Resolve the documentation body of attribute name `nm` under the MRO-aware
    lookup. `mro` is the method-resolution order as owner codes (the class first,
    then its bases). `ens`/`enm`/`edoc` are the parallel record table: record `j`
    has owner `ens[j]`, attribute-name `enm[j]`, documentation body `edoc[j]`.
    Returns the resolving documentation body -- the body recorded under the
    earliest MRO class that owns a matching record (and the first such record for
    that class) -- or `ABSENT` if no MRO class owns a record naming `nm`.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(mro), 1 / 2))
    Requires(Acc(list_pred(ens), 1 / 2))
    Requires(Acc(list_pred(enm), 1 / 2))
    Requires(Acc(list_pred(edoc), 1 / 2))
    Requires(len(ens) == len(enm))
    Requires(len(enm) == len(edoc))
    # TERMINATION: resolving one name against the finite MRO and the finite
    # record table is a bounded scan and must actually ANSWER. Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. `while True: pass` or bare
    # self-recursion before the return) satisfies every Ensures vacuously;
    # the real collection loop always returns its members.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(mro), 1 / 2))
    Ensures(Acc(list_pred(ens), 1 / 2))
    Ensures(Acc(list_pred(enm), 1 / 2))
    Ensures(Acc(list_pred(edoc), 1 / 2))
    Ensures(len(ToSeq(ens)) == len(ToSeq(enm)))
    Ensures(len(ToSeq(enm)) == len(ToSeq(edoc)))
    # The resolved documentation body is exactly the earliest-MRO-owner,
    # first-record resolution of the name. This pins both the membership
    # (base-class owners count) and the override precedence.
    Ensures(Result() == resolved_doc(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                                     ToSeq(edoc)))
    # post-conditions-end
    # impl-start
    c = 0
    while c < len(mro):
        # invariants-start
        Invariant(Acc(list_pred(mro), 1 / 2))
        Invariant(Acc(list_pred(ens), 1 / 2))
        Invariant(Acc(list_pred(enm), 1 / 2))
        Invariant(Acc(list_pred(edoc), 1 / 2))
        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
        Invariant(0 <= c and c <= len(mro))
        # every MRO class before `c` owned no record for `nm`
        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), 0) ==
                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), c))
        # The loop consumes the termination obligation: len(mro) - c is the
        # strictly decreasing, bounded-below measure.
        Invariant(MustTerminate(len(mro) - c))
        # invariants-end
        owner = mro[c]
        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
                                 ToSeq(edoc), 0)
        if found != ABSENT:
            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                                ToSeq(edoc), c) == found)
            return found
        c = c + 1
    return ABSENT
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Project root (SBU_BENCHMARK_DIR=benchmark-verified); verifier env. Bundle has patch_diff='gold patch verbatim' placeholder in meta.json; gold patch materialized from data/swe_bench_verified/test.jsonl.

STRUCTURE: postcondition Ensures(Result()==resolved_doc(nm,ToSeq(mro),ToSeq(ens),ToSeq(enm),ToSeq(edoc))) is a FULLY FUNCTIONAL spec — it pins the exact return value on every input. Any same-spec impl that verifies must equal the oracle resolved_doc (earliest-MRO-owner / first-record resolution), hence is behaviorally correct. This is why only the echo verifies.

atk_1.py PREPATCH (match only own owner mro[0]): weakness -> NOT-A-COUNTEREXAMPLE, does not verify (exit 2). PREPATCH REPRODUCED.
- atk_2.py ECHO/ungrounded-oracle (return resolved_doc(...) directly): weakness -> CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (exit 0).
- atk_3.py BOUNDARY off-by-one (resolve_from start c=1, skip subject): does not verify (exit 2).
- atk_4.py CONTROL-FLOW/wrong-precedence (last owner match wins, deepest base): does not verify (exit 2).
- atk_5.py CONTROL-FLOW-EFFECT (loop but always return ABSENT): does not verify (exit 2).
- atk_6.py UNGROUNDED over-keep (first record naming nm, ignore MRO owner membership): does not verify (exit 2).
- atk_7.py PARTIAL-DOMAIN (prepatch own-owner-only for len(mro)==2, else resolved_doc): does not verify (exit 2).

CANDIDATE RESOLVE (MANDATORY): atk_2's faithful refined patch = the gold MRO-walking patch. The echo returns exactly resolved_doc which by G-AX equals the real patched get_class_members loop (validated live below), so the faithful patch IS the gold patch. Ran official harness: ... python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path <preds> --run_id sbu-audit-direct-8548 --namespace swebench --instance_image_tag latest --instance_ids sphinx-doc__sphinx-8548 RESULT: Instances resolved: 1. report.json resolved=true; FAIL_TO_PASS {test_inherited_instance_variable: success}; PASS_TO_PASS all 5 success (test_classes, test_instance_variable, test_decorators, test_slots_attribute, test_show_inheritance_for_subclass_of_generic_type).

Report at experiments/logs/run_evaluation/sbu-audit-direct-8548/sbu_patch/sphinx-doc__sphinx-8548/report.json. (Note: the swebench_unified.harness.run_resolve wrapper returned completed=False twice due to a report-path lookup race under concurrent contention; the direct run_evaluation invocation completed cleanly and is the authoritative verdict. An independent prior concurrent runs run kikwy8rc-atk5-b1 on the identical patch also recorded resolved=True.) => The sole verifying same-spec impl RESOLVES; verify does NOT admit an incorrect impl here.

A-LEG / refinement.md AUDIT: legs A1=R, A2=A-reference, A3=A-reference, A4=I, A5=R, A6=I, B1=R. No kind-3 (unexpressible-changed-op) leg. axioms=[] in meta.json — genuinely no consumed @ContractOnly; the changed decision logic (MRO-wide membership + earliest-MRO-class precedence + first-record-per-owner) is modeled DEEPLY as pure resolve_from/lookup_owner_doc and consumed by the impl. A-reference correspondence (deep model == real patched loop) validated by axiom_check.py: exit 0 — 'resolve_from deep model == patched collection loop on 8 boundary + 20000 fuzz hierarchies' + record-table abstraction grounded against real sphinx.pycode parser keys {(Foo,attr1),(Foo,attr2),(Bar,attr2),(Bar,attr3)} (real-get_class_members end-to-end leg auto-skipped on host, container G-AX covers it). Model↔patch correspondence holds: mro<->getmro(subject); (ens,enm,edoc)<->(owner-qualname,name)->doc from ModuleAnalyzer.attr_docs; ns==qualname per MRO class <-> ens[j]==mro[c]; name-not-in-members first-wins <-> lookup_owner_doc first match + resolve_from front-recursion; ABSENT=-1 <-> name absent from members.

Positive control (bundle model.py verbatim): verifies (18.15s, exit 0). MustTerminate obligation present and satisfied by the loop measure len(mro)-c.

VERDICT: SOUND. 7 same-spec attacks run (6 distinct genuinely-wrong impls all rejected by the functional postcondition; the sole verifying impl is the behaviorally-correct echo whose materialized faithful patch RESOLVES). No verifying wrong impl exists; verify does not overshoot correct for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8548.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the documented members of a class are gathered with inheritance enabled,
  the comment-derived documentation of a data attribute must be found for the
  attribute no matter WHICH class along the class's method-resolution order
  (MRO) the attribute's documentation was recorded under -- not only the
  documentation recorded directly under the class itself.

  A documentation record is keyed by a pair (owner, attribute-name), where
  `owner` identifies the class whose source the documentation comment was read
  from. The resolution for a queried attribute name is:

    * the name resolves to a documentation body exactly when some record names
      it whose `owner` is one of the classes on the MRO (the class itself OR
      any of its base classes) -- so an attribute documented only on a base
      class still resolves;

    * when several records name the attribute under different MRO classes, the
      record whose `owner` sits EARLIEST on the MRO wins (the class itself
      overrides its bases); among records of that same owner, the first-recorded
      one wins;

    * if no MRO class owns a matching record, the name resolves to the absent
      marker.

  Resolution is a bounded scan of the finite MRO against the finite record
  table: the operation MUST terminate and return its answer (a total-
  correctness obligation, carried as MustTerminate in the precondition).

  The discriminating guarantee: an attribute documented ONLY on a base class
  resolves (to that base class's documentation), and an attribute documented on
  both the class and a base class resolves to the class's own documentation. A
  resolution that matches records only against the class's own `owner` does NOT
  satisfy this -- it leaves every base-only attribute absent.

Identifiers (class owners, attribute names, documentation bodies) are modelled
as integer codes; the MRO and the record table are `List[int]` carriers, with
the specification carried by `PSeq[int]` via `ToSeq`. No callee is axiomatized:
the membership/precedence resolution is the changed decision logic and is
modelled deeply (pure `resolve_from` / `lookup_owner_doc`), paired with a
verified nested-loop implementation that mirrors it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. The operation that changed -- the rule deciding which
# documentation record resolves a given attribute name (own-owner match vs.
# any-MRO-owner match, with earliest-MRO-owner precedence) -- is the decision
# logic under specification, so it is modelled DEEPLY here (the pure
# `resolve_from` / `lookup_owner_doc` spec and the verified nested loop), never
# hidden behind an axiom.
# axioms-end

# pure-start
ABSENT = -1  # "no documentation record resolves this name"

@Pure
def lookup_owner_doc(owner: int, nm: int, ens: PSeq[int], enm: PSeq[int],
                     edoc: PSeq[int], j: int) -> int:
    """Documentation body of the first record (scanning entries `j, j+1, ...`
    to the end) whose owner is `owner` and whose attribute-name is `nm`;
    `ABSENT` if none. Front-recursive over the entry suffix start `j` so one
    unfold is available per inner-loop step."""
    Requires(len(ens) == len(enm) and len(enm) == len(edoc))
    Requires(0 <= j and j <= len(ens))
    if j == len(ens):
        return ABSENT
    if ens[j] == owner and enm[j] == nm:
        return edoc[j]
    return lookup_owner_doc(owner, nm, ens, enm, edoc, j + 1)

@Pure
def resolve_from(nm: int, mro: PSeq[int], ens: PSeq[int], enm: PSeq[int],
                 edoc: PSeq[int], c: int) -> int:
    """Documentation body resolving attribute name `nm`, considering MRO
    classes `mro[c], mro[c+1], ...` to the end: take the first MRO class (from
    `c`) that owns a record named `nm`, and within it that record's doc body;
    `ABSENT` if no such MRO class owns one. Front-recursive over the MRO start
    `c`, so the earliest MRO class wins."""
    Requires(len(ens) == len(enm) and len(enm) == len(edoc))
    Requires(0 <= c and c <= len(mro))
    if c == len(mro):
        return ABSENT
    if lookup_owner_doc(mro[c], nm, ens, enm, edoc, 0) != ABSENT:
        return lookup_owner_doc(mro[c], nm, ens, enm, edoc, 0)
    return resolve_from(nm, mro, ens, enm, edoc, c + 1)

@Pure
def resolved_doc(nm: int, mro: PSeq[int], ens: PSeq[int], enm: PSeq[int],
                 edoc: PSeq[int]) -> int:
    """The documentation body resolving attribute name `nm` under the full MRO,
    or `ABSENT` if `nm` is documented on no MRO class."""
    Requires(len(ens) == len(enm) and len(enm) == len(edoc))
    return resolve_from(nm, mro, ens, enm, edoc, 0)
# pure-end

def resolve_attribute_doc(nm: int, mro: List[int], ens: List[int],
                          enm: List[int], edoc: List[int]) -> int:
    """Resolve the documentation body of attribute name `nm` under the MRO-aware
    lookup. `mro` is the method-resolution order as owner codes (the class first,
    then its bases). `ens`/`enm`/`edoc` are the parallel record table: record `j`
    has owner `ens[j]`, attribute-name `enm[j]`, documentation body `edoc[j]`.
    Returns the resolving documentation body -- the body recorded under the
    earliest MRO class that owns a matching record (and the first such record for
    that class) -- or `ABSENT` if no MRO class owns a record naming `nm`.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(mro), 1 / 2))
    Requires(Acc(list_pred(ens), 1 / 2))
    Requires(Acc(list_pred(enm), 1 / 2))
    Requires(Acc(list_pred(edoc), 1 / 2))
    Requires(len(ens) == len(enm))
    Requires(len(enm) == len(edoc))
    # TERMINATION: resolving one name against the finite MRO and the finite
    # record table is a bounded scan and must actually ANSWER. Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. `while True: pass` or bare
    # self-recursion before the return) satisfies every Ensures vacuously;
    # the real collection loop always returns its members.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(mro), 1 / 2))
    Ensures(Acc(list_pred(ens), 1 / 2))
    Ensures(Acc(list_pred(enm), 1 / 2))
    Ensures(Acc(list_pred(edoc), 1 / 2))
    Ensures(len(ToSeq(ens)) == len(ToSeq(enm)))
    Ensures(len(ToSeq(enm)) == len(ToSeq(edoc)))
    # The resolved documentation body is exactly the earliest-MRO-owner,
    # first-record resolution of the name. This pins both the membership
    # (base-class owners count) and the override precedence.
    Ensures(Result() == resolved_doc(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                                     ToSeq(edoc)))
    # post-conditions-end
    # impl-start
    c = 0
    while c < len(mro):
        # invariants-start
        Invariant(Acc(list_pred(mro), 1 / 2))
        Invariant(Acc(list_pred(ens), 1 / 2))
        Invariant(Acc(list_pred(enm), 1 / 2))
        Invariant(Acc(list_pred(edoc), 1 / 2))
        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
        Invariant(0 <= c and c <= len(mro))
        # every MRO class before `c` owned no record for `nm`
        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), 0) ==
                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), c))
        # The loop consumes the termination obligation: len(mro) - c is the
        # strictly decreasing, bounded-below measure.
        Invariant(MustTerminate(len(mro) - c))
        # invariants-end
        owner = mro[c]
        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
                                 ToSeq(edoc), 0)
        if found != ABSENT:
            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                                ToSeq(edoc), c) == found)
            return found
        c = c + 1
    return ABSENT
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Project root (SBU_BENCHMARK_DIR=benchmark-verified); verifier env. Bundle has patch_diff='gold patch verbatim' placeholder in meta.json; gold patch materialized from data/swe_bench_verified/test.jsonl.

STRUCTURE: postcondition Ensures(Result()==resolved_doc(nm,ToSeq(mro),ToSeq(ens),ToSeq(enm),ToSeq(edoc))) is a FULLY FUNCTIONAL spec — it pins the exact return value on every input. Any same-spec impl that verifies must equal the oracle resolved_doc (earliest-MRO-owner / first-record resolution), hence is behaviorally correct. This is why only the echo verifies.

atk_1.py PREPATCH (match only own owner mro[0]): weakness -> NOT-A-COUNTEREXAMPLE, does not verify (exit 2). PREPATCH REPRODUCED.
- atk_2.py ECHO/ungrounded-oracle (return resolved_doc(...) directly): weakness -> CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (exit 0).
- atk_3.py BOUNDARY off-by-one (resolve_from start c=1, skip subject): does not verify (exit 2).
- atk_4.py CONTROL-FLOW/wrong-precedence (last owner match wins, deepest base): does not verify (exit 2).
- atk_5.py CONTROL-FLOW-EFFECT (loop but always return ABSENT): does not verify (exit 2).
- atk_6.py UNGROUNDED over-keep (first record naming nm, ignore MRO owner membership): does not verify (exit 2).
- atk_7.py PARTIAL-DOMAIN (prepatch own-owner-only for len(mro)==2, else resolved_doc): does not verify (exit 2).

CANDIDATE RESOLVE (MANDATORY): atk_2's faithful refined patch = the gold MRO-walking patch. The echo returns exactly resolved_doc which by G-AX equals the real patched get_class_members loop (validated live below), so the faithful patch IS the gold patch. Ran official harness: ... python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path <preds> --run_id sbu-audit-direct-8548 --namespace swebench --instance_image_tag latest --instance_ids sphinx-doc__sphinx-8548 RESULT: Instances resolved: 1. report.json resolved=true; FAIL_TO_PASS {test_inherited_instance_variable: success}; PASS_TO_PASS all 5 success (test_classes, test_instance_variable, test_decorators, test_slots_attribute, test_show_inheritance_for_subclass_of_generic_type).

Report at experiments/logs/run_evaluation/sbu-audit-direct-8548/sbu_patch/sphinx-doc__sphinx-8548/report.json. (Note: the swebench_unified.harness.run_resolve wrapper returned completed=False twice due to a report-path lookup race under concurrent contention; the direct run_evaluation invocation completed cleanly and is the authoritative verdict. An independent prior concurrent runs run kikwy8rc-atk5-b1 on the identical patch also recorded resolved=True.) => The sole verifying same-spec impl RESOLVES; verify does NOT admit an incorrect impl here.

A-LEG / refinement.md AUDIT: legs A1=R, A2=A-reference, A3=A-reference, A4=I, A5=R, A6=I, B1=R. No kind-3 (unexpressible-changed-op) leg. axioms=[] in meta.json — genuinely no consumed @ContractOnly; the changed decision logic (MRO-wide membership + earliest-MRO-class precedence + first-record-per-owner) is modeled DEEPLY as pure resolve_from/lookup_owner_doc and consumed by the impl. A-reference correspondence (deep model == real patched loop) validated by axiom_check.py: exit 0 — 'resolve_from deep model == patched collection loop on 8 boundary + 20000 fuzz hierarchies' + record-table abstraction grounded against real sphinx.pycode parser keys {(Foo,attr1),(Foo,attr2),(Bar,attr2),(Bar,attr3)} (real-get_class_members end-to-end leg auto-skipped on host, container G-AX covers it). Model↔patch correspondence holds: mro<->getmro(subject); (ens,enm,edoc)<->(owner-qualname,name)->doc from ModuleAnalyzer.attr_docs; ns==qualname per MRO class <-> ens[j]==mro[c]; name-not-in-members first-wins <-> lookup_owner_doc first match + resolve_from front-recursion; ABSENT=-1 <-> name absent from members.

Positive control (bundle model.py verbatim): verifies (18.15s, exit 0). MustTerminate obligation present and satisfied by the loop measure len(mro)-c.

VERDICT: SOUND. 7 same-spec attacks run (6 distinct genuinely-wrong impls all rejected by the functional postcondition; the sole verifying impl is the behaviorally-correct echo whose materialized faithful patch RESOLVES). No verifying wrong impl exists; verify does not overshoot correct for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) lens for sphinx-doc__sphinx-8548 nagini. The modeled function resolve_attribute_doc pins Result() == resolved_doc(nm, mro, ens, enm, edoc): the earliest-MRO-owner, first-record resolution of an attribute's documentation body. I checked this against the REAL patched callee get_class_members (post gold patch) and found no divergence within the modeled domain:

1. nagini_verify.sh: 'Verification successful' (18s) — spec is satisfiable by the impl.
2. G-AX fuzz equivalence (axiom_check.fuzz_loop_equivalence): model's resolve_from == faithful transcription of the patched nested loop on 8 boundary + 20000 random hierarchies. PASS.
3. check_real_parser(): PASS — the (owner-qualname, name)->doc record-table abstraction matches real sphinx.pycode.parser output; F2P Bar(Foo) attr1/attr2/attr3 resolve as modeled.
4. check_real_sphinx() (ran with docutils 0.16 venv against the actually-patched get_class_members): PASS — attr1(base-only)->foo, attr2(overridden)->bar, attr3(own)->bar.
5. Independent adversarial probe I authored: diamond MRO D(C), C(A,B) with base-only attrs a1/b1, own c1/d1, and an overridden 'shared' documented on A/B/C. Model resolution == real get_class_members exactly: real MRO [D,C,A,B,object], shared->'doc C.shared' (earliest MRO owner wins), all base-only attrs resolve. No divergence.

The spec is if anything NARROWER than reality, not stronger: mapping.md §2 openly discloses the abstraction models only the comment-documented instance-attribute branch and assumes no annotation/comment name collision across MRO classes (the annotation-only branch is omitted). That is a domain restriction that never forces the model to demand an answer the real code would not produce inside the modeled domain — it cannot make the spec 'too strong'. MustTerminate(2) is faithful: the real loop over two finite carriers (getmro tuple, attr_docs dict) always returns. No consumed @ContractOnly axiom, so no axiom-soundness over-trust point. Verdict: FAITHFUL — no diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures). Manual semantic review of the full spec view (docstring + comments + abstract model) confirms NO leakage of the gold edit beyond the public problem_statement:

- Public problem_statement already discloses the substance: bug is that autodoc inherited-members fails for inherited data-member attributes because the docstring is searched by an (namespace, attrname) key that 'doesn't check for baseclass-namespace'. It thereby already asks for the fix = also check base-class namespaces (walk the MRO).
- The spec view restates exactly that DESIRED behaviour in abstract terms: a documentation record keyed by (owner, attribute-name), resolved over the whole MRO (class + bases), earliest-MRO-owner precedence, base-only attributes must resolve. This is the problem_statement's own '(namespace, attrname) key / check baseclass-namespace' framing made precise -- not new gold-edit information.
- No patched file paths present (sphinx/ext/autodoc/importer.py, __init__.py absent; L2 clean).
- No patched repo symbols leak: changed def/class symbols are {get_class_members, add_directive_header}; neither appears in spec view. The gold-edit-specific identifiers (ModuleAnalyzer, PycodeError, analyzer param, getmro, attr_docs, safe_getattr, qualname) appear ONLY in refinement.md/mapping.md (audit docs, NOT part of the consumer spec view). The spec view uses invented abstract names (resolve_from, lookup_owner_doc, resolve_attribute_doc) over integer-code carriers.
- No reproduced gold-diff lines (all changed lines are Python impl over real repo objects; none reproduced verbatim in the abstract-int model), no diff markers, no bug/fix narration (L1/L3 clean).
- The mechanical shape of the actual edit (dropping the analyzer argument, building ModuleAnalyzer.for_module per MRO class, the __init__.py signature follow-through) is NOT disclosed anywhere in the spec view.

Conclusion: the spec view is a faithful behavioural specification of what the public task already requests, expressed over abstract carriers; it leaks nothing about the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.