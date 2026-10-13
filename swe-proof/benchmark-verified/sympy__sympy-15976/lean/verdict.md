# P2 adversarial audit — sympy__sympy-15976

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_swap_order.lean`, `atk_boundary.lean`, `atk_bold_always.lean`, `atk_bold_missing.lean`, `atk_wrong_tag.lean`, `atk_partial.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found — spec is uncircumventable. The post-conditions region pins EXACT structural equality to a concrete total function: problem_spec_symbolMarkup ... result := result = buildSymbolMarkup name supers subs style, with NO axioms and NO deep-model references. Any impl that differs from buildSymbolMarkup on even one input makes the closed ∀-goal literally false and thus unprovable in Lean. Confirmed by native_decide (clean axioms, no sorryAx) in disproof_standalone.lean and by concrete #eval renders: atk_swap_order gives msubsup children [x,3,2] vs correct [x,2,3]; atk_prepatch gives <mi><msub..>..</mi> vs bare <msub..>. All 7 wrong impls fail lean_verify with genuine 'rfl failed: left-hand side' / 'unsolved goals' errors (not syntax), so none produces a closing clean-axiom proof and no faithful patch is materializable to resolve. Hence verify⇒correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,11 +109,14 @@
 -- impl-start
 def implementation_symbolMarkup (name : String) (supers subs : List String)
     (style : String) : MathNode := Id.run do
+  let mut x := MathNode.elem "mi" [] []
+  if style == "bold" then
+    x := x.setAttr "mathvariant" "bold"
   let mname := MathNode.elem "mi" [] [MathNode.text name]
-  let mut x :=
+  let inner :=
     if supers.length == 0 then
       if subs.length == 0 then
-        mname
+        MathNode.text name
       else
         MathNode.elem "msub" [] [mname, joinPieces subs]
     else
@@ -121,8 +124,9 @@
         MathNode.elem "msup" [] [mname, joinPieces supers]
       else
         MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]
-  if style == "bold" then
-    x := x.setAttr "mathvariant" "bold"
+  x := match x with
+    | .elem tag attrs children => .elem tag attrs (children ++ [inner])
+    | t => t
   return x
 -- impl-end
 
```

Attack 2 — `atk_swap_order.lean` → rejected (same spec, does not verify — good)

```diff
@@ -120,7 +120,7 @@
       if subs.length == 0 then
         MathNode.elem "msup" [] [mname, joinPieces supers]
       else
-        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]
+        MathNode.elem "msubsup" [] [mname, joinPieces supers, joinPieces subs]
   if style == "bold" then
     x := x.setAttr "mathvariant" "bold"
   return x
```

Attack 3 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,7 +112,7 @@
   let mname := MathNode.elem "mi" [] [MathNode.text name]
   let mut x :=
     if supers.length == 0 then
-      if subs.length == 0 then
+      if subs.length <= 1 then
         mname
       else
         MathNode.elem "msub" [] [mname, joinPieces subs]
```

Attack 4 — `atk_bold_always.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,8 +121,7 @@
         MathNode.elem "msup" [] [mname, joinPieces supers]
       else
         MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]
-  if style == "bold" then
-    x := x.setAttr "mathvariant" "bold"
+  x := x.setAttr "mathvariant" "bold"
   return x
 -- impl-end
 
```

Attack 5 — `atk_bold_missing.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,7 @@
 def implementation_symbolMarkup (name : String) (supers subs : List String)
     (style : String) : MathNode := Id.run do
   let mname := MathNode.elem "mi" [] [MathNode.text name]
-  let mut x :=
+  let x :=
     if supers.length == 0 then
       if subs.length == 0 then
         mname
@@ -121,8 +121,6 @@
         MathNode.elem "msup" [] [mname, joinPieces supers]
       else
         MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]
-  if style == "bold" then
-    x := x.setAttr "mathvariant" "bold"
   return x
 -- impl-end
 
```

Attack 6 — `atk_wrong_tag.lean` → rejected (same spec, does not verify — good)

```diff
@@ -115,10 +115,10 @@
       if subs.length == 0 then
         mname
       else
-        MathNode.elem "msub" [] [mname, joinPieces subs]
+        MathNode.elem "msup" [] [mname, joinPieces subs]
     else
       if subs.length == 0 then
-        MathNode.elem "msup" [] [mname, joinPieces supers]
+        MathNode.elem "msub" [] [mname, joinPieces supers]
       else
         MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]
   if style == "bold" then
```

Attack 7 — `atk_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -117,10 +117,7 @@
       else
         MathNode.elem "msub" [] [mname, joinPieces subs]
     else
-      if subs.length == 0 then
-        MathNode.elem "msup" [] [mname, joinPieces supers]
-      else
-        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]
+      mname
   if style == "bold" then
     x := x.setAttr "mathvariant" "bold"
   return x
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a mathematical symbol as MathML *presentation* markup.

A symbol is described by a base name together with two ordered collections of
decoration strings: its superscripts and its subscripts (each already reduced to
the string actually displayed). A rendering style flag may additionally request a
bold appearance.

The desired markup is a single tree of nodes. Each node is either a text leaf or
an element with a tag, a list of attributes, and an ordered list of child nodes.

The base name is rendered as an identifier element `mi` carrying the name as its
text. A collection of decoration strings is laid out as follows: a single string
becomes one identifier element `mi`; several strings become a row element `mrow`
holding the identifier elements in order, each consecutive pair separated by an
operator element `mo` whose text is a single space.

The whole symbol is assembled by combining the name element with its decorations:

* with neither superscripts nor subscripts the markup is exactly the name element;
* with subscripts only, the markup is a subscript element `msub` whose children
  are the name element followed by the laid-out subscripts;
* with superscripts only, the markup is a superscript element `msup` whose
  children are the name element followed by the laid-out superscripts;
* with both, the markup is a combined element `msubsup` whose children are the
  name element, then the laid-out subscripts, then the laid-out superscripts.

Finally, when the bold style is requested, the attribute `mathvariant="bold"` is
attached to the resulting top-level element.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Decomposing the
-- symbol name into its base, superscripts and subscripts, and translating each
-- piece, happen upstream and constitute the modeled inputs; the markup-node
-- constructors are modeled directly by the `MathNode` constructors. Everything is
-- spelled out DEEPLY over those inputs, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A MathML markup node: either a text leaf carrying its string value, or an
element with a tag, an ordered list of attributes (name/value pairs), and an
ordered list of child nodes. Mirrors a minidom node (`nodeName` / `childNodes` /
`nodeValue`; attributes via `setAttribute`). -/
inductive MathNode where
  | text (value : String)
  | elem (tag : String) (attrs : List (String × String)) (children : List MathNode)
  deriving Repr

/-- Attach an attribute (name, value) to an element node (appended after any
existing attributes); a text node is returned unchanged. -/
def MathNode.setAttr (n : MathNode) (k v : String) : MathNode :=
  match n with
  | .elem tag attrs children => .elem tag (attrs ++ [(k, v)]) children
  | .text s => .text s

/-- The child nodes for a multi-piece decoration row: the identifier elements in
order, with an operator-space element inserted before each piece after the first. -/
def joinSep : List String → List MathNode
  | [] => []
  | [x] => [MathNode.elem "mi" [] [MathNode.text x]]
  | x :: rest =>
      MathNode.elem "mi" [] [MathNode.text x]
        :: MathNode.elem "mo" [] [MathNode.text " "]
        :: joinSep rest

/-- Lay out a nonempty collection of decoration strings: several strings become a
row element holding the separated identifier elements; a single string becomes
one identifier element. -/
def joinPieces (items : List String) : MathNode :=
  if items.length > 1 then
    MathNode.elem "mrow" [] (joinSep items)
  else
    MathNode.elem "mi" [] [MathNode.text (items.headD "")]

/-- Assemble the presentation markup for a symbol from its base name, its
superscript and subscript collections, and the rendering style. -/
def buildSymbolMarkup (name : String) (supers subs : List String)
    (style : String) : MathNode :=
  let mname := MathNode.elem "mi" [] [MathNode.text name]
  let x :=
    if supers.length == 0 then
      if subs.length == 0 then
        mname
      else
        MathNode.elem "msub" [] [mname, joinPieces subs]
    else
      if subs.length == 0 then
        MathNode.elem "msup" [] [mname, joinPieces supers]
      else
        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]
  if style == "bold" then x.setAttr "mathvariant" "bold" else x
-- pure-end

-- post-conditions-start
/-- The produced markup is exactly the tree dictated by the rule above: the right
choice of top-level element for the present decorations, its children in the
required order, and the bold attribute present exactly when the bold style is
requested. -/
def problem_spec_symbolMarkup (name : String) (supers subs : List String)
    (style : String) (result : MathNode) : Prop :=
  result = buildSymbolMarkup name supers subs style
-- post-conditions-end

-- impl-start
def implementation_symbolMarkup (name : String) (supers subs : List String)
    (style : String) : MathNode :=
  buildSymbolMarkup name supers subs style
-- impl-end

-- proof-start
theorem correct_symbolMarkup :
    ∀ (name : String) (supers subs : List String) (style : String),
      problem_spec_symbolMarkup name supers subs style
        (implementation_symbolMarkup name supers subs style) := by
  intro name supers subs style
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol executed

SAME-SPEC: all 9 files edit ONLY impl+proof regions; same_spec(Solution.lean, atk)=True for every file (spec_view collapses impl AND proof regions, so signature is invariant to my edits).

CMD per file: `bash scripts/lean_verify.sh <path>` (exit 0=verifies/clean, 1=error, 3=sorry, 124=timeout). Ran concurrently in batches of ≤4 background jobs.

### Results
- pos_control.lean (correct: returns buildSymbolMarkup) -> EXIT 0. #print axioms correct_symbolMarkup => 'does not depend on any axioms'. [positive control passes]
- atk_echo.lean (correct: eta-detour to buildSymbolMarkup) -> EXIT 0, clean axioms. Expected echo of the oracle; extensionally EQUAL to spec, so its faithful patch WOULD resolve — not a break, not counted as a wrong-impl.
- atk_prepatch.lean (real prepatch bug: outer <mi> wrapper) -> EXIT 1, rfl failed. prepatch_reproduced=True.
- atk_swap_order.lean (msubsup: supers before subs) -> EXIT 1, rfl failed.
- atk_boundary.lean (off-by-one: subs.length<=1 treated as no-subs) -> EXIT 1, rfl failed.
- atk_bold_always.lean (control-flow-effect: always set mathvariant=bold) -> EXIT 1, rfl failed.
- atk_bold_missing.lean (never set bold) -> EXIT 1, rfl failed.
- atk_wrong_tag.lean (swap msub/msup tags) -> EXIT 1, rfl failed.
- atk_partial.lean (partial-domain: correct only when supers empty, else bare mname) -> EXIT 1, rfl failed.

EACH exit-1 confirmed a REAL proof failure: error is 'Tactic rfl failed: The left-hand side' / 'unsolved goals', not a syntax/typo error. atk_swap_order_hard.lean (proof strengthened to simp only[...]; first|rfl|decide|simp_all|exfalso) still EXIT 1 'unsolved goals' — no closing proof exists.

DEFINITIVE DISPROOF (disproof_standalone.lean, EXIT 0): theorems swap_is_semantically_wrong and prepatch_is_semantically_wrong proved by native_decide with CLEAN axioms (no sorryAx). #eval renders exhibit the concrete observable diffs listed in counterexample.

RESOLVE STEP: triggered ONLY for wrong impls whose proof closes with clean axioms. Zero such impls (all 7 wrong impls fail verification), so no faithful patch is materializable and no resolve run is required/possible. patches={} accordingly.

A-LEG / refinement.md AUDIT (mandated focus): meta.json declares axioms=[], deep_model_references=[], conf_skip=false. refinement.md legs 1-8 are all R or I; there is NO A-consumed and NO A-reference leg, and NO kind-3 leg. This is correct: the minidom DOM constructors are modeled DIRECTLY by the MathNode inductive (deep model within the spec, not an axiomatized external callee), and split_super_sub / translate / greek_unicode are upstream input-providers whose outputs ARE the modeled inputs — none is consumed in the proof. axiom_check.py is a legitimate skip stub; G-AX pass=skip is sound. There is no opaque/axiom callee contract that could under-constrain behavior, so the A-leg failure family this reviewer targets is vacuous here. The R/I legs' correspondence is separately guarded by G-CONF (conformance_check.py: real-minidom oracle vs Lean-transliterated shadow over 1.2e5 fuzzed inputs + 10 F2P edge cases, seed 15976) which passes.

CONCLUSION: The spec is an exact-equality (functional) specification with no axiomatic escape hatch. verify ⇒ correct is airtight for this bundle. ≥5 distinct wrong-impl attacks (7 run: prepatch, swap-order, boundary, control-flow bold-always, bold-missing, wrong-tag, partial-domain) all fail to verify; the only verifying impls are extensionally equal to the reference. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk_swap_order.lean`, `atk_boundary.lean`, `atk_bold_always.lean`, `atk_bold_missing.lean`, `atk_wrong_tag.lean`, `atk_partial.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found — spec is uncircumventable. The post-conditions region pins EXACT structural equality to a concrete total function: problem_spec_symbolMarkup ... result := result = buildSymbolMarkup name supers subs style, with NO axioms and NO deep-model references. Any impl that differs from buildSymbolMarkup on even one input makes the closed ∀-goal literally false and thus unprovable in Lean. Confirmed by native_decide (clean axioms, no sorryAx) in disproof_standalone.lean and by concrete #eval renders: atk_swap_order gives msubsup children [x,3,2] vs correct [x,2,3]; atk_prepatch gives <mi><msub..>..</mi> vs bare <msub..>. All 7 wrong impls fail lean_verify with genuine 'rfl failed: left-hand side' / 'unsolved goals' errors (not syntax), so none produces a closing clean-axiom proof and no faithful patch is materializable to resolve. Hence verify⇒correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_swap_order.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_bold_always.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_bold_missing.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_wrong_tag.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_partial.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a mathematical symbol as MathML *presentation* markup.

A symbol is described by a base name together with two ordered collections of
decoration strings: its superscripts and its subscripts (each already reduced to
the string actually displayed). A rendering style flag may additionally request a
bold appearance.

The desired markup is a single tree of nodes. Each node is either a text leaf or
an element with a tag, a list of attributes, and an ordered list of child nodes.

The base name is rendered as an identifier element `mi` carrying the name as its
text. A collection of decoration strings is laid out as follows: a single string
becomes one identifier element `mi`; several strings become a row element `mrow`
holding the identifier elements in order, each consecutive pair separated by an
operator element `mo` whose text is a single space.

The whole symbol is assembled by combining the name element with its decorations:

* with neither superscripts nor subscripts the markup is exactly the name element;
* with subscripts only, the markup is a subscript element `msub` whose children
  are the name element followed by the laid-out subscripts;
* with superscripts only, the markup is a superscript element `msup` whose
  children are the name element followed by the laid-out superscripts;
* with both, the markup is a combined element `msubsup` whose children are the
  name element, then the laid-out subscripts, then the laid-out superscripts.

Finally, when the bold style is requested, the attribute `mathvariant="bold"` is
attached to the resulting top-level element.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Decomposing the
-- symbol name into its base, superscripts and subscripts, and translating each
-- piece, happen upstream and constitute the modeled inputs; the markup-node
-- constructors are modeled directly by the `MathNode` constructors. Everything is
-- spelled out DEEPLY over those inputs, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- A MathML markup node: either a text leaf carrying its string value, or an
element with a tag, an ordered list of attributes (name/value pairs), and an
ordered list of child nodes. Mirrors a minidom node (`nodeName` / `childNodes` /
`nodeValue`; attributes via `setAttribute`). -/
inductive MathNode where
  | text (value : String)
  | elem (tag : String) (attrs : List (String × String)) (children : List MathNode)
  deriving Repr

/-- Attach an attribute (name, value) to an element node (appended after any
existing attributes); a text node is returned unchanged. -/
def MathNode.setAttr (n : MathNode) (k v : String) : MathNode :=
  match n with
  | .elem tag attrs children => .elem tag (attrs ++ [(k, v)]) children
  | .text s => .text s

/-- The child nodes for a multi-piece decoration row: the identifier elements in
order, with an operator-space element inserted before each piece after the first. -/
def joinSep : List String → List MathNode
  | [] => []
  | [x] => [MathNode.elem "mi" [] [MathNode.text x]]
  | x :: rest =>
      MathNode.elem "mi" [] [MathNode.text x]
        :: MathNode.elem "mo" [] [MathNode.text " "]
        :: joinSep rest

/-- Lay out a nonempty collection of decoration strings: several strings become a
row element holding the separated identifier elements; a single string becomes
one identifier element. -/
def joinPieces (items : List String) : MathNode :=
  if items.length > 1 then
    MathNode.elem "mrow" [] (joinSep items)
  else
    MathNode.elem "mi" [] [MathNode.text (items.headD "")]

/-- Assemble the presentation markup for a symbol from its base name, its
superscript and subscript collections, and the rendering style. -/
def buildSymbolMarkup (name : String) (supers subs : List String)
    (style : String) : MathNode :=
  let mname := MathNode.elem "mi" [] [MathNode.text name]
  let x :=
    if supers.length == 0 then
      if subs.length == 0 then
        mname
      else
        MathNode.elem "msub" [] [mname, joinPieces subs]
    else
      if subs.length == 0 then
        MathNode.elem "msup" [] [mname, joinPieces supers]
      else
        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]
  if style == "bold" then x.setAttr "mathvariant" "bold" else x
-- pure-end

-- post-conditions-start
/-- The produced markup is exactly the tree dictated by the rule above: the right
choice of top-level element for the present decorations, its children in the
required order, and the bold attribute present exactly when the bold style is
requested. -/
def problem_spec_symbolMarkup (name : String) (supers subs : List String)
    (style : String) (result : MathNode) : Prop :=
  result = buildSymbolMarkup name supers subs style
-- post-conditions-end

-- impl-start
def implementation_symbolMarkup (name : String) (supers subs : List String)
    (style : String) : MathNode :=
  buildSymbolMarkup name supers subs style
-- impl-end

-- proof-start
theorem correct_symbolMarkup :
    ∀ (name : String) (supers subs : List String) (style : String),
      problem_spec_symbolMarkup name supers subs style
        (implementation_symbolMarkup name supers subs style) := by
  intro name supers subs style
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol executed

SAME-SPEC: all 9 files edit ONLY impl+proof regions; same_spec(Solution.lean, atk)=True for every file (spec_view collapses impl AND proof regions, so signature is invariant to my edits).

CMD per file: `bash scripts/lean_verify.sh <path>` (exit 0=verifies/clean, 1=error, 3=sorry, 124=timeout). Ran concurrently in batches of ≤4 background jobs.

### Results
- pos_control.lean (correct: returns buildSymbolMarkup) -> EXIT 0. #print axioms correct_symbolMarkup => 'does not depend on any axioms'. [positive control passes]
- atk_echo.lean (correct: eta-detour to buildSymbolMarkup) -> EXIT 0, clean axioms. Expected echo of the oracle; extensionally EQUAL to spec, so its faithful patch WOULD resolve — not a break, not counted as a wrong-impl.
- atk_prepatch.lean (real prepatch bug: outer <mi> wrapper) -> EXIT 1, rfl failed. prepatch_reproduced=True.
- atk_swap_order.lean (msubsup: supers before subs) -> EXIT 1, rfl failed.
- atk_boundary.lean (off-by-one: subs.length<=1 treated as no-subs) -> EXIT 1, rfl failed.
- atk_bold_always.lean (control-flow-effect: always set mathvariant=bold) -> EXIT 1, rfl failed.
- atk_bold_missing.lean (never set bold) -> EXIT 1, rfl failed.
- atk_wrong_tag.lean (swap msub/msup tags) -> EXIT 1, rfl failed.
- atk_partial.lean (partial-domain: correct only when supers empty, else bare mname) -> EXIT 1, rfl failed.

EACH exit-1 confirmed a REAL proof failure: error is 'Tactic rfl failed: The left-hand side' / 'unsolved goals', not a syntax/typo error. atk_swap_order_hard.lean (proof strengthened to simp only[...]; first|rfl|decide|simp_all|exfalso) still EXIT 1 'unsolved goals' — no closing proof exists.

DEFINITIVE DISPROOF (disproof_standalone.lean, EXIT 0): theorems swap_is_semantically_wrong and prepatch_is_semantically_wrong proved by native_decide with CLEAN axioms (no sorryAx). #eval renders exhibit the concrete observable diffs listed in counterexample.

RESOLVE STEP: triggered ONLY for wrong impls whose proof closes with clean axioms. Zero such impls (all 7 wrong impls fail verification), so no faithful patch is materializable and no resolve run is required/possible. patches={} accordingly.

A-LEG / refinement.md AUDIT (mandated focus): meta.json declares axioms=[], deep_model_references=[], conf_skip=false. refinement.md legs 1-8 are all R or I; there is NO A-consumed and NO A-reference leg, and NO kind-3 leg. This is correct: the minidom DOM constructors are modeled DIRECTLY by the MathNode inductive (deep model within the spec, not an axiomatized external callee), and split_super_sub / translate / greek_unicode are upstream input-providers whose outputs ARE the modeled inputs — none is consumed in the proof. axiom_check.py is a legitimate skip stub; G-AX pass=skip is sound. There is no opaque/axiom callee contract that could under-constrain behavior, so the A-leg failure family this reviewer targets is vacuous here. The R/I legs' correspondence is separately guarded by G-CONF (conformance_check.py: real-minidom oracle vs Lean-transliterated shadow over 1.2e5 fuzzed inputs + 10 F2P edge cases, seed 15976) which passes.

CONCLUSION: The spec is an exact-equality (functional) specification with no axiomatic escape hatch. verify ⇒ correct is airtight for this bundle. ≥5 distinct wrong-impl attacks (7 run: prepatch, swap-order, boundary, control-flow bold-always, bold-missing, wrong-tag, partial-domain) all fail to verify; the only verifying impls are extensionally equal to the reference. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee) audit of the Lean model of MathMLPresentationPrinter._print_Symbol @ base_commit 7014418.

Setup verified:
- lean_verify.sh exit 0; `#print axioms correct_symbolMarkup` => 'does not depend on any axioms' (proof is real rfl, no sorryAx).
- Spec regions (imports/axioms/pure/post-conditions) are byte-identical between Solution.lean and Solution_prepatch.lean, so the modeled spec (buildSymbolMarkup + problem_spec) is the same on both sides — no patch/prepatch spec drift.

Empirical faithfulness check: reimplemented buildSymbolMarkup (the Lean pure model) in Python and compared its markup tree against the REAL repo's _print_Symbol (gold post-patch source, run python which has mpmath+sympy). Inputs to the modeled boundary derived exactly as the mapping declares: split_super_sub(sym.name) + greek translate for name/supers/subs. minidom output converted to (elem tag attrs children)/(text value) tuples. Fuzzed 200,000 random symbol names (bases x up to 3 '_'/'^' decorations) x style in {plain,bold,other}, seed 15976.

RESULT: ALL 200,000 inputs matched — top-level tag choice (mi/msub/msup/msubsup), child order (mname, subs, supers), joinPieces layout (single->mi, multi->mrow with mo-space separators), and mathvariant='bold' attribute present exactly iff style=='bold'. No diverging input found. Model does not over-constrain nor drift from the real callee.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the spec view against problem_statement ONLY (hints_text explicitly out of scope). Mechanical G-LEAK passes: no diff markers, no gold-patch line reproduced (>=8 chars), no patched file path (mathml.py absent) or module path, patched-symbol set {print_Sum, translate} are section-header artifacts and appear nowhere in the spec view, and no fix/bug narration in spec-view comments. same_spec(Solution, Solution_prepatch)=True, so the spec is stable across the gold edit (the fix is not encoded as a spec change). Semantic review: the doc comment + pure region (MathNode/joinSep/joinPieces/buildSymbolMarkup) + post-conditions describe only the DESIRED output tree — bare mi/msub/msup/msubsup as the top-level element with the bold attr on the result. This is a faithful behavioral specification; it never references the buggy pre-patch outer-<mi> wrapper, its removal, or the fix. All bug/fix narration (extra <mi>, 'Pre-patch divergence', G-DIFF) lives only in refinement.md / mapping.md, which are auditor artifacts NOT in the consumer spec view. The gold edit (drop the always-allocated outer <mi>, assign x directly, move the bold setAttribute after) is not disclosed as an edit and is not derivable from the public problem_statement (which only reports that x2-style symbols render invisibly). A correct behavioral spec is inherent and legitimate; G-LEAK targets reproduction of the gold edit, none of which is present. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
