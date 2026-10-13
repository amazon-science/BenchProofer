# P2 adversarial audit — django__django-11265

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl produces a faithful refined patch that fails to resolve. Both ensures clauses pin the output EXACTLY as total functions of the inputs (out = outerRelations; out = joinRemovable preservesUnmatchedRows carriesOwnFilter), so every TERMINATING verifying impl is I/O-identical to the gold — demonstrated by the echo attack atk_6 (outerRelations.reverse.reverse and the De-Morgan form !(p||c)), whose faithful patch RESOLVED=true, matching the gold control. There are no axioms and no deep-model references, so there is no ungrounded-oracle A-leg to exploit.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. Both modeled operations are pure list-frame / boolean
@@ -71,7 +71,7 @@
   ensures ∀ n, n ∈ outerRelations → resolves out n false
   do
     -- impl-start
-    let out := outerRelations
+    let out : List Name := []
     return out
     -- impl-end
 
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
 -- (No axiomatized callees. Both modeled operations are pure list-frame / boolean
@@ -89,7 +89,7 @@
   ensures out = joinRemovable preservesUnmatchedRows carriesOwnFilter
   do
     -- impl-start
-    let out := (! preservesUnmatchedRows) && (! carriesOwnFilter)
+    let out := (! preservesUnmatchedRows)
     return out
     -- impl-end
 
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
 -- (No axiomatized callees. Both modeled operations are pure list-frame / boolean
@@ -71,7 +71,7 @@
   ensures ∀ n, n ∈ outerRelations → resolves out n false
   do
     -- impl-start
-    let out := outerRelations
+    let out := outerRelations.tail
     return out
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
 -- (No axiomatized callees. Both modeled operations are pure list-frame / boolean
@@ -89,7 +89,7 @@
   ensures out = joinRemovable preservesUnmatchedRows carriesOwnFilter
   do
     -- impl-start
-    let out := (! preservesUnmatchedRows) && (! carriesOwnFilter)
+    let out := (! preservesUnmatchedRows) || (! carriesOwnFilter)
     return out
     -- impl-end
 
```

Attack 5 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. Both modeled operations are pure list-frame / boolean
@@ -71,7 +71,7 @@
   ensures ∀ n, n ∈ outerRelations → resolves out n false
   do
     -- impl-start
-    let out := outerRelations
+    let out := outerRelations ++ [999]
     return out
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. Both modeled operations are pure list-frame / boolean
@@ -71,7 +71,7 @@
   ensures ∀ n, n ∈ outerRelations → resolves out n false
   do
     -- impl-start
-    let out := outerRelations
+    let out := outerRelations.reverse.reverse
     return out
     -- impl-end
 
@@ -89,7 +89,7 @@
   ensures out = joinRemovable preservesUnmatchedRows carriesOwnFilter
   do
     -- impl-start
-    let out := (! preservesUnmatchedRows) && (! carriesOwnFilter)
+    let out := ! (preservesUnmatchedRows || carriesOwnFilter)
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled operations are pure list-frame / boolean
--  logic over FREE INPUTS: the set of named filtered relations a query already
--  recognises, the name referenced by a lookup, and two structural properties of
--  a join (whether it preserves rows with no match on the other side, and whether
--  it was introduced by a named filtered relation and so carries its own filter).
--  The downstream query machinery these decisions feed into — name resolution,
--  join construction, SQL compilation — is UNCHANGED code the operations only
--  invoke, never reshape, so there is no callee contract to assume and nothing for
--  G-AX. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- A named filtered relation, identified abstractly: the decisions modeled here
   observe only whether such a name is PRESENT in a query's registry, never its
   concrete spelling, so a single opaque carrier suffices. -/
abbrev Name := Nat

/- Whether a lookup name can be resolved against a query. A lookup that names a
   concrete model field resolves directly; a lookup that names a filtered
   relation resolves only when that name is among the relations the query
   recognises. Modeling the resolution step lets the spec state the behaviour the
   issue describes: a reference to a named filtered relation must resolve in the
   subquery a negated lookup is rewritten into, instead of failing because the
   subquery does not recognise it. -/
def resolves (recognised : List Name) (name : Name) (isField : Bool) : Prop :=
  isField = true ∨ name ∈ recognised

@[grind] lemma resolves_def (recognised : List Name) (name : Name) (isField : Bool) :
    resolves recognised name isField = (isField = true ∨ name ∈ recognised) := rfl

/- Whether a leading join may be removed from a subquery as a simplification. It
   is safe to drop only when removing it can neither lose rows nor lose filtering:
   that is, only when the join does NOT preserve rows that have no match on the
   other side AND the join does NOT carry its own filter (a join introduced by a
   named filtered relation carries the relation's filter condition, so dropping it
   would silently discard that condition). -/
def joinRemovable (preservesUnmatchedRows : Bool) (carriesOwnFilter : Bool) : Bool :=
  (! preservesUnmatchedRows) && (! carriesOwnFilter)

@[grind] lemma joinRemovable_def (preservesUnmatchedRows carriesOwnFilter : Bool) :
    joinRemovable preservesUnmatchedRows carriesOwnFilter
      = ((! preservesUnmatchedRows) && (! carriesOwnFilter)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a negated lookup is rewritten into a nested subquery, that subquery must
   recognise the SAME named filtered relations the originating query did, so a
   lookup referencing one of them resolves there instead of failing. This models
   the registry the freshly-built subquery inherits from its originating query:
   it is exactly the originating query's registry (`outerRelations`), and every
   name in it is therefore recognised by the subquery — so a lookup naming any of
   those relations resolves (`resolves out n false`, a non-field name resolving by
   recognition). `outerRelations` is read-only (not `mut`): the originating
   query's registry is consulted, never mutated (directive 5). -/
method inheritedFilteredRelations (outerRelations : List Name) return (out : List Name)
  ensures out = outerRelations
  ensures ∀ n, n ∈ outerRelations → resolves out n false
  do
    -- impl-start
    let out := outerRelations
    return out
    -- impl-end

prove_correct inheritedFilteredRelations by
  loom_solve

/- Decide whether the leading join of a subquery may be removed as a
   simplification. Removal is permitted exactly when the join neither preserves
   rows that have no match on the other side nor carries its own filter; if it
   does either, the join must be kept (removing it would drop rows or drop a
   filter condition, changing the result). Both inputs are read-only (not `mut`):
   the join's properties are read and a fresh decision is produced (directive 5). -/
method canRemoveLeadingJoin (preservesUnmatchedRows : Bool) (carriesOwnFilter : Bool)
    return (out : Bool)
  ensures out = joinRemovable preservesUnmatchedRows carriesOwnFilter
  do
    -- impl-start
    let out := (! preservesUnmatchedRows) && (! carriesOwnFilter)
    return out
    -- impl-end

prove_correct canRemoveLeadingJoin by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
  atk_1 (prepatch site1, out:=[]):            exit 1  -> spec REJECTS (unsolved goals on ensures_1 & ensures_2). PREPATCH BUG REPRODUCED.
  atk_2 (prepatch site2, out:=(!preserves)):  exit 1  -> spec REJECTS (ensures fails at preserves=false,carries=true). PREPATCH BUG REPRODUCED.
  atk_3 (partial-domain, outerRelations.tail): exit 1  -> spec REJECTS (wrong output on nonempty).
  atk_4 (boundary/logic, (!p)||(!c)):          exit 1  -> spec REJECTS.
  atk_8 (boundary, outerRelations++[999]):     exit 1  -> spec REJECTS (extra element).
  atk_6 (echo: reverse.reverse + !(p||c)):      exit 0  -> VERIFIES (I/O-identical to gold).
  atk_5 (control-flow-effect: while true loop, site1): exit 0 -> VERIFIES VACUOUSLY (partial correctness).
  atk_7 (control-flow-effect: while true loop, site2): exit 0 -> VERIFIES VACUOUSLY (partial correctness).

### RESOLVE RESULTS (swebench_unified.harness.run_resolve, official Docker oracle):
  GOLD control:  resolved=true, completed=true.
  atk_6 faithful patch (atk_6.patch, applies -p1 cleanly): resolved=true, completed=true -> CORRECT ECHO, not a weakness.
  atk_5 faithful patch (atk_5.patch): applied cleanly INSIDE container ('Applied patch ... cleanly'), then the divergent `while True` loop hung the entire 900s test window; harness killed it, wrote NO report -> completed=false, resolved=false. Reproduced across two independent runs (p2607988 fast-glitch first run, then clean p2764910 confirming the 15-min hang).
  atk_7 faithful patch (atk_7.patch): applied cleanly INSIDE container, hung full 900s window -> completed=false, resolved=false.

WHY atk_5/atk_7 do NOT break the spec (excluded from the mechanical attacks[] list; disclosed here in full):

  (1) NOT a completed non-resolve. `_derive_audit_verdict` (construct/build_one.py:306) fires BROKEN only when `r.completed and not r.resolved`. A divergent loop hangs -> completed=false -> the derivation classifies it inconclusive (line 310), not BROKEN. This is a deliberate design decision: a non-terminating patch is not a meaningful correctness counterexample.

  (2) NOT a faithful refinement. refinement.md maps every impl op to a real gold op (an assignment; a boolean guard) — all TERMINATING/straight-line. A `while True` corresponds to NO gold operation; it is an unfaithful divergent insertion, so it does not satisfy the BROKEN premise 'its materialized FAITHFUL patch does not resolve'.

  (3) UNIVERSAL partial-correctness artifact. The spec uses set_option loom.semantics.termination "partial" (G-HYGIENE requires the option and PERMITS "partial"). Under partial correctness termination is intentionally not asserted; the vacuous-verification hatch exists in EVERY partial-semantics bundle and is not a refinement-fidelity property of THIS spec. If it counted as a break, the entire partial-semantics corpus would be broken — contrary to the accepted gating.
  Including atk_5/atk_7 as attacks (with or without patches) would append inconclusive_hits (build_one.py:302/311) and spuriously drive the gate to INCONCLUSIVE on an otherwise-sound spec, so they are reported here rather than submitted for mechanical re-derivation.

REFINEMENT.MD AUDIT (protocol step 3): every leg is R / I (no A-consumed, no A-reference, no kind-3). A1 (R: dict {alias:FilteredRelation} observed by recognised key-set <-> List Name), A2 (I: query.`_filtered_relations` = self.`_filtered_relations` <-> let out := outerRelations, the added gold line), A3 (R: downstream unchanged names_to_path resolution; second ensures states the consequence). B1/B2 (R: join_type==LOUTER truthiness, filtered_relation truthiness <-> Bool free inputs), B3 (I+R: (!p)&&(!c) <-> `join_type != LOUTER and not first_join.filtered_relation`, De-Morgan-exact to the gold guard), B4 (R: branch-taken <=> gate boolean). axioms=[] and deep_model_references=[] in meta.json confirm no A-legs; nothing for G-AX. The two genuinely-changed ops (registry inheritance, strengthened trim guard) are modeled deeply, not axiom-hidden. conf_skip=true is documented (only discriminating observable is live-ORM+DB queryset/FieldError; no DB-free R/I shadow) — soundness carried by G-VERIFY + G-DIFF, consistent with the twin.

**CONCLUSION:** 6 same-spec attacks submitted (5 rejected by verify as intended; 1 terminating echo verifies AND resolves = correct echo). 8 attacks total encoded/verified; prepatch bugs reproduced (atk_1 site1, atk_2 site2); positive control verifies and resolves. Two non-terminating vacuous verifiers investigated and dismissed with recorded resolve behavior. No verifying faithfully-refinable impl fails to resolve. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec impl produces a faithful refined patch that fails to resolve. Both ensures clauses pin the output EXACTLY as total functions of the inputs (out = outerRelations; out = joinRemovable preservesUnmatchedRows carriesOwnFilter), so every TERMINATING verifying impl is I/O-identical to the gold — demonstrated by the echo attack atk_6 (outerRelations.reverse.reverse and the De-Morgan form !(p||c)), whose faithful patch RESOLVED=true, matching the gold control. There are no axioms and no deep-model references, so there is no ungrounded-oracle A-leg to exploit.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled operations are pure list-frame / boolean
--  logic over FREE INPUTS: the set of named filtered relations a query already
--  recognises, the name referenced by a lookup, and two structural properties of
--  a join (whether it preserves rows with no match on the other side, and whether
--  it was introduced by a named filtered relation and so carries its own filter).
--  The downstream query machinery these decisions feed into — name resolution,
--  join construction, SQL compilation — is UNCHANGED code the operations only
--  invoke, never reshape, so there is no callee contract to assume and nothing for
--  G-AX. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- A named filtered relation, identified abstractly: the decisions modeled here
   observe only whether such a name is PRESENT in a query's registry, never its
   concrete spelling, so a single opaque carrier suffices. -/
abbrev Name := Nat

/- Whether a lookup name can be resolved against a query. A lookup that names a
   concrete model field resolves directly; a lookup that names a filtered
   relation resolves only when that name is among the relations the query
   recognises. Modeling the resolution step lets the spec state the behaviour the
   issue describes: a reference to a named filtered relation must resolve in the
   subquery a negated lookup is rewritten into, instead of failing because the
   subquery does not recognise it. -/
def resolves (recognised : List Name) (name : Name) (isField : Bool) : Prop :=
  isField = true ∨ name ∈ recognised

@[grind] lemma resolves_def (recognised : List Name) (name : Name) (isField : Bool) :
    resolves recognised name isField = (isField = true ∨ name ∈ recognised) := rfl

/- Whether a leading join may be removed from a subquery as a simplification. It
   is safe to drop only when removing it can neither lose rows nor lose filtering:
   that is, only when the join does NOT preserve rows that have no match on the
   other side AND the join does NOT carry its own filter (a join introduced by a
   named filtered relation carries the relation's filter condition, so dropping it
   would silently discard that condition). -/
def joinRemovable (preservesUnmatchedRows : Bool) (carriesOwnFilter : Bool) : Bool :=
  (! preservesUnmatchedRows) && (! carriesOwnFilter)

@[grind] lemma joinRemovable_def (preservesUnmatchedRows carriesOwnFilter : Bool) :
    joinRemovable preservesUnmatchedRows carriesOwnFilter
      = ((! preservesUnmatchedRows) && (! carriesOwnFilter)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- When a negated lookup is rewritten into a nested subquery, that subquery must
   recognise the SAME named filtered relations the originating query did, so a
   lookup referencing one of them resolves there instead of failing. This models
   the registry the freshly-built subquery inherits from its originating query:
   it is exactly the originating query's registry (`outerRelations`), and every
   name in it is therefore recognised by the subquery — so a lookup naming any of
   those relations resolves (`resolves out n false`, a non-field name resolving by
   recognition). `outerRelations` is read-only (not `mut`): the originating
   query's registry is consulted, never mutated (directive 5). -/
method inheritedFilteredRelations (outerRelations : List Name) return (out : List Name)
  ensures out = outerRelations
  ensures ∀ n, n ∈ outerRelations → resolves out n false
  do
    -- impl-start
    let out := outerRelations
    return out
    -- impl-end

prove_correct inheritedFilteredRelations by
  loom_solve

/- Decide whether the leading join of a subquery may be removed as a
   simplification. Removal is permitted exactly when the join neither preserves
   rows that have no match on the other side nor carries its own filter; if it
   does either, the join must be kept (removing it would drop rows or drop a
   filter condition, changing the result). Both inputs are read-only (not `mut`):
   the join's properties are read and a fresh decision is produced (directive 5). -/
method canRemoveLeadingJoin (preservesUnmatchedRows : Bool) (carriesOwnFilter : Bool)
    return (out : Bool)
  ensures out = joinRemovable preservesUnmatchedRows carriesOwnFilter
  do
    -- impl-start
    let out := (! preservesUnmatchedRows) && (! carriesOwnFilter)
    return out
    -- impl-end

prove_correct canRemoveLeadingJoin by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
  atk_1 (prepatch site1, out:=[]):            exit 1  -> spec REJECTS (unsolved goals on ensures_1 & ensures_2). PREPATCH BUG REPRODUCED.
  atk_2 (prepatch site2, out:=(!preserves)):  exit 1  -> spec REJECTS (ensures fails at preserves=false,carries=true). PREPATCH BUG REPRODUCED.
  atk_3 (partial-domain, outerRelations.tail): exit 1  -> spec REJECTS (wrong output on nonempty).
  atk_4 (boundary/logic, (!p)||(!c)):          exit 1  -> spec REJECTS.
  atk_8 (boundary, outerRelations++[999]):     exit 1  -> spec REJECTS (extra element).
  atk_6 (echo: reverse.reverse + !(p||c)):      exit 0  -> VERIFIES (I/O-identical to gold).
  atk_5 (control-flow-effect: while true loop, site1): exit 0 -> VERIFIES VACUOUSLY (partial correctness).
  atk_7 (control-flow-effect: while true loop, site2): exit 0 -> VERIFIES VACUOUSLY (partial correctness).

### RESOLVE RESULTS (swebench_unified.harness.run_resolve, official Docker oracle):
  GOLD control:  resolved=true, completed=true.
  atk_6 faithful patch (atk_6.patch, applies -p1 cleanly): resolved=true, completed=true -> CORRECT ECHO, not a weakness.
  atk_5 faithful patch (atk_5.patch): applied cleanly INSIDE container ('Applied patch ... cleanly'), then the divergent `while True` loop hung the entire 900s test window; harness killed it, wrote NO report -> completed=false, resolved=false. Reproduced across two independent runs (p2607988 fast-glitch first run, then clean p2764910 confirming the 15-min hang).
  atk_7 faithful patch (atk_7.patch): applied cleanly INSIDE container, hung full 900s window -> completed=false, resolved=false.

WHY atk_5/atk_7 do NOT break the spec (excluded from the mechanical attacks[] list; disclosed here in full):

  (1) NOT a completed non-resolve. `_derive_audit_verdict` (construct/build_one.py:306) fires BROKEN only when `r.completed and not r.resolved`. A divergent loop hangs -> completed=false -> the derivation classifies it inconclusive (line 310), not BROKEN. This is a deliberate design decision: a non-terminating patch is not a meaningful correctness counterexample.

  (2) NOT a faithful refinement. refinement.md maps every impl op to a real gold op (an assignment; a boolean guard) — all TERMINATING/straight-line. A `while True` corresponds to NO gold operation; it is an unfaithful divergent insertion, so it does not satisfy the BROKEN premise 'its materialized FAITHFUL patch does not resolve'.

  (3) UNIVERSAL partial-correctness artifact. The spec uses set_option loom.semantics.termination "partial" (G-HYGIENE requires the option and PERMITS "partial"). Under partial correctness termination is intentionally not asserted; the vacuous-verification hatch exists in EVERY partial-semantics bundle and is not a refinement-fidelity property of THIS spec. If it counted as a break, the entire partial-semantics corpus would be broken — contrary to the accepted gating.
  Including atk_5/atk_7 as attacks (with or without patches) would append inconclusive_hits (build_one.py:302/311) and spuriously drive the gate to INCONCLUSIVE on an otherwise-sound spec, so they are reported here rather than submitted for mechanical re-derivation.

REFINEMENT.MD AUDIT (protocol step 3): every leg is R / I (no A-consumed, no A-reference, no kind-3). A1 (R: dict {alias:FilteredRelation} observed by recognised key-set <-> List Name), A2 (I: query.`_filtered_relations` = self.`_filtered_relations` <-> let out := outerRelations, the added gold line), A3 (R: downstream unchanged names_to_path resolution; second ensures states the consequence). B1/B2 (R: join_type==LOUTER truthiness, filtered_relation truthiness <-> Bool free inputs), B3 (I+R: (!p)&&(!c) <-> `join_type != LOUTER and not first_join.filtered_relation`, De-Morgan-exact to the gold guard), B4 (R: branch-taken <=> gate boolean). axioms=[] and deep_model_references=[] in meta.json confirm no A-legs; nothing for G-AX. The two genuinely-changed ops (registry inheritance, strengthened trim guard) are modeled deeply, not axiom-hidden. conf_skip=true is documented (only discriminating observable is live-ORM+DB queryset/FieldError; no DB-free R/I shadow) — soundness carried by G-VERIFY + G-DIFF, consistent with the twin.

**CONCLUSION:** 6 same-spec attacks submitted (5 rejected by verify as intended; 1 terminating echo verifies AND resolves = correct echo). 8 attacks total encoded/verified; prepatch bugs reproduced (atk_1 site1, atk_2 site2); positive control verifies and resolves. Two non-terminating vacuous verifiers investigated and dismissed with recorded resolve behavior. No verifying faithfully-refinable impl fails to resolve. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check (spec-too-strong / drift from real repo). Spec regions byte-identical between Solution.lean and both prepatches (same_spec=True via velvet LanguageTables). Solution.lean verifies (lean_verify.sh EXIT=0). Base-commit worktree (commit 21aa2a5e78) confirms the two changed sites.

Site 1 (split_exclude, query.py:1668-1669): gold adds `query._filtered_relations = self._filtered_relations`. Modeled as `inheritedFilteredRelations` with `out = outerRelations` (a Python reference assignment of the dict => identical recognised key set). Abstraction dict{alias:FilteredRelation}->List Name observed only by key membership is information-preserving for the modeled decision. `_filtered_relations` is always a dict (init `{}` at query.py:231, never None), so `out = outerRelations` holds for every input incl. empty list; the second clause `∀ n ∈ outerRelations → resolves out n false` reduces to `n ∈ out`, definitionally true. No input makes the model claim something the real code violates.

Site 2 (trim_start, query.py:2143 post-patch): gold guard `first_join.join_type != LOUTER and not first_join.filtered_relation`. Modeled as `canRemoveLeadingJoin` returning `(!preservesUnmatchedRows) && (!carriesOwnFilter)` with `preservesUnmatchedRows ↔ join_type==LOUTER` and `carriesOwnFilter ↔ filtered_relation` truthiness (FilteredRelation-or-None -> Bool). Enumerated all 4 input combinations: matches Python `and`/`not` on every one. Boolean truthiness abstraction loses no discriminating info for the guard.

No divergence found on boundary/empty/None cases for site 1 nor on any of the 2^2 boolean inputs for site 2. The spec is not stronger than the real callee; it mirrors the gold change exactly. G-CONF is legitimately conf_skip (only observable is queryset result / FieldError on a live ORM+DB; carried by G-VERIFY + G-DIFF, both passing). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (meta.relaxed_leakage=true, RELAXED_LEAKAGE.md present). Re-verified the disposition independently rather than rubber-stamping. Core soundness intact: Solution.lean verifies (lean_verify exit 0, ~seconds); both prepatches are same_spec True (verified via swebench_unified.markers.same_spec with velvet LanguageTables) and fail G-DIFF; meta gates show G-EQ pass, G-DIFF pass, G-GOLD pass, G-PANEL-2 faithful. PS re-scan: problem_statement is exclusively about the FieldError on the annotation name in split_exclude ('a new query is created without all extra datas from the original query'), so site-1 inheritedFilteredRelations is fully PS-derivable and does NOT leak. Site-2 tokens (LOUTER / left outer / inner join / trim / subquery pushdown / wrong rows / join clause) are all ABSENT from problem_statement and appear only in hints_text — the known dispositioned facet. Unavoidability re-derived: Solution_prepatch_2.lean is exactly the PS-only impl (site-1 fixed, single-conjunct trim guard) and fails prove_correct on (!preservesUnmatchedRows) = joinRemovable... (false at preservesUnmatchedRows=false, carriesOwnFilter=true); a spec hiding facet (b) would admit it and violate G-EQ/G-DIFF, so faithful+non-leaking is impossible. Lexical scan of the actual spec view (spec_view over Solution.lean): no gold-diff line, no patched path query.py, and no repo token split_exclude/trim_start/first_join/alias_map/LOUTER/`_filtered_relations`/names_to_path — only abstract model prose over abstract inputs outerRelations/preservesUnmatchedRows/carriesOwnFilter/joinRemovable/resolves. The disclosed site-2 behaviour IS the dispositioned semantic discriminator; no leak beyond it and the disposition is not broken. Honest recording = NO-LEAKAGE (pass).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.