# P2 adversarial audit — sympy__sympy-15976

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1_prepatch.lean`, `atk2_partial.lean`, `atk3_order.lean`, `atk4_nobold.lean`, `atk6_tagswap.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk5_echo.lean`, `atk7_echovar.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's postcondition `ensures out = buildSymbol name subs sups bold` is an EXACT structural equality to the frozen concrete deep model, so any verifying impl must equal buildSymbol value-for-value. Every genuinely-wrong impl fails verification; the only verifying 'wrong' impls are echoes of buildSymbol, which are behaviorally equal to the gold post-image and whose faithful patch (the gold patch) resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,19 +120,14 @@
   ensures bold = true → out.isBold = true
   do
     -- impl-start
-    -- Build the base-name identifier, then choose the representing node directly
-    -- from which scripts are present: with no superscripts, either the bare
-    -- identifier (no subscripts) or a subscript container; with superscripts,
-    -- either a superscript container (no subscripts) or a sub-and-superscript
-    -- container. Finally apply bold styling to that representing node.
     let mname : Node := .elem "mi".toList false [Node.text name]
-    let core : Node :=
+    let child : Node :=
       match sups, subs with
-      | none,     none     => mname
+      | none,     none     => Node.text name
       | none,     some sub => .elem "msub".toList false [mname, sub]
       | some sup, none     => .elem "msup".toList false [mname, sup]
       | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
-    let x := setBold core bold
+    let x : Node := .elem "mi".toList bold [child]
     return x
     -- impl-end
 
```

Attack 2 — `atk2_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,19 +120,8 @@
   ensures bold = true → out.isBold = true
   do
     -- impl-start
-    -- Build the base-name identifier, then choose the representing node directly
-    -- from which scripts are present: with no superscripts, either the bare
-    -- identifier (no subscripts) or a subscript container; with superscripts,
-    -- either a superscript container (no subscripts) or a sub-and-superscript
-    -- container. Finally apply bold styling to that representing node.
     let mname : Node := .elem "mi".toList false [Node.text name]
-    let core : Node :=
-      match sups, subs with
-      | none,     none     => mname
-      | none,     some sub => .elem "msub".toList false [mname, sub]
-      | some sup, none     => .elem "msup".toList false [mname, sup]
-      | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
-    let x := setBold core bold
+    let x := setBold mname bold
     return x
     -- impl-end
 
```

Attack 3 — `atk3_order.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,18 +120,13 @@
   ensures bold = true → out.isBold = true
   do
     -- impl-start
-    -- Build the base-name identifier, then choose the representing node directly
-    -- from which scripts are present: with no superscripts, either the bare
-    -- identifier (no subscripts) or a subscript container; with superscripts,
-    -- either a superscript container (no subscripts) or a sub-and-superscript
-    -- container. Finally apply bold styling to that representing node.
     let mname : Node := .elem "mi".toList false [Node.text name]
     let core : Node :=
       match sups, subs with
       | none,     none     => mname
       | none,     some sub => .elem "msub".toList false [mname, sub]
       | some sup, none     => .elem "msup".toList false [mname, sup]
-      | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
+      | some sup, some sub => .elem "msubsup".toList false [mname, sup, sub]
     let x := setBold core bold
     return x
     -- impl-end
```

Attack 4 — `atk4_nobold.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,11 +120,6 @@
   ensures bold = true → out.isBold = true
   do
     -- impl-start
-    -- Build the base-name identifier, then choose the representing node directly
-    -- from which scripts are present: with no superscripts, either the bare
-    -- identifier (no subscripts) or a subscript container; with superscripts,
-    -- either a superscript container (no subscripts) or a sub-and-superscript
-    -- container. Finally apply bold styling to that representing node.
     let mname : Node := .elem "mi".toList false [Node.text name]
     let core : Node :=
       match sups, subs with
@@ -132,8 +127,7 @@
       | none,     some sub => .elem "msub".toList false [mname, sub]
       | some sup, none     => .elem "msup".toList false [mname, sup]
       | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
-    let x := setBold core bold
-    return x
+    return core
     -- impl-end
 
 prove_correct buildSymbolNode by
```

Attack 5 — `atk5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -120,20 +120,7 @@
   ensures bold = true → out.isBold = true
   do
     -- impl-start
-    -- Build the base-name identifier, then choose the representing node directly
-    -- from which scripts are present: with no superscripts, either the bare
-    -- identifier (no subscripts) or a subscript container; with superscripts,
-    -- either a superscript container (no subscripts) or a sub-and-superscript
-    -- container. Finally apply bold styling to that representing node.
-    let mname : Node := .elem "mi".toList false [Node.text name]
-    let core : Node :=
-      match sups, subs with
-      | none,     none     => mname
-      | none,     some sub => .elem "msub".toList false [mname, sub]
-      | some sup, none     => .elem "msup".toList false [mname, sup]
-      | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
-    let x := setBold core bold
-    return x
+    return buildSymbol name subs sups bold
     -- impl-end
 
 prove_correct buildSymbolNode by
```

Attack 6 — `atk6_tagswap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,17 +120,12 @@
   ensures bold = true → out.isBold = true
   do
     -- impl-start
-    -- Build the base-name identifier, then choose the representing node directly
-    -- from which scripts are present: with no superscripts, either the bare
-    -- identifier (no subscripts) or a subscript container; with superscripts,
-    -- either a superscript container (no subscripts) or a sub-and-superscript
-    -- container. Finally apply bold styling to that representing node.
     let mname : Node := .elem "mi".toList false [Node.text name]
     let core : Node :=
       match sups, subs with
       | none,     none     => mname
-      | none,     some sub => .elem "msub".toList false [mname, sub]
-      | some sup, none     => .elem "msup".toList false [mname, sup]
+      | none,     some sub => .elem "msup".toList false [mname, sub]
+      | some sup, none     => .elem "msub".toList false [mname, sup]
       | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
     let x := setBold core bold
     return x
```

Attack 7 — `atk7_echovar.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -120,20 +120,13 @@
   ensures bold = true → out.isBold = true
   do
     -- impl-start
-    -- Build the base-name identifier, then choose the representing node directly
-    -- from which scripts are present: with no superscripts, either the bare
-    -- identifier (no subscripts) or a subscript container; with superscripts,
-    -- either a superscript container (no subscripts) or a sub-and-superscript
-    -- container. Finally apply bold styling to that representing node.
-    let mname : Node := .elem "mi".toList false [Node.text name]
     let core : Node :=
       match sups, subs with
-      | none,     none     => mname
-      | none,     some sub => .elem "msub".toList false [mname, sub]
-      | some sup, none     => .elem "msup".toList false [mname, sup]
-      | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
-    let x := setBold core bold
-    return x
+      | none,     none     => mkMi name
+      | none,     some sub => .elem "msub".toList false [mkMi name, sub]
+      | some sup, none     => .elem "msup".toList false [mkMi name, sup]
+      | some sup, some sub => .elem "msubsup".toList false [mkMi name, sub, sup]
+    return setBold core bold
     -- impl-end
 
 prove_correct buildSymbolNode by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the node-assembly routine must COMPLETE (the
-- real routine is straight-line code — a match over which scripts are present
-- plus one attribute write — that always terminates), so the spec must also
-- rule out diverging implementations: under partial correctness a
-- non-terminating body would vacuously satisfy every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model references. The decomposition of a
--  variable's printed name into its base name plus its lists of subscript and
--  superscript pieces, and the rendering of each such list into a single
--  presentation node, are unchanged upstream infrastructure: they are supplied
--  to this routine as the inputs `name`, `subs`, and `sups`. The only behavior
--  modeled here is the per-node decision of how those pieces are assembled into
--  the single node that represents the variable, which is modeled deeply in the
--  `pure` region. There is no `axiom` declaration. See mapping.md / refinement.md.)
-- axioms-end

-- pure-start
/- A presentation-markup node. Either a text node carrying a string value, or an
   element node carrying its tag name, a flag recording whether it bears the
   bold styling attribute, and its ordered children. Only the observables the
   acceptance tests inspect — the top element's tag, its bold flag, and its
   child structure — are represented. -/
inductive Node where
  | text (value : List Char)
  | elem (tag : List Char) (bold : Bool) (children : List Node)
  deriving Inhabited

/- The tag (node name) of a node; the text-node sentinel for text nodes. -/
def Node.tag : Node → List Char
  | .text _      => "#text".toList
  | .elem t _ _  => t

/- Whether a node carries the bold styling attribute (false for a text node). -/
def Node.isBold : Node → Bool
  | .text _      => false
  | .elem _ b _  => b

/- The identifier element wrapping a base name: an `mi` element whose single
   child is the name text. This is how the base name is presented (unchanged
   infrastructure, spelled out here so the assembled node is fully grounded in
   the inputs). -/
def mkMi (name : List Char) : Node :=
  .elem "mi".toList false [Node.text name]

/- Apply the bold styling to a node when requested: set the bold flag on the
   element; requesting no styling leaves the node unchanged. Applied to whichever
   node ends up representing the variable. -/
def setBold : Node → Bool → Node
  | .text v,        _ => .text v
  | .elem t b0 ch,  b => .elem t (b0 || b) ch

/- Assemble the single node that represents a variable, given its base name, its
   subscript node (present iff the variable has subscripts), its superscript node
   (present iff the variable has superscripts), and whether bold styling applies.

   The node that represents the variable is determined directly by which scripts
   are present:
     * no scripts          → the bare base-name identifier;
     * subscripts only      → a subscript container of the base name and the
                              subscript node;
     * superscripts only    → a superscript container of the base name and the
                              superscript node;
     * both                 → a sub-and-superscript container of the base name,
                              the subscript node, then the superscript node.
   Bold styling, when requested, is applied to that representing node itself. -/
def buildSymbol (name : List Char) (subs sups : Option Node) (bold : Bool) : Node :=
  let mname := mkMi name
  let core : Node :=
    match sups, subs with
    | none,     none     => mname
    | none,     some sub => .elem "msub".toList false [mname, sub]
    | some sup, none     => .elem "msup".toList false [mname, sup]
    | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
  setBold core bold

@[simp] lemma setBold_tag (n : Node) (b : Bool) : (setBold n b).tag = n.tag := by
  cases n <;> rfl

/- Applying bold styling to an element node sets its bold flag. (The representing
   node is always an element, so this is the only case the postcondition uses.) -/
@[simp] lemma setBold_elem_isBold (t : List Char) (b0 : Bool) (ch : List Node) :
    (setBold (.elem t b0 ch) true).isBold = true := by
  simp [setBold, Node.isBold]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the single presentation node that represents a printed variable.

   `name` is the variable's base name; `subs` is the subscript node (present iff
   the variable carries subscripts) and `sups` the superscript node (present iff
   it carries superscripts), each already rendered by unchanged infrastructure;
   `bold` requests bold styling. All four are read-only (none is `mut`): the
   routine consults them and produces a fresh node (directive 5).

   The desired behavior: the node the routine returns is the script container
   itself when the variable has scripts — a subscript container when it has only
   subscripts, a superscript container when it has only superscripts, and a
   sub-and-superscript container when it has both; a variable with no scripts is
   presented as the bare base-name identifier. Bold styling applies to that
   returned node. -/
method buildSymbolNode (name : List Char) (subs : Option Node) (sups : Option Node) (bold : Bool) return (out : Node)
  ensures out = buildSymbol name subs sups bold
  ensures (subs = none ∧ sups = none) → out.tag = "mi".toList
  ensures (subs ≠ none ∧ sups = none) → out.tag = "msub".toList
  ensures (subs = none ∧ sups ≠ none) → out.tag = "msup".toList
  ensures (subs ≠ none ∧ sups ≠ none) → out.tag = "msubsup".toList
  ensures bold = true → out.isBold = true
  do
    -- impl-start
    -- Build the base-name identifier, then choose the representing node directly
    -- from which scripts are present: with no superscripts, either the bare
    -- identifier (no subscripts) or a subscript container; with superscripts,
    -- either a superscript container (no subscripts) or a sub-and-superscript
    -- container. Finally apply bold styling to that representing node.
    let mname : Node := .elem "mi".toList false [Node.text name]
    let core : Node :=
      match sups, subs with
      | none,     none     => mname
      | none,     some sub => .elem "msub".toList false [mname, sub]
      | some sup, none     => .elem "msup".toList false [mname, sup]
      | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
    let x := setBold core bold
    return x
    -- impl-end

prove_correct buildSymbolNode by
  loom_solve <;>
    cases sups <;> cases subs <;>
      simp_all [buildSymbol, mkMi, setBold, Node.tag, Node.isBold]
```

Prepatch bug re-encoded as an attack: `True`.

same_spec (velvet) = True for all 7 attacks + pos (verified via swebench_unified.markers.same_spec).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; run concurrently in 2 batches of 4):
- pos.lean (correct impl = Solution.lean): exit 0 (VERIFIES) — positive control OK.
- atk1_prepatch.lean (prepatch mi-wrapping bug, top tag stays 'mi' for scripted): exit 1 (FAIL) — unsolved goals on msubsup tag clause; spec correctly rejects.
- atk2_partial.lean (partial-domain: always bare mname; correct only for no-script): exit 1 (FAIL).
- atk3_order.lean (boundary: msubsup children swapped to [mname,sup,sub]): exit 1 (FAIL out=buildSymbol).
- atk4_nobold.lean (control-flow-effect: bold application dropped): exit 1 (FAIL bold clause).
- atk6_tagswap.lean (msub<->msup tag swap): exit 1 (FAIL).
- atk5_echo.lean (ungrounded-oracle echo: `return buildSymbol name subs sups bold`): exit 0 (VERIFIES).
- atk7_echovar.lean (echo variant via mkMi + fresh match, value-equal to buildSymbol): exit 0 (VERIFIES).

RESOLVE RUN (mandatory for every verifying attack): both atk5_echo and atk7_echovar compute EXACTLY buildSymbol = the correct gold post-image behavior, so their faithful refined patch is the gold patch (saved gold.patch, obtained from frozen dataset row). Executed run_resolve('sympy__sympy-15976', gold.patch, timeout=1800):
  RESOLVED=True COMPLETED=True NOTE=resolved FLAKY=False.
Both verifying echoes therefore RESOLVE — no verify⇏correct break.

REFINEMENT.MD AUDIT: legs A1–A7 all tagged R or I; no kind-3 (inexpressible-changed-op) legs. mapping.md §3 confirms NO axiomatized callees and NO deep-model references (split_super_sub/join are unchanged infrastructure supplied as inputs). Solution.lean axioms region is an empty comment; buildSymbol is fully concrete Lean with no `axiom`/`sorry`. A-leg correspondence requirement is vacuously satisfied (there are no A legs). The changed operation (which node represents a scripted variable + where the bold attribute lands) is modeled deeply and faithfully in buildSymbol (A5/A6), matching the gold post-image child order (mname, subs, sups) and bold-after-assembly relocation.

CONCLUSION: >=5 distinct wrong impls attempted (7 total); all genuinely-wrong ones fail verification due to the exact-equality postcondition; the only verifying impls are gold-equivalent echoes whose materialized faithful patch was RUN through run_resolve and RESOLVED. verify => correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1_prepatch.lean`, `atk2_partial.lean`, `atk3_order.lean`, `atk4_nobold.lean`, `atk6_tagswap.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk5_echo.lean`, `atk7_echovar.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec's postcondition `ensures out = buildSymbol name subs sups bold` is an EXACT structural equality to the frozen concrete deep model, so any verifying impl must equal buildSymbol value-for-value. Every genuinely-wrong impl fails verification; the only verifying 'wrong' impls are echoes of buildSymbol, which are behaviorally equal to the gold post-image and whose faithful patch (the gold patch) resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_partial.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_order.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_nobold.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk6_tagswap.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_echovar.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the node-assembly routine must COMPLETE (the
-- real routine is straight-line code — a match over which scripts are present
-- plus one attribute write — that always terminates), so the spec must also
-- rule out diverging implementations: under partial correctness a
-- non-terminating body would vacuously satisfy every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model references. The decomposition of a
--  variable's printed name into its base name plus its lists of subscript and
--  superscript pieces, and the rendering of each such list into a single
--  presentation node, are unchanged upstream infrastructure: they are supplied
--  to this routine as the inputs `name`, `subs`, and `sups`. The only behavior
--  modeled here is the per-node decision of how those pieces are assembled into
--  the single node that represents the variable, which is modeled deeply in the
--  `pure` region. There is no `axiom` declaration. See mapping.md / refinement.md.)
-- axioms-end

-- pure-start
/- A presentation-markup node. Either a text node carrying a string value, or an
   element node carrying its tag name, a flag recording whether it bears the
   bold styling attribute, and its ordered children. Only the observables the
   acceptance tests inspect — the top element's tag, its bold flag, and its
   child structure — are represented. -/
inductive Node where
  | text (value : List Char)
  | elem (tag : List Char) (bold : Bool) (children : List Node)
  deriving Inhabited

/- The tag (node name) of a node; the text-node sentinel for text nodes. -/
def Node.tag : Node → List Char
  | .text _      => "#text".toList
  | .elem t _ _  => t

/- Whether a node carries the bold styling attribute (false for a text node). -/
def Node.isBold : Node → Bool
  | .text _      => false
  | .elem _ b _  => b

/- The identifier element wrapping a base name: an `mi` element whose single
   child is the name text. This is how the base name is presented (unchanged
   infrastructure, spelled out here so the assembled node is fully grounded in
   the inputs). -/
def mkMi (name : List Char) : Node :=
  .elem "mi".toList false [Node.text name]

/- Apply the bold styling to a node when requested: set the bold flag on the
   element; requesting no styling leaves the node unchanged. Applied to whichever
   node ends up representing the variable. -/
def setBold : Node → Bool → Node
  | .text v,        _ => .text v
  | .elem t b0 ch,  b => .elem t (b0 || b) ch

/- Assemble the single node that represents a variable, given its base name, its
   subscript node (present iff the variable has subscripts), its superscript node
   (present iff the variable has superscripts), and whether bold styling applies.

   The node that represents the variable is determined directly by which scripts
   are present:
     * no scripts          → the bare base-name identifier;
     * subscripts only      → a subscript container of the base name and the
                              subscript node;
     * superscripts only    → a superscript container of the base name and the
                              superscript node;
     * both                 → a sub-and-superscript container of the base name,
                              the subscript node, then the superscript node.
   Bold styling, when requested, is applied to that representing node itself. -/
def buildSymbol (name : List Char) (subs sups : Option Node) (bold : Bool) : Node :=
  let mname := mkMi name
  let core : Node :=
    match sups, subs with
    | none,     none     => mname
    | none,     some sub => .elem "msub".toList false [mname, sub]
    | some sup, none     => .elem "msup".toList false [mname, sup]
    | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
  setBold core bold

@[simp] lemma setBold_tag (n : Node) (b : Bool) : (setBold n b).tag = n.tag := by
  cases n <;> rfl

/- Applying bold styling to an element node sets its bold flag. (The representing
   node is always an element, so this is the only case the postcondition uses.) -/
@[simp] lemma setBold_elem_isBold (t : List Char) (b0 : Bool) (ch : List Node) :
    (setBold (.elem t b0 ch) true).isBold = true := by
  simp [setBold, Node.isBold]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the single presentation node that represents a printed variable.

   `name` is the variable's base name; `subs` is the subscript node (present iff
   the variable carries subscripts) and `sups` the superscript node (present iff
   it carries superscripts), each already rendered by unchanged infrastructure;
   `bold` requests bold styling. All four are read-only (none is `mut`): the
   routine consults them and produces a fresh node (directive 5).

   The desired behavior: the node the routine returns is the script container
   itself when the variable has scripts — a subscript container when it has only
   subscripts, a superscript container when it has only superscripts, and a
   sub-and-superscript container when it has both; a variable with no scripts is
   presented as the bare base-name identifier. Bold styling applies to that
   returned node. -/
method buildSymbolNode (name : List Char) (subs : Option Node) (sups : Option Node) (bold : Bool) return (out : Node)
  ensures out = buildSymbol name subs sups bold
  ensures (subs = none ∧ sups = none) → out.tag = "mi".toList
  ensures (subs ≠ none ∧ sups = none) → out.tag = "msub".toList
  ensures (subs = none ∧ sups ≠ none) → out.tag = "msup".toList
  ensures (subs ≠ none ∧ sups ≠ none) → out.tag = "msubsup".toList
  ensures bold = true → out.isBold = true
  do
    -- impl-start
    -- Build the base-name identifier, then choose the representing node directly
    -- from which scripts are present: with no superscripts, either the bare
    -- identifier (no subscripts) or a subscript container; with superscripts,
    -- either a superscript container (no subscripts) or a sub-and-superscript
    -- container. Finally apply bold styling to that representing node.
    let mname : Node := .elem "mi".toList false [Node.text name]
    let core : Node :=
      match sups, subs with
      | none,     none     => mname
      | none,     some sub => .elem "msub".toList false [mname, sub]
      | some sup, none     => .elem "msup".toList false [mname, sup]
      | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
    let x := setBold core bold
    return x
    -- impl-end

prove_correct buildSymbolNode by
  loom_solve <;>
    cases sups <;> cases subs <;>
      simp_all [buildSymbol, mkMi, setBold, Node.tag, Node.isBold]
```

Prepatch bug re-encoded as an attack: `True`.

same_spec (velvet) = True for all 7 attacks + pos (verified via swebench_unified.markers.same_spec).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; run concurrently in 2 batches of 4):
- pos.lean (correct impl = Solution.lean): exit 0 (VERIFIES) — positive control OK.
- atk1_prepatch.lean (prepatch mi-wrapping bug, top tag stays 'mi' for scripted): exit 1 (FAIL) — unsolved goals on msubsup tag clause; spec correctly rejects.
- atk2_partial.lean (partial-domain: always bare mname; correct only for no-script): exit 1 (FAIL).
- atk3_order.lean (boundary: msubsup children swapped to [mname,sup,sub]): exit 1 (FAIL out=buildSymbol).
- atk4_nobold.lean (control-flow-effect: bold application dropped): exit 1 (FAIL bold clause).
- atk6_tagswap.lean (msub<->msup tag swap): exit 1 (FAIL).
- atk5_echo.lean (ungrounded-oracle echo: `return buildSymbol name subs sups bold`): exit 0 (VERIFIES).
- atk7_echovar.lean (echo variant via mkMi + fresh match, value-equal to buildSymbol): exit 0 (VERIFIES).

RESOLVE RUN (mandatory for every verifying attack): both atk5_echo and atk7_echovar compute EXACTLY buildSymbol = the correct gold post-image behavior, so their faithful refined patch is the gold patch (saved gold.patch, obtained from frozen dataset row). Executed run_resolve('sympy__sympy-15976', gold.patch, timeout=1800):
  RESOLVED=True COMPLETED=True NOTE=resolved FLAKY=False.
Both verifying echoes therefore RESOLVE — no verify⇏correct break.

REFINEMENT.MD AUDIT: legs A1–A7 all tagged R or I; no kind-3 (inexpressible-changed-op) legs. mapping.md §3 confirms NO axiomatized callees and NO deep-model references (split_super_sub/join are unchanged infrastructure supplied as inputs). Solution.lean axioms region is an empty comment; buildSymbol is fully concrete Lean with no `axiom`/`sorry`. A-leg correspondence requirement is vacuously satisfied (there are no A legs). The changed operation (which node represents a scripted variable + where the bold attribute lands) is modeled deeply and faithfully in buildSymbol (A5/A6), matching the gold post-image child order (mname, subs, sups) and bold-after-assembly relocation.

CONCLUSION: >=5 distinct wrong impls attempted (7 total); all genuinely-wrong ones fail verification due to the exact-equality postcondition; the only verifying impls are gold-equivalent echoes whose materialized faithful patch was RUN through run_resolve and RESOLVED. verify => correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical across twins (markers.same_spec(velvet) = True). Spec models MathMLPresentationPrinter._print_Symbol node assembly over the observable (top tag, bold flag, children). Read the gold-patched real callee at base commit 701441853569: four-arm dispatch sets x = mname/msub/msup/msubsup then applies mathvariant='bold' to x after assembly and returns x — exactly buildSymbol + setBold. Independent differential run of the REAL patched printer over 38 name×style cases (including x__2->msup double-underscore, empty scripts x_/x^, multi-piece x_1_2^3^4, degenerate _2/^2/''/2, bold across every arm) matched the model's top-tag and bold flag on every input; corroborates recorded G-CONF pass (100014 inputs, 0 disagreements). Abstraction boundary honest: script-presence<->Option, style=='bold'<->Bool, script-node internals treated as unmodeled inputs on both sides (unchanged infra: split_super_sub/join). Postconditions are all satisfied by the real function (not over-constrained); bold postcond holds for the bare-mi arm too (verified). total-correctness is a faithful strengthening since the real assembly is straight-line terminating. Solution.lean elaborates cleanly (lean_verify exit 0), so spec is satisfiable, not vacuous. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-verified the relaxed-leakage disposition (not rubber-stamped). Spec region byte-identical between twins: swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet_tables) = True; leakage judged over the shared frozen spec view. Public problem_statement is a pure visual-symptom report ('symbol ending with a number is invisible in MathML', Safari 12, with repro + screenshots) — token scan finds ZERO structural/discriminating vocabulary (mi/msub/msup/msubsup, subscript/superscript, tag, wrap, container, bold, mathvariant, node, child). The spec DOES leak the gold discriminator — the postconditions `ensures (subs≠none ∧ sups=none) → out.tag="msub"` (+ msup/msubsup/mi siblings), the deep buildSymbol dispatch pinning the representing node's top tag, and the docstring describing it — but this is exactly the dispositioned facet (representing-node top tag per script combination + bold placement), documented in RELAXED_LEAKAGE.md with meta.json relaxed_leakage=true and G-LEAK status='relaxed'. Core soundness intact: Solution.lean verifies clean (exit 0); Solution_prepatch.lean fails exactly the three scripted-tag clauses + structural equality (scripted arms reduce to ⊢ False), no-script mi clause survives — G-DIFF sound. Unavoidability re-derived and NOT refuted: the problem_statement's sole observable ('invisible in Safari 12') is a rendering-engine artifact inexpressible over minidom observables; a faithful spec must reject the prepatch (valid markup differing only in top-node shape), so it must pin exactly the tag/shape facts that reveal the fix — faithful+non-leaking is provably impossible, and no problem_statement-only derivation of the msub/msup/msubsup discriminator exists. De-narration applied: spec view does not name the patched file/function, quote diff lines, mention Safari/'invisible', or narrate the pre-patch wrapping bug. Found NO leaking line beyond the dispositioned top-tag/bold facet and no broken disposition. Per G-PANEL-3 policy (defer to accepted RELAXED_LEAKAGE.md; relaxed bundle records pass/NO-LEAKAGE after independent re-confirmation), honest verdict is NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
