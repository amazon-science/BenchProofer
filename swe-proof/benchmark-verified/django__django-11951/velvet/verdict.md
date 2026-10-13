# P2 adversarial audit — django__django-11951

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verifying wrong impl exists. The ensures clause `(batchSize=0 → n=maxBatchSize) ∧ (batchSize>0 → n=min batchSize maxBatchSize)` pins n EXACTLY on the entire reachable domain (batchSize:Nat, maxBatchSize≥1, and repo's max(...,1)≥1 excludes nothing reachable). The only other verifying impl (atk_7 = `min maxBatchSize batchSize`) is the commutative echo of gold and its faithful patch RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The database-computed compatible maximum is taken as
@@ -45,7 +45,7 @@
     if batchSize = 0 then
       return maxBatchSize
     else
-      return min batchSize maxBatchSize
+      return batchSize
     -- impl-end
 
 prove_correct effectiveBatchSize by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The database-computed compatible maximum is taken as
@@ -45,7 +45,7 @@
     if batchSize = 0 then
       return maxBatchSize
     else
-      return min batchSize maxBatchSize
+      return max batchSize maxBatchSize
     -- impl-end
 
 prove_correct effectiveBatchSize by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The database-computed compatible maximum is taken as
@@ -42,10 +42,7 @@
   ensures (batchSize = 0 → n = maxBatchSize) ∧ (batchSize > 0 → n = min batchSize maxBatchSize)
   do
     -- impl-start
-    if batchSize = 0 then
-      return maxBatchSize
-    else
-      return min batchSize maxBatchSize
+    return min batchSize maxBatchSize
     -- impl-end
 
 prove_correct effectiveBatchSize by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The database-computed compatible maximum is taken as
@@ -42,7 +42,7 @@
   ensures (batchSize = 0 → n = maxBatchSize) ∧ (batchSize > 0 → n = min batchSize maxBatchSize)
   do
     -- impl-start
-    if batchSize = 0 then
+    if batchSize <= 1 then
       return maxBatchSize
     else
       return min batchSize maxBatchSize
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The database-computed compatible maximum is taken as
@@ -42,10 +42,7 @@
   ensures (batchSize = 0 → n = maxBatchSize) ∧ (batchSize > 0 → n = min batchSize maxBatchSize)
   do
     -- impl-start
-    if batchSize = 0 then
-      return maxBatchSize
-    else
-      return min batchSize maxBatchSize
+    return maxBatchSize
     -- impl-end
 
 prove_correct effectiveBatchSize by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The database-computed compatible maximum is taken as
@@ -42,10 +42,7 @@
   ensures (batchSize = 0 → n = maxBatchSize) ∧ (batchSize > 0 → n = min batchSize maxBatchSize)
   do
     -- impl-start
-    if batchSize = 0 then
-      return maxBatchSize
-    else
-      return min batchSize maxBatchSize
+    return batchSize
     -- impl-end
 
 prove_correct effectiveBatchSize by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The database-computed compatible maximum is taken as
@@ -45,7 +45,7 @@
     if batchSize = 0 then
       return maxBatchSize
     else
-      return min batchSize maxBatchSize
+      return min maxBatchSize batchSize
     -- impl-end
 
 prove_correct effectiveBatchSize by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The database-computed compatible maximum is taken as
--  a plain non-zero input — the operation under spec does not change how that
--  maximum is produced; the floor-at-one is captured by `require`.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When records are written to the store in chunks, two chunk-size figures meet:
   a size the caller may explicitly request, and a size the store reports as the
   largest it can accept in one round-trip. The caller's request is optional — a
   value of zero means "no explicit request, decide for me."

   The effective chunk size must always honour BOTH figures. When the caller
   makes no request, the store's reported maximum is used as-is. When the caller
   does request a size, that request must still be capped at the store's
   maximum — the smaller of the two wins — so a caller can never force a chunk
   larger than the store can handle.

   The reported maximum is read-only (not `mut`) and is always at least one (the
   store never reports a zero capacity); the requested size is read-only too. The
   operation derives a single size and mutates nothing (directive 5). Both inputs
   and the result are modeled as `Nat`. -/
method effectiveBatchSize (batchSize : Nat) (maxBatchSize : Nat) return (n : Nat)
  require maxBatchSize ≥ 1
  ensures (batchSize = 0 → n = maxBatchSize) ∧ (batchSize > 0 → n = min batchSize maxBatchSize)
  do
    -- impl-start
    if batchSize = 0 then
      return maxBatchSize
    else
      return min batchSize maxBatchSize
    -- impl-end

prove_correct effectiveBatchSize by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL RESULTS. same_spec(velvet) == True for all 8 files (pos_control + atk_1..7). Verify cmd: `bash scripts/lean_verify.sh <D>/<f>.lean`, run concurrently ≤4 at a time in two batches.

### Results
- pos_control.lean (gold verbatim): EXIT 0 — VERIFIES (positive control OK).
- atk_1.lean (PREPATCH BUG, raw batchSize in nonzero branch): EXIT 1 — FAILS. Unsolved goal `batchSize > 0 → batchSize = min batchSize maxBatchSize` (cap-ignoring bug reproduced exactly).
- atk_2.lean (boundary: `max batchSize maxBatchSize`): EXIT 1 — FAILS. Goal `max = min` unsolvable.
- atk_3.lean (partial-domain: unconditional `min batchSize maxBatchSize`, drops the zero branch): EXIT 1 — FAILS. Goal `batchSize=0 → min batchSize maxBatchSize = maxBatchSize` (=0≠maxBatchSize).
- atk_4.lean (control-flow off-by-one: `batchSize ≤ 1 → maxBatchSize`): EXIT 1 — FAILS. Goal at batchSize=1 `maxBatchSize = min 1 maxBatchSize`.
- atk_5.lean (ungrounded-oracle echo: return maxBatchSize unconditionally): EXIT 1 — FAILS. Goal `batchSize>0 → maxBatchSize = min batchSize maxBatchSize`.
- atk_6.lean (control-flow-effect: return batchSize unconditionally, no branch): EXIT 1 — FAILS. Both conjuncts unsolved.
- atk_7.lean (commutative echo: `min maxBatchSize batchSize`): EXIT 0 — VERIFIES. This equals gold's `min batchSize maxBatchSize` by Nat.min commutativity, i.e. a CORRECT impl, not a wrong one.

ECHO RESOLVE CHECK (mandatory for verifying impl): materialized atk_7.patch (transliterated `min(max_batch_size, batch_size)`) and ran `run_resolve('django__django-11951', ...timeout=1200,retries=1)` → RESOLVED=True COMPLETED=True NOTE='resolved'. So the only verifying non-gold impl is a RESOLVING echo (not a weakness per G-PANEL-1/eq echo policy) — spec is NOT broken.

REFINEMENT.MD AUDIT: 4 legs — A1 R (int|None↔Nat, None/0↔0), A2 R (max(bulk_batch_size,1) abstracted as plain input maxBatchSize; max(...,1) floor ↔ require maxBatchSize≥1; identical pre/post-fix ⇒ correctly NOT axiomatized), A3 I (zero→maxBatchSize, identical control), A4 I (nonzero→min, identical). NO A-legs (no axioms), NO kind-3 legs. Callee correspondence holds: bulk_batch_size unchanged by patch, R-abstracted; G-AX skip legitimate; no axiom_check.py. The changed min/max combination logic is modeled deeply and tagged I; correspondence to gold source line `min(batch_size,max_batch_size) if batch_size else max_batch_size` holds exactly.

CONCLUSION: 6 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, prepatch) all FAIL to verify against the byte-identical tight spec; positive control verifies; prepatch reproduced with the discriminating counterexample; the sole verifying non-gold impl resolves. verify⇒correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verifying wrong impl exists. The ensures clause `(batchSize=0 → n=maxBatchSize) ∧ (batchSize>0 → n=min batchSize maxBatchSize)` pins n EXACTLY on the entire reachable domain (batchSize:Nat, maxBatchSize≥1, and repo's max(...,1)≥1 excludes nothing reachable). The only other verifying impl (atk_7 = `min maxBatchSize batchSize`) is the commutative echo of gold and its faithful patch RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The database-computed compatible maximum is taken as
--  a plain non-zero input — the operation under spec does not change how that
--  maximum is produced; the floor-at-one is captured by `require`.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When records are written to the store in chunks, two chunk-size figures meet:
   a size the caller may explicitly request, and a size the store reports as the
   largest it can accept in one round-trip. The caller's request is optional — a
   value of zero means "no explicit request, decide for me."

   The effective chunk size must always honour BOTH figures. When the caller
   makes no request, the store's reported maximum is used as-is. When the caller
   does request a size, that request must still be capped at the store's
   maximum — the smaller of the two wins — so a caller can never force a chunk
   larger than the store can handle.

   The reported maximum is read-only (not `mut`) and is always at least one (the
   store never reports a zero capacity); the requested size is read-only too. The
   operation derives a single size and mutates nothing (directive 5). Both inputs
   and the result are modeled as `Nat`. -/
method effectiveBatchSize (batchSize : Nat) (maxBatchSize : Nat) return (n : Nat)
  require maxBatchSize ≥ 1
  ensures (batchSize = 0 → n = maxBatchSize) ∧ (batchSize > 0 → n = min batchSize maxBatchSize)
  do
    -- impl-start
    if batchSize = 0 then
      return maxBatchSize
    else
      return min batchSize maxBatchSize
    -- impl-end

prove_correct effectiveBatchSize by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL RESULTS. same_spec(velvet) == True for all 8 files (pos_control + atk_1..7). Verify cmd: `bash scripts/lean_verify.sh <D>/<f>.lean`, run concurrently ≤4 at a time in two batches.

### Results
- pos_control.lean (gold verbatim): EXIT 0 — VERIFIES (positive control OK).
- atk_1.lean (PREPATCH BUG, raw batchSize in nonzero branch): EXIT 1 — FAILS. Unsolved goal `batchSize > 0 → batchSize = min batchSize maxBatchSize` (cap-ignoring bug reproduced exactly).
- atk_2.lean (boundary: `max batchSize maxBatchSize`): EXIT 1 — FAILS. Goal `max = min` unsolvable.
- atk_3.lean (partial-domain: unconditional `min batchSize maxBatchSize`, drops the zero branch): EXIT 1 — FAILS. Goal `batchSize=0 → min batchSize maxBatchSize = maxBatchSize` (=0≠maxBatchSize).
- atk_4.lean (control-flow off-by-one: `batchSize ≤ 1 → maxBatchSize`): EXIT 1 — FAILS. Goal at batchSize=1 `maxBatchSize = min 1 maxBatchSize`.
- atk_5.lean (ungrounded-oracle echo: return maxBatchSize unconditionally): EXIT 1 — FAILS. Goal `batchSize>0 → maxBatchSize = min batchSize maxBatchSize`.
- atk_6.lean (control-flow-effect: return batchSize unconditionally, no branch): EXIT 1 — FAILS. Both conjuncts unsolved.
- atk_7.lean (commutative echo: `min maxBatchSize batchSize`): EXIT 0 — VERIFIES. This equals gold's `min batchSize maxBatchSize` by Nat.min commutativity, i.e. a CORRECT impl, not a wrong one.

ECHO RESOLVE CHECK (mandatory for verifying impl): materialized atk_7.patch (transliterated `min(max_batch_size, batch_size)`) and ran `run_resolve('django__django-11951', ...timeout=1200,retries=1)` → RESOLVED=True COMPLETED=True NOTE='resolved'. So the only verifying non-gold impl is a RESOLVING echo (not a weakness per G-PANEL-1/eq echo policy) — spec is NOT broken.

REFINEMENT.MD AUDIT: 4 legs — A1 R (int|None↔Nat, None/0↔0), A2 R (max(bulk_batch_size,1) abstracted as plain input maxBatchSize; max(...,1) floor ↔ require maxBatchSize≥1; identical pre/post-fix ⇒ correctly NOT axiomatized), A3 I (zero→maxBatchSize, identical control), A4 I (nonzero→min, identical). NO A-legs (no axioms), NO kind-3 legs. Callee correspondence holds: bulk_batch_size unchanged by patch, R-abstracted; G-AX skip legitimate; no axiom_check.py. The changed min/max combination logic is modeled deeply and tagged I; correspondence to gold source line `min(batch_size,max_batch_size) if batch_size else max_batch_size` holds exactly.

CONCLUSION: 6 distinct wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, prepatch) all FAIL to verify against the byte-identical tight spec; positive control verifies; prepatch reproduced with the discriminating counterexample; the sole verifying non-gold impl resolves. verify⇒correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-11951 velvet bundle. No diverging input found; the modeled function agrees with the real callee everywhere in-domain.

SPEC REGION INTEGRITY: swebench_unified.markers.same_spec(Solution, prepatch, velvet) = True — spec region is byte-identical. Spec view is clean (impl elided, prove_correct body elided; no leakage of impl into the spec).

SPEC: method effectiveBatchSize (batchSize maxBatchSize : Nat) return (n : Nat); require maxBatchSize ≥ 1; ensures (batchSize = 0 → n = maxBatchSize) ∧ (batchSize > 0 → n = min batchSize maxBatchSize).

### REAL REPO (base_commit 3120490912, django/db/models/query.py:1212, gold-patched _batched_insert):
  max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)
  batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size

WHY NOT TOO-STRONG (over-restrictive precondition): require maxBatchSize ≥ 1 exactly mirrors the max(..., 1) floor the real callee always applies — it excludes NO reachable input. bulk_create's `assert batch_size is None or batch_size > 0` and bulk_update's ValueError on <0 confirm batch_size is a non-negative count, so the Nat carrier and the batchSize=0 (None/0 truthiness) branch mapping are exact — no drift.

WHY NOT UNDER/DRIFT: for batchSize=0 spec gives maxBatchSize (Python else branch); for batchSize>0 spec gives min batchSize maxBatchSize (Python min, Nat.min ≡ Python min on non-negatives). Every input matches.

### Evidence
- G-CONF differential SHADOW vs verbatim patched-source ORACLE over 200,035 (batch_size,max_batch_size) pairs (boundary + fuzz, seed 11951, max_batch_size≥1): 0 disagreements (re-ran, exit 0).
- lean_verify.sh Solution.lean: exit 0 (verifies).
- lean_verify.sh Solution_prepatch.lean (returns raw batchSize): exit 1, counterexample a-b≥1 i.e. batchSize>maxBatchSize — confirms the spec is non-vacuous and discriminates the cap-ignoring bug (F2P test_explicit_batch_size_respects_max_batch_size).

Conclusion: spec is a faithful model of the real callee; not too strong, no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. (1) markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend language) == True — spec region byte-identical; the discriminating impl branch (min batchSize maxBatchSize vs raw batchSize) and the prove_correct proof are BOTH elided from the rendered spec_view (impl shows 'implementation elided', proof shows 'proof elided'), so the spec view cannot leak the gold edit via impl/proof. (2) The only behavior-describing spec-view content is the ensures clause `(batchSize = 0 -> n = maxBatchSize) AND (batchSize > 0 -> n = min batchSize maxBatchSize)` plus the prose docstring ('smaller of the two wins', 'capped at the store's maximum', zero = no explicit request). (3) Fetched the real public problem_statement from data/swe_bench_verified/test.jsonl: it discloses the gold edit VERBATIM — 'batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size' — names the file behavior and the bug ('bulk_create batch_size param overrides the compatible batch size calculation'). hints_text is empty (''), and is out of scope regardless. The ensures clause is a faithful mathematical restatement of the min(...) if batch_size else max_batch_size formula already fully public in problem_statement; the zero=unspecified mapping is the standard Python `if batch_size:` truthiness reading already implicit in the disclosed guard. No spec-view line reveals anything beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
