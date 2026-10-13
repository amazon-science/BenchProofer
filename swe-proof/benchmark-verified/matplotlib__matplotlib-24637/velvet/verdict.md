# P2 adversarial audit — matplotlib__matplotlib-24637

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying-but-wrong impl exists. The spec pins out to the closed form `out = RenderCmd.beginGroup gid :: (children ++ [RenderCmd.endGroup])` (plus 4 derived head?/getLast?/tail/length clauses), leaving no admissible wrong output.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees: the enclosing-group commands and the child renderings
@@ -68,9 +68,8 @@
   ensures out.length = children.length + 2
   do
     -- impl-start
-    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]
+    let mut trace : List RenderCmd := []
     trace := trace ++ children
-    trace := trace ++ [RenderCmd.endGroup]
     return trace
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
 -- (No axiomatized callees: the enclosing-group commands and the child renderings
@@ -68,10 +68,7 @@
   ensures out.length = children.length + 2
   do
     -- impl-start
-    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]
-    trace := trace ++ children
-    trace := trace ++ [RenderCmd.endGroup]
-    return trace
+    return children ++ [RenderCmd.endGroup]
     -- impl-end
 
 prove_correct groupedRender by
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
 -- (No axiomatized callees: the enclosing-group commands and the child renderings
@@ -68,10 +68,7 @@
   ensures out.length = children.length + 2
   do
     -- impl-start
-    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]
-    trace := trace ++ children
-    trace := trace ++ [RenderCmd.endGroup]
-    return trace
+    return RenderCmd.beginGroup gid :: children
     -- impl-end
 
 prove_correct groupedRender by
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
 -- (No axiomatized callees: the enclosing-group commands and the child renderings
@@ -68,10 +68,7 @@
   ensures out.length = children.length + 2
   do
     -- impl-start
-    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]
-    trace := trace ++ children
-    trace := trace ++ [RenderCmd.endGroup]
-    return trace
+    return RenderCmd.beginGroup none :: (children ++ [RenderCmd.endGroup])
     -- impl-end
 
 prove_correct groupedRender by
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
 -- (No axiomatized callees: the enclosing-group commands and the child renderings
@@ -68,10 +68,7 @@
   ensures out.length = children.length + 2
   do
     -- impl-start
-    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]
-    trace := trace ++ children
-    trace := trace ++ [RenderCmd.endGroup]
-    return trace
+    return RenderCmd.beginGroup gid :: [RenderCmd.endGroup]
     -- impl-end
 
 prove_correct groupedRender by
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
 -- (No axiomatized callees: the enclosing-group commands and the child renderings
@@ -68,10 +68,7 @@
   ensures out.length = children.length + 2
   do
     -- impl-start
-    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]
-    trace := trace ++ children
-    trace := trace ++ [RenderCmd.endGroup]
-    return trace
+    return RenderCmd.beginGroup gid :: (children.reverse ++ [RenderCmd.endGroup])
     -- impl-end
 
 prove_correct groupedRender by
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
 -- (No axiomatized callees: the enclosing-group commands and the child renderings
@@ -68,10 +68,7 @@
   ensures out.length = children.length + 2
   do
     -- impl-start
-    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]
-    trace := trace ++ children
-    trace := trace ++ [RenderCmd.endGroup]
-    return trace
+    return RenderCmd.endGroup :: (children ++ [RenderCmd.beginGroup gid])
     -- impl-end
 
 prove_correct groupedRender by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the enclosing-group commands and the child renderings
@@ -68,10 +68,10 @@
   ensures out.length = children.length + 2
   do
     -- impl-start
-    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]
-    trace := trace ++ children
-    trace := trace ++ [RenderCmd.endGroup]
-    return trace
+    if children.isEmpty then
+      return RenderCmd.beginGroup gid :: (children ++ [RenderCmd.endGroup])
+    else
+      return children
     -- impl-end
 
 prove_correct groupedRender by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the enclosing-group commands and the child renderings
@@ -68,10 +68,7 @@
   ensures out.length = children.length + 2
   do
     -- impl-start
-    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]
-    trace := trace ++ children
-    trace := trace ++ [RenderCmd.endGroup]
-    return trace
+    return RenderCmd.beginGroup gid :: (children ++ [RenderCmd.endGroup, RenderCmd.endGroup])
     -- impl-end
 
 prove_correct groupedRender by
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees: the enclosing-group commands and the child renderings
@@ -68,9 +68,8 @@
   ensures out.length = children.length + 2
   do
     -- impl-start
-    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]
+    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid, RenderCmd.endGroup]
     trace := trace ++ children
-    trace := trace ++ [RenderCmd.endGroup]
     return trace
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the enclosing-group commands and the child renderings
--  are modeled directly as the command stream the render handed to the back end;
--  no unchanged callee's contract is consumed by the proof.)
-- axioms-end

-- pure-start
/- A single drawing command handed to the rendering back end while a composite
   artist is rendered.

     * `beginGroup gid` — start a grouping element tagged with the artist's own
        identifier `gid` (absent when the artist has none);
     * `endGroup`       — finish the grouping element opened most recently;
     * `child`          — one of the drawing commands emitted by a contained
        sub-artist (its concrete payload is opaque to this model; only its
        position in the stream matters here).

   The command stream is the observable the back end turns into output, so it is
   the carrier of the rendering behaviour. -/
inductive RenderCmd where
  | beginGroup (gid : Option String)
  | endGroup
  | child (tag : Nat)
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Rendering a composite artist that is to be drawn (its visibility/placement
   guard already passed). The artist exposes an optional identifier `gid` and a
   contained drawing `children` — the in-order command stream produced by its
   sub-renderings. The rendering of the whole composite must be enclosed as a
   single addressable unit tagged with the artist's OWN identifier: the stream
   opens with a grouping element carrying `gid`, then contains the children's
   commands unchanged and in order, then closes that grouping element. Thus the
   artist's identifier reaches the back end and labels the composite as a whole
   in the output.

   `gid` and `children` are read-only inputs (neither is `mut`): the rendering
   neither invents nor alters the identifier and reproduces the children's
   command stream verbatim (directive 5). -/
method groupedRender (gid : Option String) (children : List RenderCmd)
    return (out : List RenderCmd)
  -- The full enclosed stream: open-tag(gid), then the children verbatim and in
  -- order, then the matching close-tag.
  ensures out = RenderCmd.beginGroup gid :: (children ++ [RenderCmd.endGroup])
  -- The stream OPENS with a grouping element carrying the artist's own
  -- identifier (the discriminating observable: the identifier is passed on).
  ensures out.head? = some (RenderCmd.beginGroup gid)
  -- The enclosing grouping element is closed (the stream ends with the matching
  -- close-tag), so the children are bracketed as one unit.
  ensures out.getLast? = some RenderCmd.endGroup
  -- The children are carried through unchanged, in order, bracketed by the two
  -- enclosing commands.
  ensures out.tail = children ++ [RenderCmd.endGroup]
  ensures out.length = children.length + 2
  do
    -- impl-start
    return RenderCmd.beginGroup gid :: (children ++ [RenderCmd.endGroup])
    -- impl-end

prove_correct groupedRender by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) audit for matplotlib__matplotlib-24637 velvet.

SAME-SPEC: all 10 attacks + positive control same_spec=True vs frozen Solution.lean (via swebench_unified.markers.same_spec, velvet lang). Diffs confined to impl region (lines 71-74) only; axioms/pure/pre/post byte-identical.

VERIFY (bash scripts/lean_verify.sh <f>), run concurrently in batches of 4:
- atk_1 prepatch bug (only children, no group) -> exit=1 (rejected on all 5 ensures). prepatch reproduced.
- atk_2 missing beginGroup (children ++ [endGroup]) -> exit=1 (head?/full-eq).
- atk_3 missing endGroup (beginGroup gid :: children) -> exit=1 (getLast?/tail/length/full-eq).
- atk_4 ungrounded-oracle/wrong-identifier (beginGroup none) -> exit=1 (ensures_4 head? + ensures_5 full-eq). Core issue observable.
- atk_5 children dropped (beginGroup gid :: [endGroup]) -> exit=1 (tail/length/full-eq).
- atk_6 children reordered (children.reverse) -> exit=1 (tail/full-eq).
- atk_7 open/close swapped (endGroup :: children ++ [beginGroup gid]) -> exit=1 (head?/getLast?/full-eq).
- atk_8 PARTIAL-DOMAIN (correct iff children empty, else returns bare children) -> exit=1: verified genuine failure on the else branch (unsolved goals ensures_1..5 under if_neg ¬children.isEmpty). Confirms the spec is total, not domain-restricted.
- atk_9 BOUNDARY (extra endGroup: ...++[endGroup,endGroup]) -> exit=1 (tail/length/full-eq).
- atk_10 CONTROL-FLOW-EFFECT (mut accumulator seeded [beginGroup,endGroup] then ++children => endGroup misplaced) -> exit=1.
All failures are Lean `unsolved goals` (real proof failures, verified from logs), not syntax/import errors.

POSITIVE CONTROL atk_pos (structurally different correct impl: single `return beginGroup gid :: (children ++ [endGroup])`, no mut) -> exit=0, clean log. Spec non-vacuous.

STEP-2 (materialize faithful patch + run_resolve): NOT TRIGGERED — the protocol requires it only for wrong impls that VERIFY, and zero wrong impls verified. No verify⇏correct exhibit is possible when nothing wrong passes the checker.

A-LEG / REFINEMENT AUDIT (the assigned focus): ls confirms NO axiom_check.py; Solution.lean axioms block is empty (only comment lines 9-13). refinement.md legs A1/A2/A3 are all R+I with the two genuinely-changed grouping ops (open_group(gid=get_gid())/close_group) modeled DIRECTLY as beginGroup gid / endGroup at head/tail — no A-consumed, no A-reference deep model, no kind-3. There is therefore no axiom-soundness or deep-model↔callee correspondence trust point to subvert; the postcondition is grounded entirely in the read-only inputs gid/children (no opaque oracle to echo, killing the ungrounded-oracle vector — atk_4 confirms an impl that drops gid is rejected). Model↔patch correspondence holds: verified stream = beginGroup gid :: children ++ [endGroup] maps to open_group(gid=self.get_gid()) + unchanged body + close_group, i.e. gold patch up to type refinement (mapping.md §2 bijection). G-CONF cross-checks the real patched draw.

VERDICT: SOUND. 10 distinct same-spec wrong impls (incl. partial-domain, boundary, control-flow-effect, ungrounded-oracle/wrong-id echo) all fail verification; positive control passes; no verifying-but-wrong impl exists, so verify⇒correct is not falsifiable here. Spec is tight and the (empty) A-legs are vacuously sound.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying-but-wrong impl exists. The spec pins out to the closed form `out = RenderCmd.beginGroup gid :: (children ++ [RenderCmd.endGroup])` (plus 4 derived head?/getLast?/tail/length clauses), leaving no admissible wrong output.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the enclosing-group commands and the child renderings
--  are modeled directly as the command stream the render handed to the back end;
--  no unchanged callee's contract is consumed by the proof.)
-- axioms-end

-- pure-start
/- A single drawing command handed to the rendering back end while a composite
   artist is rendered.

     * `beginGroup gid` — start a grouping element tagged with the artist's own
        identifier `gid` (absent when the artist has none);
     * `endGroup`       — finish the grouping element opened most recently;
     * `child`          — one of the drawing commands emitted by a contained
        sub-artist (its concrete payload is opaque to this model; only its
        position in the stream matters here).

   The command stream is the observable the back end turns into output, so it is
   the carrier of the rendering behaviour. -/
inductive RenderCmd where
  | beginGroup (gid : Option String)
  | endGroup
  | child (tag : Nat)
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Rendering a composite artist that is to be drawn (its visibility/placement
   guard already passed). The artist exposes an optional identifier `gid` and a
   contained drawing `children` — the in-order command stream produced by its
   sub-renderings. The rendering of the whole composite must be enclosed as a
   single addressable unit tagged with the artist's OWN identifier: the stream
   opens with a grouping element carrying `gid`, then contains the children's
   commands unchanged and in order, then closes that grouping element. Thus the
   artist's identifier reaches the back end and labels the composite as a whole
   in the output.

   `gid` and `children` are read-only inputs (neither is `mut`): the rendering
   neither invents nor alters the identifier and reproduces the children's
   command stream verbatim (directive 5). -/
method groupedRender (gid : Option String) (children : List RenderCmd)
    return (out : List RenderCmd)
  -- The full enclosed stream: open-tag(gid), then the children verbatim and in
  -- order, then the matching close-tag.
  ensures out = RenderCmd.beginGroup gid :: (children ++ [RenderCmd.endGroup])
  -- The stream OPENS with a grouping element carrying the artist's own
  -- identifier (the discriminating observable: the identifier is passed on).
  ensures out.head? = some (RenderCmd.beginGroup gid)
  -- The enclosing grouping element is closed (the stream ends with the matching
  -- close-tag), so the children are bracketed as one unit.
  ensures out.getLast? = some RenderCmd.endGroup
  -- The children are carried through unchanged, in order, bracketed by the two
  -- enclosing commands.
  ensures out.tail = children ++ [RenderCmd.endGroup]
  ensures out.length = children.length + 2
  do
    -- impl-start
    return RenderCmd.beginGroup gid :: (children ++ [RenderCmd.endGroup])
    -- impl-end

prove_correct groupedRender by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) audit for matplotlib__matplotlib-24637 velvet.

SAME-SPEC: all 10 attacks + positive control same_spec=True vs frozen Solution.lean (via swebench_unified.markers.same_spec, velvet lang). Diffs confined to impl region (lines 71-74) only; axioms/pure/pre/post byte-identical.

VERIFY (bash scripts/lean_verify.sh <f>), run concurrently in batches of 4:
- atk_1 prepatch bug (only children, no group) -> exit=1 (rejected on all 5 ensures). prepatch reproduced.
- atk_2 missing beginGroup (children ++ [endGroup]) -> exit=1 (head?/full-eq).
- atk_3 missing endGroup (beginGroup gid :: children) -> exit=1 (getLast?/tail/length/full-eq).
- atk_4 ungrounded-oracle/wrong-identifier (beginGroup none) -> exit=1 (ensures_4 head? + ensures_5 full-eq). Core issue observable.
- atk_5 children dropped (beginGroup gid :: [endGroup]) -> exit=1 (tail/length/full-eq).
- atk_6 children reordered (children.reverse) -> exit=1 (tail/full-eq).
- atk_7 open/close swapped (endGroup :: children ++ [beginGroup gid]) -> exit=1 (head?/getLast?/full-eq).
- atk_8 PARTIAL-DOMAIN (correct iff children empty, else returns bare children) -> exit=1: verified genuine failure on the else branch (unsolved goals ensures_1..5 under if_neg ¬children.isEmpty). Confirms the spec is total, not domain-restricted.
- atk_9 BOUNDARY (extra endGroup: ...++[endGroup,endGroup]) -> exit=1 (tail/length/full-eq).
- atk_10 CONTROL-FLOW-EFFECT (mut accumulator seeded [beginGroup,endGroup] then ++children => endGroup misplaced) -> exit=1.
All failures are Lean `unsolved goals` (real proof failures, verified from logs), not syntax/import errors.

POSITIVE CONTROL atk_pos (structurally different correct impl: single `return beginGroup gid :: (children ++ [endGroup])`, no mut) -> exit=0, clean log. Spec non-vacuous.

STEP-2 (materialize faithful patch + run_resolve): NOT TRIGGERED — the protocol requires it only for wrong impls that VERIFY, and zero wrong impls verified. No verify⇏correct exhibit is possible when nothing wrong passes the checker.

A-LEG / REFINEMENT AUDIT (the assigned focus): ls confirms NO axiom_check.py; Solution.lean axioms block is empty (only comment lines 9-13). refinement.md legs A1/A2/A3 are all R+I with the two genuinely-changed grouping ops (open_group(gid=get_gid())/close_group) modeled DIRECTLY as beginGroup gid / endGroup at head/tail — no A-consumed, no A-reference deep model, no kind-3. There is therefore no axiom-soundness or deep-model↔callee correspondence trust point to subvert; the postcondition is grounded entirely in the read-only inputs gid/children (no opaque oracle to echo, killing the ungrounded-oracle vector — atk_4 confirms an impl that drops gid is rejected). Model↔patch correspondence holds: verified stream = beginGroup gid :: children ++ [endGroup] maps to open_group(gid=self.get_gid()) + unchanged body + close_group, i.e. gold patch up to type refinement (mapping.md §2 bijection). G-CONF cross-checks the real patched draw.

VERDICT: SOUND. 10 distinct same-spec wrong impls (incl. partial-domain, boundary, control-flow-effect, ungrounded-oracle/wrong-id echo) all fail verification; positive control passes; no verifying-but-wrong impl exists, so verify⇒correct is not falsifiable here. Spec is tight and the (empty) A-legs are vacuously sound.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on velvet groupedRender (models matplotlib.offsetbox.AnnotationBbox.draw @ base a9ba9d5d, lib/matplotlib/offsetbox.py:1449). No diverging input found; the modeled function agrees with the real callee everywhere tested.

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean)=True; spec_view sha256=6914289000028df4f1f8b55c4fb2ee19e8ceca548ad3029356d57bbca16a7177, matching the recorded G-PANEL-3 hash. Only impl regions differ (post-patch emits open::children::close; prepatch emits children only and correctly fails the postconditions). Positive control: Solution.lean verifies under lean_verify.sh (exit 0).

GOLD PATCH: inserts renderer.open_group(cls, gid=self.get_gid()) before the composite body and renderer.close_group(cls) after it, inside the visibility/_check_xy guard. Model: out = beginGroup gid :: (children ++ [endGroup]); postconditions pin head?=beginGroup gid, getLast?=endGroup, tail=children++[endGroup], length=children.length+2.

INDEPENDENT REPO CHECK: I applied the gold-patched draw via monkeypatch and captured the real ordered back-end command stream against a recording renderer (open_group/close_group + draw_path/image/text/... instrumented) over the F2P identifier ('a test for issue 20044') plus boundary inputs None, '', unicode 'générateur', and 'id with <chars>'. Every case produced first=('open',gid), last=('close',), single enclosing bracket (depth returns to 0 only at the final close), and real child draw commands (4) strictly interior — exactly the model's structural prediction, 0 disagreements. Matches the bundled conformance_check.py logic.

ABSTRACTION SOUNDNESS: children is a free opaque List RenderCmd; the real body wraps whatever sub-renderings emit, so for ANY children stream the real function yields open::children::close — the spec is not stronger than reality (no children value can break it; sub-artists' own groups stay nested inside children, confirmed empirically). gid:Option String faithfully models the self.get_gid() argument (None/'' falsy ↔ no id; non-empty ↔ id). The abstracted constant label self.__class__.__name__ and opaque child payloads do not affect the tested behaviour (the SVG <g id=...> observable depends only on the gid carried to the FIRST open_group). The excluded visibility/_check_xy early-return is outside the modeled guarded body and legitimately abstracted (the F2P artist is visible). No axioms, so no axiom-soundness trust point. Conclusion: spec is faithful, not too strong; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True (spec region byte-identical, only impl differs); spec_view rendered via spec_signature and token-scanned.

Gold edit: wrap AnnotationBbox.draw body between renderer.open_group(self.__class__.__name__, gid=self.get_gid()) and renderer.close_group(...) in lib/matplotlib/offsetbox.py.

Public problem_statement (excluding hints_text) discloses only the GOAL: a gid set on an AnnotationBbox does not reach the SVG output, and the user wants the annotation-as-a-whole to carry the gid (references prior PR #15087 gid fix). It does NOT reveal the open_group/close_group mechanism, which appears ONLY in hints_text (out of scope).

Spec view = RenderCmd inductive (beginGroup/endGroup/child) + groupedRender(gid, children) with postconditions out = beginGroup gid :: (children ++ [endGroup]) and head?/getLast?/tail/length, plus abstract prose ('enclose the whole composite as a single addressable unit tagged with the artist's OWN identifier'). Token scan of the spec view finds NONE of the gold-patch identifiers: no open_group/close_group, no AnnotationBbox/offsetbox, no get_gid/__class__, no 'renderer', no 'svg', no '<g', no file path, no update_positions/arrow_patch/patch.draw/offsetbox.draw. 'draw' appears only as generic prose ('drawing command', 'to be drawn').

The spec view formalizes the required observable (bracket the children in a group carrying gid) at a fully abstracted level; that obligation IS the specification and is a natural formalization of the already-public goal. It does not disclose edit locus, concrete API names, class label, or file. All repo bindings (open_group/close_group, offsetbox.py:1449, get_gid, SVG <g id>) live exclusively in mapping.md / refinement.md, which are NOT part of the spec view. Reconstructing the gold patch still requires independently locating AnnotationBbox.draw and knowing the renderer.open_group/close_group API — the spec view supplies neither. No line leaks the gold edit beyond the public problem_statement. Consistent with G-LEAK pass (failures=[]).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
