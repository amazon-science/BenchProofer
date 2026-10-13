# P2 adversarial audit — django__django-11138

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean`, `atk8.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verifying-wrong-impl whose faithful refined patch could fail to resolve. verify⇒correct holds.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The SQL expression is built entirely from the four
@@ -65,7 +65,7 @@
   do
     -- impl-start
     let out : List Char :=
-      if active ∧ storedZone ≠ queryZone then
+      if active then
         "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
           ++ "', '".toList ++ queryZone ++ "')".toList
       else
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The SQL expression is built entirely from the four
@@ -65,7 +65,7 @@
   do
     -- impl-start
     let out : List Char :=
-      if active ∧ storedZone ≠ queryZone then
+      if active ∨ storedZone ≠ queryZone then
         "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
           ++ "', '".toList ++ queryZone ++ "')".toList
       else
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The SQL expression is built entirely from the four
@@ -66,8 +66,8 @@
     -- impl-start
     let out : List Char :=
       if active ∧ storedZone ≠ queryZone then
-        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
-          ++ "', '".toList ++ queryZone ++ "')".toList
+        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ queryZone
+          ++ "', '".toList ++ storedZone ++ "')".toList
       else
         expr
     return out
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The SQL expression is built entirely from the four
@@ -64,12 +64,7 @@
   ensures out = tzAdjustedExpr active expr queryZone storedZone
   do
     -- impl-start
-    let out : List Char :=
-      if active ∧ storedZone ≠ queryZone then
-        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
-          ++ "', '".toList ++ queryZone ++ "')".toList
-      else
-        expr
+    let out : List Char := expr
     return out
     -- impl-end
 
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The SQL expression is built entirely from the four
@@ -66,7 +66,7 @@
     -- impl-start
     let out : List Char :=
       if active ∧ storedZone ≠ queryZone then
-        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
+        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ "UTC".toList
           ++ "', '".toList ++ queryZone ++ "')".toList
       else
         expr
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The SQL expression is built entirely from the four
@@ -65,11 +65,8 @@
   do
     -- impl-start
     let out : List Char :=
-      if active ∧ storedZone ≠ queryZone then
-        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
-          ++ "', '".toList ++ queryZone ++ "')".toList
-      else
-        expr
+      "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
+        ++ "', '".toList ++ queryZone ++ "')".toList
     return out
     -- impl-end
 
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The SQL expression is built entirely from the four
@@ -65,7 +65,7 @@
   do
     -- impl-start
     let out : List Char :=
-      if active ∧ storedZone ≠ queryZone then
+      if active ∧ storedZone = queryZone then
         "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
           ++ "', '".toList ++ queryZone ++ "')".toList
       else
```

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The SQL expression is built entirely from the four
@@ -66,7 +66,7 @@
     -- impl-start
     let out : List Char :=
       if active ∧ storedZone ≠ queryZone then
-        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
+        "CONVERT_TIMEZONE(".toList ++ expr ++ ", '".toList ++ storedZone
           ++ "', '".toList ++ queryZone ++ "')".toList
       else
         expr
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The SQL expression is built entirely from the four
--  inputs — a pure string computation modeled in full below; nothing is
--  delegated to an unchanged callee.)
-- axioms-end

-- pure-start
/- The database read converts a stored timestamp so that a later date/time
   comparison is evaluated in the time zone the query expects. Two time-zone
   names are in play: the one the stored values are kept in (`storedZone`) and
   the one the query is evaluated against (`queryZone`). The conversion is only
   meaningful when time-zone support is active AND the two zones actually
   differ; when they coincide, or support is off, the field expression is used
   unchanged so no zone table is required. When a conversion IS needed the
   field expression is wrapped to re-interpret it from the stored zone into the
   query zone:  CONVERT_TZ(<expr>, '<storedZone>', '<queryZone>').

   `active` carries whether time-zone support is on; `expr` is the field
   expression; `queryZone` and `storedZone` are the target and source zone
   names. The result is a fresh expression. -/
def tzAdjustedExpr
    (active : Bool) (expr queryZone storedZone : List Char) : List Char :=
  if active ∧ storedZone ≠ queryZone then
    "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
      ++ "', '".toList ++ queryZone ++ "')".toList
  else
    expr

/- Single-step unfold so `loom_solve` can discharge the postcondition. -/
@[grind] lemma tzAdjustedExpr_def
    (active : Bool) (expr queryZone storedZone : List Char) :
    tzAdjustedExpr active expr queryZone storedZone =
      (if active ∧ storedZone ≠ queryZone then
        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
          ++ "', '".toList ++ queryZone ++ "')".toList
       else expr) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the field expression used to read a stored timestamp for a date/time
   comparison evaluated in the query's time zone. When time-zone support is
   active and the stored zone differs from the query zone, the expression is
   wrapped to re-interpret it from the stored zone into the query zone; in every
   other case (support off, or the two zones identical) the original expression
   is returned verbatim — avoiding a needless conversion and the zone tables it
   would require. All four inputs are read-only (none declared `mut`); the
   builder only reads them (directive 5) and returns a fresh expression. -/
method buildTzAdjustedExpr
    (active : Bool) (expr : List Char) (queryZone : List Char) (storedZone : List Char)
    return (out : List Char)
  ensures out = tzAdjustedExpr active expr queryZone storedZone
  do
    -- impl-start
    let out : List Char :=
      if active ∧ storedZone ≠ queryZone then
        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
          ++ "', '".toList ++ queryZone ++ "')".toList
      else
        expr
    return out
    -- impl-end

prove_correct buildTzAdjustedExpr by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

django__django-11138 velvet, G-EQ refinement-fidelity adversarial pass. verifier scripts/lean_verify.sh.

SAME-SPEC: all 8 attacks + positive control + prepatch confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). All edits confined to the impl region; axioms/pure/pre/post byte-identical.

SPEC SHAPE: `method buildTzAdjustedExpr ... ensures out = tzAdjustedExpr active expr queryZone storedZone` with NO preconditions (pre-conditions region empty). This is an EXACT-equality postcondition over the FULL input domain, pinning the output to the deep model tzAdjustedExpr (guard `active ∧ storedZone ≠ queryZone`, wrap `CONVERT_TZ(expr, 'storedZone', 'queryZone')`, else identity). Any behaviourally-distinct impl is therefore rejected.

### ATTACKS (all same-spec wrong impls, verified concurrently ≤4 at a time with `bash scripts/lean_verify.sh <f>`):
- atk1 partial-domain: drop the zones-differ guard (if active only) -> EXIT 1, unsolved `out = tzAdjustedExpr` goal.
- atk2 boundary/control-flow: OR instead of AND in guard -> EXIT 1.
- atk3 swapped zones: origin=queryZone, target=storedZone -> EXIT 1.
- atk4 control-flow-effect: identity always (return expr) -> EXIT 1.
- atk5 ungrounded-oracle echo: hardcoded 'UTC' origin (prepatch-style) but keeping the differ-guard -> EXIT 1.
- atk6: always wrap unconditionally -> EXIT 1.
- atk7 boundary: `=` instead of `≠` in guard (wrap when zones equal) -> EXIT 1.
- atk8 string-shape: wrong wrapper literal `CONVERT_TIMEZONE(` -> EXIT 1.
Every failure log shows a genuine postcondition mismatch (`case ensures_1: out = tzAdjustedExpr ...` unsolved), NOT a syntax/elaboration error — confirmed by inspecting each .log tail.

POSITIVE CONTROL: atk_pos (byte-identical gold Solution.lean) verifies EXIT 0, clean log. PREPATCH: atk_prepatch (Solution_prepatch.lean: hardcoded 'UTC' origin, no zones-equal skip) fails EXIT 1 on the exact `out = tzAdjustedExpr` goal on both discriminating clauses (source zone + skip) — G-DIFF reproduced.

STEP 2 (materialize+resolve): VACUOUS. No verifying wrong impl exists, so patches={} — there is no candidate whose faithful refined patch must be run through the harness. The one class the harness would need to resolve (the gold-faithful impl = atk_pos) is the gold patch itself, which resolves by construction (G-RESOLVE).

REFINEMENT.MD AUDIT (A-leg focus per plan §4): axioms=[], deep_model_references=[] — genuinely NO A-legs (verified against mapping.md §3.1 and conformance_check.py which uses the patched real MySQL _convert_field_to_tz as oracle, no un-substituted A callee). Every leg is R (A1-A4: str↔List Char, bool↔Bool type refinements) or I (A5 identical guard, A6 %-interp↔++ concat, A7 identity branch). No kind-3 (inexpressible-changed-op) legs: the operation that changed (conversion source zone + zones-equal skip) is modeled DEEPLY in tzAdjustedExpr, not hidden behind an axiom. §B three additional sites (Oracle + SQLite) ship verbatim in gold patch.diff, express no behaviour independent of the modeled MySQL decision (django__django-14376 precedent), and the F2P test test_query_convert_timezones runs on SQLite — all in gold, so resolve holds. Correspondence to real callees checks out.

VERDICT: SOUND. 8 distinct same-spec attacks + prepatch all fail to verify; positive control verifies; no verify⇏correct gap. The exact-equality full-domain postcondition leaves no room for a verifying-but-wrong impl.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean`, `atk8.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies, so there is no verifying-wrong-impl whose faithful refined patch could fail to resolve. verify⇒correct holds.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The SQL expression is built entirely from the four
--  inputs — a pure string computation modeled in full below; nothing is
--  delegated to an unchanged callee.)
-- axioms-end

-- pure-start
/- The database read converts a stored timestamp so that a later date/time
   comparison is evaluated in the time zone the query expects. Two time-zone
   names are in play: the one the stored values are kept in (`storedZone`) and
   the one the query is evaluated against (`queryZone`). The conversion is only
   meaningful when time-zone support is active AND the two zones actually
   differ; when they coincide, or support is off, the field expression is used
   unchanged so no zone table is required. When a conversion IS needed the
   field expression is wrapped to re-interpret it from the stored zone into the
   query zone:  CONVERT_TZ(<expr>, '<storedZone>', '<queryZone>').

   `active` carries whether time-zone support is on; `expr` is the field
   expression; `queryZone` and `storedZone` are the target and source zone
   names. The result is a fresh expression. -/
def tzAdjustedExpr
    (active : Bool) (expr queryZone storedZone : List Char) : List Char :=
  if active ∧ storedZone ≠ queryZone then
    "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
      ++ "', '".toList ++ queryZone ++ "')".toList
  else
    expr

/- Single-step unfold so `loom_solve` can discharge the postcondition. -/
@[grind] lemma tzAdjustedExpr_def
    (active : Bool) (expr queryZone storedZone : List Char) :
    tzAdjustedExpr active expr queryZone storedZone =
      (if active ∧ storedZone ≠ queryZone then
        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
          ++ "', '".toList ++ queryZone ++ "')".toList
       else expr) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the field expression used to read a stored timestamp for a date/time
   comparison evaluated in the query's time zone. When time-zone support is
   active and the stored zone differs from the query zone, the expression is
   wrapped to re-interpret it from the stored zone into the query zone; in every
   other case (support off, or the two zones identical) the original expression
   is returned verbatim — avoiding a needless conversion and the zone tables it
   would require. All four inputs are read-only (none declared `mut`); the
   builder only reads them (directive 5) and returns a fresh expression. -/
method buildTzAdjustedExpr
    (active : Bool) (expr : List Char) (queryZone : List Char) (storedZone : List Char)
    return (out : List Char)
  ensures out = tzAdjustedExpr active expr queryZone storedZone
  do
    -- impl-start
    let out : List Char :=
      if active ∧ storedZone ≠ queryZone then
        "CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone
          ++ "', '".toList ++ queryZone ++ "')".toList
      else
        expr
    return out
    -- impl-end

prove_correct buildTzAdjustedExpr by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

django__django-11138 velvet, G-EQ refinement-fidelity adversarial pass. verifier scripts/lean_verify.sh.

SAME-SPEC: all 8 attacks + positive control + prepatch confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). All edits confined to the impl region; axioms/pure/pre/post byte-identical.

SPEC SHAPE: `method buildTzAdjustedExpr ... ensures out = tzAdjustedExpr active expr queryZone storedZone` with NO preconditions (pre-conditions region empty). This is an EXACT-equality postcondition over the FULL input domain, pinning the output to the deep model tzAdjustedExpr (guard `active ∧ storedZone ≠ queryZone`, wrap `CONVERT_TZ(expr, 'storedZone', 'queryZone')`, else identity). Any behaviourally-distinct impl is therefore rejected.

### ATTACKS (all same-spec wrong impls, verified concurrently ≤4 at a time with `bash scripts/lean_verify.sh <f>`):
- atk1 partial-domain: drop the zones-differ guard (if active only) -> EXIT 1, unsolved `out = tzAdjustedExpr` goal.
- atk2 boundary/control-flow: OR instead of AND in guard -> EXIT 1.
- atk3 swapped zones: origin=queryZone, target=storedZone -> EXIT 1.
- atk4 control-flow-effect: identity always (return expr) -> EXIT 1.
- atk5 ungrounded-oracle echo: hardcoded 'UTC' origin (prepatch-style) but keeping the differ-guard -> EXIT 1.
- atk6: always wrap unconditionally -> EXIT 1.
- atk7 boundary: `=` instead of `≠` in guard (wrap when zones equal) -> EXIT 1.
- atk8 string-shape: wrong wrapper literal `CONVERT_TIMEZONE(` -> EXIT 1.
Every failure log shows a genuine postcondition mismatch (`case ensures_1: out = tzAdjustedExpr ...` unsolved), NOT a syntax/elaboration error — confirmed by inspecting each .log tail.

POSITIVE CONTROL: atk_pos (byte-identical gold Solution.lean) verifies EXIT 0, clean log. PREPATCH: atk_prepatch (Solution_prepatch.lean: hardcoded 'UTC' origin, no zones-equal skip) fails EXIT 1 on the exact `out = tzAdjustedExpr` goal on both discriminating clauses (source zone + skip) — G-DIFF reproduced.

STEP 2 (materialize+resolve): VACUOUS. No verifying wrong impl exists, so patches={} — there is no candidate whose faithful refined patch must be run through the harness. The one class the harness would need to resolve (the gold-faithful impl = atk_pos) is the gold patch itself, which resolves by construction (G-RESOLVE).

REFINEMENT.MD AUDIT (A-leg focus per plan §4): axioms=[], deep_model_references=[] — genuinely NO A-legs (verified against mapping.md §3.1 and conformance_check.py which uses the patched real MySQL _convert_field_to_tz as oracle, no un-substituted A callee). Every leg is R (A1-A4: str↔List Char, bool↔Bool type refinements) or I (A5 identical guard, A6 %-interp↔++ concat, A7 identity branch). No kind-3 (inexpressible-changed-op) legs: the operation that changed (conversion source zone + zones-equal skip) is modeled DEEPLY in tzAdjustedExpr, not hidden behind an axiom. §B three additional sites (Oracle + SQLite) ship verbatim in gold patch.diff, express no behaviour independent of the modeled MySQL decision (django__django-14376 precedent), and the F2P test test_query_convert_timezones runs on SQLite — all in gold, so resolve holds. Correspondence to real callees checks out.

VERDICT: SOUND. 8 distinct same-spec attacks + prepatch all fail to verify; positive control verifies; no verify⇏correct gap. The exact-equality full-domain postcondition leaves no room for a verifying-but-wrong impl.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution, Solution_prepatch)=True (spec region byte-identical, verified via swebench_unified.markers.same_spec with velvet backend). Solution.lean verifies (lean_verify exit 0). The modeled function buildTzAdjustedExpr/tzAdjustedExpr faithfully models the POST-patch MySQL DatabaseOperations._convert_field_to_tz: field_name wrapped as CONVERT_TZ(expr, 'storedZone', 'queryZone') iff active ∧ storedZone≠queryZone, else expr verbatim — exactly the gold hunk (source = connection.timezone_name, skip when zones equal). Differential testing vs the patched real callee shows ZERO divergence across (a) the pinned conformance seed (SEED=11138, 10^5 inputs), (b) an exhaustive cross-product over zones/exprs, and (c) an adversarial pass with format-injection args ('%s','%d','%(x)s',quotes,newlines,unicode). The %-format ↔ ++concat mapping is exact because the format template is fixed and its arguments are never re-interpreted, so any % in args stays literal on both sides. No axioms (deep model), so no un-substituted callee could hide drift. The 3 additional change sites (Oracle/SQLite) ship verbatim in patch.diff for G-RESOLVE and express the same predicate — legitimately unmodeled (django-14376 precedent). No input found where the spec disagrees with the real (patched) repo behavior; spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous gold-reconstruction check of the velvet spec view for django__django-11138.

Mechanical confirmations: same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) = True (spec regions axioms/pure/pre/post are byte-identical, spec frozen). leakage.screen passed=True, hard_failures=[] (no diff markers, no gold-patch line reproduced >=8 normalized chars, no patched file path/module in spec view, no spec identifier embedding a patched repo symbol).

Spec-view discriminating content that could reconstruct the gold edit:
  (1) conversion source = storedZone, NOT hardcoded 'UTC': CONVERT_TZ(<expr>, '<storedZone>', '<queryZone>');
  (2) wrap only when active AND storedZone != queryZone, else return expr verbatim (skip when zones equal / support off).

Both are fully disclosed by the PUBLIC problem_statement (not hints_text):
  - names CONVERT_TZ and shows the buggy CONVERT_TZ(`...`, 'UTC', 'Europe/Paris') SQL;
  - 'conversion should be from Paris to Paris, instead of UTC to Paris ... should go from the database timezone tz2 to the django app one tz1' => source is the stored/DB zone, not UTC (clause 1);
  - 'when tz1 == tz2, there should be no need to use CONVERT_TZ and the query will work without timezone tables' => skip-when-equal guard, including the 'no zone table required' rationale (clause 2);
  - even cites the exact operations.py line forcing 'UTC'.

Spec identifiers (tzAdjustedExpr, buildTzAdjustedExpr, storedZone, queryZone, active, expr, out) are neutral abstractions; none echo patched repo symbols (_convert_field_to_tz, connection.timezone_name, settings.USE_TZ, conn_tzname, _sqlite_datetime_* are all ABSENT from the spec view). The multi-site (Oracle/SQLite) detail lives only in refinement.md/mapping.md, which are not part of the spec view; and that scope is itself stated in the public problem title ('MySQL, SQLite, and Oracle').

Conclusion: the spec view reveals nothing about the gold edit beyond what the public problem_statement states verbatim. No leaking line. Matches recorded G-LEAK=pass and prior G-PANEL-3 NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
