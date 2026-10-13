# P2 adversarial audit — astropy__astropy-13236

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callees. The classification is a pure dispatch over the shape
@@ -101,7 +101,7 @@
       match input with
       | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind
       | .alreadyMixin     => .mixinKind
-      | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind
+      | .structuredPlain  => .mixinKind
       | .structuredMasked => .maskedColumnKind
       | .plainMasked      => .maskedColumnKind
       | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind
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
 -- (No axiomatized callees. The classification is a pure dispatch over the shape
@@ -99,7 +99,7 @@
     -- is wrapped masked in a masked table and ordinary otherwise.
     let result : ColumnKind :=
       match input with
-      | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind
+      | .alreadyColumn    => .columnKind
       | .alreadyMixin     => .mixinKind
       | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind
       | .structuredMasked => .maskedColumnKind
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
 -- (No axiomatized callees. The classification is a pure dispatch over the shape
@@ -103,7 +103,7 @@
       | .alreadyMixin     => .mixinKind
       | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind
       | .structuredMasked => .maskedColumnKind
-      | .plainMasked      => .maskedColumnKind
+      | .plainMasked      => .columnKind
       | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind
     return result
     -- impl-end
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
 -- (No axiomatized callees. The classification is a pure dispatch over the shape
@@ -102,7 +102,7 @@
       | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind
       | .alreadyMixin     => .mixinKind
       | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind
-      | .structuredMasked => .maskedColumnKind
+      | .structuredMasked => .mixinKind
       | .plainMasked      => .maskedColumnKind
       | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind
     return result
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
 -- (No axiomatized callees. The classification is a pure dispatch over the shape
@@ -104,7 +104,7 @@
       | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind
       | .structuredMasked => .maskedColumnKind
       | .plainMasked      => .maskedColumnKind
-      | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind
+      | .plainOther       => .columnKind
     return result
     -- impl-end
 
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
 -- (No axiomatized callees. The classification is a pure dispatch over the shape
@@ -99,12 +99,12 @@
     -- is wrapped masked in a masked table and ordinary otherwise.
     let result : ColumnKind :=
       match input with
-      | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind
+      | .alreadyColumn    => if tableIsMasked then .columnKind else .maskedColumnKind
       | .alreadyMixin     => .mixinKind
-      | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind
+      | .structuredPlain  => if tableIsMasked then .columnKind else .maskedColumnKind
       | .structuredMasked => .maskedColumnKind
       | .plainMasked      => .maskedColumnKind
-      | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind
+      | .plainOther       => if tableIsMasked then .columnKind else .maskedColumnKind
     return result
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The classification is a pure dispatch over the shape
@@ -101,7 +101,7 @@
       match input with
       | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind
       | .alreadyMixin     => .mixinKind
-      | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind
+      | .structuredPlain  => .maskedColumnKind
       | .structuredMasked => .maskedColumnKind
       | .plainMasked      => .maskedColumnKind
       | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The classification is a pure dispatch over the shape
--  of the value being added plus the host table's masked-ness and is modeled
--  DEEPLY in the `pure` region below; the surrounding helpers that detect that
--  shape and build the wrapper are collapsed into the inputs/result and owed no
--  contract. There is no `axiom` declaration and no A-reference deep model of
--  an outside callee.)
-- axioms-end

-- pure-start
/- The shapes a value can have when it is offered to a table as a new column,
   reduced to the only distinctions the classification reacts to:
     * `alreadyColumn`    — the value is already an ordinary column object;
     * `alreadyMixin`     — the value is already a valid mixin column for this
                            table (a rich column type such as a coordinate or
                            time column);
     * `structuredPlain`  — an unmasked array whose element record carries more
                            than one field (a multi-field "structured" array);
     * `structuredMasked` — a masked array whose element record carries more
                            than one field;
     * `plainMasked`      — a masked array whose element record carries a single
                            field;
     * `plainOther`       — any remaining plain array value.
   The structured/plain and masked/unmasked distinctions are kept apart because
   the classification treats them differently. -/
inductive InputShape where
  | alreadyColumn
  | alreadyMixin
  | structuredPlain
  | structuredMasked
  | plainMasked
  | plainOther
  deriving Inhabited, DecidableEq

/- The column-class kind a value is wrapped in:
     * `columnKind`       — the ordinary column class;
     * `maskedColumnKind` — the masked column class (used when the value carries
                            a mask, so the mask is preserved — or when the host
                            table itself wraps its data as masked);
     * `mixinKind`        — kept as a mixin column. -/
inductive ColumnKind where
  | columnKind
  | maskedColumnKind
  | mixinKind
  deriving Inhabited, DecidableEq

/- The classification, modeled deeply. Besides the value's shape it depends on
   the host table's masked-ness (`tableIsMasked`): a masked table wraps every
   array-like value as a masked column. The desired behaviour:
     * a value that is already a mixin column is kept as a mixin column — this
       is the ONLY way a value ends up a mixin column;
     * a value that carries a mask (a masked array, whether structured or not)
       becomes a masked column so its mask is preserved, whatever the table's
       masked-ness;
     * every other value — one already an ordinary column, a multi-field
       structured array, or any other plain array — is classified purely by the
       table's masked-ness: a masked column in a masked table, an ordinary
       column otherwise. In particular a multi-field structured array is
       classified by the same rule as any other array of its masked-ness — it
       is NOT singled out for the mixin class. -/
def classify : InputShape → Bool → ColumnKind
  | .alreadyColumn,    tableIsMasked => if tableIsMasked then .maskedColumnKind else .columnKind
  | .alreadyMixin,     _             => .mixinKind
  | .structuredPlain,  tableIsMasked => if tableIsMasked then .maskedColumnKind else .columnKind
  | .structuredMasked, _             => .maskedColumnKind
  | .plainMasked,      _             => .maskedColumnKind
  | .plainOther,       tableIsMasked => if tableIsMasked then .maskedColumnKind else .columnKind
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Classify a value offered to a table as a new column into the column-class
   kind that wraps it. `input` and `tableIsMasked` are read-only (not `mut`);
   the query computes a single kind and mutates nothing (directive 5). -/
method classifyColumn (input : InputShape) (tableIsMasked : Bool) return (out : ColumnKind)
  ensures out = classify input tableIsMasked
  ensures (input = .structuredPlain ∧ tableIsMasked = false) → out = .columnKind
  ensures input = .structuredMasked → out = .maskedColumnKind
  ensures input = .alreadyMixin → out = .mixinKind
  ensures (out = .mixinKind) → (input = .alreadyMixin)
  do
    -- impl-start
    -- Dispatch on the shape of the value and the table's masked-ness. A value
    -- already a mixin column is the only one kept as a mixin column; a masked
    -- array (structured or not) becomes a masked column; everything else — an
    -- existing ordinary column, a structured array, or any other plain array —
    -- is wrapped masked in a masked table and ordinary otherwise.
    let result : ColumnKind :=
      match input with
      | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind
      | .alreadyMixin     => .mixinKind
      | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind
      | .structuredMasked => .maskedColumnKind
      | .plainMasked      => .maskedColumnKind
      | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind
    return result
    -- impl-end

prove_correct classifyColumn by
  loom_solve
  cases input <;> cases tableIsMasked <;> simp_all [classify]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec's FIRST postcondition `ensures out = classify input tableIsMasked` is a TOTAL functional specification: `classify` pins the output for every one of the 6 InputShape x 2 tableIsMasked = 12 inputs. Any verifying impl is therefore extensionally equal to `classify`, leaving no room for a verifying-but-wrong impl. The 4 extra ensures clauses are redundant reinforcements of the same function. Consequently NO wrong impl verifies, so there is no verify=>correct gap and no faithful patch is owed a resolve run (the resolve step in the protocol fires only for wrong impls that VERIFY; here that set is empty, so `patches` is empty by construction, not by omission).

### Protocol executed
- same_spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec (velvet language); only the impl match-arm(s) edited, axioms/pure/pre/post byte-identical.
- Verified each with `bash scripts/lean_verify.sh <file>`, run concurrently (<=4 background jobs per batch).

ATTACKS (each same_spec=True, each FAILS to verify with a genuine `error: unsolved goals ⊢ False` at exactly the mutated arm — not a linter/timeout artifact):
- atk_1 partial-domain (structuredPlain->mixinKind, prepatch half): EXIT=1, unsolved goals at .structuredPlain.{false,true}
- atk_2 control-flow-effect (alreadyColumn ignores tableIsMasked -> always columnKind): EXIT=1, unsolved at .alreadyColumn.true
- atk_3 boundary/mask-not-preserved (plainMasked->columnKind): EXIT=1, unsolved at .plainMasked.{false,true}
- atk_4 structuredMasked->mixinKind (prepatch's other half): EXIT=1, unsolved at .structuredMasked.{false,true}
- atk_5 plainOther ignores masked table (-> always columnKind): EXIT=1, unsolved at .plainOther.true
- atk_6 ungrounded-oracle echo with negated table flag on masked-sensitive arms: EXIT=1, unsolved at .structuredPlain.false
- atk_7 over-masking (structuredPlain->maskedColumnKind unconditionally, wrong for unmasked table): EXIT=1, unsolved at .structuredPlain.false

POSITIVE CONTROL: pos_control.lean (byte-identical to bundle Solution.lean) verifies clean, EXIT=0.
PREPATCH: prepatch.lean (Solution_prepatch.lean, both structured shapes -> mixinKind) FAILS as designed, EXIT=1 (G-DIFF reproduced).

REFINEMENT/A-LEG AUDIT: meta.json declares axioms=[] and deep_model_references=[]; grep finds no `axiom`/`sorry`/`admit` in Solution.lean. refinement.md legs are all R/I (1 R + 6 I), zero A-legs, zero kind-3 steps. The `classify` deep model is a self-contained pure Lean function, NOT an axiomatized/A-reference outside callee, so there is no A-leg correspondence available to break. G-CONF passes: R/I shadow agrees with the patched selection logic on 100012 inputs (12 exhaustive + fuzz, seed=13236), 0 disagreements. mapping.md correctly takes tableIsMasked as a second input (fixing the prior G-PANEL-2 one-input unfaithfulness where a masked table wraps arrays/Columns as MaskedColumn).

CONCLUSION: >=7 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, over-masking) attempted; none verifies. No verifying wrong impl => no non-resolving faithful patch => verify=>correct holds for the tested falsification surface. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The classification is a pure dispatch over the shape
--  of the value being added plus the host table's masked-ness and is modeled
--  DEEPLY in the `pure` region below; the surrounding helpers that detect that
--  shape and build the wrapper are collapsed into the inputs/result and owed no
--  contract. There is no `axiom` declaration and no A-reference deep model of
--  an outside callee.)
-- axioms-end

-- pure-start
/- The shapes a value can have when it is offered to a table as a new column,
   reduced to the only distinctions the classification reacts to:
     * `alreadyColumn`    — the value is already an ordinary column object;
     * `alreadyMixin`     — the value is already a valid mixin column for this
                            table (a rich column type such as a coordinate or
                            time column);
     * `structuredPlain`  — an unmasked array whose element record carries more
                            than one field (a multi-field "structured" array);
     * `structuredMasked` — a masked array whose element record carries more
                            than one field;
     * `plainMasked`      — a masked array whose element record carries a single
                            field;
     * `plainOther`       — any remaining plain array value.
   The structured/plain and masked/unmasked distinctions are kept apart because
   the classification treats them differently. -/
inductive InputShape where
  | alreadyColumn
  | alreadyMixin
  | structuredPlain
  | structuredMasked
  | plainMasked
  | plainOther
  deriving Inhabited, DecidableEq

/- The column-class kind a value is wrapped in:
     * `columnKind`       — the ordinary column class;
     * `maskedColumnKind` — the masked column class (used when the value carries
                            a mask, so the mask is preserved — or when the host
                            table itself wraps its data as masked);
     * `mixinKind`        — kept as a mixin column. -/
inductive ColumnKind where
  | columnKind
  | maskedColumnKind
  | mixinKind
  deriving Inhabited, DecidableEq

/- The classification, modeled deeply. Besides the value's shape it depends on
   the host table's masked-ness (`tableIsMasked`): a masked table wraps every
   array-like value as a masked column. The desired behaviour:
     * a value that is already a mixin column is kept as a mixin column — this
       is the ONLY way a value ends up a mixin column;
     * a value that carries a mask (a masked array, whether structured or not)
       becomes a masked column so its mask is preserved, whatever the table's
       masked-ness;
     * every other value — one already an ordinary column, a multi-field
       structured array, or any other plain array — is classified purely by the
       table's masked-ness: a masked column in a masked table, an ordinary
       column otherwise. In particular a multi-field structured array is
       classified by the same rule as any other array of its masked-ness — it
       is NOT singled out for the mixin class. -/
def classify : InputShape → Bool → ColumnKind
  | .alreadyColumn,    tableIsMasked => if tableIsMasked then .maskedColumnKind else .columnKind
  | .alreadyMixin,     _             => .mixinKind
  | .structuredPlain,  tableIsMasked => if tableIsMasked then .maskedColumnKind else .columnKind
  | .structuredMasked, _             => .maskedColumnKind
  | .plainMasked,      _             => .maskedColumnKind
  | .plainOther,       tableIsMasked => if tableIsMasked then .maskedColumnKind else .columnKind
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Classify a value offered to a table as a new column into the column-class
   kind that wraps it. `input` and `tableIsMasked` are read-only (not `mut`);
   the query computes a single kind and mutates nothing (directive 5). -/
method classifyColumn (input : InputShape) (tableIsMasked : Bool) return (out : ColumnKind)
  ensures out = classify input tableIsMasked
  ensures (input = .structuredPlain ∧ tableIsMasked = false) → out = .columnKind
  ensures input = .structuredMasked → out = .maskedColumnKind
  ensures input = .alreadyMixin → out = .mixinKind
  ensures (out = .mixinKind) → (input = .alreadyMixin)
  do
    -- impl-start
    -- Dispatch on the shape of the value and the table's masked-ness. A value
    -- already a mixin column is the only one kept as a mixin column; a masked
    -- array (structured or not) becomes a masked column; everything else — an
    -- existing ordinary column, a structured array, or any other plain array —
    -- is wrapped masked in a masked table and ordinary otherwise.
    let result : ColumnKind :=
      match input with
      | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind
      | .alreadyMixin     => .mixinKind
      | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind
      | .structuredMasked => .maskedColumnKind
      | .plainMasked      => .maskedColumnKind
      | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind
    return result
    -- impl-end

prove_correct classifyColumn by
  loom_solve
  cases input <;> cases tableIsMasked <;> simp_all [classify]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec's FIRST postcondition `ensures out = classify input tableIsMasked` is a TOTAL functional specification: `classify` pins the output for every one of the 6 InputShape x 2 tableIsMasked = 12 inputs. Any verifying impl is therefore extensionally equal to `classify`, leaving no room for a verifying-but-wrong impl. The 4 extra ensures clauses are redundant reinforcements of the same function. Consequently NO wrong impl verifies, so there is no verify=>correct gap and no faithful patch is owed a resolve run (the resolve step in the protocol fires only for wrong impls that VERIFY; here that set is empty, so `patches` is empty by construction, not by omission).

### Protocol executed
- same_spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec (velvet language); only the impl match-arm(s) edited, axioms/pure/pre/post byte-identical.
- Verified each with `bash scripts/lean_verify.sh <file>`, run concurrently (<=4 background jobs per batch).

ATTACKS (each same_spec=True, each FAILS to verify with a genuine `error: unsolved goals ⊢ False` at exactly the mutated arm — not a linter/timeout artifact):
- atk_1 partial-domain (structuredPlain->mixinKind, prepatch half): EXIT=1, unsolved goals at .structuredPlain.{false,true}
- atk_2 control-flow-effect (alreadyColumn ignores tableIsMasked -> always columnKind): EXIT=1, unsolved at .alreadyColumn.true
- atk_3 boundary/mask-not-preserved (plainMasked->columnKind): EXIT=1, unsolved at .plainMasked.{false,true}
- atk_4 structuredMasked->mixinKind (prepatch's other half): EXIT=1, unsolved at .structuredMasked.{false,true}
- atk_5 plainOther ignores masked table (-> always columnKind): EXIT=1, unsolved at .plainOther.true
- atk_6 ungrounded-oracle echo with negated table flag on masked-sensitive arms: EXIT=1, unsolved at .structuredPlain.false
- atk_7 over-masking (structuredPlain->maskedColumnKind unconditionally, wrong for unmasked table): EXIT=1, unsolved at .structuredPlain.false

POSITIVE CONTROL: pos_control.lean (byte-identical to bundle Solution.lean) verifies clean, EXIT=0.
PREPATCH: prepatch.lean (Solution_prepatch.lean, both structured shapes -> mixinKind) FAILS as designed, EXIT=1 (G-DIFF reproduced).

REFINEMENT/A-LEG AUDIT: meta.json declares axioms=[] and deep_model_references=[]; grep finds no `axiom`/`sorry`/`admit` in Solution.lean. refinement.md legs are all R/I (1 R + 6 I), zero A-legs, zero kind-3 steps. The `classify` deep model is a self-contained pure Lean function, NOT an axiomatized/A-reference outside callee, so there is no A-leg correspondence available to break. G-CONF passes: R/I shadow agrees with the patched selection logic on 100012 inputs (12 exhaustive + fuzz, seed=13236), 0 disagreements. mapping.md correctly takes tableIsMasked as a second input (fixing the prior G-PANEL-2 one-input unfaithfulness where a masked table wraps arrays/Columns as MaskedColumn).

CONCLUSION: >=7 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, over-masking) attempted; none verifies. No verifying wrong impl => no non-resolving faithful patch => verify=>correct holds for the tested falsification surface. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (swebench_unified.markers.same_spec(Solution, Solution_prepatch, VelvetBackend) = True). Solution.lean verifies (lean_verify.sh exit 0); Solution_prepatch.lean fails prove_correct, confirming the four discriminating clauses are load-bearing.

Faithfulness checked empirically against the REAL repo: applied the gold patch (deletion of the structured-ndarray auto-mixin branch at table.py:1244-1250) to a fresh copy of the base_commit worktree and drove Table._convert_data_to_col via `t['a']=val` over all 6 InputShape cases x 2 tableIsMasked = 12 cells. Every cell matches the model's `classify` and every extra ensures clause holds:

  tableIsMasked=False: alreadyColumn->column, alreadyMixin->mixin, structuredPlain->column, structuredMasked->maskedColumn, plainMasked->maskedColumn, plainOther->column
  tableIsMasked=True:  alreadyColumn->maskedColumn, alreadyMixin->mixin, structuredPlain->maskedColumn, structuredMasked->maskedColumn, plainMasked->maskedColumn, plainOther->maskedColumn

These reproduce classify(shape, masked) exactly. The extra postconditions are all satisfied by the real repo: (structuredPlain & !masked)->columnKind (empirically column), structuredMasked->maskedColumnKind (both tables), alreadyMixin->mixinKind, and out=mixinKind -> input=alreadyMixin (mixin arises ONLY for alreadyMixin post-patch). So the spec is not too strong: every clause it asserts is a true property of the patched callee, and it does not rule out any behavior the real repo exhibits in the modeled domain.

The model correctly takes tableIsMasked as a second input (the prior G-PANEL-2 collapse noted in mapping.md is fixed): a masked table wraps alreadyColumn/structuredPlain/plainOther as MaskedColumn, exactly matching _get_col_cls_for_table/self.ColumnClass, while masked arrays route through masked_col_cls regardless. The domain restriction (excluding None, mixin-handler products, sequences-of-mixins, non-dtype scalars) is declared out-of-scope and those cases are never reached by the F2P tests; within the modeled domain there is no diverging input. No defect found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True; spec view correctly elides impl and proof body (spec regions axioms/pure/pre/post are frozen and identical across pre/post-patch). Leakage assessed against the PUBLIC problem_statement only (not hints_text). The problem_statement is extremely explicit: it quotes the exact branch to delete verbatim (data.view(NdarrayMixin) clause guarded by isinstance(data, np.ndarray) and len(data.dtype) > 1) and states the intended outcome ('the structured array will be added as a Column', 'removing this clause'). The spec view (InputShape/ColumnKind/classify + postconditions: structuredPlain&!masked -> columnKind, out=mixinKind -> input=alreadyMixin) is an abstract behavioral restatement fully subsumed by that public disclosure. The only detail not literally in the problem_statement — structuredMasked -> maskedColumnKind (mask preserved) — is a direct behavioral consequence of the publicly-described deletion (structured masked arrays fall through to the existing masked arm), i.e. a correctness spec of the same edit, not implementation guidance beyond the problem statement. No spec-view line reconstructs the gold edit beyond what problem_statement already reveals.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
