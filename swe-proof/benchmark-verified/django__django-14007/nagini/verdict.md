# P2 adversarial audit — django__django-14007

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies. The only verifying same-spec attack (atk_1) is behaviourally gold-equivalent (correct per-row/per-column fold, exact length preservation), and its materialized faithful refined patch — the gold patch verbatim — RESOLVES under the official harness (run_resolve: resolved=True, completed=True, attempts=1). verify does NOT admit an incorrect impl here.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -132,6 +132,7 @@
         # invariants-end
         old = out  # type: PSeq[PSeq[int]]
         cr = apply_row(rows[j], chains, ncols)
+        Assert(len(cr) == ncols)
         out = out + PSeq(cr)
         Assert(out[j] is cr)
         Assert(len(out[j]) == ncols)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -116,7 +116,7 @@
     # impl-start
     out = rows.take(0)  # type: PSeq[PSeq[int]]
     j = 0
-    while j < len(rows):
+    while j < len(rows) - 1:
         # invariants-start
         Invariant(0 <= j and j <= len(rows))
         Invariant(len(chains) == ncols)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -77,15 +77,12 @@
         Invariant(len(row) == ncols)
         Invariant(len(chains) == ncols)
         Invariant(len(out) == p)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < p,
-            out[k] == fold_chain(chains[k], row[k])), [[out[k]]])))
         # invariants-end
-        old = out  # type: PSeq[int]
-        nv = fold_chain(chains[p], row[p])
+        if p == 0:
+            nv = fold_chain(chains[p], row[p])
+        else:
+            nv = row[p]
         out = out + PSeq(nv)
-        Assert(out[p] == nv)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < p,
-            out[k] == old[k]), [[out[k]]])))
         p = p + 1
     return out
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -77,15 +77,10 @@
         Invariant(len(row) == ncols)
         Invariant(len(chains) == ncols)
         Invariant(len(out) == p)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < p,
-            out[k] == fold_chain(chains[k], row[k])), [[out[k]]])))
         # invariants-end
-        old = out  # type: PSeq[int]
-        nv = fold_chain(chains[p], row[p])
+        idx = (p + 1) % ncols if ncols > 0 else 0
+        nv = fold_chain(chains[p], row[idx])
         out = out + PSeq(nv)
-        Assert(out[p] == nv)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < p,
-            out[k] == old[k]), [[out[k]]])))
         p = p + 1
     return out
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -77,15 +77,9 @@
         Invariant(len(row) == ncols)
         Invariant(len(chains) == ncols)
         Invariant(len(out) == p)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < p,
-            out[k] == fold_chain(chains[k], row[k])), [[out[k]]])))
         # invariants-end
-        old = out  # type: PSeq[int]
-        nv = fold_chain(chains[p], row[p])
+        nv = fold_chain(chains[p], fold_chain(chains[p], row[p]))
         out = out + PSeq(nv)
-        Assert(out[p] == nv)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < p,
-            out[k] == old[k]), [[out[k]]])))
         p = p + 1
     return out
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,20 +123,8 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(rows),
             len(rows[k]) == ncols), [[rows[k]]])))
         Invariant(len(out) == j)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
-            len(out[k]) == ncols), [[out[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
-            Forall(int, lambda p: (Implies(0 <= p and p < ncols,
-                out[k][p] == fold_chain(chains[p], rows[k][p])),
-                [[out[k][p]]]))), [[out[k]]])))
         # invariants-end
-        old = out  # type: PSeq[PSeq[int]]
-        cr = apply_row(rows[j], chains, ncols)
-        out = out + PSeq(cr)
-        Assert(out[j] is cr)
-        Assert(len(out[j]) == ncols)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
-            out[k] is old[k]), [[out[k]]])))
+        out = out + PSeq(rows[j])
         j = j + 1
     return out
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,20 +123,12 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(rows),
             len(rows[k]) == ncols), [[rows[k]]])))
         Invariant(len(out) == j)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
-            len(out[k]) == ncols), [[out[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
-            Forall(int, lambda p: (Implies(0 <= p and p < ncols,
-                out[k][p] == fold_chain(chains[p], rows[k][p])),
-                [[out[k][p]]]))), [[out[k]]])))
         # invariants-end
-        old = out  # type: PSeq[PSeq[int]]
-        cr = apply_row(rows[j], chains, ncols)
-        out = out + PSeq(cr)
-        Assert(out[j] is cr)
-        Assert(len(out[j]) == ncols)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
-            out[k] is old[k]), [[out[k]]])))
+        if j == 0:
+            cr = apply_row(rows[j], chains, ncols)
+            out = out + PSeq(cr)
+        else:
+            out = out + PSeq(rows[j])
         j = j + 1
     return out
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14007.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a row-returning database write hands back the freshly assigned column
  values, those raw values must be run through the per-column value-conversion
  pipeline before they reach the caller -- exactly as every other read path
  already does. Each returned column carries an ordered chain of value
  converters (possibly empty). The value the caller observes at a column is the
  left-fold of that column's converter chain over the raw value:

      observed = c_k(... c_2(c_1(raw)) ...)              for a chain c_1..c_k
      observed = raw                                     for an empty chain

  applied independently to every returned row and every column. A column whose
  chain is empty is therefore the identity (the raw value passes through), and a
  column whose chain is non-empty yields the converted value -- never the raw
  one. The number and shape of the returned rows is preserved exactly.

Rows are modelled as a pure sequence of pure rows, `PSeq[PSeq[int]]` (each row a
`PSeq[int]` of column values). Pure sequences carry no heap permission, so the
specification quantifies over rows and columns directly. A single converter step
is an opaque unchanged callee, `step(converter_id, value)`, axiomatized as a
@Pure @ContractOnly function; the conversion chain `fold_chain` and the row/grid
application are modelled deeply (front-recursive fold + verified loops) and
pinned element-wise by the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def step(converter_id: int, value: int) -> int:
    """One value converter applied to one value (an unchanged callee of the
    conversion pipeline; e.g. a field's stored value-restoration hook). Opaque:
    no relation between input and output is assumed, in particular it is NOT
    assumed to be the identity. Provenance + executable soundness: mapping.md /
    axiom_check.py (G-AX)."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def fold_chain(chain: PSeq[int], value: int) -> int:
    """Left-fold one column's converter chain over a raw value (front-recursive
    so a single unfold is available per loop step). An empty chain is the
    identity; otherwise each converter id is applied in order via `step`."""
    if len(chain) == 0:
        return value
    return fold_chain(chain.drop(1), step(chain[0], value))
# pure-end


def apply_row(row: PSeq[int], chains: PSeq[PSeq[int]], ncols: int) -> PSeq[int]:
    # pre-conditions-start
    Requires(ncols >= 0)
    Requires(len(row) == ncols)
    Requires(len(chains) == ncols)
    # pre-conditions-end
    # post-conditions-start
    # The converted row has the same width, and each column holds the fold of
    # that column's converter chain over the raw column value.
    Ensures(len(Result()) == ncols)
    Ensures(Forall(int, lambda p: (Implies(0 <= p and p < ncols,
        Result()[p] == fold_chain(chains[p], row[p])), [[Result()[p]]])))
    # post-conditions-end
    # impl-start
    out = PSeq(0).take(0)  # type: PSeq[int]
    p = 0
    while p < ncols:
        # invariants-start
        Invariant(0 <= p and p <= ncols)
        Invariant(len(row) == ncols)
        Invariant(len(chains) == ncols)
        Invariant(len(out) == p)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < p,
            out[k] == fold_chain(chains[k], row[k])), [[out[k]]])))
        # invariants-end
        old = out  # type: PSeq[int]
        nv = fold_chain(chains[p], row[p])
        out = out + PSeq(nv)
        Assert(out[p] == nv)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < p,
            out[k] == old[k]), [[out[k]]])))
        p = p + 1
    return out
    # impl-end


def execute_returning(rows: PSeq[PSeq[int]], chains: PSeq[PSeq[int]],
                      ncols: int) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(ncols >= 0)
    # one converter chain per returned column
    Requires(len(chains) == ncols)
    # every raw row has one value per returned column
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(rows),
        len(rows[j]) == ncols), [[rows[j]]])))
    # pre-conditions-end
    # post-conditions-start
    # Row count and width are preserved exactly.
    Ensures(len(Result()) == len(rows))
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(rows),
        len(Result()[j]) == ncols), [[Result()[j]]])))
    # Every observed value is the converter-chain fold over the raw value:
    # identity for an empty chain, the converted value for a non-empty chain.
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(rows),
        Forall(int, lambda p: (Implies(0 <= p and p < ncols,
            Result()[j][p] == fold_chain(chains[p], rows[j][p])),
            [[Result()[j][p]]]))), [[Result()[j]]])))
    # post-conditions-end
    # impl-start
    out = rows.take(0)  # type: PSeq[PSeq[int]]
    j = 0
    while j < len(rows):
        # invariants-start
        Invariant(0 <= j and j <= len(rows))
        Invariant(len(chains) == ncols)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(rows),
            len(rows[k]) == ncols), [[rows[k]]])))
        Invariant(len(out) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
            len(out[k]) == ncols), [[out[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
            Forall(int, lambda p: (Implies(0 <= p and p < ncols,
                out[k][p] == fold_chain(chains[p], rows[k][p])),
                [[out[k][p]]]))), [[out[k]]])))
        # invariants-end
        old = out  # type: PSeq[PSeq[int]]
        cr = apply_row(rows[j], chains, ncols)
        out = out + PSeq(cr)
        Assert(out[j] is cr)
        Assert(len(out[j]) == ncols)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
            out[k] is old[k]), [[out[k]]])))
        j = j + 1
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (project root; adversary run via python -m swebench_unified.adversary; nagini env swebench-nagini-verifier). Attacks built by copying model.py and editing ONLY the impl regions (lines 72-90 apply_row, 117-141 execute_returning, invariants included — all nested in impl and elided from the spec view); axioms/@Pure/Requires/Ensures kept byte-identical (a Python-side reconstruction of the original from the same builder asserted byte-identical to model.py before generating attacks). All 7 attacks confirmed same-spec (adversary same-spec exit 0).

POSITIVE CONTROL: bash scripts/nagini_verify.sh positive_control.py -> exit 0, 'Verification successful' (8.6s).
PREPATCH: prepatch.py (model_prepatch.py, raw passthrough) -> nagini_verify exit 1: 'Postcondition of execute_returning might not hold' at model line 111 (the Result()[j][p]==fold_chain clause); same-spec exit 0. Prepatch bug reproduced.

ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini django__django-14007 <path>; run concurrently <=3 at a time as background jobs):
- atk_1.py ECHO/gold-equivalent (inlined correct apply_row call per row): weakness exit 0 => CANDIDATE (shares spec AND verifies, 12.4s). MATERIALIZED faithful patch (= gold patch verbatim) and RAN run_resolve('django__django-14007', patch, timeout=1800): resolved=True, completed=True, note='resolved', attempts=1. Docker + image swebench/sweb.eval.x86_64.django_1776_django-14007 present. A resolving echo of gold is NOT a weakness (2026-08-06 policy).
- atk_2.py BOUNDARY (drop last row: while j < len(rows)-1): weakness exit 2 (verification failed). REJECTED.
- atk_3.py PARTIAL-DOMAIN on columns (fold only column 0, rest raw): weakness exit 2. REJECTED.
- atk_4.py OFF-BY-ONE column index (fold_chain(chains[p], row[(p+1)%ncols])): weakness exit 2. REJECTED.
- atk_5.py CONTROL-FLOW-EFFECT (double fold: fold_chain applied twice): weakness exit 2. REJECTED.
- atk_6.py UNGROUNDED-ORACLE/raw passthrough via different control flow (out + PSeq(rows[j])): weakness exit 2. REJECTED.
- atk_7.py PARTIAL-DOMAIN on rows (fold only row 0, rest raw): weakness exit 2. REJECTED.

So 6/6 genuinely-wrong impls are rejected by the verifier; the single verifying same-spec impl is gold-equivalent and its patch resolves. Reason it holds: both postconditions pin the output element-wise AND totally — len(Result())==len(rows), per-row width==ncols, and Result()[j][p]==fold_chain(chains[p], rows[j][p]) for all j,p — leaving zero observable freedom, so any verifying impl is behaviourally forced to equal gold on the tested inputs.

G-AX / A-LEG AUDIT: ran axiom_check.py -> exit 0: 'deep model execute_returning/apply_row/fold_chain == real apply_converters on 20009 boundary + fuzz cases; step axiom Ensures(True) trivially met'. refinement.md legs: A1 (rows param)=R, A2 (chains/ncols)=R, A3 (running the converter pipeline, modeled deeply as fold_chain+apply_row+execute_returning)=A-reference validated by G-AX against the real SQLCompiler.apply_converters, A4 (step = one value converter, weakest Ensures(True))=A-consumed, A5 (return converted rows)=I. NO kind-3 leg: the one operation that genuinely changed is modeled deeply, not hidden behind an axiom about the function-under-change; the only consumed axiom (step) covers an UNCHANGED single-converter callee. A-reference correspondence (fold_chain left-fold <-> the innermost per-converter fold in apply_converters, empty chain <-> untouched/omitted column <-> the 'if converters:' no-op guard) holds and is machine-validated by axiom_check.py. Model<->patch correspondence sound.

VERDICT: SOUND. >=5 attacks run (7 total, all fully verified/reported), the sole verifying candidate's materialized faithful patch was run through the official harness and RESOLVED, so no verify=>correct violation was exhibited; G-AX and refinement.md A-legs check out.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies. The only verifying same-spec attack (atk_1) is behaviourally gold-equivalent (correct per-row/per-column fold, exact length preservation), and its materialized faithful refined patch — the gold patch verbatim — RESOLVES under the official harness (run_resolve: resolved=True, completed=True, attempts=1). verify does NOT admit an incorrect impl here.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14007.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a row-returning database write hands back the freshly assigned column
  values, those raw values must be run through the per-column value-conversion
  pipeline before they reach the caller -- exactly as every other read path
  already does. Each returned column carries an ordered chain of value
  converters (possibly empty). The value the caller observes at a column is the
  left-fold of that column's converter chain over the raw value:

      observed = c_k(... c_2(c_1(raw)) ...)              for a chain c_1..c_k
      observed = raw                                     for an empty chain

  applied independently to every returned row and every column. A column whose
  chain is empty is therefore the identity (the raw value passes through), and a
  column whose chain is non-empty yields the converted value -- never the raw
  one. The number and shape of the returned rows is preserved exactly.

Rows are modelled as a pure sequence of pure rows, `PSeq[PSeq[int]]` (each row a
`PSeq[int]` of column values). Pure sequences carry no heap permission, so the
specification quantifies over rows and columns directly. A single converter step
is an opaque unchanged callee, `step(converter_id, value)`, axiomatized as a
@Pure @ContractOnly function; the conversion chain `fold_chain` and the row/grid
application are modelled deeply (front-recursive fold + verified loops) and
pinned element-wise by the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def step(converter_id: int, value: int) -> int:
    """One value converter applied to one value (an unchanged callee of the
    conversion pipeline; e.g. a field's stored value-restoration hook). Opaque:
    no relation between input and output is assumed, in particular it is NOT
    assumed to be the identity. Provenance + executable soundness: mapping.md /
    axiom_check.py (G-AX)."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def fold_chain(chain: PSeq[int], value: int) -> int:
    """Left-fold one column's converter chain over a raw value (front-recursive
    so a single unfold is available per loop step). An empty chain is the
    identity; otherwise each converter id is applied in order via `step`."""
    if len(chain) == 0:
        return value
    return fold_chain(chain.drop(1), step(chain[0], value))
# pure-end


def apply_row(row: PSeq[int], chains: PSeq[PSeq[int]], ncols: int) -> PSeq[int]:
    # pre-conditions-start
    Requires(ncols >= 0)
    Requires(len(row) == ncols)
    Requires(len(chains) == ncols)
    # pre-conditions-end
    # post-conditions-start
    # The converted row has the same width, and each column holds the fold of
    # that column's converter chain over the raw column value.
    Ensures(len(Result()) == ncols)
    Ensures(Forall(int, lambda p: (Implies(0 <= p and p < ncols,
        Result()[p] == fold_chain(chains[p], row[p])), [[Result()[p]]])))
    # post-conditions-end
    # impl-start
    out = PSeq(0).take(0)  # type: PSeq[int]
    p = 0
    while p < ncols:
        # invariants-start
        Invariant(0 <= p and p <= ncols)
        Invariant(len(row) == ncols)
        Invariant(len(chains) == ncols)
        Invariant(len(out) == p)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < p,
            out[k] == fold_chain(chains[k], row[k])), [[out[k]]])))
        # invariants-end
        old = out  # type: PSeq[int]
        nv = fold_chain(chains[p], row[p])
        out = out + PSeq(nv)
        Assert(out[p] == nv)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < p,
            out[k] == old[k]), [[out[k]]])))
        p = p + 1
    return out
    # impl-end


def execute_returning(rows: PSeq[PSeq[int]], chains: PSeq[PSeq[int]],
                      ncols: int) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(ncols >= 0)
    # one converter chain per returned column
    Requires(len(chains) == ncols)
    # every raw row has one value per returned column
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(rows),
        len(rows[j]) == ncols), [[rows[j]]])))
    # pre-conditions-end
    # post-conditions-start
    # Row count and width are preserved exactly.
    Ensures(len(Result()) == len(rows))
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(rows),
        len(Result()[j]) == ncols), [[Result()[j]]])))
    # Every observed value is the converter-chain fold over the raw value:
    # identity for an empty chain, the converted value for a non-empty chain.
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(rows),
        Forall(int, lambda p: (Implies(0 <= p and p < ncols,
            Result()[j][p] == fold_chain(chains[p], rows[j][p])),
            [[Result()[j][p]]]))), [[Result()[j]]])))
    # post-conditions-end
    # impl-start
    out = rows.take(0)  # type: PSeq[PSeq[int]]
    j = 0
    while j < len(rows):
        # invariants-start
        Invariant(0 <= j and j <= len(rows))
        Invariant(len(chains) == ncols)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(rows),
            len(rows[k]) == ncols), [[rows[k]]])))
        Invariant(len(out) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
            len(out[k]) == ncols), [[out[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
            Forall(int, lambda p: (Implies(0 <= p and p < ncols,
                out[k][p] == fold_chain(chains[p], rows[k][p])),
                [[out[k][p]]]))), [[out[k]]])))
        # invariants-end
        old = out  # type: PSeq[PSeq[int]]
        cr = apply_row(rows[j], chains, ncols)
        out = out + PSeq(cr)
        Assert(out[j] is cr)
        Assert(len(out[j]) == ncols)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
            out[k] is old[k]), [[out[k]]])))
        j = j + 1
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (project root; adversary run via python -m swebench_unified.adversary; nagini env swebench-nagini-verifier). Attacks built by copying model.py and editing ONLY the impl regions (lines 72-90 apply_row, 117-141 execute_returning, invariants included — all nested in impl and elided from the spec view); axioms/@Pure/Requires/Ensures kept byte-identical (a Python-side reconstruction of the original from the same builder asserted byte-identical to model.py before generating attacks). All 7 attacks confirmed same-spec (adversary same-spec exit 0).

POSITIVE CONTROL: bash scripts/nagini_verify.sh positive_control.py -> exit 0, 'Verification successful' (8.6s).
PREPATCH: prepatch.py (model_prepatch.py, raw passthrough) -> nagini_verify exit 1: 'Postcondition of execute_returning might not hold' at model line 111 (the Result()[j][p]==fold_chain clause); same-spec exit 0. Prepatch bug reproduced.

ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini django__django-14007 <path>; run concurrently <=3 at a time as background jobs):
- atk_1.py ECHO/gold-equivalent (inlined correct apply_row call per row): weakness exit 0 => CANDIDATE (shares spec AND verifies, 12.4s). MATERIALIZED faithful patch (= gold patch verbatim) and RAN run_resolve('django__django-14007', patch, timeout=1800): resolved=True, completed=True, note='resolved', attempts=1. Docker + image swebench/sweb.eval.x86_64.django_1776_django-14007 present. A resolving echo of gold is NOT a weakness (2026-08-06 policy).
- atk_2.py BOUNDARY (drop last row: while j < len(rows)-1): weakness exit 2 (verification failed). REJECTED.
- atk_3.py PARTIAL-DOMAIN on columns (fold only column 0, rest raw): weakness exit 2. REJECTED.
- atk_4.py OFF-BY-ONE column index (fold_chain(chains[p], row[(p+1)%ncols])): weakness exit 2. REJECTED.
- atk_5.py CONTROL-FLOW-EFFECT (double fold: fold_chain applied twice): weakness exit 2. REJECTED.
- atk_6.py UNGROUNDED-ORACLE/raw passthrough via different control flow (out + PSeq(rows[j])): weakness exit 2. REJECTED.
- atk_7.py PARTIAL-DOMAIN on rows (fold only row 0, rest raw): weakness exit 2. REJECTED.

So 6/6 genuinely-wrong impls are rejected by the verifier; the single verifying same-spec impl is gold-equivalent and its patch resolves. Reason it holds: both postconditions pin the output element-wise AND totally — len(Result())==len(rows), per-row width==ncols, and Result()[j][p]==fold_chain(chains[p], rows[j][p]) for all j,p — leaving zero observable freedom, so any verifying impl is behaviourally forced to equal gold on the tested inputs.

G-AX / A-LEG AUDIT: ran axiom_check.py -> exit 0: 'deep model execute_returning/apply_row/fold_chain == real apply_converters on 20009 boundary + fuzz cases; step axiom Ensures(True) trivially met'. refinement.md legs: A1 (rows param)=R, A2 (chains/ncols)=R, A3 (running the converter pipeline, modeled deeply as fold_chain+apply_row+execute_returning)=A-reference validated by G-AX against the real SQLCompiler.apply_converters, A4 (step = one value converter, weakest Ensures(True))=A-consumed, A5 (return converted rows)=I. NO kind-3 leg: the one operation that genuinely changed is modeled deeply, not hidden behind an axiom about the function-under-change; the only consumed axiom (step) covers an UNCHANGED single-converter callee. A-reference correspondence (fold_chain left-fold <-> the innermost per-converter fold in apply_converters, empty chain <-> untouched/omitted column <-> the 'if converters:' no-op guard) holds and is machine-validated by axiom_check.py. Model<->patch correspondence sound.

VERDICT: SOUND. >=5 attacks run (7 total, all fully verified/reported), the sole verifying candidate's materialized faithful patch was run through the official harness and RESOLVED, so no verify=>correct violation was exhibited; G-AX and refinement.md A-legs check out.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) audit of execute_returning vs SQLCompiler.apply_converters @ base_commit 619f26d2.

1. SAME-SPEC: model.py's spec region is byte-identical to the bundle (adversary same-spec exit 0).

2. REFERENCE FIDELITY: verified via `git show 619f26d2:django/db/models/sql/compiler.py` that the real apply_converters (compiler.py:1110-1119) is the nested left-fold `for row(map(list,rows)) -> for pos,(convs,expr) -> for converter in convs: value=converter(value,expr,conn); row[pos]=value; yield row`. axiom_check.py's _apply_converters_verbatim transcribes it verbatim. The model's fold_chain/apply_row/execute_returning reproduce exactly this: per-row per-column left-fold, empty chain = identity (matching get_converters omitting no-converter columns and the patch's `if converters:` no-op), row count + width preserved.

3. INDEPENDENT DIFFERENTIAL: I ran a 200000-case fuzz (0..5 rows x 0..5 cols, chains up to length 3) comparing the real 3-arg apply_converters against the model's value-only fold. Crucially I used converters that DEPEND on expression (column index, fixed per column) and connection (fixed per query) -- the only channels through which the real converter(value,expr,conn) could differ from step(converter_id,value). ZERO divergence. Sound because expr/conn are constant within a column/query, so each real converter reduces to a pure fn of value -- precisely what step models.

4. NON-VACUITY / DISCRIMINATION: pre-patch execute_sql returns the raw rows (confirmed at base_commit); the prepatch model reproduces that and FAILS the discriminating postcondition Result()[j][p]==fold_chain(chains[p],rows[j][p]) on a non-empty chain (step opaque, not provably identity). So the spec is not too weak either.

The spec pins observed = fold of the chain with step opaque (Ensures(True)) -- exactly the real behavior and no stronger. No diverging input exists between the modeled function and the real callee. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over the projected spec_view) passes with zero hard failures. Manual confirmation: (1) No diff markers, patched file paths ('django/db/models/sql/compiler.py'), or module paths in the spec view. (2) No gold-patch lines reproduced — impl regions are elided ('... implementation elided'); spec postconditions are abstract (fold_chain / PSeq[PSeq[int]] left-fold), not the patch's concrete 'cols = [field.get_col(...)]' / 'converters = self.get_converters(cols)' / 'rows = list(self.apply_converters(rows, converters))'. (3) The single distinctive changed symbol ('execute_sql') and the newly-called repo callees (apply_converters, get_converters, get_col, fetch_returned_insert_rows) appear NOWHERE in the spec view — the model uses neutral names (execute_returning, apply_row, fold_chain, step). Those repo symbols are confined to mapping.md/refinement.md, which are auditor docs, not the consumer spec view. (4) No bug/fix/regression narration in comments or docstrings. (5) The behavioral description ('returned raw values must be run through the per-column value-conversion pipeline before reaching the caller, as every other read path already does') is a restatement of the desired behavior already public in problem_statement ('Database converters (from_db_value) not called for returning_fields on insert'), not a disclosure of the edit. The spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
