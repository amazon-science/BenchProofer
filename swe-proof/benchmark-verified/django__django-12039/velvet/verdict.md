# P2 adversarial audit — django__django-12039

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_no_empty_guard.lean`, `atk_3_boundary.lean`, `atk_4_drop_suffix.lean`, `atk_5_two_space.lean`, `atk_7_index0.lean`, `atk_8_nospace_guard.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec's postcondition `out = columnText name suffixes idx` fully pins the output for ALL inputs (no preconditions; total termination). Every behaviorally-distinct wrong impl fails prove_correct. The only verifying attack (atk_6_echo) returns `columnText name suffixes idx` verbatim — behaviorally identical to the gold — and its faithful refined patch (the gold patch) RESOLVES=True. verify ⇒ correct holds.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,9 +41,7 @@
     -- impl-start
     let mut col := name
     if idx < suffixes.length then
-      let suffix := suffixes[idx]!
-      if suffix ≠ [] then
-        col := name ++ ' ' :: suffix
+      col := name ++ suffixes[idx]!
     return col
     -- impl-end
 
```

Attack 2 — `atk_2_no_empty_guard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,9 +41,7 @@
     -- impl-start
     let mut col := name
     if idx < suffixes.length then
-      let suffix := suffixes[idx]!
-      if suffix ≠ [] then
-        col := name ++ ' ' :: suffix
+      col := name ++ ' ' :: suffixes[idx]!
     return col
     -- impl-end
 
```

Attack 3 — `atk_3_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,7 @@
   do
     -- impl-start
     let mut col := name
-    if idx < suffixes.length then
+    if idx <= suffixes.length then
       let suffix := suffixes[idx]!
       if suffix ≠ [] then
         col := name ++ ' ' :: suffix
```

Attack 4 — `atk_4_drop_suffix.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,11 +39,7 @@
   ensures out = columnText name suffixes idx
   do
     -- impl-start
-    let mut col := name
-    if idx < suffixes.length then
-      let suffix := suffixes[idx]!
-      if suffix ≠ [] then
-        col := name ++ ' ' :: suffix
+    let col := name
     return col
     -- impl-end
 
```

Attack 5 — `atk_5_two_space.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
     if idx < suffixes.length then
       let suffix := suffixes[idx]!
       if suffix ≠ [] then
-        col := name ++ ' ' :: suffix
+        col := name ++ ' ' :: ' ' :: suffix
     return col
     -- impl-end
 
```

Attack 6 — `atk_6_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -39,12 +39,7 @@
   ensures out = columnText name suffixes idx
   do
     -- impl-start
-    let mut col := name
-    if idx < suffixes.length then
-      let suffix := suffixes[idx]!
-      if suffix ≠ [] then
-        col := name ++ ' ' :: suffix
-    return col
+    return columnText name suffixes idx
     -- impl-end
 
 prove_correct renderColumn by
```

Attack 7 — `atk_7_index0.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,8 +40,8 @@
   do
     -- impl-start
     let mut col := name
-    if idx < suffixes.length then
-      let suffix := suffixes[idx]!
+    if 0 < suffixes.length then
+      let suffix := suffixes[0]!
       if suffix ≠ [] then
         col := name ++ ' ' :: suffix
     return col
```

Attack 8 — `atk_8_nospace_guard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,7 +43,7 @@
     if idx < suffixes.length then
       let suffix := suffixes[idx]!
       if suffix ≠ [] then
-        col := name ++ ' ' :: suffix
+        col := name ++ suffix
     return col
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees. The per-column rendering is spelled out directly as
   `columnText` below. The column-name token is taken as an input carrier
   (mapping.md §2), so the name-quoting helper is not represented as an axiom. -/
-- axioms-end

-- pure-start
/- The textual form of one indexed column reference. A column is rendered as
   its name token, optionally followed by a trailing qualifier. A qualifier is
   appended only when one is supplied for this position (`idx` is within the
   supplied list) AND that qualifier is non-empty; in that case exactly one
   space separates the name from the qualifier. An absent qualifier (`idx`
   beyond the supplied list) or an empty qualifier contributes nothing — not
   even a separating space. -/
def columnText (name : List Char) (suffixes : List (List Char)) (idx : Nat) :
    List Char :=
  if idx < suffixes.length then
    if suffixes[idx]! = [] then name
    else name ++ ' ' :: suffixes[idx]!
  else name
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method renderColumn (name : List Char) (suffixes : List (List Char)) (idx : Nat)
    return (out : List Char)
  ensures out = columnText name suffixes idx
  do
    -- impl-start
    let mut col := name
    if idx < suffixes.length then
      let suffix := suffixes[idx]!
      if suffix ≠ [] then
        col := name ++ ' ' :: suffix
    return col
    -- impl-end

prove_correct renderColumn by
  loom_solve <;> simp_all [columnText]
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed. same_spec=True for all 8 attacks + positive control (verified via swebench_unified.markers.same_spec with velvet backend). Verification via `bash scripts/lean_verify.sh <file>` (run concurrently, ≤4/batch):

- pos_control.lean (gold impl): EXIT 0 (verifies, no sorry) ✓
- atk_1_prepatch.lean (bare concat `name ++ suffixes[idx]!`, no space — the prepatch bug): EXIT 1. Unsolved goal `name ++ suffixes[idx] = if suffixes[idx]=[] then name else name ++ ' ' :: suffixes[idx]` → PREPATCH REPRODUCED. Fails on non-empty-qualifier case ("name"DESC vs "name" DESC, the F2P test_descending_columns_list_sql).
- atk_2_no_empty_guard.lean (append even when empty → trailing space): EXIT 1 (dropped empty-qualifier guard).
- atk_3_boundary.lean (off-by-one `idx <= suffixes.length`, hits default): EXIT 1.
- atk_4_drop_suffix.lean (control-flow: always return bare name): EXIT 1.
- atk_5_two_space.lean (two-space separator): EXIT 1.
- atk_6_echo.lean (ungrounded-oracle echo: `return columnText name suffixes idx`): EXIT 0 — VERIFIES. Behaviorally identical to gold. Per protocol its faithful refined patch (= gold patch, the R/I transliteration of columnText into col_str) was materialized and RUN through official harness: run_resolve('django__django-12039', patch, timeout=1800) → RESOLVED=True, note='resolved'. Does NOT break the spec.
- atk_7_index0.lean (partial-domain: always suffixes[0], ignores idx): EXIT 1.
- atk_8_nospace_guard.lean (keep empty-guard but no space): EXIT 1.

Attack classes covered: prepatch bug, boundary (off-by-one), control-flow-effect (drop suffix / two-space), partial-domain (index0), missing-guard (no_empty_guard, nospace_guard), ungrounded-oracle echo. 6 distinct behaviorally-wrong impls all correctly REJECTED by the spec; only the behaviorally-equivalent echo verifies and its patch resolves.

Refinement audit: meta.json axioms=[], deep_model_references=[] — NO A-legs (matches refinement.md §C / mapping.md §3). All legs are R (str↔List Char carrier, quote_name identity, positions) or I (bounds test A3, non-empty+space A4, return A5, ', '.join glue A6). No kind-3 (inexpressible-changed-op) legs: the changed op — per-column qualifier rendering — is modeled DEEPLY as columnText, not hidden behind an axiom. The single test-neutral parallel site (IndexColumns.__str__, PostgreSQL-only @skipUnless/@skipIf tests, skipped on SQLite eval image) is the same op, correctly audited by refinement.md §B without a separate modeled method. R/I legs mechanically covered by G-CONF (conformance_check.py, seed 12039, quote_name=identity, full Columns.__str__ render over ≥1e5 inputs).

Conclusion: verify ⇒ correct. No verifying wrong impl whose faithful patch fails resolve was found. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_no_empty_guard.lean`, `atk_3_boundary.lean`, `atk_4_drop_suffix.lean`, `atk_5_two_space.lean`, `atk_7_index0.lean`, `atk_8_nospace_guard.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec's postcondition `out = columnText name suffixes idx` fully pins the output for ALL inputs (no preconditions; total termination). Every behaviorally-distinct wrong impl fails prove_correct. The only verifying attack (atk_6_echo) returns `columnText name suffixes idx` verbatim — behaviorally identical to the gold — and its faithful refined patch (the gold patch) RESOLVES=True. verify ⇒ correct holds.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_no_empty_guard.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_drop_suffix.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_two_space.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_index0.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_nospace_guard.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees. The per-column rendering is spelled out directly as
   `columnText` below. The column-name token is taken as an input carrier
   (mapping.md §2), so the name-quoting helper is not represented as an axiom. -/
-- axioms-end

-- pure-start
/- The textual form of one indexed column reference. A column is rendered as
   its name token, optionally followed by a trailing qualifier. A qualifier is
   appended only when one is supplied for this position (`idx` is within the
   supplied list) AND that qualifier is non-empty; in that case exactly one
   space separates the name from the qualifier. An absent qualifier (`idx`
   beyond the supplied list) or an empty qualifier contributes nothing — not
   even a separating space. -/
def columnText (name : List Char) (suffixes : List (List Char)) (idx : Nat) :
    List Char :=
  if idx < suffixes.length then
    if suffixes[idx]! = [] then name
    else name ++ ' ' :: suffixes[idx]!
  else name
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method renderColumn (name : List Char) (suffixes : List (List Char)) (idx : Nat)
    return (out : List Char)
  ensures out = columnText name suffixes idx
  do
    -- impl-start
    let mut col := name
    if idx < suffixes.length then
      let suffix := suffixes[idx]!
      if suffix ≠ [] then
        col := name ++ ' ' :: suffix
    return col
    -- impl-end

prove_correct renderColumn by
  loom_solve <;> simp_all [columnText]
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed. same_spec=True for all 8 attacks + positive control (verified via swebench_unified.markers.same_spec with velvet backend). Verification via `bash scripts/lean_verify.sh <file>` (run concurrently, ≤4/batch):

- pos_control.lean (gold impl): EXIT 0 (verifies, no sorry) ✓
- atk_1_prepatch.lean (bare concat `name ++ suffixes[idx]!`, no space — the prepatch bug): EXIT 1. Unsolved goal `name ++ suffixes[idx] = if suffixes[idx]=[] then name else name ++ ' ' :: suffixes[idx]` → PREPATCH REPRODUCED. Fails on non-empty-qualifier case ("name"DESC vs "name" DESC, the F2P test_descending_columns_list_sql).
- atk_2_no_empty_guard.lean (append even when empty → trailing space): EXIT 1 (dropped empty-qualifier guard).
- atk_3_boundary.lean (off-by-one `idx <= suffixes.length`, hits default): EXIT 1.
- atk_4_drop_suffix.lean (control-flow: always return bare name): EXIT 1.
- atk_5_two_space.lean (two-space separator): EXIT 1.
- atk_6_echo.lean (ungrounded-oracle echo: `return columnText name suffixes idx`): EXIT 0 — VERIFIES. Behaviorally identical to gold. Per protocol its faithful refined patch (= gold patch, the R/I transliteration of columnText into col_str) was materialized and RUN through official harness: run_resolve('django__django-12039', patch, timeout=1800) → RESOLVED=True, note='resolved'. Does NOT break the spec.
- atk_7_index0.lean (partial-domain: always suffixes[0], ignores idx): EXIT 1.
- atk_8_nospace_guard.lean (keep empty-guard but no space): EXIT 1.

Attack classes covered: prepatch bug, boundary (off-by-one), control-flow-effect (drop suffix / two-space), partial-domain (index0), missing-guard (no_empty_guard, nospace_guard), ungrounded-oracle echo. 6 distinct behaviorally-wrong impls all correctly REJECTED by the spec; only the behaviorally-equivalent echo verifies and its patch resolves.

Refinement audit: meta.json axioms=[], deep_model_references=[] — NO A-legs (matches refinement.md §C / mapping.md §3). All legs are R (str↔List Char carrier, quote_name identity, positions) or I (bounds test A3, non-empty+space A4, return A5, ', '.join glue A6). No kind-3 (inexpressible-changed-op) legs: the changed op — per-column qualifier rendering — is modeled DEEPLY as columnText, not hidden behind an axiom. The single test-neutral parallel site (IndexColumns.__str__, PostgreSQL-only @skipUnless/@skipIf tests, skipped on SQLite eval image) is the same op, correctly audited by refinement.md §B without a separate modeled method. R/I legs mechanically covered by G-CONF (conformance_check.py, seed 12039, quote_name=identity, full Columns.__str__ render over ≥1e5 inputs).

Conclusion: verify ⇒ correct. No verifying wrong impl whose faithful patch fails resolve was found. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for the modeled site Columns.__str__.col_str (django/db/backends/ddl_references.py:85), modeled as `columnText`.

Spec integrity: swebench_unified.markers.same_spec(Solution, prepatch, velvet backend) = True; the spec view elides only impl/proof and the columnText model + `ensures out = columnText name suffixes idx` pass through unchanged.

Model vs real post-patch behavior: reconstructed the real patched col_str from the gold patch and the base_commit (58c1acb) source — with quote_name = identity per mapping.md §2:
  col = name; try: suffix = suffixes[idx]; if suffix: col = '{} {}'.format(col, suffix); except IndexError: pass; return col.
Bijection: Python str '' ↔ Lean []; idx>=len ↔ idx>=suffixes.length. The Lean columnText is:
  if idx < len: (if suffixes[idx]=[] then name else name ++ ' ' :: suffixes[idx]) else name.
These are point-for-point identical: in-range empty suffix -> bare name (no space); in-range non-empty suffix -> name + single space + suffix; out-of-range -> bare name (mirrors the IndexError/pass path).

Differential testing (independent of the recorded G-CONF): 200k random inputs (names over 'ab {}', suffix lists over ['','DESC','ASC','x','a b',' ','{}','DE SC'], idx 0..6) -> 0 disagreements; plus a structured-exhaustive sweep over names ∈ {'', 'n', '"n"', 'na me', '{}', ' '} × suffix-lists of length 0..3 over 14 tokens (incl. whitespace-only ' ', '\t', unicode 'É', format-looking '{}','{0}') × idx 0..L+2 -> 0 disagreements. Whitespace-only suffixes (truthy in Python) are correctly appended with one space by both; empty string is correctly falsy in both. Recorded G-CONF also passed on 100008 inputs (seed=12039), 0 disagreements.

The model is neither too strong nor drifted: it agrees with the real callee on every tested input, and the branch structure exactly matches the real control flow. The parallel IndexColumns site is test-neutral (PostgreSQL-only, skipped on SQLite eval image) and applies the byte-identical whitespace fix, so it does not affect faithfulness for the observed tests. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorously checked. Mechanical leakage.screen (velvet/lean flavor) over the spec_view returns passed=True, 0 hard failures. same_spec(Solution, Solution_prepatch)=True; spec regions byte-identical. No RELAXED_LEAKAGE.md / relaxed_leakage flag (deferral N/A).

Spec view contents: the `columnText` model + its docstring, the `renderColumn` signature with `ensures out = columnText name suffixes idx`; impl and proof are elided.

Semantic leakage analysis vs the SOLVER-VISIBLE problem_statement only (not hints_text):
- The public problem statement already fully mandates the target behavior: expected `"name" DESC` (exactly one separating space), the empty-suffix/ascending case must NOT emit a trailing space, and it explicitly states col_suffixes "will contain empty strings." The columnText behavior (non-empty qualifier -> name ++ ' ' :: qualifier with one space; empty '' or out-of-range -> bare name) is precisely the publicly-specified expected output — a spec is supposed to encode correct behavior; this does not exceed the public task.
- No repo-localizing tokens leak: spec view contains none of col_str, col_suffixes, quote_name, IndexError, opclasses, text_pattern_ops, ddl_references, Columns/IndexColumns, no patched file/module path, no diff markers, no reproduced gold-patch line, no bug/fix narration terms.
- The gold edit's mechanics (try/except IndexError, '{} {}'.format, the col accumulator) are NOT revealed; only the required input/output relation the problem statement already describes.

Conclusion: the spec view does not disclose the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
