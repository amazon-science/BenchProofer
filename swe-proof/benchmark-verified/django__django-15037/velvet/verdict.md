# P2 adversarial audit — django__django-15037

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,20 +68,11 @@
   ensures out = targetQualifier isUniqueRef refColumn idKey
   do
     -- impl-start
-    -- A one-to-one / identity link never carries an explicit qualifier.
-    if isUniqueRef then
-      return none
-    else
-      -- A plain many-to-one link: consult the target collection's identity key.
-      match idKey with
-      | none   => return none
-      | some k =>
-        -- Qualify only when the identity key is a present, non-empty column
-        -- that differs from the column actually referenced.
-        if k ≠ [] ∧ k ≠ refColumn then
-          return (some refColumn)
-        else
-          return none
+    -- ATTACK: prepatch — never consults idKey, always none.
+    let _ := isUniqueRef
+    let _ := refColumn
+    let _ := idKey
+    return none
     -- impl-end
 
 prove_correct qualifyReference by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,17 +68,14 @@
   ensures out = targetQualifier isUniqueRef refColumn idKey
   do
     -- impl-start
-    -- A one-to-one / identity link never carries an explicit qualifier.
+    -- ATTACK: drops the non-empty (k != []) guard.
     if isUniqueRef then
       return none
     else
-      -- A plain many-to-one link: consult the target collection's identity key.
       match idKey with
       | none   => return none
       | some k =>
-        -- Qualify only when the identity key is a present, non-empty column
-        -- that differs from the column actually referenced.
-        if k ≠ [] ∧ k ≠ refColumn then
+        if k ≠ refColumn then
           return (some refColumn)
         else
           return none
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,17 +68,14 @@
   ensures out = targetQualifier isUniqueRef refColumn idKey
   do
     -- impl-start
-    -- A one-to-one / identity link never carries an explicit qualifier.
+    -- ATTACK: inverted distinctness test (k = refColumn instead of !=).
     if isUniqueRef then
       return none
     else
-      -- A plain many-to-one link: consult the target collection's identity key.
       match idKey with
       | none   => return none
       | some k =>
-        -- Qualify only when the identity key is a present, non-empty column
-        -- that differs from the column actually referenced.
-        if k ≠ [] ∧ k ≠ refColumn then
+        if k ≠ [] ∧ k = refColumn then
           return (some refColumn)
         else
           return none
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,20 +68,17 @@
   ensures out = targetQualifier isUniqueRef refColumn idKey
   do
     -- impl-start
-    -- A one-to-one / identity link never carries an explicit qualifier.
+    -- ATTACK: qualifier attached on the identity (unique) branch instead.
     if isUniqueRef then
-      return none
-    else
-      -- A plain many-to-one link: consult the target collection's identity key.
       match idKey with
       | none   => return none
       | some k =>
-        -- Qualify only when the identity key is a present, non-empty column
-        -- that differs from the column actually referenced.
         if k ≠ [] ∧ k ≠ refColumn then
           return (some refColumn)
         else
           return none
+    else
+      return none
     -- impl-end
 
 prove_correct qualifyReference by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,18 +68,15 @@
   ensures out = targetQualifier isUniqueRef refColumn idKey
   do
     -- impl-start
-    -- A one-to-one / identity link never carries an explicit qualifier.
+    -- ATTACK: emits idKey column (some k) rather than refColumn.
     if isUniqueRef then
       return none
     else
-      -- A plain many-to-one link: consult the target collection's identity key.
       match idKey with
       | none   => return none
       | some k =>
-        -- Qualify only when the identity key is a present, non-empty column
-        -- that differs from the column actually referenced.
         if k ≠ [] ∧ k ≠ refColumn then
-          return (some refColumn)
+          return (some k)
         else
           return none
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,20 +68,15 @@
   ensures out = targetQualifier isUniqueRef refColumn idKey
   do
     -- impl-start
-    -- A one-to-one / identity link never carries an explicit qualifier.
-    if isUniqueRef then
-      return none
-    else
-      -- A plain many-to-one link: consult the target collection's identity key.
-      match idKey with
-      | none   => return none
-      | some k =>
-        -- Qualify only when the identity key is a present, non-empty column
-        -- that differs from the column actually referenced.
-        if k ≠ [] ∧ k ≠ refColumn then
-          return (some refColumn)
-        else
-          return none
+    -- ATTACK: ignores isUniqueRef; always computes the plain-link decision.
+    let _ := isUniqueRef
+    match idKey with
+    | none   => return none
+    | some k =>
+      if k ≠ [] ∧ k ≠ refColumn then
+        return (some refColumn)
+      else
+        return none
     -- impl-end
 
 prove_correct qualifyReference by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,17 +68,14 @@
   ensures out = targetQualifier isUniqueRef refColumn idKey
   do
     -- impl-start
-    -- A one-to-one / identity link never carries an explicit qualifier.
+    -- ATTACK: any present non-empty key qualifies (drops k != refColumn).
     if isUniqueRef then
       return none
     else
-      -- A plain many-to-one link: consult the target collection's identity key.
       match idKey with
       | none   => return none
       | some k =>
-        -- Qualify only when the identity key is a present, non-empty column
-        -- that differs from the column actually referenced.
-        if k ≠ [] ∧ k ≠ refColumn then
+        if k ≠ [] then
           return (some refColumn)
         else
           return none
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axiom. The only outside callee the modeled decision consults —
--  the lookup that yields the target collection's identity-key column — is an
--  UNCHANGED callee whose result is taken as the free input `idKey` (an
--  A-reference, not a consumed contract). Its only relied-on property — that it
--  reports the target collection's identity-key column when one exists and
--  nothing otherwise — is validated against the real introspection machinery by
--  axiom_check.py (G-AX).)
-- axioms-end

-- pure-start
/- The explicit target-column qualifier a stored cross-row reference must carry.

   A reference points at a column of another collection. When the reference is a
   plain (many-to-one) link AND the target collection's identity-key column is
   present and is a DIFFERENT column from the one actually referenced, the
   generated description must carry an explicit qualifier that names the
   referenced column; in every other case no qualifier is added. A
   one-to-one / identity reference never carries the qualifier.

   `isUniqueRef` is true when the link is one-to-one (identity) rather than a
   plain many-to-one link; `refColumn` is the referenced column; `idKey` is the
   target collection's identity-key column (`none` when the collection has no
   identity key). A present identity key is recognised only when it is a
   non-empty column name (an absent / empty key is treated as "no key"). -/
def targetQualifier (isUniqueRef : Bool) (refColumn : List Char)
    (idKey : Option (List Char)) : Option (List Char) :=
  if isUniqueRef then none
  else
    match idKey with
    | none   => none
    | some k => if k ≠ [] ∧ k ≠ refColumn then some refColumn else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Deriving the explicit target-column qualifier for one stored cross-row
   reference. The inputs are read-only (none is `mut`; the derivation mutates
   nothing — directive 5):

   - `isUniqueRef` — the link is one-to-one (identity) rather than a plain
     many-to-one link;
   - `refColumn`   — the column the reference points at in the target
     collection;
   - `idKey`       — the target collection's identity-key column, or `none`
     when the collection exposes no identity key.

   The result is the explicit qualifier to attach to the generated description:
   `some refColumn` exactly when a plain link points at a non-identity-key
   column (the identity key is present, non-empty and different from the
   referenced column), and `none` otherwise. Pinned to `targetQualifier` so the
   derivation is forced to be that structural decision over the inputs, not an
   echo of any one carrier. -/
method qualifyReference (isUniqueRef : Bool) (refColumn : List Char)
    (idKey : Option (List Char)) return (out : Option (List Char))
  ensures out = targetQualifier isUniqueRef refColumn idKey
  do
    -- impl-start
    -- POSITIVE CONTROL: equivalent, restructured (conj reordered, combined match).
    match isUniqueRef, idKey with
    | true, _      => return none
    | false, none  => return none
    | false, some k =>
      if k ≠ refColumn ∧ k ≠ [] then
        return (some refColumn)
      else
        return none
    -- impl-end

prove_correct qualifyReference by
  loom_solve <;> simp_all [targetQualifier]
  all_goals tauto
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec shape: postcondition `out = targetQualifier isUniqueRef refColumn idKey` with NO preconditions — a total, exact-equality obligation over the entire input domain (Bool x List Char x Option (List Char)). Any impl that verifies is therefore provably behaviourally identical to targetQualifier on ALL inputs, so a verifying-wrong-impl cannot exist and verify⇏correct cannot be exhibited via a weak-spec attack.

ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec / velvet; each verified with `bash scripts/lean_verify.sh <file>`):
- atk_1 (prepatch bug re-encoded, ungrounded/always-none): never consults idKey, always returns none. exit=1 (unsolved `ensures_1: out = targetQualifier...`, tauto failed). Counterexample branch: isUniqueRef=false, idKey=some k (k nonempty, k≠refColumn) → spec wants some refColumn, impl gives none.
- atk_2 (boundary): drops the non-empty `k ≠ []` guard. exit=1. Differs on (false, refColumn, some []): spec none, impl some refColumn.
- atk_3 (boundary/control-flow): inverts distinctness test to `k = refColumn`. exit=1.
- atk_4 (control-flow-effect): attaches qualifier on the isUniqueRef (identity) branch instead of the plain branch. exit=1.
- atk_5 (ungrounded-oracle echo): emits `some k` (the idKey column) instead of `some refColumn`. exit=1.
- atk_6 (control-flow-effect): ignores isUniqueRef, always computes the plain-link decision. exit=1.
- atk_7 (partial-domain/boundary): any present non-empty key qualifies (drops `k ≠ refColumn`). exit=1.
All 7 fail with genuine `prove_correct`/ensures obligation failures (not syntax errors): `error: unsolved goals — case ensures_1: out = targetQualifier isUniqueRef refColumn idKey`.

POSITIVE CONTROL: pos.lean — behaviourally equivalent, restructured (combined match, reordered conjunction). exit=0 (verifies). Confirms the spec is satisfiable by a faithful impl, so the 7 failures are due to wrongness, not an unsatisfiable spec.

No verifying wrong impl exists ⇒ `patches` is empty (nothing to materialize/resolve for the weak-spec leg). To confirm harness health + the verify⇒resolve direction, the gold-faithful patch (which equals the behaviour any verifying impl must have, since verify pins out=targetQualifier=gold to_field decision) was run through the official run_resolve: RESOLVED=True, F2P test_foreign_key_to_field success, all PASS_TO_PASS success, attempts=1, not flaky. Patch at gold_faithful.patch.

REFINEMENT.MD AUDIT: legs A1(R), A2(R), A3(A-reference), A4(I), A5(R+I), A6(I), A7(R). No kind-3 (inexpressible changed-op) legs — the one genuinely-changed op (attach explicit target-column qualifier) is modeled deeply as the spelled-out `targetQualifier` structural function, not hidden behind an axiom about the function under change. Sole A leg (A3): idKey ↔ connection.introspection.get_primary_key_column, an UNCHANGED callee newly consulted by the fix, taken as a free input (A-reference), validated by G-AX/axiom_check.py against a live sqlite backend (boundary + 2000 fuzz schemas) — correspondence holds; the model's empty-name guard (k ≠ []) is conservative vs. the real callee, which never returns "". No consumed axiom. bundle gates already record G-AX pass, G-CONF pass (100008 inputs, 0 disagreements), G-DIFF pass (prepatch fails).

Verdict SOUND: ≥5 (here 7) distinct same-spec attacks run, none verifies (so none breaks the spec); positive control verifies; gold-faithful patch resolves under the official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axiom. The only outside callee the modeled decision consults —
--  the lookup that yields the target collection's identity-key column — is an
--  UNCHANGED callee whose result is taken as the free input `idKey` (an
--  A-reference, not a consumed contract). Its only relied-on property — that it
--  reports the target collection's identity-key column when one exists and
--  nothing otherwise — is validated against the real introspection machinery by
--  axiom_check.py (G-AX).)
-- axioms-end

-- pure-start
/- The explicit target-column qualifier a stored cross-row reference must carry.

   A reference points at a column of another collection. When the reference is a
   plain (many-to-one) link AND the target collection's identity-key column is
   present and is a DIFFERENT column from the one actually referenced, the
   generated description must carry an explicit qualifier that names the
   referenced column; in every other case no qualifier is added. A
   one-to-one / identity reference never carries the qualifier.

   `isUniqueRef` is true when the link is one-to-one (identity) rather than a
   plain many-to-one link; `refColumn` is the referenced column; `idKey` is the
   target collection's identity-key column (`none` when the collection has no
   identity key). A present identity key is recognised only when it is a
   non-empty column name (an absent / empty key is treated as "no key"). -/
def targetQualifier (isUniqueRef : Bool) (refColumn : List Char)
    (idKey : Option (List Char)) : Option (List Char) :=
  if isUniqueRef then none
  else
    match idKey with
    | none   => none
    | some k => if k ≠ [] ∧ k ≠ refColumn then some refColumn else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Deriving the explicit target-column qualifier for one stored cross-row
   reference. The inputs are read-only (none is `mut`; the derivation mutates
   nothing — directive 5):

   - `isUniqueRef` — the link is one-to-one (identity) rather than a plain
     many-to-one link;
   - `refColumn`   — the column the reference points at in the target
     collection;
   - `idKey`       — the target collection's identity-key column, or `none`
     when the collection exposes no identity key.

   The result is the explicit qualifier to attach to the generated description:
   `some refColumn` exactly when a plain link points at a non-identity-key
   column (the identity key is present, non-empty and different from the
   referenced column), and `none` otherwise. Pinned to `targetQualifier` so the
   derivation is forced to be that structural decision over the inputs, not an
   echo of any one carrier. -/
method qualifyReference (isUniqueRef : Bool) (refColumn : List Char)
    (idKey : Option (List Char)) return (out : Option (List Char))
  ensures out = targetQualifier isUniqueRef refColumn idKey
  do
    -- impl-start
    -- POSITIVE CONTROL: equivalent, restructured (conj reordered, combined match).
    match isUniqueRef, idKey with
    | true, _      => return none
    | false, none  => return none
    | false, some k =>
      if k ≠ refColumn ∧ k ≠ [] then
        return (some refColumn)
      else
        return none
    -- impl-end

prove_correct qualifyReference by
  loom_solve <;> simp_all [targetQualifier]
  all_goals tauto
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec shape: postcondition `out = targetQualifier isUniqueRef refColumn idKey` with NO preconditions — a total, exact-equality obligation over the entire input domain (Bool x List Char x Option (List Char)). Any impl that verifies is therefore provably behaviourally identical to targetQualifier on ALL inputs, so a verifying-wrong-impl cannot exist and verify⇏correct cannot be exhibited via a weak-spec attack.

ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec / velvet; each verified with `bash scripts/lean_verify.sh <file>`):
- atk_1 (prepatch bug re-encoded, ungrounded/always-none): never consults idKey, always returns none. exit=1 (unsolved `ensures_1: out = targetQualifier...`, tauto failed). Counterexample branch: isUniqueRef=false, idKey=some k (k nonempty, k≠refColumn) → spec wants some refColumn, impl gives none.
- atk_2 (boundary): drops the non-empty `k ≠ []` guard. exit=1. Differs on (false, refColumn, some []): spec none, impl some refColumn.
- atk_3 (boundary/control-flow): inverts distinctness test to `k = refColumn`. exit=1.
- atk_4 (control-flow-effect): attaches qualifier on the isUniqueRef (identity) branch instead of the plain branch. exit=1.
- atk_5 (ungrounded-oracle echo): emits `some k` (the idKey column) instead of `some refColumn`. exit=1.
- atk_6 (control-flow-effect): ignores isUniqueRef, always computes the plain-link decision. exit=1.
- atk_7 (partial-domain/boundary): any present non-empty key qualifies (drops `k ≠ refColumn`). exit=1.
All 7 fail with genuine `prove_correct`/ensures obligation failures (not syntax errors): `error: unsolved goals — case ensures_1: out = targetQualifier isUniqueRef refColumn idKey`.

POSITIVE CONTROL: pos.lean — behaviourally equivalent, restructured (combined match, reordered conjunction). exit=0 (verifies). Confirms the spec is satisfiable by a faithful impl, so the 7 failures are due to wrongness, not an unsatisfiable spec.

No verifying wrong impl exists ⇒ `patches` is empty (nothing to materialize/resolve for the weak-spec leg). To confirm harness health + the verify⇒resolve direction, the gold-faithful patch (which equals the behaviour any verifying impl must have, since verify pins out=targetQualifier=gold to_field decision) was run through the official run_resolve: RESOLVED=True, F2P test_foreign_key_to_field success, all PASS_TO_PASS success, attempts=1, not flaky. Patch at gold_faithful.patch.

REFINEMENT.MD AUDIT: legs A1(R), A2(R), A3(A-reference), A4(I), A5(R+I), A6(I), A7(R). No kind-3 (inexpressible changed-op) legs — the one genuinely-changed op (attach explicit target-column qualifier) is modeled deeply as the spelled-out `targetQualifier` structural function, not hidden behind an axiom about the function under change. Sole A leg (A3): idKey ↔ connection.introspection.get_primary_key_column, an UNCHANGED callee newly consulted by the fix, taken as a free input (A-reference), validated by G-AX/axiom_check.py against a live sqlite backend (boundary + 2000 fuzz schemas) — correspondence holds; the model's empty-name guard (k ≠ []) is conservative vs. the real callee, which never returns "". No consumed axiom. bundle gates already record G-AX pass, G-CONF pass (100008 inputs, 0 disagreements), G-DIFF pass (prepatch fails).

Verdict SOUND: ≥5 (here 7) distinct same-spec attacks run, none verifies (so none breaks the spec); positive control verifies; gold-faithful patch resolves under the official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. Modeled function targetQualifier/qualifyReference exactly matches the gold patch decision in inspectdb.py (to_field=ref_db_column iff ForeignKey AND ref_pk_column AND ref_pk_column != ref_db_column). Verification: (1) gold patch from swe_bench test.jsonl confirms the branch logic; (2) same_spec(cur, prepatch, lean_tables)=True — frozen spec byte-identical across the patch, prepatch skeleton (return none) correctly fails prove_correct; only diff vs reference bundle is partial->total correctness, a STRENGTHENING; (3) lean_verify.sh exit 0 (proof closes, no sorry/native_decide); (4) exhaustive fuzz of model vs real-gold transliteration over full cross product of (is_unique,is_primary_key,refColumn,idKey) with idKey drawn from the REACHABLE domain of get_primary_key_column (None or non-empty name) => 0 divergences, incl. primary_key collapse into OneToOne branch and unicode/'0'/'id' names; (5) the model's `k != []` guard on idKey conservatively models the unreachable empty-string case — real callee's `if ref_pk_column` is also falsy for '', so it agrees there too. isUniqueRef=(unique or primary_key), refColumn, and idKey A-reference bindings all align with mapping.md. Spec is not too strong and does not drift from repo behavior on any reachable input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, zero hard_failures) and same_spec confirms the Solution.lean vs Solution_prepatch.lean spec regions are byte-identical. Manual review of the full spec view (imports/axioms/pure targetQualifier/method qualifyReference signature+ensures, impl and proof elided): the spec is deliberately abstracted to backend-neutral vocabulary ('cross-row reference', 'identity-key column', 'collection', 'qualifier') and does NOT name any patched repo symbol (to_field, get_primary_key_column, ForeignKey, OneToOneField, ref_db_column, ref_pk_column, inspectdb). No diff markers, no patched file path/module path, no gold-patch line reproduced, no bug/fix narration. The public problem_statement already describes the target behavior more concretely than the spec (it explicitly discusses foreign keys to a specific non-PK field, with an SQL reproduction referencing foo(other_id)), so the spec view discloses nothing about the gold edit beyond what the solver already sees. The single consulted callee is abstracted to the free input idKey (A-reference), not the concrete introspection callee. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
