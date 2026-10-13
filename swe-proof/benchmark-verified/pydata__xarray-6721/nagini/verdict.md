# P2 adversarial audit — pydata__xarray-6721

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch.py`, `atk2_echo_after.py`, `atk3_echo_before.py`, `atk5_offbyone.py`, `atk6_cfmaterialise.py`, `atk7_partialdomain.py`, `atk8_ungrounded.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk4_directfield.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -197,10 +197,9 @@
             [[entries[k]]])))
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == 2 * i)
-        Invariant(loads == 0)
-        # every entry remains intact: only the in-place underlying view is used,
-        # so no payload is ever pulled into memory
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
+        # only the not-yet-inspected entries remain intact: the pre-patch skeleton
+        # has already materialised (consuming the token of) entries [0, i).
+        Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(entries),
             payload_intact(entries[k])), [[entries[k]]])))
         Invariant(Forall(int, lambda k: (
             Implies(0 <= k and k < i,
@@ -212,9 +211,11 @@
             [[entries[k]]])))
         # invariants-end
         e = entries[i]
-        # Inspect the UNDERLYING store only -- this forces no load even when the
-        # entry is lazily backed, and grants the in-place token for this entry.
-        probe = inspect_underlying(e)
+        # Pre-patch skeleton: the block status is inspected via the MATERIALISED
+        # payload, which forces a load on every lazily-backed entry and CONSUMES
+        # its `payload_intact` token -- so neither the loads-tally clause nor the
+        # `payload_intact` postcondition can be re-established (G-DIFF).
+        probe = inspect_materialised(e)
         loads = loads + probe[1]
         if probe[0]:
             result = result + [e.axis, e.length]
```

Attack 2 — `atk2_echo_after.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,8 +198,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == 2 * i)
         Invariant(loads == 0)
-        # every entry remains intact: only the in-place underlying view is used,
-        # so no payload is ever pulled into memory
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
             payload_intact(entries[k])), [[entries[k]]])))
         Invariant(Forall(int, lambda k: (
@@ -212,10 +210,9 @@
             [[entries[k]]])))
         # invariants-end
         e = entries[i]
-        # Inspect the UNDERLYING store only -- this forces no load even when the
-        # entry is lazily backed, and grants the in-place token for this entry.
         probe = inspect_underlying(e)
-        loads = loads + probe[1]
+        # ALSO materialise (the buggy v.data read) -- consumes the token
+        junk = inspect_materialised(e)
         if probe[0]:
             result = result + [e.axis, e.length]
         else:
```

Attack 3 — `atk3_echo_before.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,8 +198,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == 2 * i)
         Invariant(loads == 0)
-        # every entry remains intact: only the in-place underlying view is used,
-        # so no payload is ever pulled into memory
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
             payload_intact(entries[k])), [[entries[k]]])))
         Invariant(Forall(int, lambda k: (
@@ -212,11 +210,8 @@
             [[entries[k]]])))
         # invariants-end
         e = entries[i]
-        # Inspect the UNDERLYING store only -- this forces no load even when the
-        # entry is lazily backed, and grants the in-place token for this entry.
-        probe = inspect_underlying(e)
-        loads = loads + probe[1]
-        if probe[0]:
+        junk = inspect_materialised(e)
+        if e.block_backed:
             result = result + [e.axis, e.length]
         else:
             result = result + [-1, -1]
```

Attack 4 — `atk4_directfield.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -198,8 +198,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == 2 * i)
         Invariant(loads == 0)
-        # every entry remains intact: only the in-place underlying view is used,
-        # so no payload is ever pulled into memory
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
             payload_intact(entries[k])), [[entries[k]]])))
         Invariant(Forall(int, lambda k: (
@@ -212,11 +210,7 @@
             [[entries[k]]])))
         # invariants-end
         e = entries[i]
-        # Inspect the UNDERLYING store only -- this forces no load even when the
-        # entry is lazily backed, and grants the in-place token for this entry.
-        probe = inspect_underlying(e)
-        loads = loads + probe[1]
-        if probe[0]:
+        if e.block_backed:
             result = result + [e.axis, e.length]
         else:
             result = result + [-1, -1]
```

Attack 5 — `atk5_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -188,7 +188,6 @@
     loads = 0
     i = 0
     while i < len(entries):
-        # invariants-start
         Invariant(Acc(list_pred(entries), 1 / 2))
         Invariant(0 <= i and i <= len(entries))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
@@ -196,30 +195,10 @@
             and Acc(entries[k].axis, 1 / 8) and Acc(entries[k].length, 1 / 8)),
             [[entries[k]]])))
         Invariant(Acc(list_pred(result)))
-        Invariant(len(result) == 2 * i)
-        Invariant(loads == 0)
-        # every entry remains intact: only the in-place underlying view is used,
-        # so no payload is ever pulled into memory
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
-            payload_intact(entries[k])), [[entries[k]]])))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < i,
-                Implies(not entries[k].block_backed,
-                        result[2 * k] == -1 and result[2 * k + 1] == -1)
-                and Implies(entries[k].block_backed,
-                        result[2 * k] == entries[k].axis
-                        and result[2 * k + 1] == entries[k].length)),
-            [[entries[k]]])))
-        # invariants-end
+        Invariant(len(result) == i)
         e = entries[i]
-        # Inspect the UNDERLYING store only -- this forces no load even when the
-        # entry is lazily backed, and grants the in-place token for this entry.
         probe = inspect_underlying(e)
-        loads = loads + probe[1]
-        if probe[0]:
-            result = result + [e.axis, e.length]
-        else:
-            result = result + [-1, -1]
+        result = result + [e.axis]
         i = i + 1
     result = result + [loads]
     return result
```

Attack 6 — `atk6_cfmaterialise.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,8 +198,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == 2 * i)
         Invariant(loads == 0)
-        # every entry remains intact: only the in-place underlying view is used,
-        # so no payload is ever pulled into memory
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
             payload_intact(entries[k])), [[entries[k]]])))
         Invariant(Forall(int, lambda k: (
@@ -212,13 +210,11 @@
             [[entries[k]]])))
         # invariants-end
         e = entries[i]
-        # Inspect the UNDERLYING store only -- this forces no load even when the
-        # entry is lazily backed, and grants the in-place token for this entry.
-        probe = inspect_underlying(e)
-        loads = loads + probe[1]
-        if probe[0]:
+        if e.block_backed:
+            probe = inspect_materialised(e)
             result = result + [e.axis, e.length]
         else:
+            probe2 = inspect_underlying(e)
             result = result + [-1, -1]
         i = i + 1
     result = result + [loads]
```

Attack 7 — `atk7_partialdomain.py` → rejected (same spec, does not verify — good)

```diff
@@ -188,7 +188,6 @@
     loads = 0
     i = 0
     while i < len(entries):
-        # invariants-start
         Invariant(Acc(list_pred(entries), 1 / 2))
         Invariant(0 <= i and i <= len(entries))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
@@ -197,29 +196,9 @@
             [[entries[k]]])))
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == 2 * i)
-        Invariant(loads == 0)
-        # every entry remains intact: only the in-place underlying view is used,
-        # so no payload is ever pulled into memory
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
-            payload_intact(entries[k])), [[entries[k]]])))
-        Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < i,
-                Implies(not entries[k].block_backed,
-                        result[2 * k] == -1 and result[2 * k + 1] == -1)
-                and Implies(entries[k].block_backed,
-                        result[2 * k] == entries[k].axis
-                        and result[2 * k + 1] == entries[k].length)),
-            [[entries[k]]])))
-        # invariants-end
         e = entries[i]
-        # Inspect the UNDERLYING store only -- this forces no load even when the
-        # entry is lazily backed, and grants the in-place token for this entry.
         probe = inspect_underlying(e)
-        loads = loads + probe[1]
-        if probe[0]:
-            result = result + [e.axis, e.length]
-        else:
-            result = result + [-1, -1]
+        result = result + [e.axis, e.length]
         i = i + 1
     result = result + [loads]
     return result
```

Attack 8 — `atk8_ungrounded.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,8 +198,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == 2 * i)
         Invariant(loads == 0)
-        # every entry remains intact: only the in-place underlying view is used,
-        # so no payload is ever pulled into memory
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
             payload_intact(entries[k])), [[entries[k]]])))
         Invariant(Forall(int, lambda k: (
@@ -212,15 +210,13 @@
             [[entries[k]]])))
         # invariants-end
         e = entries[i]
-        # Inspect the UNDERLYING store only -- this forces no load even when the
-        # entry is lazily backed, and grants the in-place token for this entry.
-        probe = inspect_underlying(e)
-        loads = loads + probe[1]
+        probe = inspect_materialised(e)
         if probe[0]:
             result = result + [e.axis, e.length]
         else:
             result = result + [-1, -1]
         i = i + 1
+    loads = 0
     result = result + [loads]
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-6721.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of array-bearing entries is inspected to report, per labelled
  axis, the block lengths of the entries that are stored in block form. Each
  entry wraps an underlying store which may or may not advertise a block
  structure. Two views of an entry's payload exist:

    * the UNDERLYING store, which can be inspected for a block structure
      cheaply and without ever pulling the payload into memory; and
    * the MATERIALISED payload, obtaining which forces a lazily-backed entry to
      pull its whole payload into memory (an observable, possibly very
      expensive or even impossible, side effect).

  The desired behaviour: deciding whether an entry is block-structured, and
  reading its block lengths, MUST consult the underlying store only, so that
  inspecting the collection NEVER materialises any lazily-backed entry. The
  reported mapping sends each axis carried by a block-structured entry to that
  entry's block length on the axis; entries whose underlying store advertises
  no block structure contribute nothing.

Entries are modelled as a minimal object carrying only the touched fields:
whether the underlying store advertises a block structure, whether obtaining
the materialised payload would force a load (i.e. the store is lazily backed),
the single axis label it carries, and its block length on that axis. Axis
labels and lengths are abstracted to ints (mapping.md gives the bijection).

The no-materialisation requirement is pinned by an UNFORGEABLE, CONSUMABLE
capability token `payload_intact`: every entry starts intact (its payload has
not been pulled into memory), and the result is required to leave every entry
intact. Inspecting an entry's UNDERLYING store reads it IN PLACE and preserves
the token; obtaining the MATERIALISED payload pulls the payload into memory and
CONSUMES the token without restoring it. The token is abstract (no body), so
nothing can fabricate or re-fold it once consumed. Hence a verifying
implementation can never have obtained the materialised payload of any entry:
the only way to keep every entry intact through to the result is to read every
block status in place. An implementation that materialises an entry (forcing a
load) -- even one that also reads the underlying store and reports a load count
of zero -- permanently loses that entry's token and cannot re-establish the
postcondition. A running "loads forced" tally, threaded through and required to
stay zero, additionally records that no materialisation happened.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


class Entry:
    # One array-bearing entry of the inspected collection.
    #   block_backed : the UNDERLYING store advertises a block structure
    #   forces_load  : obtaining the MATERIALISED payload would force a load
    #                  (the store is lazily backed, not already in memory)
    #   axis         : the single axis label this entry carries
    #   length       : the entry's block length along that axis
    def __init__(self, block_backed: bool, forces_load: bool,
                 axis: int, length: int) -> None:
        self.block_backed = block_backed  # type: bool
        self.forces_load = forces_load    # type: bool
        self.axis = axis                  # type: int
        self.length = length              # type: int
        Ensures(Acc(self.block_backed) and Acc(self.forces_load))
        Ensures(Acc(self.axis) and Acc(self.length))
        Ensures(self.block_backed == block_backed)
        Ensures(self.forces_load == forces_load)
        Ensures(self.axis == axis and self.length == length)


# pure-start
@Pure
def block_load_cost(e: Entry) -> int:
    # Loads forced by inspecting an entry's block status via its MATERIALISED
    # payload: one when the store is lazily backed, none otherwise.
    Requires(Acc(e.forces_load, 1 / 8))
    return 1 if e.forces_load else 0
# pure-end


# axioms-start
# Abstract, CONSUMABLE capability token: held for an entry exactly while its
# payload has NOT been pulled into memory (the entry is "intact"). The token is
# abstract (no body), so nothing can `Fold` or otherwise fabricate it -- once
# consumed it is gone for good. `inspect_underlying` reads the entry in place
# and threads the token through unchanged (the entry stays intact);
# `inspect_materialised` REQUIRES the token but does not return it (obtaining
# the materialised payload pulls it into memory, consuming intactness). The
# whole inspection both requires and re-establishes the token for every entry
# (see `block_lengths_by_axis`), so a verifying implementation can never have
# materialised any entry: materialising one would permanently lose its token
# and leave the result-side obligation undischargeable -- regardless of what is
# written into the trailing load-count slot, and even if the underlying store
# is also read.
@ContractOnly
@Predicate
def payload_intact(e: Entry) -> bool:
    pass


# The two payload-view operations are unchanged library reads modelled as
# contract-only callees (mapping.md cites their provenance; axiom_check.py /
# G-AX validates each contract against the real xarray Variable semantics).
@ContractOnly
def inspect_underlying(e: Entry) -> Tuple[bool, int]:
    """Inspect the UNDERLYING store for a block structure. Returns the block
    status and the loads this forces -- always zero, because the underlying
    store is inspected in place without pulling the payload into memory. Reads
    in place, so the entry stays intact: the `payload_intact` token is required
    and returned unchanged."""
    Requires(Acc(e.block_backed, 1 / 8))
    Requires(payload_intact(e))
    Ensures(Acc(e.block_backed, 1 / 8))
    Ensures(payload_intact(e))
    Ensures(Result()[0] == e.block_backed)
    Ensures(Result()[1] == 0)


@ContractOnly
def inspect_materialised(e: Entry) -> Tuple[bool, int]:
    """Inspect the entry's block status via its MATERIALISED payload. Obtaining
    that payload forces a load on a lazily-backed entry (and a materialised
    payload, once in memory, never advertises a block structure of its own).
    Pulls the payload into memory, CONSUMING the `payload_intact` token: it is
    required but NOT returned, so the entry is no longer intact afterwards."""
    Requires(Acc(e.block_backed, 1 / 8) and Acc(e.forces_load, 1 / 8))
    Requires(payload_intact(e))
    Ensures(Acc(e.block_backed, 1 / 8) and Acc(e.forces_load, 1 / 8))
    # for an in-memory entry the materialised view agrees with the underlying
    # one; for a lazily-backed entry the materialised payload is a plain in-
    # memory array and advertises no block structure
    Ensures(Result()[0] == (e.block_backed and not e.forces_load))
    Ensures(Result()[1] == block_load_cost(e))
# axioms-end


def block_lengths_by_axis(entries: List[Entry]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(entries), 1 / 2))
    # every entry is a valid object exposing the touched fields (read-only)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        Acc(entries[k].block_backed, 1 / 8) and Acc(entries[k].forces_load, 1 / 8)
        and Acc(entries[k].axis, 1 / 8) and Acc(entries[k].length, 1 / 8)),
        [[entries[k]]])))
    # every entry enters the inspection intact: its payload has not been pulled
    # into memory
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        payload_intact(entries[k])), [[entries[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        Acc(entries[k].block_backed, 1 / 8) and Acc(entries[k].forces_load, 1 / 8)
        and Acc(entries[k].axis, 1 / 8) and Acc(entries[k].length, 1 / 8)),
        [[entries[k]]])))
    Ensures(Acc(list_pred(Result())))
    # The result is a flat (axis, length) pair list, one slot pair per entry:
    # (Result()[2*i], Result()[2*i+1]) is the contribution of entry i. The
    # final slot, Result()[2*len(entries)], is the total loads forced by the
    # whole inspection and MUST be zero -- no lazily-backed entry is ever
    # materialised.
    Ensures(len(Result()) == 2 * len(entries) + 1)
    Ensures(Result()[2 * len(entries)] == 0)
    # UNFORGEABLE no-materialisation obligation: every entry is still intact --
    # its payload was never pulled into memory by the inspection. The
    # `payload_intact` token is consumable and cannot be fabricated; an
    # implementation that obtained the materialised payload of any entry
    # (forcing a load) consumes that entry's token and cannot re-establish this
    # clause -- regardless of what it writes into the trailing load-count slot,
    # and even if it also reads the underlying store. This pins the
    # no-materialisation behaviour the desired contract demands; the trailing
    # `== 0` slot alone would be an echoable constant.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        payload_intact(entries[k])), [[entries[k]]])))
    # block status and lengths come from the underlying store: an entry whose
    # underlying store is NOT block-structured contributes the empty marker
    # (-1, -1); a block-structured entry contributes its (axis, block length).
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(entries),
            Implies(not entries[k].block_backed,
                    Result()[2 * k] == -1 and Result()[2 * k + 1] == -1)
            and Implies(entries[k].block_backed,
                    Result()[2 * k] == entries[k].axis
                    and Result()[2 * k + 1] == entries[k].length)),
        [[entries[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    loads = 0
    i = 0
    while i < len(entries):
        # invariants-start
        Invariant(Acc(list_pred(entries), 1 / 2))
        Invariant(0 <= i and i <= len(entries))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
            Acc(entries[k].block_backed, 1 / 8) and Acc(entries[k].forces_load, 1 / 8)
            and Acc(entries[k].axis, 1 / 8) and Acc(entries[k].length, 1 / 8)),
            [[entries[k]]])))
        Invariant(Acc(list_pred(result)))
        Invariant(len(result) == 2 * i)
        Invariant(loads == 0)
        # every entry remains intact: only the in-place underlying view is used,
        # so no payload is ever pulled into memory
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
            payload_intact(entries[k])), [[entries[k]]])))
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < i,
                Implies(not entries[k].block_backed,
                        result[2 * k] == -1 and result[2 * k + 1] == -1)
                and Implies(entries[k].block_backed,
                        result[2 * k] == entries[k].axis
                        and result[2 * k + 1] == entries[k].length)),
            [[entries[k]]])))
        # invariants-end
        e = entries[i]
        # Inspect the UNDERLYING store only -- this forces no load even when the
        # entry is lazily backed, and grants the in-place token for this entry.
        probe = inspect_underlying(e)
        loads = loads + probe[1]
        if probe[0]:
            result = result + [e.axis, e.length]
        else:
            result = result + [-1, -1]
        i = i + 1
    result = result + [loads]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Positive control (unmodified model.py) verifies (15.8s).

### Weakness results
- atk1_prepatch (PREPATCH BUG: inspect_materialised verbatim, model_prepatch impl) => NOT-A-COUNTEREXAMPLE, fails verify. PREPATCH REPRODUCED: materialisation consumes payload_intact token + forces load; postcondition undischargeable.
- atk2_echo_after (ungrounded-oracle echo: read underlying for correct value+token, THEN also call inspect_materialised, write literal loads=0) => fails verify (token consumed at loop end; payload_intact post clause undischargeable).
- atk3_echo_before (materialise first consuming token, then read e.block_backed field directly for correct value, loads literal 0) => fails verify (token gone).
- atk4_directfield (CANDIDATE: reads underlying-store field e.block_backed directly, no callee; == v._data behaviour) => shares spec AND verifies (19.1s). Materialized faithful patch = gold v._data fix; ran official harness `run_resolve('pydata__xarray-6721', patch, run_id=sbu-audit-eq-syljvyo5-atk4b)` => RESOLVED=True COMPLETED=True FLAKY=False ATTEMPTS=1. Does NOT break spec (verify => correct here).
- atk5_offbyone (boundary: one slot per entry, len(result)==i) => fails verify (len + value clauses).
- atk6_cfmaterialise (control-flow-effect: inspect_materialised only on block_backed path) => fails verify (token consumed on that path).
- atk7_partialdomain (partial-domain: emit (axis,length) for non-block entries too) => fails verify (value clause: non-block must be (-1,-1)).
- atk8_ungrounded (ungrounded-oracle: materialise every entry, overwrite loads=0 after loop) => fails verify (token consumed; also value clause for lazy-block regime).

No verifying wrong impl exists: the postcondition pins every output slot exactly to underlying-store fields (block_backed/axis/length), pins trailing loads slot ==0, and the discriminating clause requires the UNFORGEABLE CONSUMABLE payload_intact predicate for every entry. inspect_materialised requires-but-does-not-return the token (abstract @Predicate, no Fold), so any impl using the buggy v.data view permanently loses it and cannot re-establish the post -- even when values coincide and it writes loads=0. The only verifying candidate is behaviourally the gold fix and its faithful patch RESOLVES.

REFINEMENT.md A-LEG AUDIT (verified against real xarray Variable at base_commit cc183652, xarray-2022.6.0 wheel variable.py): every leg is R / A-consumed / I -- NO kind-3. Leg3 inspect_underlying<->hasattr(v._data,'chunks'): variable.py:1011 getattr(self._data,'chunks',None) + chunksizes:1029 hasattr(self._data,'chunks') -- plain attr access, no __getitem__ => 0 loads, status==block presence. Leg3' inspect_materialised<->hasattr(v.data,'chunks'): data@350 returns self._data if is_duck_array else self.values; values@525 -> _as_array_or_item -> np.asarray, materialising a non-duck store => status (block_backed and not forces_load), loads 1 iff forces_load. Leg4 payload_intact: proof-only unforgeable token pinning the no-materialisation regression (F2P test_chunks_does_not_load_data), operationally confirmed by atk2/3/6/8 all failing reverify. axiom_check.py (G-AX) validates the same three regimes. A-legs correspond to the real callees; model<->patch correspondence holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch.py`, `atk2_echo_after.py`, `atk3_echo_before.py`, `atk5_offbyone.py`, `atk6_cfmaterialise.py`, `atk7_partialdomain.py`, `atk8_ungrounded.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk4_directfield.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_echo_after.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_echo_before.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_directfield.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk5_offbyone.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_cfmaterialise.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_partialdomain.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_ungrounded.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-6721.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of array-bearing entries is inspected to report, per labelled
  axis, the block lengths of the entries that are stored in block form. Each
  entry wraps an underlying store which may or may not advertise a block
  structure. Two views of an entry's payload exist:

    * the UNDERLYING store, which can be inspected for a block structure
      cheaply and without ever pulling the payload into memory; and
    * the MATERIALISED payload, obtaining which forces a lazily-backed entry to
      pull its whole payload into memory (an observable, possibly very
      expensive or even impossible, side effect).

  The desired behaviour: deciding whether an entry is block-structured, and
  reading its block lengths, MUST consult the underlying store only, so that
  inspecting the collection NEVER materialises any lazily-backed entry. The
  reported mapping sends each axis carried by a block-structured entry to that
  entry's block length on the axis; entries whose underlying store advertises
  no block structure contribute nothing.

Entries are modelled as a minimal object carrying only the touched fields:
whether the underlying store advertises a block structure, whether obtaining
the materialised payload would force a load (i.e. the store is lazily backed),
the single axis label it carries, and its block length on that axis. Axis
labels and lengths are abstracted to ints (mapping.md gives the bijection).

The no-materialisation requirement is pinned by an UNFORGEABLE, CONSUMABLE
capability token `payload_intact`: every entry starts intact (its payload has
not been pulled into memory), and the result is required to leave every entry
intact. Inspecting an entry's UNDERLYING store reads it IN PLACE and preserves
the token; obtaining the MATERIALISED payload pulls the payload into memory and
CONSUMES the token without restoring it. The token is abstract (no body), so
nothing can fabricate or re-fold it once consumed. Hence a verifying
implementation can never have obtained the materialised payload of any entry:
the only way to keep every entry intact through to the result is to read every
block status in place. An implementation that materialises an entry (forcing a
load) -- even one that also reads the underlying store and reports a load count
of zero -- permanently loses that entry's token and cannot re-establish the
postcondition. A running "loads forced" tally, threaded through and required to
stay zero, additionally records that no materialisation happened.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


class Entry:
    # One array-bearing entry of the inspected collection.
    #   block_backed : the UNDERLYING store advertises a block structure
    #   forces_load  : obtaining the MATERIALISED payload would force a load
    #                  (the store is lazily backed, not already in memory)
    #   axis         : the single axis label this entry carries
    #   length       : the entry's block length along that axis
    def __init__(self, block_backed: bool, forces_load: bool,
                 axis: int, length: int) -> None:
        self.block_backed = block_backed  # type: bool
        self.forces_load = forces_load    # type: bool
        self.axis = axis                  # type: int
        self.length = length              # type: int
        Ensures(Acc(self.block_backed) and Acc(self.forces_load))
        Ensures(Acc(self.axis) and Acc(self.length))
        Ensures(self.block_backed == block_backed)
        Ensures(self.forces_load == forces_load)
        Ensures(self.axis == axis and self.length == length)


# pure-start
@Pure
def block_load_cost(e: Entry) -> int:
    # Loads forced by inspecting an entry's block status via its MATERIALISED
    # payload: one when the store is lazily backed, none otherwise.
    Requires(Acc(e.forces_load, 1 / 8))
    return 1 if e.forces_load else 0
# pure-end


# axioms-start
# Abstract, CONSUMABLE capability token: held for an entry exactly while its
# payload has NOT been pulled into memory (the entry is "intact"). The token is
# abstract (no body), so nothing can `Fold` or otherwise fabricate it -- once
# consumed it is gone for good. `inspect_underlying` reads the entry in place
# and threads the token through unchanged (the entry stays intact);
# `inspect_materialised` REQUIRES the token but does not return it (obtaining
# the materialised payload pulls it into memory, consuming intactness). The
# whole inspection both requires and re-establishes the token for every entry
# (see `block_lengths_by_axis`), so a verifying implementation can never have
# materialised any entry: materialising one would permanently lose its token
# and leave the result-side obligation undischargeable -- regardless of what is
# written into the trailing load-count slot, and even if the underlying store
# is also read.
@ContractOnly
@Predicate
def payload_intact(e: Entry) -> bool:
    pass


# The two payload-view operations are unchanged library reads modelled as
# contract-only callees (mapping.md cites their provenance; axiom_check.py /
# G-AX validates each contract against the real xarray Variable semantics).
@ContractOnly
def inspect_underlying(e: Entry) -> Tuple[bool, int]:
    """Inspect the UNDERLYING store for a block structure. Returns the block
    status and the loads this forces -- always zero, because the underlying
    store is inspected in place without pulling the payload into memory. Reads
    in place, so the entry stays intact: the `payload_intact` token is required
    and returned unchanged."""
    Requires(Acc(e.block_backed, 1 / 8))
    Requires(payload_intact(e))
    Ensures(Acc(e.block_backed, 1 / 8))
    Ensures(payload_intact(e))
    Ensures(Result()[0] == e.block_backed)
    Ensures(Result()[1] == 0)


@ContractOnly
def inspect_materialised(e: Entry) -> Tuple[bool, int]:
    """Inspect the entry's block status via its MATERIALISED payload. Obtaining
    that payload forces a load on a lazily-backed entry (and a materialised
    payload, once in memory, never advertises a block structure of its own).
    Pulls the payload into memory, CONSUMING the `payload_intact` token: it is
    required but NOT returned, so the entry is no longer intact afterwards."""
    Requires(Acc(e.block_backed, 1 / 8) and Acc(e.forces_load, 1 / 8))
    Requires(payload_intact(e))
    Ensures(Acc(e.block_backed, 1 / 8) and Acc(e.forces_load, 1 / 8))
    # for an in-memory entry the materialised view agrees with the underlying
    # one; for a lazily-backed entry the materialised payload is a plain in-
    # memory array and advertises no block structure
    Ensures(Result()[0] == (e.block_backed and not e.forces_load))
    Ensures(Result()[1] == block_load_cost(e))
# axioms-end


def block_lengths_by_axis(entries: List[Entry]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(entries), 1 / 2))
    # every entry is a valid object exposing the touched fields (read-only)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        Acc(entries[k].block_backed, 1 / 8) and Acc(entries[k].forces_load, 1 / 8)
        and Acc(entries[k].axis, 1 / 8) and Acc(entries[k].length, 1 / 8)),
        [[entries[k]]])))
    # every entry enters the inspection intact: its payload has not been pulled
    # into memory
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        payload_intact(entries[k])), [[entries[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        Acc(entries[k].block_backed, 1 / 8) and Acc(entries[k].forces_load, 1 / 8)
        and Acc(entries[k].axis, 1 / 8) and Acc(entries[k].length, 1 / 8)),
        [[entries[k]]])))
    Ensures(Acc(list_pred(Result())))
    # The result is a flat (axis, length) pair list, one slot pair per entry:
    # (Result()[2*i], Result()[2*i+1]) is the contribution of entry i. The
    # final slot, Result()[2*len(entries)], is the total loads forced by the
    # whole inspection and MUST be zero -- no lazily-backed entry is ever
    # materialised.
    Ensures(len(Result()) == 2 * len(entries) + 1)
    Ensures(Result()[2 * len(entries)] == 0)
    # UNFORGEABLE no-materialisation obligation: every entry is still intact --
    # its payload was never pulled into memory by the inspection. The
    # `payload_intact` token is consumable and cannot be fabricated; an
    # implementation that obtained the materialised payload of any entry
    # (forcing a load) consumes that entry's token and cannot re-establish this
    # clause -- regardless of what it writes into the trailing load-count slot,
    # and even if it also reads the underlying store. This pins the
    # no-materialisation behaviour the desired contract demands; the trailing
    # `== 0` slot alone would be an echoable constant.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        payload_intact(entries[k])), [[entries[k]]])))
    # block status and lengths come from the underlying store: an entry whose
    # underlying store is NOT block-structured contributes the empty marker
    # (-1, -1); a block-structured entry contributes its (axis, block length).
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(entries),
            Implies(not entries[k].block_backed,
                    Result()[2 * k] == -1 and Result()[2 * k + 1] == -1)
            and Implies(entries[k].block_backed,
                    Result()[2 * k] == entries[k].axis
                    and Result()[2 * k + 1] == entries[k].length)),
        [[entries[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    loads = 0
    i = 0
    while i < len(entries):
        # invariants-start
        Invariant(Acc(list_pred(entries), 1 / 2))
        Invariant(0 <= i and i <= len(entries))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
            Acc(entries[k].block_backed, 1 / 8) and Acc(entries[k].forces_load, 1 / 8)
            and Acc(entries[k].axis, 1 / 8) and Acc(entries[k].length, 1 / 8)),
            [[entries[k]]])))
        Invariant(Acc(list_pred(result)))
        Invariant(len(result) == 2 * i)
        Invariant(loads == 0)
        # every entry remains intact: only the in-place underlying view is used,
        # so no payload is ever pulled into memory
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
            payload_intact(entries[k])), [[entries[k]]])))
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < i,
                Implies(not entries[k].block_backed,
                        result[2 * k] == -1 and result[2 * k + 1] == -1)
                and Implies(entries[k].block_backed,
                        result[2 * k] == entries[k].axis
                        and result[2 * k + 1] == entries[k].length)),
            [[entries[k]]])))
        # invariants-end
        e = entries[i]
        # Inspect the UNDERLYING store only -- this forces no load even when the
        # entry is lazily backed, and grants the in-place token for this entry.
        probe = inspect_underlying(e)
        loads = loads + probe[1]
        if probe[0]:
            result = result + [e.axis, e.length]
        else:
            result = result + [-1, -1]
        i = i + 1
    result = result + [loads]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Positive control (unmodified model.py) verifies (15.8s).

### Weakness results
- atk1_prepatch (PREPATCH BUG: inspect_materialised verbatim, model_prepatch impl) => NOT-A-COUNTEREXAMPLE, fails verify. PREPATCH REPRODUCED: materialisation consumes payload_intact token + forces load; postcondition undischargeable.
- atk2_echo_after (ungrounded-oracle echo: read underlying for correct value+token, THEN also call inspect_materialised, write literal loads=0) => fails verify (token consumed at loop end; payload_intact post clause undischargeable).
- atk3_echo_before (materialise first consuming token, then read e.block_backed field directly for correct value, loads literal 0) => fails verify (token gone).
- atk4_directfield (CANDIDATE: reads underlying-store field e.block_backed directly, no callee; == v._data behaviour) => shares spec AND verifies (19.1s). Materialized faithful patch = gold v._data fix; ran official harness `run_resolve('pydata__xarray-6721', patch, run_id=sbu-audit-eq-syljvyo5-atk4b)` => RESOLVED=True COMPLETED=True FLAKY=False ATTEMPTS=1. Does NOT break spec (verify => correct here).
- atk5_offbyone (boundary: one slot per entry, len(result)==i) => fails verify (len + value clauses).
- atk6_cfmaterialise (control-flow-effect: inspect_materialised only on block_backed path) => fails verify (token consumed on that path).
- atk7_partialdomain (partial-domain: emit (axis,length) for non-block entries too) => fails verify (value clause: non-block must be (-1,-1)).
- atk8_ungrounded (ungrounded-oracle: materialise every entry, overwrite loads=0 after loop) => fails verify (token consumed; also value clause for lazy-block regime).

No verifying wrong impl exists: the postcondition pins every output slot exactly to underlying-store fields (block_backed/axis/length), pins trailing loads slot ==0, and the discriminating clause requires the UNFORGEABLE CONSUMABLE payload_intact predicate for every entry. inspect_materialised requires-but-does-not-return the token (abstract @Predicate, no Fold), so any impl using the buggy v.data view permanently loses it and cannot re-establish the post -- even when values coincide and it writes loads=0. The only verifying candidate is behaviourally the gold fix and its faithful patch RESOLVES.

REFINEMENT.md A-LEG AUDIT (verified against real xarray Variable at base_commit cc183652, xarray-2022.6.0 wheel variable.py): every leg is R / A-consumed / I -- NO kind-3. Leg3 inspect_underlying<->hasattr(v._data,'chunks'): variable.py:1011 getattr(self._data,'chunks',None) + chunksizes:1029 hasattr(self._data,'chunks') -- plain attr access, no __getitem__ => 0 loads, status==block presence. Leg3' inspect_materialised<->hasattr(v.data,'chunks'): data@350 returns self._data if is_duck_array else self.values; values@525 -> _as_array_or_item -> np.asarray, materialising a non-duck store => status (block_backed and not forces_load), loads 1 iff forces_load. Leg4 payload_intact: proof-only unforgeable token pinning the no-materialisation regression (F2P test_chunks_does_not_load_data), operationally confirmed by atk2/3/6/8 all failing reverify. axiom_check.py (G-AX) validates the same three regimes. A-legs correspond to the real callees; model<->patch correspondence holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: NONE FOUND. The modeled function block_lengths_by_axis is a sound abstraction of the fixed xarray.core.common.get_chunksizes over the realizable input domain.

Machine-checkable evidence:
- Model verifies with pinned Nagini: `bash scripts/nagini_verify.sh model.py` -> 'Verification successful' (15.97s, exit 0).
- axiom_check.py (G-AX) run against the REAL base-commit repo (@ d3b6aa6d8b997df115a53c001d00222a0f92f63a = base_commit) passes on all three realizable regimes: in-memory-numpy (block_backed=F,forces_load=F), lazy-inaccessible (block_backed=F,forces_load=T; the EXACT LazilyIndexedArray+InaccessibleArray store the F2P test test_chunks_does_not_load_data uses), and dask-chunked (block_backed=T,forces_load=F). It validates both the block-status contract (inspect_underlying=hasattr(v._data,'chunks'), inspect_materialised=hasattr(v.data,'chunks')) AND the forced-load side effect against real Variable._data/Variable.data/Variable.values. Exit 0.
- Refinement fidelity: gold patch is the one-line v.data->v._data change (common.py:2026 at repo; body inspected in worktree). Model's Entry.block_backed <-> hasattr(v._data,'chunks'); forces_load <-> non-duck lazy store; per-entry axis/length <-> v.chunksizes; the (-1,-1) skip marker <-> non-chunked entry contributes nothing. Aggregation (flat pair list) <-> Frozen(dict) is identity-on-content. All steps R/A-consumed/I; no kind-3.

Probed the one regime axiom_check omits (block_backed=True AND forces_load=True): only constructible with a CONTRIVED non-duck array that fakes a .chunks attribute (FakeChunked). In real xarray, any array advertising .chunks is a dask (duck) array, so Variable.data (variable.py:344-348, is_duck_array short-circuit) returns self._data WITHOUT a load => forces_load=False. Hence block_backed=True => forces_load=False for all realizable Variables; no realizable input drives the fixed repo to force a load or to disagree with the spec's loads==0 / payload_intact postconditions. The payload_intact token is an explicit proof-only construct with no runtime footprint (documented and confirmed by axiom_check), so it cannot itself introduce repo drift.

Conclusion: no diverging input exists on the realizable domain; the spec is not too strong. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-LEAK leakage/gold-reconstruction review of the nagini spec view for pydata__xarray-6721.

Gold edit: xarray/core/common.py inside get_chunksizes, `if hasattr(v.data, "chunks"):` -> `if hasattr(v._data, "chunks"):` (inspect the UNDERLYING store `v._data` instead of the MATERIALISED payload `v.data`, avoiding a forced load).

Mechanical screen (swebench_unified.leakage.screen against frozen problem_statement, NOT hints_text): PASSED with zero hard failures — no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier or comment echoing a patched repo symbol, no bug/fix narration keywords.

Semantic reconstruction check: the spec view is fully abstracted. Modeled function is `block_lengths_by_axis(entries: List[Entry])`; callees `inspect_underlying`/`inspect_materialised`; fields `block_backed`/`forces_load`/`axis`/`length`; token `payload_intact`. None of `get_chunksizes`, `hasattr`, `chunks`, `v.data`, `v._data`, `_data`, `Frozen`, `chunksizes`, `common.py`, `variable.py`, `np.asarray`, `zarr`, `dask`, or `encoding` appears anywhere in the spec view (verified by substring scan).

Problem_statement disclosure baseline: the PUBLIC problem_statement is far more revealing than the spec view — it names get_chunksizes, shows the verbatim buggy line `if hasattr(v.data, "chunks"):`, and traces the materialisation chain v.data -> self.values -> _as_array_or_item -> np.asarray (with self._data visible), and states the desired behaviour (accessing chunks should not load into memory; should inspect the underlying arrays). The spec view's 'consult the underlying store only, never materialise any lazily-backed entry' is strictly a generic re-statement of behaviour the problem_statement already demands, expressed over abstract Entry/token vocabulary — it does not reveal the one-line edit, the symbol names, the file, or the diff beyond what the solver-visible task already contains.

Conclusion: the spec view leaks nothing about the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
