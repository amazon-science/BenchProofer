# P2 adversarial audit — sphinx-doc__sphinx-9602

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1.lean`, `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- An inline documentation node. A rendered type annotation is a sequence of
    these. Only the fields the rendered signature observes are kept: `text`
@@ -105,19 +105,8 @@
   ensures out = expandLiteral head values
   do
     -- impl-start
-    -- The head renders as a navigable cross-reference; the bracketed argument
-    -- list is built by `valSeq`, where each constant value becomes a PLAIN
-    -- display-text node carrying its source representation (`reprVal`). Because
-    -- the value nodes are plain text — not cross-references — a constant such as
-    -- a boolean or integer carries no class reference. (Pre-image skeleton routed
-    -- the same constants through the cross-reference path, so each value became
-    -- a navigable reference; the frozen spec requires plain text, so that
-    -- pre-image fails prove_correct.)
-    let inner := valSeq DocNode.text reprVal values
-    let result := wrap head inner
-    return result
+    return expandLiteral head values
     -- impl-end
 
 prove_correct literalTypeNodes by
   loom_solve
-  rfl
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 /- An inline documentation node. A rendered type annotation is a sequence of
    these. Only the fields the rendered signature observes are kept: `text`
@@ -105,17 +105,8 @@
   ensures out = expandLiteral head values
   do
     -- impl-start
-    -- The head renders as a navigable cross-reference; the bracketed argument
-    -- list is built by `valSeq`, where each constant value becomes a PLAIN
-    -- display-text node carrying its source representation (`reprVal`). Because
-    -- the value nodes are plain text — not cross-references — a constant such as
-    -- a boolean or integer carries no class reference. (Pre-image skeleton routed
-    -- the same constants through the cross-reference path, so each value became
-    -- a navigable reference; the frozen spec requires plain text, so that
-    -- pre-image fails prove_correct.)
     let inner := valSeq DocNode.text reprVal values
-    let result := wrap head inner
-    return result
+    return wrap head inner
     -- impl-end
 
 prove_correct literalTypeNodes by
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
 
 /- An inline documentation node. A rendered type annotation is a sequence of
    these. Only the fields the rendered signature observes are kept: `text`
@@ -105,17 +105,14 @@
   ensures out = expandLiteral head values
   do
     -- impl-start
-    -- The head renders as a navigable cross-reference; the bracketed argument
-    -- list is built by `valSeq`, where each constant value becomes a PLAIN
-    -- display-text node carrying its source representation (`reprVal`). Because
-    -- the value nodes are plain text — not cross-references — a constant such as
-    -- a boolean or integer carries no class reference. (Pre-image skeleton routed
-    -- the same constants through the cross-reference path, so each value became
-    -- a navigable reference; the frozen spec requires plain text, so that
-    -- pre-image fails prove_correct.)
-    let inner := valSeq DocNode.text reprVal values
-    let result := wrap head inner
-    return result
+    let rawRender : LitVal → List Char := fun v =>
+      match v with
+      | .bool true  => "True".toList
+      | .bool false => "False".toList
+      | .int n      => (toString n).toList
+      | .str s      => s
+    let inner := valSeq DocNode.text rawRender values
+    return wrap head inner
     -- impl-end
 
 prove_correct literalTypeNodes by
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
 
 /- An inline documentation node. A rendered type annotation is a sequence of
    these. Only the fields the rendered signature observes are kept: `text`
@@ -105,17 +105,8 @@
   ensures out = expandLiteral head values
   do
     -- impl-start
-    -- The head renders as a navigable cross-reference; the bracketed argument
-    -- list is built by `valSeq`, where each constant value becomes a PLAIN
-    -- display-text node carrying its source representation (`reprVal`). Because
-    -- the value nodes are plain text — not cross-references — a constant such as
-    -- a boolean or integer carries no class reference. (Pre-image skeleton routed
-    -- the same constants through the cross-reference path, so each value became
-    -- a navigable reference; the frozen spec requires plain text, so that
-    -- pre-image fails prove_correct.)
-    let inner := valSeq DocNode.text reprVal values
-    let result := wrap head inner
-    return result
+    let inner := valSeq DocNode.xref reprVal values
+    return wrap head inner
     -- impl-end
 
 prove_correct literalTypeNodes by
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
 
 /- An inline documentation node. A rendered type annotation is a sequence of
    these. Only the fields the rendered signature observes are kept: `text`
@@ -105,17 +105,9 @@
   ensures out = expandLiteral head values
   do
     -- impl-start
-    -- The head renders as a navigable cross-reference; the bracketed argument
-    -- list is built by `valSeq`, where each constant value becomes a PLAIN
-    -- display-text node carrying its source representation (`reprVal`). Because
-    -- the value nodes are plain text — not cross-references — a constant such as
-    -- a boolean or integer carries no class reference. (Pre-image skeleton routed
-    -- the same constants through the cross-reference path, so each value became
-    -- a navigable reference; the frozen spec requires plain text, so that
-    -- pre-image fails prove_correct.)
-    let inner := valSeq DocNode.text reprVal values
-    let result := wrap head inner
-    return result
+    -- Partial-domain: only emits the first value's node, ignoring the rest.
+    let inner := [DocNode.text (reprVal values.head!)]
+    return wrap head inner
     -- impl-end
 
 prove_correct literalTypeNodes by
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
 
 /- An inline documentation node. A rendered type annotation is a sequence of
    these. Only the fields the rendered signature observes are kept: `text`
@@ -105,17 +105,11 @@
   ensures out = expandLiteral head values
   do
     -- impl-start
-    -- The head renders as a navigable cross-reference; the bracketed argument
-    -- list is built by `valSeq`, where each constant value becomes a PLAIN
-    -- display-text node carrying its source representation (`reprVal`). Because
-    -- the value nodes are plain text — not cross-references — a constant such as
-    -- a boolean or integer carries no class reference. (Pre-image skeleton routed
-    -- the same constants through the cross-reference path, so each value became
-    -- a navigable reference; the frozen spec requires plain text, so that
-    -- pre-image fails prove_correct.)
-    let inner := valSeq DocNode.text reprVal values
-    let result := wrap head inner
-    return result
+    -- Wrong separator punctuation (", " -> ",") — boundary attack.
+    let bad : List Char → DocNode := DocNode.text
+    let inner := valSeq bad reprVal values
+    -- reuse valSeq but wrap with a wrong closing bracket
+    return DocNode.xref head :: DocNode.punct "[".toList :: (inner ++ [DocNode.punct ")".toList])
     -- impl-end
 
 prove_correct literalTypeNodes by
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
 
 /- An inline documentation node. A rendered type annotation is a sequence of
    these. Only the fields the rendered signature observes are kept: `text`
@@ -105,19 +105,12 @@
   ensures out = expandLiteral head values
   do
     -- impl-start
-    -- The head renders as a navigable cross-reference; the bracketed argument
-    -- list is built by `valSeq`, where each constant value becomes a PLAIN
-    -- display-text node carrying its source representation (`reprVal`). Because
-    -- the value nodes are plain text — not cross-references — a constant such as
-    -- a boolean or integer carries no class reference. (Pre-image skeleton routed
-    -- the same constants through the cross-reference path, so each value became
-    -- a navigable reference; the frozen spec requires plain text, so that
-    -- pre-image fails prove_correct.)
-    let inner := valSeq DocNode.text reprVal values
-    let result := wrap head inner
-    return result
+    -- Control-flow-effect: diverge (partial correctness => postcondition vacuous).
+    let mut x := 0
+    while true do
+      x := x + 1
+    return expandLiteral head values
     -- impl-end
 
 prove_correct literalTypeNodes by
   loom_solve
-  rfl
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- An inline documentation node. A rendered type annotation is a sequence of
   these. Only the fields the rendered signature observes are kept: `text`
   carries literal display text, `xref` carries a cross-reference whose target
   is a type name (a navigable class reference), `punct` carries structural
   punctuation (brackets, commas). The bijection to the real inline-node
   carriers is in mapping.md §2. -/
inductive DocNode where
  | text  (s : List Char)
  | xref  (target : List Char)
  | punct (s : List Char)
  deriving DecidableEq, Inhabited, Repr

/- A constant value that can appear inside a parametrised type. Three shapes are
   modeled — a boolean, an integer, and a (simple) string literal — covering the
   constant kinds the documented annotations in scope use. The bijection to the
   real Python constant objects is in mapping.md §2. -/
inductive LitVal where
  | bool (b : Bool)
  | int  (n : Int)
  | str  (s : List Char)
  deriving DecidableEq, Inhabited, Repr

-- axioms-start
-- (No consumed axiom: the rendering of a parametrised type is modeled deeply —
--  see the `pure` region.)
-- axioms-end

-- pure-start
/- The domain on which the string representation below is exact: a "simple"
   string is one whose characters are all printable ASCII (32–126) other than
   the apostrophe and the backslash. Such a string is shown delimited by single
   quotes with no character needing an escape. Constant strings outside this
   domain (containing quotes, backslashes, or non-printable code points) are out
   of scope and excluded by the method precondition. -/
def isSimpleStrChar (c : Char) : Bool :=
  decide (32 ≤ c.toNat ∧ c.toNat ≤ 126) && c ≠ '\'' && c ≠ '\\'

def okLit : LitVal → Bool
  | .str s => s.all isSimpleStrChar
  | .int n => decide (0 ≤ n)
  | _      => true

/- The display text of one constant value: its canonical source representation.
   A boolean shows as `True`/`False`, an integer as its decimal digits, and a
   simple string as its single-quoted form (the surrounding quotes ARE part of
   the displayed text — a string constant is shown with delimiters so it reads
   unambiguously). Validated against the real value-representation routine over
   this domain by axiom_check.py (G-AX); provenance mapping.md §3.1. -/
def reprVal : LitVal → List Char
  | .bool true  => "True".toList
  | .bool false => "False".toList
  | .int n      => (toString n).toList
  | .str s      => '\'' :: (s ++ ['\''])

/- The node sequence for a comma-separated list of constant values: each value
   becomes one node built by `mk` from its display text `render v`, and adjacent
   values are separated by a `", "` punctuation node. Front-recursive so a single
   unfold is available per step. Parametrised over the node constructor `mk` and
   the per-value renderer `render` so the value-display policy is explicit at the
   call site. -/
def valSeq (mk : List Char → DocNode) (render : LitVal → List Char) :
    List LitVal → List DocNode
  | []      => []
  | [v]     => [mk (render v)]
  | v :: vs => mk (render v) :: DocNode.punct ", ".toList :: valSeq mk render vs

/- Frame the inner sequence with the head cross-reference and the surrounding
   brackets: `head` renders as a navigable cross-reference (the parametrised
   type itself), then `[`, then the inner nodes, then `]`. -/
def wrap (head : List Char) (inner : List DocNode) : List DocNode :=
  DocNode.xref head :: DocNode.punct "[".toList :: (inner ++ [DocNode.punct "]".toList])

/- Deep model (A-reference) of rendering a parametrised type whose arguments are
   constant values, on the domain this signature uses. The head is a navigable
   cross-reference; each constant argument is shown as PLAIN DISPLAY TEXT (its
   `reprVal`), NOT as a cross-reference — a constant value is not a class, so it
   carries no navigable reference. Validated == the real renderer over this
   domain by axiom_check.py (G-AX); provenance mapping.md §3.1. -/
def expandLiteral (head : List Char) (values : List LitVal) : List DocNode :=
  wrap head (valSeq DocNode.text reprVal values)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

method literalTypeNodes (head : List Char) (values : List LitVal)
    return (out : List DocNode)
  require head = "Literal".toList ∨ head = "typing.Literal".toList
  require values ≠ []
  require values.all okLit
  ensures out = expandLiteral head values
  do
    -- impl-start
    let inner := valSeq DocNode.text reprVal values
    let result := wrap head inner
    return result
    -- impl-end

prove_correct literalTypeNodes by
  loom_solve
  rfl
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition `ensures out = expandLiteral head values` FULLY PINS the output to the fully-concrete deep model expandLiteral/wrap/valSeq/reprVal (no axiom/opaque/:|/sorry). So any verifying impl must return exactly expandLiteral head values; a semantically-wrong impl cannot verify. Break-surface is therefore (a) deep-model faithfulness and (b) whether the sole verifying class ('echo' the RHS) has a faithful patch that resolves.

same_spec=True confirmed for all 8 files (velvet backend, byte-identical axioms/pure/pre/post).

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>):
- atk_1 (echo: `return expandLiteral head values`) -> exit 0 VERIFIES. Correct; = gold.
- atk_2 (one-level unfold: `wrap head (valSeq DocNode.text reprVal values)`) -> exit 0 VERIFIES. Correct; = gold.
- atk_3 (prepatch bug 1: str rendered RAW, no quotes) -> exit 1 REJECTED on `... != expandLiteral head values`.
- atk_4 (prepatch bug 2: values via DocNode.xref not .text) -> exit 1 REJECTED on `valSeq DocNode.xref reprVal values ... != expandLiteral`.
- atk_5 (partial-domain: emits only first value, drops rest) -> exit 1 REJECTED on `wrap head [DocNode.text (reprVal values.head!)] != expandLiteral`.
- atk_6 (boundary: wrong closing bracket ')' instead of ']') -> exit 1 REJECTED on `... punct ')' ... != expandLiteral`.
- atk_7 (control-flow-effect: `while true do ...` divergence) -> exit 0 VERIFIES (vacuously, under global loom.semantics.termination "partial").
- atk_pc (positive control = frozen impl) -> exit 0 VERIFIES.
Note: atk_1 and atk_7 initially exited 1 ONLY due to the trailing `rfl` after `loom_solve` in the (non-spec) proof block giving 'No goals to be solved'; removing the redundant rfl (proof script is outside the spec view; same_spec stays True) makes both verify. This is a proof-tactic artifact, not a semantic rejection.

RESOLVE RUN (mandatory, for the verifying impls atk_1/atk_2/atk_7): all three produce exactly the gold node sequence `expandLiteral head values`, so their FAITHFUL refined patch is the gold patch (verbatim, faithful_patch.diff = gold9602.patch). Ran through the official harness: swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9602', gold, timeout=1800) -> RESOLVED=True COMPLETED=True attempts=1 flaky=False. The verifying impls' faithful patch RESOLVES.

atk_7 divergence disposition: verifying-but-diverging is a universal artifact of the global partial-correctness setting, NOT a refinement-fidelity defect of THIS spec. The `while true` loop has no corresponding operation in patch.diff; a FAITHFUL refinement drops the non-corresponding infinite loop, leaving `return expandLiteral head values` = the gold patch, which resolves. It does not exhibit a verifying impl whose faithful patch fails to resolve.

DEEP-MODEL FAITHFULNESS (independent probe, faith_probe.py, run against the gold-patched real _parse_annotation): compared node-for-node (class, astext) vs the expandLiteral shadow on the two F2P rows + 4 variants (Literal[True,False]; typing.Literal[0,1,'abc'] with 'abc' single-quoted; Literal['x y z',7,False]; typing.Literal['a']; Literal[255]; Literal['']) -> BAD=0, all MATCH. This confirms expandLiteral == patched callee on the modeled domain, incl. the dotted head 'typing.Literal' and the single-quoted string repr.

REFINEMENT.MD AUDIT: 5 legs, all R / I / A-reference; NO kind-3 (no inexpressible-changed-op, no axiom about the changed function). A-references hold: (3.1) reprVal == builtin repr on bool/int/simple-str (G-AX, unchanged callee, base_commit); (3.2) head type_to_xref carrier -> pending_xref text/reftarget == head (G-AX); (3.3) whole-function expandLiteral == patched _parse_annotation (G-CONF 1e5 inputs seed 9602, and my independent probe, 0 disagreements). The genuinely-changed ops (repr-rendering, literal-text-vs-xref routing) are modeled DEEPLY in the concrete pure region, not hidden behind an axiom.

No verifying wrong impl has a faithful patch that fails to resolve; 5+ distinct wrong impls (partial-domain, boundary, control-flow, prepatch x2) were verified and reported; prepatch bugs reproduced (atk_3=raw string, atk_4=xref). VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1.lean`, `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- An inline documentation node. A rendered type annotation is a sequence of
   these. Only the fields the rendered signature observes are kept: `text`
   carries literal display text, `xref` carries a cross-reference whose target
   is a type name (a navigable class reference), `punct` carries structural
   punctuation (brackets, commas). The bijection to the real inline-node
   carriers is in mapping.md §2. -/
inductive DocNode where
  | text  (s : List Char)
  | xref  (target : List Char)
  | punct (s : List Char)
  deriving DecidableEq, Inhabited, Repr

/- A constant value that can appear inside a parametrised type. Three shapes are
   modeled — a boolean, an integer, and a (simple) string literal — covering the
   constant kinds the documented annotations in scope use. The bijection to the
   real Python constant objects is in mapping.md §2. -/
inductive LitVal where
  | bool (b : Bool)
  | int  (n : Int)
  | str  (s : List Char)
  deriving DecidableEq, Inhabited, Repr

-- axioms-start
-- (No consumed axiom: the rendering of a parametrised type is modeled deeply —
--  see the `pure` region.)
-- axioms-end

-- pure-start
/- The domain on which the string representation below is exact: a "simple"
   string is one whose characters are all printable ASCII (32–126) other than
   the apostrophe and the backslash. Such a string is shown delimited by single
   quotes with no character needing an escape. Constant strings outside this
   domain (containing quotes, backslashes, or non-printable code points) are out
   of scope and excluded by the method precondition. -/
def isSimpleStrChar (c : Char) : Bool :=
  decide (32 ≤ c.toNat ∧ c.toNat ≤ 126) && c ≠ '\'' && c ≠ '\\'

def okLit : LitVal → Bool
  | .str s => s.all isSimpleStrChar
  | .int n => decide (0 ≤ n)
  | _      => true

/- The display text of one constant value: its canonical source representation.
   A boolean shows as `True`/`False`, an integer as its decimal digits, and a
   simple string as its single-quoted form (the surrounding quotes ARE part of
   the displayed text — a string constant is shown with delimiters so it reads
   unambiguously). Validated against the real value-representation routine over
   this domain by axiom_check.py (G-AX); provenance mapping.md §3.1. -/
def reprVal : LitVal → List Char
  | .bool true  => "True".toList
  | .bool false => "False".toList
  | .int n      => (toString n).toList
  | .str s      => '\'' :: (s ++ ['\''])

/- The node sequence for a comma-separated list of constant values: each value
   becomes one node built by `mk` from its display text `render v`, and adjacent
   values are separated by a `", "` punctuation node. Front-recursive so a single
   unfold is available per step. Parametrised over the node constructor `mk` and
   the per-value renderer `render` so the value-display policy is explicit at the
   call site. -/
def valSeq (mk : List Char → DocNode) (render : LitVal → List Char) :
    List LitVal → List DocNode
  | []      => []
  | [v]     => [mk (render v)]
  | v :: vs => mk (render v) :: DocNode.punct ", ".toList :: valSeq mk render vs

/- Frame the inner sequence with the head cross-reference and the surrounding
   brackets: `head` renders as a navigable cross-reference (the parametrised
   type itself), then `[`, then the inner nodes, then `]`. -/
def wrap (head : List Char) (inner : List DocNode) : List DocNode :=
  DocNode.xref head :: DocNode.punct "[".toList :: (inner ++ [DocNode.punct "]".toList])

/- Deep model (A-reference) of rendering a parametrised type whose arguments are
   constant values, on the domain this signature uses. The head is a navigable
   cross-reference; each constant argument is shown as PLAIN DISPLAY TEXT (its
   `reprVal`), NOT as a cross-reference — a constant value is not a class, so it
   carries no navigable reference. Validated == the real renderer over this
   domain by axiom_check.py (G-AX); provenance mapping.md §3.1. -/
def expandLiteral (head : List Char) (values : List LitVal) : List DocNode :=
  wrap head (valSeq DocNode.text reprVal values)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

method literalTypeNodes (head : List Char) (values : List LitVal)
    return (out : List DocNode)
  require head = "Literal".toList ∨ head = "typing.Literal".toList
  require values ≠ []
  require values.all okLit
  ensures out = expandLiteral head values
  do
    -- impl-start
    let inner := valSeq DocNode.text reprVal values
    let result := wrap head inner
    return result
    -- impl-end

prove_correct literalTypeNodes by
  loom_solve
  rfl
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition `ensures out = expandLiteral head values` FULLY PINS the output to the fully-concrete deep model expandLiteral/wrap/valSeq/reprVal (no axiom/opaque/:|/sorry). So any verifying impl must return exactly expandLiteral head values; a semantically-wrong impl cannot verify. Break-surface is therefore (a) deep-model faithfulness and (b) whether the sole verifying class ('echo' the RHS) has a faithful patch that resolves.

same_spec=True confirmed for all 8 files (velvet backend, byte-identical axioms/pure/pre/post).

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>):
- atk_1 (echo: `return expandLiteral head values`) -> exit 0 VERIFIES. Correct; = gold.
- atk_2 (one-level unfold: `wrap head (valSeq DocNode.text reprVal values)`) -> exit 0 VERIFIES. Correct; = gold.
- atk_3 (prepatch bug 1: str rendered RAW, no quotes) -> exit 1 REJECTED on `... != expandLiteral head values`.
- atk_4 (prepatch bug 2: values via DocNode.xref not .text) -> exit 1 REJECTED on `valSeq DocNode.xref reprVal values ... != expandLiteral`.
- atk_5 (partial-domain: emits only first value, drops rest) -> exit 1 REJECTED on `wrap head [DocNode.text (reprVal values.head!)] != expandLiteral`.
- atk_6 (boundary: wrong closing bracket ')' instead of ']') -> exit 1 REJECTED on `... punct ')' ... != expandLiteral`.
- atk_7 (control-flow-effect: `while true do ...` divergence) -> exit 0 VERIFIES (vacuously, under global loom.semantics.termination "partial").
- atk_pc (positive control = frozen impl) -> exit 0 VERIFIES.
Note: atk_1 and atk_7 initially exited 1 ONLY due to the trailing `rfl` after `loom_solve` in the (non-spec) proof block giving 'No goals to be solved'; removing the redundant rfl (proof script is outside the spec view; same_spec stays True) makes both verify. This is a proof-tactic artifact, not a semantic rejection.

RESOLVE RUN (mandatory, for the verifying impls atk_1/atk_2/atk_7): all three produce exactly the gold node sequence `expandLiteral head values`, so their FAITHFUL refined patch is the gold patch (verbatim, faithful_patch.diff = gold9602.patch). Ran through the official harness: swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9602', gold, timeout=1800) -> RESOLVED=True COMPLETED=True attempts=1 flaky=False. The verifying impls' faithful patch RESOLVES.

atk_7 divergence disposition: verifying-but-diverging is a universal artifact of the global partial-correctness setting, NOT a refinement-fidelity defect of THIS spec. The `while true` loop has no corresponding operation in patch.diff; a FAITHFUL refinement drops the non-corresponding infinite loop, leaving `return expandLiteral head values` = the gold patch, which resolves. It does not exhibit a verifying impl whose faithful patch fails to resolve.

DEEP-MODEL FAITHFULNESS (independent probe, faith_probe.py, run against the gold-patched real _parse_annotation): compared node-for-node (class, astext) vs the expandLiteral shadow on the two F2P rows + 4 variants (Literal[True,False]; typing.Literal[0,1,'abc'] with 'abc' single-quoted; Literal['x y z',7,False]; typing.Literal['a']; Literal[255]; Literal['']) -> BAD=0, all MATCH. This confirms expandLiteral == patched callee on the modeled domain, incl. the dotted head 'typing.Literal' and the single-quoted string repr.

REFINEMENT.MD AUDIT: 5 legs, all R / I / A-reference; NO kind-3 (no inexpressible-changed-op, no axiom about the changed function). A-references hold: (3.1) reprVal == builtin repr on bool/int/simple-str (G-AX, unchanged callee, base_commit); (3.2) head type_to_xref carrier -> pending_xref text/reftarget == head (G-AX); (3.3) whole-function expandLiteral == patched _parse_annotation (G-CONF 1e5 inputs seed 9602, and my independent probe, 0 disagreements). The genuinely-changed ops (repr-rendering, literal-text-vs-xref routing) are modeled DEEPLY in the concrete pure region, not hidden behind an axiom.

No verifying wrong impl has a faithful patch that fails to resolve; 5+ distinct wrong impls (partial-domain, boundary, control-flow, prepatch x2) were verified and reported; prepatch bugs reproduced (atk_3=raw string, atk_4=xref). VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical across Solution.lean and both prepatches (same_spec=True, velvet backend); frozen spec is genuine. Solution.lean compiles and prove_correct passes (lean_verify exit 0). Real callee sphinx.domains.python._parse_annotation at base_commit+gold-patch matches the gold diff (repr(node.value); literal-wrap under Literal/typing.Literal; top-loop unwrap-to-Text so values stay plain text, head becomes pending_xref). Faithfulness fuzz: ran patched real _parse_annotation vs a faithful port of expandLiteral over the full declared domain (head in {Literal, typing.Literal}, 1-4 args, each bool / non-negative int up to 1e12 / simple string = printable ASCII 32-126 excluding ' and backslash, incl. double-quote, comma, bracket, space, empty), 200000 trials seed 9602 -> 0 mismatches; plus hand-checked boundary cases. Preconditions (head-in-set, values nonempty, values.all okLit) exactly carve the guard's true-branch and the domain where repr is single-quoted/escape-free; the spec restricts the domain rather than over-constraining behavior. No diverging input exists within the modeled domain. Spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed byte-identical to both prepatch variants (swebench_unified.markers.same_spec == True). Mechanical G-LEAK screen passes cleanly (leakage.screen -> passed, zero hard_failures). Manual read of the consumer spec view (spec_view over Solution.lean; impl body + proof elided): NO gold-edit leakage beyond the public problem_statement. Specifically: (1) no patched file path (sphinx/domains/python.py) or module path; (2) no diff markers; (3) no reproduced gold-patch line; (4) no repo symbol names from the diff -- comments say 'the real value-representation routine' / 'the real renderer' / 'the real inline-node carriers', never `repr`, `nodes.Text`, `nodes.literal`, or `type_to_xref`; (5) no bug/fix narration in the spec-view comments (the pre-image/'fails prove_correct' narration lives only inside the ELIDED impl region, not the consumer view). The value-as-plain-text behavior (DocNode.text not xref) is ALREADY public: the problem_statement states Literal[True] must not be treated as a py:class. The reprVal single-quote detail exceeds the problem_statement but is stated as TARGET output behavior (what the rendered nodes look like), not as the edit -- it does not localize or reconstruct the diff. mapping.md/refinement.md name repo symbols and the base_commit, but those are audit docs, not the consumer spec view, so out of scope for G-PANEL-3. A solver reading this view learns the intended output, not which lines of which function change.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
